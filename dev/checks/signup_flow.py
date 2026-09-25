# -*- coding: utf-8 -*-
"""가입 직후 '기존 사용자 1회 인증' 으로 끌려가지 않는지 본다.

2026-09-02 ~ 09-26 에 가입 뷰가 AccountSecurity.newrulepassed 를 켜지 않아,
이메일 인증을 막 마친 새 가입자 8명 전원이 곧바로 1회 인증 화면으로 가서
인증 메일을 한 번 더 받았다. 그 회귀를 막는다.

reCAPTCHA 는 네트워크를 타므로 막아 둔다(검증 통과로 친다). 이메일 인증은
인증을 마친 뒤의 세션 상태를 직접 심는다 — 코드 발송·대조는 이 검사의 대상이 아니다.

    python dev/checks/signup_flow.py
"""
import _bootstrap  # noqa: F401
import django

django.setup()

from unittest import mock  # noqa: E402

from django.contrib.auth.models import User  # noqa: E402
from django.test import Client  # noqa: E402
from django.utils import timezone  # noqa: E402

from captcha.fields import ReCaptchaField  # noqa: E402
from iidxrank import accounts, models  # noqa: E402

fails = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name,
                         (' — %s' % detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


UID = 'zzsignupcheck'
EMAIL = 'zz-signup-check@example.invalid'
User.objects.filter(username=UID).delete()

c = Client()
c.get('/join/')                                   # 세션 만들기
s = c.session
s[accounts.SESSION_KEY] = {'signup': {'email': EMAIL, 'at': timezone.now().timestamp()}}
s.save()

try:
    with mock.patch.object(ReCaptchaField, 'clean', lambda self, v: 'ok'):
        r = c.post('/join/', {
            'id': UID, 'email': EMAIL,
            'password': 'Zz-check-pass-8', 'password_again': 'Zz-check-pass-8',
            'agree_privacy': 'on', 'g-recaptcha-response': 'x',
        })
    check('가입 POST → 302', r.status_code == 302, '%s %s' % (r.status_code, r.content[:300]))
    u = User.objects.filter(username=UID).first()
    check('계정 생성', u is not None)
    if u:
        check('newrulepassed = True',
              models.AccountSecurity.objects.filter(user=u, newrulepassed=True).exists())
        check('needs_migration = False', not accounts.needs_migration(u))
        r = c.get('/account/')
        check('/account/ 가 1회 인증으로 보내지 않음',
              not (r.status_code == 302 and 'verify-account' in r.get('Location', '')),
              '%s %s' % (r.status_code, r.get('Location')))
        check('가입 인증 기록을 세션에서 지움',
              'signup' not in (c.session.get(accounts.SESSION_KEY) or {}))
finally:
    u = User.objects.filter(username=UID).first()
    if u:
        models.Player.objects.filter(user=u).delete()
        u.delete()

print('=== 비밀번호 재설정 → 1회 인증도 끝난 것으로 ===')
# 아직 1회 인증을 안 한 기존 사용자(AccountSecurity 없음, 주소는 이 계정만 씀).
LID, LEMAIL = 'zzresetcheck', 'zz-reset-check@example.invalid'
User.objects.filter(username=LID).delete()
legacy = User.objects.create_user(LID, email=LEMAIL, password='old')
try:
    check('시작: 1회 인증 대상', accounts.needs_migration(legacy))
    c2 = Client()
    c2.get('/reset-password/')
    s = c2.session
    s[accounts.SESSION_KEY] = {'reset_pw': {'email': LEMAIL, 'at': timezone.now().timestamp()}}
    s.save()
    r = c2.post('/reset-password/', {'email': LEMAIL, 'new_password': 'Zz-reset-pass-8',
                                     'new_password_again': 'Zz-reset-pass-8'})
    check('재설정 200', r.status_code == 200, str(r.status_code))
    legacy.refresh_from_db()
    check('새 비밀번호로 바뀜', legacy.check_password('Zz-reset-pass-8'))
    check('재설정 후 1회 인증 대상 아님', not accounts.needs_migration(legacy))
    c2.login(username=LID, password='Zz-reset-pass-8')
    r = c2.get('/account/')
    check('로그인 후 /account/ 가 1회 인증으로 보내지 않음',
          not (r.status_code == 302 and 'verify-account' in r.get('Location', '')),
          '%s %s' % (r.status_code, r.get('Location')))
finally:
    models.Player.objects.filter(user__username=LID).delete()
    User.objects.filter(username=LID).delete()

print('')
print('총 실패: %d' % len(fails))
