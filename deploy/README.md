# 라이브 서버 배포 (Docker)

Apache 가 mod_wsgi 로 파이썬을 직접 품던 구성에서, Apache 는 TLS 만 끊고
컨테이너로 넘기는 구성으로 바꾼다. MySQL 은 호스트에 그대로 둔다.

```
인터넷 → Apache(443, TLS)
           ├─ /media/  → /srv/beatmania/media (파일 직접)
           └─ 그 외    → 127.0.0.1:8731 → 컨테이너 gunicorn → 호스트 MySQL:3306
```

---

## 처음 한 번만

### 1. 호스트 준비

```bash
sudo mkdir -p /srv/beatmania/media
sudo chown -R 10001:10001 /srv/beatmania/media   # 컨테이너의 uid
```

기존 업로드본이 있으면 옮긴다. **소유자를 반드시 바꾼다** — 안 그러면
프로필 사진 업로드가 조용히 실패한다.

```bash
sudo rsync -a /기존/경로/media/ /srv/beatmania/media/
sudo chown -R 10001:10001 /srv/beatmania/media
```

### 2. MySQL 접속 허용

컨테이너에서 오는 접속은 MySQL 에게 `localhost` 가 아니라 도커 브리지
대역(보통 `172.17.0.x`)에서 온 것으로 보인다. 기존 `'iidxrank'@'localhost'`
권한만으로는 거부된다.

```sql
CREATE USER 'iidxrank'@'172.17.%' IDENTIFIED BY '기존과 같은 비밀번호';
GRANT ALL PRIVILEGES ON iidxrank.* TO 'iidxrank'@'172.17.%';
FLUSH PRIVILEGES;
```

MySQL 이 `127.0.0.1` 에만 묶여 있으면 `bind-address` 를 넓혀야 한다.
같은 호스트에 Nextcloud 등 다른 데이터가 있으므로 `0.0.0.0` 으로 열지 말고
도커 브리지 주소만 추가한다.

```ini
# /etc/mysql/mysql.conf.d/mysqld.cnf
bind-address = 127.0.0.1,172.17.0.1
```

### 3. `.env`

```bash
cp .env.example .env
$EDITOR .env
```

기존 운영 `.env` 에서 값을 가져오되 **다음 넷은 반드시 확인한다.**

| 키 | 값 | 이유 |
|---|---|---|
| `DB_HOST` | `host.docker.internal` | 컨테이너에서 호스트 MySQL 로 |
| `DB_CHARSET` | `utf8mb4` | `utf8` 은 utf8mb3 별칭이라 이모지에서 깨진다 |
| `DJANGO_BEHIND_PROXY` | `true` | Apache 가 TLS 를 끊는다 |
| `DJANGO_DEBUG` | `false` | |

`DJANGO_SECRET_KEY` 는 **기존 값을 그대로 옮긴다.** 새로 만들면 전 사용자의
세션이 끊겨 269명이 한꺼번에 재로그인해야 한다.

### 4. Apache

```bash
sudo cp deploy/apache-beatmania.conf.example \
        /etc/apache2/sites-available/beatmania.app.conf
sudo $EDITOR /etc/apache2/sites-available/beatmania.app.conf   # 인증서 경로 확인
sudo a2enmod proxy proxy_http headers
sudo apache2ctl configtest
sudo systemctl reload apache2
```

기존 `WSGIDaemonProcess` / `WSGIScriptAlias` 줄은 **지운다.** 남겨 두면 어느
쪽이 응답했는지 알 수 없어 문제를 못 찾는다.

---

## 배포할 때마다

```bash
cd /경로/beatmania.app
git pull
docker compose build
docker compose run --rm app python manage.py migrate    # 아래 주의 참고
docker compose up -d
docker compose logs -f app
```

`build` 와 `up` 사이에 `migrate` 를 끼우는 이유: 새 코드가 아직 없는 컬럼을
읽으면 500 이 난다. 반대로 컨테이너 시작 시 자동으로 migrate 하게 두면
`--build` 한 번에 되돌릴 수 없는 변경이 조용히 지나간다.

### 첫 배포에서 적용될 마이그레이션 — 되돌릴 수 없는 것 둘

2026-09-01 덤프 기준으로 라이브는 `iidxrank/0019_machinestatus`,
`update/0004_auto_20160716_0133` 까지 적용돼 있다. 밀린 것은 여섯 개다.

| | 내용 | 되돌리기 |
|---|---|---|
| `iidxrank/0020_player_avatar` | 프로필 사진 컬럼 추가 | 가능 |
| `iidxrank/0021_healthcheck` | 헬스체크 결과 테이블 추가 | 가능 |
| `iidxrank/0022_drop_board_tables` | 게시판 테이블 DROP | **불가** |
| `iidxrank/0023_remove_unused_ranktables` | SP12TEST · SP10R 와 그 조회 기록 삭제 | **불가** |
| `update/0005_commandrun` | 대시보드 명령 실행 기록 테이블 | 가능 |
| `update/0006_auto_20260901_1822` | 위 테이블 필드 조정 | 가능 |

`0023` 은 두 서열표의 카테고리·곡 배치·조회 기록(각각 176건, 75건)을 지운다.
**곡(Song)과 사용자 플레이 기록(PlayRecord)은 남는다** — 이 두 표에만 있고
다른 표에 없는 곡은 0개였다.

**migrate 전에 반드시 덤프를 뜬다.**

```bash
mysqldump --no-tablespaces -u iidxrank -p iidxrank | gzip > ~/iidxrank_$(date +%F).sql.gz
```

`--no-tablespaces` 가 없으면 `PROCESS` 권한이 없다며 실패한다. 그렇다고
전역 `PROCESS` 를 주면 같은 서버의 다른 서비스 쿼리까지 들여다볼 수 있게
되므로 주지 않는다.

---

## 정기 실행

컨테이너 안에는 cron 이 없다. 호스트 cron 에서 넣는다.

```cron
# 헬스체크. /status/ 의 타임라인이 이걸로 채워진다.
*/5 * * * * cd /경로/beatmania.app && docker compose exec -T app python manage.py healthcheck >> /var/log/beatmania-health.log 2>&1
```

`-T` 가 없으면 cron 처럼 TTY 가 없는 환경에서 실패한다.

곡 데이터 갱신(`updateSongInfinitas`)은 관리자 대시보드에서 사람이 확인하며
돌리는 명령이라 cron 에 넣지 않는다.

---

## 확인

```bash
docker compose ps                 # STATUS 가 healthy 여야 한다
curl -I https://beatmania.app/    # 200
curl -I https://beatmania.app/static/css/refactor-style.css   # 200, 컨테이너가 낸다
curl -I https://beatmania.app/media/avatar/아무거나.png        # 200, Apache 가 낸다
```

`/media/` 가 404 면 Apache Alias 가 빠진 것이다. `DEBUG=False` 인 Django 는
미디어를 아예 처리하지 않으므로 컨테이너 탓이 아니다.

---

## 되돌리기

컨테이너만 되돌리는 것은 쉽다.

```bash
docker compose down
docker run ... beatmania-app:<이전 태그>       # 또는 git checkout 후 재빌드
```

다만 `0022` · `0023` 이 이미 적용됐다면 **DB 는 코드만 되돌려서 원상복구되지
않는다.** 그 경우 위에서 뜬 덤프로 복원한다.
