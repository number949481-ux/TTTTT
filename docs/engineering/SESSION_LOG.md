# 📝 سجل الجلسات والقرارات المعمارية (SESSION_LOG.md)

> **المشروع:** Genspark Multi-Project WebApp Bridge System  
> **نوع التوثيق:** سجل تراكمي زمني لكافة الجلسات والقرارات المعمارية المعتمدة  

---

## 📌 سجل تسلسل الإصدارات وتوثيق المسارات (Version History & Evolution)

| الإصدار | الحالة | الوصف وسبب الانتقال |
|:---:|:---:|---|
| **`01.15`** | ✅ مكتمل | التأسيس الأولي لمعمارية الـ Bridge وربط مشاريع الويب. |
| **`01.16` - `01.17`** | 🔄 مدمج | إصدارات تطويرية وسيطة تم دمج تحسيناتها واستقرارها داخل `01.18`. |
| **`01.18`** | ✅ مكتمل | معمارية ربط إعدادات المشاريع وفحص GitHub ومصفوفة TSK-101 إلى TSK-702. |
| **`01.19`** | ✅ مكتمل | تثبيت عقود التخزين والربط مع الحسابات المتعددة. |
| **`01.20` - `01.23`** | 🔄 مدمج | جولات تطوير متتالية لتحسين الأداء وتجربة المستخدم وعزل مسارات الموديلات تم تتويجها في `01.24`. |
| **`01.24`** | ✅ مكتمل | دعم أزرار الفروع بنقرة واحدة (1-Click UI)، كتم إشعارات الأرشيف D-002، دمج عقود الموديلات الـ 5، واجتياز 24/24 اختبار وحدة. |
| **`01.25`** | ⭐ **نشط ومكتمل** | **الإصدار النشط المعتمد:** المعاينة الحية الفورية (P7-A) عبر SSE Callback في أول ثانية، دورة الرسالة المتطورة (Single Evolving Message)، كتم الإشعارات الزائدة، واجتياز 31/31 اختبار وحدة. |
| **`01.25 — S28`** | ✅ مكتمل | **توحيد Single-File Doctrine (P8):** دمج `runtime/model_runtime.py` (CONTRACTS + is_protected + apply_contract) داخل `01.25` كـ SSOT وحيد، تحويل imports الاختبارات و`generate_docs.py` للاستيراد من `01.25`، حذف `runtime/` نهائياً، إصلاح `import re` المفقود في `hadith_sijil.py`، واجتياز 32/32 اختبار — Gate Exit Code 0 (commit `0ec245e`). |
| **`01.25 — S29`** | ✅ مكتمل | **إصلاح البث الحقيقي (P9 — True SSE Streaming):** جذر العلة كان في المحرك `01.02`: طلب `ask_proxy` بدون `stream=True` + قراءة `r.text.splitlines()` التي تحجب كامل الـ SSE حتى نهاية التوليد، فكان زر المعاينة الحية يظهر بعد الاكتمال بدل الثانية الأولى. الإصلاح: `stream=True` + `iter_lines()` لحظية + `r.close()` آمن، مع 3 اختبارات حراسة جديدة (`TestTrueSSEStreamingGuard`)، واجتياز 35/35 اختبار — Gate Exit Code 0. |
| **`01.26 — S30`** | ✅ مكتمل | **أزرار Inline ملونة (P11 — Button Styles — Bot API 9.4):** ترقية البوت إلى `01.26_telegram_gen_bridge.py` والمحرك إلى `01.03Genspark_claude-opus-5-code.py` (baseline جديد: `01.25` مجمّد). إضافة `ALLOWED_BUTTON_STYLES = {primary, success, danger}` (القيم الرسمية الوحيدة في Bot API 9.4) مع تنقية مركزية في `make_inline_keyboard` تحذف أي قيمة غير رسمية لتجنب `400 invalid button style`. تلوين الأزرار الاستراتيجية: معاينة حية = أزرق، مكتمل/كمل الآن = أخضر، إلغاء = أحمر، مشروع جديد = أزرق. 10 اختبارات حراسة جديدة (`tests/test_p11_button_styles.py`) — اجتياز 45/45 اختبار — Gate Exit Code 0 (0.249s). |
| **`01.27 — S34`** | ⭐ **نشط ومكتمل** | **إصدار 01.27 + استقلال محرك كوين (P15):** ترقية البوت إلى `01.27_telegram_gen_bridge.py` ببانر جديد يعكس P12+P13+P14 (baseline جديد: `01.26` مجمّد). نقل منظومة Qwen.ai Direct بالكامل من `04_upload_to_Fable_github.py` إلى موديول مستقل `qwen_engine.py` (27/27 مكوناً، نقل حرفي، حقن لوجر عبر `configure`، حالة فائز حية عبر `qwen_engine.LAST_AI_*`). تدقيق شامل Zero-Regression على 6 محاور = 25/25. 16 اختبار حراسة جديد (`tests/test_p15_qwen_engine.py`) — اجتياز 115/115 اختبار — Gate Exit Code 0 (0.440s). |

---

## 🏛️ أرشيف القرارات المعمارية المعتمدة (Architectural Decisions Log)

### [DEC-001] — اعتماد مبدأ الـ Single-File Doctrine للمحرك والبوت
* **القرار:** دمج عقود الموديلات وقواميس التحويل وآليات الاتصال محلياً داخل ملفات المشروع (`01.25_telegram_gen_bridge.py` و `01.02Genspark_claude-opus-5-code.py`).
* **السبب:** ضمان سهولة النقل والتشغيل كـ Self-Contained Unit دون التعرض لأخطاء مسارات الاستيراد أو فقدان ملفات خارجية.
* **الحالة:** مُعتمد وفعال.

### [DEC-002] — كتم رسائل سياسة الأرشيفات في شات التيليجرام
* **القرار:** تعديل دالة `describe_archive_delivery` لإرجاع مسار الملف محلياً بدون إرسال رسائل نصية فنية مزعجة في شات البوت.
* **السبب:** نظافة واجهة المستخدم وحماية خصوصية المسارات الفنية للملفات.
* **الحالة:** مُعتمد وفعال (Commit: `22bcd3d`).

### [DEC-003] — اعتماد أزرار الفروع بنقرة واحدة (1-Click Branch Selection)
* **القرار:** تحويل قائمة الفروع المكتشفة في GitHub إلى قائمة عمودية بنقاط `<code>` قابلة للنسخ المباشر + توليد أزرار Inline تفاعلية لكل فرع.
* **السبب:** تمكين المستخدم من اختيار الفرع المطلوب بضغطة زر واحدة دون الحاجة للكتابة أو النسخ اليدوي.
* **الحالة:** مُعتمد وفعال (Commit: `b8c3358`).

### [DEC-004] — اعتماد المعمارية المزدوجة للتوثيق (`docs/engineering/` + `docs/tests/`)
* **القرار:** فصل وثائق التخطيط والمعمارية في `docs/engineering/` عن وثائق وكتالوجات وتقارير الاختبارات في `docs/tests/`، وجعل `docs/engineering/PROGRESS.md` هو الـ SSOT الوحيد.
* **السبب:** تنظيم العمل البرمجي وفق معايير Enterprise ومنع تشتت أو تضارب التوثيق.
* **الحالة:** مُعتمد وفعال.

### [DEC-005] — اعتماد معمارية المعاينة الحية الفورية ودورة الرسالة المتطورة (P7-A)
* **القرار:** التقاط حدث `project_start` في الثانية الأولى من تدفق الـ SSE واستدعاء `on_project_start_callback` لإرسال زر URL Button فوري، وتعديل نفس الرسالة لاحقاً عند اكتمال المشروع إلى زر المشروع المكتمل (`edit_telegram_message_text`).
* **السبب:** منح المستخدم تجربة فورية لمتابعة التوليد الحي وتفادي إغراق الشات بالرسائل المكررة (`Single Evolving Message`).
* **الحالة:** مُعتمد وفعال في 01.25 (اكتمل فعلياً بإصلاح DEC-007 في S29).

### [DEC-006] — تنفيذ Single-File Doctrine v16: دمج `runtime/` داخل `01.25` (S28)
* **القرار:** نقل كامل منطق عقود الموديلات (`CONTRACTS`, `is_protected`, `apply_contract`) من حزمة `runtime/model_runtime.py` إلى داخل `01.25_telegram_gen_bridge.py` مباشرة بعد `MODEL_ALIASES`، ثم حذف `runtime/` نهائياً، مع تحويل كل المستهلكين (اختبارات + `generate_docs.py`) للاستيراد من `01.25` كـ SSOT وحيد.
* **السبب:** تطبيق مبدأ DEC-001 (Self-Contained Unit) وإزالة ازدواجية مصدر الحقيقة بين `runtime/` و `01.25` التي رصدتها مراجعة CEV-TG.
* **الأدلة:** commit `0ec245e` — `python scripts/hadith_sijil.py` ➔ 32/32 PASS, Exit Code 0 (قبل وبعد حذف `runtime/`).
* **الحالة:** مُعتمد وفعال.

### [DEC-007] — اعتماد البث الحقيقي True SSE Streaming في المحرك (S29)
* **القرار:** فتح طلب `ask_proxy` في `01.02Genspark_claude-opus-5-code.py` بـ `stream=True` واستهلاك الاستجابة عبر `r.iter_lines()` اللحظية سطراً بسطر (مع فك ترميز bytes آمن وإغلاق `r.close()` في كل مسارات الخروج)، وتحريم `r.text` نهائياً في مسار الـ SSE.
* **السبب:** في `curl_cffi` قراءة `r.text` بدون بث تحجب الاستجابة كاملة حتى إغلاق الخادم للاتصال، ما جعل حدث `project_start` وزر المعاينة الحية (P7-A/DEC-005) يظهران بعد اكتمال التوليد بالكامل بدلاً من الثانية الأولى.
* **الحراسة:** 3 اختبارات جديدة في `tests/test_p7_live_preview.py` (`TestTrueSSEStreamingGuard`): إلزام `stream=True`، تحريم `r.text.splitlines()`، ومحاكاة بث تثبت انطلاق الـ callback قبل استهلاك أي chunk.
* **الأدلة:** `python scripts/hadith_sijil.py` ➔ 35/35 PASS, Exit Code 0 (0.252s).
* **الحالة:** مُعتمد وفعال.


