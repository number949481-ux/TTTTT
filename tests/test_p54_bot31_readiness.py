"""
P54 — MAINT-4-C (05.02 graft of 05.03 Bot-31 activation logic): D40 / D41 / D42 / D43.

Spec: RESUME.md §3.12 + §4 D40–D44 (owner GO card 2026-11-01, Q-1..Q-5 resolved).

What is verified (offline, no network, no repo file touched):
  * helper ``_activate_for_bot31(acc, bal)`` lives beside ``_merge_by_email`` (A5, DRY)
      - last_updated=ISO, quarantine_info/quarantined popped (both branches)
      - bal >= 100  -> status="active", active=True, cooldown_until=0 + cooldown_released_at=ISO (Q-1 / owner A)
      - bal <  100  -> [MAINT-4-D] status="cooldown", active=False, cooldown_until=now+29h (docs 19/20;
                       mirrors 01.33 mark_account_cooldown 1286-1297), no cooldown_released_at
  * D40  run_quarantine HEALTHY block calls the helper (primary + success carry the flags)
  * D41  run_revival HEALTHY<=3d calls the helper (revived record carries the flags)
  * cross-program contract: a vault record exactly as 01.33 writes it
    (status="cooldown", active=False, quarantine_info{reason:"cooldown_*"})
    -> run_revival -> 01.33 ``is_account_ready`` returns True
  * D42  sort by balance desc still holds after the graft
  * D43  SRE invariants untouched: ``_with_vault_lock`` / ``_log_move`` / ``_trim_account_log``
         / ``COOLDOWN_VAULT_LOCK_FILENAME`` present; 05.02 pure LF; no ``.bak`` tracked
  * 05.03 docstring drift (``<=``/``>``) is NOT imported: code keeps ``>= threshold_days``

Loading follows the P52 pattern (``spec_from_file_location`` + stubbed
``genspark_master_account_manager``). 01.33 is loaded read-only via the P48 pattern.
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import re
import socket
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANAGER_FILE = ROOT / "05.02_genspark_delayed_gifts_manager.py"
BRIDGE_FILE = ROOT / "01.33_telegram_gen_bridge.py"
MANAGER_SRC = MANAGER_FILE.read_text(encoding="utf-8")


class _NoNetworkSocket:
    def __init__(self, *a, **k):
        raise RuntimeError("network access is forbidden inside P54")


def _load_manager_module():
    stub = types.ModuleType("genspark_master_account_manager")
    for name in ("do_b2c_login", "get_session", "check_account_balance"):
        def _boom(*_a, _n=name, **_k):  # pragma: no cover
            raise RuntimeError(f"{_n} stub must never be reached in P54")
        setattr(stub, name, _boom)
    sys.modules.setdefault("genspark_master_account_manager", stub)
    spec = importlib.util.spec_from_file_location("p54_manager_under_test", MANAGER_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MOD = _load_manager_module()


@pytest.fixture(scope="module")
def bridge():
    """01.33 loaded read-only (P48 pattern) — only ``is_account_ready`` is used."""
    spec = importlib.util.spec_from_file_location("bridge_p54", str(BRIDGE_FILE))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setattr(socket, "socket", _NoNetworkSocket)
    monkeypatch.setattr(MOD.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(MOD.random, "uniform", lambda a, b: 0.0)
    monkeypatch.setattr(MOD, "IS_RUNNING", True)
    monkeypatch.setattr(MOD.Config, "AUTO_BACKUP", False)
    yield


ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def _write(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _by_email(lst, email):
    return next(a for a in (lst or []) if a["email"].lower() == email.lower())


def _vault_record_as_written_by_0133(email="cool@x.com", **extra):
    """Mirror of 01.33 ``move_account_to_cooldown_vault`` record (1431–1442)."""
    d = {
        "email": email, "password": "pw", "cookies": {"session_id": "abc"},
        "status": "cooldown", "active": False, "balance": 0,
        "cooldown_until": 0,
        "quarantine_info": {
            "reason": "cooldown_forbidden", "http_status": 403,
            "moved_at": "2026-11-01T00:00:00", "moved_at_ts": 1.0,
            "source": "accounts_genspark.json", "project_key": "", "pid": "1",
        },
    }
    d.update(extra)
    return d


def _mgr(tmp_path, monkeypatch, vault_path_name="accounts_cooldown.json"):
    primary = tmp_path / "accounts_genspark.json"
    success = tmp_path / "accounts_success.json"
    vault = tmp_path / vault_path_name
    failed = tmp_path / MOD.Config.FAILED_FILE
    dead = tmp_path / MOD.Config.DEAD_FILE
    monkeypatch.setattr(MOD, "resolve_file_path", lambda name: tmp_path / name)
    mgr = MOD.MasterDelayedGiftsManager(
        primary_path=primary, success_path=success, quarantine_path=vault,
        failed_path=failed, dead_path=dead, min_delay=0.0, max_delay=0.0,
    )
    return mgr


def _route(monkeypatch, table):
    """table: email -> (status, days, msg, bal, last_gift)."""
    def fake(self, account):
        status, days, msg, bal, lg = table[account["email"]]
        account["balance"] = bal
        return status, days, msg, bal, lg
    monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "check_account_status", fake)


# ─────────────────────────────────────────────────────────────────────────────
# 1) helper contract
# ─────────────────────────────────────────────────────────────────────────────
class TestHelper:
    def test_01_helper_exists_beside_merge_by_email(self):
        assert hasattr(MOD.MasterDelayedGiftsManager, "_activate_for_bot31")
        src = MANAGER_SRC
        i_helper = src.index("def _activate_for_bot31(")
        i_merge = src.index("def _merge_by_email(")
        i_revival = src.index("def run_revival(")
        # A5 zone: helpers live next to _merge_by_email, before run_revival
        assert abs(i_helper - i_merge) < 2500
        assert i_helper < i_revival

    def test_02_rich_balance_releases_cooldown(self):
        acc = {"email": "a@x.com", "status": "cooldown", "active": False,
               "cooldown_until": 9999999999.0, "quarantined": True,
               "quarantine_info": {"reason": "cooldown_forbidden"}}
        out = MOD.MasterDelayedGiftsManager._activate_for_bot31(acc, 100)
        assert out is acc  # in-place, returns the same dict
        assert acc["status"] == "active" and acc["active"] is True
        assert acc["cooldown_until"] == 0
        assert ISO_RE.match(acc["cooldown_released_at"])
        assert ISO_RE.match(acc["last_updated"])
        assert "quarantine_info" not in acc and "quarantined" not in acc

    def test_03_poor_balance_is_cooled_29h_like_bot31(self):
        """[MAINT-4-D] <100 => status=cooldown, active=False, cooldown_until=now+29h (01.33 1286-1297 shape)."""
        acc = {"email": "a@x.com", "status": "auth_failed", "active": True,
               "cooldown_until": 123.0, "quarantine_info": {"x": 1}, "quarantined": True}
        t0 = time.time()
        MOD.MasterDelayedGiftsManager._activate_for_bot31(acc, 99)
        assert acc["status"] == "cooldown" and acc["active"] is False
        assert isinstance(acc["cooldown_until"], int)
        assert t0 + 29 * 3600 - 2 <= acc["cooldown_until"] <= time.time() + 29 * 3600 + 2
        assert "cooldown_released_at" not in acc
        assert ISO_RE.match(acc["last_updated"])
        assert "quarantine_info" not in acc and "quarantined" not in acc

    def test_04_none_balance_treated_as_zero(self):
        acc = {"email": "a@x.com", "cooldown_until": 5}
        MOD.MasterDelayedGiftsManager._activate_for_bot31(acc, None)
        assert acc["status"] == "cooldown" and acc["active"] is False
        assert acc["cooldown_until"] > time.time() + 28 * 3600

    def test_04b_zero_balance_is_rejected_by_0133_after_helper(self, bridge):
        """[MAINT-4-D] owner's case: balance 0 must NOT become selectable by bot 31."""
        acc = {"email": "zero@x.com", "status": "active", "active": True, "balance": 0}
        MOD.MasterDelayedGiftsManager._activate_for_bot31(acc, 0)
        assert bridge.is_account_ready(acc) is False

    def test_04c_boundary_99_vs_100(self, bridge):
        poor = MOD.MasterDelayedGiftsManager._activate_for_bot31({"email": "p@x.com"}, 99)
        rich = MOD.MasterDelayedGiftsManager._activate_for_bot31({"email": "r@x.com"}, 100)
        assert poor["status"] == "cooldown" and bridge.is_account_ready(poor) is False
        assert rich["status"] == "active" and rich["cooldown_until"] == 0 and bridge.is_account_ready(rich) is True

    def test_05_helper_never_touches_credentials(self):
        acc = {"email": "a@x.com", "password": "pw", "cookies": {"s": 1}, "balance": 7}
        MOD.MasterDelayedGiftsManager._activate_for_bot31(acc, 500)
        assert acc["password"] == "pw" and acc["cookies"] == {"s": 1} and acc["balance"] == 7


