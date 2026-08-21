#!/usr/bin/env python3
""" 
╔══════════════════════════════════════════════════════════════╗
║         💬 genspark_chat.py  v4.3                            ║
║     شات Genspark — Smart Picker + Persistent Conversations   ║
╠══════════════════════════════════════════════════════════════╣
║  🎯 Smart Picker: أولويات رصيد مرنة (Config dataclass)      ║
║  💬 Persistent: يحفظ المحادثة ويكمل من آخر رابط             ║
║  🔄 Auto-Login: لو session انتهت يسجل دخول تلقائي           ║
║  📊 Balance Check: يتأكد من الرصيد قبل الإرسال              ║
║  🤖 Workflow: .agents/workflows/00-claude-fable.md          ║
╠══════════════════════════════════════════════════════════════╣
║  تشغيل:                                                       ║
║    python genspark_chat.py "سؤال"           ← كمّل default   ║
║    python genspark_chat.py --new "سؤال"     ← محادثة جديدة   ║
║    python genspark_chat.py --conv work "سؤال"                 ║
║    python genspark_chat.py --cli            ← تفاعلي مستمر   ║
║    python genspark_chat.py --list-convs                       ║
║    python genspark_chat.py --clear-conv default               ║
║    python genspark_chat.py --status         ← حالة الحسابات  ║
║    python genspark_chat.py --export default ← markdown export ║
╚══════════════════════════════════════════════════════════════╝
"""

import argparse
import json
import os
import re
import pathlib
import random
import subprocess
import sys
import time
import uuid
import contextlib
import shutil
import zipfile
import tarfile
from dataclasses import dataclass, field

