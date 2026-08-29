#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p43_fast_lean_mode.py
=================================
⚡ [P43] حراسة المرحلة 43 — Fast Lean Mode & Artifacts/Diff Bypass
(وثيقة `17_FAST_LEAN_MODE_AND_ARTIFACTS_BYPASS.MD` — DEC-039).

العلة المعالجة: كل مشروع — حتى غير المربوط بـ GitHub — يمر بعد اكتمال
الموديل بـ download_project_archive (timeout 180s) + فك ضغط +
make_project_always_public (3×POST×15s) + registry.snapshot (sha256 لكل
ملف + Diff). الحل: حقل fast_mode واحد (افتراضي False — D5/R1) يتخطى
التنزيل/فك الضغط/snapshot فقط عند GitHub معطل (D3)، مع إبقاء
make_project_always_public (D2) وشجرة الاستئناف save_project_branch
دائماً + Telemetry FAST_MODE_SKIP (D7) + زر تنزيل متأخر pctl:fetch (D6)
+ شفافية كاملة (X7).

المصفوفة (16 اختباراً — الوثيقة 17 §6، Mocks/Spies بلا شبكة):
 1. الحقل في الافتراضيات (D5)          9. Zero-Regression بايت-ببايت
 2. Backward-Compat (F9)              10. Telemetry FAST_MODE_SKIP (D7)
 3. GitHub مفعّل يفرض التنزيل (D3)     11. كارت الاكتمال الشفاف (X7)
 4. fast off ➔ False (D3)             12. خطوة Wizard لـ GitHub-no فقط (D4)
 5. Toggle يعكس ويحفظ                 13. الاختيار + نجاة pending_prompt
 6. style=primary من الـ Whitelist (D1) 14. زر D6 = Pipeline كامل
 7. Spy: صفر تنزيل في fast mode        15. فشل صريح + Idempotency
 8. make_public تعمل في fast mode (D2) 16. عقود P40/المجمّد بلا تغيير
"""

import importlib.util
import pathlib
import re
import sys
import time
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIDGE_PATH = ROOT / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_p43", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("bridge_p43", _bridge)
_spec.loader.exec_module(_bridge)


# ═══════════════════════════════════════════════════════════════
# 1) Schema — الحقل الواحد fast_mode (D5/R1) + Backward-Compat (F9)
# ═══════════════════════════════════════════════════════════════
class TestFastModeSchema(unittest.TestCase):
    def test_default_settings_include_fast_mode_false(self):
        """[1] D5: الحقل موجود في الافتراضيات وقيمته False حرفياً."""
        settings = _bridge.default_project_settings()
        self.assertIn("fast_mode", settings)
        self.assertIs(settings["fast_mode"], False)
        # R1: لا حقل ثانٍ ولا Invariant — download_artifacts شبح محظور
        self.assertNotIn("download_artifacts", settings)
        self.assertNotIn("download_artifacts", BRIDGE_SRC)

    def test_old_manifest_without_field_reads_false(self):
        """[2] F9: مشروع قديم بلا الحقل يُقرأ False عبر Normalization حصرياً."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            # عزل السجل المركزي بنمط test_p26 (توقيع ProjectRegistry ثابت — مفتاح فقط)
            orig_home = _bridge.PROJECT_REGISTRY_HOME
            orig_index = _bridge.PROJECT_REGISTRY_INDEX_FILE
            _bridge.PROJECT_REGISTRY_HOME = pathlib.Path(td) / "project_registry"
            _bridge.PROJECT_REGISTRY_INDEX_FILE = _bridge.PROJECT_REGISTRY_HOME / "registry.json"
            _bridge.PROJECT_REGISTRY_HOME.mkdir(parents=True, exist_ok=True)
            try:
                reg = _bridge.ProjectRegistry("prj_p43compat")
                # manifest قديم: settings بلا fast_mode إطلاقاً
                old = {"model": "claude-opus-5-code", "github": {"enabled": False}}
                normalized = reg._normalize_project_settings(old)
                self.assertIn("fast_mode", normalized)
                self.assertIs(normalized["fast_mode"], False)
                # None / أنواع فاسدة ➔ False بلا Crash (الحدية 3/15)
                self.assertIs(reg._normalize_project_settings(None)["fast_mode"], False)
                self.assertIs(reg._normalize_project_settings({"fast_mode": "yes"})["fast_mode"], True)
                self.assertIs(reg._normalize_project_settings({"fast_mode": 0})["fast_mode"], False)
                # True يُحفظ ويعود True عبر جولة كتابة/قراءة كاملة (الحدية 15)
                saved = reg.update_project_settings({"fast_mode": True})
                self.assertIs(saved["fast_mode"], True)
                reread = reg.get_project_settings()
                self.assertIs(reread["fast_mode"], True)
            finally:
                _bridge.PROJECT_REGISTRY_HOME = orig_home
                _bridge.PROJECT_REGISTRY_INDEX_FILE = orig_index


