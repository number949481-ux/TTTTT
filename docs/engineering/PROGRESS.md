# PROGRESS — Telegram Gen Bridge 01.31

> **عقد هذا الملف:** هذا هو المصدر الوحيد للحالة الحية للبرنامج: tasks والمراحل والحواجز والنسب وقرار الإصدار.
> الملفات الأخرى تعرّف الأدلة والقرارات والمواصفات فقط، وتشير إلى IDs؛ لا تنسخ status تشغيلياً.
> لا تغلق أي Task دون دليل: commit SHA + نتيجة Quality Gate فعلية، أو `DEFERRED/WAIVED` بقرار مالك صريح.

---

## ⚡ تعليمات الاستئناف السريع (Fast Resume Instructions)

1. اقرأ Header ثم آخر قيد في `SESSION_LOG.md`.
2. لا تبدأ Task جديدة قبل معرفة `current-task` و `current-blocker`.
3. لا تخمّن قرار مالك؛ القرار غير المكتوب يعني `BLOCKED-ON-OWNER`.
4. لا تعدل baseline `01.24` أو مسار نجاحه قبل Task/قرار/اختبار صريح.

---

## 📊 Header

| الحقل | القيمة |
|---|---|
| **last-updated** | 2026-08-20 — S41 |
| **repository / branch** | `number949481-ux/TTTTT` / `genspark_ai_developer` |
| **target-version** | `01.31` |
| **baseline code** | `01.30` (Baseline مجمّد — و`01.29`/`01.28`/`01.27`/`01.26` Golden Baselines للمرجعية فقط، ممنوع تعديلها) 🛡️ |
| **target bot script** | `01.31_telegram_gen_bridge.py` 🚀 |
| **target engine** | `01.03Genspark_claude-opus-5-code.py` ⚙️ |
| **program-stage** | Stage 3 — Execution |
| **current WBS phase** | **P21 — دقة تصنيف commit في الرفع REST (جديد ➕ vs معدل ✏️)** 🎯 |
| **current slice** | `TSK-3901` (DONE) ➔ إصلاح `_default_github_uploader`: الملف الموجود على الريموت بمحتوى مختلف يُصنّف `modified` (✏️ معدل) بدل دمجه مع `uploaded` (➕ جديد) — التصنيف عبر `remote_sha` المتاح أصلاً قبل الـ PUT + حارسان جديدان في test_p20 (اختبارات 09/10) + تحديث PARTS (+4 أسطر → 6390) وإعادة بناء bridge_refactor بتطابق بايت |
| **current-task** | `P21 complete` + صيانة S41: المزامنة التلقائية أعادت تتبع `.pytest_cache/` و `bridge_bot.log` فكسرت حارسَي P17 (219/221) ➔ أُخرجا من التتبع مجدداً (commit `e1a388b`) — عادت 221/221 + بوابة Exit 0 |
| **next-action** | اختبار تشغيلي حي (E2E) من المالك على 01.31 (مسار DATA_RETENTION + الرفع REST مع التحقق من عدّاد ✏️ معدل) + قرارا مالك معلّقان: (أ) حد قص التاريخ المحقون في استئناف الجسر، (ب) مصير `01.30_telegram_gen_bridge.py` القديم — وفي بداية كل جلسة: فحص `git ls-files | grep -E "pytest_cache|bridge_bot.log"` لأن المزامنة التلقائية تعيد تتبعهما |
| **current-blocker** | `BLOCKED-ON-OWNER` — كل البنود المتبقية تحتاج قرار مالك صريح (E2E حي + قرارا القص/حذف 01.30) — البوابة مجتازة بالكامل |
| **completion** | 221/221 Tests Verified (100%) 🧪 |
| **quality-gate** | `python scripts/hadith_sijil.py` ➔ 221/221 PASS — Exit Code 0 |
| **session-log** | `docs/engineering/SESSION_LOG.md` |
| **release decision** | `READY` 🟢 (P21: تصنيف commit دقيق + P20: REST-Only + DATA_RETENTION failover + P19 نسخ الإعدادات + P18 وقف فوري لمؤشر النشاط — صفر انحدار) |

---

## 📌 سجل البنود المؤجلة (Deferred Backlog) — بقرار مالك صريح

| ID | البند | القرار | الحالة |
|---|---|---|---|
| **DEFERRED-001** | **ميزة نسخ إعدادات مشروع لمشروع آخر** (Copy Project Settings) — نسخ إعدادات مشروع قائم من `ProjectRegistry` إلى مشروع جديد بأمر تيليجرام | كانت مؤجلة بعد P16/P17/P18 — نُفذت في P19 (إصدار 01.30) | ✅ `DONE` — أُنجزت في S38 بحزمة حراسة 24 اختباراً (`tests/test_p19_copy_settings.py`) |


---

## 🔒 Scope Freeze — 01.25 (P7-A)

### 🟢 داخل النطاق (In-Scope):
1. **المعاينة الحية الفورية:** التقاط حدث `project_start` في أول ثانية وإرسال زر `URL Button` مباشر.
2. **الامتثال لـ 00-telegram-ux-guardian:**
   - تطبيق مبدأ الرسالة الواحدة المتطورة (Single Evolving Message) وتعديل نفس الرسالة عند `COMPLETED`.
   - كتم الإشعارات التقنية الزائدة وسياسات الأرشيفات لحماية نظافة الشات.
