#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
🏁 test_acceptance.py — خطة الاعتماد الأربع مراحل لمحرك gh_bulk (v5.4)
=============================================================================
المرحلة 1: dry_run وفحص الإحصائيات الدقيقة
المرحلة 2: push على ريبو فارغ (Bootstrap بملف حقيقي)
المرحلة 3: مزامنة بعد تعديل (up_to_date وصفر Blobs عند التطابق)
المرحلة 4: الفشل والتعافي الصامد (Idempotent Recovery)
"""

import os
import sys
import tempfile
import pathlib
from unittest.mock import MagicMock

# إضافة المسار الحالي
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import gh_bulk
from gh_bulk import GhClient, sync


def run_acceptance_tests():
    print("\n" + "=" * 60)
    print("🚀 بدء خطة الاعتماد الأربع مراحل — محرك gh_bulk v5.4")
    print("=" * 60 + "\n")

    # -------------------------------------------------------------
    # ── المرحلة 1: dry_run ──
    # -------------------------------------------------------------
    print("── المرحلة 1: dry_run ──")
    client1 = GhClient("org", "repo1", "mock_token")
    client1.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    client1.list_branches = MagicMock(return_value=["main"])
    client1.get_ref = MagicMock(return_value={"object": {"sha": "sha_base"}})
    client1.get_commit = MagicMock(return_value={"tree": {"sha": "tree_base"}})
    client1.get_tree = MagicMock(return_value={"tree": []})

    # تجهيز 15 ملف نصي (واحد منهم سيصبح bootstrap لو كان فارغاً) + 4 ملفات بلوب
    upload_files = []
    for i in range(15):
        name = "index.html" if i == 0 else f"src/file_{i}.js"
        upload_files.append({
            "path": name,
            "content_bytes": f"console.log('file {i}');".encode("utf-8"),
            "bytes": 20,
        })
    for j in range(4):
        upload_files.append({
            "path": f"assets/image_{j}.png",
            "content_bytes": b"\x00\xff" * 3000,  # binary 6000 bytes > 4096
            "bytes": 6000,
        })

    payload1 = {
        "repository": "org/repo1",
        "branch": "main",
        "upload_files": upload_files,
        "delete_files": [],
    }

    res1 = sync(client1, branch="main", dry_run=True, payload=payload1)
    assert res1["status"] == "dry_run"
    assert res1["scanned"] == 19
    assert res1["would_send_inline"] == 15  # 15 ملف نصي <= 4KB
    assert res1["would_upload_blobs"] == 4  # 4 ملفات ثنائية كبيرة
    print(f"  ✅ inline == {res1['would_send_inline']} · blobs == {res1['would_upload_blobs']} · scanned == {res1['scanned']}")

    # -------------------------------------------------------------
    # ── المرحلة 2: push على ريبو فارغ ──
    # -------------------------------------------------------------
    print("── المرحلة 2: push على ريبو فارغ ──")
    client2 = GhClient("org", "empty-repo", "mock_token")
    client2.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    client2.list_branches = MagicMock(return_value=[])  # ريبو فارغ بدون فروع!
    
    client2.bootstrap_put_contents = MagicMock(return_value={
        "commit": {"sha": "bootstrap_commit_sha_123"},
        "content": {"sha": "blob_init_sha"},
    })
    client2.get_commit = MagicMock(return_value={"tree": {"sha": "tree_init_sha"}})
    client2.get_tree = MagicMock(return_value={"tree": []})
    client2.create_tree = MagicMock(return_value="tree_after_boot_sha")
    client2.create_commit = MagicMock(return_value="final_commit_sha_456")
    mock_resp2 = MagicMock()
    mock_resp2.status_code = 200
    client2.update_ref = MagicMock(return_value=mock_resp2)

    payload2 = {
        "repository": "org/empty-repo",
        "branch": "main",
        "upload_files": [
            {"path": "index.html", "content_bytes": b"<!DOCTYPE html><html></html>", "bytes": 27},
            {"path": "app.py", "content_bytes": b"print('app')", "bytes": 12},
        ],
        "delete_files": [],
    }

    res2 = sync(client2, branch="main", payload=payload2)
    assert res2["status"] == "success"
    assert res2["bootstrap_file"] == "index.html"
    client2.bootstrap_put_contents.assert_called_once()
    print(f"   ملف التهيئة: {res2['bootstrap_file']}   ← ملف حقيقي من الأرشيف")
    print(f"  ✅ الدفع نجح · الفرع اتعمل · {res2['scanned']} ملف")

    # -------------------------------------------------------------
    # ── المرحلة 3: مزامنة بعد تعديل ──
    # -------------------------------------------------------------
    print("── المرحلة 3: مزامنة بعد تعديل ──")
    client3 = GhClient("org", "repo3", "mock_token")
    client3.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    client3.list_branches = MagicMock(return_value=["main"])
    
    f_content = b"unchanged app code"
    f_sha = gh_bulk.git_blob_sha(f_content)

    client3.get_ref = MagicMock(return_value={"object": {"sha": "commit_head_333"}})
    client3.get_commit = MagicMock(return_value={"tree": {"sha": "tree_sha_333"}})
    client3.get_tree = MagicMock(return_value={
        "tree": [{"path": "app.py", "type": "blob", "sha": f_sha}]
    })

    payload3 = {
        "repository": "org/repo3",
        "branch": "main",
        "upload_files": [{"path": "app.py", "content_bytes": f_content, "bytes": len(f_content)}],
        "delete_files": [],
    }

    res3 = sync(client3, branch="main", payload=payload3)
    assert res3["status"] == "up_to_date"
    assert res3["blob_count"] == 0
    print("  ✅ up_to_date (3 GET) · صفر بلوبس إضافية · المستودع مطابق")

    # -------------------------------------------------------------
    # ── المرحلة 4: الفشل والتعافي ──
    # -------------------------------------------------------------
    print("── المرحلة 4: الفشل والتعافي ──")
    client4 = GhClient("org", "repo4", "mock_token")
    client4.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    client4.list_branches = MagicMock(return_value=["main"])
    
    # محاكاة خطأ اتصال أثناء PATCH ثم إعادة القراءة يكتشف أنه تم التحديث
    client4.get_ref = MagicMock(side_effect=[
        {"object": {"sha": "head_before_attempt"}},
        {"object": {"sha": "commit_winner_sha"}},
    ])
    client4.get_commit = MagicMock(return_value={"tree": {"sha": "tree_sha_4"}})
    client4.get_tree = MagicMock(return_value={"tree": []})
    client4.create_tree = MagicMock(return_value="tree_sha_new_4")
    client4.create_commit = MagicMock(return_value="commit_winner_sha")
    
    # يفشل الطلب في المرة الأولى بمحاكاة انقطاع الاتصال
    import requests
    client4.update_ref = MagicMock(side_effect=requests.exceptions.ReadTimeout("Timeout"))

    payload4 = {
        "repository": "org/repo4",
        "branch": "main",
        "upload_files": [{"path": "fix.py", "content_bytes": b"bugfix", "bytes": 6}],
        "delete_files": [],
    }

    res4 = sync(client4, branch="main", payload=payload4)
    assert res4["status"] == "success"
    assert res4["commit_sha"] == "commit_winner_sha"
    print("  ✅ فشل الاتصال أثناء ref → إعادة القراءة والتحقق → idempotent success")

    print("\n" + "=" * 60)
    print("🏁 كل مراحل الاعتماد الأربعة اجتيزت بنجاح 100%!")
    print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    success = run_acceptance_tests()
    sys.exit(0 if success else 1)
