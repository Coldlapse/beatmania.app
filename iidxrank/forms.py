#-*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth import password_validation
from captcha.fields import ReCaptchaField
from django.utils.functional import lazy
from django.utils.safestring import mark_safe

# mark_safe() 는 받은 값을 그 자리에서 문자열로 만든다. gettext_lazy 를 그대로
# 넣으면 모듈을 읽는 시점(언어가 정해지기 전)에 번역이 굳어 버려, 어떤 언어로
# 봐도 한국어가 나온다. 감싸는 일 자체를 미룬다.
mark_safe_lazy = lazy(mark_safe, str)

from iidxrank import reserved
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from iidxrank import models
from iidxrank import iidx


"""
membership related
"""

alphanumeric = RegexValidator(r'^[0-9a-zA-Z_]*$', 'ID: Only alphanumeric characters are allowed. 영문/숫자,_만 입력 가능합니다.')

class LoginForm(forms.Form):
    id = forms.CharField(
            label=_('아이디'), min_length=4,
            widget=forms.TextInput(attrs={
                'autocomplete': 'username', 'autofocus': True,
                'placeholder': _('아이디')}))
    password = forms.CharField(
            label=_('비밀번호'),
            widget=forms.PasswordInput(attrs={
                'autocomplete': 'current-password', 'placeholder': _('비밀번호')}))

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        if ('id' not in cleaned_data):
            return
        if ('password' not in cleaned_data):
            return
        _username = cleaned_data['id']
        _password = cleaned_data['password']
        user = authenticate(username=_username, password=_password)
        if (user==None):
            raise forms.ValidationError('ID or Password does not exists.')

