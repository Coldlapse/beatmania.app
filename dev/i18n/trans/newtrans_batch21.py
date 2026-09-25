# -*- coding: utf-8 -*-
"""로드맵 2026 Q3 마감, 데이터 동기화의 파일 위치·출처, CPI 공유 안내."""

TRANS = {

# ── 로드맵 ──────────────────────────────────────────────────────────────
'2026 Q3 (완료)': ('2026 Q3 (done)', '2026 Q3（完了）', '2026 Q3（已完成）'),
'- healthcheck 구현': ('- Health check', '- ヘルスチェックの実装', '- 实现健康检查'),
'- 타건 기록 리더보드 추가': ('- Keystroke leaderboard', '- 打鍵記録リーダーボードの追加', '- 新增击键记录排行榜'),
'- 다국어 지원(영문·일본어·중국어) 번역 추가': (
    '- Multilingual support: English, Japanese and Chinese',
    '- 多言語対応(英語・日本語・中国語)の翻訳を追加', '- 新增多语言支持（英语、日语、中文）'),
'- CPI 연계 레이팅 추정 도입': (
    '- CPI-based rating estimate', '- CPI 連携のレーティング推定を導入', '- 引入基于 CPI 的评分估算'),

# ── 데이터 동기화: 파일 위치 ─────────────────────────────────────────────
'파일은 Reflux 를 어떻게 띄우는지에 따라 이곳에 있습니다.': (
    'Where the file is depends on how you run Reflux.',
    'ファイルの場所は Reflux の起動方法によって異なります。',
    '文件位置取决于您如何运行 Reflux。'),
'Reflux 를 직접 실행한다면: Reflux.exe 가 있는 폴더': (
    'If you run Reflux yourself: the folder containing Reflux.exe',
    'Reflux を直接起動している場合: Reflux.exe のあるフォルダ',
    '如果直接运行 Reflux：Reflux.exe 所在的文件夹'),
'INF오소리를 쓴다면: INF오소리도 내부에서 Reflux 를 실행해 같은 파일을 만들어 둡니다.': (
    'If you use INFOhSorry: it runs Reflux internally and creates the same file.',
    'INFOhSorry をお使いの場合: INFOhSorry も内部で Reflux を実行し、同じファイルを作成します。',
    '如果使用 INFOhSorry：它会在内部运行 Reflux 并生成同一文件。'),

# ── 데이터 동기화: 출처 ─────────────────────────────────────────────────
'함께 쓰는 프로젝트': ('Projects we build on', '利用しているプロジェクト', '所使用的项目'),
'INF오소리': ('INFOhSorry', 'INFOhSorry', 'INFOhSorry'),
'INFINITAS 가 실행되는 동안 게임 기록을 읽어 tracker.tsv 로 남기는 도구입니다. 이 페이지와 동기화 앱이 읽는 파일이 이것입니다.': (
    'A tool that reads game records while INFINITAS is running and writes them to tracker.tsv. '
    'This is the file this page and the sync app read.',
    'INFINITAS の起動中にゲーム記録を読み取り、tracker.tsv に書き出すツールです。'
    'このページと同期アプリが読むのはこのファイルです。',
    '在 INFINITAS 运行期间读取游戏记录并写入 tracker.tsv 的工具。本页面和同步应用读取的就是这个文件。'),
'최신 INFINITAS 패치에 대응한 Reflux 포크입니다. 원본은 2026년 5월 이후 갱신이 없어, 동기화 앱은 이 판을 받아 씁니다.': (
    'A Reflux fork that keeps up with the latest INFINITAS patches. The original has not been '
    'updated since May 2026, so the sync app downloads this version.',
    '最新の INFINITAS パッチに対応した Reflux のフォークです。本家は2026年5月以降更新がないため、'
    '同期アプリはこちらを使います。',
    '适配最新 INFINITAS 补丁的 Reflux 分支。原版自 2026 年 5 月后未再更新，因此同步应用使用此版本。'),
'같은 Reflux 를 쓰는 기록 분석 앱입니다. 이미 쓰고 계신 분이 그 파일을 그대로 올리거나 동기화 앱과 함께 쓸 수 있게 연동했습니다. 코드를 가져오지는 않았습니다.': (
    'A record analysis app that uses the same Reflux. We made it work together so existing users '
    'can upload that file as is or run it alongside the sync app. No code was taken from it.',
    '同じ Reflux を使う記録分析アプリです。すでにお使いの方がそのファイルをそのままアップロードしたり、'
    '同期アプリと併用したりできるよう連携しました。コードは流用していません。',
    '使用同一 Reflux 的记录分析应用。为了让现有用户可以直接上传该文件或与同步应用同时使用而做了联动。'
    '未使用其代码。'),

# ── CPI 공유 ────────────────────────────────────────────────────────────
'프로필이 비공개라 공유 주소는 다른 사람에게 열리지 않습니다.': (
    'Your profile is private, so others cannot open the shared link.',
    'プロフィールが非公開のため、共有アドレスは他の人には開けません。',
    '您的个人资料为非公开，他人无法打开分享链接。'),
}
