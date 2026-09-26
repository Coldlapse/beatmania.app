# -*- coding: utf-8 -*-
"""CPI(추정) — cpi.makecir.com 의 채보별 공개 값으로 플레이어 CPI 를 어림한다.

CPI(Clear Power Indicator)는 cpi.makecir.com 이 SP☆12 클리어 램프로 매기는 실력
지표다. 원래 계산은 약 2.4만~3만 명의 '고스트 플레이어' 램프와 1:1 로 승패를 세어
Elo 식으로 바꾸는 것이라(공개 소스 makecir/clear-power-indicator, setRating),
그 고스트 DB 없이는 똑같이 재현할 수 없다. 여기서는 사이트가 공개하는 채보별
두 값으로 근사한다 — 그래서 화면에는 반드시 "추정" 이라고 적는다.

채보별 값 (/scores/tables, 램프 EASY·CLEAR·HARD·EX-HARD·FC 각각)
  적정CPI μ   그 램프를 달성한 플레이어가 50% 가 되는 CPI
  개인차도 d  달성률 25% ~ 75% 사이의 CPI 폭
  달성 확률을 로지스틱 P(R) = 1 / (1 + exp(-(R - μ) / s)) 로 둔다.
  25%~75% 폭이 2·s·ln3 이므로 s = d / (2·ln3).
  원 사이트 곡선은 비대칭 항(cfactor)이 하나 더 있는데 공개되지 않아 0 으로 둔다.

플레이어 추정
  기록이 있는 SP☆12 채보마다, 램프 L(EASY~FC)에 대해 "L 이상 달성했는가" 를
  한 번의 관측으로 본다. 모든 관측의 로그우도 합을 최대로 하는 R 이 추정 CPI 다.
  로그-로지스틱의 합은 R 에 대해 오목하므로 최댓값이 하나뿐이고, 황금분할 탐색으로
  찾는다. ASSIST 는 FAILED 로 친다(원 사이트와 같다). 기록 없는 채보는 뺀다.

데이터를 가져오는 쪽 예절
  하루 한 번, 한 페이지만 받는다(update_cpi 명령). 누가 받아 가는지 User-Agent 에
  밝힌다. 원 사이트 운영자가 원하지 않으면 ENABLED 를 끄고 표를 비우면 된다.
"""
import html
import math
import re

import requests
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from iidxrank import models

ENABLED = True                     # 운영자 요청이 오면 끈다(화면·수집 모두 멈춘다)
SOURCE_URL = 'https://cpi.makecir.com/scores/tables'
SITE_URL = 'https://cpi.makecir.com/'
USER_AGENT = 'beatmania.app (https://beatmania.app) - daily CPI reference fetch'

LAMPS = {'easy': 3, 'clear': 4, 'hard': 5, 'exh': 6, 'fc': 7}   # iidx.py 의 클리어 번호
MIN_CHARTS = 10                    # 이보다 적은 채보로는 추정하지 않는다
R_LO, R_HI = -1000.0, 5000.0
CACHE_SECONDS = 600
_LN3x2 = 2 * math.log(3)

_RX_TABLE = re.compile(r'<table id="(\w+)_table"(.*?)</table>', re.S)
_RX_CELL = re.compile(
    r'<a href="/scores/view/(\d+)">([^<]*)</a>\s*<div class="small-txt"[^>]*>'
    r'\s*([\d.]+|inf)\s*/\s*([\d.]+|-)\s*</div>')
_RX_TYPE = re.compile(r'\s*\[(H|L|A)\]$')


def parse(page):
    """/scores/tables → {(제목, 'SPA'): {lamp번호: (μ 또는 None, d 또는 None)}}.

    μ=None 은 'inf' — 아무도 그 램프를 달성하지 못한 채보다. 관측에서 뺀다.
    """
    out = {}
    for lamp, body in _RX_TABLE.findall(page):
        num = LAMPS.get(lamp)
        if num is None:
            continue
        for _vid, title, mu, d in _RX_CELL.findall(body):
            title = html.unescape(title).strip()
            m = _RX_TYPE.search(title)
            ty = 'SP' + (m.group(1) if m else 'A')
            if m:
                title = title[:m.start()]
            out.setdefault((title, ty), {})[num] = (
                None if mu == 'inf' else float(mu), None if d == '-' else float(d))
    return out


