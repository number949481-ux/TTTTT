"""bridge_refactor.projects.registry
ProjectRegistry + فهرس الهوية + أقفال التشغيل
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p07_state_registry, p08_registry_index
"""
from bridge_refactor.runtime import ns as _ns

__all__ = [
    "EXECUTOR",
    "USER_STATE_STORE",
    "USER_STATE_LOCK",
    "set_user_state",
    "get_user_state",
    "UPLOAD_QUEUE_SCHEMA_VERSION",
    "UPLOAD_MAX_INLINE_BYTES",
    "UPLOAD_RETRY_BASE_SECONDS",
    "UPLOAD_RETRY_MAX_SECONDS",
    "ProjectRegistry",
    "PROJECT_LOCKS",
    "PROJECT_LOCKS_GUARD",
    "PROJECT_RUN_OWNERS",
    "PROJECT_RUN_OWNERS_GUARD",
    "REGISTRY_INDEX_LOCK",
    "PROJECT_MANIFEST_SCHEMA_VERSION",
    "CHECKPOINT_RECORD_SCHEMA_VERSION",
    "get_project_lock",
    "claim_project_run",
    "release_project_run",
    "_utc",
    "_sha256_file",
    "is_probable_project_id",
    "extract_stage_project_id",
    "REGISTRY_INDEX_SCHEMA_VERSION",
    "_registry_index_backup_path",
    "_project_record_default",
    "_normalize_project_record",
    "_registry_index_default",
    "_normalize_registry_index_payload",
    "_read_registry_index",
    "_write_registry_index",
    "lookup_project_key_for_locator",
    "get_project_identity_record",
    "resolve_resume_context",
    "upsert_project_identity",
    "remember_registry_identity",
    "build_genspark_viewer_url",
    "build_viewer_url",
    "build_live_preview_keyboard",
    "summarize_project_context",
]

def __getattr__(name):
    if name in __all__:
        return getattr(_ns, name)
    raise AttributeError(name)

def __dir__():
    return sorted(__all__)
