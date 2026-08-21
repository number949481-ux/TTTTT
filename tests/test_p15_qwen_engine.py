# -*- coding: utf-8 -*-
"""
[P15] اختبارات استقلال محرك كوين (qwen_engine.py) + ترقية 01.31

يغطي:
  1. الموديول qwen_engine يستورد بأمان وبدون side effects.
  2. اكتمال المكونات المنقولة 100% (27 مكوناً: ثوابت + دوال + قفل).
  3. 04_upload_to_Fable_github.py يستورد من الموديول ولا يحتفظ بنسخ مكررة.
  4. حقن اللوجر (configure) يعمل.
  5. الإصدار 01.31: بانر جديد + BUILD_VERSION + مراجع scripts/tests.
"""
import importlib.util
import os
import threading
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_PATH = os.path.join(BASE_DIR, "qwen_engine.py")
UPLOADER_PATH = os.path.join(BASE_DIR, "04_upload_to_Fable_github.py")
BRIDGE_PATH = os.path.join(BASE_DIR, "01.32_telegram_gen_bridge.py")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


QE = _load("qwen_engine_p15", ENGINE_PATH)
UPLOADER_SRC = open(UPLOADER_PATH, encoding="utf-8").read()
ENGINE_SRC = open(ENGINE_PATH, encoding="utf-8").read()
BRIDGE_SRC = open(BRIDGE_PATH, encoding="utf-8").read()

# قائمة المكونات الكاملة المطلوب نقلها (عقد المالك — 27 مكوناً)
REQUIRED_COMPONENTS = [
    # ⚙️ الإعدادات وسلسلة الموديلات
    "AI_ENABLED", "AI_MODEL_CHAIN", "AI_MAX_DIFF_CHARS", "AI_MIN_VALID_CHARS",
    "AI_RACE_ACCOUNTS", "AI_FALLBACK_COMMIT_MSG",
    "QWEN_ACCOUNTS_FILE", "DEFAULT_QWEN_ACCOUNTS", "load_or_create_qwen_accounts",
    # 🌈 شريط التقدم الملون
    "SPECTRUM_256", "get_rainbow_color", "get_second_rainbow_color",
    "render_seconds_progress_bar",
    # 🏁 محرك السباق
    "_QWEN_FILE_LOCK", "_reset_ai_race_state", "_qwen_time_left",
    "_qwen_worker", "qwenguest_worker", "race_accounts",
    "_select_race_indices", "_call_qwen_ai_direct",
    # 🔄 التجديد وحفظ الفائز
    "_save_qwen_accounts", "auto_refresh_qwen_account", "_save_qwen_winner_cookies",
    # 🤖 استخراج الرد
    "generate_ai_summary",
    # 📢 واجهة الحقن
    "configure", "log_message",
]


class TestP15EngineCompleteness(unittest.TestCase):
    """اكتمال الموديول المستقل 100%."""

    def test_01_all_27_components_present(self):
        missing = [n for n in REQUIRED_COMPONENTS if not hasattr(QE, n)]
        self.assertEqual(missing, [], f"مكونات ناقصة في qwen_engine: {missing}")

    def test_02_model_chain_contract(self):
        """سلسلة الموديلات: مرحلتان بمهلة 30s + Thinking/Fast."""
        self.assertEqual(len(QE.AI_MODEL_CHAIN), 2)
        for cfg in QE.AI_MODEL_CHAIN:
            self.assertEqual(cfg["timeout"], 30)
            self.assertIn("thinking_mode", cfg)
            self.assertIn("thinking_enabled", cfg)
        self.assertTrue(QE.AI_MODEL_CHAIN[0]["thinking_enabled"])   # Thinking
        self.assertFalse(QE.AI_MODEL_CHAIN[1]["thinking_enabled"])  # Fast

    def test_03_constants_values(self):
        self.assertEqual(QE.AI_MAX_DIFF_CHARS, 15000)
        self.assertEqual(QE.AI_MIN_VALID_CHARS, 20)
        self.assertEqual(QE.AI_RACE_ACCOUNTS, 0)
        self.assertTrue(QE.QWEN_ACCOUNTS_FILE.endswith("accounts_qwen.json"))
        self.assertGreaterEqual(len(QE.DEFAULT_QWEN_ACCOUNTS), 3)

    def test_04_file_lock_is_real_lock(self):
        """القفل الذري _QWEN_FILE_LOCK موجود وقابل للاستخدام."""
        self.assertIsInstance(QE._QWEN_FILE_LOCK, type(threading.Lock()))

    def test_05_dalvik_android15_headers_in_workers(self):
        """هيدرات Dalvik / Android 15 موجودة في ثريد الحسابات وثريد الزائر."""
        self.assertIn("Dalvik/2.1.0 (Linux; U; Android 15", ENGINE_SRC)
        self.assertIn('"X-Platform": "android"', ENGINE_SRC)
        # في الاتنين: _qwen_worker و qwenguest_worker
        self.assertGreaterEqual(ENGINE_SRC.count("Dalvik/2.1.0"), 2)

    def test_06_sse_streaming_and_stop_event(self):
        """تدفق SSE مع الإلغاء الفوري بـ stop_event في العاملين."""
        self.assertIn("stream=True", ENGINE_SRC)
        self.assertIn("iter_lines()", ENGINE_SRC)
        self.assertGreaterEqual(ENGINE_SRC.count("stop_event.is_set()"), 6)

    def test_07_guest_worker_runs_in_parallel(self):
        """ثريد الزائر يُطلق بالتوازي داخل race_accounts (Bypass احتياطي)."""
        import re
        m = re.search(r"def race_accounts\(.*?\n(?=\ndef |\Z)", ENGINE_SRC, re.DOTALL)
        self.assertIsNotNone(m)
        body = m.group(0)
        self.assertIn("executor.submit(qwenguest_worker", body)
        self.assertIn("render_seconds_progress_bar", body)
        self.assertIn("stop_event.set()", body)
        self.assertIn("_save_qwen_winner_cookies", body)

    def test_08_auto_refresh_uses_password_hash(self):
        import re
        m = re.search(r"def auto_refresh_qwen_account\(.*?\n(?=\ndef |\Z)", ENGINE_SRC, re.DOTALL)
        self.assertIsNotNone(m)
        body = m.group(0)
        self.assertIn("password_hash", body)
        self.assertIn("api/v2/auths/signin", body)
        self.assertIn("_save_qwen_accounts", body)

    def test_09_logger_injection_works(self):
        captured = []
        QE.configure(log_func=lambda msg, color=None: captured.append(str(msg)))
        try:
            QE.log_message("p15-injection-test")
            self.assertTrue(any("p15-injection-test" in m for m in captured))
        finally:
            QE._LOG_FUNC = None  # إعادة الحالة الافتراضية

    def test_10_generate_ai_summary_parses_commit_and_summary(self):
        """استخراج COMMIT/SUMMARY من الرد — عبر حقن رد وهمي بدون شبكة."""
        original = QE._call_qwen_ai_direct
        QE._call_qwen_ai_direct = lambda prompt: (
            "COMMIT: إضافة نظام اختبار وهمي للتحقق\nSUMMARY: ملخص تجريبي للاختبار الوظيفي.",
            "Qwen3.8-Max",
        )
        try:
            commit, summary, model = QE.generate_ai_summary("files", "diff", [])
            self.assertEqual(commit, "إضافة نظام اختبار وهمي للتحقق")
            self.assertIn("ملخص تجريبي", summary)
            self.assertEqual(model, "Qwen3.8-Max")
        finally:
            QE._call_qwen_ai_direct = original


