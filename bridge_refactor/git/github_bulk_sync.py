#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bridge_refactor.git.github_bulk_sync
واجهة تصدير محرك المزامنة الذري gh_bulk عبر Git Data API
"""
import sys
import pathlib

# إضافة مجلد حزمة bridge_refactor_31 للمسار إذا لم يكن موجوداً
_CURRENT_DIR = pathlib.Path(__file__).resolve().parent
_PKG_ROOT = _CURRENT_DIR.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from gh_bulk import (
    GhClient,
    sync,
    sync_payload,
    git_blob_sha,
    normalize_remote_path,
    is_text_content,
    find_bootstrap_candidate,
    GhBulkError,
    RepoNotFoundError,
    EmptyRepoNoBootstrapError,
    ConcurrentPushConflictError,
    ValidationFailedError,
    SyncTimeoutError,
    INLINE_CONTENT_MAX_BYTES,
    MAX_TOTAL_SYNC_SECONDS,
)

__all__ = [
    "GhClient",
    "sync",
    "sync_payload",
    "git_blob_sha",
    "normalize_remote_path",
    "is_text_content",
    "find_bootstrap_candidate",
    "GhBulkError",
    "RepoNotFoundError",
    "EmptyRepoNoBootstrapError",
    "ConcurrentPushConflictError",
    "ValidationFailedError",
    "SyncTimeoutError",
    "INLINE_CONTENT_MAX_BYTES",
    "MAX_TOTAL_SYNC_SECONDS",
]
