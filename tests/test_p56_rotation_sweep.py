"""
P56 — MAINT-6 (owner REVIEW_AND_EXECUTE card 2026-11-03, Gist b6ba8643…, voices 123–133, doc 23; D48 + Q-18..Q-24):
Drip Health Sweeper & Rotation Engine — ``--sweep`` inside 05.02 only. 01.33 / 01.03 untouched.

What is verified (offline, no network, no repo file touched):
  * RotationCheckpoint: sha256 keys only (Q-23, no e-mail inside the file), atomic save after every
    account (voice 130 / SRE risk 3), orphan-hash pruning + dynamic reset
    ``remaining = set(primary) - set(checked) == 0`` => cycle_no+1 (voice 130 / SRE risk 2).
  * run_quarantine(rotation=...): checked accounts are skipped next run, every primary account
    (cooldown/zero/immune) enters the checkpoint (voice 130), AUTH_FAILED counts as checked (Q-20),
    dry-run never writes the checkpoint, routing matrix 4a–4d unchanged, return dict unchanged.
  * Q-22: primary writes happen under the shared D33 lock (``accounts_cooldown.json.lock``) and merge
    05.02 fields into the fresh on-disk record instead of replacing it (01.33's ``last_used`` survives);
    busy lock => nothing written, ``{"error": "vault_lock_busy"}`` => exit 1 (D39).
  * Q-19 (voice 124): <100 with a *running* cooldown set by 01.33 is left exactly as is; expired/zero
    cooldown still gets now+29h (D45 kept for that case).
  * main(): ``--sweep`` passes the Q-14 guard, default batch 10 / first_n (Q-21), ``-m all`` refused,
    ``-l`` capped at 20 (Q-24), ``--sweep --revive`` refused, delays 60–300 s (voice 130).
  * Contracts: ``.gitignore`` covers the checkpoint, 01.33 byte-identical to the MAINT-5 baseline, LF only.
"""
from __future__ import annotations
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
import time
import types
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
MANAGER_FILE = ROOT / "05.02_genspark_delayed_gifts_manager.py"
BRIDGE_FILE = ROOT / "01.33_telegram_gen_bridge.py"
CKPT = "genspark_rotation_checkpoint.json"


