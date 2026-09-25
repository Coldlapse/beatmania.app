# -*- coding: utf-8 -*-
"""서비스 현황의 외부 감시탑 안내와 Cloudflare 상태 칸.

Cloudflare 거점 이름(Seoul, South Korea - (ICN) 등)은 감시탑이 주는 값을 그대로
싣고 번역하지 않는다.
"""

TRANS = {

'이 점검은 beatmania.app 안에서 스스로를 확인한 결과입니다. 사이트 자체가 내려가면 이 페이지도 열리지 않으므로, 바깥에 외부 감시탑을 따로 두었습니다. 외부 감시탑은 1분마다 사이트와 데이터베이스, Cloudflare 상태를 확인합니다.': (
    'These checks are beatmania.app checking itself. If the site goes down, this page '
    'goes down with it, so there is a separate external watchtower outside. It checks '
    'the site, the database and Cloudflare every minute.',
    'この点検は beatmania.app が自分自身を確認した結果です。サイトが落ちるとこのページも'
    '開けないため、外部に監視塔を別に置いています。外部監視塔は1分ごとにサイト・'
    'データベース・Cloudflare の状態を確認します。',
    '这些检查是 beatmania.app 对自身的检查。网站宕机时本页也无法打开，因此在外部另设了'
    '监控塔。外部监控塔每分钟检查网站、数据库和 Cloudflare 的状态。'),

'외부 감시탑 보기': ('View the external watchtower', '外部監視塔を見る', '查看外部监控塔'),
'외부 감시탑': ('external watchtower', '外部監視塔', '外部监控塔'),
'Cloudflare 상태': ('Cloudflare status', 'Cloudflare の状態', 'Cloudflare 状态'),
'관련 거점·서비스': ('Relevant locations and services', '関連拠点・サービス', '相关节点与服务'),
'데이터 출처': ('Data source', 'データ出典', '数据来源'),
'%(when)s 전 확인': ('checked %(when)s ago', '%(when)s前に確認', '%(when)s前确认'),
}
