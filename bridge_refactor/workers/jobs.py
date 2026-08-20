"""bridge_refactor.workers.jobs
مشغل المهام + بوابة الـ checkpoint + وصف النتائج النهائية
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p10_progress_credit, p11_worker
"""
from bridge_refactor.runtime import ns as _ns

__all__ = [
    "_is_fresh_artifact",
    "inspect_stage_artifacts",
    "should_capture_project_update",
    "NON_ACTIONABLE_PROGRESS_STATUSES",
    "should_emit_progress_event",
    "describe_archive_delivery",
    "get_credit_continuation_limit",
    "get_credit_continuation_progress",
    "format_credit_continuation_progress",
    "_set_credit_checkpoint_state",
    "_normalize_progress_callback_result",
    "evaluate_credit_checkpoint_gate",
    "describe_credit_checkpoint_state",
    "describe_terminal_outcome",
    "process_user_task_async",
]

def __getattr__(name):
    if name in __all__:
        return getattr(_ns, name)
    raise AttributeError(name)

def __dir__():
    return sorted(__all__)
