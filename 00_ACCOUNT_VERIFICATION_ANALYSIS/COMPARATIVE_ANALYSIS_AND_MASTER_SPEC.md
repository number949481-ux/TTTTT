# 📊 تقرير التحليل المقارن ومواصفات الدالة الموحدة لكشف الحسابات والرصيد
## Genspark Account Verification, Suspension Detection & Balance Checker Study

> **🎯 الهدف:** دراسة تفصيلية مقارنة بين 4 سكريبتات:
> 1. `01.21_genspark_register.py` (منظومة التسجيل V5.5)
> 2. `01_genspark_balance_checker_and_sorter.py` (منظومة الفحص والتصنيف 1111)
> 3. `02_genspark_balance_checker_and_sorter.py` (منظومة الفحص والتصنيف 1111)
> 4. `03_genspark_balance_checker_and_sorter.py` (منظومة الفحص والتصنيف المحدثة 1111)
> 
> والهدف النهائي: استخلاص **دالة شاملة متكاملة (Master Engine)** لدمجها في مجلد `31` (`01.33_telegram_gen_bridge.py` و `01.03Genspark_claude-opus-5-code.py`) لكشف الحظر التلقائي والرصيد الحقيقي وفحص نشاط المستخدم دون الوقوع في الفخاخ العمياء أو الحلقات المفرغة.

---

### 1️⃣ جدول المقارنة الشامل للدوال بين السكريبتات الأربعة

| الوظيفة التقنية | سكريبت التسجيل `01.21` | سكريبت الفحص `01` و `02` | سكريبت الفحص `03` | سكريبتات مجلد `31` الحالية (`01.03` / `01.33`) |
|-----------------|------------------------|---------------------------|-------------------|------------------------------------------------|
| **كشف الحظر أثناء تسجيل الدخول B2C** | ❌ غير موجود (فحص نجاح فقط) | ✅ **`do_b2c_login`** (يفحص `user_suspended` في Step 4) | ✅ **`do_b2c_login`** (يفحص `user_suspended` في Step 4) | ❌ **أعمى تماماً** (يرجع `None` فقط ويعتبره `auth_failed`) |
| **كشف الحظر أثناء استعلام الرصيد** | ❌ لا يفحص الـ Redirect | ✅ **`check_single_account_balance`** (يفحص `location` و 302/307 و نص 200) | ✅ **`check_single_account_balance`** (نفس منطق 01 و 02) | ❌ لا يفحص `user_suspended` ويعامل أي عطل كـ `-1` أو `-2` |
| **فحص وجود اليوزر ونشاطه** | ✅ **`validate_account_status`** (يفحص `/api/user` وحالة -5 و inactive) | ⚠️ يفحص فقط وجود `cogen` لـ Data Retention | ⚠️ يفحص فقط وجود `cogen` لـ Data Retention | ❌ لا يستعلم عن `/api/user` أصلاً للتحقق من نشاط الحساب |
| **البحث المتعمق في JSON للرصيد** | ✅ **`_extract_credits_from_dict`** (بحث بازغ في 6 حقول ومسارات فرعية) | ❌ يقرأ مسار ثابت `data.data.balance` | ❌ يقرأ مسار ثابت `data.data.balance` | ❌ يقرأ مسار ثابت `data.balance` فقط |
| **إعادة المحاولة مع Backoff** | ✅ `backoff = (0, 3, 5)` ثواني | ❌ محاولة واحدة مع Timeout | ❌ محاولة واحدة مع Timeout | ⚠️ محاولة ثانية بـ Backoff عشوائي لكنها تعيد نفس الخطأ |
| **تتبع الجلسة ودورات الفحص** | ❌ | ❌ | ✅ **`scan_id`** بصمة فحص زمنية لكل دورة | ❌ |
| **تطهير الماستر من المحظور** | ❌ يكتب في `rejected.log` | ⚠️ استبعاد من ملف `accounts.json` فقط | ✅ **`clean_master`** يستبعد `suspended` من الملف الماستر تلقائياً | ❌ الحساب المحظور يظل في القائمة ويدخل كول داون 30 دقيقة فقط |

