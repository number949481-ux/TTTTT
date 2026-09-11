"""Offline automatic compaction: fresh session/history, cancellation and handoff."""
import ast
import copy
import threading
import types
import unittest
from unittest import mock
import test_credit_completion_recovery as base

bridge, ROOT, PID, URL = base.bridge, base.ROOT, base.PID, base.URL
DONE, CREDIT = base.DONE, base.CREDIT
NEW_PID = "22222222-2222-4222-8222-222222222222"
SUMMARY = {"role": "assistant", "id": "fresh-summary", "content": "Verified summary",
           "session_state": {"is_compact_summary": True}}
OLD_SUMMARY = {**SUMMARY, "id": "old-summary", "content": "Old summary"}


class CompactTests(unittest.TestCase):
    patch = base.CreditRecoveryTests.patch
    archive = base.CreditRecoveryTests.archive
    run_pipeline = base.CreditRecoveryTests.run_pipeline
    isolated_registry = base.CreditRecoveryTests.isolated_registry

    def setUp(self):
        base.CreditRecoveryTests.setUp(self)
        self.engine.VERIFIED_COMPACT_CONTEXT_SUPPORTED = True
        self.cfg.project_fast_lean_skip = True
        self.cfg.session_timeout = 0.03
        self.runtime = types.SimpleNamespace(cancel_event=None)
        def completed(*args, **kwargs):
            kwargs["cfg"]._chat_attempt = {"request_id": "compact-request",
                "project_id": self.engine.send_chat.return_value[1], "finished": True,
                "credit_exhausted": False}
            return self.engine.send_chat.return_value
        self.engine.send_chat.return_value = (DONE, PID, "summary-result")
        self.engine.send_chat.side_effect = completed
        self.fetch_count = 0
        def fetch(pid, cookies, cfg):
            self.fetch_count += 1
            cfg._last_fetch_status = 200
            cfg._last_chat_session_id = "new-session" if self.fetch_count > 1 else "old-session"
            return copy.deepcopy([SUMMARY] if self.fetch_count > 1 else [OLD_SUMMARY])
        self.engine.fetch_project_messages.side_effect = fetch

    def compact(self):
        return bridge.run_verified_compact(
            self.engine, {}, self.runtime, self.cfg, PID, self.accounts[0]["email"])

    def test_post_compact_save_failure_keeps_latest_without_work_or_recompact(self):
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, fail_save=True)
        self.assertEqual([c[0] for c in calls], ["/compact"])
        self.assertEqual(result[1], "COMPACT_HANDOFF_BLOCKED")
        self.assertEqual(bridge.extract_project_id(result[0]), "33333333-3333-4333-8333-333333333333")
        self.assertFalse(reg.get_compact_state()["due"])
        self.cooldown.assert_called_once()

    def test_identity_save_failure_stops_handoff_without_business_send(self):
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, fail_identity=True)
        self.assertEqual([c[0] for c in calls], ["/compact"])
        self.assertEqual(result[1], "COMPACT_HANDOFF_BLOCKED")
        self.assertTrue(result[0])
        self.assertFalse(reg.get_compact_state()["due"])
        self.cooldown.assert_called_once()

    def test_owner_manifest_fresh_fork_dispatches_without_maintenance(self):
        state = {"due": False, "deferred": True, "verified": False,
                 "bypass_ready": False, "source_pid": PID, "chat_session_id": "old"}
        calls, result, _, _, _ = self.worker_scenario(initial_due=True, restored_state=state)
        self.assertEqual([c[0] for c in calls], ["User modification"])
        self.assertEqual(result[1], "COMPLETED")
        self.cooldown.assert_not_called()

    def test_untagged_due_is_cleared_and_never_compacts(self):
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, restored_state={
            "due": True, "source_pid": PID, "duration_seconds": 55})
        self.assertEqual([c[0] for c in calls], ["User modification"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(reg.get_compact_state()["due"])

    def test_new_credit_replaces_old_deferral_and_long_credit_clears_due(self):
        reg = self.isolated_registry()
        before = reg._read()
        reg.set_compact_state(False, PID, deferred=True, chat_session_id="same", bypass_ready=False)
        reg.set_compact_state(True, NEW_PID, 180, chat_session_id="same", trigger_status="CREDIT_EXHAUSTED")
        self.assertTrue(reg.get_compact_state()["due"])
        self.assertNotIn("deferred", reg.get_compact_state())
        reg.set_compact_state(True, NEW_PID, 180.001, trigger_status="CREDIT_EXHAUSTED")
        self.assertFalse(reg.get_compact_state()["due"])
        reg.set_compact_state(True, NEW_PID, 55, trigger_status="COMPLETED")
        self.assertFalse(reg.get_compact_state()["due"])
        for key in ("file_index", "checkpoints", "updates", "project_settings", "schema_version"):
            self.assertEqual(before[key], reg._read()[key])

    def test_compact_uses_full_session_timeout_and_can_finish_after_180_seconds(self):
        clock = {"now": 0.0, "sent": False}
        self.cfg.session_timeout = 1000
        self.runtime = types.SimpleNamespace(cancel_event=None)
        def send(*args, **kwargs):
            clock["sent"] = True
            cfg = kwargs["cfg"]
            self.assertEqual(cfg._chat_deadline, 1000)
            cfg._chat_attempt = {"request_id": "compact-request", "project_id": PID,
                "message_ids": {"current-reply"}, "old_message_ids": {"old-summary"}, "finished": False}
            return "__STREAM_INTERRUPTED__", PID, None
        def fetch(pid, cookies, cfg):
            cfg._last_fetch_status = 200
            cfg._last_chat_session_id = "current-session"
            if not clock["sent"]:
                return [OLD_SUMMARY]
            return [{"id": "current-reply", "role": "assistant", "content": DONE,
                     "session_state": {"_finish_reason": "stop"} if clock["now"] >= 900 else {}}]
        self.engine.send_chat.side_effect = send
        self.engine.fetch_project_messages.side_effect = fetch
        with mock.patch.object(bridge.time, "time", side_effect=lambda: clock["now"]), \
             mock.patch.object(bridge.time, "monotonic", side_effect=lambda: clock["now"]), \
             mock.patch.object(bridge.time, "sleep", side_effect=lambda seconds: clock.update(now=clock["now"]+seconds)):
            self.assertEqual(self.compact()[0], "COMPACT_COMPLETED")
        self.assertGreaterEqual(clock["now"], 900)
        self.assertLess(clock["now"], 1000)
        self.engine.send_chat.assert_called_once()
        self.cooldown.assert_not_called()  # Cooling belongs to the failover transition.

    def test_low_balance_after_compact_is_skipped_and_next_account_sends_work(self):
        self.engine.check_balance.side_effect = [99999, 0, 99999]
        calls, result, _, _, _ = self.worker_scenario(initial_due=True)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification"])
        self.assertEqual(calls[-1][1], self.accounts[2]["email"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertEqual(self.cooldown.call_count, 2)

    def test_unknown_balance_after_compact_keeps_existing_no_penalty_policy(self):
        self.engine.check_balance.side_effect = [99999, -1]
        calls, result, _, _, _ = self.worker_scenario(initial_due=True)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification"])
        self.assertEqual(calls[-1][1], self.accounts[1]["email"])
        self.assertEqual(result[1], "COMPLETED")
        self.cooldown.assert_called_once()  # A only, never punish B for -1.

    def test_threshold_uses_monotonic_span_at_exactly_180_seconds(self):
        self.assertEqual(bridge.COMPACT_TRIGGER_SECONDS, 180)
        self.cfg.account_journey_spans = [{"email": "x", "started_monotonic": 100.0}]
        with mock.patch.object(bridge.time, "monotonic", return_value=279.999):
            self.assertLess(bridge.current_account_duration(self.cfg, "x"), 180)
        with mock.patch.object(bridge.time, "monotonic", return_value=280.0):
            self.assertEqual(bridge.current_account_duration(self.cfg, "x"), 180)

    def test_same_project_new_summary_and_session_are_verified(self):
        self.cfg.compact_before_send = True
        status, pid, context = self.compact()
        self.assertEqual(status, "COMPACT_COMPLETED")
        self.assertEqual(pid, PID)
        self.assertEqual(context["chat_session_id"], "new-session")
        self.assertEqual(context["messages"], [SUMMARY])
        self.assertFalse(self.cfg.compact_before_send)
        self.assertFalse(self.cfg.compact_in_progress)
        self.assertEqual(self.engine.send_chat.call_args.args[1], "/compact")
        self.download.assert_not_called()

    def test_new_project_result_is_authoritative(self):
        self.engine.send_chat.return_value = (DONE, NEW_PID, "summary-result")
        status, pid, context = self.compact()
        self.assertEqual(status, "COMPACT_COMPLETED")
        self.assertEqual(pid, NEW_PID)
        self.assertEqual(context["project_id"], NEW_PID)
        self.assertEqual(self.engine.fetch_project_messages.call_args.args[0], NEW_PID)

    def test_finished_noop_does_not_require_a_new_summary(self):
        for messages in [[{"role": "assistant", "content": "Compact complete"}], [OLD_SUMMARY]]:
            with self.subTest(messages=messages):
                self.engine.fetch_project_messages.side_effect = None
                self.engine.fetch_project_messages.return_value = messages
                def fetch(pid, cookies, cfg):
                    cfg._last_fetch_status = 200
                    cfg._last_chat_session_id = "current-session"
                    return messages
                self.engine.fetch_project_messages.side_effect = fetch
                status, _, context = self.compact()
                self.assertEqual(status, "COMPACT_COMPLETED")
                self.assertFalse(context["summary_key"])

    def test_new_summary_without_current_session_is_not_success(self):
        def no_session(pid, cookies, cfg):
            self.fetch_count += 1
            return [] if self.fetch_count == 1 else [SUMMARY]
        self.engine.fetch_project_messages.side_effect = no_session
        self.assertEqual(self.compact()[0], "READ_FAILED")

    def test_cancel_before_send_and_during_stream_blocks_next_prompt(self):
        self.cfg.cancel_event = threading.Event()
        self.cfg.cancel_event.set()
        self.assertEqual(self.compact()[0], bridge.CANCELLED_STATUS)
        self.engine.send_chat.assert_not_called()
        self.cfg.cancel_event.clear()
        def cancel(*args, **kwargs):
            self.cfg.cancel_event.set()
            return bridge.USER_CANCELLED_MARKER, PID, None
        self.engine.send_chat.side_effect = cancel
        self.assertEqual(self.compact()[0], bridge.CANCELLED_STATUS)
        self.assertFalse(self.cfg.compact_in_progress)

    def test_optional_save_failure_does_not_block_completed_maintenance(self):
        self.cfg.compact_verified_callback = mock.Mock(side_effect=OSError("disk full"))
        self.cfg.compact_before_send = True
        self.assertEqual(self.compact()[0], "COMPACT_COMPLETED")
        self.assertFalse(self.cfg.compact_before_send)

    def test_compact_eligibility_survives_registry_reload(self):
        reg = self.isolated_registry()
        reg.set_compact_state(True, PID, 180, trigger_status="CREDIT_EXHAUSTED")
        self.assertTrue(bridge.ProjectRegistry(reg.key).get_compact_state()["due"])
        status, pid, context = self.compact()
        reg.set_compact_state(False, pid, context=context)
        state = bridge.ProjectRegistry(reg.key).get_compact_state()
        self.assertFalse(state["due"])
        self.assertEqual(state["chat_session_id"], "new-session")
        self.assertFalse((reg.root / "archive").exists())

    def test_actual_engine_fetch_pins_verified_history_without_network(self):
        source = (ROOT / "01.03Genspark_claude-opus-5-code.py").read_text(encoding="utf-8")
        function = next(n for n in ast.parse(source).body
                        if isinstance(n, ast.FunctionDef) and n.name == "fetch_project_messages")
        namespace = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "engine-fetch", "exec"), namespace)
        context = {"project_id": PID, "chat_session_id": "verified-session", "messages": [SUMMARY]}
        cfg = types.SimpleNamespace(_verified_compact_context=context)
        result = namespace["fetch_project_messages"](PID, {}, cfg)
        self.assertEqual(result, [SUMMARY])
        self.assertEqual(cfg._last_chat_session_id, "verified-session")
        result[0]["content"] = "changed copy"
        self.assertEqual(context["messages"][0]["content"], SUMMARY["content"])
        with self.assertRaises(RuntimeError):
            namespace["fetch_project_messages"](NEW_PID, {}, cfg)

    def worker_scenario(self, initial_due=False, first_duration=180, failure=False,
                        cancel=False, complete_only=False, resume_pid=PID,
                        fail_defer=False, restart=False, post_bypass_credit=False,
                        restored_state=None, fail_save=False, fail_identity=False):
        reg = self.isolated_registry("compact_worker")
        while len(self.accounts) < 6:
            i = len(self.accounts)
            self.accounts.append({**self.accounts[0], "email": f"account{i}@test.invalid",
                                  "cookies": {"session_id": f"account-{i}"}})
        if initial_due:
            reg.set_compact_state(True, PID, 180, trigger_status="CREDIT_EXHAUSTED")
        if restored_state is not None:
            data = reg._read()
            data["compact_state"] = restored_state
            reg._write(data)
        compact_pid = "33333333-3333-4333-8333-333333333333"
        calls, results, previews = [], [], []
        phase = {"compacted": False, "work_count": 0, "credit": False}
        ordinary = {"role": "assistant", "id": "ordinary-finished-reply", "content": "Compact unavailable",
                    "pending": False, "session_state": {"_finish_reason": "stop"}}
        real_failover = bridge.send_message_with_auto_account_failover
        def bind(cfg, *args, **kwargs):
            cfg.project_fast_lean_skip = True
            cfg.session_timeout = 0.03
            cfg.extracted_webapp_dir = self.root / "extracted"
            return {}
        bridge.apply_project_runtime_binding.side_effect = bind
        self.patch("claim_eligible_account_for_owner", side_effect=[
            (a, self.accounts, "claimed") for a in self.accounts])
        self.patch("release_account_selection")
        forks = []
        def fork(pid, *args, **kwargs):
            target = "44444444-4444-4444-8444-444444444444" if pid == compact_pid else NEW_PID
            forks.append((pid, target))
            return target
        self.patch("get_public_forked_pid", side_effect=fork)
        self.patch("make_project_always_public", side_effect=lambda pid, *a, **kw: bridge.build_genspark_viewer_url(pid))
        self.stack.enter_context(mock.patch.object(bridge.threading, "Thread"))
        self.patch("current_account_duration", side_effect=[first_duration] + [300] * 10)
        sends = self.patch("send_telegram_message")
        self.patch("edit_telegram_message_text")
        self.patch("send_telegram_message_detailed", side_effect=lambda *a, **kw: previews.append((a, kw)) or {"ok": False})
        snapshot = self.stack.enter_context(mock.patch.object(bridge.ProjectRegistry, "snapshot"))
        sync = self.stack.enter_context(mock.patch.object(bridge.ProjectRegistry, "github_sync"))
        scan = self.patch("should_capture_project_update", wraps=bridge.should_capture_project_update)
        if failure == "active":
            self.activity.return_value = {"active": True}
        if fail_defer:
            original_save = bridge.ProjectRegistry.set_compact_state
            def save(registry, *args, **kwargs):
                if kwargs.get("deferred"):
                    raise OSError("disk full")
                return original_save(registry, *args, **kwargs)
            self.stack.enter_context(mock.patch.object(bridge.ProjectRegistry, "set_compact_state", new=save))
        if fail_save:
            original_save = bridge.ProjectRegistry.set_compact_state
            def save_context(registry, *args, **kwargs):
                if kwargs.get("context") is not None:
                    raise OSError("post-maintenance disk failure")
                return original_save(registry, *args, **kwargs)
            self.stack.enter_context(mock.patch.object(bridge.ProjectRegistry, "set_compact_state", new=save_context))
        if fail_identity:
            original_identity = bridge.remember_registry_identity
            def save_identity(registry, **kwargs):
                if kwargs.get("status") == "COMPACT_COMPLETED":
                    raise OSError("identity disk failure")
                return original_identity(registry, **kwargs)
            self.patch("remember_registry_identity", side_effect=save_identity)
        def fetch(pid, cookies, cfg):
            cfg._last_fetch_status = 200
            cfg._last_chat_session_id = "verified-session" if phase["compacted"] else "old-session"
            if phase["credit"]:
                return [{"role": "assistant", "content": CREDIT,
                         "action": {"type": "ACTION_CREDIT_EXHAUSTED"}}]
            if phase["compacted"]:
                if failure == "no_session":
                    cfg._last_chat_session_id = ""
                if failure == "unreadable":
                    cfg._last_fetch_status = 503
                    return []
                if failure == "pending":
                    return [{**ordinary, "pending": True}]
                if failure == "stale":
                    return [OLD_SUMMARY]
                if failure == "user_last":
                    return [ordinary, {"role": "user", "content": "Still waiting"}]
                if failure == "compact_last":
                    return [ordinary, {"role": "user", "content": "/compact"}]
                if failure == "unconfirmed_credit":
                    return [{"role": "assistant", "content": "__CREDIT_EXHAUSTED__"}]
                if failure == "cancel_fetch":
                    cfg.cancel_event.set()
                return [copy.deepcopy(ordinary)] if failure else [SUMMARY]
            if pid == PID and not initial_due:
                return [{"role": "assistant", "content": CREDIT,
                         "action": {"type": "ACTION_CREDIT_EXHAUSTED"}}]
            return [OLD_SUMMARY]
        self.engine.fetch_project_messages.side_effect = fetch
        def chat(cookies, query, email, **kwargs):
            calls.append((query, email, kwargs.get("project_id")))
            cfg = kwargs["cfg"]
            if query == "/compact":
                phase["compacted"] = True
                phase["credit"] = False
                if cancel:
                    cfg.cancel_event.set()
                    return bridge.USER_CANCELLED_MARKER, compact_pid, None
                cfg._chat_attempt = {"request_id": "compact-request", "project_id": compact_pid,
                    "finished": failure not in ("pending", "stale", "user_last", "active", "unconfirmed_credit"),
                    "credit_exhausted": False, "old_message_ids": {"old-summary"}}
                return ("__CREDIT_EXHAUSTED__" if failure == "unconfirmed_credit" else "Compacted"), compact_pid, "summary"
            if not initial_due and len(calls) == 1:
                return (DONE if complete_only else CREDIT), PID, "first"
            if phase["compacted"]:
                self.assertIsNone(cfg._resume_context)
                self.assertIsNone(cfg._verified_compact_context)
                self.assertEqual(kwargs["project_id"], forks[-1][1])
                self.assertNotEqual(kwargs["project_id"], compact_pid)
                self.assertEqual(self.engine.fetch_project_messages.call_args.args[0], forks[-1][0])
                self.assertFalse(bridge.ProjectRegistry(reg.key).get_compact_state()["due"])
                self.assertNotEqual(email, next(c[1] for c in calls if c[0] == "/compact"))
            phase["work_count"] += 1
            phase["credit"] = post_bypass_credit and phase["work_count"] == 1
            return (CREDIT if phase["credit"] else DONE), kwargs["project_id"] or NEW_PID, "final"
        self.engine.send_chat.side_effect = chat
        def failover(**kwargs):
            result = real_failover(**kwargs)
            results.append(result)
            return result
        self.patch("send_message_with_auto_account_failover", side_effect=failover)
        bridge.process_user_task_async(12345, bridge.build_genspark_viewer_url(resume_pid) if initial_due else None,
                                       "User modification", project_key_hint=reg.key)
        if restart:
            bridge.process_user_task_async(12345, bridge.build_genspark_viewer_url(compact_pid),
                                           "Second user prompt", project_key_hint=reg.key)
        self.assertEqual(len(results), 2 if restart else 1, str(sends.call_args_list))
        self.download.assert_not_called()
        snapshot.assert_not_called()
        sync.assert_not_called()
        scan.assert_not_called()
        self.assertEqual(reg._read()["schema_version"], 1)
        return calls, results[-1], previews, reg, sends

    def test_credit_at_180_compacts_on_new_account_before_resume(self):
        calls, result, previews, reg, sends = self.worker_scenario()
        self.assertEqual([c[0] for c in calls], ["User modification", "/compact", "تابع"])
        self.assertEqual(calls[0][1], self.accounts[0]["email"])
        self.assertEqual(calls[1][1], self.accounts[1]["email"])
        self.assertEqual(calls[2][1], self.accounts[2]["email"])
        self.assertEqual(result[1], "COMPLETED")
        compact_cards = [item for item in previews if "/compact" in item[0][1]]
        self.assertTrue(compact_cards)
        markup = str(compact_cards[0][1]["reply_markup"])
        self.assertIn("cancel_prompt:", markup)
        self.assertIn("https://", markup)
        self.assertIn(self.accounts[1]["email"], compact_cards[0][0][1])

    def test_account_above_180_does_not_compact(self):
        calls, result, _, _, _ = self.worker_scenario(first_duration=180.001)
        self.assertEqual(len(calls), 2)
        self.assertNotIn("/compact", [c[0] for c in calls])
        self.assertEqual(result[1], "COMPLETED")

    def assert_credit_threshold(self, duration, expected_compact):
        calls, result, _, _, _ = self.worker_scenario(first_duration=duration)
        expected = ["User modification", "/compact", "تابع"] if expected_compact else ["User modification", "تابع"]
        self.assertEqual([call[0] for call in calls], expected)
        self.assertEqual(result[1], "COMPLETED")

    def test_55_second_credit_exhaustion_compacts(self):
        self.assert_credit_threshold(55, True)

    def test_90_second_credit_exhaustion_compacts(self):
        self.assert_credit_threshold(90, True)

    def test_just_below_180_credit_exhaustion_compacts(self):
        self.assert_credit_threshold(179.999, True)

    def test_zero_duration_uses_inclusive_owner_policy(self):
        self.assert_credit_threshold(0, True)

    def test_five_minute_credit_exhaustion_does_not_compact(self):
        self.assert_credit_threshold(300, False)

    def test_nine_minute_credit_exhaustion_does_not_compact(self):
        self.assert_credit_threshold(540, False)

    def assert_completion_threshold(self, duration, expected_due):
        calls, result, _, reg, _ = self.worker_scenario(complete_only=True, first_duration=duration)
        self.assertEqual([call[0] for call in calls], ["User modification"])
        self.assertEqual(result[1], "COMPLETED")
        state = bridge.ProjectRegistry(reg.key).get_compact_state()
        self.assertIs(state["due"], expected_due)
        self.assertEqual(state["duration_seconds"], 0.0)
        self.assertEqual(state["trigger_status"], "COMPLETED")

    def test_short_completion_clears_due_without_compact(self):
        self.assert_completion_threshold(55, False)

    def test_completion_just_above_180_persists_not_due(self):
        self.assert_completion_threshold(180.001, False)

    def test_five_minute_completion_persists_not_due(self):
        self.assert_completion_threshold(300, False)

    def test_nine_minute_completion_persists_not_due(self):
        self.assert_completion_threshold(540, False)

    def test_completed_run_clears_due_without_scheduling(self):
        calls, result, _, reg, _ = self.worker_scenario(complete_only=True)
        self.assertEqual([c[0] for c in calls], ["User modification"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(bridge.ProjectRegistry(reg.key).get_compact_state()["due"])

    def test_next_user_prompt_consumes_persisted_compact_eligibility(self):
        calls, result, _, _, _ = self.worker_scenario(initial_due=True)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification"])
        self.assertEqual(result[1], "COMPLETED")

    def test_finished_noop_rotates_then_sends_original_prompt_once(self):
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, failure=True)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification"])
        self.assertNotEqual(calls[0][1], calls[1][1])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(bridge.ProjectRegistry(reg.key).get_compact_state()["due"])
        self.cooldown.assert_called_once()

    def test_finished_noop_on_receiver_rotates_then_sends_resume_once(self):
        calls, result, _, reg, _ = self.worker_scenario(failure=True)
        self.assertEqual([c[0] for c in calls], ["User modification", "/compact", "تابع"])
        self.assertEqual(calls[1][1], self.accounts[1]["email"])
        self.assertEqual(calls[2][1], self.accounts[2]["email"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(reg.get_compact_state()["due"])
        self.assertEqual(self.cooldown.call_count, 2)

    def test_deferred_session_survives_new_worker_without_recompacting(self):
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, failure=True, restart=True)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification", "Second user prompt"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(bridge.ProjectRegistry(reg.key).get_compact_state().get("deferred", False))
        self.assertFalse(reg.get_compact_state()["due"])

    def test_long_credit_after_maintenance_resumes_without_recompacting(self):
        calls, result, _, reg, _ = self.worker_scenario(
            initial_due=True, failure=True, post_bypass_credit=True, first_duration=300)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification", "تابع"])
        self.assertEqual(calls[-1][1], self.accounts[2]["email"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(reg.get_compact_state()["due"])
        self.assertEqual(len(reg._read()["updates"]), 1)
        self.assertEqual(self.cooldown.call_count, 2)

    def assert_bypass_blocked(self, failure):
        calls, result, _, reg, sends = self.worker_scenario(initial_due=True, failure=failure)
        self.assertEqual([c[0] for c in calls], ["/compact"])
        self.assertEqual(result[1], "COMPACT_HANDOFF_BLOCKED" if failure in ("no_session", "unreadable") else "TIMEOUT")
        self.assertFalse(reg.get_compact_state()["due"])
        self.assertFalse(reg.get_compact_state()["bypass_ready"])
        self.assertNotIn("تم التوليد بنجاح", str(sends.call_args_list))
        if failure in ("no_session", "unreadable"):
            self.cooldown.assert_called_once()  # Terminal maintenance, failed handoff read.
        else:
            self.cooldown.assert_not_called()

    def test_stale_summary_without_finished_turn_blocks_bypass(self):
        self.assert_bypass_blocked("stale")

    def test_absent_current_session_blocks_bypass(self):
        self.assert_bypass_blocked("no_session")

    def test_unreadable_history_blocks_bypass(self):
        self.assert_bypass_blocked("unreadable")

    def test_pending_turn_blocks_bypass(self):
        self.assert_bypass_blocked("pending")

    def test_latest_user_turn_blocks_bypass(self):
        self.assert_bypass_blocked("user_last")

    def test_active_generation_blocks_bypass(self):
        self.assert_bypass_blocked("active")

    def test_trigger_save_failure_stops_before_compact(self):
        calls, result, _, _, _ = self.worker_scenario(initial_due=True, failure=True, fail_defer=True)
        self.assertEqual(calls, [])
        self.assertEqual(result[1], "COMPACT_HANDOFF_BLOCKED")
        self.assertTrue(result[0])
        self.cooldown.assert_not_called()

    def test_unconfirmed_credit_in_bypass_does_not_rotate_or_send(self):
        calls, result, _, _, _ = self.worker_scenario(initial_due=True, failure="unconfirmed_credit")
        self.assertEqual([c[0] for c in calls], ["/compact"])
        self.assertEqual(result[1], "CREDIT_UNCONFIRMED")
        self.cooldown.assert_not_called()

    def test_cancel_during_post_compact_fetch_never_sends_work(self):
        calls, result, _, _, _ = self.worker_scenario(initial_due=True, failure="cancel_fetch")
        self.assertEqual([c[0] for c in calls], ["/compact"])
        self.assertEqual(result[1], bridge.CANCELLED_STATUS)
        self.cooldown.assert_not_called()

    def test_deferred_metadata_preserves_v1_manifest_and_session_scope(self):
        reg = self.isolated_registry()
        before = reg._read()
        reg.set_compact_state(False, PID, deferred=True, chat_session_id="same", bypass_ready=True)
        reg = bridge.ProjectRegistry(reg.key)
        reg.set_compact_state(True, NEW_PID, 55, chat_session_id="same")
        self.assertFalse(reg.get_compact_state()["due"])
        self.assertTrue(reg.get_compact_state()["bypass_ready"])
        reg.set_compact_state(True, NEW_PID, 55)  # Unknown session must not clear deferral.
        self.assertFalse(reg.get_compact_state()["due"])
        after = reg._read()
        self.assertEqual(after["schema_version"], 1)
        for key in ("project_settings", "file_index", "checkpoints", "updates"):
            self.assertEqual(after[key], before[key])
        reg.set_compact_state(True, NEW_PID, 55, chat_session_id="distinct-session")
        self.assertTrue(reg.get_compact_state()["due"])
        self.assertNotIn("deferred", reg.get_compact_state())

    def test_restart_fresh_fork_bypasses_inherited_wait_without_recompacting(self):
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, failure="stale", restart=True)
        self.assertEqual([c[0] for c in calls], ["/compact", "Second user prompt"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(reg.get_compact_state()["due"])
        self.assertEqual(reg.get_compact_state()["trigger_status"], "COMPLETED")

    def test_legacy_due_and_deferred_state_does_not_repeat_compact(self):
        state = {"due": True, "deferred": True, "source_pid": PID,
                 "chat_session_id": "old-session"}
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, restored_state=state)
        self.assertEqual([c[0] for c in calls], ["User modification"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(reg.get_compact_state()["due"])

    def test_schedule_write_error_preserves_credit_checkpoint_but_stops_handoff(self):
        self.patch("current_account_duration", return_value=55)
        self.patch("claim_eligible_account_for_owner", side_effect=[
            (a, self.accounts, "claimed") for a in self.accounts])
        release = self.patch("release_account_selection")
        pipeline = self.patch("send_message_and_make_public", side_effect=[
            (URL, "CREDIT_EXHAUSTED", None, CREDIT, None),
            (URL, "COMPLETED", None, DONE, None)])
        self.cfg.compact_schedule_callback = mock.Mock(side_effect=OSError("disk full"))
        progress = mock.Mock(return_value={"allow_continuation": True,
                                          "project_update_preserved": True})
        result = bridge.send_message_with_auto_account_failover(
            None, "Original work", bridge_cfg=self.cfg, progress_callback=progress)
        self.assertEqual(result[1], "COMPACT_HANDOFF_BLOCKED")
        self.assertEqual(result[0], URL)
        self.assertEqual(pipeline.call_count, 1)
        self.assertEqual(pipeline.call_args.kwargs["query"], "Original work")
        self.assertEqual(progress.call_args_list[0].args[1], "CREDIT_EXHAUSTED")
        self.assertFalse(self.cfg.compact_before_send)
        self.assertTrue(self.cfg.compact_state_save_failed)
        self.cooldown.assert_called_once()
        self.assertEqual(release.call_count, 1)

    def test_verified_compact_clears_deferred_metadata(self):
        reg = self.isolated_registry()
        reg.set_compact_state(False, PID, deferred=True, chat_session_id="same")
        context = {"chat_session_id": "verified", "summary_key": "fresh"}
        reg.set_compact_state(False, PID, context=context)
        self.assertTrue(reg.get_compact_state()["verified"])
        self.assertNotIn("deferred", reg.get_compact_state())

    def test_pending_compact_from_different_source_is_cleared(self):
        calls, result, _, _, _ = self.worker_scenario(initial_due=True, resume_pid=NEW_PID)
        self.assertEqual([c[0] for c in calls], ["User modification"])
        self.assertEqual(result[1], "COMPLETED")

    def test_platform_credit_during_compact_remains_credit_exhausted(self):
        def fetch(pid, cookies, cfg):
            self.fetch_count += 1
            cfg._last_fetch_status = 200
            return [OLD_SUMMARY] if self.fetch_count == 1 else [
                {"role": "assistant", "content": CREDIT,
                 "action": {"type": "ACTION_CREDIT_EXHAUSTED"}}]
        self.engine.fetch_project_messages.side_effect = fetch
        self.cfg.compact_before_send = True
        def credit(*args, **kwargs):
            kwargs["cfg"]._chat_attempt = {"request_id": "compact", "project_id": PID,
                                          "credit_exhausted": True, "finished": False}
            return "__CREDIT_EXHAUSTED__", PID, None
        self.engine.send_chat.side_effect = credit
        self.assertEqual(self.compact()[0], "CREDIT_EXHAUSTED")
        self.assertTrue(self.cfg.compact_before_send)

    def test_cancel_during_compact_never_sends_user_prompt(self):
        calls, result, _, _, _ = self.worker_scenario(initial_due=True, cancel=True)
        self.assertEqual([c[0] for c in calls], ["/compact"])
        self.assertEqual(result[1], bridge.CANCELLED_STATUS)
        self.cooldown.assert_not_called()

    def test_finished_compact_trailing_user_turn_rotates_and_dispatches(self):
        # Current compact terminal evidence authorizes maintenance handoff,
        # not an old assistant reply or work on the maintenance account.
        calls, result, _, reg, sends = self.worker_scenario(initial_due=True, failure="compact_last")
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(reg.get_compact_state()["due"])
        self.assertEqual(reg.get_compact_state()["trigger_status"], "COMPLETED")
        self.assertNotEqual(calls[0][1], calls[1][1])
        self.assertIn("تم التوليد بنجاح", str(sends.call_args_list))
        self.cooldown.assert_called_once()


    def test_har_user_role_compact_summary_is_verified_and_accepted_by_engine(self):
        # HAR entry 70 line 36: Genspark returns summary as role="user" with is_compact_summary: True
        user_summary = {
            "role": "user",
            "id": "har-user-summary-70",
            "content": "Full compact summary content from Genspark SSE",
            "session_state": {"is_compact_summary": True},
        }
        self.fetch_count = 0
        def fetch(pid, cookies, cfg):
            self.fetch_count += 1
            cfg._last_fetch_status = 200
            cfg._last_chat_session_id = "har-session-123"
            return [OLD_SUMMARY] if self.fetch_count == 1 else [user_summary]
        self.engine.fetch_project_messages.side_effect = fetch
        self.cfg.compact_before_send = True
        status, pid, context = self.compact()
        self.assertEqual(status, "COMPACT_COMPLETED")
        self.assertEqual(pid, PID)
        self.assertEqual(context["chat_session_id"], "har-session-123")
        self.assertEqual(context["messages"], [user_summary])

        # Test engine monolith acceptance via fetch_project_messages
        import importlib.util
        spec = importlib.util.spec_from_file_location("engine_monolith", ROOT / "01.03Genspark_claude-opus-5-code.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        verified_ctx = {
            "project_id": PID,
            "chat_session_id": "har-session-123",
            "messages": [user_summary],
        }
        self.cfg._verified_compact_context = verified_ctx
        resolved = mod.fetch_project_messages(PID, {}, self.cfg)
        self.assertEqual(resolved, [user_summary])


if __name__ == "__main__":
    unittest.main()


class ApprovedCompactPolicyTests(unittest.TestCase):
    patch = base.CreditRecoveryTests.patch
    archive = base.CreditRecoveryTests.archive
    isolated_registry = base.CreditRecoveryTests.isolated_registry

    def setUp(self):
        base.CreditRecoveryTests.setUp(self)
        self.cfg.project_fast_lean_skip = True
        self.patch("claim_eligible_account_for_owner", side_effect=[
            (a, self.accounts, "claimed") for a in self.accounts])
        self.release = self.patch("release_account_selection")

    def maintenance_sender(self):
        self.cfg.compact_handoff_saved = True
        return self.patch("send_message_and_make_public", return_value=(URL, "COMPACT_COMPLETED", None, "", None))

    def test_cooldown_failure_returns_public_url_without_next_account(self):
        sender = self.maintenance_sender()
        for failure in (False, OSError("cannot save cooldown")):
            with self.subTest(failure=type(failure).__name__):
                bridge.claim_eligible_account_for_owner.side_effect = [(self.accounts[0], self.accounts, "claimed")]
                sender.reset_mock()
                self.cooldown.side_effect = failure if isinstance(failure, Exception) else None
                self.cooldown.return_value = False
                result = bridge.send_message_with_auto_account_failover(URL, "Work", bridge_cfg=self.cfg)
                self.assertEqual(result[:2], (URL, "COMPACT_HANDOFF_BLOCKED"))
                sender.assert_called_once()

    def test_missing_handoff_save_never_sends_work_on_another_account(self):
        sender = self.maintenance_sender()
        self.cfg.compact_handoff_saved = False
        result = bridge.send_message_with_auto_account_failover(URL, "Work", bridge_cfg=self.cfg)
        self.assertEqual(result[:2], (URL, "COMPACT_HANDOFF_BLOCKED"))
        sender.assert_called_once()
        self.cooldown.assert_called_once()

    def test_no_next_account_keeps_maintenance_public_url(self):
        sender = self.maintenance_sender()
        for reason, expected in (("no-eligible", "ALL_ACCOUNTS_IN_COOLDOWN"), ("busy", "ALL_ACCOUNTS_BUSY")):
            with self.subTest(reason=reason):
                bridge.claim_eligible_account_for_owner.side_effect = [
                    (self.accounts[0], self.accounts, "claimed"), (None, [], reason)]
                sender.reset_mock()
                self.cfg.max_account_attempts = 2
                result = bridge.send_message_with_auto_account_failover(URL, "Work", bridge_cfg=self.cfg)
                self.assertEqual(result[:2], (URL, expected))
                sender.assert_called_once()
        bridge.claim_eligible_account_for_owner.side_effect = [(self.accounts[0], self.accounts, "claimed")]
        self.cfg.max_account_attempts = 1
        result = bridge.send_message_with_auto_account_failover(URL, "Work", bridge_cfg=self.cfg)
        self.assertEqual(result[:2], (URL, "MAX_ATTEMPTS_EXHAUSTED"))

    def test_same_pid_and_failed_fork_do_not_bypass_readiness(self):
        self.cfg.compact_deferred = self.cfg.compact_bypass_blocked = True
        fork = self.patch("get_public_forked_pid")
        self.stack.enter_context(mock.patch.object(bridge.threading, "Thread"))
        monitor = self.patch("monitor_chat_completion", return_value=("TIMEOUT", ""))
        for fork_pid in (None, PID, "__INVALID_PROJECT__"):
            with self.subTest(fork=fork_pid):
                fork.return_value = fork_pid
                result = bridge.send_message_and_make_public(URL, self.accounts[0]["email"], "test-only", "Work", self.cfg)
                self.assertEqual(result[1], "TIMEOUT")
                self.assertTrue(monitor.call_args.kwargs["readiness"])
        self.engine.send_chat.assert_not_called()

    def test_cancellation_after_maintenance_prevents_next_account_claim(self):
        sender = self.maintenance_sender()
        self.cfg.cancel_event = threading.Event()
        self.cooldown.side_effect = lambda *a, **kw: self.cfg.cancel_event.set() or True
        result = bridge.send_message_with_auto_account_failover(URL, "Work", bridge_cfg=self.cfg)
        self.assertEqual(result[:2], (URL, bridge.CANCELLED_STATUS))
        sender.assert_called_once()
        bridge.claim_eligible_account_for_owner.assert_called_once()

    def test_completion_clear_failure_is_explicit_and_retains_real_result(self):
        self.patch("send_message_and_make_public", return_value=(URL, "COMPLETED", None, DONE, None))
        self.cfg.compact_clear_callback = mock.Mock(side_effect=OSError("clear failed"))
        result = bridge.send_message_with_auto_account_failover(URL, "Work", bridge_cfg=self.cfg)
        self.assertEqual(result[:2], (URL, "COMPACT_HANDOFF_BLOCKED"))
        self.assertEqual(result[-1], DONE)
        self.cooldown.assert_not_called()

    def test_cancel_precedes_pending_metadata_failure_in_sender(self):
        self.cfg.cancel_event = threading.Event()
        self.cfg.cancel_event.set()
        self.cfg.compact_state_save_failed = True
        result = bridge.send_message_and_make_public(URL, self.accounts[0]["email"], "test-only", "Work", self.cfg)
        self.assertEqual(result[1], bridge.CANCELLED_STATUS)
        self.engine.send_chat.assert_not_called()
        self.cooldown.assert_not_called()

    def test_completed_never_schedules_compact(self):
        self.patch("current_account_duration", return_value=55)
        self.patch("send_message_and_make_public", return_value=(URL, "COMPLETED", None, DONE, None))
        self.cfg.compact_before_send = True
        self.cfg.compact_schedule_callback = mock.Mock()
        self.cfg.compact_clear_callback = mock.Mock()
        result = bridge.send_message_with_auto_account_failover(None, "Work", bridge_cfg=self.cfg)
        self.assertEqual(result[1], "COMPLETED")
        self.cfg.compact_schedule_callback.assert_not_called()
        self.cfg.compact_clear_callback.assert_called_once_with(URL)
        self.assertFalse(self.cfg.compact_before_send)

    def test_fresh_fork_skips_only_inherited_readiness(self):
        self.cfg.compact_deferred = self.cfg.compact_bypass_blocked = True
        self.patch("get_public_forked_pid", return_value=NEW_PID)
        self.stack.enter_context(mock.patch.object(bridge.threading, "Thread"))
        self.engine.send_chat.return_value = (DONE, NEW_PID, "reply")
        monitor = self.patch("monitor_chat_completion", side_effect=lambda *a, **kw:
                             ("TIMEOUT" if kw.get("readiness") else "COMPLETED", DONE))
        result = bridge.send_message_and_make_public(URL, self.accounts[0]["email"], "test-only",
                                                      "Original query", self.cfg)
        self.assertEqual(result[1], "COMPLETED")
        self.engine.send_chat.assert_called_once()
        self.assertEqual(self.engine.send_chat.call_args.args[1], "Original query")
        self.assertFalse(any(c.kwargs.get("readiness") for c in monitor.call_args_list))

    def test_successful_maintenance_rotates_before_work_without_credit_increment(self):
        self.cfg.compact_handoff_saved = True
        latest = bridge.build_genspark_viewer_url(NEW_PID)
        sender = self.patch("send_message_and_make_public", side_effect=[
            (latest, "COMPACT_COMPLETED", None, "", None),
            (latest, "COMPLETED", None, DONE, None)])
        result = bridge.send_message_with_auto_account_failover(URL, "Original work", bridge_cfg=self.cfg)
        self.assertEqual(result[1], "COMPLETED")
        self.assertEqual(sender.call_count, 2)
        self.assertEqual(sender.call_args.kwargs["query"], "Original work")
        self.assertEqual(sender.call_args.kwargs["url"], latest)
        self.assertNotEqual(sender.call_args_list[0].kwargs["email"], sender.call_args.kwargs["email"])
        self.cooldown.assert_called_once()
        self.assertEqual(self.cfg.last_credit_continuations, 0)
        self.assertEqual(self.release.call_count, 2)


class SharedCompletionTests(unittest.TestCase):
    patch = base.CreditRecoveryTests.patch
    archive = base.CreditRecoveryTests.archive
    run_pipeline = base.CreditRecoveryTests.run_pipeline

    def setUp(self):
        base.CreditRecoveryTests.setUp(self)
        self.cfg.project_fast_lean_skip = True
        self.engine.CHAT_ATTEMPT_EVIDENCE_SUPPORTED = True
        self.runtime = types.SimpleNamespace(_chat_attempt={
            "request_id": "this-request", "project_id": PID, "chat_session_id": "session",
            "old_message_ids": {"old-reply"}, "message_ids": {"reply"},
            "finished": False, "credit_exhausted": False})
        self.count = 0

    def reply(self, text=DONE, **fields):
        return {"id": "reply", "role": "assistant", "content": text, **fields}

    def monitor(self, answer="__STREAM_INTERRUPTED__", **kwargs):
        return bridge.monitor_chat_completion(self.engine, {}, self.runtime, self.cfg,
            PID, answer, bridge.time.time(), **kwargs)

    def test_maintenance_and_business_timeouts_use_same_full_budget(self):
        self.cfg.session_timeout = 1000
        self.engine.fetch_project_messages.return_value = [self.reply("Working, not terminal")]
        for maintenance in (False, True):
            with self.subTest(maintenance=maintenance):
                clock = {"now": 0.0}
                with mock.patch.object(bridge.time, "time", side_effect=lambda: clock["now"]), \
                     mock.patch.object(bridge.time, "sleep", side_effect=lambda seconds: clock.update(now=clock["now"]+seconds)):
                    status, _ = self.monitor(maintenance=maintenance)
                self.assertEqual(status, "TIMEOUT")
                self.assertEqual(clock["now"], 1000)
        self.engine.send_chat.assert_not_called()
        self.cooldown.assert_not_called()

    def test_initial_and_polling_credit_suspicion_keep_monitoring_same_request(self):
        for initial in ("__CREDIT_EXHAUSTED__", "__STREAM_INTERRUPTED__"):
            with self.subTest(initial=initial):
                self.count = 0
                self.activity.return_value = {"active": True, "deep_thinking": True, "tasks_remaining": 2}
                def fetch(pid, cookies, cfg):
                    self.count += 1
                    return [self.reply("used all your credits", **(
                        {"action": {"type": "ACTION_CREDIT_EXHAUSTED"}} if self.count >= 4 else {}))]
                self.engine.fetch_project_messages.side_effect = fetch
                status, _ = self.monitor(initial)
                self.assertEqual(status, "CREDIT_EXHAUSTED")
                self.assertGreaterEqual(self.count, 4)
                self.engine.send_chat.assert_not_called()
                self.cooldown.assert_not_called()

    def test_partial_text_cannot_become_completed_at_timeout_or_resend(self):
        self.cfg.max_timeout_retries = 3
        def chat(*args, **kwargs):
            kwargs["cfg"]._chat_attempt = dict(self.runtime._chat_attempt)
            return "Still working on the files and the requested tests", PID, "reply"
        self.engine.send_chat.side_effect = chat
        self.engine.fetch_project_messages.return_value = [self.reply("Still working on the files and the requested tests")]
        result = self.run_pipeline()
        self.assertEqual(result[1], "TIMEOUT")
        self.engine.send_chat.assert_called_once()
        self.download.assert_not_called()
        self.saved_branch.assert_not_called()

    def test_unknown_activity_is_not_completion_without_terminal_evidence(self):
        self.engine.fetch_project_messages.return_value = [self.reply()]
        self.assertEqual(self.monitor()[0], "TIMEOUT")

    def test_later_current_finished_reply_resolves_text_only_suspicion(self):
        self.count = 0
        def fetch(*args):
            self.count += 1
            return [self.reply("Documentation: used all your credits", **(
                {"session_state": {"_finish_reason": "stop"}} if self.count >= 3 else {}))]
        self.engine.fetch_project_messages.side_effect = fetch
        self.assertEqual(self.monitor("__CREDIT_EXHAUSTED__")[0], "COMPLETED")
        self.assertGreaterEqual(self.count, 3)
        self.cooldown.assert_not_called()

    def test_old_finished_or_credit_reply_and_newer_user_turn_are_not_current(self):
        old = {"id": "old-reply", "role": "assistant", "content": CREDIT,
               "action": {"type": "ACTION_CREDIT_EXHAUSTED"}}
        self.assertIsNone(bridge.current_attempt_reply([old], self.runtime._chat_attempt))
        self.assertIsNone(bridge.current_attempt_reply([
            self.reply(), {"id": "another-request", "role": "user", "content": "/compact"}],
            self.runtime._chat_attempt))
        self.assertIsNone(bridge.current_attempt_reply([
            {"id": "unobserved", "role": "assistant", "content": DONE}], self.runtime._chat_attempt))

    def test_fresh_request_identity_allows_polling_after_early_stream_disconnect(self):
        self.runtime._chat_attempt["message_ids"] = set()
        self.engine.fetch_project_messages.return_value = [
            {"role": "user", "id": "this-request", "content": "Work"},
            self.reply(session_state={"_finish_reason": "stop"})]
        self.assertEqual(self.monitor()[0], "COMPLETED")

    def test_cancel_during_read_and_wait_returns_without_another_send(self):
        self.cfg.cancel_event = threading.Event()
        def fetch(*args):
            self.cfg.cancel_event.set()
            return [self.reply()]
        self.engine.fetch_project_messages.side_effect = fetch
        self.assertEqual(self.monitor()[0], bridge.CANCELLED_STATUS)
        self.engine.send_chat.assert_not_called()

    def test_p18_stops_maintenance_without_authorizing_pending_business_send(self):
        self.activity.side_effect = [{"active": True, "deep_thinking": True, "tasks_remaining": 2},
                                    {"active": True, "deep_thinking": True, "tasks_remaining": 1}]
        self.engine.fetch_project_messages.return_value = [self.reply()]
        self.assertEqual(self.monitor(maintenance=True)[0], "ACTIVITY_STOPPED")
        self.assertEqual(self.activity.call_count, 2)

    def test_ready_legacy_compact_never_uses_old_credit(self):
        self.runtime._chat_attempt = None
        def fetch(pid, cookies, cfg):
            cfg._last_fetch_status = 200
            cfg._last_fetch_project_id = pid
            cfg._last_fetch_authoritative = True
            cfg._last_project_status = "FINISHED"
            cfg._last_chat_session_id = "current-session"
            return [{"role": "assistant", "content": CREDIT, "action": {"type": "ACTION_CREDIT_EXHAUSTED"}},
                    {"role": "user", "content": "/compact"}]
        self.engine.fetch_project_messages.side_effect = fetch
        self.assertEqual(self.monitor(readiness=True)[0], "COMPLETED")
        self.engine.send_chat.assert_not_called()

    def test_collapsed_summary_and_project_finished_need_no_finish_reason(self):
        self.runtime._chat_attempt["summary_ids"] = {"new-summary"}
        def fetch(pid, cookies, cfg):
            cfg._last_fetch_status = 200
            cfg._last_fetch_project_id = pid
            cfg._last_fetch_authoritative = True
            cfg._last_project_status = "FINISHED"
            cfg._last_chat_session_id = "new-session"
            return [{"id": "new-summary", "role": "user", "content": "Summary",
                     "session_state": {"is_compact_summary": True}}, self.reply("")]
        self.engine.fetch_project_messages.side_effect = fetch
        self.assertEqual(self.monitor(maintenance=True)[0], "COMPLETED")

    def test_legacy_bypass_false_ready_project_dispatches_original_once(self):
        self.cfg.compact_deferred = True
        self.cfg.compact_bypass_blocked = True
        self.cfg.compact_before_send = True
        self.patch("get_public_forked_pid", return_value=PID)
        self.stack.enter_context(mock.patch.object(bridge.threading, "Thread"))
        def fetch(pid, cookies, cfg):
            cfg._last_fetch_status = 200
            cfg._last_fetch_project_id = pid
            cfg._last_fetch_authoritative = True
            cfg._last_project_status = "FINISHED"
            cfg._last_chat_session_id = "current-session"
            return [{"role": "user", "content": "/compact"}]
        self.engine.fetch_project_messages.side_effect = fetch
        def chat(*args, **kwargs):
            kwargs["cfg"]._chat_attempt = {**self.runtime._chat_attempt, "finished": True}
            return DONE, PID, "reply"
        self.engine.send_chat.side_effect = chat
        result = bridge.send_message_and_make_public(URL, self.accounts[0]["email"], "test-only",
                                                      "Original prompt", bridge_cfg=self.cfg)
        self.assertEqual(result[1], "COMPLETED")
        self.engine.send_chat.assert_called_once()
        self.assertEqual(self.engine.send_chat.call_args.args[1], "Original prompt")
        self.assertEqual(self.engine.send_chat.call_args.kwargs["project_id"], PID)
        self.download.assert_not_called()
