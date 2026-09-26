# -*- coding: utf-8 -*-
"""계정 인증 - 이메일 인증 코드 발송·확인과 그에 딸린 규칙.

뷰에서 쓰는 함수는 넷이다.

    send_code(request, email, purpose)   코드를 만들어 메일로 보낸다
    check_code(request, email, purpose, code)  코드를 대조하고 세션에 기록한다
    verified_email(request, purpose)     지금 세션에서 인증이 끝난 주소
    clear_verification(request, purpose) 인증 기록을 지운다

세션에도 결과를 남기는 이유: 가입 폼이 비밀번호 오류 등으로 다시 그려져도
이메일 인증이 풀리면 안 된다.

횟수 제한(2026-09-26, iidxrank/throttle.py): 발송은 IP·주소·사이트 전체 한도, 재발송 간격은
브라우저(세션)마다, 코드 오입력은 (주소, 목적)마다 하루 한도. 가입 여부에 따라 응답이 달라지지
않게 하는 것이 이 파일 규칙의 절반이다 — 달라지면 그 차이로 가입자 목록을 캐낼 수 있다.
"""

import logging
import re
import secrets
import threading

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db import connections
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext as _

from iidxrank import client_ip, models, throttle

log = logging.getLogger(__name__)

# 세션에 인증 결과를 담는 자리. 목적별로 따로 둔다 - 가입 인증이 이메일 변경
# 인증으로 재활용되면 안 된다.
SESSION_KEY = 'email_verified'

# 화면에서 쓰는 것과 같은 검사. Django 의 EmailValidator 보다 좁게 잡는다 -
# 여기서 통과한 주소로 실제로 메일을 보내야 하므로, 애매한 것은 거른다.
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]{2,}$')


def is_email_shaped(value):
    return isinstance(value, str) and bool(EMAIL_RE.match(value.strip()))


def normalize(email):
    """대소문자와 앞뒤 공백만 정리한다.

    Gmail 의 점(.)이나 +태그까지 정규화하지는 않는다. 그렇게 하면
    a.b@gmail.com 과 ab@gmail.com 을 같은 주소로 보게 되는데, 그것을 다르게
    쓰고 있는 기존 사용자가 있으면 중복으로 걸려 버린다.
    """
    # JSON 으로 숫자·목록이 와도 500 이 나지 않게 문자열만 받는다
    return email.strip().lower() if isinstance(email, str) else ''


# ---------------------------------------------------------------------------
# 이메일 중복
# ---------------------------------------------------------------------------
def email_taken(email, exclude_user=None):
    """이 주소를 이미 쓰고 있는 계정이 있나.

    비교 대상은 newrulepassed=1 인 계정뿐이 아니다. 새로 정하는 주소는
    누구의 것과도 겹치면 안 된다. 기존 중복(2026-09 기준 15종 30명)은
    그대로 두되, 그 사람들이 마이그레이션할 때 먼저 온 사람이 가져간다.
    """
    qs = User.objects.filter(email__iexact=normalize(email))
    if exclude_user is not None:
        qs = qs.exclude(pk=exclude_user.pk)
    return qs.exists()


def recoverable_user(email):
    """아이디/비밀번호 찾기의 대상 계정. 없으면 None.

    원칙은 newrulepassed=1 인 계정만이다. 그 계정만 이메일이 유일하다고
    보장되기 때문이다.

    다만 그 원칙만 따르면, 아직 마이그레이션하지 않은 기존 사용자가 비밀번호를
    잊었을 때 로그인도 찾기도 못 해 영구히 잠긴다. 그래서 아직 0 이더라도
    **그 주소를 쓰는 계정이 하나뿐이고 주소 형식이 맞으면** 찾기를 허용한다.
    중복(30명)이거나 형식이 깨진(5명) 경우에만 막힌다 - 그때는 어느 계정인지
    고를 수 없으니 사람이 판단해야 한다.
    """
    email = normalize(email)
    if not is_email_shaped(email):
        return None
    users = list(User.objects.filter(email__iexact=email, is_active=True))
    if not users:
        return None
    passed = [u for u in users
              if models.AccountSecurity.objects
              .filter(user=u, newrulepassed=True).exists()]
    if len(passed) == 1:
        return passed[0]
    if passed:
        # 규칙을 지난 계정이 둘 이상이면 유일성이 깨진 것이다. 있어서는 안 되는
        # 상태이므로 조용히 아무거나 고르지 않는다.
        return None
    # 아직 마이그레이션 전. 그 주소를 쓰는 계정이 하나뿐일 때만 허용한다.
    return users[0] if len(users) == 1 else None


