import sys
import pathlib
import unittest
import urllib.parse
from unittest.mock import MagicMock

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))


def build_viewer_url(project_id: str) -> str:
    """بناء رابط العارض السحابي مع ترميز المعرف بأمان"""
    clean_id = urllib.parse.quote(str(project_id or "").strip(), safe="")
    return f"https://www.genspark.ai/autopilotagent_viewer?id={clean_id}"


def make_inline_keyboard(rows: list[list[dict]] | None) -> dict:
    """بناء Inline Keyboard قياسي متوافق مع كافة عملاء تيليجرام"""
    safe_rows = []
    for row in rows or []:
        if not isinstance(row, list):
            continue
        safe_buttons = []
        for button in row:
            if not isinstance(button, dict):
                continue
            text = str(button.get("text") or "").strip()
            callback_data = str(button.get("callback_data") or "").strip()
            url = str(button.get("url") or "").strip()
            if not text:
                continue
            if not callback_data and not url:
                continue
            safe_button = {"text": text}
            if callback_data:
                safe_button["callback_data"] = callback_data
            if url:
                safe_button["url"] = url
            safe_buttons.append(safe_button)
        if safe_buttons:
            safe_rows.append(safe_buttons)
    return {"inline_keyboard": safe_rows}


def build_live_preview_keyboard(project_id: str, status: str = "running") -> dict:
    """بناء Inline URL Button نظيف ومتوافق 100% مع جميع إصدارات تيليجرام"""
    viewer_url = build_viewer_url(project_id)
    if status == "running":
        return make_inline_keyboard([[
            {"text": "🌐 ⚡ فتح المعاينة ومتابعة البناء لايف ↗️", "url": viewer_url}
        ]])
    else:
        return make_inline_keyboard([[
            {"text": "🟢 فتح المشروع المكتمل ↗️", "url": viewer_url}
        ]])


def process_sse_project_start(obj: dict, on_project_start_callback=None):
    """محاكاة معالجة حدث project_start و project_field داخل حلقة الـ SSE مع حماية الـ Callback"""
    t = obj.get("type")
    proj_id_new = None
    if t == "project_start" and obj.get("id"):
        proj_id_new = obj["id"]
        if on_project_start_callback and callable(on_project_start_callback):
            try:
                on_project_start_callback(proj_id_new)
            except Exception:
                pass
    elif t == "project_field" and obj.get("field_name") == "id":
        proj_id_new = obj.get("field_value")
        if on_project_start_callback and callable(on_project_start_callback) and proj_id_new:
            try:
                on_project_start_callback(proj_id_new)
            except Exception:
                pass
    return proj_id_new


class TestLivePreviewP7(unittest.TestCase):
    """حزمة اختبارات الوحدة لمعمارية المعاينة الحية الفورية P7-A"""

    def test_01_build_viewer_url_formatting(self):
        """1. التحقق من بناء رابط العارض السحابي وترميز المعرف بدقة"""
        pid = "prj_abc123"
        url = build_viewer_url(pid)
        self.assertEqual(url, "https://www.genspark.ai/autopilotagent_viewer?id=prj_abc123")

        # مع أحرف خاصة
        special_pid = "prj/123@#45"
        encoded_url = build_viewer_url(special_pid)
        self.assertIn("prj%2F123%40%2345", encoded_url)

    def test_02_build_live_preview_keyboard_running(self):
        """2. التحقق من بناء زر المعاينة الحية أثناء البناء (status=running)"""
        pid = "test_live_001"
        kb = build_live_preview_keyboard(pid, status="running")
        self.assertIn("inline_keyboard", kb)
        self.assertEqual(len(kb["inline_keyboard"]), 1)
        btn = kb["inline_keyboard"][0][0]
        self.assertIn("🌐 ⚡ فتح المعاينة ومتابعة البناء لايف ↗️", btn["text"])
        self.assertEqual(btn["url"], f"https://www.genspark.ai/autopilotagent_viewer?id={pid}")

    def test_03_build_live_preview_keyboard_completed(self):
        """3. التحقق من بناء زر المشروع المكتمل عند انتهاء التوليد (status=completed)"""
        pid = "test_live_002"
        kb = build_live_preview_keyboard(pid, status="completed")
        self.assertIn("inline_keyboard", kb)
        btn = kb["inline_keyboard"][0][0]
        self.assertIn("🟢 فتح المشروع المكتمل ↗️", btn["text"])
        self.assertEqual(btn["url"], f"https://www.genspark.ai/autopilotagent_viewer?id={pid}")

    def test_04_no_dead_buttons_or_unsupported_style(self):
        """4. التحقق من خلو الأزرار من أي callback_data ميت أو حقل style مسبب لأخطاء 400"""
        pid = "test_live_003"
        for status in ["running", "completed"]:
            kb = build_live_preview_keyboard(pid, status=status)
            for row in kb["inline_keyboard"]:
                for btn in row:
                    self.assertNotIn("callback_data", btn, "يجب عدم وجود أزرار callback_data ميتة مثل retry")
                    self.assertNotIn("style", btn, "حقل style غير مدعوم في تليجرام ويسبب أخطاء 400")
                    self.assertIn("url", btn)
                    self.assertTrue(btn["url"].startswith("https://www.genspark.ai/autopilotagent_viewer"))

    def test_05_project_start_callback_dispatch(self):
        """5. التحقق من استدعاء الـ callback وتمرير project_id فور وصول حدث project_start"""
        mock_cb = MagicMock()
        event_obj = {"type": "project_start", "id": "pid_stream_999"}
        res = process_sse_project_start(event_obj, on_project_start_callback=mock_cb)
        self.assertEqual(res, "pid_stream_999")
        mock_cb.assert_called_once_with("pid_stream_999")

    def test_06_project_start_callback_resilience(self):
        """6. التحقق من صمود واستمرار تدفق الـ SSE حتى لو ألقى الـ callback خطأ استثنائي"""
        failing_cb = MagicMock(side_effect=RuntimeError("Telegram Network Timeout"))
        event_obj = {"type": "project_start", "id": "pid_stream_error_proof"}
        # لا يجب أن ينفجر الخطأ أو يوقف المعالجة
        try:
            res = process_sse_project_start(event_obj, on_project_start_callback=failing_cb)
            self.assertEqual(res, "pid_stream_error_proof")
        except Exception as e:
            self.fail(f"فشلت المعالجة بسبب عدم عزل الخطأ: {e}")

    def test_07_project_field_fallback_dispatch(self):
        """7. التحقق من استدعاء الـ callback كـ fallback عند وصول حدث project_field"""
        mock_cb = MagicMock()
        event_obj = {"type": "project_field", "field_name": "id", "field_value": "pid_field_fallback_123"}
        res = process_sse_project_start(event_obj, on_project_start_callback=mock_cb)
        self.assertEqual(res, "pid_field_fallback_123")
        mock_cb.assert_called_once_with("pid_field_fallback_123")


