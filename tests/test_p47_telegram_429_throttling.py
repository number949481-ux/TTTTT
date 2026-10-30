# -*- coding: utf-8 -*-
"""
test_p47_telegram_429_throttling.py
===================================
حزمة اختبارات التحقق من فرملة رسائل التعديل الحية (7-Seconds Throttling Gate)
واستثناء أحداث القبول المفصلية (account-claimed, attempt-succeeded, handoff)
وصمام التعافي التلقائي من HTTP 429 Retry-After.
"""
import time
from unittest.mock import patch, MagicMock
import pytest
from bridge_refactor import runtime


def test_p47_initial_send_creates_message_id():
    """الحدث الأول يُنشئ رسالة جديدة ويحفظ message_id."""
    transport = runtime.AccountSelectionLiveTransport(chat_id=123, project_key="pk_test", project_name="TestProject")
    with patch.object(runtime.ns, "send_telegram_message_detailed", return_value={"ok": True, "message_id": 888}) as mock_send, \
         patch.object(runtime.ns, "edit_telegram_message_text", return_value={"ok": True}) as mock_edit:
        
        ok = transport.publish({"event": "attempt-started", "attempt_number": 1})
        assert ok is True
        assert mock_send.call_count == 1
        assert mock_edit.call_count == 0
        assert transport.message_id == 888


def test_p47_rapid_skips_throttled_within_7_seconds():
    """الأحداث المتتالية السريعة خلال 7 ثوانٍ يتم فرملتها ولا ترسل editMessageText."""
    transport = runtime.AccountSelectionLiveTransport(chat_id=123, project_key="pk_test", project_name="TestProject")
    with patch.object(runtime.ns, "send_telegram_message_detailed", return_value={"ok": True, "message_id": 888}), \
         patch.object(runtime.ns, "edit_telegram_message_text", return_value={"ok": True}) as mock_edit:
        
        # 1. First event establishes message
        transport.publish({"event": "attempt-started", "attempt_number": 1})
        
        # 2. Rapid event 1s later -> throttled!
        ok2 = transport.publish({"event": "attempt-failed", "attempt_number": 1, "reason": "empty"})
        assert ok2 is True
        assert mock_edit.call_count == 0

        # 3. Another rapid event 2s later -> throttled!
        ok3 = transport.publish({"event": "attempt-started", "attempt_number": 2})
        assert ok3 is True
        assert mock_edit.call_count == 0


def test_p47_priority_event_bypasses_throttle_immediately():
    """أحداث القبول الحيوية (account-claimed) تكسر الفرملة وتُرسل فورياً للمستخدم."""
    transport = runtime.AccountSelectionLiveTransport(chat_id=123, project_key="pk_test", project_name="TestProject")
    with patch.object(runtime.ns, "send_telegram_message_detailed", return_value={"ok": True, "message_id": 888}), \
         patch.object(runtime.ns, "edit_telegram_message_text", return_value={"ok": True}) as mock_edit:
        
        transport.publish({"event": "attempt-started", "attempt_number": 1})
        
        # Priority event -> bypasses throttle immediately
        ok = transport.publish({
            "event": "account-claimed",
            "attempt_number": 2,
            "account_masked": "u***@g***.com"
        })
        assert ok is True
        assert mock_edit.call_count == 1


def test_p47_normal_edit_after_7_seconds_elapsed():
    """الأحداث العادية تُرسل تعديلاً فور انقضاء مهلة الـ 7 ثوانٍ."""
    transport = runtime.AccountSelectionLiveTransport(chat_id=123, project_key="pk_test", project_name="TestProject")
    with patch.object(runtime.ns, "send_telegram_message_detailed", return_value={"ok": True, "message_id": 888}), \
         patch.object(runtime.ns, "edit_telegram_message_text", return_value={"ok": True}) as mock_edit:
        
        transport.publish({"event": "attempt-started", "attempt_number": 1})
        
        # Simulate passage of 7.5 seconds
        transport.last_publish_time -= 7.5
        
        ok = transport.publish({"event": "attempt-failed", "attempt_number": 1, "reason": "rate_limit"})
        assert ok is True
        assert mock_edit.call_count == 1


def test_p47_automatic_429_backoff_recovery():
    """دالة _call_telegram_api_json تستخرج retry_after وتنتظر وتكرر المحاولة بنجاح."""
    from curl_cffi import requests as cffi

    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.json.return_value = {
        "ok": False,
        "error_code": 429,
        "description": "Too Many Requests: retry after 2",
        "parameters": {"retry_after": 2}
    }

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {"ok": True, "result": {"message_id": 9999}}

    with patch.object(runtime.ns, "TELEGRAM_BOT_TOKEN", "12345:mock_test_token"), \
         patch("time.sleep") as mock_sleep, \
         patch.object(cffi, "post", side_effect=[resp_429, resp_200]):
        res = runtime._call_telegram_api_json("sendMessage", {"chat_id": 123, "text": "hello"})
        assert res["ok"] is True
        assert res["result"]["message_id"] == 9999
        mock_sleep.assert_called_with(3.0)
