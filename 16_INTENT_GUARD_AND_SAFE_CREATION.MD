# 16 — INTENT GUARD & SAFE PROJECT CREATION FLOW (Phase 42)

> **وثيقة المواصفات الرسمية — S67 / DEC-038**
> بروتوكول المالك: `Deep_Thinking_Tasks_Remaining.TXT` — البند 7 (PHASE 42).
> القاعدة الحاكمة: INSPECT FIRST + **Confirmation before ANY Mutation** —
> هذه الوثيقة كُتبت **قبل** أي تعديل كود.

---

## 🔄 Deep Thinking Tasks — القائمة الحية (تُحدَّث مع كل خطوة)

- [x] **Checkpoint 0:** قراءة ملفات التوجيه + إثبات Baseline
      (883/883 PASS + `hadith_sijil.py` Exit 0 — بعد نظافة git المرة 40:
      إخراج `.pytest_cache/` + `bridge_bot.log` اللذين أعادتهما المزامنة) —
      commits `6bae036` + `2f37670`.
- [x] **Checkpoint 1:** INSPECT جنائي لـ `handle_telegram_update` (مسار message)
      + توثيق نقطة الـ Fallback والحدود الخمسة بأرقام الأسطر (القسمان 1–2).
- [x] **Checkpoint 2:** كتابة FIX DESIGN كاملاً في هذه الوثيقة
      (شامل الـ Edge Cases التسعة — الأقسام 3–4) قبل أي تنفيذ.
- [x] **Checkpoint 3A:** حذف الـ Fallback + تركيب الـ Intent Guard +
      حالة `AWAITING_PROJECT_CONFIRMATION` ✅ S68: الـ Fallback استُبدل
      حرفياً باستدعاء `handle_idle_intent_guard` (سطر 8123–8125) —
      كتلة P42 كاملة أسطر 6702–6815 (الثوابت §3.9 + الدوال §3.10) +
      فرع الحالة في سلسلة النص (أسطر 7742–7763 — Edge 6: P41 يفوز).
- [x] **Checkpoint 3B:** بطاقة التأكيد + Callbacks (nonce + idempotency) +
      Smart Prompt Forwarding للـ Wizard القائم ✅ S68: معالج `pconf:yes/no:<nonce>`
      كتلة معزولة مبكرة بنمط P25/P26 (أسطر 6977–7035: CONFIRMED/DUPLICATE/
      EXPIRED/CANCELLED) + نقل `pending_prompt`/`consumed_confirm_nonce` في
      `AWAITING_NEW_PROJECT_NAME` (أسطر 7765–7777) + `forward_pending_prompt_after_wizard`
      في موضعي `finalize_new_project_from_state` (سطرا 7195 و 7856).
- [x] **Checkpoint 4:** اختبارات P42 + Parity 11/11 + pytest 100% +
      hadith_sijil Exit 0.
- [x] **Checkpoint 5:** تحديث الوثائق (DEC-038) + تحديث البند 7 + Commit +
      التقرير النهائي.

---

## 1. CAUSE — الفحص الجنائي لنقطة الـ Fallback (Checkpoint 1)

### 1.1 EVIDENCE — السلوك الحي المُبلَّغ (حالات المالك)

إرسال أي نص عابر في وضع الخمول (IDLE — `user_state = {}`):

| النص المُرسَل | ما يحدث فعلياً (قبل P42) |
|---|---|
| `2+7=` | مشروع `prj_*` جديد + حجز حساب + توليد Genspark كامل |
| `63636` | نفس الشيء — مشروع شبحي جديد في `project_registry/` |
| `121` | نفس الشيء — هدر رصيد ودقائق على نص بلا معنى |
| صورة/ستيكر بلا نص | `text = ""` ➔ **نفس المسار** بنص فارغ (لا يوجد حارس `if not text`) |

### 1.2 نقطة الـ Fallback القاتلة — `01.33_telegram_gen_bridge.py`

**الأسطر 7917–7921** (آخر كتلة في فرع `"message"` داخل `handle_telegram_update`):

```python
7917        set_user_state(chat_id, {})
7918        try:
7919            EXECUTOR.submit(process_user_task_async, chat_id, None, text)
7920        except Exception as e:
7921            log_event("error", f"فشل جدولة المهمة: {e}")
```

