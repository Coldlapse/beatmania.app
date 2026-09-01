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

from django.contrib.auth.models import User
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


def redirect_user(request, username, rest):
    """옛 최상위 사용자 경로 `/sadang/SP12H/` → `/u/sadang/table/SP12H/`.

    실제로 존재하는 사용자일 때만 넘긴다. 그러지 않으면 오타나 없는 경로가
    전부 리다이렉트되어 404 가 사라진다.
    """
    if not User.objects.filter(username=username).exists():
        raise Http404

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
