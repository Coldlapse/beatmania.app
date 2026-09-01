#-*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.exceptions import MultipleObjectsReturned
from django.urls import reverse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.clickjacking import xframe_options_exempt
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.db.models import F
from iidxrank import models
from iidxrank import forms
import settings
from iidxrank import rankpage as rp
import update.parser_csv as parser_csv
from iidxrank import iidx
from iidxrank import views_json
import json
import base64
import os
import requests


from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.db.models import Count
from datetime import datetime
from django.utils import timezone
from datetime import timedelta

from hitcount.models import HitCount
from hitcount.views import HitCountMixin
from django.core.paginator import Paginator







def userpage(request, username=None):
    if username is None:
        # load player information from DB
        pobj = rp.get_player_from_request(request)
        userinfo = rp.get_udata_from_player(pobj)
    else:
        player, reason = rp.find_player_from_id(username)
        if player is None:
            # 없는 계정인지 비공개인지 구별해 주지 않는다 — 구별이 곧 계정 열거다
            return _unavailable(request, username)
        userinfo = rp.get_udata_from_player(player, username)
    # 남의 페이지인지 알려 준다. 여기서만 판단하고 화면은 그대로 쓴다 —
    # 로그인 여부가 아니라 '주소에 아이디가 있는가' 가 기준이다.
    # 내 페이지는 /(아이디 없음), 남의 페이지는 /u/<아이디>/ 다.
    return render(request, 'user/userpage.html', {
        'userdata': userinfo,
        'viewing_other': username is not None,
        'other_username': username,
    })

def get_pdata(request, username, tablename):
    """서열표 데이터를 만든다.

    username 이 None 이면 로그인한 본인의 서열표다.
    실패하면 rp.NOT_FOUND / rp.PRIVATE 문자열을 돌려준다 — 호출한 뷰가
    404 로 할지 '비공개' 안내로 할지 정한다.
    """
    table = rp.get_ranktable(tablename)
    if table is None:
        return rp.NO_SUCH_TABLE

    if username is None:
        player = rp.get_player_from_request(request)
        pdata = rp.get_pdata_from_player(player, table)
        # 로그인한 본인만 편집할 수 있다
        pdata['editable'] = bool(player)
    else:
        player, reason = rp.find_player_from_id(username)
        if player is None:
            return reason
        pdata = rp.get_pdata_from_player(player, table, username)
        pdata['editable'] = False
    return pdata


def _unavailable(request, username):
    """프로필을 볼 수 없을 때의 응답.

    없는 계정과 비공개 계정에 **같은 화면, 같은 상태코드**를 준다.
    다르게 응답하면 아이디를 무차별 대입해 존재 여부를 알아낼 수 있다.
    """
    return render(request, 'user/unavailable.html',
                  {'username': username}, status=404)


def _pdata_or_response(request, pdata, username):
    """get_pdata 결과가 실패 사유면 알맞은 응답을 만든다. 아니면 None."""
    if pdata == rp.UNAVAILABLE:
        return _unavailable(request, username)
    if pdata == rp.NO_SUCH_TABLE or pdata is None:
        raise Http404
    return None

def rankpage(request, username=None, tablename="SP12"):
    pdata = get_pdata(request, username, tablename)
    early = _pdata_or_response(request, pdata, username)
    if early is not None:
        return early
    # append additional data
    pdata['tabledata_json'] = rp.serialize_ranktable(pdata)

    # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
    # django-hitcount의 내장 로직을 사용하여 조회수를 처리합니다.
    # ---------------------------------------------------------
    try:
        # 조회수를 집계할 대상 객체를 가져옵니다.
        ranktable = models.RankTable.objects.get(tablename=tablename)

        # 1. 대상 객체에 연결된 조회수 객체를 가져옵니다.
        hit_count = HitCount.objects.get_for_object(ranktable)

        # 2. HitCountMixin의 hit_count 함수를 호출하여 조회수를 증가시킵니다.
        #    이 함수 내에 세션, 사용자 기반의 중복 방지 로직이 이미 포함되어 있습니다.
        #    (별도의 중복 확인 로직이 필요 없습니다.)
        hit_count_response = HitCountMixin.hit_count(request, hit_count)

    except Exception as e:
        # 조회수 집계 중 오류가 발생하더라도 페이지 렌더링은 계속됩니다.
        # print(f"Hit count error: {e}")
        pass
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    return render(request, 'user/rankview.html', pdata)

