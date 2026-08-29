#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p44_resume_pipeline_integrity.py
============================================
🚪 [P44] حراسة المرحلة 44 — Resume Pipeline Integrity
(وثيقة `18_COT_CLEANUP_AND_DYNAMIC_RESUME_PROMPT.MD` — DEC-040 — Router 18.03).

العلة المعالجة (B1): COMPLETED مبكر كاذب — الموديل «بيفكر» والنص >25 حرفاً
فيُعتمد رد وسطي. الحل: Activity Gate تغليفاً (D5/D6/D9) + بصمة استقرار
الرد (D7) + جلبة نهائية بعد وقف P18 (D8) — البوابة تمنع فقط COMPLETED
المبكر والإشارات المهيكلة تخترقها فوراً، وسقف session_timeout فوق الكل (D12).

العلة المعالجة (B2): برومبت الاستئناف يتجمد على Snapshot₀ لحظة بدء المهمة —
تعديل المستخدم أثناء الجلسة لا يصل. الحل: Live Rebind في فرع CREDIT_EXHAUSTED
قبل الإشعار وقبل active_query (D1/D2/D4) مع استثناء P20 الصريح (D3) —
«اللي يظهر = اللي يتبعت» وFail-Open بالصورة القديمة عند أي فشل.

المصفوفة (12 اختباراً — 18.03 §E حرفياً، Mocks/Spies بلا شبكة حقيقية):
 01 gate_holds_running_while_active        07 final_fetch_failure_keeps_old_text
 02 gate_releases_after_two_inactive_reads 08 live_rebind_picks_edited_prompt
 03 structured_signals_pierce_gate         09 rebind_failure_falls_back_to_snapshot
 04 gate_neutral_on_network_none           10 p20_data_retention_no_rebind
 05 unstable_reply_holds                   11 display_cards_match_sent_prompt
 06 final_fetch_after_p18_stop             12 zero_regression_p35_p40_p18
"""

import importlib.util
import pathlib
import re
import sys
import tempfile
import textwrap
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIDGE_PATH = ROOT / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_p44", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("bridge_p44", _bridge)
_spec.loader.exec_module(_bridge)

# رد وسطي طويل (>25 حرفاً) — قبل P44 كان يُعتمد COMPLETED كاذباً رغم أن
# الموديل ما زال يعمل (Deep Thinking active) — جوهر العلة B1.
LONG_INTERMEDIATE_REPLY = (
    "تم إنشاء الهيكل الأساسي للمشروع وجاري الآن استكمال بقية الملفات "
    "والاختبارات المطلوبة وفق الخطة المعتمدة خطوة بخطوة."
)


def _extract_rebind_snippet() -> str:
    """يستخرج مقطع الـ Live Rebind الحرفي (try/apply → OK / except → FALLBACK)
    من فرع CREDIT_EXHAUSTED في الملف نفسه — الاختبار ينفذ كود الإنتاج ذاته
    لا نسخة منه (مقاوم لإزاحة الأسطر: التقاط بالمراسي النصية لا بالأرقام)."""
    lines = BRIDGE_SRC.splitlines(keepends=True)
    fb = next(i for i, l in enumerate(lines) if "LIVE_REBIND_FALLBACK" in l)
    start = max(i for i in range(fb) if lines[i].strip() == "try:")
    assert "apply_project_runtime_binding(" in lines[start + 1], (
        "try: الملتقط لا يسبق apply_project_runtime_binding مباشرة")
    # نهاية بلوك except: أول سطر إغلاق ")" بعد سطر الـ FALLBACK (يغلق log_event)
    end = next(i for i in range(fb + 1, fb + 6) if lines[i].strip() == ")")
    return textwrap.dedent("".join(lines[start:end + 1]))


def _extract_p20_skip_snippet() -> str:
    """يستخرج مقطع استثناء P20 الحرفي (LIVE_REBIND_SKIPPED_P20 ثم continue)
    من فرع DATA_RETENTION — يُغلَّف بحلقة صورية ليصح continue خارج سياقه."""
    m = re.search(
        r"( +log_event\(\n +\"info\",\n +f\"🔄 \[P44\] LIVE_REBIND_SKIPPED_P20"
        r"(?:.*\n)*? +continue\n)",
        BRIDGE_SRC,
    )
    assert m, "مقطع LIVE_REBIND_SKIPPED_P20 غير موجود في فرع DATA_RETENTION"
    body = textwrap.indent(textwrap.dedent(m.group(1)), "    ")
    return "for _p44_once in (0,):\n" + body


class _TempRegistryMixin:
    """عزل Registry في مجلد مؤقت — نفس نمط P43 حرفياً (صفر لمس للبيئة)."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self._orig_home = _bridge.PROJECT_REGISTRY_HOME
        self._orig_index = _bridge.PROJECT_REGISTRY_INDEX_FILE
        _bridge.PROJECT_REGISTRY_HOME = pathlib.Path(self._td.name) / "project_registry"
        _bridge.PROJECT_REGISTRY_INDEX_FILE = _bridge.PROJECT_REGISTRY_HOME / "registry.json"
        _bridge.PROJECT_REGISTRY_HOME.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        _bridge.PROJECT_REGISTRY_HOME = self._orig_home
        _bridge.PROJECT_REGISTRY_INDEX_FILE = self._orig_index
        self._td.cleanup()