# ═══════════════════════════════════════════════════════════════
# 2) الدالة الحاكمة should_skip_artifacts_download (D3 حرفياً)
# ═══════════════════════════════════════════════════════════════
class TestGoverningHelper(unittest.TestCase):
    def test_skip_helper_github_enabled_forces_download(self):
        """[3] D3/الحدية 2: GitHub مفعّل ⇒ التنزيل إلزامي حتى مع fast_mode=True."""
        self.assertFalse(_bridge.should_skip_artifacts_download(
            {"fast_mode": True, "github": {"enabled": True}}))
        # الحدية 10: تفعيل GitHub لاحقاً على مشروع fast ➔ D3 يفوز
        settings = _bridge.default_project_settings()
        settings["fast_mode"] = True
        settings["github"]["enabled"] = True
        self.assertFalse(_bridge.should_skip_artifacts_download(settings))

    def test_skip_helper_fast_off_returns_false(self):
        """[4] D3: fast_mode=False (أو غائب/فاسد) ⇒ لا تخطي — Zero Regression."""
        self.assertFalse(_bridge.should_skip_artifacts_download(
            {"fast_mode": False, "github": {"enabled": False}}))
        self.assertFalse(_bridge.should_skip_artifacts_download({}))
        self.assertFalse(_bridge.should_skip_artifacts_download({"github": None}))
        # الحالة الوحيدة الموجبة: fast=True + GitHub معطل
        self.assertTrue(_bridge.should_skip_artifacts_download(
            {"fast_mode": True, "github": {"enabled": False}}))
        self.assertTrue(_bridge.should_skip_artifacts_download({"fast_mode": True}))


# ═══════════════════════════════════════════════════════════════
# 3) CP3 — زر pset:fastmode:* (D1: style=primary) + Toggle يعكس ويحفظ
# ═══════════════════════════════════════════════════════════════
class _IsolatedRegistryMixin:
    """عزل سجل المشاريع في مجلد مؤقت (نمط test_p26) + كتم الشبكة."""

    def setUp(self):
        import tempfile
        self._td = tempfile.TemporaryDirectory()
        self._orig_home = _bridge.PROJECT_REGISTRY_HOME
        self._orig_index = _bridge.PROJECT_REGISTRY_INDEX_FILE
        _bridge.PROJECT_REGISTRY_HOME = pathlib.Path(self._td.name) / "project_registry"
        _bridge.PROJECT_REGISTRY_INDEX_FILE = _bridge.PROJECT_REGISTRY_HOME / "registry.json"
        _bridge.PROJECT_REGISTRY_HOME.mkdir(parents=True, exist_ok=True)
        _bridge.USER_STATE_STORE.clear()
        self._patchers = [
            mock.patch.object(_bridge, "send_telegram_message"),
            mock.patch.object(_bridge, "log_event"),
        ]
        self.send, self.logev = [p.start() for p in self._patchers]

    def tearDown(self):
        for p in self._patchers:
            p.stop()
        _bridge.PROJECT_REGISTRY_HOME = self._orig_home
        _bridge.PROJECT_REGISTRY_INDEX_FILE = self._orig_index
        _bridge.USER_STATE_STORE.clear()
        self._td.cleanup()


CHAT = 1124247595  # ضمن ALLOWED_CHAT_IDS الافتراضية (نمط test_p42)


def _cb_update(data: str, message_id: int = 55) -> dict:
    """تحديث callback_query قياسي من شات مسموح (نمط test_p42 حرفياً)."""
    return {
        "callback_query": {
            "message": {"chat": {"id": CHAT}, "message_id": message_id},
            "from": {"id": CHAT},
            "data": data,
        }
    }


