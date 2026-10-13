# 📐 الخطة الهندسية الكبرى الشاملة لنظام فحص وعزل حسابات Genspark
## Master Engineering Plan & Surgical Spec (Bolla Constitution v1.2 Compliant)
> **المشروع:** Genspark Telegram Bridge (Folder 31)  
> **الملفات المستهدفة:** `01.03Genspark_claude-opus-5-code.py` + `01.33_telegram_gen_bridge.py` + `genspark_verifier_engine.py`  
> **ملف العزل المعتمد:** `accounts_genspark_blocked_failed__block_failed.json`  
> **تصنيف الخطر:** 🔴 **المستوى T2 (تعديل معماري وعزل بيانات وتكامل محرك جديد)**  
> **حالة الكود:** ⛔ **وضع التخطيط الصارم [PLANNING] — صفر كود تنفيذي حتى موافقة صريحة "GO"**

---

## 🏛️ المرجعيات الدستورية الحاكمة (Bolla Ironclad Governance)

| البند | القاعدة الدستورية | التطبيق في هذه الخطة |
|:---|:---|:---|
| **القانون 1** | التدرج الثلاثي والمراسي التشفيرية | أخذ نسخة `.anchor` وحساب SHA-256 للملفات قبل وبعد أي تعديل جراحي. |
| **القانون 4** | حظر الكود أثناء التخطيط (`[PLANNING]`) | حظر لمس أو تعديل أي سطر في مجلد 31 حتى اعتماد الخطة والموافقة عليها. |
| **القانون 6** | بوابة الاعتماد الصريحة (Approval Gate) | التوقف الإلزامي لانتظار كلمة "GO" من المستخدم قبل الانتقال لوضع `[CODING]`. |
| **القانون 8** | الإسناد المرجعي الصريح بالسطور (Citation) | كل تعديل مستند لأرقام أسطر حقيقية مقتبسة حرفياً `L[Start]-L[End]`. |
| **القانون 9** | المواصفات المسبقة ومحاكي الجاف (Spec-Kit) | توثيق كتل (BEFORE) و (AFTER) بالكامل داخل هذه الوثيقة قبل كتابتها. |
| **القانون 10** | عزل المشاريع وعدم خلط الملفات | عزل ملفات الفحص والتقارير داخل المجلد المخصص وتحديث دفاتر النواة. |

---

## 🔐 البصمات التشفيرية المشفرة المعتمدة قبل التعديل (Baseline SHA-256 Hashes)

| الملف المستهدف | الحجم بالبايت | المسار الكامل | بصمة SHA-256 الأصلية الحالية |
|:---|:---:|:---|:---|
| `01.33_telegram_gen_bridge.py` | 526,005 | `.../bridge_refactor_31/01.33_telegram_gen_bridge.py` | `3d8b5c776536fba8ecc580192b2bbbaf905799209e211437b060fd9ed2325669` |
| `01.03Genspark_claude-opus-5-code.py` | 214,897 | `.../bridge_refactor_31/01.03Genspark_claude-opus-5-code.py` | `52c828d056613a079b0416d4e33c6c170d0b9d0412bc97c6ad112a97b909c9c8` |
| `genspark_verifier_engine.py` | 21,987 | `.../bridge_refactor_31/genspark_verifier_engine.py` | `59a9caf641ae49c0dc74d9933f1a0f794542982fd477250a0078eb5eb387a3b0` |

---

## 📢 1. ملخص تنفيذي وأسئلة شائعة (Amazon Working Backwards PR/FAQ)

### البيان الصحفي (Press Release):
> **اليوم:** تعلن منظومة بوتات التيليجرام في مجلد 31 عن إطلاق "نظام التحصين والعزل الذاتي للحسابات" (Immune Account Engine).  
> **الهدف:** القضاء النهائي على الفخ الدائري للحسابات المحظورة؛ فبدلاً من أن يقف البوت عاجزاً أو يكرر المحاولة على حساب محظور كل 30 دقيقة، يقوم النظام باكتشاف الحظر فوراً في أجزاء من الثانية، وتفعيل ميزة **AI Data Retention** بذكاء كاش محلي دون أي هدر للشبكة، ونقل الحساب الميت تلقائياً وبشكل ذري إلى ملف العزل المخصص `accounts_genspark_blocked_failed__block_failed.json`، مما يرفع استقرار وموثوقية التوليد بنسبة 100%.

