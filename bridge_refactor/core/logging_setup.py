"""bridge_refactor.core.logging_setup
التسجيل الملوّن + redact_email + html_escape
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p01_bootstrap
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
    "load_bot_token",
    "TELEGRAM_BOT_TOKEN",
]

def __getattr__(name):
    if name in __all__:
        return getattr(_ns, name)
    raise AttributeError(name)

def __dir__():
    return sorted(__all__)
