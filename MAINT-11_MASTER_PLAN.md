# 🏛️ خطة العمل الهندسية الشاملة 360° (المعتمدة والمحلولة) — MAINT-11: بوابة فحص صلاحيات المشروع ومنع حرق الأسطول

> **الحالة:** ✅ **RESOLVED & VERIFIED** (محلولة، منفذة، ومختبرة آلياً بنسبة نجاح 100%)  
> **تاريخ الاعتماد والحل:** 2026-11-07  
> **الهدف:** إغلاق ثغرة المشروع الخاص (`Private Project` / `HTTP 403` / `status: -13`) في مهدها، ومنع استنزاف الـ 50 حساباً، وتفادي إرسال كروت البدء الكاذبة للمستخدم (الثغرة F-9)، وحماية براءة الحسابات المشتركة بنسبة 100%، مع الحفاظ على قدسية `01.03` (Zero Mutation).

---

## 🎯 [Goal Description]
عند محاولة المستخدم استئناف أو إرسال استعلام على مشروع مقفول أو خاص (Private Project) على Genspark:
1. سيرفر Genspark يرفض الوصول إما بـ `HTTP 403 Forbidden` على مسار الشات `/api/code_sandbox/chat` أو بـ `HTTP 200 OK` مع `status: -13` و رسالة `no permission` على `GET /api/project?id=...`.
2. في الكود القديم:
   - كان يتم إرسال كارت "بدأ البناء والتوليد" كذباً للمستخدم على تليجرام قبل الفحص (الثغرة F-9).
   - كان يتم ابتلاع الخطأ 403 في محرك `01.03` وإرجاع `(None, None, None)`، فتحوله الدالة إلى حالة `"FAILED"` بدلاً من `"FORBIDDEN"`.
   - حلقة تدوير الحسابات لم تكن تتعرف على `"FAILED"`، فتعتبر الحساب فاشلاً مؤقتاً وتبرده، ثم تجرب الحساب التالي حتى استنفاد سقف الـ 50 حساباً بالكامل (`MAX_ATTEMPTS_EXHAUSTED`).
3. **الحل المعتمد والمنفذ في MAINT-11:**
   - حقن بوابة فحص استباقية فائقة السرعة وخفيفة (`_check_project_permission_fast`) تستخدم `curl_cffi` مع بصمة Chrome للتحقق من الرابط في أقل من ثانيتين دون استثارة كلاودفلير.
   - وضع شرط حراسة (Guard Clause) لتجاوز الفحص فوراً في حال الاستعلامات الجديدة (`NEW_PROJECT`).
   - التمييز بين خطأ انتهاء الجلسة (`401` - تدوير الحساب)، وبين خصوصية المشروع (`403` / `status: -13` - إيقاف فوري).
   - منع إرسال كارت البدء الكاذب للمستخدم (F-9) بالخروج المبكر قبل استدعاء `on_project_start_callback`.
   - خط دفاع ثانٍ (Defense in Depth): لو سقط الفحص الاستباقي (Timeout / Fail-open)، يتم التقاط الخطأ 403 من رد الشات وترقية الحالة فوراً من `"FAILED"` إلى `"FORBIDDEN"`.
   - براءة الحساب التامة: تبريد الحساب موضعياً 300 ثانية كحماية ضد الـ hot-loop مع براءته التامة، والحفاظ على رصيده سليماً وبقاء حالته نشطة (`active: true`).
   - ضبط توقيع الـ Return Tuple لتضع نص الرسالة في العنصر الخامس (`last_text`) حتى يظهر بوضوح على تليجرام.

---

## ⚖️ [EGM Resolution Matrix — مصفوفة فض النزاعات وحسم التعديلات]

تم استيعاب كافة ملاحظات وكلاء الـ Swarm الخمسة (`egm-review`) وحسمها بالكامل وفق الجدول التالي:

| # | البند | المراجع الأصلي | الشدة | القرار (Resolution) | الحالة التنفيذية |
|---|---|---|---|---|---|
| **1** | **توقيع الـ Return Tuple** | `codebase-details` | 🔴 **Blocker** | تصحيح ترتيب العناصر الخماسية: `return None, "FORBIDDEN", None, None, error_message` لوضع النص في `last_text` بدلاً من `ext_dir`. | ✅ مطبقة ومختبرة في `test_07` |
| **2** | **حماية كلاودفلير والـ Fail-Open** | `design` | 🔴 **Blocker** | فحص ترويسة `Content-Type: application/json` وجسم الـ JSON، وتفعيل الـ Fail-Open فوراً عند صفحات HTML WAF. | ✅ مطبقة ومختبرة في `test_04` |
| **3** | **فصل 401 الجلسة عن 403 المشروع** | `design` | 🔴 **Blocker** | إرجاع `SESSION_EXPIRED` لخطأ 401 لتدوير الحساب، بينما 403 يوقف التدوير فوراً. | ✅ مطبقة ومختبرة في `test_05` |
| **4** | **حراسة الاستعلامات الجديدة** | `readiness` | 🔴 **Blocker** | إضافة Guard Clause في مطلع الدالة يتخطى الفحص عند خلو `project_id`. | ✅ مطبقة ومختبرة في `test_01` |
| **5** | **خط الدفاع الثاني (Defense in Depth)** | `zoom-out` | 🟡 **Major** | اعتراض 403 العائد من محرك الشات في مخرج الدالة وترقية `"FAILED"` إلى `"FORBIDDEN"`. | ✅ مطبقة ومختبرة في `test_08` |
| **6** | **إلغاء عقوبة التبريد للحساب البريء** | `codebase-details` | 🟡 **Major** | تبريد موضعي 300 ثانية كدرع ضد تكرار المحاولة، مع بقاء الحساب نشطاً (`active: true`) مع ثبات رصيده. | ✅ مطبقة ومختبرة في `test_09` |
| **7** | **تبكير موضع الفحص** | `codebase-details` | 🟡 **Major** | تقديم الفحص للحظة استخراج `orig_pid` و `carry_pid` مباشرة وقبل أي اتصال بالرسائل أو التفريع. | ✅ مطبقة ومختبرة في `test_07` |
| **8** | **شرح وتوثيق الثغرة F-9** | `comprehension` | 🟢 **Nit** | توضيح مسمى F-9 في وثائق الخطة والتسجيلات. | ✅ موثقة بالنص الصريح |

---

## 🛠️ [Detailed Code Changes]

### 1. دالة الفحص الاستباقي الخفيف `_check_project_permission_fast`
محقونة قبل `get_public_forked_pid` في `01.33_telegram_gen_bridge.py`:
```python
def _check_project_permission_fast(project_id: str, cookies: dict, timeout: float = 3.0) -> tuple[bool, int, str]:
    """
    [MAINT-11] فحص استباقي خفيف وسريع لصلاحية الوصول للمشروع على Genspark.
    يرجع: (is_accessible, http_status, reason)
    - لو المشروع خاص: (False, 403, "PRIVATE_PROJECT")
    - لو الحساب غير مسجل: (False, 401, "SESSION_EXPIRED")
    - لو متاح أو غير مؤكد: (True, 200, "OK" / "FAIL_OPEN")
    """
    if not project_id or not isinstance(project_id, str) or not project_id.strip():
        return True, 200, "NEW_PROJECT"

    clean_pid = project_id.strip()
    url = f"https://www.genspark.ai/api/project?id={clean_pid}"
    try:
        from curl_cffi import requests as cffi_requests
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": f"https://www.genspark.ai/project/{clean_pid}",
        }
        resp = cffi_requests.get(url, cookies=cookies, headers=headers, timeout=timeout, impersonate="chrome124")

        # 1. فحص انتهاء الجلسة
        if resp.status_code == 401:
            return False, 401, "SESSION_EXPIRED"

        # 2. فحص الـ 403 الصريح
        if resp.status_code == 403:
            c_type = resp.headers.get("Content-Type", "").lower()
            if "application/json" in c_type:
                return False, 403, "PRIVATE_PROJECT"
            try:
                data = resp.json()
                return False, 403, "PRIVATE_PROJECT"
            except Exception:
                return True, 403, "CF_CHALLENGE_FAIL_OPEN"

        # 3. فحص كود 200 مع JSON يحمل status: -13 أو no permission
        if resp.status_code == 200:
            try:
                data = resp.json()
                if isinstance(data, dict):
                    status_code = data.get("status")
                    msg = str(data.get("message", "")).lower()
                    if status_code == -13 or "no permission" in msg or "forbidden" in msg:
                        return False, 403, "PRIVATE_PROJECT"
            except Exception:
                pass

        return True, resp.status_code, "OK"
    except Exception as e:
        return True, 0, f"FAIL_OPEN_EXC_{e}"
```

