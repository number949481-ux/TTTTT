# RESUME.md — نقطة الاستئناف الحية للوكيل

> يُحدَّث عند كل محطة إنجاز (Milestone) جنبًا إلى جنب مع رأس `PROGRESS.md`.
> لا يحتوي أرقام commit ثابتة كمرجع تنفيذ؛ القاعدة دائمًا = أحدث HEAD في `origin/genspark_ai_developer`.
> لا أسرار هنا أبدًا. **المرجع الذاتي الوحيد للأولويات = جدول الأولويات في رأس `PROGRESS.md`.**

---

## 1) أين أقف الآن؟ (2026-10-31 — بعد تنفيذ STEP-3 Q-F)

| البند | الحالة |
|---|---|
| الفرع | `genspark_ai_developer` فقط (main READ-ONLY، لا فروع جانبية) — Layer A في أول 30 ثانية من كل جلسة بلا استثناء |
| المرحلة | **STEP-3 (Q-F) منجز بالأدلة** (`scripts/merge_legacy_quarantine.py` + `tests/test_p49_*` 14 passed؛ 0 انحدار بالأسماء؛ **لم يُشغَّل على ملفات حقيقية**). **التالي المباشر: STEP-4 (DEC-07)** — يبدأ بـS4-A مواصفة تحتاج اعتماد المالك قبل أي اختبار/كود. |
| MODE الحالي | انتهى تنفيذ STEP-3؛ لا تنفيذ لـSTEP-4 قبل اعتماد S4-A وإشارة «ابدأ تنفيذ» جديدة |
| PR | #9 Draft (يبقى Draft؛ لا merge) |
| وضع التسليم | حفظ محلي في `/home/user/webapp` → أداة المزامنة الخارجية ترفع تلقائيًا. لا push/gh/ZIP من الوكيل. |
| الخط الأساسي للاختبارات | **بالأسماء لا بالرقم**: 26 فاشلة معروفة (12 تاريخية + 14 drift؛ القائمة في `current_execution.baseline_failing_names`). أي اسم جديد = انحدار. آخر قياس: **1182 passed / 26 failed / 1 skipped** (بعد STEP-3؛ الأسماء الفاشلة مطابقة حرفياً لما قبلها). |

### القرارات المعتمدة من المالك (مرجع ثابت)
المسار (أ) الهدية الثلاثية؛ READ-ONLY = 01.03 + verifier (verifier بإذن AGENTS:22)؛ فحص **أوفلاين** من بيانات 05.02 فقط؛ UNKNOWN = **Fail-Open**؛ حد `>=14` شامل؛ Q-F دمج المعزل القديم في `accounts_failed.json` مع أرشيف؛ Q-C استبعاد عند الاختيار وin-flight يكمل؛ Q-R منجز؛ DEC-04 تأجيل الـ14 drift؛ **STEP-3**: سكربت مستقل `scripts/merge_legacy_quarantine.py`، عدم لمس 05.02، dry-run افتراضي/`--apply`، `.bak` مؤرخة، تفرد `email.lower()`، `legacy_quarantine`، اختبارات أولاً، حارس المسار `--i-know-this-is-real`؛ **STEP-4 (DEC-07)** مجدول رسمياً بعد STEP-3؛ **MAINT-1** مجدول.

---

## 2) خريطة الطريق (ملخص — التفصيل في PROGRESS)

| # | التذكرة | الحالة |
|---|---|---|
| 1 | STEP-1 اختبارات عزل 05.02 (34 passed) | `[x]` |
| 2 | STEP-2 Pre-Flight أوفلاين في 01.33 (34 passed؛ 0 انحدار؛ parity أخضر) | `[x]` مغلق |
| 3 | **STEP-3 (Q-F)** S3-A..D — سكربت مستقل + 14 اختباراً + إغلاق بالأسماء | `[x]` **منجز** |
| 4 | **STEP-4 (DEC-07)** صمام الرد الفارغ + `user_suspended` في `monitor_chat_completion` | `[ ]` **التالي** (S4-A أولاً) |
| 5 | **MAINT-1** حماية `github_bulk_sync.py` + CRLF في `rebuild_refactor.py` | `[ ]` مجدول (مستقل) |
| 6 | MAINT-2 الـ14 drift | `[ ]` مؤجل بقرار |
| 7 | Layer B/C | مقترح غير معتمد |