### [DEC-008] — استئناف نفس المشروع بعد انقطاع البث + مهلة الخمول + الطباعة الكاملة (S31 / P12)
* **القرار:** (1) مهلة `ask_proxy` تصبح tuple `(connect, read)` مع `stream=True` — داخل curl_cffi تتحول إلى مهلة خمول (LOW_SPEED_TIME) لا تقطع التوليد الطويل النشط. (2) عند انقطاع البث مع project_id حي يرجع المحرك `__STREAM_INTERRUPTED__` + الـ pid، ويحوّله البوت إلى `RUNNING` ثم polling عبر `fetch_project_messages` على نفس الـ pid حتى الاكتمال. (3) نمط `carry_pid` في `send_message_and_make_public`: أي إعادة محاولة تستأنف نفس المشروع — ممنوع fork/شات جديد بعد الانقطاع. (4) إلغاء البث الحي للترمنال: الرد يُطبع كاملاً دفعة واحدة مع `⏱️ اخد X ثانية` (ticket_file اللحظي باقٍ). (5) زر المعاينة الحية يُرسل فوراً في مسارات الاستئناف/الـ fork أيضاً.
* **السبب:** لوج المالك أظهر TIMEOUT بلا سبب على توليدات طويلة نشطة، وإنشاء chat id جديد تماماً بعد كل انقطاع بدل استكمال نفس المشروع.
* **مراجعة P12-E الإضافية:** `return []` صريح في مسار خطأ `fetch_project_messages` (كانت None ضمنياً)، وحلقة polling تقرأ آخر رسالة `assistant` فقط (كانت تقرأ آخر رسالة أياً كانت — خطر COMPLETED كاذب بنص رسالة المستخدم).
* **الحراسة:** `tests/test_p12_resume_same_project.py` (13 اختباراً) + تحديث test_08 في `test_p7_live_preview.py`.
* **الأدلة:** `python scripts/hadith_sijil.py` ➔ 69/69 PASS, Exit Code 0 (0.375s). Push/PR بانتظار تفويض GitHub.
* **الحالة:** مُعتمد وفعال.

### [DEC-009] — بوابة فحص الرصيد المسبقة Pre-Flight Balance Check (S32 / P13)
* **القرار:** قبل لمس الشات أو إرسال أي حرف يُفحص رصيد الحساب عبر `check_balance`. رصيد فعلي < `min_preflight_balance` (100 نقطة، قابلة للضبط في `BridgeConfig`) → `mark_account_cooldown(29h)` فوري + إرجاع `LOW_BALANCE` بدون أي fork أو شات، وحلقة `send_message_with_auto_account_failover` تتخطاه **بصمت** (`continue`) للحساب التالي حتى تجد حساباً صالحاً.
* **السبب:** الفحص القديم كان يقبل أي رصيد > 0 — حساب بـ 20 نقطة يفتح fork/شات ويهدر الوقت حتى يرفضه الخادم؛ ورصيد 0 كان يُفسَّر ككوكيز فاسدة فيأخذ حظر `auth_failed` لمدة 30 دقيقة فقط ويُعاد اختياره وهو فارغ.
* **دلالات `check_balance` المحترمة:** `>=0` رصيد فعلي (يُحكم عليه) / `-2` جلسة منتهية (مسار تجديد) / `-1` فشل شبكة (**لا عقوبة**). وبعد نجاح `refresh_cookies_on_401` يُعاد فحص الرصيد بالكوكيز الجديدة لسد ثغرة "جلسة متجددة برصيد فارغ".
* **الحراسة:** `tests/test_p13_preflight_balance.py` (14 اختباراً): العتبة، ترتيب البوابة قبل fork/send_chat، التبريد 29h، إعادة الفحص بعد التجديد، عدم معاقبة فشل الشبكة، التخطي الصامت بدون إشعارات وبدون حظر 1800 ثانية الخاطئ، وتزامن bridge_refactor.
* **الأدلة:** `python scripts/hadith_sijil.py` ➔ 83/83 PASS, Exit Code 0 (0.396s).
* **الحالة:** مُعتمد وفعال.

### [DEC-010] — Upsert Sync لرافع GitHub: مقارنة بالمحتوى + حارس الحذف + كشف جذر ذكي (S33 / P14)
* **القرار:** إصلاح ثلاثي في `04_upload_to_Fable_github.py`: (1) **Upsert Copy** في `sync_tree` — قبل النسخ تُقارن الوجهة الموجودة بالمحتوى (`filecmp.cmp shallow=False` ثم مطابقة بعد توحيد CRLF→LF للملفات ≤5MB)؛ المطابق لا يُلمس إطلاقاً (لا `M` كاذب)، والمختلف يُكتب فوقه فيظهر `✏️ M` الصحيح بدل `➕ A`. (2) **حارس الحذف المرآتي** — تُجمَّع قائمة `would_delete` كاملة أولاً؛ لو نسبتها من ملفات الريبو تتجاوز `DELETE_GUARD_MAX_DELETE_RATIO` (50%) يُلغى الحذف المرآتي بالكامل لهذه الدورة مع تحذير صريح (الأرشيف الجزئي ≠ حذف مقصود). (3) **كشف جذر ذكي** `detect_best_source_root` — يُستدعى **بعد** `git clone` ويختار من مرشحي الجذور (حتى عمق 3) الأعلى تطابقاً بأسماء الملفات النسبية مع الريبو الفعلي (Repo-Anchored)، مع fallback لـ `get_source_root` القديم عند ريبو فارغ أو صفر تطابق.
* **السبب:** حالة saray2and2 الموثقة: أرشيف 4 ملفات ظهرت كلها "➕ جديد" رغم وجود `package.json` و`src/index.tsx` في الريبو (كان يجب `✏️ معدل`)، ومُسحت 69 ملفاً قائماً من الريبو. الجذور: كشف جذر أعمى بمستوى واحد قبل الاستنساخ + حذف مرآتي بلا حارس + نسخ أعمى يكسر التتبع حتى بفروق CRLF فقط.
* **الحراسة:** `tests/test_p14_upsert_sync.py` (16 اختباراً وظيفياً ونصياً) — تشمل إعادة تمثيل سيناريو saray2and2 (73 ملف ريبو + أرشيف 4 ملفات = صفر حذف) وحماية الأسرار القائمة.
* **الأدلة:** `python scripts/hadith_sijil.py` ➔ 99/99 PASS, Exit Code 0 (0.473s). ملاحظة: هذا الملف خارج نطاق `bridge_refactor/` فلا إعادة توليد مطلوبة.
* **الحالة:** مُعتمد وفعال.

### [DEC-011] — إصدار 01.27 + استقلال محرك كوين qwen_engine.py + التدقيق الشامل (S34 / P15)
* **القرار:** (1) **ترقية الإصدار 01.26 ➔ 01.27** — نسخ 01.26 المجمّد إلى `01.27_telegram_gen_bridge.py` ببانر جديد يعكس P12+P13+P14 (استئناف carry_pid، مهلة خمول ذكية، بوابة رصيد < 100 = تبريد 29h + تخطٍ صامت، طباعة دفعة واحدة + ⏱️، معاينة حية فورية) و`BUILD_VERSION = "01.27"`، مع تحديث كل المراجع في scripts/tests وإزاحة خريطة PARTS بمقدار +3 أسطر (نمو البانر) وإعادة توليد `bridge_refactor/` بتطابق بايت. (2) **استخراج محرك كوين** — نقل منظومة Qwen.ai Direct بالكامل من `04_upload_to_Fable_github.py` إلى موديول مستقل `qwen_engine.py` (946 سطراً، نقل حرفي): AI_MODEL_CHAIN (مرحلتان qwen3.8-max Thinking/Fast بمهلة 30s)، الثوابت AI_MAX_DIFF_CHARS/AI_MIN_VALID_CHARS/AI_RACE_ACCOUNTS، حسابات QWEN_ACCOUNTS_FILE + load_or_create_qwen_accounts، الطيف اللوني SPECTRUM_256 + render_seconds_progress_bar، `_qwen_worker` (هيدرات Dalvik/Android 15 + SSE + إلغاء فوري stop_event)، `qwenguest_worker` (تجاوز الضيف الموازي)، `race_accounts` (سباق FIRST_COMPLETED + شريط تقدم ملون)، `auto_refresh_qwen_account` (إعادة تسجيل عبر password_hash)، `_save_qwen_winner_cookies` تحت `_QWEN_FILE_LOCK` (كتابة ذرية tmp+os.replace)، `_call_qwen_ai_direct`، `generate_ai_summary`. حقن اللوجر عبر `configure(log_func=...)` وقراءة حالة الفائز الحية كصفة موديول `qwen_engine.LAST_AI_*` (from-import محرّم لأنه يجمّد القيمة). `04` أصبح 1234 سطراً يستورد 16 اسماً بتوافق تام. (3) **التدقيق الشامل Zero-Regression** — 25 فحصاً آلياً على 6 محاور (ستريم/معاينة/أزرار/P13/P14/P15) = 25/25 فعلياً.
* **السبب:** طلب المالك الثلاثي: بانر جديد 01.27، نقل محرك كوين لموديول مستقل ومتكامل 100% دون إسقاط أي تفصيلة مع التوافق التام، وتدقيق شامل بدون أي كسر وظيفي مع تقرير ختامي.
* **الحراسة:** `tests/test_p15_qwen_engine.py` (16 اختباراً): اكتمال 27/27 مكوناً، عقد سلسلة الموديلات (مرحلتان × 30s × Thinking/Fast)، هيدرات Dalvik/Android 15، SSE `stream=True` + `iter_lines()` + فحوص stop_event، سباق الضيف داخل نفس الـ executor، حقن اللوجر وظيفياً، توافق أسماء `04` وعدم وجود تعريفات مكررة، بانر 01.27 والمراجع.
* **الأدلة:** pytest ➔ 115 passed + `python scripts/hadith_sijil.py` ➔ 115/115 PASS, Exit Code 0 (0.440s)، الإصدار المعتمد `01.27_telegram_gen_bridge.py` — commit `706f3aa` (الكود) + هذا الـ commit (التوثيق). Push/PR بانتظار تفويض GitHub.
* **الحالة:** مُعتمد وفعال.

