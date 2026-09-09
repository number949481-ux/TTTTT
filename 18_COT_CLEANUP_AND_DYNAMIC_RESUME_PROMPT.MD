# ⚡ 18_COT_CLEANUP_AND_DYNAMIC_RESUME_PROMPT.MD
## وثيقة المواصفات المعتمدة — SSOT التنفيذي الكامل لـ PHASE 44
### DEC-040: Resume Pipeline Integrity
### (B1: Final Reply Discrimination — تمييز الرد النهائي عن سرد العمل الوسيط)
### (B2: Live Resume Prompt Rebind — قراءة حية لبرومبت الاستئناف عند كل استئناف)

---

## 🪪 1. الهوية

| البند | القيمة |
|---|---|
| المرحلة | **PHASE 44** |
| قرار المالك | **DEC-040** |
| الريبو / الفرع | `github.com/number949481-ux/TTTTT` / `main` (حصرياً) |
| الملف الحاكم | `01.33_telegram_gen_bridge.py` (**8422 سطراً** — Single-File Doctrine) |
| المحرك | `01.03Genspark_claude-opus-5-code.py` — **READ-ONLY في P44** |
| Baseline المُثبت (§B — Terminal فعلي S72 / 2026-08-24) | pytest **962/962 PASS (+12 subtests)** + `hadith_sijil.py` **Exit 0** + Parity **11/11** + `git ls-files .pytest_cache bridge_bot.log` فارغ |
| المرجع السابق المقفول | P43 (DEC-039) — ممنوع إعادة فتحها |
| العقيدة | Single-File Doctrine + Test-Before-Talk + Approve-Before-Execute + Zero-Regression + Evidence-First |

---

## 🎯 2. الفهرس التنفيذي (B1 / B2)

| القضية | الملف | المرساة الأساسية | المشكلة | الحل المعتمد |
|---|---|---|---|---|
| **B1 — Final Reply Discrimination** | `01.33` | `detect_response_status` + حلقة المتابعة (polling) + فرع وقف P18 | أي نص ≥ 25 حرفاً بلا كلمات مفتاحية = COMPLETED افتراضياً → كلام التفكير/الأوامر الوسيط يتصنف رداً مكتملاً كاذباً وحلقة المتابعة تقف مبكراً، فيصل للتليجرام رد وسطي بدل الرد الختامي الحقيقي | **Activity Gate** (تغليف بلا تعديل — D5/D9) + **Debounce قراءتين** (D6) + **Stability Check** (D8) + **Final Fetch** بعد خروج الحلقة (D7) |
| **B2 — Snapshot Lock** | `01.33` | `apply_project_runtime_binding` (الربط الأولي) + `get_bridge_cfg_runtime_resume_prompt` (الاستهلاك في فرع CREDIT_EXHAUSTED) | برومبت الاستئناف يُلتقط على `bridge_cfg` مرة واحدة عند انطلاق المهمة؛ تعديل المستخدم يُحفظ في الـ manifest صحيحاً (`set_project_resume_prompt`) لكن كل استئناف داخل الجلسة الشغالة يقرأ الصورة القديمة من الذاكرة — التعديل الحي لا يُطبَّق أبداً | **Live Rebind** قبل بناء `active_query` في فرع CREDIT_EXHAUSTED (D1) + Fail-Open Fallback (D2) + استثناء P20 (D3) + Display Parity (D4) |

---

## 🔬 3. التشخيص الجنائي (BEFORE + السبب الجذري)

### 3.1 — B1: كيف يتقرر «الاكتمال» اليوم (BEFORE)
- `detect_response_status(text)`: تفحص أولاً الكلمات المفتاحية المهيكلة (CREDIT_EXHAUSTED / DATA_RETENTION / SESSION_EXPIRED / FORBIDDEN)، ثم النص القصير/علامات التوليد الجزئي — **وأي نص ≥ 25 حرفاً بلا علامات = `COMPLETED` افتراضياً** (fallback).
- حلقة المتابعة (polling) تأخذ **آخر رسالة `role == "assistant"`** من `fetch_project_messages` وتصنفها بنفس الدالة — وفي وضع الـ Agent، رسائل السرد الوسيط («سأفحص الملف كذا... سأشغّل bash...») هي نفسها رسائل assistant طويلة → COMPLETED كاذب → الحلقة تقف مبكراً و`last_resp_text` = كلام تفكير.
- فرع وقف P18 (تغيّر مؤشر النشاط): `final_status = "COMPLETED"; break` **بدون أي fetch أخير** — حتى الوقف الصحيح يترك `last_resp_text` حاملاً آخر رسالة وسطية التُقطت قبل الاكتمال الفعلي.

### 3.2 — B1: السبب الجذري
«الاكتمال» heuristic نصي بلا إشارة — هو **الافتراضي** لأي نص طويل. الفحص الوحيد الذي يميّز «ما زال يعمل» (مؤشر P18 — Deep Thinking / Tasks Remaining عبر `fetch_project_activity_signature`) موجود في نفس الحلقة لكنه لا يُستخدم كبوابة لقرار الاكتمال.

