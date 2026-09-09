#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p29_account_observability.py
========================================
🧾 [P29] حراسة ميزة «مراقبة الحسابات الحية ومسار رحلة الحسابات»
(Live Account Observability & Account Journey Chain):

1. Journey: تسجيل لحظة الـ claim الفعلي فقط + منع التكرار المتتالي (A→A تبقى A)
   + عزل كل تشغيل (reset) + السماح بالعودة (A→B→A).
2. Immutable Event Snapshots: كل event يحمل نسخة مستقلة من account_journey
   لا تتغير عند تغيّر الحساب لاحقاً.
3. Live Renderer: سطر «الحساب النشط» من snapshot الحدث فقط (لا Email وهمي)
   + سطر «تبديل الحساب: من X ← إلى Y» عند أول claim بعد handoff.
4. الرسالة النهائية: سطر «مسار الحسابات» يظهر فقط عند تعدد الحسابات الفعلية،
   ويغيب تماماً عند حساب واحد أو journey فارغة (backward compatible).
5. عقود المصدر: نقاط الالتقاط في مواضعها الصحيحة (claim / failover reset / final msg).
"""

import sys
import pathlib
import unittest
import importlib.util

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p29", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)


class _CfgStub:
    """Stub خفيف بدل BridgeConfig لعزل اختبارات الوحدات."""
    def __init__(self):
        self.account_journey = []
        self.selection_project_key = "proj-x"
        self.selection_attempt_number = 0
        self.selected_account_email = ""
        self.selected_account_claim_state = ""
        self.last_credit_continuations = 0
        self.project_resume_prompt_public = _bridge.DEFAULT_PROJECT_RESUME_PROMPT
        self.project_resume_prompt_runtime = _bridge.DEFAULT_PROJECT_RESUME_PROMPT
        self.project_runtime_binding_source = ""
        self.account_selection_observer = None
        self.max_credit_continuations = 10


class TestAccountJourneyRecording(unittest.TestCase):
    """1️⃣ تسجيل مسار الرحلة: ترتيب + dedup متتالي + عزل + عودة."""

    def test_records_in_claim_order(self):
        cfg = _CfgStub()
        _bridge.record_account_journey(cfg, "a@x.com")
        _bridge.record_account_journey(cfg, "b@x.com")
        _bridge.record_account_journey(cfg, "c@x.com")
        self.assertEqual(cfg.account_journey, ["a@x.com", "b@x.com", "c@x.com"])

    def test_consecutive_duplicates_collapse(self):
        cfg = _CfgStub()
        for email in ["a@x.com", "a@x.com", "a@x.com", "b@x.com", "b@x.com"]:
            _bridge.record_account_journey(cfg, email)
        self.assertEqual(cfg.account_journey, ["a@x.com", "b@x.com"])

    def test_return_to_previous_account_is_kept(self):
        cfg = _CfgStub()
        for email in ["a@x.com", "b@x.com", "a@x.com"]:
            _bridge.record_account_journey(cfg, email)
        self.assertEqual(cfg.account_journey, ["a@x.com", "b@x.com", "a@x.com"])

    def test_empty_or_blank_email_never_recorded(self):
        cfg = _CfgStub()
        _bridge.record_account_journey(cfg, "")
        _bridge.record_account_journey(cfg, "   ")
        _bridge.record_account_journey(cfg, None)
        self.assertEqual(cfg.account_journey, [])

    def test_none_cfg_is_safe(self):
        self.assertEqual(_bridge.record_account_journey(None, "a@x.com"), [])

    def test_missing_attribute_initialized_as_list(self):
        class Bare:
            pass
        bare = Bare()
        _bridge.record_account_journey(bare, "a@x.com")
        self.assertEqual(bare.account_journey, ["a@x.com"])

    def test_bridgeconfig_instances_are_isolated(self):
        cfg1 = _bridge.BridgeConfig()
        cfg2 = _bridge.BridgeConfig()
        _bridge.record_account_journey(cfg1, "a@x.com")
        self.assertEqual(cfg1.account_journey, ["a@x.com"])
        self.assertEqual(cfg2.account_journey, [])


class TestImmutableEventSnapshots(unittest.TestCase):
    """2️⃣ العقد الأساسي: snapshot الحدث لا يتغير بعد إنشائه."""

    def _capture_events(self, cfg):
        events = []
        cfg.account_selection_observer = events.append
        return events

    def test_event_carries_journey_snapshot(self):
        cfg = _CfgStub()
        events = self._capture_events(cfg)
        _bridge.record_account_journey(cfg, "a@x.com")
        cfg.selected_account_email = "a@x.com"
        _bridge.notify_account_selection_observer(cfg, "account-claimed", status="CLAIMED")
        self.assertEqual(events[0]["account_journey"], ["a@x.com"])

    def test_old_event_snapshot_never_mutates(self):
        cfg = _CfgStub()
        events = self._capture_events(cfg)
        _bridge.record_account_journey(cfg, "a@x.com")
        cfg.selected_account_email = "a@x.com"
        _bridge.notify_account_selection_observer(cfg, "account-claimed", status="CLAIMED")
        first_snapshot = events[0]["account_journey"]
        # يتغير الحساب لاحقاً — الحدث القديم يجب أن يبقى كما هو
        _bridge.record_account_journey(cfg, "b@x.com")
        cfg.selected_account_email = "b@x.com"
        _bridge.notify_account_selection_observer(cfg, "account-claimed", status="CLAIMED")
        self.assertEqual(first_snapshot, ["a@x.com"])
        self.assertEqual(events[0]["selected_account_email"], "a@x.com")
        self.assertEqual(events[1]["account_journey"], ["a@x.com", "b@x.com"])
        self.assertIsNot(events[0]["account_journey"], cfg.account_journey)
        self.assertIsNot(events[1]["account_journey"], cfg.account_journey)

    def test_event_without_cfg_has_empty_journey(self):
        # notify مع bridge_cfg=None لا ينهار ولا يخترع journey
        result = _bridge.notify_account_selection_observer(None, "account-claimed")
        self.assertFalse(result)


class TestLiveRendererActiveAccount(unittest.TestCase):
    """3️⃣ سطر الحساب النشط وسطر تبديل الحساب في الرسالة الحية."""

    def _renderer(self):
        return _bridge.AccountSelectionLiveRenderer(project_key="proj-x", project_name="مشروعي")

    def _event(self, event_type, email="", attempt=1, **extra):
        base = {
            "event": event_type,
            "project_key": "proj-x",
            "attempt_number": attempt,
            "selected_account_email": email,
            "selected_account_claim_state": "claimed" if email else "",
            "credit_continuations": 0,
            "max_credit_continuations": 10,
            "account_journey": [],
        }
        base.update(extra)
        return base

    def test_active_account_line_appears_after_claim(self):
        renderer = self._renderer()
        text = renderer.apply(self._event("account-claimed", email="a@x.com", status="CLAIMED"))
        self.assertIn("الحساب النشط", text)
        self.assertIn("a@x.com", text)

    def test_no_active_line_before_any_claim(self):
        renderer = self._renderer()
        text = renderer.apply(self._event("no-eligible-accounts", email="", attempt=0))
        self.assertNotIn("الحساب النشط", text)

    def test_active_account_updates_on_new_claim(self):
        renderer = self._renderer()
        renderer.apply(self._event("account-claimed", email="a@x.com", status="CLAIMED"))
        text = renderer.apply(self._event("account-claimed", email="b@x.com", attempt=2, status="CLAIMED"))
        self.assertIn("📧 <b>الحساب النشط:</b> <code>b@x.com</code>", text)

    def test_handoff_then_claim_produces_switch_line(self):
        renderer = self._renderer()
        renderer.apply(self._event("account-claimed", email="a@x.com", status="CLAIMED"))
        renderer.apply(self._event(
            "continuation-handoff-ready", email="a@x.com", status="CREDIT_EXHAUSTED",
            continuation_url="https://www.genspark.ai/autopilotagent_viewer?id=p1",
            checkpoint_id="cp-1",
        ))
        text = renderer.apply(self._event("account-claimed", email="b@x.com", attempt=2, status="CLAIMED"))
        self.assertIn("تبديل الحساب", text)
        self.assertIn("من <code>a@x.com</code> ← إلى <code>b@x.com</code>", text)

    def test_no_switch_line_without_handoff(self):
        renderer = self._renderer()
        renderer.apply(self._event("account-claimed", email="a@x.com", status="CLAIMED"))
        text = renderer.apply(self._event("account-claimed", email="b@x.com", attempt=2, status="CLAIMED"))
        self.assertNotIn("تبديل الحساب", text)

    def test_handoff_then_same_account_no_switch_line(self):
        renderer = self._renderer()
        renderer.apply(self._event("account-claimed", email="a@x.com", status="CLAIMED"))
        renderer.apply(self._event("continuation-handoff-ready", email="a@x.com", status="CREDIT_EXHAUSTED"))
        text = renderer.apply(self._event("account-claimed", email="a@x.com", attempt=2, status="CLAIMED"))
        self.assertNotIn("تبديل الحساب", text)

    def test_renderer_email_html_escaped(self):
        renderer = self._renderer()
        text = renderer.apply(self._event("account-claimed", email="a<b>@x.com", status="CLAIMED"))
        self.assertIn("a&lt;b&gt;@x.com", text)
        self.assertNotIn("a<b>@x.com", text)


class TestFinalJourneyLine(unittest.TestCase):
    """4️⃣ سطر مسار الحسابات في الرسالة النهائية — يظهر فقط عند تعدد الحسابات."""

    def test_empty_journey_gives_empty_line(self):
        self.assertEqual(_bridge.format_account_journey_line([]), "")
        self.assertEqual(_bridge.format_account_journey_line(None), "")

    def test_single_account_gives_empty_line(self):
        # حساب واحد = لا سطر إضافي (backward compatible مع الرسالة القديمة)
        self.assertEqual(_bridge.format_account_journey_line(["a@x.com"]), "")

    def test_multi_account_journey_rendered_with_arrows(self):
        line = _bridge.format_account_journey_line(["a@x.com", "b@x.com", "c@x.com"])
        self.assertIn("مسار الحسابات", line)
        self.assertIn("<code>a@x.com</code> ← <code>b@x.com</code> ← <code>c@x.com</code>", line)

    def test_blank_entries_filtered_before_count(self):
        self.assertEqual(_bridge.format_account_journey_line(["", "a@x.com", "  "]), "")
        line = _bridge.format_account_journey_line(["a@x.com", "", "b@x.com"])
        self.assertIn("a@x.com", line)
        self.assertIn("b@x.com", line)

    def test_journey_emails_html_escaped(self):
        line = _bridge.format_account_journey_line(["a<b>@x.com", "c@x.com"])
        self.assertIn("a&lt;b&gt;@x.com", line)
        self.assertNotIn("a<b>@x.com", line)


class TestSourceContracts(unittest.TestCase):
    """5️⃣ عقود المصدر: نقاط الالتقاط في مواضعها الصحيحة."""

    def test_journey_recorded_at_claim_moment(self):
        # التسجيل يتم مباشرة بعد تثبيت selected_account_claim_state = "claimed"
        anchor = BRIDGE_SRC.find('bridge_cfg.selected_account_claim_state = "claimed"')
        self.assertGreater(anchor, -1)
        window = BRIDGE_SRC[anchor:anchor + 300]
        self.assertIn("record_account_journey(bridge_cfg, curr_email)", window)

    def test_journey_reset_at_failover_start(self):
        self.assertIn("bridge_cfg.account_journey = []", BRIDGE_SRC)

    def test_event_snapshot_contract_in_notify(self):
        anchor = BRIDGE_SRC.find("def notify_account_selection_observer")
        window = BRIDGE_SRC[anchor:anchor + 3000]
        self.assertIn('"account_journey"', window)

    def test_final_message_uses_journey_block(self):
        # 🧹 [P39] عقد الحقن أُلغي: journey_block حُذف من بطاقة الاكتمال (القائمة
        # الرأسية المفلترة تغني عنه) — لكن دالة P29 نفسها باقية للاستخدام المستقبلي.
        self.assertIn("def format_account_journey_line(journey)", BRIDGE_SRC)
        self.assertNotIn("</code>{journey_block}", BRIDGE_SRC)

    def test_bridgeconfig_declares_journey_with_default_factory(self):
        self.assertIn("account_journey: list = field(default_factory=list)", BRIDGE_SRC)

    def test_start_message_has_no_email_line(self):
        # قاعدة «لا Email وهمي»: رسالة البدء لا تحتوي على حساب لأن الاختيار لم يحدث بعد
        anchor = BRIDGE_SRC.find("جاري بدء المعالجة والتوليد")
        self.assertGreater(anchor, -1)
        start_line = BRIDGE_SRC[BRIDGE_SRC.rfind("\n", 0, anchor):BRIDGE_SRC.find("\n", anchor + 200)]
        self.assertNotIn("الحساب", start_line)


if __name__ == "__main__":
    unittest.main()
