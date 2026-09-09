#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p42_intent_guard_and_safe_creation.py
=================================================
🛡️ [P42] حراسة المرحلة 42 — Intent Guard & Safe Project Creation Flow
(وثيقة `16_INTENT_GUARD_AND_SAFE_CREATION.MD` — DEC-038).

العلة المعالجة (Live Bug): الـ Fallback الأعمى «أي نص غير مفهوم في IDLE =
مشروع جديد تلقائياً» كان يولّد مفتاحاً ويسجّل مشروعاً ويحجز حساباً حقيقياً
ويبدأ توليداً فعلياً على نص عابر مثل "2+7=" — الآن حُذف من الوجود واستُبدل
بـ Intent Guard: بطاقة تأكيد إلزامية (Confirmation before ANY Mutation)،
والنص يعيش في user_state (pending_prompt) والزر يحمل nonce فقط.

المجموعات:
1. TestIntentClassification    — classify_idle_text_intent (نقية: strong/ambiguous)
2. TestConfirmationKeyboard    — الكيبورد: nonce لا نص + حد 64 بايت + تعقيم
3. TestConfirmationCard        — نص البطاقة: اقتباس مُهرَّب + قصّ العرض + التلميحان
4. TestIdleGuardBehavior       — handle_idle_intent_guard: الحالة/الرفض المهذب/صفر Mutation
5. TestFallbackRemoval         — حراس سورس + E2E: استحالة الإنشاء التلقائي من IDLE
6. TestConfirmCallback         — pconf:yes/no — nonce مطابق/Stale/Double-Click/إلغاء
7. TestCardInvalidation        — نص جديد/رابط مشروع/رابط مشوّه/أمر أثناء البطاقة
8. TestSmartPromptForwarding   — forward_pending_prompt_after_wizard + حمل الـ Wizard
9. TestExplicitCreationUnchanged — cmd:new_proj والمسار المباشر بلا أي تغيير
10. TestZeroRegression         — العقود المجمّدة (P41/Success/Resume/Keyboards)

(كله عبر Mocks/Spies — بدون شبكة حقيقية أو حسابات حقيقية أو كتابة سجل.)
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

