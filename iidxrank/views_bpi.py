# -*- coding: utf-8 -*-
"""BPI 페이지 — /bpi/ (내 것) · /u/<아이디>/bpi/ (공유).

공개 규칙은 서열표와 같다. 남의 페이지는 비공개거나 없는 계정이면 같은 화면
(views._unavailable, 404)을 준다 — 둘을 구별하면 계정 열거가 된다.
공유 버튼은 내 페이지에서만 보이고 /u/<아이디>/bpi/ 를 복사한다.
"""
from django.shortcuts import render
from django.views.decorators.http import require_GET

from iidxrank import bpi
from iidxrank import rankpage as rp
from iidxrank.views import _unavailable


@require_GET
def bpi_page(request, username=None):
    if username is None:
        player = rp.get_player_from_request(request)
    else:
        player, _reason = rp.find_player_from_id(username)
        if player is None:
            return _unavailable(request, username)
    return render(request, 'user/bpi.html', {
        'userdata': rp.get_udata_from_player(player, username),
        'detail': bpi.details(player) if player else None,
        'own': username is None and player is not None,
        # 내 프로필이 비공개면 공유 주소를 복사해도 남에게는 열리지 않는다. 화면에서 알린다.
        'private': bool(player and player.private),
        'source_url': bpi.SITE_URL,
    })
