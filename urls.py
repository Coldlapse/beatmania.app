"""beatmania.app URL 설계

이전에는 "내 것"을 뜻하는 구분자로 `!` 를 썼다: `/!/SP12H/` 는 내 서열표,
`/sadang/SP12H/` 는 남의 서열표. 사용자 이름이 최상위 와일드카드였기 때문에
`!` 없이는 서열표 이름과 사용자 이름을 구별할 수 없었다.

이제 네임스페이스로 나눈다.

    /                       내 서열표 목록 (프로필)
    /table/<name>/          내 서열표
    /table/<name>/embed/    내 서열표 (임베드용)
    /table/<name>/json/     내 서열표 JSON
    /u/<username>/          남의 프로필
    /u/<username>/table/... 남의 서열표

최상위 와일드카드가 사라져 `!` 가 필요 없어졌고, 나머지 페이지도 전부
평범한 경로로 내려왔다(`/login/`, `/analytics/` ...).

**옛 주소는 전부 301 로 넘긴다.** 245명의 북마크와 디스코드·velog 의 외부
링크, 검색엔진 색인이 옛 주소를 가리키고 있다. `legacy.py` 참조.
"""

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog

import board.views as views_board
import iidxrank.legacy as legacy
import iidxrank.views as views
import iidxrank.views_json as views_json
import iidxrank.views_manage as views_manage
import iidxrank.views_overjoy as views_overjoy
import iidxrank.views_status as views_status
import iidxrank.views_typing as views_typing

# 서열표 한 개에 딸린 하위 경로. 내 것과 남의 것이 같은 모양을 갖도록 공유한다.
table_patterns = [
    url(r'^$', views.rankpage, name='rankpage'),
    url(r'^embed/$', views.ranktable, name='ranktable_embed'),
    url(r'^json/$', views.rankjson, name='ranktable_json'),
]

