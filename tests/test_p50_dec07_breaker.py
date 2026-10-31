"""P50 — STEP-4 (DEC-07): empty-stream circuit breaker + textual suspended detection in 01.33.

Owner-ratified contract (PROGRESS.md › S4-A / S4-A-RATIFIED, 2026-10-31):
  * Constants: DEC07_EMPTY_BREAKER_ENABLED=True, DEC07_EMPTY_READS_REQUIRED=3,
    DEC07_EMPTY_MIN_SECONDS=30, DEC07_EMPTY_COOLDOWN_HOURS=1.0, DEC07_SUSPENDED_MARKERS.
  * New statuses: EMPTY_STREAM_FAILED, ACCOUNT_SUSPENDED — NOT added to P44_STRUCTURED_STATUSES.
  * Injection A (monitor_chat_completion loop): consecutive empty reads (no message / EMPTY text)
    while activity is not active, after >= 30 s since start_time -> EMPTY_STREAM_FAILED.
    Guards: readiness / unconfirmed / maintenance / evidence.finished -> breaker inactive.
  * Injection A2: reply text contains a DEC07_SUSPENDED_MARKERS marker -> ACCOUNT_SUSPENDED.
  * Injection B (send_message_with_auto_account_failover): EMPTY_STREAM_FAILED -> cooldown 1h + next
    account immediately; ACCOUNT_SUSPENDED -> status=suspended/quarantined=True/cookies={} + next account.
  * Untouched: is_account_ready, P48, detect_response_status(_gated), P44_STRUCTURED_STATUSES, P25.
  * Pure offline: no live probe, no network. Log lines carry the e-mail via the existing log_event.

Everything here is offline: the bridge module is loaded from file, collaborators are injected.
"""

from __future__ import annotations

import contextlib
import importlib.util
import pathlib
import re
import sys
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE.read_text(encoding="utf-8")
PID = "p50_project_0001"
EMAIL_A = "dec07.alpha@test.invalid"
EMAIL_B = "dec07.beta@test.invalid"


