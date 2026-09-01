# -*- coding: utf-8 -*-
"""관리자 대시보드에서 management command 를 실행하는 계층.

설계 원칙 — 이 파일은 웹에서 서버 명령을 실행한다. 사실상 원격 코드 실행이므로
다음을 코드 구조로 못 박는다. 편의를 이유로 완화하지 마라.

1. **셸을 쓰지 않는다.** subprocess 가 아니라 `call_command` 로 인프로세스 실행한다.
   문자열을 조립해 셸에 넘기는 경로 자체를 만들지 않는다.
2. **화이트리스트만 실행된다.** 아래 COMMANDS 에 선언된 이름만 허용한다.
   사용자가 보낸 문자열은 명령 이름으로 쓰이지 않고, 키 조회에만 쓰인다.
3. **인수도 화이트리스트다.** 각 명령이 받을 옵션과 타입을 여기서 선언하고,
   선언에 없는 옵션은 조용히 버린다. 임의 문자열이 인수로 흘러들지 않는다.
4. **날것의 `input()` 을 부르는 명령은 등록하지 않는다.** 웹에서 돌리면 워커가
   stdin 에서 영영 멈춘다. 물어봐야 하는 명령은 `update/prompt.py` 의 `ask()` 를
   쓰도록 고친 뒤에 등록한다 — 그러면 CLI 와 웹 양쪽에서 동작한다.
5. **동시 실행을 막는다.** 같은 DB 를 긁어 쓰는 작업이라 겹치면 데이터가 깨진다.
"""
import datetime
import io
import sys
import threading
import traceback

from django.core.management import call_command
from django.db import close_old_connections
from django.utils import timezone

from update import prompt as _prompt


class Opt(object):
    """명령이 받을 옵션 하나의 선언."""

    def __init__(self, name, kind, label, help='', default=None, choices=None):
        self.name = name          # call_command 에 넘길 키워드
        self.kind = kind          # 'flag' | 'int' | 'choice'
        self.label = label
        self.help = help
        self.default = default
        self.choices = choices or []


class Cmd(object):
    def __init__(self, name, label, description, options=None,
                 danger=False, duration='보통', requires=''):
        self.name = name
        self.label = label
        self.description = description
        self.options = options or []
        self.danger = danger          # 되돌리기 어려운 작업인가
        self.duration = duration
        self.requires = requires      # 외부 의존성 안내


# --- 실행을 허용하는 명령 -----------------------------------------------------
# py_compile 이 실패하는 명령(dumpCalc, fixSongDB, updateCalc, updateUser)은
# Python 2 문법이라 애초에 import 되지 않는다. 등록하지 않는다.
COMMANDS = [
    Cmd(
        'updateSongInfinitas',
        'INFINITAS 수록곡 + 서열표 갱신',
        'textage.cc 에서 수록곡을 가져오고, 구글 시트의 서열표를 읽어 곡을 '
        '카테고리에 매핑한다. 평소 쓰던 갱신 작업이다. 서열표 안에서 위치가 '
        '바뀐 곡이 있으면 실행을 멈추고 어느 것을 적용할지 물어본다.',
        options=[
            Opt('mode', 'choice', '모드', choices=[
                ('update', '변동분만 갱신 (권장)'),
                ('reset', '서열표를 비우고 처음부터 매핑'),
            ], default='update'),
            Opt('test', 'flag', '테스트 실행',
                help='DB 에 쓰지 않고 동작만 확인한다. 서열표 매핑은 건너뛴다.'),
            Opt('set_version', 'int', '버전 지정',
                help='비워두면 전체를 대상으로 한다.'),
        ],
        duration='수 분 (중간에 확인을 요청할 수 있음)',
        requires='playwright (브라우저 바이너리 필요), textage.cc · Google Sheets 접근',
    ),
    Cmd(
        'compareRankTables',
        'SP12TEST ↔ SP12H 대조',
        '두 서열표의 분류 결과를 비교해 차이를 보고한다. DB 를 바꾸지 않는다.',
        duration='짧음',
    ),
    Cmd(
        'cleanDuplicateSongs',
        '중복 곡 정리',
        '유사도 분석으로 중복 등록된 곡을 찾아 그룹별로 보여준다. '
        '어느 것을 지울지 그룹마다 물어본다.',
        danger=True,
        duration='짧음 (그룹마다 확인 필요)',
    ),
    Cmd(
        'copyRankTable',
        'SP12H → SP12TEST 복사',
        'SP12H 의 카테고리와 곡 배치를 SP12TEST 로 통째로 복사한다.',
        danger=True,
        duration='짧음',
    ),
]

