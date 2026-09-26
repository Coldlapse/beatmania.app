# -*- coding: utf-8 -*-
"""방문자의 실제 IP.

요청 경로는 Cloudflare → cloudflared 터널(이 서버) → Apache → gunicorn 이다. 그래서
REMOTE_ADDR 는 늘 127.0.0.1 이고, X-Forwarded-For 의 첫 값은 **방문자가 직접 적어
보낸 값**일 수 있다(Cloudflare 는 받은 X-Forwarded-For 뒤에 덧붙일 뿐이다).
진짜 방문자 IP 는 Cloudflare 가 넣는 CF-Connecting-IP 에 있다.

이 헤더를 믿어도 되는 전제 — **바뀌면 이 파일을 다시 볼 것**:
  - Apache 의 beatmania vhost 는 터널(192.168.0.5·127.0.0.1·::1)과 외부 감시탑에서 온
    요청만 받는다(polygon-server-deployment/dashboard deploy/hardening/public-surface.sh,
    2026-09-26). 바깥에서 원 서버로 바로 붙어 이 헤더를 지어낼 길이 없다.
  - Cloudflare 는 방문자가 보낸 CF-Connecting-IP 를 자기 값으로 덮어쓴다.
  감시탑의 직결 요청에는 이 헤더가 없다 — 그때는 원래 값을 그대로 둔다.

미들웨어가 REMOTE_ADDR 를 바꿔 두면 나머지(로그인·메일 횟수 제한, 조회수)는
request.META['REMOTE_ADDR'] 만 보면 된다. 조회수(django-hitcount)는 X-Forwarded-For 의
첫 값을 먼저 읽으므로 그것도 같은 값으로 맞춘다 — 안 하면 헤더를 지어내 조회수를 부풀릴 수 있다.
"""
import ipaddress


def _valid(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


class RealClientIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cf = (request.META.get('HTTP_CF_CONNECTING_IP') or '').strip()
        if cf and _valid(cf):
            request.META['REMOTE_ADDR'] = cf
            request.META['HTTP_X_FORWARDED_FOR'] = cf
        return self.get_response(request)


def get(request):
    """요청의 방문자 IP. 요청이 없으면(명령행 등) None."""
    if request is None:
        return None
    return request.META.get('REMOTE_ADDR') or None
