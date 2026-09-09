"""
test_p37_decline_resume_summary.py
==================================
حزمة حراسة [P37] — فتح بطاقة ملخص الاستئناف من زر إعادة الصياغة
(Decline ➔ Resume Summary Card):

في P35 كان زر «✍️ أعد صياغة البرومبت» (الأزرق) يرسل إرشاداً نصياً فقط،
فيضطر المستخدم للبحث عن زر 🔄 استئناف المشروع يدوياً. منذ P37 الزر يحمل
مفتاح المشروع (cmd:decline_retry:{project_key}) وضغطه يفتح فوراً بطاقة
«🔄 ملخص الاستئناف» الكاملة بكيبوردها التفاعلي ويضبط الحالة على
AWAITING_PROJECT_RESUME_DECISION بسياق المشروع النظيف — فيقدر المستخدم
يضغط [▶️ كمل الآن] ويبعت البرومبت الجديد فيكمل على نفس المشروع فوراً،
أو [⚙️ عدّل الإعدادات] لتعديل الموديل/الفرع.

العقود المحروسة:
  1. build_model_decline_keyboard: الزر الأزرق يحمل cmd:decline_retry:{key}
     عند توفر مفتاح المشروع — مع تعقيم المفتاح (regex [^A-Za-z0-9_-] ➔ _).
  2. Fallback آمن: بلا مفتاح (None/"") أو لو تجاوز الـcallback حد تليجرام
     64 بايت ➔ الحرفية القديمة cmd:decline_retry (عقد P35 التاريخي).
  3. معالج الموزّع الجديد data.startswith("cmd:decline_retry:") يستدعي
     start_project_resume_from_key (بطاقة الملخص + الحالة + السياق النظيف)
     وله رسالة fallback مهذبة عند فشل الفتح — وبلا EXECUTOR.submit أبداً
     (ممنوع إطلاق مهمة تلقائية ببرومبت مرفوض — عقد P35 رقم 7 محفوظ).
  4. ترتيب الفروع: المطابقة الحرفية == "cmd:decline_retry" تسبق startswith
     — الزر القديم بلا مفتاح يظل يعمل بالإرشاد النصي حرفياً.
  5. سلوكياً: start_project_resume_from_key ➔ present_resume_summary يضبط
     AWAITING_PROJECT_RESUME_DECISION + project_key + pid ويرسل نص
     «🔄 ملخص الاستئناف» مع كيبورد فيه cmd:resume_continue (▶️ كمل الآن)
     و cmd:resume_settings (⚙️ عدّل الإعدادات).
  6. Zero Breaking: كيبورد الاكتمال العادي بلا أزرار رفض، أزرار الاكتمال
     تأتي تحت زرَي الرفض حرفياً، والزر الأحمر cmd:decline_dashboard بلا مساس.
"""
import importlib.util
import pathlib
import sys
import unittest
from unittest import mock

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

SRC = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = SRC.read_text(encoding="utf-8")


def _load_bridge():
    spec = importlib.util.spec_from_file_location("bridge_p37", SRC)
    module = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p37"] = module
    spec.loader.exec_module(module)
    return module


bridge = _load_bridge()

PID = "prj_p37_abcdef123456"
KEY = "proj_key_p37"
URL = "https://example.com/preview/p37"
CHAT = 424242


def _rows(kb: dict) -> list:
    return kb.get("inline_keyboard") or []


def _flat(kb: dict) -> list:
    return [btn for row in _rows(kb) for btn in row]


def _callbacks(kb: dict) -> list:
    return [btn["callback_data"] for btn in _flat(kb) if "callback_data" in btn]


# ══════════════════════════════════════════════════════════════
# 1) الزر الأزرق يحمل مفتاح المشروع — cmd:decline_retry:{key}
# ══════════════════════════════════════════════════════════════
class TestP37KeyedRetryButton(unittest.TestCase):
    def setUp(self):
        self.kb = bridge.build_model_decline_keyboard(URL, PID, KEY)
        self.btn = _rows(self.kb)[0][0]

    def test_01_callback_carries_project_key(self):
        self.assertEqual(self.btn["callback_data"], f"cmd:decline_retry:{KEY}")

    def test_02_text_and_style_unchanged(self):
        self.assertEqual(self.btn["text"], "✍️ أعد صياغة البرومبت")
        self.assertEqual(self.btn["style"], "primary")

    def test_03_style_within_allowed_whitelist(self):
        self.assertIn(self.btn["style"], bridge.ALLOWED_BUTTON_STYLES)

    def test_04_callback_within_telegram_64_bytes(self):
        self.assertLessEqual(len(self.btn["callback_data"].encode("utf-8")), 64)

    def test_05_key_sanitized_like_registry_keys(self):
        kb = bridge.build_model_decline_keyboard(None, None, "weird key!@#")
        cb = _rows(kb)[0][0]["callback_data"]
        self.assertEqual(cb, "cmd:decline_retry:weird_key___",
                         "تعقيم المفتاح يجب أن يطابق regex مفاتيح السجل [^A-Za-z0-9_-] ➔ _")

    def test_06_dashboard_danger_button_untouched(self):
        btn = _rows(self.kb)[1][0]
        self.assertEqual(btn["callback_data"], "cmd:decline_dashboard")
        self.assertEqual(btn["style"], "danger")


