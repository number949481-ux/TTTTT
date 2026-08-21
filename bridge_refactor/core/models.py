"""bridge_refactor.core.models
BridgeConfig (النموذج التشغيلي لكل مهمة)
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p03_engine_accounts
"""
from bridge_refactor.runtime import ns as _ns

__all__ = [
    "_ENGINE_CACHE",
    "_ENGINE_LOCK",
    "get_genspark_engine",
    "get_account_lock",
    "_normalize_account_claim_key",
    "get_account_selection_claim",
    "claim_account_selection",
    "release_account_selection",
    "claim_eligible_account_for_owner",
    "record_account_journey",
    "format_account_journey_line",
    "notify_account_selection_observer",
    "is_valid_email",
    "get_account_fingerprint",
    "needs_web_search",
    "BridgeConfig",
    "get_accounts_file_path",
    "read_accounts_safe",
    "update_account_data",
    "is_account_ready",
    "reactivate_account_if_due",
    "get_eligible_accounts",
    "mark_account_cooldown",
    "refresh_cookies_on_401",
]

def __getattr__(name):
    if name in __all__:
        return getattr(_ns, name)
    raise AttributeError(name)

def __dir__():
    return sorted(__all__)