def _load_bridge_module():
    spec = importlib.util.spec_from_file_location("bridge_p50", str(BRIDGE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p50"] = mod
    spec.loader.exec_module(mod)
    return mod


def _extract_func(src: str, name: str) -> str:
    """Return the function body only: stops at the first module-level statement
    (unindented, non-comment, non-blank line) so trailing constants are not included."""
    m = re.search(rf"^def {name}\(", src, re.MULTILINE)
    assert m, f"function not found: {name}"
    # skip the (possibly multi-line) signature: scan from the first line that ends the def header
    sig_end = re.search(r"\)\s*(?:->[^:\n]+)?:[ \t]*\n", src[m.end():])
    assert sig_end, f"signature end not found: {name}"
    scan_from = m.end() + sig_end.end()
    nxt = re.search(r"^(?!\s)(?!#)\S", src[scan_from:], re.MULTILINE)
    end = scan_from + (nxt.start() if nxt else len(src) - scan_from)
    return src[m.start():end]


bridge = _load_bridge_module()


class _FakeClock:
    """Deterministic time: every poll advances by `step` seconds."""

    def __init__(self, start=1_800_000_000.0, step=5.0):
        self.now = start
        self.step = step
        self.sleeps = 0

    def time(self):
        return self.now

    def sleep(self, seconds=0):
        self.sleeps += 1
        self.now += self.step


class _MonitorHarness(unittest.TestCase):
    """Drives monitor_chat_completion offline with scripted message reads."""

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.clock = _FakeClock()
        self.stack.enter_context(mock.patch.object(bridge.time, "time", self.clock.time))
        self.stack.enter_context(mock.patch.object(bridge.time, "sleep", self.clock.sleep))
        self.logs = []
        self.stack.enter_context(mock.patch.object(
            bridge, "log_event", side_effect=lambda level, msg, email="", extra=None: self.logs.append((level, msg, email))))
        self.activity = self.stack.enter_context(mock.patch.object(
            bridge, "fetch_project_activity_signature", return_value={"active": False, "deep_thinking": False, "tasks_remaining": None}))
        self.stack.enter_context(mock.patch.object(bridge, "fetch_final_reply_text", side_effect=lambda mod, pid, cookies, cfg, old, email="": old))
        self.reads = []
        self.mod = types.SimpleNamespace(
            CHAT_ATTEMPT_EVIDENCE_SUPPORTED=False,
            fetch_project_messages=mock.Mock(side_effect=self._next_read),
        )
        self.cfg = types.SimpleNamespace(_last_fetch_status=200, _chat_attempt=None)
        self.bridge_cfg = bridge.BridgeConfig()
        self.bridge_cfg.session_timeout = 2000
        self.bridge_cfg.cancel_event = None

    def _next_read(self, pid, cookies, cfg):
        if not self.reads:
            raise AssertionError("scripted reads exhausted — loop did not break where expected")
        item = self.reads.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    @staticmethod
    def assistant(text, finished=False):
        state = {"_finish_reason": "stop"} if finished else {}
        return [{"role": "assistant", "content": text, "session_state": state, "id": "m1"}]

    def run_monitor(self, answer=None, start_offset=0.0, **kw):
        start_time = self.clock.now - start_offset
        return bridge.monitor_chat_completion(self.mod, {"s": "1"}, self.cfg, self.bridge_cfg, PID,
                                              answer, start_time, email=EMAIL_A, **kw)

    def dec07_logs(self):
        return [m for _, m, _ in self.logs if "[DEC07]" in m]


# ── 1: constants ─────────────────────────────────────────────────────────────

class TestConstants(unittest.TestCase):
    def test_01_constants_and_values(self):
        self.assertIs(bridge.DEC07_EMPTY_BREAKER_ENABLED, True)
        self.assertEqual(bridge.DEC07_EMPTY_READS_REQUIRED, 3)
        self.assertEqual(bridge.DEC07_EMPTY_MIN_SECONDS, 30)
        self.assertEqual(bridge.DEC07_EMPTY_COOLDOWN_HOURS, 1.0)
        markers = bridge.DEC07_SUSPENDED_MARKERS
        self.assertIsInstance(markers, tuple)
        self.assertIn("user_suspended", markers)
        self.assertTrue(all(m == m.lower() for m in markers), "markers must be lowercase for case-insensitive matching")
        self.assertEqual(bridge.EMPTY_STREAM_FAILED_STATUS, "EMPTY_STREAM_FAILED")
        self.assertEqual(bridge.ACCOUNT_SUSPENDED_STATUS, "ACCOUNT_SUSPENDED")
        # contract: not part of the legacy structured tuple
        self.assertEqual(bridge.P44_STRUCTURED_STATUSES, ("CREDIT_EXHAUSTED", "DATA_RETENTION", "SESSION_EXPIRED", "FORBIDDEN"))


# ── 2–8: monitor loop behaviour ──────────────────────────────────────────────

class TestEmptyStreamBreaker(_MonitorHarness):
    def test_02_three_empty_reads_after_30s_break_fast(self):
        self.reads = [[], [], [], [], [], []]  # more than needed; loop must stop at 3
        status, text = self.run_monitor(answer=None, start_offset=40)
        self.assertEqual(status, "EMPTY_STREAM_FAILED")
        self.assertEqual(text, "")
        self.assertEqual(self.mod.fetch_project_messages.call_count, 3)
        self.assertLess(self.clock.sleeps, 5, "must not idle towards session_timeout")
        self.assertTrue(any("EMPTY_STREAM_BREAK" in m for m in self.dec07_logs()))
        self.assertTrue(all(e == EMAIL_A for _, m, e in self.logs if "[DEC07]" in m), "log carries full e-mail")

    def test_03_streak_resets_on_real_text_then_completes(self):
        self.reads = [[], [], self.assistant("Partial content arrives here", finished=False),
                      self.assistant("Final answer body is complete.", finished=True),
                      self.assistant("Final answer body is complete.", finished=True)]
        status, text = self.run_monitor(answer=None, start_offset=40)
        self.assertEqual(status, "COMPLETED")
        self.assertIn("complete", text)
        self.assertFalse(self.dec07_logs())

    def test_04_active_indicator_blocks_breaker(self):
        # 4 empty reads while the Deep-Thinking indicator is active must NOT trip the breaker;
        # the indicator then disappears -> P18 stops the loop (before a 5th read).
        self.reads = [[], [], [], [], self.assistant("done at last", finished=True)]
        self.activity.side_effect = [{"active": True, "deep_thinking": True, "tasks_remaining": 2}] * 5 + \
                                    [{"active": False, "deep_thinking": False, "tasks_remaining": None}] * 10
        status, _ = self.run_monitor(answer=None, start_offset=40)
        self.assertNotEqual(status, "EMPTY_STREAM_FAILED")
        self.assertEqual(self.mod.fetch_project_messages.call_count, 4)
        self.assertFalse(self.dec07_logs())

    def test_05_before_min_seconds_no_break_then_break_after(self):
        # start_time == now, clock advances 5 s per poll -> 30 s reached at the 6th poll
        self.reads = [[] for _ in range(12)]
        status, _ = self.run_monitor(answer=None, start_offset=0)
        self.assertEqual(status, "EMPTY_STREAM_FAILED")
        self.assertGreaterEqual(self.mod.fetch_project_messages.call_count, 6)

    def test_06_readiness_mode_never_breaks(self):
        self.reads = [[] for _ in range(4)] + [self.assistant("ready text", finished=True)] * 3
        status, _ = self.run_monitor(answer=None, start_offset=100, readiness=True)
        self.assertNotEqual(status, "EMPTY_STREAM_FAILED")
        self.assertFalse(self.dec07_logs())

    def test_07_unconfirmed_credit_keeps_its_meaning(self):
        self.bridge_cfg.session_timeout = 60
        self.reads = [[] for _ in range(40)]
        status, _ = self.run_monitor(answer="__CREDIT_EXHAUSTED__", start_offset=40)
        self.assertEqual(status, "CREDIT_UNCONFIRMED")
        self.assertFalse(self.dec07_logs())

    def test_07b_maintenance_mode_never_breaks(self):
        self.bridge_cfg.session_timeout = 60
        self.reads = [[] for _ in range(40)]
        status, _ = self.run_monitor(answer=None, start_offset=40, maintenance=True)
        self.assertNotEqual(status, "EMPTY_STREAM_FAILED")
        self.assertFalse(self.dec07_logs())

    def test_08_suspended_marker_in_text_returns_account_suspended(self):
        self.reads = [self.assistant("Redirected to https://www.genspark.ai/user_suspended")]
        status, text = self.run_monitor(answer=None, start_offset=5)  # no 30 s requirement for suspension
        self.assertEqual(status, "ACCOUNT_SUSPENDED")
        self.assertIn("user_suspended", text)
        self.assertTrue(any("ACCOUNT_SUSPENDED" in m for m in self.dec07_logs()))

    def test_08b_suspended_marker_in_initial_answer(self):
        self.reads = [[] for _ in range(3)]
        status, _ = self.run_monitor(answer="Your account is suspended. Please contact support.", start_offset=5)
        self.assertEqual(status, "ACCOUNT_SUSPENDED")

    def test_08c_http_403_stays_forbidden(self):
        self.cfg._last_fetch_status = 403
        self.reads = [[]]
        status, _ = self.run_monitor(answer=None, start_offset=100)
        self.assertEqual(status, "FORBIDDEN")  # decision (4): 403 is NOT a suspicion of ban

    def test_11_flag_off_restores_legacy_timeout(self):
        self.bridge_cfg.session_timeout = 60
        self.reads = [[] for _ in range(40)]
        with mock.patch.object(bridge, "DEC07_EMPTY_BREAKER_ENABLED", False):
            status, _ = self.run_monitor(answer=None, start_offset=40)
        self.assertEqual(status, "TIMEOUT")
        self.assertFalse(self.dec07_logs())


# ── 9–10: failover handling ──────────────────────────────────────────────────

class TestFailoverHandling(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.accounts = [
            {"email": EMAIL_A, "password": "test-only", "cookies": {"session_id": "x"}, "last_refresh": 1.0, "status": "active", "active": True},
            {"email": EMAIL_B, "password": "test-only", "cookies": {"session_id": "y"}, "last_refresh": 1.0, "status": "active", "active": True},
        ]
        self.cfg = bridge.BridgeConfig()
        self.cfg.max_account_attempts = 2
        self.patch("read_accounts_safe", return_value=self.accounts)
        self.updates = self.patch("update_account_data")
        self.cooldown = self.patch("mark_account_cooldown")
        self.patch("get_account_fingerprint", return_value={"browser": "chrome120", "user_agent": "t"})
        self.patch("log_event")
        self.patch("apply_project_runtime_binding")
        self.patch("notify_account_selection_observer")
        self.patch("reactivate_account_if_due", side_effect=lambda account, **kw: account)
        self.patch("claim_eligible_account_for_owner",
                   side_effect=[(self.accounts[0], self.accounts, "claimed"), (self.accounts[1], self.accounts, "claimed")])
        self.patch("release_account_selection")
        self.stack.enter_context(mock.patch.object(bridge.time, "sleep"))

    def patch(self, name, **kwargs):
        return self.stack.enter_context(mock.patch.object(bridge, name, **kwargs))

    def _run(self, first_status):
        url = bridge.build_genspark_viewer_url(PID)
        sends = self.patch("send_message_and_make_public", side_effect=[
            (url, first_status, None, "", None),
            (url, "COMPLETED", None, "ok", None),
        ])
        result = bridge.send_message_with_auto_account_failover(
            None, "build it", bridge_cfg=self.cfg, json_path="unused.json")
        return sends, result

    def test_09_empty_stream_failed_cools_1h_and_moves_on(self):
        sends, (pub_url, status, acc, _ext, _text) = self._run("EMPTY_STREAM_FAILED")
        self.assertEqual(sends.call_count, 2, "second account must be tried in the same call")
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(acc["email"], EMAIL_B)
        self.cooldown.assert_any_call(EMAIL_A, cooldown_hours=bridge.DEC07_EMPTY_COOLDOWN_HOURS, json_path="unused.json")
        # no 29h cooldown and no suspension for an empty stream
        for call in self.cooldown.call_args_list:
            self.assertNotEqual(call.kwargs.get("cooldown_hours"), 29.0)
        for call in self.updates.call_args_list:
            if call.args and call.args[0] == EMAIL_A:
                self.assertNotEqual(call.args[1].get("status"), "suspended")

    def test_10_account_suspended_quarantines_and_moves_on(self):
        sends, (pub_url, status, acc, _ext, _text) = self._run("ACCOUNT_SUSPENDED")
        self.assertEqual(sends.call_count, 2)
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(acc["email"], EMAIL_B)
        suspended_writes = [c for c in self.updates.call_args_list
                            if c.args and c.args[0] == EMAIL_A and c.args[1].get("status") == "suspended"]
        self.assertTrue(suspended_writes, "suspended account must be written as status=suspended")
        payload = suspended_writes[0].args[1]
        self.assertIs(payload.get("quarantined"), True)
        self.assertEqual(payload.get("cookies"), {})
        # no time-based cooldown for a banned account
        for call in self.cooldown.call_args_list:
            self.assertNotEqual(call.args[0] if call.args else None, EMAIL_A)


# ── 12: source contracts ─────────────────────────────────────────────────────

class TestSourceContracts(unittest.TestCase):
    def test_12a_single_injection_in_monitor_loop(self):
        body = _extract_func(BRIDGE_SRC, "monitor_chat_completion")
        self.assertEqual(body.count("EMPTY_STREAM_BREAK"), 1, "exactly one empty-stream break log in the loop")
        self.assertIn("DEC07_EMPTY_READS_REQUIRED", body)
        self.assertIn("DEC07_EMPTY_MIN_SECONDS", body)
        self.assertIn("dec07_text_has_suspended_marker", body)  # textual detection via the pure helper
        helper = _extract_func(BRIDGE_SRC, "dec07_text_has_suspended_marker")
        self.assertIn("DEC07_SUSPENDED_MARKERS", helper)
        self.assertNotIn("requests", helper)  # decision (5): no network in the detector

    def test_12b_failover_handles_both_statuses(self):
        body = _extract_func(BRIDGE_SRC, "send_message_with_auto_account_failover")
        self.assertIn("EMPTY_STREAM_FAILED", body)
        self.assertIn("ACCOUNT_SUSPENDED", body)
        self.assertIn("DEC07_EMPTY_COOLDOWN_HOURS", body)

    def test_12c_untouched_contracts(self):
        self.assertEqual(bridge.P44_STRUCTURED_STATUSES, ("CREDIT_EXHAUSTED", "DATA_RETENTION", "SESSION_EXPIRED", "FORBIDDEN"))
        for name in ("is_account_ready", "detect_response_status", "detect_response_status_gated",
                     "classify_gift_freshness", "get_eligible_accounts"):
            self.assertNotIn("DEC07", _extract_func(BRIDGE_SRC, name), f"{name} must not reference DEC07")
        self.assertNotIn("user_suspended\"", _extract_func(BRIDGE_SRC, "is_account_ready"))

    def test_12d_no_live_probe_added(self):
        # decision (5): pure offline — no new request towards a /user_suspended page
        self.assertNotIn("genspark.ai/user_suspended\"", BRIDGE_SRC.replace("'", "\""))
        self.assertEqual(BRIDGE_SRC.count("/user_suspended"), 0, "no HTTP probe URL for the suspended page")

    def test_12e_crlf_preserved(self):
        raw = BRIDGE.read_bytes()
        lf_only = raw.count(b"\n") - raw.count(b"\r\n")
        self.assertEqual(lf_only, 0, "01.33 must stay pure CRLF")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
