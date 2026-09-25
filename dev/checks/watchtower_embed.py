# -*- coding: utf-8 -*-
"""서비스 현황의 '외부 감시탑 → Cloudflare 상태' 칸을 검사한다.

네트워크는 막고(requests.get 을 가짜로) 네 경우를 본다.
  1. 정상 응답 → 칸이 그려지고 거점·장애가 나온다. 출처 줄이 있다
  2. 남의 데이터 — Cloudflare 상태 페이지가 아닌 링크는 싣지 않고, 이름은 이스케이프
  3. 감시탑 실패 → 칸만 숨고 페이지는 200
  4. 실패도 캐시 → 60초 안에는 다시 붙지 않는다(감시탑이 죽은 동안 요청마다 기다리지 않게)

    python dev/checks/watchtower_embed.py
"""
import _bootstrap  # noqa: F401
import django

django.setup()

from unittest import mock  # noqa: E402

import requests  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402

from iidxrank import views_status  # noqa: E402

fails = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name,
                         (' — %s' % detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


class Resp:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


GOOD = {
    'at': 1790369094949,
    'cloudflare': {
        'components': [
            {'name': 'Seoul, South Korea - (ICN)', 'status': 'up'},
            {'name': 'Hong Kong - (HKG)', 'status': 'degraded'},
            {'name': '<script>x</script>', 'status': 'down'},
        ],
        'incidents': [
            {'name': 'Network Performance Degradation', 'status': 'identified',
             'url': 'https://www.cloudflarestatus.com/incidents/abc'},
            {'name': 'Phish', 'status': 'x', 'url': 'https://evil.example/'},
        ],
    },
}

c = Client()

print('=== 1·2. 정상 응답 ===')
cache.delete(views_status._WT_KEY)
with mock.patch.object(views_status.requests, 'get', return_value=Resp(GOOD)) as g:
    page = c.get('/status/').content.decode()
check('Cloudflare 칸이 그려짐', 'bm-cf-grid' in page)
check('거점 이름', 'Seoul, South Korea - (ICN)' in page and 'Hong Kong - (HKG)' in page)
check('상태 → 점 색 (degraded)', 'bm-health-degraded' in page)
check('장애 링크는 cloudflarestatus 만', 'cloudflarestatus.com/incidents/abc' in page
      and 'evil.example' not in page)
check('남의 이름은 이스케이프', '<script>x</script>' not in page and '&lt;script&gt;' in page)
check('출처 줄', '데이터 출처' in page and 'stats.polygon.nz' in page)
check('감시탑 안내 문구', '외부 감시탑을 따로 두었습니다' in page)

print('=== 3·4. 감시탑 실패 ===')
cache.delete(views_status._WT_KEY)
with mock.patch.object(views_status.requests, 'get',
                       side_effect=requests.ConnectionError('down')) as g:
    r = c.get('/status/')
    page = r.content.decode()
    r2 = c.get('/status/')
    calls = g.call_count
check('페이지는 200', r.status_code == 200 and r2.status_code == 200)
check('Cloudflare 칸은 숨음', 'bm-cf-grid' not in page)
check('안내 문구와 링크는 그대로', '외부 감시탑 보기' in page)
check('실패도 캐시 — 두 번 열어도 한 번만 붙음', calls == 1, str(calls))

cache.delete(views_status._WT_KEY)
with mock.patch.object(views_status.requests, 'get', return_value=Resp({'cloudflare': None})):
    page = c.get('/status/').content.decode()
check('모양이 다른 응답 → 칸만 숨음', 'bm-cf-grid' not in page)
cache.delete(views_status._WT_KEY)

print('')
print('총 실패: %d' % len(fails))
