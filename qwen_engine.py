#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
🤖 qwen_engine.py — محرك Qwen.ai Direct المستقل (P15)
=============================================================
موديول مستقل ومتكامل يضم منظومة كوين بالكامل (منقولة حرفياً
من 04_upload_to_Fable_github.py بدون إسقاط أي تفصيلة):

  ⚙️  الإعدادات وسلسلة الموديلات:
      AI_MODEL_CHAIN (الموديل + المهلة 30s + Thinking/Fast Mode)
      AI_MAX_DIFF_CHARS / AI_MIN_VALID_CHARS / AI_RACE_ACCOUNTS
      QWEN_ACCOUNTS_FILE + DEFAULT_QWEN_ACCOUNTS + التعافي الذاتي

  🏁 محرك السباق المتوازي:
      _qwen_worker  (هيدرات Dalvik/Android 15 + بث SSE + إلغاء فوري stop_event)
      qwenguest_worker (ثريد الزائر Bypass بالتوازي في نفس اللحظة)
      race_accounts (إدارة السباق + شريط التقدم اللحظي الملون بالثواني)
      _call_qwen_ai_direct (التنقل عبر سلسلة الموديلات + Guest fallback)

  🔄 التجديد التلقائي وحفظ الفائز:
      auto_refresh_qwen_account (تجديد الجلسة عبر password_hash)
      _save_qwen_winner_cookies (حفظ الفائز فقط تحت القفل _QWEN_FILE_LOCK)

  🤖 استخراج ومعالجة الرد:
      generate_ai_summary (رسالة الكوميت + الملخص من رد الموديل)

الاستخدام:
    import qwen_engine
    qwen_engine.configure(log_func=my_logger)   # حقن اللوجر (اختياري)
    commit, summary, model = qwen_engine.generate_ai_summary(files, diff, alerts)