# ─────────────────────────────────────────────────────────────────────────────
# 2) D40 — run_quarantine HEALTHY block
# ─────────────────────────────────────────────────────────────────────────────
class TestD40RunQuarantine:
    def test_10_healthy_rich_account_is_activated_in_primary_and_success(self, tmp_path, monkeypatch):
        mgr = _mgr(tmp_path, monkeypatch, "accounts_delayed_gifts_credits.json")
        _write(mgr.primary_path, [{
            "email": "rich@x.com", "password": "pw", "status": "auth_failed", "active": False,
            "cooldown_until": 9999999999.0, "quarantined": True,
            "quarantine_info": {"reason": "stale_daily_gift", "days_without_gift": 20},
        }])
        _route(monkeypatch, {"rich@x.com": ("HEALTHY", 1, "t", 400, {})})
        res = mgr.run_quarantine()
        assert res["healthy"] == 1
        for path in (mgr.primary_path, mgr.success_path):
            a = _by_email(_read(path), "rich@x.com")
            assert a["status"] == "active" and a["active"] is True
            assert a["cooldown_until"] == 0 and ISO_RE.match(a["cooldown_released_at"])
            assert ISO_RE.match(a["last_updated"])
            assert "quarantine_info" not in a and "quarantined" not in a

    def test_11_healthy_poor_account_is_cooled_in_place(self, tmp_path, monkeypatch, bridge):
        """[MAINT-4-D] HEALTHY but <100: stays in primary (no move) with cooldown 29h, active=False."""
        mgr = _mgr(tmp_path, monkeypatch, "accounts_delayed_gifts_credits.json")
        _write(mgr.primary_path, [{"email": "poor@x.com", "password": "pw", "active": True,
                                   "cooldown_until": 777.0}])
        _route(monkeypatch, {"poor@x.com": ("HEALTHY", 1, "t", 50, {})})
        mgr.run_quarantine()
        a = _by_email(_read(mgr.primary_path), "poor@x.com")
        assert a["active"] is False and a["status"] == "cooldown"
        assert a["cooldown_until"] > time.time() + 28 * 3600 and "cooldown_released_at" not in a
        assert bridge.is_account_ready(a) is False
        assert a["password"] == "pw"  # still in primary, credentials intact (no physical move)

    def test_12_stale_and_dead_are_not_activated(self, tmp_path, monkeypatch):
        mgr = _mgr(tmp_path, monkeypatch, "accounts_delayed_gifts_credits.json")
        _write(mgr.primary_path, [{"email": "stale@x.com", "password": "pw", "active": False},
                                  {"email": "dead@x.com", "password": "pw", "active": False}])
        _route(monkeypatch, {"stale@x.com": ("STALE", 20, "t", 500, {}),
                             "dead@x.com": ("DEAD", 0, "suspended", 0, {"reason": "suspended"})})
        mgr.run_quarantine()
        q = _by_email(_read(mgr.quarantine_path), "stale@x.com")
        assert q.get("active") is False and "cooldown_released_at" not in q
        f = _by_email(_read(mgr.failed_path), "dead@x.com")
        assert f.get("active") is False and f["status"] == "suspended"

    def test_13_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        mgr = _mgr(tmp_path, monkeypatch, "accounts_delayed_gifts_credits.json")
        _write(mgr.primary_path, [{"email": "rich@x.com", "password": "pw", "active": False}])
        _route(monkeypatch, {"rich@x.com": ("HEALTHY", 1, "t", 400, {})})
        before = mgr.primary_path.read_bytes()
        mgr.run_quarantine(dry_run=True)
        assert mgr.primary_path.read_bytes() == before and not mgr.success_path.exists()

    def test_14_ready_31_tag_printed_only_for_rich(self, tmp_path, monkeypatch, capsys):
        mgr = _mgr(tmp_path, monkeypatch, "accounts_delayed_gifts_credits.json")
        _write(mgr.primary_path, [{"email": "rich@x.com", "password": "pw"},
                                  {"email": "poor@x.com", "password": "pw"}])
        _route(monkeypatch, {"rich@x.com": ("HEALTHY", 1, "t", 400, {}),
                             "poor@x.com": ("HEALTHY", 1, "t", 40, {})})
        mgr.run_quarantine()
        out = capsys.readouterr().out
        rich_line = next(l for l in out.splitlines() if "rich@x.com" in l)
        poor_line = next(l for l in out.splitlines() if "poor@x.com" in l)
        assert "31" in rich_line and "31" not in poor_line