### أصعب الأسئلة الشائعة (Toughest FAQs):
* **س1: ماذا يحدث لو انقطع اتصال الإنترنت أو واجهنا Cloudflare 403 أو Rate Limit 429؟ هل يُعزل الحساب؟**  
  **ج:** **مستحيل تماماً.** صُمم المحرك للتمييز الصارم بين "الموت القطعي للحساب" (Suspension / User Not Found / Invalid Credentials) وبين "العطل الشبكي العابر" (Transient Error). الأعطال العابرة لا تلمس الحساب ولا تعزله.
* **س2: هل سيتم فحص وتفعيل AI Data Retention في كل مرة يرسل فيها المستخدم رسالة؟**  
  **ج:** **لا.** الفحص والتفعيل يحدث **فقط عند تجديد الجلسة المنتهية (401)** أو الفحص الأولي. بالإضافة إلى ذلك، بمجرد تفعيله أول مرة، يُسجل في `accounts_genspark.json` كـ `"data_retention_enabled": true`، وفي المرات التالية يتم التخطي فوراً (0 ثانية و 0 استدعاء شبكة).
* **س3: هل يمكن استعادة حساب إذا عُزل بالخطأ؟**  
  **ج:** نعم، لأن ملف العزل `accounts_genspark_blocked_failed__block_failed.json` مستقل بذاته، ويسجل التاريخ والسبب بدقة، دون حذف بيانات الحساب الأصلية، مما يسمح بمراجعته يدوياً في أي وقت.

---

## 🎯 2. الأهداف الصريحة والأبعاد المستبعدة (Goals & Non-Goals)

### ✅ الأهداف الصريحة (Goals):
1. **كشف الحظر المطلق:** التقاط `user_suspended` في كل مسارات B2C و endpoints الرصيد واليوزر.
2. **كشف الحسابات المحذوفة:** اصطياد استجابة `/api/user` ذات الكود `-5` أو نص `"user not found"`.
3. **العزل الذري الفوري:** نقل الحساب الميت تلقائياً لملف `accounts_genspark_blocked_failed__block_failed.json`.
4. **كاش Data Retention:** التحقق من وجود القيمة مسبقاً في الـ JSON، وتفعيلها بطلب رسمي فقط لو كانت معطلة.
5. **تطهير دورة الاختيار:** تحديث حالة الحساب في `accounts_genspark.json` لمنع اختياره أو إدخاله في كول داون مؤقت مكرر.

### ❌ الأبعاد المستبعدة عمداً (Non-Goals):
1. **عدم لمس محرك التوليد أو البرومبت:** لن يتم تعديل دوال `send_chat` أو منطق صياغة الردود في التيليجرام نهائياً.
2. **عدم تعديل واجهات الأوامر أو أزرار البوت:** كل واجهات التيليجرام والأزرار تظل ثابتة ومستقرة كما هي.
3. **عدم لمس سكريبتات المشاريع الأخرى:** التطوير محصور جراحياً داخل مجلد `31`.

---

## 📜 3. سجل القرارات المعمارية (Architecture Decision Records - ADRs)

### 🏛️ ADR-01: عزل الحسابات المحظورة في ملف منفصل
* **الوضع:** Proposed (بانتظار موافقة GO).
* **السياق:** الحسابات المحظورة كانت تظل داخل `accounts_genspark.json` وتأخذ `cooldown_until: 1800` فتتكرر محاولة تشغيلها كل نصف ساعة وتستهلك وقت البوت.
* **القرار:** إنشاء ملف مخصص باسم `accounts_genspark_blocked_failed__block_failed.json` لتفريغ وعزل الحسابات الميتة بـ Thread-Safe Lock و `.tmp` atomic replace.
* **الأثر الإيجابي:** تنظيف دورة التشغيل ورفع موثوقية البوت، وسهولة تتبع الحسابات المستبعدة.

### 🏛️ ADR-02: فحص وكاش AI Data Retention المسبق من الـ JSON
* **الوضع:** Proposed (بانتظار موافقة GO).
* **السياق:** موديلات Claude و Opus تفشل وتظهر خطأ P20 إذا كانت خاصية Data Retention معطلة. فحصها بالشبكة في كل محاولة يسبب بطء غير مبرر.
* **القرار:** قراءة حقل `"data_retention_enabled"` من كائن الحساب في الـ JSON مباشرة: لو `True` يتم التخطي فوراً (0 شبكة). لو `False` أو غير موجود يتم فحصها وتفعيلها عبر `POST /api/user/update` وتوثيقها في الـ JSON.
* **الأثر الإيجابي:** حماية الموديلات المتقدمة مع سرعة فائقة وعدم إجهاد سيرفرات جين سبارك.

