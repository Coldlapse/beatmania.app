# -*- coding: utf-8 -*-
"""BPI·CPI 데이터 출처와 감사 인사, 뱃지 풍선 도움말에서 '문제가 있으면 알려 주세요' 를 뺀 것."""

_A = ' target="_blank" rel="noopener"'
_MAIL = '<a href="mailto:beatmania.app@gmail.com">beatmania.app@gmail.com</a>'
_DISCORD = '<a href="https://discord.gg/RxjwbvWa8D"' + _A + '>'


def _credit(url, name):
    link = '<a href="%s"%s>%s</a>' % (url, _A, name)
    ko = (link + '의 데이터를 활용했습니다. 문제가 있다면 ' + _MAIL + ' 이나 ' + _DISCORD + '디스코드</a>로 '
          '문의해주시면 감사하겠습니다. 양질의 데이터 제공에 진심으로 감사드립니다.')
    return ko, (
        'This page uses data from ' + link + '. If you find a problem, please contact us at ' + _MAIL + ' or on '
        + _DISCORD + 'Discord</a>. We sincerely thank them for providing such high-quality data.',
        link + ' のデータを活用しています。問題がありましたら ' + _MAIL + ' または ' + _DISCORD + 'Discord</a> '
        'までお問い合わせいただけると幸いです。質の高いデータのご提供に心より感謝申し上げます。',
        '本页使用了 ' + link + ' 的数据。如有问题,请通过 ' + _MAIL + ' 或 ' + _DISCORD + 'Discord</a> '
        '联系我们,不胜感激。衷心感谢对方提供优质的数据。')


TRANS = {

'SP☆12 %(n)s채보의 EX SCORE 로 계산한 합산 BPI 입니다. 계산식과 채보별 값은 BPIManager(bpi2.poyashi.me)를 따릅니다.': (
    'Total BPI calculated from EX SCOREs on %(n)s SP☆12 charts. The formula and per-chart values follow BPIManager (bpi2.poyashi.me).',
    'SP☆12 %(n)s 譜面の EX SCORE から計算した総合BPIです。計算式と譜面ごとの値は BPIManager(bpi2.poyashi.me)に準拠しています。',
    '根据 %(n)s 个 SP☆12 谱面的 EX SCORE 计算的总合 BPI。计算公式和各谱面数值遵循 BPIManager(bpi2.poyashi.me)。'),

'SP☆12 %(n)s채보의 클리어 램프로 계산한 추정값입니다. 채보별 값은 cpi.makecir.com 의 공개 수치를 씁니다.': (
    'Estimated from clear lamps on %(n)s SP☆12 charts, using the per-chart values published by cpi.makecir.com.',
    'SP☆12 %(n)s 譜面のクリアランプから計算した推定値です。譜面ごとの値は cpi.makecir.com の公開値を使用しています。',
    '根据 %(n)s 个 SP☆12 谱面的通关灯计算的估算值。各谱面数值使用 cpi.makecir.com 公开的数据。'),

}

for _url, _name in (('https://bpi2.poyashi.me/', 'BPIManager (bpi2.poyashi.me)'),
                    ('https://cpi.makecir.com/', 'CPI (cpi.makecir.com)')):
    _ko, _tr = _credit(_url, _name)
    TRANS[_ko] = _tr