3. **أزرار Telegram النظيفة:** أزرار `Inline URL Buttons` نقية دون حقل `style` ودون أزرار `retry` ميتة.
4. **حماية تدفق الـ SSE:** عزل استدعاء الـ Callback بـ `try/except` لضمان عدم توقف التوليد إطلاقاً.
5. **تنزيل الأرشيف:** الإبقاء على مسار تنزيل وفك الأرشيف المحلي بعد اكتمال المشروع فقط بنسبة 100% (`COMPLETED`).

### 🔴 خارج النطاق / مجمّد (Out-of-Scope / Frozen):
- ⛔ لا تعديل على كود `01.24_telegram_gen_bridge.py` نهائياً.
- ⛔ لا أزرار `callback_data` ميتة بدون handler معتمد.
- ⛔ لا تعديل قسري على إعداد الخصوصية العام بالمحرك (`is_private` متروك كقرار لـ P7-B).

---

## 🧩 مصفوفة المهام المجهرية التتابعية (Micro-Tasks Pipeline):

- [x] **`[TSK-2501]`** توثيق النطاق والمهمة في `docs/engineering/PROGRESS.md` بحالة `Approved`.
- [x] **`[TSK-2502]`** بناء حزمة اختبارات الوحدة الـ 6 لـ P7-A في `tests/test_p7_live_preview.py` (31/31 PASS).
- [x] **`[TSK-2503]`** إضافة `on_project_start_callback` في المحرك `01.02Genspark_claude-opus-5-code.py` (31/31 PASS).
- [x] **`[TSK-2504]`** بناء أزرار المعاينة الحية ودورة الرسالة في البوت `01.25_telegram_gen_bridge.py` (31/31 PASS).
- [x] **`[TSK-2505]`** توليد منظومة الـ 10 وثائق لـ 01.25 والفحص الآلي الشامل (`31/31 PASS`) بـ `hadith_sijil.py`.

---

## 🧩 P8 — Single-File Doctrine Consolidation (S28):

- [x] **`[TSK-2601]`** إصلاح انهيار بوابة الجودة: `import re` مفقود في `scripts/hadith_sijil.py` (كانت Exit Code 1 عند الخطوة 3). — دليل: commit `0ec245e` + Gate Exit Code 0.
- [x] **`[TSK-2602]`** دمج `CONTRACTS` + `is_protected` + `apply_contract` من `runtime/model_runtime.py` داخل `01.25_telegram_gen_bridge.py` بعد `MODEL_ALIASES` (SSOT موحد، بدون تغيير أي signature قائمة). — دليل: commit `0ec245e` + 32/32 PASS.
- [x] **`[TSK-2603]`** تحويل imports الاختبارات (`test_p2_model_routing.py` + `test_p3_regression.py`) للاستيراد من `01.25` مباشرة دون لمس أي assertion، وتحويل `scripts/generate_docs.py` لقراءة العقود من `01.25`. — دليل: commit `0ec245e` + 32/32 PASS.
- [x] **`[TSK-2604]`** حذف حزمة `runtime/` نهائياً من الشجرة والـ git index بعد نجاح البوابة (`git rm -r runtime/`). — دليل: commit `0ec245e` + `hadith_sijil.py` Exit Code 0 بعد الحذف.
- [x] **`[TSK-2605]`** تصحيح انحرافات هذا الملف عن الواقع: repository/branch الفعلي (`number949481-ux/TTTTT` / `main`)، وتوضيح أن baseline `01.24` غير موجود كملف في المستودع. — دليل: هذا الـ commit.

---

## ⚡ P9 — True SSE Streaming Fix (S29):

> **جذر العلة (مؤكد):** استدعاء `ask_proxy` في المحرك كان **بدون** `stream=True`، ثم تُقرأ الاستجابة عبر `r.text.splitlines()`. في `curl_cffi` هذا يعني تحميل جسم الـ SSE **كاملاً حتى إغلاق الخادم للاتصال** قبل معالجة أي سطر. النتيجة: حدث `project_start` وزر المعاينة الحية كانا يظهران **بعد انتهاء التوليد بالكامل** بدلاً من الثانية الأولى، رغم سلامة معمارية الـ Callback نفسها (P7-A).

- [x] **`[TSK-2701]`** إصلاح المحرك `01.02Genspark_claude-opus-5-code.py`: إضافة `stream=True` لطلب `ask_proxy` + استبدال `r.text.splitlines()` بـ `r.iter_lines()` اللحظية (مع فك ترميز bytes آمن) + قراءة آمنة لأجسام أخطاء HTTP + `r.close()` في كل مسارات الخروج. — دليل: 35/35 PASS + Gate Exit 0.
- [x] **`[TSK-2702]`** إضافة 3 اختبارات حراسة ضد الانحدار في `tests/test_p7_live_preview.py` (`TestTrueSSEStreamingGuard`): (8) إلزام `stream=True` في ask_proxy، (9) إلزام `iter_lines()` وتحريم `r.text.splitlines()`، (10) محاكاة بث تثبت انطلاق الـ callback قبل استهلاك أي chunk من الرد. — دليل: 35/35 PASS.
- [x] **`[TSK-2703]`** تشغيل بوابة `hadith_sijil.py` كاملة: 35/35 PASS — Exit Code 0 — 0.252s.
- [x] **`[TSK-2704]`** تحديث ملفات البروتوكول الإجبارية (`PROGRESS.md` + `V3_RESUME_SESSION.md` + `README.md` + `SESSION_LOG.md`) ومواءمتها مع الواقع (عداد الاختبارات 32→35). — دليل: هذا الـ commit.

---

## 🛡️ P10 — Docs Integrity Guard (توثيق استدراكي):

