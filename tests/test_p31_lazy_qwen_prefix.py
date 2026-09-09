#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p31_lazy_qwen_prefix.py
==================================
⏳ [P31] حراسة الاستدعاء الكسول لكوين داخل _default_github_uploader:

المشكلة الأصلية: ai_prefix كان يُحسب قبل حلقة الـ PUT — أي قبل معرفة إن كانت
هناك تغييرات فعلية أصلاً — فكان كوين يُستدعى (شبكة + مهلة حتى 30ث) حتى لو
كل ملفات الـ job مطابقة للريموت بايت-بايت (unchanged) وصفر commits تحدث.

عقود P31:
1. job كله unchanged (وكل delete_files غير موجودة على الريموت 404)
   ← كوين لا يُستدعى إطلاقاً (صفر نداء — توفير الباقة والوقت).
2. أول ملف متغير فعلياً ← كوين يُستدعى مرة واحدة فقط (memoized)
   حتى مع تعدد الملفات المتغيرة — نفس عقد DEC-019.
3. delete فعلي (الملف موجود على الريموت 200) ← يوقظ كوين إن لم يستيقظ.
4. رسائل الكوميت نفسها حرفياً: بادئة كوين عند النجاح، وإلا الرسالة القديمة
   f"[{key}] sync {job_id}: {rel}" بلا أي تغيير (Zero Breaking).
5. عقود مصدرية: ai_prefix = None + def _lazy_ai_prefix + النداء الكسول
   يقع بعد فحص unchanged داخل الحلقة.

