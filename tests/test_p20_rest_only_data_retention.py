#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p20_rest_only_data_retention.py
==========================================
🧬🔧 [P20] حراسة العقدين الجديدين:

العقد الأول — REST-Only Upload:
1. إزالة _git_native_sync_uploader و _generate_ai_commit_message نهائياً.
2. عدم وجود أي عمليات git clone/push/init داخل مسار الرفع.
3. _default_github_uploader يستخدم GitHub Contents REST API مباشرة
   (PUT/DELETE على api.github.com/repos/.../contents/...).
4. تخطي الملفات غير المتغيرة عبر مقارنة git blob sha (بدون git binary).

العقد الثاني — DATA_RETENTION Failover:
5. detect_response_status يكشف كلمات AI Data Retention → "DATA_RETENTION".
6. الكشف له أولوية قبل SESSION_EXPIRED / CREDIT_EXHAUSTED.
7. حلقة الـ failover تعامل DATA_RETENTION كنفاد رصيد: تبريد 29h + حساب تالٍ
   + إعادة إرسال «نفس آخر رسالة» (بدون التحويل لبرومبت الاستئناف) + تنبيه مميز.
8. حلقة polling الرئيسية تخرج عند DATA_RETENTION (حالة نهائية).
9. الوصف النهائي للمستخدم يتضمن رسالة مميزة للحالة.
"""

import sys
import re
import pathlib
import unittest
import importlib.util
from unittest import mock

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

BRIDGE_PATH = webapp_dir / "01.31_telegram_gen_bridge.py"
BRIDGE_SRC = BRIDGE_PATH.read_text(encoding="utf-8")

_spec = importlib.util.spec_from_file_location("bridge_mod_p20", BRIDGE_PATH)
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)

detect_response_status = _bridge.detect_response_status


def _extract_func(src: str, name: str, indent: str = "") -> str:
    m = re.search(rf"^{indent}def {name}\(", src, re.MULTILINE)
    assert m, f"لم أجد الدالة {name}"
    start = m.start()
    nxt = re.search(rf"^{indent}(?:def |class |@)", src[m.end():], re.MULTILINE)
    end = m.end() + (nxt.start() if nxt else len(src) - m.end())
    return src[start:end]


# ═══════════════════════════════════════════════════════════════
# العقد الأول: REST-Only Upload
# ═══════════════════════════════════════════════════════════════

class TestRestOnlyUpload(unittest.TestCase):
    """🔧 [P20] الرفع عبر REST API فقط — لا Git Native Sync"""

    def test_01_git_native_uploader_removed(self):
        self.assertNotIn("def _git_native_sync_uploader(", BRIDGE_SRC)
        self.assertNotIn("_git_native_sync_uploader(", BRIDGE_SRC)

    def test_02_ai_commit_message_removed(self):
        self.assertNotIn("def _generate_ai_commit_message(", BRIDGE_SRC)
        self.assertNotIn("_generate_ai_commit_message(", BRIDGE_SRC)

    def test_03_no_git_binary_operations(self):
        # لا clone/push/init في أي مكان بالملف
        for forbidden in ("git clone", "git push", "git init"):
            self.assertNotIn(forbidden, BRIDGE_SRC, f"وجدت عملية git native محظورة: {forbidden}")

    def test_04_default_uploader_uses_contents_api(self):
        fn = _extract_func(BRIDGE_SRC, "_default_github_uploader", indent="    ")
        self.assertIn("api.github.com/repos/", fn)
        self.assertIn("/contents/", fn)
        self.assertIn("requests.put(", fn)
        self.assertIn("requests.delete(", fn)

    def test_05_uploader_skips_unchanged_via_blob_sha(self):
        fn = _extract_func(BRIDGE_SRC, "_default_github_uploader", indent="    ")
        self.assertIn("_git_blob_sha", fn)
        self.assertIn("unchanged", fn)

    def test_06_uploader_requires_project_token(self):
        fn = _extract_func(BRIDGE_SRC, "_default_github_uploader", indent="    ")
        self.assertIn("get_project_github_token", fn)
        self.assertIn("PROJECT_GITHUB_TOKEN_MISSING", fn)

    def test_07_blob_sha_pure_python(self):
        # حساب git blob sha بدون استدعاء git binary (hashlib فقط)
        fn = _extract_func(BRIDGE_SRC, "_git_blob_sha", indent="    ")
        self.assertIn("hashlib", fn)
        self.assertNotIn("subprocess", fn)

    def test_08_p20_decision_documented_inline(self):
        fn = _extract_func(BRIDGE_SRC, "_default_github_uploader", indent="    ")
        self.assertIn("P20", fn)

    def test_09_p21_uploader_distinguishes_new_vs_modified(self):
        """🎯 [P21] عقد دقة التصنيف: ملف موجود على الريموت بمحتوى مختلف = modified،
        وملف غير موجود (404) = uploaded — ممنوع دمجهما في قائمة واحدة."""
        fn = _extract_func(BRIDGE_SRC, "_default_github_uploader", indent="    ")
        # قائمة modified مستقلة ومُهيأة
        self.assertIn("uploaded, modified, unchanged, deleted, skipped", fn)
        # التصنيف الشرطي عند نجاح الـ PUT حسب وجود remote_sha
        self.assertIn("(modified if remote_sha else uploaded).append(rel)", fn)
        # النتيجة تُرجع المفتاحين معاً
        self.assertIn('"modified": modified', fn)
        self.assertIn('"uploaded": uploaded', fn)

    def test_10_p21_github_sync_consumes_modified(self):
        """github_sync يقرأ modified من نتيجة التنفيذ ويمررها لرسالة تليجرام"""
        self.assertIn('modified = list(execution.get("modified", []) or [])', BRIDGE_SRC)
        # سطر الإحصائيات في رسالة تليجرام يعرض المعدل من نفس المفتاح
        self.assertIn("len(sync.get('modified', []))", BRIDGE_SRC)


# ═══════════════════════════════════════════════════════════════
# العقد الثاني: كشف DATA_RETENTION
# ═══════════════════════════════════════════════════════════════

class TestDataRetentionDetection(unittest.TestCase):
    """🧬 [P20] كشف خطأ AI Data Retention في detect_response_status"""

    def test_01_keywords_defined(self):
        self.assertTrue(hasattr(_bridge, "DATA_RETENTION_KEYWORDS"))
        self.assertGreaterEqual(len(_bridge.DATA_RETENTION_KEYWORDS), 3)

    def test_02_detects_basic_phrase(self):
        self.assertEqual(
            detect_response_status("This model requires AI Data Retention to be enabled."),
            "DATA_RETENTION",
        )

    def test_03_detects_turn_on_phrase(self):
        self.assertEqual(
            detect_response_status("Please turn on AI data retention in Settings → Data Controls"),
            "DATA_RETENTION",
        )

    def test_04_detects_inside_dict_response(self):
        resp = {"error": "requires AI data retention", "code": 400}
        self.assertEqual(detect_response_status(resp), "DATA_RETENTION")

    def test_05_priority_over_session_expired(self):
        # لو النص فيه إشارات جلسة + data retention → الأولوية للأكثر تحديداً
        mixed = "unauthorized — this model requires ai data retention to be enabled"
        self.assertEqual(detect_response_status(mixed), "DATA_RETENTION")

    def test_06_priority_over_credit_exhausted(self):
        mixed = "out of credits? no — requires ai data retention"
        self.assertEqual(detect_response_status(mixed), "DATA_RETENTION")

    def test_07_normal_completed_not_affected(self):
        long_ok = "تم بناء الموقع بنجاح ورفع الملفات، كل حاجة تمام " * 5
        self.assertEqual(detect_response_status(long_ok), "COMPLETED")

    def test_08_empty_still_empty(self):
        self.assertEqual(detect_response_status(None), "EMPTY")
        self.assertEqual(detect_response_status(""), "EMPTY")


# ═══════════════════════════════════════════════════════════════
# العقد الثاني: معالجة failover
# ═══════════════════════════════════════════════════════════════

class TestDataRetentionFailover(unittest.TestCase):
    """🧬 [P20] التبريد + الحساب التالي + نفس آخر رسالة + تنبيه مميز"""

    FAILOVER_SRC = _extract_func(BRIDGE_SRC, "send_message_and_make_public_with_auto_account_failover") \
        if re.search(r"^def send_message_and_make_public_with_auto_account_failover\(", BRIDGE_SRC, re.MULTILINE) \
        else _extract_func(BRIDGE_SRC, "send_message_with_auto_account_failover")

    def _dr_block(self) -> str:
        src = self.FAILOVER_SRC
        m = re.search(r'if status == "DATA_RETENTION":', src)
        assert m, "لم أجد كتلة معالجة DATA_RETENTION في حلقة الـ failover"
        return src[m.start():m.start() + 1200]

    def test_01_failover_handles_data_retention(self):
        self.assertIn('if status == "DATA_RETENTION":', self.FAILOVER_SRC)

    def test_02_cooldown_applied_like_credit_exhausted(self):
        block = self._dr_block()
        self.assertIn("mark_account_cooldown", block)
        self.assertIn("cooldown_hours", block)

    def test_03_continues_to_next_account(self):
        block = self._dr_block()
        self.assertIn("continue", block)

    def test_04_distinct_observer_notification(self):
        block = self._dr_block()
        self.assertIn("data-retention-blocked", block)

    def test_05_observer_label_registered(self):
        # التنبيه المميز مسجّل في خريطة أحداث المراقب
        self.assertIn('"data-retention-blocked"', BRIDGE_SRC)
        self.assertIn("Data Retention", BRIDGE_SRC)

    def test_06_resends_same_last_message_not_resume_prompt(self):
        # كتلة DATA_RETENTION تعمل continue بدون تعديل active_query
        # (بعكس مسار CREDIT_EXHAUSTED الذي يحوّل لبرومبت الاستئناف لاحقاً)
        block = self._dr_block()
        self.assertNotIn("get_bridge_cfg_runtime_resume_prompt", block)
        self.assertNotIn("active_query =", block)

    def test_07_polling_loop_treats_as_terminal(self):
        # حلقة while الرئيسية تعتبر DATA_RETENTION حالة نهائية توقف الانتظار
        m = re.search(r'while final_status not in \(([^)]*)\):', BRIDGE_SRC)
        self.assertIsNotNone(m, "لم أجد حلقة polling الرئيسية")
        self.assertIn("DATA_RETENTION", m.group(1))

    def test_08_terminal_describer_has_distinct_message(self):
        self.assertIn('"DATA_RETENTION": (', BRIDGE_SRC)
        self.assertIn("AI Data Retention", BRIDGE_SRC)
        self.assertIn("Data Controls", BRIDGE_SRC)


# ═══════════════════════════════════════════════════════════════
# تكامل bridge_refactor
# ═══════════════════════════════════════════════════════════════

class TestRefactorParityP20(unittest.TestCase):
    """🧬🔧 [P20] العقدان منعكسان في bridge_refactor (تقسيم حرفي)"""

    def test_01_refactor_has_data_retention(self):
        p05 = (webapp_dir / "bridge_refactor" / "parts" / "p05_project_tree.py").read_text(encoding="utf-8")
        self.assertIn("DATA_RETENTION_KEYWORDS", p05)

    def test_02_refactor_clean_of_git_native(self):
        for part in sorted((webapp_dir / "bridge_refactor" / "parts").glob("p*.py")):
            src = part.read_text(encoding="utf-8")
            self.assertNotIn("_git_native_sync_uploader", src, f"بقايا git native في {part.name}")
            self.assertNotIn("_generate_ai_commit_message", src, f"بقايا git native في {part.name}")

    def test_03_refactor_uploader_rest_only(self):
        p07 = (webapp_dir / "bridge_refactor" / "parts" / "p07_state_registry.py").read_text(encoding="utf-8")
        self.assertIn("_default_github_uploader", p07)
        self.assertIn("api.github.com/repos/", p07)


if __name__ == "__main__":
    unittest.main(verbosity=2)
