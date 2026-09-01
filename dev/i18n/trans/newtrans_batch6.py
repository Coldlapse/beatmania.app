# -*- coding: utf-8 -*-
"""흰숫 변환기 UI 문구.

기존 카탈로그의 표기를 그대로 따른다. 게임 용어는 세 언어 모두 원문을 쓴다.
  리프트        LIFT
  투덱 서든     IIDX SUDDEN+
  비토라쟈 서든 beatoraja SUDDEN+
"""

TRANS = {

# --- 안내문 ---
'Beatoraja의 LITONE 계열 스킨 등 IIDX와 동일한 구조로 제작된 스킨에 대응합니다. 일부 LITONE 버전은 IIDX AC 계산식대로의 서든 계산을 지원하지만, 일부 버전은 Beatoraja의 서든 계산대로 작동합니다. 확인 후 이용해주세요.': (
    'This works with skins built to the same structure as IIDX, such as the '
    'LITONE family for beatoraja. Some LITONE versions calculate SUDDEN+ the '
    'way IIDX AC does, while others follow beatoraja\'s own calculation. '
    'Please check which one your skin uses before relying on this.',
    'beatoraja の LITONE 系スキンなど、IIDX と同じ構造で作られたスキンに対応します。'
    'LITONE の一部バージョンは IIDX AC の計算式どおりに SUDDEN+ を算出しますが、'
    '別のバージョンは beatoraja 独自の計算で動作します。ご確認のうえご利用ください。',
    '本工具适用于与 IIDX 结构相同的皮肤，例如 beatoraja 的 LITONE 系列。'
    '部分 LITONE 版本按 IIDX AC 的公式计算 SUDDEN+，另一部分版本则依照 '
    'beatoraja 自身的算法。请确认后再使用。'),

# --- 필드 라벨 ---
'레인 전체가 1000': (
    'the whole lane is 1000', 'レーン全体が 1000', '整条轨道为 1000'),
'리프트 위쪽만 1000': (
    'only above LIFT is 1000', 'LIFT より上だけが 1000', '仅 LIFT 以上为 1000'),
'IIDX 서든 플러스': ('IIDX SUDDEN+', 'IIDX SUDDEN+', 'IIDX SUDDEN+'),
'beatoraja 서든': ('beatoraja SUDDEN+', 'beatoraja SUDDEN+', 'beatoraja SUDDEN+'),
'서든 플러스': ('SUDDEN+', 'SUDDEN+', 'SUDDEN+'),
'서든': ('SUDDEN+', 'SUDDEN+', 'SUDDEN+'),

# --- 조작 ---
'덮개의 모서리를 끌거나, 덮개 안의 숫자를 직접 입력하세요. 방향키로도 조절됩니다.': (
    'Drag the edge of a cover, or type a number inside it. Arrow keys work too.',
    'カバーの端をドラッグするか、カバー内の数値を直接入力してください。'
    '矢印キーでも調整できます。',
    '拖动遮罩的边缘，或直接在遮罩内输入数值。方向键同样可以调节。'),
'리프트를 바꿔도 보이는 넓이 유지': (
    'Keep the visible area when LIFT changes',
    'LIFT を変えても見える範囲を保つ',
    '改变 LIFT 时保持可见范围'),
'초기화': ('Reset', 'リセット', '重置'),

# --- 작동 원리 ---
'작동 원리와 계산식': (
    'How it works, and the formulas', '仕組みと計算式', '工作原理与计算公式'),

'IIDX는 레인 전체 높이를 1000으로 본다. 서든 플러스는 위에서 내려오는 덮개의 높이이고, 리프트는 아래에서 올라오는 덮개의 높이다. 둘 다 같은 1000 기준의 절대값이라, 보이는 넓이는 <b>1000 − 서든 − 리프트</b>가 된다.': (
    'IIDX treats the full height of the lane as 1000. SUDDEN+ is the height of '
    'the cover coming down from the top, and LIFT is the height of the cover '
    'rising from the bottom. Both are absolute values against that same 1000, '
    'so the visible area is <b>1000 − SUDDEN+ − LIFT</b>.',
    'IIDX はレーン全体の高さを 1000 とみなします。SUDDEN+ は上から降りてくる'
    'カバーの高さ、LIFT は下から上がってくるカバーの高さです。どちらも同じ '
    '1000 を基準にした絶対値なので、見える範囲は <b>1000 − SUDDEN+ − LIFT</b> '
    'になります。',
    'IIDX 把整条轨道的高度视为 1000。SUDDEN+ 是从上方降下的遮罩高度，'
    'LIFT 是从下方升起的遮罩高度。两者都是以同一个 1000 为基准的绝对值，'
    '因此可见范围为 <b>1000 − SUDDEN+ − LIFT</b>。'),

'beatoraja는 다르다. 리프트로 잘려 나간 뒤 <b>남은 영역</b>을 다시 1000으로 놓고 서든을 센다. 그래서 리프트가 0이 아니면 화면은 똑같은데 숫자만 달라진다. 위의 두 필드가 언제나 같은 모양인데 숫자가 다른 것이 그 때문이다.': (
    'beatoraja is different. It takes the <b>area left over</b> after LIFT has '
    'cut into the lane and treats that as 1000 again, then counts SUDDEN+ '
    'against it. So whenever LIFT is not zero, the screen looks identical but '
    'the number differs. That is why the two fields above always match in shape '
    'yet show different numbers.',
    'beatoraja は異なります。LIFT で切り取られたあとに<b>残った領域</b>を'
    'あらためて 1000 とみなし、そこから SUDDEN+ を数えます。そのため LIFT が '
    '0 でなければ、画面は同じなのに数値だけが変わります。上の二つのフィールドが'
    '常に同じ形なのに数値が違うのはこのためです。',
    'beatoraja 则不同。它把被 LIFT 截去之后<b>剩余的区域</b>重新视为 1000，'
    '再据此计算 SUDDEN+。因此只要 LIFT 不为 0，画面完全相同而数值却不同。'
    '上方两个区域形状始终一致、数字却不一样，原因正在于此。'),

'되돌리는 쪽에 <code>ceil</code>을 쓰는 이유가 있다. 게임이 실제로 하는 계산은 beatoraja → IIDX 방향의 내림뿐이므로, IIDX 수치 S를 얻으려면 그 식에 넣었을 때 S가 나오는 가장 작은 BMS 값을 찾아야 한다. 내림으로 되돌리면 리프트에 따라 한 칸 모자란 값이 나온다.': (
    'There is a reason <code>ceil</code> appears on the way back. The only '
    'calculation the game itself performs is the rounding-down in the '
    'beatoraja → IIDX direction, so to land on an IIDX value of S you need the '
    'smallest BMS value that yields S when fed into that formula. Rounding down '
    'on the way back leaves you one short at some LIFT values.',
    '戻す側に <code>ceil</code> を使うのには理由があります。ゲームが実際に'
    '行う計算は beatoraja → IIDX 方向の切り捨てだけなので、IIDX の値 S を'
    '得るには、その式に入れたときに S になる最小の BMS 値を求める必要が'
    'あります。切り捨てで戻すと、LIFT によっては 1 だけ足りない値になります。',
    '回算时使用 <code>ceil</code> 是有原因的。游戏本身执行的运算只有 '
    'beatoraja → IIDX 方向的向下取整，因此若要得到 IIDX 数值 S，'
    '就必须找出代入该公式后能得出 S 的最小 BMS 值。'
    '若回算时也向下取整，在某些 LIFT 下会少一格。'),

'넓이를 유지한 채 리프트만 변경': (
    'Change LIFT only, keeping the visible area',
    '見える範囲を保ったまま LIFT だけ変更',
    '保持可见范围，仅改变 LIFT'),
}