"""
def detailpage(request, username="!", tablename="SP12"):
    d = retrieve_userdata(username, tablename)
    return render(request, 'user/detailview.html', d)
"""

def ranktable(request, username=None, tablename="SP12"):
    pdata = get_pdata(request, username, tablename)
    early = _pdata_or_response(request, pdata, username)
    if early is not None:
        return early
    if (request.GET.get('edit') != None):
        pdata['edit'] = True
    
    return render(request, 'ranktable.html', pdata)

def rankjson(request, username=None, tablename="SP12"):
    pdata = get_pdata(request, username, tablename)
    early = _pdata_or_response(request, pdata, username)
    if early is not None:
        return early
    return JsonResponse(pdata)

def rankedit(request, id=-1):
    # render rankedit page for each user (for internal load)
    if (not request.user.is_authenticated):
        islogined = False
        valid = False
        song_obj = None
        title = ''
    else:
        islogined = True
        user = request.user
        # check song is exists
        song_obj = models.Song.objects.filter(id=id).first()
        title = song_obj.songtitle
        if (song_obj == None):
            valid = False
        else:
            valid = True
            # fetch playrecord if available
            pr_obj = models.PlayRecord.objects.filter(player_id=user.id, song_id=id).first()
            if (pr_obj == None):
                pr_obj = models.PlayRecord()
    return render(request, 'user/rankedit.html', {
        'valid': valid,
        'islogined': islogined,
        'title': title,
        'item': pr_obj,
        })

def ranktableedit(request, tablename):
    tablename = tablename.upper()

    # only admin can access it
    if (not request.user.is_staff):
        raise PermissionDenied
    
    # in case of POST? -> return JSON result
    if (request.method == "POST"):
        return views_json.json_rankedit(request)
    
    # check is valid table
    ranktable = models.RankTable.objects.filter(tablename=tablename).first()
    if (ranktable == None):
        raise Http404
    # compile table data
    songs = rp.search_songs_from_ranktable(ranktable)
    prs = rp.generate_pr(songs)
    categories = rp.categorize_musicdata(prs, ranktable, False)
    tableinfo = rp.get_ranktable_metadata(ranktable)
    return render(request, 'rankedit.html', { 'categories': categories, 'tableid': ranktable.id, 'tableinfo': tableinfo })

# /iidx/musiclist
#@xframe_options_exempt
def musiclist(request):
    # all the other things will done in json & html
    return render(request, 'musiclist.html')

# converter
def converter(request):
    return render(request, 'converter.html')

# roadmap
def roadmap(request):
    # 템플릿 이름은 roadmap.html 그대로다. 개발자 소개가 위에 붙었을 뿐
    # 로드맵이 이 페이지의 본체라, 파일까지 옮기면 이력만 끊긴다.
    return render(request, 'roadmap.html')


def privacy(request):
    return render(request, 'privacy.html')

# /iidx/!/songrank/
def songrank(request):
    return render(request, 'songrank.html')

# /iidx/!/userrank/
def userrank(request):
    return render(request, 'userrank.html')


"""
user related part
"""

# /!/login/
login_django = login
def login(request):
    if (request.user.is_authenticated):
        return redirect('home')
    if (request.method == "POST"):
        form = forms.LoginForm(request.POST)
        if (form.is_valid()):
            user = authenticate(username=form.data['id'], password=form.data['password'])
            login_django(request, user)
            return redirect('home')
    else:
        form = forms.LoginForm()

    return render(request, 'user/login.html', {'form': form})

# /!/join/
def join(request):
    if (request.user.is_authenticated):
        return redirect('home')
    if (request.method == "POST"):
        form = forms.JoinForm(request, request.POST)
        if (form.is_valid()):
            user = User.objects.create_user(
                    username=form.data['id'],
                    first_name=form.data['id'],
                    email=form.data['email'],
                    password=form.data['password'])
            # automatically create player object
            #rp.get_player_from_user(user)
            rp.newplayer(user)
            user = authenticate(username=form.data['id'], password=form.data['password'])
            login_django(request, user)
            return redirect('home')
    else:
        form = forms.JoinForm(request)
    return render(request, 'user/join.html', {'form': form})

