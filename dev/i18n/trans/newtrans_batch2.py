# -*- coding: utf-8 -*-
"""개발자 소개 · 계정 폼 도움말 · 타인 페이지 안내 번역.

용어는 기존 카탈로그를 따른다.
  닉네임          Display name / 表示名 / 显示名称
  서열표          Rank Tables / 難易度表 / 难度表
  일일 타건 기록  Daily Keystrokes / 日別打鍵記録 / 每日击键记录

blocktrans 의 msgid 는 %(var)s 형태다. {{ var }} 로 적으면 매칭되지 않는다.
"""

TRANS = {

# --- 계정 설정 폼 도움말 ---
'순위표 등 사이트 곳곳에 표시되는 공개 이름입니다. 다른 사람과 같아도 되며 언제든 바꿀 수 있습니다. 주소에 쓰이는 아이디와는 다릅니다.': (
    'The public name shown across the site, including the leaderboard. It may '
    'be the same as someone else\'s and you can change it at any time. It is '
    'not the ID used in your address.',
    'リーダーボードなど、サイトの各所に表示される公開名です。他の人と同じでも'
    '構わず、いつでも変更できます。アドレスに使われる ID とは別のものです。',
    '在排行榜等站内各处显示的公开名称。可以与他人相同，并且随时可以修改。'
    '与网址中使用的 ID 不同。'),

'서열표 프로필에 DJ NAME 으로 표시됩니다. 사이트 닉네임과는 별개이며, 다른 사람과 같아도 됩니다.': (
    'Shown as DJ NAME on your rank table profile. It is separate from your '
    'display name on this site, and may be the same as someone else\'s.',
    '難易度表のプロフィールに DJ NAME として表示されます。サイトの表示名とは'
    '別のもので、他の人と同じでも構いません。',
    '在难度表个人资料中显示为 DJ NAME。与站点显示名称无关，可以与他人相同。'),

'게임 화면에 나오는 ID 입니다. 앞글자를 고르고 네 자리씩 입력하세요.': (
    'The ID shown on the game screen. Pick the leading letter, then enter four '
    'digits in each box.',
    'ゲーム画面に表示される ID です。先頭の文字を選び、4桁ずつ入力してください。',
    '游戏画面上显示的 ID。请先选择首字母，再每四位分别输入。'),

'닉네임과 IIDX DJ NAME은 가입 초기 아이디로 기본 설정됩니다.': (
    'Your display name and IIDX DJ NAME are both set to your ID when you sign up.',
    '表示名と IIDX DJ NAME は、登録時には ID が初期値として設定されます。',
    '显示名称与 IIDX DJ NAME 在注册时默认设为您的 ID。'),

# --- 타인 서열표 안내 ---
'DJ %(dj)s (%(nick)s) 님의 서열표 페이지에 접근하셨습니다. 읽기 전용입니다.': (
    "You are viewing DJ %(dj)s (%(nick)s)'s rank table page. It is read-only.",
    'DJ %(dj)s（%(nick)s）さんの難易度表ページを表示しています。読み取り専用です。',
    '您正在查看 DJ %(dj)s（%(nick)s）的难度表页面，此页面为只读。'),

# --- API 토큰 안내 ---
'올라간 기록은 <a href="%(mypage_url)s">일일 타건 기록</a>에서 볼 수 있습니다.': (
    'You can see the uploaded records on '
    '<a href="%(mypage_url)s">Daily Keystrokes</a>.',
    'アップロードされた記録は<a href="%(mypage_url)s">日別打鍵記録</a>で確認できます。',
    '上传的记录可在<a href="%(mypage_url)s">每日击键记录</a>中查看。'),

# --- 개발자 소개 ---
# 발광개전은 BMS 의 発狂皆伝을 가리킨다. 고유명사이므로 각 언어의 표기를 쓴다.
'2022년에 IIDX와 BMS를 시작하여, 현재 SP 발광개전을 취득한 BMS 플레이어입니다. IIDX 인피니타스를 위한 독점 서열표 사이트가 없다는 점에 착안, <a href="%(repo)s" target="_blank" rel="noopener">lazykuna/iidxranktable</a> 을 포크하여 인피니타스 독점 서비스로 개발 및 유지보수 해왔습니다. 서비스에 대한 문의는 <a href="%(discord)s" target="_blank" rel="noopener">디스코드</a>에서 부탁드립니다.': (
    'I started IIDX and BMS in 2022 and now hold SP Hakkyou Kaiden as a BMS '
    'player. Noticing that no rank table site existed for IIDX INFINITAS alone, '
    'I forked <a href="%(repo)s" target="_blank" rel="noopener">lazykuna/iidxranktable</a> '
    'and have developed and maintained it as an INFINITAS-only service. For '
    'enquiries about the service, please reach me on '
    '<a href="%(discord)s" target="_blank" rel="noopener">Discord</a>.',
    '2022年に IIDX と BMS を始め、現在は SP 発狂皆伝を取得した BMS プレイヤーです。'
    'IIDX INFINITAS 専用の難易度表サイトが無いことに着目し、'
    '<a href="%(repo)s" target="_blank" rel="noopener">lazykuna/iidxranktable</a> '
    'をフォークして INFINITAS 専用サービスとして開発・保守してきました。'
    'サービスに関するお問い合わせは '
    '<a href="%(discord)s" target="_blank" rel="noopener">Discord</a> '
    'までお願いします。',
    '2022 年开始接触 IIDX 与 BMS，目前是已取得 SP 发狂皆传的 BMS 玩家。'
    '注意到没有专为 IIDX INFINITAS 打造的难度表站点，于是 fork 了 '
    '<a href="%(repo)s" target="_blank" rel="noopener">lazykuna/iidxranktable</a>，'
    '作为 INFINITAS 专用服务持续开发与维护。'
    '有关服务的咨询请前往 '
    '<a href="%(discord)s" target="_blank" rel="noopener">Discord</a>。'),

'유튜브': ('YouTube', 'YouTube', 'YouTube'),
}
