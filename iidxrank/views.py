#-*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.exceptions import MultipleObjectsReturned
from django.urls import reverse
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_exempt
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from iidxrank import accounts
from iidxrank import models
from iidxrank import forms
import settings
from iidxrank import rankpage as rp
from iidxrank import iidx
from iidxrank import views_json
from iidxrank import views_notice
import json
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
        'notice_tabs': views_notice.tabs(),
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
        # 공유 상자에 '비공개라 남에게 열리지 않는다' 를 적을지
        pdata['share_private'] = bool(player and player.private)
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
        pr_obj = None
        # 없는 곡이면 제목을 읽기 전에 걸러야 한다(전에는 None.songtitle 로 500 이 났다)
        title = song_obj.songtitle if song_obj else ''
        if (song_obj == None):
            valid = False
        else:
            valid = True
            # fetch playrecord if available
            # Player 의 id 는 User 의 id 와 다르다. 전에는 player_id=user.id 로 찾아
            # 남의 기록(또는 없음)을 읽었다 — 저장은 맞게 되고 팝업 표시만 틀렸다.
            player = rp.get_player_from_request(request)
            pr_obj = models.PlayRecord.objects.filter(player=player, song_id=id).first()
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



"""
user related part
"""

# /!/login/
login_django = login
def login(request):
    if (request.user.is_authenticated):
        return redirect('home')
    if (request.method == "POST"):
        form = forms.LoginForm(request.POST, request=request)
        if (form.is_valid()):
            login_django(request, form.user_cache)
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
            # 검증을 거친 값(cleaned_data)을 저장한다. 전에는 날것 form.data 를 저장해 앞뒤 공백이
            # 붙은 아이디·이메일이 생겼다(라이브에 아이디 2·이메일 1). 이메일은 clean_email 이
            # 소문자·공백 정리를 한 값이라 중복 검사(iexact)·아이디 찾기와도 어긋나지 않는다.
            cd = form.cleaned_data
            user = User.objects.create_user(
                    username=cd['id'],
                    first_name=cd['id'],
                    email=cd['email'],
                    password=cd['password'])
            # automatically create player object
            #rp.get_player_from_user(user)
            rp.newplayer(user)
            # 가입 폼이 이메일 인증과 새 비밀번호 규칙을 이미 요구한다. 그 사실을
            # 남기지 않으면 미들웨어가 새 가입자를 '기존 사용자'로 보고 1회 인증
            # 화면으로 보내, 가입 직후 인증 메일이 한 번 더 나간다.
            # (2026-09-02 ~ 09-26 가입자 8명 전원이 그렇게 두 번 인증했다.)
            sec = accounts.security_of(user)
            sec.newrulepassed = True
            sec.email_verified_at = timezone.now()
            sec.save()
            accounts.clear_verification(request, 'signup')
            user = authenticate(username=cd['id'], password=cd['password'])
            login_django(request, user)
            return redirect('home')
    else:
        form = forms.JoinForm(request)
    return render(request, 'user/join.html', {'form': form})

# /!/logout/
# POST 로만 로그아웃한다. GET 으로 되던 때는 남의 페이지에 <img src="/logout/"> 한 줄로 방문자를
# 로그아웃시킬 수 있었다. GET 으로 오면(옛 북마크·옛 주소 /!/logout/) 아무것도 하지 않고 홈으로.
logout_django = logout
def logout(request):
    if request.method == 'POST':
        logout_django(request)
    return redirect('home')

# /!/withdraw/
def withdraw(request):
    if (not request.user.is_authenticated):
        return redirect('login')
    # 운영자 계정은 지우지 않는다. 전에는 raise Exception 이라 500 으로 오류 로그에 남았다
    if (request.user.is_superuser):
        raise PermissionDenied
    if (request.method == "POST"):
        form = forms.WithdrawForm(request.user, request.POST)
        if (form.is_valid()):
            user = request.user
            user.delete()
            logout_django(request)
            return redirect('home')
    else:
        form = forms.WithdrawForm(request.user)
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

