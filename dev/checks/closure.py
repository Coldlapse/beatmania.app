# -*- coding: utf-8 -*-
"""직접 의존성에서 출발해 실제로 필요한 패키지의 폐포를 구한다.

pip freeze 는 환경에 남은 찌꺼기(예: 이미 걷어낸 django-hijack)까지 담는다.
여기서는 코드가 import 하는 것에서 시작해 requires 를 따라 내려간다.
"""
import sys
from importlib import metadata

sys.stdout.reconfigure(encoding='utf-8')

# 코드가 실제로 import 하는 것들 (AST 조사 결과) + 배포에만 쓰는 것
DIRECT = [
    'Django', 'PyMySQL', 'django-bootstrap5', 'django-hitcount',
    'django-recaptcha', 'beautifulsoup4', 'requests', 'thefuzz', 'playwright',
]

dists = {d.metadata['Name'].lower(): d for d in metadata.distributions()
         if d.metadata['Name']}

seen = {}
stack = list(DIRECT)
missing = []
while stack:
    name = stack.pop()
    key = name.lower()
    if key in seen:
        continue
    d = dists.get(key)
    if d is None:
        missing.append(name)
        continue
    seen[key] = d.version
    for req in (d.requires or []):
        # "extra" 로 걸린 선택 의존성은 뺀다. 우리는 기본 설치만 쓴다.
        if 'extra ==' in req:
            continue
        dep = req.split(';')[0].split('[')[0]
        for ch in ('=', '<', '>', '!', '~', '(', ' '):
            dep = dep.split(ch)[0]
        dep = dep.strip()
        if dep:
            stack.append(dep)

print('필요한 패키지 %d개' % len(seen))
print('')
direct_keys = {n.lower() for n in DIRECT}
for k in sorted(seen):
    print('%-24s %-14s %s' % (k, seen[k], '직접' if k in direct_keys else '전이'))

if missing:
    print('')
    print('환경에 없음: %s' % ', '.join(missing))

print('')
installed = set(dists) - set(seen)
print('설치돼 있지만 필요 없는 것 %d개:' % len(installed))
print('  ' + ', '.join(sorted(installed)))
