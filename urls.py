"""iidxrank URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog
import iidxrank.views as views
import iidxrank.views_json as views_json
import iidxrank.views_manage as views_manage
import board.views as views_board



urlpatterns = [

	url(r'', include([
        
	# utilities (admin, imgtl ...)
	    url(r'^admin/', admin.site.urls),
        # 언어 전환. URL 에 언어를 넣지 않고 쿠키/세션에 저장한다.
        # set_language 는 POST + next 로만 동작하므로 오픈 리다이렉트가 되지 않는다.
            url(r'^i18n/', include('django.conf.urls.i18n')),
        # JS 안의 번역 문자열용 카탈로그
            url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
            url(r'^imgtl/$', views.imgtl),
            url(r'^imgdownload/$', views.imgdownload),
            # IIDX IDs are stored hyphenated (e.g. 5241-1234), so \w+ is not enough
            url(r'^qpro/(?P<iidxid>[\w-]+)/$', views.qpro),
            url(r'^qpro/!/$', views.qpro),

	# update (NOT WORKING NOW)
            url(r'^update/', include([
                    url(r'^rankedit/(?P<tablename>\w+)/$', views.ranktableedit, name="ranktableedit"),
            ])),

        # comment, board
            url(r'^board/', include([
                    url(r'^view/(?P<postid>[0-9]+)/$', views_board.view, name="postview"),
                    url(r'^modify/(?P<postid>[0-9]+)/$', views_board.modify, name="postmodify"),
                    url(r'^delete/(?P<postid>[0-9]+)/$', views_board.delete, name="postdelete"),
                    url(r'^comment/add/(?P<postid>[0-9]+)/$', views_board.comment_add, name="comment_add"),
                    url(r'^comment/delete/$', views_board.comment_delete, name="comment_delete"),
                    url(r'^(?P<boardname>\w+)/$', views_board.list, name="postlist"),
                    url(r'^(?P<boardname>\w+)/(?P<page>[0-9]+)/$', views_board.list, name="postlist"),
                    url(r'^(?P<boardname>\w+)/write/$', views_board.write, name="postwrite"),
            ])),

        # select music
            url(r'^musiclist/$', views.musiclist),
            url(r'^json/', include([
                    url(r'^musiclist/(?P<type>\w+)/level/(?P<level>[0-9]+)/$', views_json.json_level),
                    url(r'^musiclist/(?P<type>\w+)/series/(?P<series>\w+)/$', views_json.json_series),
                    url(r'^userlist/$', views_json.json_user),
                    # username
                    url(r'^recommend/(?P<username>(\w|-)+)/(?P<type>\w+)/$', views_json.json_recommend),
                    url(r'^recommend/(?P<username>(\w|-)+)/(?P<type>\w+)/(?P<level>[0-9]+)/$', views_json.json_recommend),
            ])),

            # hijack
            url(r'^hijack/', include('hijack.urls', namespace='hijack')),

        # membership
            url(r'^!/login/$', views.login, name='login'),
            url(r'^!/join/$', views.join),
            url(r'^!/logout/$', views.logout),
            url(r'^!/account/$', views.account),
            url(r'^!/setpassword/$', views.set_password),
            url(r'^!/withdraw/$', views.withdraw),

            url(r'^!/rankedit/(?P<id>[0-9]+)/$', views.rankedit),
            url(r'^!/modify/$', views.modify),

        # API
            # 2. API 엔드포인트 URL
            url(r'^api/v1/update-typing-count/$', views.update_typing_count_api, name='update_typing_count_api'),
            # ▼ 대기 현황 Agent용 POST API 추가
            url(r'^api/v1/update-machine-status/$', views.update_machine_status_api, name='update_machine_status_api'),
        # common urls (mainpage, userpage, rankpage)
            #url(r'^$', views.mainpage, name="main"),
            url(r'^$', RedirectView.as_view(url='/!/'), name="main"),
            #url(r'^!/$', RedirectView.as_view(url='/')),
            url(r'^!/$', views.userpage),
            url(r'^!/songrank/$', views.songrank),
            url(r'^!/userrank/$', views.userrank),
            url(r'^!/update/$', views.updatelamp),
            url(r'^!/converter', views.converter),
            url(r'^!/roadmap', views.roadmap),
            url(r'^!/analytics/$', views.rankpage_analytics, name="analytics"), # 이 줄 추가
            # ▼ 대기 현황 위젯 및 JSON API 추가
            # 위젯 페이지: /!/status/hwajeong_iidx_1/
            url(r'^!/status/(?P<machine_id>[\w-]+)/$', views.machine_status_view, name="machine_status_view"),
            # 실시간 갱신용 JSON: /!/status/hwajeong_iidx_1/json/
            url(r'^!/status/(?P<machine_id>[\w-]+)/json/$', views.get_machine_status_json, name="get_machine_status_json"),
            url(r'^!/my-page/$', views.my_page_view, name="my_page"),

        # 관리자 대시보드 (staff 전용). 서버에서 명령을 실행하므로
        # tablename 패턴(^!/(\w+)/$)보다 반드시 위에 있어야 한다.
            url(r'^!/manage/$', views_manage.dashboard, name="manage_dashboard"),
            url(r'^!/manage/run/$', views_manage.run_command, name="manage_run_command"),
            url(r'^!/manage/run/(?P<run_id>[0-9]+)/$', views_manage.run_detail, name="manage_run"),
            url(r'^!/manage/run/(?P<run_id>[0-9]+)/log/$', views_manage.run_log, name="manage_run_log"),
            url(r'^!/manage/run/(?P<run_id>[0-9]+)/abort/$', views_manage.abort_run, name="manage_run_abort"),
            url(r'^!/manage/run/(?P<run_id>[0-9]+)/answer/$', views_manage.answer_prompt, name="manage_run_answer"),
            url(r'^!/(?P<tablename>\w+)/$', views.rankpage, name="rankpage"),
            url(r'^!/(?P<tablename>\w+)/table/$', views.ranktable),
            url(r'^!/(?P<tablename>\w+)/json/$', views.rankjson),
            # username
            url(r'^(?P<username>(\w|-)+)/', include([
                    url(r'^$', views.userpage),
                    url(r'^json/$', views.userjson),
                    # /stat/recm/ and /stat/skill/ removed: both were served from
                    # json.iidx.me, whose DNS record no longer exists.
                    url(r'^(?P<tablename>\w+)/$', views.rankpage, name="rankpage"),
                    url(r'^(?P<tablename>\w+)/table/$', views.ranktable),
                    url(r'^(?P<tablename>\w+)/json/$', views.rankjson),
            ])),

	])),
]

# 개발 서버에서만 업로드 파일을 Django 가 서빙한다.
# 운영에서는 Apache 가 /media/ 를 Alias 로 직접 서빙해야 한다 —
# WSGI 워커가 이미지 전송에 묶이면 안 된다.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