# JSON
# /modify/ — 서열표 편집 팝업이 기록을 바꾸는 입구.
#
# POST 만 받는다. 전에는 GET 도 받아서, 외부 페이지가 방문자를 이 주소로 보내기만 하면
# (SameSite=Lax 쿠키는 최상위 GET 이동에 실려 간다) 그 사람 계정의 값을 바꿀 수 있었다.
# POST 는 Django CSRF 검사를 거친다(이 뷰는 csrf_exempt 가 아니다).
#
# 동작은 둘뿐이다: edit(램프·DJ RANK), exscore. 예전의 djname·iidxid·spclass·dpclass·delete 는
# 사이트 어디에서도 부르지 않는 채로 계정 설정 폼(AccountForm)의 검증을 건너뛰는 뒷문이어서 지웠다.
# 이름·ID·단위는 /account/ 에서만 바꾼다.
MODIFY_MAX_ITEMS = 1000


@require_POST
def modify(request):
    if (not request.user.is_authenticated):
        return JsonResponse({'code': 1, 'message': 'please log in'})
    # Player 행이 없는 계정(/admin/ 에서 만든 계정 등)도 여기서 만든다 — 없으면 PlayRecord 의
    # player(NOT NULL)에 None 이 들어가 500 이었다. account 뷰와 같은 처리.
    player = rp.newplayer(request.user)
    action = request.POST.get('action', '')
    v = request.POST.get('v', '')
    if (action == 'edit'):
        # v = [{"id": 곡 pk, "clear": 0~7} 또는 {"id": 곡 pk, "rank": 0~8}, ...]
        # 전에는 clear 없이 rank 만 오면 desc 가 정의되지 않은 채 쓰이거나, 실패 응답에서
        # 없는 변수 e 를 읽어 500 이 났다.
        # 항목 수 상한: 팝업은 1개씩 보내고, 옛 오프라인 편집 저장분 복원(common.js)이 한 표의 곡
        # 수(최대 약 700)만큼 보낸다. 상한이 없으면 요청 하나로 수십만 항목 × 쿼리를 일으킬 수 있었다.
        try:
            lst = json.loads(v)
            if not isinstance(lst, list) or len(lst) > MODIFY_MAX_ITEMS:
                raise ValueError
            items = []
            for l in lst:
                desc = {}
                if 'clear' in l:
                    desc['clear'] = int(l['clear'])
                    if not 0 <= desc['clear'] <= 7:
                        raise ValueError
                if 'rank' in l:
                    desc['rank'] = int(l['rank'])
                    if not 0 <= desc['rank'] <= 8:
                        raise ValueError
                if not desc:
                    raise ValueError
                items.append((int(l['id']), desc))
        except (ValueError, TypeError, KeyError):
            return JsonResponse({'code': 1, 'message': _('잘못된 요청입니다.')})
        for sid, desc in items:
            log = []
            try:
                ok = rp.update_record(sid, player, desc, log)
            except models.Song.DoesNotExist:
                return JsonResponse({'code': 1, 'message': _('잘못된 요청입니다.')})
            if not ok:
                return JsonResponse({'code': 1, 'message': log[0] if log else _('잘못된 요청입니다.')})
    elif (action == 'exscore'):
        # v = {"id": 곡 pk, "exscore": 숫자 또는 null(지우기)}
        # 손으로 넣은 값은 그대로 쓴다(낮춰도 된다) — 잘못 넣은 것을 고칠 길이어야 한다.
        try:
            d = json.loads(v)
            song = models.Song.objects.get(id=int(d['id']))
            ex = d.get('exscore')
            ex = None if ex in (None, '') else int(ex)
        except (ValueError, TypeError, KeyError, models.Song.DoesNotExist):
            return JsonResponse({'code': 1, 'message': _('잘못된 요청입니다.')})
        # 노트 수를 알면 만점(노트×2)까지, 모르면 넉넉한 상한. 곡 DB 의 노트 수는 아직
        # 대부분 비어 있다(2026-09-26 라이브 SP/DP 4,410채보 모두 0).
        limit = song.songnotes * 2 if song.songnotes else 9999
        if ex is not None and not (0 <= ex <= limit):
            return JsonResponse({'code': 1, 'message': _('EX SCORE 는 0 에서 %(n)d 사이여야 합니다.') % {'n': limit}})
        pr = models.PlayRecord.objects.filter(song=song, player=player).first()
        if pr is None:
            if ex is None:
                return JsonResponse({'code': 0, 'message': _('저장했습니다.'), 'exscore': None})
            pr = models.PlayRecord(song=song, player=player)
        lowered = pr.exscore is not None and (ex is None or ex < pr.exscore)
        pr.exscore = ex
        pr.save()
        if lowered:
            # 합산 BPI 는 최고값을 붙잡아 둔다(bpi.BpiBest). 잘못 넣은 높은 값을 고쳤는데 그 값이
            # 계속 남으면 안 되므로 최고값을 지우고 지금 기록으로 다시 잰다.
            from iidxrank import bpi
            bpi.forget_best(player)
        return JsonResponse({'code': 0, 'message': _('저장했습니다.'), 'exscore': ex})
    else:
        return JsonResponse({'code': 1, 'message': 'invalid action'})
    return JsonResponse({'code': 0, 'message': 'Done'})
