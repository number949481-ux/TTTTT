"""
test_p32_account_password_lookup.py
===================================
حزمة حراسة [P32] — استخراج باسورد الحساب ببحث هجين (Hybrid Search):
إدخال يدوي مباشر للإيميل + تصفح الحسابات بنظام الصفحات (التالي/السابق) + إلغاء.

العقود المحروسة (مستخلصة من الفحص الميداني T0–T7 على السورس الفعلي):
  1. الزر في اللوحة أصبح «🔐 استخراج باسورد الحساب» (cmd:account_pwd_lookup)
     والزر القديم cmd:check_accs اختفى نهائياً من الملف.
  2. فتح الشاشة يعيّن AWAITING_ACCOUNT_PASSWORD_LOOKUP مع page=1.
  3. المسار اليدوي: نص الإيميل (بأي حالة أحرف/مسافات) يرجع الباسورد الصحيح.
  4. Pagination: 5/صفحة + حدود آمنة تماماً + تقليب In-Place بـ editMessageText.
  5. acc_view:{index} بالفهرس لا بالإيميل (حد callback_data = 64 بايت).
  6. الحالات الاستثنائية: إيميل غير موجود / حساب بلا باسورد / فهرس تالف / إلغاء.
  7. Zero Regression: القراءة فقط — صفر كتابة على ملف الحسابات (عقود P29/P30 سليمة).
"""
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

SRC = webapp_dir / "01.33_telegram_gen_bridge.py"


def _load_bridge():
    spec = importlib.util.spec_from_file_location("bridge_p32", SRC)
    module = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p32"] = module
    spec.loader.exec_module(module)
    return module


bridge = _load_bridge()


def _make_accounts(count: int) -> list[dict]:
    """حسابات اصطناعية بترتيب أبجدي متوقع: acc00@x.com .. accNN@x.com"""
    return [
        {
            "email": f"acc{i:02d}@example.com",
            "password": f"Pass#{i:02d}@XYZ",
            "status": "active",
            "active": True,
            "balance": 100 + i,
        }
        for i in range(count)
    ]


class _AccountsFixture:
    """ملف حسابات مؤقت على القرص يُمرَّر عبر json_path (بلا لمس ملف المشروع)."""

    def __init__(self, accounts):
        self.accounts = accounts
        self._tmp = None

    def __enter__(self):
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump(self.accounts, self._tmp, ensure_ascii=False)
        self._tmp.close()
        return self._tmp.name

    def __exit__(self, *exc):
        try:
            pathlib.Path(self._tmp.name).unlink()
        except Exception:
            pass
        return False


# ══════════════════════════════════════════════════════════════
# 1) عقود السورس: الزر الجديد وغياب الزر القديم
# ══════════════════════════════════════════════════════════════
class TestDashboardButtonContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SRC.read_text(encoding="utf-8")

    def test_01_new_button_label_present(self):
        self.assertIn("🔐 استخراج باسورد الحساب", self.src)

    def test_02_new_callback_present(self):
        self.assertIn('"callback_data": "cmd:account_pwd_lookup"', self.src)

    def test_03_old_check_accs_callback_removed(self):
        self.assertNotIn("check_accs", self.src)

    def test_04_old_button_label_removed(self):
        self.assertNotIn("📊 فحص الحسابات والكريدت", self.src)

    def test_05_dashboard_keyboard_exposes_lookup(self):
        kb = bridge.build_dashboard_keyboard(12345)
        flat = [b for row in kb["inline_keyboard"] for b in row]
        callbacks = [b.get("callback_data") for b in flat]
        self.assertIn("cmd:account_pwd_lookup", callbacks)
        self.assertNotIn("cmd:check_accs", callbacks)

    def test_06_state_constant_defined(self):
        self.assertEqual(
            bridge.AWAITING_ACCOUNT_PASSWORD_LOOKUP,
            "AWAITING_ACCOUNT_PASSWORD_LOOKUP",
        )

    def test_07_page_size_is_five(self):
        self.assertEqual(bridge.ACCOUNTS_PER_PAGE, 5)


