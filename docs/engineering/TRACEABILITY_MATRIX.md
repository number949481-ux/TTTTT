# 🔗 مصفوفة التتبع والربط الهندسي (TRACEABILITY_MATRIX.md)

> **المسؤولية:** الجسر الرابط بين المتطلبات، الشفرات المصدرية، ملفات الاختبارات، والـ Git Commits  

---

## 📊 مصفوفة تتبع الإصدار الحالي النشط (01.25 Traceability Matrix)

| Feature ID | Task # | البيان الهندسي | Source File | Test File | Commit Hash | الحالة |
|:---:|:---:|---|---|---|:---:|:---:|
| **FEAT-GH-01** | `TSK-2401` | دعم Pagination فروع GitHub حتى 50 صفحة وإزالة التكرار | `01.24_telegram_gen_bridge.py` | `tests/test_p1_github_branches.py` | `8e5467e` | ✅ مغلقة |
| **FEAT-RT-02** | `TSK-2402` | دمج عقود الموديلات الـ 5 والـ Aliases وتوجيه Sol و Kimi | `01.24_telegram_gen_bridge.py` + المحرك | `tests/test_p2_model_routing.py` | `793e6fd` | ✅ مغلقة |
| **FEAT-RG-03** | `TSK-2403` | لقطات التراجع وحماية المسارات القديمة بالبايت | المحرك + البوت | `tests/test_p3_regression.py` | `f05f572` | ✅ مغلقة |
| **FEAT-UX-04** | `TSK-2404` | كتم إشعارات الأرشيفات الفنية الزائدة D-002 | `01.24_telegram_gen_bridge.py` | تحقق ميداني ووحدات | `22bcd3d` | ✅ مغلقة |
| **FEAT-UX-05** | `TSK-2405` | أزرار الفروع بنقرة واحدة (1-Click UI) وقائمة Monospace | `01.24_telegram_gen_bridge.py` | تحقق تفاعلي ووحدات | `b8c3358` | ✅ مغلقة |
| **FEAT-SK-06** | `TSK-2406` | مهارة حارس تجربة المستخدم `00-telegram-ux-guardian` | `.agents/skills/` و `.agents/workflows/` | مراجعة السلاش والدستور | `b8c3358` | ✅ مغلقة |
| **FEAT-DC-07** | `TSK-2407` | المعمارية المزدوجة للتوثيق (`docs/engineering/` + `docs/tests/`) | `docs/` | `python -m unittest discover tests -v` | `1b330e2` | ✅ مغلقة |
| **FEAT-PV-08** | `TSK-2501` | توثيق النطاق وتحديث الهيكل القياسي لـ `PROGRESS.md` ومهارة التوثيق | `docs/engineering/PROGRESS.md` + `.agents/` | مطابقة مع المرجع القياسي | `01.25` | ✅ مغلقة |
| **FEAT-PV-09** | `TSK-2502` | حزمة اختبارات الوحدة الـ 6 لـ P7-A في `tests/test_p7_live_preview.py` | `tests/test_p7_live_preview.py` | `tests/test_p7_live_preview.py` (6/6 PASS) | `01.25` | ✅ مغلقة |
| **FEAT-PV-10** | `TSK-2503` | إضافة `on_project_start_callback` في المحرك 01.02 | `01.02Genspark_claude-opus-5-code.py` | `tests/test_p7_live_preview.py` | `01.25` | ✅ مغلقة |
| **FEAT-PV-11** | `TSK-2504` | بطاقة المعاينة الفورية ودورة الرسالة المتطورة في البوت | `01.25_telegram_gen_bridge.py` | `tests/test_p7_live_preview.py` | `01.25` | ✅ مغلقة |
| **FEAT-DC-12** | `TSK-2505` | توليد الـ 10 وثائق لـ 01.25 والفحص الآلي الشامل بـ `hadith_sijil.py` | `docs/` + `scripts/hadith_sijil.py` | 31/31 PASS (Exit Code 0) | `01.25` | ✅ مغلقة |

---

## ♻️ مصفوفة تتبع P12 — Same-Project Resume (S31)

