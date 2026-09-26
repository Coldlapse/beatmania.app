# -*- coding: utf-8 -*-
"""로그인 시도 제한이 걸린 인증 백엔드.

일반 로그인(/login/)과 Django 관리자(/admin/login/)는 둘 다 authenticate() 를 거치고 같은
사용자 표를 쓴다. 그래서 제한을 뷰가 아니라 여기에 건다 — 관리자 계정의 비밀번호도 일반
로그인 쪽으로 시험할 수 있으므로 한쪽만 막으면 소용이 없다.

  잠김 판단: 여기(authenticate 전에). 잠겼으면 맞는 비밀번호여도 들여보내지 않는다.
  실패 세기: user_login_failed 신호(apps.py) — authenticate 가 실패하면 Django 가 보낸다.
  성공:     user_logged_in 신호로 그 (아이디, IP) 조합의 실패를 지운다.

request 가 없는 authenticate(명령행, 테스트)는 IP 를 모르므로 제한하지 않는다.
"""
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied

from iidxrank import client_ip, throttle


class ThrottledModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is not None and username is not None:
            blocked, _left = throttle.login_blocked(username, client_ip.get(request))
            if blocked:
                # PermissionDenied 면 Django 가 다른 백엔드를 보지 않고 실패로 끝낸다
                raise PermissionDenied
        return super().authenticate(request, username=username, password=password, **kwargs)


def on_login_failed(sender, credentials, request=None, **kwargs):
    username = credentials.get('username')
    if request is not None and username:
        throttle.login_failed(username, client_ip.get(request))


def on_logged_in(sender, request, user, **kwargs):
    if request is not None:
        throttle.login_succeeded(user.get_username(), client_ip.get(request))
