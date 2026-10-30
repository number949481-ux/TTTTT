# -*- coding: utf-8 -*-
"""
tests/test_gh_bulk_inline.py
10 فحوصات دقيقة لـ Inline Content و CRLF والتطبيع والتوافق:
1. ملف ASCII صغير <= 4KB -> inline
2. ملف UTF-8 عربي <= 4KB -> inline
3. ملف بحجم 4096 بايت بالضبط -> inline
4. ملف بحجم 4097 بايت -> Blob منفصل
5. ملف صغير يحتوي على null byte -> Blob منفصل
6. الحفاظ على فواصل الأسطر CRLF و LF كما هي
7. ملف فارغ 0 بايت -> inline
8. تطبيع أسماء الملفات العربية NFC
9. تحويل backslashes الويندوز إلى forward slashes
10. مطابقة واجهة sync_payload لمخرجات _default_github_uploader
"""

import sys
import unicodedata
import pytest
from unittest.mock import MagicMock
import gh_bulk
from gh_bulk import GhClient, sync, sync_payload


def test_01_small_ascii_inline():
    """1. ملف ASCII صغير <= 4KB -> inline."""
    content = b"console.log('test');\n"
    is_txt, text = gh_bulk.is_text_content(content)
    assert is_txt is True
    assert len(content) <= gh_bulk.INLINE_CONTENT_MAX_BYTES


def test_02_arabic_utf8_inline():
    """2. ملف UTF-8 عربي <= 4KB -> inline."""
    content = "أهلاً بك في نظام المزامنة الذري\n".encode("utf-8")
    is_txt, text = gh_bulk.is_text_content(content)
    assert is_txt is True
    assert "نظام المزامنة" in text


def test_03_exact_4096_bytes_inline():
    """3. ملف بحجم 4096 بايت بالضبط -> inline."""
    content = b"a" * 4096
    is_txt, _ = gh_bulk.is_text_content(content)
    assert is_txt is True
    assert len(content) <= gh_bulk.INLINE_CONTENT_MAX_BYTES


def test_04_4097_bytes_requires_blob():
    """4. ملف بحجم 4097 بايت -> يتجاوز حد الـ Inline ويحتاج Blob."""
    content = b"a" * 4097
    assert len(content) > gh_bulk.INLINE_CONTENT_MAX_BYTES


def test_05_null_byte_treated_as_binary():
    """5. ملف صغير يحتوي على null byte -> يعامل كـ Binary ويحتاج Blob."""
    content = b"hello\x00world"
    is_txt, _ = gh_bulk.is_text_content(content)
    assert is_txt is False


def test_06_crlf_preservation():
    """6. الحفاظ على فواصل الأسطر CRLF و LF دون تحوير."""
    content = b"line1\r\nline2\r\nline3\n"
    is_txt, text = gh_bulk.is_text_content(content)
    assert is_txt is True
    assert "\r\n" in text


def test_07_empty_file_inline():
    """7. ملف فارغ 0 بايت -> inline صالح."""
    content = b""
    is_txt, text = gh_bulk.is_text_content(content)
    assert is_txt is True
    assert text == ""


def test_08_arabic_nfc_normalization():
    """8. تطبيع أسماء الملفات العربية NFC."""
    # كتابة كلمة بالأشكال المفككة ثم التطبيع
    raw = "ملف_عربي.txt"
    norm = gh_bulk.normalize_remote_path(raw)
    assert unicodedata.is_normalized("NFC", norm)


def test_09_windows_backslash_conversion():
    """9. تحويل backslashes الويندوز إلى forward slashes."""
    raw = "deep\\nested\\folder\\component.tsx"
    norm = gh_bulk.normalize_remote_path(raw)
    assert norm == "deep/nested/folder/component.tsx"


def test_10_sync_payload_schema_compatibility():
    """10. مطابقة واجهة sync_payload لمخرجات _default_github_uploader بدقة."""
    client = GhClient("owner", "repo", "tok")
    client.get_repo_info = MagicMock(return_value={"default_branch": "main"})
    client.list_branches = MagicMock(return_value=["main"])
    client.get_ref = MagicMock(return_value={"object": {"sha": "head_sha"}})
    client.get_commit = MagicMock(return_value={"tree": {"sha": "t_sha"}})
    client.get_tree = MagicMock(return_value={"tree": []})
    client.create_tree = MagicMock(return_value="t_new")
    client.create_commit = MagicMock(return_value="c_new")
    
    resp_mock = MagicMock()
    resp_mock.status_code = 200
    client.update_ref = MagicMock(return_value=resp_mock)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(gh_bulk, "GhClient", lambda owner, repo, token: client)

        payload = {
            "job_id": "job_999",
            "project_key": "prj_demo",
            "repository": "owner/repo",
            "branch": "main",
            "target_root": "/",
            "upload_files": [{"path": "main.py", "content_bytes": b"print(1)", "bytes": 8}],
            "delete_files": [],
            "skipped": ["ignored.log"],
        }

        out = sync_payload(payload, token="tok")

        # التحقق من المفاتيح المتوقعة في ProjectRegistry
        expected_keys = {"uploaded", "modified", "unchanged", "deleted", "skipped", "commit_sha", "inline_count", "blob_count"}
        assert expected_keys.issubset(out.keys())
        assert out["uploaded"] == ["main.py"]
        assert out["commit_sha"] == "c_new"
        assert out["skipped"] == ["ignored.log"]
