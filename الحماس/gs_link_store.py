# gs_link_store.py — مخزن معرّفات مشاريع الشات (آخر 3 PIDs) — Additive Only
import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone

_DIR = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.environ.get("GS_LINK_STORE", os.path.join(_DIR, "gs_link_store.json"))
MAX_KEEP = 3
_LOCK = threading.Lock()
_UUID_RE = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")


def _clean_pid(pid) -> str:
    """تطبيع الـ PID: إزالة كل المسافات/whitespace (حتى اللي جوّا النص) + lowercase.
    ده بيصلّح الـ PIDs الباظة زي '9de3ba6b-9bae -4a45-...' اللي كانت بتمنع التكملة."""
    if not pid or not isinstance(pid, str):
        return ""
    return _WS_RE.sub("", pid).lower()


def _is_valid_pid(pid: str) -> bool:
    """التحقق من صحة معرّف المشروع (UUID v4 مكون من 36 حرفاً) بعد التنظيف الكامل"""
    return bool(_UUID_RE.match(_clean_pid(pid)))


def _read() -> dict:
    """قراءة المخزن بأمان — أي استثناء يرجع dict فارغ بصمت تام"""
    try:
        if not os.path.exists(STORE_PATH):
            return {}
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write(data: dict) -> None:
    """كتابة ذرية وآمنة عبر tempfile و os.replace لمنع تلف الملفات نهائياً"""
    d = os.path.dirname(os.path.abspath(STORE_PATH)) or "."
    try:
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, STORE_PATH)
    except Exception:
        try:
            if "tmp" in locals() and os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass


def _repair_store() -> None:
    """🩹 Self-Heal: تنظيف كل الـ PIDs الباظة (مسافات داخلية) في الملف وإعادة كتابته.
    بيشتغل مرة واحدة عند أول قراءة — آمن تماماً وأي فشل بيتجاهل بصمت."""
    with _LOCK:
        data = _read()
        changed = False
        for k, v in list(data.items()):
            if k.startswith("_"):
                if k == "_owners" and isinstance(v, dict):
                    new_owners = {}
                    for opid, owner in v.items():
                        cpid = _clean_pid(opid)
                        if cpid != opid:
                            changed = True
                        if _UUID_RE.match(cpid):
                            new_owners[cpid] = owner
                    if changed:
                        data["_owners"] = new_owners
                continue
            if isinstance(v, list):
                cleaned = []
                for p in v:
                    cp = _clean_pid(p)
                    if _UUID_RE.match(cp):
                        if cp != p:
                            changed = True
                        if cp not in cleaned:
                            cleaned.append(cp)
                    else:
                        changed = True  # عنصر تالف نهائياً → يتشال
                if cleaned != v:
                    data[k] = cleaned[:MAX_KEEP]
        if changed:
            data["_updated_at"] = datetime.now(timezone.utc).isoformat()
            _write(data)


_REPAIRED = False


def _ensure_repaired() -> None:
    global _REPAIRED
    if not _REPAIRED:
        _REPAIRED = True
        try:
            _repair_store()
        except Exception:
            pass


def get_pids(key: str = "default") -> list:
    """إرجاع قائمة الـ PIDs المحفوظة للمفتاح المحدد (الأحدث أولاً)"""
    _ensure_repaired()
    data = _read()
    raw_list = data.get(key, [])
    if not isinstance(raw_list, list):
        return []
    return [_clean_pid(p) for p in raw_list if _is_valid_pid(p)][:MAX_KEEP]


def get_pid(key: str = "default") -> str | None:
    """إرجاع الـ PID النشط حالياً (الأحدث) — يرجع None لو فارغ أو غير موجود"""
    pids = get_pids(key)
    return pids[0] if pids else None


def push_pid(pid: str, key: str = "default", owner: str | None = None) -> bool:
    """إضافة PID صالح للمقدمة مع إزالة التكرار والقص على 3 — يرفض أي نص غير صالح.
    owner (اختياري): إيميل صاحب المشروع — بيتخزن عشان الشغلة الجاية تقدر
    تقفل على نفس الحساب وتكمل مباشرة بدل ما تعمل Fork."""
    if not pid or not isinstance(pid, str):
        return False
    pid_clean = _clean_pid(pid)
    if not _UUID_RE.match(pid_clean):
        return False  # رفض حاسم لأي نص غير مطابق للـ UUID مثل __INVALID_PROJECT__

    with _LOCK:
        data = _read()
        existing = [_clean_pid(p) for p in data.get(key, []) if _is_valid_pid(p)]
        lst = [p for p in existing if p != pid_clean]
        lst.insert(0, pid_clean)
        data[key] = lst[:MAX_KEEP]
        if owner:
            owners = data.get("_owners")
            if not isinstance(owners, dict):
                owners = {}
            owners[pid_clean] = str(owner).strip().lower()
            data["_owners"] = owners
        data["_updated_at"] = datetime.now(timezone.utc).isoformat()
        _write(data)
        return True


def get_owner(pid: str) -> str | None:
    """إيميل صاحب الـ PID (لو متسجل) — أو None"""
    if not pid or not isinstance(pid, str):
        return None
    pid_clean = _clean_pid(pid)
    if not _UUID_RE.match(pid_clean):
        return None
    owners = _read().get("_owners")
    if not isinstance(owners, dict):
        return None
    owner = owners.get(pid_clean)
    return str(owner).strip().lower() if owner else None


def drop_pid(pid: str, key: str = "default") -> bool:
    """حذف PID باظ من المخزن ليصبح المعرّف التالي في القائمة هو النشط تلقائياً"""
    if not pid or not isinstance(pid, str):
        return False
    pid_clean = _clean_pid(pid)
    if not _UUID_RE.match(pid_clean):
        return False

    with _LOCK:
        data = _read()
        existing = [_clean_pid(p) for p in data.get(key, []) if _is_valid_pid(p)]
        if pid_clean not in existing:
            return False
        lst = [p for p in existing if p != pid_clean]
        data[key] = lst
        owners = data.get("_owners")
        if isinstance(owners, dict) and pid_clean in owners:
            del owners[pid_clean]
        data["_updated_at"] = datetime.now(timezone.utc).isoformat()
        _write(data)
        return True
