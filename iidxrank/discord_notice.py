# -*- coding: utf-8 -*-
"""메인 페이지 '공지사항' 칸 — 디스코드 공지 채널을 읽어 사이트에 보여 준다.

읽기 전용 봇(DISCORD_BOT_TOKEN)이 채널 메시지를 REST 로 가져온다. 게이트웨이
(상시 접속)는 쓰지 않는다 — 공지는 하루 몇 건이라 몇 분 늦게 보여도 되고, 상시
접속은 웹 워커와 생명주기가 맞지 않는다.

  DISCORD_NOTICE_CHANNELS = "탭 이름:채널ID,탭 이름:채널ID,..."  (맨 앞이 기본 탭)

메시지 본문은 사람이 쓴 디스코드 마크다운이다. 여기서 HTML 로 바꾸는데, 본문
글자는 **전부 이스케이프하고** 정해 둔 태그만 만든다. 링크는 http(s) 만 건다.
그래서 본문에 무엇이 들어 있어도 글자로 보일 뿐 태그가 되지 않는다.

캐시: 채널마다 5분. 디스코드가 실패하면 6시간 안의 마지막 성공분을 보여 주고,
실패 자체도 1분 기억해 매 요청마다 디스코드를 두드리지 않는다. 첨부 이미지 주소는
디스코드가 서명해 약 하루 뒤 만료되므로 오래된 사본을 더 길게 들고 있지 않는다.
"""
import datetime
import logging
import re

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateformat import format as dformat
from django.utils.html import escape

log = logging.getLogger(__name__)

API = 'https://discord.com/api/v10'
CDN = 'https://cdn.discordapp.com'
# 디스코드는 봇 요청의 User-Agent 를 이 모양으로 요구한다
USER_AGENT = 'DiscordBot (https://beatmania.app, 1)'
LIMIT = 30              # 채널마다 최근 몇 건을 보여 줄지
FRESH = 300             # 초. 이 시간 안에는 디스코드에 다시 묻지 않는다
STALE = 6 * 3600        # 실패했을 때 대신 보여 줄 마지막 성공분의 수명
FAIL = 60               # 실패를 기억하는 시간
GROUP_GAP = 7 * 60      # 같은 사람이 이 시간 안에 이어 쓰면 머리(아바타·이름)를 생략 — 디스코드와 같다
SHOWN_TYPES = (0, 19)   # 일반 메시지와 답장. 고정 알림(6) 같은 시스템 메시지는 뺀다


def channels():
    """[(탭 이름, 채널ID), ...]. 토큰이나 채널이 없으면 빈 목록 — 칸이 숨는다."""
    if not getattr(settings, 'DISCORD_BOT_TOKEN', ''):
        return []
    out = []
    for item in getattr(settings, 'DISCORD_NOTICE_CHANNELS', []):
        name, _, cid = item.rpartition(':')
        if name.strip() and cid.strip().isdigit():
            out.append((name.strip(), cid.strip()))
    return out


# ── 가져오기 ───────────────────────────────────────────────────────────────

def _fetch(cid):
    r = requests.get('%s/channels/%s/messages' % (API, cid), params={'limit': LIMIT},
                     headers={'Authorization': 'Bot ' + settings.DISCORD_BOT_TOKEN,
                              'User-Agent': USER_AGENT},
                     timeout=5)
    r.raise_for_status()
    return r.json()


def messages(cid):
    """채널의 최근 메시지를 화면에 쓸 모양으로. 가져오지 못하면 None."""
    key = 'dnotice:%s' % cid
    data = cache.get(key)
    if data is not None:
        return data
    if cache.get(key + ':fail'):
        return cache.get(key + ':stale')
    try:
        data = build(_fetch(cid))
    except Exception as e:     # 네트워크, 권한(403), 속도 제한(429), 모양이 바뀐 응답
        # 종류만 남긴다. 요청 내용(토큰 헤더)은 로그에 넣지 않는다
        log.warning('discord notice %s: %s', cid, type(e).__name__)
        cache.set(key + ':fail', 1, FAIL)
        return cache.get(key + ':stale')
    cache.set(key, data, FRESH)
    cache.set(key + ':stale', data, STALE)
    return data


