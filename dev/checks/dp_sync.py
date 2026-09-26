"""DP 서열표(zasa) 갱신을 확인한다 — update/parser_infinitas.py 의 _parse_zasa · _apply.

원본에는 묻지 않는다: 작은 가짜 run.php 를 넣는다. 반영은 임시 표(ZZDP12)에만 한다.

  1. 파싱: H/A/L 칸, 공식 ☆ 와 비공식 수치, HTML 엔티티, 레벨 거르기
  2. 매칭: 그 레벨의 (정규화 제목, 타입)이 정확히 한 곡일 때만
  3. 반영(SP 와 같은 규칙): 위치 변경은 관리자 확인, 같은 곡 중복은 하나로, 수치 분류 순서 다시 매김
  4. DP 는 RESET 하지 않는다(INFINITAS 전용곡 손작업 보존)
  5. 관리자 대시보드: '대상 표' 선택(all/sp/dp)

    python dev/checks/dp_sync.py
"""
import html as _html

import _bootstrap  # noqa: F401
import django

django.setup()

from iidxrank.models import RankCategory, RankItem, RankTable, Song  # noqa: E402
from update import parser_infinitas as pi  # noqa: E402
from update import prompt as _prompt  # noqa: E402
from update import runner  # noqa: E402

fails = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name, (' — %s' % detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


# 곡 DB 의 DP ☆12 채보 둘을 기준으로 쓴다
a, b = list(Song.objects.filter(songlevel=12, songtype='DPA').order_by('id')[:2])
row = '<tr><td class="rank">%s</td><td class="rank">%s</td><td class="rank">%s</td><td class="music">%s</td></tr>'
cell = '<a class="music" href="music.php?id=x"><span class="%s">☆%d (%s)</span></a>'
FIXTURE = '<table class="run"><tr><th colspan="4">x</th></tr>' + ''.join([
    row % ('-', cell % ('A', 12, '12.5'), '-', _html.escape(a.songtitle)),
    row % (cell % ('H', 11, '11.2'), cell % ('A', 12, '12.3'), '-', _html.escape(b.songtitle)),
    row % ('-', cell % ('A', 12, '12.0'), '-', 'zz 원본에만 있는 곡 &amp; 기호'),
]) + '</table>'


class Fake:
    status_code = 200
    text = FIXTURE
    encoding = 'utf-8'

    def raise_for_status(self):
        pass


real_get = pi.requests.get
pi.requests.get = lambda *x, **k: Fake()
real_ask = _prompt.ask
try:
    p = pi.IIDXSheetParser()
    rows = p._zasa_rows()
    print('=== 1. 파싱 ===')
    check('채보 4개(H 11 · A 12 셋)', len(rows) == 4, str(rows))
    check('HTML 엔티티를 푼 제목', any(r[0] == 'zz 원본에만 있는 곡 & 기호' for r in rows))
    check('타입·레벨·수치', (a.songtitle, 'DPA', 12, '12.5') in rows and (b.songtitle, 'DPH', 11, '11.2') in rows)

    print('=== 2. 매칭 ===')
    sheet = {'table_name': 'ZZDP12', 'table_title': 'ZZDP12', 'level': 12, 'default_type': 'DP', 'loader': 'zasa'}
    parsed, nfail = p._parse_zasa(sheet)
    check('그 레벨의 곡만 매칭(DPH 11 은 제외)', set(parsed) == {a.id, b.id}, str(parsed.keys()))
    check('분류 이름 = 원본 수치', parsed[a.id]['cat_name'] == '12.5' and parsed[b.id]['cat_name'] == '12.3')
    check('원본에만 있는 곡은 못 찾음으로', nfail == 1, str(nfail))

    print('=== 3. 반영 ===')
    RankTable.objects.filter(tablename='ZZDP12').delete()
    tb = RankTable.objects.create(tablename='ZZDP12', tabletitle='ZZDP12', level=12, type='DP')
    c_only = RankCategory.objects.create(ranktable=tb, categoryname='INFINITAS 전용곡', categorytype=1, sortindex=1)
    c121 = RankCategory.objects.create(ranktable=tb, categoryname='12.1', categorytype=1, sortindex=2)
    c123 = RankCategory.objects.create(ranktable=tb, categoryname='12.3', categorytype=1, sortindex=3)
    RankItem.objects.create(rankcategory=c121, song=a, info='')        # 관리자가 손으로 둔 곳
    RankItem.objects.create(rankcategory=c121, song=a, info='')        # 중복
    RankItem.objects.create(rankcategory=c123, song=b, info='')
    other = Song.objects.filter(songlevel=12, songtype='DPA').exclude(id__in=[a.id, b.id]).first()
    RankItem.objects.create(rankcategory=c_only, song=other, info='')  # 원본에 없는 전용곡
    asked = []
    _prompt.ask = lambda **kw: asked.append(kw) or ''                   # 넘기기(기본값)
    p.process_sheet(sheet, 'UPDATE')
    items = list(RankItem.objects.filter(rankcategory__ranktable=tb).select_related('rankcategory'))
    check('위치가 다르면 관리자에게 묻는다(SP 와 같다)', len(asked) == 1 and '1건' in asked[0]['question'],
          str([x.get('question') for x in asked]))
    check('넘기면 옮기지 않는다', any(i.song_id == a.id and i.rankcategory.categoryname == '12.1' for i in items))
    check('중복은 하나만 남는다', sum(1 for i in items if i.song_id == a.id) == 1)
    check('원본에 없는 전용곡은 그대로', any(i.song_id == other.id and i.rankcategory_id == c_only.id for i in items))
    _prompt.ask = lambda **kw: 'all'
    p.process_sheet(sheet, 'UPDATE')
    ia = RankItem.objects.get(rankcategory__ranktable=tb, song=a)
    check('전부 적용하면 원본 분류를 따른다', ia.rankcategory.categoryname == '12.5')
    order = list(RankCategory.objects.filter(ranktable=tb).order_by('sortindex').values_list('categoryname', 'sortindex'))
    check('수치 분류 순서를 다시 매긴다(전용곡은 아래)',
          [n for n, _ in order] == ['INFINITAS 전용곡', '12.1', '12.3', '12.5'] and order[0][1] < order[1][1], str(order))

    print('=== 4. RESET 거부 ===')
    before = RankItem.objects.filter(rankcategory__ranktable=tb).count()
    p._apply(sheet, parsed, 0, 'RESET')
    check('DP 는 RESET 대신 변동분 갱신(전용곡 보존)',
          RankItem.objects.filter(rankcategory__ranktable=tb, song=other).exists()
          and RankItem.objects.filter(rankcategory__ranktable=tb).count() == before)

    print('=== 5. 관리자 대시보드 ===')
    cmd = runner.COMMANDS_BY_NAME['updateSongInfinitas']
    opt = next((o for o in cmd.options if o.name == 'tables'), None)
    check("'대상 표' 선택지 all/sp/dp", opt is not None and [c[0] for c in opt.choices] == ['all', 'sp', 'dp'])
    kw, label = runner.build_kwargs(cmd, {'mode': 'update', 'tables': 'dp'})
    check('명령 인자로 --tables=dp 가 나간다', kw.get('tables') == 'dp' and kw.get('update') is True, str(kw))
    dp_sheets = [s['table_name'] for s in p.target_sheets if s['table_name'].startswith('DP')]
    check('대상 시트에 DP10·11·12', dp_sheets == ['DP12', 'DP11', 'DP10'], str(dp_sheets))
finally:
    pi.requests.get = real_get
    _prompt.ask = real_ask
    RankTable.objects.filter(tablename='ZZDP12').delete()

print('')
print('총 실패: %d' % len(fails))