_spec = importlib.util.spec_from_file_location("bridge_p42", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("bridge_p42", _bridge)
_spec.loader.exec_module(_bridge)

CHAT = 1124247595  # ضمن ALLOWED_CHAT_IDS الافتراضية
VALID_PID = "abcdefab-1111-2222-3333-444444444444"
PROJECT_URL = f"https://www.genspark.ai/agents?id={VALID_PID}"
MALFORMED_URL = "https://www.genspark.ai/agents?id=not-a-uuid"


def _msg_update(text: str) -> dict:
    """تحديث message نصي قياسي من شات مسموح."""
    return {"message": {"chat": {"id": CHAT}, "from": {"id": CHAT}, "text": text}}


def _cb_update(data: str, message_id: int = 55) -> dict:
    """تحديث callback_query قياسي من شات مسموح."""
    return {
        "callback_query": {
            "message": {"chat": {"id": CHAT}, "message_id": message_id},
            "from": {"id": CHAT},
            "data": data,
        }
    }


class _MutationSpiesMixin:
    """عزل كامل: تصفير user_state + Spies على كل الحدود الخمسة للطفرات.

    أي وصول لـ EXECUTOR.submit / process_user_task_async /
    claim_account_selection / ProjectRegistry أثناء مسار الـ Guard =
    فشل فوري (Zero Pollution — بوابة قبول Phase 42 رقم 4).
    """

    def setUp(self):
        _bridge.USER_STATE_STORE.clear()
        self._patchers = [
            mock.patch.object(_bridge, "send_telegram_message"),
            mock.patch.object(_bridge, "edit_telegram_message_reply_markup"),
            mock.patch.object(_bridge.EXECUTOR, "submit"),
            mock.patch.object(_bridge, "process_user_task_async"),
            mock.patch.object(_bridge, "claim_account_selection"),
            mock.patch.object(_bridge, "ProjectRegistry"),
            mock.patch.object(_bridge, "log_event"),
        ]
        (self.send, self.edit_markup, self.submit, self.task,
         self.claim, self.registry, self.logev) = [p.start() for p in self._patchers]

    def tearDown(self):
        for p in self._patchers:
            p.stop()
        _bridge.USER_STATE_STORE.clear()

    def assert_zero_mutation(self):
        """صفر مشروع / صفر تسجيل / صفر حجز حساب / صفر توليد."""
        self.submit.assert_not_called()
        self.task.assert_not_called()
        self.claim.assert_not_called()
        self.registry.assert_not_called()

    def state(self) -> dict:
        return _bridge.get_user_state(CHAT)

    def functional_state(self) -> dict:
        """الحالة الوظيفية بلا مفتاح ts الإداري (set_user_state يضيفه دائماً)."""
        return {k: v for k, v in self.state().items() if k != "ts"}


# ═══════════════════════════════════════════════════════════════
# 1. تصنيف النية — دالة نقية بلا أي أثر جانبي
# ═══════════════════════════════════════════════════════════════
class TestIntentClassification(unittest.TestCase):

    def test_01_evidence_cases_are_ambiguous(self):
        """حالات الأدلة الثلاث من بيان المشكلة: 2+7= / 63636 / 121."""
        for evidence in ("2+7=", "63636", "121"):
            self.assertEqual(_bridge.classify_idle_text_intent(evidence), "ambiguous", evidence)

    def test_02_real_project_prompt_is_strong(self):
        prompt = "ابنِ لي موقعاً لعرض منتجات متجر إلكتروني مع سلة شراء وصفحة دفع"
        self.assertEqual(_bridge.classify_idle_text_intent(prompt), "strong")

    def test_03_short_text_is_ambiguous(self):
        self.assertEqual(_bridge.classify_idle_text_intent("hello"), "ambiguous")

    def test_04_long_but_few_words_is_ambiguous(self):
        """≥ 20 حرفاً لكن أقل من 4 كلمات ⟔ ambiguous (شرطا العتبة معاً)."""
        self.assertEqual(_bridge.classify_idle_text_intent("a" * 40), "ambiguous")

    def test_05_many_words_but_short_is_ambiguous(self):
        self.assertEqual(_bridge.classify_idle_text_intent("a b c d e"), "ambiguous")

    def test_06_exact_thresholds_are_strong(self):
        """الحد الأدنى بالضبط (20 حرفاً + 4 كلمات) ⟔ strong."""
        text = "abcde abcde abcd abc"  # 20 حرفاً و 4 كلمات
        self.assertEqual(len(text), _bridge.INTENT_GUARD_STRONG_MIN_CHARS)
        self.assertEqual(len(text.split()), _bridge.INTENT_GUARD_STRONG_MIN_WORDS)
        self.assertEqual(_bridge.classify_idle_text_intent(text), "strong")

    def test_07_none_and_empty_are_ambiguous(self):
        self.assertEqual(_bridge.classify_idle_text_intent(None), "ambiguous")
        self.assertEqual(_bridge.classify_idle_text_intent("   "), "ambiguous")

    def test_08_constants_are_top_level(self):
        """Edge 8: لا Hardcoding — الثوابت معرّفة top-level."""
        for const in (
            "AWAITING_PROJECT_CONFIRMATION", "PROJECT_CONFIRM_CALLBACK_PREFIX",
            "INTENT_GUARD_STRONG_MIN_CHARS", "INTENT_GUARD_STRONG_MIN_WORDS",
            "INTENT_GUARD_QUOTE_PREVIEW_LIMIT", "INTENT_GUARD_STRONG_HINT",
            "INTENT_GUARD_AMBIGUOUS_HINT", "INTENT_GUARD_EMPTY_MESSAGE",
            "INTENT_GUARD_EXPIRED_MESSAGE", "INTENT_GUARD_ALREADY_CONFIRMED_MESSAGE",
            "INTENT_GUARD_CANCELLED_MESSAGE", "PROJECT_CONFIRM_YES_LABEL",
            "PROJECT_CONFIRM_NO_LABEL",
        ):
            self.assertTrue(hasattr(_bridge, const), f"ثابت مفقود: {const}")


# ═══════════════════════════════════════════════════════════════
# 2. كيبورد البطاقة — nonce لا نص (Edge 1 + Edge 2)
# ═══════════════════════════════════════════════════════════════
class TestConfirmationKeyboard(unittest.TestCase):

    def test_01_two_buttons_with_nonce(self):
        kb = _bridge.build_project_confirmation_keyboard("deadbeef1234")
        rows = kb["inline_keyboard"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0]["callback_data"], "pconf:yes:deadbeef1234")
        self.assertEqual(rows[1][0]["callback_data"], "pconf:no:deadbeef1234")
        self.assertEqual(rows[0][0]["text"], _bridge.PROJECT_CONFIRM_YES_LABEL)
        self.assertEqual(rows[1][0]["text"], _bridge.PROJECT_CONFIRM_NO_LABEL)

    def test_02_callback_data_within_64_bytes(self):
        """Edge 2: حد Telegram — الزر يحمل المعرف لا النص."""
        kb = _bridge.build_project_confirmation_keyboard("a" * 12)
        for row in kb["inline_keyboard"]:
            for btn in row:
                self.assertLessEqual(len(btn["callback_data"].encode("utf-8")), 64)

    def test_03_nonce_is_sanitized_and_clamped(self):
        """حقن نص خبيث/طويل في الـ nonce ⟔ تعقيم hex-only وقصّ لـ 12."""
        kb = _bridge.build_project_confirmation_keyboard("ZZ<b>deadbeef1234extra</b>")
        cb = kb["inline_keyboard"][0][0]["callback_data"]
        nonce_part = cb.split(":", 2)[2]
        self.assertRegex(nonce_part, r"^[a-f0-9]{0,12}$")
        self.assertLessEqual(len(nonce_part), 12)

    def test_04_prompt_text_never_in_callback_data(self):
        """النص يعيش في user_state فقط — الكيبورد لا يحمل أي جزء منه."""
        kb = _bridge.build_project_confirmation_keyboard("deadbeef1234")
        flat = str(kb)
        self.assertNotIn("pending_prompt", flat)
        self.assertNotIn("2+7=", flat)


