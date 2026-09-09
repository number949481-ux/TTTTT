"""
test_p36_engine_fast_decline.py
================================
حزمة حراسة [P36] — مسار الرفض السريع في المحرك (Engine Fast Decline Path):
رد الرفض القصير "The model declined to answer this request..." لا يحمل أي ناتج،
ومع ذلك كان المحرك `01.03Genspark_claude-opus-5-code.py` يشغّل عليه المسارات
الثلاثة المكلفة: الشير العام (_do_auto_share) + التنزيل التلقائي
(auto_download_project) + التحقق العام (ensure_public — كان يهدر حتى ~60s
timeout قبل وصول رسالة الرفض للمستخدم).

فلسفة P36 المحروسة: **استجابة الرفض لحظية** — تخطّي المسارات الثلاثة فوراً.

العقود المحروسة (مستخلصة من الفحص الميداني على السورس الفعلي):
  1. كاشف مطابق دلالياً لكاشف P35 في الجسر 01.33: نفس العبارات + نفس عتبة
     الـ 300 حرف + نفس حارس False Positive (الرد الطويل الذي يقتبس الجملة
     ليس رفضاً أبداً).
  2. المواقع الثلاثة في المحرك (CLI chat + المسار الرئيسي URL-mode +
     المسار المتوازي) كلها تحسب `_declined` قبل أي مسار مكلف.
  3. `_do_auto_share` محروسة بـ `not _declined` في المواقع الثلاثة.
  4. `ensure_public` محروسة بـ `not _declined` (الرئيسي + المتوازي) —
     الرابط المباشر يُبنى بلا شبكة عند الرفض.
  5. `auto_download_project` (المسار المتوازي) محروسة بـ `not _declined`.
  6. `args.share` اليدوي محروس أيضاً — لا مشاركة لرفض.
  7. Zero Breaking: حفظ المحادثة (update_conversation) وتحديث الرصيد
     (_update_balance) والتذاكر تعمل كالمعتاد حتى مع الرفض — الرفض يُسجَّل،
     فقط المسارات العامة المكلفة تُتخطى.
"""
import importlib.util
import pathlib
import re
import sys
import unittest

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

ENGINE_PATH = webapp_dir / "01.03Genspark_claude-opus-5-code.py"
ENGINE_SRC = ENGINE_PATH.read_text(encoding="utf-8")

# ── عزل كاشف الرفض من سورس المحرك وتشغيله معزولاً (بلا استيراد المحرك كاملاً) ──
_det_start = ENGINE_SRC.index("MODEL_DECLINE_MARKERS = [")
_det_end = ENGINE_SRC.index("\ndef create_downloader_session(")
_DETECTOR_SNIPPET = ENGINE_SRC[_det_start:_det_end]
_ns: dict = {}
exec(compile(_DETECTOR_SNIPPET, str(ENGINE_PATH), "exec"), _ns)

MODEL_DECLINE_MARKERS = _ns["MODEL_DECLINE_MARKERS"]
MODEL_DECLINE_MAX_RESPONSE_CHARS = _ns["MODEL_DECLINE_MAX_RESPONSE_CHARS"]
is_model_decline_response = _ns["is_model_decline_response"]

DECLINE_TEXT = "The model declined to answer this request. Please try rephrasing your prompt."


def _region(start_marker: str, end_marker: str) -> str:
    """قصّ منطقة من سورس المحرك بين علامتين نصيتين فريدتين."""
    s = ENGINE_SRC.index(start_marker)
    e = ENGINE_SRC.index(end_marker, s)
    return ENGINE_SRC[s:e]


# المنطقة 1 — CLI chat (if answer: بعد user_msg_id)
CLI_REGION = _region(
    "user_msg_id = str(uuid.uuid4())\n            project_id = pid or project_id",
    "_update_balance(accounts, acc.get(\"email\", \"\"), cookies, cfg)",
)

# المنطقة 2 — المسار الرئيسي URL-mode (final_pid + ensure_public + args.share)
MAIN_REGION = _region(
    'final_pid = pid or project_id or ""',
    "# ← فشل غير CREDIT_EXHAUSTED (500 أو غيره)",
)

# المنطقة 3 — المسار المتوازي (الشير + التنزيل + URL mode بعد _update_balance)
PARALLEL_REGION = _region(
    "# ── ✅ إصلاح: حدّث الرصيد + وقت الاستخدام بعد كل رد ناجح",
    "# ── 🤖 Auto Classification via ChatGPT Shelby",
)


