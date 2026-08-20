"""bridge_refactor.telegram.messaging
طبقة رسائل تيليجرام + Live Renderer/Transport
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p04_telegram_api
"""
from bridge_refactor.runtime import ns as _ns

__all__ = [
    "_call_telegram_api_json",
    "send_telegram_message_detailed",
    "edit_telegram_message_text",
    "send_telegram_message",
    "_account_selection_event_title",
    "AccountSelectionLiveRenderer",
    "render_account_selection_live_text",
    "render_account_selection_handoff_text",
    "AccountSelectionLiveTransport",
    "attach_account_selection_live_transport",
    "format_elapsed_seconds",
    "LiveOpsReporter",
    "get_live_ops_reporter",
    "attach_live_ops_reporter",
    "send_telegram_document",
]

def __getattr__(name):
    if name in __all__:
        return getattr(_ns, name)
    raise AttributeError(name)

def __dir__():
    return sorted(__all__)
