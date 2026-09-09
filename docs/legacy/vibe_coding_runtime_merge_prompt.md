# 🏛️ برومت Vibe Coding — دمج `runtime/` داخل `01.25_telegram_gen_bridge.py`
# (Single-File Doctrine — Zero-Regression — Read-Before-Touch)

---

## 🎯 الهدف الوحيد من هذا الطلب:

دمج كود ملف `runtime/model_runtime.py` بشكل صحيح ومباشر داخل ملف `01.25_telegram_gen_bridge.py`، ثم تعديل ملفات الاختبارات لتستورد منه مباشرةً، ثم حذف مجلد `runtime/` نهائياً.

**النتيجة المطلوبة:**
- الملف `01.25_telegram_gen_bridge.py` يحتوي على كل منطق الموديلات بشكل موحد (SSOT).
- ملفات الاختبارات تشتغل وتعطي `32/32 PASS` بدون تغيير أي سطر من اختبارات الـ assertions نفسها.
- `runtime/` يُحذف ولا يُرفع للريبو.

---

## 🚨 القيود الصارمة (NON-NEGOTIABLE — لا تُكسر أبداً):

1. **❌ ممنوع تغيير أي signature دالة موجودة** في `01.25_telegram_gen_bridge.py` — حتى ولو بدت مشابهة.
2. **❌ ممنوع حذف أي سطر كود** من `01.25` ما لم يكن تكراراً حرفياً بالضبط لما ستضيفه.
3. **❌ ممنوع دمج أو دمج جزئي** — إما يبقى الكود في مكانه كاملاً أو يُحذف كاملاً.
4. **❌ ممنوع تغيير أي assertion** داخل ملفات الاختبارات — فقط استبدال سطر الـ import.
5. **✅ إلزامي: تشغيل الاختبارات وتأكيد `Ran 32 tests — OK`** قبل اعتبار المهمة مكتملة.

---

## 📋 خطة التنفيذ (خطوة بخطوة — لا تتجاوز أي خطوة):

### الخطوة 1 — اقرأ الملفات التالية بالكامل قبل أي تعديل:

```
# ملفات إلزامية للقراءة قبل البدء:
1. runtime/model_runtime.py          ← الكود المراد دمجه (116 سطر)
2. 01.25_telegram_gen_bridge.py      ← السطر 160-215 فقط (الـ model constants الموجودة)
3. tests/test_p2_model_routing.py    ← كامل (سطر الـ import + الـ assertions)
4. tests/test_p3_regression.py       ← كامل (سطر الـ import فقط)
```

---

### الخطوة 2 — التحليل الإلزامي قبل أي تعديل:

قبل ما تلمس أي ملف، أجب على هذه الأسئلة الأربعة:

**Q1:** هل `CONTRACTS` و `apply_contract` موجودة بالفعل في `01.25_telegram_gen_bridge.py`؟
- ➡️ ابحث عن كلمة `CONTRACTS` في `01.25` — لو الجواب **لأ (غير موجود)** → ستضيفهم.
- لو الجواب **أيوه (موجود)** → قارن السطور بالضبط قبل أي إجراء.

**Q2:** هل `is_protected` موجودة في `01.25`؟
- ➡️ ابحث عن `def is_protected` في `01.25`.

**Q3:** ما الفرق بين `ALIASES` في `runtime/` و `MODEL_ALIASES` في `01.25`؟
- ➡️ قارن المحتوى حرفياً — الجداول هل بياناتها متطابقة أم ناقصة في أحدهما؟

**Q4:** ما القيم الدقيقة في `CONTRACTS` في `runtime/`؟
```python
CONTRACTS = {
    "claude-fable-5":  (["gpt-4.1"],         "claude-fable-5",  None,              True),
    "claude-opus-5":   (["claude-opus-5"],    "claude-opus-5",   None,              True),
    "claude-sonnet-5": (["claude-sonnet-5"],  "claude-sonnet-5", "claude-sonnet-5", True),
    "gpt-5.6-sol":     (["gpt-5.6-sol"],      "gpt-5.6-sol",     "gpt-5.6-sol",     True),
    "kimi-k3":         (["kimi-k3"],          "kimi-k3",         "kimi-k3",         True),
}
```

---

### الخطوة 3 — التعديلات المطلوبة بالترتيب:

#### [التعديل A] في `01.25_telegram_gen_bridge.py`:

بعد سطر `MODEL_ALIASES = {...}` (تقريباً السطر 197)، وقبل `def normalize_project_model(...)`:

**أضف** الكود التالي فقط لو غير موجود بالفعل (افحص أولاً):