"""
user end
"""

# --- 1. Electron 앱과 통신할 API 뷰 ---
# 상한은 사람이 칠 수 있는 한계로 잡았다(2026-09-26 사용자 결정). 라이브 실측은 7명, 하루 합계
# 최대 223,789 · 99번째 백분위 182,142. 상한이 없으면 토큰 하나(누구나 발급)로 한 번에 리더보드 1위가
# 되고, 2^31 을 넘기면 IntegerField 가 넘친다.
TYPING_MAX_PER_REQUEST = 600000
TYPING_MAX_PER_DAY = 2000000


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
    if not user.is_active:
        return JsonResponse({'error': 'Invalid token.'}, status=401)

    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):     # JSONDecodeError 는 ValueError 의 하위
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    # 본문이 객체가 아니면(배열·숫자) data.get 에서 500 이었다. true 는 int 로 통과했었다
    count_to_add = data.get('count') if isinstance(data, dict) else None
    if (isinstance(count_to_add, bool) or not isinstance(count_to_add, int)
            or not 0 < count_to_add <= TYPING_MAX_PER_REQUEST):
        return JsonResponse({'error': "1 이상 %d 이하의 정수 'count' 값을 보내야 합니다."
                             % TYPING_MAX_PER_REQUEST}, status=400)

    # '오늘'의 기준은 한국 시간
    today = timezone.localdate()

    # 행을 잠그고 더한다. 전에는 get → create 사이가 벌어져, 같은 날 첫 요청 둘이 겹치면
    # unique_together(user, date)에 걸려 500 이었다. get_or_create 는 그 경합을 스스로 처리한다.
    with transaction.atomic():
        log_entry, _created = (models.TypingLog.objects.select_for_update()
                               .get_or_create(user=user, date=today, defaults={'count': 0}))
        if log_entry.count + count_to_add > TYPING_MAX_PER_DAY:
            return JsonResponse({'error': '하루 합계 상한(%d)을 넘습니다.' % TYPING_MAX_PER_DAY,
                                 'daily_total': log_entry.count}, status=400)
        log_entry.count = F('count') + count_to_add
        log_entry.save(update_fields=['count'])

    log_entry.refresh_from_db()

    return JsonResponse({"status": "success", "daily_total": log_entry.count}, status=200)


# --- 2. 사용자가 웹에서 볼 마이페이지 뷰 ---

# --- 대기 현황 API ---
MACHINE_STATUS_GROUP = 'machine-status'


@csrf_exempt
def update_machine_status_api(request):
    """오프라인 기계의 대기 인원을 에이전트(현장 PC)가 올리는 API.

    인증: Authorization: Token <키>. 그리고 그 토큰의 주인이 기기 전용 그룹(machine-status)에 있어야 한다.
    (2026-09-26 전에는 superuser 였다 — 아래 '왜 is_superuser' 문단은 그때의 판단이고, 지금은 전용 계정으로 좁혔다.)

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
    #
    # 기기 전용 계정(그룹 MACHINE_STATUS_GROUP)의 토큰만 받는다(2026-09-26). 전에는 superuser 토큰이었는데,
    # 현장 PC 가 털리면 그 토큰으로 superuser 의 기록 동기화 API 까지 쓸 수 있었다. 전용 계정의 토큰은
    # 털려도 대기 인원 보고만 할 수 있다(그 계정에는 기록도 권한도 없다).
    # superuser 는 더 받지 않는다 — 전환 기간 없이 바로 끊었다(사용자 결정, 현장 PC 토큰 교체는 급하지 않음).
    allowed = user.groups.filter(name=MACHINE_STATUS_GROUP).exists()
    if not (user.is_active and allowed):
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