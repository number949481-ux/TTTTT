# 15 — PROJECT URL ROUTING & GRACEFUL POLLING SHUTDOWN (Phase 41)

> **وثيقة المواصفات الرسمية — S66 / DEC-037**
> بروتوكول المالك: `Deep_Thinking_Tasks_Remaining.TXT` — البند 7 (PHASE 41).
> القاعدة الحاكمة: INSPECT FIRST — هذه الوثيقة كُتبت **قبل** أي تعديل كود.

---

## 🔄 Deep Thinking Tasks — القائمة الحية (تُحدَّث مع كل خطوة)

- [x] **Checkpoint 0:** قراءة ملفات التوجيه + إثبات Baseline
      (833/833 PASS + `hadith_sijil.py` Exit 0 — بعد نظافة git المرة 36:
      إخراج `.pytest_cache/` + `bridge_bot.log` اللذين أعادتهما المزامنة).
- [x] **Checkpoint 1A:** INSPECT مسار توجيه الروابط + توثيق نقاط التصادم بالأدلة (القسم 2).
- [x] **Checkpoint 1B:** INSPECT `run_telegram_polling` + إثبات سبب ابتلاع Ctrl+C (القسم 3).
- [x] **Checkpoint 2:** كتابة FIX DESIGN كاملاً في هذه الوثيقة قبل أي تنفيذ (القسم 4).
- [x] **Checkpoint 3A:** تنفيذ توجيه الروابط (Parsing SSOT + Registry + Context Guard) — commit `8fc9bc5`.
- [x] **Checkpoint 3B:** تنفيذ الإغلاق النظيف (requests.Session + KeyboardInterrupt) — commit `8fc9bc5`.
- [x] **Checkpoint 4:** اختبارات P41 (**50/50**) + Parity **11/11** + pytest **883/883** + hadith_sijil **Exit 0**.
- [x] **Checkpoint 5:** تحديث الوثائق (DEC-037) + تحديث البند 7 + Commit + التقرير النهائي.

---

## 1. خط الأساس المثبت (Checkpoint 0 — أدلة Terminal حقيقية)

```
$ python3 -m pytest tests/ -q
833 passed, 12 subtests passed in 2.21s

$ python3 scripts/hadith_sijil.py ; echo $?
GATE_EXIT=0
```

ملاحظة نظافة: المزامنة التلقائية أعادت `.pytest_cache/` + `bridge_bot.log`
للتتبع (كسر حارسي `test_p17_hardening`) ➔ أُخرجا بـ `git rm --cached`
(**المرة 36** — موافقة S41 الدائمة) ثم عاد الأساس أخضر 833/833.

---

## 2. الفحص الجنائي — محور A: فك وتوجيه الروابط (Checkpoint 1A)

### 2.1 CALL PATH الكامل لرسالة نصية تحمل رابط مشروع

```
run_telegram_polling (p12 — سطر 7852)
  └─ EXECUTOR.submit(handle_telegram_update, update)
       └─ handle_telegram_update (p12)
            ├─ بوابة is_chat_allowed (P17)
            ├─ كتلة Document Ingestion (P28)
            ├─ أوامر /start وأزرار الكيبورد
            ├─ سلسلة حالات user_state (AWAITING_*):
            │    ├─ AWAITING_CONT_URL (سطر 7784) ➔ resolve_resume_context(text) ✅ سليم
            │    ├─ AWAITING_NEW_PROMPT (سطر 7793) ⚠️ نقطة التصادم 1
            │    │    └─ text يُمرَّر مباشرة كبرومبت لـ process_user_task_async
            │    │       بسياق state.project_key (مشروع A) — حتى لو كان رابط مشروع B
            │    └─ AWAITING_CONT_PROMPT (سطر 7804) ⚠️ نقطة التصادم 2
            │         └─ text يُمرَّر كبرومبت + url = state["url"] (مشروع A)
            │            — رابط مشروع B يُنفَّذ حرفياً كنص برومبت على A
            └─ الفرع العام للروابط (سطر 7816):
                 if "genspark.ai" in text or re.search(r"[a-f0-9\-]{36}", text)
                   └─ resolve_resume_context (p08 — سطر 4187)
                        ├─ extract_project_id (p05 — سطر 1900) ⚠️ نقطة التصادم 3
                        ├─ lookup_project_key_for_locator (p08 — سطر 4169)
                        │    └─ REGISTRY_INDEX_LOCK ➔ pid_to_key[pid] ✅ سليم
                        ├─ مفتاح موجود ➔ present_resume_summary (p09 — سطر 5066)
                        └─ غير مسجّل ➔ present_external_resume_decision (p09 — سطر 5709)
```

