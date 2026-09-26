# -*- coding: utf-8 -*-
"""API 토큰 페이지: 서명 없는 배포 프로그램 안내(widgets/unsigned_notice.html), 동기화 앱 설명 정리.

Windows 화면 이름은 각 언어판 Windows 에 나오는 표기를 쓴다(SmartScreen·Windows 보안).
"""

TRANS = {

'최신 버전을 받아 설치합니다.': (
    'Download and install the latest version.',
    '最新バージョンをダウンロードしてインストールします。',
    '下载并安装最新版本。'),

'켜 두면 INFINITAS 기록이 바뀔 때마다 클리어 램프·DJ RANK·EX SCORE 를 서열표에 자동으로 반영합니다.': (
    'While it is running, it automatically updates your rank tables with clear lamps, DJ RANK and EX SCORE whenever your INFINITAS records change.',
    '起動しておくと、INFINITAS の記録が変わるたびにクリアランプ・DJ RANK・EX SCORE を序列表へ自動で反映します。',
    '保持运行时,每当 INFINITAS 记录变化,都会自动将通关灯・DJ RANK・EX SCORE 反映到难度表。'),

'설치가 막히거나 백신이 경고할 때': (
    'If installation is blocked or your antivirus warns you',
    'インストールがブロックされたり、ウイルス対策ソフトが警告したりする場合',
    '安装被阻止或杀毒软件发出警告时'),

'모든 beatmania.app 배포 프로그램에는 디지털 서명이 없어, 백신이 악성 프로그램으로 오진하거나 Windows SmartScreen 이 실행을 막을 수 있습니다. 특히 동기화 앱이 쓰는 Reflux 는 게임 메모리를 읽는 도구라 오진이 잦습니다.': (
    'None of the programs distributed by beatmania.app are digitally signed, so antivirus software may flag them as malware by mistake, or Windows SmartScreen may block them. Reflux, used by the sync app, reads game memory and is especially prone to false positives.',
    'beatmania.app が配布するプログラムにはデジタル署名がないため、ウイルス対策ソフトがマルウェアと誤検知したり、Windows SmartScreen が実行をブロックしたりすることがあります。特に同期アプリが使う Reflux はゲームのメモリを読むツールのため、誤検知がよく起こります。',
    'beatmania.app 发布的所有程序都没有数字签名,因此杀毒软件可能误报为恶意程序,或 Windows SmartScreen 可能阻止运行。尤其是同步应用使用的 Reflux 会读取游戏内存,更容易被误报。'),

'<b>SmartScreen</b> — "Windows에서 PC를 보호했습니다" 창이 뜨면 <b>추가 정보</b>를 누른 뒤 <b>실행</b>을 누릅니다.': (
    '<b>SmartScreen</b> — when "Windows protected your PC" appears, click <b>More info</b>, then <b>Run anyway</b>.',
    '<b>SmartScreen</b> — 「Windows によって PC が保護されました」と表示されたら、<b>詳細情報</b>を押してから<b>実行</b>を押します。',
    '<b>SmartScreen</b> — 出现“Windows 已保护你的电脑”时,点击<b>更多信息</b>,然后点击<b>仍要运行</b>。'),

'<b>백신이 파일을 지우거나 격리할 때</b> — Windows 보안 → 바이러스 및 위협 방지 → 보호 기록에서 해당 항목을 <b>허용</b>하고, 설정 관리 → 제외 → <b>제외 추가 → 폴더</b>로 아래 폴더를 추가합니다. 다른 백신은 예외(제외) 목록에 같은 폴더를 넣습니다.': (
    '<b>If your antivirus deletes or quarantines a file</b> — in Windows Security → Virus &amp; threat protection → Protection history, <b>Allow</b> the item, then under Manage settings → Exclusions choose <b>Add an exclusion → Folder</b> and add the folders below. For other antivirus software, add the same folders to its exclusion list.',
    '<b>ウイルス対策ソフトがファイルを削除・隔離した場合</b> — Windows セキュリティ → ウイルスと脅威の防止 → 保護の履歴で該当項目を<b>許可</b>し、設定の管理 → 除外 → <b>除外の追加 → フォルダー</b>で下のフォルダーを追加します。他のウイルス対策ソフトでは、除外リストに同じフォルダーを追加してください。',
    '<b>杀毒软件删除或隔离文件时</b> — 在 Windows 安全中心 → 病毒和威胁防护 → 保护历史记录中<b>允许</b>该项目,然后在管理设置 → 排除项 → <b>添加排除项 → 文件夹</b>中添加以下文件夹。其他杀毒软件请将相同文件夹加入排除列表。'),

'동기화 앱이 받는 Reflux': (
    'Reflux (downloaded by the sync app)',
    '同期アプリがダウンロードする Reflux',
    '同步应用下载的 Reflux'),

'모든 프로그램은 오픈소스이므로, 무엇을 하는지 위해성을 코드로 직접 검증할 수 있습니다:': (
    'All programs are open source, so you can verify for yourself in the code that they are safe:',
    'すべてのプログラムはオープンソースなので、安全性をコードで直接確認できます:',
    '所有程序均为开源,你可以直接查看代码来验证其安全性:'),

}
