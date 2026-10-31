# -*- coding: utf-8 -*-
"""
tests/test_gh_bulk_unit.py
وحدات الاختبار المرجعية لمحرك gh_bulk:
- حساب git_blob_sha
- تطبيع المسارات واليونيكود NFC
- الكشف عن الملفات النصية UTF-8 مقابل الثنائية
- اختيار مرشح الـ Bootstrap
- حدود أطوال المسارات
"""

import os
import tempfile
import pathlib
import pytest
import gh_bulk


def test_git_blob_sha_calculation():
    """التحقق من مطابقة حساب الـ Blob SHA مع Git بالضبط."""
    data = b"test content for git blob sha"
    # blob 29\0test content for git blob sha -> 3225a4689da9aacab9621247c3b9861ae933b0f2
    expected = "3225a4689da9aacab9621247c3b9861ae933b0f2"
    assert gh_bulk.git_blob_sha(data) == expected


def test_normalize_remote_path_safe():
    """التحقق من تطبيع المسارات وإزالة الفواصل المعكوسة."""
    assert gh_bulk.normalize_remote_path("src\\components\\App.jsx") == "src/components/App.jsx"
    assert gh_bulk.normalize_remote_path("folder/sub/file.py", target_root="/root/") == "root/folder/sub/file.py"
    assert gh_bulk.normalize_remote_path("/leading/slash.txt") == "leading/slash.txt"


def test_normalize_remote_path_traversal_blocked():
    """منع أي محاولة path traversal باستخدام .."""
    with pytest.raises(gh_bulk.GhBulkError, match="PATH_TRAVERSAL_DETECTED"):
        gh_bulk.normalize_remote_path("../secrets.env")

    with pytest.raises(gh_bulk.GhBulkError, match="PATH_TRAVERSAL_DETECTED"):
        gh_bulk.normalize_remote_path("safe/../../danger.txt")


def test_normalize_remote_path_length_limit():
    """التحقق من سقف الحد الأقصى للمسار."""
    long_path = "a/" * 500  # 1000 chars > 900
    with pytest.raises(gh_bulk.GhBulkError, match="PATH_TOO_LONG"):
        gh_bulk.normalize_remote_path(long_path)


def test_is_text_content_detection():
    """التحقق من التمييز الدقيق بين الملفات النصية والملفات الثنائية."""
    text_sample = "console.log('مرحباً بالعالم');\n".encode("utf-8")
    is_txt, s = gh_bulk.is_text_content(text_sample)
    assert is_txt is True
    assert "مرحباً بالعالم" in s

    binary_sample = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    is_txt_b, _ = gh_bulk.is_text_content(binary_sample)
    assert is_txt_b is False


def test_find_bootstrap_candidate_preference():
    """التحقق من تفضيل ملفات مثل index.html أو README.md للـ Bootstrap."""
    with tempfile.TemporaryDirectory() as td:
        p_td = pathlib.Path(td)
        f_img = p_td / "logo.png"
        f_img.write_bytes(b"\x89PNG\r\n\x00fake_image")

        f_txt = p_td / "notes.txt"
        f_txt.write_text("some large notes text " * 100, encoding="utf-8")

        f_index = p_td / "index.html"
        f_index.write_text("<!DOCTYPE html><html></html>", encoding="utf-8")

        files = [
            {"path": "assets/logo.png", "local_path": str(f_img)},
            {"path": "docs/notes.txt", "local_path": str(f_txt)},
            {"path": "public/index.html", "local_path": str(f_index)},
        ]

        cand = gh_bulk.find_bootstrap_candidate(files)
        assert cand is not None
        assert cand["path"] == "public/index.html", "يجب أن يفضل index.html"