# /!/logout/
logout_django = logout
def logout(request):
    logout_django(request)
    return redirect('home')

# /!/withdraw/
def withdraw(request):
    if (request.user.is_superuser):
        raise Exception("Superuser CANNOT withdraw!")
    if (not request.user.is_authenticated):
        return redirect('login')
    if (request.method == "POST"):
        form = forms.WithdrawForm(request.POST)
        if (form.is_valid()):
            user = request.user
            user.delete()
            logout_django(request)
            return redirect('home')
    else:
        form = forms.WithdrawForm(initial={'id': request.user.username})
    return render(request, 'user/withdraw.html', {'form': form})

# /!/account/
def account(request):
    if (not request.user.is_authenticated):
        return redirect('home')
    user = request.user
    player = rp.get_player_from_request(request)
    # Player 가 없는 계정이 있다. 가입 흐름은 rp.newplayer 로 만들어 주지만
    # createsuperuser 나 admin 으로 만든 계정에는 없다. 가드가 없어서 이
    # 화면이 통째로 500 이었다(AttributeError: 'NoneType' ... 'iidxid').
    # 여기서 만들어 준다 - 가입 때와 같은 함수라 결과도 같다.
    if (player is None):
        player = rp.newplayer(user)
    if (request.method == "POST"):
        form = forms.AccountForm(request.POST)
        avatar_form = forms.AvatarForm(request.POST, request.FILES)

        # 사진 삭제는 폼 유효성과 무관하게 처리한다
        if (request.POST.get('avatar-clear') and player.avatar):
            player.avatar.delete(save=False)
            player.avatar = None
            player.save()

        if (avatar_form.is_valid() and avatar_form.cleaned_data.get('avatar')):
            # 새 사진을 올리면 이전 파일은 지운다. 안 그러면 디스크에 계속 쌓인다.
            if (player.avatar):
                player.avatar.delete(save=False)
            player.avatar = avatar_form.cleaned_data['avatar']
            player.save()

        if (form.is_valid()):
            # form.data 는 화면에서 온 날것이다. IIDX ID 는 칸 네 개로 나뉘어
            # 오므로 날것으로는 읽을 수 없다. 검사와 조립을 마친
            # cleaned_data 를 쓴다.
            cd = form.cleaned_data
            user.first_name = cd['first_name']
            player.iidxid = cd['iidxid']
            player.iidxnick = cd['iidxnick']
            player.spclass = cd['spclass']
            player.dpclass = cd['dpclass']
            player.private = bool(cd.get('private'))
            user.save()
            player.save()
            return redirect('home')
    else:
        avatar_form = forms.AvatarForm()
        form = forms.AccountForm(initial={
            'first_name': user.first_name,
            'iidxid': player.iidxid,
            'iidxnick': player.iidxnick,
            'spclass': player.spclass,
            'dpclass': player.dpclass,
            'private' : player.private
            })
    return render(request, 'user/account.html', {
        'form': form, 'avatar_form': avatar_form, 'player': player})

# /!/set_password/
def set_password(request):
    if not request.user.is_authenticated:
        return redirect('home')
    if (request.method == "POST"):
        # 첫 인자가 user 다. 폼이 현재 비밀번호를 대조해야 하기 때문이다.
        form = forms.SetPasswordForm(request.user, request.POST)
        if (form.is_valid()):
            user = request.user
            # form.data(생 POST) 가 아니라 cleaned_data 를 쓴다.
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            # 비밀번호가 바뀌면 세션 인증 해시가 달라져 그 계정의 모든 세션이
            # 끊긴다. 그것이 옳다 — 탈취된 세션도 같이 끊겨야 비밀번호를 바꾼
            # 의미가 있다. 다만 지금 바꾸고 있는 본인까지 튕기면 "바꿨는데 왜
            # 로그아웃되지" 가 된다(실제로 그랬다). 이 한 줄이 현재 세션만
            # 새 해시로 갱신한다.
            update_session_auth_hash(request, user)
            return redirect('account')
    else:
        form = forms.SetPasswordForm(request.user)
    return render(request, 'user/setpassword.html', {'form':form})