### [DEC-012] — النشر العام المبكر Early Make-Public (S35 / P16)
* **القرار:** إصدار `01.28_telegram_gen_bridge.py` مع دالة `_early_make_public` داخل `send_message_and_make_public`: فور التقاط أول project id يُستدعى `make_public` في خيط daemon منفصل (Fire-and-Forget) في المسارات الثلاثة: (1) `pid_capture_callback` أثناء بث SSE، (2) مسار استئناف `carry_pid`، (3) مسار fork بالـ URL. حراسات: dedup لكل pid (النشر مرة واحدة فقط)، تجاهل sentinels مثل `__INVALID_PROJECT__`، snapshot معزول للكوكيز لكل خيط.
* **السبب:** زر «المعاينة الحية» كان يعطي 404 لأن `make_public` كان يُنفَّذ متأخراً بعد اكتمال التوليد — المطلوب أن يكون المشروع Public من أول ثانية.
* **الحراسة:** `tests/test_p16_early_public.py` (9 اختبارات).
* **الأدلة:** `python scripts/hadith_sijil.py` ➔ 124/124 PASS, Exit Code 0.
* **الحالة:** مُعتمد وفعال.

### [DEC-013] — التصليب التشغيلي Hardening (S36 / P17)
* **القرار:** حزمة إصلاحات حرجة من التشغيل الحي على `01.28`: (1) **بوابة الجلسة المنتهية** — `SESSION_EXPIRED` أثناء الشات يفعّل تجديد الحساب فوراً بدل إسقاط المحاولة. (2) **بوابة الرصيد أثناء الشات** — كشف `CREDIT_EXHAUSTED` داخل حلقة polling نفسها وليس فقط في الفحص المسبق P13. (3) **دعم الجروبات** — `is_chat_allowed` يقبل chat ids السالبة (group/supergroup) مع الحفاظ على قائمة السماح. (4) **تكامل كوين لرسائل الـ commit** في مسار GitHub. (5) **نظافة المستودع** — `.pytest_cache/` و `bridge_bot.log` أُخرجا من تتبع git (`git rm --cached`) ومغطيان في `.gitignore` مع اختبار حارس يمنع عودتهما.
* **السبب:** لوجات المالك التشغيلية: جلسة منتهية كانت تحرق المحاولة، رصيد ينفد وسط التوليد بلا كشف، والبوت لا يرد في الجروبات.
* **الحراسة:** `tests/test_p17_hardening.py` (27 اختباراً — 5 مجموعات).
* **الأدلة:** `python scripts/hadith_sijil.py` ➔ 151/151 PASS, Exit Code 0.
* **الحالة:** مُعتمد وفعال.

### [DEC-014] — الوقف الفوري عند تغيّر مؤشر النشاط الحي (S37 / P18) + إصدار 01.29
* **القرار:** إصدار `01.29_telegram_gen_bridge.py` بمراقب مؤشر النشاط الحي (Deep Thinking / Tasks Remaining): (1) `extract_activity_signature` يستخرج بصمة المؤشر من صفحة `/agents?id=PID` (deep_thinking + tasks_remaining + active). (2) `fetch_project_activity_signature` جلب حي بـ curl_cffi يرجع None عند أي فشل — فشل الجلب لا يؤثر إطلاقاً على حلقة المتابعة. (3) `should_stop_on_activity_change` — قاعدة الوقف الفوري الصريحة: **أي تغيّر في tasks_remaining (زيادة أو نقصان) = المهام اتغيرت = وقف فوري بلا أي تكملة**، اختفاء المؤشر بعد نشاط = وقف، تقلّب deep_thinking = وقف؛ لا baseline نشط = لا قرار. (4) التكامل في حلقة polling: baseline قبل الحلقة ➔ فحص كل دورة قبل جلب الرسائل ➔ عند الوقف: log تحذيري + `final_status = "COMPLETED"` + `break` فوري. مواءمة كاملة: scripts/tests على 01.29 + إعادة توليد `bridge_refactor/` بتطابق بايت.
* **السبب:** طلب المالك النصي: «لو غيرت مهام وقف مش تكمل — Deep Thinking / Tasks Remaining لما يكون ده اتغير وقف فوراً».
* **الحراسة:** `tests/test_p18_activity_stop.py` (20 اختباراً — يشمل test_03_tasks_decreased_also_stops الذي يثبت أن النقصان أيضاً = وقف).
* **الأدلة:** `python scripts/hadith_sijil.py` ➔ 171/171 PASS, Exit Code 0 (0.532s). Push/PR بانتظار تفويض GitHub.
* **قرار مالك ملحق:** ميزة «نسخ إعدادات مشروع لمشروع آخر» مؤجلة رسمياً بعد P16/P17/P18 — مسجلة `DEFERRED-001` في PROGRESS.md وهي أول بند بعد اعتماد 01.29 تشغيلياً.
* **الحالة:** مُعتمد وفعال.

### [DEC-015] — نسخ إعدادات مشروع آخر Copy Project Settings (S38 / P19) + إصدار 01.30
* **القرار:** إصدار `01.30_telegram_gen_bridge.py` بتنفيذ البند المؤجل DEFERRED-001: (1) `generate_sequential_project_name` — ترقيم تسلسلي تلقائي للأسماء المكررة («الحج 1» موجود ➔ الاسم الجديد «الحج 2») بفصل الرقم الذيلي عن الجذر وأخذ أعلى رقم مستخدم + 1. (2) `copy_project_settings_to_new_project` — نسخ إعدادات GitHub (repo/branch/token من مخزن المشروع السري فقط `allow_env_fallback=False`) + الموديل + برومبت الاستئناف من مشروع محفوظ إلى مفتاح جديد `prj_<uuid>`، مع ربط الهوية `upsert_project_identity` عند وجود pid. (3) واجهة تيليجرام: زر «📋 نسخ إعدادات من مشروع آخر» في لوحة المشروع غير المحفوظ ➔ لوحة اختيار المصدر `cpysrc:<key>` ➔ ملخص الإعدادات المنسوخة ➔ انتقال مباشر لـ `AWAITING_CONT_PROMPT`.
* **قاعدة المالك المحفوظة:** ميزات P18 (الوقف الفوري عند تغيّر Deep Thinking / Tasks Remaining — «لو غيرت مهام وقف مش تكمل») منقولة بتطابق حرفي إلى 01.30، والدوال الثلاث + تكامل حلقة polling محروسة بـ 20 اختبار P18 تعمل الآن مباشرة على 01.30.
* **الحراسة:** `tests/test_p19_copy_settings.py` (24 اختباراً — 6 مجموعات).
* **الأدلة:** `python scripts/hadith_sijil.py` ➔ 195/195 PASS, Exit Code 0 (0.595s). الإصدار المعتمد `01.30_telegram_gen_bridge.py`. bridge_refactor بتطابق بايت. Push/PR بانتظار تفويض GitHub.
* **الحالة:** مُعتمد وفعال.

### [DEC-016] — الرفع REST-Only + معالجة AI Data Retention (S39 / P20) + إصدار 01.31
* **القرار:** إصدار `01.31_telegram_gen_bridge.py` بإغلاق المهام الخمس المعتمدة (Deep Thinking — Total: 5 Tasks): (1) **إزالة Git Native Sync بالكامل** — حذف `_git_native_sync_uploader` و `_generate_ai_commit_message` وأي عمليات clone/push/init؛ `_default_github_uploader` يرفع حصرياً عبر GitHub Contents REST API (GET sha ➔ مقارنة `_git_blob_sha` بايثون خالص hashlib ➔ PUT للمتغير فقط ➔ DELETE للمحذوف) مع `PROJECT_GITHUB_TOKEN_MISSING` عند غياب التوكن. (2) **كشف DATA_RETENTION** — `DATA_RETENTION_KEYWORDS` تُفحص أولاً في `detect_response_status` (أولوية قبل SESSION_EXPIRED/CREDIT_EXHAUSTED)، والحالة أُضيفت لشرط حلقة polling الرئيسية كحالة نهائية، وفي حلقة الـ failover تُعامل كنفاد رصيد: `mark_account_cooldown(29h)` + `continue` لحساب تالٍ + إعادة إرسال **نفس آخر رسالة** (بدون لمس `active_query` — لا تحويل لبرومبت الاستئناف) + تنبيه مميز `data-retention-blocked` + رسالة نهائية مميزة للمستخدم (Settings → Data Controls). (3) **تحديث الاختبارات** — تنظيف `test_p17_hardening.py` من مرجع qwen commit الملغي + إنشاء `tests/test_p20_rest_only_data_retention.py` (27 اختباراً: 8 REST-Only + 8 كشف + 8 failover + 3 refactor parity). (4) **PARTS boundaries + bridge_refactor** — إعادة توليد كاملة بتطابق بايت (11/11 parity). (5) **التوثيق** — تحديث PROGRESS.md (الجذري + engineering) و SESSION_LOG و V3_RESUME_SESSION و README و TEST_SUITE_CATALOG + بوابة hadith_sijil كاملة.
* **السبب:** قرار المالك: Git Native Sync كان يفشل بـ `name 'dest_root' is not defined` بشكل متكرر ➔ REST هو المسار الوحيد؛ وخطأ "requires AI Data Retention" كان يعلّق المهمة بلا failover.
* **الحراسة:** `tests/test_p20_rest_only_data_retention.py` (27 اختباراً — 4 مجموعات) + تعديل حراس P17.
* **الأدلة:** pytest ➔ 219 passed + `python scripts/hadith_sijil.py` ➔ Exit Code 0. الإصدار المعتمد `01.31_telegram_gen_bridge.py`. bridge_refactor بتطابق بايت. Push/PR اليدوي بانتظار تفويض GitHub (المزامنة التلقائية تدفع لـ main).
* **الحالة:** مُعتمد وفعال.

