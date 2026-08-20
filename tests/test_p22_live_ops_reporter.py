#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p22_live_ops_reporter.py
===================================
📡 [P22] حراسة مراسل العمليات الحية (LiveOpsReporter):

العقد — شفافية الباك-إند الكاملة:
1. حقل `live_ops_reporter` موجود في BridgeConfig (افتراضي None).
2. `format_elapsed_seconds` ينسق الزمن بالعربي «X.X ثانية».
3. `LiveOpsReporter.stage` يرقم المراحل تسلسلياً ويرجع دالة إغلاق موقوتة.
4. `event` يضيف للـ timeline ويطبع للترمنال (log_event) دائماً.
5. `push_telegram` يحترم الـ throttle (TELEGRAM_EDIT_MIN_INTERVAL) —
   أول نداء sendMessage ثم editMessageText فقط.
6. تعطيل تليجرام (enable_telegram=False أو chat_id=None) = صفر نداءات شبكة.
7. `finish` يطبع الصندوق الختامي + سطر «⏱️ اخد X ثانية» + آخر تحديث للرسالة
   الحية force — و idempotent (نداء ثانٍ لا يكرر).
8. `get_live_ops_reporter` / `attach_live_ops_reporter` آمنتان و idempotent.
9. الربط داخل process_user_task_async: attach بعد transport + stage حول
   الـ failover + finish في finally — كله معزول بـ try/except (لا يكسر المهمة).
