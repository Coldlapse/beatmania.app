# -*- coding: utf-8 -*-
"""BPI(Beat Power Indicator) V2 — BPIManager(bpi2.poyashi.me)와 같은 식으로 계산한다.

BPI 는 BPIManager 가 매기는 SP☆11·12 EX SCORE 실력 지표다. 2026-09-15 부터 V2(분포 기반 재정의)를
쓴다. CPI 와 달리 계산식이 공개돼 있어 **추정이 아니라 같은 계산**이다 — 채보별 값(mu·sigma 등)은
원 사이트 API 에서 받고, 식은 아래 두 곳을 옮겼다.

  계산식    npm @bpim/bpicalc (MIT) src/core.ts · src/v2.ts
  모델 상수  BPIManager2 src/constants/iidx/newBpi/modelConstants.ts
            (생성 2026-09-09, 버전 33, 5113명). 원 사이트가 다시 만들면 아래 상수를 바꾼다.

단일 채보
  t = -ln(max(0.5, m - s))              m = 노트×2, s = EX SCORE
  z = (t - mu) / sigma,  z100 = 세계 기록의 z
  BPI = 100 · sign(r) · |r|^k,  r = (z - z0) / (z100 - z0)      (-15 아래는 -15)
  k 는 곡별 곡선 지수(coef)와 세계 기록 위치 보정(gamma)의 곱

합산 BPI (원 사이트 '総合BPI')
  대상은 원본 목록의 ☆12 전부(INF 671채보). 친 채보는 그 BPI, 안 친 채보는 플레이어 잠재 실력 a 로
  예측한 값(신뢰도 w 로 -15 와 섞음)을 쓰고, 이동 멱평균(c=15, k'=ln n / ln(115/65))으로 모은다.
  잠재 실력 a 는 ☆12 EX SCORE 로 추정한다. 원 사이트 주석은 '☆11·12 전부' 라고 하지만, 실제 호출
  (subhandlers/stats/totalBpi.ts → calculateTotalBPI(observations, level12Master))은 채보 값을 ☆12 목록에서만
  찾아 ☆11 관측이 mu 없는 채보가 되어 빠진다. 화면에 나오는 값을 따르므로 ☆12 만 쓴다(2026-09-26 확인).
  안 친 채보의 예측이 새 기록 하나로 내려갈 수 있어서, 원 사이트는 저장할 때 이전 최고값과 max 를
  잡는다(ratchetTotalBpi). 같이 따른다 — models.BpiBest.

데이터를 가져오는 쪽 예절
  하루 한 번, 요청 한 번(update_bpi 명령). User-Agent 에 누구인지 밝힌다. 원 사이트 운영자가
  원하지 않으면 ENABLED 를 끄고 표를 비우면 된다.
"""
import math

import requests
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from iidxrank import models

ENABLED = True                     # 운영자 요청이 오면 끈다(화면·수집 모두 멈춘다)
SOURCE_URL = 'https://bpi2.poyashi.me/api/v2/songs?version=INF'
SITE_URL = 'https://bpi2.poyashi.me/'
USER_AGENT = 'beatmania.app (https://beatmania.app) - daily BPI reference fetch'
CACHE_SECONDS = 600
TYPES = {'HYPER': 'SPH', 'ANOTHER': 'SPA', 'LEGGENDARIA': 'SPL'}

# ── 모델 상수(BPIManager2 modelConstants.ts, 2026-09-09) ─────────────────
Z0 = -0.19383932671707751
Z100_MEDIAN = 6.516395340703802
Z_REF = 1.9481138704797247
RESIDUAL_RMSE = 0.3012
Z100_IQR = 1.1916
COEF_MEDIAN = 0.949
CONSTANTS_DATE = '2026-09-09'

# ── @bpim/bpicalc V2_DEFAULTS ─────────────────────────────────────────────
FLOOR = -15.0
SHIFT = 15.0
GAMMA_CLAMP = (0.3, 3.0)
CURVE_EXP_CLAMP = (0.62, 3.0)


def _js_round2(x):
    """JavaScript Math.round(x * 100) / 100. 파이썬 round 는 짝수 쪽으로 반올림해 .5 에서 어긋난다."""
    return math.floor(x * 100 + 0.5) / 100


def _sign(x):
    return (x > 0) - (x < 0)


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def t_of(score, m):
    miss = max(0.5, m - min(max(score, 0), m))
    return -math.log(miss)


def _gamma(z100):
    g_ref = Z100_MEDIAN - Z0
    g_song = z100 - Z0
    r_typ = (Z_REF - Z0) / g_ref
    r_song = (Z_REF - Z0) / g_song
    if r_typ <= 0 or r_typ >= 1 or r_song <= 0 or r_song >= 1:
        return 1.0
    raw = math.log(r_typ) / math.log(r_song)
    if not math.isfinite(raw):
        return 1.0
    clamped = _clamp(raw, *GAMMA_CLAMP)
    d = abs(z100 - Z100_MEDIAN) / Z100_IQR
    w = d * d / (d * d + 1)
    return 1 + w * (clamped - 1)