# ═══════════════════════════════════════════════════════════════
# 3. نص البطاقة — اقتباس حرفي مُهرَّب + التلميحان (Edge 7)
# ═══════════════════════════════════════════════════════════════
class TestConfirmationCard(unittest.TestCase):

    def test_01_quotes_received_text_verbatim(self):
        card = _bridge.render_project_confirmation_card("2+7=", "ambiguous")
        self.assertIn("2+7=", card)
        self.assertIn("النص المستلم", card)

    def test_02_html_is_escaped(self):
        card = _bridge.render_project_confirmation_card("<script>alert(1)</script>", "ambiguous")
        self.assertNotIn("<script>", card)
        self.assertIn("&lt;script&gt;", card)

    def test_03_hint_differs_behavior_same(self):
        """Edge 7: Strong و Ambiguous يختلفان في الصياغة فقط."""
        strong = _bridge.render_project_confirmation_card("x", "strong")
        ambiguous = _bridge.render_project_confirmation_card("x", "ambiguous")
        self.assertIn(_bridge.INTENT_GUARD_STRONG_HINT, strong)
        self.assertIn(_bridge.INTENT_GUARD_AMBIGUOUS_HINT, ambiguous)
        # جسم البطاقة (بعد التلميح) متطابق — سلوك واحد
        self.assertEqual(strong.split("\n", 1)[1], ambiguous.split("\n", 1)[1])

    def test_04_long_text_clamped_for_display_only(self):
        long_text = "كلمة " * 300
        card = _bridge.render_project_confirmation_card(long_text, "strong")
        self.assertIn("…", card)
        self.assertLess(len(card), len(long_text))

    def test_05_no_mutation_promise_present(self):
        card = _bridge.render_project_confirmation_card("x", "strong")
        self.assertIn("لن يُنشأ أي مشروع ولن يُحجز أي حساب", card)


# ═══════════════════════════════════════════════════════════════
# 4. سلوك الحارس — الحالة + الرفض المهذب + صفر Mutation
# ═══════════════════════════════════════════════════════════════
class TestIdleGuardBehavior(_MutationSpiesMixin, unittest.TestCase):

    def test_01_sets_confirmation_state_with_full_prompt(self):
        _bridge.handle_idle_intent_guard(CHAT, "2+7=")
        st = self.state()
        self.assertEqual(st.get("action"), _bridge.AWAITING_PROJECT_CONFIRMATION)
        self.assertEqual(st.get("pending_prompt"), "2+7=")
        self.assertRegex(st.get("confirm_nonce", ""), r"^[a-f0-9]{12}$")

    def test_02_long_prompt_kept_full_in_state(self):
        """القصّ للعرض فقط — pending_prompt يُحفظ كاملاً."""
        long_text = "كلمة " * 300
        _bridge.handle_idle_intent_guard(CHAT, long_text)
        self.assertEqual(self.state().get("pending_prompt"), long_text.strip())

    def test_03_card_sent_with_nonce_keyboard(self):
        _bridge.handle_idle_intent_guard(CHAT, "hello")
        self.send.assert_called_once()
        kwargs = self.send.call_args.kwargs
        nonce = self.state()["confirm_nonce"]
        self.assertIn(f"pconf:yes:{nonce}", str(kwargs.get("reply_markup")))

    def test_04_empty_text_polite_refusal_no_state(self):
        """Edge 3: رسالة بلا نص ⟔ رفض مهذب بلا بطاقة ولا حالة."""
        _bridge.handle_idle_intent_guard(CHAT, "   ")
        self.assertEqual(self.state(), {})
        self.send.assert_called_once_with(CHAT, _bridge.INTENT_GUARD_EMPTY_MESSAGE)

    def test_05_guard_is_mutation_free(self):
        """الحارس لا يملك أي صلاحية وصول للحدود الخمسة."""
        for text in ("2+7=", "63636", "121", "hello", "", "ابنِ لي متجراً إلكترونياً كاملاً الآن"):
            _bridge.handle_idle_intent_guard(CHAT, text)
        self.assert_zero_mutation()

    def test_06_telemetry_shown_logged(self):
        """Edge 9: سطر Log واضح عند قرار SHOWN."""
        _bridge.handle_idle_intent_guard(CHAT, "hello")
        logged = " | ".join(str(c.args) for c in self.logev.call_args_list)
        self.assertIn("SHOWN", logged)


