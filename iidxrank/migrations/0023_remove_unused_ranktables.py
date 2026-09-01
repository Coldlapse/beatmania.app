# -*- coding: utf-8 -*-
"""쓰지 않는 서열표 두 개(SP12TEST, SP10R)를 지운다.

SP12TEST 는 분류 결과를 대조해 보기 위한 시험용 표였고, 그 대조 명령
(compareRankTables / copyRankTable)을 이미 지웠다. SP10R 은 추천 곡 표인데
더 쓰지 않기로 했다.

같이 사라지는 것
  - 두 표의 카테고리와 곡 배치 (SP10R 13/43, SP12TEST 19/499)
  - 두 표의 조회 기록. RankTable 에 GenericRelation(HitCount) 이 걸려 있어
    표를 지우면 HitCount 와 그에 딸린 Hit 이 함께 지워진다
    (SP10R 176건, SP12TEST 75건).

**남는 것**
  - 곡(Song) 자체. 이 두 표에만 있고 다른 표에 없는 곡은 0개였다.
  - 사용자의 플레이 기록(PlayRecord). 곡에 매여 있고 표와 무관하다.

되돌릴 수 없다. 표를 다시 만들어도 곡 배치와 조회 기록은 돌아오지 않으므로
reverse 는 두지 않았다.
"""
from django.db import migrations

TABLES = ['SP12TEST', 'SP10R']


def drop_tables(apps, schema_editor):
    # 마이그레이션에서는 apps.get_model 을 써야 한다. 지금 코드의 모델을 쓰면
    # 나중에 모델이 바뀌었을 때 과거 마이그레이션이 깨진다.
    #
    # 다만 GenericRelation 을 통한 연쇄 삭제는 과거 모델에는 없다. 조회 기록은
    # content type 으로 직접 찾아 지운다.
    RankTable = apps.get_model('iidxrank', 'RankTable')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    HitCount = apps.get_model('hitcount', 'HitCount')

    rows = list(RankTable.objects.filter(tablename__in=TABLES))
    if not rows:
        return

    ct = ContentType.objects.filter(app_label='iidxrank',
                                    model='ranktable').first()
    if ct:
        HitCount.objects.filter(
            content_type=ct,
            object_pk__in=[str(r.pk) for r in rows]).delete()

    # 카테고리와 곡 배치는 FK CASCADE 로 함께 지워진다.
    RankTable.objects.filter(tablename__in=TABLES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('iidxrank', '0022_drop_board_tables'),
        ('hitcount', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(drop_tables, migrations.RunPython.noop),
    ]