**ما تم فعلياً (بالأدلة):** STEP-1، Q-R، SYNC-TEST، ALIGN-0، BASELINE-DRIFT parity، STEP-2 (S2-A..D)، docstring 05.02، حذف GITHUB_SYNC، مراجعة 360°، خريطة الطريق، **STEP-3 (S3-A..D)**.
**لم يُنفَّذ (ولا يُدَّعى):** تشغيل `--apply` على ملفات المالك الحقيقية؛ STEP-4؛ MAINT-1/2؛ إصلاح أي من الـ26؛ أي تشغيل حي؛ V2 §17.6.

---

## 3) الخطوة التنفيذية التالية مباشرة — STEP-4 (DEC-07)

**STEP-3 مغلق.** أداة الدمج جاهزة: `python scripts/merge_legacy_quarantine.py --legacy <ملف المعزل القديم> --failed <accounts_failed.json>` = dry-run (ملخص JSON مقنّع، لا كتابة)؛ `--apply` يكتب بعد `.bak` للملفين؛ على المسارات الحقيقية يلزم `--i-know-this-is-real` **ولا يُنفَّذ إلا بأمر صريح من المالك** (خارج نطاق هذه التذاكر).

**STEP-4 عند وصول «ابدأ تنفيذ» له:** Layer A → قراءة رأس PROGRESS → `pytest tests -q` بالأسماء + `verify_docs_integrity.py` Exit 0 → ثم:
1. **S4-A** — كتابة المواصفة في PROGRESS فقط (حالات الإرجاع المقترحة `EMPTY_RESPONSE` / `ACCOUNT_SUSPENDED`، عتبة الردود الفارغة المتتالية، سلوك failover الفوري، ما لا يُمس: `is_account_ready`/P48) → **تتوقف لاعتماد المالك**.
2. **S4-B** — `tests/test_p50_dec07_breaker.py` حمراء أولاً (ردود وهمية محقونة؛ لا شبكة؛ CRLF؛ نقطة حقن واحدة).
3. **S4-C** — التنفيذ في 01.33 (`monitor_chat_completion` ~2838–2884 + معالجة الحالة في `send_message_with_auto_account_failover` ~3312+) + تحديث PARTS/parity + استعادة `github_bulk_sync.py` وCRLF بعد أي إعادة توليد.
4. **S4-D** — الإغلاق بالأسماء + docs + الوثائق الثلاث.

**الحدود الصلبة:** لا لمس 05.02/01.03/verifier؛ لا تشغيل حي؛ كل chunk يُكتب في PROGRESS فور إنجازه.

---

## 4) ما يحتاجه الوكيل من المالك (بلا تخمين)
1. إشارة **«ابدأ تنفيذ»** لـSTEP-4 (S4-A مواصفة فقط في البداية).
2. (بعد S4-A) اعتماد أسماء الحالات وعتبة الكسر.
3. (منفصل تماماً) هل يُراد تشغيل `merge_legacy_quarantine.py --apply` على الملفات الحقيقية؟ إن نعم: المسارات + أمر صريح؛ الوكيل لا يبادر.
4. (اختياري) قرار MAINT-2.

## 5) فحص الصحة عند كل استئناف (أقوم به تلقائيًا)
`git fetch origin genspark_ai_developer && git checkout -B genspark_ai_developer origin/genspark_ai_developer && git reset --hard origin/genspark_ai_developer` (إبلاغ الفرع/HEAD/dirty) → قراءة رأس PROGRESS + هذا الملف + `current_execution` → فحص الـGist إن ورد → إن كان MODE تنفيذياً: `pytest tests -q` مطابقة **بالأسماء** + `verify_docs_integrity.py` Exit 0 → البدء من أول `[ ]` في جدول الأولويات.
