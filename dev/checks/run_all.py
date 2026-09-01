# -*- coding: utf-8 -*-
"""회귀 검사 네 개를 순서대로 돌리고 기대값과 맞는지 본다.

각 스크립트는 따로도 돌아간다. 여기서는 마지막 줄의 숫자만 읽어 요약한다.
compilecheck 는 .py 파일 수가 늘면 OK 숫자도 늘기 때문에 FAIL 만 본다.

    python dev/checks/run_all.py

dev MySQL(dev/docker-compose.yml)이 떠 있어야 livecheck 와 test_urls 가 돈다.
"""
import os
import re
import subprocess
import sys

import _bootstrap  # noqa: F401  (sys.path / 설정 모듈)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = _bootstrap.ROOT

# (파일, 인자, 결과를 읽을 정규식, 기대값)
JOBS = [
    ('compilecheck.py', [ROOT], r'compile FAIL:\s*(\d+)', 0),
    ('livecheck.py',    [],     r'실패 (\d+) / 총', 0),
    ('test_urls.py',    [],     r'총 실패:\s*(\d+)', 0),
    ('untranslated.py', [],     r'번역이 빠진 원문:\s*(\d+)개', 0),
]

failed = []
for script, args, pat, want in JOBS:
    p = subprocess.run([sys.executable, os.path.join(HERE, script)] + args,
                       cwd=ROOT, capture_output=True)
    out = p.stdout.decode('utf-8', 'replace')
    m = re.search(pat, out)
    if p.returncode != 0 or not m:
        print('%-18s 실행 실패 (returncode=%s)' % (script, p.returncode))
        print(p.stderr.decode('utf-8', 'replace').strip()[-800:])
        failed.append(script)
        continue
    got = int(m.group(1))
    ok = got == want
    failed += [] if ok else [script]
    print('%-18s %s (기대 %d, 실제 %d)'
          % (script, 'OK' if ok else 'FAIL', want, got))

print('')
if failed:
    print('실패한 검사: %s' % ', '.join(failed))
    sys.exit(1)
print('전부 통과')
