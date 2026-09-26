# -*- coding: utf-8 -*-
"""게임 기록 동기화(tracker.tsv → 서열표 기록)를 검사한다.

dev DB 의 실제 곡으로 가짜 tracker.tsv 를 만들어 넣는다. 머리줄은 Reflux
Tracker.cs 가 쓰는 것 그대로다. 까다로운 경우를 일부러 섞는다:
  - 겉모양만 같은 다른 글자 (DB 'uәn' 키릴 ә ↔ 파일 'uən' 라틴 ə)
  - 대소문자만 다른 두 곡 ('Take Me Higher' 1003 / 'take me higher' 3157)
  - 전각 문자, 레벨 10 미만, 안 친 채보(NP·0점), 모르는 곡, PFC, MAX 판정
그리고 반영 규칙(좋을 때만 올림, 멱등)과 API·웹 경로를 본다.

임시 사용자 zz_sync_* 를 만들고 끝나면 지운다.

    python dev/checks/records_import.py
"""
import _bootstrap  # noqa: F401
import django

django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402

from iidxrank import models, records_import  # noqa: E402
from iidxrank.rankpage import newplayer  # noqa: E402

SLOTS = ['SPB', 'SPN', 'SPH', 'SPA', 'SPL', 'DPN', 'DPH', 'DPA', 'DPL']
COLS = ['Unlocked', 'Rating', 'Lamp', 'Letter', 'EX Score', 'Miss Count',
        'Note Count', 'DJ Points']
HEAD = ('title\tType\tLabel\tCost Normal\tCost Hyper\tCost Another\t'
        'SP DJ Points\tDP DJ Points\t'
        + '\t'.join('%s %s' % (s, c) for s in SLOTS for c in COLS))

