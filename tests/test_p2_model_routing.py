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
format_model_display_label = _bridge.format_model_display_label
MODEL_DISPLAY_NAMES = _bridge.MODEL_DISPLAY_NAMES
is_protected = _bridge.is_protected
PROTECTED_MODELS = _bridge.PROTECTED_MODELS



class TestP2ModelRouting(unittest.TestCase):
    def test_grok_contract(self):
        payload = apply_contract({}, "grok-4.7", "msg_001")
        self.assertEqual(payload["models"], ["grok-4.7"])
        self.assertEqual(payload["use_model"], "grok-4.7")
        self.assertNotIn("ai_chat_model", payload)
        self.assertEqual(payload["client_message_id"], "msg_001")

    def test_muse_contract(self):
        payload = apply_contract({}, "muse-spark-open", "msg_002")
        self.assertEqual(payload["models"], ["muse-spark-open"])
        self.assertEqual(payload["use_model"], "muse-spark-open")
        self.assertNotIn("ai_chat_model", payload)
        self.assertEqual(payload["client_message_id"], "msg_002")

    def test_sonnet55_contract(self):
        payload = apply_contract({}, "claude-sonnet-5-5", "msg_003")
        self.assertEqual(payload["models"], ["claude-sonnet-5-5"])
        self.assertEqual(payload["use_model"], "claude-sonnet-5-5")
        self.assertNotIn("ai_chat_model", payload)
        self.assertEqual(payload["client_message_id"], "msg_003")

    def test_gemini_argon_contract(self):
        payload = apply_contract({}, "gemini-4-argon", "msg_008")
        self.assertEqual(payload["models"], ["gemini-4-argon"])
        self.assertEqual(payload["use_model"], "gemini-4-argon")
        self.assertNotIn("ai_chat_model", payload)
        self.assertEqual(payload["client_message_id"], "msg_008")

    def test_gpt61_sol_contract(self):
        payload = apply_contract({}, "gpt-6.1-sol", "msg_004")
        self.assertEqual(payload["models"], ["gpt-6.1-sol"])
        self.assertEqual(payload["use_model"], "gpt-6.1-sol")
        self.assertNotIn("ai_chat_model", payload)
        self.assertEqual(payload["client_message_id"], "msg_004")

    def test_kimi_k31_contract(self):
        payload = apply_contract({}, "kimi-k3.1-pro", "msg_005")
        self.assertEqual(payload["models"], ["kimi-k3.1-pro"])
        self.assertEqual(payload["use_model"], "kimi-k3.1-pro")
        self.assertNotIn("ai_chat_model", payload)
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
        self.assertEqual(normalize_project_model(None), "grok-4.7")
        self.assertEqual(normalize_project_model(""), "grok-4.7")
        self.assertEqual(normalize_project_model("Claude Fable 5.1"), "grok-4.7")
        self.assertEqual(normalize_project_model("🧠 Claude Fable 5.1"), "grok-4.7")
        self.assertEqual(normalize_project_model("Grok 4.7"), "grok-4.7")
        self.assertEqual(normalize_project_model("🌌 Grok 4.7"), "grok-4.7")
        self.assertEqual(normalize_project_model("Claude Sonnet 5"), "claude-sonnet-5-5")
        self.assertEqual(normalize_project_model("GPT-6 Astra"), "gemini-4-argon")
        self.assertEqual(normalize_project_model("⚡ GPT-6 Astra"), "gemini-4-argon")
        self.assertEqual(normalize_project_model("GPT 5.6 sol"), "gpt-6.1-sol")
        self.assertEqual(normalize_project_model("Kimi K3"), "kimi-k3.1-pro")
        self.assertEqual(normalize_project_model("GPT 5.5"), "gpt-5.5")
        self.assertEqual(normalize_project_model("Claude Opus 4.8"), "claude-opus-4-8")
        self.assertEqual(normalize_project_model("invalid_xyz_model"), "grok-4.7")
        # Ensure return type is strictly str
        self.assertIsInstance(normalize_project_model("grok-4.7"), str)

    def test_format_model_display_label(self):
        self.assertEqual(format_model_display_label("grok-4.7"), "🌌 Grok 4.7")
        self.assertEqual(format_model_display_label("muse-spark-open"), "🎨 Muse Spark Open")
        self.assertEqual(format_model_display_label("claude-sonnet-5-5"), "🎭 Claude Sonnet 5.5")
        self.assertEqual(format_model_display_label("gemini-4-argon"), "💎 Gemini 4 Argon")
        self.assertEqual(format_model_display_label("gpt-6.1-sol"), "☀️ GPT-6.1 Sol")
        self.assertEqual(format_model_display_label("kimi-k3.1-pro"), "🚀 Kimi K3.1 Pro")
        # None and empty fallback to default formatted
        self.assertEqual(format_model_display_label(None), "🌌 Grok 4.7")
        self.assertEqual(format_model_display_label(""), "🌌 Grok 4.7")
        # Aliases format to canonical display name
        self.assertEqual(format_model_display_label("GPT-6 Astra"), "💎 Gemini 4 Argon")
        self.assertEqual(format_model_display_label("astra"), "💎 Gemini 4 Argon")
        self.assertEqual(format_model_display_label("kimi k3"), "🚀 Kimi K3.1 Pro")


if __name__ == "__main__":
    unittest.main()
