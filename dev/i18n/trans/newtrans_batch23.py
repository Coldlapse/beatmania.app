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

# ── 이메일 변경 알림 (accounts.send_email_changed_notice) ─────────────────
TRANS.update({
'[beatmania.app] 이메일 주소가 변경되었습니다': (
    '[beatmania.app] Your email address was changed',
    '[beatmania.app] メールアドレスが変更されました',
    '[beatmania.app] 您的邮箱地址已更改'),
'이메일 주소가 변경되었습니다': (
    'Your email address was changed', 'メールアドレスが変更されました', '您的邮箱地址已更改'),
'계정 %(id)s 의 이메일 주소가 %(new)s 로 변경되었습니다.': (
    'The email address of account %(id)s was changed to %(new)s.',
    'アカウント %(id)s のメールアドレスが %(new)s に変更されました。',
    '账户 %(id)s 的邮箱地址已更改为 %(new)s。'),
'본인이 변경한 것이 아니라면 사이트 디스코드로 운영자에게 바로 알려 주세요.': (
    'If you did not make this change, please tell the operator on the site Discord right away.',
    'ご自身で変更していない場合は、サイトの Discord で運営者にすぐお知らせください。',
    '如果不是您本人更改的，请立即在网站的 Discord 告知管理员。'),
})

# ── 403 화면 (templates/403.html) ─────────────────────────────────────────
TRANS.update({
'접근할 수 없음': ('Access denied', 'アクセスできません', '无法访问'),
'이 페이지에 접근할 수 없습니다': ('You cannot access this page', 'このページにはアクセスできません', '您无法访问此页面'),
'이 계정으로는 쓸 수 없는 기능입니다.': (
    'This feature is not available for this account.', 'このアカウントでは使えない機能です。', '此账户无法使用该功能。'),
})

# ── 공유 상자 (widgets/share_box.html) ───────────────────────────────────
TRANS.update({
'공유 주소': ('Share link', '共有アドレス', '分享链接'),
'클립보드에 복사': ('Copy to clipboard', 'クリップボードにコピー', '复制到剪贴板'),
})

# ── 연동 앱 받기·사용법 (widgets/app_guide.html) ─────────────────────────
TRANS.update({
'최신 버전 받기': ('Download latest', '最新版をダウンロード', '下载最新版'),
'최신 버전(2.1.0 이상)을 받아 설치합니다.': (
    'Download and install the latest version (2.1.0 or later).',
    '最新版(2.1.0 以上)をダウンロードしてインストールします。',
    '下载并安装最新版（2.1.0 及以上）。'),
'프로그램 설정에 <a href="%(token_url)s">API 토큰</a>을 넣고 저장합니다.': (
    'Enter your <a href="%(token_url)s">API token</a> in the program settings and save.',
    'プログラムの設定に <a href="%(token_url)s">API トークン</a> を入力して保存します。',
    '在程序设置中填入 <a href="%(token_url)s">API 令牌</a> 并保存。'),
'켜 두면 타건 수가 자동으로 올라가고, <a href="%(mypage_url)s">일일 타건 기록</a>에서 볼 수 있습니다.': (
    'Keep it running and your key count is sent automatically; see it in <a href="%(mypage_url)s">Daily keystrokes</a>.',
    '起動しておくと打鍵数が自動で送信され、<a href="%(mypage_url)s">日別打鍵記録</a>で確認できます。',
    '保持运行即可自动上传击键数，可在<a href="%(mypage_url)s">每日击键记录</a>中查看。'),
'INFINITAS 를 켜 둔 동안 트레이에 머물며, 기록이 바뀌면 클리어 램프·DJ RANK·EX SCORE 를 서열표에 자동으로 반영합니다.': (
    'Stays in the tray while INFINITAS is running and applies clear lamps, DJ RANK and EX SCORE to your rank tables whenever your records change.',
    'INFINITAS の起動中はトレイに常駐し、記録が変わるとクリアランプ・DJ RANK・EX SCORE を序列表に自動で反映します。',
    '在 INFINITAS 运行期间常驻托盘，记录变化时自动将通关灯、DJ RANK、EX SCORE 同步到难度表。'),
'최신 버전을 받아 설치합니다. 처음 실행할 때 "Windows에서 PC를 보호했습니다" 가 뜨면 추가 정보 → 실행을 누릅니다.': (
    'Download and install the latest version. If "Windows protected your PC" appears on first launch, click More info → Run anyway.',
    '最新版をダウンロードしてインストールします。初回起動時に「Windows によって PC が保護されました」と表示されたら、詳細情報 → 実行 を押してください。',
    '下载并安装最新版。首次运行若出现"Windows 已保护你的电脑"，请点击"更多信息"→"仍要运行"。'),
'앱의 API 토큰 칸에 <a href="%(token_url)s">API 토큰</a>을 넣습니다.': (
    'Enter your <a href="%(token_url)s">API token</a> in the app.',
    'アプリの API トークン欄に <a href="%(token_url)s">API トークン</a> を入力します。',
    '在应用的 API 令牌栏中填入 <a href="%(token_url)s">API 令牌</a>。'),
'게임을 켜고 곡 선택 화면에 한 번 들어가면 기록이 올라갑니다. INF오소리를 쓰고 있다면 그대로 두셔도 됩니다.': (
    'Start the game and enter the song select screen once to upload your records. If you use INFOhSorry, you can keep using it as is.',
    'ゲームを起動して選曲画面に一度入ると記録が送信されます。INFOhSorry をお使いの場合もそのままで構いません。',
    '启动游戏并进入一次选曲画面即可上传记录。如果正在使用 INFOhSorry，保持原样即可。'),
})

TRANS.update({
'IIDX/BMS 스트리밍용 타건 비주얼라이저 위젯입니다. 이 위젯 프로그램에서 카운팅된 타건 횟수를 beatmania.app 에 기록할 수 있습니다.': (
    'A key-press visualizer widget for IIDX/BMS streaming. The key presses it counts can be recorded on beatmania.app.',
    'IIDX/BMS 配信用の打鍵ビジュアライザーウィジェットです。このウィジェットで数えた打鍵数を beatmania.app に記録できます。',
    '用于 IIDX/BMS 直播的击键可视化小组件。可以将该小组件统计的击键次数记录到 beatmania.app。'),
})

TRANS.update({
'게임을 켜고 곡 선택 화면에 한 번 들어가면 기록이 올라갑니다. INF오소리와 동시 실행이 가능하며, 충돌이 일어나지 않게끔 설계했습니다.': (
    'Start the game and enter the song select screen once to upload your records. It can run alongside INFOhSorry and is designed not to conflict with it.',
    'ゲームを起動して選曲画面に一度入ると記録が送信されます。INFOhSorry と同時に起動でき、競合しないよう設計しています。',
    '启动游戏并进入一次选曲画面即可上传记录。可与 INFOhSorry 同时运行，并已设计为不会发生冲突。'),
})
