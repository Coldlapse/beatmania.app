# -*- coding: utf-8 -*-
"""보안 검토 2-b: 로그인 시도 제한, 인증 메일·코드 한도, 가입 여부를 숨기는 문구."""

TRANS = {

'로그인 시도가 너무 많습니다. %(min)d분 뒤에 다시 시도해 주세요.': (
    'Too many login attempts. Please try again in %(min)d minutes.',
    'ログインの試行回数が多すぎます。%(min)d 分後に再度お試しください。',
    '登录尝试次数过多。请在 %(min)d 分钟后重试。'),

'지금은 인증 메일을 보낼 수 없습니다. 잠시 뒤에 다시 시도해 주세요.': (
    'We cannot send a verification email right now. Please try again later.',
    '現在、認証メールを送信できません。しばらくしてから再度お試しください。',
    '暂时无法发送验证邮件。请稍后再试。'),

'메일을 보내지 못했습니다. 잠시 뒤에 다시 시도해 주세요.': (
    'The email could not be sent. Please try again later.',
    'メールを送信できませんでした。しばらくしてから再度お試しください。',
    '邮件发送失败。请稍后再试。'),

'인증 코드가 맞지 않거나 만료되었습니다. 코드를 요청한 브라우저에서 입력해 주세요.': (
    'The code is incorrect or has expired. Enter it in the browser where you requested it.',
    '認証コードが正しくないか、有効期限が切れています。コードを請求したブラウザで入力してください。',
    '验证码不正确或已过期。请在申请验证码的浏览器中输入。'),

'오늘은 인증 코드를 너무 많이 틀렸습니다. 내일 다시 시도해 주세요.': (
    'Too many incorrect codes today. Please try again tomorrow.',
    '本日は認証コードの誤入力が多すぎます。明日再度お試しください。',
    '今天验证码输入错误次数过多。请明天再试。'),

'가입된 주소라면 인증 코드를 보냈습니다. 메일이 오지 않으면 스팸함을 확인하거나 5분 뒤에 다시 요청해 주세요.': (
    'If this address is registered, we have sent a code. If no email arrives, check your spam folder '
    'or request again in 5 minutes.',
    '登録済みのアドレスであれば認証コードを送信しました。メールが届かない場合は迷惑メールフォルダを'
    '確認するか、5 分後に再度リクエストしてください。',
    '如果该地址已注册，我们已发送验证码。若未收到邮件，请检查垃圾邮件文件夹或在 5 分钟后重新申请。'),

# ── 이미 가입된 주소 안내 메일 (accounts.send_already_registered) ─────────
'[beatmania.app] 이미 가입된 이메일 주소입니다': (
    '[beatmania.app] This email address is already registered',
    '[beatmania.app] このメールアドレスは登録済みです',
    '[beatmania.app] 该邮箱地址已注册'),
'이미 가입된 이메일 주소입니다': (
    'This email address is already registered', 'このメールアドレスは登録済みです', '该邮箱地址已注册'),
'이 이메일 주소로 가입된 beatmania.app 계정이 이미 있습니다.': (
    'A beatmania.app account already exists for this email address.',
    'このメールアドレスで登録された beatmania.app のアカウントがすでにあります。',
    '已有使用此邮箱地址注册的 beatmania.app 账户。'),
'아이디가 기억나지 않으면 로그인 화면의 "아이디 찾기" 를, 비밀번호가 기억나지 않으면 "비밀번호 재설정" 을 이용해 주세요.': (
    'If you forgot your ID, use "Find ID" on the login page; if you forgot your password, use "Reset password".',
    'ID を忘れた場合はログイン画面の「ID を探す」を、パスワードを忘れた場合は「パスワード再設定」をご利用ください。',
    '如果忘记了用户名，请使用登录页面的"找回用户名"；如果忘记了密码，请使用"重置密码"。'),
'이 메일은 beatmania.app 의 계정 인증 때문에 발송되었습니다.\n본인이 요청한 것이 아니라면 이 메일을 무시하셔도 됩니다.\n': (
    'This email was sent for beatmania.app account verification.\nIf you did not request it, you can ignore this email.\n',
    'このメールは beatmania.app のアカウント認証のために送信されました。\nお心当たりがない場合は、このメールを無視してください。\n',
    '此邮件因 beatmania.app 账户验证而发送。\n如果不是您本人的请求，请忽略此邮件。\n'),
}