### 2.2 نقاط التصادم المثبتة بالأدلة

| # | الموضع (قبل الإصلاح) | الدليل الحرفي | الخطر |
|---|---|---|---|
| **T1** | `AWAITING_NEW_PROMPT` — سطر 7793 | `EXECUTOR.submit(process_user_task_async, chat_id, None, text, ..., state_project_key, ...)` | سياق A نشط + المستخدم يرسل رابط مشروع B ➔ الرابط يُرسَل **كنص برومبت** لمشروع A = **Cross-Project Context Hijacking** |
| **T2** | `AWAITING_CONT_PROMPT` — سطر 7804 | `target_url = state.get("url")` ثم `EXECUTOR.submit(..., target_url, text, ...)` | نفس T1 لكن أخطر: التنفيذ يستأنف فعلياً على مشروع A بينما المستخدم قصد المشروع B |
| **T3** | `extract_project_id` — سطر 1910 | `return url_str` (fallback) | رابط مشوّه/نص عشوائي بلا UUID يُعاد **كما هو** كـ"PID" — يتسرب للمسارات (الدوال المستهلكة تحتمي جزئياً بـ `is_probable_project_id` لكن ليس كلها) |
| **T4** | تضارب Root/Latest — `upsert_project_identity` سطر 4241 | `data["pid_to_key"][alias] = key` لكل alias | الكتابة **آخر كاتب يكسب** بلا تحذير: لو root_pid لمشروع سُجّل لاحقاً كـ latest لمشروع آخر (خطأ تشغيلي) يُخطف المفتاح بصمت |

**قرار نطاق T4:** بعد الفحص، آلية aliases نفسها **سليمة بنيوياً** (root/latest
لنفس المشروع دائماً عبر المسار الشرعي، والحذف P26 ينظف الـ aliases) — الخطر
الحقيقي المطلوب علاجه في نص المهمة هو T1/T2 (تصادم السياق النشط) + T3 (الرابط
المشوّه). **T4 يُغطى بحارس اختباري توثيقي** (سلوك آخر-كاتب-يكسب الموثق) بلا
تعديل كود — تعديل دلالات الـ Registry خارج النص الصريح = Refactor ممنوع.

### 2.3 Edge Cases المطلوبة نصاً وحالتها قبل الإصلاح

| Edge Case | السلوك قبل P41 | الحكم |
|---|---|---|
| رابط لمشروع غير مسجّل (بلا سياق نشط) | الفرع العام ➔ `present_external_resume_decision` برسالة صريحة | ✅ سليم أصلاً |
| رابط مشوّه (نص فيه `genspark.ai` بلا UUID) | `extract_project_id` يعيد النص كاملاً ➔ `is_probable_project_id=False` ➔ خيار خارجي بـ URL خام | ⚠️ يلزم رسالة رفض صريحة |
| رابط أثناء سياق نشط (T1/T2) | يُنفَّذ كبرومبت نصي على المشروع الخطأ | ❌ العلة الجوهرية |
| تضارب Root ID مع Project ID | آخر كاتب يكسب بصمت (T4) | 🛡️ حارس توثيقي |

---

## 3. الفحص الجنائي — محور B: حلقة Polling وCtrl+C (Checkpoint 1B)

### 3.1 CALL PATH الكامل للحلقة (قبل الإصلاح — أسطر 7852–7894)