# ─────────────────────────────────────────────────────────────────────────────
# 3) D41 — run_revival + cross-program contract with 01.33
# ─────────────────────────────────────────────────────────────────────────────
class TestD41RunRevival:
    def _setup(self, tmp_path, monkeypatch, vault, verdicts, bal=1000):
        mgr = _mgr(tmp_path, monkeypatch)
        _write(mgr.primary_path, [])
        _write(mgr.success_path, [])
        _write(mgr.quarantine_path, vault)

        def fake(self, account):
            status, days = verdicts[account["email"]]
            account["balance"] = bal
            return status, days, "2026-10-30T00:00:00", bal, None
        monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "check_account_status", fake)
        return mgr

    def test_20_revived_record_carries_all_bot31_flags(self, tmp_path, monkeypatch):
        mgr = self._setup(tmp_path, monkeypatch, [_vault_record_as_written_by_0133()],
                          {"cool@x.com": ("HEALTHY", 1)}, bal=1000)
        res = mgr.run_revival(limit=0)
        assert res["revived"] == 1
        for path in (mgr.primary_path, mgr.success_path):
            a = _by_email(_read(path), "cool@x.com")
            assert a["status"] == "active" and a["active"] is True
            assert a["cooldown_until"] == 0 and ISO_RE.match(a["cooldown_released_at"])
            assert ISO_RE.match(a["last_updated"])
            assert "quarantine_info" not in a and "quarantined" not in a
            assert a["password"] == "pw" and a["cookies"] == {"session_id": "abc"}
        assert _read(mgr.quarantine_path) == []

    def test_21_cross_program_0133_accepts_revived_account(self, tmp_path, monkeypatch, bridge):
        """01.33 vault record -> 05.02 run_revival -> 01.33 is_account_ready == True."""
        rec = _vault_record_as_written_by_0133(email="bridge@x.com", cooldown_until=9999999999.0)
        assert bridge.is_account_ready(rec) is False  # before: rejected (active=False / cooldown)
        mgr = self._setup(tmp_path, monkeypatch, [rec], {"bridge@x.com": ("HEALTHY", 2)}, bal=250)
        mgr.run_revival(limit=0)
        revived = _by_email(_read(mgr.primary_path), "bridge@x.com")
        assert bridge.is_account_ready(revived) is True

    def test_22_revived_poor_balance_is_cooled_and_bridge_rejects(self, tmp_path, monkeypatch, bridge):
        """[MAINT-4-D] revived with <100 => back in primary as cooldown/active=False/29h; 01.33 rejects it."""
        rec = _vault_record_as_written_by_0133(email="poor@x.com", cooldown_until=9999999999.0)
        mgr = self._setup(tmp_path, monkeypatch, [rec], {"poor@x.com": ("HEALTHY", 1)}, bal=20)
        mgr.run_revival(limit=0)
        revived = _by_email(_read(mgr.primary_path), "poor@x.com")
        assert revived["active"] is False and revived["status"] == "cooldown"
        assert time.time() + 28 * 3600 < revived["cooldown_until"] < time.time() + 30 * 3600
        assert "quarantine_info" not in revived and "quarantined" not in revived
        assert bridge.is_account_ready(revived) is False

    def test_23_still_stale_and_dead_not_activated(self, tmp_path, monkeypatch):
        vault = [_vault_record_as_written_by_0133("dead@x.com"),
                 _vault_record_as_written_by_0133("old@x.com")]
        mgr = self._setup(tmp_path, monkeypatch, vault,
                          {"dead@x.com": ("DEAD", None), "old@x.com": ("HEALTHY", 9)})
        res = mgr.run_revival(limit=0)
        assert res["revived"] == 0 and res["moved_to_failed"] == 1 and res["still_stale"] == 1
        f = _by_email(_read(mgr.failed_path), "dead@x.com")
        assert f["active"] is False and "cooldown_released_at" not in f
        o = _by_email(_read(mgr.quarantine_path), "old@x.com")
        assert o["active"] is False

    def test_24_revival_logs_full_record_with_new_flags(self, tmp_path, monkeypatch):
        mgr = self._setup(tmp_path, monkeypatch, [_vault_record_as_written_by_0133()],
                          {"cool@x.com": ("HEALTHY", 1)})
        mgr.run_revival(limit=0)
        log = tmp_path / "account_log.jsonl"
        assert log.exists()
        line = json.loads(log.read_text(encoding="utf-8").strip().splitlines()[-1])
        # D43: _log_move schema untouched (email/password/cookies/reason/paths/by)
        assert line["event"] == "return_to_primary" and line["reason"] == "HEALTHY"
        assert line["email"] == "cool@x.com" and line["password"] == "pw" and line["by"] == "05.02"
        assert line["to_path"].endswith("accounts_genspark.json")


