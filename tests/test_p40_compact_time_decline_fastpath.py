#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p40_compact_time_decline_fastpath.py
================================================
⏱️🚫⚡ [P40] حراسة المرحلة 40 — Compact Time UX + Decline Fast-Path Latency
(بروتوكول `14_DECLINE_FAST_PATH_LATENCY.MD` — DEC-036).

العلة المعالجَة: رسالة الرفض 🚫 كانت تتأخر حتى ~225 ثانية لأن
`send_message_and_make_public` كانت تنفّذ `download_project_archive`
(timeout=180) + `make_project_always_public` (حتى 3×15s) على رد رفض بلا
أي ناتج — كشف P35 كان يعيش في الـ worker حصرياً أي بعد دفع كل التكاليف.

المجموعات:
1. TestCompactDuration        — الدالة الجديدة بكل الحواف (جدول المالك حرفياً)
2. TestTimingBlockUsesCompact — الكتلة تستخدم المضغوط في المواضع الثلاثة
3. TestLegacyDurationIntact   — format_arabic_duration باقية بلا مساس
4. TestFastPathSourceGuards   — حراس سورس Fast-Path (نمط حراس P36)
5. TestZeroBreaking           — التسجيل المحلي بلا حراسة + عقود P35/P36 سليمة
"""

import importlib.util
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIDGE_PATH = ROOT / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_p40", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("bridge_p40", _bridge)
_spec.loader.exec_module(_bridge)


class _CfgStub:
    """Stub خفيف بنفس السمات المطلوبة من format_account_timing_block."""
    def __init__(self, spans=None, continuations=0):
        self.account_journey_spans = spans or []
        self.last_credit_continuations = continuations


def _mk(email, dur):
    return {"email": email, "duration_seconds": dur, "closed": True,
            "started_monotonic": 0.0, "started_wall": 0.0}


# ══════════════════════════════════════════════════════════════
# 1) الدالة الجديدة — جدول المالك حرفياً + كل الحواف
# ══════════════════════════════════════════════════════════════
class TestCompactDuration(unittest.TestCase):

    def test_owner_table_45s(self):
        self.assertEqual(_bridge.format_compact_duration(45), "45s")

    def test_owner_table_12m_17s(self):
        self.assertEqual(_bridge.format_compact_duration(737), "12m 17s")

    def test_owner_table_1h_5m(self):
        self.assertEqual(_bridge.format_compact_duration(3900), "1h 5m")

    def test_owner_table_1h_exact_no_zero_minutes(self):
        """لا مكوّن صفري مع مكوّن أكبر — 3600 = «1h» وليس «1h 0m»."""
        self.assertEqual(_bridge.format_compact_duration(3600), "1h")

    def test_exact_minutes_no_zero_seconds(self):
        self.assertEqual(_bridge.format_compact_duration(120), "2m")

    def test_zero_none_negative_junk_all_0s(self):
        """نفس عقد القديمة: لا Crash أبداً في مسار الرسالة النهائية."""
        for bad in (0, None, -10, "junk", "", [], {}):
            self.assertEqual(_bridge.format_compact_duration(bad), "0s",
                             f"المدخل {bad!r} يجب أن يعيد 0s")

    def test_float_seconds_truncated(self):
        self.assertEqual(_bridge.format_compact_duration(59.9), "59s")

    def test_hours_with_seconds_dropped(self):
        """مع الساعات ➔ بلا ثوانٍ أبداً (3661 = 1h 1m وليس 1h 1m 1s)."""
        self.assertEqual(_bridge.format_compact_duration(3661), "1h 1m")

    def test_defined_once_top_level(self):
        defs = re.findall(r"^def format_compact_duration\(", BRIDGE_SRC, re.MULTILINE)
        self.assertEqual(len(defs), 1, "تعريف وحيد top-level — ممنوع التكرار")


# ══════════════════════════════════════════════════════════════
# 2) الكتلة تستخدم المضغوط في المواضع الثلاثة
# ══════════════════════════════════════════════════════════════
class TestTimingBlockUsesCompact(unittest.TestCase):

    def test_per_account_line_compact(self):
        cfg = _CfgStub([_mk("a@x.com", 737)])
        block = _bridge.format_account_timing_block(cfg)
        self.assertIn("12m 17s", block)
        self.assertNotIn("دقيقة", block.split("الزمن الكلي")[0])

    def test_productive_total_compact(self):
        cfg = _CfgStub([_mk("a@x.com", 60), _mk("b@x.com", 60)])
        block = _bridge.format_account_timing_block(cfg)
        self.assertIn("إجمالي زمن التوليد", block)
        self.assertIn("2m", block)

    def test_wall_clock_line_compact(self):
        cfg = _CfgStub([_mk("a@x.com", 90)])
        block = _bridge.format_account_timing_block(cfg, task_total_seconds=2353)
        self.assertIn("الزمن الكلي للمهمة", block)
        self.assertIn("39m 13s", block)

    def test_three_call_sites_in_block_source(self):
        """جسم format_account_timing_block يستدعي المضغوط 3 مرات بالضبط
        ولا يستدعي format_arabic_duration إطلاقاً بعد P40."""
        m = re.search(
            r"^def format_account_timing_block\(.*?(?=^def |\Z)",
            BRIDGE_SRC, re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(m, "الدالة غير موجودة")
        body = m.group(0)
        self.assertEqual(body.count("format_compact_duration("), 3)
        self.assertNotIn("format_arabic_duration(", body)


# ══════════════════════════════════════════════════════════════
# 3) الدالة القديمة باقية بلا مساس (عقد البروتوكول الصريح)
# ══════════════════════════════════════════════════════════════
class TestLegacyDurationIntact(unittest.TestCase):

    def test_legacy_function_still_defined(self):
        self.assertTrue(callable(getattr(_bridge, "format_arabic_duration", None)),
                        "format_arabic_duration يجب أن تبقى — التصدير عبر عقد parity المرايا")

    def test_legacy_behavior_unchanged(self):
        out = _bridge.format_arabic_duration(3600 + 5 * 60)
        self.assertIn("1 ساعة", out)
        self.assertIn("5 دقيقة", out)

    def test_legacy_zero_contract(self):
        self.assertEqual(_bridge.format_arabic_duration(59.9), "59 ثانية")


# ══════════════════════════════════════════════════════════════
# 4) حراس سورس Fast-Path — نمط حراس P36
# ══════════════════════════════════════════════════════════════
def _smapp_body() -> str:
    m = re.search(
        r"^def send_message_and_make_public\(.*?(?=^def send_message_with_auto_account_failover)",
        BRIDGE_SRC, re.MULTILINE | re.DOTALL,
    )
    assert m, "send_message_and_make_public غير موجودة"
    return m.group(0)


class TestFastPathSourceGuards(unittest.TestCase):

    def setUp(self):
        self.body = _smapp_body()

    def test_declined_computed_before_costly_paths(self):
        """`_declined` يُحسب قبل download_project_archive وmake_project_always_public."""
        decl = self.body.find("_declined = final_status == \"COMPLETED\" and is_model_decline_response(last_resp_text)")
        dl = self.body.find("download_project_archive(pid")
        pub = self.body.find("make_project_always_public(pid")
        self.assertGreater(decl, -1, "سطر _declined غير موجود")
        self.assertGreater(dl, decl, "الحساب يجب أن يسبق تنزيل الأرشيف")
        self.assertGreater(pub, decl, "الحساب يجب أن يسبق النشر العام")

    def test_archive_download_guarded(self):
        # [P43] الحارس توسّع حرفياً (وثيقة 17 §4.1): skip_archive = _declined or fast_lean_skip
        # — دلالة P40 محفوظة (الرفض ما زال يتخطى التنزيل دائماً لأنه طرف OR الأول).
        self.assertIn("skip_archive = _declined or fast_lean_skip", self.body,
                      "الرفض يجب أن يبقى الطرف الأول في شرط التخطي (الحدية 5)")
        self.assertRegex(
            self.body,
            r"archive_path = None if skip_archive else download_project_archive\(",
            "تنزيل الأرشيف (timeout=180) يجب أن يُتخطى عند الرفض/الوضع السريع",
        )

    def test_make_public_guarded_with_direct_url_fallback(self):
        """عند الرفض يُبنى الرابط المباشر بلا شبكة — نفس قيمة fallback الدالة المتخطاة.

        [P43-D2] تخطي make_public يبقى حصرياً لفرع `_declined` — الوضع السريع
        (fast_lean_skip) لا يتخطاه أبداً (الحارس على `if _declined:` لا `if skip_archive:`).
        """
        self.assertIn('f"https://www.genspark.ai/autopilotagent_viewer?id={pid}"', self.body)
        idx_if = self.body.find("if _declined:", self.body.find("archive_path = None if skip_archive"))
        idx_else_pub = self.body.find("make_project_always_public(pid", idx_if)
        self.assertGreater(idx_if, -1)
        self.assertGreater(idx_else_pub, idx_if, "النشر العام في فرع else حصرياً")
        # D2: ممنوع توسيع تخطي النشر العام ليشمل fast mode
        self.assertNotIn("if skip_archive:\n            final_public_url", self.body)

    def test_fast_path_logs_early_detection(self):
        self.assertIn("[P40]", self.body, "التسجيل الجنائي للكشف المبكر إلزامي")

    def test_uses_central_p35_detector(self):
        """الكشف حصرياً عبر is_model_decline_response المركزية — ممنوع منطق مكرر."""
        self.assertIn("is_model_decline_response(last_resp_text)", self.body)
        self.assertNotIn("MODEL_DECLINE_MARKERS", self.body,
                         "ممنوع فحص العبارات يدوياً داخل الدالة — الكاشف المركزي فقط")


# ══════════════════════════════════════════════════════════════
# 5) Zero Breaking — التسجيل المحلي وعقود P35/P36/failover سليمة
# ══════════════════════════════════════════════════════════════
class TestZeroBreaking(unittest.TestCase):

    def setUp(self):
        self.body = _smapp_body()

    def test_save_project_branch_unguarded(self):
        """عقد P36 رقم 3: التسجيل المحلي رخيص ويعمل كالمعتاد حتى مع الرفض."""
        idx = self.body.find("save_project_branch(")
        self.assertGreater(idx, -1)
        # المقطع بين نهاية فرع النشر العام واستدعاء save_project_branch
        seg_start = self.body.find("make_project_always_public(pid")
        segment = self.body[seg_start:idx]
        self.assertNotIn("if _declined", segment.split("make_project_always_public(pid", 1)[-1]
                         .split("save_project_branch", 1)[0],
                         "ممنوع حراسة save_project_branch بـ _declined")

    def test_return_contract_unchanged(self):
        """الرجوع بـ pub_url غير فارغ + COMPLETED ⇒ فرع attempt-succeeded في failover كما هو."""
        self.assertIn("return final_public_url, final_status, ext_dir, last_resp_text, None",
                      self.body)

    def test_worker_reclassification_stays_in_worker(self):
        """عقد P35 رقم 2: إعادة التصنيف MODEL_DECLINED في الـ worker حصرياً —
        الدالة لا ترجع MODEL_DECLINED أبداً."""
        self.assertNotIn("MODEL_DECLINED_STATUS", self.body)
        self.assertNotIn('"MODEL_DECLINED"', self.body)
        worker = re.search(
            r"model_declined = status == \"COMPLETED\" and is_model_decline_response\(last_resp_text\)",
            BRIDGE_SRC,
        )
        self.assertIsNotNone(worker, "كشف الـ worker (P35) يجب أن يبقى حرفياً")

    def test_activity_signature_baseline_untouched(self):
        """خارج النطاق عمداً (قرار موثق): fetch_project_activity_signature قبل الحلقة
        لا يُحرس بـ _declined — عقد P18 baseline محفوظ."""
        idx_sig = self.body.find("fetch_project_activity_signature")
        if idx_sig != -1:
            prefix = self.body[max(0, idx_sig - 200):idx_sig]
            self.assertNotIn("_declined", prefix,
                             "ممنوع حراسة التقاط baseline النشاط — قرار خارج النطاق")

    def test_module_compiles(self):
        import py_compile
        py_compile.compile(str(BRIDGE_PATH), doraise=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