- بلا أي `project_key_hint` / `project_name_hint` / `model` ➔ داخل
  `process_user_task_async` يُولَّد مفتاح مشروع جديد حتماً.
- بلا أي شرط على محتوى `text` — حتى النص الفارغ يمر.
- الفلسفة المعطوبة: "أي نص غير مفهوم في IDLE = مشروع جديد".

### 1.3 CALL PATH الكامل الحالي (من IDLE حتى التوليد)

```
run_telegram_polling (سطر ~7975)
  └─ EXECUTOR.submit(handle_telegram_update, update)
       └─ handle_telegram_update (سطر 6735) ➔ فرع "message" (سطر 7490)
            ├─ 7493: text = msg.get("text","").strip()
            ├─ 7495: بوابة is_chat_allowed (P17)
            ├─ 7501–7533: Document Ingestion (P28) — .txt/.md ➔ text
            ├─ 7534: /start و /help
            ├─ 7538–7540: state = get_user_state(chat_id); action = state.get("action")
            ├─ 7545: كتلة P32 (AWAITING_ACCOUNT_PASSWORD_LOOKUP)
            ├─ 7565–7906: سلسلة حالات الـ Wizard (AWAITING_* — 17 حالة)
            │    ├─ 7879: AWAITING_NEW_PROMPT ➔ EXECUTOR.submit (سطر 7887) — بسياق مشروع شرعي ✅
            │    └─ 7892: AWAITING_CONT_PROMPT ➔ EXECUTOR.submit (سطر 7901) — بسياق مشروع شرعي ✅
            ├─ 7907–7916: توجيه روابط المشاريع (P41 — parse_project_locator/resolve_resume_context) ✅
            └─ 7917–7921: ⚠️ الـ FALLBACK القاتل — أي نص متبقٍّ ➔ مشروع جديد بلا تأكيد ❌
```

### 1.4 الحدود الأمنية الخمسة داخل `process_user_task_async` (سطر 6332)

البند 7.2 يسمّي الحدود بأسماء مفاهيمية (`create_project()` /
`register_project()` / `generate_project_key()` / `claim_account()` /
`start_generation()`) — **لا توجد دوال بهذه الأسماء حرفياً**؛ الخريطة
الفعلية بأرقام الأسطر:

| # | الحد المفاهيمي | التطبيق الفعلي في `01.33` | السطر |
|---|---|---|---|
| 1 | `generate_project_key()` | توليد Inline: `project_key = hinted or known or f"prj_{uuid.uuid4().hex[:16]}"` | **6362** |
| 2 | `create_project()` | `claim_project_run(project_key, run_owner_token)` — قفل تشغيل المشروع (def سطر 3973) | **6363** |
| 3 | `register_project()` | `ProjectRegistry(project_key)` — الـ `__init__` (سطر 3016) ينفّذ `self.root.mkdir(...)` ➔ **تلوث السجل يقع هنا فوراً** + `remember_registry_identity` (سطر 6374 ➔ `upsert_project_identity` سطر 4261) يكتب manifest دائم | **6368 + 6374** |
| 4 | `claim_account()` | `send_message_with_auto_account_failover` (استدعاء سطر **6526**، def سطر 2629) ➔ حلقة `claim_eligible_account_for_owner` (سطر 2678، def سطر 560) ➔ `claim_account_selection` (def سطر 529) — **حجز حساب حقيقي من 880** | **6526 ➔ 2678 ➔ 529** |
| 5 | `start_generation()` | داخل `send_message_with_auto_account_failover` نفسها — إرسال البرومبت لمحرك Genspark وبدء التوليد الفعلي (هدر الرصيد) | **6526** |

**الخلاصة الجنائية:** بمجرد وصول `process_user_task_async` بلا
`project_key_hint` تنفجر الحدود الخمسة تسلسلياً بلا أي نقطة توقف —
الحد الوحيد الشرعي هو **منع الوصول أصلاً** من نقطة الـ Fallback (7917).

### 1.5 نقاط الدخول الشرعية لحالة `AWAITING_NEW_PROMPT` (لن تُمَس)

| السطر | المسار |
|---|---|
| 5678 | `finalize_new_project_from_state` — إكمال Wizard المشروع الجديد |
| 7232 | زر `cmd:resume_continue` لمشروع محفوظ بلا رابط استئناف |