> أداة `scripts/verify_docs_integrity.py` مدمجة كخطوة 2 داخل بوابة `hadith_sijil.py`: تمسح كامل منظومة `docs/` (31 ملفاً) وتتحقق من سلامة كل الروابط الداخلية، مع اختبار وحدة حارس في `tests/test_p10_docs_integrity.py` (محسوب ضمن عداد الـ 35 التاريخي).

- [x] **`[TSK-2801]`** أداة فحص تكامل التوثيق `verify_docs_integrity` + دمجها في البوابة كخطوة إلزامية. — دليل: Gate Step 2 OK (31 ملف، صفر أخطاء).
- [x] **`[TSK-2802]`** اختبار حراسة `test_p10_docs_integrity.py` يضمن صفر روابط مكسورة و ≥20 ملفاً ممسوحاً. — دليل: PASS ضمن البوابة.

---

## 🎨 P11 — Button Styles: أزرار Inline ملونة (S30 — Telegram Bot API 9.4):

> **الميزة:** Bot API 9.4 أضاف حقل `style` الاختياري لأزرار `InlineKeyboardButton` بالقيم الرسمية الثلاثة فقط: `primary` (أزرق) / `success` (أخضر) / `danger` (أحمر). أي قيمة أخرى (مثل `positive`/`destructive`) ترجع `400 invalid button style`، لذلك اعتُمدت Whitelist صارمة مع تنقية مركزية في `make_inline_keyboard`.

- [x] **`[TSK-2901]`** ترقية الإصدار: نسخ `01.25` المجمّد إلى `01.26_telegram_gen_bridge.py` (baseline جديد `01.25`) ونسخ المحرك `01.02` إلى `01.03Genspark_claude-opus-5-code.py` مع تحديث مرجع المحرك داخل البوت. — دليل: commits `0dda411` + `3a812e2`/`1c5cad9` + 45/45 PASS.
- [x] **`[TSK-2902]`** إضافة `ALLOWED_BUTTON_STYLES = frozenset({"primary","success","danger"})` وتنقية مركزية للحقل `style` داخل `make_inline_keyboard` (normalize: strip+lower، وحذف أي قيمة خارج الـ Whitelist). — دليل: 45/45 PASS.
- [x] **`[TSK-2903]`** تلوين الأزرار الاستراتيجية: زر المعاينة الحية أثناء البناء `primary` (أزرق)، زر المشروع المكتمل `success` (أخضر)، زر الإلغاء `danger` (أحمر)، زر "كمل الآن" `success`، زر "مشروع جديد" `primary`. — دليل: 45/45 PASS.
- [x] **`[TSK-2904]`** بناء 10 اختبارات حراسة في `tests/test_p11_button_styles.py` (`TestButtonStylesWhitelist` + `TestColoredKeyboardsIntegration`): تطابق الـ Whitelist الرسمية حرفياً، تمرير style الصالح، حذف غير الصالح، normalization، عدم كسر الأزرار القديمة، سلامة JSON، منع تسرب حقول غير مدعومة، ألوان المعاينة الحية، ومنع أي literal غير رسمي في الكود المصدري. — دليل: 45/45 PASS — Gate Exit 0 (0.249s).
- [x] **`[TSK-2905]`** تحديث ملفات البروتوكول الإجبارية (`PROGRESS.md` + `SESSION_LOG.md` + `V3_RESUME_SESSION.md` + `README.md`) ومواءمة العدادات (35→45) والإصدار (01.25→01.26) والمحرك (01.02→01.03). — دليل: هذا الـ commit.




---

## ♻️ P12 — Same-Project Resume + Idle-Timeout + Full-Print (S31):

> **جذور العلة (3 مؤكدة من اللوج):**
> 1. **TIMEOUT بلا لزمة:** `timeout` سكالري في `ask_proxy` = قطع كلي يقتل المشاريع الطويلة في منتصف التوليد حتى لو الخادم يبث بنشاط.
> 2. **ضياع project_id عند الانقطاع:** أي استثناء أثناء حلقة SSE كان يرجع `(None, None, None)` فيضيع الـ pid الملتقط.
> 3. **شات ID جديد عند كل إعادة محاولة:** حلقة retry في `send_message_and_make_public` كانت تعيد الـ fork من الرابط الأصلي في كل محاولة → مشروع/شات جديد تماماً بدل استكمال نفس المشروع.

