#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات continue_project.py — CLI تكملة نفس المشروع من رابط.
موثّق في: genspark-session-bridge/06_CONTINUE_SAME_PROJECT_API.md (SESSION-GSB-001)

لا تفتح أي اتصال شبكة: كل اختبار إما وحدة نقية (parsing) أو --dry-run.
"""
import importlib.util
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLI = ROOT / "continue_project.py"
VALID_UUID = "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6"


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("continue_project_mod", CLI)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_cli(*args, timeout=60):
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True, text=True, timeout=timeout, cwd=str(ROOT),
        env={"PATH": "/usr/bin:/bin", "NO_COLOR": "1", "HOME": "/home/user",
             "PYTHONIOENCODING": "utf-8"},
    )


class TestCliExists(unittest.TestCase):
    def test_file_exists_and_compiles(self):
        self.assertTrue(CLI.exists(), "continue_project.py غير موجود")
        import ast
        ast.parse(CLI.read_text(encoding="utf-8"))


class TestProjectLocatorParsing(unittest.TestCase):
    """وحدة نقية — نفس سلوك extract_project_id/is_probable_project_id في 01.33"""

    @classmethod
    def setUpClass(cls):
        cls.m = _load_cli_module()

    def test_viewer_link_is_pid(self):
        """مثال المالك: autopilotagent_viewer?id=<UUID>"""
        r = self.m.parse_project_locator(
            f"https://www.genspark.ai/autopilotagent_viewer?id={VALID_UUID}")
        self.assertEqual(r["kind"], "pid")
        self.assertEqual(r["pid"], VALID_UUID)

    def test_agents_link_is_pid(self):
        r = self.m.parse_project_locator(f"https://www.genspark.ai/agents?id={VALID_UUID}")
        self.assertEqual(r["kind"], "pid")
        self.assertEqual(r["pid"], VALID_UUID)

    def test_raw_uuid_is_pid(self):
        r = self.m.parse_project_locator(VALID_UUID)
        self.assertEqual(r["kind"], "pid")
        self.assertEqual(r["pid"], VALID_UUID)

    def test_uuid_embedded_in_sentence(self):
        r = self.m.parse_project_locator(f"كمّل على {VALID_UUID} بسرعة")
        self.assertEqual(r["kind"], "pid")
        self.assertEqual(r["pid"], VALID_UUID)

    def test_domain_without_valid_uuid_is_malformed(self):
        for bad in (
            "https://www.genspark.ai/agents?id=12345",
            "https://www.genspark.ai/agents?id=not-a-uuid-at-all",
            "https://www.genspark.ai/agents",
        ):
            with self.subTest(bad=bad):
                self.assertEqual(self.m.parse_project_locator(bad)["kind"], "malformed")

    def test_plain_prompt_is_none(self):
        for txt in ("اعملي موقع", "", "   ", "hello world"):
            with self.subTest(txt=txt):
                self.assertEqual(self.m.parse_project_locator(txt)["kind"], "none")

    def test_login_redirect_rejected(self):
        """رابط login لا يجوز اعتباره PID (حماية من كوكيز منتهية)"""
        self.assertFalse(self.m.is_probable_project_id("https://www.genspark.ai/login"))
        self.assertFalse(self.m.is_probable_project_id("login"))

    def test_is_probable_project_id_strictness(self):
        self.assertTrue(self.m.is_probable_project_id(VALID_UUID))
        self.assertTrue(self.m.is_probable_project_id(VALID_UUID.upper()))
        for bad in ("", None, "غير معروف", "__INVALID_PROJECT__",
                    VALID_UUID[:-1], VALID_UUID + "x", f"a/{VALID_UUID}",
                    f"{VALID_UUID} extra", "prj_660b714cee4f4184"):
            with self.subTest(bad=bad):
                self.assertFalse(self.m.is_probable_project_id(bad))


class TestEmailMasking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _load_cli_module()

    def test_email_never_leaked_fully(self):
        masked = self.m.mask_email("secretuser@example.com")
        self.assertNotIn("secretuser", masked)
        self.assertIn("@example.com", masked)

    def test_masking_handles_junk(self):
        for val in ("", None, "noatsign"):
            self.assertIsInstance(self.m.mask_email(val), str)


class TestDryRunBehaviour(unittest.TestCase):
    """--dry-run يجب ألا يلمس الشبكة ولا المحرك"""

    def test_dry_run_viewer_link_succeeds(self):
        r = _run_cli("--dry-run", f"https://www.genspark.ai/autopilotagent_viewer?id={VALID_UUID}", "كمّل")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(VALID_UUID, r.stdout)
        self.assertIn("send_chat", r.stdout)
        # لم يُحمّل المحرك في dry-run
        self.assertNotIn("المحرك محمّل", r.stdout)

    def test_dry_run_fork_plan_has_three_steps(self):
        r = _run_cli("--dry-run", "--fork", "--owner-email", "owner@example.com",
                     f"https://www.genspark.ai/agents?id={VALID_UUID}", "كمّل")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ensure_public", r.stdout)
        self.assertIn("create_forked_project", r.stdout)
        self.assertIn("send_chat", r.stdout)

    def test_malformed_link_exits_6(self):
        r = _run_cli("--dry-run", "https://www.genspark.ai/agents?id=12345", "كمّل")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)
        self.assertIn("malformed", r.stdout)

    def test_plain_prompt_as_link_exits_6(self):
        r = _run_cli("--dry-run", "مش رابط خالص", "كمّل")
        self.assertEqual(r.returncode, 6, r.stdout + r.stderr)

    def test_empty_prompt_exits_2(self):
        r = _run_cli("--dry-run", VALID_UUID, "   ")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_owner_email_without_fork_warns(self):
        r = _run_cli("--dry-run", "--owner-email", "owner@example.com", VALID_UUID, "كمّل")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("سيُتجاهل", r.stdout)


class TestEngineContract(unittest.TestCase):
    """الدوال المستدعاة يجب أن تكون موجودة فعلاً في محرك 01.03 (منع الهلوسة)"""

    def test_engine_exposes_required_functions(self):
        engine = ROOT / "01.03Genspark_claude-opus-5-code.py"
        self.assertTrue(engine.exists(), "محرك 01.03 غير موجود")
        src = engine.read_text(encoding="utf-8")
        for fn in ("def send_chat(", "def ensure_public(", "def create_forked_project(",
                   "def load_accounts(", "def pick_account(", "def lock_pick_and_reserve(",
                   "class Config"):
            with self.subTest(fn=fn):
                self.assertIn(fn, src, f"{fn} غير موجود في المحرك")

    def test_send_chat_accepts_project_id_kwarg(self):
        """قلب التكملة: send_chat لازم يقبل project_id"""
        src = (ROOT / "01.03Genspark_claude-opus-5-code.py").read_text(encoding="utf-8")
        head = src[src.index("def send_chat("):src.index("def send_chat(") + 700]
        self.assertIn("project_id", head)
        self.assertIn("fork_project_id", head)

    def test_bridge_doc_exists(self):
        doc = ROOT / "genspark-session-bridge" / "06_CONTINUE_SAME_PROJECT_API.md"
        self.assertTrue(doc.exists(), "ملف التوثيق 06 مفقود")
        txt = doc.read_text(encoding="utf-8")
        self.assertIn("send_chat", txt)
        self.assertIn("create_forked_project", txt)


class TestEmbeddableApi(unittest.TestCase):
    """continue_from_link() — واجهة الاستدعاء الخارجي بمحرك وهمي (بدون شبكة).

    نبني ساندبوكس مؤقت فيه محرك وهمي بنفس عقد 01.03 + نسخة من السكريبت،
    عشان نختبر الدورة كاملة: حجز ➔ (فورك) ➔ إرسال ➔ فك الحجز فوراً.
    """

    FAKE_ENGINE_SRC = '''
from dataclasses import dataclass
CALLS = []
@dataclass
class Config:
    accounts_file: str = "accounts_genspark.json"
    model: str = "claude-opus-5"
    timeout: int = 600
    persistent: bool = True
    cli_history_max: int = -1
    show_debug: bool = False
def load_accounts(cfg):
    return [{"email": "mockuser@test.com", "balance": 500,
             "cookies": {"session_id": "sek-123"}}]
def pick_account(accounts, cfg, skip_emails=None):
    a = accounts[0]; return a, a["cookies"]
def lock_pick_and_reserve(cfg, skip_emails=None):
    CALLS.append("reserve")
    a = load_accounts(cfg)[0]; return a, a["cookies"]
def release_account(email, cfg, status_zero=False, status_failed=False):
    CALLS.append(f"release:{email}")
def ensure_public(project_id, cookies, cfg, label=""):
    CALLS.append("ensure_public"); return f"https://pub/{project_id}"
def create_forked_project(project_id, cookies, cfg=None):
    CALLS.append("fork"); return "b2c3d4e5-f6a7-48b8-9c0d-1e2f3a4b5c6d"
def send_chat(cookies, question, email="", project_id=None, history=None,
              cfg=None, ticket_file=None, fork_project_id=None,
              on_project_start_callback=None):
    CALLS.append(f"send:{project_id}")
    assert cookies.get("session_id"), "كوكيز مفقودة!"
    return f"رد وهمي على: {question}", project_id, "msg-001"
'''
    LINK = f"https://www.genspark.ai/autopilotagent_viewer?id={VALID_UUID}"
    FORKED = "b2c3d4e5-f6a7-48b8-9c0d-1e2f3a4b5c6d"

    def _build_sandbox(self, engine_src=None):
        import tempfile
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="cp_api_"))
        self.addCleanup(__import__("shutil").rmtree, tmp, ignore_errors=True)
        (tmp / "99_fakeGenspark_claude-opus-5-code.py").write_text(
            engine_src or self.FAKE_ENGINE_SRC, encoding="utf-8")
        (tmp / "continue_project.py").write_text(
            CLI.read_text(encoding="utf-8"), encoding="utf-8")
        spec = importlib.util.spec_from_file_location(
            f"cp_api_{tmp.name}", tmp / "continue_project.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _quiet_call(self, mod, *args, **kw):
        """استدعاء مع كتم stdout عشان مخرجات الاختبارات تفضل نظيفة."""
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            return mod.continue_from_link(*args, **kw)

    def test_success_returns_dict_and_releases_reservation(self):
        mod = self._build_sandbox()
        r = self._quiet_call(mod, self.LINK, "كمّل من حيث توقفت")
        self.assertTrue(r["ok"])
        self.assertEqual(r["exit_code"], 0)
        self.assertTrue(r["answer"].startswith("رد وهمي"))
        self.assertEqual(r["final_pid"], VALID_UUID)
        self.assertIn(VALID_UUID, r["resume_url"])
        calls = mod._ENGINE["mod"].CALLS
        self.assertIn("reserve", calls)
        self.assertIn("release:mockuser@test.com", calls)
        self.assertLess(calls.index("reserve"),
                        calls.index("release:mockuser@test.com"),
                        "فك الحجز لازم يحصل بعد الحجز")

    def test_fork_flow_order(self):
        mod = self._build_sandbox()
        r = self._quiet_call(mod, self.LINK, "كمّل", fork=True)
        self.assertTrue(r["ok"])
        self.assertEqual(r.get("forked_pid"), self.FORKED)
        self.assertEqual(r["final_pid"], self.FORKED)
        self.assertEqual(mod._ENGINE["mod"].CALLS,
                         ["reserve", "ensure_public", "fork",
                          f"send:{self.FORKED}", "release:mockuser@test.com"])

    def test_bad_link_returns_dict_not_systemexit(self):
        mod = self._build_sandbox()
        r = self._quiet_call(mod, "https://www.genspark.ai/agents?id=12345", "كمّل")
        self.assertFalse(r["ok"])
        self.assertEqual(r["exit_code"], 6)
        self.assertIn("UUID", r["error"])

    def test_empty_prompt_returns_exit_2(self):
        mod = self._build_sandbox()
        r = mod.continue_from_link(self.LINK, "   ")
        self.assertFalse(r["ok"])
        self.assertEqual(r["exit_code"], 2)

    def test_send_exception_isolated_and_reservation_released(self):
        mod = self._build_sandbox()
        eng_first = self._quiet_call(mod, self.LINK, "تحميل")  # يحمّل المحرك
        self.assertTrue(eng_first["ok"])
        eng = mod._ENGINE["mod"]
        eng.CALLS.clear()
        orig = eng.send_chat

        def boom(*a, **k):
            eng.CALLS.append("send-boom")
            raise RuntimeError("انفجار وهمي")

        eng.send_chat = boom
        try:
            r = self._quiet_call(mod, self.LINK, "كمّل")
        finally:
            eng.send_chat = orig
        self.assertFalse(r["ok"])
        self.assertEqual(r["exit_code"], 8)
        self.assertIn("release:mockuser@test.com", eng.CALLS,
                      "الحجز ما اتفكش بعد الاستثناء!")

    def test_fork_unsupported_engine_exit_7(self):
        src = (self.FAKE_ENGINE_SRC
               .replace("def create_forked_project", "def _disabled_fork")
               .replace("def ensure_public", "def _disabled_public"))
        mod = self._build_sandbox(engine_src=src)
        r = self._quiet_call(mod, self.LINK, "كمّل", fork=True)
        self.assertFalse(r["ok"])
        self.assertEqual(r["exit_code"], 7)
        self.assertIn("لا يدعم الفورك", r["error"])


class TestEngineDiscovery(unittest.TestCase):
    """discover_engine_names — اكتشاف ديناميكي مع أولوية 01.03 الأساسي."""

    @classmethod
    def setUpClass(cls):
        cls.m = _load_cli_module()

    def test_root_dir_finds_canonical(self):
        names = self.m.discover_engine_names(ROOT)
        self.assertIn("01.03Genspark_claude-opus-5-code.py", names)
        self.assertEqual(names[0], "01.03Genspark_claude-opus-5-code.py",
                         "01.03 الأساسي لازم يتصدّر لو موجود")

    def test_owner_copies_find_their_engines(self):
        for folder, engine in (("الحماس", "01.04_Genspark_claude-opus-5-code.py"),
                               ("جديد", "02.07_Genspark_claude-opus-5-code.py")):
            d = ROOT / folder
            if not d.exists():
                continue
            with self.subTest(folder=folder):
                self.assertIn(engine, self.m.discover_engine_names(d))

    def test_empty_dir_returns_empty(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(self.m.discover_engine_names(td), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
