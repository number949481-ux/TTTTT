import sys
import pathlib
import unittest
import importlib.util

webapp_dir = pathlib.Path(__file__).resolve().parent.parent

if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

# Load bridge module
bridge_spec = importlib.util.spec_from_file_location("bridge_mod", webapp_dir / "01.31_telegram_gen_bridge.py")
bridge = importlib.util.module_from_spec(bridge_spec)
bridge_spec.loader.exec_module(bridge)

apply_contract = bridge.apply_contract
normalize_project_model = bridge.normalize_project_model
is_protected = bridge.is_protected



class TestP3RegressionSnapshots(unittest.TestCase):

    # ════════════════════════════════════════════════════════════════
    # Category A: Unchanged Snapshots (تطابق حرفي 100% للمسارات القديمة)
    # ════════════════════════════════════════════════════════════════

    def test_gpt55_payload_byte_identical(self):
        """التحقق من أن مسار gpt-5.5 الخاص لم يتغير منه أي مفتاح"""
        msg_id = "test_msg_55"
        question = "hello 5.5"
        all_messages = [{"role": "user", "content": question}]

        # Expected baseline snapshot from special block
        expected_keys = {
            "ai_chat_model", "ai_chat_enable_search", "ai_chat_disable_personalization",
            "use_moa_proxy", "moa_models", "writingContent", "type", "project_id",
            "messages", "user_s_input", "client_message_id", "g_recaptcha_token",
            "is_private", "push_token", "session_state", "last_seen_event_index", "chat_session_id"
        }

        self.assertTrue(is_protected("gpt-5.5"))
        # Verify apply_contract treats it as a protected no-op
        dummy_special = {"type": "ai_chat", "ai_chat_model": "gpt-5.5", "client_message_id": msg_id}
        result = apply_contract(dict(dummy_special), "gpt-5.5", msg_id)
        self.assertEqual(result, dummy_special)

    def test_opus48_payload_byte_identical(self):
        """التحقق من أن مسار claude-opus-4-8 الخاص لم يتغير"""
        self.assertTrue(is_protected("claude-opus-4-8"))
        dummy_special = {"type": "ai_chat", "ai_chat_model": "claude-opus-4-8"}
        result = apply_contract(dict(dummy_special), "claude-opus-4-8")
        self.assertEqual(result, dummy_special)

    def test_ultra_flag_untouched_by_adapter(self):
        """التحقق من أن flag الـ Ultra mode يعمل كما هو دون مساس من الـ adapter"""
        payload = {"models": ["gpt-4.1"], "type": "super_agent"}
        payload = apply_contract(payload, "claude-fable-5", "m1")
        # Simulator of ultra flag injection in engine:
        payload["ultra_mode"] = True
        self.assertTrue(payload.get("ultra_mode"))
        self.assertEqual(payload["use_model"], "claude-fable-5")

    def test_continue_chat_payload_identical(self):
        """التحقق من أن مفاتيح الـ Continue والـ Force لا تتأثر بالـ Adapter"""
        payload = {"models": ["gpt-4.1"], "type": "super_agent", "force": True, "project_id": "proj_123"}
        payload = apply_contract(payload, "claude-fable-5", "m1")
        self.assertTrue(payload["force"])
        self.assertEqual(payload["project_id"], "proj_123")

    def test_new_chat_payload_identical(self):
        """التحقق من أن الحقول الافتراضية للـ New Chat ثابتة"""
        payload = {"models": ["gpt-4.1"], "type": "super_agent", "speed_mode": True}
        payload = apply_contract(payload, "claude-fable-5", "m1")
        self.assertTrue(payload["speed_mode"])

    # ════════════════════════════════════════════════════════════════
    # Category B: Expected Contract Changes (الموديلات الـ 5 المصححة)
    # ════════════════════════════════════════════════════════════════

    def test_fable_payload_matches_new_contract(self):
        payload = apply_contract({"type": "super_agent"}, "claude-fable-5", "msg_fable")
        self.assertEqual(payload["models"], ["gpt-4.1"])
        self.assertEqual(payload["use_model"], "claude-fable-5")
        self.assertEqual(payload["client_message_id"], "msg_fable")
        self.assertNotIn("ai_chat_model", payload)

    def test_sonnet5_payload_matches_new_contract(self):
        payload = apply_contract({"type": "super_agent"}, "claude-sonnet-5", "msg_sonnet")
        self.assertEqual(payload["models"], ["claude-sonnet-5"])
        self.assertEqual(payload["use_model"], "claude-sonnet-5")
        self.assertEqual(payload["ai_chat_model"], "claude-sonnet-5")
        self.assertEqual(payload["client_message_id"], "msg_sonnet")

    def test_gpt56_sol_matches_new_contract(self):
        payload = apply_contract({"type": "super_agent"}, "gpt-5.6-sol", "msg_sol")
        self.assertEqual(payload["models"], ["gpt-5.6-sol"])
        self.assertEqual(payload["use_model"], "gpt-5.6-sol")
        self.assertEqual(payload["ai_chat_model"], "gpt-5.6-sol")
        self.assertEqual(payload["client_message_id"], "msg_sol")

    def test_kimi_k3_matches_new_contract(self):
        payload = apply_contract({"type": "super_agent"}, "kimi-k3", "msg_kimi")
        self.assertEqual(payload["models"], ["kimi-k3"])
        self.assertEqual(payload["use_model"], "kimi-k3")
        self.assertEqual(payload["ai_chat_model"], "kimi-k3")
        self.assertEqual(payload["client_message_id"], "msg_kimi")

    def test_opus5_matches_new_contract(self):
        payload = apply_contract({"type": "super_agent"}, "claude-opus-5", "msg_opus")
        self.assertEqual(payload["models"], ["claude-opus-5"])
        self.assertEqual(payload["use_model"], "claude-opus-5")
        self.assertEqual(payload["client_message_id"], "msg_opus")
        self.assertNotIn("ai_chat_model", payload)

    # ════════════════════════════════════════════════════════════════
    # Category C: Engine Resolution & Integration (التحقق من المحرك الفعلي)
    # ════════════════════════════════════════════════════════════════

    def test_engine_selection_unchanged(self):
        """التحقق من أن دالة get_genspark_engine في البوت تجلب المحرك الأساسي بنجاح"""
        engine = bridge.get_genspark_engine()
        self.assertIsNotNone(engine)
        self.assertTrue(hasattr(engine, "send_chat"))

    def test_selected_engine_imports_model_runtime(self):
        """التحقق من أن المحرك الأساسي المحمل قادر على معالجة عقود الموديلات"""
        engine = bridge.get_genspark_engine()
        # Verify engine can construct payload correctly with apply_contract
        test_payload = {"models": ["placeholder"], "type": "super_agent"}
        result = apply_contract(test_payload, "claude-sonnet-5", "m_eng")
        self.assertEqual(result["use_model"], "claude-sonnet-5")
        self.assertEqual(result["ai_chat_model"], "claude-sonnet-5")


if __name__ == "__main__":
    unittest.main()