# ─────────────────────────────────────────────────────────────────────────────
# 4) D42 / D43 / hygiene
# ─────────────────────────────────────────────────────────────────────────────
class TestInvariants:
    def test_30_d42_sort_desc_after_graft(self, tmp_path, monkeypatch):
        mgr = _mgr(tmp_path, monkeypatch, "accounts_delayed_gifts_credits.json")
        _write(mgr.primary_path, [{"email": e, "password": "pw"} for e in ("a@x.com", "b@x.com", "c@x.com")])
        _route(monkeypatch, {"a@x.com": ("HEALTHY", 1, "t", 10, {}),
                             "b@x.com": ("HEALTHY", 1, "t", 500, {}),
                             "c@x.com": ("HEALTHY", 1, "t", 70, {})})
        mgr.run_quarantine()
        assert [a["email"] for a in _read(mgr.primary_path)] == ["b@x.com", "c@x.com", "a@x.com"]
        assert [a["email"] for a in _read(mgr.success_path)] == ["b@x.com", "c@x.com", "a@x.com"]

    def test_31_d43_sre_primitives_untouched(self):
        for name in ("_with_vault_lock", "_log_move", "_trim_account_log", "_merge_by_email"):
            assert hasattr(MOD.MasterDelayedGiftsManager, name)
        assert MOD.MasterDelayedGiftsManager.COOLDOWN_VAULT_LOCK_FILENAME == "accounts_cooldown.json.lock"
        rev = inspect.getsource(MOD.MasterDelayedGiftsManager.run_revival)
        assert "_with_vault_lock(" in rev and "_log_move(" in rev and "_trim_account_log(" in rev
        assert "sys.exit(1)" in MANAGER_SRC

    def test_32_helper_called_exactly_once_per_site(self):
        rq = inspect.getsource(MOD.MasterDelayedGiftsManager.run_quarantine)
        rv = inspect.getsource(MOD.MasterDelayedGiftsManager.run_revival)
        assert rq.count("_activate_for_bot31(") == 1
        assert rv.count("_activate_for_bot31(") == 1
        # DRY: field writes live only inside the helper
        assert MANAGER_SRC.count('"cooldown_released_at"') == 1

    def test_33_threshold_contract_not_drifted_from_0503(self):
        assert "days_elapsed >= self.threshold_days" in MANAGER_SRC
        assert "Edition 05.03" not in MANAGER_SRC

    def test_34_file_is_pure_lf_and_no_bak_tracked(self):
        raw = MANAGER_FILE.read_bytes()
        assert b"\r" not in raw
        tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout
        assert not [l for l in tracked.splitlines() if l.endswith(".bak")]
