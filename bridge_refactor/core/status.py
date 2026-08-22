"""bridge_refactor.core.status
كشف حالة الاستجابة واستخراج Project ID
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p05_project_tree
"""
from bridge_refactor.runtime import ns as _ns

__all__ = [
    "save_project_branch",
    "get_project_branches",
    "check_project_finished_flag",
    "get_random_email_from_accounts_genspark",
    "SESSION_EXPIRED_KEYWORDS",
    "FORBIDDEN_KEYWORDS",
    "CREDIT_EXHAUSTED_KEYWORDS",
    "PARTIAL_GENERATION_MARKERS",
    "DATA_RETENTION_KEYWORDS",
    "detect_response_status",
    "MODEL_DECLINE_MARKERS",
    "MODEL_DECLINE_MAX_RESPONSE_CHARS",
    "MODEL_DECLINED_STATUS",
    "is_model_decline_response",
    "DEEP_THINKING_MARKERS",
    "TASKS_REMAINING_PATTERN",
    "TASKS_REMAINING_TEXT_MARKERS",
    "extract_activity_signature",
    "fetch_project_activity_signature",
    "should_stop_on_activity_change",
    "extract_project_id",
]

def __getattr__(name):
    if name in __all__:
        return getattr(_ns, name)
    raise AttributeError(name)

def __dir__():
    return sorted(__all__)