def _load():
    stub = types.ModuleType("genspark_master_account_manager")
    for name in ("do_b2c_login", "get_session", "check_account_balance"):
        setattr(stub, name, lambda *a, _n=name, **k: (_ for _ in ()).throw(RuntimeError(f"{_n} must never run in P56")))
    sys.modules.setdefault("genspark_master_account_manager", stub)
    spec = importlib.util.spec_from_file_location("p56_manager_under_test", MANAGER_FILE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


MOD = _load()
SRC = MANAGER_FILE.read_text(encoding="utf-8")


def _write(p: Path, data):
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _read(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def _by_email(rows, email):
    return next(a for a in rows if a["email"] == email)


def _mgr(tmp_path, monkeypatch):
    monkeypatch.setattr(MOD, "resolve_file_path", lambda name: tmp_path / name)
    return MOD.MasterDelayedGiftsManager(
        primary_path=tmp_path / "accounts_genspark.json",
        quarantine_path=tmp_path / MOD.Config.QUARANTINE_FILE,
        failed_path=tmp_path / MOD.Config.FAILED_FILE,
        dead_path=tmp_path / MOD.Config.DEAD_FILE,
        min_delay=0.0, max_delay=0.0,
    )


def _route(monkeypatch, table, calls=None):
    """table: email -> (status, days, msg, bal, last_gift). Records call order in ``calls``."""
    def fake(self, account):
        if calls is not None:
            calls.append(account["email"])
        status, days, msg, bal, lg = table[account["email"]]
        account["balance"] = bal
        return status, days, msg, bal, lg
    monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "check_account_status", fake)


def _accounts(n, prefix="u"):
    return [{"email": f"{prefix}{i}@x.com", "password": "pw", "balance": None} for i in range(n)]


HEALTHY_RICH = ("HEALTHY", 1, "t", 150, {"credit_type": "daily_gift"})
HEALTHY_POOR = ("HEALTHY", 1, "t", 20, {"credit_type": "daily_gift"})
STALE = ("STALE", 20, "t", 300, {"credit_type": "daily_gift"})
DEAD = ("DEAD", 0, "banned", 0, {"reason": "suspended"})
NET = ("AUTH_FAILED", None, "network", 0, None)


# ─────────────────────────────────────────────────────────────────────────────
# 1) RotationCheckpoint unit contract
# ─────────────────────────────────────────────────────────────────────────────
class TestRotationCheckpoint:
    def test_01_keys_are_sha256_and_no_email_on_disk(self, tmp_path):
        ck = MOD.RotationCheckpoint(tmp_path / CKPT)
        assert ck.mark("Alice@X.com") is True
        raw = (tmp_path / CKPT).read_text(encoding="utf-8")
        assert "alice" not in raw.lower() and "@" not in raw
        assert MOD.RotationCheckpoint.key("ALICE@x.com ") == hashlib.sha256(b"alice@x.com").hexdigest()
        assert ck.checked == {hashlib.sha256(b"alice@x.com").hexdigest()}
        state = json.loads(raw)
        assert state["schema"] == 1 and state["cycle_no"] == 1 and set(state) >= {"cycle_started_at", "last_run_at", "checked"}

    def test_02_begin_cycle_remaining_prune_and_reset(self, tmp_path):
        ck = MOD.RotationCheckpoint(tmp_path / CKPT)
        ck.mark("a@x.com"); ck.mark("gone@x.com")          # gone@ left the primary (cut to failed)
        remaining = ck.begin_cycle(["a@x.com", "b@x.com"])
        assert remaining == {"b@x.com"}
        assert ck.checked == {MOD.RotationCheckpoint.key("a@x.com")}  # orphan pruned (SRE risk 2)
        ck.mark("b@x.com")
        # all live accounts covered => reset to a new cycle with everything remaining again
        remaining2 = ck.begin_cycle(["a@x.com", "b@x.com"])
        assert remaining2 == {"a@x.com", "b@x.com"} and ck.state["cycle_no"] == 2 and ck.checked == set()

    def test_03_corrupt_or_missing_file_starts_fresh(self, tmp_path):
        p = tmp_path / CKPT
        p.write_text("{not json", encoding="utf-8")
        ck = MOD.RotationCheckpoint(p)
        assert ck.state["cycle_no"] == 1 and ck.checked == set()
        assert MOD.RotationCheckpoint(tmp_path / "absent.json").checked == set()

    def test_04_empty_primary_does_not_reset(self, tmp_path):
        ck = MOD.RotationCheckpoint(tmp_path / CKPT)
        ck.mark("a@x.com")
        assert ck.begin_cycle([]) == set() and ck.state["cycle_no"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# 2) run_quarantine with rotation — the drip loop
# ─────────────────────────────────────────────────────────────────────────────
class TestSweepLoop:
    def test_10_batches_rotate_until_full_cycle_then_reset(self, tmp_path, monkeypatch):
        mgr = _mgr(tmp_path, monkeypatch)
        accs = _accounts(25)
        _write(mgr.primary_path, accs)
        table = {a["email"]: HEALTHY_RICH for a in accs}
        seen = []
        _route(monkeypatch, table, seen)
        ck_path = tmp_path / CKPT
        for run in range(3):
            res = mgr.run_quarantine(scan_mode="first_n", limit=10, rotation=MOD.RotationCheckpoint(ck_path))
            assert res["scanned"] == (10, 10, 5)[run]
        assert len(seen) == 25 and len(set(seen)) == 25            # every primary account entered once
        st = json.loads(ck_path.read_text(encoding="utf-8"))
        assert len(st["checked"]) == 25 and st["cycle_no"] == 1
        # 4th run: remaining == 0 => auto reset, new cycle, batch of 10 again
        res = mgr.run_quarantine(scan_mode="first_n", limit=10, rotation=MOD.RotationCheckpoint(ck_path))
        st = json.loads(ck_path.read_text(encoding="utf-8"))
        assert res["scanned"] == 10 and st["cycle_no"] == 2 and len(st["checked"]) == 10

    def test_11_every_state_enters_checkpoint_including_auth_failed(self, tmp_path, monkeypatch):
        """voice 130: cooldown/zero/immune all enter; Q-20: transient network error counts as checked."""
        mgr = _mgr(tmp_path, monkeypatch)
        _write(mgr.primary_path, [
            {"email": "rich@x.com", "password": "pw"},
            {"email": "poor@x.com", "password": "pw", "status": "cooldown", "active": False, "cooldown_until": time.time() + 3600},
            {"email": "stale@x.com", "password": "pw"},
            {"email": "dead@x.com", "password": "pw"},
            {"email": "net@x.com", "password": "pw"},
        ])
        _route(monkeypatch, {"rich@x.com": HEALTHY_RICH, "poor@x.com": HEALTHY_POOR, "stale@x.com": STALE,
                             "dead@x.com": DEAD, "net@x.com": NET})
        res = mgr.run_quarantine(scan_mode="first_n", limit=10, rotation=MOD.RotationCheckpoint(tmp_path / CKPT))
        assert res == {"scanned": 5, "healthy": 2, "stale_cut": 1, "dead_cut": 1, "auth_failed": 1, "total_credits": 170}
        st = json.loads((tmp_path / CKPT).read_text(encoding="utf-8"))
        assert set(st["checked"]) == {MOD.RotationCheckpoint.key(e) for e in ("rich@x.com", "poor@x.com", "stale@x.com", "dead@x.com", "net@x.com")}
        # routing matrix 4a–4d intact
        primary = {a["email"]: a for a in _read(mgr.primary_path)}
        assert set(primary) == {"rich@x.com", "poor@x.com", "net@x.com"}
        assert primary["rich@x.com"]["status"] == "active" and primary["rich@x.com"]["cooldown_until"] == 0
        assert primary["poor@x.com"]["status"] == "cooldown" and primary["poor@x.com"]["active"] is False
        assert {a["email"] for a in _read(mgr.quarantine_path)} == {"stale@x.com"}
        assert {a["email"] for a in _read(mgr.failed_path)} == {"dead@x.com"}
        # next run: nothing left except the orphans pruned => reset => all 3 live ones again
        seen = []
        _route(monkeypatch, {"rich@x.com": HEALTHY_RICH, "poor@x.com": HEALTHY_POOR, "net@x.com": NET}, seen)
        mgr.run_quarantine(scan_mode="first_n", limit=10, rotation=MOD.RotationCheckpoint(tmp_path / CKPT))
        assert sorted(seen) == ["net@x.com", "poor@x.com", "rich@x.com"]
        assert json.loads((tmp_path / CKPT).read_text(encoding="utf-8"))["cycle_no"] == 2

    def test_12_checkpoint_saved_after_each_account_not_only_at_end(self, tmp_path, monkeypatch):
        """SRE risk 3: power cut after the 3rd account must not lose the first three."""
        mgr = _mgr(tmp_path, monkeypatch)
        accs = _accounts(6)
        _write(mgr.primary_path, accs)
        snapshots = []

        def fake(self, account):
            p = tmp_path / CKPT
            snapshots.append(len(json.loads(p.read_text(encoding="utf-8"))["checked"]) if p.exists() else -1)
            account["balance"] = 150
            if account["email"] == "u3@x.com":
                MOD.IS_RUNNING = False      # simulate Ctrl+C / scheduler kill after the 4th probe
            return HEALTHY_RICH
        monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "check_account_status", fake)
        try:
            mgr.run_quarantine(scan_mode="first_n", limit=10, rotation=MOD.RotationCheckpoint(tmp_path / CKPT))
        finally:
            MOD.IS_RUNNING = True
        assert snapshots == [0, 1, 2, 3]                                  # grew by one per account
        st = json.loads((tmp_path / CKPT).read_text(encoding="utf-8"))
        assert len(st["checked"]) == 4                                    # u0..u3 persisted before the stop

    def test_13_dry_run_never_writes_checkpoint_or_files(self, tmp_path, monkeypatch):
        mgr = _mgr(tmp_path, monkeypatch)
        _write(mgr.primary_path, _accounts(3))
        _route(monkeypatch, {f"u{i}@x.com": STALE for i in range(3)})
        before = mgr.primary_path.read_bytes()
        mgr.run_quarantine(scan_mode="first_n", limit=10, dry_run=True, rotation=MOD.RotationCheckpoint(tmp_path / CKPT))
        assert not (tmp_path / CKPT).exists() and mgr.primary_path.read_bytes() == before
        assert not mgr.quarantine_path.exists()

    def test_14_without_rotation_legacy_behaviour_and_no_checkpoint(self, tmp_path, monkeypatch):
        mgr = _mgr(tmp_path, monkeypatch)
        _write(mgr.primary_path, _accounts(3))
        _route(monkeypatch, {f"u{i}@x.com": HEALTHY_RICH for i in range(3)})
        assert mgr.run_quarantine()["scanned"] == 3
        assert not (tmp_path / CKPT).exists()


# ─────────────────────────────────────────────────────────────────────────────
# 3) Q-22 — shared lock + field merge
# ─────────────────────────────────────────────────────────────────────────────
class TestLockAndMerge:
    def test_20_merge_keeps_fields_written_by_0133_during_the_probe(self, tmp_path, monkeypatch):
        mgr = _mgr(tmp_path, monkeypatch)
        _write(mgr.primary_path, [{"email": "a@x.com", "password": "pw", "last_used": 1.0, "quarantined": True}])

        def fake(self, account):
            # 01.33 writes last_used + a new note while 05.02 holds its in-memory copy
            rows = _read(mgr.primary_path)
            rows[0]["last_used"] = 999.0
            rows[0]["note_from_bridge"] = "kept"
            _write(mgr.primary_path, rows)
            account["balance"] = 150
            return HEALTHY_RICH
        monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "check_account_status", fake)
        mgr.run_quarantine(scan_mode="first_n", limit=10, rotation=MOD.RotationCheckpoint(tmp_path / CKPT))
        a = _by_email(_read(mgr.primary_path), "a@x.com")
        assert a["last_used"] == 999.0 and a["note_from_bridge"] == "kept"      # not clobbered
        assert a["status"] == "active" and a["active"] is True and a["cooldown_until"] == 0 and a["balance"] == 150
        assert "quarantined" not in a and a["password"] == "pw"

    def test_21_primary_writes_happen_under_the_d33_lock(self, tmp_path, monkeypatch):
        mgr = _mgr(tmp_path, monkeypatch)
        _write(mgr.primary_path, [{"email": "a@x.com", "password": "pw"}])
        _route(monkeypatch, {"a@x.com": HEALTHY_RICH})
        lock = tmp_path / "accounts_cooldown.json.lock"
        seen = {"held": False}
        orig = MOD.atomic_save_json

        def spy(path, data):
            if Path(path) == mgr.primary_path:
                seen["held"] = lock.exists()
            return orig(path, data)
        monkeypatch.setattr(MOD, "atomic_save_json", spy)
        mgr.run_quarantine(scan_mode="first_n", limit=10, rotation=MOD.RotationCheckpoint(tmp_path / CKPT))
        assert seen["held"] is True and not lock.exists()                       # held during, released after

    def test_22_busy_lock_writes_nothing_and_reports_error(self, tmp_path, monkeypatch):
        mgr = _mgr(tmp_path, monkeypatch)
        _write(mgr.primary_path, [{"email": "a@x.com", "password": "pw"}, {"email": "s@x.com", "password": "pw"}])
        _route(monkeypatch, {"a@x.com": HEALTHY_RICH, "s@x.com": STALE})
        monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "COOLDOWN_VAULT_LOCK_TIMEOUT_S", 0.2)
        lock = tmp_path / "accounts_cooldown.json.lock"
        lock.write_text("other-process", encoding="utf-8")                      # fresh lock, not orphan
        before = mgr.primary_path.read_bytes()
        res = mgr.run_quarantine(scan_mode="first_n", limit=10, rotation=MOD.RotationCheckpoint(tmp_path / CKPT))
        assert res.get("error") == "vault_lock_busy"
        assert mgr.primary_path.read_bytes() == before and not mgr.quarantine_path.exists()
        assert not (tmp_path / CKPT).exists() or json.loads((tmp_path / CKPT).read_text(encoding="utf-8"))["checked"] == []
        lock.unlink()


