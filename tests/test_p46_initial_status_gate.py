#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p46_initial_status_gate.py
======================================
🚪 [P46/T-GSB-7] حراسة إصلاح «الاكتمال المبكر الكاذب» عند الحالة الابتدائية.

العلة (بدليل حي من الاختبار الخارجي): detect_response_status الخام صنّف
افتتاحية Autopilot القصيرة («تمام، الخطة واضحة… هنبدأ بالاستكشاف:» ~108 حرفاً)
كـ COMPLETED فور انتهاء البث → polled_any=False → تُتخطى حلقة المتابعة
والجلبة النهائية (fetch_final_reply_text لا تُستدعى أبداً) ويخرج البوت
بعد ~29 ثانية والخادم ما زال يعمل.

الإصلاح (T1 — صفر شبكة إضافية):
  - قراءة prev_activity (P18 baseline) نُقلت قبل حسم الحالة الابتدائية —
    نفس القراءة الواحدة تخدم البوابة والـ baseline معاً.
  - فرع else يمر عبر detect_response_status_gated(raw_initial, prev_activity,
    inactive_streak=0, stable_streak=None) — بوابة P44-D9 القائمة بلا لمس.

القرار T2 (واعٍ وموثق): حارس polled_any عند الجلبة النهائية باقٍ كما هو —
T1 وحده يقلب COMPLETED الكاذب → RUNNING → polled_any=True تلقائياً،
وعقد P44-D8 («صفر شبكة للبث المكتمل») محفوظ حرفياً.

المصفوفة (10 اختبارات / 4 فئات):
 01 قراءة النشاط قبل حسم الحالة (وقراءة واحدة فقط في المقطع)
 02 الاستدعاء المبوَّب بالمعاملات الصحيحة (ولا إسناد خام غير مبوَّب في المقطع)
 03 فرع __STREAM_INTERRUPTED__ لم يُمس (RUNNING بلا بوابة — عقد P12)
 04 COMPLETED كاذب + نشاط حي → RUNNING (سيناريو Autopilot الحرفي)
 05 COMPLETED + غير نشط لكن streak=0 → RUNNING (debounce)
 06 الحالات المهيكلة تخترق البوابة فوراً (4 حالات فرعية)
 07 activity=None → حياد Fail-Open (الحالة الخام تمر كما هي)
 08 نتيجة polled_any: الخام → False (توثيق العلة) / المبوَّب → True (إثبات الإصلاح)
 09 مراسي P44/P18 حية بعد التعديل (عقود الاختبارات القائمة)
 10 bridge_refactor/p06 يحوي الإصلاح حرفياً (تكافؤ التقسيم الأمين)