- [x] **`[TSK-3001]`** المحرك: تهيئة حالة البث قبل `try` (`full_text`/`proj_id_new`/`stream_interrupted`/`_t_start`) + مهلة tuple `(connect, read)` تتحول داخل curl_cffi مع `stream=True` إلى **مهلة خمول** (LOW_SPEED_TIME) — البث لا يُقطع طالما الخادم يرسل، ويُقطع فقط عند صمته الكامل. (تحقق من مصدر `curl_cffi/requests/utils.py` قبل الاعتماد). — دليل: 69/69 PASS.
- [x] **`[TSK-3002]`** المحرك: عزل حلقة SSE بـ try/except؛ عند الانقطاع مع pid حي يرجع `("__STREAM_INTERRUPTED__", proj_id_new, asst_msg_id)` بدل الفشل، و`except` الخارجي يرجع `proj_id_new` بدل `None`. — دليل: 69/69 PASS.
- [x] **`[TSK-3003]`** المحرك: إزالة البث الحي من الترمنال (`print(chunk)` + `live_started`) — الرد يُطبع **كاملاً دفعة واحدة** عند الاكتمال + سطر `⏱️ اخد X.X ثانية`، مع الإبقاء على الكتابة اللحظية في `ticket_file` (ميزة أصلية). — دليل: 69/69 PASS.
- [x] **`[TSK-3004]`** البوت: نمط `carry_pid` في `send_message_and_make_public` — أي pid يُلتقط (من `project_start` أو من رجوع `send_chat`) يثبت عبر المحاولات؛ أي retry تالية تستأنف **نفس المشروع** ولا تعيد الـ fork من الرابط الأصلي أبداً. — دليل: 69/69 PASS.
- [x] **`[TSK-3005]`** البوت: `__STREAM_INTERRUPTED__` → `final_status="RUNNING"` → دخول حلقة polling عبر `fetch_project_messages` على نفس pid حتى الاكتمال السحابي (المهمة لا تفشل ولا تُعاد من الصفر). — دليل: 69/69 PASS.
- [x] **`[TSK-3006]`** البوت (P12-C): زر المعاينة الحية يُرسل فوراً في مسارات الاستئناف والـ fork أيضاً (الخادم لا يرسل `project_start` لمشروع قائم) — استدعاء الـ callback مباشرة فور معرفة الـ pid. — دليل: 69/69 PASS.
- [x] **`[TSK-3007]`** المراجعة الشاملة (P12-E): (أ) `fetch_project_messages` كانت ترجع `None` ضمنياً في مسار الخطأ — أُضيف `return []` صريح. (ب) حلقة polling كانت تقرأ آخر رسالة أياً كان دورها — قد تكون رسالة **المستخدم** نفسها فيُحتسب COMPLETED كاذب ويُعاد نص السؤال كأنه الرد؛ أُصلحت لتقرأ آخر رسالة `role == "assistant"` فقط. — دليل: 69/69 PASS + Gate Exit 0.
- [x] **`[TSK-3008]`** حزمة حراسة `tests/test_p12_resume_same_project.py` (13 اختباراً): علامة الانقطاع، حفظ pid في كل مسارات الخروج، تحريم البث للترمنال، طباعة زمن التنفيذ، مهلة tuple، بقاء ticket_file، وجود carry_pid وتخطي الـ fork، STREAM_INTERRUPTED→RUNNING، تمرير الـ callback دائماً، انطلاق المعاينة في مسارات الاستئناف، وتزامن `bridge_refactor/parts/p06`. + تحديث `test_p7` (test_08) لصيغة الـ tuple. — دليل: 56→69 اختباراً، Gate Exit 0 (0.375s).
- [x] **`[TSK-3009]`** تحديث خريطة `scripts/rebuild_refactor.py` (حدود p06–p12 بعد نمو 01.26 إلى 6128 سطراً) + إعادة توليد `bridge_refactor/` بتطابق بايت مثبت. — دليل: `test_refactor_parity` PASS ضمن 69/69.
- [x] **`[TSK-3010]`** تحديث ملفات البروتوكول الإجبارية (`PROGRESS.md` + `SESSION_LOG.md`) ومواءمة العدادات (45→69) والفرع (`genspark_ai_developer`). — دليل: هذا الـ commit.

---

## 💰 P13 — Pre-Flight Balance Check (S32): فحص الرصيد قبل أي إرسال + تبريد 29h للرصيد المنخفض

> **جذر العلة (مؤكد بمراجعة P13-A):** الفحص المسبق الحالي في `send_message_and_make_public` يقبل أي رصيد `> 0` — حساب بـ 20 نقطة (أو حتى 1) يمر ويفتح fork/شات ويُهدر الوقت حتى يرفضه الخادم بـ CREDIT_EXHAUSTED. والأسوأ: رصيد `0` كان يُفسَّر ككوكيز فاسدة → مسار تجديد جلسة → عند الفشل حظر `auth_failed` لمدة **30 دقيقة فقط** بدل تبريد 29 ساعة، فيُعاد اختيار الحساب الفارغ مراراً. حلقة `send_message_with_auto_account_failover` تحجز الحساب وترسل بدون أي بوابة رصيد.

> **العقد المطلوب:** قبل لمس الشات أو إرسال أي حرف: فحص `check_balance`. لو الرصيد `< 100` → **لا fork ولا شات إطلاقاً** → `mark_account_cooldown(29h)` فوراً → إرجاع `LOW_BALANCE` → حلقة الـ failover تتخطاه **بصمت** للحساب التالي حتى تجد حساباً بـ 100 نقطة كاملة.

