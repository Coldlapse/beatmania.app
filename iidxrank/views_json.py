#-*- coding: utf-8 -*-
"""서열표 전체 편집(/update/rankedit/<표>/, staff 전용)의 POST 처리.

곡 목록·유저 목록·추천 JSON 은 2026-09-26 에 지웠다(urls.py 참조).
"""

from django.http import JsonResponse
from iidxrank import models


def json_rankedit(request):
  # staff / admin only
  if not request.user.is_staff:
    return JsonResponse({'message': 'access denied'})

  # in case of POST? -> return JSON result
  if (request.method == "POST"):
    if (request.POST['action'] == 'song'):
      pk = int(request.POST['id'])
      obj = models.RankItem.objects.filter(id=pk).first()
      if (obj == None):
        return JsonResponse({'message': 'wrong object id'})
      pk_cate = int(request.POST['categoryid'])
      if (pk_cate == -1):
        obj.remove()
      else:
        obj_cate = models.RankCategory.objects.filter(id=pk_cate).first()
        if (obj_cate == None):
          return JsonResponse({'message': 'wrong category id'})
        obj.title = request.POST['title']
        obj.tag = request.POST['tag']
        obj.category = obj_cate;
        obj.save();
      return JsonResponse({'message': 'successfully done'})
    elif (request.POST['action'] == 'category'):
      pk = int(request.POST['id'])
      obj_cate = models.RankCategory.objects.filter(id=obj_cate).first()
      if (obj_cate == None):
        return JsonResponse({'message': 'wrong category id'})
      obj_cate.title = request.POST['title']
      obj_cate.categorytype = int(request.POST(['categorytype']))
      obj_cate.sortindex = float(request.POST(['sortindex']))
      obj_cate.save()
      return JsonResponse({'message': 'successfully done'})
    elif (request.POST['action'] == 'table'):
      return JsonResponse({'message': 'not implemented'})
    elif (request.POST['action'] == 'songcategory'):
      pk = int(request.POST['id'])
      obj = models.RankItem.objects.filter(id=pk).first()
      pk_cate = int(request.POST['category'])
      if (pk_cate == -1):
        obj_cate = None
      else:
        obj_cate = models.RankCategory.objects.filter(id=pk_cate).first()
        if (obj_cate == None):
          return JsonResponse({'message': 'wrong category id'})
      if (obj == None):
        # create rankitem object
        # in case of none-created rankitem
        # if even songid doesn't exists,
        # then - serious error.
        songpk = int(request.POST['songid'])
        obj_song = models.Song.objects.filter(id=songpk).first()
        if (obj_song == None):
          return JsonResponse({'messasge': 'wrong object id'})
        else:
          obj = models.RankItem.objects.create(
                  rankcategory = obj_cate,
                  song = obj_song,
                  info = ''
                  )
      else:
        # delete or modify songitem's category
        if (obj_cate == None):
          print('deleted')
          obj.delete()
        else:
          print('%s to %s' % (obj.song.songtitle, obj_cate.categoryname))
          obj.rankcategory = obj_cate
          obj.save()
      return JsonResponse({'message': 'successfully done'})
  else:
    return JsonResponse({'message': 'invalid access'})
