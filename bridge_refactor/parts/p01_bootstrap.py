"""[VERBATIM SLICE] p01_bootstrap
المصدر: 01.31_telegram_gen_bridge.py — الأسطر 1..154
المحتوى: Header + imports + logging + redact + html_escape + resolve_shared_path (P23) + load_bot_token
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          🌐 ⚡ 01.31_telegram_gen_bridge.py                 ║
║  إصدار REST-Only + Data Retention (P12..P19 + P20):       ║
║  • P20: 🔧 إلغاء Git Native Sync — الرفع عبر REST API فقط  ║
║  • P20: 🧬 خطأ AI Data Retention = بروتوكول نفاد الرصيد     ║
║    (تبريد + حساب تالٍ + نفس آخر رسالة + تنبيه مميز)         ║
║  • P19: 📋 نسخ إعدادات مشروع آخر (GitHub+موديل+برومبت)  ║
║    + الترقيم التسلسلي التلقائي للأسماء المكررة (الحج 2)    ║
║  • وقف فوري P18: أي تغيّر في Deep Thinking / Tasks Remaining ║
║  • تصليب P17: تجديد فوري للجلسة المنتهية + دعم الجروبات    ║
║  • نشر عام مبكر P16: المشروع Public فور التقاط الـ pid       ║
║  • استئناف نفس المشروع بعد انقطاع البث (carry_pid — لا شات جديد)║
║  • مهلة خمول ذكية: لا TIMEOUT على التوليدات الطويلة النشطة    ║
║  • بوابة الرصيد المسبقة: رصيد < 100 = تبريد 29h + تخطٍ صامت   ║
║  • طباعة الرد كاملاً دفعة واحدة + زمن التوليد بالثواني ⏱️     ║
║  • بطاقة المعاينة الفورية (Instant Live Preview) من أول ثانية ║
║  • مبدأ الرسالة الواحدة المتطورة (Single Evolving Message)    ║
║  • حارس التيليجرام 00-telegram-ux-guardian وأزرار URL نظيفة   ║
║  • تصفح فروع GitHub بنقرة واحدة (1-Click UI) ودعم Pagination ║
║  • توجيه عقود الموديلات الـ 5 وتوجيه Sol و Kimi تلقائياً     ║
║  • عزل متعدد المشاريع + نقاط استئناف + مزامنة GitHub اختيارية ║
╚══════════════════════════════════════════════════════════════╝
"""

import hashlib
import json
import logging
import os
import random
import re
import sys
import time
import pathlib
import threading
import shutil
import subprocess
import uuid
import base64
import urllib.parse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

# ضبط ترميز التيرمينال العربي
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# إعداد الألوان بـ Colorama مع Fallback آمن
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    class _NC:
        def __getattr__(self, _):
            return ""
    Fore = Style = _NC()

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
BUILD_VERSION = "01.31"
BUILD_PARENT_BASELINE = "01.30"
BUILD_PARENT_BASELINE_SHA256 = "0130_p19_copy_settings_baseline"

LOG_FILE = SCRIPT_DIR / "bridge_bot.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("bridge")


def redact_email(email: str) -> str:
    """إخفاء الإيميل في اللوجات لزيادة الأمان والحفاظ على الخصوصية"""
    if not email or "@" not in email:
        return email or ""
    parts = email.split("@")
    user, domain = parts[0], parts[1]
    masked = user[0] + "***" if len(user) <= 3 else user[:3] + "***"
    return f"{masked}@{domain}"


def log_event(level: str, msg: str, email: str = "", extra: dict = None):
    """تسجيل حدث ملون في التيرمينال + حفظ دائم بملف اللوج مع إخفاء الإيميل للحماية"""
    colors = {
        "info": Fore.CYAN,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED
    }
    color = colors.get(level, "")
    safe_email = redact_email(email) if email else ""
    prefix = f"[{safe_email}] " if safe_email else ""
    print(color + f"{prefix}{msg}")
    log_func = getattr(logger, level if hasattr(logger, level) else "info", logger.info)
    log_msg = f"{prefix}{msg}"
    if extra:
        log_msg += f" | {json.dumps(extra, ensure_ascii=False)}"
    log_func(log_msg)


def html_escape(text: str) -> str:
    """تهريب HTML كامل (& أولاً) لأي نص قادم من المستخدم قبل وضعه في رسائل HTML"""
    return str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ══════════════════════════════════════════════════════════════
# 🔎 [P23] البحث الهرمي للملفات المشتركة: محلي أولاً ثم الفولدر الأب (W___webapp/)
# ══════════════════════════════════════════════════════════════
def resolve_shared_path(name: str) -> pathlib.Path:
    """مسار مشترك ذكي: لو الملف/المجلد موجود جنب النسخة يستخدمه (أولوية محلية)،
    وإلا يلقطه من الفولدر الأب المركزي — ولو غير موجود في الاثنين يرجع المحلي (للإنشاء).
    Zero Breaking Changes: النسخ القديمة بملفاتها المحلية تشتغل كما هي تماماً."""
    local = SCRIPT_DIR / name
    if local.exists():
        return local
    parent = SCRIPT_DIR.parent / name
    if parent.exists():
        return parent
    return local


# ══════════════════════════════════════════════════════════════
# 🔑 توكن البوت: من متغير البيئة أو ملف محلي (gitignored) — ممنوع الـ Hardcode
# ══════════════════════════════════════════════════════════════
def load_bot_token() -> str:
    """قراءة توكن البوت بأمان: TELEGRAM_BOT_TOKEN ← telegram_bot_token.txt (محلي ثم الأب، خارج git)"""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if token:
        return token
    token_file = resolve_shared_path("telegram_bot_token.txt")  # 🔎 [P23] محلي ثم الأب
    try:
        if token_file.exists():
            token = token_file.read_text(encoding="utf-8").strip()
            if token:
                log_event("warning", "تم تحميل توكن البوت من الملف المحلي telegram_bot_token.txt (يُفضَّل متغير البيئة TELEGRAM_BOT_TOKEN)")
                return token
    except Exception as e:
        log_event("error", f"تعذر قراءة ملف التوكن المحلي: {e}")
    return ""


TELEGRAM_BOT_TOKEN = load_bot_token()