# ══════════════════════════════════════════════════════════════
# 1) الثوابت المركزية — تطابق دلالي مع كاشف P35 في الجسر
# ══════════════════════════════════════════════════════════════
class TestP36Constants(unittest.TestCase):
    def test_01_markers_list_exists_and_lowercase(self):
        self.assertIsInstance(MODEL_DECLINE_MARKERS, list)
        self.assertGreaterEqual(len(MODEL_DECLINE_MARKERS), 3)
        for marker in MODEL_DECLINE_MARKERS:
            self.assertEqual(marker, marker.lower(), "كل العبارات lowercase إلزامياً")

    def test_02_threshold_is_300(self):
        self.assertEqual(MODEL_DECLINE_MAX_RESPONSE_CHARS, 300)

    def test_03_core_decline_phrase_present(self):
        self.assertIn("the model declined to answer this request", MODEL_DECLINE_MARKERS)

    def test_04_semantic_parity_with_bridge_p35(self):
        """كاشف المحرك مطابق دلالياً لكاشف P35 في الجسر 01.33 (نفس العبارات والعتبة)."""
        bridge_src = (webapp_dir / "01.33_telegram_gen_bridge.py").read_text(encoding="utf-8")
        for marker in MODEL_DECLINE_MARKERS:
            self.assertIn(f'"{marker}"', bridge_src,
                          f"عبارة المحرك «{marker}» يجب أن توجد حرفياً في كاشف الجسر P35")
        self.assertIn("MODEL_DECLINE_MAX_RESPONSE_CHARS = 300", bridge_src)

    def test_05_single_definition_in_engine(self):
        """تعريف وحيد للكاشف داخل المحرك — ممنوع التكرار."""
        self.assertEqual(ENGINE_SRC.count("MODEL_DECLINE_MARKERS = ["), 1)
        self.assertEqual(ENGINE_SRC.count("def is_model_decline_response("), 1)


# ══════════════════════════════════════════════════════════════
# 2) سلوك الكاشف — نفس عقود P35 حرفياً
# ══════════════════════════════════════════════════════════════
class TestDeclineDetector(unittest.TestCase):
    def test_01_detects_canonical_decline(self):
        self.assertTrue(is_model_decline_response(DECLINE_TEXT))

    def test_02_empty_and_none_are_not_decline(self):
        self.assertFalse(is_model_decline_response(""))
        self.assertFalse(is_model_decline_response(None))
        self.assertFalse(is_model_decline_response("   \n  "))

    def test_03_case_insensitive(self):
        self.assertTrue(is_model_decline_response("THE MODEL DECLINED TO ANSWER THIS REQUEST."))

    def test_04_false_positive_guard_long_quote(self):
        """رد طويل شرعي يقتبس جملة الرفض داخله — ليس رفضاً أبداً."""
        long_reply = ("Here is the essay you asked for. " * 20
                      + "Note: earlier the model declined to answer this request, "
                      + "but after rephrasing it succeeded. " + "More content. " * 20)
        self.assertGreater(len(long_reply), MODEL_DECLINE_MAX_RESPONSE_CHARS)
        self.assertFalse(is_model_decline_response(long_reply))

    def test_05_normal_short_answer_not_decline(self):
        self.assertFalse(is_model_decline_response("Done! Your website is ready."))

    def test_06_boundary_at_300_chars(self):
        """رد رفض بطول ≤300 بعد strip يُكشف — وما يتجاوزها لا."""
        padded = DECLINE_TEXT + " " * 500  # strip يعيده قصيراً
        self.assertTrue(is_model_decline_response(padded))
        over = DECLINE_TEXT + " x" * 200   # جوهر > 300 حرف
        self.assertGreater(len(over.strip()), 300)
        self.assertFalse(is_model_decline_response(over))


# ══════════════════════════════════════════════════════════════
# 3) المنطقة 1 — CLI chat: الشير العام محروس
# ══════════════════════════════════════════════════════════════
class TestCliChatRegion(unittest.TestCase):
    def test_01_declined_computed_before_share(self):
        pos_decl = CLI_REGION.index("_declined = is_model_decline_response(answer)")
        pos_share = CLI_REGION.index("_do_auto_share(")
        self.assertLess(pos_decl, pos_share, "_declined يجب أن يُحسب قبل الشير")

    def test_02_auto_share_guarded(self):
        m = re.search(r"if not _declined:\s*\n\s*_do_auto_share\(cfg, conv_name, project_id or \"\", cookies\)", CLI_REGION)
        self.assertIsNotNone(m, "الشير في CLI يجب أن يكون محروساً بـ not _declined")

    def test_03_conversation_still_saved_on_decline(self):
        """Zero Breaking: حفظ المحادثة غير محروس — الرفض يُسجَّل في السجل."""
        pos_decl = CLI_REGION.index("_declined =")
        pos_save = CLI_REGION.index("update_conversation(")
        self.assertGreater(pos_save, pos_decl)
        guard_window = CLI_REGION[CLI_REGION.rindex("\n", 0, pos_save - 60):pos_save]
        self.assertNotIn("if not _declined", guard_window,
                         "update_conversation ممنوع حراستها — الرفض يُحفظ")


