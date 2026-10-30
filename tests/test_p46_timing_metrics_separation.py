# -*- coding: utf-8 -*-
"""
Tests for P46: Separation of Timing Metrics 360° (Zero Metrics Pollution)
Tests the isolated display of:
1. AI Generation Time (per productive account and continuations)
2. Local Prep & Archival Time (extract, scan, sha256)
3. GitHub Sync & Bulk Upload Time (Git Database API v5.4)
4. Total Wall-Clock Task Time
"""
import unittest
from types import SimpleNamespace

from bridge_refactor import runtime
p03_format = runtime.ns.format_account_timing_block

import importlib.util

spec = importlib.util.spec_from_file_location("main_bridge", "01.33_telegram_gen_bridge.py")
main_bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_bridge)
main_format = main_bridge.format_account_timing_block


class TestP46TimingMetricsSeparation(unittest.TestCase):

    def setUp(self):
        self.cfg = SimpleNamespace(
            account_journey_spans=[
                {"email": "bot1@example.com", "duration_seconds": 60.0},
                {"email": "bot2@example.com", "duration_seconds": 40.0},
            ],
            last_credit_continuations=1,
            project_fast_lean_skip=False,
            github_enabled=True,
            last_local_prep_seconds=12.5,
            last_github_sync_seconds=8.0,
            last_github_status="synced",
        )

    def test_full_isolated_metrics_display(self):
        """تأكيد ظهور الأسطر الثلاثة المنفصلة بنقاء تام دون أي تداخل."""
        res = p03_format(self.cfg, task_total_seconds=120.0)
        self.assertIn("🧠 <b>إجمالي زمن التوليد:</b>", res)
        self.assertIn("📦 <b>زمن الأرشفة والمعالجة المحلية:</b>", res)
        self.assertIn("🚀 <b>زمن المزامنة والرفع لـ GitHub:</b> 8s (منفصل تماماً)", res)
        self.assertIn("🕒 <b>الزمن الكلي للمهمة:</b> 2m", res)

    def test_fast_lean_skip_mode(self):
        """الوضع السريع: يظهر متخطى للأرشفة المحلية."""
        self.cfg.project_fast_lean_skip = True
        res = p03_format(self.cfg, task_total_seconds=105.0)
        self.assertIn("📦 <b>زمن الأرشفة والمعالجة المحلية:</b> متخطى (الوضع السريع)", res)

    def test_github_disabled(self):
        """عند تعطيل الرفع إلى GitHub يظهر سطر توضيحي."""
        self.cfg.github_enabled = False
        res = p03_format(self.cfg, task_total_seconds=100.0)
        self.assertIn("🚀 <b>زمن المزامنة والرفع لـ GitHub:</b> غير مفعل لهذا المشروع", res)

    def test_github_queued_in_background(self):
        """عند عمل المزامنة في الخلفية عبر طابور مستقل."""
        self.cfg.last_github_status = "queued"
        res = p03_format(self.cfg, task_total_seconds=100.0)
        self.assertIn("🚀 <b>زمن المزامنة والرفع لـ GitHub:</b> جاري في الخلفية (طابور مستقل)", res)

    def test_github_identical_no_changes(self):
        """عندما تكون الشجرة مطابقة تماماً للأصل دون أي تعديلات."""
        self.cfg.last_github_sync_seconds = 0.0
        res = p03_format(self.cfg, task_total_seconds=100.0)
        self.assertIn("🚀 <b>زمن المزامنة والرفع لـ GitHub:</b> مطابق للأصل (لا تغييرات)", res)

    def test_parity_between_p03_and_main_bridge(self):
        """تطابق كامل بين الوحدة المقسمة والسكريبت الرئيسي 01.33."""
        out_p03 = p03_format(self.cfg, task_total_seconds=120.5)
        out_main = main_format(self.cfg, task_total_seconds=120.5)
        self.assertEqual(out_p03, out_main)


if __name__ == "__main__":
    unittest.main()
