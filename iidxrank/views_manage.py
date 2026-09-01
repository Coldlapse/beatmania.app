# -*- coding: utf-8 -*-
"""관리자 대시보드 — management command 실행과 로그 조회.

Django admin 과 별개의 화면이다. admin 은 모델 CRUD 를 위한 것이고,
여기는 "서열표 갱신을 돌리고 로그를 본다"는 운영 작업을 위한 것이다.

접근 제어: 전부 is_staff 전용이다. 데코레이터를 지우지 마라 —
이 화면은 서버에서 명령을 실행한다.
"""
import json

from django.contrib.auth.decorators import user_passes_test
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from update import runner
from update.models import CommandRun


def _is_staff(user):
    return user.is_active and user.is_staff


# login_url 을 사이트 로그인으로 둔다. admin 로그인 화면으로 튕기지 않게.
staff_only = user_passes_test(_is_staff, login_url='/!/login/')


@staff_only
def dashboard(request):
    # 서버 재시작 등으로 스레드만 사라진 기록을 여기서 정리한다.
    # 안 하면 그 기록이 남아 이후 모든 실행을 막는다.
    runner.reap_stale()
    running = CommandRun.objects.filter(
        status__in=[CommandRun.PENDING, CommandRun.RUNNING]).first()
    return render(request, 'manage/dashboard.html', {
        'commands': runner.COMMANDS,
        'runs': CommandRun.objects.all()[:20],
        'running': running,
        'error': request.session.pop('manage_error', None),
    })


@staff_only
@require_POST
def run_command(request):
    name = request.POST.get('command', '')
    run, error = runner.start(name, request.POST, request.user)
    if error:
        request.session['manage_error'] = error
        return redirect('manage_dashboard')
    return redirect('manage_run', run_id=run.pk)


@staff_only
@require_POST
def abort_run(request, run_id):
    """멈춘 것으로 판단되는 실행의 잠금을 푼다.

    파이썬은 스레드를 안전하게 강제 종료할 수 없다. 기록만 실패로 표시한다.
    """
    ok = runner.abort(run_id)
    if not ok:
        request.session['manage_error'] = '이미 종료된 작업입니다.'
    return redirect('manage_dashboard')


@staff_only
@require_POST
def answer_prompt(request, run_id):
    """대기 중인 실행에 답을 넣는다.

    'multi' 질문은 체크박스 여러 개로 오므로 쉼표로 합친다. 명령 쪽이
    "1,3,7" / "all" / "" 형식을 그대로 이해한다(CLI 와 같은 형식).
    """
    if request.POST.get('all'):
        value = 'all'
    else:
        picked = request.POST.getlist('choice')
        value = ','.join(picked)
    runner.answer(run_id, value)
    return redirect('manage_run', run_id=run_id)


@staff_only
def run_detail(request, run_id):
    try:
        run = CommandRun.objects.get(pk=run_id)
    except CommandRun.DoesNotExist:
        raise Http404
    cmd = runner.COMMANDS_BY_NAME.get(run.command)
    return render(request, 'manage/run.html', {'run': run, 'cmd': cmd})


@staff_only
def run_log(request, run_id):
    """로그 폴링용. 이미 받은 만큼(offset)은 빼고 새 부분만 돌려준다."""
    try:
        run = CommandRun.objects.get(pk=run_id)
    except CommandRun.DoesNotExist:
        raise Http404
    try:
        offset = max(0, int(request.GET.get('offset', 0)))
    except (TypeError, ValueError):
        offset = 0
    log = run.log or ''
    return JsonResponse({
        'status': run.status,
        'status_display': run.get_status_display(),
        'done': run.is_done,
        'offset': len(log),
        'append': log[offset:],
        'duration': run.duration_seconds,
        # 대기 중이면 질문을 함께 보낸다. 화면이 폴링만으로 프롬프트를 띄운다.
        'prompt': run.prompt_data(),
    })
