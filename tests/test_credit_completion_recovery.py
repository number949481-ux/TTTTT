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
                {"role": "assistant", "content": CREDIT}]),
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
            {"role": "assistant", "content": final_text},
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

    def test_credit_in_fast_mode_downloads_recovery_checkpoint(self):
        self.cfg.project_fast_lean_skip = True
        self.engine.send_chat.return_value = (CREDIT, PID, "assistant")
        result = self.run_pipeline()
        self.assertEqual(result[1], "CREDIT_EXHAUSTED")
        self.download.assert_called_once()
        actionable, _ = bridge.should_capture_project_update(URL, result[1], result[2])
        self.assertTrue(actionable)

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
        checkpoints = []

        def progress(url, status, folder, text, email, query):
            actionable, meta = bridge.should_capture_project_update(url, status, folder)
            if not actionable or not allow_checkpoint:
                return {"allow_continuation": False, "project_update_preserved": False,
                        "reason": meta["reason"] or "Preservation failed"}
            update = registry.snapshot(folder, url, status, text)
            checkpoint = update["checkpoint"]
            self.assertTrue(registry.verify_checkpoint_record_checksum(checkpoint))
            checkpoints.append(checkpoint)
            return {"allow_continuation": True, "project_update_preserved": True,
                    "checkpoint_id": checkpoint}

        result = bridge.send_message_with_auto_account_failover(
            None, "Original task", bridge_cfg=self.cfg, progress_callback=progress)
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


if __name__ == "__main__":
    unittest.main()
