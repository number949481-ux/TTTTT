# ⚡ 17_FAST_LEAN_MODE_AND_ARTIFACTS_BYPASS.MD
## وثيقة المواصفات المعتمدة — SSOT التنفيذي الكامل لـ PHASE 43
### DEC-039: Fast Lean Mode & Artifacts/Diff Bypass

> **مصدر هذه الوثيقة:** النسخة المُفلترة (Commit `1128971`) بعد دمج **قرارات المالك D1–D7**
> من التوجيه الرسمي `17.04_FAST_LEAN_MODE_AND_ARTIFACTS_BYPASS.MD` + أدلة الفحص الجنائي
> التحضيري S1–S2 (جلسة 2026-08-23/24، السورس `01.33_telegram_gen_bridge.py` = **8212 سطراً**).
>
> **⚠️ Baseline المُقاس (S1 — حسم تضارب 883/946):** `pytest tests/ -q` ➔ **946 passed**
> (+12 subtests) + `hadith_sijil.py` ➔ **Exit 0** + `rebuild_refactor.py` ➔ **Exit 0** (parity 11/11).
> الرقم 946 هو الحقيقة؛ 883 كان baseline P41 قبل إغلاق P42.
>
> **🚨 أرشيف محظور التنفيذ منه:** `17.02` + `17.03` (مسودات خام ملغّمة بالأشباح:
> `fetch_sandbox_archive` / `p11_worker.py` / `download_artifacts` / `cmd:toggle_fast_mode` /
> أرقام غير مقاسة). المرجع الوحيد = هذه الوثيقة + قرارات D1–D7 المدموجة فيها.
>
> **⚠️ حالة التفعيل:** التنفيذ لا يبدأ إلا بعد اعتماد المالك لبرومبت الاستئناف
> (بوابة S6 — RESUME PROMPT APPROVAL GATE).

---

## 🧹 0. سجل الفلترة والأدلة — ما ثبت وما سقط

