# -*- coding: utf-8 -*-
"""sadang.org 에서 옮겨온 Overjoy 난이도표.

이 페이지는 사람만 보는 것이 아니다. **BMS 구동기(LR2, beatoraja 등)가
기계로 읽어 간다.** 규약은 이렇다.

1. 클라이언트가 페이지 HTML 을 받아 `<meta name="bmstable" content="...">` 를 읽는다
2. 그 주소에서 header.json 을 받는다
3. header.json 의 `data_url` 에서 곡 목록(score.json)을 받는다

그래서 header.json 의 `data_url` 은 **절대주소** 로 준다. 원본
(sadang.org)도 절대주소였다. 상대경로로 두면 클라이언트마다 무엇을 기준으로
푸는지가 달라서(페이지 기준 / header.json 기준 / 아예 미지원) 일부 구동기에서
목록을 못 가져간다. 도메인을 코드에 박지 않고 요청에서 만들어 쓴다 — 그래야
개발 서버와 운영이 같은 코드로 돈다.
"""
import os

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.http import require_GET

# 원본 header.json 의 값. score.json 의 위치만 요청에 맞춰 채운다.
TABLE_NAME = 'Overjoy'
TABLE_SYMBOL = '★★'
LEVEL_ORDER = ['0', '1', '2', '3', '4', '5', '6', '7', '8']
# 원본에 있던 값을 그대로 둔다. 클라이언트가 갱신 여부 판단에 쓴다.
TABLE_UPDATE = 1527318397


@require_GET
def page(request):
    return render(request, 'overjoy.html')


@require_GET
def header_json(request):
    """BMS 구동기가 읽는 표 정의."""
    return JsonResponse({
        'name': TABLE_NAME,
        'symbol': TABLE_SYMBOL,
        'data_url': request.build_absolute_uri(
            static('overjoy/data/score.json')),
        'update': TABLE_UPDATE,
        'level_order': LEVEL_ORDER,
    }, json_dumps_params={'ensure_ascii': False})