# ═══════════════════════════════════════════════════════════════
# 5. حذف الـ Fallback — حراس سورس + E2E عبر handle_telegram_update
# ═══════════════════════════════════════════════════════════════
class TestFallbackRemoval(_MutationSpiesMixin, unittest.TestCase):

    def test_01_source_tail_calls_guard_exclusively(self):
        """ذيل فرع الرسالة: بعد توجيه الروابط لا يوجد إلا استدعاء الحارس."""
        tail_start = BRIDGE_SRC.rindex("present_external_resume_decision(chat_id, target_url=ctx[\"target_url\"], target_pid=ctx[\"pid\"])")
        tail = BRIDGE_SRC[tail_start:BRIDGE_SRC.index("def load_telegram_offset")]
        self.assertIn("handle_idle_intent_guard(chat_id, text)", tail)
        self.assertNotIn("EXECUTOR.submit", tail)
        self.assertNotIn("process_user_task_async", tail)

    def test_02_source_no_auto_project_fallback_markers(self):
        """بصمات الـ Fallback القديم (اسم تلقائي + جدولة مباشرة من IDLE) غير موجودة."""
        # الاستدعاءات الشرعية الوحيدة لـ process_user_task_async داخل فرع message:
        # AWAITING_NEW_PROMPT / AWAITING_CONT_PROMPT / forward_pending_prompt_after_wizard
        msg_branch = BRIDGE_SRC[BRIDGE_SRC.index('if "message" in update:'):BRIDGE_SRC.index("def load_telegram_offset")]
        submit_count = msg_branch.count("EXECUTOR.submit(process_user_task_async")
        self.assertEqual(submit_count, 2, "فرع message يجب أن يجدول من فرعي البرومبت النشطين فقط")

    def test_03_e2e_evidence_texts_no_create(self):
        """Idle + '2+7=' / '63636' / '121' ⟔ NO CREATE إطلاقاً."""
        for evidence in ("2+7=", "63636", "121"):
            _bridge.USER_STATE_STORE.clear()
            _bridge.handle_telegram_update(_msg_update(evidence))
            st = self.state()
            self.assertEqual(st.get("action"), _bridge.AWAITING_PROJECT_CONFIRMATION, evidence)
            self.assertEqual(st.get("pending_prompt"), evidence)
        self.assert_zero_mutation()

    def test_04_e2e_hello_shows_card_no_create(self):
        """Idle + 'hello' ⟔ بطاقة تأكيد بلا أي إنشاء."""
        _bridge.handle_telegram_update(_msg_update("hello"))
        self.assertEqual(self.state().get("action"), _bridge.AWAITING_PROJECT_CONFIRMATION)
        sent_text = str(self.send.call_args.args)
        self.assertIn("hello", sent_text)
        self.assert_zero_mutation()

    def test_05_e2e_non_text_message_polite_refusal(self):
        """Edge 3: رسالة IDLE بلا نص (ستيكر/صورة) ⟔ رفض مهذب بلا تسرب."""
        _bridge.handle_telegram_update({"message": {"chat": {"id": CHAT}, "from": {"id": CHAT}, "sticker": {"file_id": "x"}}})
        self.assertEqual(self.state(), {})
        self.send.assert_called_once_with(CHAT, _bridge.INTENT_GUARD_EMPTY_MESSAGE)
        self.assert_zero_mutation()


