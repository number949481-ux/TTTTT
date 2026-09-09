#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
🚀 03_upload_to_Fable_github.py — نسخة سباق Qwen المتوازي
=============================================================
سكريبت مستقل تماماً — لا يعدل أي ملفات قديمة.

الوظيفة:
  1. يراقب مجلد السكريبت + Downloads بحثاً عن ملفات .tar.gz جديدة
  2. يفك الضغط بأمان (حماية من Path Traversal)
  3. يقارن مع مستودع GitHub (git status --porcelain)
  4. 🛡️ الحارس الذكي: مفيش تغييرات = ممنوع تشغيل الـ AI نهائياً
  5. 🔔 تنبيهات الملفات الهامة (tasks.md / plan.md / ...) في الصدارة
  6. 🏁 سباق Qwen المتوازي (كل الحسابات في نفس اللحظة على موديل واحد):
        🥇 المرحلة 1: qwen3.8-max   ⏱️ 30 ثانية
        🥈 المرحلة 2: qwen3.8-max            ⏱️ 30 ثانية
        🥉 المرحلة 3: مفيش رد → رسالة كوميت عادية بدون AI
  7. أول حساب يرد بردّ صالح يفوز، وباقي الطلبات تُقطع فوراً (توفير كوتا)
  8. إشعار تليجرام HTML منسق + تقرير محلي تقرير_qwen.md (باسم الموديل الفائز)
  9. حذف ملف tar.gz بعد النجاح

⚠️ الأسرار من متغيرات البيئة أو ملف .env المحلي فقط:
   GITHUB_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
