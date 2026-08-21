#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p24_qwen_commit_bridge.py
====================================
🧠 [DEC-019] حراسة تكامل محرك كوين مع رفع GitHub في الجسر:

1. resolve_shared_path موجودة في qwen_engine (محلي ➔ الأب ➔ محلي للإنشاء)
   ومطبقة على QWEN_ACCOUNTS_FILE.
2. _qwen_commit_prefix_for_job: استدعاء generate_ai_summary مرة واحدة لكل job
   قبل حلقة الـ PUT (mock — بدون أي شبكة).
3. Fallback حرفي: فشل كوين (None أو Exception) ➔ prefix فارغ ➔ نفس رسالة
   الكوميت القديمة حرفياً f"[{key}] sync {job_id}: {rel}" — الرفع لا ينكسر أبداً.
4. AI_RACE_ACCOUNTS = 0 مثبّت (قرار المالك: كل الحسابات تتسابق).
"""

import os
import sys
import pathlib
import tempfile
import unittest
import importlib.util
from unittest import mock

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.32_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")
ENGINE_PATH = webapp_dir / "qwen_engine.py"
ENGINE_SRC = ENGINE_PATH.read_text(encoding="utf-8")


def _load_bridge():
    spec = importlib.util.spec_from_file_location("_bridge_p24", str(BRIDGE_PATH))
    module = importlib.util.module_from_spec(spec)
    sys.modules["_bridge_p24"] = module
    spec.loader.exec_module(module)
    return module


_bridge = _load_bridge()
import qwen_engine  # noqa: E402


def _make_registry(key: str = "demo"):
    """ProjectRegistry بدون __init__ (لا نحتاج ملفات المشروع للاختبار الوحدوي)"""
    reg = object.__new__(_bridge.ProjectRegistry)
    reg.key = key
    return reg


SAMPLE_PAYLOAD = {
    "job_id": "JOB1",
    "upload_files": [{"path": "src/app.py", "local_path": "/tmp/x"}],
    "delete_files": ["old.txt"],
}


# ═══════════════════════════════════════════════════════════════
# العقد الأول: المسار المشترك في qwen_engine (M1)
# ═══════════════════════════════════════════════════════════════

class TestEngineSharedPath(unittest.TestCase):
    """🔎 resolve_shared_path في qwen_engine — نفس منطق P23 حرفياً"""

    def test_01_resolve_shared_path_exists(self):
        self.assertTrue(hasattr(qwen_engine, "resolve_shared_path"))

    def test_02_accounts_file_uses_resolver(self):
        self.assertIn("QWEN_ACCOUNTS_FILE = resolve_shared_path(QWEN_ACCOUNTS_BASENAME)", ENGINE_SRC)

    def test_03_local_priority(self):
        """الملف المحلي موجود ➔ يفوز حتى لو الأب فيه نسخة (Zero Breaking)"""
        with tempfile.TemporaryDirectory() as root:
            parent = pathlib.Path(root)
            child = parent / "copy1"
            child.mkdir()
            (parent / "f.json").write_text("parent", encoding="utf-8")
            (child / "f.json").write_text("local", encoding="utf-8")
            with mock.patch.object(qwen_engine, "SCRIPT_DIR", str(child)):
                self.assertEqual(qwen_engine.resolve_shared_path("f.json"), str(child / "f.json"))

    def test_04_parent_fallback(self):
        """لا محلي ➔ يلتقط من الفولدر الأب المركزي"""
        with tempfile.TemporaryDirectory() as root:
            parent = pathlib.Path(root)
            child = parent / "copy1"
            child.mkdir()
            (parent / "f.json").write_text("parent", encoding="utf-8")
            with mock.patch.object(qwen_engine, "SCRIPT_DIR", str(child)):
                self.assertEqual(qwen_engine.resolve_shared_path("f.json"), str(parent / "f.json"))

    def test_05_local_for_creation(self):
        """غير موجود في الاثنين ➔ يرجع المحلي (للإنشاء)"""
        with tempfile.TemporaryDirectory() as root:
            child = pathlib.Path(root) / "copy1"
            child.mkdir()
            with mock.patch.object(qwen_engine, "SCRIPT_DIR", str(child)):
                self.assertEqual(qwen_engine.resolve_shared_path("ghost.json"), str(child / "ghost.json"))


# ═══════════════════════════════════════════════════════════════
# العقد الثاني: حقن كوين في uploader الجسر (M2)
# ═══════════════════════════════════════════════════════════════

class TestQwenCommitPrefix(unittest.TestCase):
    """🧠 _qwen_commit_prefix_for_job — mock كامل بدون شبكة"""

    def test_01_success_returns_commit(self):
        reg = _make_registry()
        with mock.patch.object(qwen_engine, "generate_ai_summary",
                               return_value=("إضافة ميزة الكوميت الذكي", "ملخص", "qwen3.8-max")) as m:
            prefix = reg._qwen_commit_prefix_for_job(dict(SAMPLE_PAYLOAD))
        self.assertEqual(prefix, "إضافة ميزة الكوميت الذكي")
        m.assert_called_once()  # مرة واحدة فقط لكل job

    def test_02_none_result_falls_back_empty(self):
        reg = _make_registry()
        with mock.patch.object(qwen_engine, "generate_ai_summary", return_value=(None, None, None)):
            self.assertEqual(reg._qwen_commit_prefix_for_job(dict(SAMPLE_PAYLOAD)), "")

    def test_03_exception_is_isolated(self):
        """أي Exception من كوين ➔ prefix فارغ — الرفع لا ينكسر أبداً"""
        reg = _make_registry()
        with mock.patch.object(qwen_engine, "generate_ai_summary", side_effect=RuntimeError("network down")):
            self.assertEqual(reg._qwen_commit_prefix_for_job(dict(SAMPLE_PAYLOAD)), "")

    def test_04_empty_job_skips_engine(self):
        """job بلا ملفات ➔ كوين لا يُستدعى إطلاقاً (توفير الوقت والحسابات)"""
        reg = _make_registry()
        with mock.patch.object(qwen_engine, "generate_ai_summary") as m:
            prefix = reg._qwen_commit_prefix_for_job({"job_id": "J2", "upload_files": [], "delete_files": []})
        self.assertEqual(prefix, "")
        m.assert_not_called()

    def test_05_prefix_capped_150(self):
        reg = _make_registry()
        with mock.patch.object(qwen_engine, "generate_ai_summary", return_value=("ط" * 500, "s", "m")):
            self.assertEqual(len(reg._qwen_commit_prefix_for_job(dict(SAMPLE_PAYLOAD))), 150)


class TestUploaderMessageContract(unittest.TestCase):
    """📜 عقد رسائل الكوميت داخل _default_github_uploader (مصدري)"""

    def test_01_prefix_computed_once_before_put_loop(self):
        idx_prefix = BRIDGE_SRC.index("ai_prefix = self._qwen_commit_prefix_for_job(payload)")
        idx_loop = BRIDGE_SRC.index('for file_info in payload.get("upload_files", [])')
        self.assertLess(idx_prefix, idx_loop, "استدعاء كوين يجب أن يسبق حلقة الـ PUT")

    def test_02_sync_message_ai_prefix_with_verbatim_fallback(self):
        self.assertIn(
            "f\"{ai_prefix} [{self.key}] sync {payload['job_id']}: {rel}\" if ai_prefix else f\"[{self.key}] sync {payload['job_id']}: {rel}\"",
            BRIDGE_SRC,
        )

    def test_03_delete_message_ai_prefix_with_verbatim_fallback(self):
        self.assertIn(
            "f\"{ai_prefix} [{self.key}] delete {payload['job_id']}: {rel}\" if ai_prefix else f\"[{self.key}] delete {payload['job_id']}: {rel}\"",
            BRIDGE_SRC,
        )

    def test_04_helper_is_fully_isolated(self):
        """الـ helper كله داخل try/except Exception — كوين لا يكسر الرفع"""
        start = BRIDGE_SRC.index("def _qwen_commit_prefix_for_job")
        end = BRIDGE_SRC.index("def _default_github_uploader")
        helper = BRIDGE_SRC[start:end]
        self.assertIn("try:", helper)
        self.assertIn("except Exception", helper)
        self.assertIn('return ""', helper)


# ═══════════════════════════════════════════════════════════════
# العقد الثالث: تثبيت قرار المالك AI_RACE_ACCOUNTS = 0
# ═══════════════════════════════════════════════════════════════

class TestOwnerDecisions(unittest.TestCase):
    def test_01_all_accounts_race(self):
        """قرار (A): 0 = كل الحسابات النشطة تتسابق"""
        self.assertEqual(qwen_engine.AI_RACE_ACCOUNTS, 0)

    def test_02_engine_timeout_unchanged(self):
        """مهلة المحرك الأصلية 30ث/مرحلة كما هي — بدون اختراع أرقام"""
        for stage in qwen_engine.AI_MODEL_CHAIN:
            self.assertEqual(stage.get("timeout"), 30)

    def test_03_fallback_msg_constant(self):
        self.assertEqual(qwen_engine.AI_FALLBACK_COMMIT_MSG, "كوميت")


if __name__ == "__main__":
    unittest.main(verbosity=2)
