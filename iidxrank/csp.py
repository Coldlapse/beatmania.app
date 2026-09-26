# -*- coding: utf-8 -*-
"""Content-Security-Policy — **보고 전용**으로 시작한다(2026-09-26, 보안 검토 2순위).

CSP 는 XSS 가 다시 생겼을 때 두 번째 벽이다: 허락한 곳이 아닌 스크립트·연결을 브라우저가 막는다.
다만 이 사이트는 템플릿 안 인라인 스크립트가 많아 바로 막는 모드(Content-Security-Policy)로 켜면
화면이 깨진다. 그래서 먼저 Report-Only 로 켜서 **무엇이 실제로 걸리는지** 모은다. 막지는 않는다.
위반 보고는 브라우저가 /csp-report/ 로 보내고, 서버 로그(logger iidxrank.csp)에 한 줄씩 남는다.

허락 목록(2026-09-26 템플릿·JS 에서 찾은 외부 자원):
  - cdn.jsdelivr.net     Bootstrap·아이콘·차트 라이브러리
  - fonts.googleapis.com / fonts.gstatic.com   서열표 글꼴(Comfortaa)
  - www.google.com / www.gstatic.com           가입 폼 reCAPTCHA(스크립트·iframe)
  - cdn.discordapp.com / media.discordapp.net  디스코드 공지 칸의 아바타·첨부 이미지
  - www.googletagmanager.com / *.google-analytics.com   Google Analytics(common.html 의 gtag).
    템플릿 검색에서 놓쳤다가 보고 전용 모드의 첫 보고로 찾았다(2026-09-26) — 이 모드를 먼저 켠 이유다
막는 모드로 바꾸는 것은 보고를 몇 주 모아 본 뒤의 일이다. 'unsafe-inline' 이 남아 있는 한 막는 모드도
인라인 주입은 막지 못한다 — 그것까지 가려면 인라인 스크립트를 파일로 빼는 작업이 먼저다.
"""
import json
import logging
from urllib.parse import urlsplit

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from iidxrank import client_ip, throttle

log = logging.getLogger(__name__)

POLICY = '; '.join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://www.google.com https://www.gstatic.com"
    " https://www.googletagmanager.com https://www.google-analytics.com",
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
    "font-src 'self' data: https://cdn.jsdelivr.net https://fonts.gstatic.com",
    "img-src 'self' data: blob: https://cdn.discordapp.com https://media.discordapp.net"
    " https://www.google-analytics.com https://www.googletagmanager.com",
    "connect-src 'self' https://www.google-analytics.com https://*.google-analytics.com"
    " https://www.googletagmanager.com",
    "frame-src https://www.google.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'self'",
    "report-uri /csp-report/",
])

REPORT_MAX_BYTES = 16 * 1024
REPORT_PER_IP = (60, 60 * 60)      # IP 당 1시간 60건까지만 기록한다(로그를 채우는 것을 막는다)


class CSPReportOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # HTML 에만 붙인다. JSON·파일에는 의미가 없다
        if response.get('Content-Type', '').startswith('text/html'):
            response.setdefault('Content-Security-Policy-Report-Only', POLICY)
        return response


def _where(url):
    """보고에 담긴 주소에서 호스트와 경로만 남긴다(쿼리에 무엇이 있을지 모른다)."""
    if not isinstance(url, str) or not url:
        return '-'
    if '://' not in url:
        return url[:40]          # 'inline', 'eval', 'data' 같은 키워드
    p = urlsplit(url)
    return (p.netloc + p.path)[:120]


@csrf_exempt            # 브라우저가 스스로 보내는 보고다. 상태를 바꾸지 않고 로그만 남긴다
@require_POST
def report(request):
    if len(request.body) > REPORT_MAX_BYTES:
        return HttpResponse(status=413)
    ip = client_ip.get(request)
    if ip and throttle.hit('csp_report', REPORT_PER_IP[1], ip) > REPORT_PER_IP[0]:
        return HttpResponse(status=204)
    try:
        body = json.loads(request.body.decode('utf-8'))
        r = body.get('csp-report', {}) if isinstance(body, dict) else {}
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)
    if isinstance(r, dict):
        log.warning('csp violation: %s blocked=%s on=%s',
                    str(r.get('violated-directive') or r.get('effective-directive') or '-')[:60],
                    _where(r.get('blocked-uri')), _where(r.get('document-uri')))
    return HttpResponse(status=204)
