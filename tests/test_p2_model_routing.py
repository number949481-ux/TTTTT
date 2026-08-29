import sys
import pathlib
import unittest

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

import importlib.util
_bridge_spec = importlib.util.spec_from_file_location("bridge_mod", webapp_dir / "01.33_telegram_gen_bridge.py")
_bridge = importlib.util.module_from_spec(_bridge_spec)
_bridge_spec.loader.exec_module(_bridge)
apply_contract = _bridge.apply_contract
normalize_project_model = _bridge.normalize_project_model
is_protected = _bridge.is_protected
PROTECTED_MODELS = _bridge.PROTECTED_MODELS



class TestP2ModelRouting(unittest.TestCase):
    def test_fable_models_is_gpt41_hardcoded(self):
        payload = apply_contract({}, "claude-fable-5", "msg_001")
        self.assertEqual(payload["models"], ["gpt-4.1"])
        self.assertEqual(payload["use_model"], "claude-fable-5")
        self.assertNotIn("ai_chat_model", payload)
        self.assertEqual(payload["client_message_id"], "msg_001")

    def test_opus5_has_no_ai_chat_model(self):
        payload = apply_contract({}, "claude-opus-5", "msg_002")
        self.assertEqual(payload["models"], ["claude-opus-5"])
        self.assertEqual(payload["use_model"], "claude-opus-5")
        self.assertNotIn("ai_chat_model", payload)
        self.assertEqual(payload["client_message_id"], "msg_002")

    def test_sonnet5_has_both_use_and_ai_chat(self):
        payload = apply_contract({}, "claude-sonnet-5", "msg_003")
        self.assertEqual(payload["models"], ["claude-sonnet-5"])
        self.assertEqual(payload["use_model"], "claude-sonnet-5")
        self.assertEqual(payload["ai_chat_model"], "claude-sonnet-5")
        self.assertEqual(payload["client_message_id"], "msg_003")

    def test_gpt56_sol_contract(self):
        payload = apply_contract({}, "gpt-5.6-sol", "msg_004")
        self.assertEqual(payload["models"], ["gpt-5.6-sol"])
        self.assertEqual(payload["use_model"], "gpt-5.6-sol")
        self.assertEqual(payload["ai_chat_model"], "gpt-5.6-sol")
        self.assertEqual(payload["client_message_id"], "msg_004")

    def test_kimi_k3_contract(self):
        payload = apply_contract({}, "kimi-k3", "msg_005")
        self.assertEqual(payload["models"], ["kimi-k3"])
        self.assertEqual(payload["use_model"], "kimi-k3")
        self.assertEqual(payload["ai_chat_model"], "kimi-k3")
        self.assertEqual(payload["client_message_id"], "msg_005")

    def test_unknown_gets_models_key_only(self):
        payload = apply_contract({}, "unknown-future-model", "msg_006")
        self.assertEqual(payload["models"], ["unknown-future-model"])
        self.assertNotIn("use_model", payload)
        self.assertNotIn("ai_chat_model", payload)
        self.assertNotIn("client_message_id", payload)

    def test_protected_is_noop_and_logs_warning(self):
        original = {"type": "traditional", "foo": "bar"}
        payload = apply_contract(dict(original), "gpt-5.5", "msg_007")
        self.assertEqual(payload, original)
        self.assertTrue(is_protected("gpt-5.5"))
        self.assertTrue(is_protected("claude-opus-4-8"))
        self.assertTrue(is_protected("GPT 5.5"))

    def test_normalize_always_returns_str(self):
        self.assertEqual(normalize_project_model(None), "claude-fable-5")
        self.assertEqual(normalize_project_model(""), "claude-fable-5")
        self.assertEqual(normalize_project_model("Claude Fable 5"), "claude-fable-5")
        self.assertEqual(normalize_project_model("Claude Sonnet 5"), "claude-sonnet-5")
        self.assertEqual(normalize_project_model("GPT 5.6 sol"), "gpt-5.6-sol")
        self.assertEqual(normalize_project_model("Kimi K3"), "kimi-k3")
        self.assertEqual(normalize_project_model("GPT 5.5"), "gpt-5.5")
        self.assertEqual(normalize_project_model("Claude Opus 4.8"), "claude-opus-4-8")
        self.assertEqual(normalize_project_model("invalid_xyz_model"), "claude-fable-5")
        # Ensure return type is strictly str
        self.assertIsInstance(normalize_project_model("claude-fable-5"), str)


if __name__ == "__main__":
    unittest.main()
