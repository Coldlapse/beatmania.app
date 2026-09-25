# -*- coding: utf-8 -*-
"""/status/health.json — 외부 감시탑이 읽는 경로를 검사한다.

감시탑은 응답 코드로 사이트와 DB 를 나눠 읽는다(200 정상 / 503 DB 만 장애 /
그 밖의 5xx·무응답 사이트 장애). 그래서 코드와 모양이 곧 계약이다.

1. 정상        200, 모양, note 없음, Cache-Control: no-store, HEAD 도 200
2. 흉내 장애   check_db_isolated 가 예외를 내면 503, checks 는 빈 배열
3. 실제 장애   하위 프로세스에서 **진짜 연결로** 돌린다. mock 으로는 "쿠키 없는
               요청이 미들웨어에서 DB 를 안 건드린다" 를 증명할 수 없다. 흉내 낸
               check_db 앞에서 누가 DB 를 건드려도 연결은 살아 있으니 통과해 버린다.
     a. 닫힌 포트      연결 거부 → 곧바로 503
     b. 응답 없는 주소 SYN 에 답이 없음 → connect_timeout(3초) 안에 503.
                       PyMySQL 기본값 10초면 감시탑 제한(10초)을 넘긴다.
     c. 멈춘 서버      TCP 는 받고 인사(handshake)를 안 보냄 → 얼어붙은 mysqld.
                       PyMySQL 의 connect_timeout 은 TCP 연결에만 걸려서 앱
                       연결로는 무제한 묶인다. 그래서 이 경로는 read_timeout 을
                       건 별도 연결을 쓴다 → 약 3초에 503.

    python dev/checks/health_json.py
"""
import json
import os
import socket
import subprocess
import sys
import threading
import time

import _bootstrap  # noqa: F401  (sys.path / 설정 모듈)

