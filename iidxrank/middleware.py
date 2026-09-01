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

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext as _

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


def _ajax_redirect(url):
    """AJAX 로 들어온 요청에 "창 전체를 옮기라" 고 답한다.

    서열표 캔버스는 항목을 클릭하면 jQuery .load() 로 /rankedit/<id>/ 를 불러
    작은 팝업 div 에 끼워 넣는다. 여기서 그냥 302 를 주면 jQuery 가 그것을
    따라가 **인증 페이지 전체(12KB)를 그 팝업 안에 밀어 넣는다.**

    그 상태가 위험한 이유는 보이는 것과 실제가 다르기 때문이다. 끼워 넣어진
    폼의 action="./" 은 현재 주소(/table/SP12H/)로 풀리므로, '인증 마치기' 를
    누르면 POST 가 인증 뷰가 아니라 서열표로 간다. 서열표는 200 을 돌려주고
    페이지가 다시 그려지면서 팝업이 사라진다. 사용자에게는 인증이 끝난 것처럼
    보이지만 아무 일도 일어나지 않았다(실측함).

    그래서 조각을 끼워 넣게 두지 않고 창 전체를 인증 화면으로 보낸다.
    JS 가 막힌 환경을 위해 눈에 보이는 링크도 함께 둔다.
    """
    safe = escape(url)
    html = (
        '<div style="padding:12px; font-size:13px; line-height:1.6;">'
        '<p>%s</p><p><a href="%s">%s</a></p></div>'
        '<script>window.top.location.href = "%s";</script>'
        % (escape(str(_('계정 인증이 필요합니다.'))), safe,
           escape(str(_('인증 화면으로 이동'))), safe))
    # 200 으로 돌려준다. jQuery .load() 는 오류 상태에서 본문을 넣지 않아
    # 링크조차 보이지 않게 된다.
    return HttpResponse(html)


class RequireAccountVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            path = request.path
            if not any(r.match(path) for r in _ALLOW_RE):
                if accounts.needs_migration(user):
                    url = reverse('verify_account')
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return _ajax_redirect(url)
                    return redirect(url)
        return self.get_response(request)
