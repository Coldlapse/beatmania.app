# -*- coding: utf-8 -*-
"""서비스 현황 — 규모 요약과 서열표 조회수 추이.

예전 '사이트뷰 분석' 은 기간을 고르면 그 기간의 **합계** 를 표로 보여 줬다.
"지난 30일에 SP12H 가 몇 번" 은 알 수 있어도 언제 늘고 줄었는지는 알 수 없다.

`hitcount.Hit` 는 조회 한 건마다 `created` 를 남기므로 시계열을 만들 수 있다
(2025-08-30 부터 쌓여 있다). 그래서 합계 대신 **날짜별 추이** 를 준다.
기간을 바꾸면 페이지를 다시 받지 않고 JSON 만 받아 그래프를 갈아 끼운다.

집계 기준은 KST 다. TIME_ZONE 이 Asia/Seoul 이라 TruncDate/TruncHour 가
알아서 그 기준으로 자른다. UTC 로 자르면 한국 시간 오전 9시에 날짜가 바뀐다.
"""
import datetime

from django.db.models import Count
from django.db.models.functions import TruncDate, TruncHour
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET

from hitcount.models import Hit

from iidxrank import health, models

# 서열표를 두 묶음으로 나눈다.
#
# RankTable.type 으로는 못 나눈다 — onehand 는 type 이 'SP' 지만 DP 쪽에
# 두기로 했고, DBR/11DBR 은 type 자체가 따로다. 이름으로 명시한다.
# 새 서열표가 생기면 여기에 넣어야 그래프에 나온다(아래 _group 참조).
SP_TABLES = ['SP12H', 'SP12N', 'SP11H', 'SP11N', 'SP10H', 'SP10R', 'SP12TEST']
DP_TABLES = ['DP12', 'DP11', 'DP10', 'DBR', '11DBR', 'onehand']

PERIODS = {
    # key: (버튼에 쓸 이름, 문장에 쓸 구절, 거슬러 갈 길이, 시간 단위인가)
    #
    # 문장 쪽은 '동안'까지 포함한 구절로 둔다. 화면에서 라벨 뒤에 '동안'을
    # 붙이면 '오늘 동안'이 되어 어색하다. 조사가 붙고 안 붙고는 말의 문제라
    # 라벨과 함께 있어야 한다.
    'today': ('오늘', '오늘', datetime.timedelta(days=1), True),
    'week': ('지난 7일', '지난 7일 동안', datetime.timedelta(days=7), False),
    'month': ('지난 30일', '지난 30일 동안', datetime.timedelta(days=30), False),
    'year': ('지난 365일', '지난 365일 동안', datetime.timedelta(days=365), False),
}
DEFAULT_PERIOD = 'week'


def _group(tablename):
    if tablename in SP_TABLES:
        return 'SP'
    if tablename in DP_TABLES:
        return 'DP'
    # 목록에 없는 새 서열표. 버리지 않고 type 으로 넘겨짚는다.
    return 'DP' if tablename.upper().startswith('DP') else 'SP'


def _service_numbers():
    """문장에 넣을 수치. 한 번에 세고 캐시하지 않는다 — 초당 수십 번 열릴
    페이지가 아니고, 캐시를 두면 '지금 몇 명' 이라는 말이 거짓이 된다."""
    return {
        'users': models.User.objects.count(),
        'players_with_record': (models.PlayRecord.objects
                                .values('player_id').distinct().count()),
        'records': models.PlayRecord.objects.count(),
        'songs': models.Song.objects.count(),
        'tables': models.RankTable.objects.count(),
    }


# 업타임 막대에 몇 칸을 보여 줄 것인가. 5분 간격 점검 기준으로 24시간.
UPTIME_SLOTS = 48
UPTIME_WINDOW = datetime.timedelta(hours=24)

# 마지막 점검이 이보다 오래됐으면 화면을 열 때 한 번 돌린다.
#
# 점검은 원래 `manage.py healthcheck` 를 주기적으로 불러 쌓는 것이고, 화면은
# 그것을 읽기만 한다. 그런데 그 주기 작업이 없거나 멈춰 있으면 지금 칸이
# 계속 비어 회색으로 남는다 — 서비스는 멀쩡한데 화면만 고장 난 것처럼 보인다.
# 그래서 오래됐을 때만 그 자리에서 한 번 채운다. 자주 열려도 이 간격보다
# 잦게는 돌지 않는다.
SELF_CHECK_AFTER = datetime.timedelta(minutes=5)


