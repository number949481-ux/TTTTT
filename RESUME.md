# RESUME.md — نقطة الاستئناف الحية للوكيل

> يُحدَّث عند كل محطة إنجاز (Milestone) جنبًا إلى جنب مع رأس `PROGRESS.md`.
> لا يحتوي أرقام commit ثابتة كمرجع تنفيذ؛ القاعدة دائمًا = أحدث HEAD في `origin/genspark_ai_developer`.
> لا أسرار هنا أبدًا.

---

## 1) أين أقف الآن؟ (2026-10-31)

| البند | الحالة |
|---|---|
| الفرع | `genspark_ai_developer` فقط (main READ-ONLY، لا فروع جانبية) |
| HEAD المسحوب في هذه الجلسة | `73256fa` (2026-10-31؛ للتوثيق فقط — اسحب الأحدث دائمًا). منذ `a3cd2e3` وصلت 4 commits من المالك: `93456ad` p47 (Telegram 429/throttle/priority claim)، `a3cd2e3`/`bb4a4a9` وثائق وVoice Notes 5–6، `73256fa` v5.4 atomic git data sync + 4 edge invariants + SRE 360. تمسّ `01.33` (9561 سطرًا) في 6 hunks (918، 3261–3297، 4454–4497، 7687) **لا تشمل دوال الحسابات**؛ مراسي STEP-2 ثابتة: `read_accounts_safe` 1052، `update_account_data` 1068، `is_account_ready` 1104، `get_eligible_accounts` 1171، `mark_account_cooldown` 1187، `refresh_cookies_on_401` 1201، `send_message_with_auto_account_failover` 3312. STEP-1 ما زالت **34 passed** على هذا HEAD. |
| PR | #9 Draft (يبقى Draft؛ لا merge) |
| وضع التسليم | **حفظ محلي في `/home/user/webapp` فقط** → أداة المزامنة الخارجية (Bridge Sync Engine) ترفع تلقائيًا. لا push، لا gh auth، لا ZIP. |
| المرحلة | **ALIGN-0 — مواءمة هندسية قبل أي كود** (بطلب المالك). بانتظار اعتماد الخطة أدناه. |

### ⚠️ انحراف الخط الأساسي للاختبارات (BASELINE-DRIFT) — مُكتشف في هذه الجلسة
`pytest tests -q` على HEAD الحالي = **1134 passed / 26 failed / 1 skipped** (كان 1106 / 13 عند `65f7078` في الـsandbox نفسه).
الـ26 = **13 تاريخية** (auto_compact ×5، credit_completion_recovery ×3، p2_model_routing ×2، p32 banned_state، p3 opus5 contract، refactor_parity) **+ 13 جديدة**:

| الاختبار الجديد الفاشل | السبب (فحص سريع بالأدلة) | التصنيف |
|---|---|---|
| `test_p46_timing_metrics_separation::test_parity_between_p03_and_main_bridge` | `منفصل تماماً` 2× في 01.33 مقابل 3× في `bridge_refactor/parts/p03` — الجزء المولَّد لم يُعَد توليده بعد `73256fa` | انحدار/parity drift |
| `test_p17_hardening::test_04_p20_decision_documented` + `test_p20_rest_only::test_08_…_inline` | علامة `[P20]` أُزيلت من `_default_github_uploader` في `e70363a` (gh_bulk v5.4) | انحدار توثيقي |
| `test_p26_project_deletion::test_06_index_cleanup_under_registry_lock` | `shutil.rmtree(project_dir)` لم يعد في `delete_project_atomically` (كان موجودًا عند `65f7078`) | انحدار عقد مصدر |
| `test_p33_completed_quick_actions::test_01_worker_calls_central_builder` | جسم `process_user_task_async` تغيّر في `73256fa` (hunk 7687) | انحدار عقد مصدر |
| `test_p24_qwen_commit_bridge` ×2 + `test_p31_lazy_qwen_prefix` ×5 | بادئة Qwen تعود `''` / `generate_ai_summary` لا يُستدعى — سلوك تغيّر في commits المالك | انحدار سلوكي |
| `test_p47_telegram_429_throttling::test_p47_automatic_429_backoff_recovery` | `ModuleNotFoundError: curl_cffi` (غير مثبت في الـsandbox) | بيئي |

**لم أُصلح أيًا منها** — خارج المهمة الحالية، وقبل اعتماد الخطة. القرار للمالك: (1) إعادة توليد الأجزاء عبر `scripts/rebuild_refactor.py` + تحديث الاختبارات المتأثرة لتعكس v5.4، أو (2) مهمة إصلاح منفصلة قبل STEP-2، أو (3) اعتماد 26 كخط أساسي مؤقت (غير مستحسن). **الخط الأساسي المعتمد لفحص الانحدار في أي عمل قادم = قائمة الأسماء هذه، لا الرقم.**