```
main() (سطر 7896)
  └─ run_telegram_polling() (سطر 7852)
       ├─ سطر 7862–7867: عميل getUpdates:
       │     try: from curl_cffi import requests as cffi ; sess = cffi.Session()
       │     except: import requests ; sess = requests.Session()   ← curl_cffi يفوز دائماً عند توفره
       ├─ سطر 7870: try الخارجي
       │     └─ while True:
       │          ├─ سطر 7873: r = sess.get(url, params={offset, timeout:20}, timeout=30)
       │          ├─ سطر 7887: except Exception ← يلتقط أخطاء الشبكة
       │          └─ سطر 7891: time.sleep(backoff)
       └─ سطر 7892: except KeyboardInterrupt ← طباعة رسالة فقط، بلا sys.exit(0)
```

### 3.2 السبب الجذري المثبت لابتلاع Ctrl+C

1. **CFFI Interrupt Corruption (ويندوز):** `curl_cffi` ينفّذ I/O داخل امتداد C
   — ضغط Ctrl+C أثناء `sess.get` المعلقة (long-poll يصل 30 ثانية) لا يصل
   كـ `KeyboardInterrupt` نظيف؛ يظهر كخطأ CFFI/`curl: (23)` وهو **Exception
   عادي** ➔ يُلتقط في `except Exception` (سطر 7887) ➔ يُسجَّل كـ"خطأ حلقة"
   ➔ الحلقة **تستمر بالدوران** وكأن شيئاً لم يكن = المستخدم لا يستطيع إيقاف
   البوت.
2. **غياب `sys.exit(0)`:** حتى عندما يصل `KeyboardInterrupt` نظيفاً (لحظة
   `time.sleep` مثلاً)، الحاصل طباعة رسالة والعودة من الدالة — بلا كود خروج
   صريح، و`SystemExit` غير ملتقط أصلاً.
3. **`requests` النقية آمنة:** مكتبة `requests` (pure-Python I/O عبر socket)
   تسمح بوصول `KeyboardInterrupt` أثناء الانتظار كـ BaseException حقيقي لا
   يلتقطه `except Exception` — وهي مثبتة أصلاً (`requirements.txt`:
   `requests>=2.28.0` + الاستيراد الاحتياطي موجود بالفعل بالكود).

### 3.3 حدود النطاق المجمّد (⛔ ممنوع لمسه)

`curl_cffi` في كل مسارات Genspark يبقى حرفياً: الأسطر 1117 (Telegram API core —
خارج الحلقة)، 1857، 2077، 2123، 2177، 2202 — **الموضع الوحيد** المستبدل هو
عميل getUpdates داخل `run_telegram_polling` (سطر 7862–7867).

---

## 4. FIX DESIGN (Checkpoint 2 — قبل أي تنفيذ)

### 4.1 محور A — التوجيه

**A1. Parsing SSOT — دالة مركزية جديدة `parse_project_locator(text)` (p05، بعد `extract_project_id`):**
```python
def parse_project_locator(text) -> dict:
    # ترجع دائماً: {"kind": "...", "pid": "...", "raw": "..."}
    # kind ∈ {"pid", "malformed", "none"}
    # - "pid":       نص فيه UUID صالح (رابط genspark أو UUID خام) + pid مستخرج
    # - "malformed": النص يشبه رابط مشروع ("genspark.ai" فيه) لكن بلا UUID صالح
    # - "none":      نص عادي لا علاقة له بالروابط (برومبت طبيعي)
```
- تُبنى **فوق** `extract_project_id` + `is_probable_project_id` القائمتين
  (بلا أي تعديل عليهما — عقود P27/P26 القائمة عليهما محفوظة حرفياً).
- تعالج T3: الرابط المشوّه يُصنَّف `malformed` صراحةً بدل التسرب.

**A2. Context Collision Guard — دالة `detect_context_collision(state, text)` (p05):**
```python
def detect_context_collision(state, text) -> dict | None:
    # None = لا تصادم (النص برومبت عادي — المسار القديم حرفياً)
    # dict = {"pid": ..., "kind": ...} عند نص يحمل رابط/PID داخل سياق برومبت نشط
```
- تُستدعى **حصرياً** في فرعي `AWAITING_NEW_PROMPT` + `AWAITING_CONT_PROMPT`
  (p12) **قبل** جدولة `process_user_task_async`.