# ══════════════════════════════════════════════════════════════
# 2) قائمة الحسابات: ترتيب ثابت وتصفية آمنة
# ══════════════════════════════════════════════════════════════
class TestLookupAccountListing(unittest.TestCase):
    def test_01_deterministic_alphabetical_order(self):
        shuffled = [
            {"email": "zeta@x.com", "password": "z"},
            {"email": "Alpha@x.com", "password": "a"},
            {"email": "mid@x.com", "password": "m"},
        ]
        with _AccountsFixture(shuffled) as path:
            emails = [a["email"] for a in bridge.list_lookup_accounts(path)]
        self.assertEqual(emails, ["Alpha@x.com", "mid@x.com", "zeta@x.com"])

    def test_02_skips_entries_without_email(self):
        messy = [
            {"email": "good@x.com", "password": "p"},
            {"email": "", "password": "p"},
            {"password": "orphan"},
            "not-a-dict",
        ]
        with _AccountsFixture(messy) as path:
            result = bridge.list_lookup_accounts(path)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["email"], "good@x.com")

    def test_03_empty_file_returns_empty_list(self):
        with _AccountsFixture([]) as path:
            self.assertEqual(bridge.list_lookup_accounts(path), [])

    def test_04_read_only_never_mutates_file(self):
        accounts = _make_accounts(4)
        with _AccountsFixture(accounts) as path:
            before = pathlib.Path(path).read_text(encoding="utf-8")
            bridge.list_lookup_accounts(path)
            bridge.find_account_by_email("acc02@example.com", path)
            bridge.render_account_lookup_text(page=1, json_path=path)
            bridge.build_account_lookup_keyboard(page=1, json_path=path)
            after = pathlib.Path(path).read_text(encoding="utf-8")
        self.assertEqual(before, after)


# ══════════════════════════════════════════════════════════════
# 3) حدود الصفحات — Out-of-Bounds Safe
# ══════════════════════════════════════════════════════════════
class TestAccountsPageBounds(unittest.TestCase):
    def test_01_first_page_of_twelve(self):
        self.assertEqual(bridge.compute_accounts_page_bounds(12, 1), (1, 3, 0))

    def test_02_middle_page(self):
        self.assertEqual(bridge.compute_accounts_page_bounds(12, 2), (2, 3, 5))

    def test_03_last_page(self):
        self.assertEqual(bridge.compute_accounts_page_bounds(12, 3), (3, 3, 10))

    def test_04_page_beyond_last_clamps_down(self):
        self.assertEqual(bridge.compute_accounts_page_bounds(12, 99), (3, 3, 10))

    def test_05_zero_and_negative_clamp_up(self):
        self.assertEqual(bridge.compute_accounts_page_bounds(12, 0), (1, 3, 0))
        self.assertEqual(bridge.compute_accounts_page_bounds(12, -7), (1, 3, 0))

    def test_06_garbage_page_defaults_to_first(self):
        for junk in ("abc", None, "", [], {}):
            self.assertEqual(bridge.compute_accounts_page_bounds(12, junk), (1, 3, 0))

    def test_07_empty_total_still_one_page(self):
        self.assertEqual(bridge.compute_accounts_page_bounds(0, 1), (1, 1, 0))

    def test_08_exact_multiple_has_no_phantom_page(self):
        self.assertEqual(bridge.compute_accounts_page_bounds(10, 2), (2, 2, 5))
        self.assertEqual(bridge.compute_accounts_page_bounds(10, 3), (2, 2, 5))


# ══════════════════════════════════════════════════════════════
# 4) البحث اليدوي بالإيميل
# ══════════════════════════════════════════════════════════════
class TestManualEmailSearch(unittest.TestCase):
    def test_01_exact_match_returns_password(self):
        with _AccountsFixture(_make_accounts(6)) as path:
            acc = bridge.find_account_by_email("acc03@example.com", path)
        self.assertIsNotNone(acc)
        self.assertEqual(acc["password"], "Pass#03@XYZ")

    def test_02_case_and_whitespace_insensitive(self):
        with _AccountsFixture(_make_accounts(6)) as path:
            acc = bridge.find_account_by_email("  ACC04@EXAMPLE.COM  ", path)
        self.assertIsNotNone(acc)
        self.assertEqual(acc["email"], "acc04@example.com")

    def test_03_missing_email_returns_none(self):
        with _AccountsFixture(_make_accounts(6)) as path:
            self.assertIsNone(bridge.find_account_by_email("ghost@nope.com", path))

    def test_04_blank_input_returns_none(self):
        with _AccountsFixture(_make_accounts(6)) as path:
            for blank in ("", "   ", None):
                self.assertIsNone(bridge.find_account_by_email(blank, path))

    def test_05_no_partial_substring_match(self):
        with _AccountsFixture(_make_accounts(6)) as path:
            self.assertIsNone(bridge.find_account_by_email("acc03", path))


