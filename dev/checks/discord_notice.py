# -*- coding: utf-8 -*-
"""메인 페이지 공지사항 칸(iidxrank/discord_notice.py)을 확인한다.

디스코드에는 실제로 묻지 않는다 — _fetch 를 바꿔 끼운다.

  1. 마크다운 렌더러: 서식이 맞게 바뀌는지, 그리고 본문에 무엇이 있어도
     태그·속성이 새로 생기지 않는지(이스케이프). 링크는 http(s) 만.
  2. build: 시스템 메시지 제외, 오래된 것이 위, 같은 사람 묶기, 날짜 구분.
  3. 화면: 토큰이 없으면 칸이 숨고, 있으면 탭이 그려지고 /notice/<n>/ 가 채널을 그린다.
     디스코드가 실패하면 마지막 성공분, 그것도 없으면 안내 문구.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401
import django

django.setup()

from django.core.cache import cache  # noqa: E402
from django.test import Client, override_settings  # noqa: E402

from iidxrank import discord_notice as dn  # noqa: E402

fails = []


def check(name, cond, detail=''):
    print('%s %s%s' % ('OK  ' if cond else 'FAIL', name, (' — ' + detail) if (detail and not cond) else ''))
    if not cond:
        fails.append(name)


R = dn.render

# ── 1. 렌더러 ─────────────────────────────────────────────────────────────
check('굵게·기울임·밑줄·취소', R('**a** *b* __c__ ~~d~~') ==
      '<strong>a</strong> <em>b</em> <u>c</u> <s>d</s>', R('**a** *b* __c__ ~~d~~'))
check('snake_case 는 기울임이 아니다', '<em>' not in R('file_name_here'))
check('줄바꿈', R('a\nb') == 'a<br>b', R('a\nb'))
check('제목·작은 글씨', R('# T\nx\n-# s') == '<div class="dn-h1">T</div>x<br><div class="dn-sub">s</div>',
      R('# T\nx\n-# s'))
check('인용', R('> q1\n> q2\nafter') == '<blockquote class="dn-quote">q1<br>q2</blockquote>after',
      R('> q1\n> q2\nafter'))
check('목록', R('- a\n- b') == '<ul class="dn-list"><li>a</li><li>b</li></ul>', R('- a\n- b'))
check('인라인 코드 안은 서식 없음', R('`**x**`') == '<code class="dn-code">**x**</code>')
check('코드 블록', '<pre class="dn-codeblock"><code>a &lt;b&gt;</code></pre>' in R('```py\na <b>\n```'),
      R('```py\na <b>\n```'))
check('@everyone', R('@everyone hi') == '<span class="dn-mention">@everyone</span> hi')
check('사용자 멘션은 이름으로', '@Sadang' in R('<@325>', {'mentions': [{'id': '325', 'global_name': 'Sadang'}]}))
check('커스텀 이모지', 'cdn.discordapp.com/emojis/123.webp' in R('<:pog:123>'))
url = 'https://cdn.discordapp.com/a/b.png?ex=1&is=2&hm=3&'
out = R('see ' + url)
check('주소 끝의 & 까지 링크', 'href="https://cdn.discordapp.com/a/b.png?ex=1&amp;is=2&amp;hm=3&amp;"' in out, out)
check('주소 뒤 마침표는 링크 밖', R('https://a.com/x.').endswith('</a>.'), R('https://a.com/x.'))
check('주소 안의 _ 는 서식이 아니다', '<em>' not in R('https://a.com/a_b_c'))
check('가려진 링크', R('[문서](https://a.com/d)') ==
      '<a href="https://a.com/d" target="_blank" rel="noopener nofollow ugc">문서</a>', R('[문서](https://a.com/d)'))
check('스포일러', 'dn-spoiler' in R('||비밀||'))
check('타임스탬프', '<span class="dn-time">2026-09-21 23:13' in R('<t:1790000000:f>'), R('<t:1790000000:f>'))

# 주입: 결과에 이 렌더러가 만들지 않는 태그·속성이 없어야 한다
evil = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    '[x](javascript:alert(1))',
    '[x"onmouseover="alert(1)](https://a.com)',
    'https://a.com/"onmouseover="alert(1)',
    '<https://a.com/x" onclick="y>',
    '**<b>x</b>**',
    '<:x" onerror="alert(1):123>',
    '```</code></pre><script>x</script>```',
    '`<script>`',
    '> <iframe src=//evil>',
    '# <svg onload=alert(1)>',
    '\x00' + '0' + '\x00',
]
import re  # noqa: E402
ALLOWED_ATTRS = {'class', 'href', 'target', 'rel', 'src', 'alt', 'title', 'loading', 'tabindex'}
ALLOWED_TAGS = {'strong', 'em', 'u', 's', 'span', 'a', 'img', 'code', 'pre', 'br', 'div', 'blockquote', 'ul', 'li'}
for e in evil:
    out = R(e)
    # 이스케이프된 글자(&lt;…)는 태그가 아니다. 실제 태그만 뽑아 이름·속성을 본다
    problems = []
    for tag in re.findall(r'<[^>]*>', out):
        name = re.match(r'</?\s*([a-zA-Z0-9]+)', tag)
        if not name or name.group(1).lower() not in ALLOWED_TAGS:
            problems.append(tag)
            continue
        attrs = re.findall(r'\s([a-zA-Z-]+)="([^"]*)"', tag)
        if tag.count('"') % 2:
            problems.append(tag)
        for k, v in attrs:
            if k.lower() not in ALLOWED_ATTRS:
                problems.append(tag)
            if k.lower() in ('href', 'src') and not v.startswith('https://'):
                problems.append(tag)
    check('주입 막힘: %r' % e[:40], not problems, ' | '.join(problems) or out)

# ── 2. build ──────────────────────────────────────────────────────────────
def msg(i, ts, author='1', content='x', typ=0, **kw):
    d = {'id': str(i), 'type': typ, 'timestamp': ts, 'content': content,
         'author': {'id': author, 'username': 'u' + author, 'avatar': None}, 'attachments': [], 'embeds': []}
    d.update(kw)
    return d

raw = [  # 디스코드 응답은 최신이 앞
    msg(6, '2026-09-25T15:30:00+00:00', author='2'),
    msg(5, '2026-09-25T15:02:00+00:00', attachments=[{'content_type': 'image/png', 'proxy_url': 'https://media.discordapp.net/p.png',
                                                       'url': 'https://cdn.discordapp.com/p.png', 'width': 10, 'height': 20, 'filename': 'p.png'}]),
    msg(4, '2026-09-25T15:00:00+00:00'),
    msg(3, '2026-09-25T14:59:00+00:00', typ=6),
    msg(2, '2026-09-24T10:00:00+00:00', edited_timestamp='2026-09-24T11:00:00+00:00'),
    msg(1, '2026-09-24T09:58:00+00:00'),
]
b = dn.build(raw)
check('시스템 메시지(고정 알림) 제외', [m['id'] for m in b] == ['1', '2', '4', '5', '6'], str([m['id'] for m in b]))
check('7분 안 같은 사람은 묶음', [m['grouped'] for m in b] == [False, True, False, True, False],
      str([m['grouped'] for m in b]))
check('날짜가 바뀌면 구분선', [m['new_day'] for m in b] == [True, False, True, False, False],
      str([m['new_day'] for m in b]))
check('시각은 한국 시간', b[2]['when'].strftime('%Y-%m-%d %H:%M') == '2026-09-26 00:00', str(b[2]['when']))
check('수정됨 표시', b[1]['edited'] and not b[0]['edited'])
check('이미지 첨부', b[3]['images'] and b[3]['images'][0]['url'].startswith('https://media.discordapp.net/'))
check('아바타 없는 계정은 기본 그림', b[0]['avatar'].startswith('https://cdn.discordapp.com/embed/avatars/'))

# ── 3. 화면 ───────────────────────────────────────────────────────────────
CH = ['중요 공지:111', '일반 공지:222']
calls = []


def fake_ok(cid):
    calls.append(cid)
    return [msg(1, '2026-09-25T15:00:00+00:00', content='공지 **본문** <script>x</script>')]


def fake_fail(cid):
    calls.append(cid)
    raise RuntimeError('down')


c = Client()
real_fetch = dn._fetch
try:
    with override_settings(DISCORD_BOT_TOKEN='', DISCORD_NOTICE_CHANNELS=CH):
        r = c.get('/')
        check('토큰이 없으면 칸이 숨는다', r.status_code == 200 and b'bm-notice' not in r.content)
        check('토큰이 없으면 /notice/0/ 은 404', c.get('/notice/0/').status_code == 404)

    with override_settings(DISCORD_BOT_TOKEN='test', DISCORD_NOTICE_CHANNELS=CH):
        cache.clear()
        dn._fetch = fake_ok
        r = c.get('/')
        html = r.content.decode()
        check('탭이 그려진다', html.count('class="dn-chan') == 2 and '중요 공지' in html)
        check('메인 페이지는 디스코드에 묻지 않는다', calls == [], str(calls))
        r = c.get('/notice/1/')
        body = r.content.decode()
        check('채널 내용', r.status_code == 200 and '<strong>본문</strong>' in body, body[:300])
        check('본문의 태그는 글자로', '<script>x' not in body and '&lt;script&gt;x' in body)
        c.get('/notice/1/')
        check('두 번째는 캐시', calls == ['222'], str(calls))
        check('없는 탭은 404', c.get('/notice/5/').status_code == 404)

        # 실패: 신선 캐시가 지난 뒤 디스코드가 죽으면 마지막 성공분
        cache.delete('dnotice:222')
        dn._fetch = fake_fail
        body = c.get('/notice/1/').content.decode()
        check('실패하면 마지막 성공분', '<strong>본문</strong>' in body)
        n = len(calls)
        c.get('/notice/1/')
        check('실패는 1분 기억(다시 두드리지 않음)', len(calls) == n, str(calls))
        # 성공분도 없으면 안내
        body = c.get('/notice/0/').content.decode()
        check('성공분도 없으면 안내', 'dn-empty' in body and 'bi-cloud-slash' in body, body[:300])

        # 영어 화면에서 탭 이름·문구 번역
        ce = Client(HTTP_ACCEPT_LANGUAGE='en')
        html = ce.get('/').content.decode()
        check('탭 이름 번역(en)', 'Important' in html and '중요 공지' not in html)
        check('칸 제목 번역(en)', 'Announcements' in html)
finally:
    dn._fetch = real_fetch
    cache.clear()

print()
print('총 실패: %d' % len(fails))
sys.exit(1 if fails else 0)
