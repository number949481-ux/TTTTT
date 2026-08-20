# -*- coding: utf-8 -*-
"""
P17 — Hardening Tests (استئناف مهام الانقطاع)
1) سد ثغرة نافذة 120ث: جلسة منتهية (-2) تُجدَّد فوراً حتى لو last_refresh حديث.
2) بوابة رصيد بعد تجديد 401 أثناء الشات (نفس عقد P13: تبريد 29h + LOW_BALANCE).
3) دعم الجروبات: is_chat_allowed تسمح بالجروب المعتمد أو المستخدم المعتمد داخل أي جروب.
4) 🔧 [P20] التأكد من إزالة Git Native Sync بالكامل (REST-Only هو مسار الرفع الوحيد).
5) الملفات المولّدة (.pytest_cache / bridge_bot.log) خارج تتبع git.
"""
import pathlib
import re
import subprocess
import sys
import unittest
import importlib.util

ROOT = pathlib.Path(__file__).parent.parent.resolve()
BRIDGE = ROOT / "01.31_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE.read_text(encoding="utf-8")


def _extract_func(src: str, name: str, indent: str = "") -> str:
    m = re.search(rf"^{indent}def {name}\(", src, re.MULTILINE)
    assert m, f"لم أجد الدالة {name}"
    start = m.start()
    nxt = re.search(rf"^{indent}(?:def |class |@)", src[m.end():], re.MULTILINE)
    end = m.end() + (nxt.start() if nxt else len(src) - m.end())
    return src[start:end]


