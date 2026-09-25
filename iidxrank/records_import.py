# -*- coding: utf-8 -*-
"""게임 기록(Reflux 의 tracker.tsv)을 서열표 기록으로 옮긴다.

들어오는 길은 둘이다 — 웹 /sync/ 에서 사용자가 파일을 올리는 것과, 게임 옆에
상주하는 동기화 앱이 파일이 바뀔 때마다 API 로 보내는 것. 둘 다 **같은 파일**
을 보내고 여기 한 벌로 처리한다. 파싱·곡 매칭·반영 규칙을 앱에 두면 앱을 새로
배포해야 고칠 수 있다. 서버에 두면 배포 한 번이다.

tracker.tsv
  Reflux(olji/Reflux, MIT)의 Tracker.cs 가 쓴다. 곡마다 한 줄, 채보 슬롯
  (SPB SPN SPH SPA SPL DPN DPH DPA DPL)마다 8열:
      Unlocked, Rating(=게임 레벨), Lamp, Letter, EX Score, Miss Count,
      Note Count, DJ Points
  기록이 없는 채보는 8열이 비어 있다. **곡 ID 열은 없다** — 제목으로 맞춘다.

곡 매칭
  (제목, 채보 타입)으로 찾는다. 라이브 곡 4,410채보를 게임 곡 ID 가 붙은
  외부 목록(Tachi)과 대조했을 때 정규화 제목 + 타입 + 레벨로 99.6% 가
  한 번에 맞았고, 나머지는 겉모양이 같은 다른 유니코드 문자(아래 _CONFUSABLE)
  였다(2026-09-26 실측). 순서:
    1. 원제목 그대로 (대소문자 포함) — 'Take Me Higher' 와 'take me higher'
       는 다른 곡이다. 원제목 기준으로는 중복이 0 이다
    2. 정규화 제목 — 기호·공백·전각/반각·대소문자 차이를 흡수
    3. 정규화 제목이 여러 곡에 걸리면 레벨로 가린다. 그래도 둘 이상이면
       맞추지 않는다(틀린 곡에 쓰는 것보다 안 쓰는 것이 낫다)

반영 규칙
  **더 좋을 때만 올린다.** 램프도 등급도 각각 max. 손으로 넣은 기록이 게임
  기록보다 높으면 그대로 둔다 — 사용자가 일부러 넣은 값을 기계가 깎지 않는다.
  같은 파일을 여러 번 보내도 결과가 같다(멱등). 앱이 파일이 바뀔 때마다
  통째로 보내도 되는 이유다.

서열표에 있는 채보만(레벨 10 이상) 다룬다. 곡 DB 에 그것만 있다.
"""
import html
import re
import unicodedata

from django.db import transaction
from django.utils.translation import gettext as _

from iidxrank import models

SLOTS = ('SPN', 'SPH', 'SPA', 'SPL', 'DPN', 'DPH', 'DPA', 'DPL')   # SPB 는 버린다
MIN_LEVEL = 10

# Reflux Lamp → playclear (iidxrank/iidx.py 의 getclearstring 순서)
LAMP = {'NP': 0, 'F': 1, 'AC': 2, 'EC': 3, 'NC': 4, 'HC': 5, 'EX': 6,
        'FC': 7, 'PFC': 7}
# Reflux Grade → playscore (서열표 편집의 data-rank 순서: F E D C B A AA AAA MAX)
GRADE = {'F': 0, 'E': 1, 'D': 2, 'C': 3, 'B': 4, 'A': 5, 'AA': 6, 'AAA': 7}
GRADE_MAX = 8

# 들어오는 파일 한도. 실제 tracker.tsv 는 수백 KB 로 본다(실물로 재지 못함).
# API 경로는 Django 기본 DATA_UPLOAD_MAX_MEMORY_SIZE(2.5MB)가 먼저 막는다 — 역시 400.
MAX_BYTES = 4 * 1024 * 1024

# 겉모양은 같고 코드가 다른 글자. 곡 DB(textage)와 게임 쪽 제목이 서로 다른
# 글자를 쓴 경우가 실측으로 두 곡 있었다(uәn, POLꓘAMAИIA).
_CONFUSABLE = str.maketrans({
    'ә': 'ə',   # CYRILLIC SMALL SCHWA → LATIN SMALL SCHWA
    'ꓘ': 'Ʞ',   # LISU LETTER KHA → LATIN CAPITAL TURNED K
})
_STRIP = re.compile(
    r'[\s　・･\-‐―~〜～!！?？\'"’“”.,、。:：;/\\()（）\[\]【】「」『』<>'
    r'＊*†♪☆★♥♡&＆#＃%@_+=|]')


def norm_title(t):
    t = html.unescape(t or '').translate(_CONFUSABLE)
    t = unicodedata.normalize('NFKC', t).lower()
    return _STRIP.sub('', t)


