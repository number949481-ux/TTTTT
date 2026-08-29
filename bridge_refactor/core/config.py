"""bridge_refactor.core.config
الإعدادات والثوابت وعقود الموديلات وأدوات resume prompt
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p01_bootstrap, p02_config_contracts
"""
from bridge_refactor.runtime import ns as _ns

__all__ = [
    "SCRIPT_DIR",
    "BUILD_VERSION",
    "BUILD_PARENT_BASELINE",
    "BUILD_PARENT_BASELINE_SHA256",
    "LOG_FILE",
    "logger",
    "redact_email",
    "log_event",
    "html_escape",
    "resolve_shared_path",
    "load_bot_token",
    "TELEGRAM_BOT_TOKEN",
    "FILE_LOCK",
    "REFRESH_LOCK",
    "ACCOUNT_LOCKS",
    "ACCOUNT_LOCKS_GUARD",
    "ACCOUNT_SELECTION_CLAIMS",
    "ACCOUNT_SELECTION_CLAIMS_GUARD",
    "COOLDOWN_SECONDS",
    "TELEGRAM_OFFSET_FILE",
    "USER_AGENTS",
    "BROWSER_PROFILES",
    "ALLOWED_CHAT_IDS",
    "DEFAULT_CHANNEL_ID",
    "ALLOWED_GROUP_IDS",
    "is_chat_allowed",
    "PROJECTS_TREE_FILE",
    "PROJECT_REGISTRY_HOME",
    "PROJECT_REGISTRY_INDEX_FILE",
    "CONTRACT_VERSION",
    "AVAILABLE_MODELS",
    "DEFAULT_PROJECT_MODEL",
    "PROTECTED_MODELS",
    "MODEL_ALIASES",
    "CONTRACTS",
    "is_protected",
    "apply_contract",
    "normalize_project_model",
    "DEFAULT_PROJECT_RESUME_PROMPT",
    "PROJECT_SECRET_SCHEMA_VERSION",
    "MALFORMED_PROJECT_LINK_MESSAGE",
    "normalize_project_resume_prompt",
    "normalize_project_resume_mode",
    "RUNTIME_GITHUBTOKEN_SUFFIX_RE",
    "GENERIC_GITHUB_SECRET_RE",
    "strip_runtime_github_token_suffix",
    "redact_github_secrets",
    "get_public_continuation_prompt_text",
    "get_default_github_token_from_env",
    "compose_runtime_resume_prompt",
    "summarize_resume_prompt_for_display",
    "resolve_project_runtime_binding",
    "get_bridge_cfg_public_resume_prompt",
    "get_bridge_cfg_runtime_resume_prompt",
    "apply_project_runtime_binding",
    "default_project_settings",
    "should_skip_artifacts_download",
]

def __getattr__(name):
    if name in __all__:
        return getattr(_ns, name)
    raise AttributeError(name)

def __dir__():
    return sorted(__all__)
