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


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'iidxrank',
    'board',
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
        'OPTIONS': {'charset': env('DB_CHARSET', 'utf8')}
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
# https://docs.djangoproject.com/en/1.8/howto/static-files/
#STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
LOGIN_URL = '/login/'
#    '/home/sadang/iidxranktable/static/',
#]

# redis Websocket part

WSGI_APPLICATION = 'wsgi.application'
WEBSOCKET_URL = '/ws/'
WS4REDIS_EXPIRE = 7200	# reconnection delay
WS4REDIS_PREFIX = 'ws'	# for convinence in redis

# custom setting

NOCAPTCHA = False
RECAPTCHA_PUBLIC_KEY = env('RECAPTCHA_PUBLIC_KEY', required=True)
RECAPTCHA_PRIVATE_KEY = env('RECAPTCHA_PRIVATE_KEY', required=True)

# for imgtl image upload service
imgtlkey = env('IMGTL_KEY', '')

# hitcount setting
HITCOUNT_KEEP_HIT_ACTIVE = {'hours': 4}