class TsvError(ValueError):
    """파일이 tracker.tsv 가 아니다. 사용자에게 그대로 보여 줄 문장을 담는다."""


def _int(s):
    try:
        return int(s)
    except (TypeError, ValueError):
        return 0


def parse(text):
    """tracker.tsv 본문 → [(제목, 슬롯, 레벨, playclear, playscore)].

    기록이 없는 채보(램프 NP 이고 점수 0)와 레벨 10 미만은 여기서 버린다.
    """
    lines = text.lstrip('﻿').splitlines()
    if not lines:
        raise TsvError(_('빈 파일입니다.'))
    head = {name.strip(): i for i, name in enumerate(lines[0].split('\t'))}
    if 'title' not in head or 'SPA Lamp' not in head:
        raise TsvError(_('tracker.tsv 형식이 아닙니다. Reflux 가 만든 파일을 올려 주세요.'))

    out = []
    for line in lines[1:]:
        f = line.split('\t')
        title = f[head['title']] if head['title'] < len(f) else ''
        if not title:
            continue
        for slot in SLOTS:
            col = lambda c: f[head['%s %s' % (slot, c)]] \
                if head.get('%s %s' % (slot, c), 1 << 30) < len(f) else ''
            lamp = col('Lamp').strip()
            if lamp == '':
                continue                    # 이 곡에 이 채보가 없다
            level = _int(col('Rating'))
            if level < MIN_LEVEL:
                continue
            clear = LAMP.get(lamp)
            if clear is None:
                continue                    # 모르는 램프 — 추측하지 않는다
            ex = _int(col('EX Score'))
            notes = _int(col('Note Count'))
            if clear == 0 and ex == 0:
                continue                    # 안 친 채보
            if notes > 0 and ex >= notes * 2:
                grade = GRADE_MAX
            else:
                grade = GRADE.get(col('Letter').strip(), 0)
            out.append((title, slot, level, clear, grade))
    return out


class _Index:
    """곡 DB 를 한 번 읽어 (제목, 타입) 조회표를 만든다. 요청당 한 번."""

    def __init__(self):
        self.exact = {}
        self.normed = {}
        for sid, title, ty, lv in (models.Song.objects
                                   .filter(songtype__in=SLOTS)
                                   .values_list('id', 'songtitle', 'songtype', 'songlevel')):
            self.exact.setdefault((title, ty), []).append((sid, lv))
            self.normed.setdefault((norm_title(title), ty), []).append((sid, lv))

    def find(self, title, slot, level):
        hit = self.exact.get((title, slot))
        if hit and len(hit) == 1:
            return hit[0][0]
        cands = self.normed.get((norm_title(title), slot), [])
        if len(cands) > 1:
            cands = [c for c in cands if c[1] == level]
        return cands[0][0] if len(cands) == 1 else None


def apply(user, text, source):
    """파일 하나를 반영하고 요약을 돌려준다.

    요약: {'charts', 'created', 'improved', 'unchanged', 'unmatched', 'unmatched_titles'}
    unmatched_titles 는 앞 20개만 — 사람이 보고 곡 DB 를 고칠 단서다.
    """
    from iidxrank.rankpage import newplayer

    rows = parse(text)
    index = _Index()
    player = newplayer(user)

    matched = {}                      # song_id → (clear, grade). 같은 채보가 두 번 나오면 좋은 쪽
    missing = []
    for title, slot, level, clear, grade in rows:
        sid = index.find(title, slot, level)
        if sid is None:
            missing.append('%s [%s %d]' % (title, slot, level))
            continue
        c0, g0 = matched.get(sid, (0, 0))
        matched[sid] = (max(c0, clear), max(g0, grade))

    created = improved = unchanged = 0
    with transaction.atomic():
        have = {pr.song_id: pr for pr in
                models.PlayRecord.objects.select_for_update()
                .filter(player=player, song_id__in=list(matched))}
        new, changed = [], []
        for sid, (clear, grade) in matched.items():
            pr = have.get(sid)
            if pr is None:
                new.append(models.PlayRecord(player=player, song_id=sid,
                                             playclear=clear, playscore=grade))
                continue
            c = max(pr.playclear or 0, clear)
            g = max(pr.playscore or 0, grade)
            if (c, g) == (pr.playclear, pr.playscore):
                unchanged += 1
                continue
            pr.playclear, pr.playscore = c, g
            changed.append(pr)
        models.PlayRecord.objects.bulk_create(new)
        models.PlayRecord.objects.bulk_update(changed, ['playclear', 'playscore'])
        created, improved = len(new), len(changed)
        models.RecordSync.objects.create(
            user=user, source=source, charts=len(rows), created=created,
            improved=improved, unmatched=len(missing))

    return {'charts': len(rows), 'created': created, 'improved': improved,
            'unchanged': unchanged, 'unmatched': len(missing),
            'unmatched_titles': missing[:20]}