ومدخل الـ Wizard الرسمي: زر `cmd:new_proj` (سطر 6897) ➔
`AWAITING_NEW_PROJECT_NAME` (معالجها سطر 7565 — يولّد المفتاح شرعياً بعد
اختيار المالك الصريح).

---

## 2. SCOPE (In / Frozen)

**In-Scope (P42):**
- حذف كتلة الـ Fallback (7917–7921) من الوجود.
- Intent Guard + حالة `AWAITING_PROJECT_CONFIRMATION` + بطاقة التأكيد.
- Smart Prompt Forwarding عبر الـ Wizard القائم.
- اختبارات P42 + تحديث حراس سابقين **فقط إن كسرهم الحذف بوعي موثّق**.

**Frozen (ممنوع اللمس):**
- كل حالات `AWAITING_*` القائمة الـ 17 وسلوكها الحرفي.
- منطق P41 (توجيه الروابط 7907–7916) — يبقى قبل الـ Guard في الترتيب.
- `process_user_task_async` والحدود الخمسة — لا تغيير داخلي.
- مسار الأزرار/الـ callbacks القائمة، محرك Genspark، وكل مسارات curl_cffi.
- الـ Wizard الرسمي (`cmd:new_proj` ➔ `AWAITING_NEW_PROJECT_NAME` ➔ ...).

---

## 3. FIX DESIGN (Checkpoint 2 — قبل أي سطر كود)

### 3.1 المبدأ الحاكم

**Confirmation before ANY Mutation:** كتلة الـ Fallback (7917–7921)
**تُحذف من الوجود** — لا تُخفى خلف شرط. أي نص حر في IDLE يمر على
Intent Guard الذي لا يملك صلاحية الوصول لأي حد من الحدود الخمسة؛
الوصول الوحيد يكون عبر الـ Wizard الرسمي القائم بعد تأكيد صريح.

### 3.2 جدول قبل/بعد (CURRENT BEHAVIOR vs FIX)

| الحالة | قبل P42 | بعد P42 |
|---|---|---|
| نص عابر في IDLE (`2+7=`) | مشروع + حساب + توليد فوراً | بطاقة تأكيد (صياغة Ambiguous) — صفر Mutation |
| نص يشبه برومبت حقيقي في IDLE | نفس الشيء | بطاقة تأكيد (صياغة Strong) — صفر Mutation |
| رسالة غير نصية بلا caption (صورة/ستيكر) | `text=""` ➔ مشروع بنص فارغ! | رفض مهذب — لا بطاقة ولا Mutation |
| زر ✅ تأكيد (nonce مطابق) | — | دخول الـ Wizard الرسمي (`AWAITING_NEW_PROJECT_NAME`) + حفظ `pending_prompt` |
| زر ❌ إلغاء (nonce مطابق) | — | تفريغ الحالة بالكامل + رسالة قصيرة — صفر أثر |
| زر على بطاقة مُبطلة/قديمة | — | «انتهت صلاحية هذا الطلب» بلا Mutation |
| ضغطة ثانية على ✅ (Double-Click) | — | «تم بالفعل» بلا Mutation إضافي |
| اكتمال الـ Wizard بعد التأكيد | المستخدم يعيد كتابة البرومبت | **Smart Prompt Forwarding:** `pending_prompt` يُجدول تلقائياً كأول برومبت |
| كل حالات `AWAITING_*` القائمة | كما هي | كما هي حرفياً (Frozen) |

### 3.3 ترتيب الفحص الإلزامي في فرع message (الخطوة 0)

```
1. is_chat_allowed (P17)                      ← قائم، لا يتغير
2. Document Ingestion (P28)                   ← قائم، لا يتغير
3. /start و /help (Commands)                  ← قائم، قبل الحالات — يفوز على كل شيء
4. سلسلة حالات user_state (AWAITING_* × 17)   ← قائمة، لا تتغير
   + حالة جديدة: AWAITING_PROJECT_CONFIRMATION (§3.5)
5. Project URL Routing (P41 — 7907–7916)      ← قائم، يفوز على الـ Guard دائماً
6. Intent Guard (P42) — يحل محل الـ Fallback  ← جديد (§3.4)
```

### 3.4 الـ Intent Guard (يحل محل أسطر 7917–7921)

```python
# بدل الكتلة القديمة حرفياً:
        handle_idle_intent_guard(chat_id, text)
```

