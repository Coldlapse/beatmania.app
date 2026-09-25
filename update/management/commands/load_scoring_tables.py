# -*- coding: utf-8 -*-
"""스코어 난이도표(SP10S · SP12S)를 데이터 파일에서 만든다.

    python manage.py load_scoring_tables            # 무엇이 매칭되는지만 보여 준다
    python manage.py load_scoring_tables --apply    # 서열표를 새로 만든다(있으면 갈아 끼운다)

원본은 구글 시트가 아니라 이미지(けんたんチャンネル 기준 スコア難易度表)라 자동으로
따라갈 곳이 없다. 사람이 옮겨 적은 update/data/scoring_sp*.tsv 가 원본이다. 표가
갱신되면 그 파일을 고치고 --apply 로 다시 만든다.

곡 매칭: 제목 끝의 † 는 LEGGENDARIA(SPL). 그 밖에는 같은 레벨의 SP 채보 중 SPA 를
먼저, 없으면 SPH 를 쓴다. 제목 자체에 † 가 들어간 곡(†渚の小悪魔…, DEATH†ZIGOQ)이
있어서, 끝의 † 를 떼고 못 찾으면 떼지 않은 제목으로 한 번 더 찾는다.
못 찾은 곡은 빼고 목록으로 보여 준다 — 틀린 곡에 넣는 것보다 비워 두는 것이 낫다.
"""
import io
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from iidxrank import models
from iidxrank.records_import import norm_title

DATA = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
TIERS = ['E', 'D', 'C', 'B', 'A', 'A+', 'S', 'S+']        # 쉬운 쪽이 작은 정렬값
COPYRIGHT = 'スコア難易度表: けんたんチャンネル基準 (2026年8月)'

TABLES = [
    {'file': 'scoring_sp10.tsv', 'name': 'SP10S', 'title': 'IIDX INFINITAS SP ☆10 Scoring Rank by KENTAN', 'level': 10,
     'copyright': COPYRIGHT},
    {'file': 'scoring_sp12.tsv', 'name': 'SP12S', 'title': 'IIDX INFINITAS SP ☆12 Scoring Rank by KENTAN', 'level': 12,
     'copyright': COPYRIGHT + ' / 協力 KKM* SOMORI NIKE.'},
]


def read(path):
    rows = []
    for line in io.open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line or line.startswith('#'):
            continue
        tier, title = line.split('\t', 1)
        if tier not in TIERS:
            raise ValueError('모르는 티어 %r: %s' % (tier, line))
        rows.append((tier, title.strip()))
    return rows


def match(rows, level):
    index = {}
    for sid, title, ty in (models.Song.objects
                           .filter(songlevel=level, songtype__in=('SPA', 'SPH', 'SPL'))
                           .values_list('id', 'songtitle', 'songtype')):
        index.setdefault(norm_title(title), {})[ty] = sid

    def find(title, types):
        hit = index.get(norm_title(title), {})
        for ty in types:
            if ty in hit:
                return hit[ty]
        return None

    def find_all(title, types):
        hit = index.get(norm_title(title), {})
        return [hit[ty] for ty in types if ty in hit]

    placed, missing, dup = {}, [], []
    for tier, title in rows:
        # 끝의 † 는 LEGGENDARIA 만 뜻한다. SPL 이 없으면 비운다 — 일반 채보로 넘기면
        # 같은 곡의 SPA 자리를 뺏는다(제목 비교는 † 를 지우므로 실제로 그랬다).
        types = ('SPL',) if title.endswith('†') else ('SPA', 'SPH')
        cands = [sid for sid in find_all(title, types) if sid not in placed]
        if not cands:
            if find_all(title, types):
                dup.append('%s / %s\t%s' % (placed[find_all(title, types)[0]], tier, title))
            else:
                missing.append('%s\t%s' % (tier, title))
            continue
        # 같은 제목이 두 티어에 있으면 같은 레벨의 다른 채보(A 와 H)다. 이미지에는 어느
        # 쪽이 H 인지 없어서, 먼저 나온 쪽을 SPA 로, 다음을 SPH 로 둔다 — 추정이다.
        if len(find_all(title, types)) > 1 and cands[0] != find_all(title, types)[0]:
            dup.append('추정 SPH  %s\t%s' % (tier, title))
        placed[cands[0]] = tier
    return placed, missing, dup


class Command(BaseCommand):
    help = '스코어 난이도표 SP10S·SP12S 를 update/data/scoring_sp*.tsv 에서 만든다.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='실제로 서열표를 만든다')

    def handle(self, *args, **options):
        for t in TABLES:
            rows = read(os.path.join(DATA, t['file']))
            placed, missing, dup = match(rows, t['level'])
            self.stdout.write('[%s] 목록 %d곡 → 매칭 %d, 못 찾음 %d, 중복 %d'
                              % (t['name'], len(rows), len(placed), len(missing), len(dup)))
            for m in missing:
                self.stdout.write('   못 찾음  ' + m)
            for d in dup:
                self.stdout.write('   중복     ' + d)
            if not options['apply']:
                continue
            with transaction.atomic():
                table, _ = models.RankTable.objects.update_or_create(
                    tablename=t['name'],
                    defaults={'tabletitle': t['title'], 'level': t['level'], 'type': 'SP',
                              'copyright': t['copyright'][:100]})
                models.RankItem.objects.filter(rankcategory__ranktable=table).delete()
                models.RankCategory.objects.filter(ranktable=table).delete()
                # 분류 이름은 'Tier S+' 처럼 원본 표기를 따른다.
                cats = {tier: models.RankCategory.objects.create(
                            ranktable=table, categoryname='Tier %s' % tier, categorytype=1,
                            sortindex=float(i + 1))
                        for i, tier in enumerate(TIERS)}
                models.RankItem.objects.bulk_create([
                    models.RankItem(rankcategory=cats[tier], song_id=sid, info='')
                    for sid, tier in placed.items()])
            self.stdout.write('   → %s 만듦 (%d곡)' % (t['name'], len(placed)))