# ═══════════════════════════════════════════════════════════════
# 6. معالج pconf — التأكيد/الإلغاء/Stale/Double-Click (Edges 1+4)
# ═══════════════════════════════════════════════════════════════
class TestConfirmCallback(_MutationSpiesMixin, unittest.TestCase):

    def _arm_card(self, prompt: str = "ابنِ لي متجراً إلكترونياً متكاملاً رجاءً") -> str:
        _bridge.handle_idle_intent_guard(CHAT, prompt)
        nonce = self.state()["confirm_nonce"]
        self.send.reset_mock()
        self.logev.reset_mock()
        return nonce

    def test_01_confirm_enters_official_wizard(self):
        """تأكيد ⟔ AWAITING_NEW_PROJECT_NAME (الـ Wizard القائم — DRY) بلا Mutation."""
        nonce = self._arm_card("برومبت مشروع حقيقي بأربع كلمات على الأقل")
        _bridge.handle_telegram_update(_cb_update(f"pconf:yes:{nonce}"))
        st = self.state()
        self.assertEqual(st.get("action"), "AWAITING_NEW_PROJECT_NAME")
        self.assertEqual(st.get("pending_prompt"), "برومبت مشروع حقيقي بأربع كلمات على الأقل")
        self.assertEqual(st.get("consumed_confirm_nonce"), nonce)
        self.assert_zero_mutation()

    def test_02_confirm_disarms_card_buttons(self):
        nonce = self._arm_card()
        _bridge.handle_telegram_update(_cb_update(f"pconf:yes:{nonce}", message_id=77))
        self.edit_markup.assert_called_once_with(CHAT, 77, None)

    def test_03_double_click_is_idempotent(self):
        """Edge 4: الضغطة الثانية ⟔ 'تم بالفعل' بلا أي Mutation إضافي."""
        nonce = self._arm_card()
        _bridge.handle_telegram_update(_cb_update(f"pconf:yes:{nonce}"))
        st_after_first = dict(self.state())
        self.send.reset_mock()
        _bridge.handle_telegram_update(_cb_update(f"pconf:yes:{nonce}"))
        self.assertEqual(self.state(), st_after_first)  # الحالة لم تُمس
        self.send.assert_called_once_with(CHAT, _bridge.INTENT_GUARD_ALREADY_CONFIRMED_MESSAGE)
        self.assert_zero_mutation()

    def test_04_stale_nonce_rejected_no_mutation(self):
        """Edge 1: nonce قديم لا يطابق آخر بطاقة نشطة ⟔ 'انتهت الصلاحية'."""
        stale = self._arm_card("النص الأول قبل تجديد البطاقة الحالية")
        _bridge.handle_idle_intent_guard(CHAT, "النص الثاني الذي جدد البطاقة والمعرف")  # nonce جديد
        self.send.reset_mock()
        _bridge.handle_telegram_update(_cb_update(f"pconf:yes:{stale}"))
        # الحالة الجديدة باقية على البطاقة الثانية — الضغطة القديمة لم تغير شيئاً
        self.assertEqual(self.state().get("action"), _bridge.AWAITING_PROJECT_CONFIRMATION)
        self.send.assert_called_once_with(CHAT, _bridge.INTENT_GUARD_EXPIRED_MESSAGE)
        self.assert_zero_mutation()

    def test_05_cancel_leaves_zero_trace(self):
        """إلغاء ⟔ user_state نظيف + صفر مشروع/تسجيل/حجز/توليد."""
        nonce = self._arm_card()
        _bridge.handle_telegram_update(_cb_update(f"pconf:no:{nonce}"))
        self.assertEqual(self.functional_state(), {})
        self.send.assert_called_once_with(CHAT, _bridge.INTENT_GUARD_CANCELLED_MESSAGE)
        self.assert_zero_mutation()

    def test_06_cancel_on_stale_card_expired(self):
        stale = self._arm_card()
        _bridge.handle_idle_intent_guard(CHAT, "نص جديد أبطل البطاقة الأولى تماماً")
        self.send.reset_mock()
        _bridge.handle_telegram_update(_cb_update(f"pconf:no:{stale}"))
        self.assertEqual(self.state().get("action"), _bridge.AWAITING_PROJECT_CONFIRMATION)
        self.send.assert_called_once_with(CHAT, _bridge.INTENT_GUARD_EXPIRED_MESSAGE)
        self.assert_zero_mutation()

    def test_07_confirm_without_any_state_expired(self):
        """ضغطة على بطاقة من جلسة منتهية (state فارغة) ⟔ رفض آمن."""
        _bridge.handle_telegram_update(_cb_update("pconf:yes:deadbeef1234"))
        self.assertEqual(self.state(), {})
        self.send.assert_called_once_with(CHAT, _bridge.INTENT_GUARD_EXPIRED_MESSAGE)
        self.assert_zero_mutation()

    def test_08_malicious_nonce_sanitized(self):
        """حقن قيمة غير hex في الـ callback ⟔ تعقيم ورفض بلا كسر."""
        self._arm_card()
        _bridge.handle_telegram_update(_cb_update("pconf:yes:<injected>"))
        self.send.assert_called_once_with(CHAT, _bridge.INTENT_GUARD_EXPIRED_MESSAGE)
        self.assert_zero_mutation()

    def test_09_telemetry_confirmed_cancelled_expired(self):
        """Edge 9: قرارات CONFIRMED / CANCELLED / EXPIRED مسجلة باللوج."""
        nonce = self._arm_card()
        _bridge.handle_telegram_update(_cb_update(f"pconf:yes:{nonce}"))
        nonce2_prompt = _bridge.handle_idle_intent_guard(CHAT, "نص جديد لبطاقة ثانية للإلغاء")
        del nonce2_prompt
        nonce2 = self.state()["confirm_nonce"]
        _bridge.handle_telegram_update(_cb_update(f"pconf:no:{nonce2}"))
        _bridge.handle_telegram_update(_cb_update("pconf:yes:deadbeef9999"))
        logged = " | ".join(str(c.args) for c in self.logev.call_args_list)
        for marker in ("CONFIRMED", "CANCELLED", "EXPIRED"):
            self.assertIn(marker, logged)


