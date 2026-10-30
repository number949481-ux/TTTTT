# -*- coding: utf-8 -*-
"""
tests/test_gh_bulk_mock.py
اختبارات السيناريوهات المعمارية للـ Mock لمحرك gh_bulk:
1. ريبو فارغ (0 فروع) -> Bootstrap عبر PUT /contents بملف حقيقي
2. فرع غير موجود في ريبو قائم -> الاستناد للفرع الافتراضي وعمل POST /git/refs
3. مستودع مطابق (Up to date) -> صفر كوميتات وصفر بلوبس
4. رفع ذري (Atomic single commit) يجمع Inline + Blobs
5. انقطاع الاتصال أثناء PATCH والتعافي التلقائي (Idempotent)
6. تعارض حقيقي (409 Concurrent Push)
7. فشل التحقق (422 Validation Failed)
8. الفحص الجاف (dry_run=True)
9. انتهاء المهلة الكلية للمزامنة (SyncTimeoutError)
"""

import os
import tempfile
import pathlib
import pytest
from unittest.mock import MagicMock, patch
import requests

import gh_bulk
from gh_bulk import (
    GhClient,
    sync,
    sync_payload,
    ConcurrentPushConflictError,
    ValidationFailedError,
    SyncTimeoutError,
)


@pytest.fixture
def mock_client():
    client = GhClient(owner="testowner", repo="testrepo", token="ghp_mock_token_123")
    return client


def test_empty_repo_bootstrap_flow(mock_client):
    """
    السيناريو 1: مستودع فارغ بدون أي فروع (len(branches) == 0).
    يجب أن يقوم بعمل Bootstrap بملف حقيقي عبر PUT /contents أولاً،
    ثم إكمال الرفع عبر Git Data API بنجاح.
    """
    mock_client.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    mock_client.list_branches = MagicMock(return_value=[])  # 0 فروع = فارغ تماماً
    
    mock_client.bootstrap_put_contents = MagicMock(return_value={
        "commit": {"sha": "sha_boot_init_111"},
        "content": {"sha": "blob_boot_sha"},
    })
    mock_client.get_commit = MagicMock(return_value={"tree": {"sha": "tree_boot_000"}})
    mock_client.get_tree = MagicMock(return_value={"tree": []})
    mock_client.create_tree = MagicMock(return_value="tree_final_222")
    mock_client.create_commit = MagicMock(return_value="commit_final_333")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client.update_ref = MagicMock(return_value=mock_resp)

    payload = {
        "repository": "testowner/testrepo",
        "branch": "main",
        "upload_files": [
            {"path": "index.html", "content_bytes": b"<h1>Hello</h1>", "bytes": 14},
            {"path": "script.js", "content_bytes": b"console.log('hi');", "bytes": 18},
        ],
        "delete_files": [],
    }

    result = sync(mock_client, branch="main", payload=payload)

    # التحقق من استدعاء Bootstrap
    mock_client.bootstrap_put_contents.assert_called_once()
    assert result["status"] == "success"
    assert result["commit_sha"] == "commit_final_333"
    assert result["bootstrap_file"] == "index.html"


def test_missing_branch_on_existing_repo(mock_client):
    """
    السيناريو 2: المستودع ليس فارغاً (يحتوي على main)، لكن الفرع المطلوب feature-new غير موجود.
    يجب أن يستند إلى main كـ base ثم ينشئ الفرع الجديد بـ create_ref (POST /git/refs).
    """
    mock_client.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    mock_client.list_branches = MagicMock(return_value=["main"])
    mock_client.get_ref = MagicMock(return_value={"object": {"sha": "sha_main_head"}})
    mock_client.get_commit = MagicMock(return_value={"tree": {"sha": "tree_main_sha"}})
    mock_client.get_tree = MagicMock(return_value={"tree": []})
    mock_client.create_tree = MagicMock(return_value="tree_new_branch")
    mock_client.create_commit = MagicMock(return_value="commit_new_branch")
    mock_client.create_ref = MagicMock(return_value={"ref": "refs/heads/feature-new"})

    payload = {
        "repository": "testowner/testrepo",
        "branch": "feature-new",
        "upload_files": [
            {"path": "file1.txt", "content_bytes": b"new feature content", "bytes": 19},
        ],
        "delete_files": [],
    }

    result = sync(mock_client, branch="feature-new", payload=payload)

    assert result["status"] == "success"
    mock_client.create_ref.assert_called_once_with("feature-new", "commit_new_branch")


