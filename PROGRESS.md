# 📌 PROGRESS.md — بروتوكول نقطة الاستئناف الدائمة

> ⚠️ **قاعدة إلزامية**: هذا الملف يُحدَّث بعد **كل** جلسة عمل — أول قسم فيه هو دائماً
> نقطة الاستئناف المعتمدة للجلسة التالية. لا تبدأ أي عمل جديد قبل قراءته.

---

## 🟢 نقطة الاستئناف الحالية — 2026-08-20 (جلسة S40 — P21: دقة تصنيف commit جديد/معدل)

### الإصدار النشط
- **الملف الأساسي**: `01.31_telegram_gen_bridge.py` (6390 سطراً — +4 بعد إصلاح P21)
- **BUILD_VERSION**: `01.31`
- **BUILD_PARENT_BASELINE**: `01.30` (`0130_p19_copy_settings_baseline`)
- **الحالة**: ✅ كل الاختبارات ناجحة — **221 passed** (`python3 -m pytest tests/ -q`)

### ✅ ما أُنجز في S40 (P21 — بلاغ المالك: الإحصائيات لا تفرّق جديد/معدل)
1. **إصلاح `_default_github_uploader`** (سطر ~2978): الملف الموجود على الريموت
   بمحتوى مختلف (`remote_sha` موجود) يُصنّف الآن `modified` ✏️، والملف غير الموجود
   (404) يُصنّف `uploaded` ➕ — كانا مدموجين في `uploaded` وقائمة `modified` لا تُملأ أبداً.
2. **حارسان جديدان** في `tests/test_p20_rest_only_data_retention.py` (test_09 + test_10) — الإجمالي 221.
3. **PARTS boundaries** في `scripts/rebuild_refactor.py` مُزاحة +4 (p07 → 3342 … p12 → 6390)
   + إعادة بناء `bridge_refactor/` بتطابق بايت.
4. **التوثيق**: SESSION_LOG (DEC-017) + PROGRESS (الموضعان) + README + TEST_SUITE_CATALOG + V3_RESUME_SESSION.
5. **إعادة إخراج** `.pytest_cache/` و `bridge_bot.log` من التتبع (أعادتهما المزامنة التلقائية مجدداً).

### ✅ المهام الخمس (Deep Thinking — Total: 5 Tasks) كلها مُنجزة
| # | المهمة | الحالة |
|---|---|---|
| 1 | إزالة Git Native Sync بالكامل — REST API المسار الوحيد | ✅ (لا أثر لـ `_git_native_sync_uploader`/`_generate_ai_commit_message`/clone/push) |
| 2 | كشف DATA_RETENTION + معالجة polling + failover (تبريد + حساب تالٍ + نفس آخر رسالة + تنبيه مميز) | ✅ (سطور ~1297–~1320، ~1994، ~2187–~2202، ~5058) |
| 3 | تحديث اختبارات P17 (إزالة حراس qwen commit) + إنشاء test_p20 | ✅ `tests/test_p20_rest_only_data_retention.py` — 27 اختباراً |
| 4 | تحديث PARTS boundaries + إعادة بناء bridge_refactor + parity | ✅ byte-parity — `test_refactor_parity.py` 11/11 |
| 5 | تحديث التوثيق + بوابة hadith_sijil + commit | ✅ (هذه الجلسة S39) |

### 🔴 العقد الأهم (طلب المالك الصريح) — P18 وقف فوري عند تغيّر المهام
> "لو غيرت مهام وقف مش تكمل — Deep Thinking / Tasks Remaining لما يكون ده اتغير وقف فوراً"

مطبق ومؤكد في `01.31_telegram_gen_bridge.py`:
- `should_stop_on_activity_change` (سطر ~1405):
  - **أي** تغيّر في عدد `Tasks Remaining` — زيادة **أو نقصان** → المهام اتغيرت
    → **وقف فوري، مفيش أي تكملة** (`tasks-remaining-changed`) — سطر ~1425.
  - اختفاء المؤشر كلياً → وقف فوري (`activity-indicator-disappeared`) — سطر ~1420.
  - تقلّب Deep Thinking (ظهر/اختفى) → وقف فوري (`deep-thinking-changed`) — سطر ~1427.
- الفحص يعمل داخل حلقة المتابعة **كل 5 ثوانٍ قبل** polling الرسائل (سطر ~2001)
  — لحظة `stop_now` يحدث `break` فوراً.
- baseline يُلتقط قبل دخول الحلقة (`prev_activity` — سطر ~1993).
- فشل الشبكة في جلب البصمة يرجع `None` ويُتجاهل — لا يكسر المتابعة أبداً.
- مغطى بـ **20 اختباراً** في `tests/test_p18_activity_stop.py` — كلها ناجحة ✅.
- ⚠️ **نفس العقد مطبق على مستوى جلسات العمل نفسها**: لو تغيّرت قائمة
  Deep Thinking Tasks Remaining أثناء التنفيذ → توقّف فوري + تحديث كل نسخ PROGRESS.md
  (الجذري + `docs/engineering/PROGRESS.md`) قبل أي توقف.

### ما أُنجز في هذه الجلسة (ترقية 01.30 → 01.31 / P20)
1. **P20 — REST-Only Upload**: إلغاء مسار Git Native Sync نهائياً (كان يفشل بـ
   `name 'dest_root' is not defined`). الرفع إلى GitHub الآن حصرياً عبر
   Contents REST API داخل `_default_github_uploader` — بدون clone/push،
   وحُذفت `_git_native_sync_uploader` و `_generate_ai_commit_message`.