class TestP15UploaderDelegation(unittest.TestCase):
    """04 يستورد من الموديول ولا يحتفظ بنسخ مكررة."""

    def test_11_uploader_imports_engine(self):
        self.assertIn("import qwen_engine", UPLOADER_SRC)
        self.assertIn("from qwen_engine import", UPLOADER_SRC)
        self.assertIn("qwen_engine.configure(log_func=log_message)", UPLOADER_SRC)

    def test_12_no_duplicate_engine_functions_in_uploader(self):
        """ممنوع بقاء نسخ مكررة من دوال كوين داخل 04."""
        for fn in ["def _qwen_worker(", "def qwenguest_worker(", "def race_accounts(",
                   "def auto_refresh_qwen_account(", "def _call_qwen_ai_direct(",
                   "def generate_ai_summary(", "def load_or_create_qwen_accounts(",
                   "def render_seconds_progress_bar(", "def _save_qwen_winner_cookies("]:
            self.assertNotIn(fn, UPLOADER_SRC, f"نسخة مكررة باقية في 04: {fn}")

    def test_13_uploader_module_loads_with_compat_names(self):
        mod = _load("uploader04_p15", UPLOADER_PATH)
        for n in ["AI_ENABLED", "AI_MODEL_CHAIN", "generate_ai_summary",
                  "race_accounts", "load_or_create_qwen_accounts",
                  "sync_tree", "detect_best_source_root"]:
            self.assertTrue(hasattr(mod, n), f"اسم متوافق مفقود في 04: {n}")

    def test_14_winner_state_accessed_via_module(self):
        """LAST_AI_* تُقرأ من qwen_engine (globals حية) وليس نسخة ميتة."""
        self.assertIn("qwen_engine.LAST_AI_ACCOUNT", UPLOADER_SRC)
        self.assertIn("qwen_engine.LAST_AI_SOURCE", UPLOADER_SRC)
        self.assertIn("qwen_engine.LAST_AI_ELAPSED", UPLOADER_SRC)


class TestP15VersionBump(unittest.TestCase):
    """ترقية 01.31: بانر + إصدار + مراجع."""

    def test_15_bridge_0128_banner_and_version(self):
        self.assertIn("01.32_telegram_gen_bridge.py", BRIDGE_SRC[:1200])
        self.assertIn('BUILD_VERSION = "01.32"', BRIDGE_SRC)
        self.assertIn('BUILD_PARENT_BASELINE = "01.30"', BRIDGE_SRC)
        # البانر الجديد يعكس P12..P19 + P20
        self.assertIn("P12..P19 + P20", BRIDGE_SRC[:1500])
        self.assertIn("تبريد 29h", BRIDGE_SRC[:1800])

    def test_16_scripts_reference_0128(self):
        gate = open(os.path.join(BASE_DIR, "scripts", "hadith_sijil.py"), encoding="utf-8").read()
        rebuild = open(os.path.join(BASE_DIR, "scripts", "rebuild_refactor.py"), encoding="utf-8").read()
        self.assertIn("01.32_telegram_gen_bridge.py", gate)
        self.assertNotIn("01.27_telegram_gen_bridge.py", gate)
        self.assertIn("01.32_telegram_gen_bridge.py", rebuild)
        self.assertNotIn("01.27_telegram_gen_bridge.py", rebuild)


if __name__ == "__main__":
    unittest.main(verbosity=2)