class TestTrueSSEStreamingGuard(unittest.TestCase):
    """حراسة صارمة ضد انحدار البث الحقيقي (TSK-2701):
    r.text في curl_cffi يحجب الرد كاملاً حتى نهاية التوليد، ما كان يجعل
    زر المعاينة الحية يظهر بعد اكتمال المشروع بدلاً من الثانية الأولى.
    الإصلاح: stream=True + iter_lines() — وهذه الاختبارات تمنع عودته للأبد."""

    @classmethod
    def setUpClass(cls):
        engine_path = webapp_dir / "01.03Genspark_claude-opus-5-code.py"
        cls.engine_src = engine_path.read_text(encoding="utf-8")
        # عزل جسم دالة send_chat فقط (من تعريفها حتى الدالة التالية على مستوى الوحدة)
        start = cls.engine_src.index("def send_chat(")
        next_def = cls.engine_src.index("\ndef ", start + 10)
        cls.send_chat_src = cls.engine_src[start:next_def]

    def test_08_ask_proxy_uses_stream_true(self):
        """8. طلب ask_proxy يجب أن يُفتح بـ stream=True (بث حي، لا تحميل كامل)"""
        import re as _re
        # [P12] المطابقة على السطر الكامل بدل [^)]* — لأن timeout أصبح tuple بقوس داخلي
        m = _re.search(r"^.*sess\.post\(.*ask_proxy.*$", self.send_chat_src, _re.MULTILINE)
        self.assertIsNotNone(m, "لم يتم العثور على استدعاء ask_proxy داخل send_chat")
        self.assertIn("stream=True", m.group(0), "ask_proxy بدون stream=True = زر المعاينة يتأخر حتى الاكتمال!")
        # [P12] حراسة إضافية: مهلة القراءة يجب أن تكون idle-timeout عبر tuple لا قطعاً كلياً
        self.assertIn("timeout=(", m.group(0), "timeout يجب أن يكون tuple (اتصال، قراءة) لمنع قطع المشاريع الطويلة")

    def test_09_sse_loop_uses_iter_lines_not_text(self):
        """9. حلقة الـ SSE يجب أن تستهلك iter_lines() ويُمنع r.text.splitlines() نهائياً"""
        self.assertIn(".iter_lines()", self.send_chat_src, "حلقة SSE يجب أن تقرأ عبر iter_lines() اللحظية")
        self.assertNotIn("r.text.splitlines()", self.send_chat_src, "r.text يحجب البث حتى الاكتمال — ممنوع الرجوع له!")

    def test_10_callback_fires_before_stream_completion(self):
        """10. محاكاة بث حي: الـ callback يجب أن يُستدعى عند سطر project_start قبل وصول باقي البث"""
        import json as _json
        events = [
            {"type": "project_start", "id": "pid_early_bird"},
            {"type": "message_field_delta", "field_name": "content", "delta": "chunk-1"},
            {"type": "message_field_delta", "field_name": "content", "delta": "chunk-2"},
        ]
        fired_at = []
        consumed = []

        def cb(pid):
            # لحظة الاستدعاء نسجل كم حدث تم استهلاكه حتى الآن
            fired_at.append(len(consumed))

        # محاكاة iter_lines: معالجة كل سطر فور وصوله (وليس بعد اكتمال الكل)
        for ev in events:
            line = "data: " + _json.dumps(ev)
            raw = line[5:].strip()
            obj = _json.loads(raw)
            process_sse_project_start(obj, on_project_start_callback=cb)
            consumed.append(obj)

        self.assertEqual(fired_at, [0], "الـ callback يجب أن ينطلق عند أول حدث (قبل استهلاك أي chunk من الرد)")


if __name__ == "__main__":
    unittest.main()

