# -*- coding: utf-8 -*-
"""인증 메일을 HTML 로 다시 만들면서 생긴 문구.

메일 맨 위의 한 줄(heading)은 "무엇 때문에 온 메일인지" 를 알리는 자리다.
제목과 겹치지 않게, 사용자가 지금 하던 일을 이어 주는 말로 쓴다.
"""

TRANS = {

# ── 메일 첫 줄 ──────────────────────────────────────────────────────────
'회원가입을 마무리해 주세요': (
    'Finish creating your account', '会員登録を完了してください', '完成注册'),

'새 이메일 주소를 확인해 주세요': (
    'Confirm your new email address',
    '新しいメールアドレスをご確認ください', '确认您的新邮箱'),

'아이디를 확인하시려면': (
    'To see your ID', 'ID を確認するには', '要查看您的 ID'),

'비밀번호를 재설정하시려면': (
    'To reset your password', 'パスワードを再設定するには', '要重置密码'),

'계정 인증을 진행해 주세요': (
    'Please verify your account', 'アカウント認証を進めてください', '请完成账号验证'),

# ── 메일 본문 (HTML) ────────────────────────────────────────────────────
'아래 인증 코드를 입력해 주세요.': (
    'Enter the verification code below.',
    '以下の認証コードを入力してください。', '请输入下面的验证码。'),

'유효 시간은 %(min)s분입니다.': (
    'Valid for %(min)s minutes.', '有効時間は %(min)s 分です。',
    '有效时间为 %(min)s 分钟。'),

'이 메일은 beatmania.app 의 계정 인증 때문에 발송되었습니다. 본인이 요청한 것이 아니라면 이 메일을 무시하셔도 됩니다.': (
    'This email was sent for account verification on beatmania.app. '
    'If you did not request it, you can ignore this message.',
    'このメールは beatmania.app のアカウント認証のために送信されました。'
    'お心当たりがない場合は破棄してください。',
    '本邮件因 beatmania.app 的账号验证而发送。如果不是您本人操作，忽略本邮件即可。'),

'저희는 계정 인증과 아이디·비밀번호 찾기 외의 목적으로는 메일을 보내지 않습니다. 마케팅 메일도 보내지 않습니다.': (
    'We never send email for anything other than account verification and '
    'recovering your ID or password. No marketing email either.',
    '当サイトはアカウント認証と ID・パスワードの確認以外の目的でメールを'
    '送ることはありません。マーケティングメールもお送りしません。',
    '除账号验证和找回 ID、密码之外，我们不会因其他目的发送邮件，也没有营销邮件。'),
}
