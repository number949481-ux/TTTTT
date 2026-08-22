# 🧪 كتالوج حالات واختبارات الوحدة (TEST_SUITE_CATALOG.md)

> **الكتالوج الشامل:** يوثق الـ 164 فحصاً التاريخية التراكمية للمشروع + الـ **736 فحصاً النشطة محلياً** لإصدار `01.33` + المحرك `01.03`  
> **حالة الاختبارات النشطة:** 736/736 PASS (100% OK) — بوابة `hadith_sijil.py` بـ Exit Code 0 ⚡  

## 📊 0. المصفوفة النشطة الحالية — 01.33 + المحرك 01.03 (736 فحصاً / 31 ملفاً)

| الحزمة | الملف | العدد | النطاق |
|---|---|:---:|---|
| P1 فروع GitHub | `test_p1_github_branches.py` | 4 | Pagination + الفرع الافتراضي |
| P2 توجيه الموديلات | `test_p2_model_routing.py` | 8 | عقود الموديلات الـ 5 + Aliases |
| P3 لقطات التراجع | `test_p3_regression.py` | 12 | تطابق بايتات الحمولات القديمة |
| P7 المعاينة الحية | `test_p7_live_preview.py` | 10 | زر لايف + حارس UX |
| P10 تكامل التوثيق | `test_p10_docs_integrity.py` | 1 | فحص 33 ملف docs + الروابط |
| P11 أنماط الأزرار | `test_p11_button_styles.py` | 10 | Whitelist styles (Bot API 9.4) |
| P12 استئناف المشروع | `test_p12_resume_same_project.py` | 13 | carry_pid + مهلة الخمول |
| P13 بوابة الرصيد | `test_p13_preflight_balance.py` | 14 | رصيد < 100 = تبريد 29h |
| P14 مزامنة Upsert | `test_p14_upsert_sync.py` | 16 | مقارنة محتوى + حارس الحذف 50% |
| P15 محرك كوين | `test_p15_qwen_engine.py` | 16 | اكتمال 27 مكوناً + التوافق |
| P16 النشر المبكر | `test_p16_early_public.py` | 9 | make_public فور التقاط الـ pid |
| P17 التصليب | `test_p17_hardening.py` | 24 | جلسة/رصيد/جروبات (حُذفت 3 حراس qwen commit الملغاة في P20) |
| **P18 وقف النشاط** | `test_p18_activity_stop.py` | **20** | **أي تغيّر Deep Thinking / Tasks Remaining = وقف فوري (حتى النقصان)** |
| **P19 نسخ الإعدادات** | `test_p19_copy_settings.py` | **24** | **نسخ إعدادات مشروع آخر + الترقيم التسلسلي («الحج 1» ➔ «الحج 2») + منع تسرب توكن env** |
| **P20/P21 REST-Only + DATA_RETENTION + تصنيف commit** | `test_p20_rest_only_data_retention.py` | **29** | **إلغاء Git Native Sync (رفع REST حصرياً) + كشف AI Data Retention ومعاملته كنفاد رصيد (تبريد 29h + نفس آخر رسالة) + P21: تمييز جديد ➕ / معدل ✏️ عبر remote_sha (الحارسان test_09/test_10)** |
| **P23 المسارات المشتركة** | `test_p23_shared_paths.py` | **17** | **`resolve_shared_path` (محلي ➔ الأب `W___webapp/` ➔ المحلي) للتوكن/السجل/الشجرة/الحسابات + يافطة AGENTS/GEMINI + صفر hardcode** |
| **P24 الكوميت الذكي** | `test_p24_qwen_commit_bridge.py` | **17** | **حقن `qwen_engine.generate_ai_summary` كبادئة لرسائل sync/delete (مرة/job) + fallback حرفي للرسالة القديمة + مركزية `accounts_qwen.json` + `AI_RACE_ACCOUNTS=0`** |
| **P25 الإلغاء التفاعلي** | `test_p25_interactive_cancel.py` | **42** | **مسجل أحداث الإلغاء (توكن 12-hex + Lock) + زر 🛑 بخطوتي أمان + قطع بث SSE تعاوني (`__USER_CANCELLED__` قبل تصنيف الرصيد + `r.close()`) + `Event.wait(5)` + `CANCELLED` بلا عقوبة + Zero Leaks في `finally` + حارسا S46: اللوحة الكاملة `build_dashboard_keyboard` بعد الإلغاء وممنوع الزر اليتيم** |
| **P26 حذف المشروع الذري** | `test_p26_project_deletion.py` | **33** | **زر 🗑️ أحمر (danger) كصف مستقل + تأكيد بخطوتي أمان In-Place (`pdel_prompt/abort/exec`) + حماية البناء النشط `is_project_build_active` + الحذف الذري `delete_project_atomically` (فهرس + aliases تحت القفل ➔ شجرة ➔ قرص) + سلامة الجيران (5 مجموعات: Keyboards 7 + RunningProtection 5 + AtomicDeletion 10 + NeighborSafety 3 + SourceContracts 8)** |
| **P27 تصفح المشاريع بالصفحات** | `test_p27_projects_pagination.py` | **39** | **الثابت `PROJECTS_PER_PAGE=20` (تعريف وحيد) + `compute_projects_page_bounds` (قصّ آمن لأي مدخل تالف/سالب/متجاوز) + كيبورد التصفح (حواف أولى/أخيرة/وسطى + عداد `plist:noop` + عزل chat_id + إعادة استخدام عقود `proj:`/`pview:`) + الفروع الثلاثة (`cmd:list_projects` إصلاح الزر الميت + `plist:page:` In-Place + `plist:noop`) + عدم انحدار اللوحة (limit=3)** |
| **P28 استقبال ملفات المهام (.txt & .md)** | `test_p28_document_input.py` | **37** | **الثابتان `ALLOWED_DOCUMENT_EXTENSIONS` (frozenset رباعي) + `MAX_DOCUMENT_SIZE_BYTES=5MB` + دالة `download_telegram_document_text` (getFile ➔ تنزيل UTF-8 بـ `errors="replace"` — أي فشل ➔ None بلا Crash، 9 حراس بموديول requests وهمي) + الـ Dispatcher (قبول txt/md/markdown/.TXT + دمج Caption + تغذية Wizard + رفض pdf/zip/بلا اسم/تجاوز 5MB قبل أي تنزيل) + Zero Regression (النص العادي/`/start`/text+document معاً/الشات غير المعتمد) + عقود المصدر (الموقع بعد البوابة وقبل /start + شرط `document and not text`)** |
| **P29 مراقبة الحسابات الحية** | `test_p29_account_observability.py` | **28** | **`record_account_journey` (لحظة الـ claim الفعلي فقط + منع تكرار A→A + السماح بالعودة A→B→A + reset لكل تشغيل) + Snapshots ثابتة لكل event (نسخة مستقلة لا تتغير لاحقاً) + Live Renderer (سطر «الحساب النشط» من snapshot الحدث فقط — لا Email وهمي + سطر «تبديل الحساب من X ← إلى Y») + سطر «مسار الحسابات» بالرسالة النهائية يظهر فقط عند تعدد الحسابات الفعلية (backward compatible) + عقود المصدر** |
| **P30 المحاسبة الزمنية الجنائية** | `test_p30_account_timing.py` | **35** | **`open_account_timing_span` لحظة الـ claim + `close_account_timing_span` حتمي idempotent في `finally` + `aggregate_journey_spans_per_email` (تجميع عودة الحساب A→B→A في مدخل واحد ×2) + `format_arabic_duration` (ثوانٍ/دقائق/ساعات + سالب/None بلا Crash) + `format_account_timing_block` (إيميلات كاملة Unmasked + توتال + «(المُنجِز)» لآخر حساب) + monotonic مصدر المدة (محصّن ضد قفزات wall clock) + عزل التشغيلات والـ configs المتوازية + الفصل الصارم Resume ≠ Accounts−1** |
| **P31 الاستدعاء الكسول لكوين** | `test_p31_lazy_qwen_prefix.py` | **14** | **`ai_prefix = None` + `_lazy_ai_prefix` memoized داخل `_default_github_uploader` — job كله unchanged (وكل delete على ريموت 404) = صفر نداء لكوين (توفير الباقة + إلغاء تأخير حتى 30ث/sync) + أول PUT/DELETE فعلي يوقظه مرة واحدة فقط (عقد DEC-019) + رسائل الكوميت حرفياً بلا تغيير (بادئة عند النجاح / القديمة عند الفشل) + عقود مصدرية (النداء بعد فحص unchanged داخل الحلقة)** |
| **P32 استخراج باسورد الحساب (بحث هجين)** | `test_p32_account_password_lookup.py` | **78** | **استبدال زر `cmd:check_accs` بـ `cmd:account_pwd_lookup` (اختفاء الزر القديم نهائياً من الملف) + `list_lookup_accounts` (ترتيب أبجدي ثابت يضمن استقرار الفهرس + تصفية بلا-إيميل/non-dict + قراءة خالصة تُحرس ببصمة الملف قبل/بعد) + `compute_accounts_page_bounds` (5/صفحة — Out-of-Bounds Safe: 0/سالب/999/نص/None + بلا صفحة وهمية عند المضاعف التام) + `find_account_by_email` (تطبيع strip+lower + رفض التطابق الجزئي) + `render_account_password_card` (الإيميل والباسورد `<code>` للنسخ + تبليغ صريح عند غياب الباسورد + هروب HTML) + `describe_account_state` (ACTIVE/COOLDOWN/BANNED) + Pagination عبر `handle_telegram_update` (تقليب In-Place بـ editMessageText بلا Spam + فهارس مطلقة للصفحة الثانية + حفظ الصفحة في الحالة + `acc_page:noop` لا يفعل شيئاً) + `acc_view:{index}` بالفهرس لا بالإيميل (حراسة حد تيليجرام 64 بايت بإيميلات طويلة) + المسار اليدوي كأول فحص action (الإيميل لا يُرسل كبرومبت مهمة أبداً + الحالة تبقى عند الفشل لإعادة المحاولة) + الإلغاء `acc_cancel` (تصفير + لوحة التحكم + النص بعده يعود مهمة عادية) + Zero Regression لعقود P29/P30/P31** |
| **P33 أزرار الإجراءات السريعة (رسالة الاكتمال)** | `test_p33_completed_quick_actions.py` | **34** | **البنّاء المركزي `build_completed_message_keyboard` (استخراج بناء `kb_rows` المحلي من الـ worker — Extract-then-Add) + الأزرار الخمسة القديمة محفوظة حرفياً (نص + callback/url — Pure Add Only) + [▶️ كمل الآن] صف مستقل بـ `cont:{resume_pid}` (إعادة استخدام معالج الاستئناف القائم + يختفي بلا pid + قياس حد 64 بايت فعلياً) + [⬅️ رجوع للوحة التحكم] `cmd:dashboard` آخر صف في كل التركيبات الثمانية للمدخلات + الشرطيات التاريخية الثلاث (لا زر url ميت بلا pub_url / لا استئناف بلا pid / لا تفاصيل بلا key) + معالج `cmd:dashboard` الحي مكافئ حرفياً لـ `cmd:show_dashboard` (لوحة كاملة + بوابة is_chat_allowed) + عقود مصدرية (تعريف وحيد + صفر kb_rows متبقٍ بالـ worker + الفرع الجديد elif بعد القديم) + حراس S54 الثلاثة: [▶️ كمل الآن] بنمط أخضر `style == "success"` حرفياً + النمط ضمن `ALLOWED_BUTTON_STYLES` (لن يسقط في make_inline_keyboard) + زر 🔄 استئناف القديم بلا style (Zero Breaking)** |
| **P34 التنسيق الآمن وحدود الأحرف** | `test_p34_safe_message_formatting.py` | **41** | **الثوابت المركزية (تعريف وحيد لكل منها): `PREVIEW_MAX_CHARS=1000` + `PREVIEW_TRUNCATION_SUFFIX` («... [انقر على الرابط لمشاهدة الرد الكامل]») + `RES_MSG_MAX_CHARS=3500` + `OUTGOING_TEXT_HARD_LIMIT=3900` + `OUTGOING_TEXT_SAFE_LIMIT=3800` (والترتيب الحتمي 3500 < 3800 < 3900 < 4096) + `clamp_preview_text` (≤1000 يمر حرفياً / >1000 قصّ + لاحقة — None/فارغ آمن) + `enforce_completion_message_budget` (رسالة الاكتمال المجمعة ≤3500 دائماً — القصّ على جسم المعاينة أولاً والبيانات التشغيلية «الروابط/الحالة/المفاتيح» محفوظة + fallback ذيلي + idempotent) + `clamp_outgoing_text` بطبقة الإرسال (≤3900 حرفياً / >3900 ➔ ≤3800) + سلامة HTML عند نقاط القص (`_strip_partial_html_token` — لا وسم `<...>` ولا كيان `&...;` مبتور = منع 400 Bad Request) + محاكاة إرسال حية: النص يُقص و`reply_markup` (صفوف الأزرار) يمر إلى الـ payload سليماً بالكامل + عقود مصدرية (الحقن في `payload["text"]` + الاستدعاءان بالـ worker + فرض الميزانية قبل الإرسال + اختفاء القصّ القديم 2500/«تم الاقتصاص لزيادة الحجم» نهائياً + مرآة bridge_refactor)** |
| **P35 كشف رفض الموديل والتعافي (Model Decline Recovery)** | `test_p35_model_decline.py` | **42** | **الثوابت المركزية بتعريف وحيد (`MODEL_DECLINE_MARKERS` lowercase + `MODEL_DECLINE_MAX_RESPONSE_CHARS=300` + `MODEL_DECLINED_STATUS`) + `is_model_decline_response` (كشف الرفض للردود القصيرة ≤300 فقط + case-insensitive + strip — وحارس False Positive الجوهري: الرد الطويل الذي يقتبس جملة الرفض ليس رفضاً + حدّية 300/301 فعلية) + `detect_response_status` بلا مساس (الرفض COMPLETED تقنياً وإعادة التصنيف بالـ worker حصرياً فوق COMPLETED — Zero Breaking لكل فشل آخر) + فلسفة «كأن الطلب لم يُرسل»: تصفير `final_pid` يمنع تقدم مؤشر الاستئناف لنقطة الرفض + `describe_terminal_outcome(MODEL_DECLINED)` = failure بعنوان 🚫 مميز و`allow_preview=True` (الوحيد بين حالات الفشل — نص الرفض قصير وعرضه مفيد) + `build_model_decline_keyboard` (✍️ أعد صياغة البرومبت `cmd:decline_retry` primary + ⬅️ رجوع `cmd:decline_dashboard` danger أعلى الكيبورد ثم أزرار الاكتمال حرفياً عبر البنّاء المركزي بلا نسخ — في كل التركيبات الثمانية + حد 64 بايت) + معالجا الموزّع (الإرشاد بلا EXECUTOR.submit + لوحة التحكم المكافئة حرفياً) + Zero Breaking (كيبورد الاكتمال بلا أزرار رفض + فرع COMPLETED سليم)** |
| **P36 مسار الرفض السريع في المحرك (Engine Fast Decline Path)** | `test_p36_engine_fast_decline.py` | **29** | **كاشف المحرك `01.03` المطابق دلالياً لكاشف P35 (نفس الـ 5 عبارات lowercase حرفياً + عتبة 300 + حارس False Positive — حارس تطابق يقرأ سورس الجسر ويطابق العبارات) + تعريف وحيد بيافطة `[P36]` + سلوك الكاشف معزولاً (قصّ snippet من السورس — بلا استيراد المحرك) + المواقع الثلاثة (CLI chat / الرئيسي URL-mode / المتوازي): `_declined` يُحسب قبل أي مسار مكلف + `_do_auto_share`/`auto_download_project`/`ensure_public`/`args.share` كلها محروسة بـ `not _declined` + الرابط المباشر يُبنى بلا شبكة عند الرفض + Zero Breaking (`_update_balance`/`update_conversation`/`_save_ticket_question`/`save_url_entry` بلا حراسة) + 3 تعريفات بالضبط (صفر NameError) + py_compile** |
| **P37 فتح بطاقة ملخص الاستئناف من زر إعادة الصياغة (Decline ➔ Resume Summary Card)** | `test_p37_decline_resume_summary.py` | **29** | **`build_model_decline_keyboard`: الزر الأزرق يحمل مفتاح المشروع `cmd:decline_retry:{project_key}` مع تعقيم المفتاح (regex `[^A-Za-z0-9_-]` ➔ `_` + قصّ 80) وفحص حد تليجرام 64 بايت فعلياً بالـ UTF-8 + Fallback آمن (بلا مفتاح None/"" أو تجاوز الحد ➔ الحرفية القديمة `cmd:decline_retry` — عقد P35 التاريخي) + معالج الموزّع الجديد `startswith("cmd:decline_retry:")` يستدعي `start_project_resume_from_key` (بطاقة 🔄 ملخص الاستئناف + `AWAITING_PROJECT_RESUME_DECISION` بسياق نظيف root/latest pid + كيبورد ▶️ كمل الآن `cmd:resume_continue` / ⚙️ عدّل الإعدادات `cmd:resume_settings`) + رسالة fallback مهذبة عند الفشل + بلا `EXECUTOR.submit` أبداً (عقد P35 رقم 7) + ترتيب الفروع: المطابقة الحرفية تسبق startswith (الزر القديم يعمل حرفياً) + Zero Breaking (كيبورد الاكتمال بلا أزرار رفض + أزرار الاكتمال تحت زرَي الرفض + الزر الأحمر بلا مساس)** |
| Parity المرآة | `test_refactor_parity.py` | 11 | تطابق بايت bridge_refactor مع 01.33 (7792 سطراً) |
| **الإجمالي** | **31 ملفاً** | **736** | ✅ 736/736 PASS |