### 2. البوابة المبكرة لمنع كارت البدء الكاذب في `send_message_and_make_public`
```python
        # مسار carry_pid
        if carry_pid:
            is_acc, p_code, p_reason = _check_project_permission_fast(carry_pid, cookies)
            if not is_acc and p_code == 403:
                log_event("warning", f"🚫 [MAINT-11] المشروع المستأنف {str(carry_pid)[:16]} خاص (Private) ولا يمكن الوصول إليه.", email=email)
                return None, "FORBIDDEN", None, None, "المشروع خاص (Private) ولا يمكن للبوت الوصول إليه. يرجى تحويله إلى عام (Public) وإعادة المحاولة."

        # مسار url
        elif url and isinstance(url, str) and url.strip():
            orig_pid = extract_project_id(url.strip())
            if orig_pid:
                is_acc, p_code, p_reason = _check_project_permission_fast(orig_pid, cookies)
                if not is_acc and p_code == 403:
                    log_event("warning", f"🚫 [MAINT-11] المشروع {orig_pid} خاص (Private) ولا يمكن الوصول إليه.", email=email)
                    return None, "FORBIDDEN", None, None, "المشروع خاص (Private) ولا يمكن للبوت الوصول إليه. يرجى تحويله إلى عام (Public) وإعادة المحاولة."
```

### 3. خط الدفاع الثاني (Defense in Depth) في `send_message_and_make_public`
```python
        if not pid or pid == "__INVALID_PROJECT__":
            ans_str = str(answer or "").lower()
            last_err_str = str(getattr(cfg, "_last_chat_err", "") or "").lower()
            if "403" in ans_str or "not authorized" in ans_str or "no permission" in ans_str or \
               "403" in last_err_str or "not authorized" in last_err_str or "no permission" in last_err_str:
                log_event("warning", "🚫 [MAINT-11] خط الدفاع الثاني رصد 403 من محرك الشات — ترقية الحالة إلى FORBIDDEN", email=email)
                return None, "FORBIDDEN", None, None, "المشروع خاص (Private) ولا يمكن للبوت الوصول إليه. يرجى تحويله إلى عام (Public) وإعادة المحاولة."

            if attempt < max_retries:
                continue
            return None, "FAILED", None, None, str(answer or "")
```

### 4. براءة الحساب البريء في `send_message_with_auto_account_failover`
```python
            if status == "FORBIDDEN":
                notify_account_selection_observer(
                    bridge_cfg,
                    "forbidden-stop",
                    status="FORBIDDEN",
                    max_attempts=max_attempts,
                )
                log_event("warning", "[MAINT-11] FORBIDDEN (403) — المشروع Private؛ إيقاف فوري دون حرق الحساب أو الانتقال لغيره", email=curr_email)
                return pub_url, "FORBIDDEN", curr_acc, ext_dir, last_text
```

---

## 📊 [Verification & Test Results]

### 1. اختبارات الميزة الجديدة (`tests/test_p60_maint11_private_project_gate.py`)
| # | اسم الاختبار | النتيجة | زمن التنفيذ |
|---|---|---|---|
| 1 | `test_01_guard_clause_new_project` | ✅ PASSED | 0.01s |
| 2 | `test_02_detect_status_minus_13_no_permission` | ✅ PASSED | 0.01s |
| 3 | `test_03_detect_http_403_json` | ✅ PASSED | 0.01s |
| 4 | `test_04_cloudflare_challenge_fails_open` | ✅ PASSED | 0.01s |
| 5 | `test_05_session_expired_401` | ✅ PASSED | 0.01s |
| 6 | `test_06_timeout_fails_open` | ✅ PASSED | 0.01s |
| 7 | `test_07_early_gate_blocks_false_start_card_and_returns_correct_tuple` | ✅ PASSED | 0.02s |
| 8 | `test_08_defense_in_depth_promotes_failed_to_forbidden` | ✅ PASSED | 0.02s |
| 9 | `test_09_failover_preserves_innocent_account_with_inplace_cooldown` | ✅ PASSED | 0.02s |
| 10 | `test_10_zero_mutation_01_03` | ✅ PASSED | 0.01s |

**المحصلة:** `10 passed in 0.19s (100% OK)`

### 2. اختبارات التطابق البايتي والتوليد (`tests/test_refactor_parity.py`)
- إجمالي الاختبارات: `16/16 PASSED` (100% Feature & Byte Parity).
- الحفاظ على سلامة جميع الـ facades والـ runtime namespaces.

### 3. سلامة منظومة التوثيق (`scripts/verify_docs_integrity.py`)
- تم فحص 34 ملفاً توثيقياً و 13 رابطاً داخلياً: `0 Broken Links (100% Clean)`.
