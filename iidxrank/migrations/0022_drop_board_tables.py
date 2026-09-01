# -*- coding: utf-8 -*-
"""게시판 앱을 지우면서 남은 테이블을 걷어낸다.

board 앱은 쓰지 않기로 하고 코드째 지웠다. 그런데 앱을 지우는 것만으로는
테이블이 사라지지 않는다 — Django 는 없는 앱의 마이그레이션을 되돌릴 수 없어
board_* 테이블이 DB 에 그대로 남는다. 여기서 명시적으로 지운다.

**이 마이그레이션은 되돌릴 수 없다.** 테이블을 되살려도 내용은 돌아오지
않으므로 reverse 는 두지 않았다. 지우기 전 라이브 데이터는
board_board 2행(notice, freetalk), board_boardpost 1행(2022년 'test' 글),
나머지 3개 테이블은 0행이었다.

앱을 지운 마이그레이션은 iidxrank 에 두는 것이 맞다. board 앱 안에 두면
그 앱을 지우는 순간 이 파일도 같이 사라진다.
"""
from django.db import migrations

# 자식(외래키를 가진 쪽)부터 지운다. 순서를 뒤집으면 제약 때문에 실패한다.
TABLES = [
    'board_boardcomment',
    'board_boardpost',
    'board_bannedword',
    'board_banneduser',
    'board_board',
]

DROP = '\n'.join('DROP TABLE IF EXISTS `%s`;' % t for t in TABLES)

# 지운 앱의 마이그레이션 기록도 함께 정리한다. 남겨 두면 showmigrations 에
# 없는 앱이 계속 뜬다.
FORGET = "DELETE FROM django_migrations WHERE app = 'board';"


class Migration(migrations.Migration):

    dependencies = [
        ('iidxrank', '0021_healthcheck'),
    ]

    operations = [
        migrations.RunSQL(DROP, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(FORGET, reverse_sql=migrations.RunSQL.noop),
    ]
