"""P59 — MAINT-10 account-lifecycle surgery in 01.33 (owner GO card gist db5d6f65 L384–402 / L463–485).

Covers the eight executed tasks of MAINT-10_MASTER_PLAN.md (A-1…A-7 + C-1/C-2):
  * A-5  ``mark_account_cooldown(email, cooldown_hours, json_path, balance=None)`` writes ``balance``
         only when passed; ``balance=0`` at both CREDIT_EXHAUSTED sites, the post-start cancel and COMPLETED.
  * A-4  the real balance is persisted before every in-place LOW_BALANCE exit (bal_check / bal_recheck / bal_mid).
  * A-2  ``OFFLINE_MIN_BALANCE = 100`` + offline filter in ``get_eligible_accounts`` (numeric < 100 ⇒ skipped,
         None/non-numeric/bool ⇒ fail-open) placed after ``is_account_ready`` and before the P48 gift pre-flight.
  * C-1  ``reactivate_account_if_due`` writes ``balance: 100`` together with ``cooldown_until: 0``.
  * A-1  403/FORBIDDEN: no vault, no balance change, ``active`` untouched, 5-minute in-place ``cooldown_until``,
         task stops with ``return … "FORBIDDEN"`` (never MAX_ATTEMPTS_EXHAUSTED); p10 message mentions Public/403.
  * A-7  ``BridgeConfig.generation_started``: reset per attempt, raised on the first real pid / carry_pid resume;
         cancel after start ⇒ balance 0 + 29h, cancel before start ⇒ legacy active release.
  * C-2  real COMPLETED (not a model decline) ⇒ ``last_success_at`` kept + balance 0 + 29h cooldown.
  * Untouched: 01.03 / verifier / 05.02 (sha e1216b51…), 01.33 stays CRLF.

Everything is offline: temp JSON files, mocked engine, no network.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import inspect
import json
import pathlib
import re
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE.read_text(encoding="utf-8")
EMAIL_A = "p59-alpha@example.com"
EMAIL_B = "p59-beta@example.com"
PID_A = "59595959-aaaa-4bbb-8ccc-000000000001"


def _load_bridge_module():
    spec = importlib.util.spec_from_file_location("bridge_p59", str(BRIDGE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p59"] = mod
    spec.loader.exec_module(mod)
    return mod


def _extract_func(src: str, name: str) -> str:
    m = re.search(rf"^def {name}\(", src, re.MULTILINE)
    assert m, f"function not found: {name}"
    sig_end = re.search(r"\)\s*(?:->[^:\n]+)?:[ \t]*\n", src[m.end():])
    assert sig_end, f"signature end not found: {name}"
    scan_from = m.end() + sig_end.end()
    nxt = re.search(r"^(?!\s)(?!#)\S", src[scan_from:], re.MULTILINE)
    end = scan_from + (nxt.start() if nxt else len(src) - scan_from)
    return src[m.start():end]


bridge = _load_bridge_module()
FAILOVER_SRC = _extract_func(BRIDGE_SRC, "send_message_with_auto_account_failover")
SEND_PUBLIC_SRC = _extract_func(BRIDGE_SRC, "send_message_and_make_public")
ELIGIBLE_SRC = _extract_func(BRIDGE_SRC, "get_eligible_accounts")


class _FakeEngine(types.SimpleNamespace):
    """Minimal stand-in for 01.03: Config + check_balance; anything else raises (never reached)."""

    def __init__(self, balances):
        super().__init__()
        self._balances = list(balances)
        self.calls = 0

        class Config:  # noqa: D401 - plain attribute bag
            def __init__(self):
                self.model = None

        self.Config = Config

    def check_balance(self, cookies):
        self.calls += 1
        if self._balances:
            return self._balances.pop(0)
        return -1


class _Fixture(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = pathlib.Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.primary = self.tmp / "accounts_genspark.json"
        self.vault = self.tmp / "accounts_cooldown.json"
        self.accounts = [
            {"email": EMAIL_A, "password": "secret-a", "cookies": {"session_id": "x"}, "last_refresh": time.time(),
             "status": "active", "active": True, "balance": 73},
            {"email": EMAIL_B, "password": "secret-b", "cookies": {"session_id": "y"}, "last_refresh": time.time(),
             "status": "active", "active": True, "balance": 250},
        ]
        self.write_primary(self.accounts)
        self.logs = self.patch("log_event")

    def patch(self, name, **kwargs):
        return self.stack.enter_context(mock.patch.object(bridge, name, **kwargs))

    def write_primary(self, accounts):
        self.primary.write_text(json.dumps(accounts, ensure_ascii=False, indent=2), encoding="utf-8")

    def read(self, path=None):
        path = path or self.primary
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def rec(self, email=EMAIL_A):
        return next((a for a in (self.read() or []) if a.get("email") == email), None)


# ── 01–03: mark_account_cooldown(balance=) ───────────────────────────────────

class TestMarkCooldownBalance(_Fixture):
    def test_01_balance_omitted_keeps_existing_value(self):
        self.assertTrue(bridge.mark_account_cooldown(EMAIL_A, cooldown_hours=29.0, json_path=str(self.primary)))
        a = self.rec()
        self.assertEqual(a["balance"], 73, "A-6: temporary faults never touch the recorded balance")
        self.assertEqual(a["status"], "cooldown")
        self.assertFalse(a["active"])
        self.assertAlmostEqual(a["cooldown_until"], time.time() + 29 * 3600, delta=60)

    def test_02_balance_zero_written_when_passed(self):
        bridge.mark_account_cooldown(EMAIL_A, cooldown_hours=29.0, json_path=str(self.primary), balance=0)
        a = self.rec()
        self.assertEqual(a["balance"], 0)
        self.assertIsInstance(a["balance"], int)
        self.assertEqual(a["status"], "cooldown")

    def test_03_signature_is_backward_compatible(self):
        params = list(inspect.signature(bridge.mark_account_cooldown).parameters)
        self.assertEqual(params, ["email", "cooldown_hours", "json_path", "balance"])
        self.assertIsNone(inspect.signature(bridge.mark_account_cooldown).parameters["balance"].default)


# ── 04–06: real balance persisted before LOW_BALANCE exits ───────────────────

class _PreflightFixture(_Fixture):
    def setUp(self):
        super().setUp()
        self.cfg = bridge.BridgeConfig()
        self.cfg.min_preflight_balance = 100
        self.cooldown = self.patch("mark_account_cooldown", wraps=bridge.mark_account_cooldown)
        self.patch("get_account_fingerprint", return_value={"browser": "chrome120", "user_agent": "t"})
        self.patch("needs_web_search", return_value=False)
        self.move = self.patch("move_account_to_cooldown_vault", return_value=True)
        self.stack.enter_context(mock.patch.object(bridge.time, "sleep"))

    def _send(self, engine, refresh=None):
        self.patch("get_genspark_engine", return_value=engine)
        self.refresh = self.patch("refresh_cookies_on_401", return_value=refresh)
        return bridge.send_message_and_make_public(
            None, EMAIL_A, "secret-a", "build it", bridge_cfg=self.cfg, json_path=str(self.primary))


class TestLowBalanceWritesRealValue(_PreflightFixture):
    def test_04_preflight_low_balance_persists_real_number(self):
        eng = _FakeEngine([40])
        _u, status, *_ = self._send(eng)
        self.assertEqual(status, "LOW_BALANCE")
        a = self.rec()
        self.assertEqual(a["balance"], 40, "A-4: the real balance (not 0, not stale 73) is stored")
        self.assertEqual(a["status"], "cooldown")
        self.assertEqual(eng.calls, 1)
        self.assertFalse(self.move.called)
        self.cooldown.assert_called_once()
        self.assertNotIn("balance", self.cooldown.call_args.kwargs, "A-6: LOW_BALANCE passes no balance= (real value already written)")

    def test_05_recheck_after_refresh_persists_real_number(self):
        eng = _FakeEngine([-2, 55])
        _u, status, *_ = self._send(eng, refresh={"session_id": "fresh"})
        self.assertEqual(status, "LOW_BALANCE")
        self.assertTrue(self.refresh.called)
        a = self.rec()
        self.assertEqual(a["balance"], 55)
        self.assertEqual(a["status"], "cooldown")
        self.assertEqual(eng.calls, 2)

    def test_06_source_every_in_place_low_balance_exit_has_balance_write(self):
        # Three in-place LOW_BALANCE exits (bal_check / bal_recheck / bal_mid) must each be preceded by a real
        # balance write; the D35 vault exit (account moved) is the only LOW_BALANCE return without one.
        exits = [m.start() for m in re.finditer(r'return None, "LOW_BALANCE", None, None, None', SEND_PUBLIC_SRC)]
        self.assertEqual(len(exits), 4, "3 in-place exits + 1 D35 vault exit")
        with_write = [e for e in exits if '{"balance": int(' in SEND_PUBLIC_SRC[max(0, e - 900):e]]
        self.assertEqual(len(with_write), 3)
        vault_exit = [e for e in exits if e not in with_write][0]
        self.assertIn("ZERO_BALANCE_STALE_GIFT", SEND_PUBLIC_SRC[max(0, vault_exit - 700):vault_exit])
        self.assertIn("bal_mid", SEND_PUBLIC_SRC)
        self.assertEqual(SEND_PUBLIC_SRC.count("[MAINT-10/A-4"), 3)


# ── 07–11: offline balance filter ────────────────────────────────────────────

class TestOfflineBalanceFilter(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.logs = self.stack.enter_context(mock.patch.object(bridge, "log_event"))

    @staticmethod
    def _acc(email, **extra):
        d = {"email": email, "status": "active", "active": True, "last_used": 1.0}
        d.update(extra)
        return d

    def test_07_constant_and_purity(self):
        self.assertEqual(bridge.OFFLINE_MIN_BALANCE, 100)
        self.assertIsInstance(bridge.OFFLINE_MIN_BALANCE, int)
        for token in ("requests.", "check_balance", "update_account_data(", "mark_account_cooldown(",
                      "move_account_to_cooldown_vault("):
            self.assertNotIn(token, ELIGIBLE_SRC, f"A-2: get_eligible_accounts stays offline/pure ({token})")

    def test_08_low_numeric_excluded_high_kept(self):
        accs = [self._acc("a0@example.com", balance=0), self._acc("a99@example.com", balance=99),
                self._acc("a100@example.com", balance=100), self._acc("a250@example.com", balance=250.0)]
        with mock.patch.object(bridge, "GIFT_PREFLIGHT_ENABLED", False):
            out = bridge.get_eligible_accounts(accs, set())
        self.assertEqual([a["email"] for a in out], ["a100@example.com", "a250@example.com"])
        msgs = [str(c.args[1]) for c in self.logs.call_args_list if len(c.args) > 1]
        self.assertEqual(sum("[OFFLINE_BALANCE]" in m for m in msgs), 2)

    def test_09_unknown_balance_fails_open(self):
        accs = [self._acc("n@example.com", balance=None), self._acc("m@example.com"),
                self._acc("s@example.com", balance="abc"), self._acc("t@example.com", balance=True),
                self._acc("f@example.com", balance=False)]
        with mock.patch.object(bridge, "GIFT_PREFLIGHT_ENABLED", False):
            out = bridge.get_eligible_accounts(accs, set())
        self.assertEqual(len(out), 5, "A-2/A-3: None / missing / non-numeric / bool never exclude")

    def test_10_filter_order_ready_then_balance_then_gift(self):
        i_ready = ELIGIBLE_SRC.index("is_account_ready(acc)")
        i_bal = ELIGIBLE_SRC.index("OFFLINE_MIN_BALANCE")
        i_gift = ELIGIBLE_SRC.index("GIFT_PREFLIGHT_ENABLED")
        self.assertLess(i_ready, i_bal)
        self.assertLess(i_bal, i_gift)
        # cooled account with low balance is already dropped by is_account_ready (no OFFLINE log)
        cooled = self._acc("c@example.com", status="cooldown", cooldown_until=time.time() + 3600, balance=0)
        with mock.patch.object(bridge, "GIFT_PREFLIGHT_ENABLED", False):
            out = bridge.get_eligible_accounts([cooled], set())
        self.assertEqual(out, [])
        self.assertFalse(any("[OFFLINE_BALANCE]" in str(c.args[1]) for c in self.logs.call_args_list if len(c.args) > 1))

    def test_11_tried_emails_still_respected(self):
        accs = [self._acc("x@example.com", balance=500), self._acc("y@example.com", balance=500)]
        with mock.patch.object(bridge, "GIFT_PREFLIGHT_ENABLED", False):
            out = bridge.get_eligible_accounts(accs, {"x@example.com"})
        self.assertEqual([a["email"] for a in out], ["y@example.com"])


# ── 12–13: reactivate writes balance 100 ─────────────────────────────────────

class TestReactivateWritesHundred(_Fixture):
    def test_12_expired_cooldown_reactivates_with_balance_100(self):
        self.accounts[0].update({"status": "cooldown", "active": False, "cooldown_until": time.time() - 10, "balance": 0})
        self.write_primary(self.accounts)
        out = bridge.reactivate_account_if_due(dict(self.accounts[0]), json_path=str(self.primary))
        self.assertEqual(out["balance"], 100)
        self.assertEqual(out["status"], "active")
        a = self.rec()
        self.assertEqual(a["balance"], 100, "C-1 / D-01: default 100 after the 29h window")
        self.assertEqual(a["cooldown_until"], 0)
        self.assertTrue(a["active"])
        self.assertIn("cooldown_released_at", a)

    def test_13_still_cooling_is_untouched(self):
        self.accounts[0].update({"status": "cooldown", "active": False, "cooldown_until": time.time() + 3600, "balance": 0})
        self.write_primary(self.accounts)
        out = bridge.reactivate_account_if_due(dict(self.accounts[0]), json_path=str(self.primary))
        self.assertEqual(out["status"], "cooldown")
        a = self.rec()
        self.assertEqual(a["balance"], 0)
        self.assertEqual(a["status"], "cooldown")


# ── 14–22: failover surface (403 / cancel / COMPLETED) ───────────────────────

class _FailoverFixture(_Fixture):
    def setUp(self):
        super().setUp()
        self.cfg = bridge.BridgeConfig()
        self.cfg.max_account_attempts = 2
        self.cfg.selection_project_key = "pk-59"
        self.cooldown = self.patch("mark_account_cooldown", wraps=bridge.mark_account_cooldown)
        self.patch("get_account_fingerprint", return_value={"browser": "chrome120", "user_agent": "t"})
        self.patch("apply_project_runtime_binding")
        self.observer = self.patch("notify_account_selection_observer")
        self.patch("claim_eligible_account_for_owner",
                   side_effect=lambda accs, tried, *a, **k: next(
                       ((a_, accs, "claimed") for a_ in accs if a_["email"] not in tried), (None, accs, "no-eligible")))
        self.patch("release_account_selection")
        self.move = self.patch("move_account_to_cooldown_vault", return_value=True)
        self.stack.enter_context(mock.patch.object(bridge.time, "sleep"))

    def _run(self, outcomes):
        url = bridge.build_genspark_viewer_url(PID_A)
        side = []
        for item in outcomes:
            if callable(item):
                side.append(item)
            else:
                status, text = item
                side.append((url, status, None, text, None))

        def _dispatch(*a, **k):
            nxt = side.pop(0)
            if callable(nxt):
                return nxt(*a, **k)
            return nxt
        self.sends = self.patch("send_message_and_make_public", side_effect=_dispatch)
        return bridge.send_message_with_auto_account_failover(
            None, "build it", bridge_cfg=self.cfg, json_path=str(self.primary))


class TestForbiddenSourceContracts(_FailoverFixture):
    def test_14_single_forbidden_branch_returns_with_300s(self):
        self.assertEqual(FAILOVER_SRC.count('if status == "FORBIDDEN":'), 1)
        blk_start = FAILOVER_SRC.index('if status == "FORBIDDEN":')
        blk = FAILOVER_SRC[blk_start:blk_start + 900]
        first_ctrl = re.search(r"^\s+(return|break|continue)\b", blk, re.MULTILINE)
        self.assertIsNotNone(first_ctrl)
        self.assertEqual(first_ctrl.group(1), "return", "A-1: return, not break (break would reach MAX_ATTEMPTS_EXHAUSTED)")
        self.assertIn('return pub_url, "FORBIDDEN", curr_acc, ext_dir, last_text', blk)
        self.assertIn('"cooldown_until": time.time() + 300', blk)
        self.assertIn('"forbidden-stop"', blk)
        self.assertNotIn('reason="FORBIDDEN"', FAILOVER_SRC, "A-1: no vault move with reason FORBIDDEN")
        self.assertNotIn("register_forbidden_hit", FAILOVER_SRC)
        self.assertLess(blk_start, FAILOVER_SRC.index('status == "COMPLETED"'))

    def test_15_other_vault_reasons_and_breaker_unchanged(self):
        self.assertIn("FORBIDDEN", bridge.COOLDOWN_VAULT_REASONS)   # tuple itself untouched (A-1 bypasses it)
        for r in ("EMPTY_STREAM_FAILED", "LOGIN_FAILED", "BALANCE_UNREADABLE", "ZERO_BALANCE_STALE_GIFT"):
            self.assertIn(r, bridge.COOLDOWN_VAULT_REASONS)
        self.assertEqual(bridge.P44_STRUCTURED_STATUSES, ("CREDIT_EXHAUSTED", "DATA_RETENTION", "SESSION_EXPIRED", "FORBIDDEN"))
        self.assertEqual(bridge.BALANCE_UNREADABLE_BREAKER_N, 2)
        self.assertIn("reason=EMPTY_STREAM_FAILED_STATUS", FAILOVER_SRC)   # D10 move path still present
        self.assertEqual(FAILOVER_SRC.count('reason="LOGIN_FAILED"'), 2)     # D26 C1 both 401 sites untouched

    def test_16_terminal_message_explains_private_project(self):
        out = bridge.describe_terminal_outcome("FORBIDDEN", None, self.cfg)
        blob = json.dumps(out, ensure_ascii=False)
        self.assertEqual(out["kind"], "failure")
        self.assertIn("Public", blob)
        self.assertIn("403", blob)
        self.assertIn("Private", blob)
        self.assertFalse(out.get("allow_preview"))

    def test_16b_runtime_forbidden_stops_in_place(self):
        _u, status, acc, _e, _t = self._run([("FORBIDDEN", ""), ("COMPLETED", "ok")])
        self.assertEqual(status, "FORBIDDEN")
        self.assertEqual(self.sends.call_count, 1)
        self.assertEqual(acc["email"], EMAIL_A)
        a = self.rec()
        self.assertEqual(a["balance"], 73, "A-6: 403 never changes balance")
        self.assertTrue(a["active"])
        self.assertEqual(a["status"], "active")
        self.assertAlmostEqual(a["cooldown_until"], time.time() + 300, delta=30)
        self.assertFalse(self.move.called)
        self.assertFalse(self.cooldown.called)
        self.assertFalse(self.vault.exists())
        self.assertTrue(any(c.args[1] == "forbidden-stop" for c in self.observer.call_args_list))
        b = self.rec(EMAIL_B)
        self.assertEqual(b["balance"], 250)
        self.assertNotIn("cooldown_until", b)


class TestCancelBoundary(_FailoverFixture):
    def test_17_cancel_before_start_releases_account_without_cooldown(self):
        self.cfg.generation_started = True        # stale flag from a previous task must be reset per attempt
        _u, status, acc, _e, _t = self._run([(bridge.CANCELLED_STATUS, "")])
        self.assertEqual(status, bridge.CANCELLED_STATUS)
        a = self.rec()
        self.assertEqual(a["status"], "active")
        self.assertEqual(a["balance"], 73)
        self.assertNotIn("cooldown_until", a)
        self.assertFalse(self.cooldown.called)
        self.assertFalse(self.cfg.generation_started)

    def test_18_cancel_after_first_stream_event_costs_the_account(self):
        url = bridge.build_genspark_viewer_url(PID_A)

        def _send(*a, **k):
            k["bridge_cfg"].generation_started = True   # what _pid_capture_callback does on the first real pid
            return url, bridge.CANCELLED_STATUS, None, "", None
        _u, status, acc, _e, _t = self._run([_send])
        self.assertEqual(status, bridge.CANCELLED_STATUS)
        self.assertEqual(self.sends.call_count, 1)
        a = self.rec()
        self.assertEqual(a["balance"], 0)
        self.assertEqual(a["status"], "cooldown")
        self.assertFalse(a["active"])
        self.assertAlmostEqual(a["cooldown_until"], time.time() + self.cfg.cooldown_hours * 3600, delta=60)
        self.cooldown.assert_called_once_with(EMAIL_A, cooldown_hours=self.cfg.cooldown_hours,
                                              json_path=str(self.primary), balance=0)

    def test_19_flag_contract_in_source(self):
        self.assertFalse(bridge.BridgeConfig().generation_started)
        self.assertGreaterEqual(SEND_PUBLIC_SRC.count("bridge_cfg.generation_started = True"), 2,
                                "A-7: raised in _pid_capture_callback and on carry_pid resume")
        self.assertEqual(FAILOVER_SRC.count("bridge_cfg.generation_started = False"), 1)
        i_reset = FAILOVER_SRC.index("bridge_cfg.generation_started = False")
        i_send = FAILOVER_SRC.index("send_message_and_make_public(")
        self.assertLess(i_reset, i_send, "reset happens before the attempt's send")
        cb = SEND_PUBLIC_SRC[SEND_PUBLIC_SRC.index("def _pid_capture_callback"):]
        cb = cb[:cb.index("on_project_start_callback(live_pid)")]
        self.assertIn("generation_started = True", cb)
        self.assertIn('startswith("__")', cb, "sentinel pids never raise the flag")


class TestCompletedConsumesAccount(_FailoverFixture):
    def test_20_real_completed_keeps_success_and_cools_29h(self):
        _u, status, acc, _e, _t = self._run([("COMPLETED", "Here is your finished website with all pages.")])
        self.assertEqual(status, "COMPLETED")
        a = self.rec()
        self.assertIn("last_success_at", a, "U-6: last_success_at is kept")
        self.assertEqual(a["balance"], 0)
        self.assertEqual(a["status"], "cooldown")
        self.assertFalse(a["active"])
        self.assertAlmostEqual(a["cooldown_until"], time.time() + self.cfg.cooldown_hours * 3600, delta=60)
        self.cooldown.assert_called_once_with(EMAIL_A, cooldown_hours=self.cfg.cooldown_hours,
                                              json_path=str(self.primary), balance=0)

    def test_21_model_decline_is_not_consumption(self):
        self.patch("is_model_decline_response", return_value=True)
        _u, status, acc, _e, _t = self._run([("COMPLETED", "I can't help with that request.")])
        self.assertEqual(status, "COMPLETED")
        a = self.rec()
        self.assertEqual(a["status"], "active")
        self.assertTrue(a["active"])
        self.assertEqual(a["balance"], 73)
        self.assertEqual(a["cooldown_until"], 0)
        self.assertFalse(self.cooldown.called)

    def test_22_balance_zero_sites_are_exactly_the_consumption_points(self):
        sites = [m.start() for m in re.finditer(r"json_path=json_path, balance=0\)", FAILOVER_SRC)]
        self.assertEqual(len(sites), 4, "cancel-after-start, CREDIT_EXHAUSTED x2, COMPLETED")
        for s in sites:
            ctx = FAILOVER_SRC[max(0, s - 400):s]
            self.assertNotIn("DATA_RETENTION_TRIGGERED", ctx)
            self.assertNotIn('status == "DATA_RETENTION"', ctx)
            self.assertNotIn("DEC07_EMPTY_COOLDOWN_HOURS", ctx)
        self.assertEqual(SEND_PUBLIC_SRC.count("balance=0)"), 0, "no zeroing inside the pre-flight layer")


# ── 23: untouched surfaces ───────────────────────────────────────────────────

class TestUntouched(unittest.TestCase):
    def test_23_protected_files_and_line_endings(self):
        raw = BRIDGE.read_bytes()
        self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"), "01.33 stays pure CRLF")
        manager = (ROOT / "05.02_genspark_delayed_gifts_manager.py").read_bytes()
        self.assertEqual(manager.count(b"\r"), 0)
        self.assertTrue(hashlib.sha256(manager).hexdigest().startswith("e1216b5186d99420"), "05.02 untouched")
        engine = (ROOT / "01.03Genspark_claude-opus-5-code.py").read_text(encoding="utf-8", errors="ignore")
        self.assertNotIn("generation_started", engine)
        self.assertNotIn("MAINT-10", engine)
        self.assertNotIn("MAINT-10", (ROOT / "genspark_verifier_engine.py").read_text(encoding="utf-8", errors="ignore"))


if __name__ == "__main__":
    unittest.main()
