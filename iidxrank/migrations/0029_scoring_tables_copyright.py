# 스코어 난이도표(SP10S·SP12S)의 좌하단 표기를 다른 서열표처럼 beatmania.app 으로 바꾼다.
# 표를 다시 만들지 않고 이미 있는 행만 고친다(update/management/commands/load_scoring_tables.py 와 같은 값).
from django.db import migrations


def forward(apps, schema_editor):
    apps.get_model('iidxrank', 'RankTable').objects.filter(tablename__in=['SP10S', 'SP12S']) \
        .update(copyright='beatmania.app')


class Migration(migrations.Migration):

    dependencies = [
        ('iidxrank', '0028_bpi'),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
