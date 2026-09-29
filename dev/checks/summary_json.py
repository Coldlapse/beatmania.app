# -*- coding: utf-8 -*-
"""/status/summary.json — 포트폴리오(coldlapse.dev)가 브라우저에서 읽는 규모 요약을 검사한다.

  1. 200, 필드와 타입, HEAD 도 200
  2. 값이 서비스 현황과 같다 — 가입자 수는 User 수, visits365 는 views.json 의
     '지난 365일' 합계와 같아야 한다(둘이 다르면 포트폴리오와 이 사이트가 어긋난다)
  3. CORS — coldlapse.dev 에서 온 요청에만 Access-Control-Allow-Origin 을 준다.
     다른 출처·출처 없음에는 주지 않는다. Vary: Origin, 캐시 기간
  4. 캐시 — 10분 안에는 다시 세지 않는다

    python dev/checks/summary_json.py
"""
import _bootstrap  # noqa: F401
import django

django.setup()

from unittest import mock  # noqa: E402

from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402

from iidxrank import models, views_status  # noqa: E402

URL = '/status/summary.json'
fails = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name,
                         (' — %s' % detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


c = Client()
cache.delete(views_status._SUMMARY_KEY)

# 1. 모양
r = c.get(URL)
check('200', r.status_code == 200, str(r.status_code))
d = r.json()
fields = ['users', 'playersWithRecord', 'records', 'charts', 'tables', 'visits365']
check('필드', all(isinstance(d.get(k), int) for k in fields), repr(d))
check('generatedAt', isinstance(d.get('generatedAt'), str))
check('HEAD 도 200', c.head(URL).status_code == 200)

# 2. 서비스 현황과 같은 값
check('users == User 수', d['users'] == models.User.objects.count())
check('records == PlayRecord 수', d['records'] == models.PlayRecord.objects.count())
year = c.get('/status/views.json', {'period': 'year'}).json()['visits']['total']
check('visits365 == views.json 지난 365일', d['visits365'] == year,
      '%s != %s' % (d['visits365'], year))

# 3. CORS
r = c.get(URL, HTTP_ORIGIN='https://coldlapse.dev')
check('coldlapse.dev 에는 허용', r.get('Access-Control-Allow-Origin') == 'https://coldlapse.dev',
      repr(r.get('Access-Control-Allow-Origin')))
r = c.get(URL, HTTP_ORIGIN='https://evil.example')
check('다른 출처에는 허용 안 함', r.get('Access-Control-Allow-Origin') is None)
r = c.get(URL)
check('출처 없으면 허용 헤더 없음', r.get('Access-Control-Allow-Origin') is None)
check('Vary: Origin', 'Origin' in (r.get('Vary') or ''), repr(r.get('Vary')))
check('Cache-Control 10분', r.get('Cache-Control') == 'public, max-age=600',
      repr(r.get('Cache-Control')))

# 4. 캐시 — 이미 채워진 상태에서 다시 부르면 세지 않는다
with mock.patch.object(views_status, '_service_numbers',
                       side_effect=AssertionError('다시 셈')) as m:
    r = c.get(URL)
check('캐시 안에서는 다시 세지 않음', r.status_code == 200 and m.call_count == 0)
cache.delete(views_status._SUMMARY_KEY)

print('')
print('총 실패: %d' % len(fails))
