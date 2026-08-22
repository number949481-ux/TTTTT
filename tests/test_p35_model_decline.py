"""
test_p35_model_decline.py
=========================
حزمة حراسة [P35] — كشف رفض الموديل والتعافي منه (Model Decline Recovery):
الرد القصير "The model declined to answer this request..." كان يُحتسب COMPLETED
(طوله > 25 حرفاً) فيتقدم مؤشر الاستئناف لنقطة "الرفض" رغم غياب أي ناتج.

فلسفة P35 المحروسة: **الرفض يُعامل كأن الطلب لم يُرسل.**

العقود المحروسة (مستخلصة من الفحص الميداني على السورس الفعلي):
  1. ثوابت مركزية بتعريف وحيد: MODEL_DECLINE_MARKERS +
     MODEL_DECLINE_MAX_RESPONSE_CHARS=300 + MODEL_DECLINED_STATUS="MODEL_DECLINED".
  2. is_model_decline_response: True فقط لردود قصيرة (≤300 بعد strip) جوهرها
     عبارة رفض معتمدة — حارس False Positive: الرد الطويل الذي *يقتبس* الجملة
     لا يُحتسب رفضاً أبداً (نفس فلسفة إصلاح RUNNING الكاذب).
  3. إعادة التصنيف في الـ worker تحدث **فقط** فوق COMPLETED — أي فشل آخر
     (CREDIT_EXHAUSTED/TIMEOUT/...) يمر بمساره القديم حرفياً (Zero Breaking).
  4. الرفض لا يقدّم مؤشر الاستئناف: `final_pid = ""` عند model_declined —
     latest_genspark_pid يبقى على آخر نقطة صالحة قبل الطلب المرفوض.
  5. describe_terminal_outcome(MODEL_DECLINED): kind=failure + allow_preview=True
     (نص الرفض قصير وعرضه يفيد المستخدم) + عنوان 🚫 مميز.
  6. build_model_decline_keyboard: زران ملونان أعلى الكيبورد
     (✍️ أعد صياغة البرومبت cmd:decline_retry style=primary +
      ⬅️ رجوع للوحة التحكم cmd:decline_dashboard style=danger)
     ثم أزرار الاكتمال المعتادة تحتهما حرفياً عبر build_completed_message_keyboard
     (بلا نسخ يدوي) — والنمطان ضمن ALLOWED_BUTTON_STYLES.
  7. معالجا الموزّع: cmd:decline_retry (إرشاد إعادة الصياغة — بلا إطلاق مهمة) +
     cmd:decline_dashboard (مكافئ حرفياً لـ cmd:dashboard بفرع منفصل).
  8. Zero Breaking: كيبورد الاكتمال العادي لا يحمل أزرار الرفض، وفرع COMPLETED
     في describe_terminal_outcome بلا مساس، وdetect_response_status لا يُلمس.
"""
import importlib.util
import pathlib
import sys
import unittest

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

SRC = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = SRC.read_text(encoding="utf-8")


def _load_bridge():
    spec = importlib.util.spec_from_file_location("bridge_p35", SRC)
    module = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p35"] = module
    spec.loader.exec_module(module)
    return module


bridge = _load_bridge()

DECLINE_TEXT = "The model declined to answer this request. Please try rephrasing your prompt."
PID = "prj_p35_abcdef123456"
KEY = "proj_key_p35"
URL = "https://example.com/preview/p35"


def _rows(kb: dict) -> list:
    return kb["inline_keyboard"]


def _flat(kb: dict) -> list:
    return [btn for row in _rows(kb) for btn in row]


def _callbacks(kb: dict) -> list:
    return [b.get("callback_data") for b in _flat(kb) if "callback_data" in b]


# ══════════════════════════════════════════════════════════════
# 1) الثوابت المركزية
# ══════════════════════════════════════════════════════════════
class TestP35Constants(unittest.TestCase):
    def test_01_markers_list_exists_and_lowercase(self):
        self.assertIsInstance(bridge.MODEL_DECLINE_MARKERS, list)
        self.assertGreaterEqual(len(bridge.MODEL_DECLINE_MARKERS), 3)
        for marker in bridge.MODEL_DECLINE_MARKERS:
            self.assertEqual(marker, marker.lower(), "العبارات يجب أن تكون lowercase — المقارنة تتم على low")

    def test_02_canonical_marker_present(self):
        self.assertIn("the model declined to answer this request", bridge.MODEL_DECLINE_MARKERS)

    def test_03_max_chars_is_300(self):
        self.assertEqual(bridge.MODEL_DECLINE_MAX_RESPONSE_CHARS, 300)

    def test_04_status_constant_value(self):
        self.assertEqual(bridge.MODEL_DECLINED_STATUS, "MODEL_DECLINED")

    def test_05_single_definition_of_each_constant(self):
        for token in ("MODEL_DECLINE_MARKERS = ", "MODEL_DECLINE_MAX_RESPONSE_CHARS = ", "MODEL_DECLINED_STATUS = "):
            self.assertEqual(BRIDGE_SRC.count(token), 1, f"تعريف وحيد إلزامي لـ {token.strip()}")


