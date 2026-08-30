#!/usr/bin/env python3
"""
bridge_refactor.main
====================
نقطة تشغيل البوت:
    python -m bridge_refactor.main
أو  python bridge_refactor/main.py
"""
import pathlib
import sys

# دعم التشغيل المباشر كملف (بدون -m)
if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.resolve()))
    from bridge_refactor import runtime
else:
    from . import runtime


if __name__ == "__main__":
    runtime.main()
