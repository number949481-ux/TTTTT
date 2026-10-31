"""P49 — STEP-3 (Q-F): merge legacy verifier quarantine file into 05.02 ``accounts_failed.json``.

Tests-first contract for ``scripts/merge_legacy_quarantine.py`` (S3-A data contract in PROGRESS.md).

Isolation rules:
  * ``tmp_path`` only — never touches real account files.
  * No network: ``socket.socket`` raises for any attempt.
  * The script is loaded via ``importlib`` and driven through ``main(argv) -> int``.
  * Logging contract (owner decision 2026-10-31): e-mails are printed IN FULL (no masking);
    passwords and cookies must never appear in stdout.
"""

from __future__ import annotations

import importlib.util
import json
import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "merge_legacy_quarantine.py"
MANAGER_FILE = REPO_ROOT / "05.02_genspark_delayed_gifts_manager.py"

LEGACY_NAME = "accounts_genspark_blocked_failed__block_failed.json"
FAILED_NAME = "accounts_failed.json"

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_GUARDED = 3


class _NoNetworkSocket:
    def __init__(self, *a, **k):
        raise RuntimeError("network access is forbidden inside the P49 pack")


def _load_script():
    assert SCRIPT.exists(), f"script missing: {SCRIPT}"
    spec = importlib.util.spec_from_file_location("merge_legacy_quarantine_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mod():
    return _load_script()


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    monkeypatch.setattr(socket, "socket", _NoNetworkSocket)
    yield


# ── sample data ──────────────────────────────────────────────────────────────

def _legacy_rec(email, verdict="suspended_by_verifier", detail="user_suspended", ts="2026-10-20T10:11:12", **extra):
    rec = {
        "email": email,
        "password": "SuperSecretP@ss",
        "status": "suspended",
        "quarantine_verdict": verdict,
        "quarantine_detail": detail,
        "quarantined_at": ts,
        "active": False,
        "balance": 0,
        "cookies": {"session": "COOKIE_SECRET_VALUE"},
    }
    rec.update(extra)
    return rec


def _failed_rec(email, status="dead", removed_at="2026-09-01 08:00:00"):
    return {
        "email": email,
        "status": status,
        "failure_reason": "original_reason",
        "dead_reason": "original_reason",
        "removed_at": removed_at,
    }


def _write(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _baks(path: Path):
    return sorted(path.parent.glob(f"{path.name}.*.bak"))


@pytest.fixture
def files(tmp_path):
    legacy = tmp_path / LEGACY_NAME
    failed = tmp_path / FAILED_NAME
    _write(legacy, [_legacy_rec("Alpha@Example.com"), _legacy_rec("beta@example.com")])
    _write(failed, [_failed_rec("gamma@example.com")])
    return legacy, failed


def _run(mod, legacy, failed, *flags):
    argv = ["--legacy", str(legacy), "--failed", str(failed), *flags]
    return mod.main(argv)


# ── 1–2: dry-run default / apply ─────────────────────────────────────────────

def test_01_dry_run_default_no_write_no_bak(mod, files):
    legacy, failed = files
    before_failed = failed.read_bytes()
    before_legacy = legacy.read_bytes()
    rc = _run(mod, legacy, failed)
    assert rc == EXIT_OK
    assert failed.read_bytes() == before_failed
    assert legacy.read_bytes() == before_legacy
    assert _baks(failed) == [] and _baks(legacy) == []


def test_02_apply_writes_and_creates_bak_for_both(mod, files):
    legacy, failed = files
    rc = _run(mod, legacy, failed, "--apply")
    assert rc == EXIT_OK
    data = _read(failed)
    emails = sorted(r["email"].lower() for r in data)
    assert emails == ["alpha@example.com", "beta@example.com", "gamma@example.com"]
    assert len(_baks(failed)) == 1
    assert len(_baks(legacy)) == 1
    # legacy file itself stays untouched (owner decision: file stays + dated .bak)
    assert _read(legacy) == _read(_baks(legacy)[0])


# ── 3–7: merge semantics ─────────────────────────────────────────────────────

def test_03_dedupe_email_case_and_whitespace(mod, tmp_path):
    legacy = tmp_path / LEGACY_NAME
    failed = tmp_path / FAILED_NAME
    _write(legacy, [_legacy_rec("  Dup@Example.COM "), _legacy_rec("dup@example.com"), _legacy_rec("New@x.com")])
    _write(failed, [_failed_rec("DUP@example.com")])
    rc = _run(mod, legacy, failed, "--apply")
    assert rc == EXIT_OK
    data = _read(failed)
    assert len(data) == 2
    assert sorted(r["email"].strip().lower() for r in data) == ["dup@example.com", "new@x.com"]


def test_04_legacy_fields_preserved_under_legacy_quarantine(mod, files):
    legacy, failed = files
    _run(mod, legacy, failed, "--apply")
    rec = next(r for r in _read(failed) if r["email"].lower() == "alpha@example.com")
    assert "legacy_quarantine" in rec
    lq = rec["legacy_quarantine"]
    assert lq["quarantine_verdict"] == "suspended_by_verifier"
    assert lq["quarantine_detail"] == "user_suspended"
    assert lq["quarantined_at"] == "2026-10-20T10:11:12"
    assert lq["cookies"] == {"session": "COOKIE_SECRET_VALUE"}
    assert lq["balance"] == 0 and lq["active"] is False
    # top-level 05.02 shape
    assert rec["status"] == "suspended"
    assert rec["failure_reason"] == "legacy_quarantine: suspended_by_verifier"
    assert rec["dead_reason"] == "user_suspended"
    assert "merged_from_legacy_at" in rec
    # cookies/balance/active NOT lifted to top level
    assert "cookies" not in rec and "balance" not in rec and "active" not in rec
    # password carried over (needed by 05.02 relogin), unchanged
    assert rec["password"] == "SuperSecretP@ss"


def test_05_quarantined_at_converted_to_removed_at(mod, tmp_path):
    legacy = tmp_path / LEGACY_NAME
    failed = tmp_path / FAILED_NAME
    _write(legacy, [
        _legacy_rec("a@x.com", ts="2026-10-20T10:11:12"),
        _legacy_rec("b@x.com", ts="not-a-date"),
        _legacy_rec("c@x.com", ts=None),
    ])
    _write(failed, [])
    assert _run(mod, legacy, failed, "--apply") == EXIT_OK
    by = {r["email"]: r for r in _read(failed)}
    assert by["a@x.com"]["removed_at"] == "2026-10-20 10:11:12"
    assert by["b@x.com"]["removed_at"] == "not-a-date"  # fallback: as-is
    assert "removed_at" in by["c@x.com"]  # present (merge timestamp fallback), never crashes


def test_06_oldest_wins_on_conflict(mod, tmp_path):
    legacy = tmp_path / LEGACY_NAME
    failed = tmp_path / FAILED_NAME
    _write(legacy, [_legacy_rec("same@x.com", verdict="NEW_VERDICT")])
    original = _failed_rec("same@x.com")
    _write(failed, [original])
    assert _run(mod, legacy, failed, "--apply") == EXIT_OK
    data = _read(failed)
    assert len(data) == 1
    assert data[0] == original  # untouched: oldest wins
    assert "legacy_quarantine" not in data[0]


def test_07_idempotent_second_run_adds_zero(mod, files):
    legacy, failed = files
    assert _run(mod, legacy, failed, "--apply") == EXIT_OK
    after_first = _read(failed)
    assert _run(mod, legacy, failed, "--apply") == EXIT_OK
    after_second = _read(failed)
    assert after_second == after_first
    assert len(after_second) == 3


# ── 8–9: missing / corrupt legacy → no change ────────────────────────────────

def test_08_legacy_missing_exit2_no_change_no_bak(mod, tmp_path):
    legacy = tmp_path / LEGACY_NAME  # not created
    failed = tmp_path / FAILED_NAME
    _write(failed, [_failed_rec("g@x.com")])
    before = failed.read_bytes()
    rc = _run(mod, legacy, failed, "--apply")
    assert rc == EXIT_INPUT_ERROR
    assert failed.read_bytes() == before
    assert _baks(failed) == [] and _baks(legacy) == []


def test_09_legacy_corrupt_exit2_no_change(mod, tmp_path):
    legacy = tmp_path / LEGACY_NAME
    failed = tmp_path / FAILED_NAME
    legacy.write_text("{ this is : not json", encoding="utf-8")
    _write(failed, [_failed_rec("g@x.com")])
    before = failed.read_bytes()
    rc = _run(mod, legacy, failed, "--apply")
    assert rc == EXIT_INPUT_ERROR
    assert failed.read_bytes() == before
    assert _baks(failed) == [] and _baks(legacy) == []


# ── 10–12: target shapes & invalid records ───────────────────────────────────

def test_10_target_missing_created_as_list(mod, tmp_path):
    legacy = tmp_path / LEGACY_NAME
    failed = tmp_path / FAILED_NAME  # not created
    _write(legacy, [_legacy_rec("a@x.com")])
    assert _run(mod, legacy, failed, "--apply") == EXIT_OK
    data = _read(failed)
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["email"] == "a@x.com"
    assert _baks(failed) == []  # nothing to back up for a missing target


def test_11_target_dict_shape_preserved(mod, tmp_path):
    legacy = tmp_path / LEGACY_NAME
    failed = tmp_path / FAILED_NAME
    _write(legacy, [_legacy_rec("a@x.com")])
    _write(failed, {"meta": {"v": 1}, "accounts": [_failed_rec("g@x.com")]})
    assert _run(mod, legacy, failed, "--apply") == EXIT_OK
    data = _read(failed)
    assert isinstance(data, dict)
    assert data["meta"] == {"v": 1}
    assert sorted(r["email"] for r in data["accounts"]) == ["a@x.com", "g@x.com"]


def test_12_record_without_email_skipped_invalid(mod, tmp_path, capsys):
    legacy = tmp_path / LEGACY_NAME
    failed = tmp_path / FAILED_NAME
    _write(legacy, [_legacy_rec("ok@x.com"), {"quarantine_verdict": "x"}, {"email": "   "}, "not-a-dict", None])
    _write(failed, [])
    assert _run(mod, legacy, failed, "--apply") == EXIT_OK
    data = _read(failed)
    assert [r["email"] for r in data] == ["ok@x.com"]
    out = capsys.readouterr().out
    assert "skipped_invalid" in out
    summary = json.loads(out[out.index("{"):out.rindex("}") + 1])
    assert summary["skipped_invalid"] == 4
    assert summary["added"] == 1
    assert summary["legacy_total"] == 5


# ── 13: Logging contract — full e-mails, never secrets ──────────────────────

def test_13_full_emails_in_stdout_no_secrets(mod, files, capsys):
    legacy, failed = files
    _write(failed, [_failed_rec("alpha@example.com")])  # force a skipped_existing entry too
    assert _run(mod, legacy, failed, "--apply") == EXIT_OK
    out = capsys.readouterr().out
    low = out.lower()
    # owner decision: e-mails are explicit and complete — no stars, no masking
    assert "alpha@example.com" in low
    assert "beta@example.com" in low
    assert "***" not in out
    summary = json.loads(out[out.index("{"):out.rindex("}") + 1])
    assert summary["added_emails"] == ["beta@example.com"]
    assert summary["skipped_existing_emails"] == ["alpha@example.com"]
    assert "added_masked" not in summary and "skipped_existing_masked" not in summary
    # secrets are still never printed
    assert "supersecretp@ss" not in low
    assert "cookie_secret_value" not in low
    assert mod.display_email("  Alpha@Example.com ") == "Alpha@Example.com"
    assert mod.display_email("") == "<empty>"
    assert not hasattr(mod, "mask_email")


# ── 14: path guard ───────────────────────────────────────────────────────────

def test_14_path_guard_real_filename_outside_tmp(mod, tmp_path, capsys):
    outside = Path("/nonexistent_p49_guard_dir") / FAILED_NAME
    legacy = tmp_path / LEGACY_NAME
    _write(legacy, [_legacy_rec("a@x.com")])
    # guarded: refused before any read (exit 3), even in dry-run
    assert _run(mod, legacy, outside) == EXIT_GUARDED
    assert "--i-know-this-is-real" in capsys.readouterr().out
    # also guards the legacy side
    assert _run(mod, Path("/nonexistent_p49_guard_dir") / LEGACY_NAME, tmp_path / FAILED_NAME) == EXIT_GUARDED
    # with the flag, the guard is lifted → normal flow (missing target = new list; dry-run → exit 0, nothing created)
    assert _run(mod, legacy, outside, "--i-know-this-is-real") == EXIT_OK
    assert not outside.parent.exists()
    # ...and a missing *legacy* with the flag reaches the input check (exit 2, not 3)
    assert _run(mod, Path("/nonexistent_p49_guard_dir") / LEGACY_NAME, tmp_path / FAILED_NAME,
                "--i-know-this-is-real") == EXIT_INPUT_ERROR
    # tmp paths with real names are never guarded (that is what the whole pack relies on)
    assert mod.is_guarded_path(tmp_path / FAILED_NAME) is False
    assert mod.is_guarded_path(outside) is True
    assert mod.is_guarded_path(Path("/nonexistent_p49_guard_dir") / "other.json") is False