# ══════════════════════════════════════════════════════════════
# 2) is_model_decline_response — الكشف وحارس False Positive
# ══════════════════════════════════════════════════════════════
class TestP35Detection(unittest.TestCase):
    def test_01_canonical_decline_detected(self):
        self.assertTrue(bridge.is_model_decline_response(DECLINE_TEXT))

    def test_02_all_markers_detected(self):
        for marker in bridge.MODEL_DECLINE_MARKERS:
            self.assertTrue(bridge.is_model_decline_response(marker), f"العبارة {marker!r} يجب أن تُكشف")

    def test_03_case_insensitive(self):
        self.assertTrue(bridge.is_model_decline_response(DECLINE_TEXT.upper()))

    def test_04_whitespace_stripped(self):
        self.assertTrue(bridge.is_model_decline_response(f"\n\n   {DECLINE_TEXT}   \n"))

    def test_05_none_and_empty_are_not_decline(self):
        self.assertFalse(bridge.is_model_decline_response(None))
        self.assertFalse(bridge.is_model_decline_response(""))
        self.assertFalse(bridge.is_model_decline_response("   \n  "))

    def test_06_long_legit_response_quoting_marker_is_not_decline(self):
        # 🛡️ حارس False Positive الجوهري: رد شرعي طويل يقتبس جملة الرفض
        long_text = ("إليك شرحاً كاملاً للمشروع. " * 30) + DECLINE_TEXT
        self.assertGreater(len(long_text), bridge.MODEL_DECLINE_MAX_RESPONSE_CHARS)
        self.assertFalse(bridge.is_model_decline_response(long_text))

    def test_07_boundary_at_exactly_300_chars(self):
        padded = DECLINE_TEXT + " " + ("x" * (300 - len(DECLINE_TEXT) - 1))
        self.assertEqual(len(padded), 300)
        self.assertTrue(bridge.is_model_decline_response(padded))
        self.assertFalse(bridge.is_model_decline_response(padded + "y"), "301 حرفاً = رد طويل = ليس رفضاً")

    def test_08_normal_short_answer_is_not_decline(self):
        self.assertFalse(bridge.is_model_decline_response("تم إنشاء المشروع بنجاح ✅"))

    def test_09_detect_response_status_still_completed_for_decline_text(self):
        # العقد المعماري: detect_response_status لا يُلمس (الرفض COMPLETED تقنياً)
        # وإعادة التصنيف تحدث في الـ worker حصرياً.
        self.assertEqual(bridge.detect_response_status(DECLINE_TEXT), "COMPLETED")


# ══════════════════════════════════════════════════════════════
# 3) describe_terminal_outcome — فرع MODEL_DECLINED
# ══════════════════════════════════════════════════════════════
class TestP35TerminalOutcome(unittest.TestCase):
    def setUp(self):
        self.outcome = bridge.describe_terminal_outcome(bridge.MODEL_DECLINED_STATUS, None)

    def test_01_kind_is_failure(self):
        self.assertEqual(self.outcome["kind"], "failure")

    def test_02_allow_preview_true(self):
        # نص الرفض قصير (≤300) وعرضه يزيد ثقة المستخدم — عكس بقية حالات الفشل
        self.assertTrue(self.outcome["allow_preview"])

    def test_03_title_is_distinct_decline_banner(self):
        self.assertIn("🚫", self.outcome["title"])
        self.assertIn("رفض الموديل", self.outcome["title"])

    def test_04_note_explains_not_sent_semantics(self):
        self.assertIn("لم يُرسل", self.outcome["note"])
        self.assertIn("مؤشر الاستئناف", self.outcome["note"])

    def test_05_completed_outcome_untouched(self):
        ok = bridge.describe_terminal_outcome("COMPLETED", URL)
        self.assertEqual(ok["kind"], "success")
        self.assertTrue(ok["allow_preview"])
        self.assertIn("🎉", ok["title"])

    def test_06_other_failures_keep_allow_preview_false(self):
        for status in ("CREDIT_EXHAUSTED", "TIMEOUT", "FAILED", "LOGIN_FAILED"):
            self.assertFalse(bridge.describe_terminal_outcome(status, None)["allow_preview"], status)


