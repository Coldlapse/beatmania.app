# -*- coding: utf-8 -*-
"""개발용 설정 — 운영 settings.py 를 그대로 쓰되 DB 만 dev 컨테이너로 돌린다.

    docker compose -f dev/docker-compose.yml up -d
    set DJANGO_SETTINGS_MODULE=dev.settings_dev
    python manage.py runserver

**운영 비밀값을 쓰지 않는다.** 아래에서 필수 환경변수에 개발용 기본값을
먼저 박아 넣는다. settings.py 의 .env 로더는 os.environ.setdefault 를 쓰므로
이미 값이 있으면 .env 를 덮지 않는다 — 즉 여기서 정한 값이 이긴다.
운영 SECRET_KEY 로 개발 세션이 서명되는 일을 막기 위한 것이다.

DB 는 settings.py 의 DATABASES 를 통째로 갈아끼운다. 라이브와 같은
MySQL 8.0.45 에 같은 접속 charset(utf8 = MySQL 8 의 utf8mb3)으로 붙는다.
그래야 콜레이션·격리수준까지 라이브와 같은 조건에서 검증할 수 있다.
"""
import os

_DEV_DEFAULTS = {
    'DJANGO_SECRET_KEY': 'dev-only-not-a-real-key',
    'DJANGO_DEBUG': '1',
    'DJANGO_ALLOWED_HOSTS': '*',
    # reCAPTCHA 공개 테스트 키. 항상 통과하므로 가입 폼을 오프라인에서 눌러 볼 수 있다.
    'RECAPTCHA_PUBLIC_KEY': '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI',
    'RECAPTCHA_PRIVATE_KEY': '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe',
    'IMGTL_KEY': 'dev-unused',
    'DB_PASSWORD': 'devpassword',
}
for _k, _v in _DEV_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

from settings import *  # noqa: E402,F401,F403

DEBUG = True
ALLOWED_HOSTS = ['*']

# dev/docker-compose.yml 의 컨테이너. 라이브와 같은 8.0.45 / 같은 접속 charset.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DEV_DB_NAME', 'iidxrank'),
        'USER': os.environ.get('DEV_DB_USER', 'iidxrank'),
        'PASSWORD': os.environ.get('DEV_DB_PASSWORD', 'devpassword'),
        'HOST': os.environ.get('DEV_DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DEV_DB_PORT', '3307'),
        'OPTIONS': {'charset': os.environ.get('DEV_DB_CHARSET', 'utf8')},
    }
}

# 개발 중에는 업로드가 저장소를 더럽히지 않게 dev/ 밑으로 모은다.
MEDIA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')

SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']