---

## 📊 1. ملخص مصفوفة الاختبارات الكلية (164 Tests Master Catalog)

| النطاق / المرحلة | ملفات الاختبارات الرئيسية | عدد الفحوصات | الحالة |
|---|---|:---:|:---:|
| **الإعدادات والمستودع (TSK-101 ➔ 105)** | `test_tsk101_phase1.py` ... `test_tsk105_continuation_limit.py` | 28 فحص | ✅ مغلقة |
| **سجل المشاريع والتخزين (TSK-201 ➔ 204)** | `test_tsk201_registry_mapping.py` ... `test_tsk204_resume_context.py` | 24 فحص | ✅ مغلقة |
| **إدارة الملفات والـ Checkpoints (TSK-301 ➔ 304)** | `test_tsk301_file_index.py` ... `test_tsk304_hot_archive_retention.py` | 26 فحص | ✅ مغلقة |
| **طابور الرفع وإعادة المحاولة (TSK-401 ➔ 403)** | `test_tsk401_upload_queue.py` ... `test_tsk403_sync_recovery.py` | 22 فحص | ✅ مغلقة |
| **الرصيد والسياق التراكمي (TSK-501 ➔ 502)** | `test_tsk501_credit_checkpoint.py` ... `test_tsk502_continuation_context.py` | 18 فحص | ✅ مغلقة |
| **لوحة التحكم والمراقبة (TSK-601 ➔ 603e)** | `test_tsk601_dashboard.py` ... `test_tsk603e_closeout.py` | 32 فحص | ✅ مغلقة |
| **التكامل وإعلان الجاهزية (TSK-701 ➔ 702)** | `test_tsk701_integration_evidence.py` ... `test_tsk702_release_readiness.py` | 14 فحص | ✅ مغلقة |
| **المجموع التراكمي الشامل** | **34 ملف اختبار تاريخي** | **164 فحص** | ✅ مغلقة |

