#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p18_activity_stop.py
===============================
⛳ [P18] حراسة مراقب مؤشر النشاط الحي (Deep Thinking / Tasks Remaining):

1. extract_activity_signature: كشف Deep Thinking و Tasks Remaining (بأرقام وبدون).
2. should_stop_on_activity_change: وقف فوري عند اختفاء المؤشر أو أي تغيّر في المهام (زيادة أو نقصان).
3. عدم الوقف: baseline غير نشط، ثبات المهام، فشل الجلب (None).
4. تكامل: حلقة المتابعة في send_message_and_make_public تستدعي المراقب وتكسر فوراً.
"""

import sys
import re
import pathlib
import unittest
import importlib.util

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.32_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p18", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)

extract_activity_signature = _bridge.extract_activity_signature
should_stop_on_activity_change = _bridge.should_stop_on_activity_change


class TestExtractActivitySignature(unittest.TestCase):
    """1. استخراج بصمة المؤشر من نص الصفحة"""

    def test_01_deep_thinking_detected(self):
        sig = extract_activity_signature("<div>Deep Thinking</div>")
        self.assertTrue(sig["deep_thinking"])
        self.assertTrue(sig["active"])

    def test_02_tasks_remaining_with_number(self):
        sig = extract_activity_signature("... 5 tasks remaining ...")
        self.assertEqual(sig["tasks_remaining"], 5)
        self.assertTrue(sig["active"])

    def test_03_tasks_remaining_number_after_label(self):
        sig = extract_activity_signature("Tasks Remaining: 3")
        self.assertEqual(sig["tasks_remaining"], 3)

    def test_04_tasks_remaining_without_number(self):
        sig = extract_activity_signature("tasks remaining soon")
        self.assertEqual(sig["tasks_remaining"], -1)
        self.assertTrue(sig["active"])

    def test_05_no_indicator(self):
        sig = extract_activity_signature("الموقع جاهز والرد مكتمل")
        self.assertFalse(sig["deep_thinking"])
        self.assertIsNone(sig["tasks_remaining"])
        self.assertFalse(sig["active"])

    def test_06_none_and_empty_safe(self):
        for v in (None, "", "   "):
            sig = extract_activity_signature(v)
            self.assertFalse(sig["active"])


class TestShouldStopOnActivityChange(unittest.TestCase):
    """2-3. قرار الوقف الفوري"""

    def _sig(self, active=True, deep=False, tasks=None):
        return {"deep_thinking": deep, "tasks_remaining": tasks, "active": active}

    def test_01_indicator_disappeared_stops(self):
        stop, reason = should_stop_on_activity_change(
            self._sig(active=True, deep=True), self._sig(active=False)
        )
        self.assertTrue(stop)
        self.assertEqual(reason, "activity-indicator-disappeared")

    def test_02_tasks_increased_stops(self):
        stop, reason = should_stop_on_activity_change(
            self._sig(tasks=2), self._sig(tasks=5)
        )
        self.assertTrue(stop)
        self.assertEqual(reason, "tasks-remaining-changed")

    def test_03_tasks_decreased_also_stops(self):
        # ⛳ أي تغيّر في المهام = وقف فوري — حتى النقصان (المهام اتغيرت → مفيش تكملة)
        stop, reason = should_stop_on_activity_change(self._sig(tasks=5), self._sig(tasks=2))
        self.assertTrue(stop)
        self.assertEqual(reason, "tasks-remaining-changed")

    def test_04_tasks_same_continues(self):
        stop, _ = should_stop_on_activity_change(self._sig(tasks=3), self._sig(tasks=3))
        self.assertFalse(stop)

    def test_05_inactive_baseline_no_decision(self):
        stop, _ = should_stop_on_activity_change(self._sig(active=False), self._sig(active=False))
        self.assertFalse(stop)

    def test_06_none_prev_or_curr_no_decision(self):
        self.assertEqual(should_stop_on_activity_change(None, self._sig()), (False, ""))
        self.assertEqual(should_stop_on_activity_change(self._sig(), None), (False, ""))

    def test_07_unknown_count_disappearance_still_stops(self):
        # بصمة نشطة بدون رقم (-1) ثم اختفاء كامل → وقف
        stop, reason = should_stop_on_activity_change(
            self._sig(tasks=-1), self._sig(active=False)
        )
        self.assertTrue(stop)
        self.assertEqual(reason, "activity-indicator-disappeared")

    def test_08_deep_thinking_toggled_stops(self):
        # Deep Thinking ظهر/اختفى مع بقاء النشاط (بنفس عدد المهام) → وقف فوري
        stop, reason = should_stop_on_activity_change(
            self._sig(deep=True, tasks=3), self._sig(deep=False, tasks=3)
        )
        self.assertTrue(stop)
        self.assertEqual(reason, "deep-thinking-changed")

    def test_09_deep_thinking_appeared_stops(self):
        stop, reason = should_stop_on_activity_change(
            self._sig(deep=False, tasks=2), self._sig(deep=True, tasks=2)
        )
        self.assertTrue(stop)
        self.assertEqual(reason, "deep-thinking-changed")

    def test_10_stable_signature_continues(self):
        # نفس البصمة تماماً (Deep Thinking شغال ونفس عدد المهام) → استمرار المتابعة
        stop, _ = should_stop_on_activity_change(
            self._sig(deep=True, tasks=4), self._sig(deep=True, tasks=4)
        )
        self.assertFalse(stop)


class TestPollingLoopIntegration(unittest.TestCase):
    """4. تكامل المراقب داخل حلقة المتابعة"""

    def test_01_monitor_called_inside_polling_loop(self):
        m = re.search(
            r"while final_status not in \(\"COMPLETED\", \"CREDIT_EXHAUSTED\", \"DATA_RETENTION\", \"SESSION_EXPIRED\", \"FORBIDDEN\"\):(.*?)\n        if is_timeout:",
            BRIDGE_SRC, re.DOTALL,
        )
        self.assertIsNotNone(m, "لم يتم العثور على حلقة المتابعة")
        loop_body = m.group(1)
        self.assertIn("fetch_project_activity_signature", loop_body)
        self.assertIn("should_stop_on_activity_change", loop_body)
        self.assertIn("break", loop_body)

    def test_02_baseline_captured_before_loop(self):
        idx_baseline = BRIDGE_SRC.index("prev_activity = fetch_project_activity_signature(pid, cookies)")
        idx_loop = BRIDGE_SRC.index('while final_status not in ("COMPLETED", "CREDIT_EXHAUSTED"')
        self.assertLess(idx_baseline, idx_loop, "الـ baseline يجب أن يُلتقط قبل الحلقة")

    def test_03_fetch_failure_returns_none_and_is_ignored(self):
        # فشل الشبكة يرجع None ولا يوقف الحلقة (curr_activity is not None guard)
        self.assertIsNone(_bridge.fetch_project_activity_signature("", {}))
        self.assertIn("if curr_activity is not None:", BRIDGE_SRC)

    def test_04_build_version_bumped(self):
        self.assertEqual(_bridge.BUILD_VERSION, "01.32")


if __name__ == "__main__":
    unittest.main(verbosity=2)
