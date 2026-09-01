# -*- coding: utf-8 -*-
"""옛 URL 을 새 주소로 301 영구 리다이렉트한다.

이 서비스는 2022년부터 `/!/SP12H/` 형태의 주소를 써 왔다. 245명의 북마크,
디스코드와 velog 글의 외부 링크, 검색엔진 색인이 전부 그 주소를 가리킨다.
주소 체계를 바꾸면서 이것들을 그냥 깨뜨릴 수는 없다.

301(Moved Permanently)을 쓰는 이유: 검색엔진이 색인을 새 주소로 옮기고,
브라우저가 리다이렉트를 캐시해 두 번째부터는 왕복이 없다.

이 모듈은 지우지 마라. 옛 링크가 살아 있는 한 계속 필요하다.
"""
import re

from django.http import Http404
from django.shortcuts import redirect

# 옛 `/!/...` 경로 → 새 경로.
# 앞에서부터 처음 맞는 규칙을 쓴다. 순서가 중요하다 —
# `(?P<t>\w+)/` 같은 포괄 규칙은 반드시 뒤에 와야 한다.
BANG_RULES = [
    (r'^login/?$',            '/login/'),
    (r'^join/?$',             '/join/'),
    (r'^logout/?$',           '/logout/'),
    (r'^account/?$',          '/account/'),
    (r'^setpassword/?$',      '/setpassword/'),
    (r'^withdraw/?$',         '/withdraw/'),
    (r'^my-page/?$',          '/my-page/'),
    (r'^analytics/?$',        '/analytics/'),
    (r'^roadmap/?$',          '/roadmap/'),
    (r'^converter/?$',        '/converter/'),
    (r'^songrank/?$',         '/songrank/'),
    (r'^userrank/?$',         '/userrank/'),
    (r'^update/?$',           '/lampupdate/'),
    (r'^modify/?$',           '/modify/'),
    (r'^rankedit/(?P<id>[0-9]+)/?$',            '/rankedit/%(id)s/'),
    (r'^status/(?P<m>[\w-]+)/json/?$',          '/status/%(m)s/json/'),
    (r'^status/(?P<m>[\w-]+)/?$',               '/status/%(m)s/'),
    (r'^manage/(?P<rest>.*)$',                  '/manage/%(rest)s'),
    # 서열표. 포괄 규칙이므로 마지막이다.
    (r'^(?P<t>\w+)/table/?$',   '/table/%(t)s/embed/'),
    (r'^(?P<t>\w+)/json/?$',    '/table/%(t)s/json/'),
    (r'^(?P<t>\w+)/?$',         '/table/%(t)s/'),
]
BANG_RULES = [(re.compile(p), t) for p, t in BANG_RULES]


def _with_query(request, path):
    qs = request.META.get('QUERY_STRING', '')
    return path + ('?' + qs if qs else '')


def redirect_bang(request, rest):
    """`/!/...` → 새 주소."""
    rest = rest.lstrip('/')
    for pattern, target in BANG_RULES:
        m = pattern.match(rest)
        if m:
            return redirect(_with_query(request, target % m.groupdict()),
                            permanent=True)
    # 규칙에 없는 `/!/...` 는 홈으로 보낸다. 404 보다 낫다.
    return redirect('/', permanent=True)


# 사이트 자신의 경로로 쓰거나 쓸 이름들. 사용자 이름으로 넘기지 않는다.
#
# 이 규칙은 URLconf 의 맨 끝에서 "남은 모든 최상위 경로"를 받는다. 그래서
# 아직 만들지 않은 페이지 주소도 여기 걸려 **영구** 리다이렉트가 나간다.
# 방문자 브라우저는 301 을 오래 캐시하므로, 나중에 그 주소로 페이지를
# 만들어도 이미 방문한 사람에게는 계속 /u/... 로 날아간다.
# 실제로 /status/ 가 그렇게 한 번 물렸다.
#
# 존재 여부를 확인하지 않는 원칙(계정 열거 차단)은 그대로다. 이 목록은
# 고정된 사이트 경로일 뿐 계정에 대해 아무것도 알려주지 않는다.
RESERVED = frozenset("""
about account admin analytics api board converter embed favicon.ico
health i18n imgdownload join json jsi18n login logout manage media
musiclist my-page overjoy privacy rankedit robots.txt roadmap
songrank static status table u user userrank
""".split())


def redirect_user(request, username, rest):
    """옛 최상위 사용자 경로 `/sadang/SP12H/` → `/u/sadang/table/SP12H/`.

    계정 존재 여부를 확인하지 않고 무조건 넘긴다. 여기서 확인하면
    "리다이렉트되면 존재하는 계정"이라는 신호가 되어 계정 열거가 가능해진다.
    존재 여부 판단은 새 주소의 뷰가 하고, 없는 계정과 비공개 계정에
    같은 화면을 준다.
    """
    if username.lower() in RESERVED:
        # 사이트 경로다. 지금 없는 주소면 그냥 404 로 둔다 — 영구
        # 리다이렉트를 캐시시켜 두면 나중에 그 주소를 못 쓴다.
        raise Http404()

    rest = rest.strip('/')
    base = '/u/%s/' % username
    if not rest:
        target = base
    else:
        parts = rest.split('/')
        table = parts[0]
        tail = parts[1] if len(parts) > 1 else ''
        if tail == 'table':
            target = '%stable/%s/embed/' % (base, table)
        elif tail == 'json':
            target = '%stable/%s/json/' % (base, table)
        elif not tail:
            target = '%stable/%s/' % (base, table)
        else:
            # 지원하지 않는 옛 경로(stat/recm 등)는 프로필로 보낸다
            target = base
    return redirect(_with_query(request, target), permanent=True)