# ══════════════════════════════════════════════════════════════
# 2) Fallback آمن — بلا مفتاح أو مفتاح يتجاوز 64 بايت
# ══════════════════════════════════════════════════════════════
class TestP37FallbackSafety(unittest.TestCase):
    def test_01_no_key_falls_back_to_legacy_callback(self):
        for empty in (None, ""):
            kb = bridge.build_model_decline_keyboard(URL, PID, empty)
            self.assertEqual(_rows(kb)[0][0]["callback_data"], "cmd:decline_retry", empty)

    def test_02_oversized_key_falls_back_to_legacy_callback(self):
        # 80 حرفاً (حد التعقيم) + بادئة 18 بايت = 98 بايت > 64 ⟹ fallback إجباري
        kb = bridge.build_model_decline_keyboard(None, None, "k" * 80)
        self.assertEqual(_rows(kb)[0][0]["callback_data"], "cmd:decline_retry")

    def test_03_boundary_key_exactly_64_bytes_kept(self):
        # بادئة "cmd:decline_retry:" = 18 بايت ⟹ مفتاح 46 حرفاً ASCII = 64 بايت بالضبط
        key46 = "a" * 46
        kb = bridge.build_model_decline_keyboard(None, None, key46)
        cb = _rows(kb)[0][0]["callback_data"]
        self.assertEqual(cb, f"cmd:decline_retry:{key46}")
        self.assertEqual(len(cb.encode("utf-8")), 64)

    def test_04_decline_rows_callbacks_valid_in_every_combination(self):
        # نطاق P37: زرا الرفض (الصفان الأولان) — أزرار الاكتمال الموروثة (P33)
        # خارج نطاق هذه الحزمة وتُحرس في حزمها الخاصة
        for pub in (URL, None):
            for pid in (PID, None):
                for key in (KEY, None, "k" * 80):
                    kb = bridge.build_model_decline_keyboard(pub, pid, key)
                    for row in _rows(kb)[:2]:
                        for btn in row:
                            cb = btn.get("callback_data")
                            if cb is not None:
                                self.assertLessEqual(len(cb.encode("utf-8")), 64, (pub, pid, key))

    def test_05_no_dead_url_button_without_pub_url(self):
        kb = bridge.build_model_decline_keyboard(None, PID, KEY)
        for btn in _flat(kb):
            self.assertNotIn("url", btn)


# ══════════════════════════════════════════════════════════════
# 3) معالج الموزّع الجديد — بنية السورس
# ══════════════════════════════════════════════════════════════
class TestP37DispatcherHandler(unittest.TestCase):
    def _keyed_snippet(self) -> str:
        idx = BRIDGE_SRC.index('elif data.startswith("cmd:decline_retry:"):')
        next_branch = BRIDGE_SRC.index("elif data ==", idx + 10)
        return BRIDGE_SRC[idx:next_branch]

    def test_01_keyed_handler_exists(self):
        self.assertIn('elif data.startswith("cmd:decline_retry:"):', BRIDGE_SRC)

    def test_02_keyed_handler_opens_resume_summary(self):
        self.assertIn("start_project_resume_from_key(chat_id, retry_key)", self._keyed_snippet())

    def test_03_keyed_handler_has_polite_fallback_message(self):
        snippet = self._keyed_snippet()
        self.assertIn("تعذر فتح ملخص الاستئناف", snippet)

    def test_04_keyed_handler_never_submits_task(self):
        self.assertNotIn("EXECUTOR.submit", self._keyed_snippet(),
                         "ممنوع إطلاق مهمة تلقائية ببرومبت مرفوض — عقد P35 رقم 7")

    def test_05_exact_match_branch_precedes_startswith(self):
        exact = BRIDGE_SRC.index('elif data == "cmd:decline_retry":')
        keyed = BRIDGE_SRC.index('elif data.startswith("cmd:decline_retry:"):')
        self.assertLess(exact, keyed,
                        "المطابقة الحرفية يجب أن تسبق startswith حتى يظل الزر القديم إرشاداً نصياً")

    def test_06_legacy_guidance_branch_untouched(self):
        idx = BRIDGE_SRC.index('elif data == "cmd:decline_retry":')
        next_branch = BRIDGE_SRC.index("elif data", idx + 10)
        snippet = BRIDGE_SRC[idx:next_branch]
        self.assertIn("أعد صياغة البرومبت وأرسله الآن كرسالة جديدة", snippet)
        self.assertNotIn("EXECUTOR.submit", snippet)

    def test_07_decline_dashboard_branch_untouched(self):
        self.assertIn('elif data == "cmd:decline_dashboard":', BRIDGE_SRC)


