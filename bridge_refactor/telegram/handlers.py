"""bridge_refactor.telegram.handlers
معالجات التحديثات + الـ polling + الكيبوردات الرئيسية
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p12_handlers_main
"""
from bridge_refactor.runtime import ns as _ns

__all__ = [
    "AWAITING_PROJECT_CONFIRMATION",
    "PROJECT_CONFIRM_CALLBACK_PREFIX",
    "INTENT_GUARD_STRONG_MIN_CHARS",
    "INTENT_GUARD_STRONG_MIN_WORDS",
    "INTENT_GUARD_QUOTE_PREVIEW_LIMIT",
    "INTENT_GUARD_STRONG_HINT",
    "INTENT_GUARD_AMBIGUOUS_HINT",
    "INTENT_GUARD_EMPTY_MESSAGE",
    "INTENT_GUARD_EXPIRED_MESSAGE",
    "INTENT_GUARD_ALREADY_CONFIRMED_MESSAGE",
    "INTENT_GUARD_CANCELLED_MESSAGE",
    "PROJECT_CONFIRM_YES_LABEL",
    "PROJECT_CONFIRM_NO_LABEL",
    "classify_idle_text_intent",
    "build_project_confirmation_keyboard",
    "render_project_confirmation_card",
    "handle_idle_intent_guard",
    "forward_pending_prompt_after_wizard",
    "get_main_keyboard",
    "handle_prompt_context_collision",
    "handle_telegram_update",
    "load_telegram_offset",
    "save_telegram_offset",
    "run_telegram_polling",
    "main",
]

def __getattr__(name):
    if name in __all__:
        return getattr(_ns, name)
    raise AttributeError(name)

def __dir__():
    return sorted(__all__)