class TestFastModeToggleButton(_IsolatedRegistryMixin, unittest.TestCase):
    KEY = "prj_p43toggle"

    def test_toggle_fastmode_callback_flips_and_persists(self):
        """[5] pset:fastmode يعكس القيمة ويحفظها ويعيد اللوحة بالكيبورد المحدّث."""
        reg = _bridge.ProjectRegistry(self.KEY)
        self.assertIs(reg.get_project_settings()["fast_mode"], False)

        # الضغطة الأولى: False ➔ True + حفظ على القرص
        _bridge.handle_telegram_update(_cb_update(f"pset:fastmode:{self.KEY}"))
        self.assertIs(
            _bridge.ProjectRegistry(self.KEY).get_project_settings()["fast_mode"], True)
        # اللوحة أُعيد إرسالها بالكيبورد المحدّث (زر مفعّل 🔵)
        self.assertTrue(self.send.called)
        args, kwargs = self.send.call_args
        markup = str(kwargs.get("reply_markup") or (args[2] if len(args) > 2 else ""))
        self.assertIn(f"pset:fastmode:{self.KEY}", markup)
        self.assertIn("الوضع السريع: مفعّل", markup)
        # رسالة التفعيل شفافة وتذكر التخطي وأولوية GitHub (D3)
        body = str(args[1]) if len(args) > 1 else str(kwargs.get("text") or "")
        self.assertIn("تم تفعيل الوضع السريع", body)

        # الضغطة الثانية: True ➔ False (Toggle حقيقي لا one-way)
        self.send.reset_mock()
        _bridge.handle_telegram_update(_cb_update(f"pset:fastmode:{self.KEY}"))
        self.assertIs(
            _bridge.ProjectRegistry(self.KEY).get_project_settings()["fast_mode"], False)
        args2, kwargs2 = self.send.call_args
        markup2 = str(kwargs2.get("reply_markup") or (args2[2] if len(args2) > 2 else ""))
        self.assertIn("تنزيل الملفات: مفعّل", markup2)
        # الحالة صُفّرت — لا state معلّقة بعد الضغط
        self.assertNotIn("action", _bridge.get_user_state(CHAT))

    def test_settings_button_uses_primary_style_whitelist(self):
        """[6] D1/F10: الزر بستايل primary ضمن ALLOWED_BUTTON_STYLES وينجو من make_inline_keyboard."""
        self.assertIn("primary", _bridge.ALLOWED_BUTTON_STYLES)
        keyboard = _bridge.build_project_settings_keyboard(self.KEY)
        flat = [b for row in keyboard["inline_keyboard"] for b in row]
        fast_buttons = [b for b in flat
                        if b.get("callback_data") == f"pset:fastmode:{self.KEY}"]
        self.assertEqual(len(fast_buttons), 1)
        btn = fast_buttons[0]
        # style نجا من فلترة make_inline_keyboard لأنه ضمن الـ Whitelist
        self.assertEqual(btn.get("style"), "primary")
        self.assertIn(btn["style"], _bridge.ALLOWED_BUTTON_STYLES)
        # الافتراضي (fast_mode=False) ➔ ليبل التنزيل ⚪📦
        self.assertIn("📦", btn["text"])
        # الحدية 9: حد 64 بايت لـ callback_data
        self.assertLessEqual(len(btn["callback_data"].encode("utf-8")), 64)
        # عند التفعيل ينقلب الليبل لـ 🔵⚡ والزر يبقى primary
        _bridge.ProjectRegistry(self.KEY).update_project_settings({"fast_mode": True})
        keyboard_on = _bridge.build_project_settings_keyboard(self.KEY)
        flat_on = [b for row in keyboard_on["inline_keyboard"] for b in row]
        btn_on = next(b for b in flat_on
                      if b.get("callback_data") == f"pset:fastmode:{self.KEY}")
        self.assertIn("⚡", btn_on["text"])
        self.assertIn("مفعّل", btn_on["text"])
        self.assertEqual(btn_on.get("style"), "primary")


# ═══════════════════════════════════════════════════════════════
# 4) CP4 — حقن التخطي في worker (اختبارات 7–11: Spy وظيفي بلا شبكة)
# ═══════════════════════════════════════════════════════════════
class _FakeEngine:
    """محرك Genspark مزيف: يكمل التوليد فوراً بلا أي شبكة (نمط test_p13)."""

    class Config:
        def __init__(self):
            self.model = ""

    @staticmethod
    def check_balance(cookies):
        return 99999  # رصيد وفير — بوابة P13 تمر

    @staticmethod
    def send_chat(cookies, query, email, **kwargs):
        cb = kwargs.get("on_project_start_callback")
        if cb:
            cb("prj_fake_p43_pid")
        # رد طويل مكتمل ➔ detect_response_status = COMPLETED فوراً (لا polling)
        return "تم بناء الموقع بالكامل بنجاح وكل الصفحات جاهزة للعرض النهائي.", "prj_fake_p43_pid", "asst_1"

    @staticmethod
    def fetch_project_messages(pid, cookies, cfg):
        return []