---

## 🔬 2. كتالوج الـ 31 فحصاً النشطة محلياً لإصدار 01.25 (`tests/*.py`)

### 🌿 أ) حزمة فروع GitHub والـ Pagination (`test_p1_github_branches.py` — 4 فحوصات)
1. `test_default_branch_first`: التحقق من تصدير الفرع الافتراضي في أول القائمة دائماً.
2. `test_extract_from_raw_list`: التحقق من استخراج الفروع عند إرجاع GitHub لقائمة مباشرة.
3. `test_extract_from_wrapper_json`: التحقق من استخراج الفروع عند إرجاع GitHub لكائن مغلف `{"branches": [...]}`.
4. `test_paginate_100_100_37_exactly_3_requests`: التحقق من طلب 3 صفحات متتالية عند وجود 237 فرعاً والتوقف التلقائي.

### 🤖 ب) حزمة توجيه عقود الموديلات والـ Aliases (`test_p2_model_routing.py` — 8 فحوصات)
5. `test_fable_models_is_gpt41_hardcoded`: مطابقة عقد `claude-fable-5` مع `gpt-4.1`.
6. `test_gpt56_sol_contract`: مطابقة عقد `gpt-5.6-sol` وتوجيهه المعياري.
7. `test_kimi_k3_contract`: مطابقة عقد `kimi-k3` وقواميسه.
8. `test_normalize_always_returns_str`: التحقق من إرجاع سترينج سليم والتراجع لـ default عند الموديل المجهول.
9. `test_opus5_has_no_ai_chat_model`: التحقق من خصوصية عقد `claude-opus-5-code`.
10. `test_protected_is_noop_and_logs_warning`: التحقق من حماية مسارات `gpt-5.5` الخاصة.
11. `test_sonnet5_has_both_use_and_ai_chat`: التحقق من احتواء عقد `claude-sonnet-5` على المفتاحين معاً.
12. `test_unknown_gets_models_key_only`: التحقق من معالجة الموديلات المستقبلية دون كسر البوت.

