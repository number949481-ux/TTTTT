# 14 — PHASE 40: Compact Time UX + Decline Fast-Path Latency
> **بروتوكول معتمد قبل تعديل الكود** (عقد EXECUTION PROTOCOL — INSPECT ➔ PROVE ➔ PLAN ➔ EXECUTE)
> التاريخ: 2026-08-23 | الجلسة: S62 | الملف النشط: `01.33_telegram_gen_bridge.py` (7873 سطراً قبل التعديل)

---

## 🔴 أولاً: العلة المبلَّغة

> «تأخر Telegram بعد اكتشاف `is_model_decline_response`» — رسالة الرفض 🚫 تصل للمستخدم متأخرة
> دقائق رغم أن رد الرفض نفسه قصير (≤300 حرف) ويصل من المحرك خلال ثوانٍ.

---

## 🔬 ثانياً: السبب الجذري المُثبت بالأدلة (INSPECT-FIRST)

### التسلسل الفعلي الحالي (من السورس — لا من الافتراض)

1. رد الرفض القصير يصل من `mod.send_chat` (أو من polling المتابعة) داخل
   `send_message_and_make_public` ويُصنَّف `COMPLETED` تقنياً
   (`detect_response_status` — سطر **2456**؛ الرد > 25 حرفاً).
2. **قبل الرجوع** من `send_message_and_make_public` تُنفَّذ المسارات المكلفة التالية
   على رد رفض **بلا أي ناتج**:

| السطر | العملية | التكلفة الشبكية القصوى | الدليل |
|---|---|---|---|
| **2527** | `download_project_archive(pid, ...)` | `sess.get(..., timeout=180)` — سطر **2070** (حتى **3 دقائق** انتظاراً لأرشيف ساندبوكس قد لا يوجد أصلاً لمشروع مرفوض) | `grep -n "timeout=180"` |
| **2528** | `make_project_always_public(pid, ...)` | `mod.ensure_public` + حتى **3 طلبات POST** بـ `timeout=15` لكل واحد — أسطر **2121–2131** (حتى **45+ ثانية**) | جسم الدالة سطر 2083 |

3. كشف P35 (`model_declined = status == "COMPLETED" and is_model_decline_response(last_resp_text)`)
   يعيش في الـ **worker** حصرياً — سطر **6448** — أي **بعد** دفع كل التكاليف أعلاه.

### الخلاصة الكمية
التأخير الأقصى المحتمل بين وصول رد الرفض وإرسال رسالة 🚫 = **~225 ثانية** (180 + 45)
من عمليات شبكية عديمة القيمة لمشروع رفض الموديل بناءه.

### المفارقة المعمارية
**P36 (S57) عالج نفس العلة بالضبط في المحرك `01.03`** — المواقع الثلاثة (CLI / URL-mode / المتوازي)
تحسب `_declined` قبل أي مسار مكلف وتحرس `_do_auto_share` + `auto_download_project` + `ensure_public`
بـ `not _declined` (أسطر 2493/3377/3651 في `01.03`). لكن **مسار الجسر المستقل**
(`send_message_and_make_public` في `01.33` — الجسر يتولى الأرشفة/النشر بنفسه بعد `send_chat`)
**غير محروس** — فجوة تغطية لا كسر عقد: قاعدة P36 «الملفين معاً» تخص **عبارات الكاشف** (متطابقة ✅)
لا مواقع الحراسة.

---

## 🛠️ ثالثاً: خطة الحل

### T1 — Decline Fast-Path في الجسر (p06)
داخل `send_message_and_make_public` — بعد خروج حلقة المتابعة وكتلة `is_timeout`
و**قبل** سطر 2526 مباشرة:

```python
_declined = final_status == "COMPLETED" and is_model_decline_response(last_resp_text)
```

- عند `_declined`: **تخطي** `download_project_archive` + `make_project_always_public`
  (الحارسان `if not _declined`) وبناء الرابط المباشر بلا شبكة:
  `f"https://www.genspark.ai/autopilotagent_viewer?id={pid}"` — **نفس فلسفة P36 حرفياً**
  (الرابط لا يضيع؛ وهو نفس القيمة التي كانت `make_project_always_public` سترجعها
  حتى عند فشل كل الـ APIs ⇒ **صفر تغيير دلالي** في القيمة المرجعة).
