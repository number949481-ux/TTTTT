# 🏛️ وثيقة الخطة الهندسية المعمارية الشاملة — دمج المعزل الثلاثي والهدية المتأخرة والمترجم
## Comprehensive Tri-State Architecture, SRE Fortification & Compiler Parity Plan (v2.0)

> **الموقع:** `bridge_refactor_31/00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_PLAN.md`  
> **الملف الشقيق للملاحظات:** [`00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_NOTES.md`](file:///d:/SMS/.hRhRhRhRhRhR/..............................................................................................................%D8%B4%D8%BA%D9%84%20%D9%81%D8%B1%D9%8A%D9%82/Genspark/W___webapp/bridge_refactor_31/00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_NOTES.md)  
> **الهوية الإلزامية:** Lead Architect & DevOps/Security Inspector /SRE (`00-architect-sre`)  
> **الدستور الحاكم:** دستور بولا الهندسي v1.2 (`00-bolla-constitution`) + الصمامات الـ 86 الميدانية (`00-architect-sre`)  
> **وضع العمل:** 🛑 وضع التخطيط الصارم `[PLANNING]` — حظر تام لأي تعديل تنفيذي قبل صدور موافقة "GO" الصريحة.

---

## 📊 لوحة المتابعة ونسبة الإنجاز (Progress & State Dashboard)

| المرحلة | الوصف الهندسي | النطاق والمستوى | الحالة الحالية | المخرجات المتوقعة |
|---|---|:---:|:---:|---|
| **Phase 0** | التجميد التشفيري والمرساة وحصر خطوط الأساس | 🟢 T0 | ⏳ بانتظار الاعتماد | `.anchor` + بصمات SHA-256 في `ANCHORS.md` |
| **Phase 1** | بناء حزمة الاختبارات المعزولة مسبقاً (Pre-Lab) | 🟢 T0 (Tests) | ⏳ قيد التخطيط | `tests/test_tri_state_isolation.py` (5 اختبارات) |
| **Phase 2** | ترقية محرك الفحص والقص والنقل الذري | 🟡 T1 | ⏳ قيد التخطيط | `genspark_verifier_engine.py` (عزل وقص 100%) |
| **Phase 3** | دمج الفحص المسبق والهدية وسحب الحسابات بالجسر | 🔴 T2 | ⏳ قيد التخطيط | `01.33_telegram_gen_bridge.py` (فحص حي + تبريد 29h) |
| **Phase 4** | استئصال التخمين الأعمى وتثبيت الرصيد الحي بالمحرك | 🟡 T1 | ⏳ قيد التخطيط | `01.03Genspark_claude-opus-5-code.py` (حذف الرصيد المفترض) |
| **Phase 5** | إعادة معايرة وإطلاق "المترجم" وفحص التطابق | 🔴 T2 | ⏳ قيد التخطيط | `scripts/rebuild_refactor.py` (Parity 11/11) |
| **Phase 6** | فحص الإثبات الميداني الشامل (Test-Before-Talk) | 🟢 T0 | ⏳ بانتظار التنفيذ | `pytest` + `hadith_sijil.py` خالي من الأخطاء |
| **Phase 7** | المزامنة الدستورية لدفاتر النواة والسجلات | 🟢 T0 | ⏳ بانتظار الإغلاق | `Root/ai_state.json` + `PROGRESS.md` + `tasks.md` |

**الحالة العامة للخطة:** 📝 **معتمدة ومفصلة هندسياً 100% — بانتظار إشارة "GO" للانتقال لوضع التنفيذ `[EXECUTE]`.**

---

## 🎯 سجل المهام التفاعلي التتابعي (Interactive Tasks Checklist)

### 🔹 المرحلة 0: التحصين التشفيري وحصر خطوط الأساس (Crypto Anchors)
- [ ] `TASK-001`: أخذ نسخة مرساة مشفرة لكل ملف مستهدف:
  - `genspark_verifier_engine.py.anchor`
  - `01.33_telegram_gen_bridge.py.anchor`
  - `01.03Genspark_claude-opus-5-code.py.anchor`
  - `scripts/rebuild_refactor.py.anchor`
- [ ] `TASK-002`: حساب بصمات SHA-256 قبل أي تعديل وتدوينها في [`Root/ANCHORS.md`](file:///d:/SMS/.hRhRhRhRhRhR/Root/ANCHORS.md) (دستور بولا - القانون 1 و 9).
- [ ] `TASK-003`: تأكيد عدم وجود أي تغييرات غير ملتزمة في `git status`.

### 🔹 المرحلة 1: بناء حزمة الاختبارات المسبقة (Pre-Lab TDD Suite)
- [ ] `TASK-101`: إنشاء ملف الاختبار المعزول [`tests/test_tri_state_isolation.py`](file:///d:/SMS/.hRhRhRhRhRhR/..............................................................................................................%D8%B4%D8%BA%D9%84%20%D9%81%D8%B1%D9%8A%D9%82/Genspark/W___webapp/bridge_refactor_31/tests/test_tri_state_isolation.py).
- [ ] `TASK-102`: كتابة اختبار القص والنقل الذري `test_atomic_cut_and_move` (التأكد أن الحساب يضاف في ملف المعزل ويُحذف ذرياً من الملف الأساسي بلا فقد ولا تكرار).
- [ ] `TASK-103`: كتابة اختبار عتبة الهدية `test_gift_freshness_threshold` (فحص حالة $> 14$ يوماً كـ `STALE` مقابل $\le 14$ يوماً كـ `HEALTHY`).
- [ ] `TASK-104`: كتابة اختبار صمام حماية أخطاء الشبكة `test_transient_error_immunity` (التأكد بنسبة 100% أن أخطاء 500 و 502 و 504 و Timeout لا ترمي الحساب في `accounts_failed.json`).
- [ ] `TASK-105`: كتابة اختبار أمان التزامن والأقفال `test_vault_concurrency_locks` تحت ثريدات موازية.
- [ ] `TASK-106`: تشغيل الاختبارات مسبقاً وتأكيد فشلها الطبيعي (Red Stage) قبل تعديل الكود التشغيلي.

### 🔹 المرحلة 2: ترقية محرك الفحص والقص والنقل الذري (`genspark_verifier_engine.py`)
- [ ] `TASK-201`: استبدال اسم ملف العزل الطويل القديم بثوابت الملفات الثلاثة المعتمدة:
  - `FAILED_ACCOUNTS_FILENAME = "accounts_failed.json"`
  - `DELAYED_GIFTS_FILENAME = "accounts_delayed_gifts_credits.json"`
- [ ] `TASK-202`: نقل دالة فحص سجل الهدية المرجعية `inspect_account_gift_status(sess, threshold_days=14)` من سكريبت `05.02` (السطور 376-415) مع حساب الأيام وفارق التوقيت.
- [ ] `TASK-203`: ترقية دالة العزل `quarantine_failed_account_atomic` لتقص الحساب من `accounts_genspark.json` وتضيفه إلى `accounts_failed.json` مع توثيق سبب الفشل وتاريخه.
- [ ] `TASK-204`: بناء دالة العزل لمتأخري الهدية `quarantine_delayed_gift_atomic` لتقص الحساب من `accounts_genspark.json` وتضيفه إلى `accounts_delayed_gifts_credits.json` مع توثيق `days_without_gift` وتاريخ آخر هدية بتوقيت القاهرة.
- [ ] `TASK-205`: تثبيت صمام الفصل القطعي (Bolla Law #7): حظر عزل الحسابات عند الـ 502/504 واقتصار الـ Failed على (`invalid_credentials`, `suspended`, `domain_banned`).

### 🔹 المرحلة 3: دمج المنظومة في جسر التليجرام (`01.33_telegram_gen_bridge.py`)
- [ ] `TASK-301`: ترقية دالة سحب الحسابات `get_eligible_accounts` (L1104) لترتيب الحسابات بالأعلى رصيداً ($\ge 100$) أولاً، ثم الأقدم استخداماً.
- [ ] `TASK-302`: تعديل بوابة فحص الرصيد المسبق (Pre-Flight Gate) في L2954-L2958:
  - إذا كان الرصيد $\ge 100$: مسار فائق السرعة (Fast-Path) — الانتقال فوراً للتوليد بدون أي استعلام لسجل الهدايا.
  - إذا كان الرصيد $< 100$: فحص سجل الهدية `inspect_account_gift_status`:
    - لو الهدية مقطوعة $> 14$ يوماً $\to$ عزل فوري في `accounts_delayed_gifts_credits.json` وقص من الأساسي.
    - لو الهدية طبيعية مستمرة ($\le 14$ يوماً) $\to$ تبريد أمان 29 ساعة (`mark_account_cooldown`) وتخطي صامت.
- [ ] `TASK-303`: تطبيق نفس منطق الفحص عند تجديد الجلسة المنتهية (401 Session Renewal) في L2977.
- [ ] `TASK-304`: إلغاء أي افتراض أو كود خاص بإنعاش الحسابات (Revival) تنفيذاً لتوجيه الباشمهندس الحاسم في الفويس 6.
- [ ] `TASK-305`: استبعاد أي تعقيدات زائدة (لا كاش TTL ولا رسائل تنظيف عند الإقلاع) حفاظاً على البساطة والمرونة وسهولة الصيانة (فويس 8).

### 🔹 المرحلة 4: استئصال التخمين الأعمى في محرك جينسبارك (`01.03Genspark_claude-opus-5-code.py`)
- [ ] `TASK-401`: استئصال التخمين الأعمى في L1093-L1108 (`_maybe_refresh_balance`):
  - حذف السطر القاتل `acc["balance"] = cfg.refreshed_balance`.
  - استبداله بفحص API حي حقيقي عبر سيرفر جينسبارك، أو منع رفع الرصيد بدون استعلام شبكي قطعي.
- [ ] `TASK-402`: تعطيل خاصية `refreshed_balance = 100` في `GensparkConfig` (L177) لمنع التخمين البنيوي نهائياً.

### 🔹 المرحلة 5: إعادة معايرة وتشغيل "المترجم" (`scripts/rebuild_refactor.py`)
- [ ] `TASK-501`: تدقيق الفارق السطري لجميع أجزاء الكود (Parts p01..p12) في `01.33_telegram_gen_bridge.py` بعد التعديلات الجراحية.
- [ ] `TASK-502`: تحديث خريطة الأجزاء `PARTS` في سكريبت المترجم [`scripts/rebuild_refactor.py`](file:///d:/SMS/.hRhRhRhRhRhR/..............................................................................................................%D8%B4%D8%BA%D9%84%20%D9%81%D8%B1%D9%8A%D9%82/Genspark/W___webapp/bridge_refactor_31/scripts/rebuild_refactor.py) بالأرقام السطرية الدقيقة (لتغطية كامل أسطر الملف من 1 إلى النهاية بلا أي فجوة أو تداخل).
- [ ] `TASK-503`: تشغيل "المترجم" رسمياً:
  ```powershell
  python -X utf8 scripts/rebuild_refactor.py
  ```
- [ ] `TASK-504`: التحقق من سلامة البناء المعياري:
  - تطابق الأسطر بالكامل (`التغطية == إجمالي الأسطر`).
  - خلو الأجزاء المولدة `bridge_refactor/parts/` من أي أخطاء نحوية (Syntax OK).
  - اكتمال الواجهات الـ 14 المولدة (`FACADES`).
- [ ] `TASK-505`: اختبار تطابق المعمارية بنسبة 100% (11/11 Parity Check) وتشغيل runtime namespace.

### 🔹 المرحلة 6: الاختبار والتثبت الميداني (Test-Before-Talk Validation)
- [ ] `TASK-601`: تشغيل حزمة الاختبارات المعزولة الجديدة:
  ```powershell
  pytest tests/test_tri_state_isolation.py -v
  ```
- [ ] `TASK-602`: تشغيل فحص النحو الشامل `py_compile` على كل الملفات المعدلة:
  ```powershell
  python -m py_compile genspark_verifier_engine.py 01.33_telegram_gen_bridge.py 01.03Genspark_claude-opus-5-code.py scripts/rebuild_refactor.py
  ```
- [ ] `TASK-603`: تشغيل سكريبت التحقق الشامل والسجل `scripts/hadith_sijil.py`.
- [ ] `TASK-604`: التحقق من عدم حدوث أي انحدار (Zero Regression) في ميزات الجسر القائمة (إلغاء تفاعلي، إعدادات GitHub، Intent Guard، Mode Fast-Lean).

### 🔹 المرحلة 7: التوثيق الدستوري وإغلاق السجلات (Constitutional Sync)
- [ ] `TASK-701`: تحديث بوصلة الحالة الفورية [`Root/ai_state.json`](file:///d:/SMS/.hRhRhRhRhRhR/Root/ai_state.json) بالحالة المكتملة.
- [ ] `TASK-702`: تدوين الإنجاز والدروس المستفادة في [`Root/tasks.md`](file:///d:/SMS/.hRhRhRhRhRhR/Root/tasks.md) و [`Root/memory.md`](file:///d:/SMS/.hRhRhRhRhRhR/Root/memory.md).
- [ ] `TASK-703`: تحديث سجل التقدم الخطي [`PROGRESS.md`](file:///d:/SMS/.hRhRhRhRhRhR/..............................................................................................................%D8%B4%D8%BA%D9%84%20%D9%81%D8%B1%D9%8A%D9%82/Genspark/W___webapp/bridge_refactor_31/PROGRESS.md).
- [ ] `TASK-704`: حفظ التغييرات بحزمة commit نظيفة وواضحة لحماية حالة النجاح.

---

## ⚙️ قلب المنظومة: استراتيجية "المترجم" (`scripts/rebuild_refactor.py`)

### ❓ ما هو "المترجم" ولماذا هو حجر الزاوية؟
في هذا المشروع، يعتمد جسر التليجرام على معمارية مزدوجة متطابقة (Dual Parity Architecture):
1. **الملف الأحادي المرجعي:** `01.33_telegram_gen_bridge.py` (يحتوي كامل المنظومة في ملف واحد لسهولة النشر والتشغيل المباشر).
2. **الحزمة المعيارية المجزأة:** `bridge_refactor/` المقسمة إلى 12 جزءاً حرفياً (`parts/p01` حتى `p12`) تديرها واجهات الـ Facades.
3. **المترجم (`scripts/rebuild_refactor.py`):** هو المحرك الذي يقوم بقص الأجزاء الحرفية بايت-بايت من الملف الأحادي وتوليد الحزمة المعيارية والتأكد من عدم وجود أي نقص أو فجوة برمجية.

### ⚠️ الخطر المكتشف (Ground Truth):
* حالياً الملف المرجعي `01.33_telegram_gen_bridge.py` نما ليصبح **9286 سطراً**.
* بينما خريطة "المترجم" `scripts/rebuild_refactor.py` في نسختها القديمة مسجلة حتى **9181 سطراً** فقط (بفارق 105 أسطر بسبب تحسينات سابقة).
* **الحل المعماري الحاسم:**
  - يتم في المرحلة 5 إعادة تدقيق البدايات والنهايات لجميع الأجزاء الـ 12.
  - حساب الفارق السطري للتعديلات الجراحية الجديدة بدقة مطلقة.
  - تغطية الأسطر الـ 9286 كاملة وزياداتها بلا أي سطر يتيم.
  - تشغيل المترجم للتأكد من نجاح الـ Assertion: `assert expected - 1 == total`.

---

## 📁 مواصفات الخزائن الثلاث (The Tri-State Vault Specifications)

```
                     ┌──────────────────────────────────────────────┐
                     │         accounts_genspark.json               │
                     │  (الملف الأساسي: الحسابات السليمة الجاهزة)     │
                     └──────────────────────┬───────────────────────┘
                                            │
                      فحص الرصيد الفعلي والهدية عند الاستخدام
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
     [حساب ميت / محظور قطعي]                                   [حساب سليم لكن هديته]
  (invalid_credentials / suspended)                             [انقطعت لأكثر من 14 يوماً]
               │                                                         │
               ▼ (قص ونقل ذري 100%)                                      ▼ (قص ونقل ذري 100%)
┌──────────────────────────────┐                         ┌──────────────────────────────────────┐
│     accounts_failed.json     │                         │ accounts_delayed_gifts_credits.json  │
│  (سلة الموتى والمحظورين)     │                         │     (معزل الحسابات المتأخرة)         │
└──────────────────────────────┘                         └──────────────────────────────────────┘
```

1. **`accounts_genspark.json` (الملف الأساسي):**
   - يحتوي الحسابات النشطة السليمة فقط.
   - الحسابات مرتبة بالأعلى رصيداً ($\ge 100$) أولاً، ثم الأقدم استخداماً.
   - أي حساب ينقل إلى معزل يُحذف فوراً وذرياً من هذا الملف لمنع استدعائه مجدداً.

2. **`accounts_delayed_gifts_credits.json` (معزل متأخري الهدية):**
   - يحتوي الحسابات التي باسووردها صحيح وجلستها سليمة، لكن انقطعت هديتها اليومية $> 14$ يوماً.
   - يُسجل لكل حساب: `days_without_gift` و `last_gift_time_cairo` و `quarantined_at`.
   - **دستور صارم (فويس 6):** لا يوجد أي مسار استرجاع (No Revival) — الحساب يبقى هنا نهائياً.

3. **`accounts_failed.json` (سلة الحسابات الميتة):**
   - يحتوي الحسابات الميتة قطعياً فقط (`invalid_credentials`, `suspended`, `domain_banned`).
   - يُسجل لكل حساب: `verdict` و `failure_reason` و `removed_at`.
   - **صمام أمان (فويس 9):** حظر تام لعزل أي حساب عند أخطاء الشبكة أو 500 أو 502 أو 504.

4. **`accounts_success.json`:**
   - **مستبعد تماماً** من كود الجسر وتليجرام (خاص بأرشيف الماستر مانجر فقط منعاً للازدواجية).

---

## 🛡️ مصفوفة الدفاع والحصانة المعمارية 360° (SRE Defense Matrix)

| # | الثغرة أو الاحتمال المعماري | السلوك الخطأ القديم | التحصين المعماري الجديد في الخطة |
|---|---|---|---|
| **1** | عطل عابر في سيرفر جينسبارك (500 / 502 / 504 / Cloudflare) | اعتبار الحساب ميتاً وعزله في `accounts_failed.json` بالخطأ! | **صمام الفصل القطعي:** لا يُعزل أي حساب إلا بخطأ باسوورد قطعي أو تحويل لـ `user_suspended`. أخطاء الـ 502/504 تُصنف كخطأ شبكة عابر ولا تمس الحساب. |
| **2** | حساب رصيده 0 لكن هديته منتظمة وسيرفر جينسبارك تأخر في تجديدها | عزله في المعزل أو محاولة استخدامه المتكرر | **تبريد الأمان 29 ساعة:** إدخال الحساب في Cooldown لمدة 29 ساعة ليحصل على بفر أمان كافٍ لتجديد الهدية بدون إزعاجه. |
| **3** | بطء استعلام الشبكة في تليجرام عند فحص الهدايا | انتظار المستخدم طويلاً إذا كان الحساب جاهزاً | **المسار السريع (Fast-Path):** لو رصيد الحساب $\ge 100$، يتم القفز فوراً للتوليد دون أي استعلام لسجل الهدايا. الفحص يتم فقط عند الرصيد المنخفض. |
| **4** | تضارب الثريدات الموازية عند قص ونقل الحسابات | كتابة متزامنة تسبب فقدان بيانات أو تلف ملف JSON | **أقفال العزل الذري:** استخدام `VAULT_LOCK` مع الكتابة الآمنة عبر ملفات مؤقتة `.tmp` والاستبدال الذري `os.replace`. |
| **5** | التخمين الأعمى وتعيين رصيد 100 افتراضياً | افتراض رجوع الرصيد بعد 29 ساعة وسحب الحساب وهو فارغ | **الاستئصال الجذري (Root Cause):** حذف `refreshed_balance = 100` وفرض الفحص الشبكي الحي للرصيد دائماً. |
| **6** | تعقيد الكود بميزات غير ضرورية (كاش، تنظيف الإقلاع) | تعقيد الصيانة وكسر سهولة الامتداد وتأخير الرد | **الالتزام بالبساطة القصوى (فويس 8):** لا كاش TTL ولا إجراءات إقلاع ثقيلة؛ كود مرن، خفيف، وسهل الفهم والتوسيع. |
| **7** | عدم تطابق "المترجم" بعد تعديل أسطر الملف الأحادي | كسر تقسيم الحزمة المعيارية وفشل بناء `bridge_refactor/` | **إعادة المعايرة السطرية الصارمة:** تدقيق وتحديث `PARTS` في `scripts/rebuild_refactor.py` ومطابقة 11/11 Parity. |

---

## 📍 الخريطة السطرية الحرفية للتعديلات (VERBATIM CODE MAP)

### 1️⃣ الموقع 1: بوابة الرصيد المسبق وسجل الهدايا
* **الملف:** `01.33_telegram_gen_bridge.py`
* **الموقع:** `L2954 - L2958`
* **BEFORE (الكود القائم):**
  ```python
  if isinstance(bal_check, (int, float)) and bal_check >= 0:
      if bal_check < _min_balance:
          log_event("warning", f"💰 رصيد منخفض ({int(bal_check)} < {_min_balance}) — تبريد 29h وتخطٍ صامت بدون أي إرسال", email=email)
          mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
          return None, "LOW_BALANCE", None, None, None
  ```
* **AFTER (الكود الجراحي المقترح):**
  ```python
  if isinstance(bal_check, (int, float)) and bal_check >= 0:
      if bal_check < _min_balance:
          # فحص سجل الهدية لمعرفة هل انقطعت > 14 يوم أم مستمرة طبيعياً
          gift_status, days_without_gift, last_gift_cairo = check_gift_status_for_account(acc, cookies)
          if gift_status == "STALE":
              log_event("warning", f"📦 هدية متأخرة ({days_without_gift} يوم) — عزل الحساب في accounts_delayed_gifts_credits.json", email=email)
              isolate_stale_gift_account(acc, days_without_gift, last_gift_cairo, json_path=json_path)
          else:
              log_event("warning", f"💰 رصيد منخفض وهدية منتظمة — تبريد 29h وتخطٍ صامت", email=email)
              mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
          return None, "LOW_BALANCE", None, None, None
  ```

---

### 2️⃣ الموقع 2: ثوابت أسماء ملفات الفشل والمعزل
* **الملف:** `genspark_verifier_engine.py`
* **الموقع:** `L38 - L40`
* **BEFORE (الكود القائم):**
  ```python
  QUARANTINE_FILENAME = "accounts_genspark_blocked_failed__block_failed.json"
  VAULT_LOCK = threading.Lock()
  ```
* **AFTER (الكود الجراحي المقترح):**
  ```python
  FAILED_ACCOUNTS_FILENAME = "accounts_failed.json"
  DELAYED_GIFTS_FILENAME = "accounts_delayed_gifts_credits.json"
  VAULT_LOCK = threading.Lock()
  ```

---

### 3️⃣ الموقع 3: استئصال التخمين الأعمى للرصيد
* **الملف:** `01.03Genspark_claude-opus-5-code.py`
* **الموقع:** `L1093 - L1108`
* **BEFORE (الكود القائم):**
  ```python
  def _maybe_refresh_balance(acc: dict, cfg: Config) -> dict:
      """لو الحساب مشتغلش من balance_refresh_hours ساعة → اعتبر رصيده اتجدد"""
      last = acc.get("last_sent_chat_sent") or acc.get("last_sent", "")
      if not last:
          return acc
      try:
          from datetime import datetime
          last_dt = datetime.fromisoformat(last)
          hours_passed = (datetime.now() - last_dt).total_seconds() / 3600
          if hours_passed >= cfg.balance_refresh_hours:
              acc["balance"] = cfg.refreshed_balance
              if cfg.show_debug:
                  p(Fore.CYAN, f"  ⏰ {acc.get('email','')[:20]}... مضى {hours_passed:.0f}س → رصيد اتجدد ({cfg.refreshed_balance})")
      except Exception:
          pass
      return acc
  ```
* **AFTER (الكود الجراحي المقترح):**
  ```python
  def _maybe_refresh_balance(acc: dict, cfg: Config) -> dict:
      """
      تم استئصال التخمين الأعمى نهائياً (Root Cause Eradication):
      الرصيد لا يتم افتراضه 100 أبداً بعد 29 ساعة، بل يظل كما هو
      حتى يتم استعلامه حياً من سيرفر جينسبارك عبر API فوري ومؤكد.
      """
      return acc
  ```

---

## 🔄 خطة التراجع السريع عند الطوارئ (Rollback Plan)

لو حدث أي طارئ غير متوقع أو عدم تطابق في الاختبارات، التراجع يتم فورياً بضغطة واحدة باستخدام النسخ المشفرة المعتمدة:

```powershell
# 1. استعادة محرك الفحص
Copy-Item "genspark_verifier_engine.py.anchor" "genspark_verifier_engine.py" -Force

# 2. استعادة جسر التليجرام
Copy-Item "01.33_telegram_gen_bridge.py.anchor" "01.33_telegram_gen_bridge.py" -Force

# 3. استعادة محرك التوليد 01.03
Copy-Item "01.03Genspark_claude-opus-5-code.py.anchor" "01.03Genspark_claude-opus-5-code.py" -Force

# 4. إعادة تشغيل المترجم لاستعادة الحزمة المعيارية الأصلية
python -X utf8 scripts/rebuild_refactor.py
```

---

## 🔒 الإقرار الدستوري والتوقف الإلزامي (Approval Gate)
* **تمت صياغة هذه الخطة الهندسية الشاملة بكل أركانها وتفاصيلها دون تعديل سطر كود تشغيلي واحد (Bolla Law #4 & #6).**
* **تم تضمين حسابات ودور "المترجم" (`scripts/rebuild_refactor.py`) في صميم الخطة لضمان تطابق الحزمة المعيارية بنسبة 100%.**
* **تم الالتزام التام بتوجيهات الباشمهندس في جميع الفويسات الـ 11 (إلغاء الاسترجاع، منع التعقيد، حماية 502، شجرة 29h، والدليل السطري الحرفي).**
* **نحن الآن في حالة انتظار كامل وجاهزية تامة لتلقي إشارة البدء `GO` للبدء في تنفيذ الخطوات التتابعية فوراً! 🚀**
