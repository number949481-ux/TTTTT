"""P53 — MAINT-4-B: Blind N=1 instant move + persistent vault + full-data ``account_log.jsonl``
+ cross-process lockfile + 05.02 dual-run readiness (owner card EXECUTE_NOW 2026-11-01, D26–D39, C1–C7).

Contract under test (RESUME.md §3.11 / §3.11.8):
  * D26  any refusal (403), LOGIN_FAILED after session→credentials, unreadable balance ⇒ immediate blind
         move to ``accounts_cooldown.json`` (N=1, no hit cache, no 5-minute wait). The 5-minute cooldown
         survives ONLY as the fallback when the move itself fails (hot-loop guard).
         Balance 0 + daily gift STALE (>=14d, 05.02 snapshot) ⇒ move too; FRESH/UNKNOWN ⇒ legacy 29h (D35).
  * D27  vault is persistent: no time-based revival anywhere in 01.33; ``cooldown_until_ts``/
         ``COOLDOWN_VAULT_HOURS`` removed (C2).
  * D28  ``account_log.jsonl`` JSON Lines, one line per move, FULL account data (email, password,
         cookies, time, reason, path) — owner's local decision, no masking. 01.33 appends O(1);
         trimming (30d / 5000) happens only when 05.02 ``run_revival`` starts (D32).
  * D33  R-A (05.02 reloads the vault from disk before saving) + R-B (shared lockfile
         ``accounts_cooldown.json.lock`` used by both programs, O_CREAT|O_EXCL, timeout, orphan override).
  * D34  task-level breaker: two consecutive BALANCE_UNREADABLE accounts in one failover ⇒ NETWORK_DOWN.
  * D37  ``.gitignore`` covers ``account_log.jsonl*``, ``*.lock``, ``*.cooldown_move.bak``,
         ``accounts*.json.tmp*``, ``*.bak``.
  * D38  ``run_revival(limit=0)`` scans everything (CLI ``-l 0``).  D39  ``main()`` exit code != 0 on error.

Everything is offline: real temp JSON files, the real ``FILE_LOCK``, no network.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "01.33_telegram_gen_bridge.py"
MANAGER = ROOT / "05.02_genspark_delayed_gifts_manager.py"
BRIDGE_SRC = BRIDGE.read_text(encoding="utf-8")
MANAGER_SRC = MANAGER.read_text(encoding="utf-8")
PID_A = "11111111-aaaa-4bbb-8ccc-000000000001"
EMAIL_A = "p53.alpha@test.invalid"
EMAIL_B = "p53.beta@test.invalid"
EMAIL_C = "p53.gamma@test.invalid"
LOCK_NAME = "accounts_cooldown.json.lock"


def _load_bridge_module():
    spec = importlib.util.spec_from_file_location("bridge_p53", str(BRIDGE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p53"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_manager_module():
    stub = types.ModuleType("genspark_master_account_manager")
    for name in ("do_b2c_login", "get_session", "check_account_balance"):
        setattr(stub, name, lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("stub")))
    sys.modules.setdefault("genspark_master_account_manager", stub)
    spec = importlib.util.spec_from_file_location("manager_p53", str(MANAGER))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["manager_p53"] = mod
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


class _FakeEngine:
    """Minimal 01.03 stand-in for the P13 pre-flight: only ``Config`` + ``check_balance``."""

    class Config:
        def __init__(self):
            self.model = None

    def __init__(self, balances):
        self._balances = list(balances)
        self.calls = 0

    def check_balance(self, cookies):
        self.calls += 1
        v = self._balances[min(self.calls - 1, len(self._balances) - 1)]
        if isinstance(v, Exception):
            raise v
        return v


class _VaultFixture(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = pathlib.Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.primary = self.tmp / "accounts_genspark.json"
        self.vault = self.tmp / "accounts_cooldown.json"
        self.log = self.tmp / "account_log.jsonl"
        self.lock = self.tmp / LOCK_NAME
        self.accounts = [
            {"email": EMAIL_A, "password": "secret-a", "cookies": {"session_id": "x"}, "last_refresh": time.time(),
             "status": "active", "active": True},
            {"email": EMAIL_B, "password": "secret-b", "cookies": {"session_id": "y"}, "last_refresh": time.time(),
             "status": "active", "active": True},
            {"email": EMAIL_C, "password": "secret-c", "cookies": {"session_id": "z"}, "last_refresh": time.time(),
             "status": "active", "active": True},
        ]
        self.write_primary(self.accounts)
        self.logs = self.patch("log_event")

    def patch(self, name, **kwargs):
        return self.stack.enter_context(mock.patch.object(bridge, name, **kwargs))

    def write_primary(self, accounts):
        self.primary.write_text(json.dumps(accounts, ensure_ascii=False, indent=2), encoding="utf-8")

    def read(self, path):
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def primary_rec(self, email=EMAIL_A):
        return next((a for a in (self.read(self.primary) or []) if a.get("email") == email), None)

    def vault_record(self, email=EMAIL_A):
        return next((a for a in (self.read(self.vault) or []) if a.get("email") == email), None)

    def log_lines(self):
        if not self.log.exists():
            return []
        return [json.loads(l) for l in self.log.read_text(encoding="utf-8").splitlines() if l.strip()]

    def log_messages(self):
        return [str(c.args[1]) for c in self.logs.call_args_list if len(c.args) > 1]


class _FailoverFixture(_VaultFixture):
    def setUp(self):
        super().setUp()
        self.cfg = bridge.BridgeConfig()
        self.cfg.max_account_attempts = 3
        self.cfg.selection_project_key = "pk-53"
        self.cooldown = self.patch("mark_account_cooldown", wraps=bridge.mark_account_cooldown)
        self.patch("get_account_fingerprint", return_value={"browser": "chrome120", "user_agent": "t"})
        self.patch("apply_project_runtime_binding")
        self.patch("notify_account_selection_observer")
        self.patch("claim_eligible_account_for_owner",
                   side_effect=lambda accs, tried, *a, **k: next(
                       ((a_, accs, "claimed") for a_ in accs if a_["email"] not in tried), (None, accs, "no-eligible")))
        self.patch("release_account_selection")
        self.stack.enter_context(mock.patch.object(bridge.time, "sleep"))

    def _run(self, statuses, pid=PID_A):
        url = bridge.build_genspark_viewer_url(pid)
        sends = self.patch("send_message_and_make_public",
                           side_effect=[(url, s, None, "" if s != "COMPLETED" else "ok", None) for s in statuses])
        result = bridge.send_message_with_auto_account_failover(
            None, "build it", bridge_cfg=self.cfg, json_path=str(self.primary))
        return sends, result


class _PreflightFixture(_VaultFixture):
    """Drives ``send_message_and_make_public`` only up to the P13 pre-flight gate."""

    def setUp(self):
        super().setUp()
        self.cfg = bridge.BridgeConfig()
        self.cooldown = self.patch("mark_account_cooldown", wraps=bridge.mark_account_cooldown)
        self.patch("get_account_fingerprint", return_value={"browser": "chrome120", "user_agent": "t"})
        self.stack.enter_context(mock.patch.object(bridge.time, "sleep"))

    def preflight(self, balances, email=EMAIL_A, refresh=None):
        eng = _FakeEngine(balances)
        self.patch("get_genspark_engine", return_value=eng)
        self.patch("refresh_cookies_on_401", side_effect=refresh if callable(refresh) else (lambda *a, **k: refresh))
        return bridge.send_message_and_make_public(None, email, "pw", "hi", bridge_cfg=self.cfg,
                                                   json_path=str(self.primary))


# ── 35–37: M1 blind FORBIDDEN move ───────────────────────────────────────────

class TestBlindForbidden(_FailoverFixture):
    def test_35_first_forbidden_moves_immediately_no_hits_cache(self):
        sends, (pub_url, status, acc, _e, _t) = self._run(["FORBIDDEN", "COMPLETED"])
        self.assertEqual(sends.call_count, 2)
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(acc["email"], EMAIL_B)
        self.assertIsNone(self.primary_rec(), "N=1: the 403 account is cut from primary on the FIRST hit")
        rec = self.vault_record()
        self.assertEqual(rec["quarantine_info"]["reason"], "cooldown_forbidden")
        self.assertEqual(rec["quarantine_info"]["pid"], PID_A)
        self.assertNotIn("forbidden_hits", rec)
        self.assertNotIn("cooldown_until_ts", rec["quarantine_info"])          # D27 / C2
        self.assertNotIn("last_success_at", rec)                               # T5 stays fixed
        self.assertFalse(self.cooldown.called)

    def test_36_no_threshold_machinery_left_in_source(self):
        for token in ("register_forbidden_hit", "FORBIDDEN_MOVE_AFTER_N", "FORBIDDEN_HITS_WINDOW_HOURS",
                      "COOLDOWN_VAULT_HOURS", "_ACCOUNT_LOG_FORBIDDEN_KEYS", "cooldown_until_ts", "forbidden_hits"):
            self.assertNotIn(token, BRIDGE_SRC, f"D26/D27: {token} must be gone from 01.33")
        for reason in ("FORBIDDEN", "EMPTY_STREAM_FAILED", "LOGIN_FAILED", "BALANCE_UNREADABLE", "ZERO_BALANCE_STALE_GIFT"):
            self.assertIn(reason, bridge.COOLDOWN_VAULT_REASONS)
        self.assertTrue(bridge.ACCOUNT_LOG_FILENAME.endswith(".jsonl"), "D28/D32: JSON Lines")
        self.assertEqual(bridge.COOLDOWN_VAULT_LOCK_FILENAME, LOCK_NAME)
        self.assertEqual(bridge.BALANCE_UNREADABLE_BREAKER_N, 2)
        body = _extract_func(BRIDGE_SRC, "send_message_with_auto_account_failover")
        self.assertEqual(body.count('status == "FORBIDDEN"'), 1)
        self.assertLess(body.index('status == "FORBIDDEN"'), body.index('if pub_url or status == "COMPLETED"'))

    def test_37_move_failure_falls_back_to_5_minutes_only(self):
        self.patch("move_account_to_cooldown_vault", return_value=False)
        sends, (_u, status, acc, _e, _t) = self._run(["FORBIDDEN", "COMPLETED"])
        self.assertEqual(acc["email"], EMAIL_B)
        a = self.primary_rec()
        self.assertAlmostEqual(a["cooldown_until"], time.time() + 300, delta=30)
        self.assertNotIn("last_success_at", a)


# ── 38–41: M2 LOGIN_FAILED, D27 guard, M4 zero balance ──────────────────────

class TestLoginFailedAndZeroBalance(_PreflightFixture):
    def test_38_login_failed_after_session_then_credentials_moves_to_vault(self):
        self.accounts[0]["last_refresh"] = 1.0
        self.write_primary(self.accounts)
        result = self.preflight([-2], refresh=None)          # session dead, credentials login failed
        self.assertEqual(result[1], "LOGIN_FAILED")
        self.assertIsNone(self.primary_rec())
        rec = self.vault_record()
        self.assertEqual(rec["quarantine_info"]["reason"], "cooldown_login_failed")
        self.assertEqual(rec["password"], "secret-a")
        # C1: all four auth_failed+1800s sites are gone from 01.33
        self.assertEqual(len(re.findall(r'"auth_failed",\s*"active":\s*False,\s*"cooldown_until":\s*time\.time\(\)\s*\+\s*1800', BRIDGE_SRC)), 0)
        self.assertEqual(BRIDGE_SRC.count("time.time() + 1800"), 0, "no 30-minute auth ban anywhere (C1)")

    def test_39_d27_guard_no_vault_reader_or_timer_in_bridge(self):
        for name in ("read_accounts_safe", "get_eligible_accounts", "is_account_ready", "claim_eligible_account_for_owner"):
            fn = _extract_func(BRIDGE_SRC, name)
            self.assertNotIn("COOLDOWN_VAULT", fn)
            self.assertNotIn("accounts_cooldown", fn)
        move_body = _extract_func(BRIDGE_SRC, "move_account_to_cooldown_vault")
        self.assertNotIn("hours", move_body.lower(), "no hour/timer metadata in the vault record")
        ok = bridge.move_account_to_cooldown_vault(EMAIL_A, "FORBIDDEN", json_path=str(self.primary))
        self.assertTrue(ok)
        qi = self.vault_record()["quarantine_info"]
        self.assertEqual(set(qi) & {"cooldown_until_ts", "cooldown_hours", "revive_at"}, set())

    def test_40_zero_balance_with_stale_gift_moves(self):
        self.accounts[0].update({"days_without_gift": 20, "last_checked": time.strftime("%Y-%m-%dT%H:%M:%S")})
        self.write_primary(self.accounts)
        result = self.preflight([0])
        self.assertEqual(result[1], "LOW_BALANCE")
        self.assertIsNone(self.primary_rec())
        self.assertEqual(self.vault_record()["quarantine_info"]["reason"], "cooldown_zero_balance_stale_gift")
        self.assertFalse(self.cooldown.called)

    def test_41_zero_balance_with_fresh_gift_keeps_29h_cooldown(self):
        self.accounts[0].update({"days_without_gift": 1, "last_checked": time.strftime("%Y-%m-%dT%H:%M:%S")})
        self.write_primary(self.accounts)
        result = self.preflight([0])
        self.assertEqual(result[1], "LOW_BALANCE")
        self.assertIsNotNone(self.primary_rec())
        self.assertIsNone(self.vault_record())
        self.cooldown.assert_called_once()
        # UNKNOWN snapshot (no last_checked) is conservative too (C5)
        self.cooldown.reset_mock()
        self.accounts[0].pop("last_checked")
        self.write_primary(self.accounts)
        self.preflight([0])
        self.assertIsNone(self.vault_record())
        self.cooldown.assert_called_once()


# ── 42–45: jsonl full data, trim in 05.02 only, R-A, R-B ─────────────────────

class TestJsonlAndLocks(_VaultFixture):
    def test_42_jsonl_one_line_per_move_with_full_account_data(self):
        self.assertTrue(bridge.move_account_to_cooldown_vault(
            EMAIL_A, "FORBIDDEN", json_path=str(self.primary), meta={"http_status": 403, "pid": PID_A}))
        self.assertTrue(self.log.exists(), "account_log.jsonl must be written next to the primary file")
        self.assertFalse((self.tmp / "account_log.json").exists(), "legacy JSON list log must not be created")
        lines = self.log_lines()
        self.assertEqual(len(lines), 1, "exactly one line per move, no schema header line")
        e = lines[0]
        self.assertEqual(e["event"], "exit_to_cooldown")
        self.assertEqual(e["email"], EMAIL_A)
        self.assertEqual(e["password"], "secret-a")                       # D28: explicit, no masking
        self.assertEqual(e["cookies"], {"session_id": "x"})
        self.assertEqual(e["reason"], "FORBIDDEN")
        self.assertEqual(e["from_path"], str(self.primary))
        self.assertEqual(e["to_path"], str(self.vault))
        self.assertEqual(e["by"], "01.33")
        for k in ("ts", "at", "http_status", "pid"):
            self.assertIn(k, e)
        # second move of another account appends (O(1)), never rewrites the file
        raw_before = self.log.read_bytes()
        bridge.move_account_to_cooldown_vault(EMAIL_B, "EMPTY_STREAM_FAILED", json_path=str(self.primary))
        raw_after = self.log.read_bytes()
        self.assertTrue(raw_after.startswith(raw_before))
        self.assertEqual(len(self.log_lines()), 2)

    def test_43_bridge_never_trims_jsonl_and_tolerates_corruption(self):
        junk = "{not json\n" + "\n".join(json.dumps({"ts": 1, "event": "x", "email": "old@t"}) for _ in range(10)) + "\n"
        self.log.write_text(junk, encoding="utf-8")
        self.assertTrue(bridge.append_account_log("exit_to_cooldown", {"email": EMAIL_A, "password": "p", "cookies": {}},
                                                  reason="FORBIDDEN", base_dir=self.tmp))
        text = self.log.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(junk), "01.33 is append-only: existing bytes untouched (trim lives in 05.02)")
        self.assertEqual(json.loads(text.splitlines()[-1])["email"], EMAIL_A)
        body = _extract_func(BRIDGE_SRC, "append_account_log")
        for forbidden in ("json.load(", "ACCOUNT_LOG_RETENTION_DAYS", "ACCOUNT_LOG_MAX_ENTRIES", "_atomic_json_dump"):
            self.assertNotIn(forbidden, body, f"append must be O(1): no {forbidden}")

    def test_44_r_a_concurrent_external_vault_change_is_not_lost(self):
        """05.02 run_revival must reload the vault from disk before saving (R-A)."""
        mgr = _load_manager_module()
        folder = self.tmp
        vault = folder / "accounts_cooldown.json"
        primary = folder / "accounts_genspark.json"
        success = folder / "accounts_success.json"
        failed = folder / "accounts_failed.json"
        vault.write_text(json.dumps([
            {"email": EMAIL_A, "password": "a", "cookies": {}, "quarantine_info": {"reason": "cooldown_forbidden"}},
        ]), encoding="utf-8")
        primary.write_text("[]", encoding="utf-8")
        m = mgr.MasterDelayedGiftsManager(primary_path=primary, success_path=success, quarantine_path=vault,
                                          failed_path=failed, dead_path=folder / "dead.json",
                                          threshold_days=14, sort_by_balance=False, auto_relogin=False,
                                          min_delay=0, max_delay=0)

        def fake_status(acc):
            # while 05.02 is "checking" EMAIL_A, 01.33 moves EMAIL_B into the vault
            data = json.loads(vault.read_text(encoding="utf-8"))
            data.append({"email": EMAIL_B, "password": "b", "cookies": {}, "quarantine_info": {"reason": "cooldown_forbidden"}})
            vault.write_text(json.dumps(data), encoding="utf-8")
            return "HEALTHY", 1, "x", 500, None

        with mock.patch.object(m, "check_account_status", side_effect=fake_status), \
             mock.patch.object(mgr.time, "sleep"), mock.patch("builtins.print"):
            res = m.run_revival(limit=0)
        self.assertEqual(res["revived"], 1)
        emails = [a["email"] for a in json.loads(vault.read_text(encoding="utf-8"))]
        self.assertEqual(emails, [EMAIL_B], "R-A: the account added by 01.33 mid-run must survive the save")
        self.assertEqual([a["email"] for a in json.loads(primary.read_text(encoding="utf-8"))], [EMAIL_A])
        # D28 in 05.02: one full-data line for the return move
        lines = [json.loads(l) for l in (folder / "account_log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        ret = [l for l in lines if l["event"] == "return_to_primary"]
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]["email"], EMAIL_A)
        self.assertEqual(ret[0]["password"], "a")
        self.assertEqual(ret[0]["by"], "05.02")
        self.assertEqual(ret[0]["from_path"], str(vault))
        self.assertEqual(ret[0]["to_path"], str(primary))

    def test_45_r_b_shared_lockfile_blocks_and_overrides_orphan(self):
        # 1) a live lock held by "another process" blocks the move until released
        self.lock.write_text(str(os.getpid()), encoding="utf-8")
        done = threading.Event()
        result = {}

        def worker():
            result["ok"] = bridge.move_account_to_cooldown_vault(EMAIL_A, "FORBIDDEN", json_path=str(self.primary))
            done.set()

        with mock.patch.object(bridge, "COOLDOWN_VAULT_LOCK_TIMEOUT_S", 3.0), \
             mock.patch.object(bridge, "COOLDOWN_VAULT_LOCK_ORPHAN_S", 60.0):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            time.sleep(0.4)
            self.assertFalse(done.is_set(), "move must wait while the shared lockfile exists")
            self.lock.unlink()
            self.assertTrue(done.wait(5))
        self.assertTrue(result["ok"])
        self.assertFalse(self.lock.exists(), "lock released after the move")
        # 2) an orphan lock (older than COOLDOWN_VAULT_LOCK_ORPHAN_S) is overridden with a warning
        self.lock.write_text("dead", encoding="utf-8")
        old = time.time() - 3600
        os.utime(self.lock, (old, old))
        self.assertTrue(bridge.move_account_to_cooldown_vault(EMAIL_B, "FORBIDDEN", json_path=str(self.primary)))
        self.assertTrue(any("orphan" in m.lower() or "يتيم" in m for m in self.log_messages()))
        self.assertFalse(self.lock.exists())
        # 3) 05.02 uses the very same lock name
        self.assertIn(LOCK_NAME, MANAGER_SRC)
        self.assertIn("O_EXCL", MANAGER_SRC)
        self.assertIn("O_EXCL", _extract_func(BRIDGE_SRC, "_with_vault_lock"))


# ── 46–49: D29 doc contract, D34 breaker, D37 gitignore, D38/D39 readiness ───

class TestBreakerAndReadiness(_FailoverFixture):
    def test_46_d29_empty_answer_is_empty_status_documented(self):
        self.assertEqual(bridge.detect_response_status(None), "EMPTY")
        readme = (ROOT / "README_COOLDOWN_VAULT.md").read_text(encoding="utf-8")
        self.assertIn("⏳ بيفكر", readme)
        self.assertIn("account_log.jsonl", readme)
        self.assertIn("-l 0", readme)
        self.assertIn(LOCK_NAME, readme)
        self.assertNotIn("لا password/cookies", readme)

    def test_47_network_down_breaker_after_two_consecutive_unreadable(self):
        # three accounts, each pre-flight returns BALANCE_UNREADABLE → first two move (D26), third never tried
        sends, (pub_url, status, acc, _e, _t) = self._run(["BALANCE_UNREADABLE", "BALANCE_UNREADABLE", "BALANCE_UNREADABLE"])
        self.assertEqual(status, "NETWORK_DOWN")
        self.assertIsNone(acc)
        self.assertEqual(sends.call_count, 2, "breaker trips after N=2 consecutive unreadable balances")
        self.assertIsNotNone(self.primary_rec(EMAIL_C), "third account untouched")
        self.assertIn("NETWORK_DOWN", bridge.NON_ACTIONABLE_PROGRESS_STATUSES)
        self.assertIn("NETWORK_DOWN", _extract_func(BRIDGE_SRC, "build_failure_notice") if "def build_failure_notice(" in BRIDGE_SRC else BRIDGE_SRC)

    def test_48_gitignore_covers_secret_bearing_artifacts(self):
        names = ["account_log.jsonl", "account_log.jsonl.tmp", LOCK_NAME,
                 "accounts_genspark.json.cooldown_move.bak", "accounts_genspark.json.tmp123",
                 "accounts_success.json.20261101_120000.bak"]
        out = subprocess.run(["git", "check-ignore"] + names, cwd=str(ROOT), capture_output=True, text=True)
        ignored = set(out.stdout.split())
        self.assertEqual(ignored, set(names), f"D37: not ignored: {set(names) - ignored}")

    def test_49_revival_limit_zero_means_all_and_main_exits_nonzero_on_error(self):
        mgr = _load_manager_module()
        rv = _extract_func(MANAGER_SRC.replace("\n    def run_revival", "\ndef run_revival"), "run_revival")
        self.assertNotIn("[:limit]", rv.split("limit <= 0")[0] if "limit <= 0" in rv else rv,
                         "D38: limit<=0 must mean 'all' before slicing")
        src_main = _extract_func(MANAGER_SRC, "main")
        self.assertIn("sys.exit(1)", src_main, "D39: non-zero exit on error")
        self.assertIn('"error"', src_main)
        self.assertIn("ACCOUNT_LOG_RETENTION_DAYS", MANAGER_SRC)
        self.assertIn("_trim_account_log", rv, "D32: trimming is invoked from run_revival start")
        # 05.02 stays pure LF, 01.33 pure CRLF
        raw = BRIDGE.read_bytes()
        self.assertEqual(raw.count(b"\n") - raw.count(b"\r\n"), 0)
        self.assertEqual(MANAGER.read_bytes().count(b"\r"), 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
