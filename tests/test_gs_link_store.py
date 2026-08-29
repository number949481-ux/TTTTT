# -*- coding: utf-8 -*-
"""
🔗 حراس gs_link_store — مخزن معرّفات مشاريع الشات (آخر 3 PIDs + owners)
=======================================================================
المخزن موجود بنسختين متطابقتين: `جديد/gs_link_store.py` و `الحماس/gs_link_store.py`
ويستهلكه المحركان 01.04 و 02.07 (import gs_link_store + push/get/drop/get_owner).

الحراس هنا بتغطي:
- تطابق بايت-ببايت بين النسختين (Parity).
- عقد الواجهة العامة (push_pid / get_pid / get_pids / get_owner / drop_pid).
- الرفض الحاسم للنصوص غير الصالحة (مثل __INVALID_PROJECT__).
- تطبيع الـ PID الباظ (مسافات داخلية) + Self-Heal للملف التالف.
- قصّ القائمة على MAX_KEEP=3 + عزل المفاتيح + سلامة القراءة من JSON تالف.

كل اختبار بيحمّل الموديول نسخة طازة على ملف مؤقت (GS_LINK_STORE) —
صفر لمس لأي ملف حقيقي وصفر شبكة.
"""
import importlib.util
import json
import os
import pathlib
import sys
import unittest
import tempfile
import uuid as _uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE_COPIES = [ROOT / "جديد" / "gs_link_store.py",
                ROOT / "الحماس" / "gs_link_store.py"]

_LOAD_SEQ = [0]


