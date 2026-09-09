# PROGRESS — Telegram Gen Bridge 01.33

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
| **last-updated** | 2026-08-24 — S78 (**P44 ✅ مُقفلة بالكامل CP0–CP9** — DEC-040 Resume Pipeline Integrity: Live Rebind + Activity Gate + Stability + Final Fetch — 974/974 PASS (+12 subtests) / hadith_sijil Exit 0 / Parity 11/11 / Zero-Regression 158 PASS — البند 7 وبلوك ## 0 ➔ BLOCKED-ON-OWNER + أرشيف 7.7-ج + نظافة git المرة 46) — سابقاً: S73 (**P44 — Resume Pipeline Integrity** / DEC-040 — SPEC_DOC: `18_COT_CLEANUP_AND_DYNAMIC_RESUME_PROMPT.MD`: CP0 ✅ تبني المواصفة + CP1 ✅ المراسي F1–F10 مُثبتة بـ grep -n في الوثيقة 18 §8.1 — Baseline 962/962 +12 subtests / Exit 0 / Parity 11/11) — السابق: 2026-08-23 — S68 (**P42 — Intent Guard & Safe Project Creation Flow** / DEC-038 — بروتوكول `16_INTENT_GUARD_AND_SAFE_CREATION.MD`: حذف Fallback الإنشاء الأعمى من IDLE «Confirmation before ANY Mutation» + بطاقة تأكيد بـ nonce + Smart Prompt Forwarding للـ Wizard القائم + 63 حارساً جدد + نظافة git المرات 40–41 + بوابة 946/946 Exit 0) |
| **repository / branch** | `number949481-ux/TTTTT` / `genspark_ai_developer` |
| **target-version** | `01.33` |
| **baseline code** | `01.30` (Baseline مجمّد — و`01.29`/`01.28`/`01.27`/`01.26` Golden Baselines للمرجعية فقط، ممنوع تعديلها) 🛡️ |
| **target bot script** | `01.33_telegram_gen_bridge.py` 🚀 |
| **target engine** | `01.03Genspark_claude-opus-5-code.py` ⚙️ |
| **program-stage** | Stage 3 — Execution |
| **current WBS phase** | **P44 🚧 قيد التنفيذ (Resume Pipeline Integrity — DEC-040 — B1: Activity Gate/تغليف detect_response_status + Final Fetch | B2: Live Rebind قبل السطر 2977 في فرع CREDIT_EXHAUSTED + استثناء P20 — CP0 ✅ (S72 تبني الوثيقة 18) + CP1 ✅ (S73 المراسي F1–F10: detect_response_status def 1765/عتبة 1798 + حلقة while 2562/detect داخلي 2611 + وقف P18 2591 + apply_project_runtime_binding def 432/worker 6530 + active_query 2977 + DATA_RETENTION 2808–2822 + كروت العرض 861/1425/1504/2978/6559/6631) + CP2 ✅ (S74 — Live Rebind محقون في فرع CREDIT_EXHAUSTED قبل active_query داخل try/except بالتوقيع القائم def 432: LIVE_REBIND_OK سطر 2998 / LIVE_REBIND_FALLBACK سطر 3004 Fail-Open بالصورة القديمة + استثناء P20 في فرع DATA_RETENTION: LIVE_REBIND_SKIPPED_P20 سطر 2826 — إثبات سلوكي Terminal: تعديل الـ manifest أثناء الجلسة يُقرأ بعد الـ rebind ومجمد قبله) + CP3 ✅ (S75 — Display Parity D4: الـ rebind نُقل ليسبق إشعار continuation-handoff-ready — الترتيب الآن rebind (OK 2978/FALLBACK 2984) → notify 2989 (الكارت يقرأ continuation_prompt_public الحية سطر 861) → active_query 3013 — «اللي يظهر = اللي يتبعت» — القراءة خلف self.lock القائم في get_project_settings سطر 3286 بلا أقفال جديدة — الملف 8458 سطراً + حدود PARTS مُزاحة +6) + CP4 ✅ (S76 — Activity Gate D5+D6+D9+D12: `detect_response_status_gated` def سطر 1819 تغليفاً بلا لمس جسم `detect_response_status` def 1765 حرفياً (R4/D9) — الثوابت P44_STRUCTURED_STATUSES سطر 1812 (CREDIT_EXHAUSTED/DATA_RETENTION/SESSION_EXPIRED/FORBIDDEN تخترق البوابة فوراً) + P44_GATE_INACTIVE_READS_REQUIRED=2 سطر 1815 (debounce) + P44_GATE_STABLE_READS_REQUIRED=2 سطر 1817 (hook جاهز لـ CP5/D8) — عدّاد inactive_streak يتغذى من قراءة P18 القائمة بلا أي طلب شبكة إضافي: init قبل while سطر 2619 / تحديث 2654 (active يصفّر، inactive يزيد، None لا يلمس — حياد Fail-Open) — نقطة القرار raw_status→final_status عبر البوابة سطور 2676–2678 — D12: سقف session_timeout القائم 2622–2625 قبل البوابة بلا تغيير — دخاني 9/9 Terminal: COMPLETED+active→RUNNING / خمول قراءة واحدة يمسك وقراءتان تفتحان / المهيكلة تخترق رغم active / None→سلوك اليوم — الملف 8525 سطراً + PARTS مُزاحة p05→2047/p06→3118/p12→8525) — الحالة: **962+12 subtests / Exit 0 / Parity 11/11** — كان التالي: CP5 Stability + Final Fetch (D7+D8)) + CP5 ✅ (S77 — Stability + Final Fetch D7+D8: `compute_reply_fingerprint` def سطر 1861 (len+sha256 على UTF-8/replace — رخيصة محلية تكشف تغيّر المحتوى حتى مع ثبات الطول) + `fetch_final_reply_text` def سطر 1871 (آخر رسالة assistant حقيقية بطلب واحد أخير: FINAL_FETCH_OK سطر 1890 / أي فشل → FINAL_FETCH_FALLBACK سطر 1894 بالنص القديم كما هو Fail-Open) — التوصيل: init prev_reply_fp/stable_streak سطور 2659–2660 + التحديث من نفس قراءة الرسائل القائمة 2721–2723 (تطابُق يزيد العداد، تغيّر يعيده لـ 1) + تمرير stable_streak الحي للبوابة بدل None سطور 2730–2731 (hook CP4 اكتمل: <2 = REPLY_UNSTABLE_HOLD → RUNNING) — علم polled_any يُحسم قبل الحلقة من نفس شرطها سطور 2665–2666 (عقد P25 فحص الإلغاء أول الدورة محفوظ) + الجلبة النهائية بعد خروج الحلقة بأي سبب خصوصاً وقف P18: if polled_any and COMPLETED سطور 2750–2751 (الرد المكتمل من البث مباشرة = صفر شبكة إضافية) — دخاني 8/8 Terminal — الملف 8585 سطراً + PARTS مُزاحة p05→2084/p06→3178/p12→8585) + CP6 ✅ (S77 — Telemetry D11: الأسطر الثمانية قائمة بنمط P43 — ACTIVITY_GATE_HOLD indicator-active 1849 / debounce 1852 + REPLY_UNSTABLE_HOLD 1855 + ACTIVITY_GATE_RELEASE 1857 + FINAL_FETCH_OK 1890 + FINAL_FETCH_FALLBACK 1894 + LIVE_REBIND_OK 3105 + LIVE_REBIND_FALLBACK 3111 + LIVE_REBIND_SKIPPED_P20 2953 — أُثبت ظهورها فعلياً Terminal واحداً واحداً بمستوياتها الصحيحة INFO/WARNING عبر الاستدعاء المباشر + تنفيذ المقاطع الحرفية 3097–3113 و2951–2955 من الملف نفسه — صفر كود جديد: توثيق فقط) + CP7 ✅ (S78 — `tests/test_p44_resume_pipeline_integrity.py` 373 سطراً بالأسماء الحرفية الـ 12 من 18.03 §E — 12/12 PASS بنمط Mocks/Spies بلا شبكة + عزل Registry مؤقت (نمط P43) — الاختبارات 08/09/10/11 تنفّذ المقاطع الحرفية من كود الإنتاج نفسه عبر compile بمسار الملف (استخراج سطري بمراسي LIVE_REBIND_FALLBACK/SKIPPED_P20 — مقاوم لإزاحة الأسطر) — صفر لمس لـ 01.33 (8585 كما هو) → PARTS بلا تغيير + Parity 11/11 + pytest الكامل 974 PASS (+12 subtests) + نظافة git المرة 44) + CP8 ✅ (S78 — Quality Gates كلها خضراء: pytest 974/974 PASS (+12 subtests) صفر Skip + hadith_sijil Exit 0 (P10: 34 files) + rebuild Exit 0 + Parity 11/11 + Zero-Regression 158 اختبار p35/p40/p18/decline/activity PASS + 01.33 = 8585 بلا لمس + شجرة نظيفة — نظافة git المرة 45)** + P43 ✅ مغلقة (DEC-039 — Fast Lean Mode & Artifacts Bypass — كل CP0–CP9 محسومة في S69–S71، وثيقة 17 + أرشيف 7.7-ب) + P42 ✅ مغلقة (DEC-038) + P41 ✅ + P40 ✅ 🛡️⚡ |
| **previous slice** | `TSK-5003` (DONE) ➔ S54 مكتملة: Button Style Update — زر [▶️ كمل الآن] أخضر `"style": "success"` في `build_completed_message_keyboard` + 3 حراس (حزمة P33 ➔ 34) + بوابة 636/636 Exit 0 |
| **current slice** | `TSK-5103` (DONE) ➔ S55 مكتملة: **P35** داخل `01.33` (**7765 سطراً**) — Model Decline Recovery (طلب مالك مباشر): الرد القصير "The model declined to answer this request..." كان يُحتسب COMPLETED فيتقدم مؤشر الاستئناف لنقطة الرفض رغم غياب أي ناتج ➔ الفلسفة: «الرفض كأن الطلب لم يُرسل» — كشف مركزي `is_model_decline_response` (≤300 حرف — حارس False Positive للردود الطويلة المقتبسة) + إعادة تصنيف بالـ worker فوق COMPLETED حصرياً ➔ MODEL_DECLINED + تصفير `final_pid` (المؤشر لا يتقدم) + فرع 🚫 في `describe_terminal_outcome` (allow_preview=True) + `build_model_decline_keyboard` (✍️ أعد صياغة primary + ⬅️ رجوع danger فوق أزرار الاكتمال المركزية) + معالجا cmd:decline_retry/cmd:decline_dashboard + **42 حارساً** + parity 11/11 + بوابة 678/678 Exit 0 |
| **current-task** | ⏸️ **BLOCKED-ON-OWNER — بانتظار مهمة جديدة من المالك** ➔ آخر مرحلة: **P44 Resume Pipeline Integrity (DEC-040) ✅ مُقفلة S72–S78** داخل `01.33` (**8585 سطراً**): B2 Live Rebind في فرع CREDIT_EXHAUSTED قبل notify/active_query (`LIVE_REBIND_OK/FALLBACK/SKIPPED_P20`) + Display Parity + B1 Activity Gate (`detect_response_status_gated` تغليفاً بلا لمس جسم الأصلية) + Debounce قراءتين + حياد None + Stability (`compute_reply_fingerprint` len+sha256 + `REPLY_UNSTABLE_HOLD`) + Final Fetch بعد خروج الحلقة (`FINAL_FETCH_OK/FALLBACK` Fail-Open) + Telemetry الثمانية بنمط P43 + **12 حارساً** في `test_p44_resume_pipeline_integrity.py` — الإجمالي **974** + Parity 11/11 — أرشيفها 7.7-ج في البند 7 والتفاصيل في `18_COT_CLEANUP_AND_DYNAMIC_RESUME_PROMPT.MD` (كل Checkboxes محسومة). المرجع السابق: `TSK-5904` (DONE) ➔ S67–S68 مكتملتان: **P42** داخل `01.33` (**8212 سطراً**، +204) — Intent Guard & Safe Project Creation Flow (بروتوكول PHASE 42 / DEC-038 / وثيقة `16_INTENT_GUARD_AND_SAFE_CREATION.MD` قبل الكود): حذف الـ Fallback الأعمى «أي نص IDLE = مشروع جديد» (كان يولّد prj_* + يسجل + يحجز حساباً + يبدأ توليداً على «2+7=») واستبداله حرفياً بـ `handle_idle_intent_guard` — المبدأ الحاكم **Confirmation before ANY Mutation** على الحدود الخمسة (create/register/generate_key/claim/start_generation) + ترتيب الفحص State ➔ Commands ➔ P41 URL ➔ Guard + `classify_idle_intent` (Strong/Ambiguous للصياغة فقط — بطاقة تأكيد دائماً) + حالة `AWAITING_PROJECT_CONFIRMATION` (النص في pending_prompt — الزر يحمل nonce 12-hex فقط) + معالج `pconf:*` معزول بنمط P25/P26 (تأكيد ➔ الـ Wizard القائم DRY / إلغاء ➔ صفر أثر / Stale ➔ انتهت الصلاحية / Double-Click ➔ Idempotent) + Smart Prompt Forwarding في موضعي finalize + Telemetry 🛡️ [P42] + **63 حارساً جدد** في `test_p42_intent_guard_and_safe_creation.py` — الإجمالي **946** + parity 11/11. المرجع السابق: `TSK-5804` (DONE) ➔ S66 مكتملة: **P41** داخل `01.33` (**8008 أسطر**، +103) — Forensic Project URL Routing & Graceful Polling Shutdown (بروتوكول PHASE 41 / DEC-037 / وثيقة `15_PROJECT_ROUTING_AND_CLEAN_SHUTDOWN.MD` قبل الكود): (أ) منع Cross-Project Context Hijacking — `MALFORMED_PROJECT_LINK_MESSAGE` + `parse_project_locator` (Parsing SSOT) + `detect_context_collision` + `handle_prompt_context_collision` أول سطر في فرعي `AWAITING_NEW_PROMPT`/`AWAITING_CONT_PROMPT` قبل أي `EXECUTOR.submit` (سياق A نشط + رابط B = إغلاق السياق وتوجيه الرابط لمساره الشرعي — مسجّل/غير مسجّل/مشوّه برفض صريح بلا Fallback صامت)؛ (ب) الإغلاق النظيف — عميل getUpdates = `requests.Session()` النقية حصرياً (curl_cffi باقٍ بكل مسارات Genspark) + إعادة رفع المقاطعة داخل الحلقة + معالج خارجي `sys.exit(0)` بلا Traceback + **50 حارساً جدد** في `test_p41_routing_and_graceful_shutdown.py` — الإجمالي **883** + parity 11/11. المرجع السابق: `TSK-5704` (DONE) ➔ S65 مكتملة: **P40** داخل `01.33` (**7905 أسطر**، +32) — Compact Time UX & Bridge Decline Fast-Path (بروتوكول PHASE 40 / DEC-036): `format_compact_duration` (45s / 12m 17s / 1h 5m) في المواضع الثلاثة لكتلة P39 + Decline Fast-Path في `send_message_and_make_public` (`_declined` قبل المسارات المكلفة — تخطي الأرشيف وmake_public + الرابط بلا شبكة + `save_project_branch` بلا حراسة) + **26 حارساً** في `test_p40_compact_time_decline_fastpath.py` + وثيقة `14_DECLINE_FAST_PATH_LATENCY.MD`. المرجع الأسبق: `TSK-5503` (DONE) ➔ S60 مكتملة: **P39** داخل `01.33` (**7873 سطراً**، +66) — Streamlined Completion Card (بروتوكول `13_STREAMLINED_COMPLETION_UX.MD` / DEC-034): ثابت مركزي `PRODUCTIVE_SPAN_MIN_SECONDS=60` + فلتر نقي `filter_productive_account_entries` (عتبة الدقيقة على المجموع المجمَّع + تحصين الحساب المُنجِز + Fail-Open) + `format_account_timing_block` المطوَّرة (عنوان «الحسابات الفعلية» عند الفلترة/عنوان P30 عند Fail-Open + أدوار البداية/استئناف k/🌟 المنجز + السطر المدمج ⏱️ إجمالي (N منتجة | 🔁 M استئناف) من المفلتر فقط — التوقيع لم يتغير) + تنظيف res_msg من 6 عناصر حشو (latest_line 🧷/resume_line/fork_line/📁 الساندبوكس/🏁 علم الانتهاء+استدعاء is_finished اليتيم/حقن journey_block — الدوال P29/P30/P38 كلها باقية) + التسجيل الجنائي للقائمة الكاملة في اللوج + **46 حارساً جدد** في `test_p39_completion_ux_streamlining.py` + تحديث واعٍ لحراس p29/p30/p38 — الإجمالي **807** + PARTS محدَّثة (p03 +63 / p11 ➔ 6233–6613 / p12 ➔ 6614–7873) + parity 11/11 + نظافة git المرات 26–29. المرجع السابق: `TSK-5403` (DONE) — P38 Unified Active Account Email — 25 حارساً 
| **next-action** | بانتظار مهمة جديدة من المالك في البند 7 (أي جلسة بلا مهمة ➔ BLOCKED-ON-OWNER). اختبار تشغيلي حي (E2E) من المالك: **P44** (تعديل برومبت الاستئناف من الإعدادات أثناء جلسة حية بها نفاد رصيد ➔ الاستئناف يُرسل النص المعدَّل الجديد وكارت الـ handoff يعرضه ذاته + مهمة طويلة التفكير ➔ الحلقة لا تقف على كلام وسطي والرد الختامي الحقيقي يصل حتى مع وقف P18) + **P43** (مشروع بلا GitHub + fast_mode ➔ تخطي التنزيل مع بقاء الرابط العام + قياس السرعة الفعلي X3) + **P42** (إرسال «2+7=» أو أي نص عابر في الخمول ➔ بطاقة تأكيد فقط بلا أي إنشاء/حجز/توليد + ❌ إلغاء ➔ صفر أثر + ✅ تأكيد ➔ الـ Wizard القائم والبرومبت المحفوظ ينطلق تلقائياً بعد الاسم والموديل + زر 🚀 مشروع جديد يعمل كما كان) + **P41** (فتح سياق برومبت لمشروع A ثم إرسال رابط مشروع B ➔ يستحيل تنفيذ المهمة على A ويُوجّه الرابط لمساره + Ctrl+C أثناء تشغيل البوت على ويندوز ➔ خروج نظيف فوري برسالة ⏹️ بلا Traceback ولا خطأ CFFI) + **P40** (برومبت يُرفض ➔ رسالة الرفض تصل فوراً من الجسر بلا انتظار الأرشيف + المدد بصيغة 12m 17s) + **P39** (مهمة متعددة الحسابات فيها حسابات نفد رصيدها فوراً ➔ بطاقة الاكتمال تعرض الحسابات المنتجة فقط بالأدوار والسطر المدمج، واللوج يحوي القائمة الكاملة غير المفلترة) + **P38** (بدء مهمة ➔ سطر 📧 الحساب يظهر في بطاقة اللايف فوراً وفي بطاقات اللقطة/handoff/الاكتمال بنفس الصياغة الموحدة) + **P37** (برومبت يُرفض ➔ ضغط ✍️ أعد صياغة البرومبت ➔ بطاقة 🔄 ملخص الاستئناف تفتح فوراً ➔ ▶️ كمل الآن + برومبت جديد يكمل على نفس المشروع) + **P36** (برومبت يُتوقع رفضه عبر المحرك ➔ رسالة الرفض تصل لحظياً بلا انتظار ensure_public/share/download) + **P35** (برومبت يُتوقع رفضه ➔ رسالة 🚫 بالزرين الملونين + استئناف بعدها يكمل من النقطة الصالحة قبل الرفض) + **P34** (مهمة برد طويل >2500 حرف ومتعددة الحسابات ➔ الرسالة الختامية تنزل كاملة بكل أزرارها) + **P33** (بناء مهمة للاكتمال ➔ ضغط ▶️ كمل الآن = استئناف فوري + ضغط ⬅️ رجوع = لوحة كاملة) + P32 (زر 🔐 ➔ بحث هجين) + P29/P30 (مهمة متعددة الحسابات) + P28 (ملف .txt فعلي) + تفويض GitHub لدفع Push/PR يدوياً (المزامنة التلقائية تدفع لـ main) |
| **current-blocker** | `BLOCKED-ON-OWNER` — (أ) ميزة P22 معلّقة كلياً ⏸️ — لا تنفيذ إلا بخطة معتمدة Approve أولاً. (ب) **تنبيه وظيفي S51:** فحص الرصيد السريع الذي كان بالزر القديم `cmd:check_accs` زال بالاستبدال (قرار الطلب الصريح — الخيار B) — لو أراده المالك يُعاد كزر مستقل بجواره (الخيار C). (موافقة P27 صدرت ونُفذت في S48 ✅ — `AI_RACE_ACCOUNTS` حُسم في S44: `0` = الكل يتسابق) |
| **completion** | 946/946 Tests Verified (100%) 🧪 |
| **quality-gate** | `python scripts/hadith_sijil.py` ➔ 946/946 PASS — Exit Code 0 |
| **session-log** | `docs/engineering/SESSION_LOG.md` |
| **release decision** | `READY` 🟢 (P42: حارس النية والإنشاء الآمن — يستحيل إنشاء مشروع/حجز حساب/بدء توليد من نص عابر بلا تأكيد صريح — Zero Registry Pollution) |

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

---

## 🔎 P23 — البحث الهرمي للملفات المشتركة Shared Secrets Auto-Discovery (S42): سجل مركزي في الفولدر الأب + Zero Breaking Changes

> **طلب المالك (خطة معتمدة في `P23_Shared_Secrets_And_Project_Registry_Auto_Discovery.md`):** توحيد ملفات الحسابات والأسرار (`telegram_bot_token.txt`, `accounts_genspark.json`, `project_registry/`, `projects_tree.json`) في الفولدر الأب الكبير (`W___webapp/`) بحيث كل نسخ الجسر تلقطها تلقائياً — بأولوية محلية (لو الملف جنب النسخة يُستخدم) وبدون كسر أي نسخة قديمة، + يافطة `AGENTS.md`/`GEMINI.md` لأي AI يفتح المشروع.

- [x] **`[TSK-4001]`** T1 — `resolve_shared_path(name)` (سطر ~117): محلي ➔ الأب ➔ المحلي (للإنشاء). — دليل: `TestResolveSharedPath` 5/5 PASS (أولوية محلية + fallback الأب + الإنشاء + المجلدات).
- [x] **`[TSK-4002]`** T2 — `load_bot_token` يقرأ `telegram_bot_token.txt` عبر الدالة الموحدة. — دليل: `TestLoadBotTokenHierarchy` 3/3 PASS (env أولاً / الأب عند غياب المحلي / المحلي يكسب).
- [x] **`[TSK-4003]`** T3 — `PROJECT_REGISTRY_HOME` + `PROJECTS_TREE_FILE` عبر `resolve_shared_path` (و`registry.json` يرث المركزية). — دليل: `TestSharedPathWiring` tests 02/03/05 PASS.
- [x] **`[TSK-4004]`** T4 — المرشح الأول في `get_accounts_file_path` هو `resolve_shared_path("accounts_genspark.json")` مع إبقاء fallback القديم. — دليل: `TestSharedPathWiring::test_04` PASS.
- [x] **`[TSK-4005]`** القفل الثاني — إنشاء `AGENTS.md` + `GEMINI.md` بيافطة القاعدة المركزية والقواعد الإلزامية. — دليل: `TestCentralRuleSignage` 3/3 PASS (+ حارس صفر hardcode للتوكن).
- [x] **`[TSK-4006]`** مواءمة كاملة: PARTS boundaries مُزاحة +16 (p01 → 154 … p12 → 6406) + إعادة بناء `bridge_refactor/` بتطابق بايت (parity 11/11) + بوابة `hadith_sijil.py` = **238/238 PASS Exit Code 0** + تحديث التوثيق (هذا الملف + PROGRESS الجذري + SESSION_LOG DEC-018 + V3_RESUME). — دليل: Gate 238/238 + هذا الـ commit.

---

## 🤖 P24 — الكوميت الذكي: حقن محرك كوين في رفع GitHub (S44): Qwen Commit Bridge + المسار المشترك لحسابات كوين

> **طلب المالك:** رسائل الكوميت في الرفع REST كانت ثابتة بلا معنى (`sync {job_id}: {rel}`) رغم جاهزية `qwen_engine.py` — المطلوب حقن الملخص الذكي من كوين كبادئة للرسالة **بدون أي مخاطرة على الرفع نفسه** + مركزية `accounts_qwen.json` بنفس منطق P23.

- [x] **`[TSK-4101]`** M1 — `resolve_shared_path` داخل `qwen_engine.py` (سطر ~182): `QWEN_ACCOUNTS_FILE = resolve_shared_path("accounts_qwen.json")` — محلي ➔ الأب `W___webapp/` ➔ المحلي للإنشاء. — دليل: مجموعة المسار المشترك 5/5 PASS في `test_p24_qwen_commit_bridge.py`.
- [x] **`[TSK-4102]`** M2 — `ProjectRegistry._qwen_commit_prefix_for_job` (سطر ~2994 في `01.31`): استدعاء `qwen_engine.generate_ai_summary()` **مرة واحدة/job** قبل حلقة PUT في `_default_github_uploader` (سطر ~3032)؛ الملخص = بادئة رسائل sync/delete. — دليل: مجموعة prefix mock (بدون شبكة) 5/5 PASS.
- [x] **`[TSK-4103]`** M3 — Fallback حرفي معزول: أي فشل (None / Exception / فشل استيراد / job فارغ) ➔ prefix فارغ ➔ **نفس الرسالة القديمة حرفياً** — الرفع لا ينكسر أبداً بسبب كوين. — دليل: مجموعة عقد رسائل uploader 4/4 PASS.
- [x] **`[TSK-4104]`** قرارات المالك مثبتة: `AI_RACE_ACCOUNTS = 0` (كل الحسابات النشطة تتسابق — حُسم في S44) + مهلة المحرك الأصلية 30ث/مرحلة بلا تغيير. — دليل: مجموعة قرارات المالك 3/3 PASS.
- [x] **`[TSK-4105]`** مواءمة كاملة: PARTS boundaries مُزاحة +24 (p07 ➔ 3382 … p12 ➔ 6430) + إعادة بناء `bridge_refactor/` بتطابق بايت (parity 11/11) + بوابة `hadith_sijil.py` = **255/255 PASS Exit Code 0** + التوثيق (هذا الملف + PROGRESS الجذري + SESSION_LOG DEC-019 + TEST_SUITE_CATALOG + V3_RESUME). — دليل: Gate 255/255 + هذا الـ commit.
- [x] **`[TSK-4106]`** نظافة git (المرة السادسة): إخراج `.pytest_cache/` و `bridge_bot.log` من التتبع بعد أن أعادتهما المزامنة التلقائية وكسرا حارسي P17 (الموافقة الدائمة من S41). — دليل: `TestGeneratedFilesUntracked` 3/3 PASS.

---

## 🛑 P25 — الإلغاء التفاعلي وإيقاف التوليد الفوري Interactive Cancellation Flow (S45): زر 🛑 بخطوتي أمان + Cooperative Stream Abort + ترقية 01.32

> **طلب المالك (`Cancel_Flag.md`):** أثناء البناء لا توجد أي وسيلة لإيقاف التوليد — المطلوب زر [🛑 إلغاء البناء الحالي] أحمر أسفل زر المعاينة، بتأكيد أمان تفاعلي من خطوتين، وإيقاف قهري آمن يقطع بث SSE فوراً (مطابق لزر ⏹️ Stop) مع صفر تسريب موارد وصفر تعارض مع باقي الأزرار.

- [x] **`[TSK-4201]`** T1 — مسجل أحداث الإلغاء (سطر ~3495 في `01.32`): `_ACTIVE_CANCEL_EVENTS` + `_CANCEL_EVENTS_GUARD` (Lock) + 7 دوال (`new_cancel_token` 12-hex ≤64 بايت callback_data / `register` / `get_entry` / `update_entry` / `trigger` / `is_requested` / `unregister`) + الثابتان `CANCELLED_STATUS` و `USER_CANCELLED_MARKER`. — دليل: `TestCancellationManager` 12/12 PASS.
- [x] **`[TSK-4202]`** T2 — الكيبورد والمعالجات: `build_live_preview_keyboard(cancel_token=None)` توافق خلفي كامل — زر 🛑 danger أثناء running، وكيبورد تأكيد (🚨 نعم danger / ↩️ تراجع primary) عند `confirm_cancel`؛ بلوك callbacks مبكر معزول (`cancel_prompt:/cancel_exec:/cancel_abort:` سطر ~5700) صفر تعارض مع `pctl:*`؛ دالتان جديدتان `edit_telegram_message_text` (~925) و `edit_telegram_message_reply_markup` (~962). — دليل: `TestLivePreviewKeyboard` 5/5 PASS.
- [x] **`[TSK-4203]`** T3 — الإيقاف القهري التعاوني: `BridgeConfig.cancel_event/cancel_token` (~656) ➔ المحرك `01.03` يفحص الـ Event كأول سطر داخل `r.iter_lines()` ➔ `break` ➔ `r.close()` (قطع ask_proxy) ➔ `__USER_CANCELLED__` بأولوية قبل تصنيف `__CREDIT_EXHAUSTED__` (~1997-2087)؛ الجسر p06: فحص قبل الإرسال وداخل المتابعة + `Event.wait(timeout=5)` بدل sleep (استيقاظ فوري) + `CANCELLED` يخرج من failover **بلا عقوبة/تبريد** (~1886-2264)؛ الـ worker: تسجيل قبل أي عمل + `update_cancel_entry(live_pid=...)` عند التقاط pid (~5509) + رسالة نهائية هادئة (~5544) + **`unregister_cancel_event` في `finally`** = Zero Leaks (~5670). — دليل: `TestWorkerIntegrationContracts` 16/16 + `TestEngineStreamAbortContract` 5/5 PASS.
- [x] **`[TSK-4204]`** T4 — حزمة الحراسة `tests/test_p25_interactive_cancel.py`: **40 اختباراً** (مسجل 12 + كيبورد 5 + عقود worker/failover 16 + عقد قطع بث المحرك 5 + محاكاة تدفق كامل 2 تشمل تسجيل ➔ زر ➔ تأكيد ➔ استيقاظ فوري ➔ تنظيف). — دليل: 40/40 PASS.
- [x] **`[TSK-4205]`** المواءمة الكاملة + ترقية الإصدار: `BUILD_VERSION = "01.32"` والملف النشط `01.32_telegram_gen_bridge.py` (6702 سطراً) + PARTS boundaries الجديدة (p03 ➔ 850 … p12 ➔ 6702) + إعادة بناء `bridge_refactor/` بتطابق بايت (parity 11/11) + تصحيح ليبلات «01.31» النصية القديمة في `hadith_sijil.py`/`generate_docs.py` + بوابة `hadith_sijil.py` = **295/295 PASS Exit Code 0** + التوثيق (هذا الملف + PROGRESS الجذري + SESSION_LOG DEC-020 + TEST_SUITE_CATALOG + README + V3_RESUME). — دليل: Gate 295/295 + هذا الـ commit.
- [x] **`[TSK-4206]`** نظافة git (المرة السابعة): إخراج `.pytest_cache/` و `bridge_bot.log` من التتبع بعد أن أعادتهما المزامنة التلقائية وكسرا حارسي P17 (الموافقة الدائمة من S41). — دليل: `TestGeneratedFilesUntracked` 3/3 PASS.

---

## 🧭 S46 — إصلاح لوحة ما بعد الإلغاء + ترقية 01.33 (بلاغ `Cancel_Flag_03.md`)

> **بلاغ المالك (`Cancel_Flag_03.md`):** بعد تأكيد الإلغاء الناجح كانت الرسالة النهائية تعرض زراً يتيماً واحداً فقط [🚀 مشروع جديد] — المطلوب عرض لوحة التحكم الكاملة (Dashboard) ليستأنف المستخدم عمله فوراً بدون أوامر يدوية.

- [x] **`[TSK-4301]`** الإصلاح الجراحي: رسالة الإلغاء النهائية في الـ worker (سطر ~5563 في `01.33`) تستدعي `build_dashboard_keyboard(chat_id)` كاملةً بدل الكيبورد اليتيم — سلوك ما بعد الإلغاء الآن مطابق لسلوك ما بعد اكتمال البناء. — دليل: `test_17_cancel_terminal_shows_full_dashboard_keyboard` + `test_18_cancel_terminal_has_no_orphan_single_button` (حارسا S46 في `tests/test_p25_interactive_cancel.py` — الملف الآن **42 اختباراً**).
- [x] **`[TSK-4302]`** ترقية الإصدار + المواءمة: `BUILD_VERSION = "01.33"` والملف النشط `01.33_telegram_gen_bridge.py` (6702 سطراً — نفس boundaries p03 ➔ 850 … p12 ➔ 6702)، `01.32` أُرشف في `docs/legacy/`، parity 11/11، بوابة `hadith_sijil.py` = **297/297 PASS Exit Code 0** + تحديث التوثيق الشامل (هذا الملف + PROGRESS الجذري + V3_RESUME + TEST_SUITE_CATALOG + README + SESSION_LOG DEC-021). — دليل: Gate 297/297 + هذا الـ commit.
- [x] **`[TSK-4303]`** نظافة git (المرة الثامنة): إخراج `.pytest_cache/` و `bridge_bot.log` من التتبع بعد أن أعادتهما المزامنة التلقائية مجدداً وكسرا حارسي P17 (الموافقة الدائمة من S41). — دليل: `TestGeneratedFilesUntracked` 3/3 PASS.

---

## 🗑️ P26 / S47 — حذف المشروع التفاعلي والتنظيف الذري Interactive Project Deletion & Atomic Cleanup

> **طلب المالك (`Atomic_Cleanup_02.MD` + `Deep_Thinking_Tasks_Remaining.TXT`):** تمكين حذف أي مشروع من شاشة تفاصيل المشروع — لكن ليس مباشرة: زر 🗑️ أحمر ➔ شاشة تأكيد In-Place بخطوتي أمان (نعم/تراجع) ➔ منع الحذف لو المشروع له بناء نشط ➔ حذف ذري شامل (فهرس + شجرة + قرص) بلا مساس بالجيران.

- [x] **`[TSK-4401]`** واجهة المستخدم: زر «🗑️ حذف المشروع» (style=danger) كصف مستقل في لوحة تفاصيل المشروع (سطر ~4707 — إضافة وليس استبدالاً لزر إلغاء البناء P25) + `build_project_delete_confirm_keyboard` (نعم أحمر / تراجع أخضر) + `render_project_delete_confirm_text` + `build_project_deleted_keyboard` لشاشة النجاح (سطور ~4712-4740). — دليل: `TestDeleteKeyboards` 7/7.
- [x] **`[TSK-4402]`** المنطق الذري: `is_project_build_active` (سطر ~3818 — فحص `_ACTIVE_CANCEL_EVENTS` لمنع حذف مشروع له بناء نشط) + `delete_project_atomically` (سطر ~3865 — الترتيب الآمن: حماية التشغيل ➔ الفهرس + كل pid aliases تحت القفل ➔ `projects_tree.json` ➔ مجلد القرص `project_registry/<key>/` — يُرجع dict نتيجة دون استثناءات) + معالجات `pdel_prompt:`/`pdel_abort:`/`pdel_exec:` ككتلة معزولة مبكرة في handler الـ callbacks (سطر ~5921) مع تأكيد In-Place عبر `edit_telegram_message_text`. — دليل: `TestRunningProtection` 5/5 + `TestAtomicDeletion` 10/10 + `TestNeighborSafety` 3/3 + `TestSourceContracts` 8/8.
- [x] **`[TSK-4403]`** الحراسة والمواءمة: حزمة `tests/test_p26_project_deletion.py` (**33 اختباراً** — عزل كامل بمجلد مؤقت لكل اختبار) + إعادة حساب PARTS boundaries (الملف الآن **6946 سطراً**: p08 ➔ 4019 / p09 ➔ 5227 / p12 ➔ 6946) + إعادة بناء `bridge_refactor/` (parity 11/11 ✅) + بوابة `hadith_sijil.py` = **330/330 PASS Exit Code 0** + تحديث التوثيق الشامل (هذا الملف + PROGRESS الجذري + V3_RESUME + TEST_SUITE_CATALOG + README + SESSION_LOG DEC-022). — دليل: Gate 330/330 + هذا الـ commit.
- [x] **`[TSK-4404]`** نظافة git (المرة التاسعة): إخراج `.pytest_cache/` و `bridge_bot.log` من التتبع بعد أن أعادتهما المزامنة التلقائية مجدداً (الموافقة الدائمة من S41). — دليل: `TestGeneratedFilesUntracked` 3/3 PASS.


---

## 🔐 P32 / S51 — استخراج باسورد الحساب ببحث هجين وتصفح بالصفحات Hybrid Account Password Lookup

> **طلب المالك (`09_Hybrid_Search.MD`):** استبدال زر «📊 فحص الحسابات والكريدت» في لوحة التحكم بزر «🔐 استخراج باسورد الحساب» — بمسارين متكاملين: كتابة الإيميل يدوياً للوصول المباشر، أو تصفح الحسابات المخزّنة صفحةً صفحة (التالي/السابق) مع زر إلغاء. البروتوكول: فحص ميداني T0–T7 أولاً، ثم التنفيذ.

- [x] **`[TSK-4700]`** الفحص الميداني (INSPECT ONLY — T0–T7): إثبات كل بند من السورس/التيرمينال لا من نص الطلب، وكشف **انحرافين جوهريين** صُححا قبل كتابة أي سطر: (1) الخطة افترضت دالة `handle_text_message` — **غير موجودة إطلاقاً** في `01.33`؛ توزيع النصوص سلسلة `if action == ...` داخل `handle_telegram_update` (بدأت سطر 6912 قبل التعديل) ➔ حُقن المسار اليدوي هناك. (2) الخطة اقترحت `acc_view:{email}` — **مرفوض معمارياً** لأن حد `callback_data` في تيليجرام 64 بايت والإيميلات الطويلة تكسره (نفس علة توكن P25) ➔ اعتُمد **الفهرس** مع ترتيب أبجدي ثابت. (3) الترقيم: الطلب سماها «Phase 31» و P31 محجوزة للاستدعاء الكسول لكوين (DEC-025) ➔ اعتُمدت **P32**. — دليل: DEC-026 في `SESSION_LOG.md`.
- [x] **`[TSK-4701]`** البنية (p09): `ACCOUNTS_PER_PAGE = 5` + حالة `AWAITING_ACCOUNT_PASSWORD_LOOKUP` + `list_lookup_accounts` (قراءة خالصة من `read_accounts_safe` بترتيب أبجدي ثابت — شرط استقرار الفهرس) + `compute_accounts_page_bounds` (Out-of-Bounds Safe على نمط P27) + `find_account_by_email` (strip+lower، بلا تطابق جزئي) + `describe_account_state` (مبنية على عقد `is_account_ready` القائم) + `render_account_lookup_text` + `build_account_lookup_keyboard` + `render_account_password_card` + كيبورداي الكارت وإعادة المحاولة. — دليل: `TestAccountListing` + `TestPageBounds` + `TestManualSearch` + `TestPasswordCard` + `TestKeyboards`.
- [x] **`[TSK-4702]`** التدفق (p12): استبدال الزر في `build_dashboard_keyboard` + **حذف معالج `cmd:check_accs` القديم نهائياً** (كان يعرض حساباً عشوائياً ورصيده) + 4 معالجات جديدة: `cmd:account_pwd_lookup` (تعيين الحالة + الصفحة الأولى) و`acc_page:` (تقليب In-Place بـ `edit_telegram_message_text` + `noop` للعداد) و`acc_view:` (بالفهرس مع رفض هادئ لأي فهرس تالف/سالب/خارج المدى) و`acc_cancel` (تصفير الحالة + لوحة التحكم) + المسار اليدوي **كأول فحص `action`** في السلسلة (وإلا فُسّر الإيميل كبرومبت مهمة). — دليل: `TestDashboardButton` + `TestFullFlow` (محاكاة إرسال/تعديل عبر `handle_telegram_update`).
- [x] **`[TSK-4703]`** الحراسة والمواءمة: حزمة `tests/test_p32_account_password_lookup.py` (**78 حارساً** في 8 مجموعات) — والحراسة كشفت خللين حقيقيين فور كتابتها: تعليق برمجي أعاد نص الزر القديم للملف (أُصلح)، وافتراض خاطئ أن `set_user_state(chat_id, {})` يعيد dict فارغاً بينما العقد الفعلي يبصم `ts` (صُحح الاختبار للعقد الفعلي لا العكس) + تحديث PARTS boundaries (p09 ➔ 4275–5713 / p10 ➔ 5714–5994 / p11 ➔ 5995–6345 / p12 ➔ 6346–7571) + إعادة توليد `bridge_refactor/` (parity **11/11** بايت-بايت) + بوابة `hadith_sijil.py` = **561/561 PASS Exit Code 0** + التوثيق الشامل (هذا الملف + PROGRESS الجذري + SESSION_LOG DEC-026 + TEST_SUITE_CATALOG + README + V3_RESUME). — دليل: Gate 561/561 + هذا الـ commit.
- [x] **`[TSK-4704]`** نظافة git (المرة الخامسة عشرة): إخراج `.pytest_cache/` و `bridge_bot.log` من التتبع بعد أن أعادتهما المزامنة التلقائية مجدداً وكسرا حارسي P17 (الموافقة الدائمة من S41). — دليل: `TestGeneratedFilesUntracked` PASS.

---

## 🧹 P39 / S60 — بطاقة الاكتمال المبسطة وفلترة الحسابات المنتجة Streamlined Completion Card & Productive Accounts Filtering

> **بروتوكول المالك (`13_STREAMLINED_COMPLETION_UX.MD` / DEC-034):** بطاقة الاكتمال محشوة بتكرار أعمى (Latest=pid حرفياً، رابط الاستئناف=الرابط العام، fork/الساندبوكس/علم الانتهاء معلومات داخلية، سطر أسهم journey يستهلك 800+ حرف من ميزانية P34) وكتلة P30 تعرض حسابات نفدت في ثوانٍ بلا توليد ➔ الفلسفة: **«الفلترة تنظيف لا إخفاء» — الشات نظيف واللوج جنائي كامل**.

- [x] **`[TSK-5501]`** البنية (p03): الثابت المركزي `PRODUCTIVE_SPAN_MIN_SECONDS = 60` (تعريف وحيد top-level — لا hardcoding متناثر) + الفلتر النقي `filter_productive_account_entries(aggregated, last_email)` ➔ `(filtered, fail_open)` — عتبة الدقيقة على **المجموع المجمَّع** (عودة A→B→A بمجموع الفترتين) + **تحصين الحساب المُنجِز** (آخر حساب يظهر دائماً ولو < 60ث) + **Fail-Open إلزامي** (فلترة أفرغت الكل ➔ القائمة الكاملة) + `format_account_timing_block` المطوَّرة بنفس التوقيع: عنوان «📊 الحسابات الفعلية التي قامت بالتوليد والاستئناف» عند الفلترة / عنوان P30 عند Fail-Open + أدوار `(البداية)`/`(استئناف k)`/`(🌟 الحساب المنجز)` + السطر المدمج `⏱️ إجمالي زمن التوليد: X (N حسابات منتجة | 🔁 M استئناف)` (الإجمالي من المفلتر فقط، العداد من `last_credit_continuations` حصرياً — عقد P30 `Resume ≠ Accounts−1` باقٍ) + `🕒 الزمن الكلي` بلا مساس. — دليل: `TestProductiveFilter` + `TestTimingBlockNew`.
- [x] **`[TSK-5502]`** تنظيف `res_msg` (p11): حذف 6 عناصر — `latest_line` (🧷) + `resume_line` (🔗) + `fork_line` (🔀) + `📁 مسار الساندبوكس` + `🏁 علم الانتهاء` مع استدعاء `is_finished` اليتيم (الدالة `check_project_finished_flag` باقية في p05 بحراسها) + حقن `journey_block` (الدالة `format_account_journey_line` باقية — عقد P38 صار `📧 الحساب: {acc_email}` بلا journey_block) + التسجيل الجنائي: القائمة الكاملة غير المفلترة ➔ `log_event("info", "[P39] ...")` قبل الإرسال (best-effort داخل try/except صامت). بطاقات handoff واللقطة **خارج النطاق عمداً** (Root/Latest مختلفان فعلياً لحظة الـ fork). — دليل: `TestResMsgCleanup` + `TestForensicLogging`.
- [x] **`[TSK-5503]`** الحراسة والمواءمة: حزمة `tests/test_p39_completion_ux_streamlining.py` (**46 حارساً** — 5 مجموعات: الفلتر النقي/الكتلة الجديدة/نظافة res_msg بالمصدر/Zero-Breaking/HTML وحواف) + تحديث واعٍ للقدامى (p30 عناوين وأدوار / p29 `test_final_message_uses_journey_block` صار عقد إلغاء الحقن / p38 الحرفية بلا journey_block) + PARTS boundaries (الملف الآن **7873 سطراً**: p03 ➔ 460–1084 «+63» / إزاحة p04..p10 / p11 ➔ 6233–6613 / p12 ➔ 6614–7873) + إعادة توليد `bridge_refactor/` (parity **11/11** ✅) + بوابة `hadith_sijil.py` = **807/807 PASS Exit Code 0** + التوثيق الشامل (هذا الملف + PROGRESS الجذري + SESSION_LOG DEC-034 + TEST_SUITE_CATALOG + README + V3_RESUME). — دليل: Gate 807/807 + هذا الـ commit.
- [x] **`[TSK-5504]`** نظافة git (المرات 26–29): إخراج `.pytest_cache/` و `bridge_bot.log` من التتبع بعد أن أعادتهما المزامنة التلقائية (الموافقة الدائمة من S41). — دليل: `TestGeneratedFilesUntracked` PASS.

---

## 🏛️ S61 — التدقيق المعماري الشامل والتوليف التاريخي Full Architectural Audit & Historical Synthesis (2026-08-23)

> **طلب المالك:** مراجعة معمارية شاملة للملفات الثلاثة (`01.33_telegram_gen_bridge.py` 7873 سطراً + `01.03Genspark_claude-opus-5-code.py` + `qwen_engine.py`) — دوال مكررة/محجوبة، استثناءات عارية، تعارض ثوابت، parity المرايا — مع توليف تاريخي كامل (TSK-101 ➔ P39) في وثيقة واحدة.

- [x] **`[TSK-5601]`** التدقيق الآلي (AST): صفر دوال مكررة/محجوبة (module-level + methods + nested) + صفر `except:` عارٍ + صفر تعارض ثوابت (`MODEL_DECLINE_MARKERS`/`MODEL_DECLINE_MAX_RESPONSE_CHARS` متطابقة حرفياً بين `01.33` و`01.03` — قاعدة «الملفين معاً» P36 سليمة) + الـ 47 كتلة `except Exception: pass` رُوجعت وكلها Fail-Safe مقصودة + صفر mutable default args + parity 11/11. — دليل: قسم (ب) في وثيقة التدقيق.
- [x] **`[TSK-5602]`** إصلاحان ذريان Zero-Regression: (1) `440630e` — نظافة git (المرة 30): إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع (موافقة S41). (2) `3423b1d` — إزالة إعادة تعريف `_DIR` المكررة في `01.03` (سطر 300 — نفس القيمة بايتاً ببايت، أُبقي التعريف الأول سطر 154 حصرياً + تعليق تدقيقي). — دليل: بوابة 807/807 + Exit 0 بعد كل إصلاح.
- [x] **`[TSK-5603]`** وثيقة `docs/engineering/FULL_ARCHITECTURAL_AUDIT_REPORT.md`: ملخص زمني شامل (TSK-101 ➔ P39 بجدولي المراحل التأسيسية والنشطة) + نتائج التدقيق + جدول الإصلاحات + 6 توصيات مستقبلية BLOCKED-ON-OWNER + بوابة الجودة الختامية. — دليل: حارس p10 (docs integrity) PASS.
- [x] **`[TSK-5604]`** مواءمة التوثيق: تحديث بانر `docs/engineering/README.md` المتقادم (01.29/Phase 18/«32 فحصاً»/أمر unittest القديم ➔ 01.33/Phase 39/807/pytest+hadith_sijil + رابط وثيقة التدقيق) + تصحيح عدادات `V3_RESUME_SESSION.md` (761 ➔ 807) + نقطة استئناف S61 في PROGRESS الجذري + هذا القسم + SESSION_LOG (DEC-035). — دليل: بوابة 807/807 Exit 0 + هذا الـ commit.
- [x] **`[TSK-5605]`** نظافة git (المرة 31): إخراج `.pytest_cache/`+`bridge_bot.log` من التتبع بعد أن أعادتهما المزامنة التلقائية مجدداً (موافقة S41 الدائمة). — دليل: `TestGeneratedFilesUntracked` PASS.

---

## ⚡ P40 / S65 — المدة المضغوطة ومسار الرفض السريع بالجسر Compact Time UX & Bridge Decline Fast-Path

> **طلب المالك (`Deep_Thinking_Tasks_Remaining.TXT` — PHASE 40):** إثبات سبب تأخر رسالة Telegram بعد اكتشاف `is_model_decline_response` + وثيقة `14_DECLINE_FAST_PATH_LATENCY.MD` قبل تعديل الكود + Compact Duration (45s / 12m 17s / 1h 5m) + Decline Fast-Path بلا تعطيل Success / Resume / Rotation.

- [x] **`[TSK-5701]`** الإثبات والوثيقة: السبب المثبت — الجسر `01.33` (بخلاف المحرك بعد P36) كان يكمل `download_project_archive` (15–40ث لأرشيف مرفوض لن يُستخدم) + `make_project_always_public` قبل إرسال رسالة الرفض. الأدلة الحرفية بأرقام الأسطر في `14_DECLINE_FAST_PATH_LATENCY.MD` (أُنشئت **قبل** أي تعديل كود). — دليل: DEC-036.
- [x] **`[TSK-5702]`** Compact Duration (p03): `format_compact_duration(seconds)` top-level بيافطة `[P40]` (45s / 12m 17s / 1h 5m — بلا أصفار حشو + سالب/None/تالف ➔ 0s بلا Crash) مستبدلة في المواضع الثلاثة لكتلة P39 حصرياً (سطر الحساب ⏱ + ⏱️ الإجمالي + 🕒 الزمن الكلي) — `format_arabic_duration` باقية محروسة (عقد P30). — دليل: حراس الصيَغ والحدّيات في `test_p40`.
- [x] **`[TSK-5703]`** Decline Fast-Path (p06): `_declined` يُحسب في `send_message_and_make_public` فور اكتمال البث وقبل المسارات المكلفة — تخطي الأرشيف + make_public + الرابط المباشر بلا شبكة، مع `save_project_branch` **بلا حراسة عمداً** (السجل دائماً) وعقد P35 (إعادة التصنيف بالـ worker) بلا مساس. — دليل: عقود Fast-Path المصدرية + Zero Breaking في `test_p40`.
- [x] **`[TSK-5704]`** الحراسة والمواءمة: `tests/test_p40_compact_time_decline_fastpath.py` (**26 حارساً**) + PARTS boundaries (الملف **7905 أسطر**: p03 ➔ 460–1105 / p06 ➔ 1913–2922 / p12 ➔ 6646–7905) + إعادة توليد `bridge_refactor/` (parity **11/11** ✅) + بوابة `hadith_sijil.py` = **833/833 PASS Exit Code 0** + التوثيق الشامل (هذا الملف + PROGRESS الجذري + SESSION_LOG DEC-036 + TEST_SUITE_CATALOG + README الجذري وengineering + V3_RESUME قاعدة P40 الدائمة). — دليل: Gate 833/833 + هذا الـ commit.
- [x] **`[TSK-5705]`** نظافة git (المرة 35): إخراج `.pytest_cache/` و `bridge_bot.log` من التتبع بعد أن أعادتهما المزامنة التلقائية مجدداً (الموافقة الدائمة من S41). — دليل: `TestGeneratedFilesUntracked` PASS.

---

## 🧭 P41 / S66 — التوجيه الجنائي لروابط المشاريع والإغلاق النظيف Forensic Project URL Routing & Graceful Polling Shutdown

> **طلب المالك (`Deep_Thinking_Tasks_Remaining.TXT` — PHASE 41):** التحقيق الجنائي في فك وتوجيه روابط المشاريع (Zero Context Collision — منع Cross-Project Context Hijacking) + الخروج النظيف الفوري بـ Ctrl+C (requests النقية لحلقة getUpdates + sys.exit(0) بلا Traceback) + وثيقة `15_PROJECT_ROUTING_AND_CLEAN_SHUTDOWN.MD` **قبل** الكود.

- [x] **`[TSK-5801]`** الوثيقة والفحص الجنائي (Checkpoints 0↔2): Baseline 833/833 Exit 0 + INSPECT محور A (نقاط التصادم: فرعا `AWAITING_NEW_PROMPT`/`AWAITING_CONT_PROMPT` كانا يجدولان أي نص فوراً حتى لو كان رابط مشروع آخر) + INSPECT محور B (سبب ابتلاع Ctrl+C: `except Exception` عامة داخل الحلقة + عميل curl_cffi في getUpdates يرمي CFFI error / curl: (23) على ويندوز) + FIX DESIGN كامل بالوثيقة قبل أي تنفيذ. — دليل: `15_PROJECT_ROUTING_AND_CLEAN_SHUTDOWN.MD` (كل الـ Checkboxes محسومة).
- [x] **`[TSK-5802]`** توجيه الروابط (Checkpoint 3A — commit `8fc9bc5`): `MALFORMED_PROJECT_LINK_MESSAGE` + `parse_project_locator` (Parsing SSOT — كل صيغ الروابط) + `detect_context_collision` + `handle_prompt_context_collision` **أول سطر** في فرعي البرومبت قبل أي `EXECUTOR.submit` — سياق (A) نشط + رابط (B) = إغلاق السياق وتوجيه الرابط لمساره الشرعي: مسجّل ➔ بطاقة الملخص / غير مسجّل ➔ المسار الخارجي / مشوّه ➔ رفض صريح بلا Fallback صامت. — دليل: حراس التصادم والتوجيه في `test_p41`.
- [x] **`[TSK-5803]`** الإغلاق النظيف (Checkpoint 3B — commit `8fc9bc5`): عميل getUpdates داخل `run_telegram_polling` = `requests.Session()` النقية حصرياً (curl_cffi باقٍ بكل مسارات Genspark بلا تغيير) + إعادة رفع `KeyboardInterrupt`/`SystemExit` داخل الحلقة (لا تبتلعهما `except Exception`) + معالج خارجي برسالة إغلاق ⏹️ ثم `sys.exit(0)` بلا Traceback. — دليل: Source Contracts + Spies في `test_p41`.
- [x] **`[TSK-5804]`** الحراسة والمواءمة (Checkpoints 4↔5): `tests/test_p41_routing_and_graceful_shutdown.py` (**50 حارساً** — إصلاح صياغة 4 حراس مراسيهم الأولية خاطئة والكود سليم) + الملف **8008 أسطر** (+103) + إعادة توليد `bridge_refactor/` (parity **11/11** ✅) + بوابة `hadith_sijil.py` = **883/883 PASS Exit Code 0** + التوثيق الشامل (هذا الملف + PROGRESS الجذري + SESSION_LOG DEC-037 + TEST_SUITE_CATALOG + README الجذري وengineering + V3_RESUME قاعدة P41 الدائمة + وثيقة 15 + تحديث البند 7). — دليل: Gate 883/883 + هذا الـ commit.
- [x] **`[TSK-5805]`** نظافة git (المرات 36–38): إخراج `.pytest_cache/` و `bridge_bot.log` من التتبع بعد أن أعادتهما المزامنة التلقائية مجدداً (الموافقة الدائمة من S41). — دليل: `TestGeneratedFilesUntracked` PASS.

---

## 🛡️ P42 / S67–S68 — حارس النية وتدفق الإنشاء الآمن Intent Guard & Safe Project Creation Flow

> **طلب المالك (`Deep_Thinking_Tasks_Remaining.TXT` — PHASE 42):** إغلاق Live Bug «الإنشاء الأعمى» — أي نص عابر في الخمول («2+7=» / «63636» / «121») كان ينشئ مشروعاً ويحجز حساباً ويبدأ توليداً بلا إذن. المبدأ الحاكم: **Confirmation before ANY Mutation** — وفق وثيقة `16_INTENT_GUARD_AND_SAFE_CREATION.MD` (كُتبت قبل الكود — INSPECT FIRST) وقرار DEC-038.

- [x] **`[TSK-5901]`** الوثيقة والفحص الجنائي (Checkpoints 0↔2 — S67): نظافة git المرة 40 + Baseline 883/883 Exit 0 + INSPECT الـ Fallback (أسطر 7917–7921 آنذاك) + الحدود الأمنية الخمسة بأرقام الأسطر (6362/6363/6368+6374/6526➔2678➔529) + FIX DESIGN كامل (Flow + جدول قبل/بعد + Edge Cases التسعة بقرار موثق لكل منها) بالوثيقة قبل أي تنفيذ. — دليل: `16_INTENT_GUARD_AND_SAFE_CREATION.MD` §1–§4.
- [x] **`[TSK-5902]`** الحارس والحالة (Checkpoint 3A — S68): حذف الـ Fallback واستبداله حرفياً بـ `handle_idle_intent_guard` (8123–8125) + كتلة P42 كاملة (6702–6815: الثوابت top-level + `classify_idle_intent` Strong/Ambiguous للصياغة فقط + بطاقة تقتبس النص حرفياً + nonce 12-hex في callback_data والنص في `pending_prompt`) + حالة `AWAITING_PROJECT_CONFIRMATION` في سلسلة النص (Edge 6: أمر/رابط P41 يفوزان والبطاقة تُبطل). — دليل: حراس SourceStructure + CardInvalidation في `test_p42`.
- [x] **`[TSK-5903]`** الـ Callbacks والتمرير الذكي (Checkpoint 3B — S68): معالج `pconf:*` معزول مبكراً بنمط P25/P26 (تأكيد ➔ `AWAITING_NEW_PROJECT_NAME` القائمة — DRY صفر Wizard موازٍ / إلغاء ➔ صفر أثر / Stale nonce ➔ انتهت الصلاحية / Double-Click ➔ Idempotent عبر `consumed_confirm_nonce`) + نقل `pending_prompt` عبر خطوة الاسم + `forward_pending_prompt_after_wizard` في موضعي finalize (البرومبت ينطلق تلقائياً على المشروع الشرعي) + Telemetry 🛡️ [P42] SHOWN/CONFIRMED/CANCELLED/EXPIRED/DUPLICATE. — دليل: حراس ConfirmCallback + SmartPromptForwarding (E2E).
- [x] **`[TSK-5904]`** الحراسة والمواءمة (Checkpoints 4↔5): `tests/test_p42_intent_guard_and_safe_creation.py` (**63 حارساً** في 10 مجموعات — منها Zero-Mutation بـ Spies على الحدود الخمسة + الرسائل غير النصية + Zero-Regression لعقود P41/P32/P25-P26 والإنشاء الصريح) + الملف **8212 سطراً** (+204) + إعادة توليد `bridge_refactor/` (parity **11/11** ✅) + بوابة `hadith_sijil.py` = **946/946 PASS Exit Code 0** + التوثيق الشامل (هذا الملف + PROGRESS الجذري + SESSION_LOG DEC-038 + TEST_SUITE_CATALOG + README + V3_RESUME قاعدة P42 الدائمة + وثيقة 16 §5 + تحديث البند 7). — دليل: Gate 946/946 + هذا الـ commit.
- [x] **`[TSK-5905]`** نظافة git (المرتان 40–41): إخراج `.pytest_cache/` و `bridge_bot.log` من التتبع بعد أن أعادتهما المزامنة التلقائية مجدداً (الموافقة الدائمة من S41). — دليل: `TestGeneratedFilesUntracked` PASS.

---

## ⚡ P43 / S69–S71 — الوضع السريع وتخطي تنزيل الملفات والـ Diff — Fast Lean Mode & Artifacts/Diff Bypass

> **طلب المالك (`Deep_Thinking_Tasks_Remaining.TXT` — PHASE 43):** كل مشروع — حتى غير المربوط بـ GitHub — كان يمر بعد اكتمال الموديل بـ `download_project_archive` (timeout 180s) + فك ضغط + `registry.snapshot` (sha256 لكل ملف + Diff) بلا حاجة فعلية. وفق وثيقة `17_FAST_LEAN_MODE_AND_ARTIFACTS_BYPASS.MD` (SSOT بقرارات المالك D1–D7 + الأدلة الجنائية F1–F13 — كُتبت قبل الكود) وقرار DEC-039.

- [x] **`[TSK-6001]`** الفحص والقياس (CP0–CP1): Baseline 946/946 (+12 subtests) + Exit 0 + Parity 11/11 + إثبات مواضع F1–F13 بـ grep بلا انزياح + **قياس فعلي**: محاكاة snapshot 400 ملف/12MB ➔ 0.162s + Diff ➔ 0.054s ⇒ العبء المهيمن شبكي حصراً (التنزيل 180s + النشر 3×POST×15s) — لا أرقام سرعة إجمالية قبل قياس E2E حي (X3). — دليل: وثيقة 17 §CP0–CP1.
- [x] **`[TSK-6002]`** الـ Schema والدالة الحاكمة (CP2): حقل `fast_mode` واحد في `default_project_settings` (default=False — D5/R2، لا حقل ثانٍ/Invariant — R1) + `should_skip_artifacts_download(project_settings)` (D3: GitHub مفعّل ➔ تنزيل إلزامي يفوز دائماً) + Backward-Compat في `_normalize_project_settings` (المشاريع القديمة ➔ False) + `update_project_settings` (bool حصراً). — دليل: اختبارات 1–4.
- [x] **`[TSK-6003]`** الـ UI الثلاثي (CP3+CP5+CP6): (أ) زر ⚡/📦 `pset:fastmode:{key}` style=primary (D1) + المعالج داخل router الـ `pset:*` القائم (X5/R3 — لا `cmd:toggle_fast_mode` شبح)؛ (ب) زر «⬇️ تنزيل الساندبوكس الآن» `pctl:fetch:{key}` (D6) + `run_project_late_fetch` (Pipeline كامل بالدوال القائمة بلا نسخ + فشل صريح للجلسة المنتهية + Idempotent)؛ (ج) خطوة Wizard `build_new_project_fast_mode_keyboard` (D4 — تُعرض فقط عند تخطي GitHub) + معالجا `cmd:new_proj_fast_no/yes` + `pending_fast_mode` + حارس `and not github_enabled` في finalize + نجاة `pending_prompt` (تكامل P42). — دليل: اختبارات 5–6 + 12–15.
- [x] **`[TSK-6004]`** حقن التخطي بالـ worker (CP4): في `send_message_and_make_public` (p06): `skip_archive = _declined or fast_lean_skip` (**_declined أولاً** — الرفض يفوز ويتخطى النشر أيضاً، توسيع P40 الحرفي) + `archive_path=None` عند التخطي + **`make_project_always_public` تعمل في fast mode (D2)** + `save_project_branch` بلا حراسة (شجرة الاستئناف دائماً) + Telemetry `⚡ [P43] FAST_MODE_SKIP project=<key> pid=<pid16>` (D7) + الكارت الشفاف `fast_mode_line` («⚡ الوضع السريع — تم تخطي تنزيل الملفات والـ Diff» — لا إحصائيات Diff مزيفة). — دليل: اختبارات 7–11 (Spies على download/make_public + Zero-Regression بايت-ببايت).
- [x] **`[TSK-6005]`** الحراسة والمواءمة والبوابات (CP7–CP9): `tests/test_p43_fast_lean_mode.py` (**16 حارساً** — يختمها حارس عقود P40 المجمدة) + الملف **8422 سطراً** (+210) + تحديث حدود PARTS (p09➔4567–6186 / p10➔6187–6481 / p11➔6482–6868 / p12➔6869–8422) + إعادة توليد `bridge_refactor/` (parity **11/11** ✅) + بوابة pytest = **962/962 PASS** (946+16، +12 subtests) + `hadith_sijil.py` **Exit 0** + نظافة git (المرة 43) + التوثيق الشامل (PROGRESS الجذري + هذا الملف + SESSION_LOG DEC-039 + V3_RESUME + TEST_SUITE_CATALOG + README + وثيقة 17 محسومة بالكامل + البند 7 وبلوك ## 0). — دليل: Gate 962/962 + هذا الـ commit.
