# -*- coding: utf-8 -*-
"""
[P14] اختبارات Upsert Sync + حارس الحذف + كشف الجذر الذكي
في 04_upload_to_Fable_github.py

يغطي جذور المشكلة الثلاثة:
1. الملف الموجود في الريبو والمعدل يجب أن يظهر ✏️ معدل (M) وليس ➕ جديد (A).
2. الأرشيف الجزئي يجب ألا يمسح ملفات الريبو (حارس نسبة الحذف 50%).
3. فرق CRLF/LF وحده أو المسار الداخلي الخاطئ لا يكسر التتبع.
"""
import importlib.util
import os
import shutil
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE_DIR, "04_upload_to_Fable_github.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("uploader04_p14", TARGET)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load_module()
with open(TARGET, "r", encoding="utf-8") as fh:
    SRC = fh.read()


def _write(base, rel, content, binary=False):
    path = os.path.join(base, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if binary else "w"
    kwargs = {} if binary else {"encoding": "utf-8", "newline": ""}
    with open(path, mode, **kwargs) as fh:
        fh.write(content)
    return path


class TestP14Constants(unittest.TestCase):
    """TSK-3201: ثوابت حارس الحذف."""

    def test_01_delete_guard_constants_exist(self):
        self.assertTrue(hasattr(MOD, "DELETE_GUARD_ENABLED"))
        self.assertTrue(hasattr(MOD, "DELETE_GUARD_MAX_DELETE_RATIO"))
        self.assertTrue(MOD.DELETE_GUARD_ENABLED)
        self.assertEqual(MOD.DELETE_GUARD_MAX_DELETE_RATIO, 0.5)


class TestP14ContentEqual(unittest.TestCase):
    """TSK-3203: مقارنة المحتوى (بايت + توحيد CRLF/LF)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p14_eq_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_02_identical_files_equal(self):
        a = _write(self.tmp, "a.txt", "hello\nworld\n")
        b = _write(self.tmp, "b.txt", "hello\nworld\n")
        self.assertTrue(MOD._files_content_equal(a, b))

    def test_03_crlf_vs_lf_considered_equal(self):
        a = _write(self.tmp, "a.txt", b"hello\r\nworld\r\n", binary=True)
        b = _write(self.tmp, "b.txt", b"hello\nworld\n", binary=True)
        self.assertTrue(MOD._files_content_equal(a, b))

    def test_04_different_content_not_equal(self):
        a = _write(self.tmp, "a.txt", "hello v1\n")
        b = _write(self.tmp, "b.txt", "hello v2\n")
        self.assertFalse(MOD._files_content_equal(a, b))

    def test_05_missing_file_not_equal(self):
        a = _write(self.tmp, "a.txt", "hello\n")
        self.assertFalse(MOD._files_content_equal(a, os.path.join(self.tmp, "nope.txt")))


class TestP14UpsertCopy(unittest.TestCase):
    """TSK-3203: Upsert — الملف المطابق لا يُلمَس، والمعدل يُستبدل."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p14_upsert_")
        self.src = os.path.join(self.tmp, "src")
        self.dst = os.path.join(self.tmp, "dst")
        os.makedirs(self.src)
        os.makedirs(self.dst)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_06_identical_file_not_touched(self):
        _write(self.src, "package.json", '{"name": "app"}\n')
        dst_file = _write(self.dst, "package.json", '{"name": "app"}\n')
        old_mtime = os.path.getmtime(dst_file) - 100
        os.utime(dst_file, (old_mtime, old_mtime))

        MOD.sync_tree(self.src, self.dst, mirror_delete=False)

        # mtime لم يتغير ➔ الملف لم يُنسخ فوقه (Git لن يرى M كاذب)
        self.assertEqual(os.path.getmtime(dst_file), old_mtime)

    def test_07_crlf_only_difference_not_touched(self):
        _write(self.src, "index.tsx", b"const x = 1;\r\n", binary=True)
        dst_file = _write(self.dst, "index.tsx", b"const x = 1;\n", binary=True)
        old_mtime = os.path.getmtime(dst_file) - 100
        os.utime(dst_file, (old_mtime, old_mtime))

        MOD.sync_tree(self.src, self.dst, mirror_delete=False)

        self.assertEqual(os.path.getmtime(dst_file), old_mtime)
        with open(dst_file, "rb") as fh:
            self.assertEqual(fh.read(), b"const x = 1;\n")  # لم يُستبدل بنسخة CRLF

    def test_08_modified_file_is_overwritten(self):
        _write(self.src, "app.py", "print('v2')\n")
        dst_file = _write(self.dst, "app.py", "print('v1')\n")

        MOD.sync_tree(self.src, self.dst, mirror_delete=False)

        with open(dst_file, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "print('v2')\n")

    def test_09_new_file_is_copied(self):
        _write(self.src, "new_module.py", "x = 1\n")
        MOD.sync_tree(self.src, self.dst, mirror_delete=False)
        self.assertTrue(os.path.isfile(os.path.join(self.dst, "new_module.py")))


