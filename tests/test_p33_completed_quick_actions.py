"""
test_p33_completed_quick_actions.py
===================================
حزمة حراسة [P33] — أزرار الإجراءات السريعة في كيبورد رسالة الاكتمال:
  [ ▶️ كمل الآن ] (cont:{resume_pid} بصف مستقل) + [ ⬅️ رجوع للوحة التحكم ] (cmd:dashboard أسفل الكيبورد).

العقود المحروسة (مستخلصة من الفحص الميداني على السورس الفعلي):
  1. الأزرار الخمسة القديمة كلها محفوظة حرفياً (نص + callback/url) — Zero Breaking:
     🌐 فتح المعاين المباشر / 🔄 استئناف هذا المشروع / 🌳 نقاط الاستئناف /
     ⭐ تفاصيل المشروع / 🚀 مشروع جديد.
  2. ▶️ كمل الآن: صف مستقل خاص به، callback = cont:{resume_pid} — يظهر فقط عند وجود resume_pid،
     وبنمط أخضر style == "success" (ضمن ALLOWED_BUTTON_STYLES المعتمدة).
  3. ⬅️ رجوع للوحة التحكم: آخر صف دائماً في كل التركيبات، callback = cmd:dashboard.
  4. الشرطية القديمة محفوظة: pub_url=None ⟹ لا زر url ميت (كان يكسر الرسالة بصمت)،
     resume_pid=None ⟹ لا أزرار استئناف، project_key=None ⟹ لا زر تفاصيل.
  5. معالج cmd:dashboard في الموزّع: سلوك مطابق حرفياً لـ cmd:show_dashboard
     (لوحة التحكم كاملة) — فرع منفصل بلا مساس بحرفية الفرع القديم (مرساة حراس P26).
  6. عقود مصدرية: الاستدعاء المركزي داخل process_user_task_async بدل بناء kb_rows المحلي.
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
    spec = importlib.util.spec_from_file_location("bridge_p33", SRC)
    module = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p33"] = module
    spec.loader.exec_module(module)
    return module


bridge = _load_bridge()

PID = "prj_p33_abcdef123456"
KEY = "proj_key_p33"
URL = "https://example.com/preview/p33"


def _rows(kb: dict) -> list:
    return kb["inline_keyboard"]


def _flat(kb: dict) -> list:
    return [btn for row in _rows(kb) for btn in row]


def _callbacks(kb: dict) -> list:
    return [b.get("callback_data") for b in _flat(kb) if "callback_data" in b]


def _texts(kb: dict) -> list:
    return [b.get("text") for b in _flat(kb)]


# ══════════════════════════════════════════════════════════════
# 1) البنية الكاملة: كل المدخلات متوفرة
# ══════════════════════════════════════════════════════════════
class TestFullKeyboardComposition(unittest.TestCase):
    def setUp(self):
        self.kb = bridge.build_completed_message_keyboard(URL, PID, KEY)

    def test_01_returns_inline_keyboard_dict(self):
        self.assertIsInstance(self.kb, dict)
        self.assertIn("inline_keyboard", self.kb)

    def test_02_six_rows_in_exact_order(self):
        rows = _rows(self.kb)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0][0]["text"], "🌐 فتح المعاين المباشر")
        self.assertEqual(rows[1][0]["text"], "▶️ كمل الآن")
        self.assertEqual(rows[2][0]["text"], "🔄 استئناف هذا المشروع")
        self.assertEqual(rows[2][1]["text"], "🌳 نقاط الاستئناف")
        self.assertEqual(rows[3][0]["text"], "⭐ تفاصيل المشروع")
        self.assertEqual(rows[4][0]["text"], "🚀 مشروع جديد")
        self.assertEqual(rows[5][0]["text"], "⬅️ رجوع للوحة التحكم")

    def test_03_all_five_legacy_buttons_intact(self):
        texts = _texts(self.kb)
        for legacy in (
            "🌐 فتح المعاين المباشر",
            "🔄 استئناف هذا المشروع",
            "🌳 نقاط الاستئناف",
            "⭐ تفاصيل المشروع",
            "🚀 مشروع جديد",
        ):
            self.assertIn(legacy, texts)

    def test_04_legacy_callbacks_unchanged(self):
        callbacks = _callbacks(self.kb)
        self.assertIn(f"cont:{PID}", callbacks)
        self.assertIn(f"tree:{PID}", callbacks)
        self.assertIn(f"pview:{KEY}", callbacks)
        self.assertIn("cmd:new_proj", callbacks)

    def test_05_preview_button_is_url_not_callback(self):
        preview = _rows(self.kb)[0][0]
        self.assertEqual(preview.get("url"), URL)
        self.assertNotIn("callback_data", preview)


# ══════════════════════════════════════════════════════════════
# 2) الزر الجديد الأول: ▶️ كمل الآن
# ══════════════════════════════════════════════════════════════
class TestContinueNowButton(unittest.TestCase):
    def test_01_dedicated_row_alone(self):
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        row = _rows(kb)[1]
        self.assertEqual(len(row), 1)
        self.assertEqual(row[0]["text"], "▶️ كمل الآن")

    def test_02_callback_is_cont_resume_pid(self):
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        self.assertEqual(_rows(kb)[1][0]["callback_data"], f"cont:{PID}")

    def test_02b_style_is_success_green(self):
        """زر ▶️ كمل الآن أخضر: style == "success" حرفياً."""
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        self.assertEqual(_rows(kb)[1][0]["style"], "success")

    def test_02c_success_style_is_in_allowed_styles(self):
        """النمط المستخدم ضمن ALLOWED_BUTTON_STYLES — لن يسقط في make_inline_keyboard."""
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        self.assertIn(_rows(kb)[1][0]["style"], bridge.ALLOWED_BUTTON_STYLES)

    def test_02d_legacy_resume_button_has_no_style(self):
        """Zero Breaking: زر 🔄 استئناف هذا المشروع القديم بلا style — لم يُمَس."""
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        self.assertNotIn("style", _rows(kb)[2][0])

    def test_03_reuses_existing_cont_handler_prefix(self):
        """يعيد استعمال معالج cont: القائم — نفس بادئة زر الاستئناف القديم حرفياً."""
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        continue_cb = _rows(kb)[1][0]["callback_data"]
        legacy_cb = _rows(kb)[2][0]["callback_data"]
        self.assertEqual(continue_cb, legacy_cb)

    def test_04_hidden_without_resume_pid(self):
        kb = bridge.build_completed_message_keyboard(URL, None, KEY)
        self.assertNotIn("▶️ كمل الآن", _texts(kb))

    def test_05_hidden_with_empty_resume_pid(self):
        kb = bridge.build_completed_message_keyboard(URL, "", KEY)
        self.assertNotIn("▶️ كمل الآن", _texts(kb))

    def test_06_callback_data_within_telegram_64_byte_limit(self):
        """عقد P25/P32: حد callback_data في تيليجرام 64 بايت — قياس فعلي بالبايتات."""
        long_pid = "prj_" + "a" * 40
        kb = bridge.build_completed_message_keyboard(URL, long_pid, KEY)
        for btn in _flat(kb):
            cb = btn.get("callback_data")
            if cb:
                self.assertLessEqual(len(cb.encode("utf-8")), 64, f"callback أطول من 64 بايت: {cb}")


# ══════════════════════════════════════════════════════════════
# 3) الزر الجديد الثاني: ⬅️ رجوع للوحة التحكم
# ══════════════════════════════════════════════════════════════
class TestBackToDashboardButton(unittest.TestCase):
    def test_01_always_last_row_full_composition(self):
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        last = _rows(kb)[-1]
        self.assertEqual(len(last), 1)
        self.assertEqual(last[0]["text"], "⬅️ رجوع للوحة التحكم")
        self.assertEqual(last[0]["callback_data"], "cmd:dashboard")

    def test_02_always_last_even_minimal_composition(self):
        kb = bridge.build_completed_message_keyboard(None, None, None)
        last = _rows(kb)[-1]
        self.assertEqual(last[0]["callback_data"], "cmd:dashboard")

    def test_03_present_in_all_8_input_combinations(self):
        for pub in (URL, None):
            for pid in (PID, None):
                for key in (KEY, None):
                    kb = bridge.build_completed_message_keyboard(pub, pid, key)
                    self.assertEqual(
                        _rows(kb)[-1][0]["callback_data"], "cmd:dashboard",
                        f"غاب زر الرجوع في التركيبة pub={bool(pub)} pid={bool(pid)} key={bool(key)}",
                    )

    def test_04_new_project_row_stays_above_back_row(self):
        kb = bridge.build_completed_message_keyboard(None, None, None)
        rows = _rows(kb)
        self.assertEqual(rows[-2][0]["callback_data"], "cmd:new_proj")


# ══════════════════════════════════════════════════════════════
# 4) الشرطية القديمة محفوظة (Zero Regression)
# ══════════════════════════════════════════════════════════════
class TestConditionalRowsPreserved(unittest.TestCase):
    def test_01_no_dead_url_button_when_pub_url_missing(self):
        """url=None كان يكسر الرسالة كلها بصمت — العقد التاريخي محفوظ."""
        kb = bridge.build_completed_message_keyboard(None, PID, KEY)
        self.assertNotIn("🌐 فتح المعاين المباشر", _texts(kb))
        for btn in _flat(kb):
            self.assertIsNotNone(btn.get("callback_data") or btn.get("url"))

    def test_02_no_resume_rows_without_pid(self):
        kb = bridge.build_completed_message_keyboard(URL, None, KEY)
        texts = _texts(kb)
        self.assertNotIn("🔄 استئناف هذا المشروع", texts)
        self.assertNotIn("🌳 نقاط الاستئناف", texts)

    def test_03_no_details_button_without_project_key(self):
        kb = bridge.build_completed_message_keyboard(URL, PID, None)
        self.assertNotIn("⭐ تفاصيل المشروع", _texts(kb))

    def test_04_minimal_keyboard_still_has_two_rows(self):
        kb = bridge.build_completed_message_keyboard(None, None, None)
        rows = _rows(kb)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0]["callback_data"], "cmd:new_proj")
        self.assertEqual(rows[1][0]["callback_data"], "cmd:dashboard")

    def test_05_resume_and_tree_share_same_row_as_before(self):
        kb = bridge.build_completed_message_keyboard(URL, PID, KEY)
        resume_row = _rows(kb)[2]
        self.assertEqual(len(resume_row), 2)
        self.assertEqual(resume_row[0]["callback_data"], f"cont:{PID}")
        self.assertEqual(resume_row[1]["callback_data"], f"tree:{PID}")


# ══════════════════════════════════════════════════════════════
# 5) معالج cmd:dashboard في الموزّع — سلوك حي مُحاكى
# ══════════════════════════════════════════════════════════════
class TestDashboardCallbackHandler(unittest.TestCase):
    CHAT = 991133

    def setUp(self):
        self.sent = []
        self._orig_send = bridge.send_telegram_message
        self._orig_allowed = bridge.is_chat_allowed
        self._orig_render = bridge.render_dashboard_text
        self._orig_kb = bridge.get_main_keyboard
        bridge.send_telegram_message = lambda cid, text, **kw: (
            self.sent.append({"chat_id": cid, "text": text, **kw}) or {"ok": True}
        )
        bridge.is_chat_allowed = lambda *a, **k: True
        bridge.render_dashboard_text = lambda cid: f"DASH_TEXT_{cid}"
        bridge.get_main_keyboard = lambda cid: {"inline_keyboard": [[{"text": "K", "callback_data": "cmd:show_dashboard"}]]}

    def tearDown(self):
        bridge.send_telegram_message = self._orig_send
        bridge.is_chat_allowed = self._orig_allowed
        bridge.render_dashboard_text = self._orig_render
        bridge.get_main_keyboard = self._orig_kb

    def _cb(self, data):
        bridge.handle_telegram_update({
            "callback_query": {
                "data": data,
                "from": {"id": self.CHAT},
                "message": {"message_id": 777, "chat": {"id": self.CHAT}},
            }
        })

    def test_01_cmd_dashboard_sends_full_dashboard(self):
        self._cb("cmd:dashboard")
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.sent[0]["text"], f"DASH_TEXT_{self.CHAT}")
        self.assertIsNotNone(self.sent[0].get("reply_markup"))

    def test_02_behavior_identical_to_show_dashboard(self):
        self._cb("cmd:dashboard")
        first = dict(self.sent[0])
        self.sent.clear()
        self._cb("cmd:show_dashboard")
        second = dict(self.sent[0])
        self.assertEqual(first["text"], second["text"])
        self.assertEqual(first["reply_markup"], second["reply_markup"])

    def test_03_unauthorized_chat_blocked(self):
        bridge.is_chat_allowed = lambda *a, **k: False
        self._cb("cmd:dashboard")
        self.assertEqual(len(self.sent), 1)
        self.assertIn("غير مصرح", self.sent[0]["text"])


# ══════════════════════════════════════════════════════════════
# 6) عقود مصدرية بنيوية (Structural Source Contracts)
# ══════════════════════════════════════════════════════════════
class TestSourceContracts(unittest.TestCase):
    def test_01_worker_calls_central_builder(self):
        """process_user_task_async يستدعي البنّاء المركزي بدل kb_rows المحلي."""
        worker_start = BRIDGE_SRC.index("def process_user_task_async")
        worker_chunk = BRIDGE_SRC[worker_start:worker_start + 30000]
        self.assertIn(
            "reply_markup = build_completed_message_keyboard(pub_url, resume_pid, project_key)",
            worker_chunk,
        )

    def test_02_builder_defined_exactly_once(self):
        self.assertEqual(BRIDGE_SRC.count("def build_completed_message_keyboard("), 1)

    def test_03_dashboard_branch_exists_in_dispatcher(self):
        self.assertIn('elif data == "cmd:dashboard":', BRIDGE_SRC)

    def test_04_legacy_show_dashboard_branch_untouched(self):
        """مرساة حراس P26: حرفية الفرع القديم if data == "cmd:show_dashboard" باقية."""
        self.assertIn('if data == "cmd:show_dashboard"', BRIDGE_SRC)

    def test_05_dashboard_branch_comes_after_show_dashboard(self):
        """الفرع الجديد elif يلي الفرع القديم if في نفس السلسلة."""
        old_pos = BRIDGE_SRC.index('if data == "cmd:show_dashboard"')
        new_pos = BRIDGE_SRC.index('elif data == "cmd:dashboard":')
        self.assertGreater(new_pos, old_pos)

    def test_06_continue_now_button_text_in_source(self):
        self.assertIn("▶️ كمل الآن", BRIDGE_SRC)

    def test_07_back_button_text_in_source(self):
        self.assertIn("⬅️ رجوع للوحة التحكم", BRIDGE_SRC)

    def test_08_no_local_kb_rows_left_in_worker(self):
        """صفر بناء محلي متبقٍ للكيبورد داخل الـ worker (منع الازدواجية)."""
        worker_start = BRIDGE_SRC.index("def process_user_task_async")
        # نهاية الـ worker = بداية get_main_keyboard التالية
        worker_end = BRIDGE_SRC.index("def get_main_keyboard", worker_start)
        worker_chunk = BRIDGE_SRC[worker_start:worker_end]
        self.assertNotIn("kb_rows = []", worker_chunk)


if __name__ == "__main__":
    unittest.main()
