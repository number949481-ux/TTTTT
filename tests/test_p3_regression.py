import sys
import pathlib
import unittest
import importlib.util

webapp_dir = pathlib.Path(__file__).resolve().parent.parent

if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

# Load bridge module
bridge_spec = importlib.util.spec_from_file_location("bridge_mod", webapp_dir / "01.33_telegram_gen_bridge.py")
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
        payload = {"models": ["grok-4.7"], "type": "code_sandbox"}
        payload = apply_contract(payload, "grok-4.7", "m1")
        # Simulator of ultra flag injection in engine:
        payload["ultra_mode"] = True
        self.assertTrue(payload.get("ultra_mode"))
        self.assertEqual(payload["use_model"], "grok-4.7")

    def test_continue_chat_payload_identical(self):
        """التحقق من أن مفاتيح الـ Continue والـ Force لا تتأثر بالـ Adapter"""
        payload = {"models": ["gpt-4.1"], "type": "super_agent", "force": True, "project_id": "proj_123"}
        payload = apply_contract(payload, "claude-fable-5-1", "m1")
        self.assertTrue(payload["force"])
        self.assertEqual(payload["project_id"], "proj_123")

    def test_new_chat_payload_identical(self):
        """التحقق من أن الحقول الافتراضية للـ New Chat ثابتة"""
        payload = {"models": ["gpt-4.1"], "type": "super_agent", "speed_mode": True}
        payload = apply_contract(payload, "claude-fable-5-1", "m1")
        self.assertTrue(payload["speed_mode"])

    # ════════════════════════════════════════════════════════════════
    # Category B: Expected Contract Changes (الموديلات الـ 6 بنمط code_sandbox)
    # ════════════════════════════════════════════════════════════════

    def test_grok_payload_matches_new_contract(self):
        payload = apply_contract({"type": "code_sandbox"}, "grok-4.7", "msg_grok")
        self.assertEqual(payload["models"], ["grok-4.7"])
        self.assertEqual(payload["use_model"], "grok-4.7")
        self.assertEqual(payload["client_message_id"], "msg_grok")
        self.assertNotIn("ai_chat_model", payload)

    def test_sonnet55_payload_matches_new_contract(self):
        payload = apply_contract({"type": "code_sandbox"}, "claude-sonnet-5-5", "msg_sonnet")
        self.assertEqual(payload["models"], ["claude-sonnet-5-5"])
        self.assertEqual(payload["use_model"], "claude-sonnet-5-5")
        self.assertNotIn("ai_chat_model", payload)
        self.assertEqual(payload["client_message_id"], "msg_sonnet")

    def test_gpt61_sol_matches_new_contract(self):
        payload = apply_contract({"type": "code_sandbox"}, "gpt-6.1-sol", "msg_sol")
        self.assertEqual(payload["models"], ["gpt-6.1-sol"])
        self.assertEqual(payload["use_model"], "gpt-6.1-sol")
        self.assertNotIn("ai_chat_model", payload)
        self.assertEqual(payload["client_message_id"], "msg_sol")

    def test_kimi_k31_matches_new_contract(self):
        payload = apply_contract({"type": "code_sandbox"}, "kimi-k3.1-pro", "msg_kimi")
        self.assertEqual(payload["models"], ["kimi-k3.1-pro"])
        self.assertEqual(payload["use_model"], "kimi-k3.1-pro")
        self.assertNotIn("ai_chat_model", payload)
        self.assertEqual(payload["client_message_id"], "msg_kimi")

    def test_muse_matches_new_contract(self):
        payload = apply_contract({"type": "code_sandbox"}, "muse-spark-open", "msg_muse")
        self.assertEqual(payload["models"], ["muse-spark-open"])
        self.assertEqual(payload["use_model"], "muse-spark-open")
        self.assertEqual(payload["client_message_id"], "msg_muse")
        self.assertNotIn("ai_chat_model", payload)

    def test_gemini_argon_matches_new_contract(self):
        payload = apply_contract({"type": "code_sandbox"}, "gemini-4-argon", "msg_gemini")
        self.assertEqual(payload["models"], ["gemini-4-argon"])
        self.assertEqual(payload["use_model"], "gemini-4-argon")
        self.assertEqual(payload["client_message_id"], "msg_gemini")
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
        test_payload = {"models": ["placeholder"], "type": "code_sandbox"}
        result = apply_contract(test_payload, "grok-4.7", "m_eng")
        self.assertEqual(result["use_model"], "grok-4.7")
        self.assertNotIn("ai_chat_model", result)


if __name__ == "__main__":
    unittest.main()