class _WorkerBypassHarness(unittest.TestCase):
    """تشغيل send_message_and_make_public الحقيقية بمحرك مزيف + Spies شبكية."""

    EMAIL = "p43@test.local"

    def _run_pipeline(self, fast_skip: bool):
        cfg = _bridge.BridgeConfig(model="claude-fable-5")
        cfg.project_fast_lean_skip = fast_skip
        cfg.selection_project_key = "prj_p43worker"
        account = {"email": self.EMAIL, "cookies": {"session_id": "x"},
                   "last_refresh": time.time()}
        spies = {}
        patches = {
            "get_genspark_engine": mock.patch.object(
                _bridge, "get_genspark_engine", return_value=_FakeEngine),
            "read_accounts_safe": mock.patch.object(
                _bridge, "read_accounts_safe", return_value=[account]),
            "update_account_data": mock.patch.object(_bridge, "update_account_data"),
            "get_account_fingerprint": mock.patch.object(
                _bridge, "get_account_fingerprint",
                return_value={"user_agent": "UA", "browser": "chrome120"}),
            "fetch_project_activity_signature": mock.patch.object(
                _bridge, "fetch_project_activity_signature", return_value=None),
            "download": mock.patch.object(
                _bridge, "download_project_archive", return_value="/tmp/fake.tar.gz"),
            "make_public": mock.patch.object(
                _bridge, "make_project_always_public",
                return_value="https://fake.public/url"),
            "save_branch": mock.patch.object(_bridge, "save_project_branch"),
            "log_event": mock.patch.object(_bridge, "log_event"),
        }
        started = {name: p.start() for name, p in patches.items()}
        spies.update(started)
        try:
            result = _bridge.send_message_and_make_public(
                url=None, email=self.EMAIL, password="pw",
                query="ابنِ موقعاً", bridge_cfg=cfg,
            )
        finally:
            for p in patches.values():
                p.stop()
        return result, spies


class TestWorkerFastModeBypass(_WorkerBypassHarness):
    def test_worker_skips_download_when_fast_mode(self):
        """[7] Spy: صفر استدعاء لـ download_project_archive في الوضع السريع."""
        (pub_url, status, ext_dir, resp, err), spies = self._run_pipeline(fast_skip=True)
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(spies["download"].call_count, 0)
        # شجرة الاستئناف tree:* محفوظة دائماً — save_project_branch بلا حراسة
        self.assertEqual(spies["save_branch"].call_count, 1)

    def test_worker_keeps_make_public_in_fast_mode(self):
        """[8] D2: make_project_always_public تعمل في fast mode — الرابط لا يضيع."""
        (pub_url, status, ext_dir, resp, err), spies = self._run_pipeline(fast_skip=True)
        # >= 1: الاستدعاء النهائي مضمون + قد يسبقه خيط P16 الخلفي (early-public)
        self.assertGreaterEqual(spies["make_public"].call_count, 1)
        self.assertEqual(pub_url, "https://fake.public/url")

    def test_worker_downloads_when_fast_mode_off(self):
        """[9] Zero-Regression: fast off ➔ التنزيل + النشر + الشجرة كلها تعمل."""
        (pub_url, status, ext_dir, resp, err), spies = self._run_pipeline(fast_skip=False)
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(spies["download"].call_count, 1)
        self.assertGreaterEqual(spies["make_public"].call_count, 1)
        self.assertEqual(spies["save_branch"].call_count, 1)
        # عقد الإرجاع لم يتغير: 5-tuple والرابط من make_public
        self.assertEqual(pub_url, "https://fake.public/url")

    def test_fast_mode_telemetry_log_line(self):
        """[10] D7: سطر FAST_MODE_SKIP يظهر عند كل تخطٍ — وبغيابه لا يظهر."""
        _, spies_on = self._run_pipeline(fast_skip=True)
        logged = [str(c) for c in spies_on["log_event"].call_args_list]
        self.assertTrue(any("FAST_MODE_SKIP" in line and "prj_p43worker" in line
                            for line in logged),
                        "سطر Telemetry إلزامي عند التخطي (D7)")
        _, spies_off = self._run_pipeline(fast_skip=False)
        logged_off = [str(c) for c in spies_off["log_event"].call_args_list]
        self.assertFalse(any("FAST_MODE_SKIP" in line for line in logged_off),
                         "لا Telemetry تخطٍ في المسار الكامل")

    def test_fast_mode_completion_card_transparent(self):
        """[11] X7: كارت الإكمال يعلن التخطي صراحةً — والحقن مصدرياً بترتيب _declined أولاً."""
        # (أ) نص الإعلان الشفاف موجود ويُبنى شرطياً على project_fast_lean_skip
        self.assertIn("تم تخطي تنزيل الملفات والـ Diff", BRIDGE_SRC)
        card_block = BRIDGE_SRC.split("fast_mode_line = \"\"", 1)[1][:400]
        self.assertIn("project_fast_lean_skip", card_block)
        self.assertIn('status == "COMPLETED"', card_block)
        # (ب) الترتيب الحرفي (الحدية 5): skip_archive = _declined or fast_lean_skip
        self.assertIn("skip_archive = _declined or fast_lean_skip", BRIDGE_SRC)
        # (ج) make_public تُتخطى حصرياً في فرع _declined لا في fast mode (D2)
        m = re.search(
            r"^def send_message_and_make_public\(.*?(?=^def send_message_with_auto_account_failover)",
            BRIDGE_SRC, re.MULTILINE | re.DOTALL)
        body = m.group(0)
        self.assertIn("if _declined:\n            final_public_url", body)
        self.assertNotIn("if skip_archive:\n            final_public_url", body)
        # (د) لا حقل download_artifacts شبح (R1) ولا namespace cmd:toggle_fast_mode (R3)
        self.assertNotIn("download_artifacts", BRIDGE_SRC)
        self.assertNotIn("cmd:toggle_fast_mode", BRIDGE_SRC)


