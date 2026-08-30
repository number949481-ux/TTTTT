"""[VERBATIM SLICE] p08_registry_index
المصدر: 01.33_telegram_gen_bridge.py — الأسطر 4196..4760
المحتوى: Project run locks + P25: Interactive Cancellation Manager (register/trigger/unregister cancel events) + registry index I/O + identity + resume context + P26: is_project_build_active + delete_project_atomically (الحذف الذري الشامل: فهرس + شجرة + قرص) + viewer URLs + live preview keyboard (P25: cancel_token + confirm_cancel)
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
PROJECT_LOCKS = {}; PROJECT_LOCKS_GUARD = threading.Lock()
PROJECT_RUN_OWNERS = {}; PROJECT_RUN_OWNERS_GUARD = threading.Lock()
REGISTRY_INDEX_LOCK = threading.Lock()
PROJECT_MANIFEST_SCHEMA_VERSION = 1
CHECKPOINT_RECORD_SCHEMA_VERSION = 1


def get_project_lock(key):
    with PROJECT_LOCKS_GUARD:
        return PROJECT_LOCKS.setdefault(key, threading.Lock())


def claim_project_run(project_key: str, owner_token: str) -> bool:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    token = str(owner_token or "").strip()
    if not key or not token:
        return False
    with PROJECT_RUN_OWNERS_GUARD:
        current = PROJECT_RUN_OWNERS.get(key)
        if current and current != token:
            return False
        PROJECT_RUN_OWNERS[key] = token
        return True


def release_project_run(project_key: str, owner_token: str) -> bool:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    token = str(owner_token or "").strip()
    with PROJECT_RUN_OWNERS_GUARD:
        if PROJECT_RUN_OWNERS.get(key) != token:
            return False
        PROJECT_RUN_OWNERS.pop(key, None)
        return True


# ══════════════════════════════════════════════════════════════
# 🛑 [P25] Interactive Cancellation Manager — إلغاء تفاعلي فوري
# ══════════════════════════════════════════════════════════════
# مسجل مركزي Thread-Safe لأحداث الإلغاء النشطة:
#   token قصير (uuid hex 12) ← threading.Event + metadata
# السبب: callback_data في تيليجرام محدود بـ 64 بايت بينما
# project_key قد يبلغ 80 حرفاً — لذا نستخدم توكن قصيراً كمفتاح.
_ACTIVE_CANCEL_EVENTS: dict[str, dict] = {}
_CANCEL_EVENTS_GUARD = threading.Lock()
CANCELLED_STATUS = "CANCELLED"
USER_CANCELLED_MARKER = "__USER_CANCELLED__"


def new_cancel_token() -> str:
    """توليد توكن إلغاء قصير آمن للاستخدام داخل callback_data (≤ 64 بايت)"""
    return uuid.uuid4().hex[:12]


def register_cancel_event(token: str, project_key: str = "", chat_id=None) -> threading.Event | None:
    """تسجيل حدث إلغاء جديد لمهمة نشطة — يُرجع الـ Event للحقن في cfg.cancel_event"""
    key = str(token or "").strip()
    if not key:
        return None
    with _CANCEL_EVENTS_GUARD:
        entry = _ACTIVE_CANCEL_EVENTS.get(key)
        if entry is not None:
            return entry["event"]
        ev = threading.Event()
        _ACTIVE_CANCEL_EVENTS[key] = {
            "event": ev,
            "project_key": str(project_key or ""),
            "chat_id": chat_id,
            "created_at": time.time(),
        }
        return ev


def get_cancel_entry(token: str) -> dict | None:
    """قراءة metadata حدث الإلغاء (نسخة آمنة) — None لو التوكن غير مسجل/منتهي"""
    key = str(token or "").strip()
    if not key:
        return None
    with _CANCEL_EVENTS_GUARD:
        entry = _ACTIVE_CANCEL_EVENTS.get(key)
        return dict(entry) if isinstance(entry, dict) else None


def update_cancel_entry(token: str, **fields) -> bool:
    """تحديث metadata حدث إلغاء نشط (مثل live_pid و message_id لبطاقة المعاينة)"""
    key = str(token or "").strip()
    if not key:
        return False
    with _CANCEL_EVENTS_GUARD:
        entry = _ACTIVE_CANCEL_EVENTS.get(key)
        if not isinstance(entry, dict):
            return False
        entry.update(fields)
        return True


def trigger_cancel(token: str) -> bool:
    """تفعيل الإلغاء القهري — يضبط الـ Event فيلتقطه المحرك وحلقات المتابعة فوراً"""
    key = str(token or "").strip()
    if not key:
        return False
    with _CANCEL_EVENTS_GUARD:
        entry = _ACTIVE_CANCEL_EVENTS.get(key)
        if not isinstance(entry, dict):
            return False
        entry["event"].set()
        entry["cancelled_at"] = time.time()
        return True


def is_cancel_requested(token: str) -> bool:
    """فحص سريع: هل طُلب إلغاء هذه المهمة؟"""
    key = str(token or "").strip()
    if not key:
        return False
    with _CANCEL_EVENTS_GUARD:
        entry = _ACTIVE_CANCEL_EVENTS.get(key)
        return bool(entry and entry["event"].is_set())


def unregister_cancel_event(token: str) -> bool:
    """تنظيف مضمون بعد انتهاء المهمة (نجاحاً/فشلاً/إلغاءً) — Zero Leaks"""
    key = str(token or "").strip()
    if not key:
        return False
    with _CANCEL_EVENTS_GUARD:
        return _ACTIVE_CANCEL_EVENTS.pop(key, None) is not None


def _utc(): return datetime.now(timezone.utc).isoformat()
def _sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""): h.update(block)
    return h.hexdigest()


def is_probable_project_id(value: str | None) -> bool:
    text = str(value or "").strip()
    if not text or text == "غير معروف" or "__INVALID_PROJECT__" in text:
        return False
    if "login" in text.lower() or "/" in text or " " in text:
        return False
    return bool(re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", text, re.IGNORECASE))


def extract_stage_project_id(stage_url: str | None, stage_dir: str | None = None) -> str:
    pid = extract_project_id(stage_url) if stage_url else ""
    if is_probable_project_id(pid):
        return pid
    if stage_dir:
        candidate = pathlib.Path(stage_dir).name
        if is_probable_project_id(candidate):
            return candidate
    return ""


REGISTRY_INDEX_SCHEMA_VERSION = 1


def _registry_index_backup_path() -> pathlib.Path:
    return PROJECT_REGISTRY_INDEX_FILE.with_suffix(".bak")


def _project_record_default(project_key: str) -> dict:
    return {
        "project_key": project_key,
        "root_genspark_pid": "",
        "latest_genspark_pid": "",
        "project_name": "",
        "chat_id": None,
        "status": "",
        "created_at": _utc(),
        "updated_at": _utc(),
        "schema_version": REGISTRY_INDEX_SCHEMA_VERSION,
    }


def _normalize_project_record(project_key: str, record: dict | None) -> dict:
    base = _project_record_default(project_key)
    if isinstance(record, dict):
        for field_name in ("root_genspark_pid", "latest_genspark_pid", "project_name", "status", "created_at", "updated_at"):
            if record.get(field_name) is not None:
                base[field_name] = record.get(field_name)
        if record.get("chat_id") is not None:
            try:
                base["chat_id"] = int(record.get("chat_id"))
            except Exception:
                base["chat_id"] = None
    base["schema_version"] = REGISTRY_INDEX_SCHEMA_VERSION
    return base


def _registry_index_default() -> dict:
    return {"schema_version": REGISTRY_INDEX_SCHEMA_VERSION, "projects": {}, "pid_to_key": {}}


def _normalize_registry_index_payload(data: dict) -> dict:
    projects_src = data.get("projects") if isinstance(data.get("projects"), dict) else {}
    pid_to_key_src = data.get("pid_to_key") if isinstance(data.get("pid_to_key"), dict) else {}
    normalized_projects = {}
    normalized_aliases = {}
    for raw_key, raw_record in projects_src.items():
        key = re.sub(r"[^A-Za-z0-9_-]", "_", str(raw_key or ""))[:80]
        if not key:
            continue
        record = _normalize_project_record(key, raw_record)
        for pid_field in ("root_genspark_pid", "latest_genspark_pid"):
            pid_value = extract_project_id(record.get(pid_field)) if record.get(pid_field) else ""
            if not is_probable_project_id(pid_value):
                record[pid_field] = ""
            else:
                record[pid_field] = pid_value
                normalized_aliases[pid_value] = key
        normalized_projects[key] = record
    for pid, key in pid_to_key_src.items():
        pid_str = extract_project_id(pid) if pid else ""
        key_str = re.sub(r"[^A-Za-z0-9_-]", "_", str(key or ""))[:80]
        if is_probable_project_id(pid_str) and key_str in normalized_projects:
            normalized_aliases.setdefault(pid_str, key_str)
    return {
        "schema_version": REGISTRY_INDEX_SCHEMA_VERSION,
        "projects": normalized_projects,
        "pid_to_key": normalized_aliases,
    }


def _read_registry_index() -> dict:
    if not PROJECT_REGISTRY_INDEX_FILE.exists():
        return _registry_index_default()
    try:
        data = json.loads(PROJECT_REGISTRY_INDEX_FILE.read_text(encoding="utf-8"))
    except Exception as err:
        log_event("warning", f"تعذر قراءة registry index؛ سيتم التعامل معه fail-closed: {type(err).__name__}")
        return _registry_index_default()
    if not isinstance(data, dict):
        log_event("warning", "ملف registry index ليس JSON object؛ تم التعامل معه fail-closed")
        return _registry_index_default()

    schema_version = data.get("schema_version")
    if schema_version is None:
        normalized = _normalize_registry_index_payload(data)
        if normalized["projects"] or normalized["pid_to_key"]:
            try:
                _write_registry_index(normalized)
            except Exception:
                pass
        return normalized
    if schema_version != REGISTRY_INDEX_SCHEMA_VERSION:
        log_event("warning", f"schema_version غير معروف في registry index: {schema_version} — تم التعامل fail-closed")
        return _registry_index_default()
    return _normalize_registry_index_payload(data)


def _write_registry_index(data: dict):
    PROJECT_REGISTRY_HOME.mkdir(parents=True, exist_ok=True)
    normalized = _normalize_registry_index_payload(data)
    if PROJECT_REGISTRY_INDEX_FILE.exists():
        backup = _registry_index_backup_path()
        backup.write_text(PROJECT_REGISTRY_INDEX_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    temp = PROJECT_REGISTRY_INDEX_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(PROJECT_REGISTRY_INDEX_FILE)


def lookup_project_key_for_locator(url_or_pid: str | None) -> str | None:
    pid = extract_project_id(url_or_pid) if url_or_pid else ""
    if not is_probable_project_id(pid):
        return None
    with REGISTRY_INDEX_LOCK:
        data = _read_registry_index()
        key = data["pid_to_key"].get(pid)
        return str(key) if key else None


def get_project_identity_record(project_key: str) -> dict | None:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        return None
    with REGISTRY_INDEX_LOCK:
        record = _read_registry_index()["projects"].get(key)
        return dict(record) if isinstance(record, dict) else None


def resolve_resume_context(url_or_pid: str | None) -> dict:
    pid = extract_project_id(url_or_pid) if url_or_pid else ""
    target_url = f"https://www.genspark.ai/autopilotagent_viewer?id={pid}" if is_probable_project_id(pid) else str(url_or_pid or "")
    project_key = lookup_project_key_for_locator(url_or_pid) if url_or_pid else None
    identity = get_project_identity_record(project_key) if project_key else None
    project_name = ""
    if identity and identity.get("project_name"):
        project_name = str(identity.get("project_name"))
    return {
        "pid": pid,
        "target_url": target_url,
        "project_key": project_key or "",
        "project_name": project_name,
        "identity": identity or {},
    }


def upsert_project_identity(
    project_key: str,
    root_pid: str | None = None,
    latest_pid: str | None = None,
    project_name: str | None = None,
    chat_id: int | None = None,
    status: str | None = None,
) -> dict:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        raise ValueError("project_key missing")
    clean_root = extract_project_id(root_pid) if root_pid else ""
    clean_latest = extract_project_id(latest_pid) if latest_pid else ""
    if not is_probable_project_id(clean_root):
        clean_root = ""
    if not is_probable_project_id(clean_latest):
        clean_latest = ""

    with REGISTRY_INDEX_LOCK:
        data = _read_registry_index()
        record = data["projects"].get(key, {"project_key": key, "created_at": _utc()})
        if clean_root and not record.get("root_genspark_pid"):
            record["root_genspark_pid"] = clean_root
        if clean_latest:
            record["latest_genspark_pid"] = clean_latest
        if project_name:
            record["project_name"] = str(project_name)
        if chat_id is not None:
            record["chat_id"] = int(chat_id)
        if status:
            record["status"] = str(status)
        if not record.get("latest_genspark_pid") and record.get("root_genspark_pid"):
            record["latest_genspark_pid"] = record["root_genspark_pid"]
        record["updated_at"] = _utc()
        data["projects"][key] = record

        alias_values = [record.get("root_genspark_pid"), record.get("latest_genspark_pid"), clean_root, clean_latest]
        for alias in alias_values:
            if alias and is_probable_project_id(alias):
                data["pid_to_key"][alias] = key

        _write_registry_index(data)
        return dict(record)


def remember_registry_identity(registry, **kwargs):
    if registry is None or not hasattr(registry, "remember_identity"):
        return None
    return registry.remember_identity(**kwargs)


# ══════════════════════════════════════════════════════════════
# 🗑️ [P26] Interactive Project Deletion & Atomic Cleanup
# ══════════════════════════════════════════════════════════════
# حذف مشروع محفوظ نهائياً بترتيب آمن (Fail-Safe Ordering):
#   1. حماية: منع الحذف لو المشروع له بناء نشط الآن (_ACTIVE_CANCEL_EVENTS).
#   2. الفهرس أولاً تحت REGISTRY_INDEX_LOCK (قيد المشروع + كل pid aliases).
#   3. شجرة التفريع projects_tree.json (مفتاحها root_pid وليس project_key).
#   4. أخيراً مجلد المشروع على القرص project_registry/<key>/ عبر rmtree.
# السبب: لو فشل rmtree بعد تنظيف الفهارس يبقى مجرد مجلد يتيم غير مرئي
# للنظام — أهون بكثير من قيد فهرس يشير لمجلد محذوف.


def is_project_build_active(project_key: str) -> bool:
    """فحص الحماية [P26]: هل للمشروع بناء نشط الآن (Event مسجل وغير مُلغى)؟"""
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        return False
    with _CANCEL_EVENTS_GUARD:
        for entry in _ACTIVE_CANCEL_EVENTS.values():
            if not isinstance(entry, dict):
                continue
            if str(entry.get("project_key") or "") == key and not entry["event"].is_set():
                return True
    return False


def _remove_project_from_tree_file(pids: list[str]) -> int:
    """إزالة قيود شجرة التفريع لمشروع محذوف — الشجرة مفتاحها root_pid.

    يُرجع عدد الجذور المحذوفة. كتابة ذرية (tmp ثم replace) كنمط save_project_tree.
    """
    clean_pids = [p for p in pids if p and is_probable_project_id(p)]
    if not clean_pids or not PROJECTS_TREE_FILE.exists():
        return 0
    try:
        with open(PROJECTS_TREE_FILE, "r", encoding="utf-8", errors="ignore") as f:
            tree_data = json.load(f)
    except Exception:
        return 0
    if not isinstance(tree_data, dict):
        return 0
    removed = 0
    for pid in clean_pids:
        if pid in tree_data:
            tree_data.pop(pid, None)
            removed += 1
    if not removed:
        return 0
    try:
        tmp_file = PROJECTS_TREE_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(PROJECTS_TREE_FILE)
    except Exception as err:
        log_event("warning", f"🗑️ [P26] تنبيه أثناء تنظيف شجرة التفريع: {err}")
        return 0
    return removed


def delete_project_atomically(project_key: str) -> dict:
    """الحذف الذري الشامل [P26] — يُرجع dict بالنتيجة دون رفع استثناءات.

    الترتيب الآمن: حماية التشغيل ➔ الفهرس (تحت القفل) ➔ الشجرة ➔ القرص.
    """
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    result = {
        "ok": False,
        "project_key": key,
        "project_name": "",
        "reason": "",
        "index_removed": False,
        "aliases_removed": 0,
        "tree_removed": 0,
        "disk_removed": False,
    }
    if not key:
        result["reason"] = "PROJECT_KEY_MISSING"
        return result

    # 1️⃣ فحص الحماية: ممنوع حذف مشروع له بناء شغال الآن
    if is_project_build_active(key):
        result["reason"] = "PROJECT_BUILD_ACTIVE"
        return result

    # 2️⃣ تنظيف الفهرس المركزي registry.json تحت القفل (القيد + كل aliases)
    project_pids: list[str] = []
    with REGISTRY_INDEX_LOCK:
        data = _read_registry_index()
        record = data["projects"].pop(key, None)
        if isinstance(record, dict):
            result["index_removed"] = True
            result["project_name"] = str(record.get("project_name") or "")
            for pid_field in ("root_genspark_pid", "latest_genspark_pid"):
                pid_value = str(record.get(pid_field) or "")
                if is_probable_project_id(pid_value) and pid_value not in project_pids:
                    project_pids.append(pid_value)
        stale_aliases = [pid for pid, mapped in data["pid_to_key"].items() if mapped == key]
        for pid in stale_aliases:
            data["pid_to_key"].pop(pid, None)
            if pid not in project_pids:
                project_pids.append(pid)
        result["aliases_removed"] = len(stale_aliases)
        if result["index_removed"] or stale_aliases:
            try:
                _write_registry_index(data)
            except Exception as err:
                log_event("error", f"🗑️ [P26] فشل كتابة registry index أثناء الحذف: {err}")
                result["reason"] = "INDEX_WRITE_FAILED"
                return result

    # 3️⃣ تنظيف شجرة التفريع (مفاتيحها root_pid — تُتخطى بأمان لو لا يوجد pid)
    result["tree_removed"] = _remove_project_from_tree_file(project_pids)

    # 4️⃣ حذف مجلد المشروع كاملاً من القرص project_registry/<key>/
    project_dir = PROJECT_REGISTRY_HOME / key
    if project_dir.exists() and project_dir.is_dir():
        try:
            shutil.rmtree(project_dir)
            result["disk_removed"] = True
        except Exception as err:
            log_event("error", f"🗑️ [P26] فشل حذف مجلد المشروع من القرص: {err}")
            result["reason"] = "DISK_REMOVE_FAILED"
            # الفهارس نظيفة بالفعل — الحذف منطقياً ناجح مع مجلد يتيم
            result["ok"] = bool(result["index_removed"])
            return result

    if not result["index_removed"] and not result["disk_removed"]:
        result["reason"] = "PROJECT_NOT_FOUND"
        return result

    result["ok"] = True
    log_event(
        "info",
        f"🗑️ [P26] تم حذف المشروع نهائياً: key={key} "
        f"(index={result['index_removed']}, aliases={result['aliases_removed']}, "
        f"tree={result['tree_removed']}, disk={result['disk_removed']})",
    )
    return result


def build_genspark_viewer_url(project_id: str | None) -> str:
    pid = extract_project_id(project_id) if project_id else ""
    if not is_probable_project_id(pid):
        return ""
    return f"https://www.genspark.ai/autopilotagent_viewer?id={pid}"


def build_viewer_url(project_id: str | None) -> str:
    """بناء رابط العارض السحابي مع ترميز المعرف بأمان"""
    clean_id = urllib.parse.quote(str(project_id or "").strip(), safe="")
    return f"https://www.genspark.ai/autopilotagent_viewer?id={clean_id}"


def build_live_preview_keyboard(project_id: str, status: str = "running", cancel_token: str | None = None) -> dict:
    """بناء Inline URL Button نظيف ومتوافق 100% مع جميع إصدارات تيليجرام.

    🛑 [P25] cancel_token اختياري (توافق خلفي كامل):
      - بدونه: نفس الكيبورد القديم حرفياً.
      - معه + status=running: صف ثانٍ بزر إلغاء أحمر (danger).
      - status=confirm_cancel: كيبورد تأكيد بخطوتي أمان (نعم أحمر / تراجع أزرق).
    """
    viewer_url = build_viewer_url(project_id)
    if status == "confirm_cancel" and cancel_token:
        # 🚨 خطوة التأكيد — منع الإلغاء الخاطئ بضغطة عفوية
        return make_inline_keyboard([
            [{"text": "🚨 نعم، إلغاء فوري", "callback_data": f"cancel_exec:{cancel_token}", "style": "danger"}],
            [{"text": "↩️ لا، تراجع واستمرار", "callback_data": f"cancel_abort:{cancel_token}", "style": "primary"}],
        ])
    if status == "running":
        # 🎨 أزرق (primary) أثناء البناء — Bot API 9.4 Button Styles
        rows = [[
            {"text": "🌐 ⚡ فتح المعاينة ومتابعة البناء لايف ↗️", "url": viewer_url, "style": "primary"}
        ]]
        if cancel_token:
            # 🛑 أحمر (danger) — الضغطة الأولى تفتح كيبورد التأكيد فقط (لا تلغي)
            rows.append([{"text": "🛑 إلغاء البناء الحالي", "callback_data": f"cancel_prompt:{cancel_token}", "style": "danger"}])
        return make_inline_keyboard(rows)
    else:
        # 🎨 أخضر (success) عند الاكتمال
        return make_inline_keyboard([[
            {"text": "🟢 فتح المشروع المكتمل ↗️", "url": viewer_url, "style": "success"}
        ]])


def summarize_project_context(identity: dict | None, current_pid: str | None = None, current_url: str | None = None) -> dict:
    identity = identity if isinstance(identity, dict) else {}
    root_pid = extract_project_id(identity.get("root_genspark_pid")) if identity.get("root_genspark_pid") else ""
    latest_pid = extract_project_id(identity.get("latest_genspark_pid")) if identity.get("latest_genspark_pid") else ""
    current_pid_clean = extract_project_id(current_pid) if current_pid else ""
    if not is_probable_project_id(root_pid):
        root_pid = ""
    if not is_probable_project_id(latest_pid):
        latest_pid = ""
    if not is_probable_project_id(current_pid_clean):
        current_pid_clean = latest_pid or root_pid
    latest_or_current = latest_pid or current_pid_clean or root_pid
    root_or_current = root_pid or current_pid_clean or latest_pid
    current_url_text = str(current_url or "").strip()
    if not current_url_text and current_pid_clean:
        current_url_text = build_genspark_viewer_url(current_pid_clean)
    resume_pid = latest_or_current or root_or_current
    resume_url = build_genspark_viewer_url(resume_pid) if resume_pid else current_url_text
    return {
        "root_pid": root_or_current,
        "latest_pid": latest_or_current,
        "current_pid": current_pid_clean or latest_or_current,
        "root_url": build_genspark_viewer_url(root_or_current),
        "current_url": current_url_text,
        "resume_pid": resume_pid,
        "resume_url": resume_url,
        "forked": bool(root_or_current and latest_or_current and root_or_current != latest_or_current),
    }


