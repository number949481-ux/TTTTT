#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p30_account_timing.py
=================================
⏱️ [P30] حراسة ميزة «المحاسبة الزمنية الجنائية للحسابات»
(Forensic Time Accounting — Extension 08):

SCENARIO A: حساب واحد ينجز المهمة — span واحد مغلق + كتلة إحصائيات كاملة.
SCENARIO B: تعدد حسابات (A→B→C) — spans بالترتيب + «(المُنجِز)» لآخر حساب.
SCENARIO C: عودة الحساب (A→B→A) — تجميع مدتَي A في مدخل واحد ×2.
SCENARIO D: الإغلاق الحتمي — close مزدوج idempotent + إغلاق بلا فتح آمن.
SCENARIO E: Formatter العربي — ثوانٍ/دقائق/ساعات + قيم سالبة/None بلا Crash.
SCENARIO F: monotonic هو مصدر المدة (لا يتأثر بقفزات wall clock).
SCENARIO G: العزل بين التشغيلات + عزل الـ config بين المهام المتوازية.
SCENARIO H: عقود المصدر — hooks في مواضعها (claim / finally / reset / رسالة نهائية)
            + الفصل الصارم بين عداد الاستئناف وعدد الحسابات (Resume ≠ Accounts−1).
"""

import re
import sys
import time
import pathlib
import unittest
import importlib.util

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p30", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)


class _CfgStub:
    """Stub خفيف بدل BridgeConfig لعزل اختبارات الوحدات."""
    def __init__(self):
        self.account_journey = []
        self.account_journey_spans = []
        self.last_credit_continuations = 0
        self.max_credit_continuations = 10


class TestSpanLifecycle(unittest.TestCase):
    """SCENARIO A/D: فتح/إغلاق span + الحتمية + idempotency."""

    def test_open_creates_span_with_monotonic_and_wall(self):
        cfg = _CfgStub()
        span = _bridge.open_account_timing_span(cfg, "a@x.com", attempt_number=1)
        self.assertIsNotNone(span)
        self.assertEqual(span["email"], "a@x.com")
        self.assertEqual(span["attempt_number"], 1)
        self.assertIsInstance(span["started_monotonic"], float)
        self.assertIsInstance(span["started_wall"], float)
        self.assertFalse(span["closed"])
        self.assertIsNone(span["duration_seconds"])
        self.assertIs(cfg.account_journey_spans[0], span)

    def test_open_rejects_empty_email_and_none_cfg(self):
        cfg = _CfgStub()
        self.assertIsNone(_bridge.open_account_timing_span(cfg, ""))
        self.assertIsNone(_bridge.open_account_timing_span(cfg, None))
        self.assertIsNone(_bridge.open_account_timing_span(None, "a@x.com"))
        self.assertEqual(cfg.account_journey_spans, [])

    def test_close_sets_duration_and_closed(self):
        cfg = _CfgStub()
        _bridge.open_account_timing_span(cfg, "a@x.com")
        span = _bridge.close_account_timing_span(cfg, "a@x.com")
        self.assertIsNotNone(span)
        self.assertTrue(span["closed"])
        self.assertGreaterEqual(span["duration_seconds"], 0.0)
        self.assertIsNotNone(span["ended_wall"])

    def test_double_close_is_idempotent(self):
        """SCENARIO D: الإغلاق المزدوج لا يغيّر المدة المسجلة."""
        cfg = _CfgStub()
        _bridge.open_account_timing_span(cfg, "a@x.com")
        first = _bridge.close_account_timing_span(cfg, "a@x.com")
        recorded = first["duration_seconds"]
        second = _bridge.close_account_timing_span(cfg, "a@x.com")
        self.assertIsNone(second, "الإغلاق الثاني يجب ألا يجد span مفتوحاً")
        self.assertEqual(cfg.account_journey_spans[0]["duration_seconds"], recorded)

    def test_close_without_open_is_safe(self):
        cfg = _CfgStub()
        self.assertIsNone(_bridge.close_account_timing_span(cfg, "ghost@x.com"))
        self.assertIsNone(_bridge.close_account_timing_span(None, "a@x.com"))

    def test_close_targets_matching_email_only(self):
        cfg = _CfgStub()
        _bridge.open_account_timing_span(cfg, "a@x.com")
        _bridge.open_account_timing_span(cfg, "b@x.com")
        closed = _bridge.close_account_timing_span(cfg, "a@x.com")
        self.assertEqual(closed["email"], "a@x.com")
        self.assertFalse(cfg.account_journey_spans[1]["closed"], "span الحساب b يبقى مفتوحاً")


class TestAggregation(unittest.TestCase):
    """SCENARIO B/C: التجميع لكل حساب بترتيب أول ظهور + العودة A→B→A."""

    def _mk(self, email, dur):
        return {"email": email, "duration_seconds": dur, "closed": True,
                "started_monotonic": 0.0, "started_wall": 0.0}

    def test_multi_account_order_preserved(self):
        spans = [self._mk("a@x.com", 10), self._mk("b@x.com", 20), self._mk("c@x.com", 5)]
        agg = _bridge.aggregate_journey_spans_per_email(spans)
        self.assertEqual([i["email"] for i in agg], ["a@x.com", "b@x.com", "c@x.com"])
        self.assertEqual([i["total_seconds"] for i in agg], [10, 20, 5])

    def test_returning_account_sums_both_spans(self):
        """SCENARIO C: A→B→A — مدخل واحد لـ A بمجموع فترتيه."""
        spans = [self._mk("a@x.com", 30), self._mk("b@x.com", 40), self._mk("a@x.com", 25)]
        agg = _bridge.aggregate_journey_spans_per_email(spans)
        self.assertEqual(len(agg), 2)
        self.assertEqual(agg[0]["email"], "a@x.com")
        self.assertEqual(agg[0]["total_seconds"], 55)
        self.assertEqual(agg[0]["spans_count"], 2)
        self.assertEqual(agg[1]["total_seconds"], 40)

    def test_open_span_counted_best_effort(self):
        spans = [{"email": "a@x.com", "duration_seconds": None,
                  "started_monotonic": time.monotonic() - 2.0, "closed": False}]
        agg = _bridge.aggregate_journey_spans_per_email(spans)
        self.assertGreaterEqual(agg[0]["total_seconds"], 1.5)

    def test_garbage_entries_ignored(self):
        agg = _bridge.aggregate_journey_spans_per_email([None, "junk", {"email": ""}, self._mk("a@x.com", 7)])
        self.assertEqual(len(agg), 1)
        self.assertEqual(agg[0]["total_seconds"], 7)

    def test_empty_input(self):
        self.assertEqual(_bridge.aggregate_journey_spans_per_email(None), [])
        self.assertEqual(_bridge.aggregate_journey_spans_per_email([]), [])


class TestArabicDurationFormatter(unittest.TestCase):
    """SCENARIO E: الصياغة العربية للمدد بكل الحواف."""

    def test_seconds_only(self):
        self.assertEqual(_bridge.format_arabic_duration(45), "45 ثانية")

    def test_zero_and_invalid_inputs_no_crash(self):
        self.assertEqual(_bridge.format_arabic_duration(0), "0 ثانية")
        self.assertEqual(_bridge.format_arabic_duration(-10), "0 ثانية")
        self.assertEqual(_bridge.format_arabic_duration(None), "0 ثانية")
        self.assertEqual(_bridge.format_arabic_duration("junk"), "0 ثانية")

    def test_minutes_and_seconds(self):
        out = _bridge.format_arabic_duration(3 * 60 + 12)
        self.assertIn("3", out)
        self.assertIn("12 ثانية", out)
        self.assertIn("و", out)

    def test_hours_and_minutes(self):
        out = _bridge.format_arabic_duration(3600 + 5 * 60)
        self.assertIn("1 ساعة", out)
        self.assertIn("5 دقيقة", out)
        self.assertNotIn("ثانية", out, "لا تُعرض الثواني الصفرية مع وجود مكوّن أكبر")

    def test_float_seconds_truncated(self):
        self.assertEqual(_bridge.format_arabic_duration(59.9), "59 ثانية")


class TestMonotonicSource(unittest.TestCase):
    """SCENARIO F: المدة من monotonic حصراً — wall للعرض فقط."""

    def test_duration_uses_monotonic_not_wall(self):
        cfg = _CfgStub()
        span = _bridge.open_account_timing_span(cfg, "a@x.com")
        # تخريب wall عمداً — المدة يجب ألا تتأثر
        span["started_wall"] = span["started_wall"] - 99999
        closed = _bridge.close_account_timing_span(cfg, "a@x.com")
        self.assertLess(closed["duration_seconds"], 5.0,
                        "المدة تُحسب من monotonic — قفزة wall clock يجب ألا تُضخمها")

    def test_negative_monotonic_clamped(self):
        cfg = _CfgStub()
        span = _bridge.open_account_timing_span(cfg, "a@x.com")
        span["started_monotonic"] = time.monotonic() + 10_000  # مستقبل مستحيل
        closed = _bridge.close_account_timing_span(cfg, "a@x.com")
        self.assertEqual(closed["duration_seconds"], 0.0, "clamp عند صفر — لا مدد سالبة أبداً")


class TestFinalMessageBlock(unittest.TestCase):
    """SCENARIO A/B: كتلة الإحصائيات النهائية — الظهور الدائم + المُنجِز + العدادان."""

    def _cfg_with_spans(self, spans, continuations=0):
        cfg = _CfgStub()
        cfg.account_journey_spans = spans
        cfg.last_credit_continuations = continuations
        return cfg

    def _mk(self, email, dur):
        return {"email": email, "duration_seconds": dur, "closed": True,
                "started_monotonic": 0.0, "started_wall": 0.0}

    def test_single_account_block_always_shown(self):
        """SCENARIO A: الكتلة تظهر حتى بحساب واحد (عكس سطر P29 الشرطي) — أدوار P39."""
        cfg = self._cfg_with_spans([self._mk("solo@x.com", 90)])
        block = _bridge.format_account_timing_block(cfg, task_total_seconds=120)
        self.assertIn("📊", block)
        self.assertIn("solo@x.com", block)
        self.assertIn("(🌟 الحساب المنجز)", block)
        self.assertIn("الزمن الكلي للمهمة", block)
        self.assertIn("🔁 0 استئناف", block)

    def test_full_email_no_masking(self):
        cfg = self._cfg_with_spans([self._mk("very.long.email+tag@domain.example.com", 10)])
        self.assertIn("very.long.email+tag@domain.example.com",
                      _bridge.format_account_timing_block(cfg))

    def test_finisher_is_last_span_account(self):
        """SCENARIO B: «(🌟 الحساب المنجز)» لآخر حساب في الرحلة فقط (P39)."""
        cfg = self._cfg_with_spans([self._mk("a@x.com", 100), self._mk("b@x.com", 200)])
        block = _bridge.format_account_timing_block(cfg)
        a_line = [l for l in block.split("\n") if "a@x.com" in l][0]
        b_line = [l for l in block.split("\n") if "b@x.com" in l][0]
        self.assertNotIn("الحساب المنجز", a_line)
        self.assertIn("(البداية)", a_line)
        self.assertIn("الحساب المنجز", b_line)

    def test_returning_account_finisher_and_multiplier(self):
        """SCENARIO C: A→B→A — A هو المنجز ويحمل ×2 (مجموع فترتيه يعبر العتبة)."""
        cfg = self._cfg_with_spans([self._mk("a@x.com", 40), self._mk("b@x.com", 90), self._mk("a@x.com", 30)])
        block = _bridge.format_account_timing_block(cfg)
        a_line = [l for l in block.split("\n") if "a@x.com" in l][0]
        self.assertIn("الحساب المنجز", a_line)
        self.assertIn("×2", a_line)

    def test_accounts_total_is_sum_of_spans(self):
        cfg = self._cfg_with_spans([self._mk("a@x.com", 60), self._mk("b@x.com", 60)])
        block = _bridge.format_account_timing_block(cfg)
        self.assertIn("إجمالي زمن التوليد", block)
        self.assertIn("2m", block)  # ⏱️ [P40] المدة المضغوطة بدل «2 دقيقة»

    def test_resume_counter_independent_of_accounts_count(self):
        """SCENARIO H: Resume ≠ Accounts−1 — 3 حسابات مع استئناف واحد فقط (عقد P30 محفوظ بعد P39)."""
        cfg = self._cfg_with_spans(
            [self._mk("a@x.com", 100), self._mk("b@x.com", 100), self._mk("c@x.com", 100)],
            continuations=1,
        )
        block = _bridge.format_account_timing_block(cfg)
        self.assertIn("🔁 1 استئناف", block)
        self.assertNotIn("🔁 2 استئناف", block)

    def test_empty_spans_returns_empty_string(self):
        cfg = self._cfg_with_spans([])
        self.assertEqual(_bridge.format_account_timing_block(cfg), "")
        self.assertEqual(_bridge.format_account_timing_block(None), "")

    def test_html_escaping_of_email(self):
        cfg = self._cfg_with_spans([self._mk("a<b>&c@x.com", 5)])
        block = _bridge.format_account_timing_block(cfg)
        self.assertIn("a&lt;b&gt;&amp;c@x.com", block)
        self.assertNotIn("<b>&c", block)


class TestIsolation(unittest.TestCase):
    """SCENARIO G: العزل بين التشغيلات والمهام المتوازية."""

    def test_bridgeconfig_default_spans_isolated_per_instance(self):
        c1 = _bridge.BridgeConfig()
        c2 = _bridge.BridgeConfig()
        c1.account_journey_spans.append({"email": "a@x.com"})
        self.assertEqual(c2.account_journey_spans, [],
                         "default_factory يعزل الـ spans بين المهام المتوازية")

    def test_open_initializes_missing_spans_list(self):
        class Bare:
            pass
        cfg = Bare()
        span = _bridge.open_account_timing_span(cfg, "a@x.com")
        self.assertIsNotNone(span)
        self.assertEqual(len(cfg.account_journey_spans), 1)


class TestSourceContracts(unittest.TestCase):
    """SCENARIO H: عقود المصدر — الـ hooks في مواضعها الصحيحة حرفياً."""

    def test_bridgeconfig_declares_spans_field(self):
        self.assertIn("account_journey_spans: list = field(default_factory=list)", BRIDGE_SRC)

    def test_failover_resets_spans_per_run(self):
        self.assertIn('bridge_cfg.account_journey_spans = []', BRIDGE_SRC)

    def test_span_opened_at_claim_moment(self):
        """open يأتي مباشرة بعد record_account_journey (لحظة الـ claim الفعلي)."""
        pattern = re.compile(
            r"record_account_journey\(bridge_cfg, curr_email\).*\n"
            r"\s*open_account_timing_span\(bridge_cfg, curr_email, attempt_number=attempt\)"
        )
        self.assertTrue(pattern.search(BRIDGE_SRC), "فتح الـ span يجب أن يلي الـ claim مباشرة")

    def test_span_closed_inside_finally_before_release(self):
        """الإغلاق داخل finally وقبل release_account_selection — حتمي في كل المسارات."""
        pattern = re.compile(
            r"finally:\s*\n"
            r"\s*close_account_timing_span\(bridge_cfg, curr_email\).*\n"
            r"\s*release_account_selection\(curr_email, owner_token\)"
        )
        self.assertTrue(pattern.search(BRIDGE_SRC), "إغلاق الـ span يجب أن يكون أول سطر في finally")

    def test_final_message_includes_timing_block(self):
        self.assertIn('timing_stats = format_account_timing_block(cfg, task_total_seconds=time.time() - task_started_at)', BRIDGE_SRC)
        self.assertIn('f"{timing_block}"', BRIDGE_SRC)

    def test_no_rotation_or_resume_semantics_touched(self):
        """الحارس السلبي: عداد الاستئناف يزداد فقط عند CREDIT_EXHAUSTED — سطر واحد كما كان."""
        self.assertEqual(BRIDGE_SRC.count("credit_continuations += 1"), 1,
                         "الزيادة الوحيدة للعداد تبقى عند CREDIT_EXHAUSTED — P30 لا يلمسها")
        # فرعا CREDIT_EXHAUSTED الاثنان pre-existing في failover (increment + handling)
        self.assertEqual(BRIDGE_SRC.count('if status == "CREDIT_EXHAUSTED":'), 2)

    def test_monotonic_used_for_duration(self):
        self.assertIn("time.monotonic()", BRIDGE_SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
