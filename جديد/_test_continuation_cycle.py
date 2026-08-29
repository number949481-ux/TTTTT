# اختبار Harness: دورة التكملة الكاملة (run 1 يحفظ → run 2 يكمل) — بدون أي شبكة
import importlib.util, json, os, sys, uuid, pathlib

DIR = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("eng", DIR / "02.07_Genspark_claude-opus-5-code.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["eng"] = mod
spec.loader.exec_module(mod)

FAKE_ACC = {
    "email": "fake@test.local", "password": "x",
    "cookies": {"session_id": "fake"}, "balance": 100, "active": True,
    "last_sent_chat_sent": "2020-01-01T00:00:00",
}
NEW_PID = str(uuid.uuid4())
captured = {}

def fake_load_accounts(cfg): return [dict(FAKE_ACC)]
def fake_lock_pick(cfg, skip_emails=None): return dict(FAKE_ACC), dict(FAKE_ACC["cookies"])
def fake_send_chat(cookies, question, email="", project_id=None, history=None,
                   cfg=None, ticket_file=None, fork_project_id=None):
    captured["project_id"] = project_id
    return ("رد تجريبي ناجح", NEW_PID, "asst-123")
def fake_ensure_public(pid, cookies, cfg, label=""):
    return f"https://www.genspark.ai/autopilotagent_viewer?id={pid}"

mod.load_accounts = fake_load_accounts
mod.lock_pick_and_reserve = fake_lock_pick
mod.send_chat = fake_send_chat
mod.ensure_public = fake_ensure_public
mod.save_accounts = lambda accounts, cfg: None
mod.update_conversation = lambda *a, **k: None
mod.check_balance = lambda cookies: 100

import gs_link_store as store_mod
store_mod.STORE_PATH = "/tmp/harness_store.json"
if os.path.exists("/tmp/harness_store.json"):
    os.remove("/tmp/harness_store.json")

sys.argv = ["engine.py", "سؤال اول"]
print("=" * 20, "RUN 1: مخزن فاضي → يبدأ مشروع جديد", "=" * 20)
mod.main()
pid1 = store_mod.get_pid(key="default")
print("── بعد RUN 1 ──")
print("الـ PID اللي اتحفظ في المخزن:", pid1)
assert captured["project_id"] is None, "RUN 1 المفروض يبدأ جديد"
assert pid1 == NEW_PID, f"push-on-success مش شغال (حصل {pid1} مش {NEW_PID})"
print("OK-1: بدأ جديد + الـ PID الجديد اتحفظ في المخزن\n")

captured.clear()
sys.argv = ["engine.py", "سؤال تاني في نفس المحادثة"]
print("=" * 20, "RUN 2: المخزن فيه PID → لازم يكمل عليه", "=" * 20)
mod.main()
print("── بعد RUN 2 ──")
print("الـ project_id اللي اتبعت عليه:", captured["project_id"])
assert captured["project_id"] == NEW_PID, \
    f"التكملة مش شغالة: اتبعت بـ {captured['project_id']} مش {NEW_PID}"
print()
print("OK-2: الـ RUN التاني خد الـ PID من المخزن وبعت عليه")
print()
print("== كل دورة التكملة شغالة 100% ==")
