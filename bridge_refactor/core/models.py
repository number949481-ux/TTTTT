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
    "open_account_timing_span",
    "close_account_timing_span",
    "format_arabic_duration",
    "format_compact_duration",
    "aggregate_journey_spans_per_email",
    "PRODUCTIVE_SPAN_MIN_SECONDS",
    "filter_productive_account_entries",
    "format_account_timing_block",
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
    "GIFT_PREFLIGHT_ENABLED",
    "GIFT_STALE_DAYS",
    "GIFT_GRACE_DAYS",
    "GIFT_SNAPSHOT_MAX_AGE_HOURS",
    "GIFT_LABELS",
    "_parse_local_iso_ts",
    "classify_gift_freshness",
    "get_eligible_accounts",
    "mark_account_cooldown",
    "COOLDOWN_VAULT_FILENAME",
    "ACCOUNT_LOG_FILENAME",
    "ACCOUNT_LOG_RETENTION_DAYS",
    "ACCOUNT_LOG_MAX_ENTRIES",
    "ACCOUNT_LOG_LOCK",
    "COOLDOWN_VAULT_REASONS",
    "COOLDOWN_VAULT_HOURS",
    "FORBIDDEN_MOVE_AFTER_N",
    "FORBIDDEN_HITS_WINDOW_HOURS",
    "ACCOUNT_LOG_SCHEMA_ENTRY",
    "_ACCOUNT_LOG_FORBIDDEN_KEYS",
    "_atomic_json_dump",
    "append_account_log",
    "register_forbidden_hit",
    "move_account_to_cooldown_vault",
    "refresh_cookies_on_401",
]

def __getattr__(name):
    if name in __all__:
        return getattr(_ns, name)
    raise AttributeError(name)

def __dir__():
    return sorted(__all__)