class Chart:
    """채보 하나. v 는 BpiValue(또는 같은 속성을 가진 것)."""
    __slots__ = ('v', 'm', 'z100', 'k')

    def __init__(self, v):
        self.v = v
        self.m = v.notes * 2
        self.z100 = self.k = None
        if v.mu is None or v.sigma is None or not v.notes or v.wr is None:
            return
        z100 = (t_of(v.wr, self.m) - v.mu) / v.sigma
        if abs(z100 - Z0) < 1e-9:
            return
        coef = v.coef if v.coef is not None else COEF_MEDIAN
        self.z100 = z100
        self.k = _clamp(_gamma(z100) * coef, *CURVE_EXP_CLAMP)

    def bpi(self, ex):
        if self.k is None:
            return None
        z = (t_of(ex, self.m) - self.v.mu) / self.v.sigma
        r = (z - Z0) / (self.z100 - Z0)
        return max(FLOOR, _js_round2(100 * _sign(r) * abs(r) ** self.k))

    def raw_from_skill(self, a):
        if self.k is None:
            return None
        r = (a - Z0) / (self.z100 - Z0)
        return 100 * _sign(r) * abs(r) ** self.k


def latent_skill(observations):
    """[(Chart, ex)] → (축소 추정한 잠재 실력 a 또는 None, 정보량)."""
    gvar = RESIDUAL_RMSE * RESIDUAL_RMSE
    num = info = 0.0
    for c, ex in observations:
        v = c.v
        if v.mu is None or v.sigma is None or not v.notes:
            continue
        ev = v.residual_var if v.residual_var is not None else gvar
        num += v.sigma * (t_of(ex, c.m) - v.mu) / ev
        info += v.sigma * v.sigma / ev
    return (num / (info + 1) if info > 0 else None), info


def total_bpi(scope, ex_by_source):
    """BpiCalculator.calculateTotalBPI 와 같다. scope: 원본 ☆12 전부의 Chart, ex_by_source: {source_id: ex}.

    잠재 실력은 scope 안의 기록으로만 추정한다(머리말 참고). → 합산 BPI 또는 None(쓸 기록 없음).
    원 사이트는 None 대신 -15 를 준다.
    """
    by_source = {c.v.source_id: c for c in scope}
    obs = [(by_source[s], ex) for s, ex in ex_by_source.items() if s in by_source]
    a, info = latent_skill(obs)
    bpis = []
    for c in scope:
        ex = ex_by_source.get(c.v.source_id)
        if ex is not None:
            v = c.bpi(ex)
        elif info > 0:
            raw = c.raw_from_skill(a)
            if raw is None:
                v = None
            else:
                w = info / (info + 1)
                v = max(FLOOR, _js_round2(w * raw + (1 - w) * FLOOR))
        else:
            v = None
        if v is not None:
            bpis.append(v)
    if not bpis:
        return None
    n = len(scope)
    bpis.sort(reverse=True)
    kp = math.log(n) / math.log((100 + SHIFT) / (50 + SHIFT))
    s = 0.0
    for i in range(n):
        b = bpis[i] if i < len(bpis) else FLOOR
        s += (b + SHIFT) ** kp / n
    return _js_round2(s ** (1 / kp) - SHIFT)


# ── 수집 ────────────────────────────────────────────────────────────────────

def fetch_and_store():
    """원 사이트에서 받아 BpiValue 를 통째로 갈아 끼운다. 요약을 돌려준다."""
    from iidxrank.records_import import norm_title
    r = requests.get(SOURCE_URL, timeout=60, headers={'User-Agent': USER_AGENT})
    r.raise_for_status()
    data = r.json()
    body = data.get('body') if isinstance(data, dict) else None
    if data.get('error') or not isinstance(body, list) or len(body) < 500:
        # 응답 모양이 바뀌었다. 멀쩡한 값을 빈 값으로 덮지 않는다.
        raise ValueError('BPI 목록을 읽지 못했습니다 (%s)' % (len(body) if isinstance(body, list) else type(body).__name__))

    index = {}
    for sid, title, ty in (models.Song.objects.filter(songtype__in=('SPH', 'SPA', 'SPL'))
                           .values_list('id', 'songtitle', 'songtype')):
        index.setdefault((norm_title(title), ty), []).append(sid)

    def num(x, cast=float):
        return None if x is None else cast(x)

    rows, missing = [], []
    now = timezone.now()
    for x in body:
        ty = TYPES.get(x.get('difficulty'))
        if ty is None:
            continue
        ids = index.get((norm_title(x['title']), ty), [])
        if len(ids) != 1:
            missing.append('%s [%s]' % (x['title'], ty))
        coef = num(x.get('coef'))
        rows.append(models.BpiValue(
            source_id=int(x['songId']), song_id=ids[0] if len(ids) == 1 else None,
            title=x['title'][:200], songtype=ty, level=int(x['difficultyLevel']),
            notes=int(x['notes']), wr=num(x.get('wrScore'), int), kavg=num(x.get('kaidenAvg'), int),
            coef=None if coef is None or coef < 0 else coef,      # 원본은 '없음' 을 -1 로 준다
            mu=num(x.get('mu')), sigma=num(x.get('sigma')), residual_var=num(x.get('residualVar')),
            fetched_at=now))
    with transaction.atomic():
        models.BpiValue.objects.all().delete()
        models.BpiValue.objects.bulk_create(rows)
    # 캐시는 지우지 않는다. 키에 적재 시각이 들어 있어(_data_version) 웹 워커가 곧 새 값으로 계산한다.
    return {'charts': len(rows), 'matched': len(rows) - len(missing), 'missing': missing,
            'level12': sum(1 for x in rows if x.level == 12)}


