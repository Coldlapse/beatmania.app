# -*- coding: utf-8 -*-
"""데이터 동기화(tracker.tsv 올리기) 화면과 오류 문구.

용어는 앞 묶음을 따른다.
  클리어 램프  clear lamp / クリアランプ / 通关灯
  등급(DJ 등급) grade / DJレベル / 评级
  INF오소리    INFOhSorry (앱 이름. 번역하지 않는다)
"""

TRANS = {

# ── 화면 ────────────────────────────────────────────────────────────────
'파일로 올리기': ('Upload a file', 'ファイルでアップロード', '上传文件'),

'Reflux 가 만든 <code>tracker.tsv</code> 를 올리면 레벨 10 이상 채보의 클리어 램프와 등급을 서열표에 반영합니다.': (
    'Upload the <code>tracker.tsv</code> made by Reflux to apply clear lamps and grades '
    'for charts of level 10 and above to the rank tables.',
    'Reflux が作成した <code>tracker.tsv</code> をアップロードすると、レベル10以上の譜面の'
    'クリアランプとDJレベルを難易度表に反映します。',
    '上传 Reflux 生成的 <code>tracker.tsv</code>，即可将 10 级以上谱面的通关灯和评级反映到难度表。'),

'INF오소리를 쓰신다면 이 위치에 있습니다:': (
    'If you use INFOhSorry, it is here:',
    'INFOhSorry をお使いなら、ここにあります:',
    '如果您使用 INFOhSorry，文件在这里：'),

'지금 기록보다 좋을 때만 올립니다. 직접 입력한 기록을 낮추지 않습니다.': (
    'Records are only raised when better. Records you entered by hand are never lowered.',
    '今の記録より良い場合のみ更新します。手入力した記録を下げることはありません。',
    '仅在比现有记录更好时更新，不会降低您手动输入的记录。'),

'같은 파일을 다시 올려도 결과는 같습니다.': (
    'Uploading the same file again gives the same result.',
    '同じファイルを再度アップロードしても結果は同じです。',
    '再次上传同一文件，结果不变。'),

'올리기': ('Upload', 'アップロード', '上传'),

'로그인하면 올릴 수 있습니다.': (
    'Log in to upload.', 'ログインするとアップロードできます。', '登录后即可上传。'),

'자동 동기화 앱': ('Auto-sync app', '自動同期アプリ', '自动同步应用'),

'INFINITAS 를 켜 둔 동안 옆에 상주하면서 기록이 바뀔 때마다 자동으로 올리는 앱을 준비하고 있습니다. 위와 같은 API 토큰을 씁니다.': (
    'We are preparing an app that stays running alongside INFINITAS and uploads your '
    'records automatically whenever they change. It uses the same API token.',
    'INFINITAS の起動中に常駐し、記録が変わるたびに自動でアップロードするアプリを準備中です。'
    '同じ API トークンを使います。',
    '我们正在准备一款应用：在 INFINITAS 运行期间常驻后台，记录变化时自动上传。'
    '它使用同一个 API 令牌。'),

# ── 결과 ────────────────────────────────────────────────────────────────
'반영했습니다': ('Applied', '反映しました', '已应用'),
'새 기록': ('New', '新規', '新增'),
'갱신': ('Improved', '更新', '已更新'),
'변화 없음': ('Unchanged', '変化なし', '无变化'),
'못 찾은 곡': ('Not found', '見つからない曲', '未找到的曲目'),
'못 찾은 곡 보기': ('Show songs not found', '見つからない曲を表示', '查看未找到的曲目'),

'최근 동기화': ('Recent syncs', '最近の同期', '最近同步'),
'시각': ('Time', '日時', '时间'),
'경로': ('Via', '経路', '途径'),
'앱': ('App', 'アプリ', '应用'),
'웹': ('Web', 'ウェブ', '网页'),

# ── 오류 ────────────────────────────────────────────────────────────────
'파일을 골라 주세요.': (
    'Please choose a file.', 'ファイルを選択してください。', '请选择文件。'),
'잠시 뒤에 다시 올려 주세요.': (
    'Please try again in a moment.', 'しばらくしてから再度お試しください。', '请稍后再试。'),
'파일이 너무 큽니다.': (
    'The file is too large.', 'ファイルが大きすぎます。', '文件过大。'),
'UTF-8 로 읽을 수 없는 파일입니다.': (
    'The file cannot be read as UTF-8.', 'UTF-8 として読めないファイルです。',
    '无法以 UTF-8 读取该文件。'),
'빈 파일입니다.': ('The file is empty.', '空のファイルです。', '文件为空。'),
'tracker.tsv 형식이 아닙니다. Reflux 가 만든 파일을 올려 주세요.': (
    'This is not a tracker.tsv file. Please upload the file made by Reflux.',
    'tracker.tsv の形式ではありません。Reflux が作成したファイルをアップロードしてください。',
    '这不是 tracker.tsv 格式。请上传 Reflux 生成的文件。'),
}
