# -*- coding: utf-8 -*-
"""로드맵 시기 재구성으로 새로 생긴 문구.

기존 연혁 번역(newtrans_roadmap)의 표기를 그대로 따른다.
  (완료)   (done) / （完了） / （已完成）
  (진행 중) (in progress) / （進行中） / （进行中）
  추후 예정 Planned / 今後の予定 / 后续计划
"""

TRANS = {

# --- 시기 ---
'2026 Q2 (완료)': ('2026 Q2 (done)', '2026 Q2（完了）', '2026 Q2（已完成）'),
'2026 Q3 (진행 중)': (
    '2026 Q3 (in progress)', '2026 Q3（進行中）', '2026 Q3（进行中）'),
'2026 Q4 ~ (예정)': (
    '2026 Q4 onward (planned)', '2026 Q4 以降（予定）', '2026 Q4 起（计划中）'),

# --- 제목 ---
'서열 분류 자동화': (
    'Automated rank classification', '難易度分類の自動化', '难度分类自动化'),
'서비스 개발 마무리 및 운영': (
    'Wrapping up development, then operations',
    '開発の仕上げと運用', '开发收尾与运营'),

# --- 내용 ---
'- 신곡 데이터 추가 및 서열 분류 자동화': (
    '- Added new song data and automated rank classification',
    '- 新曲データの追加と難易度分類の自動化',
    '- 新增新曲数据并实现难度分类自动化'),
'- 전체 코드 전수 리팩토링 및 구조 정리': (
    '- Refactoring the entire codebase and tidying its structure',
    '- コード全体の総点検リファクタリングと構造の整理',
    '- 对全部代码进行通盘重构并整理结构'),
'- 서비스 개발을 마무리하고, 유지보수와 장애 대응에 집중': (
    '- Finish building the service, then focus on maintenance and incident response',
    '- サービス開発を仕上げ、保守と障害対応に注力',
    '- 完成服务开发，并专注于维护与故障处理'),
}
