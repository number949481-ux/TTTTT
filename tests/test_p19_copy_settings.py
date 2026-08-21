#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p19_copy_settings.py
===============================
📋 [P19] حراسة ميزة «نسخ إعدادات من مشروع آخر» + الترقيم التسلسلي التلقائي:

1. generate_sequential_project_name: «الحج 1» ➔ «الحج 2» ➔ «الحج 3» تلقائياً.
2. copy_project_settings_to_new_project: نسخ GitHub + الموديل + برومبت الاستئناف
   لمشروع جديد بمفتاح جديد — بدون fallback على متغيرات البيئة للتوكن.
3. build_copy_settings_source_keyboard: أزرار cpysrc: + أزرار الرجوع.
4. format_copied_settings_summary: الملخص يعرض المصدر والاسم والموديل.
5. تكامل الـ handlers: cmd:resume_copy_settings / cmd:resume_copy_back / cpysrc:.
6. بانر 01.31 + BUILD_VERSION + baseline الأب 01.30.
"""

import sys
import pathlib
import unittest
import importlib.util
from unittest import mock

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p19", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)


def _fake_projects(names):
    return [
        {"project_key": f"prj_{i:02d}", "project_name": name}
        for i, name in enumerate(names)
    ]


class TestSequentialProjectName(unittest.TestCase):
    """1. الترقيم التسلسلي التلقائي للأسماء المكررة"""

    def _gen(self, base, existing):
        with mock.patch.object(_bridge, "list_known_projects", return_value=_fake_projects(existing)):
            return _bridge.generate_sequential_project_name(base)

    def test_01_fresh_name_unchanged(self):
        self.assertEqual(self._gen("مشروع القمر", []), "مشروع القمر")

    def test_02_hajj1_becomes_hajj2(self):
        self.assertEqual(self._gen("الحج 1", ["الحج 1"]), "الحج 2")

    def test_03_next_after_highest(self):
        self.assertEqual(self._gen("الحج 1", ["الحج 1", "الحج 2", "الحج 5"]), "الحج 6")

    def test_04_bare_root_used(self):
        self.assertEqual(self._gen("الحج", ["الحج"]), "الحج 2")

    def test_05_unrelated_root_keeps_name(self):
        """جذر غير مستخدم إطلاقاً ➔ الاسم يُعاد كما هو (لا ترقيم بلا داعٍ)."""
        self.assertEqual(self._gen("الحج 1", ["العمرة 1", "العمرة 2"]), "الحج 1")

    def test_06_empty_name_fallback(self):
        result = self._gen("", [])
        self.assertTrue(result)  # يعيد اسماً افتراضياً غير فارغ

    def test_07_whitespace_normalized(self):
        self.assertEqual(self._gen("الحج   1", ["الحج 1"]), "الحج 2")


class TestCopyProjectSettings(unittest.TestCase):
    """2. نسخ الإعدادات لمشروع جديد"""

    def test_01_invalid_source_key_rejected(self):
        result = _bridge.copy_project_settings_to_new_project("", 111)
        self.assertFalse(result.get("ok"))

    def test_02_source_defined_with_no_env_fallback(self):
        """التوكن يُقرأ من مخزن المشروع فقط — allow_env_fallback=False حرفياً."""
        self.assertIn("get_project_github_token(allow_env_fallback=False)", BRIDGE_SRC)

    def test_03_new_key_and_sequential_name(self):
        fake_settings = {
            "model": "claude-opus-5",
            "continuation": {"prompt": "تابع البناء", "mode": "custom"},
            "github": {"enabled": False},
        }
        fake_registry = mock.MagicMock()
        fake_registry.get_project_settings.return_value = fake_settings
        fake_registry.get_project_github_token.return_value = ""
        with mock.patch.object(_bridge, "ProjectRegistry", return_value=fake_registry), \
             mock.patch.object(_bridge, "get_project_identity_record", return_value={"project_name": "الحج 1"}), \
             mock.patch.object(_bridge, "list_known_projects", return_value=_fake_projects(["الحج 1"])), \
             mock.patch.object(_bridge, "finalize_new_project_setup", side_effect=lambda *a, **k: fake_settings) as fin, \
             mock.patch.object(_bridge, "upsert_project_identity") as ups:
            result = _bridge.copy_project_settings_to_new_project(
                "prj_source", 111, target_pid="proj_abc123",
            )
        self.assertTrue(result["ok"])
        self.assertTrue(result["project_key"].startswith("prj_"))
        self.assertNotEqual(result["project_key"], "prj_source")
        self.assertEqual(result["project_name"], "الحج 2")
        self.assertEqual(result["source_name"], "الحج 1")
        fin.assert_called_once()
        ups.assert_called_once()  # الـ pid موجود ➔ يسجل هوية المشروع

    def test_04_no_pid_skips_identity_upsert(self):
        fake_settings = {"model": "claude-fable-5", "continuation": {}, "github": {}}
        fake_registry = mock.MagicMock()
        fake_registry.get_project_settings.return_value = fake_settings
        fake_registry.get_project_github_token.return_value = ""
        with mock.patch.object(_bridge, "ProjectRegistry", return_value=fake_registry), \
             mock.patch.object(_bridge, "get_project_identity_record", return_value={}), \
             mock.patch.object(_bridge, "list_known_projects", return_value=[]), \
             mock.patch.object(_bridge, "finalize_new_project_setup", side_effect=lambda *a, **k: fake_settings), \
             mock.patch.object(_bridge, "upsert_project_identity") as ups:
            result = _bridge.copy_project_settings_to_new_project("prj_source", 111)
        self.assertTrue(result["ok"])
        ups.assert_not_called()

    def test_05_github_token_passed_only_when_enabled(self):
        fake_settings = {
            "model": "claude-fable-5",
            "continuation": {"prompt": "تابع"},
            "github": {"enabled": True, "repository": "o/r", "branch": "main"},
        }
        fake_registry = mock.MagicMock()
        fake_registry.get_project_settings.return_value = fake_settings
        fake_registry.get_project_github_token.return_value = "ghp_secret_token_value"
        captured = {}

        def _capture(*args, **kwargs):
            captured.update(kwargs)
            return fake_settings

        with mock.patch.object(_bridge, "ProjectRegistry", return_value=fake_registry), \
             mock.patch.object(_bridge, "get_project_identity_record", return_value={}), \
             mock.patch.object(_bridge, "list_known_projects", return_value=[]), \
             mock.patch.object(_bridge, "finalize_new_project_setup", side_effect=_capture):
            result = _bridge.copy_project_settings_to_new_project("prj_source", 111)
        self.assertTrue(result["ok"])
        self.assertEqual(captured.get("token"), "ghp_secret_token_value")
        self.assertTrue(captured.get("github_enabled"))


class TestCopySettingsKeyboard(unittest.TestCase):
    """3. لوحة اختيار المشروع المصدر"""

    def test_01_sources_as_cpysrc_buttons(self):
        with mock.patch.object(_bridge, "list_known_projects", return_value=_fake_projects(["الحج 1", "العمرة"])):
            kb = _bridge.build_copy_settings_source_keyboard(111)
        rows = kb["inline_keyboard"]
        callbacks = [btn["callback_data"] for row in rows for btn in row]
        self.assertIn("cpysrc:prj_00", callbacks)
        self.assertIn("cpysrc:prj_01", callbacks)
        self.assertIn("cmd:resume_copy_back", callbacks)
        self.assertIn("cmd:show_dashboard", callbacks)

    def test_02_empty_projects_still_has_back_row(self):
        with mock.patch.object(_bridge, "list_known_projects", return_value=[]):
            kb = _bridge.build_copy_settings_source_keyboard(111)
        callbacks = [btn["callback_data"] for row in kb["inline_keyboard"] for btn in row]
        self.assertIn("cmd:resume_copy_back", callbacks)

    def test_03_unbound_resume_keyboard_offers_copy(self):
        kb = _bridge.build_unbound_resume_keyboard()
        callbacks = [btn["callback_data"] for row in kb["inline_keyboard"] for btn in row]
        self.assertIn("cmd:resume_copy_settings", callbacks)


class TestCopiedSettingsSummary(unittest.TestCase):
    """4. ملخص الإعدادات المنسوخة"""

    def test_01_summary_mentions_source_and_new_name(self):
        result = {
            "source_name": "الحج 1",
            "project_name": "الحج 2",
            "project_key": "prj_new",
            "settings": {
                "model": "claude-opus-5",
                "continuation": {"prompt": "تابع"},
                "github": {"enabled": True, "repository": "o/r", "branch": "main", "token_present": True},
            },
        }
        text = _bridge.format_copied_settings_summary(result)
        self.assertIn("الحج 1", text)
        self.assertIn("الحج 2", text)
        self.assertIn("claude-opus-5", text)
        self.assertIn("o/r @ main", text)

    def test_02_disabled_github_reported(self):
        result = {"source_name": "س", "project_name": "س 2", "project_key": "k",
                  "settings": {"model": "claude-fable-5", "continuation": {}, "github": {"enabled": False}}}
        text = _bridge.format_copied_settings_summary(result)
        self.assertIn("غير مفعل", text)


class TestHandlersIntegration(unittest.TestCase):
    """5. تكامل الـ callbacks في handle_telegram_update"""

    def test_01_copy_settings_callback_wired(self):
        self.assertIn('elif data == "cmd:resume_copy_settings":', BRIDGE_SRC)
        self.assertIn('"action": "AWAITING_COPY_SETTINGS_SOURCE"', BRIDGE_SRC.replace("\n", ""))

    def test_02_copy_back_callback_wired(self):
        self.assertIn('elif data == "cmd:resume_copy_back":', BRIDGE_SRC)

    def test_03_cpysrc_callback_invokes_copy(self):
        self.assertIn('elif data.startswith("cpysrc:"):', BRIDGE_SRC)
        self.assertIn("copy_project_settings_to_new_project(source_key, chat_id", BRIDGE_SRC)

    def test_04_success_transitions_to_cont_prompt(self):
        """بعد النسخ الناجح: الحالة تتحول لـ AWAITING_CONT_PROMPT بالمفتاح الجديد."""
        idx = BRIDGE_SRC.index('elif data.startswith("cpysrc:"):')
        block = BRIDGE_SRC[idx:idx + 2200]
        self.assertIn('"action": "AWAITING_CONT_PROMPT"', block)
        self.assertIn("format_copied_settings_summary(result)", block)

    def test_05_guard_requires_unbound_decision_state(self):
        idx = BRIDGE_SRC.index('elif data == "cmd:resume_copy_settings":')
        block = BRIDGE_SRC[idx:idx + 1200]
        self.assertIn('"AWAITING_UNBOUND_RESUME_DECISION"', block)


class TestP19VersionBump(unittest.TestCase):
    """6. بانر وإصدار 01.31"""

    def test_01_banner_and_version(self):
        head = BRIDGE_SRC[:1800]
        self.assertIn("01.33_telegram_gen_bridge.py", head)
        self.assertIn("P19", head)
        self.assertIn('BUILD_VERSION = "01.33"', BRIDGE_SRC)
        self.assertIn('BUILD_PARENT_BASELINE = "01.30"', BRIDGE_SRC)
        self.assertIn('BUILD_PARENT_BASELINE_SHA256 = "0130_p19_copy_settings_baseline"', BRIDGE_SRC)

    def test_02_scripts_reference_0130(self):
        for rel in ("scripts/hadith_sijil.py", "scripts/rebuild_refactor.py"):
            src = (webapp_dir / rel).read_text(encoding="utf-8")
            self.assertIn("01.33_telegram_gen_bridge.py", src, rel)
            self.assertNotIn("01.30_telegram_gen_bridge.py", src, rel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
