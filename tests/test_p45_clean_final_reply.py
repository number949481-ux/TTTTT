"""
test_p45_clean_final_reply.py
=============================
🧼 [P45] حراس تنظيف الرد النهائي الصافي (Clean Final Answer):

  A. clean_assistant_reply — التطهير الدفاعي SSOT:
     إزالة كتل <thought|thinking|antThinking> + بادئات Assistant:
     + no-op على النص النظيف + سلامة None/غير-نص.
  B. fetch_final_reply_text المحصّنة:
     تخطّي أغلفة الأدوات (assistant + tool_calls) والرسائل الفارغة
     + تمرير الناتج على clean_assistant_reply
     + Fail-Open لو التنظيف أفرغ الرد بالكامل.
  C. تطابق p05 (VERBATIM SLICE) مع المرجع 01.33 + صفر ارتجاع لعقود P44.

مرجع القرار: genspark-session-bridge/09_FINAL_REPLY_CLEANUP_PLAN.md
(الفلترة بالحقول الحقيقية tool_calls/role/content — لا يوجد is_tool_call).
"""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIDGE_PATH = ROOT / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_p45", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("bridge_p45", _bridge)
_spec.loader.exec_module(_bridge)

FINAL = "إليك الرد النهائي المكتمل بعد إنجاز كل المهام المطلوبة بنجاح."


# ═══════════════════════════════════════════════════════════════
# A — clean_assistant_reply
# ═══════════════════════════════════════════════════════════════
class TestCleanAssistantReply(unittest.TestCase):
    def test_01_removes_thought_block(self):
        dirty = f"<thought>تفكير داخلي سري</thought>{FINAL}"
        self.assertEqual(_bridge.clean_assistant_reply(dirty), FINAL)

    def test_02_removes_all_tag_variants_case_insensitive(self):
        for tag in ("thought", "thinking", "antThinking", "THOUGHT", "Thinking"):
            with self.subTest(tag=tag):
                dirty = f"<{tag}>سر</{tag}>{FINAL}"
                self.assertEqual(_bridge.clean_assistant_reply(dirty), FINAL)

    def test_03_removes_multiline_and_multiple_blocks(self):
        dirty = (f"<thought>سطر 1\nسطر 2\nسطر 3</thought>{FINAL}"
                 f"<thinking>\nكتلة تانية\n</thinking>")
        self.assertEqual(_bridge.clean_assistant_reply(dirty), FINAL)

    def test_04_strips_assistant_prefix(self):
        self.assertEqual(
            _bridge.clean_assistant_reply(f"Assistant: {FINAL}"), FINAL)
        self.assertEqual(
            _bridge.clean_assistant_reply(f"  assistant:  Assistant: {FINAL}"), FINAL)

    def test_05_noop_on_clean_text(self):
        """النص النظيف يخرج كما هو (بعد strip فقط) — صفر ضرر."""
        self.assertEqual(_bridge.clean_assistant_reply(f"  {FINAL}  "), FINAL)
        # نص يحتوي كود فيه < > عادية لا يُمس
        code = "استخدم if x < 10 and y > 3: طبيعي <div>html</div>"
        self.assertEqual(_bridge.clean_assistant_reply(code), code)

    def test_06_none_and_non_string_safe(self):
        for bad in (None, "", 0, [], {}, 3.14):
            with self.subTest(val=bad):
                self.assertEqual(_bridge.clean_assistant_reply(bad), "")

    def test_07_all_cot_reply_becomes_empty(self):
        """رد كله CoT → سلسلة فارغة (الـ caller مسؤول عن الـ Fail-Open)."""
        self.assertEqual(
            _bridge.clean_assistant_reply("<thought>فقط تفكير</thought>"), "")


