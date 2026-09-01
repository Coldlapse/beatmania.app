# -*- coding: utf-8 -*-
"""계정 인증 화면들.

    /account/verify/send/     인증 코드 발송 (AJAX)
    /account/verify/check/    인증 코드 확인 (AJAX)
    /account/email/           이메일 변경
    /find-id/                 아이디 찾기
    /reset-password/          비밀번호 재설정
    /account/verify-account/  기존 사용자 1회 인증 (마이그레이션)

가입 폼의 이메일 인증도 위 두 AJAX 를 함께 쓴다. 목적(purpose)별로 누가
부를 수 있는지는 _allowed_purpose() 한 곳에서 판단한다 - 뷰마다 흩어 두면
하나를 빠뜨렸을 때 조용히 열린다.
"""

import json

from django.contrib.auth import login as login_django
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from iidxrank import accounts, forms, models

V = models.EmailVerification


def _allowed_purpose(request, purpose):
    """이 요청이 그 목적으로 인증을 시작해도 되나."""
    if purpose == V.SIGNUP:
        return not request.user.is_authenticated
    if purpose in (V.FIND_ID, V.RESET_PW):
        return not request.user.is_authenticated
    if purpose == V.CHANGE:
        return request.user.is_authenticated
    if purpose == V.MIGRATE:
        return (request.user.is_authenticated
                and accounts.needs_migration(request.user))
    return False


def _body(request):
    try:
        return json.loads(request.body or b'{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def verify_send(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'POST only'}, status=405)
    data = _body(request)
    purpose = data.get('purpose')
    email = accounts.normalize(data.get('email'))

    if not _allowed_purpose(request, purpose):
        return JsonResponse(
            {'ok': False, 'message': _('지금은 이 인증을 진행할 수 없습니다.')},
            status=403)

    # 목적별로 "그 주소가 쓸 수 있는 주소인가" 가 다르다.
    if purpose in (V.SIGNUP, V.CHANGE, V.MIGRATE):
        exclude = request.user if request.user.is_authenticated else None
        if accounts.email_taken(email, exclude_user=exclude):
            return JsonResponse(
                {'ok': False,
                 'message': _('이미 다른 계정이 쓰고 있는 이메일입니다.')})
    elif purpose in (V.FIND_ID, V.RESET_PW):
        # 가입 여부를 알려 주지 않는다. 없는 주소여도 같은 응답을 주고
        # 메일만 보내지 않는다 - 그러지 않으면 가입자 목록을 캐낼 수 있다.
        if accounts.recoverable_user(email) is None:
            return JsonResponse(
                {'ok': True,
                 'message': _('가입된 주소라면 인증 코드를 보냈습니다.')})

    ok, message = accounts.send_code(request, email, purpose)
    return JsonResponse({'ok': ok, 'message': str(message)})


def verify_check(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'POST only'}, status=405)
    data = _body(request)
    purpose = data.get('purpose')
    if not _allowed_purpose(request, purpose):
        return JsonResponse(
            {'ok': False, 'message': _('지금은 이 인증을 진행할 수 없습니다.')},
            status=403)
    ok, message = accounts.check_code(
        request, data.get('email'), purpose, data.get('code'))
    return JsonResponse({'ok': ok, 'message': str(message)})


# ---------------------------------------------------------------------------
# 이메일 변경
# ---------------------------------------------------------------------------
def change_email(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        form = forms.ChangeEmailForm(request, request.POST)
        if form.is_valid():
            user = request.user
            user.email = form.cleaned_data['email']
            user.save(update_fields=['email'])
            sec = accounts.security_of(user)
            sec.email_verified_at = timezone.now()
            sec.save(update_fields=['email_verified_at'])
            accounts.clear_verification(request, V.CHANGE)
            return redirect('account')
    else:
        form = forms.ChangeEmailForm(request)
    return render(request, 'user/change_email.html',
                  {'form': form, 'purpose': V.CHANGE,
                   'current_email': request.user.email})


# ---------------------------------------------------------------------------
# 아이디 찾기
# ---------------------------------------------------------------------------
def find_id(request):
    if request.user.is_authenticated:
        return redirect('home')
    found = None
    if request.method == 'POST':
        form = forms.FindIdForm(request, request.POST)
        if form.is_valid():
            user = accounts.recoverable_user(form.cleaned_data['email'])
            accounts.clear_verification(request, V.FIND_ID)
            # 인증까지 끝난 사람에게는 아이디를 그대로 보여 준다. 가리면
            # 정작 본인이 못 알아본다.
            found = user.username if user else None
    else:
        form = forms.FindIdForm(request)
    return render(request, 'user/find_id.html',
                  {'form': form, 'purpose': V.FIND_ID, 'found': found})


# ---------------------------------------------------------------------------
# 비밀번호 재설정
# ---------------------------------------------------------------------------
def reset_password(request):
    if request.user.is_authenticated:
        return redirect('setpassword')
    done = False
    if request.method == 'POST':
        form = forms.ResetPasswordForm(request, request.POST)
        if form.is_valid():
            user = accounts.recoverable_user(form.cleaned_data['email'])
            if user is not None:
                user.set_password(form.cleaned_data['new_password'])
                user.save()
            accounts.clear_verification(request, V.RESET_PW)
            done = True
    else:
        form = forms.ResetPasswordForm(request)
    return render(request, 'user/reset_password.html',
                  {'form': form, 'purpose': V.RESET_PW, 'done': done})


# ---------------------------------------------------------------------------
# 기존 사용자 1회 인증
# ---------------------------------------------------------------------------
def verify_account(request):
    """2026-09 규칙으로 넘어오는 화면. 계정당 한 번만 지난다."""
    if not request.user.is_authenticated:
        return redirect('login')
    if not accounts.needs_migration(request.user):
        return redirect('account')

    if request.method == 'POST':
        form = forms.MigrateForm(request, request.POST)
        if form.is_valid():
            user = request.user
            user.email = form.cleaned_data['email']
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            # 비밀번호가 바뀌면 이 세션도 끊긴다. 지금 화면을 보고 있는
            # 본인은 유지한다.
            update_session_auth_hash(request, user)
            sec = accounts.security_of(user)
            sec.newrulepassed = True
            sec.email_verified_at = timezone.now()
            sec.migrated_at = timezone.now()
            sec.save()
            accounts.clear_verification(request, V.MIGRATE)
            return redirect('home')
    else:
        form = forms.MigrateForm(request)

    return render(request, 'user/verify_account.html', {
        'form': form,
        'purpose': V.MIGRATE,
        'current_email': request.user.email,
        # 지금 주소가 다른 계정과 겹치거나 형식이 깨져 그대로 쓸 수 없는 경우를
        # 화면에서 미리 알려 준다. 인증 버튼을 누른 뒤에 알게 하면 헛수고다.
        'current_email_usable': (
            accounts.is_email_shaped(request.user.email)
            and not accounts.email_taken(request.user.email,
                                         exclude_user=request.user)),
    })
