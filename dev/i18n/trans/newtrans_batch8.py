# -*- coding: utf-8 -*-
"""원문 문구를 다듬으면서 msgid 가 바뀐 것들.

원문이 바뀌면 msgid 가 통째로 달라져 기존 번역이 떨어져 나간다. 세 언어 모두
이미 'beatoraja' 와 프로젝트명을 쓰고 있었으므로 뜻은 그대로 옮긴다.
"""

TRANS = {

# 로드맵 머리말. 원문이 'IIDX INFINTIAS Rank Table'(오타 포함)이었는데,
# 사이트가 스스로를 부르는 이름은 beatmania.app 이라 그쪽으로 통일했다.
'beatmania.app 프로젝트의 개발 진행 상황과 앞으로 업데이트될 기능들입니다.': (
    'Development progress of the beatmania.app project and what is coming next.',
    'beatmania.app プロジェクトの開発状況と、今後追加予定の機能です。',
    'beatmania.app 项目的开发进展与今后将更新的功能。'),

# 흰숫 변환기 안내문. 한글 음차 '(비토라쟈)' 를 뺐다 - 게임 안에서도 밖에서도
# 통용되는 표기는 beatoraja 하나다. 번역문 세 개는 원래부터 음차가 없었다.
'beatoraja와 IIDX의 서든 플러스 수치를 서로 변환합니다.': (
    'Converts SUDDEN+ values between beatoraja and IIDX.',
    'beatoraja と IIDX のサドプラ数値を相互変換します。',
    '在 beatoraja 与 IIDX 的 SUDDEN+ 数值之间互相换算。'),
}
