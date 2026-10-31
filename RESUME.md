# RESUME.md — نقطة الاستئناف الحية للوكيل

> يُحدَّث عند كل محطة إنجاز (Milestone) جنبًا إلى جنب مع رأس `PROGRESS.md`.
> لا يحتوي أرقام commit ثابتة كمرجع تنفيذ؛ القاعدة دائمًا = أحدث HEAD في `origin/genspark_ai_developer`.
> لا أسرار هنا أبدًا. **المرجع الذاتي الوحيد للأولويات = جدول الأولويات في رأس `PROGRESS.md`.**

---

## 0) قاعدة دستورية دائمة لحسم MODE (معتمدة من المالك 2026-10-31 — لا تُؤرشف)
إذا ورد كارت الاستئناف بصيغة الخيارين `[ALIGNMENT_ONLY] | أو "ابدأ تنفيذ"` (القالب المعياري الثابت)، فالوضع **الافتراضي الإلزامي = «ابدأ تنفيذ» تلقائياً وذاتياً دون توقف**، طالما: (أ) القرارات اللازمة للخطوة معتمدة ومكتوبة في PROGRESS، و(ب) الخطوة = أول `[ ]` في رأس PROGRESS. **يُحظر التوقف لطلب حسم الخيارين.** الاستثناء الوحيد: خطوة تحتاج قراراً غير مكتوب → تُكتب المواصفة/الأسئلة ويُتوقف عندها فقط.

## 1) أين أقف الآن؟ (2026-10-31 — STEP-3 مغلق؛ STEP-4 (DEC-07) مغلق بالأدلة S4-A..D)

| البند | الحالة |
|---|---|
| الفرع | `genspark_ai_developer` فقط (main READ-ONLY، لا فروع جانبية) — Layer A في أول 30 ثانية من كل جلسة بلا استثناء |
| المرحلة | **STEP-3 مغلق** (+ S3-LOG-1). **STEP-4 (DEC-07) مغلق 2026-10-31:** S4-A مواصفة → S4-A-RATIFIED (قرارات 1–7) → S4-B `tests/test_p50_dec07_breaker.py` 19 اختباراً (حمراء أولاً 10/9) → S4-C ثلاث حقنات في 01.33 (ثوابت `DEC07_*` + `dec07_text_has_suspended_marker`؛ صمام الرد الفارغ في `monitor_chat_completion`؛ فرعا `EMPTY_STREAM_FAILED`/`ACCOUNT_SUSPENDED` في failover) 9660→9736 سطراً CRLF + PARTS p05..p12 محدَّثة وparity 11/11 → S4-D إغلاق بالأسماء. **التالي بالجدول: MAINT-1** (حماية `github_bulk_sync.py` + CRLF في `rebuild_refactor.py`) ثم MAINT-3 (`FORBIDDEN` في failover). |
| MODE الحالي | STEP-4 مغلق؛ أول `[ ]` = MAINT-1 (قرارات مكتوبة في PROGRESS: حذف `parts/p01..p12` فقط أو allowlist لملف المالك + كتابة CRLF كما في HEAD + اختبار parity) — كارت MODE بالخيارين = «ابدأ تنفيذ» تلقائياً (§0) |
| PR | #9 Draft (يبقى Draft؛ لا merge) |
| وضع التسليم | حفظ محلي في `/home/user/webapp` → أداة المزامنة الخارجية ترفع تلقائيًا. لا push/gh/ZIP من الوكيل. |
| الخط الأساسي للاختبارات | **بالأسماء لا بالرقم**: 26 فاشلة معروفة (12 تاريخية + 14 drift؛ القائمة في `current_execution.baseline_failing_names`). أي اسم جديد = انحدار. آخر قياس: **1201 passed / 26 failed / 1 skipped** (بعد STEP-4؛ الأسماء الفاشلة مطابقة حرفياً لما قبلها — 0 جديد؛ P50 19/19؛ parity 11/11). |

### القرارات المعتمدة من المالك (مرجع ثابت)
المسار (أ) الهدية الثلاثية؛ READ-ONLY = 01.03 + verifier (verifier بإذن AGENTS:22)؛ فحص **أوفلاين** من بيانات 05.02 فقط؛ UNKNOWN = **Fail-Open**؛ حد `>=14` شامل؛ Q-F دمج المعزل القديم في `accounts_failed.json` مع أرشيف؛ Q-C استبعاد عند الاختيار وin-flight يكمل؛ Q-R منجز؛ DEC-04 تأجيل الـ14 drift؛ **STEP-3**: سكربت مستقل `scripts/merge_legacy_quarantine.py`، عدم لمس 05.02، dry-run افتراضي/`--apply`، `.bak` مؤرخة، تفرد `email.lower()`، `legacy_quarantine`، اختبارات أولاً، حارس المسار `--i-know-this-is-real`؛ **STEP-4 (DEC-07)** مجدول رسمياً بعد STEP-3؛ **MAINT-1** مجدول.

---

## 2) خريطة الطريق (ملخص — التفصيل في PROGRESS)