### [DEC-017] — دقة تصنيف commit في الرفع REST: جديد ➕ vs معدل ✏️ (S40 / P21)
* **القرار:** إصلاح `_default_github_uploader` في `01.31_telegram_gen_bridge.py`: كان أي ملف مرفوع (جديد أو معدل) يدخل قائمة `uploaded` الواحدة، فتعرض رسالة تليجرام دائماً «➕ جديد» حتى للملفات المعدلة، وقائمة `modified` لا تُملأ أبداً رغم أن العرض (سطر stats_line) و `github_sync` يقرآنها. الإصلاح: التصنيف عند نجاح الـ PUT عبر `remote_sha` المتاح أصلاً — `(modified if remote_sha else uploaded).append(rel)` — والنتيجة ترجع المفتاحين معاً. لا تغيير في سلوك الرفع نفسه (صفر مخاطرة تشغيلية، تصنيف عرض فقط).
* **السبب:** بلاغ المالك النصي: «مش بيفرق بين ان ملف اتعدل او ملف جديد… عاوز يكون اكثر دقه في تحديد نوع الـ commit».
* **الحراسة:** حارسان جديدان في `tests/test_p20_rest_only_data_retention.py` (test_09_p21_uploader_distinguishes_new_vs_modified + test_10_p21_github_sync_consumes_modified).
* **الأدلة:** pytest ➔ 221 passed + `python scripts/hadith_sijil.py` ➔ Exit Code 0. PARTS محدثة (+4 أسطر ➔ 6390) و bridge_refactor بتطابق بايت.
* **الحالة:** مُعتمد وفعال.

### [DEC-018] — P23 البحث الهرمي للملفات المشتركة + يافطة AGENTS/GEMINI (S42)
- **القرار:** اعتماد `resolve_shared_path` (محلي أولاً ➔ الفولدر الأب `W___webapp/` ➔ المحلي للإنشاء) كآلية موحدة لالتقاط الملفات المشتركة: `telegram_bot_token.txt` + `project_registry/` + `projects_tree.json` + `accounts_genspark.json` (كمرشح أول مع إبقاء fallback القديم) — Zero Breaking Changes بأولوية `local.exists()`.
- **السبب:** توحيد الأسرار والسجلات بين نسخ الجسر المتعددة بدون نسخ يدوي ولا كسر النسخ القديمة (خطة المالك المعتمدة في `P23_Shared_Secrets_And_Project_Registry_Auto_Discovery.md`).
- **الأدلة:** `tests/test_p23_shared_paths.py` 17/17 + بوابة 238/238 Exit 0 + parity 11/11 بعد إزاحة PARTS +16 (6406 سطراً).
- **ملحق:** إنشاء `AGENTS.md` + `GEMINI.md` (القفل الثاني — يافطة القاعدة المركزية لأي AI/محرر).

### [DEC-019] — P24 الكوميت الذكي: حقن محرك كوين في رفع GitHub + المسار المشترك لحسابات كوين (S44)
- **القرار:** (1) تطبيق `resolve_shared_path` (نفس منطق P23: محلي ➔ الفولدر الأب `W___webapp/` ➔ المحلي للإنشاء) داخل `qwen_engine.py` على `QWEN_ACCOUNTS_FILE` — مركزية `accounts_qwen.json` بدون كسر النسخ القديمة. (2) حقن جراحي في `01.31`: دالة جديدة `ProjectRegistry._qwen_commit_prefix_for_job` تستدعي `qwen_engine.generate_ai_summary()` **مرة واحدة فقط لكل job** قبل حلقة الـ PUT في `_default_github_uploader`، والرسالة الذكية تُستخدم كبادئة (prefix) لرسائل sync/delete. (3) Fallback معزول حرفياً: أي فشل (None / Exception / استيراد / job فارغ) ➔ prefix فارغ ➔ **نفس الرسالة القديمة حرفياً** `f"[{key}] sync {job_id}: {rel}"` — الرفع لا ينكسر أبداً بسبب كوين. (4) تثبيت قرار المالك: `AI_RACE_ACCOUNTS = 0` (كل الحسابات تتسابق) + مهلة المحرك الأصلية 30ث/مرحلة كما هي بدون اختراع أرقام.
- **السبب:** فجوة مؤكدة بالفحص (S44-T1/T2): `01.31` لم يكن يستدعي كوين إطلاقاً رغم جاهزية المحرك (اختبار حي: فوز في 22.44s على Qwen3.8-Max) — رسائل الكوميت كانت ثابتة بلا معنى وظيفي.
- **الحراسة:** `tests/test_p24_qwen_commit_bridge.py` (17 اختباراً — 4 مجموعات: المسار المشترك 5 + prefix mock بدون شبكة 5 + عقد رسائل uploader 4 + قرارات المالك 3).
- **الأدلة:** pytest ➔ **255 passed** + `python scripts/hadith_sijil.py` ➔ Exit Code 0 + parity 11/11 بعد إزاحة PARTS +24 (6430 سطراً). ملحق: إزالة `bridge_bot.log` و `.pytest_cache/` من التتبع مجدداً (تسربا من المزامنة التلقائية وكسرا حارسي P17).
- **الحالة:** مُعتمد وفعال. **P22 (Heartbeat) تظل مجمدة ⏸️ — لم يُلمس أي ملف يخصها.**

### [DEC-020] — P25 الإلغاء التفاعلي وإيقاف التوليد الفوري + ترقية 01.32 (S45)
- **القرار:** (1) ترقية الإصدار النشط `01.31` ➔ `01.32_telegram_gen_bridge.py` (`BUILD_VERSION = "01.32"`، baseline المجمّد ما زال `01.30`). (2) مسجل أحداث إلغاء مركزي محمي بـ Lock (`_ACTIVE_CANCEL_EVENTS` + 7 دوال) بمفتاح توكن قصير 12-hex — لأن `callback_data` في تيليجرام محدود بـ 64 بايت بينما project_key قد يبلغ 80 حرفاً. (3) زر [🛑 إلغاء البناء الحالي] `danger` أسفل زر المعاينة `primary` في `build_live_preview_keyboard` (معامل `cancel_token` اختياري = توافق خلفي كامل)، مع تأكيد أمان من خطوتين: `cancel_prompt:` يعرض كيبورد التأكيد فقط، `cancel_exec:` ينفذ، `cancel_abort:` يرجع كيبورد التشغيل — البلوك يعالج مبكراً بمعزل تام عن سلسلة if/elif (صفر تعارض مع `pctl:*`). (4) الإيقاف القهري تعاوني (Cooperative Stream Abort): حقن `threading.Event` عبر `BridgeConfig.cancel_event` ➔ المحرك `01.03` يفحصه كأول سطر داخل `r.iter_lines()` ➔ `break` ➔ `r.close()` (قطع اتصال ask_proxy — مطابق لزر ⏹️ Stop) ➔ يرجع `__USER_CANCELLED__` **بأولوية قصوى قبل** تصنيف `__CREDIT_EXHAUSTED__`. (5) الجسر: نوم متقطع `Event.wait(timeout=5)` بدل sleep (استيقاظ فوري لحظة الإلغاء) + حالة `CANCELLED` تخرج من الـ failover **بلا أي عقوبة/تبريد للحساب** (الإلغاء قرار مستخدم وليس فشل حساب). (6) Zero Leaks: `unregister_cancel_event` في `finally` بالـ worker يغطي كل المخارج + `release_project_run` كما هو + الضغط على زر قديم بعد التنظيف يرد بهدوء «المهمة انتهت بالفعل».
- **السبب:** طلب المالك الصريح في `Cancel_Flag.md`: لا توجد أي وسيلة لإيقاف بناء جارٍ — والضوابط الإلزامية: ممنوع التنفيذ الأعمى، Zero Leaks، Zero Conflicts، خطوتا أمان.
- **الحراسة:** `tests/test_p25_interactive_cancel.py` (40 اختباراً — 5 مجموعات: CancellationManager 12 + كيبورد البطاقة 5 + عقود worker/failover 16 + عقد قطع بث المحرك 5 + محاكاة التدفق الكامل 2).
- **الأدلة:** pytest ➔ **295 passed** + `python scripts/hadith_sijil.py` ➔ Exit Code 0 + parity 11/11 بعد إعادة حساب PARTS بالمراسي (6702 سطراً: p03 ➔ 850 … p12 ➔ 6702). ملحق: إزالة `bridge_bot.log` و `.pytest_cache/` من التتبع (المرة السابعة) + تصحيح ليبلات «01.31» النصية في `hadith_sijil.py`/`generate_docs.py`.
- **الحالة:** مُعتمد وفعال. **P22 (Heartbeat) تظل مجمدة ⏸️ — لم يُلمس أي ملف يخصها.**

