#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          🌐 ⚡ 01.33_telegram_gen_bridge.py                 ║
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
BUILD_VERSION = "01.33"
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
    canonical_level = "warning" if level == "warn" else level
    log_func = getattr(logger, canonical_level if hasattr(logger, canonical_level) else "info", logger.info)
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

# ══════════════════════════════════════════════════════════════
# 🔒 أقفل المزامنة والسباق الشرطي والمهلة (Thread-Safety & Race Locks)
# ══════════════════════════════════════════════════════════════
FILE_LOCK = threading.Lock()
REFRESH_LOCK = threading.Lock()
ACCOUNT_LOCKS = {}
ACCOUNT_LOCKS_GUARD = threading.Lock()
ACCOUNT_SELECTION_CLAIMS = {}
ACCOUNT_SELECTION_CLAIMS_GUARD = threading.Lock()
COOLDOWN_SECONDS = 29 * 3600  # 29 ساعة بالثواني
TELEGRAM_OFFSET_FILE = SCRIPT_DIR / "telegram_offset.txt"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/129.0.0.0"
]

BROWSER_PROFILES = [
    "chrome110", "chrome116", "chrome119", "chrome120",
    "chrome123", "chrome124", "safari17_0", "safari15_5", "chrome120"
]

# 🤖 بيانات البوت والقنوات المعتمدة
ALLOWED_CHAT_IDS = {1124247595, 6750672145}
DEFAULT_CHANNEL_ID = "-1004356848093"  # قناة / جروب المشاركة والرفع التلقائي

# 👥 [P17] دعم الجروبات: الجروبات/السوبرجروبات لها IDs سالبة وكانت تُرفض صامتاً.
# السياسة: جروب معتمد صراحةً → مسموح للجميع فيه — أو أي جروب يكتب فيه مستخدم معتمد.
# يمكن توسيع القائمة بمتغير البيئة BRIDGE_ALLOWED_GROUP_IDS (مفصولة بفواصل).
ALLOWED_GROUP_IDS = {int(DEFAULT_CHANNEL_ID)}
for _gid in (os.environ.get("BRIDGE_ALLOWED_GROUP_IDS") or "").split(","):
    _gid = _gid.strip()
    if _gid.lstrip("-").isdigit():
        ALLOWED_GROUP_IDS.add(int(_gid))


def is_chat_allowed(chat_id, from_user_id=None) -> bool:
    """[P17] بوابة الصلاحيات الموحدة لمساري message و callback.

    - شات خاص معتمد (ID موجب في ALLOWED_CHAT_IDS) → مسموح.
    - جروب معتمد صراحةً (ID سالب في ALLOWED_GROUP_IDS) → مسموح.
    - أي جروب آخر: مسموح فقط لو المُرسِل نفسه مستخدم معتمد (from_user_id في ALLOWED_CHAT_IDS).
    """
    try:
        cid = int(chat_id)
    except (TypeError, ValueError):
        return False
    if cid in ALLOWED_CHAT_IDS:
        return True
    if cid < 0:
        if cid in ALLOWED_GROUP_IDS:
            return True
        try:
            return from_user_id is not None and int(from_user_id) in ALLOWED_CHAT_IDS
        except (TypeError, ValueError):
            return False
    return False

PROJECTS_TREE_FILE = resolve_shared_path("projects_tree.json")  # 🔎 [P23] شجرة مشتركة: محلي ثم الأب
PROJECT_REGISTRY_HOME = resolve_shared_path("project_registry")  # 🔎 [P23] سجل مركزي: محلي ثم الأب
PROJECT_REGISTRY_INDEX_FILE = PROJECT_REGISTRY_HOME / "registry.json"
# ══════════════════════════════════════════════════════════════
# 🧠 Model Contracts & Normalization Runtime (Self-Contained)
# ══════════════════════════════════════════════════════════════
CONTRACT_VERSION = "v15"

AVAILABLE_MODELS = [
    "claude-fable-5",
    "claude-opus-5",
    "claude-sonnet-5",
    "gpt-5.6-sol",
    "kimi-k3",
]
DEFAULT_PROJECT_MODEL = "claude-fable-5"
PROTECTED_MODELS = frozenset({"gpt-5.5", "claude-opus-4-8"})

MODEL_ALIASES = {
    "claude-fable-5": "claude-fable-5",
    "claude fable 5": "claude-fable-5",
    "fable 5": "claude-fable-5",
    "claude-opus-5": "claude-opus-5",
    "claude opus 5": "claude-opus-5",
    "opus 5": "claude-opus-5",
    "claude-sonnet-5": "claude-sonnet-5",
    "claude sonnet 5": "claude-sonnet-5",
    "sonnet 5": "claude-sonnet-5",
    "gpt-5.6-sol": "gpt-5.6-sol",
    "gpt 5.6 sol": "gpt-5.6-sol",
    "gpt 5.6": "gpt-5.6-sol",
    "kimi-k3": "kimi-k3",
    "kimi k3": "kimi-k3",
    "k3": "kimi-k3",
    "gpt-5.5": "gpt-5.5",
    "gpt 5.5": "gpt-5.5",
    "gpt5.5": "gpt-5.5",
    "claude-opus-4-8": "claude-opus-4-8",
    "claude opus 4.8": "claude-opus-4-8",
    "claude opus 4.8 pro": "claude-opus-4-8",
}

# ── عقود الموديلات (CONTRACTS) — SSOT موحد ──────────────────────────────
# model_slug → (models_list, use_model, ai_chat_model, inject_msg_id)
CONTRACTS = {
    "claude-fable-5":  (["gpt-4.1"],          "claude-fable-5",  None,              True),
    "claude-opus-5":   (["claude-opus-5"],    "claude-opus-5",   None,              True),
    "claude-sonnet-5": (["claude-sonnet-5"],  "claude-sonnet-5", "claude-sonnet-5", True),
    "gpt-5.6-sol":     (["gpt-5.6-sol"],      "gpt-5.6-sol",     "gpt-5.6-sol",     True),
    "kimi-k3":         (["kimi-k3"],          "kimi-k3",         "kimi-k3",         True),
}


def is_protected(model: str | None) -> bool:
    """التحقق مما إذا كان الموديل ينتمي للمسار الخاص المحمي (gpt-5.5 / claude-opus-4-8)"""
    m = str(model or "").strip().lower()
    return m in PROTECTED_MODELS or MODEL_ALIASES.get(m) in PROTECTED_MODELS


def apply_contract(payload: dict, model: str | None, msg_id: str | None = None) -> dict:
    """
    تطبيق عقد الموديل على الـ payload وإرجاع dict دائمًا.
    - موديل محمي → no-op (payload بدون تعديل).
    - موديل معروف → يحقن: models, use_model, ai_chat_model, client_message_id.
    - موديل مجهول → يضع models=[m] فقط.
    """
    m = str(model or "").strip().lower()
    canonical = MODEL_ALIASES.get(m, m)

    if canonical in PROTECTED_MODELS:
        log_event("warning", f"[ROUTING BUG] Protected model '{model}' reached generic apply_contract adapter")
        return payload

    c = CONTRACTS.get(canonical)
    if not c:
        payload["models"] = [canonical] if canonical else [DEFAULT_PROJECT_MODEL]
        log_event("warning", f"No contract for model '{model}', fallback models only")
        return payload

    models, use_model, ai_chat, needs_id = c
    payload["models"] = list(models)
    if use_model:
        payload["use_model"] = use_model
    if ai_chat:
        payload["ai_chat_model"] = ai_chat
    if needs_id and msg_id:
        payload["client_message_id"] = msg_id

    return payload
# ──────────────────────────────────────────────────────────────────────────


def normalize_project_model(model: str | None) -> str:
    """تطبيع اسم الموديل وإرجاع slug معتمد دائماً (str) مع دعم الأسماء المستعارة"""
    candidate = str(model or "").strip()
    if not candidate:
        return DEFAULT_PROJECT_MODEL
    lowered = candidate.lower()
    if lowered in MODEL_ALIASES:
        return MODEL_ALIASES[lowered]
    if candidate in AVAILABLE_MODELS:
        return candidate
    log_event("warn", f"Unknown model '{candidate}', falling back to default '{DEFAULT_PROJECT_MODEL}'")
    return DEFAULT_PROJECT_MODEL

DEFAULT_PROJECT_RESUME_PROMPT = "تابع"
PROJECT_SECRET_SCHEMA_VERSION = 1


def normalize_project_resume_prompt(prompt: str | None) -> str:
    clean = re.sub(r"\s+", " ", str(prompt or "")).strip()
    return clean or DEFAULT_PROJECT_RESUME_PROMPT


def normalize_project_resume_mode(mode: str | None, prompt: str | None = None) -> str:
    candidate = str(mode or "").strip().lower()
    normalized_prompt = normalize_project_resume_prompt(prompt)
    if candidate in {"default", "custom"}:
        return candidate
    return "default" if normalized_prompt == DEFAULT_PROJECT_RESUME_PROMPT else "custom"


RUNTIME_GITHUBTOKEN_SUFFIX_RE = re.compile(r"\s*GITHUBTOKEN====>\S+", re.IGNORECASE)
GENERIC_GITHUB_SECRET_RE = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{20,})\b")


def strip_runtime_github_token_suffix(text: str | None) -> str:
    raw = str(text or "")
    return re.sub(RUNTIME_GITHUBTOKEN_SUFFIX_RE, "", raw).strip()


def redact_github_secrets(text: str | None) -> str:
    raw = str(text or "")
    raw = re.sub(RUNTIME_GITHUBTOKEN_SUFFIX_RE, " GITHUBTOKEN====>[REDACTED]", raw)
    raw = re.sub(GENERIC_GITHUB_SECRET_RE, "[REDACTED_GITHUB_TOKEN]", raw)
    return raw


def get_public_continuation_prompt_text(text: str | None) -> str:
    return normalize_project_resume_prompt(redact_github_secrets(strip_runtime_github_token_suffix(text)))


def get_default_github_token_from_env() -> str:
    return os.getenv("GITHUB_TOKEN", "").strip() or os.getenv("GITHUB_UPLOAD_TOKEN", "").strip()


def compose_runtime_resume_prompt(resume_prompt: str | None, github_token: str | None = None) -> str:
    prompt = normalize_project_resume_prompt(resume_prompt)
    # الأمان الصارم: لا يتم حقن التوكن الخام نهائياً في نص البرومت المرسل للذكاء الاصطناعي
    return prompt


def summarize_resume_prompt_for_display(prompt: str | None, limit: int = 80) -> str:
    clean = get_public_continuation_prompt_text(prompt)
    return clean if len(clean) <= limit else f"{clean[:limit - 3]}..."


def resolve_project_runtime_binding(
    project_key: str | None,
    *,
    requested_model: str | None = None,
    registry: "ProjectRegistry | None" = None,
) -> dict:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    requested_model_normalized = normalize_project_model(requested_model)
    if not key:
        public_resume_prompt = DEFAULT_PROJECT_RESUME_PROMPT
        return {
            "project_key": "",
            "model": requested_model_normalized,
            "resume_prompt_public": public_resume_prompt,
            "resume_prompt_runtime": public_resume_prompt,
            "github_enabled": False,
            "source": "request",
        }
    reg = registry or ProjectRegistry(key)
    settings = reg.get_project_settings()
    has_saved_settings = reg.manifest_path.exists()
    stored_model = normalize_project_model(settings.get("model"))
    public_resume_prompt = normalize_project_resume_prompt(settings.get("continuation", {}).get("prompt"))
    github_enabled = bool(settings.get("github", {}).get("enabled"))
    runtime_resume_prompt = reg.build_effective_resume_prompt(include_github_token=github_enabled)
    selected_model = stored_model if has_saved_settings else requested_model_normalized
    return {
        "project_key": key,
        "model": selected_model,
        "resume_prompt_public": public_resume_prompt,
        "resume_prompt_runtime": runtime_resume_prompt,
        "github_enabled": github_enabled,
        "source": "project-settings" if has_saved_settings else "request",
    }


def get_bridge_cfg_public_resume_prompt(bridge_cfg: object | None) -> str:
    prompt = getattr(bridge_cfg, "project_resume_prompt_public", "") if bridge_cfg is not None else ""
    return normalize_project_resume_prompt(prompt)


def get_bridge_cfg_runtime_resume_prompt(bridge_cfg: object | None) -> str:
    prompt = str(getattr(bridge_cfg, "project_resume_prompt_runtime", "") or "").strip() if bridge_cfg is not None else ""
    return prompt or get_bridge_cfg_public_resume_prompt(bridge_cfg)


def apply_project_runtime_binding(
    bridge_cfg: object | None,
    project_key: str | None,
    *,
    requested_model: str | None = None,
    registry: "ProjectRegistry | None" = None,
) -> dict:
    binding = resolve_project_runtime_binding(project_key, requested_model=requested_model, registry=registry)
    if bridge_cfg is not None:
        bridge_cfg.model = normalize_project_model(binding.get("model"))
        bridge_cfg.project_resume_prompt_public = binding.get("resume_prompt_public") or DEFAULT_PROJECT_RESUME_PROMPT
        bridge_cfg.project_resume_prompt_runtime = binding.get("resume_prompt_runtime") or bridge_cfg.project_resume_prompt_public
        bridge_cfg.project_runtime_binding_source = str(binding.get("source") or "")
    return binding


def default_project_settings() -> dict:
    return {
        "model": DEFAULT_PROJECT_MODEL,
        "continuation": {
            "prompt": DEFAULT_PROJECT_RESUME_PROMPT,
            "mode": "default",
        },
        "github": {
            "configured": False,
            "enabled": False,
            "repository": "",
            "token_present": False,
            "token_storage": "",
            "branch": "",
            "branch_mode": "disabled",
            "detected_default_branch": "",
            "available_branches": [],
            "last_repo_check_status": "",
            "last_repo_check_at": "",
        }
    }


_ENGINE_CACHE = {"mod": None, "path": None}
_ENGINE_LOCK = threading.Lock()


def get_genspark_engine():
    """استيراد وتخزين محرك Genspark مرة واحدة فقط لتوحيد دوال الدخول والتوليد"""
    with _ENGINE_LOCK:
        if _ENGINE_CACHE["mod"] is not None:
            return _ENGINE_CACHE["mod"]

        if str(SCRIPT_DIR) not in sys.path:
            sys.path.insert(0, str(SCRIPT_DIR))

        # البحث فقط داخل مجلد W___webapp واستخدام المحرك المحلي المدمج 01.02
        search_order = [
            "01.03Genspark_claude-opus-5-code.py",
        ]
        search_dirs = [SCRIPT_DIR]

        for script_name in search_order:
            for search_dir in search_dirs:
                file_path = search_dir / script_name
                if file_path.exists():
                    try:
                        import importlib.util
                        spec = importlib.util.spec_from_file_location("genspark_engine", file_path)
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        if hasattr(mod, "send_chat"):
                            _ENGINE_CACHE["mod"] = mod
                            _ENGINE_CACHE["path"] = str(file_path)
                            log_event("success", f"تم استيراد المحرك بنجاح: {script_name}")
                            return mod
                    except Exception as e:
                        log_event("error", f"فشل استيراد المحرك {script_name}: {e}")

        log_event("error", "لم يُعثر على أي محرك Genspark متوافق!")
        return None


def get_account_lock(email: str) -> threading.Lock:
    """قفل خاص بكل إيميل لمنع تضارب الثريدات الموازية لنفس الحساب"""
    key = (email or "").strip().lower()
    with ACCOUNT_LOCKS_GUARD:
        if key not in ACCOUNT_LOCKS:
            ACCOUNT_LOCKS[key] = threading.Lock()
        return ACCOUNT_LOCKS[key]


def _normalize_account_claim_key(email: str | None) -> str:
    return str(email or "").strip().lower()


def get_account_selection_claim(email: str | None) -> dict | None:
    key = _normalize_account_claim_key(email)
    if not key:
        return None
    with ACCOUNT_SELECTION_CLAIMS_GUARD:
        claim = ACCOUNT_SELECTION_CLAIMS.get(key)
        return dict(claim) if isinstance(claim, dict) else None


def claim_account_selection(email: str | None, owner_token: str, project_key: str = "", attempt_number: int = 0) -> bool:
    key = _normalize_account_claim_key(email)
    token = str(owner_token or "").strip()
    if not key or not token:
        return False
    with ACCOUNT_SELECTION_CLAIMS_GUARD:
        existing = ACCOUNT_SELECTION_CLAIMS.get(key)
        if isinstance(existing, dict) and existing.get("owner_token") and existing.get("owner_token") != token:
            return False
        ACCOUNT_SELECTION_CLAIMS[key] = {
            "owner_token": token,
            "project_key": str(project_key or ""),
            "attempt_number": int(attempt_number or 0),
            "claimed_at": time.time(),
        }
        return True


def release_account_selection(email: str | None, owner_token: str) -> bool:
    key = _normalize_account_claim_key(email)
    token = str(owner_token or "").strip()
    if not key or not token:
        return False
    with ACCOUNT_SELECTION_CLAIMS_GUARD:
        existing = ACCOUNT_SELECTION_CLAIMS.get(key)
        if not isinstance(existing, dict) or existing.get("owner_token") != token:
            return False
        del ACCOUNT_SELECTION_CLAIMS[key]
        return True


def claim_eligible_account_for_owner(
    all_accounts: list,
    tried_emails: set,
    owner_token: str,
    project_key: str = "",
    attempt_number: int = 0,
) -> tuple[dict | None, list[dict], str]:
    ready_accounts = get_eligible_accounts(all_accounts, tried_emails)
    if not ready_accounts:
        return None, [], "no-eligible"
    candidate_pool = list(ready_accounts[:5] if len(ready_accounts) > 5 else ready_accounts)
    while candidate_pool:
        curr_acc = random.choice(candidate_pool)
        curr_email = curr_acc.get("email") if isinstance(curr_acc, dict) else ""
        if claim_account_selection(curr_email, owner_token, project_key=project_key, attempt_number=attempt_number):
            return curr_acc, ready_accounts, "claimed"
        candidate_pool = [acc for acc in candidate_pool if acc is not curr_acc]
    return None, ready_accounts, "busy"


def record_account_journey(bridge_cfg, email: str) -> list:
    """يسجل الحساب في مسار رحلة المهمة على bridge_cfg مع منع التكرار المتتالي (A→A تبقى A).

    يُستدعى فقط لحظة الـ claim الفعلي (لا Email وهمي من الـ Pool)، ويُرجع القائمة الحية.
    """
    if bridge_cfg is None:
        return []
    email_clean = str(email or "").strip()
    journey = getattr(bridge_cfg, "account_journey", None)
    if not isinstance(journey, list):
        journey = []
        bridge_cfg.account_journey = journey
    if email_clean and (not journey or journey[-1] != email_clean):
        journey.append(email_clean)
    return journey


def format_account_journey_line(journey) -> str:
    """يبني سطر «مسار الحسابات» للرسالة النهائية — يظهر فقط عند تعدد الحسابات الفعلية."""
    emails = [str(item).strip() for item in (journey or []) if str(item or "").strip()]
    if len(emails) < 2:
        return ""
    return "🧾 <b>مسار الحسابات:</b> " + " ← ".join(f"<code>{html_escape(item)}</code>" for item in emails)


# ══════════════════════════════════════════════════════════════
# ⏱️ [P30] المحاسبة الزمنية الجنائية للحسابات (Forensic Time Accounting)
# spans حية على bridge_cfg — تُفتح لحظة الـ claim الفعلي وتُغلق حتماً
# في finally (نجاح/فشل/إلغاء/استثناء). monotonic للمدة + wall للعرض.
# ══════════════════════════════════════════════════════════════
def open_account_timing_span(bridge_cfg, email: str, attempt_number: int = 0) -> dict | None:
    """يفتح span زمني لحساب لحظة الـ claim الفعلي فقط (لا Email وهمي من الـ Pool).

    المدة تُقاس بـ time.monotonic() (محصّنة ضد قفزات ساعة النظام داخل نفس البروسيس)،
    و time.time() يُسجَّل للعرض/التدقيق فقط. يُرجع الـ span الحي أو None.
    """
    if bridge_cfg is None:
        return None
    email_clean = str(email or "").strip()
    if not email_clean:
        return None
    spans = getattr(bridge_cfg, "account_journey_spans", None)
    if not isinstance(spans, list):
        spans = []
        bridge_cfg.account_journey_spans = spans
    span = {
        "email": email_clean,
        "attempt_number": int(attempt_number or 0),
        "started_monotonic": time.monotonic(),
        "started_wall": time.time(),
        "ended_monotonic": None,
        "ended_wall": None,
        "duration_seconds": None,
        "closed": False,
    }
    spans.append(span)
    return span


def close_account_timing_span(bridge_cfg, email: str | None = None) -> dict | None:
    """يغلق آخر span مفتوح (idempotent — الإغلاق المزدوج لا يغيّر المدة المسجلة).

    يُستدعى من finally حصراً فيُنفَّذ حتماً في كل المسارات. لو مرّر email
    يُغلق آخر span مفتوح لنفس الحساب؛ وإلا آخر span مفتوح أياً كان.
    """
    if bridge_cfg is None:
        return None
    spans = getattr(bridge_cfg, "account_journey_spans", None)
    if not isinstance(spans, list) or not spans:
        return None
    email_clean = str(email or "").strip()
    for span in reversed(spans):
        if not isinstance(span, dict) or span.get("closed"):
            continue
        if email_clean and str(span.get("email") or "") != email_clean:
            continue
        span["ended_monotonic"] = time.monotonic()
        span["ended_wall"] = time.time()
        span["duration_seconds"] = max(0.0, float(span["ended_monotonic"]) - float(span.get("started_monotonic") or 0.0))
        span["closed"] = True
        return span
    return None


def format_arabic_duration(seconds) -> str:
    """صياغة مدة زمنية بالعربية: «45 ثانية» / «3 دقائق و12 ثانية» / «1 ساعة و5 دقائق».

    القيم السالبة/غير الصالحة تُعامل كصفر (لا Crash أبداً في مسار الرسالة النهائية).
    """
    try:
        total = int(max(0.0, float(seconds or 0)))
    except (TypeError, ValueError):
        total = 0
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours} ساعة")
    if minutes:
        parts.append(f"{minutes} دقيقة" if hours else f"{minutes} دقائق" if minutes > 2 else f"{minutes} دقيقة")
    if secs or not parts:
        parts.append(f"{secs} ثانية")
    return " و".join(parts)


def aggregate_journey_spans_per_email(spans) -> list[dict]:
    """يجمع الـ spans لكل حساب بترتيب أول ظهور: [{email, total_seconds, spans_count}].

    A→B→A تُنتج مدخلاً واحداً لـ A بمجموع فترتيه — بدون فقدان أي فترة.
    الـ spans المفتوحة (لم تُغلق بعد) تُحتسب حتى اللحظة الحالية (best-effort).
    """
    order: list[str] = []
    totals: dict[str, dict] = {}
    now_mono = time.monotonic()
    for span in (spans or []):
        if not isinstance(span, dict):
            continue
        email = str(span.get("email") or "").strip()
        if not email:
            continue
        dur = span.get("duration_seconds")
        if dur is None:
            start = span.get("started_monotonic")
            dur = max(0.0, now_mono - float(start)) if start is not None else 0.0
        if email not in totals:
            order.append(email)
            totals[email] = {"email": email, "total_seconds": 0.0, "spans_count": 0}
        totals[email]["total_seconds"] += max(0.0, float(dur or 0.0))
        totals[email]["spans_count"] += 1
    return [totals[e] for e in order]


def format_account_timing_block(bridge_cfg, task_total_seconds=None) -> str:
    """يبني كتلة «📊 إحصائيات الحسابات وزمن التشغيل» للرسالة النهائية.

    تظهر دائماً (حتى بحساب واحد). إيميلات كاملة بلا masking (نمط P29).
    آخر حساب في الرحلة يُعلَّم «(المُنجِز)». تُرجع "" فقط لو لا توجد spans إطلاقاً.
    """
    spans = getattr(bridge_cfg, "account_journey_spans", None) if bridge_cfg is not None else None
    aggregated = aggregate_journey_spans_per_email(spans)
    if not aggregated:
        return ""
    accounts_total = sum(item["total_seconds"] for item in aggregated)
    continuations = int(getattr(bridge_cfg, "last_credit_continuations", 0) or 0)
    continuation_limit = get_credit_continuation_limit(bridge_cfg)
    last_email = ""
    raw_spans = [s for s in (spans or []) if isinstance(s, dict) and str(s.get("email") or "").strip()]
    if raw_spans:
        last_email = str(raw_spans[-1].get("email") or "").strip()
    lines = ["📊 <b>إحصائيات الحسابات وزمن التشغيل:</b>"]
    for idx, item in enumerate(aggregated, start=1):
        finisher = " <b>(المُنجِز)</b>" if item["email"] == last_email else ""
        multi = f" ×{item['spans_count']}" if item["spans_count"] > 1 else ""
        lines.append(
            f"  {idx}. <code>{html_escape(item['email'])}</code>{finisher} — "
            f"⏱ {format_arabic_duration(item['total_seconds'])}{multi}"
        )
    lines.append(f"⏱ <b>زمن تشغيل الحسابات:</b> {format_arabic_duration(accounts_total)}")
    if task_total_seconds is not None:
        lines.append(f"🕒 <b>الزمن الكلي للمهمة:</b> {format_arabic_duration(task_total_seconds)}")
    lines.append(f"🔁 <b>استئنافات نفاد الرصيد:</b> {continuations} / {continuation_limit}")
    return "\n".join(lines)


def notify_account_selection_observer(bridge_cfg, event_type: str, **payload) -> bool:
    observer = getattr(bridge_cfg, "account_selection_observer", None) if bridge_cfg is not None else None
    if not callable(observer):
        return False
    event = {
        "event": str(event_type or ""),
        "project_key": str(getattr(bridge_cfg, "selection_project_key", "") or "") if bridge_cfg is not None else "",
        "attempt_number": int(getattr(bridge_cfg, "selection_attempt_number", 0) or 0) if bridge_cfg is not None else 0,
        "selected_account_email": str(getattr(bridge_cfg, "selected_account_email", "") or "") if bridge_cfg is not None else "",
        "selected_account_claim_state": str(getattr(bridge_cfg, "selected_account_claim_state", "") or "") if bridge_cfg is not None else "",
        "credit_continuations": int(getattr(bridge_cfg, "last_credit_continuations", 0) or 0) if bridge_cfg is not None else 0,
        "max_credit_continuations": get_credit_continuation_limit(bridge_cfg),
        "continuation_prompt_public": summarize_resume_prompt_for_display(get_bridge_cfg_public_resume_prompt(bridge_cfg)) if bridge_cfg is not None else DEFAULT_PROJECT_RESUME_PROMPT,
        "runtime_binding_source": str(getattr(bridge_cfg, "project_runtime_binding_source", "") or "") if bridge_cfg is not None else "",
        # 📸 [P29] snapshot غير قابل للتغيير لمسار الحسابات لحظة إنشاء الحدث (Immutable Event Snapshot)
        "account_journey": [str(item) for item in (getattr(bridge_cfg, "account_journey", []) or [])] if bridge_cfg is not None else [],
        **payload,
    }
    try:
        observer(event)
        return True
    except Exception as obs_err:
        log_event("warning", f"فشل observer اختياري بدون إيقاف selection: {obs_err}", email=event.get("selected_account_email", ""))
        return False


def is_valid_email(email: str) -> bool:
    """التحقق من صحة صيغة الإيميل واستبعاد الإيميلات الفاسدة"""
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email or "").strip()))


def get_account_fingerprint(email: str) -> dict:
    """بصمة رقمية ثابتة ومتسقة لكل حساب (UA + Browser Profile) لمنع 401"""
    if not email:
        return {"user_agent": USER_AGENTS[0], "browser": BROWSER_PROFILES[0]}
    seed = int(hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest(), 16)
    return {
        "user_agent": USER_AGENTS[seed % len(USER_AGENTS)],
        "browser": BROWSER_PROFILES[seed % len(BROWSER_PROFILES)]
    }


def needs_web_search(query: str) -> bool:
    """تحديد ما إذا كان السؤال يتطلب البحث في الويب لتوفير الكريدت"""
    web_indicators = [
        "ابحث", "search", "آخر أخبار", "latest", "موقع", "website",
        "رابط", "link", "api", "documentation", "docs", "2025", "2026", "حالياً"
    ]
    q_lower = (query or "").lower()
    return any(ind in q_lower for ind in web_indicators)


# ══════════════════════════════════════════════════════════════
# ⚙️ كلاس الإعدادات الرئيسي (BridgeConfig) - SSOT & Config-Driven
# ══════════════════════════════════════════════════════════════
@dataclass
class BridgeConfig:
    model: str = "claude-fable-5"
    agent_type: str = "code_sandbox"
    session_timeout: int = 1000          # ⏱️ المهلة القصوى لانتظار الجلسة الواحدة (1000 ثانية)
    max_timeout_retries: int = 2         # 🔄 عدد محاولات إعادة الطلب تلقائياً عند التايم أوت
    max_account_attempts: int = 50       # 🛡️ حد أقصى للمحاولات لمنع الحلقات المفرغة
    max_credit_continuations: int = 10   # عدد مرات نقل الاستئناف عند نفاد الرصيد
    cooldown_hours: float = 29.0         # ⏱️ مهلة الـ 29 ساعة للحسابات المنتهية بـ cooldown_until
    min_preflight_balance: int = 100     # 💰 [P13] الحد الأدنى للرصيد قبل أي إرسال — أقل منه = تبريد 29h وتخطٍ صامت
    user_agent: str = USER_AGENTS[0]
    current_browser: str = "chrome120"   # 🌐 يُحدث ديناميكياً لكل حساب
    extracted_webapp_dir: pathlib.Path = field(default_factory=lambda: SCRIPT_DIR / "extracted_webapp")
    run_started_at: float | None = None
    last_credit_continuations: int = 0
    last_credit_checkpoint_state: str = ""
    last_credit_checkpoint_note: str = ""
    last_credit_checkpoint_id: str = ""
    last_credit_resume_target_url: str = ""
    last_credit_resume_project_id: str = ""
    credit_handoff_callback: object | None = None
    selection_owner_token: str = ""
    selection_project_key: str = ""
    selection_attempt_number: int = 0
    selected_account_email: str = ""
    selected_account_claim_state: str = ""
    # 🧾 [P29] مسار رحلة الحسابات الفعلية للمهمة (لحظة الـ claim فقط — لا Email وهمي)
    account_journey: list = field(default_factory=list)
    # ⏱️ [P30] spans المحاسبة الزمنية لكل claim: فتح عند الـ claim، إغلاق حتمي في finally
    account_journey_spans: list = field(default_factory=list)
    project_resume_prompt_public: str = DEFAULT_PROJECT_RESUME_PROMPT
    project_resume_prompt_runtime: str = DEFAULT_PROJECT_RESUME_PROMPT
    project_runtime_binding_source: str = ""
    account_selection_observer: object | None = None
    # 🛑 [P25] حدث الإلغاء التفاعلي — يُحقن من الـ worker ويُمرَّر لمحرك التوليد
    # (cfg.cancel_event) لقطع بث ask_proxy فوراً + وقف حلقات المتابعة (polling).
    cancel_event: object | None = None
    cancel_token: str = ""


# ══════════════════════════════════════════════════════════════
# 🛠️ إدارة الحسابات الآمنة وتحديث البيانات (Thread-Safe JSON)
# ══════════════════════════════════════════════════════════════
def get_accounts_file_path(json_path: str | None = None) -> pathlib.Path | None:
    """تحديد مسار ملف accounts_genspark.json تلقائياً"""
    possible_paths = []
    if json_path:
        possible_paths.append(pathlib.Path(json_path))
    possible_paths.extend([
        resolve_shared_path("accounts_genspark.json"),  # 🔎 [P23] محلي ثم الأب (موحّد)
        SCRIPT_DIR.parent / "accounts_genspark.json",
        pathlib.Path("accounts_genspark.json"),
    ])
    for p in possible_paths:
        if p.exists() and p.is_file():
            return p
    return None


def read_accounts_safe(json_path: str | None = None) -> list[dict]:
    """قراءة آمنة لملف الحسابات بـ FILE_LOCK لمنع التعارض مع ثريدات التحديث"""
    target_file = get_accounts_file_path(json_path)
    if not target_file or not target_file.exists():
        return []
    with FILE_LOCK:
        try:
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception as e:
            log_event("error", f"خطأ في قراءة ملف الحسابات: {e}")
    return []


def update_account_data(email: str, updates: dict, json_path: str | None = None) -> bool:
    """تحديث حقول محددة لحساب في accounts_genspark.json بأمان ذري (Thread-Safe)"""
    target_file = get_accounts_file_path(json_path)
    if not target_file or not target_file.exists():
        return False
    with FILE_LOCK:
        try:
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                accounts = json.load(f)
            if not isinstance(accounts, list):
                return False
            found = False
            for acc in accounts:
                if isinstance(acc, dict) and acc.get("email") == email:
                    acc.update(updates)
                    acc["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    found = True
                    break
            if not found:
                return False
            tmp = target_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(accounts, f, ensure_ascii=False, indent=2)
            tmp.replace(target_file)
            return True
        except Exception as e:
            log_event("error", f"فشل تحديث بيانات الحساب {email}: {e}")
            return False


def is_account_ready(acc: dict) -> bool:
    """
    فحص جاهزية الحساب (نقي 100% بدون أي كتابة على القرص):
    - status == 'cooldown' → جاهز فقط إذا انقضت مدة cooldown_until
    - status في (auth_failed, disabled) → جاهز فقط إذا كان له cooldown_until منتهي
      (أي أن الحظر مؤقت وله موعد إعادة تفعيل) — بدون موعد = رفض دائم حتى تدخل يدوي
    - status في (banned, blocked) → رفض دائم
    """
    if not isinstance(acc, dict):
        return False

    email = acc.get("email")
    if email and not is_valid_email(email):
        return False

    status = str(acc.get("status", "active")).lower().strip()
    now = time.time()

    if status in ("banned", "blocked"):
        return False

    cooldown_until = 0
    try:
        cooldown_until = float(acc.get("cooldown_until") or 0)
    except Exception:
        cooldown_until = 0

    # لسه في تبريد فعلي
    if cooldown_until > now:
        return False

    # تبريد منتهي (cooldown أو auth_failed/disabled مؤقتة) → جاهز للاستخدام
    if status == "cooldown":
        return True
    if status in ("auth_failed", "disabled"):
        # مؤقت فقط إذا كان له موعد إعادة تفعيل (cooldown_until غير صفر ومنتهي)
        return cooldown_until > 0

    if acc.get("active", True) is False:
        return False

    return True


def reactivate_account_if_due(acc: dict, json_path: str | None = None) -> dict:
    """إعادة تفعيل الحساب في الملف إذا انقضت مدة التبريد (تُستدعى عند الاستخدام الفعلي فقط)"""
    if not isinstance(acc, dict):
        return acc
    email = acc.get("email")
    if not email or not is_account_ready(acc):
        return acc
    status = str(acc.get("status", "active")).lower().strip()
    if status in ("cooldown", "auth_failed", "disabled"):
        update_account_data(email, {
            "status": "active",
            "active": True,
            "cooldown_until": 0,
            "cooldown_released_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }, json_path=json_path)
        acc = dict(acc)
        acc["status"] = "active"
        acc["active"] = True
        acc["cooldown_until"] = 0
    return acc


def get_eligible_accounts(all_accounts: list, tried_emails: set) -> list:
    """يرجع الحسابات المؤهلة فقط (خرجت من التبريد + إيميل صحيح + لم تُجرب) مرتبة بالأقدم"""
    eligible = []
    for acc in all_accounts:
        if not isinstance(acc, dict):
            continue
        em = acc.get("email")
        if not em or em in tried_emails or not is_valid_email(em):
            continue
        if not is_account_ready(acc):
            continue
        eligible.append(acc)
    eligible.sort(key=lambda x: x.get("last_used", 0) if isinstance(x.get("last_used"), (int, float)) else 0)
    return eligible


def mark_account_cooldown(email: str, cooldown_hours: float = 29.0, json_path: str | None = None) -> bool:
    """تسجيل نفاد الكريدت وتعيين cooldown_until = الآن + 29h مع active=False، وتستعاد تلقائياً بـ is_account_ready"""
    now = time.time()
    cd_until_ts = now + (cooldown_hours * 3600)
    return update_account_data(email, {
        "cooldown_until": cd_until_ts,
        "last_used": now,
        "last_credit_exhausted": now,
        "last_credit_exhausted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "cooldown",
        "active": False
    }, json_path=json_path)


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


# ══════════════════════════════════════════════════════════════
# 📲 [Task-1] دوال الاتصال المباشر والرفع الآلي لبوت تليجرام
# ══════════════════════════════════════════════════════════════
def _call_telegram_api_json(method: str, payload: dict, timeout: int = 15) -> dict:
    if not TELEGRAM_BOT_TOKEN:
        return {"ok": False, "status_code": 0, "result": {}, "description": "BOT_TOKEN_MISSING", "error": "BOT_TOKEN_MISSING"}
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    last_error = None
    for mode in ("curl_cffi", "requests"):
        try:
            if mode == "curl_cffi":
                from curl_cffi import requests as cffi
                response = cffi.post(url, json=payload, timeout=timeout)
            else:
                import requests
                response = requests.post(url, json=payload, timeout=timeout)
            try:
                body = response.json()
            except Exception:
                body = {}
            result = body.get("result") if isinstance(body, dict) and isinstance(body.get("result"), dict) else {}
            description = str(body.get("description") or getattr(response, "text", "") or "") if isinstance(body, dict) else str(getattr(response, "text", "") or "")
            ok = bool(getattr(response, "status_code", 0) == 200 and (not isinstance(body, dict) or body.get("ok", True)))
            return {
                "ok": ok,
                "status_code": int(getattr(response, "status_code", 0) or 0),
                "result": result,
                "description": description[:300],
                "error": "" if ok else description[:300],
            }
        except Exception as err:
            last_error = err
            continue
    return {
        "ok": False,
        "status_code": 0,
        "result": {},
        "description": str(last_error or "").strip()[:300],
        "error": str(last_error or "").strip()[:300],
    }


# ✂️ [P34] Safe Message Formatting — ثوابت الحدود المركزية (تعريف وحيد لكل حد)
PREVIEW_MAX_CHARS = 1000            # الحد الأقصى لجسم معاينة آخر رسالة توليد
PREVIEW_TRUNCATION_SUFFIX = "\n... [انقر على الرابط لمشاهدة الرد الكامل]"
RES_MSG_MAX_CHARS = 3500            # الحد الأقصى لرسالة الاكتمال المجمعة بالكامل
OUTGOING_TEXT_HARD_LIMIT = 3900     # عتبة تفعيل القص في طبقة الإرسال
OUTGOING_TEXT_SAFE_LIMIT = 3800     # الطول الآمن النهائي بعد القص


def _strip_partial_html_token(text: str) -> str:
    """✂️ [P34] إزالة أي وسم `<...` أو كيان `&...` مبتور عند نقطة القص — يمنع 400 Bad Request من تيليجرام."""
    trimmed = str(text or "")
    lt = trimmed.rfind("<")
    if lt != -1 and ">" not in trimmed[lt:]:
        trimmed = trimmed[:lt]
    amp = trimmed.rfind("&")
    if amp != -1 and ";" not in trimmed[amp:]:
        trimmed = trimmed[:amp]
    return trimmed


def clamp_preview_text(clean_text: str) -> str:
    """✂️ [P34] قصّ جسم المعاينة إلى 1000 حرف كحد أقصى + لاحقة إرشادية لرابط الرد الكامل."""
    body = str(clean_text or "")
    if len(body) <= PREVIEW_MAX_CHARS:
        return body
    return _strip_partial_html_token(body[:PREVIEW_MAX_CHARS]) + PREVIEW_TRUNCATION_SUFFIX


def enforce_completion_message_budget(res_msg: str, preview_body: str = "") -> str:
    """✂️ [P34] ضمان ألا تتجاوز رسالة الاكتمال المجمعة 3500 حرف:
    1. القصّ يقع على جسم المعاينة فقط (البيانات التشغيلية والروابط محفوظة حرفياً).
    2. fallback أخير: قصّ الذيل إن ظل التجاوز قائماً بدون معاينة قابلة للتقليص.
    """
    msg = str(res_msg or "")
    if len(msg) <= RES_MSG_MAX_CHARS:
        return msg
    body = str(preview_body or "")
    overflow = len(msg) - RES_MSG_MAX_CHARS
    if body and body in msg:
        keep = max(0, len(body) - overflow - len(PREVIEW_TRUNCATION_SUFFIX))
        shrunk_core = _strip_partial_html_token(body[:keep])
        if shrunk_core.endswith(PREVIEW_TRUNCATION_SUFFIX):
            shrunk = shrunk_core
        else:
            shrunk = shrunk_core + PREVIEW_TRUNCATION_SUFFIX
        msg = msg.replace(body, shrunk, 1)
    if len(msg) > RES_MSG_MAX_CHARS:
        msg = _strip_partial_html_token(msg[:RES_MSG_MAX_CHARS])
    return msg


def clamp_outgoing_text(text: str) -> str:
    """✂️ [P34] شبكة الأمان في طبقة الإرسال: نص > 3900 حرفاً ➔ قصّ آمن إلى 3800 حرفاً.
    reply_markup لا يُمس إطلاقاً — كل صفوف الأزرار التفاعلية تبقى سليمة بالكامل."""
    raw = str(text or "")
    if len(raw) <= OUTGOING_TEXT_HARD_LIMIT:
        return raw
    return _strip_partial_html_token(raw[:OUTGOING_TEXT_SAFE_LIMIT])


def send_telegram_message_detailed(
    chat_id: int | str,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str = "HTML",
) -> dict:
    """إرسال رسالة نصية مع إرجاع message_id إن توفر، بدون كسر callers القديمة."""
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "توكن البوت غير مضبوط — لا يمكن إرسال رسائل تليجرام")
        return {"ok": False, "message_id": None, "error": "BOT_TOKEN_MISSING"}
    payload = {
        "chat_id": chat_id,
        # ✂️ [P34] القصّ الآمن 3900→3800 يتم هنا مركزياً — الأزرار في reply_markup تبقى كما هي
        "text": clamp_outgoing_text(text),
        "disable_web_page_preview": False,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    result = _call_telegram_api_json("sendMessage", payload, timeout=15)
    if not result.get("ok"):
        detail = result.get("error") or result.get("description") or "UNKNOWN_TELEGRAM_SEND_ERROR"
        log_event("error", f"فشل إرسال رسالة تليجرام: HTTP {result.get('status_code', 0)} - {detail}")
    return {
        "ok": bool(result.get("ok")),
        "message_id": (result.get("result") or {}).get("message_id"),
        "status_code": result.get("status_code", 0),
        "error": result.get("error", ""),
        "description": result.get("description", ""),
    }


def edit_telegram_message_text(
    chat_id: int | str,
    message_id: int | str,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str = "HTML",
) -> dict:
    """تعديل رسالة تليجرام قائمة بأقل transport ممكن لمسار live status."""
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "توكن البوت غير مضبوط — لا يمكن تعديل رسائل تليجرام")
        return {"ok": False, "message_id": None, "error": "BOT_TOKEN_MISSING"}
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": str(text or ""),
        "disable_web_page_preview": False,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    result = _call_telegram_api_json("editMessageText", payload, timeout=15)
    description = str(result.get("description") or "")
    if not result.get("ok") and "message is not modified" in description.lower():
        return {"ok": True, "message_id": message_id, "status_code": result.get("status_code", 0), "error": "", "description": description}
    if not result.get("ok"):
        detail = result.get("error") or result.get("description") or "UNKNOWN_TELEGRAM_EDIT_ERROR"
        log_event("warning", f"فشل تعديل رسالة تليجرام live: HTTP {result.get('status_code', 0)} - {detail}")
    return {
        "ok": bool(result.get("ok")),
        "message_id": message_id,
        "status_code": result.get("status_code", 0),
        "error": result.get("error", ""),
        "description": result.get("description", ""),
    }


def edit_telegram_message_reply_markup(
    chat_id: int | str,
    message_id: int | str,
    reply_markup: dict | None,
) -> dict:
    """🛑 [P25] تعديل أزرار رسالة قائمة فقط (editMessageReplyMarkup) بدون لمس النص —
    يستخدم لتبديل كيبورد الإلغاء ⇄ كيبورد التأكيد على بطاقة المعاينة الحية."""
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "توكن البوت غير مضبوط — لا يمكن تعديل أزرار رسائل تليجرام")
        return {"ok": False, "message_id": None, "error": "BOT_TOKEN_MISSING"}
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": json.dumps(reply_markup or {"inline_keyboard": []}, ensure_ascii=False),
    }
    result = _call_telegram_api_json("editMessageReplyMarkup", payload, timeout=15)
    description = str(result.get("description") or "")
    if not result.get("ok") and "message is not modified" in description.lower():
        return {"ok": True, "message_id": message_id, "status_code": result.get("status_code", 0), "error": "", "description": description}
    if not result.get("ok"):
        detail = result.get("error") or result.get("description") or "UNKNOWN_TELEGRAM_MARKUP_ERROR"
        log_event("warning", f"فشل تعديل أزرار رسالة تليجرام: HTTP {result.get('status_code', 0)} - {detail}")
    return {
        "ok": bool(result.get("ok")),
        "message_id": message_id,
        "status_code": result.get("status_code", 0),
        "error": result.get("error", ""),
        "description": result.get("description", ""),
    }


def send_telegram_message(
    chat_id: int | str,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str = "HTML"
) -> bool:
    """إرسال رسالة نصية إلى تليجرام مع الحفاظ على العقد القديم (bool فقط)."""
    return bool(send_telegram_message_detailed(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode).get("ok"))


def _account_selection_event_title(event_type: str) -> str:
    titles = {
        "account-claimed": "🔄 <b>تم اختيار حساب للمحاولة الحالية</b>",
        "no-eligible-accounts": "⚠️ <b>لا توجد حسابات مؤهلة حالياً</b>",
        "eligible-accounts-busy": "⏳ <b>كل الحسابات المؤهلة الحالية مشغولة</b>",
        "session-refresh-required": "♻️ <b>الحساب يحتاج تجديد جلسة</b>",
        "session-refresh-succeeded": "✅ <b>تم تجديد الجلسة وسيُعاد استخدام الحساب</b>",
        "session-refresh-failed": "⛔ <b>فشل تجديد الجلسة</b>",
        "credit-exhausted-observed": "⚠️ <b>تم رصد نفاد الرصيد</b>",
        "data-retention-blocked": "🧬 <b>رُصد خطأ AI Data Retention — معاملة كنفاد رصيد</b>",
        "credit-continuations-exhausted": "⛔ <b>بلغنا حد استئناف الرصيد</b>",
        "continuation-blocked": "⛔ <b>تم حجب continuation</b>",
        "continuation-handoff-ready": "🔁 <b>تم تجهيز handoff إلى برومبت الاستئناف</b>",
        "attempt-succeeded": "✅ <b>المحاولة الحالية نجحت</b>",
        "attempt-failed-continue": "↪️ <b>المحاولة فشلت وسيستمر البحث</b>",
    }
    return titles.get(str(event_type or "").strip(), "ℹ️ <b>تحديث اختيار الحساب</b>")


class AccountSelectionLiveRenderer:
    """يبني نص live status من observer events مع آخر 3 محاولات كحد أقصى."""
    def __init__(self, project_key: str, project_name: str):
        self.project_key = str(project_key or "")
        self.project_name = str(project_name or "")
        self.latest_event_type = ""
        self.latest_status = ""
        self.final_note = ""
        self.latest_handoff_url = ""
        self.latest_handoff_checkpoint = ""
        self.entries: list[dict] = []
        self.refresh_total = 0
        self.continuation_line = "0/0"
        # 🧾 [P29] مراقبة الحساب النشط وتبديل الحساب بعد handoff
        self.active_email = ""
        self.pending_handoff_from = ""
        self.switch_line = ""

    def _upsert_entry(self, event: dict) -> dict:
        attempt_no = int(event.get("attempt_number") or 0)
        email = str(event.get("selected_account_email") or "")
        existing = next((item for item in self.entries if item.get("attempt_number") == attempt_no), None)
        if existing is None:
            existing = {
                "attempt_number": attempt_no,
                "email": email,
                "status": str(event.get("status") or ""),
                "label": "",
                "claim_state": str(event.get("selected_account_claim_state") or ""),
            }
            self.entries.append(existing)
        if email:
            existing["email"] = email
        if event.get("status"):
            existing["status"] = str(event.get("status") or "")
        if event.get("selected_account_claim_state"):
            existing["claim_state"] = str(event.get("selected_account_claim_state") or "")
        return existing

    def apply(self, event: dict) -> str:
        event_type = str(event.get("event") or "").strip()
        self.latest_event_type = event_type
        self.latest_status = str(event.get("status") or self.latest_status or "")
        self.continuation_line = f"{int(event.get('credit_continuations') or 0)}/{int(event.get('max_credit_continuations') or 0)}"
        entry = self._upsert_entry(event)
        # 🧾 [P29] تحديث الحساب النشط من snapshot الحدث فقط (لا Email وهمي)
        event_email = str(event.get("selected_account_email") or "").strip()
        if event_type == "account-claimed" and event_email:
            if self.pending_handoff_from and event_email != self.pending_handoff_from:
                # أول claim بعد handoff → سطر تبديل الحساب (الحساب الجديد لا يُعرف إلا الآن)
                self.switch_line = f"من <code>{html_escape(self.pending_handoff_from)}</code> ← إلى <code>{html_escape(event_email)}</code>"
            self.pending_handoff_from = ""
            self.active_email = event_email
        elif event_email:
            self.active_email = event_email

        continuation_prompt_public = summarize_resume_prompt_for_display(event.get("continuation_prompt_public"))
        labels = {
            "account-claimed": "تم اختيار الحساب — لم يبدأ الحكم على النتيجة بعد",
            "session-refresh-required": "الجلسة تحتاج تجديداً قبل استكمال نفس الحساب",
            "session-refresh-succeeded": "تم تجديد الجلسة بنجاح وسيُعاد استخدام نفس الحساب",
            "session-refresh-failed": "فشل تجديد الجلسة",
            "credit-exhausted-observed": "تم رصد نفاد الرصيد على هذه المحاولة",
            "data-retention-blocked": "🧬 رُصد خطأ AI Data Retention (الموديل يتطلب تفعيله بالحساب) — تبريد الحساب والانتقال لحساب آخر بنفس آخر رسالة",
            "continuation-handoff-ready": f"تم تجهيز handoff إلى برومبت الاستئناف «{continuation_prompt_public}» عند نقطة التنفيذ الحالية",
            "continuation-blocked": f"تم حجب handoff قبل برومبت الاستئناف «{continuation_prompt_public}»",
            "credit-continuations-exhausted": "بلغنا حد استئناف الرصيد",
            "attempt-succeeded": "المحاولة الحالية نجحت",
            "attempt-failed-continue": "المحاولة فشلت وسيستمر البحث في حساب آخر إن وجد",
            "eligible-accounts-busy": "كل الحسابات المؤهلة الحالية مشغولة",
            "no-eligible-accounts": "لا توجد حسابات مؤهلة حالياً",
        }
        if event_type in labels:
            entry["label"] = labels[event_type]
        if event_type == "session-refresh-required":
            self.refresh_total += 1
        if event_type == "continuation-handoff-ready":
            self.pending_handoff_from = event_email or self.active_email  # 🧾 [P29] الحساب السابق لحظة الـ handoff
            self.latest_handoff_url = str(event.get("continuation_url") or "")
            self.latest_handoff_checkpoint = str(event.get("checkpoint_id") or "")
            self.final_note = "تم تجهيز handoff الآن؛ لم يتم إعلان اكتمال المهمة بعد."
        elif event_type == "continuation-blocked":
            self.final_note = f"تم حجب handoff: {str(event.get('reason') or '')}".strip()
        elif event_type == "credit-continuations-exhausted":
            self.final_note = "تم الوصول إلى حد استئناف الرصيد الحالي."
        elif event_type == "eligible-accounts-busy":
            self.final_note = "كل الحسابات المؤهلة الحالية محجوزة لمهمات أخرى؛ لا توجد جولة انتظار إضافية."
        elif event_type == "no-eligible-accounts":
            self.final_note = "لا توجد حسابات مؤهلة حالياً وفق الواقع الحالي؛ لا توجد جولة انتظار أو retry إضافية من الـUI."
        elif event_type == "attempt-succeeded":
            self.final_note = "المحاولة الحالية نجحت؛ الرسالة النهائية العامة يمكن أن تأتي لاحقاً من مسار المهمة نفسه."

        return self.render()

    def render(self) -> str:
        lines = [_account_selection_event_title(self.latest_event_type)]
        if self.project_name:
            lines.append(f"<b>المشروع:</b> {html_escape(self.project_name)}")
        if self.project_key:
            lines.append(f"<b>مفتاح المشروع:</b> <code>{html_escape(self.project_key)}</code>")
        if self.active_email:
            lines.append(f"📧 <b>الحساب النشط:</b> <code>{html_escape(self.active_email)}</code>")
        if self.switch_line:
            lines.append(f"🔁 <b>تبديل الحساب:</b> {self.switch_line}")
        lines.append(f"<b>إجمالي المحاولات المرصودة:</b> <code>{len([x for x in self.entries if x.get('attempt_number')])}</code>")
        lines.append(f"<b>عداد الاستئناف:</b> <code>{html_escape(self.continuation_line)}</code>")
        if self.refresh_total:
            lines.append(f"<b>مرات تجديد الجلسة المرصودة:</b> <code>{self.refresh_total}</code>")
        lines.append("<b>آخر 3 محاولات:</b>")
        recent = sorted((entry for entry in self.entries if entry.get("attempt_number")), key=lambda item: item.get("attempt_number", 0), reverse=True)[:3]
        if recent:
            for entry in recent:
                lines.append(
                    f"• <code>{int(entry.get('attempt_number') or 0)}</code> — <code>{html_escape(str(entry.get('email') or ''))}</code>"
                    f" — {html_escape(str(entry.get('label') or entry.get('status') or 'بدون توصيف'))}"
                )
        else:
            lines.append("• لا توجد محاولة مرصودة بعد.")
        if self.latest_status:
            lines.append(f"<b>الحالة الحالية:</b> <code>{html_escape(self.latest_status)}</code>")
        if self.latest_handoff_checkpoint:
            lines.append(f"<b>Checkpoint الحالى:</b> <code>{html_escape(self.latest_handoff_checkpoint)}</code>")
        if self.latest_handoff_url:
            lines.append(f"<b>رابط handoff:</b> {html_escape(self.latest_handoff_url)}")
        if self.final_note:
            lines.append(f"<b>ملاحظة:</b> {html_escape(self.final_note)}")
        return "\n".join(lines)


def render_account_selection_live_text(event: dict, project_name: str = "") -> str:
    renderer = AccountSelectionLiveRenderer(project_key=str(event.get("project_key") or ""), project_name=project_name)
    return renderer.apply(event)


def render_account_selection_handoff_text(event: dict, project_name: str = "") -> str:
    continuation_prompt_public = summarize_resume_prompt_for_display(event.get("continuation_prompt_public"))
    return "\n".join(
        part for part in [
            f"🔁 <b>تم تجهيز handoff إلى برومبت الاستئناف «{html_escape(continuation_prompt_public)}»</b>",
            f"<b>المشروع:</b> {html_escape(project_name)}" if project_name else "",
            f"<b>مفتاح المشروع:</b> <code>{html_escape(str(event.get('project_key') or ''))}</code>" if event.get("project_key") else "",
            f"<b>الحساب الحالي:</b> <code>{html_escape(str(event.get('selected_account_email') or ''))}</code>" if event.get("selected_account_email") else "",
            f"<b>Checkpoint:</b> <code>{html_escape(str(event.get('checkpoint_id') or ''))}</code>" if event.get("checkpoint_id") else "",
            f"<b>برومبت الاستئناف:</b> <code>{html_escape(continuation_prompt_public)}</code>",
            f"<b>رابط handoff:</b> {html_escape(str(event.get('continuation_url') or ''))}" if event.get("continuation_url") else "",
            "<b>الوضع:</b> لم يكتمل المشروع بعد؛ تم الوصول فقط إلى نقطة handoff الحالية وفق `D-012`."
        ]
        if part
    )


class AccountSelectionLiveTransport:
    """ينقل observer events إلى رسالة Telegram واحدة قابلة للتعديل بأقل تغيير."""
    def __init__(self, chat_id: int | str, project_key: str, project_name: str):
        self.chat_id = chat_id
        self.project_key = str(project_key or "")
        self.project_name = str(project_name or "")
        self.message_id = None
        self.last_text = ""
        self.renderer = AccountSelectionLiveRenderer(project_key=self.project_key, project_name=self.project_name)
        self.sent_handoff_signatures: set[str] = set()

    def publish(self, event: dict) -> bool:
        text = self.renderer.apply(event)
        send_ok = False
        if self.message_id:
            edited = edit_telegram_message_text(self.chat_id, self.message_id, text)
            if edited.get("ok"):
                self.last_text = text
                send_ok = True
        if not send_ok:
            sent = send_telegram_message_detailed(self.chat_id, text)
            if sent.get("ok") and sent.get("message_id") is not None:
                self.message_id = sent.get("message_id")
                self.last_text = text
                send_ok = True
            else:
                send_ok = bool(sent.get("ok"))
        if str(event.get("event") or "") == "continuation-handoff-ready":
            signature = f"{event.get('attempt_number')}:{event.get('checkpoint_id')}:{event.get('continuation_url')}"
            if signature not in self.sent_handoff_signatures:
                self.sent_handoff_signatures.add(signature)
                send_ok = bool(send_telegram_message_detailed(self.chat_id, render_account_selection_handoff_text(event, project_name=self.project_name)).get("ok")) and send_ok
        return send_ok


def attach_account_selection_live_transport(bridge_cfg, chat_id: int | str, project_key: str, project_name: str):
    if bridge_cfg is None or getattr(bridge_cfg, "account_selection_observer", None):
        return getattr(bridge_cfg, "account_selection_observer", None) if bridge_cfg is not None else None
    transport = AccountSelectionLiveTransport(chat_id=chat_id, project_key=project_key, project_name=project_name)
    bridge_cfg.account_selection_observer = transport.publish
    return transport


# ══════════════════════════════════════════════════════════════
# 📄 [P28] استقبال ملفات المهام (.txt / .md) — Document Ingestion
# ══════════════════════════════════════════════════════════════
# الامتدادات النصية المسموح تحويلها إلى Prompt (تُقارن بعد lower()).
ALLOWED_DOCUMENT_EXTENSIONS = frozenset({".txt", ".md", ".markdown", ".text"})
# حد أقصى وقائي — أكبر منه يُرفض ودياً قبل أي تنزيل (يحمي خيط الـ Polling).
MAX_DOCUMENT_SIZE_BYTES = 5 * 1024 * 1024


def download_telegram_document_text(file_id: str) -> str | None:
    """تنزيل ملف نصي من تليجرام عبر getFile ثم رابط الملف، وإرجاع محتواه كنص UTF-8.

    أي فشل (شبكة / HTTP غير 200 / ok=false / file_path مفقود) يُرجع None
    بدون أي استثناء يتسرب لخيط الـ Polling — التنبيه الودي مسؤولية المستدعي.
    """
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "توكن البوت غير مضبوط — لا يمكن تنزيل الملفات")
        return None
    try:
        import requests
        meta_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"
        meta_resp = requests.get(meta_url, params={"file_id": str(file_id)}, timeout=(10, 30))
        if meta_resp.status_code != 200:
            log_event("error", f"getFile فشل: HTTP {meta_resp.status_code} - {meta_resp.text[:200]}")
            return None
        meta = meta_resp.json()
        if not meta.get("ok"):
            log_event("error", f"getFile أعاد ok=false: {str(meta)[:200]}")
            return None
        file_path = (meta.get("result") or {}).get("file_path") or ""
        if not file_path:
            log_event("error", "getFile نجح لكن file_path مفقود — لا يمكن التنزيل")
            return None
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        file_resp = requests.get(file_url, timeout=(10, 60))
        if file_resp.status_code != 200:
            log_event("error", f"تنزيل الملف فشل: HTTP {file_resp.status_code}")
            return None
        # errors="replace" يضمن عدم الانهيار على بايتات غير UTF-8 (ترميزات قديمة).
        return file_resp.content.decode("utf-8", errors="replace")
    except Exception as err:
        log_event("error", f"استثناء أثناء تنزيل الملف من تليجرام: {err}")
        return None


def send_telegram_document(
    chat_id: int | str,
    document_path: str | pathlib.Path,
    caption: str | None = None,
    max_attempts: int = 3
) -> bool:
    """رفع ملف إلى تليجرام مع إعادة فتح الملف وإعادة المحاولة عند انقطاع الاتصال."""
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "توكن البوت غير مضبوط — لا يمكن رفع الملفات")
        return False
    doc_p = pathlib.Path(document_path).resolve()
    if not doc_p.exists() or not doc_p.is_file():
        log_event("error", f"الملف المراد رفعه غير موجود: {doc_p}")
        return False

    # حد Bot API الحالي للوثائق؛ الفحص المبكر أوضح من انتظار ConnectionReset مبهم.
    max_document_bytes = 50 * 1024 * 1024
    if doc_p.stat().st_size > max_document_bytes:
        log_event("error", f"الملف أكبر من حد تليجرام للبوتات (50 MB): {doc_p.name}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    attempts = max(1, int(max_attempts))
    for upload_attempt in range(1, attempts + 1):
        log_event("info", f"جارٍ رفع الملف [{doc_p.name}] إلى تليجرام (Chat: {chat_id}) — محاولة {upload_attempt}/{attempts}...")
        try:
            # يجب فتح الملف داخل كل محاولة: الطلب السابق قد يكون استهلك الـ stream قبل انقطاعه.
            import requests
            with open(doc_p, "rb") as f:
                files = {"document": (doc_p.name, f, "application/gzip")}
                data = {"chat_id": str(chat_id)}
                if caption:
                    data["caption"] = caption[:1024]
                    data["parse_mode"] = "HTML"
                r = requests.post(url, data=data, files=files, timeout=(20, 600))
            if r.status_code == 200:
                log_event("success", f"تم رفع الملف [{doc_p.name}] إلى تليجرام بنجاح!")
                return True
            # أخطاء 4xx (عدا rate limit) لن تنجح بإعادة نفس الطلب.
            log_event("error", f"فشل رفع الملف: HTTP {r.status_code} - {r.text[:300]}")
            if 400 <= r.status_code < 500 and r.status_code != 429:
                return False
        except Exception as err:
            log_event("warning", f"انقطع/فشل رفع الملف (محاولة {upload_attempt}/{attempts}): {err}")

        if upload_attempt < attempts:
            delay = min(20, 2 ** upload_attempt) + random.uniform(0, 0.75)
            log_event("info", f"إعادة محاولة رفع الملف بعد {delay:.1f} ثانية...")
            time.sleep(delay)

    log_event("error", f"تعذر رفع الملف [{doc_p.name}] بعد {attempts} محاولات")
    return False

# ══════════════════════════════════════════════════════════════
# 🌳 [Task-2] شجرة التفريعات وعلم انتهاء المشروع
# ══════════════════════════════════════════════════════════════
def save_project_branch(
    parent_id: str | None,
    child_id: str,
    title: str = "تحديث محادثة",
    model: str = "claude-fable-5",
    status: str = "COMPLETED"
) -> bool:
    """حفظ شجرة تفريع المشروع (parent_pid -> child_pid) في projects_tree.json"""
    tree_data = {}
    if PROJECTS_TREE_FILE.exists():
        try:
            with open(PROJECTS_TREE_FILE, "r", encoding="utf-8", errors="ignore") as f:
                tree_data = json.load(f)
        except Exception:
            tree_data = {}
    root_key = parent_id or child_id
    if root_key not in tree_data:
        tree_data[root_key] = {
            "root_id": root_key,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "branches": []
        }
    safe_title = summarize_resume_prompt_for_display(title, limit=30)
    branch_entry = {
        "project_id": child_id,
        "parent_id": parent_id,
        "title": safe_title,
        "model": model,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    existing_ids = [b.get("project_id") for b in tree_data[root_key]["branches"]]
    if child_id not in existing_ids:
        tree_data[root_key]["branches"].append(branch_entry)
    try:
        tmp_file = PROJECTS_TREE_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(PROJECTS_TREE_FILE)
        return True
    except Exception as err:
        log_event("warning", f"تنبيه أثناء حفظ شجرة التفريع: {err}")
        return False


def get_project_branches(root_id: str) -> list[dict]:
    """استرجاع نقاط الاستئناف والتفريعات لمشروع معين"""
    if not PROJECTS_TREE_FILE.exists():
        return []
    try:
        with open(PROJECTS_TREE_FILE, "r", encoding="utf-8", errors="ignore") as f:
            tree_data = json.load(f)
        return tree_data.get(root_id, {}).get("branches", [])
    except Exception:
        return []


def check_project_finished_flag(status: str, response_text: str | None = None) -> bool:
    """كشف علم اكتمال انتهاء المشروع PROJECT_FINISHED_FLAG"""
    if status == "COMPLETED":
        return True
    if response_text:
        text_lower = response_text.lower()
        if "تم التنفيذ" in text_lower or "جاهزة للعب" in text_lower or "project completed" in text_lower:
            return True
    return False


def get_random_email_from_accounts_genspark(json_path: str | None = None) -> dict | None:
    accounts = read_accounts_safe(json_path)
    active_accounts = [
        acc for acc in accounts
        if isinstance(acc, dict) and acc.get("email") and is_account_ready(acc)
    ]
    if not active_accounts:
        return None
    chosen = random.choice(active_accounts)
    return reactivate_account_if_due(chosen, json_path=json_path)


# ══════════════════════════════════════════════════════════════
# 🧠 كشف حالة الرد — نسخة محصّنة ضد الكلمات العامة
# ══════════════════════════════════════════════════════════════
SESSION_EXPIRED_KEYWORDS = ["401", "unauthorized", "session expired", "session منتهية", "login required", "not logged in"]
FORBIDDEN_KEYWORDS = ["403", "forbidden", "not authorized", "permission denied", "access denied"]
CREDIT_EXHAUSTED_KEYWORDS = [
    "your credit balance is negative", "this run was stopped", "please top up to continue",
    "you've used all your credits", "used all your credits", "credits are insufficient",
    "action_credit_exhausted", "__credit_exhausted__", "upgrade to continue", "out of credits",
    "كريدت منتهية"
]
# علامات التوليد الجزئي — تُستخدم فقط للنصوص القصيرة جداً (أقل من 60 حرفاً)
PARTIAL_GENERATION_MARKERS = ["thinking", "processing", "generating", "بيفكر", "جاري", "جارٍ"]
# 🧬 [P20] خطأ AI Data Retention — يُعامل كحساب منتهي الرصيد (تبريد + انتقال لحساب آخر)
# مع تنبيه مميز + إعادة إرسال «نفس آخر رسالة» المستخدمة في نفس الحساب كما هي.
DATA_RETENTION_KEYWORDS = [
    "ai data retention", "requires ai data retention",
    "data retention to be enabled", "turn on ai data retention",
]


def detect_response_status(response: str | dict | None) -> str:
    """
    كشف واستخراج حالة الرد بدقة بين SESSION_EXPIRED, FORBIDDEN, CREDIT_EXHAUSTED,
    DATA_RETENTION (🧬 P20), RUNNING, COMPLETED.
    ⚠️ الإصلاح: كلمات مثل running/processing/thinking في ردود مكتملة طويلة (مثل: "الموقع شغال running")
    كانت تسبب RUNNING كاذب → تعليق حتى TIMEOUT. الآن RUNNING تُحتسب فقط للنصوص القصيرة جداً
    التي تُمثل مرحلة توليد فعلية، وأي نص غير قصير يعتبر COMPLETED افتراضياً.
    """
    if not response:
        return "EMPTY"

    text = json.dumps(response, ensure_ascii=False) if isinstance(response, dict) else str(response)
    t = text.lower()
    check_text = t[-3500:] if len(t) > 3500 else t

    # 🧬 [P20] فحص Data Retention أولاً — أكثر تحديداً من باقي الفئات
    if any(kw in check_text for kw in DATA_RETENTION_KEYWORDS):
        return "DATA_RETENTION"
    if any(kw in check_text for kw in SESSION_EXPIRED_KEYWORDS):
        return "SESSION_EXPIRED"
    if any(kw in check_text for kw in FORBIDDEN_KEYWORDS):
        return "FORBIDDEN"
    if any(kw in check_text for kw in CREDIT_EXHAUSTED_KEYWORDS):
        return "CREDIT_EXHAUSTED"

    if len(check_text.strip()) < 2:
        return "EMPTY"

    # RUNNING فقط للنصوص القصيرة جداً (<25 حرف) أو التي تبدأ بعلامة توليد فعلية
    # (مثل "thinking..." أو "جاري التوليد") — أي رد مكتمل مهما احتوى على
    # كلمات عامة مثل processing/running/جاري يُعتبر COMPLETED
    stripped = check_text.strip()
    if stripped:
        is_very_short = len(stripped) < 25
        starts_with_marker = any(stripped.startswith(kw) for kw in PARTIAL_GENERATION_MARKERS)
        if (is_very_short or starts_with_marker) and any(kw in stripped for kw in PARTIAL_GENERATION_MARKERS):
            return "RUNNING"

    return "COMPLETED"


# ══════════════════════════════════════════════════════════════
# 🚫 [P35] كشف رفض الموديل (Model Decline Recovery)
# ══════════════════════════════════════════════════════════════
# الرد "The model declined to answer this request..." يصل بطول > 25 حرفاً
# فيُحتسب COMPLETED في detect_response_status — وهذا صحيح تقنياً (المهمة
# انتهت فعلاً) لكنه خاطئ دلالياً: لا يوجد ناتج، والأسوأ أن مؤشر الاستئناف
# كان يتقدم لنقطة "الرفض". فلسفة P35: الرفض يُعامل «كأن الطلب لم يُرسل».
#
# ⚠️ حارس False Positive: الكشف يعمل فقط للردود القصيرة
# (≤ MODEL_DECLINE_MAX_RESPONSE_CHARS) — أي رد طويل شرعي *يقتبس* جملة
# الرفض داخله لا يُحتسب رفضاً أبداً (نفس فلسفة إصلاح RUNNING الكاذب).
MODEL_DECLINE_MARKERS = [
    "the model declined to answer this request",
    "model declined to answer",
    "declined to answer this request",
    "the model declined to respond",
    "model declined this request",
]
MODEL_DECLINE_MAX_RESPONSE_CHARS = 300
MODEL_DECLINED_STATUS = "MODEL_DECLINED"


def is_model_decline_response(response_text: str | None) -> bool:
    """🚫 [P35] هل هذا الرد رفض صريح من الموديل؟

    True فقط إذا: الرد غير فارغ + قصير (≤ 300 حرف بعد strip) + جوهره
    إحدى عبارات الرفض المعتمدة. الردود الطويلة تُستبعد فوراً حتى لو
    احتوت العبارة (اقتباس داخل رد شرعي ≠ رفض).
    """
    text = str(response_text or "").strip()
    if not text:
        return False
    if len(text) > MODEL_DECLINE_MAX_RESPONSE_CHARS:
        return False
    low = text.lower()
    return any(marker in low for marker in MODEL_DECLINE_MARKERS)


# ══════════════════════════════════════════════════════════════
# ⛳ [P18] مراقب مؤشر النشاط الحي (Deep Thinking / Tasks Remaining)
# لو المؤشر اتغيّر أثناء المتابعة → وقف فوري (مفيش أي تكملة على مهام جديدة)
# ══════════════════════════════════════════════════════════════
DEEP_THINKING_MARKERS = ["deep thinking", "deep-thinking", "deepthinking"]
TASKS_REMAINING_PATTERN = re.compile(r"tasks?\s*remaining\D{0,16}?(\d+)|(\d+)\s*tasks?\s*remaining", re.IGNORECASE)
TASKS_REMAINING_TEXT_MARKERS = ["tasks remaining", "task remaining", "tasks left", "task left"]


def extract_activity_signature(page_text: str | None) -> dict:
    """
    ⛳ [P18] يستخرج بصمة مؤشر النشاط من نص صفحة المشروع (/agents?id=PID):
      - deep_thinking: هل مؤشر Deep Thinking ظاهر؟
      - tasks_remaining: عدد المهام المتبقية إن وُجد رقم (وإلا -1 لو النص موجود بدون رقم، None لو غير موجود)
      - active: هل يوجد أي مؤشر توليد حي (Deep Thinking أو Tasks Remaining)؟
    """
    text = str(page_text or "")
    low = text.lower()
    deep = any(m in low for m in DEEP_THINKING_MARKERS)
    tasks = None
    m = TASKS_REMAINING_PATTERN.search(low)
    if m:
        num = m.group(1) or m.group(2)
        try:
            tasks = int(num)
        except (TypeError, ValueError):
            tasks = -1
    elif any(k in low for k in TASKS_REMAINING_TEXT_MARKERS):
        tasks = -1
    return {
        "deep_thinking": deep,
        "tasks_remaining": tasks,
        "active": bool(deep or tasks is not None),
    }


def fetch_project_activity_signature(project_id: str, cookies: dict) -> dict | None:
    """
    ⛳ [P18] يجلب صفحة المشروع الحية ويستخرج بصمة مؤشر Deep Thinking / Tasks Remaining.
    يرجع None عند أي فشل شبكة/HTTP حتى لا يؤثر إطلاقاً على حلقة المتابعة الأساسية.
    """
    if not project_id:
        return None
    try:
        from curl_cffi import requests as cffi
        sess = cffi.Session(impersonate="chrome120")
        sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Referer": "https://www.genspark.ai/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        for name, val in (cookies or {}).items():
            sess.cookies.set(str(name), str(val), domain="www.genspark.ai")
        r = sess.get(f"https://www.genspark.ai/agents?id={project_id}", timeout=30)
        if getattr(r, "status_code", 0) != 200:
            return None
        return extract_activity_signature(getattr(r, "text", "") or "")
    except Exception:
        return None


def should_stop_on_activity_change(prev: dict | None, curr: dict | None) -> tuple[bool, str]:
    """
    ⛳ [P18] قرار الوقف الفوري: أي تغيّر في مؤشر Deep Thinking / Tasks Remaining = وقف فوراً.
      1. المؤشر كان ظاهراً (active) ثم اختفى تماماً → وقف فوري.
      2. عدد Tasks Remaining اتغيّر بأي شكل (زيادة أو نقصان) → المهام اتغيرت → وقف فوري
         (المطلوب صراحةً: لو المهام اتغيرت مفيش أي تكملة).
      3. مؤشر Deep Thinking اتقلب (ظهر/اختفى مع بقاء النشاط) → وقف فوري.
      4. لو مفيش بصمة سابقة نشطة → لا قرار (لسه بنلتقط الـ baseline).
    ملاحظة صريحة: أي تغيّر في العدد — حتى النقصان — يعني المهام اتغيرت → وقف فوري، مفيش أي تكملة.
    """
    if not prev or not curr:
        return False, ""
    if not prev.get("active"):
        return False, ""
    if not curr.get("active"):
        return True, "activity-indicator-disappeared"
    # ⛳ [P18] المطلوب صراحةً: أي تغيّر في المهام = وقف فوري (زيادة أو نقصان — مفيش تكملة)
    prev_tasks = prev.get("tasks_remaining")
    curr_tasks = curr.get("tasks_remaining")
    if prev_tasks != curr_tasks:
        return True, "tasks-remaining-changed"
    if bool(prev.get("deep_thinking")) != bool(curr.get("deep_thinking")):
        return True, "deep-thinking-changed"
    return False, ""


def extract_project_id(url_or_id: str) -> str:
    if not url_or_id:
        return ""
    url_str = str(url_or_id).strip()
    match = re.search(r"id=([a-f0-9\-]{36})", url_str, re.IGNORECASE)
    if match:
        return match.group(1)
    uuid_match = re.search(r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})", url_str, re.IGNORECASE)
    if uuid_match:
        return uuid_match.group(1)
    return url_str


# ══════════════════════════════════════════════════════════════
# 📦 فك الأرشيف الآمن (إصلاح Tar-Slip / Path Traversal)
# ══════════════════════════════════════════════════════════════
def _is_safe_archive_member_name(member_name: str) -> bool:
    """رفض أي مسار مطلق أو متجاوز (../) أو حرف درايف (C:) داخل الأرشيف"""
    if not member_name:
        return False
    name = member_name.replace("\\", "/")
    if name.startswith("/"):
        return False
    if re.match(r"^[A-Za-z]:", name):
        return False
    # مدخلات الجذر مثل "./" طبيعية في tar الذي ينشئه GNU tar وليست Path Traversal.
    parts = [p for p in name.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        return False
    return True


def _archive_signature_label(archive_bytes: bytes) -> str:
    head = archive_bytes[:8]
    if head.startswith(b"PK\x03\x04"):
        return "zip"
    if head.startswith(b"\x1f\x8b"):
        return "gzip"
    if len(archive_bytes) >= 262 and archive_bytes[257:262] == b"ustar":
        return "tar"
    return "unknown"


def _archive_diag(ok: bool, archive_type: str, reason_code: str = "", member: str = "", detail: str = "") -> dict:
    return {
        "ok": ok,
        "archive_type": archive_type,
        "reason_code": reason_code,
        "member": member,
        "detail": detail[:240],
    }


def _should_skip_archive_member(rel_path: str) -> bool:
    """تخطي node_modules والمجلدات المؤقتة والـ cache لتقليل الحجم وتفادي أخطاء symlink"""
    parts = pathlib.PurePosixPath(str(rel_path or "").replace("\\", "/")).parts
    skip_dirs = {"node_modules", ".git", ".cache", "__pycache__", ".npm", ".wrangler"}
    return any(p in skip_dirs for p in parts)


def _is_never_copy_file(filename: str) -> bool:
    """منع نسخ ملفات الأسرار والبيانات الحساسة والأرشيفات الخام إلى المستودع (مستوحى من 04_upload)"""
    f = str(filename or "").lower()
    if f.endswith((".tar.gz", ".tar", ".zip", ".failed")):
        return True
    if f.startswith(".env") or f in ("accounts_genspark.json", "accounts_qwen.json", "accounts_deepseek.json", "keys.txt"):
        return True
    return False


def _resolve_effective_source_root(sandbox_dir: pathlib.Path | None) -> pathlib.Path | None:
    """تحديد جذر الكود الفعلي داخل مجلد الساندبوكس المفكوك لتسطيح المجلدات الفرعية (webapp/repo/clone) (مستوحى من 04_upload get_source_root)"""
    if not sandbox_dir or not sandbox_dir.exists():
        return None
    entries = [p for p in sandbox_dir.iterdir() if not p.name.startswith(".") and not p.name.endswith((".tar.gz", ".zip"))]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    for p in entries:
        if p.is_dir() and any(kw in p.name.lower() for kw in ("webapp", "clone", "repo")):
            return p
    return sandbox_dir


def _extract_archive_with_diagnostics(archive_bytes: bytes, out_dir: pathlib.Path) -> dict:
    """فك archive مع استبعاد node_modules وتخطي symlinks بأمان مع الحفاظ على ملفات المشروع والتوثيق."""
    import io
    import tarfile
    import zipfile

    tar_err = ""
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:*") as tf:
            safe_members = []
            for member in tf.getmembers():
                if not _is_safe_archive_member_name(member.name):
                    return _archive_diag(False, "tar", "ARCHIVE_TAR_UNSAFE_PATH", member=member.name)
                if _should_skip_archive_member(member.name):
                    continue
                # تخطي الروابط الرمزية بأمان دون إيقاف باقي ملفات الأرشيف
                if member.issym() or member.islnk():
                    continue
                if member.isfile() or member.isdir():
                    safe_members.append(member)
            if not safe_members:
                return _archive_diag(True, "tar")
            try:
                tf.extractall(str(out_dir), members=safe_members, filter="data")
            except TypeError:
                tf.extractall(str(out_dir), members=safe_members)
            except Exception as err:
                return _archive_diag(False, "tar", "ARCHIVE_TAR_EXTRACT_ERROR", detail=f"{type(err).__name__}: {str(err)[:160]}")
        return _archive_diag(True, "tar")
    except Exception as err:
        tar_err = f"{type(err).__name__}: {str(err)[:160]}"

    zip_err = ""
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
            safe_infos = []
            for info in zf.infolist():
                if not _is_safe_archive_member_name(info.filename):
                    return _archive_diag(False, "zip", "ARCHIVE_ZIP_UNSAFE_PATH", member=info.filename)
                if _should_skip_archive_member(info.filename):
                    continue
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    continue
                safe_infos.append(info)
            try:
                for info in safe_infos:
                    zf.extract(info, str(out_dir))
            except Exception as err:
                return _archive_diag(False, "zip", "ARCHIVE_ZIP_EXTRACT_ERROR", detail=f"{type(err).__name__}: {str(err)[:160]}")
        return _archive_diag(True, "zip")
    except Exception as err:
        zip_err = f"{type(err).__name__}: {str(err)[:160]}"

    signature = _archive_signature_label(archive_bytes)
    return _archive_diag(
        False,
        signature,
        "ARCHIVE_UNSUPPORTED_FORMAT",
        detail=f"signature={signature}; tar={tar_err or 'n/a'}; zip={zip_err or 'n/a'}",
    )


def format_archive_diagnostic(diag: dict, archive_name: str) -> str:
    code = diag.get("reason_code") or "ARCHIVE_UNKNOWN"
    archive_type = diag.get("archive_type") or "unknown"
    parts = [f"فشل فك ضغط الأرشيف [{archive_type}/{code}]"]
    if diag.get("member"):
        parts.append(f"member={diag['member']}")
    if diag.get("detail"):
        parts.append(f"detail={diag['detail']}")
    parts.append(f"تم حفظ الملف الخام فقط: {archive_name}")
    return " | ".join(parts)


def download_project_archive(
    project_id: str,
    cookies: dict,
    out_dir: str | pathlib.Path | None = None,
    remote_path: str = "/home/user/webapp",
    email: str = "default@genspark.ai",
    bridge_cfg: BridgeConfig | None = None
) -> str | None:
    if not project_id or not cookies:
        return None
    if bridge_cfg is not None:
        default_dir = bridge_cfg.extracted_webapp_dir
    else:
        default_dir = SCRIPT_DIR / "extracted_webapp"
    out_dir = default_dir if out_dir is None else pathlib.Path(out_dir).resolve()
    os.makedirs(str(out_dir), exist_ok=True)
    tar_path = out_dir / "webapp.tar.gz"
    url = "https://www.genspark.ai/api/code_sandbox/download_directory"
    params = {"project_id": project_id, "path": remote_path}
    try:
        from curl_cffi import requests as cffi
        fp = get_account_fingerprint(email)
        browser = getattr(bridge_cfg, "current_browser", fp["browser"])
        ua = getattr(bridge_cfg, "user_agent", fp["user_agent"])
        try:
            sess = cffi.Session(impersonate=browser) if hasattr(cffi, "Session") else cffi.Session()
        except Exception:
            sess = cffi.Session(impersonate="chrome120") if hasattr(cffi, "Session") else cffi.Session()
        sess.headers.update({"User-Agent": ua, "Referer": "https://www.genspark.ai/"})
        for k, v in cookies.items():
            if hasattr(sess.cookies, "set"):
                sess.cookies.set(str(k), str(v), domain=".genspark.ai")
            else:
                sess.cookies[str(k)] = str(v)
        r = sess.get(url, params=params, timeout=180)
        if r.status_code == 200 and len(r.content) > 50:
            with open(tar_path, "wb") as f:
                f.write(r.content)
            archive_diag = _extract_archive_with_diagnostics(r.content, out_dir)
            if not archive_diag.get("ok"):
                log_event("warning", format_archive_diagnostic(archive_diag, tar_path.name), extra=archive_diag)
            return str(tar_path)
    except Exception as e:
        log_event("error", f"فشل تحميل أرشيف المشروع: {e}")
    return None


def make_project_always_public(
    project_id: str,
    cookies: dict,
    mod: any = None,
    cfg: any = None,
    email: str = "default@genspark.ai",
    bridge_cfg: BridgeConfig | None = None
) -> str:
    if not project_id:
        return ""
    public_url = f"https://www.genspark.ai/autopilotagent_viewer?id={project_id}"
    if mod and hasattr(mod, "ensure_public"):
        try:
            pub_res = mod.ensure_public(project_id, cookies, cfg, label="telegram_gen_bridge")
            if pub_res and "genspark.ai" in pub_res:
                return pub_res
        except Exception:
            pass
    try:
        from curl_cffi import requests as cffi
        fp = get_account_fingerprint(email)
        browser = getattr(bridge_cfg, "current_browser", fp["browser"])
        ua = getattr(bridge_cfg, "user_agent", fp["user_agent"])
        try:
            sess = cffi.Session(impersonate=browser) if hasattr(cffi, "Session") else cffi.Session()
        except Exception:
            sess = cffi.Session(impersonate="chrome120") if hasattr(cffi, "Session") else cffi.Session()
        sess.headers.update({
            "User-Agent": ua,
            "Referer": "https://www.genspark.ai/",
            "Content-Type": "application/json"
        })
        for k, v in cookies.items():
            if hasattr(sess.cookies, "set"):
                sess.cookies.set(str(k), str(v), domain=".genspark.ai")
            else:
                sess.cookies[str(k)] = str(v)
        make_public_urls = [
            f"https://www.genspark.ai/api/code_sandbox/make_public?project_id={project_id}",
            "https://www.genspark.ai/api/code_sandbox/make_public",
            "https://www.genspark.ai/api/share_project"
        ]
        for api_u in make_public_urls:
            try:
                res = sess.post(api_u, json={"project_id": project_id, "is_public": True}, timeout=15)
                if res.status_code in (200, 201):
                    log_event("success", f"تم تحويل المشروع [{project_id[:12]}] إلى Public عام بنجاح!")
                    break
            except Exception:
                pass
    except Exception as pub_err:
        log_event("warning", f"تنبيه النشر العام: {pub_err}")
    return public_url


def get_public_forked_pid(
    orig_pid: str,
    cookies: dict,
    mod: any = None,
    cfg: any = None,
    email: str = "default@genspark.ai",
    bridge_cfg: BridgeConfig | None = None
) -> str | None:
    if not orig_pid:
        return None
    if mod and hasattr(mod, "create_forked_project"):
        try:
            fk_pid = mod.create_forked_project(orig_pid, cookies, cfg)
            if fk_pid and fk_pid != "__INVALID_PROJECT__":
                return fk_pid
        except Exception:
            pass
    try:
        from curl_cffi import requests as cffi
        fp = get_account_fingerprint(email)
        browser = getattr(bridge_cfg, "current_browser", fp["browser"])
        ua = getattr(bridge_cfg, "user_agent", fp["user_agent"])
        sess = cffi.Session(impersonate=browser) if hasattr(cffi, "Session") else cffi.Session()
        sess.headers.update({
            "User-Agent": ua,
            "Referer": "https://www.genspark.ai/"
        })
        for name, val in cookies.items():
            if hasattr(sess.cookies, "set"):
                sess.cookies.set(str(name), str(val), domain="www.genspark.ai")
            else:
                sess.cookies[str(name)] = str(val)
        r = sess.get(f"https://www.genspark.ai/api/continue_conversation?id={orig_pid}", allow_redirects=False, timeout=20)
        if r.status_code in (301, 302, 307, 308, 200):
            loc = r.headers.get("location", "") or r.text
            if loc and "/login" not in loc:
                fk_pid = extract_project_id(loc)
                if fk_pid and fk_pid != orig_pid and "login" not in fk_pid and len(fk_pid) > 10:
                    log_event("success", f"تم التفريع بنجاح: {fk_pid[:16]}...", email=email)
                    return fk_pid
    except Exception:
        pass
    try:
        from curl_cffi import requests as cffi
        fp = get_account_fingerprint(email)
        browser = getattr(bridge_cfg, "current_browser", fp["browser"])
        ua = getattr(bridge_cfg, "user_agent", fp["user_agent"])
        clean_sess = cffi.Session(impersonate=browser) if hasattr(cffi, "Session") else cffi.Session()
        clean_sess.headers.update({
            "User-Agent": ua,
            "Referer": "https://www.genspark.ai/"
        })
        r = clean_sess.get(f"https://www.genspark.ai/api/continue_conversation?id={orig_pid}", allow_redirects=False, timeout=20)
        if r.status_code in (301, 302, 307, 308, 200):
            loc = r.headers.get("location", "") or r.text
            if loc and "/login" not in loc:
                fk_pid = extract_project_id(loc)
                if fk_pid and fk_pid != orig_pid and "login" not in fk_pid and len(fk_pid) > 10:
                    log_event("success", f"تم التفريع المباشر بدون 403: {fk_pid[:16]}...", email=email)
                    return fk_pid
    except Exception as pub_fk_err:
        log_event("warning", f"تنبيه التفريع العام: {pub_fk_err}", email=email)
    return None


def send_message_and_make_public(
    url: str | None,
    email: str,
    password: str,
    query: str,
    bridge_cfg: BridgeConfig | None = None,
    json_path: str | None = None,
    on_project_start_callback=None,
) -> tuple[str | None, str, str | None, str | None, str | None]:
    if bridge_cfg is None:
        bridge_cfg = BridgeConfig()
    max_retries = max(1, getattr(bridge_cfg, "max_timeout_retries", 2))
    session_timeout = getattr(bridge_cfg, "session_timeout", 1000)

    mod = get_genspark_engine()
    if not mod:
        return None, "NO_ENGINE", None, None, None

    # ⚡ [P12] carry_pid: أي project_id يُلتقط (من project_start أو من رجوع send_chat)
    # يُحفظ هنا ويُستأنف عليه في أي محاولة تالية — ممنوع إنشاء شات/ID جديد بعد الانقطاع.
    carry_pid = None

    # 🌐 [P16] Early Make-Public: بمجرد التقاط project_id حي — نحوّل المشروع إلى Public
    # فوراً في خيط خلفي (Fire-and-Forget) قبل/مع إرسال زر المعاينة الفورية،
    # حتى يعمل رابط المعاينة الحية من أول ثانية بدلاً من انتظار اكتمال التوليد.
    # مرة واحدة فقط لكل pid — بدون أي تأخير للبث الرئيسي.
    early_public_pids: set = set()
    cookies: dict = {}
    cfg = None

    def _early_make_public_async(live_pid: str):
        if not live_pid or str(live_pid).startswith("__") or live_pid in early_public_pids:
            return
        early_public_pids.add(live_pid)
        snapshot_cookies = dict(cookies) if isinstance(cookies, dict) else {}
        snapshot_cfg = cfg

        def _worker():
            try:
                make_project_always_public(
                    live_pid, snapshot_cookies, mod=mod, cfg=snapshot_cfg,
                    email=email, bridge_cfg=bridge_cfg,
                )
                log_event("info", f"🌐 [P16] المشروع {str(live_pid)[:12]}… أصبح Public مبكراً — زر المعاينة يعمل فوراً", email=email)
            except Exception as early_pub_err:
                log_event("warning", f"[P16] تعذر النشر العام المبكر: {early_pub_err}", email=email)

        try:
            threading.Thread(target=_worker, daemon=True, name=f"early-public-{str(live_pid)[:8]}").start()
        except Exception:
            pass

    def _pid_capture_callback(live_pid):
        nonlocal carry_pid
        if live_pid and not str(live_pid).startswith("__"):
            carry_pid = live_pid
            # [P16] النشر العام فور معرفة الـ pid — قبل أي انتظار لاكتمال التوليد
            _early_make_public_async(live_pid)
        if on_project_start_callback is not None:
            try:
                on_project_start_callback(live_pid)
            except Exception:
                pass

    for attempt in range(1, max_retries + 1):
        cfg = getattr(mod, "Config")()
        cfg.model = bridge_cfg.model
        fp = get_account_fingerprint(email)
        user_agent_str = fp["user_agent"]
        try:
            cfg.user_agent = user_agent_str
            cfg.headers = {"User-Agent": user_agent_str}
        except Exception:
            pass

        cfg.use_ultra = False
        cfg.agent_type = bridge_cfg.agent_type
        cfg.request_web_knowledge = needs_web_search(query)
        # 🛑 [P25] حقن حدث الإلغاء في cfg المحرك — send_chat يفحصه كل سطر SSE
        # ويقطع البث فوراً (r.close) بنفس تأثير زر ⏹️ Stop في واجهة جينسبارك.
        _cancel_event = getattr(bridge_cfg, "cancel_event", None)
        try:
            cfg.cancel_event = _cancel_event
        except Exception:
            pass
        # 🛑 [P25] إلغاء طُلب قبل بدء المحاولة أصلاً → خروج فوري بدون أي إرسال
        if _cancel_event is not None and _cancel_event.is_set():
            log_event("warning", "🛑 [P25] إلغاء المستخدم قبل بدء المحاولة — خروج فوري بدون إرسال", email=email)
            return None, CANCELLED_STATUS, None, None, None
        project_id, history = None, []

        accounts = read_accounts_safe(json_path)
        acc = next((a for a in accounts if isinstance(a, dict) and a.get("email") == email), None)
        cookies = acc.get("cookies", {}) if acc else {}

        # ⚡ فحص مسبق وتجديد الجلسة بـ REFRESH_LOCK منفرد للإيميل
        # إصلاح: لو تم تجديد الكوكيز قبل أقل من 120 ثانية نتخطى الفحص المسبق
        # لمنع التكرار المزدوج للمحاولة (كان يظهر مرتين في اللوج لكل حساب).
        last_refresh = 0
        if acc:
            try:
                last_refresh = float(acc.get("last_refresh") or 0)
            except Exception:
                last_refresh = 0

        # 💰 [P13] Pre-Flight Balance Check — قبل لمس الشات أو إرسال أي حرف:
        # دلالات check_balance: >=0 رصيد فعلي | -2 جلسة منتهية | -1 فشل شبكة (لا عقوبة).
        # رصيد فعلي < min_preflight_balance → تبريد 29h فوراً + LOW_BALANCE (لا fork ولا شات).
        _min_balance = int(getattr(bridge_cfg, "min_preflight_balance", 100) or 100)
        cookies_valid = False
        bal_check = -1
        if cookies and isinstance(cookies, dict) and hasattr(mod, "check_balance"):
            try:
                bal_check = mod.check_balance(cookies)
            except Exception:
                bal_check = -1
            if isinstance(bal_check, (int, float)) and bal_check >= 0:
                if bal_check < _min_balance:
                    log_event("warning", f"💰 رصيد منخفض ({int(bal_check)} < {_min_balance}) — تبريد 29h وتخطٍ صامت بدون أي إرسال", email=email)
                    mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                    return None, "LOW_BALANCE", None, None, None
                cookies_valid = True
                try:
                    update_account_data(email, {"balance": int(bal_check)}, json_path=json_path)
                except Exception:
                    pass

        # 💰 [P17] سد ثغرة نافذة الـ 120 ثانية: جلسة منتهية صراحةً (-2) تُجدَّد فوراً
        # حتى لو آخر تجديد كان حديثاً — لأن تخطيها يعني fork/شات بجلسة ميتة بلا فحص رصيد.
        if not cookies_valid and (bal_check == -2 or (time.time() - last_refresh) > 120):
            new_cookies = refresh_cookies_on_401(mod, email, password, json_path=json_path)
            if new_cookies and isinstance(new_cookies, dict):
                cookies = new_cookies
                # [P13] سد ثغرة "جلسة متجددة برصيد فارغ": إعادة فحص الرصيد بالكوكيز الجديدة
                if hasattr(mod, "check_balance"):
                    try:
                        bal_recheck = mod.check_balance(cookies)
                    except Exception:
                        bal_recheck = -1
                    if isinstance(bal_recheck, (int, float)) and 0 <= bal_recheck < _min_balance:
                        log_event("warning", f"💰 رصيد منخفض بعد تجديد الجلسة ({int(bal_recheck)} < {_min_balance}) — تبريد 29h وتخطٍ صامت", email=email)
                        mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                        return None, "LOW_BALANCE", None, None, None
            else:
                update_account_data(email, {"status": "auth_failed", "active": False, "cooldown_until": time.time() + 1800}, json_path=json_path)
                return None, "LOGIN_FAILED", None, None, None

        # ⚡ [P12] لو معانا مشروع ملتقط من محاولة سابقة → نستأنف عليه مباشرة
        # (بدون fork جديد وبدون شات جديد) — هذا جوهر إصلاح مشكلة chat id الجديد.
        if carry_pid:
            project_id = carry_pid
            history = []
            log_event("info", f"♻️ استئناف على نفس المشروع الملتقط {str(carry_pid)[:16]}... (محاولة {attempt})", email=email)
            # [P12-C] زر المعاينة الحية يصل فوراً حتى في الاستئناف (السيرفر لا يرسل project_start لمشروع قائم)
            # [P16] النشر العام المبكر قبل/مع إرسال زر المعاينة — الرابط يعمل من أول ضغطة
            _early_make_public_async(project_id)
            if on_project_start_callback is not None:
                try:
                    on_project_start_callback(project_id)
                except Exception:
                    pass
        elif url and isinstance(url, str) and url.strip():
            orig_pid = extract_project_id(url.strip())
            if orig_pid:
                try:
                    history = mod.fetch_project_messages(orig_pid, cookies, cfg)
                except Exception as h_err:
                    if "403" in str(h_err) or "not authorized" in str(h_err).lower():
                        log_event("warning", "تجاوز 403 في جلب الرسائل، جاري التفريع العام...", email=email)
                    history = []
                forked_pid = get_public_forked_pid(orig_pid, cookies, mod=mod, cfg=cfg, email=email, bridge_cfg=bridge_cfg)
                project_id = forked_pid or orig_pid
                # [P12-C] زر المعاينة الحية فور معرفة مشروع الاستئناف/الفورك (لا انتظار لـ project_start)
                # [P16] النشر العام المبكر قبل/مع إرسال زر المعاينة — الرابط يعمل من أول ضغطة
                if project_id:
                    _early_make_public_async(project_id)
                if project_id and on_project_start_callback is not None:
                    try:
                        on_project_start_callback(project_id)
                    except Exception:
                        pass

        start_time = time.time()
        answer, pid, asst_id = None, None, None
        last_chat_err = None
        chat_failed = False

        for chat_attempt in range(2):
            try:
                send_chat_kwargs = {
                    "project_id": project_id,
                    "history": history,
                    "cfg": cfg,
                    # [P12] دائماً نمرر ملتقط الـ pid — حتى لو انقطع البث لاحقاً نعرف المشروع ونستأنف عليه
                    "on_project_start_callback": _pid_capture_callback,
                }
                answer, pid, asst_id = mod.send_chat(cookies, query, email, **send_chat_kwargs)
                break

            except Exception as chat_err:
                err_str = str(chat_err).lower()
                if ("401" in err_str or "unauthorized" in err_str or "session" in err_str) and chat_attempt == 0:
                    log_event("warning", "التقاط 401 أثناء الشات، تجديد الكوكيز وإعادة المحاولة...", email=email)
                    new_cookies = refresh_cookies_on_401(mod, email, password, json_path=json_path)
                    if new_cookies and isinstance(new_cookies, dict):
                        cookies = new_cookies
                        # 💰 [P17] بوابة الرصيد بعد تجديد 401 أثناء الشات — نفس عقد P13:
                        # جلسة متجددة برصيد أقل من العتبة ممنوع تكمل الإرسال (تبريد 29h + LOW_BALANCE صامت).
                        if hasattr(mod, "check_balance"):
                            try:
                                bal_mid = mod.check_balance(cookies)
                            except Exception:
                                bal_mid = -1
                            if isinstance(bal_mid, (int, float)) and 0 <= bal_mid < _min_balance:
                                log_event("warning", f"💰 رصيد منخفض بعد تجديد 401 أثناء الشات ({int(bal_mid)} < {_min_balance}) — تبريد 29h وتخطٍ صامت", email=email)
                                mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                                return None, "LOW_BALANCE", None, None, None
                        time.sleep(1.5)  # مهلة قصيرة لثبات الجلسة الجديدة قبل إعادة الإرسال
                        continue
                chat_failed = True
                last_chat_err = str(chat_err)
                break

        if chat_failed:
            if attempt < max_retries:
                continue
            return None, "CHAT_ERROR", None, None, last_chat_err

        # 🛑 [P25] المحرك قطع البث بناءً على طلب المستخدم → إنهاء فوري بلا retry
        # (الحساب يُحرَّر في finally داخل failover — Zero Resources Leak)
        if answer == USER_CANCELLED_MARKER or (
            _cancel_event is not None and _cancel_event.is_set()
        ):
            log_event("warning", f"🛑 [P25] تم إلغاء البث بواسطة المستخدم — إنهاء المهمة فوراً (pid={str(pid or '')[:16]})", email=email)
            return None, CANCELLED_STATUS, None, None, None

        if not pid or pid == "__INVALID_PROJECT__":
            if attempt < max_retries:
                continue
            return None, "FAILED", None, None, str(answer or "")

        # [P12] تثبيت المشروع الملتقط للمحاولات التالية — لا شات جديد بعد الآن
        carry_pid = pid

        # [P12] انقطاع البث مع مشروع حي → لا نفشل ولا نعيد من الصفر:
        # ندخل حلقة المتابعة (polling) على نفس الـ pid حتى يكتمل التوليد سحابياً.
        if answer == "__STREAM_INTERRUPTED__":
            log_event("warning", f"انقطع بث الرد — متابعة نفس المشروع {str(pid)[:16]}... حتى الاكتمال", email=email)
            final_status = "RUNNING"
            last_resp_text = ""
        else:
            final_status = detect_response_status(answer)
            last_resp_text = str(answer) if answer else ""
        is_timeout = False

        # ⛳ [P18] بصمة مؤشر النشاط (Deep Thinking / Tasks Remaining) — baseline قبل المتابعة
        prev_activity = fetch_project_activity_signature(pid, cookies)

        while final_status not in ("COMPLETED", "CREDIT_EXHAUSTED", "DATA_RETENTION", "SESSION_EXPIRED", "FORBIDDEN"):
            # 🛑 [P25] فحص الإلغاء أول كل دورة متابعة — استجابة شبه فورية للزر
            if _cancel_event is not None and _cancel_event.is_set():
                log_event("warning", f"🛑 [P25] إلغاء المستخدم أثناء متابعة المشروع {str(pid)[:16]} — وقف فوري", email=email)
                return None, CANCELLED_STATUS, None, None, None
            elapsed = time.time() - start_time
            if elapsed > session_timeout:
                is_timeout = True
                break
            # 🛑 [P25] النوم متقطع على حدث الإلغاء نفسه بدل sleep أصم —
            # الضغط على «نعم، إلغاء فوري» يوقظنا خلال < 0.1s بدل انتظار 5s كاملة.
            if _cancel_event is not None:
                if _cancel_event.wait(timeout=5):
                    log_event("warning", f"🛑 [P25] إلغاء المستخدم أثناء الانتظار — وقف فوري (pid={str(pid)[:16]})", email=email)
                    return None, CANCELLED_STATUS, None, None, None
            else:
                time.sleep(5)

            # ⛳ [P18] أهم فحص: لو مؤشر Deep Thinking / Tasks Remaining اتغيّر
            # (اختفى أو دخل مهام جديدة) → وقف فوري — مفيش أي تكملة على مهام اتغيرت.
            curr_activity = fetch_project_activity_signature(pid, cookies)
            if curr_activity is not None:
                stop_now, stop_reason = should_stop_on_activity_change(prev_activity, curr_activity)
                if stop_now:
                    log_event(
                        "warning",
                        f"⛳ [P18] مؤشر النشاط اتغيّر ({stop_reason}) — وقف فوري للمتابعة على المشروع {str(pid)[:16]}",
                        email=email,
                    )
                    final_status = "COMPLETED"
                    break
                prev_activity = curr_activity

            try:
                if hasattr(mod, "fetch_project_messages"):
                    latest_msgs = mod.fetch_project_messages(pid, cookies, cfg)
                    if latest_msgs:
                        # [P12-E] نأخذ آخر رسالة "assistant" فقط — آخر عنصر قد يكون
                        # رسالة المستخدم نفسها بعد انقطاع البث فيُحتسب COMPLETED كاذب
                        # ويعود نص السؤال كأنه الرد!
                        last_asst = next(
                            (m for m in reversed(latest_msgs)
                             if isinstance(m, dict) and m.get("role") == "assistant"),
                            None,
                        )
                        if last_asst:
                            last_c = last_asst.get("content", "")
                            if last_c:
                                last_resp_text = last_c
                            final_status = detect_response_status(last_c)
            except Exception:
                pass

        if is_timeout:
            # إصلاح: لو انتهت المهلة ومعانا نص رد فعلي، نعتبره مكتملاً بدل TIMEOUT
            # (كشف الحالة الجديد لن يعلق على كلمات عامة، لكن يبقى هذا شبكة أمان أخيرة)
            if last_resp_text and str(last_resp_text).strip():
                log_event("warning", "انتهت مهلة الانتظار مع وجود نص رد — سيتم اعتباره مكتملاً", email=email)
                final_status = "COMPLETED"
            else:
                if attempt < max_retries:
                    continue
                return None, "TIMEOUT", None, None, None

        ext_base = pathlib.Path(bridge_cfg.extracted_webapp_dir)
        ext_dir = str(ext_base / pid)
        archive_path = download_project_archive(pid, cookies, out_dir=ext_dir, email=email, bridge_cfg=bridge_cfg)
        final_public_url = make_project_always_public(pid, cookies, mod=mod, cfg=cfg, email=email, bridge_cfg=bridge_cfg)
        save_project_branch(
            parent_id=extract_project_id(url) if url else None,
            child_id=pid,
            title=get_public_continuation_prompt_text(query)[:30],
            model=cfg.model,
            status=final_status,
        )
        return final_public_url, final_status, ext_dir, last_resp_text, None

    return None, "TIMEOUT", None, None, None


def send_message_with_auto_account_failover(
    url: str | None,
    query: str,
    email: str | None = None,
    password: str | None = None,
    bridge_cfg: BridgeConfig | None = None,
    json_path: str | None = None,
    progress_callback=None,
    on_project_start_callback=None,
) -> tuple[str | None, str, dict | None, str | None, str | None]:

    """
    النسخة الذكية بتبريد 29 ساعة + REFRESH_LOCK منفرد للإيميل + بصمة متسقة ثنائية لكل حساب.
    عند CREDIT_EXHAUSTED لا تُرجع الرد الجزئي: تُبرّد الحساب، تفرّع المشروع في حساب آخر،
    وترسل حرفياً "تابع " حتى يكتمل الرد أو تنفد الحسابات.
    """
    if bridge_cfg is None:
        bridge_cfg = BridgeConfig()
    if getattr(bridge_cfg, "run_started_at", None) is None:
        bridge_cfg.run_started_at = time.time()
    apply_project_runtime_binding(
        bridge_cfg,
        getattr(bridge_cfg, "selection_project_key", "") or None,
        requested_model=getattr(bridge_cfg, "model", DEFAULT_PROJECT_MODEL),
    )
    all_accounts = read_accounts_safe(json_path)

    owner_token = str(getattr(bridge_cfg, "selection_owner_token", "") or uuid.uuid4().hex)
    bridge_cfg.selection_owner_token = owner_token
    tried_emails = set()
    state_refresh = {}
    attempt = 0
    max_attempts = getattr(bridge_cfg, "max_account_attempts", 50)
    credit_continuations = 0
    max_credit_continuations = get_credit_continuation_limit(bridge_cfg)
    bridge_cfg.last_credit_continuations = 0
    bridge_cfg.last_credit_checkpoint_id = ""
    bridge_cfg.last_credit_resume_target_url = ""
    bridge_cfg.last_credit_resume_project_id = ""
    bridge_cfg.selected_account_email = ""
    bridge_cfg.selected_account_claim_state = ""
    bridge_cfg.account_journey = []  # 🧾 [P29] عزل مسار الحسابات لكل تشغيل جديد
    bridge_cfg.account_journey_spans = []  # ⏱️ [P30] عزل spans التوقيت لكل تشغيل جديد
    _set_credit_checkpoint_state(bridge_cfg, "", "")
    active_url = url
    active_query = query

    while attempt < max_attempts:
        attempt += 1
        curr_acc, ready_accounts, claim_reason = claim_eligible_account_for_owner(
            all_accounts,
            tried_emails,
            owner_token,
            project_key=str(getattr(bridge_cfg, "selection_project_key", "") or ""),
            attempt_number=attempt,
        )
        if claim_reason == "no-eligible":
            bridge_cfg.selected_account_claim_state = "no-eligible"
            notify_account_selection_observer(
                bridge_cfg,
                "no-eligible-accounts",
                status="ALL_ACCOUNTS_IN_COOLDOWN",
                max_attempts=max_attempts,
            )
            log_event("error", "كافة الحسابات المصرح بها حالياً في مهلة الـ 29h أو الحظر!")
            return None, "ALL_ACCOUNTS_IN_COOLDOWN", None, None, None
        if claim_reason == "busy":
            bridge_cfg.selected_account_claim_state = "busy"
            notify_account_selection_observer(
                bridge_cfg,
                "eligible-accounts-busy",
                status="ALL_ACCOUNTS_BUSY",
                max_attempts=max_attempts,
            )
            log_event("warning", "كل الحسابات المؤهلة الحالية محجوزة لمهمات أخرى؛ لا يوجد حساب حر الآن لهذه المهمة")
            return None, "ALL_ACCOUNTS_BUSY", None, None, None

        curr_acc = reactivate_account_if_due(curr_acc, json_path=json_path)
        curr_email = curr_acc.get("email")
        curr_pass = curr_acc.get("password", "")
        tried_emails.add(curr_email)
        bridge_cfg.selection_attempt_number = attempt
        bridge_cfg.selected_account_email = str(curr_email or "")
        bridge_cfg.selected_account_claim_state = "claimed"
        record_account_journey(bridge_cfg, curr_email)  # 🧾 [P29] لحظة الـ claim الفعلي فقط
        open_account_timing_span(bridge_cfg, curr_email, attempt_number=attempt)  # ⏱️ [P30] فتح span لحظة الـ claim

        fp = get_account_fingerprint(curr_email)
        bridge_cfg.user_agent = fp["user_agent"]
        bridge_cfg.current_browser = fp["browser"]
        notify_account_selection_observer(
            bridge_cfg,
            "account-claimed",
            status="CLAIMED",
            max_attempts=max_attempts,
            current_browser=fp["browser"],
        )

        log_event("info", f"تجربة حساب ({attempt}/{max_attempts}) | Profile: {fp['browser']}", email=curr_email)
        log_event("info", "تم حجز الحساب للمهمة الحالية أثناء التنفيذ", email=curr_email)

        now_ts = time.time()
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        update_account_data(curr_email, {"last_used": now_ts, "last_used_at": now_str}, json_path=json_path)

        try:
            pub_url, status, ext_dir, last_text, extra = send_message_and_make_public(
                url=active_url, email=curr_email, password=curr_pass, query=active_query,
                bridge_cfg=bridge_cfg, json_path=json_path,
                on_project_start_callback=on_project_start_callback,
            )

            # 🛑 [P25] إلغاء المستخدم التفاعلي → إنهاء فوري للمهمة كلها:
            # لا محاولة بحساب آخر، لا عقوبة/تبريد للحساب الحالي (يُحرَّر في finally)،
            # ولا progress_callback — المستخدم طلب الوقف القهري بنفسه.
            if status == CANCELLED_STATUS:
                notify_account_selection_observer(
                    bridge_cfg,
                    "user-cancelled",
                    status=CANCELLED_STATUS,
                    max_attempts=max_attempts,
                )
                log_event("warning", "🛑 [P25] أُلغيت المهمة بواسطة المستخدم — تحرير الحساب فوراً وإنهاء الـ failover", email=curr_email)
                update_account_data(curr_email, {"last_used": time.time(), "status": "active"}, json_path=json_path)
                return pub_url, CANCELLED_STATUS, curr_acc, ext_dir, last_text

            # 💰 [P13] رصيد منخفض مكتشف قبل الإرسال → الحساب مُبرَّد 29h بالفعل داخل
            # send_message_and_make_public — تخطٍ صامت فوري للحساب التالي:
            # لا progress_callback، لا إشعار للمستخدم، لا حظر auth_failed خاطئ.
            if status == "LOW_BALANCE":
                notify_account_selection_observer(
                    bridge_cfg,
                    "low-balance-skip",
                    status="LOW_BALANCE",
                    max_attempts=max_attempts,
                )
                log_event("info", "⏭️ تخطٍ صامت لحساب برصيد منخفض (مُبرَّد 29h) — الانتقال للحساب التالي", email=curr_email)
                continue

            # 🧬 [P20] خطأ AI Data Retention → بروتوكول نفاد الرصيد نفسه (تبريد 29h + حساب تالٍ)
            # لكن بتنبيه مميز، ومع إعادة إرسال «نفس آخر رسالة» المستخدمة في نفس الحساب
            # (سواء كانت رسالة استئناف أو رسالة مشروع جديد) — بدون التحويل لبرومبت الاستئناف.
            if status == "DATA_RETENTION":
                notify_account_selection_observer(
                    bridge_cfg,
                    "data-retention-blocked",
                    status="DATA_RETENTION",
                    max_attempts=max_attempts,
                )
                mark_account_cooldown(curr_email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                log_event(
                    "warning",
                    "🧬 [P20] رُصد خطأ AI Data Retention على هذا الحساب — معاملة كنفاد رصيد: تبريد وانتقال لحساب آخر مع إعادة إرسال نفس آخر رسالة كما هي",
                    email=curr_email,
                )
                continue

            if status == "CREDIT_EXHAUSTED":
                credit_continuations += 1
                bridge_cfg.last_credit_continuations = credit_continuations
                _set_credit_checkpoint_state(bridge_cfg, "PENDING", "awaiting checkpoint/report preservation")

            callback_result = None
            callback_error = None
            event_meta = {}
            if progress_callback:
                emit_event, event_meta = should_emit_progress_event(
                    pub_url, status, ext_dir, min_mtime=getattr(bridge_cfg, "run_started_at", None)
                )
                public_stage_query = get_public_continuation_prompt_text(active_query)
                safe_last_text = redact_github_secrets(last_text)
                if emit_event:
                    try:
                        callback_result = progress_callback(pub_url, status, ext_dir, safe_last_text, curr_email, public_stage_query)
                    except Exception as callback_err:
                        callback_error = callback_err
                        log_event("warning", f"فشل حفظ تحديث المشروع بدون إيقاف المهمة: {callback_err}", email=curr_email)
                else:
                    log_event(
                        "info",
                        f"تمت فلترة progress event غير قابل للحفظ للحالة {status}: {event_meta.get('reason')}",
                        email=curr_email,
                        extra=event_meta,
                    )

            is_401 = status in ("SESSION_EXPIRED", "LOGIN_FAILED") or (last_text and ("401" in str(last_text) or "unauthorized" in str(last_text).lower()))
            if is_401:
                refresh_count = state_refresh.get(curr_email, 0)
                notify_account_selection_observer(
                    bridge_cfg,
                    "session-refresh-required",
                    status=str(status or "SESSION_EXPIRED"),
                    refresh_count=refresh_count,
                    max_attempts=max_attempts,
                )
                if refresh_count >= 1:
                    notify_account_selection_observer(
                        bridge_cfg,
                        "session-refresh-exhausted",
                        status="auth_failed",
                        refresh_count=refresh_count,
                    )
                    log_event("error", "الحساب فشل بعد التجديد مرة واحدة -> وضع الحظر المؤقت", email=curr_email)
                    update_account_data(curr_email, {"status": "auth_failed", "active": False, "cooldown_until": time.time() + 1800}, json_path=json_path)
                    continue

                state_refresh[curr_email] = refresh_count + 1
                log_event("warning", "401 session منتهية! جاري التجديد مع راندوم Backoff...", email=curr_email)
                time.sleep(1 + random.uniform(0.5, 1.5))
                update_account_data(curr_email, {"cookies": {}, "status": "SESSION_EXPIRED"}, json_path=json_path)
                try:
                    mod = get_genspark_engine()
                    new_cookies = refresh_cookies_on_401(mod, curr_email, curr_pass, json_path=json_path)
                    if new_cookies and isinstance(new_cookies, dict):
                        notify_account_selection_observer(
                            bridge_cfg,
                            "session-refresh-succeeded",
                            status="active",
                            refresh_count=state_refresh.get(curr_email, 0),
                        )
                        tried_emails.discard(curr_email)
                        continue
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

            if status == "CREDIT_EXHAUSTED":
                notify_account_selection_observer(
                    bridge_cfg,
                    "credit-exhausted-observed",
                    status="CREDIT_EXHAUSTED",
                    continuation_index=credit_continuations,
                    continuation_limit=max_credit_continuations,
                )
                mark_account_cooldown(curr_email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                gate = evaluate_credit_checkpoint_gate(
                    bridge_cfg,
                    callback_result=callback_result,
                    callback_error=callback_error,
                    progress_callback_present=bool(progress_callback),
                )
                if not gate["allow_continuation"]:
                    notify_account_selection_observer(
                        bridge_cfg,
                        "continuation-blocked",
                        status="CREDIT_EXHAUSTED",
                        reason=str(gate.get("reason") or ""),
                    )
                    log_event(
                        "error",
                        f"تم إيقاف continuation بعد نفاد الرصيد لأن checkpoint/report لم يثبت قبل المتابعة: {gate['reason']}",
                        email=curr_email,
                        extra=event_meta if event_meta else None,
                    )
                    return pub_url, status, curr_acc, ext_dir, last_text
                if credit_continuations >= max_credit_continuations:
                    notify_account_selection_observer(
                        bridge_cfg,
                        "credit-continuations-exhausted",
                        status="CREDIT_EXHAUSTED",
                        continuation_index=credit_continuations,
                        continuation_limit=max_credit_continuations,
                    )
                    log_event(
                        "error",
                        f"تجاوزنا الحد الآمن لمحاولات الاستئناف بعد نفاد الرصيد ({credit_continuations}/{max_credit_continuations})",
                        email=curr_email,
                    )
                    return pub_url, status, curr_acc, ext_dir, last_text

                source_pid = extract_project_id(pub_url) if pub_url else ""
                continuation_url = pub_url or (
                    f"https://www.genspark.ai/autopilotagent_viewer?id={source_pid}" if source_pid else active_url
                )
                if not continuation_url:
                    log_event("error", "تعذر تحديد رابط المشروع لاستئنافه بحساب آخر", email=curr_email)
                    return pub_url, status, curr_acc, ext_dir, last_text

                bridge_cfg.last_credit_resume_target_url = continuation_url
                bridge_cfg.last_credit_resume_project_id = source_pid or extract_project_id(continuation_url)
                notify_account_selection_observer(
                    bridge_cfg,
                    "continuation-handoff-ready",
                    status="CREDIT_EXHAUSTED",
                    continuation_index=credit_continuations,
                    continuation_limit=max_credit_continuations,
                    continuation_url=continuation_url,
                    source_project_id=bridge_cfg.last_credit_resume_project_id,
                    checkpoint_id=gate.get("checkpoint_id") or getattr(bridge_cfg, "last_credit_checkpoint_id", ""),
                )
                handoff_callback = getattr(bridge_cfg, "credit_handoff_callback", None)
                if callable(handoff_callback):
                    try:
                        handoff_callback({
                            "source_project_id": bridge_cfg.last_credit_resume_project_id,
                            "continuation_url": continuation_url,
                            "checkpoint_id": gate.get("checkpoint_id") or getattr(bridge_cfg, "last_credit_checkpoint_id", ""),
                            "continuation_index": credit_continuations,
                            "continuation_limit": max_credit_continuations,
                        })
                    except Exception as notify_err:
                        log_event("warning", f"فشل تبليغ handoff بدون إيقاف المتابعة: {notify_err}", email=curr_email)

                active_url = continuation_url
                active_query = get_bridge_cfg_runtime_resume_prompt(bridge_cfg)
                public_resume_prompt = summarize_resume_prompt_for_display(get_bridge_cfg_public_resume_prompt(bridge_cfg))
                log_event(
                    "warning",
                    f"نفد الرصيد؛ الرد غير مكتمل. الانتقال تلقائياً لحساب آخر وإرسال برومبت الاستئناف «{public_resume_prompt}» ({credit_continuations}/{max_credit_continuations})",
                    email=curr_email
                )
                continue

            if pub_url or status == "COMPLETED":
                notify_account_selection_observer(
                    bridge_cfg,
                    "attempt-succeeded",
                    status=str(status or "COMPLETED"),
                    public_url=str(pub_url or ""),
                )
                update_account_data(curr_email, {
                    "last_used": time.time(),
                    "status": "active",
                    "active": True,
                    "cooldown_until": 0,
                    "last_success_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                }, json_path=json_path)
                return pub_url, status, curr_acc, ext_dir, last_text

            notify_account_selection_observer(
                bridge_cfg,
                "attempt-failed-continue",
                status=str(status or "FAILED"),
            )
            update_account_data(curr_email, {"cooldown_until": time.time() + 300}, json_path=json_path)
            continue
        finally:
            close_account_timing_span(bridge_cfg, curr_email)  # ⏱️ [P30] إغلاق حتمي للـ span في كل المسارات
            release_account_selection(curr_email, owner_token)
            bridge_cfg.selected_account_claim_state = "released"
    return None, "MAX_ATTEMPTS_EXHAUSTED", None, None, None


# ══════════════════════════════════════════════════════════════
# ⚡ [Task-4] مشغل المهام الموازية للبوت (Concurrent Parallel Queue)
# ══════════════════════════════════════════════════════════════
EXECUTOR = ThreadPoolExecutor(max_workers=3, thread_name_prefix="genspark_worker")
USER_STATE_STORE = {}
USER_STATE_LOCK = threading.Lock()


def set_user_state(chat_id: int, state: dict):
    with USER_STATE_LOCK:
        state["ts"] = time.time()
        USER_STATE_STORE[chat_id] = state


def get_user_state(chat_id: int) -> dict:
    with USER_STATE_LOCK:
        state = USER_STATE_STORE.get(chat_id, {})
        if not state:
            return {}
        if time.time() - state.get("ts", 0) > 1800:
            del USER_STATE_STORE[chat_id]
            return {}
        return state


UPLOAD_QUEUE_SCHEMA_VERSION = 1
UPLOAD_MAX_INLINE_BYTES = 95 * 1024 * 1024
UPLOAD_RETRY_BASE_SECONDS = 5
UPLOAD_RETRY_MAX_SECONDS = 300


class ProjectRegistry:
    """عزل دائم لكل مشروع: ملفات، checkpoints، manifests وقفل مستقل.

    الأسرار لا تُكتب على القرص ولا تُرسل لتليجرام. GitHub اختياري ويُفعل فقط من
    GITHUB_UPLOAD_TOKEN و GITHUB_UPLOAD_REPOSITORY=owner/repo.
    """
    def __init__(self, project_key: str):
        self.key = re.sub(r"[^A-Za-z0-9_-]", "_", project_key)[:80]
        self.root = PROJECT_REGISTRY_HOME / self.key
        # fallback environment token يبقى احتياطياً فقط؛ الأولوية لاحقاً لتوكن المشروع نفسه.
        self._github_token = get_default_github_token_from_env()
        self._github_repo = os.getenv("GITHUB_UPLOAD_REPOSITORY", "").strip()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = get_project_lock(self.key)
        self.manifest_path = self.root / "manifest.json"

    def remember_identity(self, root_pid: str | None = None, latest_pid: str | None = None,
                          project_name: str | None = None, chat_id: int | None = None,
                          status: str | None = None) -> dict:
        return upsert_project_identity(
            self.key,
            root_pid=root_pid,
            latest_pid=latest_pid,
            project_name=project_name,
            chat_id=chat_id,
            status=status,
        )

    def _manifest_backup_path(self) -> pathlib.Path:
        return self.manifest_path.with_suffix(".bak")

    def _secrets_path(self) -> pathlib.Path:
        return self.root / "secrets.local.json"

    def _secrets_default(self) -> dict:
        return {
            "schema_version": PROJECT_SECRET_SCHEMA_VERSION,
            "github": {"token": ""},
        }

    def _normalize_project_secrets(self, data: dict | None) -> dict:
        base = self._secrets_default()
        if not isinstance(data, dict):
            return base
        github = data.get("github") if isinstance(data.get("github"), dict) else {}
        base["github"] = {"token": str(github.get("token") or "").strip()}
        return base

    def _read_secrets(self) -> dict:
        path = self._secrets_path()
        if not path.exists():
            return self._secrets_default()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return self._secrets_default()
        if not isinstance(raw, dict):
            return self._secrets_default()
        if raw.get("schema_version") not in (None, PROJECT_SECRET_SCHEMA_VERSION):
            return self._secrets_default()
        return self._normalize_project_secrets(raw)

    def _write_secrets(self, data: dict):
        normalized = self._normalize_project_secrets(data)
        path = self._secrets_path()
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)

    def _manifest_default(self) -> dict:
        return {
            "project_key": self.key,
            "created_at": _utc(),
            "updated_at": _utc(),
            "schema_version": PROJECT_MANIFEST_SCHEMA_VERSION,
            "updates": [],
            "checkpoints": [],
            "last_three_urls": [],
            "file_index": {},
            "project_settings": default_project_settings(),
        }

    def _normalize_project_settings(self, settings: dict | None) -> dict:
        base = default_project_settings()
        payload = settings if isinstance(settings, dict) else {}
        base["model"] = normalize_project_model(payload.get("model"))
        continuation = payload.get("continuation") if isinstance(payload.get("continuation"), dict) else {}
        prompt = normalize_project_resume_prompt(continuation.get("prompt"))
        base["continuation"] = {
            "prompt": prompt,
            "mode": normalize_project_resume_mode(continuation.get("mode"), prompt=prompt),
        }
        github = payload.get("github") if isinstance(payload.get("github"), dict) else {}
        base["github"] = {
            "configured": bool(github.get("configured", False)),
            "enabled": bool(github.get("enabled", False)),
            "repository": str(github.get("repository") or "").strip(),
            "token_present": bool(github.get("token_present", False)),
            "token_storage": str(github.get("token_storage") or "").strip(),
            "branch": str(github.get("branch") or "").strip(),
            "branch_mode": str(github.get("branch_mode") or ("manual" if github.get("branch") else "disabled")),
            "detected_default_branch": str(github.get("detected_default_branch") or "").strip(),
            "available_branches": [str(x).strip() for x in (github.get("available_branches") or []) if str(x).strip()][:20],
            "last_repo_check_status": str(github.get("last_repo_check_status") or "").strip(),
            "last_repo_check_at": str(github.get("last_repo_check_at") or "").strip(),
        }
        if not base["github"]["enabled"] and base["github"]["configured"] and base["github"]["branch_mode"] == "manual":
            base["github"]["branch_mode"] = "disabled"
        if base["github"]["enabled"] and base["github"]["branch_mode"] == "disabled":
            base["github"]["branch_mode"] = "manual" if base["github"]["branch"] else "auto_default"
        return base

    def _apply_secret_metadata_to_settings(self, settings: dict) -> dict:
        normalized = self._normalize_project_settings(settings)
        token_present = bool(self._read_secrets().get("github", {}).get("token"))
        normalized["github"]["token_present"] = token_present
        normalized["github"]["token_storage"] = "project-local-secret" if token_present else ""
        return normalized

    def _normalize_manifest(self, data: dict | None) -> dict:
        base = self._manifest_default()
        if not isinstance(data, dict):
            return base
        if data.get("project_key"):
            base["project_key"] = self.key
        for field_name in ("created_at", "updated_at"):
            if data.get(field_name):
                base[field_name] = data.get(field_name)
        for list_field in ("updates", "checkpoints", "last_three_urls"):
            if isinstance(data.get(list_field), list):
                base[list_field] = list(data.get(list_field))
        if isinstance(data.get("file_index"), dict):
            normalized_index = {}
            for raw_path, raw_entry in data.get("file_index", {}).items():
                rel_path = pathlib.PurePosixPath(str(raw_path)).as_posix()
                if not rel_path or rel_path == ".":
                    continue
                entry = raw_entry if isinstance(raw_entry, dict) else {}
                normalized_index[rel_path] = {
                    "project_key": self.key,
                    "relative_path": rel_path,
                    "sha256": str(entry.get("sha256") or ""),
                    "bytes": int(entry.get("bytes") or 0),
                    "last_seen_at": str(entry.get("last_seen_at") or ""),
                    "deleted_at": entry.get("deleted_at"),
                }
            base["file_index"] = normalized_index
        base["project_settings"] = self._normalize_project_settings(data.get("project_settings"))
        base["schema_version"] = PROJECT_MANIFEST_SCHEMA_VERSION
        return base

    def _read(self):
        if not self.manifest_path.exists():
            return self._manifest_default()
        try:
            raw = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception as err:
            log_event("warning", f"تعذر قراءة manifest للمشروع {self.key}; سيتم التعامل fail-closed: {type(err).__name__}")
            return self._manifest_default()
        if not isinstance(raw, dict):
            log_event("warning", f"manifest للمشروع {self.key} ليست JSON object؛ تم التعامل fail-closed")
            return self._manifest_default()
        schema_version = raw.get("schema_version")
        if schema_version not in (None, PROJECT_MANIFEST_SCHEMA_VERSION):
            log_event("warning", f"schema_version غير معروفة في manifest المشروع {self.key}: {schema_version}")
            return self._manifest_default()
        normalized = self._normalize_manifest(raw)
        if schema_version is None:
            try:
                self._write(normalized)
            except Exception:
                pass
        return normalized

    def _write(self, data):
        normalized = self._normalize_manifest(data)
        normalized["updated_at"] = _utc()
        if self.manifest_path.exists():
            self._manifest_backup_path().write_text(self.manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
        temp = self.manifest_path.with_suffix(".tmp")
        temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.manifest_path)

    def restore_manifest_from_backup(self) -> bool:
        backup = self._manifest_backup_path()
        if not backup.exists() or not backup.is_file():
            return False
        try:
            raw = json.loads(backup.read_text(encoding="utf-8"))
        except Exception:
            return False
        if not isinstance(raw, dict):
            return False
        schema_version = raw.get("schema_version")
        if schema_version not in (None, PROJECT_MANIFEST_SCHEMA_VERSION):
            return False
        normalized = self._normalize_manifest(raw)
        temp = self.manifest_path.with_suffix(".restore.tmp")
        temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.manifest_path)
        return True

    def get_project_settings(self) -> dict:
        with self.lock:
            data = self._read()
            return self._apply_secret_metadata_to_settings(data.get("project_settings") or {})

    def update_project_settings(self, settings: dict | None = None) -> dict:
        with self.lock:
            data = self._read()
            current = self._normalize_project_settings(data.get("project_settings"))
            patch = settings if isinstance(settings, dict) else {}
            if "model" in patch:
                current["model"] = normalize_project_model(patch.get("model"))
            if isinstance(patch.get("continuation"), dict):
                continuation_patch = patch.get("continuation") or {}
                prompt = current["continuation"]["prompt"]
                if "prompt" in continuation_patch:
                    prompt = normalize_project_resume_prompt(continuation_patch.get("prompt"))
                    current["continuation"]["prompt"] = prompt
                if "mode" in continuation_patch or "prompt" in continuation_patch:
                    current["continuation"]["mode"] = normalize_project_resume_mode(continuation_patch.get("mode"), prompt=prompt)
            if isinstance(patch.get("github"), dict):
                github_patch = patch.get("github") or {}
                for key, value in github_patch.items():
                    if key == "configured":
                        current["github"][key] = bool(value)
                    elif key == "enabled":
                        current["github"][key] = bool(value)
                    elif key in {"repository", "token_storage", "branch", "branch_mode", "detected_default_branch", "last_repo_check_status", "last_repo_check_at"}:
                        current["github"][key] = str(value or "").strip()
                    elif key == "token_present":
                        current["github"][key] = bool(value)
                    elif key == "available_branches":
                        current["github"][key] = [str(x).strip() for x in (value or []) if str(x).strip()][:20]
                current = self._normalize_project_settings(current)
            data["project_settings"] = current
            self._write(data)
            return self._apply_secret_metadata_to_settings(current)

    def get_project_github_token(self, allow_env_fallback: bool = True) -> str:
        with self.lock:
            token = self._read_secrets().get("github", {}).get("token", "")
        if token:
            return token
        return get_default_github_token_from_env() if allow_env_fallback else ""

    def set_project_github_token(self, token: str | None) -> dict:
        clean = str(token or "").strip()
        with self.lock:
            secrets = self._read_secrets()
            secrets.setdefault("github", {})["token"] = clean
            self._write_secrets(secrets)
        return self.update_project_settings({
            "github": {
                "token_present": bool(clean),
                "token_storage": "project-local-secret" if clean else "",
            }
        })

    def clear_project_github_token(self) -> dict:
        return self.set_project_github_token("")

    def set_project_model(self, model: str | None) -> dict:
        return self.update_project_settings({"model": model})

    def set_project_resume_prompt(self, prompt: str | None) -> dict:
        return self.update_project_settings({"continuation": {"prompt": prompt}})

    def build_effective_resume_prompt(self, include_github_token: bool = False) -> str:
        settings = self.get_project_settings()
        github_token = self.get_project_github_token() if include_github_token else ""
        return compose_runtime_resume_prompt(settings.get("continuation", {}).get("prompt"), github_token=github_token)

    def _hot_checkpoint_path(self, checkpoint_id: str) -> pathlib.Path:
        return self.root / "checkpoints" / "hot" / checkpoint_id

    def _archive_path(self, checkpoint_id: str) -> pathlib.Path:
        return self.root / "archive" / f"{checkpoint_id}.tar.gz"

    def _queue_path(self) -> pathlib.Path:
        return self.root / "queue.json"

    def _queue_default(self) -> dict:
        return {"schema_version": UPLOAD_QUEUE_SCHEMA_VERSION, "jobs": []}

    def _normalize_upload_job(self, job: dict | None) -> dict:
        data = job if isinstance(job, dict) else {}
        destination = data.get("destination") if isinstance(data.get("destination"), dict) else {}
        branch = str(destination.get("branch") or "")
        branch_mode = str(destination.get("branch_mode") or ("manual" if branch else "auto_default"))
        return {
            "job_id": str(data.get("job_id") or uuid.uuid4().hex),
            "project_key": self.key,
            "checkpoint_id": str(data.get("checkpoint_id") or ""),
            "destination": {
                "repository": str(destination.get("repository") or ""),
                "branch": branch,
                "branch_mode": branch_mode,
                "target_root": str(destination.get("target_root") or "/"),
            },
            "idempotency_key": str(data.get("idempotency_key") or ""),
            "attempt_count": int(data.get("attempt_count") or 0),
            "next_retry_at": data.get("next_retry_at"),
            "last_error_code": str(data.get("last_error_code") or ""),
            "state": str(data.get("state") or "pending"),
            "created_at": str(data.get("created_at") or _utc()),
            "updated_at": str(data.get("updated_at") or _utc()),
            "schema_version": UPLOAD_QUEUE_SCHEMA_VERSION,
        }

    def _read_queue(self) -> dict:
        path = self._queue_path()
        if not path.exists():
            return self._queue_default()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as err:
            log_event("warning", f"تعذر قراءة queue للمشروع {self.key}; سيتم التعامل fail-closed: {type(err).__name__}")
            return self._queue_default()
        if not isinstance(raw, dict):
            return self._queue_default()
        if raw.get("schema_version") not in (None, UPLOAD_QUEUE_SCHEMA_VERSION):
            return self._queue_default()
        jobs = raw.get("jobs") if isinstance(raw.get("jobs"), list) else []
        return {
            "schema_version": UPLOAD_QUEUE_SCHEMA_VERSION,
            "jobs": [self._normalize_upload_job(job) for job in jobs],
        }

    def _write_queue(self, payload: dict):
        normalized = {
            "schema_version": UPLOAD_QUEUE_SCHEMA_VERSION,
            "jobs": [self._normalize_upload_job(job) for job in (payload.get("jobs") or [])],
        }
        path = self._queue_path()
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)

    def _github_destination(self) -> dict | None:
        settings = self.get_project_settings().get("github", {})
        if not settings.get("configured"):
            return None
        if not settings.get("enabled"):
            return None
        repo = str(settings.get("repository") or "").strip()
        if not repo or not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            return None
        branch = str(settings.get("branch") or "").strip()
        branch_mode = str(settings.get("branch_mode") or ("manual" if branch else "auto_default"))
        return {
            "repository": repo,
            "branch": branch,
            "branch_mode": branch_mode,
            "target_root": "/",
        }

    def inspect_github_repository(self, repo_ref: str | None = None, requester=None) -> dict:
        target_repo = str(repo_ref or self.get_project_settings().get("github", {}).get("repository") or self._github_repo or "").strip()
        return inspect_github_repository(target_repo, token=self.get_project_github_token(), requester=requester)

    def enqueue_github_sync(self, update: dict) -> dict:
        destination = self._github_destination()
        if not self.get_project_github_token() or not destination:
            return {"enabled": False, "queued": [], "jobs": [], "uploaded": [], "unchanged": [], "skipped": []}
        queue_data = self._read_queue()
        checkpoint_id = str(update.get("checkpoint") or "")
        checksum = str(update.get("checksum") or "")
        branch_part = destination.get("branch") or destination.get("branch_mode") or "auto"
        idempotency_key = f"{self.key}:{checkpoint_id}:{checksum}:{destination['repository']}:{branch_part}"
        existing = next((job for job in queue_data["jobs"] if job.get("idempotency_key") == idempotency_key), None)
        if existing:
            return {"enabled": True, "queued": [existing["job_id"]], "jobs": [existing], "uploaded": [], "unchanged": [], "skipped": []}
        job = self._normalize_upload_job({
            "job_id": uuid.uuid4().hex,
            "project_key": self.key,
            "checkpoint_id": checkpoint_id,
            "destination": destination,
            "idempotency_key": idempotency_key,
            "attempt_count": 0,
            "next_retry_at": None,
            "last_error_code": "",
            "state": "pending",
            "created_at": _utc(),
            "updated_at": _utc(),
        })
        queue_data["jobs"].append(job)
        self._write_queue(queue_data)
        return {"enabled": True, "queued": [job["job_id"]], "jobs": [job], "uploaded": [], "unchanged": [], "skipped": []}

    def list_upload_jobs(self, state: str | None = None) -> list[dict]:
        jobs = self._read_queue().get("jobs", [])
        if state:
            jobs = [job for job in jobs if job.get("state") == state]
        return [dict(job) for job in jobs]

    def _parse_iso_time(self, value: str | None) -> float | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value)).timestamp()
        except Exception:
            return None

    def compute_upload_backoff_seconds(self, attempt_count: int) -> int:
        attempts = max(1, int(attempt_count or 1))
        return min(UPLOAD_RETRY_MAX_SECONDS, UPLOAD_RETRY_BASE_SECONDS * (2 ** (attempts - 1)))

    def claim_next_upload_job(self, now_ts: float | None = None) -> dict | None:
        now_ts = time.time() if now_ts is None else float(now_ts)
        queue_data = self._read_queue()
        chosen_idx = None
        chosen_job = None
        for idx, job in enumerate(queue_data.get("jobs", [])):
            state = str(job.get("state") or "")
            if state == "pending":
                chosen_idx, chosen_job = idx, job
                break
            if state == "retrying":
                due_ts = self._parse_iso_time(job.get("next_retry_at"))
                if due_ts is None or due_ts <= now_ts:
                    chosen_idx, chosen_job = idx, job
                    break
        if chosen_job is None:
            return None
        updated = self._normalize_upload_job(chosen_job)
        updated["attempt_count"] = int(updated.get("attempt_count") or 0) + 1
        updated["state"] = "uploading"
        updated["next_retry_at"] = None
        updated["updated_at"] = _utc()
        queue_data["jobs"][chosen_idx] = updated
        self._write_queue(queue_data)
        return dict(updated)

    def claim_upload_job_by_id(self, job_id: str, now_ts: float | None = None) -> dict | None:
        now_ts = time.time() if now_ts is None else float(now_ts)
        queue_data = self._read_queue()
        for idx, job in enumerate(queue_data.get("jobs", [])):
            if str(job.get("job_id") or "") != str(job_id or ""):
                continue
            state = str(job.get("state") or "")
            if state == "synced":
                return dict(self._normalize_upload_job(job))
            if state == "uploading":
                return None
            if state == "retrying":
                due_ts = self._parse_iso_time(job.get("next_retry_at"))
                if due_ts is not None and due_ts > now_ts:
                    return None
            if state not in {"pending", "retrying"}:
                return None
            updated = self._normalize_upload_job(job)
            updated["attempt_count"] = int(updated.get("attempt_count") or 0) + 1
            updated["state"] = "uploading"
            updated["next_retry_at"] = None
            updated["updated_at"] = _utc()
            queue_data["jobs"][idx] = updated
            self._write_queue(queue_data)
            return dict(updated)
        return None

    def update_upload_job_state(self, job_id: str, state: str, last_error_code: str = "", next_retry_at: str | None = None) -> dict | None:
        queue_data = self._read_queue()
        for idx, job in enumerate(queue_data.get("jobs", [])):
            if job.get("job_id") != job_id:
                continue
            updated = self._normalize_upload_job(job)
            updated["state"] = str(state)
            updated["last_error_code"] = str(last_error_code or "")
            updated["next_retry_at"] = next_retry_at
            updated["updated_at"] = _utc()
            queue_data["jobs"][idx] = updated
            self._write_queue(queue_data)
            return dict(updated)
        return None

    def mark_upload_job_retrying(self, job_id: str, last_error_code: str, now_ts: float | None = None) -> dict | None:
        queue_data = self._read_queue()
        now_ts = time.time() if now_ts is None else float(now_ts)
        for idx, job in enumerate(queue_data.get("jobs", [])):
            if job.get("job_id") != job_id:
                continue
            updated = self._normalize_upload_job(job)
            backoff = self.compute_upload_backoff_seconds(updated.get("attempt_count") or 1)
            updated["state"] = "retrying"
            updated["last_error_code"] = str(last_error_code or "")
            updated["next_retry_at"] = datetime.fromtimestamp(now_ts + backoff, timezone.utc).isoformat()
            updated["updated_at"] = _utc()
            queue_data["jobs"][idx] = updated
            self._write_queue(queue_data)
            return dict(updated)
        return None

    def build_upload_job_plan(self, job_id: str) -> dict | None:
        job = next((j for j in self.list_upload_jobs() if j.get("job_id") == job_id), None)
        if not job:
            return None
        record = self.load_checkpoint_record(job.get("checkpoint_id"))
        if not record:
            return {
                "job": job,
                "upload_files": [],
                "delete_files": [],
                "skipped": [f"checkpoint:{job.get('checkpoint_id')} (CHECKPOINT_RECORD_MISSING)"],
            }
        checkpoint_dir = self._hot_checkpoint_path(job.get("checkpoint_id"))
        upload_files = []
        skipped = []
        for info in record.get("files", []):
            rel = str(info.get("path") or "")
            size = int(info.get("bytes") or 0)
            if size > UPLOAD_MAX_INLINE_BYTES:
                skipped.append(f"{rel} (FILE_TOO_LARGE_LOCAL_ONLY)")
                continue
            local = checkpoint_dir / rel
            if not local.exists() or not local.is_file():
                skipped.append(f"{rel} (CHECKPOINT_FILE_MISSING)")
                continue
            upload_files.append({"path": rel, "bytes": size, "local_path": str(local)})
        delete_files = [str(info.get("path") or "") for info in record.get("deleted_files", []) if info.get("path")]
        return {
            "job": job,
            "upload_files": upload_files,
            "delete_files": delete_files,
            "skipped": skipped,
        }

    def _normalize_remote_relative_path(self, rel_path: str) -> str:
        rel = pathlib.PurePosixPath(str(rel_path or "").replace("\\", "/")).as_posix()
        if not rel or rel.startswith("/") or ".." in pathlib.PurePosixPath(rel).parts:
            raise ValueError(f"INVALID_REMOTE_PATH:{rel_path}")
        return rel

    def _default_branch_resolver(self, repository: str) -> str:
        if not repository:
            return "main"
        inspection = self.inspect_github_repository(repository)
        branch = str(inspection.get("default_branch") or "").strip()
        return branch or "main"

    @staticmethod
    def _git_blob_sha(local_path: str) -> str:
        """Compute the SHA returned by GitHub Contents API without invoking git."""
        import hashlib
        size = pathlib.Path(local_path).stat().st_size
        digest = hashlib.sha1()
        digest.update(f"blob {size}\0".encode("ascii"))
        with open(local_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _qwen_commit_prefix_for_job(self, payload: dict) -> str:
        """🧠 [DEC-019] طلب رسالة كوميت ذكية من محرك كوين مرة واحدة لكل job.
        ⏳ [P31] يُستدعى Lazy عبر _lazy_ai_prefix داخل uploader — فقط عند أول
        PUT/DELETE فعلي؛ job كله unchanged ← كوين لا يُستدعى إطلاقاً.
        معزول بالكامل: أي فشل (استيراد/شبكة/مهلة/رد فارغ) ← يرجع "" ويكمل الرفع
        بنفس رسالة الكوميت القديمة حرفياً — الرفع لا ينكسر أبداً بسبب كوين.
        المهلة: مهلة المحرك الداخلية نفسها (30ث/مرحلة) — بدون اختراع أرقام جديدة."""
        try:
            changed_names = [str(f.get("path") or "") for f in payload.get("upload_files", [])]
            changed_names += [f"(حذف) {rel}" for rel in payload.get("delete_files", [])]
            changed_lines = "\n".join(name for name in changed_names if name)
            if not changed_lines:
                return ""
            import qwen_engine
            commit_msg, _summary, _model = qwen_engine.generate_ai_summary(changed_lines, "", [])
            if commit_msg and str(commit_msg).strip():
                return str(commit_msg).strip()[:150]
        except Exception as exc:
            log_event("warning", f"⚠️ [DEC-019] تعذر توليد كوميت كوين (fallback للرسالة القديمة): {exc}")
        return ""

    def _default_github_uploader(self, payload: dict) -> dict:
        repository = payload["repository"]
        branch = payload["branch"]
        target_root = str(payload.get("target_root") or "/").strip("/")
        token = self.get_project_github_token()
        if not token:
            raise RuntimeError("PROJECT_GITHUB_TOKEN_MISSING")

        # 🔧 [P20] قرار المالك: إلغاء مسار Git Native Sync نهائياً (كان يفشل بـ
        # name 'dest_root' is not defined بشكل متكرر) — GitHub Contents REST API
        # هو مسار الرفع الوحيد والمباشر الآن بدون أي محاولة clone/push.
        import base64
        import requests
        headers = build_github_api_headers(token)
        # 🎯 [P21] دقة تصنيف commit: التمييز بين ملف جديد (غير موجود على الريموت
        # → 404 → uploaded) وملف معدل (له remote_sha مختلف → modified) — كان الاثنان
        # يُحسبان "➕ جديد" في الإحصائيات رغم أن remote_sha متاح أصلاً قبل الـ PUT.
        uploaded, modified, unchanged, deleted, skipped = [], [], [], [], list(payload.get("skipped", []))
        # 🧠 [DEC-019] كوميت ذكي من كوين مرة واحدة لكل job — فشله لا يكسر الرفع.
        # ⏳ [P31] Lazy Call: كوين لا يُستدعى إلا عند أول PUT/DELETE فعلي — job كله
        # unchanged (كل الملفات مطابقة للريموت بايت-بايت) ← صفر نداء لكوين
        # (توفير باقة API + إلغاء تأخير حتى 30ث مجاني في كل sync cycle بلا تغيير).
        # memoized: None = لم يُستدعَ بعد | "" = استُدعي وفشل/فارغ (fallback حرفي).
        ai_prefix = None

        def _lazy_ai_prefix() -> str:
            nonlocal ai_prefix
            if ai_prefix is None:
                ai_prefix = self._qwen_commit_prefix_for_job(payload)
            return ai_prefix
        for file_info in payload.get("upload_files", []):
            rel = self._normalize_remote_relative_path(file_info["path"])
            if _should_skip_archive_member(rel):
                skipped.append(rel)
                continue
            remote_rel = "/".join(part for part in (target_root, rel) if part)
            api = f"https://api.github.com/repos/{repository}/contents/{remote_rel}"
            remote_sha = None
            got = requests.get(api, headers=headers, params={"ref": branch}, timeout=30)
            if got.status_code == 200:
                remote_sha = str(got.json().get("sha") or "")
            elif got.status_code != 404:
                raise RuntimeError(f"HTTP_{got.status_code}")
            local_sha = self._git_blob_sha(file_info["local_path"])
            if remote_sha and remote_sha == local_sha:
                unchanged.append(rel)
                continue
            with open(file_info["local_path"], "rb") as fh:
                content_b64 = base64.b64encode(fh.read()).decode("ascii")
            # [DEC-019] رسالة كوين كبادئة عند النجاح — وإلا نفس الرسالة القديمة حرفياً.
            # [P31] أول ملف متغير فعلياً هو الذي يوقظ كوين (بعد فحص unchanged) — مرة واحدة لكل job.
            _lazy_ai_prefix()
            commit_message = f"{ai_prefix} [{self.key}] sync {payload['job_id']}: {rel}" if ai_prefix else f"[{self.key}] sync {payload['job_id']}: {rel}"
            body = {"message": commit_message, "content": content_b64, "branch": branch}
            if remote_sha:
                body["sha"] = remote_sha
            put = requests.put(api, headers=headers, json=body, timeout=120)
            if put.status_code in (200, 201):
                # [P21] remote_sha موجود = الملف كان على الريموت واختلف محتواه → معدل ✏️
                (modified if remote_sha else uploaded).append(rel)
            else:
                raise RuntimeError(f"HTTP_{put.status_code}")
        for rel in payload.get("delete_files", []):
            rel = self._normalize_remote_relative_path(rel)
            remote_rel = "/".join(part for part in (target_root, rel) if part)
            api = f"https://api.github.com/repos/{repository}/contents/{remote_rel}"
            got = requests.get(api, headers=headers, params={"ref": branch}, timeout=30)
            if got.status_code == 404:
                continue
            if got.status_code != 200:
                raise RuntimeError(f"HTTP_{got.status_code}")
            sha = got.json().get("sha")
            # [P31] الحذف الفعلي (الملف موجود على الريموت 200) يوقظ كوين إن لم يستيقظ بعد.
            _lazy_ai_prefix()
            delete_message = f"{ai_prefix} [{self.key}] delete {payload['job_id']}: {rel}" if ai_prefix else f"[{self.key}] delete {payload['job_id']}: {rel}"
            body = {"message": delete_message, "sha": sha, "branch": branch}
            delete_resp = requests.delete(api, headers=headers, json=body, timeout=120)
            if delete_resp.status_code in (200, 204):
                deleted.append(rel)
            else:
                raise RuntimeError(f"HTTP_{delete_resp.status_code}")
        return {"uploaded": uploaded, "modified": modified, "unchanged": unchanged, "deleted": deleted, "skipped": skipped}

    def recover_upload_queue_after_restart(self, now_ts: float | None = None) -> list[dict]:
        now_ts = time.time() if now_ts is None else float(now_ts)
        queue_data = self._read_queue()
        recovered = []
        changed = False
        for idx, job in enumerate(queue_data.get("jobs", [])):
            state = str(job.get("state") or "")
            attempts = int(job.get("attempt_count") or 0)
            if attempts >= 5 and state != "synced":
                job["state"] = "failed"
                job["last_error_code"] = "MAX_RETRIES_EXCEEDED"
                job["updated_at"] = _utc()
                changed = True
                continue
            if state in {"uploading", "retrying"}:
                updated = self._normalize_upload_job(job)
                updated["state"] = "retrying"
                updated["next_retry_at"] = None  # تصفير الانتظار لإعادة المحاولة الفورية
                updated["updated_at"] = _utc()
                queue_data["jobs"][idx] = updated
                recovered.append(dict(updated))
                changed = True
        if changed:
            self._write_queue(queue_data)
        return recovered

    def _execute_claimed_upload_job(self, job: dict, uploader=None, branch_resolver=None, now_ts: float | None = None) -> dict:
        plan = self.build_upload_job_plan(job["job_id"])
        if not plan:
            retry_job = self.mark_upload_job_retrying(job["job_id"], "JOB_PLAN_MISSING", now_ts=now_ts)
            return {"processed": False, "reason": "JOB_PLAN_MISSING", "job": retry_job or job}
        destination = plan["job"].get("destination", {}) if isinstance(plan.get("job"), dict) else {}
        repository = str(destination.get("repository") or "")
        if not repository:
            retry_job = self.mark_upload_job_retrying(job["job_id"], "DESTINATION_MISSING", now_ts=now_ts)
            return {"processed": False, "reason": "DESTINATION_MISSING", "job": retry_job or job}
        branch = str(destination.get("branch") or "")
        if not branch:
            resolver = branch_resolver or self._default_branch_resolver
            branch = resolver(repository)
        payload = {
            "job_id": job["job_id"],
            "project_key": self.key,
            "repository": repository,
            "branch": branch,
            "target_root": str(destination.get("target_root") or "/"),
            "upload_files": plan.get("upload_files", []),
            "delete_files": plan.get("delete_files", []),
            "skipped": list(plan.get("skipped", [])),
        }
        try:
            result = (uploader or self._default_github_uploader)(payload)
        except Exception as err:
            retry_job = self.mark_upload_job_retrying(job["job_id"], type(err).__name__ if type(err).__name__ != "RuntimeError" else str(err), now_ts=now_ts)
            return {"processed": False, "job": retry_job or job, "error": str(err)}
        updated = self.update_upload_job_state(job["job_id"], "synced", last_error_code="", next_retry_at=None)
        return {"processed": True, "job": updated or job, **(result or {})}

    def process_upload_job_by_id(self, job_id: str, uploader=None, branch_resolver=None, now_ts: float | None = None) -> dict:
        current = next((j for j in self.list_upload_jobs() if j.get("job_id") == job_id), None)
        if current and str(current.get("state") or "") == "synced":
            return {"processed": True, "already_synced": True, "job": current, "uploaded": [], "deleted": [], "skipped": []}
        job = self.claim_upload_job_by_id(job_id, now_ts=now_ts)
        if not job:
            return {"processed": False, "reason": "JOB_NOT_DUE_OR_MISSING", "job": current}
        if str(job.get("state") or "") == "synced":
            return {"processed": True, "already_synced": True, "job": job, "uploaded": [], "deleted": [], "skipped": []}
        return self._execute_claimed_upload_job(job, uploader=uploader, branch_resolver=branch_resolver, now_ts=now_ts)

    def process_next_upload_job(self, uploader=None, branch_resolver=None, now_ts: float | None = None) -> dict:
        job = self.claim_next_upload_job(now_ts=now_ts)
        if not job:
            return {"processed": False, "reason": "NO_DUE_JOB"}
        return self._execute_claimed_upload_job(job, uploader=uploader, branch_resolver=branch_resolver, now_ts=now_ts)

    def _checkpoint_record_path(self, checkpoint_id: str) -> pathlib.Path:
        return self.root / "reports" / f"{checkpoint_id}.json"

    def _normalize_checkpoint_record(self, record: dict | None) -> dict:
        data = record if isinstance(record, dict) else {}
        checkpoint_id = str(data.get("checkpoint_id") or "")
        return {
            "checkpoint_id": checkpoint_id,
            "project_key": self.key,
            "run_id": str(data.get("run_id") or checkpoint_id),
            "created_at": str(data.get("created_at") or _utc()),
            "artifact_state": str(data.get("artifact_state") or "empty"),
            "manifest_path": str(data.get("manifest_path") or ""),
            "archive_ref": str(data.get("archive_ref") or ""),
            "summary": data.get("summary") if isinstance(data.get("summary"), dict) else {},
            "files": data.get("files") if isinstance(data.get("files"), list) else [],
            "deleted_files": data.get("deleted_files") if isinstance(data.get("deleted_files"), list) else [],
            "status": str(data.get("status") or ""),
            "url": str(data.get("url") or ""),
            "schema_version": CHECKPOINT_RECORD_SCHEMA_VERSION,
            "checksum": str(data.get("checksum") or ""),
        }

    def _checkpoint_record_checksum(self, record: dict) -> str:
        normalized = self._normalize_checkpoint_record(record)
        normalized["checksum"] = ""
        payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _write_checkpoint_archive(self, checkpoint_id: str, checkpoint_dir: pathlib.Path) -> pathlib.Path:
        import tarfile
        archive_path = self._archive_path(checkpoint_id)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        temp = archive_path.with_suffix(".tmp")
        with tarfile.open(temp, mode="w:gz") as tf:
            if checkpoint_dir.exists():
                for item in sorted(checkpoint_dir.rglob("*")):
                    arcname = item.relative_to(checkpoint_dir).as_posix()
                    if item.is_dir() and not arcname:
                        continue
                    tf.add(item, arcname=arcname or ".")
        temp.replace(archive_path)
        return archive_path

    def _write_checkpoint_record(self, record: dict) -> dict:
        normalized = self._normalize_checkpoint_record(record)
        path = self._checkpoint_record_path(normalized["checkpoint_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized["manifest_path"] = path.relative_to(self.root).as_posix()
        normalized["checksum"] = self._checkpoint_record_checksum(normalized)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)
        return normalized

    def load_checkpoint_record(self, checkpoint_id: str) -> dict | None:
        path = self._checkpoint_record_path(checkpoint_id)
        if not path.exists() or not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(raw, dict):
            return None
        if raw.get("schema_version") != CHECKPOINT_RECORD_SCHEMA_VERSION:
            return None
        return self._normalize_checkpoint_record(raw)

    def verify_checkpoint_record_checksum(self, checkpoint_id: str) -> bool:
        record = self.load_checkpoint_record(checkpoint_id)
        if not record:
            return False
        expected = str(record.get("checksum") or "")
        return bool(expected) and expected == self._checkpoint_record_checksum(record)

    def snapshot(self, sandbox_dir, public_url, status, message):
        """نسخ streaming إلى hot checkpoint مع تسطيح مسار webapp واستبعاد الأرشيف والملفات السرية."""
        with self.lock:
            data = self._read(); stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            checkpoint = self._hot_checkpoint_path(stamp)
            checkpoint.mkdir(parents=True, exist_ok=True)
            files = []
            deleted_files = []
            raw_src = pathlib.Path(sandbox_dir) if sandbox_dir else None
            src = _resolve_effective_source_root(raw_src) if raw_src else None
            prior_index = data.get("file_index") if isinstance(data.get("file_index"), dict) else {}
            current_seen_at = _utc()
            seen_paths = set()
            if src and src.exists():
                for item in src.rglob("*"):
                    if item.is_file():
                        if _is_never_copy_file(item.name) or _should_skip_archive_member(item.name):
                            continue
                        rel = item.relative_to(src)
                        rel_path = pathlib.PurePosixPath(rel.as_posix()).as_posix()
                        if _should_skip_archive_member(rel_path):
                            continue
                        dest = checkpoint / rel; dest.parent.mkdir(parents=True, exist_ok=True)
                        # copy2 streams internally; لا يحمل الأرشيف الكبير في الذاكرة.
                        shutil.copy2(item, dest)
                        sha256 = _sha256_file(item)
                        files.append({"path": rel_path, "bytes": item.stat().st_size, "sha256": sha256})
                        seen_paths.add(rel_path)
            for item in files:
                previous_entry = prior_index.get(item["path"], {}) if isinstance(prior_index.get(item["path"]), dict) else {}
                if not previous_entry or previous_entry.get("deleted_at"):
                    classification = "ADDED"
                    changed = True
                elif previous_entry.get("sha256") != item["sha256"]:
                    classification = "MODIFIED"
                    changed = True
                else:
                    classification = "UNCHANGED"
                    changed = False
                item["changed"] = changed
                item["classification"] = classification
                prior_index[item["path"]] = {
                    "project_key": self.key,
                    "relative_path": item["path"],
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                    "last_seen_at": current_seen_at,
                    "deleted_at": None,
                }

            for rel_path, entry_prev in list(prior_index.items()):
                if rel_path in seen_paths or not isinstance(entry_prev, dict):
                    continue
                if entry_prev.get("deleted_at"):
                    continue
                entry_prev["deleted_at"] = current_seen_at
                deleted_files.append({
                    "path": rel_path,
                    "bytes": int(entry_prev.get("bytes") or 0),
                    "sha256": str(entry_prev.get("sha256") or ""),
                    "changed": True,
                    "classification": "DELETED",
                })

            summary = {
                "added": sum(1 for item in files if item.get("classification") == "ADDED"),
                "modified": sum(1 for item in files if item.get("classification") == "MODIFIED"),
                "unchanged": sum(1 for item in files if item.get("classification") == "UNCHANGED"),
                "deleted": len(deleted_files),
            }
            artifact_state = "files_present" if (files or deleted_files) else "empty"
            archive_path = self._write_checkpoint_archive(stamp, checkpoint)
            archive_ref = archive_path.relative_to(self.root).as_posix()
            checkpoint_record = self._write_checkpoint_record({
                "checkpoint_id": stamp,
                "run_id": stamp,
                "created_at": current_seen_at,
                "artifact_state": artifact_state,
                "archive_ref": archive_ref,
                "summary": summary,
                "files": files,
                "deleted_files": deleted_files,
                "status": status,
                "url": public_url or "",
            })
            data["file_index"] = prior_index
            entry = {
                "at": current_seen_at,
                "status": status,
                "url": public_url or "",
                "files": files,
                "deleted_files": deleted_files,
                "summary": summary,
                "artifact_state": artifact_state,
                "archive_ref": archive_ref,
                "manifest_path": checkpoint_record["manifest_path"],
                "checksum": checkpoint_record["checksum"],
                "message_preview": redact_github_secrets(str(message or ""))[:500],
                "checkpoint": stamp,
            }
            data["updates"].append(entry); data["checkpoints"].append(stamp)
            # hot checkpoints فقط آخر 3؛ archive التاريخي الكامل يبقى محفوظاً منفصلاً.
            for old in data["checkpoints"][:-3]:
                shutil.rmtree(self._hot_checkpoint_path(old), ignore_errors=True)
            data["checkpoints"] = data["checkpoints"][-3:]
            data["last_three_urls"] = [u.get("url", "") for u in data["updates"] if u.get("url")][-3:]
            self._write(data)
            return entry

    def github_sync(self, update, uploader=None, branch_resolver=None, now_ts: float | None = None):
        """في 01.19: أنشئ queue job ثم حاول معالجة نفس job فوراً إذا كانت إعدادات المشروع مكتملة."""
        sync = self.enqueue_github_sync(update)
        if not sync.get("enabled"):
            return sync
        job = (sync.get("jobs") or [{}])[0]
        job_id = str(job.get("job_id") or "")
        if not job_id:
            return {**sync, "upload_confirmed": False, "job_state": ""}
        execution = self.process_upload_job_by_id(job_id, uploader=uploader, branch_resolver=branch_resolver, now_ts=now_ts)
        final_job = execution.get("job") or job
        state = str((final_job or {}).get("state") or "")
        uploaded = list(execution.get("uploaded", []) or [])
        modified = list(execution.get("modified", []) or [])
        deleted = list(execution.get("deleted", []) or [])
        skipped = list(execution.get("skipped", []) or [])
        unchanged = list(execution.get("unchanged", []) or [])
        commit_hash = str(execution.get("commit_hash") or "")
        confirmed = bool(execution.get("processed")) and state == "synced"
        return {
            "enabled": True,
            "queued": [] if confirmed else [job_id],
            "jobs": [final_job] if final_job else [],
            "uploaded": uploaded,
            "modified": modified,
            "deleted": deleted,
            "unchanged": unchanged,
            "skipped": skipped,
            "commit_hash": commit_hash,
            "upload_confirmed": confirmed,
            "job_state": state,
            "upload_error": str(execution.get("error") or execution.get("reason") or ""),
        }

PROJECT_LOCKS = {}; PROJECT_LOCKS_GUARD = threading.Lock()
PROJECT_RUN_OWNERS = {}; PROJECT_RUN_OWNERS_GUARD = threading.Lock()
REGISTRY_INDEX_LOCK = threading.Lock()
PROJECT_MANIFEST_SCHEMA_VERSION = 1
CHECKPOINT_RECORD_SCHEMA_VERSION = 1


def get_project_lock(key):
    with PROJECT_LOCKS_GUARD:
        return PROJECT_LOCKS.setdefault(key, threading.Lock())


def claim_project_run(project_key: str, owner_token: str) -> bool:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    token = str(owner_token or "").strip()
    if not key or not token:
        return False
    with PROJECT_RUN_OWNERS_GUARD:
        current = PROJECT_RUN_OWNERS.get(key)
        if current and current != token:
            return False
        PROJECT_RUN_OWNERS[key] = token
        return True


def release_project_run(project_key: str, owner_token: str) -> bool:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    token = str(owner_token or "").strip()
    with PROJECT_RUN_OWNERS_GUARD:
        if PROJECT_RUN_OWNERS.get(key) != token:
            return False
        PROJECT_RUN_OWNERS.pop(key, None)
        return True


# ══════════════════════════════════════════════════════════════
# 🛑 [P25] Interactive Cancellation Manager — إلغاء تفاعلي فوري
# ══════════════════════════════════════════════════════════════
# مسجل مركزي Thread-Safe لأحداث الإلغاء النشطة:
#   token قصير (uuid hex 12) ← threading.Event + metadata
# السبب: callback_data في تيليجرام محدود بـ 64 بايت بينما
# project_key قد يبلغ 80 حرفاً — لذا نستخدم توكن قصيراً كمفتاح.
_ACTIVE_CANCEL_EVENTS: dict[str, dict] = {}
_CANCEL_EVENTS_GUARD = threading.Lock()
CANCELLED_STATUS = "CANCELLED"
USER_CANCELLED_MARKER = "__USER_CANCELLED__"


def new_cancel_token() -> str:
    """توليد توكن إلغاء قصير آمن للاستخدام داخل callback_data (≤ 64 بايت)"""
    return uuid.uuid4().hex[:12]


def register_cancel_event(token: str, project_key: str = "", chat_id=None) -> threading.Event | None:
    """تسجيل حدث إلغاء جديد لمهمة نشطة — يُرجع الـ Event للحقن في cfg.cancel_event"""
    key = str(token or "").strip()
    if not key:
        return None
    with _CANCEL_EVENTS_GUARD:
        entry = _ACTIVE_CANCEL_EVENTS.get(key)
        if entry is not None:
            return entry["event"]
        ev = threading.Event()
        _ACTIVE_CANCEL_EVENTS[key] = {
            "event": ev,
            "project_key": str(project_key or ""),
            "chat_id": chat_id,
            "created_at": time.time(),
        }
        return ev


def get_cancel_entry(token: str) -> dict | None:
    """قراءة metadata حدث الإلغاء (نسخة آمنة) — None لو التوكن غير مسجل/منتهي"""
    key = str(token or "").strip()
    if not key:
        return None
    with _CANCEL_EVENTS_GUARD:
        entry = _ACTIVE_CANCEL_EVENTS.get(key)
        return dict(entry) if isinstance(entry, dict) else None


def update_cancel_entry(token: str, **fields) -> bool:
    """تحديث metadata حدث إلغاء نشط (مثل live_pid و message_id لبطاقة المعاينة)"""
    key = str(token or "").strip()
    if not key:
        return False
    with _CANCEL_EVENTS_GUARD:
        entry = _ACTIVE_CANCEL_EVENTS.get(key)
        if not isinstance(entry, dict):
            return False
        entry.update(fields)
        return True


def trigger_cancel(token: str) -> bool:
    """تفعيل الإلغاء القهري — يضبط الـ Event فيلتقطه المحرك وحلقات المتابعة فوراً"""
    key = str(token or "").strip()
    if not key:
        return False
    with _CANCEL_EVENTS_GUARD:
        entry = _ACTIVE_CANCEL_EVENTS.get(key)
        if not isinstance(entry, dict):
            return False
        entry["event"].set()
        entry["cancelled_at"] = time.time()
        return True


def is_cancel_requested(token: str) -> bool:
    """فحص سريع: هل طُلب إلغاء هذه المهمة؟"""
    key = str(token or "").strip()
    if not key:
        return False
    with _CANCEL_EVENTS_GUARD:
        entry = _ACTIVE_CANCEL_EVENTS.get(key)
        return bool(entry and entry["event"].is_set())


def unregister_cancel_event(token: str) -> bool:
    """تنظيف مضمون بعد انتهاء المهمة (نجاحاً/فشلاً/إلغاءً) — Zero Leaks"""
    key = str(token or "").strip()
    if not key:
        return False
    with _CANCEL_EVENTS_GUARD:
        return _ACTIVE_CANCEL_EVENTS.pop(key, None) is not None


def _utc(): return datetime.now(timezone.utc).isoformat()
def _sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""): h.update(block)
    return h.hexdigest()


def is_probable_project_id(value: str | None) -> bool:
    text = str(value or "").strip()
    if not text or text == "غير معروف" or "__INVALID_PROJECT__" in text:
        return False
    if "login" in text.lower() or "/" in text or " " in text:
        return False
    return bool(re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", text, re.IGNORECASE))


def extract_stage_project_id(stage_url: str | None, stage_dir: str | None = None) -> str:
    pid = extract_project_id(stage_url) if stage_url else ""
    if is_probable_project_id(pid):
        return pid
    if stage_dir:
        candidate = pathlib.Path(stage_dir).name
        if is_probable_project_id(candidate):
            return candidate
    return ""


REGISTRY_INDEX_SCHEMA_VERSION = 1


def _registry_index_backup_path() -> pathlib.Path:
    return PROJECT_REGISTRY_INDEX_FILE.with_suffix(".bak")


def _project_record_default(project_key: str) -> dict:
    return {
        "project_key": project_key,
        "root_genspark_pid": "",
        "latest_genspark_pid": "",
        "project_name": "",
        "chat_id": None,
        "status": "",
        "created_at": _utc(),
        "updated_at": _utc(),
        "schema_version": REGISTRY_INDEX_SCHEMA_VERSION,
    }


def _normalize_project_record(project_key: str, record: dict | None) -> dict:
    base = _project_record_default(project_key)
    if isinstance(record, dict):
        for field_name in ("root_genspark_pid", "latest_genspark_pid", "project_name", "status", "created_at", "updated_at"):
            if record.get(field_name) is not None:
                base[field_name] = record.get(field_name)
        if record.get("chat_id") is not None:
            try:
                base["chat_id"] = int(record.get("chat_id"))
            except Exception:
                base["chat_id"] = None
    base["schema_version"] = REGISTRY_INDEX_SCHEMA_VERSION
    return base


def _registry_index_default() -> dict:
    return {"schema_version": REGISTRY_INDEX_SCHEMA_VERSION, "projects": {}, "pid_to_key": {}}


def _normalize_registry_index_payload(data: dict) -> dict:
    projects_src = data.get("projects") if isinstance(data.get("projects"), dict) else {}
    pid_to_key_src = data.get("pid_to_key") if isinstance(data.get("pid_to_key"), dict) else {}
    normalized_projects = {}
    normalized_aliases = {}
    for raw_key, raw_record in projects_src.items():
        key = re.sub(r"[^A-Za-z0-9_-]", "_", str(raw_key or ""))[:80]
        if not key:
            continue
        record = _normalize_project_record(key, raw_record)
        for pid_field in ("root_genspark_pid", "latest_genspark_pid"):
            pid_value = extract_project_id(record.get(pid_field)) if record.get(pid_field) else ""
            if not is_probable_project_id(pid_value):
                record[pid_field] = ""
            else:
                record[pid_field] = pid_value
                normalized_aliases[pid_value] = key
        normalized_projects[key] = record
    for pid, key in pid_to_key_src.items():
        pid_str = extract_project_id(pid) if pid else ""
        key_str = re.sub(r"[^A-Za-z0-9_-]", "_", str(key or ""))[:80]
        if is_probable_project_id(pid_str) and key_str in normalized_projects:
            normalized_aliases.setdefault(pid_str, key_str)
    return {
        "schema_version": REGISTRY_INDEX_SCHEMA_VERSION,
        "projects": normalized_projects,
        "pid_to_key": normalized_aliases,
    }


def _read_registry_index() -> dict:
    if not PROJECT_REGISTRY_INDEX_FILE.exists():
        return _registry_index_default()
    try:
        data = json.loads(PROJECT_REGISTRY_INDEX_FILE.read_text(encoding="utf-8"))
    except Exception as err:
        log_event("warning", f"تعذر قراءة registry index؛ سيتم التعامل معه fail-closed: {type(err).__name__}")
        return _registry_index_default()
    if not isinstance(data, dict):
        log_event("warning", "ملف registry index ليس JSON object؛ تم التعامل معه fail-closed")
        return _registry_index_default()

    schema_version = data.get("schema_version")
    if schema_version is None:
        normalized = _normalize_registry_index_payload(data)
        if normalized["projects"] or normalized["pid_to_key"]:
            try:
                _write_registry_index(normalized)
            except Exception:
                pass
        return normalized
    if schema_version != REGISTRY_INDEX_SCHEMA_VERSION:
        log_event("warning", f"schema_version غير معروف في registry index: {schema_version} — تم التعامل fail-closed")
        return _registry_index_default()
    return _normalize_registry_index_payload(data)


def _write_registry_index(data: dict):
    PROJECT_REGISTRY_HOME.mkdir(parents=True, exist_ok=True)
    normalized = _normalize_registry_index_payload(data)
    if PROJECT_REGISTRY_INDEX_FILE.exists():
        backup = _registry_index_backup_path()
        backup.write_text(PROJECT_REGISTRY_INDEX_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    temp = PROJECT_REGISTRY_INDEX_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(PROJECT_REGISTRY_INDEX_FILE)


def lookup_project_key_for_locator(url_or_pid: str | None) -> str | None:
    pid = extract_project_id(url_or_pid) if url_or_pid else ""
    if not is_probable_project_id(pid):
        return None
    with REGISTRY_INDEX_LOCK:
        data = _read_registry_index()
        key = data["pid_to_key"].get(pid)
        return str(key) if key else None


def get_project_identity_record(project_key: str) -> dict | None:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        return None
    with REGISTRY_INDEX_LOCK:
        record = _read_registry_index()["projects"].get(key)
        return dict(record) if isinstance(record, dict) else None


def resolve_resume_context(url_or_pid: str | None) -> dict:
    pid = extract_project_id(url_or_pid) if url_or_pid else ""
    target_url = f"https://www.genspark.ai/autopilotagent_viewer?id={pid}" if is_probable_project_id(pid) else str(url_or_pid or "")
    project_key = lookup_project_key_for_locator(url_or_pid) if url_or_pid else None
    identity = get_project_identity_record(project_key) if project_key else None
    project_name = ""
    if identity and identity.get("project_name"):
        project_name = str(identity.get("project_name"))
    return {
        "pid": pid,
        "target_url": target_url,
        "project_key": project_key or "",
        "project_name": project_name,
        "identity": identity or {},
    }


def upsert_project_identity(
    project_key: str,
    root_pid: str | None = None,
    latest_pid: str | None = None,
    project_name: str | None = None,
    chat_id: int | None = None,
    status: str | None = None,
) -> dict:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        raise ValueError("project_key missing")
    clean_root = extract_project_id(root_pid) if root_pid else ""
    clean_latest = extract_project_id(latest_pid) if latest_pid else ""
    if not is_probable_project_id(clean_root):
        clean_root = ""
    if not is_probable_project_id(clean_latest):
        clean_latest = ""

    with REGISTRY_INDEX_LOCK:
        data = _read_registry_index()
        record = data["projects"].get(key, {"project_key": key, "created_at": _utc()})
        if clean_root and not record.get("root_genspark_pid"):
            record["root_genspark_pid"] = clean_root
        if clean_latest:
            record["latest_genspark_pid"] = clean_latest
        if project_name:
            record["project_name"] = str(project_name)
        if chat_id is not None:
            record["chat_id"] = int(chat_id)
        if status:
            record["status"] = str(status)
        if not record.get("latest_genspark_pid") and record.get("root_genspark_pid"):
            record["latest_genspark_pid"] = record["root_genspark_pid"]
        record["updated_at"] = _utc()
        data["projects"][key] = record

        alias_values = [record.get("root_genspark_pid"), record.get("latest_genspark_pid"), clean_root, clean_latest]
        for alias in alias_values:
            if alias and is_probable_project_id(alias):
                data["pid_to_key"][alias] = key

        _write_registry_index(data)
        return dict(record)


def remember_registry_identity(registry, **kwargs):
    if registry is None or not hasattr(registry, "remember_identity"):
        return None
    return registry.remember_identity(**kwargs)


# ══════════════════════════════════════════════════════════════
# 🗑️ [P26] Interactive Project Deletion & Atomic Cleanup
# ══════════════════════════════════════════════════════════════
# حذف مشروع محفوظ نهائياً بترتيب آمن (Fail-Safe Ordering):
#   1. حماية: منع الحذف لو المشروع له بناء نشط الآن (_ACTIVE_CANCEL_EVENTS).
#   2. الفهرس أولاً تحت REGISTRY_INDEX_LOCK (قيد المشروع + كل pid aliases).
#   3. شجرة التفريع projects_tree.json (مفتاحها root_pid وليس project_key).
#   4. أخيراً مجلد المشروع على القرص project_registry/<key>/ عبر rmtree.
# السبب: لو فشل rmtree بعد تنظيف الفهارس يبقى مجرد مجلد يتيم غير مرئي
# للنظام — أهون بكثير من قيد فهرس يشير لمجلد محذوف.


def is_project_build_active(project_key: str) -> bool:
    """فحص الحماية [P26]: هل للمشروع بناء نشط الآن (Event مسجل وغير مُلغى)؟"""
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        return False
    with _CANCEL_EVENTS_GUARD:
        for entry in _ACTIVE_CANCEL_EVENTS.values():
            if not isinstance(entry, dict):
                continue
            if str(entry.get("project_key") or "") == key and not entry["event"].is_set():
                return True
    return False


def _remove_project_from_tree_file(pids: list[str]) -> int:
    """إزالة قيود شجرة التفريع لمشروع محذوف — الشجرة مفتاحها root_pid.

    يُرجع عدد الجذور المحذوفة. كتابة ذرية (tmp ثم replace) كنمط save_project_tree.
    """
    clean_pids = [p for p in pids if p and is_probable_project_id(p)]
    if not clean_pids or not PROJECTS_TREE_FILE.exists():
        return 0
    try:
        with open(PROJECTS_TREE_FILE, "r", encoding="utf-8", errors="ignore") as f:
            tree_data = json.load(f)
    except Exception:
        return 0
    if not isinstance(tree_data, dict):
        return 0
    removed = 0
    for pid in clean_pids:
        if pid in tree_data:
            tree_data.pop(pid, None)
            removed += 1
    if not removed:
        return 0
    try:
        tmp_file = PROJECTS_TREE_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(PROJECTS_TREE_FILE)
    except Exception as err:
        log_event("warning", f"🗑️ [P26] تنبيه أثناء تنظيف شجرة التفريع: {err}")
        return 0
    return removed


def delete_project_atomically(project_key: str) -> dict:
    """الحذف الذري الشامل [P26] — يُرجع dict بالنتيجة دون رفع استثناءات.

    الترتيب الآمن: حماية التشغيل ➔ الفهرس (تحت القفل) ➔ الشجرة ➔ القرص.
    """
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    result = {
        "ok": False,
        "project_key": key,
        "project_name": "",
        "reason": "",
        "index_removed": False,
        "aliases_removed": 0,
        "tree_removed": 0,
        "disk_removed": False,
    }
    if not key:
        result["reason"] = "PROJECT_KEY_MISSING"
        return result

    # 1️⃣ فحص الحماية: ممنوع حذف مشروع له بناء شغال الآن
    if is_project_build_active(key):
        result["reason"] = "PROJECT_BUILD_ACTIVE"
        return result

    # 2️⃣ تنظيف الفهرس المركزي registry.json تحت القفل (القيد + كل aliases)
    project_pids: list[str] = []
    with REGISTRY_INDEX_LOCK:
        data = _read_registry_index()
        record = data["projects"].pop(key, None)
        if isinstance(record, dict):
            result["index_removed"] = True
            result["project_name"] = str(record.get("project_name") or "")
            for pid_field in ("root_genspark_pid", "latest_genspark_pid"):
                pid_value = str(record.get(pid_field) or "")
                if is_probable_project_id(pid_value) and pid_value not in project_pids:
                    project_pids.append(pid_value)
        stale_aliases = [pid for pid, mapped in data["pid_to_key"].items() if mapped == key]
        for pid in stale_aliases:
            data["pid_to_key"].pop(pid, None)
            if pid not in project_pids:
                project_pids.append(pid)
        result["aliases_removed"] = len(stale_aliases)
        if result["index_removed"] or stale_aliases:
            try:
                _write_registry_index(data)
            except Exception as err:
                log_event("error", f"🗑️ [P26] فشل كتابة registry index أثناء الحذف: {err}")
                result["reason"] = "INDEX_WRITE_FAILED"
                return result

    # 3️⃣ تنظيف شجرة التفريع (مفاتيحها root_pid — تُتخطى بأمان لو لا يوجد pid)
    result["tree_removed"] = _remove_project_from_tree_file(project_pids)

    # 4️⃣ حذف مجلد المشروع كاملاً من القرص project_registry/<key>/
    project_dir = PROJECT_REGISTRY_HOME / key
    if project_dir.exists() and project_dir.is_dir():
        try:
            shutil.rmtree(project_dir)
            result["disk_removed"] = True
        except Exception as err:
            log_event("error", f"🗑️ [P26] فشل حذف مجلد المشروع من القرص: {err}")
            result["reason"] = "DISK_REMOVE_FAILED"
            # الفهارس نظيفة بالفعل — الحذف منطقياً ناجح مع مجلد يتيم
            result["ok"] = bool(result["index_removed"])
            return result

    if not result["index_removed"] and not result["disk_removed"]:
        result["reason"] = "PROJECT_NOT_FOUND"
        return result

    result["ok"] = True
    log_event(
        "info",
        f"🗑️ [P26] تم حذف المشروع نهائياً: key={key} "
        f"(index={result['index_removed']}, aliases={result['aliases_removed']}, "
        f"tree={result['tree_removed']}, disk={result['disk_removed']})",
    )
    return result


def build_genspark_viewer_url(project_id: str | None) -> str:
    pid = extract_project_id(project_id) if project_id else ""
    if not is_probable_project_id(pid):
        return ""
    return f"https://www.genspark.ai/autopilotagent_viewer?id={pid}"


def build_viewer_url(project_id: str | None) -> str:
    """بناء رابط العارض السحابي مع ترميز المعرف بأمان"""
    clean_id = urllib.parse.quote(str(project_id or "").strip(), safe="")
    return f"https://www.genspark.ai/autopilotagent_viewer?id={clean_id}"


def build_live_preview_keyboard(project_id: str, status: str = "running", cancel_token: str | None = None) -> dict:
    """بناء Inline URL Button نظيف ومتوافق 100% مع جميع إصدارات تيليجرام.

    🛑 [P25] cancel_token اختياري (توافق خلفي كامل):
      - بدونه: نفس الكيبورد القديم حرفياً.
      - معه + status=running: صف ثانٍ بزر إلغاء أحمر (danger).
      - status=confirm_cancel: كيبورد تأكيد بخطوتي أمان (نعم أحمر / تراجع أزرق).
    """
    viewer_url = build_viewer_url(project_id)
    if status == "confirm_cancel" and cancel_token:
        # 🚨 خطوة التأكيد — منع الإلغاء الخاطئ بضغطة عفوية
        return make_inline_keyboard([
            [{"text": "🚨 نعم، إلغاء فوري", "callback_data": f"cancel_exec:{cancel_token}", "style": "danger"}],
            [{"text": "↩️ لا، تراجع واستمرار", "callback_data": f"cancel_abort:{cancel_token}", "style": "primary"}],
        ])
    if status == "running":
        # 🎨 أزرق (primary) أثناء البناء — Bot API 9.4 Button Styles
        rows = [[
            {"text": "🌐 ⚡ فتح المعاينة ومتابعة البناء لايف ↗️", "url": viewer_url, "style": "primary"}
        ]]
        if cancel_token:
            # 🛑 أحمر (danger) — الضغطة الأولى تفتح كيبورد التأكيد فقط (لا تلغي)
            rows.append([{"text": "🛑 إلغاء البناء الحالي", "callback_data": f"cancel_prompt:{cancel_token}", "style": "danger"}])
        return make_inline_keyboard(rows)
    else:
        # 🎨 أخضر (success) عند الاكتمال
        return make_inline_keyboard([[
            {"text": "🟢 فتح المشروع المكتمل ↗️", "url": viewer_url, "style": "success"}
        ]])


def summarize_project_context(identity: dict | None, current_pid: str | None = None, current_url: str | None = None) -> dict:
    identity = identity if isinstance(identity, dict) else {}
    root_pid = extract_project_id(identity.get("root_genspark_pid")) if identity.get("root_genspark_pid") else ""
    latest_pid = extract_project_id(identity.get("latest_genspark_pid")) if identity.get("latest_genspark_pid") else ""
    current_pid_clean = extract_project_id(current_pid) if current_pid else ""
    if not is_probable_project_id(root_pid):
        root_pid = ""
    if not is_probable_project_id(latest_pid):
        latest_pid = ""
    if not is_probable_project_id(current_pid_clean):
        current_pid_clean = latest_pid or root_pid
    latest_or_current = latest_pid or current_pid_clean or root_pid
    root_or_current = root_pid or current_pid_clean or latest_pid
    current_url_text = str(current_url or "").strip()
    if not current_url_text and current_pid_clean:
        current_url_text = build_genspark_viewer_url(current_pid_clean)
    resume_pid = latest_or_current or root_or_current
    resume_url = build_genspark_viewer_url(resume_pid) if resume_pid else current_url_text
    return {
        "root_pid": root_or_current,
        "latest_pid": latest_or_current,
        "current_pid": current_pid_clean or latest_or_current,
        "root_url": build_genspark_viewer_url(root_or_current),
        "current_url": current_url_text,
        "resume_pid": resume_pid,
        "resume_url": resume_url,
        "forked": bool(root_or_current and latest_or_current and root_or_current != latest_or_current),
    }


def parse_github_repository_ref(text: str | None) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    patterns = [
        r"^(?:https?://)?github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$",
        r"^git@github\.com:(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?$",
        r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, raw, re.IGNORECASE)
        if match:
            owner = str(match.group("owner") or "").strip()
            repo = str(match.group("repo") or "").strip()
            if owner and repo:
                return f"{owner}/{repo}"
    return ""


def build_github_api_headers(token: str | None = None) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    clean = str(token or "").strip()
    if clean:
        headers["Authorization"] = f"Bearer {clean}"
    return headers


def _extract_items_from_github_response(resp: dict) -> list:
    payload = resp.get("json") if isinstance(resp, dict) else resp
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("items") or payload.get("branches") or []
    return []


def _github_api_get_json(url: str, *, headers: dict, params: dict | None = None, timeout: int = 20, requester=None) -> dict:
    if requester is not None:
        return requester("GET", url, headers=headers, params=params, timeout=timeout)
    import requests
    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    try:
        payload = response.json()
    except Exception:
        payload = {}
    return {
        "status_code": int(getattr(response, "status_code", 0) or 0),
        "json": payload if isinstance(payload, (dict, list)) else {},
        "text": str(getattr(response, "text", "") or "")[:300],
    }


def inspect_github_repository(repo_ref: str, token: str | None = None, requester=None, inspector=None) -> dict:
    repository = parse_github_repository_ref(repo_ref)
    if not repository:
        return {
            "ok": False,
            "repository": "",
            "default_branch": "",
            "branches": [],
            "is_private": False,
            "used_token": False,
            "reason": "صيغة المستودع غير صالحة؛ استخدم owner/repo أو رابط GitHub مباشر.",
        }
    if inspector is not None:
        info = inspector(repository)
        if not isinstance(info, dict):
            return {"ok": False, "repository": repository, "default_branch": "", "branches": [], "is_private": False, "used_token": bool(token), "reason": "inspector returned non-dict"}
        branches = [str(x) for x in (info.get("branches") or []) if str(x).strip()][:500]
        default_branch = str(info.get("default_branch") or (branches[0] if branches else "")).strip()
        ok = bool(info.get("ok", bool(default_branch or branches)))
        return {
            "ok": ok,
            "repository": repository,
            "default_branch": default_branch,
            "branches": branches,
            "is_private": bool(info.get("is_private", False)),
            "used_token": bool(token),
            "reason": str(info.get("reason") or ""),
        }

    clean_token = str(token or "").strip() or get_default_github_token_from_env()
    headers = build_github_api_headers(clean_token)
    repo_resp = _github_api_get_json(
        f"https://api.github.com/repos/{repository}",
        headers=headers,
        requester=requester,
        timeout=20,
    )
    status_code = int(repo_resp.get("status_code") or 0)
    repo_payload = repo_resp.get("json") if isinstance(repo_resp.get("json"), dict) else {}
    if status_code != 200:
        if status_code in (401, 403):
            reason = "التوكن غير صالح أو لا يملك صلاحية كافية لفحص المستودع."
        elif status_code == 404:
            reason = "المستودع غير موجود أو خاص ويحتاج GitHub token صالح لهذا المشروع."
        else:
            reason = f"تعذر فحص المستودع الآن: HTTP_{status_code or 'UNKNOWN'}"
        return {
            "ok": False,
            "repository": repository,
            "default_branch": "",
            "branches": [],
            "is_private": False,
            "used_token": bool(clean_token),
            "reason": reason,
        }

    default_branch = str(repo_payload.get("default_branch") or "").strip()
    is_private = bool(repo_payload.get("private", False))
    branches = []
    seen_branches = set()
    page = 1
    max_pages = 50
    branch_status = 200

    while page <= max_pages:
        branches_resp = _github_api_get_json(
            f"https://api.github.com/repos/{repository}/branches",
            headers=headers,
            params={"per_page": 100, "page": page},
            requester=requester,
            timeout=20,
        )
        branch_status = int(branches_resp.get("status_code") or 0)
        if branch_status not in (0, 200):
            break
        items = _extract_items_from_github_response(branches_resp)
        if not items:
            break
        new_count = 0
        for item in items:
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                if name and name not in seen_branches:
                    seen_branches.add(name)
                    branches.append(name)
                    new_count += 1
        if len(items) < 100 or new_count == 0:
            break
        page += 1

    if default_branch and default_branch in branches:
        branches.remove(default_branch)
        branches.insert(0, default_branch)
    elif default_branch and default_branch not in branches:
        branches.insert(0, default_branch)

    if branch_status not in (0, 200):
        reason = f"تم الوصول للمستودع لكن تعذر جلب الفروع الآن: HTTP_{branch_status}"
    else:
        reason = ""
    return {
        "ok": bool(default_branch or branches),
        "repository": repository,
        "default_branch": default_branch,
        "branches": branches,
        "is_private": is_private,
        "used_token": bool(clean_token),
        "reason": reason,
    }


def configure_project_github_settings(
    project_key: str,
    *,
    enabled: bool,
    repository: str = "",
    branch: str = "",
    branch_mode: str = "disabled",
    detected_default_branch: str = "",
    available_branches: list[str] | None = None,
    repo_check_status: str = "",
    token: str | None = None,
) -> dict:
    registry = ProjectRegistry(project_key)
    if token is not None:
        if str(token).strip():
            registry.set_project_github_token(token)
        else:
            registry.clear_project_github_token()
    settings = {
        "github": {
            "configured": True,
            "enabled": bool(enabled),
            "repository": parse_github_repository_ref(repository) if enabled else "",
            "branch": str(branch or "").strip(),
            "branch_mode": str(branch_mode or ("manual" if branch else ("auto_default" if enabled else "disabled"))),
            "detected_default_branch": str(detected_default_branch or "").strip(),
            "available_branches": [str(x) for x in (available_branches or []) if str(x).strip()][:20],
            "last_repo_check_status": str(repo_check_status or ("checked" if enabled else "disabled")),
            "last_repo_check_at": _utc(),
        }
    }
    if not enabled:
        settings["github"]["branch"] = ""
        settings["github"]["branch_mode"] = "disabled"
        settings["github"]["detected_default_branch"] = ""
        settings["github"]["available_branches"] = []
    return registry.update_project_settings(settings)


def list_known_projects(chat_id: int | None = None, limit: int | None = None) -> list[dict]:
    with REGISTRY_INDEX_LOCK:
        data = _read_registry_index()
    projects = []
    for key, raw_record in (data.get("projects") or {}).items():
        record = _normalize_project_record(key, raw_record)
        if chat_id is not None and record.get("chat_id") != int(chat_id):
            continue
        projects.append(record)
    projects.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
    if limit is not None:
        projects = projects[:max(0, int(limit))]
    return projects


def get_latest_project_for_chat(chat_id: int) -> dict | None:
    projects = list_known_projects(chat_id=chat_id, limit=1)
    return projects[0] if projects else None


def get_project_dashboard_snapshot(project_key: str) -> dict:
    identity = get_project_identity_record(project_key) or {}
    registry = ProjectRegistry(project_key)
    manifest = registry._read()
    updates = manifest.get("updates") if isinstance(manifest.get("updates"), list) else []
    checkpoints = manifest.get("checkpoints") if isinstance(manifest.get("checkpoints"), list) else []
    queue_jobs = registry.list_upload_jobs()
    settings = registry.get_project_settings().get("github", {})
    latest_update = updates[-1] if updates else {}
    context = summarize_project_context(identity, current_pid=identity.get("latest_genspark_pid"), current_url=latest_update.get("url"))
    github_label = "غير مفعل"
    if settings.get("configured") and settings.get("enabled"):
        branch_label = settings.get("branch") or settings.get("detected_default_branch") or "auto-default"
        github_label = f"{settings.get('repository') or 'غير معروف'} @ {branch_label}"
    elif settings.get("configured"):
        github_label = "معطل لهذا المشروع"
    return {
        "project_key": project_key,
        "project_name": str(identity.get("project_name") or project_key),
        "status": str(identity.get("status") or latest_update.get("status") or "UNKNOWN"),
        "chat_id": identity.get("chat_id"),
        "updated_at": str(identity.get("updated_at") or manifest.get("updated_at") or ""),
        "updates_count": len(updates),
        "checkpoints_count": len(checkpoints),
        "queue_open_count": sum(1 for job in queue_jobs if str(job.get("state") or "") not in {"synced", "failed"}),
        "queue_total_count": len(queue_jobs),
        "latest_checkpoint": str((latest_update or {}).get("checkpoint") or ""),
        "latest_url": str((latest_update or {}).get("url") or context.get("resume_url") or ""),
        "root_pid": context.get("root_pid") or "",
        "latest_pid": context.get("latest_pid") or "",
        "resume_pid": context.get("resume_pid") or "",
        "resume_url": context.get("resume_url") or "",
        "github_label": github_label,
        "has_pid": bool(context.get("resume_pid")),
    }


def count_ready_accounts() -> int:
    accounts = read_accounts_safe()
    try:
        return len(get_eligible_accounts(accounts, set()))
    except Exception:
        return 0


def build_dashboard_snapshot(chat_id: int) -> dict:
    projects = list_known_projects(chat_id=chat_id)
    current = get_project_dashboard_snapshot(projects[0]["project_key"]) if projects else None
    running_keys = set(PROJECT_RUN_OWNERS.keys())
    running_for_chat = sum(1 for project in projects if project.get("project_key") in running_keys)
    queue_open = 0
    github_enabled = 0
    for project in projects:
        snap = get_project_dashboard_snapshot(project["project_key"])
        queue_open += snap["queue_open_count"]
        if "@" in snap["github_label"] or snap["github_label"].startswith("env:"):
            github_enabled += 1
    return {
        "projects_count": len(projects),
        "running_count": running_for_chat,
        "ready_accounts": count_ready_accounts(),
        "queue_open": queue_open,
        "github_enabled": github_enabled,
        "latest_project": current,
        "projects": projects,
    }


# 🎨 أنماط الألوان الرسمية لأزرار تيليجرام (Bot API 9.4 — Button Styles)
# القيم الوحيدة المسموحة رسمياً: primary (أزرق) / success (أخضر) / danger (أحمر)
# ⚠️ أي قيمة أخرى (positive/destructive/...) ترجع 400 invalid button style — لذلك الـ Whitelist صارمة
ALLOWED_BUTTON_STYLES = frozenset({"primary", "success", "danger"})


def make_inline_keyboard(rows: list[list[dict]] | None) -> dict:
    safe_rows = []
    for row in rows or []:
        if not isinstance(row, list):
            continue
        safe_buttons = []
        for button in row:
            if not isinstance(button, dict):
                continue
            text = str(button.get("text") or "").strip()
            callback_data = str(button.get("callback_data") or "").strip()
            url = str(button.get("url") or "").strip()
            if not text:
                continue
            if not callback_data and not url:
                continue
            safe_button = {"text": text}
            if callback_data:
                safe_button["callback_data"] = callback_data
            if url:
                safe_button["url"] = url
            # 🎨 حقل style الاختياري (Bot API 9.4): يمرر فقط لو كان ضمن الـ Whitelist الرسمية
            # لأننا نرسل reply_markup كـ JSON خام مباشرة، الحقل يصل لتيليجرام بدون أي مكتبة وسيطة
            style = str(button.get("style") or "").strip().lower()
            if style in ALLOWED_BUTTON_STYLES:
                safe_button["style"] = style
            safe_buttons.append(safe_button)
        if safe_buttons:
            safe_rows.append(safe_buttons)
    return {"inline_keyboard": safe_rows}


def render_dashboard_text(chat_id: int) -> str:
    snapshot = build_dashboard_snapshot(chat_id)
    latest = snapshot.get("latest_project") or {}
    latest_line = "لا يوجد بعد"
    if latest:
        latest_line = f"{latest.get('project_name')} / {latest.get('project_key')}"
    github_status = "✅" if snapshot.get("github_enabled") else "❌"
    return (
        f"🤖 <b>Genspark Multi-Project Bridge v{BUILD_VERSION}</b>\n\n"
        "📊 <b>الحالة</b>\n"
        f"• المشاريع المعروفة: <b>{snapshot.get('projects_count', 0)}</b>\n"
        f"• المهام الجارية: <b>{snapshot.get('running_count', 0)}</b>\n"
        f"• الحسابات الجاهزة: <b>{snapshot.get('ready_accounts', 0)}</b>\n"
        f"• Upload Queue المفتوحة: <b>{snapshot.get('queue_open', 0)}</b>\n"
        f"• GitHub للمشاريع: <b>{github_status}</b>\n"
        f"• آخر مشروع: <code>{html_escape(latest_line)}</code>\n\n"
        "💡 <b>دليل سريع</b>\n"
        "• مشروع جديد: يبدأ Wizard باسم مشروع ثم GitHub أو بدون GitHub.\n"
        "• مشاريعي: يعرض المشاريع المحفوظة كأزرار جاهزة للاستكمال.\n"
        "• المشروع الحالي: يعرض حالة آخر مشروع محفوظ من الـRegistry الحقيقية.\n"
        "• عند نفاد الرصيد: يحفظ checkpoint ثم يكمل بنفس مفتاح المشروع."
    )


def render_project_status_text(project_key: str) -> str:
    snap = get_project_dashboard_snapshot(project_key)
    settings = ProjectRegistry(project_key).get_project_settings()
    checkpoint_line = f"\n• آخر checkpoint: <code>{html_escape(snap['latest_checkpoint'])}</code>" if snap.get("latest_checkpoint") else ""
    resume_line = f"\n• رابط/سياق الاستئناف: {html_escape(snap['resume_url'])}" if snap.get("resume_url") else ""
    pid_line = f"\n• Latest PID: <code>{html_escape(snap['latest_pid'])}</code>" if snap.get("latest_pid") else ""
    root_line = f"\n• Root PID: <code>{html_escape(snap['root_pid'])}</code>" if snap.get("root_pid") else ""
    model_line = f"\n• الموديل: <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>"
    resume_prompt_line = f"\n• برومبت الاستئناف: <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>"
    return (
        f"⭐ <b>المشروع الحالي</b>\n"
        f"• الاسم: <b>{html_escape(snap['project_name'])}</b>\n"
        f"• المفتاح: <code>{html_escape(snap['project_key'])}</code>\n"
        f"• الحالة: <code>{html_escape(snap['status'])}</code>\n"
        f"• التحديثات: <b>{snap['updates_count']}</b>\n"
        f"• checkpoints الساخنة: <b>{snap['checkpoints_count']}</b>\n"
        f"• Upload Queue المفتوحة: <b>{snap['queue_open_count']}</b> من أصل <b>{snap['queue_total_count']}</b>{model_line}{resume_prompt_line}\n"
        f"• GitHub: <code>{html_escape(snap['github_label'])}</code>{checkpoint_line}{root_line}{pid_line}{resume_line}"
    )


def render_project_checkpoints_text(project_key: str) -> str:
    registry = ProjectRegistry(project_key)
    manifest = registry._read()
    checkpoint_ids = list(manifest.get("checkpoints") or [])[-3:]
    if not checkpoint_ids:
        return "🗂 <b>آخر 3 checkpoints</b>\nلا توجد checkpoints محفوظة بعد لهذا المشروع."
    lines = ["🗂 <b>آخر 3 checkpoints</b>"]
    for checkpoint_id in reversed(checkpoint_ids):
        record = registry.load_checkpoint_record(checkpoint_id) or {}
        summary = record.get("summary") or {}
        lines.append(
            f"• <code>{html_escape(checkpoint_id)}</code> — status=<code>{html_escape(str(record.get('status') or 'UNKNOWN'))}</code>"
            f" — A/M/D/U={summary.get('added', 0)}/{summary.get('modified', 0)}/{summary.get('deleted', 0)}/{summary.get('unchanged', 0)}"
        )
    return "\n".join(lines)


def render_project_archive_text(project_key: str) -> str:
    registry = ProjectRegistry(project_key)
    manifest = registry._read()
    updates = manifest.get("updates") or []
    latest = updates[-1] if updates else {}
    archive_ref = str(latest.get("archive_ref") or "")
    if not archive_ref:
        return "📦 <b>آخر Archive</b>\nلا يوجد archive محفوظ بعد لهذا المشروع."
    archive_path = registry.root / archive_ref
    return (
        "📦 <b>آخر Archive</b>\n"
        f"• المرجع: <code>{html_escape(archive_ref)}</code>\n"
        f"• المسار المحلي: <code>{html_escape(str(archive_path))}</code>\n"
        f"• موجود الآن: <b>{'نعم' if archive_path.exists() else 'لا'}</b>"
    )


def render_project_history_text(project_key: str) -> str:
    registry = ProjectRegistry(project_key)
    updates = list((registry._read().get("updates") or [])[-5:])
    if not updates:
        return "📜 <b>سجل التحديثات</b>\nلا توجد تحديثات محفوظة بعد لهذا المشروع."
    lines = ["📜 <b>سجل التحديثات</b>"]
    for item in reversed(updates):
        lines.append(
            f"• <code>{html_escape(str(item.get('at') or ''))}</code> — <code>{html_escape(str(item.get('status') or ''))}</code>"
            f" — checkpoint=<code>{html_escape(str(item.get('checkpoint') or '-'))}</code>"
        )
    return "\n".join(lines)


def render_project_file_report_text(project_key: str) -> str:
    registry = ProjectRegistry(project_key)
    updates = registry._read().get("updates") or []
    latest = updates[-1] if updates else {}
    checkpoint_id = str(latest.get("checkpoint") or "")
    record = registry.load_checkpoint_record(checkpoint_id) if checkpoint_id else None
    if not record:
        return "📁 <b>تقرير الملفات</b>\nلا يوجد checkpoint record صالح لعرض تفاصيل الملفات بعد."
    summary = record.get("summary") or {}
    files = list(record.get("files") or [])[:5]
    deleted = list(record.get("deleted_files") or [])[:5]
    lines = [
        "📁 <b>تقرير الملفات</b>",
        f"• checkpoint: <code>{html_escape(checkpoint_id)}</code>",
        f"• Added/Modified/Deleted/Unchanged = <b>{summary.get('added', 0)}/{summary.get('modified', 0)}/{summary.get('deleted', 0)}/{summary.get('unchanged', 0)}</b>",
    ]
    for item in files:
        lines.append(f"• {html_escape(str(item.get('classification') or 'FILE'))}: <code>{html_escape(str(item.get('path') or ''))}</code>")
    for item in deleted:
        lines.append(f"• DELETED: <code>{html_escape(str(item.get('path') or ''))}</code>")
    return "\n".join(lines)


def render_project_github_status_text(project_key: str) -> str:
    registry = ProjectRegistry(project_key)
    settings = registry.get_project_settings().get("github", {})
    jobs = registry.list_upload_jobs()
    if settings.get("configured"):
        mode = "مفعل" if settings.get("enabled") else "معطل"
        branch = settings.get("branch") or settings.get("detected_default_branch") or "auto-default"
        repo = settings.get("repository") or "غير معروف"
    else:
        mode = "غير مفعّل"
        branch = "—"
        repo = "—"
    queued = [job for job in jobs if str(job.get("state") or "") != "synced"]
    synced = [job for job in jobs if str(job.get("state") or "") == "synced"]
    last_states = ", ".join(str(job.get("state") or "") for job in jobs[:4]) or "لا يوجد"
    if queued:
        status_note = "• تم إنشاء job أو أكثر للرفع، لكن لم يتم تأكيد اكتمال الرفع بعد. الحالات <code>pending/uploading/retrying</code> تعني جدولة أو تنفيذ جارٍ فقط."
    elif synced:
        status_note = "• آخر jobs المسجلة لهذه اللقطة وصلت إلى حالة <code>synced</code>."
    else:
        status_note = "• لا توجد jobs GitHub محفوظة بعد لهذا المشروع."
    return (
        "🔗 <b>حالة GitHub</b>\n"
        f"• النمط: <code>{html_escape(mode)}</code>\n"
        f"• المستودع: <code>{html_escape(str(repo))}</code>\n"
        f"• الفرع: <code>{html_escape(str(branch))}</code>\n"
        f"• jobs المفتوحة: <b>{len(queued)}</b> من أصل <b>{len(jobs)}</b>\n"
        f"• آخر حالات queue: <code>{html_escape(last_states)}</code>\n"
        f"{status_note}"
    )


def render_project_settings_text(project_key: str) -> str:
    identity = get_project_identity_record(project_key) or {}
    registry = ProjectRegistry(project_key)
    settings = registry.get_project_settings()
    github = settings.get("github", {})
    repo = github.get("repository") or "—"
    branch = github.get("branch") or github.get("detected_default_branch") or "—"
    branch_mode = github.get("branch_mode") or "disabled"
    github_mode = "مفعل" if github.get("enabled") else ("معطل" if github.get("configured") else "غير مضبوط")
    token_status = "موجود" if github.get("token_present") else "غير محفوظ"
    check_status = github.get("last_repo_check_status") or "—"
    check_at = github.get("last_repo_check_at") or "—"
    return (
        "⚙️ <b>إعدادات المشروع</b>\n"
        f"• الاسم: <b>{html_escape(str(identity.get('project_name') or project_key))}</b>\n"
        f"• المفتاح: <code>{html_escape(project_key)}</code>\n"
        f"• الموديل: <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n"
        f"• برومبت الاستئناف: <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>\n"
        f"• GitHub: <code>{html_escape(github_mode)}</code>\n"
        f"• المستودع: <code>{html_escape(str(repo))}</code>\n"
        f"• الفرع: <code>{html_escape(str(branch))}</code>\n"
        f"• branch mode: <code>{html_escape(str(branch_mode))}</code>\n"
        f"• token للمشروع: <code>{html_escape(token_status)}</code>\n"
        f"• آخر repo check: <code>{html_escape(str(check_status))}</code>\n"
        f"• وقت آخر check: <code>{html_escape(str(check_at))}</code>"
    )


def render_project_resume_summary_text(project_key: str, *, target_url: str = "", target_pid: str = "") -> str:
    identity = get_project_identity_record(project_key) or {}
    registry = ProjectRegistry(project_key)
    settings = registry.get_project_settings()
    github = settings.get("github", {})
    repo = github.get("repository") or "—"
    branch = github.get("branch") or github.get("detected_default_branch") or "—"
    github_mode = "مفعل" if github.get("enabled") else ("معطل" if github.get("configured") else "غير مضبوط")
    public_resume_prompt = settings.get("continuation", {}).get("prompt") or DEFAULT_PROJECT_RESUME_PROMPT
    pid_value = extract_project_id(target_url) if target_url else ""
    if not pid_value:
        pid_value = str(target_pid or identity.get("latest_genspark_pid") or identity.get("root_genspark_pid") or "")
    resume_line = f"\n• رابط الاستئناف: {html_escape(target_url)}" if target_url else ""
    pid_line = f"\n• Project ID الحالي: <code>{html_escape(pid_value)}</code>" if pid_value else ""
    next_step = "يمكنك المتابعة الآن مباشرة أو تعديل الإعدادات أولاً بدون إعادة Wizard كاملة."
    if not target_url:
        next_step = "هذا المشروع لا يملك رابط استئناف محفوظاً بعد؛ يمكنك تعديل الإعدادات أو إرسال أول prompt لبدءه بنفس المفتاح."
    return (
        "🔄 <b>ملخص الاستئناف</b>\n"
        f"• الاسم: <b>{html_escape(str(identity.get('project_name') or project_key))}</b>\n"
        f"• المفتاح: <code>{html_escape(project_key)}</code>\n"
        f"• الموديل: <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n"
        f"• برومبت الاستئناف: <code>{html_escape(public_resume_prompt)}</code>\n"
        f"• GitHub: <code>{html_escape(github_mode)}</code>\n"
        f"• المستودع: <code>{html_escape(str(repo))}</code>\n"
        f"• الفرع: <code>{html_escape(str(branch))}</code>{pid_line}{resume_line}\n\n"
        f"{next_step}"
    )


def build_project_settings_keyboard(project_key: str) -> dict:
    github = ProjectRegistry(project_key).get_project_settings().get("github", {})
    toggle_label = "🚫 تعطيل GitHub" if github.get("enabled") else "✅ تفعيل GitHub"
    return make_inline_keyboard([
        [{"text": "🧠 تعديل الموديل", "callback_data": f"pset:model:{project_key}"}, {"text": "✍️ تعديل برومبت الاستئناف", "callback_data": f"pset:resume:{project_key}"}],
        [{"text": "🔗 تعديل المستودع", "callback_data": f"pset:repo:{project_key}"}, {"text": "🌿 تعديل الـbranch", "callback_data": f"pset:branch:{project_key}"}],
        [{"text": "🔑 تحديث GitHub token", "callback_data": f"pset:token:{project_key}"}, {"text": toggle_label, "callback_data": f"pset:toggle:{project_key}"}],
        [{"text": "⭐ رجوع لتفاصيل المشروع", "callback_data": f"pview:{project_key}"}, {"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def build_project_resume_summary_keyboard(project_key: str, *, target_url: str = "", target_pid: str = "") -> dict:
    rows = [
        [{"text": "▶️ كمل الآن", "callback_data": "cmd:resume_continue", "style": "success"}, {"text": "⚙️ عدّل الإعدادات", "callback_data": "cmd:resume_settings"}],
    ]
    if target_url:
        rows.append([{"text": "🌐 فتح المشروع", "url": target_url}])
    if target_pid:
        rows.append([{"text": "🌳 نقاط الاستئناف", "callback_data": f"tree:{target_pid}"}])
    rows.append([{"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"}, {"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}])
    return make_inline_keyboard(rows)


def build_unbound_resume_keyboard() -> dict:
    return make_inline_keyboard([
        [{"text": "📌 اربطه كمشروع محفوظ", "callback_data": "cmd:resume_bind_saved"}],
        [{"text": "⚡ استئناف سريع بدون حفظ", "callback_data": "cmd:resume_quick_continue"}],
        [{"text": "📋 نسخ إعدادات من مشروع آخر", "callback_data": "cmd:resume_copy_settings"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def build_copy_settings_source_keyboard(chat_id: int, *, limit: int = 8) -> dict:
    """[P19] قائمة المشاريع المحفوظة كأزرار لاختيار المشروع المصدر لنسخ إعداداته."""
    rows = []
    for record in list_known_projects(chat_id=chat_id, limit=limit):
        label = str(record.get("project_name") or record.get("project_key") or "مشروع")[:32]
        rows.append([{"text": f"📋 {label}", "callback_data": f"cpysrc:{record['project_key']}"}])
    rows.append([
        {"text": "⬅️ رجوع", "callback_data": "cmd:resume_copy_back"},
        {"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"},
    ])
    return make_inline_keyboard(rows)


def build_bound_project_github_choice_keyboard() -> dict:
    return make_inline_keyboard([
        [{"text": "🔗 ربط GitHub لهذا المشروع الخارجي", "callback_data": "cmd:bound_proj_github_yes"}],
        [{"text": "➡️ المتابعة بدون GitHub", "callback_data": "cmd:bound_proj_github_no"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def build_bound_project_resume_prompt_keyboard() -> dict:
    return make_inline_keyboard([
        [{"text": "✅ استخدم «تابع» الافتراضية", "callback_data": "cmd:bound_proj_resume_default"}],
        [{"text": "✍️ أدخل برومبت استئناف مخصص", "callback_data": "cmd:bound_proj_resume_custom"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def present_resume_summary(chat_id: int, *, project_key: str, target_url: str = "", target_pid: str = "") -> bool:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        return False
    identity = get_project_identity_record(key) or {}
    project_name = str(identity.get("project_name") or key)
    project_model = get_project_selected_model(key)
    pid_value = extract_project_id(target_url) if target_url else ""
    if not pid_value:
        pid_value = str(target_pid or identity.get("latest_genspark_pid") or identity.get("root_genspark_pid") or "")
    set_user_state(chat_id, {
        "action": "AWAITING_PROJECT_RESUME_DECISION",
        "project_key": key,
        "project_name": project_name,
        "project_model": project_model,
        "url": target_url,
        "pid": pid_value,
    })
    send_telegram_message(
        chat_id,
        render_project_resume_summary_text(key, target_url=target_url, target_pid=pid_value),
        reply_markup=build_project_resume_summary_keyboard(key, target_url=target_url, target_pid=pid_value),
    )
    return True


def send_project_settings_panel(chat_id: int, project_key: str, prefix: str = "") -> None:
    body = render_project_settings_text(project_key)
    message = f"{prefix}\n\n{body}" if prefix else body
    send_telegram_message(chat_id, message, reply_markup=build_project_settings_keyboard(project_key))


def run_project_upload_control(project_key: str, action: str) -> str:
    registry = ProjectRegistry(project_key)
    dest = registry._github_destination()
    if not dest:
        return "⚠️ <b>GitHub غير مفعّل لهذا المشروع حالياً.</b>\nفعّل إعداد GitHub أولاً من Wizard المشروع الجديد أو استخدم الإعداد المحفوظ."
    if action == "sync":
        result = registry.process_next_upload_job()
        state = str(result.get("state") or "no-due-job")
        return (
            "📤 <b>مزامنة الآن</b>\n"
            f"• النتيجة: <code>{html_escape(state)}</code>\n"
            f"• job: <code>{html_escape(str(result.get('job_id') or '-'))}</code>"
        )
    if action == "retry":
        recovered = registry.recover_upload_queue_after_restart()
        result = registry.process_next_upload_job()
        state = str(result.get("state") or "no-due-job")
        return (
            "🔁 <b>إعادة محاولة الرفع</b>\n"
            f"• jobs المعاد تجهيزها: <b>{len(recovered)}</b>\n"
            f"• النتيجة الحالية: <code>{html_escape(state)}</code>\n"
            f"• job: <code>{html_escape(str(result.get('job_id') or '-'))}</code>"
        )
    if action == "pause":
        return "⏸ <b>إيقاف مؤقت</b>\nلا يوجد worker دائم مستقل لكل مشروع حالياً داخل 01.15، لذلك هذا الزر يوضّح فقط أن الإيقاف المؤقت التشغيلي سيأتي لاحقاً دون الادعاء بتنفيذ غير موجود."
    if action == "cancel":
        return "❌ <b>إلغاء</b>\nلا يوجد عقد إلغاء آمن لمهمة جارية داخل 01.15 الحالية، لذلك لا يتم قتل أي process من هذا الزر. استخدمه لاحقاً بعد إغلاق TSK مخصصة لذلك."
    return "ℹ️ تحكم غير معروف."


def build_current_project_keyboard(project_key: str) -> dict:
    snap = get_project_dashboard_snapshot(project_key)
    rows = []
    if snap.get("resume_url"):
        rows.append([{"text": "🌐 فتح المشروع", "url": snap["resume_url"]}])
    rows.append([
        {"text": "🔄 استئناف هذا المشروع", "callback_data": f"proj:{project_key}"},
        {"text": "⚙️ إعدادات المشروع", "callback_data": f"pset:view:{project_key}"},
    ])
    rows.append([
        {"text": "🗂 آخر 3 checkpoints", "callback_data": f"pctl:checkpoints:{project_key}"},
        {"text": "📦 آخر Archive", "callback_data": f"pctl:archive:{project_key}"},
    ])
    rows.append([
        {"text": "📁 تقرير الملفات", "callback_data": f"pctl:files:{project_key}"},
        {"text": "📜 سجل التحديثات", "callback_data": f"pctl:history:{project_key}"},
    ])
    rows.append([
        {"text": "🔗 حالة GitHub", "callback_data": f"pctl:gh:{project_key}"},
        {"text": "📤 مزامنة الآن", "callback_data": f"pctl:sync:{project_key}"},
    ])
    rows.append([
        {"text": "🔁 إعادة محاولة الرفع", "callback_data": f"pctl:retry:{project_key}"},
        {"text": "⏸ إيقاف مؤقت", "callback_data": f"pctl:pause:{project_key}"},
        {"text": "❌ إلغاء", "callback_data": f"pctl:cancel:{project_key}", "style": "danger"},
    ])
    if snap.get("resume_pid"):
        rows.append([{"text": "🌳 نقاط الاستئناف", "callback_data": f"tree:{snap['resume_pid']}"}])
    # 🗑️ [P26] صف مستقل لحذف المشروع — إضافة وليس استبدالاً لزر إلغاء البناء (P25)
    rows.append([{"text": "🗑️ حذف المشروع", "callback_data": f"pdel_prompt:{project_key}", "style": "danger"}])
    rows.append([{"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"}, {"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}])
    return make_inline_keyboard(rows)


def build_project_delete_confirm_keyboard(project_key: str) -> dict:
    """🗑️ [P26] كيبورد تأكيد الحذف بخطوتي أمان — نعم أحمر / تراجع أخضر"""
    return make_inline_keyboard([
        [{"text": "🚨 نعم، احذف نهائياً", "callback_data": f"pdel_exec:{project_key}", "style": "danger"}],
        [{"text": "↩️ لا، إلغاء ورجوع", "callback_data": f"pdel_abort:{project_key}", "style": "success"}],
    ])


def build_project_deleted_keyboard() -> dict:
    """🗑️ [P26] كيبورد شاشة نجاح الحذف — مشاريعي + مشروع جديد"""
    return make_inline_keyboard([
        [
            {"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"},
            {"text": "🚀 مشروع جديد", "callback_data": "cmd:new_proj", "style": "primary"},
        ],
    ])


def render_project_delete_confirm_text(project_key: str) -> str:
    """🗑️ [P26] نص التحذير قبل الحذف النهائي — بالاسم والمفتاح"""
    identity = get_project_identity_record(project_key) or {}
    project_name = str(identity.get("project_name") or project_key)
    return (
        "🗑️ <b>تأكيد حذف المشروع نهائياً</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 <b>الاسم:</b> {html_escape(project_name)}\n"
        f"🔑 <b>المفتاح:</b> <code>{html_escape(project_key)}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ سيتم حذف مجلد المشروع كاملاً (manifest + checkpoints)\n"
        "وإزالته من الفهرس المركزي وشجرة نقاط الاستئناف.\n"
        "🚫 <b>هذا الإجراء لا يمكن التراجع عنه بعد التأكيد!</b>"
    )


def build_dashboard_keyboard(chat_id: int) -> dict:
    rows = [
        [{"text": "🚀 مشروع جديد", "callback_data": "cmd:new_proj", "style": "primary"}, {"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"}],
        [{"text": "🔄 استئناف مشروع", "callback_data": "cmd:cont_proj"}, {"text": "⭐ المشروع الحالي", "callback_data": "cmd:current_project"}],
        # 🔐 [P32] زر الحسابات القديم (فحص الرصيد العشوائي) استُبدل بشاشة الباسورد الهجينة
        [{"text": "🌳 نقاط الاستئناف", "callback_data": "cmd:list_tree"}, {"text": "🔐 استخراج باسورد الحساب", "callback_data": "cmd:account_pwd_lookup"}],
    ]
    for record in list_known_projects(chat_id=chat_id, limit=3):
        label = str(record.get("project_name") or record.get("project_key") or "مشروع")[:24]
        rows.append([
            {"text": f"📌 {label}", "callback_data": f"proj:{record['project_key']}"},
            {"text": "⭐ التفاصيل", "callback_data": f"pview:{record['project_key']}"},
        ])
    return make_inline_keyboard(rows)


# ══════════════════════════════════════════════════════════════
# 📄 [P27] تصفح المشاريع بنظام الصفحات (Projects List Pagination)
# لوحة التحكم الرئيسية تبقى معاينة سريعة (أحدث 3) — وزر «📁 مشاريعي»
# يفتح شاشة تصفح مستقلة بكل المشاريع مقسمة صفحات مع أزرار تقليب.
# ══════════════════════════════════════════════════════════════
PROJECTS_PER_PAGE = 20  # 📄 [P27] عدد المشاريع في الصفحة — الثابت المركزي الوحيد (تغييره لاحقاً = سطر واحد)


def compute_projects_page_bounds(total: int, page) -> tuple[int, int, int]:
    """📄 [P27] حساب حدود الصفحة بأمان تام (Out-of-Bounds Safe — صفر Crash).
    يعيد (safe_page, total_pages, start_index) — ترقيم الصفحات يبدأ من 1.
    أي قيمة page غير صالحة (نص/سالب/أكبر من الأخيرة) تُقَصّ لأقرب صفحة صالحة."""
    per_page = max(1, int(PROJECTS_PER_PAGE))
    total = max(0, int(total))
    total_pages = max(1, (total + per_page - 1) // per_page)
    try:
        page_num = int(page)
    except (TypeError, ValueError):
        page_num = 1
    safe_page = min(max(1, page_num), total_pages)
    start_index = (safe_page - 1) * per_page
    return safe_page, total_pages, start_index


def render_projects_page_text(chat_id: int, page=1) -> str:
    """📄 [P27] نص شاشة تصفح المشاريع — عداد إجمالي + موضع الصفحة الحالي."""
    total = len(list_known_projects(chat_id=chat_id))
    if total == 0:
        return (
            "📁 <b>مشاريعي</b>\n"
            "لا توجد مشاريع محفوظة بعد لهذه المحادثة.\n"
            "ابدأ الآن بزر <b>🚀 مشروع جديد</b>."
        )
    safe_page, total_pages, start_index = compute_projects_page_bounds(total, page)
    end_index = min(start_index + PROJECTS_PER_PAGE, total)
    return (
        "📁 <b>مشاريعي</b>\n"
        f"إجمالي المشاريع: <b>{total}</b> — صفحة <b>{safe_page}</b> من <b>{total_pages}</b>\n"
        f"يعرض المشاريع <b>{start_index + 1}–{end_index}</b> (الأحدث أولاً).\n"
        "اختر 📌 للاستئناف المباشر أو ⭐ لعرض التفاصيل:"
    )


def build_projects_page_keyboard(chat_id: int, page=1) -> dict:
    """📄 [P27] كيبورد صفحة المشاريع: صفوف المشاريع (نفس عقود proj:/pview: القائمة —
    صفر تغيير على تدفق الاختيار) + صف تنقل [⬅️ السابقة][📄 N/X][التالية ➡️]
    (أزرار الحواف تُحذف تلقائياً) + صف [🚀 مشروع جديد][🏠 رجوع للوحة التحكم]."""
    projects = list_known_projects(chat_id=chat_id)
    total = len(projects)
    rows: list[list[dict]] = []
    if total:
        safe_page, total_pages, start_index = compute_projects_page_bounds(total, page)
        for record in projects[start_index:start_index + PROJECTS_PER_PAGE]:
            label = str(record.get("project_name") or record.get("project_key") or "مشروع")[:24]
            rows.append([
                {"text": f"📌 {label}", "callback_data": f"proj:{record['project_key']}"},
                {"text": "⭐ التفاصيل", "callback_data": f"pview:{record['project_key']}"},
            ])
        if total_pages > 1:
            nav_row = []
            if safe_page > 1:
                nav_row.append({"text": "⬅️ السابقة", "callback_data": f"plist:page:{safe_page - 1}"})
            nav_row.append({"text": f"📄 {safe_page} / {total_pages}", "callback_data": "plist:noop"})
            if safe_page < total_pages:
                nav_row.append({"text": "التالية ➡️", "callback_data": f"plist:page:{safe_page + 1}"})
            rows.append(nav_row)
    rows.append([
        {"text": "🚀 مشروع جديد", "callback_data": "cmd:new_proj", "style": "primary"},
        {"text": "🏠 رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"},
    ])
    return make_inline_keyboard(rows)


# ══════════════════════════════════════════════════════════════
# 🔐 [P32] استخراج باسورد الحساب — بحث هجين (يدوي + تصفح بالصفحات)
# ══════════════════════════════════════════════════════════════
# العقد المعماري (مستخلص من الفحص الميداني T0–T7):
#  • مصدر البيانات الوحيد: read_accounts_safe() — نفس عقد P23 (محلي ثم الأب).
#    قراءة فقط (Read-Only) بلا أي كتابة على القرص ← صفر تأثير على P29/P30.
#  • callback_data بالفهرس (acc_view:{index}) وليس بالإيميل: حد تيليجرام 64 بايت
#    والإيميلات الطويلة تكسره ← الفهرس يضمن ثباتاً وأماناً مطلقاً.
#  • الترتيب مثبّت (sorted بالإيميل) حتى يبقى الفهرس مستقراً بين الصفحات والضغطات.
ACCOUNTS_PER_PAGE = 5  # 📄 [P32] عدد الحسابات في الصفحة — الثابت المركزي الوحيد
AWAITING_ACCOUNT_PASSWORD_LOOKUP = "AWAITING_ACCOUNT_PASSWORD_LOOKUP"


def list_lookup_accounts(json_path: str | None = None) -> list[dict]:
    """🔐 [P32] قائمة الحسابات القابلة للاستعلام بترتيب ثابت (Deterministic Order).

    الترتيب الأبجدي بالإيميل يضمن أن الفهرس المستخدم في acc_view:{index}
    يشير لنفس الحساب دائماً — شرط سلامة التصفح بالصفحات.
    قراءة خالصة: لا تكتب ولا تُعدّل أي حساب (بخلاف get_random_email_...).
    """
    accounts = read_accounts_safe(json_path)
    valid = [
        acc for acc in accounts
        if isinstance(acc, dict) and str(acc.get("email") or "").strip()
    ]
    return sorted(valid, key=lambda a: str(a.get("email") or "").strip().lower())


def compute_accounts_page_bounds(total: int, page) -> tuple[int, int, int]:
    """📄 [P32] حدود صفحة الحسابات بأمان تام (Out-of-Bounds Safe — صفر Crash).
    يعيد (safe_page, total_pages, start_index) — الترقيم يبدأ من 1.
    أي page غير صالحة (نص/سالب/أكبر من الأخيرة) تُقَصّ لأقرب صفحة صالحة."""
    per_page = max(1, int(ACCOUNTS_PER_PAGE))
    total = max(0, int(total))
    total_pages = max(1, (total + per_page - 1) // per_page)
    try:
        page_num = int(page)
    except (TypeError, ValueError):
        page_num = 1
    safe_page = min(max(1, page_num), total_pages)
    start_index = (safe_page - 1) * per_page
    return safe_page, total_pages, start_index


def find_account_by_email(email: str, json_path: str | None = None) -> dict | None:
    """🔐 [P32] بحث يدوي عن حساب بالإيميل — تطبيع كامل (strip + lower).
    يعيد None عند عدم الوجود أو المدخل الفارغ (لا استثناءات أبداً)."""
    needle = str(email or "").strip().lower()
    if not needle:
        return None
    for acc in list_lookup_accounts(json_path):
        if str(acc.get("email") or "").strip().lower() == needle:
            return acc
    return None


def describe_account_state(acc: dict) -> str:
    """🔐 [P32] وصف عربي مقروء لحالة الحساب مبني على عقد is_account_ready القائم."""
    if not isinstance(acc, dict):
        return "غير معروفة"
    status = str(acc.get("status") or "active").lower().strip()
    if status in ("banned", "blocked"):
        return "محظور نهائياً (BANNED)"
    if is_account_ready(acc):
        return "نشط (ACTIVE)"
    if status == "cooldown":
        return "قيد التبريد (COOLDOWN)"
    if status in ("auth_failed", "disabled"):
        return f"معطّل مؤقتاً ({status.upper()})"
    return "غير جاهز (INACTIVE)"


def render_account_lookup_text(page=1, json_path: str | None = None) -> str:
    """🔐 [P32] نص شاشة الاستخراج الهجينة: تعليمة الكتابة اليدوية + موضع الصفحة."""
    accounts = list_lookup_accounts(json_path)
    total = len(accounts)
    if total == 0:
        return (
            "🔐 <b>استخراج باسورد وبيانات الحساب</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "❌ لا توجد حسابات مسجلة في قاعدة الحسابات حالياً."
        )
    safe_page, total_pages, start_index = compute_accounts_page_bounds(total, page)
    end_index = min(start_index + ACCOUNTS_PER_PAGE, total)
    return (
        "🔐 <b>استخراج باسورد وبيانات الحساب</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✍️ اكتب الإيميل المطلوب في الشات مباشرة،\n"
        "أو اختر الإيميل بضغطة زر من القائمة:\n"
        f"📄 <b>قائمة الحسابات</b> (صفحة <b>{safe_page}</b> من <b>{total_pages}</b>)\n"
        f"يعرض الحسابات <b>{start_index + 1}–{end_index}</b> من إجمالي <b>{total}</b>."
    )


def build_account_lookup_keyboard(page=1, json_path: str | None = None) -> dict:
    """🔐 [P32] كيبورد الشاشة الهجينة: زر لكل حساب (acc_view:{index}) +
    صف تنقل [⬅️ السابق][📄 N/X][التالي ➡️] (أزرار الحواف تُحذف تلقائياً) +
    زر الإلغاء الحتمي. الفهرس مطلق داخل القائمة المرتبة — لا يتأثر بالصفحة."""
    accounts = list_lookup_accounts(json_path)
    total = len(accounts)
    rows: list[list[dict]] = []
    if total:
        safe_page, total_pages, start_index = compute_accounts_page_bounds(total, page)
        for offset, acc in enumerate(accounts[start_index:start_index + ACCOUNTS_PER_PAGE]):
            email = str(acc.get("email") or "").strip()
            rows.append([{
                "text": f"📧 {email[:40]}",
                "callback_data": f"acc_view:{start_index + offset}",
            }])
        if total_pages > 1:
            nav_row = []
            if safe_page > 1:
                nav_row.append({"text": "⬅️ السابق", "callback_data": f"acc_page:{safe_page - 1}"})
            nav_row.append({"text": f"📄 {safe_page} / {total_pages}", "callback_data": "acc_page:noop"})
            if safe_page < total_pages:
                nav_row.append({"text": "التالي ➡️", "callback_data": f"acc_page:{safe_page + 1}"})
            rows.append(nav_row)
    rows.append([{"text": "↩️ إلغاء ورجوع للوحة التحكم", "callback_data": "acc_cancel"}])
    return make_inline_keyboard(rows)


def render_account_password_card(acc: dict) -> str:
    """🔐 [P32] كارت بيانات الحساب — الإيميل والباسورد بنمط <code> للنسخ بلمسة.
    حساب بلا باسورد يُبلَّغ صراحةً بدلاً من عرض قيمة فارغة مضللة."""
    email = str(acc.get("email") or "").strip()
    password = str(acc.get("password") or "").strip()
    password_line = (
        f"🔑 <b>الباسورد (المس للنسخ):</b> <code>{html_escape(password)}</code>"
        if password else
        "🔑 <b>الباسورد:</b> ⚠️ لا يوجد باسورد مسجل لهذا الحساب"
    )
    return (
        "✅ <b>بيانات الحساب المطلوبة:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📧 <b>الإيميل:</b> <code>{html_escape(email)}</code>\n"
        f"{password_line}\n"
        f"📊 <b>الحالة:</b> {html_escape(describe_account_state(acc))}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )


def build_account_password_card_keyboard() -> dict:
    """🔐 [P32] كيبورد كارت النتيجة: [🔄 فحص حساب آخر][⬅️ رجوع للوحة التحكم]."""
    return make_inline_keyboard([[
        {"text": "🔄 فحص حساب آخر", "callback_data": "cmd:account_pwd_lookup"},
        {"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"},
    ]])


def build_account_lookup_retry_keyboard() -> dict:
    """🔐 [P32] كيبورد حالة الإيميل غير الموجود: إعادة المحاولة أو الرجوع."""
    return make_inline_keyboard([[
        {"text": "🔄 حاول مرة أخرى", "callback_data": "cmd:account_pwd_lookup"},
        {"text": "↩️ إلغاء ورجوع للوحة التحكم", "callback_data": "acc_cancel"},
    ]])


def build_project_model_keyboard(*, back_callback: str = "cmd:show_dashboard", back_label: str = "⬅️ رجوع للوحة التحكم") -> dict:
    rows = []
    for model_name in AVAILABLE_MODELS:
        rows.append([{"text": f"🧠 {model_name}", "callback_data": f"cmd:new_proj_model:{model_name}"}])
    rows.append([{"text": back_label, "callback_data": back_callback}])
    return make_inline_keyboard(rows)


def build_new_project_model_keyboard(*, back_callback: str = "cmd:show_dashboard", back_label: str = "⬅️ رجوع للوحة التحكم") -> dict:
    return build_project_model_keyboard(back_callback=back_callback, back_label=back_label)


def build_new_project_github_choice_keyboard() -> dict:
    return make_inline_keyboard([
        [{"text": "🔗 ربط GitHub لهذا المشروع", "callback_data": "cmd:new_proj_github_yes"}],
        [{"text": "➡️ المتابعة بدون GitHub", "callback_data": "cmd:new_proj_github_no"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def format_github_repo_inspection_summary(repository: str, default_branch: str, branches: list[str]) -> str:
    lines = [
        f"✅ <b>تم فحص المستودع:</b> <code>{html_escape(repository)}</code>",
        f"<b>Default branch:</b> <code>{html_escape(default_branch or 'غير معروف')}</code>",
        "",
        "<b>🌿 Branches المكتشفة (اضغط للنسخ):</b>",
    ]
    if branches:
        for b in branches[:8]:
            tag = " 🌟 (الافتراضي)" if b == default_branch else ""
            lines.append(f"  • <code>{html_escape(b)}</code>{tag}")
    else:
        lines.append("  • <code>لا توجد فروع مكتشفة</code>")
    lines.append("\nاختر الفرع مباشرة من الأزرار بالأسفل، أو أدخله يدوياً:")
    return "\n".join(lines)


def build_project_branch_choice_keyboard(
    default_callback: str,
    manual_callback: str,
    *,
    branches: list[str] | None = None,
    branch_prefix: str = "",
    default_branch: str = "",
    back_callback: str = "",
    back_label: str = "⬅️ رجوع",
    disable_callback: str = "",
    disable_label: str = "➡️ كمّل بدون GitHub",
) -> dict:
    rows = []
    if branches and branch_prefix:
        for b in branches[:6]:
            tag = " 🌟 (افتراضي)" if b == default_branch else ""
            rows.append([{"text": f"🌿 {b}{tag}", "callback_data": f"{branch_prefix}{b}"}])
    else:
        rows.append([{"text": "✅ استخدم الـ default branch المكتشف", "callback_data": default_callback}])
    rows.append([{"text": "✍️ أريد تحديد branch يدويًا", "callback_data": manual_callback}])
    if disable_callback:
        rows.append([{"text": disable_label, "callback_data": disable_callback}])
    if back_callback:
        rows.append([{"text": back_label, "callback_data": back_callback}])
    return make_inline_keyboard(rows)


def build_new_project_branch_choice_keyboard(branches: list[str] | None = None, default_branch: str = "") -> dict:
    return build_project_branch_choice_keyboard(
        "cmd:new_proj_branch_default",
        "cmd:new_proj_branch_manual",
        branches=branches,
        branch_prefix="cmd:new_proj_branch_pick:",
        default_branch=default_branch,
        back_callback="cmd:show_dashboard",
        back_label="⬅️ رجوع للوحة التحكم",
        disable_callback="cmd:new_proj_github_disable",
    )


def build_existing_project_branch_choice_keyboard(project_key: str, branches: list[str] | None = None, default_branch: str = "") -> dict:
    return build_project_branch_choice_keyboard(
        f"pset:branch_default:{project_key}",
        f"pset:branch_manual:{project_key}",
        branches=branches,
        branch_prefix=f"pset:branch_pick:{project_key}:",
        default_branch=default_branch,
        back_callback=f"pset:view:{project_key}",
        back_label="⬅️ رجوع لإعدادات المشروع",
    )


def build_bound_project_branch_choice_keyboard(branches: list[str] | None = None, default_branch: str = "") -> dict:
    return build_project_branch_choice_keyboard(
        "cmd:bound_proj_branch_default",
        "cmd:bound_proj_branch_manual",
        branches=branches,
        branch_prefix="cmd:bound_proj_branch_pick:",
        default_branch=default_branch,
        back_callback="cmd:show_dashboard",
        back_label="⬅️ رجوع للوحة التحكم",
        disable_callback="cmd:bound_proj_github_disable",
    )


def build_new_project_resume_prompt_keyboard() -> dict:
    return make_inline_keyboard([
        [{"text": "✅ استخدم «تابع» الافتراضية", "callback_data": "cmd:new_proj_resume_default"}],
        [{"text": "✍️ أدخل برومبت استئناف مخصص", "callback_data": "cmd:new_proj_resume_custom"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def get_project_selected_model(project_key: str | None) -> str:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        return DEFAULT_PROJECT_MODEL
    return ProjectRegistry(key).get_project_settings().get("model") or DEFAULT_PROJECT_MODEL


def finalize_new_project_setup(
    project_key: str,
    project_name: str,
    *,
    model: str,
    resume_prompt: str,
    chat_id: int,
    github_enabled: bool,
    repository: str = "",
    branch: str = "",
    branch_mode: str = "disabled",
    detected_default_branch: str = "",
    available_branches: list[str] | None = None,
    repo_check_status: str = "",
    token: str | None = None,
) -> dict:
    upsert_project_identity(project_key, project_name=project_name, chat_id=chat_id, status="DRAFT")
    registry = ProjectRegistry(project_key)
    registry.set_project_model(model)
    registry.set_project_resume_prompt(resume_prompt)
    configure_project_github_settings(
        project_key,
        enabled=github_enabled,
        repository=repository,
        branch=branch,
        branch_mode=branch_mode,
        detected_default_branch=detected_default_branch,
        available_branches=available_branches,
        repo_check_status=repo_check_status,
        token=token,
    )
    return registry.get_project_settings()


def finalize_new_project_from_state(state: dict, chat_id: int, resume_prompt: str | None = None) -> tuple[dict, dict]:
    project_key = str(state.get("project_key") or "")
    project_name = str(state.get("project_name") or "")
    project_model = normalize_project_model(state.get("project_model"))
    github_enabled = bool(state.get("pending_github_enabled", False))
    repository = str(state.get("pending_github_repository") or "")
    token = str(state.get("pending_github_token") or "") if github_enabled else ""
    branch = str(state.get("pending_github_branch") or "")
    branch_mode = str(state.get("pending_github_branch_mode") or ("manual" if branch else ("auto_default" if github_enabled else "disabled")))
    detected_default_branch = str(state.get("pending_github_default_branch") or "")
    available_branches = list(state.get("pending_github_branches") or [])
    repo_check_status = str(state.get("pending_github_repo_check_status") or ("disabled" if not github_enabled else "checked"))
    effective_resume = normalize_project_resume_prompt(resume_prompt if resume_prompt is not None else state.get("pending_resume_prompt"))
    settings = finalize_new_project_setup(
        project_key,
        project_name,
        model=project_model,
        resume_prompt=effective_resume,
        chat_id=chat_id,
        github_enabled=github_enabled,
        repository=repository,
        branch=branch,
        branch_mode=branch_mode,
        detected_default_branch=detected_default_branch,
        available_branches=available_branches,
        repo_check_status=repo_check_status,
        token=token if github_enabled else None,
    )
    next_state = {
        "action": "AWAITING_NEW_PROMPT",
        "project_key": project_key,
        "project_name": project_name,
        "project_model": project_model,
    }
    return settings, next_state


PROJECT_SETTINGS_TOKEN_UNSET = object()


def update_existing_project_github_settings(
    project_key: str,
    *,
    enabled: bool | None = None,
    repository: str | None = None,
    branch: str | None = None,
    branch_mode: str | None = None,
    detected_default_branch: str | None = None,
    available_branches: list[str] | None = None,
    repo_check_status: str | None = None,
    token=PROJECT_SETTINGS_TOKEN_UNSET,
) -> dict:
    registry = ProjectRegistry(project_key)
    current = registry.get_project_settings().get("github", {})
    if token is not PROJECT_SETTINGS_TOKEN_UNSET:
        if str(token or "").strip():
            registry.set_project_github_token(str(token))
        else:
            registry.clear_project_github_token()
    repo_value = parse_github_repository_ref(repository) if repository is not None else str(current.get("repository") or "").strip()
    configured = bool(
        current.get("configured")
        or current.get("repository")
        or current.get("token_present")
        or repo_value
        or (token is not PROJECT_SETTINGS_TOKEN_UNSET and str(token or "").strip())
        or current.get("enabled")
        or enabled
    )
    patch = {"github": {"configured": configured}}
    if enabled is not None:
        patch["github"]["enabled"] = bool(enabled)
    if repository is not None:
        patch["github"]["repository"] = repo_value
    if branch is not None:
        patch["github"]["branch"] = str(branch or "").strip()
    if branch_mode is not None:
        patch["github"]["branch_mode"] = str(branch_mode or "").strip()
    if detected_default_branch is not None:
        patch["github"]["detected_default_branch"] = str(detected_default_branch or "").strip()
    if available_branches is not None:
        patch["github"]["available_branches"] = [str(x).strip() for x in (available_branches or []) if str(x).strip()][:20]
    if repo_check_status is not None:
        patch["github"]["last_repo_check_status"] = str(repo_check_status or "").strip()
    if len(patch["github"]) > 1 or token is not PROJECT_SETTINGS_TOKEN_UNSET:
        patch["github"]["last_repo_check_at"] = _utc()
    return registry.update_project_settings(patch)


def finalize_existing_project_github_from_state(
    state: dict,
    *,
    branch: str | None = None,
    branch_mode: str | None = None,
    repo_check_status: str | None = None,
) -> dict:
    token_value = state["pending_github_token"] if "pending_github_token" in state else PROJECT_SETTINGS_TOKEN_UNSET
    resolved_branch = str(branch if branch is not None else state.get("pending_github_branch") or "").strip()
    resolved_branch_mode = str(
        branch_mode
        if branch_mode is not None
        else state.get("pending_github_branch_mode") or ("manual" if resolved_branch else "auto_default")
    ).strip()
    return update_existing_project_github_settings(
        str(state.get("project_key") or ""),
        enabled=bool(state.get("pending_github_enabled", False)),
        repository=str(state.get("pending_github_repository") or ""),
        branch=resolved_branch,
        branch_mode=resolved_branch_mode,
        detected_default_branch=str(state.get("pending_github_default_branch") or ""),
        available_branches=list(state.get("pending_github_branches") or []),
        repo_check_status=str(repo_check_status if repo_check_status is not None else state.get("pending_github_repo_check_status") or ""),
        token=token_value,
    )


def present_external_resume_decision(chat_id: int, *, target_url: str, target_pid: str = "") -> bool:
    pid_value = str(target_pid or extract_project_id(target_url) or "")
    set_user_state(chat_id, {
        "action": "AWAITING_UNBOUND_RESUME_DECISION",
        "url": target_url,
        "pid": pid_value,
    })
    pid_line = f"\n<b>Project ID:</b> <code>{html_escape(pid_value)}</code>" if pid_value else ""
    url_line = f"\n<b>الرابط:</b> {html_escape(target_url)}" if target_url else ""
    send_telegram_message(
        chat_id,
        f"🔗 <b>تم اكتشاف مشروع غير محفوظ بعد.</b>{pid_line}{url_line}\nيمكنك استئنافه سريعاً بدون حفظ، أو ربطه أولاً كمشروع محفوظ بإعدادات كاملة.",
        reply_markup=build_unbound_resume_keyboard(),
    )
    return True


def finalize_bound_external_project_from_state(state: dict, chat_id: int, resume_prompt: str | None = None) -> tuple[dict, dict]:
    project_key = str(state.get("project_key") or "")
    project_name = str(state.get("project_name") or "")
    project_model = normalize_project_model(state.get("project_model"))
    github_enabled = bool(state.get("pending_github_enabled", False))
    repository = str(state.get("pending_github_repository") or "")
    token = str(state.get("pending_github_token") or "") if github_enabled else ""
    branch = str(state.get("pending_github_branch") or "")
    branch_mode = str(state.get("pending_github_branch_mode") or ("manual" if branch else ("auto_default" if github_enabled else "disabled")))
    detected_default_branch = str(state.get("pending_github_default_branch") or "")
    available_branches = list(state.get("pending_github_branches") or [])
    repo_check_status = str(state.get("pending_github_repo_check_status") or ("disabled" if not github_enabled else "checked"))
    effective_resume = normalize_project_resume_prompt(resume_prompt if resume_prompt is not None else state.get("pending_resume_prompt"))
    target_url = str(state.get("url") or "")
    target_pid = str(state.get("pid") or extract_project_id(target_url) or "")
    settings = finalize_new_project_setup(
        project_key,
        project_name,
        model=project_model,
        resume_prompt=effective_resume,
        chat_id=chat_id,
        github_enabled=github_enabled,
        repository=repository,
        branch=branch,
        branch_mode=branch_mode,
        detected_default_branch=detected_default_branch,
        available_branches=available_branches,
        repo_check_status=repo_check_status,
        token=token if github_enabled else None,
    )
    if target_pid:
        upsert_project_identity(
            project_key,
            root_pid=target_pid,
            latest_pid=target_pid,
            project_name=project_name,
            chat_id=chat_id,
            status="RESUME_REQUESTED",
        )
    next_state = {
        "action": "AWAITING_CONT_PROMPT",
        "url": target_url,
        "project_key": project_key,
        "project_name": project_name,
        "project_model": project_model,
        "pid": target_pid,
    }
    return settings, next_state


def generate_sequential_project_name(base_name: str, chat_id: int | None = None) -> str:
    """[P19] توليد اسم تسلسلي فريد: «الحج 1» ➔ «الحج 2» ➔ «الحج 3» تلقائياً.

    - يفصل الرقم الذيلي عن الجذر إن وُجد («الحج 1» ➔ جذر «الحج»).
    - يفحص كل المشاريع المعروفة ويحسب أعلى رقم مستخدم لنفس الجذر.
    - يعيد الجذر + (أعلى رقم + 1). لو الجذر غير مستخدم إطلاقاً يعيده كما هو.
    """
    clean = re.sub(r"\s+", " ", str(base_name or "")).strip()[:60] or "مشروع"
    match = re.match(r"^(.*?)\s*(\d+)$", clean)
    root = (match.group(1).strip() if match else clean) or clean
    existing_names = set()
    for record in list_known_projects(chat_id=chat_id):
        name = re.sub(r"\s+", " ", str(record.get("project_name") or "")).strip()
        if name:
            existing_names.add(name)
    if clean not in existing_names and not match:
        return clean
    max_index = 0
    root_used = False
    for name in existing_names:
        if name == root:
            root_used = True
            max_index = max(max_index, 1)
            continue
        m = re.match(r"^(.*?)\s*(\d+)$", name)
        if m and m.group(1).strip() == root:
            root_used = True
            try:
                max_index = max(max_index, int(m.group(2)))
            except Exception:
                pass
    if not root_used and clean not in existing_names:
        return clean
    return f"{root} {max_index + 1}"[:60]


def copy_project_settings_to_new_project(
    source_project_key: str,
    chat_id: int,
    *,
    target_url: str = "",
    target_pid: str = "",
) -> dict:
    """[P19] نسخ إعدادات مشروع محفوظ (GitHub + الموديل + برومبت الاستئناف) لمشروع جديد.

    - يقرأ إعدادات المصدر من ProjectRegistry (بما فيها token من المخزن السري للمشروع فقط
      بدون fallback على متغيرات البيئة حتى لا تتسرب أسرار عامة لمشروع خاص).
    - ينشئ مفتاحاً جديداً واسم تسلسلي فريد («الحج 1» ➔ «الحج 2»).
    - يعيد dict كامل: project_key/project_name/settings/source_name.
    """
    source_key = re.sub(r"[^A-Za-z0-9_-]", "_", str(source_project_key or ""))[:80]
    if not source_key:
        return {"ok": False, "reason": "مفتاح المشروع المصدر غير صالح"}
    source_identity = get_project_identity_record(source_key) or {}
    source_name = str(source_identity.get("project_name") or source_key)
    registry = ProjectRegistry(source_key)
    settings = registry.get_project_settings()
    github = settings.get("github", {}) if isinstance(settings.get("github"), dict) else {}
    source_token = registry.get_project_github_token(allow_env_fallback=False)
    github_enabled = bool(github.get("enabled"))
    new_project_key = f"prj_{uuid.uuid4().hex[:16]}"
    new_project_name = generate_sequential_project_name(source_name, chat_id=chat_id)
    new_settings = finalize_new_project_setup(
        new_project_key,
        new_project_name,
        model=normalize_project_model(settings.get("model")),
        resume_prompt=normalize_project_resume_prompt((settings.get("continuation") or {}).get("prompt")),
        chat_id=chat_id,
        github_enabled=github_enabled,
        repository=str(github.get("repository") or ""),
        branch=str(github.get("branch") or ""),
        branch_mode=str(github.get("branch_mode") or ("disabled" if not github_enabled else "auto_default")),
        detected_default_branch=str(github.get("detected_default_branch") or ""),
        available_branches=list(github.get("available_branches") or []),
        repo_check_status=str(github.get("last_repo_check_status") or ("disabled" if not github_enabled else "copied")),
        token=source_token if (github_enabled and source_token) else None,
    )
    pid_value = str(target_pid or extract_project_id(target_url) or "")
    if pid_value:
        upsert_project_identity(
            new_project_key,
            root_pid=pid_value,
            latest_pid=pid_value,
            project_name=new_project_name,
            chat_id=chat_id,
            status="RESUME_REQUESTED",
        )
    return {
        "ok": True,
        "project_key": new_project_key,
        "project_name": new_project_name,
        "source_key": source_key,
        "source_name": source_name,
        "settings": new_settings,
    }


def format_copied_settings_summary(result: dict) -> str:
    """[P19] ملخص نصي للإعدادات المنسوخة يُرسل للمستخدم بعد النسخ."""
    settings = result.get("settings") or {}
    github = settings.get("github", {}) if isinstance(settings.get("github"), dict) else {}
    if github.get("enabled"):
        branch_label = github.get("branch") or github.get("detected_default_branch") or "auto-default"
        github_line = f"{github.get('repository') or 'غير معروف'} @ {branch_label}"
        token_line = "منسوخ من المشروع المصدر ✅" if github.get("token_present") else "غير موجود بالمصدر — أضفه من الإعدادات ⚠️"
    else:
        github_line = "غير مفعل (كما في المصدر)"
        token_line = "—"
    resume_prompt = (settings.get("continuation") or {}).get("prompt") or DEFAULT_PROJECT_RESUME_PROMPT
    return (
        "📋 <b>تم نسخ الإعدادات بنجاح من مشروع آخر.</b>\n"
        f"<b>المصدر:</b> {html_escape(str(result.get('source_name') or ''))}\n"
        f"<b>الاسم الجديد:</b> {html_escape(str(result.get('project_name') or ''))}\n"
        f"<b>المفتاح:</b> <code>{html_escape(str(result.get('project_key') or ''))}</code>\n"
        f"<b>الموديل:</b> <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n"
        f"<b>GitHub:</b> {html_escape(github_line)}\n"
        f"<b>Token:</b> {html_escape(token_line)}\n"
        f"<b>برومبت الاستئناف:</b> <code>{html_escape(resume_prompt)}</code>\n"
        "أرسل الآن التعديل أو البرومبت المطلوب على هذا المشروع."
    )


def start_project_resume_from_key(chat_id: int, project_key: str) -> bool:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        return False
    identity = get_project_identity_record(key) or {}
    context = summarize_project_context(identity, current_pid=identity.get("latest_genspark_pid"))
    target_url = str(context.get("resume_url") or "")
    target_pid = str(context.get("resume_pid") or context.get("latest_pid") or context.get("root_pid") or "")
    return present_resume_summary(chat_id, project_key=key, target_url=target_url, target_pid=target_pid)


def build_completed_message_keyboard(pub_url: str | None, resume_pid: str | None, project_key: str | None) -> dict:
    """🎛️ [P33] كيبورد رسالة الاكتمال النهائية — بناء مركزي قابل للاختبار.

    الترتيب المعتمد (الأزرار الخمسة القديمة كلها محفوظة حرفياً بلا حذف أو تعديل):
      1. 🌐 فتح المعاين المباشر (url — فقط عند وجود رابط عام: url=None كان يكسر الرسالة كلها بصمت)
      2. ▶️ كمل الآن (cont:{resume_pid}) — صف مستقل [P33 جديد]
      3. 🔄 استئناف هذا المشروع + 🌳 نقاط الاستئناف (نفس الصف القديم)
      4. ⭐ تفاصيل المشروع (pview:{project_key})
      5. 🚀 مشروع جديد
      6. ⬅️ رجوع للوحة التحكم (cmd:dashboard) — أسفل الكيبورد دائماً [P33 جديد]
    الزران الجديدان يعيدان استعمال معالجات قائمة: cont: (سطر السلسلة) + فرع
    cmd:dashboard المكافئ حرفياً لـ cmd:show_dashboard (بلا لمس الفرع القديم —
    حراس P26 يستخدمون حرفيته كمرساة index).
    """
    kb_rows = []
    if pub_url:
        kb_rows.append([{"text": "🌐 فتح المعاين المباشر", "url": pub_url}])
    if resume_pid:
        kb_rows.append([{"text": "▶️ كمل الآن", "callback_data": f"cont:{resume_pid}", "style": "success"}])
        kb_rows.append([
            {"text": "🔄 استئناف هذا المشروع", "callback_data": f"cont:{resume_pid}"},
            {"text": "🌳 نقاط الاستئناف", "callback_data": f"tree:{resume_pid}"},
        ])
    if project_key:
        kb_rows.append([{"text": "⭐ تفاصيل المشروع", "callback_data": f"pview:{project_key}"}])
    kb_rows.append([{"text": "🚀 مشروع جديد", "callback_data": "cmd:new_proj"}])
    kb_rows.append([{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:dashboard"}])
    return make_inline_keyboard(kb_rows)


def build_model_decline_keyboard(pub_url: str | None, resume_pid: str | None, project_key: str | None) -> dict:
    """🚫 [P35] كيبورد رسالة رفض الموديل — تمييز بصري فوري عن رسالة الاكتمال.

    الفرق البصري المعتمد: رسالة اكتمال عادية = زر أخضر واحد (▶️ كمل الآن) /
    رسالة رفض = زران ملونان بارزان أعلى الكيبورد:
      1. 🔵 [✍️ أعد صياغة البرومبت] — style: primary (أزرق)
         🔄 [P37] يحمل مفتاح المشروع: cmd:decline_retry:{project_key} ⟹ ضغطه يفتح
         بطاقة «🔄 ملخص الاستئناف» الكاملة فوراً (▶️ كمل الآن / ⚙️ عدّل الإعدادات).
         Fallback آمن: بلا مفتاح (أو لو تجاوز الـcallback حد تليجرام 64 بايت)
         يعود للحرفية القديمة cmd:decline_retry (إرشاد نصي فقط — عقد P35).
      2. 🔴 [⬅️ رجوع للوحة التحكم] (cmd:decline_dashboard) — style: danger (أحمر)
    ثم كل أزرار الاكتمال المعتادة تحتهما حرفياً عبر build_completed_message_keyboard
    (بلا أي نسخ يدوي — أي تطور مستقبلي في كيبورد الاكتمال يسري هنا تلقائياً).
    كلا النمطين ضمن ALLOWED_BUTTON_STYLES الرسمية (primary/success/danger).
    """
    # 🔄 [P37] الزر الأزرق يمرر مفتاح المشروع لفتح بطاقة ملخص الاستئناف مباشرة
    retry_cb = "cmd:decline_retry"
    clean_key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if clean_key:
        candidate = f"cmd:decline_retry:{clean_key}"
        if len(candidate.encode("utf-8")) <= 64:
            retry_cb = candidate
    kb_rows = [
        [{"text": "✍️ أعد صياغة البرومبت", "callback_data": retry_cb, "style": "primary"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:decline_dashboard", "style": "danger"}],
    ]
    base = build_completed_message_keyboard(pub_url, resume_pid, project_key)
    kb_rows.extend(base.get("inline_keyboard") or [])
    return make_inline_keyboard(kb_rows)


def _is_fresh_artifact(path: pathlib.Path, min_mtime: float | None) -> bool:
    if min_mtime is None:
        return True
    try:
        return path.stat().st_mtime >= (float(min_mtime) - 1.0)
    except Exception:
        return False


def inspect_stage_artifacts(stage_dir: str | None, min_mtime: float | None = None) -> dict:
    details = {
        "stage_dir": str(stage_dir or ""),
        "stage_dir_exists": False,
        "archive_exists": False,
        "archive_fresh": False,
        "payload_files": 0,
        "fresh_payload_files": 0,
        "stale_only": False,
    }
    if not stage_dir:
        return details
    try:
        root = pathlib.Path(stage_dir).resolve()
    except Exception:
        return details
    if not root.exists() or not root.is_dir():
        return details
    details["stage_dir_exists"] = True
    archive_path = root / "webapp.tar.gz"
    if archive_path.exists() and archive_path.is_file() and archive_path.stat().st_size > 0:
        details["archive_exists"] = True
        details["archive_fresh"] = _is_fresh_artifact(archive_path, min_mtime)
    for item in root.rglob("*"):
        if item.is_file() and item.name != "webapp.tar.gz":
            details["payload_files"] += 1
            if _is_fresh_artifact(item, min_mtime):
                details["fresh_payload_files"] += 1
    any_artifacts = details["archive_exists"] or details["payload_files"] > 0
    details["stale_only"] = any_artifacts and not (details["archive_fresh"] or details["fresh_payload_files"] > 0)
    return details


def should_capture_project_update(stage_url: str | None, stage_status: str | None, stage_dir: str | None, min_mtime: float | None = None) -> tuple[bool, dict]:
    pid = extract_stage_project_id(stage_url, stage_dir)
    artifacts = inspect_stage_artifacts(stage_dir, min_mtime=min_mtime)
    has_artifacts = artifacts["archive_fresh"] or artifacts["fresh_payload_files"] > 0
    reason = ""
    if not pid:
        reason = "لا يوجد Project ID صالح للحفظ أو الاستئناف"
    elif artifacts["stale_only"]:
        reason = "الملفات الموجودة قديمة من تشغيل سابق وليست artefacts جديدة لهذه المحاولة"
    elif not has_artifacts:
        reason = "لا توجد ملفات أو archive صالحة للحفظ من هذه المحاولة"
    actionable = bool(pid and has_artifacts)
    return actionable, {
        "pid": pid,
        "status": str(stage_status or ""),
        "has_artifacts": has_artifacts,
        "reason": reason,
        **artifacts,
    }


NON_ACTIONABLE_PROGRESS_STATUSES = {
    "NO_ENGINE", "LOGIN_FAILED", "SESSION_EXPIRED", "FORBIDDEN",
    "FAILED", "CHAT_ERROR", "TIMEOUT",
}


def should_emit_progress_event(stage_url: str | None, stage_status: str | None, stage_dir: str | None, min_mtime: float | None = None) -> tuple[bool, dict]:
    status = str(stage_status or "").strip()
    actionable, meta = should_capture_project_update(stage_url, stage_status, stage_dir, min_mtime=min_mtime)
    if status not in NON_ACTIONABLE_PROGRESS_STATUSES:
        meta["emit_reason"] = "actionable-status"
        return True, meta
    if actionable:
        meta["emit_reason"] = "failure-with-salvageable-artifacts"
        return True, meta
    meta["emit_reason"] = "filtered-non-actionable-failure-event"
    return False, meta


def describe_archive_delivery(ext_dir: str | None) -> tuple[pathlib.Path | None, str | None]:
    if not ext_dir:
        return None, None
    archive_path = pathlib.Path(ext_dir) / "webapp.tar.gz"
    if not archive_path.exists() or not archive_path.is_file():
        return None, None
    # إرجاع None للرسالة حتى لا يتم إرسال أي إشعار مزعج في التليجرام
    return archive_path, None


def get_credit_continuation_limit(bridge_cfg: BridgeConfig | None) -> int:
    try:
        return max(1, int(getattr(bridge_cfg, "max_credit_continuations", 10) or 10))
    except Exception:
        return 10


def get_credit_continuation_progress(bridge_cfg: BridgeConfig | None) -> tuple[int, int]:
    limit = get_credit_continuation_limit(bridge_cfg)
    try:
        current = max(0, int(getattr(bridge_cfg, "last_credit_continuations", 0) or 0))
    except Exception:
        current = 0
    return current, limit


def format_credit_continuation_progress(bridge_cfg: BridgeConfig | None) -> str:
    current, limit = get_credit_continuation_progress(bridge_cfg)
    return f"{current}/{limit}"


def _set_credit_checkpoint_state(bridge_cfg: BridgeConfig | None, state: str, note: str = "") -> None:
    if bridge_cfg is None:
        return
    bridge_cfg.last_credit_checkpoint_state = str(state or "")
    bridge_cfg.last_credit_checkpoint_note = str(note or "")
    if not state:
        bridge_cfg.last_credit_checkpoint_id = ""
        bridge_cfg.last_credit_resume_target_url = ""
        bridge_cfg.last_credit_resume_project_id = ""


def _normalize_progress_callback_result(callback_result) -> dict:
    if isinstance(callback_result, dict):
        return {
            "allow_continuation": bool(callback_result.get("allow_continuation", True)),
            "project_update_preserved": callback_result.get("project_update_preserved"),
            "reason": str(callback_result.get("reason") or ""),
            "checkpoint_id": str(callback_result.get("checkpoint_id") or ""),
        }
    if callback_result is False:
        return {
            "allow_continuation": False,
            "project_update_preserved": False,
            "reason": "progress_callback returned False",
            "checkpoint_id": "",
        }
    return {
        "allow_continuation": True,
        "project_update_preserved": None,
        "reason": "",
        "checkpoint_id": "",
    }


def evaluate_credit_checkpoint_gate(
    bridge_cfg: BridgeConfig | None,
    callback_result=None,
    callback_error: Exception | None = None,
    progress_callback_present: bool = False,
) -> dict:
    if not progress_callback_present:
        _set_credit_checkpoint_state(bridge_cfg, "UNTRACKED", "no progress callback attached")
        return {"allow_continuation": True, "reason": "", "checkpoint_id": ""}
    if callback_error is not None:
        reason = f"progress_callback failed: {callback_error}"
        _set_credit_checkpoint_state(bridge_cfg, "BLOCKED_CALLBACK_ERROR", reason)
        if bridge_cfg is not None:
            bridge_cfg.last_credit_checkpoint_id = ""
        return {"allow_continuation": False, "reason": reason, "checkpoint_id": ""}
    decision = _normalize_progress_callback_result(callback_result)
    if decision["project_update_preserved"] is True:
        note = decision["checkpoint_id"] or "checkpoint preserved"
        _set_credit_checkpoint_state(bridge_cfg, "PRESERVED", note)
        if bridge_cfg is not None:
            bridge_cfg.last_credit_checkpoint_id = decision["checkpoint_id"]
        return {
            "allow_continuation": bool(decision["allow_continuation"]),
            "reason": decision["reason"],
            "checkpoint_id": decision["checkpoint_id"],
        }
    if decision["project_update_preserved"] is False or not decision["allow_continuation"]:
        reason = decision["reason"] or "checkpoint/report was not preserved before continuation"
        _set_credit_checkpoint_state(bridge_cfg, "BLOCKED_NOT_PRESERVED", reason)
        if bridge_cfg is not None:
            bridge_cfg.last_credit_checkpoint_id = decision["checkpoint_id"]
        return {"allow_continuation": False, "reason": reason, "checkpoint_id": decision["checkpoint_id"]}
    _set_credit_checkpoint_state(bridge_cfg, "UNSPECIFIED", decision["reason"])
    if bridge_cfg is not None:
        bridge_cfg.last_credit_checkpoint_id = decision["checkpoint_id"]
    return {
        "allow_continuation": bool(decision["allow_continuation"]),
        "reason": decision["reason"],
        "checkpoint_id": decision["checkpoint_id"],
    }


def describe_credit_checkpoint_state(bridge_cfg: BridgeConfig | None) -> str:
    state = str(getattr(bridge_cfg, "last_credit_checkpoint_state", "") or "") if bridge_cfg else ""
    note = str(getattr(bridge_cfg, "last_credit_checkpoint_note", "") or "") if bridge_cfg else ""
    if state == "PRESERVED":
        if note:
            return f"تم حفظ آخر checkpoint صالح قبل التوقف ({note})."
        return "تم حفظ آخر checkpoint صالح قبل التوقف."
    if state == "BLOCKED_CALLBACK_ERROR":
        return f"لم يتم الانتقال تلقائياً للحساب التالي لأن حفظ checkpoint/report فشل: {note}."
    if state == "BLOCKED_NOT_PRESERVED":
        return f"لم يتم الانتقال تلقائياً للحساب التالي لأن آخر مرحلة CREDIT_EXHAUSTED لم تنتج checkpoint صالحاً: {note}."
    if state == "UNTRACKED":
        return "لم يكن هناك progress callback فعّال لتأكيد checkpoint/runtime preservation لهذه المرحلة."
    return ""


def describe_terminal_outcome(status: str | None, pub_url: str | None, bridge_cfg: BridgeConfig | None = None) -> dict:
    status = str(status or "").strip()
    if status == "COMPLETED":
        return {
            "kind": "success",
            "title": "🎉 <b>تم التوليد بنجاح!</b>",
            "note": "اكتمل التنفيذ أو تم الحصول على رابط عام صالح للمشروع.",
            "allow_preview": True,
        }

    # 🚫 [P35] رفض الموديل — فرع مخصص لأنه الفشل الوحيد الذي يُسمح له
    # بمعاينة الرد (نص الرفض قصير ≤ 300 حرف وعرضه يزيد ثقة المستخدم).
    if status == MODEL_DECLINED_STATUS:
        return {
            "kind": "failure",
            "title": "🚫 <b>رفض الموديل تنفيذ هذا الطلب.</b>",
            "note": (
                "وصل رد رفض صريح بلا أي ناتج، فعومل الطلب كأنه لم يُرسل: "
                "مؤشر الاستئناف لم يتقدم ولم يُسجل أي ناتج جديد. "
                "أعد صياغة البرومبت بشكل أوضح أو قسّمه لخطوات أصغر ثم أرسله من جديد."
            ),
            "allow_preview": True,
        }

    mapping = {
        "MAX_ATTEMPTS_EXHAUSTED": (
            "⚠️ <b>توقفت المهمة بعد استنفاد كل محاولات تغيير الحسابات.</b>",
            "لم ينجح أي حساب في إكمال الطلب ضمن الحد المسموح للمحاولات.",
        ),
        "ALL_ACCOUNTS_IN_COOLDOWN": (
            "⚠️ <b>جميع الحسابات في فترة تبريد حالياً.</b>",
            "لا يوجد حساب جاهز الآن لبدء الطلب؛ جرّب لاحقاً بعد انتهاء التبريد.",
        ),
        "ALL_ACCOUNTS_BUSY": (
            "⏳ <b>الحسابات المؤهلة الحالية مشغولة بمهمات أخرى.</b>",
            "لا يوجد حساب حر الآن يمكن نسبه لهذه المهمة بأمان؛ أعد المحاولة بعد قليل.",
        ),
        "CREDIT_EXHAUSTED": (
            "⚠️ <b>توقف التنفيذ قبل الاكتمال بسبب نفاد الرصيد.</b>",
            " ".join(
                part for part in [
                    f"قد يكون تم حفظ آخر تقدم صالح، لكن المشروع لم يكتمل في هذه المحاولة. عداد الاستئناف الحالي: {format_credit_continuation_progress(bridge_cfg)}.",
                    describe_credit_checkpoint_state(bridge_cfg),
                ]
                if part
            ),
        ),
        "DATA_RETENTION": (
            "🧬 <b>توقفت المحاولة بسبب خطأ AI Data Retention على الحساب.</b>",
            "الموديل يتطلب تفعيل AI Data Retention من إعدادات الحساب (Settings → Data Controls)؛ عومل الحساب كنفاد رصيد وتم تبريده، وأعيد إرسال نفس آخر رسالة على حساب آخر إن وُجد.",
        ),
        "LOGIN_FAILED": (
            "⛔ <b>فشل التنفيذ بسبب مشكلة تسجيل دخول بالحسابات.</b>",
            "لم يتم الوصول إلى جلسة صالحة لإكمال الطلب؛ راجع حالة الحسابات أو جرّب لاحقاً.",
        ),
        "auth_failed": (
            "⛔ <b>فشل التنفيذ بسبب جلسة غير صالحة.</b>",
            "الحساب المستخدم دخل فترة تبريد بعد فشل التحقق أو التحديث.",
        ),
        "TIMEOUT": (
            "⏳ <b>توقفت المهمة بعد انتهاء مهلة الانتظار.</b>",
            "لم يصل رد نهائي صالح قبل انتهاء المهلة المحددة لهذه المحاولة.",
        ),
        "FAILED": (
            "⚠️ <b>انتهت المهمة بدون مشروع صالح مكتمل.</b>",
            "المحاولة انتهت بدون Project ID أو ناتج صالح للاستكمال.",
        ),
        "CHAT_ERROR": (
            "⚠️ <b>فشل التنفيذ بسبب خطأ أثناء إرسال الطلب.</b>",
            "حدث خطأ في طبقة المحادثة قبل اكتمال المشروع الحالي.",
        ),
        "NO_ENGINE": (
            "⛔ <b>تعذر بدء التنفيذ لعدم توفر محرك Genspark صالح.</b>",
            "لم يتم تحميل محرك التوليد المطلوب داخل البيئة الحالية.",
        ),
        "FORBIDDEN": (
            "⛔ <b>توقفت المهمة بسبب رفض الوصول للمشروع.</b>",
            "تم رفض الاستمرار في المشروع الحالي قبل الوصول إلى ناتج قابل للحفظ.",
        ),
    }
    title, note = mapping.get(
        status,
        (
            "⚠️ <b>انتهت المهمة بدون نجاح مكتمل.</b>",
            "الحالة النهائية لا تمثل نجاحاً كاملاً، لذلك لم يتم إعلان اكتمال المشروع.",
        ),
    )
    return {"kind": "failure", "title": title, "note": note, "allow_preview": False}


def format_active_account_line(raw_email) -> str:
    """📧 [P38] سطر الحساب النشط الموحد عبر كل بطاقات دورة حياة المشروع.

    مصدر واحد للحقيقة بدل نسخ متفرقة: تفريغ/تقليم آمن للإيميل الخام ثم
    fallback ودّي «غير محدد» ثم تهريب HTML مركزي — حتى يعرف المالك دائماً
    أي حساب ينفذ المهمة الحالية في أي بطاقة (لايف/handoff/لقطة/اكتمال/رفض).
    """
    active_email = str(raw_email or "").strip() or "غير محدد"
    return f"📧 <b>الحساب:</b> <code>{html_escape(active_email)}</code>\n"


def process_user_task_async(
    chat_id: int,
    url: str | None,
    query: str,
    model: str = "claude-fable-5",
    project_key_hint: str | None = None,
    project_name_hint: str | None = None,
):
    """دالة خلفية موازية تنفذ المهمة وترفع النتيجة مباشرة لتليجرام والقناة مع نص أحدث رسالة والمسار"""
    run_owner_token = uuid.uuid4().hex
    project_key = None
    claimed_project_run = False
    # 🛑 [P25] تسجيل حدث الإلغاء التفاعلي لهذه المهمة قبل أي عمل —
    # التوكن قصير (12 hex) ليعيش داخل callback_data ≤ 64 بايت.
    cancel_token = new_cancel_token()
    cancel_event = register_cancel_event(cancel_token, chat_id=chat_id)
    try:
        # إصلاح: تهريب HTML لكل مدخلات المستخدم قبل وضعها في رسالة
        safe_query = html_escape(query)[:80]
        task_started_at = time.time()
        cfg = BridgeConfig(model=model, cooldown_hours=29.0)
        cfg.run_started_at = task_started_at
        cfg.selection_owner_token = run_owner_token
        # 🛑 [P25] حقن حدث الإلغاء في الـ config — يسري تلقائياً لمحرك SSE وحلقات المتابعة
        cfg.cancel_event = cancel_event
        cfg.cancel_token = cancel_token
        requested_pid = extract_project_id(url) if url else ""
        known_project_key = lookup_project_key_for_locator(url) if url else None
        hinted_project_key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key_hint or ""))[:80]
        # نفس Project Context يُفضَّل من state/handler أولاً، ثم lookup من الـURL/PID، ثم مشروع جديد.
        project_key = hinted_project_key or known_project_key or f"prj_{uuid.uuid4().hex[:16]}"
        claimed_project_run = claim_project_run(project_key, run_owner_token)
        if not claimed_project_run:
            send_telegram_message(chat_id, f"⏳ <b>المشروع <code>{html_escape(project_key)}</code> قيد التنفيذ حالياً.</b>\nانتظر انتهاء المهمة الجارية أو أعد المحاولة بعد قليل.")
            return
        registry = ProjectRegistry(project_key)
        cfg.selection_project_key = project_key
        runtime_binding = apply_project_runtime_binding(cfg, project_key, requested_model=model, registry=registry)
        send_telegram_message(chat_id, f"🚀 <b>جاري بدء المعالجة والتوليد...</b> <code>v{BUILD_VERSION}</code>\n💬 البرومبت: <i>{safe_query}...</i>\n🧠 الموديل: <code>{html_escape(cfg.model)}</code>")
        existing_identity = get_project_identity_record(project_key) or {}
        project_name = project_name_hint or existing_identity.get("project_name") or re.sub(r"\s+", " ", query).strip()[:60] or "مشروع بدون اسم"
        runtime_identity = remember_registry_identity(
            registry,
            root_pid=existing_identity.get("root_genspark_pid") or requested_pid,
            latest_pid=requested_pid or existing_identity.get("latest_genspark_pid"),
            project_name=project_name,
            chat_id=chat_id,
            status="RESUME_REQUESTED" if requested_pid else "STARTED",
        ) or existing_identity
        if (
            getattr(send_telegram_message, "__name__", "") == "send_telegram_message"
            and getattr(send_telegram_message, "__module__", "") == __name__
        ):
            attach_account_selection_live_transport(cfg, chat_id=chat_id, project_key=project_key, project_name=project_name)

        def on_credit_handoff(handoff_meta: dict):
            context = summarize_project_context(
                runtime_identity,
                current_pid=handoff_meta.get("source_project_id"),
                current_url=handoff_meta.get("continuation_url"),
            )
            checkpoint_id = str(handoff_meta.get("checkpoint_id") or getattr(cfg, "last_credit_checkpoint_id", "") or "")
            root_pid = context.get("root_pid") or handoff_meta.get("source_project_id") or "غير معروف"
            latest_pid = context.get("latest_pid") or context.get("current_pid") or root_pid
            checkpoint_line = f"\n<b>Checkpoint:</b> <code>{html_escape(checkpoint_id)}</code>" if checkpoint_id else ""
            resume_url = context.get("resume_url") or str(handoff_meta.get("continuation_url") or "")
            public_resume_prompt = summarize_resume_prompt_for_display(get_bridge_cfg_public_resume_prompt(cfg))
            send_telegram_message(
                chat_id,
                "🔁 <b>تم تثبيت handoff وسيبدأ الآن الاستئناف بنفس سياق المشروع.</b>\n"
                f"<b>المشروع:</b> {html_escape(project_name)}\n"
                f"<b>مفتاح المشروع:</b> <code>{project_key}</code>\n"
                f"{format_active_account_line(getattr(cfg, 'selected_account_email', ''))}"  # 📧 [P38] الحساب المستنزَف الذي ثبّت الـ handoff
                f"<b>Root Project ID:</b> <code>{html_escape(root_pid)}</code>\n"
                f"<b>Latest Project ID:</b> <code>{html_escape(latest_pid)}</code>\n"
                f"<b>عداد الاستئناف:</b> <code>{html_escape(str(handoff_meta.get('continuation_index') or 0))}/{html_escape(str(handoff_meta.get('continuation_limit') or get_credit_continuation_limit(cfg)))}</code>{checkpoint_line}\n"
                f"<b>برومبت الاستئناف التالي:</b> <code>{html_escape(public_resume_prompt)}</code>\n"
                f"<b>رابط الاستئناف التالي:</b> {html_escape(resume_url)}\n"
                "<b>الوضع:</b> سيتم إرسال برومبت الاستئناف الخاص بهذا المشروع بعد اكتمال الحفظ بنجاح."
            )

        cfg.credit_handoff_callback = on_credit_handoff

        def on_project_update(stage_url, stage_status, stage_dir, stage_text, stage_email, stage_query):
            nonlocal runtime_identity
            actionable, stage_meta = should_capture_project_update(stage_url, stage_status, stage_dir, min_mtime=task_started_at)
            if not actionable:
                log_event("warning", f"تم تخطي checkpoint/report للحالة {stage_status}: {stage_meta['reason']}", extra=stage_meta)
                return {
                    "allow_continuation": stage_status != "CREDIT_EXHAUSTED",
                    "project_update_preserved": False,
                    "reason": stage_meta["reason"],
                    "checkpoint_id": "",
                }
            runtime_identity = remember_registry_identity(
                registry,
                root_pid=(runtime_identity or {}).get("root_genspark_pid") or requested_pid or stage_meta["pid"],
                latest_pid=stage_meta["pid"],
                project_name=project_name,
                chat_id=chat_id,
                status=stage_status,
            ) or runtime_identity
            update = registry.snapshot(stage_dir, stage_url, stage_status, stage_text)
            checkpoint_id = str(update.get("checkpoint") or "")
            sync = registry.github_sync(update)
            all_jobs = sync.get("jobs") or []
            queued_jobs = [job for job in all_jobs if str(job.get("state") or "") != "synced"]
            queued_ids = sync.get("queued") or []
            context = summarize_project_context(runtime_identity, current_pid=stage_meta["pid"], current_url=stage_url)
            if queued_jobs:
                first_job = queued_jobs[0]
                dest = first_job.get("destination", {}) if isinstance(first_job, dict) else {}
                branch_label = dest.get("branch") or ("auto-default" if dest.get("branch_mode") == "auto_default" else "غير محدد")
                details = "\n".join(
                    f"• <code>{html_escape(job.get('job_id'))}</code> → <code>{html_escape(job.get('state'))}</code> → <code>{html_escape(dest.get('repository') or '')}</code> @ <code>{html_escape(branch_label)}</code>"
                    for job in queued_jobs[:3]
                )
                details += "\n• لم يتم تأكيد الرفع إلى GitHub بعد؛ هذه فقط job/queue جاهزة أو قيد التنفيذ."
            elif sync.get("upload_confirmed") or sync.get("uploaded") or sync.get("modified") or sync.get("deleted"):
                commit_info = f"\n• 🔗 <b>Commit:</b> <code>{html_escape(sync.get('commit_hash', ''))}</code>" if sync.get("commit_hash") else ""
                stats_line = f"• 📊 <b>الإحصائيات:</b> ➕ <b>{len(sync.get('uploaded', []))}</b> جديد | ✏️ <b>{len(sync.get('modified', []))}</b> معدل | 🗑️ <b>{len(sync.get('deleted', []))}</b> محذوف | ⏸️ <b>{len(sync.get('unchanged', []))}</b> مطابق"
                file_lines = []
                for x in sync.get("uploaded", [])[:10]:
                    file_lines.append(f"  ➕ <code>{html_escape(x)}</code>")
                for x in sync.get("modified", [])[:10]:
                    file_lines.append(f"  ✏️ <code>{html_escape(x)}</code>")
                for x in sync.get("deleted", [])[:10]:
                    file_lines.append(f"  🗑️ <code>{html_escape(x)}</code>")
                files_block = "\n" + "\n".join(file_lines) if file_lines else ""
                details = f"{stats_line}{commit_info}{files_block}"
            else:
                details = f"• لم يجد النظام أي تغيير جديد؛ المستودع مطابق تماماً للأرشيف الحالي (Unchanged: <code>{len(sync.get('unchanged', []))}</code>)."
            skipped = "\n".join(f"• <code>{html_escape(x)}</code>" for x in sync.get("skipped", [])[:8])
            github_label = "تم إنشاء job GitHub لهذا المشروع ولم يتم تأكيد الرفع بعد" if sync.get("enabled") and queued_jobs else ("✅ تم الرفع والمزامنة بنجاح لـ GitHub" if sync.get("upload_confirmed") or sync.get("uploaded") or sync.get("modified") else ("تعذر تأكيد رفع GitHub لهذه اللقطة" if sync.get("enabled") and sync.get("upload_error") else "غير مفعل لهذا المشروع أو إعدادات GitHub غير مكتملة"))
            stage_label = "⚠️ استنزاف رصيد — تم حفظ نقطة استئناف صالحة ويجري الآن تقييم handoff" if stage_status == "CREDIT_EXHAUSTED" else "🔄 تحديث مشروع صالح"
            continuation_line = ""
            handoff_line = ""
            if stage_status == "CREDIT_EXHAUSTED":
                public_resume_prompt = summarize_resume_prompt_for_display(get_bridge_cfg_public_resume_prompt(cfg))
                continuation_line = f"\n<b>عداد الاستئناف:</b> <code>{format_credit_continuation_progress(cfg)}</code>"
                handoff_line = (
                    f"\n<b>Checkpoint:</b> <code>{html_escape(checkpoint_id)}</code>"
                    f"\n<b>Root Project ID:</b> <code>{html_escape(context.get('root_pid') or stage_meta['pid'])}</code>"
                    f"\n<b>Latest Project ID:</b> <code>{html_escape(context.get('latest_pid') or stage_meta['pid'])}</code>"
                    f"\n<b>برومبت الاستئناف المرشح:</b> <code>{html_escape(public_resume_prompt)}</code>"
                    f"\n<b>رابط الاستئناف المرشح:</b> {html_escape(context.get('current_url') or context.get('resume_url') or build_genspark_viewer_url(stage_meta['pid']))}"
                    "\n<b>الوضع:</b> لم يبدأ إرسال برومبت الاستئناف بعد؛ سيبدأ فقط إذا اكتمل حفظ checkpoint/report ضمن نفس مفتاح المشروع."
                )
            msg = (f"{stage_label}\n<b>المشروع:</b> {html_escape(project_name)}\n"
                   f"<b>مفتاح المشروع:</b> <code>{project_key}</code>\n"
                   f"{format_active_account_line(stage_email or getattr(cfg, 'selected_account_email', ''))}"  # 📧 [P38] الحساب المنفِّذ للقطة — stage_email من المحرك أولاً
                   f"<b>الحالة:</b> <code>{html_escape(stage_status)}</code>\n"
                   f"<b>Project ID:</b> <code>{html_escape(stage_meta['pid'])}</code>{continuation_line}{handoff_line}\n"
                   f"<b>GitHub:</b> {github_label}\n<b>طابور/الملفات:</b>\n{details}")
            if skipped:
                msg += f"\n<b>ملفات لم تُرفع:</b>\n{skipped}"
            send_telegram_message(chat_id, msg)
            return {
                "allow_continuation": True,
                "project_update_preserved": True,
                "reason": "",
                "checkpoint_id": checkpoint_id,
                "queued": queued_ids,
                "resume_url": context.get("resume_url") or context.get("current_url"),
                "root_pid": context.get("root_pid"),
                "latest_pid": context.get("latest_pid"),
            }

        live_preview_msg_id = None
        seen_live_preview_pid = None

        def handle_live_project_start(live_pid: str):
            nonlocal live_preview_msg_id, seen_live_preview_pid
            if not live_pid or seen_live_preview_pid == live_pid:
                return
            seen_live_preview_pid = live_pid
            # 🛑 [P25] زر الإلغاء الأحمر يظهر أسفل زر المعاينة الأزرق من أول لحظة
            preview_kb = build_live_preview_keyboard(live_pid, status="running", cancel_token=cancel_token)
            update_cancel_entry(cancel_token, live_pid=live_pid, project_key=project_key)
            text = (
                f"⚡ <b>بدأ بناء المشروع السحابي فوراً!</b>\n"
                f"📌 <b>المشروع:</b> {html_escape(project_name)}\n"
                f"🆔 <b>Project ID:</b> <code>{html_escape(live_pid)}</code>\n"
                f"{format_active_account_line(getattr(cfg, 'selected_account_email', ''))}"  # 📧 [P38] الحساب المنفِّذ من أول لحظة
                f"🧠 <b>الموديل:</b> <code>{html_escape(cfg.model)}</code>\n\n"
                f"🌐 <i>يمكنك متابعة التوليد والأكواد لحظياً عبر الزر أدناه:</i>"
            )
            try:
                res = send_telegram_message_detailed(chat_id, text, reply_markup=preview_kb)
                if res and isinstance(res, dict) and res.get("ok"):
                    live_preview_msg_id = res.get("result", {}).get("message_id")
            except Exception as live_err:
                log_event("warning", f"تعذر إرسال بطاقة المعاينة الفورية: {live_err}")

        pub_url, status, used_acc, ext_dir, last_resp_text = send_message_with_auto_account_failover(
            url=url, query=query, bridge_cfg=cfg, progress_callback=on_project_update,
            on_project_start_callback=handle_live_project_start,
        )

        # 🚫 [P35] كشف رفض الموديل — الرد القصير "The model declined..." يصل
        # بحالة COMPLETED تقنياً (طوله > 25 حرفاً) لكنه بلا أي ناتج؛ يُعاد
        # تصنيفه MODEL_DECLINED ويُعامل «كأن الطلب لم يُرسل» — مؤشر الاستئناف
        # لا يتقدم لنقطة الرفض أبداً (التجاوز فقط فوق COMPLETED — أي فشل آخر
        # يمر بمساره القديم حرفياً = Zero Breaking).
        model_declined = status == "COMPLETED" and is_model_decline_response(last_resp_text)
        if model_declined:
            status = MODEL_DECLINED_STATUS
            log_event("warning", "🚫 [P35] الموديل رفض الطلب — يُعامل كأن الطلب لم يُرسل (مؤشر الاستئناف ثابت)")

        if status == "ALL_ACCOUNTS_IN_COOLDOWN":
            send_telegram_message(
                chat_id,
                "⚠️ <b>جميع الحسابات المصرح بها مشغولة أو في فترة التبريد حالياً.</b>\n"
                "يرجى المحاولة بعد قليل أو عند تجدد رصيد الحسابات تلقائياً (29h)."
            )
            return
        if status == "ALL_ACCOUNTS_BUSY":
            send_telegram_message(
                chat_id,
                "⏳ <b>كل الحسابات المؤهلة الحالية محجوزة لمهمات أخرى.</b>\n"
                "لم يبدأ التنفيذ على حساب جديد لأننا ثبّتْنا attribution آمن لكل مهمة. أعد المحاولة بعد قليل."
            )
            return
        # 🛑 [P25] المستخدم أكد الإلغاء — رسالة نهائية هادئة وتسجيل الحالة ثم خروج نظيف
        if status == CANCELLED_STATUS:
            cancelled_pid = seen_live_preview_pid or requested_pid or ""
            try:
                remember_registry_identity(
                    registry,
                    latest_pid=cancelled_pid or None,
                    project_name=project_name,
                    chat_id=chat_id,
                    status=CANCELLED_STATUS,
                )
            except Exception:
                pass
            pid_line = f"\n🆔 <b>Project ID:</b> <code>{html_escape(cancelled_pid)}</code>" if cancelled_pid else ""
            send_telegram_message(
                chat_id,
                "⛔ <b>تم إلغاء المهمة بالكامل بناءً على تأكيدك.</b>\n"
                f"📌 <b>المشروع:</b> {html_escape(project_name)}\n"
                f"🔐 <b>مفتاح المشروع:</b> <code>{project_key}</code>{pid_line}\n"
                "🧹 تم قطع البث وتحرير الحساب والموارد فوراً — يمكنك بدء مهمة جديدة الآن.",
                reply_markup=build_dashboard_keyboard(chat_id),  # 🛑 [P25] اللوحة الكاملة بعد الإلغاء بدل الزر اليتيم
            )
            return

        acc_email = html_escape(used_acc.get("email")) if used_acc else "غير محدد"
        # 🧾 [P29] سطر مسار الحسابات — يظهر فقط عند تعدد الحسابات الفعلية أثناء المهمة
        journey_line = format_account_journey_line(getattr(cfg, "account_journey", []))
        journey_block = f"\n{journey_line}" if journey_line else ""
        # ⏱️ [P30] كتلة المحاسبة الزمنية — تظهر دائماً عند وجود spans (حتى بحساب واحد)
        timing_stats = format_account_timing_block(cfg, task_total_seconds=time.time() - task_started_at)
        timing_block = f"\n\n{timing_stats}" if timing_stats else ""
        is_finished = check_project_finished_flag(status, last_resp_text)
        final_pid = extract_stage_project_id(pub_url, ext_dir)
        if model_declined:
            # 🚫 [P35] الرفض كأن الطلب لم يُرسل: تصفير final_pid يمنع تقدّم
            # latest_genspark_pid/resume_pid لنقطة الرفض — المؤشر يبقى على
            # آخر نقطة صالحة قبل الطلب المرفوض (requested_pid أو المخزّن).
            final_pid = ""
        runtime_identity = remember_registry_identity(
            registry,
            root_pid=(runtime_identity or {}).get("root_genspark_pid") or requested_pid or final_pid,
            latest_pid=final_pid or requested_pid or (runtime_identity or {}).get("latest_genspark_pid"),
            project_name=project_name,
            chat_id=chat_id,
            status=status,
        ) or runtime_identity
        context = summarize_project_context(runtime_identity, current_pid=final_pid or requested_pid, current_url=pub_url or url)
        pid = context.get("current_pid") or final_pid or requested_pid or "غير معروف"
        resume_pid = context.get("resume_pid") or final_pid or requested_pid or ""
        outcome = describe_terminal_outcome(status, pub_url, cfg)

        response_preview = ""
        preview_body = ""
        if outcome["allow_preview"] and last_resp_text:
            clean_text = redact_github_secrets(str(last_resp_text).strip())
            clean_text = html_escape(clean_text)
            # ✂️ [P34] قصّ المعاينة مركزياً إلى 1000 حرف + لاحقة الرابط الكامل
            clean_text = clamp_preview_text(clean_text)
            preview_body = clean_text
            response_preview = f"💬 <b>آخر رسالة من التوليد:</b>\n<pre>{clean_text}</pre>\n\n"

        # إصلاح: لو مفيش رابط عام نكتب تنبيه بدل زر ميت (كان تليجرام يرفض الكيبورد بالكامل)
        if pub_url:
            url_line = f"🌐 <b>رابط الويب اب العام:</b> {html_escape(pub_url)}"
        else:
            url_line = "🌐 <b>رابط الويب اب العام:</b> غير متاح (المشروع قد يكون خاصاً أو لم يكتمل)"
        root_line = f"\n🌱 <b>Root Project ID:</b> <code>{html_escape(context.get('root_pid') or pid)}</code>"
        latest_line = f"\n🧷 <b>Latest Project ID:</b> <code>{html_escape(context.get('latest_pid') or pid)}</code>"
        resume_line = ""
        if context.get("resume_url"):
            resume_line = f"\n🔗 <b>رابط الاستئناف الحالي:</b> {html_escape(context.get('resume_url'))}"
        fork_line = ""
        if context.get("forked"):
            fork_line = "\n🔀 <b>سياق المشروع:</b> تم الحفاظ على نفس مفتاح المشروع رغم انتقال الـProject ID أثناء continuation/fork."

        res_msg = (
            f"{outcome['title']}\n\n"
            f"{response_preview}"
            f"🧭 <b>النتيجة النهائية:</b> {html_escape(outcome['note'])}\n"
            f"{url_line}\n"
            f"📁 <b>مسار الساندبوكس:</b> <code>{html_escape(ext_dir or 'غير متاح')}</code>\n"
            f"📊 <b>الحالة:</b> <code>{html_escape(status)}</code>\n"
            f"📌 <b>اسم المشروع:</b> {html_escape(project_name)}\n"
            f"🔐 <b>مفتاح المشروع:</b> <code>{project_key}</code>\n"
            f"📧 <b>الحساب:</b> <code>{acc_email}</code>{journey_block}\n"  # 📧 [P38] تسمية موحدة (acc_email مُهرَّب مسبقاً — لا تهريب مزدوج) + عقد P29 journey_block محفوظ حرفياً
            f"🆔 <b>Project ID:</b> <code>{html_escape(pid)}</code>{root_line}{latest_line}{resume_line}{fork_line}\n"
            f"🏁 <b>علم الانتهاء:</b> {'✅ مكتمل (FINISHED)' if is_finished else '⚠️ غير مكتمل'}"
            f"{timing_block}"
        )
        # ✂️ [P34] ميزانية الرسالة المجمعة: لا تتجاوز 3500 حرفاً أبداً (القصّ على المعاينة أولاً)
        res_msg = enforce_completion_message_budget(res_msg, preview_body)

        # 🎛️ [P33] الكيبورد المركزي للاكتمال — الأزرار الخمسة القديمة + ▶️ كمل الآن + ⬅️ رجوع للوحة التحكم
        # 🚫 [P35] رسالة الرفض تأخذ كيبورداً مميزاً (زران ملونان أعلاه ثم أزرار الاكتمال المعتادة)
        if status == MODEL_DECLINED_STATUS:
            reply_markup = build_model_decline_keyboard(pub_url, resume_pid, project_key)
        else:
            reply_markup = build_completed_message_keyboard(pub_url, resume_pid, project_key)

        send_telegram_message(chat_id, res_msg, reply_markup=reply_markup)

        # 🟢 تحديث بطاقة المعاينة الفورية المتطورة لتصبح زر مكتمل (P7-A)
        if live_preview_msg_id and seen_live_preview_pid and status == "COMPLETED":
            completed_kb = build_live_preview_keyboard(seen_live_preview_pid, status="completed")
            completed_text = (
                f"✅ <b>اكتمل بناء المشروع بنجاح 100%!</b>\n"
                f"📌 <b>المشروع:</b> {html_escape(project_name)}\n"
                f"🆔 <b>Project ID:</b> <code>{html_escape(seen_live_preview_pid)}</code>\n"
                f"{format_active_account_line(used_acc.get('email') if used_acc else '')}"  # 📧 [P38] الحساب المنفِّذ في بطاقة اللايف المكتملة
                f"🧠 <b>الموديل:</b> <code>{html_escape(cfg.model)}</code>\n\n"
                f"🟢 <i>تم الانتهاء وجاهز للعرض والمعاينة التفاعلية:</i>"
            )
            try:
                edit_telegram_message_text(chat_id, live_preview_msg_id, completed_text, reply_markup=completed_kb)
            except Exception as edit_err:
                log_event("warning", f"تعذر تحديث بطاقة المعاينة المكتملة: {edit_err}")

        archive_path, archive_msg = describe_archive_delivery(ext_dir)

        if archive_msg:
            log_event("info", f"تم تعطيل رفع الأرشيف إلى Telegram وفق D-002: {archive_path.name}")
            send_telegram_message(chat_id, archive_msg)
            if str(chat_id) != DEFAULT_CHANNEL_ID:
                send_telegram_message(DEFAULT_CHANNEL_ID, res_msg, reply_markup=reply_markup)
    except Exception as e:
        # إصلاح: أي خطأ داخلي في المهمة يوصل للمستخدم بدل الاختفاء الصامت
        safe_error = redact_github_secrets(str(e))[:500]
        log_event("error", f"خطأ غير متوقع في معالجة المهمة: {safe_error}")
        try:
            send_telegram_message(chat_id, f"⚠️ <b>حدث خطأ داخلي أثناء المعالجة:</b>\n<code>{html_escape(safe_error)}</code>")
        except Exception:
            pass
    finally:
        # 🛑 [P25] تنظيف مضمون لحدث الإلغاء من الذاكرة (Zero Leaks) —
        # يشمل كل المخارج: نجاح/فشل/إلغاء/استثناء. الضغط على زر قديم بعد
        # التنظيف يرد بهدوء "المهمة انتهت بالفعل" (get_cancel_entry ➔ None).
        try:
            unregister_cancel_event(cancel_token)
        except Exception:
            pass
        if project_key and claimed_project_run:
            release_project_run(project_key, run_owner_token)


def get_main_keyboard(chat_id: int | None = None):
    if chat_id is None:
        return build_dashboard_keyboard(next(iter(ALLOWED_CHAT_IDS)))
    return build_dashboard_keyboard(int(chat_id))


def handle_telegram_update(update: dict):
    if "callback_query" in update:
        cb = update["callback_query"]
        msg_info = cb.get("message") or {}
        chat_id = msg_info.get("chat", {}).get("id")
        if not chat_id:
            return
        data = cb.get("data", "")
        # [P17] مسار callback: نحكم بالجروب أو بهوية الضاغط نفسه (cb.from)
        if not is_chat_allowed(chat_id, (cb.get("from") or {}).get("id")):
            send_telegram_message(chat_id, "⛔ غير مصرح لك باستخدام هذا البوت.")
            return

        # ══════════════════════════════════════════════════════
        # 🛑 [P25] الإلغاء التفاعلي — خطوتا أمان قبل التنفيذ القهري
        # (يعالج مبكراً وبمعزل تام عن سلسلة if/elif — صفر تعارض مع pctl:* وغيرها)
        # ══════════════════════════════════════════════════════
        if data.startswith(("cancel_prompt:", "cancel_exec:", "cancel_abort:")):
            action, _, cancel_token = data.partition(":")
            entry = get_cancel_entry(cancel_token)
            card_msg_id = msg_info.get("message_id")
            if entry is None:
                # مهمة انتهت بالفعل أو توكن منتهي — ننظف الأزرار بهدوء
                if card_msg_id:
                    edit_telegram_message_reply_markup(chat_id, card_msg_id, None)
                send_telegram_message(chat_id, "ℹ️ هذه المهمة انتهت بالفعل — لا يوجد بناء نشط لإلغائه.")
                return
            live_pid = str(entry.get("live_pid") or "")
            if action == "cancel_prompt":
                # الخطوة 1: عرض كيبورد التأكيد فقط — لا إلغاء بعد
                if card_msg_id:
                    edit_telegram_message_reply_markup(
                        chat_id, card_msg_id,
                        build_live_preview_keyboard(live_pid, status="confirm_cancel", cancel_token=cancel_token),
                    )
            elif action == "cancel_abort":
                # تراجع: إعادة كيبورد التشغيل الأصلي والاستمرار كأن شيئاً لم يكن
                if card_msg_id:
                    edit_telegram_message_reply_markup(
                        chat_id, card_msg_id,
                        build_live_preview_keyboard(live_pid, status="running", cancel_token=cancel_token),
                    )
            elif action == "cancel_exec":
                # الخطوة 2 (مؤكدة): تفعيل الإلغاء القهري الفوري
                triggered = trigger_cancel(cancel_token)
                if triggered:
                    log_event("warning", f"🛑 [P25] المستخدم أكد إلغاء البناء (token={cancel_token}, pid={live_pid[:16]})")
                    if card_msg_id:
                        edit_telegram_message_text(
                            chat_id, card_msg_id,
                            "⛔ <b>تم إلغاء بناء المشروع فوراً بناءً على طلبك.</b>\n"
                            "🧹 جاري قطع البث وتحرير الحساب والموارد المحجوزة...",
                            reply_markup=None,
                        )
                else:
                    send_telegram_message(chat_id, "ℹ️ تعذر تفعيل الإلغاء — المهمة غالباً انتهت بالفعل.")
            return

        # ══════════════════════════════════════════════════════
        # 🗑️ [P26] حذف المشروع التفاعلي — تأكيد In-Place بخطوتي أمان
        # (كتلة معزولة مبكرة بنمط P25 — صفر تعارض مع pctl:/pset:/pview:)
        # ══════════════════════════════════════════════════════
        if data.startswith(("pdel_prompt:", "pdel_abort:", "pdel_exec:")):
            action, _, raw_key = data.partition(":")
            project_key = re.sub(r"[^A-Za-z0-9_-]", "_", str(raw_key or ""))[:80]
            card_msg_id = msg_info.get("message_id")
            if not project_key:
                send_telegram_message(chat_id, "⚠️ مفتاح المشروع غير صالح — لا يمكن المتابعة.")
                return
            if action == "pdel_prompt":
                # الخطوة 1: تحديث نفس الرسالة فوراً لشاشة التحذير — بدون Spam
                if card_msg_id:
                    edit_telegram_message_text(
                        chat_id, card_msg_id,
                        render_project_delete_confirm_text(project_key),
                        reply_markup=build_project_delete_confirm_keyboard(project_key),
                    )
                else:
                    send_telegram_message(chat_id, render_project_delete_confirm_text(project_key), reply_markup=build_project_delete_confirm_keyboard(project_key))
            elif action == "pdel_abort":
                # التراجع الفوري: عودة نفس الرسالة لشاشة التفاصيل — صفر تعديل ملفات
                if card_msg_id:
                    edit_telegram_message_text(
                        chat_id, card_msg_id,
                        render_project_status_text(project_key),
                        reply_markup=build_current_project_keyboard(project_key),
                    )
                else:
                    send_telegram_message(chat_id, render_project_status_text(project_key), reply_markup=build_current_project_keyboard(project_key))
            elif action == "pdel_exec":
                # الخطوة 2 (مؤكدة): الحذف الذري الشامل — الحماية تُفحص داخل الدالة
                outcome = delete_project_atomically(project_key)
                if outcome.get("ok"):
                    display_name = str(outcome.get("project_name") or project_key)
                    success_text = (
                        "✅ <b>تم حذف المشروع بنجاح.</b>\n"
                        f"📛 <b>الاسم:</b> {html_escape(display_name)}\n"
                        f"🔑 <b>المفتاح:</b> <code>{html_escape(project_key)}</code>\n"
                        "🧹 تم تنظيف الفهرس المركزي وشجرة الاستئناف ومجلد القرص بالكامل."
                    )
                    if card_msg_id:
                        edit_telegram_message_text(chat_id, card_msg_id, success_text, reply_markup=build_project_deleted_keyboard())
                    else:
                        send_telegram_message(chat_id, success_text, reply_markup=build_project_deleted_keyboard())
                elif outcome.get("reason") == "PROJECT_BUILD_ACTIVE":
                    warn_text = (
                        "🛡️ <b>لا يمكن حذف المشروع الآن — يوجد بناء نشط قيد التنفيذ.</b>\n"
                        "🛑 أوقف/ألغِ البناء الجاري أولاً (زر إلغاء البناء) ثم أعد المحاولة."
                    )
                    if card_msg_id:
                        edit_telegram_message_text(
                            chat_id, card_msg_id,
                            render_project_status_text(project_key),
                            reply_markup=build_current_project_keyboard(project_key),
                        )
                    send_telegram_message(chat_id, warn_text)
                elif outcome.get("reason") == "PROJECT_NOT_FOUND":
                    nf_text = "ℹ️ هذا المشروع محذوف بالفعل أو غير موجود في السجل."
                    if card_msg_id:
                        edit_telegram_message_text(chat_id, card_msg_id, nf_text, reply_markup=build_project_deleted_keyboard())
                    else:
                        send_telegram_message(chat_id, nf_text, reply_markup=build_project_deleted_keyboard())
                else:
                    send_telegram_message(chat_id, f"⚠️ تعذر إتمام الحذف: <code>{html_escape(str(outcome.get('reason') or 'UNKNOWN'))}</code> — راجع السجل.")
            return

        if data == "cmd:show_dashboard":
            send_telegram_message(chat_id, render_dashboard_text(chat_id), reply_markup=get_main_keyboard(chat_id))
        elif data == "cmd:dashboard":
            # ⬅️ [P33] زر «رجوع للوحة التحكم» من رسالة الاكتمال — سلوك مطابق حرفياً
            # لـ cmd:show_dashboard (فرع منفصل عمداً: حراس P26 يرسون على حرفية الفرع القديم)
            send_telegram_message(chat_id, render_dashboard_text(chat_id), reply_markup=get_main_keyboard(chat_id))
        elif data == "cmd:decline_retry":
            # 🚫 [P35] زر «✒️ أعد صياغة البرومبت» بعد رفض الموديل — إرشاد فوري:
            # مؤشر الاستئناف لم يتقدم (الرفض كأن الطلب لم يُرسل)، فزر 🔄 استئناف
            # المشروع في نفس الرسالة يكمل من آخر نقطة صالحة قبل الرفض مباشرة.
            # (فرع الـ fallback القديم بحرفيته — يصل هنا فقط لو الكيبورد بلا مفتاح مشروع)
            send_telegram_message(
                chat_id,
                "✒️ <b>أعد صياغة البرومبت وأرسله الآن كرسالة جديدة.</b>\n"
                "🚫 الرفض عومل كأن الطلب لم يُرسل: مؤشر الاستئناف لم يتقدم ولم يُسجل أي ناتج.\n"
                "💡 جرّب صياغة أوضح أو قسّم الطلب لخطوات أصغر، ثم استخدم زر 🔄 استئناف هذا المشروع "
                "لإكمال نفس السياق، أو أرسل البرومبت مباشرة كمهمة جديدة.",
            )
        elif data.startswith("cmd:decline_retry:"):
            # 🔄 [P37] زر «✍️ أعد صياغة البرومبت» بمفتاح مشروع — فتح بطاقة ملخص
            # الاستئناف الكاملة فوراً: render_project_resume_summary_text + كيبوردها
            # التفاعلي (▶️ كمل الآن / ⚙️ عدّل الإعدادات) وضبط الحالة على
            # AWAITING_PROJECT_RESUME_DECISION بسياق المشروع النظيف (root/latest pid)
            # عبر start_project_resume_from_key — البرومبت الجديد التالي يكمل على
            # نفس المشروع مباشرة (المؤشر لم يتقدم لنقطة الرفض — عقد P35 محفوظ).
            retry_key = data.split("cmd:decline_retry:", 1)[1]
            if not start_project_resume_from_key(chat_id, retry_key):
                send_telegram_message(
                    chat_id,
                    "⚠️ <b>تعذر فتح ملخص الاستئناف لهذا المشروع.</b>\n"
                    "✒️ أعد صياغة البرومبت وأرسله كرسالة جديدة، أو استخدم زر 🔄 استئناف المشروع من الرسالة.",
                )
        elif data == "cmd:decline_dashboard":
            # 🚫 [P35] رجوع للوحة التحكم من رسالة الرفض — سلوك مطابق حرفياً لـ cmd:dashboard
            # (فرع منفصل عمداً — نفس فلسفة P33: ممنوع مسّ حرفية الفروع القديمة)
            send_telegram_message(chat_id, render_dashboard_text(chat_id), reply_markup=get_main_keyboard(chat_id))
        elif data == "cmd:new_proj":
            set_user_state(chat_id, {"action": "AWAITING_NEW_PROJECT_NAME"})
            send_telegram_message(chat_id, "🚀 <b>بدء مشروع جديد</b>\nاكتب اسم المشروع أولاً. الاسم يُطلب للمشروع الجديد فقط، وبعدها سنختار الموديل ثم نكمل إعداد GitHub أو بدون GitHub.")
        elif data.startswith("cmd:new_proj_model:"):
            state = get_user_state(chat_id)
            model_name = data.split("cmd:new_proj_model:", 1)[1]
            selected_model = normalize_project_model(model_name)
            if state.get("action") == "AWAITING_NEW_PROJECT_MODEL":
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_GITHUB_MODE",
                    "project_model": selected_model,
                })
                send_telegram_message(chat_id, f"✅ <b>الموديل المختار:</b> <code>{html_escape(selected_model)}</code>\nهل تريد تفعيل GitHub لهذا المشروع من البداية؟", reply_markup=build_new_project_github_choice_keyboard())
            elif state.get("action") == "AWAITING_PROJECT_SETTINGS_MODEL":
                project_key = str(state.get("project_key") or "")
                if not project_key:
                    send_telegram_message(chat_id, "ℹ️ افتح إعدادات مشروع موجود أولاً ثم اختر الموديل المطلوب.")
                else:
                    ProjectRegistry(project_key).set_project_model(selected_model)
                    set_user_state(chat_id, {})
                    send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم تحديث موديل المشروع.</b>\n<b>الموديل الجديد:</b> <code>{html_escape(selected_model)}</code>")
            elif state.get("action") == "AWAITING_BOUND_PROJECT_MODEL":
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_GITHUB_MODE",
                    "project_model": selected_model,
                })
                send_telegram_message(chat_id, f"✅ <b>الموديل المختار:</b> <code>{html_escape(selected_model)}</code>\nهل تريد تفعيل GitHub لهذا المشروع الخارجي من البداية؟", reply_markup=build_bound_project_github_choice_keyboard())
            else:
                send_telegram_message(chat_id, "ℹ️ ابدأ أولاً من زر <b>مشروع جديد</b> أو افتح إعدادات مشروع موجود أو ابدأ ربط مشروع خارجي قبل اختيار الموديل.")
        elif data == "cmd:new_proj_github_yes":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_NEW_PROJECT_GITHUB_MODE":
                send_telegram_message(chat_id, "ℹ️ ابدأ أولاً من زر <b>مشروع جديد</b> ثم اختر الموديل قبل إعداد GitHub.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_GITHUB_REPO",
                })
                send_telegram_message(chat_id, "🔗 <b>ربط GitHub لهذا المشروع</b>\nأرسل رابط المستودع أو الصيغة <code>owner/repo</code> أولاً.")
        elif data in {"cmd:new_proj_github_no", "cmd:new_proj_github_disable"}:
            state = get_user_state(chat_id)
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            project_model = normalize_project_model(state.get("project_model"))
            if not project_key or not project_name:
                send_telegram_message(chat_id, "ℹ️ ابدأ أولاً من زر <b>مشروع جديد</b> ثم اختر الاسم والموديل.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION",
                    "project_model": project_model,
                    "pending_github_enabled": False,
                    "pending_github_repository": "",
                    "pending_github_token": "",
                    "pending_github_branch": "",
                    "pending_github_branch_mode": "disabled",
                    "pending_github_default_branch": "",
                    "pending_github_branches": [],
                    "pending_github_repo_check_status": "disabled",
                })
                send_telegram_message(chat_id, f"✅ <b>سيتم إعداد المشروع بدون GitHub حالياً.</b>\n<b>الاسم:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\n<b>الموديل:</b> <code>{html_escape(project_model)}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_new_project_resume_prompt_keyboard())
        elif data.startswith("cmd:new_proj_branch_pick:"):
            chosen_branch = data[len("cmd:new_proj_branch_pick:"):]
            state = get_user_state(chat_id)
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            repository = str(state.get("pending_github_repository") or "")
            detected_default = str(state.get("pending_github_default_branch") or "")
            branches = list(state.get("pending_github_branches") or [])
            if not project_key or not project_name or not repository:
                send_telegram_message(chat_id, "ℹ️ لا توجد بيانات GitHub قيد الإعداد حالياً. ابدأ من <b>مشروع جديد</b>.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION",
                    "pending_github_enabled": True,
                    "pending_github_branch": chosen_branch,
                    "pending_github_branch_mode": "manual",
                    "pending_github_default_branch": detected_default,
                    "pending_github_branches": branches,
                    "pending_github_repo_check_status": "checked",
                })
                send_telegram_message(chat_id, f"✅ <b>تم اختيار الفرع بنجاح:</b> <code>{html_escape(chosen_branch)}</code>\n<b>المستودع:</b> <code>{html_escape(repository)}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_new_project_resume_prompt_keyboard())
        elif data == "cmd:new_proj_branch_default":
            state = get_user_state(chat_id)
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            repository = str(state.get("pending_github_repository") or "")
            detected_default = str(state.get("pending_github_default_branch") or "")
            branches = list(state.get("pending_github_branches") or [])
            if not project_key or not project_name or not repository:
                send_telegram_message(chat_id, "ℹ️ لا توجد بيانات GitHub قيد الإعداد حالياً. ابدأ من <b>مشروع جديد</b>.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION",
                    "pending_github_enabled": True,
                    "pending_github_branch": "",
                    "pending_github_branch_mode": "auto_default",
                    "pending_github_default_branch": detected_default,
                    "pending_github_branches": branches,
                    "pending_github_repo_check_status": "checked",
                })
                send_telegram_message(chat_id, f"✅ <b>تم حفظ إعداد GitHub المبدئي.</b>\n<b>المستودع:</b> <code>{html_escape(repository)}</code>\n<b>الفرع:</b> <code>{html_escape(detected_default or 'auto-default')}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_new_project_resume_prompt_keyboard())
        elif data == "cmd:new_proj_branch_manual":
            state = get_user_state(chat_id)
            if not state.get("pending_github_repository"):
                send_telegram_message(chat_id, "ℹ️ لا توجد بيانات مستودع جاهزة. أرسل أولاً رابط المستودع ثم التوكن من Wizard المشروع الجديد.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_GITHUB_BRANCH",
                })
                send_telegram_message(chat_id, "✍️ <b>أدخل اسم الـbranch المطلوب لهذا المشروع</b>\nمثال: <code>main</code> أو <code>develop</code> أو أي branch موجود عندك.")
        elif data == "cmd:new_proj_resume_default":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION":
                send_telegram_message(chat_id, "ℹ️ أكمل Wizard المشروع الجديد أولاً حتى تصل لخطوة برومبت الاستئناف.")
            else:
                settings, next_state = finalize_new_project_from_state(state, chat_id=chat_id, resume_prompt=DEFAULT_PROJECT_RESUME_PROMPT)
                set_user_state(chat_id, next_state)
                send_telegram_message(chat_id, f"✅ <b>تم حفظ إعدادات المشروع.</b>\n<b>الاسم:</b> {html_escape(str(state.get('project_name') or ''))}\n<b>المفتاح:</b> <code>{html_escape(str(state.get('project_key') or ''))}</code>\n<b>الموديل:</b> <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n<b>برومبت الاستئناف:</b> <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>\nأرسل الآن أول برومبت لبدء المشروع.")
        elif data == "cmd:new_proj_resume_custom":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION":
                send_telegram_message(chat_id, "ℹ️ أكمل Wizard المشروع الجديد أولاً حتى تصل لخطوة برومبت الاستئناف.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT",
                })
                send_telegram_message(chat_id, "✍️ <b>أدخل برومبت الاستئناف الخاص بهذا المشروع</b>\nلو أحببت لاحقاً يمكن تعديله من إعدادات المشروع. القيمة الافتراضية هي <code>تابع</code>.")
        elif data == "cmd:current_project":
            current = get_latest_project_for_chat(chat_id)
            if not current:
                send_telegram_message(chat_id, "⭐ <b>لا يوجد مشروع حالي محفوظ بعد.</b>\nاستخدم زر <b>مشروع جديد</b> أو أرسل رابط مشروع معروف للاستكمال.", reply_markup=get_main_keyboard(chat_id))
            else:
                send_telegram_message(chat_id, render_project_status_text(current["project_key"]), reply_markup=build_current_project_keyboard(current["project_key"]))
        elif data == "cmd:list_projects":
            # 📄 [P27] فتح شاشة تصفح المشاريع (الصفحة الأولى) — إصلاح الزر الميت + Pagination
            send_telegram_message(
                chat_id,
                render_projects_page_text(chat_id, page=1),
                reply_markup=build_projects_page_keyboard(chat_id, page=1),
            )
        elif data.startswith("plist:page:"):
            # 📄 [P27] تقليب الصفحات In-Place: تعديل نفس الرسالة — صفر Spam في المحادثة
            page_token = data.split("plist:page:", 1)[1]
            list_msg_id = msg_info.get("message_id")
            page_text = render_projects_page_text(chat_id, page=page_token)
            page_keyboard = build_projects_page_keyboard(chat_id, page=page_token)
            if list_msg_id:
                edit_telegram_message_text(chat_id, list_msg_id, page_text, reply_markup=page_keyboard)
            else:
                send_telegram_message(chat_id, page_text, reply_markup=page_keyboard)
        elif data == "plist:noop":
            # 📄 [P27] زر العداد «📄 N / X» — عرض فقط، لا يفعل شيئاً عمداً
            pass
        elif data.startswith("pview:"):
            project_key = data.split("pview:", 1)[1]
            send_telegram_message(chat_id, render_project_status_text(project_key), reply_markup=build_current_project_keyboard(project_key))
        elif data.startswith("pset:"):
            parts = data.split(":")
            action = parts[1] if len(parts) > 1 else ""
            project_key = re.sub(r"[^A-Za-z0-9_-]", "_", str(parts[2] if len(parts) > 2 else ""))[:80]
            identity = get_project_identity_record(project_key) or {}
            project_name = str(identity.get("project_name") or project_key)
            registry = ProjectRegistry(project_key)
            settings = registry.get_project_settings()
            github = settings.get("github", {})
            if action == "branch_pick":
                branch_name = ":".join(parts[3:]) if len(parts) > 3 else ""
                if not branch_name:
                    send_telegram_message(chat_id, "⚠️ لم يتم تحديد اسم الفرع بشكل صحيح.")
                else:
                    updated = update_existing_project_github_settings(project_key, branch=branch_name, branch_mode="manual", repo_check_status="checked")
                    set_user_state(chat_id, {})
                    send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم حفظ وتحديث GitHub branch للمشروع.</b>\n<b>الفرع المستخدم:</b> <code>{html_escape(branch_name)}</code>")
            if action == "view":
                set_user_state(chat_id, {})
                send_project_settings_panel(chat_id, project_key)
            elif action == "model":
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_MODEL",
                    "project_key": project_key,
                    "project_name": project_name,
                })
                send_telegram_message(chat_id, f"🧠 <b>تعديل موديل المشروع</b>\n<b>المشروع:</b> {html_escape(project_name)}\nاختر الموديل الجديد لهذا المشروع.", reply_markup=build_new_project_model_keyboard(back_callback=f"pset:view:{project_key}", back_label="⬅️ رجوع لإعدادات المشروع"))
            elif action == "resume":
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_RESUME_PROMPT",
                    "project_key": project_key,
                    "project_name": project_name,
                })
                send_telegram_message(chat_id, f"✍️ <b>تعديل برومبت الاستئناف</b>\n<b>المشروع:</b> {html_escape(project_name)}\nأرسل البرومبت الجديد الآن. القيمة الحالية هي <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>.")
            elif action == "repo":
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_GITHUB_REPO",
                    "project_key": project_key,
                    "project_name": project_name,
                    "settings_edit_scope": "repo_update",
                    "pending_github_enabled": bool(github.get("enabled")),
                })
                current_repo = str(github.get("repository") or "")
                current_repo_line = f"\n<b>المستودع الحالي:</b> <code>{html_escape(current_repo)}</code>" if current_repo else ""
                send_telegram_message(chat_id, f"🔗 <b>تعديل مستودع GitHub للمشروع</b>\n<b>المشروع:</b> {html_escape(project_name)}{current_repo_line}\nأرسل رابط المستودع الجديد أو الصيغة <code>owner/repo</code>.")
            elif action == "token":
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_GITHUB_TOKEN",
                    "project_key": project_key,
                    "project_name": project_name,
                    "settings_edit_scope": "token_update",
                    "pending_github_enabled": bool(github.get("enabled")),
                    "pending_github_repository": str(github.get("repository") or ""),
                })
                send_telegram_message(chat_id, f"🔑 <b>تحديث GitHub token للمشروع</b>\n<b>المشروع:</b> {html_escape(project_name)}\nأرسل token جديداً لهذا المشروع. لن أعرض قيمته في الرسائل.")
            elif action == "branch":
                repository = str(github.get("repository") or "").strip()
                if not repository:
                    send_telegram_message(chat_id, "⚠️ لا يوجد مستودع محفوظ لهذا المشروع بعد. استخدم زر <b>تعديل المستودع</b> أولاً.", reply_markup=build_project_settings_keyboard(project_key))
                else:
                    project_token = registry.get_project_github_token(allow_env_fallback=False)
                    if not project_token:
                        set_user_state(chat_id, {
                            "action": "AWAITING_PROJECT_SETTINGS_GITHUB_TOKEN",
                            "project_key": project_key,
                            "project_name": project_name,
                            "settings_edit_scope": "branch_update",
                            "pending_github_enabled": bool(github.get("enabled")),
                            "pending_github_repository": repository,
                        })
                        send_telegram_message(chat_id, f"🔑 <b>نحتاج GitHub token للمشروع قبل فحص الـbranch</b>\n<b>المشروع:</b> {html_escape(project_name)}\nأرسل token المشروع حتى أتحقق من الـdefault branch ثم أسمح لك بالتأكيد أو التعديل اليدوي.")
                    else:
                        inspection = inspect_github_repository(repository, token=project_token)
                        if inspection.get("ok"):
                            raw_branches = inspection.get("branches") or []
                            default_branch = inspection.get("default_branch") or (raw_branches[0] if raw_branches else "")
                            set_user_state(chat_id, {
                                "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH_DECISION",
                                "project_key": project_key,
                                "project_name": project_name,
                                "settings_edit_scope": "branch_update",
                                "pending_github_enabled": bool(github.get("enabled")),
                                "pending_github_repository": repository,
                                "pending_github_default_branch": default_branch,
                                "pending_github_branches": raw_branches,
                                "pending_github_repo_check_status": "checked",
                            })
                            summary_msg = format_github_repo_inspection_summary(repository, default_branch, raw_branches)
                            send_telegram_message(chat_id, summary_msg, reply_markup=build_existing_project_branch_choice_keyboard(project_key, branches=raw_branches, default_branch=default_branch))
                        else:
                            set_user_state(chat_id, {
                                "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH",
                                "project_key": project_key,
                                "project_name": project_name,
                                "settings_edit_scope": "branch_update",
                                "pending_github_enabled": bool(github.get("enabled")),
                                "pending_github_repository": repository,
                                "pending_github_default_branch": str(github.get("detected_default_branch") or ""),
                                "pending_github_branches": list(github.get("available_branches") or []),
                                "pending_github_repo_check_status": "manual-branch",
                            })
                            send_telegram_message(chat_id, f"⚠️ <b>تعذر فحص المستودع الآن:</b> {html_escape(inspection.get('reason') or 'سبب غير معروف')}\nأدخل branch يدويًا لهذا المشروع مثل <code>main</code> أو <code>develop</code>.")
            elif action == "branch_default":
                state = get_user_state(chat_id)
                if state.get("action") != "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH_DECISION" or str(state.get("project_key") or "") != project_key:
                    send_telegram_message(chat_id, "ℹ️ افتح أولاً خطوة تعديل الـbranch من إعدادات المشروع ثم اختر طريقة الحفظ.")
                else:
                    updated = finalize_existing_project_github_from_state(state, branch="", branch_mode="auto_default", repo_check_status="checked")
                    set_user_state(chat_id, {})
                    send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم تحديث GitHub branch للمشروع.</b>\n<b>الفرع المستخدم:</b> <code>{html_escape(updated.get('github', {}).get('detected_default_branch') or state.get('pending_github_default_branch') or 'auto-default')}</code>")
            elif action == "branch_manual":
                state = get_user_state(chat_id)
                if state.get("action") != "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH_DECISION" or str(state.get("project_key") or "") != project_key:
                    send_telegram_message(chat_id, "ℹ️ افتح أولاً خطوة تعديل الـbranch من إعدادات المشروع ثم اختر branch يدوي إذا أردت.")
                else:
                    set_user_state(chat_id, {
                        **state,
                        "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH",
                    })
                    send_telegram_message(chat_id, "✍️ <b>أدخل اسم الـbranch المطلوب لهذا المشروع</b>\nمثال: <code>main</code> أو <code>develop</code> أو أي branch موجود عندك.")
            elif action == "toggle":
                currently_enabled = bool(github.get("enabled"))
                if currently_enabled:
                    update_existing_project_github_settings(project_key, enabled=False, repo_check_status="disabled-by-user")
                    set_user_state(chat_id, {})
                    send_project_settings_panel(chat_id, project_key, prefix="✅ <b>تم تعطيل GitHub لهذا المشروع مع الاحتفاظ بالإعدادات المحفوظة.</b>")
                else:
                    repository = str(github.get("repository") or "").strip()
                    if not repository:
                        send_telegram_message(chat_id, "⚠️ لا يمكن تفعيل GitHub قبل حفظ المستودع لهذا المشروع. استخدم زر <b>تعديل المستودع</b> أولاً.", reply_markup=build_project_settings_keyboard(project_key))
                    else:
                        update_existing_project_github_settings(project_key, enabled=True, repo_check_status="enabled-by-user")
                        warning = ""
                        if not github.get("token_present"):
                            warning = "\n⚠️ <b>ملاحظة:</b> لا يوجد token محفوظ للمشروع حالياً؛ أضفه إذا كان المستودع خاصاً أو يحتاج صلاحيات كتابة."
                        set_user_state(chat_id, {})
                        send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم تفعيل GitHub لهذا المشروع بالإعدادات المحفوظة.</b>{warning}")
            else:
                send_telegram_message(chat_id, "ℹ️ أمر إعدادات مشروع غير معروف.")
        elif data.startswith("pctl:"):
            _, action, project_key = data.split(":", 2)
            renderers = {
                "checkpoints": render_project_checkpoints_text,
                "archive": render_project_archive_text,
                "files": render_project_file_report_text,
                "history": render_project_history_text,
                "gh": render_project_github_status_text,
            }
            if action in renderers:
                send_telegram_message(chat_id, renderers[action](project_key), reply_markup=build_current_project_keyboard(project_key))
            else:
                send_telegram_message(chat_id, run_project_upload_control(project_key, action), reply_markup=build_current_project_keyboard(project_key))
        elif data == "cmd:resume_continue":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_PROJECT_RESUME_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً ملخص الاستئناف للمشروع ثم اختر هل تريد المتابعة الآن.")
            else:
                project_key = str(state.get("project_key") or "")
                project_name = str(state.get("project_name") or "")
                project_model = normalize_project_model(state.get("project_model") or get_project_selected_model(project_key))
                target_url = str(state.get("url") or "")
                if target_url:
                    set_user_state(chat_id, {
                        "action": "AWAITING_CONT_PROMPT",
                        "url": target_url,
                        "project_key": project_key,
                        "project_name": project_name,
                        "project_model": project_model,
                    })
                    send_telegram_message(chat_id, f"✅ <b>جاهز لاستئناف المشروع.</b>\n<b>الاسم:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\n<b>الموديل:</b> <code>{html_escape(project_model)}</code>\nأرسل الآن التعديل أو البرومبت الجديد، وسيُستخدم السياق المحفوظ لهذا المشروع.")
                else:
                    set_user_state(chat_id, {
                        "action": "AWAITING_NEW_PROMPT",
                        "project_key": project_key,
                        "project_name": project_name,
                        "project_model": project_model,
                    })
                    send_telegram_message(chat_id, f"🆕 <b>هذا المشروع لا يملك رابط استئناف محفوظاً بعد.</b>\n<b>الاسم:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\n<b>الموديل:</b> <code>{html_escape(project_model)}</code>\nأرسل أول prompt الآن ليبدأ بنفس المفتاح والإعدادات المحفوظة.")
        elif data == "cmd:resume_settings":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_PROJECT_RESUME_DECISION" or not state.get("project_key"):
                send_telegram_message(chat_id, "ℹ️ افتح أولاً ملخص الاستئناف لمشروع محفوظ إذا أردت تعديل إعداداته قبل المتابعة.")
            else:
                send_project_settings_panel(chat_id, str(state.get("project_key") or ""), prefix="⚙️ <b>يمكنك تعديل إعدادات المشروع قبل المتابعة.</b>")
        elif data == "cmd:resume_quick_continue":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_UNBOUND_RESUME_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً رابط/Project ID غير محفوظ حتى تختار بين الحفظ أو الاستئناف السريع.")
            else:
                target_url = str(state.get("url") or "")
                pid_value = str(state.get("pid") or extract_project_id(target_url) or "")
                set_user_state(chat_id, {
                    "action": "AWAITING_CONT_PROMPT",
                    "url": target_url,
                    "project_key": "",
                    "project_name": "",
                    "project_model": DEFAULT_PROJECT_MODEL,
                    "pid": pid_value,
                })
                send_telegram_message(chat_id, f"⚡ <b>استئناف سريع بدون حفظ</b>\n<b>Project ID:</b> <code>{html_escape(pid_value)}</code>\nأرسل الآن التعديل أو البرومبت الذي تريد تنفيذه على هذا المشروع.")
        elif data == "cmd:resume_bind_saved":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_UNBOUND_RESUME_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً رابط/Project ID غير محفوظ حتى تبدأ ربطه كمشروع محفوظ.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_NAME",
                })
                send_telegram_message(chat_id, "📌 <b>ربط مشروع خارجي كمشروع محفوظ</b>\nاكتب اسماً واضحاً لهذا المشروع حتى يظهر لاحقاً في قائمة المشاريع.")
        elif data == "cmd:resume_copy_settings":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_UNBOUND_RESUME_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً رابط/Project ID غير محفوظ حتى تنسخ له إعدادات مشروع آخر.")
            elif not list_known_projects(chat_id=chat_id, limit=1):
                send_telegram_message(chat_id, "ℹ️ <b>لا توجد مشاريع محفوظة بعد لنسخ إعداداتها.</b>\nأنشئ مشروعاً محفوظاً أولاً ثم استخدم هذا الزر.", reply_markup=build_unbound_resume_keyboard())
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_COPY_SETTINGS_SOURCE",
                })
                send_telegram_message(chat_id, "📋 <b>نسخ إعدادات من مشروع آخر</b>\nاختر المشروع المصدر — سيتم نسخ إعدادات GitHub والموديل وبرومبت الاستئناف لمشروع جديد باسم تسلسلي تلقائي.", reply_markup=build_copy_settings_source_keyboard(chat_id))
        elif data == "cmd:resume_copy_back":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_COPY_SETTINGS_SOURCE":
                send_telegram_message(chat_id, "ℹ️ لا توجد عملية نسخ إعدادات جارية.")
            else:
                target_url = str(state.get("url") or "")
                pid_value = str(state.get("pid") or "")
                present_external_resume_decision(chat_id, target_url=target_url, target_pid=pid_value)
        elif data.startswith("cpysrc:"):
            source_key = data[len("cpysrc:"):]
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_COPY_SETTINGS_SOURCE":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً شاشة نسخ الإعدادات من زر «📋 نسخ إعدادات من مشروع آخر».")
            else:
                target_url = str(state.get("url") or "")
                pid_value = str(state.get("pid") or extract_project_id(target_url) or "")
                result = copy_project_settings_to_new_project(source_key, chat_id, target_url=target_url, target_pid=pid_value)
                if not result.get("ok"):
                    send_telegram_message(chat_id, f"⚠️ <b>تعذر نسخ الإعدادات:</b> {html_escape(str(result.get('reason') or 'سبب غير معروف'))}")
                else:
                    set_user_state(chat_id, {
                        "action": "AWAITING_CONT_PROMPT",
                        "url": target_url,
                        "project_key": str(result.get("project_key") or ""),
                        "project_name": str(result.get("project_name") or ""),
                        "project_model": normalize_project_model((result.get("settings") or {}).get("model")),
                        "pid": pid_value,
                    })
                    send_telegram_message(chat_id, format_copied_settings_summary(result))
        elif data == "cmd:bound_proj_github_yes":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_BOUND_PROJECT_GITHUB_MODE":
                send_telegram_message(chat_id, "ℹ️ ابدأ أولاً ربط المشروع الخارجي ثم اختر الموديل قبل إعداد GitHub.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_GITHUB_REPO",
                })
                send_telegram_message(chat_id, "🔗 <b>ربط GitHub للمشروع الخارجي</b>\nأرسل رابط المستودع أو الصيغة <code>owner/repo</code> أولاً.")
        elif data in {"cmd:bound_proj_github_no", "cmd:bound_proj_github_disable"}:
            state = get_user_state(chat_id)
            if state.get("action") not in {"AWAITING_BOUND_PROJECT_GITHUB_MODE", "AWAITING_BOUND_PROJECT_GITHUB_BRANCH_DECISION"}:
                send_telegram_message(chat_id, "ℹ️ ابدأ أولاً ربط المشروع الخارجي ثم اختر الموديل قبل تحديد وضع GitHub.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION",
                    "pending_github_enabled": False,
                    "pending_github_repository": "",
                    "pending_github_token": "",
                    "pending_github_branch": "",
                    "pending_github_branch_mode": "disabled",
                    "pending_github_default_branch": "",
                    "pending_github_branches": [],
                    "pending_github_repo_check_status": "disabled",
                })
                send_telegram_message(chat_id, "✅ <b>سيتم ربط المشروع الخارجي بدون GitHub حالياً.</b>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_bound_project_resume_prompt_keyboard())
        elif data.startswith("cmd:bound_proj_branch_pick:"):
            chosen_branch = data[len("cmd:bound_proj_branch_pick:"):]
            state = get_user_state(chat_id)
            detected_default = str(state.get("pending_github_default_branch") or "")
            branches = list(state.get("pending_github_branches") or [])
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION",
                "pending_github_enabled": True,
                "pending_github_branch": chosen_branch,
                "pending_github_branch_mode": "manual",
                "pending_github_default_branch": detected_default,
                "pending_github_branches": branches,
                "pending_github_repo_check_status": "checked",
            })
            send_telegram_message(chat_id, f"✅ <b>تم اختيار الفرع بنجاح:</b> <code>{html_escape(chosen_branch)}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_bound_project_resume_prompt_keyboard())
        elif data == "cmd:bound_proj_branch_default":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_BOUND_PROJECT_GITHUB_BRANCH_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً خطوة فحص GitHub للمشروع الخارجي ثم اختر طريقة الفرع.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION",
                    "pending_github_enabled": True,
                    "pending_github_branch": "",
                    "pending_github_branch_mode": "auto_default",
                    "pending_github_repo_check_status": "checked",
                })
                send_telegram_message(chat_id, "✅ <b>تم حفظ إعداد GitHub المبدئي للمشروع الخارجي.</b>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_bound_project_resume_prompt_keyboard())
        elif data == "cmd:bound_proj_branch_manual":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_BOUND_PROJECT_GITHUB_BRANCH_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً خطوة فحص GitHub للمشروع الخارجي ثم اختر branch يدوي إذا أردت.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_GITHUB_BRANCH",
                })
                send_telegram_message(chat_id, "✍️ <b>أدخل اسم الـbranch المطلوب لهذا المشروع الخارجي</b>\nمثال: <code>main</code> أو <code>develop</code>.")
        elif data == "cmd:bound_proj_resume_default":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION":
                send_telegram_message(chat_id, "ℹ️ أكمل أولاً ربط المشروع الخارجي حتى تصل لخطوة برومبت الاستئناف.")
            else:
                settings, next_state = finalize_bound_external_project_from_state(state, chat_id=chat_id, resume_prompt=DEFAULT_PROJECT_RESUME_PROMPT)
                set_user_state(chat_id, next_state)
                send_telegram_message(chat_id, f"✅ <b>تم ربط المشروع الخارجي كمشروع محفوظ.</b>\n<b>الاسم:</b> {html_escape(str(state.get('project_name') or ''))}\n<b>المفتاح:</b> <code>{html_escape(str(state.get('project_key') or ''))}</code>\n<b>الموديل:</b> <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n<b>برومبت الاستئناف:</b> <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>\nأرسل الآن التعديل أو البرومبت المطلوب على هذا المشروع الخارجي.")
        elif data == "cmd:bound_proj_resume_custom":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION":
                send_telegram_message(chat_id, "ℹ️ أكمل أولاً ربط المشروع الخارجي حتى تصل لخطوة برومبت الاستئناف.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_RESUME_PROMPT",
                })
                send_telegram_message(chat_id, "✍️ <b>أدخل برومبت الاستئناف الخاص بهذا المشروع الخارجي</b>\nالقيمة الافتراضية هي <code>تابع</code> ويمكن تعديلها لاحقاً من إعدادات المشروع.")
        elif data == "cmd:cont_proj":
            set_user_state(chat_id, {"action": "AWAITING_CONT_URL"})
            send_telegram_message(chat_id, "🔄 <b>استئناف مشروع حالي:</b>\nأرسل رابط المشروع (URL) أو الـ Project ID لاستئناف الشغل عليه!")
        elif data.startswith("proj:"):
            project_key = data.split("proj:", 1)[1]
            if not start_project_resume_from_key(chat_id, project_key):
                send_telegram_message(chat_id, "⚠️ تعذر فتح هذا المشروع من الـRegistry الحالية.")
        elif data.startswith("cont:"):
            pid = data.split("cont:")[1]
            ctx = resolve_resume_context(pid)
            if ctx["project_key"]:
                present_resume_summary(chat_id, project_key=ctx["project_key"], target_url=ctx["target_url"], target_pid=ctx["pid"])
            else:
                present_external_resume_decision(chat_id, target_url=ctx["target_url"], target_pid=ctx["pid"])
        elif data.startswith("tree:") or data == "cmd:list_tree":
            pid = data.split("tree:")[1] if "tree:" in data else None
            if not pid:
                current = get_latest_project_for_chat(chat_id)
                current_pid = str(current.get("latest_genspark_pid") or current.get("root_genspark_pid") or "") if current else ""
                pid = current_pid
            if not pid:
                send_telegram_message(chat_id, "🌳 أرسل رابط المشروع أولاً أو اختر المشروع الحالي لعرض شجرة التفريعات الخاصة به.")
            else:
                branches = get_project_branches(pid)
                if not branches:
                    send_telegram_message(chat_id, f"ℹ️ لا توجد تفريعات سابقة للمشروع <code>{html_escape(pid[:8])}...</code>")
                else:
                    b_buttons = []
                    for b in branches[:6]:
                        b_pid = b.get("project_id")
                        b_title = html_escape(b.get("title", "فرع"))[:20]
                        b_buttons.append([{"text": f"📍 {b_title} ({str(b_pid)[:6]}...)", "callback_data": f"cont:{b_pid}"}])
                    send_telegram_message(chat_id, f"🌳 <b>نقاط الاستئناف المتاحة للمشروع <code>{html_escape(pid[:8])}...</code>:</b>", reply_markup=make_inline_keyboard(b_buttons))
        elif data == "cmd:account_pwd_lookup":
            # 🔐 [P32] فتح الشاشة الهجينة: تعيين الحالة التفاعلية (يفتح المسار اليدوي)
            # وعرض الصفحة الأولى من قائمة الحسابات في نفس اللحظة.
            set_user_state(chat_id, {"action": AWAITING_ACCOUNT_PASSWORD_LOOKUP, "page": 1})
            send_telegram_message(
                chat_id,
                render_account_lookup_text(page=1),
                reply_markup=build_account_lookup_keyboard(page=1),
            )
        elif data.startswith("acc_page:"):
            page_token = data.split("acc_page:", 1)[1]
            if page_token == "noop":
                # 🔐 [P32] زر العداد «📄 N / X» — عرض فقط، لا يفعل شيئاً عمداً
                pass
            else:
                # 🔐 [P32] تقليب الصفحات In-Place (نفس نمط P27) — صفر Spam في المحادثة.
                # الحالة التفاعلية تبقى قائمة ليظل المسار اليدوي متاحاً أثناء التصفح.
                safe_page, _total_pages, _start = compute_accounts_page_bounds(
                    len(list_lookup_accounts()), page_token
                )
                set_user_state(chat_id, {"action": AWAITING_ACCOUNT_PASSWORD_LOOKUP, "page": safe_page})
                page_text = render_account_lookup_text(page=safe_page)
                page_keyboard = build_account_lookup_keyboard(page=safe_page)
                lookup_msg_id = msg_info.get("message_id")
                if lookup_msg_id:
                    edit_telegram_message_text(chat_id, lookup_msg_id, page_text, reply_markup=page_keyboard)
                else:
                    send_telegram_message(chat_id, page_text, reply_markup=page_keyboard)
        elif data.startswith("acc_view:"):
            # 🔐 [P32] ضغط زر إيميل من القائمة: الفهرس المطلق داخل القائمة المرتبة.
            # أي فهرس تالف/خارج المدى يُرفض بهدوء بلا Crash.
            index_token = data.split("acc_view:", 1)[1]
            accounts = list_lookup_accounts()
            try:
                acc_index = int(index_token)
            except (TypeError, ValueError):
                acc_index = -1
            if 0 <= acc_index < len(accounts):
                set_user_state(chat_id, {})
                send_telegram_message(
                    chat_id,
                    render_account_password_card(accounts[acc_index]),
                    reply_markup=build_account_password_card_keyboard(),
                )
            else:
                send_telegram_message(
                    chat_id,
                    "⚠️ <b>تعذر عرض هذا الحساب</b> — تغيّرت قائمة الحسابات. افتح الشاشة من جديد.",
                    reply_markup=build_account_lookup_retry_keyboard(),
                )
        elif data == "acc_cancel":
            # 🔐 [P32] إلغاء حتمي: تصفير الحالة التفاعلية والعودة للوحة التحكم
            set_user_state(chat_id, {})
            send_telegram_message(
                chat_id,
                "↩️ <b>تم إلغاء استخراج الباسورد.</b>\n" + render_dashboard_text(chat_id),
                reply_markup=get_main_keyboard(chat_id),
            )
        return

    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()
        # [P17] مسار message: نحكم بالجروب أو بهوية المُرسِل نفسه (msg.from)
        if not is_chat_allowed(chat_id, (msg.get("from") or {}).get("id")):
            return

        # 📄 [P28] Document Ingestion: ملف .txt/.md يتحول لمحتوى نصي يغذي
        # نفس مسار text أدناه (كل حالات الـ Wizard + المسار الافتراضي) بلا تكرار.
        # رسائل الـ Document لا تحمل text أصلاً — الشرط يضمن Zero Regression للنصوص العادية.
        document = msg.get("document") or {}
        if document and not text:
            doc_name = str(document.get("file_name") or "")
            doc_ext = pathlib.Path(doc_name).suffix.lower()
            if doc_ext not in ALLOWED_DOCUMENT_EXTENSIONS:
                send_telegram_message(
                    chat_id,
                    "⚠️ <b>نوع الملف غير مدعوم.</b>\n"
                    f"المدعوم حالياً: <code>.txt</code> و <code>.md</code> فقط — "
                    f"استلمت: <code>{html_escape(doc_name or 'ملف بلا اسم')}</code>"
                )
                return
            doc_size = int(document.get("file_size") or 0)
            if doc_size > MAX_DOCUMENT_SIZE_BYTES:
                send_telegram_message(
                    chat_id,
                    "⚠️ <b>الملف أكبر من الحد المسموح (5 MB).</b>\n"
                    f"حجم الملف: <code>{doc_size / (1024 * 1024):.1f} MB</code> — "
                    "قسّمه أو اختصر محتواه ثم أعد الإرسال."
                )
                return
            doc_content = download_telegram_document_text(document.get("file_id") or "")
            if doc_content is None or not doc_content.strip():
                send_telegram_message(
                    chat_id,
                    "❌ <b>تعذر قراءة محتوى الملف.</b>\n"
                    "تأكد أنه ملف نصي سليم غير فارغ ثم أعد المحاولة."
                )
                return
            caption = str(msg.get("caption") or "").strip()
            text = f"{caption}\n\n{doc_content}".strip() if caption else doc_content.strip()
            log_event("info", f"📄 [P28] تم استيعاب ملف مهمة [{doc_name}] ({doc_size} بايت) من Chat {chat_id}")

        if text in ["/start", "/help"]:
            send_telegram_message(chat_id, render_dashboard_text(chat_id), reply_markup=get_main_keyboard(chat_id))
            return

        state = get_user_state(chat_id)
        action = state.get("action")

        # 🔐 [P32] المسار اليدوي لاستخراج الباسورد — أول فحص في سلسلة الحالات:
        # الإيميل نص عادي، ولو تُرك للمسار الافتراضي لأسفل لكان أُرسل كبرومبت مهمة.
        # كتلة مستقلة تماماً ← صفر تأثير على أي حالة Wizard أخرى.
        if action == AWAITING_ACCOUNT_PASSWORD_LOOKUP:
            requested_email = str(text or "").strip().lower()
            matched = find_account_by_email(requested_email)
            if matched:
                set_user_state(chat_id, {})
                send_telegram_message(
                    chat_id,
                    render_account_password_card(matched),
                    reply_markup=build_account_password_card_keyboard(),
                )
            else:
                # الحالة تبقى قائمة: المالك يعيد الكتابة فوراً بلا إعادة فتح الشاشة
                send_telegram_message(
                    chat_id,
                    "❌ <b>الحساب غير مسجل في قاعدة الحسابات.</b>\n"
                    f"البريد المطلوب: <code>{html_escape(requested_email or 'بلا إيميل')}</code>\n"
                    "تأكد من كتابته بشكل صحيح وأعد الإرسال، أو ارجع للوحة التحكم.",
                    reply_markup=build_account_lookup_retry_keyboard(),
                )
            return

        if action == "AWAITING_NEW_PROJECT_NAME":
            project_name = re.sub(r"\s+", " ", text).strip()[:60] or "مشروع بدون اسم"
            project_key = f"prj_{uuid.uuid4().hex[:16]}"
            set_user_state(chat_id, {
                "action": "AWAITING_NEW_PROJECT_MODEL",
                "project_key": project_key,
                "project_name": project_name,
            })
            send_telegram_message(chat_id, f"✅ <b>اسم المشروع:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\nاختر الآن الموديل المطلوب لهذا المشروع.", reply_markup=build_new_project_model_keyboard())
            return

        if action == "AWAITING_NEW_PROJECT_GITHUB_REPO":
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            project_model = normalize_project_model(state.get("project_model"))
            repository = parse_github_repository_ref(text)
            if not repository:
                send_telegram_message(chat_id, "⚠️ صيغة المستودع غير واضحة. أرسل رابط GitHub كامل أو الصيغة <code>owner/repo</code>.")
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_NEW_PROJECT_GITHUB_TOKEN",
                "project_key": project_key,
                "project_name": project_name,
                "project_model": project_model,
                "pending_github_repository": repository,
            })
            send_telegram_message(chat_id, f"✅ <b>المستودع:</b> <code>{html_escape(repository)}</code>\nأرسل الآن <b>GitHub token</b> الخاص بهذا المشروع حتى أتمكن من فحص المستودع والفروع، خصوصاً إذا كان المستودع خاصاً.")
            return

        if action == "AWAITING_NEW_PROJECT_GITHUB_TOKEN":
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            project_model = normalize_project_model(state.get("project_model"))
            repository = str(state.get("pending_github_repository") or "")
            token_value = str(text or "").strip()
            if not token_value:
                send_telegram_message(chat_id, "⚠️ أدخل GitHub token صالحاً لهذا المشروع أو استخدم زر المتابعة بدون GitHub.")
                return
            inspection = inspect_github_repository(repository, token=token_value)
            if inspection.get("ok"):
                raw_branches = inspection.get("branches") or []
                default_branch = inspection.get("default_branch") or (raw_branches[0] if raw_branches else "")
                set_user_state(chat_id, {
                    "action": "AWAITING_NEW_PROJECT_GITHUB_BRANCH_DECISION",
                    "project_key": project_key,
                    "project_name": project_name,
                    "project_model": project_model,
                    "pending_github_enabled": True,
                    "pending_github_repository": repository,
                    "pending_github_token": token_value,
                    "pending_github_default_branch": default_branch,
                    "pending_github_branches": raw_branches,
                    "pending_github_repo_check_status": "checked",
                })
                summary_msg = format_github_repo_inspection_summary(repository, default_branch, raw_branches)
                send_telegram_message(chat_id, summary_msg, reply_markup=build_new_project_branch_choice_keyboard(branches=raw_branches, default_branch=default_branch))
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_NEW_PROJECT_GITHUB_TOKEN",
                "pending_github_repository": repository,
                "pending_github_token": "",
            })
            send_telegram_message(chat_id, f"⚠️ <b>تعذر فحص المستودع الآن:</b> {html_escape(inspection.get('reason') or 'سبب غير معروف')}\nأعد إدخال token صالح لهذا المشروع، أو استخدم زر <b>المتابعة بدون GitHub</b> إذا أردت التخطي.")
            return

        if action == "AWAITING_NEW_PROJECT_GITHUB_BRANCH":
            repository = str(state.get("pending_github_repository") or "")
            branch = re.sub(r"\s+", "", text).strip()
            if not branch:
                send_telegram_message(chat_id, "⚠️ اكتب اسم branch صالح مثل <code>main</code> أو <code>develop</code>.")
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION",
                "pending_github_enabled": True,
                "pending_github_branch": branch,
                "pending_github_branch_mode": "manual",
                "pending_github_repo_check_status": "manual-branch",
            })
            send_telegram_message(chat_id, f"✅ <b>تم حفظ إعداد GitHub اليدوي.</b>\n<b>المستودع:</b> <code>{html_escape(repository)}</code>\n<b>الفرع:</b> <code>{html_escape(branch)}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_new_project_resume_prompt_keyboard())
            return

        if action == "AWAITING_NEW_PROJECT_RESUME_PROMPT":
            settings, next_state = finalize_new_project_from_state(state, chat_id=chat_id, resume_prompt=text)
            set_user_state(chat_id, next_state)
            send_telegram_message(chat_id, f"✅ <b>تم حفظ إعدادات المشروع.</b>\n<b>الاسم:</b> {html_escape(str(state.get('project_name') or ''))}\n<b>المفتاح:</b> <code>{html_escape(str(state.get('project_key') or ''))}</code>\n<b>الموديل:</b> <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n<b>برومبت الاستئناف:</b> <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>\nأرسل الآن أول برومبت لبدء المشروع.")
            return

        if action == "AWAITING_PROJECT_SETTINGS_RESUME_PROMPT":
            project_key = str(state.get("project_key") or "")
            if not project_key:
                send_telegram_message(chat_id, "⚠️ لا يوجد مشروع صالح لتعديل برومبت الاستئناف حالياً.")
                return
            ProjectRegistry(project_key).set_project_resume_prompt(text)
            set_user_state(chat_id, {})
            send_project_settings_panel(chat_id, project_key, prefix="✅ <b>تم تحديث برومبت الاستئناف للمشروع.</b>")
            return

        if action == "AWAITING_PROJECT_SETTINGS_GITHUB_REPO":
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            repository = parse_github_repository_ref(text)
            if not repository:
                send_telegram_message(chat_id, "⚠️ صيغة المستودع غير واضحة. أرسل رابط GitHub كامل أو الصيغة <code>owner/repo</code>.")
                return
            registry = ProjectRegistry(project_key)
            current_github = registry.get_project_settings().get("github", {})
            project_token = registry.get_project_github_token(allow_env_fallback=False)
            if not project_token:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_PROJECT_SETTINGS_GITHUB_TOKEN",
                    "settings_edit_scope": "repo_update",
                    "pending_github_repository": repository,
                })
                send_telegram_message(chat_id, f"✅ <b>المستودع الجديد:</b> <code>{html_escape(repository)}</code>\nأرسل الآن <b>GitHub token</b> الخاص بهذا المشروع حتى أتمكن من فحص الـdefault branch والفروع المتاحة.")
                return
            inspection = inspect_github_repository(repository, token=project_token)
            if inspection.get("ok"):
                raw_branches = inspection.get("branches") or []
                default_branch = inspection.get("default_branch") or (raw_branches[0] if raw_branches else "")
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH_DECISION",
                    "project_key": project_key,
                    "project_name": project_name,
                    "settings_edit_scope": "repo_update",
                    "pending_github_enabled": bool(state.get("pending_github_enabled", current_github.get("enabled"))),
                    "pending_github_repository": repository,
                    "pending_github_default_branch": default_branch,
                    "pending_github_branches": raw_branches,
                    "pending_github_repo_check_status": "checked",
                })
                summary_msg = format_github_repo_inspection_summary(repository, default_branch, raw_branches)
                send_telegram_message(chat_id, summary_msg, reply_markup=build_existing_project_branch_choice_keyboard(project_key, branches=raw_branches, default_branch=default_branch))
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_PROJECT_SETTINGS_GITHUB_TOKEN",
                "settings_edit_scope": "repo_update",
                "pending_github_repository": repository,
            })
            send_telegram_message(chat_id, f"⚠️ <b>تعذر فحص المستودع بالتوكن المحفوظ حالياً:</b> {html_escape(inspection.get('reason') or 'سبب غير معروف')}\nأرسل token محدثاً لهذا المشروع، أو بعد ذلك سنسمح لك بإدخال branch يدوي إذا لزم الأمر.")
            return

        if action == "AWAITING_PROJECT_SETTINGS_GITHUB_TOKEN":
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            registry = ProjectRegistry(project_key)
            current_github = registry.get_project_settings().get("github", {})
            repository = parse_github_repository_ref(state.get("pending_github_repository") or current_github.get("repository") or "")
            token_value = str(text or "").strip()
            scope = str(state.get("settings_edit_scope") or "token_update")
            if not token_value:
                send_telegram_message(chat_id, "⚠️ أدخل GitHub token صالحاً لهذا المشروع.")
                return
            if scope == "token_update" and not repository:
                update_existing_project_github_settings(project_key, token=token_value, repo_check_status="token-updated")
                set_user_state(chat_id, {})
                send_project_settings_panel(chat_id, project_key, prefix="✅ <b>تم تحديث GitHub token للمشروع.</b>")
                return
            inspection = inspect_github_repository(repository, token=token_value) if repository else {"ok": False, "reason": "لا يوجد repo محفوظ بعد."}
            if scope == "token_update":
                if repository and inspection.get("ok"):
                    default_branch = inspection.get("default_branch") or ((inspection.get("branches") or [""])[0])
                    update_existing_project_github_settings(
                        project_key,
                        enabled=bool(state.get("pending_github_enabled", current_github.get("enabled"))),
                        repository=repository,
                        detected_default_branch=default_branch,
                        available_branches=inspection.get("branches") or [],
                        repo_check_status="checked",
                        token=token_value,
                    )
                    set_user_state(chat_id, {})
                    send_project_settings_panel(chat_id, project_key, prefix="✅ <b>تم تحديث GitHub token للمشروع وفحص المستودع الحالي بنجاح.</b>")
                else:
                    update_existing_project_github_settings(project_key, token=token_value, repo_check_status="token-updated")
                    set_user_state(chat_id, {})
                    warning = ""
                    if repository and not inspection.get("ok"):
                        warning = f"\n⚠️ <b>ملاحظة:</b> تعذر فحص المستودع الحالي الآن: {html_escape(inspection.get('reason') or 'سبب غير معروف')}"
                    send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم تحديث GitHub token للمشروع.</b>{warning}")
                return
            if repository and inspection.get("ok"):
                raw_branches = inspection.get("branches") or []
                default_branch = inspection.get("default_branch") or (raw_branches[0] if raw_branches else "")
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH_DECISION",
                    "project_key": project_key,
                    "project_name": project_name,
                    "settings_edit_scope": scope,
                    "pending_github_enabled": bool(state.get("pending_github_enabled", current_github.get("enabled"))),
                    "pending_github_repository": repository,
                    "pending_github_token": token_value,
                    "pending_github_default_branch": default_branch,
                    "pending_github_branches": raw_branches,
                    "pending_github_repo_check_status": "checked",
                })
                summary_msg = format_github_repo_inspection_summary(repository, default_branch, raw_branches)
                send_telegram_message(chat_id, summary_msg, reply_markup=build_existing_project_branch_choice_keyboard(project_key, branches=raw_branches, default_branch=default_branch))
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH",
                "settings_edit_scope": scope,
                "pending_github_repository": repository,
                "pending_github_token": token_value,
                "pending_github_repo_check_status": "manual-branch",
            })
            send_telegram_message(chat_id, f"⚠️ <b>تعذر فحص المستودع الآن:</b> {html_escape(inspection.get('reason') or 'سبب غير معروف')}\nاكتب اسم branch يدويًا لهذا المشروع مثل <code>main</code> أو <code>develop</code>.")
            return

        if action == "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH":
            project_key = str(state.get("project_key") or "")
            branch = re.sub(r"\s+", "", text).strip()
            if not branch:
                send_telegram_message(chat_id, "⚠️ اكتب اسم branch صالح مثل <code>main</code> أو <code>develop</code>.")
                return
            finalize_existing_project_github_from_state(state, branch=branch, branch_mode="manual", repo_check_status="manual-branch")
            set_user_state(chat_id, {})
            send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم حفظ branch المشروع يدوياً.</b>\n<b>الفرع:</b> <code>{html_escape(branch)}</code>")
            return

        if action == "AWAITING_BOUND_PROJECT_NAME":
            project_name = re.sub(r"\s+", " ", text).strip()[:60] or "مشروع خارجي بدون اسم"
            project_key = f"prj_{uuid.uuid4().hex[:16]}"
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_BOUND_PROJECT_MODEL",
                "project_key": project_key,
                "project_name": project_name,
            })
            send_telegram_message(chat_id, f"✅ <b>اسم المشروع الخارجي:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\nاختر الآن الموديل المطلوب لهذا المشروع.", reply_markup=build_new_project_model_keyboard())
            return

        if action == "AWAITING_BOUND_PROJECT_GITHUB_REPO":
            repository = parse_github_repository_ref(text)
            if not repository:
                send_telegram_message(chat_id, "⚠️ صيغة المستودع غير واضحة. أرسل رابط GitHub كامل أو الصيغة <code>owner/repo</code>.")
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_BOUND_PROJECT_GITHUB_TOKEN",
                "pending_github_repository": repository,
            })
            send_telegram_message(chat_id, f"✅ <b>المستودع:</b> <code>{html_escape(repository)}</code>\nأرسل الآن <b>GitHub token</b> الخاص بهذا المشروع الخارجي حتى أتمكن من فحص المستودع والفروع.")
            return

        if action == "AWAITING_BOUND_PROJECT_GITHUB_TOKEN":
            repository = str(state.get("pending_github_repository") or "")
            token_value = str(text or "").strip()
            if not token_value:
                send_telegram_message(chat_id, "⚠️ أدخل GitHub token صالحاً لهذا المشروع الخارجي.")
                return
            inspection = inspect_github_repository(repository, token=token_value)
            if inspection.get("ok"):
                raw_branches = inspection.get("branches") or []
                default_branch = inspection.get("default_branch") or (raw_branches[0] if raw_branches else "")
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_GITHUB_BRANCH_DECISION",
                    "pending_github_enabled": True,
                    "pending_github_repository": repository,
                    "pending_github_token": token_value,
                    "pending_github_default_branch": default_branch,
                    "pending_github_branches": raw_branches,
                    "pending_github_repo_check_status": "checked",
                })
                summary_msg = format_github_repo_inspection_summary(repository, default_branch, raw_branches)
                send_telegram_message(chat_id, summary_msg, reply_markup=build_bound_project_branch_choice_keyboard(branches=raw_branches, default_branch=default_branch))
                return
            set_user_state(chat_id, {
                **state,
                "pending_github_repository": repository,
                "pending_github_token": "",
            })
            send_telegram_message(chat_id, f"⚠️ <b>تعذر فحص المستودع الآن:</b> {html_escape(inspection.get('reason') or 'سبب غير معروف')}\nأعد إدخال token صالح لهذا المشروع، أو استخدم المتابعة بدون GitHub إذا أردت التخطي.")
            return

        if action == "AWAITING_BOUND_PROJECT_GITHUB_BRANCH":
            branch = re.sub(r"\s+", "", text).strip()
            if not branch:
                send_telegram_message(chat_id, "⚠️ اكتب اسم branch صالح مثل <code>main</code> أو <code>develop</code>.")
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION",
                "pending_github_enabled": True,
                "pending_github_branch": branch,
                "pending_github_branch_mode": "manual",
                "pending_github_repo_check_status": "manual-branch",
            })
            send_telegram_message(chat_id, f"✅ <b>تم حفظ إعداد GitHub اليدوي للمشروع الخارجي.</b>\n<b>الفرع:</b> <code>{html_escape(branch)}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_bound_project_resume_prompt_keyboard())
            return

        if action == "AWAITING_BOUND_PROJECT_RESUME_PROMPT":
            settings, next_state = finalize_bound_external_project_from_state(state, chat_id=chat_id, resume_prompt=text)
            set_user_state(chat_id, next_state)
            send_telegram_message(chat_id, f"✅ <b>تم ربط المشروع الخارجي كمشروع محفوظ.</b>\n<b>الاسم:</b> {html_escape(str(state.get('project_name') or ''))}\n<b>المفتاح:</b> <code>{html_escape(str(state.get('project_key') or ''))}</code>\n<b>الموديل:</b> <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n<b>برومبت الاستئناف:</b> <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>\nأرسل الآن التعديل أو البرومبت المطلوب على هذا المشروع الخارجي.")
            return

        if action == "AWAITING_CONT_URL":
            ctx = resolve_resume_context(text)
            if ctx["project_key"]:
                present_resume_summary(chat_id, project_key=ctx["project_key"], target_url=ctx["target_url"], target_pid=ctx["pid"])
                return
            present_external_resume_decision(chat_id, target_url=ctx["target_url"], target_pid=ctx["pid"])
            return

        if action == "AWAITING_NEW_PROMPT":
            state_project_key = state.get("project_key")
            state_project_name = state.get("project_name")
            state_project_model = normalize_project_model(state.get("project_model") or get_project_selected_model(state_project_key))
            set_user_state(chat_id, {})
            try:
                EXECUTOR.submit(process_user_task_async, chat_id, None, text, state_project_model, state_project_key, state_project_name)
            except Exception as e:
                log_event("error", f"فشل جدولة المهمة: {e}")
            return

        if action == "AWAITING_CONT_PROMPT":
            target_url = state.get("url")
            state_project_key = state.get("project_key")
            state_project_name = state.get("project_name")
            state_project_model = normalize_project_model(state.get("project_model") or get_project_selected_model(state_project_key))
            set_user_state(chat_id, {})
            try:
                EXECUTOR.submit(process_user_task_async, chat_id, target_url, text, state_project_model, state_project_key, state_project_name)
            except Exception as e:
                log_event("error", f"فشل جدولة المهمة: {e}")
            return

        if "genspark.ai" in text or re.search(r"[a-f0-9\-]{36}", text):
            ctx = resolve_resume_context(text)
            if ctx["project_key"]:
                present_resume_summary(chat_id, project_key=ctx["project_key"], target_url=ctx["target_url"], target_pid=ctx["pid"])
                return
            present_external_resume_decision(chat_id, target_url=ctx["target_url"], target_pid=ctx["pid"])
            return

        set_user_state(chat_id, {})
        try:
            EXECUTOR.submit(process_user_task_async, chat_id, None, text)
        except Exception as e:
            log_event("error", f"فشل جدولة المهمة: {e}")


def load_telegram_offset() -> int:
    try:
        if TELEGRAM_OFFSET_FILE.exists():
            return int(TELEGRAM_OFFSET_FILE.read_text(encoding="utf-8").strip() or "0")
    except Exception:
        pass
    return 0


def save_telegram_offset(offset: int):
    try:
        TELEGRAM_OFFSET_FILE.write_text(str(offset), encoding="utf-8")
    except Exception:
        pass


def run_telegram_polling():
    print(Fore.GREEN + Style.BRIGHT + "╔══════════════════════════════════════════════════════════════╗")
    print(Fore.GREEN + Style.BRIGHT + f"║  🤖 تشغيل بوت تليجرام التفاعلي ({pathlib.Path(__file__).name})   ║")
    print(Fore.GREEN + Style.BRIGHT + "╚══════════════════════════════════════════════════════════════╝")
    print(Fore.YELLOW + f"📌 RUNNING FILE PATH: {pathlib.Path(__file__).resolve()}")

    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "⚠️ توكن البوت غير مضبوط!")
        log_event("error", "   اضبط متغير البيئة TELEGRAM_BOT_TOKEN أو أنشئ ملف telegram_bot_token.txt بجوار السكربت (خارج git).")
        return

    offset = load_telegram_offset()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    for cid in ALLOWED_CHAT_IDS:
        send_telegram_message(cid, f"🟢 <b>بوت Genspark Telegram Bridge ({pathlib.Path(__file__).name}) شغال ومستعد لاستقبال الأوامر!</b>", reply_markup=get_main_keyboard(cid))
    try:
        from curl_cffi import requests as cffi
        sess = cffi.Session()
    except Exception:
        import requests
        sess = requests.Session()

    consecutive_errors = 0
    try:
        while True:
            try:
                r = sess.get(url, params={"offset": offset, "timeout": 20}, timeout=30)
                if r.status_code == 200:
                    consecutive_errors = 0
                    data = r.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        save_telegram_offset(offset)
                        try:
                            EXECUTOR.submit(handle_telegram_update, update)
                        except Exception as e:
                            log_event("error", f"فشل جدولة معالجة التحديث: {e}")
                else:
                    consecutive_errors += 1
                    log_event("warning", f"getUpdates HTTP {r.status_code}")
            except Exception as e:
                consecutive_errors += 1
                log_event("error", f"خطأ في حلقة Telegram polling: {e}")
            # إصلاح: backoff تدريجي عند تكرار الأخطاء (حتى 15 ثانية) بدل النوم الثابت
            time.sleep(min(3 * consecutive_errors, 15) if consecutive_errors else 1)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "⏹️ تم إيقاف البوت يدوياً (Ctrl+C)")


def main():
    log_event("success", f"RUNNING FILE VERIFIED: {pathlib.Path(__file__).resolve()}")
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "لم يتم العثور على توكن البوت — شغّل مع متغير البيئة TELEGRAM_BOT_TOKEN أو ملف telegram_bot_token.txt")
        sys.exit(1)
    run_telegram_polling()


if __name__ == "__main__":
    main()