# ─────────────────────────────────────────────────────────────────────────────
# 4) Q-19 — voice 124: running cooldown is left untouched
# ─────────────────────────────────────────────────────────────────────────────
class TestQ19LeaveRunningCooldown:
    def test_30_running_cooldown_is_not_extended(self):
        cd = int(time.time() + 5 * 3600)                                        # set by 01.33 24h ago (29h window)
        acc = {"email": "a@x.com", "status": "cooldown", "active": False, "cooldown_until": cd}
        MOD.MasterDelayedGiftsManager._activate_for_bot31(acc, 0)
        assert acc["cooldown_until"] == cd and acc["status"] == "cooldown" and acc["active"] is False

    def test_31_expired_or_zero_cooldown_still_gets_29h(self):
        for old in (0, 123.0, None, "bad"):
            acc = {"email": "a@x.com", "cooldown_until": old}
            MOD.MasterDelayedGiftsManager._activate_for_bot31(acc, 50)
            assert time.time() + 28 * 3600 < acc["cooldown_until"] <= time.time() + 29 * 3600 + 2

    def test_32_absurd_far_future_cooldown_is_normalised(self):
        acc = {"email": "a@x.com", "cooldown_until": 9999999999.0}
        MOD.MasterDelayedGiftsManager._activate_for_bot31(acc, 50)
        assert acc["cooldown_until"] <= time.time() + 29 * 3600 + 2

    def test_33_rich_balance_unaffected(self):
        acc = {"email": "a@x.com", "cooldown_until": time.time() + 3600}
        MOD.MasterDelayedGiftsManager._activate_for_bot31(acc, 100)
        assert acc["cooldown_until"] == 0 and acc["status"] == "active" and acc["active"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 5) main() — --sweep valves
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(MOD, "resolve_file_path", lambda name: tmp_path / name)
    _write(tmp_path / "accounts_genspark.json", [{"email": "a@x.com", "password": "pw"}])
    _write(tmp_path / "accounts_cooldown.json", [])

    def _no_net(self, account):  # pragma: no cover
        raise AssertionError("network probe reached")
    monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "check_account_status", _no_net)
    calls = {}

    def fake_q(self, scan_mode="all", limit=10, dry_run=False, rotation=None):
        calls["quarantine"] = {"scan_mode": scan_mode, "limit": limit, "dry_run": dry_run,
                               "rotation": None if rotation is None else rotation.path.name,
                               "delays": (self.min_delay, self.max_delay)}
        return {"scanned": 0}

    def fake_r(self, limit=50, dry_run=False):
        calls["revival"] = {"limit": limit}
        return {"revived": 0}
    monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "run_quarantine", fake_q)
    monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "run_revival", fake_r)
    return tmp_path, calls


