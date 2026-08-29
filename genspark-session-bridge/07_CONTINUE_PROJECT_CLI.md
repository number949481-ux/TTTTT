# 🛠️ 07_CONTINUE_PROJECT_CLI — سكريبت `continue_project.py` (أداة التكملة الجاهزة)
> موثّق: 2026-08-29 — SESSION-GSB-001، رسالة المالك الرابعة ("اوكي موافق نفذ")
> المرجع النظري: `06_CONTINUE_SAME_PROJECT_API.md`

## 🎯 الهدف
تغليف سلسلة تكملة نفس المشروع (المشروحة في الملف 06) في **أمر واحد** من الطرفية،
بدل كتابة كود يدوي كل مرة.

## 📍 المسار
- السكريبت: `continue_project.py` (جذر الريبو) + نسخ متطابقة في `الحماس/` و `جديد/`
- الاختبارات: `tests/test_continue_project_cli.py` — **29 اختبار، كلها ناجحة**

## ⚙️ ما ينفّذه بالترتيب
```
1. parse_project_locator(link)      ← تصنيف: pid / malformed / none   [SSOT محلي]
2. load_engine()                    ← اكتشاف ديناميكي: أي *Genspark_claude-opus-5-code.py
                                      جنب السكريبت (01.03 الأساسي يتصدّر لو موجود)
3. resolve_account()                ← lock_pick_and_reserve أو --email محدد
4. لو --fork:  ensure_public()  ➔  create_forked_project()  ➔ NEW_PID
5. send_chat(cookies, prompt, project_id=PID)   ← ❤️ قلب التكملة
6. فك حجز الحساب فوراً (finally — حتى مع فشل/Ctrl+C) بدل انتظار TTL الـ60ث
7. طبع رابط الاستئناف + حفظ اختياري (--out)
```

## 🔌 واجهة الاستدعاء الخارجي — `continue_from_link()`
للاستخدام من أي سكريبت بايثون تاني بدون subprocess:
```python
import importlib.util
spec = importlib.util.spec_from_file_location("cp", "continue_project.py")
cp = importlib.util.module_from_spec(spec); spec.loader.exec_module(cp)

r = cp.continue_from_link("<رابط أو UUID>", "كمّل من حيث توقفت", fork=False)
if r["ok"]:
    print(r["answer"], r["resume_url"])
else:
    print(r["exit_code"], r["error"])
```
**الضمانة**: لا ترمي `SystemExit` أبداً — ترجع dict دايماً بالمفاتيح:
`ok / exit_code / source_pid / final_pid / forked / forked_pid / answer /
message_id / resume_url / elapsed_sec / error`.
نفس أكواد الخروج أدناه ترجع في `exit_code` (+ كود `7` لو المحرك المجاور
لا يدعم الفورك وطُلب `fork=True` — زي نسخ 01.04/02.07 الناقصة `create_forked_project`).

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
| `3` | فشل تحميل أي محرك مجاور (أو لا يوجد محرك بنمط *Genspark_claude-opus-5-code.py) |
| `4` | الحساب المطلوب غير موجود / بدون session_id |
| `5` | لا يوجد حساب صالح متاح (رصيد/كوكيز/cooldown) |
| `6` | الرابط malformed أو لا يحمل PID صالح |
| `7` | فشل الفورك (مشروع غير عام / كوكيز منتهية / المحرك المجاور لا يدعم الفورك) |
| `8` | استثناء داخل send_chat |
| `9` | لم يرجع رد (لكن الـ PID يُطبع للاستئناف) |
| `130` | إلغاء بـ Ctrl+C |

## 🔐 ضمانات الأمان (متحقّقة باختبارات)
- ❌ **لا يطبع كوكيز أو أسرار** إطلاقاً.
- 🎭 الإيميلات مقنّعة: `secretuser@x.com` ➔ `se***@x.com` (اختبار يمنع التسريب الكامل).
- 🧪 `--dry-run` لا يفتح شبكة **ولا يحمّل المحرك** (متحقّق: غياب "المحرك محمّل" من الخرج).
- 🚫 رابط `login` مرفوض كـ PID (حماية من كوكيز منتهية تنتج redirect).
- 🔒 `is_probable_project_id` بصيغة fullmatch صارمة — `prj_660b71…` مرفوض (ليس UUID).

## ✅ حالة التحقق (2026-08-29 — محدّث)
- `python3 -m unittest tests.test_continue_project_cli` ➔ **Ran 29 tests — OK**
  (20 أصلية + 6 لواجهة `continue_from_link` بمحرك وهمي + 3 لاكتشاف المحركات)
- المجموعة الكاملة: `python3 -m unittest discover tests` ➔ **Ran 994 tests — OK**
- تحميل المحرك الفعلي متحقّق يدوياً من الثلاث مجلدات:
  جذر ➔ 01.03 │ الحماس/ ➔ 01.04 │ جديد/ ➔ 02.07
- دورة كاملة بمحرك وهمي (بدون شبكة) متحقّقة: حجز ➔ إرسال ➔ فك حجز فوري،
  وفورك كامل بالترتيب reserve ➔ ensure_public ➔ fork ➔ send ➔ release.
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