# ── 화면에 쓸 모양 ─────────────────────────────────────────────────────────

def _when(iso):
    """디스코드의 ISO 시각 → 사이트 시간대(Asia/Seoul)."""
    return timezone.localtime(datetime.datetime.fromisoformat(iso))


def _avatar(author):
    uid, h = author.get('id') or '0', author.get('avatar')
    if h:
        # a_ 로 시작하면 움직이는 아바타지만 png 로 달라고 하면 첫 장면을 준다
        return '%s/avatars/%s/%s.png?size=80' % (CDN, uid, h)
    # 아바타가 없는 계정의 기본 그림. 새 사용자명 체계에서는 (id >> 22) % 6 이다
    return '%s/embed/avatars/%d.png' % (CDN, (int(uid) >> 22) % 6)


def _name_color(author):
    """디스코드 프로필의 이름 색(있을 때만). 서버 역할 색은 REST 로 오지 않는다."""
    try:
        return '#%06x' % int(author['display_name_styles']['colors'][0])
    except (KeyError, IndexError, TypeError, ValueError):
        return ''


IMG_BOX = (416, 320)     # 첨부 이미지를 이 상자 안에 비율대로 줄여 보여 준다


def _image(url, full, width, height, name=''):
    """보여 줄 크기를 여기서 정한다. 크기를 미리 알아야 이미지가 뜨기 전에도 자리가
    잡혀, 목록을 맨 아래(최신)로 내린 위치가 이미지가 뜨면서 밀리지 않는다."""
    w, h = width or 0, height or 0
    if w and h:
        scale = min(1.0, IMG_BOX[0] / w, IMG_BOX[1] / h)
        w, h = max(1, round(w * scale)), max(1, round(h * scale))
    return {'url': url, 'full': full or url, 'width': w, 'height': h, 'name': name}


def build(raw):
    """디스코드 응답(최신이 앞) → 오래된 것부터의 목록. 디스코드처럼 아래가 최신이다."""
    out = []
    prev = None
    for m in reversed(raw):
        if m.get('type') not in SHOWN_TYPES:
            continue
        author = m.get('author') or {}
        when = _when(m['timestamp'])
        new_day = prev is None or when.date() != prev['when'].date()
        grouped = (not new_day and m.get('type') != 19
                   and prev['author_id'] == author.get('id')
                   and (when - prev['when']).total_seconds() < GROUP_GAP)
        images, files = [], []
        for a in m.get('attachments') or []:
            ctype = (a.get('content_type') or '').split(';')[0]
            if ctype.startswith('image/') and a.get('proxy_url'):
                images.append(_image(a['proxy_url'], a.get('url'), a.get('width'), a.get('height'),
                                     a.get('filename', '')))
            elif a.get('url'):
                files.append({'url': a['url'], 'name': a.get('filename', ''), 'size': a.get('size') or 0})
        embeds = []
        for e in m.get('embeds') or []:
            thumb = e.get('thumbnail') or {}
            if e.get('type') == 'image' and thumb.get('proxy_url'):
                # 본문에 붙인 이미지 주소의 미리보기 — 이미지로 보여 준다
                images.append(_image(thumb['proxy_url'], e.get('url'), thumb.get('width'), thumb.get('height')))
            elif e.get('title') or e.get('description'):
                url = e.get('url') or ''
                embeds.append({
                    'title': e.get('title', ''),
                    'url': url if url.startswith(('http://', 'https://')) else '',
                    'html': render(e.get('description', ''), m),
                    'color': '#%06x' % e['color'] if isinstance(e.get('color'), int) else '',
                    'image': (e.get('image') or thumb).get('proxy_url') or '',
                })
        reply = None
        ref = m.get('referenced_message')
        if m.get('type') == 19 and ref:
            ra = ref.get('author') or {}
            reply = {'name': ra.get('global_name') or ra.get('username', ''),
                     'avatar': _avatar(ra),
                     'text': re.sub(r'\s+', ' ', ref.get('content', ''))[:100]}
        item = {
            'id': m['id'],
            'author_id': author.get('id'),
            'name': author.get('global_name') or author.get('username', ''),
            'name_color': _name_color(author),
            'bot': bool(author.get('bot')),
            'avatar': _avatar(author),
            'when': when,
            'edited': bool(m.get('edited_timestamp')),
            'grouped': grouped,
            'new_day': new_day,
            'html': render(m.get('content', ''), m),
            'images': images,
            'files': files,
            'embeds': embeds,
            'reply': reply,
        }
        out.append(item)
        prev = item
    return out


