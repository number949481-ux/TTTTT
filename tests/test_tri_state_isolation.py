"""
Isolated test pack for the tri-state gift / quarantine engine
(05.02_genspark_delayed_gifts_manager.py).

Coverage required by owner GO (Step 1):
  Fresh, Grace, Stale, Banned, Network Error
plus Cut & Move routing and the atomic-save helpers.

Isolation guarantees:
  * No network: ``socket.socket`` raises for any attempt.
  * The missing ``genspark_master_account_manager`` module is stubbed in
    ``sys.modules`` before loading the manager file.
  * Every external call (get_session / check_account_balance / do_b2c_login /
    ensure_data_retention_enabled) is monkeypatched per test.
  * All JSON files live in ``tmp_path``; no repo file is touched.
  * ``time.sleep`` and ``random.uniform`` are neutralised.
"""
from __future__ import annotations

import importlib.util
import json
import socket
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANAGER_FILE = ROOT / "05.02_genspark_delayed_gifts_manager.py"
THRESHOLD = 14


# ─────────────────────────────────────────────────────────────────────────────
# Loading the module under test without network / without the real master
# ─────────────────────────────────────────────────────────────────────────────
class _NoNetworkSocket:
    def __init__(self, *a, **k):
        raise RuntimeError("network access is forbidden inside the isolation pack")


