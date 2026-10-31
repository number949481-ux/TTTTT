# RESUME.md — نقطة الاستئناف الحية للوكيل

> يُحدَّث عند كل محطة إنجاز (Milestone) جنبًا إلى جنب مع رأس `PROGRESS.md`.
> لا يحتوي أرقام commit ثابتة كمرجع تنفيذ؛ القاعدة دائمًا = أحدث HEAD في `origin/genspark_ai_developer`.
> لا أسرار هنا أبدًا.

---

## 1) أين أقف الآن؟ (2026-10-31 — بعد تنفيذ STEP-2)

| البند | الحالة |
|---|---|
| الفرع | `genspark_ai_developer` فقط (main READ-ONLY، لا فروع جانبية) — اسحب أحدث HEAD دائمًا |
| المرحلة | **STEP-2 منجز بالأدلة** (Pre-Flight أوفلاين لفحص الهدية). **التالي المباشر: STEP-3** (دمج المعزل القديم Q-F) — بانتظار تأكيد المالك لاسم/موقع السكربت فقط. |
| PR | #9 Draft (يبقى Draft؛ لا merge) |
| وضع التسليم | حفظ محلي في `/home/user/webapp` → أداة المزامنة الخارجية ترفع تلقائيًا. لا push/gh/ZIP من الوكيل. |
| الخط الأساسي للاختبارات | **بالأسماء لا بالرقم**: 26 فاشلة معروفة (12 تاريخية + 14 drift من commits المالك: p17×2، p20، p24×2، p26، p31×5، p33، p46 `test_full_isolated_metrics_display`، p47 بيئي `curl_cffi`). أي اسم جديد = انحدار. |

### القرارات المعتمدة من المالك (مرجع ثابت)
المسار (أ) الهدية الثلاثية؛ SCOPE = `01.33` + `tests/` + `PROGRESS.md` + `RESUME.md` (+ docstring 05.02 + حذف GITHUB_SYNC — نُفِّذا)؛ READ-ONLY = 01.03 + verifier؛ فحص **أوفلاين** من بيانات 05.02 فقط؛ UNKNOWN = **Fail-Open** معلن؛ حد الهدية **>= 14** شامل؛ Q-F/Q-C/Q-R كما في PROGRESS.

---

## 2) ما تم إنجازه واختباره فعليًا (بالأدلة)

- [x] **STEP-1** — `tests/test_tri_state_isolation.py`: 34 اختبارًا معزولًا لـ05.02 → **34 passed**.
- [x] **Q-R / SYNC-TEST / ALIGN-0** — مغلقة (التفاصيل في رأس PROGRESS).
- [x] **BASELINE-DRIFT** — `scripts/rebuild_refactor.py` خريطة PARTS محدَّثة؛ `test_parts_reassemble_to_original` أخضر. ⚠️ السكربت يحذف `bridge_refactor/` كاملًا (يُسقط ملف المالك `git/github_bulk_sync.py`) ويكتب LF؛ بعد كل تشغيل: استعادة الملف + تحويل CRLF للملفات التي كانت CRLF في HEAD.
- [x] **STEP-2** — في `01.33` (9660 سطرًا، CRLF نقي):
  - ثوابت: `GIFT_PREFLIGHT_ENABLED=True`، `GIFT_STALE_DAYS=14`، `GIFT_GRACE_DAYS=3`، `GIFT_SNAPSHOT_MAX_AGE_HOURS=72`، `GIFT_LABELS`.
  - `_parse_local_iso_ts(value)` + `classify_gift_freshness(acc, now=None, stale_days=None, grace_days=None) -> (label, days)` نقية: `quarantine_info.reason=="stale_daily_gift"` → STALE؛ `days_without_gift` غير رقمي/سالب → UNKNOWN؛ `last_checked` مفقود → UNKNOWN؛ عمر اللقطة يُضاف للأيام (متشائم)؛ `aged >= 14` → STALE مهما قدُمت اللقطة؛ لقطة > 72h → UNKNOWN؛ `[11,14)` GRACE؛ `<11` FRESH.
  - `get_eligible_accounts`: بعد `is_account_ready` — STALE يُستبعد + لوج `[GIFT_PREFLIGHT]`؛ FRESH/GRACE بترتيب `last_used`؛ UNKNOWN في الذيل + لوج Fail-Open؛ `GIFT_PREFLIGHT_ENABLED=False` = السلوك القديم حرفيًا. **صفر كتابة/cooldown/عزل.**
  - **لم يُمس**: `is_account_ready`، `send_message_with_auto_account_failover`، 01.03، verifier.
  - الأدلة: `tests/test_p48_gift_preflight.py` **34 passed** (ثوابت 2، تصنيف 16، أهلية 10، عقود مصدر 6 منها CRLF ونقطة حقن واحدة وعدم لمس حلقة failover)؛ الحزمة الكاملة **1168 passed / 26 failed** = نفس الأسماء قبل STEP-2 (0 جديد)؛ `verify_docs_integrity` Exit 0؛ parity أخضر بعد إعادة التوليد.