---

### 2️⃣ التشريح التفصيلي لكل سكريبت مع أرقام السطور (Ground Truth)

#### أ. سكريبت التسجيل: `01.21_genspark_register.py`
- **الدوال المعنية:**
  1. `validate_account_status(cookies, proxies=None)` (السطور `3282-3357`):
     - **نقطة القوة العبقرية:** يفحص `GET /api/user`.
     - لو السيرفر رجع HTTP 200 ولكن JSON يحتوي على `status == -5` أو نص `"user not found"` -> يعطي كود صريح `REJ_USER_NOT_FOUND`.
     - لو `status not in [0, "0", 200, "200"]` -> يعطي `REJ_USER_INACTIVE`.
     - يعمل بـ Backoff تدريجي `(0, 3, 5)` ثواني للتغلب على تأخر الـ Provisioning في قاعدة بيانات Genspark.
  2. `_extract_credits_from_dict(obj)` (السطور `3202-3240`):
     - يبحث بذكاء عن الرصيد الحقيقي تحت مفاتيح: `total_credits`, `balance`, `remained_credits`, `remaining_credits`, `new_balance`, `points`.
     - يتجاهل حقول `credits` و `amount` لأنها تعني في Genspark "الرصيد المستهلك" وتكون صفراً.

---

#### ب. سكريبتات الفحص والتصنيف: `01` و `02_genspark_balance_checker_and_sorter.py`
- **حقيقة التطابق:** النسخة `01` والنسخة `02` متطابقتان بنسبة 100% بايت ببايت (لا يوجد أي اختلاف بينهما).
- **الدوال المعنية:**
  1. `do_b2c_login(email, password)` (السطور `206-300`):
     - **مربط الفرس الأول (كشف الحظر في الخطوة 4):**
       ```python
       r4 = sess.get(auth_url, allow_redirects=False, timeout=25)
       redirect_target = r4.headers.get("location", r4.headers.get("Location", ""))

       # كشف الحظر المباشر من هيدر التحويل 302/307
       if "user_suspended" in redirect_target or (r4.status_code in [302, 307] and "suspended" in redirect_target):
           return None, "suspended"

       # لو تتبع التحويل وجاء الرابط النهائي user_suspended
       if redirect_target:
           r4_final = sess.get(
               redirect_target if redirect_target.startswith("http") else f"{GENSPARK_HOST}{redirect_target}",
               allow_redirects=True, timeout=25
           )
           if "user_suspended" in str(r4_final.url):
               return None, "suspended"
       ```
     - **كشف خطأ الباسورد والإيميل (الخطوة 2):** لو رجع status ليس 200 وفيه كلمة `password` أو `incorrect` أو كود `400` -> يرجع `(None, "invalid_credentials")`.
  2. `check_single_account_balance(cookies)` (السطور `302-388`):
     - **مربط الفرس الثاني (كشف الحظر أثناء طلب الرصيد):**
       يطلب الرابط مع `allow_redirects=False`:
       ```python
       resp = sess.get(ENDPOINT_BALANCE, timeout=25, allow_redirects=False)
       status_code = resp.status_code
       loc = resp.headers.get("location", resp.headers.get("Location", ""))

       if "user_suspended" in loc or "suspended" in loc:
           return 0, "suspended", "حساب محظور وموقوف (Suspended)", False, False, {}, None

       if status_code == 200:
           if "user_suspended" in resp.text:
               return 0, "suspended", "حساب محظور وموقوف (Suspended)", False, False, {}, None
       ```

---

