# -*- coding: utf-8 -*-
"""계정 인증 - 이메일 인증 코드 발송·확인과 그에 딸린 규칙.

뷰에서 쓰는 함수는 넷이다.

    send_code(request, email, purpose)   코드를 만들어 메일로 보낸다
    check_code(request, email, purpose, code)  코드를 대조하고 세션에 기록한다
    verified_email(request, purpose)     지금 세션에서 인증이 끝난 주소
    clear_verification(request, purpose) 인증 기록을 지운다

세션에도 결과를 남기는 이유: 가입 폼이 비밀번호 오류 등으로 다시 그려져도
이메일 인증이 풀리면 안 된다. 반대로 재발송 간격은 세션이 아니라 DB 로 잰다 -
쿠키를 지우는 것만으로 우회되면 안 되기 때문이다.
"""

import re
import secrets

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext as _

from iidxrank import models

# 세션에 인증 결과를 담는 자리. 목적별로 따로 둔다 - 가입 인증이 이메일 변경
# 인증으로 재활용되면 안 된다.
SESSION_KEY = 'email_verified'

# 화면에서 쓰는 것과 같은 검사. Django 의 EmailValidator 보다 좁게 잡는다 -
# 여기서 통과한 주소로 실제로 메일을 보내야 하므로, 애매한 것은 거른다.
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]{2,}$')


def is_email_shaped(value):
    return bool(value) and bool(EMAIL_RE.match(value.strip()))


def normalize(email):
    """대소문자와 앞뒤 공백만 정리한다.

    Gmail 의 점(.)이나 +태그까지 정규화하지는 않는다. 그렇게 하면
    a.b@gmail.com 과 ab@gmail.com 을 같은 주소로 보게 되는데, 그것을 다르게
    쓰고 있는 기존 사용자가 있으면 중복으로 걸려 버린다.
    """
    return (email or '').strip().lower()


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


def _latest(email, purpose):
    return (models.EmailVerification.objects
            .filter(email=normalize(email), purpose=purpose)
            .order_by('-created_at').first())


def seconds_until_resend(email, purpose):
    """지금 다시 보낼 수 있나. 0 이면 보낼 수 있고, 양수면 그만큼 남았다."""
    row = _latest(email, purpose)
    if row is None:
        return 0
    waited = (timezone.now() - row.last_sent_at).total_seconds()
    left = settings.EMAIL_RESEND_INTERVAL - waited
    return max(0, int(left + 0.999))


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


def send_code(request, email, purpose):
    """코드를 만들어 보낸다. (성공여부, 메시지) 를 돌려준다."""
    email = normalize(email)
    if not is_email_shaped(email):
        return False, _('이메일 주소 형식이 올바르지 않습니다.')

    left = seconds_until_resend(email, purpose)
    if left:
        return False, _('%(sec)d초 뒤에 다시 보낼 수 있습니다.') % {'sec': left}

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

    msg = EmailMultiAlternatives(
        subject, text_body, settings.DEFAULT_FROM_EMAIL, [email])
    msg.attach_alternative(html_body, 'text/html')
    msg.send(fail_silently=False)
    return True, _('인증 코드를 보냈습니다. 메일함을 확인해 주세요.')


def check_code(request, email, purpose, code):
    """코드를 대조한다. 맞으면 세션에 인증 사실을 남긴다."""
    email = normalize(email)
    code = (code or '').strip()
    row = _latest(email, purpose)
    if row is None:
        return False, _('먼저 인증 코드를 받아 주세요.')

    age = (timezone.now() - row.created_at).total_seconds()
    if age > settings.EMAIL_CODE_TTL:
        return False, _('인증 코드가 만료되었습니다. 다시 받아 주세요.')

    if row.attempts >= settings.EMAIL_CODE_MAX_ATTEMPTS:
        return False, _('시도 횟수를 넘겼습니다. 인증 코드를 다시 받아 주세요.')

    # 코드를 알아낸 제3자가 다른 브라우저에서 쓰지 못하게 한다.
    if row.session_key and row.session_key != request.session.session_key:
        return False, _('인증을 시작한 브라우저에서 진행해 주세요.')

    if not secrets.compare_digest(row.code, code):
        row.attempts += 1
        row.save(update_fields=['attempts'])
        left = settings.EMAIL_CODE_MAX_ATTEMPTS - row.attempts
        return False, _('인증 코드가 맞지 않습니다. (%(n)d번 남음)') % {'n': max(0, left)}

    row.verified_at = timezone.now()
    row.save(update_fields=['verified_at'])

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
