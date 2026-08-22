#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_p34_safe_message_formatting.py
===================================
حزمة حراسة [P34] — Safe Message Formatting and Character Limits:

العقود المحروسة (مستخلصة من الفحص الميداني على السورس الفعلي):
  1. الثوابت المركزية (تعريف وحيد): PREVIEW_MAX_CHARS=1000 /
     PREVIEW_TRUNCATION_SUFFIX / RES_MSG_MAX_CHARS=3500 /
     OUTGOING_TEXT_HARD_LIMIT=3900 / OUTGOING_TEXT_SAFE_LIMIT=3800.
  2. clamp_preview_text: جسم المعاينة ≤ 1000 يمر حرفياً بلا مساس؛
     > 1000 ➔ قصّ إلى 1000 + اللاحقة «... [انقر على الرابط لمشاهدة الرد الكامل]».
  3. enforce_completion_message_budget: رسالة الاكتمال المجمعة لا تتجاوز
     3500 حرفاً أبداً — القصّ يقع على جسم المعاينة أولاً والبيانات التشغيلية
     (الروابط/الحالة/المفاتيح) محفوظة، مع fallback ذيلي أخير.
  4. clamp_outgoing_text في طبقة الإرسال: نص ≤ 3900 يمر حرفياً؛
     نص > 3900 ➔ قصّ آمن إلى ≤ 3800 — و reply_markup (صفوف الأزرار
     التفاعلية) يمر إلى payload الإرسال سليماً بالكامل بلا أي مساس.
  5. سلامة HTML عند نقاط القص: لا وسم <...> مبتور ولا كيان &...; مبتور
     (يمنع 400 Bad Request من تيليجرام).
  6. عقود مصدرية: الحقن في payload["text"] داخل send_telegram_message_detailed +
     استدعاء clamp_preview_text و enforce_completion_message_budget داخل الـ worker +
     اختفاء القصّ القديم 2500/«تم الاقتصاص لزيادة الحجم» نهائياً من الملف النشط.