# ══════════════════════════════════════════════════════════════
# 5) كارت النتيجة
# ══════════════════════════════════════════════════════════════
class TestPasswordCardRendering(unittest.TestCase):
    def test_01_email_and_password_are_copyable_code(self):
        acc = {"email": "horus@qejjyl.com", "password": "Pass#2026@XYZ", "status": "active"}
        card = bridge.render_account_password_card(acc)
        self.assertIn("<code>horus@qejjyl.com</code>", card)
        self.assertIn("<code>Pass#2026@XYZ</code>", card)

    def test_02_missing_password_is_reported_explicitly(self):
        acc = {"email": "nopass@x.com", "password": "", "status": "active"}
        card = bridge.render_account_password_card(acc)
        self.assertIn("لا يوجد باسورد مسجل لهذا الحساب", card)
        self.assertNotIn("<code></code>", card)

    def test_03_absent_password_key_does_not_crash(self):
        card = bridge.render_account_password_card({"email": "x@y.com"})
        self.assertIn("لا يوجد باسورد مسجل", card)

    def test_04_html_special_chars_escaped(self):
        acc = {"email": "a<b>@x.com", "password": "p&<script>"}
        card = bridge.render_account_password_card(acc)
        self.assertIn("&lt;", card)
        self.assertNotIn("<script>", card)

    def test_05_status_line_reflects_active(self):
        acc = {"email": "a@x.com", "password": "p", "status": "active", "active": True}
        self.assertIn("نشط (ACTIVE)", bridge.render_account_password_card(acc))

    def test_06_banned_state_described(self):
        self.assertIn("محظور", bridge.describe_account_state({"email": "a@x.com", "status": "banned"}))

    def test_07_cooldown_state_described(self):
        import time as _t
        acc = {"email": "a@x.com", "status": "cooldown", "cooldown_until": _t.time() + 9999}
        self.assertIn("COOLDOWN", bridge.describe_account_state(acc))

    def test_08_card_keyboard_has_retry_and_back(self):
        kb = bridge.build_account_password_card_keyboard()
        callbacks = [b["callback_data"] for row in kb["inline_keyboard"] for b in row]
        self.assertIn("cmd:account_pwd_lookup", callbacks)
        self.assertIn("cmd:show_dashboard", callbacks)


