# -*- coding: utf-8 -*-
"""CPI(추정) 계산과 CPI 표 파싱을 네트워크 없이 검사한다.

추정식 자체의 정확도는 여기서 재지 않는다 — 2026-09-26 에 CPI 사이트 공개
사용자 9명과 비교해 평균 절대 오차 약 13, 최대 35 였다(handoff 참고).
여기서는 회귀만 막는다: 파싱 모양, 단조성, 최소 채보 수, ASSIST 처리.

    python dev/checks/cpi_check.py
"""
import _bootstrap  # noqa: F401
import django

django.setup()

from django.utils import timezone  # noqa: E402

from iidxrank import cpi, models  # noqa: E402

fails = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name, (' — %s' % detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


print('=== 1. 표 파싱 ===')
PAGE = '''
<table id="easy_table"><tr><td>
<a href="/scores/view/1">AKASHIC BREAK</a> <div class="small-txt" style="x">1371.23 / 200.00</div>
</td><td><a href="/scores/view/2">GuNGNiR [L]</a> <div class="small-txt">1897.93 / 211.52</div>
</td><td><a href="/scores/view/3">Sinus Iridum</a> <div class="small-txt">inf / -</div></td></tr></table>
<table id="hard_table"><tr><td>
<a href="/scores/view/1">AKASHIC BREAK</a> <div class="small-txt">1545.55 / 150.00</div></td></tr></table>
'''
parsed = cpi.parse(PAGE)
check('제목·타입 가르기 ([L] → SPL)', ('GuNGNiR', 'SPL') in parsed and ('AKASHIC BREAK', 'SPA') in parsed, str(list(parsed)))
check('램프 번호 (easy 3, hard 5)', parsed[('AKASHIC BREAK', 'SPA')] == {3: (1371.23, 200.0), 5: (1545.55, 150.0)})
check("'inf / -' 는 None", parsed[('Sinus Iridum', 'SPA')] == {3: (None, None)})

print('=== 2. 추정 ===')
songs = list(models.Song.objects.filter(songlevel=12, songtype='SPA').order_by('id')[:40])
saved = list(models.CpiValue.objects.values_list('song_id', 'lamp', 'mu', 'width', 'fetched_at'))
try:
    models.CpiValue.objects.all().delete()
    now = timezone.now()
    # 채보 40개: 쉬운 것부터 어려운 것까지 HARD 적정 1400~2200
    rows = []
    for i, s in enumerate(songs):
        base = 1400 + i * 20
        for lamp, off in ((3, -200), (4, -100), (5, 0), (6, 250), (7, 450)):
            rows.append(models.CpiValue(song=s, lamp=lamp, mu=base + off, width=200, fetched_at=now))
    models.CpiValue.objects.bulk_create(rows)
    ids = [s.id for s in songs]

    def est(clear_fn):
        return cpi.estimate({sid: clear_fn(i) for i, sid in enumerate(ids)})

    weak, n = est(lambda i: 5 if i < 10 else 1)
    mid, _ = est(lambda i: 5 if i < 20 else 4)
    strong, _ = est(lambda i: 5 if i < 35 else 4)
    check('채보 40개 모두 씀', n == 40, str(n))
    check('단조: 하드가 많을수록 높다', weak < mid < strong, '%s %s %s' % (weak, mid, strong))
    check('하드 20개(적정 1400~1780) → 1700~1900 사이', 1700 <= mid <= 1900, str(mid))
    few, n2 = cpi.estimate({sid: 5 for sid in ids[:cpi.MIN_CHARTS - 1]})
    check('채보가 %d개 미만이면 추정 안 함' % cpi.MIN_CHARTS, few is None and n2 == cpi.MIN_CHARTS - 1)
    a, _ = est(lambda i: 2 if i % 2 else 5)
    f, _ = est(lambda i: 1 if i % 2 else 5)
    check('ASSIST 는 FAILED 와 같다', a is not None and a == f, '%s %s' % (a, f))
    # 달성·미달성이 한쪽뿐이면 범위 끝(-1000/5000)이 나오던 것 — 라이브 첫 실행에서 4명이 -1000 이었다
    allf, n4 = est(lambda i: 1)
    check('전부 FAILED 면 추정 안 함(-1000 이 아니라)', allf is None and n4 == 40, str(allf))
    allfc, _ = est(lambda i: 7)
    check('전부 FC 면 추정 안 함(상한이 아니라)', allfc is None, str(allfc))
    np_, n3 = est(lambda i: 0)
    check('NO PLAY 만 있으면 추정 안 함', np_ is None and n3 == 0)
finally:
    models.CpiValue.objects.all().delete()
    models.CpiValue.objects.bulk_create([models.CpiValue(song_id=a, lamp=b, mu=c, width=d, fetched_at=e)
                                         for a, b, c, d, e in saved])

print('=== 3. CPI 페이지 (공개 규칙·공유 버튼) ===')
from django.contrib.auth.models import User  # noqa: E402
from django.test import Client  # noqa: E402
u = User.objects.create_user('zz_cpi_check', password='x-Unused-123')
try:
    from iidxrank.rankpage import newplayer
    pl = newplayer(u)
    models.AccountSecurity.objects.update_or_create(user=u, defaults={'newrulepassed': True})
    c = Client()
    check('남의 공개 페이지 200', c.get('/u/zz_cpi_check/cpi/').status_code == 200)
    check('공유 버튼은 남의 페이지에 없음', 'id="share"' not in c.get('/u/zz_cpi_check/cpi/').content.decode())
    pl.private = True
    pl.save()
    r1, r2 = c.get('/u/zz_cpi_check/cpi/'), c.get('/u/zz_nobody_here/cpi/')
    check('비공개 = 없는 계정 (둘 다 404, 같은 화면)', r1.status_code == r2.status_code == 404)
    pl.private = False
    pl.save()
    c.force_login(u)
    page = c.get('/cpi/').content.decode()
    check('내 페이지 200', c.get('/cpi/').status_code == 200)
    check('기록이 없으면 안내 문구', 'CPI 를 계산할 기록이 부족합니다' in page)
    prof0 = c.get('/table/SP12H/').content.decode()
    check("기록이 없어도 CPI 뱃지는 보임('-', 흐리게)", 'class="profile-cpi is-empty" href="/cpi/"' in prof0)
    check('비로그인 /cpi/ 도 200', Client().get('/cpi/').status_code == 200)
    # 기록이 있어 CPI 가 계산되는 경우: CPI 값이 있는 채보 12개에 HARD 기록을 만든다
    sids = list(models.CpiValue.objects.values_list('song_id', flat=True).distinct()[:12])
    models.PlayRecord.objects.bulk_create([models.PlayRecord(player=pl, song_id=x, playclear=5, playscore=6) for x in sids])
    from django.core.cache import cache
    cache.clear()          # CPI 캐시 키에 적재 시각이 들어가 키를 짚어 지우기보다 비운다
    page = c.get('/cpi/').content.decode()
    check('기록이 있으면 내 페이지에 공유 버튼', 'id="share"' in page and 'bm-cpi-hero' in page, str(len(sids)))
    check('공개 상태에선 비공개 안내 없음', 'bm-share-private' not in page)
    check('공유 주소는 /u/<아이디>/cpi/', 'data-share-path="/u/zz_cpi_check/cpi/"' in page)
    check('남이 보면 공유 버튼 없음', 'id="share"' not in Client().get('/u/zz_cpi_check/cpi/').content.decode())
    pl.private = True
    pl.save()
    page = c.get('/cpi/').content.decode()
    check('비공개여도 내 페이지는 200 · 공유 버튼 + 비공개 안내', 'id="share"' in page and 'bm-share-private' in page)
    check('비공개면 남에게 404', Client().get('/u/zz_cpi_check/cpi/').status_code == 404)
    # 서열표의 공유 상자도 같은 부품이다
    models.AccountSecurity.objects.update_or_create(user=u, defaults={'newrulepassed': True})
    tpage = c.get('/table/SP12H/').content.decode()
    check('서열표 공유 상자: 주소와 비공개 안내', 'data-share-path="/u/zz_cpi_check/table/SP12H/"' in tpage
          and 'bm-share-private' in tpage and 'bm-share-copy' in tpage)
    check('서열표: 곧바로 복사하던 alert 는 없다', '서열표 공유 주소가 복사되었습니다' not in tpage)
    pl.private = False
    pl.save()
    check('공개면 서열표 공유 상자에 비공개 안내 없음', 'bm-share-private' not in c.get('/table/SP12H/').content.decode())
    models.PlayRecord.objects.filter(player=pl).delete()
finally:
    models.Player.objects.filter(user=u).delete()
    u.delete()

print('')
print('총 실패: %d' % len(fails))
