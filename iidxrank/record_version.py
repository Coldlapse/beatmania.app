# -*- coding: utf-8 -*-
"""플레이어 기록의 '버전' — BPI·CPI 캐시 키에 넣어, 기록이 바뀌면 곧바로 다시 계산하게 한다.

기본 캐시(locmem)는 gunicorn 워커(5개)마다 따로라, 기록을 바꾼 요청이 자기 워커의 캐시를 지워도
다른 워커에는 옛 값이 10분 남았다. 그래서 워커가 같이 보는 DB 캐시(CACHES['throttle'])에 번호를
하나 두고, 기록을 바꾸는 곳에서 올린다(bump). 계산 결과의 캐시 키에 이 번호가 들어가므로 번호가
바뀌면 모든 워커가 새 키로 다시 계산한다.

기록을 바꾸는 곳 — 새로 만들면 여기에 bump 를 넣어야 한다(빠뜨리면 그 경로만 최대 10분 늦는다):
  records_import.apply      동기화 앱·tracker.tsv 업로드
  views.modify              서열표에서 손으로 램프·DJ RANK·EX SCORE 수정
dev/checks/bpi_check.py 가 두 경로를 확인한다.
"""
import time

from django.core.cache import caches


def _key(player_id):
    return 'recver:%d' % player_id


def get(player_id):
    """지금 번호. 없으면(처음, 또는 캐시가 비워 냄) 지금 시각으로 새로 둔다 — 0 같은 고정값으로
    돌아가면 그 번호로 캐시해 둔 옛 결과가 다시 쓰일 수 있다."""
    c = caches['throttle']
    v = c.get(_key(player_id))
    if v is None:
        v = time.time_ns() // 1000
        c.add(_key(player_id), v, None)
        v = c.get(_key(player_id), v)
    return v


def bump(player_id):
    caches['throttle'].set(_key(player_id), time.time_ns() // 1000, None)