```python
# ── عقود الموديلات (CONTRACTS) — SSOT موحد ──────────────────────────────
# model_slug → (models_list, use_model, ai_chat_model, inject_msg_id)
CONTRACTS = {
    "claude-fable-5":  (["gpt-4.1"],          "claude-fable-5",  None,              True),
    "claude-opus-5":   (["claude-opus-5"],     "claude-opus-5",   None,              True),
    "claude-sonnet-5": (["claude-sonnet-5"],   "claude-sonnet-5", "claude-sonnet-5", True),
    "gpt-5.6-sol":     (["gpt-5.6-sol"],       "gpt-5.6-sol",     "gpt-5.6-sol",     True),
    "kimi-k3":         (["kimi-k3"],           "kimi-k3",         "kimi-k3",         True),
}


def is_protected(model: str | None) -> bool:
    """التحقق مما إذا كان الموديل ينتمي للمسار الخاص المحمي (gpt-5.5 / claude-opus-4-8)"""
    m = str(model or "").strip().lower()
    return m in PROTECTED_MODELS or MODEL_ALIASES.get(m) in PROTECTED_MODELS


def apply_contract(payload: dict, model: str | None, msg_id: str | None = None) -> dict:
    """
    تطبيق عقد الموديل على الـ payload وإرجاع dict دائمًا.
    - موديل محمي → no-op (payload بدون تعديل).
    - موديل معروف → يحقن: models, use_model, ai_chat_model, client_message_id.
    - موديل مجهول → يضع models=[m] فقط.
    """
    m = str(model or "").strip().lower()
    canonical = MODEL_ALIASES.get(m, m)

    if canonical in PROTECTED_MODELS:
        log_event("warning", f"[ROUTING BUG] Protected model '{model}' reached generic apply_contract adapter")
        return payload

    c = CONTRACTS.get(canonical)
    if not c:
        payload["models"] = [canonical] if canonical else [DEFAULT_PROJECT_MODEL]
        log_event("warning", f"No contract for model '{model}', fallback models only")
        return payload

    models, use_model, ai_chat, needs_id = c
    payload["models"] = list(models)
    if use_model:
        payload["use_model"] = use_model
    if ai_chat:
        payload["ai_chat_model"] = ai_chat
    if needs_id and msg_id:
        payload["client_message_id"] = msg_id

    return payload
# ──────────────────────────────────────────────────────────────────────────
```

> ⚠️ **ملاحظة:** استخدام `log_event(...)` بدل `logger.warning(...)` لأن `01.25` يستخدم `log_event` كـ helper خاص — لا تستورد `logging` من جديد.

---

#### [التعديل B] في `tests/test_p2_model_routing.py`:

**فقط** استبدل سطر الـ import (السطر 9):

```python
# قبل (BEFORE):
from runtime.model_runtime import apply_contract, normalize_project_model, is_protected, PROTECTED_MODELS

# بعد (AFTER):
import importlib.util
_bridge_spec = importlib.util.spec_from_file_location("bridge_mod", webapp_dir / "01.25_telegram_gen_bridge.py")
_bridge = importlib.util.module_from_spec(_bridge_spec)
_bridge_spec.loader.exec_module(_bridge)
apply_contract = _bridge.apply_contract
normalize_project_model = _bridge.normalize_project_model
is_protected = _bridge.is_protected
PROTECTED_MODELS = _bridge.PROTECTED_MODELS
```

---

#### [التعديل C] في `tests/test_p3_regression.py`:

**فقط** استبدل سطر الـ import (السطر 13):

```python
# قبل (BEFORE):
from runtime.model_runtime import apply_contract, normalize_project_model, is_protected

# بعد (AFTER):
apply_contract = bridge.apply_contract
normalize_project_model = bridge.normalize_project_model
is_protected = bridge.is_protected
```

> ملاحظة: `bridge` هو المتغير الموجود بالفعل في الـ module-level imports في `test_p3_regression.py`.

---

### الخطوة 4 — التحقق الإلزامي (Test-Before-Talk Gate):

```bash
# شغّل من مجلد W___webapp بالضبط:
python -m unittest discover tests -v

# النتيجة المطلوبة الوحيدة المقبولة:
# Ran 32 tests in X.XXXs
# OK
# (Exit Code = 0)
```

**❌ لو الناتج أي حاجة غير كده** → توقف فوراً، لا ترفع أي كود، ابلّغ بالمشكلة والـ traceback الكامل.

---

### الخطوة 5 — الحذف النهائي لـ `runtime/`:

فقط بعد نجاح `32/32 PASS`:

```bash
# احذف المجلد نهائياً من الـ working tree والـ git index:
git rm -r runtime/
git commit -m "refactor: migrate runtime/model_runtime.py into 01.25 core — Single-File Doctrine v16"
```

---

## 🔍 Checklist النهائي قبل الرفع:

```
[ ] CONTRACTS موجود في 01.25 بنفس القيم الحرفية الموجودة في runtime/model_runtime.py
[ ] is_protected موجود في 01.25 ويشتغل صح مع PROTECTED_MODELS
[ ] apply_contract موجود في 01.25 بنفس المنطق الحرفي
[ ] test_p2_model_routing.py يستورد من 01.25 لا من runtime/
[ ] test_p3_regression.py يستورد من bridge (01.25) لا من runtime/
[ ] python -m unittest discover tests -v → Ran 32 tests — OK (Exit Code 0)
[ ] runtime/ محذوف من الـ git tree
[ ] لم يُضف أي import جديد غير ضروري
[ ] لم تتغير أي signature دالة موجودة في 01.25
```

---

## 📁 ملاحظة للوكيل عن بنية المشروع:

```
W___webapp/
├── 01.25_telegram_gen_bridge.py   ← الملف الأساسي الوحيد (مسار الدمج)
├── 01.02Genspark_claude-opus-5-code.py
├── requirements.txt
├── runtime/
│   ├── __init__.py
│   └── model_runtime.py           ← يُحذف بعد الدمج
├── tests/
│   ├── test_p1_github_branches.py
│   ├── test_p2_model_routing.py   ← يتعدل Import فقط
│   ├── test_p3_regression.py      ← يتعدل Import فقط
│   ├── test_p7_live_preview.py
│   └── test_p10_docs_integrity.py
├── scripts/
│   └── hadith_sijil.py
└── docs/
```