---

## ⚠️ 4. مصفوفة المخاطر وتحليل ما قبل الكارثة (Pre-Mortem Analysis)

| السيناريو الكارثي المحتمل | سبب الحدوث المحتمل | الإجراء الوقائي الصارم المدمج في الخطة |
|:---|:---|:---|
| **عزل حساب سليم فيه رصيد بالخطأ (False Positive)** | حدوث Timeout أو مشكلة في البروكسي أثناء الفحص. | حظر العزل في حالات `NETWORK_ERROR`, `RATE_LIMITED` (429), `CLOUDFLARE_BLOCKED` (403). العزل مقتصر حصراً على `user_suspended` و `-5` وخطأ الباسورد. |
| **تلف ملف الـ JSON أثناء كتابة العزل المتوازي** | قيام ثريدين بالكتابة في نفس اللحظة. | استخدام قفل الملفات المركزي `VAULT_LOCK = threading.Lock()` مع أسلوب الكتابة في `.tmp` ثم الاستبدال الذري `replace()`. |
| **تعليق البوت إذا فشل تجديد الجلسة** | الحساب دخل حظر ولكن البوت فضل منتظر. | إرجاع تشخيص فوري واستبعاد الحساب فوراً من قائمة `tried_emails` والانتقال للحساب التالي بدون أي كول داون 30 دقيقة. |
| **حدوث Regression في كود الباك إند القائم** | تعديل دوال حساسة تؤثر على `send_chat`. | عزل منطق الفحص داخل `genspark_verifier_engine.py` واستدعائه جراحياً في نقطتين محددتين فقط دون لمس جسم المحرك الأساسي. |

---

## 🔬 5. التوصيف الجراحي الدقيق بالسطور (BEFORE vs AFTER with Exact Lines)

---

### 📂 الملف الأول: `01.33_telegram_gen_bridge.py`
* **المسار:** `D:\SMS\...\bridge_refactor_31\01.33_telegram_gen_bridge.py`
* **بصمة SHA-256 الأصلية:** `3d8b5c776536fba8ecc580192b2bbbaf905799209e211437b060fd9ed2325669`

#### 🔴 التعديل الأول: توسيع فلاتر رفض الحساب في `is_account_ready`
* **الموقع:** السطور `L1034-L1039`

```python
# -------------------------------------------------------------
# ⏪ BEFORE (L1034-L1039 في الملف الأصلي):
# -------------------------------------------------------------
    status = str(acc.get("status", "active")).lower().strip()
    now = time.time()

    if status in ("banned", "blocked"):
        return False
```

```python
# -------------------------------------------------------------
# ⏩ AFTER (التعديل الجراحي المعتمد):
# -------------------------------------------------------------
    status = str(acc.get("status", "active")).lower().strip()
    now = time.time()

    # 🛡️ استبعاد قطعي ودائم لأي حساب معزول أو محظور أو ملوش يوزر
    if status in ("banned", "blocked", "suspended", "user_not_found", "invalid_credentials") or acc.get("quarantined") is True:
        return False
```

---

#### 🔴 التعديل الثاني: ترقية دالة `refresh_cookies_on_401` لدعم العزل وتفعيل Data Retention
* **الموقع:** السطور `L1115-L1142`

```python
# -------------------------------------------------------------
# ⏪ BEFORE (L1115-L1142 في الملف الأصلي):
# -------------------------------------------------------------
def refresh_cookies_on_401(mod, email: str, password: str, json_path: str | None = None) -> dict | None:
    """تجديد الكوكيز بقفل محكوم منفرد لكل إيميل يمنع التضارب بين الثريدات الموازية"""
    lock = get_account_lock(email)
    with lock:
        try:
            log_event("warning", "جاري تجديد كوكيز الجلسة...", email=email)
            new_cookies = mod.do_login(email, password) if hasattr(mod, "do_login") else None
            if new_cookies and isinstance(new_cookies, dict) and len(new_cookies) > 0:
                update_account_data(email, {
                    "cookies": new_cookies,
                    "status": "active",
                    "active": True,
                    "last_refresh": time.time(),
                    "last_refresh_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                }, json_path=json_path)
                log_event("success", "تم تجديد الكوكيز والجلسة بنجاح!", email=email)
                return new_cookies
        except Exception as e:
            log_event("error", f"فشل تجديد كوكيز الجلسة: {e}", email=email)
            update_account_data(email, {
                "status": "auth_failed",
                "active": False,
                "cooldown_until": time.time() + 1800,  # حظر مؤقت 30 دقيقة فقط ثم يُعاد تلقائياً
                "last_auth_error": str(e),
                "last_auth_error_at": time.strftime("%Y-%m-%dT%H:%M:%S")
            }, json_path=json_path)
        return None
```