def _load_manager_module():
    stub = types.ModuleType("genspark_master_account_manager")

    def do_b2c_login(email, password, timeout=45):  # pragma: no cover - replaced per test
        raise RuntimeError("do_b2c_login stub must be monkeypatched")

    def get_session():  # pragma: no cover - replaced per test
        raise RuntimeError("get_session stub must be monkeypatched")

    def check_account_balance(cookies):  # pragma: no cover - replaced per test
        raise RuntimeError("check_account_balance stub must be monkeypatched")

    stub.do_b2c_login = do_b2c_login
    stub.get_session = get_session
    stub.check_account_balance = check_account_balance
    sys.modules.setdefault("genspark_master_account_manager", stub)

    spec = importlib.util.spec_from_file_location("tri_state_manager_under_test", MANAGER_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MOD = _load_manager_module()


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _NoNetworkSocket)
    monkeypatch.setattr(MOD.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(MOD.random, "uniform", lambda a, b: 0.0)
    yield


# ─────────────────────────────────────────────────────────────────────────────
# Fakes
# ─────────────────────────────────────────────────────────────────────────────
class FakeResponse:
    def __init__(self, status_code=200, body=None, raise_on_json=False):
        self.status_code = status_code
        self._body = body if body is not None else {}
        self._raise_on_json = raise_on_json
        self.text = json.dumps(self._body, ensure_ascii=False) if not raise_on_json else "<html>"

    def json(self):
        if self._raise_on_json:
            raise ValueError("malformed json")
        return self._body


class FakeCookieJar:
    def __init__(self):
        self.store = []

    def set(self, k, v, domain=None):
        self.store.append((k, v, domain))


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.headers = {}
        self.cookies = FakeCookieJar()
        self._response = response
        self._exc = exc
        self.calls = []

    def get(self, url, **kw):
        self.calls.append((url, kw))
        if self._exc is not None:
            raise self._exc
        return self._response


def _gift_body(gift_times):
    recs = [{"credit_type": "daily_gift", "ctime": t, "amount": 100} for t in gift_times]
    recs.append({"credit_type": "purchase", "ctime": "2020-01-01T00:00:00Z", "amount": 9999})
    return {"status": 0, "list": recs}


def _iso_days_ago(days, hours=0):
    dt = datetime.now(timezone.utc) - timedelta(days=days, hours=hours)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_manager(tmp_path, **overrides):
    kwargs = dict(
        primary_path=tmp_path / "accounts_genspark.json",
        success_path=tmp_path / "accounts_success.json",
        quarantine_path=tmp_path / "accounts_delayed_gifts_credits.json",
        failed_path=tmp_path / "accounts_failed.json",
        dead_path=tmp_path / "dead_accounts.json",
        threshold_days=THRESHOLD,
        min_delay=0.0,
        max_delay=0.0,
    )
    kwargs.update(overrides)
    return MOD.MasterDelayedGiftsManager(**kwargs)


def wire(monkeypatch, balance=(120, "active", None), b2c=None, session=None):
    """Patch all externals of check_account_status.

    balance: tuple returned by check_account_balance, or a callable(cookies).
    b2c:     None -> must not be called; tuple -> constant; callable -> per call.
    session: FakeSession returned by get_session (default: healthy empty body).
    """
    sess = session if session is not None else FakeSession(FakeResponse(200, _gift_body([_iso_days_ago(1)])))
    b2c_calls = []

    def _balance(cookies):
        return balance(cookies) if callable(balance) else balance

    def _b2c(email, password, timeout=45):
        b2c_calls.append((email, password))
        if b2c is None:
            raise AssertionError("do_b2c_login must not be called in this scenario")
        return b2c(len(b2c_calls)) if callable(b2c) else b2c

    monkeypatch.setattr(MOD, "get_session", lambda: sess)
    monkeypatch.setattr(MOD, "check_account_balance", _balance)
    monkeypatch.setattr(MOD, "ensure_data_retention_enabled", lambda s, c: (True, "enabled"))
    monkeypatch.setattr(MOD, "do_b2c_login", _b2c)
    return sess, b2c_calls


def account(**over):
    base = {"email": "user@example.com", "password": "pw", "cookies": {"session_id": "abc"}, "balance": None}
    base.update(over)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# 1) FRESH — gift received recently
# ─────────────────────────────────────────────────────────────────────────────
class TestFresh:
    def test_fresh_gift_yesterday_is_healthy(self, tmp_path, monkeypatch):
        sess, _ = wire(monkeypatch, session=FakeSession(FakeResponse(200, _gift_body([_iso_days_ago(1)]))))
        mgr = make_manager(tmp_path)
        acc = account()
        status, days, diag, bal, raw = mgr.check_account_status(acc)
        assert status == "HEALTHY"
        assert days in (0, 1)
        assert bal == 120
        assert raw["credit_type"] == "daily_gift"
        assert acc["balance"] == 120
        assert acc["days_without_gift"] == days
        assert "last_checked" in acc
        assert "recharge_logs" in sess.calls[0][0]

    def test_fresh_picks_latest_gift_not_first_in_list(self, tmp_path, monkeypatch):
        body = _gift_body([_iso_days_ago(30), _iso_days_ago(2), _iso_days_ago(20)])
        wire(monkeypatch, session=FakeSession(FakeResponse(200, body)))
        mgr = make_manager(tmp_path)
        status, days, *_ = mgr.check_account_status(account())
        assert status == "HEALTHY"
        assert days == 2


# ─────────────────────────────────────────────────────────────────────────────
# 2) GRACE — approaching but below threshold; boundary at threshold
# ─────────────────────────────────────────────────────────────────────────────
class TestGrace:
    def test_grace_13_days_is_still_healthy(self, tmp_path, monkeypatch):
        wire(monkeypatch, session=FakeSession(FakeResponse(200, _gift_body([_iso_days_ago(13, hours=1)]))))
        status, days, *_ = make_manager(tmp_path).check_account_status(account())
        assert status == "HEALTHY"
        assert days == 13

    def test_grace_boundary_exact_14_days_is_stale(self, tmp_path, monkeypatch):
        # Owner decision: threshold is inclusive (>= 14) as implemented at 05.02:408.
        wire(monkeypatch, session=FakeSession(FakeResponse(200, _gift_body([_iso_days_ago(14, hours=1)]))))
        status, days, *_ = make_manager(tmp_path).check_account_status(account())
        assert days == 14
        assert status == "STALE"

    def test_grace_respects_custom_threshold(self, tmp_path, monkeypatch):
        wire(monkeypatch, session=FakeSession(FakeResponse(200, _gift_body([_iso_days_ago(10, hours=1)]))))
        mgr = make_manager(tmp_path, threshold_days=7)
        status, days, *_ = mgr.check_account_status(account())
        assert days == 10
        assert status == "STALE"


# ─────────────────────────────────────────────────────────────────────────────
# 3) STALE — gift too old, missing, or unparseable
# ─────────────────────────────────────────────────────────────────────────────
class TestStale:
    def test_stale_20_days(self, tmp_path, monkeypatch):
        wire(monkeypatch, session=FakeSession(FakeResponse(200, _gift_body([_iso_days_ago(20, hours=1)]))))
        acc = account()
        status, days, diag, bal, raw = make_manager(tmp_path).check_account_status(acc)
        assert status == "STALE"
        assert days == 20
        assert bal == 120
        assert acc["days_without_gift"] == 20
        assert raw["credit_type"] == "daily_gift"

    def test_stale_no_daily_gift_in_60_days_is_999(self, tmp_path, monkeypatch):
        body = {"status": 0, "list": [{"credit_type": "purchase", "ctime": _iso_days_ago(1)}]}
        wire(monkeypatch, session=FakeSession(FakeResponse(200, body)))
        acc = account()
        status, days, diag, bal, raw = make_manager(tmp_path).check_account_status(acc)
        assert status == "STALE"
        assert days == 999
        assert raw is None
        assert acc["days_without_gift"] == 999

    def test_stale_unparseable_gift_date_is_999(self, tmp_path, monkeypatch):
        body = {"status": 0, "list": [{"credit_type": "daily_gift", "ctime": "not-a-date"}]}
        wire(monkeypatch, session=FakeSession(FakeResponse(200, body)))
        acc = account()
        status, days, diag, bal, raw = make_manager(tmp_path).check_account_status(acc)
        assert status == "STALE"
        assert days == 999
        assert raw["ctime"] == "not-a-date"
        assert acc["days_without_gift"] == 999


# ─────────────────────────────────────────────────────────────────────────────
# 4) BANNED / DEAD
# ─────────────────────────────────────────────────────────────────────────────
class TestBanned:
    @pytest.mark.parametrize("auth", ["suspended", "user_not_found"])
    def test_banned_on_balance_check_is_dead_without_b2c(self, tmp_path, monkeypatch, auth):
        sess, b2c_calls = wire(monkeypatch, balance=(0, auth, None), b2c=None)
        status, days, diag, bal, raw = make_manager(tmp_path).check_account_status(account())
        assert status == "DEAD"
        assert days == 0 and bal == 0
        assert raw == {"reason": auth}
        assert b2c_calls == []
        assert sess.calls == []  # gift log never queried

    @pytest.mark.parametrize("b2c_status", ["invalid_credentials", "suspended", "domain_banned"])
    def test_banned_after_b2c_relogin_is_dead(self, tmp_path, monkeypatch, b2c_status):
        sess, b2c_calls = wire(monkeypatch, balance=(0, "expired", None), b2c=(None, b2c_status))
        status, days, diag, bal, raw = make_manager(tmp_path).check_account_status(account())
        assert status == "DEAD"
        assert raw == {"reason": b2c_status}
        assert len(b2c_calls) == 1
        assert sess.calls == []

    def test_expired_session_without_password_is_dead(self, tmp_path, monkeypatch):
        sess, b2c_calls = wire(monkeypatch, balance=(0, "expired", None), b2c=None)
        status, days, diag, bal, raw = make_manager(tmp_path).check_account_status(account(password=""))
        assert status == "DEAD"
        assert raw == {"reason": "expired_session_no_password"}
        assert b2c_calls == []

    def test_relogin_success_refreshes_cookies_and_continues(self, tmp_path, monkeypatch):
        new_cookies = {"session_id": "fresh"}

        def balance(cookies):
            return (300, "active", None) if cookies == new_cookies else (0, "expired", None)

        sess, b2c_calls = wire(monkeypatch, balance=balance, b2c=(new_cookies, "active"),
                               session=FakeSession(FakeResponse(200, _gift_body([_iso_days_ago(1)]))))
        acc = account()
        status, days, diag, bal, raw = make_manager(tmp_path).check_account_status(acc)
        assert status == "HEALTHY"
        assert bal == 300
        assert acc["cookies"] == new_cookies
        assert len(b2c_calls) == 1
        assert ("session_id", "fresh", ".genspark.ai") in sess.cookies.store


# ─────────────────────────────────────────────────────────────────────────────
# 5) NETWORK ERROR — transient faults must never be classified DEAD/STALE
# ─────────────────────────────────────────────────────────────────────────────
class TestNetworkError:
    def test_b2c_network_error_retries_once_then_auth_failed(self, tmp_path, monkeypatch):
        sess, b2c_calls = wire(monkeypatch, balance=(0, "expired", None), b2c=(None, "network_error_timeout"))
        acc = account()
        status, days, diag, bal, raw = make_manager(tmp_path).check_account_status(acc)
        assert status == "AUTH_FAILED"
        assert days is None and raw is None
        assert len(b2c_calls) == 2  # exactly one retry
        assert sess.calls == []
        assert "days_without_gift" not in acc

    def test_b2c_recovers_on_second_attempt(self, tmp_path, monkeypatch):
        new_cookies = {"session_id": "fresh"}

        def balance(cookies):
            return (50, "active", None) if cookies == new_cookies else (0, "expired", None)

        def b2c(n):
            return (None, "network_error") if n == 1 else (new_cookies, "active")

        _, b2c_calls = wire(monkeypatch, balance=balance, b2c=b2c)
        status, days, diag, bal, raw = make_manager(tmp_path).check_account_status(account())
        assert status == "HEALTHY"
        assert bal == 50
        assert len(b2c_calls) == 2

    def test_connection_error_on_gift_log_is_auth_failed(self, tmp_path, monkeypatch):
        sess = FakeSession(exc=ConnectionError("boom"))
        wire(monkeypatch, session=sess)
        acc = account()
        status, days, diag, bal, raw = make_manager(tmp_path).check_account_status(acc)
        assert status == "AUTH_FAILED"
        assert days is None and raw is None
        assert bal == 120  # balance already known, preserved
        assert "days_without_gift" not in acc
        assert len(sess.calls) == 1

    @pytest.mark.parametrize("code", [502, 503, 504, 429, 401])
    def test_http_error_on_gift_log_is_auth_failed(self, tmp_path, monkeypatch, code):
        wire(monkeypatch, session=FakeSession(FakeResponse(code, {})))
        acc = account()
        status, days, *_ = make_manager(tmp_path).check_account_status(acc)
        assert status == "AUTH_FAILED"
        assert days is None
        assert "days_without_gift" not in acc

    def test_api_status_nonzero_is_auth_failed(self, tmp_path, monkeypatch):
        wire(monkeypatch, session=FakeSession(FakeResponse(200, {"status": 1, "msg": "rate limited"})))
        status, days, *_ = make_manager(tmp_path).check_account_status(account())
        assert status == "AUTH_FAILED"
        assert days is None

    def test_malformed_json_is_auth_failed(self, tmp_path, monkeypatch):
        wire(monkeypatch, session=FakeSession(FakeResponse(200, raise_on_json=True)))
        status, days, *_ = make_manager(tmp_path).check_account_status(account())
        assert status == "AUTH_FAILED"
        assert days is None


# ─────────────────────────────────────────────────────────────────────────────
# 6) ROUTING — Cut & Move into the three files
# ─────────────────────────────────────────────────────────────────────────────
def _route_by_email(monkeypatch, table):
    """Replace check_account_status with a lookup table: email -> 5-tuple."""

    def fake(self, acc):
        res = table[acc["email"]]
        acc["balance"] = res[3]
        return res

    monkeypatch.setattr(MOD.MasterDelayedGiftsManager, "check_account_status", fake)
    monkeypatch.setattr(MOD.Config, "AUTO_BACKUP", False)


def _read(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


ROUTE_TABLE = {
    "fresh@x.com": ("HEALTHY", 1, "2026-10-29  10:00:00 AM", 150, {"credit_type": "daily_gift"}),
    "stale@x.com": ("STALE", 20, "2026-10-09  10:00:00 AM", 80, {"credit_type": "daily_gift"}),
    "banned@x.com": ("DEAD", 0, "حساب معلق (suspended)", 0, {"reason": "suspended"}),
    "net@x.com": ("AUTH_FAILED", None, "فشل مصادقة (network_error)", 0, None),
}


def _seed_primary(mgr, emails=None):
    emails = emails or list(ROUTE_TABLE)
    MOD.atomic_save_json(mgr.primary_path, [account(email=e) for e in emails])


class TestRouting:
    def test_four_way_routing_result_and_files(self, tmp_path, monkeypatch):
        _route_by_email(monkeypatch, ROUTE_TABLE)
        mgr = make_manager(tmp_path)
        _seed_primary(mgr)
        result = mgr.run_quarantine()
        assert result == {"scanned": 4, "healthy": 1, "stale_cut": 1, "dead_cut": 1,
                          "auth_failed": 1, "total_credits": 150}

        primary = {a["email"] for a in _read(mgr.primary_path)}
        assert primary == {"fresh@x.com", "net@x.com"}  # stale+dead cut; AUTH_FAILED untouched

        success = _read(mgr.success_path)
        assert [a["email"] for a in success] == ["fresh@x.com"]
        assert success[0]["balance"] == 150

        quarantine = _read(mgr.quarantine_path)
        assert [a["email"] for a in quarantine] == ["stale@x.com"]
        qi = quarantine[0]["quarantine_info"]
        assert qi["reason"] == "stale_daily_gift"
        assert qi["days_without_gift"] == 20
        assert qi["threshold_applied"] == THRESHOLD

        failed = _read(mgr.failed_path)
        dead = _read(mgr.dead_path)
        assert [a["email"] for a in failed] == ["banned@x.com"]
        assert [a["email"] for a in dead] == ["banned@x.com"]
        assert failed[0]["status"] == "suspended"
        assert failed[0]["failure_reason"] == "حساب معلق (suspended)"

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        _route_by_email(monkeypatch, ROUTE_TABLE)
        mgr = make_manager(tmp_path)
        _seed_primary(mgr)
        before = mgr.primary_path.read_bytes()
        result = mgr.run_quarantine(dry_run=True)
        assert result["scanned"] == 4
        assert mgr.primary_path.read_bytes() == before
        for p in (mgr.success_path, mgr.quarantine_path, mgr.failed_path, mgr.dead_path):
            assert not p.exists()

    def test_already_classified_accounts_are_skipped(self, tmp_path, monkeypatch):
        _route_by_email(monkeypatch, ROUTE_TABLE)
        mgr = make_manager(tmp_path)
        _seed_primary(mgr)
        MOD.atomic_save_json(mgr.quarantine_path, [account(email="STALE@x.com")])  # case-insensitive
        MOD.atomic_save_json(mgr.failed_path, [account(email="banned@x.com")])
        result = mgr.run_quarantine()
        assert result["scanned"] == 2
        assert result["stale_cut"] == 0 and result["dead_cut"] == 0

    def test_healthy_sorted_by_balance_desc(self, tmp_path, monkeypatch):
        table = {
            "a@x.com": ("HEALTHY", 1, "t", 10, {}),
            "b@x.com": ("HEALTHY", 1, "t", 500, {}),
            "c@x.com": ("HEALTHY", 1, "t", 70, {}),
        }
        _route_by_email(monkeypatch, table)
        mgr = make_manager(tmp_path)
        _seed_primary(mgr, list(table))
        mgr.run_quarantine()
        assert [a["email"] for a in _read(mgr.success_path)] == ["b@x.com", "c@x.com", "a@x.com"]
        assert [a["email"] for a in _read(mgr.primary_path)] == ["b@x.com", "c@x.com", "a@x.com"]

    def test_empty_primary_returns_error(self, tmp_path, monkeypatch):
        _route_by_email(monkeypatch, ROUTE_TABLE)
        mgr = make_manager(tmp_path)
        assert mgr.run_quarantine() == {"error": "No accounts found"}
        assert not mgr.success_path.exists()


# ─────────────────────────────────────────────────────────────────────────────
# 7) HELPERS — atomic save / load / backup
# ─────────────────────────────────────────────────────────────────────────────
class TestHelpers:
    def test_atomic_save_and_load_roundtrip(self, tmp_path):
        p = tmp_path / "x.json"
        data = [account(email="é@x.com")]
        assert MOD.atomic_save_json(p, data) is True
        assert MOD.load_accounts(p) == data
        assert not list(tmp_path.glob("*.tmp_*"))  # no temp leftovers

    def test_load_accounts_corrupt_and_missing(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        assert MOD.load_accounts(p) == []
        assert MOD.load_accounts(tmp_path / "missing.json") == []

    def test_load_accounts_wrapped_dict(self, tmp_path):
        p = tmp_path / "wrapped.json"
        p.write_text(json.dumps({"accounts": [account()]}), encoding="utf-8")
        assert [a["email"] for a in MOD.load_accounts(p)] == ["user@example.com"]

    def test_create_backup_produces_bak(self, tmp_path):
        p = tmp_path / "accounts_genspark.json"
        p.write_text("[]", encoding="utf-8")
        bak = MOD.create_backup(p)
        assert bak is not None and bak.exists()
        assert bak.name.startswith("accounts_genspark.json.") and bak.suffix == ".bak"
        assert MOD.create_backup(tmp_path / "nope.json") is None
