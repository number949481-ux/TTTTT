# RESUME.md — نقطة الاستئناف الحية للوكيل

> يُحدَّث عند كل محطة إنجاز (Milestone) جنبًا إلى جنب مع رأس `PROGRESS.md`.
> لا يحتوي أرقام commit ثابتة كمرجع تنفيذ؛ القاعدة دائمًا = أحدث HEAD في `origin/genspark_ai_developer`.
> لا أسرار هنا أبدًا. **المرجع الذاتي الوحيد للأولويات = جدول الأولويات في رأس `PROGRESS.md`.**

---

## 1) أين أقف الآن؟ (2026-10-31 — بعد مراجعة 360° وتثبيت خريطة الطريق)

| البند | الحالة |
|---|---|
| الفرع | `genspark_ai_developer` فقط (main READ-ONLY، لا فروع جانبية) — Layer A في أول 30 ثانية من كل جلسة بلا استثناء |
| المرحلة | **STEP-2 مغلق نهائياً** (ثوابت العقد مثبتة في PROGRESS). **التالي المباشر: STEP-3 (Q-F)** — المواصفة معتمدة؛ **التنفيذ ينتظر إشارة «ابدأ تنفيذ»** + تأكيد بنود ⏳ في S3-A (أو قبول الافتراضات المقترحة). |
| MODE الحالي | `[ALIGNMENT_ONLY]` — لا كود تنفيذي |
| PR | #9 Draft (يبقى Draft؛ لا merge) |
| وضع التسليم | حفظ محلي في `/home/user/webapp` → أداة المزامنة الخارجية ترفع تلقائيًا. لا push/gh/ZIP من الوكيل. |
| الخط الأساسي للاختبارات | **بالأسماء لا بالرقم**: 26 فاشلة معروفة (12 تاريخية + 14 drift؛ القائمة في `current_execution.baseline_failing_names`). أي اسم جديد = انحدار. آخر قياس: 1168 passed / 26 failed (جلسة STEP-2). |

### القرارات المعتمدة من المالك (مرجع ثابت)
المسار (أ) الهدية الثلاثية؛ READ-ONLY = 01.03 + verifier (verifier بإذن AGENTS:22)؛ فحص **أوفلاين** من بيانات 05.02 فقط؛ UNKNOWN = **Fail-Open**؛ حد `>=14` شامل؛ Q-F دمج المعزل القديم في `accounts_failed.json` مع أرشيف؛ Q-C استبعاد عند الاختيار وin-flight يكمل؛ Q-R منجز؛ DEC-04 تأجيل الـ14 drift؛ **STEP-3**: سكربت مستقل `scripts/merge_legacy_quarantine.py`، عدم لمس 05.02، dry-run افتراضي/`--apply`، `.bak` مؤرخة، تفرد `email.lower()`، `legacy_quarantine`، اختبارات أولاً، حارس المسار `--i-know-this-is-real`؛ **STEP-4 (DEC-07)** مجدول رسمياً بعد STEP-3؛ **MAINT-1** مجدول.

---

## 2) خريطة الطريق (ملخص — التفصيل في PROGRESS)

| # | التذكرة | الحالة |
|---|---|---|
| 1 | STEP-1 اختبارات عزل 05.02 (34 passed) | `[x]` |
| 2 | STEP-2 Pre-Flight أوفلاين في 01.33 (34 passed؛ 0 انحدار؛ parity أخضر) | `[x]` مغلق |
| 3 | **STEP-3 (Q-F)** S3-A عقد البيانات → S3-B 14 اختباراً → S3-C السكربت → S3-D الإغلاق | `[ ]` **التالي** |
| 4 | **STEP-4 (DEC-07)** صمام الرد الفارغ + `user_suspended` في `monitor_chat_completion` | `[ ]` مجدول |
| 5 | **MAINT-1** حماية `github_bulk_sync.py` + CRLF في `rebuild_refactor.py` | `[ ]` مجدول (مستقل) |
| 6 | MAINT-2 الـ14 drift | `[ ]` مؤجل بقرار |
| 7 | Layer B/C | مقترح غير معتمد |

**ما تم فعلياً (بالأدلة):** STEP-1، Q-R، SYNC-TEST، ALIGN-0، BASELINE-DRIFT parity، STEP-2 (S2-A..D)، docstring 05.02، حذف GITHUB_SYNC، مراجعة 360° (وثائق 01–14 + تحقق قراءة فقط من الكود)، خريطة الطريق هذه.
**لم يُنفَّذ (ولا يُدَّعى):** STEP-3؛ STEP-4؛ MAINT-1/2؛ إصلاح أي من الـ26؛ أي تشغيل حي؛ V2 §17.6.

---

## 3) الخطوة التنفيذية التالية مباشرة — STEP-3 (Q-F)

**عند وصول «ابدأ تنفيذ»:** Layer A → قراءة رأس PROGRESS → `pytest tests -q` مطابقة بالأسماء + `verify_docs_integrity.py` Exit 0 → ثم بالترتيب:
1. **S3-A** — عقد البيانات مثبت في PROGRESS؛ يُنفَّذ كما هو بعد تأكيد بنود ⏳ (التعارض = الأقدم يفوز؛ `dead_accounts.json` لا يُمس؛ الملف القديم يبقى + `.bak`).
2. **S3-B** — `tests/test_p49_legacy_quarantine_merge.py` حمراء أولاً (14 اختباراً؛ tmp_path فقط؛ Zero-Leakage؛ حارس المسار).
3. **S3-C** — `scripts/merge_legacy_quarantine.py` (CLI `--legacy/--failed/--apply/--i-know-this-is-real`؛ مساعدات 05.02 عبر `spec_from_file_location` + stub).
4. **S3-D** — الحزمة الكاملة بالأسماء (0 جديد) + docs Exit 0 + PROGRESS/RESUME/`current_execution`.

**الحدود الصلبة:** لا لمس 05.02/01.33/01.03/verifier في STEP-3؛ لا تشغيل على ملفات حقيقية؛ كل chunk يُكتب في PROGRESS فور إنجازه.

---

## 4) ما يحتاجه الوكيل من المالك (بلا تخمين)
1. إشارة **«ابدأ تنفيذ»** لـSTEP-3.
2. تأكيد بنود ⏳ في S3-A (أو «اقبل الافتراضات»): (أ) سياسة التعارض «الأقدم يفوز»؛ (ب) `dead_accounts.json` خارج النطاق؛ (ج) الملف القديم يبقى كما هو بعد الدمج.
3. (لاحقاً، قبل S4-B) اعتماد مواصفة S4-A: أسماء الحالات الجديدة وعتبات الكسر.
4. (اختياري) قرار MAINT-2.

## 5) فحص الصحة عند كل استئناف (أقوم به تلقائيًا)
`git fetch origin genspark_ai_developer && git checkout -B genspark_ai_developer origin/genspark_ai_developer && git reset --hard origin/genspark_ai_developer` (إبلاغ الفرع/HEAD/dirty) → قراءة رأس PROGRESS + هذا الملف + `current_execution` → فحص الـGist إن ورد → إن كان MODE تنفيذياً: `pytest tests -q` مطابقة **بالأسماء** + `verify_docs_integrity.py` Exit 0 → البدء من أول `[ ]` في جدول الأولويات.
