"""
P57 — MAINT-7 (owner card REVIEW_AND_CONDITIONAL_EXECUTE 2026-11-03, Gist b6ba8643…, voices 135–137; D49–D54):
``bridge_refactor/main_upgrade.py`` — additive Process Supervisor beside ``main.py``. main.py / 01.33 untouched.

What is verified (offline, no network, no Telegram, no Genspark; children are tiny python stubs):
  * D49/D51  file location + absolute, dynamic SCRIPT_DIR/ROOT_DIR via pathlib; stdlib-only imports.
  * D52      bot child = [sys.executable, SCRIPT_DIR/main.py] cwd=SCRIPT_DIR; engine child cwd=ROOT_DIR with
             stdout+stderr redirected to logs/scheduler_0502.log (nothing on the supervisor's stdout).
  * D54      exact 05.02 argv for sweep/revive (``--revive`` carries ``-q accounts_cooldown.json`` — 7.11/D16/D17)
             and the four fixed slots; each slot fires once per day; overlapping job is skipped, never doubled.
  * D53      SIGINT/SIGTERM => children terminated and reaped (no zombie), bot exit => supervisor exits with same rc.
  * D50      main.py + 01.33 byte-identical to baseline hashes; no existing bridge_refactor file modified.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
SUP_FILE = ROOT / "bridge_refactor" / "main_upgrade.py"
ALLOWED_IMPORTS = {"atexit", "logging", "pathlib", "signal", "subprocess", "sys", "time", "__future__"}


def _load(path: Path = SUP_FILE):
    spec = importlib.util.spec_from_file_location(f"main_upgrade_{abs(hash(path))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load()
SRC = SUP_FILE.read_text(encoding="utf-8")

BOT_STUB = textwrap.dedent("""
    import os, sys, time, json, signal
    marker = sys.argv[1] if len(sys.argv) > 1 else "bot_marker.json"
    with open(marker, "w", encoding="utf-8") as f:
        json.dump({"cwd": os.getcwd(), "pid": os.getpid(), "argv": sys.argv}, f)
    rc = int(os.environ.get("STUB_EXIT_AFTER_RC", "-1"))
    t_exit = float(os.environ.get("STUB_EXIT_AFTER_S", "0"))
    t0 = time.time()
    while True:
        if t_exit and time.time() - t0 > t_exit:
            sys.exit(rc)
        time.sleep(0.05)
""")

ENGINE_STUB = textwrap.dedent("""
    import os, sys, time, json
    print("ENGINE_STDOUT", json.dumps({"cwd": os.getcwd(), "argv": sys.argv[1:]}))
    print("ENGINE_STDERR", file=sys.stderr)
    sys.stdout.flush(); sys.stderr.flush()
    time.sleep(float(os.environ.get("ENGINE_SLEEP_S", "0.2")))
    sys.exit(int(os.environ.get("ENGINE_RC", "0")))
