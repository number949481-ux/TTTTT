#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p23_shared_paths.py
==============================
🔎 [P23] حراسة البحث الهرمي للملفات المشتركة (Shared Secrets Auto-Discovery):

1. resolve_shared_path: أولوية محلية ➔ الفولدر الأب ➔ المحلي (للإنشاء).
2. load_bot_token يقرأ التوكن عبر resolve_shared_path (محلي ثم الأب).
3. PROJECT_REGISTRY_HOME و PROJECTS_TREE_FILE يمران عبر resolve_shared_path.
4. get_accounts_file_path يفحص المسار الموحد أولاً ثم fallback القديم.
5. Zero Breaking Changes: النسخ بملفاتها المحلية تلتقط المحلي دائماً.
6. القفل الثاني: يافطة القاعدة المركزية موجودة في AGENTS.md و GEMINI.md.
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

BRIDGE_PATH = webapp_dir / "01.31_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p23", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)


class TestResolveSharedPath(unittest.TestCase):
    """عقد الدالة resolve_shared_path — البحث الهرمي محلي ➔ أب ➔ محلي"""

    def test_01_function_exists_and_returns_path(self):
        self.assertTrue(hasattr(_bridge, "resolve_shared_path"))
        result = _bridge.resolve_shared_path("zzz_p23_missing_everywhere")
        self.assertIsInstance(result, pathlib.Path)

    def test_02_local_file_wins(self):
        """أولوية محلية: الملف الموجود جنب النسخة يُستخدم حتى لو الأب فيه نسخة"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp)
            local_dir = parent / "copy_a"
            local_dir.mkdir()
            (parent / "secret.txt").write_text("parent", encoding="utf-8")
            (local_dir / "secret.txt").write_text("local", encoding="utf-8")
            with mock.patch.object(_bridge, "SCRIPT_DIR", local_dir):
                got = _bridge.resolve_shared_path("secret.txt")
            self.assertEqual(got, local_dir / "secret.txt")
            self.assertEqual(got.read_text(encoding="utf-8"), "local")

    def test_03_parent_fallback_when_local_missing(self):
        """لو الملف مش موجود محلياً يُلقط من الفولدر الأب تلقائياً"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp)
            local_dir = parent / "copy_b"
            local_dir.mkdir()
            (parent / "secret.txt").write_text("parent", encoding="utf-8")
            with mock.patch.object(_bridge, "SCRIPT_DIR", local_dir):
                got = _bridge.resolve_shared_path("secret.txt")
            self.assertEqual(got, parent / "secret.txt")
            self.assertEqual(got.read_text(encoding="utf-8"), "parent")

    def test_04_missing_everywhere_returns_local_for_creation(self):
        """لو غير موجود في الاثنين يرجع المسار المحلي (عشان الإنشاء الجديد)"""
        with tempfile.TemporaryDirectory() as tmp:
            local_dir = pathlib.Path(tmp) / "copy_c"
            local_dir.mkdir()
            with mock.patch.object(_bridge, "SCRIPT_DIR", local_dir):
                got = _bridge.resolve_shared_path("never_exists.json")
            self.assertEqual(got, local_dir / "never_exists.json")

    def test_05_works_for_directories_too(self):
        """يدعم المجلدات (project_registry) وليس الملفات فقط"""
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp)
            local_dir = parent / "copy_d"
            local_dir.mkdir()
            (parent / "project_registry").mkdir()
            with mock.patch.object(_bridge, "SCRIPT_DIR", local_dir):
                got = _bridge.resolve_shared_path("project_registry")
            self.assertEqual(got, parent / "project_registry")