### 3.3 — لماذا صائد `ACTION_CREDIT_EXHAUSTED` سليم؟
لأن نفاد الرصيد **إشارة مهيكلة (Structured)** لا تخمين نصي: المحرك `01.03` يلتقط `ACTION_CREDIT_EXHAUSTED` كـ event رسمي من الـ API داخل الـ SSE stream ويحوّله إلى marker مميز، والجسر عنده كلمات مفتاحية مميزة تُلتقط من ذيل النص. **الرصيد يتكشف بدليل، والاكتمال يتكشف بالظن** — هذا جوهر B1، وهو أيضاً سبب اختيار إشارة P18 المهيكلة من المنصة كأساس الحل (لا heuristic نصي جديد).

### 3.4 — B2: مسار التجميد (BEFORE)
1. بدء المهمة: `apply_project_runtime_binding(cfg, project_key)` يقرأ الـ manifest ويصوّر البرومبت على `bridge_cfg.project_resume_prompt_runtime` (**Snapshot₀**).
2. المستخدم يعدّل أثناء التشغيل: `set_project_resume_prompt(...)` يكتب في الـ manifest بنجاح ✅ (لذا يظهر التعديل في الملف وفي كارت البوت).
3. نفاد رصيد داخل نفس الجلسة: `active_query = get_bridge_cfg_runtime_resume_prompt(bridge_cfg)` — يقرأ **من صورة الذاكرة القديمة (Snapshot₀)**، ولا يوجد أي كود يعيد قراءة الـ manifest أثناء الجلسة ❌.
4. مهمة جديدة بعد الإنهاء/الإلغاء: الربط يُعاد من الصفر → النسخة الجديدة تُلتقط ✅ — وهذا يفسر الظاهرة الموصوفة بالضبط.

**الخلاصة:** الحفظ سليم ✅ + العرض سليم ✅ + **القراءة لحظة الاستئناف هي المقفولة** ❌.

---

## 🏗️ 4. القرارات المعمارية (D1–D12)

### B2 — Live Resume Prompt Rebind (يُنفذ أولاً — الأصغر والأكثر أماناً)

| الكود | القرار |
|---|---|
| **D1 — Live Rebind** | داخل فرع `CREDIT_EXHAUSTED`، قبل بناء `active_query`، يُعاد استدعاء `apply_project_runtime_binding(bridge_cfg, ...)` **بتوقيعه القائم** داخل `try/except` → `bridge_cfg` يتحدث بآخر برومبت/إعدادات محفوظة في الـ manifest. نجاح = `LIVE_REBIND_OK`. |
| **D2 — Fail-Open Fallback** | لو إعادة الربط فشلت (ملف/JSON/قفل/أي استثناء) → يُكمل بالصورة القديمة + `LIVE_REBIND_FALLBACK` — **صفر كسر** للسلوك الحالي. |
| **D3 — استثناء P20** | عقد P20 الموثق (DATA_RETENTION) = «إعادة إرسال نفس آخر رسالة كما هي» → فرع DATA_RETENTION **مستثنى تماماً** من إعادة الربط (`LIVE_REBIND_SKIPPED_P20`). الربط الحي لفرع CREDIT_EXHAUSTED حصرياً. |
| **D4 — Display Parity** | كروت العرض («برومبت الاستئناف التالي/المرشح») تسحب القيمة الحية بعد الـ rebind خلف `self.lock` **القائم** (بلا أقفال جديدة) — «اللي يظهر = اللي يتبعت». |

### B1 — Final Reply Discrimination

