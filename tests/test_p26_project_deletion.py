#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p26_project_deletion.py
==================================
🗑️ [P26] حراسة ميزة «حذف المشروع وتأكيد الحذف التفاعلي والحذف الذري الشامل»
(Interactive Project Deletion & Atomic Cleanup):

1. واجهة المستخدم: زر حذف أحمر (danger) في لوحة تفاصيل المشروع كصف مستقل
   (إضافة وليس استبدالاً لزر إلغاء البناء P25) + كيبورد تأكيد بخطوتي أمان
   (نعم أحمر / تراجع أخضر) + كيبورد شاشة النجاح.
2. فحص الحماية: منع حذف مشروع له بناء نشط الآن عبر _ACTIVE_CANCEL_EVENTS.
3. الحذف الذري: تنظيف registry.json (القيد + كل pid aliases تحت القفل)
   ثم projects_tree.json ثم مجلد القرص project_registry/<key>/ بالكامل.
4. سلامة الجيران: حذف مشروع لا يمس أي مشروع آخر في الفهرس أو الشجرة أو القرص.
5. عقود التكامل في المصدر: معالج callbacks يفصل pdel_prompt/abort/exec
   ككتلة مبكرة معزولة، والتأكيد In-Place عبر edit_telegram_message_text.
"""

import json
import re
import sys
import shutil
import pathlib
import tempfile
import threading
import unittest
import importlib.util

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p26", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)

VALID_PID_A = "aaaaaaaa-1111-2222-3333-444444444444"
VALID_PID_B = "bbbbbbbb-1111-2222-3333-444444444444"
VALID_PID_C = "cccccccc-1111-2222-3333-444444444444"


def _extract_texts(keyboard: dict) -> list[str]:
    return [btn.get("text", "") for row in keyboard.get("inline_keyboard", []) for btn in row]


def _extract_callbacks(keyboard: dict) -> list[str]:
    return [btn.get("callback_data", "") for row in keyboard.get("inline_keyboard", []) for btn in row if btn.get("callback_data")]


class _IsolatedRegistryMixin:
    """عزل كامل: تحويل مسارات السجل والشجرة لمجلد مؤقت قبل كل اختبار"""

    def setUp(self):
        self._tmp = pathlib.Path(tempfile.mkdtemp(prefix="p26_test_"))
        self._orig_home = _bridge.PROJECT_REGISTRY_HOME
        self._orig_index = _bridge.PROJECT_REGISTRY_INDEX_FILE
        self._orig_tree = _bridge.PROJECTS_TREE_FILE
        _bridge.PROJECT_REGISTRY_HOME = self._tmp / "project_registry"
        _bridge.PROJECT_REGISTRY_INDEX_FILE = _bridge.PROJECT_REGISTRY_HOME / "registry.json"
        _bridge.PROJECTS_TREE_FILE = self._tmp / "projects_tree.json"
        _bridge.PROJECT_REGISTRY_HOME.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        _bridge.PROJECT_REGISTRY_HOME = self._orig_home
        _bridge.PROJECT_REGISTRY_INDEX_FILE = self._orig_index
        _bridge.PROJECTS_TREE_FILE = self._orig_tree
        shutil.rmtree(self._tmp, ignore_errors=True)

    # ── أدوات تجهيز بيئة الاختبار ──
    def _seed_project(self, key: str, root_pid: str = "", name: str = "", chat_id: int = 777) -> dict:
        record = _bridge.upsert_project_identity(
            key, root_pid=root_pid or None, project_name=name or key, chat_id=chat_id, status="COMPLETED"
        )
        project_dir = _bridge.PROJECT_REGISTRY_HOME / key
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "manifest.json").write_text(json.dumps({"key": key}), encoding="utf-8")
        (project_dir / "checkpoints").mkdir(exist_ok=True)
        (project_dir / "checkpoints" / "cp1.txt").write_text("x", encoding="utf-8")
        return record

    def _seed_tree(self, root_pid: str, child_pid: str):
        self.assertTrue(_bridge.save_project_branch(root_pid, child_pid, title="فرع اختبار"))

    def _read_index(self) -> dict:
        return json.loads(_bridge.PROJECT_REGISTRY_INDEX_FILE.read_text(encoding="utf-8"))


class TestDeleteKeyboards(unittest.TestCase):
    """1. واجهة المستخدم — الأزرار والأنماط والـ callbacks"""

    def test_01_details_keyboard_has_delete_button(self):
        kb = _bridge.build_current_project_keyboard("proj_ui_test")
        callbacks = _extract_callbacks(kb)
        self.assertIn("pdel_prompt:proj_ui_test", callbacks)

    def test_02_delete_button_is_danger_and_own_row(self):
        kb = _bridge.build_current_project_keyboard("proj_ui_test")
        delete_rows = [
            row for row in kb["inline_keyboard"]
            if any(str(btn.get("callback_data", "")).startswith("pdel_prompt:") for btn in row)
        ]
        self.assertEqual(len(delete_rows), 1)
        # صف مستقل بزر واحد فقط — منع الضغط الخاطئ بجوار أزرار أخرى
        self.assertEqual(len(delete_rows[0]), 1)
        self.assertEqual(delete_rows[0][0].get("style"), "danger")
        self.assertIn("🗑️", delete_rows[0][0].get("text", ""))

    def test_03_p25_cancel_button_still_present(self):
        # تعديل السلامة المعتمد: زر إلغاء البناء (P25/pctl) يبقى كما هو — إضافة لا استبدال
        kb = _bridge.build_current_project_keyboard("proj_ui_test")
        callbacks = _extract_callbacks(kb)
        self.assertIn("pctl:cancel:proj_ui_test", callbacks)

    def test_04_confirm_keyboard_two_step_safety(self):
        kb = _bridge.build_project_delete_confirm_keyboard("proj_x")
        callbacks = _extract_callbacks(kb)
        self.assertIn("pdel_exec:proj_x", callbacks)
        self.assertIn("pdel_abort:proj_x", callbacks)
        styles = {btn.get("callback_data", ""): btn.get("style") for row in kb["inline_keyboard"] for btn in row}
        self.assertEqual(styles.get("pdel_exec:proj_x"), "danger")
        self.assertEqual(styles.get("pdel_abort:proj_x"), "success")

    def test_05_callback_data_within_telegram_limit(self):
        # callback_data محدود بـ 64 بايت — مفتاح المشروع حتى 80 حرفاً قد يتجاوز؛
        # نضمن هنا أن البادئات نفسها قصيرة والمفاتيح الواقعية (≤ 50) آمنة
        realistic_key = "a" * 50
        for prefix in ("pdel_prompt", "pdel_exec", "pdel_abort"):
            self.assertLessEqual(len(f"{prefix}:{realistic_key}".encode("utf-8")), 64)

    def test_06_deleted_keyboard_has_next_actions(self):
        kb = _bridge.build_project_deleted_keyboard()
        callbacks = _extract_callbacks(kb)
        self.assertIn("cmd:list_projects", callbacks)
        self.assertIn("cmd:new_proj", callbacks)

    def test_07_confirm_text_shows_name_and_key(self):
        text = _bridge.render_project_delete_confirm_text("proj_warn_test")
        self.assertIn("proj_warn_test", text)
        self.assertIn("تأكيد حذف المشروع", text)
        self.assertIn("لا يمكن التراجع", text)


class TestRunningProtection(unittest.TestCase):
    """2. فحص الحماية — منع حذف مشروع له بناء نشط"""

    def setUp(self):
        self.token = _bridge.new_cancel_token()

    def tearDown(self):
        _bridge.unregister_cancel_event(self.token)

    def test_01_inactive_project_not_flagged(self):
        self.assertFalse(_bridge.is_project_build_active("proj_idle_p26"))

    def test_02_active_build_is_flagged(self):
        _bridge.register_cancel_event(self.token, project_key="proj_busy_p26", chat_id=1)
        self.assertTrue(_bridge.is_project_build_active("proj_busy_p26"))

    def test_03_cancelled_build_not_flagged(self):
        _bridge.register_cancel_event(self.token, project_key="proj_busy_p26", chat_id=1)
        _bridge.trigger_cancel(self.token)
        self.assertFalse(_bridge.is_project_build_active("proj_busy_p26"))

    def test_04_unregistered_build_not_flagged(self):
        _bridge.register_cancel_event(self.token, project_key="proj_busy_p26", chat_id=1)
        _bridge.unregister_cancel_event(self.token)
        self.assertFalse(_bridge.is_project_build_active("proj_busy_p26"))

    def test_05_empty_key_never_flagged(self):
        self.assertFalse(_bridge.is_project_build_active(""))
        self.assertFalse(_bridge.is_project_build_active(None))


class TestAtomicDeletion(_IsolatedRegistryMixin, unittest.TestCase):
    """3. الحذف الذري الشامل — فهرس + شجرة + قرص"""

    def test_01_full_deletion_happy_path(self):
        self._seed_project("proj_del_a", root_pid=VALID_PID_A, name="مشروع للحذف")
        self._seed_tree(VALID_PID_A, VALID_PID_B)
        outcome = _bridge.delete_project_atomically("proj_del_a")
        self.assertTrue(outcome["ok"])
        self.assertEqual(outcome["project_name"], "مشروع للحذف")
        self.assertTrue(outcome["index_removed"])
        self.assertGreaterEqual(outcome["aliases_removed"], 1)
        self.assertEqual(outcome["tree_removed"], 1)
        self.assertTrue(outcome["disk_removed"])
        # التحقق الميداني: لا أثر على القرص ولا في الفهارس
        self.assertFalse((_bridge.PROJECT_REGISTRY_HOME / "proj_del_a").exists())
        index = self._read_index()
        self.assertNotIn("proj_del_a", index["projects"])
        self.assertNotIn(VALID_PID_A, index["pid_to_key"])
        tree = json.loads(_bridge.PROJECTS_TREE_FILE.read_text(encoding="utf-8"))
        self.assertNotIn(VALID_PID_A, tree)

    def test_02_identity_record_gone_after_delete(self):
        self._seed_project("proj_del_b", root_pid=VALID_PID_B)
        _bridge.delete_project_atomically("proj_del_b")
        self.assertIsNone(_bridge.get_project_identity_record("proj_del_b"))
        self.assertIsNone(_bridge.lookup_project_key_for_locator(VALID_PID_B))

    def test_03_active_build_blocks_deletion(self):
        self._seed_project("proj_del_busy", root_pid=VALID_PID_A)
        token = _bridge.new_cancel_token()
        _bridge.register_cancel_event(token, project_key="proj_del_busy", chat_id=1)
        try:
            outcome = _bridge.delete_project_atomically("proj_del_busy")
            self.assertFalse(outcome["ok"])
            self.assertEqual(outcome["reason"], "PROJECT_BUILD_ACTIVE")
            # صفر تعديل: المجلد والقيد سليمان تماماً
            self.assertTrue((_bridge.PROJECT_REGISTRY_HOME / "proj_del_busy").exists())
            self.assertIsNotNone(_bridge.get_project_identity_record("proj_del_busy"))
        finally:
            _bridge.unregister_cancel_event(token)

    def test_04_deletion_allowed_after_build_finishes(self):
        self._seed_project("proj_del_freed", root_pid=VALID_PID_A)
        token = _bridge.new_cancel_token()
        _bridge.register_cancel_event(token, project_key="proj_del_freed", chat_id=1)
        _bridge.unregister_cancel_event(token)
        outcome = _bridge.delete_project_atomically("proj_del_freed")
        self.assertTrue(outcome["ok"])

    def test_05_missing_project_reports_not_found(self):
        outcome = _bridge.delete_project_atomically("proj_ghost_404")
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["reason"], "PROJECT_NOT_FOUND")

    def test_06_empty_key_rejected(self):
        outcome = _bridge.delete_project_atomically("")
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["reason"], "PROJECT_KEY_MISSING")

    def test_07_disk_only_project_still_deleted(self):
        # مجلد يتيم على القرص بلا قيد فهرس — يجب حذفه بنجاح
        orphan_dir = _bridge.PROJECT_REGISTRY_HOME / "proj_orphan_disk"
        orphan_dir.mkdir(parents=True)
        (orphan_dir / "manifest.json").write_text("{}", encoding="utf-8")
        outcome = _bridge.delete_project_atomically("proj_orphan_disk")
        self.assertTrue(outcome["ok"])
        self.assertTrue(outcome["disk_removed"])
        self.assertFalse(orphan_dir.exists())

    def test_08_all_pid_aliases_purged(self):
        # قيد بـ root + latest مختلفين — كلا الـ aliases يجب مسحهما
        _bridge.upsert_project_identity("proj_two_pids", root_pid=VALID_PID_A, latest_pid=VALID_PID_C, chat_id=1)
        (_bridge.PROJECT_REGISTRY_HOME / "proj_two_pids").mkdir(parents=True, exist_ok=True)
        outcome = _bridge.delete_project_atomically("proj_two_pids")
        self.assertTrue(outcome["ok"])
        self.assertEqual(outcome["aliases_removed"], 2)
        index = self._read_index()
        self.assertNotIn(VALID_PID_A, index["pid_to_key"])
        self.assertNotIn(VALID_PID_C, index["pid_to_key"])

    def test_09_no_tree_file_is_safe(self):
        # لا يوجد projects_tree.json إطلاقاً — الحذف يكمل بدون أخطاء
        self._seed_project("proj_no_tree", root_pid=VALID_PID_A)
        self.assertFalse(_bridge.PROJECTS_TREE_FILE.exists())
        outcome = _bridge.delete_project_atomically("proj_no_tree")
        self.assertTrue(outcome["ok"])
        self.assertEqual(outcome["tree_removed"], 0)

    def test_10_project_without_pid_skips_tree_safely(self):
        # قيد بلا أي pid (لم يُنشأ مشروع Genspark بعد) — الشجرة تُتخطى بأمان
        self._seed_project("proj_no_pid")
        outcome = _bridge.delete_project_atomically("proj_no_pid")
        self.assertTrue(outcome["ok"])
        self.assertEqual(outcome["tree_removed"], 0)


class TestNeighborSafety(_IsolatedRegistryMixin, unittest.TestCase):
    """4. سلامة الجيران — حذف مشروع لا يمس مشروعاً آخر"""

    def test_01_sibling_untouched_everywhere(self):
        self._seed_project("proj_victim", root_pid=VALID_PID_A, name="الضحية")
        self._seed_project("proj_survivor", root_pid=VALID_PID_B, name="الناجي")
        self._seed_tree(VALID_PID_A, VALID_PID_C)
        self._seed_tree(VALID_PID_B, VALID_PID_C)
        outcome = _bridge.delete_project_atomically("proj_victim")
        self.assertTrue(outcome["ok"])
        # الناجي سليم: فهرس + alias + شجرة + قرص
        index = self._read_index()
        self.assertIn("proj_survivor", index["projects"])
        self.assertEqual(index["pid_to_key"].get(VALID_PID_B), "proj_survivor")
        tree = json.loads(_bridge.PROJECTS_TREE_FILE.read_text(encoding="utf-8"))
        self.assertIn(VALID_PID_B, tree)
        self.assertNotIn(VALID_PID_A, tree)
        survivor_dir = _bridge.PROJECT_REGISTRY_HOME / "proj_survivor"
        self.assertTrue(survivor_dir.exists())
        self.assertTrue((survivor_dir / "manifest.json").exists())

    def test_02_registry_index_file_survives_deletion(self):
        # حذف مشروع لا يحذف ملف الفهرس نفسه ولا يفسده
        self._seed_project("proj_solo", root_pid=VALID_PID_A)
        _bridge.delete_project_atomically("proj_solo")
        self.assertTrue(_bridge.PROJECT_REGISTRY_INDEX_FILE.exists())
        index = self._read_index()
        self.assertEqual(index.get("schema_version"), _bridge.REGISTRY_INDEX_SCHEMA_VERSION)

    def test_03_delete_is_idempotent(self):
        self._seed_project("proj_twice", root_pid=VALID_PID_A)
        first = _bridge.delete_project_atomically("proj_twice")
        second = _bridge.delete_project_atomically("proj_twice")
        self.assertTrue(first["ok"])
        self.assertFalse(second["ok"])
        self.assertEqual(second["reason"], "PROJECT_NOT_FOUND")


class TestSourceContracts(unittest.TestCase):
    """5. عقود التكامل في المصدر — بدون تشغيل تليجرام فعلي"""

    def test_01_pdel_block_isolated_and_early(self):
        # كتلة pdel معزولة بنمط startswith tuple مثل P25 تماماً
        self.assertIn('data.startswith(("pdel_prompt:", "pdel_abort:", "pdel_exec:"))', BRIDGE_SRC)

    def test_02_pdel_block_before_main_chain(self):
        pdel_pos = BRIDGE_SRC.index('data.startswith(("pdel_prompt:')
        chain_pos = BRIDGE_SRC.index('if data == "cmd:show_dashboard"')
        self.assertLess(pdel_pos, chain_pos)

    def test_03_confirmation_is_in_place_edit(self):
        # التأكيد In-Place: داخل كتلة pdel يوجد edit_telegram_message_text
        block_start = BRIDGE_SRC.index('data.startswith(("pdel_prompt:')
        block_end = BRIDGE_SRC.index('if data == "cmd:show_dashboard"')
        block = BRIDGE_SRC[block_start:block_end]
        self.assertIn("edit_telegram_message_text", block)
        self.assertIn("render_project_delete_confirm_text", block)
        self.assertIn("build_project_delete_confirm_keyboard", block)

    def test_04_exec_calls_atomic_deletion(self):
        block_start = BRIDGE_SRC.index('data.startswith(("pdel_prompt:')
        block_end = BRIDGE_SRC.index('if data == "cmd:show_dashboard"')
        block = BRIDGE_SRC[block_start:block_end]
        self.assertIn("delete_project_atomically(project_key)", block)
        self.assertIn("PROJECT_BUILD_ACTIVE", block)

    def test_05_abort_restores_details_screen(self):
        block_start = BRIDGE_SRC.index('data.startswith(("pdel_prompt:')
        block_end = BRIDGE_SRC.index('if data == "cmd:show_dashboard"')
        block = BRIDGE_SRC[block_start:block_end]
        self.assertIn("render_project_status_text(project_key)", block)
        self.assertIn("build_current_project_keyboard(project_key)", block)

    def test_06_index_cleanup_under_registry_lock(self):
        # الأسماء الفعلية المعتمدة: REGISTRY_INDEX_LOCK وليس _REGISTRY_LOCK
        fn_start = BRIDGE_SRC.index("def delete_project_atomically(")
        fn_end = BRIDGE_SRC.index("def build_genspark_viewer_url(")
        fn_src = BRIDGE_SRC[fn_start:fn_end]
        self.assertIn("with REGISTRY_INDEX_LOCK:", fn_src)
        self.assertIn("shutil.rmtree(project_dir)", fn_src)
        self.assertIn("is_project_build_active(key)", fn_src)

    def test_07_project_key_sanitized_in_handler(self):
        block_start = BRIDGE_SRC.index('data.startswith(("pdel_prompt:')
        block_end = BRIDGE_SRC.index('if data == "cmd:show_dashboard"')
        block = BRIDGE_SRC[block_start:block_end]
        self.assertIn('re.sub(r"[^A-Za-z0-9_-]", "_"', block)

    def test_08_danger_style_is_allowed_value(self):
        self.assertIn("danger", _bridge.ALLOWED_BUTTON_STYLES)
        self.assertIn("success", _bridge.ALLOWED_BUTTON_STYLES)


if __name__ == "__main__":
    unittest.main(verbosity=2)
