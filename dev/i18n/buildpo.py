# -*- coding: utf-8 -*-
"""새 번역을 기존 .po 에 합치고 .mo 를 다시 만든다.

이 PC 에 GNU gettext 가 없어서 msgfmt 를 쓸 수 없다. .mo 를 직접 쓴다.
형식은 GNU 문서의 것을 그대로 따른다 — 매직 0x950412de, 원문/번역 문자열
표를 오프셋으로 가리키는 단순한 구조다.

빈 msgid("") 헤더 항목을 반드시 넣는다. 없으면 gettext 가 카탈로그 인코딩을
알 수 없어 ascii 로 읽다가 UnicodeDecodeError 로 죽는다(전에 한 번 겪었다).
"""
import io
import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8')
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_HERE, 'trans'))

import newtrans
import newtrans_privacy
import newtrans_batch2
import newtrans_batch3
import newtrans_batch4
import newtrans_batch5
import newtrans_batch6
import newtrans_batch7
import newtrans_batch8
import newtrans_batch9
import newtrans_batch10
import newtrans_batch11
import newtrans_batch12
import newtrans_batch13
import newtrans_batch14
import newtrans_batch15
import newtrans_roadmap

LANGS = [('en', 0), ('ja', 1), ('zh_Hans', 2)]

NEW = {}
NEW.update(newtrans.TRANS)
NEW.update(newtrans_privacy.TRANS)
NEW.update(newtrans_roadmap.TRANS)
NEW.update(newtrans_batch2.TRANS)
NEW.update(newtrans_batch3.TRANS)
NEW.update(newtrans_batch4.TRANS)
NEW.update(newtrans_batch5.TRANS)
NEW.update(newtrans_batch6.TRANS)
NEW.update(newtrans_batch7.TRANS)
NEW.update(newtrans_batch8.TRANS)
NEW.update(newtrans_batch9.TRANS)
NEW.update(newtrans_batch10.TRANS)
NEW.update(newtrans_batch11.TRANS)
NEW.update(newtrans_batch12.TRANS)
NEW.update(newtrans_batch13.TRANS)
NEW.update(newtrans_batch14.TRANS)
NEW.update(newtrans_batch15.TRANS)


def read_po(path):
    """아주 단순한 .po 읽기. 우리가 쓰는 형식만 다룬다."""
    entries = {}
    msgid = msgstr = None
    mode = None
    for raw in io.open(path, encoding='utf-8'):
        line = raw.rstrip('\n')
        m = re.match(r'^msgid "(.*)"$', line)
        if m:
            if msgid is not None:
                entries[msgid] = msgstr or ''
            msgid, msgstr, mode = m.group(1), '', 'id'
            continue
        m = re.match(r'^msgstr "(.*)"$', line)
        if m:
            msgstr, mode = m.group(1), 'str'
            continue
        m = re.match(r'^"(.*)"$', line)
        if m and mode:
            if mode == 'id':
                msgid += m.group(1)
            else:
                msgstr += m.group(1)
            continue
    if msgid is not None:
        entries[msgid] = msgstr or ''
    return entries


def esc(s):
    return (s.replace('\\', '\\\\').replace('"', '\\"')
             .replace('\n', '\\n').replace('\t', '\\t'))


def unesc(s):
    return (s.replace('\\n', '\n').replace('\\t', '\t')
             .replace('\\"', '"').replace('\\\\', '\\'))


def write_po(path, entries):
    out = []
    out.append('msgid ""')
    out.append('msgstr ""')
    for part in entries[''].split('\\n'):
        if part:
            out.append('"%s\\n"' % part)
    out.append('')
    for k in sorted(entries):
        if k == '':
            continue
        out.append('msgid "%s"' % k)
        out.append('msgstr "%s"' % entries[k])
        out.append('')
    io.open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))


def write_mo(path, entries):
    items = sorted((unesc(k), unesc(v)) for k, v in entries.items() if v or k == '')
    keys = b'\x00'.join(k.encode('utf-8') for k, _ in items)
    vals = b'\x00'.join(v.encode('utf-8') for _, v in items)

    n = len(items)
    korig = 7 * 4
    ktrans = korig + n * 8
    kstart = ktrans + n * 8
    vstart = kstart + len(keys) + 1

    ktable, vtable = [], []
    off = kstart
    for k, _ in items:
        b = k.encode('utf-8')
        ktable.append((len(b), off))
        off += len(b) + 1
    off = vstart
    for _, v in items:
        b = v.encode('utf-8')
        vtable.append((len(b), off))
        off += len(b) + 1

    out = struct.pack('<Iiiiiii', 0x950412de, 0, n, korig, ktrans, 0, 0)
    for ln, o in ktable:
        out += struct.pack('<ii', ln, o)
    for ln, o in vtable:
        out += struct.pack('<ii', ln, o)
    out += keys + b'\x00' + vals + b'\x00'
    open(path, 'wb').write(out)


def build():
    """.po 를 병합하고 .mo 를 다시 쓴다. import 만으로는 돌지 않는다 —
    untranslated.py 가 read_po/unesc 를 쓰려고 이 모듈을 import 하는데,
    그때 카탈로그가 덮여 쓰이면 검사 스크립트가 파일을 바꾸는 셈이 된다."""
    added_total = 0
    for lang, idx in LANGS:
        po = os.path.join(ROOT, 'locale', lang, 'LC_MESSAGES', 'django.po')
        mo = os.path.join(ROOT, 'locale', lang, 'LC_MESSAGES', 'django.mo')
        entries = read_po(po)
        before = len(entries)

        for ko, trio in NEW.items():
            entries[esc(ko)] = esc(trio[idx])

        write_po(po, entries)
        write_mo(mo, entries)
        added = len(entries) - before
        added_total += added
        print('%-8s %d -> %d 항목 (+%d)' % (lang, before, len(entries), added))

    print('')
    print('새 번역 사전: %d개' % len(NEW))
    print('.mo 가 바뀌었으면 서버를 재시작해야 반영된다.')


if __name__ == '__main__':
    build()