# ── 디스코드 마크다운 → 안전한 HTML ────────────────────────────────────────
#
# 순서가 중요하다.
#   1) 코드(``` 와 `)를 떼어 둔다 — 그 안에서는 아무 서식도 적용하지 않는다.
#   2) 멘션·이모지·시각·링크를 떼어 둔다. 떼어 둘 때 그 조각을 직접 이스케이프한다.
#      이스케이프 **전의** 글자에서 찾아야 주소 끝의 & 가 &amp; 로 바뀌어 잘리지 않고,
#      주소 안의 _ 나 * 가 서식으로 먹히지도 않는다.
#   3) 나머지를 전부 이스케이프한다. 이 뒤로는 '<' 가 본문에서 올 수 없다.
#   4) 서식(**, __, ~~ …)과 줄 단위 블록(제목, 인용, 목록)을 만들고 떼어 둔 것을 되돌린다.
#      서식은 한 줄 안에서만 짝을 찾는다 — 줄을 넘으면 블록 태그와 엇갈릴 수 있다.
#
# 떼어 둔 자리는 NUL 로 감싼 번호로 표시한다. 본문에 NUL 이 오면 처음에 지운다.

_NUL = chr(0)
_PH_RE = re.compile(_NUL + r'(\d+)' + _NUL)

_URL = r'https?://[^\s<>"' + _NUL + r']*[^\s<>"' + _NUL + r""".,:;!?)\]'*_~]"""
_INLINE = [
    (re.compile(r'\*\*(.+?)\*\*'), r'<strong>\1</strong>'),
    (re.compile(r'__(.+?)__'), r'<u>\1</u>'),
    (re.compile(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])'), r'<em>\1</em>'),
    (re.compile(r'(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])'), r'<em>\1</em>'),
    (re.compile(r'~~(.+?)~~'), r'<s>\1</s>'),
    (re.compile(r'\|\|(.+?)\|\|'), r'<span class="dn-spoiler" tabindex="0">\1</span>'),
]
_TS_FORMATS = {'t': 'H:i', 'T': 'H:i:s', 'd': 'Y-m-d', 'D': 'Y-m-d', 'f': 'Y-m-d H:i',
               'F': 'Y-m-d H:i', 'R': 'Y-m-d H:i'}


