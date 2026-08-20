# 🧪 خطة ضمان الجودة الشاملة (QA_MASTER_PLAN.md)

> **المسؤولية:** تعريف سياسات الجودة، بوابات الاختبارات، واستراتيجية عدم التراجع (Zero-Regression Strategy)  

---

## 🏛️ 1. المبادئ الأساسية لضمان الجودة (QA Core Principles)
1. **قاعدة Test-Before-Talk:** ممنوع ادعاء نجاح أي ميزة أو إغلاق أي مهمة بدون تشغيل الاختبارات الآلية والخروج بـ Exit Code 0.
2. **عزل زمن الاختبارات:** الاختبارات وحدوية خالصة تعمل محلياً دون أي اعتماديات شبكية معقدة بزمن < 0.02s.
3. **حماية التوافق الخلفي:** كل ترقية جديدة يجب ألا تكسر مسارات الموديلات السابقة أو تنسيقات الـ JSON.

---

## 📊 2. بوابات الجودة الإلزامية (Quality Gates)

```
[كتابة الكود] ➔ [بوابة 1: فحص Syntax] ➔ [بوابة 2: اختبارات 24/24] ➔ [بوابة 3: التوثيق] ➔ [بوابة 4: Git Commit]
```

* **بوابة 1 (Syntax Gate):** `python -m py_compile 01.24_telegram_gen_bridge.py`
* **بوابة 2 (Unit & Regression Gate):** `python -m unittest discover tests -v`
* **بوابة 3 (Docs Sync Gate):** مطابقة `PROGRESS.md` و `TRACEABILITY_MATRIX.md`.
* **بوابة 4 (Commit Gate):** تسجيل الـ Closed Commit برقم الـ Task.