### [DEC-021] — S46 إصلاح لوحة ما بعد الإلغاء + ترقية 01.33 (بلاغ `Cancel_Flag_03.md`)
- **القرار:** (1) ترقية الإصدار النشط `01.32` ➔ `01.33_telegram_gen_bridge.py` (`BUILD_VERSION = "01.33"`، baseline المجمّد ما زال `01.30`، و`01.32` أُرشف في `docs/legacy/`). (2) إصلاح جراحي واحد: رسالة الإلغاء النهائية في الـ worker (سطر ~5563) تستدعي `build_dashboard_keyboard(chat_id)` كاملةً بدل الكيبورد اليتيم ذي الزر الواحد [🚀 مشروع جديد] — سلوك ما بعد الإلغاء الآن مطابق حرفياً لسلوك ما بعد اكتمال البناء. (3) قاعدة دائمة جديدة: أي رسالة نهائية (terminal) بعد إلغاء يجب أن ترفق اللوحة الكاملة — ممنوع الزر اليتيم.
- **السبب:** بلاغ المالك الصريح في `Cancel_Flag_03.md`: بعد الإلغاء الناجح كان المستخدم يُترك أمام زر وحيد ولا يستطيع استئناف عمله (معاينة/سجل/إعدادات) بدون أوامر يدوية.
- **الحراسة:** حارسان جديدان في `tests/test_p25_interactive_cancel.py` (الملف الآن 42): `test_17_cancel_terminal_shows_full_dashboard_keyboard` + `test_18_cancel_terminal_has_no_orphan_single_button`.
- **الأدلة:** pytest ➔ **297 passed** + `python scripts/hadith_sijil.py` ➔ Exit Code 0 + parity 11/11 (نفس boundaries — 6702 سطراً). ملحق: إزالة `bridge_bot.log` و `.pytest_cache/` من التتبع (المرة الثامنة — الموافقة الدائمة من S41).
- **الحالة:** مُعتمد وفعال. **P22 (Heartbeat) تظل مجمدة ⏸️ — لم يُلمس أي ملف يخصها.**

### [DEC-022] — P26 حذف المشروع التفاعلي والتنظيف الذري (S47 — طلب `Atomic_Cleanup_02.MD`)
- **القرار:** تنفيذ ميزة Interactive Project Deletion & Atomic Cleanup داخل `01.33_telegram_gen_bridge.py` (الملف الآن 6946 سطراً — نفس `BUILD_VERSION = "01.33"`): (1) زر «🗑️ حذف المشروع» أحمر (danger) كصف مستقل في لوحة تفاصيل المشروع — إضافة وليس استبدالاً لزر إلغاء البناء P25. (2) تأكيد In-Place بخطوتي أمان عبر `edit_telegram_message_text`: `pdel_prompt:` (شاشة تحذير — نعم أحمر/تراجع أخضر) ➔ `pdel_exec:` (تنفيذ) أو `pdel_abort:` (عودة لشاشة التفاصيل بصفر تعديل ملفات) — معالجات ككتلة معزولة مبكرة (سطر ~5921). (3) حماية التشغيل: `is_project_build_active` (سطر ~3818) يمنع حذف مشروع له بناء نشط عبر `_ACTIVE_CANCEL_EVENTS`. (4) الحذف الذري: `delete_project_atomically` (سطر ~3865) — حماية ➔ الفهرس + كل pid aliases تحت القفل ➔ `projects_tree.json` ➔ مجلد القرص — يُرجع dict نتيجة دون استثناءات وبلا مساس بأي جار.
- **السبب:** طلب المالك الصريح في `Atomic_Cleanup_02.MD` (بروتوكول INSPECT ➔ PLAN ➔ EXECUTION): لا وسيلة لحذف مشروع من تيليجرام — والضوابط: ممنوع الحذف بضغطة واحدة، ممنوع حذف مشروع يعمل، Zero Neighbor Damage.
- **الحراسة:** حزمة جديدة `tests/test_p26_project_deletion.py` (**33 اختباراً** — 5 مجموعات: Keyboards 7 + RunningProtection 5 + AtomicDeletion 10 + NeighborSafety 3 + SourceContracts 8) بعزل كامل بمجلد مؤقت لكل اختبار.
- **الأدلة:** pytest ➔ **330 passed** + `python scripts/hadith_sijil.py` ➔ Exit Code 0 + parity 11/11 بعد إعادة حساب PARTS بالمراسي (6946 سطراً: p08 ➔ 4019 / p09 ➔ 5227 / p12 ➔ 6946). ملحق: إزالة `bridge_bot.log` و `.pytest_cache/` من التتبع (المرة التاسعة — الموافقة الدائمة من S41).
- **الحالة:** مُعتمد وفعال. **P22 (Heartbeat) تظل مجمدة ⏸️ — لم يُلمس أي ملف يخصها.**

### [S48 — قيد جلسة بلا قرار تنفيذي] — P27 فحص ميداني INSPECT-ONLY لميزة تصفح المشاريع بنظام الصفحات (2026-08-21)
- **الطبيعة:** جلسة فحص فقط — **صفر تعديل على أي ملف كود** التزاماً بشرط المالك الصريح في `تصفح_المشاريع_بنظام_الصفحات.MD` («لا تنفذ أي تعديل قبل أن أعطيك موافقة صريحة» — INSPECT → PLAN → APPROVE → EXECUTE).
- **نتائج T1–T7 (على السورس الفعلي `01.33_telegram_gen_bridge.py` — 6946 سطراً):** (1) سبب ظهور 3 مشاريع: `limit=3` حرفي في `build_dashboard_keyboard` سطر 4752. (2) 🔴 اكتشاف: زر «📁 مشاريعي» `cmd:list_projects` موجود في 5 كيبوردات (4561/4574/4708/4724/4748) لكنه **زر ميت بلا handler** في موزّع الـ callbacks (فُحصت السلسلة 5985–6506 كاملة). (3) `list_known_projects` (سطر 4222) جاهزة كمصدر بيانات مرتّب (updated_at تنازلياً تحت القفل). (4) اختيار المشروع `proj:`/`pview:` (handlers 6470/6127) لن يُمس.
- **الخطة المقترحة (بانتظار الموافقة):** ثابت مركزي `PROJECTS_PER_PAGE = 20` + دالة `build_projects_page_keyboard` + handlers جديدة (`cmd:list_projects` يُصلح الزر الميت + `plist:page:{N}` بتعديل نفس الرسالة `edit_telegram_message_text` + `plist:noop` للعداد) + حماية Out-of-Bounds + حزمة `tests/test_p27_projects_pagination.py` — التفاصيل الكاملة في `PROGRESS.md` الجذري (قسم S48).
- **قرار تفسيري مقترح:** ملف المالك متضارب داخلياً (الجسم الآمر: 20/صفحة — فقرات ملصوقة لاحقة: 5/صفحة) ➔ نعتمد **20/صفحة** لأنه النص الصريح الأحدث («القيمة المطلوبة حالياً هي 20 فقط») والثابت المركزي يجعل تغييرها لاحقاً سطراً واحداً. يُعرض على المالك للتثبيت.
- **الأدلة:** pytest ➔ 330 passed + `hadith_sijil.py` ➔ Exit Code 0 (قبل وبعد إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع — المرة العاشرة، موافقة S41 الدائمة).
- **الحالة:** ⛔ `BLOCKED-ON-OWNER` — بانتظار كلمة موافقة صريحة قبل T-A.

### [DEC-023] — P27 تنفيذ ميزة تصفح المشاريع بنظام الصفحات كاملة (S48 — الجزء الثاني: التنفيذ المعتمد، 2026-08-21)
- **الاعتماد:** صدرت موافقة المالك الصريحة («نفّذ يا هندسة على بركة الله») مع تثبيت القرارين: (1) `PROJECTS_PER_PAGE = 20`. (2) اللوحة الرئيسية تبقى معاينة سريعة (أحدث 3) وزر «📁 مشاريعي» يفتح شاشة التصفح المستقلة.
- **T-A (البنية):** الثابت المركزي `PROJECTS_PER_PAGE = 20` + `compute_projects_page_bounds` (حساب حدود آمن تماماً: صفحة سالبة/صفر/نص/تجاوز ➔ قصّ لأقرب صفحة صالحة — صفر Crash) + `render_projects_page_text` (عداد إجمالي + موضع + نطاق العرض N–M + رسالة صفر مشاريع) + `build_projects_page_keyboard` (صفوف المشاريع بنفس عقود `proj:`/`pview:` القائمة + صف تنقل `[⬅️ السابقة][📄 N / X][التالية ➡️]` بأزرار حواف تُحذف تلقائياً + صف `[🚀 مشروع جديد][🏠 رجوع للوحة التحكم]` دائماً) — أدرجت داخل نطاق p09 بعد `build_dashboard_keyboard`.
- **T-B (المعالجات):** 3 فروع جديدة في الموزّع قبل `pview:` — `cmd:list_projects` (يفتح الصفحة 1 — **إصلاح الزر الميت المكتشف في INSPECT**) + `plist:page:{N}` (تقليب In-Place عبر `edit_telegram_message_text` على نفس الرسالة — صفر Spam، مع fallback إرسال عند غياب message_id) + `plist:noop` (زر العداد عرض فقط).
- **T-C (الحراسة):** حزمة `tests/test_p27_projects_pagination.py` — **39 حارساً** في 6 محاور: الثابت (20 + تعريف وحيد) / حدود الصفحات (0/20/21/47/100 + قصّ سالب/تجاوز/نص تالف) / الكيبورد (حواف أولى-أخيرة-وسطى + عداد + عزل chat_id + ترتيب الأحدث أولاً + إعادة استخدام عقود proj:/pview:) / النص / عدم انحدار اللوحة الرئيسية (limit=3 حرفياً + بلا أزرار تقليب) / عقود المصدر (الفروع الثلاثة + In-Place + ترتيب التعريف قبل الموزّع).
- **T-D (المرايا):** تحديث خريطة PARTS في `rebuild_refactor.py` (p09 ➔ 4020–5300، p10 ➔ 5301–5581، p11 ➔ 5582–5925، p12 ➔ 5926–7039) + إعادة توليد `bridge_refactor/` ➔ parity **11/11** (بايت-بايت).
- **T-E (البوابة):** pytest ➔ **369 passed** (330 + 39 جديداً) + `hadith_sijil.py` ➔ **Exit Code 0** ✅ (بعد إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع — المرة الحادية عشرة، موافقة S41 الدائمة).
- **الحجم:** `01.33` أصبح **7039 سطراً** (+93: T-A 73 + T-B 20).
- **القرار:** ✅ P27 مغلقة — الحالة `READY` 🟢 بانتظار E2E حي من المالك.

