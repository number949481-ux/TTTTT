# -*- coding: utf-8 -*-
"""
P16 — Early Make-Public Guard Tests
حراسة عقد النشر العام المبكر (المشروع Public فور التقاط الـ pid):
- وجود _early_make_public_async داخل send_message_and_make_public
- الاستدعاء داخل _pid_capture_callback (فور project_start من البث)
- الاستدعاء في مسار الاستئناف carry_pid (المشروع القائم لا يرسل project_start)
- الاستدعاء في مسار الفورك/URL (forked_pid / orig_pid)
- Fire-and-Forget: خيط خلفي daemon لا يعطّل البث الرئيسي
- عدم التكرار: مرة واحدة فقط لكل pid (early_public_pids)
- تجاهل الـ pids الوهمية (تبدأ بـ __ مثل __STREAM_INTERRUPTED__)
- البانر والإصدار 01.31 يعكسان P16
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).parent.parent.resolve()
BRIDGE = ROOT / "01.32_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE.read_text(encoding="utf-8")


def _extract_func(src: str, name: str) -> str:
    """يعزل جسم دالة top-level بالاسم من المصدر."""
    m = re.search(rf"^def {name}\(", src, re.MULTILINE)
    assert m, f"لم أجد الدالة {name}"
    start = m.start()
    nxt = re.search(r"^(?:def |class |@)", src[m.end():], re.MULTILINE)
    end = m.end() + (nxt.start() if nxt else len(src) - m.end())
    return src[start:end]


SEND_PUBLIC = _extract_func(BRIDGE_SRC, "send_message_and_make_public")


class TestP16EarlyMakePublic(unittest.TestCase):
    """حراسة النشر العام المبكر داخل send_message_and_make_public."""

    def test_01_helper_defined_inside_send_public(self):
        """الدالة المساعدة معرفة داخل الدالة الرئيسية."""
        self.assertIn("def _early_make_public_async(", SEND_PUBLIC)

    def test_02_called_from_pid_capture_callback(self):
        """النشر المبكر يُستدعى من ملتقط الـ pid (مسار البث الحي)."""
        cb = SEND_PUBLIC[SEND_PUBLIC.index("def _pid_capture_callback"):]
        nxt = re.search(r"\n    for attempt in range", cb)
        cb = cb[: nxt.start() if nxt else len(cb)]
        self.assertIn("_early_make_public_async(live_pid)", cb)

    def test_03_called_in_carry_pid_resume_path(self):
        """مسار الاستئناف carry_pid ينشر مبكراً (المشروع القائم لا يرسل project_start)."""
        seg = SEND_PUBLIC[SEND_PUBLIC.index("if carry_pid:"):]
        seg = seg[: seg.index("elif url")]
        self.assertIn("_early_make_public_async(project_id)", seg)

    def test_04_called_in_fork_url_path(self):
        """مسار الفورك/URL ينشر مبكراً فور معرفة المشروع."""
        seg = SEND_PUBLIC[SEND_PUBLIC.index("elif url"):]
        seg = seg[: seg.index("start_time = time.time()")]
        self.assertIn("_early_make_public_async(project_id)", seg)

    def test_05_fire_and_forget_daemon_thread(self):
        """التنفيذ في خيط خلفي daemon — لا يعطّل البث الرئيسي."""
        helper = SEND_PUBLIC[SEND_PUBLIC.index("def _early_make_public_async"):]
        helper = helper[: helper.index("def _pid_capture_callback")]
        self.assertIn("threading.Thread(", helper)
        self.assertIn("daemon=True", helper)
        self.assertIn("make_project_always_public(", helper)

    def test_06_once_per_pid_dedup(self):
        """عدم التكرار: pid منشور مسبقاً لا يُعاد نشره."""
        helper = SEND_PUBLIC[SEND_PUBLIC.index("def _early_make_public_async"):]
        helper = helper[: helper.index("def _pid_capture_callback")]
        self.assertIn("early_public_pids", helper)
        self.assertIn("live_pid in early_public_pids", helper)
        self.assertIn("early_public_pids.add(live_pid)", helper)

    def test_07_ignores_sentinel_pids(self):
        """الـ pids الوهمية (تبدأ بـ __) تُتجاهل — لا نشر لـ __STREAM_INTERRUPTED__."""
        helper = SEND_PUBLIC[SEND_PUBLIC.index("def _early_make_public_async"):]
        self.assertIn('str(live_pid).startswith("__")', helper)

    def test_08_cookies_snapshot_isolation(self):
        """الخيط الخلفي يعمل على نسخة snapshot من الكوكيز — لا سباق مع الحلقة الرئيسية."""
        helper = SEND_PUBLIC[SEND_PUBLIC.index("def _early_make_public_async"):]
        helper = helper[: helper.index("def _pid_capture_callback")]
        self.assertIn("snapshot_cookies", helper)

    def test_09_banner_and_version_reflect_p16(self):
        """البانر 01.31 يذكر P16 والنشر العام المبكر."""
        head = BRIDGE_SRC[:1800]
        self.assertIn("P12..P19 + P20", head)
        self.assertIn("نشر عام مبكر P16", head)
        self.assertIn('BUILD_VERSION = "01.32"', BRIDGE_SRC)
        self.assertIn('BUILD_PARENT_BASELINE = "01.30"', BRIDGE_SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
