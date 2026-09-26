# -*- coding: utf-8 -*-
"""로그인·인증 메일·인증 코드의 횟수 제한 (2026-09-26, 보안 검토 2-b).

횟수는 'throttle' 캐시(DB 테이블 bm_throttle)에 둔다. 기본 캐시는 gunicorn 워커(5개)마다
따로 있는 메모리라, 거기에 세면 제한이 사실상 5배가 되고 재시작하면 초기화된다.
테이블은 `manage.py createcachetable` 이 만든다(배포 워크플로가 매번 돌린다 — 이미 있으면 그대로).

창(window)은 고정 창이다: 처음 센 때부터 window 초 동안 모은다. '최근 15분' 을 정확히 재는
미끄러지는 창보다 거칠지만, 여기서 막으려는 것(수백·수천 번의 추측과 발송)에는 충분하다.
여러 워커가 동시에 세면 한두 번 덜 셀 수 있다(읽고 쓰기 사이가 원자적이지 않다) — 같은 이유로 허용한다.

기준 값은 사용자가 정했다(2026-09-26). 근거는 각 항목 옆에.
"""
import hashlib
import time

from django.core.cache import caches

# (횟수, 창 초)
LOGIN_PAIR = (10, 15 * 60)     # 같은 (아이디, IP) 로 15분에 10번 틀리면 그 조합만 15분 잠금
LOGIN_IP = (30, 60 * 60)       # 한 IP 가 아이디 상관없이 1시간에 30번 틀리면 1시간 잠금
MAIL_IP = (10, 60 * 60)        # 인증 메일 요청 IP 당 1시간 10번
MAIL_ADDR = (5, 60 * 60)       # 같은 주소로 1시간 5번(목적 불문)
MAIL_DAY = (100, 24 * 60 * 60)  # 사이트 전체 하루 100통 — 역대 하루 최대 7통(2026-09-26 실측)
CODE_FAIL = (10, 24 * 60 * 60)  # 같은 (주소, 목적)의 코드 오입력 하루 10번(코드가 바뀌어도 누적)


def _cache():
    return caches['throttle']


def _key(kind, *parts):
    # 아이디·주소가 캐시 키 규칙(길이·글자)에 걸리지 않게 해시한다
    h = hashlib.sha256('\x1f'.join(str(p) for p in parts).encode('utf-8')).hexdigest()[:40]
    return 'thr:%s:%s' % (kind, h)


def _get(key):
    v = _cache().get(key)
    if not v or v[1] <= time.time():
        return None
    return v


def count(kind, *parts):
    v = _get(_key(kind, *parts))
    return v[0] if v else 0


def seconds_left(kind, *parts):
    v = _get(_key(kind, *parts))
    return max(0, int(v[1] - time.time() + 0.999)) if v else 0


def hit(kind, window, *parts):
    """한 번 센다. 센 뒤의 횟수를 돌려준다."""
    key = _key(kind, *parts)
    v = _get(key)
    now = time.time()
    if v is None:
        v = (0, now + window)
    v = (v[0] + 1, v[1])
    _cache().set(key, v, timeout=max(1, int(v[1] - now + 1)))
    return v[0]


def reset(kind, *parts):
    _cache().delete(_key(kind, *parts))


def over(limit, kind, *parts):
    """이미 한도에 닿았나(더 받으면 넘는다)."""
    return count(kind, *parts) >= limit


# ── 로그인 ────────────────────────────────────────────────────────────────

def login_blocked(username, ip):
    """(잠겼나, 남은 초). ip 가 없으면(명령행 authenticate 등) 막지 않는다."""
    if ip is None:
        return False, 0
    if over(LOGIN_PAIR[0], 'login_pair', username, ip):
        return True, seconds_left('login_pair', username, ip)
    if over(LOGIN_IP[0], 'login_ip', ip):
        return True, seconds_left('login_ip', ip)
    return False, 0


def login_failed(username, ip):
    if ip is None:
        return
    hit('login_pair', LOGIN_PAIR[1], username, ip)
    hit('login_ip', LOGIN_IP[1], ip)


def login_succeeded(username, ip):
    # 맞게 들어오면 그 조합의 실패는 지운다. IP 전체의 실패는 남긴다(여러 아이디를 도는 것을 막으려는 것)
    if ip is not None:
        reset('login_pair', username, ip)