class TestP44ResumePipelineIntegrity(_TempRegistryMixin, unittest.TestCase):
    # ═══════════════════════════════════════════════════════════
    # B1 — Activity Gate (D5/D6/D9)
    # ═══════════════════════════════════════════════════════════
    def test_01_gate_holds_running_while_active(self):
        """[01] D5: نص >25 حرفاً (COMPLETED خام) + مؤشر النشاط active → RUNNING."""
        raw = _bridge.detect_response_status(LONG_INTERMEDIATE_REPLY)
        self.assertEqual(raw, "COMPLETED")  # العلة: الخام يعتمد الرد الوسطي
        with mock.patch.object(_bridge, "log_event") as spy:
            gated = _bridge.detect_response_status_gated(
                raw, {"active": True}, inactive_streak=5, stable_streak=5)
        self.assertEqual(gated, "RUNNING")
        logged = [str(c) for c in spy.call_args_list]
        self.assertTrue(any("ACTIVITY_GATE_HOLD" in l and "indicator-active" in l
                            for l in logged), "Telemetry D11: HOLD indicator-active مفقود")

    def test_02_gate_releases_after_two_inactive_reads(self):
        """[02] D6 debounce: قراءة خمول واحدة لا تكفي — الثانية تفتح البوابة."""
        with mock.patch.object(_bridge, "log_event") as spy:
            first = _bridge.detect_response_status_gated(
                "COMPLETED", {"active": False}, inactive_streak=1, stable_streak=2)
            second = _bridge.detect_response_status_gated(
                "COMPLETED", {"active": False}, inactive_streak=2, stable_streak=2)
        self.assertEqual(first, "RUNNING")
        self.assertEqual(second, "COMPLETED")
        logged = [str(c) for c in spy.call_args_list]
        self.assertTrue(any("ACTIVITY_GATE_HOLD" in l and "debounce" in l for l in logged))
        self.assertTrue(any("ACTIVITY_GATE_RELEASE" in l for l in logged))
        # الثابت المعلن نفسه = 2 (18.03 §D6) — لا قيمة سحرية منفصلة في البوابة
        self.assertEqual(_bridge.P44_GATE_INACTIVE_READS_REQUIRED, 2)

    def test_03_structured_signals_pierce_gate(self):
        """[03] §3.3: المهيكلة الأربع تخترق البوابة فوراً رغم active — صفر تأخير."""
        for status in ("CREDIT_EXHAUSTED", "DATA_RETENTION", "SESSION_EXPIRED", "FORBIDDEN"):
            with mock.patch.object(_bridge, "log_event"):
                gated = _bridge.detect_response_status_gated(
                    status, {"active": True}, inactive_streak=0, stable_streak=0)
            self.assertEqual(gated, status, f"{status} يجب أن يخترق فوراً")
        self.assertEqual(
            set(_bridge.P44_STRUCTURED_STATUSES),
            {"CREDIT_EXHAUSTED", "DATA_RETENTION", "SESSION_EXPIRED", "FORBIDDEN"})
        # غير-COMPLETED غير المهيكلة (RUNNING/EMPTY) تمر كما هي أيضاً
        with mock.patch.object(_bridge, "log_event"):
            self.assertEqual(_bridge.detect_response_status_gated(
                "RUNNING", {"active": True}, 0, 0), "RUNNING")
            self.assertEqual(_bridge.detect_response_status_gated(
                "EMPTY", {"active": False}, 9, 9), "EMPTY")

    def test_04_gate_neutral_on_network_none(self):
        """[04] D6 Fail-Open: activity=None (فشل شبكة P18) → سلوك اليوم حرفياً."""
        with mock.patch.object(_bridge, "log_event") as spy:
            gated = _bridge.detect_response_status_gated(
                "COMPLETED", None, inactive_streak=0, stable_streak=0)
        self.assertEqual(gated, "COMPLETED")  # البوابة محايدة تماماً — صفر إمساك
        logged = [str(c) for c in spy.call_args_list]
        self.assertFalse(any("ACTIVITY_GATE" in l or "REPLY_UNSTABLE" in l
                             for l in logged), "None يجب ألا يُنتج أي Telemetry بوابة")

    # ═══════════════════════════════════════════════════════════
    # B1 — Reply Stability + Final Fetch (D7/D8)
    # ═══════════════════════════════════════════════════════════
    def test_05_unstable_reply_holds(self):
        """[05] D7/D8: محتوى متغير بين قراءتين (stable_streak=1) → RUNNING."""
        with mock.patch.object(_bridge, "log_event") as spy:
            held = _bridge.detect_response_status_gated(
                "COMPLETED", {"active": False}, inactive_streak=2, stable_streak=1)
            released = _bridge.detect_response_status_gated(
                "COMPLETED", {"active": False}, inactive_streak=2, stable_streak=2)
            neutral = _bridge.detect_response_status_gated(
                "COMPLETED", {"active": False}, inactive_streak=2, stable_streak=None)
        self.assertEqual(held, "RUNNING")
        self.assertEqual(released, "COMPLETED")
        self.assertEqual(neutral, "COMPLETED")  # None = غير مقاس (محايد)
        logged = [str(c) for c in spy.call_args_list]
        self.assertTrue(any("REPLY_UNSTABLE_HOLD" in l for l in logged))
        # البصمة نفسها (len+sha256) تكشف تغيّر المحتوى حتى مع ثبات الطول
        fp_a = _bridge.compute_reply_fingerprint("نص أول 1234")
        fp_b = _bridge.compute_reply_fingerprint("نص ثانٍ 1234")
        self.assertEqual(fp_a, _bridge.compute_reply_fingerprint("نص أول 1234"))
        self.assertNotEqual(fp_a, fp_b)
        self.assertEqual(_bridge.compute_reply_fingerprint(None)[0], 0)  # None-safe

    def test_06_final_fetch_after_p18_stop(self):
        """[06] D8: وقف P18 يكسر الحلقة قبل قراءة الرسائل — الجلبة النهائية
        تعتمد آخر رسالة assistant حقيقية بدل النص الوسطي القديم."""
        final_text = "الرد الختامي الكامل بعد اكتمال كل المهام المطلوبة فعلياً."
        mod = types.SimpleNamespace(fetch_project_messages=mock.Mock(return_value=[
            {"role": "user", "content": "برومبت المستخدم"},
            {"role": "assistant", "content": LONG_INTERMEDIATE_REPLY},
            {"role": "assistant", "content": final_text},
            {"role": "user", "content": "تابع"},  # آخر عنصر user — عقد P12-E محفوظ
        ]))
        with mock.patch.object(_bridge, "log_event") as spy:
            got = _bridge.fetch_final_reply_text(
                mod, "pid-p44", {}, None, LONG_INTERMEDIATE_REPLY, email="t@t")
        self.assertEqual(got, final_text)  # الختامية لا الوسطية — وآخر assistant تحديداً
        mod.fetch_project_messages.assert_called_once()  # طلب واحد أخير فقط
        logged = [str(c) for c in spy.call_args_list]
        self.assertTrue(any("FINAL_FETCH_OK" in l for l in logged))

    def test_07_final_fetch_failure_keeps_old_text(self):
        """[07] D8 Fail-Open: فشل الجلبة بأي صورة → النص القديم كما هو + Telemetry."""
        old = "النص القديم المحفوظ من البث — يجب ألا يُمس عند أي فشل."
        cases = {
            "network-error": types.SimpleNamespace(
                fetch_project_messages=mock.Mock(side_effect=RuntimeError("net down"))),
            "no-messages": types.SimpleNamespace(
                fetch_project_messages=mock.Mock(return_value=[])),
            "empty-content": types.SimpleNamespace(
                fetch_project_messages=mock.Mock(return_value=[
                    {"role": "assistant", "content": "   "}])),
            "engine-without-fetch": types.SimpleNamespace(),
        }
        for name, mod in cases.items():
            with mock.patch.object(_bridge, "log_event") as spy:
                got = _bridge.fetch_final_reply_text(mod, "pid", {}, None, old, email="t@t")
            self.assertEqual(got, old, f"حالة {name}: النص القديم يجب أن يبقى")
            logged = [str(c) for c in spy.call_args_list]
            self.assertTrue(any("FINAL_FETCH_FALLBACK" in l for l in logged),
                            f"حالة {name}: Telemetry الفشل مفقودة")

    # ═══════════════════════════════════════════════════════════
    # B2 — Live Rebind (D1/D2/D3/D4)
    # ═══════════════════════════════════════════════════════════
    def test_08_live_rebind_picks_edited_prompt(self):
        """[08] D1: تعديل برومبت الاستئناف وسط الجلسة → أول استئناف بعد التعديل
        يلتقط الجديد — عبر تنفيذ مقطع الـ rebind الحرفي من الملف نفسه."""
        reg = _bridge.ProjectRegistry("prj_p44rebind")
        reg.update_project_settings({"continuation": {"prompt": "برومبت الجلسة الأصلي Snapshot0"}})
        cfg = types.SimpleNamespace(model="claude-fable-5", selection_project_key="prj_p44rebind")
        # Snapshot₀ لحظة بدء المهمة (المسار القائم نفسه)
        _bridge.apply_project_runtime_binding(cfg, "prj_p44rebind", requested_model=cfg.model)
        self.assertEqual(_bridge.get_bridge_cfg_runtime_resume_prompt(cfg),
                         "برومبت الجلسة الأصلي Snapshot0")
        # المستخدم يعدّل وسط الجلسة — قبل الـ rebind القيمة مجمدة على القديم
        reg.update_project_settings({"continuation": {"prompt": "أكمل من نقطة التوقف بالخطة الجديدة"}})
        self.assertEqual(_bridge.get_bridge_cfg_runtime_resume_prompt(cfg),
                         "برومبت الجلسة الأصلي Snapshot0")
        # تنفيذ مقطع فرع CREDIT_EXHAUSTED الحرفي (try/apply → LIVE_REBIND_OK)
        spy = mock.Mock()
        exec(compile(_extract_rebind_snippet(), str(BRIDGE_PATH), "exec"), {
            "apply_project_runtime_binding": _bridge.apply_project_runtime_binding,
            "log_event": spy, "bridge_cfg": cfg, "curr_email": "t@t",
            "DEFAULT_PROJECT_MODEL": _bridge.DEFAULT_PROJECT_MODEL, "getattr": getattr,
        })
        self.assertEqual(_bridge.get_bridge_cfg_runtime_resume_prompt(cfg),
                         "أكمل من نقطة التوقف بالخطة الجديدة")
        logged = [str(c) for c in spy.call_args_list]
        self.assertTrue(any("LIVE_REBIND_OK" in l and "prj_p44rebind" in l for l in logged))

    def test_09_rebind_failure_falls_back_to_snapshot(self):
        """[09] D2 Fail-Open: فشل الـ rebind (manifest تالف/استثناء) → الصورة
        القديمة Snapshot₀ بصفر كسر + LIVE_REBIND_FALLBACK."""
        cfg = types.SimpleNamespace(
            model="claude-fable-5", selection_project_key="prj_p44broken",
            project_resume_prompt_public="صورة قديمة سليمة",
            project_resume_prompt_runtime="صورة قديمة سليمة",
        )
        spy = mock.Mock()
        broken_apply = mock.Mock(side_effect=RuntimeError("manifest تالف"))
        # المقطع الحرفي نفسه — apply يرمي والاستثناء يُلتقط داخله (لا ينفجر)
        exec(compile(_extract_rebind_snippet(), str(BRIDGE_PATH), "exec"), {
            "apply_project_runtime_binding": broken_apply,
            "log_event": spy, "bridge_cfg": cfg, "curr_email": "t@t",
            "DEFAULT_PROJECT_MODEL": _bridge.DEFAULT_PROJECT_MODEL, "getattr": getattr,
        })
        self.assertEqual(_bridge.get_bridge_cfg_runtime_resume_prompt(cfg), "صورة قديمة سليمة")
        self.assertEqual(cfg.project_resume_prompt_public, "صورة قديمة سليمة")
        logged = [str(c) for c in spy.call_args_list]
        self.assertTrue(any("LIVE_REBIND_FALLBACK" in l for l in logged))
        self.assertFalse(any("LIVE_REBIND_OK" in l for l in logged))

    def test_10_p20_data_retention_no_rebind(self):
        """[10] D3: فرع DATA_RETENTION بلا أي rebind (عقد P20 «نفس آخر رسالة») —
        بنيوياً وسلوكياً: SKIPPED_P20 ثم continue قبل بناء active_query."""
        # بنيوياً: بين دخول الفرع وأول continue — صفر استدعاء rebind وصفر active_query
        branch = re.search(
            r'if status == "DATA_RETENTION":\n(?:.*\n)*?\s+continue\n', BRIDGE_SRC)
        self.assertIsNotNone(branch, "فرع DATA_RETENTION غير موجود")
        self.assertNotIn("apply_project_runtime_binding", branch.group(0))
        self.assertNotIn("active_query =", branch.group(0))
        self.assertIn("LIVE_REBIND_SKIPPED_P20", branch.group(0))
        # سلوكياً: تنفيذ المقطع الحرفي — SKIPPED يُسجَّل وapply لا يُستدعى إطلاقاً
        cfg = types.SimpleNamespace(selection_project_key="prj_p44p20")
        spy, apply_spy = mock.Mock(), mock.Mock()
        exec(compile(_extract_p20_skip_snippet(), str(BRIDGE_PATH), "exec"), {
            "log_event": spy, "bridge_cfg": cfg, "curr_email": "t@t",
            "apply_project_runtime_binding": apply_spy, "getattr": getattr,
        })
        logged = [str(c) for c in spy.call_args_list]
        self.assertTrue(any("LIVE_REBIND_SKIPPED_P20" in l and "prj_p44p20" in l
                            for l in logged))
        apply_spy.assert_not_called()

    def test_11_display_cards_match_sent_prompt(self):
        """[11] D4 Display Parity: كارت الـ handoff يقرأ نفس القيمة الحية التي
        ستُبنى منها active_query — «اللي يظهر = اللي يتبعت» + ترتيب المصدر:
        rebind → notify(continuation-handoff-ready) → active_query."""
        # بنيوياً: الترتيب داخل فرع CREDIT_EXHAUSTED (موقع الاستدعاء الفعلي —
        # لا أول ظهور نصي: قاموس عناوين الأحداث يذكر الاسم قبل الاستدعاء بكثير)
        call = re.search(
            r'notify_account_selection_observer\(\s*\n\s*bridge_cfg,\s*\n'
            r'\s*"continuation-handoff-ready",', BRIDGE_SRC)
        self.assertIsNotNone(call, "استدعاء notify(continuation-handoff-ready) غير موجود")
        i_notify = call.start()
        i_rebind = BRIDGE_SRC.rfind("apply_project_runtime_binding(", 0, i_notify)
        i_query = BRIDGE_SRC.find(
            "active_query = get_bridge_cfg_runtime_resume_prompt(", i_notify)
        self.assertTrue(0 <= i_rebind < i_notify < i_query,
                        "الترتيب المطلوب: rebind ثم notify ثم active_query")
        # الـ rebind الملاصق فعلاً لمسار الـ handoff (نفس الفرع لا استدعاء بعيد)
        self.assertLess(i_notify - i_rebind, 2500, "rebind بعيد عن notify — ليس نفس الفرع")
        self.assertIn("LIVE_REBIND_OK", BRIDGE_SRC[i_rebind:i_notify])
        # سلوكياً: الكارت (observer event) = عرض نفس البرومبت المعتمد للإرسال
        reg = _bridge.ProjectRegistry("prj_p44card")
        reg.update_project_settings({"continuation": {"prompt": "برومبت معدل يظهر ويتبعت"}})
        captured = []
        cfg = types.SimpleNamespace(
            model="claude-fable-5", selection_project_key="prj_p44card",
            account_selection_observer=captured.append)
        _bridge.apply_project_runtime_binding(cfg, "prj_p44card", requested_model=cfg.model)
        with mock.patch.object(_bridge, "log_event"):
            self.assertTrue(_bridge.notify_account_selection_observer(
                cfg, "continuation-handoff-ready", status="CREDIT_EXHAUSTED"))
        shown = captured[0]["continuation_prompt_public"]
        sent = _bridge.get_bridge_cfg_runtime_resume_prompt(cfg)
        self.assertEqual(shown, _bridge.summarize_resume_prompt_for_display(sent))
        self.assertEqual(sent, "برومبت معدل يظهر ويتبعت")

    # ═══════════════════════════════════════════════════════════
    # Zero-Regression (G3/R4/D9/D10)
    # ═══════════════════════════════════════════════════════════
    def test_12_zero_regression_p35_p40_p18(self):
        """[12] R4/D9/D10: جسم detect_response_status لم يُمس (تغليف فقط) +
        عقود P35 (كشف الرفض) وP40 (fast-path يقرأ الكشف نفسه) وP18
        (should_stop_on_activity_change) بلا أي تغيير سلوكي."""
        # R4: دالة الكشف الخام معرفة مرة واحدة والبوابة دالة منفصلة تستدعيها لا تعدلها
        self.assertEqual(BRIDGE_SRC.count("def detect_response_status(response"), 1)
        self.assertEqual(BRIDGE_SRC.count("def detect_response_status_gated("), 1)
        # سلوك الخام كما هو: قصير بعلامة توليد → RUNNING / طويل → COMPLETED / فارغ → EMPTY
        self.assertEqual(_bridge.detect_response_status("thinking..."), "RUNNING")
        self.assertEqual(_bridge.detect_response_status(LONG_INTERMEDIATE_REPLY), "COMPLETED")
        self.assertEqual(_bridge.detect_response_status(""), "EMPTY")
        self.assertEqual(_bridge.detect_response_status(
            "your credit balance is negative"), "CREDIT_EXHAUSTED")
        self.assertEqual(_bridge.detect_response_status(
            "requires ai data retention"), "DATA_RETENTION")
        # P35: كشف الرفض القصير كما هو — والبوابة لا تغيّر مدخلاته
        self.assertTrue(_bridge.is_model_decline_response(
            "The model declined to answer this request."))
        self.assertFalse(_bridge.is_model_decline_response(LONG_INTERMEDIATE_REPLY))
        # P40: الـ fast-path ما زال يقرأ نفس الكشف (COMPLETED + is_model_decline_response)
        self.assertIn('_declined = final_status == "COMPLETED" '
                      'and is_model_decline_response(last_resp_text)', BRIDGE_SRC)
        # P18: عقد الوقف الفوري حرفياً — اختفاء المؤشر/تغير المهام/تقلب Deep Thinking
        stop, why = _bridge.should_stop_on_activity_change(
            {"active": True, "tasks_remaining": 3}, {"active": False})
        self.assertEqual((stop, why), (True, "activity-indicator-disappeared"))
        stop, why = _bridge.should_stop_on_activity_change(
            {"active": True, "tasks_remaining": 3},
            {"active": True, "tasks_remaining": 2})
        self.assertEqual((stop, why), (True, "tasks-remaining-changed"))
        self.assertEqual(_bridge.should_stop_on_activity_change(None, {"active": True}),
                         (False, ""))
        # D12: سقف session_timeout القائم ما زال قبل البوابة في الحلقة (شبكة أمان)
        loop_seg = BRIDGE_SRC[BRIDGE_SRC.find("polled_any = final_status"):
                              BRIDGE_SRC.find("if polled_any and final_status")]
        self.assertLess(loop_seg.find("elapsed > session_timeout"),
                        loop_seg.find("detect_response_status_gated("))
        # D8: الجلبة النهائية محروسة بـ polled_any وCOMPLETED فقط (صفر شبكة للبث المكتمل)
        self.assertIn('if polled_any and final_status == "COMPLETED":', BRIDGE_SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
