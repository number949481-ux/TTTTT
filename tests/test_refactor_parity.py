"""
test_refactor_parity.py
=======================
اختبار التكافؤ الكامل (Feature Parity) بين حزمة bridge_refactor/
والملف المرجعي 01.31_telegram_gen_bridge.py:

  1. byte-parity: إعادة تجميع الأجزاء parts/p*.py تطابق الأصل حرفياً.
  2. symbol-parity: كل def/class top-level في الأصل موجودة في الـ runtime.
  3. facade-parity: كل واجهة domain تعيد نفس الكائنات (identity check).
  4. behavior spot-checks: عينات سلوكية للمسارات الحرجة.
"""
import ast
import hashlib
import pathlib
import sys
import unittest

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

SRC = webapp_dir / "01.31_telegram_gen_bridge.py"
PARTS_DIR = webapp_dir / "bridge_refactor" / "parts"

from bridge_refactor import runtime  # noqa: E402

ns = runtime.ns


class TestByteParity(unittest.TestCase):
    def test_parts_reassemble_to_original(self):
        src = SRC.read_text(encoding="utf-8")
        recon = ""
        for part in sorted(PARTS_DIR.glob("p*.py")):
            text = part.read_text(encoding="utf-8")
            self.assertTrue(text.startswith('"""[VERBATIM SLICE]'), part.name)
            end = text.index('"""', 3) + 4
            recon += text[end:]
        self.assertEqual(
            hashlib.sha256(src.encode()).hexdigest(),
            hashlib.sha256(recon.encode()).hexdigest(),
            "إعادة تجميع الأجزاء لا تطابق الملف المرجعي بايت-بايت",
        )


class TestSymbolParity(unittest.TestCase):
    def test_all_toplevel_defs_present(self):
        tree = ast.parse(SRC.read_text(encoding="utf-8"))
        original = {
            n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        missing = {name for name in original if not hasattr(ns, name)}
        self.assertFalse(missing, f"رموز مفقودة من الـ runtime: {sorted(missing)}")

    def test_critical_features_present(self):
        critical = [
            "CONTRACTS", "apply_contract", "is_protected",
            "send_message_and_make_public", "send_message_with_auto_account_failover",
            "make_project_always_public", "get_public_forked_pid",
            "download_project_archive", "ProjectRegistry",
            "AccountSelectionLiveRenderer", "AccountSelectionLiveTransport",
            "build_live_preview_keyboard", "evaluate_credit_checkpoint_gate",
            "process_user_task_async", "handle_telegram_update",
            "run_telegram_polling", "refresh_cookies_on_401",
            "inspect_github_repository", "resolve_resume_context",
        ]
        for name in critical:
            self.assertTrue(hasattr(ns, name), f"ميزة حرجة مفقودة: {name}")


class TestFacadeParity(unittest.TestCase):
    def test_facades_reexport_identical_objects(self):
        from bridge_refactor.core import config, models, status, security, logging_setup
        from bridge_refactor.genspark import engine, account_manager
        from bridge_refactor.telegram import messaging, handlers, ui
        from bridge_refactor.projects import registry, tree
        from bridge_refactor.git import github_sync
        from bridge_refactor.workers import jobs

        pairs = [
            (config.CONTRACTS, ns.CONTRACTS),
            (models.BridgeConfig, ns.BridgeConfig),
            (status.detect_response_status, ns.detect_response_status),
            (security._extract_archive_with_diagnostics, ns._extract_archive_with_diagnostics),
            (logging_setup.log_event, ns.log_event),
            (engine.send_message_with_auto_account_failover, ns.send_message_with_auto_account_failover),
            (account_manager.refresh_cookies_on_401, ns.refresh_cookies_on_401),
            (messaging.AccountSelectionLiveTransport, ns.AccountSelectionLiveTransport),
            (handlers.handle_telegram_update, ns.handle_telegram_update),
            (ui.build_dashboard_keyboard, ns.build_dashboard_keyboard),
            (registry.ProjectRegistry, ns.ProjectRegistry),
            (tree.save_project_branch, ns.save_project_branch),
            (github_sync.inspect_github_repository, ns.inspect_github_repository),
            (jobs.process_user_task_async, ns.process_user_task_async),
        ]
        for facade_obj, ns_obj in pairs:
            self.assertIs(facade_obj, ns_obj)


class TestBehaviorSpotChecks(unittest.TestCase):
    def test_detect_response_status(self):
        self.assertEqual(ns.detect_response_status("out of credits"), "CREDIT_EXHAUSTED")
        self.assertEqual(ns.detect_response_status({"status": 401}), "SESSION_EXPIRED")
        self.assertEqual(ns.detect_response_status("thinking..."), "RUNNING")
        self.assertEqual(
            ns.detect_response_status("تم بناء الموقع بنجاح والرابط جاهز للاستخدام النهائي"),
            "COMPLETED",
        )

    def test_extract_project_id_uuid(self):
        pid = "0a1b2c3d-1111-2222-3333-444455556666"
        self.assertEqual(ns.extract_project_id(f"https://www.genspark.ai/agents?id={pid}"), pid)

    def test_credit_checkpoint_gate_untracked(self):
        cfg = ns.BridgeConfig()
        gate = ns.evaluate_credit_checkpoint_gate(cfg, None, None, False)
        self.assertTrue(gate["allow_continuation"])
        self.assertEqual(cfg.last_credit_checkpoint_state, "UNTRACKED")

    def test_credit_checkpoint_gate_blocks_on_error(self):
        cfg = ns.BridgeConfig()
        gate = ns.evaluate_credit_checkpoint_gate(cfg, None, RuntimeError("x"), True)
        self.assertFalse(gate["allow_continuation"])
        self.assertEqual(cfg.last_credit_checkpoint_state, "BLOCKED_CALLBACK_ERROR")

    def test_account_selection_claims(self):
        email = "parity-test@example.com"
        self.assertTrue(ns.claim_account_selection(email, "tokA", "proj", 1))
        self.assertFalse(ns.claim_account_selection(email, "tokB"))
        self.assertTrue(ns.release_account_selection(email, "tokA"))

    def test_terminal_outcome(self):
        self.assertEqual(ns.describe_terminal_outcome("COMPLETED", None)["kind"], "success")
        self.assertEqual(ns.describe_terminal_outcome("TIMEOUT", None)["kind"], "failure")

    def test_engine_loads_from_bridge_home(self):
        mod = ns.get_genspark_engine()
        self.assertIsNotNone(mod)
        self.assertTrue(hasattr(mod, "send_chat"))
        self.assertTrue(hasattr(mod, "do_login"))


if __name__ == "__main__":
    unittest.main()
