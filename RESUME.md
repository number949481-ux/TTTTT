# RESUME.md — نقطة الاستئناف الحية للوكيل

> يُحدَّث عند كل محطة إنجاز (Milestone) جنبًا إلى جنب مع رأس `PROGRESS.md`.
> لا يحتوي أرقام commit ثابتة كمرجع تنفيذ؛ القاعدة دائمًا = أحدث HEAD في `origin/genspark_ai_developer`.
> لا أسرار هنا أبدًا. **المرجع الذاتي الوحيد للأولويات = جدول الأولويات في رأس `PROGRESS.md`.**

---

## 0) قاعدة دستورية دائمة لحسم MODE (معتمدة من المالك 2026-10-31 — لا تُؤرشف)
إذا ورد كارت الاستئناف بصيغة الخيارين `[ALIGNMENT_ONLY] | أو "ابدأ تنفيذ"` (القالب المعياري الثابت)، فالوضع **الافتراضي الإلزامي = «ابدأ تنفيذ» تلقائياً وذاتياً دون توقف**، طالما: (أ) القرارات اللازمة للخطوة معتمدة ومكتوبة في PROGRESS، و(ب) الخطوة = أول `[ ]` في رأس PROGRESS. **يُحظر التوقف لطلب حسم الخيارين.** الاستثناء الوحيد: خطوة تحتاج قراراً غير مكتوب → تُكتب المواصفة/الأسئلة ويُتوقف عندها فقط.

## 1) أين أقف الآن؟ (2026-10-31 — STEP-3 + STEP-4 (DEC-07) + MAINT-1 مغلقة بالأدلة)

| البند | الحالة |
|---|---|
| الفرع | `genspark_ai_developer` فقط (main READ-ONLY، لا فروع جانبية) — Layer A في أول 30 ثانية من كل جلسة بلا استثناء |
| المرحلة | **STEP-3 مغلق** (+ S3-LOG-1). **STEP-4 (DEC-07) مغلق 2026-10-31:** S4-A مواصفة → S4-A-RATIFIED (قرارات 1–7) → S4-B `tests/test_p50_dec07_breaker.py` 19 اختباراً (حمراء أولاً 10/9) → S4-C ثلاث حقنات في 01.33 (ثوابت `DEC07_*` + `dec07_text_has_suspended_marker`؛ صمام الرد الفارغ في `monitor_chat_completion`؛ فرعا `EMPTY_STREAM_FAILED`/`ACCOUNT_SUSPENDED` في failover) 9660→9736 سطراً CRLF + PARTS p05..p12 محدَّثة وparity 11/11 → S4-D إغلاق بالأسماء. **MAINT-1 مغلق 2026-10-31:** `rebuild_refactor.py` صار purge-only (لا rmtree) + كاتب CRLF + `main(root=)`؛ 5 اختبارات `TestGeneratorSafety` (حمراء أولاً) → parity 16/16؛ تشغيل حي في المكان ⇒ `git status bridge_refactor` فارغ. **التالي بالجدول: MAINT-3** (`FORBIDDEN` في failover) — **معلّق على قرار المالك (§4 بند 1)**. |
| MODE الحالي | MAINT-1 مغلق؛ أول `[ ]` = **MAINT-3** لكن قرارها غير مكتوب بعد → عند الكارت التالي: إن ورد القرار في DECISIONS → «ابدأ تنفيذ» (§0)؛ وإلا تُكتب مواصفة MAINT-3 (قراءة فقط) ويُطرح السؤال الواحد في §4 — لا تخمين في سلوك failover |
| PR | #9 Draft (يبقى Draft؛ لا merge) |
| وضع التسليم | حفظ محلي في `/home/user/webapp` → أداة المزامنة الخارجية ترفع تلقائيًا. لا push/gh/ZIP من الوكيل. |
| الخط الأساسي للاختبارات | **بالأسماء لا بالرقم**: 26 فاشلة معروفة (12 تاريخية + 14 drift؛ القائمة في `current_execution.baseline_failing_names`). أي اسم جديد = انحدار. آخر قياس: **1206 passed / 26 failed / 1 skipped** (بعد MAINT-1؛ الأسماء الفاشلة مطابقة حرفياً — 0 جديد؛ P50 19/19؛ parity 16/16). |

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