def _run(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["05.02", *argv])
    return MOD.main()


class TestMainSweepValves:
    def test_40_sweep_passes_guard_with_defaults(self, env, monkeypatch):
        _, calls = env
        _run(monkeypatch, ["--sweep"])
        q = calls["quarantine"]
        assert q["limit"] == 10 and q["scan_mode"] == "first_n" and q["rotation"] == CKPT
        assert q["delays"] == (60.0, 300.0) and "revival" not in calls

    def test_41_sweep_rejects_mode_all(self, env, monkeypatch, capsys):
        with pytest.raises(SystemExit) as e:
            _run(monkeypatch, ["--sweep", "-m", "all"])
        assert e.value.code == 1 and "Q-21" in capsys.readouterr().out and "quarantine" not in env[1]

    @pytest.mark.parametrize("bad", ["0", "21", "-3"])
    def test_42_sweep_caps_limit_at_20(self, env, monkeypatch, capsys, bad):
        with pytest.raises(SystemExit) as e:
            _run(monkeypatch, ["--sweep", "-l", bad])
        assert e.value.code == 1 and "Q-24" in capsys.readouterr().out

    def test_43_sweep_accepts_limit_20_and_random(self, env, monkeypatch):
        _, calls = env
        _run(monkeypatch, ["--sweep", "-l", "20", "-m", "random"])
        assert calls["quarantine"]["limit"] == 20 and calls["quarantine"]["scan_mode"] == "random"

    def test_44_sweep_and_revive_refused(self, env, monkeypatch, capsys):
        with pytest.raises(SystemExit) as e:
            _run(monkeypatch, ["--sweep", "--revive"])
        assert e.value.code == 1 and "MAINT-6" in capsys.readouterr().out

    def test_45_legacy_paths_unchanged(self, env, monkeypatch):
        _, calls = env
        _run(monkeypatch, ["--allow-primary-scan"])
        q = calls["quarantine"]
        assert q["limit"] == 10 and q["scan_mode"] == "all" and q["rotation"] is None and q["delays"] == (10.0, 60.0)
        with pytest.raises(SystemExit):
            _run(monkeypatch, [])                                             # Q-14 guard still bites
        _run(monkeypatch, ["--revive"])
        assert calls["revival"]["limit"] == 0

    def test_46_sweep_busy_lock_exits_1(self, env, monkeypatch):
        def busy(self, **kw):
            return {"error": "vault_lock_busy", "scanned": 0}
        monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "run_quarantine", busy)
        with pytest.raises(SystemExit) as e:
            _run(monkeypatch, ["--sweep"])
        assert e.value.code == 1


