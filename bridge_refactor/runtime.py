"""
bridge_refactor.runtime
=======================
قلب النظام: يبني namespace تشغيلي موحّد بتنفيذ أجزاء الكود
(parts/p01..p12) بالترتيب — وهي قصّ حرفي line-range من الملف
المرجعي 01.32_telegram_gen_bridge.py بدون أي تعديل.

بهذا التصميم:
  - الدلالات (semantics) مطابقة 100% للملف الأصلي الأحادي.
  - كل part موثّق بمداه السطري في الأصل لسهولة المراجعة والتدقيق.
  - الواجهات (core/, genspark/, telegram/, projects/, git/, workers/)
    تعيد تصدير الرموز من هذا الـ namespace.

BRIDGE_HOME: مجلد العمل (حيث accounts_genspark.json والمحرك 01.03
و telegram_offset.txt و project_registry/) — افتراضياً المجلد الأب
لحزمة bridge_refactor، ويمكن تخصيصه عبر متغير البيئة BRIDGE_HOME.
"""
import os
import pathlib
import sys
import types

_PKG_DIR = pathlib.Path(__file__).parent.resolve()
_PARTS_DIR = _PKG_DIR / "parts"

BRIDGE_HOME = pathlib.Path(os.getenv("BRIDGE_HOME", str(_PKG_DIR.parent))).resolve()

_NS_NAME = "bridge_refactor._bridge_ns"


def _build_namespace() -> types.ModuleType:
    """تنفيذ كل الأجزاء بالترتيب داخل module واحد مشترك."""
    mod = types.ModuleType(_NS_NAME)
    # __file__ افتراضي داخل BRIDGE_HOME حتى يبقى SCRIPT_DIR في الأصل
    # (pathlib.Path(__file__).parent) مشيراً لمجلد العمل الصحيح.
    mod.__file__ = str(BRIDGE_HOME / "01.32_telegram_gen_bridge.py")
    sys.modules[_NS_NAME] = mod
    part_files = sorted(_PARTS_DIR.glob("p*.py"))
    if not part_files:
        raise RuntimeError(f"لا توجد أجزاء داخل {_PARTS_DIR}")
    for part in part_files:
        source = part.read_text(encoding="utf-8")
        code = compile(source, str(part), "exec")
        exec(code, mod.__dict__)
    return mod


ns = _build_namespace()


def __getattr__(name: str):
    """تفويض الوصول لأي رمز غير معروف إلى الـ namespace الموحّد."""
    try:
        return getattr(ns, name)
    except AttributeError:
        raise AttributeError(f"module 'bridge_refactor.runtime' has no attribute {name!r}") from None


def main():
    """نقطة الدخول الرسمية — مطابقة لـ main() في الملف الأصلي."""
    return ns.main()