# ═══════════════════════════════════════════════════════════════
# 5) CP6 — خطوة Wizard الوضع السريع (D4 — اختبارات 12–13)
# ═══════════════════════════════════════════════════════════════
class TestWizardFastModeStep(_IsolatedRegistryMixin, unittest.TestCase):
    KEY = "prj_p43wizard"

    def _base_state(self, **extra) -> dict:
        return {
            "project_key": self.KEY,
            "project_name": "مشروع Wizard",
            "project_model": _bridge.DEFAULT_PROJECT_MODEL,
            **extra,
        }

    def test_wizard_fast_step_only_when_github_disabled(self):
        """[12] D4: الخطوة تظهر في فرع GitHub-no فقط — مسار GitHub-yes لا يراها."""
        # (أ) فرع cmd:new_proj_github_no ➔ حالة AWAITING_NEW_PROJECT_FAST_MODE
        _bridge.set_user_state(CHAT, self._base_state(action="AWAITING_NEW_PROJECT_GITHUB_MODE"))
        _bridge.handle_telegram_update(_cb_update("cmd:new_proj_github_no"))
        state = _bridge.get_user_state(CHAT)
        self.assertEqual(state.get("action"), "AWAITING_NEW_PROJECT_FAST_MODE")
        self.assertIs(state.get("pending_fast_mode"), False)
        # الكيبورد المعروض يحمل الزرين والافتراضي 📦 بستايل primary (D1)
        markup = str(self.send.call_args.kwargs.get("reply_markup") or "")
        self.assertIn("cmd:new_proj_fast_no", markup)
        self.assertIn("cmd:new_proj_fast_yes", markup)
        kb = _bridge.build_new_project_fast_mode_keyboard()
        flat = [b for row in kb["inline_keyboard"] for b in row]
        default_btn = next(b for b in flat if b.get("callback_data") == "cmd:new_proj_fast_no")
        self.assertEqual(default_btn.get("style"), "primary")
        # (ب) مسار GitHub-yes (اختيار فرع) ➔ مباشرة RESUME_PROMPT_DECISION بلا خطوة fast
        _bridge.set_user_state(CHAT, self._base_state(
            action="AWAITING_NEW_PROJECT_GITHUB_BRANCH_MODE",
            pending_github_repository="owner/repo",
            pending_github_default_branch="main",
            pending_github_branches=["main"],
        ))
        _bridge.handle_telegram_update(_cb_update("cmd:new_proj_branch_default"))
        gh_state = _bridge.get_user_state(CHAT)
        self.assertEqual(gh_state.get("action"), "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION")
        self.assertNotIn("pending_fast_mode", gh_state)
        # (ج) وحتى لو تسلل pending_fast_mode مع GitHub مفعّل ➔ finalize يفرض False (D3)
        with mock.patch.object(_bridge, "configure_project_github_settings"):
            settings, _ = _bridge.finalize_new_project_from_state(
                self._base_state(pending_fast_mode=True, pending_github_enabled=True,
                                 pending_github_repository="owner/repo"),
                chat_id=CHAT)
        self.assertIs(settings["fast_mode"], False)
        # (د) الضغط خارج الحالة الصحيحة ➔ رسالة إرشاد بلا Mutation (الحدية 8)
        _bridge.set_user_state(CHAT, {})
        _bridge.handle_telegram_update(_cb_update("cmd:new_proj_fast_yes"))
        self.assertNotIn("pending_fast_mode", _bridge.get_user_state(CHAT))

    def test_wizard_fast_selection_sets_flag_and_pending_prompt_survives(self):
        """[13] D4 + الحدية 13: الاختيار يُحفظ والـ pending_prompt ينجو عبر **state."""
        # (أ) اختيار ⚡ مع pending_prompt محفوظ من P42 ➔ ينجوان معاً في الحالة التالية
        _bridge.set_user_state(CHAT, self._base_state(
            action="AWAITING_NEW_PROJECT_FAST_MODE",
            pending_fast_mode=False,
            pending_prompt="ابنِ لي موقعاً كاملاً",
        ))
        _bridge.handle_telegram_update(_cb_update("cmd:new_proj_fast_yes"))
        state = _bridge.get_user_state(CHAT)
        self.assertEqual(state.get("action"), "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION")
        self.assertIs(state.get("pending_fast_mode"), True)
        self.assertEqual(state.get("pending_prompt"), "ابنِ لي موقعاً كاملاً")  # الحارس المخصص
        # (ب) إكمال الـ Wizard (برومبت الاستئناف الافتراضي) ➔ fast_mode=True على القرص
        #     + Smart Forwarding يطلق البرومبت المحفوظ (P42 كما هي)
        with mock.patch.object(_bridge.EXECUTOR, "submit") as submit:
            _bridge.handle_telegram_update(_cb_update("cmd:new_proj_resume_default"))
        saved = _bridge.ProjectRegistry(self.KEY).get_project_settings()
        self.assertIs(saved["fast_mode"], True)
        self.assertEqual(submit.call_count, 1)  # البرومبت انطلق تلقائياً
        self.assertIn("ابنِ لي موقعاً كاملاً", str(submit.call_args))
        # حالة نظيفة بعد الإطلاق (تبقى ts وحدها — طابع set_user_state الداخلي)
        self.assertNotIn("action", _bridge.get_user_state(CHAT))
        self.assertNotIn("pending_prompt", _bridge.get_user_state(CHAT))
        # (ج) اختيار 📦 (الافتراضي) ➔ fast_mode=False على القرص — R2/X8
        key2 = "prj_p43wizard2"
        _bridge.set_user_state(CHAT, self._base_state(
            action="AWAITING_NEW_PROJECT_FAST_MODE", project_key=key2))
        _bridge.handle_telegram_update(_cb_update("cmd:new_proj_fast_no"))
        self.assertIs(_bridge.get_user_state(CHAT).get("pending_fast_mode"), False)
        _bridge.handle_telegram_update(_cb_update("cmd:new_proj_resume_default"))
        self.assertIs(_bridge.ProjectRegistry(key2).get_project_settings()["fast_mode"], False)