def render(text, msg=None):
    if not text:
        return ''
    # 본문에 NUL 이 섞여 오면 자리표시로 오인된다 — 먼저 지운다
    text = text.replace(_NUL, '')
    held = []

    def hold(html):
        held.append(html)
        return '%s%d%s' % (_NUL, len(held) - 1, _NUL)

    # 1) 코드
    text = re.sub(r'```(?:[\w+-]*\n)?(.*?)```',
                  lambda mo: hold('<pre class="dn-codeblock"><code>%s</code></pre>'
                                  % escape(mo.group(1).strip('\n'))), text, flags=re.S)
    text = re.sub(r'`([^`\n]+)`',
                  lambda mo: hold('<code class="dn-code">%s</code>' % escape(mo.group(1))), text)

    # 2) 멘션·이모지·시각·링크 (조각마다 직접 이스케이프)
    users = {u.get('id'): (u.get('global_name') or u.get('username', ''))
             for u in (msg or {}).get('mentions') or []}
    text = re.sub(r'<@!?(\d+)>', lambda mo: hold(
        '<span class="dn-mention">@%s</span>' % escape(users.get(mo.group(1)) or 'user')), text)
    text = re.sub(r'<@&(\d+)>', lambda mo: hold('<span class="dn-mention">@role</span>'), text)
    text = re.sub(r'<#(\d+)>', lambda mo: hold('<span class="dn-mention">#channel</span>'), text)
    text = re.sub(r'@(everyone|here)\b', lambda mo: hold(
        '<span class="dn-mention">@%s</span>' % mo.group(1)), text)
    text = re.sub(r'<(a?):(\w+):(\d+)>', lambda mo: hold(
        '<img class="dn-emoji" src="%s/emojis/%s.%s?size=48" alt=":%s:" title=":%s:" loading="lazy">'
        % (CDN, mo.group(3), 'gif' if mo.group(1) else 'webp', mo.group(2), mo.group(2))), text)

    def _ts(mo):
        try:
            dt = timezone.localtime(datetime.datetime.fromtimestamp(int(mo.group(1)), datetime.timezone.utc))
        except (OverflowError, OSError, ValueError):
            return hold(escape(mo.group(0)))
        return hold('<span class="dn-time">%s</span>'
                    % dformat(dt, _TS_FORMATS.get(mo.group(2) or 'f', 'Y-m-d H:i')))
    text = re.sub(r'<t:(-?\d{1,12})(?::([tTdDfFR]))?>', _ts, text)

    def _link(href, label):
        return hold('<a href="%s" target="_blank" rel="noopener nofollow ugc">%s</a>'
                    % (escape(href), escape(label)))
    # [글자](주소) 와 [글자](<주소>). 글자 쪽에는 서식을 적용하지 않는다
    text = re.sub(r'\[([^\[\]\n]+)\]\(<?(%s)>?\)' % _URL,
                  lambda mo: _link(mo.group(2), mo.group(1)), text)
    # <주소> 는 디스코드에서 미리보기를 끄는 표기. 링크로만 건다
    text = re.sub(r'<(https?://[^\s<>"' + _NUL + r']+)>',
                  lambda mo: _link(mo.group(1), mo.group(1)), text)
    text = re.sub(_URL, lambda mo: _link(mo.group(0), mo.group(0)), text)

    # 3) 나머지 이스케이프 (자리표시의 NUL 과 숫자는 건드리지 않는다)
    text = escape(text)

    # 4) 서식과 줄 단위 블록
    for pat, rep in _INLINE:
        text = pat.sub(rep, text)

    html, quote, items = [], [], []

    def flush():
        if quote:
            html.append('<blockquote class="dn-quote">%s</blockquote>' % '<br>'.join(quote))
            del quote[:]
        if items:
            html.append('<ul class="dn-list">%s</ul>' % ''.join('<li>%s</li>' % i for i in items))
            del items[:]

    for line in text.split('\n'):
        mo = re.match(r'&gt; ?(.*)$', line)          # "> " 는 이스케이프되어 "&gt; " 다
        if mo:
            if items:
                flush()
            quote.append(mo.group(1))
            continue
        mo = re.match(r'\s*[-*] +(.*)$', line)
        if mo:
            if quote:
                flush()
            items.append(mo.group(1))
            continue
        flush()
        mo = re.match(r'(#{1,3}) +(.+)$', line)
        if mo:
            html.append('<div class="dn-h%d">%s</div>' % (len(mo.group(1)), mo.group(2)))
            continue
        mo = re.match(r'-# +(.+)$', line)
        if mo:
            html.append('<div class="dn-sub">%s</div>' % mo.group(1))
            continue
        html.append(line + '<br>')
    flush()
    out = ''.join(html)
    out = re.sub(r'(<br>)+$', '', out)
    # 블록은 스스로 줄을 나누므로 바로 뒤의 줄바꿈 하나를 덜어 낸다
    out = re.sub(r'(</blockquote>|</ul>|</div>|</pre>)<br>', r'\1', out)

    # 되돌리기
    out = _PH_RE.sub(lambda mo: held[int(mo.group(1))], out)
    return out.replace(_NUL, '')
