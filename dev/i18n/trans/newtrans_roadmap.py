# -*- coding: utf-8 -*-
"""로드맵 연혁 번역.

연혁은 사실 기록이라 뜻을 바꾸지 않는다. 고유명사(IIDXwidget, Reflux, CPI,
beatoraja, INFINITAS)는 그대로 둔다.
"""

TRANS = {

# 페이지 머리
'beatmania.app 로드맵': (
    'beatmania.app Roadmap', 'beatmania.app ロードマップ', 'beatmania.app 路线图'),
'IIDX INFINTIAS Rank Table 프로젝트의 개발 진행 상황과 앞으로 업데이트될 기능들입니다.': (
    'Development progress of the IIDX INFINITAS Rank Table project and what is coming next.',
    'IIDX INFINITAS Rank Table プロジェクトの開発状況と、今後追加予定の機能です。',
    'IIDX INFINITAS Rank Table 项目的开发进展与今后将更新的功能。'),

# 시기
'2022 Q4 (완료)': ('2022 Q4 (done)', '2022 Q4（完了）', '2022 Q4（已完成）'),
'2023 Q1 (완료)': ('2023 Q1 (done)', '2023 Q1（完了）', '2023 Q1（已完成）'),
'2023 Q2 (완료)': ('2023 Q2 (done)', '2023 Q2（完了）', '2023 Q2（已完成）'),
'2023 Q3 (완료)': ('2023 Q3 (done)', '2023 Q3（完了）', '2023 Q3（已完成）'),
'2025 Q3 (완료)': ('2025 Q3 (done)', '2025 Q3（完了）', '2025 Q3（已完成）'),
'2026 Q2 (진행 중)': (
    '2026 Q2 (in progress)', '2026 Q2（進行中）', '2026 Q2（进行中）'),
'추후 예정': ('Planned', '今後の予定', '后续计划'),

# 제목
'서버 구축 및 프로젝트 개시': (
    'Server setup and project launch', 'サーバー構築とプロジェクト開始',
    '搭建服务器与项目启动'),
'시스템 안정화 및 기능 추가': (
    'Stabilisation and new features', 'システム安定化と機能追加',
    '系统稳定化与功能新增'),
'주요 기능 추가 및 UI 보강': (
    'Major features and UI improvements', '主要機能の追加と UI 強化',
    '主要功能新增与 UI 强化'),
'SPL 난이도 지원 추가': (
    'SPL difficulty support', 'SPL 難易度対応の追加', '新增 SPL 难度支持'),
'기능 업데이트 공백기': (
    'Feature update hiatus', '機能アップデートの空白期', '功能更新空窗期'),
'웹사이트 외관 전면 개편 및 생태계 확장': (
    'Full visual overhaul and ecosystem expansion',
    'サイト外観の全面刷新とエコシステム拡張', '网站外观全面改版与生态扩展'),
'데이터 연동 및 시스템 고도화': (
    'Data integration and system upgrades', 'データ連携とシステム高度化',
    '数据联动与系统升级'),
'다국어 지원': ('Multilingual support', '多言語対応', '多语言支持'),

# 내용
'- 프로젝트 서비스를 위한 베어본 서버 PC 구매 및 구축': (
    '- Bought and set up a barebone server PC for the service',
    '- サービス用のベアボーンサーバー PC を購入し構築',
    '- 购置并搭建用于服务的准系统服务器 PC'),
'- iidxranktable 프로젝트 클론 및 INFINITAS 수록곡 반영': (
    '- Cloned the iidxranktable project and applied the INFINITAS song list',
    '- iidxranktable プロジェクトをクローンし INFINITAS の収録曲を反映',
    '- 克隆 iidxranktable 项目并导入 INFINITAS 收录曲'),
'- 난이도표 UI 한글화': (
    '- Translated the rank table UI into Korean', '- 難易度表 UI の韓国語化',
    '- 难度表 UI 韩语化'),
'- 원본 코드에서 SPN, SPH의 난이도 구분이 배경색으로 구현되도록 의도되었으나 작동하지 않던 버그 수정': (
    '- Fixed a bug where SPN/SPH difficulty was meant to be distinguished by background '
    'colour but never worked',
    '- 元のコードで SPN・SPH の難易度を背景色で区別する意図だったが動作していなかった'
    'バグを修正',
    '- 修复原代码中本应以背景色区分 SPN、SPH 难度却未生效的缺陷'),
'- SSL 인증서 적용 및 점수순 정렬 추가': (
    '- Applied an SSL certificate and added sorting by score',
    '- SSL 証明書の適用とスコア順ソートの追加',
    '- 应用 SSL 证书并新增按分数排序'),
'- 랭크(B, A, AA, AAA, MAX-) 기록 기능 구현': (
    '- Added rank (B, A, AA, AAA, MAX-) recording',
    '- ランク(B, A, AA, AAA, MAX-)記録機能の実装',
    '- 实现等级（B、A、AA、AAA、MAX-）记录功能'),
'- BMS(beatoraja) 플레이어를 위한 흰숫 변환기 기능 구현': (
    '- Added a SUDDEN+ converter for BMS (beatoraja) players',
    '- BMS(beatoraja) プレイヤー向けの白数字コンバーター実装',
    '- 为 BMS(beatoraja) 玩家实现白数字换算器'),
'- 점수(랭크)순 정렬 기능 구현': (
    '- Added sorting by score (rank)', '- スコア(ランク)順ソート機能の実装',
    '- 实现按分数（等级）排序'),
'- 다크 모드 및 곡 이름 검색 강조 기능 구현': (
    '- Added dark mode and song title search highlighting',
    '- ダークモードと曲名検索ハイライトの実装',
    '- 实现深色模式与曲名搜索高亮'),
'- iidx.sadang.org → beatmania.app 사이트 도메인 변경': (
    '- Moved the domain from iidx.sadang.org to beatmania.app',
    '- サイトドメインを iidx.sadang.org から beatmania.app へ変更',
    '- 站点域名由 iidx.sadang.org 变更为 beatmania.app'),
'- 타인 서열표 조회(유저 검색) 및 프로필 비공개 기능 추가': (
    "- Added viewing other players' tables (user search) and private profiles",
    '- 他人の難易度表の閲覧(ユーザー検索)とプロフィール非公開機能の追加',
    '- 新增查看他人难度表（用户搜索）与资料不公开功能'),
'- INFINITAS의 레겐데리아 업뎃에 맞추어 서열표에 [L] 난이도가 지원되도록 기능 추가, 곡 배경색으로 구분하도록 설정': (
    '- Added [L] difficulty support in line with the INFINITAS LEGGENDARIA update, '
    'distinguished by song background colour',
    '- INFINITAS のレジェンダリア追加に合わせて難易度表で [L] 難易度に対応し、'
    '曲の背景色で区別するよう設定',
    '- 配合 INFINITAS 的 LEGGENDARIA 更新，难度表支持 [L] 难度，并以曲目背景色区分'),
'수록곡 데이터 갱신 유지, 서버 안정화 및 유지보수': (
    'Kept the song data updated; server stabilisation and maintenance',
    '収録曲データの更新維持、サーバー安定化と保守',
    '维持收录曲数据更新、服务器稳定化与维护'),
'- 부트스트랩(Bootstrap) 적용 등 사이트 디자인 및 UI 개선': (
    '- Improved site design and UI, including adopting Bootstrap',
    '- Bootstrap の適用などサイトデザインと UI の改善',
    '- 应用 Bootstrap 等，改善站点设计与 UI'),
'- 서열표 조회수 기록 및 조회 기능 구현': (
    '- Added recording and viewing of rank table view counts',
    '- 難易度表の閲覧数記録と閲覧機能の実装',
    '- 实现难度表浏览量的记录与查看'),
'- 신곡 데이터 추가 및 서열 분류 자동화(완료)': (
    '- Added new song data and automated rank classification (done)',
    '- 新曲データの追加と難易度分類の自動化(完了)',
    '- 新增新曲数据并实现难度分类自动化（已完成）'),
'- CPI 사이트 연계 레이팅 시스템 및 리더보드 구현': (
    '- Rating system and leaderboard linked with the CPI site',
    '- CPI サイトと連携したレーティングシステムとリーダーボードの実装',
    '- 实现与 CPI 站点联动的评分系统与排行榜'),
'- Reflux를 통한 자동 데이터 갱신 구현': (
    '- Automatic data updates via Reflux', '- Reflux による自動データ更新の実装',
    '- 通过 Reflux 实现数据自动更新'),
'- healthcheck 및 로깅 서버 구현': (
    '- Health check and logging server', '- ヘルスチェックとロギングサーバーの実装',
    '- 实现健康检查与日志服务器'),
'- <a href="%(url)s" target="_blank" style="color: #007bff; text-decoration: underline;">IIDXwidget</a> 프로젝트 기반 타건 횟수 기록 일지 기능 구현': (
    '- Daily keystroke log built on the '
    '<a href="%(url)s" target="_blank" style="color: #007bff; text-decoration: underline;">IIDXwidget</a> project',
    '- <a href="%(url)s" target="_blank" style="color: #007bff; text-decoration: underline;">IIDXwidget</a> '
    'プロジェクトを基にした打鍵数記録日誌機能の実装',
    '- 基于 <a href="%(url)s" target="_blank" style="color: #007bff; text-decoration: underline;">IIDXwidget</a> '
    '项目实现打键次数记录日志功能'),
'- 영문 및 일본어 번역 추가': (
    '- Added English and Japanese translations', '- 英語と日本語の翻訳を追加',
    '- 新增英语与日语翻译'),
}