# ═══════════════════════════════════════════════════════════════
# 6) CP5 — زر D6 التنزيل المتأخر pctl:fetch (اختبارات 14–15)
# ═══════════════════════════════════════════════════════════════
class TestLateFetchButton(_IsolatedRegistryMixin, unittest.TestCase):
    KEY = "prj_p43fetch"
    PID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # PID بصيغة UUID (is_probable_project_id)

    def _prepare_identity(self):
        _bridge.upsert_project_identity(self.KEY, root_pid=self.PID, latest_pid=self.PID,
                                        project_name="مشروع D6", chat_id=CHAT, status="COMPLETED")

    def test_late_fetch_button_runs_full_pipeline(self):
        """[14] D6: الزر ينفّذ الـ Pipeline الكامل بنفس الدوال القائمة بلا نسخ."""
        # (أ) الزر موجود في كارت المشروع بالـ namespace المحسوم وبحد 64 بايت (الحدية 9)
        keyboard = _bridge.build_current_project_keyboard(self.KEY)
        flat = [b for row in keyboard["inline_keyboard"] for b in row]
        fetch_btn = next(b for b in flat
                         if b.get("callback_data") == f"pctl:fetch:{self.KEY}")
        self.assertIn("تنزيل الساندبوكس", fetch_btn["text"])
        self.assertLessEqual(len(fetch_btn["callback_data"].encode("utf-8")), 64)
        # (ب) الضغطة تستدعي download_project_archive ثم snapshot ثم github_sync
        self._prepare_identity()
        account = {"email": "d6@test.local", "cookies": {"session_id": "x"},
                   "status": "active", "last_refresh": time.time()}
        fake_update = {"checkpoint": "cp_d6_1"}
        with mock.patch.object(_bridge, "read_accounts_safe", return_value=[account]), \
             mock.patch.object(_bridge, "download_project_archive",
                               return_value="/tmp/fake_d6.tar.gz") as dl, \
             mock.patch.object(_bridge.ProjectRegistry, "snapshot",
                               return_value=fake_update) as snap, \
             mock.patch.object(_bridge.ProjectRegistry, "github_sync",
                               return_value={"enabled": False}) as sync:
            _bridge.handle_telegram_update(_cb_update(f"pctl:fetch:{self.KEY}"))
        self.assertEqual(dl.call_count, 1)
        self.assertEqual(dl.call_args.args[0], self.PID)  # نفس الـ PID المحفوظ
        self.assertEqual(snap.call_count, 1)
        self.assertEqual(sync.call_count, 1)
        # رسالة نجاح صريحة بالـ checkpoint
        body = str(self.send.call_args.args[1])
        self.assertIn("تم تنزيل الساندبوكس", body)
        self.assertIn("cp_d6_1", body)

    def test_late_fetch_failure_and_idempotency(self):
        """[15] الحديتان 11–12: فشل صريح بلا Crash + ضغط مزدوج Idempotent."""
        self._prepare_identity()
        account = {"email": "d6@test.local", "cookies": {"session_id": "x"},
                   "status": "active", "last_refresh": time.time()}
        # الحدية 11: جلسة منتهية ➔ download يرجع None ➔ رسالة فشل صريحة، صفر snapshot
        with mock.patch.object(_bridge, "read_accounts_safe", return_value=[account]), \
             mock.patch.object(_bridge, "download_project_archive", return_value=None), \
             mock.patch.object(_bridge.ProjectRegistry, "snapshot") as snap:
            msg_fail = _bridge.run_project_late_fetch(self.KEY)
        self.assertIn("فشل تنزيل الساندبوكس", msg_fail)
        self.assertIn("جلسة", msg_fail)  # السبب المحتمل مذكور صراحةً
        self.assertEqual(snap.call_count, 0)
        # الكارت يبقى صالحاً لإعادة المحاولة: المفتاح خرج من in-flight (finally)
        self.assertNotIn(self.KEY, _bridge.LATE_FETCH_IN_FLIGHT)
        # استثناء داخل download ➔ نفس رسالة الفشل بلا Crash
        with mock.patch.object(_bridge, "read_accounts_safe", return_value=[account]), \
             mock.patch.object(_bridge, "download_project_archive",
                               side_effect=RuntimeError("session expired")):
            msg_exc = _bridge.run_project_late_fetch(self.KEY)
        self.assertIn("فشل تنزيل الساندبوكس", msg_exc)
        self.assertNotIn(self.KEY, _bridge.LATE_FETCH_IN_FLIGHT)
        # الحدية 12: مفتاح داخل in-flight ➔ «جارٍ بالفعل» بلا أي تنزيل جديد
        with _bridge.LATE_FETCH_LOCK:
            _bridge.LATE_FETCH_IN_FLIGHT.add(self.KEY)
        try:
            with mock.patch.object(_bridge, "download_project_archive") as dl_busy:
                msg_busy = _bridge.run_project_late_fetch(self.KEY)
            self.assertIn("جارٍ بالفعل", msg_busy)
            self.assertEqual(dl_busy.call_count, 0)
        finally:
            with _bridge.LATE_FETCH_LOCK:
                _bridge.LATE_FETCH_IN_FLIGHT.discard(self.KEY)
        # لا حسابات جاهزة ➔ رسالة صريحة أيضاً (امتداد الحدية 11)
        with mock.patch.object(_bridge, "read_accounts_safe", return_value=[]):
            msg_noacc = _bridge.run_project_late_fetch(self.KEY)
        self.assertIn("لا يوجد حساب جاهز", msg_noacc)
        # الحدية 14: مشروع fast بلا أرشيف ➔ رسالة «لا أرشيف — الوضع السريع» الموجهة لزر D6
        _bridge.ProjectRegistry(self.KEY).update_project_settings({"fast_mode": True})
        archive_msg = _bridge.render_project_archive_text(self.KEY)
        self.assertIn("الوضع السريع", archive_msg)
        self.assertIn("تنزيل الساندبوكس الآن", archive_msg)
        files_msg = _bridge.render_project_file_report_text(self.KEY)
        self.assertIn("الوضع السريع", files_msg)
        self.assertIn("تنزيل الساندبوكس الآن", files_msg)


