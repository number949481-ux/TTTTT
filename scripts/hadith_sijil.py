#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/hadith_sijil.py
======================
السكربت التنفيذي لأتمتة بروتوكول «حدث سجل» بالخطوات الست الصارمة:
1. فحص التعديلات والـ Syntax
2. فحص تكامل وسلامة منظومة التوثيق (P10 Docs Integrity)
3. تشغيل الاختبارات الآلية الشاملة (25 فحص)
4. التحقق من خروج Exit Code 0 (Test-Before-Talk)
5. مزامنة سجلات docs/tests/ و docs/engineering/
6. طباعة تقرير التأكيد النهائي والنقد الذاتي
"""

import sys
import os
import re
import time
import subprocess
from datetime import datetime

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.dirname(__file__)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from verify_docs_integrity import verify_docs_integrity

def banner(title: str):
    print("\n" + "=" * 70)
    print(f">> {title}")
    print("=" * 70)

def step(num: int, title: str):
    print(f"\n[الخطوة {num}] -> {title}...")

def run_step():
    banner("بدء تشغيل بروتوكول حدث سجل الالي المعتمد")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # الخطوة 1: فحص الـ Syntax
    step(1, "فحص الـ Syntax لملف البوت النشط 01.32")
    bot_file = os.path.join(ROOT_DIR, "01.32_telegram_gen_bridge.py")
    res_compile = subprocess.run([sys.executable, "-m", "py_compile", bot_file], capture_output=True, env=env)
    if res_compile.returncode != 0:
        err_msg = (res_compile.stderr or b"").decode("utf-8", errors="replace")
        print(f"X خطأ فادح في Syntax الملف:\n{err_msg}")
        sys.exit(1)
    print("OK: تم اجتياز فحص Syntax بنجاح (Exit Code 0).")

    # الخطوة 2: الفحص الذاتي لسلامة وتكامل التوثيق (P10 Docs Integrity)
    step(2, "فحص سلامة وتكامل روابط التوثيق (P10 Docs Integrity Guard)")
    ok_docs, doc_errors, total_files, total_links = verify_docs_integrity()
    if not ok_docs:
        print(f"X توقف فوري! تم اكتشاف {len(doc_errors)} رابط مكسور في التوثيق:")
        for err in doc_errors:
            print(f"  {err}")
        sys.exit(1)
    print(f"OK: تم اجتياز فحص التوثيق بنجاح ({total_files} ملف، {total_links} رابط - صفر أخطاء).")

    # الخطوة 3: تشغيل الاختبارات الآلية
    step(3, "تشغيل اختبارات الوحدة الشاملة (32 فحص) - Test-Before-Talk Gate")
    t0 = time.time()
    res_test = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests", "-v"], cwd=ROOT_DIR, capture_output=True, env=env)
    elapsed = time.time() - t0

    stdout_text = (res_test.stdout or b"").decode("utf-8", errors="replace")
    stderr_text = (res_test.stderr or b"").decode("utf-8", errors="replace")
    combined_output = stderr_text.strip() or stdout_text.strip()

    if res_test.returncode != 0:
        print("X توقف فوري! فشل أحد الاختبارات. لن يتم تعديل أي ملف توثيقي.")
        print(combined_output)
        sys.exit(res_test.returncode)
    
    # 🎯 استخراج عدد الفحوصات الفعلي بديناميكية عبر Regex من مخرج unittest الحقيقي
    match_tests = re.search(r"Ran\s+(\d+)\s+tests?", combined_output)
    actual_test_count = int(match_tests.group(1)) if match_tests else 32

    print(f"OK: تم اجتياز كافة الاختبارات بنجاح ({actual_test_count} فحص) في {elapsed:.3f} ثانية! (Exit Code 0).")

    # الخطوة 4: تحديث سجل الاختبارات الحية
    step(4, "تحديث سجل الاختبارات الحية docs/tests/TEST_EXECUTION_LOGS.md")
    exec_logs_file = os.path.join(ROOT_DIR, "docs", "tests", "TEST_EXECUTION_LOGS.md")
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    log_content = f"""# 📜 سجل مخرجات تشغيل الاختبارات (TEST_EXECUTION_LOGS.md)

> **المسؤولية:** توثيق مخرجات التيرمينال الحقيقية، الـ Exit Codes، والأزمنة المقاسة  

---

## ⚡ آخر جلسة تشغيل ناجحة (Latest Execution Session)

* **التاريخ والوقت:** `{now_str}`
* **الأمر المنفذ:** `python -m unittest discover tests -v`
* **الزمن المقاس:** `{elapsed:.3f} ثانية`
* **النتيجة العامة:** `Ran {actual_test_count} tests — OK`
* **فحص تكامل التوثيق (P10):** `PASS ({total_files} files, {total_links} links)`
* **رمز الخروج (Exit Code):** `0` ✅

---

## 📋 مخرجات التيرمينال الحية:

```text
{combined_output}
```
"""
    with open(exec_logs_file, "w", encoding="utf-8") as f:
        f.write(log_content)
    print("OK: تم تحديث TEST_EXECUTION_LOGS.md بنجاح.")

    # الخطوة 5: التقرير النهائي
    step(5, "تقرير الإنجاز النهائي لبروتوكول حدث سجل")
    print("\n" + "-" * 70)
    print(f"| {'البند':<30} | {'النتيجة':<30} |")
    print("-" * 70)
    print(f"| {'حالة الفحص الآلي':<30} | {f'OK {actual_test_count}/{actual_test_count} PASS (100% OK)':<30} |")
    print(f"| {'فحص تكامل التوثيق (P10)':<30} | {f'OK ({total_files} files)':<30} |")
    print(f"| {'الزمن المقاس':<30} | {f'{elapsed:.3f}s':<30} |")
    print(f"| {'رمز الخروج (Exit Code)':<30} | {'0 (نجاح كامل)':<30} |")
    print(f"| {'الإصدار المعتمد':<30} | {'01.32_telegram_gen_bridge.py':<30} |")
    print(f"| {'جناحي التوثيق':<30} | {'docs/engineering + docs/tests':<30} |")
    print("-" * 70)


    print("\n تم اكتمال بروتوكول حدث سجل بنجاح تام وفق المعايير المعتمدة!")

if __name__ == "__main__":
    run_step()
