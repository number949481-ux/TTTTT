#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p28_document_input.py
================================
📄 [P28] حراسة ميزة «استقبال ملفات المهام النصية» (Document Ingestion .txt & .md):

1. الثوابت المركزية: ALLOWED_DOCUMENT_EXTENSIONS (الامتدادات الأربعة، frozenset)
   + MAX_DOCUMENT_SIZE_BYTES = 5 MB بالضبط.
2. دالة التنزيل download_telegram_document_text: نجاح getFile + التنزيل ➔ نص UTF-8،
   بايتات غير صالحة ➔ errors="replace" بلا استثناء، فشل شبكة/HTTP/ok=false/file_path
   مفقود ➔ None بدون Crash يتسرب لخيط الـ Polling.
3. الـ Dispatcher (handle_telegram_update): .txt/.md/.markdown مقبولة وتُجدول
   process_user_task_async بالمحتوى، Caption يُدمج «caption\\n\\ncontent»، بدون
   Caption ➔ المحتوى فقط، امتداد بحروف كبيرة .TXT مقبول (normalize lower)،
   .pdf/.zip/بلا اسم ➔ رسالة رفض ودية بلا تنزيل، حجم > 5MB ➔ رسالة حجم بلا تنزيل،
   فشل التنزيل/ملف فارغ ➔ تنبيه تعذر القراءة، ملف داخل حالة AWAITING_NEW_PROMPT ➔
   يمر كنص الـ Wizard نفسه.
4. Zero Regression: الرسائل النصية العادية و /start لا تلمس مسار الـ Document
   إطلاقاً، ورسالة تحمل text + document تُعامل كنص عادي (الشرط document and not text).
