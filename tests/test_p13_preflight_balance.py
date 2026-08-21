# -*- coding: utf-8 -*-
"""
P13 — Pre-Flight Balance Check Guard Tests (TSK-3105)
حراسة عقد فحص الرصيد قبل أي إرسال:
- عتبة min_preflight_balance = 100 في BridgeConfig
- بوابة الرصيد قبل أي fork/شات في send_message_and_make_public
- رصيد فعلي < 100 → mark_account_cooldown(29h) + إرجاع LOW_BALANCE
- إعادة فحص الرصيد بعد refresh_cookies_on_401 (سد ثغرة الجلسة المتجددة الفارغة)
- فشل الشبكة (-1) لا يُعاقَب بالتبريد
- التخطي الصامت في حلقة الـ failover (continue بدون progress_callback)
"""
import pathlib
import re
import sys
import unittest
import importlib.util

ROOT = pathlib.Path(__file__).parent.parent.resolve()
BRIDGE = ROOT / "01.32_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE.read_text(encoding="utf-8")


def _extract_func(src: str, name: str) -> str:
    """يعزل جسم دالة top-level بالاسم من المصدر."""
    m = re.search(rf"^def {name}\(", src, re.MULTILINE)
    assert m, f"لم أجد الدالة {name}"
    start = m.start()
    nxt = re.search(r"^(?:def |class |@)", src[m.end():], re.MULTILINE)
    end = m.end() + (nxt.start() if nxt else len(src) - m.end())
    return src[start:end]


SEND_PUBLIC = _extract_func(BRIDGE_SRC, "send_message_and_make_public")
FAILOVER = _extract_func(BRIDGE_SRC, "send_message_with_auto_account_failover")


def _load_bridge_module():
    spec = importlib.util.spec_from_file_location("bridge_p13", str(BRIDGE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p13"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestPreflightBalanceConfig(unittest.TestCase):
    """TSK-3101: عتبة الرصيد في BridgeConfig"""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_bridge_module()

    def test_01_min_preflight_balance_default_100(self):
        cfg = self.mod.BridgeConfig()
        self.assertEqual(cfg.min_preflight_balance, 100)

    def test_02_min_preflight_balance_configurable(self):
        cfg = self.mod.BridgeConfig(min_preflight_balance=250)
        self.assertEqual(cfg.min_preflight_balance, 250)


class TestPreflightBalanceGate(unittest.TestCase):
    """TSK-3102/3103: بوابة الرصيد قبل الإرسال في send_message_and_make_public"""

    def test_03_gate_exists_and_reads_threshold(self):
        self.assertIn("min_preflight_balance", SEND_PUBLIC)
        self.assertIn("LOW_BALANCE", SEND_PUBLIC)

    def test_04_low_balance_triggers_29h_cooldown(self):
        # داخل بوابة الرصيد يجب استدعاء mark_account_cooldown بساعات التبريد الكاملة
        gate = SEND_PUBLIC.split("min_preflight_balance", 1)[1]
        self.assertIn("mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours", gate)

    def test_05_low_balance_returns_before_any_fork_or_chat(self):
        # إرجاع LOW_BALANCE يجب أن يسبق أول ذكر لـ fork أو send_chat في جسم الدالة
        low_pos = SEND_PUBLIC.find('"LOW_BALANCE"')
        fork_pos = SEND_PUBLIC.find("get_public_forked_pid")
        chat_pos = SEND_PUBLIC.find("mod.send_chat(")
        self.assertGreater(low_pos, 0)
        self.assertLess(low_pos, fork_pos, "بوابة الرصيد يجب أن تسبق الـ fork")
        self.assertLess(low_pos, chat_pos, "بوابة الرصيد يجب أن تسبق send_chat")

    def test_06_recheck_after_session_refresh(self):
        # بعد refresh_cookies_on_401 الناجح يجب إعادة فحص الرصيد (bal_recheck)
        refresh_block = SEND_PUBLIC.split("refresh_cookies_on_401(mod, email", 1)[1]
        self.assertIn("bal_recheck", refresh_block)
        self.assertIn("LOW_BALANCE", refresh_block)

    def test_07_network_failure_not_punished(self):
        # -1 (فشل شبكة) يجب ألا يدخل مسار التبريد: الشرط يتطلب رصيداً فعلياً >= 0
        self.assertTrue(
            re.search(r"bal_check\s*>=\s*0", SEND_PUBLIC) or "0 <= bal_check" in SEND_PUBLIC,
            "يجب اشتراط رصيد فعلي (>=0) قبل الحكم بالرصيد المنخفض — -1 فشل شبكة لا عقوبة عليه",
        )
        self.assertTrue(
            re.search(r"0\s*<=\s*bal_recheck", SEND_PUBLIC),
            "إعادة الفحص بعد التجديد يجب أن تشترط رصيداً فعلياً (0 <= bal_recheck)",
        )

    def test_08_valid_balance_persisted_to_account(self):
        # الرصيد الصالح يُحفظ في accounts json (حقل balance) للاستعلامات اللاحقة
        self.assertIn('{"balance": int(bal_check)}', SEND_PUBLIC)


class TestFailoverSilentSkip(unittest.TestCase):
    """TSK-3104: التخطي الصامت في حلقة الـ failover"""

    def test_09_low_balance_handled_in_failover(self):
        self.assertIn('status == "LOW_BALANCE"', FAILOVER)

    def test_10_low_balance_skips_silently_with_continue(self):
        block = FAILOVER.split('status == "LOW_BALANCE"', 1)[1]
        # أول توجيه تحكم بعد المعالجة يجب أن يكون continue (الحساب التالي)
        first_ctrl = re.search(r"^\s+(continue|return|break)\b", block, re.MULTILINE)
        self.assertIsNotNone(first_ctrl)
        self.assertEqual(first_ctrl.group(1), "continue")

    def test_11_low_balance_skip_precedes_credit_exhausted_handling(self):
        low_pos = FAILOVER.find('status == "LOW_BALANCE"')
        credit_pos = FAILOVER.find('status == "CREDIT_EXHAUSTED"', low_pos)
        self.assertGreater(low_pos, 0)
        self.assertGreater(credit_pos, low_pos)

    def test_12_no_user_notification_in_skip_block(self):
        # بلوك التخطي لا يرسل أي رسالة تيليجرام للمستخدم (صمت كامل)
        block = FAILOVER.split('status == "LOW_BALANCE"', 1)[1]
        end = re.search(r"^\s+continue\b", block, re.MULTILINE)
        skip_block = block[: end.end()]
        self.assertNotIn("send_telegram_message", skip_block)
        self.assertNotIn("progress_callback(", skip_block)

    def test_13_no_wrong_30min_auth_ban_for_low_balance(self):
        # بلوك التخطي لا يضع حظر auth_failed الخاطئ (1800 ثانية)
        block = FAILOVER.split('status == "LOW_BALANCE"', 1)[1]
        end = re.search(r"^\s+continue\b", block, re.MULTILINE)
        skip_block = block[: end.end()]
        self.assertNotIn("auth_failed", skip_block)
        self.assertNotIn("1800", skip_block)


class TestRefactorParityAfterP13(unittest.TestCase):
    """TSK-3106: تزامن bridge_refactor مع إصلاحات P13"""

    def test_14_p06_part_contains_preflight_gate(self):
        p06 = (ROOT / "bridge_refactor" / "parts" / "p06_engine_flow.py").read_text(encoding="utf-8")
        self.assertIn("min_preflight_balance", p06)
        self.assertIn("LOW_BALANCE", p06)


if __name__ == "__main__":
    unittest.main(verbosity=2)