- [x] **`[TSK-3101]`** إضافة `min_preflight_balance: int = 100` إلى `BridgeConfig` كعتبة الحد الأدنى القابلة للضبط. — دليل: 83/83 PASS + Gate Exit 0 (0.396s).
- [x] **`[TSK-3102]`** بوابة الرصيد المسبقة في `send_message_and_make_public`: تفسير دلالات `check_balance` الثلاث (`>=0` رصيد فعلي / `-2` جلسة منتهية / `-1` فشل شبكة)؛ رصيد فعلي `< 100` → `mark_account_cooldown(cooldown_hours=29)` + إرجاع `(None, "LOW_BALANCE", ...)` **قبل** أي fork أو شات أو إهدار وقت. — دليل: 83/83 PASS + Gate Exit 0 (0.396s).
- [x] **`[TSK-3103]`** مسار تجديد الجلسة: بعد نجاح `refresh_cookies_on_401` يُعاد فحص الرصيد بالكوكيز الجديدة — لو `< 100` → تبريد 29h + `LOW_BALANCE` (سد ثغرة "جلسة متجددة برصيد فارغ"). — دليل: 83/83 PASS + Gate Exit 0 (0.396s).
- [x] **`[TSK-3104]`** حلقة `send_message_with_auto_account_failover`: معالجة `LOW_BALANCE` بتخطٍ **صامت** (`continue` للحساب التالي) — بدون إشعار مزعج للمستخدم وبدون حظر `auth_failed` الخاطئ ذي الـ 30 دقيقة. — دليل: 83/83 PASS + Gate Exit 0 (0.396s).
- [x] **`[TSK-3105]`** حزمة حراسة `tests/test_p13_preflight_balance.py`: العتبة 100 في BridgeConfig، وجود البوابة قبل الإرسال، التبريد 29h عند الرصيد المنخفض، إرجاع LOW_BALANCE بدون fork، إعادة الفحص بعد التجديد، التخطي الصامت في الـ failover، وعدم معاقبة فشل الشبكة (-1) بالتبريد. — دليل: 83/83 PASS + Gate Exit 0 (0.396s).
- [x] **`[TSK-3106]`** تحديث خريطة `scripts/rebuild_refactor.py` + إعادة توليد `bridge_refactor/` بتطابق بايت. — دليل: 83/83 PASS + Gate Exit 0 (0.396s).
- [x] **`[TSK-3107]`** تحديث ملفات البروتوكول: `PROGRESS.md` (إغلاق التاسكات بأدلة) + `SESSION_LOG.md` (DEC-009) + `V3_RESUME_SESSION.md` + `TRACEABILITY_MATRIX.md` + `README.md`. — دليل: هذا الـ commit.

---

## 🔀 P14 — GitHub Upsert Sync (S33): مقارنة بالمحتوى + حارس الحذف المرآتي + كشف جذر ذكي في `04_upload_to_Fable_github.py`

> **جذور العلة (3 مؤكدة بمراجعة P14-A):**
> 1. **كشف جذر الأرشيف ضعيف:** `get_source_root` ينزل مستوى واحداً فقط ويُستدعى **قبل** clone الريبو — أرشيف بمسار داخلي متداخل يُنسخ بمسار خاطئ داخل المستودع، فيرى Git الملفات القائمة `A` (جديد كلياً) + `D` (محذوف) بدلاً من `M` (معدل).
> 2. **الحذف المرآتي أعمى:** `sync_tree(mirror_delete=True)` بلا أي حارس نسبة — أرشيف ناقص بـ 4 ملفات مسح 69 ملفاً قائماً من الريبو (حالة saray2and2 الموثقة).
> 3. **نسخ أعمى بالمحتوى:** `shutil.copy2` يكتب فوق الوجهة حتى لو المحتوى مطابق بايت-ببايت أو الفرق نهايات سطور فقط (CRLF↔LF) — ضجيج `M` كاذب وفقدان تتبع.

> **العقد المطلوب (Upsert Mode):** الملف الموجود في الريبو وتغيّر محتواه ➔ `✏️ M` وليس `➕ A`؛ الملف المطابق (ولو بفرق نهايات سطور فقط) لا يُلمس؛ أرشيف جزئي لا يحق له مسح المستودع.

- [x] **`[TSK-3201]`** ثوابت حارس الحذف: `DELETE_GUARD_ENABLED = True` + `DELETE_GUARD_MAX_DELETE_RATIO = 0.5` — لو الحذف المخطط يتجاوز النسبة من ملفات الريبو ➔ أرشيف جزئي ➔ تعطيل الحذف لهذه الدورة فقط مع تحذير صريح. — دليل: 99/99 PASS + Gate Exit 0 (0.473s).
- [x] **`[TSK-3202]`** كشف جذر ذكي `detect_best_source_root(extract_dir, repo_dir)`: يمسح مرشحي الجذور حتى عمق 3 ويختار الأعلى تطابقاً بأسماء الملفات النسبية مع الريبو المستنسخ (Repo-Anchored)، مع fallback للسلوك القديم؛ ونقل استدعاء كشف الجذر في `process_single_tar` إلى **بعد** `git clone`. — دليل: 99/99 PASS + Gate Exit 0 (0.473s) + test_13/test_15.
- [x] **`[TSK-3203]`** نسخ بالمقارنة (Upsert Copy) داخل `sync_tree`: الوجهة الموجودة تُقارن بالمحتوى — مطابقة بايت-ببايت (`filecmp.cmp shallow=False`) أو مطابقة بعد توحيد نهايات السطور (CRLF→LF، ≤5MB) ➔ تخطي النسخ والإبقاء على نسخة الريبو؛ غير ذلك ➔ كتابة فوقها (تظهر `M` الصحيحة). — دليل: 99/99 PASS + Gate Exit 0 (0.473s) + test_06/07/08.
- [x] **`[TSK-3204]`** حارس الحذف المرآتي داخل `sync_tree`: تجميع قائمة `would_delete` كاملة أولاً، ثم تطبيق الحارس (نسبة الحذف > 50% من ملفات الريبو ➔ إلغاء الحذف بالكامل مع تحذير صريح) قبل أي `os.remove` — الحماية الشرطية القائمة (`.git`/`.agents`/`.github`/`.gitignore`) تبقى كما هي. — دليل: 99/99 PASS + Gate Exit 0 (0.473s) + test_10 (سيناريو saray2and2: 73 ملف ريبو + أرشيف 4 ملفات = صفر حذف).
- [x] **`[TSK-3205]`** حزمة حراسة `tests/test_p14_upsert_sync.py` (16 اختباراً): اختبارات نصية (وجود الثوابت والحارس وترتيب كشف الجذر بعد clone) + اختبارات وظيفية بأشجار ملفات مؤقتة (مطابق لا يُنسخ، CRLF-فقط لا يُنسخ، معدل يُكتب فوقه، أرشيف جزئي لا يحذف، أرشيف كامل يحذف الغائب، كشف الجذر المتداخل الصحيح، حماية الأسرار سليمة). — دليل: 16/16 PASS ضمن 99/99.
- [x] **`[TSK-3206]`** تحديث ملفات البروتوكول: `PROGRESS.md` (إغلاق بأدلة + Header S33) + `SESSION_LOG.md` (DEC-010) + `V3_RESUME_SESSION.md` + `TRACEABILITY_MATRIX.md` + `README.md`. — دليل: هذا الـ commit.