# ══════════════════════════════════════════════════════════════
# 4) build_model_decline_keyboard — الكيبورد المميز
# ══════════════════════════════════════════════════════════════
class TestP35DeclineKeyboard(unittest.TestCase):
    def setUp(self):
        self.kb = bridge.build_model_decline_keyboard(URL, PID, KEY)
        self.rows = _rows(self.kb)

    def test_01_first_row_is_retry_prompt_primary(self):
        btn = self.rows[0][0]
        self.assertEqual(btn["text"], "✍️ أعد صياغة البرومبت")
        self.assertEqual(btn["callback_data"], "cmd:decline_retry")
        self.assertEqual(btn["style"], "primary")

    def test_02_second_row_is_dashboard_danger(self):
        btn = self.rows[1][0]
        self.assertEqual(btn["text"], "⬅️ رجوع للوحة التحكم")
        self.assertEqual(btn["callback_data"], "cmd:decline_dashboard")
        self.assertEqual(btn["style"], "danger")

    def test_03_styles_within_allowed_whitelist(self):
        for btn in _flat(self.kb):
            style = btn.get("style")
            if style is not None:
                self.assertIn(style, bridge.ALLOWED_BUTTON_STYLES)

    def test_04_completed_keyboard_rows_appended_verbatim(self):
        base_rows = _rows(bridge.build_completed_message_keyboard(URL, PID, KEY))
        self.assertEqual(self.rows[2:], base_rows,
                         "أزرار الاكتمال المعتادة يجب أن تأتي تحت زرَي الرفض حرفياً — بلا نسخ يدوي")

    def test_05_no_dead_url_button_without_pub_url(self):
        kb = bridge.build_model_decline_keyboard(None, PID, KEY)
        for btn in _flat(kb):
            self.assertNotIn("url", btn, "pub_url=None ⟹ ممنوع زر url ميت")

    def test_06_decline_rows_survive_all_input_combinations(self):
        for pub in (URL, None):
            for pid in (PID, None):
                for key in (KEY, None):
                    kb = bridge.build_model_decline_keyboard(pub, pid, key)
                    cbs = _callbacks(kb)
                    self.assertEqual(cbs[0], "cmd:decline_retry", (pub, pid, key))
                    self.assertEqual(cbs[1], "cmd:decline_dashboard", (pub, pid, key))

    def test_07_resume_button_present_with_pid(self):
        # زر ▶️ كمل الآن (cont:{pid}) يبقى متاحاً تحت زرَي الرفض —
        # طريق «كمل من آخر نقطة صالحة» لأن المؤشر لم يتقدم لنقطة الرفض
        self.assertIn(f"cont:{PID}", _callbacks(self.kb))

    def test_08_callback_data_within_telegram_64_bytes(self):
        for btn in _flat(self.kb):
            cb = btn.get("callback_data")
            if cb is not None:
                self.assertLessEqual(len(cb.encode("utf-8")), 64)


