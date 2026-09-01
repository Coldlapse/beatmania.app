# -*- coding: utf-8 -*-
"""새 URL 체계와 옛 주소 301 리다이렉트를 검증한다."""
import _bootstrap  # noqa: F401  (sys.path / 설정 모듈)
import django

django.setup()

from django.contrib.auth.models import User
from django.test import Client

from iidxrank.models import Player

c = Client(raise_request_exception=False)

print('=== 새 주소 ===')
NEW = [
    ('/', 200), ('/table/SP12H/', 200), ('/table/SP12H/embed/', 200),
    ('/table/SP12H/json/', 200),
    ('/u/sadang/', 200), ('/u/sadang/table/SP12H/', 200),
    ('/u/sadang/table/SP12H/embed/', 200), ('/u/sadang/table/SP12H/json/', 200),
    ('/login/', 200), ('/join/', 200), ('/status/', 200), ('/privacy/', 200),
    ('/converter/', 200), ('/about/', 200), ('/songrank/', 200),
    ('/userrank/', 200), ('/musiclist/', 200), 
    ('/json/userlist/', 200),
]
bad = 0
for u, want in NEW:
    got = c.get(u).status_code
    ok = got == want
    bad += not ok
    print('  %-34s %s %s' % (u, got, '' if ok else '<-- 기대 %s' % want))

print('')
print('=== 옛 주소 → 301 영구 리다이렉트 ===')
OLD = [
    ('/!/', '/'),
    ('/!/SP12H/', '/table/SP12H/'),
    ('/!/SP12H/table/', '/table/SP12H/embed/'),
    ('/!/SP12H/json/', '/table/SP12H/json/'),
    ('/!/login/', '/login/'),
    ('/!/join/', '/join/'),
    ('/!/account/', '/account/'),
    ('/!/my-page/', '/my-page/'),
    ('/!/analytics/', '/analytics/'),
    ('/!/roadmap', '/roadmap/'),
    ('/!/converter/', '/converter/'),
    ('/!/manage/', '/manage/'),
    ('/!/status/abc/', '/status/abc/'),
    ('/!/rankedit/5/', '/rankedit/5/'),
    ('/sadang/', '/u/sadang/'),
    ('/sadang/SP12H/', '/u/sadang/table/SP12H/'),
    ('/sadang/SP12H/table/', '/u/sadang/table/SP12H/embed/'),
    ('/sadang/SP12H/json/', '/u/sadang/table/SP12H/json/'),
    # 이름이 바뀌며 옮긴 주소
    ('/analytics/', '/status/'),
    ('/roadmap/', '/about/'),
]
for u, want in OLD:
    r = c.get(u)
    loc = r.get('Location', '')
    ok = r.status_code == 301 and loc == want
    bad += not ok
    print('  %-30s %s %-34s %s'
          % (u, r.status_code, loc, '' if ok else '<-- 기대 301 %s' % want))

print('')
print('=== 쿼리스트링 보존 ===')
r = c.get('/!/analytics/?period=weekly')
print('  /!/analytics/?period=weekly -> %s %s  %s'
      % (r.status_code, r.get('Location'),
         '✅' if r.get('Location') == '/analytics/?period=weekly' else '❌'))

print('')
print('=== 옛 주소는 존재 여부와 무관하게 301 ===')
# 옛 주소는 존재 여부와 무관하게 301 로 넘긴다 — 여기서 구별하면 계정 열거가 된다
for u in ('/nosuchuser/', '/nosuchuser/SP12H/', '/typo/'):
    r = c.get(u)
    ok = r.status_code == 301
    print('  %-24s -> %s %s (존재 여부를 흘리지 않음)'
          % (u, r.status_code, '✅' if ok else '❌'))
    bad += not ok

print('')
print('=== 비공개 프로필 ===')
# 라이브 데이터에는 시드 계정('hidden')이 없다. 실제 비공개 계정을 고른다.
p = Player.objects.filter(private=True).select_related('user').first()
assert p is not None, '비공개 계정이 하나도 없다'
hidden = p.user.username
print('  비공개 표본: %s (private=%s)' % (hidden, p.private))
for url in ('/u/%s/' % hidden, '/u/%s/table/SP12H/' % hidden, '/u/nosuchuser/'):
    r = c.get(url)
    body = r.content.decode('utf-8', 'replace')
    ok = r.status_code == 404 and '프로필을 볼 수 없습니다' in body
    bad += not ok
    print('  %-30s -> %s / 안내문 %s %s'
          % (url, r.status_code,
             '있음' if '프로필을 볼 수 없습니다' in body else '없음',
             '✅' if ok else '❌'))

print('')
print('=== 가입 폼 안심 문구 ===')
body = c.get('/join/').content.decode('utf-8')
for probe in ['아이디는 공개 주소가 됩니다', 'bm-id-reassure', '프로필 비공개',
              'beatmania.app/u/']:
    ok = probe in body
    bad += not ok
    print('  %-30s %s' % (probe, '✅' if ok else '❌'))

print('')
print('총 실패: %d' % bad)
