#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════════════════
🚀 Genspark Master Tri-State Account Manager & Cleaner (v2.0)
نظام الإدارة والفرز الثلاثي الموحد لحسابات Genspark
════════════════════════════════════════════════════════════════════════════════
الملفات الناتجة المنفصلة (The 3-File Architecture):
 1. 🎯 accounts_success.json : الحسابات السليمة والنشطة (شغالة + رصيد + هدية حديثة <= 14 يوم)
 2. 📦 accounts_delayed_gifts_credits.json : معزل الحسابات متأخرة الهدية (شغالة وباسورد صح لكن انقطعت هديتها > 14 يوم)
 3. 🗑️ accounts_failed.json   : الحسابات الفاشلة والميتة (باسوورد غلط / حظر / تعليق / دومين محظور)
 4. 📁 accounts_genspark.json : الملف الأساسي المصفى النظيف 100% (مرتب تنازلياً بالرصيد في القمة)

المميزات المدمجة:
 • 💰 فحص وتحديث الرصيد الحقيقي الحي (Live Real Credits).
 • 📊 ترتيب تنازلي فوري بالأعلى رصيداً في قمة الملفات الناجحة (Sort by Balance).
 • 🔄 تجديد تلقائي ذكي للجلسات عبر Azure AD B2C الرسمي لو الكوكيز منتهية.
 • ✂️ قص ونقل ذري حقيقي (Cut & Move): الحساب المعزول أو الميت يُحذف من الملف الأساسي فورياً.
 • 🔄 دعم إنعاش الحسابات المعزولة (--revive) واسترجاعها للأساسي والناجح إذا عاد لها الرصيد.
 • 🛡️ حفظ ذري آمن (Atomic Writes) مع نسخ احتياطية زمنية (.bak) لمنع أي تلف للبيانات.
 • ⚡ 100% بدون متصفح (Pure Requests / Zero Browser).
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import signal
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ── ضبط تشفير التيرمينال لويندوز لدعم العربية والرموز بأمان ──
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── ألوان التيرمينال عبر colorama مع fallback آمن ──
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    G = Fore.GREEN; R = Fore.RED; Y = Fore.YELLOW; C = Fore.CYAN
    M = Fore.MAGENTA; W = Fore.WHITE; B = Style.BRIGHT; RST = Style.RESET_ALL
except ImportError:
    class _EmptyColor:
        def __getattr__(self, _): return ""
    G = R = Y = C = M = W = B = RST = ""

SCRIPT_DIR = Path(__file__).resolve().parent

# ── استيراد دوال التسجيل وفحص الرصيد من الماستر مانجر ──
try:
    from genspark_master_account_manager import do_b2c_login, get_session, check_account_balance
except ImportError:
    sys.path.insert(0, str(SCRIPT_DIR))
    sys.path.insert(0, str(SCRIPT_DIR.parent / "Genspark_Account_Manager"))
    from genspark_master_account_manager import do_b2c_login, get_session, check_account_balance

GENSPARK_HOST = "https://www.genspark.ai"
ENDPOINT_RECHARGE = f"{GENSPARK_HOST}/api/credit_audit/recharge_logs"
ENDPOINT_BALANCE = f"{GENSPARK_HOST}/api/payment/get_credit_balance"
ENDPOINT_USER_INFO = f"{GENSPARK_HOST}/api/user"
ENDPOINT_USER_UPDATE = f"{GENSPARK_HOST}/api/user/update"

# 🎯 تفعيل حفظ البيانات (False = الزرار مفتوح ومنور في الموقع لحفظ المحادثات والبيانات)
TARGET_DISABLE_RETENTION = False

# علم الإيقاف النظيف عند الضغط على Ctrl+C
IS_RUNNING = True

def handle_sigint(sig, frame):
    global IS_RUNNING
    print(f"\n{Y}{B}⚠️ تم استلام إشارة إيقاف (Ctrl+C).. جاري الحفظ الآمن والخروج...{RST}")
    IS_RUNNING = False

signal.signal(signal.SIGINT, handle_sigint)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                     ⚙️ إعدادات التشغيل السريعة (CONFIG)                      ║
# ╠════════════════════════════════════════════════════════════════════════════╣
# ║  عدّل هنا مباشرة بالماوس بكل سهولة، أو مرر الأوامر عبر سطر الأوامر (CLI)    ║
# ╚════════════════════════════════════════════════════════════════════════════╝
class Config:
    # ⏱️ الحد الأقصى للأيام بدون هدية يومية (الحساب الذي لم يستلم هدية منذ هذه المدة يُنقل للمعزل)
    STALE_GIFT_DAYS_THRESHOLD: int = 14

    # 📁 أسماء الملفات الرئيسية الثلاثة + الأساسي
    PRIMARY_FILE: str = "accounts_genspark.json"                  # الملف الأساسي المصفى النظيف
    SUCCESS_FILE: str = "accounts_success.json"                  # 1. الحسابات الناجحة النشطة
    QUARANTINE_FILE: str = "accounts_delayed_gifts_credits.json" # 2. الحسابات متأخرة الهدية
    FAILED_FILE: str = "accounts_failed.json"                    # 3. الحسابات الفاشلة والميتة
    DEAD_FILE: str = "dead_accounts.json"                        # مزامنة للملف القديم للرجوع إليه

    # 🎯 نمط الفحص:
    # "all"     : فحص جميع الحسابات في الملف بلا استثناء
    # "first_n" : فحص أول N حساب فقط
    # "random"  : سحب عينة عشوائية
    SCAN_MODE: str = "all"
    SCAN_LIMIT: int = 10

    # 📊 ترتيب تنازلي فوري (أعلى رصيد نقاط في قمة الملفات دائماً)
    SORT_BY_BALANCE: bool = True

    # 🔄 تجديد تلقائي للكوكيز المنتهية عبر تسجيل دخول B2C بالإيميل والباسورد
    AUTO_RELOGIN: bool = True

    # 🛡️ الأمان: إنشاء نسخة احتياطية .bak تلقائياً قبل أي تعديل
    AUTO_BACKUP: bool = True

    # ⏱️ مهلة التأخير العشوائي بالثواني بين كل فحص حساب (حماية ضد الـ Rate Limit)
    MIN_DELAY: float = 10.0
    MAX_DELAY: float = 60.0

    # 🧪 وضع المعاينة فقط بدون تعديل أي ملف (False = حفظ فعلي | True = معاينة)
    DRY_RUN: bool = False


