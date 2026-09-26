# -*- coding: utf-8 -*-
"""메인 페이지 '공지사항' 칸 (iidxrank/discord_notice.py).

메인 페이지는 탭 이름만 그리고, 채널 내용은 /notice/<번호>/ 로 따로 불러온다.
디스코드가 느리거나 멈춰도 메인 페이지가 기다리지 않게 하려는 것이다 —
캐시가 빈 순간에는 디스코드 응답(최대 5초)을 기다려야 한다.
"""
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_control

from iidxrank import discord_notice

# 디스코드 서버 초대 주소 — 메인 페이지 안내문과 같다
INVITE = 'https://discord.gg/RxjwbvWa8D'


def tabs():
    """[(번호, 탭 이름)]. 탭 이름은 .env 의 값이지만, 카탈로그에 있으면 번역해 보여 준다."""
    return [(i, _(name)) for i, (name, _cid) in enumerate(discord_notice.channels())]


# 언어별로 문구가 달라 공용 캐시(Cloudflare)에는 두지 않는다
@cache_control(private=True, max_age=60)
def notice_fragment(request, idx):
    chans = discord_notice.channels()
    idx = int(idx)
    if idx >= len(chans):
        raise Http404
    name, cid = chans[idx]
    return render(request, 'widgets/discord_notice.html', {
        'channel_name': _(name),
        'messages': discord_notice.messages(cid),
        'invite': INVITE,
    })
