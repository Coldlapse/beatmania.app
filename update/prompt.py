# -*- coding: utf-8 -*-
"""명령이 운영자에게 물어보는 지점을 CLI 와 웹 양쪽에서 쓸 수 있게 하는 계층.

배경 — `parser_infinitas.py` 는 서열표에서 위치가 바뀐 곡 목록을 보여주고
어느 것을 적용할지 `input()` 으로 물어본다. 터미널에서는 잘 동작하지만,
웹 대시보드에서 그대로 돌리면 실행 스레드가 stdin 에서 영영 멈춘다.

그래서 물어보는 행위를 `ask()` 하나로 추상화했다.

  - CLI 로 실행하면      -> 예전처럼 input() 을 쓴다. 동작이 전혀 바뀌지 않는다.
  - 대시보드로 실행하면  -> 질문을 DB(CommandRun.prompt)에 써 두고 상태를
                            '입력 대기'로 바꾼 뒤, 답이 채워질 때까지 폴링한다.

DB 를 경유하는 이유는 로그와 같다. mod_wsgi 는 워커 프로세스가 여러 개라
질문을 쓴 워커와 답을 받는 워커가 다를 수 있다. 메모리로는 전달되지 않는다.
"""
import json
import threading
import time

from django.utils import timezone

# 실행 스레드에만 붙는 컨텍스트. runner 가 채우고, 여기서 읽는다.
_ctx = threading.local()

# 아무도 답하지 않을 때 언제까지 기다릴지.
# 무한정 기다리면 실행 잠금이 영영 풀리지 않는다.
DEFAULT_TIMEOUT = 30 * 60      # 30분
POLL_INTERVAL = 1.0


def bind(run_pk, flush=None):
    """runner 가 실행 직전에 호출한다.

    flush: 로그 스트림을 비우는 콜백. 질문을 띄우기 전에 호출해서,
    질문의 근거가 된 출력이 버퍼에 갇힌 채 남지 않게 한다.
    """
    _ctx.run_pk = run_pk
    _ctx.flush = flush


def unbind():
    _ctx.run_pk = None
    _ctx.flush = None


def current_run_pk():
    return getattr(_ctx, 'run_pk', None)


def is_web():
    return current_run_pk() is not None


class PromptTimeout(Exception):
    pass


def ask(question, choices=None, kind='text', default='',
        help='', timeout=DEFAULT_TIMEOUT, cli_prompt=None):
    """운영자에게 묻고 답 문자열을 돌려준다.

    question : 질문 제목
    choices  : [{'value':..., 'label':..., 'detail':...}] — kind 가 'multi' 일 때 목록
    kind     : 'text'  자유 입력
               'multi' 목록에서 여러 개 선택 (값은 쉼표로 join 되어 돌아온다)
    default  : 시간이 초과되거나 그냥 넘길 때의 값
    cli_prompt: CLI 에서 input() 에 넘길 문구. 없으면 question 을 쓴다.
    """
    if not is_web():
        # 터미널에서 돌린 경우 — 기존 동작을 그대로 유지한다.
        try:
            return input(cli_prompt or (question + ' ')).strip()
        except EOFError:
            return default

    from update.models import CommandRun

    # 질문 직전에 로그를 화면으로 내보낸다. 무엇을 보고 묻는지가 보여야 한다.
    _flush = getattr(_ctx, 'flush', None)
    if _flush:
        try:
            _flush()
        except Exception:
            pass

    run_pk = current_run_pk()
    payload = {
        'question': question,
        'kind': kind,
        'choices': choices or [],
        'default': default,
        'help': help,
    }
    CommandRun.objects.filter(pk=run_pk).update(
        prompt=json.dumps(payload, ensure_ascii=False),
        prompt_answer='',
        prompt_asked_at=timezone.now(),
        status=CommandRun.WAITING)

    waited = 0.0
    while waited < timeout:
        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL
        row = CommandRun.objects.filter(pk=run_pk).values(
            'prompt_answer', 'status').first()
        if row is None:                       # 기록이 지워졌다
            break
        if row['status'] == CommandRun.FAILED:  # 강제 해제됨
            break
        if row['prompt_answer']:
            answer = row['prompt_answer']
            # __SKIP__ 은 "그냥 넘기기"(CLI 의 빈 Enter)에 해당한다
            if answer == '__SKIP__':
                answer = default
            CommandRun.objects.filter(pk=run_pk).update(
                prompt='', prompt_answer='', prompt_asked_at=None,
                status=CommandRun.RUNNING)
            return answer

    # 시간 초과 — 기본값으로 계속 간다. 멈춰 있는 것보다 낫다.
    CommandRun.objects.filter(pk=run_pk).update(
        prompt='', prompt_answer='', prompt_asked_at=None,
        status=CommandRun.RUNNING)
    return default