# ══════════════════════════════════════════════════════════════
# 4) المنطقة 2 — المسار الرئيسي: ensure_public + الشير + args.share
# ══════════════════════════════════════════════════════════════
class TestMainRegion(unittest.TestCase):
    def test_01_declined_computed_first(self):
        pos_decl = MAIN_REGION.index("_declined = is_model_decline_response(answer)")
        pos_pub = MAIN_REGION.index("ensure_public(")
        pos_share = MAIN_REGION.index("_do_auto_share(")
        self.assertLess(pos_decl, pos_pub)
        self.assertLess(pos_decl, pos_share)

    def test_02_ensure_public_guarded(self):
        self.assertIn("if VERIFY_PUBLIC_AFTER and not _declined:", MAIN_REGION)

    def test_03_direct_url_fallback_still_built(self):
        """عند الرفض يُبنى الرابط المباشر بلا شبكة — لا يضيع الرابط."""
        m = re.search(
            r"if VERIFY_PUBLIC_AFTER and not _declined:\s*\n\s*_public_url = ensure_public\(.*?\)\s*\n\s*else:\s*\n\s*_public_url = f\"\{GENSPARK\}/autopilotagent_viewer\?id=\{final_pid\}\"",
            MAIN_REGION)
        self.assertIsNotNone(m)

    def test_04_auto_share_guarded(self):
        m = re.search(r"if not _declined:\s*\n\s*_do_auto_share\(cfg, conv_name, final_pid, cookies\)", MAIN_REGION)
        self.assertIsNotNone(m)

    def test_05_manual_share_flag_guarded(self):
        self.assertIn("if args.share and final_pid and not _declined:", MAIN_REGION)

    def test_06_balance_and_tickets_untouched(self):
        """Zero Breaking: الرصيد والتذاكر تُحدَّث كالمعتاد حتى مع الرفض."""
        self.assertIn('_update_balance(accounts, acc.get("email", ""), cookies, cfg)', MAIN_REGION)
        self.assertIn("_save_ticket_question(cfg, question, ticket_num)", MAIN_REGION)


# ══════════════════════════════════════════════════════════════
# 5) المنطقة 3 — المسار المتوازي: الشير + التنزيل + ensure_public
# ══════════════════════════════════════════════════════════════
class TestParallelRegion(unittest.TestCase):
    def test_01_declined_computed_after_balance_before_paths(self):
        pos_bal = PARALLEL_REGION.index("_update_balance(accounts, email, cookies, cfg)")
        pos_decl = PARALLEL_REGION.index("_declined = is_model_decline_response(answer)")
        pos_share = PARALLEL_REGION.index("_do_auto_share(")
        self.assertLess(pos_bal, pos_decl, "الرصيد يُحدَّث قبل فحص الرفض (Zero Breaking)")
        self.assertLess(pos_decl, pos_share)

    def test_02_auto_share_guarded(self):
        m = re.search(r"if pid and not _declined:\s*\n\s*_do_auto_share\(cfg, \"default\", pid, cookies\)", PARALLEL_REGION)
        self.assertIsNotNone(m)

    def test_03_auto_download_guarded(self):
        self.assertIn("if cfg.auto_download_sandbox and pid and not _declined:", PARALLEL_REGION)

    def test_04_ensure_public_guarded_with_direct_fallback(self):
        self.assertIn('(VERIFY_PUBLIC_AFTER and not _declined) else f"{GENSPARK}/autopilotagent_viewer?id={pid}"', PARALLEL_REGION)

    def test_05_url_entry_still_saved(self):
        """Zero Breaking: save_url_entry يعمل كالمعتاد (بالرابط المباشر عند الرفض)."""
        self.assertIn("save_url_entry(project_id=pid", PARALLEL_REGION)


# ══════════════════════════════════════════════════════════════
# 6) التغطية الشاملة — المواقع الثلاثة كاملة وصفر NameError
# ══════════════════════════════════════════════════════════════
class TestFullCoverage(unittest.TestCase):
    def test_01_exactly_three_decline_computations(self):
        """كل موقع من المواقع الثلاثة يحسب _declined بنفسه — لا أكثر ولا أقل."""
        self.assertEqual(ENGINE_SRC.count("_declined = is_model_decline_response(answer)"), 3)

    def test_02_every_usage_region_has_own_assignment(self):
        """كل منطقة تستخدم _declined تعرّفه محلياً أولاً — صفر NameError."""
        for region, name in ((CLI_REGION, "CLI"), (MAIN_REGION, "MAIN"), (PARALLEL_REGION, "PARALLEL")):
            self.assertIn("_declined = is_model_decline_response(answer)", region,
                          f"منطقة {name} تستخدم _declined بلا تعريف محلي")
            first_use = region.index("_declined")
            self.assertTrue(region[first_use:].startswith("_declined = "),
                            f"أول ظهور لـ _declined في {name} يجب أن يكون التعريف نفسه")

    def test_03_engine_compiles(self):
        import py_compile
        py_compile.compile(str(ENGINE_PATH), doraise=True)

    def test_04_p36_comment_marker_present(self):
        """توثيق P36 داخل السورس نفسه — يافطة الفلسفة فوق الكاشف."""
        self.assertIn("[P36]", ENGINE_SRC)
        self.assertIn("Fast Decline Path", ENGINE_SRC)


if __name__ == "__main__":
    unittest.main()