# ═══════════════════════════════════════════════════════════════
# 7) CP7 — الاختبار 16: عقود P40/Success/Resume/Rotation/Cancel مجمّدة
# ═══════════════════════════════════════════════════════════════
class _DecliningEngine(_FakeEngine):
    """محرك يرد برفض P35 القصير — لاختبار أسبقية `_declined` (الحدية 5)."""

    @staticmethod
    def send_chat(cookies, query, email, **kwargs):
        cb = kwargs.get("on_project_start_callback")
        if cb:
            cb("prj_fake_p43_pid")
        return "The model declined to answer this request.", "prj_fake_p43_pid", "asst_1"


class TestFrozenContractsUnchanged(_WorkerBypassHarness):
    def _run_decline_pipeline(self, fast_skip: bool):
        """نفس harness الاختبارات 7–10 لكن بمحرك رافض (P40 Fast-Path)."""
        with mock.patch.object(_bridge, "get_genspark_engine", return_value=_DecliningEngine):
            cfg = _bridge.BridgeConfig(model="claude-fable-5")
            cfg.project_fast_lean_skip = fast_skip
            cfg.selection_project_key = "prj_p43frozen"
            account = {"email": self.EMAIL, "cookies": {"session_id": "x"},
                       "last_refresh": time.time()}
            patches = {
                "read_accounts_safe": mock.patch.object(
                    _bridge, "read_accounts_safe", return_value=[account]),
                "update_account_data": mock.patch.object(_bridge, "update_account_data"),
                "get_account_fingerprint": mock.patch.object(
                    _bridge, "get_account_fingerprint",
                    return_value={"user_agent": "UA", "browser": "chrome120"}),
                "fetch_project_activity_signature": mock.patch.object(
                    _bridge, "fetch_project_activity_signature", return_value=None),
                "download": mock.patch.object(
                    _bridge, "download_project_archive", return_value="/tmp/fake.tar.gz"),
                "make_public": mock.patch.object(
                    _bridge, "make_project_always_public",
                    return_value="https://fake.public/url"),
                "save_branch": mock.patch.object(_bridge, "save_project_branch"),
                "log_event": mock.patch.object(_bridge, "log_event"),
            }
            spies = {name: p.start() for name, p in patches.items()}
            try:
                result = _bridge.send_message_and_make_public(
                    url=None, email=self.EMAIL, password="pw",
                    query="ابنِ موقعاً", bridge_cfg=cfg,
                )
            finally:
                for p in patches.values():
                    p.stop()
        return result, spies

    def test_p40_decline_and_frozen_contracts_unchanged(self):
        """[16] عقود P40/Success/Resume/Rotation/Cancel كما هي — الحدية 5."""
        # (أ) رفض P40 + fast mode معاً ⟔ `_declined` يفوز أولاً:
        #     صفر تنزيل + صفر make_public نهائي (الرابط المباشر) + الشجرة محفوظة
        (pub_url, status, ext_dir, resp, err), spies = self._run_decline_pipeline(fast_skip=True)
        self.assertEqual(status, "COMPLETED")  # عقد P40: COMPLETED تقنياً
        self.assertEqual(spies["download"].call_count, 0)
        self.assertEqual(pub_url, "https://www.genspark.ai/autopilotagent_viewer?id=prj_fake_p43_pid")
        self.assertEqual(spies["save_branch"].call_count, 1)  # شجرة tree:* دائماً (P36 رقم 3)
        # سطر P40 التحذيري يظهر — وسطر FAST_MODE_SKIP لا يظهر (الرفض فاز)
        logged = [str(c) for c in spies["log_event"].call_args_list]
        self.assertTrue(any("[P40]" in line and "رفض موديل" in line for line in logged))
        self.assertFalse(any("FAST_MODE_SKIP" in line for line in logged))
        # (ب) رفض P40 بلا fast mode ⟔ نفس السلوك بالبايت (Zero-Regression للرفض)
        (pub2, status2, _, _, _), spies2 = self._run_decline_pipeline(fast_skip=False)
        self.assertEqual(status2, "COMPLETED")
        self.assertEqual(spies2["download"].call_count, 0)
        self.assertEqual(pub2, pub_url)
        # (ج) العقود النصية المجمّدة في السورس حرفياً:
        #     ترتيب OR الصريح + الرابط المباشر داخل فرع `_declined` حصرياً
        self.assertIn("skip_archive = _declined or fast_lean_skip", BRIDGE_SRC)
        self.assertIn("if _declined:\n            final_public_url", BRIDGE_SRC)
        # (د) عقد الإرجاع 5-tuple + مسار TIMEOUT بلا تغيير (الحدية 4)
        self.assertIn('return None, "TIMEOUT", None, None, None', BRIDGE_SRC)
        # (هـ) عقد الاستئناف F13: save_project_branch اُستدعي بالـ PID الفعلي
        #     — الاستئناف يعتمد على URL/PID لا على الملفات (الحدية 6)
        branch_kwargs = spies["save_branch"].call_args.kwargs
        self.assertEqual(branch_kwargs.get("child_id"), "prj_fake_p43_pid")
        self.assertEqual(branch_kwargs.get("status"), "COMPLETED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
