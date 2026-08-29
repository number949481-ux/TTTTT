#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p27_projects_pagination.py
=====================================
📄 [P27] حراسة ميزة «تصفح المشاريع بنظام الصفحات» (Projects List Pagination):

1. الثابت المركزي: PROJECTS_PER_PAGE = 20 (قرار المالك الصريح — 20/صفحة).
2. حساب الحدود: compute_projects_page_bounds آمنة تماماً ضد Out-of-Bounds
   (صفحة سالبة/صفر/نص/أكبر من الأخيرة ➔ قصّ لأقرب صفحة صالحة، صفر Crash).
3. الكيبورد: build_projects_page_keyboard — صفوف المشاريع بنفس عقود proj:/pview:
   القائمة + صف تنقل [⬅️ السابقة][📄 N/X][التالية ➡️] بأزرار حواف ذكية
   + صف [🚀 مشروع جديد][🏠 رجوع للوحة التحكم] دائماً.
4. النص: render_projects_page_text — عداد إجمالي + موضع صفحة + رسالة صفر مشاريع.
5. عدم الانحدار: لوحة التحكم الرئيسية تبقى معاينة سريعة (أحدث 3) كما هي.
6. عقود التكامل في المصدر: إصلاح الزر الميت cmd:list_projects بمعالج فعلي +
   plist:page: يعدّل نفس الرسالة (edit_telegram_message_text) + plist:noop للعداد.