```python
# -------------------------------------------------------------
# ⏩ AFTER (التعديل الجراحي المعتمد):
# -------------------------------------------------------------
def refresh_cookies_on_401(mod, email: str, password: str, json_path: str | None = None) -> dict | None:
    """تجديد الكوكيز مع العزل الفوري للحسابات المحظورة وفحص كاش AI Data Retention الذكي"""
    lock = get_account_lock(email)
    with lock:
        try:
            log_event("warning", "جاري تجديد كوكيز الجلسة وفحص الحساب...", email=email)
            
            # استيراد محرك الفحص الموحد
            import genspark_verifier_engine as gve
            
            # جلب بيانات الحساب الحالية من الـ JSON لفحص كاش الـ Data Retention المسبق
            current_accounts = read_accounts_safe(json_path)
            acc_entry = next((a for a in current_accounts if isinstance(a, dict) and a.get("email") == email), {})
            
            # تشغيل الفاحص الشامل
            report = gve.master_inspect_and_heal_account(
                email=email,
                password=password,
                existing_cookies=acc_entry.get("cookies"),
                account_dict=acc_entry,
                min_required_balance=1,
                timeout=25
            )
            
            # 1. لو الحساب ميت (محظور / ملوش يوزر / باسورد غلط) -> عزل فوري دائم
            if report.get("is_dead") is True:
                verdict = report.get("verdict", "SUSPENDED")
                detail = report.get("detail", "")
                base_dir = SCRIPT_DIR.parent if (SCRIPT_DIR.parent / "accounts_genspark.json").exists() else SCRIPT_DIR
                
                # عزل ذري في accounts_genspark_blocked_failed__block_failed.json
                gve.quarantine_account_atomic(acc_entry, verdict=verdict, base_dir=base_dir, detail=detail)
                
                # وسم الحساب كمحظور دائم في accounts_genspark.json وتصفير كوكيزه
                update_account_data(email, {
                    "status": "suspended",
                    "active": False,
                    "quarantined": True,
                    "cooldown_until": 0,
                    "cookies": {},
                    "quarantine_reason": verdict,
                    "quarantined_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                }, json_path=json_path)
                log_event("error", f"[🚫 حساب محظور نهائياً تم استبعاده وعزله]: {email} | السبب: {verdict}", email=email)
                return None

            # 2. لو الحساب نشط وجدد كوكيز بنجاح
            new_cookies = report.get("cookies")
            if new_cookies and isinstance(new_cookies, dict) and len(new_cookies) > 0:
                updates = {
                    "cookies": new_cookies,
                    "status": "active",
                    "active": True,
                    "balance": report.get("balance", acc_entry.get("balance", 0)),
                    "is_plus": report.get("is_plus", False),
                    "last_refresh": time.time(),
                    "last_refresh_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                }
                # لو تم تفعيل Data Retention جديدة -> كتابتها في الـ JSON فوراً
                if report.get("needs_json_retention_save") is True:
                    updates["data_retention_enabled"] = True
                    updates["data_retention_activated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    log_event("success", "🧬 تم تفعيل AI Data Retention وتوثيقها في الـ JSON للحساب بنجاح", email=email)
                elif report.get("data_retention_source") == "cached_in_json":
                    log_event("info", "⚡ تم تخطي فحص Data Retention (موثقة ومفعلة مسبقاً في الـ JSON)", email=email)

                update_account_data(email, updates, json_path=json_path)
                log_event("success", f"تم تجديد الكوكيز وتحديث الرصيد ({updates['balance']}) بنجاح!", email=email)
                return new_cookies

        except Exception as e:
            log_event("error", f"فشل تجديد كوكيز الجلسة: {e}", email=email)
            update_account_data(email, {
                "status": "auth_failed",
                "active": False,
                "cooldown_until": time.time() + 1800,
                "last_auth_error": str(e),
                "last_auth_error_at": time.strftime("%Y-%m-%dT%H:%M:%S")
            }, json_path=json_path)
        return None
```

