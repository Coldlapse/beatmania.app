# -*- coding: utf-8 -*-
"""번역이 빠진 원문을 찾는다.

blocktrans 의 msgid 는 템플릿에 쓴 {{ var }} 가 아니라 %(var)s 형태다.
앞서 이걸 빠뜨려서 68개를 헛되이 넣은 적이 있으므로 여기서 변환한다.
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'i18n'))
import buildpo

po = buildpo.read_po(os.path.join(ROOT, 'locale', 'en', 'LC_MESSAGES', 'django.po'))
have = {buildpo.unesc(k) for k, v in po.items() if v}

pat_trans = re.compile(r"{%\s*trans(?:late)?\s+(['\"])(.*?)\1")
pat_block = re.compile(r'{%\s*blocktrans(?:late)?[^%]*%}(.*?){%\s*endblocktrans',
                       re.S)
# 파이썬 쪽: _( 로 시작해 ) 로 닫히는 인접 문자열 묶음
pat_py = re.compile(r"_\(\s*((?:(?:'[^']*'|\"[^\"]*\")\s*)+)\)", re.S)
pat_str = re.compile(r"'([^']*)'|\"([^\"]*)\"")
hangul = re.compile(r'[\uac00-\ud7a3]')


def to_msgid(body):
    return re.sub(r'{{\s*([a-zA-Z_0-9]+)\s*}}', r'%(\1)s', body).strip()


missing = {}
for base, dirs, files in os.walk(ROOT):
    if any(x in base for x in ('locale', '.git', 'node_modules')):
        continue
    for fn in files:
        if not fn.endswith(('.html', '.py')):
            continue
        p = os.path.join(base, fn)
        try:
            s = io.open(p, encoding='utf-8').read()
        except Exception:
            continue
        found = [m.group(2) for m in pat_trans.finditer(s)]
        found += [to_msgid(m.group(1)) for m in pat_block.finditer(s)]
        for m in pat_py.finditer(s):
            found.append(''.join(a or b for a, b in pat_str.findall(m.group(1))))
        for t in found:
            if not hangul.search(t) or t in have:
                continue
            missing.setdefault(t, os.path.relpath(p, ROOT))

print('번역이 빠진 원문: %d개' % len(missing))
print('')
for t in sorted(missing, key=lambda x: (missing[x], x)):
    print('[%s]' % missing[t])
    print('  %r' % t)