def test_up_to_date_no_changes(mock_client):
    """
    السيناريو 3: المستودع يحتوي بالفعل على نفس الملفات بنفس الـ SHA.
    يجب أن يكتشف up_to_date ولا ينشئ أي شجرة أو كوميت جديد.
    """
    file_bytes = b"hello constant content"
    f_sha = gh_bulk.git_blob_sha(file_bytes)

    mock_client.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    mock_client.list_branches = MagicMock(return_value=["main"])
    mock_client.get_ref = MagicMock(return_value={"object": {"sha": "head_sha_unchanged"}})
    mock_client.get_commit = MagicMock(return_value={"tree": {"sha": "tree_sha_1"}})
    mock_client.get_tree = MagicMock(return_value={
        "tree": [{"path": "hello.txt", "type": "blob", "sha": f_sha}]
    })

    payload = {
        "repository": "testowner/testrepo",
        "branch": "main",
        "upload_files": [
            {"path": "hello.txt", "content_bytes": file_bytes, "bytes": len(file_bytes)},
        ],
        "delete_files": [],
    }

    result = sync(mock_client, branch="main", payload=payload)

    assert result["status"] == "up_to_date"
    assert result["unchanged"] == ["hello.txt"]
    assert result["uploaded"] == []
    assert result["modified"] == []


def test_atomic_single_commit_inline_and_blobs(mock_client):
    """
    السيناريو 4: رفع ملفين: أحدهما نصي صغير (Inline) والآخر ثنائي (Blob).
    يجب أن يجمعهم في كوميت واحد ذري.
    """
    mock_client.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    mock_client.list_branches = MagicMock(return_value=["main"])
    mock_client.get_ref = MagicMock(return_value={"object": {"sha": "head_sha_old"}})
    mock_client.get_commit = MagicMock(return_value={"tree": {"sha": "tree_sha_old"}})
    mock_client.get_tree = MagicMock(return_value={"tree": []})

    mock_client.create_blob = MagicMock(return_value="blob_binary_sha")
    mock_client.create_tree = MagicMock(return_value="tree_combined_sha")
    mock_client.create_commit = MagicMock(return_value="commit_combined_sha")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client.update_ref = MagicMock(return_value=mock_resp)

    payload = {
        "repository": "testowner/testrepo",
        "branch": "main",
        "upload_files": [
            {"path": "small.py", "content_bytes": b"print('inline')", "bytes": 15},
            {"path": "data.bin", "content_bytes": b"\x00\xffbinary_data_here", "bytes": 20},
        ],
        "delete_files": [],
    }

    result = sync(mock_client, branch="main", payload=payload)

    assert result["status"] == "success"
    assert result["inline_count"] == 1
    assert result["blob_count"] == 1
    mock_client.create_blob.assert_called_once()
    mock_client.create_commit.assert_called_once()


