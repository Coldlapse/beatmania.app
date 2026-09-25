# -*- coding: utf-8 -*-
"""CPI(추정) 페이지."""

TRANS = {

'CPI 를 계산할 기록이 부족합니다': (
    'Not enough records to estimate CPI', 'CPI を推定する記録が足りません', '记录不足，无法估算 CPI'),

'SP☆12 클리어 램프가 %(n)s채보 이상 있어야 추정할 수 있습니다.': (
    'An estimate needs clear lamps on at least %(n)s SP☆12 charts.',
    'SP☆12 のクリアランプが %(n)s 譜面以上必要です。',
    '需要至少 %(n)s 张 SP☆12 谱面的通关灯才能估算。'),

'SP☆12 %(n)s채보 기준': ('Based on %(n)s SP☆12 charts', 'SP☆12 %(n)s 譜面から', '基于 %(n)s 张 SP☆12 谱面'),

'공유': ('Share', '共有', '分享'),

'어떻게 계산하나요': ('How is this calculated?', '計算方法', '计算方法'),

'채보별 값은 <a href="https://cpi.makecir.com/" target="_blank" rel="noopener">cpi.makecir.com</a> 이 공개하는 램프별 적정CPI(달성률 %(half)s 지점)와 개인차도(%(mid)s 폭)입니다.': (
    'Per-chart values are the per-lamp appropriate CPI (%(half)s clear point) and individual-difference '
    'width (%(mid)s) published by <a href="https://cpi.makecir.com/" target="_blank" rel="noopener">cpi.makecir.com</a>.',
    '譜面ごとの値は <a href="https://cpi.makecir.com/" target="_blank" rel="noopener">cpi.makecir.com</a> '
    'が公開しているランプ別の適正CPI(達成率%(half)sの点)と個人差度(%(mid)sの幅)です。',
    '各谱面数值为 <a href="https://cpi.makecir.com/" target="_blank" rel="noopener">cpi.makecir.com</a> '
    '公开的各灯适正CPI(达成率 %(half)s 处)与个人差度(%(mid)s 的宽度)。'),

'각 채보·램프를 "달성했는가" 로 보고, 모든 기록을 가장 잘 설명하는 CPI 를 찾습니다(최대우도). ASSIST 는 FAILED 로, 기록 없는 채보는 뺍니다.': (
    'Each chart and lamp is treated as "achieved or not", and we find the CPI that best explains all '
    'records (maximum likelihood). ASSIST counts as FAILED; charts without records are skipped.',
    '各譜面・ランプを「達成したか」として扱い、全記録を最もよく説明する CPI を求めます(最尤推定)。'
    'ASSIST は FAILED として扱い、記録のない譜面は除きます。',
    '将每个谱面·灯视为"是否达成"，求出最能解释全部记录的 CPI(最大似然)。ASSIST 按 FAILED 处理，无记录的谱面不计。'),

'원래 CPI 는 약 3만 명의 램프와 직접 비교해 계산하므로 같은 값이 나오지 않습니다. 공개 사용자 9명과 비교했을 때 평균 13점, 가장 크게 35점 차이가 났습니다(2026-09-26).': (
    'The original CPI compares directly against the lamps of about 30,000 players, so the values '
    'differ. Against 9 public users the difference was 13 points on average and 35 at most (2026-09-26).',
    '本来の CPI は約3万人のランプと直接比較して計算するため、同じ値にはなりません。'
    '公開ユーザー9名と比べた差は平均13点、最大35点でした(2026-09-26)。',
    '原 CPI 是与约 3 万名玩家的灯直接比较计算的，因此数值不会相同。与 9 名公开用户比较，'
    '平均相差 13 分，最大相差 35 分(2026-09-26)。'),

'채보별 값 갱신: %(d)s': ('Per-chart values updated: %(d)s', '譜面別の値の更新: %(d)s', '谱面数值更新: %(d)s'),

'문제가 있으면 디스코드로 알려 주세요.': (
    'Please let us know on Discord if there is any problem.',
    '問題があれば Discord でお知らせください。', '如有问题请在 Discord 告诉我们。'),

'달성 난도가 높은 기록': ('Hardest achievements', '達成難度の高い記録', '达成难度高的记录'),

'채보마다 가장 높은 램프 하나를, 그 램프의 적정CPI 가 높은 순으로 보여 줍니다. 달성 확률은 이 CPI 의 플레이어가 그 램프를 달성할 확률입니다 — 낮을수록 실력에 비해 잘 해낸 기록입니다.': (
    'Your best lamp on each chart, sorted by that lamp\'s appropriate CPI. The chance is how likely a '
    'player at this CPI would achieve it — the lower, the more impressive for your level.',
    '譜面ごとの最高ランプを、そのランプの適正CPIが高い順に表示します。達成確率はこの CPI の'
    'プレイヤーがそのランプを達成する確率で、低いほど実力以上の記録です。',
    '按每个谱面的最高灯，以该灯的适正CPI从高到低显示。达成概率是该 CPI 的玩家达成此灯的概率，越低说明越超出实力。'),

'곡': ('Song', '曲', '曲目'),
'램프': ('Lamp', 'ランプ', '灯'),
'적정CPI': ('Appropriate CPI', '適正CPI', '适正CPI'),
'달성 확률': ('Chance', '達成確率', '达成概率'),
'클립보드에 CPI 공유 주소가 복사되었습니다!': (
    'The CPI share link has been copied to the clipboard!',
    'CPI の共有アドレスをクリップボードにコピーしました！', 'CPI 分享链接已复制到剪贴板！'),
}