| الكود | القرار |
|---|---|
| **D5 — Activity Gate** | طول ما مؤشر النشاط P18 (`fetch_project_activity_signature`) يرجع `active=True` → الحالة **تُجبَر RUNNING مهما طال النص** (`ACTIVITY_GATE_HOLD`). |
| **D6 — Debounce قراءتين + حياد None** | إعلان الاكتمال عبر البوابة يتطلب **قراءتين متتاليتين** بـ `active=False`. فشل الشبكة (`activity=None`) لا يُحتسب قراءة — البوابة **محايدة** عنده (Fail-Open = سلوك اليوم كما هو). |
| **D7 — Final Fetch** | بعد خروج الحلقة بأي سبب اكتمال (خصوصاً وقف P18) → **جلبة نهائية واحدة** لـ `fetch_project_messages` وأخذ آخر رسالة assistant حقيقية كـ `last_resp_text` النهائي (`FINAL_FETCH_OK` / فشلها = `FINAL_FETCH_FALLBACK` بالنص القديم). |
| **D8 — Stability Check** | الرد يعتبر نهائياً فقط لو نفس آخر رسالة assistant **ثبت محتواها بين قراءتين** (بصمة `len + hash` خفيفة) — الرسالة المتغيرة = RUNNING (`REPLY_UNSTABLE_HOLD`). |
| **D9 — Wrapper لا تعديل** | دالة جديدة `detect_response_status_gated(...)` **تغلّف** `detect_response_status` القائمة بلا لمس جسمها. الإشارات المهيكلة (CREDIT_EXHAUSTED / DATA_RETENTION / SESSION_EXPIRED / FORBIDDEN) **تخترق البوابة فوراً دائماً** — البوابة تمنع فقط COMPLETED المبكر. «التغليف مسموح، التعديل محظور». |
| **D10 — دلالات P18 محفوظة حرفياً** | قاعدة «المهام تغيّرت = وقف فوري، لا تكملة» (قرار مالك موثق في الكود — `should_stop_on_activity_change`) **تبقى كما هي** — P44 يصلح فقط أن الوقف كان يأخذ رسالة وسطية كرد نهائي (يُحل بـ D7). |
| **D11 — Telemetry الثمانية** | بنمط P43: `ACTIVITY_GATE_HOLD` / `ACTIVITY_GATE_RELEASE` / `REPLY_UNSTABLE_HOLD` / `FINAL_FETCH_OK` / `FINAL_FETCH_FALLBACK` / `LIVE_REBIND_OK` / `LIVE_REBIND_FALLBACK` / `LIVE_REBIND_SKIPPED_P20`. |
| **D12 — سقف session_timeout** | البوابة لا تتجاوز `session_timeout` القائم — لو المؤشر ظل active حتى المهلة، سلوك الـ timeout الحالي يبقى كما هو (شبكة أمان محفوظة). |

---

## 🚫 5. المرفوضات (R1–R5) والبدائل المرفوضة (X1–X3)

| الكود | المرفوض | السبب |
|---|---|---|
| **R1** | حقن sentinel `<final_reply>` (أو أي تعليمات) في برومبت المستخدم المُرسل لوكيل Genspark | يلوّث سياق المشاريع المولَّدة نفسها (البرومبت يبني webapps حقيقية)، غير مضمون الطاعة، ويكسر عقد «البرومبت ملك المستخدم». إشارة P18 المهيكلة من المنصة أقوى من أي heuristic نصي — نفس فلسفة نجاح صائد الرصيد. |
| **R2** | أي تعديل في المحرك `01.03` | خارج نطاق هذه الـ Phase — المحرك READ-ONLY (وكذلك Golden Baselines). |
| **R3** | تعديل `is_model_decline_response` (P35) أو Decline Fast-Path (P40) | Zero-Regression قاطع — التكامل معهما بالترتيب الحاكم فقط. |
| **R4** | تعديل جسم `detect_response_status` نفسها | 962 اختباراً معتمدة على سلوكها — التغليف (D9) بدل الجراحة. |
| **R5** | Pub/Sub أو in-memory cache invalidation بين الـ callback والجلسة الشغالة | يكسر idempotency + معقّد في Single-File — الـ Live Rebind عند نقطة الاستهلاك أبسط وأصح. |
| **X1** | Sentinel + heuristic fallback (`extract_final_reply` — اقتراح مسودات 18.02) | نفس علة R1 + يضيف heuristic نصياً جديداً بينما نحن أصلاً نستبدل heuristic نصياً بإشارة مهيكلة. |
| **X2** | File lock جديد محمول (`fcntl`/`msvcrt`) لقراءة الـ manifest | غير مطلوب — إعادة الربط تحدث عند حدث نادر (نفاد رصيد) خلف القفل القائم، وكتابات الـ manifest أصلاً بنمط المشروع القائم. |
| **X3** | فصل المشكلتين في Phase 44 + Phase 45 | قرار المالك النهائي: Phase واحدة — الاثنتان تمسّان نفس الـ resume pipeline، وترتيب CPs يبدأ بالأصغر (B2) لعزل المخاطر. |

**مرفوضات فلتر 0.1 الإضافية (هلوسات المادة الخام 18.02 التي سقطت):**
- أسماء دوال/بنى متخيّلة لا وجود لها في السورس: `session.cached_resume_prompt` / `load_resume_prompt_live` / `extract_final_reply` / `classify_terminal_response` / `RunSnapshot` schema / `settings_revision` — الوثيقة الحالية مبنية حصرياً على الأسماء الحقيقية (`apply_project_runtime_binding` / `get_bridge_cfg_runtime_resume_prompt` / `detect_response_status` / `fetch_project_activity_signature` / `should_stop_on_activity_change` / `set_project_resume_prompt` / `fetch_project_messages`).
- ادعاء «fork PID لا يُسجل في `pid_to_key`» — سقط بالفحص المضاد داخل 18.02 نفسها (`upsert_project_identity` يسجّل الـ alias)، وعلى أي حال خارج نطاق P44.
- مسودة «Message Lifecycle / RunSnapshot / snapshot lock protocol» الموسعة (CP0–CP9 بديلة داخل 18.02) — بنية جديدة كاملة تخالف مبدأ «صفر بنية جديدة — كله مبني على دوال قائمة».

---

