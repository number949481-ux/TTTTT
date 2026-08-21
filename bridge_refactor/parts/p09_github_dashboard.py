"""[VERBATIM SLICE] p09_github_dashboard
المصدر: 01.31_telegram_gen_bridge.py — الأسطر 3692..4863
المحتوى: GitHub inspection + dashboards + keyboards + project settings panels + finalize flows + resume decision + P19: copy_project_settings_to_new_project + generate_sequential_project_name + لوحة اختيار المصدر
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
def parse_github_repository_ref(text: str | None) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    patterns = [
        r"^(?:https?://)?github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?/?$",
        r"^git@github\.com:(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?$",
        r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, raw, re.IGNORECASE)
        if match:
            owner = str(match.group("owner") or "").strip()
            repo = str(match.group("repo") or "").strip()
            if owner and repo:
                return f"{owner}/{repo}"
    return ""


def build_github_api_headers(token: str | None = None) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    clean = str(token or "").strip()
    if clean:
        headers["Authorization"] = f"Bearer {clean}"
    return headers


def _extract_items_from_github_response(resp: dict) -> list:
    payload = resp.get("json") if isinstance(resp, dict) else resp
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("items") or payload.get("branches") or []
    return []


def _github_api_get_json(url: str, *, headers: dict, params: dict | None = None, timeout: int = 20, requester=None) -> dict:
    if requester is not None:
        return requester("GET", url, headers=headers, params=params, timeout=timeout)
    import requests
    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    try:
        payload = response.json()
    except Exception:
        payload = {}
    return {
        "status_code": int(getattr(response, "status_code", 0) or 0),
        "json": payload if isinstance(payload, (dict, list)) else {},
        "text": str(getattr(response, "text", "") or "")[:300],
    }


def inspect_github_repository(repo_ref: str, token: str | None = None, requester=None, inspector=None) -> dict:
    repository = parse_github_repository_ref(repo_ref)
    if not repository:
        return {
            "ok": False,
            "repository": "",
            "default_branch": "",
            "branches": [],
            "is_private": False,
            "used_token": False,
            "reason": "صيغة المستودع غير صالحة؛ استخدم owner/repo أو رابط GitHub مباشر.",
        }
    if inspector is not None:
        info = inspector(repository)
        if not isinstance(info, dict):
            return {"ok": False, "repository": repository, "default_branch": "", "branches": [], "is_private": False, "used_token": bool(token), "reason": "inspector returned non-dict"}
        branches = [str(x) for x in (info.get("branches") or []) if str(x).strip()][:500]
        default_branch = str(info.get("default_branch") or (branches[0] if branches else "")).strip()
        ok = bool(info.get("ok", bool(default_branch or branches)))
        return {
            "ok": ok,
            "repository": repository,
            "default_branch": default_branch,
            "branches": branches,
            "is_private": bool(info.get("is_private", False)),
            "used_token": bool(token),
            "reason": str(info.get("reason") or ""),
        }

    clean_token = str(token or "").strip() or get_default_github_token_from_env()
    headers = build_github_api_headers(clean_token)
    repo_resp = _github_api_get_json(
        f"https://api.github.com/repos/{repository}",
        headers=headers,
        requester=requester,
        timeout=20,
    )
    status_code = int(repo_resp.get("status_code") or 0)
    repo_payload = repo_resp.get("json") if isinstance(repo_resp.get("json"), dict) else {}
    if status_code != 200:
        if status_code in (401, 403):
            reason = "التوكن غير صالح أو لا يملك صلاحية كافية لفحص المستودع."
        elif status_code == 404:
            reason = "المستودع غير موجود أو خاص ويحتاج GitHub token صالح لهذا المشروع."
        else:
            reason = f"تعذر فحص المستودع الآن: HTTP_{status_code or 'UNKNOWN'}"
        return {
            "ok": False,
            "repository": repository,
            "default_branch": "",
            "branches": [],
            "is_private": False,
            "used_token": bool(clean_token),
            "reason": reason,
        }

    default_branch = str(repo_payload.get("default_branch") or "").strip()
    is_private = bool(repo_payload.get("private", False))
    branches = []
    seen_branches = set()
    page = 1
    max_pages = 50
    branch_status = 200

    while page <= max_pages:
        branches_resp = _github_api_get_json(
            f"https://api.github.com/repos/{repository}/branches",
            headers=headers,
            params={"per_page": 100, "page": page},
            requester=requester,
            timeout=20,
        )
        branch_status = int(branches_resp.get("status_code") or 0)
        if branch_status not in (0, 200):
            break
        items = _extract_items_from_github_response(branches_resp)
        if not items:
            break
        new_count = 0
        for item in items:
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                if name and name not in seen_branches:
                    seen_branches.add(name)
                    branches.append(name)
                    new_count += 1
        if len(items) < 100 or new_count == 0:
            break
        page += 1

    if default_branch and default_branch in branches:
        branches.remove(default_branch)
        branches.insert(0, default_branch)
    elif default_branch and default_branch not in branches:
        branches.insert(0, default_branch)

    if branch_status not in (0, 200):
        reason = f"تم الوصول للمستودع لكن تعذر جلب الفروع الآن: HTTP_{branch_status}"
    else:
        reason = ""
    return {
        "ok": bool(default_branch or branches),
        "repository": repository,
        "default_branch": default_branch,
        "branches": branches,
        "is_private": is_private,
        "used_token": bool(clean_token),
        "reason": reason,
    }


def configure_project_github_settings(
    project_key: str,
    *,
    enabled: bool,
    repository: str = "",
    branch: str = "",
    branch_mode: str = "disabled",
    detected_default_branch: str = "",
    available_branches: list[str] | None = None,
    repo_check_status: str = "",
    token: str | None = None,
) -> dict:
    registry = ProjectRegistry(project_key)
    if token is not None:
        if str(token).strip():
            registry.set_project_github_token(token)
        else:
            registry.clear_project_github_token()
    settings = {
        "github": {
            "configured": True,
            "enabled": bool(enabled),
            "repository": parse_github_repository_ref(repository) if enabled else "",
            "branch": str(branch or "").strip(),
            "branch_mode": str(branch_mode or ("manual" if branch else ("auto_default" if enabled else "disabled"))),
            "detected_default_branch": str(detected_default_branch or "").strip(),
            "available_branches": [str(x) for x in (available_branches or []) if str(x).strip()][:20],
            "last_repo_check_status": str(repo_check_status or ("checked" if enabled else "disabled")),
            "last_repo_check_at": _utc(),
        }
    }
    if not enabled:
        settings["github"]["branch"] = ""
        settings["github"]["branch_mode"] = "disabled"
        settings["github"]["detected_default_branch"] = ""
        settings["github"]["available_branches"] = []
    return registry.update_project_settings(settings)


def list_known_projects(chat_id: int | None = None, limit: int | None = None) -> list[dict]:
    with REGISTRY_INDEX_LOCK:
        data = _read_registry_index()
    projects = []
    for key, raw_record in (data.get("projects") or {}).items():
        record = _normalize_project_record(key, raw_record)
        if chat_id is not None and record.get("chat_id") != int(chat_id):
            continue
        projects.append(record)
    projects.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
    if limit is not None:
        projects = projects[:max(0, int(limit))]
    return projects


def get_latest_project_for_chat(chat_id: int) -> dict | None:
    projects = list_known_projects(chat_id=chat_id, limit=1)
    return projects[0] if projects else None


def get_project_dashboard_snapshot(project_key: str) -> dict:
    identity = get_project_identity_record(project_key) or {}
    registry = ProjectRegistry(project_key)
    manifest = registry._read()
    updates = manifest.get("updates") if isinstance(manifest.get("updates"), list) else []
    checkpoints = manifest.get("checkpoints") if isinstance(manifest.get("checkpoints"), list) else []
    queue_jobs = registry.list_upload_jobs()
    settings = registry.get_project_settings().get("github", {})
    latest_update = updates[-1] if updates else {}
    context = summarize_project_context(identity, current_pid=identity.get("latest_genspark_pid"), current_url=latest_update.get("url"))
    github_label = "غير مفعل"
    if settings.get("configured") and settings.get("enabled"):
        branch_label = settings.get("branch") or settings.get("detected_default_branch") or "auto-default"
        github_label = f"{settings.get('repository') or 'غير معروف'} @ {branch_label}"
    elif settings.get("configured"):
        github_label = "معطل لهذا المشروع"
    return {
        "project_key": project_key,
        "project_name": str(identity.get("project_name") or project_key),
        "status": str(identity.get("status") or latest_update.get("status") or "UNKNOWN"),
        "chat_id": identity.get("chat_id"),
        "updated_at": str(identity.get("updated_at") or manifest.get("updated_at") or ""),
        "updates_count": len(updates),
        "checkpoints_count": len(checkpoints),
        "queue_open_count": sum(1 for job in queue_jobs if str(job.get("state") or "") not in {"synced", "failed"}),
        "queue_total_count": len(queue_jobs),
        "latest_checkpoint": str((latest_update or {}).get("checkpoint") or ""),
        "latest_url": str((latest_update or {}).get("url") or context.get("resume_url") or ""),
        "root_pid": context.get("root_pid") or "",
        "latest_pid": context.get("latest_pid") or "",
        "resume_pid": context.get("resume_pid") or "",
        "resume_url": context.get("resume_url") or "",
        "github_label": github_label,
        "has_pid": bool(context.get("resume_pid")),
    }


def count_ready_accounts() -> int:
    accounts = read_accounts_safe()
    try:
        return len(get_eligible_accounts(accounts, set()))
    except Exception:
        return 0


def build_dashboard_snapshot(chat_id: int) -> dict:
    projects = list_known_projects(chat_id=chat_id)
    current = get_project_dashboard_snapshot(projects[0]["project_key"]) if projects else None
    running_keys = set(PROJECT_RUN_OWNERS.keys())
    running_for_chat = sum(1 for project in projects if project.get("project_key") in running_keys)
    queue_open = 0
    github_enabled = 0
    for project in projects:
        snap = get_project_dashboard_snapshot(project["project_key"])
        queue_open += snap["queue_open_count"]
        if "@" in snap["github_label"] or snap["github_label"].startswith("env:"):
            github_enabled += 1
    return {
        "projects_count": len(projects),
        "running_count": running_for_chat,
        "ready_accounts": count_ready_accounts(),
        "queue_open": queue_open,
        "github_enabled": github_enabled,
        "latest_project": current,
        "projects": projects,
    }


# 🎨 أنماط الألوان الرسمية لأزرار تيليجرام (Bot API 9.4 — Button Styles)
# القيم الوحيدة المسموحة رسمياً: primary (أزرق) / success (أخضر) / danger (أحمر)
# ⚠️ أي قيمة أخرى (positive/destructive/...) ترجع 400 invalid button style — لذلك الـ Whitelist صارمة
ALLOWED_BUTTON_STYLES = frozenset({"primary", "success", "danger"})


def make_inline_keyboard(rows: list[list[dict]] | None) -> dict:
    safe_rows = []
    for row in rows or []:
        if not isinstance(row, list):
            continue
        safe_buttons = []
        for button in row:
            if not isinstance(button, dict):
                continue
            text = str(button.get("text") or "").strip()
            callback_data = str(button.get("callback_data") or "").strip()
            url = str(button.get("url") or "").strip()
            if not text:
                continue
            if not callback_data and not url:
                continue
            safe_button = {"text": text}
            if callback_data:
                safe_button["callback_data"] = callback_data
            if url:
                safe_button["url"] = url
            # 🎨 حقل style الاختياري (Bot API 9.4): يمرر فقط لو كان ضمن الـ Whitelist الرسمية
            # لأننا نرسل reply_markup كـ JSON خام مباشرة، الحقل يصل لتيليجرام بدون أي مكتبة وسيطة
            style = str(button.get("style") or "").strip().lower()
            if style in ALLOWED_BUTTON_STYLES:
                safe_button["style"] = style
            safe_buttons.append(safe_button)
        if safe_buttons:
            safe_rows.append(safe_buttons)
    return {"inline_keyboard": safe_rows}


def render_dashboard_text(chat_id: int) -> str:
    snapshot = build_dashboard_snapshot(chat_id)
    latest = snapshot.get("latest_project") or {}
    latest_line = "لا يوجد بعد"
    if latest:
        latest_line = f"{latest.get('project_name')} / {latest.get('project_key')}"
    github_status = "✅" if snapshot.get("github_enabled") else "❌"
    return (
        f"🤖 <b>Genspark Multi-Project Bridge v{BUILD_VERSION}</b>\n\n"
        "📊 <b>الحالة</b>\n"
        f"• المشاريع المعروفة: <b>{snapshot.get('projects_count', 0)}</b>\n"
        f"• المهام الجارية: <b>{snapshot.get('running_count', 0)}</b>\n"
        f"• الحسابات الجاهزة: <b>{snapshot.get('ready_accounts', 0)}</b>\n"
        f"• Upload Queue المفتوحة: <b>{snapshot.get('queue_open', 0)}</b>\n"
        f"• GitHub للمشاريع: <b>{github_status}</b>\n"
        f"• آخر مشروع: <code>{html_escape(latest_line)}</code>\n\n"
        "💡 <b>دليل سريع</b>\n"
        "• مشروع جديد: يبدأ Wizard باسم مشروع ثم GitHub أو بدون GitHub.\n"
        "• مشاريعي: يعرض المشاريع المحفوظة كأزرار جاهزة للاستكمال.\n"
        "• المشروع الحالي: يعرض حالة آخر مشروع محفوظ من الـRegistry الحقيقية.\n"
        "• عند نفاد الرصيد: يحفظ checkpoint ثم يكمل بنفس مفتاح المشروع."
    )


def render_project_status_text(project_key: str) -> str:
    snap = get_project_dashboard_snapshot(project_key)
    settings = ProjectRegistry(project_key).get_project_settings()
    checkpoint_line = f"\n• آخر checkpoint: <code>{html_escape(snap['latest_checkpoint'])}</code>" if snap.get("latest_checkpoint") else ""
    resume_line = f"\n• رابط/سياق الاستئناف: {html_escape(snap['resume_url'])}" if snap.get("resume_url") else ""
    pid_line = f"\n• Latest PID: <code>{html_escape(snap['latest_pid'])}</code>" if snap.get("latest_pid") else ""
    root_line = f"\n• Root PID: <code>{html_escape(snap['root_pid'])}</code>" if snap.get("root_pid") else ""
    model_line = f"\n• الموديل: <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>"
    resume_prompt_line = f"\n• برومبت الاستئناف: <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>"
    return (
        f"⭐ <b>المشروع الحالي</b>\n"
        f"• الاسم: <b>{html_escape(snap['project_name'])}</b>\n"
        f"• المفتاح: <code>{html_escape(snap['project_key'])}</code>\n"
        f"• الحالة: <code>{html_escape(snap['status'])}</code>\n"
        f"• التحديثات: <b>{snap['updates_count']}</b>\n"
        f"• checkpoints الساخنة: <b>{snap['checkpoints_count']}</b>\n"
        f"• Upload Queue المفتوحة: <b>{snap['queue_open_count']}</b> من أصل <b>{snap['queue_total_count']}</b>{model_line}{resume_prompt_line}\n"
        f"• GitHub: <code>{html_escape(snap['github_label'])}</code>{checkpoint_line}{root_line}{pid_line}{resume_line}"
    )


def render_project_checkpoints_text(project_key: str) -> str:
    registry = ProjectRegistry(project_key)
    manifest = registry._read()
    checkpoint_ids = list(manifest.get("checkpoints") or [])[-3:]
    if not checkpoint_ids:
        return "🗂 <b>آخر 3 checkpoints</b>\nلا توجد checkpoints محفوظة بعد لهذا المشروع."
    lines = ["🗂 <b>آخر 3 checkpoints</b>"]
    for checkpoint_id in reversed(checkpoint_ids):
        record = registry.load_checkpoint_record(checkpoint_id) or {}
        summary = record.get("summary") or {}
        lines.append(
            f"• <code>{html_escape(checkpoint_id)}</code> — status=<code>{html_escape(str(record.get('status') or 'UNKNOWN'))}</code>"
            f" — A/M/D/U={summary.get('added', 0)}/{summary.get('modified', 0)}/{summary.get('deleted', 0)}/{summary.get('unchanged', 0)}"
        )
    return "\n".join(lines)


def render_project_archive_text(project_key: str) -> str:
    registry = ProjectRegistry(project_key)
    manifest = registry._read()
    updates = manifest.get("updates") or []
    latest = updates[-1] if updates else {}
    archive_ref = str(latest.get("archive_ref") or "")
    if not archive_ref:
        return "📦 <b>آخر Archive</b>\nلا يوجد archive محفوظ بعد لهذا المشروع."
    archive_path = registry.root / archive_ref
    return (
        "📦 <b>آخر Archive</b>\n"
        f"• المرجع: <code>{html_escape(archive_ref)}</code>\n"
        f"• المسار المحلي: <code>{html_escape(str(archive_path))}</code>\n"
        f"• موجود الآن: <b>{'نعم' if archive_path.exists() else 'لا'}</b>"
    )


def render_project_history_text(project_key: str) -> str:
    registry = ProjectRegistry(project_key)
    updates = list((registry._read().get("updates") or [])[-5:])
    if not updates:
        return "📜 <b>سجل التحديثات</b>\nلا توجد تحديثات محفوظة بعد لهذا المشروع."
    lines = ["📜 <b>سجل التحديثات</b>"]
    for item in reversed(updates):
        lines.append(
            f"• <code>{html_escape(str(item.get('at') or ''))}</code> — <code>{html_escape(str(item.get('status') or ''))}</code>"
            f" — checkpoint=<code>{html_escape(str(item.get('checkpoint') or '-'))}</code>"
        )
    return "\n".join(lines)


def render_project_file_report_text(project_key: str) -> str:
    registry = ProjectRegistry(project_key)
    updates = registry._read().get("updates") or []
    latest = updates[-1] if updates else {}
    checkpoint_id = str(latest.get("checkpoint") or "")
    record = registry.load_checkpoint_record(checkpoint_id) if checkpoint_id else None
    if not record:
        return "📁 <b>تقرير الملفات</b>\nلا يوجد checkpoint record صالح لعرض تفاصيل الملفات بعد."
    summary = record.get("summary") or {}
    files = list(record.get("files") or [])[:5]
    deleted = list(record.get("deleted_files") or [])[:5]
    lines = [
        "📁 <b>تقرير الملفات</b>",
        f"• checkpoint: <code>{html_escape(checkpoint_id)}</code>",
        f"• Added/Modified/Deleted/Unchanged = <b>{summary.get('added', 0)}/{summary.get('modified', 0)}/{summary.get('deleted', 0)}/{summary.get('unchanged', 0)}</b>",
    ]
    for item in files:
        lines.append(f"• {html_escape(str(item.get('classification') or 'FILE'))}: <code>{html_escape(str(item.get('path') or ''))}</code>")
    for item in deleted:
        lines.append(f"• DELETED: <code>{html_escape(str(item.get('path') or ''))}</code>")
    return "\n".join(lines)


def render_project_github_status_text(project_key: str) -> str:
    registry = ProjectRegistry(project_key)
    settings = registry.get_project_settings().get("github", {})
    jobs = registry.list_upload_jobs()
    if settings.get("configured"):
        mode = "مفعل" if settings.get("enabled") else "معطل"
        branch = settings.get("branch") or settings.get("detected_default_branch") or "auto-default"
        repo = settings.get("repository") or "غير معروف"
    else:
        mode = "غير مفعّل"
        branch = "—"
        repo = "—"
    queued = [job for job in jobs if str(job.get("state") or "") != "synced"]
    synced = [job for job in jobs if str(job.get("state") or "") == "synced"]
    last_states = ", ".join(str(job.get("state") or "") for job in jobs[:4]) or "لا يوجد"
    if queued:
        status_note = "• تم إنشاء job أو أكثر للرفع، لكن لم يتم تأكيد اكتمال الرفع بعد. الحالات <code>pending/uploading/retrying</code> تعني جدولة أو تنفيذ جارٍ فقط."
    elif synced:
        status_note = "• آخر jobs المسجلة لهذه اللقطة وصلت إلى حالة <code>synced</code>."
    else:
        status_note = "• لا توجد jobs GitHub محفوظة بعد لهذا المشروع."
    return (
        "🔗 <b>حالة GitHub</b>\n"
        f"• النمط: <code>{html_escape(mode)}</code>\n"
        f"• المستودع: <code>{html_escape(str(repo))}</code>\n"
        f"• الفرع: <code>{html_escape(str(branch))}</code>\n"
        f"• jobs المفتوحة: <b>{len(queued)}</b> من أصل <b>{len(jobs)}</b>\n"
        f"• آخر حالات queue: <code>{html_escape(last_states)}</code>\n"
        f"{status_note}"
    )


def render_project_settings_text(project_key: str) -> str:
    identity = get_project_identity_record(project_key) or {}
    registry = ProjectRegistry(project_key)
    settings = registry.get_project_settings()
    github = settings.get("github", {})
    repo = github.get("repository") or "—"
    branch = github.get("branch") or github.get("detected_default_branch") or "—"
    branch_mode = github.get("branch_mode") or "disabled"
    github_mode = "مفعل" if github.get("enabled") else ("معطل" if github.get("configured") else "غير مضبوط")
    token_status = "موجود" if github.get("token_present") else "غير محفوظ"
    check_status = github.get("last_repo_check_status") or "—"
    check_at = github.get("last_repo_check_at") or "—"
    return (
        "⚙️ <b>إعدادات المشروع</b>\n"
        f"• الاسم: <b>{html_escape(str(identity.get('project_name') or project_key))}</b>\n"
        f"• المفتاح: <code>{html_escape(project_key)}</code>\n"
        f"• الموديل: <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n"
        f"• برومبت الاستئناف: <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>\n"
        f"• GitHub: <code>{html_escape(github_mode)}</code>\n"
        f"• المستودع: <code>{html_escape(str(repo))}</code>\n"
        f"• الفرع: <code>{html_escape(str(branch))}</code>\n"
        f"• branch mode: <code>{html_escape(str(branch_mode))}</code>\n"
        f"• token للمشروع: <code>{html_escape(token_status)}</code>\n"
        f"• آخر repo check: <code>{html_escape(str(check_status))}</code>\n"
        f"• وقت آخر check: <code>{html_escape(str(check_at))}</code>"
    )


def render_project_resume_summary_text(project_key: str, *, target_url: str = "", target_pid: str = "") -> str:
    identity = get_project_identity_record(project_key) or {}
    registry = ProjectRegistry(project_key)
    settings = registry.get_project_settings()
    github = settings.get("github", {})
    repo = github.get("repository") or "—"
    branch = github.get("branch") or github.get("detected_default_branch") or "—"
    github_mode = "مفعل" if github.get("enabled") else ("معطل" if github.get("configured") else "غير مضبوط")
    public_resume_prompt = settings.get("continuation", {}).get("prompt") or DEFAULT_PROJECT_RESUME_PROMPT
    pid_value = extract_project_id(target_url) if target_url else ""
    if not pid_value:
        pid_value = str(target_pid or identity.get("latest_genspark_pid") or identity.get("root_genspark_pid") or "")
    resume_line = f"\n• رابط الاستئناف: {html_escape(target_url)}" if target_url else ""
    pid_line = f"\n• Project ID الحالي: <code>{html_escape(pid_value)}</code>" if pid_value else ""
    next_step = "يمكنك المتابعة الآن مباشرة أو تعديل الإعدادات أولاً بدون إعادة Wizard كاملة."
    if not target_url:
        next_step = "هذا المشروع لا يملك رابط استئناف محفوظاً بعد؛ يمكنك تعديل الإعدادات أو إرسال أول prompt لبدءه بنفس المفتاح."
    return (
        "🔄 <b>ملخص الاستئناف</b>\n"
        f"• الاسم: <b>{html_escape(str(identity.get('project_name') or project_key))}</b>\n"
        f"• المفتاح: <code>{html_escape(project_key)}</code>\n"
        f"• الموديل: <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n"
        f"• برومبت الاستئناف: <code>{html_escape(public_resume_prompt)}</code>\n"
        f"• GitHub: <code>{html_escape(github_mode)}</code>\n"
        f"• المستودع: <code>{html_escape(str(repo))}</code>\n"
        f"• الفرع: <code>{html_escape(str(branch))}</code>{pid_line}{resume_line}\n\n"
        f"{next_step}"
    )


def build_project_settings_keyboard(project_key: str) -> dict:
    github = ProjectRegistry(project_key).get_project_settings().get("github", {})
    toggle_label = "🚫 تعطيل GitHub" if github.get("enabled") else "✅ تفعيل GitHub"
    return make_inline_keyboard([
        [{"text": "🧠 تعديل الموديل", "callback_data": f"pset:model:{project_key}"}, {"text": "✍️ تعديل برومبت الاستئناف", "callback_data": f"pset:resume:{project_key}"}],
        [{"text": "🔗 تعديل المستودع", "callback_data": f"pset:repo:{project_key}"}, {"text": "🌿 تعديل الـbranch", "callback_data": f"pset:branch:{project_key}"}],
        [{"text": "🔑 تحديث GitHub token", "callback_data": f"pset:token:{project_key}"}, {"text": toggle_label, "callback_data": f"pset:toggle:{project_key}"}],
        [{"text": "⭐ رجوع لتفاصيل المشروع", "callback_data": f"pview:{project_key}"}, {"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def build_project_resume_summary_keyboard(project_key: str, *, target_url: str = "", target_pid: str = "") -> dict:
    rows = [
        [{"text": "▶️ كمل الآن", "callback_data": "cmd:resume_continue", "style": "success"}, {"text": "⚙️ عدّل الإعدادات", "callback_data": "cmd:resume_settings"}],
    ]
    if target_url:
        rows.append([{"text": "🌐 فتح المشروع", "url": target_url}])
    if target_pid:
        rows.append([{"text": "🌳 نقاط الاستئناف", "callback_data": f"tree:{target_pid}"}])
    rows.append([{"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"}, {"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}])
    return make_inline_keyboard(rows)


def build_unbound_resume_keyboard() -> dict:
    return make_inline_keyboard([
        [{"text": "📌 اربطه كمشروع محفوظ", "callback_data": "cmd:resume_bind_saved"}],
        [{"text": "⚡ استئناف سريع بدون حفظ", "callback_data": "cmd:resume_quick_continue"}],
        [{"text": "📋 نسخ إعدادات من مشروع آخر", "callback_data": "cmd:resume_copy_settings"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def build_copy_settings_source_keyboard(chat_id: int, *, limit: int = 8) -> dict:
    """[P19] قائمة المشاريع المحفوظة كأزرار لاختيار المشروع المصدر لنسخ إعداداته."""
    rows = []
    for record in list_known_projects(chat_id=chat_id, limit=limit):
        label = str(record.get("project_name") or record.get("project_key") or "مشروع")[:32]
        rows.append([{"text": f"📋 {label}", "callback_data": f"cpysrc:{record['project_key']}"}])
    rows.append([
        {"text": "⬅️ رجوع", "callback_data": "cmd:resume_copy_back"},
        {"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"},
    ])
    return make_inline_keyboard(rows)


def build_bound_project_github_choice_keyboard() -> dict:
    return make_inline_keyboard([
        [{"text": "🔗 ربط GitHub لهذا المشروع الخارجي", "callback_data": "cmd:bound_proj_github_yes"}],
        [{"text": "➡️ المتابعة بدون GitHub", "callback_data": "cmd:bound_proj_github_no"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def build_bound_project_resume_prompt_keyboard() -> dict:
    return make_inline_keyboard([
        [{"text": "✅ استخدم «تابع» الافتراضية", "callback_data": "cmd:bound_proj_resume_default"}],
        [{"text": "✍️ أدخل برومبت استئناف مخصص", "callback_data": "cmd:bound_proj_resume_custom"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def present_resume_summary(chat_id: int, *, project_key: str, target_url: str = "", target_pid: str = "") -> bool:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        return False
    identity = get_project_identity_record(key) or {}
    project_name = str(identity.get("project_name") or key)
    project_model = get_project_selected_model(key)
    pid_value = extract_project_id(target_url) if target_url else ""
    if not pid_value:
        pid_value = str(target_pid or identity.get("latest_genspark_pid") or identity.get("root_genspark_pid") or "")
    set_user_state(chat_id, {
        "action": "AWAITING_PROJECT_RESUME_DECISION",
        "project_key": key,
        "project_name": project_name,
        "project_model": project_model,
        "url": target_url,
        "pid": pid_value,
    })
    send_telegram_message(
        chat_id,
        render_project_resume_summary_text(key, target_url=target_url, target_pid=pid_value),
        reply_markup=build_project_resume_summary_keyboard(key, target_url=target_url, target_pid=pid_value),
    )
    return True


def send_project_settings_panel(chat_id: int, project_key: str, prefix: str = "") -> None:
    body = render_project_settings_text(project_key)
    message = f"{prefix}\n\n{body}" if prefix else body
    send_telegram_message(chat_id, message, reply_markup=build_project_settings_keyboard(project_key))


def run_project_upload_control(project_key: str, action: str) -> str:
    registry = ProjectRegistry(project_key)
    dest = registry._github_destination()
    if not dest:
        return "⚠️ <b>GitHub غير مفعّل لهذا المشروع حالياً.</b>\nفعّل إعداد GitHub أولاً من Wizard المشروع الجديد أو استخدم الإعداد المحفوظ."
    if action == "sync":
        result = registry.process_next_upload_job()
        state = str(result.get("state") or "no-due-job")
        return (
            "📤 <b>مزامنة الآن</b>\n"
            f"• النتيجة: <code>{html_escape(state)}</code>\n"
            f"• job: <code>{html_escape(str(result.get('job_id') or '-'))}</code>"
        )
    if action == "retry":
        recovered = registry.recover_upload_queue_after_restart()
        result = registry.process_next_upload_job()
        state = str(result.get("state") or "no-due-job")
        return (
            "🔁 <b>إعادة محاولة الرفع</b>\n"
            f"• jobs المعاد تجهيزها: <b>{len(recovered)}</b>\n"
            f"• النتيجة الحالية: <code>{html_escape(state)}</code>\n"
            f"• job: <code>{html_escape(str(result.get('job_id') or '-'))}</code>"
        )
    if action == "pause":
        return "⏸ <b>إيقاف مؤقت</b>\nلا يوجد worker دائم مستقل لكل مشروع حالياً داخل 01.15، لذلك هذا الزر يوضّح فقط أن الإيقاف المؤقت التشغيلي سيأتي لاحقاً دون الادعاء بتنفيذ غير موجود."
    if action == "cancel":
        return "❌ <b>إلغاء</b>\nلا يوجد عقد إلغاء آمن لمهمة جارية داخل 01.15 الحالية، لذلك لا يتم قتل أي process من هذا الزر. استخدمه لاحقاً بعد إغلاق TSK مخصصة لذلك."
    return "ℹ️ تحكم غير معروف."


def build_current_project_keyboard(project_key: str) -> dict:
    snap = get_project_dashboard_snapshot(project_key)
    rows = []
    if snap.get("resume_url"):
        rows.append([{"text": "🌐 فتح المشروع", "url": snap["resume_url"]}])
    rows.append([
        {"text": "🔄 استئناف هذا المشروع", "callback_data": f"proj:{project_key}"},
        {"text": "⚙️ إعدادات المشروع", "callback_data": f"pset:view:{project_key}"},
    ])
    rows.append([
        {"text": "🗂 آخر 3 checkpoints", "callback_data": f"pctl:checkpoints:{project_key}"},
        {"text": "📦 آخر Archive", "callback_data": f"pctl:archive:{project_key}"},
    ])
    rows.append([
        {"text": "📁 تقرير الملفات", "callback_data": f"pctl:files:{project_key}"},
        {"text": "📜 سجل التحديثات", "callback_data": f"pctl:history:{project_key}"},
    ])
    rows.append([
        {"text": "🔗 حالة GitHub", "callback_data": f"pctl:gh:{project_key}"},
        {"text": "📤 مزامنة الآن", "callback_data": f"pctl:sync:{project_key}"},
    ])
    rows.append([
        {"text": "🔁 إعادة محاولة الرفع", "callback_data": f"pctl:retry:{project_key}"},
        {"text": "⏸ إيقاف مؤقت", "callback_data": f"pctl:pause:{project_key}"},
        {"text": "❌ إلغاء", "callback_data": f"pctl:cancel:{project_key}", "style": "danger"},
    ])
    if snap.get("resume_pid"):
        rows.append([{"text": "🌳 نقاط الاستئناف", "callback_data": f"tree:{snap['resume_pid']}"}])
    rows.append([{"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"}, {"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}])
    return make_inline_keyboard(rows)


def build_dashboard_keyboard(chat_id: int) -> dict:
    rows = [
        [{"text": "🚀 مشروع جديد", "callback_data": "cmd:new_proj", "style": "primary"}, {"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"}],
        [{"text": "🔄 استئناف مشروع", "callback_data": "cmd:cont_proj"}, {"text": "⭐ المشروع الحالي", "callback_data": "cmd:current_project"}],
        [{"text": "🌳 نقاط الاستئناف", "callback_data": "cmd:list_tree"}, {"text": "📊 فحص الحسابات والكريدت", "callback_data": "cmd:check_accs"}],
    ]
    for record in list_known_projects(chat_id=chat_id, limit=3):
        label = str(record.get("project_name") or record.get("project_key") or "مشروع")[:24]
        rows.append([
            {"text": f"📌 {label}", "callback_data": f"proj:{record['project_key']}"},
            {"text": "⭐ التفاصيل", "callback_data": f"pview:{record['project_key']}"},
        ])
    return make_inline_keyboard(rows)


def build_project_model_keyboard(*, back_callback: str = "cmd:show_dashboard", back_label: str = "⬅️ رجوع للوحة التحكم") -> dict:
    rows = []
    for model_name in AVAILABLE_MODELS:
        rows.append([{"text": f"🧠 {model_name}", "callback_data": f"cmd:new_proj_model:{model_name}"}])
    rows.append([{"text": back_label, "callback_data": back_callback}])
    return make_inline_keyboard(rows)


def build_new_project_model_keyboard(*, back_callback: str = "cmd:show_dashboard", back_label: str = "⬅️ رجوع للوحة التحكم") -> dict:
    return build_project_model_keyboard(back_callback=back_callback, back_label=back_label)


def build_new_project_github_choice_keyboard() -> dict:
    return make_inline_keyboard([
        [{"text": "🔗 ربط GitHub لهذا المشروع", "callback_data": "cmd:new_proj_github_yes"}],
        [{"text": "➡️ المتابعة بدون GitHub", "callback_data": "cmd:new_proj_github_no"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def format_github_repo_inspection_summary(repository: str, default_branch: str, branches: list[str]) -> str:
    lines = [
        f"✅ <b>تم فحص المستودع:</b> <code>{html_escape(repository)}</code>",
        f"<b>Default branch:</b> <code>{html_escape(default_branch or 'غير معروف')}</code>",
        "",
        "<b>🌿 Branches المكتشفة (اضغط للنسخ):</b>",
    ]
    if branches:
        for b in branches[:8]:
            tag = " 🌟 (الافتراضي)" if b == default_branch else ""
            lines.append(f"  • <code>{html_escape(b)}</code>{tag}")
    else:
        lines.append("  • <code>لا توجد فروع مكتشفة</code>")
    lines.append("\nاختر الفرع مباشرة من الأزرار بالأسفل، أو أدخله يدوياً:")
    return "\n".join(lines)


def build_project_branch_choice_keyboard(
    default_callback: str,
    manual_callback: str,
    *,
    branches: list[str] | None = None,
    branch_prefix: str = "",
    default_branch: str = "",
    back_callback: str = "",
    back_label: str = "⬅️ رجوع",
    disable_callback: str = "",
    disable_label: str = "➡️ كمّل بدون GitHub",
) -> dict:
    rows = []
    if branches and branch_prefix:
        for b in branches[:6]:
            tag = " 🌟 (افتراضي)" if b == default_branch else ""
            rows.append([{"text": f"🌿 {b}{tag}", "callback_data": f"{branch_prefix}{b}"}])
    else:
        rows.append([{"text": "✅ استخدم الـ default branch المكتشف", "callback_data": default_callback}])
    rows.append([{"text": "✍️ أريد تحديد branch يدويًا", "callback_data": manual_callback}])
    if disable_callback:
        rows.append([{"text": disable_label, "callback_data": disable_callback}])
    if back_callback:
        rows.append([{"text": back_label, "callback_data": back_callback}])
    return make_inline_keyboard(rows)


def build_new_project_branch_choice_keyboard(branches: list[str] | None = None, default_branch: str = "") -> dict:
    return build_project_branch_choice_keyboard(
        "cmd:new_proj_branch_default",
        "cmd:new_proj_branch_manual",
        branches=branches,
        branch_prefix="cmd:new_proj_branch_pick:",
        default_branch=default_branch,
        back_callback="cmd:show_dashboard",
        back_label="⬅️ رجوع للوحة التحكم",
        disable_callback="cmd:new_proj_github_disable",
    )


def build_existing_project_branch_choice_keyboard(project_key: str, branches: list[str] | None = None, default_branch: str = "") -> dict:
    return build_project_branch_choice_keyboard(
        f"pset:branch_default:{project_key}",
        f"pset:branch_manual:{project_key}",
        branches=branches,
        branch_prefix=f"pset:branch_pick:{project_key}:",
        default_branch=default_branch,
        back_callback=f"pset:view:{project_key}",
        back_label="⬅️ رجوع لإعدادات المشروع",
    )


def build_bound_project_branch_choice_keyboard(branches: list[str] | None = None, default_branch: str = "") -> dict:
    return build_project_branch_choice_keyboard(
        "cmd:bound_proj_branch_default",
        "cmd:bound_proj_branch_manual",
        branches=branches,
        branch_prefix="cmd:bound_proj_branch_pick:",
        default_branch=default_branch,
        back_callback="cmd:show_dashboard",
        back_label="⬅️ رجوع للوحة التحكم",
        disable_callback="cmd:bound_proj_github_disable",
    )


def build_new_project_resume_prompt_keyboard() -> dict:
    return make_inline_keyboard([
        [{"text": "✅ استخدم «تابع» الافتراضية", "callback_data": "cmd:new_proj_resume_default"}],
        [{"text": "✍️ أدخل برومبت استئناف مخصص", "callback_data": "cmd:new_proj_resume_custom"}],
        [{"text": "⬅️ رجوع للوحة التحكم", "callback_data": "cmd:show_dashboard"}],
    ])


def get_project_selected_model(project_key: str | None) -> str:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        return DEFAULT_PROJECT_MODEL
    return ProjectRegistry(key).get_project_settings().get("model") or DEFAULT_PROJECT_MODEL


def finalize_new_project_setup(
    project_key: str,
    project_name: str,
    *,
    model: str,
    resume_prompt: str,
    chat_id: int,
    github_enabled: bool,
    repository: str = "",
    branch: str = "",
    branch_mode: str = "disabled",
    detected_default_branch: str = "",
    available_branches: list[str] | None = None,
    repo_check_status: str = "",
    token: str | None = None,
) -> dict:
    upsert_project_identity(project_key, project_name=project_name, chat_id=chat_id, status="DRAFT")
    registry = ProjectRegistry(project_key)
    registry.set_project_model(model)
    registry.set_project_resume_prompt(resume_prompt)
    configure_project_github_settings(
        project_key,
        enabled=github_enabled,
        repository=repository,
        branch=branch,
        branch_mode=branch_mode,
        detected_default_branch=detected_default_branch,
        available_branches=available_branches,
        repo_check_status=repo_check_status,
        token=token,
    )
    return registry.get_project_settings()


def finalize_new_project_from_state(state: dict, chat_id: int, resume_prompt: str | None = None) -> tuple[dict, dict]:
    project_key = str(state.get("project_key") or "")
    project_name = str(state.get("project_name") or "")
    project_model = normalize_project_model(state.get("project_model"))
    github_enabled = bool(state.get("pending_github_enabled", False))
    repository = str(state.get("pending_github_repository") or "")
    token = str(state.get("pending_github_token") or "") if github_enabled else ""
    branch = str(state.get("pending_github_branch") or "")
    branch_mode = str(state.get("pending_github_branch_mode") or ("manual" if branch else ("auto_default" if github_enabled else "disabled")))
    detected_default_branch = str(state.get("pending_github_default_branch") or "")
    available_branches = list(state.get("pending_github_branches") or [])
    repo_check_status = str(state.get("pending_github_repo_check_status") or ("disabled" if not github_enabled else "checked"))
    effective_resume = normalize_project_resume_prompt(resume_prompt if resume_prompt is not None else state.get("pending_resume_prompt"))
    settings = finalize_new_project_setup(
        project_key,
        project_name,
        model=project_model,
        resume_prompt=effective_resume,
        chat_id=chat_id,
        github_enabled=github_enabled,
        repository=repository,
        branch=branch,
        branch_mode=branch_mode,
        detected_default_branch=detected_default_branch,
        available_branches=available_branches,
        repo_check_status=repo_check_status,
        token=token if github_enabled else None,
    )
    next_state = {
        "action": "AWAITING_NEW_PROMPT",
        "project_key": project_key,
        "project_name": project_name,
        "project_model": project_model,
    }
    return settings, next_state


PROJECT_SETTINGS_TOKEN_UNSET = object()


def update_existing_project_github_settings(
    project_key: str,
    *,
    enabled: bool | None = None,
    repository: str | None = None,
    branch: str | None = None,
    branch_mode: str | None = None,
    detected_default_branch: str | None = None,
    available_branches: list[str] | None = None,
    repo_check_status: str | None = None,
    token=PROJECT_SETTINGS_TOKEN_UNSET,
) -> dict:
    registry = ProjectRegistry(project_key)
    current = registry.get_project_settings().get("github", {})
    if token is not PROJECT_SETTINGS_TOKEN_UNSET:
        if str(token or "").strip():
            registry.set_project_github_token(str(token))
        else:
            registry.clear_project_github_token()
    repo_value = parse_github_repository_ref(repository) if repository is not None else str(current.get("repository") or "").strip()
    configured = bool(
        current.get("configured")
        or current.get("repository")
        or current.get("token_present")
        or repo_value
        or (token is not PROJECT_SETTINGS_TOKEN_UNSET and str(token or "").strip())
        or current.get("enabled")
        or enabled
    )
    patch = {"github": {"configured": configured}}
    if enabled is not None:
        patch["github"]["enabled"] = bool(enabled)
    if repository is not None:
        patch["github"]["repository"] = repo_value
    if branch is not None:
        patch["github"]["branch"] = str(branch or "").strip()
    if branch_mode is not None:
        patch["github"]["branch_mode"] = str(branch_mode or "").strip()
    if detected_default_branch is not None:
        patch["github"]["detected_default_branch"] = str(detected_default_branch or "").strip()
    if available_branches is not None:
        patch["github"]["available_branches"] = [str(x).strip() for x in (available_branches or []) if str(x).strip()][:20]
    if repo_check_status is not None:
        patch["github"]["last_repo_check_status"] = str(repo_check_status or "").strip()
    if len(patch["github"]) > 1 or token is not PROJECT_SETTINGS_TOKEN_UNSET:
        patch["github"]["last_repo_check_at"] = _utc()
    return registry.update_project_settings(patch)


def finalize_existing_project_github_from_state(
    state: dict,
    *,
    branch: str | None = None,
    branch_mode: str | None = None,
    repo_check_status: str | None = None,
) -> dict:
    token_value = state["pending_github_token"] if "pending_github_token" in state else PROJECT_SETTINGS_TOKEN_UNSET
    resolved_branch = str(branch if branch is not None else state.get("pending_github_branch") or "").strip()
    resolved_branch_mode = str(
        branch_mode
        if branch_mode is not None
        else state.get("pending_github_branch_mode") or ("manual" if resolved_branch else "auto_default")
    ).strip()
    return update_existing_project_github_settings(
        str(state.get("project_key") or ""),
        enabled=bool(state.get("pending_github_enabled", False)),
        repository=str(state.get("pending_github_repository") or ""),
        branch=resolved_branch,
        branch_mode=resolved_branch_mode,
        detected_default_branch=str(state.get("pending_github_default_branch") or ""),
        available_branches=list(state.get("pending_github_branches") or []),
        repo_check_status=str(repo_check_status if repo_check_status is not None else state.get("pending_github_repo_check_status") or ""),
        token=token_value,
    )


def present_external_resume_decision(chat_id: int, *, target_url: str, target_pid: str = "") -> bool:
    pid_value = str(target_pid or extract_project_id(target_url) or "")
    set_user_state(chat_id, {
        "action": "AWAITING_UNBOUND_RESUME_DECISION",
        "url": target_url,
        "pid": pid_value,
    })
    pid_line = f"\n<b>Project ID:</b> <code>{html_escape(pid_value)}</code>" if pid_value else ""
    url_line = f"\n<b>الرابط:</b> {html_escape(target_url)}" if target_url else ""
    send_telegram_message(
        chat_id,
        f"🔗 <b>تم اكتشاف مشروع غير محفوظ بعد.</b>{pid_line}{url_line}\nيمكنك استئنافه سريعاً بدون حفظ، أو ربطه أولاً كمشروع محفوظ بإعدادات كاملة.",
        reply_markup=build_unbound_resume_keyboard(),
    )
    return True


def finalize_bound_external_project_from_state(state: dict, chat_id: int, resume_prompt: str | None = None) -> tuple[dict, dict]:
    project_key = str(state.get("project_key") or "")
    project_name = str(state.get("project_name") or "")
    project_model = normalize_project_model(state.get("project_model"))
    github_enabled = bool(state.get("pending_github_enabled", False))
    repository = str(state.get("pending_github_repository") or "")
    token = str(state.get("pending_github_token") or "") if github_enabled else ""
    branch = str(state.get("pending_github_branch") or "")
    branch_mode = str(state.get("pending_github_branch_mode") or ("manual" if branch else ("auto_default" if github_enabled else "disabled")))
    detected_default_branch = str(state.get("pending_github_default_branch") or "")
    available_branches = list(state.get("pending_github_branches") or [])
    repo_check_status = str(state.get("pending_github_repo_check_status") or ("disabled" if not github_enabled else "checked"))
    effective_resume = normalize_project_resume_prompt(resume_prompt if resume_prompt is not None else state.get("pending_resume_prompt"))
    target_url = str(state.get("url") or "")
    target_pid = str(state.get("pid") or extract_project_id(target_url) or "")
    settings = finalize_new_project_setup(
        project_key,
        project_name,
        model=project_model,
        resume_prompt=effective_resume,
        chat_id=chat_id,
        github_enabled=github_enabled,
        repository=repository,
        branch=branch,
        branch_mode=branch_mode,
        detected_default_branch=detected_default_branch,
        available_branches=available_branches,
        repo_check_status=repo_check_status,
        token=token if github_enabled else None,
    )
    if target_pid:
        upsert_project_identity(
            project_key,
            root_pid=target_pid,
            latest_pid=target_pid,
            project_name=project_name,
            chat_id=chat_id,
            status="RESUME_REQUESTED",
        )
    next_state = {
        "action": "AWAITING_CONT_PROMPT",
        "url": target_url,
        "project_key": project_key,
        "project_name": project_name,
        "project_model": project_model,
        "pid": target_pid,
    }
    return settings, next_state


def generate_sequential_project_name(base_name: str, chat_id: int | None = None) -> str:
    """[P19] توليد اسم تسلسلي فريد: «الحج 1» ➔ «الحج 2» ➔ «الحج 3» تلقائياً.

    - يفصل الرقم الذيلي عن الجذر إن وُجد («الحج 1» ➔ جذر «الحج»).
    - يفحص كل المشاريع المعروفة ويحسب أعلى رقم مستخدم لنفس الجذر.
    - يعيد الجذر + (أعلى رقم + 1). لو الجذر غير مستخدم إطلاقاً يعيده كما هو.
    """
    clean = re.sub(r"\s+", " ", str(base_name or "")).strip()[:60] or "مشروع"
    match = re.match(r"^(.*?)\s*(\d+)$", clean)
    root = (match.group(1).strip() if match else clean) or clean
    existing_names = set()
    for record in list_known_projects(chat_id=chat_id):
        name = re.sub(r"\s+", " ", str(record.get("project_name") or "")).strip()
        if name:
            existing_names.add(name)
    if clean not in existing_names and not match:
        return clean
    max_index = 0
    root_used = False
    for name in existing_names:
        if name == root:
            root_used = True
            max_index = max(max_index, 1)
            continue
        m = re.match(r"^(.*?)\s*(\d+)$", name)
        if m and m.group(1).strip() == root:
            root_used = True
            try:
                max_index = max(max_index, int(m.group(2)))
            except Exception:
                pass
    if not root_used and clean not in existing_names:
        return clean
    return f"{root} {max_index + 1}"[:60]


def copy_project_settings_to_new_project(
    source_project_key: str,
    chat_id: int,
    *,
    target_url: str = "",
    target_pid: str = "",
) -> dict:
    """[P19] نسخ إعدادات مشروع محفوظ (GitHub + الموديل + برومبت الاستئناف) لمشروع جديد.

    - يقرأ إعدادات المصدر من ProjectRegistry (بما فيها token من المخزن السري للمشروع فقط
      بدون fallback على متغيرات البيئة حتى لا تتسرب أسرار عامة لمشروع خاص).
    - ينشئ مفتاحاً جديداً واسم تسلسلي فريد («الحج 1» ➔ «الحج 2»).
    - يعيد dict كامل: project_key/project_name/settings/source_name.
    """
    source_key = re.sub(r"[^A-Za-z0-9_-]", "_", str(source_project_key or ""))[:80]
    if not source_key:
        return {"ok": False, "reason": "مفتاح المشروع المصدر غير صالح"}
    source_identity = get_project_identity_record(source_key) or {}
    source_name = str(source_identity.get("project_name") or source_key)
    registry = ProjectRegistry(source_key)
    settings = registry.get_project_settings()
    github = settings.get("github", {}) if isinstance(settings.get("github"), dict) else {}
    source_token = registry.get_project_github_token(allow_env_fallback=False)
    github_enabled = bool(github.get("enabled"))
    new_project_key = f"prj_{uuid.uuid4().hex[:16]}"
    new_project_name = generate_sequential_project_name(source_name, chat_id=chat_id)
    new_settings = finalize_new_project_setup(
        new_project_key,
        new_project_name,
        model=normalize_project_model(settings.get("model")),
        resume_prompt=normalize_project_resume_prompt((settings.get("continuation") or {}).get("prompt")),
        chat_id=chat_id,
        github_enabled=github_enabled,
        repository=str(github.get("repository") or ""),
        branch=str(github.get("branch") or ""),
        branch_mode=str(github.get("branch_mode") or ("disabled" if not github_enabled else "auto_default")),
        detected_default_branch=str(github.get("detected_default_branch") or ""),
        available_branches=list(github.get("available_branches") or []),
        repo_check_status=str(github.get("last_repo_check_status") or ("disabled" if not github_enabled else "copied")),
        token=source_token if (github_enabled and source_token) else None,
    )
    pid_value = str(target_pid or extract_project_id(target_url) or "")
    if pid_value:
        upsert_project_identity(
            new_project_key,
            root_pid=pid_value,
            latest_pid=pid_value,
            project_name=new_project_name,
            chat_id=chat_id,
            status="RESUME_REQUESTED",
        )
    return {
        "ok": True,
        "project_key": new_project_key,
        "project_name": new_project_name,
        "source_key": source_key,
        "source_name": source_name,
        "settings": new_settings,
    }


def format_copied_settings_summary(result: dict) -> str:
    """[P19] ملخص نصي للإعدادات المنسوخة يُرسل للمستخدم بعد النسخ."""
    settings = result.get("settings") or {}
    github = settings.get("github", {}) if isinstance(settings.get("github"), dict) else {}
    if github.get("enabled"):
        branch_label = github.get("branch") or github.get("detected_default_branch") or "auto-default"
        github_line = f"{github.get('repository') or 'غير معروف'} @ {branch_label}"
        token_line = "منسوخ من المشروع المصدر ✅" if github.get("token_present") else "غير موجود بالمصدر — أضفه من الإعدادات ⚠️"
    else:
        github_line = "غير مفعل (كما في المصدر)"
        token_line = "—"
    resume_prompt = (settings.get("continuation") or {}).get("prompt") or DEFAULT_PROJECT_RESUME_PROMPT
    return (
        "📋 <b>تم نسخ الإعدادات بنجاح من مشروع آخر.</b>\n"
        f"<b>المصدر:</b> {html_escape(str(result.get('source_name') or ''))}\n"
        f"<b>الاسم الجديد:</b> {html_escape(str(result.get('project_name') or ''))}\n"
        f"<b>المفتاح:</b> <code>{html_escape(str(result.get('project_key') or ''))}</code>\n"
        f"<b>الموديل:</b> <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n"
        f"<b>GitHub:</b> {html_escape(github_line)}\n"
        f"<b>Token:</b> {html_escape(token_line)}\n"
        f"<b>برومبت الاستئناف:</b> <code>{html_escape(resume_prompt)}</code>\n"
        "أرسل الآن التعديل أو البرومبت المطلوب على هذا المشروع."
    )


def start_project_resume_from_key(chat_id: int, project_key: str) -> bool:
    key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key or ""))[:80]
    if not key:
        return False
    identity = get_project_identity_record(key) or {}
    context = summarize_project_context(identity, current_pid=identity.get("latest_genspark_pid"))
    target_url = str(context.get("resume_url") or "")
    target_pid = str(context.get("resume_pid") or context.get("latest_pid") or context.get("root_pid") or "")
    return present_resume_summary(chat_id, project_key=key, target_url=target_url, target_pid=target_pid)


