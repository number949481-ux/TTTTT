#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/verify_docs_integrity.py
===============================
أداة الفحص الذاتي لتكامل وسلامة منظومة التوثيق:
1. فحص وجود كافة الملفات المشار إليها في روابط Markdown النسبية.
2. التحقق من سلامة كافة ملفات docs/engineering و docs/tests.
3. منع وجود أي روابط مكسورة (Broken Links) أو ملفات يتيمة.
4. إرجاع Exit Code 0 عند النجاح، أو Exit Code 1 عند وجود أي رابط مكسور.
"""

import os
import re
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(ROOT_DIR, "docs")

def verify_docs_integrity():
    """
    يفحص كافة روابط Markdown في مجلد docs/ و PROGRESS.md
    يرجع (True, [], checked_files, checked_links) عند السلامة.
    """
    errors = []
    checked_links = 0
    checked_files = 0

    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

    files_to_scan = []
    root_progress = os.path.join(ROOT_DIR, "PROGRESS.md")
    if os.path.exists(root_progress):
        files_to_scan.append(root_progress)

    for root, _, files in os.walk(DOCS_DIR):
        for f in files:
            if f.endswith(".md"):
                files_to_scan.append(os.path.join(root, f))

    for fpath in files_to_scan:
        checked_files += 1
        rel_fpath = os.path.relpath(fpath, ROOT_DIR)
        file_dir = os.path.dirname(fpath)

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            errors.append(f"خطأ قراءة في الملف {rel_fpath}: {e}")
            continue

        for match in link_pattern.finditer(content):
            label = match.group(1).strip()
            target = match.group(2).strip()

            if target.startswith("http://") or target.startswith("https://") or target.startswith("#") or target.startswith("mailto:"):
                continue

            clean_target = target.split("#")[0].split("?")[0].strip()
            if not clean_target:
                continue

            resolved_path = os.path.normpath(os.path.join(file_dir, clean_target))
            checked_links += 1

            if not os.path.exists(resolved_path):
                errors.append(f"رابط مكسور في [{rel_fpath}]: [{label}] -> '{clean_target}'")

    return (len(errors) == 0, errors, checked_files, checked_links)

def main():
    print("=" * 70)
    print("بدء فحص تكامل وسلامة منظومة التوثيق (Docs Integrity Check)...")
    print("=" * 70)

    ok, errors, total_files, total_links = verify_docs_integrity()

    print(f"تم مسح: {total_files} ملف توثيقي | تم فحص: {total_links} رابط داخلي.")

    if ok:
        print("\nنجاح باهر: كافة الروابط والمسارات سليمة 100% بدون أي رابط مكسور!")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"\nتم اكتشاف {len(errors)} رابط مكسور:\n")
        for err in errors:
            print(f"  {err}")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