---

#### 🔴 التعديل الثالث: معالجة الـ 401 في الحلقة الرئيسية لتخطي الحساب المعزول فوراً
* **الموقع:** السطور `L3405-L3414`

```python
# -------------------------------------------------------------
# ⏪ BEFORE (L3405-L3414 في الملف الأصلي):
# -------------------------------------------------------------
                except Exception as e:
                    log_event("error", f"فشل تجديد كوكيز الحساب: {e}", email=curr_email)
                notify_account_selection_observer(
                    bridge_cfg,
                    "session-refresh-failed",
                    status="auth_failed",
                    refresh_count=state_refresh.get(curr_email, 0),
                )
                update_account_data(curr_email, {"cooldown_until": time.time() + 1800, "status": "auth_failed", "active": False}, json_path=json_path)
                continue
```

```python
# -------------------------------------------------------------
# ⏩ AFTER (التعديل الجراحي المعتمد):
# -------------------------------------------------------------
                except Exception as e:
                    log_event("error", f"فشل تجديد كوكيز الحساب: {e}", email=curr_email)
                
                # فحص هل تم عزل الحساب بالفعل في الخطوة السابقة؟
                latest_accs = read_accounts_safe(json_path)
                check_acc = next((a for a in latest_accs if isinstance(a, dict) and a.get("email") == curr_email), {})
                if check_acc.get("quarantined") is True or check_acc.get("status") == "suspended":
                    log_event("warning", f"الحساب {curr_email} تم عزله نهائياً — تخطٍ فوري للحساب التالي بدون كول داون", email=curr_email)
                    tried_emails.add(curr_email)
                    continue

                notify_account_selection_observer(
                    bridge_cfg,
                    "session-refresh-failed",
                    status="auth_failed",
                    refresh_count=state_refresh.get(curr_email, 0),
                )
                update_account_data(curr_email, {"cooldown_until": time.time() + 1800, "status": "auth_failed", "active": False}, json_path=json_path)
                continue
```

---

### 🛡️ 6. الدوال التي لن تُمس نهائياً (Unchanged Functions Protection)
لضمان عدم حدوث أي Regression وحماية استقرار البوت:
* `send_chat()` في `01.03` (السطور `L1200-L2400`): **لن تُمس نهائياً**.
* دوال تيليجرام `_call_telegram_api_json()` ومولدات الرسائل (السطور `L1145-L1700`): **لن تُمس نهائياً**.
* نظام الساندبوكس وتنزيل الأرشيف `download_project_sandbox()`: **لن يُمس نهائياً**.
* إدارة الفروع والـ GitHub API: **لن تُمس نهائياً**.

---

## 🔄 7. خطة التراجع الفوري الشاملة (Rollback Plan)

في حال حدوث أي خطأ غير متوقع بعد التنفيذ:
1. **تثبيت النسخ الاحتياطية قبل أي لمس:**
   ```bash
   cp "01.33_telegram_gen_bridge.py" "01.33_telegram_gen_bridge.py.anchor_pre_quarantine"
   cp "01.03Genspark_claude-opus-5-code.py" "01.03Genspark_claude-opus-5-code.py.anchor_pre_quarantine"
   ```
2. **أمر الاسترجاع الفوري (أقل من ثانية واحدة):**
   ```bash
   cp "01.33_telegram_gen_bridge.py.anchor_pre_quarantine" "01.33_telegram_gen_bridge.py"
   cp "01.03Genspark_claude-opus-5-code.py.anchor_pre_quarantine" "01.03Genspark_claude-opus-5-code.py"
   ```

---

## 🚦 8. بوابة الاعتماد الصريحة (Bolla Approval Gate)

> ✋ **التوقف الإلزامي وفق الدستور:**  
> تم تدوين وتوثيق الخطة الهندسية بالكامل وبكافة تفاصيلها السطرية والهاشات دون كتابة سطر كود تنفيذي واحد داخل سكريبتات مجلد 31.  
> 
> **بانتظار موافقتك الصريحة بكلمة "GO" لنبدأ أخذ المراسي التشفيرية والتنفيذ الجراحي الفوري!** 🫡🚀
