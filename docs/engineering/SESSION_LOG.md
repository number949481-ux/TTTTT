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