=============================================================
"""

import concurrent.futures
import filecmp
import html
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor
from datetime import datetime

# =============================================================
# 🤖 [P15] محرك كوين المستقل — كل منظومة Qwen.ai Direct في موديول واحد
# =============================================================
import qwen_engine
from qwen_engine import (
    AI_ENABLED, AI_MODEL_CHAIN, AI_MAX_DIFF_CHARS, AI_MIN_VALID_CHARS,
    AI_RACE_ACCOUNTS, AI_FALLBACK_COMMIT_MSG,
    QWEN_ACCOUNTS_FILE, DEFAULT_QWEN_ACCOUNTS, load_or_create_qwen_accounts,
    SPECTRUM_256, get_rainbow_color, get_second_rainbow_color,
    render_seconds_progress_bar,
    auto_refresh_qwen_account, race_accounts, generate_ai_summary,
)

# -------------------------------------------------------------
# 🖥️ إصلاح الترميز والتخزين المؤقت على ويندوز (كونسول UTF-8 + ألوان)
# -------------------------------------------------------------
if os.name == "nt":
    os.system("")  # تفعيل ألوان ANSI في كونسول ويندوز فقط

def _force_utf8_stream(stream_name):
    """
    ضبط ترميز UTF-8 بأمان للـ stdout/stderr.
    ✅ نستخدم reconfigure أولاً (بدون إعادة تغليف) عشان منقفلش الـ buffer الأصلي
       لو السكريبت اتحمّل أكتر من مرة (استيراد/اختبارات) — ده كان بيسبب
       ValueError: I/O operation on closed file.
    """
    stream = getattr(sys, stream_name, None)
    if stream is None:
        return
    try:
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        elif hasattr(stream, "buffer"):
            setattr(sys, stream_name, io.TextIOWrapper(
                stream.buffer, encoding="utf-8", errors="replace", line_buffering=True
            ))
    except Exception:
        pass


_force_utf8_stream("stdout")
_force_utf8_stream("stderr")

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

# -------------------------------------------------------------
# ⏱️ حاسب أوقات الخطوات (Step execution timer)
# -------------------------------------------------------------
class StepTimer:
    def __init__(self):
        self.start_time = time.time()
        self.last_mark = time.time()

    def mark(self):
        now = time.time()
        elapsed = now - self.last_mark
        self.last_mark = now
        col = get_second_rainbow_color(elapsed)
        return f"({col}{elapsed:.2f}s{RESET})"

    def total(self):
        elapsed = time.time() - self.start_time
        col = get_second_rainbow_color(elapsed)
        return f"({col}{elapsed:.2f}s{RESET})"


# =============================================================
# ⚙️⚙️⚙️ الإعدادات — عدّل من هنا فقط ⚙️⚙️⚙️
# =============================================================

# 🔔 الملفات الهامة — أي تعديل فيها يظهر تنبيه بارز في أول التقرير
# (المقارنة باسم الملف فقط - غير حساسة لحالة الأحرف)
PRIORITY_FILES = {
    "task.md":                       "📝 تم تحديث التاسك",
    "tasks.md":                      "📝 تم تحديث التاسك",
    "plan.md":                       "📋 تم تحديث البلان",
    "development_tasks.md":          "⚙️ تم تحديث التاسك",
    "master_development_roadmap.md": "🗺️ تم تحديث البلان",
    "progress.md":                   "🚩 تم تحديث سير التقدم",
}

# 📂 مسارات المراقبة (حصر المراقبة في Downloads فقط وتجاهل مجلد السكربت)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
WATCH_DIRS = [DOWNLOADS_DIR]


# 🔄 إعدادات التزامن الكامل والحذف الآمن (Mirror Sync)
MIRROR_SYNC_MODE = True

# 🛡️ [P14] حارس الحذف المرآتي: أرشيف جزئي/ناقص لا يحق له مسح المستودع.
# لو نسبة الملفات المخطط حذفها من الريبو تتجاوز الحد ➔ نعتبر الأرشيف جزئياً
# ونعطّل الحذف لهذه الدورة فقط (النسخ/التعديل يستمران طبيعياً).
DELETE_GUARD_ENABLED = True
DELETE_GUARD_MAX_DELETE_RATIO = 0.5   # الحد الأقصى المسموح: 50% من ملفات الريبو

# 📥 مرحلة النسخ: نتخطى .git فقط — .agents و .github و .gitignore ملفات مشروع تتزامن طبيعي
COPY_SKIP_DIRS = {".git"}

# 🗑️ مرحلة الحذف: نحمي .git دايماً
DELETE_SKIP_DIRS = {".git"}

# 🛡️ مجلدات حساسة: تتزامن بالكامل (M/A/D) لو موجودة في الأرشيف،
# لكن لو غابت عنه تماماً (أداة ضغط تجاهلت المخفي) تُترك في المستودع بدون مساس
SMART_PROTECT_DIRS = {".agents", ".github"}

# 🛡️ ملفات جذر حساسة: نفس المنطق الشرطي — تتزامن لو موجودة، وتُترك لو غابت تماماً
SMART_PROTECT_FILES = {".gitignore"}

# 🔐 ملفات أسرار لا يتم نسخها للريبو حتى لو ظهرت داخل الأرشيف
NEVER_COPY_FILES = {"accounts_qwen.json"}


def _norm_rel(path):
    return os.path.normpath(path).replace("\\", "/")


def _is_never_copy_file(filename):
    """منع نسخ الأسرار: accounts_qwen.json و .env و .env.* (local/production/...)"""
    return filename in NEVER_COPY_FILES or filename == ".env" or filename.startswith(".env.")



# 🐙 مستودع GitHub (المستودع التجريبي الجديد)
REPO_URL = "https://github.com/number949481-ux/TTTTT.git"
REPO_BRANCH = "main"
GIT_USER_NAME = "Auto Uploader Bot"
GIT_USER_EMAIL = "auto-uploader@localhost"

# 📝 اسم ملف التقرير المحلي (منفصل عن نسخة Groq القديمة)
REPORT_FILENAME = "تقرير_qwen.md"

# =============================================================
# 🔑 الأسرار — من متغيرات البيئة أولاً ثم ملف .env المحلي (بدون أي توكن مكتوب في الكود)
# =============================================================
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")


def _load_dotenv(path=ENV_FILE):
    """
    قارئ .env بسيط بدون أي مكتبات خارجية:
      KEY=VALUE   (يتجاهل الأسطر الفاضية و# التعليقات ويدعم علامات التنصيص)
    متغيرات البيئة الحقيقية لها الأولوية دائماً على الملف.
    """
    loaded = {}
    if not os.path.isfile(path):
        return loaded
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
                    loaded[key] = value
    except Exception:
        pass
    return loaded


_DOTENV_LOADED = _load_dotenv()

# تحميل التوكنات مع Fallback للملف المحلي وقيم التشغيل المباشرة
_token_file = os.path.join(SCRIPT_DIR, "telegram_bot_token.txt")
_fallback_tg_token = ""
if os.path.exists(_token_file):
    try:
        _fallback_tg_token = open(_token_file, "r", encoding="utf-8").read().strip()
    except Exception:
        pass

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", _fallback_tg_token or "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1124247595").strip()

# =============================================================
# 🧰 أدوات مساعدة
# =============================================================
def mask_token(text):
    """إخفاء أي أسرار من النصوص قبل طباعتها في اللوج."""
    if not text:
        return text
    for secret in (GITHUB_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID):
        if secret and len(secret) > 3 and secret in text:
            text = text.replace(secret, "***TOKEN***")
    return text

def log_message(message, color=RESET):
    ts = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    print(f"{color}[{ts}] {mask_token(str(message))}{RESET}", flush=True)

def h(text):
    """هروب HTML آمن لأي نص ديناميكي داخل رسالة تليجرام."""
    return html.escape(str(text), quote=False)

# 📢 [P15] حقن لوجر السكريبت داخل محرك كوين المستقل (طوابع زمنية + إخفاء توكنات موحدة)
qwen_engine.configure(log_func=log_message)

# -------------------------------------------------------------
# 📱 إرسال إشعار تليجرام (HTML)
# -------------------------------------------------------------
def send_telegram_message(message_html):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log_message("⚠️ إعدادات تليجرام غير موجودة (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID) — تم تخطي الإشعار.", YELLOW)
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_html[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:
            ok = json.loads(resp.read().decode("utf-8")).get("ok", False)
        if ok:
            log_message("تم إرسال إشعار تليجرام بنجاح. ✅", GREEN)
            return True
        else:
            log_message("⚠️ تليجرام رد برفض الرسالة (HTML). جاري المحاولة بنص عادي...", YELLOW)
    except Exception as e:
        log_message(f"⚠️ فشل إرسال إشعار HTML: {mask_token(str(e))} — جاري المحاولة بنص عادي...", YELLOW)

    # 🔄 Fallback: إرسال بنص عادي بدون parse_mode عند حدوث أي خطأ HTML
    try:
        plain_text = re.sub(r"<[^>]+>", "", message_html)[:4000]
        fallback_payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": plain_text,
            "disable_web_page_preview": True,
        }
        fallback_data = urllib.parse.urlencode(fallback_payload).encode("utf-8")
        req_fb = urllib.request.Request(url, data=fallback_data, method="POST")
        with urllib.request.urlopen(req_fb, timeout=20) as resp_fb:
            ok_fb = json.loads(resp_fb.read().decode("utf-8")).get("ok", False)
        if ok_fb:
            log_message("تم إرسال إشعار تليجرام بالنص العادي (Fallback) بنجاح. ✅", GREEN)
        else:
            log_message("⚠️ تليجرام رد برفض الرسالة حتى بالنص العادي.", YELLOW)
        return ok_fb
    except Exception as fb_err:
        log_message(f"⚠️ فشل إرسال إشعار تليجرام النهائي: {mask_token(str(fb_err))}", YELLOW)
        return False

# -------------------------------------------------------------
# 🖥️ تنفيذ أوامر النظام (git) بأمان
# -------------------------------------------------------------
def _build_git_env():
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"   # ممنوع أي سؤال تفاعلي
    env["GIT_ASKPASS"] = ""
    return env

def run_cmd(cmd, cwd=None, timeout=300):
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True,
        encoding="utf-8", errors="replace",
        timeout=timeout, env=_build_git_env(),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"فشل الأمر: {mask_token(' '.join(cmd))}\n{mask_token(result.stderr or result.stdout or '')}"
        )
    return (result.stdout or "").strip()

# -------------------------------------------------------------
# 🛡️ فك ضغط آمن (حماية من CVE-2007-4559 Path Traversal)
# -------------------------------------------------------------
def _is_within_directory(directory, target):
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonpath([abs_directory]) == os.path.commonpath([abs_directory, abs_target])

def safe_extract(tar, path):
    for member in tar.getmembers():
        member_path = os.path.join(path, member.name)
        if not _is_within_directory(path, member_path):
            raise RuntimeError(f"⛔ ملف خطير داخل الأرشيف (Path Traversal): {member.name}")
    if sys.version_info >= (3, 12):
        tar.extractall(path, filter="data")
    else:
        tar.extractall(path)

# -------------------------------------------------------------
# 📱 إرسال تنبيه أخطاء تليجرام عند الأرشيف المعطوب / مجلد غير صالح
# -------------------------------------------------------------
def send_telegram_error_alert(tar_path, exc):
    """إرسال إشعار تليجرام عاجل باللغة العربية عند فشل معالجة مجلد غير صالح."""
    error_str = str(exc)
    tar_name = os.path.basename(tar_path)
    win_code = getattr(exc, 'winerror', None)

    is_path_error = (
        win_code in (123, 206, 3)
        or "WinError 123" in error_str
        or "filename, directory name" in error_str
        or "syntax is incorrect" in error_str
    )
    cause_msg = (
        "تم ضغط/رفع مجلد يحتوي على أسماء ملفات أو مسارات غير مدعومة على الويندوز."
        if is_path_error
        else "حدث خطأ أثناء فك الضغط أو النسخ."
    )

    msg_html = (
        "🚨 <b>تنبيه — فشل معالجة الأرشيف (مجلد غير صالح)!</b>\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        f"📦 <b>الملف المضغوط:</b> <code>{h(tar_name)}</code>\n"
        f"⚠️ <b>السبب:</b> {h(cause_msg)}\n"
        f"💥 <b>الخطأ التقني:</b> <code>{h(error_str[:300])}</code>\n"
        f"⏰ <b>التوقيت:</b> <code>{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}</code>\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "🚫 <b>الإجراء:</b> تم إيقاف معالجة هذا الملف ونقله لعدم التكرار."
    )
    return send_telegram_message(msg_html)

# -------------------------------------------------------------
# 📦 البحث عن أحدث ملف tar.gz في مجلد السكريبت ومجلد Downloads
# -------------------------------------------------------------
def find_latest_tar_file(exclude_set=None):
    if exclude_set is None:
        exclude_set = set()
    candidates = []
    for d in WATCH_DIRS:
        if not os.path.exists(d):
            continue
        try:
            for name in os.listdir(d):
                if name.lower().endswith(".tar.gz") and not name.lower().endswith(".failed"):
                    full = os.path.join(d, name)
                    if full not in exclude_set and os.path.isfile(full):
                        candidates.append((os.path.getmtime(full), full))
        except OSError:
            continue
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]

# -------------------------------------------------------------
# 📂 تحديد جذر المصدر داخل الأرشيف المفكوك
# -------------------------------------------------------------
def get_source_root(extract_dir):
    entries = [e for e in os.listdir(extract_dir) if not e.startswith(".")]
    # لو فيه مجلد واحد اسمه فيه clone أو repo نعتبره الجذر
    if len(entries) == 1 and os.path.isdir(os.path.join(extract_dir, entries[0])):
        return os.path.join(extract_dir, entries[0])
    for e in entries:
        full = os.path.join(extract_dir, e)
        if os.path.isdir(full) and any(kw in e.lower() for kw in ("clone", "repo")):
            return full
    return extract_dir


# -------------------------------------------------------------
# 🎯 [P14] كشف جذر ذكي مرتكز على الريبو (Repo-Anchored Root Detection)
# -------------------------------------------------------------
def _list_rel_files(base_dir, max_files=5000):
    """يبني مجموعة المسارات النسبية للملفات (متجاهلاً .git) حتى حد أقصى."""
    rel_files = set()
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d != ".git"]
        rel_dir = os.path.relpath(root, base_dir)
        for f in files:
            rel = f if rel_dir == "." else os.path.join(rel_dir, f)
            rel_files.add(_norm_rel(rel))
            if len(rel_files) >= max_files:
                return rel_files
    return rel_files


def detect_best_source_root(extract_dir, repo_dir, max_depth=3):
    """
    [P14/TSK-3202] يختار جذر المصدر الصحيح داخل الأرشيف المفكوك بمقارنة
    أسماء الملفات النسبية مع الريبو المستنسخ فعلياً:
    - يجمع مرشحي الجذور: extract_dir نفسه + كل المجلدات حتى عمق max_depth.
    - المرشح صاحب أعلى تقاطع بأسماء الملفات مع ملفات الريبو يفوز.
    - لو الريبو فارغ أو لا يوجد أي تقاطع ➔ fallback للسلوك القديم get_source_root.
    هذا يمنع نسخ الأرشيف بمسار داخلي خاطئ يجعل Git يرى A+D بدلاً من M.
    """
    try:
        repo_files = _list_rel_files(repo_dir)
        if not repo_files:
            return get_source_root(extract_dir)

        candidates = [extract_dir]
        for root, dirs, _files in os.walk(extract_dir):
            dirs[:] = [d for d in dirs if d != ".git"]
            depth = os.path.relpath(root, extract_dir).count(os.sep) + (0 if root == extract_dir else 1)
            if depth >= max_depth:
                dirs[:] = []
                continue
            for d in dirs:
                candidates.append(os.path.join(root, d))

        best_root, best_score = None, 0
        for cand in candidates:
            cand_files = _list_rel_files(cand)
            if not cand_files:
                continue
            score = len(cand_files & repo_files)
            if score > best_score:
                best_root, best_score = cand, score

        if best_root and best_score > 0:
            if best_root != extract_dir:
                log_message(
                    f"🎯 [P14] كشف جذر ذكي: تم اختيار '{os.path.relpath(best_root, extract_dir)}' "
                    f"(تطابق {best_score} ملفاً مع الريبو)", CYAN
                )
            return best_root
        return get_source_root(extract_dir)
    except Exception as e:
        log_message(f"⚠️ [P14] فشل الكشف الذكي للجذر ({e}) — العودة للسلوك القياسي", YELLOW)
        return get_source_root(extract_dir)


# -------------------------------------------------------------
# ⚖️ [P14] مقارنة محتوى ملفين (بايت-ببايت ثم بتوحيد نهايات السطور)
# -------------------------------------------------------------
def _files_content_equal(path_a, path_b):
    """
    [P14/TSK-3203] True لو الملفان متطابقان فعلياً:
    1) مطابقة بايت-ببايت (بعد فحص الحجم أولاً للسرعة).
    2) أو مطابقة بعد توحيد نهايات السطور CRLF→LF (فرق الترميز السطري وحده ≠ تعديل).
    """
    try:
        if filecmp.cmp(path_a, path_b, shallow=False):
            return True
        # فرق نهايات سطور فقط؟ (للملفات حتى 5MB تجنباً لالتهام الذاكرة)
        if os.path.getsize(path_a) > 5_000_000 or os.path.getsize(path_b) > 5_000_000:
            return False
        with open(path_a, "rb") as fa, open(path_b, "rb") as fb:
            a = fa.read().replace(b"\r\n", b"\n")
            b = fb.read().replace(b"\r\n", b"\n")
        return a == b
    except OSError:
        return False


# -------------------------------------------------------------
# 🔄 تزامن شجرة الملفات بالكامل (Upsert Sync + حارس الحذف + حماية الأسرار)
# -------------------------------------------------------------
def sync_tree(src, dst, mirror_delete=True):
    """
    تزامن شجرة الملفات:
    - ينسخ الملفات الجديدة والمعدلة.
    - يحذف من المستودع الملفات التي لم تعد موجودة في الأرشيف إذا mirror_delete=True.
    - يحمي .git دائماً.
    - حماية شرطية: .agents و .github و .gitignore لو غابوا تماماً عن الأرشيف
      لا يُحذفوا من المستودع (أداة ضغط تجاهلت المخفي ≠ حذف مقصود).
    - يمنع نسخ ملفات الأسرار: .env و .env.* و accounts_qwen.json.
    """
    src_rel_files = set()

    # 1) نسخ الملفات الجديدة والمعدلة وبناء قائمة ملفات المصدر
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in COPY_SKIP_DIRS]

        rel_dir = os.path.relpath(root, src)
        target_root = dst if rel_dir == "." else os.path.join(dst, rel_dir)
        os.makedirs(target_root, exist_ok=True)

        for filename in files:
            rel_file = filename if rel_dir == "." else os.path.join(rel_dir, filename)
            rel_file_norm = _norm_rel(rel_file)

            # لا تنسخ ملفات الأسرار للريبو نهائياً
            if _is_never_copy_file(filename):
                log_message(f"🔐 تم تخطي ملف حساس ولن يتم نسخه للريبو: {rel_file_norm}", YELLOW)
                continue

            src_rel_files.add(rel_file_norm)
            src_path = os.path.join(root, filename)
            dst_path = os.path.join(target_root, filename)

            # ⚖️ [P14/TSK-3203] Upsert Copy: لو الملف موجود بالفعل في الريبو
            # ومحتواه مطابق (ولو بفرق CRLF/LF فقط) ➔ لا نلمسه إطلاقاً —
            # Git يحتفظ بالتتبع الأصلي ولا يظهر M كاذب ولا A خاطئ.
            if os.path.isfile(dst_path) and _files_content_equal(src_path, dst_path):
                continue

            shutil.copy2(src_path, dst_path)

    # 2) لو الحذف المرآتي غير مفعّل، توقف هنا
    if not mirror_delete:
        return

    # 3) الحماية الشرطية: المجلدات والملفات الحساسة الغائبة تماماً عن الأرشيف تُستثنى من الحذف
    missing_protected = {
        d for d in SMART_PROTECT_DIRS
        if not os.path.isdir(os.path.join(src, d))
    }
    missing_protected_files = {
        _norm_rel(f) for f in SMART_PROTECT_FILES
        if not os.path.isfile(os.path.join(src, f))
    }
    # ملاحظة: missing_protected_files لا تُضاف لـ skip_on_delete (ده فلتر مجلدات فقط) —
    # الملفات تتفلتر بسطر continue داخل حلقة الملفات
    skip_on_delete = DELETE_SKIP_DIRS | missing_protected

    if missing_protected or missing_protected_files:
        log_message(
            f"🛡️ حماية شرطية: {sorted(missing_protected | missing_protected_files)} غائبة عن الأرشيف — لن تُمَس في المستودع",
            YELLOW
        )

    # 4) [P14/TSK-3204] جمع قائمة المرشحين للحذف أولاً (بدون تنفيذ)
    repo_file_count = 0
    would_delete = []
    for root, dirs, files in os.walk(dst):
        dirs[:] = [d for d in dirs if d not in skip_on_delete]

        rel_dir = os.path.relpath(root, dst)

        for filename in files:
            rel_file = filename if rel_dir == "." else os.path.join(rel_dir, filename)
            rel_file_norm = _norm_rel(rel_file)

            # حماية إضافية لمجلد .git
            if rel_file_norm == ".git" or rel_file_norm.startswith(".git/"):
                continue

            repo_file_count += 1

            # حماية شرطية لملفات الجذر الحساسة الغائبة عن الأرشيف
            if rel_file_norm in missing_protected_files:
                continue

            if rel_file_norm not in src_rel_files:
                would_delete.append((os.path.join(root, filename), rel_file_norm))

    # 5) [P14/TSK-3204] حارس الحذف: لو الأرشيف ناقص (هيمسح نسبة كبيرة من الريبو)
    #    نوقف الحذف المرآتي بالكامل لهذه الدورة — الأرشيف الجزئي ≠ حذف مقصود.
    if would_delete and DELETE_GUARD_ENABLED and repo_file_count > 0:
        delete_ratio = len(would_delete) / repo_file_count
        if delete_ratio > DELETE_GUARD_MAX_DELETE_RATIO:
            log_message(
                f"🛑 [P14] حارس الحذف: الأرشيف يطلب حذف {len(would_delete)}/{repo_file_count} "
                f"ملف ({delete_ratio:.0%}) — يتجاوز الحد {DELETE_GUARD_MAX_DELETE_RATIO:.0%}. "
                f"تم إلغاء الحذف المرآتي بالكامل لحماية المستودع (أرشيف جزئي على الأرجح).",
                RED
            )
            return

    # 6) تنفيذ الحذف الفعلي (بعد اجتياز الحارس)
    for abs_path, rel_file_norm in would_delete:
        try:
            os.remove(abs_path)
            log_message(f"🗑️ تم حذف ملف غير موجود في الأرشيف: {rel_file_norm}", YELLOW)
        except OSError as e:
            log_message(
                f"⚠️ تعذر حذف الملف غير الموجود في الأرشيف: {rel_file_norm} ({e})",
                YELLOW
            )

# -------------------------------------------------------------
# 🔤 فك ترميز أسماء الملفات العربية من مخرجات git
# -------------------------------------------------------------
def decode_git_path(path_str):
    path_str = path_str.strip()
    if path_str.startswith('"') and path_str.endswith('"'):
        path_str = path_str[1:-1]
    try:
        return path_str.encode('latin1').decode('unicode_escape').encode('latin1').decode('utf-8')
    except Exception:
        return path_str

# -------------------------------------------------------------
# 🔔 اكتشاف الملفات الهامة ضمن التغييرات
# -------------------------------------------------------------
def detect_priority_files(all_changed_paths):
    alerts = []
    seen = set()
    for path in all_changed_paths:
        base = os.path.basename(path).lower()
        if base in PRIORITY_FILES and base not in seen:
            seen.add(base)
            alerts.append((path, PRIORITY_FILES[base]))
    return alerts


# =============================================================
# 🌸 1. كارت عدم وجود تغييرات باللون البينك للكونسول (English Pink Card)
# =============================================================
def render_no_changes_card(tar_name, repo_branch, elapsed_str):
    """
    طباعة كارت مينيبيست باللون البينك في Terminal / CMD عند عدم وجود أي تغييرات.
    """
    width = 74
    line = f"{BOLD_PINK}╭" + "─" * (width - 2) + f"╮{RESET}"
    sep  = f"{BOLD_PINK}├" + "─" * (width - 2) + f"┤{RESET}"
    bottom = f"{BOLD_PINK}╰" + "─" * (width - 2) + f"╯{RESET}"

    header_text = "🌸 SMART GUARD ➔ NO CHANGES DETECTED"
    h_padded = f"│ {header_text}".ljust(width - 1) + "│"
    header_line = f"{BOLD_PINK}{h_padded}{RESET}"

    rows = [
        f"│ 📦 Archive  : {tar_name}".ljust(width - 1) + "│",
        f"│ 📂 Target   : {repo_branch} branch (Claude-Fable-5)".ljust(width - 1) + "│",
        f"│ ⚡ Elapsed  : {elapsed_str} total execution time".ljust(width - 1) + "│",
        "│ 🤖 AI Race  : Skipped (Quota & Time Saved)".ljust(width - 1) + "│",
        "│ 📱 Telegram : Notification Sent (Arabic Status Update)".ljust(width - 1) + "│",
    ]

    print("\n" + line, flush=True)
    print(header_line, flush=True)
    print(sep, flush=True)
    for r in rows:
        print(f"{PINK}{r}{RESET}", flush=True)
    print(bottom + "\n", flush=True)

# -------------------------------------------------------------
# 🌳 منسق شجري راسي لمسارات الملفات (الكونسول وتليجرام)
# -------------------------------------------------------------
def _format_file_tree_telegram(file_list, max_show=7):
    lines = []
    total = len(file_list)
    show_count = min(total, max_show)
    for i in range(show_count):
        branch = "└" if (i == show_count - 1 and total <= max_show) else "├"
        lines.append(f"     {branch} <code>{h(file_list[i])}</code>")
    if total > max_show:
        rem = total - max_show
        lines.append(f"     └ <code>... (+{rem} ملفات أخرى)</code>")
    return lines

def _format_file_tree_console(file_list, icon, label, w=76, max_show=5):
    rows = []
    if not file_list:
        return rows
    total = len(file_list)
    show_count = min(total, max_show)
    rows.append(f"║    {icon} {label} ({total}):".ljust(w - 1) + "║")
    for i in range(show_count):
        branch = "└" if (i == show_count - 1 and total <= max_show) else "├"
        path_str = file_list[i]
        if len(path_str) > w - 16:
            path_str = "..." + path_str[-(w - 19):]
        rows.append(f"║       {branch} {path_str}".ljust(w - 1) + "║")
    if total > max_show:
        rem = total - max_show
        rows.append(f"║       └ ... (+{rem} more files)".ljust(w - 1) + "║")
    return rows

# =============================================================
# 🟢 2. كارت نجاح الرفع بالأخضر النيون والـ Metrics (Green Dashboard Card)
# =============================================================
def render_success_card(tar_name, commit_hash, commit_msg, new_files, upd_files, del_files,
                         ren_cnt, cop_cnt, total_cnt, ai_summary, elapsed_str,
                         ai_source="", ai_account="", ai_elapsed=0.0):
    """
    طباعة لوحة تحكم نيون خضراء كاملة بالـ Metrics ومسارات الملفات رأسياً في الكونسول.
    """
    w = 76
    top    = f"{BOLD_GREEN}╔" + "═" * (w - 2) + f"╗{RESET}"
    sep_d  = f"{BOLD_GREEN}╠" + "═" * (w - 2) + f"╣{RESET}"
    sep_s  = f"{BOLD_GREEN}╠" + "─" * (w - 2) + f"╣{RESET}"
    bottom = f"{BOLD_GREEN}╚" + "═" * (w - 2) + f"╝{RESET}"

    title = "🚀 GITHUB AUTO-UPLOADER ➔ DEPLOYMENT SUCCESSFUL"
    t_line = f"{BOLD_GREEN}║ {title}".ljust(w - 1) + f"║{RESET}"

    short_msg = (commit_msg[:45] + "...") if len(commit_msg) > 48 else commit_msg

    info_rows = [
        f"║ 📦 Archive  : {tar_name}".ljust(w - 1) + "║",
        f"║ 🔑 Commit   : {commit_hash} ➔ \"{short_msg}\"".ljust(w - 1) + "║",
        f"║ ⏱️ Elapsed  : {elapsed_str} total execution time".ljust(w - 1) + "║",
    ]

    stat_title = f"{BOLD_CYAN}║ 📊 METRICS & FILE STATS".ljust(w - 1) + f"{BOLD_GREEN}║{RESET}"
    stat_rows = [
        f"║    🆕 New      : {len(new_files)} files".ljust(w - 1) + "║",
        f"║    ✏️ Modified : {len(upd_files)} files".ljust(w - 1) + "║",
        f"║    🗑️ Deleted  : {len(del_files)} files".ljust(w - 1) + "║",
        f"║    🔄 Renamed  : {ren_cnt} files · 📋 Copied: {cop_cnt} files".ljust(w - 1) + "║",
        f"║    📦 Total    : {total_cnt} file changes".ljust(w - 1) + "║",
    ]

    # أسطر مسارات الملفات الشجرية الرأسية في الكونسول
    tree_rows = []
    tree_rows.extend(_format_file_tree_console(new_files, "🆕", "New Files", w))
    tree_rows.extend(_format_file_tree_console(upd_files, "✏️", "Modified Files", w))
    tree_rows.extend(_format_file_tree_console(del_files, "🗑️", "Deleted Files", w))

    ai_label = ai_source or "No AI"
    summary_title = f"{BOLD_CYAN}║ 🤖 AI SUMMARY ({ai_label})".ljust(w - 1) + f"{BOLD_GREEN}║{RESET}"
    clean_ai = (ai_summary.replace("\n", " ").strip()[:65] + "...") if ai_summary else "N/A (Standard Formatting)"
    summary_row = f"║    \"{clean_ai}\"".ljust(w - 1) + "║"
    winner_row = None
    if ai_summary and ai_account:
        winner_row = f"║    🏆 Winner : {ai_account} in {ai_elapsed:.2f}s".ljust(w - 1) + "║"

    print("\n" + top, flush=True)
    print(t_line, flush=True)
    print(sep_d, flush=True)
    for r in info_rows:
        print(f"{GREEN}{r}{RESET}", flush=True)
    print(sep_s, flush=True)
    print(stat_title, flush=True)
    for r in stat_rows:
        print(f"{GREEN}{r}{RESET}", flush=True)
    if tree_rows:
        print(sep_s, flush=True)
        print(f"{BOLD_CYAN}║ 📁 DETAILED FILE PATHS BREAKDOWN".ljust(w - 1) + f"{BOLD_GREEN}║{RESET}", flush=True)
        for r in tree_rows:
            print(f"{GREEN}{r}{RESET}", flush=True)
    print(sep_s, flush=True)
    print(summary_title, flush=True)
    print(f"{GREEN}{summary_row}{RESET}", flush=True)
    if winner_row:
        print(f"{GREEN}{winner_row}{RESET}", flush=True)
    print(bottom + "\n", flush=True)

# =============================================================
# 🎨 بناء إشعار تليجرام النهائي (HTML)
# =============================================================
# -------------------------------------------------------------
# 📱 بناء الهيدر الديناميكي للإشعار الخارجي (Push Notification)
# -------------------------------------------------------------
def build_telegram_header(priority_alerts, total_changes):
    """
    📱 اختيارات الهيدر لإشعارات تليجرام وقفل الشاشة (اختر السطر اللي يعجبك وشيل الشباك # من قدامه):
    """
    file_word = "ملف واحد" if total_changes == 1 else f"{total_changes} ملفات"
    
    if priority_alerts:
        first_msg = priority_alerts[0][1]
        
        # 1️⃣ [موصى به] النمط النظيف بفاصل النقطة (آمن 100% بدون أقواس):
        return f"🚀 {first_msg} • تم رفع {file_word} لـ GitHub"
        
        # 2️⃣ النمط التدفقي بالسهم العربي:
        # return f"🚀 {first_msg} ➔ تم رفع {file_word} لـ GitHub"
        
        # 3️⃣ النمط المباشر المختصر:
        # return f"🚀 {first_msg} ➔ GitHub"
        
        # 4️⃣ النمط بفاصل الأقواس المربعة المفصولة:
        # return f"🚀 {first_msg} [ {file_word} ] ➔ GitHub"

    else:
        # 1️⃣ [موصى به] النمط النظيف بفاصل النقطة للرفع العادي:
        return f"🏆 تحديث جديد • تم رفع {file_word} لـ GitHub"
        
        # 2️⃣ النمط التدفقي بالسهم العربي:
        # return f"🏆 تم رفع {file_word} جديدة لـ GitHub"
        
        # 3️⃣ النمط المباشر المختصر:
        # return f"🏆 تحديث جديد ({file_word}) ➔ GitHub"

def build_telegram_report(tar_path, commit_hash, commit_msg, ai_summary,
                          priority_alerts, new_files, updated_files,
                          deleted_files, renamed_files, copied_files,
                          total_changes, ai_source):
    header = build_telegram_header(priority_alerts, total_changes)
    lines = [f"<b>{header}</b>"]

    # 1) تنبيهات الملفات الهامة — دايماً في الصدارة
    if priority_alerts:
        lines.append("➖➖➖➖➖➖➖➖➖➖")
        lines.append("🔔 <b>تنبيه — ملفات هامة اتحدثت:</b>")
        for path, msg in priority_alerts:
            lines.append(f"  {h(msg)}")
            lines.append(f"     └ <code>{h(path)}</code>")

    # 2) ملخص الذكاء الاصطناعي (باسم الموديل الفائز الحقيقي في السباق)
    if ai_summary:
        lines.append("➖➖➖➖➖➖➖➖➖➖")
        lines.append(f"🤖 <b>ملخص التغييرات ({h(ai_source or 'AI')}):</b>")
        lines.append(f"<i>{h(ai_summary)}</i>")
        if qwen_engine.LAST_AI_ACCOUNT:
            lines.append(
                f"🏆 <b>الفائز بالسباق:</b> <code>{h(qwen_engine.LAST_AI_ACCOUNT)}</code> "
                f"في <b>{qwen_engine.LAST_AI_ELAPSED:.2f}</b> ثانية"
            )
    else:
        lines.append("➖➖➖➖➖➖➖➖➖➖")
        lines.append("🤖 <b>الذكاء الاصطناعي:</b> <i>مفيش رد خلال المهلة — تم استخدام الكوميت العادي.</i>")

    # 3) تفاصيل المسارات والملفات المتغيرة رأسياً (تحت بعض)
    if new_files or updated_files or deleted_files:
        lines.append("➖➖➖➖➖➖➖➖➖➖")
        lines.append("📁 <b>تفاصيل المسارات والملفات المتغيرة:</b>")
        if new_files:
            lines.append(f"\n  🆕 <b>ملفات جديدة ({len(new_files)}):</b>")
            lines.extend(_format_file_tree_telegram(new_files))
        if updated_files:
            lines.append(f"\n  ✏️ <b>ملفات معدلة ({len(updated_files)}):</b>")
            lines.extend(_format_file_tree_telegram(updated_files))
        if deleted_files:
            lines.append(f"\n  🗑 <b>ملفات محذوفة ({len(deleted_files)}):</b>")
            lines.extend(_format_file_tree_telegram(deleted_files))

    # 4) بيانات الكوميت والملف
    lines.append("➖➖➖➖➖➖➖➖➖➖")
    lines.append(f"📦 <b>الملف المرفوع:</b> <code>{h(os.path.basename(tar_path))}</code>")
    lines.append(f"📂 <b>المصدر:</b> <code>{h(os.path.dirname(tar_path))}</code>")
    lines.append(f"💬 <b>رسالة الكوميت:</b> <code>{h(commit_msg)}</code>")
    lines.append(f"🔑 <b>الكوميت:</b> <code>{h(commit_hash)}</code>")

    # 5) الإحصائيات
    lines.append("➖➖➖➖➖➖➖➖➖➖")
    lines.append("📊 <b>إحصائيات التغييرات:</b>")
    lines.append(f"  🆕 جديدة: <b>{len(new_files)}</b>")
    lines.append(f"  ✏️ معدلة: <b>{len(updated_files)}</b>")
    lines.append(f"  🗑 محذوفة: <b>{len(deleted_files)}</b>")
    lines.append(f"  🔄 معاد تسميتها: <b>{len(renamed_files)}</b>")
    lines.append(f"  📋 منسوخة: <b>{len(copied_files)}</b>")
    lines.append("➖➖➖➖➖➖➖➖➖➖")
    lines.append(f"📦 <b>إجمالي التغييرات:</b> <b>{total_changes}</b> ✅")

    return "\n".join(lines)

# -------------------------------------------------------------
# معالجة ملف tar.gz منفرد
# -------------------------------------------------------------
def process_single_tar(tar_path):
    if not os.path.exists(tar_path):
        print(f"{RED}❌ Error: File not found: {tar_path}{RESET}")
        return False
    if not GITHUB_TOKEN:
        print(f"{RED}❌ Environment variable GITHUB_TOKEN missing — process halted.{RESET}")
        return False

    timer = StepTimer()
    tar_name = os.path.basename(tar_path)
    log_message(f"🚀 [START] Processing archive: {tar_name}", BOLD_CYAN)

    temp_dir = None
    success = False
    try:
        temp_dir = tempfile.mkdtemp(prefix="git_upload_gpt_")
        extract_dir = os.path.join(temp_dir, "extracted")
        clone_dir = os.path.join(temp_dir, "_clone")
        os.makedirs(extract_dir)

        log_message(f"[1/4] 📦 Unpacking archive safely... {timer.mark()}", CYAN)
        with tarfile.open(tar_path, "r:gz") as tar:
            safe_extract(tar, extract_dir)

        log_message(f"[2/4] 🐙 Fetching GitHub repository ({REPO_BRANCH})... {timer.mark()}", CYAN)
        auth_url = REPO_URL.replace("https://", f"https://x-access-token:{GITHUB_TOKEN}@")
        run_cmd(["git", "clone", "-b", REPO_BRANCH, auth_url, clone_dir])

        # [P14/TSK-3202] كشف الجذر الذكي بعد الاستنساخ: نقارن مرشحي الجذر
        # داخل الأرشيف بملفات الريبو الفعلية ونختار الأعلى تطابقاً.
        source_root = detect_best_source_root(extract_dir, clone_dir)

        run_cmd(["git", "config", "core.quotepath", "false"], cwd=clone_dir)
        run_cmd(["git", "config", "user.name", GIT_USER_NAME], cwd=clone_dir)
        run_cmd(["git", "config", "user.email", GIT_USER_EMAIL], cwd=clone_dir)
        run_cmd(["git", "config", "credential.helper", ""], cwd=clone_dir)

        log_message(f"[3/4] 📂 Syncing source files to workspace (Mirror Sync)... {timer.mark()}", CYAN)
        sync_tree(source_root, clone_dir, mirror_delete=MIRROR_SYNC_MODE)

        # =====================================================
        # 🛡️ Guard 1: git status --porcelain
        # =====================================================
        log_message(f"[4/4] 🔍 Inspecting working directory status... {timer.mark()}", CYAN)
        porcelain = run_cmd(["git", "status", "--porcelain"], cwd=clone_dir)
        if not porcelain.strip():
            render_no_changes_card(tar_name, REPO_BRANCH, timer.total())
            send_telegram_message(
                "🔍 <b>نتيجة الفحص — لا توجد تغييرات</b>\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                f"📦 <b>الملف المفحوص:</b> <code>{h(tar_name)}</code>\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                "✅ المستودع <b>مطابق تماماً</b> لمحتوى الأرشيف.\n"
                "🚫 لا توجد تغييرات لرفعها على GitHub.\n"
                "🤖 <i>تم تخطي AI (توفير وقت).</i>"
            )
            _write_report(tar_path, "N/A (مستودع مطابق)", "لا توجد تغييرات",
                          [], [], [], [], [], [], 0, None)
            _delete_tar(tar_path)
            success = True
            return True

        run_cmd(["git", "add", "-A"], cwd=clone_dir)
        diff_out = run_cmd(["git", "diff", "--cached", "--name-status", "-M", "-C"], cwd=clone_dir)

        new_files, updated_files, deleted_files = [], [], []
        renamed_files, copied_files = [], []

        for line in diff_out.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                parts = line.split(maxsplit=1)
                if len(parts) < 2:
                    continue
            status = parts[0].strip()
            if status.startswith("R") and len(parts) >= 3:
                renamed_files.append((decode_git_path(parts[1]), decode_git_path(parts[2])))
            elif status.startswith("C") and len(parts) >= 3:
                copied_files.append((decode_git_path(parts[1]), decode_git_path(parts[2])))
            elif status == "A":
                new_files.append(decode_git_path(parts[1]))
            elif status == "M":
                updated_files.append(decode_git_path(parts[1]))
            elif status == "D":
                deleted_files.append(decode_git_path(parts[1]))
            else:
                updated_files.append(decode_git_path(parts[1]))

        total_changes = (len(new_files) + len(updated_files) + len(deleted_files)
                         + len(renamed_files) + len(copied_files))

        # =====================================================
        # 🛡️ Guard 2: total_changes == 0
        # =====================================================
        if total_changes == 0:
            render_no_changes_card(tar_name, REPO_BRANCH, timer.total())
            send_telegram_message(
                "🔍 <b>نتيجة الفحص — لا توجد تغييرات</b>\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                f"📦 <b>الملف المفحوص:</b> <code>{h(tar_name)}</code>\n"
                "➖➖➖➖➖➖➖➖➖➖\n"
                "✅ المستودع <b>مطابق تماماً</b> لمحتوى الأرشيف.\n"
                "🚫 لا توجد تغييرات لرفعها على GitHub.\n"
                "🤖 <i>تم تخطي AI (توفير وقت).</i>"
            )
            _write_report(tar_path, "N/A (مستودع مطابق)", "لا توجد تغييرات",
                          [], [], [], [], [], [], 0, None)
            _delete_tar(tar_path)
            success = True
            return True

        log_message(
            f"📊 Changes found: {len(new_files)} new, {len(updated_files)} modified, "
            f"{len(deleted_files)} deleted, {len(renamed_files)} renamed, {len(copied_files)} copied.",
            BOLD_GREEN
        )

        # 🔔 Priority files detection
        all_changed = (new_files + updated_files + deleted_files
                       + [n for _, n in renamed_files] + [d for _, d in copied_files])
        priority_alerts = detect_priority_files(all_changed)
        for path, msg in priority_alerts:
            log_message(f"🔔 Priority File Update Detected: {msg} ➔ {path}", BOLD + YELLOW)

        # 🤖 Qwen3.8-Max Direct Summary
        short_diff = ""
        if AI_ENABLED:
            try:
                stat = run_cmd(["git", "diff", "--cached", "--stat"], cwd=clone_dir)
                short_diff = stat[:AI_MAX_DIFF_CHARS]
            except Exception:
                short_diff = ""

        ai_commit, ai_summary, ai_model = generate_ai_summary(diff_out, short_diff, priority_alerts)

        # 🏷️ الموديل اللي فاز فعلياً بالسباق (3.8 أو 3.7) بدل الاسم الثابت
        if ai_summary and (ai_model or qwen_engine.LAST_AI_SOURCE):
            ai_source = qwen_engine.LAST_AI_SOURCE or f"{ai_model} Direct"
        else:
            ai_source = "بدون AI"

        # 💬 رسالة الكوميت النهائية:
        #    لو نجح AI → رسالته | لو فشلت كل الموديلات → "كوميت" حرفياً
        commit_msg = ai_commit if ai_commit else AI_FALLBACK_COMMIT_MSG

        commit_args = ["git", "commit", "-m", commit_msg]
        if priority_alerts:
            body = "\n".join(f"{msg}: {path}" for path, msg in priority_alerts)
            commit_args += ["-m", body]
        run_cmd(commit_args, cwd=clone_dir)
        commit_hash = run_cmd(["git", "rev-parse", "HEAD"], cwd=clone_dir)[:8]

        log_message(f"🚀 Pushing changes to GitHub main branch... {timer.mark()}", BLUE)
        try:
            run_cmd(["git", "push", "origin", REPO_BRANCH], cwd=clone_dir)
        except Exception as e:
            log_message(f"⚠️ تعارض في الـ Push ({e}) — جاري عمل git pull --rebase وإعادة الرفع تلقائياً...", YELLOW)
            run_cmd(["git", "pull", "--rebase", "origin", REPO_BRANCH], cwd=clone_dir)
            run_cmd(["git", "push", "origin", REPO_BRANCH], cwd=clone_dir)
        
        # 🟢 Display Green Success Dashboard in Terminal / CMD
        render_success_card(
            tar_name=tar_name,
            commit_hash=commit_hash,
            commit_msg=commit_msg,
            new_files=new_files,
            upd_files=updated_files,
            del_files=deleted_files,
            ren_cnt=len(renamed_files),
            cop_cnt=len(copied_files),
            total_cnt=total_changes,
            ai_summary=ai_summary,
            elapsed_str=timer.total(),
            ai_source=ai_source,
            ai_account=qwen_engine.LAST_AI_ACCOUNT,
            ai_elapsed=qwen_engine.LAST_AI_ELAPSED,
        )

        send_telegram_message(build_telegram_report(
            tar_path, commit_hash, commit_msg, ai_summary, priority_alerts,
            new_files, updated_files, deleted_files, renamed_files,
            copied_files, total_changes, ai_source
        ))

        _write_report(tar_path, commit_hash, commit_msg, new_files,
                      updated_files, deleted_files, renamed_files,
                      copied_files, priority_alerts, total_changes, ai_summary)

        _delete_tar(tar_path)
        success = True

    except Exception as e:
        log_message(f"🚨 خطأ أثناء معالجة الملف المضغوط: {e}", RED)

        # 1️⃣ إرسال إشعار تليجرام بشكل آمن (لا يوقف العزل لو فشل النت)
        try:
            send_telegram_error_alert(tar_path, e)
        except Exception as alert_err:
            log_message(f"⚠️ فشل إرسال تنبيه تليجرام: {alert_err}", RED)

        # 2️⃣ عزل الملف وإعادة تسميته مع Timestamp لمنع الحلقة المفرغة (Infinite Loop)
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            failed_path = f"{tar_path}.{ts}.failed"
            os.replace(tar_path, failed_path)
            log_message(f"⚠️ تم إعادة تسمية الملف المعطوب إلى: {os.path.basename(failed_path)} لمنع التكرار.", YELLOW)
        except Exception as rename_err:
            log_message(f"⚠️ تعذر إعادة تسمية الملف ({rename_err}) — جاري الحذف كـ Fallback لحماية السكريبت...", RED)
            try:
                _delete_tar(tar_path)
            except Exception as del_err:
                log_message(f"🚨 تعذر حذف الملف أيضاً: {del_err}", RED)
        return False

    finally:
        if temp_dir and os.path.exists(temp_dir):
            log_message(f"🧹 Cleaning up temporary files... {timer.mark()}", BLUE)
            shutil.rmtree(temp_dir, ignore_errors=True)
        if success:
            log_message("✨ Pipeline completed successfully.", BOLD_GREEN)

    return success

# -------------------------------------------------------------
# كتابة التقرير المحلي (تقرير_chatgpt.md — منفصل عن القديم)
# -------------------------------------------------------------
def _write_report(tar_path, commit_hash, commit_msg, new_files, updated_files,
                  deleted_files, renamed_files, copied_files,
                  priority_alerts, total_changes, ai_summary):
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    entry = [f"## 📅 تقرير عملية الرفع (Qwen.ai Direct Edition) — {now_str}"]

    if priority_alerts:
        entry.append("\n### 🔔 تنبيهات الملفات الهامة:")
        for path, msg in priority_alerts:
            entry.append(f"- **{msg}** — `{path}`")

    if ai_summary:
        entry.append(f"\n### 🤖 ملخص {qwen_engine.LAST_AI_SOURCE or 'AI'}:")
        entry.append(f"> {ai_summary}")
        if qwen_engine.LAST_AI_ACCOUNT:
            entry.append(f"\n- 🏆 **الفائز بالسباق:** `{qwen_engine.LAST_AI_ACCOUNT}` في **{qwen_engine.LAST_AI_ELAPSED:.2f}** ثانية")
    else:
        entry.append("\n### 🤖 الذكاء الاصطناعي:")
        entry.append("> لم يرد أي موديل خلال المهلة — تم استخدام رسالة الكوميت العادية.")

    entry.append(f"\n- 📦 **الملف المرفوع:** `{os.path.basename(tar_path)}`")
    entry.append(f"- 💬 **رسالة الكوميت:** `{commit_msg}`")
    entry.append(f"- 🔑 **حالة الكوميت:** `{commit_hash}`")
    entry.append("- 📊 **إحصائيات الرفع:**")
    entry.append(f"  - 🆕 جديدة: **{len(new_files)}** · ✏️ محدثة: **{len(updated_files)}** · "
                 f"🗑️ محذوفة: **{len(deleted_files)}** · 🔄 معاد تسميتها: **{len(renamed_files)}** · "
                 f"📋 منسوخة: **{len(copied_files)}**")
    entry.append(f"  - 📦 الإجمالي: **{total_changes}**")

    for title, items in (("🆕 الملفات الجديدة", new_files),
                         ("✏️ الملفات المحدثة", updated_files),
                         ("🗑️ الملفات المحذوفة", deleted_files)):
        if items:
            entry.append(f"\n### {title}:")
            for idx, f in enumerate(sorted(items), 1):
                entry.append(f"{idx}. `{f}`")

    if renamed_files:
        entry.append("\n### 🔄 الملفات المعاد تسميتها:")
        for idx, (o, n) in enumerate(sorted(renamed_files), 1):
            entry.append(f"{idx}. `{o}` ← إلى ← `{n}`")
    if copied_files:
        entry.append("\n### 📋 الملفات المنسوخة:")
        for idx, (s, d) in enumerate(sorted(copied_files), 1):
            entry.append(f"{idx}. `{s}` ← إلى ← `{d}`")

    entry.append("\n---\n")
    report_path = os.path.join(SCRIPT_DIR, REPORT_FILENAME)
    with open(report_path, "a", encoding="utf-8") as rf:
        rf.write("\n".join(entry))
    log_message(f"تمت إضافة التقرير في: {report_path} 📝", GREEN)

# -------------------------------------------------------------
# حذف ملف tar.gz الأصلي
# -------------------------------------------------------------
def _delete_tar(tar_path):
    log_message(f"جاري حذف الملف المضغوط الأصلي: {os.path.basename(tar_path)}...", YELLOW)
    try:
        os.remove(tar_path)
        log_message("تم حذف الملف المضغوط الأصلي بنجاح. 🗑️", GREEN)
    except Exception as e:
        log_message(f"⚠️ فشل حذف الملف المضغوط: {e}", RED)

# -------------------------------------------------------------
# البرنامج الرئيسي
# -------------------------------------------------------------
def _startup_banner():
    """🚦 طباعة ملخص إعدادات السباق وحالة الأسرار عند بدء التشغيل."""
    if AI_ENABLED:
        chain_txt = " ➔ ".join(
            f"{c.get('label', c['model'])} ({int(c.get('timeout', 30))}ث)" for c in AI_MODEL_CHAIN
        )
        max_wait = int(sum(float(c.get("timeout", 30)) for c in AI_MODEL_CHAIN))
        who = "كل الحسابات النشطة" if not AI_RACE_ACCOUNTS else f"{AI_RACE_ACCOUNTS} حسابات"
        log_message(
            f"🏁 سباق Qwen مفعّل: {who} بالتوازي على {chain_txt} "
            f"| أقصى انتظار {max_wait} ثانية ثم كوميت عادي. 🚀",
            GREEN,
        )
    else:
        log_message("🤖 ذكاء Qwen.ai معطّل — سيُستخدم التنسيق القياسي.", YELLOW)

    if _DOTENV_LOADED:
        log_message(f"🔐 تم تحميل {len(_DOTENV_LOADED)} متغير سري من ملف .env المحلي.", CYAN)
    if not GITHUB_TOKEN:
        log_message("⚠️ GITHUB_TOKEN غير موجود — حط التوكن في متغير بيئة أو في ملف .env جنب السكريبت.", RED)
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log_message("⚠️ إعدادات تليجرام ناقصة — الإشعارات هتتخطى (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).", YELLOW)


def main():
    _startup_banner()

    if len(sys.argv) >= 2:
        process_single_tar(os.path.abspath(sys.argv[1]))
        return

    failed_blacklist = set()
    log_message("وضع المراقبة المستمرة — بانتظار ملفات .tar.gz جديدة... (Ctrl+C للخروج)", CYAN)
    try:
        while True:
            tar_path = find_latest_tar_file(exclude_set=failed_blacklist)
            if tar_path:
                try:
                    res = process_single_tar(tar_path)
                    if not res:
                        failed_blacklist.add(tar_path)
                except Exception as e:
                    log_message(f"🚨 فشل استثنائي غير متوقع: {e} — سيتم إضافة الملف للقائمة السوداء واستئناف المراقبة.", RED)
                    failed_blacklist.add(tar_path)
            time.sleep(2)
    except KeyboardInterrupt:
        print()
        log_message("تم إيقاف المراقبة (Ctrl+C). إلى اللقاء! 👋", YELLOW)

if __name__ == "__main__":
    main()