### ⚠️ تعارض مرجعي مفتوح يجب أن يحسمه المالك أولًا
رسالة الاستئناف الأخيرة أحالت إلى Gist **جديد**: `gist.github.com/pijsal1-tech/d7e933267ab63c441e9097c5af9d6334`
- محتواه: `DIAGNOSTIC_COMPACT_ISSUE.md` (2026-09-09، revision واحدة) — تشخيص **compact deadlock** (`run_verified_compact` / `COMPACT_FAILED` / `compact_state["due"]` المحتبس).
- الفحص على HEAD الحالي: الرمز `COMPACT_FAILED` **غير موجود في أي ملف `.py` تشغيلي**؛ مسار فشل الضغط يعتمد الآن `deferred/bypass_ready` (01.33 ~4664–4685، 7486–7491) ومُغطى بـ`tests/test_auto_compact.py`؛ سجل `genspark/recovery_state.json → completed_compact_credit_execution` يوثق إغلاق هذا العطل عبر PR #7 بموافقة المالك.
- بينما `PROGRESS.md` والـGist السابق (`number949481-ux/b64bef6ac…`، rev `d6a0088`، لم يتغير) يخصان **tri-state gift integration** (STEP-2/STEP-3 بعد GO مرحلي + Q-F/Q-C/Q-R).

(أُعيد فحص الـGist في الجولة 2: المالك `pijsal1-tech`، ملف واحد، آخر تحديث 2026-09-09، revision واحدة — لم يتغير.)

**السؤال الحاسم للمالك:** هل المهمة التالية هي (أ) STEP-2 من مسار الهدية الثلاثية كما في PROGRESS، أم (ب) إعادة فتح/مراجعة مسار compact وفق الـGist الجديد، أم (ج) كلاهما بترتيب محدد؟ **لن يُلمس أي ملف تشغيلي قبل الجواب.**

---

## 2) ما تم إنجازه واختباره فعليًا (بالأدلة)

- [x] **STEP-1** — `tests/test_tri_state_isolation.py`: 34 اختبارًا معزولًا لمحرك 05.02 (Fresh/Grace/Stale/Banned/Network/Routing/Helpers). الدليل: `pytest tests/test_tri_state_isolation.py -q` → **34 passed**؛ الحزمة الكاملة 1106 passed / 13 failed (= الأسماء التاريخية نفسها، لا انحدار). منشور على remote.
- [x] **Q-R** — حُذف `manifest.json` و`review_recovery.patch` من الجذر. الدليل: غير موجودين في شجرة remote.
- [x] **SYNC-TEST** — أداة المزامنة ترفع الملفات المعدَّلة والجديدة. الدليل: commits `d8459fa`/`481a8a2`/`0577f59` على remote تحمل الملفين الجديدين وPROGRESS.
- [x] **ALIGN-0 (جزء التوثيق)** — هذا الملف + سطر ALIGN-0 في PROGRESS.

**لم يُنفَّذ (ولا يُدَّعى):** STEP-2، STEP-3، أي إصلاح للـ13 failure التاريخية، أي تشغيل حي، V2 §17.6.

---

## 3) الخطوة التنفيذية التالية مباشرة — **الخطة المقترحة لاعتماد المالك**

### إن كان الجواب (أ) STEP-2: طبقة Pre-Flight لفحص الهدية في الجسر (Q-C)

**المبدأ الهندسي:** لا نُدخل فحص الهدية في قلب حلقة الإرسال؛ نضعه **بوابة واحدة قبل اختيار الحساب**، بعقد تصنيفي واضح، مع fail-open للحالات المجهولة حتى لا نكرر "لغم Fail-Closed" الذي أسقط البوت في حادثة compact.

**العقد (Contract) — ثلاث نتائج فقط:**
| نتيجة الفحص | التصرف |
|---|---|
| `FRESH` / `GRACE` (أيام < 14) | الحساب مؤهل؛ يُرسل |
| `STALE` (أيام ≥ 14) أو `DEAD` | يُستبعد من الاختيار **ويُسجَّل** (`gift_status`, `days_without_gift`, `gift_checked_at`) — لا يُعزل ملفيًا من الجسر؛ العزل الملفي يبقى لـ05.02 |
| `UNKNOWN` (شبكة/HTTP≠200/JSON تالف/B2C مؤقت) | **لا إرسال بهذا الحساب الآن، لا cooldown، لا عزل، لا كتابة** — ينتقل للحساب التالي؛ إن كانوا كلهم UNKNOWN يُستخدم المسار الحالي دون فحص (fail-open معلَن في اللوج) |