"""

import sys
import types
import shutil
import pathlib
import tempfile
import unittest
import importlib.util
from unittest import mock

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p28", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)

CHAT_ID = 888


# ══════════════ أدوات محاكاة requests (import داخلي في الدالة) ══════════════
class _FakeResponse:
    def __init__(self, status_code=200, json_data=None, content=b"", text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.content = content
        self.text = text or (content.decode("utf-8", errors="replace") if content else "")

    def json(self):
        return self._json


class _FakeRequests(types.ModuleType):
    """موديول requests وهمي يُحقن في sys.modules — يلتقط النداءات ويعيد ردوداً مُعدّة."""

    def __init__(self, responses):
        super().__init__("requests")
        self._responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if not self._responses:
            raise ConnectionError("لا ردود متبقية في المحاكاة")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class _RequestsPatchMixin:
    def _patch_requests(self, responses):
        fake = _FakeRequests(responses)
        self._orig_requests = sys.modules.get("requests")
        sys.modules["requests"] = fake
        self.addCleanup(self._restore_requests)
        return fake

    def _restore_requests(self):
        if self._orig_requests is not None:
            sys.modules["requests"] = self._orig_requests
        else:
            sys.modules.pop("requests", None)


# ══════════════ 1) الثوابت المركزية ══════════════
class TestP28Constants(unittest.TestCase):
    def test_allowed_extensions_exact_set(self):
        self.assertEqual(
            _bridge.ALLOWED_DOCUMENT_EXTENSIONS,
            frozenset({".txt", ".md", ".markdown", ".text"}),
        )

    def test_allowed_extensions_is_frozenset(self):
        self.assertIsInstance(_bridge.ALLOWED_DOCUMENT_EXTENSIONS, frozenset)

    def test_max_size_is_exactly_5mb(self):
        self.assertEqual(_bridge.MAX_DOCUMENT_SIZE_BYTES, 5 * 1024 * 1024)

    def test_extensions_are_lowercase_with_dot(self):
        for ext in _bridge.ALLOWED_DOCUMENT_EXTENSIONS:
            self.assertTrue(ext.startswith("."))
            self.assertEqual(ext, ext.lower())


# ══════════════ 2) دالة التنزيل ══════════════
class TestP28DownloadFunction(_RequestsPatchMixin, unittest.TestCase):
    def setUp(self):
        self._orig_token = _bridge.TELEGRAM_BOT_TOKEN
        _bridge.TELEGRAM_BOT_TOKEN = "123456:TEST-TOKEN"

    def tearDown(self):
        _bridge.TELEGRAM_BOT_TOKEN = self._orig_token

    def _meta_ok(self, file_path="documents/task.txt"):
        return _FakeResponse(200, {"ok": True, "result": {"file_path": file_path}})

    def test_success_returns_utf8_text(self):
        fake = self._patch_requests([
            self._meta_ok(),
            _FakeResponse(200, content="ابنِ لي موقعاً كاملاً ✅".encode("utf-8")),
        ])
        result = _bridge.download_telegram_document_text("FILE123")
        self.assertEqual(result, "ابنِ لي موقعاً كاملاً ✅")
        self.assertEqual(len(fake.calls), 2)
        self.assertIn("/getFile", fake.calls[0][0])
        self.assertIn("/file/bot", fake.calls[1][0])

    def test_getfile_passes_file_id_param(self):
        fake = self._patch_requests([self._meta_ok(), _FakeResponse(200, content=b"x")])
        _bridge.download_telegram_document_text("ABC-42")
        self.assertEqual(fake.calls[0][1].get("params"), {"file_id": "ABC-42"})

    def test_invalid_utf8_bytes_replaced_not_crash(self):
        self._patch_requests([self._meta_ok(), _FakeResponse(200, content=b"ok\xff\xfe end")])
        result = _bridge.download_telegram_document_text("F")
        self.assertIsNotNone(result)
        self.assertIn("ok", result)
        self.assertIn("\ufffd", result)  # حرف الاستبدال بدل الانهيار

    def test_getfile_http_500_returns_none(self):
        self._patch_requests([_FakeResponse(500, text="server error")])
        self.assertIsNone(_bridge.download_telegram_document_text("F"))

    def test_getfile_ok_false_returns_none(self):
        self._patch_requests([_FakeResponse(200, {"ok": False, "description": "bad"})])
        self.assertIsNone(_bridge.download_telegram_document_text("F"))

    def test_missing_file_path_returns_none(self):
        self._patch_requests([_FakeResponse(200, {"ok": True, "result": {}})])
        self.assertIsNone(_bridge.download_telegram_document_text("F"))

    def test_download_http_404_returns_none(self):
        self._patch_requests([self._meta_ok(), _FakeResponse(404)])
        self.assertIsNone(_bridge.download_telegram_document_text("F"))

    def test_network_exception_returns_none_no_crash(self):
        self._patch_requests([ConnectionError("network down")])
        self.assertIsNone(_bridge.download_telegram_document_text("F"))

    def test_empty_bot_token_returns_none_without_network(self):
        _bridge.TELEGRAM_BOT_TOKEN = ""
        fake = self._patch_requests([])
        self.assertIsNone(_bridge.download_telegram_document_text("F"))
        self.assertEqual(fake.calls, [])


# ══════════════ 3) الـ Dispatcher: مسار الملفات ══════════════
class _DispatcherHarness(unittest.TestCase):
    """عزل كامل لمسار handle_telegram_update: التقاط الرسائل والجدولة والتنزيل."""

    def setUp(self):
        self._tmp = pathlib.Path(tempfile.mkdtemp(prefix="p28_test_"))
        self.addCleanup(shutil.rmtree, self._tmp, True)

        self.sent_messages = []
        self.scheduled = []
        self.download_calls = []
        self.download_result = "محتوى الملف الافتراضي"
        self._state = {}

        patches = [
            mock.patch.object(_bridge, "is_chat_allowed", return_value=True),
            mock.patch.object(
                _bridge, "send_telegram_message",
                side_effect=lambda cid, txt, **kw: self.sent_messages.append((cid, txt)) or True,
            ),
            mock.patch.object(
                _bridge, "download_telegram_document_text",
                side_effect=lambda fid: self.download_calls.append(fid) or self.download_result,
            ),
            mock.patch.object(_bridge, "get_user_state", side_effect=lambda cid: dict(self._state)),
            mock.patch.object(
                _bridge, "set_user_state",
                side_effect=lambda cid, st: self._state.clear() or self._state.update(st or {}),
            ),
            mock.patch.object(
                _bridge.EXECUTOR, "submit",
                side_effect=lambda fn, *a, **kw: self.scheduled.append((fn, a, kw)) or mock.MagicMock(),
            ),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def _doc_update(self, file_name="task.txt", file_size=1024, caption=None, text=None, file_id="FID1"):
        msg = {
            "chat": {"id": CHAT_ID},
            "from": {"id": CHAT_ID},
            "document": {"file_name": file_name, "file_size": file_size, "file_id": file_id},
        }
        if caption is not None:
            msg["caption"] = caption
        if text is not None:
            msg["text"] = text
        return {"message": msg}

    def _last_scheduled_query(self):
        self.assertTrue(self.scheduled, "لم تُجدول أي مهمة")
        fn, args, _ = self.scheduled[-1]
        self.assertIs(fn, _bridge.process_user_task_async)
        # التوقيع: (chat_id, url, query, ...)
        return args[2]

    def _last_pending_prompt(self):
        """🛡️ [P42] العقد الجديد (DEC-038): نص حر/محتوى ملف في IDLE ⟔ بطاقة تأكيد
        (صفر جدولة) — المحتوى يُحفظ كاملاً في pending_prompt بحالة AWAITING_PROJECT_CONFIRMATION."""
        self.assertEqual(self.scheduled, [], "P42: ممنوع جدولة أي مهمة قبل التأكيد")
        self.assertEqual(self._state.get("action"), _bridge.AWAITING_PROJECT_CONFIRMATION)
        return self._state.get("pending_prompt")


class TestP28DispatcherAccepted(_DispatcherHarness):
    # 🛡️ [P42] تحديث واعٍ موثّق (وثيقة 16 / DEC-038): محتوى الملف في IDLE صار نصاً حراً
    # يمر على Intent Guard (بطاقة تأكيد — صفر Mutation) بدل الجدولة التلقائية المحذوفة.
    # التنزيل والدمج والرفض الودي (عقد P28 نفسه) بلا أي تغيير.
    def test_txt_file_content_reaches_intent_guard(self):
        self.download_result = "ابنِ تطبيق مهام كامل"
        _bridge.handle_telegram_update(self._doc_update("spec.txt"))
        self.assertEqual(self.download_calls, ["FID1"])
        self.assertEqual(self._last_pending_prompt(), "ابنِ تطبيق مهام كامل")

    def test_md_file_accepted(self):
        _bridge.handle_telegram_update(self._doc_update("README.md"))
        self.assertEqual(self.download_calls, ["FID1"])
        self.assertIsNotNone(self._last_pending_prompt())

    def test_markdown_extension_accepted(self):
        _bridge.handle_telegram_update(self._doc_update("notes.markdown"))
        self.assertEqual(self.download_calls, ["FID1"])
        self.assertIsNotNone(self._last_pending_prompt())

    def test_uppercase_extension_accepted(self):
        _bridge.handle_telegram_update(self._doc_update("SPEC.TXT"))
        self.assertEqual(self.download_calls, ["FID1"])
        self.assertIsNotNone(self._last_pending_prompt())

    def test_caption_merged_before_content(self):
        self.download_result = "التفاصيل الكاملة هنا"
        _bridge.handle_telegram_update(self._doc_update("t.txt", caption="نفذ هذه المواصفات"))
        self.assertEqual(self._last_pending_prompt(), "نفذ هذه المواصفات\n\nالتفاصيل الكاملة هنا")

    def test_no_caption_content_only_stripped(self):
        self.download_result = "  المحتوى فقط  \n"
        _bridge.handle_telegram_update(self._doc_update("t.md"))
        self.assertEqual(self._last_pending_prompt(), "المحتوى فقط")

    def test_document_inside_awaiting_new_prompt_feeds_wizard(self):
        self._state.update({"action": "AWAITING_NEW_PROMPT", "project_key": "prj_x", "project_name": "مشروعي"})
        self.download_result = "برومبت من ملف"
        _bridge.handle_telegram_update(self._doc_update("prompt.txt"))
        self.assertTrue(self.scheduled)
        fn, args, _ = self.scheduled[-1]
        self.assertIs(fn, _bridge.process_user_task_async)
        self.assertEqual(args[2], "برومبت من ملف")
        self.assertEqual(args[4], "prj_x")  # project_key_hint من حالة الـ Wizard


class TestP28DispatcherRejected(_DispatcherHarness):
    def _assert_rejected_without_download(self, needle):
        self.assertEqual(self.download_calls, [])
        self.assertEqual(self.scheduled, [])
        self.assertTrue(self.sent_messages, "لم تُرسل رسالة الرفض")
        self.assertIn(needle, self.sent_messages[-1][1])

    def test_pdf_rejected_no_download(self):
        _bridge.handle_telegram_update(self._doc_update("report.pdf"))
        self._assert_rejected_without_download("غير مدعوم")

    def test_zip_rejected(self):
        _bridge.handle_telegram_update(self._doc_update("archive.zip"))
        self._assert_rejected_without_download("غير مدعوم")

    def test_missing_file_name_rejected(self):
        _bridge.handle_telegram_update(self._doc_update(file_name=""))
        self._assert_rejected_without_download("غير مدعوم")

    def test_oversize_rejected_no_download(self):
        _bridge.handle_telegram_update(
            self._doc_update("big.txt", file_size=_bridge.MAX_DOCUMENT_SIZE_BYTES + 1)
        )
        self._assert_rejected_without_download("أكبر من الحد")

    def test_exactly_5mb_accepted(self):
        # 🛡️ [P42] القبول = تنزيل + بطاقة تأكيد (لا جدولة تلقائية بعد حذف الـ Fallback)
        _bridge.handle_telegram_update(
            self._doc_update("edge.txt", file_size=_bridge.MAX_DOCUMENT_SIZE_BYTES)
        )
        self.assertEqual(self.download_calls, ["FID1"])
        self.assertIsNotNone(self._last_pending_prompt())

    def test_download_failure_sends_friendly_error(self):
        self.download_result = None
        _bridge.handle_telegram_update(self._doc_update("t.txt"))
        self.assertEqual(self.scheduled, [])
        self.assertIn("تعذر قراءة", self.sent_messages[-1][1])

    def test_empty_content_sends_friendly_error(self):
        self.download_result = "   \n  "
        _bridge.handle_telegram_update(self._doc_update("t.txt"))
        self.assertEqual(self.scheduled, [])
        self.assertIn("تعذر قراءة", self.sent_messages[-1][1])


class TestP28ZeroRegression(_DispatcherHarness):
    def test_plain_text_message_never_touches_document_path(self):
        # 🛡️ [P42] النص العادي لا يلمس مسار الـ Document إطلاقاً — وفي IDLE يمر على Intent Guard
        _bridge.handle_telegram_update(
            {"message": {"chat": {"id": CHAT_ID}, "from": {"id": CHAT_ID}, "text": "ابنِ لي موقعاً"}}
        )
        self.assertEqual(self.download_calls, [])
        self.assertEqual(self._last_pending_prompt(), "ابنِ لي موقعاً")

    def test_start_command_still_shows_dashboard(self):
        with mock.patch.object(_bridge, "render_dashboard_text", return_value="لوحة"), \
             mock.patch.object(_bridge, "get_main_keyboard", return_value={"inline_keyboard": []}):
            _bridge.handle_telegram_update(
                {"message": {"chat": {"id": CHAT_ID}, "from": {"id": CHAT_ID}, "text": "/start"}}
            )
        self.assertEqual(self.scheduled, [])
        self.assertEqual(self.download_calls, [])
        self.assertTrue(self.sent_messages)

    def test_message_with_both_text_and_document_treated_as_text(self):
        # الشرط (document and not text) — النص له الأولوية ولا تنزيل إطلاقاً.
        # 🛡️ [P42] وفي IDLE النص يمر على Intent Guard بدل الجدولة التلقائية
        _bridge.handle_telegram_update(self._doc_update("t.txt", text="نص صريح"))
        self.assertEqual(self.download_calls, [])
        self.assertEqual(self._last_pending_prompt(), "نص صريح")

    def test_document_from_disallowed_chat_blocked_before_download(self):
        with mock.patch.object(_bridge, "is_chat_allowed", return_value=False):
            _bridge.handle_telegram_update(self._doc_update("t.txt"))
        self.assertEqual(self.download_calls, [])
        self.assertEqual(self.scheduled, [])
        self.assertEqual(self.sent_messages, [])


# ══════════════ 4) عقود التكامل في نص المصدر ══════════════
class TestP28SourceContracts(unittest.TestCase):
    def test_ingestion_block_after_permission_gate(self):
        gate_pos = BRIDGE_SRC.find('if not is_chat_allowed(chat_id, (msg.get("from") or {}).get("id")):')
        ingest_pos = BRIDGE_SRC.find('document = msg.get("document") or {}')
        self.assertGreater(gate_pos, 0)
        self.assertGreater(ingest_pos, gate_pos, "كتلة الاستيعاب يجب أن تأتي بعد بوابة الصلاحيات")

    def test_ingestion_block_before_start_command(self):
        ingest_pos = BRIDGE_SRC.find('document = msg.get("document") or {}')
        start_pos = BRIDGE_SRC.find('if text in ["/start", "/help"]:')
        self.assertGreater(start_pos, ingest_pos, "الاستيعاب يجب أن يسبق فحص /start ليغذي text")

    def test_guard_condition_document_and_not_text(self):
        self.assertIn("if document and not text:", BRIDGE_SRC)

    def test_extension_normalized_lowercase(self):
        self.assertIn(".suffix.lower()", BRIDGE_SRC)

    def test_download_uses_errors_replace(self):
        self.assertIn('decode("utf-8", errors="replace")', BRIDGE_SRC)

    def test_helper_lives_in_p04_next_to_send_document(self):
        helper_pos = BRIDGE_SRC.find("def download_telegram_document_text(")
        send_pos = BRIDGE_SRC.find("def send_telegram_document(")
        self.assertGreater(helper_pos, 0)
        self.assertLess(helper_pos, send_pos, "دالة التنزيل بجوار send_telegram_document في p04")


if __name__ == "__main__":
    unittest.main(verbosity=2)
