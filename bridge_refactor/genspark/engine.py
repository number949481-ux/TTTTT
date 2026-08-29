"""bridge_refactor.genspark.engine
محرك Genspark: التحميل + الإرسال + make_public + الأرشفة + الـ failover
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p03_engine_accounts, p06_engine_flow
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
    "get_eligible_accounts",
    "mark_account_cooldown",
    "refresh_cookies_on_401",
    "_is_safe_archive_member_name",
    "_archive_signature_label",
    "_archive_diag",
    "_should_skip_archive_member",
    "_is_never_copy_file",
    "_resolve_effective_source_root",
    "_extract_archive_with_diagnostics",
    "format_archive_diagnostic",
    "download_project_archive",
    "make_project_always_public",
    "get_public_forked_pid",
    "send_message_and_make_public",
    "send_message_with_auto_account_failover",
]

def __getattr__(name):
    if name in __all__:
        return getattr(_ns, name)
    raise AttributeError(name)

def __dir__():
    return sorted(__all__)