دالة نقية الحدود `handle_idle_intent_guard(chat_id, text)`:

1. `text` فارغ ➔ رسالة `INTENT_GUARD_EMPTY_MESSAGE` (رفض مهذب) —
   Telemetry `EMPTY` — **return** (لا بطاقة).
2. `classify_idle_text_intent(text)` ➔ `"strong"` أو `"ambiguous"`
   (Heuristic نقي: نص ≥ 20 حرفاً **و** ≥ 4 كلمات ➔ strong، غير ذلك
   ambiguous — **يؤثر على الصياغة فقط، السلوك واحد**).
3. توليد `nonce = uuid.uuid4().hex[:12]` (نمط `new_cancel_token` القائم).
4. `set_user_state(chat_id, {"action": AWAITING_PROJECT_CONFIRMATION,
   "pending_prompt": text, "confirm_nonce": nonce})` — النص في الحالة
   حصرياً، **ليس** في callback_data.
5. إرسال بطاقة التأكيد: اقتباس النص حرفياً (مُهرَّب HTML + قصّ للعرض
   فقط عند 500 حرف — `pending_prompt` يُحفظ كاملاً) + الزرين:
   - `[✅ نعم، أنشئ مشروعاً بهذا الطلب]` ➔ `pconf:yes:<nonce>`
   - `[❌ إلغاء]` ➔ `pconf:no:<nonce>`
   (`pconf:yes:` + 12 hex = **21 بايت** ≤ 64 ✓)
6. Telemetry: `🛡️ [P42] Intent Guard SHOWN (<strong|ambiguous>) …`.

### 3.5 حالة `AWAITING_PROJECT_CONFIRMATION` في سلسلة النص

يُضاف فرع في سلسلة الحالات (قبل فرع الروابط العام):

- **نص جديد أثناء الحالة** ➔ إبطال ضمني للبطاقة القديمة:
  - لو النص رابط/معرّف مشروع ➔ `set_user_state({})` ثم منطق P41 نفسه
    (توجيه شرعي) — **Edge 6: الرابط يفوز**.
  - غير ذلك ➔ إعادة تشغيل الـ Guard بنص جديد و nonce جديد
    (البطاقة القديمة صارت مُبطلة تلقائياً لأن nonce الحالة تغيّر).
- `/start` و `/help` أصلاً يُفحصان **قبل** الحالات (سطر 7534) ➔
  **Edge 5 محسوم بنيوياً**: الأمر يفوز والحالة تُستبدل عند الضغط عليه.

### 3.6 معالج الـ Callback — `pconf:*` (في قسم callback_query)

```
pconf:yes:<nonce>:
  state.action == AWAITING_PROJECT_CONFIRMATION و nonce مطابق و pending_prompt موجود:
    ➔ set_user_state({"action": "AWAITING_NEW_PROJECT_NAME",
                       "pending_prompt": …, "consumed_confirm_nonce": nonce})
    ➔ رسالة دخول الـ Wizard الرسمي (نفس صياغة cmd:new_proj + سطر
      «برومبتك محفوظ وسيُرسل تلقائياً بعد اكتمال الإعداد»)
    ➔ Telemetry CONFIRMED
  nonce == state.consumed_confirm_nonce (ضغطة ثانية):
    ➔ «تم بالفعل — أكمل خطوات الإعداد» — Telemetry DUPLICATE — صفر Mutation
  غير ذلك (بطاقة مُبطلة/قديمة):
    ➔ «انتهت صلاحية هذا الطلب» — Telemetry EXPIRED — صفر Mutation

pconf:no:<nonce>:
  مطابق للحالة النشطة ➔ set_user_state({}) + رسالة قصيرة — Telemetry CANCELLED
  غير ذلك ➔ «انتهت صلاحية هذا الطلب» — Telemetry EXPIRED
```

**ملاحظة أمنية:** التأكيد نفسه **لا ينفّذ أي Mutation** — يدخل الـ Wizard
فقط؛ الحدود الخمسة تنفجر لاحقاً بالمسار الطبيعي بعد إكمال الـ Wizard
(اسم ➔ موديل ➔ GitHub ➔ resume prompt) — **DRY: صفر Wizard موازٍ**.

### 3.7 Smart Prompt Forwarding

