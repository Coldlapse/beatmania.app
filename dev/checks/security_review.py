"""보안 코드 리뷰(handoff-security-review.md, 2026-09-26) 1장·2-1 의 수정을 확인한다.

  1-1 서열표 페이지: 닉네임의 '</script>' 가 스크립트 블록을 끝내지 못한다
  1-2 유저 랭킹: 페이지와 /json/userlist/ 를 지웠다(쓰지 않던 기능) → 404
  1-3 /modify/: POST 만, CSRF 검사, 쓰지 않던 동작(djname 등) 제거, edit 입력 검증
      + 계정 설정 폼이 이름의 < > 를 거부한다
  2-1 /json/recommend/: 지웠다(쓰지 않던 기능) → 404
  덧: NOPLAY 로 바꿔도 EX SCORE 가 있는 기록은 지우지 않는다

임시 사용자 zz_sec_* 를 만들고 끝나면 지운다.

    python dev/checks/security_review.py
"""
import json
import re

import _bootstrap  # noqa: F401
import django

django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.test import Client  # noqa: E402

from iidxrank import forms, models  # noqa: E402
from iidxrank.rankpage import newplayer  # noqa: E402

fails = []
EVIL = '</script><i>&x'   # 이름 칸(20자) 안에 들어가는 탈출 페이로드


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name,
                         (' — %s' % detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


# 서열표에 있는 SP☆12 곡 하나
table = models.RankTable.objects.get(tablename='SP12H')
song = models.Song.objects.filter(songtype='SPA', songlevel=12).first()

u = User.objects.create_user('zz_sec_a', password='x-Unused-123', first_name=EVIL)
v = User.objects.create_user('zz_sec_b', password='x-Unused-123')
extra = []   # 검사 중에 만드는 임시 계정(끝나면 지운다)
try:
    player = newplayer(u)
    player.iidxnick = EVIL
    player.iidxid = EVIL
    player.save()
    models.AccountSecurity.objects.update_or_create(user=u, defaults={'newrulepassed': True})
    pv = newplayer(v)
    models.AccountSecurity.objects.update_or_create(user=v, defaults={'newrulepassed': True})

    print('=== 1-1. 서열표 페이지의 JSON ===')
    html = Client().get('/u/zz_sec_a/table/SP12H/').content.decode()
    m = re.search(r'var tabledata = (.*?);\n', html)
    check('tabledata 줄이 있다', m is not None)
    if m:
        raw = m.group(1)
        check('JSON 안에 < > & 가 그대로 없다', not re.search(r'[<>&]', raw), raw[:200])
        check('풀면 원래 값', EVIL in json.dumps(json.loads(raw), ensure_ascii=False))
    check('페이지 어디에도 날것의 페이로드가 없다', EVIL not in html)

    print('=== 1-3. /modify/ ===')
    c = Client(enforce_csrf_checks=True)
    c.force_login(v)
    check('GET 은 405', c.get('/modify/', {'action': 'edit', 'v': '[]'}).status_code == 405)
    check('CSRF 토큰 없는 POST 는 403',
          c.post('/modify/', {'action': 'edit', 'v': '[]'}).status_code == 403)
    w = Client()
    w.force_login(v)
    post = lambda action, val: w.post('/modify/', {'action': action, 'v': val}).json()
    for gone in ('djname', 'iidxid', 'spclass', 'dpclass', 'delete'):
        check('없앤 동작 %s → invalid action' % gone,
              post(gone, 'X').get('message') == 'invalid action')
    pv.refresh_from_db()
    check('djname 이 바뀌지 않음', pv.iidxnick != 'X')
    rj = post('edit', json.dumps([{'id': song.id, 'rank': 6}]))
    check('rank 만 보내도 500 이 아니다(code 0)', rj.get('code') == 0, str(rj))
    rec = models.PlayRecord.objects.get(player=pv, song=song)
    check('rank 반영', rec.playscore == 6)
    rj = post('edit', json.dumps([{'id': song.id, 'clear': 5}]))
    check('clear 반영', rj.get('code') == 0 and models.PlayRecord.objects.get(player=pv, song=song).playclear == 5)
    for bad, label in ((json.dumps([{'id': song.id, 'clear': 9}]), 'clear 범위 밖'),
                       (json.dumps([{'id': song.id, 'rank': -1}]), 'rank 범위 밖'),
                       (json.dumps([{'id': song.id}]), '값 없음'),
                       (json.dumps([{'id': 99999999, 'clear': 3}]), '없는 곡'),
                       ('nope', 'JSON 아님')):
        r = w.post('/modify/', {'action': 'edit', 'v': bad})
        check('거부: %s' % label, r.status_code == 200 and r.json().get('code') == 1,
              '%s %s' % (r.status_code, r.content[:120]))

    print('=== 1-3. 계정 설정 폼 ===')
    base = {'first_name': 'ok', 'iidxnick': 'OK', 'iidxid_0': 'C', 'iidxid_1': '', 'iidxid_2': '',
            'iidxid_3': '', 'spclass': '1', 'dpclass': '1'}
    f = forms.AccountForm(dict(base))
    check('평범한 이름은 통과', f.is_valid(), str(f.errors))
    for field in ('first_name', 'iidxnick'):
        for val in ('<b>', 'a>b', 'tab\there', 'x' * 21):
            f = forms.AccountForm(dict(base, **{field: val}))
            check('%s 거부 %r' % (field, val[:8]), not f.is_valid() and field in f.errors)
    f = forms.AccountForm(dict(base, first_name='홍길동 A&B'))
    check('& 와 한글은 허용', f.is_valid(), str(f.errors))

    print('=== 덧. NOPLAY 와 EX SCORE ===')
    models.PlayRecord.objects.filter(player=pv, song=song).update(exscore=1500)
    post('edit', json.dumps([{'id': song.id, 'clear': 0}]))
    rec = models.PlayRecord.objects.filter(player=pv, song=song).first()
    check('EX SCORE 있는 기록은 NOPLAY 로 남는다', rec is not None and rec.playclear == 0 and rec.exscore == 1500,
          str(rec and (rec.playclear, rec.exscore)))
    models.PlayRecord.objects.filter(player=pv, song=song).update(exscore=None, playclear=3)
    post('edit', json.dumps([{'id': song.id, 'clear': 0}]))
    check('EX SCORE 없으면 전처럼 지운다', not models.PlayRecord.objects.filter(player=pv, song=song).exists())

    print('=== 2a-1. 서열표 이미지 저장 ===')
    check('/imgdownload/ 404', Client().post('/imgdownload/', {'name': 'x.bat', 'base64': 'eA=='}).status_code == 404)
    js = open('static/js/common.js', encoding='utf-8').read()
    check('downloadCanvas 가 toBlob 으로 저장', 'c.toBlob(' in js and '#imgdownload' not in js)
    html = w.get('/table/SP12H/').content.decode()
    check('서열표에 서버 왕복용 폼이 없다', 'id="imgdownload"' not in html and 'id="capture"' in html)

    print('=== 2a-2. 탈퇴 ===')
    s4 = User.objects.create_user('zzs4', password='x-Unused-123')     # 4자 아이디
    extra.append(s4)
    newplayer(s4)
    models.AccountSecurity.objects.update_or_create(user=s4, defaults={'newrulepassed': True})
    c4 = Client()
    c4.force_login(s4)
    page = c4.get('/withdraw/').content.decode()
    check('탈퇴 폼에 아이디 칸이 없다', 'name="id"' not in page and 'name="password"' in page)
    # 남의 자격(다른 아이디 + 그 비밀번호)을 넣어도 폼이 아이디를 받지 않으니 통하지 않는다
    c4.post('/withdraw/', {'id': 'zz_sec_b', 'password': 'wrong-pw-1', 'password_again': 'wrong-pw-1'})
    check('틀린 비밀번호로는 지워지지 않는다', User.objects.filter(pk=s4.pk).exists())
    c4.post('/withdraw/', {'password': 'x-Unused-123', 'password_again': 'x-Unused-123'})
    check('4자 아이디도 본인 비밀번호로 탈퇴된다', not User.objects.filter(pk=s4.pk).exists())
    su = User.objects.create_superuser('zz_sec_su', 'zz_sec_su@example.invalid', 'x-Unused-123')
    extra.append(su)
    models.AccountSecurity.objects.update_or_create(user=su, defaults={'newrulepassed': True})
    csu = Client()
    csu.force_login(su)
    check('superuser 탈퇴 화면은 403(500 아님)', csu.get('/withdraw/').status_code == 403)

    print('=== 2a-3. /modify/ 상한, Player 없는 계정 ===')
    rj = post('edit', json.dumps([{'id': song.id, 'clear': 3}] * 1001))
    check('1,001개는 거부', rj.get('code') == 1, str(rj))
    rj = post('edit', json.dumps({'id': song.id, 'clear': 3}))
    check('목록이 아니면 거부', rj.get('code') == 1, str(rj))
    rj = post('edit', json.dumps([{'id': song.id, 'clear': 3}] * 1000))
    check('1,000개는 받는다', rj.get('code') == 0, str(rj))
    np_user = User.objects.create_user('zz_sec_np', password='x-Unused-123')   # Player 행 없음
    extra.append(np_user)
    models.AccountSecurity.objects.update_or_create(user=np_user, defaults={'newrulepassed': True})
    cn = Client()
    cn.force_login(np_user)
    r = cn.post('/modify/', {'action': 'exscore', 'v': json.dumps({'id': song.id, 'exscore': 100})})
    check('Player 없는 계정도 500 이 아니다', r.status_code == 200 and r.json().get('code') == 0,
          '%s %s' % (r.status_code, r.content[:120]))

    print('=== 2a-4. /sync/ 업로드 크기 ===')
    from django.core.files.uploadedfile import SimpleUploadedFile
    from iidxrank import records_import
    big = SimpleUploadedFile('tracker.tsv', b'x' * (records_import.MAX_BYTES + 1), 'text/tab-separated-values')
    w.post('/sync/', {'tracker': big})
    check('큰 파일은 읽기 전에 거부', '파일이 너무 큽니다' in w.get('/sync/').content.decode())

    print('=== 2a-5. 타건 기록 API ===')
    tok = models.ApiToken.objects.create(user=v).key
    api = lambda body: Client().post('/api/v1/update-typing-count/', body, content_type='application/json',
                                      HTTP_AUTHORIZATION='Token ' + tok)
    check('600,000 은 받는다', api(json.dumps({'count': 600000})).status_code == 200)
    check('600,001 은 거부', api(json.dumps({'count': 600001})).status_code == 400)
    check('true 는 거부', api(json.dumps({'count': True})).status_code == 400)
    check('배열 본문은 400(500 아님)', api(json.dumps([1, 2])).status_code == 400)
    check('UTF-8 아닌 본문은 400', api(b'\xff\xfe').status_code == 400)
    for _i in range(2):
        api(json.dumps({'count': 600000}))          # 합계 1,800,000
    r = api(json.dumps({'count': 200000}))
    check('하루 합계 2,000,000 까지 받는다', r.status_code == 200 and r.json().get('daily_total') == 2000000,
          str(r.content[:120]))
    r = api(json.dumps({'count': 1}))
    check('하루 합계를 넘으면 거부', r.status_code == 400, str(r.content[:120]))
    User.objects.filter(pk=v.pk).update(is_active=False)
    check('비활성 계정 토큰은 401', api(json.dumps({'count': 1})).status_code == 401)
    User.objects.filter(pk=v.pk).update(is_active=True)
    models.TypingLog.objects.filter(user=v).delete()

    print('=== 2a-6. 로그아웃 ===')
    lo = Client()
    lo.force_login(v)
    lo.get('/logout/')
    check('GET 으로는 로그아웃되지 않는다', '_auth_user_id' in lo.session)
    lo.post('/logout/')
    check('POST 로 로그아웃된다', '_auth_user_id' not in lo.session)

    print('=== 2a-7. 비밀번호 앞뒤 공백 ===')
    pw_user = User.objects.create_user('zz_sec_pw', password='Pw-long-9 ')   # 옛 가입처럼 그대로 저장
    extra.append(pw_user)
    check('그대로 저장된 비밀번호를 그대로 입력하면 로그인', forms.LoginForm({'id': 'zz_sec_pw', 'password': 'Pw-long-9 '}).is_valid())
    pw_user.set_password('Pw-long-9')                                        # 옛 변경·재설정처럼 자른 값
    pw_user.save()
    check('잘려 저장된 비밀번호에 공백을 붙여 입력해도 로그인', forms.LoginForm({'id': 'zz_sec_pw', 'password': 'Pw-long-9 '}).is_valid())
    check('틀린 비밀번호는 거부', not forms.LoginForm({'id': 'zz_sec_pw', 'password': 'Pw-long-8'}).is_valid())
    models.AccountSecurity.objects.update_or_create(user=pw_user, defaults={'newrulepassed': True})
    lc = Client()
    r = lc.post('/login/', {'id': 'zz_sec_pw', 'password': 'Pw-long-9 '})
    check('로그인 뷰가 폼이 찾은 사용자로 로그인(302)', r.status_code == 302 and '_auth_user_id' in lc.session,
          str(r.status_code))

    print('=== 2a-8. 서비스 현황의 점검 문장 ===')
    from django.utils import timezone as tz
    from iidxrank import health
    now = tz.now()
    hc = [models.HealthCheck.objects.create(target=t, status='down', note='ZZ_SEC_NOTE %s' % t, checked_at=now)
          for t in health.CHECKS]
    try:
        check('익명에게는 점검 문장이 안 보인다', 'ZZ_SEC_NOTE' not in Client().get('/status/').content.decode())
        check('staff 에게는 보인다', 'ZZ_SEC_NOTE' in csu.get('/status/').content.decode())
    finally:
        models.HealthCheck.objects.filter(pk__in=[h.pk for h in hc]).delete()

    # ── 2-b ────────────────────────────────────────────────────────────────
    from django.conf import settings as dj_settings
    from django.core import mail
    from django.core.cache import caches
    from django.test import RequestFactory, override_settings
    from iidxrank import accounts as acc
    from iidxrank import throttle as thr
    from iidxrank.client_ip import RealClientIPMiddleware
    caches['throttle'].clear()

    print('=== 2b-1. 실제 IP ===')
    check('미들웨어가 맨 앞', dj_settings.MIDDLEWARE[0] == 'iidxrank.client_ip.RealClientIPMiddleware')
    mw = RealClientIPMiddleware(lambda r: r)
    r = mw(RequestFactory().get('/', HTTP_CF_CONNECTING_IP='203.0.113.5', HTTP_X_FORWARDED_FOR='1.2.3.4'))
    check('CF-Connecting-IP → REMOTE_ADDR·X-Forwarded-For',
          r.META['REMOTE_ADDR'] == '203.0.113.5' and r.META['HTTP_X_FORWARDED_FOR'] == '203.0.113.5')
    r = mw(RequestFactory().get('/', HTTP_CF_CONNECTING_IP='nope', REMOTE_ADDR='127.0.0.1'))
    check('IP 가 아닌 값은 무시', r.META['REMOTE_ADDR'] == '127.0.0.1')

    def ipc(ip):
        return Client(HTTP_CF_CONNECTING_IP=ip)

    print('=== 2b-2. 로그인 시도 제한 ===')
    lg = User.objects.create_user('zz_sec_lg', password='Lg-right-77')
    extra.append(lg)
    newplayer(lg)
    models.AccountSecurity.objects.update_or_create(user=lg, defaults={'newrulepassed': True})
    a = ipc('198.51.100.1')
    for _i in range(10):
        a.post('/login/', {'id': 'zz_sec_lg', 'password': 'wrong-pw-%d' % _i})
    r = a.post('/login/', {'id': 'zz_sec_lg', 'password': 'Lg-right-77'})
    check('10번 틀린 뒤에는 맞는 비밀번호도 막힘', r.status_code == 200 and '_auth_user_id' not in a.session
          and '로그인 시도가 너무 많습니다' in r.content.decode())
    b = ipc('198.51.100.2')
    r = b.post('/login/', {'id': 'zz_sec_lg', 'password': 'Lg-right-77'})
    check('다른 IP 에서는 정상 로그인', r.status_code == 302 and '_auth_user_id' in b.session)
    adm = ipc('198.51.100.1')
    r = adm.post('/admin/login/?next=/admin/', {'username': 'zz_sec_lg', 'password': 'Lg-right-77'})
    check('관리자 로그인에도 같은 잠금', '_auth_user_id' not in adm.session)
    ghost = ipc('198.51.100.3')
    for _i in range(10):
        ghost.post('/login/', {'id': 'zz_sec_nobody', 'password': 'wrong-pw-x'})
    r = ghost.post('/login/', {'id': 'zz_sec_nobody', 'password': 'wrong-pw-x'})
    check('없는 아이디도 똑같이 잠김(존재 여부 안 샘)', '로그인 시도가 너무 많습니다' in r.content.decode())
    many = ipc('198.51.100.4')
    for _i in range(30):
        many.post('/login/', {'id': 'zz_sec_n%02d' % _i, 'password': 'wrong-pw-x'})
    r = many.post('/login/', {'id': 'zz_sec_lg', 'password': 'Lg-right-77'})
    check('한 IP 가 30번 틀리면 다른 아이디도 막힘', '_auth_user_id' not in many.session)
    ok_ip = ipc('198.51.100.5')
    for _i in range(9):
        ok_ip.post('/login/', {'id': 'zz_sec_lg', 'password': 'wrong'})
    ok_ip.post('/login/', {'id': 'zz_sec_lg', 'password': 'Lg-right-77'})
    check('성공하면 그 조합의 실패는 지워진다', thr.count('login_pair', 'zz_sec_lg', '198.51.100.5') == 0)

    print('=== 2b-3. 가입 여부가 응답으로 새지 않는다 ===')
    taken = User.objects.create_user('zz_sec_tk', email='zz_sec_taken@example.com', password='x-Unused-123')
    extra.append(taken)
    models.AccountSecurity.objects.update_or_create(user=taken, defaults={'newrulepassed': True})
    send = lambda c, email, purpose: c.post('/account/verify/send/', json.dumps({'email': email, 'purpose': purpose}),
                                            content_type='application/json').json()
    chk = lambda c, email, purpose, code: c.post('/account/verify/check/', json.dumps(
        {'email': email, 'purpose': purpose, 'code': code}), content_type='application/json').json()
    import re as _re

    def last_code():
        return _re.search(r'\b(\d{6})\b', mail.outbox[-1].body).group(1)

    with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', EMAIL_SEND_ASYNC=False):
        mail.outbox = []
        r1 = send(ipc('198.51.100.10'), 'zz_sec_taken@example.com', 'signup')
        r2 = send(ipc('198.51.100.11'), 'zz_sec_fresh@example.com', 'signup')
        check('가입: 이미 쓰는 주소와 새 주소의 응답이 같다', r1 == r2 and r1.get('ok') is True, '%s / %s' % (r1, r2))
        subjects = [m.subject for m in mail.outbox]
        check('이미 쓰는 주소에는 코드 대신 안내 메일', len(mail.outbox) == 2 and '이미 가입된' in subjects[0]
              and not _re.search(r'\b\d{6}\b', mail.outbox[0].body), str(subjects))
        mail.outbox = []
        r1 = send(ipc('198.51.100.12'), 'zz_sec_taken@example.com', 'find_id')
        r2 = send(ipc('198.51.100.13'), 'zz_sec_none@example.com', 'find_id')
        check('아이디 찾기: 가입·미가입 응답이 같다', r1 == r2 and r1.get('ok') is True, '%s / %s' % (r1, r2))
        check('메일은 가입된 주소에만 간다', len(mail.outbox) == 1 and mail.outbox[0].to == ['zz_sec_taken@example.com'])
        c1, c2 = ipc('198.51.100.14'), ipc('198.51.100.15')
        send(c1, 'zz_sec_taken@example.com', 'reset_pw')
        send(c2, 'zz_sec_none2@example.com', 'reset_pw')
        s1 = send(c1, 'zz_sec_taken@example.com', 'reset_pw')
        s2 = send(c2, 'zz_sec_none2@example.com', 'reset_pw')
        norm = lambda m: _re.sub(r'\d+', 'N', m.get('message', ''))
        check('재발송 간격 문구도 같다', norm(s1) == norm(s2) and s1.get('ok') is False, '%s / %s' % (s1, s2))
        k1 = chk(c1, 'zz_sec_taken@example.com', 'reset_pw', '000000')
        k2 = chk(c2, 'zz_sec_none2@example.com', 'reset_pw', '000000')
        check('코드 확인 실패 문구가 같다', k1 == k2, '%s / %s' % (k1, k2))

        print('=== 2b-4. 메일 발송 한도 ===')
        caches['throttle'].clear()
        f = ipc('198.51.100.20')
        rs = [send(f, 'zz_sec_ip%02d@example.com' % i, 'find_id') for i in range(11)]
        check('IP 당 1시간 10번, 11번째는 거부', all(x.get('ok') for x in rs[:10]) and rs[10].get('ok') is False,
              str(rs[10]))
        rs = [send(ipc('198.51.100.%d' % (30 + i)), 'zz_sec_addr@example.com', 'find_id') for i in range(6)]
        check('주소당 1시간 5번, 6번째는 거부', all(x.get('ok') for x in rs[:5]) and rs[5].get('ok') is False,
              str(rs[5]))
        for _i in range(thr.MAIL_DAY[0]):
            thr.hit('mail_day', thr.MAIL_DAY[1])
        r = send(ipc('198.51.100.40'), 'zz_sec_day@example.com', 'signup')
        check('사이트 전체 하루 100통을 넘으면 거부', r.get('ok') is False, str(r))
        caches['throttle'].clear()
        real_deliver = acc._deliver

        def boom(*a, **k):
            raise OSError('smtp down')
        acc._deliver = boom
        try:
            g = ipc('198.51.100.41')
            before = models.EmailVerification.objects.filter(email='zz_sec_fail@example.com').count()
            r = send(g, 'zz_sec_fail@example.com', 'signup')
            check('로그인 전 목적: 발송 실패여도 응답은 같다(500 아님)', r.get('ok') is True, str(r))
            check('실패한 코드는 남지 않는다',
                  models.EmailVerification.objects.filter(email='zz_sec_fail@example.com').count() == before)
            r = send(g, 'zz_sec_fail@example.com', 'signup')
            check('재발송 간격은 그대로 걸린다', r.get('ok') is False and '초 뒤' in r.get('message', ''), str(r))
            chg = Client(HTTP_CF_CONNECTING_IP='198.51.100.42')
            chg.force_login(v)
            r = send(chg, 'zz_sec_newaddr@example.com', 'change')
            check('로그인한 목적(이메일 변경): 실패를 알린다',
                  r.get('ok') is False and '보내지 못했습니다' in r.get('message', ''), str(r))
            acc._deliver = real_deliver
            r = send(chg, 'zz_sec_newaddr@example.com', 'change')
            check('그 뒤 바로 다시 요청할 수 있다', r.get('ok') is True, str(r))
        finally:
            acc._deliver = real_deliver

        print('=== 2b-5. 인증 코드 ===')
        caches['throttle'].clear()
        mail.outbox = []
        me, other = ipc('198.51.100.50'), ipc('198.51.100.51')
        send(me, 'zz_sec_taken@example.com', 'reset_pw')
        my_code = last_code()
        send(other, 'zz_sec_taken@example.com', 'reset_pw')      # 남이 같은 주소로 요청
        k = chk(me, 'zz_sec_taken@example.com', 'reset_pw', my_code)
        check('남이 같은 주소로 요청해도 내 코드는 통한다', k.get('ok') is True, str(k))
        k = chk(me, 'zz_sec_taken@example.com', 'reset_pw', my_code)
        check('한 번 쓴 코드는 다시 통하지 않는다', k.get('ok') is False, str(k))
        caches['throttle'].clear()
        for _i in range(10):
            chk(me, 'zz_sec_none3@example.com', 'reset_pw', '%06d' % _i)
        k = chk(me, 'zz_sec_none3@example.com', 'reset_pw', '123456')
        check('하루 10번 틀리면 그날은 막힘', k.get('ok') is False and '오늘은' in k.get('message', ''), str(k))
        k = chk(me, 'zz_sec_taken@example.com', 'reset_pw', '１２３４５６')
        check('전각 숫자 코드도 500 이 아니다', k.get('ok') is False)
    print('=== p1-1. 응답 시간으로 가입 여부가 새지 않는다(백그라운드 발송) ===')
    import time as _t
    caches['throttle'].clear()
    with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', EMAIL_SEND_ASYNC=True):
        mail.outbox = []
        slow_real = acc._deliver

        def slow(*a, **k):
            _t.sleep(1.5)          # 느린 SMTP 흉내
            return slow_real(*a, **k)
        acc._deliver = slow
        try:
            t0 = _t.time()
            ra = send(ipc('198.51.100.60'), 'zz_sec_taken@example.com', 'reset_pw')
            ta = _t.time() - t0
            t0 = _t.time()
            rb = send(ipc('198.51.100.61'), 'zz_sec_none4@example.com', 'reset_pw')
            tb = _t.time() - t0
            check('가입된 주소도 SMTP 를 기다리지 않는다(<1초)', ta < 1.0, '%.2fs' % ta)
            check('두 응답 시간 차이 0.5초 미만', abs(ta - tb) < 0.5, '%.2fs / %.2fs' % (ta, tb))
            acc.wait_for_mail()
            check('메일은 응답 뒤에 나간다', len(mail.outbox) == 1 and mail.outbox[0].to == ['zz_sec_taken@example.com'])
        finally:
            acc._deliver = slow_real

    print('=== p1-3. 이메일 변경: 비밀번호 재확인, 이전 주소 알림 ===')
    caches['throttle'].clear()
    ce = User.objects.create_user('zz_sec_ce', email='zz_sec_old@example.com', password='Ce-right-55')
    extra.append(ce)
    newplayer(ce)
    models.AccountSecurity.objects.update_or_create(user=ce, defaults={'newrulepassed': True})
    with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', EMAIL_SEND_ASYNC=False):
        mail.outbox = []
        cc = Client(HTTP_CF_CONNECTING_IP='198.51.100.70')
        cc.force_login(ce)
        send(cc, 'zz_sec_new@example.com', 'change')
        code = last_code()
        chk(cc, 'zz_sec_new@example.com', 'change', code)
        r = cc.post('/account/email/', {'email': 'zz_sec_new@example.com', 'current_password': 'wrong-pw-1'})
        ce.refresh_from_db()
        check('비밀번호가 틀리면 바뀌지 않는다', ce.email == 'zz_sec_old@example.com')
        mail.outbox = []
        r = cc.post('/account/email/', {'email': 'zz_sec_new@example.com', 'current_password': 'Ce-right-55'})
        ce.refresh_from_db()
        check('맞으면 바뀐다', ce.email == 'zz_sec_new@example.com', '%s %s' % (r.status_code, ce.email))
        check('이전 주소로 알림(새 주소는 가림)', len(mail.outbox) == 1 and mail.outbox[0].to == ['zz_sec_old@example.com']
              and 'zz***@example.com' in mail.outbox[0].body and 'zz_sec_new@' not in mail.outbox[0].body,
              str([(m.to, m.body[:80]) for m in mail.outbox]))
    models.EmailVerification.objects.filter(email__startswith='zz_sec_').delete()
    caches['throttle'].clear()

    print('=== p2. 2순위 ===')
    from iidxrank import views_status, health as _health
    from update import runner as _runner
    caches['throttle'].clear()
    # 서비스 현황 점검 잠금
    calls = []
    real_run_all = _health.run_all
    _health.run_all = lambda: calls.append(1) or []
    try:
        models.HealthCheck.objects.filter(target__startswith='zz').delete()
        caches['throttle'].add('status:refresh-lock', 1, 60)
        stale = models.HealthCheck.objects.order_by('-checked_at').first()
        if stale:
            models.HealthCheck.objects.update()     # 아무것도 바꾸지 않음(가독용)
        with override_settings():
            views_status.SELF_CHECK_AFTER_saved = views_status.SELF_CHECK_AFTER
            import datetime as _dt
            views_status.SELF_CHECK_AFTER = _dt.timedelta(seconds=-1)     # 늘 오래됐다고 보게
            views_status._refresh_if_stale()
            check('잠금을 누가 쥐고 있으면 점검하지 않는다', calls == [], str(calls))
            caches['throttle'].delete('status:refresh-lock')
            views_status._refresh_if_stale()
            check('잠금이 없으면 한 번 점검', calls == [1], str(calls))
            check('점검 뒤 잠금을 푼다', caches['throttle'].get('status:refresh-lock') is None)
            views_status.SELF_CHECK_AFTER = views_status.SELF_CHECK_AFTER_saved
    finally:
        _health.run_all = real_run_all
    # 프록시 설정·미들웨어 순서
    check('USE_X_FORWARDED_HOST 꺼짐', not getattr(dj_settings, 'USE_X_FORWARDED_HOST', False))
    body = Client(HTTP_X_FORWARDED_HOST='evil.example').get('/overjoy/header.json').content.decode()
    check('X-Forwarded-Host 로 사이트 주소가 바뀌지 않는다', 'evil.example' not in body, body[:120])
    mw = list(dj_settings.MIDDLEWARE)
    check('SecurityMiddleware·WhiteNoise 가 앞쪽(2·3번째)',
          mw[1] == 'django.middleware.security.SecurityMiddleware'
          and mw[2] == 'whitenoise.middleware.WhiteNoiseMiddleware', str(mw[:4]))
    r = Client().get('/withdraw/')                 # 로그인 강제 리다이렉트(앞에서 끝나는 응답)
    check('리다이렉트 응답에도 보안 헤더', r.status_code == 302 and r.get('X-Content-Type-Options') == 'nosniff',
          '%s %s' % (r.status_code, r.get('X-Content-Type-Options')))
    # CSP 보고 전용
    r = Client().get('/about/')
    check('HTML 에 CSP(보고 전용) 헤더', "default-src 'self'" in r.get('Content-Security-Policy-Report-Only', '')
          and not r.has_header('Content-Security-Policy'))
    check('JSON 에는 CSP 헤더 없음', not Client().get('/status/health.json').has_header('Content-Security-Policy-Report-Only'))
    rep = {'csp-report': {'violated-directive': 'script-src', 'blocked-uri': 'https://evil.example/x.js?q=secret',
                          'document-uri': 'https://beatmania.app/about/?token=abc'}}
    r = Client().post('/csp-report/', json.dumps(rep), content_type='application/csp-report')
    check('보고 받기 204', r.status_code == 204, str(r.status_code))
    check('보고 GET 405', Client().get('/csp-report/').status_code == 405)
    check('보고가 너무 크면 413', Client().post('/csp-report/', 'x' * 20000, content_type='application/json').status_code == 413)
    check('보고 JSON 아니면 400', Client().post('/csp-report/', 'nope', content_type='application/json').status_code == 400)
    from iidxrank import csp as _csp
    check('보고 로그에는 쿼리를 남기지 않는다', _csp._where('https://evil.example/x.js?q=secret') == 'evil.example/x.js')
    # 500 나던 입력
    tj = Client()
    tj.force_login(v)
    check('?days=abc 는 200', tj.get('/my-page/typing.json?days=abc').status_code == 200)
    # 403 화면
    r = csu.get('/withdraw/')
    check('403 이 사이트 모양으로', r.status_code == 403 and 'bm-auth-card' in r.content.decode())
    # 관리자 표 편집 API
    su_post = lambda d: csu.post('/update/rankedit/SP12H/', d).json()
    check('없어진 동작은 invalid access', su_post({'action': 'category', 'id': '1'}).get('message') == 'invalid access')
    check('숫자가 아닌 입력은 500 대신 메시지',
          su_post({'action': 'songcategory', 'id': 'x', 'category': 'y'}).get('message') == 'invalid parameter')
    check('없는 항목을 빼려 하면 500 대신 메시지',
          su_post({'action': 'songcategory', 'id': '0', 'category': '-1', 'songid': '0'}).get('message') == 'nothing to remove')
    # 관리자 명령 동시 실행 잠금
    caches['throttle'].add('runner:start-lock', 1, 30)
    run, err = _runner.start('cleanDuplicateSongs', {}, su)   # 잠금에 막혀 실제로 돌지 않는다
    check('시작 잠금을 누가 쥐고 있으면 실행하지 않는다', run is None and '이미 실행 중' in (err or ''), str(err))
    caches['throttle'].delete('runner:start-lock')
    # 기기 현황 API: 전용 그룹 계정만 허용, 일반 계정·superuser 403
    from django.contrib.auth.models import Group
    grp, _c = Group.objects.get_or_create(name='machine-status')
    dev_user = User.objects.create_user('zz_sec_dev')
    extra.append(dev_user)
    dev_user.set_unusable_password()
    dev_user.save()
    dev_user.groups.add(grp)
    body = json.dumps({'machine_id': 'zz-sec-machine', 'waiting_count': 3})
    mpost = lambda tok: Client().post('/api/v1/update-machine-status/', body, content_type='application/json',
                                      HTTP_AUTHORIZATION='Token ' + tok)
    check('기기 전용 계정 토큰은 허용', mpost(models.ApiToken.objects.create(user=dev_user).key).status_code == 200)
    plain = models.ApiToken.objects.get_or_create(user=v)[0].key
    check('일반 계정 토큰은 403', mpost(plain).status_code == 403)
    check('superuser 토큰은 이제 403(전용 계정만)', mpost(models.ApiToken.objects.get_or_create(user=su)[0].key).status_code == 403)
    models.MachineStatus.objects.filter(machine_id='zz-sec-machine').delete()
    if not grp.user_set.exclude(pk=dev_user.pk).exists() and _c:
        grp.delete()
    caches['throttle'].clear()

    print('=== 앱 받기 안내 (widgets/app_guide.html) ===')
    SYNC_URL = 'https://github.com/Coldlapse/beatmania.app-synchronizer/releases/latest'
    WIDGET_URL = 'https://github.com/Coldlapse/IIDXwidget/releases/latest'
    ga = Client()
    ga.force_login(v)
    for path, want in (('/sync/', [SYNC_URL]), ('/my-page/', [WIDGET_URL]), ('/account/token/', [SYNC_URL, WIDGET_URL])):
        body = ga.get(path).content.decode()
        check('%s 에 최신 버전 링크' % path, all(u in body for u in want) and '준비 중' not in body
              and '준비하고 있습니다' not in body)
    check('비로그인 동기화 페이지에도 앱 안내', SYNC_URL in Client().get('/sync/').content.decode())

    print('=== 1-2·2-1. 지운 페이지·JSON (유저 랭킹, 추천) ===')
    player.iidxmeid = 'user_zz_sec_a'
    player.save()
    for path in ('/userrank/', '/json/userlist/', '/json/recommend/user_zz_sec_a/SP/'):
        check('%s 404' % path, Client().get(path).status_code == 404)
finally:
    for x in [u, v] + [e for e in extra if User.objects.filter(pk=e.pk).exists()]:
        models.PlayRecord.objects.filter(player__user=x).delete()
        models.Player.objects.filter(user=x).delete()
        x.delete()

print('')
print('총 실패: %d' % len(fails))