# ═══════════════════════════════════════════════════════════════
# B — fetch_final_reply_text المحصّنة
# ═══════════════════════════════════════════════════════════════
class TestHardenedFinalFetch(unittest.TestCase):
    def _fetch(self, msgs, old="النص القديم المحفوظ"):
        mod = types.SimpleNamespace(
            fetch_project_messages=mock.Mock(return_value=msgs))
        with mock.patch.object(_bridge, "log_event") as spy:
            got = _bridge.fetch_final_reply_text(
                mod, "pid-p45", {}, None, old, email="t@t")
        return got, [str(c) for c in spy.call_args_list]

    def test_01_skips_tool_call_wrapper(self):
        """غلاف أداة أخير (assistant + tool_calls) يُتخطى للرد الحقيقي قبله."""
        got, logged = self._fetch([
            {"role": "user", "content": "برومبت"},
            {"role": "assistant", "content": FINAL},
            {"role": "assistant", "content": "",
             "tool_calls": [{"id": "call_1", "type": "function"}]},
            {"role": "tool", "tool_call_id": "call_1", "content": "Applied 3 edits"},
        ])
        self.assertEqual(got, FINAL)
        self.assertTrue(any("FINAL_FETCH_OK" in l for l in logged))

    def test_02_skips_tool_wrapper_even_with_content(self):
        """غلاف أداة له content (زي Applied edits) يُتخطى برضو — tool_calls حاسمة."""
        got, _ = self._fetch([
            {"role": "assistant", "content": FINAL},
            {"role": "assistant", "content": "Applied 3 edits to file X",
             "tool_calls": [{"id": "c2"}]},
        ])
        self.assertEqual(got, FINAL)

    def test_03_skips_empty_and_whitespace_assistants(self):
        got, _ = self._fetch([
            {"role": "assistant", "content": FINAL},
            {"role": "assistant", "content": ""},
            {"role": "assistant", "content": "   \n  "},
        ])
        self.assertEqual(got, FINAL)

    def test_04_skips_tool_role_messages(self):
        got, _ = self._fetch([
            {"role": "assistant", "content": FINAL},
            {"role": "tool", "tool_call_id": "c1", "content": "exit_code=0"},
        ])
        self.assertEqual(got, FINAL)

    def test_05_cleans_cot_from_fetched_reply(self):
        got, _ = self._fetch([
            {"role": "assistant",
             "content": f"<thought>خطة داخلية</thought>{FINAL}"},
        ])
        self.assertEqual(got, FINAL)

    def test_06_fail_open_when_cleaning_empties_reply(self):
        """رد كله CoT → بعد التنظيف فارغ → Fail-Open بالنص القديم + Telemetry."""
        old = "النص الوسطي القديم من البث"
        got, logged = self._fetch(
            [{"role": "assistant", "content": "<thought>كله تفكير</thought>"}],
            old=old)
        self.assertEqual(got, old)
        self.assertTrue(any("FINAL_FETCH_FALLBACK" in l for l in logged))

    def test_07_fail_open_when_only_tool_wrappers_exist(self):
        """كل رسائل الـ assistant أغلفة أدوات → لا مرشح → النص القديم."""
        old = "آخر نص سليم من البث المباشر"
        got, logged = self._fetch(
            [{"role": "assistant", "content": "", "tool_calls": [{"id": "c"}]},
             {"role": "tool", "content": "output"}],
            old=old)
        self.assertEqual(got, old)
        self.assertTrue(any("FINAL_FETCH_FALLBACK" in l for l in logged))

    def test_08_p44_contracts_unbroken(self):
        """صفر ارتجاع P44: النجاح العادي + كل حالات الفشل القديمة كما هي."""
        # نجاح عادي (نفس فيكستشر test_p44 رقم 06)
        got, _ = self._fetch([
            {"role": "user", "content": "برومبت"},
            {"role": "assistant", "content": "رد وسطي قديم"},
            {"role": "assistant", "content": FINAL},
            {"role": "user", "content": "تابع"},
        ])
        self.assertEqual(got, FINAL)
        # حالات الفشل الأربع القديمة → Fail-Open
        old = "قديم يجب أن يبقى"
        cases = {
            "network-error": types.SimpleNamespace(
                fetch_project_messages=mock.Mock(side_effect=RuntimeError("net"))),
            "no-messages": types.SimpleNamespace(
                fetch_project_messages=mock.Mock(return_value=[])),
            "empty-content": types.SimpleNamespace(
                fetch_project_messages=mock.Mock(return_value=[
                    {"role": "assistant", "content": "   "}])),
            "engine-without-fetch": types.SimpleNamespace(),
        }
        for name, mod in cases.items():
            with self.subTest(case=name):
                with mock.patch.object(_bridge, "log_event"):
                    got = _bridge.fetch_final_reply_text(
                        mod, "pid", {}, None, old, email="t@t")
                self.assertEqual(got, old)

    def test_09_none_tool_calls_field_is_not_wrapper(self):
        """tool_calls=None (زي _NULL_MSG_FIELDS) = رسالة حقيقية مش غلاف."""
        got, _ = self._fetch([
            {"role": "assistant", "content": FINAL, "tool_calls": None},
        ])
        self.assertEqual(got, FINAL)


# ═══════════════════════════════════════════════════════════════
# C — تطابق البنية والمصدر
# ═══════════════════════════════════════════════════════════════
class TestSourceIntegrity(unittest.TestCase):
    P05 = (ROOT / "bridge_refactor" / "parts" / "p05_project_tree.py").read_text(
        encoding="utf-8")

    def test_01_p05_contains_p45_symbols(self):
        """p05 (VERBATIM SLICE) يحمل الدالة والتحصين — لا تفرّع عن المرجع."""
        for needle in ("def clean_assistant_reply",
                       'and not m.get("tool_calls")',
                       "clean_assistant_reply(str(final_c))"):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.P05)
                self.assertIn(needle, BRIDGE_SRC)

    def test_02_no_imaginary_is_tool_call_field(self):
        """الحقل المتخيَّل is_tool_call ممنوع — الفلترة بالحقول الحقيقية فقط."""
        self.assertNotIn("is_tool_call", BRIDGE_SRC)
        self.assertNotIn("is_tool_call", self.P05)

    def test_03_engine_golden_baseline_untouched(self):
        """المحرك 01.03 = Golden Baseline — ممنوع يظهر فيه clean_assistant_reply."""
        eng = (ROOT / "01.03Genspark_claude-opus-5-code.py").read_text(
            encoding="utf-8")
        self.assertNotIn("clean_assistant_reply", eng)

    def test_04_runtime_exposes_p45_function(self):
        """runtime المجمَّع من الأجزاء يصدّر الدالة الجديدة فعلياً."""
        from bridge_refactor import runtime
        self.assertTrue(hasattr(runtime.ns, "clean_assistant_reply"))
        self.assertEqual(
            runtime.ns.clean_assistant_reply(f"<thought>x</thought>{FINAL}"),
            FINAL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
