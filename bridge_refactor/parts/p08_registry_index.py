"""[VERBATIM SLICE] p08_registry_index
المصدر: 01.31_telegram_gen_bridge.py — الأسطر 3383..3691
المحتوى: Project run locks + registry index I/O + identity + resume context + viewer URLs + live preview keyboard
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
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


def build_genspark_viewer_url(project_id: str | None) -> str:
    pid = extract_project_id(project_id) if project_id else ""
    if not is_probable_project_id(pid):
        return ""
    return f"https://www.genspark.ai/autopilotagent_viewer?id={pid}"


def build_viewer_url(project_id: str | None) -> str:
    """بناء رابط العارض السحابي مع ترميز المعرف بأمان"""
    clean_id = urllib.parse.quote(str(project_id or "").strip(), safe="")
    return f"https://www.genspark.ai/autopilotagent_viewer?id={clean_id}"


def build_live_preview_keyboard(project_id: str, status: str = "running") -> dict:
    """بناء Inline URL Button نظيف ومتوافق 100% مع جميع إصدارات تيليجرام"""
    viewer_url = build_viewer_url(project_id)
    if status == "running":
        # 🎨 أزرق (primary) أثناء البناء — Bot API 9.4 Button Styles
        return make_inline_keyboard([[
            {"text": "🌐 ⚡ فتح المعاينة ومتابعة البناء لايف ↗️", "url": viewer_url, "style": "primary"}
        ]])
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


