# -*- coding: utf-8 -*-
"""메인 페이지 공지사항 칸(디스코드). 탭 이름은 .env 값이지만 카탈로그에 두어 번역한다."""

TRANS = {

'공지사항': ('Announcements', 'お知らせ', '公告'),
'디스코드에서 보기': ('View on Discord', 'Discord で見る', '在 Discord 查看'),
'공지 채널': ('Announcement channels', 'お知らせチャンネル', '公告频道'),
'불러오는 중…': ('Loading…', '読み込み中…', '加载中…'),
'공지를 불러오지 못했습니다.': (
    'Could not load announcements.', 'お知らせを読み込めませんでした。', '无法加载公告。'),
'아직 올라온 공지가 없습니다.': (
    'No announcements yet.', 'まだお知らせはありません。', '暂无公告。'),
'수정됨': ('edited', '編集済', '已编辑'),

# ── 탭 이름 (DISCORD_NOTICE_CHANNELS) ──────────────────────────────────
'중요 공지': ('Important', '重要なお知らせ', '重要公告'),
'일반 공지': ('General', '一般のお知らせ', '一般公告'),
'갱신 이력': ('Update log', '更新履歴', '更新记录'),
}

# ── 서열표 편집 팝업의 EX SCORE 저장 (views.modify action=exscore) ─────────
TRANS.update({
'저장했습니다.': ('Saved.', '保存しました。', '已保存。'),
'잘못된 요청입니다.': ('Invalid request.', '不正なリクエストです。', '无效的请求。'),
'EX SCORE 는 0 에서 %(n)d 사이여야 합니다.': (
    'EX SCORE must be between 0 and %(n)d.', 'EX SCORE は 0 から %(n)d の間で入力してください。',
    'EX SCORE 必须在 0 到 %(n)d 之间。'),
})

# ── 계정 설정의 이름 검증 (forms.no_markup) ────────────────────────────────
TRANS.update({
'< > 와 제어 문자는 쓸 수 없습니다.': (
    '< > and control characters are not allowed.', '< > と制御文字は使えません。', '不能使用 < > 和控制字符。'),
})
