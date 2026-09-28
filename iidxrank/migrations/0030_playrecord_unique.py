# (player, song) 중복 기록을 한 줄로 합친 뒤 유일 제약을 건다.
#
# 중복은 서열표에서 램프와 DJ RANK 를 거의 동시에 저장할 때 생겼다 — 한 줄에는 램프, 다른 줄에는 DJ RANK 가
# 들어 있는 모양이다(라이브 8쌍·5명, 2026-09-28). 합칠 때는 id 가 작은 줄을 남기고 각 값의 더 좋은 쪽을 쓴다:
#   playclear·playscore·exscore 는 큰 값(EX SCORE 는 None 이 아닌 것 중), playmiss 는 0 이 아닌 것 중 작은 값.
from django.db import migrations, models


def merge_duplicates(apps, schema_editor):
    PlayRecord = apps.get_model('iidxrank', 'PlayRecord')
    from django.db.models import Count
    pairs = (PlayRecord.objects.values('player_id', 'song_id')
             .annotate(n=Count('id')).filter(n__gt=1))
    for p in list(pairs):
        rows = list(PlayRecord.objects.filter(player_id=p['player_id'], song_id=p['song_id']).order_by('id'))
        keep, rest = rows[0], rows[1:]
        keep.playclear = max(r.playclear or 0 for r in rows)
        keep.playscore = max(r.playscore or 0 for r in rows)
        misses = [r.playmiss for r in rows if r.playmiss]
        keep.playmiss = min(misses) if misses else keep.playmiss
        exs = [r.exscore for r in rows if r.exscore is not None]
        keep.exscore = max(exs) if exs else None
        keep.save()
        PlayRecord.objects.filter(id__in=[r.id for r in rest]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('iidxrank', '0029_scoring_tables_copyright'),
    ]

    operations = [
        migrations.RunPython(merge_duplicates, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='playrecord',
            constraint=models.UniqueConstraint(fields=('player', 'song'), name='uniq_playrecord_player_song'),
        ),
    ]