### [DEC-024] — P28 استقبال ملفات المهام النصية (.txt & .md) — Document Ingestion (S49 — طلب `05_—.txt_&_.md-Document_Ingestion.md`، 2026-08-21)
- **الاعتماد:** تقرير INSPECT (T1–T7) قُدِّم أولاً وصدرت موافقة المالك الصريحة («نفذ») قبل أي تعديل.
- **المبدأ المعماري (DRY):** حقن واحد مبكر في مسار `message` يحوّل محتوى الملف إلى متغير `text` القائم — فيغذي تلقائياً **كل** حالات الـ Wizard (`AWAITING_NEW_PROMPT`, `AWAITING_CONT_PROMPT`, ...) والمسار الافتراضي بلا لمس أي handler.
- **T-A (البنية — p04 بجوار `send_telegram_document`):** الثابتان `ALLOWED_DOCUMENT_EXTENSIONS = frozenset({".txt", ".md", ".markdown", ".text"})` و `MAX_DOCUMENT_SIZE_BYTES = 5MB` + دالة `download_telegram_document_text(file_id)` (getFile ➔ استخراج `file_path` ➔ تنزيل ➔ `decode("utf-8", errors="replace")`؛ أي فشل شبكة/HTTP≠200/ok=false/file_path مفقود ➔ `None` بدون استثناء يتسرب لخيط الـ Polling).
- **T-B (الحقن — p12 داخل `handle_telegram_update`):** كتلة معزولة **بعد بوابة `is_chat_allowed`** (لا تنزيل من غرباء) و**قبل فحص `/start`** بشرط الحراسة `if document and not text:` (رسائل الـ Document لا تحمل `text` أصلاً ➔ Zero Regression حرفي للنصوص العادية) — فحص الامتداد بـ `suffix.lower()` (يقبل `.TXT`) ➔ رفض ودي، فحص الحجم قبل أي تنزيل ➔ رفض ودي، فشل التنزيل/محتوى فارغ ➔ تنبيه «تعذر قراءة»، دمج الـ Caption: `f"{caption}\n\n{content}"` وإلا المحتوى وحده.
- **T-C (الحراسة):** حزمة `tests/test_p28_document_input.py` — **37 حارساً** في 4 محاور: الثوابت (4) / دالة التنزيل بموديول `requests` وهمي محقون في `sys.modules` (9: نجاح UTF-8 + بايتات تالفة ➔ `\ufffd` بلا Crash + HTTP 500/404 + ok=false + file_path مفقود + استثناء شبكة + توكن فارغ بلا نداء شبكة) / الـ Dispatcher (15: قبول txt/md/markdown/.TXT + دمج Caption + تغذية Wizard `AWAITING_NEW_PROMPT` مع `project_key_hint` + رفض pdf/zip/بلا اسم/تجاوز 5MB **قبل** أي تنزيل + حد 5MB بالضبط مقبول + تنبيه تعذر القراءة) / Zero Regression (4: النص العادي لا يلمس مسار الملفات + `/start` سليم + text+document معاً = نص + الشات غير المعتمد محجوب قبل التنزيل) + عقود المصدر (6).
- **T-D (المرايا):** تحديث خريطة PARTS (p04 ➔ 851–1294 «+45»، إزاحة p05–p12 حتى 7120) + إعادة توليد `bridge_refactor/` ➔ parity **11/11** (بايت-بايت).
- **T-E (البوابة):** pytest ➔ **406 passed** (369 + 37 جديداً) + `hadith_sijil.py` ➔ **Exit Code 0** ✅ (بعد إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع — المرة الثانية عشرة، موافقة S41 الدائمة).
- **الحجم:** `01.33` أصبح **7120 سطراً** (+81: T-A 46 + T-B 35).
- **مخاطر موثقة بشفافية:** التنزيل متزامن داخل خيط الـ Polling (مقبول لحد 5MB مع timeouts صارمة (10,30)/(10,60)) + الوثائق المعاد توجيهها بلا `file_name` تُرفض ودياً كامتداد غير مدعوم.
- **القرار:** ✅ P28 مغلقة — الحالة `READY` 🟢 بانتظار E2E حي من المالك (إرسال ملف .txt فعلي للبوت).

### [DEC-025] — P29+P30+P31: مراقبة الحسابات الحية + المحاسبة الزمنية الجنائية + الاستدعاء الكسول لكوين (S50 — طلبا `06_Account_Journey_Chain.md` و`08_EXTENSION.md`، 2026-08-21)
- **الاعتماد:** نُفذت الحزم الثلاث في `01.33` (7337 سطراً) واكتمل توثيقها وإغلاق بوابتها في هذه الجلسة وفق بروتوكول الاستئناف.
- **P29 (مراقبة الحسابات — Account Journey Chain):** `record_account_journey` يسجل حصرياً لحظة الـ claim الفعلي (سطر 2462 — منع تكرار A→A المتتالي + السماح بالعودة A→B→A + `bridge_cfg.account_journey = []` reset لكل تشغيل بسطر 2419) + Snapshots ثابتة لكل event لا تتغير عند تبديل الحساب لاحقاً + الـ Live Renderer يعرض «الحساب النشط» من snapshot الحدث فقط (لا Email وهمي) وسطر «تبديل الحساب: من X ← إلى Y» + `format_account_journey_line` في الرسالة النهائية (سطر 6073) يظهر فقط عند تعدد الحسابات الفعلية (backward compatible).
- **P30 (المحاسبة الزمنية — Extension 08 نقطة المالك الثامنة):** `open_account_timing_span` لحظة الـ claim (سطر 2463) + `close_account_timing_span` حتمي idempotent في `finally` (سطر 2722 — كل المسارات: نجاح/فشل/إلغاء/استثناء) + المدة من `time.monotonic()` حصرياً (wall للعرض فقط) + `aggregate_journey_spans_per_email` (عودة الحساب A→B→A = مدخل واحد مجمّع ×2) + `format_arabic_duration` (ثوانٍ/دقائق/ساعات + سالب/None بلا Crash) + كتلة `format_account_timing_block` بالرسالة النهائية (سطر 6076): إيميلات كاملة **Unmasked** + مدة كل حساب + «(المُنجِز)» للأخير + توتال + عدد الحسابات وعدّاد الاستئناف بفصل صارم (Resume ≠ Accounts−1).
- **P31 (الاستدعاء الكسول لكوين):** المشكلة — `ai_prefix` كان يُحسب قبل حلقة الـ PUT فكان كوين يُستدعى (شبكة + مهلة حتى 30ث) حتى لو الـ job كله unchanged وصفر commits. الحل — `ai_prefix = None` + `_lazy_ai_prefix()` متداخلة memoized داخل `_default_github_uploader` (سطر 3358) تُستدعى فقط عند أول PUT فعلي بعد فحص unchanged أو أول DELETE فعلي (ريموت 200): job كله مطابق = **صفر نداء لكوين**. عقد DEC-019 محفوظ حرفياً (نداء واحد/job + fallback للرسالة القديمة حرفياً — Zero Breaking).
- **T-C (الحراسة):** 3 حزم جديدة = **77 حارساً**: `test_p29_account_observability.py` (28: Journey/Snapshots/Renderer/الرسالة النهائية/عقود المصدر) + `test_p30_account_timing.py` (35: سيناريوهات A–H شاملة monotonic والإغلاق المزدوج وعزل الـ configs المتوازية) + `test_p31_lazy_qwen_prefix.py` (14: صفر نداء عند unchanged كامل + memoization + delete يوقظ + الرسائل حرفياً + عقود مصدرية — mock كامل بلا شبكة).
- **T-D (المرايا):** `bridge_refactor/` محدَّثة ➔ parity **11/11** (بايت-بايت مع 7337 سطراً).
- **T-E (البوابة):** pytest ➔ **483 passed** (406 + 77) + `hadith_sijil.py` ➔ **Exit Code 0** ✅ (بعد إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع — المرة الثالثة عشرة، موافقة S41 الدائمة).
- **التوثيق:** تحديث TEST_SUITE_CATALOG (483/25 ملفاً) + README (483) + V3_RESUME (3 قواعد دائمة جديدة P29/P30/P31) + نسختا PROGRESS.
- **القرار:** ✅ P29+P30+P31 مغلقة — الحالة `READY` 🟢 بانتظار E2E حي من المالك (مهمة متعددة الحسابات لرؤية مسار الحسابات + كتلة التوقيت في الرسالة النهائية).

### [DEC-026] — P32: استخراج باسورد الحساب ببحث هجين وتصفح بالصفحات (S51 — طلب `09_Hybrid_Search.MD`، 2026-08-21)
- **الطلب:** استبدال زر «📊 فحص الحسابات والكريدت» بـ «🔐 استخراج باسورد الحساب» مع دعم البحث اليدوي بالإيميل + تصفح الحسابات بالصفحات (التالي/السابق) وزر الإلغاء، بعد فحص ميداني T0–T7.
- **تصحيحان جوهريان للخطة (أُثبتا من السورس لا من كلام الطلب):**
  1. الخطة افترضت وجود دالة `handle_text_message` — **غير موجودة إطلاقاً** في `01.33`. توزيع النصوص سلسلة `if action == ...` داخل `handle_telegram_update` (تبدأ سطر 6912 قبل التعديل)، فحُقن المسار اليدوي هناك.
  2. الخطة اقترحت `acc_view:{email_or_index}` — **الإيميل مرفوض معمارياً**: حد `callback_data` في تيليجرام 64 بايت والإيميلات الطويلة تكسره (نفس علة توكن P25). القرار: **الفهرس حصراً** مع ترتيب أبجدي ثابت في `list_lookup_accounts` لضمان استقرار الفهرس (حارس يقيس البايتات فعلياً بإيميلات طويلة).
