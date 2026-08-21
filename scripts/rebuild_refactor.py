#!/usr/bin/env python3
"""
rebuild_refactor.py
===================
إعادة بناء bridge_refactor/ من الملف المرجعي 01.31_telegram_gen_bridge.py
بطريقة "التقسيم الأمين الحرفي" (Verbatim Faithful Split):

  - كل ملف جزء (part) هو قصّ نصي حرفي line-range من الأصل — بدون أي تعديل.
  - runtime.py ينفّذ الأجزاء بالترتيب داخل namespace موحّد
    (نفس دلالات الملف الواحد الأصلي تماماً).
  - واجهات (facades) لكل domain تعيد تصدير الرموز من الـ runtime.

النتيجة: 100% Feature Parity مضمونة لأن الكود المنفَّذ مطابق بايت-بايت.
"""
import ast
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).parent.parent.resolve()
SRC = ROOT / "01.31_telegram_gen_bridge.py"
OUT = ROOT / "bridge_refactor"

# ─── خريطة الأجزاء: (اسم الملف، أول سطر، آخر سطر، وصف) ───────
# الحدود مُختارة عند بدايات def/class top-level للحفاظ على السلامة النحوية.
PARTS = [
    ("p01_bootstrap",     1,   138, "Header + imports + logging + redact + html_escape + load_bot_token"),
    ("p02_config_contracts",   139,   442, "Global config + models + CONTRACTS + resume-prompt utils + project settings (P17: ALLOWED_GROUP_IDS + is_chat_allowed لدعم الجروبات)"),
    ("p03_engine_accounts",   443,   830, "Engine loader + account locks/claims + fingerprint + BridgeConfig + accounts I/O + readiness + cooldown + refresh_cookies_on_401"),
    ("p04_telegram_api",   831,  1198, "Telegram API core + send/edit + AccountSelection Live Renderer/Transport + send_document"),
    ("p05_project_tree",  1199,  1443, "projects_tree branches + finished flag + random account + detect_response_status (P20: DATA_RETENTION كنفاد رصيد) + P18: activity signature monitor (Deep Thinking / Tasks Remaining وقف فوري) + extract_project_id"),
    ("p06_engine_flow",  1444,  2393, "Archive safety/extraction + download_project_archive + make_project_always_public + get_public_forked_pid + send_message_and_make_public + send_message_with_auto_account_failover (P12: carry_pid resume + stream-interrupt | P13: pre-flight balance gate + LOW_BALANCE silent skip | P16: early make-public فور التقاط pid | P17: تجديد فوري للجلسة المنتهية -2 + بوابة رصيد بعد تجديد 401 أثناء الشات | P18: وقف فوري عند تغيّر مؤشر النشاط أثناء polling المتابعة)"),
    ("p07_state_registry",  2394,  3342, "EXECUTOR + user state + upload queue consts + ProjectRegistry (snapshots/checkpoints/github_sync | P20: الرفع REST-Only — إلغاء Git Native Sync نهائياً | P21: تصنيف دقيق جديد/معدل في uploader)"),
    ("p08_registry_index",  3343,  3651, "Project run locks + registry index I/O + identity + resume context + viewer URLs + live preview keyboard"),
    ("p09_github_dashboard",  3652,  4823, "GitHub inspection + dashboards + keyboards + project settings panels + finalize flows + resume decision + P19: copy_project_settings_to_new_project + generate_sequential_project_name + لوحة اختيار المصدر"),
    ("p10_progress_credit",  4824,  5104, "Stage artifacts + progress gate + credit checkpoint gate + terminal outcome describer"),
    ("p11_worker",  5105,  5409, "process_user_task_async (المشغل الكامل للمهمة)"),
    ("p12_handlers_main",  5410,  6390, "get_main_keyboard + handle_telegram_update + offset + polling + main (P17: بوابة is_chat_allowed للمسارين | P19: معالجات cmd:resume_copy_settings + cpysrc:)"),
]

