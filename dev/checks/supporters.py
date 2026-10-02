"""후원자 기능을 확인한다 — iidxrank/supporters.py, views_manage.supporter_*, 계정 설정, 리더보드, 프로젝트 소개.

  1. 관리자 대시보드: staff 만, 아이디·이메일 검색, 지정·해제
  2. 배지: 서열표(본인 포함)·리더보드·소개 목록 모두 공개한 후원자만
  3. 계정 설정: 후원자에게만 '배지 공개' 칸, 끄고 켜기
  4. 소개 목록: 프로필 비공개면 링크 없이 이름만

    python dev/checks/supporters.py
"""
import re

import _bootstrap  # noqa: F401
import django

django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.test import Client  # noqa: E402
from django.utils import timezone  # noqa: E402

from iidxrank import models  # noqa: E402
from iidxrank.rankpage import newplayer  # noqa: E402

fails = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name, (' — %s' % detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


def mk(name, staff=False, email=''):
    u = User.objects.create_user(name, email=email, password='x-Unused-123', first_name=name.upper())
    u.is_staff = staff
    u.save()
    pl = newplayer(u)
    pl.iidxnick = name.upper()
    pl.save()
    models.AccountSecurity.objects.update_or_create(user=u, defaults={'newrulepassed': True})
    return u, pl


BADGE = 'class="bm-supporter"'
names = ['zz_sup_admin', 'zz_sup_fan', 'zz_sup_other']
User.objects.filter(username__in=names).delete()
admin, _ = mk('zz_sup_admin', staff=True)
fan, fan_pl = mk('zz_sup_fan', email='zz-sup-fan@example.invalid')
other, _ = mk('zz_sup_other')
try:
    ca, cf, co, anon = Client(), Client(), Client(), Client()
    ca.force_login(admin)
    cf.force_login(fan)
    co.force_login(other)

    print('=== 1. 관리자 대시보드 ===')
    check('일반 사용자는 지정 못 함', co.post('/manage/supporters/add/', {'user_id': fan.pk}).status_code in (302, 403)
          and not models.Supporter.objects.filter(user=fan).exists())
    page = ca.get('/manage/', {'q': 'zz-sup-fan@example'}).content.decode()
    check('이메일 일부로 검색', 'zz_sup_fan' in page and '후원자로 지정' in page)
    check('아이디 일부로 검색', 'zz_sup_fan' in ca.get('/manage/', {'q': 'sup_fa'}).content.decode())
    r = ca.post('/manage/supporters/add/', {'user_id': fan.pk, 'note': 'BMC 2026-10-02', 'q': 'sup_fa'})
    s = models.Supporter.objects.filter(user=fan).first()
    check('지정 → 기본 공개, 메모 저장', s is not None and s.public and s.note == 'BMC 2026-10-02', str(r.status_code))
    check('지정 뒤 검색어를 지닌 채 돌아감', r.status_code == 302 and 'q=sup_fa' in r['Location'] and r['Location'].endswith('#supporters'))
    check('목록에 보임', 'BMC 2026-10-02' in ca.get('/manage/').content.decode())

    print('=== 2. 배지 노출 ===')
    check('내 서열표: 배지', BADGE in cf.get('/table/SP12H/').content.decode())
    check('남이 보는 내 서열표: 배지', BADGE in co.get('/u/zz_sup_fan/table/SP12H/').content.decode())
    check('비로그인도 배지', BADGE in anon.get('/u/zz_sup_fan/table/SP12H/').content.decode())
    check('후원자 아닌 사람은 배지 없음', 'bm-supporter' not in anon.get('/u/zz_sup_other/table/SP12H/').content.decode())
    today = timezone.localdate()
    models.TypingLog.objects.create(user=fan, date=today, count=10 ** 9)          # 1위
    models.TypingLog.objects.create(user=other, date=today, count=10 ** 9 - 1)
    lb = anon.get('/my-page/', {'rank': 'all'}).content.decode()
    i = lb.find('ZZ_SUP_FAN')
    check('리더보드: 이름 오른쪽에 배지', i > 0 and BADGE in lb[i:i + 400], lb[i:i + 200] if i > 0 else 'no row')
    j = lb.find('ZZ_SUP_OTHER')
    check('리더보드: 후원자 아니면 배지 없음', j > 0 and 'bm-supporter' not in lb[j:j + 200])
    about = anon.get('/about/').content.decode()
    check('소개: 후원자 목록에 링크와 함께', '후원자 목록' in about and 'href="/u/zz_sup_fan/">ZZ_SUP_FAN' in about)

    print('=== 3. 계정 설정 ===')
    check('후원자 아닌 사람에게는 칸 없음', 'supporter_public' not in co.get('/account/').content.decode())
    acc = cf.get('/account/').content.decode()
    tag = re.search(r'<input[^>]*name="supporter_public"[^>]*>', acc)
    check('후원자에게는 칸이 있고 켜져 있음', tag is not None and 'checked' in tag.group(0))
    form = {'first_name': 'ZZ_SUP_FAN', 'iidxnick': 'ZZ_SUP_FAN', 'spclass': '1', 'dpclass': '1'}
    # IIDX ID 칸 이름은 폼이 정한다 — 화면에서 읽어 비워 보낸다
    for n in set(re.findall(r'name="(iidxid[^"]*)"', acc)):
        form[n] = ''
    cf.post('/account/', form)                                           # 체크 안 함 = 비공개
    check('끄면 비공개로 저장', models.Supporter.objects.get(user=fan).public is False)
    check('비공개: 남의 서열표에서 배지 없음', 'bm-supporter' not in co.get('/u/zz_sup_fan/table/SP12H/').content.decode())
    check('비공개: 내 서열표에서도 배지 없음', 'bm-supporter' not in cf.get('/table/SP12H/').content.decode())
    lb = anon.get('/my-page/', {'rank': 'all'}).content.decode()
    i = lb.find('ZZ_SUP_FAN')
    check('비공개: 리더보드 배지 없음', i > 0 and 'bm-supporter' not in lb[i:i + 200])
    check('비공개: 소개 목록에서 빠짐', 'ZZ_SUP_FAN' not in anon.get('/about/').content.decode())
    cf.post('/account/', dict(form, supporter_public='on'))
    check('다시 켜면 공개, 내 서열표에 곧바로 다시 보임', models.Supporter.objects.get(user=fan).public is True
          and BADGE in cf.get('/table/SP12H/').content.decode())

    print('=== 4. 프로필 비공개 ===')
    fan_pl.private = True
    fan_pl.save()
    about = anon.get('/about/').content.decode()
    check('프로필 비공개면 소개 목록에 이름만(링크 없음)', 'ZZ_SUP_FAN' in about and '/u/zz_sup_fan/' not in about)
    fan_pl.private = False
    fan_pl.save()

    print('=== 5. 해제 ===')
    ca.post('/manage/supporters/remove/', {'user_id': fan.pk})
    check('해제하면 배지·목록 모두 사라짐', not models.Supporter.objects.filter(user=fan).exists()
          and 'bm-supporter' not in cf.get('/table/SP12H/').content.decode()
          and 'ZZ_SUP_FAN' not in anon.get('/about/').content.decode())
finally:
    models.TypingLog.objects.filter(user__username__in=names).delete()
    models.Player.objects.filter(user__username__in=names).delete()
    User.objects.filter(username__in=names).delete()

print('')
print('총 실패: %d' % len(fails))