- عند التصادم (kind=pid): **يستحيل التنفيذ على المشروع الخطأ** — لا جدولة؛
  تُمسح الحالة وتُوجَّه الرسالة عبر المسار الشرعي نفسه المستخدم في الفرع
  العام (`resolve_resume_context` ➔ `present_resume_summary` للمسجّل /
  `present_external_resume_decision` لغير المسجّل) + رسالة تنبيه صريحة
  بأن السياق السابق أُغلق.
- عند kind=malformed: رسالة رفض صريحة (بلا Fallback صامت) وبقاء الحالة
  كما هي (المستخدم ما زال في سياقه يمكنه إرسال برومبت صحيح).
- **حارس دقة حاسم:** برومبت طبيعي يذكر "genspark" نصاً أو يحتوي أرقاماً
  ليست UUID ➔ `None` (لا تصادم) — منع False Positive يكسر البرومبتات العادية.

**A3. الفرع العام (سطر 7816) + `AWAITING_CONT_URL`:** بلا تغيير سلوكي —
يستفيد من رسالة الرفض الصريحة للرابط المشوّه فقط عند `malformed`.

**A4. T4 (تضارب Root/Latest):** حارس اختباري توثيقي فقط (القرار بالقسم 2.2).

### 4.2 محور B — الإغلاق النظيف

**B1. عميل getUpdates = `requests.Session()` حصرياً (سطر 7862–7867):**
```python
import requests as _polling_requests   # داخل الدالة (نمط الاستيراد المحلي القائم)
sess = _polling_requests.Session()
```
- يستبدل كتلة try/except الحالية (curl_cffi أولاً) — **داخل الحلقة فقط**.
- كل مسارات Genspark تبقى curl_cffi حرفياً (القسم 3.3).

**B2. التقاط KeyboardInterrupt/SystemExit داخل الحلقة وخارجها:**
```python
while True:
    try:
        ...
    except (KeyboardInterrupt, SystemExit):
        raise                      # لا ابتلاع في معالج أخطاء الحلقة
    except Exception as e:
        ...                        # الحالي حرفياً
# الخارجي:
except (KeyboardInterrupt, SystemExit):
    print(... "⏹️ تم إيقاف البوت يدوياً (Ctrl+C) — إغلاق نظيف")
    log_event("info", "⏹️ Clean shutdown: KeyboardInterrupt")
    sys.exit(0)
```
- ملاحظة دقيقة: `except Exception` لا يلتقط KeyboardInterrupt نظرياً، لكن
  إضافة `except (KeyboardInterrupt, SystemExit): raise` **قبله** تحمي من
  حالة التغليف (مقاطعة تصل أثناء معالجة `r.json()`/الجدولة وتتحول لسلسلة
  استثناءات) وتوثق النية صراحة — Defense in Depth.
- `sys.exit(0)` صريح في المعالج الخارجي + بلا أي Traceback.

### 4.3 حزمة الاختبارات `tests/test_p41_routing_and_graceful_shutdown.py`

| المجموعة | التغطية |
|---|---|
| TestLocatorParsing | كل صيغ الروابط (agents?id= / autopilotagent_viewer?id= / UUID خام / مشوّه / نص عادي / None / أرقام غير UUID) |
| TestRegistryResolution | مطابقة key/root/latest + غير الموجود ➔ None بلا Fallback + T4 التوثيقي |
| TestContextCollisionGuard | A نشط + رابط B (مسجّل/غير مسجّل/مشوّه) ➔ استحالة التنفيذ الخطأ + برومبت عادي ➔ None |
| TestHandlerIntegration (سورس) | الحارس مستدعى في الفرعين قبل الجدولة + المسارات القديمة باقية |
| TestPollingClientContract (سورس) | عميل getUpdates = requests وليس curl_cffi + بقاء curl_cffi بالمواضع الأخرى |
| TestGracefulShutdown | KeyboardInterrupt ➔ خروج نظيف + sys.exit(0) (Mocks — بلا شبكة/Ctrl+C فعلي) |
| TestZeroRegression | عقود Success/Resume/Rotation + P35/P40 سليمة |