# ═══════════════════════════════════════════════════════════════
# 7. إبطال البطاقة — نص جديد/رابط/رابط مشوّه/أمر (Edges 5+6 + التجاهل)
# ═══════════════════════════════════════════════════════════════
class TestCardInvalidation(_MutationSpiesMixin, unittest.TestCase):

    def _arm_card(self) -> str:
        _bridge.handle_idle_intent_guard(CHAT, "النص الأول للبطاقة الأولى هنا")
        nonce = self.state()["confirm_nonce"]
        self.send.reset_mock()
        return nonce

    def test_01_new_text_reissues_card_with_new_nonce(self):
        """تجاهل: نص جديد أثناء البطاقة ⟔ إبطال ضمني + بطاقة جديدة بـ nonce جديد."""
        old_nonce = self._arm_card()
        _bridge.handle_telegram_update(_msg_update("نص ثانٍ مختلف تماماً عن الأول"))
        st = self.state()
        self.assertEqual(st.get("action"), _bridge.AWAITING_PROJECT_CONFIRMATION)
        self.assertEqual(st.get("pending_prompt"), "نص ثانٍ مختلف تماماً عن الأول")
        self.assertNotEqual(st.get("confirm_nonce"), old_nonce)
        self.assert_zero_mutation()

    def test_02_project_url_wins_and_clears_card(self):
        """Edge 6: رابط مشروع أثناء البطاقة ⟔ منطق P41 يفوز والحالة تُغلق."""
        self._arm_card()
        with mock.patch.object(_bridge, "resolve_resume_context",
                               return_value={"project_key": "prj_x", "target_url": PROJECT_URL, "pid": VALID_PID}) as res, \
             mock.patch.object(_bridge, "present_resume_summary") as summ:
            _bridge.handle_telegram_update(_msg_update(PROJECT_URL))
            res.assert_called_once()
            summ.assert_called_once_with(CHAT, project_key="prj_x", target_url=PROJECT_URL, target_pid=VALID_PID)
        self.assertEqual(self.functional_state(), {})
        self.assert_zero_mutation()

    def test_03_external_url_routes_to_external_decision(self):
        self._arm_card()
        with mock.patch.object(_bridge, "resolve_resume_context",
                               return_value={"project_key": "", "target_url": PROJECT_URL, "pid": VALID_PID}), \
             mock.patch.object(_bridge, "present_external_resume_decision") as ext:
            _bridge.handle_telegram_update(_msg_update(PROJECT_URL))
            ext.assert_called_once_with(CHAT, target_url=PROJECT_URL, target_pid=VALID_PID)
        self.assertEqual(self.functional_state(), {})
        self.assert_zero_mutation()

    def test_04_malformed_url_explicit_refusal(self):
        """رابط مشوّه أثناء البطاقة ⟔ رفض صريح (رسالة P41) + إغلاق الحالة."""
        self._arm_card()
        _bridge.handle_telegram_update(_msg_update(MALFORMED_URL))
        self.assertEqual(self.functional_state(), {})
        self.send.assert_called_once_with(CHAT, _bridge.MALFORMED_PROJECT_LINK_MESSAGE)
        self.assert_zero_mutation()

    def test_05_command_wins_over_card(self):
        """Edge 5: /start أثناء البطاقة ⟔ الأمر يفوز (يُفحص قبل الحالات بنيوياً)."""
        self._arm_card()
        with mock.patch.object(_bridge, "render_dashboard_text", return_value="dash"), \
             mock.patch.object(_bridge, "get_main_keyboard", return_value={}):
            _bridge.handle_telegram_update(_msg_update("/start"))
        sent = str(self.send.call_args.args)
        self.assertIn("dash", sent)
        self.assert_zero_mutation()

    def test_06_source_command_check_precedes_state_chain(self):
        """حارس سورس: فحص /start و /help يسبق get_user_state في فرع الرسالة."""
        msg_branch = BRIDGE_SRC[BRIDGE_SRC.index('if "message" in update:'):]
        cmd_pos = msg_branch.index('if text in ["/start", "/help"]')
        state_pos = msg_branch.index("state = get_user_state(chat_id)")
        self.assertLess(cmd_pos, state_pos)

    def test_07_stale_button_after_invalidation_expired(self):
        """ضغط زر بطاقة مُبطلة (بعد نص جديد) ⟔ 'انتهت الصلاحية' بلا Mutation."""
        stale = self._arm_card()
        _bridge.handle_telegram_update(_msg_update("نص جديد يبطل البطاقة الأولى الآن"))
        self.send.reset_mock()
        _bridge.handle_telegram_update(_cb_update(f"pconf:yes:{stale}"))
        self.send.assert_called_once_with(CHAT, _bridge.INTENT_GUARD_EXPIRED_MESSAGE)
        self.assert_zero_mutation()


