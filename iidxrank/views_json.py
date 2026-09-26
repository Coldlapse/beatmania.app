#-*- coding: utf-8 -*-
"""서열표 전체 편집(/update/rankedit/<표>/, staff 전용)의 POST 처리.

곡 목록·유저 목록·추천 JSON 은 2026-09-26 에 지웠다(urls.py 참조).
"""

from django.http import JsonResponse
from iidxrank import models


def json_rankedit(request):
  """곡을 다른 분류로 옮기거나(category=분류 pk) 표에서 뺀다(category=-1). staff 전용.

  예전에는 song·category·table 동작도 있었는데 셋 다 호출하면 500 이었다(정의 전 변수 사용,
  request.POST(...) 호출, RankItem 에 없는 remove()). 부르는 곳도 rankedit.html 의 songcategory
  하나뿐이라 지웠다(2026-09-26). 입력이 없거나 숫자가 아니면 500 대신 오류 메시지를 준다.
  """
  if not request.user.is_staff:
    return JsonResponse({'message': 'access denied'})
  if request.method != "POST" or request.POST.get('action') != 'songcategory':
    return JsonResponse({'message': 'invalid access'})
  try:
    pk = int(request.POST.get('id', '0'))
    pk_cate = int(request.POST.get('category', ''))
    songpk = int(request.POST.get('songid', '0'))
  except ValueError:
    return JsonResponse({'message': 'invalid parameter'})

  obj = models.RankItem.objects.filter(id=pk).first()
  obj_cate = None
  if pk_cate != -1:
    obj_cate = models.RankCategory.objects.filter(id=pk_cate).first()
    if obj_cate is None:
      return JsonResponse({'message': 'wrong category id'})

  if obj is None:
    # 표에 아직 없는 곡을 분류에 넣는다. 분류 없이(-1) 새로 만들 수는 없다 — rankcategory 는 NOT NULL
    if obj_cate is None:
      return JsonResponse({'message': 'nothing to remove'})
    obj_song = models.Song.objects.filter(id=songpk).first()
    if obj_song is None:
      return JsonResponse({'message': 'wrong object id'})
    models.RankItem.objects.create(rankcategory=obj_cate, song=obj_song, info='')
  elif obj_cate is None:
    obj.delete()
  else:
    obj.rankcategory = obj_cate
    obj.save()
  return JsonResponse({'message': 'successfully done'})