| Feature ID | Task # | البيان الهندسي | Source File | Test File | Commit Hash | الحالة |
|:---:|:---:|---|---|---|:---:|:---:|
| **FEAT-RS-13** | `TSK-3001..3003` | مهلة خمول tuple + حفظ pid عند الانقطاع + طباعة الرد كاملاً مع زمن التنفيذ | `01.03Genspark_claude-opus-5-code.py` | `tests/test_p12_resume_same_project.py` | `c3911d1` | ✅ مغلقة |
| **FEAT-RS-14** | `TSK-3004..3006` | carry_pid استئناف نفس المشروع + STREAM_INTERRUPTED→polling + زر معاينة فوري في الاستئناف | `01.26_telegram_gen_bridge.py` | `tests/test_p12_resume_same_project.py` | `c3911d1` | ✅ مغلقة |
| **FEAT-RS-15** | `TSK-3007..3010` | مراجعة P12-E (آخر رسالة assistant + return []) + 13 اختباراً + بروتوكول | البوت + المحرك + `docs/` | 69/69 PASS (Exit Code 0) | `c3911d1` | ✅ مغلقة |

---

## 💰 مصفوفة تتبع P13 — Pre-Flight Balance Check (S32)

| Feature ID | Task # | البيان الهندسي | Source File | Test File | Commit Hash | الحالة |
|:---:|:---:|---|---|---|:---:|:---:|
| **FEAT-BL-16** | `TSK-3101` | عتبة `min_preflight_balance = 100` في BridgeConfig | `01.26_telegram_gen_bridge.py` | `tests/test_p13_preflight_balance.py` | هذا الـ commit | ✅ مغلقة |
| **FEAT-BL-17** | `TSK-3102..3103` | بوابة الرصيد قبل أي fork/شات (< 100 → تبريد 29h + LOW_BALANCE) + إعادة الفحص بعد تجديد الجلسة | `01.26_telegram_gen_bridge.py` | `tests/test_p13_preflight_balance.py` | هذا الـ commit | ✅ مغلقة |
| **FEAT-BL-18** | `TSK-3104..3107` | التخطي الصامت في الـ failover + 14 اختباراً + تزامن bridge_refactor + بروتوكول | البوت + `docs/` | 83/83 PASS (Exit Code 0) | هذا الـ commit | ✅ مغلقة |

---

## 🔀 مصفوفة تتبع P14 — GitHub Upsert Sync (S33)

| Feature ID | Task # | البيان الهندسي | Source File | Test File | Commit Hash | الحالة |
|:---:|:---:|---|---|---|:---:|:---:|
| **FEAT-US-19** | `TSK-3203` | Upsert Copy: مقارنة محتوى (بايت + CRLF→LF) قبل النسخ — الموجود+المعدل يظهر `✏️ M` وليس `➕ A`، والمطابق لا يُلمس | `04_upload_to_Fable_github.py` | `tests/test_p14_upsert_sync.py` | هذا الـ commit | ✅ مغلقة |
| **FEAT-US-20** | `TSK-3201, TSK-3204` | حارس الحذف المرآتي: `would_delete` تُجمَّع أولاً؛ نسبة > 50% من ملفات الريبو = أرشيف جزئي ➔ إلغاء الحذف بالكامل (حماية سيناريو saray2and2) | `04_upload_to_Fable_github.py` | `tests/test_p14_upsert_sync.py` | هذا الـ commit | ✅ مغلقة |
| **FEAT-US-21** | `TSK-3202` | كشف جذر ذكي Repo-Anchored (`detect_best_source_root` حتى عمق 3) بعد `git clone` مع fallback للسلوك القديم | `04_upload_to_Fable_github.py` | `tests/test_p14_upsert_sync.py` | هذا الـ commit | ✅ مغلقة |
| **FEAT-US-22** | `TSK-3205..3206` | 16 اختبار حراسة + تحديث ملفات البروتوكول الخمسة | `tests/` + `docs/` | 99/99 PASS (Exit Code 0) | هذا الـ commit | ✅ مغلقة |

---

## 🚀 مصفوفة تتبع P15 — إصدار 01.27 + استقلال محرك كوين + التدقيق الشامل (S34)