### 🛡️ ج) حزمة لقطات التراجع وحماية القديم (`test_p3_regression.py` — 12 فحصاً)
13. `test_continue_chat_payload_identical`: التحقق من تطابق بايتات مفاتيح الـ Continue والـ Force.
14. `test_engine_selection_unchanged`: التحقق من استيراد وتحميل المحرك الفعلي `01.02Genspark_claude-opus-5-code.py`.
15. `test_fable_payload_matches_new_contract`: التحقق من مطابقة حمولة Fable.
16. `test_gpt55_payload_byte_identical`: إثبات تطابق بايتات مسار `gpt-5.5` القديم بنسبة 100%.
17. `test_gpt56_sol_matches_new_contract`: التحقق من حمولة GPT-5.6-Sol.
18. `test_kimi_k3_matches_new_contract`: التحقق من حمولة Kimi-K3.
19. `test_new_chat_payload_identical`: التحقق من ثبات حقول الـ New Chat.
20. `test_opus48_payload_byte_identical`: إثبات تطابق مسار `claude-opus-4-8` القديم.
21. `test_opus5_matches_new_contract`: التحقق من حمولة Opus-5.
22. `test_selected_engine_imports_model_runtime`: التحقق من قدرة المحرك على معالجة عقود الموديلات.
23. `test_sonnet5_payload_matches_new_contract`: التحقق من حمولة Sonnet-5.
24. `test_ultra_flag_untouched_by_adapter`: التحقق من ثبات flag الـ Ultra Mode دون أي مساس.