class TestSharedPathWiring(unittest.TestCase):
    """التحقق أن مواضع T2/T3/T4 فعلاً موصولة بـ resolve_shared_path في المصدر"""

    def test_01_token_uses_resolver(self):
        self.assertIn(
            'token_file = resolve_shared_path("telegram_bot_token.txt")', BRIDGE_SRC
        )
        self.assertNotIn('token_file = SCRIPT_DIR / "telegram_bot_token.txt"', BRIDGE_SRC)

    def test_02_registry_home_uses_resolver(self):
        self.assertIn(
            'PROJECT_REGISTRY_HOME = resolve_shared_path("project_registry")', BRIDGE_SRC
        )

    def test_03_projects_tree_uses_resolver(self):
        self.assertIn(
            'PROJECTS_TREE_FILE = resolve_shared_path("projects_tree.json")', BRIDGE_SRC
        )

    def test_04_accounts_candidates_use_resolver_first(self):
        """المرشح الأول في get_accounts_file_path هو المسار الموحد"""
        self.assertIn(
            'resolve_shared_path("accounts_genspark.json")', BRIDGE_SRC
        )
        # fallback القديم للأب ما زال موجوداً (توافق خلفي)
        self.assertIn('SCRIPT_DIR.parent / "accounts_genspark.json"', BRIDGE_SRC)

    def test_05_registry_index_derived_from_home(self):
        """registry.json يظل مشتقاً من PROJECT_REGISTRY_HOME (فيرث المركزية)"""
        self.assertIn(
            'PROJECT_REGISTRY_INDEX_FILE = PROJECT_REGISTRY_HOME / "registry.json"',
            BRIDGE_SRC,
        )

    def test_06_resolver_defined_before_first_use(self):
        """الدالة معرفة قبل أول استخدام (load_bot_token)"""
        def_pos = BRIDGE_SRC.index("def resolve_shared_path(")
        use_pos = BRIDGE_SRC.index('resolve_shared_path("telegram_bot_token.txt")')
        self.assertLess(def_pos, use_pos)


class TestLoadBotTokenHierarchy(unittest.TestCase):
    """عقد load_bot_token: env أولاً ➔ ملف محلي ➔ ملف الأب"""

    def test_01_env_var_wins(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "env-token-123"}):
            self.assertEqual(_bridge.load_bot_token(), "env-token-123")

    def test_02_parent_token_file_used_when_local_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp)
            local_dir = parent / "copy_x"
            local_dir.mkdir()
            (parent / "telegram_bot_token.txt").write_text(
                "parent-token-999", encoding="utf-8"
            )
            with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}), \
                 mock.patch.object(_bridge, "SCRIPT_DIR", local_dir):
                self.assertEqual(_bridge.load_bot_token(), "parent-token-999")

    def test_03_local_token_file_wins_over_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp)
            local_dir = parent / "copy_y"
            local_dir.mkdir()
            (parent / "telegram_bot_token.txt").write_text("parent-token", encoding="utf-8")
            (local_dir / "telegram_bot_token.txt").write_text("local-token", encoding="utf-8")
            with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}), \
                 mock.patch.object(_bridge, "SCRIPT_DIR", local_dir):
                self.assertEqual(_bridge.load_bot_token(), "local-token")


class TestCentralRuleSignage(unittest.TestCase):
    """القفل الثاني [P23]: يافطة القاعدة المركزية في AGENTS.md و GEMINI.md"""

    def test_01_agents_md_exists_with_rule(self):
        agents = webapp_dir / "AGENTS.md"
        self.assertTrue(agents.exists(), "AGENTS.md مفقود")
        src = agents.read_text(encoding="utf-8")
        for needle in ("قاعدة مركزية", "resolve_shared_path", "telegram_bot_token.txt",
                       "accounts_genspark.json", "project_registry"):
            self.assertIn(needle, src)

    def test_02_gemini_md_exists_with_rule(self):
        gemini = webapp_dir / "GEMINI.md"
        self.assertTrue(gemini.exists(), "GEMINI.md مفقود")
        src = gemini.read_text(encoding="utf-8")
        for needle in ("قاعدة مركزية", "resolve_shared_path", "AGENTS.md"):
            self.assertIn(needle, src)

    def test_03_no_hardcoded_bot_token(self):
        """ممنوع الـ hardcode: لا يوجد توكن تيليجرام حرفي في المصدر"""
        import re
        self.assertIsNone(re.search(r"\d{8,10}:[A-Za-z0-9_-]{35}", BRIDGE_SRC))


if __name__ == "__main__":
    unittest.main()
