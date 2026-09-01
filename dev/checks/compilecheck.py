import os
import pathlib
import py_compile
import sys
import tempfile

root = pathlib.Path(sys.argv[1])
out = pathlib.Path(tempfile.mkdtemp()) / "x.pyc"
bad = []
ok = 0
for p in sorted(root.rglob("*.py")):
    rel = p.relative_to(root).as_posix()
    if "__pycache__" in rel or rel.startswith(".git/"):
        continue
    try:
        py_compile.compile(str(p), cfile=str(out), doraise=True)
        ok += 1
    except py_compile.PyCompileError as e:
        msg = str(e).strip().splitlines()[-1].strip()
        bad.append((rel, msg))

print("compile OK  : %d" % ok)
print("compile FAIL: %d" % len(bad))
for rel, msg in bad:
    print("  X %-48s %s" % (rel, msg))
