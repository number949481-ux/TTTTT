"""
P48 — Pre-Flight Gift Freshness Layer (STEP-2 of tri-state gift integration).

Contract (owner-approved, offline only):
  classify_gift_freshness(acc, now=None, stale_days=None, grace_days=None)
      -> (label, days)  with label in {"FRESH", "GRACE", "STALE", "UNKNOWN"}
  * reads ONLY fields written by 05.02 (days_without_gift / last_checked /
    quarantine_info) — never touches the network.
  * days >= stale_days            -> STALE
  * stale_days-grace <= days < stale -> GRACE
  * days < stale_days-grace       -> FRESH
  * missing / malformed / stale snapshot -> UNKNOWN (fail-open)
  get_eligible_accounts():
  * STALE accounts are excluded from selection (not isolated, not written).
  * FRESH/GRACE keep the existing last_used ordering; UNKNOWN are appended
    after them (fail-open, still usable).
  * Zero disk writes; in-flight accounts are untouched because the filter
    runs only at selection time.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
import time
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).parent.parent.resolve()
BRIDGE = ROOT / "01.33_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE.read_text(encoding="utf-8")


def _load_bridge_module():
    spec = importlib.util.spec_from_file_location("bridge_p48", str(BRIDGE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p48"] = mod
    spec.loader.exec_module(mod)
    return mod


def _extract_func(src: str, name: str) -> str:
    m = re.search(rf"^def {name}\(", src, re.MULTILINE)
    assert m, f"لم أجد الدالة {name}"
    nxt = re.search(r"^(?:def |class |@)", src[m.end():], re.MULTILINE)
    end = m.end() + (nxt.start() if nxt else len(src) - m.end())
    return src[m.start():end]


NOW = 1_800_000_000.0  # fixed epoch for determinism


def _acc(email="a@x.com", **over):
    base = {"email": email, "status": "active", "active": True, "cookies": {"s": "1"}, "last_used": 0}
    base.update(over)
    return base


def _iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts))


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_bridge_module()


# ─────────────────────────────────────────────────────────────────────────────
# 1) Constants
# ─────────────────────────────────────────────────────────────────────────────
class TestConstants(_Base):
    def test_01_defaults(self):
        self.assertTrue(self.mod.GIFT_PREFLIGHT_ENABLED)
        self.assertEqual(self.mod.GIFT_STALE_DAYS, 14)
        self.assertEqual(self.mod.GIFT_GRACE_DAYS, 3)
        self.assertEqual(self.mod.GIFT_SNAPSHOT_MAX_AGE_HOURS, 72)

    def test_02_labels_tuple(self):
        self.assertEqual(self.mod.GIFT_LABELS, ("FRESH", "GRACE", "STALE", "UNKNOWN"))


# ─────────────────────────────────────────────────────────────────────────────
# 2) classify_gift_freshness — pure function
# ─────────────────────────────────────────────────────────────────────────────
class TestClassify(_Base):
    def c(self, acc, **kw):
        return self.mod.classify_gift_freshness(acc, now=NOW, **kw)

    def test_01_fresh_1_day(self):
        self.assertEqual(self.c(_acc(days_without_gift=1, last_checked=_iso(NOW - 3600))), ("FRESH", 1))

    def test_02_fresh_upper_edge_10_days(self):
        # stale 14 - grace 3 = 11 → 10 is still FRESH
        self.assertEqual(self.c(_acc(days_without_gift=10, last_checked=_iso(NOW - 3600))), ("FRESH", 10))

    def test_03_grace_lower_edge_11_days(self):
        self.assertEqual(self.c(_acc(days_without_gift=11, last_checked=_iso(NOW - 3600))), ("GRACE", 11))

    def test_04_grace_upper_edge_13_days(self):
        self.assertEqual(self.c(_acc(days_without_gift=13, last_checked=_iso(NOW - 3600))), ("GRACE", 13))

    def test_05_stale_boundary_exact_14_inclusive(self):
        # owner decision: >= 14 is STALE (matches 05.02:408)
        self.assertEqual(self.c(_acc(days_without_gift=14, last_checked=_iso(NOW - 3600))), ("STALE", 14))

    def test_06_stale_999_no_gift_marker(self):
        self.assertEqual(self.c(_acc(days_without_gift=999, last_checked=_iso(NOW - 3600))), ("STALE", 999))

    def test_07_stale_from_quarantine_info_without_days(self):
        acc = _acc(quarantine_info={"reason": "stale_daily_gift", "days_without_gift": 20})
        self.assertEqual(self.c(acc), ("STALE", 20))

    def test_08_unknown_when_no_fields(self):
        self.assertEqual(self.c(_acc()), ("UNKNOWN", None))

    def test_09_unknown_when_days_malformed(self):
        self.assertEqual(self.c(_acc(days_without_gift="abc", last_checked=_iso(NOW - 3600))), ("UNKNOWN", None))
        self.assertEqual(self.c(_acc(days_without_gift=None, last_checked=_iso(NOW - 3600))), ("UNKNOWN", None))
        self.assertEqual(self.c(_acc(days_without_gift=-5, last_checked=_iso(NOW - 3600))), ("UNKNOWN", None))

    def test_10_unknown_when_snapshot_too_old(self):
        # last_checked older than GIFT_SNAPSHOT_MAX_AGE_HOURS → data not trusted → UNKNOWN (fail-open)
        old = _iso(NOW - (self.mod.GIFT_SNAPSHOT_MAX_AGE_HOURS + 1) * 3600)
        self.assertEqual(self.c(_acc(days_without_gift=2, last_checked=old)), ("UNKNOWN", None))

    def test_11_stale_snapshot_age_does_not_rescue_stale(self):
        # a STALE verdict with a stale snapshot is still STALE if days still >= threshold after ageing
        old_ts = NOW - 5 * 86400
        acc = _acc(days_without_gift=12, last_checked=_iso(old_ts))
        # 12 days at snapshot + 5 days elapsed = 17 → STALE (ageing applied, never optimistic)
        self.assertEqual(self.c(acc), ("STALE", 17))

    def test_12_ageing_moves_fresh_to_grace(self):
        acc = _acc(days_without_gift=9, last_checked=_iso(NOW - 2 * 86400))
        self.assertEqual(self.c(acc), ("GRACE", 11))

    def test_13_no_last_checked_but_days_present_is_unknown(self):
        self.assertEqual(self.c(_acc(days_without_gift=3)), ("UNKNOWN", None))

    def test_14_custom_thresholds(self):
        acc = _acc(days_without_gift=5, last_checked=_iso(NOW - 3600))
        self.assertEqual(self.c(acc, stale_days=5, grace_days=2), ("STALE", 5))
        self.assertEqual(self.c(acc, stale_days=7, grace_days=2), ("GRACE", 5))
        self.assertEqual(self.c(acc, stale_days=10, grace_days=2), ("FRESH", 5))

    def test_15_non_dict_is_unknown(self):
        self.assertEqual(self.mod.classify_gift_freshness(None, now=NOW), ("UNKNOWN", None))
        self.assertEqual(self.mod.classify_gift_freshness("x", now=NOW), ("UNKNOWN", None))

    def test_16_pure_no_mutation(self):
        acc = _acc(days_without_gift=2, last_checked=_iso(NOW - 3600))
        snap = dict(acc)
        self.c(acc)
        self.assertEqual(acc, snap)


# ─────────────────────────────────────────────────────────────────────────────
# 3) get_eligible_accounts — selection-time filter
# ─────────────────────────────────────────────────────────────────────────────
class TestEligibility(_Base):
    def setUp(self):
        self.fresh = _acc("fresh@x.com", days_without_gift=1, last_checked=_iso(NOW - 3600), last_used=300)
        self.grace = _acc("grace@x.com", days_without_gift=12, last_checked=_iso(NOW - 3600), last_used=100)
        self.stale = _acc("stale@x.com", days_without_gift=20, last_checked=_iso(NOW - 3600), last_used=10)
        self.unknown = _acc("unk@x.com", last_used=5)  # no gift fields at all
        self.all = [self.stale, self.unknown, self.fresh, self.grace]

    def _elig(self, accounts=None, tried=None):
        with mock.patch.object(self.mod.time, "time", return_value=NOW):
            return self.mod.get_eligible_accounts(accounts if accounts is not None else self.all, tried or set())

    def test_01_stale_excluded(self):
        emails = [a["email"] for a in self._elig()]
        self.assertNotIn("stale@x.com", emails)

    def test_02_fresh_and_grace_kept_in_last_used_order_then_unknown_tail(self):
        emails = [a["email"] for a in self._elig()]
        # known-good first by last_used asc (grace=100 < fresh=300), then UNKNOWN appended
        self.assertEqual(emails, ["grace@x.com", "fresh@x.com", "unk@x.com"])

    def test_03_unknown_is_fail_open_not_excluded(self):
        emails = [a["email"] for a in self._elig([self.unknown])]
        self.assertEqual(emails, ["unk@x.com"])

    def test_04_all_stale_returns_empty_not_crash(self):
        self.assertEqual(self._elig([self.stale, dict(self.stale, email="s2@x.com")]), [])

    def test_05_tried_emails_still_respected(self):
        emails = [a["email"] for a in self._elig(tried={"fresh@x.com"})]
        self.assertEqual(emails, ["grace@x.com", "unk@x.com"])

    def test_06_cooldown_and_banned_still_filtered_before_gift(self):
        cd = _acc("cd@x.com", status="cooldown", cooldown_until=NOW + 999, days_without_gift=1, last_checked=_iso(NOW - 3600))
        banned = _acc("ban@x.com", status="banned", days_without_gift=1, last_checked=_iso(NOW - 3600))
        emails = [a["email"] for a in self._elig([cd, banned, self.fresh])]
        self.assertEqual(emails, ["fresh@x.com"])

    def test_07_no_disk_write_and_no_mutation(self):
        snapshot = [dict(a) for a in self.all]
        with mock.patch.object(self.mod, "update_account_data") as upd, \
             mock.patch.object(self.mod, "mark_account_cooldown") as cool:
            self._elig()
        upd.assert_not_called()
        cool.assert_not_called()
        self.assertEqual(self.all, snapshot)
        for a in self.all:
            self.assertNotIn("gift_status", a)
            self.assertNotIn("quarantined", a)

    def test_08_disabled_flag_restores_legacy_behaviour(self):
        with mock.patch.object(self.mod, "GIFT_PREFLIGHT_ENABLED", False):
            emails = [a["email"] for a in self._elig()]
        # legacy: pure last_used ascending, stale included
        self.assertEqual(emails, ["unk@x.com", "stale@x.com", "grace@x.com", "fresh@x.com"])

    def test_09_stale_skip_is_logged_once_per_call(self):
        with mock.patch.object(self.mod, "log_event") as le:
            self._elig()
        msgs = [str(c.args[1]) for c in le.call_args_list if len(c.args) > 1]
        self.assertTrue(any("GIFT_PREFLIGHT" in m and "stale@x.com" in m for m in msgs), msgs)

    def test_10_unknown_fail_open_is_logged(self):
        with mock.patch.object(self.mod, "log_event") as le:
            self._elig([self.unknown])
        msgs = [str(c.args[1]) for c in le.call_args_list if len(c.args) > 1]
        self.assertTrue(any("GIFT_PREFLIGHT" in m and "UNKNOWN" in m for m in msgs), msgs)


# ─────────────────────────────────────────────────────────────────────────────
# 4) Source contracts — single injection point, in-flight untouched
# ─────────────────────────────────────────────────────────────────────────────
class TestSourceContracts(unittest.TestCase):
    def test_01_classify_is_top_level_and_before_get_eligible(self):
        i_cls = BRIDGE_SRC.index("\ndef classify_gift_freshness(")
        i_elig = BRIDGE_SRC.index("\ndef get_eligible_accounts(")
        self.assertLess(i_cls, i_elig)

    def test_02_classify_has_no_network_or_io(self):
        body = _extract_func(BRIDGE_SRC, "classify_gift_freshness")
        for forbidden in ("requests.", "curl_cffi", "sess.", "open(", "update_account_data(", "mark_account_cooldown(", "json.dump"):
            self.assertNotIn(forbidden, body, forbidden)

    def test_03_failover_loop_not_touched(self):
        body = _extract_func(BRIDGE_SRC, "send_message_with_auto_account_failover")
        self.assertNotIn("classify_gift_freshness", body)
        self.assertNotIn("GIFT_PREFLIGHT", body)

    def test_04_single_injection_point(self):
        # classify is referenced only in: its own def + get_eligible_accounts
        refs = [m.start() for m in re.finditer(r"classify_gift_freshness\(", BRIDGE_SRC)]
        elig = _extract_func(BRIDGE_SRC, "get_eligible_accounts")
        self.assertEqual(len(refs), 1 + elig.count("classify_gift_freshness("))
        self.assertGreaterEqual(elig.count("classify_gift_freshness("), 1)

    def test_05_is_account_ready_unchanged_signature(self):
        self.assertIn("def is_account_ready(acc: dict) -> bool:", BRIDGE_SRC)
        self.assertNotIn("classify_gift_freshness", _extract_func(BRIDGE_SRC, "is_account_ready"))

    def test_06_crlf_preserved(self):
        raw = BRIDGE.read_bytes()
        self.assertIn(b"\r\n", raw)
        self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"), "mixed line endings detected")


if __name__ == "__main__":
    unittest.main()
