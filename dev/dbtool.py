# -*- coding: utf-8 -*-
"""dev MySQL 컨테이너에 라이브 덤프를 올리고 상태를 확인하는 도구.

    python dev/dbtool.py up                      # 컨테이너 기동 + 준비될 때까지 대기
    python dev/dbtool.py import dumps/live.sql   # 덤프 적재 (기존 DB 를 비우고)
    python dev/dbtool.py status                  # 적재 결과 / charset / 행 수
    python dev/dbtool.py anonymize               # 개인정보 스크럽 (아래 설명)
    python dev/dbtool.py sql "SELECT ..."        # 임의 조회
    python dev/dbtool.py down                    # 컨테이너 정지 (볼륨 유지)
    python dev/dbtool.py reset                   # 볼륨까지 삭제하고 처음부터

개인정보에 대해
---------------
라이브 덤프에는 실제 사용자 245명의 이메일과 비밀번호 해시가 들어 있다.
이 PC 에 그대로 두는 것이 부담스러우면 적재 직후 anonymize 를 돌린다.
이메일을 user<id>@example.invalid 로, 비밀번호를 사용 불가 해시로 바꾼다.
서열표·기록 데이터는 건드리지 않으므로 갱신 명령 테스트에는 영향이 없다.
다만 **로그인 테스트는 못 하게 된다** — 그게 필요하면 익명화하지 말고,
대신 작업이 끝난 뒤 reset 으로 볼륨을 지워라.
"""
import argparse
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPOSE = os.path.join(BASE, 'dev', 'docker-compose.yml')
CONTAINER = 'bmapp-dev-mysql'
DB = 'iidxrank'
ROOTPW = 'devroot'


def mysql(sql, database=DB, quiet=False):
    """컨테이너 안의 mysql 클라이언트로 한 문장 실행."""
    cmd = ['docker', 'exec', '-i', CONTAINER, 'mysql',
           '-uroot', '-p' + ROOTPW, '--default-character-set=utf8mb4']
    if database:
        cmd.append(database)
    cmd += ['-e', sql]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    if r.returncode and not quiet:
        sys.stderr.write(r.stderr or '')
    return r


def wait_ready(timeout=180):
    print('MySQL 이 준비될 때까지 기다린다...', end='', flush=True)
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = subprocess.run(
            ['docker', 'exec', CONTAINER, 'mysqladmin', 'ping',
             '-h', '127.0.0.1', '-p' + ROOTPW],
            capture_output=True, text=True)
        if r.returncode == 0 and 'alive' in (r.stdout or ''):
            print(' 준비됨 (%.0fs)' % (time.time() - t0))
            return True
        print('.', end='', flush=True)
        time.sleep(2)
    print(' 시간 초과')
    return False


def cmd_up(a):
    subprocess.run(['docker', 'compose', '-f', COMPOSE, 'up', '-d'])
    if not wait_ready():
        sys.exit('컨테이너가 준비되지 않았다. docker logs %s 를 확인하라.' % CONTAINER)
    r = mysql('SELECT VERSION();', database=None)
    print('버전:', (r.stdout or '').strip().split('\n')[-1])


def cmd_down(a):
    subprocess.run(['docker', 'compose', '-f', COMPOSE, 'down'])


def cmd_reset(a):
    ans = input('볼륨까지 지운다. 적재한 데이터가 전부 사라진다. YES 입력: ').strip()
    if ans != 'YES':
        sys.exit('중단했다.')
    subprocess.run(['docker', 'compose', '-f', COMPOSE, 'down', '-v'])
    print('볼륨 삭제 완료. 다시 쓰려면 up 부터.')


