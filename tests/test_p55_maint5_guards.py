"""
P55 — MAINT-5 (owner GO card 2026-11-02, Gist b6ba8643…, voices 105–114; Q-11..Q-17):
05.02 ``main()`` safety valves only — 01.33 untouched (Q-11).

What is verified (offline, no network, no repo file touched):
  * Q-14 Rate-Limit guard: ``main()`` without ``--revive`` refuses to scan the primary
    file over the network unless ``--allow-primary-scan`` is passed -> exit 1, clear
    message, ``check_account_status`` never reached (also under ``--dry-run``).
  * Q-14 with the flag -> ``run_quarantine`` runs with the legacy ``SCAN_LIMIT`` default.
  * Q-15 ``--revive`` default = whole vault (``limit=0``); explicit ``-l N`` still honoured.
  * Q-13 no new manual tools (``--list-ready`` absent).  Q-16 floating 29h kept.
  * D33 lock name ``accounts_cooldown.json.lock``;  MAINT-4-E: no ``accounts_success`` token.
  * Surgery confined to ``main()``/``Config`` — ``run_quarantine``/``run_revival`` bodies carry no guard.
"""
from __future__ import annotations
import importlib.util
import inspect
import json
import sys
import types
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
MANAGER_FILE = ROOT / "05.02_genspark_delayed_gifts_manager.py"


def _load():
    stub = types.ModuleType("genspark_master_account_manager")
    for name in ("do_b2c_login", "get_session", "check_account_balance"):
        setattr(stub, name, lambda *a, _n=name, **k: (_ for _ in ()).throw(RuntimeError(f"{_n} must never run in P55")))
    sys.modules.setdefault("genspark_master_account_manager", stub)
    spec = importlib.util.spec_from_file_location("p55_manager_under_test", MANAGER_FILE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


MOD = _load()
SRC = MANAGER_FILE.read_text(encoding="utf-8")


def _write(p: Path, data):
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(MOD, "resolve_file_path", lambda name: tmp_path / name)
    _write(tmp_path / "accounts_genspark.json", [{"email": "a@x.com", "password": "pw"}])
    _write(tmp_path / "accounts_cooldown.json", [])

    def _no_net(self, account):  # pragma: no cover
        raise AssertionError("network probe reached — guard failed")
    monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "check_account_status", _no_net)
    calls = {}

    def fake_q(self, scan_mode="all", limit=10, dry_run=False):
        calls["quarantine"] = {"scan_mode": scan_mode, "limit": limit, "dry_run": dry_run}
        return {"scanned": 0}

    def fake_r(self, limit=50, dry_run=False):
        calls["revival"] = {"limit": limit, "dry_run": dry_run}
        return {"revived": 0}
    monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "run_quarantine", fake_q)
    monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "run_revival", fake_r)
    return tmp_path, calls


def _run(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["05.02", *argv])
    return MOD.main()


class TestQ14RateLimitGuard:
    def test_01_primary_scan_refused_without_flag(self, env, monkeypatch, capsys):
        _, calls = env
        with pytest.raises(SystemExit) as ex:
            _run(monkeypatch, [])
        assert ex.value.code == 1
        out = capsys.readouterr().out
        assert "--allow-primary-scan" in out and "accounts_cooldown.json" in out
        assert "quarantine" not in calls and "revival" not in calls

    def test_02_dry_run_is_also_refused(self, env, monkeypatch):
        """check_account_status hits the network even in dry-run -> same guard."""
        _, calls = env
        with pytest.raises(SystemExit) as ex:
            _run(monkeypatch, ["--dry-run"])
        assert ex.value.code == 1 and not calls

    def test_03_flag_allows_primary_scan_with_legacy_default_limit(self, env, monkeypatch):
        _, calls = env
        _run(monkeypatch, ["--allow-primary-scan"])
        assert calls["quarantine"]["limit"] == MOD.Config.SCAN_LIMIT == 10
        assert calls["quarantine"]["scan_mode"] == "all" and "revival" not in calls

    def test_04_revive_never_needs_the_flag(self, env, monkeypatch):
        _, calls = env
        _run(monkeypatch, ["--revive", "-q", "accounts_cooldown.json"])
        assert "revival" in calls and "quarantine" not in calls


class TestQ15ReviveWholeVault:
    def test_10_revive_default_limit_is_zero(self, env, monkeypatch):
        _, calls = env
        _run(monkeypatch, ["--revive", "-q", "accounts_cooldown.json"])
        assert calls["revival"]["limit"] == 0  # D38: 0 = whole vault

    def test_11_explicit_limit_still_honoured(self, env, monkeypatch):
        _, calls = env
        _run(monkeypatch, ["--revive", "-q", "accounts_cooldown.json", "-l", "5"])
        assert calls["revival"]["limit"] == 5

    def test_12_quarantine_explicit_limit_honoured(self, env, monkeypatch):
        _, calls = env
        _run(monkeypatch, ["--allow-primary-scan", "-m", "first_n", "-l", "3"])
        assert calls["quarantine"] == {"scan_mode": "first_n", "limit": 3, "dry_run": False}


class TestMaint5SourceContracts:
    def test_20_lock_name_and_no_success_token(self):
        assert MOD.MasterDelayedGiftsManager.COOLDOWN_VAULT_LOCK_FILENAME == "accounts_cooldown.json.lock"  # D33
        assert "accounts_success" not in SRC  # MAINT-4-E

    def test_21_no_new_manual_tools_q13(self):
        assert "--list-ready" not in SRC and "list_ready" not in SRC

    def test_22_floating_29h_kept_q16(self):
        body = inspect.getsource(MOD.MasterDelayedGiftsManager._activate_for_bot31)
        assert "29 * 3600" in body and "midnight" not in body.lower()

    def test_23_guard_lives_in_main_only(self):
        for fn in (MOD.MasterDelayedGiftsManager.run_quarantine, MOD.MasterDelayedGiftsManager.run_revival):
            assert "allow_primary" not in inspect.getsource(fn)
        assert "allow_primary_scan" in inspect.getsource(MOD.main)

    def test_24_lf_only(self):
        assert b"\r" not in MANAGER_FILE.read_bytes()