- `ext_dir` يبقى يُحسب كالمعتاد (مسار بلا أرشيف): `describe_archive_delivery` ترجع
  `(None, None)` بأمان للمسار غير الموجود (سطر 6024) — لا رسالة أرشيف مزعجة.
- **ممنوع حراسة التسجيل المحلي** (عقد P36 رقم 3): `save_project_branch` (سطر 2529)
  يعمل كالمعتاد — رخيص محلي.
- **Zero Breaking على Success/Resume/Rotation:** الرجوع بـ `pub_url` غير فارغ +
  `status=COMPLETED` ⇒ فرع `attempt-succeeded` في failover كما هو حرفياً؛ إعادة التصنيف
  `MODEL_DECLINED` + تصفير `final_pid` تبقى في الـ worker حصرياً (عقد P35 رقم 2 بلا مساس).

### T2 — Compact Duration (p03)
دالة جديدة top-level `format_compact_duration(seconds)` بجوار `format_arabic_duration`:

| المدخل | المخرج |
|---|---|
| 45 | `45s` |
| 737 | `12m 17s` |
| 3900 | `1h 5m` |
| 3600 | `1h` |
| 0 / None / سالب / junk | `0s` (لا Crash أبداً — نفس عقد القديمة) |

قاعدة العرض: مع الساعات ⇒ `Xh` + (` Ym` إن > 0) بلا ثوانٍ؛ مع الدقائق فقط ⇒ `Xm` + (` Zs` إن > 0)؛
وإلا `Zs` — مطابقة لفلسفة القديمة «لا ثوانٍ صفرية مع مكوّن أكبر».

- **تحويل الاستدعاءات الثلاثة** داخل `format_account_timing_block` (أسطر 787/792/796)
  من `format_arabic_duration` إلى `format_compact_duration`.
- **`format_arabic_duration` تبقى بلا أي مساس** — حراسها المباشرون
  (SCENARIO E في `test_p30`) يظلون خضراً بلا تعديل، والدالة مُصدَّرة عبر parity المرايا
  (سابقة S61: التصدير عبر العقد ليس كوداً ميتاً).

### T3 — الحراسة
- ملف جديد `tests/test_p40_compact_time_decline_fastpath.py`:
  مجموعات (المدة المضغوطة بكل الحواف / الكتلة تستخدم المضغوط / بقاء القديمة /
  حراس سورس Fast-Path على نمط حراس P36 / Zero-Breaking للتسجيل المحلي وfailover).
- تحديث واعٍ للحراس القدامى الذين يفحصون **مخرجات الكتلة** (سابقة P39 المعتمدة):
  - `test_p30`: `test_accounts_total_is_sum_of_spans` («2 دقيقة» ➔ `2m`).
  - `test_p39`: `test_total_computed_from_filtered_only` («38 دقائق و24 ثانية» ➔ `38m 24s`)
    + `test_wall_clock_independent_of_filtering` («39 دقائق و13 ثانية» ➔ `39m 13s`).

### T4 — المواءمة
PARTS boundaries (p03 يكبر بالدالة الجديدة، p06 بأسطر الحراسة، إزاحة ما بعدهما)
➔ إعادة بناء `bridge_refactor/` ➔ parity 11/11 ➔ pytest كامل ➔ `hadith_sijil.py` Exit 0
➔ التوثيق (PROGRESS ×2 + SESSION_LOG DEC-036 + V3_RESUME + TEST_SUITE_CATALOG) ➔ Commit.

---

## 🚧 رابعاً: خارج النطاق عمداً (قرارات موثقة)

1. **`fetch_project_activity_signature` قبل الحلقة (سطر 2459):** طلب GET واحد (~1–3ث)
   يُنفَّذ حتى مع COMPLETED فوري — لمسه يهدد baseline عقد P18 المحروس بـ 20 اختباراً
   («baseline يُلتقط قبل دخول الحلقة»). التوفير هامشي مقابل المخاطرة ⇒ **لا يُلمس**.
2. **نقل إعادة تصنيف MODEL_DECLINED من الـ worker للجسر:** يكسر عقد P35 رقم 2 الصريح
   («إعادة التصنيف تحدث في الـ worker حصرياً») ⇒ **مرفوض** — الحارسان الجديدان
   يخدمان نفس الغاية بلا كسر.
3. **تغيير `format_arabic_duration` نفسها:** الاسم يصبح مضللاً وحراسها المباشرون ينكسرون
   بلا داعٍ ⇒ دالة جديدة + تحويل الاستدعاءات.