## ⚙️ 6. Pseudo-Diffs الثلاثة (الأسطر النهائية تُثبت بالـ grep في CP1)

### 6.1 — B2: الـ rebind في فرع CREDIT_EXHAUSTED (قبل السطر 2977 — مُثبت CP1)
```python
# داخل فرع CREDIT_EXHAUSTED (يبدأ 2899) — قبل السطر القائم 2977:
#   active_query = get_bridge_cfg_runtime_resume_prompt(bridge_cfg)
# مفتاح المشروع المتاح في السياق: getattr(bridge_cfg, "selection_project_key", "")
# (نفس المفتاح الذي ربط به worker في 6530 — التوقيع القائم من 432 بلا تغيير)
try:
    apply_project_runtime_binding(bridge_cfg, getattr(bridge_cfg, "selection_project_key", "") or None)
    log_event("info", "🔄 [P44] LIVE_REBIND_OK ...", email=curr_email)
except Exception as _rb_err:
    log_event("warning", f"🔄 [P44] LIVE_REBIND_FALLBACK reason={_rb_err}", email=curr_email)
active_query = get_bridge_cfg_runtime_resume_prompt(bridge_cfg)   # السطر 2977 القائم — لا يتغير
# فرع DATA_RETENTION (2808–2822): لا rebind إطلاقاً — الفرع يعمل continue بنفس آخر رسالة
# ولا يمر على 2977 أصلاً — LIVE_REBIND_SKIPPED_P20 (عقد «نفس آخر رسالة»)
```

### 6.2 — B1: البوابة داخل حلقة المتابعة (تغليف — D9 — نقطة الحقن: السطر 2611 — مُثبت CP1)
```python
# curr_activity متاحة من فحص P18 في نفس الدورة (السطر 2582) — صفر طلبات شبكة إضافية
raw_status = detect_response_status(last_c)          # الجسم القائم بلا لمس (def 1765 — استدعاء 2611)
final_status = detect_response_status_gated(
    raw_status, curr_activity, inactive_streak, stable_streak)
# داخل الـ wrapper:
#   raw_status مهيكلة (CREDIT_EXHAUSTED/DATA_RETENTION/SESSION_EXPIRED/FORBIDDEN)
#       → تمر فوراً (تخترق البوابة)
#   raw_status == COMPLETED and activity.active      → RUNNING (ACTIVITY_GATE_HOLD)
#   raw_status == COMPLETED and inactive_streak < 2  → RUNNING (D6 debounce)
#   raw_status == COMPLETED and stable_streak  < 2   → RUNNING (D8 استقرار)
#   activity is None → البوابة محايدة (Fail-Open — سلوك اليوم حرفياً)
#   سقف session_timeout القائم فوق كل ذلك (D12)
```

### 6.3 — B1: الجلبة النهائية بعد خروج الحلقة (D7 — نقطة الحقن: بعد خروج while 2562، قبل بلوك is_timeout 2615 — يغطي خصوصاً وقف P18 في 2591 — مُثبت CP1)
```python
if final_status == "COMPLETED":
    try:
        _final_msgs = <fetch_project_messages بالاستدعاء القائم>
        _fin = next((m for m in reversed(_final_msgs or [])
                     if isinstance(m, dict) and m.get("role") == "assistant"), None)
        if _fin and _fin.get("content"):
            last_resp_text = _fin["content"]        # FINAL_FETCH_OK
    except Exception:
        pass                                        # FINAL_FETCH_FALLBACK — النص القديم يبقى
```

---

## 🧪 7. مصفوفة الاختبارات الـ 12 — `tests/test_p44_resume_pipeline_integrity.py`
(Mocks/Spies بلا شبكة حقيقية)

| # | الاسم الحرفي | يثبت |
|---|---|---|
| 01 | `test_01_gate_holds_running_while_active` | نص > 25 حرفاً + active → RUNNING |
| 02 | `test_02_gate_releases_after_two_inactive_reads` | قراءة واحدة لا تكفي — الثانية تفتح |
| 03 | `test_03_structured_signals_pierce_gate` | CREDIT_EXHAUSTED يخترق فوراً رغم active |
| 04 | `test_04_gate_neutral_on_network_none` | None → سلوك اليوم (Fail-Open) |
| 05 | `test_05_unstable_reply_holds` | محتوى متغير بين قراءتين → RUNNING |
| 06 | `test_06_final_fetch_after_p18_stop` | وقف P18 → الرسالة الختامية لا الوسطية |
| 07 | `test_07_final_fetch_failure_keeps_old_text` | فشل الجلبة → النص القديم + telemetry |
| 08 | `test_08_live_rebind_picks_edited_prompt` | تعديل وسط الجلسة → أول استئناف بالجديد |
| 09 | `test_09_rebind_failure_falls_back_to_snapshot` | manifest تالف → الصورة القديمة بلا كسر |
| 10 | `test_10_p20_data_retention_no_rebind` | DATA_RETENTION بلا rebind (عقد P20) |
| 11 | `test_11_display_cards_match_sent_prompt` | الكارت = القيمة المرسلة فعلاً |
| 12 | `test_12_zero_regression_p35_p40_p18` | P35/P40/P18 بلا أي تغيير سلوكي |

