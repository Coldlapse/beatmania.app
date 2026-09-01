# -*- coding: utf-8 -*-
"""코드가 실제로 import 하는 서드파티 최상위 모듈을 모은다.

pip freeze 를 그대로 쓰지 않는 이유: conda 환경에는 이 프로젝트와 무관한
패키지가 섞여 있고, 반대로 어떤 것이 왜 필요한지도 남지 않는다.
"""
import ast
import io
import os
import sys
import sysconfig

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', 'static', 'media', 'locale'}

# 표준 라이브러리 판별
stdlib = set(getattr(sys, 'stdlib_module_names', ()))
if not stdlib:
    import distutils.sysconfig  # noqa
    stdlib = set()

local_tops = set()
files = []
for base, dirs, names in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for n in names:
        if n.endswith('.py'):
            files.append(os.path.join(base, n))

# 저장소 안에 있는 최상위 패키지/모듈 이름 = 우리 코드
for n in os.listdir(ROOT):
    p = os.path.join(ROOT, n)
    if os.path.isdir(p) and os.path.exists(os.path.join(p, '__init__.py')):
        local_tops.add(n)
    elif n.endswith('.py'):
        local_tops.add(n[:-3])

found = {}
for f in files:
    rel = os.path.relpath(f, ROOT)
    try:
        tree = ast.parse(io.open(f, encoding='utf-8').read(), f)
    except Exception as e:
        print('파싱 실패 %s: %s' % (rel, e))
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:          # 상대 import 는 우리 코드
                continue
            names = [node.module or '']
        else:
            continue
        for name in names:
            top = name.split('.')[0]
            if not top or top in stdlib or top in local_tops:
                continue
            found.setdefault(top, set()).add(rel)

print('서드파티 최상위 모듈 %d개' % len(found))
print('')
for top in sorted(found):
    where = sorted(found[top])
    print('%-22s %s%s' % (top, where[0],
                          ' 외 %d곳' % (len(where) - 1) if len(where) > 1 else ''))