# ══════════════════════════════════════════════════════════════
# 6) كيبورد الشاشة الهجينة والتصفح
# ══════════════════════════════════════════════════════════════
class TestLookupKeyboardPagination(unittest.TestCase):
    def test_01_first_page_shows_five_accounts(self):
        with _AccountsFixture(_make_accounts(12)) as path:
            kb = bridge.build_account_lookup_keyboard(page=1, json_path=path)
        views = [
            b["callback_data"]
            for row in kb["inline_keyboard"] for b in row
            if b["callback_data"].startswith("acc_view:")
        ]
        self.assertEqual(views, [f"acc_view:{i}" for i in range(5)])

    def test_02_second_page_uses_absolute_indices(self):
        with _AccountsFixture(_make_accounts(12)) as path:
            kb = bridge.build_account_lookup_keyboard(page=2, json_path=path)
        views = [
            b["callback_data"]
            for row in kb["inline_keyboard"] for b in row
            if b["callback_data"].startswith("acc_view:")
        ]
        self.assertEqual(views, [f"acc_view:{i}" for i in range(5, 10)])

    def test_03_first_page_has_next_but_no_prev(self):
        with _AccountsFixture(_make_accounts(12)) as path:
            kb = bridge.build_account_lookup_keyboard(page=1, json_path=path)
        callbacks = [b["callback_data"] for row in kb["inline_keyboard"] for b in row]
        self.assertIn("acc_page:2", callbacks)
        self.assertNotIn("acc_page:0", callbacks)

    def test_04_last_page_has_prev_but_no_next(self):
        with _AccountsFixture(_make_accounts(12)) as path:
            kb = bridge.build_account_lookup_keyboard(page=3, json_path=path)
        callbacks = [b["callback_data"] for row in kb["inline_keyboard"] for b in row]
        self.assertIn("acc_page:2", callbacks)
        self.assertNotIn("acc_page:4", callbacks)

    def test_05_middle_page_has_both_directions(self):
        with _AccountsFixture(_make_accounts(12)) as path:
            kb = bridge.build_account_lookup_keyboard(page=2, json_path=path)
        callbacks = [b["callback_data"] for row in kb["inline_keyboard"] for b in row]
        self.assertIn("acc_page:1", callbacks)
        self.assertIn("acc_page:3", callbacks)

    def test_06_counter_button_is_noop(self):
        with _AccountsFixture(_make_accounts(12)) as path:
            kb = bridge.build_account_lookup_keyboard(page=2, json_path=path)
        labels = {b["callback_data"]: b["text"] for row in kb["inline_keyboard"] for b in row}
        self.assertIn("acc_page:noop", labels)
        self.assertIn("2 / 3", labels["acc_page:noop"])

    def test_07_single_page_hides_nav_row(self):
        with _AccountsFixture(_make_accounts(3)) as path:
            kb = bridge.build_account_lookup_keyboard(page=1, json_path=path)
        callbacks = [b["callback_data"] for row in kb["inline_keyboard"] for b in row]
        self.assertFalse([c for c in callbacks if c.startswith("acc_page:")])

    def test_08_cancel_button_always_present(self):
        for count in (0, 3, 12):
            with _AccountsFixture(_make_accounts(count)) as path:
                kb = bridge.build_account_lookup_keyboard(page=1, json_path=path)
            callbacks = [b["callback_data"] for row in kb["inline_keyboard"] for b in row]
            self.assertIn("acc_cancel", callbacks, f"count={count}")

    def test_09_callback_data_within_telegram_64_byte_limit(self):
        long_accounts = [
            {"email": f"extremely.long.address.number{i:03d}@some-really-long-domain.example.com",
             "password": "p"}
            for i in range(12)
        ]
        with _AccountsFixture(long_accounts) as path:
            kb = bridge.build_account_lookup_keyboard(page=1, json_path=path)
        for row in kb["inline_keyboard"]:
            for b in row:
                self.assertLessEqual(len(b["callback_data"].encode("utf-8")), 64, b)

    def test_10_empty_db_text_reports_no_accounts(self):
        with _AccountsFixture([]) as path:
            text = bridge.render_account_lookup_text(page=1, json_path=path)
        self.assertIn("لا توجد حسابات مسجلة", text)

    def test_11_text_shows_page_position_and_total(self):
        with _AccountsFixture(_make_accounts(12)) as path:
            text = bridge.render_account_lookup_text(page=2, json_path=path)
        self.assertIn("<b>2</b>", text)
        self.assertIn("<b>3</b>", text)
        self.assertIn("<b>12</b>", text)

    def test_12_text_invites_manual_typing(self):
        with _AccountsFixture(_make_accounts(6)) as path:
            text = bridge.render_account_lookup_text(page=1, json_path=path)
        self.assertIn("اكتب الإيميل المطلوب في الشات", text)


