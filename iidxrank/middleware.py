# -*- coding: utf-8 -*-
"""기존 사용자를 1회 인증 화면으로 보내는 미들웨어.

강제 수준은 "로그인 상태에서만 되는 기능"까지다. 서열표 열람이나 공개
페이지는 그대로 열어 둔다 - 로그인한 사람에게만 사이트를 통째로 막으면,
그냥 로그아웃하고 쓰다가 영영 인증하지 않는다.

허용 목록을 '막을 경로' 가 아니라 '열어 둘 경로' 로 적은 이유: 나중에
로그인 전용 기능이 새로 생겼을 때 목록에 넣는 것을 잊어도 안전한 쪽으로
틀리기 때문이다(막힘 → 사용자가 알려 줌 / 열림 → 아무도 모름).
"""

import re

from django.shortcuts import redirect
from django.urls import reverse

from iidxrank import accounts

# 인증을 마치지 않아도 볼 수 있는 경로.
_ALLOW = [
    r'^/$',
    r'^/table/',
    r'^/u/',
    r'^/json/',
    r'^/status/',
    r'^/musiclist/',
    r'^/songrank/',
    r'^/userrank/',
    r'^/converter/',
    r'^/about/',
    r'^/privacy/',
    r'^/overjoy/',
    r'^/roadmap/',
    r'^/analytics/',
    # 인증 자체와 그에 필요한 것들
    r'^/account/verify-account/',
    r'^/account/verify/',
    r'^/logout/',
    r'^/i18n/',
    r'^/jsi18n/',
    r'^/static/',
    r'^/media/',
    r'^/admin/',
]
_ALLOW_RE = [re.compile(p) for p in _ALLOW]


class RequireAccountVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            path = request.path
            if not any(r.match(path) for r in _ALLOW_RE):
                if accounts.needs_migration(user):
                    return redirect(reverse('verify_account'))
        return self.get_response(request)