# ─── خريطة الواجهات: facade module → أجزاء تُجمع رموزها ─────
FACADES = {
    "core/config.py":            (["p01_bootstrap", "p02_config_contracts"], "الإعدادات والثوابت وعقود الموديلات وأدوات resume prompt"),
    "core/logging_setup.py":     (["p01_bootstrap"], "التسجيل الملوّن + redact_email + html_escape"),
    "core/models.py":            (["p03_engine_accounts"], "BridgeConfig (النموذج التشغيلي لكل مهمة)"),
    "core/status.py":            (["p05_project_tree"], "كشف حالة الاستجابة واستخراج Project ID"),
    "core/security.py":          (["p06_engine_flow"], "فحوصات أمان الأرشيف والاستخراج الآمن"),
    "genspark/engine.py":        (["p03_engine_accounts", "p06_engine_flow"], "محرك Genspark: التحميل + الإرسال + make_public + الأرشفة + الـ failover"),
    "genspark/account_manager.py": (["p03_engine_accounts"], "إدارة الحسابات: readiness/claims/cooldown/refresh"),
    "telegram/messaging.py":     (["p04_telegram_api"], "طبقة رسائل تيليجرام + Live Renderer/Transport"),
    "telegram/handlers.py":      (["p12_handlers_main"], "معالجات التحديثات + الـ polling + الكيبوردات الرئيسية"),
    "telegram/ui.py":            (["p09_github_dashboard"], "الداشبورد والكيبوردات وشاشات إعدادات المشاريع"),
    "projects/registry.py":      (["p07_state_registry", "p08_registry_index"], "ProjectRegistry + فهرس الهوية + أقفال التشغيل"),
    "projects/tree.py":          (["p05_project_tree"], "شجرة الفروع projects_tree.json"),
    "git/github_sync.py":        (["p09_github_dashboard"], "فحص مستودعات GitHub وربط إعدادات المزامنة"),
    "workers/jobs.py":           (["p10_progress_credit", "p11_worker"], "مشغل المهام + بوابة الـ checkpoint + وصف النتائج النهائية"),
}

RUNTIME_TEMPLATE = '''"""
bridge_refactor.runtime
=======================
قلب النظام: يبني namespace تشغيلي موحّد بتنفيذ أجزاء الكود
(parts/p01..p12) بالترتيب — وهي قصّ حرفي line-range من الملف
المرجعي 01.31_telegram_gen_bridge.py بدون أي تعديل.

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
    mod.__file__ = str(BRIDGE_HOME / "01.31_telegram_gen_bridge.py")
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
'''

MAIN_TEMPLATE = '''#!/usr/bin/env python3
"""
bridge_refactor.main
====================
نقطة تشغيل البوت:
    python -m bridge_refactor.main
أو  python bridge_refactor/main.py
"""
import pathlib
import sys

# دعم التشغيل المباشر كملف (بدون -m)
if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.resolve()))
    from bridge_refactor import runtime
else:
    from . import runtime


if __name__ == "__main__":
    runtime.main()
'''

PKG_INIT = '''"""
bridge_refactor
===============
إعادة بناء معيارية أمينة (Faithful Modular Rebuild) للملف المرجعي
01.31_telegram_gen_bridge.py — راجع PARITY_REPORT.md للتفاصيل.

الاستخدام:
    from bridge_refactor import runtime      # الـ namespace الكامل
    from bridge_refactor.core import config   # واجهات الدومينات
"""
BUILD_SOURCE = "01.31_telegram_gen_bridge.py"
'''