# ══════════════════════════════════════════════════════════════
# 7) التدفق الكامل عبر handle_telegram_update (End-to-End مُحاكى)
# ══════════════════════════════════════════════════════════════
class _FlowHarness(unittest.TestCase):
    """أساس مشترك: يعترض إرسال/تعديل الرسائل ويثبّت ملف حسابات مؤقت."""

    def setUp(self):
        self.sent = []
        self.edited = []
        self.tasks = []
        self.accounts = _make_accounts(12)

        self._fixture = _AccountsFixture(self.accounts)
        self.acc_path = self._fixture.__enter__()

        self._orig = {
            "send": bridge.send_telegram_message,
            "edit": bridge.edit_telegram_message_text,
            "allowed": bridge.is_chat_allowed,
            "lookup": bridge.list_lookup_accounts,
            "find": bridge.find_account_by_email,
            "render": bridge.render_account_lookup_text,
            "kb": bridge.build_account_lookup_keyboard,
            "executor": bridge.EXECUTOR,
        }

        bridge.send_telegram_message = lambda cid, text, **kw: (
            self.sent.append({"chat_id": cid, "text": text, **kw}) or {"ok": True}
        )
        bridge.edit_telegram_message_text = lambda cid, mid, text, **kw: (
            self.edited.append({"chat_id": cid, "message_id": mid, "text": text, **kw}) or {"ok": True}
        )
        bridge.is_chat_allowed = lambda *a, **k: True
        bridge.list_lookup_accounts = lambda json_path=None: self._orig["lookup"](self.acc_path)
        bridge.find_account_by_email = lambda email, json_path=None: self._orig["find"](email, self.acc_path)
        bridge.render_account_lookup_text = lambda page=1, json_path=None: self._orig["render"](page=page, json_path=self.acc_path)
        bridge.build_account_lookup_keyboard = lambda page=1, json_path=None: self._orig["kb"](page=page, json_path=self.acc_path)

        harness = self

        class _FakeExecutor:
            def submit(self, fn, *args, **kwargs):
                harness.tasks.append((fn, args, kwargs))
                return None

        bridge.EXECUTOR = _FakeExecutor()
        bridge.set_user_state(999, {})

    def tearDown(self):
        bridge.send_telegram_message = self._orig["send"]
        bridge.edit_telegram_message_text = self._orig["edit"]
        bridge.is_chat_allowed = self._orig["allowed"]
        bridge.list_lookup_accounts = self._orig["lookup"]
        bridge.find_account_by_email = self._orig["find"]
        bridge.render_account_lookup_text = self._orig["render"]
        bridge.build_account_lookup_keyboard = self._orig["kb"]
        bridge.EXECUTOR = self._orig["executor"]
        bridge.set_user_state(999, {})
        self._fixture.__exit__(None, None, None)

    def _cb(self, data, message_id=555):
        bridge.handle_telegram_update({
            "callback_query": {
                "data": data,
                "from": {"id": 999},
                "message": {"message_id": message_id, "chat": {"id": 999}},
            }
        })

    def _text(self, text):
        bridge.handle_telegram_update({
            "message": {"chat": {"id": 999}, "from": {"id": 999}, "text": text}
        })


class TestOpenLookupScreen(_FlowHarness):
    def test_01_sets_interactive_state_with_page_one(self):
        self._cb("cmd:account_pwd_lookup")
        state = bridge.get_user_state(999)
        self.assertEqual(state.get("action"), "AWAITING_ACCOUNT_PASSWORD_LOOKUP")
        self.assertEqual(state.get("page"), 1)

    def test_02_sends_hybrid_screen_with_keyboard(self):
        self._cb("cmd:account_pwd_lookup")
        self.assertEqual(len(self.sent), 1)
        self.assertIn("استخراج باسورد", self.sent[0]["text"])
        callbacks = [
            b["callback_data"]
            for row in self.sent[0]["reply_markup"]["inline_keyboard"] for b in row
        ]
        self.assertIn("acc_view:0", callbacks)
        self.assertIn("acc_cancel", callbacks)