### ✅ الادعاءات المُثبتة (F1–F13 — أرقام أسطر جلسة 2026-08-23/24 بعد إعادة grep في S1ج):
| # | الادعاء | الدليل من السورس |
|---|---------|------------------|
| F1 | دالة التنزيل الحقيقية `download_project_archive` | سطر **2113** — `sess.get(..., timeout=180)` |
| F2 | موضع الاستدعاء داخل مسار التوليد | سطر **2612**: `archive_path = None if _declined else download_project_archive(...)` |
| F3 | النشر العام `make_project_always_public` (حتى 3 طلبات POST ×15s) | تعريف **2160** — استدعاء **2616** |
| F4 | سابقة P40 Decline Fast-Path جاهزة للتوسيع | أسطر **2604–2616**: `_declined` ➔ تخطي التنزيل والنشر + رابط `autopilotagent_viewer?id={pid}` بلا شبكة |
| F5 | `snapshot` هي المستهلك الثقيل | سطر **3818**: `rglob` + `copy2` + sha256 لكل ملف |
| F6 | تصنيف الـ Diff داخل `snapshot` | أسطر ~3846–3867 (مقارنة sha256 مع prior_index) |
| F7 | `registry.snapshot`/`github_sync` في worker الجسر | سطرا **6434**/**6436** داخل `on_project_update` (**6415**) ضمن `process_user_task_async` (**6332**) |
| F8 | لوحة الإعدادات `build_project_settings_keyboard` | سطر **5060** — router `pset:*` سطر **7237** |
| F9 | Normalization يضمن Backward-Compat تلقائياً | `default_project_settings` **444** + `_normalize_project_settings` **3092** + `update_project_settings` خلف `self.lock` (**3217–3218**) |
| F10 | **[D1]** Whitelist الـ style موجودة فعلاً | `ALLOWED_BUTTON_STYLES = frozenset({"primary","success","danger"})` سطر **4819** + الفحص في `make_inline_keyboard` سطر **4846** + سوابق استخدام: primary (4478/4483)، danger (4477/5208)، success (4492) — P11 أدخلت style في Bot API 9.4 |
| F11 | **[D4]** نقطة حقن خطوة الـ Wizard | فرع `cmd:new_proj_github_no`/`disable` سطر **7113** (قبل `AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION`) + `finalize_new_project_from_state` سطر **5649** + موضعا finalize مع `forward_pending_prompt_after_wizard` سطرا **7195/7856** — `pending_prompt` ينجو عبر `**state` |
| F12 | **[D6]** namespace أزرار كارت المشروع | `pctl:*` — الكيبورد أسطر **5194–5208** (`pctl:archive`/`pctl:files`/`pctl:sync`...) + handler سطر **7376** |
| F13 | **سابقة تخطي checkpoint شرعية (P40 نفسها)** | `should_capture_project_update` (**6068**) يتطلب artifacts طازجة (`inspect_stage_artifacts` **6035**)؛ بلا أرشيف ➔ `actionable=False` ➔ snapshot لا تُستدعى، بينما `save_project_branch` (**2618**) يحفظ شجرة الاستئناف دائماً. الوضع السريع يرث هذا العقد حرفياً — **لا حاجة لـ checkpoint metadata مبتدع** |

### ❌ المرفوضات النهائية (لا تدخل أي كود — مرفوضات المالك R1–R3 + هلوسات المسودة):
| # | البند الساقط | السبب |
|---|--------------|-------|
| X1 | `fetch_sandbox_archive()` | اسم شبح — grep = صفر. البديل الوحيد: `download_project_archive` |
| X2 | `p11_worker.py` | ملف شبح — Single-File Doctrine؛ الـ worker داخل `01.33` |
| X3 | الأرقام الزمنية غير المقاسة (15s/0.5s/0.2s) | تُستبدل بالحدود المثبتة (180s + 3×POST×15s)؛ القياس الفعلي في CP1 (اللوج الحالي خالٍ من أسطر توقيت — أُثبت في S2) |
| X4 | ~~«أسطورة الزر الأزرق»~~ | **صُحح بقرار D1**: الـ style حقيقي ومدعوم (F10) — الزر يأخذ `"style": "primary"` + إيموجي 🔵/⚪ |
| X5 | `cmd:toggle_fast_mode:*` | **[R3]** namespace مرفوض — المعتمد `pset:fastmode:{project_key}` |
| X6 | حقل `download_artifacts` أو أي Invariant بين حقلين | **[R1]** حقل واحد `fast_mode: bool` فقط — SSOT |
| X7 | «ضبط `modified_files_count = 0`» | تزوير بيانات — الكارت يعلن التخطي صراحةً |
| X8 | جعل fast_mode افتراضياً في الـ Wizard | **[R2 + D5]** الافتراضي `False` للجميع — لا استثناء |

---

## 🎯 1. الملخص التنفيذي

### 1.1 المشكلة (CAUSE — بالمواضع المثبتة):
بعد انتهاء الموديل، يمر كل مشروع — حتى غير المربوط بـ GitHub — بـ Pipeline إلزامي:
1. `download_project_archive` (2612 ➔ 2113): طلب بمهلة **180s** + كتابة `webapp.tar.gz` + فك ضغط.
2. `make_project_always_public` (2616 ➔ 2160): حتى **3 طلبات POST ×15s**.
3. `registry.snapshot` (6434 ➔ 3818): نسخ الشجرة + **sha256 لكل ملف** + تصنيف Diff.
4. `registry.github_sync` (6436): لا-عملية عند تعطيل GitHub لكنها تُستدعى.

### 1.2 الأهداف (بعد حسم D2):
- **G1 — تخطٍ اختياري آمن:** عند `fast_mode=True` + GitHub معطل ➔ تخطي **التنزيل + فك الضغط + snapshot الثقيل فقط**. **`make_project_always_public` تبقى تعمل** (قرار D2 — لا دليل Terminal أن الرابط يفتح عاماً بدونها؛ سابقة P40 تخطتها لمشروع مرفوض لا يحتاج معاينة، وهذا لا يصلح دليلاً لمشروع مكتمل يُعرض). لو أثبت CP1 بدليل Terminal العكس ➔ يجوز تخطيها ويُسجل الدليل هنا.
- **G2 — واجهة كاملة:** زر Toggle في لوحة الإعدادات (`pset:fastmode:*`) + خطوة Wizard (D4) + زر التنزيل المتأخر (D6).
- **G3 — Zero Regression:** `fast_mode=False` (الافتراضي — D5) = السلوك الحالي بالبايت. GitHub مفعّل = تنزيل إلزامي دائماً (D3).
- **G4 — Telemetry (D7):** سطر لوج `FAST_MODE_SKIP project=<key>` عند كل تخطٍ — أي رقم سرعة يُنشر من قياس فعلي فقط.

---

## 🏗️ 2. هيكل البيانات (Schema)

حقل **واحد** جديد في `project_settings` (يضاف إلى `default_project_settings` سطر 444):

```json
{ "project_settings": { "model": "...", "fast_mode": false, "continuation": {}, "github": {} } }
```

- الافتراضي `false` للجميع (D5/R2) — `_normalize_project_settings` (3092) يقرأ المشاريع القديمة بلا الحقل كـ `false` تلقائياً (F9).
- لا حقل ثانٍ ولا Invariant (R1).

### الدالة الحاكمة (D3 — التوقيع حرفياً، وسيط واحد):
```python
def should_skip_artifacts_download(project_settings: dict) -> bool:
    gh = project_settings.get("github") or {}
    if bool(gh.get("enabled", False)):
        return False
    return bool(project_settings.get("fast_mode", False))
```

---

## 🎨 3. الواجهة (UI)

### 3.1 زر التبديل في لوحة الإعدادات (`build_project_settings_keyboard` سطر 5060):
صف مستقل تحت صف token/toggle — **بستايل `"style": "primary"` عبر Whitelist القائمة (D1/F10)**:
- مفعّل: `🔵 ⚡ الوضع السريع: مفعّل (تخطي تنزيل الساندبوكس)`
- معطّل: `⚪ 📦 تنزيل الملفات: مفعّل (حفظ الساندبوكس والـ Diff)`
- **CallbackData: `pset:fastmode:{project_key}`** (14 بايت + key ≤ حد 64) — داخل router الـ `pset:*` القائم (7237)، لا handler موازٍ.

### 3.2 خطوة Wizard الإنشاء (D4 — الموضع المحسوم من S2):
تُعرض **فقط** في فرع `cmd:new_proj_github_no`/`cmd:new_proj_github_disable` (سطر 7113) — لأن GitHub المفعّل يجعل التنزيل إلزامياً فلا معنى للسؤال:
- حالة جديدة `AWAITING_NEW_PROJECT_FAST_MODE` بين GITHUB_MODE(no) و RESUME_PROMPT_DECISION.
- زران: `📦 مشروع متكامل — حفظ الساندبوكس والـ Diff` (الافتراضي، style=primary) / `⚡ توليد فائق السرعة — تخطي تنزيل الملفات`.
- الاختيار يُحمل في `pending_fast_mode` داخل الـ state (بنمط `pending_github_*` القائم) ➔ `finalize_new_project_from_state` (5649) يقرؤه ويمرره لـ `finalize_new_project_setup`.
- **نجاة `pending_prompt` إلزامية** عبر `**state` (نفس نمط 7113 الحالي) — حارس اختبار مخصص.
- مسار GitHub-yes لا يرى الخطوة إطلاقاً ➔ `fast_mode=False` ضمنياً.

### 3.3 زر التنزيل المتأخر (D6 — namespace محسوم من S2):
زر `⬇️ تنزيل الساندبوكس الآن` في كارت تفاصيل المشروع السريع (كيبورد `pctl:*` أسطر 5194–5208):
- **CallbackData: `pctl:fetch:{project_key}`** (11 بايت + key — آمن) داخل handler `pctl:*` القائم (7376).
- ينفّذ الـ Pipeline الكامل عند الطلب **بنفس الدوال القائمة بلا نسخ**: `download_project_archive` ➔ `registry.snapshot` ➔ (github_sync إن مفعّل).
- جلسة/كوكيز منتهية ➔ رسالة فشل صريحة بلا Crash. ضغط مزدوج ➔ Idempotent (تنزيل جارٍ/مكتمل ➔ «تم بالفعل»).

---

## ⚙️ 4. منطق التخطي (Worker Bypass)

### 4.1 نقطة الحقن (توسيع P40 حرفياً — أسطر 2604–2616):
- العلم يصل عبر `bridge_cfg` (نمط `apply_project_runtime_binding` القائم — سطر 428).
- **الترتيب: `_declined` أولاً ثم fast skip** — `skip_archive = _declined or fast_lean_skip`:
  - `archive_path = None` عند التخطي.
  - **`make_project_always_public` تبقى تعمل في fast mode** (D2) — تخطيها يبقى حصرياً لفرع `_declined` (P40 كما هي).
  - `save_project_branch` (2618) بلا حراسة — شجرة الاستئناف `tree:*` محفوظة دائماً.
- Telemetry (D7): `log_event("info", f"⚡ [P43] FAST_MODE_SKIP project={project_key} pid={pid[:16]}")`.

### 4.2 سلوك on_project_update (F13 — بلا اختراع):
عند التخطي لا توجد artifacts طازجة ➔ `should_capture_project_update` ترجع `actionable=False` بالعقد القائم ➔ snapshot/github_sync لا تُستدعيان — **نفس مسار P40 الحالي حرفياً، صفر كود جديد هنا**. الاستئناف يعتمد على URL/PID من `save_project_branch` لا على الملفات (يُثبت باختبار).

### 4.3 الشفافية (X7):
كارت الإكمال في الوضع السريع يعرض `⚡ الوضع السريع — تم تخطي تنزيل الملفات والـ Diff` + زر D6 — لا إحصائيات Diff مزيفة.

### 4.4 المجمّد (Frozen Scope):
⛔ المحرك `01.03` | دلالات Success/Resume/Rotation/Failover/CREDIT_EXHAUSTED | أجسام `download_project_archive`/`make_project_always_public`/`snapshot` (تُستدعى بشرط، لا تُعدّل) | عقود P40/P41/P42 | أي Refactor خارج نقاط الحقن.

---

## 🧨 5. الحالات الحدية (15):
1. تبديل الزر أثناء مهمة جارية ➔ العلم يُقرأ عند بدء المهمة فقط — يسري من التالية.
2. GitHub مفعّل + `fast_mode=True` ➔ التنزيل إلزامي (D3 يفوز).
3. مشروع قديم بلا الحقل ➔ `False` عبر Normalization (F9).
4. TIMEOUT في fast mode ➔ نفس مسار TIMEOUT الحالي (التخطي في فرع الإكمال فقط).
5. رد رفض P40 + fast mode ➔ `_declined` يفوز أولاً (يتخطى النشر أيضاً) — شرط OR بترتيب صريح.
6. استئناف مشروع fast ➔ يعمل عبر URL/PID (F13) — يُثبت باختبار.
7. ضغط مزدوج على Toggle ➔ طبيعي (خلف `self.lock` — F9).
8. أمر/رابط أثناء أي حالة ➔ قواعد P41/P42 كما هي.
9. حد 64 بايت: `pset:fastmode:` (14) و`pctl:fetch:` (11) + key ➔ آمن.
10. تفعيل GitHub لاحقاً على مشروع fast ➔ التنزيل يعود إلزامياً من المهمة التالية (D3) والمزامنة الأولى ترفع snapshot كاملاً جديداً.
11. زر D6 بجلسة/كوكيز منتهية ➔ رسالة فشل صريحة، صفر Crash، الكارت يبقى صالحاً لإعادة المحاولة.
12. زر D6 ضغط مزدوج ➔ Idempotent («التنزيل تم/جارٍ بالفعل»).
13. نجاة `pending_prompt` (P42) عبر خطوة `AWAITING_NEW_PROJECT_FAST_MODE` الجديدة ➔ حارس مخصص.
14. مشروع fast + زر `pctl:archive`/`pctl:files` ➔ رسالة واضحة «لا أرشيف — الوضع السريع، استخدم ⬇️ تنزيل الآن» بدل صمت مبهم.
15. manifest جديد يُكتب بالحقل صراحةً والقديم يُقرأ بلا الحقل — كلاهما عبر `_normalize_project_settings` حصرياً (لا قراءة مباشرة).

---

## 🧪 6. مصفوفة الاختبارات — `tests/test_p43_fast_lean_mode.py` (16 — Mocks/Spies بلا شبكة):
1. `test_default_settings_include_fast_mode_false` — الحقل في الافتراضيات (D5).
2. `test_old_manifest_without_field_reads_false` — Backward-Compat (F9).
3. `test_skip_helper_github_enabled_forces_download` — D3/الحدية 2.
4. `test_skip_helper_fast_off_returns_false` — D3.
5. `test_toggle_fastmode_callback_flips_and_persists` — `pset:fastmode` يعكس ويحفظ ويحدّث الكيبورد.
6. `test_settings_button_uses_primary_style_whitelist` — D1 (style ضمن ALLOWED_BUTTON_STYLES).
7. `test_worker_skips_download_when_fast_mode` — Spy: صفر استدعاء لـ `download_project_archive`.
8. `test_worker_keeps_make_public_in_fast_mode` — D2 (النشر العام يعمل).
9. `test_worker_downloads_when_fast_mode_off` — Zero-Regression بايت-ببايت.
10. `test_fast_mode_telemetry_log_line` — D7 (`FAST_MODE_SKIP`).
11. `test_fast_mode_completion_card_transparent` — إعلان التخطي، لا Diff مزيف (X7).
12. `test_wizard_fast_step_only_when_github_disabled` — D4 (مسار GitHub-yes لا يرى الخطوة).
13. `test_wizard_fast_selection_sets_flag_and_pending_prompt_survives` — D4 + الحدية 13.
14. `test_late_fetch_button_runs_full_pipeline` — D6 (نفس الدوال القائمة).
15. `test_late_fetch_failure_and_idempotency` — الحديتان 11–12.
16. `test_p40_decline_and_frozen_contracts_unchanged` — عقود P40/Success/Resume/Rotation/Cancel.

---

## 📋 7. خطة الـ Checkpoints (CP0–CP9 — لكل CP: دليل Terminal ➔ Checkbox ➔ Commit):
- [x] **CP0**: قراءة ملفات التوجيه + إثبات Baseline (946/946 + Exit 0 + Parity 11/11) بمخرجات حقيقية — ✅ 2026-08-24: `pytest tests/ -q` ➔ 946 passed +12 subtests + `hadith_sijil.py` Exit 0 + `rebuild_refactor.py` Exit 0 + `test_refactor_parity.py` 11 passed (بعد إخراج .pytest_cache/bridge_bot.log التي أعادتها المزامنة للتتبع).
- [x] **CP1**: إعادة إثبات المواضع بـ grep بأرقام جلسة التنفيذ + **قياس زمني فعلي** — ✅ 2026-08-24 (جلسة التنفيذ): **كل أرقام F1–F13 مطابقة بلا انزياح** (2113/2612/2160+2616/2604–2616/3818/3846–3867/6434+6436+6415+6332/5060+7237/444+3092+3217–3218/4819+4846/7113+5649+7195+7856/5194–5208+7376/6068+6035+2617). **القياس الفعلي**: محاكاة عقد snapshot الحرفي (rglob+copy2+sha256) على شجرة 400 ملف/12MB ➔ **0.162s** + تمرير Diff ➔ **0.054s** ⇒ العبء المهيمن شبكي حصراً (التنزيل timeout=180s + النشر 3×POST×15s — الحدود المثبتة من السورس؛ غير قابلة للقياس أوفلاين بلا جلسة حية — X3 محترم، لا أرقام سرعة إجمالية تُنشر قبل قياس E2E حي). اللوج الحالي (418KB) خالٍ من أسطر توقيت (grep=0) — يؤكد S2. **دليل D2 الاختياري**: يتطلب جلسة Genspark حية — غير متاح ➔ قرار D2 يبقى كما هو (make_public تعمل في fast mode).
- [x] **CP2**: حقل `fast_mode` في `default_project_settings` + الدالة الحاكمة D3 + اختبارات 1–4 — ✅ 2026-08-24: الحقل عند السطر 447 (default=False — D5/R2) + `should_skip_artifacts_download` عند 468–478 (توقيع D3 حرفياً، وسيط واحد) + `_normalize_project_settings` يقرأ المشاريع القديمة كـ False (F9 — سطر 3113) + معالجة `fast_mode` في `update_project_settings` (bool حصراً — سطر 3240–3242) + `tests/test_p43_fast_lean_mode.py` (اختبارات 1–4: Schema/Backward-Compat/D3×2) ➔ **4 passed** + الكلي **950 passed +12 subtests** + hadith_sijil Exit 0 + تحديث حدود PARTS في `rebuild_refactor.py` (p02: 156–480 / p07: 2993–3985 وما بعدهما) ➔ rebuild Exit 0 + **Parity 11/11**. لا `download_artifacts` شبح (حارس نصي في الاختبار 1).
- [x] **CP3**: زر `pset:fastmode:*` بستايل primary (D1) + المعالج في router الـ `pset` القائم + اختبارات 5–6 — ✅ 2026-08-24: الزر في `build_project_settings_keyboard` سطر **5092** (صف مستقل، ليبل مزدوج ⚡/📦 + `"style": "primary"` عبر Whitelist F10، CallbackData `pset:fastmode:{key}` ≤ 64 بايت) + المعالج فرع `elif action == "fastmode"` سطر **7400** داخل router الـ `pset:*` القائم (لا handler موازٍ — X5/R3): يعكس القيمة عبر `update_project_settings({"fast_mode": ...})` ثم يعيد إرسال اللوحة بالكيبورد المحدّث + رسالة شفافة تذكر أولوية GitHub (D3). الاختباران 5–6 في `tests/test_p43_fast_lean_mode.py` (Toggle مزدوج الاتجاه مع الحفظ على القرص + الزر ضمن ALLOWED_BUTTON_STYLES ونجاته من فلترة make_inline_keyboard) ➔ **6 passed** بالملف + الكلي **952 passed +12 subtests** + hadith_sijil Exit 0 + تحديث حدود PARTS (p09➔4544–6051 / p10➔6052–6346 / p11➔6347–6727 / p12➔6728–8257) ➔ rebuild Exit 0 + **Parity 11/11**.
- [x] **CP4**: حقن التخطي في 2604–2616 (**`_declined` أولاً**) + إبقاء make_public (D2) + Telemetry D7 + كارت الإكمال الشفاف + اختبارات 7–11 — ✅ 2026-08-24: الحقن عند **2637–2649** (انزياح بعد CP2/CP3): `fast_lean_skip` من `bridge_cfg.project_fast_lean_skip` (يركب عبر `apply_project_runtime_binding` سطر 447 بالدالة الحاكمة D3) + `skip_archive = _declined or fast_lean_skip` (الحدية 5 — الرفض يفوز) + `archive_path=None` عند التخطي + **make_project_always_public تعمل في fast mode (D2)** — تخطيها بقي حصرياً لفرع `_declined` + `save_project_branch` بلا حراسة + سطر Telemetry `FAST_MODE_SKIP project=<key> pid=<pid16>` (D7 — سطر 2648، يُطبع فقط عند fast بلا رفض) + الكارت الشفاف X7: `fast_mode_line` في كارت الإكمال (أسطر 6686–6699) «⚡ الوضع السريع — تم تخطي تنزيل الملفات والـ Diff» بلا إحصائيات مزيفة. الاختبارات 7–11 (Spy على download/make_public + Zero-Regression بايت-ببايت + Telemetry + الكارت) ➔ **11 passed** بالملف + الكلي **957 passed +12 subtests** + hadith_sijil Exit 0 + تحديث حدود PARTS (p02➔156–487 / p06➔1993–3015 / p11➔6370–6756 / p12➔6757–8286) ➔ rebuild Exit 0 + **Parity 11/11** + إخراج `.pytest_cache`/`bridge_bot.log` من التتبع مجدداً (أعادتهما المزامنة).
- [x] **CP5**: زر D6 `pctl:fetch:*` (الـ Pipeline الكامل بالدوال القائمة + فشل صريح + Idempotency) + رسالة الحدية 14 + اختبارات 14–15 — ✅ 2026-08-24: الزر «⬇️ تنزيل الساندبوكس الآن» في `build_current_project_keyboard` سطر **5339** (`pctl:fetch:{key}` = 11 بايت + key ≤ 64 — الحدية 9، style=primary عبر Whitelist) + الدالة `run_project_late_fetch` سطر **5254** (Pipeline كامل بالدوال القائمة بلا نسخ: download_project_archive ← استخراج آمن ← snapshot — فشل صريح للجلسة المنتهية برسالة ودية + Idempotent للضغط المزدوج) + المعالج فرع `if action == "fetch"` سطر **7592** داخل router الـ `pctl:*` القائم (لا handler موازٍ — X5/R3). الاختباران 14–15 (`test_late_fetch_button_runs_full_pipeline` + `test_late_fetch_failure_and_idempotency`) ➔ PASS.
- [x] **CP6**: خطوة Wizard (D4) + نجاة pending_prompt + اختبارات 12–13 — ✅ 2026-08-24: `build_new_project_fast_mode_keyboard` سطر **5751** (الافتراضي 📦 متكامل style=primary — D5/R2) + الخطوة تُعرض فقط عند تخطي GitHub (فرع التخطي سطر **7302**، `pending_fast_mode: False` أولياً) + معالجا `cmd:new_proj_fast_no/yes` سطر **7305–7315** (`pending_fast_mode: chosen_fast` في state مع بقاء pending_prompt) + `finalize_new_project_setup` يستقبل معامل `fast_mode` (سطر 5785–5792) وحارس `and not github_enabled` سطر **5820** (D3 — GitHub مفعّل يُبطل الاختيار). الاختباران 12–13 (`test_wizard_fast_step_only_when_github_disabled` + `test_wizard_fast_selection_sets_flag_and_pending_prompt_survives` — نجاة pending_prompt بحارس صريح) ➔ PASS.
- [x] **CP7**: اكتمال الـ 16 اختباراً + اختبار 16 (Zero-Regression) + تحديث حدود PARTS + إعادة بناء `bridge_refactor/` + Parity 11/11 — ✅ 2026-08-24: `tests/test_p43_fast_lean_mode.py` ➔ **16 passed** (يشمل الاختبار 16 `test_p40_decline_and_frozen_contracts_unchanged` — Zero-Regression لعقود P40 المجمدة) + تحديث حدود PARTS للملف 8422 سطراً (p09➔4567–6186 / p10➔6187–6481 / p11➔6482–6868 / p12➔6869–8422 — معالم متحققة: `_is_fresh_artifact`@6187 / `format_active_account_line`@6482 / فاصل P42@6869) + أوصاف P43 في p09/p12 + `rebuild_refactor.py` Exit 0 + **Parity 11/11 PASS** (Commit `662d79f`).
- [x] **CP8**: البوابات: pytest 100% (946 + 16، بلا Skip جديد) + hadith_sijil Exit 0 + نظافة Git — ✅ 2026-08-24: `pytest tests/ -q` ➔ **962 passed + 12 subtests** (946 baseline + 16 P43، صفر فشل/صفر Skip جديد) + `hadith_sijil.py` ➔ **Exit 0** + نظافة Git مستعادة (إخراج `.pytest_cache`/`bridge_bot.log` اللتين أعادتهما المزامنة + تثبيتهما في `.gitignore` — Commit `1cfd6e2`، وبها عاد اختبارا P17 `TestGeneratedFilesUntracked` للنجاح).
- [x] **CP9**: التوثيق الكامل + Commit نهائي + التقرير — ✅ 2026-08-24: **PROGRESS الجذري** (نقطة استئناف جديدة S69–S71/P43 + أرشفة S67–S68) + **docs/engineering/PROGRESS.md** (قسم P43 بمهام TSK-6001–6005) + **SESSION_LOG.md** (قرار DEC-039 كاملاً: السبب المثبت + D1–D7 + التنفيذ الثلاثي + الحراسة + البوابات) + **V3_RESUME_SESSION.md** (قاعدة P43 الدائمة بالبنود السبعة + عدادات 962) + **TEST_SUITE_CATALOG.md** (صف P43 بـ 16 حارساً ➔ 37 ملفاً / 962 + تصحيح سطر Parity لـ 8422) + **README الجذري** (Milestone P43 + 962) + **docs/engineering/README.md** (Phase 43 + 8422 سطراً + 962) + هذه الوثيقة (كل Checkboxes CP0–CP9 محسومة [x]) + تحديث **البند 7** في `Deep_Thinking_Tasks_Remaining.TXT` (P43 مُقفلة ➔ الحالة BLOCKED-ON-OWNER بانتظار المهمة التالية) + **بلوك ## 0** في `00_MASTER_RESUME_PROTOCOL.md` بنفس الحالة. البوابات الختامية بعد التوثيق: pytest ➔ **962/962 PASS** + hadith_sijil ➔ **Exit 0** + Parity **11/11**.

---

## 📑 8. عناوين التقرير النهائي (حرفياً وبالترتيب):
`STATUS → CAUSE → EVIDENCE → CALL PATH → FIX DESIGN → CHANGES → TESTS → PARITY → QUALITY GATE → GIT → REMAINING RISK → NEXT RESUME POINT`

---

## ⚖️ 9. القواعد الحاكمة (Non-Negotiable):
- **Evidence-First**: أي ادعاء (خصوصاً أرقام السرعة) بلا مخرجات Terminal = غير منجز.
- **Zero Blind Mutation** + **Micro-Tasking** + **Single-File Doctrine** (التعديل في `01.33` فقط).
- **لا شبح (R1–R3)**: `fetch_sandbox_archive` / `p11_worker.py` / `download_artifacts` / `cmd:toggle_fast_mode` / أرقام غير مقاسة — محظورة.
- أرقام الأسطر مرجعية بتاريخ 2026-08-23/24 — يُعاد التحقق في CP1.
- أي التباس يمس النطاق المجمّد ➔ BLOCKED-ON-OWNER في PROGRESS.md بدل الاجتهاد.
- **بوابة الموافقة**: التنفيذ (CP0+) لا يبدأ قبل موافقة المالك الصريحة على برومبت الاستئناف.

---
*نهاية الوثيقة — الأرشيف التاريخي المحظور: `17.02` + `17.03` (تحت بانر). توجيه المالك: `17.04`.*
