#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p25_interactive_cancel.py
====================================
🛑 [P25] حراسة ميزة «الإلغاء التفاعلي وإيقاف التوليد الفوري» (Interactive Cancellation Flow):

1. مدير أحداث الإلغاء (Cancellation Manager): توكن قصير + دورة حياة كاملة
   (register ➔ update ➔ trigger ➔ unregister) بدون تسريب ذاكرة (Zero Leaks).
2. كيبورد المعاينة الحية: توافق خلفي كامل بدون توكن + زر إلغاء أحمر (danger)
   + كيبورد التأكيد بخطوتي أمان (نعم/تراجع).
3. عقود التكامل في المصدر: الـ worker يسجل وينظف في finally، الـ failover يعيد
   CANCELLED بلا عقوبة، حلقة المتابعة تستيقظ فوراً (wait بدل sleep)،
   ومعالج الـ callbacks يفصل cancel_prompt/exec/abort عن باقي الأزرار.
4. عقد المحرك (01.03): فحص cfg.cancel_event كل سطر SSE + قطع البث + ماركر
   __USER_CANCELLED__ له الأولوية القصوى قبل أي تصنيف.
"""

import re
import sys
import pathlib
import threading
import unittest
import importlib.util

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")
ENGINE_PATH = webapp_dir / "01.03Genspark_claude-opus-5-code.py"
ENGINE_SRC = ENGINE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p25", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)


class TestCancellationManager(unittest.TestCase):
    """1. مدير أحداث الإلغاء — دورة الحياة الكاملة Thread-Safe"""

    def setUp(self):
        self.token = _bridge.new_cancel_token()

    def tearDown(self):
        _bridge.unregister_cancel_event(self.token)

    def test_01_token_short_enough_for_callback_data(self):
        # callback_data محدود بـ 64 بايت — "cancel_prompt:" + توكن يجب أن يظل أقل بكثير
        self.assertEqual(len(self.token), 12)
        self.assertTrue(re.fullmatch(r"[0-9a-f]{12}", self.token))
        self.assertLessEqual(len(f"cancel_prompt:{self.token}"), 64)

    def test_02_register_returns_event(self):
        ev = _bridge.register_cancel_event(self.token, chat_id=123)
        self.assertIsInstance(ev, threading.Event)
        self.assertFalse(ev.is_set())

    def test_03_register_idempotent_same_event(self):
        ev1 = _bridge.register_cancel_event(self.token)
        ev2 = _bridge.register_cancel_event(self.token)
        self.assertIs(ev1, ev2)

    def test_04_register_empty_token_returns_none(self):
        self.assertIsNone(_bridge.register_cancel_event(""))
        self.assertIsNone(_bridge.register_cancel_event("   "))

    def test_05_get_entry_metadata(self):
        _bridge.register_cancel_event(self.token, project_key="proj_x", chat_id=42)
        entry = _bridge.get_cancel_entry(self.token)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["project_key"], "proj_x")
        self.assertEqual(entry["chat_id"], 42)

    def test_06_get_entry_unknown_token_returns_none(self):
        self.assertIsNone(_bridge.get_cancel_entry("deadbeef0000"))

    def test_07_update_entry_live_pid(self):
        _bridge.register_cancel_event(self.token)
        self.assertTrue(_bridge.update_cancel_entry(self.token, live_pid="abc-123"))
        self.assertEqual(_bridge.get_cancel_entry(self.token)["live_pid"], "abc-123")

    def test_08_update_unknown_token_returns_false(self):
        self.assertFalse(_bridge.update_cancel_entry("deadbeef0000", live_pid="x"))

    def test_09_trigger_sets_event(self):
        ev = _bridge.register_cancel_event(self.token)
        self.assertTrue(_bridge.trigger_cancel(self.token))
        self.assertTrue(ev.is_set())
        self.assertTrue(_bridge.is_cancel_requested(self.token))

    def test_10_trigger_unknown_token_returns_false(self):
        self.assertFalse(_bridge.trigger_cancel("deadbeef0000"))

    def test_11_unregister_zero_leaks(self):
        _bridge.register_cancel_event(self.token)
        self.assertTrue(_bridge.unregister_cancel_event(self.token))
        # بعد التنظيف: التوكن اختفى تماماً من المسجل — الضغط على زر قديم = None
        self.assertIsNone(_bridge.get_cancel_entry(self.token))
        self.assertFalse(_bridge.unregister_cancel_event(self.token))

    def test_12_cancelled_status_constant(self):
        self.assertEqual(_bridge.CANCELLED_STATUS, "CANCELLED")
        self.assertEqual(_bridge.USER_CANCELLED_MARKER, "__USER_CANCELLED__")


class TestLivePreviewKeyboard(unittest.TestCase):
    """2. كيبورد المعاينة الحية — توافق خلفي + زر الإلغاء + كيبورد التأكيد"""

    def test_01_backward_compat_no_token_single_row(self):
        kb = _bridge.build_live_preview_keyboard("pid-1", status="running")
        rows = kb["inline_keyboard"]
        self.assertEqual(len(rows), 1)
        self.assertIn("url", rows[0][0])

    def test_02_running_with_token_adds_danger_cancel_row(self):
        token = "aabbccddeeff"
        kb = _bridge.build_live_preview_keyboard("pid-1", status="running", cancel_token=token)
        rows = kb["inline_keyboard"]
        self.assertEqual(len(rows), 2)
        # الصف الأول: زر المعاينة الأزرق (بلا تغيير)
        self.assertIn("url", rows[0][0])
        self.assertEqual(rows[0][0].get("style"), "primary")
        # الصف الثاني: زر إلغاء أحمر يفتح كيبورد التأكيد فقط (cancel_prompt)
        btn = rows[1][0]
        self.assertEqual(btn["callback_data"], f"cancel_prompt:{token}")
        self.assertEqual(btn.get("style"), "danger")

    def test_03_confirm_cancel_keyboard_two_step_safety(self):
        token = "aabbccddeeff"
        kb = _bridge.build_live_preview_keyboard("pid-1", status="confirm_cancel", cancel_token=token)
        rows = kb["inline_keyboard"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0]["callback_data"], f"cancel_exec:{token}")
        self.assertEqual(rows[0][0].get("style"), "danger")
        self.assertEqual(rows[1][0]["callback_data"], f"cancel_abort:{token}")
        self.assertEqual(rows[1][0].get("style"), "primary")

    def test_04_completed_keyboard_unchanged(self):
        kb = _bridge.build_live_preview_keyboard("pid-1", status="completed", cancel_token="aabbccddeeff")
        rows = kb["inline_keyboard"]
        # الاكتمال: زر أخضر واحد فقط — لا زر إلغاء لمشروع منتهٍ
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0].get("style"), "success")
        self.assertNotIn("callback_data", rows[0][0])

    def test_05_callback_data_within_telegram_64_bytes(self):
        token = _bridge.new_cancel_token()
        try:
            for status, expected in (("running", "cancel_prompt"), ("confirm_cancel", "cancel_exec")):
                kb = _bridge.build_live_preview_keyboard("pid-1", status=status, cancel_token=token)
                for row in kb["inline_keyboard"]:
                    for btn in row:
                        if "callback_data" in btn:
                            self.assertLessEqual(len(btn["callback_data"].encode("utf-8")), 64)
        finally:
            _bridge.unregister_cancel_event(token)


class TestWorkerIntegrationContracts(unittest.TestCase):
    """3. عقود التكامل في مصدر الجسر — worker/failover/polling/callbacks"""

    def test_01_worker_registers_token_before_work(self):
        m = re.search(r"cancel_token = new_cancel_token\(\)\s*\n\s*cancel_event = register_cancel_event\(cancel_token", BRIDGE_SRC)
        self.assertIsNotNone(m, "الـ worker يجب أن يسجل حدث الإلغاء قبل أي عمل")

    def test_02_worker_injects_event_into_cfg(self):
        self.assertIn("cfg.cancel_event = cancel_event", BRIDGE_SRC)
        self.assertIn("cfg.cancel_token = cancel_token", BRIDGE_SRC)

    def test_03_worker_finally_unregisters_zero_leaks(self):
        m = re.search(r"finally:.{0,600}?unregister_cancel_event\(cancel_token\).{0,600}?release_project_run", BRIDGE_SRC, re.DOTALL)
        self.assertIsNotNone(m, "التنظيف في finally يجب أن يسبق تحرير قفل المشروع ويشمل كل المخارج")

    def test_04_failover_returns_cancelled_without_penalty(self):
        # في الـ failover: CANCELLED يعيد فوراً مع status=active (لا تبريد/عقوبة)
        m = re.search(
            r"if status == CANCELLED_STATUS:.{0,900}?update_account_data\(curr_email, \{\"last_used\": time\.time\(\), \"status\": \"active\"\}.{0,200}?return pub_url, CANCELLED_STATUS",
            BRIDGE_SRC, re.DOTALL,
        )
        self.assertIsNotNone(m, "إلغاء المستخدم = تحرير الحساب active فوراً بدون تبريد")

    def test_05_cancelled_check_before_low_balance(self):
        pos_cancel = BRIDGE_SRC.find("if status == CANCELLED_STATUS:")
        pos_low = BRIDGE_SRC.find('if status == "LOW_BALANCE":')
        self.assertGreater(pos_cancel, 0)
        self.assertGreater(pos_low, pos_cancel, "فحص CANCELLED يجب أن يسبق LOW_BALANCE في الـ failover")

    def test_06_precheck_before_attempt_starts(self):
        m = re.search(r"if _cancel_event is not None and _cancel_event\.is_set\(\):\s*\n\s*log_event\([^\n]*قبل بدء المحاولة", BRIDGE_SRC)
        self.assertIsNotNone(m, "إلغاء طُلب قبل بدء المحاولة = خروج فوري بدون أي إرسال")

    def test_07_engine_marker_ends_task_without_retry(self):
        m = re.search(r"if answer == USER_CANCELLED_MARKER or \(\s*\n\s*_cancel_event is not None and _cancel_event\.is_set\(\)\s*\n\s*\):", BRIDGE_SRC)
        self.assertIsNotNone(m, "ماركر المحرك __USER_CANCELLED__ يجب أن ينهي المهمة بلا retry")

    def test_08_polling_loop_checks_cancel_first(self):
        m = re.search(
            r"while final_status not in \([^)]*\):\s*\n\s*# 🛑 \[P25\][^\n]*\n\s*if _cancel_event is not None and _cancel_event\.is_set\(\):",
            BRIDGE_SRC,
        )
        self.assertIsNotNone(m, "فحص الإلغاء يجب أن يكون أول سطر في كل دورة متابعة")

    def test_09_polling_sleep_is_interruptible_wait(self):
        m = re.search(r"_cancel_event\.wait\(timeout=5\)", BRIDGE_SRC)
        self.assertIsNotNone(m, "النوم يجب أن يكون Event.wait متقطعاً — لا sleep أصم أثناء وجود حدث إلغاء")

    def test_10_callback_handler_three_actions_isolated(self):
        m = re.search(r'if data\.startswith\(\("cancel_prompt:", "cancel_exec:", "cancel_abort:"\)\):', BRIDGE_SRC)
        self.assertIsNotNone(m, "معالج الإلغاء يجب أن يعالج الأنماط الثلاثة مبكراً وبمعزل عن سلسلة if/elif")

    def test_11_callback_exec_triggers_and_edits_message(self):
        m = re.search(r'elif action == "cancel_exec":.{0,600}?trigger_cancel\(cancel_token\)', BRIDGE_SRC, re.DOTALL)
        self.assertIsNotNone(m, "cancel_exec يجب أن يفعّل trigger_cancel")

    def test_12_callback_abort_restores_running_keyboard(self):
        m = re.search(r'elif action == "cancel_abort":.{0,500}?status="running", cancel_token=cancel_token', BRIDGE_SRC, re.DOTALL)
        self.assertIsNotNone(m, "التراجع يجب أن يعيد كيبورد التشغيل الأصلي والاستمرار طبيعياً")

    def test_13_expired_token_cleans_buttons_quietly(self):
        m = re.search(r"if entry is None:.{0,400}?انتهت بالفعل", BRIDGE_SRC, re.DOTALL)
        self.assertIsNotNone(m, "توكن منتهٍ = تنظيف هادئ للأزرار + رسالة إخبارية بدون أخطاء")

    def test_14_worker_handles_cancelled_terminal_message(self):
        m = re.search(r"if status == CANCELLED_STATUS:.{0,900}?تم إلغاء المهمة بالكامل", BRIDGE_SRC, re.DOTALL)
        self.assertIsNotNone(m, "الـ worker يجب أن يرسل رسالة إلغاء نهائية ويخرج بلا متابعة")

    def test_15_live_preview_card_carries_cancel_button(self):
        m = re.search(r'build_live_preview_keyboard\(live_pid, status="running", cancel_token=cancel_token\)\s*\n\s*update_cancel_entry\(cancel_token, live_pid=live_pid', BRIDGE_SRC)
        self.assertIsNotNone(m, "بطاقة المعاينة الفورية يجب أن تحمل زر الإلغاء وتحدّث metadata التوكن")

    def test_16_bridge_config_declares_cancel_fields(self):
        cfg = _bridge.BridgeConfig(model="test")
        self.assertTrue(hasattr(cfg, "cancel_event"))
        self.assertTrue(hasattr(cfg, "cancel_token"))
        self.assertIsNone(cfg.cancel_event)


class TestEngineStreamAbortContract(unittest.TestCase):
    """4. عقد المحرك 01.03 — قطع بث SSE تعاونياً + أولوية الماركر"""

    def test_01_engine_reads_cancel_event_from_cfg(self):
        self.assertIn('getattr(cfg, "cancel_event", None)', ENGINE_SRC)

    def test_02_engine_checks_event_inside_iter_lines(self):
        m = re.search(r"for _raw_line in r\.iter_lines\(\):\s*\n\s*if _cancel_event is not None and _cancel_event\.is_set\(\):", ENGINE_SRC)
        self.assertIsNotNone(m, "الفحص يجب أن يكون أول سطر داخل حلقة البث — استجابة كل سطر SSE")

    def test_03_engine_returns_user_cancelled_marker(self):
        m = re.search(r"if user_cancelled:\s*\n\s*return \"__USER_CANCELLED__\", proj_id_new, asst_msg_id", ENGINE_SRC)
        self.assertIsNotNone(m)

    def test_04_marker_priority_before_credit_classification(self):
        pos_cancel = ENGINE_SRC.find('if user_cancelled:')
        pos_credit = ENGINE_SRC.find('if full_text == "__CREDIT_EXHAUSTED__"')
        self.assertGreater(pos_cancel, 0)
        self.assertGreater(pos_credit, pos_cancel, "فحص الإلغاء له الأولوية القصوى قبل تصنيف الرصيد")

    def test_05_socket_closed_after_break(self):
        # break من الحلقة ➔ r.close() في البلوك التالي يقطع اتصال ask_proxy (نفس زر ⏹️ Stop)
        m = re.search(r"user_cancelled = True.{0,300}?break", ENGINE_SRC, re.DOTALL)
        self.assertIsNotNone(m)
        # فحص موضعي: r.close() يجب أن يوجد بعد نقطة الـ break (نافذة ترتيب لا مسافة)
        pos_break = ENGINE_SRC.find("user_cancelled = True")
        pos_close = ENGINE_SRC.find("r.close()", pos_break)
        self.assertGreater(pos_close, pos_break, "r.close() يجب أن يلي الخروج من الحلقة لتحرير الاتصال")
        # ولا يجوز أن يوجد return بين الـ break وإغلاق الاتصال يقفز فوق r.close()
        between = ENGINE_SRC[pos_break:pos_close]
        self.assertNotIn("\n        return ", between, "ممنوع أي return يسبق r.close() بعد الإلغاء — الاتصال يجب أن يُغلق أولاً")


class TestFullCancelFlowSimulation(unittest.TestCase):
    """5. محاكاة التدفق الكامل: تسجيل ➔ زر ➔ تأكيد ➔ استيقاظ فوري ➔ تنظيف"""

    def test_01_end_to_end_cancel_wakes_waiter_instantly(self):
        token = _bridge.new_cancel_token()
        ev = _bridge.register_cancel_event(token, chat_id=99)
        try:
            _bridge.update_cancel_entry(token, live_pid="pid-e2e")
            woke = {"flag": False}

            def waiter():
                # نفس نمط حلقة المتابعة: wait متقطع بدل sleep أصم
                if ev.wait(timeout=10):
                    woke["flag"] = True

            th = threading.Thread(target=waiter, daemon=True)
            th.start()
            self.assertTrue(_bridge.trigger_cancel(token))
            th.join(timeout=2)
            self.assertTrue(woke["flag"], "الضغط على «نعم، إلغاء فوري» يجب أن يوقظ المنتظر خلال أجزاء من الثانية")
        finally:
            _bridge.unregister_cancel_event(token)
        self.assertIsNone(_bridge.get_cancel_entry(token))

    def test_02_abort_leaves_event_unset_and_task_continues(self):
        token = _bridge.new_cancel_token()
        ev = _bridge.register_cancel_event(token)
        try:
            # cancel_prompt ثم cancel_abort: لا trigger — الحدث يظل غير مضبوط والبناء يستمر
            self.assertFalse(ev.is_set())
            self.assertFalse(_bridge.is_cancel_requested(token))
        finally:
            _bridge.unregister_cancel_event(token)


if __name__ == "__main__":
    unittest.main(verbosity=2)