### 4.4 خطة PARTS/Parity

التعديلات في p05 (دالتان جديدتان) + p12 (الفرعان + الحلقة) ➔ تحديث حدود
p05/p06…p12 بإزاحة الأسطر + إعادة `scripts/rebuild_refactor.py` ➔ 11/11.

---

## 5. سجل تنفيذ Checkpoints 3–5

(يُملأ أولاً بأول مع الأدلة — القسم يُحدَّث مع كل خطوة)

- **CP3A ✅ (`8fc9bc5`):** الملف 8008 أسطر (+103 من 7905):
  - p05: ثابت `MALFORMED_PROJECT_LINK_MESSAGE` (بعد سطر 324) + دالتا
    `parse_project_locator` / `detect_context_collision` (بعد `extract_project_id`
    — أسطر ~1920–1974) — بلا أي تعديل على الدوال القائمة.
  - p11/p12: `handle_prompt_context_collision` (بعد `get_main_keyboard` سطر ~6704)
    + استدعاء الحارس أول سطر في فرعي `AWAITING_NEW_PROMPT`/`AWAITING_CONT_PROMPT`
    + رفض صريح للـ malformed في `AWAITING_CONT_URL` + الفرع العام.
- **CP3B ✅ (`8fc9bc5`):** في `run_telegram_polling`:
  - عميل getUpdates = `requests.Session()` حصرياً (استبدال كتلة curl_cffi try/except).
  - `except (KeyboardInterrupt, SystemExit): raise` داخل الحلقة قبل `except Exception`.
  - المعالج الخارجي: رسالة إغلاق نظيف + `sys.exit(0)`.
  - curl_cffi باقٍ بكل مسارات Genspark الأخرى حرفياً.
- **CP4 ✅:** حزمة `tests/test_p41_routing_and_graceful_shutdown.py` مكتملة — **50 حارساً**
  (8 مجموعات: Parsing / Registry / CollisionGuard / CollisionHandler /
  HandlerIntegration / PollingClientContract / GracefulShutdown / ZeroRegression).
  إصلاح 4 حراس كانت صياغتهم أولية خاطئة (الكود كان سليماً):
  - `test_polling_no_curl_cffi` ➔ `test_polling_no_curl_cffi_usage`: الحارس على
    الاستيراد/الاستخدام الفعلي — ذكر curl_cffi في تعليق [P41] التوثيقي مسموح.
  - `test_requests_in_requirements`: `^requests>=` ➔ `(?m)^requests>=` (السطر ليس أول الملف).
  - `test_inner_interrupt_handler_precedes_generic_exception`: المرساة صارت
    رسالة خطأ الحلقة نفسها (أول `except Exception` بالدالة خاص بـ EXECUTOR.submit).
  - `test_p18_activity_monitor_intact`: الاسم الحقيقي `should_stop_on_activity_change`
    (لا `detect_activity_signature_change`) بعقده الفعلي (active + tasks_remaining).
  الأدلة: `50 passed` + `883 passed, 12 subtests` + `test_refactor_parity` = 11/11
  + `hadith_sijil.py` ➔ `GATE 883/883 — Exit Code 0` + نظافة git (المرة 37:
  إخراج `.pytest_cache/` + `bridge_bot.log` بعد أن أعادتهما المزامنة).
- **CP5 ✅:** DEC-037 في SESSION_LOG + تحديث PROGRESS (الجذري + engineering)
  + V3_RESUME (قاعدة P41 الدائمة + عدادات 883) + TEST_SUITE_CATALOG (35 ملفاً / 883)
  + README (الجذري + engineering) + تحديث البند 7 من `Deep_Thinking_Tasks_Remaining.TXT`.