COMMANDS_BY_NAME = {c.name: c for c in COMMANDS}


class _DBLogStream(io.TextIOBase):
    """명령의 출력을 받아 DB 에 옮기는 스트림.

    **DB 쓰기를 명령의 실행 스택에서 떼어냈다.** 예전에는 write() 안에서 바로
    UPDATE 를 쳤는데, 그 write() 는 파서가 DB 를 순회하는 도중에 print() 로
    불린다. 같은 커넥션에 중첩해서 쓰다가 SQLite 에서 교착이 났다
    (`updateSongInfinitas` 가 시트 매핑 단계에서 영영 멈췄다).

    지금은 write() 가 메모리 버퍼에만 쌓고, 별도의 writer 스레드가 주기적으로
    자기 커넥션으로 옮긴다. 명령 쪽 DB 작업과 로그 쓰기가 서로 얽히지 않는다.
    """

    INTERVAL = 1.0           # writer 스레드가 옮기는 주기(초)
    MAX_LOG = 400_000        # 폭주하는 로그로 DB 를 채우지 않는다

    def __init__(self, run):
        self.run_pk = run.pk
        self._buf = []
        self._lock = threading.Lock()
        self._total = len(run.log or '')
        self._truncated = False
        self._stop = threading.Event()
        self._thread = None

    # --- 스트림 인터페이스 ------------------------------------------------
    def writable(self):
        return True

    def write(self, s):
        if not s:
            return 0
        with self._lock:
            if self._total < self.MAX_LOG:
                self._buf.append(s)
                self._total += len(s)
            elif not self._truncated:
                self._truncated = True
                self._buf.append(
                    '\n... 로그가 너무 길어 이후 출력은 생략합니다 ...\n')
        return len(s)

    def flush(self):
        """버퍼를 즉시 DB 로 옮긴다. 프롬프트 직전 등에 명시적으로 부른다."""
        self._drain()

    # --- writer 스레드 ----------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name='logwriter-%d' % self.run_pk)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=10)
        self._drain()

    def _loop(self):
        while not self._stop.wait(self.INTERVAL):
            self._drain()

    def _drain(self):
        with self._lock:
            if not self._buf:
                return
            chunk = ''.join(self._buf)
            self._buf = []
        from django.db.models import F, TextField, Value
        from django.db.models.functions import Concat

        from update.models import CommandRun
        try:
            # 파이썬에서 읽어와 이어붙이지 않고 DB 안에서 붙인다.
            # read-modify-write 사이에 다른 쓰기가 끼어들면 로그가 유실된다.
            CommandRun.objects.filter(pk=self.run_pk).update(
                log=Concat(F('log'), Value(chunk), output_field=TextField()))
        except Exception:
            # 로그를 못 남기는 것이 명령 자체를 죽이면 안 된다.
            # 다음 주기에 다시 시도할 수 있게 버퍼 앞에 되돌린다.
            with self._lock:
                self._buf.insert(0, chunk)


class _ThreadRoutedIO(object):
    """명령을 돌리는 스레드의 출력만 가로채는 sys.stdout/stderr 대역.

    `contextlib.redirect_stdout` 은 sys.stdout 을 **프로세스 전역으로** 바꾼다.
    명령이 도는 동안 다른 스레드가 print() 한 것까지 명령 로그에 섞인다.
    스레드 단위로 갈라서, 등록된 스레드의 출력만 로그로 보내고 나머지는
    원래 stdout 으로 그대로 흘린다.
    """

    def __init__(self, original):
        self._original = original
        self._targets = {}

    def bind(self, stream):
        self._targets[threading.get_ident()] = stream

    def unbind(self):
        self._targets.pop(threading.get_ident(), None)

    def _target(self):
        return self._targets.get(threading.get_ident(), self._original)

    def write(self, s):
        t = self._target()
        return t.write(s) if t is not None else len(s)

    def flush(self):
        t = self._target()
        if t is not None:
            t.flush()

    def writable(self):
        return True

    def isatty(self):
        return False

    @property
    def encoding(self):
        return getattr(self._original, 'encoding', 'utf-8')