كل الفحوصات mock كامل — بدون أي شبكة حقيقية.
"""

import sys
import pathlib
import tempfile
import unittest
import importlib.util
from unittest import mock

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")
P07_PATH = webapp_dir / "bridge_refactor" / "parts" / "p07_state_registry.py"
P07_SRC = P07_PATH.read_text(encoding="utf-8")


def _load_bridge():
    spec = importlib.util.spec_from_file_location("_bridge_p31", str(BRIDGE_PATH))
    module = importlib.util.module_from_spec(spec)
    sys.modules["_bridge_p31"] = module
    spec.loader.exec_module(module)
    return module


_bridge = _load_bridge()
import qwen_engine  # noqa: E402


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def _make_registry(key: str = "demo"):
    """ProjectRegistry بدون __init__ + توكن وهمي (لا ملفات مشروع ولا شبكة)"""
    reg = object.__new__(_bridge.ProjectRegistry)
    reg.key = key
    reg.get_project_github_token = lambda: "ghp_dummy_token_for_tests"
    return reg


def _write_tmp(dirpath: str, name: str, content: bytes) -> str:
    p = pathlib.Path(dirpath) / name
    p.write_bytes(content)
    return str(p)


def _base_payload(**overrides) -> dict:
    payload = {
        "job_id": "JOBX",
        "repository": "owner/repo",
        "branch": "main",
        "target_root": "/",
        "upload_files": [],
        "delete_files": [],
        "skipped": [],
    }
    payload.update(overrides)
    return payload


# ═══════════════════════════════════════════════════════════════
# العقد الأول: job كله unchanged ← صفر نداء لكوين (جوهر P31)
# ═══════════════════════════════════════════════════════════════

class TestLazySkipsQwenWhenNothingChanged(unittest.TestCase):

    def test_01_all_unchanged_files_never_call_qwen(self):
        """كل الملفات مطابقة للريموت (نفس blob sha) ← كوين لا يُستدعى إطلاقاً"""
        reg = _make_registry()
        with tempfile.TemporaryDirectory() as tmp:
            local = _write_tmp(tmp, "same.py", b"identical content")
            same_sha = reg._git_blob_sha(local)
            payload = _base_payload(
                upload_files=[{"path": "same.py", "local_path": local}],
            )
            with mock.patch("requests.get", return_value=_FakeResponse(200, {"sha": same_sha})), \
                 mock.patch("requests.put") as m_put, \
                 mock.patch.object(qwen_engine, "generate_ai_summary") as m_qwen:
                result = reg._default_github_uploader(payload)
        m_qwen.assert_not_called()
        m_put.assert_not_called()
        self.assertEqual(result["unchanged"], ["same.py"])
        self.assertEqual(result["uploaded"], [])
        self.assertEqual(result["modified"], [])

    def test_02_delete_of_missing_remote_file_never_calls_qwen(self):
        """delete_files كلها 404 على الريموت (لا حذف فعلي) ← كوين لا يُستدعى"""
        reg = _make_registry()
        payload = _base_payload(delete_files=["ghost.txt"])
        with mock.patch("requests.get", return_value=_FakeResponse(404)), \
             mock.patch("requests.delete") as m_del, \
             mock.patch.object(qwen_engine, "generate_ai_summary") as m_qwen:
            result = reg._default_github_uploader(payload)
        m_qwen.assert_not_called()
        m_del.assert_not_called()
        self.assertEqual(result["deleted"], [])

    def test_03_unchanged_plus_missing_delete_combined_zero_calls(self):
        """المزيج الكامل: unchanged + delete 404 ← صفر نداء (سيناريو sync cycle الدوري)"""
        reg = _make_registry()
        with tempfile.TemporaryDirectory() as tmp:
            local = _write_tmp(tmp, "same.py", b"stable")
            same_sha = reg._git_blob_sha(local)
            payload = _base_payload(
                upload_files=[{"path": "same.py", "local_path": local}],
                delete_files=["ghost.txt"],
            )

            def fake_get(api, **kwargs):
                if api.endswith("/same.py"):
                    return _FakeResponse(200, {"sha": same_sha})
                return _FakeResponse(404)

            with mock.patch("requests.get", side_effect=fake_get), \
                 mock.patch.object(qwen_engine, "generate_ai_summary") as m_qwen:
                reg._default_github_uploader(payload)
        m_qwen.assert_not_called()


# ═══════════════════════════════════════════════════════════════
# العقد الثاني: أول تغيير فعلي يوقظ كوين — مرة واحدة فقط (memoized)
# ═══════════════════════════════════════════════════════════════

class TestLazyWakesQwenOnceOnRealChange(unittest.TestCase):

    def test_01_changed_file_calls_qwen_exactly_once(self):
        """ملف جديد (404 على الريموت) ← كوين مرة واحدة + البادئة في الرسالة"""
        reg = _make_registry(key="prj_test")
        with tempfile.TemporaryDirectory() as tmp:
            local = _write_tmp(tmp, "new.py", b"fresh code")
            payload = _base_payload(upload_files=[{"path": "new.py", "local_path": local}])
            with mock.patch("requests.get", return_value=_FakeResponse(404)), \
                 mock.patch("requests.put", return_value=_FakeResponse(201)) as m_put, \
                 mock.patch.object(qwen_engine, "generate_ai_summary",
                                   return_value=("رسالة كوين", "s", "m")) as m_qwen:
                result = reg._default_github_uploader(payload)
        m_qwen.assert_called_once()
        self.assertEqual(result["uploaded"], ["new.py"])
        sent_message = m_put.call_args.kwargs["json"]["message"]
        self.assertEqual(sent_message, "رسالة كوين [prj_test] sync JOBX: new.py")

    def test_02_multiple_changed_files_still_one_qwen_call(self):
        """3 ملفات متغيرة ← كوين مرة واحدة فقط (memoization — عقد DEC-019 محفوظ)"""
        reg = _make_registry()
        with tempfile.TemporaryDirectory() as tmp:
            files = [
                {"path": f"f{i}.py", "local_path": _write_tmp(tmp, f"f{i}.py", f"code{i}".encode())}
                for i in range(3)
            ]
            payload = _base_payload(upload_files=files)
            with mock.patch("requests.get", return_value=_FakeResponse(404)), \
                 mock.patch("requests.put", return_value=_FakeResponse(201)), \
                 mock.patch.object(qwen_engine, "generate_ai_summary",
                                   return_value=("كوميت", "s", "m")) as m_qwen:
                result = reg._default_github_uploader(payload)
        m_qwen.assert_called_once()
        self.assertEqual(len(result["uploaded"]), 3)

    def test_03_unchanged_then_changed_wakes_qwen_after_skip(self):
        """ملف unchanged أولاً ثم ملف متغير ← كوين يستيقظ عند الثاني فقط — مرة واحدة"""
        reg = _make_registry()
        with tempfile.TemporaryDirectory() as tmp:
            same = _write_tmp(tmp, "same.py", b"stable")
            fresh = _write_tmp(tmp, "new.py", b"fresh")
            same_sha = reg._git_blob_sha(same)
            payload = _base_payload(upload_files=[
                {"path": "same.py", "local_path": same},
                {"path": "new.py", "local_path": fresh},
            ])

            def fake_get(api, **kwargs):
                if api.endswith("/same.py"):
                    return _FakeResponse(200, {"sha": same_sha})
                return _FakeResponse(404)

            with mock.patch("requests.get", side_effect=fake_get), \
                 mock.patch("requests.put", return_value=_FakeResponse(201)), \
                 mock.patch.object(qwen_engine, "generate_ai_summary",
                                   return_value=("كوميت", "s", "m")) as m_qwen:
                result = reg._default_github_uploader(payload)
        m_qwen.assert_called_once()
        self.assertEqual(result["unchanged"], ["same.py"])
        self.assertEqual(result["uploaded"], ["new.py"])

    def test_04_real_delete_wakes_qwen(self):
        """delete فعلي (الملف موجود 200 على الريموت) ← كوين يُستدعى مرة واحدة"""
        reg = _make_registry(key="prj_del")
        payload = _base_payload(delete_files=["old.txt"])
        with mock.patch("requests.get", return_value=_FakeResponse(200, {"sha": "remote_sha"})), \
             mock.patch("requests.delete", return_value=_FakeResponse(200)) as m_del, \
             mock.patch.object(qwen_engine, "generate_ai_summary",
                               return_value=("حذف قديم", "s", "m")) as m_qwen:
            result = reg._default_github_uploader(payload)
        m_qwen.assert_called_once()
        self.assertEqual(result["deleted"], ["old.txt"])
        sent_message = m_del.call_args.kwargs["json"]["message"]
        self.assertEqual(sent_message, "حذف قديم [prj_del] delete JOBX: old.txt")


# ═══════════════════════════════════════════════════════════════
# العقد الثالث: Fallback الحرفي محفوظ (Zero Breaking من DEC-019)
# ═══════════════════════════════════════════════════════════════

class TestVerbatimFallbackPreserved(unittest.TestCase):

    def test_01_qwen_failure_keeps_old_message_verbatim(self):
        """فشل كوين (Exception) ← نفس رسالة الكوميت القديمة حرفياً — الرفع لا ينكسر"""
        reg = _make_registry(key="prj_fb")
        with tempfile.TemporaryDirectory() as tmp:
            local = _write_tmp(tmp, "app.py", b"code")
            payload = _base_payload(upload_files=[{"path": "app.py", "local_path": local}])
            with mock.patch("requests.get", return_value=_FakeResponse(404)), \
                 mock.patch("requests.put", return_value=_FakeResponse(201)) as m_put, \
                 mock.patch.object(qwen_engine, "generate_ai_summary",
                                   side_effect=RuntimeError("network down")):
                result = reg._default_github_uploader(payload)
        self.assertEqual(result["uploaded"], ["app.py"])
        sent_message = m_put.call_args.kwargs["json"]["message"]
        self.assertEqual(sent_message, "[prj_fb] sync JOBX: app.py")

    def test_02_failed_qwen_memoized_not_retried_per_file(self):
        """فشل كوين مرة ← يُحفظ "" ولا تتكرر المحاولة لكل ملف (memoized حتى في الفشل)"""
        reg = _make_registry()
        with tempfile.TemporaryDirectory() as tmp:
            files = [
                {"path": f"f{i}.py", "local_path": _write_tmp(tmp, f"f{i}.py", f"c{i}".encode())}
                for i in range(3)
            ]
            payload = _base_payload(upload_files=files)
            with mock.patch("requests.get", return_value=_FakeResponse(404)), \
                 mock.patch("requests.put", return_value=_FakeResponse(201)), \
                 mock.patch.object(qwen_engine, "generate_ai_summary",
                                   side_effect=RuntimeError("down")) as m_qwen:
                reg._default_github_uploader(payload)
        m_qwen.assert_called_once()


# ═══════════════════════════════════════════════════════════════
# العقد الرابع: عقود مصدرية (المصدر 01.33 + الجزء p07 متطابقان)
# ═══════════════════════════════════════════════════════════════

class TestSourceContracts(unittest.TestCase):

    def _uploader_block(self, src: str) -> str:
        start = src.index("def _default_github_uploader")
        end = src.index("def recover_upload_queue_after_restart")
        return src[start:end]

    def test_01_ai_prefix_starts_none_in_both(self):
        for src in (BRIDGE_SRC, P07_SRC):
            block = self._uploader_block(src)
            self.assertIn("ai_prefix = None", block)

    def test_02_lazy_helper_defined_in_both(self):
        for src in (BRIDGE_SRC, P07_SRC):
            block = self._uploader_block(src)
            self.assertIn("def _lazy_ai_prefix()", block)
            self.assertIn("nonlocal ai_prefix", block)

    def test_03_lazy_call_after_unchanged_check(self):
        """النداء الكسول داخل حلقة الرفع يقع بعد فحص unchanged (وليس قبل الحلقة)"""
        block = self._uploader_block(BRIDGE_SRC)
        idx_unchanged = block.index("unchanged.append(rel)")
        idx_lazy_call = block.index("_lazy_ai_prefix()", block.index("for file_info"))
        self.assertGreater(idx_lazy_call, idx_unchanged,
                           "النداء الكسول يجب أن يقع بعد فحص unchanged داخل الحلقة")

    def test_04_no_eager_call_before_put_loop(self):
        """لا يوجد استدعاء مباشر eager لـ _qwen_commit_prefix_for_job قبل الحلقة —
        الاستدعاء الوحيد داخل جسم _lazy_ai_prefix (مسبوق بـ nonlocal + فحص None)"""
        block = self._uploader_block(BRIDGE_SRC)
        call = "self._qwen_commit_prefix_for_job(payload)"
        self.assertEqual(block.count(call), 1, "استدعاء واحد فقط داخل _lazy_ai_prefix")
        idx_call = block.index(call)
        idx_lazy_def = block.index("def _lazy_ai_prefix()")
        idx_loop = block.index('for file_info in payload.get("upload_files"')
        self.assertGreater(idx_call, idx_lazy_def)
        self.assertLess(idx_call, idx_loop, "جسم _lazy_ai_prefix معرَّف قبل الحلقة")

    def test_05_commit_messages_unchanged_verbatim(self):
        """صياغة رسائل sync/delete كما هي حرفياً (لم يمسها P31)"""
        for needle in (
            "f\"{ai_prefix} [{self.key}] sync {payload['job_id']}: {rel}\" if ai_prefix else f\"[{self.key}] sync {payload['job_id']}: {rel}\"",
            "f\"{ai_prefix} [{self.key}] delete {payload['job_id']}: {rel}\" if ai_prefix else f\"[{self.key}] delete {payload['job_id']}: {rel}\"",
        ):
            self.assertIn(needle, BRIDGE_SRC)
            self.assertIn(needle, P07_SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
