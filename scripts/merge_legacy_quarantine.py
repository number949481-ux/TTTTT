#!/usr/bin/env python3
"""
STEP-3 (Q-F) — merge the legacy verifier quarantine file into 05.02's ``accounts_failed.json``.

Standalone tool (owner decision, Gist RESUME11.md): 05.02 is NOT modified; only its
``create_backup`` / ``atomic_save_json`` helpers are reused (loaded via importlib with a
stub for the absent ``genspark_master_account_manager`` module, exactly as in STEP-1).

Data contract (PROGRESS.md › S3-A, approved 2026-10-31):
  * source  : ``accounts_genspark_blocked_failed__block_failed.json`` (verifier QUARANTINE_FILENAME)
              list[dict] with status/quarantine_verdict/quarantine_detail/quarantined_at/active/balance/cookies
  * target  : ``accounts_failed.json`` (05.02 Config.FAILED_FILE) — list[dict] OR {"accounts": [...]}
              saved back in the SAME shape it was found in.
  * record  : {email, password?, status="suspended",
               failure_reason="legacy_quarantine: <verdict>", dead_reason=<detail or verdict>,
               removed_at=<quarantined_at → "%Y-%m-%d %H:%M:%S" | as-is>, merged_from_legacy_at=<now>,
               legacy_quarantine={<full original record>}}  — cookies/balance/active stay nested only.
  * conflict: oldest wins (existing target record is never overwritten).
  * dead_accounts.json: out of scope (not touched).
  * legacy file: stays in place; a dated ``.bak`` is created for both files before writing.
  * dry-run is the DEFAULT; writes only with ``--apply``.
  * missing/corrupt input → exit 2, no change, no ``.bak``.
  * path guard: real file names outside a temp directory are refused (exit 3) unless
    ``--i-know-this-is-real`` is given.  NEVER run on real files without an explicit owner order.
  * Logging: e-mails are printed in full (owner decision 2026-10-31 — no masking);
    passwords/cookies are never printed.

Exit codes: 0 ok (incl. dry-run) · 2 input missing/corrupt · 3 refused by path guard.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import signal
import sys
import tempfile
import types
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
MANAGER_FILE = REPO_ROOT / "05.02_genspark_delayed_gifts_manager.py"

LEGACY_NAME = "accounts_genspark_blocked_failed__block_failed.json"   # verifier QUARANTINE_FILENAME
FAILED_NAME = "accounts_failed.json"                                  # 05.02 Config.FAILED_FILE
DEAD_NAME = "dead_accounts.json"                                      # 05.02 Config.DEAD_FILE (never written here)
REAL_FILE_NAMES = frozenset({LEGACY_NAME, FAILED_NAME, DEAD_NAME})

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_GUARDED = 3

_SAFE_PARTS = frozenset({"tmp", "temp", "tests", "test_data", "fixtures"})


# ── 05.02 helpers (read-only reuse) ──────────────────────────────────────────

def _load_manager_helpers():
    """Load ``create_backup`` / ``atomic_save_json`` from 05.02 without touching it.

    A stub replaces the absent ``genspark_master_account_manager`` module; the SIGINT
    handler 05.02 installs at import time is restored afterwards.  Falls back to local
    equivalents if 05.02 cannot be loaded, so the merge never depends on the live env.
    """
    if "genspark_master_account_manager" not in sys.modules:
        stub = types.ModuleType("genspark_master_account_manager")

        def _unavailable(*_a, **_k):  # pragma: no cover - never called by this tool
            raise RuntimeError("live Genspark access is forbidden inside merge_legacy_quarantine")

        stub.do_b2c_login = _unavailable
        stub.get_session = _unavailable
        stub.check_account_balance = _unavailable
        sys.modules["genspark_master_account_manager"] = stub

    prev_sigint = signal.getsignal(signal.SIGINT)
    try:
        spec = importlib.util.spec_from_file_location("_gifts_manager_helpers", MANAGER_FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.create_backup, module.atomic_save_json
    except Exception:  # pragma: no cover - defensive fallback
        return _local_create_backup, _local_atomic_save_json
    finally:
        try:
            signal.signal(signal.SIGINT, prev_sigint)
        except Exception:
            pass


def _local_create_backup(file_path: Path) -> Optional[Path]:
    if not file_path.exists():
        return None
    import shutil
    bak = file_path.parent / f"{file_path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    shutil.copy2(file_path, bak)
    return bak


def _local_atomic_save_json(file_path: Path, data: Any) -> bool:
    tmp = file_path.parent / f"{file_path.name}.tmp_merge"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(file_path)
    return True


# ── pure helpers ─────────────────────────────────────────────────────────────

def display_email(email: Any) -> str:
    """E-mail as printed in the summary: full and explicit (owner decision: no masking)."""
    s = str(email or "").strip()
    return s if s else "<empty>"


def normalize_email(value: Any) -> str:
    return str(value).strip().lower() if isinstance(value, str) else ""


def is_guarded_path(path: Path) -> bool:
    """True when ``path`` carries a real account-file name and is NOT inside a temp/test dir."""
    p = Path(path)
    if p.name not in REAL_FILE_NAMES:
        return False
    try:
        resolved = p.resolve()
    except Exception:
        resolved = p
    try:
        tmp_root = Path(tempfile.gettempdir()).resolve()
        if resolved == tmp_root or tmp_root in resolved.parents:
            return False
    except Exception:
        pass
    if any(part.lower() in _SAFE_PARTS or part.lower().startswith("pytest") for part in resolved.parts):
        return False
    return True


def convert_quarantined_at(value: Any, fallback: str) -> str:
    """``%Y-%m-%dT%H:%M:%S`` → ``%Y-%m-%d %H:%M:%S``; unparsable string → as-is; empty → fallback."""
    if not isinstance(value, str) or not value.strip():
        return fallback
    raw = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return raw


def build_merged_record(legacy: Dict[str, Any], now_str: str) -> Dict[str, Any]:
    verdict = legacy.get("quarantine_verdict")
    detail = legacy.get("quarantine_detail")
    rec: Dict[str, Any] = {
        "email": str(legacy.get("email", "")).strip(),
    }
    if isinstance(legacy.get("password"), str) and legacy["password"]:
        rec["password"] = legacy["password"]
    rec.update({
        "status": "suspended",
        "failure_reason": f"legacy_quarantine: {verdict if verdict else 'unknown'}",
        "dead_reason": detail if detail else (verdict if verdict else "legacy_quarantine"),
        "removed_at": convert_quarantined_at(legacy.get("quarantined_at"), now_str),
        "merged_from_legacy_at": now_str,
        "legacy_quarantine": dict(legacy),
    })
    return rec


def merge_records(
    legacy_records: List[Any],
    target_records: List[Any],
    now_str: str,
) -> Tuple[List[Any], Dict[str, Any]]:
    """Pure merge. Returns (new_target_list, stats). Existing target records are never modified."""
    existing = {normalize_email(r.get("email")) for r in target_records if isinstance(r, dict)}
    existing.discard("")
    added: List[Dict[str, Any]] = []
    stats = {"added": 0, "skipped_existing": 0, "skipped_invalid": 0,
             "added_emails": [], "skipped_existing_emails": []}
    for rec in legacy_records:
        if not isinstance(rec, dict):
            stats["skipped_invalid"] += 1
            continue
        key = normalize_email(rec.get("email"))
        if not key:
            stats["skipped_invalid"] += 1
            continue
        if key in existing:
            stats["skipped_existing"] += 1
            stats["skipped_existing_emails"].append(display_email(key))
            continue
        existing.add(key)
        added.append(build_merged_record(rec, now_str))
        stats["added"] += 1
        stats["added_emails"].append(display_email(key))
    return list(target_records) + added, stats


# ── strict IO (05.02's load_accounts swallows corruption → cannot honour exit 2) ──

def load_json_strict(path: Path) -> Any:
    """Raise FileNotFoundError / ValueError; never returns a silent default."""
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8-sig"))


def split_target_shape(data: Any) -> Tuple[Any, List[Any]]:
    """Return (container, records) so the container can be re-filled in its original shape."""
    if isinstance(data, list):
        return None, data
    if isinstance(data, dict):
        accounts = data.get("accounts", [])
        if not isinstance(accounts, list):
            raise ValueError("target 'accounts' is not a list")
        return data, accounts
    raise ValueError("target JSON must be a list or an object with 'accounts'")


def rebuild_target(container: Any, records: List[Any]) -> Any:
    if container is None:
        return records
    out = dict(container)
    out["accounts"] = records
    return out


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="merge_legacy_quarantine",
        description="Merge legacy verifier quarantine records into 05.02 accounts_failed.json (dry-run by default).",
    )
    p.add_argument("--legacy", required=True, help=f"path to legacy quarantine file ({LEGACY_NAME})")
    p.add_argument("--failed", required=True, help=f"path to 05.02 failed-accounts file ({FAILED_NAME})")
    p.add_argument("--apply", action="store_true", help="actually write (default is dry-run)")
    p.add_argument("--i-know-this-is-real", dest="i_know_this_is_real", action="store_true",
                   help="lift the real-path guard (owner order required)")
    return p


def _emit(summary: Dict[str, Any]) -> None:
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    legacy_path = Path(args.legacy)
    failed_path = Path(args.failed)
    dry_run = not args.apply

    # 0) path guard — before any read
    if not args.i_know_this_is_real:
        for label, p in (("legacy", legacy_path), ("failed", failed_path)):
            if is_guarded_path(p):
                print(f"[GUARD] refused: --{label} points to a real account file outside a temp/test dir "
                      f"({p.name}). Re-run with --i-know-this-is-real ONLY under explicit owner order.")
                return EXIT_GUARDED

    # 1) strict load legacy (missing/corrupt → exit 2, nothing touched)
    try:
        legacy_data = load_json_strict(legacy_path)
    except FileNotFoundError:
        print(f"[INPUT] legacy file missing: {legacy_path.name} — no change made, no backup created.")
        return EXIT_INPUT_ERROR
    except (ValueError, OSError) as e:
        print(f"[INPUT] legacy file unreadable/corrupt: {legacy_path.name} ({type(e).__name__}) — no change made.")
        return EXIT_INPUT_ERROR
    if isinstance(legacy_data, dict) and isinstance(legacy_data.get("accounts"), list):
        legacy_records = legacy_data["accounts"]
    elif isinstance(legacy_data, list):
        legacy_records = legacy_data
    else:
        print(f"[INPUT] legacy JSON must be a list (or object with 'accounts'): {legacy_path.name} — no change made.")
        return EXIT_INPUT_ERROR

    # 2) strict load target (missing → new list; corrupt → exit 2)
    target_exists = failed_path.exists()
    if target_exists:
        try:
            target_data = load_json_strict(failed_path)
            container, target_records = split_target_shape(target_data)
        except (ValueError, OSError) as e:
            print(f"[INPUT] target file unreadable/corrupt: {failed_path.name} ({type(e).__name__}) — no change made.")
            return EXIT_INPUT_ERROR
    else:
        container, target_records = None, []

    # 3) pure merge
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    merged, stats = merge_records(legacy_records, target_records, now_str)

    summary: Dict[str, Any] = {
        "dry_run": dry_run,
        "legacy_file": legacy_path.name,
        "target_file": failed_path.name,
        "legacy_total": len(legacy_records),
        "target_before": len(target_records),
        "added": stats["added"],
        "skipped_existing": stats["skipped_existing"],
        "skipped_invalid": stats["skipped_invalid"],
        "target_after": len(merged),
        "added_emails": stats["added_emails"],
        "skipped_existing_emails": stats["skipped_existing_emails"],
        "backups": [],
        "written": False,
    }

    if dry_run:
        _emit(summary)
        return EXIT_OK

    # 4) apply: backups first (both files), then atomic save of target only. Legacy stays as-is.
    create_backup, atomic_save_json = _load_manager_helpers()
    for p in (legacy_path, failed_path):
        if p.exists():
            bak = create_backup(p)
            if bak is None:
                print(f"[ABORT] backup failed for {p.name} — nothing written.")
                return EXIT_INPUT_ERROR
            summary["backups"].append(bak.name)
    if stats["added"] == 0 and target_exists:
        summary["written"] = False
        summary["note"] = "nothing to add — target left untouched (idempotent)"
        _emit(summary)
        return EXIT_OK
    failed_path.parent.mkdir(parents=True, exist_ok=True)
    ok = atomic_save_json(failed_path, rebuild_target(container, merged))
    if not ok:
        print(f"[ABORT] atomic save failed for {failed_path.name}.")
        return EXIT_INPUT_ERROR
    summary["written"] = True
    _emit(summary)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