# ═══════════════════════════════════════════════════════════════
# 8. Smart Prompt Forwarding — تمرير البرومبت بعد اكتمال الـ Wizard
# ═══════════════════════════════════════════════════════════════
class TestSmartPromptForwarding(_MutationSpiesMixin, unittest.TestCase):

    NEXT_STATE = {
        "action": "AWAITING_NEW_PROMPT",
        "project_key": "prj_test1234",
        "project_name": "مشروعي",
        "project_model": _bridge.DEFAULT_PROJECT_MODEL,
    }

    def test_01_no_pending_prompt_returns_next_state_verbatim(self):
        """لا pending_prompt ⟔ next_state كما هي (السلوك القديم حرفياً — صفر انحدار)."""
        result = _bridge.forward_pending_prompt_after_wizard(CHAT, {"action": "x"}, dict(self.NEXT_STATE), {})
        self.assertEqual(result, self.NEXT_STATE)
        self.assert_zero_mutation()
        self.send.assert_not_called()

    def test_02_pending_prompt_schedules_task_with_project_context(self):
        """يوجد pending_prompt ⟔ جدولة المهمة بسياق المشروع المُنشأ شرعياً."""
        state = {"pending_prompt": "ابنِ لي موقعاً كاملاً من فضلك"}
        result = _bridge.forward_pending_prompt_after_wizard(CHAT, state, dict(self.NEXT_STATE), {})
        self.assertEqual(result, {})
        self.submit.assert_called_once()
        args = self.submit.call_args.args
        self.assertIs(args[0], _bridge.process_user_task_async)
        self.assertEqual(args[1], CHAT)
        self.assertIsNone(args[2])  # لا URL — مشروع جديد
        self.assertEqual(args[3], "ابنِ لي موقعاً كاملاً من فضلك")
        self.assertEqual(args[5], "prj_test1234")
        self.assertEqual(args[6], "مشروعي")

    def test_03_user_notified_of_auto_forward(self):
        state = {"pending_prompt": "برومبت محفوظ"}
        _bridge.forward_pending_prompt_after_wizard(CHAT, state, dict(self.NEXT_STATE), {})
        self.assertIn("انطلق تلقائياً", str(self.send.call_args.args))

    def test_04_wizard_name_step_carries_pending_prompt(self):
        """AWAITING_NEW_PROJECT_NAME يحمل pending_prompt للخطوة التالية (مسار البطاقة)."""
        _bridge.set_user_state(CHAT, {
            "action": "AWAITING_NEW_PROJECT_NAME",
            "pending_prompt": "برومبتي المحفوظ",
            "consumed_confirm_nonce": "deadbeef1234",
        })
        _bridge.handle_telegram_update(_msg_update("اسم مشروعي"))
        st = self.state()
        self.assertEqual(st.get("action"), "AWAITING_NEW_PROJECT_MODEL")
        self.assertEqual(st.get("pending_prompt"), "برومبتي المحفوظ")
        self.assertTrue(str(st.get("project_key", "")).startswith("prj_"))
        self.assert_zero_mutation()  # الاسم وحده لا يسجل ولا يحجز شيئاً

    def test_05_wizard_name_step_without_pending_identical_to_old(self):
        """مسار cmd:new_proj المباشر (بلا pending_prompt) ⟔ dict مطابق للقديم حرفياً."""
        _bridge.set_user_state(CHAT, {"action": "AWAITING_NEW_PROJECT_NAME"})
        _bridge.handle_telegram_update(_msg_update("مشروع مباشر"))
        st = self.functional_state()
        self.assertEqual(
            sorted(st.keys()),
            ["action", "project_key", "project_name"],
            "لا مفاتيح P42 دخيلة على المسار المباشر",
        )

    def test_06_source_forward_called_at_both_finalize_sites(self):
        """حارس سورس: forward يُستدعى بعد موضعي finalize_new_project_from_state."""
        count = BRIDGE_SRC.count("next_state = forward_pending_prompt_after_wizard(chat_id, state, next_state, settings)")
        self.assertEqual(count, 2, "الاستدعاء مطلوب في موضعي الإنهاء (default + custom resume prompt)")

    def test_07_e2e_full_confirm_to_forward_path(self):
        """E2E: بطاقة ⟔ تأكيد ⟔ اسم ⟔ (إنهاء) ⟔ البرومبت المحفوظ ينطلق تلقائياً."""
        _bridge.handle_idle_intent_guard(CHAT, "ابنِ لي متجراً إلكترونياً متكاملاً الآن")
        nonce = self.state()["confirm_nonce"]
        _bridge.handle_telegram_update(_cb_update(f"pconf:yes:{nonce}"))
        _bridge.handle_telegram_update(_msg_update("متجري"))
        state = self.state()
        with mock.patch.object(_bridge, "finalize_new_project_setup", return_value={"model": _bridge.DEFAULT_PROJECT_MODEL, "continuation": {"prompt": "p"}}):
            settings, next_state = _bridge.finalize_new_project_from_state(state, chat_id=CHAT)
            result = _bridge.forward_pending_prompt_after_wizard(CHAT, state, next_state, settings)
        self.assertEqual(result, {})
        self.submit.assert_called_once()
        self.assertEqual(self.submit.call_args.args[3], "ابنِ لي متجراً إلكترونياً متكاملاً الآن")