# ---------------------------------------------------------------------------
# 코드 발송 / 확인
# ---------------------------------------------------------------------------
def _new_code():
    # 6자리 숫자. 사람이 메일에서 옮겨 적는 값이라 대소문자나 헷갈리는 글자가
    # 없는 편이 낫다.
    return '%06d' % secrets.randbelow(1000000)


def _subject(purpose):
    """메일 제목.

    딕셔너리를 모듈 최상위에 두고 gettext 로 만들면 **import 시점에 한 번**
    평가돼 그때의 언어로 굳는다. 실제로 그랬다 - 본문은 사용자의 언어를
    따르는데 제목만 한국어로 나갔다. 부를 때마다 평가되도록 함수로 감싼다.
    """
    return {
        models.EmailVerification.SIGNUP: _('[beatmania.app] 가입 인증 코드'),
        models.EmailVerification.CHANGE: _('[beatmania.app] 이메일 변경 인증 코드'),
        models.EmailVerification.FIND_ID: _('[beatmania.app] 아이디 찾기 인증 코드'),
        models.EmailVerification.RESET_PW: _('[beatmania.app] 비밀번호 재설정 인증 코드'),
        models.EmailVerification.MIGRATE: _('[beatmania.app] 계정 인증 코드'),
    }[purpose]


def _heading(purpose):
    """메일 본문 맨 위의 한 줄. 무엇 때문에 온 메일인지 바로 알리는 자리다."""
    return {
        models.EmailVerification.SIGNUP: _('회원가입을 마무리해 주세요'),
        models.EmailVerification.CHANGE: _('새 이메일 주소를 확인해 주세요'),
        models.EmailVerification.FIND_ID: _('아이디를 확인하시려면'),
        models.EmailVerification.RESET_PW: _('비밀번호를 재설정하시려면'),
        models.EmailVerification.MIGRATE: _('계정 인증을 진행해 주세요'),
    }[purpose]


def _cooldown_parts(request, email, purpose):
    return (normalize(email), purpose, request.session.session_key or '')


def seconds_until_resend(request, email, purpose):
    """이 브라우저가 이 주소·목적으로 다시 보낼 수 있을 때까지 남은 초. 0 이면 지금 보낼 수 있다.

    예전에는 (주소, 목적)의 마지막 발송으로 쟀다. 그러면 남이 내 주소로 5분마다 요청하는 것만으로
    나는 영영 새 코드를 받을 수 없었다. 이제 브라우저(세션)마다 잰다. 쿠키를 지워 이 간격을
    건너뛰는 것은 주소당·IP당 발송 한도(throttle)가 막는다.

    가입 여부와 상관없이 같은 규칙이다 — 가입된 주소에만 간격이 생기면 그 차이로 가입 여부가 샌다.
    """
    return throttle.seconds_left('mail_cool', *_cooldown_parts(request, email, purpose))


def send_limit_message(request, email):
    """발송 한도에 걸렸으면 안내 문구, 아니면 None. 가입 여부와 상관없이 같은 순서로 본다."""
    ip = client_ip.get(request)
    if (throttle.over(throttle.MAIL_DAY[0], 'mail_day')
            or (ip and throttle.over(throttle.MAIL_IP[0], 'mail_ip', ip))
            or throttle.over(throttle.MAIL_ADDR[0], 'mail_addr', normalize(email))):
        return _('지금은 인증 메일을 보낼 수 없습니다. 잠시 뒤에 다시 시도해 주세요.')
    return None


def note_send_request(request, email, purpose):
    """발송 요청 하나를 센다(실제로 메일이 나갔는지와 상관없이). 재발송 간격도 여기서 시작한다."""
    if not request.session.session_key:
        request.session.save()
    ip = client_ip.get(request)
    if ip:
        throttle.hit('mail_ip', throttle.MAIL_IP[1], ip)
    throttle.hit('mail_addr', throttle.MAIL_ADDR[1], normalize(email))
    throttle.hit('mail_cool', settings.EMAIL_RESEND_INTERVAL, *_cooldown_parts(request, email, purpose))


