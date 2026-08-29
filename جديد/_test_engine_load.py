# اختبار مؤقت: تأكيد تحميل المحرك + كل الـ APIs المطلوبة
import continue_project as cp

print("── 4) اختبار تحميل المحرك الفعلي ──")
paths = cp._find_engine_paths()
print("مرشحي المحرك:")
for p in paths:
    status = "موجود" if p.exists() else "مفيش"
    print(f"   - {p.name} ({status})")

mod = cp.load_engine()
print("المحرك اللي اتحمّل: " + cp._ENGINE["path"].split("/")[-1])

# كل الـ APIs اللي continue_project.py بيستدعيها
required = [
    "send_chat", "load_accounts", "pick_account", "lock_pick_and_reserve",
    "ensure_public", "create_forked_project", "Config",
]
missing = [f for f in required if not hasattr(mod, f)]
if missing:
    raise SystemExit("❌ ناقص APIs: %s" % missing)
print("✅ كل الـ APIs المطلوبة موجودة (شاملة create_forked_project الجديد)")

# توكيد السيجنيتشر
import inspect
sig = inspect.signature(mod.send_chat)
assert "project_id" in sig.parameters and "fork_project_id" in sig.parameters
print("✅ send_chat بيقبل project_id و fork_project_id")

cfg = mod.Config()
assert cfg.continue_from_store is True
print("✅ Config.continue_from_store = True (الافتراضي الجديد)")
print()
print("✅✅✅ المحرك + continue_project متوصّلين وشغالين")
