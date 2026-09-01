"""iidxrank(beatmania.app) 설정.

민감한 값은 전부 환경변수에서 읽는다. 아래 Configuration 주석 참조.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import pymysql
pymysql.install_as_MySQLdb()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Configuration
#
# Values come from the process environment. When BASE_DIR/.env exists its
# entries are loaded first, but a real environment variable always wins - so
# the same file works under mod_wsgi (which cannot pass env vars reliably)
# and under docker compose `env_file:` with no code change.
#
# See .env.example for the full list. Never commit .env itself.
# ---------------------------------------------------------------------------
def _load_dotenv(path):
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)   # setdefault: real env wins

_load_dotenv(os.path.join(BASE_DIR, '.env'))


def env(key, default=None, required=False):
    value = os.environ.get(key, default)
    if required and not value:
        raise RuntimeError(
            "필수 환경변수 %s 가 없습니다. %s/.env 를 확인하세요 "
            "(.env.example 참고)." % (key, BASE_DIR))
    return value


def env_bool(key, default=False):
    return str(os.environ.get(key, default)).lower() in ('1', 'true', 'yes', 'on')


def env_list(key, default=''):
    return [v.strip() for v in os.environ.get(key, default).split(',') if v.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY', required=True)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool('DJANGO_DEBUG', False)

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'beatmania.app')

# 컨테이너로 돌릴 때는 Apache 가 TLS 를 끊고 평문 HTTP 로 넘겨 준다. 그러면
# Django 입장에서는 모든 요청이 http 로 보이고, 그 상태로는
#   - request.is_secure() 가 False 라 CSRF 의 Referer 대조가 어긋나고
#   - build_absolute_uri() 가 http:// 주소를 만들어 낸다.
# X-Forwarded-Proto 를 믿게 해서 이를 바로잡는다.
#
# 반드시 스위치로 둔다. 프록시 뒤가 아닌데 켜 두면, 누구든 이 헤더를 붙여
# 보내는 것만으로 자기 요청을 HTTPS 인 척할 수 있다. Apache 는 이 헤더를
# 자기가 덮어쓰므로(RequestHeader set) 바깥에서 위조한 값은 들어오지 못한다.
BEHIND_PROXY = env_bool('DJANGO_BEHIND_PROXY', False)

if BEHIND_PROXY:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

# 쿠키에 Secure 를 붙이고 HSTS 를 낸다. 이 둘을 위 스위치에 묶은 것은 취향이
# 아니라 순서 문제다. is_secure() 가 False 인 채로 SESSION_COOKIE_SECURE 를
# 켜면 브라우저가 쿠키를 아예 저장하지 않아 로그인이 되지 않는다. 즉
# SECURE_PROXY_SSL_HEADER 가 먼저 서 있어야 이것을 켤 수 있다.
#
# HSTS 는 되돌리기가 어렵다. 브라우저가 max-age 동안 이 도메인을 기억하므로,
# 잘못 내보내면 그 기간 내내 http 로 접속할 방법이 없다. 그래서
#   - 값을 환경변수로 빼고 (DJANGO_HSTS_SECONDS)
#   - 기본을 1시간으로 두었다.
# 배포 후 며칠 지켜보고 문제가 없으면 .env 에서 31536000(1년)으로 올린다.
# preload 는 넣지 않았다 — 목록에 오르면 사이트를 접을 때까지 빠지기 어렵다.
if BEHIND_PROXY:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    LANGUAGE_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = int(env('DJANGO_HSTS_SECONDS', '3600'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
        'DJANGO_HSTS_INCLUDE_SUBDOMAINS', False)

# http → https 리다이렉트는 켜지 않는다. Apache 의 80 번 vhost 가 이미
# RewriteRule 로 하고 있어 중복이고, 더 중요하게는 컨테이너 헬스체크가
# 평문으로 127.0.0.1:8000/login/ 을 때린다. 이걸 켜면 그 요청이 301 을 받아
# 헬스체크가 영원히 실패하고 compose 가 컨테이너를 계속 재시작한다.
SECURE_SSL_REDIRECT = False

# 쿠키를 자바스크립트에서 읽을 이유가 없다. 프록시 여부와 무관하게 켠다.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# 브라우저가 Content-Type 을 추측하지 못하게 한다. 사용자가 올린 프로필
# 사진을 브라우저가 HTML 로 넘겨짚는 경로를 막는다.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 서비스 현황 문장의 자릿수 구분자(|intcomma)에만 쓴다.
    'django.contrib.humanize',
    'iidxrank',
    'update',
    'captcha',
    'django_bootstrap5',
    'hitcount',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    # LocaleMiddleware 는 Session 뒤, Common 앞에 와야 한다.
    # 세션·쿠키에 저장된 언어를 읽어야 하고, Common 이 URL 을 확정하기 전에
    # 언어가 정해져 있어야 하기 때문이다.
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # 정적 파일은 여기서 끝난다. 아래 미들웨어와 뷰까지 가지 않는다.
    'whitenoise.middleware.WhiteNoiseMiddleware',
)


ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]



# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME', 'iidxrank'),
        'USER': env('DB_USER', 'iidxrank'),
        'PASSWORD': env('DB_PASSWORD', required=True),
        # container -> host MySQL uses the docker0 gateway, not 'localhost'
        'HOST': env('DB_HOST', 'localhost'),
        'PORT': env('DB_PORT', '3306'),
        # 기본값이 utf8 이면 안 된다. MySQL 8 에서 'utf8' 은 utf8mb3 의 별칭이라
        # 3바이트까지만 담는다. 이 DB 의 컬럼은 전부 utf8mb4 이므로, 접속만
        # utf8mb3 이면 4바이트 문자(이모지)를 쓸 때 콜레이션이 충돌해서
        #   (1270, "Illegal mix of collations ... for operation 'concat'")
        # 로 실패한다. 관리자 대시보드의 명령 로그가 이모지를 쏟아내므로
        # 실제로 이 경로에서 터졌다.
        'OPTIONS': {'charset': env('DB_CHARSET', 'utf8mb4')}
    }
}


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

# ---------------------------------------------------------------------------
# 다국어
#
# URL 에는 언어를 넣지 않는다(i18n_patterns 미사용). /!/SP12H/ 같은 기존 주소가
# 전부 리다이렉트되고 245명의 북마크와 외부 링크가 깨지기 때문이다.
# 대신 세션·쿠키(django_language)에 저장한다.
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'ko'

LANGUAGES = [
    ('ko', '한국어'),
    ('en', 'English'),
    ('ja', '日本語'),
    ('zh-hans', '简体中文'),
]

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

# 쿠키로도 유지되게 한다. 세션만 쓰면 로그아웃 시 언어가 초기화된다.
LANGUAGE_COOKIE_NAME = 'django_language'
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
LANGUAGE_COOKIE_SAMESITE = 'Lax'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# ---------------------------------------------------------------------------
# 업로드 파일 (프로필 사진)
#
# 운영에서는 Apache 가 /media/ 를 직접 서빙해야 한다. Django 로 파일을
# 흘려보내면 WSGI 워커가 이미지 전송에 묶인다.
#   Alias /media/ /srv/beatmania/media/
# ---------------------------------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = env('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))

# 업로드 상한. 넘으면 Django 가 요청 단계에서 거부한다.
# 폼에서도 따로 검사하지만, 여기서 막아야 디스크·메모리를 안 쓴다.
MAX_AVATAR_BYTES = 2 * 1024 * 1024          # 2MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
# collectstatic 이 모으는 곳. 원본 static/ 과 반드시 달라야 한다 — 같으면
# collectstatic 이 자기 입력 디렉터리에 쓰게 되어 거부한다.
STATIC_ROOT = env('STATIC_ROOT', os.path.join(BASE_DIR, 'staticfiles'))

# whitenoise 가 정적 파일을 직접 낸다. Apache 쪽에 Alias 를 두지 않아도 되고,
# 컨테이너를 어디에 갖다 놔도 같은 방식으로 동작한다.
#
# 해시 붙이는 Manifest 계열 대신 압축만 하는 쪽을 골랐다. 템플릿이 이미
# '?v=' 로 캐시를 깨고 있어 해시가 없어도 되고, Manifest 는 CSS 안에서
# 참조하는 파일이 하나라도 없으면 collectstatic 자체가 실패한다.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

LOGIN_URL = '/login/'

WSGI_APPLICATION = 'wsgi.application'

# custom setting

NOCAPTCHA = False
RECAPTCHA_PUBLIC_KEY = env('RECAPTCHA_PUBLIC_KEY', required=True)
RECAPTCHA_PRIVATE_KEY = env('RECAPTCHA_PRIVATE_KEY', required=True)

# for imgtl image upload service
imgtlkey = env('IMGTL_KEY', '')

# hitcount setting
HITCOUNT_KEEP_HIT_ACTIVE = {'hours': 4}


# ---------------------------------------------------------------------------
# 로깅
#
# 전부 stdout 으로 낸다. 파일로 쓰지 않는 이유는 컨테이너 안의 파일은
# 컨테이너를 다시 만들면 사라지고, 로그 로테이션을 이미지 안에서 또
# 만들어야 하기 때문이다. stdout 으로 내면 docker 의 json-file 드라이버가
# 받아 가고, 크기 제한은 docker-compose.yml 의 max-size/max-file 이 건다.
#
# DEBUG=False 인 Django 는 기본적으로 서버 에러를 ADMINS 에게 메일로만 보낸다.
# ADMINS 가 비어 있으면 500 이 나도 아무 데도 남지 않는다 — 지금까지가 그
# 상태였다. django.request 를 콘솔로 돌려 스택 트레이스가 보이게 한다.
#
# 레벨은 환경변수로 뺐다. 평소에는 INFO, 무언가 쫓을 때만 .env 에서 DEBUG 로
# 올린다. 코드를 고치거나 이미지를 다시 만들 필요가 없다.
# ---------------------------------------------------------------------------
LOG_LEVEL = env('DJANGO_LOG_LEVEL', 'INFO').upper()

LOGGING = {
    'version': 1,
    # 서드파티가 등록해 둔 로거를 죽이지 않는다.
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        # 500 의 스택 트레이스. DEBUG=False 에서도 콘솔에 남는다.
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        # SQL 은 기본적으로 끈다. DEBUG=True 일 때만 나오지만, 그때조차
        # 쿼리 하나마다 한 줄이라 로그가 쓸모없어진다. 필요하면 여기만 켠다.
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # 관리자 대시보드의 명령 실행 로그. 컨테이너 밖에서 진행을 보려면
        # 이것이 stdout 에 있어야 한다.
        'update': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'iidxrank': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}