- **الترقيم:** الطلب سماها «Phase 31» لكن P31 محجوزة فعلاً للاستدعاء الكسول لكوين (DEC-025) ➔ اعتُمدت **P32** لمنع تضارب الترقيم في الكتالوج والوثائق.
- **التنفيذ (p09):** `ACCOUNTS_PER_PAGE = 5` + `AWAITING_ACCOUNT_PASSWORD_LOOKUP` + `list_lookup_accounts` (قراءة خالصة من `read_accounts_safe` بترتيب ثابت) + `compute_accounts_page_bounds` (Out-of-Bounds Safe على نمط P27) + `find_account_by_email` (strip+lower، بلا تطابق جزئي) + `describe_account_state` (مبنية على عقد `is_account_ready` القائم) + `render_account_lookup_text` + `build_account_lookup_keyboard` + `render_account_password_card` + كيبورداي الكارت وإعادة المحاولة.
- **التنفيذ (p12):** استبدال الزر في `build_dashboard_keyboard` + حذف معالج `cmd:check_accs` القديم نهائياً (كان يعرض حساباً عشوائياً ورصيده) + 4 معالجات جديدة: `cmd:account_pwd_lookup` (تعيين الحالة + الصفحة الأولى) و`acc_page:` (تقليب In-Place بـ `edit_telegram_message_text` + `noop` للعداد) و`acc_view:` (بالفهرس مع رفض هادئ لأي فهرس تالف/سالب/خارج المدى) و`acc_cancel` (تصفير + لوحة التحكم) + المسار اليدوي **كأول فحص `action`** في السلسلة.
- **ملاحظة الوظيفة المفقودة:** فحص الرصيد السريع الذي كان يقدمه الزر القديم زال بقرار المالك الصريح في الطلب (الخيار B/الاستبدال) — الرصيد ما زال ظاهراً في مسارات المهام (بوابة P13 + الرسالة النهائية P30).
- **الحراسة:** حزمة `tests/test_p32_account_password_lookup.py` = **78 حارساً** (8 مجموعات: عقود الزر + القائمة والترتيب + حدود الصفحات + البحث اليدوي + الكارت + الكيبورد والتصفح + التدفق الكامل عبر `handle_telegram_update` بمحاكاة الإرسال/التعديل + عقود مصدرية بنيوية). من نتائج الحراسة الفعلية: 4 اختبارات كشفت خللين حقيقيين فور كتابتها — تعليق برمجي أعاد نص الزر القديم للملف (أُصلح)، وافتراض خاطئ أن `set_user_state(chat_id, {})` يعيد dict فارغاً بينما العقد الفعلي يبصم `ts` (صُحح الاختبار للعقد الفعلي لا العكس).
- **المرايا والبوابة:** حدود `PARTS` محدَّثة (p09 ➔ 4275–5713، p10 ➔ 5714–5994، p11 ➔ 5995–6345، p12 ➔ 6346–7571) + إعادة توليد `bridge_refactor/` ➔ parity **11/11** بايت-بايت. pytest ➔ **561 passed** (483 + 78) + `hadith_sijil.py` ➔ **Exit Code 0** ✅ (بعد إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع — المرة الرابعة عشرة، موافقة S41 الدائمة).
- **الحجم:** `01.33` ➔ **7571 سطراً** (+234).
- **القرار:** ✅ P32 مغلقة — الحالة `READY` 🟢 بانتظار E2E حي من المالك (ضغط الزر ➔ كتابة إيميل + تقليب الصفحات + ضغط زر إيميل + إلغاء).

### [DEC-027] — P33: أزرار الإجراءات السريعة في رسالة الاكتمال (S52 — طلب `10_COMPLETED.MD`، 2026-08-22)
- **الطلب:** إضافة زرين جديدين لكيبورد الرسالة الختامية (COMPLETED) بقاعدة **Pure Add Only — صفر حذف/صفر تغيير** على الأزرار الخمسة القديمة: [▶️ كمل الآن] فوق (صف مستقل تحت زر المعاينة مباشرة) + [⬅️ رجوع للوحة التحكم] كآخر صف دائماً.
- **الفحص الميداني (قبل أي حرف):** كيبورد الاكتمال كان يُبنى **محلياً** داخل `process_user_task_async` بقائمة `kb_rows` مع 3 شرطيات تاريخية (pub_url موجود / resume_pid موجود / project_key موجود) — بناء محلي غير قابل للاختبار المعزول. الفحص أكد أيضاً أن `cmd:dashboard` **بلا معالج** في الموزّع (الموجود `cmd:show_dashboard` فقط) — إضافة الزر بدون معالج = زر ميت (نفس علة P27/T5 التاريخية).
- **قراران معماريان:**
  1. **Extract-then-Add:** استخراج البناء المحلي لدالة مركزية `build_completed_message_keyboard(pub_url, resume_pid, project_key)` في p09 (بجوار كيبوردات اللوحة) تحفظ الشرطيات الثلاث حرفياً، ثم إضافة الزرين داخلها — الـ worker يستدعيها بسطر واحد (`reply_markup = build_completed_message_keyboard(...)`) وصفر `kb_rows` محلي متبقٍ.
  2. **إعادة استخدام العقود القائمة:** [▶️ كمل الآن] يستخدم `cont:{resume_pid}` (نفس معالج زر الاستئناف القديم حرفياً — صفر معالج جديد + يختفي تلقائياً بلا pid)، و[⬅️ رجوع للوحة التحكم] يستخدم `cmd:dashboard` بفرع `elif` جديد في الموزّع **مكافئ حرفياً** لفرع `cmd:show_dashboard` (لوحة كاملة: `render_dashboard_text` + `get_main_keyboard`) بعده مباشرة — بلا مساس بحرفية الفرع القديم (مرساة حراس P26).
- **الشكل النهائي (كامل المدخلات):** 6 صفوف — 🌐 معاينة / **▶️ كمل الآن 🆕** / 🔄 استئناف + 🌳 نقاط / ⭐ تفاصيل / 🚀 جديد / **⬅️ رجوع للوحة 🆕**. زر الرجوع يظهر في **كل** التركيبات الثمانية للمدخلات (حتى الكيبورد الأدنى: 🚀 جديد + ⬅️ رجوع).
- **الحراسة:** حزمة `tests/test_p33_completed_quick_actions.py` = **31 حارساً** (6 مجموعات: البنية الكاملة 5 + زر كمل الآن 6 «منها قياس حد 64 بايت فعلياً» + زر الرجوع 4 «كل التركيبات الـ 8» + الشرطية القديمة Zero Regression 5 + معالج cmd:dashboard حي بمحاكاة كاملة 3 «منها التطابق الحرفي مع show_dashboard وبوابة is_chat_allowed» + عقود مصدرية 8 «منها صفر kb_rows متبقٍ بالـ worker»).
- **المرايا والبوابة:** حدود `PARTS` محدَّثة (p09 ➔ 4275–5743، p10 ➔ 5744–6024، p11 ➔ 6025–6364، p12 ➔ 6365–7594) + إعادة توليد `bridge_refactor/` ➔ parity **11/11** بايت-بايت. pytest ➔ **592 passed** (561 + 31) + `hadith_sijil.py` ➔ **Exit Code 0** ✅ (بعد إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع — المرة الخامسة عشرة، موافقة S41 الدائمة).
- **الحجم:** `01.33` ➔ **7594 سطراً** (+23: بنّاء p09 +30 / تنحيف worker −11 / فرع الموزّع +4).
- **القرار:** ✅ P33 مغلقة — الحالة `READY` 🟢 بانتظار E2E حي من المالك (بناء مهمة حتى الاكتمال ➔ ضغط ▶️ كمل الآن ➔ استئناف فوري، وضغط ⬅️ رجوع ➔ لوحة كاملة).

### [DEC-028] — P34: التنسيق الآمن للرسائل وحدود الأحرف — Total Message Guard (S53 — طلب `11_Cap.MD`، 2026-08-22)
- **البلاغ (تشخيص المالك المؤكد ميدانياً):** رسالة الاكتمال كانت تسقط أزرارها/تُرفض من تيليجرام (حد 4096) رغم وجود قصّ قديم — لأن القصّ القديم (سطر 6098 تاريخياً) كان يقص **نص الرد الأخير فقط** إلى 2500 حرف (`clean_text[:2500] + "\n... [تم الاقتصاص لزيادة الحجم]"`) بينما بلوكات P29/P30 الجديدة (رحلة الحسابات + التوقيت الجنائي + مسار الساندبوكس الطويل) تُضاف **بعده** فيتجاوز الإجمالي 4500 حرف. الحل المطلوب: **Total Message Guard** — قياس الرسالة المجمعة بالكامل لا الرد وحده.
- **البنية (p04 — بجوار طبقة الإرسال):** 5 ثوابت مركزية بتعريف وحيد: `PREVIEW_MAX_CHARS=1000` + `PREVIEW_TRUNCATION_SUFFIX` («... [انقر على الرابط لمشاهدة الرد الكامل]») + `RES_MSG_MAX_CHARS=3500` + `OUTGOING_TEXT_HARD_LIMIT=3900` + `OUTGOING_TEXT_SAFE_LIMIT=3800` (الترتيب الحتمي 3500 < 3800 < 3900 < 4096) + 4 دوال:
  1. `_strip_partial_html_token`: تنظيف نقطة القص من وسم `<...>` أو كيان `&...;` مبتور (منع `400 Bad Request` من parse_mode=HTML).
  2. `clamp_preview_text`: جسم المعاينة ≤1000 يمر حرفياً / >1000 قصّ + اللاحقة — None/فارغ آمن.
  3. `enforce_completion_message_budget(res_msg, preview_body)`: الرسالة المجمعة ≤3500 دائماً — **القصّ يقع على جسم المعاينة أولاً** والبيانات التشغيلية (الروابط/الحالة/المفاتيح/بلوكات P29/P30) محفوظة، مع fallback ذيلي أخير عند غياب المعاينة — idempotent.
  4. `clamp_outgoing_text`: **صمام الأمان الأخير** في `send_telegram_message_detailed` — محقون في `payload["text"]` مباشرة: ≤3900 يمر حرفياً / >3900 ➔ قصّ آمن إلى ≤3800 — و`reply_markup` يمر سليماً بالكامل (الأزرار لا تسقط أبداً مهما كان طول النص).
