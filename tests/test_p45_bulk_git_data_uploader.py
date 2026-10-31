# -*- coding: utf-8 -*-
"""
tests/test_p45_bulk_git_data_uploader.py
اختبار إدماج محرك Git Data API الذري (gh_bulk) مع ProjectRegistry في bridge_refactor:
- التحقق من استدعاء _default_github_uploader لمحرك gh_bulk.sync_payload
- التحقق من بناء الكوميت الذري وإرجاع الإحصائيات المتوقعة
- التحقق من توافق دورة حياة الوظيفة (claim_upload_job -> execute -> success)
"""

import os
import sys
import tempfile
import pathlib
import pytest
from unittest.mock import patch, MagicMock

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

import bridge_refactor.runtime as runtime
ns = runtime.ns
ProjectRegistry = ns.ProjectRegistry


def test_project_registry_uses_bulk_git_data_uploader():
    """التحقق من أن ProjectRegistry._default_github_uploader يستخدم gh_bulk بنجاح."""
    with tempfile.TemporaryDirectory() as td:
        project_home = pathlib.Path(td)
        with patch.object(ns, "PROJECT_REGISTRY_HOME", project_home), \
             patch.object(ns, "get_project_lock", return_value=MagicMock()):

            registry = ProjectRegistry("prj_bulk_test")
            registry.get_project_github_token = MagicMock(return_value="mock_gh_token")
            registry._github_destination = MagicMock(return_value={
                "repository": "testuser/myrepo",
                "branch": "main",
                "target_root": "/",
            })

            # إنشاء ملف تجريبي
            f1 = project_home / "index.html"
            f1.write_text("<h1>Bulk Uploader Test</h1>", encoding="utf-8")

            payload = {
                "job_id": "job_bulk_1",
                "repository": "testuser/myrepo",
                "branch": "main",
                "target_root": "/",
                "upload_files": [
                    {"path": "index.html", "local_path": str(f1), "bytes": f1.stat().st_size},
                ],
                "delete_files": [],
                "skipped": [],
            }

            mock_sync_result = {
                "uploaded": ["index.html"],
                "modified": [],
                "unchanged": [],
                "deleted": [],
                "skipped": [],
                "commit_sha": "commit_bulk_sha_777",
                "inline_count": 1,
                "blob_count": 0,
            }

            with patch("gh_bulk.sync_payload", return_value=mock_sync_result) as mock_sync:
                res = registry._default_github_uploader(payload)
                mock_sync.assert_called_once()
                assert res["uploaded"] == ["index.html"]
                assert res["commit_sha"] == "commit_bulk_sha_777"


def test_full_job_execution_with_bulk_uploader():
    """التحقق من تنفيذ الوظيفة بالكامل عبر _execute_claimed_upload_job بنجاح."""
    with tempfile.TemporaryDirectory() as td:
        project_home = pathlib.Path(td)
        with patch.object(ns, "PROJECT_REGISTRY_HOME", project_home), \
             patch.object(ns, "get_project_lock", return_value=MagicMock()):

            registry = ProjectRegistry("prj_job_exec")
            registry.get_project_github_token = MagicMock(return_value="mock_gh_token")

            # ملف تجريبي
            f1 = project_home / "app.py"
            f1.write_text("print('bulk ok')", encoding="utf-8")

            job = {
                "job_id": "job_exec_001",
                "project_key": registry.key,
                "checkpoint_id": "cp_100",
                "state": "uploading",
                "destination": {
                    "repository": "testuser/myrepo",
                    "branch": "main",
                    "target_root": "/",
                },
            }
            queue_data = {"schema_version": 1, "jobs": [job]}
            registry._write_queue(queue_data)

            plan = {
                "job": job,
                "upload_files": [{"path": "app.py", "local_path": str(f1), "bytes": f1.stat().st_size}],
                "delete_files": [],
                "skipped": [],
            }

            mock_sync_result = {
                "uploaded": ["app.py"],
                "modified": [],
                "unchanged": [],
                "deleted": [],
                "skipped": [],
                "commit_sha": "commit_sha_exec_999",
                "inline_count": 1,
                "blob_count": 0,
            }

            with patch.object(registry, "build_upload_job_plan", return_value=plan), \
                 patch("gh_bulk.sync_payload", return_value=mock_sync_result):

                result = registry._execute_claimed_upload_job(job)
                assert result.get("processed") is not False
                assert result["uploaded"] == ["app.py"]