def cmd_import(a):
    path = os.path.abspath(a.path)
    if not os.path.exists(path):
        sys.exit('파일이 없다: %s' % path)
    print('덤프: %s (%.1f MB)' % (path, os.path.getsize(path) / 1048576))

    # 덤프가 --databases 로 떠졌으면 CREATE DATABASE/USE 가 들어 있다.
    # 아니면 우리가 DB 를 만들어 두고 그 안에 넣어야 한다. 앞부분을 보고 판단한다.
    head = open(path, 'rb').read(65536).decode('utf-8', 'replace')
    has_create = 'CREATE DATABASE' in head.upper()
    print('덤프 형식: %s' % ('CREATE DATABASE 포함 (--databases)' if has_create
                             else '테이블만 (--databases 없음)'))

    print('기존 %s 스키마를 비운다...' % DB)
    mysql('DROP DATABASE IF EXISTS `%s`; CREATE DATABASE `%s`;' % (DB, DB),
          database=None)
    mysql("GRANT ALL ON `%s`.* TO 'iidxrank'@'%s'; FLUSH PRIVILEGES;" % (DB, '%'),
          database=None)

    print('적재 중... (덤프 크기에 따라 수 분)')
    t0 = time.time()
    cmd = ['docker', 'exec', '-i', CONTAINER, 'mysql',
           '-uroot', '-p' + ROOTPW, '--max_allowed_packet=256M']
    if not has_create:
        cmd.append(DB)
    with open(path, 'rb') as f:
        r = subprocess.run(cmd, stdin=f, capture_output=True)
    err = (r.stderr or b'').decode('utf-8', 'replace')
    # 비밀번호를 명령줄로 넘길 때 나오는 경고는 무시한다
    err = '\n'.join(l for l in err.split('\n')
                    if l.strip() and 'Using a password' not in l)
    if r.returncode:
        sys.exit('적재 실패:\n' + err)
    if err:
        print('경고:\n' + err)
    print('적재 완료 (%.0fs)' % (time.time() - t0))
    cmd_status(a)


def cmd_status(a):
    r = mysql("SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME "
              "FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='%s';" % DB,
              database=None)
    print('\n=== 데이터베이스 ===')
    print((r.stdout or '').strip())

    r = mysql("SELECT TABLE_NAME, TABLE_ROWS, TABLE_COLLATION "
              "FROM information_schema.TABLES WHERE TABLE_SCHEMA='%s' "
              "ORDER BY TABLE_ROWS DESC;" % DB, database=None)
    print('\n=== 테이블 (행 수는 InnoDB 추정치) ===')
    print((r.stdout or '').strip())

    print('\n=== 주요 테이블 실제 행 수 ===')
    for t in ('auth_user', 'iidxrank_player', 'iidxrank_song',
              'iidxrank_ranktable', 'iidxrank_rankcategory',
              'iidxrank_rankitem', 'iidxrank_playrecord'):
        r = mysql('SELECT COUNT(*) FROM `%s`;' % t, quiet=True)
        n = (r.stdout or '').strip().split('\n')[-1] if r.returncode == 0 else '(없음)'
        print('  %-28s %s' % (t, n))

    print('\n=== 기록된 마이그레이션 ===')
    r = mysql('SELECT app, COUNT(*) FROM django_migrations GROUP BY app;', quiet=True)
    print((r.stdout or '').strip() if r.returncode == 0
          else '  django_migrations 테이블 없음')


def cmd_anonymize(a):
    print('이메일과 비밀번호를 스크럽한다. 서열표·기록은 건드리지 않는다.')
    if input('계속하려면 YES 입력: ').strip() != 'YES':
        sys.exit('중단했다.')
    # 느낌표로 시작하는 해시를 Django 는 '사용 불가 비밀번호' 로 취급한다.
    mysql("UPDATE auth_user SET email = CONCAT('user', id, '@example.invalid'), "
          "password = CONCAT('!', id);")
    r = mysql('SELECT COUNT(*) FROM auth_user;')
    print('auth_user %s행 스크럽 완료. 이제 이 DB 로는 로그인할 수 없다.'
          % (r.stdout or '').strip().split('\n')[-1])


def cmd_sql(a):
    r = mysql(a.query)
    print(r.stdout or '')


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('up').set_defaults(fn=cmd_up)
    sub.add_parser('down').set_defaults(fn=cmd_down)
    sub.add_parser('reset').set_defaults(fn=cmd_reset)
    sub.add_parser('status').set_defaults(fn=cmd_status)
    sub.add_parser('anonymize').set_defaults(fn=cmd_anonymize)
    p = sub.add_parser('import')
    p.add_argument('path')
    p.set_defaults(fn=cmd_import)
    p = sub.add_parser('sql')
    p.add_argument('query')
    p.set_defaults(fn=cmd_sql)
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
