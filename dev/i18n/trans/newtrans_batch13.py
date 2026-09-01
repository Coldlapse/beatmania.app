# -*- coding: utf-8 -*-
"""비밀번호 검증기(8자 + ASCII 제한)를 넣으면서 생긴 문구.

Django 기본 검증기 넷의 메시지는 Django 가 네 언어를 이미 들고 있어
여기에 넣지 않는다. 우리가 새로 만든 문구만 담는다.

한글을 막는 이유를 '보안' 이 아니라 '로그인이 안 될 수 있음' 으로 쓴다.
실제 이유가 그렇고, 사용자에게도 그렇게 말해야 납득이 된다.
"""

TRANS = {

'8자 이상': ('8 or more characters', '8文字以上', '8 位以上'),

'8자 이상. 영문·숫자·기호를 쓸 수 있고 조합 규칙은 없습니다.': (
    'At least 8 characters. Letters, digits and symbols; no composition rules.',
    '8文字以上。英数字と記号が使えます。組み合わせの制約はありません。',
    '至少 8 位。可使用字母、数字和符号，没有组合规则。'),

'비밀번호에는 영문·숫자·기호만 쓸 수 있습니다. 한글이나 이모지는 기기에 따라 입력 방식이 달라져 같은 글자를 쳐도 로그인되지 않을 수 있습니다.': (
    'Passwords can use letters, digits and symbols only. Characters outside '
    'that range are entered differently depending on the device, so the same '
    'characters may not log you back in.',
    'パスワードに使えるのは英数字と記号のみです。それ以外の文字は端末によって'
    '入力方式が変わるため、同じ文字を入力してもログインできないことがあります。',
    '密码只能使用字母、数字和符号。其他字符在不同设备上的输入方式不同，'
    '即使输入相同的字符也可能无法登录。'),

'영문·숫자·기호만 쓸 수 있습니다.': (
    'Letters, digits and symbols only.',
    '英数字と記号のみ使えます。',
    '只能使用字母、数字和符号。'),
}