=============================================================
"""

import concurrent.futures
import json
import os
import random
import re
import sys
import threading
import time
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor
from datetime import datetime

# -------------------------------------------------------------
# 🎨 ألوان الطباعة (Console ANSI Palette)
# -------------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
PINK = "\033[95m"
BOLD_PINK = "\033[1;95m"
BOLD_GREEN = "\033[1;92m"
BOLD_CYAN = "\033[1;96m"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 🔐 اسم ملف أسرار كوين (يُستخدم أيضاً في NEVER_COPY_FILES بالسكريبت المضيف)
QWEN_ACCOUNTS_BASENAME = "accounts_qwen.json"

# -------------------------------------------------------------
# 📢 اللوجر القابل للحقن (السكريبت المضيف يحقن log_message بتاعه)
# -------------------------------------------------------------
_LOG_FUNC = None


def configure(log_func=None):
    """حقن دالة اللوج من السكريبت المضيف (مثلاً log_message بتاعة 04)."""
    global _LOG_FUNC
    if log_func is not None:
        _LOG_FUNC = log_func


def log_message(message, color=RESET):
    """لوجر افتراضي بطابع زمني — يُستبدل تلقائياً لو السكريبت المضيف حقن لوجره."""
    if _LOG_FUNC is not None:
        _LOG_FUNC(message, color)
        return
    ts = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    print(f"{color}[{ts}] {message}{RESET}", flush=True)


# -------------------------------------------------------------
# 🌈 مولد طيف الألوان الـ 100 بالثواني والنسبة المئوية
# -------------------------------------------------------------
SPECTRUM_256 = [
    51, 50, 49, 48, 47, 46, 45, 44, 43, 42,
    41, 40, 39, 38, 37, 36, 35, 34, 33, 32,
    75, 74, 73, 72, 71, 70, 69, 68, 67, 66,
    99, 98, 97, 96, 95, 94, 93, 92, 91, 90,
    129, 128, 127, 126, 125, 124, 123, 122, 121, 120,
    165, 164, 163, 162, 161, 160, 159, 158, 157, 156,
    201, 200, 199, 198, 197, 196, 195, 194, 193, 192,
    207, 206, 205, 204, 203, 202, 208, 209, 214, 215,
    220, 221, 222, 223, 226, 227, 228, 229, 118, 119,
    82, 83, 84, 85, 86, 87, 14, 15, 11, 9
]

def get_rainbow_color(percent):
    """توليد لون مختلف حصري لكل 1% في الكونسول (ANSI 256 Colors)."""
    if os.environ.get("NO_COLOR"):
        return ""
    idx = max(0, min(99, int(percent)))
    return f"\033[38;5;{SPECTRUM_256[idx]}m"

def get_second_rainbow_color(seconds):
    """
    ⏱️ توليد لون ديناميكي حصري لكل ثانية بنظام ANSI 256 Colors.
    يتغير اللون تلقائياً مع كل ثانية تمر، ويلف بسلاسة عبر الطيف الملون.
    """
    if os.environ.get("NO_COLOR"):
        return ""
    idx = int(seconds) % len(SPECTRUM_256)
    return f"\033[38;5;{SPECTRUM_256[idx]}m"


def render_seconds_progress_bar(elapsed_sec, total_sec=30, width=25, label="⏱️ Progress"):
    """
    🌈 رسم شريط تقدم ملون بالثواني التراكمية مع طيف الألوان المضيء لكل ثانية وكل مكعب!
    """
    percent = min(100.0, max(0.0, (elapsed_sec / total_sec) * 100 if total_sec > 0 else 100.0))
    filled_len = int(width * percent // 100)
    
    # بناء الشريط الملون: كل مكعب ياخد لون متدرج من طيف الثواني
    bar_chars = []
    for i in range(filled_len):
        color = get_second_rainbow_color(elapsed_sec + (i * 0.5))
        bar_chars.append(f"{color}█{RESET}")
    
    unfilled_str = "░" * (width - filled_len)
    unfilled = f"\033[90m{unfilled_str}{RESET}"
    bar_str = "".join(bar_chars) + unfilled
    
    sec_color = get_second_rainbow_color(elapsed_sec)
    time_txt = f"{sec_color}{elapsed_sec:.1f}s / {total_sec:.0f}s{RESET}"
    percent_txt = f"{sec_color}{percent:5.1f}%{RESET}"
    
    return f"{BOLD}{label}{RESET} [{bar_str}] {percent_txt} ({time_txt})"




# 🤖 إعدادات الذكاء الاصطناعي (Qwen.ai Direct)
AI_MAX_DIFF_CHARS = 15000       # أقصى حجم diff يتبعت لـ Qwen.ai
AI_ENABLED = True               # 🤖 مفعّل لاستخدام Qwen.ai Direct

# 🏁 سلسلة الموديلات بالأولوية (سباق متوازي بين كل الحسابات في كل مرحلة)
#    كل مرحلة لها مهلة مستقلة — أول حساب يرد بردّ صالح يفوز ويُلغى الباقي فوراً.
#    عايز تضيف موديل تالت؟ ضيف dict جديد هنا وبس — الكود كله ديناميكي.
AI_MODEL_CHAIN = [
    {
        "model": "qwen3.8-max",
        "label": "Qwen3.8-Max",
        "timeout": 30,                 # ⏱️ مهلة المرحلة بالثواني
        "thinking_enabled": True,
        "thinking_mode": "Thinking",
    },
    {
        "model": "qwen3.8-max",
        "label": "qwen3.8-max",
        "timeout": 30,                 # ⏱️ مهلة المرحلة بالثواني
        "thinking_enabled": False,
        "thinking_mode": "Fast",
    },
]

AI_MIN_VALID_CHARS = 20         # أقل عدد حروف نعتبره رد صالح (يمنع الردود الفاضية)
AI_RACE_ACCOUNTS = 0            # 0 = كل الحسابات النشطة تتسابق | 2 = حسابين بس
AI_FALLBACK_COMMIT_MSG = "كوميت"  # 📝 رسالة الكوميت لو كل الموديلات فشلت


# ══════════════════════════════════════════════════════════════
# 🔎 [P23/DEC-019] البحث الهرمي للملفات المشتركة: محلي أولاً ثم الفولدر الأب (W___webapp/)
# ══════════════════════════════════════════════════════════════
def resolve_shared_path(name: str) -> str:
    """مسار مشترك ذكي: لو الملف موجود جنب النسخة يستخدمه (أولوية محلية)،
    وإلا يلقطه من الفولدر الأب المركزي — ولو غير موجود في الاثنين يرجع المحلي (للإنشاء).
    Zero Breaking Changes: النسخ القديمة بملفاتها المحلية تشتغل كما هي تماماً."""
    local = os.path.join(SCRIPT_DIR, name)
    if os.path.exists(local):
        return local
    parent = os.path.join(os.path.dirname(SCRIPT_DIR), name)
    if os.path.exists(parent):
        return parent
    return local


# 🔐 إدارة حسابات Qwen.ai (التعافي الذاتي والتبديل العشوائي) — [DEC-019] عبر المسار المشترك
QWEN_ACCOUNTS_FILE = resolve_shared_path(QWEN_ACCOUNTS_BASENAME)
DEFAULT_QWEN_ACCOUNTS = [
    {
        "email": "ybvh1k@arg.edu.pl",
        "name": "1",
        "password_hash": "312c356b5ed59c92cd204d1dd27fb7bd68bdf0a51469f350eee37b2dbcd7fdbd",
        "status": "active",
        "cookies": {}
    },
    {
        "email": "ccess42@bjedu.tech",
        "name": "2",
        "password_hash": "c49e556f54a786c2de5f4181d54f6c9629b2391af3c8728937b1aef8b6d3bed4",
        "status": "active",
        "cookies": {}
    },
    {
        "email": "hatx@nm.edu.pl",
        "name": "3",
        "password_hash": "312c356b5ed59c92cd204d1dd27fb7bd68bdf0a51469f350eee37b2dbcd7fdbd",
        "status": "active",
        "cookies": {}
    },
    {
        "email": "011rl@rc.mailings.live",
        "name": "4",
        "password_hash": "31970f68dc4481fee87b103b87daef4d506960a8ff82956331aed18aa34cfe4e",
        "status": "active"
  }
]

def load_or_create_qwen_accounts():
    """
    تحميل الحسابات من accounts_qwen.json أو إنشائها تلقائياً لو كانت غير موجودة أو فارغة [].
    تضمن تعافي الملف وتعبئته بالـ 3 حسابات كاملة دائماً.
    """
    accounts = []
    if os.path.exists(QWEN_ACCOUNTS_FILE) and os.path.getsize(QWEN_ACCOUNTS_FILE) > 2:
        try:
            with open(QWEN_ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accounts = json.load(f)
        except Exception:
            accounts = []

    if not accounts:
        log_message("⚠️ ملف accounts_qwen.json غير موجود أو فارغ — جاري التعافي التلقائي وإنشاؤه...", YELLOW)
        accounts = DEFAULT_QWEN_ACCOUNTS
        try:
            with open(QWEN_ACCOUNTS_FILE, "w", encoding="utf-8") as f:
                json.dump(accounts, f, ensure_ascii=False, indent=2)
            log_message("✅ تم إنشاء ملف accounts_qwen.json وتعبئته بالـ 3 حسابات بنجاح.", GREEN)
        except Exception as e:
            log_message(f"⚠️ تعذر كتابة ملف accounts_qwen.json ({e}) — سيتم الاستمرار بالذاكرة.", RED)

    return accounts


# =============================================================
# 🤖 محرك Qwen.ai Direct — سباق متوازي بين الحسابات على سلسلة موديلات
# =============================================================

# 🔒 قفل عام يمنع تلف accounts_qwen.json عند الكتابة من عدة خيوط في نفس اللحظة
_QWEN_FILE_LOCK = threading.Lock()

# 🏷️ اسم الموديل/الحساب الفائز في آخر عملية (يظهر في تليجرام والتقرير والكونسول)
LAST_AI_SOURCE = ""
LAST_AI_MODEL = ""
LAST_AI_ACCOUNT = ""
LAST_AI_ELAPSED = 0.0


def _reset_ai_race_state():
    """تصفير بيانات آخر سباق قبل بدء عملية جديدة."""
    global LAST_AI_SOURCE, LAST_AI_MODEL, LAST_AI_ACCOUNT, LAST_AI_ELAPSED
    LAST_AI_SOURCE = ""
    LAST_AI_MODEL = ""
    LAST_AI_ACCOUNT = ""
    LAST_AI_ELAPSED = 0.0


def _save_qwen_accounts(accounts_list):
    """💾 كتابة ملف الحسابات تحت القفل — مستحيل يتلف حتى لو كل الخيوط جددت كوكيزها معاً."""
    try:
        with _QWEN_FILE_LOCK:
            tmp_path = f"{QWEN_ACCOUNTS_FILE}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as out_f:
                json.dump(accounts_list, out_f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, QWEN_ACCOUNTS_FILE)   # كتابة ذرية (Atomic)
        return True
    except Exception as io_err:
        log_message(f"⚠️ تعذر حفظ ملف الحسابات: {io_err}", RED)
        return False


def auto_refresh_qwen_account(sess, acc_index, accounts_list):
    """
    إعادة تسجيل الدخول بالـ password_hash للـ email في الحساب المحدد،
    وتحديث الكوكيز وتدوين الحسابات الـ 3 كاملة في accounts_qwen.json.
    """
    account = accounts_list[acc_index]
    email = account.get("email", "")
    pass_hash = account.get("password_hash", "")
    if not email or not pass_hash:
        return False

    log_message(f"🔄 جاري تجديد جلسة Qwen للحساب ({acc_index + 1}): {email}...", CYAN)
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://chat.qwen.ai",
        "Referer": "https://chat.qwen.ai/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        r_login = sess.post(
            "https://chat.qwen.ai/api/v2/auths/signin",
            headers={**headers, "X-Request-Id": str(uuid.uuid4())},
            json={"email": email, "password": pass_hash},
            timeout=15
        )
        if r_login.status_code == 200 and r_login.json().get("success"):
            new_cookies = sess.cookies.get_dict()
            cookie_string = "; ".join([f"{k}={v}" for k, v in new_cookies.items()])
            
            # تحديث الحساب المحدد فقط مع الحفاظ على الحسابات الأخرى كاملة
            account["cookies"] = new_cookies
            account["cookie_string"] = cookie_string
            account["token"] = new_cookies.get("token", "")
            account["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            accounts_list[acc_index] = account

            # 🔒 كتابة آمنة تحت القفل — يمنع تلف الملف عند تجديد كوكيز من عدة خيوط
            if _save_qwen_accounts(accounts_list):
                log_message(
                    f"✅ تم تجديد كوكيز الحساب {email} وحفظ الملف كاملاً بـ {len(accounts_list)} حسابات.",
                    GREEN
                )
            return True
        else:
            log_message(f"⚠️ فشل تسجيل الدخول للحساب {email}: {r_login.text[:200]}", RED)
            return False
    except Exception as e:
        log_message(f"🚨 خطأ أثناء تجديد جلسة Qwen: {e}", RED)
        return False

# =============================================================
# 🏁 محرك السباق المتوازي — كل الحسابات على موديل واحد في نفس اللحظة
# =============================================================
def _qwen_time_left(deadline):
    """الوقت المتبقي للمرحلة بالثواني (0 لو خلص)."""
    return max(0.0, deadline - time.monotonic())


def _qwen_worker(acc_index, accounts_list, model_cfg, prompt, deadline, stop_event):
    """
    🧵 عامل السباق: ثريد مستقل لحساب واحد على موديل واحد.
      - يرجّع dict فيه الرد + بيانات الحساب عند النجاح
      - يرجّع None عند الفشل / الإلغاء / الكابتشا / انتهاء المهلة
      - يفحص stop_event و deadline باستمرار عشان يقطع الاتصال فوراً
        لو حساب تاني فاز أو خلصت الـ 30 ثانية (صفر إهدار كوتا).
    """
    if stop_event.is_set() or _qwen_time_left(deadline) <= 0:
        return None

    try:
        from curl_cffi import requests
    except ImportError:
        return None

    account = accounts_list[acc_index]
    email = account.get("email", "Unknown")
    acc_name = account.get("name", str(acc_index + 1))
    model = model_cfg["model"]
    started = time.monotonic()

    sess = requests.Session(impersonate="chrome120")
    for k, v in (account.get("cookies") or {}).items():
        sess.cookies.set(k, v, domain="chat.qwen.ai")

    token = account.get("token", "")
    headers = {
        "X-Platform": "android",
        "source": "app",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 15; RMX3834 Build/AP3A.240905.015.A2),Dalvik/2.1.0 (Linux; U; Android 15; RMX3834 Build/AP3A.240905.015.A2) AliApp(QWENCHAT/2.7.2) AppType/Release AplusBridgeLite",
        "Authorization": f"Bearer {token}" if token else "",
        "x-device-id": f"ai{uuid.uuid4().hex[:32]}",
        "Accept": "application/json",
        "Accept-Language": "en-US",
        "Accept-Charset": "UTF-8",
        "Content-Type": "application/json",
    }

    def _create_chat():
        return sess.post(
            "https://chat.qwen.ai/api/v2/chats/new",
            headers={**headers, "X-Request-Id": str(uuid.uuid4())},
            json={"title": "Auto Uploader Commit", "models": [model]},
            timeout=max(1.0, min(12.0, _qwen_time_left(deadline))),
        )

    try:
        # 1️⃣ إنشاء المحادثة (مع تجديد الكوكيز تلقائياً لو الجلسة منتهية)
        r_chat = _create_chat()
        if stop_event.is_set():
            return None

        if r_chat.status_code != 200 or not r_chat.json().get("success"):
            log_message(f"⚠️ [{acc_name}] كوكيز منتهية — جاري التجديد التلقائي...", YELLOW)
            # ✅ الفهرس الصحيح + الليستة الأصلية = مفيش حساب بيضيع
            if not auto_refresh_qwen_account(sess, acc_index, accounts_list):
                return None
            if stop_event.is_set() or _qwen_time_left(deadline) <= 0:
                return None
            r_chat = _create_chat()

        if r_chat.status_code != 200 or not r_chat.json().get("success"):
            log_message(f"❌ [{acc_name}] تعذر إنشاء محادثة على {model}.", YELLOW)
            return None

        chat_id = r_chat.json()["data"]["id"]
        fid, cid = str(uuid.uuid4()), str(uuid.uuid4())
        now_ts = int(time.time())

        # 2️⃣ Payload بموديل واحد فقط في الجولة (مش الموديلين مع بعض)
        payload = {
            "stream": True,
            "version": "2.1",
            "incremental_output": True,
            "chatId": chat_id,
            "parentId": "",
            "chat_id": chat_id,
            "chat_mode": "normal",
            "model": model,
            "parent_id": None,
            "messages": [
                {
                    "id": None,
                    "fid": fid,
                    "parentId": None,
                    "childrenIds": [cid],
                    "role": "user",
                    "content": prompt,
                    "user_action": "chat",
                    "files": [],
                    "timestamp": now_ts,
                    "models": [model],
                    "model": model,
                    "chat_type": "t2t",
                    "feature_config": {
                        "thinking_enabled": model_cfg.get("thinking_enabled", False),
                        "output_schema": "phase",
                        "research_mode": "normal",
                        "auto_thinking": False,
                        "thinking_mode": model_cfg.get("thinking_mode", "Fast"),
                        "thinking_format": "summary",
                        "auto_search": True,
                    },
                    "extra": {"meta": {"subChatType": "t2t"}},
                    "sub_chat_type": "t2t",
                    "parent_id": None,
                }
            ],
            "timestamp": now_ts,
        }

        remaining = _qwen_time_left(deadline)
        if stop_event.is_set() or remaining <= 0:
            return None

        log_message(f"📡 [{acc_name}] {email} ← {model} (بث مباشر)...", CYAN)

        # 3️⃣ استقبال البث المباشر مع الإلغاء الفوري
        r_comp = sess.post(
            f"https://chat.qwen.ai/api/v2/chat/completions?chat_id={chat_id}",
            headers={**headers, "X-Request-Id": str(uuid.uuid4())},
            json=payload,
            stream=True,
            timeout=max(1.0, remaining),
        )

        if r_comp.status_code != 200:
            log_message(f"❌ [{acc_name}] السيرفر رد بـ HTTP {r_comp.status_code}.", YELLOW)
            return None

        full_reply = []
        for line in r_comp.iter_lines():
            # 🛑 حساب تاني فاز أو انتهت المهلة → اقطع الاتصال فوراً ووفّر الكوتا
            if stop_event.is_set() or _qwen_time_left(deadline) <= 0:
                return None
            if not line:
                continue

            decoded = line.decode("utf-8", errors="replace") if isinstance(line, bytes) else str(line)
            if "rgv587_flag" in decoded or "punish" in decoded:
                log_message(f"⚠️ [{acc_name}] كابتشا WAF — الحساب خرج من السباق.", YELLOW)
                return None
            if not decoded.startswith("data:"):
                continue

            raw = decoded[5:].strip()
            if raw == "[DONE]":
                break
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                choice = (obj.get("choices") or [{}])[0]
                delta = (choice.get("delta") or {}).get("content", "")
                if delta:
                    full_reply.append(delta)
                if choice.get("finish_reason"):
                    break
            except Exception:
                continue

        answer = "".join(full_reply).strip()

        # ✅ أول رد **مكتمل وصالح** يفوز — مش أول حرف من الستريم
        if len(answer) < AI_MIN_VALID_CHARS:
            log_message(f"⚠️ [{acc_name}] رد فارغ أو قصير جداً — تم استبعاده.", YELLOW)
            return None
        if stop_event.is_set() or _qwen_time_left(deadline) <= 0:
            return None   # ⛔ رد متأخر بعد نهاية الجولة = مرفوض

        return {
            "answer": answer,
            "model": model,
            "label": model_cfg.get("label", model),
            "email": email,
            "name": acc_name,
            "account_index": acc_index,
            "elapsed": time.monotonic() - started,
            "cookies": dict(sess.cookies.get_dict() or {}),
        }

    except Exception as err:
        if not stop_event.is_set():
            log_message(f"⚠️ [{acc_name}] خطأ اتصال: {err}", YELLOW)
        return None
    finally:
        try:
            sess.close()
        except Exception:
            pass



def qwenguest_worker(model_cfg, prompt, deadline, stop_event):
    """محاولة اتصال Guest اختيارية. نجاحها يعتمد على قبول الخادم للطلب."""
    if stop_event.is_set() or _qwen_time_left(deadline) <= 0:
        return None
    try:
        from curl_cffi import requests
    except ImportError:
        return None
    model = model_cfg["model"]
    started = time.monotonic()
    sess = requests.Session(impersonate="chrome120")
    headers = {
        "X-Platform": "android",
        "source": "app",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 15; RMX3834 Build/AP3A.240905.015.A2),Dalvik/2.1.0 (Linux; U; Android 15; RMX3834 Build/AP3A.240905.015.A2) AliApp(QWENCHAT/2.7.2) AppType/Release AplusBridgeLite",
        "x-device-id": f"ai{uuid.uuid4().hex[:32]}",
        "Accept": "application/json",
        "Accept-Language": "en-US",
        "Accept-Charset": "UTF-8",
        "Content-Type": "application/json",
    }
    try:
        r_chat = sess.post(
            "https://chat.qwen.ai/api/v2/chats/new",
            headers={**headers, "X-Request-Id": str(uuid.uuid4())},
            json={"title": "Auto Uploader Guest Commit", "models": [model], "chat_mode": "guest"},
            timeout=max(1.0, min(12.0, _qwen_time_left(deadline))),
        )
        if r_chat.status_code != 200 or not r_chat.json().get("success"):
            return None
        chat_id = r_chat.json()["data"]["id"]
        fid, cid = str(uuid.uuid4()), str(uuid.uuid4())
        now_ts = int(time.time())
        payload = {
            "stream": True,
            "version": "2.1",
            "incremental_output": True,
            "chatId": chat_id,
            "parentId": "",
            "chat_id": chat_id,
            "chat_mode": "guest",
            "model": model,
            "parent_id": None,
            "messages": [
                {
                    "id": None,
                    "fid": fid,
                    "parentId": None,
                    "childrenIds": [cid],
                    "role": "user",
                    "content": prompt,
                    "user_action": "chat",
                    "files": [],
                    "timestamp": now_ts,
                    "models": [model],
                    "model": model,
                    "chat_type": "t2t",
                    "feature_config": {
                        "thinking_enabled": model_cfg.get("thinking_enabled", True),
                        "output_schema": "phase",
                        "research_mode": "normal",
                        "auto_thinking": True,
                        "thinking_mode": "Auto",
                        "thinking_format": "summary",
                        "auto_search": True,
                    },
                    "extra": {"meta": {"subChatType": "t2t"}},
                    "sub_chat_type": "t2t",
                    "parent_id": None,
                }
            ],
            "timestamp": now_ts,
        }
        r_comp = sess.post(
            f"https://chat.qwen.ai/api/v2/chat/completions?chat_id={chat_id}",
            headers={**headers, "X-Request-Id": str(uuid.uuid4())},
            json=payload,
            stream=True,
            timeout=max(1.0, _qwen_time_left(deadline)),
        )
        if r_comp.status_code != 200:
            return None
        full_reply = []
        for line in r_comp.iter_lines():
            if stop_event.is_set() or _qwen_time_left(deadline) <= 0:
                return None
            if not line:
                continue
            decoded = line.decode("utf-8", errors="replace") if isinstance(line, bytes) else str(line)
            if not decoded.startswith("data:"):
                continue
            raw = decoded[5:].strip()
            if raw == "[DONE]":
                break
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                choice = (obj.get("choices") or [{}])[0]
                delta = (choice.get("delta") or {}).get("content", "")
                if delta:
                    full_reply.append(delta)
            except Exception:
                continue
        answer = "".join(full_reply).strip()
        if len(answer) < AI_MIN_VALID_CHARS:
            return None
        return {
            "answer": answer,
            "model": model,
            "label": f"{model_cfg.get('label', model)} (Guest)",
            "email": "Guest Session (Bypass)",
            "name": "Guest",
            "elapsed": time.monotonic() - started,
        }
    except Exception:
        return None
    finally:
        try:
            sess.close()
        except Exception:
            pass


def _save_qwen_winner_cookies(accounts_list, winner):
    """💾 حفظ كوكيز الحساب الفائز فقط — من الثريد الرئيسي وتحت القفل."""
    if not winner:
        return
    idx = winner.get("account_index")
    cookies = winner.get("cookies") or {}
    if not isinstance(idx, int) or idx < 0 or idx >= len(accounts_list) or not cookies:
        return

    acc = accounts_list[idx]
    acc["cookies"] = cookies
    acc["cookie_string"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    acc["token"] = cookies.get("token", acc.get("token", ""))
    acc["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    accounts_list[idx] = acc
    _save_qwen_accounts(accounts_list)


def race_accounts(model_cfg, prompt, accounts_list, race_indices=None):
    """
    🏁 يشغّل كل الحسابات في نفس اللحظة على موديل واحد.
       أول حساب يرجّع رد صالح = يفوز، ونقتل الباقي فوراً.
       لو عدّت المهلة ومحدش رد → يرجّع None (ننتقل للموديل التالي).
    """
    model = model_cfg["model"]
    label = model_cfg.get("label", model)
    timeout = float(model_cfg.get("timeout", 30))

    if race_indices is None:
        race_indices = list(range(len(accounts_list)))
    if not race_indices:
        return None

    log_message(
        f"🏁 بدء السباق على {label} ({model}) — {len(race_indices)} حساب بالتوازي "
        f"| ⏱️ مهلة {int(timeout)} ثانية",
        BOLD_CYAN,
    )

    deadline = time.monotonic() + timeout
    stop_event = threading.Event()
    executor = ThreadPoolExecutor(
        max_workers=max(1, len(race_indices)),
        thread_name_prefix=f"qwen-{model}",
    )
    future_map = {}
    winner = None

    try:
        for i in race_indices:
            fut = executor.submit(
                _qwen_worker, i, accounts_list, model_cfg, prompt, deadline, stop_event
            )
            future_map[fut] = i

        # 🚀 إطلاق ثريد الزائر (Guest) بالتوازي في نفس اللحظة
        fut_guest = executor.submit(qwenguest_worker, model_cfg, prompt, deadline, stop_event)
        future_map[fut_guest] = -1

        start_race_time = time.monotonic()

        while future_map:
            elapsed_race = time.monotonic() - start_race_time
            remaining = _qwen_time_left(deadline)
            if remaining <= 0:
                sys.stdout.write("\n")
                sys.stdout.flush()
                log_message(f"⏱️ انتهت مهلة الـ {int(timeout)} ثانية ومحدش رد من {label} ❌", YELLOW)
                break

            # 🌈 طباعة شريط التقدم بالثواني الحركي الملون في نفس السطر (\r)
            if sys.stdout.isatty():
                bar_str = render_seconds_progress_bar(elapsed_race, timeout, width=25, label=f"📡 {label} Race")
                sys.stdout.write(f"\r{bar_str}")
                sys.stdout.flush()

            # ⏱️ انتظار قصير (0.2 ثانية) ليتحدث الشريط حركياً ملوناً في التيرمينال
            done, _pending = concurrent.futures.wait(
                list(future_map.keys()),
                timeout=min(0.2, remaining),
                return_when=FIRST_COMPLETED,
            )

            if not done:
                continue

            for fut in done:
                future_map.pop(fut, None)
                try:
                    result = fut.result()
                except Exception as e:
                    if sys.stdout.isatty():
                        sys.stdout.write("\n")
                        sys.stdout.flush()
                    log_message(f"⚠️ خطأ في سباق {label}: {e}", YELLOW)
                    result = None

                if result and result.get("answer"):
                    winner = result
                    if sys.stdout.isatty():
                        sys.stdout.write("\n")
                        sys.stdout.flush()
                    log_message(
                        f"🏆 الفائز: الحساب [{result['name']}] {result['email']} على {label} "
                        f"في {result['elapsed']:.2f} ثانية ✅ ({len(result['answer'])} حرف)",
                        BOLD_GREEN,
                    )
                    break
            if winner:
                break

        return winner

    finally:
        # 🛑 إشارة الإيقاف لكل الخيوط الباقية (تقطع الاتصال فوراً وتوفّر الكوتا)
        stop_event.set()
        for fut in future_map:
            fut.cancel()
        executor.shutdown(wait=False)
        if winner:
            _save_qwen_winner_cookies(accounts_list, winner)


def _select_race_indices(accounts_list):
    """اختيار الحسابات المتسابقة: كل الحسابات النشطة (أو أول AI_RACE_ACCOUNTS منها عشوائياً)."""
    active = [i for i, a in enumerate(accounts_list) if a.get("status", "active") == "active"]
    if not active:
        active = list(range(len(accounts_list)))
    if AI_RACE_ACCOUNTS and 0 < AI_RACE_ACCOUNTS < len(active):
        random.shuffle(active)
        active = active[:AI_RACE_ACCOUNTS]
    return active


def _call_qwen_ai_direct(prompt):
    """
    🎯 المنطق النهائي بالأولوية:
      🥇 المرحلة 1: سباق كل الحسابات على qwen3.8-max  ⏱️ 30s
      🥈 المرحلة 2: سباق كل الحسابات على qwen3.8-max          ⏱️ 30s
      🥉 المرحلة 3: مفيش حد رد → None → رسالة كوميت عادية بدون AI

    الحد الأقصى للانتظار مضمون = مجموع مهلات المراحل (30 + 30 = 60 ثانية).
    """
    global LAST_AI_SOURCE, LAST_AI_MODEL, LAST_AI_ACCOUNT, LAST_AI_ELAPSED
    _reset_ai_race_state()

    if not AI_ENABLED:
        log_message("🤖 Qwen.ai غير مفعّل — تم التخطي.", YELLOW)
        return None, None

    try:
        import curl_cffi  # noqa: F401
    except ImportError:
        log_message("⚠️ مكتبة curl_cffi غير مثبّتة — تعذر الاتصال بـ Qwen.ai.", RED)
        return None, None

    accounts_list = load_or_create_qwen_accounts()
    if not accounts_list:
        log_message("⚠️ لم يتم العثور على أي حسابات Qwen صالحة.", RED)
        return None, None

    race_indices = _select_race_indices(accounts_list)
    emails = " | ".join(accounts_list[i].get("email", "?") for i in race_indices)
    log_message(f"👥 حسابات السباق ({len(race_indices)}): {emails}", BOLD_CYAN)

    total_stages = len(AI_MODEL_CHAIN)
    for stage, model_cfg in enumerate(AI_MODEL_CHAIN, start=1):
        log_message(
            f"🚦 المرحلة {stage}/{total_stages} ➔ {model_cfg.get('label', model_cfg['model'])}",
            BOLD + CYAN,
        )
        winner = race_accounts(model_cfg, prompt, accounts_list, race_indices)
        if winner:
            LAST_AI_MODEL = winner["label"]
            LAST_AI_SOURCE = f"{winner['label']} Direct"
            LAST_AI_ACCOUNT = winner["email"]
            LAST_AI_ELAPSED = winner["elapsed"]
            return winner["answer"], winner["label"]

        if stage < total_stages:
            nxt = AI_MODEL_CHAIN[stage].get("label", AI_MODEL_CHAIN[stage]["model"])
            log_message(f"➡️ التحويل التلقائي للموديل الاحتياطي: {nxt}", BOLD + YELLOW)

    # 🚀 T2b Integration: استدعاء وضع الزائر الاختياري عند فشل كوكيز الحسابات المسجلة
    log_message("❌ كل الموديلات والحسابات فشلت خلال المهلات المحددة.", RED)
    log_message("🔄 محاولة Guest Mode اختيارية...", BOLD + YELLOW)
    stop_event_g = threading.Event()
    deadline_g = time.monotonic() + 25
    guest_res = qwenguest_worker(AI_MODEL_CHAIN[0], prompt, deadline_g, stop_event_g)
    if not guest_res and len(AI_MODEL_CHAIN) > 1:
        stop_event_g = threading.Event()
        deadline_g = time.monotonic() + 25
        guest_res = qwenguest_worker(AI_MODEL_CHAIN[1], prompt, deadline_g, stop_event_g)

    if guest_res and guest_res.get("answer"):
        LAST_AI_MODEL = guest_res["label"]
        LAST_AI_SOURCE = guest_res["label"]
        LAST_AI_ACCOUNT = guest_res["email"]
        LAST_AI_ELAPSED = guest_res["elapsed"]
        log_message(
            f"✅ تم الحصول على الرد عبر وضع الزائر ({guest_res['label']}) في {guest_res['elapsed']:.2f}s",
            BOLD_GREEN,
        )
        return guest_res["answer"], guest_res["label"]

    log_message("❌ فشل كل المسارات (حسابات + Guest) خلال المهلات المحددة.", RED)
    log_message(f'⏭️ سيتم كتابة رسالة كوميت عادية بدون AI: "{AI_FALLBACK_COMMIT_MSG}"', YELLOW)
    return None, None


def generate_ai_summary(changed_files_lines, short_diff, priority_alerts):
    """
    يبعت لـ Qwen.ai برومبت قصير ويطلب سطرين محددين:
        COMMIT: <سطر واحد>
        SUMMARY: <سطرين لثلاثة>
    يرجع (commit_msg, summary, ai_model) أو (None, None, None).
    """
    priority_note = ""
    if priority_alerts:
        notes = "، ".join(f"{msg}" for _, msg in priority_alerts)
        priority_note = f"ملفات هامة اتعدلت: {notes}. "

    prompt = (
        "أنت مهندس برمجيات خبير (Principal Engineer) متخصص في مراجعة الكود وكتابة رسائل Git احترافية.\n"
        "مهمتك: تحليل التغييرات التالية بعمق وإنتاج رسالة كوميت وملخص تنفيذي بالعربية.\n\n"

        "🎯 صيغة الرد الإلزامية (سطرين فقط، بدون أي مقدمات أو شرح أو Markdown):\n"
        "COMMIT: <العنوان>\n"
        "SUMMARY: <الملخص>\n\n"

        "📐 منهجية التحليل (نفّذها ذهنياً قبل الكتابة):\n"
        "1. صنّف طبيعة التغيير: ميزة جديدة / إصلاح خطأ / إعادة هيكلة / تحديث توثيق / تعديل إعدادات / حذف.\n"
        "2. حدد الملف أو الوحدة الأكثر أهمية في التغييرات وابنِ العنوان حولها.\n"
        "3. لو التغييرات متعددة وغير مترابطة، ركّز على أهم 2-3 تغييرات فقط واذكر الباقي إجمالاً.\n\n"

        "⚖️ قوانين صياغة الكوميت:\n"
        "1. ابدأ بفعل حركة دقيق: إضافة / إصلاح / تحديث / إعادة هيكلة / دمج / حذف / تحسين / تأمين.\n"
        "2. العنوان سطر واحد، 50-80 حرفاً، يصف الوظيفة التقنية بالضبط (ماذا + أين).\n"
        "3. ممنوع نهائياً: 'تغييرات بسيطة'، 'تحديث ملفات'، 'تعديلات متنوعة'، أو أي صياغة عامة.\n"
        "4. ممنوع نسخ أسماء الملفات كقائمة في العنوان؛ صِف الأثر الوظيفي وليس أسماء الملفات.\n\n"

        "⚖️ قوانين صياغة الملخص:\n"
        "1. من 2 إلى 3 جمل: ما تم إنجازه + القيمة المضافة أو المشكلة التي حُلّت + أي أثر جانبي مهم.\n"
        "2. اكتب للمدير التقني وليس للآلة: لغة واضحة، بدون مصطلحات Git خام.\n"
        "3. لو التغيير حذف ملفات فقط، وضّح سبب الحذف المرجّح (تنظيف / استبدال / إلغاء ميزة).\n"
        "4. لو الـ diff مقطوع أو ضخم، اعتمد على أسماء الملفات وأنماطها ولا تخترع تفاصيل غير موجودة.\n\n"

        "🏷️ تسمية إلزامية للملفات الخاصة:\n"
        "- task.md أو tasks.md أو development_tasks.md ← قل 'تاسك' فقط.\n"
        "- plan.md أو master_development_roadmap.md ← قل 'بلان' فقط.\n"
        "- progress.md ← قل 'بروجرس' فقط.\n\n"

        "✅ أمثلة على المستوى المطلوب:\n"
        "COMMIT: إضافة نظام تجديد جلسات Qwen التلقائي مع التبديل بين 3 حسابات\n"
        "SUMMARY: تم بناء آلية تعافي ذاتي تعيد تسجيل الدخول عند انتهاء الكوكيز وتبدّل الحسابات عشوائياً عند فشل أي حساب، مما يضمن استمرارية توليد الملخصات دون تدخل يدوي.\n\n"
        "COMMIT: تحديث التاسك بإغلاق مرحلة الرفع التلقائي وفتح مرحلة الاختبارات\n"
        "SUMMARY: تم تعليم مهام خط الرفع كمكتملة في التاسك وإضافة بنود اختبار التكامل القادمة، بما يعكس انتقال المشروع لمرحلة ضمان الجودة.\n\n"

        f"{priority_note}📁 الملفات المتغيرة:\n{changed_files_lines[:600]}\n\n"
        f"📄 جزء من الـ diff:\n{short_diff[:AI_MAX_DIFF_CHARS]}"
    )

    raw, ai_model = _call_qwen_ai_direct(prompt)
    if not raw:
        return None, None, None

    # استخراج COMMIT و SUMMARY من الرد (بمرونة فائقة تشمل Markdown)
    clean_raw = re.sub(r"```[a-z]*", "", raw).strip()
    commit_msg = None
    summary = None

    m_commit = re.search(r"(?:COMMIT|\*\*COMMIT\*\*|Commit|الكوميت)\s*[:：]\s*(.+)", clean_raw, re.IGNORECASE)
    m_summary = re.search(r"(?:SUMMARY|\*\*SUMMARY\*\*|Summary|الملخص)\s*[:：]\s*(.+)", clean_raw, re.IGNORECASE | re.DOTALL)

    if m_commit:
        commit_msg = m_commit.group(1).strip().splitlines()[0][:150]
        commit_msg = re.sub(r"^[\*\s\"']+|[\*\s\"']+$", "", commit_msg)

    if m_summary:
        summary = m_summary.group(1).strip()[:600]

    # لو الرد جه بدون الصيغة المطلوبة: استخدم أول سطر كـ commit والباقي summary
    if not commit_msg and clean_raw:
        lines = [l.strip() for l in clean_raw.splitlines() if l.strip() and not l.startswith("```")]
        if lines:
            commit_msg = re.sub(r"^[\*\s\"']+|[\*\s\"']+$", "", lines[0])[:150]
            summary = " ".join(lines[1:4])[:600] if len(lines) > 1 else lines[0][:600]

    if not commit_msg:
        log_message(
            f'⚠️ تعذر استخراج رسالة الكوميت من رد Qwen.ai — سيتم استخدام "{AI_FALLBACK_COMMIT_MSG}".',
            YELLOW,
        )
        return None, None, None

    return commit_msg, summary, ai_model