# ══════════════════════════════════════════════════════════════
# 4) السلوك الحي — بطاقة الملخص + الحالة + السياق النظيف
# ══════════════════════════════════════════════════════════════
class TestP37ResumeSummaryBehavior(unittest.TestCase):
    def _run(self, identity: dict | None):
        sent, states = [], []
        with mock.patch.object(bridge, "send_telegram_message",
                               side_effect=lambda cid, text, **kw: sent.append((cid, text, kw))), \
             mock.patch.object(bridge, "set_user_state",
                               side_effect=lambda cid, st: states.append((cid, st))), \
             mock.patch.object(bridge, "get_project_identity_record", return_value=identity):
            ok = bridge.start_project_resume_from_key(CHAT, KEY)
        return ok, sent, states

    def _identity(self) -> dict:
        return {"project_key": KEY, "project_name": "مشروع P37",
                "root_genspark_pid": "prj_root_p37_000001",
                "latest_genspark_pid": PID}

    def test_01_returns_true_and_sends_summary_card(self):
        ok, sent, _ = self._run(self._identity())
        self.assertTrue(ok)
        self.assertEqual(len(sent), 1)
        self.assertIn("🔄 <b>ملخص الاستئناف</b>", sent[0][1])

    def test_02_state_set_to_awaiting_resume_decision(self):
        _, _, states = self._run(self._identity())
        self.assertEqual(len(states), 1)
        state = states[0][1]
        self.assertEqual(state["action"], "AWAITING_PROJECT_RESUME_DECISION")
        self.assertEqual(state["project_key"], KEY)

    def test_03_state_carries_clean_pid_from_identity(self):
        _, _, states = self._run(self._identity())
        # المؤشر النظيف: latest_genspark_pid (لم يتقدم لنقطة الرفض — عقد P35)
        self.assertEqual(states[0][1]["pid"], PID)

    def test_04_keyboard_has_continue_and_settings_buttons(self):
        _, sent, _ = self._run(self._identity())
        kb = sent[0][2].get("reply_markup") or {}
        cbs = _callbacks(kb)
        self.assertIn("cmd:resume_continue", cbs)
        self.assertIn("cmd:resume_settings", cbs)

    def test_05_continue_button_text_and_style(self):
        _, sent, _ = self._run(self._identity())
        kb = sent[0][2].get("reply_markup") or {}
        first = _rows(kb)[0]
        self.assertEqual(first[0]["text"], "▶️ كمل الآن")
        self.assertEqual(first[0]["style"], "success")
        self.assertEqual(first[1]["text"], "⚙️ عدّل الإعدادات")

    def test_06_empty_key_returns_false_without_side_effects(self):
        ok, sent, states = self._run(None)
        # مفتاح KEY صالح لكن بلا هوية ⟹ ما زال يعمل (بطاقة بلا pid) — أما المفتاح الفارغ:
        with mock.patch.object(bridge, "send_telegram_message") as tg, \
             mock.patch.object(bridge, "set_user_state") as st:
            self.assertFalse(bridge.start_project_resume_from_key(CHAT, ""))
            tg.assert_not_called()
            st.assert_not_called()

    def test_07_summary_text_mentions_project_key(self):
        _, sent, _ = self._run(self._identity())
        self.assertIn(KEY, sent[0][1])


# ══════════════════════════════════════════════════════════════
# 5) Zero Breaking — عقود P35/P33 محفوظة
# ══════════════════════════════════════════════════════════════
class TestP37ZeroBreaking(unittest.TestCase):
    def test_01_completed_keyboard_has_no_decline_buttons(self):
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        for cb in _callbacks(kb):
            self.assertFalse(cb.startswith("cmd:decline_retry"), cb)
            self.assertNotEqual(cb, "cmd:decline_dashboard")

    def test_02_completed_rows_still_appended_verbatim(self):
        decline = _rows(bridge.build_model_decline_keyboard(URL, PID, KEY))
        base = _rows(bridge.build_completed_message_keyboard(URL, PID, KEY))
        self.assertEqual(decline[2:], base)

    def test_03_resume_continue_path_intact(self):
        # زر ▶️ كمل الآن (cont:{pid}) ما زال تحت زرَي الرفض
        kb = bridge.build_model_decline_keyboard(URL, PID, KEY)
        self.assertIn(f"cont:{PID}", _callbacks(kb))

    def test_04_decline_status_constants_untouched(self):
        self.assertEqual(bridge.MODEL_DECLINED_STATUS, "MODEL_DECLINED")
        self.assertEqual(bridge.MODEL_DECLINE_MAX_RESPONSE_CHARS, 300)


if __name__ == "__main__":
    unittest.main(verbosity=2)