class JoinForm(forms.Form):
    id = forms.CharField(
            label=_('아이디'), min_length=4, validators=[alphanumeric],
            help_text=_('영문·숫자·밑줄(_)만, 4자 이상. 가입 후에는 바꿀 수 없습니다. 사이트가 쓰는 이름(admin, status 등)은 쓸 수 없습니다.'),
            widget=forms.TextInput(attrs={
                'autocomplete': 'username', 'autofocus': True,
                'placeholder': _('영문/숫자 4자 이상'),
                # 가입 폼에서 주소 미리보기를 실시간으로 보여주기 위한 훅
                'data-url-preview': '1'}))
    email = forms.CharField(
            label=_('이메일'),
            help_text=_('계정 인증과 아이디·비밀번호 찾기에만 씁니다. 인증을 끝내야 가입할 수 있습니다.'),
            widget=forms.EmailInput(attrs={
                'autocomplete': 'email', 'placeholder': _('you@example.com')}))
    # min_length 를 여기에도 두는 이유: 검증기가 잡기 전에 브라우저와 폼이
    # 먼저 알려 주는 편이 친절하다. 값은 AUTH_PASSWORD_VALIDATORS 와 맞춘다 —
    # 어긋나면 "4자 이상" 이라 써 놓고 8자에서 거부하는 화면이 된다.
    password = forms.CharField(
            label=_('비밀번호'), min_length=8,
            help_text=_('8자 이상. 영문·숫자·기호를 쓸 수 있고 조합 규칙은 없습니다.'),
            widget=forms.PasswordInput(attrs={
                'autocomplete': 'new-password', 'placeholder': _('8자 이상')}))
    password_again = forms.CharField(
            label=_('비밀번호 확인'),
            widget=forms.PasswordInput(attrs={
                'autocomplete': 'new-password', 'placeholder': _('한 번 더 입력')}))
    # 동의는 캡차보다 먼저 와야 한다. 캡차를 푼 뒤에 체크박스가 나오면
    # 놓치기 쉽고, 놓치면 캡차를 다시 풀어야 한다.
    agree_privacy = forms.BooleanField(
        required=True,
        label=mark_safe_lazy(_(
            '<a href="/privacy/" target="_blank" rel="noopener">개인정보처리방침</a>'
            '을 읽었고 이에 동의합니다.')),
        error_messages={'required': _('개인정보처리방침에 동의해야 가입할 수 있습니다.')})
    # 선언 순서가 곧 렌더 순서다. 캡차는 마지막에 와야 자연스럽다.
    #
    # 기본 오류 문구는 "필수 항목입니다." 인데, 캡차는 라벨이 비어 있어서
    # 무엇이 필수라는 것인지 화면에서 알 수 없었다. 캡차를 안 풀고 가입을
    # 누르면 그냥 새로고침된 것처럼 보였다.
    captcha = ReCaptchaField(
        label='',
        error_messages={
            'required': _('로봇이 아님을 확인해 주세요.'),
            'invalid': _('로봇 확인에 실패했습니다. 다시 시도해 주세요.'),
        })

    def __init__(self, request=None, *args, **kwargs):
        # 이메일 인증 결과가 세션에 있으므로 request 가 필요하다. 기본값을
        # 둔 이유는 이 폼을 request 없이 만들어 쓰는 자리(테스트 등)를
        # 깨뜨리지 않기 위해서다 - 그때는 인증 확인이 실패한다.
        self.request = request
        super(JoinForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        from iidxrank import accounts
        email = accounts.normalize(self.cleaned_data['email'])
        if not accounts.is_email_shaped(email):
            raise forms.ValidationError(_('이메일 주소 형식이 올바르지 않습니다.'))
        if accounts.email_taken(email):
            raise forms.ValidationError(_('이미 다른 계정이 쓰고 있는 이메일입니다.'))
        done = accounts.verified_email(self.request, 'signup') if self.request else None
        if done != email:
            raise forms.ValidationError(
                _('이메일 인증을 먼저 끝내 주세요. 주소를 바꾸셨다면 다시 인증해야 합니다.'))
        return email

    def clean_password(self):
        # settings.AUTH_PASSWORD_VALIDATORS 는 저절로 돌지 않는다. 그것을
        # 적용해 주는 것은 django.contrib.auth 의 기본 폼들인데 이 폼은
        # 직접 만든 것이다. 여기서 부르지 않으면 설정이 통째로 무효다.
        password = self.cleaned_data['password']
        password_validation.validate_password(password)
        return password

    def clean_id(self):
        # 아이디는 그대로 공개 주소(/u/<아이디>/)가 된다. 사이트가 쓰는 이름을
        # 가져가면 그 사람의 프로필이 사이트 페이지에 가려지거나, 반대로
        # 사이트 페이지가 개인 프로필로 오해된다. 사칭에 쓰이기 쉬운 이름도
        # 같이 막는다. 목록은 iidxrank/reserved.py 에 있다.
        name = self.cleaned_data['id']
        if reserved.is_blocked_username(name):
            raise forms.ValidationError(
                _('"%(name)s" 은(는) 사용할 수 없는 아이디입니다.'),
                params={'name': name})
        return name

    def clean(self):
        # self.data 를 직접 읽으면 필드가 빠진 POST 에 KeyError -> 500 이 난다.
        # 게다가 그 500 이 아이디 중복 검사보다 먼저 터져 검사 자체를 건너뛴다.
        cleaned_data = super(JoinForm, self).clean()
        username = cleaned_data.get('id')
        if username and User.objects.filter(username=username).exists():
            self.add_error('id', _('이미 사용 중인 아이디입니다.'))
        password = cleaned_data.get('password')
        again = cleaned_data.get('password_again')
        if password and again and password != again:
            self.add_error('password_again', _('비밀번호가 서로 다릅니다.'))
        return cleaned_data

class IIDXIDWidget(forms.MultiWidget):
    """IIDX ID 를 '앞글자 + 네 자리 3칸' 으로 받는다.

    한 칸짜리 자유 입력이던 것을 나눈 이유 — 저장된 값이 제각각이었다.
    X000000000000 149건, X-0000-0000-0000 49건, 여덟 자리만 37건, 그 밖에
    하이픈 위치가 다른 것들. 자유 입력이면 계속 섞인다.

    화면에서 나눠 받고 저장은 X-0000-0000-0000 한 가지로 맞춘다.
    """

    PREFIXES = [('K', 'K'), ('C', 'C')]

    def __init__(self, attrs=None):
        base = {'inputmode': 'numeric', 'pattern': '[0-9]{4}',
                'maxlength': '4', 'class': 'form-control bm-iidxid-part',
                'placeholder': '0000'}
        widgets = [
            forms.Select(choices=self.PREFIXES,
                         attrs={'class': 'form-select bm-iidxid-prefix'}),
            forms.TextInput(attrs=dict(base)),
            forms.TextInput(attrs=dict(base)),
            forms.TextInput(attrs=dict(base)),
        ]
        super().__init__(widgets, attrs)

    # 칸 사이에 하이픈을 그려 저장될 모양(X-0000-0000-0000)이 눈에 보이게 한다.
    # MultiWidget 기본 렌더링은 칸만 나열해서 무엇이 만들어지는지 알 수 없다.
    template_name = 'widgets/iidxid.html'

    def decompress(self, value):
        """저장된 값을 네 칸으로 되돌린다.

        형식이 섞여 있으므로 느슨하게 읽는다. 알아볼 수 없으면 빈 칸으로 둔다 —
        엉뚱하게 채워 두면 저장할 때 남의 값으로 덮어쓴다.
        """
        if not value:
            return ['K', '', '', '']
        v = str(value).strip().upper()
        prefix = 'K'
        if v[:1] in ('K', 'C'):
            prefix, v = v[0], v[1:]
        digits = ''.join(ch for ch in v if ch.isdigit())
        if len(digits) == 12:
            return [prefix, digits[0:4], digits[4:8], digits[8:12]]
        return [prefix, '', '', '']


class IIDXIDField(forms.MultiValueField):
    widget = IIDXIDWidget

    def __init__(self, **kwargs):
        fields = (
            forms.ChoiceField(choices=IIDXIDWidget.PREFIXES),
            forms.RegexField(regex=r'^[0-9]{4}$'),
            forms.RegexField(regex=r'^[0-9]{4}$'),
            forms.RegexField(regex=r'^[0-9]{4}$'),
        )
        super().__init__(fields=fields, require_all_fields=True, **kwargs)

    def compress(self, values):
        if not values or not all(values):
            return ''
        return '%s-%s-%s-%s' % tuple(values)


class AccountForm(forms.Form):
    first_name = forms.CharField(
            label=_('닉네임'),
            help_text=_('순위표 등 사이트 곳곳에 표시되는 공개 이름입니다. '
                        '다른 사람과 같아도 되며 언제든 바꿀 수 있습니다. '
                        '주소에 쓰이는 아이디와는 다릅니다.'),
            widget=forms.TextInput(attrs={'placeholder': _('사이트에 표시될 이름')}))
    # 게임 안의 이름(DJ NAME)을 ID 보다 먼저 묻는다. 사람이 자기 이름을 먼저
    # 떠올리고 숫자를 나중에 찾아보기 때문이다.
    iidxnick = forms.CharField(
            label='IIDX DJ NAME',
            required=False,
            help_text=_('서열표 프로필에 DJ NAME 으로 표시됩니다. 사이트 닉네임과는 '
                        '별개이며, 다른 사람과 같아도 됩니다.'),
            widget=forms.TextInput(attrs={'placeholder': _('DJ NAME')}))
    iidxid = IIDXIDField(
            label='IIDX ID',
            required=False,
            help_text=_('게임 화면에 나오는 ID 입니다. 앞글자를 고르고 네 자리씩 입력하세요.'))
    classes = iidx.classes
    spclass = forms.ChoiceField(label=_('SP 단위'), choices=classes)
    dpclass = forms.ChoiceField(label=_('DP 단위'), choices=classes)
    private = forms.BooleanField(
            label=_('프로필 비공개'),
            help_text=_('켜면 다른 사람이 내 서열표와 유저 목록에서 나를 볼 수 없습니다.'),
            widget=forms.CheckboxInput(), required=False)


class SetPasswordForm(forms.Form):
    """비밀번호 변경.

    현재 비밀번호를 반드시 함께 받는다. 예전에는 새 비밀번호 두 칸만 있었는데,
    그러면 로그인된 세션을 손에 넣은 사람이 비밀번호를 바꿔 계정을 영구히
    가져갈 수 있었다(실측함). 세션 탈취는 세션이 만료되면 끝나지만 비밀번호
    변경은 되돌릴 수 없다 — 현재 비밀번호를 물어 그 상승을 막는다.

    같은 사이트의 탈퇴 폼은 이미 비밀번호를 확인하고 있었다. 계정을 지우는
    쪽은 막혀 있고 빼앗는 쪽은 열려 있던 셈이다.

    Django 의 PasswordChangeForm 과 같은 호출 방식을 쓴다: 첫 인자가 user 다.
    """

    old_password = forms.CharField(
            label=_('현재 비밀번호'),
            widget=forms.PasswordInput(attrs={
                'autocomplete': 'current-password', 'autofocus': True,
                'placeholder': _('지금 쓰는 비밀번호')}))
    new_password = forms.CharField(
            label=_('새 비밀번호'), min_length=8,
            help_text=_('8자 이상. 영문·숫자·기호를 쓸 수 있고 조합 규칙은 없습니다.'),
            widget=forms.PasswordInput(attrs={
                'autocomplete': 'new-password',
                'placeholder': _('8자 이상')}))
    new_password_again = forms.CharField(
            label=_('새 비밀번호 확인'),
            widget=forms.PasswordInput(attrs={
                'autocomplete': 'new-password', 'placeholder': _('한 번 더 입력')}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(*args, **kwargs)

    def clean_old_password(self):
        old = self.cleaned_data['old_password']
        if not self.user.check_password(old):
            raise forms.ValidationError(_('현재 비밀번호가 맞지 않습니다.'))
        return old

    def clean_new_password(self):
        # JoinForm 과 같은 이유로 여기서 직접 부른다. user 를 넘기면
        # UserAttributeSimilarityValidator 가 아이디·이메일과 비교할 수 있다.
        new = self.cleaned_data['new_password']
        password_validation.validate_password(new, self.user)
        return new

    def clean(self):
        # cleaned_data 를 쓴다. self.data 를 직접 읽으면 필드가 빠진 POST 하나에
        # KeyError 로 500 이 난다.
        cleaned_data = super(SetPasswordForm, self).clean()
        new = cleaned_data.get('new_password')
        again = cleaned_data.get('new_password_again')
        old = cleaned_data.get('old_password')

        # 오류는 해당 칸 옆에 붙인다. 폼 전체 오류로 던지면 어느 칸이
        # 잘못됐는지 화면에서 알 수 없다.
        if new and again and new != again:
            self.add_error('new_password_again',
                           _('새 비밀번호가 서로 다릅니다.'))
        if new and old and new == old:
            self.add_error('new_password',
                           _('지금 쓰는 비밀번호와 다른 것으로 정해 주세요.'))
        return cleaned_data


class WithdrawForm(forms.Form):
    id = forms.CharField(
            label=_('아이디'), min_length=5,
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    password = forms.CharField(
            label=_('비밀번호'),
            widget=forms.PasswordInput(attrs={
                'autocomplete': 'current-password', 'autofocus': True}))
    password_again = forms.CharField(
            label=_('비밀번호 확인'),
            widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))

    def clean(self):
        cleaned_data = super(WithdrawForm, self).clean()
        username = cleaned_data.get('id')
        password = cleaned_data.get('password')
        again = cleaned_data.get('password_again')
        if password and again and password != again:
            self.add_error('password_again', _('비밀번호가 서로 다릅니다.'))
            return cleaned_data
        if username and password and authenticate(
                username=username, password=password) is None:
            self.add_error('password', _('비밀번호가 맞지 않습니다.'))
        return cleaned_data


class AvatarForm(forms.Form):
    """프로필 사진 업로드.

    확장자만 믿지 않는다. Django 의 ImageField 가 Pillow 로 실제 이미지인지
    검사하고, 그 위에 용량·크기 상한을 따로 건다. 확장자를 png 로 바꾼
    실행 파일은 여기서 걸린다.
    """
    avatar = forms.ImageField(
            label=_('프로필 사진'),
            required=False,
            help_text=_('JPG · PNG · GIF · WebP, 최대 2MB. 정사각형 이미지를 권장합니다.'),
            widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}))

    MAX_SIDE = 2000     # 픽셀 폭탄(작은 파일, 거대한 해상도) 방지

    def clean_avatar(self):
        f = self.cleaned_data.get('avatar')
        if not f:
            return f
        limit = getattr(settings, 'MAX_AVATAR_BYTES', 2 * 1024 * 1024)
        if f.size > limit:
            raise forms.ValidationError(
                _('파일이 너무 큽니다. %(limit)dMB 이하로 올려주세요.')
                % {'limit': limit // (1024 * 1024)})
        w, h = getattr(f, 'image', None) and (f.image.width, f.image.height) or (0, 0)
        if w > self.MAX_SIDE or h > self.MAX_SIDE:
            raise forms.ValidationError(
                _('이미지가 너무 큽니다. 가로·세로 %(side)dpx 이하로 올려주세요.')
                % {'side': self.MAX_SIDE})
        return f


# ---------------------------------------------------------------------------
# 이메일 인증이 붙는 폼들
#
# 공통 규칙: 이메일 칸의 값이 **이 세션에서 인증이 끝난 주소와 같아야** 한다.
# 인증은 AJAX 로 먼저 끝내고, 폼 제출은 그 사실을 확인만 한다. 그래야
# 비밀번호 오류로 폼이 다시 그려져도 인증이 풀리지 않는다.
# ---------------------------------------------------------------------------
class _VerifiedEmailForm(forms.Form):
    """request 를 받아 세션의 인증 결과를 확인하는 폼의 공통 부분."""

    PURPOSE = None

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(_VerifiedEmailForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        from iidxrank import accounts
        email = accounts.normalize(self.cleaned_data['email'])
        if not accounts.is_email_shaped(email):
            raise forms.ValidationError(_('이메일 주소 형식이 올바르지 않습니다.'))
        done = accounts.verified_email(self.request, self.PURPOSE)
        if done != email:
            raise forms.ValidationError(
                _('이메일 인증을 먼저 끝내 주세요. 주소를 바꾸셨다면 다시 인증해야 합니다.'))
        return email


class ChangeEmailForm(_VerifiedEmailForm):
    PURPOSE = 'change'
    email = forms.CharField(
        label=_('새 이메일'),
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email', 'placeholder': _('you@example.com')}))

    def clean(self):
        from iidxrank import accounts
        cleaned_data = super(ChangeEmailForm, self).clean()
        email = cleaned_data.get('email')
        if email and accounts.email_taken(email, exclude_user=self.request.user):
            self.add_error('email', _('이미 다른 계정이 쓰고 있는 이메일입니다.'))
        return cleaned_data


class FindIdForm(_VerifiedEmailForm):
    PURPOSE = 'find_id'
    email = forms.CharField(
        label=_('가입할 때 쓴 이메일'),
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email', 'autofocus': True,
            'placeholder': _('you@example.com')}))


class ResetPasswordForm(_VerifiedEmailForm):
    PURPOSE = 'reset_pw'
    email = forms.CharField(
        label=_('가입할 때 쓴 이메일'),
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email', 'autofocus': True,
            'placeholder': _('you@example.com')}))
    new_password = forms.CharField(
        label=_('새 비밀번호'), min_length=8,
        help_text=_('8자 이상. 영문·숫자·기호를 쓸 수 있고 조합 규칙은 없습니다.'),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password', 'placeholder': _('8자 이상')}))
    new_password_again = forms.CharField(
        label=_('새 비밀번호 확인'),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password', 'placeholder': _('한 번 더 입력')}))

    def clean_new_password(self):
        from iidxrank import accounts
        new = self.cleaned_data['new_password']
        # 아이디·이메일과 비슷한지 보려면 대상 계정이 필요하다. 이 시점에는
        # 이메일 인증이 끝나 있으므로 계정을 특정할 수 있다.
        email = accounts.verified_email(self.request, self.PURPOSE)
        user = accounts.recoverable_user(email) if email else None
        password_validation.validate_password(new, user)
        return new

    def clean(self):
        cleaned_data = super(ResetPasswordForm, self).clean()
        new = cleaned_data.get('new_password')
        again = cleaned_data.get('new_password_again')
        if new and again and new != again:
            self.add_error('new_password_again', _('새 비밀번호가 서로 다릅니다.'))
        return cleaned_data


class MigrateForm(_VerifiedEmailForm):
    """기존 사용자 1회 인증.

    비밀번호는 '바꾸는' 것이 아니라 '규칙을 지키는 값으로 다시 정하는' 것이다.
    쓰던 비밀번호가 이미 규칙을 지킨다면 같은 값을 그대로 넣어도 된다 -
    기존 비밀번호와 같은지 검사하지 않는다.
    """

    PURPOSE = 'migrate'

    email = forms.CharField(
        label=_('이메일'),
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email', 'placeholder': _('you@example.com')}))
    new_password = forms.CharField(
        label=_('비밀번호'), min_length=8,
        help_text=_('8자 이상. 영문·숫자·기호를 쓸 수 있고 조합 규칙은 없습니다. 쓰시던 비밀번호가 규칙에 맞으면 그대로 입력하셔도 됩니다.'),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password', 'placeholder': _('8자 이상')}))
    new_password_again = forms.CharField(
        label=_('비밀번호 확인'),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password', 'placeholder': _('한 번 더 입력')}))

    def clean_new_password(self):
        new = self.cleaned_data['new_password']
        password_validation.validate_password(new, self.request.user)
        return new

    def clean(self):
        from iidxrank import accounts
        cleaned_data = super(MigrateForm, self).clean()
        email = cleaned_data.get('email')
        if email and accounts.email_taken(email, exclude_user=self.request.user):
            self.add_error('email', _('이미 다른 계정이 쓰고 있는 이메일입니다.'))
        new = cleaned_data.get('new_password')
        again = cleaned_data.get('new_password_again')
        if new and again and new != again:
            self.add_error('new_password_again', _('비밀번호가 서로 다릅니다.'))
        return cleaned_data