def _refresh_if_stale():
    """마지막 점검이 오래됐으면 한 번 돌려 기록한다."""
    newest = (models.HealthCheck.objects
              .order_by('-checked_at')
              .values_list('checked_at', flat=True).first())
    if newest and timezone.now() - newest < SELF_CHECK_AFTER:
        return
    try:
        results = health.run_all()
    except Exception:
        # 상태 페이지가 점검 때문에 통째로 죽으면 안 된다.
        return
    models.HealthCheck.objects.bulk_create([
        models.HealthCheck(target=r['target'], status=r['status'],
                           latency_ms=r['latency_ms'], note=r['note'][:200],
                           checked_at=r['checked_at'])
        for r in results])


def _uptime():
    """대상별로 최근 24시간을 UPTIME_SLOTS 칸으로 접어 돌려준다.

    한 칸 안에 여러 번 점검한 결과가 들어가면 **가장 나쁜 것**을 남긴다.
    30분 중 한 번이라도 죽었으면 그 칸은 초록이면 안 된다.
    """
    now = timezone.localtime()
    start = now - UPTIME_WINDOW
    slot = UPTIME_WINDOW / UPTIME_SLOTS
    rank = {health.OK: 0, health.DEGRADED: 1, health.DOWN: 2}

    rows = (models.HealthCheck.objects
            .filter(checked_at__gte=start)
            .values('target', 'status', 'latency_ms', 'checked_at'))

    grid = {t: [None] * UPTIME_SLOTS for t in health.CHECKS}
    latest = {}
    lat_sum = {t: [0, 0] for t in health.CHECKS}
    for r in rows:
        t = r['target']
        if t not in grid:
            continue
        i = int((timezone.localtime(r['checked_at']) - start) / slot)
        i = min(max(i, 0), UPTIME_SLOTS - 1)
        cur = grid[t][i]
        if cur is None or rank[r['status']] > rank[cur]:
            grid[t][i] = r['status']
        if t not in latest or r['checked_at'] > latest[t]['checked_at']:
            latest[t] = r
        lat_sum[t][0] += r['latency_ms']
        lat_sum[t][1] += 1

    out = []
    for t in health.CHECKS:
        seen = [s for s in grid[t] if s]
        ok = sum(1 for s in seen if s == health.OK)
        out.append({
            'key': t,
            'label': health.LABELS[t],
            'description': health.DESCRIPTIONS[t],
            'slots': grid[t],
            'current': latest.get(t, {}).get('status'),
            'note': latest.get(t, {}).get('note', ''),
            'checked_at': latest.get(t, {}).get('checked_at'),
            # 점검이 한 번도 안 돌았으면 비율을 지어내지 않는다.
            'uptime': round(100.0 * ok / len(seen), 1) if seen else None,
            'avg_ms': int(lat_sum[t][0] / lat_sum[t][1]) if lat_sum[t][1] else None,
        })
    return out


