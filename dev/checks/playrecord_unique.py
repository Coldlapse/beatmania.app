"""기록 (player, song) 유일 제약과 저장 경로를 확인한다 — 마이그레이션 0030.

  1. 중복 쌍이 없다
  2. 같은 (player, song) 을 또 만들면 DB 가 막는다
  3. 서열표에서 램프·DJ RANK·EX SCORE 를 번갈아 저장해도 한 줄에 모인다(램프 저장이 실패하지 않는다)

    python dev/checks/playrecord_unique.py
"""
import json

import _bootstrap  # noqa: F401
import django

django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.db import IntegrityError, transaction  # noqa: E402
from django.db.models import Count  # noqa: E402
from django.test import Client  # noqa: E402

from iidxrank import models  # noqa: E402

fails = []


def check(name, cond, detail=''):
    print('%-4s %s%s' % ('OK' if cond else 'FAIL', name, (' — %s' % detail) if detail and not cond else ''))
    if not cond:
        fails.append(name)


dups = models.PlayRecord.objects.values('player', 'song').annotate(n=Count('id')).filter(n__gt=1).count()
check('중복 (player, song) 쌍 없음', dups == 0, str(dups))

u = User.objects.create_user('zz_pr_unique', password='x-Unused-123')
try:
    from iidxrank.rankpage import newplayer
    pl = newplayer(u)
    models.AccountSecurity.objects.update_or_create(user=u, defaults={'newrulepassed': True})
    song = models.Song.objects.filter(songtype='SPA', songlevel=12).order_by('id').first()
    models.PlayRecord.objects.create(player=pl, song=song, playclear=3)
    try:
        with transaction.atomic():
            models.PlayRecord.objects.create(player=pl, song=song, playclear=5)
        check('같은 줄을 또 만들면 DB 가 막는다', False)
    except IntegrityError:
        check('같은 줄을 또 만들면 DB 가 막는다', True)

    c = Client()
    c.force_login(u)
    post = lambda action, v: c.post('/modify/', {'action': action, 'v': json.dumps(v)}).json()
    r1 = post('edit', [{'id': song.id, 'clear': 6}])
    r2 = post('edit', [{'id': song.id, 'rank': 7}])
    r3 = post('exscore', {'id': song.id, 'exscore': 3000})
    rows = list(models.PlayRecord.objects.filter(player=pl, song=song).values_list('playclear', 'playscore', 'exscore'))
    check('램프·DJ RANK·EX SCORE 저장 모두 성공', [r1['code'], r2['code'], r3['code']] == [0, 0, 0], str([r1, r2, r3]))
    check('한 줄에 모인다', rows == [(6, 7, 3000)], str(rows))
    other = models.Song.objects.filter(songtype='SPA', songlevel=12).order_by('id')[1]
    r4 = post('exscore', {'id': other.id, 'exscore': 1234})
    check('기록 없는 채보에 EX SCORE 만 넣어도 한 줄 생성', r4['code'] == 0 and
          models.PlayRecord.objects.filter(player=pl, song=other).count() == 1)
finally:
    models.Player.objects.filter(user=u).delete()
    u.delete()

print('')
print('총 실패: %d' % len(fails))
