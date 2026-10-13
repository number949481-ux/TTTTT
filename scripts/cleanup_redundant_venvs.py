#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 cleanup_redundant_venvs.py
سكربت التنظيف الآمن لبيئات .venv المكررة في مجلدات الساندبوكس والـ Checkpoints.

القواعد الفولاذية:
1. الحذف محصور حصراً بمجلدات .venv داخل extracted_webapp و checkpoints/hot.
2. لا يتم لمس أي كود مصدري للمشاريع (HTML, CSS, JS, Python خارج .venv).
3. معالجة ملفات Read-Only في ويندوز لمنع توقف الحذف.
"""

import os
import pathlib
import shutil
import stat
import time

def handle_remove_readonly(func, path, exc):
    """معالجة ملفات القراءة فقط على ويندوز أثناء الحذف"""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

def get_dir_size_bytes(path):
    total = 0
    try:
        for root, dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
    except Exception:
        pass
    return total

def run_cleanup():
    base_dirs = [
        pathlib.Path(r"D:\SMS\.hRhRhRhRhRhR\..............................................................................................................شغل فريق\Genspark\W___webapp"),
    ]

    target_venvs = []
    print("🔍 جاري حصر مجلدات .venv المستهدفة...", flush=True)

    for b_dir in base_dirs:
        if not b_dir.exists():
            continue

        # 1) extracted_webapp/*/webapp/.venv or extracted_webapp/*/.venv
        ext_dirs = [
            b_dir / "extracted_webapp",
            b_dir / "bridge_refactor_31" / "extracted_webapp",
        ]
        for ed in ext_dirs:
            if ed.exists():
                for item in ed.glob("*"):
                    if item.is_dir():
                        v1 = item / "webapp" / ".venv"
                        v2 = item / ".venv"
                        if v1.exists() and v1.is_dir():
                            target_venvs.append(v1)
                        if v2.exists() and v2.is_dir() and v2 not in target_venvs:
                            target_venvs.append(v2)

        # 2) project_registry/*/checkpoints/hot/*/.venv
        reg_dir = b_dir / "project_registry"
        if reg_dir.exists():
            for p_item in reg_dir.glob("*"):
                if p_item.is_dir():
                    hot_dir = p_item / "checkpoints" / "hot"
                    if hot_dir.exists():
                        for cp in hot_dir.glob("*"):
                            if cp.is_dir():
                                v1 = cp / ".venv"
                                v2 = cp / "webapp" / ".venv"
                                if v1.exists() and v1.is_dir() and v1 not in target_venvs:
                                    target_venvs.append(v1)
                                if v2.exists() and v2.is_dir() and v2 not in target_venvs:
                                    target_venvs.append(v2)

    print(f"📌 تم العثور على {len(target_venvs)} بيئة .venv لحذفها بأمان.", flush=True)

    deleted_count = 0
    total_freed_bytes = 0

    for idx, v_path in enumerate(target_venvs, 1):
        try:
            sz = get_dir_size_bytes(v_path)
            shutil.rmtree(v_path, onerror=handle_remove_readonly)
            total_freed_bytes += sz
            deleted_count += 1
            sz_mb = sz / (1024 * 1024)
            # تقصير المسار للعرض النظيف
            short_path = str(v_path).replace(r"D:\SMS\.hRhRhRhRhRhR\..............................................................................................................شغل فريق\Genspark\W___webapp", "W___webapp")
            print(f"  [{idx:02d}/{len(target_venvs):02d}] 🗑️ تم حذف: {short_path} ({sz_mb:.1f} MB)", flush=True)
        except Exception as e:
            print(f"  ❌ خطأ في حذف {v_path}: {e}", flush=True)

    freed_gb = total_freed_bytes / (1024 ** 3)
    freed_mb = total_freed_bytes / (1024 ** 2)

    print("\n" + "=" * 65, flush=True)
    print("🎉 اكتمل التنظيف بنجاح تام!", flush=True)
    print(f"  • عدد المجلدات المحذوفة: {deleted_count} من أصل {len(target_venvs)}")
    print(f"  • إجمالي المساحة المحررة: {freed_gb:.2f} GB ({freed_mb:.1f} MB)")
    print("=" * 65, flush=True)

if __name__ == "__main__":
    run_cleanup()
