"""Offline regressions for final-fetch credit errors and fast-mode handoff."""
import contextlib
import importlib.util
import pathlib
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "bridge_credit_recovery", ROOT / "01.33_telegram_gen_bridge.py")
bridge = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bridge
SPEC.loader.exec_module(bridge)
PID = "11111111-1111-4111-8111-111111111111"
URL = f"https://www.genspark.ai/autopilotagent_viewer?id={PID}"
CREDIT = "Your credit balance is negative. Please top up to continue."
DONE = "The implementation is complete and the requested tests all passed."


class CreditRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = pathlib.Path(self.stack.enter_context(
            tempfile.TemporaryDirectory(dir=ROOT)))
        self.accounts = [
            {"email": f"account{i}@test.invalid", "password": "test-only",
             "cookies": {"session_id": "test-only"}, "last_refresh": time.time()}
            for i in range(2)
        ]
        self.engine = types.SimpleNamespace(
            Config=types.SimpleNamespace,
            check_balance=mock.Mock(return_value=99999),
            send_chat=mock.Mock(return_value=(DONE, PID, "assistant")),
            fetch_project_messages=mock.Mock(return_value=[
                {"role": "assistant", "content": CREDIT,
                 "action": {"type": "ACTION_CREDIT_EXHAUSTED"}}]),
        )
        self.cfg = bridge.BridgeConfig()
        self.cfg.max_timeout_retries = 1
        self.cfg.max_account_attempts = 2
        self.cfg.extracted_webapp_dir = str(self.root / "extracted")
        self.patch("get_genspark_engine", return_value=self.engine)
        self.patch("read_accounts_safe", return_value=self.accounts)
        self.patch("update_account_data")
        self.cooldown = self.patch("mark_account_cooldown")
        self.patch("get_account_fingerprint", return_value={
            "browser": "chrome120", "user_agent": "test-agent"})
        self.activity = self.patch("fetch_project_activity_signature", return_value=None)
        self.download = self.patch("download_project_archive", side_effect=self.archive)
        self.patch("make_project_always_public", return_value=URL)
        self.saved_branch = self.patch("save_project_branch")
        self.patch("log_event")
        self.patch("apply_project_runtime_binding")
        self.patch("notify_account_selection_observer")
        self.patch("reactivate_account_if_due", side_effect=lambda account, **kw: account)
        self.stack.enter_context(mock.patch.object(bridge.time, "sleep"))

    def patch(self, name, **kwargs):
        return self.stack.enter_context(mock.patch.object(bridge, name, **kwargs))

    def archive(self, pid, cookies, out_dir, **kwargs):
        folder = pathlib.Path(out_dir)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text("<main>Saved progress</main>", encoding="utf-8")
        return str(folder / "webapp.tar.gz")

    def interrupted_then_activity_stop(self, final_text=CREDIT):
        self.engine.send_chat.return_value = ("__STREAM_INTERRUPTED__", PID, "assistant")
        self.engine.fetch_project_messages.return_value = [
            {"role": "assistant", "content": final_text,
             "action": {"type": "ACTION_CREDIT_EXHAUSTED"} if final_text == CREDIT else {}},
            {"role": "user", "content": "This user message is not the final reply"},
        ]
        self.activity.side_effect = [
            {"active": True, "deep_thinking": True, "tasks_remaining": 2},
            {"active": False, "deep_thinking": False, "tasks_remaining": None},
        ]

    def run_pipeline(self):
        return bridge.send_message_and_make_public(
            url=None, email=self.accounts[0]["email"], password="test-only",
            query="Continue the existing task", bridge_cfg=self.cfg)

    def test_final_fetch_credit_overrides_activity_stop_completion(self):
        self.interrupted_then_activity_stop()
        result = self.run_pipeline()
        self.assertEqual(result[1], "CREDIT_EXHAUSTED")
        self.assertEqual(result[3], CREDIT)
        self.assertEqual(self.saved_branch.call_args.kwargs["status"], "CREDIT_EXHAUSTED")
        self.engine.fetch_project_messages.assert_called_once()
        self.assertEqual(self.activity.call_count, 2)  # Polling still stops immediately.

    def test_final_fetch_other_structured_failures_are_not_success(self):
        for content, expected in [
            ("This model requires AI Data Retention to be enabled", "DATA_RETENTION"),
            ("Session expired. Login required.", "SESSION_EXPIRED"),
            ({"status": 403, "message": "Rejected by endpoint"}, "FORBIDDEN"),
        ]:
            with self.subTest(expected=expected):
                self.interrupted_then_activity_stop(content)
                self.assertEqual(self.run_pipeline()[1], expected)

    def test_final_fetch_success_preserves_completion(self):
        self.interrupted_then_activity_stop(DONE)
        self.assertEqual(self.run_pipeline()[1], "COMPLETED")

    def test_final_fetch_failure_keeps_previous_behavior(self):
        self.interrupted_then_activity_stop()
        self.engine.fetch_project_messages.side_effect = OSError("offline")
        result = self.run_pipeline()
        self.assertEqual(result[1], "COMPLETED")
        self.assertEqual(result[3], "")

    def test_credit_in_fast_mode_never_downloads_recovery_artifacts(self):
        self.cfg.project_fast_lean_skip = True
        self.engine.send_chat.return_value = (CREDIT, PID, "assistant")
        result = self.run_pipeline()
        self.assertEqual(result[1], "CREDIT_EXHAUSTED")
        self.download.assert_not_called()
        self.assertFalse(pathlib.Path(result[2]).exists())

    def test_successful_fast_mode_still_skips_archive_and_final_fetch(self):
        self.cfg.project_fast_lean_skip = True
        self.assertEqual(self.run_pipeline()[1], "COMPLETED")
        self.download.assert_not_called()
        self.engine.fetch_project_messages.assert_not_called()

    def test_decline_fast_path_is_unchanged(self):
        self.engine.send_chat.return_value = (
            "The model declined to answer this request.", PID, "assistant")
        self.assertEqual(self.run_pipeline()[1], "COMPLETED")
        self.download.assert_not_called()

    def test_explicit_cancellation_wins_over_credit(self):
        self.cfg.cancel_event = threading.Event()
        self.cfg.cancel_event.set()
        self.engine.send_chat.return_value = (CREDIT, PID, "assistant")
        self.assertEqual(self.run_pipeline()[1], bridge.CANCELLED_STATUS)
        self.engine.send_chat.assert_not_called()
        self.download.assert_not_called()
        self.cooldown.assert_not_called()

    def run_failover(self, interrupted=False, allow_checkpoint=True, limit=10):
        # Isolate credit recovery from auto-compact; short-run policy has its own suite.
        self.patch("current_account_duration", return_value=300)
        self.cfg.project_fast_lean_skip = True
        self.cfg.max_credit_continuations = limit
        if interrupted:
            self.interrupted_then_activity_stop()
            self.activity.side_effect = [
                {"active": True, "deep_thinking": True, "tasks_remaining": 2},
                {"active": False, "deep_thinking": False, "tasks_remaining": None},
                None,
            ]
        first = "__STREAM_INTERRUPTED__" if interrupted else CREDIT
        self.engine.send_chat.side_effect = [(first, PID, "a1"), (DONE, PID, "a2")]
        self.patch("claim_eligible_account_for_owner", side_effect=[
            (account, self.accounts, "claimed") for account in self.accounts])
        release = self.patch("release_account_selection")
        self.patch("get_public_forked_pid", return_value=PID)
        # Prevent early-public daemon threads in the resume path.
        self.stack.enter_context(mock.patch.object(bridge.threading, "Thread"))
        registry_home = self.root / "registry"
        self.stack.enter_context(mock.patch.object(bridge, "PROJECT_REGISTRY_HOME", registry_home))
        registry = bridge.ProjectRegistry("credit_recovery")
        registry.update_project_settings({"fast_mode": True})
        checkpoints = []

        def progress(url, status, folder, text, email, query):
            if status != "CREDIT_EXHAUSTED":
                return {"allow_continuation": True, "project_update_preserved": False}
            if not allow_checkpoint:
                return {"allow_continuation": False, "project_update_preserved": False,
                        "reason": "Preservation failed"}
            update = registry.preserve_cloud_resume(url, PID, email, query, text)
            checkpoint = update["checkpoint"]
            self.assertTrue(registry.verify_checkpoint_record_checksum(checkpoint))
            checkpoints.append(checkpoint)
            return {"allow_continuation": True, "project_update_preserved": True,
                    "checkpoint_id": checkpoint}

        result = bridge.send_message_with_auto_account_failover(
            None, "Original task", bridge_cfg=self.cfg, progress_callback=progress)
        self.download.assert_not_called()
        self.assertFalse((registry.root / "archive").exists())
        return result, checkpoints, release

    def test_fast_credit_handoff_preserves_checkpoint_before_second_account(self):
        result, checkpoints, release = self.run_failover()
        self.assertEqual(result[1], "COMPLETED")
        self.assertTrue(checkpoints)
        self.assertEqual(self.engine.send_chat.call_count, 2)
        self.assertEqual(result[2]["email"], self.accounts[1]["email"])
        self.assertEqual(self.cfg.last_credit_continuations, 1)
        self.assertEqual(self.engine.send_chat.call_args_list[1].args[1],
                         bridge.get_bridge_cfg_runtime_resume_prompt(self.cfg))
        self.assertEqual(self.engine.send_chat.call_args_list[1].kwargs["project_id"], PID)
        self.cooldown.assert_called_once()
        self.assertEqual(release.call_count, 2)

    def test_final_fetch_credit_reaches_real_failover_in_fast_mode(self):
        result, checkpoints, _ = self.run_failover(interrupted=True)
        self.assertEqual(result[1], "COMPLETED")
        self.assertTrue(checkpoints)
        self.assertEqual(self.engine.send_chat.call_count, 2)
        self.cooldown.assert_called_once()

    def test_failed_preservation_does_not_send_on_another_account(self):
        result, _, _ = self.run_failover(allow_checkpoint=False)
        self.assertEqual(result[1], "CREDIT_EXHAUSTED")
        self.assertEqual(self.engine.send_chat.call_count, 1)
        self.assertEqual(self.cfg.last_credit_checkpoint_state, "BLOCKED_NOT_PRESERVED")

    def test_continuation_limit_is_still_enforced(self):
        result, _, _ = self.run_failover(limit=1)
        self.assertEqual(result[1], "CREDIT_EXHAUSTED")
        self.assertEqual(self.engine.send_chat.call_count, 1)

    def isolated_registry(self, key="cloud_worker"):
        home = self.root / "registry"
        self.stack.enter_context(mock.patch.object(bridge, "PROJECT_REGISTRY_HOME", home))
        self.stack.enter_context(mock.patch.object(bridge, "PROJECT_REGISTRY_INDEX_FILE", home / "registry.json"))
        reg = bridge.ProjectRegistry(key)
        reg.update_project_settings({"fast_mode": True})
        return reg

    def test_metadata_survives_reload_without_deleting_existing_files(self):
        reg = self.isolated_registry()
        data = reg._read()
        data["file_index"] = {"index.html": {"sha256": "old", "bytes": 12}}
        data["checkpoints"] = ["existing-artifact"]
        reg._write(data)
        before = reg._read()
        update = reg.preserve_cloud_resume(URL, PID, "owner@test.invalid", "Continue", CREDIT)
        reloaded = bridge.ProjectRegistry(reg.key)
        record = reloaded.load_checkpoint_record(update["checkpoint"])
        self.assertTrue(reloaded.verify_checkpoint_record_checksum(update["checkpoint"]))
        self.assertEqual(record["artifact_state"], "cloud_resume_only")
        self.assertFalse(record["summary"]["artifact_backup"])
        self.assertEqual(record["summary"]["latest_pid"], PID)
        self.assertEqual(record["archive_ref"], "")
        self.assertEqual(record["deleted_files"], [])
        self.assertEqual(reloaded._read()["file_index"], before["file_index"])
        self.assertEqual(reloaded._read()["checkpoints"], before["checkpoints"])
        self.assertFalse((reg.root / "archive").exists())
        self.assertFalse((reg.root / "checkpoints").exists())

    def test_metadata_rejects_invalid_locator_and_github_artifact_mode(self):
        reg = self.isolated_registry()
        with self.assertRaises(ValueError):
            reg.preserve_cloud_resume("not-a-project", PID, "e", "Continue", CREDIT)
        reg.update_project_settings({"fast_mode": False})
        with self.assertRaises(ValueError):
            reg.preserve_cloud_resume(URL, PID, "e", "Continue", CREDIT)
        data = reg._read()
        data["project_settings"]["fast_mode"] = True
        data["project_settings"]["github"]["enabled"] = True
        reg._write(data)
        with self.assertRaises(ValueError):
            reg.preserve_cloud_resume(URL, PID, "e", "Continue", CREDIT)
        self.assertFalse((reg.root / "reports").exists())

    def test_metadata_checksum_failure_blocks_preservation(self):
        reg = self.isolated_registry()
        with mock.patch.object(reg, "verify_checkpoint_record_checksum", return_value=False):
            with self.assertRaises(RuntimeError):
                reg.preserve_cloud_resume(URL, PID, "e", "Continue", CREDIT)

    def test_platform_flags_override_completed_and_empty_content(self):
        for fields in [
            {"action": {"type": "ACTION_CREDIT_EXHAUSTED"}},
            {"action": {"action_params": {"block_reason": "balance_drained"}}},
            {"session_state": {"consume_usage_quota_exceeded": True}},
        ]:
            with self.subTest(fields=fields):
                message = {"role": "assistant", "content": DONE, **fields}
                self.assertTrue(bridge.has_platform_credit_signal(message))
                self.assertEqual(bridge.resolve_runtime_credit_status(
                    "COMPLETED", DONE, self.engine, PID, {}, types.SimpleNamespace(), message),
                    "CREDIT_EXHAUSTED")
                self.interrupted_then_activity_stop()
                self.engine.fetch_project_messages.return_value = [{**message, "content": ""}]
                self.assertEqual(self.run_pipeline()[1], "CREDIT_EXHAUSTED")

    def test_quoted_json_user_messages_and_string_booleans_are_not_flags(self):
        for message in [
            {"role": "assistant", "content": 'Example: {"type":"ACTION_CREDIT_EXHAUSTED"}'},
            {"role": "user", "action": {"type": "ACTION_CREDIT_EXHAUSTED"}},
            {"role": "assistant", "session_state": {"consume_usage_quota_exceeded": "true"}},
            {"role": "assistant", "action": "ACTION_CREDIT_EXHAUSTED"},
        ]:
            with self.subTest(message=message):
                self.assertFalse(bridge.has_platform_credit_signal(message))

    def test_quoted_credit_text_in_finished_reply_does_not_rotate(self):
        text = "Documentation: visit https://www.genspark.ai/pricing for pricing."
        self.engine.send_chat.return_value = (text, PID, "assistant")
        self.engine.fetch_project_messages.return_value = [
            {"role": "assistant", "content": text, "session_state": {"_finish_reason": "stop"}}]
        self.cfg.project_fast_lean_skip = True
        result = self.run_pipeline()
        self.assertEqual(result[1], "COMPLETED")
        self.assertEqual(result[3], text)
        self.cooldown.assert_not_called()
        self.download.assert_not_called()

    def test_unconfirmed_credit_and_network_failure_are_not_success(self):
        self.engine.send_chat.return_value = ("__CREDIT_EXHAUSTED__", PID, "assistant")
        for failure in [False, True]:
            with self.subTest(network_failure=failure):
                self.engine.fetch_project_messages.return_value = []
                self.engine.fetch_project_messages.side_effect = OSError("offline") if failure else None
                result = self.run_pipeline()
                self.assertEqual(result[1], "CREDIT_UNCONFIRMED")
                self.assertEqual(bridge.describe_terminal_outcome(result[1], result[0])["kind"], "failure")
        self.cooldown.assert_not_called()
        self.download.assert_not_called()

    def test_old_credit_before_new_user_turn_is_not_current_evidence(self):
        self.engine.send_chat.return_value = ("__CREDIT_EXHAUSTED__", PID, "assistant")
        self.engine.fetch_project_messages.return_value = [
            {"role": "assistant", "content": CREDIT, "action": {"type": "ACTION_CREDIT_EXHAUSTED"}},
            {"role": "user", "content": "New task"}]
        self.assertEqual(self.run_pipeline()[1], "CREDIT_UNCONFIRMED")

    def test_sentinel_cannot_become_success_from_a_stale_finished_reply(self):
        self.engine.send_chat.return_value = ("__CREDIT_EXHAUSTED__", PID, "assistant")
        self.engine.fetch_project_messages.return_value = [
            {"role": "assistant", "content": DONE, "session_state": {"_finish_reason": "stop"}}]
        self.assertEqual(self.run_pipeline()[1], "CREDIT_UNCONFIRMED")
        self.cooldown.assert_not_called()

    def test_normal_mode_credit_still_preserves_artifacts(self):
        self.cfg.project_fast_lean_skip = False
        self.engine.send_chat.return_value = (CREDIT, PID, "assistant")
        result = self.run_pipeline()
        self.assertEqual(result[1], "CREDIT_EXHAUSTED")
        self.download.assert_called_once()
        self.assertTrue(bridge.should_capture_project_update(URL, result[1], result[2])[0])

    def run_real_worker(self, fail_write=False, unconfirmed=False):
        # This fixture verifies recovery, not the separately tested compact path.
        self.patch("current_account_duration", return_value=300)
        reg = self.isolated_registry()
        fork_pid = "22222222-2222-4222-8222-222222222222"
        original_failover = bridge.send_message_with_auto_account_failover
        def bind(cfg, *args, **kwargs):
            cfg.project_fast_lean_skip = True
            cfg.extracted_webapp_dir = str(self.root / "extracted")
            return {}
        bridge.apply_project_runtime_binding.side_effect = bind
        self.patch("claim_eligible_account_for_owner", side_effect=[
            (a, self.accounts, "claimed") for a in self.accounts])
        release = self.patch("release_account_selection")
        self.patch("get_public_forked_pid", return_value=fork_pid)
        self.patch("make_project_always_public", side_effect=lambda pid, *a, **kw: bridge.build_genspark_viewer_url(pid))
        self.stack.enter_context(mock.patch.object(bridge.threading, "Thread"))
        sends = self.patch("send_telegram_message")
        self.patch("send_telegram_message_detailed", return_value={"ok": False})
        self.patch("edit_telegram_message_text")
        snapshot = self.stack.enter_context(mock.patch.object(bridge.ProjectRegistry, "snapshot"))
        sync = self.stack.enter_context(mock.patch.object(bridge.ProjectRegistry, "github_sync"))
        scan = self.patch("should_capture_project_update", wraps=bridge.should_capture_project_update)
        if fail_write:
            self.stack.enter_context(mock.patch.object(bridge.ProjectRegistry, "_write_checkpoint_record", side_effect=OSError("disk full")))
        if unconfirmed:
            self.engine.fetch_project_messages.return_value = []
        calls = []
        def chat(cookies, query, email, **kwargs):
            calls.append(email)
            if len(calls) == 1:
                return CREDIT, PID, "a1"
            updates = reg._read()["updates"]
            self.assertEqual(len(updates), 1)
            self.assertTrue(reg.verify_checkpoint_record_checksum(updates[0]["checkpoint"]))
            self.assertEqual(kwargs["project_id"], fork_pid)
            return DONE, fork_pid, "a2"
        self.engine.send_chat.side_effect = chat
        result_box = []
        def failover(**kwargs):
            result = original_failover(**kwargs)
            result_box.append(result)
            return result
        self.patch("send_message_with_auto_account_failover", side_effect=failover)
        bridge.process_user_task_async(12345, None, "Implement existing task", project_key_hint=reg.key)
        self.assertEqual(len(result_box), 1)
        self.download.assert_not_called()
        snapshot.assert_not_called()
        sync.assert_not_called()
        scan.assert_not_called()
        self.assertFalse((reg.root / "archive").exists())
        self.assertFalse((self.root / "extracted").exists())
        return result_box[0], calls, sends, release, reg

    def test_real_worker_handoff_uses_cloud_checkpoint_and_second_account(self):
        result, calls, sends, release, reg = self.run_real_worker()
        self.assertEqual(result[1], "COMPLETED")
        self.assertEqual(calls, [a["email"] for a in self.accounts])
        self.assertEqual(release.call_count, 2)
        self.assertEqual(len(reg._read()["updates"]), 1)
        self.assertIn("cloud_resume_only", str(reg._read()["updates"]))
        self.assertIn("بدون تنزيل", str(sends.call_args_list))
        self.assertNotIn("حدث خطأ داخلي", str(sends.call_args_list))

    def test_real_worker_disk_failure_blocks_handoff(self):
        result, calls, sends, release, reg = self.run_real_worker(fail_write=True)
        self.assertEqual(result[1], "CREDIT_EXHAUSTED")
        self.assertEqual(len(calls), 1)
        self.assertEqual(release.call_count, 1)
        self.assertNotIn("تم التوليد بنجاح", str(sends.call_args_list))

    def test_real_worker_unconfirmed_credit_does_not_cooldown_or_retry(self):
        result, calls, sends, _, _ = self.run_real_worker(unconfirmed=True)
        self.assertEqual(result[1], "CREDIT_UNCONFIRMED")
        self.assertEqual(len(calls), 1)
        self.cooldown.assert_not_called()
        self.assertIn("تعذر تأكيد", str(sends.call_args_list))

    def test_credit_exhausted_preserves_cloud_resume_in_normal_mode_without_artifacts(self):
        reg = self.isolated_registry()
        reg.update_project_settings({"fast_mode": False})
        # Verifying preserve_cloud_resume with allow_non_fast=True succeeds in normal mode
        update = reg.preserve_cloud_resume(
            URL, PID, "owner@test.invalid", "Continue", CREDIT, allow_non_fast=True
        )
        self.assertEqual(update["summary"]["latest_pid"], PID)
        self.assertEqual(update["status"], "CREDIT_EXHAUSTED")
        data = reg._read()
        self.assertEqual(len(data["updates"]), 1)
        self.assertEqual(data["updates"][0]["artifact_state"], "cloud_resume_only")

        # Verifying evaluate_credit_checkpoint_gate returns allow_continuation=True
        b_cfg = bridge.BridgeConfig()
        gate = bridge.evaluate_credit_checkpoint_gate(
            b_cfg,
            callback_result={
                "allow_continuation": True,
                "project_update_preserved": True,
                "reason": "cloud resume metadata preserved; local artifacts pending next turn",
                "checkpoint_id": update["checkpoint"],
                "resume_url": update["url"],
            },
            progress_callback_present=True,
        )
        self.assertTrue(gate["allow_continuation"])
        self.assertEqual(b_cfg.last_credit_checkpoint_state, "PRESERVED")


if __name__ == "__main__":
    unittest.main()
