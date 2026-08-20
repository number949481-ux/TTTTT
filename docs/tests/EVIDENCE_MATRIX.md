# 📊 مصفوفة الأدلة وإثبات عدم كسر الموديلات (EVIDENCE_MATRIX.md)

> **المسؤولية:** توثيق الأدلة الميدانية، ثبات الـ Payloads، وتأكيد حماية المسارات  

---

## 🔍 1. مصفوفة أدلة حماية الموديلات (Model Evidence Matrix)

| الموديل | مسار المعالجة | الحالة قبل 01.24 | الحالة بعد 01.24 | نوع الدليل | نتيجة التحقق |
|---|---|---|---|---|:---:|
| `gpt-5.5` | مسار محمي خاص | شغال ومستقر | لا يوجد أي مساس بالبايتات | `test_gpt55_payload_byte_identical` | ✅ PASS |
| `claude-opus-4-8` | مسار محمي خاص | شغال ومستقر | لا يوجد أي مساس بالبايتات | `test_opus48_payload_byte_identical` | ✅ PASS |
| `claude-fable-5` | محول العقود العام | غير موجه | موجه لـ `gpt-4.1` hardcoded | `test_fable_models_is_gpt41_hardcoded` | ✅ PASS |
| `claude-opus-5-code` | محول العقود العام | افتراضي | بدون `ai_chat_model` | `test_opus5_has_no_ai_chat_model` | ✅ PASS |
| `claude-sonnet-5` | محول العقود العام | افتراضي | يحتوي على المفتاحين معاً | `test_sonnet5_has_both_use_and_ai_chat` | ✅ PASS |
| `gpt-5.6-sol` | محول العقود العام | افتراضي | موجه لمعايير Sol | `test_gpt56_sol_contract` | ✅ PASS |
| `kimi-k3` | محول العقود العام | افتراضي | موجه لمعايير Kimi | `test_kimi_k3_contract` | ✅ PASS |
| `Ultra Mode` | مسار الوضع الفائق | شغال ومستقر | ثابت دون أي تغيير | `test_ultra_flag_untouched_by_adapter` | ✅ PASS |

---

## 📱 2. مصفوفة أدلة واجهة التيليجرام (Telegram UI Evidence Matrix)

| الميزة | السلوك القديم | السلوك الجديد في 01.24 | الدليل في الكود | حالة الفحص |
|---|---|---|---|:---:|
| **عرض الفروع المكتشفة** | سطر نصي ملزق بجانب بعض | قائمة عمودية بنقاط `<code>` قابلة للنسخ بنقرة واحدة | دالة `format_github_repo_inspection_summary` | ✅ تم التحقق |
| **اختيار الفرع** | إدخال يدوي بالنسخ والكتابة | زرار تفاعلي مستقل لكل فرع (`🌿 <branch>`) | لوحات مفاتيح `build_*_branch_choice_keyboard` | ✅ تم التحقق |
| **إشعارات سياسة الأرشيفات D-002** | رسالة فنية طويلة ومزعجة في شات البوت | كتم الرسالة تماماً وحفظ الملف محلياً بهدوء | دالة `describe_archive_delivery` | ✅ تم التحقق |