def top_level_symbols(source: str) -> list[str]:
    """أسماء الرموز top-level (دوال/كلاسات/متغيرات) في مصدر بايثون."""
    tree = ast.parse(source)
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    names.append(tgt.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
    # الحفاظ على الترتيب مع إزالة التكرار
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def main():
    if not SRC.exists():
        sys.exit(f"الملف المرجعي غير موجود: {SRC}")
    lines = SRC.read_text(encoding="utf-8").splitlines(keepends=True)
    total = len(lines)
    print(f"المرجع: {SRC.name} — {total} سطر")

    # تحقق من تغطية كاملة بلا فجوات أو تداخل
    expected = 1
    for name, start, end, _ in PARTS:
        assert start == expected, f"فجوة/تداخل قبل {name}: متوقع {expected} وجدنا {start}"
        assert end >= start
        expected = end + 1
    assert expected - 1 == total, f"التغطية {expected-1} ≠ إجمالي الأسطر {total}"
    print("✅ خريطة الأجزاء تغطي الملف بالكامل بلا فجوات")

    # إزالة البناء القديم بالكامل (الملفات المرجعية في الجذر لا تُمس)
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "parts").mkdir(parents=True)

    part_symbols: dict[str, list[str]] = {}
    for name, start, end, desc in PARTS:
        chunk = "".join(lines[start - 1:end])
        header = (
            f'"""[VERBATIM SLICE] {name}\n'
            f"المصدر: 01.31_telegram_gen_bridge.py — الأسطر {start}..{end}\n"
            f"المحتوى: {desc}\n"
            f'⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py\n"""\n'
        )
        path = OUT / "parts" / f"{name}.py"
        path.write_text(header + chunk, encoding="utf-8")
        try:
            part_symbols[name] = top_level_symbols(chunk)
        except SyntaxError as e:
            sys.exit(f"❌ {name} غير سليم نحوياً: {e}")
        print(f"  📦 {name}.py  ({start}..{end}, {end-start+1} سطر, {len(part_symbols[name])} رمز)")

    (OUT / "parts" / "__init__.py").write_text(
        '"""أجزاء حرفية من الملف المرجعي — تُنفَّذ بالترتيب عبر runtime.py"""\n',
        encoding="utf-8",
    )

    (OUT / "__init__.py").write_text(PKG_INIT, encoding="utf-8")
    (OUT / "runtime.py").write_text(RUNTIME_TEMPLATE, encoding="utf-8")
    (OUT / "main.py").write_text(MAIN_TEMPLATE, encoding="utf-8")

    # ─── توليد الواجهات ───────────────────────────────────────
    for rel, (parts_list, desc) in FACADES.items():
        symbols: list[str] = []
        seen = set()
        for p in parts_list:
            for s in part_symbols[p]:
                if s not in seen and not s.startswith("__"):
                    seen.add(s)
                    symbols.append(s)
        mod_path = OUT / rel
        mod_path.parent.mkdir(parents=True, exist_ok=True)
        init_path = mod_path.parent / "__init__.py"
        if not init_path.exists():
            init_path.write_text(f'"""bridge_refactor.{mod_path.parent.name} — واجهة domain"""\n', encoding="utf-8")
        sym_lines = ",\n    ".join(symbols)
        content = (
            f'"""bridge_refactor.{rel[:-3].replace("/", ".")}\n'
            f"{desc}\n"
            f"واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها\n"
            f"الأجزاء: {', '.join(parts_list)}\n"
            f'"""\n'
            f"from bridge_refactor.runtime import ns as _ns\n\n"
            f"__all__ = [\n    "
            + ",\n    ".join(f'"{s}"' for s in symbols)
            + ",\n]\n\n"
            f"def __getattr__(name):\n"
            f"    if name in __all__:\n"
            f"        return getattr(_ns, name)\n"
            f"    raise AttributeError(name)\n\n"
            f"def __dir__():\n"
            f"    return sorted(__all__)\n"
        )
        _ = sym_lines
        mod_path.write_text(content, encoding="utf-8")
        print(f"  🔌 facade {rel} ({len(symbols)} رمز)")

    print("✅ اكتمل توليد bridge_refactor/")


if __name__ == "__main__":
    main()
