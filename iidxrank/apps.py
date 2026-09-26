# -*- coding: utf-8 -*-
from django.apps import AppConfig


class IidxrankConfig(AppConfig):
    name = 'iidxrank'

    def ready(self):
        # 로그인 시도 제한(auth_backend.py)의 실패·성공 세기
        from django.contrib.auth.signals import user_logged_in, user_login_failed

        from iidxrank import auth_backend
        user_login_failed.connect(auth_backend.on_login_failed, dispatch_uid='bm_login_failed')
        user_logged_in.connect(auth_backend.on_logged_in, dispatch_uid='bm_logged_in')
