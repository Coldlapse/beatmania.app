# -*- coding: utf-8 -*-
"""언어 선택기용 태그.

Django 기본 `{% get_available_languages %}` 를 쓰면 안 된다. 그 태그는
언어 이름에 gettext() 를 적용하기 때문에, Django 자체 카탈로그에 들어 있는
'English' 가 현재 언어에 따라 '영어' / '英語(米国)' / '英语' 로 번역된다.
('한국어', '日本語', '简体中文' 은 Django 의 msgid 가 아니라 우연히 살아남는다.)

언어 선택 메뉴는 **그 언어를 쓰는 사람이 읽고 고르는 자리**다. 지금 화면이
무슨 언어든 각 항목은 항상 그 언어의 이름(자칭, endonym)으로 보여야 한다.
그래서 settings.LANGUAGES 를 번역 없이 그대로 넘긴다.
"""
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def native_languages():
    """[(코드, 자칭), ...] 를 번역하지 않고 그대로 돌려준다."""
    return list(settings.LANGUAGES)