""")


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """A fake project tree: tmp/bridge_refactor/main.py (stub) + tmp/05.02 (stub); module paths re-pointed."""
    br = tmp_path / "bridge_refactor"
    br.mkdir()
    (br / "main.py").write_text(BOT_STUB, encoding="utf-8")
    (tmp_path / "05.02_genspark_delayed_gifts_manager.py").write_text(ENGINE_STUB, encoding="utf-8")
    (tmp_path / "accounts_genspark.json").write_text("[]", encoding="utf-8")
    mod = _load()
    monkeypatch.setattr(mod, "SCRIPT_DIR", br)
    monkeypatch.setattr(mod, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(mod, "BOT_MAIN_PY", br / "main.py")
    monkeypatch.setattr(mod, "ENGINE_0502", tmp_path / "05.02_genspark_delayed_gifts_manager.py")
    monkeypatch.setattr(mod, "ACCOUNTS_FILE", tmp_path / "accounts_genspark.json")
    monkeypatch.setattr(mod, "COOLDOWN_VAULT", tmp_path / "accounts_cooldown.json")
    monkeypatch.setattr(mod, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(mod, "TERMINATE_GRACE_S", 2.0)
    monkeypatch.chdir(tmp_path / "logs" if (tmp_path / "logs").exists() else tmp_path)
    return mod, tmp_path


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # on POSIX a zombie still answers kill(0); check /proc state when available
    st = Path(f"/proc/{pid}/stat")
    if st.exists():
        try:
            return st.read_text().split(")")[-1].split()[0] != "Z"
        except Exception:
            return True
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 1) static contracts (D49/D50/D51/LIMITS)
# ─────────────────────────────────────────────────────────────────────────────
class TestStaticContracts:
    def test_01_location_and_neighbour(self):
        assert SUP_FILE.exists() and (SUP_FILE.parent / "main.py").exists()
        assert SUP_FILE.parent.name == "bridge_refactor"

    def test_02_stdlib_only_imports(self):
        import ast
        tree = ast.parse(SRC)
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                names.add((n.module or "").split(".")[0])
        assert names <= ALLOWED_IMPORTS, names - ALLOWED_IMPORTS

    def test_03_dynamic_paths_and_executable(self):
        assert "pathlib.Path(__file__).resolve().parent" in SRC and "SCRIPT_DIR.parent" in SRC
        assert "sys.executable" in SRC
        assert MOD.SCRIPT_DIR == SUP_FILE.parent and MOD.ROOT_DIR == ROOT
        assert MOD.BOT_MAIN_PY == ROOT / "bridge_refactor" / "main.py"
        assert MOD.ENGINE_0502 == ROOT / "05.02_genspark_delayed_gifts_manager.py"

    def test_04_bot31_and_main_py_untouched(self):
        assert hashlib.sha256((ROOT / "01.33_telegram_gen_bridge.py").read_bytes()).hexdigest().startswith("fe039f0f3f90ac8b")
        assert hashlib.sha256((ROOT / "bridge_refactor" / "main.py").read_bytes()).hexdigest().startswith("d083885a9bb352f6")
        assert "main_upgrade" not in (ROOT / "bridge_refactor" / "main.py").read_text(encoding="utf-8")

    def test_05_lf_only(self):
        assert b"\r" not in SUP_FILE.read_bytes()


# ─────────────────────────────────────────────────────────────────────────────
# 2) D54 schedule + argv (pure functions)
# ─────────────────────────────────────────────────────────────────────────────
class TestSchedule:
    def test_10_slots(self):
        assert MOD.SCHEDULE == ((0, 0, "revive"), (6, 0, "sweep"), (12, 0, "revive"), (18, 0, "sweep"))

    def test_11_sweep_argv(self):
        cmd = MOD.build_job_cmd("sweep")
        assert cmd[0] == sys.executable and cmd[1] == str(MOD.ENGINE_0502)
        assert cmd[2:] == ["--sweep", "-f", str(MOD.ACCOUNTS_FILE), "-l", "10"]

    def test_12_revive_argv_targets_cooldown_vault_only(self):
        """7.11 / D16 / D17: --revive must point -q at accounts_cooldown.json (never the gift quarantine)."""
        cmd = MOD.build_job_cmd("revive")
        assert cmd[2:] == ["--revive", "-q", str(MOD.COOLDOWN_VAULT), "-f", str(MOD.ACCOUNTS_FILE), "-l", "0"]
        assert MOD.COOLDOWN_VAULT.name == "accounts_cooldown.json"
        with pytest.raises(ValueError):
            MOD.build_job_cmd("nope")

    def test_13_due_slot_fires_once_per_day(self):
        fired = set()
        lt = time.struct_time((2026, 11, 3, 6, 0, 15, 1, 307, 0))
        key, kind = MOD.due_slot(lt, fired)
        assert kind == "sweep" and key == (2026, 307, 6, 0)
        fired.add(key)
        assert MOD.due_slot(lt, fired) == (None, None)                      # same minute, already fired
        lt2 = time.struct_time((2026, 11, 3, 6, 1, 0, 1, 307, 0))
        assert MOD.due_slot(lt2, fired) == (None, None)                     # minute passed
        lt3 = time.struct_time((2026, 11, 4, 6, 0, 0, 2, 308, 0))
        assert MOD.due_slot(lt3, fired)[1] == "sweep"                       # next day fires again
        assert MOD.due_slot(time.struct_time((2026, 11, 3, 12, 0, 0, 1, 307, 0)), set())[1] == "revive"
        assert MOD.due_slot(time.struct_time((2026, 11, 3, 0, 0, 0, 1, 307, 0)), set())[1] == "revive"
        assert MOD.due_slot(time.struct_time((2026, 11, 3, 18, 0, 0, 1, 307, 0)), set())[1] == "sweep"
        assert MOD.due_slot(time.struct_time((2026, 11, 3, 9, 30, 0, 1, 307, 0)), set()) == (None, None)

    def test_14_tick_period_below_one_minute(self):
        assert 0 < MOD.TICK_SECONDS < 60 and MOD.SWEEP_BATCH == 10


# ─────────────────────────────────────────────────────────────────────────────
# 3) live launch / teardown with stub children (D52 / D53)
# ─────────────────────────────────────────────────────────────────────────────
class TestLiveProcesses:
    def test_20_bot_launch_cwd_and_teardown_no_zombie(self, sandbox, monkeypatch):
        mod, tmp = sandbox
        sup = mod.Supervisor(with_bot=True)
        bot = sup.start_bot()
        marker = tmp / "bridge_refactor" / "bot_marker.json"
        for _ in range(100):
            if marker.exists():
                break
            time.sleep(0.05)
        info = json.loads(marker.read_text(encoding="utf-8"))
        assert Path(info["cwd"]).resolve() == (tmp / "bridge_refactor").resolve()
        assert bot.poll() is None
        sup.shutdown()
        assert bot.poll() is not None and not _alive(bot.pid)
        sup.shutdown()                                                      # idempotent

    def test_21_engine_runs_in_root_and_logs_to_file(self, sandbox, monkeypatch, capfd):
        mod, tmp = sandbox
        monkeypatch.setenv("ENGINE_SLEEP_S", "0.1")
        sup = mod.Supervisor(with_bot=False)
        assert sup.start_job("sweep") is True
        sup.job.wait(timeout=10)
        sup.reap_job()
        out = capfd.readouterr()
        assert "ENGINE_STDOUT" not in out.out and "ENGINE_STDERR" not in out.err   # screen stays clean (D52)
        log = (tmp / "logs" / "scheduler_0502.log").read_text(encoding="utf-8")
        assert "START sweep" in log and "ENGINE_STDOUT" in log and "ENGINE_STDERR" in log and "END sweep exit=0" in log
        payload = json.loads(log.split("ENGINE_STDOUT ", 1)[1].split("\n", 1)[0])
        assert Path(payload["cwd"]).resolve() == tmp.resolve()
        assert payload["argv"] == ["--sweep", "-f", str(tmp / "accounts_genspark.json"), "-l", "10"]
        assert sup.job is None and sup.job_log is None

    def test_22_overlapping_job_is_skipped_not_doubled(self, sandbox, monkeypatch):
        mod, tmp = sandbox
        monkeypatch.setenv("ENGINE_SLEEP_S", "3")
        sup = mod.Supervisor(with_bot=False)
        assert sup.start_job("sweep") is True
        first = sup.job.pid
        assert sup.start_job("revive") is False and sup.job.pid == first
        sup.shutdown()
        assert not _alive(first)

    def test_23_nonzero_engine_exit_is_logged_and_reaped(self, sandbox, monkeypatch):
        mod, tmp = sandbox
        monkeypatch.setenv("ENGINE_RC", "1")
        monkeypatch.setenv("ENGINE_SLEEP_S", "0.05")
        sup = mod.Supervisor(with_bot=False)
        sup.start_job("revive")
        sup.job.wait(timeout=10)
        sup.tick(time.struct_time((2026, 11, 3, 9, 30, 0, 1, 307, 0)))     # tick reaps, nothing due
        log = (tmp / "logs" / "scheduler_0502.log").read_text(encoding="utf-8")
        assert "END revive exit=1" in log and sup.job is None

    def test_24_tick_launches_due_slot_once(self, sandbox, monkeypatch):
        mod, tmp = sandbox
        monkeypatch.setenv("ENGINE_SLEEP_S", "0.05")
        sup = mod.Supervisor(with_bot=False)
        lt = time.struct_time((2026, 11, 3, 18, 0, 5, 1, 307, 0))
        sup.tick(lt)
        assert sup.job is not None and sup.job_kind == "sweep"
        pid = sup.job.pid
        sup.job.wait(timeout=10)
        sup.tick(lt)                                                        # same minute again => no relaunch
        assert sup.job is None and (2026, 307, 18, 0) in sup.fired
        assert not _alive(pid)

    def test_25_bot_exit_stops_supervisor_with_same_rc(self, sandbox, monkeypatch):
        mod, tmp = sandbox
        monkeypatch.setenv("STUB_EXIT_AFTER_S", "0.3")
        monkeypatch.setenv("STUB_EXIT_AFTER_RC", "7")
        sup = mod.Supervisor(with_bot=True)
        rc = sup.run(tick_seconds=0.05)
        assert rc == 7 and "bot exited rc=7" in sup.stop_reason
        assert sup.bot.poll() == 7

    def test_26_run_now_launches_job_immediately(self, sandbox, monkeypatch):
        mod, tmp = sandbox
        monkeypatch.setenv("ENGINE_SLEEP_S", "0.05")
        monkeypatch.setenv("STUB_EXIT_AFTER_S", "0.5")
        sup = mod.Supervisor(with_bot=True)
        sup.run(run_now="revive", tick_seconds=0.05)
        log = (tmp / "logs" / "scheduler_0502.log").read_text(encoding="utf-8")
        assert "START revive" in log and "END revive exit=0" in log

    @pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX signal delivery")
    def test_27_sigterm_tears_down_children_no_zombie(self, sandbox, monkeypatch):
        """Real signal path: run the supervisor as its own process, SIGTERM it, ensure children die."""
        mod, tmp = sandbox
        env = dict(os.environ, ENGINE_SLEEP_S="30", PYTHONDONTWRITEBYTECODE="1")
        driver = tmp / "driver.py"
        driver.write_text(textwrap.dedent(f"""
            import importlib.util, pathlib, sys, json
            spec = importlib.util.spec_from_file_location("mu", {str(SUP_FILE)!r})
            mu = importlib.util.module_from_spec(spec); spec.loader.exec_module(mu)
            tmp = pathlib.Path({str(tmp)!r})
            mu.SCRIPT_DIR = tmp / "bridge_refactor"; mu.ROOT_DIR = tmp
            mu.BOT_MAIN_PY = mu.SCRIPT_DIR / "main.py"
            mu.ENGINE_0502 = tmp / "05.02_genspark_delayed_gifts_manager.py"
            mu.ACCOUNTS_FILE = tmp / "accounts_genspark.json"; mu.COOLDOWN_VAULT = tmp / "accounts_cooldown.json"
            mu.LOGS_DIR = tmp / "logs"; mu.TERMINATE_GRACE_S = 2.0
            mu._setup_logging()
            sup = mu.Supervisor(with_bot=True)
            import threading, time
            def dump():
                for _ in range(200):
                    if sup.bot is not None and sup.job is not None:
                        (tmp / "pids.json").write_text(json.dumps({{"bot": sup.bot.pid, "job": sup.job.pid}}))
                        return
                    time.sleep(0.05)
            threading.Thread(target=dump, daemon=True).start()
            sys.exit(sup.run(run_now="sweep", tick_seconds=0.05))
        """), encoding="utf-8")
        p = subprocess.Popen([sys.executable, str(driver)], cwd=str(tmp), env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pids_file = tmp / "pids.json"
        for _ in range(200):
            if pids_file.exists():
                break
            time.sleep(0.05)
        pids = json.loads(pids_file.read_text())
        assert _alive(pids["bot"]) and _alive(pids["job"])
        p.send_signal(signal.SIGTERM)
        p.wait(timeout=20)
        time.sleep(0.3)
        assert not _alive(pids["bot"]) and not _alive(pids["job"])
        sup_log = (tmp / "logs" / "main_upgrade.log").read_text(encoding="utf-8")
        assert "signal" in sup_log and "إيقاف" in sup_log


# ─────────────────────────────────────────────────────────────────────────────
# 4) CLI surface
# ─────────────────────────────────────────────────────────────────────────────
class TestCli:
    def test_30_parse_args(self):
        assert MOD.parse_args([]) == {"run_now": None, "with_bot": True, "help": False}
        assert MOD.parse_args(["--run-now", "sweep", "--no-bot"]) == {"run_now": "sweep", "with_bot": False, "help": False}
        with pytest.raises(SystemExit):
            MOD.parse_args(["--bogus"])
        with pytest.raises(SystemExit):
            MOD.parse_args(["--run-now", "all"])

    def test_31_help_exits_zero_without_processes(self, capsys):
        assert MOD.main(["--help"]) == 0
        assert "main_upgrade" in capsys.readouterr().out

    def test_32_missing_engine_exits_2(self, sandbox, monkeypatch):
        mod, tmp = sandbox
        (tmp / "05.02_genspark_delayed_gifts_manager.py").unlink()
        assert mod.main(["--no-bot"]) == 2