# ════════════════════════════════════════════════════════════════════════════════
# 🛠️ دوال المساعدة والتاريخ والحفظ الآمن
# ════════════════════════════════════════════════════════════════════════════════
def parse_iso_dt(iso_str: Optional[str]) -> Optional[datetime]:
    """تحويل توقيت ISO إلى datetime مع timezone UTC"""
    if not iso_str:
        return None
    try:
        clean_iso = iso_str.replace("Z", "+00:00")
        if "." in clean_iso and "+" in clean_iso:
            parts = clean_iso.split("+")
            base = parts[0]
            if len(base.split(".")[1]) > 6:
                base = base.split(".")[0] + "." + base.split(".")[1][:6]
            clean_iso = base + "+" + parts[1]
        return datetime.fromisoformat(clean_iso)
    except Exception:
        return None


def format_cairo_time(dt: Optional[datetime]) -> str:
    """تحويل datetime إلى توقيت مصر المقروء"""
    if not dt:
        return "لا يوجد تاريخ"
    cairo_tz = timezone(timedelta(hours=3))
    dt_cairo = dt.astimezone(cairo_tz)
    return dt_cairo.strftime("%Y-%m-%d  %I:%M:%S %p")


def ensure_data_retention_enabled(sess, cookies: dict) -> tuple[bool, str]:
    """
    فحص وتفعيل خاصية AI Data Retention للحسابات النشطة (SRE & Security Compliant).
    يرجع: (is_enabled, status_desc)
    """
    try:
        # 1. قراءة الحالة الحالية مع حماية ضد التوجيهات
        r_user = sess.get(ENDPOINT_USER_INFO, allow_redirects=False, timeout=25)
        if r_user.status_code == 200:
            u_json = r_user.json()
            if u_json.get("status") != 0:
                return False, f"api_status_{u_json.get('status')}"

            data = u_json.get("data")
            if not isinstance(data, dict):
                return False, "missing_user_data"

            cogen = data.get("cogen")
            if not isinstance(cogen, dict):
                current_disabled = None
            else:
                current_disabled = cogen.get("disable_data_retention")

            # لو الزرار مفتوح بالفعل مسبقاً (disable == False)
            if current_disabled is False:
                return True, "already_enabled"

            # 2. إرسال أمر التفعيل فوراً
            r_update = sess.post(
                ENDPOINT_USER_UPDATE,
                json={"disable_data_retention": TARGET_DISABLE_RETENTION},
                headers={"Content-Type": "application/json"},
                allow_redirects=False,
                timeout=25,
            )
            if r_update.status_code == 200:
                up_json = r_update.json()
                if up_json.get("status") == 0:
                    return True, "newly_enabled"
                return False, f"rejected_{up_json.get('message', 'err')}"
            return False, f"update_http_{r_update.status_code}"
        elif r_user.status_code in (301, 302, 307, 308):
            return False, "redirect_to_login"
        return False, f"http_{r_user.status_code}"
    except Exception as e:
        # SRE Rule: استثناء الشبكة لا يعطل الفرز أبداً
        return False, f"exception_{type(e).__name__}"


def create_backup(file_path: Path) -> Optional[Path]:
    """إنشاء نسخة احتياطية آمنة قبل أي تعديل"""
    if not file_path.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak_path = file_path.parent / f"{file_path.name}.{timestamp}.bak"
    try:
        shutil.copy2(file_path, bak_path)
        return bak_path
    except Exception as e:
        print(f"  {R}⚠️ فشل إنشاء نسخة احتياطية للملف {file_path.name}: {e}{RST}")
        return None


def atomic_save_json(file_path: Path, data: Any) -> bool:
    """حفظ ذري آمن للملف لمنع أي تلف في حالة انقطاع التشغيل"""
    temp_path = file_path.parent / f"{file_path.name}.tmp_{random.randint(1000, 9999)}"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(file_path)
        return True
    except Exception as e:
        print(f"  {R}❌ خطأ في الحفظ الذري للملف {file_path.name}: {e}{RST}")
        if temp_path.exists():
            temp_path.unlink()
        return False


def load_accounts(file_path: Path) -> List[Dict[str, Any]]:
    """تحميل قائمة الحسابات من ملف JSON بأمان"""
    if not file_path.exists():
        return []
    try:
        content = file_path.read_text(encoding="utf-8-sig")
        data = json.loads(content)
        return data if isinstance(data, list) else data.get("accounts", [])
    except Exception as e:
        print(f"  {R}❌ فشل قراءة الملف {file_path.name}: {e}{RST}")
        return []


def resolve_file_path(filename: str) -> Path:
    """تحديد المسار الفعلي للملف والبحث في مجلدات المشروع"""
    p = Path(filename)
    if p.is_absolute() and p.exists():
        return p
    candidates = [
        SCRIPT_DIR / filename,
        SCRIPT_DIR.parent / "Genspark" / "W___webapp" / filename,
        SCRIPT_DIR.parent / "Genspark" / filename,
        SCRIPT_DIR.parent / "Genspark_Account_Manager" / filename,
    ]
    for c in candidates:
        if c.exists():
            return c
    return SCRIPT_DIR / filename