# ── 백그라운드 발송 ───────────────────────────────────────────────────────
#
# 로그인하지 않은 목적(가입·아이디 찾기·비밀번호 재설정)은 메일을 응답 뒤에 보낸다(2026-09-26).
# 같은 자리에서 보내면 SMTP 가 응답을 붙잡아, 메일을 보내는 경우(가입된 주소)와 보내지 않는
# 경우(가입 안 된 주소)가 응답 시간으로 갈렸다 — 라이브 실측 4,366ms 대 210ms. 문구를 같게 해도
# 시간만 재면 가입 여부를 알 수 있었다.
# 대가: 발송이 실패해도 화면은 "보냈습니다" 다. 실패하면 코드를 지우고 로그만 남기며, 사용자는
# 재발송 간격(5분) 뒤 다시 요청한다(안내 문구가 그렇게 말한다).
# 로그인한 목적(이메일 변경·1회 인증)은 가입 여부를 숨길 일이 없어 전처럼 그 자리에서 보내고
# 실패를 알린다.
_pending = []


def _later(job):
    """job 을 응답 뒤에 돌린다. EMAIL_SEND_ASYNC=False 면 그 자리에서(검사용)."""
    if not getattr(settings, 'EMAIL_SEND_ASYNC', True):
        job()
        return

    def run():
        try:
            job()
        finally:
            # 스레드가 연 DB 연결(코드 행 삭제, 발송량 카운터)을 닫는다 — 안 닫으면 쌓인다
            connections.close_all()
    t = threading.Thread(target=run, name='bm-mail', daemon=True)
    t.start()
    _pending[:] = [x for x in _pending if x.is_alive()] + [t]


def wait_for_mail(timeout=10):
    """백그라운드 발송이 끝나기를 기다린다(검사용)."""
    for t in list(_pending):
        t.join(timeout)


def _deliver(email, subject, text_body, html_body):
    """실제 발송. 사이트 전체 하루 발송량을 여기서 센다."""
    msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [email])
    msg.attach_alternative(html_body, 'text/html')
    msg.send(fail_silently=False)
    throttle.hit('mail_day', throttle.MAIL_DAY[1])


def send_code(request, email, purpose, success_message=None, background=False):
    """코드를 만들어 보낸다. (성공여부, 메시지) 를 돌려준다.

    형식 검사·발송 한도·재발송 간격은 부르는 쪽(views_account.verify_send)이 먼저 본다.
    background=True 면 응답 뒤에 보내고 늘 성공으로 답한다(위 '백그라운드 발송' 참조).
    """
    email = normalize(email)
    if not request.session.session_key:
        request.session.save()

    now = timezone.now()
    row = models.EmailVerification.objects.create(
        email=email, purpose=purpose, code=_new_code(),
        last_sent_at=now, session_key=request.session.session_key or '')

    minutes = settings.EMAIL_CODE_TTL // 60
    subject = str(_subject(purpose))

    # 평문과 HTML 을 함께 보낸다. HTML 을 못 읽거나 꺼 둔 클라이언트가 있고,
    # 평문만 보내면 스팸 점수가 올라가는 경향도 있다.
    text_body = _(
        '아래 인증 코드를 입력해 주세요.\n\n'
        '    %(code)s\n\n'
        '유효 시간은 %(min)d분입니다.\n\n'
        '이 메일은 beatmania.app 의 계정 인증 때문에 발송되었습니다.\n'
        '본인이 요청한 것이 아니라면 이 메일을 무시하셔도 됩니다.\n'
        '저희는 계정 인증과 아이디·비밀번호 찾기 외의 목적으로는\n'
        '메일을 보내지 않습니다.\n'
    ) % {'code': row.code, 'min': minutes}

    html_body = render_to_string('mail/verify_code.html', {
        'subject': subject,
        'heading': _heading(purpose),
        'code': row.code,
        'min': minutes,
        'lang': get_language() or 'ko',
    })

    if background:
        pk = row.pk

        def job():
            try:
                _deliver(email, subject, text_body, html_body)
            except Exception as e:
                # 코드를 지워 이 코드로는 인증되지 않게 한다. 재발송 간격은 그대로 둔다
                # (응답은 이미 "보냈습니다" 로 나갔고, 문구가 5분 뒤 다시 요청하라고 안내한다)
                log.warning('verification mail failed (background): %s', type(e).__name__)
                models.EmailVerification.objects.filter(pk=pk).delete()
        _later(job)
        return True, (success_message or _('인증 코드를 보냈습니다. 메일함을 확인해 주세요.'))

    try:
        _deliver(email, subject, text_body, html_body)
    except Exception as e:
        # 전에는 여기서 500 이 났고, 메일은 안 갔는데 재발송 간격만 소모됐다.
        # 코드를 지우고 간격도 풀어 바로 다시 요청할 수 있게 한다.
        log.warning('verification mail failed: %s', type(e).__name__)
        row.delete()
        throttle.reset('mail_cool', *_cooldown_parts(request, email, purpose))
        return False, _('메일을 보내지 못했습니다. 잠시 뒤에 다시 시도해 주세요.')
    return True, (success_message or _('인증 코드를 보냈습니다. 메일함을 확인해 주세요.'))


