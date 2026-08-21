"""[VERBATIM SLICE] p02_config_contracts
المصدر: 01.33_telegram_gen_bridge.py — الأسطر 155..458
المحتوى: Global config + models + CONTRACTS + resume-prompt utils + project settings (P17: ALLOWED_GROUP_IDS + is_chat_allowed لدعم الجروبات)
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
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


