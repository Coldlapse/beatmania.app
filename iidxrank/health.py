# -*- coding: utf-8 -*-
"""서비스 상태 점검.

무엇을 보는가
  site  — 이 웹 앱이 요청을 처리하고 있는가. 이 코드가 도는 것 자체가 답이다.
  db    — 데이터베이스에 실제로 질의가 되는가.
  textage / sheet — 갱신 작업이 긁어 오는 외부 페이지에 지금 닿는가.

외부 두 곳은 **크롤러를 띄우지 않는다.** playwright 로 브라우저를 올리면
한 번에 수백 MB 를 쓰고 수 초가 걸린다. 상태 점검은 자주 도는 것이라
그렇게 하면 안 된다. HTTP 로 받아서 (1) 응답하는가 (2) 우리가 기대하는
표식이 본문에 있는가 까지만 본다. 표식까지 보는 이유는, 사이트가 살아
있어도 내용이 통째로 바뀌면 크롤링이 깨지기 때문이다. 200 만 보고
'정상'이라 하면 그 경우를 놓친다.
"""
import time

import requests
from django.db import connection
from django.utils import timezone

# 외부 점검은 오래 붙들지 않는다. 느린 것도 장애다.
TIMEOUT = 8

# 주소를 여기에 베껴 두지 않는다. 갱신 작업이 실제로 보는 곳을 그대로
# 봐야 의미가 있다. 파서가 주소를 바꾸면 점검 대상도 같이 따라간다.
TEXTAGE_URL = 'https://textage.cc/score/index.html?a021B000'


def _sheet_url():
    from update.parser_infinitas import IIDXSheetParser
    p = IIDXSheetParser.__new__(IIDXSheetParser)   # DB 를 건드리는 __init__ 을 피한다
    p.__init__()
    return p.target_sheets[0]['url']

OK = 'ok'
DEGRADED = 'degraded'      # 응답은 하는데 기대한 내용이 아니다
DOWN = 'down'

CHECKS = ['site', 'db', 'textage', 'sheet']

LABELS = {
    'site': '웹 서비스',
    'db': '데이터베이스',
    'textage': 'textage.cc (수록곡 출처)',
    'sheet': 'Google Sheets (서열표 출처)',
}

DESCRIPTIONS = {
    'site': '이 페이지를 그려 주는 서버가 요청을 처리하고 있는지.',
    'db': '데이터베이스에 질의가 되는지.',
    'textage': '수록곡을 긁어 오는 페이지에 닿는지. 내려받아 표식까지 확인한다.',
    'sheet': '서열표를 긁어 오는 시트에 닿는지. 내려받아 표식까지 확인한다.',
}


def _timed(fn):
    t0 = time.time()
    try:
        status, note = fn()
    except Exception as e:
        status, note = DOWN, '%s: %s' % (type(e).__name__, str(e)[:120])
    return status, note, int((time.time() - t0) * 1000)


def check_site():
    # 이 함수가 불렸다는 것은 워커가 요청을 처리하고 있다는 뜻이다.
    return OK, ''


def check_db():
    cur = connection.cursor()
    cur.execute('SELECT 1')
    row = cur.fetchone()
    if not row or row[0] != 1:
        return DOWN, '질의 결과가 예상과 다름'
    return OK, ''


def _fetch(url, marker, label):
    r = requests.get(url, timeout=TIMEOUT,
                     headers={'User-Agent': 'beatmania.app health check'})
    if r.status_code != 200:
        return DOWN, 'HTTP %s' % r.status_code
    if marker not in r.text:
        # 살아 있지만 우리가 읽던 모양이 아니다. 갱신 작업이 깨질 신호다.
        return DEGRADED, "응답은 왔지만 '%s' 표식이 없음" % label
    return OK, ''


def check_textage():
    # 곡 목록 페이지가 이 스크립트를 싣는다. 갱신 작업이 여기서 값을 읽는다.
    return _fetch(TEXTAGE_URL, 'actbl', 'actbl')


def check_sheet():
    # 구글 시트 퍼블리시 페이지는 표를 table.waffle 로 낸다.
    # 파서가 그 클래스를 찾아 들어가므로 그것이 곧 표식이다.
    return _fetch(_sheet_url(), 'waffle', 'waffle')


RUNNERS = {
    'site': check_site,
    'db': check_db,
    'textage': check_textage,
    'sheet': check_sheet,
}


def run_all(targets=None):
    """점검을 돌리고 결과를 돌려준다. 저장은 호출자가 한다."""
    out = []
    for name in (targets or CHECKS):
        status, note, ms = _timed(RUNNERS[name])
        out.append({'target': name, 'status': status, 'note': note,
                    'latency_ms': ms, 'checked_at': timezone.now()})
    return out