- **الحقن في الـ worker (P34 فوق P33):** `clean_text = clamp_preview_text(clean_text)` (بديل القصّ القديم 2500 المحذوف نهائياً) + التقاط `preview_body` + `res_msg = enforce_completion_message_budget(res_msg, preview_body)` **قبل** `send_telegram_message` — فرض الميزانية يسبق الإرسال حتمياً.
- **الحراسة:** حزمة `tests/test_p34_safe_message_formatting.py` = **41 حارساً** (6 مجموعات: الثوابت 7 «منها التعريف الوحيد بالمصدر والترتيب الحتمي» + clamp_preview_text 8 «منها سلامة كيان/وسم HTML عند نقطة القص واختفاء 2500 القديم» + ميزانية الاكتمال 8 «منها حفظ البيانات التشغيلية وidempotency» + clamp_outgoing_text 7 + محاكاة إرسال حية 4 «النص يُقص وreply_markup يمر حرفياً بالكامل» + عقود مصدرية 7 «منها فرض الميزانية قبل الإرسال ومرآة bridge_refactor»).
- **المرايا والبوابة:** حدود `PARTS` محدَّثة (p04 ➔ 1021–1544 يشمل P34، الإزاحة حتى p12 ➔ 7659) + إعادة توليد `bridge_refactor/` ➔ parity **11/11** بايت-بايت. pytest ➔ **633 passed** (592 + 41) + `hadith_sijil.py` ➔ **Exit Code 0** ✅ (بعد إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع — المرة السادسة عشرة، موافقة S41 الدائمة).
- **الحجم:** `01.33` ➔ **7659 سطراً** (+65: ثوابت ودوال P34 في p04 + حقن الـ worker).
- **القرار:** ✅ P34 مغلقة — الحالة `READY` 🟢 بانتظار E2E حي من المالك (مهمة متعددة الحسابات برد طويل >2500 حرف ➔ الرسالة الختامية تنزل كاملة بكل أزرارها بلا رفض من تيليجرام).

### [DEC-029] — S54: تحويل زر [▶️ كمل الآن] إلى الأخضر style: success (طلب مالك مباشر، 2026-08-22)
- **الطلب:** Button Style Update — إضافة `"style": "success"` لزر [▶️ كمل الآن] داخل `build_completed_message_keyboard` (كيبورد الاكتمال المركزي P33) في `01.33`، مع مزامنة المرايا وتحديث حراس P33 والبوابة الكاملة والتوثيق.
- **الفحص قبل التنفيذ:** النمط `success` ضمن `ALLOWED_BUTTON_STYLES = {"primary", "success", "danger"}` المعتمدة منذ البداية — `make_inline_keyboard` يمرره سليماً بلا إسقاط. سابقة قائمة بالفعل: زر [▶️ كمل الآن] في كيبورد قرار الاستئناف (`cmd:resume_continue`) يحمل `success` منذ إنشائه — التعديل يوحّد الهوية البصرية للزر نفسه في كيبورد الاكتمال.
- **التنفيذ (سطر واحد لكل مرآة):** `kb_rows.append([{"text": "▶️ كمل الآن", "callback_data": f"cont:{resume_pid}", "style": "success"}])` في `01.33` (داخل حدود p09) + `bridge_refactor/parts/p09_github_dashboard.py` + إعادة توليد `bridge_refactor/` بـ `scripts/rebuild_refactor.py` — تكافؤ الدالة **IDENTICAL** والوصول عبر `bridge_refactor.telegram.ui` يعيد الزر بالنمط الأخضر. **Zero Breaking:** زر 🔄 استئناف القديم وكل الأزرار الأخرى بلا مساس (بلا style).
- **الحراسة (+3 ➔ 34):** في `tests/test_p33_completed_quick_actions.py`: `test_02b_style_is_success_green` (النمط حرفياً "success") + `test_02c_success_style_is_in_allowed_styles` (عضوية ALLOWED_BUTTON_STYLES — ضمان عدم السقوط في make_inline_keyboard) + `test_02d_legacy_resume_button_has_no_style` (Zero Breaking على زر 🔄 القديم).
- **البوابة:** pytest ➔ **636 passed** (633 + 3) + `hadith_sijil.py` ➔ **Exit Code 0** ✅ + parity 11/11 ✅ (بعد إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع — المرة الثامنة عشرة، موافقة S41 الدائمة).
- **الحجم:** `01.33` ➔ **7659 سطراً** (بلا تغيير — تعديل داخل سطر قائم).
- **القرار:** ✅ S54 مغلقة — الحالة `READY` 🟢 — E2E الحي لـ P33 لدى المالك يشمل الآن التحقق البصري من الزر الأخضر.

### [DEC-030] — S55/P35: كشف رفض الموديل والتعافي منه — Model Decline Recovery (طلب مالك مباشر، 2026-08-22)
- **العلة المكتشفة:** الرد القصير "The model declined to answer this request..." يصل بطول > 25 حرفاً فيُحتسب `COMPLETED` في `detect_response_status` — صحيح تقنياً (المهمة انتهت) لكنه خاطئ دلالياً: لا يوجد أي ناتج، والأسوأ أن **مؤشر الاستئناف كان يتقدم لنقطة "الرفض"** فيفسد سلسلة الاستئناف على المشروع.
- **الفلسفة المعتمدة:** الرفض يُعامل **«كأن الطلب لم يُرسل»** — لا ناتج يُسجل، لا مؤشر يتقدم، والمستخدم يُوجَّه لإعادة الصياغة مع بقاء طريق «كمل من آخر نقطة صالحة» مفتوحاً.
- **البنية (4 مواضع في `01.33`):**
  1. **p05 — الكشف:** ثوابت مركزية بتعريف وحيد (`MODEL_DECLINE_MARKERS` 5 عبارات lowercase + `MODEL_DECLINE_MAX_RESPONSE_CHARS=300` + `MODEL_DECLINED_STATUS="MODEL_DECLINED"`) + `is_model_decline_response` (قصير ≤300 بعد strip + جوهره عبارة رفض — **حارس False Positive**: الرد الطويل الذي يقتبس الجملة ليس رفضاً، نفس فلسفة إصلاح RUNNING الكاذب). `detect_response_status` **لم يُلمس**.
  2. **p10 — الوصف:** فرع `MODEL_DECLINED` في `describe_terminal_outcome`: failure بعنوان 🚫 مميز + `allow_preview=True` (الاستثناء الوحيد بين حالات الفشل — نص الرفض قصير وعرضه يزيد الثقة).
  3. **p09 — الكيبورد:** `build_model_decline_keyboard` — زران ملونان أعلى الكيبورد (✍️ أعد صياغة البرومبت `cmd:decline_retry` primary + ⬅️ رجوع `cmd:decline_dashboard` danger) ثم أزرار الاكتمال المعتادة تحتهما حرفياً عبر `build_completed_message_keyboard` (بلا نسخ — أي تطور مستقبلي يسري تلقائياً).
  4. **p11 worker + p12 dispatcher:** إعادة التصنيف `model_declined = status == "COMPLETED" and is_model_decline_response(...)` (فوق COMPLETED **حصرياً** = Zero Breaking) + تصفير `final_pid = ""` (المؤشر لا يتقدم) + اختيار الكيبورد بالحالة + معالجا `cmd:decline_retry` (إرشاد فقط — بلا `EXECUTOR.submit`) و`cmd:decline_dashboard` (مكافئ حرفياً لـ `cmd:dashboard` بفرع منفصل).
- **الحراسة (+42):** `tests/test_p35_model_decline.py` — 7 مجموعات: الثوابت 5 / الكشف وحارس False Positive 9 (منها حدّية 300/301 فعلية وثبات detect_response_status) / terminal outcome 6 / الكيبورد 8 (منها التركيبات الثمانية وحد 64 بايت) / عقود worker المصدرية 6 (منها ترتيب إعادة التصنيف قبل كتابة الهوية) / معالجا الموزّع 5 / Zero Breaking 3. الإجمالي **678**.
- **المرايا:** PARTS محدَّثة (p05 ➔ 1545–1827 وإزاحة حتى p12 ➔ 7765) + إعادة توليد `bridge_refactor/` + parity **11/11**.
- **البوابة:** pytest ➔ **678 passed** + `hadith_sijil.py` ➔ **Exit Code 0** ✅ (بعد إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع — المرة التاسعة عشرة، موافقة S41 الدائمة).
- **الحجم:** `01.33` ➔ **7765 سطراً** (+106).
- **القرار:** ✅ S55 مغلقة — الحالة `READY` 🟢 — E2E الحي لدى المالك يشمل الآن P35 (برومبت يُتوقع رفضه ➔ رسالة 🚫 بالزرين الملونين + التأكد أن الاستئناف بعدها يكمل من النقطة الصالحة قبل الرفض).
