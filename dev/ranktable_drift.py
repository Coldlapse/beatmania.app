# -*- coding: utf-8 -*-
"""개발용 픽스처 — 서열표를 일부러 어긋나게 만들어 확인 프롬프트를 재현한다.

왜 필요한가
-----------
`updateSongInfinitas --update` 는 구글 시트와 DB 를 비교해서 **위치가 바뀐 곡**
(Type 1)이 있을 때만 "어느 것을 적용할까요?" 하고 물어본다. 평소에는 둘이
일치하므로 이 프롬프트가 뜨지 않아, 대시보드의 질문–응답 흐름을 실데이터로
확인할 수가 없다. 그러면 "배포하고 나서 언젠가 뜰 때" 처음 확인하게 된다.

이 스크립트는 DB 쪽 곡 몇 개를 다른 카테고리로 옮겨 놓는다. 그러면 다음
`--update` 에서 시트와 어긋난 것으로 감지되어 프롬프트가 실제로 뜬다.
확인이 끝나면 `--restore` 로 되돌린다.

사용법
------
    python dev/ranktable_drift.py --status
    python dev/ranktable_drift.py --apply 8
    # → 대시보드에서 updateSongInfinitas --update 실행 → 프롬프트 확인
    python dev/ranktable_drift.py --restore

안전장치
--------
이 스크립트는 **서열표 데이터를 일부러 망가뜨린다.** 운영 DB 에서 돌리면
곡 배치가 어긋난 채로 사용자에게 노출된다. 그래서 DEBUG=False 이면 실행을
거부한다. 정말 필요하면 --force 를 줘야 하고, 그때도 한 번 더 확인을 묻는다.
"""
import argparse
import json
import os
import random
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

from iidxrank.models import RankCategory, RankItem  # noqa: E402

# 되돌리기 정보를 여기에 남긴다. 저장소에 커밋하지 않는다(.gitignore).
STATE = os.path.join(BASE, 'dev', '.drift_state.json')


def guard(force):
    if getattr(settings, 'DEBUG', False):
        return
    if not force:
        sys.exit(
            '거부: DEBUG=False 인 환경이다. 이 스크립트는 서열표를 일부러\n'
            '어긋나게 만들기 때문에 운영 DB 에서 돌리면 안 된다.\n'
            '정말 필요하면 --force 를 붙여라.')
    ans = input('운영으로 보이는 환경이다. 서열표를 망가뜨린다. 계속하려면 '
                'YES 를 입력: ').strip()
    if ans != 'YES':
        sys.exit('중단했다.')


def status():
    if not os.path.exists(STATE):
        print('어긋난 항목 없음 (드리프트 미적용).')
        return
    with open(STATE, encoding='utf-8') as f:
        saved = json.load(f)
    print('적용된 드리프트: %d건' % len(saved))
    for row in saved:
        item = RankItem.objects.filter(pk=row['item']).first()
        now = item.rankcategory.categoryname if item else '(삭제됨)'
        mark = '그대로' if now == row['to_name'] else '되돌아감/변경됨'
        print('  %-38s %s → %s   현재: %s (%s)'
              % (row['song'], row['from_name'], row['to_name'], now, mark))


def apply_drift(count, force):
    guard(force)
    if os.path.exists(STATE):
        sys.exit('이미 드리프트가 적용돼 있다. 먼저 --restore 로 되돌려라.')

    # 카테고리가 둘 이상인 서열표만 대상으로 한다
    tables = {}
    for cat in RankCategory.objects.select_related('ranktable').all():
        tables.setdefault(cat.ranktable_id, []).append(cat)
    candidates = [(tid, cats) for tid, cats in tables.items() if len(cats) >= 2]
    if not candidates:
        sys.exit('카테고리가 2개 이상인 서열표가 없다. 먼저 갱신을 한 번 돌려라.')

    rnd = random.Random(20260901)   # 재현 가능하게 고정
    saved = []
    for tid, cats in candidates:
        # **시트가 배치한 항목만 고른다.**
        # 시트에 없는 곡을 옮겨봐야 다음 갱신에서 Type 2(시트에 없음)로 잡힐 뿐
        # Type 1(위치 변경)이 되지 않는다. 시트 매핑으로 들어온 항목은 info 에
        # 'via' 표식이 남으므로 그것으로 걸러낸다.
        items = list(RankItem.objects
                     .filter(rankcategory__ranktable_id=tid, info__contains='via')
                     .select_related('song', 'rankcategory'))
        if not items:
            continue
        rnd.shuffle(items)
        per_table = max(1, count // len(candidates))
        for item in items:
            if len([s for s in saved if s['table'] == tid]) >= per_table:
                break
            others = [c for c in cats if c.pk != item.rankcategory_id]
            if not others:
                continue
            target = rnd.choice(others)
            saved.append({
                'table': tid,
                'item': item.pk,
                'song': '%s (%s)' % (item.song.songtitle, item.song.songtype),
                'from': item.rankcategory_id,
                'from_name': item.rankcategory.categoryname,
                'to': target.pk,
                'to_name': target.categoryname,
            })
            item.rankcategory = target
            item.save(update_fields=['rankcategory'])

    with open(STATE, 'w', encoding='utf-8') as f:
        json.dump(saved, f, ensure_ascii=False, indent=1)

    print('드리프트 %d건 적용. 되돌리기 정보: %s' % (len(saved), STATE))
    print('')
    for row in saved:
        print('  %-38s %s → %s' % (row['song'], row['from_name'], row['to_name']))
    print('')
    print('이제 대시보드에서 updateSongInfinitas 를 --update 로 실행하면')
    print('위 곡들이 "위치가 변경된 곡" 목록으로 뜬다.')
    print('확인이 끝나면: python dev/ranktable_drift.py --restore')


def restore():
    if not os.path.exists(STATE):
        sys.exit('되돌릴 정보가 없다.')
    with open(STATE, encoding='utf-8') as f:
        saved = json.load(f)
    n = 0
    for row in saved:
        item = RankItem.objects.filter(pk=row['item']).first()
        if item is None:
            continue
        item.rankcategory_id = row['from']
        item.save(update_fields=['rankcategory'])
        n += 1
    os.remove(STATE)
    print('%d건 되돌렸다.' % n)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--apply', type=int, metavar='N',
                   help='곡 N개를 다른 카테고리로 옮긴다')
    g.add_argument('--restore', action='store_true', help='원래대로 되돌린다')
    g.add_argument('--status', action='store_true', help='현재 상태를 보여준다')
    ap.add_argument('--force', action='store_true',
                    help='DEBUG=False 환경에서도 실행 (위험)')
    a = ap.parse_args()

    if a.status:
        status()
    elif a.restore:
        restore()
    else:
        apply_drift(a.apply, a.force)


if __name__ == '__main__':
    main()
