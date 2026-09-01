# 배포

컨테이너 하나를 리버스 프록시 뒤에 두고, DB 는 호스트에 있는 것을 그대로 씁니다.

```
인터넷 → 웹서버(443, TLS) ─┬─ /media/  → 파일 직접
                          └─ 그 외    → 127.0.0.1:<APP_PORT> → 컨테이너 gunicorn
                                                                    ↓
                                                              호스트 MySQL:3306
```

> 이 문서는 **어느 서버에나 적용되는 일반 절차**입니다. 특정 서버의 경로·계정·
> vhost 파일명 같은 것은 여기 적지 않습니다. 운영자는 자기 환경에 맞는 별도
> 문서를 따로 두시는 편이 좋습니다 — 저장소가 공개라면 특히 그렇습니다.

---

## 목차

- [설계 판단](#설계-판단)
- [처음 한 번만](#처음-한-번만)
- [배포할 때마다](#배포할-때마다)
- [자동 배포](#자동-배포)
- [정기 실행](#정기-실행)
- [확인](#확인)
- [되돌리기](#되돌리기)
- [자주 걸리는 것](#자주-걸리는-것)

---

## 설계 판단

배포 구성에는 갈림길이 여럿 있습니다. 왜 이쪽인지 먼저 적어 둡니다. 근거를 알아야
다음 사람이 함부로 뒤집지 않습니다.

### DB 를 컨테이너에 넣지 않습니다

호스트에 이미 MySQL 이 돌고 있고, 거기에 **다른 서비스의 데이터도 들어 있는**
상황을 전제합니다. 그것까지 컨테이너로 옮기는 것은 이 작업의 범위가 아니고,
잘못되면 잃는 것이 큽니다. 컨테이너는 호스트 DB 에 붙습니다.

컨테이너에서 호스트 DB 로 가는 길은 `host.docker.internal` 입니다. 리눅스에서는
기본 제공되지 않아 compose 의 `extra_hosts: host-gateway` 로 만들어 줍니다.
`172.17.0.1` 을 직접 적지 않는 이유는 **그 주소가 환경마다 다르기 때문**입니다.

### 정적 파일은 앱이 내고, 업로드 파일은 웹서버가 냅니다

| | 누가 내나 | 왜 그런가 |
|---|---|---|
| `/static/` | 컨테이너 (whitenoise) | 파일이 이미지 안에 있습니다. 웹서버에 별칭을 두면 **배포마다 호스트로 복사하는 단계**가 생깁니다 |
| `/media/` | 웹서버 (직접) | `DEBUG=False` 인 Django 는 미디어를 아예 처리하지 않습니다. 그리고 WSGI 워커가 이미지 전송에 묶이면 안 됩니다 |

정적 파일은 `collectstatic` 을 **빌드 시점에** 돌려 이미지에 굽습니다. 실행할 때
모으면 컨테이너가 뜰 때마다 같은 일을 반복하고, 읽기 전용 파일시스템에서는
아예 실패합니다.

### 마이그레이션을 컨테이너 시작 시 자동으로 돌리지 않습니다

`build` 와 `up` **사이에** 사람이 끼워 넣습니다.

- 자동으로 돌게 두면 **되돌릴 수 없는 변경이 배포 한 번에 조용히 지나갑니다**
- 반대로 `up` 뒤에 돌리면, 새 코드가 아직 없는 컬럼을 읽는 시간이 생겨 500 이 납니다

### 컨테이너를 바깥에 직접 노출하지 않습니다

포트를 `127.0.0.1` 에만 묶습니다. `0.0.0.0` 으로 열면 방화벽 설정과 무관하게
그 포트가 인터넷에서 그대로 열리는 사고가 납니다.

### 비루트로 돌립니다

이미지가 uid `10001` 로 낮춰 실행합니다. **호스트의 media 디렉터리 소유자를
이 uid 로 맞춰야 합니다.** 그러지 않으면 업로드가 조용히 실패합니다.

---

## 처음 한 번만

### 1. Docker 설치

`docker compose`(v2) 가 필요합니다. 배포판 기본 저장소의 `docker.io` 패키지에는
없는 경우가 많으므로 공식 저장소를 쓰시길 권합니다.

<details>
<summary><b>Ubuntu / Debian</b></summary>

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
     -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
     docker-buildx-plugin docker-compose-plugin
```

</details>

`sudo` 없이 쓰려면 그룹에 넣고 **다시 로그인**해야 합니다.

```bash
sudo usermod -aG docker "$USER"
# 로그아웃 후 재접속하세요. newgrp docker 로는 그 셸만 바뀝니다.
docker compose version      # v2.x 가 나와야 합니다
```

> `docker` 그룹은 사실상 root 권한입니다. 여럿이 쓰는 서버라면 rootless 모드를
> 고려하실 자리입니다.

브리지 게이트웨이 주소를 확인해 두세요. 아래 DB 권한 설정에서 씁니다.

```bash
ip -4 addr show docker0 | grep inet     # 보통 172.17.0.1
```

### 2. 디렉터리

```bash
# 업로드 파일. 컨테이너의 uid 로 소유자를 맞춥니다.
sudo mkdir -p /srv/beatmania/media
sudo chown -R 10001:10001 /srv/beatmania/media

# 앱 소스
sudo mkdir -p /srv/beatmania/app
sudo chown -R "$USER":"$USER" /srv/beatmania/app
git clone https://github.com/Coldlapse/beatmania.app.git /srv/beatmania/app
```

기존 업로드본이 있으면 옮기고 **소유자를 반드시 바꿔 주세요.**

```bash
sudo rsync -a /기존/경로/media/ /srv/beatmania/media/
sudo chown -R 10001:10001 /srv/beatmania/media
```

### 3. DB 접속 허용

컨테이너에서 오는 접속은 MySQL 에게 `localhost` 가 아니라 **도커 브리지
대역에서 온 것**으로 보입니다. 기존 `'사용자'@'localhost'` 권한만으로는 거부됩니다.

먼저 지금 무엇이 있는지 확인합니다.

```sql
SELECT user, host FROM mysql.user WHERE user = 'iidxrank';
```

브리지 대역용 권한을 만듭니다. **비밀번호는 기존과 같은 것을 씁니다.**

```sql
CREATE USER 'iidxrank'@'172.17.%' IDENTIFIED BY '기존과 같은 비밀번호';
GRANT ALL PRIVILEGES ON iidxrank.* TO 'iidxrank'@'172.17.%';
FLUSH PRIVILEGES;
```

MySQL 이 `127.0.0.1` 에만 묶여 있으면 브리지 주소를 추가합니다.
**같은 인스턴스에 다른 서비스의 데이터가 있다면 `0.0.0.0` 으로 열지 마세요.**

```ini
# my.cnf / mysqld.cnf
bind-address = 127.0.0.1,172.17.0.1
```

```bash
sudo systemctl restart mysql
```

> **재시작은 그 DB 를 쓰는 다른 서비스도 잠깐 끊습니다.** 사람이 안 쓰는 시간에
> 하시는 것이 좋습니다. 쉼표 목록은 MySQL 8.0.13 이상에서 쓸 수 있습니다.

### 4. `.env`

```bash
cd /srv/beatmania/app
cp .env.example .env
chmod 600 .env
$EDITOR .env
```

전체 목록과 설명은 `.env.example` 에 있습니다. 컨테이너 배포에서 특히 확인할 것만
옮기면 다음과 같습니다.

| 키 | 값 | 이유 |
|---|---|---|
| `DJANGO_SECRET_KEY` | **기존 값 그대로** | 바꾸면 로그인된 세션이 전부 끊깁니다 |
| `DJANGO_DEBUG` | `false` | |
| `DB_HOST` | `host.docker.internal` | 컨테이너 → 호스트 DB |
| `DB_CHARSET` | `utf8mb4` | MySQL 8 의 `utf8` 은 utf8mb3 별칭이라 이모지가 깨집니다 |
| `DJANGO_BEHIND_PROXY` | `true` | 프록시가 TLS 를 끊습니다. **쿠키 Secure·HSTS 가 여기에 묶여 있습니다** |
| `DJANGO_HSTS_SECONDS` | `3600` 으로 시작 | 아래 경고를 봐 주세요 |
| `GUNICORN_WORKERS` | 코어 수에 맞춰 | 아래를 참고해 주세요 |

> **`DJANGO_SECRET_KEY` 를 새로 만들지 마세요.** 교체하면 세션 인증 해시가 바뀌어
> **전 사용자가 강제 로그아웃**됩니다. Django 3.2 에는 `SECRET_KEY_FALLBACKS` 가 없습니다.

> **HSTS 를 처음부터 1년으로 두지 마세요.** 브라우저가 그 기간 동안 도메인을
> 기억하므로, 잘못 내보내면 내내 http 로 접속할 방법이 없습니다. `3600`(1시간)으로
> 시작해 며칠 지켜본 뒤 `31536000` 으로 올리시길 권합니다.

<details>
<summary><b>워커 수를 정하는 법</b></summary>

gunicorn 이 권하는 `2 × 코어 + 1` 은 **그 기계가 이 앱 전용일 때**의 수치입니다.
DB·웹서버·다른 서비스가 같은 박스에 있으면 그만큼 낮춰 잡으셔야 합니다. 앱 몫으로
칠 코어 수를 정하고 거기에 공식을 적용하는 편이 현실적입니다.

이 앱만의 사정이 하나 더 있습니다. 곡 갱신 명령이 **웹 프로세스와 같은
프로세스에서 Chromium 을 띄우고** 수 분간 워커 하나를 통째로 붙잡습니다.
그동안 나머지가 트래픽을 받아야 합니다.

값은 `GUNICORN_WORKERS` 환경변수입니다. **재빌드 없이 바꿀 수 있으니**, 배포 후
응답 시간을 보고 조정하는 것을 전제로 잡으시면 됩니다.

</details>

### 5. 첫 빌드와 마이그레이션

**덤프를 먼저 뜹니다.**

```bash
mysqldump --no-tablespaces -u iidxrank -p iidxrank | gzip > ~/iidxrank_$(date +%F).sql.gz
ls -lh ~/iidxrank_*.sql.gz          # 크기가 0 이 아닌지 확인합니다
```

> `--no-tablespaces` 가 없으면 `PROCESS` 권한이 없다며 실패합니다. 그렇다고 전역
> `PROCESS` 를 주면 같은 서버의 **다른 서비스 쿼리까지 들여다볼 수 있게 되므로**
> 주지 않습니다.

적용될 마이그레이션에 **되돌릴 수 없는 것이 있는지 먼저 확인합니다.**

```bash
docker compose run --rm app python manage.py showmigrations
```

테이블·컬럼을 **DROP** 하거나 데이터를 **DELETE** 하는 마이그레이션은
`migrate <앱> <이전번호>` 로 되돌려도 원상복구되지 않습니다. 그런 것이 있으면
덤프가 유일한 되돌리기 수단입니다.

```bash
cd /srv/beatmania/app
docker compose build                                    # 브라우저를 받으므로 오래 걸립니다
docker compose run --rm app python manage.py migrate
docker compose up -d
docker compose ps                                       # STATUS 가 healthy 여야 합니다
```

이 시점에 컨테이너는 돌지만 웹서버는 아직 옛 구성입니다. **사이트는 여전히 옛
코드로 서비스되고 있습니다.** 전환 전에 컨테이너를 직접 찔러 보세요.

```bash
curl -sI -H 'Host: 도메인' http://127.0.0.1:8731/login/ | head -3
```

200 이 나와야 다음으로 갑니다. 안 나오면 `docker compose logs -f app` 을 보세요.

### 6. 웹서버 전환

여기서부터 사용자에게 보이는 변화가 생깁니다. **바꾸기 전에 기존 설정을 백업하세요.**

```bash
sudo cp /etc/apache2/sites-available/<사이트>.conf ~/<사이트>.conf.bak
```

`apache-beatmania.conf.example` 을 참고해 고칩니다. 핵심은 네 가지입니다.

```apache
# ① 프록시가 X-Forwarded-Proto 를 못 박습니다. 클라이언트가 보낸 값은 덮어씁니다.
RequestHeader set X-Forwarded-Proto "https"

# ② Host 를 그대로 넘깁니다. 안 넘기면 ALLOWED_HOSTS 에서 걸려 400 이 납니다.
ProxyPreserveHost On

# ③ 업로드 파일은 웹서버가 직접 냅니다. 프록시에서 뺍니다.
Alias /media/ /srv/beatmania/media/
ProxyPass /media/ !

# ④ 나머지를 컨테이너로. timeout 은 gunicorn 의 --timeout 보다 넉넉해야 합니다.
ProxyPass        / http://127.0.0.1:8731/ timeout=180
ProxyPassReverse / http://127.0.0.1:8731/
```

`RequestHeader set` 이지 `setifempty` 가 아닌 것이 핵심입니다. Django 가 이 헤더를
믿기 때문에, 바깥에서 위조한 값이 그대로 들어가면 자기 요청을 HTTPS 인 척할 수 있습니다.

**지울 것.**

- mod_wsgi 지시자 전부 (`WSGIDaemonProcess`, `WSGIScriptAlias`, `WSGIProcessGroup` …)
  — 남겨 두면 어느 쪽이 응답했는지 알 수 없어 문제를 못 찾습니다
- 옛 `/static/` 별칭 — **안 지우면 옛 CSS 가 계속 나갑니다.** 새 화면을 배포했는데
  안 바뀌는 상태가 되고, 브라우저 캐시로 오해하기 딱 좋습니다

**남길 것.** 그 vhost 가 겸하는 다른 용도(웹DAV 등)가 있으면 별칭을 남기고
`ProxyPass /경로 !` 로 프록시에서 빼 주세요. 그러지 않으면 컨테이너로 넘어가 404 가 됩니다.

```bash
sudo a2enmod proxy proxy_http headers
sudo apache2ctl configtest      # Syntax OK
sudo systemctl reload apache2   # reload 입니다. restart 는 다른 vhost 도 끊습니다
```

> **사이트 파일을 새 이름으로 만들지 마세요.** 인증서 자동 갱신 도구(certbot 등)가
> 기존 파일을 관리합니다. 이름을 바꾸면 갱신 때 어긋나고, 같은 ServerName 을 가진
> vhost 가 둘이 되어 어느 쪽이 응답하는지도 불분명해집니다.

---

## 배포할 때마다

```bash
cd /srv/beatmania/app
git pull
docker compose build
docker compose run --rm app python manage.py migrate
docker compose up -d
docker compose logs -f app
```

되돌릴 수 없는 마이그레이션이 포함된 배포는 **덤프를 먼저 뜨세요.**

---

## 자동 배포

`master` push 에서 도는 GitHub Actions 워크플로가
[`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) 에 있습니다.
서버에서 직접 빌드하는 **self-hosted runner** 방식입니다.

| 방식 | 장점 | 단점 |
|---|---|---|
| **self-hosted runner** ← 채택 | 인바운드 포트가 필요 없습니다. 로그가 GitHub 에 남습니다. 서버에서 빌드해 회선을 안 씁니다 | runner 가 서버에 상주합니다 |
| webhook 수신기 | 가볍습니다 | 인바운드 포트를 열어야 합니다 |
| 레지스트리 + watchtower | 서버가 단순해집니다 | 이미지를 매번 push/pull 합니다. 이 이미지는 약 1.9GB 입니다 |

**이미지 크기가 선택을 좌우했습니다.** 1.9GB 를 배포마다 올렸다 내리는 것보다,
서버에서 빌드하는 쪽이 회선을 훨씬 덜 씁니다. 레이어 캐시도 살아서 보통은 마지막
`COPY` 층만 다시 만들어집니다.

### runner 등록

```bash
sudo mkdir -p /srv/actions-runner && sudo chown "$USER":"$USER" /srv/actions-runner
cd /srv/actions-runner
curl -o runner.tar.gz -L \
  https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64.tar.gz
tar xzf runner.tar.gz

# 토큰은 저장소 → Settings → Actions → Runners → New self-hosted runner 에서 받습니다
./config.sh --url https://github.com/<소유자>/<저장소> \
            --token <토큰> \
            --labels self-hosted,linux,beatmania \
            --unattended

sudo ./svc.sh install "$USER"
sudo ./svc.sh start
```

`--labels` 는 워크플로의 `runs-on` 과 정확히 맞춰 주세요. runner 를 돌리는 계정은
`docker` 그룹에 있어야 합니다.

> ### ⚠️ 공개 저장소 + self-hosted runner
>
> **남이 보낸 PR 이 여러분의 서버에서 실행될 수 있습니다.** 그래서 워크플로는
>
> - 트리거를 `push` 로만 두고 `pull_request` 를 넣지 않았고
> - job 에 `if: github.repository == '<소유자>/<저장소>'` 를 걸었습니다
>
> **저장소 설정에서도** Settings → Actions → General → Fork pull request
> workflows 를 `Require approval for all external contributors` 로 바꿔 주세요.

워크플로는 **덤프를 뜨지 않습니다.** 되돌릴 수 없는 마이그레이션이 들어 있는
배포는 push 로 흘리지 마시고 손으로 진행해 주세요.

---

## 정기 실행

컨테이너 안에는 cron 이 없습니다. 호스트에서 넣습니다.

```cron
*/5 * * * * cd /srv/beatmania/app && /usr/bin/docker compose exec -T app python manage.py healthcheck >> /var/log/beatmania-health.log 2>&1
```

- `-T` 가 없으면 TTY 가 없는 cron 환경에서 실패합니다
- `docker` 를 절대 경로로 쓴 것은 cron 의 PATH 가 짧기 때문입니다

곡 데이터 갱신(`updateSongInfinitas`)은 관리자 대시보드에서 사람이 확인하며
돌리는 대화형 명령이라 cron 에는 넣지 않습니다.

---

## 확인

```bash
docker compose ps                              # STATUS 가 healthy
curl -sI https://도메인/login/                  # 200
curl -sI https://도메인/static/css/refactor-style.css   # 200, 컨테이너가 냅니다
curl -sI https://도메인/ | grep -i strict-transport     # HSTS 헤더
docker compose logs --tail 50 app
```

그다음 **브라우저로 직접 확인해 주세요.** curl 로는 확인되지 않는 것들이 있습니다.

| 확인할 것 | 그것이 검증하는 것 |
|---|---|
| 로그인이 됩니다 | 쿠키 Secure 가 제대로 붙었습니다 (프록시 헤더가 맞습니다) |
| 언어 전환이 유지됩니다 | 언어 쿠키의 Secure 설정 |
| 프로필 사진이 뜹니다 | `/media/` 별칭과 uid 10001 소유권 |
| 서열표가 그려집니다 | 정적 파일이 나옵니다 |

> **쿠키에 Secure 를 붙이면 평문 curl 로 로그인 흐름을 검증할 수 없습니다.**
> curl 은 http 응답으로 받은 Secure 쿠키를 저장하지 않아, CSRF 토큰이 실려
> 가지 않고 403 이 납니다. 코드 문제로 오해하기 쉽습니다. https 로 붙어야 합니다.

---

## 되돌리기

### 코드만

```bash
cd /srv/beatmania/app
git checkout <이전 커밋>
docker compose build && docker compose up -d
```

### 웹서버 구성까지

기존 앱 디렉터리를 **지우지 않으셨다면** 그대로 삽니다.

```bash
docker compose down
sudo cp ~/<사이트>.conf.bak /etc/apache2/sites-available/<사이트>.conf
sudo apache2ctl configtest && sudo systemctl reload apache2
```

### DB

**코드를 되돌려도 DB 는 원상복구되지 않습니다.** 되돌릴 수 없는 마이그레이션이
적용된 뒤라면 덤프로 복원해야 합니다.

```bash
zcat ~/iidxrank_YYYY-MM-DD.sql.gz | mysql -u iidxrank -p iidxrank
```

### HSTS

브라우저가 `Strict-Transport-Security` 를 기억합니다. `DJANGO_HSTS_SECONDS` 를
짧게 시작하라고 한 이유가 이것입니다 — 되돌려야 하면 그 시간만 기다리면 됩니다.
이미 길게 올린 뒤라면 사용자 브라우저에서 지울 방법이 사실상 없으니 https 를
계속 유지하는 쪽으로 가시는 편이 낫습니다.

---

## 자주 걸리는 것

| 증상 | 원인 |
|---|---|
| 컨테이너가 계속 재시작합니다 | `SECURE_SSL_REDIRECT` 를 켰습니다. 헬스체크가 평문으로 붙는데 301 을 받아 영원히 실패합니다 |
| 로그인이 안 됩니다 | 프록시 뒤인데 `DJANGO_BEHIND_PROXY` 가 꺼져 있습니다. `is_secure()` 가 False 라 Secure 쿠키가 저장되지 않습니다 |
| 모든 요청에 400 이 납니다 | `ProxyPreserveHost` 가 꺼져 있거나 `DJANGO_ALLOWED_HOSTS` 에 도메인이 없습니다 |
| 프로필 사진이 전부 404 입니다 | 웹서버에 `/media/` 별칭이 없습니다. `DEBUG=False` 인 Django 는 미디어를 처리하지 않습니다 |
| 사진 업로드가 조용히 실패합니다 | 호스트 media 디렉터리 소유자가 uid 10001 이 아닙니다 |
| 새 CSS 가 반영되지 않습니다 | 웹서버에 옛 `/static/` 별칭이 남아 있습니다 |
| 이모지에서 500 이 납니다 | `DB_CHARSET` 이 `utf8`(=utf8mb3) 입니다. `utf8mb4` 여야 합니다 |
| 긴 작업에서 502 가 납니다 | 프록시 `timeout` 이 gunicorn `--timeout` 보다 짧습니다 |
| DB 접속이 거부됩니다 | 브리지 대역(`'사용자'@'172.17.%'`) 권한이 없거나 `bind-address` 가 좁습니다 |
| cron 헬스체크가 실패합니다 | `docker compose exec` 에 `-T` 가 없거나 `docker` 경로가 PATH 에 없습니다 |
| 번역이 바뀌지 않습니다 | `.mo` 를 바꾼 뒤 프로세스를 재시작하지 않았습니다. gettext 는 시작 때 한 번만 읽습니다 |