10. render_telegram يهرّب HTML ويعرض آخر MAX_TIMELINE_LINES حدثاً فقط.
"""

import sys
import re
import pathlib
import unittest
import importlib.util
from unittest import mock

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.31_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p22", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)

LiveOpsReporter = _bridge.LiveOpsReporter
format_elapsed_seconds = _bridge.format_elapsed_seconds
get_live_ops_reporter = _bridge.get_live_ops_reporter
attach_live_ops_reporter = _bridge.attach_live_ops_reporter
BridgeConfig = _bridge.BridgeConfig


def _extract_func(src: str, name: str, indent: str = "") -> str:
    m = re.search(rf"^{indent}def {name}\(", src, re.MULTILINE)
    assert m, f"لم أجد الدالة {name}"
    start = m.start()
    nxt = re.search(rf"^{indent}(?:def |class |@)", src[m.end():], re.MULTILINE)
    end = m.end() + (nxt.start() if nxt else len(src) - m.end())
    return src[start:end]


class TestBridgeConfigField(unittest.TestCase):
    """📡 [P22] حقل live_ops_reporter في BridgeConfig"""

    def test_01_field_exists_default_none(self):
        cfg = BridgeConfig()
        self.assertTrue(hasattr(cfg, "live_ops_reporter"))
        self.assertIsNone(cfg.live_ops_reporter)


class TestFormatElapsed(unittest.TestCase):
    """📡 [P22] تنسيق الزمن المنقضي بالعربي"""

    def test_02_format_arabic_seconds(self):
        self.assertEqual(format_elapsed_seconds(713.14), "713.1 ثانية")
        self.assertEqual(format_elapsed_seconds(4.5), "4.5 ثانية")
        self.assertEqual(format_elapsed_seconds(0), "0.0 ثانية")

    def test_03_format_bad_input_safe(self):
        self.assertEqual(format_elapsed_seconds("مش رقم"), "؟ ثانية")


class TestReporterCore(unittest.TestCase):
    """📡 [P22] سلوك timeline والمراحل بدون شبكة"""

    def _reporter(self):
        return LiveOpsReporter(chat_id=None, project_name="مشروع", project_key="prj_x")

    def test_04_disabled_without_chat_id(self):
        rep = self._reporter()
        self.assertFalse(rep.enable_telegram)
        with mock.patch.object(_bridge, "send_telegram_message_detailed") as send_m, \
             mock.patch.object(_bridge, "edit_telegram_message_text") as edit_m:
            rep.event("حدث تجريبي")
            self.assertFalse(send_m.called)
            self.assertFalse(edit_m.called)

    def test_05_event_appends_timeline_and_logs(self):
        rep = self._reporter()
        with mock.patch.object(_bridge, "log_event") as log_m:
            rep.event("تحميل المحرك", icon="🚀")
        self.assertEqual(len(rep.timeline), 1)
        self.assertEqual(rep.timeline[0]["icon"], "🚀")
        self.assertTrue(log_m.called)
        logged = " ".join(str(a) for a in log_m.call_args[0])
        self.assertIn("تحميل المحرك", logged)

    def test_06_stage_sequential_numbering_and_close_timing(self):
        rep = self._reporter()
        close1 = rep.stage("المرحلة الأولى")
        close2 = rep.stage("المرحلة الثانية")
        self.assertEqual(rep.stage_seq, 2)
        texts = [e["text"] for e in rep.timeline]
        self.assertTrue(any("[1] المرحلة الأولى" in t for t in texts))
        self.assertTrue(any("[2] المرحلة الثانية" in t for t in texts))
        took = close1(note="تمام")
        self.assertIsInstance(took, float)
        close2()
        closes = [e for e in rep.timeline if "✔" in e["text"]]
        self.assertEqual(len(closes), 2)
        self.assertTrue(any("تمام" in e["text"] for e in closes))
        # زمن الإغلاق يظهر كملحق (X.XXs)
        self.assertTrue(all(re.search(r"\(\d+\.\d{2}s\)", e["took"]) for e in closes))

    def test_07_heartbeat_updates_status_and_timeline(self):
        rep = self._reporter()
        rep.heartbeat("polling المتابعة", extra="محاولة 3")
        self.assertEqual(rep.current_status, "polling المتابعة")
        self.assertTrue(any(e["icon"] == "⏳" for e in rep.timeline))


class TestTelegramLiveLayer(unittest.TestCase):
    """📡 [P22] الرسالة الحية: sendMessage أولاً ثم editMessageText مع throttle"""

    def _reporter(self):
        return LiveOpsReporter(chat_id=12345, project_name="حج", project_key="prj_h")

    def test_08_first_push_sends_then_edits(self):
        rep = self._reporter()
        with mock.patch.object(_bridge, "send_telegram_message_detailed",
                               return_value={"ok": True, "message_id": 777}) as send_m, \
             mock.patch.object(_bridge, "edit_telegram_message_text",
                               return_value={"ok": True}) as edit_m:
            self.assertTrue(rep.push_telegram())
            self.assertEqual(rep.message_id, 777)
            self.assertEqual(send_m.call_count, 1)
            self.assertFalse(edit_m.called)
            # تعديل قسري (force) يتجاوز الـ throttle ويستعمل edit
            self.assertTrue(rep.push_telegram(force=True))
            self.assertEqual(send_m.call_count, 1)
            self.assertEqual(edit_m.call_count, 1)

    def test_09_throttle_blocks_rapid_edits(self):
        rep = self._reporter()
        rep.message_id = 777
        rep._last_edit_at = _bridge.time.time()
        with mock.patch.object(_bridge, "edit_telegram_message_text") as edit_m:
            self.assertFalse(rep.push_telegram())     # داخل نافذة الـ throttle
            self.assertFalse(edit_m.called)

    def test_10_push_network_error_never_raises(self):
        rep = self._reporter()
        with mock.patch.object(_bridge, "send_telegram_message_detailed",
                               side_effect=RuntimeError("network down")), \
             mock.patch.object(_bridge, "log_event"):
            self.assertFalse(rep.push_telegram())     # لا استثناء — يرجع False

    def test_11_render_escapes_html_and_caps_lines(self):
        rep = LiveOpsReporter(chat_id=1, project_name="<b>اسم</b>", project_key="k")
        for i in range(rep.MAX_TIMELINE_LINES + 5):
            rep.timeline.append({"ts": _bridge.time.time(), "icon": "•", "text": f"<tag{i}>", "took": ""})
        text = rep.render_telegram()
        self.assertIn("&lt;b&gt;اسم&lt;/b&gt;", text)
        self.assertNotIn("<tag0>", text)              # قُصّ خارج آخر N
        self.assertIn(f"&lt;tag{rep.MAX_TIMELINE_LINES + 4}&gt;", text)


class TestFinish(unittest.TestCase):
    """📡 [P22] الختام: صندوق التيرمينال + «⏱️ اخد X ثانية» + idempotency"""

    def test_12_finish_prints_summary_box_and_elapsed(self):
        rep = LiveOpsReporter(chat_id=None, project_name="حج", project_key="prj_h")
        rep.stage("توليد")
        with mock.patch("builtins.print") as print_m, \
             mock.patch.object(_bridge.logger, "info") as log_info:
            rep.finish("COMPLETED", summary_lines=["🌐 الرابط: example"])
        printed = "\n".join(str(c.args[0]) if c.args else "" for c in print_m.call_args_list)
        self.assertIn("⏱️ اخد", printed)
        self.assertIn("ثانية", printed)
        self.assertIn("COMPLETED", printed)
        self.assertIn("🌐 الرابط: example", printed)
        self.assertIn("╭", printed)
        self.assertIn("╰", printed)
        self.assertTrue(rep.finished)
        self.assertTrue(log_info.called)

    def test_13_finish_idempotent(self):
        rep = LiveOpsReporter(chat_id=None)
        with mock.patch("builtins.print") as print_m:
            rep.finish("COMPLETED")
            first_calls = print_m.call_count
            rep.finish("COMPLETED")                   # نداء ثانٍ — لا يطبع مجدداً
            self.assertEqual(print_m.call_count, first_calls)

    def test_14_finish_forces_final_telegram_push(self):
        rep = LiveOpsReporter(chat_id=99)
        rep.message_id = 5
        rep._last_edit_at = _bridge.time.time()       # داخل الـ throttle عمداً
        with mock.patch("builtins.print"), \
             mock.patch.object(_bridge, "edit_telegram_message_text",
                               return_value={"ok": True}) as edit_m:
            rep.finish("COMPLETED")
        self.assertTrue(edit_m.called)                # force تجاوز الـ throttle


class TestAccessors(unittest.TestCase):
    """📡 [P22] get/attach آمنتان و idempotent"""

    def test_15_get_reporter_safe(self):
        self.assertIsNone(get_live_ops_reporter(None))
        cfg = BridgeConfig()
        self.assertIsNone(get_live_ops_reporter(cfg))
        cfg.live_ops_reporter = "مش مراسل"
        self.assertIsNone(get_live_ops_reporter(cfg))
        rep = LiveOpsReporter(chat_id=None)
        cfg.live_ops_reporter = rep
        self.assertIs(get_live_ops_reporter(cfg), rep)

    def test_16_attach_idempotent(self):
        self.assertIsNone(attach_live_ops_reporter(None))
        cfg = BridgeConfig()
        rep1 = attach_live_ops_reporter(cfg, chat_id=1, project_name="أ", project_key="k")
        rep2 = attach_live_ops_reporter(cfg, chat_id=2, project_name="ب", project_key="x")
        self.assertIs(rep1, rep2)                     # لا يستبدل مراسلاً قائماً
        self.assertIs(cfg.live_ops_reporter, rep1)


class TestWorkerWiring(unittest.TestCase):
    """📡 [P22] الربط داخل process_user_task_async (فحص مصدر — بدون شبكة)"""

    WORKER_SRC = _extract_func(BRIDGE_SRC, "process_user_task_async")

    def test_17_attach_after_transport(self):
        self.assertIn("attach_live_ops_reporter(cfg", self.WORKER_SRC)
        t_pos = self.WORKER_SRC.index("attach_account_selection_live_transport")
        r_pos = self.WORKER_SRC.index("attach_live_ops_reporter")
        self.assertGreater(r_pos, t_pos)

    def test_18_stage_wraps_failover_call(self):
        stage_pos = self.WORKER_SRC.index("live_reporter.stage(")
        call_pos = self.WORKER_SRC.index("send_message_with_auto_account_failover(")
        self.assertLess(stage_pos, call_pos)
        close_pos = self.WORKER_SRC.index("close_generation_stage(note=")
        self.assertGreater(close_pos, call_pos)

    def test_19_finish_in_finally_isolated(self):
        finally_block = self.WORKER_SRC[self.WORKER_SRC.rindex("    finally:"):]
        self.assertIn("get_live_ops_reporter", finally_block)
        self.assertIn(".finish(", finally_block)
        # معزول بـ try/except قبل release_project_run — لا يكسر تحرير القفل
        self.assertLess(finally_block.index(".finish("), finally_block.index("release_project_run"))
        self.assertIn("except Exception", finally_block.split("release_project_run")[0])

    def test_20_wiring_isolated_by_try_except(self):
        # فتح المرحلة وإغلاقها معزولان — فشل الريبورتر لا يوقف المهمة
        seg = self.WORKER_SRC[self.WORKER_SRC.index("live_reporter = get_live_ops_reporter"):
                              self.WORKER_SRC.index("ALL_ACCOUNTS_IN_COOLDOWN")]
        self.assertGreaterEqual(seg.count("except Exception"), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