---

## 🚀 P15 — إصدار 01.27 + استقلال محرك كوين + التدقيق الشامل (S34): Version Bump + Qwen Engine Module + Full Deep Audit

> **طلب المالك (3 محاور):** (1) إصدار جديد `01.27` ببانر جديد وتحديث كل المراجع. (2) نقل منظومة ومحرك كوين (Qwen.ai Direct) بالكامل من `04_upload_to_Fable_github.py` إلى موديول مستقل ومتكامل دون إسقاط أي تفصيلة (الإعدادات وسلسلة الموديلات، محرك السباق `_qwen_worker` + `qwenguest_worker` + `race_accounts` + شريط التقدم الملون، التجديد التلقائي `auto_refresh_qwen_account` + حفظ الفائز `_save_qwen_winner_cookies` تحت `_QWEN_FILE_LOCK`، واستخراج الرد `generate_ai_summary`). (3) مراجعة وتدقيق شامل Zero-Regression: الستريم والطباعة الدفعة الواحدة، زر المعاينة الحية + make_public المبكر، ألوان وتنسيق الأزرار، حماية P13 (رصيد < 100 ➔ تبريد 29h + تخطٍ صامت) و P14 (Upsert + Delete Guard)، وتوثيق docs بالكامل.

- [x] **`[TSK-3301]`** ترقية الإصدار `01.26 ➔ 01.27`: إنشاء `01.27_telegram_gen_bridge.py` ببانر جديد (يعكس P12+P13+P14) و`BUILD_VERSION = "01.27"`، وتحديث كل المراجع في `scripts/hadith_sijil.py` و`scripts/rebuild_refactor.py` و`scripts/generate_docs.py` وكل ملفات `tests/`، وإعادة توليد `bridge_refactor/` بتطابق بايت من 01.27. — دليل: 01.27 = 6168 سطراً (بانر +3 أسطر ➔ خريطة PARTS مزاحة) + `test_refactor_parity` PASS + صفر مرجع `01.26` في scripts/tests + 115/115 PASS.
- [x] **`[TSK-3302]`** استخراج موديول `qwen_engine.py` المستقل: نقل كل مكونات كوين (AI_MODEL_CHAIN، AI_MAX_DIFF_CHARS، AI_MIN_VALID_CHARS، AI_RACE_ACCOUNTS، AI_FALLBACK_COMMIT_MSG، QWEN_ACCOUNTS_FILE + DEFAULT_QWEN_ACCOUNTS + load_or_create_qwen_accounts، SPECTRUM_256 + get_rainbow_color + get_second_rainbow_color + render_seconds_progress_bar، _QWEN_FILE_LOCK + LAST_AI_* + _reset_ai_race_state + _save_qwen_accounts + auto_refresh_qwen_account، _qwen_time_left + _qwen_worker (هيدرات Dalvik/Android 15 + SSE + stop_event) + qwenguest_worker + _save_qwen_winner_cookies + race_accounts + _select_race_indices + _call_qwen_ai_direct + generate_ai_summary) مع حقن log_message عبر واجهة configure، و`04_upload_to_Fable_github.py` يستورد منه بتوافق تام (نفس الأسماء العامة). — دليل: `qwen_engine.py` = 946 سطراً بنقل حرفي، اكتمال 27/27 مكوناً مثبت آلياً، `04` أصبح 1234 سطراً يستورد 16 اسماً + `qwen_engine.configure(log_func=log_message)` + قراءة حالة الفائز الحية عبر `qwen_engine.LAST_AI_*` (وليس from-import المجمِّد) — commit `706f3aa`.
- [x] **`[TSK-3303]`** التدقيق الشامل Zero-Regression: (أ) الستريم — `stream=True` + `iter_lines` + طباعة الرد كاملاً دفعة واحدة بدون طباعة حرف-بحرف؛ (ب) المعاينة الحية — `make_public` مبكر + زر «🌐 تابع المشروع لايف» في كل المسارات (أول ثانية + استئناف + fork)؛ (ج) الأزرار — `make_inline_keyboard` بقائمة styles البيضاء (primary/success/danger) وأزرار URL نظيفة؛ (د) P13 — البوابة قبل fork/شات + تبريد 29h + تخطٍ صامت؛ (هـ) P14 — Upsert + Delete Guard 50% + كشف الجذر بعد clone. — دليل: سكربت تدقيق آلي 25 فحصاً = 25/25 PASS فعلي (فحص واحد أظهر ❌ زائف لاختلاف نص الزر الحرفي — الزر الحقيقي `🌐 ⚡ فتح المعاينة ومتابعة البناء لايف ↗️` موجود في 01.27 سطر 3540).
- [x] **`[TSK-3304]`** حزمة حراسة `tests/test_p15_qwen_engine.py`: الموديول يستورد بأمان، اكتمال المكونات المنقولة 100% (كل الدوال والثوابت والقفل)، `04` يستورد من الموديول ولا يحتفظ بنسخ مكررة من دوال كوين، توافق الأسماء العامة، وعدم كسر أي اختبار قائم (69+ اختبار P1..P14 على 01.27). — دليل: 16/16 PASS ضمن 115/115 (اكتمال 27 مكوناً + عقد سلسلة الموديلات 30s + هيدرات Dalvik/Android 15 + SSE stop_event + حقن اللوجر + توافق أسماء 04 + بانر 01.27).
- [x] **`[TSK-3305]`** تشغيل كامل الاختبارات + بوابة `python3 scripts/hadith_sijil.py` بـ Exit Code 0 وتقديم تقرير التدقيق الختامي الشامل. — دليل: pytest ➔ 115 passed + Gate ➔ 115/115 PASS (0.440s) Exit Code 0 والإصدار المعتمد `01.27_telegram_gen_bridge.py` + التقرير الختامي سُلِّم للمالك.
- [x] **`[TSK-3306]`** تحديث ملفات البروتوكول: `PROGRESS.md` (إغلاق بأدلة + Header S34) + `SESSION_LOG.md` (DEC-011) + `V3_RESUME_SESSION.md` + `TRACEABILITY_MATRIX.md` + `README.md`. — دليل: هذا الـ commit (المراجع التاريخية لـ 01.26 في أدلة TSK القديمة وسجلات الجلسات أُبقيت كما هي عمداً).