class TestP14DeleteGuard(unittest.TestCase):
    """TSK-3204: حارس الحذف — الأرشيف الجزئي لا يمسح الريبو."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p14_guard_")
        self.src = os.path.join(self.tmp, "src")
        self.dst = os.path.join(self.tmp, "dst")
        os.makedirs(self.src)
        os.makedirs(self.dst)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_10_partial_archive_does_not_wipe_repo(self):
        """سيناريو saray2and2: أرشيف 4 ملفات مقابل ريبو 73 ملف ➔ صفر حذف."""
        # الريبو: 73 ملف
        repo_files = [f"src/module_{i:02d}.py" for i in range(69)]
        repo_files += ["package.json", "src/index.tsx", "README.md", "config.yml"]
        for rel in repo_files:
            _write(self.dst, rel, f"content of {rel}\n")

        # الأرشيف الجزئي: 4 ملفات فقط (2 موجودان، 2 جديدان)
        _write(self.src, "package.json", '{"name": "changed"}\n')
        _write(self.src, "src/index.tsx", "export default 2;\n")
        _write(self.src, "notes.md", "new\n")
        _write(self.src, "extra.txt", "new\n")

        MOD.sync_tree(self.src, self.dst, mirror_delete=True)

        # كل ملفات الريبو الـ73 ما زالت موجودة (الحارس أوقف المسح)
        for rel in repo_files:
            self.assertTrue(
                os.path.isfile(os.path.join(self.dst, rel)),
                f"الملف {rel} حُذف رغم حارس الحذف!"
            )
        # والملفات الجديدة نُسخت
        self.assertTrue(os.path.isfile(os.path.join(self.dst, "notes.md")))

    def test_11_full_archive_deletes_absent_files(self):
        """أرشيف كامل ينقصه ملف واحد ➔ يُحذف طبيعياً (نسبة الحذف < 50%)."""
        for i in range(10):
            _write(self.dst, f"f{i}.py", f"v{i}\n")
        for i in range(9):  # الأرشيف فيه 9 من 10
            _write(self.src, f"f{i}.py", f"v{i}\n")

        MOD.sync_tree(self.src, self.dst, mirror_delete=True)

        self.assertFalse(os.path.isfile(os.path.join(self.dst, "f9.py")))
        for i in range(9):
            self.assertTrue(os.path.isfile(os.path.join(self.dst, f"f{i}.py")))

    def test_12_git_dir_never_counted_or_deleted(self):
        _write(self.dst, ".git/config", "[core]\n")
        _write(self.dst, "a.py", "x\n")
        _write(self.src, "a.py", "x\n")

        MOD.sync_tree(self.src, self.dst, mirror_delete=True)

        self.assertTrue(os.path.isfile(os.path.join(self.dst, ".git", "config")))


class TestP14RootDetection(unittest.TestCase):
    """TSK-3202: كشف الجذر الذكي بمطابقة ملفات الريبو."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p14_root_")
        self.extract = os.path.join(self.tmp, "extracted")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.extract)
        os.makedirs(self.repo)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_13_nested_root_detected_by_repo_overlap(self):
        """أرشيف بمجلد متداخل عميق ➔ يُختار المستوى المطابق للريبو."""
        _write(self.repo, "package.json", "{}\n")
        _write(self.repo, "src/index.tsx", "x\n")
        _write(self.repo, "src/app.tsx", "y\n")

        # الجذر الصحيح على عمق 2: home/user/webapp/
        _write(self.extract, "home/user/webapp/package.json", "{}\n")
        _write(self.extract, "home/user/webapp/src/index.tsx", "x2\n")
        _write(self.extract, "home/user/webapp/src/app.tsx", "y2\n")

        best = MOD.detect_best_source_root(self.extract, self.repo)
        self.assertEqual(
            os.path.normpath(best),
            os.path.normpath(os.path.join(self.extract, "home", "user", "webapp"))
        )

    def test_14_empty_repo_falls_back_to_legacy(self):
        """ريبو فارغ ➔ fallback لسلوك get_source_root القديم."""
        _write(self.extract, "onlydir/a.py", "x\n")
        best = MOD.detect_best_source_root(self.extract, self.repo)
        legacy = MOD.get_source_root(self.extract)
        self.assertEqual(os.path.normpath(best), os.path.normpath(legacy))

    def test_15_call_site_after_clone_in_source(self):
        """في process_single_tar: كشف الجذر يأتي بعد git clone وليس قبله."""
        clone_pos = SRC.find('"git", "clone", "-b", REPO_BRANCH')
        detect_pos = SRC.find("source_root = detect_best_source_root(extract_dir, clone_dir)")
        self.assertGreater(clone_pos, 0, "أمر git clone غير موجود")
        self.assertGreater(detect_pos, 0, "استدعاء detect_best_source_root غير موجود")
        self.assertGreater(detect_pos, clone_pos, "كشف الجذر يجب أن يكون بعد الاستنساخ")
        # الاستدعاء القديم قبل الاستنساخ لم يعد موجوداً
        old_call = "source_root = get_source_root(extract_dir)"
        old_pos = SRC.find(old_call)
        if old_pos != -1:
            self.assertGreater(old_pos, clone_pos,
                               "بقايا الاستدعاء القديم قبل git clone")


class TestP14SecretsProtection(unittest.TestCase):
    """التأكد أن حماية الأسرار القديمة لم تنكسر بعد P14."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p14_sec_")
        self.src = os.path.join(self.tmp, "src")
        self.dst = os.path.join(self.tmp, "dst")
        os.makedirs(self.src)
        os.makedirs(self.dst)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_16_secret_files_still_never_copied(self):
        _write(self.src, ".env", "SECRET=1\n")
        _write(self.src, "accounts_qwen.json", "{}\n")
        _write(self.src, "safe.py", "x\n")

        MOD.sync_tree(self.src, self.dst, mirror_delete=False)

        self.assertFalse(os.path.isfile(os.path.join(self.dst, ".env")))
        self.assertFalse(os.path.isfile(os.path.join(self.dst, "accounts_qwen.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.dst, "safe.py")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
