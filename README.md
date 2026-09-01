<div align="center">

# beatmania.app

**IIDX INFINITAS 서열표(난이도표) · 클리어 기록 · 통계 서비스**

[![Django](https://img.shields.io/badge/Django-3.2-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.9-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#라이선스)

[**beatmania.app**](https://beatmania.app) &nbsp;·&nbsp; 한국어 / English / 日本語 / 简体中文

</div>

---

레벨별 곡 난이도 서열표를 보여 주고, 로그인하면 자기 클리어 램프를 그 위에
얹어 줍니다. 어느 곡을 다음에 잡아야 할지, 같은 레벨 안에서 내가 어디쯤인지를
한 화면에서 볼 수 있습니다.

[@lazykuna](https://github.com/lazykuna) 님의 `iidxranktable` 을 포크해
운영하고 있습니다. 포크 이후 달라진 점은 [아래](#원본과-달라진-것)를 참고해 주세요.

---

## 목차

- [기능](#기능)
- [엔드포인트](#엔드포인트)
- [구성](#구성)
- [로컬에서 돌리기](#로컬에서-돌리기)
- [컨테이너로 돌리기](#컨테이너로-돌리기)
- [설정](#설정)
- [비밀번호 규칙](#비밀번호-규칙)
- [메일 발송](#메일-발송)
- [관리 명령](#관리-명령)
- [개발·검증 도구](#개발검증-도구)
- [배포](#배포)
- [원본과 달라진 것](#원본과-달라진-것)
- [라이선스](#라이선스)

---

## 기능

### 서열표

레벨·플레이 타입(SP/DP)별로 곡을 난이도순으로 늘어놓은 표입니다. 현재 11종이 있습니다.

```
SP12H  SP11H  SP10H  SP12N  SP11N  DP12  DP11  DP10  DBR  11DBR  onehand
```

- 로그인하면 **자기 클리어 램프**가 각 곡 칸에 칠해집니다
- 표 위에서 바로 램프를 고쳐 기록할 수 있습니다
- 다른 사람의 표를 볼 수 있습니다 (`/u/<아이디>/table/<표이름>/`)
- 블로그·디스코드에 넣을 **임베드 뷰**와 **이미지 다운로드**를 제공합니다
- 표는 `<canvas>` 한 장으로 그려집니다 — 다운로드 이미지와 화면이 같은 그림입니다

### 개인 페이지

`/u/<아이디>/` 에 그 사람의 표별 달성도와 통계가 모입니다.
**프로필 비공개**를 켜면 이 페이지와 유저 랭킹에서 함께 빠집니다.

### 랭킹

| | |
|---|---|
| **곡 랭킹** | 곡별 클리어 분포 |
| **유저 랭킹** | 표별 달성도 순위 (비공개 계정 제외) |
| **건실 랭킹** | 일일 타건 수 리더보드. 로그인하지 않아도 볼 수 있습니다 |

### 흰숫(SUDDEN+) 변환기

IIDX 와 beatoraja 사이의 서든+ 값을 환산합니다. 리프트를 함께 쓸 때의
계산까지 맞춥니다.

> 게임이 실제로 하는 계산은 `IIDX = floor(BMS × (1000 − LIFT) ÷ 1000)`
> **한 방향뿐입니다.** 되돌릴 때는 그 식에 넣어 목표값이 나오는 *가장 작은* BMS 를
> 찾아야 합니다. 표본 검사에서 단순 `floor` 는 69,350건이 어긋났고 `ceil` 은 0건이었습니다.

### 곡 목록 · 추천

수록곡 4,000여 곡을 레벨·시리즈로 좁혀 볼 수 있습니다. 클리어 상황을 바탕으로
다음에 잡을 만한 곡을 추천합니다.

### 서비스 현황

`/status/` 에 가동 상태 타임라인과 사이트 방문 통계가 있습니다.
`manage.py healthcheck` 를 5분마다 돌려 채웁니다.

### 기계 대기열

오프라인 기계의 대기 인원을 에이전트가 올려 두면 `/status/<기계ID>/` 에서 볼 수 있습니다.

### 계정과 이메일 인증

가입할 때 이메일 인증을 끝내야 계정이 만들어집니다. 인증 코드는 6자리 숫자이고
유효 시간은 1시간, 재발송은 5분 간격입니다.

- **이메일은 계정 인증과 아이디·비밀번호 찾기에만 씁니다.** 그 밖의 목적으로
  쓰거나 임의로 메일을 보내지 않습니다. 마케팅 메일도 없습니다
- 이메일은 계정마다 유일합니다
- 인증 메일에는 **링크를 넣지 않습니다.** 링크가 있으면 나중에 진짜 피싱 메일이
  왔을 때 사용자가 구별할 수 없습니다. 코드만 보냅니다
- 아이디 찾기·비밀번호 재설정은 이메일 인증으로 합니다
- 비밀번호는 **8자 이상**, 조합 규칙은 없습니다. 자세한 것은 [아래](#비밀번호-규칙)

### 다국어

한국어(원문) · English · 日本語 · 简体中文 을 지원합니다. URL 에는 언어를 넣지 않고
쿠키/세션에 저장합니다 — 기존 주소가 리다이렉트되지 않게 하기 위해서입니다.

### 관리자 대시보드

`/manage/` (staff 전용)입니다. 구글 시트의 서열표를 읽어 DB 에 반영합니다.
**시트와 DB 가 어긋나면 적용 전에 사람에게 물어봅니다** — 명령이 도는 중에
질문이 뜨고, 답을 받은 뒤에야 트랜잭션을 엽니다.

---

## 엔드포인트

### 서열표

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/` | 내 프로필 · 표 목록 |
| `GET` | `/table/<표이름>/` | 내 서열표 |
| `GET` | `/table/<표이름>/embed/` | 임베드용 (헤더·푸터 없음) |
| `GET` | `/table/<표이름>/json/` | 표 데이터 JSON |
| `GET` | `/u/<아이디>/` | 남의 프로필 |
| `GET` | `/u/<아이디>/table/<표이름>/` | 남의 서열표 |
| `GET` | `/u/<아이디>/table/<표이름>/embed/` | 남의 표 임베드 |
| `GET` | `/u/<아이디>/table/<표이름>/json/` | 남의 표 JSON |

> 비공개 계정은 `404` 와 함께 안내문을 돌려줍니다. **존재 여부를 흘리지 않습니다.**

### 일반 페이지

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/songrank/` | 곡 랭킹 |
| `GET` | `/userrank/` | 유저 랭킹 |
| `GET` | `/musiclist/` | 곡 목록 |
| `GET` | `/converter/` | 흰숫 변환기 |
| `GET` | `/my-page/` | 일일 타건 기록 · 건실 랭킹 |
| `GET` | `/sync/` | 데이터 동기화 안내 |
| `GET` | `/status/` | 서비스 현황 |
| `GET` | `/status/<기계ID>/` | 기계 대기열 |
| `GET` | `/overjoy/` | Overjoy 난이도표 |
| `GET` | `/about/` | 개발 로드맵 · 개발자 소개 |
| `GET` | `/privacy/` | 개인정보처리방침 |

### 계정

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` `POST` | `/join/` | 가입 (reCAPTCHA) |
| `GET` `POST` | `/login/` | 로그인 — 폼 필드는 `id` / `password` 입니다 |
| `GET` | `/logout/` | 로그아웃 |
| `GET` `POST` | `/account/` | 계정 설정 · 프로필 사진 · 비공개 전환 |
| `GET` `POST` | `/setpassword/` | 비밀번호 변경 |
| `GET` `POST` | `/withdraw/` | 탈퇴 |
| `GET` | `/account/token/` | API 토큰 확인 |
| `POST` | `/account/token/reissue/` | API 토큰 재발급 |
| `GET` `POST` | `/account/email/` | 이메일 변경 (새 주소 인증 필요) |
| `GET` `POST` | `/find-id/` | 아이디 찾기 (이메일 인증) |
| `GET` `POST` | `/reset-password/` | 비밀번호 재설정 (이메일 인증) |
| `GET` `POST` | `/account/verify-account/` | 기존 사용자 1회 인증 |
| `POST` | `/account/verify/send/` | 인증 코드 발송 (AJAX) |
| `POST` | `/account/verify/check/` | 인증 코드 확인 (AJAX) |

> 아이디 찾기·비밀번호 재설정은 **가입 여부를 알려 주지 않습니다.** 등록되지
> 않은 주소를 넣어도 같은 응답을 돌려주고 메일만 보내지 않습니다. 그러지 않으면
> 이 화면으로 가입자 목록을 캐낼 수 있습니다.

### 기록 편집

| 메서드 | 경로 | 설명 |
|---|---|---|
| `POST` | `/lampupdate/` | 클리어 램프 갱신 |
| `GET` `POST` | `/rankedit/<id>/` | 곡 배치 편집 |
| `POST` | `/modify/` | 기록 수정 |
| `GET` `POST` | `/update/rankedit/<표이름>/` | 표 전체 편집 |

### JSON

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/json/userlist/` | 사용자 목록 (**비공개 계정 제외**) |
| `GET` | `/json/musiclist/<타입>/level/<레벨>/` | 레벨별 곡 |
| `GET` | `/json/musiclist/<타입>/series/<시리즈>/` | 시리즈별 곡 |
| `GET` | `/json/recommend/<아이디>/<타입>/` | 추천 곡 |
| `GET` | `/json/recommend/<아이디>/<타입>/<레벨>/` | 레벨을 좁힌 추천 곡 |
| `GET` | `/status/views.json` | 사이트뷰 시계열 |
| `GET` | `/my-page/typing.json` | 타건 기록 시계열 |
| `GET` | `/overjoy/header.json` | BMS 구동기가 읽는 규약 주소 |

> `/overjoy/header.json` 은 **주소를 바꾸지 말아 주세요.** BMS 구동기 쪽에
> 등록돼 있어서, 바꾸면 사용자가 직접 재등록해야 합니다.

### API

| 메서드 | 경로 | 인증 | 설명 |
|---|---|---|---|
| `POST` | `/api/v1/update-typing-count/` | `Authorization: Token <키>` | 타건 수 누적 |
| `POST` | `/api/v1/update-machine-status/` | `Authorization: Token <키>` (운영자 전용) | 기계 대기열 갱신 |

```bash
curl -X POST https://beatmania.app/api/v1/update-typing-count/ \
     -H "Authorization: Token <내 토큰>" \
     -H "Content-Type: application/json" \
     -d '{"count": 1234}'
```

응답은 `200` 성공 / `400` 잘못된 본문 / `401` 토큰 없음·틀림 / `405` POST 아님입니다.
토큰은 `/account/token/` 에서 확인하고 재발급할 수 있습니다.

두 API 모두 토큰 없이는 아무것도 하지 못합니다. 다만 요구하는 권한이 다릅니다.

| | 누가 쓸 수 있나 | 왜 |
|---|---|---|
| `update-typing-count` | 토큰을 가진 **모든 사용자** | 자기 타건 기록만 쌓습니다. 남의 데이터에 닿지 않습니다 |
| `update-machine-status` | **운영자 계정의 토큰만** | 기계 대기열은 모든 방문자가 함께 보는 값이라, 아무나 바꿀 수 있으면 안 됩니다 |

권한이 없는 토큰으로 대기열 갱신을 시도하면 `403` 을 돌려줍니다
(`401` 이 아닙니다 — 토큰 자체는 유효하기 때문입니다).

### 관리자 (staff 전용)

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/manage/` | 대시보드 |
| `POST` | `/manage/run/` | 명령 실행 |
| `GET` | `/manage/run/<id>/` | 실행 상세 |
| `GET` | `/manage/run/<id>/log/` | 실행 로그 (폴링) |
| `POST` | `/manage/run/<id>/abort/` | 중단 |
| `POST` | `/manage/run/<id>/answer/` | 확인 질문에 답 |
| `GET` | `/admin/` | Django 관리자 |

### 옛 주소

포크 이전 주소는 전부 **301** 로 넘어갑니다. 쿼리스트링도 보존합니다.

| 옛 주소 | 새 주소 |
|---|---|
| `/!/` | `/` |
| `/!/<표이름>/` | `/table/<표이름>/` |
| `/!/<표이름>/table/` | `/table/<표이름>/embed/` |
| `/<아이디>/` | `/u/<아이디>/` |
| `/<아이디>/<표이름>/` | `/u/<아이디>/table/<표이름>/` |
| `/analytics/` | `/status/` |
| `/roadmap/` | `/about/` |

> 옛 사용자 주소는 **계정이 있든 없든 301** 을 돌려줍니다. 존재할 때만 넘기면
> 그 차이로 계정을 열거할 수 있기 때문입니다.

---

## 구성

| | |
|---|---|
| **언어** | Python 3.9 |
| **프레임워크** | Django 3.2 |
| **DB** | MySQL 8 (접속 charset `utf8mb4`) |
| **WSGI** | gunicorn |
| **정적 파일** | whitenoise — 앱이 직접 냅니다. 웹서버 설정이 필요 없습니다 |
| **프론트엔드** | Bootstrap 5, CSS 변수 기반 테마 (다크모드) |
| **스크래핑** | playwright + Chromium |
| **UI 프레임** | `<canvas>` 로 그리는 서열표 |

<details>
<summary><b>왜 Chromium 이 필요한가요</b></summary>

서열표 원본이 구글 시트입니다. 그 시트는 **JS 로 그려진 뒤에야** 표 내용이 DOM 에
들어옵니다. `requests` + `BeautifulSoup` 로는 빈 껍데기만 받습니다. 그래서 실제
브라우저를 띄워 렌더가 끝난 DOM 을 읽습니다.

이 때문에 이미지가 약 1.9GB 로 큽니다. 곡 갱신 명령이 웹 프로세스와 같은
프로세스에서 돌기 때문에(`update/runner.py`) 지금은 브라우저를 분리할 수 없습니다.
대시보드가 별도 워커에 작업을 던지는 구조로 바꾸면 분리할 수 있습니다.

</details>

---

## 로컬에서 돌리기

### 필요한 것

- Python 3.9
- MySQL 8 (또는 아래 [개발·검증 도구](#개발검증-도구)의 dev 컨테이너)

### 절차

```bash
git clone https://github.com/Coldlapse/beatmania.app.git
cd beatmania.app

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env      # DJANGO_SECRET_KEY, DB_PASSWORD, reCAPTCHA 키를 채웁니다
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`http://127.0.0.1:8000/` 이 열립니다.

곡 갱신 명령까지 쓰려면 브라우저를 한 번 받아야 합니다.

```bash
playwright install chromium
```

> **`runserver` 는 운영에 쓰지 마세요.** 단일 스레드이고 정적 파일도 개발용
> 방식으로 냅니다. 운영은 아래 컨테이너(gunicorn) 쪽을 쓰시면 됩니다.
>
> 예전에는 `runserver.sh` 라는 무한 재시작 루프 스크립트가 있었습니다. 지금은
> 컨테이너의 `restart: unless-stopped` 가 같은 일을 제대로 하므로 지웠습니다.

---

## 컨테이너로 돌리기

이미지 하나에 앱 + gunicorn + Chromium 이 들어갑니다.
**MySQL 은 이미지에 넣지 않습니다** — 이미 돌고 있는 DB 에 붙는 것을 전제합니다.

```bash
cp .env.example .env      # DB_HOST 를 환경에 맞게 고칩니다
docker compose up -d --build
docker compose logs -f app
```

`docker-compose.yml` 이 하는 일은 다음과 같습니다.

| | |
|---|---|
| 포트 | `127.0.0.1:${APP_PORT}` 에만 묶습니다. 앞단 웹서버가 프록시합니다 |
| `extra_hosts` | `host.docker.internal` 로 호스트 DB 에 닿게 합니다 |
| 볼륨 | `${MEDIA_DIR}:/app/media` — 업로드본은 컨테이너 밖에 둡니다 |
| 로그 | json-file, 10MB × 5 로 제한합니다 |
| 헬스체크 | 컨테이너가 스스로 `/login/` 을 때려 봅니다 |

### 컨테이너 안에서 명령 돌리기

```bash
docker compose run --rm app python manage.py migrate
docker compose exec -T app python manage.py healthcheck
```

### 이미지가 하는 일

<details>
<summary><b>Dockerfile 요약</b></summary>

1. `python:3.9-slim` 위에 `requirements.txt` 를 **먼저** 설치합니다 — 소스가
   바뀌어도 이 층의 캐시가 살아 있어 빌드가 빠릅니다
2. `playwright install --with-deps chromium` 으로 브라우저와 시스템
   라이브러리를 넣습니다. 목록을 손으로 적지 않고 playwright 에 맡깁니다
3. 소스를 복사하고 `collectstatic` 을 **빌드 시점에** 돌립니다. 실행할 때 모으면
   컨테이너가 뜰 때마다 같은 일을 반복하고, 읽기 전용 파일시스템에서는 실패합니다
4. uid `10001` 비루트 사용자로 낮춥니다. 호스트의 media 디렉터리도 이 uid 가
   쓸 수 있어야 합니다
5. gunicorn 을 `exec` 로 띄웁니다 — PID 1 이 되어야 `docker stop` 의 SIGTERM 을
   받을 수 있습니다

`collectstatic` 은 DB 에 붙지 않지만 `settings.py` 를 끝까지 읽습니다. 그래서
빌드 단계에 더미 비밀값을 넣는데, 그 값은 `RUN` 한 줄 안에서만 살아 있고
이미지에는 남지 않습니다.

</details>

### 앞단 웹서버

컨테이너는 평문 HTTP 로만 말합니다. TLS 를 끊고 넘겨 주는 웹서버를 앞에 두세요.

```
인터넷 → 웹서버(443, TLS) ─┬─ /media/  → 파일 직접
                          └─ 그 외    → 127.0.0.1:<APP_PORT> → 컨테이너
```

챙길 것이 셋 있습니다.

1. **`X-Forwarded-Proto: https` 를 웹서버가 못 박아야 합니다.** 클라이언트가 보낸
   값은 덮어씁니다. 이 헤더를 Django 가 믿기 때문입니다
2. **`/media/` 는 웹서버가 직접 냅니다.** `DEBUG=False` 인 Django 는 미디어를
   아예 처리하지 않습니다
3. **`/static/` 에는 별칭을 두지 않습니다.** 정적 파일은 이미지 안에 있고
   whitenoise 가 냅니다

Apache 예시가 [`deploy/apache-beatmania.conf.example`](deploy/apache-beatmania.conf.example)
에 있습니다. 자세한 것은 [`deploy/README.md`](deploy/README.md) 를 봐 주세요.

---

## 설정

설정값은 전부 환경변수에서 읽습니다. `BASE_DIR/.env` 가 있으면 읽되
**프로세스 환경변수가 항상 이깁니다** — 같은 코드가 파일 방식과 docker
`env_file:` 양쪽에서 그대로 돕니다.

전체 목록과 설명은 [`.env.example`](.env.example) 에 있습니다. 주요 항목만 옮기면:

| 키 | 기본값 | 설명 |
|---|---|---|
| `DJANGO_SECRET_KEY` | — | **필수.** 바꾸면 로그인된 세션이 전부 끊깁니다 |
| `DJANGO_DEBUG` | `false` | |
| `DJANGO_ALLOWED_HOSTS` | `beatmania.app` | 쉼표로 구분합니다 |
| `DJANGO_BEHIND_PROXY` | `false` | 프록시 뒤일 때만 `true`. **쿠키 Secure·HSTS 가 여기에 묶여 있습니다** |
| `DJANGO_HSTS_SECONDS` | `3600` | 위가 `true` 일 때만 나갑니다 |
| `DJANGO_LOG_LEVEL` | `INFO` | 로그는 전부 stdout 으로 나갑니다 |
| `DB_HOST` / `DB_PORT` | `localhost` / `3306` | 컨테이너에서는 `host.docker.internal` |
| `DB_CHARSET` | `utf8mb4` | MySQL 8 의 `utf8` 은 utf8mb3 별칭이라 이모지가 깨집니다 |
| `RECAPTCHA_*` | — | **필수.** 가입 폼에 씁니다 |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | — | 비우면 콘솔 백엔드로 떨어져 메일이 로그에 찍힙니다 |
| `EMAIL_CODE_TTL` | `3600` | 인증 코드 유효 시간(초) |
| `EMAIL_RESEND_INTERVAL` | `300` | 재발송 간격(초) |
| `GUNICORN_WORKERS` | `5` | 재빌드 없이 조정할 수 있습니다 |
| `APP_PORT` / `MEDIA_DIR` | `8731` / `/srv/beatmania/media` | compose 가 읽습니다 |

> **`DJANGO_BEHIND_PROXY` 를 기본으로 켜지 마세요.** 프록시 뒤가 아닌데 켜면
> 누구든 `X-Forwarded-Proto: https` 헤더를 붙여 자기 요청을 HTTPS 인 척할 수 있습니다.
> 앞단 웹서버가 그 헤더를 덮어쓰기 때문에 안전한 것입니다.

---

## 비밀번호 규칙

**8자 이상.** 특수문자나 대소문자 조합은 강요하지 않습니다.

조합 규칙을 강제하면 사람들이 `Password1!` 같은 예측 가능한 패턴으로 몰립니다
(NIST SP 800-63B 도 조합 규칙을 권하지 않습니다). 실제로 일을 하는 것은 길이가
아니라 **흔한 비밀번호 목록**입니다.

| 비밀번호 | 8자 길이만 검사 | 지금 (8자 + 목록) |
|---|---|---|
| `abcd1234` | 통과 | **차단** |
| `password` | 통과 | **차단** |
| `12345678` | 통과 | **차단** |
| `qwerty123` | 통과 | **차단** |

Django 가 들고 있는 흔한 비밀번호 19,728개 목록을 씁니다. 12자로 올려서 추가로
막히는 것은 이미 그 목록이 잡는 것들뿐이라, 길이를 더 올리지 않았습니다.

적용되는 검증기는 다섯입니다.

```
UserAttributeSimilarityValidator   아이디·이메일과 비슷한 것
MinimumLengthValidator(8)
CommonPasswordValidator            흔한 비밀번호 19,728개
NumericPasswordValidator           전부 숫자
ASCIIPasswordValidator             한글·이모지 (아래 참조)
```

### 왜 한글을 막나

약해서가 아닙니다. 글자당 정보량은 한글이 영문의 세 배쯤 됩니다.
문제는 **되찾기 어렵다**는 것입니다.

- Django 는 비밀번호를 유니코드 정규화하지 않습니다. 같은 `무한궤도` 라도
  NFC 는 코드포인트 4개, NFD 는 9개라 **서로 다른 문자열**입니다. 가입한 기기와
  로그인하는 기기의 IME 가 다른 형태로 조합하면, 같은 글자를 쳐도 틀렸다고 나옵니다
- 비밀번호 칸은 가려져 있어 IME 가 한글 상태인지 영문 상태인지 볼 수 없습니다
- 다른 기기나 게임기 브라우저에는 한글 IME 가 없을 수 있습니다

공백은 허용합니다. 여러 단어를 이어 쓰는 방식이 길이를 벌기 가장 쉽습니다.

> **`AUTH_PASSWORD_VALIDATORS` 는 저절로 적용되지 않습니다.** 그 설정을 적용해
> 주는 것은 `django.contrib.auth` 의 기본 폼들인데 이 프로젝트는 폼을 직접
> 만들어 씁니다. `iidxrank/forms.py` 가 `validate_password()` 를 직접 부릅니다 —
> 그 호출을 지우면 설정 전체가 조용히 무효가 됩니다.

---

## 메일 발송

계정 인증에만 씁니다. SMTP 설정은 환경변수로 넣습니다.

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...      # Gmail 은 '앱 비밀번호' 16자
DEFAULT_FROM_EMAIL=...
```

`EMAIL_HOST_USER` 와 `EMAIL_HOST_PASSWORD` 가 **둘 다 있어야** SMTP 로 보냅니다.
하나라도 비면 콘솔 백엔드로 떨어져 메일 내용이 로그에 찍힙니다. 개발 중에는
그것이 편하고, 운영에서 실수로 비면 메일이 조용히 사라지는 대신 로그에 남아
알아챌 수 있습니다.

메일은 평문과 HTML 을 함께 보냅니다. HTML 쪽은 이미지도 링크도 쓰지 않습니다 —
대부분의 클라이언트가 원격 이미지를 차단하고, 원격 이미지는 열람 시점과 IP 를
발신자에게 알려 주는 추적 수단이 되기 때문입니다.

**메일 언어는 요청한 사람의 언어를 따릅니다.** 언어는 `쿠키 → Accept-Language →
기본값(한국어)` 순으로 정해집니다. 즉 브라우저 언어가 그대로 쓰이고, 사용자가
사이트에서 언어를 고르면 그 선택이 1년짜리 쿠키로 남아 우선합니다.

---

## 관리 명령

```bash
python manage.py healthcheck             # 가동 상태 기록. /status/ 타임라인을 채웁니다
python manage.py updateSongInfinitas     # 곡 정보·서열표 갱신 (대화형)
python manage.py cleanDuplicateSongs     # 중복 곡 정리 (대화형)
```

`healthcheck` 는 **5분 간격 cron** 으로 돌립니다. 컨테이너 안에는 cron 이 없으니
호스트에서 넣어 주세요.

```cron
*/5 * * * * cd /경로 && /usr/bin/docker compose exec -T app python manage.py healthcheck
```

`-T` 가 없으면 TTY 가 없는 cron 환경에서 실패합니다.

`updateSongInfinitas` 는 **사람이 보면서 돌리는 명령**입니다. 시트와 DB 가
어긋나면 중간에 물어봅니다. 관리자 대시보드에서 돌리면 진행 로그와 질문이
화면에 뜹니다. cron 에는 넣지 마세요.

---

## 개발·검증 도구

`dev/` 에 dev MySQL 정의, 회귀 검사, 번역 카탈로그 빌드가 있습니다.
이미지에는 들어가지 않습니다.

```bash
cd dev && docker compose up -d     # dev MySQL (호스트 3307)
cd .. && python dev/checks/run_all.py
```

```
compilecheck.py    전 .py 파일 컴파일
livecheck.py       주요 화면 12종의 상태·응답시간·쿼리 수
test_urls.py       새 주소, 옛 주소 301, 비공개 프로필, 가입 폼
untranslated.py    번역이 빠진 원문
```

번역을 추가할 때는 `dev/i18n/` 을 씁니다. 자세한 것은 [`dev/README.md`](dev/README.md) 를 봐 주세요.

---

## 배포

[`deploy/README.md`](deploy/README.md) 에 컨테이너 + 리버스 프록시 구성으로
올리는 일반 절차가 있습니다. 되돌릴 수 없는 마이그레이션을 다루는 법도 거기에 있습니다.

`master` 에 push 하면 self-hosted runner 가 빌드·마이그레이트·재기동합니다
([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)).

---

## 원본과 달라진 것

포크 시점(2021) 이후 큰 것만 적었습니다.

| | |
|---|---|
| **배포** | AWS + mod_wsgi → **Docker + gunicorn**. 웹서버는 TLS 만 끊습니다 |
| **주기 실행** | celery + Redis 제거 → 호스트 cron |
| **DB** | MariaDB → **MySQL 8**, 접속 charset `utf8mb4` |
| **시크릿** | 하드코딩 → **전부 환경변수** |
| **URL** | `/!/...` 체계를 걷어내고 **301 로 호환** |
| **프론트엔드** | Bootstrap 5 재작성, CSS 변수 테마, 다크모드 |
| **다국어** | 4개 언어 (URL 이 아니라 쿠키/세션 방식) |
| **관리** | 대화형 확인이 붙은 웹 대시보드 |
| **정리** | 게시판·polls 등 쓰지 않는 앱 제거 |
| **의존성** | AST 로 실제 import 를 역산출해 `requirements.txt` 재작성 |

---

## 라이선스

MIT 입니다. [`LICENSE`](LICENSE) 를 참고해 주세요.

원본이 포함한 서드파티 코드(bootstrap, dragula, mooEditable)의 저작권은
각 프로젝트에 있습니다.