"""
import importlib.util
import pathlib
import re
import sys
import unittest

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

SRC = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = SRC.read_text(encoding="utf-8")


def _load_bridge():
    spec = importlib.util.spec_from_file_location("bridge_p34", SRC)
    module = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p34"] = module
    spec.loader.exec_module(module)
    return module


bridge = _load_bridge()

SUFFIX = "\n... [انقر على الرابط لمشاهدة الرد الكامل]"


# ═══════════════ 1) الثوابت المركزية ═══════════════
class TestP34Constants(unittest.TestCase):
    def test_01_preview_max_chars_is_1000(self):
        self.assertEqual(bridge.PREVIEW_MAX_CHARS, 1000)

    def test_02_truncation_suffix_exact_text(self):
        self.assertEqual(bridge.PREVIEW_TRUNCATION_SUFFIX, SUFFIX)

    def test_03_res_msg_max_chars_is_3500(self):
        self.assertEqual(bridge.RES_MSG_MAX_CHARS, 3500)

    def test_04_outgoing_hard_limit_is_3900(self):
        self.assertEqual(bridge.OUTGOING_TEXT_HARD_LIMIT, 3900)

    def test_05_outgoing_safe_limit_is_3800(self):
        self.assertEqual(bridge.OUTGOING_TEXT_SAFE_LIMIT, 3800)

    def test_06_constants_defined_once_in_source(self):
        for name in (
            "PREVIEW_MAX_CHARS",
            "RES_MSG_MAX_CHARS",
            "OUTGOING_TEXT_HARD_LIMIT",
            "OUTGOING_TEXT_SAFE_LIMIT",
        ):
            defs = re.findall(rf"^{name}\s*=", BRIDGE_SRC, flags=re.MULTILINE)
            self.assertEqual(len(defs), 1, f"{name} يجب أن يُعرَّف مرة واحدة فقط")

    def test_07_safe_below_hard_below_telegram_4096(self):
        self.assertLess(bridge.OUTGOING_TEXT_SAFE_LIMIT, bridge.OUTGOING_TEXT_HARD_LIMIT)
        self.assertLess(bridge.OUTGOING_TEXT_HARD_LIMIT, 4096)
        self.assertLess(bridge.RES_MSG_MAX_CHARS, bridge.OUTGOING_TEXT_SAFE_LIMIT)


# ═══════════════ 2) clamp_preview_text ═══════════════
class TestClampPreviewText(unittest.TestCase):
    def test_01_short_text_passes_verbatim(self):
        self.assertEqual(bridge.clamp_preview_text("نص قصير"), "نص قصير")

    def test_02_exactly_1000_passes_verbatim_no_suffix(self):
        text = "أ" * 1000
        out = bridge.clamp_preview_text(text)
        self.assertEqual(out, text)
        self.assertNotIn(SUFFIX, out)

    def test_03_over_1000_truncated_with_suffix(self):
        out = bridge.clamp_preview_text("ب" * 1001)
        self.assertTrue(out.endswith(SUFFIX))
        self.assertEqual(out, "ب" * 1000 + SUFFIX)

    def test_04_body_never_exceeds_1000_plus_suffix(self):
        out = bridge.clamp_preview_text("x" * 50000)
        self.assertLessEqual(len(out), 1000 + len(SUFFIX))

    def test_05_none_and_empty_safe(self):
        self.assertEqual(bridge.clamp_preview_text(None), "")
        self.assertEqual(bridge.clamp_preview_text(""), "")

    def test_06_no_partial_html_entity_at_cut(self):
        # كيان &amp; يقع عمداً عند نقطة القص 1000
        text = "y" * 998 + "&amp;" + "z" * 500
        out = bridge.clamp_preview_text(text)
        body = out[: -len(SUFFIX)]
        amp = body.rfind("&")
        if amp != -1:
            self.assertIn(";", body[amp:], "كيان HTML مبتور عند نقطة القص")

    def test_07_no_partial_html_tag_at_cut(self):
        text = "w" * 997 + "<code>" + "v" * 500
        out = bridge.clamp_preview_text(text)
        body = out[: -len(SUFFIX)]
        lt = body.rfind("<")
        if lt != -1:
            self.assertIn(">", body[lt:], "وسم HTML مبتور عند نقطة القص")

    def test_08_old_2500_truncation_gone_from_source(self):
        self.assertNotIn("تم الاقتصاص لزيادة الحجم", BRIDGE_SRC)
        self.assertNotIn('clean_text[:2500]', BRIDGE_SRC)


# ═══════════════ 3) enforce_completion_message_budget ═══════════════
def _build_res_msg(preview_body: str, meta_tail: str = "") -> str:
    """محاكاة حرفية لبنية رسالة الاكتمال: عنوان + معاينة + بيانات تشغيلية."""
    response_preview = (
        f"💬 <b>آخر رسالة من التوليد:</b>\n<pre>{preview_body}</pre>\n\n"
        if preview_body else ""
    )
    return (
        "✅ <b>اكتمل المشروع</b>\n\n"
        f"{response_preview}"
        "🧭 <b>النتيجة النهائية:</b> نجاح\n"
        "🌐 <b>رابط الويب اب العام:</b> https://example.com/app\n"
        "📊 <b>الحالة:</b> <code>COMPLETED</code>\n"
        f"{meta_tail}"
    )


class TestCompletionBudget(unittest.TestCase):
    def test_01_small_message_untouched(self):
        msg = _build_res_msg("معاينة قصيرة")
        self.assertEqual(bridge.enforce_completion_message_budget(msg, "معاينة قصيرة"), msg)

    def test_02_oversized_message_capped_at_3500(self):
        body = bridge.clamp_preview_text("م" * 5000)
        msg = _build_res_msg(body, meta_tail="ت" * 3000)
        out = bridge.enforce_completion_message_budget(msg, body)
        self.assertLessEqual(len(out), 3500)

    def test_03_shrink_hits_preview_first_metadata_preserved(self):
        body = "م" * 1000 + SUFFIX
        msg = _build_res_msg(body, meta_tail="📌 <b>اسم المشروع:</b> اختبار\n" + "ب" * 2500)
        out = bridge.enforce_completion_message_budget(msg, body)
        self.assertLessEqual(len(out), 3500)
        # البيانات التشغيلية (الرابط + الحالة) محفوظة حرفياً
        self.assertIn("https://example.com/app", out)
        self.assertIn("<code>COMPLETED</code>", out)
        self.assertIn("📌 <b>اسم المشروع:</b> اختبار", out)

    def test_04_shrunk_preview_keeps_suffix(self):
        body = "م" * 1000 + SUFFIX
        msg = _build_res_msg(body, meta_tail="ب" * 2600)
        out = bridge.enforce_completion_message_budget(msg, body)
        self.assertIn(SUFFIX, out)

    def test_05_no_preview_fallback_tail_trim(self):
        msg = "س" * 4000
        out = bridge.enforce_completion_message_budget(msg, "")
        self.assertLessEqual(len(out), 3500)
        self.assertEqual(out, "س" * 3500)

    def test_06_none_and_empty_safe(self):
        self.assertEqual(bridge.enforce_completion_message_budget(None), "")
        self.assertEqual(bridge.enforce_completion_message_budget("", ""), "")

    def test_07_extreme_overflow_always_capped(self):
        body = bridge.clamp_preview_text("م" * 100000)
        msg = _build_res_msg(body, meta_tail="ت" * 100000)
        out = bridge.enforce_completion_message_budget(msg, body)
        self.assertLessEqual(len(out), 3500)

    def test_08_result_is_idempotent(self):
        body = bridge.clamp_preview_text("م" * 5000)
        msg = _build_res_msg(body, meta_tail="ت" * 3000)
        once = bridge.enforce_completion_message_budget(msg, body)
        twice = bridge.enforce_completion_message_budget(once, body)
        self.assertEqual(once, twice)


# ═══════════════ 4) clamp_outgoing_text (طبقة الإرسال) ═══════════════
class TestClampOutgoingText(unittest.TestCase):
    def test_01_short_text_passes_verbatim(self):
        self.assertEqual(bridge.clamp_outgoing_text("مرحبا"), "مرحبا")

    def test_02_exactly_3900_passes_verbatim(self):
        text = "أ" * 3900
        self.assertEqual(bridge.clamp_outgoing_text(text), text)

    def test_03_over_3900_trimmed_to_3800_or_less(self):
        out = bridge.clamp_outgoing_text("ب" * 3901)
        self.assertLessEqual(len(out), 3800)
        self.assertEqual(out, "ب" * 3800)

    def test_04_huge_text_trimmed(self):
        out = bridge.clamp_outgoing_text("x" * 100000)
        self.assertLessEqual(len(out), 3800)

    def test_05_none_and_empty_safe(self):
        self.assertEqual(bridge.clamp_outgoing_text(None), "")
        self.assertEqual(bridge.clamp_outgoing_text(""), "")

    def test_06_no_partial_html_tag_at_trim_point(self):
        text = "w" * 3797 + "<code>" + "v" * 500
        out = bridge.clamp_outgoing_text(text)
        lt = out.rfind("<")
        if lt != -1:
            self.assertIn(">", out[lt:], "وسم HTML مبتور عند نقطة القص 3800")

    def test_07_between_3801_and_3900_untouched(self):
        text = "ج" * 3850
        self.assertEqual(bridge.clamp_outgoing_text(text), text)


class TestSenderKeepsButtonsIntact(unittest.TestCase):
    """التحقق الحي: الإرسال بنص > 3900 يقصّ text فقط و reply_markup يمر سليماً."""

    def setUp(self):
        self._orig_token = bridge.TELEGRAM_BOT_TOKEN
        bridge.TELEGRAM_BOT_TOKEN = "123456:TEST-TOKEN-P34"
        self._orig_call = bridge._call_telegram_api_json
        self.captured = []

        def fake_call(method, payload, timeout=15):
            self.captured.append({"method": method, "payload": dict(payload)})
            return {"ok": True, "status_code": 200, "result": {"message_id": 777},
                    "description": "", "error": ""}

        bridge._call_telegram_api_json = fake_call

    def tearDown(self):
        bridge.TELEGRAM_BOT_TOKEN = self._orig_token
        bridge._call_telegram_api_json = self._orig_call

    def _keyboard(self):
        return {"inline_keyboard": [
            [{"text": "🌐 فتح المعاين المباشر", "url": "https://example.com/v"}],
            [{"text": "▶️ كمل الآن", "callback_data": "cont:prj_p34"}],
            [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:dashboard"}],
        ]}

    def test_01_long_text_trimmed_in_payload(self):
        bridge.send_telegram_message_detailed(999, "ن" * 5000, reply_markup=self._keyboard())
        payload = self.captured[-1]["payload"]
        self.assertLessEqual(len(payload["text"]), 3800)

    def test_02_reply_markup_rows_fully_intact(self):
        import json
        kb = self._keyboard()
        bridge.send_telegram_message_detailed(999, "ن" * 5000, reply_markup=kb)
        payload = self.captured[-1]["payload"]
        sent_kb = json.loads(payload["reply_markup"])
        self.assertEqual(sent_kb, kb, "صفوف الأزرار يجب أن تمر حرفياً بلا مساس")

    def test_03_short_text_not_modified(self):
        bridge.send_telegram_message_detailed(999, "رسالة عادية", reply_markup=self._keyboard())
        self.assertEqual(self.captured[-1]["payload"]["text"], "رسالة عادية")

    def test_04_boolean_wrapper_still_works(self):
        ok = bridge.send_telegram_message(999, "ت" * 4500, reply_markup=self._keyboard())
        self.assertTrue(ok)
        self.assertLessEqual(len(self.captured[-1]["payload"]["text"]), 3800)


# ═══════════════ 5) عقود المصدر (Source Contracts) ═══════════════
class TestP34SourceContracts(unittest.TestCase):
    def test_01_sender_payload_uses_clamp(self):
        self.assertIn('"text": clamp_outgoing_text(text)', BRIDGE_SRC)

    def test_02_worker_uses_clamp_preview_text(self):
        self.assertIn("clean_text = clamp_preview_text(clean_text)", BRIDGE_SRC)

    def test_03_worker_enforces_res_msg_budget(self):
        self.assertIn(
            "res_msg = enforce_completion_message_budget(res_msg, preview_body)",
            BRIDGE_SRC,
        )

    def test_04_budget_enforced_before_send(self):
        idx_budget = BRIDGE_SRC.index("res_msg = enforce_completion_message_budget(res_msg, preview_body)")
        idx_send = BRIDGE_SRC.index("send_telegram_message(chat_id, res_msg, reply_markup=reply_markup)")
        self.assertLess(idx_budget, idx_send, "فرض الميزانية يجب أن يسبق الإرسال")

    def test_05_functions_defined_once(self):
        for fn in (
            "clamp_preview_text",
            "enforce_completion_message_budget",
            "clamp_outgoing_text",
            "_strip_partial_html_token",
        ):
            defs = re.findall(rf"^def {fn}\(", BRIDGE_SRC, flags=re.MULTILINE)
            self.assertEqual(len(defs), 1, f"{fn} يجب أن تُعرَّف مرة واحدة فقط")

    def test_06_preview_body_captured_for_budget(self):
        self.assertIn("preview_body = clean_text", BRIDGE_SRC)

    def test_07_refactor_mirror_has_p34_symbols(self):
        from bridge_refactor import runtime
        for name in (
            "clamp_preview_text",
            "enforce_completion_message_budget",
            "clamp_outgoing_text",
            "PREVIEW_MAX_CHARS",
            "RES_MSG_MAX_CHARS",
        ):
            self.assertIn(name, runtime.ns, f"{name} مفقود من مرآة bridge_refactor")


if __name__ == "__main__":
    unittest.main()
