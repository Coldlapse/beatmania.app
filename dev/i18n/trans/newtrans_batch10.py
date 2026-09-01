# -*- coding: utf-8 -*-
"""변환기 경고문의 'Beatoraja' 를 소문자로 바꾸면서 msgid 가 달라진 것.

이 프로젝트의 표기는 소문자 beatoraja 하나로 통일한다 - 공식 표기가 그렇고,
같은 화면의 다른 문구(배지, 필드 라벨, 계산식 설명)가 이미 전부 소문자였다.
번역문 세 개는 원래부터 소문자였으므로 뜻과 글자 모두 그대로 옮긴다.
"""

TRANS = {

'beatoraja의 LITONE 계열 스킨 등 IIDX와 동일한 구조로 제작된 스킨에 대응합니다. '
'일부 LITONE 버전은 IIDX AC 계산식대로의 서든 계산을 지원하지만, 일부 버전은 '
'beatoraja의 서든 계산대로 작동합니다. 확인 후 이용해주세요.': (
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
}
