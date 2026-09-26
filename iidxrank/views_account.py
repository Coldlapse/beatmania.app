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
        data = json.loads(request.body or b'{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    # 배열·숫자 본문이면 data.get 에서 500 이었다
    return data if isinstance(data, dict) else {}


def verify_send(request):
    """인증 코드 발송.

    로그인하지 않은 목적(가입·아이디 찾기·비밀번호 재설정)은 **가입 여부와 상관없이 같은 응답**을
    준다(2026-09-26). 전에는 가입은 "이미 다른 계정이 쓰고 있는 이메일", 찾기·재설정은 가입 여부에
    따라 다른 문구를 돌려줘서 주소를 넣어 보는 것만으로 가입자 목록을 캐낼 수 있었다.
      - 가입: 이미 쓰이는 주소면 코드 대신 "이미 가입된 주소" 안내 메일을 그 주소로 보낸다
      - 찾기·재설정: 대상 계정이 없으면 메일을 보내지 않는다(응답은 같다)
    발송 한도·재발송 간격도 가입 여부와 상관없이 같은 순서로 본다.
    로그인한 사람의 목적(이메일 변경·1회 인증)은 전처럼 "이미 쓰이는 주소" 를 알려 준다 — 로그인이
    필요하고 발송 한도가 걸려 있어 목록을 캐내는 데 쓰기 어렵다.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'POST only'}, status=405)
    data = _body(request)
    purpose = data.get('purpose')
    email = accounts.normalize(data.get('email'))

    if not _allowed_purpose(request, purpose):
        return JsonResponse(
            {'ok': False, 'message': _('지금은 이 인증을 진행할 수 없습니다.')},
            status=403)
    if not accounts.is_email_shaped(email):
        return JsonResponse({'ok': False, 'message': _('이메일 주소 형식이 올바르지 않습니다.')})

    limited = accounts.send_limit_message(request, email)
    if limited:
        return JsonResponse({'ok': False, 'message': str(limited)})
    left = accounts.seconds_until_resend(request, email, purpose)
    if left:
        return JsonResponse({'ok': False, 'message': _('%(sec)d초 뒤에 다시 보낼 수 있습니다.') % {'sec': left}})

    if purpose in (V.CHANGE, V.MIGRATE):
        if accounts.email_taken(email, exclude_user=request.user):
            return JsonResponse(
                {'ok': False,
                 'message': _('이미 다른 계정이 쓰고 있는 이메일입니다.')})
        accounts.note_send_request(request, email, purpose)
        ok, message = accounts.send_code(request, email, purpose)
        return JsonResponse({'ok': ok, 'message': str(message)})

    accounts.note_send_request(request, email, purpose)
    if purpose == V.SIGNUP:
        sent = _('인증 코드를 보냈습니다. 메일함을 확인해 주세요.')
        if accounts.email_taken(email):
            accounts.send_already_registered(request, email)
            return JsonResponse({'ok': True, 'message': str(sent)})
    else:   # FIND_ID, RESET_PW
        sent = _('가입된 주소라면 인증 코드를 보냈습니다. 메일이 오지 않으면 스팸함을 확인하거나 5분 뒤에 다시 요청해 주세요.')
        if accounts.recoverable_user(email) is None:
            return JsonResponse({'ok': True, 'message': str(sent)})

    ok, message = accounts.send_code(request, email, purpose, success_message=sent)
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
                # 재설정은 1회 인증의 조건(이메일 확인, 새 비밀번호 규칙, 그 주소를
                # 쓰는 계정이 하나뿐 — recoverable_user 가 보장)을 모두 지난다.
                # 기록하지 않으면 재설정 직후 로그인에서 인증 메일이 한 번 더 간다.
                sec = accounts.security_of(user)
                if not sec.newrulepassed:
                    sec.newrulepassed = True
                    sec.email_verified_at = timezone.now()
                    sec.migrated_at = timezone.now()
                    sec.save()
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
