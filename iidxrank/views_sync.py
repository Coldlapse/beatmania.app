# -*- coding: utf-8 -*-
"""게임 기록 동기화 — 웹 업로드와 상주 앱 API.

둘 다 tracker.tsv 본문을 iidxrank/records_import.apply 에 넘긴다. 차이는
누구인지 아는 방법(로그인 세션 / API 토큰)과 응답 모양(화면 / JSON)뿐이다.
"""
import datetime

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from iidxrank import models, records_import

# 같은 사용자가 이보다 잦게 보내면 거절한다. 상주 앱은 1분에 한 번까지만
# 보내도록 만들지만, 앱이 고장 나 연달아 보내도 서버가 곡 DB 를 매번 다시
# 읽지 않게 한다.
MIN_INTERVAL = datetime.timedelta(seconds=10)


def _decode(raw):
    if len(raw) > records_import.MAX_BYTES:
        raise records_import.TsvError(_('파일이 너무 큽니다.'))
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise records_import.TsvError(_('UTF-8 로 읽을 수 없는 파일입니다.'))


def _too_soon(user):
    last = (models.RecordSync.objects.filter(user=user)
            .values_list('created_at', flat=True).first())
    return last is not None and timezone.now() - last < MIN_INTERVAL


@require_http_methods(['GET', 'POST'])
def data_sync(request):
    """데이터 동기화 화면. 로그인했으면 tracker.tsv 를 직접 올릴 수 있다."""
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        # 결과는 세션에 담아 GET 으로 넘긴다(새로고침으로 다시 올라가지 않게).
        # 이 사이트는 messages 를 화면에 그리지 않아 같은 자리에 오류도 담는다.
        f = request.FILES.get('tracker')
        if f is None:
            r = {'error': _('파일을 골라 주세요.')}
        elif _too_soon(request.user):
            r = {'error': _('잠시 뒤에 다시 올려 주세요.')}
        else:
            try:
                r = records_import.apply(request.user, _decode(f.read()),
                                         models.RecordSync.WEB)
            except records_import.TsvError as e:
                r = {'error': str(e)}
        request.session['sync_result'] = r
        return redirect('data_sync')

    ctx = {'result': request.session.pop('sync_result', None)}
    if request.user.is_authenticated:
        ctx['history'] = models.RecordSync.objects.filter(user=request.user)[:5]
    return render(request, 'sync.html', ctx)


@csrf_exempt
def records_api(request):
    """상주 앱이 tracker.tsv 를 통째로 보낸다.

    POST /api/v1/records
      Authorization: Token <키>
      Content-Type: text/tab-separated-values; charset=utf-8
      본문: tracker.tsv 그대로

    성공 200: records_import.apply 의 요약. 같은 파일을 다시 보내도 결과가 같다.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method is required.'}, status=405)

    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Token '):
        return JsonResponse(
            {'error': 'Authorization header is missing or invalid.'}, status=401)
    try:
        token = (models.ApiToken.objects.select_related('user')
                 .get(key=auth.split(' ', 1)[1].strip()))
    except models.ApiToken.DoesNotExist:
        return JsonResponse({'error': 'Invalid token.'}, status=401)
    user = token.user
    if not user.is_active:
        return JsonResponse({'error': 'Inactive user.'}, status=403)

    if _too_soon(user):
        resp = JsonResponse({'error': 'Too many requests.'}, status=429)
        resp['Retry-After'] = str(int(MIN_INTERVAL.total_seconds()))
        return resp

    try:
        result = records_import.apply(user, _decode(request.body),
                                      models.RecordSync.APP)
    except records_import.TsvError as e:
        return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse(result)
