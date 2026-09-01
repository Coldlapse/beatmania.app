# -*- coding: utf-8 -*-
"""아이디로 쓸 수 없는 이름.

두 갈래로 나눈다. 쓰임이 다르고, 섞으면 한쪽이 다른 쪽을 망가뜨린다.

SITE_PATHS
    URL 판정에 쓴다. `legacy.py` 가 "남은 모든 최상위 경로"를 옛 사용자
    경로로 보고 **영구** 리다이렉트하는데, 그 그물에 사이트 자신의 주소가
    걸리면 안 된다. 방문자 브라우저가 301 을 오래 캐시하므로, 한 번 걸리면
    나중에 그 주소로 페이지를 만들어도 이미 방문한 사람은 계속 /u/... 로
    날아간다. 실제로 /status/ 가 그렇게 물렸다.

    **여기에는 이미 쓰이는 계정 이름을 넣으면 안 된다.** 넣는 순간 그 사람의
    옛 주소(/이름/)가 404 가 된다. 지금 'test' 계정이 있어서 그 이름은 뺐다.

USERNAME_BLOCKED
    가입 시 막을 이름. SITE_PATHS 를 포함하고, 거기에 헷갈리거나 사칭에
    쓰일 만한 것을 더한다. 이쪽은 넓게 잡아도 기존 계정에 영향이 없다 —
    가입할 때만 보기 때문이다.

새 주소를 만들면 SITE_PATHS 에 넣어라. 넣지 않으면 그 주소는 위 그물에
걸려 한동안 엉뚱한 곳으로 간다.
"""

# 사이트가 쓰거나 쓸 최상위 경로.
SITE_PATHS = frozenset("""
about account admin analytics api board converter embed health i18n
imgdownload join json jsi18n login logout manage media musiclist my-page
overjoy privacy rankedit roadmap robots.txt favicon.ico songrank static
status sync table u user userrank
""".split())

# 위에 더해 가입만 막을 이름.
_EXTRA = frozenset("""
administrator beatmania contact copyright dev developer donate faq
feed help home index legal mail moderator news notice official owner
report root rss security site sitemap staff support system terms
undefined null none anonymous guest
""".split())

USERNAME_BLOCKED = SITE_PATHS | _EXTRA


def is_blocked_username(name):
    """가입에 쓸 수 없는 이름인가."""
    return (name or '').strip().lower() in USERNAME_BLOCKED


def is_site_path(first_segment):
    """URL 의 첫 조각이 사이트 자신의 경로인가."""
    return (first_segment or '').lower() in SITE_PATHS