---

## 🌍 P16 — النشر العام المبكر Early Make-Public (S35): المشروع Public فور التقاط الـ pid

> **طلب المالك:** زر «المعاينة الحية» كان بيدي 404 لأن المشروع بيتعمل Public متأخراً — المطلوب نشره عاماً فور التقاط أول project id في كل المسارات.

- [x] **`[TSK-3401]`** إصدار `01.28_telegram_gen_bridge.py` + دالة `_early_make_public` داخل `send_message_and_make_public`: استدعاء `make_public` بخيط daemon منفصل (Fire-and-Forget) فور التقاط الـ pid في المسارات الثلاثة: (أ) `pid_capture_callback` أثناء البث، (ب) استئناف `carry_pid`، (ج) مسار fork بالـ URL. — دليل: `tests/test_p16_early_public.py` = 9/9 PASS.
- [x] **`[TSK-3402]`** حراسات السلامة: dedup لكل pid (مرة واحدة فقط)، تجاهل sentinels (`__INVALID_PROJECT__`)، snapshot معزول للكوكيز، البانر و`BUILD_VERSION = "01.28"`. — دليل: TestP16EarlyMakePublic اختبارات 05–09 PASS.

---

## 🛡️ P17 — التصليب التشغيلي Hardening (S36): تجديد الجلسة المنتهية + بوابة الرصيد أثناء الشات + دعم الجروبات + نظافة المستودع

> **طلب المالك:** إصلاحات حرجة من التشغيل الحي: الجلسة المنتهية كانت بتضيع المحاولة، الرصيد كان بيتفحص قبل الإرسال فقط، والبوت مكانش بيرد في الجروبات.

- [x] **`[TSK-3501]`** بوابة الجلسة المنتهية `SESSION_EXPIRED`: تجديد فوري للحساب (auto-refresh) بدل إسقاط المحاولة. — دليل: `TestExpiredSessionGate` PASS.
- [x] **`[TSK-3502]`** بوابة الرصيد أثناء الشات (Mid-Chat Balance Gate): كشف `CREDIT_EXHAUSTED` داخل حلقة polling وليس قبل الإرسال فقط. — دليل: `TestMidChatBalanceGate` PASS.
- [x] **`[TSK-3503]`** دعم الجروبات: `is_chat_allowed` يقبل group/supergroup chat ids السالبة مع الحفاظ على قائمة السماح. — دليل: `TestGroupChatSupport` PASS.
- [x] **`[TSK-3504]`** تكامل كوين للـ commit messages + نظافة المستودع: `.pytest_cache/` و `bridge_bot.log` غير متتبعين في git (`git rm --cached` + `.gitignore`). — دليل: `TestQwenCommitIntegration` + `TestGeneratedFilesUntracked` = 27/27 PASS إجمالي P17.

---

## ⛳ P18 — الوقف الفوري عند تغيّر مؤشر النشاط الحي (S37): Deep Thinking / Tasks Remaining Activity-Stop

> **طلب المالك (نصاً):** «لو غيرت مهام وقف مش تكمل — Deep Thinking / Tasks Remaining لما يكون ده اتغير وقف فوراً». أي تغيّر في المؤشر أثناء المتابعة = وقف فوري، مفيش أي تكملة على مهام اتغيرت.

