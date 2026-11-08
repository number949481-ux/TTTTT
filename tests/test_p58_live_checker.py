#!/usr/bin/env python3
"""
tests/test_p58_live_checker.py — MAINT-9 / D62–D70: منظومة فحص وتنشيط الحسابات لايف (بوت 31)
================================================================================================
بلا شبكة، بلا ملفات حقيقية (tmp_path)، الماستر مانجر stub كما p56 L41–44.
يغطي SPEC §7: الداشبورد، is_live_check_running، live_check_remaining، آلة الحالات التسعة،
راية الإيقاف، خُطّافا 05.02 (on_account/stop_flag)، المشغّل (busy/fresh/resume/صيد/خطأ شبكة/429/not-found/القاطع)،
Supervisor (busy ⇒ تخطّ)، وعقود المصدر.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys
import time
import types
import urllib.error
from datetime import datetime, timezone

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIDGE_FILE = ROOT / "01.33_telegram_gen_bridge.py"
MANAGER_FILE = ROOT / "05.02_genspark_delayed_gifts_manager.py"
RUNNER_FILE = ROOT / "bridge_refactor" / "live_account_checker.py"
SUPERVISOR_FILE = ROOT / "bridge_refactor" / "main_upgrade.py"
IGNORE_FILE = ROOT / ".gitignore"


# ── تحميل الوحدات ─────────────────────────────────────────────────────────────
def _stub_master_manager():
    stub = types.ModuleType("genspark_master_account_manager")
    for name in ("do_b2c_login", "get_session", "check_account_balance"):
        setattr(stub, name, lambda *a, _n=name, **k: (_ for _ in ()).throw(RuntimeError(f"{_n} must never run in P58")))
    sys.modules.setdefault("genspark_master_account_manager", stub)


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_stub_master_manager()
BRIDGE = _load(BRIDGE_FILE, "bridge_p58")
GM = _load(MANAGER_FILE, "manager_p58")
RUNNER = _load(RUNNER_FILE, "runner_p58")
SUP = _load(SUPERVISOR_FILE, "supervisor_p58")
BRIDGE_SRC = BRIDGE_FILE.read_text(encoding="utf-8")
RUNNER_SRC = RUNNER_FILE.read_text(encoding="utf-8")

CHAT = 777


def _key(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _accounts(n: int) -> list[dict]:
    return [{"email": f"user{i:02d}@x.com", "password": "pw", "cookies": {"s": "1"}, "balance": 10 * i} for i in range(n)]


def _callbacks(kb: dict) -> list[str]:
    return [b.get("callback_data") for row in kb["inline_keyboard"] for b in row]


@pytest.fixture
def world(tmp_path, monkeypatch):
    """ملف أساسي + مسارات الفحص في tmp_path، وكل إرسال/تعديل تيليجرام وPopen مُسجَّل لا منفَّذ."""
    primary = tmp_path / "accounts_genspark.json"
    primary.write_text(json.dumps(_accounts(5)), encoding="utf-8")
    monkeypatch.setattr(BRIDGE, "get_accounts_file_path", lambda json_path=None: primary)
    calls = {"send": [], "edit": [], "markup": [], "popen": []}
    monkeypatch.setattr(BRIDGE, "send_telegram_message",
                        lambda chat_id, text, reply_markup=None, parse_mode="HTML": calls["send"].append((chat_id, text, reply_markup)) or True)
    monkeypatch.setattr(BRIDGE, "send_telegram_message_detailed",
                        lambda chat_id, text, reply_markup=None, parse_mode="HTML": (calls["send"].append((chat_id, text, reply_markup)) or {"ok": True, "message_id": 4242}))
    monkeypatch.setattr(BRIDGE, "edit_telegram_message_text",
                        lambda chat_id, message_id, text, reply_markup=None, parse_mode="HTML": calls["edit"].append((message_id, text, reply_markup)) or {"ok": True})
    monkeypatch.setattr(BRIDGE, "edit_telegram_message_reply_markup",
                        lambda chat_id, message_id, reply_markup=None: calls["markup"].append((message_id, reply_markup)) or {"ok": True})

    class FakeProc:
        pid = 31337

    def fake_popen(cmd, **kw):
        calls["popen"].append((list(cmd), kw))
        return FakeProc()

    monkeypatch.setattr(BRIDGE.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(BRIDGE, "SCRIPT_DIR", tmp_path / "bot")
    (tmp_path / "bot" / "bridge_refactor").mkdir(parents=True)
    (tmp_path / "bot" / "bridge_refactor" / "live_account_checker.py").write_text("# stub runner\n", encoding="utf-8")
    monkeypatch.setattr(BRIDGE, "LIVE_CHECK_RUNNER", tmp_path / "bot" / "bridge_refactor" / "live_account_checker.py")
    return types.SimpleNamespace(tmp=tmp_path, primary=primary, calls=calls,
                                 busy=tmp_path / "live_check.busy", stop=tmp_path / "live_check.stop",
                                 state=tmp_path / "live_check_state.json", ckpt=tmp_path / "genspark_rotation_checkpoint.json")


def _cb(data: str, message_id: int | None = 99):
    msg_info = {"message_id": message_id} if message_id else {}
    BRIDGE.handle_live_check_callback(CHAT, data, msg_info)


# ══════════════ 1) الداشبورد ══════════════
class TestDashboard:
    def test_01_last_row_is_live_check_alone_primary(self, monkeypatch):
        monkeypatch.setattr(BRIDGE, "list_known_projects", lambda chat_id=None, limit=3: [{"project_key": f"k{i}", "project_name": f"P{i}"} for i in range(5)][:limit])
        kb = BRIDGE.build_dashboard_keyboard(CHAT)
        last = kb["inline_keyboard"][-1]
        assert len(last) == 1 and last[0]["callback_data"] == "cmd:live_check" and last[0]["style"] == "primary"
        assert len([c for c in _callbacks(kb) if c.startswith("proj:")]) == 3   # توافق p27
        assert "cmd:account_pwd_lookup" in _callbacks(kb)                        # توافق p32

    def test_02_nine_callbacks_under_64_bytes(self):
        kbs = [BRIDGE.build_live_check_confirm_keyboard(k) for k in ("fresh", "resume", "reset")]
        kbs += [BRIDGE.build_live_check_choice_keyboard(), BRIDGE.build_live_check_running_keyboard(), BRIDGE.build_live_check_stop_confirm_keyboard()]
        seen = {c for kb in kbs for c in _callbacks(kb)}
        expected = {"lc_go:fresh", "lc_go:resume", "lc_go:reset", "lc_cancel", "lc_pick:resume", "lc_pick:reset", "lc_stop", "lc_stop_yes", "lc_stop_no"}
        assert expected <= seen
        assert all(len(c.encode()) < 64 for c in seen)

    def test_03_confirm_keyboard_green_red_styles(self):
        kb = BRIDGE.build_live_check_confirm_keyboard("resume")
        flat = [b for r in kb["inline_keyboard"] for b in r]
        assert flat[0]["style"] == "success" and flat[0]["callback_data"] == "lc_go:resume"
        assert flat[1]["style"] == "danger" and flat[1]["callback_data"] == "lc_cancel"
        assert BRIDGE.build_live_check_confirm_keyboard("bogus")["inline_keyboard"][0][0]["callback_data"] == "lc_go:fresh"

    def test_04_prompt_texts_bounded(self):
        snap = {"total": 85, "checked": 20, "remaining": 65, "counters": {"checked": 20, "total": 85}, "started_at": "x"}
        for kind in ("running", "choice", "fresh", "resume", "reset", "stop_confirm", "stop_ack", "cancelled", "none"):
            t = BRIDGE.render_live_check_prompt_text(kind, snap)
            assert t and len(t) <= 4000
        assert "65" in BRIDGE.render_live_check_prompt_text("choice", snap)
        assert "21" in BRIDGE.render_live_check_prompt_text("resume", snap)


# ══════════════ 2) is_live_check_running / live_check_remaining ══════════════
class TestFileTruth:
    def test_05_running_fresh_busy_true_orphan_false(self, world):
        assert BRIDGE.is_live_check_running() is False
        world.busy.write_text("{}", encoding="utf-8")
        assert BRIDGE.is_live_check_running() is True
        assert BRIDGE.is_live_check_running(now=time.time() + 16 * 60) is False

    def test_06_remaining_counts_and_ignores_orphans(self, world):
        world.ckpt.write_text(json.dumps({"schema": 1, "cycle_no": 3, "checked": [_key("user00@x.com"), _key("user01@x.com"), "deadbeef"]}), encoding="utf-8")
        snap = BRIDGE.live_check_remaining()
        assert snap == {"total": 5, "checked": 2, "remaining": 3, "cycle_no": 3}

    def test_07_remaining_without_checkpoint(self, world):
        assert BRIDGE.live_check_remaining() == {"total": 5, "checked": 0, "remaining": 5, "cycle_no": 1}

    def test_08_key_matches_rotation_checkpoint(self):
        assert _key("  User00@X.com ") == GM.RotationCheckpoint.key("  User00@X.com ") == RUNNER.email_key("  User00@X.com ")


# ══════════════ 3) آلة الحالات ══════════════
class TestStateMachine:
    def test_09_cmd_fresh_when_no_checkpoint(self, world):
        _cb("cmd:live_check")
        _, text, kb = world.calls["send"][-1]
        assert "lc_go:fresh" in _callbacks(kb) and "5" in text
        assert not world.calls["popen"]

    def test_10_cmd_choice_when_partial_cycle(self, world):
        world.ckpt.write_text(json.dumps({"schema": 1, "cycle_no": 1, "checked": [_key("user00@x.com")]}), encoding="utf-8")
        _cb("cmd:live_check")
        _, _, kb = world.calls["send"][-1]
        assert {"lc_pick:resume", "lc_pick:reset", "lc_cancel"} <= set(_callbacks(kb))

    def test_11_cmd_running_info(self, world):
        world.busy.write_text("{}", encoding="utf-8")
        world.state.write_text(json.dumps({"counters": {"checked": 3, "total": 5}, "started_at": "10:00"}), encoding="utf-8")
        _cb("cmd:live_check")
        _, text, kb = world.calls["send"][-1]
        assert "lc_stop" in _callbacks(kb) and "3" in text and "5" in text

    def test_12_pick_edits_in_place_to_confirm(self, world):
        _cb("lc_pick:reset")
        mid, text, kb = world.calls["edit"][-1]
        assert mid == 99 and "lc_go:reset" in _callbacks(kb)
        _cb("lc_pick:resume")
        assert "lc_go:resume" in _callbacks(world.calls["edit"][-1][2])

    def test_13_go_launches_popen_with_argv_after_live_message(self, world):
        _cb("lc_go:resume")
        assert len(world.calls["popen"]) == 1
        cmd, kw = world.calls["popen"][0]
        assert cmd[0] == sys.executable and cmd[1].endswith("live_account_checker.py")
        assert cmd[cmd.index("--chat-id") + 1] == str(CHAT)
        assert cmd[cmd.index("--message-id") + 1] == "4242"       # رسالة اللايف أُرسلت أولاً
        assert cmd[cmd.index("--mode") + 1] == "resume"
        assert kw["cwd"] == str(world.tmp / "bot") and kw["stderr"] == BRIDGE.subprocess.STDOUT
        assert world.calls["markup"] and world.calls["markup"][-1] == (99, None)   # أزرار التأكيد أُزيلت

    def test_14_go_reset_and_fresh_map_to_fresh_mode(self, world):
        _cb("lc_go:reset")
        _cb("lc_go:fresh")
        modes = [c[c.index("--mode") + 1] for c, _ in world.calls["popen"]]
        assert modes == ["fresh", "fresh"]

    def test_15_go_refused_when_running(self, world):
        world.busy.write_text("{}", encoding="utf-8")
        _cb("lc_go:fresh")
        assert not world.calls["popen"]
        assert "يعمل بالفعل" in world.calls["send"][-1][1]

    def test_16_stop_sends_new_confirm_message_not_edit(self, world):
        world.busy.write_text("{}", encoding="utf-8")
        before_edits = len(world.calls["edit"])
        _cb("lc_stop")
        assert len(world.calls["edit"]) == before_edits                      # Q-GO-5
        _, _, kb = world.calls["send"][-1]
        assert set(_callbacks(kb)) == {"lc_stop_yes", "lc_stop_no"}
        assert not world.stop.exists()

    def test_17_stop_yes_writes_flag_stop_no_does_not(self, world):
        world.busy.write_text("{}", encoding="utf-8")
        _cb("lc_stop_no")
        assert not world.stop.exists()
        _cb("lc_stop_yes")
        assert world.stop.exists() and json.loads(world.stop.read_text())["by"] == "bot31"

    def test_18_stop_when_idle_is_polite(self, world):
        _cb("lc_stop")
        assert "لا يوجد" in world.calls["send"][-1][1]
        _cb("lc_stop_yes")
        assert "انتهى" in world.calls["edit"][-1][1]

    def test_19_cancel_returns_dashboard(self, world, monkeypatch):
        monkeypatch.setattr(BRIDGE, "get_main_keyboard", lambda chat_id=None: {"inline_keyboard": [[{"text": "d", "callback_data": "cmd:show_dashboard"}]]})
        _cb("lc_cancel")
        assert "cmd:show_dashboard" in _callbacks(world.calls["send"][-1][2])

    def test_20_dispatcher_routes_lc_block_before_main_chain(self, world, monkeypatch):
        monkeypatch.setattr(BRIDGE, "is_chat_allowed", lambda *a, **k: True)
        hits = []
        monkeypatch.setattr(BRIDGE, "handle_live_check_callback", lambda chat_id, data, msg_info: hits.append(data))
        for data in ("cmd:live_check", "lc_stop", "lc_go:fresh"):
            BRIDGE.handle_telegram_update({"callback_query": {"data": data, "message": {"chat": {"id": CHAT}, "message_id": 1}, "from": {"id": CHAT}}})
        assert hits == ["cmd:live_check", "lc_stop", "lc_go:fresh"]


# ══════════════ 4) خُطّافا 05.02 ══════════════
class TestManagerHooks:
    @pytest.fixture
    def mgr(self, tmp_path, monkeypatch):
        primary = tmp_path / "accounts_genspark.json"
        primary.write_text(json.dumps(_accounts(3)), encoding="utf-8")
        m = GM.MasterDelayedGiftsManager(primary, tmp_path / "q.json", tmp_path / "f.json", tmp_path / "d.json", min_delay=0.0, max_delay=0.0)
        statuses = iter(["HEALTHY", "STALE", "AUTH_FAILED"])
        monkeypatch.setattr(m, "check_account_status", lambda acc: (next(statuses), 1, "diag", 150, None))
        monkeypatch.setattr(GM, "IS_RUNNING", True)
        return types.SimpleNamespace(m=m, tmp=tmp_path, primary=primary)

    def test_21_signature_defaults_none_cli_untouched(self):
        import inspect
        sig = inspect.signature(GM.MasterDelayedGiftsManager.run_quarantine)
        assert sig.parameters["on_account"].default is None and sig.parameters["stop_flag"].default is None

    def test_22_stop_flag_present_stops_before_first_account(self, mgr):
        stop = mgr.tmp / "live_check.stop"
        stop.touch()
        seen = []
        res = mgr.m.run_quarantine(scan_mode="all", dry_run=True, on_account=lambda *a: seen.append(a), stop_flag=stop)
        assert seen == [] and res["scanned"] == 3

    def test_23_on_account_called_once_per_account_after_mark(self, mgr):
        rot = GM.RotationCheckpoint(mgr.tmp / "ckpt.json")
        order = []
        orig_mark = rot.mark

        def spy_mark(email):
            order.append(("mark", email))
            return orig_mark(email)

        rot.mark = spy_mark
        mgr.m.run_quarantine(scan_mode="all", dry_run=False, rotation=rot,
                             on_account=lambda e, s, b, d: order.append(("hook", e, s, b)), stop_flag=mgr.tmp / "nope.stop")
        hooks = [o for o in order if o[0] == "hook"]
        assert len(hooks) == 3 and [h[2] for h in hooks] == ["HEALTHY", "STALE", "AUTH_FAILED"]
        for i, o in enumerate(order):
            if o[0] == "hook":
                assert order[i - 1] == ("mark", o[1])   # الخطاف بعد البصمة مباشرة (بعد الحفظ الذري)

    def test_24_hook_exception_does_not_stop_loop(self, mgr):
        n = []

        def boom(*a):
            n.append(1)
            raise ValueError("hook boom")

        res = mgr.m.run_quarantine(scan_mode="all", dry_run=True, on_account=boom, stop_flag=mgr.tmp / "nope.stop")
        assert len(n) == 3 and res["scanned"] == 3

    def test_25_chunked_sleep_exits_on_stop_flag(self, mgr, monkeypatch):
        stop = mgr.tmp / "live_check.stop"
        mgr.m.min_delay = mgr.m.max_delay = 30.0
        slept = []
        monkeypatch.setattr(GM.time, "sleep", lambda s: slept.append(s) or stop.touch())
        seen = []
        mgr.m.run_quarantine(scan_mode="all", dry_run=True, on_account=lambda *a: seen.append(a), stop_flag=stop)
        assert len(seen) == 1 and slept and all(s <= 1.0 for s in slept)


# ══════════════ 5) المشغّل ══════════════
class FakeTG:
    def __init__(self):
        self.sent, self.edited = [], []
        self.edit_result = (True, "")
        self.enabled = True

    def send(self, text, reply_markup=None, silent=False):
        self.sent.append((text, reply_markup, silent))
        return 1000 + len(self.sent)

    def edit(self, message_id, text, reply_markup=None):
        self.edited.append((message_id, text, reply_markup))
        return self.edit_result

    def delete(self, message_id):
        return True


@pytest.fixture
def runner(tmp_path, monkeypatch):
    primary = tmp_path / "accounts_genspark.json"
    primary.write_text(json.dumps(_accounts(4)), encoding="utf-8")
    monkeypatch.setattr(RUNNER, "load_gifts_manager", lambda root: GM)
    monkeypatch.setattr(GM, "resolve_file_path", lambda name: tmp_path / name)
    monkeypatch.setattr(RUNNER, "load_bot_token", lambda root, token_file=None: "")
    args = RUNNER.build_parser().parse_args(["--chat-id", str(CHAT), "--message-id", "555", "--mode", "resume", "--root", str(tmp_path)])
    lc = RUNNER.LiveChecker(args)
    lc.tg = FakeTG()
    monkeypatch.setattr(RUNNER.time, "sleep", lambda s: None)
    monkeypatch.setattr(RUNNER, "BREAKER_PAUSE_S", 0.0)   # لا انتظار 10 دقائق حقيقية في الاختبار
    return types.SimpleNamespace(lc=lc, tmp=tmp_path, primary=primary, tg=lc.tg)


class TestRunner:
    def test_26_busy_acquire_fail_fresh_replace_orphan(self, tmp_path):
        busy = tmp_path / "live_check.busy"
        ok, _ = RUNNER.acquire_busy(busy)
        assert ok and json.loads(busy.read_text())["pid"]
        ok2, why = RUNNER.acquire_busy(busy)
        assert not ok2 and "يعمل" in why
        ok3, _ = RUNNER.acquire_busy(busy, now=time.time() + 1000)
        assert ok3

    def test_27_run_returns_busy_when_locked(self, runner):
        (runner.tmp / "live_check.busy").write_text("{}", encoding="utf-8")
        assert runner.lc.run() == RUNNER.EXIT_BUSY
        assert "يعمل بالفعل" in runner.tg.sent[-1][0]

    def test_28_fresh_resets_checkpoint_resume_keeps(self, runner, monkeypatch):
        ck = runner.tmp / GM.Config.ROTATION_CHECKPOINT_FILE
        ck.write_text(json.dumps({"schema": 1, "cycle_no": 2, "checked": [_key("user00@x.com")]}), encoding="utf-8")
        captured = {}

        def fake_rq(self_, **kw):
            captured.update(kw)
            return {"scanned": kw["limit"]}

        monkeypatch.setattr(GM.MasterDelayedGiftsManager, "run_quarantine", fake_rq)
        assert runner.lc.run() == RUNNER.EXIT_OK
        assert captured["limit"] == 3 and captured["scan_mode"] == "first_n" and captured["stop_flag"] == runner.tmp / "live_check.stop"
        q = json.loads((runner.tmp / "live_check_queue.json").read_text())
        assert q["total"] == 3 and all(len(h) == 64 for h in q["order"]) and "@" not in json.dumps(q)
        runner.lc.args.mode = "fresh"
        runner.lc.state["counters"]["checked"] = 0
        assert runner.lc.run() == RUNNER.EXIT_OK
        assert captured["limit"] == 4 and json.loads(ck.read_text())["cycle_no"] == 3

    def test_29_on_account_healthy_hunt_sends_once_and_edits(self, runner):
        runner.lc.state["counters"]["total"] = 4
        runner.lc.on_account("user03@x.com", "HEALTHY", 150, "ok")
        assert len(runner.tg.edited) == 1 and runner.tg.edited[0][0] == 555
        assert len(runner.tg.sent) == 1 and "user03@x.com" in runner.tg.sent[0][0] and runner.tg.sent[0][2] is False
        st = json.loads((runner.tmp / "live_check_state.json").read_text())
        assert st["counters"] == {"checked": 1, "total": 4, "active": 1, "cooldown": 0, "stale": 0, "dead": 0, "net_err": 0, "hunted": 1}
        runner.lc.on_account("user02@x.com", "HEALTHY", 50, "ok")
        assert len(runner.tg.sent) == 1   # لا صيد تحت 100

    def test_30_auth_failed_logs_kept_in_place(self, runner):
        runner.lc.on_account("user01@x.com", "AUTH_FAILED", 0, "net down")
        line = json.loads((runner.tmp / "account_log.jsonl").read_text().splitlines()[-1])
        assert line["event"] == "live_check_net_error" and line["action"] == "kept_in_place" and line["email"] == "user01@x.com"
        assert runner.lc.state["counters"]["net_err"] == 1

    def test_31_edit_not_found_sends_new_message_updates_state(self, runner):
        runner.tg.edit_result = (False, "Bad Request: message to edit not found")
        runner.lc.on_account("user00@x.com", "STALE", 0, "old")
        assert runner.lc.message_id == 1001 and runner.lc.state["message_id"] == 1001

    def test_32_breaker_pause_then_self_stop(self, runner):
        for i in range(5):
            runner.lc.on_account(f"a{i}@x.com", "AUTH_FAILED", 0, "x")
        assert runner.lc.state["breaker_trips"] == 1 and runner.lc.exit_code == RUNNER.EXIT_OK
        assert any("قاطع" in s[0] for s in runner.tg.sent)
        for i in range(10):
            runner.lc.on_account(f"b{i}@x.com", "AUTH_FAILED", 0, "x")
        assert runner.lc.state["breaker_trips"] == 3 and runner.lc.exit_code == RUNNER.EXIT_BREAKER
        assert (runner.tmp / "live_check.stop").exists()

    def test_33_healthy_resets_breaker_streak(self, runner):
        for i in range(4):
            runner.lc.on_account(f"a{i}@x.com", "AUTH_FAILED", 0, "x")
        runner.lc.on_account("ok@x.com", "HEALTHY", 10, "ok")
        assert runner.lc.state["breaker_consecutive"] == 0 and runner.lc.state["breaker_trips"] == 0

    def test_34_telegram_429_sleeps_and_retries_once(self, monkeypatch):
        tg = RUNNER.Telegram("tok", CHAT)
        calls, naps = [], []

        class Resp:
            def __init__(self, body): self.body = body
            def read(self): return json.dumps(self.body).encode()
            def close(self): pass
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def fake_urlopen(req, timeout=0):
            calls.append(req)
            if len(calls) == 1:
                raise urllib.error.HTTPError(req.full_url, 429, "Too Many", {}, Resp({"parameters": {"retry_after": 2}}))
            return Resp({"ok": True, "result": {"message_id": 7}})

        monkeypatch.setattr(RUNNER.urllib.request, "urlopen", fake_urlopen)
        monkeypatch.setattr(RUNNER.time, "sleep", lambda s: naps.append(s))
        assert tg.send("hi") == 7 and len(calls) == 2 and naps == [3.0]

    def test_35_delay_min_below_60_rejected(self):
        assert RUNNER.main(["--chat-id", "1", "--delay-min", "5"]) == RUNNER.EXIT_ERROR

    def test_36_stop_flag_ends_with_exit_stopped(self, runner, monkeypatch):
        def fake_rq(self_, **kw):
            kw["on_account"]("user00@x.com", "HEALTHY", 10, "ok")
            kw["stop_flag"].touch()
            return {"scanned": 1}

        monkeypatch.setattr(GM.MasterDelayedGiftsManager, "run_quarantine", fake_rq)
        assert runner.lc.run() == RUNNER.EXIT_STOPPED
        assert not (runner.tmp / "live_check.busy").exists() and not (runner.tmp / "live_check.stop").exists()


# ══════════════ 6) Supervisor ══════════════
class TestSupervisor:
    def test_37_live_check_busy_fresh_vs_orphan(self, tmp_path):
        p = tmp_path / "live_check.busy"
        assert SUP.live_check_busy(path=p) == (False, "")
        p.write_text("{}", encoding="utf-8")
        busy, why = SUP.live_check_busy(path=p)
        assert busy and "دقيقة" in why
        busy2, why2 = SUP.live_check_busy(now=time.time() + 1000, path=p)
        assert not busy2 and "orphan" in why2

    def test_38_start_job_skipped_when_busy(self, tmp_path, monkeypatch):
        p = tmp_path / "live_check.busy"
        p.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(SUP, "LIVE_BUSY_FILE", p)
        popen_calls = []
        monkeypatch.setattr(SUP.subprocess, "Popen", lambda *a, **k: popen_calls.append(a) or types.SimpleNamespace(pid=1, poll=lambda: None))
        sup = SUP.Supervisor()
        assert sup.start_job("sweep") is False and sup.start_job("revive") is False   # Q-GO-3
        assert popen_calls == []


# ══════════════ 7) عقود المصدر ══════════════
class TestContracts:
    def test_39_bridge_crlf_pure(self):
        data = BRIDGE_FILE.read_bytes()
        assert data.count(b"\n") == data.count(b"\r\n")

    def test_40_runner_stdlib_only_no_bridge_import(self):
        import re
        mods = set(re.findall(r"^(?:import|from)\s+([\w\.]+)", RUNNER_SRC, re.M))
        allowed = {"__future__", "argparse", "datetime", "hashlib", "html", "importlib.util", "json", "os", "pathlib", "sys", "time", "traceback", "urllib.error", "urllib.request"}
        assert mods <= allowed, mods - allowed
        assert "telegram_gen_bridge" not in RUNNER_SRC.replace("01.33", "")  or "import" not in RUNNER_SRC.split("01.33")[0][-20:]
        assert b"\r" not in RUNNER_FILE.read_bytes()

    def test_41_isolated_block_precedes_p25_and_main_chain(self):
        lc = BRIDGE_SRC.index('if data == LIVE_CHECK_CALLBACK or data.startswith("lc_"):')
        p25 = BRIDGE_SRC.index('if data.startswith(("cancel_prompt:", "cancel_exec:", "cancel_abort:")):')
        chain = BRIDGE_SRC.index('if data == "cmd:show_dashboard":')
        assert BRIDGE_SRC.index("def handle_telegram_update(") < lc < p25 < chain

    def test_42_gitignore_covers_live_files(self):
        ig = IGNORE_FILE.read_text(encoding="utf-8")
        for pat in ("live_check_queue.json", "live_check_state.json", "live_check.stop", "*.busy"):
            assert pat in ig

    def test_43_constants_aligned_across_files(self):
        assert BRIDGE.LIVE_CHECK_BUSY_ORPHAN_S == SUP.LIVE_BUSY_ORPHAN_S == RUNNER.BUSY_ORPHAN_S == 900.0
        assert BRIDGE.LIVE_CHECK_BUSY_FILENAME == RUNNER.BUSY_FILE_NAME == SUP.LIVE_BUSY_FILE.name
        assert BRIDGE.LIVE_CHECK_STOP_FILENAME == RUNNER.STOP_FILE_NAME
        assert BRIDGE.LIVE_CHECK_CHECKPOINT_FILENAME == GM.Config.ROTATION_CHECKPOINT_FILE
        assert RUNNER.running_keyboard()["inline_keyboard"][0][0]["callback_data"] == "lc_stop"
