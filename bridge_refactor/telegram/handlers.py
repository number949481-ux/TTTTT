"""bridge_refactor.telegram.handlers
معالجات التحديثات + الـ polling + الكيبوردات الرئيسية
واجهة إعادة تصدير من الـ runtime الموحّد — الرموز أدناه مصدرها
الأجزاء: p12_handlers_main
"""
from bridge_refactor.runtime import ns as _ns

__all__ = [
    "get_main_keyboard",
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