def send_already_registered(request, email):
    """가입하려는 주소가 이미 쓰이고 있을 때 — 화면 대신 그 주소의 메일함으로 알린다.

    화면에 "이미 쓰는 이메일" 이라고 보여 주면 누구나 주소를 넣어 가입 여부를 알아낼 수 있었다.
    메일함의 주인만 이 사실을 알게 한다. 링크는 넣지 않는다(인증 메일과 같은 원칙 — verify_code.html).
    실패해도 화면 응답은 같게 둔다(여기서 달라지면 그것이 곧 신호다).
    """
    subject = str(_('[beatmania.app] 이미 가입된 이메일 주소입니다'))
    lines = [
        _('이 이메일 주소로 가입된 beatmania.app 계정이 이미 있습니다.'),
        _('아이디가 기억나지 않으면 로그인 화면의 "아이디 찾기" 를, 비밀번호가 기억나지 않으면 "비밀번호 재설정" 을 이용해 주세요.'),
    ]
    text_body = '\n\n'.join(str(x) for x in lines) + '\n\n' + str(_(
        '이 메일은 beatmania.app 의 계정 인증 때문에 발송되었습니다.\n'
        '본인이 요청한 것이 아니라면 이 메일을 무시하셔도 됩니다.\n'))
    html_body = render_to_string('mail/verify_code.html', {
        'subject': subject,
        'heading': _('이미 가입된 이메일 주소입니다'),
        'code': None,
        'lines': lines,
        'lang': get_language() or 'ko',
    })
    def job():
        try:
            _deliver(normalize(email), subject, text_body, html_body)
        except Exception as e:
            log.warning('already-registered mail failed: %s', type(e).__name__)
    # 가입 인증과 같은 시간에 답하도록 이것도 응답 뒤에 보낸다
    _later(job)


def _mask(email):
    """알림 메일에 새 주소를 보여 줄 때 가린다: ab***@gmail.com"""
    local, _at, domain = (email or '').partition('@')
    return '%s***@%s' % (local[:2], domain) if domain else '***'


def send_email_changed_notice(user, old_email, new_email):
    """이메일이 바뀌었다고 **이전 주소**로 알린다(1순위-3, 2026-09-26).

    세션을 빼앗은 사람이 이메일을 자기 것으로 바꾸면 그 뒤 비밀번호 재설정까지 가져갈 수 있다.
    이전 주소의 주인이 그 사실을 알게 한다. 새 주소는 가려서 보여 준다. 링크는 넣지 않는다.
    """
    old_email = normalize(old_email)
    if not is_email_shaped(old_email) or old_email == normalize(new_email):
        return
    subject = str(_('[beatmania.app] 이메일 주소가 변경되었습니다'))
    lines = [
        _('계정 %(id)s 의 이메일 주소가 %(new)s 로 변경되었습니다.') % {
            'id': user.get_username(), 'new': _mask(normalize(new_email))},
        _('본인이 변경한 것이 아니라면 사이트 디스코드로 운영자에게 바로 알려 주세요.'),
    ]
    text_body = '\n\n'.join(str(x) for x in lines) + '\n'
    html_body = render_to_string('mail/verify_code.html', {
        'subject': subject, 'heading': _('이메일 주소가 변경되었습니다'),
        'code': None, 'lines': lines, 'lang': get_language() or 'ko'})

    def job():
        try:
            _deliver(old_email, subject, text_body, html_body)
        except Exception as e:
            log.warning('email-changed notice failed: %s', type(e).__name__)
    _later(job)