"""

import re
import sys
import shutil
import pathlib
import tempfile
import unittest
import importlib.util

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p27", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)

CHAT_ID = 777


def _extract_texts(keyboard: dict) -> list[str]:
    return [btn.get("text", "") for row in keyboard.get("inline_keyboard", []) for btn in row]


def _extract_callbacks(keyboard: dict) -> list[str]:
    return [btn.get("callback_data", "") for row in keyboard.get("inline_keyboard", []) for btn in row if btn.get("callback_data")]


class _IsolatedRegistryMixin:
    """عزل كامل: تحويل مسارات السجل والشجرة لمجلد مؤقت قبل كل اختبار"""

    def setUp(self):
        self._tmp = pathlib.Path(tempfile.mkdtemp(prefix="p27_test_"))
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

    def _seed_projects(self, count: int, chat_id: int = CHAT_ID) -> list[str]:
        keys = []
        for i in range(count):
            key = f"prj_p27_c{chat_id}_{i:04d}"
            _bridge.upsert_project_identity(
                key, project_name=f"مشروع {i:04d}", chat_id=chat_id, status="COMPLETED"
            )
            keys.append(key)
        return keys


# ══════════════ 1) الثابت المركزي ══════════════

class TestPaginationConstant(unittest.TestCase):
    def test_projects_per_page_is_20(self):
        """قرار المالك الصريح: 20 مشروعاً في الصفحة"""
        self.assertEqual(_bridge.PROJECTS_PER_PAGE, 20)

    def test_constant_defined_once_in_source(self):
        """الثابت المركزي يُعرَّف مرة واحدة فقط (تغييره لاحقاً = سطر واحد)"""
        self.assertEqual(len(re.findall(r"^PROJECTS_PER_PAGE\s*=", BRIDGE_SRC, re.MULTILINE)), 1)


# ══════════════ 2) حساب الحدود Out-of-Bounds Safe ══════════════

class TestComputePageBounds(unittest.TestCase):
    def test_zero_projects_single_page(self):
        self.assertEqual(_bridge.compute_projects_page_bounds(0, 1), (1, 1, 0))

    def test_exactly_one_page_boundary(self):
        """20 مشروعاً = صفحة واحدة بالضبط"""
        self.assertEqual(_bridge.compute_projects_page_bounds(20, 1), (1, 1, 0))

    def test_21_projects_two_pages(self):
        """21 مشروعاً = صفحتان، الثانية تبدأ من index 20"""
        self.assertEqual(_bridge.compute_projects_page_bounds(21, 2), (2, 2, 20))

    def test_47_projects_three_pages(self):
        self.assertEqual(_bridge.compute_projects_page_bounds(47, 3), (3, 3, 40))

    def test_100_projects_five_pages(self):
        self.assertEqual(_bridge.compute_projects_page_bounds(100, 5), (5, 5, 80))

    def test_page_below_one_clamped(self):
        """صفحة 0 أو سالبة ➔ قصّ للصفحة 1"""
        self.assertEqual(_bridge.compute_projects_page_bounds(50, 0)[0], 1)
        self.assertEqual(_bridge.compute_projects_page_bounds(50, -7)[0], 1)

    def test_page_beyond_last_clamped(self):
        """صفحة أكبر من الأخيرة ➔ قصّ للصفحة الأخيرة (صفر Crash)"""
        self.assertEqual(_bridge.compute_projects_page_bounds(47, 999), (3, 3, 40))

    def test_non_numeric_page_falls_back_to_first(self):
        """توكن تالف (نص/None) ➔ الصفحة 1 بلا استثناء"""
        self.assertEqual(_bridge.compute_projects_page_bounds(50, "abc")[0], 1)
        self.assertEqual(_bridge.compute_projects_page_bounds(50, None)[0], 1)

    def test_numeric_string_page_accepted(self):
        """التوكن يصل من الـ callback كنص رقمي — يُقبل"""
        self.assertEqual(_bridge.compute_projects_page_bounds(50, "2"), (2, 3, 20))


# ══════════════ 3) كيبورد صفحة المشاريع ══════════════

class TestProjectsPageKeyboard(_IsolatedRegistryMixin, unittest.TestCase):
    def test_empty_registry_shows_actions_only(self):
        """0 مشاريع: لا صفوف مشاريع ولا تنقل — فقط [مشروع جديد][رجوع]"""
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=1)
        callbacks = _extract_callbacks(kb)
        self.assertIn("cmd:new_proj", callbacks)
        self.assertIn("cmd:show_dashboard", callbacks)
        self.assertFalse([c for c in callbacks if c.startswith(("proj:", "pview:", "plist:"))])

    def test_single_page_has_no_nav_row(self):
        """≤20 مشروعاً = صفحة واحدة بلا أي أزرار تقليب"""
        self._seed_projects(5)
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=1)
        callbacks = _extract_callbacks(kb)
        self.assertEqual(len([c for c in callbacks if c.startswith("proj:")]), 5)
        self.assertFalse([c for c in callbacks if c.startswith("plist:")])

    def test_full_page_of_20_projects(self):
        """20 مشروعاً بالضبط = 20 صفاً بلا تنقل"""
        self._seed_projects(20)
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=1)
        callbacks = _extract_callbacks(kb)
        self.assertEqual(len([c for c in callbacks if c.startswith("proj:")]), 20)
        self.assertFalse([c for c in callbacks if c.startswith("plist:")])

    def test_first_page_has_next_but_no_prev(self):
        """الصفحة الأولى: زر التالية موجود، زر السابقة محذوف"""
        self._seed_projects(21)
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=1)
        callbacks = _extract_callbacks(kb)
        self.assertIn("plist:page:2", callbacks)
        self.assertNotIn("plist:page:0", callbacks)
        self.assertFalse([t for t in _extract_texts(kb) if "السابقة" in t])

    def test_last_page_has_prev_but_no_next(self):
        """الصفحة الأخيرة: زر السابقة موجود، زر التالية محذوف"""
        self._seed_projects(21)
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=2)
        callbacks = _extract_callbacks(kb)
        self.assertIn("plist:page:1", callbacks)
        self.assertNotIn("plist:page:3", callbacks)
        self.assertFalse([t for t in _extract_texts(kb) if "التالية" in t])
        self.assertEqual(len([c for c in callbacks if c.startswith("proj:")]), 1)

    def test_middle_page_has_both_nav_buttons(self):
        """صفحة وسطى (47 مشروعاً ➔ صفحة 2 من 3): سابقة وتالية معاً + عداد"""
        self._seed_projects(47)
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=2)
        callbacks = _extract_callbacks(kb)
        self.assertIn("plist:page:1", callbacks)
        self.assertIn("plist:page:3", callbacks)
        self.assertIn("plist:noop", callbacks)
        self.assertEqual(len([c for c in callbacks if c.startswith("proj:")]), 20)

    def test_counter_button_shows_position(self):
        """زر العداد يعرض «📄 2 / 3» ويحمل plist:noop"""
        self._seed_projects(47)
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=2)
        counter = [b for row in kb["inline_keyboard"] for b in row if b.get("callback_data") == "plist:noop"]
        self.assertEqual(len(counter), 1)
        self.assertIn("2 / 3", counter[0]["text"])

    def test_out_of_bounds_page_renders_last_page(self):
        """صفحة 999 على 21 مشروعاً ➔ تُعرض الصفحة الأخيرة بلا Crash"""
        self._seed_projects(21)
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=999)
        callbacks = _extract_callbacks(kb)
        self.assertEqual(len([c for c in callbacks if c.startswith("proj:")]), 1)
        self.assertIn("plist:page:1", callbacks)

    def test_project_rows_reuse_existing_contracts(self):
        """صفوف المشاريع تستخدم نفس عقود proj:/pview: القائمة (صفر تغيير على تدفق الاختيار)"""
        keys = self._seed_projects(3)
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=1)
        callbacks = _extract_callbacks(kb)
        for key in keys:
            self.assertIn(f"proj:{key}", callbacks)
            self.assertIn(f"pview:{key}", callbacks)

    def test_projects_ordered_newest_first(self):
        """أحدث مشروع (آخر upsert) يظهر أولاً في الصفحة الأولى"""
        keys = self._seed_projects(3)
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=1)
        proj_callbacks = [c for c in _extract_callbacks(kb) if c.startswith("proj:")]
        self.assertEqual(proj_callbacks[0], f"proj:{keys[-1]}")

    def test_other_chat_projects_excluded(self):
        """مشاريع محادثة أخرى لا تظهر أبداً (عزل chat_id)"""
        self._seed_projects(2, chat_id=CHAT_ID)
        self._seed_projects(4, chat_id=999888)
        kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=1)
        self.assertEqual(len([c for c in _extract_callbacks(kb) if c.startswith("proj:")]), 2)

    def test_new_project_button_always_present(self):
        """صف الإجراءات [🚀 مشروع جديد][🏠 رجوع] حاضر في كل الحالات"""
        for count in (0, 5, 21):
            with self.subTest(count=count):
                self._seed_projects(count) if count else None
                kb = _bridge.build_projects_page_keyboard(CHAT_ID, page=1)
                callbacks = _extract_callbacks(kb)
                self.assertIn("cmd:new_proj", callbacks)
                self.assertIn("cmd:show_dashboard", callbacks)


# ══════════════ 4) نص شاشة التصفح ══════════════

class TestProjectsPageText(_IsolatedRegistryMixin, unittest.TestCase):
    def test_empty_registry_message(self):
        text = _bridge.render_projects_page_text(CHAT_ID, page=1)
        self.assertIn("لا توجد مشاريع", text)
        self.assertIn("مشروع جديد", text)

    def test_text_shows_total_and_position(self):
        self._seed_projects(47)
        text = _bridge.render_projects_page_text(CHAT_ID, page=2)
        self.assertIn("<b>47</b>", text)
        self.assertIn("صفحة <b>2</b> من <b>3</b>", text)
        self.assertIn("21–40", text)

    def test_last_partial_page_range(self):
        """الصفحة الأخيرة الجزئية: 47 مشروعاً ➔ صفحة 3 تعرض 41–47"""
        self._seed_projects(47)
        text = _bridge.render_projects_page_text(CHAT_ID, page=3)
        self.assertIn("41–47", text)

    def test_out_of_bounds_page_text_clamped(self):
        self._seed_projects(5)
        text = _bridge.render_projects_page_text(CHAT_ID, page=99)
        self.assertIn("صفحة <b>1</b> من <b>1</b>", text)


# ══════════════ 5) عدم الانحدار: لوحة التحكم الرئيسية ══════════════

class TestDashboardRegression(_IsolatedRegistryMixin, unittest.TestCase):
    def test_dashboard_still_previews_latest_3_only(self):
        """قرار المالك: اللوحة الرئيسية تبقى معاينة سريعة بأحدث 3 مشاريع"""
        self._seed_projects(10)
        kb = _bridge.build_dashboard_keyboard(CHAT_ID)
        self.assertEqual(len([c for c in _extract_callbacks(kb) if c.startswith("proj:")]), 3)

    def test_dashboard_keeps_list_projects_button(self):
        """زر «📁 مشاريعي» ما زال في اللوحة الرئيسية ويشير لـ cmd:list_projects"""
        kb = _bridge.build_dashboard_keyboard(CHAT_ID)
        self.assertIn("cmd:list_projects", _extract_callbacks(kb))

    def test_dashboard_has_no_pagination_buttons(self):
        """اللوحة الرئيسية لا تحمل أي أزرار تقليب — التصفح شاشة مستقلة"""
        self._seed_projects(50)
        kb = _bridge.build_dashboard_keyboard(CHAT_ID)
        self.assertFalse([c for c in _extract_callbacks(kb) if c.startswith("plist:")])


# ══════════════ 6) عقود التكامل في المصدر ══════════════

class TestSourceContracts(unittest.TestCase):
    def test_dead_button_fixed_handler_exists(self):
        """🔴 إصلاح الزر الميت: فرع cmd:list_projects موجود الآن في الموزّع"""
        self.assertIn('elif data == "cmd:list_projects":', BRIDGE_SRC)

    def test_page_flip_handler_exists(self):
        self.assertIn('elif data.startswith("plist:page:"):', BRIDGE_SRC)

    def test_noop_handler_exists(self):
        self.assertIn('elif data == "plist:noop":', BRIDGE_SRC)

    def test_page_flip_edits_same_message_in_place(self):
        """التقليب يعدّل نفس الرسالة (edit_telegram_message_text) — صفر Spam"""
        handler_block = BRIDGE_SRC.split('elif data.startswith("plist:page:"):', 1)[1].split("elif ", 1)[0]
        self.assertIn("edit_telegram_message_text", handler_block)
        self.assertIn("message_id", handler_block)

    def test_page_flip_has_send_fallback(self):
        """لو غاب message_id (حالة نادرة) ➔ fallback بإرسال رسالة جديدة بلا Crash"""
        handler_block = BRIDGE_SRC.split('elif data.startswith("plist:page:"):', 1)[1].split("elif ", 1)[0]
        self.assertIn("send_telegram_message", handler_block)

    def test_list_projects_handler_uses_pagination_screen(self):
        """معالج cmd:list_projects يفتح شاشة التصفح (النص + الكيبورد الجديدان)"""
        handler_block = BRIDGE_SRC.split('elif data == "cmd:list_projects":', 1)[1].split("elif ", 1)[0]
        self.assertIn("render_projects_page_text", handler_block)
        self.assertIn("build_projects_page_keyboard", handler_block)

    def test_pagination_keyboard_defined_before_dispatcher(self):
        """الدوال تُعرَّف قبل الموزّع (سلامة ترتيب single-file)"""
        self.assertLess(
            BRIDGE_SRC.index("def build_projects_page_keyboard"),
            BRIDGE_SRC.index('elif data == "cmd:list_projects":'),
        )

    def test_existing_proj_handler_untouched(self):
        """معالج proj: القائم (الاستئناف المباشر) لم يُمس"""
        self.assertIn('elif data.startswith("proj:"):', BRIDGE_SRC)

    def test_dashboard_preview_limit_still_3(self):
        """المعاينة السريعة في اللوحة تحتفظ حرفياً بـ limit=3"""
        self.assertIn("list_known_projects(chat_id=chat_id, limit=3)", BRIDGE_SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