# 프로세스당 한 번만 갈아 끼운다. 원래 stdout 은 안에 그대로 들고 있다.
_stdout_router = None
_stderr_router = None
_router_lock = threading.Lock()


def _install_routers():
    global _stdout_router, _stderr_router
    with _router_lock:
        if _stdout_router is None:
            _stdout_router = _ThreadRoutedIO(sys.stdout)
            _stderr_router = _ThreadRoutedIO(sys.stderr)
            sys.stdout = _stdout_router
            sys.stderr = _stderr_router
    return _stdout_router, _stderr_router


def build_kwargs(cmd, raw):
    """폼에서 온 값을 call_command 키워드로 바꾼다.

    선언에 없는 키는 버린다. 값도 선언된 타입으로만 변환한다.
    """
    kwargs = {}
    labels = []
    for opt in cmd.options:
        v = raw.get(opt.name)
        if opt.kind == 'flag':
            if v in ('1', 'on', 'true', 'True'):
                # 이 프로젝트의 --test 는 store_true 가 아니라 int 를 받는다
                kwargs[opt.name] = 1
                labels.append('--%s' % opt.name)
        elif opt.kind == 'int':
            if v not in (None, ''):
                try:
                    kwargs[opt.name] = int(v)
                    labels.append('--%s=%d' % (opt.name, int(v)))
                except (TypeError, ValueError):
                    pass
        elif opt.kind == 'choice':
            allowed = [c[0] for c in opt.choices]
            if v in allowed:
                # mode 는 --reset / --update 라는 별개 플래그로 나간다
                if opt.name == 'mode':
                    kwargs[v] = True
                    labels.append('--%s' % v)
                else:
                    kwargs[opt.name] = v
                    labels.append('--%s=%s' % (opt.name, v))
    return kwargs, ' '.join(labels)


def _run(run_pk, command_name, kwargs):
    from update.models import CommandRun
    close_old_connections()          # 스레드는 자기 커넥션을 쓴다
    run = CommandRun.objects.get(pk=run_pk)
    stream = _DBLogStream(run)
    stream.start()
    status = CommandRun.SUCCESS
    try:
        CommandRun.objects.filter(pk=run_pk).update(status=CommandRun.RUNNING)
        stream.write('$ python manage.py %s %s\n\n' % (command_name, run.options))
        # 이 스레드에서 부르는 prompt.ask() 가 CLI 대신 웹 경로를 타게 한다
        _prompt.bind(run_pk, flush=stream.flush)
        # call_command(stdout=...) 는 명령의 self.stdout.write 만 잡는다.
        # 이 프로젝트의 파서들은 대부분 맨 print() 를 쓰기 때문에, 그대로 두면
        # 진행 상황이 서버 콘솔로 새고 대시보드 로그는 텅 빈 채로 남는다.
        # sys.stdout/stderr 도 같은 스트림으로 돌린다 — 단, 이 스레드에 한해서.
        out, err = _install_routers()
        out.bind(stream)
        err.bind(stream)
        try:
            call_command(command_name, stdout=stream, stderr=stream, **kwargs)
        finally:
            out.unbind()
            err.unbind()
    except Exception:
        status = CommandRun.FAILED
        stream.write('\n\n=== 예외 발생 ===\n')
        stream.write(traceback.format_exc())
    finally:
        _prompt.unbind()
        stream.stop()
        CommandRun.objects.filter(pk=run_pk).update(
            status=status, finished_at=timezone.now(),
            prompt='', prompt_answer='', prompt_asked_at=None)
        close_old_connections()