def _load_store(tmp_store_path: str, src: pathlib.Path | None = None):
    """تحميل نسخة طازة من الموديول على ملف مخزن مؤقت (بدون تلويث sys.modules)."""
    src = src or STORE_COPIES[0]
    _LOAD_SEQ[0] += 1
    name = f"_gs_link_store_test_{_LOAD_SEQ[0]}"
    old_env = os.environ.get("GS_LINK_STORE")
    os.environ["GS_LINK_STORE"] = tmp_store_path
    try:
        spec = importlib.util.spec_from_file_location(name, src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if old_env is None:
            os.environ.pop("GS_LINK_STORE", None)
        else:
            os.environ["GS_LINK_STORE"] = old_env
    sys.modules.pop(name, None)
    return mod


def _pid() -> str:
    return str(_uuid.uuid4())


class _StoreCase(unittest.TestCase):
    """قاعدة مشتركة: مخزن مؤقت جديد لكل اختبار."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.store_path = os.path.join(self._td.name, "gs_link_store.json")
        self.m = _load_store(self.store_path)


class TestParity(unittest.TestCase):
    """النسختان (جديد/ والحماس/) لازم يفضلوا بايت-ببايت متطابقين."""

    def test_copies_exist(self):
        for p in STORE_COPIES:
            with self.subTest(path=str(p)):
                self.assertTrue(p.exists(), f"نسخة المخزن مفقودة: {p}")

    def test_copies_byte_identical(self):
        contents = [p.read_bytes() for p in STORE_COPIES]
        self.assertEqual(contents[0], contents[1],
                         "جديد/gs_link_store.py و الحماس/gs_link_store.py اتفرّعوا — لازم مزامنة")


class TestPushGetDrop(_StoreCase):
    """الدورة الأساسية: push ➔ get ➔ drop."""

    def test_empty_store_returns_none(self):
        self.assertIsNone(self.m.get_pid())
        self.assertEqual(self.m.get_pids(), [])

    def test_push_then_get(self):
        pid = _pid()
        self.assertTrue(self.m.push_pid(pid))
        self.assertEqual(self.m.get_pid(), pid)
        self.assertEqual(self.m.get_pids(), [pid])

    def test_newest_first_and_dedup(self):
        p1, p2 = _pid(), _pid()
        self.m.push_pid(p1)
        self.m.push_pid(p2)
        self.assertEqual(self.m.get_pids(), [p2, p1])
        # إعادة دفع p1 يرفعه للمقدمة بدون تكرار
        self.m.push_pid(p1)
        self.assertEqual(self.m.get_pids(), [p1, p2])

    def test_max_keep_is_three(self):
        pids = [_pid() for _ in range(5)]
        for p in pids:
            self.m.push_pid(p)
        kept = self.m.get_pids()
        self.assertEqual(len(kept), 3)
        self.assertEqual(kept, list(reversed(pids))[:3])

    def test_drop_promotes_next(self):
        p1, p2 = _pid(), _pid()
        self.m.push_pid(p1)
        self.m.push_pid(p2)
        self.assertTrue(self.m.drop_pid(p2))
        self.assertEqual(self.m.get_pid(), p1)

    def test_drop_missing_returns_false(self):
        self.assertFalse(self.m.drop_pid(_pid()))

    def test_key_isolation(self):
        pa, pb = _pid(), _pid()
        self.m.push_pid(pa, key="acc_a@x.com")
        self.m.push_pid(pb, key="acc_b@x.com")
        self.assertEqual(self.m.get_pid(key="acc_a@x.com"), pa)
        self.assertEqual(self.m.get_pid(key="acc_b@x.com"), pb)
        self.assertIsNone(self.m.get_pid())  # default مش اتلمس


class TestValidation(_StoreCase):
    """الرفض الحاسم لأي نص غير UUID — أهمها __INVALID_PROJECT__."""

    def test_rejects_invalid_project_sentinel(self):
        self.assertFalse(self.m.push_pid("__INVALID_PROJECT__"))
        self.assertIsNone(self.m.get_pid())

    def test_rejects_junk(self):
        for junk in ("", None, 123, "not-a-uuid", "prj_660b714cee4f4184",
                     "12345678-1234-1234-1234"):
            with self.subTest(junk=junk):
                self.assertFalse(self.m.push_pid(junk))

    def test_normalizes_internal_whitespace(self):
        base = _pid()
        broken = base[:14] + " " + base[14:]  # مسافة جوّا النص زي الحالة الحقيقية
        self.assertTrue(self.m.push_pid(broken))
        self.assertEqual(self.m.get_pid(), base)

    def test_uppercase_normalized_to_lower(self):
        base = _pid()
        self.assertTrue(self.m.push_pid(base.upper()))
        self.assertEqual(self.m.get_pid(), base)


class TestOwner(_StoreCase):
    """خريطة _owners: صاحب الـ PID (أساس قفل الحساب في 01.04/02.07)."""

    def test_owner_roundtrip_lowercased(self):
        pid = _pid()
        self.m.push_pid(pid, owner="  Owner@Example.COM ")
        self.assertEqual(self.m.get_owner(pid), "owner@example.com")

    def test_owner_none_when_unset(self):
        pid = _pid()
        self.m.push_pid(pid)
        self.assertIsNone(self.m.get_owner(pid))

    def test_owner_removed_on_drop(self):
        pid = _pid()
        self.m.push_pid(pid, owner="a@b.c")
        self.m.drop_pid(pid)
        self.assertIsNone(self.m.get_owner(pid))

    def test_owner_lookup_tolerates_broken_pid_input(self):
        pid = _pid()
        self.m.push_pid(pid, owner="a@b.c")
        broken = pid[:8] + " " + pid[8:]
        self.assertEqual(self.m.get_owner(broken), "a@b.c")
        self.assertIsNone(self.m.get_owner("__INVALID_PROJECT__"))


class TestSelfHealAndSafety(unittest.TestCase):
    """🩹 Self-Heal للملف التالف + قراءة آمنة من JSON بايظ."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.store_path = os.path.join(self._td.name, "gs_link_store.json")

    def test_repairs_broken_pids_on_first_read(self):
        good = _pid()
        broken = good[:14] + " " + good[14:]
        pathlib.Path(self.store_path).write_text(json.dumps({
            "default": [broken, "__INVALID_PROJECT__"],
            "_owners": {broken: "Owner@X.com"},
        }), encoding="utf-8")
        m = _load_store(self.store_path)
        self.assertEqual(m.get_pids(), [good])
        self.assertEqual(m.get_owner(good), "owner@x.com")
        on_disk = json.loads(pathlib.Path(self.store_path).read_text(encoding="utf-8"))
        self.assertEqual(on_disk["default"], [good])

    def test_corrupt_json_reads_as_empty(self):
        pathlib.Path(self.store_path).write_text("{broken json!!", encoding="utf-8")
        m = _load_store(self.store_path)
        self.assertIsNone(m.get_pid())
        # ولسه ينفع نكتب بعد التلف
        pid = _pid()
        self.assertTrue(m.push_pid(pid))
        self.assertEqual(m.get_pid(), pid)

    def test_write_is_atomic_no_tmp_leftovers(self):
        m = _load_store(self.store_path)
        m.push_pid(_pid())
        leftovers = [f for f in os.listdir(self._td.name) if f.endswith(".tmp")]
        self.assertEqual(leftovers, [], "ملفات مؤقتة متسربة من الكتابة الذرية")


class TestEngineIntegrationContract(unittest.TestCase):
    """عقد التكامل: المحركات 01.04/02.07 بتستهلك نفس الواجهة الموجودة فعلاً."""

    ENGINES = [ROOT / "الحماس" / "01.04_Genspark_claude-opus-5-code.py",
               ROOT / "جديد" / "02.07_Genspark_claude-opus-5-code.py"]
    REQUIRED_CALLS = ("gs_link_store.get_pid", "gs_link_store.get_owner",
                      "gs_link_store.push_pid", "gs_link_store.drop_pid")

    def test_engines_use_only_existing_api(self):
        api = _load_store(os.path.join(tempfile.gettempdir(), "_contract_probe.json"))
        for eng in self.ENGINES:
            if not eng.exists():
                continue
            src = eng.read_text(encoding="utf-8")
            with self.subTest(engine=eng.name):
                for call in self.REQUIRED_CALLS:
                    self.assertIn(call, src, f"{eng.name} فقد استدعاء {call}")
                    fn = call.split(".")[1]
                    self.assertTrue(callable(getattr(api, fn, None)),
                                    f"الدالة {fn} مش موجودة في gs_link_store")

    def test_owner_lock_block_present(self):
        """قفل الحساب صاحب السياق (تكملة مباشرة بدون Fork) موجود في المحركين."""
        for eng in self.ENGINES:
            if not eng.exists():
                continue
            src = eng.read_text(encoding="utf-8")
            with self.subTest(engine=eng.name):
                self.assertIn("elif project_id and _store_owner:", src)
                self.assertIn("صاحب السياق المحفوظ", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