| Feature ID | Task # | البيان الهندسي | Source File | Test File | Commit Hash | الحالة |
|:---:|:---:|---|---|---|:---:|:---:|
| **FEAT-QE-23** | `TSK-3301` | ترقية الإصدار `01.26 ➔ 01.27` ببانر جديد (P12+P13+P14) + تحديث كل مراجع scripts/tests + إزاحة PARTS (+3) + إعادة توليد `bridge_refactor/` بتطابق بايت | `01.27_telegram_gen_bridge.py` | `tests/test_refactor_parity.py` + `tests/test_p15_qwen_engine.py` | `706f3aa` + هذا الـ commit | ✅ مغلقة |
| **FEAT-QE-24** | `TSK-3302` | موديول `qwen_engine.py` المستقل (946 سطراً): سلسلة الموديلات + سباق `_qwen_worker`/`qwenguest_worker`/`race_accounts` + شريط تقدم ملون + `auto_refresh_qwen_account` + `_save_qwen_winner_cookies` تحت `_QWEN_FILE_LOCK` + `generate_ai_summary` — بحقن لوجر `configure` وحالة فائز حية `qwen_engine.LAST_AI_*` | `qwen_engine.py` + `04_upload_to_Fable_github.py` | `tests/test_p15_qwen_engine.py` | `706f3aa` | ✅ مغلقة |
| **FEAT-QE-25** | `TSK-3303` | تدقيق شامل Zero-Regression على 6 محاور (ستريم دفعة واحدة / معاينة حية مبكرة / أزرار whitelist / P13 / P14 / P15) = 25/25 فحصاً | البوت + المحرك + `04` | سكربت تدقيق آلي + 115/115 PASS | هذا الـ commit | ✅ مغلقة |
| **FEAT-QE-26** | `TSK-3304..3306` | 16 اختبار حراسة P15 + بوابة Exit Code 0 + تحديث ملفات البروتوكول الخمسة | `tests/` + `docs/` | 115/115 PASS (0.440s, Exit Code 0) | هذا الـ commit | ✅ مغلقة |

---

## 🎯 معيار القبول والإغلاق (Done Definition)
لا تُعتبر أي مهمة مغلقة `✅` في هذه المصفوفة إلا بعد استيفاء الشروط الثلاثة:
1. وجود شفرة مصدرية حقيقية في الـ Source File.
2. وجود فحص آلي ناجح في الـ Test File يخرج بـ Exit Code 0.
3. وجود Git Commit فعلي يوثق الحالة في الـ Version Control.


---

## 🌍 مصفوفة تتبع P16 — النشر العام المبكر Early Make-Public (S35)

| Feature ID | Task # | البيان الهندسي | Source File | Test File | Commit Hash | الحالة |
|:---:|:---:|---|---|---|:---:|:---:|
| **FEAT-EP-27** | `TSK-3401` | `_early_make_public`: استدعاء `make_public` بخيط daemon فور التقاط الـ pid في 3 مسارات (بث SSE / استئناف carry_pid / fork بالـ URL) | `01.28_telegram_gen_bridge.py` ➔ `01.29` | `tests/test_p16_early_public.py` | هذا الـ commit | ✅ مغلقة |
| **FEAT-EP-28** | `TSK-3402` | حراسات: dedup لكل pid + تجاهل sentinels + snapshot كوكيز معزول + بانر 01.28 | `01.28_telegram_gen_bridge.py` ➔ `01.29` | `tests/test_p16_early_public.py` (9/9) | هذا الـ commit | ✅ مغلقة |

---

## 🛡️ مصفوفة تتبع P17 — التصليب التشغيلي Hardening (S36)

| Feature ID | Task # | البيان الهندسي | Source File | Test File | Commit Hash | الحالة |
|:---:|:---:|---|---|---|:---:|:---:|
| **FEAT-HD-29** | `TSK-3501` | بوابة الجلسة المنتهية: `SESSION_EXPIRED` أثناء الشات = تجديد فوري بدل حرق المحاولة | `01.29_telegram_gen_bridge.py` | `tests/test_p17_hardening.py::TestExpiredSessionGate` | هذا الـ commit | ✅ مغلقة |
| **FEAT-HD-30** | `TSK-3502` | بوابة الرصيد أثناء الشات: كشف `CREDIT_EXHAUSTED` داخل حلقة polling | `01.29_telegram_gen_bridge.py` | `tests/test_p17_hardening.py::TestMidChatBalanceGate` | هذا الـ commit | ✅ مغلقة |
| **FEAT-HD-31** | `TSK-3503` | دعم الجروبات: `is_chat_allowed` يقبل group/supergroup ids السالبة | `01.29_telegram_gen_bridge.py` | `tests/test_p17_hardening.py::TestGroupChatSupport` | هذا الـ commit | ✅ مغلقة |
| **FEAT-HD-32** | `TSK-3504` | تكامل كوين للـ commits + نظافة المستودع (`.pytest_cache/` و `bridge_bot.log` خارج التتبع) | `04` + `.gitignore` | `tests/test_p17_hardening.py` (27/27) | هذا الـ commit | ✅ مغلقة |