class TestManualPathThroughUpdate(_FlowHarness):
    def test_01_typed_email_returns_password_card(self):
        self._cb("cmd:account_pwd_lookup")
        self._text("acc07@example.com")
        card = self.sent[-1]["text"]
        self.assertIn("<code>acc07@example.com</code>", card)
        self.assertIn("<code>Pass#07@XYZ</code>", card)

    def test_02_typed_email_is_case_insensitive(self):
        self._cb("cmd:account_pwd_lookup")
        self._text("  ACC02@EXAMPLE.COM ")
        self.assertIn("<code>Pass#02@XYZ</code>", self.sent[-1]["text"])

    def test_03_state_cleared_after_success(self):
        self._cb("cmd:account_pwd_lookup")
        self._text("acc01@example.com")
        # العقد الفعلي: set_user_state(chat_id, {}) يبصم ts — التصفير = غياب action
        self.assertFalse(bridge.get_user_state(999).get("action"))

    def test_04_email_is_not_dispatched_as_task_prompt(self):
        self._cb("cmd:account_pwd_lookup")
        self._text("acc01@example.com")
        self.assertEqual(self.tasks, [], "الإيميل يجب ألا يُرسل كبرومبت مهمة")

    def test_05_unknown_email_reports_error_and_keeps_state(self):
        self._cb("cmd:account_pwd_lookup")
        self._text("ghost@nowhere.com")
        self.assertIn("غير مسجل في قاعدة الحسابات", self.sent[-1]["text"])
        self.assertEqual(
            bridge.get_user_state(999).get("action"),
            "AWAITING_ACCOUNT_PASSWORD_LOOKUP",
        )

    def test_06_unknown_email_offers_retry_keyboard(self):
        self._cb("cmd:account_pwd_lookup")
        self._text("ghost@nowhere.com")
        callbacks = [
            b["callback_data"]
            for row in self.sent[-1]["reply_markup"]["inline_keyboard"] for b in row
        ]
        self.assertIn("cmd:account_pwd_lookup", callbacks)
        self.assertIn("acc_cancel", callbacks)

    def test_07_retry_after_failure_succeeds(self):
        self._cb("cmd:account_pwd_lookup")
        self._text("ghost@nowhere.com")
        self._text("acc05@example.com")
        self.assertIn("<code>Pass#05@XYZ</code>", self.sent[-1]["text"])

    def test_08_no_regression_plain_text_reaches_intent_guard(self):
        # 🛡️ [P42] تحديث واعٍ موثّق (DEC-038): النص الحر في IDLE لم يعد يُجدول تلقائياً —
        # يمر على Intent Guard (بطاقة تأكيد — صفر Mutation). جوهر عقد P32 باقٍ:
        # النص خارج حالة الـ Lookup لا يُعامل كإيميل ولا يُفتح بطاقة باسورد.
        self._text("ابنِ لي موقعاً بسيطاً")
        self.assertEqual(self.tasks, [], "P42: لا جدولة قبل التأكيد")
        self.assertEqual(
            bridge.get_user_state(999).get("action"),
            bridge.AWAITING_PROJECT_CONFIRMATION,
        )
        self.assertNotIn("بيانات الحساب", self.sent[-1]["text"] if self.sent else "")


