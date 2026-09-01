# -*- coding: utf-8 -*-
"""비밀번호 검증기.

Django 가 주는 검증기 넷(길이·흔한 비밀번호·전부 숫자·사용자 정보 유사)에
이 파일의 ASCIIPasswordValidator 를 더해 쓴다. settings.AUTH_PASSWORD_VALIDATORS
참조.

주의: Django 는 이 설정을 **자동으로 적용하지 않는다.** 적용해 주는 것은
django.contrib.auth.forms 의 기본 폼들인데, 이 사이트는 폼을 직접 만들어 쓴다.
그래서 iidxrank/forms.py 가 validate_password() 를 직접 부른다. 설정만 넣고
그 호출을 빠뜨리면 아무 일도 일어나지 않는다(실제로 확인했다).
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ASCIIPasswordValidator:
    """비밀번호를 출력 가능한 ASCII 로 제한한다.

    한글 비밀번호를 막는 이유는 약해서가 아니다. 오히려 글자당 정보량은
    한글이 영문의 세 배쯤 된다. 문제는 **되찾기 어렵다**는 것이다.

      - Django 는 비밀번호를 유니코드 정규화하지 않는다(확인함). 같은 '무한궤도'
        라도 NFC 는 코드포인트 4개, NFD 는 9개라 서로 다른 문자열이다. 가입한
        기기와 로그인하는 기기의 IME 가 다른 형태로 조합하면, 같은 글자를 쳐도
        비밀번호가 틀렸다고 나온다.
      - 비밀번호 칸은 가려져 있어 IME 가 한글 상태인지 영문 상태인지 볼 수 없다.
      - 다른 기기·게임기 브라우저에는 한글 IME 가 아예 없을 수 있다.

    정규화(NFKC)를 넣어 허용하는 길도 있지만, 그렇게 하면 이미 한글 비밀번호를
    쓰고 있는 기존 사용자가 잠길 수 있다. 해시만 남아 있어 그런 사용자가
    있는지 확인할 방법도 없다. 그래서 '새로 정하는 비밀번호'만 제한한다.

    이 검증기는 비밀번호를 **설정할 때만** 돈다. 로그인은 검증기를 거치지
    않으므로, 지금 한글 비밀번호를 쓰는 사람이 있어도 로그인은 그대로 된다.

    공백(0x20)은 허용한다. 여러 단어를 이어 쓰는 방식이 길이를 벌기 쉽고,
    NIST 800-63B 도 공백을 막지 말라고 한다.
    """

    # 0x20(공백) ~ 0x7E(~). 제어문자와 ASCII 밖 문자를 모두 뺀다.
    MIN, MAX = 0x20, 0x7E

    def validate(self, password, user=None):
        bad = sorted({c for c in password
                      if not (self.MIN <= ord(c) <= self.MAX)})
        if not bad:
            return
        raise ValidationError(
            _('비밀번호에는 영문·숫자·기호만 쓸 수 있습니다. '
              '한글이나 이모지는 기기에 따라 입력 방식이 달라져 '
              '같은 글자를 쳐도 로그인되지 않을 수 있습니다.'),
            code='password_not_ascii')

    def get_help_text(self):
        return _('영문·숫자·기호만 쓸 수 있습니다.')
