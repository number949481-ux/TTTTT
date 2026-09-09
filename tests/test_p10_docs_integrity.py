#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p10_docs_integrity.py
===============================
اختبارات وحدة للتحقق من أداة سلامة التوثيق (P10 Docs Integrity Guard)
"""

import unittest
import os
import sys

# إضافة مجلد scripts للاستيراد
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from verify_docs_integrity import verify_docs_integrity

class TestDocsIntegrityP10(unittest.TestCase):
    def test_docs_integrity_no_broken_links(self):
        """التحقق من عدم وجود أي روابط مكسورة في منظومة docs بأكملها"""
        ok, errors, total_files, total_links = verify_docs_integrity()
        self.assertTrue(ok, f"تم العثور على روابط مكسورة: {errors}")
        self.assertEqual(len(errors), 0)
        self.assertGreaterEqual(total_files, 20, "يجب مسح 20 ملفاً توثيقياً على الأقل")

if __name__ == "__main__":
    unittest.main()