# ─────────────────────────────────────────────────────────────────────────────
# 6) source / repo contracts
# ─────────────────────────────────────────────────────────────────────────────
class TestContracts:
    def test_50_gitignore_covers_checkpoint(self):
        r = subprocess.run(["git", "check-ignore", "-q", CKPT], cwd=ROOT, capture_output=True)
        assert r.returncode == 0

    def test_51_checkpoint_class_beside_engine_and_helper_dry(self):
        assert SRC.index("class RotationCheckpoint") < SRC.index("class MasterDelayedGiftsManager")
        rq = inspect.getsource(MOD.MasterDelayedGiftsManager.run_quarantine)
        assert rq.count("_activate_for_bot31(") == 1 and "rotation.mark(" in rq and "_with_vault_lock(" in rq
        assert "allow_primary" not in rq
        assert SRC.count('"cooldown_released_at"') == 1

    def test_52_config_values_match_owner_decisions(self):
        c = MOD.Config
        assert (c.SWEEP_BATCH_SIZE, c.SWEEP_MAX_BATCH, c.SWEEP_SCAN_MODE) == (10, 20, "first_n")
        assert (c.SWEEP_MIN_DELAY, c.SWEEP_MAX_DELAY) == (60.0, 300.0)
        assert c.ROTATION_CHECKPOINT_FILE == CKPT and (c.MIN_DELAY, c.MAX_DELAY) == (10.0, 60.0)

    def test_53_lf_only_and_no_id_tracking(self):
        assert b"\r" not in MANAGER_FILE.read_bytes()
        assert '"id"' not in SRC

    def test_54_bridge_untouched(self):
        """01.33 must stay byte-identical to the MAINT-5 baseline (owner red line)."""
        assert hashlib.sha256(BRIDGE_FILE.read_bytes()).hexdigest().startswith("8728ac134b037f9d")
