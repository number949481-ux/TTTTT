"""
test_p38_unified_account_email_display.py
=========================================
حزمة حراسة [P38] — توحيد عرض إيميل الحساب النشط عبر كل بطاقات دورة حياة
المشروع (Unified Active Account Email Across All Project Lifecycle Cards):

قبل P38 كان الإيميل يظهر في بطاقة الاكتمال فقط (بتسمية «الحساب المستعمل»)
بينما بطاقات اللايف الفوري وhandoff الرصيد واللقطة/المزامنة بلا أي إيميل —
والبارامتر stage_email كان يصل من المحرك ثم يُهمل. منذ P38:

  1. دالة مركزية format_active_account_line(raw_email) — مصدر واحد للحقيقة:
     تفريغ/تقليم آمن ➔ fallback «غير محدد» ➔ html_escape ➔
     "📧 <b>الحساب:</b> <code>{email}</code>\n".
  2. حقن السطر الموحد في البطاقات الخمس:
     • ⚡ handle_live_project_start (اللايف الفوري) عبر getattr الآمن من cfg.
     • 🔁 on_credit_handoff (نفاد الرصيد/التحويل) عبر getattr الآمن من cfg.
     • 🔄 on_project_update (اللقطة/المزامنة) عبر stage_email أولاً ثم cfg.
     • ✅/🚫 بطاقة الاكتمال/الرفض (res_msg المشتركة): توحيد التسمية إلى
       «📧 الحساب:» مع الحفاظ الحرفي على {journey_block} (عقد P29) وبلا
       تهريب مزدوج (acc_email مُهرَّب مسبقاً).
     • 🟢 بطاقة اللايف المكتملة (P7-A) عبر used_acc.get("email").
  3. Zero Breaking: لا مساس بأي عقد قائم — getattr(cfg, ...) لا يرمي أبداً.
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
    spec = importlib.util.spec_from_file_location("bridge_p38", SRC)
    module = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p38"] = module
    spec.loader.exec_module(module)
    return module


bridge = _load_bridge()


def _extract_block(src: str, start_marker: str, end_marker: str) -> str:
    """قصّ كتلة نصية من المصدر بين علامتين (لعزل فحوصات كل بطاقة)."""
    start = src.index(start_marker)
    end = src.index(end_marker, start)
    return src[start:end]


# ══════════════════════════════════════════════════════════════
# 1) الدالة المركزية — العقد السلوكي الكامل
# ══════════════════════════════════════════════════════════════
class TestP38FormatterBehaviour(unittest.TestCase):
    def test_01_function_exists_top_level(self):
        self.assertTrue(callable(getattr(bridge, "format_active_account_line", None)))
        self.assertIn("\ndef format_active_account_line(raw_email) -> str:", BRIDGE_SRC)

    def test_02_unified_line_format(self):
        line = bridge.format_active_account_line("owner@genspark.ai")
        self.assertEqual(line, "📧 <b>الحساب:</b> <code>owner@genspark.ai</code>\n")

    def test_03_trailing_newline_always(self):
        self.assertTrue(bridge.format_active_account_line("a@b.c").endswith("\n"))
        self.assertTrue(bridge.format_active_account_line("").endswith("\n"))

    def test_04_html_escaped_email(self):
        line = bridge.format_active_account_line('x<script>&"@evil.com')
        self.assertNotIn("<script>", line)
        self.assertIn("&lt;script&gt;", line)
        self.assertIn("&amp;", line)

    def test_05_fallback_on_empty(self):
        for raw in ("", None, "   "):
            with self.subTest(raw=raw):
                self.assertIn("غير محدد", bridge.format_active_account_line(raw))

    def test_06_whitespace_trimmed(self):
        line = bridge.format_active_account_line("  a@b.c  ")
        self.assertIn("<code>a@b.c</code>", line)

    def test_07_non_string_input_safe(self):
        # getattr قد يعيد أي نوع — الدالة لا ترمي أبداً
        line = bridge.format_active_account_line(12345)
        self.assertIn("<code>12345</code>", line)


# ══════════════════════════════════════════════════════════════
# 2) بطاقة البدء الفوري لايف — handle_live_project_start
# ══════════════════════════════════════════════════════════════
class TestP38LiveStartCard(unittest.TestCase):
    BLOCK = _extract_block(
        BRIDGE_SRC,
        "def handle_live_project_start(live_pid: str):",
        "pub_url, status, used_acc, ext_dir, last_resp_text = send_message_with_auto_account_failover(",
    )

    def test_01_unified_line_injected(self):
        self.assertIn("format_active_account_line(getattr(cfg, 'selected_account_email', ''))", self.BLOCK)

    def test_02_safe_getattr_no_direct_attr(self):
        # ممنوع الوصول المباشر cfg.selected_account_email داخل البطاقة (كسر محتمل)
        self.assertNotIn("cfg.selected_account_email", self.BLOCK)

    def test_03_line_between_pid_and_model(self):
        pid_pos = self.BLOCK.index("Project ID:</b> <code>{html_escape(live_pid)}")
        acc_pos = self.BLOCK.index("format_active_account_line(getattr")
        model_pos = self.BLOCK.index("الموديل:</b> <code>{html_escape(cfg.model)}")
        self.assertTrue(pid_pos < acc_pos < model_pos)


# ══════════════════════════════════════════════════════════════
# 3) بطاقة نفاد الرصيد والتحويل التلقائي — on_credit_handoff
# ══════════════════════════════════════════════════════════════
class TestP38CreditHandoffCard(unittest.TestCase):
    BLOCK = _extract_block(
        BRIDGE_SRC,
        "def on_credit_handoff(handoff_meta: dict):",
        "cfg.credit_handoff_callback = on_credit_handoff",
    )

    def test_01_unified_line_injected(self):
        self.assertIn("format_active_account_line(getattr(cfg, 'selected_account_email', ''))", self.BLOCK)

    def test_02_after_project_key_line(self):
        key_pos = self.BLOCK.index("مفتاح المشروع:</b> <code>{project_key}</code>")
        acc_pos = self.BLOCK.index("format_active_account_line(getattr")
        self.assertLess(key_pos, acc_pos)


# ══════════════════════════════════════════════════════════════
# 4) بطاقة المزامنة واللقطة — on_project_update
# ══════════════════════════════════════════════════════════════
class TestP38ProjectUpdateCard(unittest.TestCase):
    BLOCK = _extract_block(
        BRIDGE_SRC,
        "def on_project_update(stage_url, stage_status, stage_dir, stage_text, stage_email, stage_query):",
        "def handle_live_project_start(live_pid: str):",
    )

    def test_01_stage_email_finally_used(self):
        # البارامتر المهمل تاريخياً صار مصدر الحقيقة الأول للبطاقة
        self.assertIn(
            "format_active_account_line(stage_email or getattr(cfg, 'selected_account_email', ''))",
            self.BLOCK,
        )

    def test_02_line_inside_msg_between_key_and_status(self):
        key_pos = self.BLOCK.index("مفتاح المشروع:</b> <code>{project_key}</code>")
        acc_pos = self.BLOCK.index("format_active_account_line(stage_email")
        status_pos = self.BLOCK.index("الحالة:</b> <code>{html_escape(stage_status)}")
        self.assertTrue(key_pos < acc_pos < status_pos)


# ══════════════════════════════════════════════════════════════
# 5) بطاقة الاكتمال/الرفض المشتركة + بطاقة اللايف المكتملة (P7-A)
# ══════════════════════════════════════════════════════════════
class TestP38CompletionAndDeclineCard(unittest.TestCase):
    def test_01_unified_label_in_res_msg(self):
        # 🧹 [P39] العقد الجديد: سطر الحساب الموحد بلا journey_block (القائمة المفلترة تغني عنه)
        self.assertIn('f"📧 <b>الحساب:</b> <code>{acc_email}</code>\\n"', BRIDGE_SRC)

    def test_02_old_label_gone(self):
        self.assertNotIn("الحساب المستعمل", BRIDGE_SRC)

    def test_03_journey_block_contract_preserved(self):
        # 🧹 [P39] عقد P29 القديم أُلغي بوعي: journey_block لم يعد يُحقن في البطاقة
        # (القائمة الرأسية المفلترة في timing_block تغني عنه) — والدالة نفسها باقية.
        self.assertNotIn("</code>{journey_block}", BRIDGE_SRC)
        self.assertIn("def format_account_journey_line(journey)", BRIDGE_SRC)

    def test_04_no_double_escaping_acc_email(self):
        # acc_email مُهرَّب مسبقاً لحظة بنائه — ممنوع html_escape ثانٍ أو تمريره للدالة الموحدة
        self.assertNotIn("html_escape(acc_email)", BRIDGE_SRC)
        self.assertNotIn("format_active_account_line(acc_email)", BRIDGE_SRC)

    def test_05_decline_card_shares_res_msg(self):
        # رسالة الرفض MODEL_DECLINED تستعمل نفس res_msg (كيبورد مختلف فقط) —
        # سطر الحساب الموحد يغطيها تلقائياً
        self.assertIn("if status == MODEL_DECLINED_STATUS:", BRIDGE_SRC)
        self.assertIn("build_model_decline_keyboard(pub_url, resume_pid, project_key)", BRIDGE_SRC)

    def test_06_completed_live_card_has_account(self):
        self.assertIn(
            "format_active_account_line(used_acc.get('email') if used_acc else '')",
            BRIDGE_SRC,
        )


# ══════════════════════════════════════════════════════════════
# 6) التوحيد الشامل + Zero Breaking
# ══════════════════════════════════════════════════════════════
class TestP38GlobalConsistency(unittest.TestCase):
    def test_01_five_lifecycle_injections(self):
        # 4 استدعاءات للدالة الموحدة (لايف/handoff/لقطة/لايف مكتملة) + سطر الاكتمال الموروث
        calls = re.findall(r"format_active_account_line\(", BRIDGE_SRC)
        # def واحدة + docstring لا تحتسب + 4 استدعاءات فعلية
        self.assertGreaterEqual(len(calls) - 1, 4)

    def test_02_unified_label_everywhere(self):
        # التسمية الموحدة «📧 الحساب:» هي الوحيدة في بطاقات دورة الحياة
        self.assertIn("📧 <b>الحساب:</b>", bridge.format_active_account_line("x@y.z"))
        self.assertIn("📧 <b>الحساب:</b> <code>{acc_email}</code>", BRIDGE_SRC)

    def test_03_p29_active_account_line_untouched(self):
        # سطر «الحساب النشط» في Live Renderer (عقد P29 مختلف الوظيفة) بلا مساس
        self.assertIn("📧 <b>الحساب النشط:</b>", BRIDGE_SRC)

    def test_04_mirror_runtime_exports_formatter(self):
        # المرايا أعيد بناؤها وتصدّر الدالة الجديدة بنفس الهوية
        runtime_path = webapp_dir / "bridge_refactor" / "runtime.py"
        self.assertTrue(runtime_path.exists())
        parts_dir = webapp_dir / "bridge_refactor" / "parts"
        p11 = (parts_dir / "p11_worker.py").read_text(encoding="utf-8")
        self.assertIn("def format_active_account_line(raw_email) -> str:", p11)

    def test_05_formatter_never_raises(self):
        for weird in (None, "", 0, [], {}, object()):
            with self.subTest(weird=weird):
                out = bridge.format_active_account_line(weird)
                self.assertIsInstance(out, str)
                self.assertIn("📧", out)


if __name__ == "__main__":
    unittest.main()