**الترتيب الآمن (الأصغر أثرًا → الأكبر):**
1. **اختبارات أولًا** — `tests/test_p45_gift_preflight.py` (اسم مؤقت): يغطي الثلاث نتائج + in-flight يكمل + UNKNOWN لا يكتب شيئًا + التوافق مع `is_account_ready` الحالي. كلها تعمل على نسخ مؤقتة من JSON؛ لا شبكة.
2. **دالة نقية** في 01.33 بجوار `is_account_ready` (~1104 على HEAD الحالي): `classify_gift_freshness(acc, now) -> ("FRESH"|"GRACE"|"STALE"|"UNKNOWN", days)` تقرأ فقط الحقول المخزَّنة (`last_gift_date`/`days_without_gift`/`gift_checked_at`) — **لا تستدعي الشبكة**.
3. **مصدر البيانات:** الجسر لا يستدعي Genspark لفحص الهدية بنفسه (يتعارض مع Rate Limit وحوكمة "لا live")؛ يعتمد على ما يكتبه 05.02 في الحسابات. فحص "حي" داخل الجسر يُقترح كـ**flag اختياري معطَّل افتراضيًا** في `BridgeConfig` (`gift_preflight_live=False`) لقرار لاحق.
4. **نقطة الحقن الوحيدة:** `get_eligible_accounts` (~1171 على HEAD الحالي) — فلتر إضافي بعد `is_account_ready`. لا تعديل في `send_message_with_auto_account_failover` ولا في حلقة failover (~3305+) → الحساب الجاري يكمل طبيعيًا بحكم البناء (Q-C) لأن الفلتر يعمل فقط عند **اختيار** حساب جديد.
5. **Pre-existing:** إن تعارض مع أي من الـ13 failure التاريخية → يُوثَّق فقط، لا جلسة إصلاح شاملة.
6. **Parity:** إن مسّ التعديل جزءًا مولَّدًا من `bridge_refactor/parts/*` يُعاد توليده عبر `scripts/rebuild_refactor.py` وتُشغَّل اختبارات parity؛ وإلا لا يُلمس.

**ملفات التعديل المطلوبة (لاعتماد المالك):** `01.33_telegram_gen_bridge.py` (دالة + فلتر)، `tests/` (ملف جديد)، `PROGRESS.md`، `RESUME.md`. **لا:** 01.03 (READ-ONLY)، verifier (يحتاج إذنًا صريحًا)، 05.02 (إلا توحيد docstring `>` → `>=` إن أُذن).

**حدود معلنة:** لا تشغيل حي، لا migration للحسابات، لا merge إلى main، لا deploy.

### إن كان الجواب (ب) مسار compact:
أول خطوة ستكون **مراجعة فقط** (لا كود): مقارنة بنود الـGist الثلاثة بالكود الحالي بالأسطر، وإثبات/نفي أن كل بند مُعالَج فعلًا على HEAD، مع تقرير أدلة. ثم ننتظر القرار.

### STEP-3 (بعد STEP-2، أيًا كان الترتيب):
أداة دمج ملف المعزل القديم في `accounts_failed.json` مع نسخة أرشيفية (Q-F)، معتمدة على `create_backup`/`atomic_save_json`/`load_accounts` في 05.02؛ اختبارات معزولة أولًا؛ لا تشغيل على ملفات حقيقية إلا بأمر المالك.

---

## 4) سياق أنقصني وأحتاج توضيحه من المالك
1. **المرجع المقصود** (أ/ب/ج أعلاه) — الأهم.
2. **نطاق الملفات** المسموح تعديلها في STEP-2 (المقترح أعلاه).
3. هل الجسر يُسمح له بفحص الهدية **حيًا** (استدعاء Genspark) أم يعتمد على بيانات 05.02 فقط؟ (توصيتي: بيانات فقط + flag معطَّل).
4. توحيد docstring في 05.02 (`>` → `>=14`) — نعم/لا.
5. حذف ملفي `GITHUB_SYNC_*.md` بعد نجاح الاختبار — نعم/لا.
6. **قرار BASELINE-DRIFT** (أعلاه): إعادة توليد + تحديث اختبارات، أم مهمة إصلاح منفصلة، أم اعتماد مؤقت؟

## 5) فحص الصحة عند كل استئناف (أقوم به تلقائيًا)
`git fetch` → `checkout -B genspark_ai_developer origin/genspark_ai_developer` → قراءة رأس PROGRESS + هذا الملف → `pytest -q` ومطابقة الخط الأساسي **بالأسماء** (13 تاريخية + 13 drift موثقة أعلاه حتى يقرر المالك) → `python scripts/verify_docs_integrity.py` Exit 0 → البدء من أول `[ ]`.
