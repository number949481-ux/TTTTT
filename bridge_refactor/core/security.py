"""bridge_refactor.core.security
فحوصات أمان الأرشيف والاستخراج الآمن
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p06_engine_flow
"""
from bridge_refactor.runtime import ns as _ns

__all__ = [
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
