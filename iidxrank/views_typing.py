# -*- coding: utf-8 -*-
"""일일 타건 기록과 API 토큰.

두 화면으로 나눴다. 예전에는 한 페이지에 토큰 발급과 기록이 같이 있었는데,
토큰은 계정 설정에 가깝고 기록은 남에게 보여 줄 것이라 성격이 다르다.

기록 화면은 **로그인하지 않아도 열린다.** 리더보드가 있어서 남이 봐도
의미가 있기 때문이다. 본인 기록 부분만 로그인한 사람에게 보인다.
"""
import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from iidxrank import models

PERIODS = {
    # key: (버튼 이름, 문장에 쓸 구절, 거슬러 갈 날수 / None 이면 전체)
    'month': ('지난 30일', '지난 30일 동안', 30),
    'year': ('지난 1년', '지난 1년 동안', 365),
    'all': ('전체', '지금까지', None),
}
DEFAULT_PERIOD = 'month'
TOP_N = 10


def _period(key):
    if key not in PERIODS:
        key = DEFAULT_PERIOD
    return key, PERIODS[key]


def _start_date(days):
    if days is None:
        return None
    return timezone.localdate() - datetime.timedelta(days=days - 1)


def _visible_logs(days):
    """집계 대상 기록.

    **프로필을 비공개로 둔 사람은 순위에서 뺀다.** 순위표는 아이디와 프로필
    사진을 드러내는 자리라, 비공개를 켠 사람을 여기 올리면 그 설정이
    무의미해진다. 본인이 자기 기록을 보는 것은 막지 않는다(아래 별도 처리).

    Player 는 User 당 여러 행이 있을 수 있는 구조(FK)라 exclude 로 거른다.
    비공개 Player 를 가진 사용자를 통째로 뺀다.
    """
    qs = models.TypingLog.objects.all()
    start = _start_date(days)
    if start:
        qs = qs.filter(date__gte=start)
    hidden = (models.Player.objects.filter(private=True)
              .values_list('user_id', flat=True))
    return qs.exclude(user_id__in=list(hidden))


def _avatar_url(player):
    try:
        return player.avatar.url if player and player.avatar else ''
    except ValueError:
        return ''


def _leaderboard(key, request_user):
    key, (_btn, phrase, days) = _period(key)

    rows = list(_visible_logs(days)
                .values('user_id', 'user__username')
                .annotate(total=Sum('count'))
                .order_by('-total'))

    # 프로필 사진은 한 번에 읽는다. 순위 열 개마다 조회하면 N+1 이다.
    ids = [r['user_id'] for r in rows[:TOP_N]]
    players = {p.user_id: p for p in
               models.Player.objects.filter(user_id__in=ids)}

    top = []
    for i, r in enumerate(rows[:TOP_N], 1):
        p = players.get(r['user_id'])
        top.append({
            'rank': i,
            'username': r['user__username'],
            'total': r['total'],
            'avatar': _avatar_url(p),
            'is_me': bool(request_user and request_user.is_authenticated
                          and r['user_id'] == request_user.id),
        })

    # 본인 순위. 비공개를 켠 사람은 위 목록에 없으므로 여기서도 안 잡힌다.
    # 그때는 순위 없이 본인 합계만 따로 낸다.
    me = None
    if request_user and request_user.is_authenticated:
        for i, r in enumerate(rows, 1):
            if r['user_id'] == request_user.id:
                me = {'rank': i, 'total': r['total'], 'of': len(rows),
                      'ranked': True}
                break
        if me is None:
            qs = models.TypingLog.objects.filter(user=request_user)
            start = _start_date(days)
            if start:
                qs = qs.filter(date__gte=start)
            total = qs.aggregate(s=Sum('count'))['s'] or 0
            if total:
                me = {'rank': None, 'total': total, 'of': len(rows),
                      'ranked': False}

    return {'key': key, 'phrase': phrase, 'top': top, 'me': me,
            'players': len(rows)}


@require_GET
def my_page(request):
    """일일 타건 기록. 로그인하지 않아도 열린다."""
    period = request.GET.get('rank', DEFAULT_PERIOD)
    board = _leaderboard(period, request.user)

    ctx = {
        'periods': [(k, PERIODS[k][0]) for k in ('month', 'year', 'all')],
        'board': board,
        'active_rank': board['key'],
    }

    if request.user.is_authenticated:
        today = timezone.localdate()
        logs = models.TypingLog.objects.filter(user=request.user)
        ctx['today_count'] = (logs.filter(date=today)
                              .values_list('count', flat=True).first() or 0)
        ctx['total_count'] = logs.aggregate(s=Sum('count'))['s'] or 0
        ctx['day_count'] = logs.count()
        ctx['last_date'] = logs.order_by('-date').values_list(
            'date', flat=True).first()
    return render(request, 'my_page.html', ctx)


@require_GET
def typing_json(request):
    """본인 타건 기록 시계열. 로그인한 사람만."""
    if not request.user.is_authenticated:
        return JsonResponse({'labels': [], 'data': []})

    days = int(request.GET.get('days', 30))
    days = max(7, min(days, 365))
    end = timezone.localdate()
    start = end - datetime.timedelta(days=days - 1)

    have = dict(models.TypingLog.objects
                .filter(user=request.user, date__gte=start, date__lte=end)
                .values_list('date', 'count'))

    labels, data = [], []
    d = start
    while d <= end:
        labels.append(d.strftime('%Y-%m-%d'))
        # 기록이 없는 날은 0 이다. 빼 버리면 쉰 날이 그래프에서 사라져
        # 매일 친 것처럼 보인다.
        data.append(have.get(d, 0))
        d += datetime.timedelta(days=1)

    return JsonResponse({'labels': labels, 'data': data,
                         'total': sum(data), 'days': days})


@require_GET
def api_token(request):
    """API 토큰 발급 화면. 비회원에게는 가입을 안내한다."""
    ctx = {}
    if request.user.is_authenticated:
        token, _created = models.ApiToken.objects.get_or_create(
            user=request.user)
        ctx['token'] = token.key
        ctx['created_at'] = token.created_at
    return render(request, 'user/api_token.html', ctx)


@login_required
@require_POST
def api_token_reissue(request):
    """토큰을 새로 발급한다. 예전 토큰은 그 즉시 못 쓰게 된다.

    키가 기본키라 값을 바꿔 저장하면 새 행이 하나 더 생긴다. 지우고 만든다.
    """
    models.ApiToken.objects.filter(user=request.user).delete()
    models.ApiToken.objects.create(user=request.user)
    return redirect('api_token')