def check_code(request, email, purpose, code):
    """코드를 대조한다. 맞으면 세션에 인증 사실을 남긴다.

    실패 문구는 하나다. 예전에는 "먼저 코드를 받아 주세요"(그 주소로 보낸 코드가 없다) ·
    "다른 브라우저" · "N번 남음" 이 갈려, 가입되지 않은 주소(코드가 없음)와 가입된 주소가 구별됐다.
    """
    generic = _('인증 코드가 맞지 않거나 만료되었습니다. 코드를 요청한 브라우저에서 입력해 주세요.')
    email = normalize(email)
    code = code.strip() if isinstance(code, str) else ''

    # (주소, 목적)당 하루 오입력 한도. 코드가 바뀌어도 누적한다 — 전에는 코드 하나에 5번이라
    # 5분마다 새 코드를 받으면 하루 약 1,440번 추측할 수 있었다. 코드가 없는 주소도 똑같이 센다.
    if throttle.over(throttle.CODE_FAIL[0], 'code_fail', email, purpose):
        return False, _('오늘은 인증 코드를 너무 많이 틀렸습니다. 내일 다시 시도해 주세요.')

    sk = request.session.session_key
    # 이 브라우저가 받은, 아직 쓰지 않은 가장 최근 코드. 남이 같은 주소로 요청한 코드는 보지 않는다.
    row = (models.EmailVerification.objects
           .filter(email=email, purpose=purpose, session_key=sk, verified_at__isnull=True)
           .order_by('-created_at').first()) if sk else None

    ok = (row is not None
          and (timezone.now() - row.created_at).total_seconds() <= settings.EMAIL_CODE_TTL
          and row.attempts < settings.EMAIL_CODE_MAX_ATTEMPTS
          # compare_digest 는 ASCII 가 아닌 문자열(전각 숫자 등)에 TypeError 를 낸다
          and code.isascii() and code.isdigit()
          and secrets.compare_digest(row.code, code))
    if not ok:
        throttle.hit('code_fail', throttle.CODE_FAIL[1], email, purpose)
        if row is not None:
            row.attempts += 1
            row.save(update_fields=['attempts'])
        return False, generic

    # 한 번 쓴 코드는 다시 통과하지 않는다(위 조회가 verified_at 이 빈 것만 본다)
    row.verified_at = timezone.now()
    row.save(update_fields=['verified_at'])
    throttle.reset('code_fail', email, purpose)

    store = request.session.get(SESSION_KEY, {})
    store[purpose] = {'email': email, 'at': timezone.now().timestamp()}
    request.session[SESSION_KEY] = store
    request.session.modified = True
    return True, _('이메일 인증이 끝났습니다.')


def verified_email(request, purpose):
    """이 세션에서 인증이 끝난 주소. 없거나 만료됐으면 None."""
    entry = (request.session.get(SESSION_KEY) or {}).get(purpose)
    if not entry:
        return None
    if timezone.now().timestamp() - entry.get('at', 0) > settings.EMAIL_CODE_TTL:
        return None
    return entry.get('email')


def clear_verification(request, purpose):
    store = request.session.get(SESSION_KEY) or {}
    if purpose in store:
        del store[purpose]
        request.session[SESSION_KEY] = store
        request.session.modified = True


# ---------------------------------------------------------------------------
# 마이그레이션 대상 판별
# ---------------------------------------------------------------------------
def security_of(user):
    """AccountSecurity 를 가져오되 없으면 만든다."""
    row, _created = models.AccountSecurity.objects.get_or_create(user=user)
    return row


def needs_migration(user):
    if not user.is_authenticated:
        return False
    return not models.AccountSecurity.objects.filter(
        user=user, newrulepassed=True).exists()