class TestPaginationThroughUpdate(_FlowHarness):
    def test_01_next_page_edits_in_place(self):
        self._cb("cmd:account_pwd_lookup")
        sent_before = len(self.sent)
        self._cb("acc_page:2")
        self.assertEqual(len(self.edited), 1)
        self.assertEqual(len(self.sent), sent_before, "التقليب لا يرسل رسالة جديدة")
        self.assertEqual(self.edited[0]["message_id"], 555)

    def test_02_next_page_shows_second_batch(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_page:2")
        callbacks = [
            b["callback_data"]
            for row in self.edited[-1]["reply_markup"]["inline_keyboard"] for b in row
        ]
        self.assertIn("acc_view:5", callbacks)
        self.assertNotIn("acc_view:0", callbacks)

    def test_03_prev_page_returns_to_first_batch(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_page:2")
        self._cb("acc_page:1")
        callbacks = [
            b["callback_data"]
            for row in self.edited[-1]["reply_markup"]["inline_keyboard"] for b in row
        ]
        self.assertIn("acc_view:0", callbacks)

    def test_04_page_persisted_in_state(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_page:3")
        self.assertEqual(bridge.get_user_state(999).get("page"), 3)

    def test_05_manual_input_still_works_while_browsing(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_page:3")
        self._text("acc09@example.com")
        self.assertIn("<code>Pass#09@XYZ</code>", self.sent[-1]["text"])

    def test_06_out_of_range_page_clamps_without_crash(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_page:999")
        self.assertEqual(bridge.get_user_state(999).get("page"), 3)

    def test_07_garbage_page_token_clamps_to_first(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_page:abc")
        self.assertEqual(bridge.get_user_state(999).get("page"), 1)

    def test_08_noop_counter_does_nothing(self):
        self._cb("cmd:account_pwd_lookup")
        sent_before, edited_before = len(self.sent), len(self.edited)
        self._cb("acc_page:noop")
        self.assertEqual(len(self.sent), sent_before)
        self.assertEqual(len(self.edited), edited_before)


class TestAccountViewButton(_FlowHarness):
    def test_01_click_email_button_shows_card(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_view:3")
        card = self.sent[-1]["text"]
        self.assertIn("<code>acc03@example.com</code>", card)
        self.assertIn("<code>Pass#03@XYZ</code>", card)

    def test_02_click_from_second_page_index(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_page:2")
        self._cb("acc_view:7")
        self.assertIn("<code>acc07@example.com</code>", self.sent[-1]["text"])

    def test_03_card_offers_lookup_again_and_dashboard(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_view:0")
        callbacks = [
            b["callback_data"]
            for row in self.sent[-1]["reply_markup"]["inline_keyboard"] for b in row
        ]
        self.assertIn("cmd:account_pwd_lookup", callbacks)
        self.assertIn("cmd:show_dashboard", callbacks)

    def test_04_state_cleared_after_view(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_view:2")
        self.assertFalse(bridge.get_user_state(999).get("action"))

    def test_05_out_of_range_index_is_graceful(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_view:9999")
        self.assertIn("تعذر عرض هذا الحساب", self.sent[-1]["text"])

    def test_06_garbage_index_is_graceful(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_view:notanumber")
        self.assertIn("تعذر عرض هذا الحساب", self.sent[-1]["text"])

    def test_07_negative_index_rejected(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_view:-1")
        self.assertIn("تعذر عرض هذا الحساب", self.sent[-1]["text"])


class TestCancelPath(_FlowHarness):
    def test_01_cancel_clears_state(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_cancel")
        self.assertFalse(bridge.get_user_state(999).get("action"))

    def test_02_cancel_returns_dashboard_keyboard(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_cancel")
        callbacks = [
            b["callback_data"]
            for row in self.sent[-1]["reply_markup"]["inline_keyboard"] for b in row
        ]
        self.assertIn("cmd:account_pwd_lookup", callbacks)
        self.assertIn("cmd:new_proj", callbacks)

    def test_03_cancel_message_confirms_cancellation(self):
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_cancel")
        self.assertIn("تم إلغاء استخراج الباسورد", self.sent[-1]["text"])

    def test_04_text_after_cancel_leaves_lookup_and_reaches_intent_guard(self):
        # 🛡️ [P42] بعد الإلغاء النص يخرج من مسار الـ Lookup ويمر على Intent Guard
        # (بطاقة تأكيد — لا جدولة تلقائية بعد حذف الـ Fallback / DEC-038)
        self._cb("cmd:account_pwd_lookup")
        self._cb("acc_cancel")
        self._text("مهمة جديدة عادية")
        self.assertEqual(self.tasks, [], "P42: لا جدولة قبل التأكيد")
        self.assertEqual(
            bridge.get_user_state(999).get("action"),
            bridge.AWAITING_PROJECT_CONFIRMATION,
        )


# ══════════════════════════════════════════════════════════════
# 8) عقود السورس البنيوية (حراسة ضد الانحدار الصامت)
# ══════════════════════════════════════════════════════════════
class TestSourceStructureContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SRC.read_text(encoding="utf-8")

    def test_01_manual_path_precedes_other_states(self):
        """المسار اليدوي يجب أن يكون أول فحص action وإلا التقطته حالة أخرى."""
        lookup_at = self.src.index('if action == AWAITING_ACCOUNT_PASSWORD_LOOKUP:')
        first_wizard = self.src.index('if action == "AWAITING_NEW_PROJECT_NAME":')
        self.assertLess(lookup_at, first_wizard)

    def test_02_all_four_callbacks_handled(self):
        for token in (
            'data == "cmd:account_pwd_lookup"',
            'data.startswith("acc_page:")',
            'data.startswith("acc_view:")',
            'data == "acc_cancel"',
        ):
            self.assertIn(token, self.src, token)

    def test_03_view_callback_uses_index_not_email(self):
        self.assertIn('f"acc_view:{start_index + offset}"', self.src)

    def test_04_lookup_uses_read_accounts_safe_only(self):
        block_start = self.src.index("def list_lookup_accounts")
        block_end = self.src.index("def compute_accounts_page_bounds")
        block = self.src[block_start:block_end]
        self.assertIn("read_accounts_safe", block)
        for forbidden in ("update_account_data", "json.dump", "open("):
            self.assertNotIn(forbidden, block, forbidden)

    def test_05_p29_p30_contracts_untouched(self):
        for symbol in (
            "def record_account_journey",
            "def format_account_journey_line",
            "def open_account_timing_span",
            "def close_account_timing_span",
            "def format_account_timing_block",
            "def _lazy_ai_prefix",
        ):
            self.assertIn(symbol, self.src, symbol)


if __name__ == "__main__":
    unittest.main(verbosity=2)