- ناقل الحالة: معالج `AWAITING_NEW_PROJECT_NAME` (سطر 7565) يبني dict
  جديداً ➔ **تعديل واعٍ وحيد**: تمرير `pending_prompt` و
  `consumed_confirm_nonce` إن وُجدا. بقية انتقالات الـ Wizard تستخدم
  `{**state, …}` أصلاً فتنقلهما تلقائياً (أدلة: 6905، 6933، 6971، 6989).
- عند اكتمال الـ Wizard (موضعا `finalize_new_project_from_state`:
  سطر 7018 زر resume_default + سطر 7650 نص resume مخصص) تُستدعى
  دالة جديدة `forward_pending_prompt_after_wizard(chat_id, state, next_state, settings)`:
  - لا `pending_prompt` ➔ ترجع `next_state` كما هي (سلوك قديم حرفياً).
  - يوجد ➔ `EXECUTOR.submit(process_user_task_async, chat_id, None,
    pending_prompt, model, project_key, project_name)` بسياق المشروع
    المُنشأ شرعياً + رسالة «🚀 برومبتك المحفوظ انطلق تلقائياً» +
    ترجع `{}` (حالة نظيفة). Telemetry `FORWARDED`.
- مسار الـ Wizard **بدون** بطاقة تأكيد (زر cmd:new_proj مباشرة):
  لا `pending_prompt` ➔ صفر تغيير في السلوك.

### 3.8 Edge Cases التسعة — القرارات النهائية

| # | Edge Case | القرار |
|---|---|---|
| 1 | Anti-Stale-Callback | nonce (12 hex) في callback_data + `confirm_nonce` في الحالة؛ القبول فقط عند التطابق مع آخر بطاقة نشطة (§3.6) |
| 2 | حد 64 بايت | النص في `user_state.pending_prompt` حصرياً؛ الزر يحمل `pconf:yes:<nonce>` = 21 بايت (§3.4-5) |
| 3 | رسائل غير نصية في IDLE | `text=""` بعد P28 ➔ رفض مهذب بلا بطاقة وبلا Mutation (§3.4-1) — يُغلق أيضاً ثغرة المشروع بالنص الفارغ |
| 4 | Double-Click على تأكيد | `consumed_confirm_nonce` يُحمل في حالة الـ Wizard ➔ الضغطة الثانية = «تم بالفعل» بلا Mutation (§3.6) |
| 5 | أمر أثناء حالة التأكيد | `/start` `/help` يُفحصان قبل الحالات بنيوياً (سطر 7534) — الأمر يفوز والبطاقة تُبطل عند أول استعمال تالٍ |
| 6 | رابط مشروع أثناء التأكيد | فرع الحالة يفحص `parse_project_locator` أولاً ➔ P41 يفوز والبطاقة تُبطل (§3.5) |
| 7 | صياغة الرسائل | `classify_idle_text_intent` ➔ Ambiguous بتلميح «يبدو نصاً عابراً» / Strong صياغة أوثق — **السلوك واحد** (§3.4-2) |
| 8 | لا Hardcoding | ثوابت top-level: `AWAITING_PROJECT_CONFIRMATION` + `PROJECT_CONFIRM_CALLBACK_PREFIX` + نصوص الرسائل والأزرار (§3.9) |
| 9 | Telemetry | `log_event` عند كل قرار: SHOWN / CONFIRMED / CANCELLED / EXPIRED (+ EMPTY / DUPLICATE / FORWARDED) |

### 3.9 الثوابت الجديدة (top-level — نمط المشروع)

```python
AWAITING_PROJECT_CONFIRMATION = "AWAITING_PROJECT_CONFIRMATION"
PROJECT_CONFIRM_CALLBACK_PREFIX = "pconf"
INTENT_GUARD_STRONG_HINT / INTENT_GUARD_AMBIGUOUS_HINT
INTENT_GUARD_EMPTY_MESSAGE / INTENT_GUARD_EXPIRED_MESSAGE
INTENT_GUARD_ALREADY_CONFIRMED_MESSAGE / INTENT_GUARD_CANCELLED_MESSAGE
PROJECT_CONFIRM_YES_LABEL / PROJECT_CONFIRM_NO_LABEL
INTENT_GUARD_STRONG_MIN_CHARS = 20 / INTENT_GUARD_STRONG_MIN_WORDS = 4
INTENT_GUARD_QUOTE_PREVIEW_LIMIT = 500
```