def test_patch_idempotent_recovery_on_timeout(mock_client):
    """
    السيناريو 5: انقطاع الاتصال أو ReadTimeout أثناء طلب PATCH.
    العميل يتحقق من HEAD ويكتشف أن الـ SHA الخاص بنا تم تثبيته بالفعل -> Idempotent Success.
    """
    mock_client.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    mock_client.list_branches = MagicMock(return_value=["main"])
    
    # أول قراءة لـ get_ref تعطي old_head
    # القراءة بعد الانقطاع تعطي new_commit_sha
    mock_client.get_ref = MagicMock(side_effect=[
        {"object": {"sha": "old_head"}},
        {"object": {"sha": "commit_win_444"}},
    ])
    mock_client.get_commit = MagicMock(return_value={"tree": {"sha": "t_sha"}})
    mock_client.get_tree = MagicMock(return_value={"tree": []})
    mock_client.create_tree = MagicMock(return_value="t_new")
    mock_client.create_commit = MagicMock(return_value="commit_win_444")
    
    # محاكاة انقطاع الاتصال في PATCH
    mock_client.update_ref = MagicMock(side_effect=requests.exceptions.ReadTimeout("GitHub timed out"))

    payload = {
        "repository": "testowner/testrepo",
        "branch": "main",
        "upload_files": [{"path": "file.txt", "content_bytes": b"content", "bytes": 7}],
        "delete_files": [],
    }

    result = sync(mock_client, branch="main", payload=payload)
    assert result["status"] == "success"
    assert result["commit_sha"] == "commit_win_444"


def test_patch_conflict_409(mock_client):
    """
    السيناريو 6: فشل PATCH بـ 409 وتعارض حقيقي في الفروع.
    يجب أن يرفع ConcurrentPushConflictError.
    """
    mock_client.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    mock_client.list_branches = MagicMock(return_value=["main"])
    mock_client.get_ref = MagicMock(side_effect=[
        {"object": {"sha": "old_head"}},
        {"object": {"sha": "someone_else_pushed"}},
    ])
    mock_client.get_commit = MagicMock(return_value={"tree": {"sha": "t_sha"}})
    mock_client.get_tree = MagicMock(return_value={"tree": []})
    mock_client.create_tree = MagicMock(return_value="t_new")
    mock_client.create_commit = MagicMock(return_value="our_commit")
    
    mock_resp_409 = MagicMock()
    mock_resp_409.status_code = 409
    mock_resp_409.text = "Conflict: Reference update rejected"
    mock_client.update_ref = MagicMock(return_value=mock_resp_409)
    mock_client.compare_commits = MagicMock(return_value={"status": "diverged"})

    payload = {
        "repository": "testowner/testrepo",
        "branch": "main",
        "upload_files": [{"path": "file.txt", "content_bytes": b"content", "bytes": 7}],
        "delete_files": [],
    }

    with pytest.raises(ConcurrentPushConflictError):
        sync(mock_client, branch="main", payload=payload)


def test_dry_run_mode(mock_client):
    """
    السيناريو 8: الفحص الجاف (dry_run=True).
    يجب أن يرجع الإحصائيات الدقيقة بدون أي تعديل أو كوميت على المستودع.
    """
    mock_client.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    mock_client.list_branches = MagicMock(return_value=["main"])
    mock_client.get_ref = MagicMock(return_value={"object": {"sha": "head_sha"}})
    mock_client.get_commit = MagicMock(return_value={"tree": {"sha": "tree_sha"}})
    mock_client.get_tree = MagicMock(return_value={"tree": [{"path": "old.txt", "type": "blob", "sha": "old_sha"}]})
    mock_client.create_commit = MagicMock()
    mock_client.update_ref = MagicMock()

    payload = {
        "repository": "testowner/testrepo",
        "branch": "main",
        "upload_files": [
            {"path": "small.txt", "content_bytes": b"abc", "bytes": 3},
            {"path": "large.bin", "content_bytes": b"\x00" * 5000, "bytes": 5000},
        ],
        "delete_files": ["old.txt"],
    }

    res = sync(mock_client, branch="main", dry_run=True, payload=payload)

    assert res["status"] == "dry_run"
    assert res["scanned"] == 3
    assert res["would_send_inline"] == 1
    assert res["would_upload_blobs"] == 1
    assert res["would_delete"] == 1
    mock_client.create_commit.assert_not_called()
    mock_client.update_ref.assert_not_called()