# ════════════════════════════════════════════════════════════════════════════════
# 🎯 محرك الفحص والفرز الثلاثي (Tri-State Manager Engine)
# ════════════════════════════════════════════════════════════════════════════════
class MasterDelayedGiftsManager:
    """المحرك الموحد لفرز وقص ونقل الحسابات إلى 3 ملفات رئيسية"""

    def __init__(
        self,
        primary_path: Path,
        success_path: Path,
        quarantine_path: Path,
        failed_path: Path,
        dead_path: Path,
        threshold_days: int = 14,
        sort_by_balance: bool = True,
        auto_relogin: bool = True,
        min_delay: float = 1.0,
        max_delay: float = 2.5,
    ):
        self.primary_path = primary_path
        self.success_path = success_path
        self.quarantine_path = quarantine_path
        self.failed_path = failed_path
        self.dead_path = dead_path
        self.threshold_days = threshold_days
        self.sort_by_balance = sort_by_balance
        self.auto_relogin = auto_relogin
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.now_utc = datetime.now(timezone.utc)

    def check_account_status(
        self, account: Dict[str, Any]
    ) -> Tuple[str, Optional[int], Optional[str], Optional[int], Optional[Dict[str, Any]]]:
        """
        فحص شامل للحساب: الرصيد الحي، الصلاحية، ومتى استلم آخر هدية يومية.
        يرجع: (status, days_since_gift, diagnostic_msg, balance, raw_gift)
        حالات status:
          - "HEALTHY"    : سليم وله رصيد واستلم هدية حديثة (days < threshold_days)
          - "STALE"      : سليم وشغال وباسورد صح، لكن هديته متأخرة (days >= threshold_days — الحد شامل، قرار المالك)
          - "DEAD"       : ميت أو محظور أو باسورد غلط
          - "AUTH_FAILED": خطأ شبكة مؤقت
        """
        email = account.get("email", "").strip()
        password = account.get("password", "").strip()
        cookies = account.get("cookies", {}) or {}

        sess = get_session()
        sess.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"{GENSPARK_HOST}/",
            "Origin": GENSPARK_HOST,
        })
        if cookies:
            for k, v in cookies.items():
                sess.cookies.set(k, v, domain=".genspark.ai")
                sess.cookies.set(k, v, domain="www.genspark.ai")

        # 1. فحص الجلسة والكوكيز الحالية
        bal, auth_status, _ = check_account_balance(cookies)
        if auth_status in ("suspended", "user_not_found"):
            return "DEAD", 0, f"حساب معلق ({auth_status})", 0, {"reason": auth_status}

        # 2. تجديد الجلسة بـ B2C لو منتهية
        if auth_status != "active":
            if password and self.auto_relogin:
                new_cookies, b2c_status = do_b2c_login(email, password, timeout=45)
                # 🛡️ SRE Transient Fault Handling: إعادة محاولة واحدة عند حدوث هبوط مؤقت في اتصال مايكروسوفت
                if not new_cookies and (b2c_status.startswith("network_error") or b2c_status == "login_failed"):
                    time.sleep(2.0)
                    new_cookies, b2c_status = do_b2c_login(email, password, timeout=45)
                if b2c_status == "active" and new_cookies:
                    account["cookies"] = new_cookies
                    cookies = new_cookies
                    sess = get_session()
                    sess.headers.update({
                        "Accept": "application/json, text/plain, */*",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": f"{GENSPARK_HOST}/",
                        "Origin": GENSPARK_HOST,
                    })
                    for k, v in new_cookies.items():
                        sess.cookies.set(k, v, domain=".genspark.ai")
                        sess.cookies.set(k, v, domain="www.genspark.ai")
                    # جلب الرصيد الحقيقي بعد تجديد الجلسة
                    bal, auth_status, _ = check_account_balance(new_cookies)
                elif b2c_status in ("invalid_credentials", "suspended", "domain_banned"):
                    reason_map = {
                        "invalid_credentials": "كلمة مرور خاطئة (AADB2C90054)",
                        "suspended": "حساب معلق (user_suspended)",
                        "domain_banned": "دومين محظور (403 Banned)",
                    }
                    diag_msg = reason_map.get(b2c_status, b2c_status)
                    return "DEAD", 0, diag_msg, 0, {"reason": b2c_status}
                else:
                    return "AUTH_FAILED", None, f"فشل مصادقة ({b2c_status})", 0, None
            else:
                return "DEAD", 0, "جلسة منتهية وبدون كلمة مرور للتجديد", 0, {"reason": "expired_session_no_password"}

        # تحديث الرصيد الحي وتاريخ الفحص في كائن الحساب
        real_balance = int(bal) if isinstance(bal, (int, float)) else 0
        account["balance"] = real_balance
        account["last_checked"] = datetime.now().isoformat(timespec="seconds")

        # 🛡️ حوكمة حفظ البيانات (Data Retention Guard):
        ret_ok, ret_desc = ensure_data_retention_enabled(sess, cookies)
        account["data_retention_enabled"] = True if ret_ok else False
        account["data_retention_status"] = ret_desc

        # 3. جلب سجل الشحن والهدايا لآخر 60 يوم للحسابات النشطة
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        url = f"{ENDPOINT_RECHARGE}?start_date={start_date}&end_date={end_date}"

        try:
            r = sess.get(url, allow_redirects=False, timeout=25)
            if r.status_code == 200:
                body = r.json()
                if body.get("status") == 0:
                    records = body.get("list", [])
                    daily_gifts = [rec for rec in records if rec.get("credit_type") == "daily_gift"]
                    if not daily_gifts:
                        account["last_gift_date"] = "لا توجد هدايا مسجلة مؤخراً (+60 يوم)"
                        account["days_without_gift"] = 999
                        return "STALE", 999, "لا توجد هدايا مسجلة مؤخراً (+60 يوم)", real_balance, None

                    # ترتيب الهدايا تنازلياً حسب التاريخ
                    daily_gifts.sort(key=lambda x: x.get("ctime", ""), reverse=True)
                    last_gift = daily_gifts[0]
                    last_dt = parse_iso_dt(last_gift.get("ctime"))
                    if not last_dt:
                        account["last_gift_date"] = "تاريخ غير معروف"
                        account["days_without_gift"] = 999
                        return "STALE", 999, "تاريخ غير معروف", real_balance, last_gift

                    delta = self.now_utc - last_dt
                    days_elapsed = max(0, delta.days)
                    cairo_time_str = format_cairo_time(last_dt)
                    account["last_gift_date"] = cairo_time_str
                    account["days_without_gift"] = days_elapsed

                    if days_elapsed >= self.threshold_days:
                        return "STALE", days_elapsed, cairo_time_str, real_balance, last_gift
                    else:
                        return "HEALTHY", days_elapsed, cairo_time_str, real_balance, last_gift

        except Exception as e:
            pass

        return "AUTH_FAILED", None, "خطأ شبكة أثناء قراءة سجل الهدايا", real_balance, None

    def run_quarantine(self, scan_mode: str = "all", limit: int = 10, dry_run: bool = False) -> Dict[str, Any]:
        """
        تشغيل عملية الفرز الثلاثي والقص والنقل (Cut & Move):
        - السليم والنشط    -> accounts_success.json + يبقى في accounts_genspark.json
        - متأخر الهدية     -> accounts_delayed_gifts_credits.json
        - الميت أو المحظور  -> accounts_failed.json + dead_accounts.json
        """
        print(f"\n{C}{B}{'═'*95}{RST}")
        print(f"{C}{B}🚀 Genspark Master Tri-State Manager & Cleaner (3-File Architecture v2.0){RST}")
        print(f"{C}{B}{'═'*95}{RST}")
        print(f" 📁 1. الملف الأساسي المنظف : {W}{self.primary_path.name}{RST}")
        print(f" 🎯 2. ملف الحسابات الناجحة : {G}{self.success_path.name}{RST} (نشط + رصيد + هدية حديثة)")
        print(f" 📦 3. معزل متأخري الهدية   : {Y}{self.quarantine_path.name}{RST} (> {self.threshold_days} يوم بدون هدية)")
        print(f" 🗑️ 4. سلة الحسابات الفاشلة : {R}{self.failed_path.name}{RST} (باسورد غلط / حظر / تعليق)")
        print(f" ⏱️ مهلة الهدية المعتمدة    : {M}أكثر من {self.threshold_days} يوماً بدون هدية يومية{RST}")
        print(f" 🎯 نمط السحب               : {C}{scan_mode}{RST}" + (f" (حد أقصى: {limit})" if scan_mode != "all" else ""))
        print(f" 📊 الترتيب بالرصيد         : {G if self.sort_by_balance else W}{self.sort_by_balance}{RST}")
        if dry_run:
            print(f" ⚠️ {Y}{B}[وضع المعاينة التجريبي DRY-RUN]: لن يتم حفظ أو تعديل أي ملف فعلياً{RST}")

        primary_accounts = load_accounts(self.primary_path)
        success_accounts = load_accounts(self.success_path)
        quarantined_accounts = load_accounts(self.quarantine_path)
        failed_accounts = load_accounts(self.failed_path)
        dead_accounts = load_accounts(self.dead_path)

        print(f"\n 📊 إحصائيات الملفات الحالية قبل البدء:")
        print(f"  • الحسابات بالملف الأساسي : {W}{len(primary_accounts)}{RST} حساب")
        print(f"  • الحسابات بملف الناجح    : {G}{len(success_accounts)}{RST} حساب")
        print(f"  • الحسابات بمعزل الهدية   : {Y}{len(quarantined_accounts)}{RST} حساب")
        print(f"  • الحسابات بملف الفاشل    : {R}{len(failed_accounts)}{RST} حساب\n")

        if not primary_accounts:
            print(f"{R}❌ لا توجد حسابات في الملف الأساسي!{RST}")
            return {"error": "No accounts found"}

        # استبعاد الحسابات المفحوصة والمحفوظة مسبقاً لتفادي تكرار الفحص
        already_done = (
            {a.get("email", "").lower() for a in success_accounts}
            | {a.get("email", "").lower() for a in quarantined_accounts}
            | {a.get("email", "").lower() for a in failed_accounts}
            | {a.get("email", "").lower() for a in dead_accounts}
        )

        unprocessed = [a for a in primary_accounts if a.get("email", "").lower() not in already_done]
        print(f"  • الحسابات المتبقية المطلوب فحصها : {C}{B}{len(unprocessed)}{RST} حساب (تم تخطي {len(already_done)} مفحوص مسبقاً)\n")

        # اختيار الحسابات المطلوب فحصها حسب النمط
        if scan_mode == "first_n":
            targets_to_check = unprocessed[:limit]
        elif scan_mode == "random":
            targets_to_check = random.sample(unprocessed, min(limit, len(unprocessed)))
        else:
            targets_to_check = unprocessed

        healthy_tested: List[Dict[str, Any]] = []
        stale_to_cut: List[Dict[str, Any]] = []
        dead_to_cut: List[Dict[str, Any]] = []
        auth_failed_count = 0
        total_live_credits = 0

        print(f"{W}{B}{'الحساب':<33} | {'التصنيف':<15} | {'الرصيد':<7} | {'التفاصيل / التشخيص'}{RST}")
        print(f"{'-'*33}-+-{'-'*15}-+-{'-'*7}-+-{'-'*35}")
        sys.stdout.flush()

        def save_checkpoint(is_final: bool = False):
            """حفظ ذري دوري للملفات لحماية التقدم كل 10 حسابات"""
            all_cut_emails = {a.get("email", "").lower() for a in (stale_to_cut + dead_to_cut)}
            if not dry_run and (all_cut_emails or healthy_tested):
                # 1. تحديث الأساسي
                p_map = {a.get("email", "").lower(): a for a in load_accounts(self.primary_path)}
                for cut_e in all_cut_emails:
                    p_map.pop(cut_e, None)
                for h in healthy_tested:
                    p_map[h.get("email", "").lower()] = h
                final_p = list(p_map.values())
                if self.sort_by_balance:
                    final_p.sort(key=lambda x: (x.get("balance") or -1), reverse=True)

                # 2. تحديث الناجح
                s_map = {a.get("email", "").lower(): a for a in load_accounts(self.success_path)}
                for cut_e in all_cut_emails:
                    s_map.pop(cut_e, None)
                for h in healthy_tested:
                    s_map[h.get("email", "").lower()] = h
                final_s = list(s_map.values())
                if self.sort_by_balance:
                    final_s.sort(key=lambda x: (x.get("balance") or -1), reverse=True)

                # 3. تحديث المعزل
                q_map = {a.get("email", "").lower(): a for a in load_accounts(self.quarantine_path)}
                for s in stale_to_cut:
                    q_map[s.get("email", "").lower()] = s
                final_q = list(q_map.values())

                # 4. تحديث الفاشل والميت
                f_map = {a.get("email", "").lower(): a for a in load_accounts(self.failed_path)}
                d_map = {a.get("email", "").lower(): a for a in load_accounts(self.dead_path)}
                for d in dead_to_cut:
                    f_map[d.get("email", "").lower()] = d
                    d_map[d.get("email", "").lower()] = d
                final_f = list(f_map.values())
                final_d = list(d_map.values())

                if Config.AUTO_BACKUP and is_final:
                    create_backup(self.primary_path)

                atomic_save_json(self.primary_path, final_p)
                atomic_save_json(self.success_path, final_s)
                atomic_save_json(self.quarantine_path, final_q)
                atomic_save_json(self.failed_path, final_f)
                atomic_save_json(self.dead_path, final_d)

        current_batch: List[Tuple[str, str, int, str]] = []
        batch_num = 1

        for idx, acc in enumerate(targets_to_check, start=1):
            if not IS_RUNNING:
                print(f"\n{Y}⚠️ تم استلام إشارة إيقاف.. جاري الحفظ الذري والخروج الآمن...{RST}")
                save_checkpoint()
                break

            email = acc.get("email", "")
            status, days, diag_msg, bal, last_gift_raw = self.check_account_status(acc)
            bal_str = f"{bal:,}" if bal is not None else "-"
            current_batch.append((email, status, bal or 0, diag_msg or ""))

            if status == "HEALTHY":
                total_live_credits += (bal or 0)
                healthy_tested.append(acc)
                ret_tag = "🔓" if acc.get("data_retention_enabled") else "⚠️"
                tag = f"{G}نشط سليم ✅ {ret_tag}{RST}"
                print(f"{W}{email:<33}{RST} | {tag:<27} | {G}{bal_str:>7}{RST} | آخر هدية: {diag_msg} ({days} يوم)")

            elif status == "STALE":
                tag = f"{Y}متأخر هدية ✂️{RST}"
                print(f"{W}{email:<33}{RST} | {tag:<25} | {Y}{bal_str:>7}{RST} | منقطع منذ {days} يوم ({diag_msg})")
                quarantine_entry = dict(acc)
                quarantine_entry["quarantine_info"] = {
                    "reason": "stale_daily_gift",
                    "days_without_gift": days,
                    "last_gift_time_cairo": diag_msg,
                    "quarantined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "threshold_applied": self.threshold_days,
                }
                stale_to_cut.append(quarantine_entry)

            elif status == "DEAD":
                tag = f"{R}ميت/محظور 🗑️{RST}"
                print(f"{W}{email:<33}{RST} | {tag:<25} | {R}{bal_str:>7}{RST} | {R}{diag_msg}{RST}")
                dead_entry = dict(acc)
                dead_entry["status"] = (last_gift_raw or {}).get("reason", "dead")
                dead_entry["failure_reason"] = diag_msg
                dead_entry["dead_reason"] = diag_msg
                dead_entry["removed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                dead_to_cut.append(dead_entry)

            else:
                auth_failed_count += 1
                tag = f"{M}خطأ اتصال ⚠️{RST}"
                print(f"{W}{email:<33}{RST} | {tag:<25} | {bal_str:>7} | {diag_msg}")

            sys.stdout.flush()

            # ── حفظ دوري كل 10 حسابات وعرض ملخص الدفعة ──
            if idx % 10 == 0 or idx == len(targets_to_check):
                save_checkpoint(is_final=(idx == len(targets_to_check)))
                b_healthy = len([x for x in current_batch if x[1] == "HEALTHY"])
                b_stale = len([x for x in current_batch if x[1] == "STALE"])
                b_dead = len([x for x in current_batch if x[1] == "DEAD"])
                b_creds = sum(x[2] for x in current_batch if x[1] == "HEALTHY")
                with_bal_list = [f"{x[0]} ({x[2]:,} نقطة)" for x in current_batch if x[2] > 0]

                print(f"\n{C}{B}{'═'*95}{RST}")
                print(f"📦 {G}{B}تقرير إنجاز الدفعة #{batch_num}{RST} | فُحص: {W}{idx}/{len(targets_to_check)}{RST} حساب")
                print(f"  • سليم وناجح ✅   : {G}{b_healthy}{RST}")
                print(f"  • متأخر الهدية ✂️  : {Y}{b_stale}{RST}")
                print(f"  • ميت ومحظور 🗑️   : {R}{b_dead}{RST}")
                print(f"  • رصيد الدفعة 💰  : {G}{B}{b_creds:,} نقطة{RST}")
                if with_bal_list:
                    print(f"  🔥 حسابات برصيد   : {', '.join(with_bal_list)}")
                print(f"  💾 تم الحفظ الذري الدوري بنجاح لكافة الملفات الثلاثة.")
                print(f"{C}{B}{'═'*95}{RST}\n")
                sys.stdout.flush()
                batch_num += 1
                current_batch = []

            # تأخير أمان عشوائي بين الحسابات
            if idx < len(targets_to_check) and IS_RUNNING:
                delay_sec = random.uniform(self.min_delay, self.max_delay)
                time.sleep(delay_sec)

        # ── التقرير الإحصائي الأنيق الختامي ──
        save_checkpoint(is_final=True)
        print(f"\n{C}{B}{'═'*95}{RST}")
        print(f"📌 {B}ملخص نتائج الفحص والفرز الختامي:{RST}")
        print(f"  • الحسابات المفحوصة في هذه الدورة       : {len(targets_to_check)}")
        print(f"  • الحسابات الناجحة (نشطة + هدية حديثة)  : {G}{B}{len(healthy_tested)}{RST} حساب (-> {self.success_path.name})")
        print(f"  • الحسابات متأخرة الهدية (لقصها للمعزل) : {Y}{B}{len(stale_to_cut)}{RST} حساب (-> {self.quarantine_path.name})")
        print(f"  • الحسابات الفاشلة والميتة (لقصها للميت): {R}{B}{len(dead_to_cut)}{RST} حساب (-> {self.failed_path.name})")
        print(f"  • الحسابات المعلقة بشبكة/مؤقتة          : {M}{auth_failed_count}{RST} حساب")
        print(f"  • إجمالي الرصيد الحي للحسابات السليمة   : {G}{B}{total_live_credits:,} نقطة{RST}")
        print(f"{C}{B}{'═'*95}{RST}\n")
        sys.stdout.flush()

        return {
            "scanned": len(targets_to_check),
            "healthy": len(healthy_tested),
            "stale_cut": len(stale_to_cut),
            "dead_cut": len(dead_to_cut),
            "auth_failed": auth_failed_count,
            "total_credits": total_live_credits,
        }

    # ── [MAINT-4-B] ثوابت المعزل المشتركة مع 01.33 (D28/D32/D33) ──
    COOLDOWN_VAULT_LOCK_FILENAME = "accounts_cooldown.json.lock"   # R-B: الاسم نفسه في 01.33
    COOLDOWN_VAULT_LOCK_TIMEOUT_S = 30.0
    COOLDOWN_VAULT_LOCK_ORPHAN_S = 60.0
    ACCOUNT_LOG_FILENAME = "account_log.jsonl"                     # JSON Lines — سطر لكل حركة
    ACCOUNT_LOG_RETENTION_DAYS = 30                                # D32: التقليم هنا فقط (عند بدء run_revival)
    ACCOUNT_LOG_MAX_ENTRIES = 5000

    def _with_vault_lock(self, lock_path: Path, fn):
        """[MAINT-4-B/D33 R-B] قفل عبر العمليات بملف O_CREAT|O_EXCL يشاركه 01.33؛ مهلة ثم تجاوز اليتيم بتحذير."""
        deadline = time.time() + self.COOLDOWN_VAULT_LOCK_TIMEOUT_S
        while True:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                try:
                    age = time.time() - lock_path.stat().st_mtime
                except OSError:
                    age = 0.0
                if age > self.COOLDOWN_VAULT_LOCK_ORPHAN_S:
                    print(f"  {Y}⚠️ قفل يتيم (orphan lock) عمره {age:.0f}s — يُتجاوز: {lock_path.name}{RST}")
                    try:
                        lock_path.unlink()
                    except OSError:
                        pass
                    continue
                if time.time() >= deadline:
                    print(f"  {R}❌ تعذر الحصول على القفل المشترك خلال {self.COOLDOWN_VAULT_LOCK_TIMEOUT_S:g}s: {lock_path.name}{RST}")
                    return False, None
                time.sleep(0.1)
        try:
            try:
                os.write(fd, f"{os.getpid()} 05.02 {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}".encode("utf-8"))
            finally:
                os.close(fd)
            return True, fn()
        finally:
            try:
                lock_path.unlink()
            except OSError:
                pass

    def _log_move(self, acc: Dict[str, Any], event: str, reason: str, src: Path, dst: Path) -> None:
        """[MAINT-4-B/D28] سطر JSON واحد في account_log.jsonl ببيانات الحساب الكاملة (إيميل/باسورد/كوكيز/وقت/سبب/مسار)
        بقرار المالك المحلي وبلا حجب — نفس صيغة 01.33 (by=05.02). best-effort."""
        try:
            entry = {"ts": time.time(), "at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "event": event,
                     "email": acc.get("email", ""), "password": acc.get("password", ""), "cookies": acc.get("cookies", {}),
                     "reason": reason, "from_path": str(src), "to_path": str(dst), "by": "05.02"}
            with open(src.parent / self.ACCOUNT_LOG_FILENAME, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except Exception as e:
            print(f"  {Y}⚠️ تعذر كتابة account_log.jsonl: {type(e).__name__}{RST}")

    def _trim_account_log(self, folder: Path) -> None:
        """[MAINT-4-B/D32] تقليم السجل مرة عند بدء run_revival فقط: إبقاء آخر 30 يوماً وبحد 5000 سطر؛ الأسطر التالفة تُهمل."""
        log_path = folder / self.ACCOUNT_LOG_FILENAME
        if not log_path.exists():
            return
        try:
            cutoff = time.time() - self.ACCOUNT_LOG_RETENTION_DAYS * 86400
            kept: List[str] = []
            for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                try:
                    if float(json.loads(line).get("ts") or 0) >= cutoff:
                        kept.append(line)
                except Exception:
                    continue
            kept = kept[-self.ACCOUNT_LOG_MAX_ENTRIES:]
            tmp = log_path.with_name(log_path.name + ".tmp")
            tmp.write_text("".join(l + "\n" for l in kept), encoding="utf-8")
            tmp.replace(log_path)
        except Exception as e:
            print(f"  {Y}⚠️ تعذر تقليم account_log.jsonl: {type(e).__name__}{RST}")

    def _merge_by_email(self, path: Path, accounts: List[Dict[str, Any]], sort: bool = False) -> None:
        """[MAINT-3-B/D24] دمج ذري بمفتاح البريد (lower) في ملف وجهة مع .bak قبل الكتابة — بديل DRY لخرائط p_map/s_map"""
        merged = {a.get("email", "").lower(): a for a in load_accounts(path)}
        merged.update({a.get("email", "").lower(): a for a in accounts})
        final = sorted(merged.values(), key=lambda x: (x.get("balance") or -1), reverse=True) if sort else list(merged.values())
        create_backup(path)
        atomic_save_json(path, final)

    def run_revival(self, limit: int = 50, dry_run: bool = False) -> Dict[str, Any]:
        """
        فحص الحسابات المعزولة في accounts_delayed_gifts_credits.json،
        واسترجاع الحسابات التي عاد لها الرصيد إلى الملف الأساسي وملف الناجح.
        """
        print(f"\n{C}{B}{'═'*95}{RST}")
        print(f"{C}{B}🔄 عملية إنعاش واسترجاع الحسابات المعزولة (Quarantine Revival & Restore){RST}")
        print(f"{C}{B}{'═'*95}{RST}")
        print(f" 📦 ملف المعزل المفحوص : {Y}{self.quarantine_path.name}{RST}")
        print(f" 📁 ملف الوجهة الأساسي  : {G}{self.primary_path.name}{RST}")
        print(f" 🎯 ملف الوجهة الناجح   : {G}{self.success_path.name}{RST}")

        self._trim_account_log(self.quarantine_path.parent)      # [MAINT-4-B/D32] التقليم هنا فقط
        if limit is None or limit <= 0:                            # [MAINT-4-B/D38] -l 0 = الكل
            limit = None
        quarantined_accounts = load_accounts(self.quarantine_path)
        # [MAINT-3-B/S1] وجهتا الكتابة فقط (⛔ لا تُفحصان): الفاشل + معزل الهدية (C2: resolve لأن -q قد يكون معزل التبريد)
        delayed_path = resolve_file_path(Config.QUARANTINE_FILE)
        dead_moves: List[Dict[str, Any]] = []
        stale_moves: List[Dict[str, Any]] = []

        if not quarantined_accounts:
            print(f"{Y}ℹ️ ملف المعزل فارغ، لا توجد حسابات معزولة حالياً.{RST}")
            return {"revived": 0}

        revived_accounts = []
        still_stale_count = 0

        for acc in quarantined_accounts[:limit]:
            if not IS_RUNNING:
                break
            email = acc.get("email", "")
            status, days, gift_time, bal, _ = self.check_account_status(acc)

            # إذا استلم الحساب هدية حديثة (خلال آخر 3 أيام) يعود فورياً للناجح والأساسي
            if status == "HEALTHY" and days is not None and days <= 3:
                print(f"  🎉 {G}مبروك! الحساب {W}{email}{G} عاد له الرصيد ({bal:,} نقطة | هدية منذ {days} يوم) -> استرجاع!{RST}")
                clean_acc = dict(acc)
                clean_acc.pop("quarantine_info", None)
                clean_acc["status"] = "active"
                revived_accounts.append(clean_acc)
            elif status == "DEAD":  # [MAINT-3-B/S2] الميت → الفاشل
                dead_moves.append(acc)
                print(f"  💀 {R}الحساب {email} ميت ({gift_time}) -> نقل إلى {self.failed_path.name}{RST}")
            elif status == "STALE":  # [MAINT-3-B/S2] المتأخر → معزل الهدية (عودته يدوية — D23)
                stale_moves.append(acc)
                print(f"  📦 {Y}الحساب {email} متأخر الهدية ({days or '?'} يوم) -> نقل إلى {delayed_path.name}{RST}")
            else:
                still_stale_count += 1
                print(f"  ⏳ {Y}الحساب {email} ما زال منقطعاً ({days or '?'} يوم | رصيد: {bal or 0}){RST}")

            time.sleep(random.uniform(self.min_delay, self.max_delay))

        if (revived_accounts or dead_moves or stale_moves) and not dry_run:  # [MAINT-3-B/S3]
            moved_emails = {a.get("email", "").lower() for a in revived_accounts + dead_moves + stale_moves}  # [S4]

            def _commit_moves():
                # [MAINT-4-B/R-A] إعادة تحميل المعزل من القرص تحت القفل — ما أضافه 01.33 أثناء الفحص لا يُفقد
                fresh_vault = load_accounts(self.quarantine_path)
                new_quarantine = [a for a in fresh_vault if a.get("email", "").lower() not in moved_emails]
                # [MAINT-3-B/S5+S6] دمج كل وجهة عبر _merge_by_email (D24) — الوجهة الفارغة لا تُكتب (صفر زيادة على الفاضي)
                if revived_accounts:
                    self._merge_by_email(self.primary_path, revived_accounts, sort=self.sort_by_balance)
                    self._merge_by_email(self.success_path, revived_accounts, sort=self.sort_by_balance)
                if dead_moves:
                    self._merge_by_email(self.failed_path, dead_moves)
                if stale_moves:
                    self._merge_by_email(delayed_path, stale_moves)
                create_backup(self.quarantine_path)
                atomic_save_json(self.quarantine_path, new_quarantine)
                # [MAINT-4-B/D28] سطر لكل حركة ببيانات الحساب الكاملة
                for a in revived_accounts:
                    self._log_move(a, "return_to_primary", "HEALTHY", self.quarantine_path, self.primary_path)
                for a in dead_moves:
                    self._log_move(a, "move_to_failed", "DEAD", self.quarantine_path, self.failed_path)
                for a in stale_moves:
                    self._log_move(a, "move_to_delayed_gifts", "STALE", self.quarantine_path, delayed_path)
                return True

            # [MAINT-4-B/R-B] القفل المشترك مع 01.33 (accounts_cooldown.json.lock بجوار المعزل)
            acquired, _ = self._with_vault_lock(self.quarantine_path.parent / self.COOLDOWN_VAULT_LOCK_FILENAME, _commit_moves)
            if not acquired:
                print(f"{R}❌ لم يُحفظ شيء: القفل المشترك مشغول — أعد التشغيل لاحقاً (لا فقدان بيانات).{RST}")
                return {"error": "vault_lock_busy", "revived": 0}
            print(f"\n{G}{B}✅ استرجاع {len(revived_accounts)} | 💀 إلى الفاشل {len(dead_moves)} | 📦 إلى معزل الهدية {len(stale_moves)}{RST}")

        return {"revived": len(revived_accounts), "still_stale": still_stale_count,
                "moved_to_failed": len(dead_moves), "moved_to_delayed": len(stale_moves)}  # [S7]


# ════════════════════════════════════════════════════════════════════════════════
# 🖥️ واجهة سطر الأوامر (CLI Interface)
# ════════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="Genspark Master Tri-State Account Manager & Cleaner (v2.0) — الفرز الثلاثي والقص والنقل الذري",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-d", "--days", type=int, default=Config.STALE_GIFT_DAYS_THRESHOLD, help=f"مهلة الأيام بدون هدية (الافتراضي: {Config.STALE_GIFT_DAYS_THRESHOLD})")
    parser.add_argument("-m", "--mode", type=str, default=Config.SCAN_MODE, choices=["all", "first_n", "random"], help=f"نمط الفحص (الافتراضي: {Config.SCAN_MODE})")
    parser.add_argument("-l", "--limit", type=int, default=Config.SCAN_LIMIT, help=f"عدد الحسابات للأنماط المحدودة (الافتراضي: {Config.SCAN_LIMIT})")
    parser.add_argument("-f", "--file", type=str, default=Config.PRIMARY_FILE, help=f"ملف الحسابات الأساسي (الافتراضي: {Config.PRIMARY_FILE})")
    parser.add_argument("--success-file", type=str, default=Config.SUCCESS_FILE, help=f"ملف الحسابات الناجحة (الافتراضي: {Config.SUCCESS_FILE})")
    parser.add_argument("-q", "--quarantine-file", type=str, default=Config.QUARANTINE_FILE, help=f"ملف المعزل (الافتراضي: {Config.QUARANTINE_FILE})")
    parser.add_argument("--failed-file", type=str, default=Config.FAILED_FILE, help=f"ملف الحسابات الفاشلة (الافتراضي: {Config.FAILED_FILE})")
    parser.add_argument("--no-sort", action="store_true", help="تعطيل الترتيب التنازلي حسب الرصيد")
    parser.add_argument("--dry-run", action="store_true", help="معاينة تجريبية دون تعديل الملفات")
    parser.add_argument("--revive", action="store_true", help="فحص المعزل واسترجاع الحسابات التي عاد لها الرصيد")
    args = parser.parse_args()

    primary_path = resolve_file_path(args.file)
    folder = primary_path.parent

    success_path = folder / args.success_file
    quarantine_path = folder / args.quarantine_file
    failed_path = folder / args.failed_file
    dead_path = folder / Config.DEAD_FILE

    manager = MasterDelayedGiftsManager(
        primary_path=primary_path,
        success_path=success_path,
        quarantine_path=quarantine_path,
        failed_path=failed_path,
        dead_path=dead_path,
        threshold_days=args.days,
        sort_by_balance=not args.no_sort and Config.SORT_BY_BALANCE,
        auto_relogin=Config.AUTO_RELOGIN,
        min_delay=Config.MIN_DELAY,
        max_delay=Config.MAX_DELAY,
    )

    # [MAINT-4-B/D39 — إذن صريح بتوسيع A5 لـmain()] كود خروج ≠ 0 عند الفشل ليميّزه المجدول/main.py الخارجي
    try:
        if args.revive:
            result = manager.run_revival(limit=args.limit, dry_run=args.dry_run or Config.DRY_RUN)
        else:
            result = manager.run_quarantine(
                scan_mode=args.mode,
                limit=args.limit,
                dry_run=args.dry_run or Config.DRY_RUN,
            )
    except Exception as e:
        print(f"{R}❌ فشل التشغيل: {type(e).__name__}: {e}{RST}")
        sys.exit(1)
    if isinstance(result, dict) and result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
