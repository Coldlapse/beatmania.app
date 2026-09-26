# -*- coding: utf-8 -*-
"""합산 BPI(프로필 뱃지 · /bpi/ 페이지)."""

TRANS = {

'SP☆12 %(n)s채보의 EX SCORE 로 계산한 합산 BPI 입니다. 계산식과 채보별 값은 BPIManager(bpi2.poyashi.me)를 따릅니다. 문제가 있으면 알려 주세요.': (
    'Total BPI calculated from EX SCOREs on %(n)s SP☆12 charts. The formula and per-chart values follow BPIManager (bpi2.poyashi.me). Let us know if something looks wrong.',
    'SP☆12 %(n)s 譜面の EX SCORE から計算した総合BPIです。計算式と譜面ごとの値は BPIManager(bpi2.poyashi.me)に準拠しています。問題があればお知らせください。',
    '根据 %(n)s 个 SP☆12 谱面的 EX SCORE 计算的总合 BPI。计算公式和各谱面数值遵循 BPIManager(bpi2.poyashi.me)。如有问题请告诉我们。'),

'<a href="https://bpi2.poyashi.me/" target="_blank" rel="noopener">BPIManager</a> 의 BPI V2 와 같은 식으로 계산합니다. 채보별 값(세계 기록·분포 모수)은 BPIManager 가 공개하는 값을 하루 한 번 받아 씁니다.': (
    'Calculated with the same formula as BPI V2 on <a href="https://bpi2.poyashi.me/" target="_blank" rel="noopener">BPIManager</a>. Per-chart values (world records and distribution parameters) are fetched once a day from BPIManager\'s public data.',
    '<a href="https://bpi2.poyashi.me/" target="_blank" rel="noopener">BPIManager</a> の BPI V2 と同じ式で計算しています。譜面ごとの値(世界記録・分布パラメータ)は BPIManager が公開している値を1日1回取得して使います。',
    '采用与 <a href="https://bpi2.poyashi.me/" target="_blank" rel="noopener">BPIManager</a> 的 BPI V2 相同的公式计算。各谱面数值(世界纪录・分布参数)每天从 BPIManager 公开的数据获取一次。'),

'BPI 가 높은 기록': (
    'Highest BPI records',
    'BPI が高い記録',
    'BPI 最高的记录'),

'BPI 를 계산할 기록이 없습니다': (
    'No records to calculate BPI',
    'BPI を計算できる記録がありません',
    '没有可用于计算 BPI 的记录'),

'BPIManager 에 표시되는 값과 다르면 디스코드로 알려 주세요.': (
    'If the value differs from what BPIManager shows, please let us know on Discord.',
    'BPIManager の表示と値が異なる場合は Discord でお知らせください。',
    '如果与 BPIManager 显示的数值不同,请在 Discord 告诉我们。'),

'EX SCORE 가 있는 SP☆11·12 채보를 BPI 가 높은 순으로 보여 줍니다.': (
    'SP☆11/12 charts with an EX SCORE, sorted by BPI (highest first).',
    'EX SCORE がある SP☆11・12 の譜面を BPI が高い順に表示します。',
    '按 BPI 从高到低显示有 EX SCORE 的 SP☆11・12 谱面。'),

'SP☆12 %(n)s채보 기록 기준': (
    'Based on %(n)s SP☆12 chart records',
    'SP☆12 %(n)s 譜面の記録に基づく',
    '基于 %(n)s 个 SP☆12 谱面的记录'),

'SP☆12 채보의 EX SCORE 가 하나 이상 있어야 합산 BPI 를 계산할 수 있습니다. 데이터 동기화 앱이나 서열표에서 EX SCORE 를 넣어 주세요.': (
    'Total BPI needs at least one EX SCORE on an SP☆12 chart. Add EX SCOREs with the data sync app or on the rank tables.',
    '総合BPIの計算には SP☆12 譜面の EX SCORE が1つ以上必要です。データ同期アプリか序列表で EX SCORE を入力してください。',
    '计算总合 BPI 需要至少一个 SP☆12 谱面的 EX SCORE。请通过数据同步应用或难度表输入 EX SCORE。'),

'새 기록 하나로 추정 실력이 내려가면 합산 값도 내려갈 수 있어, BPIManager 처럼 지금까지의 최고값을 보여 줍니다. EX SCORE 를 손으로 낮추면 최고값을 지우고 다시 계산합니다.': (
    'A single new record can lower the estimated skill and thus the total, so, like BPIManager, the highest value so far is shown. Lowering an EX SCORE by hand clears that best value and recalculates.',
    '新しい記録1つで推定実力が下がると総合値も下がることがあるため、BPIManager と同様にこれまでの最高値を表示します。EX SCORE を手動で下げると最高値を消して再計算します。',
    '一条新记录可能使估计实力下降,从而使总合值下降,因此与 BPIManager 一样显示迄今为止的最高值。手动调低 EX SCORE 时会清除最高值并重新计算。'),

'지금 기록만으로 계산한 값: %(v)s': (
    'Value from current records only: %(v)s',
    '現在の記録のみで計算した値: %(v)s',
    '仅按当前记录计算的值: %(v)s'),

'채보별 값 갱신: %(d)s · 모델 상수: %(c)s': (
    'Per-chart values updated: %(d)s · Model constants: %(c)s',
    '譜面ごとの値の更新: %(d)s ・ モデル定数: %(c)s',
    '各谱面数值更新: %(d)s · 模型常数: %(c)s'),

'합산 BPI': (
    'Total BPI',
    '総合BPI',
    '总合 BPI'),

'합산 BPI 는 SP☆12 전 채보를 대상으로 합니다. 친 채보는 그 BPI 를, 안 친 채보는 친 기록으로 추정한 실력에서 예측한 값을 넣어 모읍니다.': (
    'Total BPI covers every SP☆12 chart. Played charts use their BPI; unplayed charts use a value predicted from the skill estimated from your records.',
    '総合BPIは SP☆12 の全譜面が対象です。プレー済みの譜面はその BPI を、未プレーの譜面は記録から推定した実力による予測値を使って集計します。',
    '总合 BPI 以全部 SP☆12 谱面为对象。已玩谱面使用其 BPI,未玩谱面使用根据记录估计的实力所预测的值进行汇总。'),

}

TRANS['SP☆12 EX SCORE 가 아직 없어 합산 BPI 를 계산하지 못했습니다. 데이터 동기화 앱이나 서열표에서 EX SCORE 를 넣으면 나타납니다.'] = (
    'No SP☆12 EX SCORE yet, so Total BPI could not be calculated. It will appear once you add EX SCOREs with the data sync app or on the rank tables.',
    'SP☆12 の EX SCORE がまだないため、総合BPIを計算できませんでした。データ同期アプリか序列表で EX SCORE を入力すると表示されます。',
    '尚无 SP☆12 的 EX SCORE,无法计算总合 BPI。通过数据同步应用或难度表输入 EX SCORE 后即会显示。')

TRANS['CPI 를 추정할 SP☆12 클리어 램프 기록이 부족합니다. 눌러서 자세한 조건을 볼 수 있습니다.'] = (
    'Not enough SP☆12 clear lamps to estimate CPI. Click to see the requirements.',
    'CPI を推定するための SP☆12 クリアランプの記録が足りません。クリックすると条件を確認できます。',
    '用于估算 CPI 的 SP☆12 通关灯记录不足。点击可查看具体条件。')