"""

import importlib.util
import pathlib
import re
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIDGE_PATH = ROOT / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_p46", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("bridge_p46", _bridge)
_spec.loader.exec_module(_bridge)

# افتتاحية Autopilot الحرفية من الاختبار الحي الخارجي (~108 حرفاً) —
# detect_response_status الخام يصنّفها COMPLETED رغم أن الخادم ما زال يعمل.
AUTOPILOT_OPENER = "تمام، الخطة واضحة. المطلوب تنفيذ المهمة كاملة. هنبدأ بالاستكشاف:"

_P44_TERMINAL = ("COMPLETED", "CREDIT_EXHAUSTED", "DATA_RETENTION",
                 "SESSION_EXPIRED", "FORBIDDEN")


def _initial_block() -> str:
    """يستخرج مقطع حسم الحالة الابتدائية حرفياً — من قراءة النشاط (baseline)
    حتى حسم polled_any (مقاوم لإزاحة الأسطر: مراسٍ نصية لا أرقام)."""
    start = BRIDGE_SRC.index(
        "prev_activity = fetch_project_activity_signature(pid, cookies)")
    end = BRIDGE_SRC.index("polled_any = final_status", start)
    return BRIDGE_SRC[start:end]


class TestP46SourceWiring(unittest.TestCase):
    """فئة 1 — التوصيل المصدري: القراءة قبل الحسم + الاستدعاء المبوَّب."""

    def test_01_activity_read_before_initial_status(self):
        """[01] قراءة النشاط تسبق حسم الحالة الابتدائية — وقراءة واحدة فقط
        في المقطع (صفر شبكة إضافية — نفس قراءة P18 baseline)."""
        block = _initial_block()
        # القراءة هي أول سطر في المقطع (المرساة نفسها) — والحسم بعدها
        self.assertIn("raw_initial = detect_response_status(answer)", block)
        self.assertLess(
            block.index("fetch_project_activity_signature(pid, cookies)"),
            block.index("raw_initial = detect_response_status(answer)"),
        )
        # قراءة نشاط واحدة فقط داخل المقطع — لا استدعاء شبكي إضافي
        self.assertEqual(
            block.count("fetch_project_activity_signature("), 1,
            "يجب أن تبقى قراءة النشاط واحدة (صفر شبكة إضافية)")

    def test_02_gated_call_with_correct_params(self):
        """[02] فرع else يمر عبر البوابة بالمعاملات الصحيحة — ولا يوجد
        إسناد خام غير مبوَّب (final_status = detect_response_status(answer))."""
        block = _initial_block()
        self.assertRegex(
            block,
            r"final_status = detect_response_status_gated\(\s*"
            r"raw_initial,\s*prev_activity,\s*inactive_streak=0,\s*"
            r"stable_streak=None,\s*email=email,?\s*\)",
        )
        # العلة القديمة: الإسناد الخام المباشر — يجب ألا يعود
        self.assertNotIn("final_status = detect_response_status(answer)", block)

    def test_03_stream_interrupted_branch_untouched(self):
        """[03] عقد P12: فرع __STREAM_INTERRUPTED__ لم يُمس — RUNNING مباشرة
        بلا بوابة (نافذة 400 حرف — نفس مرساة test_p12)."""
        idx = BRIDGE_SRC.index('if answer == "__STREAM_INTERRUPTED__":')
        window = BRIDGE_SRC[idx:idx + 400]
        self.assertIn('final_status = "RUNNING"', window)
        # الفرع المقاطَع لا يمر عبر البوابة (لا حاجة — RUNNING يدخل الحلقة أصلاً)
        seg_to_else = window[:window.index("else:")] if "else:" in window else window
        self.assertNotIn("detect_response_status_gated", seg_to_else)


class TestP46GateBehavior(unittest.TestCase):
    """فئة 2 — سلوك البوابة على سيناريو Autopilot الحرفي وحالات الحواف."""

    def test_04_false_completed_with_active_indicator_becomes_running(self):
        """[04] سيناريو العلة الحرفي: الافتتاحية القصيرة COMPLETED خام +
        مؤشر نشاط حي → RUNNING (البوابة تمسك)."""
        raw = _bridge.detect_response_status(AUTOPILOT_OPENER)
        self.assertEqual(raw, "COMPLETED",
                         "توثيق العلة: الخام يعتمد الافتتاحية كاكتمال")
        with mock.patch.object(_bridge, "log_event"):
            gated = _bridge.detect_response_status_gated(
                raw, {"active": True}, inactive_streak=0, stable_streak=None)
        self.assertEqual(gated, "RUNNING")

    def test_05_completed_inactive_but_zero_streak_debounces(self):
        """[05] حتى مع مؤشر غير نشط: inactive_streak=0 < 2 → RUNNING
        (debounce D6 — قراءة واحدة لا تكفي لاعتماد الاكتمال)."""
        with mock.patch.object(_bridge, "log_event"):
            gated = _bridge.detect_response_status_gated(
                "COMPLETED", {"active": False},
                inactive_streak=0, stable_streak=None)
        self.assertEqual(gated, "RUNNING")

    def test_06_structured_statuses_pierce_gate(self):
        """[06] الحالات المهيكلة تخترق البوابة فوراً — صفر تأخير
        (عقد P44: failover يحتاجها بلا حجز)."""
        for status in ("CREDIT_EXHAUSTED", "DATA_RETENTION",
                       "SESSION_EXPIRED", "FORBIDDEN"):
            with self.subTest(status=status):
                gated = _bridge.detect_response_status_gated(
                    status, {"active": True},
                    inactive_streak=0, stable_streak=None)
                self.assertEqual(gated, status)

    def test_07_activity_none_is_neutral_fail_open(self):
        """[07] activity=None (فشل قراءة P18) → حياد تام — الحالة الخام
        تمر كما هي (Fail-Open = سلوك ما قبل P46 حرفياً)."""
        gated = _bridge.detect_response_status_gated(
            "COMPLETED", None, inactive_streak=0, stable_streak=None)
        self.assertEqual(gated, "COMPLETED")
        gated2 = _bridge.detect_response_status_gated(
            "RUNNING", None, inactive_streak=0, stable_streak=None)
        self.assertEqual(gated2, "RUNNING")


class TestP46PolledAnyConsequence(unittest.TestCase):
    """فئة 3 — النتيجة العملية على polled_any (جوهر T-GSB-7)."""

    def test_08_polled_any_raw_false_gated_true(self):
        """[08] بالخام: COMPLETED → polled_any=False (توثيق العلة: الجلبة
        النهائية لا تُستدعى). بالمبوَّب: RUNNING → polled_any=True
        (إثبات الإصلاح: الحلقة والجلبة مضمونتان)."""
        raw = _bridge.detect_response_status(AUTOPILOT_OPENER)
        polled_any_before_fix = raw not in _P44_TERMINAL
        self.assertFalse(polled_any_before_fix,
                         "توثيق العلة: الخام كان يتخطى الحلقة والجلبة")
        with mock.patch.object(_bridge, "log_event"):
            gated = _bridge.detect_response_status_gated(
                raw, {"active": True}, inactive_streak=0, stable_streak=None)
        polled_any_after_fix = gated not in _P44_TERMINAL
        self.assertTrue(polled_any_after_fix,
                        "إثبات الإصلاح: المبوَّب يدخل الحلقة → الجلبة تعمل")


class TestP46ContractsPreserved(unittest.TestCase):
    """فئة 4 — عقود الاختبارات القائمة (P44/P18/P12) + تكافؤ التقسيم."""

    def test_09_p44_p18_anchors_survive(self):
        """[09] المراسي الحرفية للاختبارات القائمة حية بعد التعديل."""
        # P44-D8: حارس الجلبة النهائية الحرفي (test_p44 سطر 369)
        self.assertIn('if polled_any and final_status == "COMPLETED":', BRIDGE_SRC)
        # P44: مرساتا الالتقاط (test_p44 سطرا 364-365)
        self.assertIn("polled_any = final_status", BRIDGE_SRC)
        self.assertIn("if polled_any and final_status", BRIDGE_SRC)
        # P44-D12: سقف session_timeout قبل البوابة داخل الحلقة
        loop_seg = BRIDGE_SRC[BRIDGE_SRC.find("polled_any = final_status"):
                              BRIDGE_SRC.find("if polled_any and final_status")]
        self.assertLess(loop_seg.find("elapsed > session_timeout"),
                        loop_seg.find("detect_response_status_gated("))
        # P18: baseline الحرفي موجود وقبل الحلقة (test_p18 test_02)
        base_idx = BRIDGE_SRC.index(
            "prev_activity = fetch_project_activity_signature(pid, cookies)")
        loop_idx = BRIDGE_SRC.index("while final_status not in (", base_idx)
        self.assertLess(base_idx, loop_idx)

    def test_10_refactor_p06_contains_fix(self):
        """[10] التقسيم الأمين: p06 يحوي الإصلاح حرفياً (تكافؤ بايتي مع 01.33)."""
        p06 = ROOT / "bridge_refactor" / "parts" / "p06_engine_flow.py"
        self.assertTrue(p06.exists(), "p06_engine_flow.py غير موجود")
        src = p06.read_text(encoding="utf-8")
        self.assertIn("raw_initial = detect_response_status(answer)", src)
        self.assertIn("P46/T-GSB-7", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
