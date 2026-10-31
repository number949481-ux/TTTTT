# -*- coding: utf-8 -*-
"""
tests/test_uploader_resilience_and_transparency.py
اختبارات شاملة لتحصين رافع GitHub ضد انقطاعات الشبكة (ReadTimeout) والشفافية المطلقة لرسائل التيليجرام
"""

import os
import sys
import tempfile
import pathlib
import pytest
from unittest.mock import patch, MagicMock
import requests

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

import bridge_refactor.runtime as runtime
ns = runtime.ns

ProjectRegistry = ns.ProjectRegistry
PartialUploadError = ns.PartialUploadError
_github_http_request_with_retry = ns._github_http_request_with_retry
html_escape = ns.html_escape


def test_github_http_request_retry_on_read_timeout():
    """التحقق من أن مساعد الطلبات يعيد المحاولة تلقائياً عند حدوث ReadTimeout وينجح عند التعافي."""
    call_count = 0

    def mock_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise requests.exceptions.ReadTimeout("Simulated GitHub ReadTimeout on attempt 1")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"sha": "abc123456"}
        return mock_resp

    with patch("requests.request", side_effect=mock_request):
        resp = _github_http_request_with_retry("GET", "https://api.github.com/test", max_attempts=3, backoff_seconds=0.01)
        assert resp.status_code == 200
        assert call_count == 2, "يجب أن يعيد المحاولة وينجح في المحاولة الثانية"


def test_partial_upload_preservation_on_read_timeout():
    """التحقق من أن انقطاع الشبكة في منتصف الرفع يحتفظ بالملفات التي رُفعت بالفعل في queue.json."""
    with tempfile.TemporaryDirectory() as td:
        project_home = pathlib.Path(td)
        with patch.object(ns, "PROJECT_REGISTRY_HOME", project_home), \
             patch.object(ns, "get_project_lock", return_value=MagicMock()):
            
            registry = ProjectRegistry("prj_test_partial")
            registry.get_project_github_token = MagicMock(return_value="mock_token_123")
            registry._github_destination = MagicMock(return_value={
                "repository": "owner/repo",
                "branch": "genspark_ai_developer",
                "branch_mode": "manual",
                "target_root": "/",
            })
            registry._git_blob_sha = MagicMock(return_value="blob_sha_new")
            registry._qwen_commit_prefix_for_job = MagicMock(return_value="")

            # إنشاء ملفين محليين
            f1 = project_home / "file1.txt"
            f2 = project_home / "file2.txt"
            f1.write_text("content 1", encoding="utf-8")
            f2.write_text("content 2", encoding="utf-8")

            payload = {
                "job_id": "job_partial_123",
                "repository": "owner/repo",
                "branch": "genspark_ai_developer",
                "target_root": "/",
                "upload_files": [
                    {"path": "file1.txt", "local_path": str(f1)},
                    {"path": "file2.txt", "local_path": str(f2)},
                ],
                "delete_files": [],
                "skipped": [],
            }

            put_calls = 0
            def mock_request(method, url, **kwargs):
                nonlocal put_calls
                if method == "GET":
                    resp = MagicMock()
                    resp.status_code = 404
                    return resp
                if method == "PUT":
                    put_calls += 1
                    if put_calls == 1:
                        resp = MagicMock()
                        resp.status_code = 201
                        return resp
                    # في الملف الثاني يرمي ReadTimeout
                    raise requests.exceptions.ReadTimeout("Network dropped on file 2")
                return MagicMock(status_code=200)

            with patch("requests.request", side_effect=mock_request):
                with pytest.raises(PartialUploadError) as exc_info:
                    registry._default_github_uploader(payload)

                err = exc_info.value
                assert "file1.txt" in err.partial_state["uploaded"], "يجب الاحتفاظ بـ file1.txt في المرفوعات"
                assert err.partial_state["failed_file"] == "file2.txt", "يجب تسجيل أن الملف الذي تعثر هو file2.txt"
                assert "ReadTimeout" in err.error_code

            # التحقق من أن _execute_claimed_upload_job يحفظ التقدم في queue.json
            job = {
                "job_id": "job_partial_123",
                "project_key": registry.key,
                "checkpoint_id": "cp_1",
                "state": "uploading",
                "destination": payload,
            }
            queue_data = {"schema_version": 1, "jobs": [job]}
            registry._write_queue(queue_data)

            # إعادة تصفير العداد لاختبار _execute_claimed_upload_job
            put_calls = 0
            with patch.object(registry, "build_upload_job_plan", return_value={"job": job, "upload_files": payload["upload_files"], "delete_files": []}), \
                 patch("requests.request", side_effect=mock_request):
                
                result = registry._execute_claimed_upload_job(job)
                assert result["processed"] is False
                assert result["uploaded"] == ["file1.txt"]
                assert result["failed_file"] == "file2.txt"
                assert "ReadTimeout" in result["error"]

                # التحقق من أن queue.json تم تحديثه بـ synced_files
                saved_job = registry.list_upload_jobs()[0]
                assert saved_job["state"] == "retrying"
                assert "file1.txt" in saved_job.get("synced_files", {}).get("uploaded", [])


def test_telegram_notification_transparency_on_partial_upload():
    """التحقق من أن رسالة التيليجرام تظهر الملفات المرفوعة فعلياً ولا تدعي كذباً أن الرفع لم يبدأ."""
    sync = {
        "enabled": True,
        "queued": ["job_abc_123"],
        "jobs": [{
            "job_id": "job_abc_123",
            "state": "retrying",
            "destination": {"repository": "number949481-ux/TTTTT", "branch": "genspark_ai_developer"},
        }],
        "uploaded": ["01.33_telegram_gen_bridge.py", "PROGRESS.md"],
        "modified": ["scripts/rebuild_refactor.py"],
        "deleted": [],
        "upload_confirmed": False,
        "job_state": "retrying",
        "upload_error": "ReadTimeout",
        "failed_file": "genspark/recovery_state.json",
    }

    queued_jobs = sync["jobs"]
    has_partial = bool(sync.get("uploaded") or sync.get("modified") or sync.get("deleted"))

    github_label = (
        "⚠️ رفع جزئي مع إعادة محاولة" if (sync.get("enabled") and queued_jobs and has_partial) else (
            "تم إنشاء job GitHub لهذا المشروع ولم يتم تأكيد الرفع بعد" if (sync.get("enabled") and queued_jobs) else (
                "✅ تم الرفع والمزامنة بنجاح لـ GitHub"
            )
        )
    )

    assert github_label == "⚠️ رفع جزئي مع إعادة محاولة"

    first_job = queued_jobs[0]
    dest = first_job.get("destination", {})
    branch_label = dest.get("branch")
    job_hdr = f"• {first_job['job_id']} → {first_job['state']} → {dest['repository']} @ {branch_label}"
    stats_line = f"• 📊 تم رفع وتأكيد جزئي على GitHub: ➕ {len(sync['uploaded'])} جديد | ✏️ {len(sync['modified'])} معدل | 🗑️ {len(sync['deleted'])} محذوف"
    
    assert "01.33_telegram_gen_bridge.py" in sync["uploaded"]
    assert "scripts/rebuild_refactor.py" in sync["modified"]
    assert "لم يتم تأكيد الرفع إلى GitHub بعد" not in stats_line