@require_GET
def service_status(request):
    _refresh_if_stale()
    return render(request, 'service_status.html', {
        'numbers': _service_numbers(),
        'periods': [(k, _(PERIODS[k][0]))
                    for k in ('today', 'week', 'month', 'year')],
        'default_period': DEFAULT_PERIOD,
        'health': _uptime(),
        'health_stale_minutes': int(SELF_CHECK_AFTER.total_seconds() // 60),
        'health_window_hours': int(UPTIME_WINDOW.total_seconds() // 3600),
    })


@require_GET
def views_json(request):
    """기간별 조회수 시계열.

    반환: {'labels': [...], 'unit': 'hour'|'day',
           'groups': {'SP': [{'name':..., 'data':[...]}, ...], 'DP': [...]}}
    """
    key = request.GET.get('period', DEFAULT_PERIOD)
    if key not in PERIODS:
        key = DEFAULT_PERIOD
    _btn_label, sentence_label, span, hourly = PERIODS[key]

    now = timezone.localtime()
    if hourly:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        trunc = TruncHour('created')
        step = datetime.timedelta(hours=1)
    else:
        start = (now - span).replace(hour=0, minute=0, second=0, microsecond=0)
        trunc = TruncDate('created')
        step = datetime.timedelta(days=1)

    # order_by() 로 기본 정렬을 지운다. Hit 는 Meta.ordering 이 ('-created',)
    # 라서, 지우지 않으면 Django 가 created 를 GROUP BY 에 끼워 넣는다.
    # 그러면 묶음이 조회 한 건 단위로 쪼개진다 — 아래 세션 집계에서 실제로
    # 고유 세션 수가 전체 조회 수와 같아지는 결과가 나왔다.
    rows = (Hit.objects
            .filter(hitcount__content_type__model='ranktable', created__gte=start)
            .order_by()
            .annotate(bucket=trunc)
            .values('bucket', 'hitcount__object_pk')
            .annotate(n=Count('id')))

    # object_pk 는 문자열이다. 이름으로 바꾸려면 한 번에 읽어 둔다.
    names = {str(pk): name for pk, name in
             models.RankTable.objects.values_list('id', 'tablename')}

    # 눈금을 먼저 만든다. 조회가 0 인 날도 자리를 남겨야 선이 끊기지 않는다.
    ticks = []
    cur = start
    end = now
    while cur <= end:
        ticks.append(cur)
        cur += step
    if hourly:
        keys = [t.strftime('%H:00') for t in ticks]
    else:
        keys = [t.strftime('%Y-%m-%d') for t in ticks]
    index = {k: i for i, k in enumerate(keys)}

    series = {}
    for r in rows:
        name = names.get(str(r['hitcount__object_pk']))
        if not name:
            continue          # 지워진 서열표
        b = r['bucket']
        if hourly:
            k = timezone.localtime(b).strftime('%H:00') if timezone.is_aware(b) \
                else b.strftime('%H:00')
        else:
            k = b.strftime('%Y-%m-%d')
        i = index.get(k)
        if i is None:
            continue
        series.setdefault(name, [0] * len(keys))[i] += r['n']

    # --- 사이트뷰 ---------------------------------------------------------
    #
    # "서열표 조회수의 합"은 사이트뷰가 아니다. 한 사람이 한 번 들어와 표
    # 세 개를 보면 합계에는 3 이 더해진다(실측: 조회 13,849건 / 고유 세션
    # 9,969개 = 세션당 1.39표). 그래서 세션 단위로 따로 센다.
    #
    # 한계도 분명히 해 둔다 — hitcount 는 **서열표 페이지에만** 걸려 있다.
    # /about/ 이나 /status/ 만 보고 나간 방문은 여기 잡히지 않는다.
    # 사이트 전체를 세려면 모든 페이지에 조회 기록을 남겨야 하는데, 그건
    # 지금 구조를 바꾸는 일이라 하지 않았다.
    visit_rows = (Hit.objects
                  .filter(hitcount__content_type__model='ranktable',
                          created__gte=start)
                  .order_by()                     # 위와 같은 이유
                  .annotate(bucket=trunc)
                  .values('bucket')
                  .annotate(n=Count('session', distinct=True)))
    visits = [0] * len(keys)
    for r in visit_rows:
        b = r['bucket']
        k = (timezone.localtime(b).strftime('%H:00')
             if hourly and timezone.is_aware(b)
             else b.strftime('%H:00' if hourly else '%Y-%m-%d'))
        i = index.get(k)
        if i is not None:
            visits[i] += r['n']

    groups = {'SP': [], 'DP': []}
    for name, data in series.items():
        groups[_group(name)].append({'name': name, 'data': data,
                                     'total': sum(data)})
    for g in groups.values():
        g.sort(key=lambda d: d['total'], reverse=True)

    return JsonResponse({
        'labels': keys,
        'unit': 'hour' if hourly else 'day',
        'groups': groups,
        # 문장을 화면에서 이어 붙이지 않고 여기서 완성한다. 조각으로 넘기면
        # 언어마다 어순이 달라 옮길 수가 없다(영어는 기간이 뒤에 온다).
        'visits': {
            'data': visits,
            'total': sum(visits),
            'sentence': _('beatmania.app 은 %(phrase)s <b>%(n)s</b> 번의 '
                          '방문을 기록했습니다.') % {
                'phrase': _(sentence_label),
                'n': '{:,}'.format(sum(visits)),
            },
        },
    })
