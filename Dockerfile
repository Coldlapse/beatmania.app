# beatmania.app 운영 이미지.
#
# 베이스를 python:3.9-slim 으로 잡았다. 개발과 라이브가 모두 3.9 이고,
# Django 3.2 는 3.10 이상에서 검증된 조합이 아니다. 파이썬을 올리는 것은
# 컨테이너화와 분리해서 따로 할 일이다.
#
# Chromium 이 들어가 이미지가 크다(재 보니 1.91GB). update/parser_infinitas.py 가
# textage 에서 JS 를 실행하고 구글 시트가 그려진 뒤의 DOM 을 읽어야 해서
# requests + bs4 로는 대체할 수 없다. 그리고 그 명령은 관리자 대시보드에서
# 웹 프로세스와 같은 프로세스로 실행되므로(update/runner.py), 브라우저를
# 웹 컨테이너 밖으로 뺄 수 없다. 나중에 대시보드가 별도 워커에 작업을
# 던지는 구조로 바꾸면 웹 이미지에서 Chromium 을 뺄 수 있다.

FROM python:3.9-slim-bookworm

# PYTHONUNBUFFERED: 로그가 버퍼에 갇혀 docker logs 에 늦게 나오는 것을 막는다.
# PYTHONDONTWRITEBYTECODE: 읽기 전용으로 굴릴 수 있게 .pyc 를 남기지 않는다.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

WORKDIR /app

# 의존성만 먼저 넣는다. 소스가 바뀌어도 이 층은 캐시가 살아 있어 빌드가 빠르다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chromium 과 그것이 요구하는 시스템 라이브러리. playwright 가 자기 버전에
# 맞는 조합을 알고 있으므로 목록을 손으로 적지 않고 맡긴다.
RUN playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# 정적 파일은 빌드할 때 모아 이미지에 넣는다. 실행할 때 모으면 컨테이너가
# 뜰 때마다 같은 일을 반복하고, 읽기 전용 파일시스템에서는 아예 실패한다.
# collectstatic 은 DB 에 붙지 않지만 settings.py 를 끝까지 읽으므로
# required=True 로 걸린 값들이 전부 있어야 한다. 아래 값들은 이 RUN 한 줄
# 안에서만 살아 있고 이미지에는 남지 않는다. 실행 시에는 .env 의 진짜 값이
# 쓰인다.
RUN DJANGO_SECRET_KEY=build-only-not-a-real-key \
    DJANGO_DEBUG=false \
    DB_PASSWORD=build-only \
    RECAPTCHA_PUBLIC_KEY=build-only \
    RECAPTCHA_PRIVATE_KEY=build-only \
    python manage.py collectstatic --noinput --clear

# 루트로 돌리지 않는다. media 볼륨은 이 uid 가 쓸 수 있어야 한다.
RUN groupadd -r app && useradd -r -g app -u 10001 app \
    && mkdir -p /app/media \
    && chown -R app:app /app/media
USER app

EXPOSE 8000

# 컨테이너 안에서 스스로 확인한다. compose 가 이 결과로 재시작을 판단한다.
# /status/ 는 DB 와 외부 연동까지 건드리므로 헬스체크로는 무겁다. 가벼운
# 정적 응답인 로그인 화면을 쓴다.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/login/', timeout=4).status == 200 else 1)"

# 워커 수 — 기본 5.
#
# gunicorn 이 권하는 2*코어+1 은 그 기계가 이 앱 전용일 때의 수치다. 이 앱은
# 보통 DB·웹서버·다른 서비스와 한 박스를 나눠 쓰는 곳에 놓인다. 전체 코어로
# 세어 큰 값을 잡으면, 정작 이 앱이 기다리고 있는 DB 와 CPU 를 다투게 된다.
# 앱 몫으로 칠 코어 수를 먼저 정하고 거기에 공식을 적용하는 편이 맞다.
#
# 이 앱만의 사정이 하나 더 있다. 대시보드의 updateSongInfinitas 는 Chromium 을
# 같은 프로세스에서 띄우고 수 분간 워커 하나를 통째로 붙잡는다. 그동안
# 나머지가 트래픽을 받아야 하므로 1~2개로는 부족하다.
#
# 값을 환경변수로 뺀 이유는, 재 보고 조정하는 것이 이미지를 다시 만드는 것보다
# 싸기 때문이다. .env 에서 GUNICORN_WORKERS 를 바꾸고 다시 띄우면 된다.
#
# --timeout 120: updateSongInfinitas 가 대시보드에서 돌면 요청이 길어진다.
#   기본 30초로는 워커가 죽는다.
# --max-requests: Chromium 을 웹 프로세스에서 띄우는 구조라 누수가 쌓일 여지가
#   있다. 일정 요청마다 워커를 갈아 끼운다. jitter 가 없으면 5개가 동시에
#   교체돼 순간적으로 응답이 끊긴다. 진행 중인 요청을 끊지는 않는다.
# --access-logfile -: 접근 로그를 stdout 으로. docker logs 로 본다.
#
# 셸 형식으로 쓴 이유는 exec 형식(JSON)에서는 환경변수가 치환되지 않기
# 때문이다. exec 를 붙여 gunicorn 이 PID 1 을 넘겨받게 한다 — 안 그러면 sh 가
# PID 1 이라 docker stop 의 SIGTERM 이 gunicorn 에 전달되지 않는다.
CMD ["sh", "-c", "exec gunicorn wsgi:application \
     --bind 0.0.0.0:8000 \
     --workers ${GUNICORN_WORKERS:-5} \
     --timeout ${GUNICORN_TIMEOUT:-120} \
     --max-requests 1000 \
     --max-requests-jitter 100 \
     --access-logfile - \
     --error-logfile -"]