def _load_bridge_module():
    if "bridge_p17" in sys.modules:
        return sys.modules["bridge_p17"]
    spec = importlib.util.spec_from_file_location("bridge_p17", str(BRIDGE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bridge_p17"] = mod
    spec.loader.exec_module(mod)
    return mod


SEND_PUBLIC = _extract_func(BRIDGE_SRC, "send_message_and_make_public")


class TestExpiredSessionGate(unittest.TestCase):
    """TSK-P17-1: جلسة منتهية (-2) تتجدد فوراً بغض النظر عن نافذة 120ث"""

    def test_01_refresh_condition_includes_expired_session(self):
        self.assertIn("bal_check == -2 or (time.time() - last_refresh) > 120", SEND_PUBLIC)

    def test_02_old_vulnerable_condition_gone(self):
        self.assertNotRegex(
            SEND_PUBLIC,
            r"if not cookies_valid and \(time\.time\(\) - last_refresh\) > 120:",
        )


class TestMidChatBalanceGate(unittest.TestCase):
    """TSK-P17-2: إعادة فحص الرصيد بعد تجديد 401 أثناء الشات"""

    def setUp(self):
        m = re.search(r"التقاط 401 أثناء الشات", SEND_PUBLIC)
        assert m, "لم أجد بلوك 401 أثناء الشات"
        self.block = SEND_PUBLIC[m.start():m.start() + 2500]

    def test_01_recheck_balance_after_mid_chat_refresh(self):
        self.assertIn("bal_mid = mod.check_balance(cookies)", self.block)

    def test_02_low_balance_triggers_cooldown_and_silent_skip(self):
        self.assertIn("0 <= bal_mid < _min_balance", self.block)
        self.assertIn("mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours", self.block)
        self.assertIn('return None, "LOW_BALANCE", None, None, None', self.block)

    def test_03_network_failure_not_punished(self):
        # bal_mid = -1 (فشل شبكة) لا يدخل شرط العقوبة لأن الشرط 0 <= bal_mid
        self.assertIn("bal_mid = -1", self.block)

    def test_04_retry_continue_preserved(self):
        self.assertIn("time.sleep(1.5)", self.block)
        self.assertIn("continue", self.block)


class TestGroupChatSupport(unittest.TestCase):
    """TSK-P17-3: دعم الجروبات في بوابة الصلاحيات"""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_bridge_module()

    def test_01_allowed_private_user(self):
        uid = next(iter(self.mod.ALLOWED_CHAT_IDS))
        self.assertTrue(self.mod.is_chat_allowed(uid))

    def test_02_unknown_private_user_denied(self):
        self.assertFalse(self.mod.is_chat_allowed(999999999))

    def test_03_default_channel_group_allowed(self):
        gid = int(self.mod.DEFAULT_CHANNEL_ID)
        self.assertTrue(self.mod.is_chat_allowed(gid))

    def test_04_unknown_group_denied_without_allowed_sender(self):
        self.assertFalse(self.mod.is_chat_allowed(-100123456789))

    def test_05_unknown_group_allowed_with_allowed_sender(self):
        uid = next(iter(self.mod.ALLOWED_CHAT_IDS))
        self.assertTrue(self.mod.is_chat_allowed(-100123456789, from_user_id=uid))

    def test_06_unknown_group_denied_with_unknown_sender(self):
        self.assertFalse(self.mod.is_chat_allowed(-100123456789, from_user_id=555))

    def test_07_invalid_ids_denied(self):
        self.assertFalse(self.mod.is_chat_allowed(None))
        self.assertFalse(self.mod.is_chat_allowed("abc"))
        self.assertFalse(self.mod.is_chat_allowed(-100123456789, from_user_id="xyz"))

    def test_08_message_path_uses_gate(self):
        m = re.search(r"^def handle_telegram_update\(", BRIDGE_SRC, re.MULTILINE)
        handler = BRIDGE_SRC[m.start():]
        nxt = re.search(r"^def ", handler[10:], re.MULTILINE)
        handler = handler[:nxt.start() + 10] if nxt else handler
        self.assertIn('is_chat_allowed(chat_id, (msg.get("from") or {}).get("id"))', handler)

    def test_09_callback_path_uses_gate(self):
        m = re.search(r"^def handle_telegram_update\(", BRIDGE_SRC, re.MULTILINE)
        handler = BRIDGE_SRC[m.start():]
        self.assertIn('is_chat_allowed(chat_id, (cb.get("from") or {}).get("id"))', handler)

    def test_10_no_raw_membership_checks_left_in_handler(self):
        m = re.search(r"^def handle_telegram_update\(", BRIDGE_SRC, re.MULTILINE)
        handler_region = BRIDGE_SRC[m.start():m.start() + 40000]
        self.assertNotIn("chat_id not in ALLOWED_CHAT_IDS", handler_region)

    def test_11_env_extension_supported(self):
        self.assertIn("BRIDGE_ALLOWED_GROUP_IDS", BRIDGE_SRC)


class TestRestOnlyUploader(unittest.TestCase):
    """🔧 [P20] الرفع REST-Only: إلغاء Git Native Sync نهائياً — REST API هو المسار الوحيد"""

    @classmethod
    def setUpClass(cls):
        cls.uploader_src = _extract_func(BRIDGE_SRC, "_default_github_uploader", indent="    ")

    def test_01_git_native_sync_removed(self):
        # الدالة القديمة _git_native_sync_uploader اتشالت بالكامل (كانت تفشل بـ dest_root)
        self.assertNotIn("def _git_native_sync_uploader(", BRIDGE_SRC)
        self.assertNotIn("_generate_ai_commit_message(", BRIDGE_SRC)

    def test_02_no_git_clone_or_push_in_uploader(self):
        self.assertNotIn("git clone", self.uploader_src)
        self.assertNotIn("git push", self.uploader_src)
        self.assertNotIn("dest_root =", self.uploader_src)  # الذكر الوحيد في تعليق P20 التوثيقي

    def test_03_uses_contents_rest_api(self):
        self.assertIn("api.github.com/repos/", self.uploader_src)
        self.assertIn("/contents/", self.uploader_src)

    def test_04_p20_decision_documented(self):
        self.assertIn("[P20]", self.uploader_src)


class TestGeneratedFilesUntracked(unittest.TestCase):
    """TSK-P17-5: الملفات المولّدة خارج تتبع git"""

    @classmethod
    def setUpClass(cls):
        res = subprocess.run(
            ["git", "ls-files"], cwd=str(ROOT), capture_output=True, text=True
        )
        cls.tracked = res.stdout.splitlines()

    def test_01_pytest_cache_untracked(self):
        self.assertFalse(any(p.startswith(".pytest_cache") for p in self.tracked))

    def test_02_bridge_log_untracked(self):
        self.assertNotIn("bridge_bot.log", self.tracked)

    def test_03_gitignore_covers_both(self):
        gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".pytest_cache/", gi)
        self.assertIn("*.log", gi)


if __name__ == "__main__":
    unittest.main(verbosity=2)
