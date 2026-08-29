#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p39_completion_ux_streamlining.py
============================================
🧹 [P39] حراسة تبسيط بطاقة الاكتمال + الفلترة الذكية للحسابات المنتجة
(بروتوكول 13_STREAMLINED_COMPLETION_UX.MD — DEC-034).

المجموعات:
1. TestProductiveConstant       — الثابت المركزي وعدم التناثر
2. TestProductiveFilter         — الفلتر النقي (عتبة/تحصين المُنجِز/Fail-Open/تجميع)
3. TestNewTimingBlock           — الكتلة الجديدة (العنوان/الأدوار/السطر المدمج)
4. TestResMsgCleanup            — نظافة res_msg بالمصدر (غياب المحذوفات الستة)
5. TestZeroBreaking             — بقاء دوال P29/P30/P38 والكيبوردات والعقود
6. TestForensicLogging          — التسجيل الجنائي للقائمة الكاملة في اللوج
7. TestEdgeCases                — HTML escaping + مدد سالبة + spans فارغة
"""

import importlib.util
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIDGE_PATH = ROOT / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_p39", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("bridge_p39", _bridge)
_spec.loader.exec_module(_bridge)


class _CfgStub:
    """Stub خفيف بنفس السمات المطلوبة من format_account_timing_block."""
    def __init__(self, spans=None, continuations=0):
        self.account_journey_spans = spans or []
        self.last_credit_continuations = continuations


def _mk(email, dur):
    return {"email": email, "duration_seconds": dur, "closed": True,
            "started_monotonic": 0.0, "started_wall": 0.0}


def _agg(*pairs):
    """بناء قائمة مجمَّعة مباشرة: [(email, total, count), ...]"""
    return [{"email": e, "total_seconds": t, "spans_count": c} for e, t, c in pairs]


# ══════════════════════════════════════════════════════════════
# 1) الثابت المركزي
# ══════════════════════════════════════════════════════════════
class TestProductiveConstant(unittest.TestCase):

    def test_constant_exists_and_is_60(self):
        self.assertEqual(_bridge.PRODUCTIVE_SPAN_MIN_SECONDS, 60)

    def test_constant_defined_once_top_level(self):
        self.assertEqual(BRIDGE_SRC.count("PRODUCTIVE_SPAN_MIN_SECONDS = "), 1,
                         "تعريف وحيد — ممنوع hardcoding متناثر (نمط P32/P34)")

    def test_filter_uses_constant_not_literal(self):
        # الدالة تقارن بالثابت لا برقم خام
        fn_src = BRIDGE_SRC.split("def filter_productive_account_entries")[1].split("\ndef ")[0]
        self.assertIn("PRODUCTIVE_SPAN_MIN_SECONDS", fn_src)


# ══════════════════════════════════════════════════════════════
# 2) الفلتر النقي
# ══════════════════════════════════════════════════════════════
class TestProductiveFilter(unittest.TestCase):

    def test_short_accounts_filtered_out(self):
        agg = _agg(("a@x.com", 5, 1), ("b@x.com", 900, 1), ("c@x.com", 11, 1))
        filtered, fail_open = _bridge.filter_productive_account_entries(agg, "b@x.com")
        self.assertFalse(fail_open)
        self.assertEqual([i["email"] for i in filtered], ["b@x.com"])

    def test_threshold_boundary_exactly_60_included(self):
        agg = _agg(("a@x.com", 60, 1), ("b@x.com", 59.9, 1))
        filtered, _ = _bridge.filter_productive_account_entries(agg, "a@x.com")
        self.assertEqual([i["email"] for i in filtered], ["a@x.com"])

    def test_finisher_immune_even_if_short(self):
        """الحساب المُنجِز يظهر دائماً حتى لو مدته < العتبة."""
        agg = _agg(("a@x.com", 900, 1), ("z@x.com", 8, 1))
        filtered, fail_open = _bridge.filter_productive_account_entries(agg, "z@x.com")
        self.assertFalse(fail_open)
        self.assertEqual([i["email"] for i in filtered], ["a@x.com", "z@x.com"])

    def test_fail_open_when_all_short(self):
        """كل الحسابات قصيرة وبلا مُنجِز مطابق ➔ القائمة الكاملة بلا فلترة."""
        agg = _agg(("a@x.com", 5, 1), ("b@x.com", 8, 1))
        filtered, fail_open = _bridge.filter_productive_account_entries(agg, "")
        self.assertTrue(fail_open)
        self.assertEqual(len(filtered), 2)

    def test_no_fail_open_when_finisher_matches(self):
        """كلها قصيرة لكن المُنجِز محدد ➔ يبقى وحده بلا Fail-Open."""
        agg = _agg(("a@x.com", 5, 1), ("b@x.com", 8, 1))
        filtered, fail_open = _bridge.filter_productive_account_entries(agg, "b@x.com")
        self.assertFalse(fail_open)
        self.assertEqual([i["email"] for i in filtered], ["b@x.com"])

    def test_aggregated_total_crosses_threshold(self):
        """A→B→A بمجموع 40+30=70 ➔ A منتج رغم أن كل فترة مفردة < 60."""
        agg = _agg(("a@x.com", 70, 2), ("b@x.com", 5, 1))
        filtered, fail_open = _bridge.filter_productive_account_entries(agg, "a@x.com")
        self.assertFalse(fail_open)
        self.assertEqual([i["email"] for i in filtered], ["a@x.com"])

    def test_empty_input_returns_empty_no_fail_open(self):
        self.assertEqual(_bridge.filter_productive_account_entries([], "x"), ([], False))
        self.assertEqual(_bridge.filter_productive_account_entries(None, None), ([], False))

    def test_malformed_entries_skipped_safely(self):
        agg = [None, "junk", {"email": "", "total_seconds": 999},
               {"email": "ok@x.com", "total_seconds": "not-a-number", "spans_count": 1},
               {"email": "good@x.com", "total_seconds": 120, "spans_count": 1}]
        filtered, fail_open = _bridge.filter_productive_account_entries(agg, "good@x.com")
        self.assertFalse(fail_open)
        self.assertEqual([i["email"] for i in filtered], ["good@x.com"])

    def test_order_preserved(self):
        agg = _agg(("c@x.com", 100, 1), ("a@x.com", 200, 1), ("b@x.com", 300, 1))
        filtered, _ = _bridge.filter_productive_account_entries(agg, "b@x.com")
        self.assertEqual([i["email"] for i in filtered], ["c@x.com", "a@x.com", "b@x.com"])


# ══════════════════════════════════════════════════════════════
# 3) الكتلة الجديدة
# ══════════════════════════════════════════════════════════════
class TestNewTimingBlock(unittest.TestCase):

    def _block(self, spans, continuations=0, total=None):
        return _bridge.format_account_timing_block(
            _CfgStub(spans, continuations), task_total_seconds=total)

    def test_filtered_header_when_filtering_active(self):
        block = self._block([_mk("a@x.com", 5), _mk("b@x.com", 900)])
        self.assertIn("الحسابات الفعلية التي قامت بالتوليد والاستئناف", block)
        self.assertNotIn("a@x.com", block)

    def test_fail_open_header_is_legacy(self):
        """Fail-Open: كلها قصيرة والمُنجِز ضمنها ➔ لا Fail-Open فعلياً؛
        نصنع Fail-Open حقيقي بحساب مُنجِز غير موجود في المجمَّع (مستحيل عملياً
        لكن الدالة النقية تُختبر مباشرة) — هنا نختبر العنوان عبر الكتلة بسيناريو
        span واحد قصير: المُنجِز محصَّن فيظهر بالعنوان الجديد."""
        block = self._block([_mk("solo@x.com", 5)])
        # المُنجِز محصَّن ➔ فلترة نشطة بعنوانها الجديد
        self.assertIn("الحسابات الفعلية", block)
        self.assertIn("solo@x.com", block)

    def test_roles_start_resume_finisher(self):
        block = self._block([_mk("a@x.com", 100), _mk("b@x.com", 200), _mk("c@x.com", 300)])
        a_line = [l for l in block.split("\n") if "a@x.com" in l][0]
        b_line = [l for l in block.split("\n") if "b@x.com" in l][0]
        c_line = [l for l in block.split("\n") if "c@x.com" in l][0]
        self.assertIn("(البداية)", a_line)
        self.assertIn("(استئناف 1)", b_line)
        self.assertIn("(🌟 الحساب المنجز)", c_line)

    def test_finisher_role_wins_when_single_account(self):
        block = self._block([_mk("solo@x.com", 120)])
        line = [l for l in block.split("\n") if "solo@x.com" in l][0]
        self.assertIn("(🌟 الحساب المنجز)", line)
        self.assertNotIn("(البداية)", line)

    def test_combined_total_line_format(self):
        block = self._block([_mk("a@x.com", 100), _mk("b@x.com", 200)], continuations=1)
        self.assertIn("إجمالي زمن التوليد", block)
        self.assertIn("(2 حسابات منتجة | 🔁 1 استئناف)", block)

    def test_singular_account_word(self):
        block = self._block([_mk("a@x.com", 120)])
        self.assertIn("(1 حساب منتج |", block)

    def test_total_computed_from_filtered_only(self):
        """المالك اعتمد 38 د 24 ث لا 39 د 13 ث: القصير المستبعَد لا يدخل الإجمالي."""
        block = self._block([_mk("short@x.com", 49), _mk("long@x.com", 2304)])
        self.assertNotIn("short@x.com", block)
        self.assertIn("38m 24s", block)  # ⏱️ [P40] المدة المضغوطة

    def test_wall_clock_independent_of_filtering(self):
        block = self._block([_mk("a@x.com", 5), _mk("b@x.com", 900)], total=2353)
        self.assertIn("الزمن الكلي للمهمة", block)
        self.assertIn("39m 13s", block)  # ⏱️ [P40] المدة المضغوطة

    def test_resume_counter_from_continuations_not_accounts(self):
        """عقد P30 الصارم: 3 حسابات منتجة + 0 استئناف = 🔁 0."""
        block = self._block([_mk(f"u{i}@x.com", 100) for i in range(3)], continuations=0)
        self.assertIn("🔁 0 استئناف", block)

    def test_numbering_restarts_after_filtering(self):
        block = self._block([_mk("skip@x.com", 5), _mk("a@x.com", 100), _mk("b@x.com", 200)])
        self.assertIn("1. <code>a@x.com</code>", block)
        self.assertIn("2. <code>b@x.com</code>", block)

    def test_signature_unchanged_contract(self):
        """عقد P30: نفس نداء worker بلا تغيير توقيع."""
        self.assertIn("timing_stats = format_account_timing_block(cfg, task_total_seconds=time.time() - task_started_at)", BRIDGE_SRC)


# ══════════════════════════════════════════════════════════════
# 4) نظافة res_msg بالمصدر
# ══════════════════════════════════════════════════════════════
class TestResMsgCleanup(unittest.TestCase):

    def test_latest_project_id_line_removed(self):
        # النطاق حصرياً بطاقة الاكتمال (latest_line برمز 🧷) — بطاقات handoff/اللقطة
        # خارج النطاق لأن Root/Latest فيهما مختلفان فعلياً لحظة الـ fork (معلومة حقيقية).
        self.assertNotIn("🧷", BRIDGE_SRC)
        # حرفية بطاقة الاكتمال تحديداً (متغير latest_line في شاشة «آخر مشروع» P28 مختلف وخارج النطاق)
        self.assertNotIn("context.get('latest_pid') or pid", BRIDGE_SRC)
        self.assertNotIn("{latest_line}", BRIDGE_SRC)

    def test_resume_url_line_removed(self):
        self.assertNotIn("رابط الاستئناف الحالي", BRIDGE_SRC)

    def test_fork_context_line_removed(self):
        self.assertNotIn("سياق المشروع:</b> تم الحفاظ", BRIDGE_SRC)

    def test_sandbox_path_line_removed(self):
        self.assertNotIn("مسار الساندبوكس", BRIDGE_SRC)

    def test_finished_flag_line_removed(self):
        # سطر العرض 🏁 حُذف (ذكر المصطلح في التعليقات التوثيقية مسموح)
        self.assertNotIn("🏁 <b>علم الانتهاء", BRIDGE_SRC)
        # الاستدعاء اليتيم حُذف مع سطر العرض
        self.assertNotIn("is_finished = check_project_finished_flag", BRIDGE_SRC)

    def test_journey_block_injection_removed(self):
        self.assertNotIn("{journey_block}", BRIDGE_SRC)
        self.assertNotIn('journey_block = f"\\n{journey_line}"', BRIDGE_SRC)

    def test_root_line_still_present(self):
        self.assertIn("Root Project ID:</b>", BRIDGE_SRC)

    def test_essential_lines_still_present(self):
        for token in ["النتيجة النهائية", "رابط الويب اب العام", "الحالة:</b>",
                      "اسم المشروع", "مفتاح المشروع", "📧 <b>الحساب:</b>"]:
            self.assertIn(token, BRIDGE_SRC, f"سطر أساسي مفقود: {token}")


# ══════════════════════════════════════════════════════════════
# 5) Zero-Breaking
# ══════════════════════════════════════════════════════════════
class TestZeroBreaking(unittest.TestCase):

    def test_p29_journey_function_kept(self):
        self.assertTrue(callable(_bridge.format_account_journey_line))
        self.assertEqual(
            _bridge.format_account_journey_line(["a@x.com", "b@x.com"]).count("←"), 1)

    def test_finished_flag_function_kept(self):
        self.assertTrue(callable(_bridge.check_project_finished_flag))
        self.assertTrue(_bridge.check_project_finished_flag("COMPLETED", "FINISHED"))

    def test_p30_span_functions_kept(self):
        for fn in ("open_account_timing_span", "close_account_timing_span",
                   "aggregate_journey_spans_per_email", "format_arabic_duration"):
            self.assertTrue(callable(getattr(_bridge, fn)), fn)

    def test_p38_active_account_line_kept(self):
        line = _bridge.format_active_account_line("x@y.com")
        self.assertIn("📧 <b>الحساب:</b>", line)

    def test_completion_keyboards_untouched(self):
        self.assertIn("build_completed_message_keyboard(pub_url, resume_pid, project_key)", BRIDGE_SRC)
        self.assertIn("build_model_decline_keyboard(pub_url, resume_pid, project_key)", BRIDGE_SRC)

    def test_p34_budget_enforcement_untouched(self):
        self.assertIn("res_msg = enforce_completion_message_budget(res_msg, preview_body)", BRIDGE_SRC)

    def test_credit_counter_increment_untouched(self):
        self.assertEqual(BRIDGE_SRC.count("credit_continuations += 1"), 1)

    def test_new_symbols_exported_for_mirrors(self):
        """رمزا P39 موجودان في p03 (قبل حد 1022) ليصلا للمرايا."""
        idx_const = BRIDGE_SRC.find("PRODUCTIVE_SPAN_MIN_SECONDS = ")
        idx_fn = BRIDGE_SRC.find("def filter_productive_account_entries")
        idx_bc = BRIDGE_SRC.find("class BridgeConfig")
        self.assertGreater(idx_const, 0)
        self.assertGreater(idx_fn, 0)
        self.assertLess(idx_const, idx_bc, "الثابت قبل BridgeConfig (p03)")
        self.assertLess(idx_fn, idx_bc, "الفلتر قبل BridgeConfig (p03)")


# ══════════════════════════════════════════════════════════════
# 6) التسجيل الجنائي
# ══════════════════════════════════════════════════════════════
class TestForensicLogging(unittest.TestCase):

    def test_full_list_logged_before_send(self):
        self.assertIn("[P39] القائمة الكاملة غير المفلترة للحسابات", BRIDGE_SRC)

    def test_logging_is_best_effort_wrapped(self):
        """التسجيل داخل try/except صامت — لا يكسر مسار الرسالة أبداً."""
        seg = BRIDGE_SRC.split("[P39] القائمة الكاملة")[0][-800:]
        self.assertIn("try:", seg)
        after = BRIDGE_SRC.split("[P39] القائمة الكاملة")[1][:300]
        self.assertIn("except Exception:", after)

    def test_forensic_uses_unfiltered_aggregation(self):
        seg_start = BRIDGE_SRC.find("_full_journey = aggregate_journey_spans_per_email")
        self.assertGreater(seg_start, 0, "التسجيل يبني من التجميع الخام غير المفلتر")


# ══════════════════════════════════════════════════════════════
# 7) الحواف
# ══════════════════════════════════════════════════════════════
class TestEdgeCases(unittest.TestCase):

    def test_empty_spans_returns_empty(self):
        self.assertEqual(_bridge.format_account_timing_block(_CfgStub([])), "")
        self.assertEqual(_bridge.format_account_timing_block(None), "")

    def test_html_escaping_in_filtered_list(self):
        block = _bridge.format_account_timing_block(
            _CfgStub([_mk("a<b>&c@x.com", 120)]))
        self.assertIn("a&lt;b&gt;&amp;c@x.com", block)
        self.assertNotIn("<b>&c", block)

    def test_negative_durations_treated_as_zero(self):
        agg = _agg(("neg@x.com", -50, 1), ("ok@x.com", 100, 1))
        filtered, fail_open = _bridge.filter_productive_account_entries(agg, "ok@x.com")
        self.assertFalse(fail_open)
        self.assertEqual([i["email"] for i in filtered], ["ok@x.com"])

    def test_block_never_raises_on_garbage_spans(self):
        cfg = _CfgStub([None, "junk", {"email": None}, _mk("real@x.com", 120)])
        block = _bridge.format_account_timing_block(cfg)
        self.assertIn("real@x.com", block)


if __name__ == "__main__":
    unittest.main(verbosity=2)
