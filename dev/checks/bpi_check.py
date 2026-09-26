"""BPI(iidxrank/bpi.py)를 확인한다.

  1. 계산: BPIManager 의 npm @bpim/bpicalc 0.3.0 이 낸 값과 같은가(기준값은 아래에 박아 둔다)
  2. 수집: 원본 응답 모양, -1 = 없음, 망가진 응답은 거부
  3. 최고값 붙잡기(ratchet)와 EX SCORE 를 손으로 낮췄을 때 풀기
  4. 페이지: 공개 규칙·공유 버튼·프로필 뱃지(CPI 왼쪽)

기준값을 다시 뽑으려면 scratchpad 의 fx.mjs 처럼 BpiV2 에 아래 FIXTURE 를 넣어 돌린다.

    python dev/checks/bpi_check.py
"""
import _bootstrap  # noqa: F401
import django

django.setup()

from types import SimpleNamespace as NS  # noqa: E402

from django.core.cache import cache  # noqa: E402

from iidxrank import bpi, models  # noqa: E402

fails = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name, (' — %s' % detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


# 원본 API 의 실제 ☆12 채보 다섯(2026-09-26 받은 값)
FIXTURE = [
    {"songId": 1016, "notes": 1912, "wrScore": 3807, "kaidenAvg": 3086, "coef": 0.954, "mu": -6.5767, "sigma": 0.5224, "residualVar": 0.0812},
    {"songId": 615, "notes": 1752, "wrScore": 3450, "kaidenAvg": 2705, "coef": 1.025, "mu": -6.6745, "sigma": 0.4279, "residualVar": 0.078},
    {"songId": 730, "notes": 1492, "wrScore": 2980, "kaidenAvg": 2658, "coef": 0.949, "mu": -5.6684, "sigma": 0.6437, "residualVar": 0.0656},
    {"songId": 895, "notes": 1763, "wrScore": 3512, "kaidenAvg": 2928, "coef": 0.992, "mu": -6.2969, "sigma": 0.5603, "residualVar": 0.0621},
    {"songId": 1079, "notes": 1449, "wrScore": 2880, "kaidenAvg": 2366, "coef": 1.023, "mu": -6.243, "sigma": 0.5132, "residualVar": 0.1077},
]
# @bpim/bpicalc 0.3.0 의 결과. 점수는 [0, 노트×1.6, 개전 평균, 세계 기록, 만점]
EXPECT_SINGLE = [[-15, 1.32, 2.46, 100, 184.09], [-15, 6.91, 2.43, 100, 276.23], [-15, -15, 0.2, 100, 144.3],
                 [-15, -4.2, 0.33, 100, 187.52], [-15, -0.53, 1.74, 100, 207.17]]
PLAYED = {1016: 3250, 615: 2628, 895: 3173}       # 합산 기준: 다섯 채보 중 셋을 쳤다
EXPECT_TOTAL = 8.54
EXPECT_LATENT = 0.4056415896834595


def val(x, level=12):
    return NS(source_id=x['songId'], notes=x['notes'], wr=x['wrScore'], coef=x['coef'], mu=x['mu'],
              sigma=x['sigma'], residual_var=x['residualVar'], level=level)


print('=== 1. 계산 (원본 패키지와 같은 값) ===')
charts = [bpi.Chart(val(x)) for x in FIXTURE]
got = [[c.bpi(e) for e in (0, c.v.notes * 16 // 10, x['kaidenAvg'], x['wrScore'], c.v.notes * 2)]
       for c, x in zip(charts, FIXTURE)]
check('단일 BPI 25개', got == EXPECT_SINGLE, str(got))
check('합산 BPI', bpi.total_bpi(charts, PLAYED) == EXPECT_TOTAL, str(bpi.total_bpi(charts, PLAYED)))
a, _info = bpi.latent_skill([(c, PLAYED[c.v.source_id]) for c in charts if c.v.source_id in PLAYED])
check('잠재 실력', abs(a - EXPECT_LATENT) < 1e-12, str(a))
check('기록이 없으면 None(원 사이트는 -15)', bpi.total_bpi(charts, {}) is None)
check('범위 밖 기록(☆11)은 합산 실력 추정에 들어가지 않음',
      bpi.total_bpi(charts, {**PLAYED, 99999: 10}) == EXPECT_TOTAL)
nop = bpi.Chart(NS(source_id=1, notes=1000, wr=1900, coef=None, mu=None, sigma=None, residual_var=None, level=12))
check('mu 없는 채보는 BPI 없음', nop.bpi(1500) is None)
check('JS 반올림(.5 는 위로)', bpi._js_round2(0.125) == 0.13 and bpi._js_round2(-0.125) == -0.12)

print('=== 2. 수집 ===')
import json  # noqa: E402

saved = list(models.BpiValue.objects.all())
real_get = bpi.requests.get


class Resp:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


song = models.Song.objects.filter(songtype='SPA', songlevel=12).order_by('id').first()
rows = []
for i in range(600):
    rows.append({'songId': 100000 + i, 'title': 'zz 없는 곡 %d' % i, 'difficulty': 'ANOTHER', 'difficultyLevel': 12,
                 'notes': 1000, 'wrScore': 1990, 'kaidenAvg': 1700, 'coef': -1, 'mu': None, 'sigma': None, 'residualVar': None})
rows[0].update(title=song.songtitle, coef=0.95, mu=-6.0, sigma=0.5, residualVar=0.07)
rows.append({'songId': 1, 'title': 'x', 'difficulty': 'BEGINNER', 'difficultyLevel': 1, 'notes': 1})
try:
    bpi.requests.get = lambda *x, **k: Resp({'error': False, 'body': rows})
    r = bpi.fetch_and_store()
    check('채보 수(모르는 난이도는 뺌)', r['charts'] == 600 and r['level12'] == 600, str(r['charts']))
    v0 = models.BpiValue.objects.get(source_id=100000)
    check('곡 DB 와 연결', v0.song_id == song.id and r['matched'] >= 1)
    check('coef -1 은 없음(None)으로', models.BpiValue.objects.get(source_id=100001).coef is None and v0.coef == 0.95)
    bpi.requests.get = lambda *x, **k: Resp({'error': False, 'body': rows[:10]})
    try:
        bpi.fetch_and_store()
        check('망가진 응답(채보가 너무 적음)은 거부', False)
    except ValueError:
        check('망가진 응답(채보가 너무 적음)은 거부', models.BpiValue.objects.count() == 600)
finally:
    bpi.requests.get = real_get
    models.BpiValue.objects.all().delete()
    models.BpiValue.objects.bulk_create(saved)

print('=== 3~4. 최고값 · 페이지 ===')
from django.contrib.auth.models import User  # noqa: E402
from django.test import Client  # noqa: E402

u = User.objects.create_user('zz_bpi_check', password='x-Unused-123')
try:
    from iidxrank.rankpage import newplayer
    pl = newplayer(u)
    models.AccountSecurity.objects.update_or_create(user=u, defaults={'newrulepassed': True})
    c = Client()
    check('남의 공개 페이지 200', c.get('/u/zz_bpi_check/bpi/').status_code == 200)
    pl.private = True
    pl.save()
    r1, r2 = c.get('/u/zz_bpi_check/bpi/'), c.get('/u/zz_nobody_here/bpi/')
    check('비공개 = 없는 계정 (둘 다 404)', r1.status_code == r2.status_code == 404)
    pl.private = False
    pl.save()
    c.force_login(u)
    page = c.get('/bpi/').content.decode()
    check('기록이 없으면 안내 문구', 'BPI 를 계산할 기록이 없습니다' in page)
    check('비로그인 /bpi/ 도 200', Client().get('/bpi/').status_code == 200)
    prof0 = c.get('/table/SP12H/').content.decode()
    check("기록이 없어도 BPI 뱃지는 보임('-', 흐리게)", 'profile-cpi profile-bpi is-empty' in prof0
          and '<span class="profile-cpi-value">-</span>' in prof0)

    vals = list(models.BpiValue.objects.filter(level=12, song__isnull=False, mu__isnull=False)[:20])
    if len(vals) < 20:
        print('SKIP 곡 DB 와 연결된 BPI 값이 부족합니다 — update_bpi 를 먼저 돌리세요')
    else:
        models.PlayRecord.objects.bulk_create([
            models.PlayRecord(player=pl, song_id=v.song_id, playclear=5, playscore=6, exscore=int(v.notes * 1.8))
            for v in vals])
        cache.clear()
        s1 = bpi.for_player(pl)
        check('합산 값 계산', s1 and s1['value'] == s1['fresh'] and s1['charts12'] == 20, str(s1))
        page = c.get('/bpi/').content.decode()
        check('내 페이지: 값·공유 버튼·주소', 'bm-cpi-hero' in page and 'data-share-path="/u/zz_bpi_check/bpi/"' in page)
        prof = c.get('/table/SP12H/').content.decode()
        check('프로필 뱃지(BPI 가 CPI 칸 모양)', 'profile-cpi profile-bpi' in prof and 'href="/bpi/"' in prof)
        check('남이 보면 공유 버튼 없음', 'id="share"' not in Client().get('/u/zz_bpi_check/bpi/').content.decode())
        # 낮은 새 기록 하나 → 새로 계산한 값은 내려가도 보여 주는 값은 최고값
        low = models.BpiValue.objects.filter(level=12, song__isnull=False, mu__isnull=False) \
            .exclude(id__in=[v.id for v in vals]).first()
        models.PlayRecord.objects.create(player=pl, song_id=low.song_id, playclear=1, exscore=int(low.notes * 0.9))
        cache.clear()
        s2 = bpi.for_player(pl)
        check('낮은 기록이 더해지면 계산값은 내려가도 표시는 최고값',
              s2['fresh'] < s1['fresh'] and s2['value'] == s1['value'], '%s → %s' % (s1, s2))
        # 손으로 EX SCORE 를 낮추면 최고값을 푼다
        r = c.post('/modify/', {'action': 'exscore', 'v': json.dumps({'id': vals[0].song_id, 'exscore': 100})})
        check('EX SCORE 저장', r.json().get('code') == 0, r.content.decode()[:200])
        check('손으로 낮추면 최고값을 지운다', not models.BpiBest.objects.filter(player=pl).exists())
        cache.clear()
        s3 = bpi.for_player(pl)
        check('지운 뒤에는 지금 기록으로 다시', s3['value'] == s3['fresh'] < s1['value'], str(s3))
        det = bpi.details(pl)
        check('BPI 높은 순 목록', [x['bpi'] for x in det['top']] == sorted([x['bpi'] for x in det['top']], reverse=True)
              and len(det['top']) == 21)
    models.PlayRecord.objects.filter(player=pl).delete()
finally:
    models.Player.objects.filter(user=u).delete()
    u.delete()

print('')
print('총 실패: %d' % len(fails))