- [x] docstring 05.02 موحَّد (`days >= threshold_days`)؛ ملفا `GITHUB_SYNC_*.md` محذوفان.

**لم يُنفَّذ (ولا يُدَّعى):** STEP-3؛ إصلاح أي من الـ26 الفاشلة؛ أي تشغيل حي؛ V2 §17.6.

---

## 3) الخطوة التنفيذية التالية مباشرة — STEP-3 (Q-F)

**الهدف:** دمج حسابات ملف المعزل القديم (`accounts_genspark_blocked_failed__block_failed.json` — `QUARANTINE_FILENAME` في verifier:39) داخل `accounts_failed.json` مع نسخة أرشيفية مؤرخة للملف القديم.

**الترتيب الآمن:**
1. اختبارات أولًا `tests/test_p49_legacy_quarantine_merge.py` (tmp_path فقط): دمج بلا تكرار (email lower)، حفظ الحقول القديمة تحت `legacy_quarantine`، أرشفة `.bak` مؤرخة قبل أي كتابة، dry-run افتراضي لا يكتب، ملف قديم مفقود/تالف → لا تغيير + رسالة، idempotent عند التشغيل مرتين.
2. سكربت جديد `scripts/merge_legacy_quarantine.py` يعتمد `create_backup`/`atomic_save_json`/`load_accounts` من 05.02 (تحميل بـ`spec_from_file_location` + stub لـ`genspark_master_account_manager` كما في STEP-1) — CLI: `--legacy`, `--failed`, `--apply` (بدونه dry-run).
3. **لا تشغيل على ملفات حقيقية إلا بأمر صريح من المالك.**

**سؤال واحد للمالك قبل البدء:** هل اسم/موقع `scripts/merge_legacy_quarantine.py` مقبول (داخل SCOPE الحالي: `scripts/` ليست مدرجة صراحة)؟ إن فضّلت وضعه كأمر CLI داخل 05.02 (`--merge-legacy`) فذلك يحتاج إذن تعديل 05.02.

---

## 4) سياق مطلوب من المالك
1. تأكيد نطاق STEP-3 (أعلاه).
2. قرار BASELINE-DRIFT للـ14 المتبقية (تحديث اختبارات لتعكس v5.4 أم مهمة منفصلة) — اختياري، لا يحجب STEP-3.

## 5) فحص الصحة عند كل استئناف (أقوم به تلقائيًا)
`git fetch` → `checkout -B genspark_ai_developer origin/genspark_ai_developer` → قراءة رأس PROGRESS + هذا الملف → `pytest -q` ومطابقة الخط الأساسي **بالأسماء** (13 تاريخية + 13 drift موثقة أعلاه حتى يقرر المالك) → `python scripts/verify_docs_integrity.py` Exit 0 → البدء من أول `[ ]`.
