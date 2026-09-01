# -*- coding: utf-8 -*-
"""라이브 데이터가 올라간 MySQL 위에서 주요 화면과 성능을 잰다."""
import time

import _bootstrap  # noqa: F401  (sys.path / 설정 모듈)
import django

django.setup()

from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.db import connection

from django.contrib.auth.models import User
from iidxrank.models import Player, RankTable

c = Client(raise_request_exception=False)

# 실데이터에서 공개 사용자 하나를 고른다
pub = Player.objects.filter(private=False).select_related('user').first()
name = pub.user.username if pub else 'sadang'
tables = list(RankTable.objects.values_list('tablename', flat=True))
print('공개 사용자 표본 : %s' % name)
print('서열표 %d개      : %s' % (len(tables), ', '.join(tables[:8])))
print('')

URLS = [
    ('/', '메인'),
    ('/table/SP12H/', '서열표'),
    ('/table/SP12H/json/', '서열표 JSON'),
    ('/u/%s/' % name, '타인 프로필'),
    ('/u/%s/table/SP12H/' % name, '타인 서열표'),
    ('/json/userlist/', '유저목록 JSON'),
    ('/login/', '로그인'),
    ('/join/', '가입'),
    ('/status/', '서비스 현황'),
    ('/musiclist/', '곡목록'),
    ('/songrank/', '곡랭킹'),
    ('/userrank/', '유저랭킹'),
]

print('%-28s %-14s %6s %8s %7s' % ('URL', '이름', '상태', '시간(ms)', '쿼리'))
print('-' * 72)
bad = 0
for url, label in URLS:
    with CaptureQueriesContext(connection) as ctx:
        t0 = time.time()
        r = c.get(url)
        dt = (time.time() - t0) * 1000
    ok = r.status_code == 200
    bad += not ok
    print('%-28s %-14s %6s %8.0f %7d %s'
          % (url, label, r.status_code, dt, len(ctx), '' if ok else '<-- 실패'))

print('')
print('=== 대소문자 콜레이션 (SQLite 로는 재현 불가하던 것) ===')
for u in (name, name.upper(), name.capitalize()):
    r = c.get('/u/%s/' % u)
    print('  /u/%-14s -> %s' % (u + '/', r.status_code))

print('')
print('실패 %d / 총 %d' % (bad, len(URLS)))