2. **P20 — DATA_RETENTION**: خطأ "AI Data Retention" يُكتشف في
   `detect_response_status` (قبل باقي الفئات) ويُعامَل كبروتوكول نفاد الرصيد:
   تبريد الحساب + الانتقال لحساب تالٍ + إعادة إرسال نفس آخر رسالة + تنبيه مميز.
   الحالة أُضيفت لشرط حلقة المتابعة (polling loop).
3. **ترقية شاملة للإصدار**: البانر + `BUILD_VERSION="01.31"` +
   `BUILD_PARENT_BASELINE="01.30"` + تحديث كل مراجع `01.30` في
   `tests/` و `scripts/` (hadith_sijil, generate_docs, rebuild_refactor).
4. **تحديث الاختبارات للعقد الجديد**:
   - `test_p17_hardening.py`: استبدال `TestQwenCommitIntegration` (كان يختبر
     Git Native Sync الملغي) بـ `TestRestOnlyUploader` (اختبارات REST-Only).
   - `test_p18_activity_stop.py`: regex حلقة المتابعة يشمل `DATA_RETENTION`
     + `BUILD_VERSION == "01.31"`.
   - `test_p15/p16/p19`: بانر `P12..P19 + P20` + baseline `01.30`.
5. **إعادة بناء `bridge_refactor/`**: تحديث خريطة `PARTS` في
   `scripts/rebuild_refactor.py` بحدود الأسطر الجديدة (6386 سطر) وإعادة توليد
   الأجزاء الحرفية — byte-parity ✅ (تأكدت مجدداً في S39: 11/11 parity).
6. **تنظيف git**: إخراج `.pytest_cache/` و `bridge_bot.log` من التتبع
   (أُعيد تطبيقه في S39 بعد أن أعادتهما المزامنة التلقائية + إضافة `bridge_bot.log` لـ `.gitignore`).
7. **إنشاء هذا الملف `PROGRESS.md`** كبروتوكول استئناف دائم — يُحدَّث كل جلسة.
8. **(S39) إغلاق المهام 3→5**: إنشاء `tests/test_p20_rest_only_data_retention.py`
   (27 اختباراً للعقدين: 8 REST-Only + 8 كشف DATA_RETENTION + 8 failover + 3 refactor)
   + تنظيف docstring في `test_p17_hardening.py` من مرجع qwen commit الملغي
   + إعادة بناء bridge_refactor + تحديث التوثيق الكامل + بوابة hadith_sijil.
9. **(S39 — تكملة) اكتمال التوثيق النهائي**: SESSION_LOG (DEC-016) +
   V3_RESUME_SESSION (219/`01.31` + قاعدتا REST-Only و DATA_RETENTION الدائمتان) +
   README (بانر 01.31/P20/219) + TEST_SUITE_CATALOG (مصفوفة 16 ملفاً/219 —
   P17=24 بعد حذف حراس qwen، P20=27) + إعادة إخراج `.pytest_cache/` و
   `bridge_bot.log` من tracking بعد أن أعادتهما المزامنة التلقائية —
   البوابة النهائية: pytest 219 passed + `hadith_sijil.py` Exit Code 0. ✅ S39 مغلقة بالكامل.

### الخطوة التالية المقترحة
- [x] إنشاء test_p20 + إعادة بناء refactor + تحديث كل التوثيق (S39 — 219 passed).
- [x] (S40 / P21) إصلاح تصنيف commit جديد/معدل + حارسان — 221 passed + بوابة Exit 0.
- [x] commit محلي — الدفع للريموت عبر المزامنة التلقائية (الدفع اليدوي يحتاج تفويض GitHub).
- [ ] **قرار مالك مقترح (لم يُنفذ)**: قص التاريخ المحقون في استئناف الجسر (مسار `elif history` في المحرك يحقن كامل التاريخ بلا حد — مسار Fetch & Forward الداخلي يقص لآخر 10). يحتاج قرار: كم رسالة سياق نُبقي؟
- [ ] حذف الملف القديم `01.30_telegram_gen_bridge.py` من الريبو إن أراد المالك
      (سياسة النسخ السابقة: يُحتفظ به أم لا؟ — يحتاج قرار).
- [ ] اختبار تشغيلي حي للبوت على تيليجرام للتأكد من مسار DATA_RETENTION عملياً.

---

## 📜 سجل الجلسات السابقة

### 01.30 (P19) — نسخ إعدادات مشروع آخر
- نسخ إعدادات (GitHub + موديل + برومبت) من مشروع قائم لمشروع جديد
- الترقيم التسلسلي التلقائي للأسماء المكررة (مثال: "الحج 2")

### 01.29 (P18) — وقف فوري عند تغيّر مؤشر النشاط
- مراقبة Deep Thinking / Tasks Remaining أثناء polling — أي تغيّر = وقف فوري

### 01.28 (P17) — تصليب
- تجديد فوري للجلسة المنتهية (-2) + بوابة رصيد بعد 401 + دعم الجروبات

### أقدم
- P16: نشر عام مبكر فور التقاط pid | P15: استقلال qwen_engine
- P12: carry_pid استئناف نفس المشروع | P13: بوابة الرصيد المسبقة (<100 = تبريد 29h)