try:
    import msvcrt  # للويندوز
    def _lock(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    def _unlock(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
except ImportError:
    import fcntl   # لليونكس/لينكس
    def _lock(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    def _unlock(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

@contextlib.contextmanager
def file_lock(path: str, timeout: float = 15.0):
    """مدير قفل ملفات على مستوى نظام التشغيل (آمن تماماً عند موت العمليات)"""
    lock_file = path + ".lock"
    f = open(lock_file, "a+")
    start_time = time.time()
    while True:
        try:
            _lock(f)
            break
        except OSError:
            if time.time() - start_time > timeout:
                f.close()
                raise TimeoutError(f"🔒 فشل الحصول على القفل للملف: {lock_file}")
            time.sleep(random.uniform(0.05, 0.25))  # محاولة إعادة القفل بـ Jitter
    try:
        yield
    finally:
        try:
            _unlock(f)
        finally:
            f.close()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    class _NC:
        def __getattr__(self, _): return ""
    Fore = Style = _NC()


# ══════════════════════════════════════════════════════════════
# ⚡️ إعدادات المستخدم — هنا بس هو اللي بتعدله
# ══════════════════════════════════════════════════════════════

# ── مود Ultra (المدفوع) ───────────────────────────────────────
# False = شغل بالموديل العادي (gpt-4.1) — رخيص وسريع
# True  = شغل بـ Claude Fable 5 — أذكى بكتير بس بيسحب رصيد أكتر
# ملحوظة: لو بعتلك –-ultra ف الأمر، هيكسب على الهنا
ULTRA_MODE    = False

# ── أقل رصيد مقبول للحساب ──────────────────────────────────
# لو رصيد الحساب أقل من الرقم ده، هيتخطاه ويجيب حساب تاني عنده رصيد كويس
MIN_BALANCE   = 90

# ── شير المحادثة تلقائي ──────────────────────────────────
# True  = اطبعلك رابط عام بعد كل رسالة عشان تقدر تشيرها
# False = متعملش شير خالص
AUTO_SHARE    = True

# ── إظهار رسائل Debug ─────────────────────────────────────
# True  = بيطبعلك تفاصيل تقنية في دم الشغل (للحل المشاكل بس)
# False = واجهة نضيفة بدون ضوضاء
SHOW_DEBUG    = False

# ── 📦 Auto-Download Sandbox — التنزيل والفك التلقائي المرن للمشاريع ──
AUTO_DOWNLOAD_SANDBOX        = True               # True = تفعيل محرك التنزيل الذاتي
AUTO_DOWNLOAD_TRIGGER_MODE  = "always"           # "always" | "on_code_change" | "manual"
AUTO_DOWNLOAD_BASE_DIR       = "downloaded_projects" # مجلد حفظ المشاريع محلياً
AUTO_DOWNLOAD_REMOTE_PATH    = "/home/user/webapp"  # المسار المستهدف داخل الساندبوكس
AUTO_DOWNLOAD_FOLDER_NAMING  = "project_id_date"    # "project_id_date" | "prompt_title" | "custom"
AUTO_DOWNLOAD_ZIP_FIRST      = True               # True = يجرب الأرشيف المباشر (TAR.GZ/ZIP) أولاً
AUTO_DOWNLOAD_SHOW_TREE      = True               # True = طباعة شجرة الملفات نيون ملونة بعد التنزيل
AUTO_DOWNLOAD_TREE_MAX_DEPTH = 4                  # أقصى عمق لطباعة الشجرة لتفادي المجلدات الضخمة
AUTO_DOWNLOAD_MAX_SIZE_MB    = 500                # أقصى حجم مسموح به للأرشيف (500MB)
AUTO_DOWNLOAD_HISTORY_FILE  = "download_history.json" # سجل المشاريع المسحوبة محلياً
AUTO_DOWNLOAD_TIMEOUT       = 30                 # مهلة تنزيل الأرشيف بالثواني

# ══════════════════════════════════════════════════════════════
# 🔗 نظام الروابط المرن — URL Mode
# ══════════════════════════════════════════════════════════════

# هل نستخدم الروابط لإكمال المحادثة؟
# True  = يقرأ آخر رابط من URLS_FILE ويكمل منه (ذاكرة مستمرة)
# False = يبدأ شات جديد كل مرة بدون أي سياق قديم (Stateless)
USE_URL_MODE         = False

# ملف حفظ الروابط — كل الروابط اللي اتعملت هتتسيف هنا
URLS_FILE            = "genspark_urls.json"

# أقصى عدد روابط يتحفظ في الملف (الأقدم يتحذف تلقائياً)
MAX_SAVED_URLS       = 50

# تحقق إن الرابط عام (Public) قبل إرسال السؤال؟
# True  = لو الرابط خاص يعمله Share تلقائياً قبل الإرسال
# False = ثق في الرابط المحفوظ بدون تحقق (أسرع)
VERIFY_PUBLIC_BEFORE = False

# تحقق إن الرابط الجديد عام بعد استقبال الرد؟
# True  = لو الرابط الجديد خاص يعمله Share تلقائياً قبل الحفظ
# False = احفظ الرابط مباشرة بدون تحقق
VERIFY_PUBLIC_AFTER  = True

# ══════════════════════════════════════════════════════════════
# ⚡️ نهاية إعدادات المستخدم — الكود تحت ده متعدلشع
# ══════════════════════════════════════════════════════════════
_DIR = pathlib.Path(__file__).resolve().parent

# ══════════════════════════════════════════════════════════════
# ⚙️ CONFIG — غيّر اللي عايزه هنا
# ══════════════════════════════════════════════════════════════
@dataclass
class Config:
    """إعدادات مرنة — غيّر أي حاجة وشغّل"""

    # ── ملف الحسابات ──
    accounts_file: str = "accounts_genspark.json" if (_DIR / "accounts_genspark.json").exists() else "Genspark_V5.5/accounts_genspark_V5.5.json"

    # ── Smart Picker — أرقام الرصيد ──
    min_balance: int = 90           # خُفّض — رصيد 45 كافي للإرسال (ثبت بالاختبار)
    prefer_balance: int = 100       # يبدأ بالأعلى رصيد
    use_zero_first: bool = False    # لو True يجرب حسابات رصيدها 0 (disabled — مش عايزين دول)
    check_balance_before: bool = False  # عطل — الكوكيز قديمة فبيفشل API check ويتخطى الحساب
    check_unknown_balance: bool = True  # لو الرصيد None يفحص API ويحدّث
    tie_break: str = "random"      # لو 2 حسابات بنفس الأولوية: "highest" = أعلى رصيد | "random" = عشوائي

    # ── تجديد الرصيد ──
    account_cooldown_hours: int = 1   # خُفّض — الحسابات القديمة (692h+) جاهزة للاستخدام
    balance_refresh_hours: int = 29  # بعد كام ساعة يعتبر الرصيد اتجدد تلقائياً
    refreshed_balance: int = 100     # الرصيد المفترض بعد التجديد

    # ── الموديل + API ──
    model: str = "claude-opus-5"
    use_ultra: bool = False              # True = تفعيل مود Ultra اللي بيسحب رصيد أعلى (1M Context)
    agent_type: str = "code_sandbox"
    timeout: int = 600
    request_web_knowledge: bool = True   # True = يبحث في الإنترنت (بيبطّئ شوية)
    is_private: bool = True              # False = المحادثة هتبقى عامة من الأول

    # ── Retry ──
    max_retries: int = 50            # عدد المحاولات قبل ما يستسلم

    # ── المحادثة ──
    persistent: bool = False         # False = دايماً شات جديد بدون استكمال
    conv_name: str = "default"      # اسم المحادثة الافتراضية
    conv_file: str = "conversations.json"

    # ── روابط المحادثات ──
    max_urls: int = 10              # كام رابط يحفظ — آخر 10 بس عشان الملف ميكبرش

    # ── 📦 Auto-Downloader Engine Controls ──
    auto_download_sandbox: bool = AUTO_DOWNLOAD_SANDBOX
    auto_download_trigger_mode: str = AUTO_DOWNLOAD_TRIGGER_MODE
    auto_download_base_dir: str = AUTO_DOWNLOAD_BASE_DIR
    auto_download_remote_path: str = AUTO_DOWNLOAD_REMOTE_PATH
    auto_download_folder_naming: str = AUTO_DOWNLOAD_FOLDER_NAMING
    auto_download_zip_first: bool = AUTO_DOWNLOAD_ZIP_FIRST
    auto_download_show_tree: bool = AUTO_DOWNLOAD_SHOW_TREE
    auto_download_tree_max_depth: int = AUTO_DOWNLOAD_TREE_MAX_DEPTH
    auto_download_max_size_mb: int = AUTO_DOWNLOAD_MAX_SIZE_MB
    auto_download_history_file: str = AUTO_DOWNLOAD_HISTORY_FILE
    auto_download_timeout: int = AUTO_DOWNLOAD_TIMEOUT
    auto_continue: bool = False      # False = دايماً جديدة بدون سؤال
    ask_new_timeout: int = 3         # كام ثانية ينتظر قبل يتخذ القرار الافتراضي | 0 = ينتظر للأبد
    ask_new_default: str = "new"  # افتراضي لو مضغطتش حاجة: "new"
    default_conv_mode: str = "new"  # "new" = جديدة دايماً | "last" = آخر رابط | "pick" = اختار
    
    # ── 🎛️ مرونة السياق والحفظ (Context & Save Control) ──
    # 💡 لو عايز البوت "دايماً يبدأ شات جديد بدون سياق" وكمان "مش يحفظ أي حاجة في الجيسون"، خلي إعداداتك كده:
    # always_new_chat = True
    # save_to_json = False

    # 1️⃣ always_new_chat: 
    #   True  = كل ما تسأله كأنك بتكلمه لأول مرة (بيصنّع project جديد خالص وبيتجاهل أي محادثة قديمة).
    #   False = بيمشي استكمال طبيعي، يعني بيكمّل على سياق آخر محادثة كنت فيها.
    always_new_chat: bool = True   

    # 2️⃣ save_to_json:
    #   False = اشتغل واعمل اللي تعمله بس متكتبش أي حاجة في الـ conversations.json (الشات بيكون طاير).
    #   True  = احفظ الروابط والرسايل أول بأول في الجيسون عشان لو قفلت السكريبت وفتحته ألاقي حاجتي.
    save_to_json: bool = False

    show_url_after_send: bool = True # يطبع الرابط الكامل بعد كل رسالة عشان تقدر تفتحه
    cli_history_max: int = -1       # -1 = يعتمد على الرابط فقط ولا يرسل رسايل قديمة (توفير رصيد) | 0 = كل الرسايل | N = آخر N رسالة

    # ── شير تلقائي ──
    auto_share: bool = False         # True = يعمل شير تلقائي بعد كل رسالة
    share_retry: int = 2            # كام محاولة لو الشير فشل

    # ── Tickets — حفظ الأسئلة والردود في ملفات ──
    save_tickets: bool = False       # True = يحفظ كل سؤال ورد في ملفات تلقائي
    save_dir: str = "tickets"       # المجلد (نسبي للمشروع أو مسار كامل)
    save_format: str = "txt"        # "txt" | "json" | "both"
    save_prefix: str = "chat"       # بداية اسم الملف (chat_001_... أو ticket_001_...)
    save_max_files: int = 10        # آخر كام زوج (سؤال+رد) يحتفظ بيهم — القديم يتحذف
    save_realtime: bool = True      # True = الرد يتكتب لحظي وأنت مستني
    save_prefix_q: str = "❓"        # بداية اسم ملف السؤال (اموجي أو حرف زي q)
    save_prefix_a: str = "✅"        # بداية اسم ملف الرد (اموجي أو حرف زي a)

    # ── Auto-Register في الخلفية ──
    auto_register: bool = True                      # True = يشغل register تلقائي لما الشات يبدأ
    auto_register_script: str = "Genspark_V5.5/genspark_register.py"  # اسم سكربت الإنشاء
    auto_register_max: int = 1                      # كام حساب يعمل ويقفل (0=unlimited)
    auto_register_args: str = "--no-loop"           # args إضافية

    # ── Auto-Refresh Session عند CREDIT_EXHAUSTED ──
    auto_refresh_on_exhausted: bool = True  # True = يعمل re-login تلقائي لو الكريدت خلص (session منتهية)
    refresh_attempts: int = 1               # كام محاولة re-login قبل يصفّر الحساب
    mark_inactive_on_fail: bool = True      # True = يحط active=false لو re-login فشل

    # ── ملف السؤال الخارجي (لو عايز تكتب فيه وتضغط Run) ──
    input_file: str = "chat_send.txt"      # اتركه فاضي لو مش بتستخدمه | "" = معطل

    # ── Cloudflare cookies (cf_clearance) — لو عايز تضيفها يدوياً ──
    cf_cookies_file: str = ""  # ملف فيه cf_clearance — تركها فاضي لو ماشغلتها

    # ── fresh_start — أول رسالة بدون رابط (شات جديد) ──
    fresh_start: bool = False     # ← مؤقتاً False عشان نختبر التكملة على رابط موجود

    # ── Entry URL — نقطة بداية ثابتة ──
    # ضع رابط محادثة Genspark هنا عشان يبدأ منها دايماً لو مفيش محادثة جارية
    # مثال: "https://www.genspark.ai/agents?id=209052fb-bd61-49bb-b60c-b5716651a09d"
    # أو:   "-..."
    entry_url: str = ""  # ← ضع رابط هنا لو عايز Fork من رابط خارجي (مفرغ الآن بناءً على طلبك ليكون الشات جديداً دائماً)
    
    # ── Agents — برومبتات الـ AI Agents يتضافوا قبل رسالتك ──
    # كل ملف هنا هيتقرأ ويتحط قبل السؤال تلقائياً
    # عايز تشيل agent؟ احذف السطر بتاعه أو حط # قبله
    # عايز تضيف؟ أضف المسار في القائمة
    agents: list = field(default_factory=lambda: [
        r"d:\SMS\Genspark\.agents\سيستم\أنت مدير المراجعة.md",
        r"d:\SMS\Genspark\.agents\هندسة-تطبيقات\أنت مراجع الكود الآمن.md",
        r"d:\SMS\Genspark\.agents\هندسة-تطبيقات\أنت مهندس Backend.md",
        r"d:\SMS\Genspark\.agents\سيستم\أنت محقق أخطاء عميق.md",
        r"d:\SMS\Genspark\.agents\سيستم\أنت محلل API Flow.md",
        r"d:\SMS\Genspark\.agents\سيستم\أنت محلل أداء.md",
        r"d:\SMS\Genspark\.agents\تخطيط\أنت مخطط احترافي شامل.md",
    ])
    agents_first_only: bool = False   # True = يضيف الـ agents في أول رسالة فقط (موفر للـ tokens)
                                      # False = يضيف في كل رسالة دايماً
    agents_separator: str = "\n\n---\n\n"  # فاصل بين كل agent وبين رسالتك
    agents_enabled: bool = False  # الكل دفعة واحدة: شغّل أو أوقف الـ agents كلها


    # ── العرض ──
    show_debug: bool = False
    show_balance: bool = True       # يطبع الرصيد قبل كل رسالة


# ══════════════════════════════════════════════════════════════
# 🎨 ألوان ومساعدات
# ══════════════════════════════════════════════════════════════
_DIR      = pathlib.Path(__file__).resolve().parent
GENSPARK  = "https://www.genspark.ai"
LOGIN_HOST = "https://login.genspark.ai"
B2C_TENANT = "gensparkad.onmicrosoft.com"
B2C_POLICY = "B2C_1_new_login"
B2C_BASE   = f"{LOGIN_HOST}/{B2C_TENANT}/{B2C_POLICY}"


def p(color, msg):
    print(f"{color}{msg}{Style.RESET_ALL}")


def extract_project_id(url: str) -> str | None:
    """يستخرج project_id من رابط Genspark (agents?id=... أو viewer?id=...)"""
    import re
    m = re.search(r'[?&]id=([a-f0-9\-]{36})', url)
    return m.group(1) if m else None


def create_downloader_session(cookies: dict):
    """إنشـاء جلسة curl_cffi معزولة وموثقة بالكوكيز المستهدفة"""
    try:
        from curl_cffi import requests as cffi
        sess = cffi.Session(impersonate="chrome124")
    except Exception:
        import requests as cffi
        sess = cffi.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://www.genspark.ai/",
        "Origin": "https://www.genspark.ai"
    }
    sess.headers.update(headers)
    if cookies:
        for k, v in cookies.items():
            sess.cookies.set(str(k), str(v), domain=".genspark.ai")
    return sess


# ══════════════════════════════════════════════════════════════
# 📦 SandboxDownloader — كلاس محرك التنزيل الأصيل والمطور
# ══════════════════════════════════════════════════════════════
class SandboxDownloader:
    """محرك تنزيل وتجميع وفك ضغط مشاريع Genspark Sandbox الأصيل والآمن 100%"""
    IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}

    def __init__(self, cfg: Config):
        self.cfg = cfg

    def is_safe_path(self, base_dir: str, target_path: str) -> bool:
        """حماية حتمية من ثغرة Path Traversal و Symlink Attacks بـ relative_to + commonpath"""
        try:
            base = pathlib.Path(base_dir).resolve()
            target = pathlib.Path(target_path).resolve(strict=False)
            target.relative_to(base)
            return os.path.commonpath([str(base), str(target)]) == str(base)
        except Exception:
            return False

    def print_neon_tree(self, directory: str, prefix: str = "", current_depth: int = 0):
        """طباعة شجرة ملفات مبهجة ونيون ومحددة العمق"""
        if current_depth >= self.cfg.auto_download_tree_max_depth:
            return
        p = pathlib.Path(directory)
        if not p.exists(): return
        try:
            entries = sorted([e for e in p.iterdir() if e.name not in self.IGNORE_DIRS], key=lambda x: (not x.is_dir(), x.name))
        except Exception:
            return
        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            if entry.is_dir():
                print(Fore.CYAN + Style.BRIGHT + f"{prefix}{connector}📁 {entry.name}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                self.print_neon_tree(str(entry), new_prefix, current_depth + 1)
            else:
                try:
                    size_kb = entry.stat().st_size / 1024
                except Exception:
                    size_kb = 0
                print(Fore.GREEN + f"{prefix}{connector}📄 {entry.name} " + Fore.YELLOW + f"({size_kb:.1f} KB)")

    def resolve_folder_name(self, project_id: str, prompt_title: str = "") -> str:
        date_str = time.strftime("%Y%m%d_%H%M%S")
        if self.cfg.auto_download_folder_naming == "project_id_date":
            return f"proj_{project_id[:8]}_{date_str}"
        elif self.cfg.auto_download_folder_naming == "prompt_title" and prompt_title:
            clean_title = re.sub(r'[^\w\u0600-\u06FF]+', '_', prompt_title)[:30].strip('_')
            return f"{clean_title}_{date_str}"
        return f"project_{project_id[:8]}_{date_str}"

    def download_directory_archive(self, sess, project_id: str, remote_path: str, out_dir: str) -> bool:
        url = f"{GENSPARK}/api/code_sandbox/download_directory"
        params = {"project_id": project_id, "path": remote_path}
        
        # إنشـاء بيئـة مؤقتة (Staging Directory)
        out_path = pathlib.Path(out_dir).resolve()
        staging_dir = out_path.parent / f".staging_{project_id[:8]}_{time.strftime('%Y%m%d_%H%M%S')}"
        tmp_file = staging_dir / "archive.download.tmp"
        
        try:
            os.makedirs(staging_dir, exist_ok=True)
            r = sess.get(url, params=params, stream=True, timeout=self.cfg.auto_download_timeout)
            if r.status_code != 200:
                shutil.rmtree(staging_dir, ignore_errors=True)
                return False
            
            downloaded_bytes = 0
            max_bytes = self.cfg.auto_download_max_size_mb * 1024 * 1024
            
            with open(tmp_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        downloaded_bytes += len(chunk)
                        if downloaded_bytes > max_bytes:
                            shutil.rmtree(staging_dir, ignore_errors=True)
                            return False
                        f.write(chunk)
            
            # فحص البصمة الرقمية Magic Bytes
            with open(tmp_file, "rb") as f:
                header = f.read(4)
            
            is_zip = header.startswith(b"PK\x03\x04")
            is_gzip = header.startswith(b"\x1f\x8b")
            
            if not (is_zip or is_gzip):
                shutil.rmtree(staging_dir, ignore_errors=True)
                return False
            
            extracted_target = staging_dir / "extracted"
            os.makedirs(extracted_target, exist_ok=True)
            
            if is_zip:
                with zipfile.ZipFile(tmp_file) as zf:
                    for member in zf.infolist():
                        dest_path = extracted_target / member.filename
                        if self.is_safe_path(str(extracted_target), str(dest_path)):
                            zf.extract(member, str(extracted_target))
                        else:
                            raise ValueError(f"Unsafe ZIP member path detected: {member.filename}")
            elif is_gzip:
                with tarfile.open(tmp_file, mode="r:*") as tf:
                    for member in tf.getmembers():
                        dest_path = extracted_target / member.name
                        if self.is_safe_path(str(extracted_target), str(dest_path)):
                            if hasattr(tarfile, 'data_filter'):
                                tf.extract(member, str(extracted_target), filter='data')
                            else:
                                if not (member.issym() or member.islnk() or member.isdev()):
                                    tf.extract(member, str(extracted_target))
                        else:
                            raise ValueError(f"Unsafe TAR member path detected: {member.name}")
            
            tmp_file.unlink(missing_ok=True)
            
            # ترقية ذرية للمسار النهائي Staging -> Final Path
            if out_path.exists():
                shutil.rmtree(out_path, ignore_errors=True)
            os.makedirs(out_path.parent, exist_ok=True)
            os.replace(extracted_target, out_path)
            shutil.rmtree(staging_dir, ignore_errors=True)
            return True
            
        except Exception as e:
            if SHOW_DEBUG: print(Fore.RED + f"⚠️ [Downloader Error]: {e}")
            shutil.rmtree(staging_dir, ignore_errors=True)
            return False

    def update_download_history(self, project_id: str, local_path: str, owner_email: str, prompt_title: str):
        history_path = _DIR / self.cfg.auto_download_history_file
        tmp_history = history_path.with_suffix(".tmp")
        record = {
            "project_id": project_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "owner_email": owner_email,
            "prompt_title": prompt_title,
            "local_path": str(local_path)
        }
        with file_lock(str(history_path)):
            data = []
            if history_path.exists():
                try: data = json.loads(history_path.read_text(encoding="utf-8"))
                except Exception: data = []
            data.append(record)
            tmp_history.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp_history, history_path)

    def auto_download_project(self, cookies: dict, project_id: str, owner_email: str = "", prompt_title: str = "") -> str | None:
        if not project_id or not self.cfg.auto_download_sandbox:
            return None
        sess = create_downloader_session(cookies)
        folder_name = self.resolve_folder_name(project_id, prompt_title)
        out_dir = _DIR / self.cfg.auto_download_base_dir / folder_name
        
        success = self.download_directory_archive(sess, project_id, self.cfg.auto_download_remote_path, str(out_dir))
        if success:
            self.update_download_history(project_id, str(out_dir), owner_email, prompt_title)
            print(Fore.GREEN + Style.BRIGHT + f"\n🎉 [Auto-Downloader] تم سحب وتفريغ المشروع بنجاح إلى: {out_dir}\n")
            if self.cfg.auto_download_show_tree:
                self.print_neon_tree(str(out_dir))
            return str(out_dir)
        return None


def build_prompt(question: str, cfg: "Config", history: list) -> str:
    """
    يبني الـ prompt النهائي:
    - لو agents_enabled و الأجنتس موجودين → أدمجهم قبل السؤال
    - agents_first_only → بيضيفهم في أول رسالة بس (لو history فاضي)
    - لو ملف مالقيش أو فاضي → يتخطاه بدون error
    """
    if not cfg.agents_enabled or not cfg.agents:
        return question

    is_first_msg = len(history) == 0
    if cfg.agents_first_only and not is_first_msg:
        return question  # مش أول رسالة → متضيفشيهم

    parts = []
    loaded = 0
    for path in cfg.agents:
        try:
            content = pathlib.Path(path).read_text(encoding="utf-8").strip()
            if content:
                parts.append(content)
                loaded += 1
        except Exception:
            pass  # لو الملف مالقيشش → بيتخطاه

    if not parts:
        return question

    parts.append(question)
    p(Fore.MAGENTA, f"  🤖 {loaded} agents اتضافوا للـ prompt")
    return cfg.agents_separator.join(parts)


def hr():
    p(Fore.CYAN, "─" * 62)


# ══════════════════════════════════════════════════════════════
# 🔗 URL Manager — حفظ وقراءة الروابط
# ══════════════════════════════════════════════════════════════
def _urls_path() -> pathlib.Path:
    """مسار ملف الروابط — دايماً جنب الملف الحالي"""
    return _DIR / URLS_FILE


def load_urls(cfg: "Config" = None) -> list:
    """يقرأ كل الروابط المحفوظة من URLS_FILE — يرجع list فاضية لو مفيش أو لو الحفظ غير مفعّل"""
    _save = getattr(cfg, "save_to_json", False) if cfg is not None else False
    if not _save:
        return []
    fp = _urls_path()
    if not fp.exists():
        return []
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_url_entry(project_id: str, public_url: str, question: str = "", email: str = "", cfg: "Config" = None) -> None:
    """
    يحفظ رابط جديد في URLS_FILE.
    - يحتفظ بآخر MAX_SAVED_URLS رابط بس (الأقدم يتحذف).
    - كتابة ذرية (.tmp → rename) لتجنب تلف الملف.
    """
    if cfg is None or not getattr(cfg, "save_to_json", False):
        return
    entries = load_urls(cfg)
    # شيل أي entry قديم بنفس الـ project_id (تجنب التكرار)
    entries = [e for e in entries if e.get("project_id") != project_id]
    entries.append({
        "project_id":      project_id,
        "url":             public_url,
        "is_public":       True,
        "saved_at":        time.strftime("%Y-%m-%dT%H:%M:%S"),
        "question_preview": (question or "")[:80],
        "account":         email,
    })
    # احتفظ بآخر MAX_SAVED_URLS بس
    entries = entries[-MAX_SAVED_URLS:]
    fp = _urls_path()
    fp.parent.mkdir(parents=True, exist_ok=True)
    tmp = fp.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(fp)
    except Exception as e:
        p(Fore.YELLOW, f"  ⚠️ فشل حفظ الرابط: {e}")


def get_last_url(cfg: "Config" = None) -> dict | None:
    """يرجع آخر رابط محفوظ (الأحدث في نهاية الـ list) أو None"""
    entries = load_urls(cfg)
    return entries[-1] if entries else None


def fork_from_url(source_url: str, cookies: dict) -> list:
    """
    🔀 Fork Mode — يجيب الرسائل القديمة من رابط عام ويرجعها كـ list.
    بيجرب 3 endpoints بالترتيب حتى يلاقي رسائل.
    لو فشل يرجع [] (يعني الـ worker يبدأ شات جديد).
    """
    from curl_cffi import requests as cffi

    pid_match = re.search(r"[?&]id=([a-f0-9-]{36})", source_url)
    if not pid_match:
        return []
    source_pid = pid_match.group(1)

    # الـ endpoints بنجربهم بالترتيب
    endpoints = [
        f"{GENSPARK}/agents?id={source_pid}",
        f"{GENSPARK}/autopilotagent_viewer?id={source_pid}",
    ]

    def _extract_msgs_from_nuxt(html_text: str) -> list:
        """يبحث عن session_state.messages في أي مكان في NUXT_DATA"""
        m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html_text, re.DOTALL)
        if not m:
            return []
        try:
            nuxt_raw = json.loads(m.group(1))
        except Exception:
            return []

        # ── 1: rehydrate_nuxt المعروفة ──
        try:
            data = rehydrate_nuxt(nuxt_raw, 1)
            # بحث متعدد المسارات
            for path in [
                lambda d: d.get("data", {}).get("project", {}).get("data", {}),
                lambda d: d.get("data", {}),
                lambda d: d.get("project", {}).get("data", {}),
                lambda d: d,
            ]:
                try:
                    inner = path(data) if isinstance(data, dict) else {}
                    ss = (inner or {}).get("session_state", {})
                    msgs = (ss or {}).get("messages", [])
                    old = [x for x in msgs if isinstance(x, dict) and "role" in x]
                    if old:
                        return old
                except Exception:
                    continue
        except Exception:
            pass

        # ── 2: بحث خام في كل الـ strings بحثاً عن messages ──
        try:
            raw_str = json.dumps(nuxt_raw)
            # لو في session_state كـ string مضمّن
            ss_match = re.search(r'"session_state"\s*:\s*(\{[^{}]{0,50000}\})', raw_str)
            if ss_match:
                ss_obj = json.loads(ss_match.group(1))
                msgs = ss_obj.get("messages", [])
                old = [x for x in msgs if isinstance(x, dict) and "role" in x]
                if old:
                    return old
        except Exception:
            pass

        return []

    try:
        sess = cffi.Session(impersonate="chrome120")
        for name, val in cookies.items():
            sess.cookies.set(name, val, domain="www.genspark.ai")

        for ep in endpoints:
            try:
                r = sess.get(ep, timeout=20)
                if r.status_code != 200:
                    continue
                old_msgs = _extract_msgs_from_nuxt(r.text)
                if old_msgs:
                    p(Fore.CYAN, f"  🔀 Fork: جاب {len(old_msgs)} رسالة من {ep.split('/')[-1].split('?')[0]}")
                    return old_msgs
                p(Fore.YELLOW, f"  🔀 {ep.split('/')[-1].split('?')[0]}: 0 رسايل — بجرب endpoint تاني...")
            except Exception as ep_err:
                p(Fore.YELLOW, f"  ⚠️ {ep}: {ep_err}")
                continue

        p(Fore.YELLOW, f"  ⚠️ fork_from_url: مش قادر يجيب رسايل من {source_pid[:16]}...")
        return []
    except Exception as e:
        p(Fore.YELLOW, f"  ⚠️ fork_from_url فشل: {e}")
        return []



def ensure_public(project_id: str, cookies: dict, cfg: "Config", label: str = "") -> str:
    """
    يضمن إن الرابط عام (Public) — يرجع الـ URL العام.
    يستخدم share_project() مباشرة (بدون _verify_public_viewer_url).
    """
    if not project_id:
        return ""
    base_url = f"{GENSPARK}/autopilotagent_viewer?id={project_id}"
    tag = f"[{label}] " if label else ""

    shared_url = share_project(project_id, cookies, show_debug=cfg.show_debug)
    if shared_url:
        if cfg.show_debug:
            p(Fore.GREEN, f"  {tag}✅ الرابط عام")
        return shared_url

    p(Fore.YELLOW, f"  {tag}⚠️ share فشل — سيُستخدم الرابط الأساسي")
    return base_url


def _cfg_path(cfg: Config, filename: str) -> str:
    """مسار ملف نسبي لمجلد السكربت"""
    return str(_DIR / filename)


# ══════════════════════════════════════════════════════════════
# 🔄 Auto-Register — تشغيل الإنشاء في الخلفية
# ══════════════════════════════════════════════════════════════
def _start_auto_register(cfg: Config):
    """يشغل genspark_register.py في الخلفية — بيرجع subprocess.Popen أو None"""
    if not cfg.auto_register:
        return None
    script = _DIR / cfg.auto_register_script
    if not script.exists():
        p(Fore.YELLOW, f"  ⚠️ Auto-Register: مش لاقي {cfg.auto_register_script}")
        return None
    cmd = [sys.executable, str(script)]
    if cfg.auto_register_max > 0:
        cmd += ["--max", str(cfg.auto_register_max)]
    if cfg.auto_register_args:
        cmd += cfg.auto_register_args.split()
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(_DIR),
            stdout=subprocess.DEVNULL,  # مش يطبع في الشات
            stderr=subprocess.DEVNULL,
        )
        p(Fore.CYAN + Style.BRIGHT,
          f"  🔄 Auto-Register شغال (PID {proc.pid}) → {cfg.auto_register_max or 'unlimited'} حسابات")
        return proc
    except Exception as e:
        p(Fore.RED, f"  ❌ Auto-Register فشل: {e}")
        return None


def _stop_auto_register(proc, run_once=False):
    """يوقف register لما الشات يخلص"""
    if proc is None:
        return
    if run_once:
        p(Fore.CYAN + Style.BRIGHT, f"  🚀 Auto-Register مستمر في الخلفية لتسجيل الحسابات (PID {proc.pid})")
        return
    if proc.poll() is None:  # لسه شغال
        try:
            proc.terminate()
            proc.wait(timeout=5)
            p(Fore.CYAN, f"  ⏹️ Auto-Register اتوقف (PID {proc.pid})")
        except Exception:
            proc.kill()  # force kill
    else:
        p(Fore.GREEN, f"  ✅ Auto-Register خلص (PID {proc.pid})")



# ══════════════════════════════════════════════════════════════
# 📂 Tickets — نظام slot دائري بـ emoji
# ══════════════════════════════════════════════════════════════

# جدول الـ emoji — قابل للتوسيع | save_max_files يتحكم في حجم الحلقة
_SLOT_EMOJIS = [
    "0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣",
    "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣",
    "🔟",  # 10
]

def _slot_emoji(n: int) -> str:
    """يرجع الـ emoji اللي يمثل رقم الـ slot"""
    if 0 <= n < len(_SLOT_EMOJIS):
        return _SLOT_EMOJIS[n]
    return f"[{n}]"  # fallback لو max_files > 11

def _emoji_to_slot(txt: str) -> int:
    """يرجع رقم الـ slot من الـ emoji — -1 لو مش عارف"""
    for i, e in enumerate(_SLOT_EMOJIS):
        if txt.startswith(e):
            return i
    return -1


def _ticket_dir(cfg: Config) -> pathlib.Path:
    """مسار مجلد التيكتات — بينشئه لو مش موجود"""
    d = pathlib.Path(cfg.save_dir)
    if not d.is_absolute():
        d = _DIR / d
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_next_ticket_num(cfg: Config) -> int:
    """
    يرجع الـ slot التالي في الحلقة الدائرية (circular buffer).
    الحلقة: 0 → 1 → ... → (save_max_files-1) → 0 → ...
    يقرأ الملفات ويستنتج آخر slot اتستخدم بناءً على mtime.
    """
    d = _ticket_dir(cfg)
    max_slots = max(1, cfg.save_max_files)
    last_mtime = -1.0
    last_slot = -1
    for f in d.iterdir():
        if cfg.save_prefix not in f.stem:
            continue
        try:
            parts = f.stem.split(f"_{cfg.save_prefix}_")
            if len(parts) < 2:
                continue
            slot = _emoji_to_slot(parts[1])
            if slot < 0:
                continue
            mtime = f.stat().st_mtime
            if mtime > last_mtime:
                last_mtime = mtime
                last_slot = slot
        except (ValueError, IndexError, OSError):
            pass
    if last_slot < 0:
        return 0  # أول مرة
    return (last_slot + 1) % max_slots


def _ticket_filename(cfg: Config, kind: str, num: int) -> str:
    """يولد اسم الملف بـ emoji — kind = 'q' أو 'a'"""
    prefix = cfg.save_prefix_q if kind == "q" else cfg.save_prefix_a
    return f"{prefix}_{cfg.save_prefix}_{_slot_emoji(num)}"


def _save_ticket_question(cfg: Config, question: str, ticket_num: int):
    """يحفظ السؤال في ملف — بيكتب فوق الـ slot القديم"""
    if not cfg.save_tickets:
        return
    d = _ticket_dir(cfg)
    base = _ticket_filename(cfg, "q", ticket_num)
    if cfg.save_format in ("txt", "both"):
        (d / f"{base}.txt").write_text(question, encoding="utf-8")
    if cfg.save_format in ("json", "both"):
        import json as _j
        (d / f"{base}.json").write_text(
            _j.dumps({"type": "question", "slot": ticket_num,
                      "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                      "content": question}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if cfg.show_debug:
        p(Fore.CYAN, f"  📝 تيكت سؤال {_slot_emoji(ticket_num)}")


def _save_ticket_answer(cfg: Config, answer: str, ticket_num: int, extra: dict = None):
    """يحفظ الرد في ملف — بيكتب فوق الـ slot القديم"""
    if not cfg.save_tickets:
        return
    d = _ticket_dir(cfg)
    base = _ticket_filename(cfg, "a", ticket_num)
    if cfg.save_format in ("txt", "both"):
        (d / f"{base}.txt").write_text(answer, encoding="utf-8")
    if cfg.save_format in ("json", "both"):
        import json as _j
        obj = {"type": "answer", "slot": ticket_num,
               "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "content": answer}
        if extra:
            obj.update(extra)
        (d / f"{base}.json").write_text(
            _j.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8",
        )
    if cfg.show_debug:
        p(Fore.GREEN, f"  📝 تيكت رد {_slot_emoji(ticket_num)}")


def _cleanup_old_tickets(cfg: Config):
    """
    مع الـ circular buffer الملفات بتتكتب فوق بعض تلقائياً.
    بس بنمسح الملفات القديمة (بالنظام القديم: 001, 002...) لو لسه موجودة.
    """
    if not cfg.save_tickets:
        return
    d = _ticket_dir(cfg)
    deleted = 0
    for f in list(d.iterdir()):
        if cfg.save_prefix not in f.stem:
            continue
        try:
            parts = f.stem.split(f"_{cfg.save_prefix}_")
            if len(parts) < 2:
                continue
            after = parts[1]
            # النظام القديم: يبدأ برقم + فيه _ (مثلاً 028_2026...)
            if after and after[0].isdigit() and '_' in after:
                f.unlink(missing_ok=True)
                deleted += 1
        except (ValueError, IndexError, OSError):
            pass
    if deleted:
        p(Fore.YELLOW, f"  🗑️ {deleted} ملف قديم (نظام 001) اتحذف")


def load_accounts(cfg: Config) -> list:
    """تحميل الحسابات من JSON"""
    path = _cfg_path(cfg, cfg.accounts_file)
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except Exception:
        return []


def save_accounts(accounts: list, cfg: Config):
    """حفظ ذري — .tmp ثم replace"""
    path = _cfg_path(cfg, cfg.accounts_file)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ══════════════════════════════════════════════════════════════
# 💰 فحص الرصيد من API
# ══════════════════════════════════════════════════════════════
def check_balance(cookies: dict) -> int:
    """يسأل API عن الرصيد الحقيقي — يرجع int أو -1 لو فشل"""
    try:
        from curl_cffi import requests as cffi
        sess = cffi.Session(impersonate="chrome120")
        sess.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        for k, v in cookies.items():
            sess.cookies.set(k, v, domain="www.genspark.ai")
        r = sess.get(f"{GENSPARK}/api/payment/get_credit_balance", timeout=15)
        if r.status_code == 200:
            return r.json().get("data", {}).get("balance", -1)
        if r.status_code == 401:
            return -2  # session منتهية
    except Exception:
        pass
    return -1


# ══════════════════════════════════════════════════════════════
# 🔐 تسجيل دخول تلقائي (B2C flow كامل)
# ══════════════════════════════════════════════════════════════
def do_login(email: str, password: str) -> dict | None:
    """4 خطوات login بدون browser — يرجع cookies أو None"""
    try:
        from curl_cffi import requests as cffi
    except ImportError:
        return None
    sess = cffi.Session(impersonate="chrome120")
    sess.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    try:
        # خطوة 1: جيب csrf + transId
        r1 = sess.get(f"{GENSPARK}/api/login", allow_redirects=True, timeout=25)
        csrf = re.search(r'"csrf"\s*:\s*"([^"]+)"', r1.text)
        tx = re.search(r'"transId"\s*:\s*"([^"]+)"', r1.text)
        if not csrf or not tx:
            return None

        # خطوة 2: بعت email + password
        r2 = sess.post(
            f"{B2C_BASE}/SelfAsserted",
            params={"tx": tx.group(1), "p": B2C_POLICY},
            data={"email": email, "password": password, "request_type": "RESPONSE"},
            headers={
                "x-csrf-token": csrf.group(1),
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": str(r1.url),   # ← مهم! بدونه بيفشل
                "Origin": LOGIN_HOST,
                "Accept": "application/json",
            },
            timeout=25,
        )
        if '"status":"200"' not in r2.text:
            return None

        # خطوة 3: confirmed
        r3 = sess.get(
            f"{B2C_BASE}/api/SelfAsserted/confirmed",
            params={"csrf_token": csrf.group(1), "tx": tx.group(1), "p": B2C_POLICY},
            allow_redirects=False, timeout=25,
        )
        auth_url = r3.headers.get("location", r3.headers.get("Location", ""))
        if not auth_url or "/api/auth" not in auth_url:
            return None

        # خطوة 4: callback
        sess.get(auth_url, allow_redirects=True, timeout=25)
        cookies = dict(sess.cookies)
        return cookies if "session_id" in cookies else None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════
# ⏰ Balance Refresh — تجديد الرصيد بعد N ساعة
# ══════════════════════════════════════════════════════════════
def _maybe_refresh_balance(acc: dict, cfg: Config) -> dict:
    """لو الحساب مشتغلش من balance_refresh_hours ساعة → اعتبر رصيده اتجدد"""
    last = acc.get("last_sent_chat_sent") or acc.get("last_sent", "")  # fallback للاسم القديم
    if not last:
        return acc                   # مجهول → متحاردش
    try:
        from datetime import datetime
        last_dt = datetime.fromisoformat(last)
        hours_passed = (datetime.now() - last_dt).total_seconds() / 3600
        if hours_passed >= cfg.balance_refresh_hours:
            acc["balance"] = cfg.refreshed_balance
            if cfg.show_debug:
                p(Fore.CYAN, f"  ⏰ {acc.get('email','')[:20]}... مضى {hours_passed:.0f}س → رصيد اتجدد ({cfg.refreshed_balance})")
    except Exception:
        pass
    return acc


# ══════════════════════════════════════════════════════════════
# 🌐 Auto-Share — شير ذكي (مرة واحدة بس)
# ══════════════════════════════════════════════════════════════
def _do_auto_share(cfg: Config, conv_name: str, project_id: str, cookies: dict) -> str | None:
    """
    شير ذكي — بيشير بس لو المحادثة مغيرتش متشاركة قبل كده
    لو موجود public_url دلوقتي → برجع من غير API call (وفّر)
    لو مش موجود → يجرب share_retry مرة مع retry
    """
    if not cfg.auto_share or not project_id:
        return None

    # شوف لو في public_url محفوظ وبخص نفس الـ project_id → ماتحاردش
    convs = load_convs(cfg)
    cv = convs.get(conv_name, {})
    saved_url = cv.get("public_url", "")
    # ← Fix: لو الـ public_url قديم (بخص project مختلف) → لازم نعمل شير جديد
    if saved_url and project_id in saved_url:
        return saved_url  # نفس الـ project → متشارك فعلاً

    # مش متشارك → جرب الشير مع retry
    if cfg.show_debug:
        p(Fore.YELLOW, f"  🌐 بيعمل شير لـ [{conv_name}]...")
    for attempt in range(max(1, cfg.share_retry)):
        url = share_project(project_id, cookies, show_debug=cfg.show_debug)
        if url:
            # نجح → احفظ في JSON
            convs2 = load_convs(cfg)
            if conv_name in convs2:
                convs2[conv_name]["public_url"] = url
                save_convs(convs2, cfg)
            p(Fore.GREEN, f"  🌐 شير: {url}")
            return url
        if attempt < cfg.share_retry - 1:
            time.sleep(2)  # انتظر ثانيتين وجرّب تاني
    if cfg.show_debug:
        p(Fore.RED, "  ❌ الشير فشل")
    return None


# ══════════════════════════════════════════════════════════════
# 📋 Smart Project Picker — اختيار أحسن project للحساب الحالي
# ══════════════════════════════════════════════════════════════
def pick_best_project(conv: dict, target_email: str) -> str | None:
    """
    اختار آخر project يملكه target_email في urls[].
    Genspark بيربط كل project بصاحبه — لازم نكمل بنفس الحساب.
    لو مفيش project للحساب ده → None (ابدأ project جديد)
    """
    if not conv or not target_email:
        return None
    email_norm = target_email.strip().lower()
    urls = conv.get("urls", [])
    for entry in reversed(urls):   # من الأحدث للأقدم
        owner = (entry.get("owner_email") or "").strip().lower()
        if owner == email_norm:
            return entry.get("project_id")
    return None


# ══════════════════════════════════════════════════════════════
# 🎯 Smart Picker — اختيار أفضل حساب
# ══════════════════════════════════════════════════════════════
def pick_account(accounts: list, cfg: Config, skip_emails: set = None) -> tuple[dict, dict] | None:
    """
    يختار أفضل حساب حسب الـ Config:
      🥇 balance ≥ prefer_balance (100)
      🥈 balance = 0 + use_zero_first (ممكن اتجدد!)
      🥉 balance بين min_balance و prefer_balance (50-99)
      ❌ balance 1 إلى min_balance-1 → skip
    """
    skip_emails = skip_emails or set()

    # لو balance = None (مجهول) → حطه في أول الترتيب (ممكن 100!)
    def sort_key(acc):
        bal = acc.get("balance")    # None = مجهول
        if bal is None:
            return (0, 0)           # مجهول → فاحص أول (ممكن 100!)
        if bal >= cfg.prefer_balance:
            return (0, -bal)        # 🥇 أعلى رصيد
        if bal == 0 and cfg.use_zero_first:
            return (1, 0)           # 🥈 ممكن اتجدد
        if bal >= cfg.min_balance:
            return (2, -bal)        # 🥉 كفاية
        return (9, 0)               # ❌ skip

    sorted_accs = sorted(accounts, key=sort_key)

    # لو tie_break = "random" → خلط الحسابات داخل كل tier عشان مش دايماً نفس الحساب
    if getattr(cfg, "tie_break", "highest") == "random":
        import random
        # خلط داخل كل group بدون ما يكسر الترتيب بين الـ tiers
        from itertools import groupby
        tiers = []
        for _, grp in groupby(sorted_accs, key=lambda a: sort_key(a)[0]):
            g = list(grp)
            random.shuffle(g)
            tiers.extend(g)
        sorted_accs = tiers

    for acc in sorted_accs:
        email = acc.get("email", "")
        if email in skip_emails:
            continue
        # ✔ تخطي الحسابات غير النشطة
        if acc.get("active") is False:
            continue
            
        # ── T2: تخطي الحسابات اللي في فترة Cooldown ──
        cooldown_until = acc.get("cooldown_until", 0)
        if time.time() < cooldown_until:
            continue

        # ── التحقق من حجز الحساب الفوري (TTL Lease) ──
        reserved_until = acc.get("reserved_until", 0)
        if time.time() < reserved_until:
            continue
            
        cookies = acc.get("cookies", {})
        if not cookies or not cookies.get("session_id"):
            continue

        # ── Cooldown 29h: لو الحساب بعت رسالة خلال 29 ساعة → تخطاه ──
        last_sent = acc.get("last_sent_chat_sent")
        if last_sent:
            try:
                import datetime as _dt
                _last = _dt.datetime.fromisoformat(last_sent)
                _now  = _dt.datetime.now()
                _hours_passed = (_now - _last).total_seconds() / 3600
                
                # لو الحساب صفري، الكول داون 29 ساعة (أو balance_refresh_hours)
                # لو الحساب عادي، الكول داون هو account_cooldown_hours (ساعة مثلاً)
                is_zero = (acc.get("balance") == 0 or acc.get("status") == "zero_balance")
                if is_zero:
                    cooldown_hours = getattr(cfg, "balance_refresh_hours", 29)
                else:
                    cooldown_hours = getattr(cfg, "account_cooldown_hours", 1)
                
                if _hours_passed < cooldown_hours:
                    if cfg.show_debug:
                        p(Fore.CYAN, f"  ⏳ {email[:22]} — cooldown ({_hours_passed:.1f}h/{cooldown_hours}h)")
                    continue
            except Exception:
                pass

        acc = _maybe_refresh_balance(acc, cfg)

        bal = acc.get("balance")    # None = مجهول

        # ── فحص الرصيد المجهول من API ──
        if bal is None and cfg.check_unknown_balance:
            if cfg.show_debug:
                p(Fore.CYAN, f"  ❓ {email[:20]}... رصيد مجهول → بيفحص")
            real = check_balance(cookies)
            if real >= 0:
                acc["balance"] = real
                bal = real
            elif real == -2:
                bal = 0   # session منتهية — هيتعامل معها login logic تحت
            else:
                # FIX: لا تفترض الرصيد صفر لو فشل الفحص
                bal = acc.get("balance") or cfg.min_balance
        else:
            bal = bal if bal is not None else 0

        # تخطي الرصيد الضعيف (1 إلى min_balance-1)
        if 1 <= bal < cfg.min_balance:
            continue

        # فحص الرصيد الحقيقي من API — بس لو مكنش اتفحص قبل كده (عشان منعملش double API call)
        already_checked = (bal is not None and bal != 0)  # لو check_unknown_balance فحص → متفحصش تاني
        if cfg.check_balance_before and not already_checked:
            real_bal = check_balance(cookies)
            if real_bal == -2:
                # session منتهية — جرب login تلقائي
                password = acc.get("password", "")
                if password:
                    p(Fore.YELLOW, f"  🔄 {email} — session منتهية، بيعمل login...")
                    new_cookies = do_login(email, password)
                    if new_cookies:
                        acc["cookies"] = new_cookies
                        cookies = new_cookies
                        real_bal = check_balance(cookies)
                        p(Fore.GREEN, f"  ✅ Login نجح! رصيد: {real_bal}")
                    else:
                        p(Fore.RED, f"  ❌ Login فشل: {email}")
                        # ── FIX: أي لمسة = cooldown 29h (حتى لو فشل!) ──
                        _touch_ts = time.strftime("%Y-%m-%dT%H:%M:%S")
                        for _ai, _aitem in enumerate(accounts):
                            if _aitem.get("email") == email:
                                accounts[_ai]["last_sent_chat_sent"] = _touch_ts
                                break
                        save_accounts(accounts, cfg)   # ← احفظ فوراً على disk
                        continue
                else:
                    continue
            if real_bal >= 0:
                bal = real_bal
                acc["balance"] = real_bal
            if 1 <= bal < cfg.min_balance:
                if cfg.show_debug:
                    p(Fore.YELLOW, f"  ⏭️  {email} — رصيد {bal} < {cfg.min_balance} → skip")
                continue

        if cfg.show_balance:
            p(Fore.GREEN, f"  ✅ [PICK] {email} | 💰 {bal}")
        return acc, cookies

    return None


def lock_pick_and_reserve(cfg: Config, skip_emails: set = None) -> tuple[dict, dict] | None:
    """يختار ويحجز حساباً بشكل ذري باستخدام قفل الملف OS-level lock"""
    path = _cfg_path(cfg, cfg.accounts_file)
    try:
        with file_lock(path):
            accounts = load_accounts(cfg)
            result = pick_account(accounts, cfg, skip_emails)
            if not result:
                return None
            acc, cookies = result
            email = acc.get("email", "")
            # حجز الحساب لمدة 60 ثانية (Lease TTL)
            for i, aitem in enumerate(accounts):
                if aitem.get("email") == email:
                    accounts[i]["reserved_until"] = time.time() + 60.0
                    break
            save_accounts(accounts, cfg)
            return acc, cookies
    except Exception as e:
        p(Fore.YELLOW, f"  ⚠️ تعذر حجز حساب بسبب قفل الملف: {e}")
        return None


def release_account(email: str, cfg: Config, status_zero: bool = False, status_failed: bool = False):
    """يفك حجز الحساب في الملف بشكل آمن"""
    path = _cfg_path(cfg, cfg.accounts_file)
    try:
        with file_lock(path):
            accounts = load_accounts(cfg)
            for i, a in enumerate(accounts):
                if a.get("email") == email:
                    accounts[i]["reserved_until"] = 0  # فك الحجز فوراً
                    accounts[i]["last_sent_chat_sent"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    if status_zero:
                        accounts[i]["balance"] = 0
                        # Soft Cooldown/Disable
                        failures = accounts[i].get("exhaust_failures", 0) + 1
                        accounts[i]["exhaust_failures"] = failures
                        if failures >= 3:
                            accounts[i]["active"] = False
                        else:
                            accounts[i]["cooldown_until"] = time.time() + 900
                    break
            save_accounts(accounts, cfg)
    except Exception as e:
        p(Fore.RED, f"  ❌ فشل تحرير الحساب: {e}")


# ══════════════════════════════════════════════════════════════
# 💾 محادثات — تحميل / حفظ / قائمة / مسح / تصدير
# ══════════════════════════════════════════════════════════════
def _conv_path(cfg: Config) -> str:
    return _cfg_path(cfg, cfg.conv_file)


def load_convs(cfg: Config) -> dict:
    if not getattr(cfg, "save_to_json", False):
        return {}
    try:
        return json.loads(pathlib.Path(_conv_path(cfg)).read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_convs(convs: dict, cfg: Config):
    if not getattr(cfg, "save_to_json", False):
        return
    path = _conv_path(cfg)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(convs, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def update_conversation(cfg, conv_name, email, question, user_msg_id, answer, asst_msg_id, project_id):
    """بيحفظ الرسالة + الرابط في المحادثة — دي القلب بتاع النظام كله"""
    if not getattr(cfg, "save_to_json", False):
        return {}
    
    convs = load_convs(cfg)
    now = time.strftime("%Y-%m-%dT%H:%M:%S")  # التاريخ بالثانية عشان نعرف كل رسالة امتى

    # لو المحادثة دي مش موجودة → اعمل واحدة جديدة
    if conv_name not in convs:
        convs[conv_name] = {
            "account": email,
            "created_at": now,
            "urls": [],       # ← هنا بنحفظ آخر 10 روابط
            "messages": [],
        }

    conv = convs[conv_name]
    conv["updated_at"] = now    # آخر تحديث (sent OR created)
    conv["sent_at"] = now       # تحديداً — آخر وقت بيعت فيه رسالة (مختلف عن created_at)
    conv["account"] = email
    conv["project_id"] = project_id  # آخر project_id دايماً

    # ── حفظ الرابط في urls[] ──
    # لو فيه project_id → يبقى فيه رابط نحفظه
    if project_id:
        url = f"https://www.genspark.ai/autopilotagent_viewer?id={project_id}"
        urls_list = conv.setdefault("urls", [])

        # شوف لو الـ project_id ده موجود قبل كده → حدّث العداد بس
        existing = next((u for u in urls_list if u["project_id"] == project_id), None)
        if existing:
            existing["msg_count"] = existing.get("msg_count", 0) + 1
            existing["last_used"] = now  # آخر مرة استخدمناه
        else:
            # رابط جديد → ضيفه في الآخر
            urls_list.append({
                "project_id": project_id,
                "url": url,
                "created_at": now,                # امتى اتعمل — بالثانية
                "msg_count": 1,                   # عدد الرسايل في الرابط ده
                "first_question": question[:80],  # أول سؤال عشان تعرف المحادثة
                "owner_email": email,             # ← FIX: صاحب الـ project =الحساب اللي عمله
            })

        # احتفظ بآخر max_urls بس (الافتراضي 10)
        conv["urls"] = urls_list[-cfg.max_urls:]
        conv["active_url"] = url  # الرابط النشط — ده اللي بيتفتح

    # ── حفظ الرسايل — بس لو مش وضع توفير الرصيد ──
    if cfg.cli_history_max != -1:
        msgs = conv.setdefault("messages", [])
        msgs.append({"role": "user", "id": user_msg_id, "content": question})
        msgs.append({"role": "assistant", "id": asst_msg_id, "content": answer})
    else:
        conv["messages"] = []  # وضع توفير → رابط فقط بدون رسايل

    # ── FIX: حفظ source_entry_url عشان نعرف المحادثة بدأت من أين ──
    if cfg.entry_url:
        conv["source_entry_url"] = cfg.entry_url.strip()

    save_convs(convs, cfg)
    return conv


def list_conversations(cfg: Config):
    """بيعرض كل المحادثات المحفوظة — عشان تعرف عندك ايه"""
    convs = load_convs(cfg)
    if not convs:
        p(Fore.YELLOW, "  📭 مفيش محادثات محفوظة")
        return
    p(Fore.CYAN + Style.BRIGHT, f"\n  📚 المحادثات ({len(convs)}):\n")
    for name, cv in convs.items():
        msgs = cv.get("messages", [])
        n_user = len([m for m in msgs if m.get("role") == "user"])
        urls = cv.get("urls", [])
        acct = (cv.get("account") or "?")[:25]
        updated = cv.get("updated_at", "?")
        active = cv.get("active_url", "—")
        p(Fore.WHITE, f"  📝 [{name}]")
        p(Fore.CYAN, f"     💬 {n_user} رسالة | 🔗 {len(urls)} روابط | 📧 {acct} | 📅 {updated}")
        if active != "—":
            p(Fore.GREEN, f"     ↳ آخر رابط: {active}")


def list_urls(cfg: Config):
    """بيعرض كل الروابط المحفوظة — عشان تقدر تفتح أي واحد"""
    convs = load_convs(cfg)
    found = False
    for name, cv in convs.items():
        urls = cv.get("urls", [])
        if not urls:
            continue
        found = True
        p(Fore.CYAN + Style.BRIGHT, f"\n  📂 [{name}] ({len(urls)} روابط):")
        for i, u in enumerate(urls, 1):
            # بنعرض: الرقم + التاريخ + عدد الرسايل + أول سؤال + الرابط
            q_preview = u.get("first_question", "?")[:40]
            p(Fore.WHITE, f"  [{i:02d}] 📅 {u['created_at']} | 💬 {u.get('msg_count', 0)} | {q_preview}")
            p(Fore.GREEN, f"       🔗 {u['url']}")
    if not found:
        p(Fore.YELLOW, "  📭 مفيش روابط محفوظة")


def pick_url(cfg: Config, conv_name: str = None) -> str | None:
    """بيعرض آخر 10 روابط ويخليك تختار — مرونة!"""
    convs = load_convs(cfg)
    conv_name = conv_name or cfg.conv_name
    if conv_name not in convs:
        p(Fore.RED, f"  ❌ [{conv_name}] مش موجودة")
        return None
    urls = convs[conv_name].get("urls", [])
    if not urls:
        p(Fore.YELLOW, "  📭 مفيش روابط — هنبدأ محادثة جديدة")
        return None

    # اعرض كل الروابط المحفوظة
    p(Fore.CYAN + Style.BRIGHT, f"\n  🔗 آخر {len(urls)} روابط [{conv_name}]:\n")
    for i, u in enumerate(urls, 1):
        q_preview = u.get("first_question", "?")[:40]
        p(Fore.WHITE, f"  [{i}] 📅 {u['created_at']} | 💬 {u.get('msg_count', 0)} | {q_preview}")
        p(Fore.CYAN, f"      {u['url']}")

    # المستخدم يختار — Enter = آخر واحد (الافتراضي)
    try:
        choice = input(f"\n  اختار رقم (Enter = آخر واحد): ").strip()
    except (EOFError, KeyboardInterrupt):
        return urls[-1]["project_id"]

    if not choice:
        return urls[-1]["project_id"]  # آخر رابط
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(urls):
            p(Fore.GREEN, f"  ✅ اخترت: {urls[idx]['url']}")
            return urls[idx]["project_id"]
    except ValueError:
        pass
    # لو اختيار غلط → آخر واحد
    p(Fore.YELLOW, "  ⚠️ اختيار مش صح — هنستخدم آخر رابط")
    return urls[-1]["project_id"]


def _extract_project_id(url_or_id: str) -> str:
    """بيستخرج project_id من URL كامل أو من الـ ID لوحده"""
    # لو URL كامل → استخرج الـ id
    if "genspark.ai" in url_or_id and "id=" in url_or_id:
        import urllib.parse
        parsed = urllib.parse.urlparse(url_or_id)
        params = urllib.parse.parse_qs(parsed.query)
        return params.get("id", [url_or_id])[0]
    # لو project_id لوحده
    return url_or_id.strip()


def clear_conversation(cfg: Config, name: str):
    """بيمسح محادثة بالاسم — خلي بالك دي مش بترجع!"""
    convs = load_convs(cfg)
    if name in convs:
        del convs[name]
        save_convs(convs, cfg)
        p(Fore.GREEN, f"  🗑️ تم مسح محادثة [{name}]")
    else:
        p(Fore.RED, f"  ❌ مفيش محادثة اسمها [{name}]")


def export_conversation(cfg: Config, name: str):
    """بيصدّر المحادثة كملف markdown — عشان تقراها أو تشاركها"""
    convs = load_convs(cfg)
    if name not in convs:
        p(Fore.RED, f"  ❌ مفيش محادثة [{name}]")
        return
    cv = convs[name]
    out = f"# 💬 محادثة: {name}\n\n"
    out += f"- **Project ID:** {cv.get('project_id', '?')}\n"
    out += f"- **الحساب:** {cv.get('account', '?')}\n"
    # لو فيه روابط → اعرضهم
    urls = cv.get("urls", [])
    if urls:
        out += f"\n### 🔗 الروابط ({len(urls)})\n\n"
        for u in urls:
            out += f"- [{u['created_at']}]({u['url']}) | 💬 {u.get('msg_count', 0)}\n"
    out += "\n---\n\n"
    for msg in cv.get("messages", []):
        role = "👤 **أنت**" if msg["role"] == "user" else "🤖 **Genspark**"
        out += f"### {role}\n\n{msg.get('content', '')}\n\n---\n\n"
    export_file = _cfg_path(cfg, f"conv_{name}.md")
    pathlib.Path(export_file).write_text(out, encoding="utf-8")
    p(Fore.GREEN, f"  📄 تم التصدير: {export_file}")


# ══════════════════════════════════════════════════════════════
# 🔍 Fetch Project Messages — يجيب رسايل المحادثة من السيرفر
# ══════════════════════════════════════════════════════════════
def rehydrate_nuxt(raw: list, idx: int, depth: int = 0) -> any:
    """فك تشفير __NUXT_DATA__"""
    if depth > 50 or idx < 0 or idx >= len(raw): return None
    item = raw[idx]
    if item is None or isinstance(item, (bool, str, int, float)): return item
    if isinstance(item, list):
        if len(item) == 2 and isinstance(item[0], str) and item[0] in ("ShallowReactive", "Reactive", "Ref", "ShallowRef"):
            return rehydrate_nuxt(raw, item[1], depth + 1)
        if len(item) >= 1 and isinstance(item[0], str) and item[0] == "Set":
            return []
        return [rehydrate_nuxt(raw, el, depth + 1) for el in item if isinstance(el, int)]
    if isinstance(item, dict):
        result = {}
        for key, val_idx in item.items():
            result[key] = rehydrate_nuxt(raw, val_idx, depth + 1) if isinstance(val_idx, int) else val_idx
        return result
    return item

def fetch_project_messages(project_id: str, cookies: dict, cfg: "Config" = None) -> list:
    """
    يجيب الرسايل القديمة من /agents?id=XXX (Public Viewer Viewer)
    عشان نتخطى قيد الـ Ownership بتاع /api/user/project_detail اللي بيرفض حساب تاني!
    """
    if not project_id:
        return []
    try:
        from curl_cffi import requests as cffi
        import re, json
        sess = cffi.Session(impersonate="chrome120")
        sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Referer": f"{GENSPARK}/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        for name, val in cookies.items():
            sess.cookies.set(name, val, domain="www.genspark.ai")

        r = sess.get(f"{GENSPARK}/agents?id={project_id}", timeout=30)
        if r.status_code != 200:
            if cfg and cfg.show_debug:
                p(Fore.YELLOW, f"  ⚠️ fetch_messages HTTP: {r.status_code}")
            return []

        match = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
        if not match:
            if cfg and cfg.show_debug: p(Fore.YELLOW, "  ⚠️ fetch_messages: لا يوجد NUXT_DATA")
            return []

        nuxt_raw = json.loads(match.group(1))
        data = rehydrate_nuxt(nuxt_raw, 1)

        proj_res = data.get("data", {}) if isinstance(data, dict) else {}
        if isinstance(proj_res, dict): 
            proj_res = proj_res.get("project", proj_res)
        
        proj_inner = proj_res.get("data", {}) if isinstance(proj_res, dict) else {}
        if not isinstance(proj_inner, dict):
            fallback_proj = data.get("project", {}) if isinstance(data, dict) else {}
            proj_inner = fallback_proj.get("data", fallback_proj) if isinstance(fallback_proj, dict) else {}

        session_state = proj_inner.get("session_state", {}) if isinstance(proj_inner, dict) else {}
        messages = session_state.get("messages", []) if isinstance(session_state, dict) else []
        
        # فلترة الرسايل لو جات بـ format غريب
        cleaned_msgs = [m for m in messages if isinstance(m, dict) and 'role' in m]

        if cfg and cfg.show_debug:
            p(Fore.CYAN, f"  📥 جاب {len(cleaned_msgs)} رسالة قديمة من NUXT_DATA")
            
        return cleaned_msgs
    except Exception as e:
        if cfg and cfg.show_debug:
            p(Fore.YELLOW, f"  ⚠️ fetch_messages error: {e}")
        return []  # [P12-E] إرجاع صريح — كانت ترجع None ضمنياً وتكسر من يتوقع list


def load_local_project_context(project_id: str) -> str:
    """
    تقوم بقراءة وتجميع سياق المشروع المحلي المسحوب مسبقاً بـ SandboxDownloader
    لضمان تعزيز ذاكرة الساندبوكس في الشات المفرّع الجديد بنسبة 100%
    """
    if not project_id:
        return ""
    try:
        import glob
        matches = glob.glob(f"downloaded_projects/proj_{project_id[:8]}*/webapp")
        if not matches:
            return ""
        local_dir = pathlib.Path(matches[0])
        summary = ""
        for rel in ["src/index.tsx", "public/static/app.js", "README.md"]:
            fpath = local_dir / rel
            if fpath.exists():
                summary += f"\n--- {rel} ---\n{fpath.read_text(encoding='utf-8', errors='ignore')[:800]}\n"
        return summary
    except Exception:
        return ""

def create_forked_project(project_id: str, cookies: dict, cfg: Config = None) -> str | None:
    """
    يقوم باستدعاء GET /api/continue_conversation?id=OLD_PID للحساب الجديد!
    يقوم سيرفر Genspark بإنشاء مشروع ساندبوكس مفرّع جديد بكامل الملفات والسجل،
    ويرجع 307 Redirect متضمناً الـ project_id الجديد في Location Header (/agents?id=NEW_PID)!
    """
    if not project_id:
        return None
    try:
        from curl_cffi import requests as cffi
        sess = cffi.Session(impersonate="chrome120")
        sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Referer": f"{GENSPARK}/",
        })
        for name, val in cookies.items():
            sess.cookies.set(name, val, domain="www.genspark.ai")

        url = f"{GENSPARK}/api/continue_conversation?id={project_id}"
        r = sess.get(url, allow_redirects=False, timeout=20)
        if r.status_code in (301, 302, 307, 308):
            loc = r.headers.get("location", "")
            if loc and "/login" not in loc:
                new_pid = extract_project_id(loc)
                if new_pid:
                    if cfg and getattr(cfg, "show_debug", False):
                        p(Fore.GREEN, f"  🔀 [SERVER FORK SUCCESS]: تم تفريع ساندبوكس كامل على السيرفر للحساب الجديد: {new_pid[:16]}...")
                    return new_pid
        return None
    except Exception as e:
        if cfg and getattr(cfg, "show_debug", False):
            p(Fore.YELLOW, f"  ⚠️ create_forked_project error: {e}")
        return None

# ══════════════════════════════════════════════════════════════
# 🧠 دالة حقن عقود الموديلات ذاتية الاحتواء (Self-Contained Model Contracts)
# ══════════════════════════════════════════════════════════════
def apply_model_contract(payload: dict, model: str | None, msg_id: str | None = None) -> dict:
    """حقن الحقول المعتمدة لكل موديل بأمان تام وبدون أي اعتماديات خارجية"""
    m = str(model or "").strip().lower()
    
    # 1. الموديلات المحمية (لا يتم لمسها بالمسار العام)
    if m in ("gpt-5.5", "claude-opus-4-8"):
        p(Fore.YELLOW, f"  ⚠️ [ROUTING BUG] Protected model '{m}' reached generic apply_contract adapter")
        return payload

    # 2. العقود المعتمدة
    if m in ("claude-fable-5", "claude fable 5", "fable 5"):
        payload["models"] = ["gpt-4.1"]
        payload["use_model"] = "claude-fable-5"
        if msg_id:
            payload["client_message_id"] = msg_id
    elif m in ("claude-opus-5", "claude opus 5", "opus 5"):
        payload["models"] = ["claude-opus-5"]
        payload["use_model"] = "claude-opus-5"
        if msg_id:
            payload["client_message_id"] = msg_id
    elif m in ("claude-sonnet-5", "claude sonnet 5", "sonnet 5"):
        payload["models"] = ["claude-sonnet-5"]
        payload["use_model"] = "claude-sonnet-5"
        payload["ai_chat_model"] = "claude-sonnet-5"
        if msg_id:
            payload["client_message_id"] = msg_id
    elif m in ("gpt-5.6-sol", "gpt 5.6 sol", "gpt 5.6"):
        payload["models"] = ["gpt-5.6-sol"]
        payload["use_model"] = "gpt-5.6-sol"
        payload["ai_chat_model"] = "gpt-5.6-sol"
        if msg_id:
            payload["client_message_id"] = msg_id
    elif m in ("kimi-k3", "kimi k3", "k3"):
        payload["models"] = ["kimi-k3"]
        payload["use_model"] = "kimi-k3"
        payload["ai_chat_model"] = "kimi-k3"
        if msg_id:
            payload["client_message_id"] = msg_id
    else:
        payload["models"] = [model] if model else ["claude-fable-5"]

    return payload


# ══════════════════════════════════════════════════════════════
# 💬 إرسال رسالة — curl_cffi + SSE Streaming
# ══════════════════════════════════════════════════════════════
def _read_stream_body(resp, limit: int = 2000) -> str:
    """يقرأ جسم استجابة مفتوحة بوضع stream=True بأمان (لرسائل الأخطاء فقط)"""
    try:
        chunks, total = [], 0
        for ch in resp.iter_content():
            if not ch:
                continue
            chunks.append(ch)
            total += len(ch)
            if total >= limit:
                break
        return b"".join(chunks).decode("utf-8", errors="replace")
    except Exception:
        return ""


def send_chat(
    cookies: dict,
    question: str,
    email: str = "",
    project_id: str | None = None,
    history: list | None = None,
    cfg: Config = None,
    ticket_file=None,  # ← ملف مفتوح للكتابة اللحظية (أو None)
    fork_project_id: str | None = None,  # ← ID المشروع القديم عشان نعمل منه Fork
    on_project_start_callback=None,  # 🎯 Callback اختياري يُستدعى فور التقاط project_start
) -> tuple[str | None, str | None, str | None]:

    """
    يبعت رسالة لـ Genspark
    يرجع: (answer_text, project_id, assistant_msg_id)
    لو ticket_file موجود → الرد بيتكتب لحظي في الملف + Terminal
    """
    cfg = cfg or Config()
    from curl_cffi import requests as cffi

    hr()
    p(Fore.CYAN, f"  📧 {email or 'unknown'}")
    p(Fore.WHITE, f"  💬 {question[:80]}{'...' if len(question) > 80 else ''}")
    if project_id:
        p(Fore.YELLOW, f"  🔗 تكملة: {project_id[:16]}...")
    elif fork_project_id:
        p(Fore.YELLOW, f"  🔀 Fork من محادثة قديمة: {fork_project_id[:16]}...")
    print()

    user_msg_id = str(uuid.uuid4())
    history = history or []
    _is_continue = bool(project_id or fork_project_id)  # True = تكملة محادثة، False = شات جديد

    # ── تقليص الـ History توفيراً للرصيد (Tokens) ──
    limit = getattr(cfg, "cli_history_max", -1)
    if limit == -1:
        if _is_continue:
            history = []
            if getattr(cfg, "show_debug", False):
                p(Fore.YELLOW, "  ✂️ تم إلغاء الـ History وإرسال سؤالك فقط (اعتماداً على الرابط لتوفير الرصيد)")
        else:
            # Seed Mode: New project with history from URL. Keep up to 10 messages.
            if len(history) > 10:
                history = history[-10:]
                if getattr(cfg, "show_debug", False):
                    p(Fore.YELLOW, "  ✂️ تم قص الـ History (Seed Mode) لآخر 10 رسائل")
    elif limit > 0:
        history = history[-limit:]
        if getattr(cfg, "show_debug", False):
            p(Fore.YELLOW, f"  ✂️ تم قص الـ History لآخر {limit} رسالة")

    # بناء الرسائل — بفورمات عينه مطابقة للـ API (مش "مش مطلوب" — دي بتسبب CREDIT_EXHAUSTED!)
    _NULL_MSG_FIELDS = {
        "action": None, "recommend_actions": None, "is_prompt": False,
        "render_template": None, "session_state": None,
        "system_reminder": None, "message_type": None,
        "tool_calls": None, "tool_call_id": None, "project_id": None,
        "thinking_blocks": None, "response_id": None,
        "reasoning_id": None, "reasoning_encrypted_content": None,
        "reasoning_content": None, "cogen_id": None, "ctime": None,
    }
    new_msg = {
        "role": "user",
        "id": user_msg_id,
        "content": question,
        "pending": True,
        "sendStatus": "sending",
        **_NULL_MSG_FIELDS
    }

    # صلّح الـ history messages كمان لو ناقصة الـ null fields
    fixed_history = []
    for m in history:
        fm = {**_NULL_MSG_FIELDS, **m}  # null fields كـ base — والـ history يفوق عليه
        fixed_history.append(fm)

    all_messages = fixed_history + [new_msg]

    # ── UA Pool ديناميكي ──
    _ua = random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    ])
    _is_ff = "Firefox" in _ua
    _ver   = "124" if "124" in _ua else "130"
    sess = cffi.Session(impersonate="chrome120")
    _req_id = str(uuid.uuid4()).replace("-", "")
    sess.headers.update({
        "User-Agent": _ua,
        "Referer": f"{GENSPARK}/",
        "Origin": GENSPARK,
        "Content-Type": "application/json",
        "request-id": f"|{_req_id}.{_req_id[:16]}",
        "traceparent": f"00-{_req_id}-{_req_id[:16]}-01",
        **({} if _is_ff else {
            "sec-ch-ua": f'"Google Chrome";v="{_ver}", "Chromium";v="{_ver}", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": random.choice(['"Windows"', '"macOS"']),
        }),
    })
    for name, val in cookies.items():
        sess.cookies.set(name, val, domain="www.genspark.ai")

    # ── CF cookies (cf_clearance + c1 + c2) — مهمة لتجاوز Cloudflare ──
    if cfg.cf_cookies_file:
        _cf_path = pathlib.Path(cfg.cf_cookies_file)
        if not _cf_path.is_absolute():
            _cf_path = pathlib.Path(__file__).parent / _cf_path
        if _cf_path.exists():
            try:
                _cf = json.loads(_cf_path.read_text(encoding="utf-8"))
                for _cn in ("cf_clearance", "c1", "c2"):
                    if _cn in _cf and _cf[_cn]:
                        sess.cookies.set(_cn, _cf[_cn], domain="www.genspark.ai")
                if cfg.show_debug:
                    p(Fore.WHITE, f"  🛡️ CF cookies loaded ({len(_cf)-1} keys)")
            except Exception as _cfe:
                if cfg.show_debug:
                    p(Fore.YELLOW, f"  ⚠️ CF cookies error: {_cfe}")

    # ── FIX: Continue vs New Chat — المتصفح يستخدم إعدادات مختلفة! ──
    # _is_continue تم تعريفها مسبقاً بالأعلى

    if cfg.model in ("gpt-5.5", "claude-opus-4-8"):
        # ── payload مخصص لـ gpt-5.5 و claude-opus-4-8 متوافق 100% مع ask_proxy ──
        payload = {
            "ai_chat_model": cfg.model,
            "ai_chat_enable_search": cfg.request_web_knowledge,
            "ai_chat_disable_personalization": False,
            "use_moa_proxy": False,
            "moa_models": [],
            "writingContent": None,
            "type": "ai_chat",
            "project_id": project_id,
            "messages": all_messages,
            "user_s_input": question,
            "client_message_id": user_msg_id,
            "g_recaptcha_token": "",
            "is_private": cfg.is_private,
            "push_token": "",
            "session_state": {
                "steps": [],
                "messages": all_messages
            },
            "last_seen_event_index": -1,
            "chat_session_id": None
        }
        
        if _is_continue:
            target_fetch_id = project_id or fork_project_id
            old_msgs = fetch_project_messages(target_fetch_id, cookies, cfg)
            if old_msgs:
                _fork_limit = limit if limit > 0 else 10
                if len(old_msgs) > _fork_limit:
                    old_msgs = old_msgs[-_fork_limit:]
                context_messages = old_msgs + [new_msg]
                payload["session_state"]["messages"] = context_messages
                payload["messages"] = context_messages
                if project_id:
                    payload["force"] = True
                p(Fore.CYAN, f"  🧠 [5.5 Pro] Fetch & Forward: {len(old_msgs)} رسالة قديمة + رسالتك")
        elif history:
            context_messages = history + [new_msg]
            payload["session_state"]["messages"] = context_messages
            payload["messages"] = context_messages
            payload["force"] = True
    else:
        # ── الـ payload التقليدي لـ super_agent ──
        payload = {
            "models":                  ["gpt-4.1"] if cfg.model == "claude-fable-5" else [cfg.model],
            "run_with_another_model":  False,
            "request_web_knowledge":   cfg.request_web_knowledge,
            "speed_mode":              (not _is_continue) or bool(fork_project_id),     # Fork أو جديد = speed_mode(True)
            "use_webpage_capture_screen": bool(project_id),                             # Continue=true, New/Fork=false
            "use_python_workspace":    False,
            "dataframe_enhanced":      False,
            "enable_jupyter":          False,
            "custom_tools":            [],
            "unselected_custom_tools": [],
            "installed_custom_tools":  [],
            "writingContent":          None,
            "type":                    cfg.agent_type,
            "project_id":              project_id,
            "messages":                all_messages,
            "user_s_input":            question,
            "is_private":              cfg.is_private,
            "push_token":              "",
        }
        
        # ── inject model contract (use_model, ai_chat_model, client_message_id, models) ──
        payload = apply_model_contract(payload, cfg.model, user_msg_id)
        
        # ── Ultra Mode Injection ──
        if getattr(cfg, "use_ultra", False):
            if cfg.model.startswith("claude-opus"):
                payload["use_model"] = cfg.model
            else:
                payload["ultra_mode"] = True

        # ── Continue: Fetch & Forward ──
        if _is_continue:
            if project_id:
                payload["force"] = True
            
            target_fetch_id = project_id or fork_project_id
            old_msgs = fetch_project_messages(target_fetch_id, cookies, cfg)
            if old_msgs:
                _fork_limit = limit if limit > 0 else 10  # لو -1 خد آخر 10 بس كحد أقصى
                if len(old_msgs) > _fork_limit:
                    old_msgs = old_msgs[-_fork_limit:]
                    if getattr(cfg, "show_debug", False):
                        p(Fore.YELLOW, f"  ✂️ تم قص الرسايل القديمة لآخر {_fork_limit} عشان الرصيد")

                context_messages = old_msgs + [new_msg]
                payload["session_state"] = {"steps": [], "messages": context_messages}
                payload["messages"] = context_messages
                p(Fore.CYAN, f"  🧠 Fetch & Forward (Fork={bool(fork_project_id)}): {len(old_msgs)} رسالة قديمة + رسالتك")
            else:
                payload["session_state"] = {"steps": [], "messages": all_messages}
                if getattr(cfg, "show_debug", False):
                    p(Fore.YELLOW, "  ⚠️ مش لاقي رسايل قديمة → project جديد فاضي")
        elif history:
            context_messages = history + [new_msg]
            payload["session_state"] = {"steps": [], "messages": context_messages}
            payload["messages"] = context_messages
            payload["force"] = True
            if getattr(cfg, "show_debug", False):
                p(Fore.CYAN, f"  🧠 Seed Injection: {len(history)} رسالة قديمة + رسالتك (force=True)")
        else:
            payload["session_state"] = {"steps": [], "messages": all_messages}

    # ── [P12] حالة البث مهيأة قبل try — حتى لا يضيع project_id الملتقط عند أي انقطاع ──
    full_text = ""
    proj_id_new = project_id
    asst_msg_id = None
    proj_name = ""
    stream_interrupted = False
    _t_start = time.time()

    try:
        # ── ask_proxy دايماً: force:true بيحل الـ ownership mismatch ──
        # 🔥 stream=True إلزامي: بدونه curl_cffi تحجب الرد كاملاً حتى نهاية التوليد
        # ويصبح project_start والمعاينة الحية بعد الاكتمال بدلاً من الثانية الأولى (TSK-2701)
        # ⚡ [P12] timeout كـ tuple (اتصال، قراءة): مع stream=True تتحول داخل curl_cffi إلى
        # LOW_SPEED_TIME أي "مهلة خمول" — البث لا يُقطع طالما الخادم يرسل أحداثاً،
        # ويُقطع فقط لو صمت الخادم تماماً طوال المهلة (كان timeout السابق قطعاً كلياً
        # يقتل المشاريع الطويلة في المنتصف ويسبب TIMEOUT بلا سبب).
        _cfg_timeout = int(getattr(cfg, "timeout", 600) or 600)
        _connect_timeout = min(120, _cfg_timeout)
        _read_timeout = max(480, _cfg_timeout)
        r = sess.post(f"{GENSPARK}/api/agent/ask_proxy", json=payload, timeout=(_connect_timeout, _read_timeout), stream=True)
        if cfg.show_debug:
            p(Fore.CYAN, f"  📡 force={payload.get('force', False)} | continue={_is_continue}")
        if cfg.show_debug:
            p(Fore.WHITE, f"  ↳ HTTP {r.status_code}")

        if r.status_code == 401:
            p(Fore.RED, "  ❌ 401 — session منتهية!")
            try:
                r.close()
            except Exception:
                pass
            return "__SESSION_EXPIRED__", None, None
        if r.status_code not in (200, 204):
            _err_body = _read_stream_body(r)
            try:
                r.close()
            except Exception:
                pass
            # ━━━ ☒️ طبقة 4: UX أحسن — ميش بنطبع الخطأ الخام ━━━
            if r.status_code == 401:
                p(Fore.RED, "  ❌ 401 — session منتهية!")
                return None, None, None
            if r.status_code in (404, 410) and project_id:
                p(Fore.YELLOW, f"  ♻️ project مش موجود ({r.status_code}) → سيبدأ جديد تلقائي")
                return None, "__INVALID_PROJECT__", None
            if r.status_code == 500 and project_id:
                p(Fore.YELLOW, f"  ♻️ خطأ داخلي (500) — غالباً ownership mismatch → سيبدأ project جديد")
                return None, "__INVALID_PROJECT__", None
            p(Fore.RED, f"  ❌ Error {r.status_code}: {_err_body[:80]}")
            return None, None, None


        # ── تحليل SSE — تجميع صامت؛ الطباعة الكاملة تتم دفعة واحدة بعد الاكتمال (P12) ──
        asst_msg_id = str(uuid.uuid4())
        print(f"\r  ⏳ بيفكر...", end="", flush=True)  # مؤشر انتظار (بدون بث حي للترمنال)

        # 🔥 قراءة لحظية سطراً بسطر من البث الحي — ممنوع r.text نهائياً (يحجب حتى الاكتمال)
        # [P12] الاستهلاك اللحظي للـ callbacks وملف التذكرة فقط — الترمنال يطبع الرد كاملاً بعد الاكتمال.
        # [P12] أي انقطاع في البث (timeout/شبكة) لا يفقد project_id — نعيد الملتقط للاستئناف على نفس الشات.
        # 🛑 [P25] إلغاء تعاوني قهري: لو المنادي حقن cfg.cancel_event (threading.Event)
        # وضُبط أثناء البث → نقطع socket فوراً (r.close) — نفس آلية زر ⏹️ في الواجهة بالضبط
        # (HAR: لا يوجد endpoint إيقاف — القطع يحرر جانبنا فقط، وقد يكمل السيرفر التوليد داخلياً).
        _cancel_event = getattr(cfg, "cancel_event", None)
        user_cancelled = False
        try:
            for _raw_line in r.iter_lines():
                if _cancel_event is not None and _cancel_event.is_set():
                    user_cancelled = True
                    p(Fore.YELLOW, "  🛑 [P25] إلغاء من المستخدم — قطع بث ask_proxy فوراً")
                    break
                if isinstance(_raw_line, (bytes, bytearray)):
                    line = _raw_line.decode("utf-8", errors="replace")
                else:
                    line = str(_raw_line)
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw in ("[DONE]", ""):
                    continue
                try:
                    obj = json.loads(raw)
                    t = obj.get("type", "")

                    # streaming delta — تجميع صامت (بدون طباعة لحظية في الترمنال)
                    if t == "message_field_delta" and obj.get("field_name") == "content":
                        chunk = obj.get("delta", "")
                        full_text += chunk
                        # ── كتابة لحظية في ملف التذكرة فقط ──
                        if ticket_file:
                            ticket_file.write(chunk)
                            ticket_file.flush()

                    # non-streaming كامل
                    if t == "message_field" and obj.get("field_name") == "content":
                        fv = obj.get("field_value", "")
                        if fv and fv not in full_text:
                            full_text = fv

                    # نتيجة كاملة
                    if t == "message_result":
                        msg_obj = obj.get("message", {})
                        if isinstance(msg_obj, dict):
                            action = msg_obj.get("action", {}) or {}
                            if isinstance(action, dict) and action.get("type") == "ACTION_CREDIT_EXHAUSTED":
                                full_text = "__CREDIT_EXHAUSTED__"
                            elif msg_obj.get("content") and msg_obj.get("role") == "assistant" and not full_text:
                                full_text = msg_obj["content"]

                    # project_id
                    if t == "project_start" and obj.get("id"):
                        proj_id_new = obj["id"]
                        if on_project_start_callback and callable(on_project_start_callback):
                            try:
                                on_project_start_callback(proj_id_new)
                            except Exception as cb_err:
                                if getattr(cfg, "show_debug", False):
                                    p(Fore.YELLOW, f"  ⚠️ تنبيه الـ Callback غير المؤثر: {cb_err}")
                    if t == "project_field" and obj.get("field_name") == "id":
                        proj_id_new = obj.get("field_value", proj_id_new) or proj_id_new
                        if on_project_start_callback and callable(on_project_start_callback) and proj_id_new:
                            try:
                                on_project_start_callback(proj_id_new)
                            except Exception:
                                pass


                    # اسم المشروع
                    if t == "project_field" and obj.get("field_name") == "name":
                        proj_name = obj.get("field_value", proj_name)

                    # assistant message id
                    if t == "message_start" and obj.get("id"):
                        asst_msg_id = obj["id"]

                except Exception:
                    pass
        except Exception as stream_err:
            # ⚡ [P12] انقطاع البث (timeout/شبكة) لا يفقد المشروع:
            # نعيد ما التقطناه حتى يستأنف المنادي نفس project_id بدلاً من إنشاء شات جديد.
            stream_interrupted = True
            p(Fore.YELLOW, f"  ⚠️ انقطع البث قبل الاكتمال: {str(stream_err)[:100]}")

        # إغلاق البث بعد استهلاكه بالكامل (تحرير الاتصال)
        try:
            r.close()
        except Exception:
            pass

        # 🛑 [P25] إلغاء المستخدم — أولوية قصوى قبل أي تصنيف آخر
        if user_cancelled:
            return "__USER_CANCELLED__", proj_id_new, asst_msg_id

        # كريدت منتهية
        if full_text == "__CREDIT_EXHAUSTED__" or "insufficient for this request" in full_text.lower():
            p(Fore.RED, "  ❌ كريدت منتهية (من الـ API أو نصاً)!")
            return "__CREDIT_EXHAUSTED__", proj_id_new, None

        # [P12] انقطاع البث مع project_id حي → ماركر استئناف (ليس فشلاً ولا شات جديد)
        if stream_interrupted and proj_id_new:
            p(Fore.YELLOW, "  ♻️ سيتم الاستئناف على نفس المشروع (بدون إنشاء شات جديد)")
            return "__STREAM_INTERRUPTED__", proj_id_new, asst_msg_id

        if not full_text:
            p(Fore.YELLOW, "  ⚠️ مفيش نص في الرد!")
            return None, proj_id_new, None

        # ── [P12] الطباعة الكاملة دفعة واحدة بعد اكتمال الرد (لا live stream في الترمنال) ──
        _elapsed = time.time() - _t_start
        print()
        p(Fore.GREEN + Style.BRIGHT, "  ┌─ الرد ─────────────────────────────────────────┐")
        for ln in full_text.splitlines():
            p(Fore.WHITE, f"  │ {ln}")
        p(Fore.GREEN + Style.BRIGHT, "  └────────────────────────────────────────────────────┘")
        p(Fore.CYAN, f"  ⏱️ اخد {_elapsed:.1f} ثانية")
        if proj_name:
            p(Fore.CYAN, f"  📌 {proj_name}")

        return full_text, proj_id_new, asst_msg_id

    except Exception as e:
        p(Fore.RED, f"  ❌ خطأ: {e}")
        # [P12] لا نفقد project_id الملتقط — يسمح للمنادي بالاستئناف على نفس الشات
        return None, proj_id_new, None


# ══════════════════════════════════════════════════════════════
# 🌐 Share — يخلي المحادثة عامة
# ══════════════════════════════════════════════════════════════
def share_project(project_id: str, cookies: dict, show_debug: bool = False) -> str | None:
    """بيرجع الرابط لو نجح — مع debug كامل"""
    from curl_cffi import requests as cffi
    sess = cffi.Session(impersonate="chrome120")
    _ua2 = random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    ])
    sess.headers.update({
        "User-Agent": _ua2,
        "Content-Type": "application/json",
        "Origin": GENSPARK,
        "Referer": f"{GENSPARK}/",
    })
    for k, v in cookies.items():
        sess.cookies.set(k, v, domain="www.genspark.ai")

    try:
        r = sess.post(f"{GENSPARK}/api/project/update", json={
            "id": project_id, "is_private": False,
            "read_permissions": [], "write_permissions": [],
        }, timeout=10)
        try:
            full = r.json()
            data = full.get("data", {})
            if show_debug:
                p(Fore.CYAN, f"  [share] status={r.status_code} | is_private={data.get('is_private')} | keys={list(data.keys())}")
                p(Fore.CYAN, f"  [share] body={r.text[:500]}")
            pub = data.get("public_url") or data.get("share_url") or data.get("share_link") or data.get("share_token")
            if pub:
                return pub
            if data.get("is_private") is False:
                # HAR analysis: /autopilotagent_viewer?id=XXX is the public URL (no auth needed)
                # /agents?id=XXX redirects here but has server-side auth check first
                return f"{GENSPARK}/autopilotagent_viewer?id={project_id}"
        except Exception:
            if show_debug:
                p(Fore.CYAN, f"  [share] raw: {r.text[:400]}")
    except Exception as e:
        if show_debug:
            p(Fore.RED, f"  [share] err: {e}")
    return None


def _do_auto_share(cfg: Config, conv_name: str, project_id: str, cookies: dict) -> str | None:
    """يقوم بعمل Share تلقائي ويطبع الرابط العام بلون بينك فاقع في آخر رسالة بالترمنال"""
    if not project_id or not cookies:
        return None

    # توليد رابط الشير العام
    shared_url = share_project(project_id, cookies, show_debug=getattr(cfg, "show_debug", False))
    public_url = shared_url or f"{GENSPARK}/autopilotagent_viewer?id={project_id}"

    # 🌸 طباعة الرابط العام بلون بينك نيون (Neon Pink) فاقع ومميز في آخر الترمنال 🌸
    pink_color = "\033[38;5;206m"
    bold_pink  = "\033[1;38;5;206m"
    reset_color = "\033[0m"

    print(f"\n{bold_pink}  💖 [رابط المحادثة العام - PUBLIC SHARE LINK]:{reset_color}")
    print(f"  {pink_color}{public_url}{reset_color}\n")

    return public_url






# ══════════════════════════════════════════════════════════════
# 📊 عرض حالة الحسابات
# ══════════════════════════════════════════════════════════════
def show_status(cfg: Config):
    """بيعرض كل الحسابات ورصيدهم"""
    accounts = load_accounts(cfg)
    if not accounts:
        p(Fore.RED, "  ❌ مفيش حسابات!")
        return
    p(Fore.CYAN + Style.BRIGHT, f"\n  📊 الحسابات ({len(accounts)}):\n")
    total_credits = 0
    active = expired = 0
    for i, acc in enumerate(accounts, 1):
        email = acc.get("email", "?")
        bal = acc.get("balance", "?")
        has_cookies = bool(acc.get("cookies", {}).get("session_id"))
        last = acc.get("last_sent_chat_sent", acc.get("last_updated", "—"))[:16]
        if has_cookies:
            if isinstance(bal, int) and bal >= cfg.prefer_balance:
                sign, color = "🟢", Fore.GREEN
            elif isinstance(bal, int) and bal >= cfg.min_balance:
                sign, color = "🟡", Fore.YELLOW
            elif bal == 0:
                sign, color = "🔵", Fore.CYAN
            else:
                sign, color = "🔴", Fore.RED
            active += 1
            if isinstance(bal, int):
                total_credits += bal
        else:
            sign, color = "❌", Fore.RED
            expired += 1
        p(color, f"  {sign} [{i:02d}] {email:<40} 💰 {str(bal):<5} 📅 {last}")
    print()
    hr()
    p(Fore.GREEN + Style.BRIGHT, f"  ✅ نشط: {active}  ❌ منتهي: {expired}  💰 مجموع: {total_credits}")

    # ── ملخص المحادثات ──
    convs = load_convs(cfg)
    if convs:
        total_urls = sum(len(cv.get("urls", [])) for cv in convs.values())
        total_msgs = sum(len([m for m in cv.get("messages", []) if m.get("role") == "user"]) for cv in convs.values())
        print()
        hr()
        p(Fore.CYAN + Style.BRIGHT, f"  💬 المحادثات: {len(convs)} | 📨 رسايل: {total_msgs} | 🔗 روابط: {total_urls}")
        for name, cv in convs.items():
            msgs = len([m for m in cv.get("messages", []) if m.get("role") == "user"])
            urls = len(cv.get("urls", []))
            active_url = cv.get("active_url", "")
            p(Fore.WHITE, f"    📝 [{name}] {msgs} رسايل | {urls} روابط")
            if active_url:
                p(Fore.GREEN, f"       ↳ {active_url}")


# ══════════════════════════════════════════════════════════════
# 💬 CLI Mode — محادثة تفاعلية مستمرة
# ══════════════════════════════════════════════════════════════
def cli_mode(cfg: Config):
    """وضع تفاعلي — كل رسالة بتتحفظ في نفس المحادثة"""
    p(Fore.CYAN + Style.BRIGHT, f"\n  💬 Genspark CLI | Model: {cfg.model}")
    p(Fore.CYAN, "  اكتب 'exit' للخروج | 'new' لمحادثة جديدة | 'urls' لعرض الروابط\n")

    accounts = load_accounts(cfg)
    if not accounts:
        p(Fore.RED, "  ❌ مفيش حسابات!")
        return

    conv_name = cfg.conv_name
    project_id = None
    history = []
    locked_email = None
    skip_emails = set()

    # ── Auto-Register في الخلفية ──
    reg_proc = _start_auto_register(cfg)

    # تحميل المحادثة الحالية لو موجودة — دايماً آخر رابط
    convs = load_convs(cfg)
    cv = {}  # default فاضي لو مفيش محادثة
    if conv_name in convs and cfg.persistent:
        cv = convs[conv_name]
        # آخر رابط مش أول رابط!
        urls = cv.get("urls", [])
        if urls:
            last_url = urls[-1]
            project_id = last_url["project_id"]
            # ━━━ FIX: نقرأ locked_email من صاحب الـ project (مش account عام!) ━━━
            # الـ owner_email = الحساب اللي عمل الـ project ده
            # كده نضمن إن نفس الحساب دايماً بيكمل نفس المشروع
            locked_email = last_url.get("owner_email") or cv.get("account")
        else:
            project_id = cv.get("project_id")
            locked_email = cv.get("account")
        # ── History: لو cli_history_max == -1 → متحملش رسايل قديمة (توفير رصيد) ──
        _saved_msgs = cv.get("messages", [])
        if cfg.cli_history_max == -1:
            history = []  # اعتمد على الرابط فقط — السيرفر عنده الشات
            p(Fore.GREEN, f"  ✂️ وضع توفير الرصيد: بيبعت سؤالك فقط (بدون history)")
        else:
            history = _saved_msgs
        active_url = cv.get("active_url", "")
        _msg_count = len(_saved_msgs) // 2
        p(Fore.YELLOW, f"  🔗 تكملة [{conv_name}] | {_msg_count} رسالة | 📧 {locked_email}")
        if active_url:
            p(Fore.GREEN, f"  ↳ {active_url}")

    # ── FIX: Entry URL Override — مقارنة URLs مش IDs ──
    if cfg.entry_url:
        current_entry = cfg.entry_url.strip()
        saved_entry = (cv.get("source_entry_url") or "").strip()

        if saved_entry == current_entry and project_id:
            # ✅ نفس الـ entry → كمّل على نفس المحادثة
            p(Fore.CYAN, f"  ✅ بيكمل على المحادثة المحفوظة: {project_id[:12]}...")

        elif not saved_entry and project_id:
            # ✅ حالة legacy (بيانات قديمة بدون source_entry_url): اربط entry الحالي بدون reset
            cv["source_entry_url"] = current_entry
            p(Fore.CYAN, f"  📎 ربط entry_url بالمحادثة الحالية (legacy)")

        else:
            # ✅ أول مرة أو entry اتغير → project_id = None (Genspark يولد محادثة جديدة)
            # ⚠️ مش بنحط entry_url ID كـ project_id — ده agent template مش محادثة (بيرجع 500!)
            project_id = None
            history = []
            locked_email = None
            if saved_entry and saved_entry != current_entry:
                p(Fore.YELLOW, f"  🔄 Entry URL اتغير → محادثة جديدة")
            else:
                p(Fore.CYAN, f"  🆕 أول محادثة — project_id=None → Genspark هيولد واحدة")


    while True:
        try:
            q = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
        except (EOFError, KeyboardInterrupt):
            p(Fore.YELLOW, "\n  ⛔ إلى اللقاء!")
            break
        if not q:
            continue
        if q.lower() in ("exit", "quit", "q"):
            p(Fore.YELLOW, "  👋 إلى اللقاء!")
            break
        if q.lower() == "new":
            conv_name = f"cli_{int(time.time())}"
            project_id = None
            history = []
            locked_email = None
            p(Fore.GREEN, f"  🆕 محادثة جديدة: [{conv_name}]")
            continue
        # عرض الروابط في الوضع التفاعلي
        if q.lower() == "urls":
            list_urls(cfg)
            continue
        # اختيار رابط محدد
        if q.lower() == "pick":
            picked = pick_url(cfg, conv_name)
            if picked:
                project_id = picked
                p(Fore.GREEN, f"  ✅ هنكمل الرابط اللي اخترته")
            continue

        # ━━━ اختيار الحساب وقفل الحجز فوراً ━━━
        result = lock_pick_and_reserve(cfg, skip_emails)
        if not result:
            p(Fore.RED, "  ❌ مفيش حساب متاح!")
            continue
        acc, cookies = result
        locked_email = acc.get("email", "")
        active_email = locked_email.strip().lower()

        # ━━━ pick_best_project: كل حساب بيكمل projectه الخاص ━━━
        # ✔ أي حساب يكمل آخر project موجود في urls[] — مفيش ownership
        if project_id:
            p(Fore.CYAN, f"  📧 {active_email[:22]} → يكمل {project_id[:12]}...")


        # ── Ticket — رقم التيكت يتحدد مبكراً, الحفظ بعد النجاح (Lazy Ticket) ──
        ticket_num = _get_next_ticket_num(cfg) if cfg.save_tickets else 0

        # فتح ملف للكتابة اللحظية
        _tf = None
        if cfg.save_tickets and cfg.save_realtime:
            d = _ticket_dir(cfg)
            base = _ticket_filename(cfg, "a", ticket_num)
            _tf_path = d / f"{base}.txt"
            _tf = open(_tf_path, "w", encoding="utf-8")

        try:
            answer, pid, asst_id = send_chat(
                cookies, q, acc.get("email", ""),
                project_id=project_id, history=history, cfg=cfg,
                ticket_file=_tf,
            )
        finally:
            if _tf:
                _tf.close()

        if answer == "__CREDIT_EXHAUSTED__":
            email_x = acc.get("email", "")
            refreshed = False

            # ── Auto-Refresh Session ──────────────────────────────
            if cfg.auto_refresh_on_exhausted and email_x:
                p(Fore.YELLOW, f"  ⚡ CREDIT_EXHAUSTED — بيجدد session لـ {email_x}...")
                new_cookies = _relogin_account(accounts, email_x, cfg)
                if new_cookies:
                    # حفظ الـ cookies الجديدة في الملف
                    save_accounts(accounts, cfg)
                    p(Fore.GREEN, "  ✅ Session اتجدد — بيحاول تاني...")
                    # حاول تاني بـ session الجديدة
                    try:
                        answer2, pid2, asst_id2 = send_chat(
                            new_cookies, q, email_x,
                            project_id=project_id, history=history, cfg=cfg,
                            ticket_file=None,
                        )
                        if answer2 and answer2 != "__CREDIT_EXHAUSTED__":
                            answer, pid, asst_id = answer2, pid2, asst_id2
                            acc["cookies"] = new_cookies
                            refreshed = True
                        else:
                            p(Fore.RED, "  ❌ لسه بيدّي CREDIT_EXHAUSTED بعد الـ refresh!")
                            # الكريدت خلص فعلاً → صفّر وشيل
                            for i, a in enumerate(accounts):
                                if a.get("email") == email_x:
                                    accounts[i]["balance"] = 0
                                    if cfg.mark_inactive_on_fail:
                                        accounts[i]["active"] = False
                                        p(Fore.YELLOW, f"  🔒 {email_x} → active=false (كريدت فعلاً خلص)")
                                    break
                            save_accounts(accounts, cfg)
                    except Exception as _e:
                        p(Fore.RED, f"  ❌ إرسال بعد refresh فشل: {_e}")

            if not refreshed:
                skip_emails.add(email_x)
                locked_email = None
                # امسح ملف الرد اللحظي لو المحاولة فشلت
                if _tf_path and _tf_path.exists():
                    try:
                        _tf_path.unlink()
                    except OSError:
                        pass
                _tf_path = None
                project_id = None
                history = []
                release_account(email_x, cfg, status_zero=True)
                p(Fore.YELLOW, "  🔄 بنجرب حساب تاني...")
                continue

            # لو الـ refresh نجح — اكمل تنفيذ الرد تحت

        if answer:
            user_msg_id = str(uuid.uuid4())
            project_id = pid or project_id
            # ── Fix: safe_asst_id واحد بس مش اتنين مختلفين ──
            safe_asst_id = asst_id or str(uuid.uuid4())
            update_conversation(
                cfg, conv_name, acc.get("email", ""), q,
                user_msg_id, answer, safe_asst_id,
                project_id or "",
            )
            # تحديث history للرسالة الجاية — بس لو مش وضع توفير الرصيد
            if cfg.cli_history_max != -1:
                history.append({"role": "user", "id": user_msg_id, "content": q})
                history.append({"role": "assistant", "id": safe_asst_id, "content": answer})
            # اعرض الرابط عشان تقدر تفتحه
            if cfg.show_url_after_send and project_id:
                # HAR: /autopilotagent_viewer?id= هو الـ public URL الصح (بدون auth)
                p(Fore.GREEN, f"  🔗 {GENSPARK}/autopilotagent_viewer?id={project_id}")
            # ── Auto-Share ذكي (مرة واحدة بس) ──
            _do_auto_share(cfg, conv_name, project_id or "", cookies)
            # ── Ticket — حفظ السؤال + الرد بعد النجاح فقط (Lazy Ticket) ──
            if cfg.save_tickets:
                _save_ticket_question(cfg, q, ticket_num)
                if not cfg.save_realtime:
                    _save_ticket_answer(cfg, answer, ticket_num)
            _cleanup_old_tickets(cfg)
            # تحديث الرصيد
            _update_balance(accounts, acc.get("email", ""), cookies, cfg)

        else:
            # ← فشل غير CREDIT_EXHAUSTED في CLI — جرب حساب تاني
            email_x = acc.get("email", "")
            p(Fore.RED, f"  ❌ فشل! ({email_x[:20]}) — بنجرب حساب تاني...")
            skip_emails.add(email_x)
            if _tf_path and _tf_path.exists():
                try:
                    _tf_path.unlink()
                except OSError:
                    pass
            _tf_path = None
            release_account(email_x, cfg, status_failed=True)
            result = lock_pick_and_reserve(cfg, skip_emails)
            if not result:
                p(Fore.RED, "  ❌ كل الحسابات فشلت! اكتب سؤال جديد")
                break
            acc, cookies = result
            locked_email = acc.get("email", "")
            p(Fore.GREEN, f"  ✅ تحول لـ {locked_email[:20]}")
            continue

    # ── لما الشات يخلص — وقف register ──
    _stop_auto_register(reg_proc)


# ══════════════════════════════════════════════════════════════
# 💰 جلب الرصيد الحقيقي من السيرفر
# ══════════════════════════════════════════════════════════════
def get_real_balance(cookies: dict) -> int:
    try:
        from curl_cffi import requests as cffi
        sess = cffi.Session(impersonate="chrome120")
        sess.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        for k, v in cookies.items():
            sess.cookies.set(k, v, domain="www.genspark.ai")
        rb = sess.get("https://www.genspark.ai/api/payment/get_credit_balance", timeout=25)
        if rb.status_code == 200 and rb.json().get("status") == 0:
            return rb.json().get("data", {}).get("balance", 0)
    except:
        pass
    return 0


# ══════════════════════════════════════════════════════════════
# 🔑 Re-Login تلقائي — 4 خطوات Azure B2C
# ══════════════════════════════════════════════════════════════
def _relogin_account(accounts: list, email: str, cfg: Config) -> dict | None:
    """
    يعمل re-login بالميل والباسورد → يرجع cookies جديدة أو None
    لو نجح → يحدّث cookies في الـ list (in-place)
    لو فشل وـ mark_inactive_on_fail=True → يحط active=false
    """
    import re as _re
    acc = next((a for a in accounts if a.get("email") == email), None)
    if not acc:
        return None
    password = acc.get("password", "")
    if not password:
        p(Fore.YELLOW, f"  ⚠️  مفيش باسورد للحساب {email} — مش ممكن re-login")
        return None

    p(Fore.CYAN, f"  🔑 Re-Login: {email}")
    from curl_cffi import requests as cffi
    sess = cffi.Session(impersonate="chrome120")
    sess.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
    try:
        r1 = sess.get(f"{GENSPARK}/api/login", allow_redirects=True, timeout=35)
        csrf_m = _re.search(r'"csrf"\s*:\s*"([^"]+)"', r1.text)
        tx_m   = _re.search(r'"transId"\s*:\s*"([^"]+)"', r1.text)
        if not csrf_m or not tx_m:
            raise ValueError("csrf/tx not found")
        csrf, tx = csrf_m.group(1), tx_m.group(1)

        r2 = sess.post(
            f"{B2C_BASE}/SelfAsserted",
            params={"tx": tx, "p": B2C_POLICY},
            data={"email": email, "password": password, "request_type": "RESPONSE"},
            headers={
                "x-csrf-token": csrf,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": str(r1.url), "Origin": LOGIN_HOST, "Accept": "application/json",
            },
            timeout=35,
        )
        if '"status":"200"' not in r2.text:
            raise ValueError(f"Login rejected: {r2.text[:80]}")

        r3 = sess.get(
            f"{B2C_BASE}/api/SelfAsserted/confirmed",
            params={"csrf_token": csrf, "tx": tx, "p": B2C_POLICY},
            allow_redirects=False, timeout=35,
        )
        auth_url = r3.headers.get("location", r3.headers.get("Location", ""))
        if not auth_url or "/api/auth" not in auth_url:
            raise ValueError("No redirect to /api/auth")

        sess.get(auth_url, allow_redirects=True, timeout=35)
        new_cookies = dict(sess.cookies)
        if "session_id" not in new_cookies:
            raise ValueError("No session_id in cookies")

        # ✅ حدّث الـ cookies in-place باستخدام قفل الملف
        path = _cfg_path(cfg, cfg.accounts_file)
        try:
            with file_lock(path):
                fresh_accounts = load_accounts(cfg)
                for i, a in enumerate(fresh_accounts):
                    if a.get("email") == email:
                        fresh_accounts[i]["cookies"] = new_cookies
                        import time
                        fresh_accounts[i]["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                        real_bal = get_real_balance(new_cookies)
                        fresh_accounts[i]["balance"] = real_bal
                        fresh_accounts[i]["expires_in"] = 48
                        fresh_accounts[i]["status"] = "active"
                        fresh_accounts[i]["active"] = True
                        p(Fore.YELLOW, f"  [DEBUG] real_bal for {email} = {real_bal}")
                        if real_bal == 0:
                            fresh_accounts[i]["last_sent_chat_sent"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                            fresh_accounts[i]["status"] = "zero_balance"
                        break
                save_accounts(fresh_accounts, cfg)
        except Exception as lock_err:
            p(Fore.RED, f"  ❌ فشل حفظ التحديث لـ {email} بسبب قفل الملف: {lock_err}")
        p(Fore.GREEN, f"  ✅ Re-Login نجح! session: {new_cookies['session_id'][:20]}...")
        return new_cookies

    except Exception as e:
        p(Fore.RED, f"  ❌ Re-Login فشل لـ {email}: {e}")
        # تحديث الكارت ببيانات الفشل والوقت الفعلي لعدم المحاولة اللانهائية
        path = _cfg_path(cfg, cfg.accounts_file)
        try:
            with file_lock(path):
                fresh_accounts = load_accounts(cfg)
                for i, a in enumerate(fresh_accounts):
                    if a.get("email") == email:
                        fresh_accounts[i]["status"] = "refresh_failed"
                        fresh_accounts[i]["active"] = False
                        fresh_accounts[i]["expires_in"] = 48
                        import time
                        fresh_accounts[i]["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                        p(Fore.YELLOW, f"  🔒 {email} → تم تسجيل الفشل وكتابة كارت التحديث")
                        break
                save_accounts(fresh_accounts, cfg)
        except Exception as lock_err:
            p(Fore.RED, f"  ❌ فشل تسجيل الفشل لـ {email} بسبب قفل الملف: {lock_err}")
        return None


# ══════════════════════════════════════════════════════════════
# ⚙️ Session Warmup & Expiry Check (48h)
# ══════════════════════════════════════════════════════════════
def warmup_and_refresh_sessions(cfg: Config, count: int = 10) -> int:
    """
    يفحص الحسابات عند بدء التشغيل:
    - يمر على الحسابات ويحدد الحسابات التي:
      1. ليس لديها مفتاح 'last_updated' (ليس لديها كارت تحديث).
      2. أو مر على آخر تحديث لها >= 48 ساعة.
      3. أو ليس لديها cookies صالحة.
    - يقوم بتشغيل التجديد (Re-Login) لـ 10 حسابات منها بحد أقصى.
    - يحدث الكروت ببيانات فعلية (رصيد حقيقي، expires_in = 48، last_updated = الآن، إلخ).
    - يحفظ التحديثات ذرياً بعد كل حساب لمنع الفقد.
    """
    import datetime as _dt
    import time as _time
    accounts = load_accounts(cfg)
    if not accounts:
        return 0

    to_refresh = []
    now = _dt.datetime.now()

    for acc in accounts:
        email = acc.get("email", "")
        if not email:
            continue
        
        last_updated_str = acc.get("last_updated")
        cookies = acc.get("cookies", {})
        
        needs_refresh = False
        reason = ""
        
        if not last_updated_str:
            needs_refresh = True
            reason = "مفيش كارت تحديث (last_updated)"
        elif not cookies or "session_id" not in cookies:
            needs_refresh = True
            reason = "الكوكيز غير صالحة أو مفقودة"
        else:
            try:
                last_dt = _dt.datetime.fromisoformat(last_updated_str)
                hours_passed = (now - last_dt).total_seconds() / 3600
                threshold = acc.get("expires_in", 48)  # 48س هو الافتراضي المؤقت
                if hours_passed >= threshold:
                    needs_refresh = True
                    reason = f"مرت {hours_passed:.1f} ساعة على التجديد (أكبر من/يساوي {threshold}س)"
            except Exception:
                needs_refresh = True
                reason = "تنسيق تاريخ التحديث غير صالح"
                
        if needs_refresh:
            to_refresh.append((acc, reason))

    if not to_refresh:
        if cfg.show_debug:
            p(Fore.GREEN, "  ✅ كل الحسابات نشطة ومحدثة خلال الـ 48 ساعة الماضية.")
        return 0

    p(Fore.YELLOW + Style.BRIGHT, f"\n  ⚙️ [Session Warmup] تم العثور على {len(to_refresh)} حساب يحتاج لتحديث.")
    p(Fore.YELLOW, f"  🚀 سيتم معالجة أول {min(count, len(to_refresh))} حسابات بالترتيب 10/10...")

    refreshed_count = 0
    for acc, reason in to_refresh[:count]:
        email = acc.get("email", "")
        p(Fore.CYAN, f"\n  🔄 [{refreshed_count + 1}/{min(count, len(to_refresh))}] جاري تجديد: {email}")
        p(Fore.MAGENTA, f"    ↳ السبب: {reason}")
        
        # تشغيل relogin_account
        # relogin_account بيقوم بتحديث الحساب وحفظه ذرياً تلقائياً
        new_cookies = _relogin_account(accounts, email, cfg)
        
        if new_cookies:
            p(Fore.GREEN + Style.BRIGHT, f"    ✅ نجح التجديد للحساب {email}!")
        else:
            p(Fore.RED, f"    ❌ فشل تجديد الحساب {email} (تم تسجيل الفشل وكتابة الكارت).")
            
        refreshed_count += 1
        # تأخير بسيط بين الحسابات لمنع التداخل أو ضغط السيرفر
        _time.sleep(1.5)

    p(Fore.GREEN + Style.BRIGHT, f"\n  ✅ اكتملت عملية الـ Warmup! تم تجديد {refreshed_count} حسابات.")
    return refreshed_count


def _update_balance(accounts: list, email: str, cookies: dict, cfg: Config):
    """يحدث الرصيد في JSON بعد الإرسال مع إعادة التحميل لحماية المزامنة"""
    bal = check_balance(cookies)
    path = _cfg_path(cfg, cfg.accounts_file)
    try:
        with file_lock(path):
            # إعادة تحميل أحدث داتا طازجة من القرص
            fresh_accounts = load_accounts(cfg)
            for i, a in enumerate(fresh_accounts):
                if a.get("email") == email:
                    if bal >= 0:
                        fresh_accounts[i]["balance"] = bal
                    fresh_accounts[i]["last_sent_chat_sent"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    fresh_accounts[i]["reserved_until"] = 0  # فك الحجز فوراً
                    break
            save_accounts(fresh_accounts, cfg)
            if cfg.show_balance and bal >= 0:
                p(Fore.GREEN, f"  💰 رصيد بعد الإرسال: {bal}")
    except Exception as e:
        p(Fore.RED, f"  ❌ فشل تحديث الرصيد وحفظ الملف: {e}")


# ══════════════════════════════════════════════════════════════
# 🔀 نظام اختيار المحادثة — جديدة أم تكملة?
# ══════════════════════════════════════════════════════════════
def _ask_continue_or_new(conv_name: str, cv: dict, cfg: "Config") -> bool:
    """
    يسأل المستخدم: كمّل المحادثة القديمة ولا ابدأ جديدة?
    يرجع True = كمّل | False = جديد
    السلوك متحكم فيه من cfg:
      ask_new_default : "continue" | "new"    → القرار عند timeout
      ask_new_timeout : int (ثواني) | 0=أبدي  → كام ثانية ينتظر
    """
    import time
    msg_count = len(cv.get("messages", [])) // 2
    project_id = cv.get("project_id", "")
    urls = cv.get("urls", [])
    # آخر رابط محفوظ — من urls list أو من project_id مباشرة
    last_pid = (urls[-1]["project_id"] if urls else project_id) or ""
    last_pid_short = last_pid[:20] + "..." if last_pid else "?"

    default_is_continue = (cfg.ask_new_default == "continue")
    timeout = cfg.ask_new_timeout  # 0 = ينتظر للأبد

    hr()
    p(Fore.CYAN + Style.BRIGHT, f"  📂 عندك محادثة [{conv_name}] | {msg_count} رسالة")
    if last_pid:
        p(Fore.GREEN, f"  ↳ autopilotagent_viewer?id={last_pid_short}")
    print()
    p(Fore.YELLOW + Style.BRIGHT, "  اختار:")
    if default_is_continue:
        timeout_txt = f"{timeout}ث" if timeout > 0 else "∞"
        p(Fore.CYAN + Style.BRIGHT, f"    [Enter] = 🔗 كمّل المحادثة الموجودة (افتراضي — {timeout_txt})")
        p(Fore.GREEN,               "    [n]     = ✨ محادثة جديدة")
    else:
        timeout_txt = f"{timeout}ث" if timeout > 0 else "∞"
        p(Fore.GREEN + Style.BRIGHT, f"    [Enter] = ✨ محادثة جديدة (افتراضي — {timeout_txt})")
        p(Fore.CYAN,                 "    [c]     = 🔗 كمّل المحادثة الموجودة")
    hr()

    def _check_key(key: str) -> bool | None:
        """يرجع True/False أو None لو مش الأزرار المعروفة"""
        k = key.lower()
        if default_is_continue:
            if k in ('\r', '\n', ' ', ''):
                return True   # Enter = كمّل
            if k == 'n':
                return False  # n = جديد
        else:
            if k in ('\r', '\n', ' ', ''):
                return False  # Enter = جديد
            if k == 'c':
                return True   # c = كمّل
        return None  # مفتاح تاني → تجاهل وفضل في الـ loop

    try:
        import msvcrt
        for i in (range(timeout, 0, -1) if timeout > 0 else iter(int, 1)):
            if timeout > 0:
                msg = f"🔗 تكملة" if default_is_continue else f"✨ جديدة"
                print(f"\r  ⏳ {msg} بعد {i} ثانية... (اضغط {'n' if default_is_continue else 'c'} للتغيير)  ", end="", flush=True)
            else:
                msg = "🔗 كمّل" if default_is_continue else "✨ جديدة"
                print(f"\r  ⌨️ اضغط {'n=جديدة' if default_is_continue else 'c=تكملة'} أو Enter={msg}  ", end="", flush=True)
            deadline = time.time() + 1
            while time.time() < deadline:
                if msvcrt.kbhit():
                    key = msvcrt.getwch()
                    result = _check_key(key)
                    if result is not None:
                        print()
                        if result:
                            p(Fore.CYAN + Style.BRIGHT, "  🔗 تمام — بنكمل المحادثة الموجودة!")
                        else:
                            p(Fore.GREEN + Style.BRIGHT, "  ✨ بنبدأ محادثة جديدة!")
                        return result
                time.sleep(0.05)

        # انتهى الـ timeout
        print()
        if default_is_continue:
            p(Fore.CYAN + Style.BRIGHT, f"  🔗 timeout — بنكمل المحادثة الموجودة!")
            return True
        else:
            p(Fore.GREEN + Style.BRIGHT, f"  ✨ timeout — محادثة جديدة!")
            return False

    except ImportError:
        # Non-Windows
        hint = "Enter=تكملة / n=جديدة" if default_is_continue else "Enter=جديدة / c=تكملة"
        try:
            choice = input(f"  اختارك ({hint}): ").strip().lower()
            if default_is_continue:
                if choice == 'n':
                    p(Fore.GREEN, "  ✨ محادثة جديدة!")
                    return False
                p(Fore.CYAN, "  🔗 تكملة!")
                return True
            else:
                if choice == 'c':
                    p(Fore.CYAN, "  🔗 تكملة!")
                    return True
                p(Fore.GREEN, "  ✨ محادثة جديدة!")
                return False
        except (EOFError, KeyboardInterrupt):
            pass
        # default
        return default_is_continue



# ══════════════════════════════════════════════════════════════
# 🚀 MAIN
# ══════════════════════════════════════════════════════════════
def main():
    # ── Jitter عشوائي لمنع هجمات التوازي الأولي ──
    import random
    time.sleep(random.uniform(0.1, 3.0))

    cfg = Config()

    # ── طبق إعدادات المستخدم من أعلى الملف ─────────────────────
    # الثوابت فوق دي بتنتقل تلقائياً للـ cfg هنا
    cfg.use_ultra   = ULTRA_MODE
    cfg.min_balance = MIN_BALANCE
    cfg.auto_share  = AUTO_SHARE
    cfg.show_debug  = SHOW_DEBUG
    # ملحوظة: لو بعتلك --ultra في الأمر، هيكسب على USER SETTINGS دي (CLI دايما اللي بيكسب)

    ap = argparse.ArgumentParser(description="💬 Genspark Chat v4.3")
    ap.add_argument("question", nargs="?", default=None, help="السؤال")
    ap.add_argument("--q", type=str, default=None, help="السؤال (بديل)")
    ap.add_argument("--conv", type=str, default=None, help="اسم المحادثة")
    ap.add_argument("--new", action="store_true", help="محادثة جديدة")
    ap.add_argument("--cli", action="store_true", help="وضع تفاعلي مستمر")
    ap.add_argument("--list-convs", action="store_true", help="عرض المحادثات")
    ap.add_argument("--clear-conv", type=str, default=None, help="مسح محادثة")
    ap.add_argument("--export", type=str, default=None, help="تصدير محادثة (markdown)")
    ap.add_argument("--status", action="store_true", help="حالة الحسابات")
    ap.add_argument("--share", action="store_true", help="رابط عام")
    ap.add_argument("--email", type=str, default=None, help="حساب محدد")
    ap.add_argument("--min-balance", type=int, default=None, help="أقل رصيد")
    ap.add_argument("--model", type=str, default=None, help="الموديل")
    ap.add_argument("--debug", action="store_true", help="إظهار debug")
    # ── أوامر الروابط الجديدة ──
    ap.add_argument("--url", type=str, default=None, help="رابط محدد تكمل بيه (URL كامل أو project_id)")
    ap.add_argument("--pick", action="store_true", help="اختار من آخر 10 روابط")
    ap.add_argument("--urls", action="store_true", help="عرض كل الروابط المحفوظة")
    ap.add_argument("--ultra", action="store_true", help="تفعيل مود Ultra (1M Context)")
    # ── أوامر التيكتات ──
    ap.add_argument("--file", type=str, default=None, help="ملف يتبعت كسؤال (txt, har, py, أي نوع)")
    args = ap.parse_args()

    # تحديث Config من CLI
    if getattr(args, "ultra", False):
        cfg.use_ultra = True

    if args.min_balance is not None:
        cfg.min_balance = args.min_balance
    if args.model:
        cfg.model = args.model
    if args.debug:
        cfg.show_debug = True

    # ── BANNER ──
    print()
    p(Fore.GREEN + Style.BRIGHT, "╔══════════════════════════════════════════════════════╗")
    p(Fore.GREEN + Style.BRIGHT, f"║   💬 Genspark Chat v4.1  |  {cfg.model:<22} ║")
    p(Fore.GREEN + Style.BRIGHT, "╚══════════════════════════════════════════════════════╝")

    # ── Session Warmup & Expiry Check (48h) ──
    # يفحص الحسابات المنتهية (مرت 48 ساعة) أو التي ليس لها كارت ويقوم بتحديثها
    warmup_and_refresh_sessions(cfg, count=10)

    # ── أوامر بدون سؤال ──
    if args.list_convs:
        list_conversations(cfg)
        return
    if args.urls:           # ← جديد: عرض كل الروابط
        list_urls(cfg)
        return
    if args.pick:           # ← جديد: اختار رابط
        picked = pick_url(cfg, args.conv or cfg.conv_name)
        if picked:
            p(Fore.GREEN, f"  ✅ اخترت: {GENSPARK}/autopilotagent_viewer?id={picked}")
        return
    if args.clear_conv:
        clear_conversation(cfg, args.clear_conv)
        return
    if args.export:
        export_conversation(cfg, args.export)
        return
    if args.status:
        show_status(cfg)
        return
    if args.share and not args.question and not args.q:
        # ── --share بدون سؤال → شارك آخر محادثة ──
        conv_name_s = args.conv or cfg.conv_name
        convs_s = load_convs(cfg)
        cv_s = convs_s.get(conv_name_s, {})
        pid_s = cv_s.get("project_id", "")
        if not pid_s:
            p(Fore.RED, f"  ❌ مفيش محادثة محفوظة في [{conv_name_s}]")
            return
        # لازم نجيب cookies من حساب نشط
        accounts_s = load_accounts(cfg)
        result_s = pick_account(accounts_s, cfg)
        if not result_s:
            p(Fore.RED, "  ❌ مفيش حساب متاح للمشاركة!")
            return
        _, cookies_s = result_s
        p(Fore.YELLOW, f"  🌐 بيعمل رابط عام لـ [{conv_name_s}]...")
        url_s = share_project(pid_s, cookies_s, show_debug=cfg.show_debug)
        if url_s:
            p(Fore.GREEN + Style.BRIGHT, f"  🔗 {url_s}")
            convs_s[conv_name_s]["public_url"] = url_s
            save_convs(convs_s, cfg)
        else:
            p(Fore.RED, "  ❌ المشاركة فشلت")
        return
    if args.cli:

        if args.conv:
            cfg.conv_name = args.conv
        cli_mode(cfg)
        return

    # ── السؤال (من CLI أو من ملف) ──
    question = args.question or args.q
    if not question:
        try:
            val = (_DIR / "chat_send.txt").read_text(encoding="utf-8", errors="replace").strip()
            if val: question = val
        except Exception:
            pass
    # لو في --file → اقرا الملف وبعته كسؤال
    if args.file:
        fp = pathlib.Path(args.file)
        if not fp.exists():
            p(Fore.RED, f"  ❌ الملف مش موجود: {args.file}")
            return
        file_content = fp.read_text(encoding="utf-8", errors="replace")
        if question:
            question = f"{question}\n\n─── محتوى {fp.name} ───\n{file_content}"
        else:
            question = file_content
        p(Fore.CYAN, f"  📄 تم تحميل {fp.name} ({len(file_content)} حرف)")
    # ── لو مفيش سؤال خلي بال من input_file التلقائي ──
    if not question and cfg.input_file:
        auto_fp = _DIR / cfg.input_file
        if auto_fp.exists():
            auto_content = auto_fp.read_text(encoding="utf-8", errors="replace").strip()
            if auto_content:
                question = auto_content
                p(Fore.CYAN, f"  📂 تم تحميل من {cfg.input_file} ({len(auto_content)} حرف)")
    if not question:
        p(Fore.YELLOW, "\n  [*] اكتب سؤالك:")
        try:
            question = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
        except (EOFError, KeyboardInterrupt):
            return
    if not question:
        p(Fore.RED, "  ❌ مفيش سؤال!")
        return

    # ── تحميل ──
    accounts = load_accounts(cfg)
    if not accounts:
        p(Fore.RED, "  ❌ مفيش حسابات!")
        sys.exit(1)

    # ── 🔗 URL Mode: قراءة آخر رابط محفوظ عشان نكمل منه ──────────────────────────
    _url_mode_project_id = None  # الـ project_id اللي جاي من الـ URL Mode
    _url_mode_question   = question  # لحفظ السؤال في الـ JSON
    if USE_URL_MODE and not args.new:
        _last_entry = get_last_url(cfg)
        if _last_entry:
            _url_mode_project_id = _last_entry.get("project_id")
            p(Fore.CYAN, f"  🔗 URL Mode: بيكمل من {_url_mode_project_id[:16] if _url_mode_project_id else '?'}...")
        else:
            p(Fore.YELLOW, "  🆕 URL Mode: مفيش روابط محفوظة — سيبدأ شات جديد")

    # ── اسم المحادثة ───────────────────────────────────────────────────────
    # URL Mode له أولوية على always_new_chat — عشان الأسئلة تتسلسل فوق بعض
    if args.new or (getattr(cfg, "always_new_chat", False) and not _url_mode_project_id):
        # محادثة جديدة خالص
        conv_name = f"chat_{int(time.time())}"
        project_id = None
        history = []
        locked_email = None
        _do_fresh = False   # ← إصلاح #5: _do_fresh لازم تتعرّف دايماً
        _fresh_pid = None
        p(Fore.GREEN, f"  🆕 محادثة جديدة: [{conv_name}]")
    elif args.url:
        # → المستخدم حدد رابط معين يكمل بيه
        conv_name = args.conv or cfg.conv_name
        project_id = _extract_project_id(args.url)  # بيقبل URL كامل أو ID
        history = []
        locked_email = None
        _do_fresh = False
        _fresh_pid = None
        _url_mode_project_id = project_id  # استخدمه في الـ URL Mode كمان الـ CLI
        p(Fore.CYAN, f"  🔗 كمّل رابط محدد: {project_id[:16] if project_id else '?'}...")
    elif _url_mode_project_id:
        # → URL Mode نشط وعندنا رابط محفوظ — نكمل منه
        conv_name = args.conv or cfg.conv_name
        project_id = _url_mode_project_id
        history = []
        locked_email = None
        _do_fresh = False
        _fresh_pid = None
    else:
        conv_name = args.conv or cfg.conv_name
        project_id = None
        history = []
        locked_email = None

        # -- fresh_start check: لو True بس استُخدم قبل → اتصرف كـ False تلقائي --
        _do_fresh = cfg.fresh_start
        _fresh_pid = None   # جديد: هيخزن fresh_project_id لو محفوظ من قبل
        if cfg.fresh_start and cfg.persistent:
            _chk_convs = load_convs(cfg)
            if conv_name in _chk_convs and _chk_convs[conv_name].get("fresh_used"):
                _do_fresh = False
                _fresh_pid = _chk_convs[conv_name].get("fresh_project_id")  # جديد: Single Source of Truth

        # تحميل المحادثة السابقة — مع prompt تفاعلي للمستخدم
        if cfg.persistent and not _do_fresh:
            convs = load_convs(cfg)
            if conv_name in convs and convs[conv_name].get("project_id"):
                cv = convs[conv_name]
                # ← اسأل المستخدم (أو اتخطى لو auto_continue=True)
                if cfg.auto_continue or args.new:
                    _should_continue = not args.new  # auto_continue → كمّل | --new → جديد
                else:
                    _should_continue = _ask_continue_or_new(conv_name, cv, cfg)
                if _should_continue:
                    # ─── FIX: اختار project بتاع حساب عندنا — بأعلى رصيد أولاً ───
                    urls = cv.get("urls", [])
                    project_id = None
                    _all_accts = load_accounts(cfg)
                    # ترتيب بأعلى رصيد أولاً عشان ناخد أفضل حساب
                    _all_accts_sorted = sorted(
                        _all_accts,
                        key=lambda a: (a.get("balance") or 0),
                        reverse=True,
                    )
                    for _acct in _all_accts_sorted:
                        _email_try = (_acct.get("email") or "").strip().lower()
                        _found = pick_best_project(cv, _email_try)
                        if _found:
                            project_id = _found
                            locked_email = _acct.get("email")  # قفّل على أعلى رصيد
                            break
                    # لو مفيش project لأي حساب عندنا → None (Genspark يولد جديد)
                    if not project_id:
                        project_id = None
                        p(Fore.YELLOW, "  ℹ️ مفيش project لأي حساب محفوظ → سيبدأ محادثة جديدة")
                    history = cv.get("messages", [])  # ← دايماً نقرأ الـ history
                    _disp_url = (f"{GENSPARK}/autopilotagent_viewer?id={project_id}" if project_id else "")
                    p(Fore.YELLOW, f"  🔗 تكملة [{conv_name}] | {len(history)//2} رسالة")
                    if _disp_url:
                        p(Fore.GREEN, f"  ↳ {_disp_url}")
                else:
                    # ← جديد: امسح كل حاجة قديمة نهائياً
                    for _key in ("project_id", "urls", "public_url", "fresh_project_id",
                                 "fresh_used", "messages", "account", "active_url"):
                        convs[conv_name].pop(_key, None)
                    convs[conv_name]["messages"] = []  # ← إصلاح #4: setdefault يحتاج messages يكون list
                    save_convs(convs, cfg)
                    locked_email = None   # ← إصلاح #4: اضمن التناسق — accountاتمسحت، locked_emailكمان
                    p(Fore.GREEN, f"  ✨ محادثة جديدة — تم مسح كل الروابط والرسايل القديمة")
        elif _do_fresh:
            p(Fore.CYAN, f"  🆕 fresh_start — شات جديد [{conv_name}] (هيكمل تلقائي بعد الرد)")

    # ── FIX: Entry URL Override في run_once — مقارنة URLs مش IDs ──
    # (نفس المنطق في cli_mode عشان يكمل المحادثة صح بدون reset كل مرة)
    if cfg.entry_url and not args.new and not args.url:
        _cur_entry = cfg.entry_url.strip()
        _convs_eu = load_convs(cfg)
        _cv_eu = _convs_eu.get(conv_name, {})
        _saved_entry = (_cv_eu.get("source_entry_url") or "").strip()

        if _saved_entry == _cur_entry and project_id:
            # ✅ نفس الـ entry_url + عندنا project → كمّل
            p(Fore.CYAN, f"  ✅ entry_url مطابق → بيكمل: {project_id[:12]}...")

        elif not _saved_entry and project_id:
            # ✅ legacy data (بدون source_entry_url) → اربط بدون reset
            pass  # كمّل عادي — update_conversation هيحفظ الـ entry_url بعدين

        else:
            # 🆕 أول مرة أو entry_url اتغير → ابدأ محادثة جديدة
            project_id = None
            history = []
            locked_email = None
            if _saved_entry and _saved_entry != _cur_entry:
                p(Fore.YELLOW, f"  🔄 entry_url اتغير → محادثة جديدة")
            else:
                p(Fore.CYAN, f"  🆕 أول محادثة — project_id=None → Genspark هيولد واحدة")



    # ── اختيار الحساب ──
    skip_emails = set()

    if args.email:
        acc = next((a for a in accounts if a.get("email") == args.email and a.get("cookies")), None)
        if not acc:
            p(Fore.RED, f"  ❌ مش لاقي: {args.email}")
            sys.exit(1)
        cookies = acc["cookies"]
    elif project_id:
        # ── FIX الجذري: pick_account أولاً (بيراعي cooldown 29h) ──
        # ثم pick_best_project للحساب المختار — مش نجبر الـ owner!
        result = lock_pick_and_reserve(cfg, skip_emails)
        if not result:
            p(Fore.RED, "  ❌ مفيش حساب متاح! (كل الحسابات في cooldown أو محجوزة)")
            sys.exit(1)
        acc, cookies = result
        active_email = (acc.get("email") or "").strip().lower()

        # اختار project الخاص بالحساب المختار فعلاً
        _cv_now = load_convs(cfg).get(conv_name, {})
        _best_pid = pick_best_project(_cv_now, active_email)
        fork_pid = None
        if _best_pid:
            project_id = _best_pid
            p(Fore.GREEN, f"  📧 {active_email[:22]} → يكمل {project_id[:12]}... (owner ✅)")
        else:
            # الحساب ده مالوش project → هنعمل Fork للـ project الحالي
            fork_pid = project_id
            project_id = None
            p(Fore.CYAN, f"  📧 {active_email[:22]} → project جديد ← context محفوظ (Fork 🔀)")

    else:
        p(Fore.CYAN, "  🎯 Smart Picker...")
        result = lock_pick_and_reserve(cfg, skip_emails)
        if not result:
            p(Fore.RED, "  ❌ مفيش حساب متاح!")
            sys.exit(1)
        acc, cookies = result

        # ✔ FIX: شلنا entry_url و mismatch check — أي حساب يكمل أي project

    # ✅ FIX: شلنا Final Entry URL Check كمان — نفس السبب

    # ── Auto-Register في الخلفية ──
    reg_proc = _start_auto_register(cfg)

    # ── Ticket — رقم التيكت يتحدد مبكراً, الحفظ يحصل بعد النجاح فقط (Lazy Ticket) ──
    ticket_num = _get_next_ticket_num(cfg) if cfg.save_tickets else 0

    # ── Retry loop — max_retries من Config مش hardcoded ──
    MAX_RETRY = cfg.max_retries
    for attempt in range(MAX_RETRY):
        if attempt > 0:
            p(Fore.YELLOW, f"\n  🔄 محاولة {attempt + 1}...")

        # فتح ملف الرد اللحظي — بس لو save_realtime
        _tf = None
        _tf_path = None  # نحتاجه عشان نمسحه لو المحاولة فشلت
        if cfg.save_tickets and cfg.save_realtime:
            d = _ticket_dir(cfg)
            base = _ticket_filename(cfg, "a", ticket_num)
            _tf_path = d / f"{base}.txt"
            _tf = open(_tf_path, "w", encoding="utf-8")

        try:
            _prompt = build_prompt(question, cfg, history)
            # ── FIX 2: حفظ last_sent_chat_sent قبل الإرسال مش بعده ──
            # عشان لو run تاني فوراً → الـ cooldown يشتغل من أول ثانية
            if attempt == 0:  # بس في أول محاولة (مش في كل retry)
                _now_ts = time.strftime("%Y-%m-%dT%H:%M:%S")
                for _i, _a in enumerate(accounts):
                    if _a.get("email") == acc.get("email"):
                        accounts[_i]["last_sent_chat_sent"] = _now_ts
                        break
                save_accounts(accounts, cfg)
            answer, pid, asst_id = send_chat(
                cookies, _prompt, acc.get("email", ""),
                project_id=project_id, history=history, cfg=cfg,
                ticket_file=_tf,
                fork_project_id=fork_pid if 'fork_pid' in locals() else None,
            )
        finally:
            if _tf:
                _tf.close()
                _tf = None

        # ── 🔴 Invalid Project Auto-Recovery ──
        if pid == "__INVALID_PROJECT__":
            p(Fore.YELLOW, "  ⚠️ Project قديم/محذوف → Auto-Recovery...")
            _bad_pid = project_id
            project_id = None
            # ✅ FIX: نحتفظ بالـ history! كده الـ AI يعرف السياق القديم
            # (زي ما المتصفح بيعمل في Continue Conversation بالظبط)
            # history = []  ← كان بيمسح — ده غلط!
            # مسح ذكي من conversations.json: امسح الـ project الباظ بس، خلي الباقي
            if cfg.persistent:
                _cv = load_convs(cfg)
                if conv_name in _cv:
                    _cv[conv_name]["project_id"] = None
                    if "urls" in _cv[conv_name] and _bad_pid:
                        _cv[conv_name]["urls"] = [
                            u for u in _cv[conv_name]["urls"]
                            if u.get("project_id") != _bad_pid
                        ]
                    # ✅ FIX: نحافظ على source_entry_url عشان الـ run الجاي يكمل
                    # مش نمسحها! الـ entry_url override logic هيستخدمها
                    save_convs(_cv, cfg)
                    p(Fore.YELLOW, f"  🗑️ مسح project القديم ({str(_bad_pid)[:12]}...) من المحفوظات")
            # ✅ FIX: project_id = None → Genspark يولد محادثة جديدة مباشرة
            # مش نستخدم entry_url ID لأن ده agent template مش محادثة (بيرجع 500!)
            p(Fore.CYAN, "  🆕 project_id = None → Genspark هيولد محادثة جديدة")
            answer, pid, asst_id = None, None, None
            continue  # ← آخر retry بـ project_id جديد (مش break عشان نبعت في نفس الـ run)



        if answer == "__CREDIT_EXHAUSTED__":
            email_x = acc.get("email", "")
            refreshed = False

            # ── Auto-Refresh Session (CREDIT_EXHAUSTED = session منتهية مش رصيد خالص) ──
            if cfg.auto_refresh_on_exhausted and email_x:
                p(Fore.YELLOW, f"  ⚡ CREDIT_EXHAUSTED — بيجدد session لـ {email_x}...")
                new_cookies = _relogin_account(accounts, email_x, cfg)
                if new_cookies:
                    save_accounts(accounts, cfg)
                    p(Fore.GREEN, "  ✅ Session اتجدد — بيحاول تاني (project جديد)...")
                    try:
                        _tf2 = None
                        if cfg.save_tickets and cfg.save_realtime:
                            d2 = _ticket_dir(cfg)
                            base2 = _ticket_filename(cfg, "a", ticket_num)
                            _tf2 = open(d2 / f"{base2}.txt", "w", encoding="utf-8")
                        try:
                            # ⚠️ ابعت بـ project_id=None عشان تبدأ project جديد مش رابط قديم 
                            answer2, pid2, asst_id2 = send_chat(
                                new_cookies, question, email_x,
                                project_id=None,  # ✔ دايماً None بعد الـ refresh
                                history=[],       # ✔ history فاضي (project جديد)
                                cfg=cfg,
                                ticket_file=_tf2,
                            )
                        finally:
                            if _tf2:
                                _tf2.close()
                        if answer2 and answer2 != "__CREDIT_EXHAUSTED__":
                            answer, pid, asst_id = answer2, pid2, asst_id2
                            acc["cookies"] = new_cookies
                            cookies = new_cookies
                            project_id = None  # هتتحدث من الـ response
                            refreshed = True
                        else:
                            p(Fore.RED, "  ❌ لسه بيدّي CREDIT_EXHAUSTED بعد الجديد!")
                            # كريدت خلص فعلاً → حط inactive
                            for i, a in enumerate(accounts):
                                if a.get("email") == email_x:
                                    accounts[i]["active"] = False
                                    p(Fore.YELLOW, f"  🔒 {email_x} → active=false")
                                    break
                            save_accounts(accounts, cfg)
                    except Exception as _e:
                        p(Fore.RED, f"  ❌ إرسال بعد refresh فشل: {_e}")

            if not refreshed:
                skip_emails.add(email_x)
                # امسح ملف الرد اللحظي لو المحاولة فشلت (لا تسيب ملفات فاضية)
                if _tf_path and _tf_path.exists():
                    try:
                        _tf_path.unlink()
                    except OSError:
                        pass
                _tf_path = None
                release_account(email_x, cfg, status_zero=True)

                if locked_email and project_id:
                    p(Fore.RED, "  ❌ الحساب المقفول خلص — مش ممكن ننقل المحادثة!"
                        " ويتجدد بعد 29 ساعة؟")
                    break

                result = lock_pick_and_reserve(cfg, skip_emails)
                if not result:
                    p(Fore.RED, "  ❌ كل الحسابات خلصت! سيتجدد بعد 29 ساعة")
                    break
                acc, cookies = result
                continue

            # لو الـ refresh نجح — اكمل تنفيذ الرد...

        if answer:
            final_pid = pid or project_id or ""
            safe_asst_id = asst_id or str(uuid.uuid4())
            # ── last_sent_chat_sent إجباري ── عشان طريقة الـ 29 ساعة تشتغل صح
            _now_ts = time.strftime("%Y-%m-%dT%H:%M:%S")
            for _i, _a in enumerate(accounts):
                if _a.get("email") == acc.get("email"):
                    accounts[_i]["last_sent_chat_sent"] = _now_ts
                    break
            save_accounts(accounts, cfg)
            update_conversation(
                cfg, conv_name, acc.get("email", ""), question,
                str(uuid.uuid4()), answer,
                safe_asst_id, final_pid,
            )
            if getattr(cfg, "save_to_json", False):
                p(Fore.GREEN, f"\n  💾 [{conv_name}] | 🔗 {final_pid[:16]}...")
            else:
                p(Fore.GREEN, f"\n  🔗 الرابط: {final_pid[:16]}...")
            # ── 🔗 URL Mode: تحقق من العمومية واحفظ الرابط في JSON ────────────────
            if final_pid:
                if VERIFY_PUBLIC_AFTER:
                    _public_url = ensure_public(final_pid, cookies, cfg, label="بعد الإرسال")
                else:
                    _public_url = f"{GENSPARK}/autopilotagent_viewer?id={final_pid}"
                if USE_URL_MODE:
                    save_url_entry(
                        project_id=final_pid,
                        public_url=_public_url,
                        question=_url_mode_question,
                        email=acc.get("email", ""),
                        cfg=cfg,
                    )
                    if getattr(cfg, "save_to_json", False):
                        p(Fore.GREEN + Style.BRIGHT, f"  💾 تم حفظ الرابط في {URLS_FILE}")
                p(Fore.GREEN + Style.BRIGHT, f"  🔗 {_public_url}")
            # ── اعرض الرابط (Legacy — بس لو URL Mode مش شغال) ──
            elif cfg.show_url_after_send and final_pid:
                p(Fore.GREEN + Style.BRIGHT, f"  \u21b3 {GENSPARK}/autopilotagent_viewer?id={final_pid}")
            # ── Auto-Share ذكي (مرة واحدة بس) ──
            # ── fresh_start: امسح public_url القديم عشان الشير يشتغل للـ project الجديد ──
            if _do_fresh and cfg.persistent:
                _clr_convs = load_convs(cfg)
                if conv_name in _clr_convs and "public_url" in _clr_convs[conv_name]:
                    del _clr_convs[conv_name]["public_url"]
                    save_convs(_clr_convs, cfg)
            _do_auto_share(cfg, conv_name, final_pid, cookies)
            # fresh_start auto-reset: احفظ العلامة + الـ project الجديد
            if _do_fresh and cfg.persistent and final_pid:  # guard: مش نحفظ إلا لو final_pid موجود
                _fresh_convs = load_convs(cfg)
                if conv_name in _fresh_convs:
                    _fresh_convs[conv_name]["fresh_used"] = True
                    _fresh_convs[conv_name]["fresh_project_id"] = final_pid  # جديد: Single Source of Truth
                    save_convs(_fresh_convs, cfg)
                    p(Fore.CYAN, "  ♻️ fresh_start استُخدم — المرة الجاية هيكمل تلقائي")

            # ── Ticket — حفظ السؤال + الرد بعد النجاح فقط (Lazy Ticket) ──
            if cfg.save_tickets:
                _save_ticket_question(cfg, question, ticket_num)  # ← حفظ السؤال بس لما يكون في رد
                if not cfg.save_realtime:  # save_realtime: الرد اتكتب لحظياً أثناء الإرسال
                    _save_ticket_answer(cfg, answer, ticket_num)
            _cleanup_old_tickets(cfg)
            _update_balance(accounts, acc.get("email", ""), cookies, cfg)

            # Share
            if args.share and final_pid:
                p(Fore.YELLOW, "  🌐 بيعمل رابط عام...")
                url = share_project(final_pid, cookies, show_debug=cfg.show_debug)
                if url:
                    p(Fore.GREEN + Style.BRIGHT, f"  🔗 {url}")
                    convs2 = load_convs(cfg)
                    if conv_name in convs2:
                        convs2[conv_name]["public_url"] = url
                        save_convs(convs2, cfg)
        else:
            # ← فشل غير CREDIT_EXHAUSTED (500 أو غيره)
            email_x = acc.get("email", "")
            p(Fore.RED, f"  ❌ فشل! ({email_x[:20]}...) — بنجرب حساب تاني...")
            skip_emails.add(email_x)
            # امسح ملف الرد اللحظي لو اتفتح
            if _tf_path and _tf_path.exists():
                try:
                    _tf_path.unlink()
                except OSError:
                    pass
            # تحرير الحجز
            release_account(email_x, cfg, status_failed=True)
            # جرب حساب تاني
            result = lock_pick_and_reserve(cfg, skip_emails)
            if not result:
                p(Fore.RED, "  ❌ كل الحسابات فشلت — توقف")
                break
            acc, cookies = result
            locked_email = acc.get("email", "")
            p(Fore.GREEN, f"  ✅ تحول لـ {locked_email[:20]}...")
            continue
        break

    print()
    # في وضع السؤال الواحد — متوقفش register، خليه يكمل في الخلفية
    if reg_proc and reg_proc.poll() is None:
        p(Fore.CYAN, f"  🔄 Auto-Register كمّل في الخلفية (PID {reg_proc.pid}) — هينشئ {cfg.auto_register_max} حسابات")


# ═══════════════════════════════════════════════════════════════════════
# 🚀 MAIN / ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════
import concurrent.futures

ACTIVE_MODELS = [
    {"name": "Claude Opus 5 (Code Sandbox)", "ultra": True, "model": "claude-opus-5"}
]

def _do_ask_parallel_worker(model_dict: dict, email: str, cookies: dict, query: str, cfg: Config, accounts: list, skip_emails: set):
    from colorama import Fore, Style  # ← إلزامي هنا (thread scope)
    t0 = time.time()
    # Override config per model
    cfg.use_ultra = model_dict["ultra"]
    cfg.model = model_dict["model"]
    cfg.save_tickets = False # Disable tickets to avoid race conditions in parallel

    # ── 🔗 URL Mode: هجين — Fork من entry_url أو تكملة من JSON ──────────────
    _start_project_id = None
    _fork_history     = []          # رسايل قديمة لو Fork Mode

    if not cfg.entry_url and ENTRY_URL:
        cfg.entry_url = ENTRY_URL

    if cfg.entry_url or USE_URL_MODE:
        if cfg.entry_url:
            orig_pid = extract_project_id(cfg.entry_url)
            p(Fore.CYAN, f"  🌱 Seed Server-Forking Mode: جاري تفريع الساندبوكس من {cfg.entry_url[:40]}...")
            _fork_history = fetch_project_messages(orig_pid, cookies, cfg)
            forked_pid = create_forked_project(orig_pid, cookies, cfg)
            _start_project_id = forked_pid or orig_pid
        elif USE_URL_MODE:
            _last = get_last_url(cfg)
            if _last and _last.get("project_id"):
                _start_project_id = _last.get("project_id")
                p(Fore.CYAN, f"  📌 Continue Mode: من آخر JSON ({_start_project_id[:16]}...)")


    for attempt in range(50): # 50 محاولة عشان يلف على كل الحسابات المتاحة بدل ما يقف بسرعة
        try:
            # لو في entry_url والحساب اتغير أثناء المحاولات → اعمل Fork للحساب الجديد
            if cfg.entry_url:
                orig_pid = extract_project_id(cfg.entry_url)
                forked_pid = create_forked_project(orig_pid, cookies, cfg)
                if forked_pid:
                    _start_project_id = forked_pid

            answer, pid, asst_id = send_chat(
                cookies, query, email,
                project_id=_start_project_id, history=_fork_history, cfg=cfg,
                ticket_file=None
            )

            elapsed = time.time() - t0

            # ── 🔴 Invalid Project Auto-Recovery ──
            if pid == "__INVALID_PROJECT__":
                from colorama import Fore
                p(Fore.YELLOW, f"  ⚠️ [Genspark Parallel] Project قديم/محذوف ({_start_project_id}) الحساب: {email} → Auto-Recovery...")
                _bad_pid = _start_project_id
                _start_project_id = None
                _fork_history = []

                if cfg.persistent:
                    _cv = load_convs(cfg)
                    conv_name = cfg.conv_name or "default"
                    if conv_name in _cv:
                        _cv[conv_name]["project_id"] = None
                        if "urls" in _cv[conv_name] and _bad_pid:
                            _cv[conv_name]["urls"] = [
                                u for u in _cv[conv_name]["urls"]
                                if u.get("project_id") != _bad_pid
                            ]
                        save_convs(_cv, cfg)
                p(Fore.GREEN, f"  🔄 بيحاول تاني مع نفس الحساب {email} بـ شات جديد...")
                continue
            
            if answer == "__SESSION_EXPIRED__":
                from colorama import Fore
                p(Fore.YELLOW, f"  ⚡ {answer} — بيجدد session لـ {email} في الخلفية...")
                import threading
                threading.Thread(target=_relogin_account, args=(accounts, email, cfg)).start()
                skip_emails.add(email)
                p(Fore.YELLOW, f"  🔄 💳 بنجرب حساب تاني فوراً...")
                pick_res = pick_account(accounts, cfg, skip_emails)
                if not pick_res:
                    return None, None, time.time() - t0, "💳 رصيد كل الحسابات خلص أو محتاج يتجدد!"
                acc, cookies = pick_res
                email = acc["email"]
                skip_emails.add(email)
                continue
                
            if answer == "__CREDIT_EXHAUSTED__":
                from colorama import Fore
                refreshed = False
                if cfg.auto_refresh_on_exhausted and email:
                    p(Fore.YELLOW, f"  ⚡ CREDIT_EXHAUSTED — بيجدد session لـ {email} في الخلفية/التوازي...")
                    new_cookies = _relogin_account(accounts, email, cfg)
                    if new_cookies:
                        save_accounts(accounts, cfg)
                        p(Fore.GREEN, f"  ✅ Session اتجدد لـ {email} — بيحاول تاني بـ project جديد...")
                        try:
                            # ⚠️ ابعت بـ project_id=None عشان تبدأ project جديد مش رابط قديم
                            answer2, pid2, asst_id2 = send_chat(
                                new_cookies, query, email,
                                project_id=None,  # ✔ دايماً None بعد الـ refresh في التوازي
                                history=[],       # ✔ history فاضي
                                cfg=cfg,
                                ticket_file=None,
                            )
                            if answer2 and answer2 != "__CREDIT_EXHAUSTED__":
                                answer, pid, asst_id = answer2, pid2, asst_id2
                                cookies = new_cookies
                                _start_project_id = None
                                refreshed = True
                            else:
                                p(Fore.RED, f"  ❌ لسه بيدّي CREDIT_EXHAUSTED لـ {email} بعد الـ refresh!")
                                # كريدت خلص فعلاً → حط inactive
                                for _i, _a in enumerate(accounts):
                                    if _a.get("email") == email:
                                        accounts[_i]["active"] = False
                                        p(Fore.YELLOW, f"  🔒 {email} → active=false (كريدت فعلاً خلص)")
                                        break
                                save_accounts(accounts, cfg)
                        except Exception as _e:
                            p(Fore.RED, f"  ❌ إرسال بعد refresh فشل لـ {email}: {_e}")

                if not refreshed:
                    release_account(email, cfg, status_zero=True)
                    skip_emails.add(email)
                    p(Fore.YELLOW, f"  🔄 💳 بنجرب حساب تاني فوراً...")
                    pick_res = lock_pick_and_reserve(cfg, skip_emails)
                    if not pick_res:
                        return None, None, time.time() - t0, "💳 رصيد كل الحسابات خلص!"
                    acc, cookies = pick_res
                    email = acc["email"]
                    skip_emails.add(email)
                    continue

            
            if answer is None:
                # ── 🔀 Smart Fallback: 500 ownership → Fork من الـ project_id اللي فشل ──
                if _start_project_id and _fork_history == []:
                    # استخدم الـ project_id اللي فشل مباشرة كـ Fork source
                    _fork_src = f"{GENSPARK}/autopilotagent_viewer?id={_start_project_id}"
                    p(Fore.YELLOW, f"  🔀 Ownership 500 → Fork من: {_start_project_id[:16]}...")
                    _fork_history = fork_from_url(_fork_src, cookies)
                    _start_project_id = None   # project جديد بتاع الحساب دلوقتي
                    if _fork_history:
                        continue   # نعيد المحاولة بـ Fork
                # لو Fork فشل أو مفيش project_id → نجرب حساب تاني
                p(Fore.YELLOW, f"  🔄 ⚠️ {email} فشل (None) بنجرب حساب تاني فوراً...")
                skip_emails.add(email)
                pick_res = pick_account(accounts, cfg, skip_emails)
                if not pick_res:
                    return None, None, time.time() - t0, "❌ كل الحسابات فشلت!"
                acc, cookies = pick_res
                email = acc["email"]
                skip_emails.add(email)
                continue

                
            # ── ✅ إصلاح: حدّث الرصيد + وقت الاستخدام بعد كل رد ناجح ──────────────
            _update_balance(accounts, email, cookies, cfg)

            # 🌸 الشير العام التلقائي + طباعة الرابط بلون بينك فاقع في الترمنال 🌸
            if pid:
                _do_auto_share(cfg, "default", pid, cookies)

            # ── 📦 Auto-Download Sandbox Hook ────────────────────────────────────
            if cfg.auto_download_sandbox and pid:
                try:
                    downloader = SandboxDownloader(cfg)
                    downloader.auto_download_project(cookies=cookies, project_id=pid, owner_email=email, prompt_title=query)
                except Exception as _dl_err:
                    if cfg.show_debug:
                        p(Fore.RED, f"⚠️ [Auto-Download Hook Error]: {_dl_err}")

            # ── 🔗 URL Mode: احفظ الرابط بعد النجاح ──────────────────────────────
            if USE_URL_MODE and pid:
                _pub = ensure_public(pid, cookies, cfg, label="parallel") if VERIFY_PUBLIC_AFTER else f"{GENSPARK}/autopilotagent_viewer?id={pid}"
                save_url_entry(project_id=pid, public_url=_pub, question=query, email=email, cfg=cfg)
                if getattr(cfg, "save_to_json", False):
                    p(Fore.GREEN, f"  💾 تم حفظ الرابط: {pid[:16]}...")

            # ── 🤖 Auto Classification via ChatGPT Shelby (09_chatgpt_shelby_classifier) ──
            if answer and answer.strip():
                try:
                    import importlib.util
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    clf_path = os.path.join(script_dir, "09_chatgpt_shelby_classifier.py")
                    if os.path.exists(clf_path):
                        spec = importlib.util.spec_from_file_location("clf_mod", clf_path)
                        clf_mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(clf_mod)
                        status_tag = clf_mod.classify_message(answer)
                        p(Fore.GREEN, f"  📊 [AUTO-CLASSIFIER ChatGPT Shelby (GPT-5-3-High)]: [ {status_tag} ]")
                except Exception as _clf_err:
                    if cfg.show_debug:
                        p(Fore.YELLOW, f"  ⚠️ [Auto-Classifier Hook Error]: {_clf_err}")

            return answer, pid, time.time() - t0, None
        except Exception as e:
            safe_name = model_dict['name'].replace(' ', '_').replace('(', '').replace(')', '')
            debug_filename = f"debug_gs_{safe_name}_error.txt"
            with open(debug_filename, "w", encoding="utf-8") as f:
                f.write(str(e))
            return None, None, time.time() - t0, f"⚠️ مفيش رد (تفاصيل الايرور في {debug_filename})"
    return None, None, time.time() - t0, "❌ فشل بعد تخطي عدد المحاولات!"


def ask_all_parallel_interactive():
    cfg = Config()
    cfg.use_ultra = ULTRA_MODE
    cfg.min_balance = MIN_BALANCE
    cfg.auto_share = AUTO_SHARE
    cfg.show_debug = SHOW_DEBUG

    print(f"\n{Fore.GREEN}{Style.BRIGHT}╔══════════════════════════════════════════════════════╗")
    print(f"║  💬 Genspark Chat (وضع التفويض الجماعي المتوازي)   ║")
    print(f"╚══════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    accounts = load_accounts(cfg)
    
    active = [m for m in ACTIVE_MODELS]
    print(f"  🤖 الأوضاع النشطة: {len(active)} وضع جاهز للتوازي")
    print(f"  📧 حسابات الخزان: {len(accounts)} حساب")
    print(f"  💡 exit=خروج")
    print(f"{Fore.LIGHTBLACK_EX}{'─' * 60}{Style.RESET_ALL}\n")

    # ── Auto-Register في الخلفية ──
    reg_proc = _start_auto_register(cfg)

    # ── 🔗 سؤال العميل عن رابط المشاركة الاستكمالي الموثق والآمن ──
    if not cfg.entry_url and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
        try:
            print(Fore.CYAN + "🔗 هل تريد الاستمرار من رابط مشاركة عامة سابق (Shared Public Link / viewer?id=...)؟")
            _user_link = input(Fore.YELLOW + "📌 ادخل الرابط أو project_id (اضغط Enter للتخطي وبدء شات جديد): ").strip()
            if _user_link:
                cfg.entry_url = _user_link
                p(Fore.GREEN, f"  ✅ اعتُمِد رابط المشاركة الاستكمالي: {cfg.entry_url}")
        except Exception:
            pass

    query = ""
    try:
        val = (_DIR / "chat_send.txt").read_text(encoding="utf-8", errors="replace").strip()
        if val: query = val
    except Exception:
        pass
        
    run_once = bool(query)

    while True:
        if not run_once:
            try:
                query = input(f"{Fore.YELLOW}  أنت ❯ {Style.RESET_ALL}").strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n  {Fore.YELLOW}⛔ باي باي!{Style.RESET_ALL}")
                break
            if not query: continue
            if query.lower() in ["exit", "quit", "/exit"]:
                print(f"  {Fore.YELLOW}⛔ باي باي!{Style.RESET_ALL}")
                break
        
        print(f"\n{Fore.CYAN}{'═' * 76}")
        print(f"  🚀 تشغيل متوازي: {len(active)} أوضاع")
        print(f"  📝 السؤال : {query}")
        print(f"{'═' * 76}{Style.RESET_ALL}\n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(active) or 1) as executor:
            future_to_model = {}
            skip_emails = set()
            for idx, m_dict in enumerate(active):
                # نستخدم الـ Smart Picker الحقيقي عشان نختار حساب فيه رصيد
                pick_res = lock_pick_and_reserve(cfg, skip_emails)
                if not pick_res:
                    print(f"{Fore.RED}❌ مفيش ولا حساب جاهز وفيه رصيد لـ {m_dict['name']}{Style.RESET_ALL}")
                    continue
                acc, cookies = pick_res
                target_email = acc["email"]
                skip_emails.add(target_email)
                
                future = executor.submit(_do_ask_parallel_worker, m_dict, target_email, cookies, query, cfg, accounts, skip_emails)
                future_to_model[future] = (m_dict, target_email)
            
            for future in concurrent.futures.as_completed(future_to_model):
                m_dict, target_acc = future_to_model[future]
                name = m_dict["name"]
                try:
                    res, stats, t_elapsed, err = future.result()
                    print(f"  🤖 {name} {Fore.LIGHTBLACK_EX}[حساب: {target_acc}] ({t_elapsed:.1f}s){Style.RESET_ALL}")
                    if err:
                        print(f"  {Fore.RED}{err}{Style.RESET_ALL}")
                    else:
                        print(f"  {Fore.WHITE}{res}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"  🤖 {name} {Fore.LIGHTBLACK_EX}[حساب: {target_acc}]{Style.RESET_ALL}")
                    print(f"  {Fore.RED}❌ كراش أثناء التنفيذ: {e}{Style.RESET_ALL}")
                print(f"  {Fore.LIGHTBLACK_EX}{'─' * 60}{Style.RESET_ALL}\n")

        if run_once:
            break

    _stop_auto_register(reg_proc, run_once=run_once)

def legacy_cli_mode():
    pass

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) > 1:
        # User passed CLI arguments, fallback to legacy main (the old one) - keeping things non-destructive
        main() 
    else:
        ask_all_parallel_interactive()
