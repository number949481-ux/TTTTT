# RESUME.md — نقطة الاستئناف الحية للوكيل

> يُحدَّث عند كل محطة إنجاز (Milestone) جنبًا إلى جنب مع رأس `PROGRESS.md`.
> لا يحتوي أرقام commit ثابتة كمرجع تنفيذ؛ القاعدة دائمًا = أحدث HEAD في `origin/genspark_ai_developer`.
> لا أسرار هنا أبدًا. **المرجع الذاتي الوحيد للأولويات = جدول الأولويات في رأس `PROGRESS.md`.**

---

## 1) أين أقف الآن؟ (2026-10-31 — STEP-3 مغلق + S3-LOG-1؛ S4-A مكتوبة)

| البند | الحالة |
|---|---|
| الفرع | `genspark_ai_developer` فقط (main READ-ONLY، لا فروع جانبية) — Layer A في أول 30 ثانية من كل جلسة بلا استثناء |
| المرحلة | **STEP-3 مغلق** (+ S3-LOG-1: لوجات السكربت تطبع البريد كاملاً بقرار المالك؛ لا أسرار). **STEP-4 (DEC-07): S4-A المواصفة مكتوبة في PROGRESS** — ⏸️ **بانتظار اعتماد القرارات (1)–(7) ثم «ابدأ تنفيذ» لـS4-B**. لا كود في 01.33 حتى الآن. |
| MODE الحالي | S4-A منجزة (توثيق فقط)؛ S4-B لا تبدأ قبل اعتماد (1)–(7) + «ابدأ تنفيذ» |
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
| 4 | **STEP-4 (DEC-07)** صمام الرد الفارغ + `user_suspended` في `monitor_chat_completion` | `[ ]` **جارٍ** — S4-A `[x]`؛ S4-B التالي بعد الاعتماد |
| 5 | **MAINT-1** حماية `github_bulk_sync.py` + CRLF في `rebuild_refactor.py` | `[ ]` مجدول (مستقل) |
| 6 | MAINT-2 الـ14 drift | `[ ]` مؤجل بقرار |
| 7 | Layer B/C | مقترح غير معتمد |

**ما تم فعلياً (بالأدلة):** STEP-1، Q-R، SYNC-TEST، ALIGN-0، BASELINE-DRIFT parity، STEP-2 (S2-A..D)، docstring 05.02، حذف GITHUB_SYNC، مراجعة 360°، خريطة الطريق، **STEP-3 (S3-A..D)**.
**لم يُنفَّذ (ولا يُدَّعى):** تشغيل `--apply` على ملفات المالك الحقيقية؛ STEP-4؛ MAINT-1/2؛ إصلاح أي من الـ26؛ أي تشغيل حي؛ V2 §17.6.

---

## 3) الخطوة التنفيذية التالية مباشرة — STEP-4 / S4-B (بعد اعتماد S4-A)

**خلاصة S4-A (التفصيل الكامل في رأس PROGRESS):** التشخيص مُتحقَّق: `detect_response_status` يعيد `EMPTY` لكنه ليس شرط خروج حلقة `monitor_chat_completion` (2869) → استطلاع حتى `session_timeout` (2000s) → TIMEOUT ~33 دقيقة؛ لا عدّاد فراغ ولا كشف `user_suspended` في 01.33. **المقترح:** ثوابت `DEC07_EMPTY_BREAKER_ENABLED/DEC07_EMPTY_READS_REQUIRED=3/DEC07_EMPTY_MIN_SECONDS=30/DEC07_SUSPENDED_MARKERS`؛ حالتان `EMPTY_STREAM_FAILED` و`ACCOUNT_SUSPENDED` (خارج `P44_STRUCTURED_STATUSES`)؛ نقطة حقن A في الحلقة (عدّاد `empty_streak` مع حواجز readiness/unconfirmed/maintenance/evidence.finished) + A2 كشف نصّي للحظر + نقطة B في failover (تخطٍّ فوري كـLOW_BALANCE؛ الحظر يكتب `status=suspended/quarantined=True/cookies={}`). لا يُمس: `is_account_ready`، P48، `detect_response_status(_gated)`، P25، 01.03، verifier، 05.02.

**عند «ابدأ تنفيذ» لـS4-B:** Layer A → رأس PROGRESS → `pytest tests -q` بالأسماء + docs Exit 0 → `tests/test_p50_dec07_breaker.py` (~12) حمراء أولاً → S4-C نقطتا حقن في 01.33 (CRLF) + PARTS/parity + استعادة `github_bulk_sync.py` وCRLF → S4-D إغلاق بالأسماء + الوثائق الثلاث.

**أداة STEP-3 جاهزة (مرجع):** `python scripts/merge_legacy_quarantine.py --legacy <legacy> --failed <accounts_failed.json>` dry-run؛ `--apply` يكتب بعد `.bak`؛ المسارات الحقيقية تحتاج `--i-know-this-is-real` **وأمراً صريحاً**.

---

## 4) ما يحتاجه الوكيل من المالك (بلا تخمين) — قرارات S4-A
1. أسماء الحالات: `EMPTY_STREAM_FAILED` + `ACCOUNT_SUSPENDED` (مقترح) أم غيرها.
2. العتبات: 3 قراءات فارغة متتالية (≈15 ث) + 30 ث حد أدنى — أم قيم أخرى.
3. تبريد حساب `EMPTY_STREAM_FAILED`: لا تبريد / قصير (1 ساعة) / 29 ساعة كـLOW_BALANCE.
4. 403 متكرر + نص فارغ = اشتباه حظر (`ACCOUNT_SUSPENDED`) أم يبقى `FORBIDDEN`.
5. تأكيد استبعاد الصمام الثالث (probe حي لـ`/user_suspended`) لتعارضه مع «أوفلاين فقط».
6. هل إلغاء حجب البريد يسري على لوجات `[DEC07]` في 01.33 (الوثيقة 12 §4 الصمام الخامس تنص على التمويه — تعارض موثَّق).
7. اعتماد تذكرة منفصلة لمعالجة `FORBIDDEN` في failover (اكتشاف جانبي خارج DEC-07).
8. ثم إشارة **«ابدأ تنفيذ»** لـS4-B. (منفصل: تشغيل `merge_legacy_quarantine.py --apply` على الملفات الحقيقية يحتاج أمراً صريحاً + مسارات.)

## 5) فحص الصحة عند كل استئناف (أقوم به تلقائيًا)
`git fetch origin genspark_ai_developer && git checkout -B genspark_ai_developer origin/genspark_ai_developer && git reset --hard origin/genspark_ai_developer` (إبلاغ الفرع/HEAD/dirty) → قراءة رأس PROGRESS + هذا الملف + `current_execution` → فحص الـGist إن ورد → إن كان MODE تنفيذياً: `pytest tests -q` مطابقة **بالأسماء** + `verify_docs_integrity.py` Exit 0 → البدء من أول `[ ]` في جدول الأولويات.
