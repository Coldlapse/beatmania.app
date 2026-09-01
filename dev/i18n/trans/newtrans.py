# -*- coding: utf-8 -*-
"""새로 만든 화면들의 번역.

영어/일본어/중국어(간체) 세 벌. 한국어는 원문이므로 카탈로그에 넣지 않는다.

용어를 화면마다 다르게 옮기지 않도록 아래를 지킨다.
  서열표      rank table / 難易度表 / 难度表
  타건        keystroke / 打鍵 / 打键
  채보        chart / 譜面 / 谱面
  사이트뷰    site views / サイトビュー / 站点访问
  토큰        token / トークン / 令牌
"""

TRANS = {

# ── 공통 / 푸터 ───────────────────────────────────────────────────────────
'개인정보처리방침': (
    'Privacy Policy', 'プライバシーポリシー', '隐私政策'),
'<a href="%(kuna)s" target="_blank" rel="noopener">@lazykuna</a> 님의 iidxranktable 레포를 클론하여 만들어졌습니다.<br>SP 난이도표 관리 : <a href="%(cold)s" target="_blank" rel="noopener">@Coldlapse</a>, DP 난이도표 관리 : P.': (
    'Built by cloning the iidxranktable repository by '
    '<a href="%(kuna)s" target="_blank" rel="noopener">@lazykuna</a>.<br>'
    'SP tables: <a href="%(cold)s" target="_blank" rel="noopener">@Coldlapse</a>, DP tables: P.',
    '<a href="%(kuna)s" target="_blank" rel="noopener">@lazykuna</a> 氏の '
    'iidxranktable リポジトリをクローンして作られました。<br>'
    'SP 難易度表担当 : <a href="%(cold)s" target="_blank" rel="noopener">@Coldlapse</a>、DP 難易度表担当 : P.',
    '基于 <a href="%(kuna)s" target="_blank" rel="noopener">@lazykuna</a> 的 '
    'iidxranktable 仓库克隆制作。<br>'
    'SP 难度表维护 : <a href="%(cold)s" target="_blank" rel="noopener">@Coldlapse</a>，DP 难度表维护 : P.'),

# ── 상단바 ────────────────────────────────────────────────────────────────
'서비스 현황': ('Service Status', 'サービス状況', '服务状态'),
'데이터 동기화': ('Data Sync', 'データ同期', '数据同步'),
'데이터 동기화 프로그램': (
    'the data sync program', 'データ同期プログラム', '数据同步程序'),
'프로젝트 소개': ('About', 'プロジェクト紹介', '项目介绍'),
'API 토큰': ('API Token', 'API トークン', 'API 令牌'),
'개발자에게 커피 사주기': (
    'Buy the developer a coffee', '開発者にコーヒーをおごる', '请开发者喝杯咖啡'),

# ── 서비스 현황 ───────────────────────────────────────────────────────────
'사이트뷰': ('Site views', 'サイトビュー', '站点访问'),
'사이트뷰 추이': ('Site view trend', 'サイトビューの推移', '站点访问趋势'),
'같은 방문자가 여러 서열표를 봐도 한 번으로 셉니다': (
    'One visitor counts once, even across several rank tables',
    '同じ訪問者が複数の難易度表を見ても 1 回として数えます',
    '同一访客浏览多个难度表也只计一次'),
'서열표 조회수': ('Rank table views', '難易度表の閲覧数', '难度表浏览量'),
'서열표 조회수 추이': (
    'Rank table view trend', '難易度表 閲覧数の推移', '难度表浏览量趋势'),
'플레이 모드': ('Play mode', 'プレイモード', '游戏模式'),
'해당 기간에 조회된 기록이 없습니다.': (
    'No views in this period.', 'この期間の閲覧記録はありません。', '该时间段内没有浏览记录。'),
'조회수를 불러오지 못했습니다.': (
    'Could not load view counts.', '閲覧数を読み込めませんでした。', '无法加载浏览量。'),
'합계': ('Total', '合計', '合计'),
'beatmania.app 은 %(phrase)s <b>%(n)s</b> 번의 방문을 기록했습니다.': (
    'beatmania.app recorded <b>%(n)s</b> visits %(phrase)s.',
    'beatmania.app は%(phrase)s <b>%(n)s</b> 回の訪問を記録しました。',
    'beatmania.app %(phrase)s记录了 <b>%(n)s</b> 次访问。'),
'상태 점검': ('Status checks', 'ステータス確認', '状态检查'),
'기록 없음': ('No data', '記録なし', '无记录'),
'가동 이력': ('Uptime history', '稼働履歴', '运行历史'),
'(외부 점검기: 준비 중)': (
    '(External checker: coming soon)', '（外部チェッカー: 準備中）', '（外部检查器：准备中）'),
'최근 %(h)s시간 · %(m)s분마다 점검': (
    'Last %(h)sh · checked every %(m)s min',
    '直近 %(h)s 時間・%(m)s 分ごとに確認',
    '最近 %(h)s 小时 · 每 %(m)s 分钟检查'),
'%(when)s 전 점검': (
    'checked %(when)s ago', '%(when)s前に確認', '%(when)s前检查'),
'beatmania.app 에는 <b>%(users)s명</b>의 유저가 있고, 그중 <b>%(players)s명</b>이 지금까지 <b>%(records)s개</b>의 플레이 기록을 남겼습니다.<br>등록된 채보는 <b>%(songs)s개</b>이며, <b>%(tables)s개</b>의 서열표가 있습니다.': (
    'beatmania.app has <b>%(users)s</b> users, and <b>%(players)s</b> of them have '
    'left <b>%(records)s</b> play records so far.<br>'
    '<b>%(songs)s</b> charts are registered across <b>%(tables)s</b> rank tables.',
    'beatmania.app には <b>%(users)s人</b>のユーザーがいて、そのうち <b>%(players)s人</b>が'
    'これまでに <b>%(records)s件</b>のプレイ記録を残しました。<br>'
    '登録された譜面は <b>%(songs)s件</b>、難易度表は <b>%(tables)s個</b>です。',
    'beatmania.app 有 <b>%(users)s</b> 位用户，其中 <b>%(players)s</b> 位至今留下了 '
    '<b>%(records)s</b> 条游玩记录。<br>'
    '已登录谱面 <b>%(songs)s</b> 个，难度表 <b>%(tables)s</b> 个。'),
'이 점검은 beatmania.app 안에서 스스로를 확인한 결과입니다. 사이트 자체가 내려가면 이 페이지도 열리지 않으므로, 바깥에서 같은 항목을 확인하는 점검기를 따로 둘 예정입니다.': (
    'These checks run inside beatmania.app itself. If the site goes down this page '
    'will not open either, so a separate external checker is planned.',
    'この確認は beatmania.app 自身が内部で行った結果です。サイト自体が落ちればこの'
    'ページも開けないため、外部から同じ項目を確認するチェッカーを別途用意する予定です。',
    '此检查是 beatmania.app 内部自我确认的结果。若站点本身宕机，本页面也无法打开，'
    '因此计划另设从外部检查相同项目的检查器。'),

# 상태 점검 항목 (health.py)
'웹 서비스': ('Web service', 'ウェブサービス', '网页服务'),
'데이터베이스': ('Database', 'データベース', '数据库'),
'textage.cc (수록곡 출처)': (
    'textage.cc (song source)', 'textage.cc（楽曲データ元）', 'textage.cc（曲目来源）'),
'Google Sheets (서열표 출처)': (
    'Google Sheets (rank table source)', 'Google Sheets（難易度表データ元）',
    'Google Sheets（难度表来源）'),
'이 페이지를 그려 주는 서버가 요청을 처리하고 있는지.': (
    'Whether the server rendering this page is handling requests.',
    'このページを返すサーバーがリクエストを処理できているか。',
    '渲染此页面的服务器是否正在处理请求。'),
'데이터베이스에 질의가 되는지.': (
    'Whether the database answers queries.',
    'データベースに問い合わせができるか。', '数据库能否响应查询。'),
'수록곡을 긁어 오는 페이지에 닿는지. 내려받아 표식까지 확인한다.': (
    'Whether the song source page is reachable. We fetch it and check for a marker.',
    '楽曲データを取得するページに到達できるか。取得して目印まで確認する。',
    '能否访问抓取曲目的页面。会下载并检查标记。'),
'서열표를 긁어 오는 시트에 닿는지. 내려받아 표식까지 확인한다.': (
    'Whether the rank table sheet is reachable. We fetch it and check for a marker.',
    '難易度表を取得するシートに到達できるか。取得して目印まで確認する。',
    '能否访问抓取难度表的表格。会下载并检查标记。'),

# ── 일일 타건 기록 ────────────────────────────────────────────────────────
'내 기록': ('My records', '自分の記録', '我的记录'),
'기간': ('Period', '期間', '时间段'),
'30일': ('30 days', '30日', '30 天'),
'90일': ('90 days', '90日', '90 天'),
'1년': ('1 year', '1年', '1 年'),
'전체': ('All time', '全期間', '全部'),
'기록한 날': ('Days logged', '記録した日数', '记录天数'),
'마지막 기록': ('Last record', '最後の記録', '最后记录'),
'일별 타건 수': ('Keystrokes per day', '日別の打鍵数', '每日打键数'),
'타건 수': ('Keystrokes', '打鍵数', '打键数'),
'아직 기록이 없습니다. IIDXwidget 을 연결하면 여기에 쌓입니다.': (
    'No records yet. Connect IIDXwidget and they will show up here.',
    'まだ記録がありません。IIDXwidget を connect すればここに溜まります。',
    '还没有记录。连接 IIDXwidget 后会显示在这里。'),
'API 토큰 발급': ('Get an API token', 'API トークンを発行', '获取 API 令牌'),
'내 기록은 로그인해야 볼 수 있습니다': (
    'Log in to see your own records', '自分の記録はログインすると見られます',
    '登录后可查看自己的记录'),
'가입하고 IIDXwidget 을 연결하면 하루에 몇 번 쳤는지가 여기에 쌓이고, 아래 순위에도 오릅니다.': (
    'Sign up and connect IIDXwidget, and your daily keystrokes will collect here '
    'and appear in the ranking below.',
    '登録して IIDXwidget を連携すると、1 日に何回叩いたかがここに溜まり、'
    '下のランキングにも載ります。',
    '注册并连接 IIDXwidget 后，每天的打键数会累积在这里，也会出现在下方排行榜中。'),
'beatmania.app 건실 랭킹': (
    'beatmania.app Diligence Ranking', 'beatmania.app 精勤ランキング',
    'beatmania.app 勤奋排行榜'),
'프로필을 비공개로 설정한 분은 순위에서 제외됩니다': (
    'Users with a private profile are excluded from the ranking',
    'プロフィールを非公開にしている方はランキングから除外されます',
    '将资料设为不公开的用户不计入排行榜'),
'해당 기간에 기록이 없습니다.': (
    'No records in this period.', 'この期間の記録はありません。', '该时间段内没有记录。'),
'최근': ('Last', '直近', '最近'),
'일에는 기록이 없습니다. 기간을 늘려 보세요.': (
    ' days have no records. Try a longer period.',
    '日間の記録はありません。期間を広げてみてください。',
    ' 天没有记录。请尝试更长的时间段。'),
'내 순위는 %(of)s명 중 <b>%(rank)s위</b>입니다. (%(phrase)s %(total)s타)': (
    'You are <b>#%(rank)s</b> of %(of)s. (%(total)s keystrokes %(phrase)s)',
    'あなたは %(of)s人中 <b>%(rank)s位</b>です。(%(phrase)s %(total)s 打鍵)',
    '你在 %(of)s 人中排名 <b>第 %(rank)s 位</b>。（%(phrase)s %(total)s 打键）'),
'프로필을 비공개로 두어 순위에 오르지 않습니다. 내 기록은 %(phrase)s <b>%(total)s타</b>입니다.': (
    'Your profile is private, so you are not listed. Your own total is '
    '<b>%(total)s</b> keystrokes %(phrase)s.',
    'プロフィールが非公開のためランキングには載りません。あなたの記録は '
    '%(phrase)s <b>%(total)s 打鍵</b>です。',
    '你的资料为不公开，因此不会出现在排行榜。你的记录为 %(phrase)s <b>%(total)s 打键</b>。'),

# 기간 문구 (views_typing.PERIODS)
'지난 1년': ('Last year', '直近 1 年', '过去 1 年'),
'지난 7일 동안': ('in the last 7 days', '直近 7 日間で', '在过去 7 天内'),
'지난 30일 동안': ('in the last 30 days', '直近 30 日間で', '在过去 30 天内'),
'지난 365일 동안': ('in the last 365 days', '直近 365 日間で', '在过去 365 天内'),
'지난 1년 동안': ('in the last year', '直近 1 年間で', '在过去 1 年内'),
'지금까지': ('so far', 'これまでに', '至今'),

# ── 연동 안내 줄 ──────────────────────────────────────────────────────────
'%(tool_name)s 연동에는 API 토큰이 필요합니다': (
    '%(tool_name)s needs an API token',
    '%(tool_name)s の連携には API トークンが必要です',
    '%(tool_name)s 需要 API 令牌'),
'계정마다 하나씩 발급되며, 프로그램 설정에 넣으면 됩니다.': (
    'One is issued per account; paste it into the program settings.',
    'アカウントごとに 1 つ発行され、プログラムの設定に入れるだけです。',
    '每个账号发放一个，填入程序设置即可。'),
'토큰은 회원에게만 발급됩니다.': (
    'Tokens are issued to members only.', 'トークンは会員のみに発行されます。',
    '令牌仅向会员发放。'),
'하루에 몇 번 쳤는지 세어 보냅니다.': (
    'It counts your daily keystrokes and sends them here.',
    '1 日に何回叩いたかを数えて送ります。',
    '统计每天的打键数并发送。'),
'게임 기록을 읽어 서열표를 자동으로 채웁니다.': (
    'It reads your game records and fills in the rank tables automatically.',
    'ゲームの記録を読み取り、難易度表を自動で埋めます。',
    '读取游戏记录，自动填写难度表。'),
'API 토큰 보기': ('View API token', 'API トークンを見る', '查看 API 令牌'),

# ── API 토큰 화면 ─────────────────────────────────────────────────────────
'내 토큰': ('My token', '自分のトークン', '我的令牌'),
'재발급': ('Reissue', '再発行', '重新发放'),
'복사됨': ('Copied', 'コピーしました', '已复制'),
'내려받기': ('Download', 'ダウンロード', '下载'),
'데이터 연동': ('Data sync', 'データ連携', '数据联动'),
'준비 중': ('Coming soon', '準備中', '准备中'),
'준비 중입니다': ('Coming soon', '準備中です', '准备中'),
'토큰은 회원에게만 발급됩니다': (
    'Tokens are issued to members only', 'トークンは会員のみに発行されます',
    '令牌仅向会员发放'),
'지금 토큰은 즉시 쓸 수 없게 됩니다. 새로 발급할까요?': (
    'Your current token stops working immediately. Issue a new one?',
    '現在のトークンは直ちに使えなくなります。新しく発行しますか？',
    '当前令牌将立即失效。要重新发放吗？'),
'계정마다 하나씩 발급되는 열쇠입니다. 아래 프로그램들이 이 토큰 하나로 계정을 확인합니다.': (
    'A key issued once per account. The programs below identify you with this single token.',
    'アカウントごとに 1 つ発行される鍵です。下のプログラムはこのトークン 1 つで'
    'アカウントを確認します。',
    '每个账号发放一个的钥匙。下列程序都用这一个令牌确认账号。'),
'발급일': ('Issued', '発行日', '发放日期'),
'<b>재발급하면 지금 토큰은 그 즉시 쓸 수 없게 됩니다.</b> 이 토큰을 넣어 둔 프로그램은 전부 새 토큰으로 다시 설정해야 기록이 올라갑니다. 토큰이 남에게 알려졌을 때만 재발급하세요.': (
    '<b>Reissuing invalidates your current token immediately.</b> Every program holding '
    'the old token must be updated before it can upload again. Reissue only if the token leaked.',
    '<b>再発行すると、現在のトークンは直ちに使えなくなります。</b>このトークンを入れて'
    'あるプログラムはすべて新しいトークンに設定し直さないと記録が上がりません。'
    'トークンが他人に知られたときだけ再発行してください。',
    '<b>重新发放后，当前令牌会立即失效。</b>所有填入旧令牌的程序都必须改为新令牌才能继续上传。'
    '仅在令牌泄露时才重新发放。'),
'토큰은 계정마다 하나씩 발급되는 열쇠라, 계정이 있어야 만들 수 있습니다. 가입하면 바로 발급되며 따로 신청할 것은 없습니다.': (
    'A token is a key tied to an account, so you need one first. It is issued as soon '
    'as you sign up — there is nothing extra to request.',
    'トークンはアカウントごとに発行される鍵なので、アカウントがないと作れません。'
    '登録すればすぐ発行され、別途申請は不要です。',
    '令牌是与账号绑定的钥匙，需要先有账号。注册后立即发放，无需另行申请。'),
'하루에 몇 번 쳤는지를 기록해 이 사이트로 보냅니다. 보낸 값은 \'일일 타건 기록\'에 쌓입니다.': (
    'It counts your daily keystrokes and sends them here. They collect under '
    "'Daily keystrokes'.",
    '1 日に何回叩いたかを記録してこのサイトに送ります。送った値は「デイリー打鍵記録」に'
    '溜まります。',
    '统计每天的打键数并发送到本站。发送的数值会累积在“每日打键记录”。'),
'IIDXwidget 설정에 위 토큰을 넣고 저장합니다.': (
    'Paste the token above into IIDXwidget settings and save.',
    'IIDXwidget の設定に上のトークンを入れて保存します。',
    '将上面的令牌填入 IIDXwidget 设置并保存。'),
'프로그램을 켜 두면 타건 수가 자동으로 올라갑니다.': (
    'Leave the program running and keystrokes upload automatically.',
    'プログラムを起動しておけば打鍵数が自動で送られます。',
    '保持程序运行，打键数会自动上传。'),
'게임 기록을 읽어 서열표의 클리어 램프와 점수를 자동으로 채워 넣을 프로그램입니다. 지금은 손으로 입력해야 하는 부분입니다.': (
    'A program that will read your game records and fill in clear lamps and scores '
    'automatically. For now this has to be entered by hand.',
    'ゲームの記録を読み取り、難易度表のクリアランプとスコアを自動で埋めるプログラムです。'
    '今は手で入力する必要がある部分です。',
    '一个读取游戏记录、自动填写难度表通关灯与分数的程序。目前这部分需要手动输入。'),
'같은 토큰을 그대로 씁니다. 따로 발급받을 것은 없습니다.': (
    'It uses the same token. Nothing extra to issue.',
    '同じトークンをそのまま使います。別途発行するものはありません。',
    '直接使用相同的令牌。无需另行发放。'),

# ── 데이터 동기화 화면 ────────────────────────────────────────────────────
'개발 로드맵 보기': ('See the roadmap', '開発ロードマップを見る', '查看开发路线图'),
'게임 기록을 읽어 서열표의 클리어 램프와 점수를 자동으로 채워 넣는 기능입니다. 지금은 서열표에서 손으로 입력해야 하는 부분입니다.': (
    'This will read your game records and fill in clear lamps and scores automatically. '
    'For now you enter them by hand on the rank table.',
    'ゲームの記録を読み取り、難易度表のクリアランプとスコアを自動で埋める機能です。'
    '今は難易度表で手入力している部分です。',
    '该功能会读取游戏记录，自动填写难度表的通关灯与分数。目前需要在难度表上手动输入。'),
'연동에는 지금 쓰는 API 토큰을 그대로 씁니다. 따로 발급받을 것은 없습니다.': (
    'It will use the API token you already have. Nothing extra to issue.',
    '連携には今使っている API トークンをそのまま使います。別途発行は不要です。',
    '联动将直接使用你现有的 API 令牌，无需另行发放。'),

# ── 프로젝트 소개 ─────────────────────────────────────────────────────────
'개발자에 대해': ('About the developer', '開発者について', '关于开发者'),
'(준비 중입니다)': ('(Coming soon)', '（準備中です）', '（准备中）'),
'Buy me a coffee': ('Buy me a coffee', 'Buy me a coffee', 'Buy me a coffee'),
'이 사이트가 마음에 드셨다면 <a href="https://buymeacoffee.com/sadang" target="_blank" rel="noopener">커피 한 잔<i class="bi bi-cup-hot-fill ms-1"></i></a> 부탁드립니다. 서버 유지에 보탬이 됩니다.': (
    'If you like this site, consider '
    '<a href="https://buymeacoffee.com/sadang" target="_blank" rel="noopener">'
    'buying a coffee<i class="bi bi-cup-hot-fill ms-1"></i></a>. It helps keep the server running.',
    'このサイトを気に入っていただけたら '
    '<a href="https://buymeacoffee.com/sadang" target="_blank" rel="noopener">'
    'コーヒーを一杯<i class="bi bi-cup-hot-fill ms-1"></i></a> いかがでしょうか。'
    'サーバー維持の助けになります。',
    '如果你喜欢这个站点，欢迎 '
    '<a href="https://buymeacoffee.com/sadang" target="_blank" rel="noopener">'
    '请我喝杯咖啡<i class="bi bi-cup-hot-fill ms-1"></i></a>，这有助于维持服务器运行。'),

# ── 계정 설정 ─────────────────────────────────────────────────────────────
'현재 사진 삭제하고 기본 아이콘으로': (
    'Remove the photo and use the default icon',
    '現在の写真を削除して既定のアイコンにする',
    '删除当前照片并使用默认图标'),

# ── 가입 폼 미리보기 ──────────────────────────────────────────────────────
'아이디': ('your-id', 'あなたのID', '你的ID'),

# ── 가입 (개인정보 동의) ──────────────────────────────────────────────────
'<a href="/privacy/" target="_blank" rel="noopener">개인정보처리방침</a>을 읽었고 이에 동의합니다.': (
    'I have read and agree to the '
    '<a href="/privacy/" target="_blank" rel="noopener">Privacy Policy</a>.',
    '<a href="/privacy/" target="_blank" rel="noopener">プライバシーポリシー</a>を'
    '読み、これに同意します。',
    '我已阅读并同意<a href="/privacy/" target="_blank" rel="noopener">隐私政策</a>。'),
'개인정보처리방침에 동의해야 가입할 수 있습니다.': (
    'You must agree to the Privacy Policy to sign up.',
    'プライバシーポリシーに同意しないと登録できません。',
    '需要同意隐私政策才能注册。'),
'"%(name)s" 은(는) 사용할 수 없는 아이디입니다.': (
    '"%(name)s" cannot be used as an ID.',
    '「%(name)s」は使用できない ID です。',
    '“%(name)s”不能用作 ID。'),
'영문·숫자·밑줄(_)만, 4자 이상. 가입 후에는 바꿀 수 없습니다. 사이트가 쓰는 이름(admin, status 등)은 쓸 수 없습니다.': (
    'Letters, digits and underscore only, 4 or more characters. Cannot be changed after '
    'signup. Names the site uses (admin, status, ...) are not allowed.',
    '英数字とアンダースコア(_)のみ、4 文字以上。登録後は変更できません。'
    'サイトが使う名前(admin, status など)は使えません。',
    '仅限字母、数字和下划线(_)，4 个字符以上。注册后不可更改。'
    '站点使用的名称（admin、status 等）不可使用。'),
}