---

## ⛳ مصفوفة تتبع P18 — الوقف الفوري عند تغيّر مؤشر النشاط (S37)

| Feature ID | Task # | البيان الهندسي | Source File | Test File | Commit Hash | الحالة |
|:---:|:---:|---|---|---|:---:|:---:|
| **FEAT-AS-33** | `TSK-3601` | إصدار `01.29` ببانر P18 + `BUILD_VERSION = "01.29"` | `01.29_telegram_gen_bridge.py` | `tests/test_p18_activity_stop.py` | هذا الـ commit | ✅ مغلقة |
| **FEAT-AS-34** | `TSK-3602..3603` | `extract_activity_signature` + `fetch_project_activity_signature` (فشل الجلب = None يُتجاهل) | `01.29_telegram_gen_bridge.py` | `TestExtractActivitySignature` | هذا الـ commit | ✅ مغلقة |
| **FEAT-AS-35** | `TSK-3604` | `should_stop_on_activity_change`: **أي تغيّر في Tasks Remaining (زيادة أو نقصان) أو تقلّب Deep Thinking أو اختفاء المؤشر = وقف فوري بلا تكملة** | `01.29_telegram_gen_bridge.py` | `TestShouldStopOnActivityChange` (يشمل النقصان) | هذا الـ commit | ✅ مغلقة |
| **FEAT-AS-36** | `TSK-3605..3606` | تكامل حلقة polling (baseline ➔ فحص كل دورة ➔ `break` فوري) + مواءمة scripts/tests/bridge_refactor + بوابة 171/171 | البوت + `scripts/` + `tests/` | `TestPollingLoopIntegration` + Gate 171/171 Exit 0 | هذا الـ commit | ✅ مغلقة |

---

## 📋 مصفوفة تتبع P19 — نسخ إعدادات مشروع آخر + الترقيم التسلسلي (S38)

| Feature ID | Task # | البيان الهندسي | Source File | Test File | Commit Hash | الحالة |
|:---:|:---:|---|---|---|:---:|:---:|
| **FEAT-CS-37** | `TSK-3701` | إصدار `01.30` ببانر P19 + `BUILD_VERSION = "01.30"` — مع نقل P18 (Activity-Stop) بتطابق حرفي | `01.30_telegram_gen_bridge.py` | `tests/test_p19_copy_settings.py::TestP19VersionBump` + 20 اختبار P18 على 01.30 | هذا الـ commit | ✅ مغلقة |
| **FEAT-CS-38** | `TSK-3702` | `generate_sequential_project_name`: «الحج 1» موجود ➔ «الحج 2» (أعلى رقم مستخدم + 1) | `01.30_telegram_gen_bridge.py` | `TestSequentialProjectName` | هذا الـ commit | ✅ مغلقة |
| **FEAT-CS-39** | `TSK-3703` | `copy_project_settings_to_new_project`: نسخ GitHub repo/branch/token (مخزن المشروع فقط `allow_env_fallback=False`) + الموديل + برومبت الاستئناف | `01.30_telegram_gen_bridge.py` | `TestCopyProjectSettings` | هذا الـ commit | ✅ مغلقة |
| **FEAT-CS-40** | `TSK-3704` | واجهة تيليجرام: زر «📋 نسخ إعدادات من مشروع آخر» + لوحة `cpysrc:` + الملخص + 3 callbacks | `01.30_telegram_gen_bridge.py` | `TestCopySettingsKeyboard` + `TestHandlersIntegration` | هذا الـ commit | ✅ مغلقة |
| **FEAT-CS-41** | `TSK-3705..3706` | حزمة 24 اختباراً + مواءمة scripts/tests/bridge_refactor بتطابق بايت + بوابة 195/195 | البوت + `scripts/` + `tests/` | `tests/test_p19_copy_settings.py` (24/24) + Gate 195/195 Exit 0 | هذا الـ commit | ✅ مغلقة |
