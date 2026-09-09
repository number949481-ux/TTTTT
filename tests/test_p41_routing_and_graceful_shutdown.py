#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p41_routing_and_graceful_shutdown.py
================================================
🧭⏹️ [P41] حراسة المرحلة 41 — Forensic Project URL Routing & Graceful Shutdown
(بروتوكول `15_PROJECT_ROUTING_AND_CLEAN_SHUTDOWN.MD` — DEC-037).

العلتان المعالجَتان:
1. Cross-Project Context Hijacking: سياق برومبت نشط لمشروع (A)
   (AWAITING_NEW_PROMPT / AWAITING_CONT_PROMPT) + رابط مشروع (B) كان
   يُمرَّر كنص برومبت حرفي إلى المشروع (A) — الآن حارس
   `handle_prompt_context_collision` يمنع الجدولة ويوجّه الرابط لمساره الشرعي.
2. Ctrl+C المبتلع: عميل getUpdates كان `curl_cffi` (مقاطعة أثناء long-poll
   تظهر كخطأ CFFI عادي فتُبتلع في except Exception) — الآن `requests` النقية
   + التقاط صريح لـ KeyboardInterrupt/SystemExit + `sys.exit(0)`.

المجموعات:
1. TestLocatorParsing          — parse_project_locator بكل صيغ الروابط والحواف
2. TestRegistryResolution      — مطابقة key/root/latest + عدم الوجود بلا Fallback
3. TestContextCollisionGuard   — detect_context_collision (تصادم/برومبت عادي)
4. TestCollisionHandler        — handle_prompt_context_collision (سلوك كامل بالـ Mocks)
5. TestHandlerIntegration      — حراس سورس: الاستدعاء قبل الجدولة بالفرعين
6. TestPollingClientContract   — حراس سورس: requests داخل الحلقة + curl_cffi باقٍ خارجها
7. TestGracefulShutdown        — حراس سورس + سلوكي: خروج نظيف بـ sys.exit(0)
8. TestZeroRegression          — العقود المجمّدة (Success/Resume/Rotation/P35/P40)
"""

import importlib.util
import json
import pathlib
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIDGE_PATH = ROOT / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_p41", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("bridge_p41", _bridge)
_spec.loader.exec_module(_bridge)

VALID_PID_A = "aaaaaaaa-1111-2222-3333-444444444444"
VALID_PID_B = "bbbbbbbb-1111-2222-3333-444444444444"
VALID_PID_C = "cccccccc-1111-2222-3333-444444444444"

URL_AGENTS = f"https://www.genspark.ai/agents?id={VALID_PID_B}"
URL_VIEWER = f"https://www.genspark.ai/autopilotagent_viewer?id={VALID_PID_B}"
URL_MALFORMED = "https://www.genspark.ai/agents?id=not-a-uuid"


class _IsolatedRegistryMixin:
    """عزل كامل لمسارات السجل (نمط P26 حرفياً)."""

    def setUp(self):
        self._tmp = pathlib.Path(tempfile.mkdtemp(prefix="p41_test_"))
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


# ══════════════════════════════════════════════════════════════
# 1) parse_project_locator — التصنيف المركزي SSOT
# ══════════════════════════════════════════════════════════════
class TestLocatorParsing(unittest.TestCase):

    def test_agents_url(self):
        r = _bridge.parse_project_locator(URL_AGENTS)
        self.assertEqual(r["kind"], "pid")
        self.assertEqual(r["pid"], VALID_PID_B)

    def test_viewer_url(self):
        r = _bridge.parse_project_locator(URL_VIEWER)
        self.assertEqual(r["kind"], "pid")
        self.assertEqual(r["pid"], VALID_PID_B)

    def test_raw_uuid(self):
        r = _bridge.parse_project_locator(VALID_PID_A)
        self.assertEqual(r["kind"], "pid")
        self.assertEqual(r["pid"], VALID_PID_A)

    def test_uuid_embedded_in_text(self):
        r = _bridge.parse_project_locator(f"شوف المشروع ده {VALID_PID_C} لو سمحت")
        self.assertEqual(r["kind"], "pid")
        self.assertEqual(r["pid"], VALID_PID_C)

    def test_malformed_genspark_link_no_uuid(self):
        r = _bridge.parse_project_locator(URL_MALFORMED)
        self.assertEqual(r["kind"], "malformed")
        self.assertEqual(r["pid"], "")

    def test_malformed_bare_domain(self):
        r = _bridge.parse_project_locator("https://www.genspark.ai/agents")
        self.assertEqual(r["kind"], "malformed")

    def test_plain_prompt_is_none(self):
        r = _bridge.parse_project_locator("اعمل لي موقع مطعم بسيط")
        self.assertEqual(r["kind"], "none")

    def test_prompt_mentioning_genspark_word_without_domain(self):
        # "genspark" وحدها (بلا genspark.ai) = برومبت عادي
        r = _bridge.parse_project_locator("اشرح لي إزاي genspark بيشتغل")
        self.assertEqual(r["kind"], "none")

    def test_prompt_with_random_numbers_not_uuid(self):
        r = _bridge.parse_project_locator("غيّر الرقم 123456 لـ 654321 في الصفحة")
        self.assertEqual(r["kind"], "none")

    def test_empty_and_none_inputs(self):
        self.assertEqual(_bridge.parse_project_locator("")["kind"], "none")
        self.assertEqual(_bridge.parse_project_locator(None)["kind"], "none")
        self.assertEqual(_bridge.parse_project_locator("   ")["kind"], "none")

    def test_raw_preserved(self):
        r = _bridge.parse_project_locator(f"  {URL_AGENTS}  ")
        self.assertEqual(r["raw"], URL_AGENTS)

    def test_uppercase_uuid_accepted(self):
        r = _bridge.parse_project_locator(VALID_PID_A.upper())
        self.assertEqual(r["kind"], "pid")


# ══════════════════════════════════════════════════════════════
# 2) مطابقة الـ Registry — key/root/latest + عدم الوجود
# ══════════════════════════════════════════════════════════════
class TestRegistryResolution(_IsolatedRegistryMixin, unittest.TestCase):

    def test_resolve_by_root_pid(self):
        _bridge.upsert_project_identity("proj_a", root_pid=VALID_PID_A, chat_id=1)
        ctx = _bridge.resolve_resume_context(f"https://www.genspark.ai/agents?id={VALID_PID_A}")
        self.assertEqual(ctx["project_key"], "proj_a")
        self.assertEqual(ctx["pid"], VALID_PID_A)

    def test_resolve_by_latest_pid(self):
        _bridge.upsert_project_identity("proj_a", root_pid=VALID_PID_A, latest_pid=VALID_PID_C, chat_id=1)
        ctx = _bridge.resolve_resume_context(VALID_PID_C)
        self.assertEqual(ctx["project_key"], "proj_a")

    def test_unregistered_pid_returns_empty_key_no_silent_fallback(self):
        ctx = _bridge.resolve_resume_context(URL_AGENTS)
        self.assertEqual(ctx["project_key"], "")
        self.assertEqual(ctx["pid"], VALID_PID_B)
        # الرابط الموحد يُبنى من الـ pid (المسار الخارجي الشرعي)
        self.assertIn(VALID_PID_B, ctx["target_url"])

    def test_t4_last_writer_wins_documented(self):
        """T4 (توثيقي): إعادة تسجيل نفس الـ pid لمشروع آخر = آخر كاتب يكسب."""
        _bridge.upsert_project_identity("proj_a", root_pid=VALID_PID_A, chat_id=1)
        _bridge.upsert_project_identity("proj_b", root_pid=VALID_PID_A, chat_id=1)
        self.assertEqual(_bridge.lookup_project_key_for_locator(VALID_PID_A), "proj_b")


# ══════════════════════════════════════════════════════════════
# 3) detect_context_collision — كشف التصادم النقي
# ══════════════════════════════════════════════════════════════
class TestContextCollisionGuard(unittest.TestCase):

    def test_plain_prompt_no_collision(self):
        state = {"action": "AWAITING_NEW_PROMPT", "project_key": "proj_a"}
        self.assertIsNone(_bridge.detect_context_collision(state, "أضف صفحة تواصل"))

    def test_project_url_collides(self):
        state = {"action": "AWAITING_CONT_PROMPT", "project_key": "proj_a",
                 "url": f"https://www.genspark.ai/agents?id={VALID_PID_A}"}
        c = _bridge.detect_context_collision(state, URL_AGENTS)
        self.assertIsNotNone(c)
        self.assertEqual(c["kind"], "pid")
        self.assertEqual(c["pid"], VALID_PID_B)
        self.assertEqual(c["active_project_key"], "proj_a")
        self.assertEqual(c["active_pid"], VALID_PID_A)

    def test_raw_uuid_collides(self):
        c = _bridge.detect_context_collision({"project_key": "proj_a"}, VALID_PID_B)
        self.assertIsNotNone(c)
        self.assertEqual(c["kind"], "pid")

    def test_malformed_link_reported(self):
        c = _bridge.detect_context_collision({"project_key": "proj_a"}, URL_MALFORMED)
        self.assertIsNotNone(c)
        self.assertEqual(c["kind"], "malformed")

    def test_empty_state_tolerated(self):
        c = _bridge.detect_context_collision(None, URL_AGENTS)
        self.assertIsNotNone(c)
        self.assertEqual(c["active_project_key"], "")
        self.assertEqual(c["active_pid"], "")

    def test_prompt_mentioning_numbers_no_false_positive(self):
        state = {"project_key": "proj_a"}
        self.assertIsNone(_bridge.detect_context_collision(state, "خلي السعر 199.99 بدل 149.99"))


# ══════════════════════════════════════════════════════════════
# 4) handle_prompt_context_collision — السلوك الكامل بالـ Mocks
# ══════════════════════════════════════════════════════════════
class TestCollisionHandler(unittest.TestCase):

    def _run(self, state, text):
        calls = {}
        with mock.patch.object(_bridge, "send_telegram_message") as send, \
             mock.patch.object(_bridge, "set_user_state") as setst, \
             mock.patch.object(_bridge, "resolve_resume_context") as res, \
             mock.patch.object(_bridge, "present_resume_summary") as summ, \
             mock.patch.object(_bridge, "present_external_resume_decision") as ext:
            res.return_value = {"pid": VALID_PID_B, "target_url": URL_VIEWER,
                                "project_key": "", "project_name": "", "identity": {}}
            handled = _bridge.handle_prompt_context_collision(777, state, text, "AWAITING_NEW_PROMPT")
            calls.update(send=send, setst=setst, res=res, summ=summ, ext=ext, handled=handled)
        return calls

    def test_plain_prompt_returns_false_untouched(self):
        c = self._run({"project_key": "proj_a"}, "زود زر تحميل")
        self.assertFalse(c["handled"])
        c["send"].assert_not_called()
        c["setst"].assert_not_called()

    def test_link_collision_clears_state_and_routes_externally(self):
        c = self._run({"project_key": "proj_a"}, URL_AGENTS)
        self.assertTrue(c["handled"])
        c["setst"].assert_called_once_with(777, {})          # السياق القديم أُغلق
        c["res"].assert_called_once()                        # المسار الشرعي
        c["ext"].assert_called_once()                        # غير مسجّل ➔ قرار خارجي
        c["summ"].assert_not_called()

    def test_link_collision_registered_routes_to_resume_summary(self):
        with mock.patch.object(_bridge, "send_telegram_message"), \
             mock.patch.object(_bridge, "set_user_state"), \
             mock.patch.object(_bridge, "resolve_resume_context") as res, \
             mock.patch.object(_bridge, "present_resume_summary") as summ, \
             mock.patch.object(_bridge, "present_external_resume_decision") as ext:
            res.return_value = {"pid": VALID_PID_B, "target_url": URL_VIEWER,
                                "project_key": "proj_b", "project_name": "ب", "identity": {}}
            handled = _bridge.handle_prompt_context_collision(
                777, {"project_key": "proj_a"}, URL_AGENTS, "AWAITING_CONT_PROMPT")
        self.assertTrue(handled)
        summ.assert_called_once()
        ext.assert_not_called()

    def test_malformed_link_rejected_state_preserved(self):
        c = self._run({"project_key": "proj_a"}, URL_MALFORMED)
        self.assertTrue(c["handled"])
        c["setst"].assert_not_called()                       # السياق باقٍ
        c["res"].assert_not_called()                         # لا توجيه
        sent = c["send"].call_args[0][1]
        self.assertIn("مشوّه", sent)

    def test_collision_message_mentions_active_context(self):
        c = self._run({"project_key": "proj_alpha"}, URL_AGENTS)
        joined = " ".join(str(call) for call in c["send"].call_args_list)
        self.assertIn("proj_alpha", joined)


# ══════════════════════════════════════════════════════════════
# 5) حراس السورس — الدمج في الفرعين قبل الجدولة
# ══════════════════════════════════════════════════════════════
class TestHandlerIntegration(unittest.TestCase):

    def _branch(self, action):
        idx = BRIDGE_SRC.index(f'if action == "{action}":')
        return BRIDGE_SRC[idx:idx + 900]

    def test_guard_called_in_awaiting_new_prompt_before_submit(self):
        seg = self._branch("AWAITING_NEW_PROMPT")
        gpos = seg.index("handle_prompt_context_collision")
        spos = seg.index("EXECUTOR.submit")
        self.assertLess(gpos, spos, "الحارس يجب أن يسبق الجدولة")

    def test_guard_called_in_awaiting_cont_prompt_before_submit(self):
        seg = self._branch("AWAITING_CONT_PROMPT")
        gpos = seg.index("handle_prompt_context_collision")
        spos = seg.index("EXECUTOR.submit")
        self.assertLess(gpos, spos)

    def test_guard_returns_stop_processing(self):
        seg = self._branch("AWAITING_NEW_PROMPT")
        self.assertIn("if handle_prompt_context_collision(chat_id, state, text, action):", seg)

    def test_malformed_rejection_in_cont_url_branch(self):
        seg = self._branch("AWAITING_CONT_URL")
        self.assertIn("MALFORMED_PROJECT_LINK_MESSAGE", seg)

    def test_malformed_rejection_in_general_link_branch(self):
        idx = BRIDGE_SRC.index('if "genspark.ai" in text or re.search')
        seg = BRIDGE_SRC[idx:idx + 700]
        self.assertIn("MALFORMED_PROJECT_LINK_MESSAGE", seg)

    def test_legacy_scheduling_signature_intact(self):
        # عقد Zero-Regression: توقيعا الجدولة القديمان باقيان حرفياً
        self.assertIn("EXECUTOR.submit(process_user_task_async, chat_id, None, text, state_project_model, state_project_key, state_project_name)", BRIDGE_SRC)
        self.assertIn("EXECUTOR.submit(process_user_task_async, chat_id, target_url, text, state_project_model, state_project_key, state_project_name)", BRIDGE_SRC)

    def test_malformed_message_constant_defined_top_level(self):
        self.assertTrue(hasattr(_bridge, "MALFORMED_PROJECT_LINK_MESSAGE"))
        self.assertIn("UUID", _bridge.MALFORMED_PROJECT_LINK_MESSAGE)


# ══════════════════════════════════════════════════════════════
# 6) حراس السورس — عميل الحلقة requests + بقاء curl_cffi خارجها
# ══════════════════════════════════════════════════════════════
def _polling_src():
    start = BRIDGE_SRC.index("def run_telegram_polling():")
    end = BRIDGE_SRC.index("def main():", start)
    return BRIDGE_SRC[start:end]


class TestPollingClientContract(unittest.TestCase):

    def test_polling_uses_pure_requests_session(self):
        seg = _polling_src()
        self.assertIn("import requests as polling_requests", seg)
        self.assertIn("polling_requests.Session()", seg)

    def test_polling_no_curl_cffi_usage(self):
        # لا استيراد ولا استخدام فعلي لـ curl_cffi داخل الحلقة
        # (ذكرها في تعليق [P41] التوثيقي مسموح — الحارس على الكود الحي)
        seg = _polling_src()
        self.assertNotIn("from curl_cffi", seg)
        self.assertNotIn("import curl_cffi", seg)
        self.assertNotIn("cffi_requests", seg)

    def test_curl_cffi_still_used_elsewhere(self):
        outside = BRIDGE_SRC.replace(_polling_src(), "")
        self.assertGreaterEqual(outside.count("from curl_cffi import requests"), 3,
                                "مسارات Genspark تبقى curl_cffi")

    def test_requests_in_requirements(self):
        req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertRegex(req, r"(?m)^requests>=", "requests مثبتة في requirements.txt")


# ══════════════════════════════════════════════════════════════
# 7) الخروج النظيف — حراس سورس + سلوكي
# ══════════════════════════════════════════════════════════════
class TestGracefulShutdown(unittest.TestCase):

    def test_inner_loop_reraises_interrupt(self):
        seg = _polling_src()
        self.assertIn("except (KeyboardInterrupt, SystemExit):", seg)
        inner = seg.index("except (KeyboardInterrupt, SystemExit):")
        self.assertIn("raise", seg[inner:inner + 200])

    def test_inner_interrupt_handler_precedes_generic_exception(self):
        seg = _polling_src()
        # معالج المقاطعة يجب أن يسبق معالج أخطاء الحلقة في نفس try
        # (أول except Exception بالدالة خاص بجدولة EXECUTOR.submit — خارج العقد)
        loop_err = seg.index('خطأ في حلقة Telegram polling')
        interrupt_pos = seg.index("except (KeyboardInterrupt, SystemExit):")
        self.assertLess(interrupt_pos, loop_err,
                        "التقاط المقاطعة يجب أن يسبق معالج أخطاء الحلقة")

    def test_outer_handler_calls_sys_exit_zero(self):
        seg = _polling_src()
        outer = seg.rindex("except (KeyboardInterrupt, SystemExit):")
        tail = seg[outer:]
        self.assertIn("sys.exit(0)", tail)
        self.assertIn("Ctrl+C", tail)

    def test_behavioral_clean_exit_on_interrupt(self):
        """سلوكي: مقاطعة أثناء sess.get ➔ sys.exit(0) بلا Traceback (كله Mocks)."""
        fake_sess = mock.MagicMock()
        fake_sess.get.side_effect = KeyboardInterrupt()
        fake_requests = mock.MagicMock()
        fake_requests.Session.return_value = fake_sess
        with mock.patch.dict(sys.modules, {"requests": fake_requests}), \
             mock.patch.object(_bridge, "TELEGRAM_BOT_TOKEN", "TEST:TOKEN"), \
             mock.patch.object(_bridge, "ALLOWED_CHAT_IDS", set()), \
             mock.patch.object(_bridge, "load_telegram_offset", return_value=0), \
             mock.patch.object(_bridge, "send_telegram_message"), \
             mock.patch.object(_bridge, "log_event"), \
             mock.patch("builtins.print"):
            with self.assertRaises(SystemExit) as ctx:
                _bridge.run_telegram_polling()
        self.assertEqual(ctx.exception.code, 0)

    def test_behavioral_generic_error_does_not_exit(self):
        """سلوكي: خطأ شبكة عادي لا يُنهي الحلقة (backoff ثم دورة تالية)."""
        fake_sess = mock.MagicMock()
        fake_sess.get.side_effect = [ConnectionError("net down"), KeyboardInterrupt()]
        fake_requests = mock.MagicMock()
        fake_requests.Session.return_value = fake_sess
        with mock.patch.dict(sys.modules, {"requests": fake_requests}), \
             mock.patch.object(_bridge, "TELEGRAM_BOT_TOKEN", "TEST:TOKEN"), \
             mock.patch.object(_bridge, "ALLOWED_CHAT_IDS", set()), \
             mock.patch.object(_bridge, "load_telegram_offset", return_value=0), \
             mock.patch.object(_bridge, "send_telegram_message"), \
             mock.patch.object(_bridge, "log_event") as logev, \
             mock.patch.object(_bridge.time, "sleep"), \
             mock.patch("builtins.print"):
            with self.assertRaises(SystemExit) as ctx:
                _bridge.run_telegram_polling()
        self.assertEqual(ctx.exception.code, 0)
        self.assertEqual(fake_sess.get.call_count, 2, "الخطأ العادي لم يُنهِ الحلقة")
        err_msgs = " ".join(str(c) for c in logev.call_args_list)
        self.assertIn("net down", err_msgs)


# ══════════════════════════════════════════════════════════════
# 8) Zero-Regression — العقود المجمّدة
# ══════════════════════════════════════════════════════════════
class TestZeroRegression(unittest.TestCase):

    def test_extract_project_id_contract_unchanged(self):
        self.assertEqual(_bridge.extract_project_id(URL_AGENTS), VALID_PID_B)
        self.assertEqual(_bridge.extract_project_id(VALID_PID_A), VALID_PID_A)
        self.assertEqual(_bridge.extract_project_id("garbage"), "garbage")  # الـ fallback القديم باقٍ
        self.assertEqual(_bridge.extract_project_id(""), "")

    def test_resolve_resume_context_contract_unchanged(self):
        ctx = _bridge.resolve_resume_context(None)
        self.assertEqual(set(ctx.keys()), {"pid", "target_url", "project_key", "project_name", "identity"})

    def test_p35_decline_detection_intact(self):
        self.assertTrue(callable(getattr(_bridge, "is_model_decline_response", None)))
        self.assertEqual(_bridge.MODEL_DECLINED_STATUS, "MODEL_DECLINED")

    def test_p40_compact_duration_intact(self):
        self.assertEqual(_bridge.format_compact_duration(737), "12m 17s")

    def test_p18_activity_monitor_intact(self):
        # الاسم الحقيقي لدالة P18: should_stop_on_activity_change — تغيّر المهام = وقف فوري
        changed, reason = _bridge.should_stop_on_activity_change(
            {"active": True, "tasks_remaining": 5},
            {"active": True, "tasks_remaining": 3})
        self.assertTrue(changed)
        self.assertTrue(reason)

    def test_failover_and_rotation_symbols_intact(self):
        for sym in ("send_message_with_auto_account_failover",
                    "send_message_and_make_public",
                    "present_resume_summary",
                    "present_external_resume_decision",
                    "lookup_project_key_for_locator",
                    "upsert_project_identity"):
            self.assertTrue(callable(getattr(_bridge, sym, None)), f"{sym} مفقودة")

    def test_backoff_logic_intact(self):
        self.assertIn("time.sleep(min(3 * consecutive_errors, 15) if consecutive_errors else 1)", _polling_src())


if __name__ == "__main__":
    unittest.main(verbosity=2)
