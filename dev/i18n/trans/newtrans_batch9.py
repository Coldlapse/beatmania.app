# -*- coding: utf-8 -*-
"""개발자 소개 카드에 IR 프로필 링크를 넣고, 로드맵의 인라인 색을 걷어내며
생긴 문구들.
"""

TRANS = {

# 보쿠타치(boku.tachi.ac)는 BMS 인터넷 랭킹이다. 서비스 이름은 옮기지 않고
# 'IR Profile' 이라는 라벨만 각 언어의 관례에 맞춘다. IR 은 이 바닥에서
# 그대로 통하는 말이라 영어권·일본어권 모두 IR 로 둔다.
'IR Profile': ('IR Profile', 'IR プロフィール', 'IR 主页'),

# 로드맵 본문. 링크에 박혀 있던 style="color:#007bff" 를 CSS 로 옮기면서
# msgid 가 바뀌었다. 뜻은 그대로다.
'- <a href="%(url)s" target="_blank">IIDXwidget</a> 프로젝트 기반 타건 횟수 기록 일지 기능 구현': (
    '- Daily keystroke log built on the '
    '<a href="%(url)s" target="_blank">IIDXwidget</a> project',
    '- <a href="%(url)s" target="_blank">IIDXwidget</a> '
    'プロジェクトを基にした打鍵数記録日誌機能の実装',
    '- 基于 <a href="%(url)s" target="_blank">IIDXwidget</a> 项目实现打键次数记录日志功能'),
}