# 이 시간이 지나도 안 끝난 실행은 죽은 것으로 본다.
# 실행 스레드는 워커 프로세스에 매여 있어서, mod_wsgi 가 워커를 재활용하거나
# 배포로 재시작하면 스레드만 사라지고 DB 의 상태는 '실행 중'으로 남는다.
# 그대로 두면 이후 모든 실행이 영구히 막힌다.
STALE_AFTER = datetime.timedelta(hours=2)


def reap_stale():
    """죽은 실행 기록을 정리한다. 정리한 건수를 돌려준다."""
    from update.models import CommandRun
    cutoff = timezone.now() - STALE_AFTER
    stale = CommandRun.objects.filter(
        status__in=[CommandRun.PENDING, CommandRun.RUNNING, CommandRun.WAITING],
        started_at__lt=cutoff)
    n = stale.count()
    if n:
        for run in stale:
            run.status = CommandRun.FAILED
            run.finished_at = timezone.now()
            run.log = (run.log or '') + (
                '\n\n=== 중단됨 ===\n'
                '%s 이상 응답이 없어 죽은 작업으로 정리했습니다.\n'
                '서버가 재시작되었거나 워커가 재활용된 경우입니다.\n'
                % _humanize(STALE_AFTER))
            run.save(update_fields=['status', 'finished_at', 'log'])
    return n


def abort(run_pk):
    """실행 기록을 강제로 실패 처리한다.

    스레드를 죽이지는 못한다(파이썬은 스레드를 안전하게 강제 종료할 수 없다).
    '이미 죽은 걸 아는데 잠금이 안 풀린다'는 상황을 푸는 용도다.
    """
    from update.models import CommandRun
    run = CommandRun.objects.filter(
        pk=run_pk,
        status__in=[CommandRun.PENDING, CommandRun.RUNNING,
                    CommandRun.WAITING]).first()
    if run is None:
        return False
    run.status = CommandRun.FAILED
    run.finished_at = timezone.now()
    run.log = (run.log or '') + (
        '\n\n=== 사용자가 강제 종료했습니다 ===\n'
        '기록만 해제했을 뿐, 실제 프로세스가 살아 있다면 계속 돌 수 있습니다.\n')
    run.save(update_fields=['status', 'finished_at', 'log'])
    return True


def _humanize(delta):
    h = int(delta.total_seconds() // 3600)
    return '%d시간' % h if h else '%d분' % int(delta.total_seconds() // 60)


def start(command_name, raw_options, user):
    """명령을 백그라운드에서 시작하고 CommandRun 을 돌려준다.

    반환: (run, error_message). error_message 가 있으면 실행되지 않은 것이다.
    """
    from update.models import CommandRun

    cmd = COMMANDS_BY_NAME.get(command_name)
    if cmd is None:
        return None, '허용되지 않은 명령입니다.'

    reap_stale()

    # 겹쳐 돌면 같은 테이블을 동시에 갈아엎는다
    if CommandRun.objects.filter(
            status__in=[CommandRun.PENDING, CommandRun.RUNNING,
                        CommandRun.WAITING]).exists():
        return None, '이미 실행 중인 작업이 있습니다. 끝난 뒤에 다시 시도하세요.'

    kwargs, label = build_kwargs(cmd, raw_options)
    run = CommandRun.objects.create(
        command=cmd.name, options=label,
        started_by=user if user and user.is_authenticated else None,
        status=CommandRun.PENDING)

    t = threading.Thread(target=_run, args=(run.pk, cmd.name, kwargs),
                         name='cmdrun-%d' % run.pk)
    t.daemon = True
    t.start()
    return run, None


def answer(run_pk, value):
    """대기 중인 실행에 답을 넣는다. 실행 스레드가 폴링으로 집어간다."""
    from update.models import CommandRun
    run = CommandRun.objects.filter(pk=run_pk, status=CommandRun.WAITING).first()
    if run is None:
        return False
    # 빈 답은 '그냥 넘기기'다. 빈 문자열로 두면 폴링이 답으로 인식하지 못한다.
    CommandRun.objects.filter(pk=run_pk).update(
        prompt_answer=value if value else '__SKIP__')
    return True
