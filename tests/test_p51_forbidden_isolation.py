"""P51 — MAINT-3-B-2: FORBIDDEN / EMPTY_STREAM_FAILED Cut&Move into ``accounts_cooldown.json`` (01.33).

Owner-approved contract (RESUME.md §3.4/§3.6/§3.7/§3.8 + decisions D1–D25 "كما أوصيت", 2026-10-31):
  * p03 (after ``mark_account_cooldown``): ``COOLDOWN_VAULT_FILENAME``, ``ACCOUNT_LOG_FILENAME``,
    ``ACCOUNT_LOG_RETENTION_DAYS=30``, ``ACCOUNT_LOG_MAX_ENTRIES=5000``, ``ACCOUNT_LOG_LOCK``,
    ``COOLDOWN_VAULT_REASONS=("FORBIDDEN","EMPTY_STREAM_FAILED")`` (empty tuple = disabled),
    ``COOLDOWN_VAULT_HOURS={"FORBIDDEN":24.0,"EMPTY_STREAM_FAILED":1.0}`` (D1 / قرار 3),
    ``FORBIDDEN_MOVE_AFTER_N=2`` + ``FORBIDDEN_HITS_WINDOW_HOURS=24`` (D19),
    ``append_account_log``, ``register_forbidden_hit``, ``move_account_to_cooldown_vault``.
  * Vault record = flat list entry loadable by 05.02 ``load_accounts``; our metadata lives inside
    ``quarantine_info`` (A3 simplification) with reason ``cooldown_<reason>`` — never
    ``stale_daily_gift`` / ``days_without_gift`` (G7), never ``quarantined``/``status=suspended`` (G14);
    ``password``/``cookies`` are kept (D2).
  * Copy-then-cut: vault written first; primary cut after a rotating ``.cooldown_move.bak`` copy;
    a failing cut leaves the account in both files and logs ``move_partial`` (recoverable).
  * Failover (p06): FORBIDDEN → ``register_forbidden_hit``; < threshold → 5-minute cooldown only;
    >= threshold → move; move failure → 5-minute cooldown. Never ``status=active``/``last_success_at``
    for a 403 account (fix of finding T5). EMPTY_STREAM_FAILED → move (1h) with
    ``mark_account_cooldown`` as the fallback only when the move fails (D10).
  * ``account_log.json``: first entry is a permanent ``schema`` record; trimming 30d + cap 5000 (D7);
    never ``password``/``cookies``.
  * Untouched: ``P44_STRUCTURED_STATUSES``, ``is_account_ready``, P48, 05.02, 01.03, verifier; 01.33 stays CRLF.

Everything is offline: real temp JSON files, the real ``FILE_LOCK``, no network.
"""

from __future__ import annotations

import contextlib
import importlib.util
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
MANAGER = ROOT / "05.02_genspark_delayed_gifts_manager.py"
BRIDGE_SRC = BRIDGE.read_text(encoding="utf-8")
PID_A = "11111111-aaaa-4bbb-8ccc-000000000001"
PID_B = "22222222-aaaa-4bbb-8ccc-000000000002"
EMAIL_A = "p51.alpha@test.invalid"
EMAIL_B = "p51.beta@test.invalid"


