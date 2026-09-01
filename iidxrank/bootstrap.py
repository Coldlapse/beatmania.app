# -*- coding: utf-8 -*-
"""django-bootstrap5 렌더러 조정.

두 가지를 바꾼다. 둘 다 "화면이 사실과 다른 말을 하는" 경우다.

1) 오류 없는 칸에 붙는 초록 체크(`is-valid`)를 뺀다.

   기본 렌더러는 폼이 bound 이기만 하면 오류가 없는 칸에 전부 `is-valid` 를
   붙인다. 그런데 비밀번호 위젯은 보안상 값을 다시 그리지 않는다. 그래서
   가입이 실패해 화면이 다시 그려지면

       <input name="password" class="form-control is-valid" value="">

   빈 칸에 "맞았습니다" 표시가 남는다. 사용자는 이미 채워진 것으로 읽고
   캡차만 풀고 다시 눌렀다가 또 실패한다.

   빨강(`is-invalid`)은 남긴다. 어느 칸이 잘못됐는지 알려 주는 정보는 맞다.

2) 서버가 그린 오류 문구는 항상 보이게 한다.

   Bootstrap 의 `.invalid-feedback` 은 `display:none` 이고, 형제 요소에
   `.is-invalid` 가 있을 때만 나타난다. 그 규칙은 마크업을 미리 그려 두고
   자바스크립트로 검사하는 흐름을 전제한다. 우리는 서버에서 오류가 있을 때만
   그 문구를 그리므로, 그려졌다는 것 자체가 "보여야 한다" 는 뜻이다.

   실제로 문제가 됐던 곳은 reCAPTCHA 다. django-recaptcha 의 위젯 템플릿이
   class 속성을 두 번 낸다.

       <div class="g-recaptcha"  ...  class="is-invalid"  ...>

   HTML 은 첫 번째 class 만 적용하므로 브라우저는 is-invalid 를 보지 못하고,
   오류 문구는 DOM 에 있는데 화면에는 없었다(실측). 캡차를 안 풀고 가입을
   누르면 "그냥 새로고침됐다" 로 보이던 원인이 이것이다.

   위젯 종류나 렌더 결과의 문자열로 판별해 보려 했지만 둘 다 이 중복 속성에
   속는다. 조건을 두지 않는 편이 단순하고, 서버 렌더에서는 언제나 옳다.
"""

from django.utils.safestring import mark_safe
from django_bootstrap5.renderers import FieldRenderer as BaseFieldRenderer


class FieldRenderer(BaseFieldRenderer):
    def get_server_side_validation_classes(self):
        if self.field_errors:
            return "is-invalid"
        return ""

    def render(self):
        html = super().render()
        if not self.field_errors:
            return html
        # 서버가 오류 문구를 그렸다는 것은 곧 보여야 한다는 뜻이다.
        # d-block 이 붙어도 이미 보이던 문구의 모양은 달라지지 않는다.
        #
        # mark_safe 를 반드시 다시 씌운다. super().render() 는 SafeString 을
        # 주는데 .replace() 를 거치면 평범한 str 이 되고, 그러면 템플릿이 폼
        # 전체를 이스케이프해 HTML 이 글자로 그대로 화면에 뿌려진다(겪었다).
        return mark_safe(html.replace(
            'class="invalid-feedback"', 'class="invalid-feedback d-block"'))
