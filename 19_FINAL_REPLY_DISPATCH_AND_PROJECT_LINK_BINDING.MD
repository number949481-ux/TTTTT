# ⚡️ PHASE 45 — FINAL REPLY TELEGRAM DISPATCH & DYNAMIC PROJECT LINK BINDING (DEC-041)
# ══════════════════════════════════════════════════════════════════════════════════════
# وثيقة المواصفات الهندسية الرسمية والتشخيص الجنائي لمشاكل التجربة الحية في التليجرام
# ══════════════════════════════════════════════════════════════════════════════════════

## 📌 1. الهوية ونطاق المرحلة
- **المرحلة:** PHASE 45 (DEC-041)
- **الهدف:** القضاء الجذري على مشكلتين تم رصدهما في التجربة الحية للبوت:
  1. **[B1] سقوط إرسال نص الرد الختامي للتليجرام:** الموديل ينتهي من كتابة الرد ويُطبع في التيرمينال، لكن لا يتم إرسال رسالة نصية للمستخدم في التليجرام.
  2. **[B2] إعادة إرسال الرابط/السياق القديم عند الاستئناف:** عند تدوير الحسابات (`Fetch & Forward`) يتم استخدام رابط المشروع الأول وسياقه القديم بدلاً من ربط رابط وسياق المشروع السحابي الجديد.
- **الملف المستهدف بالتعديل:** `01.33_telegram_gen_bridge.py` حصرياً (Single-File Doctrine).
- **المجمّدات (Scope Freeze):** المحرك `01.03` (READ-ONLY) + عقود `P20` (Data Retention) + `P35/P40/P18` (Decline & Activity Gate).

---

## 🔍 2. التشخيص الجنائي من واقع اللوج الحي (Forensic Evidence)

### 🔴 العرض الأول (B1): طباعة الرد في التيرمينال وغيابه عن التليجرام
```text
  🧠 Fetch & Forward (Fork=False): 10 رسالة قديمة + رسالتك
  ⏳ بيفكر...
  ┌─ الرد ─────────────────────────────────────────────┐
  │ يا زيزو، البشارة الحلوة: **المهمة دي جاهزة بالفعل ومتحققة** 🎯 — البرومبتات موّلدة ومصححة وموجودة في `.connect/agents/GSK/T-V02-001_DISPATCH_PROMPTS.md`. خليني أتأكد إن كل حاجة سليمة وأجيبلك النسخة النهائية:
  └────────────────────────────────────────────────────┘
  ⏱️ اخد 18.5 ثانية
```
- **الملاحظة:** الرد طُبع بالكامل في التيرمينال بعد 18.5 ثانية، لكن التليجرام استلم كارت البناء فقط (`⚡ بدأ بناء المشروع السحابي فوراً!`) ولم تصله أي رسالة نصية تحتوي على هذا الرد!
- **السبب الجذري:** 
  1. دالة `fetch_final_reply_text` تجلب النص وتطبعه، لكن خط أنابيب الإرسال للتليجرام (`send_message` أو `notify_final_reply`) معلّق بشرط اكتمال صامت، أو يسقط بسبب خطأ في الـ Markdown Parse Mode (Unescaped characters) دون عمل Fallback إلى Plain Text!
  2. عدم وجود صمام أمان يضمن أن أي نص يُطبع في التيرمينال داخل المربع يجب إرساله حتماً كـ Telegram Message.

---

### 🔴 العرض الثاني (B2): تكرار رابط وسياق أول تشغيلة عند التدوير
```text
  [l.o***@googlemail.com] تجربة حساب (11/50) | Profile: safari15_5
  [l.o***@googlemail.com] 🌐 [P16] المشروع 8d0ed94f-f97… أصبح Public مبكراً
  🧠 Fetch & Forward (Fork=False): 10 رسالة قديمة + رسالتك
```
- **الملاحظة:** الحساب الجديد رقم 11 أنشأ مشروعاً جديداً ID `8d0ed94f...`، لكنه قام بعمل Forward للرابط القديم والرسائل العشر السابقة من المشروع الأصلي الأول، ولم يقم بتحديث الرابط التشغيلي النشط في الـ State.
- **السبب الجذري:**
  1. مصفوفة الـ `project_url` وسياق الـ `continuation_prompt` لا يتم تحديثها بالرابط الجديد المتولد على الحساب البديل لحظة الـ `Public / Creation`.
  2. غياب الـ Dynamic Project URL Re-binding عند الانتقال لحساب جديد.

---

## 🏛️ 3. القرارات المعمارية (Architectural Decisions)

### 💎 [D1] الإرسال الحتمي للرد الختامي مع الحماية المزدوجة (Guaranteed Final Dispatch & Fallback):
- بمجرد جلب الرد النهائي (`fetch_final_reply_text`) وثباته، يتم استدعاء دالة إرسال التليجرام فوراً.
- تفعيل **حماية التليجرام المزدوجة (Markdown Failover to Plain Text):**
  - المحاولة 1: إرسال بـ `parse_mode="Markdown"`.
  - المحاولة 2 (عند حدوث Telegram API Error 400 Bad Request بسبب الرموز): إرسال فوري لنفس النص بدون `parse_mode` كـ Plain Text مضمون 100%.
- تجزئة الرسائل الطويلة تلقائياً (إذا زادت عن 4000 حرف) إلى مقاطع لضمان عدم رفض سيرفرات تيليجرام لها.