- [x] **`[TSK-3601]`** إصدار `01.29_telegram_gen_bridge.py` ببانر P18 و`BUILD_VERSION = "01.29"` و`BUILD_PARENT_BASELINE_SHA256 = "0128_p17_hardening_baseline"`. — دليل: بانر السطر 4–6 + test_04_build_version_bumped PASS.
- [x] **`[TSK-3602]`** `extract_activity_signature`: استخراج بصمة المؤشر من صفحة `/agents?id=PID` — كشف Deep Thinking (3 صيغ markers) + عدد Tasks Remaining (regex بأرقام قبل/بعد النص + fallback نصي بدون رقم = -1) + علم `active`. — دليل: `TestExtractActivitySignature` PASS.
- [x] **`[TSK-3603]`** `fetch_project_activity_signature`: جلب حي بـ curl_cffi (chrome120) مع إرجاع `None` عند أي فشل شبكة/HTTP حتى لا يؤثر إطلاقاً على حلقة المتابعة. — دليل: test فشل الجلب يُتجاهل PASS.
- [x] **`[TSK-3604]`** `should_stop_on_activity_change` — قاعدة الوقف الفوري: (1) المؤشر اختفى بعد نشاط ➔ وقف `activity-indicator-disappeared`؛ (2) **أي تغيّر في tasks_remaining — زيادة أو نقصان — ➔ وقف `tasks-remaining-changed` (المهام اتغيرت = مفيش تكملة)**؛ (3) تقلّب deep_thinking ➔ وقف `deep-thinking-changed`؛ (4) لا baseline نشط ➔ لا قرار. — دليل: `TestShouldStopOnActivityChange` (يشمل test_03_tasks_decreased_also_stops) PASS.
- [x] **`[TSK-3605]`** التكامل في حلقة polling داخل `send_message_and_make_public`: التقاط baseline قبل الحلقة ➔ فحص المؤشر كل دورة **قبل** جلب الرسائل ➔ عند الوقف: log تحذيري + `final_status = "COMPLETED"` + `break` فوري. — دليل: `TestPollingLoopIntegration` PASS.
- [x] **`[TSK-3606]`** مواءمة كاملة: تحديث كل مراجع `01.28 ➔ 01.29` في `scripts/` + `tests/`، إعادة توليد `bridge_refactor/` بتطابق بايت من 01.29، بوابة `hadith_sijil.py` = **171/171 PASS Exit Code 0**، وتحديث منظومة التوثيق (هذا الملف + SESSION_LOG + V3_RESUME + MATRIX + CATALOG + README). — دليل: Gate 171/171 (0.532s) + هذا الـ commit.

---

## 📋 P19 — نسخ إعدادات مشروع آخر Copy Project Settings (S38): إصدار 01.30 + الترقيم التسلسلي التلقائي

> **طلب المالك (DEFERRED-001 سابقاً):** زر «📋 نسخ إعدادات من مشروع آخر» عند فتح رابط/Project ID غير محفوظ — ينسخ إعدادات GitHub (المستودع + الفرع + التوكن) والموديل وبرومبت الاستئناف من مشروع محفوظ قائم إلى مشروع جديد، مع توليد اسم تسلسلي تلقائي للأسماء المكررة («الحج 1» ➔ «الحج 2»).
> **⚠️ قاعدة المالك المحفوظة حرفياً في 01.30 (P18):** «لو غيرت مهام وقف مش تكمل — Deep Thinking / Tasks Remaining لما يكون ده اتغير وقف فوراً» — الدوال الثلاث (`extract_activity_signature` سطر 1338 / `fetch_project_activity_signature` سطر 1365 / `should_stop_on_activity_change` سطر 1390) + التكامل في حلقة polling (سطر 1990) منقولة بتطابق حرفي إلى 01.30 ومحروسة بـ 20 اختبار P18 تعمل مباشرة على 01.30.

- [x] **`[TSK-3701]`** إصدار `01.30_telegram_gen_bridge.py` ببانر P19 و`BUILD_VERSION = "01.30"` و`BUILD_PARENT_BASELINE = "01.29"`. — دليل: `test_p19::TestP19VersionBump` PASS + كل ميزات P18 (activity-stop) حية حرفياً في 01.30 (20/20 اختبار P18 على 01.30).
- [x] **`[TSK-3702]`** `generate_sequential_project_name`: فصل الرقم الذيلي عن الجذر، فحص كل المشاريع المعروفة، وإرجاع الجذر + (أعلى رقم مستخدم + 1) — جذر غير مستخدم يُعاد كما هو («الحج 1» موجود ➔ «الحج 2»). — دليل: `TestSequentialProjectName` PASS.
- [x] **`[TSK-3703]`** `copy_project_settings_to_new_project`: قراءة إعدادات المصدر من `ProjectRegistry` (التوكن من مخزن المشروع السري فقط `allow_env_fallback=False` — منع تسرب أسرار البيئة)، إنشاء مفتاح جديد `prj_<uuid>` + اسم تسلسلي، `finalize_new_project_setup` بكامل حقول GitHub، و`upsert_project_identity` عند وجود pid. — دليل: `TestCopyProjectSettings` PASS.
- [x] **`[TSK-3704]`** واجهة تيليجرام: زر «📋 نسخ إعدادات من مشروع آخر» في `build_unbound_resume_keyboard` + لوحة `build_copy_settings_source_keyboard` (أزرار `cpysrc:<key>` + رجوع) + `format_copied_settings_summary` + الـ callbacks الثلاثة (`cmd:resume_copy_settings` بحارس حالة، `cmd:resume_copy_back`، `cpysrc:` ➔ نسخ + انتقال لـ `AWAITING_CONT_PROMPT`). — دليل: `TestCopySettingsKeyboard` + `TestCopiedSettingsSummary` + `TestHandlersIntegration` PASS.
- [x] **`[TSK-3705]`** حزمة حراسة `tests/test_p19_copy_settings.py` (24 اختباراً — 6 مجموعات). — دليل: 24/24 PASS ضمن 195/195.
- [x] **`[TSK-3706]`** مواءمة كاملة: تحديث كل مراجع `01.29 ➔ 01.30` في `scripts/` + `tests/` (صفر مرجع متبقٍ)، إعادة توليد `bridge_refactor/` بتطابق بايت من 01.30، بوابة `hadith_sijil.py` = **195/195 PASS Exit Code 0 (0.595s)**، وتحديث منظومة التوثيق (هذا الملف + SESSION_LOG + V3_RESUME + README). — دليل: Gate 195/195 + هذا الـ commit.
