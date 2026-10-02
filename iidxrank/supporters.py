# -*- coding: utf-8 -*-
"""후원자 배지 — 어디에 보이는지 규칙을 한곳에 둔다.

  서열표(본인·남 모두) · 일일 타건 리더보드 · 프로젝트 소개 목록: 공개(public)한 후원자만.
  비공개로 두면 본인에게도 보이지 않는다 — 계정 설정에서 다시 켜면 곧바로 보인다(사용자 결정 2026-10-02).

지정·해제는 관리자 대시보드(views_manage.supporter_*), 공개 여부는 본인이 계정 설정에서 바꾼다.
"""
from iidxrank import models


def is_public(user):
    """서열표 프로필에 배지를 달지."""
    return user is not None and models.Supporter.objects.filter(user=user, public=True).exists()


def public_user_ids(user_ids):
    """주어진 사용자 중 배지를 공개한 후원자의 id 집합(리더보드 한 번 조회용)."""
    return set(models.Supporter.objects.filter(user_id__in=list(user_ids), public=True)
               .values_list('user_id', flat=True))


def public_list():
    """프로젝트 소개의 후원자 목록. 지정된 순서. 프로필 비공개인 사람은 링크 없이 이름만."""
    rows = (models.Supporter.objects.filter(public=True).select_related('user')
            .order_by('since'))
    private_ids = set(models.Player.objects.filter(private=True, user_id__in=[r.user_id for r in rows])
                      .values_list('user_id', flat=True))
    return [{'nickname': r.user.first_name or r.user.username,
             'username': None if r.user_id in private_ids else r.user.username}
            for r in rows]