#### ج. سكريبت الفحص والتصنيف المحدث: `03_genspark_balance_checker_and_sorter.py`
- **الفروقات الجوهرية عن `01` و `02`:**
  1. إضافة تتبع دورات الفحص بالبصمة الزمنية **`scan_id`** (السطور `787` و `902`):
     `scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")`
     `acc["last_scan_id"] = scan_id`
  2. منطق **`clean_master`** (السطور `670-700`):
     أثناء الحفظ التراكمي، يتم فلترة واستبعاد أي حساب موقوف أو محظور نهائياً من ملف الماستر:
     ```python
     if not em or st in ["suspended", "invalid_credentials", "login_failed", "duplicate_dot_variation"] or err == "user_suspended":
         continue
     ```
  3. تفعيل الفحص الحي الطازج **Fresh Live Check** وتعطيل تخطي الحسابات المعتمد على الكاش القديم (السطور `804-806`).

---

### 3️⃣ مواصفات وتصميم "الدالة الشاملة المتكاملة" (The Master Engine Specification)
المقترح لدمجها في مجلد `31` (`01.03` + `01.33`):

الدالة الهندسية الموحدة ستتكون من طبقتين متكاملتين:

#### 🔹 الطبقة الأولى: دالة الفحص الشامل للحساب (`verify_account_full_status`)
تجمع بين دقة `01.21` في فحص `/api/user` وقوة `01/02/03` في كشف `user_suspended` و `Plus` و الرصيد:
1. **الخطوة 1: فحص الـ Session والرابط مع عدم السماح بالتحويل التلقائي (`allow_redirects=False`):**
   - استدعاء `/api/payment/get_credit_balance`.
   - لو الرد 302/307 وفيه `user_suspended` أو `suspended` -> تصنيف فوري: `"SUSPENDED"` (رصيد 0).
   - لو الرد 200 وفيه `user_suspended` -> تصنيف فوري: `"SUSPENDED"` (رصيد 0).
   - لو الرد 401 -> تصنيف فوري: `"SESSION_EXPIRED"` (يحتاج إعادة تسجيل دخول).
2. **الخطوة 2: فحص نشاط المستخدم من `/api/user` (مأخوذة من `01.21`):**
   - استدعاء `/api/user`.
   - لو رجع `status == -5` أو `"user not found"` -> تصنيف فوري: `"USER_NOT_FOUND"`.
   - لو رجع غير نشط -> تصنيف: `"INACTIVE"`.
3. **الخطوة 3: قراءة الرصيد واشتراك Plus ومكافأة الشهر الأول:**
   - قراءة الرصيد واستخدام البحث المتعمق Fallback.
   - فحص `/api/payment/current_subscriptions` لمعرفة هل هو `Plus` وهل معه كوبونات.
4. **الخطوة 4: في حال انتهاء الجلسة (401) والدخول في `do_b2c_login`:**
   - فحص الخطوة 4 في B2C: التأكد من أن `redirect_target` لا يحتوي على `user_suspended`.
   - لو الحساب محظور -> إرجاع `(None, "SUSPENDED")`.
   - لو الباسورد غلط -> إرجاع `(None, "INVALID_CREDENTIALS")`.
   - لو نجح -> إرجاع `(cookies, "ACTIVE")`.

#### 🔹 الطبقة الثانية: سلوك البريدج في `01.33_telegram_gen_bridge.py`
- عندما ترجع النتيجة `"SUSPENDED"` أو `"USER_NOT_FOUND"`:
  - وسم الحساب في ملف الحسابات بـ:
    `"status": "suspended", "active": False, "suspended_at": ISO_TIME, "error": "user_suspended"`
  - **استبعاد فوري ودائم:** لا يدخل كول داون 30 دقيقة ولا يُعاد اختياره أبداً في الدورة الحالية أو المستقبلية.
  - إرسال إشعار تليجرام للإدمن وطباعة سطر أحمر نيون مميز في التيرمينال:
    `[🚫 حساب محظور نهائياً - تم استبعاده وحذفه من الدورة: email@domain.com]`