def fetch_and_store():
    """원 사이트에서 받아 CpiValue 를 통째로 갈아 끼운다. 요약을 돌려준다."""
    from iidxrank.records_import import norm_title

    r = requests.get(SOURCE_URL, timeout=30, headers={'User-Agent': USER_AGENT})
    r.raise_for_status()
    charts = parse(r.text)
    if len(charts) < 100:
        # 페이지 모양이 바뀌었다. 멀쩡한 값을 빈 값으로 덮지 않는다.
        raise ValueError('CPI 표를 읽지 못했습니다 (%d채보)' % len(charts))

    index = {}
    for sid, title, ty in (models.Song.objects
                           .filter(songlevel=12, songtype__in=('SPH', 'SPA', 'SPL'))
                           .values_list('id', 'songtitle', 'songtype')):
        index.setdefault((norm_title(title), ty), []).append(sid)

    rows, missing = [], []
    now = timezone.now()
    for (title, ty), lamps in charts.items():
        ids = index.get((norm_title(title), ty), [])
        if len(ids) != 1:
            missing.append('%s [%s]' % (title, ty))
            continue
        for lamp, (mu, d) in lamps.items():
            rows.append(models.CpiValue(song_id=ids[0], lamp=lamp, mu=mu, width=d, fetched_at=now))
    with transaction.atomic():
        models.CpiValue.objects.all().delete()
        models.CpiValue.objects.bulk_create(rows)
    # 캐시는 지우지 않는다. 수집은 cron 의 별도 프로세스라 웹 워커의 캐시에 닿지 않는다.
    # 키에 적재 시각이 들어 있어(_data_version, 60초 기억) 1분 안에 새 값으로 바뀐다.
    return {'charts': len(charts), 'matched': len(charts) - len(missing), 'missing': missing}


def _loglik(r, obs):
    total = 0.0
    for mu, s, y in obs:
        z = (r - mu) / s
        # log(sigmoid(z)) / log(1-sigmoid(z)) 를 넘침 없이
        if y:
            total += -math.log1p(math.exp(-z)) if z > -30 else z
        else:
            total += -math.log1p(math.exp(z)) if z < 30 else -z
    return total


def estimate(clears):
    """clears: {song_id: playclear} → (추정 CPI 또는 None, 쓴 채보 수)."""
    values = {}
    for song_id, lamp, mu, width in (models.CpiValue.objects
                                     .filter(song_id__in=list(clears))
                                     .values_list('song_id', 'lamp', 'mu', 'width')):
        if mu is None or not width:
            continue
        values.setdefault(song_id, []).append((lamp, mu, width / _LN3x2))
    obs = []
    used = 0
    for sid, clear in clears.items():
        if not clear or sid not in values:
            continue                             # 기록 없음 / CPI 값 없음
        clear = 1 if clear == 2 else clear       # ASSIST 는 FAILED 로
        used += 1
        for lamp, mu, s in values[sid]:
            obs.append((mu, s, clear >= lamp))
    if used < MIN_CHARTS:
        return None, used
    # 달성한 것과 못 한 것이 둘 다 있어야 추정이 된다. 전부 못 했으면(예: SP☆12 가 FAILED·ASSIST 뿐)
    # 우도가 아래로 끝없이 커져 탐색 하한(-1000)에 붙고, 전부 했으면 상한에 붙는다 — 그 값은 추정이 아니라
    # 범위의 끝이다. 라이브 첫 실행에서 4명이 -1000 으로 나왔다(2026-09-26). 그런 경우는 값을 내지 않는다.
    if all(ok for _mu, _s, ok in obs) or not any(ok for _mu, _s, ok in obs):
        return None, used
    # 오목 함수의 최댓값 — 황금분할 탐색
    lo, hi = R_LO, R_HI
    g = (math.sqrt(5) - 1) / 2
    a, b = hi - g * (hi - lo), lo + g * (hi - lo)
    fa, fb = _loglik(a, obs), _loglik(b, obs)
    while hi - lo > 0.5:
        if fa < fb:
            lo, a, fa = a, b, fb
            b = lo + g * (hi - lo)
            fb = _loglik(b, obs)
        else:
            hi, b, fb = b, a, fa
            a = hi - g * (hi - lo)
            fa = _loglik(a, obs)
    value = (lo + hi) / 2
    # 한쪽뿐이 아니어도(예: 쉬운 채보 하나만 FAILED 로 달성 못 함) 최댓값이 범위 끝에 붙을 수 있다 — 같은 이유로 버린다
    if value < R_LO + 5 or value > R_HI - 5:
        return None, used
    return round(value), used