# ══════════════════════════════════════════════════════════════
# 5) عقود مصدرية: إعادة التصنيف في الـ worker + عدم تقدم المؤشر
# ══════════════════════════════════════════════════════════════
class TestP35WorkerSourceContracts(unittest.TestCase):
    def _worker_src(self) -> str:
        start = BRIDGE_SRC.index("def process_user_task_async(")
        end = BRIDGE_SRC.index("def get_main_keyboard(")
        return BRIDGE_SRC[start:end]

    def test_01_reclassification_only_over_completed(self):
        worker = self._worker_src()
        self.assertIn('model_declined = status == "COMPLETED" and is_model_decline_response(last_resp_text)', worker,
                      "إعادة التصنيف يجب أن تكون فوق COMPLETED حصرياً — Zero Breaking لبقية الحالات")

    def test_02_status_becomes_model_declined(self):
        self.assertIn("status = MODEL_DECLINED_STATUS", self._worker_src())

    def test_03_final_pid_reset_blocks_resume_pointer_advance(self):
        worker = self._worker_src()
        idx_decline = worker.index("if model_declined:", worker.index("final_pid = extract_stage_project_id"))
        snippet = worker[idx_decline:idx_decline + 400]
        self.assertIn('final_pid = ""', snippet,
                      "الرفض كأن الطلب لم يُرسل: تصفير final_pid إلزامي لمنع تقدم مؤشر الاستئناف")

    def test_04_decline_keyboard_used_for_declined_status(self):
        worker = self._worker_src()
        self.assertIn("if status == MODEL_DECLINED_STATUS:", worker)
        self.assertIn("reply_markup = build_model_decline_keyboard(pub_url, resume_pid, project_key)", worker)

    def test_05_completed_keyboard_still_default(self):
        self.assertIn("reply_markup = build_completed_message_keyboard(pub_url, resume_pid, project_key)",
                      self._worker_src())

    def test_06_reclassification_after_failover_before_identity_write(self):
        worker = self._worker_src()
        i_failover = worker.index("send_message_with_auto_account_failover(")
        i_reclass = worker.index("model_declined = status ==")
        i_identity = worker.index("final_pid = extract_stage_project_id")
        self.assertLess(i_failover, i_reclass)
        self.assertLess(i_reclass, i_identity,
                        "إعادة التصنيف يجب أن تسبق كتابة الهوية حتى يُسجل status=MODEL_DECLINED لا COMPLETED")


# ══════════════════════════════════════════════════════════════
# 6) معالجا الموزّع: cmd:decline_retry + cmd:decline_dashboard
# ══════════════════════════════════════════════════════════════
class TestP35DispatcherHandlers(unittest.TestCase):
    def test_01_decline_retry_handler_exists(self):
        self.assertIn('elif data == "cmd:decline_retry":', BRIDGE_SRC)

    def test_02_decline_dashboard_handler_exists(self):
        self.assertIn('elif data == "cmd:decline_dashboard":', BRIDGE_SRC)

    def test_03_decline_dashboard_matches_dashboard_behavior(self):
        # المكافئ الحرفي: نفس سطر الإرسال المستخدم في cmd:dashboard (مرساة P33)
        dash_line = "send_telegram_message(chat_id, render_dashboard_text(chat_id), reply_markup=get_main_keyboard(chat_id))"
        idx = BRIDGE_SRC.index('elif data == "cmd:decline_dashboard":')
        snippet = BRIDGE_SRC[idx:idx + 600]
        self.assertIn(dash_line, snippet)

    def test_04_retry_handler_sends_guidance_not_task(self):
        idx = BRIDGE_SRC.index('elif data == "cmd:decline_retry":')
        next_branch = BRIDGE_SRC.index("elif data ==", idx + 10)
        snippet = BRIDGE_SRC[idx:next_branch]
        self.assertIn("أعد صياغة البرومبت", snippet)
        self.assertNotIn("EXECUTOR.submit", snippet,
                         "زر إعادة الصياغة إرشاد فقط — ممنوع إطلاق مهمة تلقائية ببرومبت مرفوض")

    def test_05_legacy_dashboard_branch_untouched(self):
        # مرساة P33/P26: الفرعان القديمان بحرفيتهما
        self.assertIn('if data == "cmd:show_dashboard":', BRIDGE_SRC)
        self.assertIn('elif data == "cmd:dashboard":', BRIDGE_SRC)


# ══════════════════════════════════════════════════════════════
# 7) Zero Breaking — كيبورد الاكتمال العادي بلا أزرار رفض
# ══════════════════════════════════════════════════════════════
class TestP35ZeroBreaking(unittest.TestCase):
    def test_01_completed_keyboard_has_no_decline_buttons(self):
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        cbs = _callbacks(kb)
        self.assertNotIn("cmd:decline_retry", cbs)
        self.assertNotIn("cmd:decline_dashboard", cbs)

    def test_02_completed_keyboard_contracts_intact(self):
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        cbs = _callbacks(kb)
        self.assertIn(f"cont:{PID}", cbs)
        self.assertEqual(cbs[-1], "cmd:dashboard")

    def test_03_credit_exhausted_flow_not_reclassified(self):
        # الرفض يُكشف فقط فوق COMPLETED — نص CREDIT_EXHAUSTED لا يمر على الكشف أصلاً
        outcome = bridge.describe_terminal_outcome("CREDIT_EXHAUSTED", None)
        self.assertEqual(outcome["kind"], "failure")
        self.assertNotIn("رفض الموديل", outcome["title"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