# /!/update/
# XXX: should allow cross-domain request to allow extern site
@csrf_exempt
def updatelamp(request):
    form = {'is_valid': True, 'errors':'no errors.', 'message': ['Ready.',]}
    if (request.method == "POST"):
        if (not request.user.is_authenticated):
            return JsonResponse({'status': 'Please login to iidx.me first.'})
        if ('type' not in request.POST or 'file' not in request.FILES):
            form['is_valid'] = False
            form['errors'] = 'Invalid form data.'
        else:
            import csv
            csvtype = request.POST['type']
            csvfile = request.FILES['file']
            tbl = csv.reader(csvfile, delimiter=',')
            log = []
            print("* updatelamp: user %s, %s" % (request.user.username, csvtype))
            parser_csv.update(tbl, csvtype, request.user, log)
            form['message'] = log
            print("* updatelamp end.")
    if (not request.user.is_authenticated):
        return redirect('home')
    return render(request, 'user/updatelamp.html', {'form':form})

# JSON
# /!/modify/
def modify(request):
    if (not request.user.is_authenticated):
        return JsonResponse({'code': 1, 'message': 'please log in'})
    user = request.user
    player = rp.get_player_from_request(request)
    if (request.method == "POST"):
        action = request.POST.get('action', '')
        v = request.POST.get('v', '')
    else:
        action = request.GET.get('action', '')
        v = request.GET.get('v', '')
    if (action == 'edit'):
        lst = json.loads(v)
        for l in lst:
            sid = int(l['id'])
            if ('clear' in l):
                desc = { 'clear': int(l['clear']) }
            if ('rate' in l):
                desc['rate'] = float(l['rate'])
            if ('rank' in l):
                desc = { 'rank': int(l['rank']) }
            #desc['rank'] = int(l['rank'])
            if ('score' in l):
                desc['score'] = int(l['score'])
            log = []
            if (not rp.update_record(sid, player, desc, log)):
                return JsonResponse({
                    'code': 1,
                    'message': log[0],
                    'detail':str(e)
                })
    elif (action == 'delete'):
        try:
            sid = int(v)
            song = models.Song.objects.get(id=sid)
            pr = models.PlayRecord.objects.filter(song=song,player=player).first()
            if (pr):
                pr.delete()
        except Exception as e:
            return JsonResponse({'code': 1, 'message': 'Invalid, or not existing Song ID'})
    elif (action == 'djname'):
        player.iidxnick = v
        player.save()
    elif (action == 'iidxid'):
        player.iidxid = v
        player.save()
    elif (action == 'spclass'):
        player.spclass = int(v)
        player.save()
    elif (action == 'dpclass'):
        player.dpclass = int(v)
        player.save()
    else:
        return JsonResponse({'code': 1, 'message': 'invalid action'})
    return JsonResponse({'code': 0, 'message': 'Done'})
"""
user end
"""

# imgdownload/
@csrf_exempt
def imgdownload(request):
    if request.method != "POST":
        # allow only POST method
        raise PermissionDenied
    filename = request.POST['name']
    pngdata = base64.b64decode(request.POST['base64'])
    print("got request: %s (%d byte)" % (filename, len(pngdata)))
    r = HttpResponse(pngdata, content_type="application/octet-stream")
    r['Content-Disposition'] = 'attachment; filename=%s' % filename
    return r





# --- 1. Electron 앱과 통신할 API 뷰 ---
@csrf_exempt
def update_typing_count_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method is required.'}, status=405)

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Token '):
        return JsonResponse({'error': 'Authorization header is missing or invalid.'}, status=401)
    
    token_key = auth_header.split(' ')[1]
    try:
        api_token = models.ApiToken.objects.select_related('user').get(key=token_key)
        user = api_token.user
    except models.ApiToken.DoesNotExist:
        return JsonResponse({'error': 'Invalid token.'}, status=401)

    try:
        data = json.loads(request.body)
        count_to_add = data.get('count')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

    if count_to_add is None or not isinstance(count_to_add, int) or count_to_add <= 0:
        return JsonResponse({'error': "0보다 큰 정수 형태의 'count' 값을 보내야 합니다."}, status=400)

    # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
    # '오늘'의 기준을 한국 시간으로 변경
    today = timezone.localdate()
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
    
    try:
        log_entry = models.TypingLog.objects.get(user=user, date=today)
        log_entry.count = F('count') + count_to_add
        log_entry.save(update_fields=['count'])
    except models.TypingLog.DoesNotExist:
        log_entry = models.TypingLog.objects.create(
            user=user,
            date=today,
            count=count_to_add
        )

    log_entry.refresh_from_db()

    return JsonResponse({"status": "success", "daily_total": log_entry.count}, status=200)


