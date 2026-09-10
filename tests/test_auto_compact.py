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
        self.patch("COMPACT_VERIFY_READS", new=2)
        self.runtime = types.SimpleNamespace(cancel_event=None)
        self.engine.send_chat.return_value = (DONE, PID, "summary-result")
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
        self.assertEqual(status, "COMPACT_VERIFIED")
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
        self.assertEqual(status, "COMPACT_VERIFIED")
        self.assertEqual(pid, NEW_PID)
        self.assertEqual(context["project_id"], NEW_PID)
        self.assertEqual(self.engine.fetch_project_messages.call_args.args[0], NEW_PID)

    def test_plain_reply_or_stale_summary_never_claims_verified_compact(self):
        for messages in [[{"role": "assistant", "content": "Compact complete"}], [OLD_SUMMARY]]:
            with self.subTest(messages=messages):
                self.engine.fetch_project_messages.side_effect = None
                self.engine.fetch_project_messages.return_value = messages
                self.assertEqual(self.compact()[0], "COMPACT_FAILED")

    def test_new_summary_without_current_session_is_not_success(self):
        def no_session(pid, cookies, cfg):
            self.fetch_count += 1
            return [] if self.fetch_count == 1 else [SUMMARY]
        self.engine.fetch_project_messages.side_effect = no_session
        self.assertEqual(self.compact()[0], "COMPACT_FAILED")

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

    def test_disk_failure_after_verification_blocks_next_prompt(self):
        self.cfg.compact_verified_callback = mock.Mock(side_effect=OSError("disk full"))
        self.cfg.compact_before_send = True
        self.assertEqual(self.compact()[0], "COMPACT_FAILED")
        self.assertTrue(self.cfg.compact_before_send)

    def test_compact_eligibility_survives_registry_reload(self):
        reg = self.isolated_registry()
        reg.set_compact_state(True, PID, 180)
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
                        restored_state=None):
        reg = self.isolated_registry("compact_worker")
        if initial_due:
            reg.set_compact_state(True, PID, 180)
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
            cfg.extracted_webapp_dir = self.root / "extracted"
            return {}
        bridge.apply_project_runtime_binding.side_effect = bind
        self.patch("claim_eligible_account_for_owner", side_effect=[
            (a, self.accounts, "claimed") for a in self.accounts])
        self.patch("release_account_selection")
        self.patch("get_public_forked_pid", return_value=NEW_PID)
        self.patch("make_project_always_public", side_effect=lambda pid, *a, **kw: bridge.build_genspark_viewer_url(pid))
        self.stack.enter_context(mock.patch.object(bridge.threading, "Thread"))
        self.patch("current_account_duration", side_effect=[first_duration, 0])
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
                if cancel:
                    cfg.cancel_event.set()
                    return bridge.USER_CANCELLED_MARKER, compact_pid, None
                return "Compacted", compact_pid, "summary"
            if not initial_due and len(calls) == 1:
                return (DONE if complete_only else CREDIT), PID, "first"
            if phase["compacted"] and failure:
                self.assertIsNone(cfg._verified_compact_context)
                if phase["work_count"] == 0:
                    self.assertEqual(kwargs["project_id"], compact_pid)
                    self.assertEqual(kwargs["history"], [ordinary])
                    self.assertEqual(cfg._last_chat_session_id, "verified-session")
                    saved = bridge.ProjectRegistry(reg.key).get_compact_state()
                    self.assertFalse(saved["due"])
                    self.assertTrue(saved["deferred"])
                    self.assertFalse(saved["verified"])
                    self.assertTrue(saved["bypass_ready"])
                cfg._last_chat_session_id = "verified-session"
            elif first_duration <= bridge.COMPACT_TRIGGER_SECONDS or initial_due:
                pinned = cfg._verified_compact_context
                self.assertEqual(kwargs["project_id"], compact_pid)
                self.assertEqual(pinned["chat_session_id"], "verified-session")
                self.assertEqual(pinned["messages"], [SUMMARY])
            phase["work_count"] += 1
            phase["credit"] = post_bypass_credit and phase["work_count"] == 1
            return (CREDIT if phase["credit"] else DONE), compact_pid if phase["compacted"] else NEW_PID, "final"
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
        self.assertEqual(calls[2][1], self.accounts[1]["email"])
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
        self.assertEqual(state["duration_seconds"], duration)

    def test_short_completion_persists_due_without_immediate_compact(self):
        self.assert_completion_threshold(55, True)

    def test_completion_just_above_180_persists_not_due(self):
        self.assert_completion_threshold(180.001, False)

    def test_five_minute_completion_persists_not_due(self):
        self.assert_completion_threshold(300, False)

    def test_nine_minute_completion_persists_not_due(self):
        self.assert_completion_threshold(540, False)

    def test_completed_run_only_schedules_without_sending_compact(self):
        calls, result, _, reg, _ = self.worker_scenario(complete_only=True)
        self.assertEqual([c[0] for c in calls], ["User modification"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertTrue(bridge.ProjectRegistry(reg.key).get_compact_state()["due"])

    def test_next_user_prompt_consumes_persisted_compact_eligibility(self):
        calls, result, _, _, _ = self.worker_scenario(initial_due=True)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification"])
        self.assertEqual(result[1], "COMPLETED")

    def test_unverified_compact_safely_sends_original_prompt_once(self):
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, failure=True)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification"])
        self.assertEqual(calls[0][1], calls[1][1])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(bridge.ProjectRegistry(reg.key).get_compact_state()["due"])
        self.cooldown.assert_not_called()

    def test_unverified_compact_on_receiver_sends_resume_once(self):
        calls, result, _, reg, _ = self.worker_scenario(failure=True)
        self.assertEqual([c[0] for c in calls], ["User modification", "/compact", "تابع"])
        self.assertEqual(calls[1][1], self.accounts[1]["email"])
        self.assertEqual(calls[2][1], self.accounts[1]["email"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(reg.get_compact_state()["due"])
        self.cooldown.assert_called_once()

    def test_deferred_session_survives_new_worker_without_recompacting(self):
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, failure=True, restart=True)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification", "Second user prompt"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertTrue(bridge.ProjectRegistry(reg.key).get_compact_state()["deferred"])
        self.assertFalse(reg.get_compact_state()["due"])

    def test_credit_after_bypass_keeps_real_failover_without_recompacting(self):
        calls, result, _, reg, _ = self.worker_scenario(
            initial_due=True, failure=True, post_bypass_credit=True)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification", "تابع"])
        self.assertEqual(calls[-1][1], self.accounts[1]["email"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(reg.get_compact_state()["due"])
        self.assertEqual(len(reg._read()["updates"]), 1)
        self.cooldown.assert_called_once()

    def assert_bypass_blocked(self, failure):
        calls, result, _, reg, sends = self.worker_scenario(initial_due=True, failure=failure)
        self.assertEqual([c[0] for c in calls], ["/compact"])
        self.assertEqual(result[1], "COMPACT_BLOCKED")
        self.assertFalse(reg.get_compact_state()["due"])
        self.assertFalse(reg.get_compact_state()["bypass_ready"])
        self.assertNotIn("تم التوليد بنجاح", str(sends.call_args_list))
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

    def test_deferred_write_failure_never_sends_business_prompt(self):
        calls, result, _, _, _ = self.worker_scenario(initial_due=True, failure=True, fail_defer=True)
        self.assertEqual([c[0] for c in calls], ["/compact"])
        self.assertEqual(result[1], "COMPACT_BLOCKED")
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

    def test_blocked_restart_rechecks_readiness_without_repeating_compact(self):
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, failure="stale", restart=True)
        self.assertEqual([c[0] for c in calls], ["/compact"])
        self.assertEqual(result[1], "COMPACT_BLOCKED")
        self.assertFalse(reg.get_compact_state()["due"])
        self.assertFalse(reg.get_compact_state()["bypass_ready"])

    def test_legacy_due_and_deferred_state_does_not_repeat_compact(self):
        state = {"due": True, "deferred": True, "source_pid": PID,
                 "chat_session_id": "old-session"}
        calls, result, _, reg, _ = self.worker_scenario(initial_due=True, restored_state=state)
        self.assertEqual(calls, [])
        self.assertEqual(result[1], "COMPACT_BLOCKED")
        self.assertFalse(reg.get_compact_state()["due"])

    def test_schedule_write_error_does_not_replace_real_credit_outcome(self):
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
        self.assertEqual(result[1], "COMPLETED")
        self.assertEqual(pipeline.call_count, 2)
        self.assertEqual(pipeline.call_args.kwargs["query"], bridge.get_bridge_cfg_runtime_resume_prompt(self.cfg))
        self.assertEqual(progress.call_args_list[0].args[1], "CREDIT_EXHAUSTED")
        self.assertFalse(self.cfg.compact_before_send)
        self.assertTrue(self.cfg.compact_deferred)
        self.cooldown.assert_called_once()
        self.assertEqual(release.call_count, 2)

    def test_verified_compact_clears_deferred_metadata(self):
        reg = self.isolated_registry()
        reg.set_compact_state(False, PID, deferred=True, chat_session_id="same")
        context = {"chat_session_id": "verified", "summary_key": "fresh"}
        reg.set_compact_state(False, PID, context=context)
        self.assertTrue(reg.get_compact_state()["verified"])
        self.assertNotIn("deferred", reg.get_compact_state())

    def test_pending_compact_survives_changed_resume_project_id(self):
        calls, result, _, _, _ = self.worker_scenario(initial_due=True, resume_pid=NEW_PID)
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification"])
        self.assertEqual(result[1], "COMPLETED")

    def test_platform_credit_during_compact_remains_credit_exhausted(self):
        def fetch(pid, cookies, cfg):
            self.fetch_count += 1
            return [OLD_SUMMARY] if self.fetch_count == 1 else [
                {"role": "assistant", "content": CREDIT,
                 "action": {"type": "ACTION_CREDIT_EXHAUSTED"}}]
        self.engine.fetch_project_messages.side_effect = fetch
        self.cfg.compact_before_send = True
        self.assertEqual(self.compact()[0], "CREDIT_EXHAUSTED")
        self.assertTrue(self.cfg.compact_before_send)

    def test_cancel_during_compact_never_sends_user_prompt(self):
        calls, result, _, _, _ = self.worker_scenario(initial_due=True, cancel=True)
        self.assertEqual([c[0] for c in calls], ["/compact"])
        self.assertEqual(result[1], bridge.CANCELLED_STATUS)
        self.cooldown.assert_not_called()

    def test_collapsed_compact_user_turn_resolves_to_prior_assistant_and_dispatches(self):
        # When /compact was recorded as role=user without assistant reply,
        # bypass resolves to the prior assistant message and dispatches pending work.
        calls, result, _, reg, sends = self.worker_scenario(initial_due=True, failure="compact_last")
        self.assertEqual([c[0] for c in calls], ["/compact", "User modification"])
        self.assertEqual(result[1], "COMPLETED")
        self.assertFalse(reg.get_compact_state()["due"])
        self.assertTrue(reg.get_compact_state()["bypass_ready"])
        self.assertIn("تم التوليد بنجاح", str(sends.call_args_list))
        self.cooldown.assert_not_called()


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
        self.assertEqual(status, "COMPACT_VERIFIED")
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