| # | التذكرة | الحالة |
|---|---|---|
| 1 | STEP-1 اختبارات عزل 05.02 (34 passed) | `[x]` |
| 2 | STEP-2 Pre-Flight أوفلاين في 01.33 (34 passed؛ 0 انحدار؛ parity أخضر) | `[x]` مغلق |
| 3 | **STEP-3 (Q-F)** S3-A..D — سكربت مستقل + 14 اختباراً + إغلاق بالأسماء | `[x]` **منجز** |
| 4 | **STEP-4 (DEC-07)** صمام الرد الفارغ + `user_suspended` في `monitor_chat_completion` | `[ ]` **جارٍ** — S4-A `[x]`؛ S4-B التالي بعد الاعتماد |
| 5 | **MAINT-1** حماية `github_bulk_sync.py` + CRLF في `rebuild_refactor.py` | `[ ]` مجدول (مستقل) |
| 6 | MAINT-2 الـ14 drift | `[ ]` مؤجل بقرار |
| 7 | Layer B/C | مقترح غير معتمد |

**ما تم فعلياً (بالأدلة):** STEP-1، Q-R، SYNC-TEST، ALIGN-0، BASELINE-DRIFT parity، STEP-2 (S2-A..D)، docstring 05.02، حذف GITHUB_SYNC، مراجعة 360°، خريطة الطريق، **STEP-3 (S3-A..D)**.
**لم يُنفَّذ (ولا يُدَّعى):** تشغيل `--apply` على ملفات المالك الحقيقية؛ STEP-4؛ MAINT-1/2؛ إصلاح أي من الـ26؛ أي تشغيل حي؛ V2 §17.6.

---

## 3) الخطوة التنفيذية التالية مباشرة — MAINT-1 (صف 5 في جدول الأولويات)

**لماذا الآن:** حدث ثلاث مرات (جلسات 8، 9، 22) أن `scripts/rebuild_refactor.py` حذف `bridge_refactor/` بالكامل (`shutil.rmtree`) فأسقط ملف المالك غير المولَّد `bridge_refactor/git/github_bulk_sync.py` (49 سطراً) وكتب الأجزاء بـLF بينما HEAD يحفظها CRLF (36 ملفاً) — وأُصلح يدوياً في كل مرة.

**المواصفة (مكتوبة في PROGRESS — بلا قرارات معلّقة):** (أ) لا `rmtree` أعمى: حذف المولَّد فقط (`parts/p*.py` + الواجهات في `FACADES` + `runtime.py`/`main.py`/`__init__.py`) أو allowlist حفظ صريح يضم `git/github_bulk_sync.py`؛ (ب) الكتابة بـ`newline=""` مع نهاية سطر مطابقة لما في HEAD (CRLF للأجزاء والواجهات)؛ (ج) اختبار جديد في `tests/test_refactor_parity.py` يشغّل البناء في مجلد مؤقت ويثبت بقاء ملف المالك وCRLF. **الحدود:** يُلمَس `scripts/rebuild_refactor.py` و`tests/test_refactor_parity.py` فقط؛ 01.33 لا يتغير؛ لا تغيير في مخرجات الأجزاء بايت-بايت (parity 11 تبقى خضراء).

**عند الكارت:** Layer A → رأس PROGRESS → `pytest tests -q` بالأسماء (26 معروفة) + docs Exit 0 → اختبار MAINT-1 أحمر أولاً → تعديل السكربت → تشغيله والتحقق أن `git status` لا يُظهر تغييراً في `bridge_refactor/` (إثبات idempotency) → إغلاق بالأسماء + الوثائق الثلاث.

**بعدها:** MAINT-3 (`FORBIDDEN` في failover — تذكرة منفصلة معتمدة بالقرار 7)؛ MAINT-2 مؤجلة (DEC-04).

**أداة STEP-3 جاهزة (مرجع):** `python scripts/merge_legacy_quarantine.py --legacy <legacy> --failed <accounts_failed.json>` dry-run؛ `--apply` يكتب بعد `.bak`؛ المسارات الحقيقية تحتاج `--i-know-this-is-real` **وأمراً صريحاً**.

---

## 4) ما يحتاجه الوكيل من المالك (بلا تخمين)
1. **لا قرارات معلّقة لـMAINT-1** — مواصفتها كاملة في PROGRESS؛ تبدأ بأول كارت MODE/«ابدأ تنفيذ».
2. **MAINT-3:** سلوك `FORBIDDEN` في failover — مقترح: معاملته كـ`LOW_BALANCE` (تخطٍّ صامت + تبريد) أم كـ`ACCOUNT_SUSPENDED` (حجر)؟ يُحسم قبل بدئها (ليس الآن).
3. **MAINT-2 (DEC-04):** تحديث الاختبارات الـ14 لتعكس v5.4 أم إصلاح الكود — مؤجل بقرار المالك.
4. (منفصل) تشغيل `merge_legacy_quarantine.py --apply` على الملفات الحقيقية يحتاج أمراً صريحاً + مسارات.
5. (منفصل) تفعيل DEC-07 حياً = مجرد تشغيل 01.33 المحدَّث؛ لا migration. إن رغب المالك بتعطيله مؤقتاً: `DEC07_EMPTY_BREAKER_ENABLED=False` (اختبار 11 يثبت رجوع السلوك القديم حرفياً).

---

## 5) فحص الصحة عند كل استئناف (أقوم به تلقائيًا)
`git fetch origin genspark_ai_developer && git checkout -B genspark_ai_developer origin/genspark_ai_developer && git reset --hard origin/genspark_ai_developer` (إبلاغ الفرع/HEAD/dirty) → قراءة رأس PROGRESS + هذا الملف + `current_execution` → فحص الـGist إن ورد → إن كان MODE تنفيذياً: `pytest tests -q` مطابقة **بالأسماء** + `verify_docs_integrity.py` Exit 0 → البدء من أول `[ ]` في جدول الأولويات.