# ═══════════════════════════════════════════════════════════════
# 9. الإنشاء الصريح — يعمل كما كان بلا أي تغيير
# ═══════════════════════════════════════════════════════════════
class TestExplicitCreationUnchanged(_MutationSpiesMixin, unittest.TestCase):

    def test_01_cmd_new_proj_button_unchanged(self):
        """زر 🚀 مشروع جديد ⟔ AWAITING_NEW_PROJECT_NAME مباشرة (بلا بطاقة تأكيد)."""
        _bridge.handle_telegram_update(_cb_update("cmd:new_proj"))
        st = self.functional_state()
        self.assertEqual(st, {"action": "AWAITING_NEW_PROJECT_NAME"})
        self.assertNotIn("pending_prompt", st)

    def test_02_source_cmd_new_proj_branch_verbatim(self):
        """حارس سورس: فرع cmd:new_proj لم يُمس."""
        self.assertIn(
            'elif data == "cmd:new_proj":\n'
            '            set_user_state(chat_id, {"action": "AWAITING_NEW_PROJECT_NAME"})',
            BRIDGE_SRC,
        )

    def test_03_awaiting_new_prompt_schedules_directly(self):
        """سياق برومبت نشط (AWAITING_NEW_PROMPT) ⟔ جدولة مباشرة كما كان — لا Guard."""
        _bridge.set_user_state(CHAT, {
            "action": "AWAITING_NEW_PROMPT",
            "project_key": "prj_live",
            "project_name": "حي",
            "project_model": _bridge.DEFAULT_PROJECT_MODEL,
        })
        _bridge.handle_telegram_update(_msg_update("نفّذ المهمة"))
        self.submit.assert_called_once()
        self.assertEqual(self.submit.call_args.args[3], "نفّذ المهمة")
        self.assertEqual(self.submit.call_args.args[5], "prj_live")

    def test_04_wizard_states_bypass_guard(self):
        """كل حالات الـ Wizard النشطة لا تمر على الـ Guard (State Resolution أولاً)."""
        with mock.patch.object(_bridge, "handle_idle_intent_guard") as guard:
            _bridge.set_user_state(CHAT, {"action": "AWAITING_NEW_PROJECT_NAME"})
            _bridge.handle_telegram_update(_msg_update("اسم"))
            guard.assert_not_called()


# ═══════════════════════════════════════════════════════════════
# 10. Zero-Regression — العقود المجمّدة P01–P41
# ═══════════════════════════════════════════════════════════════
class TestZeroRegression(unittest.TestCase):

    def test_01_p41_collision_guard_intact(self):
        """حارس تصادم P41 باقٍ أول سطر في فرعي البرومبت."""
        for action in ("AWAITING_NEW_PROMPT", "AWAITING_CONT_PROMPT"):
            branch_pos = BRIDGE_SRC.index(f'if action == "{action}":')
            snippet = BRIDGE_SRC[branch_pos:branch_pos + 220]
            self.assertIn("handle_prompt_context_collision(chat_id, state, text, action)", snippet)

    def test_02_p41_idle_url_routing_precedes_guard(self):
        """توجيه روابط IDLE (genspark.ai / uuid) يسبق استدعاء الحارس في الذيل."""
        tail = BRIDGE_SRC[BRIDGE_SRC.index('if "genspark.ai" in text or re.search'):]
        url_pos = tail.index("resolve_resume_context(text)")
        guard_pos = tail.index("handle_idle_intent_guard(chat_id, text)")
        self.assertLess(url_pos, guard_pos)

    def test_03_p41_polling_shutdown_contract_intact(self):
        self.assertIn("sys.exit(0)", BRIDGE_SRC)
        self.assertIn("except (KeyboardInterrupt, SystemExit):", BRIDGE_SRC)

    def test_04_frozen_symbols_still_present(self):
        """رموز المسارات المجمّدة (Success/Resume/Rotation/P35/P40) كلها قائمة."""
        for symbol in (
            "send_message_with_auto_account_failover", "resolve_resume_context",
            "claim_account_selection", "is_model_decline_response",
            "format_compact_duration", "build_completed_message_keyboard",
            "parse_project_locator", "detect_context_collision",
            "handle_prompt_context_collision", "delete_project_atomically",
            "finalize_new_project_from_state", "build_new_project_model_keyboard",
        ):
            self.assertTrue(hasattr(_bridge, symbol), f"رمز مجمّد مفقود: {symbol}")

    def test_05_p32_password_lookup_first_in_state_chain(self):
        """P32 باقٍ أول فحص في سلسلة الحالات — وفرع P42 يليه (لا يسبقه)."""
        p32_pos = BRIDGE_SRC.index("if action == AWAITING_ACCOUNT_PASSWORD_LOOKUP:")
        p42_pos = BRIDGE_SRC.index("if action == AWAITING_PROJECT_CONFIRMATION:")
        self.assertLess(p32_pos, p42_pos)

    def test_06_pconf_block_isolated_early_pattern(self):
        """كتلة pconf معزولة مبكرة بنمط P25/P26 — قبل سلسلة cmd:*."""
        pconf_pos = BRIDGE_SRC.index('if data.startswith(f"{PROJECT_CONFIRM_CALLBACK_PREFIX}:"):')
        dashboard_pos = BRIDGE_SRC.index('if data == "cmd:show_dashboard":')
        self.assertLess(pconf_pos, dashboard_pos)

    def test_07_no_new_wizard_created(self):
        """DRY: لا Wizard موازٍ — التأكيد يدخل AWAITING_NEW_PROJECT_NAME القائمة."""
        confirm_block = BRIDGE_SRC[BRIDGE_SRC.index('if verb == "yes":'):BRIDGE_SRC.index('elif verb == "no":')]
        self.assertIn('"action": "AWAITING_NEW_PROJECT_NAME"', confirm_block)

    def test_08_keyboards_contract_intact(self):
        """كيبوردات اللوحة القائمة كما هي (زر cmd:new_proj باقٍ بالنص القديم)."""
        self.assertIn('{"text": "🚀 مشروع جديد", "callback_data": "cmd:new_proj", "style": "primary"}', BRIDGE_SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