fails = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name,
                         (' — %s' % detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


def row(title, charts):
    """charts: {slot: (level, lamp, letter, ex, notes)}"""
    cells = []
    for s in SLOTS:
        if s in charts:
            lv, lamp, letter, ex, notes = charts[s]
            cells += ['TRUE', str(lv), lamp, letter, str(ex), '0', str(notes), '0']
        else:
            cells += [''] * 8
    return '\t'.join([title, 'Bits', 'Bits', '', '', '', '0', '0'] + cells)


def song(sid):
    return models.Song.objects.get(id=sid)


def rec(player, sid):
    return (models.PlayRecord.objects.filter(player=player, song_id=sid)
            .values_list('playclear', 'playscore').first())


def ex(player, sid):
    return models.PlayRecord.objects.filter(player=player, song_id=sid).values_list('exscore', flat=True).first()


# 기준 곡들 (dev DB = 라이브 덤프)
spa12 = models.Song.objects.filter(songtype='SPA', songlevel=12).exclude(
    songtitle__in=['uәn']).order_by('id')
A, B = spa12[0], spa12[1]                       # 평범한 곡 둘
UEN = models.Song.objects.get(songtitle='uәn', songtype='SPA')   # 키릴 ә, lv12
TMH_UP = song(1003)                             # 'Take Me Higher' SPA 10
TMH_LO = song(3157)                             # 'take me higher' SPA 10
assert TMH_UP.songtitle == 'Take Me Higher' and TMH_LO.songtitle == 'take me higher'

tsv = '\n'.join([
    HEAD,
    # A: HC, AA  /  같은 줄에 레벨 9 채보(버려야 함)와 SPB
    row(A.songtitle, {'SPA': (12, 'HC', 'AA', 3000, 2000),
                      'SPH': (9, 'FC', 'AAA', 1800, 1000),
                      'SPB': (3, 'FC', 'AAA', 600, 300)}),
    # B: PFC + 만점 → FC(7) / MAX(8)
    row(B.songtitle, {'SPA': (12, 'PFC', 'AAA', 4000, 2000)}),
    # 라틴 ə 로 쓴 uən → DB 의 키릴 ә 와 맞아야 함
    row('uən', {'SPA': (12, 'EC', 'A', 2500, 2000)}),
    # 대소문자만 다른 두 곡이 서로 섞이지 않아야 함
    row('Take Me Higher', {'SPA': (10, 'NC', 'B', 1000, 1000)}),
    row('take me higher', {'SPA': (10, 'EX', 'AA', 1600, 1000)}),
    # 안 친 채보(NP, 0점) — 기록을 만들면 안 됨
    row(song(18).songtitle if song(18).id not in (A.id, B.id) else 'zz',
        {'DPA': (12, 'NP', 'F', 0, 2000)}),
    # 모르는 곡
    row('존재하지 않는 곡 zz', {'SPA': (12, 'HC', 'AA', 3000, 2000)}),
    # 모르는 램프 — 추측하지 않고 버림
    row(A.songtitle, {'DPA': (12, 'WHAT', 'AA', 3000, 2000)}),
]) + '\n'

u = User.objects.create_user('zz_sync_check', password='x-Unused-123')
try:
    player = newplayer(u)

    print('=== 1. 파싱 ===')
    rows = records_import.parse(tsv)
    slots = sorted({r[1] for r in rows})
    check('레벨 10 미만·SPB·NP·모르는 램프는 버림', len(rows) == 6, str(rows))
    check('SPB 없음', 'SPB' not in slots, str(slots))

    print('=== 2. 처음 반영 ===')
    r = records_import.apply(u, tsv, models.RecordSync.WEB)
    print('     ', {k: v for k, v in r.items() if k != 'unmatched_titles'})
    check('새 기록 5개', r['created'] == 5, str(r))
    check('못 찾은 곡 1개(모르는 곡)', r['unmatched'] == 1 and '존재하지' in r['unmatched_titles'][0],
          str(r['unmatched_titles']))
    check('A: HC(5) / AA(6)', rec(player, A.id) == (5, 6), str(rec(player, A.id)))
    check('B: PFC→FC(7) / 만점→MAX(8)', rec(player, B.id) == (7, 8), str(rec(player, B.id)))
    check('uən(라틴) → DB uәn(키릴)', rec(player, UEN.id) == (3, 5), str(rec(player, UEN.id)))
    check("'Take Me Higher' → 1003 에 NC(4)/B(4)", rec(player, TMH_UP.id) == (4, 4),
          str(rec(player, TMH_UP.id)))
    check("'take me higher' → 3157 에 EX(6)/AA(6)", rec(player, TMH_LO.id) == (6, 6),
          str(rec(player, TMH_LO.id)))
    check('NP 채보는 기록을 만들지 않음', rec(player, 18) is None or 18 in (A.id, B.id))
    check('이력 1행', models.RecordSync.objects.filter(user=u).count() == 1)

    print('=== 3. 멱등 ===')
    r2 = records_import.apply(u, tsv, models.RecordSync.WEB)
    check('같은 파일 → 새 0 · 갱신 0 · 변화 없음 5', (r2['created'], r2['improved'], r2['unchanged']) == (0, 0, 5),
          str(r2))

    print('=== 4. 낮추지 않음 / 좋아지면 올림 ===')
    models.PlayRecord.objects.filter(player=player, song_id=A.id).update(playclear=7, playscore=8)
    worse_better = '\n'.join([HEAD,
        row(A.songtitle, {'SPA': (12, 'EC', 'A', 2000, 2000)}),        # A 는 손으로 FC/MAX → 그대로
        row('Take Me Higher', {'SPA': (10, 'HC', 'A', 1300, 1000)}),   # NC→HC 오름, B→A 오름
    ])
    r3 = records_import.apply(u, worse_better, models.RecordSync.APP)
    check('직접 넣은 FC/MAX 를 낮추지 않음', rec(player, A.id) == (7, 8), str(rec(player, A.id)))
    check('더 좋은 기록은 올림 (HC 5 / A 5)', rec(player, TMH_UP.id) == (5, 5), str(rec(player, TMH_UP.id)))
    check('갱신 1 · 변화 없음 1', (r3['improved'], r3['unchanged']) == (1, 1), str(r3))

    print('=== 4-1. EX SCORE ===')
    check('처음 반영에서 EX SCORE 도 저장 (A 3000)', ex(player, A.id) == 3000, str(ex(player, A.id)))
    check('낮은 EX 는 무시 (A 3000 유지)', ex(player, A.id) == 3000, str(ex(player, A.id)))
    check('높은 EX 는 올림 (Take Me Higher 1300)', ex(player, TMH_UP.id) == 1300, str(ex(player, TMH_UP.id)))
    # 손으로 0 을 넣은 기록에 EX 0 이 오면 0 을 그대로 둔다(n/a 로 지우지 않는다)
    models.PlayRecord.objects.filter(player=player, song_id=B.id).update(exscore=0)
    records_import.apply(u, chr(10).join([HEAD, row(B.songtitle, {'SPA': (12, 'F', 'F', 0, 2000)})]),
                         models.RecordSync.APP)
    check('EX 0 이 와도 손으로 넣은 0 유지', ex(player, B.id) == 0, str(ex(player, B.id)))

    print('=== 4-2. 팝업의 EX SCORE 저장 (/modify/ action=exscore) ===')
    import json as _json
    m = Client()
    m.force_login(u)
    models.AccountSecurity.objects.update_or_create(user=u, defaults={'newrulepassed': True})
    post = lambda sid, v: m.post('/modify/', {'action': 'exscore',
                                              'v': _json.dumps({'id': sid, 'exscore': v})}).json()
    rj = post(A.id, 1234)
    check('저장 → 1234 (낮춰도 그 값)', rj.get('code') == 0 and ex(player, A.id) == 1234, str(rj))
    rj = post(A.id, None)
    check('빈 값 → n/a(None)', rj.get('code') == 0 and ex(player, A.id) is None, str(rj))
    rj = post(A.id, -1)
    check('음수 거부', rj.get('code') == 1 and ex(player, A.id) is None, str(rj))
    rj = post(A.id, 10000)
    check('상한 초과 거부', rj.get('code') == 1, str(rj))
    rj = m.post('/modify/', {'action': 'exscore', 'v': 'nope'}).json()
    check('형식 오류 거부', rj.get('code') == 1, str(rj))
    rj = Client().post('/modify/', {'action': 'exscore', 'v': _json.dumps({'id': A.id, 'exscore': 1})}).json()
    check('비로그인 거부', rj.get('code') == 1, str(rj))
    html = m.get('/rankedit/%d/' % A.id).content.decode()
    check('팝업: n/a 표기 · CLEAR LAMP · DJ RANK · EX SCORE',
          'EX SCORE : <b id="ex-current">n/a</b>' in html and 'CLEAR LAMP' in html and 'DJ RANK' in html, html[:400])
    post(A.id, 2500)
    html = m.get('/rankedit/%d/' % A.id).content.decode()
    check('팝업: 저장값 표기', 'EX SCORE : <b id="ex-current">2500</b>' in html, html[html.find('EX SCORE'):][:120])
    check('없는 곡 팝업 500 아님', m.get('/rankedit/99999999/').status_code == 200)

    print('=== 5. 형식 오류 ===')
    for bad in ('', 'hello\tworld\n1\t2\n'):
        try:
            records_import.parse(bad)
            check('형식 오류 %r' % bad[:10], False, '예외가 안 남')
        except records_import.TsvError:
            check('형식 오류 %r → TsvError' % bad[:10], True)

    print('=== 6. API ===')
    models.RecordSync.objects.filter(user=u).delete()
    tok = models.ApiToken.objects.create(user=u).key
    c = Client()
    url = '/api/v1/records/'
    ct = 'text/tab-separated-values; charset=utf-8'
    check('토큰 없음 401', c.post(url, tsv, content_type=ct).status_code == 401)
    check('틀린 토큰 401', c.post(url, tsv, content_type=ct,
                             HTTP_AUTHORIZATION='Token nope').status_code == 401)
    check('GET 405', c.get(url, HTTP_AUTHORIZATION='Token ' + tok).status_code == 405)
    rr = c.post(url, tsv.encode('utf-8'), content_type=ct, HTTP_AUTHORIZATION='Token ' + tok)
    check('정상 200 + 요약', rr.status_code == 200 and rr.json().get('unchanged', -1) >= 0,
          '%s %s' % (rr.status_code, rr.content[:200]))
    rr = c.post(url, tsv, content_type=ct, HTTP_AUTHORIZATION='Token ' + tok)
    check('10초 안에 또 → 429 + Retry-After', rr.status_code == 429 and rr.has_header('Retry-After'),
          str(rr.status_code))
    models.RecordSync.objects.filter(user=u).delete()
    rr = c.post(url, 'not a tsv', content_type=ct, HTTP_AUTHORIZATION='Token ' + tok)
    check('형식 오류 400', rr.status_code == 400, str(rr.status_code))
    rr = c.post(url, b'\xff\xfe\x00bad', content_type=ct, HTTP_AUTHORIZATION='Token ' + tok)
    check('UTF-8 아님 400', rr.status_code == 400, str(rr.status_code))
    rr = c.post(url, b'x' * (records_import.MAX_BYTES + 1), content_type=ct,
                HTTP_AUTHORIZATION='Token ' + tok)
    check('너무 큼 → 400 (500 아님)', rr.status_code == 400, str(rr.status_code))

    print('=== 6-1. 토큰 확인 API ===')
    rr = c.get('/api/v1/me/', HTTP_AUTHORIZATION='Token ' + tok)
    check('me 200 · 아이디·프로필 주소', rr.status_code == 200 and rr.json() ==
          {'username': u.username, 'profile_url': '/u/%s/' % u.username}, str(rr.content[:120]))
    check('me 에 이메일 없음', b'@' not in rr.content)
    check('me 틀린 토큰 401', c.get('/api/v1/me/', HTTP_AUTHORIZATION='Token nope').status_code == 401)
    check('me POST 405', c.post('/api/v1/me/', HTTP_AUTHORIZATION='Token ' + tok).status_code == 405)

    print('=== 7. 웹 ===')
    models.RecordSync.objects.filter(user=u).delete()
    check('비로그인 GET 200', Client().get('/sync/').status_code == 200)
    w = Client()
    w.force_login(u)
    models.AccountSecurity.objects.update_or_create(user=u, defaults={'newrulepassed': True})
    up = SimpleUploadedFile('tracker.tsv', tsv.encode('utf-8'), 'text/tab-separated-values')
    rr = w.post('/sync/', {'tracker': up})
    check('업로드 → 302 /sync/', rr.status_code == 302 and rr['Location'].endswith('/sync/'),
          '%s %s' % (rr.status_code, rr.get('Location')))
    page = w.get('/sync/').content.decode()
    check('결과 화면에 요약·이력', '반영했습니다' in page and '최근 동기화' in page)
    check('결과는 한 번만 보임(새로고침)', '반영했습니다' not in w.get('/sync/').content.decode())
finally:
    models.PlayRecord.objects.filter(player__user=u).delete()
    models.Player.objects.filter(user=u).delete()
    u.delete()

print('')
print('총 실패: %d' % len(fails))
