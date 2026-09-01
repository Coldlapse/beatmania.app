# -*- coding: utf-8 -*-
"""개인정보처리방침 본문 번역.

법적 성격이 있는 글이라 뜻을 바꾸지 않는다. 한국어 원문이 사실 관계를
스키마에서 확인해 쓴 것이므로, 번역도 그 사실을 그대로 옮긴다.
줄이거나 부드럽게 다듬지 않는다.
"""

TRANS = {

'1. 수집하는 정보': (
    '1. What we collect', '1. 収集する情報', '1. 收集的信息'),
'가입할 때': ('At signup', '登録時', '注册时'),
'아이디 — 공개 프로필 주소가 됩니다. 가입 후 바꿀 수 없습니다.': (
    'ID — becomes your public profile address. Cannot be changed after signup.',
    'ID — 公開プロフィールのアドレスになります。登録後は変更できません。',
    'ID — 会成为公开资料页地址。注册后不可更改。'),
'이메일 주소': ('Email address', 'メールアドレス', '电子邮箱地址'),
'비밀번호 — 원문을 저장하지 않습니다. 되돌릴 수 없는 해시로만 보관하므로 운영자도 알 수 없습니다.': (
    'Password — we never store the original. Only an irreversible hash is kept, so not '
    'even the operator can read it.',
    'パスワード — 平文では保存しません。元に戻せないハッシュのみを保管するため、'
    '運営者にも分かりません。',
    '密码 — 不保存明文。仅保存不可逆的哈希值，因此运营者也无法得知。'),
'서비스를 쓰면서 직접 입력하는 것': (
    'What you enter while using the service', 'サービス利用中に自分で入力するもの',
    '使用服务时你自行输入的内容'),
'IIDX ID, DJ NAME — 계정 설정에서 입력하는 경우에만 저장합니다.': (
    'IIDX ID and DJ NAME — stored only if you enter them in account settings.',
    'IIDX ID、DJ NAME — アカウント設定で入力した場合のみ保存します。',
    'IIDX ID、DJ NAME — 仅在账号设置中输入时才保存。'),
'프로필 사진 — 올리는 경우에만 저장합니다.': (
    'Profile photo — stored only if you upload one.',
    'プロフィール写真 — アップロードした場合のみ保存します。',
    '头像 — 仅在上传时才保存。'),
'플레이 기록 — 서열표에서 곡별로 기록한 클리어 램프와 점수.': (
    'Play records — the clear lamp and score you record per song on the rank tables.',
    'プレイ記録 — 難易度表で曲ごとに記録したクリアランプとスコア。',
    '游玩记录 — 你在难度表上按曲目记录的通关灯与分数。'),
'일일 타건 기록 — 날짜별 타건 수.': (
    'Daily keystrokes — keystroke counts per day.',
    'デイリー打鍵記録 — 日付ごとの打鍵数。',
    '每日打键记录 — 按日期的打键数。'),
'게시판에 글을 쓰는 경우 그 내용과 작성 시각.': (
    'If you post on the board, the content and the time it was written.',
    '掲示板に書き込む場合、その内容と書き込み時刻。',
    '如果在留言板发帖，则包括内容与发布时间。'),
'자동으로 남는 것': ('What is recorded automatically', '自動的に残るもの', '自动留下的记录'),
'접속 IP 주소, 브라우저 정보(User-Agent), 세션 식별자, 접속 시각 — 서열표 조회수를 세기 위해 남습니다. 같은 방문자를 4시간 안에 여러 번 세지 않기 위한 것으로, 이 값으로 개인을 특정하지 않으며 통계 외의 용도로 쓰지 않습니다.': (
    'IP address, browser information (User-Agent), session identifier and access time — '
    'kept in order to count rank table views. They exist so the same visitor is not '
    'counted repeatedly within 4 hours. We do not identify individuals from these values '
    'and do not use them for anything other than statistics.',
    'アクセス元 IP アドレス、ブラウザ情報(User-Agent)、セッション識別子、アクセス時刻 — '
    '難易度表の閲覧数を数えるために残ります。同じ訪問者を 4 時間以内に何度も数えない'
    'ためのもので、これらの値で個人を特定することはなく、統計以外の用途には使いません。',
    '访问 IP 地址、浏览器信息（User-Agent）、会话标识符、访问时间 — 用于统计难度表浏览量。'
    '目的是避免在 4 小时内重复统计同一访客，我们不会用这些值识别个人，也不会用于统计以外的用途。'),
'로그인 상태를 유지하기 위한 세션 정보와 마지막 로그인 시각.': (
    'Session information used to keep you logged in, and your last login time.',
    'ログイン状態を保つためのセッション情報と最終ログイン時刻。',
    '用于保持登录状态的会话信息与最后登录时间。'),
'외부 도구 연동을 쓰는 경우 그 인증 토큰.': (
    'If you use external tool integration, its authentication token.',
    '外部ツール連携を使う場合、その認証トークン。',
    '如果使用外部工具联动，则包括其认证令牌。'),

'2. 무엇에 쓰나': ('2. What we use it for', '2. 何に使うか', '2. 用途'),
'계정 식별과 로그인 유지': (
    'Identifying your account and keeping you logged in',
    'アカウントの識別とログイン状態の維持', '识别账号与保持登录'),
'서열표와 개인 기록 표시': (
    'Showing rank tables and your own records', '難易度表と個人記録の表示',
    '显示难度表与个人记录'),
'서열표별 조회수 집계 (서비스 현황 페이지에 공개)': (
    'Counting views per rank table (shown publicly on the Service Status page)',
    '難易度表ごとの閲覧数の集計（サービス状況ページで公開）',
    '统计各难度表的浏览量（在服务状态页公开）'),
'위 목적 외에는 쓰지 않습니다. 광고에 쓰거나 프로파일링하지 않습니다.': (
    'We use it for nothing beyond the purposes above. No advertising, no profiling.',
    '上記の目的以外には使いません。広告に使ったりプロファイリングしたりしません。',
    '不用于上述目的之外。不用于广告，也不进行用户画像。'),

'3. 무엇이 공개되나': ('3. What is public', '3. 何が公開されるか', '3. 哪些内容会公开'),
'아이디, DJ NAME, 프로필 사진, 플레이 기록은 공개 프로필 주소에서 누구나 볼 수 있습니다. 계정 설정에서 <b>프로필 비공개</b>를 켜면 다른 사람이 볼 수 없습니다.': (
    'Your ID, DJ NAME, profile photo and play records are visible to anyone at your '
    'public profile address. Turn on <b>private profile</b> in account settings and no '
    'one else can see them.',
    'ID、DJ NAME、プロフィール写真、プレイ記録は公開プロフィールのアドレスで誰でも'
    '見られます。アカウント設定で <b>プロフィール非公開</b> をオンにすると他の人は'
    '見られません。',
    'ID、DJ NAME、头像与游玩记录，任何人都可在你的公开资料页看到。'
    '在账号设置中开启<b>资料不公开</b>后，其他人将无法查看。'),
'이메일 주소와 접속 IP는 어떤 경우에도 공개되지 않습니다.': (
    'Your email address and IP address are never made public.',
    'メールアドレスとアクセス元 IP はいかなる場合も公開されません。',
    '电子邮箱地址与访问 IP 在任何情况下都不会公开。'),

'4. 제3자 제공과 외부 서비스': (
    '4. Third parties and external services', '4. 第三者提供と外部サービス',
    '4. 第三方提供与外部服务'),
'수집한 정보를 다른 곳에 팔거나 넘기지 않습니다.': (
    'We do not sell or hand over collected information to anyone.',
    '収集した情報を他所に売ったり渡したりしません。',
    '不会将收集的信息出售或转交他人。'),
'다만 가입 화면에서 자동 가입을 막기 위해 Google reCAPTCHA를 씁니다. 이때 Google이 자체 정책에 따라 접속 정보를 처리합니다. 이 사이트는 그 과정에서 어떤 정보도 따로 받지 않습니다.': (
    'The signup screen does use Google reCAPTCHA to block automated registrations. '
    'Google processes access information there under its own policy. This site receives '
    'no information of its own from that process.',
    'ただし登録画面では自動登録を防ぐため Google reCAPTCHA を使います。その際 Google が'
    '自社のポリシーに従ってアクセス情報を処理します。当サイトはその過程で情報を'
    '受け取ることはありません。',
    '但注册页面会使用 Google reCAPTCHA 来阻止自动注册。此时 Google 会依其自身政策处理访问信息。'
    '本站在该过程中不会另行获取任何信息。'),

'5. 얼마나 보관하나': ('5. How long we keep it', '5. どのくらい保管するか', '5. 保存多久'),
'계정과 그에 딸린 기록은 탈퇴할 때까지 보관하고, 탈퇴하면 함께 지웁니다.': (
    'Your account and its records are kept until you delete the account, and are '
    'removed with it.',
    'アカウントとそれに紐づく記録は退会するまで保管し、退会と同時に削除します。',
    '账号及其相关记录保存至注销为止，注销时一并删除。'),
'조회 기록은 서열표별 통계를 위해 기간 제한 없이 보관합니다.': (
    'View records are kept without a time limit for per-table statistics.',
    '閲覧記録は難易度表ごとの統計のため、期限を定めず保管します。',
    '浏览记录为各难度表统计之用，无期限保存。'),
'세션 정보는 만료되면 사라집니다.': (
    'Session information disappears when it expires.',
    'セッション情報は有効期限が切れると消えます。', '会话信息在过期后消失。'),

'6. 이용자의 권리': ('6. Your rights', '6. 利用者の権利', '6. 用户的权利'),
'자신의 정보는 <a href="/account/">계정 설정</a>에서 언제든 보고 고칠 수 있습니다.': (
    'You can view and edit your information at any time in '
    '<a href="/account/">account settings</a>.',
    '自分の情報は<a href="/account/">アカウント設定</a>でいつでも確認・修正できます。',
    '你可以随时在<a href="/account/">账号设置</a>中查看和修改自己的信息。'),
'계정 삭제(탈퇴)도 <a href="/account/">계정 설정</a>에서 직접 할 수 있습니다.': (
    'You can also delete your account yourself in '
    '<a href="/account/">account settings</a>.',
    'アカウントの削除(退会)も<a href="/account/">アカウント設定</a>から自分で行えます。',
    '注销账号也可在<a href="/account/">账号设置</a>中自行完成。'),
'프로필 공개 여부는 언제든 바꿀 수 있습니다.': (
    'You can change whether your profile is public at any time.',
    'プロフィールの公開・非公開はいつでも変更できます。',
    '资料是否公开可随时更改。'),

'7. 보호를 위해 하는 것': (
    '7. How we protect it', '7. 保護のために行っていること', '7. 我们采取的保护措施'),
'비밀번호는 되돌릴 수 없는 해시로만 저장합니다.': (
    'Passwords are stored only as an irreversible hash.',
    'パスワードは元に戻せないハッシュのみで保存します。', '密码仅以不可逆的哈希值保存。'),
'사이트 전체를 HTTPS로 제공합니다.': (
    'The whole site is served over HTTPS.', 'サイト全体を HTTPS で提供します。',
    '整站通过 HTTPS 提供。'),
'이 사이트는 신용카드 정보나 주민등록번호 같은 정보를 받지 않으며, 저장할 자리도 두지 않았습니다.': (
    'This site does not accept things like credit card numbers or national ID numbers, '
    'and has no place to store them.',
    '当サイトはクレジットカード情報や住民登録番号のような情報を受け取らず、'
    '保存する場所も設けていません。',
    '本站不接收信用卡信息或身份证号一类的信息，也没有设置存储它们的位置。'),

'8. 문의': ('8. Contact', '8. お問い合わせ', '8. 联系方式'),
'개인정보와 관련한 문의는 <a href="https://discord.gg/RxjwbvWa8D" target="_blank" rel="noopener">디스코드</a>로 연락해 주세요.': (
    'For privacy enquiries please contact us on '
    '<a href="https://discord.gg/RxjwbvWa8D" target="_blank" rel="noopener">Discord</a>.',
    '個人情報に関するお問い合わせは'
    '<a href="https://discord.gg/RxjwbvWa8D" target="_blank" rel="noopener">Discord</a>'
    'までご連絡ください。',
    '与个人信息相关的咨询请通过'
    '<a href="https://discord.gg/RxjwbvWa8D" target="_blank" rel="noopener">Discord</a>联系。'),
'이 방침이 바뀌면 이 페이지에서 알립니다.': (
    'If this policy changes we will announce it on this page.',
    'この方針が変わった場合はこのページでお知らせします。',
    '若本政策发生变更，将在本页面公告。'),
'최종 수정일': ('Last updated', '最終更新日', '最后更新日期'),
'beatmania.app(이하 \'이 사이트\')은 IIDX INFINITAS 서열표를 제공하는 개인 운영 사이트입니다. 아래는 이 사이트가 실제로 저장하고 사용하는 정보의 전부입니다.': (
    "beatmania.app (“this site”) is a personally operated site providing IIDX "
    'INFINITAS rank tables. Below is everything this site actually stores and uses.',
    'beatmania.app（以下「当サイト」）は IIDX INFINITAS の難易度表を提供する個人運営の'
    'サイトです。以下は当サイトが実際に保存し利用する情報のすべてです。',
    'beatmania.app（以下称“本站”）是提供 IIDX INFINITAS 难度表的个人运营站点。'
    '以下是本站实际存储并使用的全部信息。'),
}
