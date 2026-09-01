#-*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
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
            help_text=_('회원가입 외 다른 용도로 사용하지 않습니다.'),
            widget=forms.EmailInput(attrs={
                'autocomplete': 'email', 'placeholder': _('you@example.com')}))
    password = forms.CharField(
            label=_('비밀번호'), min_length=4,
            widget=forms.PasswordInput(attrs={
                'autocomplete': 'new-password', 'placeholder': _('4자 이상')}))
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
    captcha = ReCaptchaField(label='')

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
        cleaned_data = super(JoinForm, self).clean()
        username = self.data['id']
        user = User.objects.filter(username=username).first()
        if (user != None):
            raise forms.ValidationError('%s is already exists' % username)
        if (self.data['password'] != self.data['password_again']):
            raise forms.ValidationError('Password does not match!')

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
    new_password = forms.CharField(
            label=_('새 비밀번호'), min_length=4,
            widget=forms.PasswordInput(attrs={
                'autocomplete': 'new-password', 'autofocus': True,
                'placeholder': _('4자 이상')}))
    new_password_again = forms.CharField(
            label=_('새 비밀번호 확인'),
            widget=forms.PasswordInput(attrs={
                'autocomplete': 'new-password', 'placeholder': _('한 번 더 입력')}))

    def clean(self):
        if (self.data['new_password'] != self.data['new_password_again']):
            raise forms.ValidationError('Password does not match!')

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
        if (self.data['password'] != self.data['password_again']):
            raise forms.ValidationError('Password does not match!')
        user = authenticate(username=self.data['id'], password=self.data['password'])
        if (user==None):
            raise forms.ValidationError('ID or Password does not exists.')


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