def _load_bridge_module():
    spec = importlib.util.spec_from_file_location("bridge_p51", str(BRIDGE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p51"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_manager_module():
    stub = types.ModuleType("genspark_master_account_manager")
    for name in ("do_b2c_login", "get_session", "check_account_balance"):
        setattr(stub, name, lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("stub")))
    sys.modules.setdefault("genspark_master_account_manager", stub)
    spec = importlib.util.spec_from_file_location("manager_p51", str(MANAGER))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["manager_p51"] = mod
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


class _VaultFixture(unittest.TestCase):
    """Real temp directory with accounts_genspark.json; vault + log are created by the code under test."""

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = pathlib.Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.primary = self.tmp / "accounts_genspark.json"
        self.vault = self.tmp / "accounts_cooldown.json"
        self.log = self.tmp / "account_log.json"
        self.accounts = [
            {"email": EMAIL_A, "password": "secret-a", "cookies": {"session_id": "x"}, "last_refresh": 1.0,
             "status": "active", "active": True},
            {"email": EMAIL_B, "password": "secret-b", "cookies": {"session_id": "y"}, "last_refresh": 1.0,
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

    def primary_emails(self):
        return [a.get("email") for a in self.read(self.primary)]

    def vault_record(self, email=EMAIL_A):
        data = self.read(self.vault) or []
        return next((a for a in data if a.get("email") == email), None)

    def log_events(self):
        return [e for e in (self.read(self.log) or []) if isinstance(e, dict)]

    def log_messages(self):
        return [str(c.args[1]) for c in self.logs.call_args_list if len(c.args) > 1]


# ── 1–7: the move primitive ──────────────────────────────────────────────────

class TestMovePrimitive(_VaultFixture):
    def test_01_move_copies_then_cuts_and_logs(self):
        ok = bridge.move_account_to_cooldown_vault(EMAIL_A, "FORBIDDEN", json_path=str(self.primary),
                                                   meta={"http_status": 403, "project_key": "pk", "pid": PID_A})
        self.assertTrue(ok)
        self.assertEqual(self.primary_emails(), [EMAIL_B])
        rec = self.vault_record()
        self.assertIsNotNone(rec)
        qi = rec["quarantine_info"]
        self.assertEqual(qi["reason"], "cooldown_forbidden")
        self.assertEqual(qi["http_status"], 403)
        self.assertEqual(qi["pid"], PID_A)
        self.assertEqual(qi["source"], "accounts_genspark.json")
        self.assertAlmostEqual(qi["cooldown_until_ts"] - qi["moved_at_ts"], 24 * 3600, delta=1)  # D1
        self.assertIsInstance(self.read(self.vault), list)  # flat list for 05.02
        events = self.log_events()
        self.assertEqual(events[0]["event"], "schema")
        moved = [e for e in events if e.get("event") == "exit_to_cooldown"]
        self.assertEqual(len(moved), 1)
        self.assertEqual(moved[0]["email"], EMAIL_A)
        self.assertEqual(moved[0]["target_file"], "accounts_cooldown.json")
        self.assertTrue((self.tmp / "accounts_genspark.json.cooldown_move.bak").exists())

    def test_02_record_keeps_credentials_and_is_not_suspended_or_stale(self):
        bridge.move_account_to_cooldown_vault(EMAIL_A, "FORBIDDEN", json_path=str(self.primary))
        rec = self.vault_record()
        self.assertEqual(rec["password"], "secret-a")              # D2
        self.assertEqual(rec["cookies"], {"session_id": "x"})      # D2
        self.assertIsNot(rec.get("quarantined"), True)             # G14
        self.assertNotEqual(str(rec.get("status", "")).lower(), "suspended")
        self.assertNotIn("days_without_gift", rec["quarantine_info"])  # G7
        self.assertNotEqual(bridge.classify_gift_freshness(rec)[0], "STALE")

    def test_03_idempotent_duplicate_updates_metadata_only(self):
        self.assertTrue(bridge.move_account_to_cooldown_vault(EMAIL_A, "FORBIDDEN", json_path=str(self.primary)))
        # put a fresh copy back in primary and move again → single vault record, duplicate logged
        self.write_primary([dict(self.accounts[0]), dict(self.accounts[1])])
        self.assertTrue(bridge.move_account_to_cooldown_vault(EMAIL_A, "EMPTY_STREAM_FAILED", json_path=str(self.primary)))
        vault = self.read(self.vault)
        self.assertEqual([a["email"] for a in vault], [EMAIL_A])
        self.assertEqual(vault[0]["quarantine_info"]["reason"], "cooldown_empty_stream_failed")
        self.assertEqual(self.primary_emails(), [EMAIL_B])
        self.assertTrue(any(e.get("event") == "duplicate_detected" for e in self.log_events()))

    def test_04_cut_failure_keeps_account_in_both_files(self):
        with mock.patch.object(bridge.shutil, "copy2", side_effect=OSError("disk full")):
            ok = bridge.move_account_to_cooldown_vault(EMAIL_A, "FORBIDDEN", json_path=str(self.primary))
        self.assertFalse(ok)
        self.assertIn(EMAIL_A, self.primary_emails())
        self.assertIsNotNone(self.vault_record())
        self.assertTrue(any(e.get("event") == "move_partial" for e in self.log_events()))

    def test_05_missing_accounts_file_returns_false_without_side_effects(self):
        ok = bridge.move_account_to_cooldown_vault(EMAIL_A, "FORBIDDEN", json_path=str(self.tmp / "nope.json"))
        self.assertFalse(ok)
        self.assertFalse(self.vault.exists())
        self.assertFalse(self.log.exists())

    def test_06_unknown_email_returns_false(self):
        ok = bridge.move_account_to_cooldown_vault("ghost@test.invalid", "FORBIDDEN", json_path=str(self.primary))
        self.assertFalse(ok)
        self.assertFalse(self.vault.exists())
        self.assertEqual(self.primary_emails(), [EMAIL_A, EMAIL_B])

    def test_07_vault_loadable_by_0502_load_accounts(self):
        bridge.move_account_to_cooldown_vault(EMAIL_A, "FORBIDDEN", json_path=str(self.primary))
        manager = _load_manager_module()
        loaded = manager.load_accounts(self.vault)
        self.assertEqual([a["email"] for a in loaded], [EMAIL_A])
        self.assertIsInstance(loaded[0]["quarantine_info"], dict)


# ── 8–10: account_log + forbidden hits ───────────────────────────────────────

class TestAccountLogAndHits(_VaultFixture):
    def test_08_log_trims_30d_and_caps_but_keeps_schema(self):
        now = time.time()
        old = [{"ts": now - 40 * 86400, "event": "exit_to_cooldown", "email": "old@test.invalid"}]
        recent = [{"ts": now - 60 - i, "event": "exit_to_cooldown", "email": f"r{i}@test.invalid"}
                  for i in range(bridge.ACCOUNT_LOG_MAX_ENTRIES + 20)]
        self.log.write_text(json.dumps([dict(bridge.ACCOUNT_LOG_SCHEMA_ENTRY)] + old + recent), encoding="utf-8")
        self.assertTrue(bridge.append_account_log("return_to_primary", EMAIL_A, base_dir=self.tmp))
        events = self.log_events()
        self.assertEqual(events[0]["event"], "schema")
        self.assertLessEqual(len(events), bridge.ACCOUNT_LOG_MAX_ENTRIES + 1)
        self.assertTrue(all(e["ts"] >= now - bridge.ACCOUNT_LOG_RETENTION_DAYS * 86400 for e in events[1:]))
        self.assertEqual(events[-1]["event"], "return_to_primary")

    def test_09_log_never_stores_secrets_and_tolerates_corruption(self):
        self.log.write_text("{not json", encoding="utf-8")
        ok = bridge.append_account_log("exit_to_cooldown", EMAIL_A, reason="FORBIDDEN",
                                       meta={"password": "p", "cookies": {"a": 1}, "http_status": 403}, base_dir=self.tmp)
        self.assertTrue(ok)
        events = self.log_events()
        for e in events:  # keys only — the schema note may *mention* the words, data must never carry them
            self.assertFalse({"password", "cookies"} & set(e.keys()), f"secret key leaked into log entry: {e}")
        self.assertEqual(events[0]["event"], "schema")
        self.assertEqual(events[-1]["http_status"], 403)

    def test_10_register_forbidden_hit_counts_distinct_pids_within_window(self):
        now = time.time()
        self.assertEqual(bridge.register_forbidden_hit(EMAIL_A, PID_A, json_path=str(self.primary), now=now), 1)
        self.assertEqual(bridge.register_forbidden_hit(EMAIL_A, PID_A, json_path=str(self.primary), now=now + 5), 1)
        self.assertEqual(bridge.register_forbidden_hit(EMAIL_A, PID_B, json_path=str(self.primary), now=now + 10), 2)
        # outside the 24h window the old hits expire
        far = now + bridge.FORBIDDEN_HITS_WINDOW_HOURS * 3600 + 60
        self.assertEqual(bridge.register_forbidden_hit(EMAIL_A, PID_B, json_path=str(self.primary), now=far), 1)
        acc = next(a for a in self.read(self.primary) if a["email"] == EMAIL_A)
        self.assertEqual(len(acc["forbidden_hits"]), 1)
        self.assertEqual(bridge.register_forbidden_hit("ghost@test.invalid", PID_A, json_path=str(self.primary)), 0)


# ── 11–16: failover integration (real files, real FILE_LOCK) ─────────────────

class TestFailoverIsolation(_VaultFixture):
    def setUp(self):
        super().setUp()
        self.cfg = bridge.BridgeConfig()
        self.cfg.max_account_attempts = 2
        self.cfg.selection_project_key = "pk-51"
        self.cooldown = self.patch("mark_account_cooldown", wraps=bridge.mark_account_cooldown)
        self.patch("get_account_fingerprint", return_value={"browser": "chrome120", "user_agent": "t"})
        self.patch("apply_project_runtime_binding")
        self.patch("notify_account_selection_observer")
        self.patch("claim_eligible_account_for_owner",
                   side_effect=lambda accs, tried, *a, **k: next(
                       ((a_, accs, "claimed") for a_ in accs if a_["email"] not in tried), (None, accs, "no-eligible")))
        self.patch("release_account_selection")
        self.stack.enter_context(mock.patch.object(bridge.time, "sleep"))

    def _run(self, first_status, pid=PID_A):
        url = bridge.build_genspark_viewer_url(pid)
        sends = self.patch("send_message_and_make_public", side_effect=[
            (url, first_status, None, "", None),
            (url, "COMPLETED", None, "ok", None),
        ])
        result = bridge.send_message_with_auto_account_failover(
            None, "build it", bridge_cfg=self.cfg, json_path=str(self.primary))
        return sends, result

    def _primary_a(self):
        return next((a for a in self.read(self.primary) if a["email"] == EMAIL_A), None)

    def test_11_first_forbidden_cools_5_minutes_only(self):
        sends, (pub_url, status, acc, _e, _t) = self._run("FORBIDDEN")
        self.assertEqual(sends.call_count, 2)
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(acc["email"], EMAIL_B)
        a = self._primary_a()
        self.assertIsNotNone(a, "below threshold the account stays in primary")
        self.assertAlmostEqual(a["cooldown_until"], time.time() + 300, delta=30)
        self.assertEqual(len(a["forbidden_hits"]), 1)
        self.assertNotIn("last_success_at", a)                      # T5 fixed
        self.assertIsNone(self.vault_record())

    def test_12_second_forbidden_on_other_project_moves_to_vault(self):
        self.accounts[0]["forbidden_hits"] = [{"ts": time.time() - 120, "pid": PID_B}]
        self.write_primary(self.accounts)
        sends, (pub_url, status, acc, _e, _t) = self._run("FORBIDDEN", pid=PID_A)
        self.assertEqual(sends.call_count, 2)
        self.assertEqual(acc["email"], EMAIL_B)
        self.assertIsNone(self._primary_a(), "403 account must be cut from primary")
        rec = self.vault_record()
        self.assertEqual(rec["quarantine_info"]["reason"], "cooldown_forbidden")
        self.assertEqual(rec["quarantine_info"]["project_key"], "pk-51")
        self.assertEqual(rec["quarantine_info"]["pid"], PID_A)
        self.assertNotIn("last_success_at", rec)                    # T5 fixed
        self.assertTrue(any(e.get("event") == "exit_to_cooldown" and e.get("email") == EMAIL_A
                            for e in self.log_events()))
        # EMAIL_B succeeded normally
        b = next(a for a in self.read(self.primary) if a["email"] == EMAIL_B)
        self.assertIn("last_success_at", b)

    def test_13_forbidden_move_failure_falls_back_to_5_minutes(self):
        self.accounts[0]["forbidden_hits"] = [{"ts": time.time() - 120, "pid": PID_B}]
        self.write_primary(self.accounts)
        self.patch("move_account_to_cooldown_vault", return_value=False)
        sends, (_u, status, acc, _e, _t) = self._run("FORBIDDEN")
        self.assertEqual(acc["email"], EMAIL_B)
        a = self._primary_a()
        self.assertAlmostEqual(a["cooldown_until"], time.time() + 300, delta=30)
        self.assertNotIn("last_success_at", a)

    def test_14_reasons_disabled_restores_legacy_t5_baseline(self):
        self.accounts[0]["forbidden_hits"] = [{"ts": time.time() - 120, "pid": PID_B}]
        self.write_primary(self.accounts)
        with mock.patch.object(bridge, "COOLDOWN_VAULT_REASONS", ()):
            sends, (_u, status, acc, _e, _t) = self._run("FORBIDDEN")
        # legacy: pub_url non-empty → first account marked successful (documented T5 baseline)
        self.assertEqual(sends.call_count, 1)
        self.assertEqual(acc["email"], EMAIL_A)
        self.assertIn("last_success_at", self._primary_a())
        self.assertIsNone(self.vault_record())

    def test_15_empty_stream_moves_1h_without_mark_cooldown(self):
        sends, (_u, status, acc, _e, _t) = self._run("EMPTY_STREAM_FAILED")
        self.assertEqual(sends.call_count, 2)
        self.assertEqual(acc["email"], EMAIL_B)
        self.assertIsNone(self._primary_a())
        rec = self.vault_record()
        qi = rec["quarantine_info"]
        self.assertEqual(qi["reason"], "cooldown_empty_stream_failed")
        self.assertIsNone(qi["http_status"])
        self.assertAlmostEqual(qi["cooldown_until_ts"] - qi["moved_at_ts"], 3600, delta=1)
        self.assertFalse(self.cooldown.called, "no in-place cooldown when the move succeeded")

    def test_16_empty_stream_fallback_marks_1h_cooldown_when_move_fails(self):
        self.patch("move_account_to_cooldown_vault", return_value=False)
        sends, (_u, status, acc, _e, _t) = self._run("EMPTY_STREAM_FAILED")
        self.assertEqual(acc["email"], EMAIL_B)
        self.cooldown.assert_any_call(EMAIL_A, cooldown_hours=bridge.DEC07_EMPTY_COOLDOWN_HOURS,
                                      json_path=str(self.primary))
        a = self._primary_a()
        self.assertEqual(a["status"], "cooldown")


# ── 17–18: locking + source contracts ────────────────────────────────────────

class TestLocksAndContracts(_VaultFixture):
    def test_17_no_deadlock_with_real_file_lock(self):
        done = threading.Event()
        result = {}

        def worker():
            result["ok"] = bridge.move_account_to_cooldown_vault(EMAIL_A, "FORBIDDEN", json_path=str(self.primary))
            done.set()

        with bridge.FILE_LOCK:
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            time.sleep(0.2)
            self.assertFalse(done.is_set(), "move must wait for FILE_LOCK")
        self.assertTrue(done.wait(5), "move must complete once FILE_LOCK is released")
        self.assertTrue(result["ok"])

    def test_18_source_contracts(self):
        body = _extract_func(BRIDGE_SRC, "send_message_with_auto_account_failover")
        self.assertEqual(body.count('status == "FORBIDDEN"'), 1, "exactly one FORBIDDEN branch in the failover")
        self.assertLess(body.index('status == "FORBIDDEN"'), body.index('if pub_url or status == "COMPLETED"'))
        self.assertIn("register_forbidden_hit", body)
        self.assertIn("FORBIDDEN_MOVE_AFTER_N", body)
        self.assertEqual(body.count("move_account_to_cooldown_vault("), 2, "one call per reason, one function")
        self.assertEqual(bridge.P44_STRUCTURED_STATUSES, ("CREDIT_EXHAUSTED", "DATA_RETENTION", "SESSION_EXPIRED", "FORBIDDEN"))
        for name in ("is_account_ready", "classify_gift_freshness", "get_eligible_accounts", "detect_response_status"):
            self.assertNotIn("MAINT3", _extract_func(BRIDGE_SRC, name))
            self.assertNotIn("COOLDOWN_VAULT", _extract_func(BRIDGE_SRC, name))
        move_body = _extract_func(BRIDGE_SRC, "move_account_to_cooldown_vault")
        self.assertNotIn("update_account_data(", move_body, "I1: manual read/modify/write under FILE_LOCK")
        self.assertNotIn("read_accounts_safe(", move_body)
        self.assertNotIn("ACCOUNT_LOG_LOCK", move_body.split("append_account_log")[0], "log lock never nested in FILE_LOCK")
        self.assertEqual(bridge.COOLDOWN_VAULT_REASONS, ("FORBIDDEN", "EMPTY_STREAM_FAILED"))
        self.assertEqual(bridge.COOLDOWN_VAULT_HOURS, {"FORBIDDEN": 24.0, "EMPTY_STREAM_FAILED": 1.0})
        self.assertEqual(bridge.FORBIDDEN_MOVE_AFTER_N, 2)
        raw = BRIDGE.read_bytes()
        self.assertEqual(raw.count(b"\n") - raw.count(b"\r\n"), 0, "01.33 must stay pure CRLF")
        m_raw = MANAGER.read_bytes()
        self.assertEqual(m_raw.count(b"\r"), 0, "05.02 must stay pure LF")
        self.assertNotIn("MAINT3", MANAGER.read_text(encoding="utf-8"), "05.02 untouched by MAINT-3-B-2")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
