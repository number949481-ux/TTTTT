# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════════════════
🛡️ GENSPARK ULTRA MASTER VERIFIER & QUARANTINE PIPELINE (V2.0 Full Core)
════════════════════════════════════════════════════════════════════════════════
ملف العزل المعتمد: accounts_genspark_blocked_failed__block_failed.json
مستخلص ومدمج من السكريبتات الأربعة (01.21 + 01 + 02 + 03) لتشغيل مجلد 31.
════════════════════════════════════════════════════════════════════════════════
"""

import os
import re
import time
import json
import pathlib
import threading
from typing import Tuple, Dict, Any, Optional

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    import requests as cffi_requests
    HAS_CURL_CFFI = False

# ── 1. الثوابت المركزية ───────────────────────────────────────────────────────
GENSPARK_HOST = "https://www.genspark.ai"
LOGIN_HOST = "https://login.genspark.ai"
B2C_TENANT = "gensparkad.onmicrosoft.com"
B2C_POLICY = "B2C_1_new_login"
B2C_BASE = f"{LOGIN_HOST}/{B2C_TENANT}/{B2C_POLICY}"

ENDPOINT_BALANCE = f"{GENSPARK_HOST}/api/payment/get_credit_balance"
ENDPOINT_SUBSCRIPTIONS = f"{GENSPARK_HOST}/api/payment/current_subscriptions"
ENDPOINT_USER = f"{GENSPARK_HOST}/api/user"
ENDPOINT_USER_UPDATE = f"{GENSPARK_HOST}/api/user/update"

# الاسم المعتمد نهائياً من المستخدم
QUARANTINE_FILENAME = "accounts_genspark_blocked_failed__block_failed.json"
VAULT_LOCK = threading.Lock()


# ── 2. مصفوفة الحالات الدقيقة (Strict Diagnostic Classification) ───────────────
class AccountVerdict:
    # 🔴 موت قطعي لا رجعة فيه -> عزل فوري في accounts_genspark_blocked_failed__block_failed.json
    SUSPENDED = "SUSPENDED"                    # محظور برابط أو نص user_suspended
    USER_NOT_FOUND = "USER_NOT_FOUND"          # اليوزر ممسوح / غير موجود status == -5
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"# خطأ إيميل أو باسورد (400 / AADB2C90157)
    INACTIVE_ACCOUNT = "INACTIVE_ACCOUNT"      # حساب ملغي أو معطل من طرف جين سبارك

    # 🟡 حالات قابلة للإصلاح أو مؤقتة -> لا يُعزل الحساب أبداً
    SESSION_EXPIRED = "SESSION_EXPIRED"        # 401 محتاج Re-login
    RATE_LIMITED = "RATE_LIMITED"              # 429 طلبات كثيرة (تبريد مؤقت)
    CLOUDFLARE_BLOCKED = "CLOUDFLARE_BLOCKED"  # 403 / Turnstile (مشكلة IP أو بروكسي)
    NETWORK_ERROR = "NETWORK_ERROR"            # انقطاع اتصال أو Timeout مؤقت
    EMPTY_BALANCE = "EMPTY_BALANCE"            # شغال لكن رصيده 0 (تبريد حتى التجديد)
    
    # 🟢 حساب سليم 100% ومؤهل للشغل
    ACTIVE = "ACTIVE"


# ── 3. دوال المعالجة الذكية والبحث المتعمق (Deep Search) ──────────────────────
def extract_credits_recursive(obj: Any) -> Optional[int]:
    """بحث متعمق في الـ JSON لاستخراج الرصيد المتاح وتخطي الرصيد المستهلك (credits/amount)"""
    if not isinstance(obj, dict):
        return None
    priority_keys = ["total_credits", "balance", "remained_credits", "remaining_credits", "new_balance", "points"]
    for k in priority_keys:
        if k in obj and obj[k] is not None:
            try:
                return int(obj[k])
            except (ValueError, TypeError):
                pass
    for sub in ["data", "user", "user_info", "account", "balance_info", "profile"]:
        sub_obj = obj.get(sub)
        if isinstance(sub_obj, dict):
            res = extract_credits_recursive(sub_obj)
            if res is not None:
                return res
    return None


def is_suspended_response(resp, location_header: str = "") -> bool:
    """فحص جراحي ثلاثي الأبعاد لكشف الحظر Suspended في كل أجزاء الاستجابة"""
    # 1. فحص هيدر Location
    loc = location_header.lower()
    if "user_suspended" in loc or "suspended" in loc:
        return True
    
    # 2. فحص كود الاستجابة والتحويلات
    if resp is not None:
        if getattr(resp, "status_code", 0) in [302, 307] and "suspended" in loc:
            return True
        # 3. فحص الرابط النهائي المحول
        if "user_suspended" in str(getattr(resp, "url", "")).lower():
            return True
        # 4. فحص تاريخ سلسلة التحويلات بالكامل (Redirect History)
        for h in getattr(resp, "history", []):
            if "user_suspended" in str(h.url).lower() or "user_suspended" in h.headers.get("location", "").lower():
                return True
        # 5. فحص محتوى النص في حالة 200
        text = str(getattr(resp, "text", "")).lower()
        if "user_suspended" in text:
            return True
    return False


# ── 4. تسجيل دخول B2C الكامل فائق الحصانة (B2C Full Authenticator) ─────────────
def execute_bulletproof_b2c_login(
    email: str,
    password: str,
    proxies: Optional[dict] = None,
    timeout: int = 25
) -> Tuple[Optional[dict], str, str]:
    """
    تسجيل دخول B2C رباعي الخطوات مع حصانة مطلقة:
    يرجع: (cookies, verdict, detail_message)
    """
    if not email or not password:
        return None, AccountVerdict.INVALID_CREDENTIALS, "Missing email or password"

    sess = cffi_requests.Session(impersonate="chrome120") if HAS_CURL_CFFI else cffi_requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    if proxies:
        sess.proxies.update(proxies)

    try:
        # [الخطوة 1]: جلب CSRF + TransId + PageId الديناميكي
        r1 = sess.get(f"{GENSPARK_HOST}/api/login", allow_redirects=True, timeout=timeout)
        if r1.status_code == 403 or "challenge" in r1.text.lower():
            return None, AccountVerdict.CLOUDFLARE_BLOCKED, "Cloudflare challenge on /api/login"
        
        csrf = re.search(r'"csrf"\s*:\s*"([^"]+)"', r1.text)
        tx = re.search(r'"transId"\s*:\s*"([^"]+)"', r1.text)
        page_id_match = re.search(r'"pageId"\s*:\s*"([^"]+)"', r1.text)
        if not csrf or not tx:
            return None, AccountVerdict.NETWORK_ERROR, "Tokens missing from login landing page"

        page_id = page_id_match.group(1) if page_id_match else "CombinedSigninAndSignup"

        # [الخطوة 2]: إرسال بيانات الاعتماد (SelfAsserted)
        r2 = sess.post(
            f"{B2C_BASE}/SelfAsserted",
            params={"tx": tx.group(1), "p": B2C_POLICY},
            data={"email": email, "password": password, "request_type": "RESPONSE"},
            headers={
                "x-csrf-token": csrf.group(1),
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": str(r1.url),
                "Origin": LOGIN_HOST,
                "Accept": "application/json",
            },
            timeout=timeout,
        )
        r2_text = r2.text.lower()
        if '"status":"200"' not in r2.text:
            if any(err in r2_text for err in ["password", "incorrect", "aadb2c90157", "user does not exist", "400"]):
                return None, AccountVerdict.INVALID_CREDENTIALS, f"B2C Auth Failed: {r2.text[:120]}"
            if "captcha" in r2_text or "recaptcha" in r2_text:
                return None, AccountVerdict.NETWORK_ERROR, "B2C Captcha required"
            return None, AccountVerdict.NETWORK_ERROR, f"B2C Step 2 unexpected: {r2.text[:120]}"

        # [الخطوة 3]: تأكيد المصادقة وجلب رابط التفويض
        confirmed_endpoints = [
            f"{B2C_BASE}/api/{page_id}/confirmed",
            f"{B2C_BASE}/api/CombinedSigninAndSignup/confirmed",
            f"{B2C_BASE}/api/SelfAsserted/confirmed"
        ]
        auth_url = None
        for ep in confirmed_endpoints:
            r3 = sess.get(ep, params={"csrf_token": csrf.group(1), "tx": tx.group(1), "p": B2C_POLICY}, allow_redirects=False, timeout=timeout)
            loc = r3.headers.get("location", r3.headers.get("Location", ""))
            if loc and "/api/auth" in loc:
                auth_url = loc
                break

        if not auth_url:
            return None, AccountVerdict.NETWORK_ERROR, "Confirmed step did not yield /api/auth URL"

        # [الخطوة 4]: فحص كود التفويض واصطياد الحظر Suspended
        r4 = sess.get(auth_url, allow_redirects=False, timeout=timeout)
        loc4 = r4.headers.get("location", r4.headers.get("Location", ""))

        if is_suspended_response(r4, loc4):
            return None, AccountVerdict.SUSPENDED, f"Suspended in Step 4 redirect: {loc4}"

        # متابعة التحويل للرابط النهائي
        if loc4:
            target_url = loc4 if loc4.startswith("http") else f"{GENSPARK_HOST}{loc4}"
            r4_final = sess.get(target_url, allow_redirects=True, timeout=timeout)
            if is_suspended_response(r4_final):
                return None, AccountVerdict.SUSPENDED, f"Suspended in Step 4 landing URL: {r4_final.url}"

        # استخراج الكوكيز وتثبيتها على النطاقين
        cookies = dict(sess.cookies)
        if "session_id" in cookies:
            return cookies, AccountVerdict.ACTIVE, "Session acquired successfully"

        return None, AccountVerdict.NETWORK_ERROR, "No session_id cookie after B2C callback"

    except Exception as e:
        return None, AccountVerdict.NETWORK_ERROR, f"B2C Exception: {str(e)}"


# ── 5. الفاحص الشامل للحساب وتفعيل الميزات (Master Inspector & Healer) ─────────
def master_inspect_and_heal_account(
    email: str,
    password: str,
    existing_cookies: Optional[dict] = None,
    account_dict: Optional[dict] = None,
    proxies: Optional[dict] = None,
    min_required_balance: int = 1,
    timeout: int = 20
) -> dict:
    """
    الدورة الكاملة الشاملة لفحص الحساب:
    1. تجربة الكوكيز الموجودة دون حرق طلبات B2C.
    2. لو انتهت الجلسة (401) -> إعادة تسجيل دخول B2C فوري.
    3. فحص الحظر من /api/payment/get_credit_balance.
    4. فحص وجود اليوزر من /api/user.
    5. قراءة الرصيد واشتراك Plus وعروض الشهر الأول.
    6. الفحص والتفعيل التلقائي لـ AI Data Retention.
    """
    sess = cffi_requests.Session(impersonate="chrome120") if HAS_CURL_CFFI else cffi_requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"{GENSPARK_HOST}/",
        "Origin": GENSPARK_HOST,
    })
    if proxies:
        sess.proxies.update(proxies)

    def _inject_cookies(c_dict):
        for k, v in c_dict.items():
            sess.cookies.set(k, v, domain=".genspark.ai")
            sess.cookies.set(k, v, domain="www.genspark.ai")
        sess.cookies.set("agree_terms", "1", domain=".genspark.ai")
        sess.cookies.set("from_auth", "1", domain=".genspark.ai")
        sess.cookies.set("gslogin", "1", domain=".genspark.ai")

    current_cookies = dict(existing_cookies or {})
    relogin_attempted = False

    # ── أ. محاولة الفحص بالكوكيز الحالية ──
    if current_cookies and "session_id" in current_cookies:
        _inject_cookies(current_cookies)
        try:
            r_bal = sess.get(ENDPOINT_BALANCE, timeout=timeout, allow_redirects=False)
            loc_bal = r_bal.headers.get("location", r_bal.headers.get("Location", ""))

            # فحص الحظر المباشر
            if is_suspended_response(r_bal, loc_bal):
                return {"verdict": AccountVerdict.SUSPENDED, "email": email, "balance": 0, "is_dead": True, "detail": "Suspended on balance check"}

            # لو الجلسة منتهية 401 نحتاج Re-login
            if r_bal.status_code == 401:
                current_cookies = {}
        except Exception:
            current_cookies = {}

    # ── ب. إعادة تسجيل الدخول لو الكوكيز غير صالحة ──
    if not current_cookies or "session_id" not in current_cookies:
        relogin_attempted = True
        new_cookies, b2c_verdict, b2c_detail = execute_bulletproof_b2c_login(email, password, proxies=proxies, timeout=timeout)
        if b2c_verdict in [AccountVerdict.SUSPENDED, AccountVerdict.INVALID_CREDENTIALS]:
            return {"verdict": b2c_verdict, "email": email, "balance": 0, "is_dead": True, "detail": b2c_detail}
        if not new_cookies:
            return {"verdict": b2c_verdict, "email": email, "balance": 0, "is_dead": False, "detail": b2c_detail}
        current_cookies = new_cookies
        sess.cookies.clear()
        _inject_cookies(current_cookies)

    # ── ج. الفحص النهائي الصارم للرصيد واليوزر والحظر بعد ثبوت الكوكيز ──
    try:
        # 1. فحص الرصيد والحظر
        r_bal = sess.get(ENDPOINT_BALANCE, timeout=timeout, allow_redirects=False)
        loc_bal = r_bal.headers.get("location", r_bal.headers.get("Location", ""))
        if is_suspended_response(r_bal, loc_bal):
            return {"verdict": AccountVerdict.SUSPENDED, "email": email, "balance": 0, "is_dead": True, "detail": "Suspended detected in balance endpoint"}

        balance = 0
        org_pool = None
        if r_bal.status_code == 200:
            b_data = r_bal.json()
            balance = extract_credits_recursive(b_data) or 0
            org_pool = b_data.get("data", {}).get("org_pool_status")

        # 2. فحص نشاط وجود اليوزر من /api/user (من سكريبت 01.21)
        r_user = sess.get(ENDPOINT_USER, timeout=timeout, allow_redirects=False)
        if r_user.status_code == 200:
            try:
                u_data = r_user.json()
                st_val = u_data.get("status")
                msg_txt = str(u_data.get("message", "")).lower()
                if st_val == -5 or "user not found" in msg_txt:
                    return {"verdict": AccountVerdict.USER_NOT_FOUND, "email": email, "balance": 0, "is_dead": True, "detail": "status -5 user not found"}
                if st_val not in [0, "0", 200, "200"]:
                    return {"verdict": AccountVerdict.INACTIVE_ACCOUNT, "email": email, "balance": 0, "is_dead": True, "detail": f"Inactive status {st_val}"}

                # 3. الفحص والتفعيل الذكي لـ AI Data Retention (مع كاش الـ JSON لمنع تكرار الفحص)
                data_retention_enabled = False
                already_cached = bool(account_dict and account_dict.get("data_retention_enabled") is True)
                if already_cached:
                    data_retention_enabled = True
                    data_retention_source = "cached_in_json"
                else:
                    cogen = u_data.get("data", {}).get("cogen", {})
                    current_disabled = cogen.get("disable_data_retention")
                    if current_disabled is False:
                        data_retention_enabled = True
                        data_retention_source = "already_enabled_in_genspark"
                    elif current_disabled is True:
                        try:
                            r_up = sess.post(
                                ENDPOINT_USER_UPDATE,
                                json={"disable_data_retention": False},
                                headers={"Content-Type": "application/json"},
                                timeout=15
                            )
                            if r_up.status_code == 200 and r_up.json().get("status") == 0:
                                data_retention_enabled = True
                                data_retention_source = "newly_enabled"
                            else:
                                data_retention_source = "activation_failed"
                        except Exception as e_up:
                            data_retention_source = f"error_{e_up}"
                    else:
                        data_retention_source = "cogen_missing"
            except Exception:
                data_retention_enabled = False
                data_retention_source = "user_parse_exception"

        # 4. فحص اشتراك Plus وعروض الشهر الأول
        is_plus = False
        has_free_month = False
        try:
            r_sub = sess.get(ENDPOINT_SUBSCRIPTIONS, timeout=15, allow_redirects=False)
            if r_sub.status_code == 200:
                sub_data = r_sub.json()
                if sub_data.get("subType") == "plus" or sub_data.get("membershipStatus") == "active":
                    is_plus = True
                for coup in sub_data.get("wallet_coupons", []):
                    if coup.get("source") == "first_month" or "first_month" in coup.get("coupon_key", ""):
                        has_free_month = True
                        break
        except Exception:
            pass

        # 5. تقييم الرصيد النهائي
        result_payload = {
            "verdict": AccountVerdict.EMPTY_BALANCE if balance < min_required_balance else AccountVerdict.ACTIVE,
            "email": email,
            "balance": balance,
            "cookies": current_cookies,
            "is_plus": is_plus,
            "has_free_month": has_free_month,
            "org_pool": org_pool,
            "data_retention_enabled": data_retention_enabled,
            "data_retention_source": data_retention_source,
            "needs_json_retention_save": bool(data_retention_enabled and not already_cached),
            "is_dead": False,
            "relogin_done": relogin_attempted
        }
        return result_payload

    except Exception as e:
        return {"verdict": AccountVerdict.NETWORK_ERROR, "email": email, "balance": 0, "is_dead": False, "detail": f"Inspector error: {e}"}


# ── 6. خزنة العزل الذرية (Atomic Quarantine Vault) ─────────────────────────────
def quarantine_account_atomic(
    account_entry: dict,
    verdict: str,
    base_dir: pathlib.Path,
    detail: str = ""
) -> bool:
    """
    عزل ذري آمن تماماً داخل ملف:
    accounts_genspark_blocked_failed__block_failed.json
    - يمنع التكرار
    - يسجل تقريراً تشخيصياً كاملاً عن سبب الوفاة
    - يضمن عدم فقدان أي بيانات بـ Lock ذري واستبدال آمن .tmp
    """
    email = account_entry.get("email", "").strip()
    if not email:
        return False

    quarantine_file = base_dir / QUARANTINE_FILENAME
    with VAULT_LOCK:
        try:
            records = []
            if quarantine_file.exists():
                try:
                    with open(quarantine_file, "r", encoding="utf-8") as f:
                        records = json.load(f)
                    if not isinstance(records, list):
                        records = []
                except Exception:
                    records = []

            # فحص عدم التكرار بالإيميل الأساسي
            existing = {r.get("email", "").strip().lower() for r in records if isinstance(r, dict)}
            if email.lower() not in existing:
                dead_payload = dict(account_entry)
                dead_payload.update({
                    "status": "suspended",
                    "quarantine_verdict": verdict,
                    "quarantine_detail": detail,
                    "quarantined_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "active": False,
                    "balance": 0,
                    "cookies": {}  # تصفير الكوكيز الميتة
                })
                records.append(dead_payload)

                tmp_file = quarantine_file.with_suffix(".tmp")
                with open(tmp_file, "w", encoding="utf-8") as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
                tmp_file.replace(quarantine_file)
                print(f"\033[91m\033[1m[🚫 تم العزل الدائم في {QUARANTINE_FILENAME}]: {email} | الحكم: {verdict}\033[0m")
                return True
        except Exception as err:
            print(f"❌ خطأ أثناء العزل: {err}")
            return False
    return False