---

## 📋 8. خطة الـ Checkpoints (CP0 ➔ CP9 — لكل CP: دليل Terminal ➔ Checkbox ➔ Commit مستقل)

- [x] **CP0 — SPEC EXTRACTION & ADOPTION** (إداري — صفر كود — ينتهي بـ Gate-A):
  قراءة 18.02 كاملة بفلتر الحسم + إنشاء هذه الوثيقة + تحديث الحوكمة (البند 1 + البند 7 + بلوك ## 0 + PROGRESS ×2 + SESSION_LOG DEC-040) في commit واحد.
  Commit: `P44-CP0: spec adopted — 18_COT_CLEANUP_AND_DYNAMIC_RESUME_PROMPT.MD (DEC-040)` ✅ S72
- [x] **CP1 — FORENSICS:** grep -n وتثبيت المراسي الفعلية F1–F10 في 01.33 (8422 سطراً) — الجدول §8.1 مملوء بأرقام Terminal الفعلية + الـ pseudo-diffs الثلاثة مُرسّاة على الأسطر (rebind قبل 2977 / gate عند 2611 / final fetch بعد خروج 2562 قبل 2615). Baseline المُثبت: 962/962 (+12 subtests) + Exit 0 + Parity 11/11.
  Commit: `P44-CP1: forensics + baseline` ✅ S73
- [x] **CP2 — B2 LIVE REBIND (D1+D2+D3):** الـ rebind محقون داخل فرع CREDIT_EXHAUSTED قبل `active_query =` (الملف الآن 8452 سطراً) داخل try/except بالتوقيع القائم (def 432 — نفس نمط الاستدعاء المرجعي في مسار المحرك): نجاح = `LIVE_REBIND_OK` (سطر 2998) / فشل = `LIVE_REBIND_FALLBACK` بالصورة القديمة Snapshot₀ بصفر كسر (سطر 3004). استثناء P20 صريح في فرع DATA_RETENTION: `LIVE_REBIND_SKIPPED_P20` (سطر 2826) — الفرع يعمل continue ولا يمر على بناء active_query (عقد «نفس آخر رسالة» محفوظ). الإثبات السلوكي (Terminal): تعديل الـ manifest أثناء الجلسة → القراءة قبل الـ rebind مجمدة على القديم + بعد الـ rebind تقرأ الجديد ✅. البوابات: 962/962 (+12 subtests) + hadith Exit 0 + Parity خضراء.
  Commit: `P44-CP2: live resume prompt rebind` ✅ S74
- [x] **CP3 — B2 DISPLAY PARITY (D4):** الـ Live Rebind نُقل ليسبق إشعار `continuation-handoff-ready` (الآن: rebind → LIVE_REBIND_OK سطر 2978 / FALLBACK 2984 → notify 2989 → active_query 3013) — كارت الـ handoff (القراءة الحية `continuation_prompt_public` داخل notify_account_selection_observer سطر 861) يقرأ القيمة ذاتها التي ستُبنى منها active_query — «اللي يظهر = اللي يتبعت». القفل: قراءة الـ manifest تتم في `get_project_settings` خلف `with self.lock` القائم (سطر 3286–3287) — صفر أقفال جديدة. فرع P20 سليم (SKIPPED_P20 سطر 2826 بلا تغيير). الملف الآن 8458 سطراً + حدود PARTS مُزاحة +6 (p06 → 3051 / p12 → 8458). البوابات: 962/962 (+12 subtests) + hadith Exit 0 + Parity 11/11.
  Commit: `P44-CP3: display cards parity` ✅ S75
- [x] **CP4 — B1 ACTIVITY GATE (D5+D6+D9+D12):** دالة `detect_response_status_gated` (def سطر 1819) تغلّف `detect_response_status` القائمة بلا لمس جسمها (def 1765 كما هو حرفياً — R4/D9). الثوابت: `P44_STRUCTURED_STATUSES` (1812) + `P44_GATE_INACTIVE_READS_REQUIRED=2` (1815) + `P44_GATE_STABLE_READS_REQUIRED=2` (1817 — hook جاهز لـ D8/CP5). الحقن في الحلقة: عدّاد `inactive_streak` يبدأ صفراً قبل while (2619) ويتحدث من قراءة P18 القائمة نفسها — صفر طلبات شبكة إضافية (2654: active يصفّره / inactive يزيده / None لا يلمسه — حياد Fail-Open) + نقطة القرار `raw_status = detect_response_status(last_c)` ثم `final_status = detect_response_status_gated(raw_status, curr_activity, inactive_streak, None)` (2676–2678). السلوك المُثبت بدخاني 9/9 Terminal: COMPLETED+active → RUNNING (D5) / inactive_streak=1 → RUNNING، =2 → COMPLETED (D6) / المهيكلة الأربع تخترق فوراً رغم active / None → COMPLETED كسلوك اليوم / RUNNING+EMPTY تمر كما هي / stable_streak hook: 1 يمسك و2 يفتح وNone محايد. D12: فحص elapsed>session_timeout القائم (2622–2625) قبل البوابة بلا أي تغيير. الملف 8525 سطراً + حدود PARTS مُزاحة (p05→2047 / p06 2048→3118 / p12→8525). البوابات: 962/962 (+12 subtests) + Parity خضراء.
  Commit: `P44-CP4: activity-gated completion` ✅ S76
- [x] **CP5 — B1 STABILITY + FINAL FETCH (D7+D8):** `compute_reply_fingerprint` (def سطر 1861 — len + sha256 على UTF-8/replace: رخيصة ومحلية بالكامل، تكشف تغيّر المحتوى حتى مع ثبات الطول) + `fetch_final_reply_text` (def سطر 1871 — آخر رسالة assistant حقيقية بطلب واحد أخير: `FINAL_FETCH_OK` سطر 1890 / أي فشل شبكة/لا رسائل/محتوى فارغ → `FINAL_FETCH_FALLBACK` سطر 1894 بالنص القديم كما هو — Fail-Open). التوصيل في الحلقة: init `prev_reply_fp=None / stable_streak=0` (2659–2660) + التحديث من نفس قراءة الرسائل القائمة — تطابُق يزيد العداد وأي تغيّر يعيده لـ 1 (2721–2723) + تمرير `stable_streak` الحي للبوابة بدل None (2730–2731 — hook CP4 اكتمل: قيمة <2 = `REPLY_UNSTABLE_HOLD` سطر 1855 → RUNNING). الجلبة النهائية بعد خروج الحلقة بأي سبب خصوصاً وقف P18 (الذي يكسر قبل قراءة الرسائل): علم `polled_any` يُحسم قبل الحلقة من نفس شرطها (2665–2666 — بلا لمس أول سطر فيها: عقد P25 فحص الإلغاء أولاً) + الاستدعاء `if polled_any and final_status == "COMPLETED"` (2750–2751 — الرد المكتمل مباشرة من البث لا يحتاج جلبة: صفر شبكة إضافية). دخاني 8/8 Terminal: بصمتان متطابقتان / نفس الطول بمحتوى مختلف يُكشف / None-safe / بوابة 1→HOLD و2→فتح وNone محايد / OK يعتمد آخر assistant / فشل شبكة + محتوى فارغ + محرك بلا fetch → Fallback بالقديم. الملف 8585 سطراً + حدود PARTS مُزاحة (p05→2084 / p06 2085→3178 / p12→8585). البوابات: 962/962 (+12 subtests) + hadith Exit 0 + Parity 11/11.
  Commit: `P44-CP5: reply stability + final fetch` ✅ S77
- [x] **CP6 — TELEMETRY (D11):** الأسطر الثمانية كلها قائمة بنمط P43 (زُرعت تباعاً في CP2–CP5 — قاعدة «موجود → وثّق فقط»: صفر كود جديد في هذا الـ CP) وأُثبت ظهورها فعلياً في Terminal واحداً واحداً: `ACTIVITY_GATE_HOLD reason=indicator-active` (سطر 1849) + `ACTIVITY_GATE_HOLD reason=debounce` (1852) + `REPLY_UNSTABLE_HOLD` (1855) + `ACTIVITY_GATE_RELEASE` (1857) — الأربعة عبر استدعاء `detect_response_status_gated` المباشر بالحالات الأربع + `FINAL_FETCH_OK` (1890) + `FINAL_FETCH_FALLBACK` (1894) — عبر `fetch_final_reply_text` بمحرك ناجح/فاشل + `LIVE_REBIND_OK` (3105) + `LIVE_REBIND_FALLBACK` (3111) — بتنفيذ المقطع الحرفي 3097–3113 من الملف نفسه (compile بأرقام أسطره) مع apply ناجح/رامٍ استثناء + `LIVE_REBIND_SKIPPED_P20` (2953) — بتنفيذ المقطع الحرفي 2951–2955 من فرع DATA_RETENTION. كل سطر خرج بمستواه الصحيح (INFO للمسارات السوية / WARNING للـ FALLBACKs).
  Commit: `P44-CP6: telemetry branches` ✅ S77
- [x] **CP7 — الاختبارات الـ 12 (§7):** `tests/test_p44_resume_pipeline_integrity.py` (373 سطراً — الأسماء الحرفية من §E: test_01 سطر 103 → test_12 سطر 331) — **12/12 PASS** (Terminal: `12 passed`) بنمط Mocks/Spies بلا شبكة حقيقية + عزل Registry في مجلد مؤقت (نمط P43). المنهج: الاختبارات 08/09/10/11 تنفّذ **المقاطع الحرفية من كود الإنتاج نفسه** (استخراج سطري بالمراسي النصية LIVE_REBIND_FALLBACK/SKIPPED_P20 — مقاوم لإزاحة الأسطر) عبر compile بمسار الملف — لا نسخاً محاكية. صفر لمس لـ 01.33 (8585 سطراً كما هو) → حدود PARTS لم تحتج تحديثاً + Parity **11/11** ✅ + pytest الكامل **974 PASS (+12 subtests)**.
  Commit: `P44-CP7: 12 tests green` ✅ S78
- [x] **CP8 — QUALITY GATES:** pytest **974/974 PASS (+12 subtests)** بلا أي Skip (تشغيل بـ `-rs` — صفر أسطر skip) + hadith_sijil **Exit 0** (Syntax OK + P10 Docs Integrity: 34 files + 974 فحص) + rebuild_refactor Exit 0 + Parity **11/11** (test_refactor_parity) + Zero-Regression مُثبت: 158 اختباراً بمفاتيح p35/p40/p18/decline/activity كلها PASS + `01.33` = 8585 سطراً بلا لمس منذ CP5 + شجرة نظيفة (المصنوعات .pytest_cache/bridge_bot.log أُخرجت من التتبع — المرة 45 بعد إعادة المزامنة لها).
  Commit: `P44-CP8: gates green` ✅ S78
- [x] **CP9 — CLOSE:** توثيق كامل مُنفَّذ (PROGRESS ×2 + SESSION_LOG سطر DEC-040 الختامي + هذه الوثيقة كل Checkboxes محسومة CP0–CP9 + V3_RESUME (974 + قاعدة P44 الدائمة) + TEST_SUITE_CATALOG (صف P44: 38 ملفاً/974) + README (Milestone P44 + 974)) + البند 7 وبلوك ## 0 ➔ «BLOCKED-ON-OWNER بانتظار مهمة جديدة» + أرشفة P44 بنمط 7.7-ج — كله في نفس الـ Commit + التقرير النهائي بالعناوين الـ 12 حرفياً.
  Commit: `P44-CP9: close — Resume Pipeline Integrity shipped (DEC-040)` ✅ S78

### 8.1 جدول المراسي الجنائية (يُملأ بأرقام الأسطر الفعلية في CP1)

| # | المرساة | السطر الفعلي (CP1) | الدور | القضية |
|---|---|---|---|---|
| F1 | `detect_response_status` | def **1765** — استدعاءان **2555** (الرد الأول) + **2611** (داخل الحلقة) | التصنيف النصي — «أي نص ≥ 25 حرفاً بلا marker = COMPLETED» (العتبة سطر 1798) | B1 |
| F2 | حلقة المتابعة — آخر رسالة assistant | `while` **2562** — بلوك fetch_project_messages **2596–2612** (last_asst 2602 → detect 2611) | تصنف الرسالة الوسيطة COMPLETED | B1 |
| F3 | فرع وقف P18 (`final_status="COMPLETED"; break`) | **2591–2592** (+ شبكة أمان timeout **2620**) | بلا fetch أخير — نقطة حقن Final Fetch (D7) | B1 |
| F4 | `fetch_project_activity_signature` / `should_stop_on_activity_change` | def **1880** / def **1905** — baseline **2560** + داخل الحلقة **2582/2584** | بنية P18 القائمة — curr_activity متاحة في نفس الدورة (أساس البوابة بصفر طلبات إضافية) | B1 |
| F5 | `apply_project_runtime_binding` | def **432–449** (التوقيع: bridge_cfg, project_key, *, requested_model, registry) — ربط worker الأولي **6530** + مسار المحرك **2686** | تصوير البرومبت على bridge_cfg (Snapshot₀) | B2 |
| F6 | `get_bridge_cfg_runtime_resume_prompt` | def **427** — القراءة المقفولة **2977** | القراءة من الصورة المجمّدة | B2 |
| F7 | فرع CREDIT_EXHAUSTED — بناء active_query | الفرع **2899** → `active_query =` **2977** (نقطة الحقن: قبل 2977 مباشرة) | نقطة الحقن الوحيدة للـ rebind — فرع DATA_RETENTION المستثنى **2808–2822** (continue بنفس الرسالة — لا يمر على 2977) | B2 |
| F8 | `set_project_resume_prompt` | def **3317** + `build_effective_resume_prompt` **3320** — الكتابة من UI **5790** و **8076** | كتابة الـ manifest — سليمة، لا تُلمس | B2 |
| F9 | كروت العرض + الربط الأولي في worker | `summarize_resume_prompt_for_display` def **377** / `get_bridge_cfg_public_resume_prompt` def **422** — الكروت: **861 / 1425 / 1504 / 2978 / 6559 / 6631** | تقرأ من نفس الـ snapshot — مواضع Display Parity (D4) | B2 |
| F10 | `is_model_decline_response` (P35) + Decline Fast-Path (P40) | def **1828** — `_declined` **2633** + worker **6697** | تكامل الترتيب الحاكم — مجمّدة | B1 |

⚠️ أي أرقام أسطر وردت في المادة الخام 18.02 **استرشادية فقط** — لا تُعتمد إلا بعد grep -n في CP1. أي تعارض بين 18.02 والسورس الفعلي → **السورس يفوز**؛ لو الخلاف معماري → STOP + BLOCKED-ON-OWNER.

---

## ⚖️ 9. المحظورات + بوابات القبول + سيناريوهات القبول

### 9.1 المحظورات العشرة (مخالفة بند واحد = فشل المرحلة كاملة)
1. ممنوع أي كود قبل حسم CP0 وعبور Gate-A.
2. ممنوع لمس المحرك `01.03` أو Golden Baselines (`01.30`/`01.29`/`01.28`/`01.27`/`01.26`).
3. ممنوع تعديل جسم `detect_response_status` / P35 / P40 / دلالات P18 (تغليف فقط — D9/D10).
4. ممنوع تفتيت `01.33` (الاستثناء الوحيد: ملف الاختبارات الجديد).
5. ممنوع حقن sentinel/تعليمات في برومبت المستخدم المُرسل لـ Genspark (R1).
6. ممنوع dependency جديد — stdlib فقط.
7. ممنوع Refactor خارج الـ CP الجاري.
8. ممنوع «تم» قبل عبور كل البوابات بمخرجات حقيقية.
9. كل رقم سطر بـ grep -n في هذه النسخة.
10. ممنوع Mutation بلا فحص وتوثيق سبب (Zero Blind Mutation) — والغموض المعماري = STOP + BLOCKED-ON-OWNER بسؤال محدد، لا اجتهاد.

### 9.2 بوابات القبول الثماني
| # | البوابة | معيار النجاح |
|---|---|---|
| 1 | pytest | 100% PASS (962 baseline + 12 P44، بلا Skip جديد) |
| 2 | hadith_sijil.py | Exit Code 0 |
| 3 | Parity | 11/11 |
| 4 | Zero-Regression | P35 + P40 + P18 + المسارات المجمّدة بلا أي تغيير سلوكي |
| 5 | Behavior-B1 | رد وسطي > 25 حرفاً + active لا يُنهي الحلقة أبداً |
| 6 | Behavior-B2 | تعديل وسط الجلسة يظهر في أول استئناف + الكارت مطابق |
| 7 | Telemetry | الأسطر الثمانية تظهر فعلياً في فروعها |
| 8 | Git + Docs | Commit نهائي + كل الوثائق محدثة + Checkboxes محسومة |

### 9.3 سيناريوهات القبول الستة
1. سرد خطوات طويل + active → البوت صامت حتى قراءتين inactive + ثبات → الرد الختامي الحقيقي.
2. وقف P18 → الجلبة النهائية تجيب آخر رسالة فعلية — لا رد وسطي.
3. تعديل البرومبت ثم نفاد رصيد → الاستئناف بالجديد + الكارت مطابق (`LIVE_REBIND_OK`).
4. manifest تالف → fallback بلا كسر (`LIVE_REBIND_FALLBACK`).
5. نفاد رصيد + active → الاختراق فوري صفر تأخير للتبديل.
6. خطأ Data Retention → نفس آخر رسالة بلا rebind (عقد P20 محفوظ).

---

## 📛 10. توحيد الاسم وإعلان الـ SSOT

### 10.1 جدول التناقضات المحسومة في CP0 (بالدليل)
| الموضع | الحالة القديمة | التصحيح المُطبق |
|---|---|---|
| `Deep_Thinking_Tasks_Remaining.TXT` (البند 1) | «883/883» و«~7950 سطر» | **962/962 (+12 subtests)** و**~8422 سطراً** (من Terminal §B الفعلي S72) |
| `00_MASTER_RESUME_PROTOCOL.md` (## 0) | BLOCKED-ON-OWNER / P43 | **PHASE 44 + DEC-040 + SPEC_DOC: 18** |
| داخل 18.02 (~سطر 4543 وغيرها) | يشير لـ «18_RESUME_PIPELINE_INTEGRITY.MD» (وأيضاً «18_MESSAGE_LIFECYCLE_LIVE_RESUME_PROTOCOL.MD» في مسودات أخرى) | الاسم الرسمي الموحد **الوحيد**: **`18_COT_CLEANUP_AND_DYNAMIC_RESUME_PROMPT.MD`** — أي إشارة لأسماء أخرى في المادة الخام تُقرأ كإشارة لهذه الوثيقة |

### 10.2 إعلان
**هذه الوثيقة هي الـ SSOT الوحيد للمرحلة** — `18.02_COT_CLEANUP_AND_DYNAMIC_RESUME_PROMPT.MD` **أرشيف تحليلي مرجعي فقط** (مادة خام فيها تحليلات متعارضة ومسودات متعددة الأسماء — لا تُنفَّذ ولا يُستشهد بها كمرجع تنفيذي)، و`18.03_COT_CLEANUP_AND_DYNAMIC_RESUME_PROMPT.MD` هو برومبت التوجيه التشغيلي (Router/Gates) لجلسات المرحلة.
