# -*- coding: utf-8 -*-
"""이메일 인증 · 아이디/비밀번호 찾기 · 기존 사용자 1회 인증 화면의 문구.

용어는 기존 카탈로그를 따른다.
  아이디   ID / ID / ID
  이메일   email / メール / 邮箱
  인증 코드 verification code / 認証コード / 验证码

메일 본문은 줄바꿈(\n)을 그대로 옮긴다. 메일은 평문이라 문단 모양이 곧 서식이다.
"""

TRANS = {

# ── 인증 코드 발송·확인 (accounts.py) ────────────────────────────────────
'인증 코드를 보냈습니다. 메일함을 확인해 주세요.': (
    'Verification code sent. Please check your inbox.',
    '認証コードを送信しました。メールをご確認ください。',
    '验证码已发送，请查收邮件。'),

'%(sec)d초 뒤에 다시 보낼 수 있습니다.': (
    'You can request another code in %(sec)d seconds.',
    '%(sec)d 秒後に再送できます。',
    '请在 %(sec)d 秒后再次发送。'),

'먼저 인증 코드를 받아 주세요.': (
    'Request a verification code first.',
    'まず認証コードを受け取ってください。',
    '请先获取验证码。'),

'인증 코드가 만료되었습니다. 다시 받아 주세요.': (
    'The code has expired. Please request a new one.',
    '認証コードの有効期限が切れました。もう一度取得してください。',
    '验证码已过期，请重新获取。'),

'시도 횟수를 넘겼습니다. 인증 코드를 다시 받아 주세요.': (
    'Too many attempts. Please request a new code.',
    '試行回数を超えました。認証コードを取り直してください。',
    '尝试次数过多，请重新获取验证码。'),

'인증 코드가 맞지 않습니다. (%(n)d번 남음)': (
    'That code is not correct. (%(n)d attempts left)',
    '認証コードが正しくありません。（残り %(n)d 回）',
    '验证码不正确。（还可尝试 %(n)d 次）'),

'인증을 시작한 브라우저에서 진행해 주세요.': (
    'Continue in the browser where you started the verification.',
    '認証を開始したブラウザで進めてください。',
    '请在开始验证的浏览器中继续。'),

'이메일 인증이 끝났습니다.': (
    'Email verified.', 'メール認証が完了しました。', '邮箱验证完成。'),

'이메일 주소 형식이 올바르지 않습니다.': (
    'That is not a valid email address.',
    'メールアドレスの形式が正しくありません。',
    '邮箱地址格式不正确。'),

# ── 메일 제목 ────────────────────────────────────────────────────────────
'[beatmania.app] 가입 인증 코드': (
    '[beatmania.app] Sign-up verification code',
    '[beatmania.app] 登録認証コード', '[beatmania.app] 注册验证码'),
'[beatmania.app] 이메일 변경 인증 코드': (
    '[beatmania.app] Email change verification code',
    '[beatmania.app] メールアドレス変更の認証コード',
    '[beatmania.app] 邮箱变更验证码'),
'[beatmania.app] 아이디 찾기 인증 코드': (
    '[beatmania.app] Find-ID verification code',
    '[beatmania.app] ID 確認の認証コード', '[beatmania.app] 找回 ID 验证码'),
'[beatmania.app] 비밀번호 재설정 인증 코드': (
    '[beatmania.app] Password reset verification code',
    '[beatmania.app] パスワード再設定の認証コード',
    '[beatmania.app] 重置密码验证码'),
'[beatmania.app] 계정 인증 코드': (
    '[beatmania.app] Account verification code',
    '[beatmania.app] アカウント認証コード', '[beatmania.app] 账号验证码'),

# ── 메일 본문 ────────────────────────────────────────────────────────────
'아래 인증 코드를 입력해 주세요.\n\n    %(code)s\n\n유효 시간은 %(min)d분입니다.\n\n이 메일은 beatmania.app 의 계정 인증 때문에 발송되었습니다.\n본인이 요청한 것이 아니라면 이 메일을 무시하셔도 됩니다.\n저희는 계정 인증과 아이디·비밀번호 찾기 외의 목적으로는\n메일을 보내지 않습니다.\n': (
    'Enter the verification code below.\n\n'
    '    %(code)s\n\n'
    'It is valid for %(min)d minutes.\n\n'
    'This email was sent for account verification on beatmania.app.\n'
    'If you did not request it, you can ignore this message.\n'
    'We never send email for anything other than account verification\n'
    'and recovering your ID or password.\n',

    '以下の認証コードを入力してください。\n\n'
    '    %(code)s\n\n'
    '有効時間は %(min)d 分です。\n\n'
    'このメールは beatmania.app のアカウント認証のために送信されました。\n'
    'お心当たりがない場合は破棄してください。\n'
    '当サイトはアカウント認証と ID・パスワードの確認以外の目的で\n'
    'メールを送ることはありません。\n',

    '请输入下面的验证码。\n\n'
    '    %(code)s\n\n'
    '有效时间为 %(min)d 分钟。\n\n'
    '本邮件因 beatmania.app 的账号验证而发送。\n'
    '如果不是您本人操作，忽略本邮件即可。\n'
    '除账号验证和找回 ID、密码之外，我们不会因任何其他目的发送邮件。\n'),

# ── 폼 (forms.py) ────────────────────────────────────────────────────────
'이메일 인증을 먼저 끝내 주세요. 주소를 바꾸셨다면 다시 인증해야 합니다.': (
    'Please finish email verification first. If you changed the address, '
    'verify it again.',
    '先にメール認証を完了してください。アドレスを変更した場合は再認証が必要です。',
    '请先完成邮箱验证。若更改了地址，需要重新验证。'),

'이미 다른 계정이 쓰고 있는 이메일입니다.': (
    'Another account is already using that email.',
    'そのメールアドレスは別のアカウントで使われています。',
    '该邮箱已被其他账号使用。'),

'계정 인증과 아이디·비밀번호 찾기에만 씁니다. 인증을 끝내야 가입할 수 있습니다.': (
    'Used only for account verification and recovering your ID or password. '
    'You must verify it to sign up.',
    'アカウント認証と ID・パスワードの確認にのみ使用します。認証を完了すると登録できます。',
    '仅用于账号验证和找回 ID、密码。完成验证后才能注册。'),

'새 이메일': ('New email', '新しいメールアドレス', '新邮箱'),
'가입할 때 쓴 이메일': (
    'The email you signed up with', '登録時のメールアドレス', '注册时使用的邮箱'),

'8자 이상. 영문·숫자·기호를 쓸 수 있고 조합 규칙은 없습니다. 쓰시던 비밀번호가 규칙에 맞으면 그대로 입력하셔도 됩니다.': (
    'At least 8 characters. Letters, digits and symbols; no composition rules. '
    'If your current password already meets this, you may enter it as it is.',
    '8文字以上。英数字と記号が使えます。組み合わせの制約はありません。'
    '今お使いのパスワードが条件を満たしていれば、そのまま入力しても構いません。',
    '至少 8 位。可使用字母、数字和符号，没有组合规则。'
    '如果您当前的密码已符合要求，可以直接输入原密码。'),

# ── 인증 위젯 ────────────────────────────────────────────────────────────
'인증번호 받기': ('Send code', '認証コードを受け取る', '获取验证码'),
'메일로 받은 6자리 숫자': (
    'The 6-digit number from the email', 'メールに届いた 6 桁の数字',
    '邮件中的 6 位数字'),
'확인': ('Verify', '確認', '确认'),

# ── 아이디 찾기 ──────────────────────────────────────────────────────────
'아이디 찾기': ('Find ID', 'ID を確認', '找回 ID'),
'가입할 때 쓴 이메일을 인증하면 아이디를 알려 드립니다.': (
    'Verify the email you signed up with and we will show your ID.',
    '登録時のメールアドレスを認証すると ID をお知らせします。',
    '验证注册时使用的邮箱后即可查看 ID。'),
'이 이메일로 가입된 아이디입니다.': (
    'The ID registered with this email.',
    'このメールアドレスで登録された ID です。', '使用该邮箱注册的 ID。'),
'아이디 확인': ('Show my ID', 'ID を確認する', '查看 ID'),
'로그인하러 가기': ('Go to login', 'ログインへ', '前往登录'),

# ── 비밀번호 재설정 ──────────────────────────────────────────────────────
'비밀번호 재설정': ('Reset password', 'パスワード再設定', '重置密码'),
'가입할 때 쓴 이메일을 인증하면 새 비밀번호를 정할 수 있습니다.': (
    'Verify the email you signed up with to set a new password.',
    '登録時のメールアドレスを認証すると新しいパスワードを設定できます。',
    '验证注册时使用的邮箱后即可设置新密码。'),
'비밀번호를 바꿨습니다. 새 비밀번호로 로그인해 주세요.': (
    'Your password has been changed. Please log in with the new one.',
    'パスワードを変更しました。新しいパスワードでログインしてください。',
    '密码已更改，请使用新密码登录。'),
'비밀번호 바꾸기': ('Change password', 'パスワードを変更', '更改密码'),

# ── 이메일 변경 ──────────────────────────────────────────────────────────
'이메일 변경': ('Change email', 'メールアドレス変更', '更改邮箱'),
'새 이메일을 인증해야 바뀝니다. 지금 주소는 인증하지 않아도 됩니다.': (
    'The change takes effect once the new address is verified. '
    'You do not need to verify your current address.',
    '新しいアドレスを認証すると変更されます。現在のアドレスの認証は不要です。',
    '验证新邮箱后才会变更。当前邮箱无需验证。'),
'지금 등록된 이메일': ('Current email', '現在のメールアドレス', '当前邮箱'),
'이메일 바꾸기': ('Change email', 'メールアドレスを変更', '更改邮箱'),

# ── 기존 사용자 1회 인증 ────────────────────────────────────────────────
'계정 인증': ('Account verification', 'アカウント認証', '账号验证'),
'보안 규정이 바뀌어 계정마다 한 번씩 확인이 필요합니다. 이 화면은 한 번만 나옵니다.': (
    'Our security rules changed, so each account needs a one-time check. '
    'You will see this screen only once.',
    'セキュリティ規定の変更に伴い、アカウントごとに一度だけ確認が必要です。'
    'この画面が表示されるのは一度きりです。',
    '安全规则已更新，每个账号需要进行一次确认。此页面只会出现一次。'),
'무엇을 하나요': ('What this does', 'ここで行うこと', '这一步做什么'),
'이메일 인증 — 아이디·비밀번호를 잊었을 때 되찾는 유일한 수단입니다.': (
    'Email verification - the only way to recover your ID or password later.',
    'メール認証 — ID やパスワードを忘れたときに取り戻す唯一の手段です。',
    '邮箱验证 — 这是日后找回 ID 或密码的唯一方式。'),
'비밀번호를 규정에 맞게 다시 정하기 — <b>꼭 바꾸실 필요는 없습니다.</b> 쓰시던 비밀번호가 규정(8자 이상)에 맞으면 그대로 입력하셔도 됩니다.': (
    'Setting a password that meets the rules - <b>you do not have to change '
    'it.</b> If your current password already meets them (8+ characters), '
    'just enter it again.',
    'パスワードを規定に合わせて設定 — <b>変更する必要はありません。</b>'
    '今お使いのパスワードが規定（8文字以上）を満たしていれば、そのまま入力してください。',
    '设置符合规则的密码 — <b>不一定要更换。</b>'
    '如果当前密码已符合规则（8 位以上），直接再输入一次即可。'),
'이 주소는 다른 계정과 겹치거나 형식이 올바르지 않아 그대로 쓸 수 없습니다. 쓰실 수 있는 다른 주소를 넣어 주세요.': (
    'This address cannot be used as it is - it either collides with another '
    'account or is not a valid address. Please enter one you can use.',
    'このアドレスは他のアカウントと重複しているか形式が正しくないため、'
    'そのままでは使えません。使用できる別のアドレスを入力してください。',
    '该地址与其他账号重复或格式不正确，无法直接使用。请填写可用的其他地址。'),
'인증 마치기': ('Finish verification', '認証を完了する', '完成验证'),
'지금 하지 않으시면 서열표 열람은 되지만 기록 저장·설정은 쓸 수 없습니다.': (
    'Until you do this you can still browse the rank tables, but saving '
    'records and changing settings are unavailable.',
    'これを終えるまで難易度表の閲覧はできますが、記録の保存や設定の変更はできません。',
    '在完成之前仍可浏览难度表，但无法保存记录或修改设置。'),

# ── 기타 ─────────────────────────────────────────────────────────────────
'지금은 이 인증을 진행할 수 없습니다.': (
    'This verification is not available right now.',
    '現在この認証は行えません。', '当前无法进行此验证。'),
# 가입 여부를 알려 주지 않기 위해, 없는 주소여도 같은 문장을 돌려준다.
'가입된 주소라면 인증 코드를 보냈습니다.': (
    'If that address is registered, we have sent a verification code.',
    '登録済みのアドレスであれば認証コードを送信しました。',
    '如果该地址已注册，我们已发送验证码。'),
'아직 계정이 없으신가요?': (
    'No account yet?', 'アカウントをお持ちでないですか？', '还没有账号？'),

'이메일은 계정 인증 및 아이디, 비밀번호 찾기에만 사용됩니다. 그 이외에는 어떤 상황에도 이메일을 사용하거나 임의로 이메일을 발송하지 않습니다. 당연히, 마케팅 메일도 없습니다.': (
    'Your email is used only for account verification and for recovering your '
    'ID or password. We will not use it for anything else, and we will never '
    'send you unsolicited mail. No marketing email, of course.',
    'メールアドレスはアカウント認証と ID・パスワードの確認にのみ使用します。'
    'それ以外の目的で使用することも、無断でメールを送ることもありません。'
    'もちろんマーケティングメールもお送りしません。',
    '邮箱仅用于账号验证以及找回 ID 和密码。除此之外，我们不会将其用于任何其他用途，'
    '也不会擅自发送邮件。当然，也没有营销邮件。'),
}