## 3) الخطوة التنفيذية التالية مباشرة — MAINT-3 (صف 5b): `FORBIDDEN` في `send_message_with_auto_account_failover`

**الخلفية (اكتشاف S4-A، قرار 7):** `FORBIDDEN` (403) هو شرط خروج لحلقة `monitor_chat_completion` ويعود للـfailover، لكن الـfailover لا يملك فرعاً صريحاً له (بخلاف `LOW_BALANCE`/`EMPTY_STREAM_FAILED`/`ACCOUNT_SUSPENDED`) فيسقط في المعالجة العامة. القرار (4) في S4-A-RATIFIED ثبّت أن 403 **يبقى** `FORBIDDEN` ولا يُعامل كاشتباه حظر.

**قرار واحد مطلوب قبل أي كود (بلا تخمين):** عند `FORBIDDEN` من حساب — **(أ)** تخطٍّ + تبريد كـ`LOW_BALANCE` (ما المدة؟ 1h كـDEC07 أم 29h؟) أم **(ب)** حجر كـ`ACCOUNT_SUSPENDED` (`status=suspended/quarantined=True/cookies={}`) أم **(ج)** تخطٍّ بلا تبريد (الحساب يُجرَّب في المهمة التالية). المقترح الافتراضي للعرض: **(أ) مع 1h** لاتساقه مع DEC07 وعدم إحراق حساب بسبب 403 عابر.

**عند اعتماد القرار:** Layer A → `pytest tests -q` بالأسماء (26) + docs Exit 0 → `tests/test_p51_forbidden_failover.py` حمراء أولاً (harness failover من P50 `TestFailoverHandling`) → فرع واحد في failover قبل `LOW_BALANCE` (CRLF؛ `P44_STRUCTURED_STATUSES` لا يتغير) → PARTS p06 end +N وإزاحة p07..p12 → `python3 scripts/rebuild_refactor.py` (صار آمناً بعد MAINT-1: لا استعادة يدوية) → إغلاق بالأسماء + الوثائق الثلاث.

**ملاحظة تشغيلية بعد MAINT-1:** إعادة التوليد لم تعد تحتاج استعادة `github_bulk_sync.py` ولا تحويل CRLF يدوياً؛ الدليل: `git status --short bridge_refactor` فارغ بعد التشغيل.

**أداة STEP-3 جاهزة (مرجع):** `python scripts/merge_legacy_quarantine.py --legacy <legacy> --failed <accounts_failed.json>` dry-run؛ `--apply` يكتب بعد `.bak`؛ المسارات الحقيقية تحتاج `--i-know-this-is-real` **وأمراً صريحاً**.

---

## 4) ما يحتاجه الوكيل من المالك (بلا تخمين)
1. **MAINT-3 — القرار الوحيد:** سلوك `FORBIDDEN` في failover: (أ) تخطٍّ + تبريد (المدة؟) / (ب) حجر / (ج) تخطٍّ بلا تبريد. المقترح: (أ) 1h. يُكتب في DECISIONS بالكارت.
2. **MAINT-2 (DEC-04):** تحديث الاختبارات الـ14 لتعكس v5.4 أم إصلاح الكود — مؤجل بقرار المالك.
3. (منفصل) تشغيل `merge_legacy_quarantine.py --apply` على الملفات الحقيقية يحتاج أمراً صريحاً + مسارات.
4. (منفصل) تفعيل DEC-07 حياً = تشغيل 01.33 المحدَّث؛ لا migration. تعطيل مؤقت: `DEC07_EMPTY_BREAKER_ENABLED=False`.

---

## 5) فحص الصحة عند كل استئناف (أقوم به تلقائيًا)
`git fetch origin genspark_ai_developer && git checkout -B genspark_ai_developer origin/genspark_ai_developer && git reset --hard origin/genspark_ai_developer` (إبلاغ الفرع/HEAD/dirty) → قراءة رأس PROGRESS + هذا الملف + `current_execution` → فحص الـGist إن ورد → إن كان MODE تنفيذياً: `pytest tests -q` مطابقة **بالأسماء** + `verify_docs_integrity.py` Exit 0 → البدء من أول `[ ]` في جدول الأولويات.