### 3.10 الدوال الجديدة (كلها نقية الحدود قدر الإمكان)

| الدالة | الدور |
|---|---|
| `classify_idle_text_intent(text) -> str` | نقية — strong/ambiguous |
| `build_project_confirmation_keyboard(nonce) -> dict` | نقية — الزران |
| `render_project_confirmation_card(text, intent) -> str` | نقية — نص البطاقة |
| `handle_idle_intent_guard(chat_id, text)` | الحارس (state + إرسال) |
| `forward_pending_prompt_after_wizard(chat_id, state, next_state, settings) -> dict` | التمرير الذكي |

---

## 4. DECISIONS (تمهيداً لـ DEC-038)

1. **حذف لا إخفاء:** الـ Fallback يُستبدل باستدعاء الحارس — لا يبقى أي
   مسار من IDLE إلى `process_user_task_async` بلا project_key شرعي.
2. **صفر Wizard موازٍ (DRY):** التأكيد يدخل `AWAITING_NEW_PROJECT_NAME`
   القائمة نفسها؛ الفرق الوحيد وجود `pending_prompt` في الحالة.
3. **النص الفارغ يُرفض ولا يُؤكَّد:** لا معنى لبطاقة تأكيد على لا شيء —
   وهذا يغلق ثغرة الصور/الستيكرز (Edge 3) بنفس الضربة.
4. **nonce في الحالة لا في قاعدة بيانات:** آخر بطاقة نشطة واحدة فقط لكل
   chat — أي بطاقة أقدم تُبطل تلقائياً بتغيّر `confirm_nonce`.
5. **Strong/Ambiguous للصياغة فقط:** أي Heuristic يسمح بإنشاء تلقائي
   بلا تأكيد مرفوض — القرار النهائي دائماً بيد المستخدم.

## 5. TESTS (Checkpoint 4 — الأدلة النهائية)

ملف الحراس: `tests/test_p42_intent_guard_and_safe_creation.py` — **63 حارساً / 10 مجموعات**:

| # | المجموعة | يغطي |
|---|----------|------|
| 1 | TestSourceStructure | حذف الـ Fallback نصياً + الثوابت top-level (Edge 8) + Telemetry (Edge 9) |
| 2 | TestIntentClassification | Strong/Ambiguous صياغة فقط — سلوك واحد (Edge 7) |
| 3 | TestIdleGuardZeroMutation | "2+7=" / "63636" / "121" / "hello" → NO CREATE (صفر Mutation عبر Spies على الحدود الخمسة) |
| 4 | TestNonTextMessages | صور/ملفات/ستيكرز/Forward بلا نص → لا تسرب للإنشاء (Edge 3) |
| 5 | TestConfirmCallback | تأكيد → Wizard القائم + إلغاء → صفر أثر + Double-Click Idempotent (Edge 4) + Stale nonce (Edge 1) + nonce لا نص في callback_data (Edge 2) |
| 6 | TestConfirmationCardContent | اقتباس النص حرفياً + الزران + حفظ pending_prompt في الحالة |
| 7 | TestCardInvalidation | نص جديد يبطل + رابط P41 يفوز (Edge 6) + أمر يفوز (Edge 5) + رابط مشوّه يُرفض |
| 8 | TestSmartPromptForwarding | تمرير pending_prompt بعد الـ Wizard + المسار القديم verbatim + E2E كامل |
| 9 | TestExplicitCreationUnchanged | زر cmd:new_proj + AWAITING_NEW_PROMPT كما كانا حرفياً |
| 10 | TestZeroRegression | عقود P41 (تصادم/توجيه/إغلاق) + P32 + P25/P26 نمط العزل + الرموز المجمّدة + الكيبوردات |

**الأدلة (Terminal):**
- `pytest tests/` → **946 passed** (883 baseline + 63 P42) + 12 subtests — صفر Skip جديد.
- `python scripts/hadith_sijil.py` → **Exit 0**.
- `python scripts/rebuild_refactor.py` ثم `pytest tests/test_refactor_parity.py` → **11/11 PASS** (الملف الرئيسي 8212 سطراً).
- نظافة git المرة 41: `.pytest_cache/` و `bridge_bot.log` أزيلا من التتبع بعد إعادة إدخالهما من المزامنة التلقائية.
