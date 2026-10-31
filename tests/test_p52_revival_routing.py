"""
P52 — MAINT-3-B (05.02 surgical fix of gap R1): ``run_revival`` routing.

Spec: RESUME.md §3.8.3 (S1–S7) + §3.8.8 (tests 27–34). Decisions D21/D23/D24.

What is verified (offline, no network, no repo file touched):
  * HEALTHY & days <= 3  -> primary + success (legacy behaviour preserved)
  * DEAD                 -> accounts_failed.json, removed from the vault
  * STALE                -> accounts_delayed_gifts_credits.json, removed from the vault
  * AUTH_FAILED/UNKNOWN  -> stays in the vault (undecided is never moved)
  * dry_run=True         -> zero writes
  * empty destination    -> its file and .bak are NOT created (no work on nothing)
  * return keys          -> legacy keys kept + moved_to_failed / moved_to_delayed
  * constitutional guard -> only the vault is read as a *scan input*; failed/delayed
                            files are opened for merge-append only (never scanned)
  * file hygiene         -> 05.02 stays pure LF; ``_merge_by_email`` lives next to
                            ``run_revival`` (D24) and is the single merge primitive

Loading follows the P49 pattern: ``spec_from_file_location`` with the missing
``genspark_master_account_manager`` stubbed in ``sys.modules``.
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import socket
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANAGER_FILE = ROOT / "05.02_genspark_delayed_gifts_manager.py"


class _NoNetworkSocket:
    def __init__(self, *a, **k):
        raise RuntimeError("network access is forbidden inside P52")


def _load_manager_module():
    stub = types.ModuleType("genspark_master_account_manager")
    for name in ("do_b2c_login", "get_session", "check_account_balance"):
        def _boom(*_a, _n=name, **_k):  # pragma: no cover
            raise RuntimeError(f"{_n} stub must never be reached in P52")
        setattr(stub, name, _boom)
    sys.modules.setdefault("genspark_master_account_manager", stub)
    spec = importlib.util.spec_from_file_location("p52_manager_under_test", MANAGER_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MOD = _load_manager_module()


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setattr(socket, "socket", _NoNetworkSocket)
    monkeypatch.setattr(MOD.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(MOD.random, "uniform", lambda a, b: 0.0)
    monkeypatch.setattr(MOD, "IS_RUNNING", True)
    yield


# ─────────────────────────────────────────────────────────────────────────────
# Harness
# ─────────────────────────────────────────────────────────────────────────────
def _acc(email, **extra):
    d = {"email": email, "password": "x", "status": "quarantined",
         "quarantine_info": {"days_without_gift": 20}}
    d.update(extra)
    return d


def _write(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _emails(lst):
    return sorted(a["email"] for a in (lst or []))


class Harness:
    """Vault-mode manager (``-q accounts_cooldown.json``) inside tmp_path."""

    def __init__(self, tmp_path: Path, monkeypatch, vault_accounts, verdicts):
        self.dir = tmp_path
        self.primary = tmp_path / "accounts_genspark.json"
        self.success = tmp_path / "accounts_success.json"
        self.vault = tmp_path / "accounts_cooldown.json"
        self.failed = tmp_path / MOD.Config.FAILED_FILE
        self.dead = tmp_path / MOD.Config.DEAD_FILE
        self.delayed = tmp_path / MOD.Config.QUARANTINE_FILE
        _write(self.primary, [_acc("keep.primary@x.com", status="active")])
        _write(self.success, [])
        _write(self.vault, vault_accounts)
        # C2: with -q <vault> the manager has no delayed-gifts path -> it must
        # resolve Config.QUARANTINE_FILE; we pin resolution into tmp_path.
        monkeypatch.setattr(MOD, "resolve_file_path", lambda name: tmp_path / name)
        self.mgr = MOD.MasterDelayedGiftsManager(
            primary_path=self.primary, success_path=self.success,
            quarantine_path=self.vault, failed_path=self.failed, dead_path=self.dead,
            min_delay=0.0, max_delay=0.0,
        )
        self.scanned = []
        verdicts = dict(verdicts)

        def fake_check(account):
            self.scanned.append(account["email"])
            status, days = verdicts[account["email"]]
            return status, days, "2026-10-30T00:00:00", 1000, None

        monkeypatch.setattr(self.mgr, "check_account_status", fake_check)

    def baks(self, path: Path):
        return list(self.dir.glob(f"{path.name}.*.bak"))


# ─────────────────────────────────────────────────────────────────────────────
# Tests 27–34 (+ guards)
# ─────────────────────────────────────────────────────────────────────────────
def test_27_dead_routed_to_failed_and_removed_from_vault(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch, [_acc("dead@x.com")], {"dead@x.com": ("DEAD", None)})
    res = h.mgr.run_revival()
    assert res["moved_to_failed"] == 1
    assert _emails(_read(h.failed)) == ["dead@x.com"]
    assert _emails(_read(h.vault)) == []
    assert _read(h.delayed) is None  # STALE destination untouched when empty


def test_28_stale_routed_to_delayed_gifts_and_removed_from_vault(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch, [_acc("stale@x.com")], {"stale@x.com": ("STALE", 30)})
    res = h.mgr.run_revival()
    assert res["moved_to_delayed"] == 1
    assert _emails(_read(h.delayed)) == ["stale@x.com"]
    assert _emails(_read(h.vault)) == []
    assert _read(h.failed) is None


def test_29_undecided_stays_in_vault_and_is_counted(tmp_path, monkeypatch):
    vault = [_acc("auth@x.com"), _acc("unknown@x.com"), _acc("healthy_old@x.com")]
    verdicts = {"auth@x.com": ("AUTH_FAILED", None), "unknown@x.com": ("UNKNOWN", None),
                "healthy_old@x.com": ("HEALTHY", 9)}  # HEALTHY but > 3 days -> stays
    h = Harness(tmp_path, monkeypatch, vault, verdicts)
    res = h.mgr.run_revival()
    assert res["still_stale"] == 3
    assert res["revived"] == 0 and res["moved_to_failed"] == 0 and res["moved_to_delayed"] == 0
    # nothing to write -> no files touched at all
    assert _emails(_read(h.vault)) == _emails(vault)
    assert h.baks(h.vault) == [] and _read(h.failed) is None and _read(h.delayed) is None


def test_30_healthy_recent_revived_to_primary_and_success_legacy_preserved(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch, [_acc("ok@x.com")], {"ok@x.com": ("HEALTHY", 1)})
    res = h.mgr.run_revival()
    assert res["revived"] == 1
    prim = _read(h.primary)
    assert _emails(prim) == ["keep.primary@x.com", "ok@x.com"]
    revived = next(a for a in prim if a["email"] == "ok@x.com")
    assert revived["status"] == "active" and "quarantine_info" not in revived
    assert _emails(_read(h.success)) == ["ok@x.com"]
    assert _emails(_read(h.vault)) == []


def test_31_mixed_batch_full_routing_in_one_pass(tmp_path, monkeypatch):
    vault = [_acc("ok@x.com"), _acc("dead@x.com"), _acc("stale@x.com"), _acc("auth@x.com")]
    verdicts = {"ok@x.com": ("HEALTHY", 2), "dead@x.com": ("DEAD", None),
                "stale@x.com": ("STALE", 40), "auth@x.com": ("AUTH_FAILED", None)}
    h = Harness(tmp_path, monkeypatch, vault, verdicts)
    res = h.mgr.run_revival()
    assert (res["revived"], res["moved_to_failed"], res["moved_to_delayed"], res["still_stale"]) == (1, 1, 1, 1)
    assert _emails(_read(h.vault)) == ["auth@x.com"]
    assert "dead@x.com" in _emails(_read(h.failed))
    assert "stale@x.com" in _emails(_read(h.delayed))
    assert "ok@x.com" in _emails(_read(h.primary))


def test_32_dry_run_writes_nothing(tmp_path, monkeypatch):
    vault = [_acc("ok@x.com"), _acc("dead@x.com"), _acc("stale@x.com")]
    verdicts = {"ok@x.com": ("HEALTHY", 1), "dead@x.com": ("DEAD", None), "stale@x.com": ("STALE", 40)}
    h = Harness(tmp_path, monkeypatch, vault, verdicts)
    before = {p: _read(p) for p in (h.primary, h.success, h.vault)}
    res = h.mgr.run_revival(dry_run=True)
    assert (res["revived"], res["moved_to_failed"], res["moved_to_delayed"]) == (1, 1, 1)
    assert {p: _read(p) for p in (h.primary, h.success, h.vault)} == before
    assert _read(h.failed) is None and _read(h.delayed) is None
    assert not list(tmp_path.glob("*.bak"))


def test_33_merge_is_idempotent_by_email_and_preserves_existing_destination(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch, [_acc("dead@x.com")], {"dead@x.com": ("DEAD", None)})
    _write(h.failed, [{"email": "old.failed@x.com"}, {"email": "DEAD@x.com", "note": "older copy"}])
    h.mgr.run_revival()
    failed = _read(h.failed)
    assert _emails(failed) == ["dead@x.com", "old.failed@x.com"]  # case-insensitive dedupe, no duplicate
    assert len(h.baks(h.failed)) == 1  # .bak taken before overwrite


def test_34_return_keys_legacy_plus_new(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch, [_acc("ok@x.com")], {"ok@x.com": ("HEALTHY", 1)})
    res = h.mgr.run_revival()
    assert set(res) == {"revived", "still_stale", "moved_to_failed", "moved_to_delayed"}
    # empty vault keeps the legacy early-return contract
    _write(h.vault, [])
    assert h.mgr.run_revival() == {"revived": 0}


def test_35_constitutional_guard_only_vault_is_scanned(tmp_path, monkeypatch):
    """failed/delayed are write destinations only: their accounts are never status-checked."""
    h = Harness(tmp_path, monkeypatch, [_acc("dead@x.com")], {"dead@x.com": ("DEAD", None)})
    _write(h.failed, [{"email": "never.scan.me@x.com"}])
    _write(h.delayed, [{"email": "nor.me@x.com"}])
    h.mgr.run_revival()
    assert h.scanned == ["dead@x.com"]
    assert "never.scan.me@x.com" in _emails(_read(h.failed))
    assert "nor.me@x.com" in _emails(_read(h.delayed))


def test_36_file_hygiene_lf_only_and_helper_adjacent_to_run_revival():
    raw = MANAGER_FILE.read_bytes()
    assert b"\r\n" not in raw, "05.02 must stay pure LF"
    assert callable(getattr(MOD.MasterDelayedGiftsManager, "_merge_by_email", None)), "D24 helper missing"
    src = MANAGER_FILE.read_text(encoding="utf-8")
    assert src.index("def _merge_by_email") < src.index("def run_revival"), "helper must sit right before run_revival"
    # D24: helper is the single merge primitive -> no ad-hoc dict-merge left in run_revival
    body = inspect.getsource(MOD.MasterDelayedGiftsManager.run_revival)
    assert "p_map" not in body and "s_map" not in body
    assert body.count("self._merge_by_email(") == 4  # primary, success, failed, delayed