# --- 2. 사용자가 웹에서 볼 마이페이지 뷰 ---

# --- 대기 현황 API ---
@csrf_exempt
def update_machine_status_api(request):
    """오프라인 기계의 대기 인원을 에이전트(현장 PC)가 올리는 API.

    인증: Authorization: Token <키>. 그리고 그 토큰의 주인이 superuser 여야 한다.

    왜 토큰만으로는 부족한가 — 이 사이트의 API 토큰은 타건 기록을 올리려고
    사용자 누구나 발급받는다(현재 55명). 그 토큰으로 남의 오락실 대기열까지
    바꿀 수 있으면 안 된다.

    왜 is_staff 가 아니라 is_superuser 인가 — staff 는 서열표를 편집하는
    사람들이라 지금 세 명이다. 대기열은 서버를 직접 굴리는 사람의 몫이고
    그건 superuser 한 명이다. 아이디를 코드에 박지 않은 이유는, 계정 이름이
    바뀌거나 넘어갈 때 코드를 고쳐야 하는 상황을 만들지 않기 위해서다.

    예전에는 인증이 아예 없어서 주소만 알면 누구나 아무 숫자를 넣을 수 있었다.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method is required.'}, status=405)

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Token '):
        return JsonResponse(
            {'error': 'Authorization header is missing or invalid.'}, status=401)

    token_key = auth_header.split(' ', 1)[1].strip()
    try:
        api_token = models.ApiToken.objects.select_related('user').get(key=token_key)
    except models.ApiToken.DoesNotExist:
        return JsonResponse({'error': 'Invalid token.'}, status=401)

    user = api_token.user
    # 유효한 토큰이지만 권한이 없는 경우다. 401(누구인지 모르겠다)이 아니라
    # 403(누구인지는 알겠는데 안 된다)이 맞다.
    if not (user.is_active and user.is_superuser):
        return JsonResponse(
            {'error': 'This token is not allowed to update machine status.'},
            status=403)

    # 예전에는 이 아래가 통째로 bare except 로 감싸여 있었다. 그러면
    # KeyboardInterrupt 까지 삼키고, 무엇이 잘못됐는지도 알려 주지 못한다.
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({'error': 'Body must be a JSON object.'}, status=400)

    machine_id = data.get('machine_id')
    count = data.get('waiting_count')

    if not isinstance(machine_id, str) or not machine_id.strip():
        return JsonResponse(
            {'error': "'machine_id' must be a non-empty string."}, status=400)
    machine_id = machine_id.strip()
    # 모델의 max_length 와 맞춘다. 넘으면 DB 가 자르거나 터진다.
    if len(machine_id) > 50:
        return JsonResponse(
            {'error': "'machine_id' must be 50 characters or fewer."}, status=400)

    # isinstance(True, int) 가 True 라 bool 을 따로 걸러야 한다.
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return JsonResponse(
            {'error': "'waiting_count' must be a non-negative integer."}, status=400)

    models.MachineStatus.objects.update_or_create(
        machine_id=machine_id, defaults={'waiting_count': count})

    # 예전에는 조건이 안 맞으면 함수가 아무것도 반환하지 않고 끝나 500 이 났다.
    return JsonResponse({'status': 'success'}, status=200)

def get_machine_status_json(request, machine_id):
    try:
        status = models.MachineStatus.objects.get(machine_id=machine_id)
        
        # ▼ 마지막 업데이트 후 30초가 지났는지 체크 (Heartbeat 로직)
        # timezone.now()와 DB의 last_updated를 비교합니다.
        is_online = timezone.now() - status.last_updated < timedelta(seconds=30)

        return JsonResponse({
            'waiting_count': status.waiting_count,
            'is_online': is_online, # 온라인 여부 추가
            'last_updated': status.last_updated.strftime('%Y-%m-%d %H:%M:%S')
        })
    except models.MachineStatus.DoesNotExist:
        return JsonResponse({'waiting_count': 0, 'is_online': False})

# --- 페이지 렌더링 뷰 ---
def machine_status_view(request, machine_id="hwajeong_iidx_1"):
    return render(request, 'machine_status.html', {'machine_id': machine_id})