### 🌐 د) حزمة المعاينة الحية الفورية وحارس التيليجرام (`test_p7_live_preview.py` — 7 فحوصات)
25. `test_01_build_viewer_url_formatting`: التحقق من بناء رابط العارض السحابي وترميز المعرفات بدقة وأمان.
26. `test_02_build_live_preview_keyboard_running`: التحقق من بناء زر المعاينة الحية المباشر أثناء التوليد.
27. `test_03_build_live_preview_keyboard_completed`: التحقق من تحول الزر لزر المشروع المكتمل عند انتهاء التوليد.
28. `test_04_no_dead_buttons_or_unsupported_style`: التحقق من خلو الكيبورد من الأزرار الميتة وحقول style غير المدعومة.
29. `test_05_project_start_callback_dispatch`: التحقق من استدعاء الـ Callback فور التقاط حدث project_start.
30. `test_06_project_start_callback_resilience`: التحقق من صمود تدفق SSE حتى لو ألقى الـ Callback خطأ استثنائي.
31. `test_07_project_field_fallback_dispatch`: التحقق من استدعاء الـ Callback كـ Fallback عند وصول حدث project_field.

### 📚 هـ) حزمة سلامة وتكامل روابط التوثيق (`test_p10_docs_integrity.py` — 1 فحص)
32. `test_docs_integrity_no_broken_links`: فحص سلامة كافة الروابط النسبية في منظومة التوثيق بأكملها (صفر أخطاء).


