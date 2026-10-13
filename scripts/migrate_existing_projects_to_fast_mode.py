#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ migrate_existing_projects_to_fast_mode.py
سكربت ترحيل المشاريع القديمة على القرص لتفعيل الوضع السريع (fast_mode: True).

القواعد الآمنة:
1. المشاريع المربوطة بـ GitHub (github.enabled=True) لا تُمس أبداً لحماية مزامنة الـ Push.
2. يتم أخذ نسخة احتياطية manifest.json.bak_pre_fast_migration قبل أي تعديل.
3. الكتابة الذرية (Atomic Write) عبر ملف مؤقت .tmp لمنع أي تلف في حالة انقطاع الكهرباء.
"""

import json
import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PARENT_ROOT = PROJECT_ROOT.parent

REGISTRY_DIRS = [
    PROJECT_ROOT / "project_registry",
    PARENT_ROOT / "project_registry",
]

def migrate_registries():
    total_projects = 0
    migrated_count = 0
    already_fast_count = 0
    github_skipped_count = 0
    error_count = 0

    seen_dirs = set()

    for r_dir in REGISTRY_DIRS:
        if not r_dir.exists():
            continue
        real_path = str(r_dir.resolve())
        if real_path in seen_dirs:
            continue
        seen_dirs.add(real_path)

        print(f"\n🔍 فحص مجلد السجل: {r_dir}")
        for item in r_dir.glob("*"):
            if not item.is_dir():
                continue
            manifest = item / "manifest.json"
            if not manifest.exists():
                continue

            total_projects += 1
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                settings = data.get("project_settings")
                if not isinstance(settings, dict):
                    settings = {}
                    data["project_settings"] = settings

                gh = settings.get("github") or {}
                if bool(gh.get("enabled", False)):
                    github_skipped_count += 1
                    continue

                current_fast = settings.get("fast_mode")
                if current_fast is True:
                    already_fast_count += 1
                    continue

                # نسخ احتياطي
                bak_path = item / "manifest.json.bak_pre_fast_migration"
                if not bak_path.exists():
                    bak_path.write_bytes(manifest.read_bytes())

                # تعديل
                settings["fast_mode"] = True
                temp_file = item / "manifest.json.tmp"
                temp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                temp_file.replace(manifest)
                migrated_count += 1
                print(f"  ✅ تم تفعيل الوضع السريع: {item.name}")

            except Exception as e:
                error_count += 1
                print(f"  ❌ خطأ في فحص {item.name}: {e}")

    print("\n" + "=" * 60)
    print("📊 تقرير ترحيل المشاريع إلى الوضع السريع (Fast Mode):")
    print(f"  • إجمالي المشاريع المفحوصة: {total_projects}")
    print(f"  • المشاريع التي تم تفعيل الوضع السريع لها: {migrated_count} ✅")
    print(f"  • المشاريع التي كانت مفعلة أصلاً: {already_fast_count}")
    print(f"  • المشاريع المستثناة لأن GitHub مفعّل: {github_skipped_count} (تنزيل إلزامي للـ Push)")
    print(f"  • الأخطاء: {error_count}")
    print("=" * 60)

if __name__ == "__main__":
    migrate_registries()
