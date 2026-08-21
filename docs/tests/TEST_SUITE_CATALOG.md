# 🧪 كتالوج حالات واختبارات الوحدة (TEST_SUITE_CATALOG.md)

> **الكتالوج الشامل:** يوثق الـ 164 فحصاً التاريخية التراكمية للمشروع + الـ **295 فحصاً النشطة محلياً** لإصدار `01.32`  
> **حالة الاختبارات النشطة:** 295/295 PASS (100% OK) — بوابة `hadith_sijil.py` بـ Exit Code 0 ⚡  

## 📊 0. المصفوفة النشطة الحالية — 01.32 (295 فحصاً / 19 ملفاً)

| الحزمة | الملف | العدد | النطاق |
|---|---|:---:|---|
| P1 فروع GitHub | `test_p1_github_branches.py` | 4 | Pagination + الفرع الافتراضي |
| P2 توجيه الموديلات | `test_p2_model_routing.py` | 8 | عقود الموديلات الـ 5 + Aliases |
| P3 لقطات التراجع | `test_p3_regression.py` | 12 | تطابق بايتات الحمولات القديمة |
| P7 المعاينة الحية | `test_p7_live_preview.py` | 10 | زر لايف + حارس UX |
| P10 تكامل التوثيق | `test_p10_docs_integrity.py` | 1 | فحص 32 ملف docs + الروابط |
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
| **P25 الإلغاء التفاعلي** | `test_p25_interactive_cancel.py` | **40** | **مسجل أحداث الإلغاء (توكن 12-hex + Lock) + زر 🛑 بخطوتي أمان + قطع بث SSE تعاوني (`__USER_CANCELLED__` قبل تصنيف الرصيد + `r.close()`) + `Event.wait(5)` + `CANCELLED` بلا عقوبة + Zero Leaks في `finally`** |
| Parity المرآة | `test_refactor_parity.py` | 11 | تطابق بايت bridge_refactor مع 01.32 |
| **الإجمالي** | **19 ملفاً** | **295** | ✅ 295/295 PASS |


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


