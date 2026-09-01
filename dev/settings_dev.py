# -*- coding: utf-8 -*-
"""媛쒕컻???ㅼ젙 ???댁쁺 settings.py 瑜?洹몃?濡??곕릺 DB 留?dev 而⑦뀒?대꼫濡??뚮┛??

    docker compose -f dev/docker-compose.yml up -d
    set DJANGO_SETTINGS_MODULE=dev.settings_dev
    python manage.py runserver

**?댁쁺 鍮꾨?媛믪쓣 ?곗? ?딅뒗??** ?꾨옒?먯꽌 ?꾩닔 ?섍꼍蹂?섏뿉 媛쒕컻??湲곕낯媛믪쓣
癒쇱? 諛뺤븘 ?ｋ뒗?? settings.py ??.env 濡쒕뜑??os.environ.setdefault 瑜??곕?濡??대? 媛믪씠 ?덉쑝硫?.env 瑜???? ?딅뒗????利??ш린???뺥븳 媛믪씠 ?닿릿??
?댁쁺 SECRET_KEY 濡?媛쒕컻 ?몄뀡???쒕챸?섎뒗 ?쇱쓣 留됯린 ?꾪븳 寃껋씠??

DB ??settings.py ??DATABASES 瑜??듭㎏濡?媛덉븘?쇱슫?? ?쇱씠釉뚯? 媛숈?
MySQL 8.0.46 ??媛숈? ?묒냽 charset ?쇰줈 遺숇뒗?? 洹몃옒??肄쒕젅?댁뀡쨌寃⑸━?섏?源뚯?
?쇱씠釉뚯? 媛숈? 議곌굔?먯꽌 寃利앺븷 ???덈떎.
"""
import os

_DEV_DEFAULTS = {
    'DJANGO_SECRET_KEY': 'dev-only-not-a-real-key',
    'DJANGO_DEBUG': '1',
    'DJANGO_ALLOWED_HOSTS': '*',
    # reCAPTCHA 怨듦컻 ?뚯뒪???? ??긽 ?듦낵?섎?濡?媛???쇱쓣 ?ㅽ봽?쇱씤?먯꽌 ?뚮윭 蹂????덈떎.
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

# dev/docker-compose.yml ??而⑦뀒?대꼫. ?쇱씠釉뚯? 媛숈? 8.0.45 / 媛숈? ?묒냽 charset.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DEV_DB_NAME', 'iidxrank'),
        'USER': os.environ.get('DEV_DB_USER', 'iidxrank'),
        'PASSWORD': os.environ.get('DEV_DB_PASSWORD', 'devpassword'),
        'HOST': os.environ.get('DEV_DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DEV_DB_PORT', '3307'),
        # ?쇱씠釉뚯? 媛숈? 媛믪씠?댁빞 ?쒕떎. utf8(=utf8mb3) 濡??먮㈃ ?대え吏媛 ???ㅼ뼱媛怨?
        # ?ㅼ젣濡?愿由ъ옄 ??쒕낫??濡쒓렇媛 洹??뚮Ц???듭㎏濡?鍮꾩뿀???곸씠 ?덈떎.
        'OPTIONS': {'charset': os.environ.get('DEV_DB_CHARSET', 'utf8mb4')},
    }
}

# 媛쒕컻 以묒뿉???낅줈?쒓? ??μ냼瑜??붾읇?덉? ?딄쾶 dev/ 諛묒쑝濡?紐⑥???
MEDIA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')

SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']
