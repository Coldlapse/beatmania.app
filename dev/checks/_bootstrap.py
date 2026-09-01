# -*- coding: utf-8 -*-
"""검사 스크립트가 저장소 루트를 sys.path 에 올리고 dev 설정을 고른다.

스크립트를 dev/checks/ 안에서 돌리면 sys.path[0] 이 그 폴더라 저장소 루트의
settings 를 못 찾는다. 어느 위치에서 실행하든 같게 돌도록 여기서 맞춘다.

DJANGO_SETTINGS_MODULE 은 setdefault 다 — 이미 지정했으면 그것을 쓴다.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dev.settings_dev')

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