def _data_version():
    """채보별 CPI 값의 마지막 적재 시각(정수 초). 60초만 기억한다 — 요청마다 DB 에 묻지 않게."""
    v = cache.get('cpi:version')
    if v is None:
        last = models.CpiValue.objects.order_by('-fetched_at').values_list('fetched_at', flat=True).first()
        v = int(last.timestamp()) if last else 0
        cache.set('cpi:version', v, 60)
    return v


def for_player(player):
    """프로필에 쓸 값. {'value': 1843, 'charts': 312} 또는 None. 10분 캐시."""
    if not ENABLED or player is None:
        return None
    # 키에 채보별 값의 적재 시각을 넣는다. 캐시는 워커(5개)마다 따로 있는 메모리라, update_cpi 가 값을
    # 바꿔도 각 워커는 옛 결과를 10분 들고 있었다 — 첫 적재 직후에는 '기록이 부족합니다' 와 실제 값이
    # 새로고침마다 번갈아 나왔다(2026-09-26 라이브). 적재 시각이 바뀌면 키가 바뀌어 곧바로 다시 계산한다.
    from iidxrank import record_version
    key = 'cpi:%d:%s:%s' % (player.pk, _data_version(), record_version.get(player.pk))
    hit = cache.get(key)
    if hit is not None:
        return hit or None
    clears = dict(models.PlayRecord.objects
                  .filter(player=player, song__songlevel=12,
                          song__songtype__in=('SPH', 'SPA', 'SPL'))
                  .values_list('song_id', 'playclear'))
    value, used = estimate(clears)
    out = {'value': value, 'charts': used} if value is not None else {}
    cache.set(key, out, CACHE_SECONDS)
    return out or None


def details(player, limit=40):
    """CPI 페이지용: 추정값과 '달성 난도가 높은 기록'(역리커맨).

    채보마다 이 플레이어가 달성한 가장 높은 램프 하나를 골라, 그 램프의 적정CPI 가
    높은 순으로 늘어놓는다. prob 은 "이 플레이어 CPI 의 사람이 이 램프를 달성할
    확률" — 낮을수록 실력에 비해 잘 해낸 기록이다.
    """
    from iidxrank import iidx
    summary = for_player(player)
    if not summary:
        return None
    rating = summary['value']
    recs = {sid: (clear, title, ty) for sid, clear, title, ty in (
        models.PlayRecord.objects
        .filter(player=player, song__songlevel=12, song__songtype__in=('SPH', 'SPA', 'SPL'))
        .values_list('song_id', 'playclear', 'song__songtitle', 'song__songtype'))}
    best = {}
    for sid, lamp, mu, width in (models.CpiValue.objects.filter(song_id__in=list(recs))
                                 .values_list('song_id', 'lamp', 'mu', 'width')):
        clear, title, ty = recs[sid]
        clear = 1 if clear == 2 else (clear or 0)
        if mu is None or not width or clear < lamp:
            continue
        if sid not in best or lamp > best[sid]['lamp']:
            s = width / _LN3x2
            best[sid] = {'title': title, 'type': ty, 'lamp': lamp,
                         'lamp_name': iidx.getclearstring_simple(lamp),
                         'mu': round(mu), 'prob': 100.0 / (1 + math.exp(-(rating - mu) / s))}
    top = sorted(best.values(), key=lambda r: -r['mu'])[:limit]
    fetched = models.CpiValue.objects.order_by('-fetched_at').values_list('fetched_at', flat=True).first()
    return {'value': rating, 'charts': summary['charts'], 'top': top, 'fetched_at': fetched}
