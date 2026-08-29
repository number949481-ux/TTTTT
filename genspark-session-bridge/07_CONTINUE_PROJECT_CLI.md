# 🛠️ 07_CONTINUE_PROJECT_CLI — سكريبت `continue_project.py` (أداة التكملة الجاهزة)
> موثّق: 2026-08-29 — SESSION-GSB-001، رسالة المالك الرابعة ("اوكي موافق نفذ")
> المرجع النظري: `06_CONTINUE_SAME_PROJECT_API.md`

## 🎯 الهدف
تغليف سلسلة تكملة نفس المشروع (المشروحة في الملف 06) في **أمر واحد** من الطرفية،
بدل كتابة كود يدوي كل مرة.

## 📍 المسار
- السكريبت: `continue_project.py` (جذر الريبو)
- الاختبارات: `tests/test_continue_project_cli.py` — **20 اختبار، كلها ناجحة**

## ⚙️ ما ينفّذه بالترتيب
```
1. parse_project_locator(link)      ← تصنيف: pid / malformed / none   [SSOT محلي]
2. load_engine()                    ← importlib لـ 01.03Genspark_claude-opus-5-code.py
3. resolve_account()                ← lock_pick_and_reserve أو --email محدد
4. لو --fork:  ensure_public()  ➔  create_forked_project()  ➔ NEW_PID
5. send_chat(cookies, prompt, project_id=PID)   ← ❤️ قلب التكملة
6. طبع رابط الاستئناف + حفظ اختياري (--out)
```

## 🚦 الاستخدام
```bash
# فحص آمن تماماً بدون أي شبكة (يُنصح به أول مرة)
python3 continue_project.py --dry-run \
  "https://www.genspark.ai/autopilotagent_viewer?id=<UUID>" "كمّل"

# تكملة مباشرة — نفس الحساب (Fork=False)
python3 continue_project.py \
  "https://www.genspark.ai/agents?id=<UUID>" "كمّل من حيث توقفت"

# بحساب محدد
python3 continue_project.py --email me@example.com "<UUID>" "كمّل"

# من حساب مختلف — فورك سيرفري كامل (Fork=True)
python3 continue_project.py --fork --owner-email owner@example.com \
  "https://www.genspark.ai/autopilotagent_viewer?id=<UUID>" "كمّل"

# حفظ تقرير كامل JSON
python3 continue_project.py --out run.json "<رابط>" "كمّل"
```

## 🎛️ الخيارات
| الخيار | الوظيفة |
|---|---|
| `--dry-run` | فحص الرابط + طبع الخطة، **بدون أي اتصال شبكة ولا تحميل محرك** |
| `--fork` | حساب مختلف: ensure_public ➔ create_forked_project ➔ send_chat |
| `--email` | الحساب المُرسِل (الافتراضي: Smart Picker بحجز ذري) |
| `--owner-email` | مالك المشروع الأصلي (يُستخدم مع `--fork` لجعله عاماً) |
| `--model` | تجاوز الموديل (افتراضي من Config = claude-opus-5) |
| `--history N` | `cli_history_max`: `-1` اعتماد كامل على السيرفر (افتراضي/أرخص) \| `0` كل الرسائل \| `N` آخر N |
| `--timeout` / `--accounts` | تجاوز المهلة / ملف حسابات بديل |
| `--out FILE` | حفظ الرد (`.json` = تقرير كامل، غير كده = نص خام) |
| `--debug` / `--quiet` | تفعيل show_debug / عدم طبع نص الرد |

## 🔢 أكواد الخروج (Exit Codes)
| كود | المعنى |
|---|---|
| `0` | نجاح |
| `2` | خطأ في المدخلات (برومبت فاضي) |
| `3` | فشل تحميل المحرك 01.03 |
| `4` | الحساب المطلوب غير موجود / بدون session_id |
| `5` | لا يوجد حساب صالح متاح (رصيد/كوكيز/cooldown) |
| `6` | الرابط malformed أو لا يحمل PID صالح |
| `7` | فشل الفورك (المشروع غير عام أو كوكيز منتهية) |
| `8` | استثناء داخل send_chat |
| `9` | لم يرجع رد (لكن الـ PID يُطبع للاستئناف) |
| `130` | إلغاء بـ Ctrl+C |

## 🔐 ضمانات الأمان (متحقّقة باختبارات)
- ❌ **لا يطبع كوكيز أو أسرار** إطلاقاً.
- 🎭 الإيميلات مقنّعة: `secretuser@x.com` ➔ `se***@x.com` (اختبار يمنع التسريب الكامل).
- 🧪 `--dry-run` لا يفتح شبكة **ولا يحمّل المحرك** (متحقّق: غياب "المحرك محمّل" من الخرج).
- 🚫 رابط `login` مرفوض كـ PID (حماية من كوكيز منتهية تنتج redirect).
- 🔒 `is_probable_project_id` بصيغة fullmatch صارمة — `prj_660b71…` مرفوض (ليس UUID).

## ✅ حالة التحقق (2026-08-29)
- `python3 -m unittest tests.test_continue_project_cli` ➔ **Ran 20 tests — OK**
- اختبار ارتجاع: `tests/test_p1*.py` ➔ **Ran 151 tests — OK** (صفر انكسار)
- تحميل المحرك الفعلي متحقّق يدوياً: `🔌 المحرك محمّل: 01.03Genspark_claude-opus-5-code.py`
- ملاحظة: الإرسال الحقيقي لم يُجرَّب في هذا الساندبوكس لأن **ملف الحسابات
  (`accounts_genspark.json`) غير موجود هنا** (سري ومستبعد من الريبو) —
  السكريبت يفشل بأمان بكود `5` ورسالة واضحة. التجربة الحقيقية على جهاز المالك.

## 🧩 قرار تصميمي مهم
دوال التحليل (`extract_project_id` / `is_probable_project_id` / `parse_project_locator`)
**نُسخت محلياً** في السكريبت بدل استيراد `01.33_telegram_gen_bridge.py`، لأن:
1. استيراد ملف 490KB يشغّل تهيئة بوت تلغرام كاملة (غير مطلوبة لأداة CLI).
2. اسم الملف يبدأ برقم ونقطة ➔ غير قابل للاستيراد المباشر بـ import.
3. السلوك مقفول باختبار عقد (`TestEngineContract`) يتأكد أن دوال المحرك موجودة فعلاً.
⚠️ **لو عُدِّلت صيغة الـ PID في 01.33 مستقبلاً، حدّث النسخة في continue_project.py.**