urlpatterns = [
    # --- 유틸리티 ---------------------------------------------------------
    url(r'^admin/', admin.site.urls),
    # 언어 전환. URL 에 언어를 넣지 않고 쿠키/세션에 저장한다.
    # set_language 는 POST + next 로만 동작하므로 오픈 리다이렉트가 되지 않는다.
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    url(r'^imgdownload/$', views.imgdownload, name='imgdownload'),

    # --- 서열표 -----------------------------------------------------------
    url(r'^$', views.userpage, name='home'),
    url(r'^table/(?P<tablename>\w+)/', include(table_patterns)),
    url(r'^u/(?P<username>[\w-]+)/$', views.userpage, name='userpage'),
    url(r'^u/(?P<username>[\w-]+)/table/(?P<tablename>\w+)/', include(table_patterns)),

    # --- 일반 페이지 -------------------------------------------------------
    url(r'^songrank/$', views.songrank, name='songrank'),
    url(r'^userrank/$', views.userrank, name='userrank'),
    url(r'^musiclist/$', views.musiclist, name='musiclist'),
    url(r'^converter/$', views.converter, name='converter'),
    # '개발 로드맵' 이었다. 개발자 소개를 같이 담게 되어 이름을 넓혔다.
    # 옛 주소는 넘긴다.
    url(r'^about/$', views.roadmap, name='about'),
    url(r'^roadmap/$',
        RedirectView.as_view(pattern_name='about', permanent=True)),
    url(r'^privacy/$', views.privacy, name='privacy'),

    # sadang.org 에서 옮겨온 Overjoy 난이도표.
    # header.json 은 BMS 구동기가 읽는 규약 주소다. 사람이 보는 페이지보다
    # 옮기기 어려우니(클라이언트 쪽 재등록이 필요) 주소를 함부로 바꾸지 말 것.
    url(r'^overjoy/$', views_overjoy.page, name='overjoy'),
    url(r'^overjoy/header\.json$', views_overjoy.header_json,
        name='overjoy_header'),
    # 서비스 현황. 예전 이름은 '사이트뷰 분석'(/analytics/)이었다.
    # 옛 주소는 그대로 두고 새 주소로 넘긴다 — 외부에 걸린 링크가 있다.
    url(r'^status/$', views_status.service_status, name='service_status'),
    url(r'^status/views\.json$', views_status.views_json,
        name='status_views_json'),
    url(r'^analytics/$',
        RedirectView.as_view(pattern_name='service_status', permanent=True)),
    # 일일 타건 기록. 로그인하지 않아도 열린다 — 리더보드가 있어서 남이 봐도
    # 의미가 있다. 본인 기록 부분만 로그인한 사람에게 보인다.
    url(r'^my-page/$', views_typing.my_page, name='my_page'),
    url(r'^my-page/typing\.json$', views_typing.typing_json,
        name='typing_json'),
    # API 토큰은 계정 설정에 가까워 따로 뺐다.
    url(r'^account/token/$', views_typing.api_token, name='api_token'),
    url(r'^account/token/reissue/$', views_typing.api_token_reissue,
        name='api_token_reissue'),
    url(r'^status/(?P<machine_id>[\w-]+)/$',
        views.machine_status_view, name='machine_status_view'),
    url(r'^status/(?P<machine_id>[\w-]+)/json/$',
        views.get_machine_status_json, name='get_machine_status_json'),

    # --- 계정 -------------------------------------------------------------
    url(r'^login/$', views.login, name='login'),
    url(r'^join/$', views.join, name='join'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^account/$', views.account, name='account'),
    url(r'^setpassword/$', views.set_password, name='setpassword'),
    url(r'^withdraw/$', views.withdraw, name='withdraw'),

    # --- 기록 편집 --------------------------------------------------------
    url(r'^lampupdate/$', views.updatelamp, name='updatelamp'),
    url(r'^rankedit/(?P<id>[0-9]+)/$', views.rankedit, name='rankedit'),
    url(r'^modify/$', views.modify, name='modify'),
    url(r'^update/rankedit/(?P<tablename>\w+)/$',
        views.ranktableedit, name='ranktableedit'),

    # --- 게시판 -----------------------------------------------------------
    url(r'^board/', include([
        url(r'^view/(?P<postid>[0-9]+)/$', views_board.view, name='postview'),
        url(r'^modify/(?P<postid>[0-9]+)/$', views_board.modify, name='postmodify'),
        url(r'^delete/(?P<postid>[0-9]+)/$', views_board.delete, name='postdelete'),
        url(r'^comment/add/(?P<postid>[0-9]+)/$', views_board.comment_add, name='comment_add'),
        url(r'^comment/delete/$', views_board.comment_delete, name='comment_delete'),
        url(r'^(?P<boardname>\w+)/$', views_board.list, name='postlist'),
        url(r'^(?P<boardname>\w+)/(?P<page>[0-9]+)/$', views_board.list, name='postlist'),
        url(r'^(?P<boardname>\w+)/write/$', views_board.write, name='postwrite'),
    ])),

    # --- JSON -------------------------------------------------------------
    url(r'^json/', include([
        url(r'^musiclist/(?P<type>\w+)/level/(?P<level>[0-9]+)/$', views_json.json_level),
        url(r'^musiclist/(?P<type>\w+)/series/(?P<series>\w+)/$', views_json.json_series),
        url(r'^userlist/$', views_json.json_user, name='json_userlist'),
        url(r'^recommend/(?P<username>[\w-]+)/(?P<type>\w+)/$', views_json.json_recommend),
        url(r'^recommend/(?P<username>[\w-]+)/(?P<type>\w+)/(?P<level>[0-9]+)/$',
            views_json.json_recommend),
    ])),

    # --- API --------------------------------------------------------------
    url(r'^api/v1/update-typing-count/$',
        views.update_typing_count_api, name='update_typing_count_api'),
    url(r'^api/v1/update-machine-status/$',
        views.update_machine_status_api, name='update_machine_status_api'),

    # --- 관리자 대시보드 (staff 전용) --------------------------------------
    url(r'^manage/$', views_manage.dashboard, name='manage_dashboard'),
    url(r'^manage/run/$', views_manage.run_command, name='manage_run_command'),
    url(r'^manage/run/(?P<run_id>[0-9]+)/$', views_manage.run_detail, name='manage_run'),
    url(r'^manage/run/(?P<run_id>[0-9]+)/log/$', views_manage.run_log, name='manage_run_log'),
    url(r'^manage/run/(?P<run_id>[0-9]+)/abort/$', views_manage.abort_run, name='manage_run_abort'),
    url(r'^manage/run/(?P<run_id>[0-9]+)/answer/$', views_manage.answer_prompt, name='manage_run_answer'),

    # --- 옛 주소 301 리다이렉트 -------------------------------------------
    # 반드시 맨 아래에 둔다. 위의 실제 경로가 먼저 매칭되어야 한다.
    url(r'^!/$', RedirectView.as_view(url='/', permanent=True)),
    url(r'^!/(?P<rest>.*)$', legacy.redirect_bang, name='legacy_bang'),
    # 옛 최상위 사용자 경로(/sadang/SP12H/). 실제 사용자일 때만 넘긴다 —
    # 오타까지 리다이렉트하면 404 가 사라져 버린다.
    url(r'^(?P<username>[\w-]+)/(?P<rest>.*)$', legacy.redirect_user),
]

# 개발 서버에서만 업로드 파일을 Django 가 서빙한다.
# 운영에서는 Apache 가 /media/ 를 Alias 로 직접 서빙해야 한다 —
# WSGI 워커가 이미지 전송에 묶이면 안 된다.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
