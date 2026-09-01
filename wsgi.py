"""WSGI 진입점.

gunicorn 이 `wsgi:application` 으로 이것을 잡는다.

예전에는 여기에 sys.path.append('/home/sadang/iidxranktable') 이 있었다.
mod_wsgi 가 서버의 절대 경로를 알아야 settings 를 import 할 수 있어서였다.
지웠다 — 컨테이너에서는 WORKDIR 이 /app 이라 필요 없고, public 저장소에
서버의 디렉터리 구조를 적어 둘 이유도 없다.

되돌릴 곳: 라이브의 mod_wsgi 는 /home/sadang/iidxranktable 을 가리키고
있고 그 디렉터리는 git 저장소가 아니다. 즉 이 줄을 지워도 지금 돌고 있는
사이트에는 영향이 없다.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

application = get_wsgi_application()