# ── 플레이어 ────────────────────────────────────────────────────────────────

def _data_version():
    """채보별 값의 마지막 적재 시각(정수 초). 60초만 기억한다."""
    v = cache.get('bpi:version')
    if v is None:
        last = models.BpiValue.objects.order_by('-fetched_at').values_list('fetched_at', flat=True).first()
        v = int(last.timestamp()) if last else 0
        cache.set('bpi:version', v, 60)
    return v


def _compute(player):
    """→ (합산 BPI 또는 None, [(Chart, ex, bpi)] 친 채보, 친 ☆12 수)."""
    values = list(models.BpiValue.objects.all())
    if not values:
        return None, [], 0
    charts = [Chart(v) for v in values]
    by_song = {c.v.song_id: c for c in charts if c.v.song_id}
    ex_by_source, played = {}, []
    for sid, ex in (models.PlayRecord.objects
                    .filter(player=player, song_id__in=list(by_song), exscore__isnull=False)
                    .values_list('song_id', 'exscore')):
        c = by_song[sid]
        ex_by_source[c.v.source_id] = ex
        played.append((c, ex, c.bpi(ex)))
    scope = [c for c in charts if c.v.level == 12]
    total = total_bpi(scope, ex_by_source)
    return total, played, sum(1 for c, _e, _b in played if c.v.level == 12)


def _ratchet(player, fresh):
    """이전 최고값과 max. 새 값이 더 높으면 저장한다."""
    best = models.BpiBest.objects.filter(player=player).values_list('value', flat=True).first()
    if best is not None and best >= fresh:
        return best
    models.BpiBest.objects.update_or_create(player=player, defaults={'value': fresh})
    return fresh


def for_player(player):
    """프로필에 쓸 값. {'value': 52.31, 'fresh': 50.02, 'charts': 312} 또는 None. 10분 캐시."""
    if not ENABLED or player is None:
        return None
    from iidxrank import record_version
    # 채보별 값의 적재 시각 + 이 플레이어 기록의 버전. 둘 중 하나가 바뀌면 곧바로 다시 계산한다.
    key = 'bpi:%d:%s:%s' % (player.pk, _data_version(), record_version.get(player.pk))
    hit = cache.get(key)
    if hit is not None:
        return hit or None
    fresh, played, n12 = _compute(player)
    out = {}
    if fresh is not None:
        out = {'value': _ratchet(player, fresh), 'fresh': fresh, 'charts': len(played), 'charts12': n12}
    cache.set(key, out, CACHE_SECONDS)
    return out or None


def forget_best(player):
    """합산 최고값을 지운다 — EX SCORE 를 손으로 낮췄을 때(잘못 넣은 값이 최고값을 붙잡지 않게)."""
    models.BpiBest.objects.filter(player=player).delete()
    # 캐시는 기록 버전으로 바뀐다(이 함수를 부르는 views.modify 가 record_version.bump 를 한다).


def details(player, limit=50):
    """BPI 페이지용: 합산 값과 BPI 가 높은 기록."""
    summary = for_player(player)
    if not summary:
        return None
    _fresh, played, _n = _compute(player)
    top = []
    for c, ex, b in played:
        if b is None:
            continue
        top.append({'title': c.v.title, 'type': c.v.songtype, 'level': c.v.level,
                    'ex': ex, 'max': c.m, 'rate': 100.0 * min(ex, c.m) / c.m if c.m else 0,
                    'bpi': b})
    top.sort(key=lambda r: -r['bpi'])
    fetched = models.BpiValue.objects.order_by('-fetched_at').values_list('fetched_at', flat=True).first()
    return dict(summary, top=top[:limit], fetched_at=fetched, constants_date=CONSTANTS_DATE)