URL = '/status/health.json'
fails = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name,
                         (' — ' + detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


def has_key(obj, key):
    if isinstance(obj, dict):
        return key in obj or any(has_key(v, key) for v in obj.values())
    if isinstance(obj, list):
        return any(has_key(v, key) for v in obj)
    return False


# --- 하위 프로세스: DB 를 실제로 끊은 채 한 번 요청하고 결과를 JSON 으로 낸다 ---
if len(sys.argv) > 1 and sys.argv[1] == '--child':
    import django
    django.setup()
    from django.test import Client
    t0 = time.time()
    r = Client(raise_request_exception=False).get(URL)
    print(json.dumps({'code': r.status_code, 'body': r.content.decode(),
                      'cc': r.get('Cache-Control'),
                      'sec': round(time.time() - t0, 2)}))
    sys.exit(0)


def run_child(port, host='127.0.0.1', timeout=60):
    env = dict(os.environ, DEV_DB_PORT=str(port), DEV_DB_HOST=host)
    try:
        p = subprocess.run([sys.executable, os.path.abspath(__file__), '--child'],
                           env=env, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, 'timeout %ss' % timeout
    out = p.stdout.decode('utf-8', 'replace').strip().splitlines()
    if p.returncode != 0 or not out:
        return None, p.stderr.decode('utf-8', 'replace')[-600:]
    return json.loads(out[-1]), ''


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def silent_server():
    """연결은 받아 두고 아무 말도 하지 않는 서버. 얼어붙은 mysqld 흉내."""
    srv = socket.socket()
    srv.bind(('127.0.0.1', 0))
    srv.listen(8)
    held = []

    def loop():
        while True:
            try:
                c, _ = srv.accept()
            except OSError:
                return
            held.append(c)
    threading.Thread(target=loop, daemon=True).start()
    return srv, srv.getsockname()[1]


if __name__ == '__main__':
    import django
    django.setup()
    from unittest import mock
    from django.test import Client
    from iidxrank import health

    c = Client(raise_request_exception=False)

    print('=== 1. 정상 ===')
    r = c.get(URL)
    body = r.json()
    check('GET 200', r.status_code == 200, str(r.status_code))
    check('Cache-Control: no-store', r.get('Cache-Control') == 'no-store',
          str(r.get('Cache-Control')))
    check('Content-Type json', r['Content-Type'].startswith('application/json'))
    check('최상위 키', set(body) == {'generatedAt', 'live', 'checks'}, str(set(body)))
    check('live.db ok', body['live']['db']['status'] == 'ok', str(body['live']))
    check('live.db.latencyMs 정수',
          isinstance(body['live']['db']['latencyMs'], int))
    check('generatedAt 은 KST 초 단위',
          body['generatedAt'].endswith('+09:00') and '.' not in body['generatedAt'],
          body['generatedAt'])
    targets = [x['target'] for x in body['checks']]
    check('checks 대상은 health.CHECKS 안, 중복 없음',
          set(targets) <= set(health.CHECKS) and len(targets) == len(set(targets)),
          str(targets))
    check('checks 항목 키',
          all(set(x) == {'target', 'status', 'latencyMs', 'checkedAt'}
              for x in body['checks']), str(body['checks'][:1]))
    check('응답 어디에도 note 없음', not has_key(body, 'note'))
    print('     checks %d개: %s' % (len(targets), ', '.join(targets) or '(없음)'))

    r = c.head(URL)
    check('HEAD 200', r.status_code == 200, str(r.status_code))
    check('HEAD 에도 no-store', r.get('Cache-Control') == 'no-store')
    check('POST 405', c.post(URL).status_code == 405)

    # 감시탑 요청 모양 그대로(쿠키 없음, 전용 UA)
    r = c.get(URL, HTTP_USER_AGENT='polygon-watchtower/1 (+https://status.polygon.nz)')
    check('감시탑 UA 로 200', r.status_code == 200)

    print('=== 2. 흉내 장애 (check_db_isolated 예외) ===')
    boom = mock.patch.object(health, 'check_db_isolated',
                             side_effect=Exception('OperationalError: secret-host:3306'))
    with boom:
        r = c.get(URL)
    body = r.json()
    check('503', r.status_code == 503, str(r.status_code))
    check('live.db down', body['live']['db']['status'] == 'down')
    check('checks 빈 배열', body['checks'] == [])
    check('예외 문구가 새지 않음', 'secret-host' not in r.content.decode())
    check('no-store', r.get('Cache-Control') == 'no-store')

    # 시계열 읽기만 실패하는 경우: live 는 살아 있으니 200 유지
    from iidxrank import models
    with mock.patch.object(models.HealthCheck.objects, 'filter',
                           side_effect=Exception('boom')):
        r = c.get(URL)
    check('checks 읽기 실패 → 200 · 빈 배열',
          r.status_code == 200 and r.json()['checks'] == [], str(r.status_code))

    print('=== 3a. 실제 장애: 닫힌 포트 (연결 거부) ===')
    res, err = run_child(free_port())
    if res is None:
        check('하위 프로세스 실행', False, err)
    else:
        b = json.loads(res['body'])
        print('     %.2fs, %s' % (res['sec'], res['code']))
        check('503 (500 아님 — 미들웨어가 DB 를 안 건드림)', res['code'] == 503,
              res['body'][:300])
        check('live.db down · checks []',
              b.get('live', {}).get('db', {}).get('status') == 'down'
              and b.get('checks') == [])
        check('no-store', res['cc'] == 'no-store')

    print('=== 3b. 실제 장애: 응답 없는 주소 (connect_timeout) ===')
    # 사설 대역의 쓰이지 않는 주소. SYN 이 나가고 아무 답도 오지 않는다.
    res, err = run_child(3306, host='10.255.255.1')
    if res is None:
        check('하위 프로세스 실행', False, err)
    else:
        b = json.loads(res['body'])
        ms = b.get('live', {}).get('db', {}).get('latencyMs', -1)
        print('     요청 %.2fs, latencyMs %s, %s' % (res['sec'], ms, res['code']))
        check('503', res['code'] == 503, res['body'][:300])
        check('connect_timeout 안에 끝남 (2.5~6초, 감시탑 10초 이내)',
              2500 <= ms <= 6000, str(ms))

    print('=== 3c. 실제 장애: 멈춘 서버 (별도 연결의 read_timeout) ===')
    srv, port = silent_server()
    try:
        res, err = run_child(port, timeout=30)
    finally:
        srv.close()
    if res is None:
        check('하위 프로세스 실행 (30초 안에 끝남)', False, err)
    else:
        b = json.loads(res['body'])
        ms = b.get('live', {}).get('db', {}).get('latencyMs', -1)
        print('     요청 %.2fs, latencyMs %s, %s' % (res['sec'], ms, res['code']))
        check('503', res['code'] == 503, res['body'][:300])
        check('read_timeout 안에 끝남 (2.5~7초, 감시탑 10초 이내)',
              2500 <= ms <= 7000, str(ms))

    print('')
    print('총 실패: %d' % len(fails))
    sys.exit(1 if fails else 0)