### 💎 [D2] تحديث رابط المشروع الحي عند التدوير (Live Project URL & ID Re-binding):
- عند نجاح تدوير الحساب وإنشاء مشروع جديد (أو جعله Public):
  1. يتم تحديث `active_project_id` و `active_project_url` داخل الـ `manifest` فوراً.
  2. يتم تحديث كروت العرض والروابط المرسلة للمستخدم بالرابط الفعلي الجديد.
  3. يتم ربط الـ Continuation Query بالمعرف الجديد، مع تفريغ الروابط الميتة القديمة.

### 💎 [D3] تسجيل تليميتري واضح لحالة الإرسال (Telemetry):
- إضافة أسطر تليميتري صريحة:
  - `TELEGRAM_FINAL_DISPATCH_OK` (تم الإرسال للتليجرام بنجاح).
  - `TELEGRAM_FINAL_DISPATCH_FALLBACK_PLAIN` (تم الإرسال بنص عادي بعد فشل الماركداون).
  - `CONTINUATION_URL_REBIND_OK` (تم تحديث رابط وسياق المشروع بنجاح).

---

## 📋 4. خطة الـ Checkpoints التنفيذية (CP0 ➔ CP7)

- [ ] **CP0 — SPEC ADOPTION & BASELINE:**
  - اعتماد الوثيقة 19 في الروت.
  - إثبات الـ Baseline (974 PASS + hadith_sijil Exit 0 + Parity 11/11).
  - تحديث البند 7 وبلوك ## 0 بـ PHASE 45.
  - Commit: `P45-CP0: spec adopted — 19_FINAL_REPLY_DISPATCH_AND_PROJECT_LINK_BINDING.MD (DEC-041)`

- [ ] **CP1 — FORENSIC ANCHORS (grep -n):**
  - تثبيت أسطر إرسال الرسالة النهائية ودوال الـ Telegram API (`send_message`).
  - تثبيت أسطر ربط رابط المشروع في `Fetch & Forward` والتنقل بين الحسابات.
  - Commit: `P45-CP1: forensic anchors baseline`

- [ ] **CP2 — GUARANTEED TELEGRAM FINAL DISPATCH (D1):**
  - ربط استدعاء `send_message` بنهاية `fetch_final_reply_text`.
  - تطبيق آلية الـ Failover (Markdown ➔ Plain Text) وتجزئة الرسائل > 4000 حرف.
  - Commit: `P45-CP2: guaranteed final reply telegram dispatch`

- [ ] **CP3 — DYNAMIC PROJECT URL & CONTEXT REBIND (D2):**
  - تحديث رابط ومعرف المشروع النشط فور توليد الحساب الجديد.
  - تمرير الرابط الحي لـ `continuation_prompt` وكروت التليجرام.
  - Commit: `P45-CP3: live project url and context rebind`

- [ ] **CP4 — TELEMETRY & OBSERVABILITY (D3):**
  - إضافة أحداث التيليميتري الثلاثة وتوثيق ظهورها في اللوج.
  - Commit: `P45-CP4: dispatch and rebind telemetry`

- [ ] **CP5 — TEST SUITE (8 Tests):**
  - كتابة 8 اختبارات جديدة في `tests/test_p45_final_dispatch_and_link_binding.py`.
  - اجتياز كافة الاختبارات (982/982 PASS).
  - تحديث حدود PARTS والحفاظ على تطابق Parity 11/11.
  - Commit: `P45-CP5: 8 tests green + parity 11/11`

- [ ] **CP6 — QUALITY GATES & ZERO REGRESSION:**
  - `pytest` (982 PASS) + `hadith_sijil.py` (Exit 0) + `Parity` (11/11) + شجرة نظيفة.
  - Commit: `P45-CP6: quality gates green`

- [ ] **CP7 — CLOSEOUT & HANDOFF:**
  - تحديث PROGRESS ×2 و SESSION_LOG و README.
  - تحديث البند 7 وبلوك ## 0 بـ `BLOCKED-ON-OWNER`.
  - تقديم التقرير النهائي الشامل بعناوين البند 8 الاثني عشر.
  - Commit: `P45-CP7: close — Final Reply Dispatch & Link Binding shipped (DEC-041)`

---

## 🧪 5. مصفوفة الاختبارات المقترحة لـ CP5 (8 اختبارات)
1. `test_01_final_reply_triggers_telegram_dispatch` ➔ التأكد من استدعاء إرسال التليجرام عند انتهاء الرد.
2. `test_02_markdown_parse_error_falls_back_to_plain_text` ➔ الرموز غير المعالجة لا تُسقط الرسالة بل ترسلها Plain Text.
3. `test_03_long_message_chunking_under_4000_chars` ➔ النصوص > 4000 حرف تتجزأ وتصل كاملة.
4. `test_04_new_account_rebinds_active_project_id` ➔ الحساب الجديد يحدّث معرف مشروعه فوراً.
5. `test_05_continuation_url_reflects_latest_sandbox_url` ➔ رابط المشروع في الاستئناف يطابق الرابط الجديد.
6. `test_06_display_cards_show_updated_project_link` ➔ الكارت يعرض رابط المشروع الحي لا القديم.
7. `test_07_telemetry_events_emitted_correctly` ➔ انبعاث إشارات التيليميتري الثلاث.
8. `test_08_zero_regression_on_p43_and_p44` ➔ عدم تأثر الوضع السريع أو الـ Activity Gate.

---

## 🔒 6. المحظورات والقواعد الإلزامية
1. ممنوع لمس المحرك `01.03` أو التعديل على ملفات التستات القديمة.
2. ممنوع تفتيت `01.33` (Single-File Doctrine).
3. ممنوع إسقاط أي رسالة نهائية تحت أي ظرف — Fail-Open مضمون للتليجرام.
4. Evidence-First: لا [x] بدون إثبات Terminal صريح لكل Checkpoint.
