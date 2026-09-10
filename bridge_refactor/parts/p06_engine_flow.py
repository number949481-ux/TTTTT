"""[VERBATIM SLICE] p06_engine_flow
المصدر: 01.33_telegram_gen_bridge.py — الأسطر 2197..3491
المحتوى: Archive safety/extraction + download_project_archive + make_project_always_public + get_public_forked_pid + send_message_and_make_public (P40: Decline Fast-Path — _declined قبل المسارات المكلفة: تخطي download_project_archive وmake_project_always_public عند الرفض + الرابط المباشر بلا شبكة + save_project_branch بلا حراسة | P43: skip_archive = _declined or fast_lean_skip — الترتيب الحرفي للحدية 5 + إبقاء make_project_always_public في fast mode (D2) + Telemetry FAST_MODE_SKIP (D7)) + send_message_with_auto_account_failover (P12: carry_pid resume + stream-interrupt | P13: pre-flight balance gate + LOW_BALANCE silent skip | P16: early make-public فور التقاط pid | P17: تجديد فوري للجلسة المنتهية -2 + بوابة رصيد بعد تجديد 401 أثناء الشات | P18: وقف فوري عند تغيّر مؤشر النشاط أثناء polling المتابعة | P25: إلغاء تعاوني قهري — فحص cancel_event قبل الإرسال/في المتابعة + نوم متقطع Event.wait + CANCELLED بلا عقوبة في الـ failover | P30: فتح span لحظة الـ claim + إغلاق حتمي في finally + عزل spans لكل تشغيل)
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
# ══════════════════════════════════════════════════════════════
# 📦 فك الأرشيف الآمن (إصلاح Tar-Slip / Path Traversal)
# ══════════════════════════════════════════════════════════════
def _is_safe_archive_member_name(member_name: str) -> bool:
    """رفض أي مسار مطلق أو متجاوز (../) أو حرف درايف (C:) داخل الأرشيف"""
    if not member_name:
        return False
    name = member_name.replace("\\", "/")
    if name.startswith("/"):
        return False
    if re.match(r"^[A-Za-z]:", name):
        return False
    # مدخلات الجذر مثل "./" طبيعية في tar الذي ينشئه GNU tar وليست Path Traversal.
    parts = [p for p in name.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        return False
    return True


def _archive_signature_label(archive_bytes: bytes) -> str:
    head = archive_bytes[:8]
    if head.startswith(b"PK\x03\x04"):
        return "zip"
    if head.startswith(b"\x1f\x8b"):
        return "gzip"
    if len(archive_bytes) >= 262 and archive_bytes[257:262] == b"ustar":
        return "tar"
    return "unknown"


def _archive_diag(ok: bool, archive_type: str, reason_code: str = "", member: str = "", detail: str = "") -> dict:
    return {
        "ok": ok,
        "archive_type": archive_type,
        "reason_code": reason_code,
        "member": member,
        "detail": detail[:240],
    }


def _should_skip_archive_member(rel_path: str) -> bool:
    """تخطي node_modules والمجلدات المؤقتة والـ cache لتقليل الحجم وتفادي أخطاء symlink"""
    parts = pathlib.PurePosixPath(str(rel_path or "").replace("\\", "/")).parts
    skip_dirs = {"node_modules", ".git", ".cache", "__pycache__", ".npm", ".wrangler"}
    return any(p in skip_dirs for p in parts)


def _is_never_copy_file(filename: str) -> bool:
    """منع نسخ ملفات الأسرار والبيانات الحساسة والأرشيفات الخام إلى المستودع (مستوحى من 04_upload)"""
    f = str(filename or "").lower()
    if f.endswith((".tar.gz", ".tar", ".zip", ".failed")):
        return True
    if f.startswith(".env") or f in ("accounts_genspark.json", "accounts_qwen.json", "accounts_deepseek.json", "keys.txt"):
        return True
    return False


def _resolve_effective_source_root(sandbox_dir: pathlib.Path | None) -> pathlib.Path | None:
    """تحديد جذر الكود الفعلي داخل مجلد الساندبوكس المفكوك لتسطيح المجلدات الفرعية (webapp/repo/clone) (مستوحى من 04_upload get_source_root)"""
    if not sandbox_dir or not sandbox_dir.exists():
        return None
    entries = [p for p in sandbox_dir.iterdir() if not p.name.startswith(".") and not p.name.endswith((".tar.gz", ".zip"))]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    for p in entries:
        if p.is_dir() and any(kw in p.name.lower() for kw in ("webapp", "clone", "repo")):
            return p
    return sandbox_dir


def _extract_archive_with_diagnostics(archive_bytes: bytes, out_dir: pathlib.Path) -> dict:
    """فك archive مع استبعاد node_modules وتخطي symlinks بأمان مع الحفاظ على ملفات المشروع والتوثيق."""
    import io
    import tarfile
    import zipfile

    tar_err = ""
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:*") as tf:
            safe_members = []
            for member in tf.getmembers():
                if not _is_safe_archive_member_name(member.name):
                    return _archive_diag(False, "tar", "ARCHIVE_TAR_UNSAFE_PATH", member=member.name)
                if _should_skip_archive_member(member.name):
                    continue
                # تخطي الروابط الرمزية بأمان دون إيقاف باقي ملفات الأرشيف
                if member.issym() or member.islnk():
                    continue
                if member.isfile() or member.isdir():
                    safe_members.append(member)
            if not safe_members:
                return _archive_diag(True, "tar")
            try:
                tf.extractall(str(out_dir), members=safe_members, filter="data")
            except TypeError:
                tf.extractall(str(out_dir), members=safe_members)
            except Exception as err:
                return _archive_diag(False, "tar", "ARCHIVE_TAR_EXTRACT_ERROR", detail=f"{type(err).__name__}: {str(err)[:160]}")
        return _archive_diag(True, "tar")
    except Exception as err:
        tar_err = f"{type(err).__name__}: {str(err)[:160]}"

    zip_err = ""
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
            safe_infos = []
            for info in zf.infolist():
                if not _is_safe_archive_member_name(info.filename):
                    return _archive_diag(False, "zip", "ARCHIVE_ZIP_UNSAFE_PATH", member=info.filename)
                if _should_skip_archive_member(info.filename):
                    continue
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    continue
                safe_infos.append(info)
            try:
                for info in safe_infos:
                    zf.extract(info, str(out_dir))
            except Exception as err:
                return _archive_diag(False, "zip", "ARCHIVE_ZIP_EXTRACT_ERROR", detail=f"{type(err).__name__}: {str(err)[:160]}")
        return _archive_diag(True, "zip")
    except Exception as err:
        zip_err = f"{type(err).__name__}: {str(err)[:160]}"

    signature = _archive_signature_label(archive_bytes)
    return _archive_diag(
        False,
        signature,
        "ARCHIVE_UNSUPPORTED_FORMAT",
        detail=f"signature={signature}; tar={tar_err or 'n/a'}; zip={zip_err or 'n/a'}",
    )


def format_archive_diagnostic(diag: dict, archive_name: str) -> str:
    code = diag.get("reason_code") or "ARCHIVE_UNKNOWN"
    archive_type = diag.get("archive_type") or "unknown"
    parts = [f"فشل فك ضغط الأرشيف [{archive_type}/{code}]"]
    if diag.get("member"):
        parts.append(f"member={diag['member']}")
    if diag.get("detail"):
        parts.append(f"detail={diag['detail']}")
    parts.append(f"تم حفظ الملف الخام فقط: {archive_name}")
    return " | ".join(parts)


def download_project_archive(
    project_id: str,
    cookies: dict,
    out_dir: str | pathlib.Path | None = None,
    remote_path: str = "/home/user/webapp",
    email: str = "default@genspark.ai",
    bridge_cfg: BridgeConfig | None = None
) -> str | None:
    if not project_id or not cookies:
        return None
    if bridge_cfg is not None:
        default_dir = bridge_cfg.extracted_webapp_dir
    else:
        default_dir = SCRIPT_DIR / "extracted_webapp"
    out_dir = default_dir if out_dir is None else pathlib.Path(out_dir).resolve()
    os.makedirs(str(out_dir), exist_ok=True)
    tar_path = out_dir / "webapp.tar.gz"
    url = "https://www.genspark.ai/api/code_sandbox/download_directory"
    params = {"project_id": project_id, "path": remote_path}
    try:
        from curl_cffi import requests as cffi
        fp = get_account_fingerprint(email)
        browser = getattr(bridge_cfg, "current_browser", fp["browser"])
        ua = getattr(bridge_cfg, "user_agent", fp["user_agent"])
        try:
            sess = cffi.Session(impersonate=browser) if hasattr(cffi, "Session") else cffi.Session()
        except Exception:
            sess = cffi.Session(impersonate="chrome120") if hasattr(cffi, "Session") else cffi.Session()
        sess.headers.update({"User-Agent": ua, "Referer": "https://www.genspark.ai/"})
        for k, v in cookies.items():
            if hasattr(sess.cookies, "set"):
                sess.cookies.set(str(k), str(v), domain=".genspark.ai")
            else:
                sess.cookies[str(k)] = str(v)
        r = sess.get(url, params=params, timeout=180)
        if r.status_code == 200 and len(r.content) > 50:
            with open(tar_path, "wb") as f:
                f.write(r.content)
            archive_diag = _extract_archive_with_diagnostics(r.content, out_dir)
            if not archive_diag.get("ok"):
                log_event("warning", format_archive_diagnostic(archive_diag, tar_path.name), extra=archive_diag)
            return str(tar_path)
    except Exception as e:
        log_event("error", f"فشل تحميل أرشيف المشروع: {e}")
    return None


def make_project_always_public(
    project_id: str,
    cookies: dict,
    mod: any = None,
    cfg: any = None,
    email: str = "default@genspark.ai",
    bridge_cfg: BridgeConfig | None = None
) -> str:
    if not project_id:
        return ""
    public_url = f"https://www.genspark.ai/autopilotagent_viewer?id={project_id}"
    if mod and hasattr(mod, "ensure_public"):
        try:
            pub_res = mod.ensure_public(project_id, cookies, cfg, label="telegram_gen_bridge")
            if pub_res and "genspark.ai" in pub_res:
                return pub_res
        except Exception:
            pass
    try:
        from curl_cffi import requests as cffi
        fp = get_account_fingerprint(email)
        browser = getattr(bridge_cfg, "current_browser", fp["browser"])
        ua = getattr(bridge_cfg, "user_agent", fp["user_agent"])
        try:
            sess = cffi.Session(impersonate=browser) if hasattr(cffi, "Session") else cffi.Session()
        except Exception:
            sess = cffi.Session(impersonate="chrome120") if hasattr(cffi, "Session") else cffi.Session()
        sess.headers.update({
            "User-Agent": ua,
            "Referer": "https://www.genspark.ai/",
            "Content-Type": "application/json"
        })
        for k, v in cookies.items():
            if hasattr(sess.cookies, "set"):
                sess.cookies.set(str(k), str(v), domain=".genspark.ai")
            else:
                sess.cookies[str(k)] = str(v)
        make_public_urls = [
            f"https://www.genspark.ai/api/code_sandbox/make_public?project_id={project_id}",
            "https://www.genspark.ai/api/code_sandbox/make_public",
            "https://www.genspark.ai/api/share_project"
        ]
        for api_u in make_public_urls:
            try:
                res = sess.post(api_u, json={"project_id": project_id, "is_public": True}, timeout=15)
                if res.status_code in (200, 201):
                    log_event("success", f"تم تحويل المشروع [{project_id[:12]}] إلى Public عام بنجاح!")
                    break
            except Exception:
                pass
    except Exception as pub_err:
        log_event("warning", f"تنبيه النشر العام: {pub_err}")
    return public_url


def get_public_forked_pid(
    orig_pid: str,
    cookies: dict,
    mod: any = None,
    cfg: any = None,
    email: str = "default@genspark.ai",
    bridge_cfg: BridgeConfig | None = None
) -> str | None:
    if not orig_pid:
        return None
    if mod and hasattr(mod, "create_forked_project"):
        try:
            fk_pid = mod.create_forked_project(orig_pid, cookies, cfg)
            if fk_pid and fk_pid != "__INVALID_PROJECT__":
                return fk_pid
        except Exception:
            pass
    try:
        from curl_cffi import requests as cffi
        fp = get_account_fingerprint(email)
        browser = getattr(bridge_cfg, "current_browser", fp["browser"])
        ua = getattr(bridge_cfg, "user_agent", fp["user_agent"])
        sess = cffi.Session(impersonate=browser) if hasattr(cffi, "Session") else cffi.Session()
        sess.headers.update({
            "User-Agent": ua,
            "Referer": "https://www.genspark.ai/"
        })
        for name, val in cookies.items():
            if hasattr(sess.cookies, "set"):
                sess.cookies.set(str(name), str(val), domain="www.genspark.ai")
            else:
                sess.cookies[str(name)] = str(val)
        r = sess.get(f"https://www.genspark.ai/api/continue_conversation?id={orig_pid}", allow_redirects=False, timeout=20)
        if r.status_code in (301, 302, 307, 308, 200):
            loc = r.headers.get("location", "") or r.text
            if loc and "/login" not in loc:
                fk_pid = extract_project_id(loc)
                if fk_pid and fk_pid != orig_pid and "login" not in fk_pid and len(fk_pid) > 10:
                    log_event("success", f"تم التفريع بنجاح: {fk_pid[:16]}...", email=email)
                    return fk_pid
    except Exception:
        pass
    try:
        from curl_cffi import requests as cffi
        fp = get_account_fingerprint(email)
        browser = getattr(bridge_cfg, "current_browser", fp["browser"])
        ua = getattr(bridge_cfg, "user_agent", fp["user_agent"])
        clean_sess = cffi.Session(impersonate=browser) if hasattr(cffi, "Session") else cffi.Session()
        clean_sess.headers.update({
            "User-Agent": ua,
            "Referer": "https://www.genspark.ai/"
        })
        r = clean_sess.get(f"https://www.genspark.ai/api/continue_conversation?id={orig_pid}", allow_redirects=False, timeout=20)
        if r.status_code in (301, 302, 307, 308, 200):
            loc = r.headers.get("location", "") or r.text
            if loc and "/login" not in loc:
                fk_pid = extract_project_id(loc)
                if fk_pid and fk_pid != orig_pid and "login" not in fk_pid and len(fk_pid) > 10:
                    log_event("success", f"تم التفريع المباشر بدون 403: {fk_pid[:16]}...", email=email)
                    return fk_pid
    except Exception as pub_fk_err:
        log_event("warning", f"تنبيه التفريع العام: {pub_fk_err}", email=email)
    return None


COMPACT_TRIGGER_SECONDS = 180


def current_account_duration(bridge_cfg, email="") -> float:
    """Read existing monotonic account spans, never wall-clock elapsed time."""
    for span in reversed(getattr(bridge_cfg, "account_journey_spans", None) or []):
        if not isinstance(span, dict) or (email and span.get("email") != email):
            continue
        try:
            seconds = (float(span.get("duration_seconds") or 0) if span.get("closed") else
                       time.monotonic() - float(span["started_monotonic"]))
            return seconds if 0 <= seconds < float("inf") else 0.0
        except (KeyError, TypeError, ValueError):
            return 0.0
    return 0.0


def compact_summary_context(messages):
    """Return the newest typed summary and only the history following it."""
    if not isinstance(messages, list):
        return None, []
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        if not isinstance(message, dict) or message.get("role") not in ("assistant", "user"):
            continue
        state = message.get("session_state")
        if (isinstance(state, dict) and state.get("is_compact_summary") is True
                and str(message.get("content") or "").strip()):
            key = hashlib.sha256(json.dumps(
                [message.get("id"), message.get("content")], ensure_ascii=False,
                sort_keys=True).encode("utf-8")).hexdigest()
            return key, messages[index:]
    return None, []


def monitor_chat_completion(mod, cookies, cfg, bridge_cfg, pid, answer, start_time,
                            email="", maintenance=False, readiness=False):
    """One bounded, cancellable lifecycle for both maintenance and business turns.

    EOF and partial text are not terminal evidence. A readiness-only invocation
    observes the current project without sending anything or trusting old latches.
    """
    _cancel_event = getattr(bridge_cfg, "cancel_event", None)
    session_timeout = getattr(bridge_cfg, "session_timeout", 1000)
    evidence = getattr(cfg, "_chat_attempt", None)
    evidence = evidence if isinstance(evidence, dict) and evidence.get("project_id") == pid else None
    strict = bool(getattr(mod, "CHAT_ATTEMPT_EVIDENCE_SUPPORTED", False)) or maintenance or readiness
    last_resp_text = "" if answer in (None, "__STREAM_INTERRUPTED__", "__CREDIT_EXHAUSTED__") else str(answer)
    final_status = resolve_runtime_credit_status(detect_response_status(answer), answer, mod, pid, cookies, cfg)
    if answer == "__STREAM_INTERRUPTED__":
        final_status = "RUNNING"
    unconfirmed = final_status == "CREDIT_UNCONFIRMED"
    strict = strict or unconfirmed
    if evidence and evidence.get("deadline_reached"):
        return "TIMEOUT", last_resp_text
    if evidence and evidence.get("finished") and not unconfirmed and final_status not in P44_STRUCTURED_STATUSES:
        final_status = "COMPLETED"
    elif strict and final_status not in P44_STRUCTURED_STATUSES:
        final_status = "RUNNING"
    if readiness:
        final_status = "RUNNING"
    prev_activity = fetch_project_activity_signature(pid, cookies)
    inactive_streak = stable_streak = 0
    prev_reply_fp = None
    polled_any = False
    p18_stopped = False
    while final_status not in ("COMPLETED", "CREDIT_EXHAUSTED", "DATA_RETENTION", "SESSION_EXPIRED", "FORBIDDEN"):
        # Cancellation always precedes waiting and network reads.
        if _cancel_event is not None and _cancel_event.is_set():
            return CANCELLED_STATUS, last_resp_text
        if time.time() - start_time >= session_timeout:
            return ("CREDIT_UNCONFIRMED" if unconfirmed else "TIMEOUT"), last_resp_text
        if polled_any:
            remaining = max(0, session_timeout - (time.time() - start_time))
            if _cancel_event is not None:
                if _cancel_event.wait(timeout=min(5, remaining)):
                    return CANCELLED_STATUS, last_resp_text
            else:
                time.sleep(min(5, remaining))
        polled_any = True
        if time.time() - start_time >= session_timeout:
            return ("CREDIT_UNCONFIRMED" if unconfirmed else "TIMEOUT"), last_resp_text
        curr_activity = fetch_project_activity_signature(pid, cookies)
        if curr_activity is not None:
            stop_now, stop_reason = should_stop_on_activity_change(prev_activity, curr_activity)
            if stop_now:
                log_event("warning", f"[P18] Activity changed: {stop_reason}", email=email)
                p18_stopped = True
                final_status = "COMPLETED"
                break
            prev_activity = curr_activity
            inactive_streak = 0 if curr_activity.get("active") else inactive_streak + 1
        try:
            messages = mod.fetch_project_messages(pid, cookies, cfg)
            if _cancel_event is not None and _cancel_event.is_set():
                return CANCELLED_STATUS, last_resp_text
            http_status = getattr(cfg, "_last_fetch_status", 200)
            if http_status in (401, 403):
                return ("SESSION_EXPIRED" if http_status == 401 else "FORBIDDEN"), last_resp_text
            if http_status != 200:
                continue
            message = current_attempt_reply(messages, evidence)
            if message:
                text = message.get("content", "")
                if text:
                    last_resp_text = text
                raw = resolve_runtime_credit_status(detect_response_status(text), text, mod, pid, cookies, cfg, message)
                if raw == "CREDIT_UNCONFIRMED":
                    unconfirmed = True
                if raw in P44_STRUCTURED_STATUSES:
                    return raw, last_resp_text
                state = message.get("session_state") or {}
                terminal = (isinstance(state, dict) and state.get("_finish_reason") == "stop"
                            and message.get("pending") is not True and not message.get("tool_calls"))
                if unconfirmed and evidence is None and text != answer:
                    terminal = False  # Old history cannot validate an ambiguous sentinel.
                fp = compute_reply_fingerprint(text)
                stable_streak = stable_streak + 1 if fp == prev_reply_fp else 1
                prev_reply_fp = fp
            else:
                raw, terminal = "RUNNING", False
            # Fresh authoritative project status supports collapsed compact turns
            # and restart readiness. Never reuse a previous request's SSE evidence.
            snapshot_finished = (getattr(cfg, "_last_fetch_authoritative", False)
                                 and getattr(cfg, "_last_fetch_project_id", None) == pid
                                 and getattr(cfg, "_last_project_status", None) == "FINISHED"
                                 and bool(getattr(cfg, "_last_chat_session_id", "")))
            if evidence:
                snapshot_finished = snapshot_finished and any(
                    (m.get("id") == evidence.get("request_id") or m.get("id") in evidence.get("summary_ids", ()))
                    for m in messages or [] if isinstance(m, dict))
            active = isinstance(curr_activity, dict) and curr_activity.get("active")
            if (terminal or snapshot_finished) and not active:
                # Text-only suspicion in a finished real reply is ordinary content.
                if last_resp_text != "__CREDIT_EXHAUSTED__" or snapshot_finished:
                    final_status = "COMPLETED"
                    unconfirmed = False
            elif not strict:
                final_status = detect_response_status_gated(raw, curr_activity, inactive_streak, stable_streak, email=email)
        except Exception as err:
            log_event("warning", f"[CHAT_MONITOR] Read failed: {type(err).__name__}", email=email)
    if polled_any and final_status == "COMPLETED" and not readiness:
        last_resp_text = fetch_final_reply_text(mod, pid, cookies, cfg, last_resp_text, email=email)
        message = getattr(cfg, "_final_reply_message", None)
        refreshed = resolve_runtime_credit_status(detect_response_status(last_resp_text), last_resp_text,
                                                  mod, pid, cookies, cfg, message)
        if refreshed in P44_STRUCTURED_STATUSES or refreshed == "CREDIT_UNCONFIRMED":
            final_status = refreshed
    if _cancel_event is not None and _cancel_event.is_set():
        return CANCELLED_STATUS, last_resp_text
    # P18 still stops immediately, but stopping maintenance is not permission to
    # send another turn, nor proof that a suspected/partial business reply finished.
    if p18_stopped and final_status == "COMPLETED" and (strict or unconfirmed):
        return "ACTIVITY_STOPPED", last_resp_text
    return final_status, last_resp_text


def run_verified_compact(mod, cookies, cfg, bridge_cfg, project_id, email, on_start=None):
    """Maintenance completion is internal; caller MUST still send pending work."""
    event = getattr(bridge_cfg, "cancel_event", None)
    current_pid = project_id
    def cancelled():
        return event is not None and event.is_set()
    def started(pid):
        nonlocal current_pid
        if extract_project_id(pid):
            current_pid = extract_project_id(pid)
            if on_start:
                on_start(current_pid)
    bridge_cfg.compact_in_progress = True
    try:
        if cancelled():
            return CANCELLED_STATUS, current_pid, None
        cfg._verified_compact_context = cfg._resume_context = cfg._chat_attempt = None
        baseline = mod.fetch_project_messages(current_pid, cookies, cfg)
        if getattr(cfg, "_last_fetch_status", 0) != 200:
            return "READ_FAILED", current_pid, None
        old_key, _ = compact_summary_context(baseline)
        if cancelled():
            return CANCELLED_STATUS, current_pid, None
        started(current_pid)
        start_time = time.time()
        cfg._chat_deadline = time.monotonic() + getattr(bridge_cfg, "session_timeout", 1000)
        answer, returned_pid, _ = mod.send_chat(
            cookies, "/compact", email, project_id=current_pid, history=baseline,
            cfg=cfg, on_project_start_callback=started)
        if cancelled() or answer == USER_CANCELLED_MARKER:
            return CANCELLED_STATUS, current_pid, None
        if returned_pid:
            if not extract_project_id(returned_pid):
                return "READ_FAILED", current_pid, None
            started(returned_pid)
        status, _ = monitor_chat_completion(mod, cookies, cfg, bridge_cfg, current_pid,
                                            answer, start_time, email, maintenance=True)
        if status != "COMPLETED":
            return status, current_pid, None
        # No second compact-success gate: this read supplies the next payload,
        # exactly as an ordinary continuation, not a six-read summary verifier.
        cfg._last_chat_session_id = ""
        messages = mod.fetch_project_messages(current_pid, cookies, cfg)
        if cancelled():
            return CANCELLED_STATUS, current_pid, None
        session_id = str(getattr(cfg, "_last_chat_session_id", "") or "")
        if getattr(cfg, "_last_fetch_status", 0) != 200 or not session_id or not isinstance(messages, list):
            return "READ_FAILED", current_pid, None
        key, compact_history = compact_summary_context(messages)
        context = {"project_id": current_pid, "chat_session_id": session_id,
                   "messages": compact_history if key else messages, "summary_key": key if key != old_key else None}
        bridge_cfg.compact_before_send = False
        bridge_cfg.compact_latest_pid = current_pid
        if not context["summary_key"]:
            # A finished no-op needs no more verification, but do not repeatedly
            # schedule optional maintenance on the same uncompactable session.
            bridge_cfg.compact_deferred = bridge_cfg.compact_deferred_this_run = True
            context["deferred"] = True
        save = getattr(bridge_cfg, "compact_verified_callback", None)
        if callable(save):
            try:
                save(context)
            except Exception as err:
                log_event("warning", f"[COMPACT] Optional state save failed: {type(err).__name__}", email=email)
        return "COMPACT_COMPLETED", current_pid, context
    except Exception as err:
        log_event("warning", f"[COMPACT] Read/transport failure: {type(err).__name__}", email=email)
        return CANCELLED_STATUS if cancelled() else "READ_FAILED", current_pid, None
    finally:
        bridge_cfg.compact_in_progress = False


def send_message_and_make_public(
    url: str | None,
    email: str,
    password: str,
    query: str,
    bridge_cfg: BridgeConfig | None = None,
    json_path: str | None = None,
    on_project_start_callback=None,
) -> tuple[str | None, str, str | None, str | None, str | None]:
    if bridge_cfg is None:
        bridge_cfg = BridgeConfig()
    max_retries = max(1, getattr(bridge_cfg, "max_timeout_retries", 2))
    session_timeout = getattr(bridge_cfg, "session_timeout", 1000)

    mod = get_genspark_engine()
    if not mod:
        return None, "NO_ENGINE", None, None, None

    # ⚡ [P12] carry_pid: أي project_id يُلتقط (من project_start أو من رجوع send_chat)
    # يُحفظ هنا ويُستأنف عليه في أي محاولة تالية — ممنوع إنشاء شات/ID جديد بعد الانقطاع.
    carry_pid = None
    verified_compact_context = None

    # 🌐 [P16] Early Make-Public: بمجرد التقاط project_id حي — نحوّل المشروع إلى Public
    # فوراً في خيط خلفي (Fire-and-Forget) قبل/مع إرسال زر المعاينة الفورية،
    # حتى يعمل رابط المعاينة الحية من أول ثانية بدلاً من انتظار اكتمال التوليد.
    # مرة واحدة فقط لكل pid — بدون أي تأخير للبث الرئيسي.
    early_public_pids: set = set()
    cookies: dict = {}
    cfg = None

    def _early_make_public_async(live_pid: str):
        if not live_pid or str(live_pid).startswith("__") or live_pid in early_public_pids:
            return
        early_public_pids.add(live_pid)
        snapshot_cookies = dict(cookies) if isinstance(cookies, dict) else {}
        snapshot_cfg = cfg

        def _worker():
            try:
                make_project_always_public(
                    live_pid, snapshot_cookies, mod=mod, cfg=snapshot_cfg,
                    email=email, bridge_cfg=bridge_cfg,
                )
                log_event("info", f"🌐 [P16] المشروع {str(live_pid)[:12]}… أصبح Public مبكراً — زر المعاينة يعمل فوراً", email=email)
            except Exception as early_pub_err:
                log_event("warning", f"[P16] تعذر النشر العام المبكر: {early_pub_err}", email=email)

        try:
            threading.Thread(target=_worker, daemon=True, name=f"early-public-{str(live_pid)[:8]}").start()
        except Exception:
            pass

    def _pid_capture_callback(live_pid):
        nonlocal carry_pid
        if live_pid and not str(live_pid).startswith("__"):
            carry_pid = live_pid
            # [P16] النشر العام فور معرفة الـ pid — قبل أي انتظار لاكتمال التوليد
            _early_make_public_async(live_pid)
        if on_project_start_callback is not None:
            try:
                on_project_start_callback(live_pid)
            except Exception:
                pass

    for attempt in range(1, max_retries + 1):
        cfg = getattr(mod, "Config")()
        cfg.model = bridge_cfg.model
        fp = get_account_fingerprint(email)
        user_agent_str = fp["user_agent"]
        try:
            cfg.user_agent = user_agent_str
            cfg.headers = {"User-Agent": user_agent_str}
        except Exception:
            pass

        cfg.use_ultra = False
        cfg.agent_type = bridge_cfg.agent_type
        cfg.request_web_knowledge = needs_web_search(query)
        # 🛑 [P25] حقن حدث الإلغاء في cfg المحرك — send_chat يفحصه كل سطر SSE
        # ويقطع البث فوراً (r.close) بنفس تأثير زر ⏹️ Stop في واجهة جينسبارك.
        _cancel_event = getattr(bridge_cfg, "cancel_event", None)
        try:
            cfg.cancel_event = _cancel_event
        except Exception:
            pass
        # 🛑 [P25] إلغاء طُلب قبل بدء المحاولة أصلاً → خروج فوري بدون أي إرسال
        if _cancel_event is not None and _cancel_event.is_set():
            log_event("warning", "🛑 [P25] إلغاء المستخدم قبل بدء المحاولة — خروج فوري بدون إرسال", email=email)
            return None, CANCELLED_STATUS, None, None, None
        project_id, history = None, []

        accounts = read_accounts_safe(json_path)
        acc = next((a for a in accounts if isinstance(a, dict) and a.get("email") == email), None)
        cookies = acc.get("cookies", {}) if acc else {}

        # ⚡ فحص مسبق وتجديد الجلسة بـ REFRESH_LOCK منفرد للإيميل
        # إصلاح: لو تم تجديد الكوكيز قبل أقل من 120 ثانية نتخطى الفحص المسبق
        # لمنع التكرار المزدوج للمحاولة (كان يظهر مرتين في اللوج لكل حساب).
        last_refresh = 0
        if acc:
            try:
                last_refresh = float(acc.get("last_refresh") or 0)
            except Exception:
                last_refresh = 0

        # 💰 [P13] Pre-Flight Balance Check — قبل لمس الشات أو إرسال أي حرف:
        # دلالات check_balance: >=0 رصيد فعلي | -2 جلسة منتهية | -1 فشل شبكة (لا عقوبة).
        # رصيد فعلي < min_preflight_balance → تبريد 29h فوراً + LOW_BALANCE (لا fork ولا شات).
        _min_balance = int(getattr(bridge_cfg, "min_preflight_balance", 100) or 100)
        cookies_valid = False
        bal_check = -1
        if cookies and isinstance(cookies, dict) and hasattr(mod, "check_balance"):
            try:
                bal_check = mod.check_balance(cookies)
            except Exception:
                bal_check = -1
            if isinstance(bal_check, (int, float)) and bal_check >= 0:
                if bal_check < _min_balance:
                    log_event("warning", f"💰 رصيد منخفض ({int(bal_check)} < {_min_balance}) — تبريد 29h وتخطٍ صامت بدون أي إرسال", email=email)
                    mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                    return None, "LOW_BALANCE", None, None, None
                cookies_valid = True
                try:
                    update_account_data(email, {"balance": int(bal_check)}, json_path=json_path)
                except Exception:
                    pass

        # 💰 [P17] سد ثغرة نافذة الـ 120 ثانية: جلسة منتهية صراحةً (-2) تُجدَّد فوراً
        # حتى لو آخر تجديد كان حديثاً — لأن تخطيها يعني fork/شات بجلسة ميتة بلا فحص رصيد.
        if not cookies_valid and (bal_check == -2 or (time.time() - last_refresh) > 120):
            new_cookies = refresh_cookies_on_401(mod, email, password, json_path=json_path)
            if new_cookies and isinstance(new_cookies, dict):
                cookies = new_cookies
                # [P13] سد ثغرة "جلسة متجددة برصيد فارغ": إعادة فحص الرصيد بالكوكيز الجديدة
                if hasattr(mod, "check_balance"):
                    try:
                        bal_recheck = mod.check_balance(cookies)
                    except Exception:
                        bal_recheck = -1
                    if isinstance(bal_recheck, (int, float)) and 0 <= bal_recheck < _min_balance:
                        log_event("warning", f"💰 رصيد منخفض بعد تجديد الجلسة ({int(bal_recheck)} < {_min_balance}) — تبريد 29h وتخطٍ صامت", email=email)
                        mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                        return None, "LOW_BALANCE", None, None, None
            else:
                update_account_data(email, {"status": "auth_failed", "active": False, "cooldown_until": time.time() + 1800}, json_path=json_path)
                return None, "LOGIN_FAILED", None, None, None

        # ⚡ [P12] لو معانا مشروع ملتقط من محاولة سابقة → نستأنف عليه مباشرة
        # (بدون fork جديد وبدون شات جديد) — هذا جوهر إصلاح مشكلة chat id الجديد.
        if carry_pid:
            project_id = carry_pid
            history = []
            log_event("info", f"♻️ استئناف على نفس المشروع الملتقط {str(carry_pid)[:16]}... (محاولة {attempt})", email=email)
            # [P12-C] زر المعاينة الحية يصل فوراً حتى في الاستئناف (السيرفر لا يرسل project_start لمشروع قائم)
            # [P16] النشر العام المبكر قبل/مع إرسال زر المعاينة — الرابط يعمل من أول ضغطة
            _early_make_public_async(project_id)
            if on_project_start_callback is not None:
                try:
                    on_project_start_callback(project_id)
                except Exception:
                    pass
        elif url and isinstance(url, str) and url.strip():
            orig_pid = extract_project_id(url.strip())
            if orig_pid:
                try:
                    history = mod.fetch_project_messages(orig_pid, cookies, cfg)
                except Exception as h_err:
                    if "403" in str(h_err) or "not authorized" in str(h_err).lower():
                        log_event("warning", "تجاوز 403 في جلب الرسائل، جاري التفريع العام...", email=email)
                    history = []
                forked_pid = get_public_forked_pid(orig_pid, cookies, mod=mod, cfg=cfg, email=email, bridge_cfg=bridge_cfg)
                project_id = forked_pid or orig_pid
                # [P12-C] زر المعاينة الحية فور معرفة مشروع الاستئناف/الفورك (لا انتظار لـ project_start)
                # [P16] النشر العام المبكر قبل/مع إرسال زر المعاينة — الرابط يعمل من أول ضغطة
                if project_id:
                    _early_make_public_async(project_id)
                if project_id and on_project_start_callback is not None:
                    try:
                        on_project_start_callback(project_id)
                    except Exception:
                        pass

        compact_deferred = bool(getattr(bridge_cfg, "compact_deferred", False))
        if bool(getattr(bridge_cfg, "compact_before_send", False)) and not compact_deferred:
            compact_status, compact_pid, verified_compact_context = run_verified_compact(
                mod, cookies, cfg, bridge_cfg, project_id, email, _pid_capture_callback)
            carry_pid = project_id = compact_pid
            if compact_status != "COMPACT_COMPLETED":
                bridge_cfg.compact_before_send = False
                bridge_cfg.compact_deferred = True
                bridge_cfg.compact_deferred_this_run = True
                defer = getattr(bridge_cfg, "compact_deferred_callback", None)
                if callable(defer):
                    try:
                        defer(project_id, str(getattr(cfg, "_last_chat_session_id", "") or ""), False)
                    except Exception as err:
                        log_event("warning", f"[COMPACT] Optional deferral save failed: {type(err).__name__}", email=email)
                return build_genspark_viewer_url(project_id), compact_status, None, "", None
            history = verified_compact_context["messages"]
            # COMPLETED above was maintenance only. Keep the live project/card,
            # fall through to the ONE ordinary send below with the original query.
            if on_project_start_callback:
                on_project_start_callback(project_id)
        elif compact_deferred and getattr(bridge_cfg, "compact_bypass_blocked", False):
            cfg._chat_attempt = None
            ready_status, ready_text = monitor_chat_completion(
                mod, cookies, cfg, bridge_cfg, project_id, None, time.time(), email, readiness=True)
            if ready_status != "COMPLETED":
                return build_genspark_viewer_url(project_id), ready_status, None, ready_text, None
            # This flag requests a fresh observation only, never a persistent veto.
            bridge_cfg.compact_bypass_blocked = False
        if _cancel_event is not None and _cancel_event.is_set():
            return build_genspark_viewer_url(project_id), CANCELLED_STATUS, None, "", None

        start_time = time.time()
        cfg._chat_deadline = time.monotonic() + session_timeout
        answer, pid, asst_id = None, None, None
        last_chat_err = None
        chat_failed = False

        for chat_attempt in range(2):
            try:
                send_chat_kwargs = {
                    "project_id": project_id,
                    "history": history,
                    "cfg": cfg,
                    # [P12] دائماً نمرر ملتقط الـ pid — حتى لو انقطع البث لاحقاً نعرف المشروع ونستأنف عليه
                    "on_project_start_callback": _pid_capture_callback,
                }
                cfg._chat_attempt = None
                cfg._verified_compact_context = None
                cfg._resume_context = verified_compact_context
                try:
                    answer, pid, asst_id = mod.send_chat(cookies, query, email, **send_chat_kwargs)
                finally:
                    cfg._verified_compact_context = cfg._resume_context = None  # Polling sees live replies.
                    bridge_cfg.compact_current_session_id = str(getattr(cfg, "_last_chat_session_id", "") or "")
                break

            except Exception as chat_err:
                err_str = str(chat_err).lower()
                if ("401" in err_str or "unauthorized" in err_str or "session" in err_str) and chat_attempt == 0:
                    log_event("warning", "التقاط 401 أثناء الشات، تجديد الكوكيز وإعادة المحاولة...", email=email)
                    new_cookies = refresh_cookies_on_401(mod, email, password, json_path=json_path)
                    if new_cookies and isinstance(new_cookies, dict):
                        cookies = new_cookies
                        # 💰 [P17] بوابة الرصيد بعد تجديد 401 أثناء الشات — نفس عقد P13:
                        # جلسة متجددة برصيد أقل من العتبة ممنوع تكمل الإرسال (تبريد 29h + LOW_BALANCE صامت).
                        if hasattr(mod, "check_balance"):
                            try:
                                bal_mid = mod.check_balance(cookies)
                            except Exception:
                                bal_mid = -1
                            if isinstance(bal_mid, (int, float)) and 0 <= bal_mid < _min_balance:
                                log_event("warning", f"💰 رصيد منخفض بعد تجديد 401 أثناء الشات ({int(bal_mid)} < {_min_balance}) — تبريد 29h وتخطٍ صامت", email=email)
                                mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                                return None, "LOW_BALANCE", None, None, None
                        time.sleep(1.5)  # مهلة قصيرة لثبات الجلسة الجديدة قبل إعادة الإرسال
                        continue
                chat_failed = True
                last_chat_err = str(chat_err)
                break

        if chat_failed:
            if attempt < max_retries:
                continue
            return None, "CHAT_ERROR", None, None, last_chat_err

        # 🛑 [P25] المحرك قطع البث بناءً على طلب المستخدم → إنهاء فوري بلا retry
        # (الحساب يُحرَّر في finally داخل failover — Zero Resources Leak)
        if answer == USER_CANCELLED_MARKER or (
            _cancel_event is not None and _cancel_event.is_set()
        ):
            log_event("warning", f"🛑 [P25] تم إلغاء البث بواسطة المستخدم — إنهاء المهمة فوراً (pid={str(pid or '')[:16]})", email=email)
            return None, CANCELLED_STATUS, None, None, None

        if not pid or pid == "__INVALID_PROJECT__":
            if attempt < max_retries:
                continue
            return None, "FAILED", None, None, str(answer or "")

        # [P12] تثبيت المشروع الملتقط للمحاولات التالية — لا شات جديد بعد الآن
        carry_pid = pid

        # [P12] انقطاع البث مع مشروع حي → لا نفشل ولا نعيد من الصفر:
        # ندخل حلقة المتابعة (polling) على نفس الـ pid حتى يكتمل التوليد سحابياً.
        if answer == "__STREAM_INTERRUPTED__":
            log_event("warning", f"انقطع بث الرد — متابعة نفس المشروع {str(pid)[:16]}... حتى الاكتمال", email=email)
            final_status = "RUNNING"
            last_resp_text = ""
        else:
            final_status = detect_response_status(answer)
            last_resp_text = str(answer) if answer else ""
        final_status, last_resp_text = monitor_chat_completion(
            mod, cookies, cfg, bridge_cfg, pid, answer, start_time, email)
        if final_status not in ("COMPLETED", "CREDIT_EXHAUSTED", "DATA_RETENTION", "SESSION_EXPIRED", "FORBIDDEN"):
            return build_genspark_viewer_url(pid), final_status, None, last_resp_text, None

        ext_base = pathlib.Path(bridge_cfg.extracted_webapp_dir)
        ext_dir = str(ext_base / pid)
        # 🚫⚡ [P40] Decline Fast-Path: رد الرفض القصير (COMPLETED تقنياً) لا يستحق
        # أي مسار شبكي مكلف — تخطي تنزيل الأرشيف (timeout=180) والنشر العام
        # (حتى 3 طلبات ×15s) وبناء الرابط المباشر بلا شبكة (نفس فلسفة P36 في
        # المحرك حرفياً — الرابط لا يضيع، وهو نفس قيمة fallback الدالة المتخطاة).
        # التسجيل المحلي (save_project_branch) يعمل كالمعتاد — عقد P36 رقم 3.
        _declined = final_status == "COMPLETED" and is_model_decline_response(last_resp_text)
        if _declined:
            log_event("warning", f"🚫⚡ [P40] رفض موديل مكتشف مبكراً — تخطي الأرشفة والنشر العام (pid={str(pid)[:16]})", email=email)
        # ⚡ [P43] Fast Lean Mode (وثيقة 17 §4.1 — DEC-039): الترتيب `_declined`
        # أولاً ثم fast_lean_skip (الحدية 5 — الرفض يفوز ويتخطى النشر أيضاً).
        # العلم محسوم مسبقاً عند بدء المهمة عبر apply_project_runtime_binding
        # (الدالة الحاكمة should_skip_artifacts_download — D3: GitHub مفعّل ⇒
        # False والتنزيل إلزامي). عند التخطي: تنزيل الأرشيف (timeout=180) +
        # فك الضغط فقط يُتخطيان — make_project_always_public تبقى تعمل (D2)
        # وsave_project_branch بلا حراسة (شجرة الاستئناف tree:* محفوظة دائماً).
        # fast_mode=False (الافتراضي) = السلوك الحالي بالبايت (G3 Zero Regression).
        fast_lean_skip = bool(getattr(bridge_cfg, "project_fast_lean_skip", False))
        # Fast credit handoff persists cloud resume metadata, never an archive.
        skip_archive = _declined or fast_lean_skip
        if fast_lean_skip and not _declined:
            # 📊 [P43-D7] Telemetry إلزامية لكل تخطٍ — أرقام السرعة تُنشر من قياس فعلي فقط
            log_event("info", f"⚡ [P43] FAST_MODE_SKIP project={str(getattr(bridge_cfg, 'selection_project_key', '') or '')} pid={str(pid)[:16]}", email=email)
        archive_path = None if skip_archive else download_project_archive(pid, cookies, out_dir=ext_dir, email=email, bridge_cfg=bridge_cfg)
        if _declined:
            final_public_url = f"https://www.genspark.ai/autopilotagent_viewer?id={pid}"
        else:
            final_public_url = make_project_always_public(pid, cookies, mod=mod, cfg=cfg, email=email, bridge_cfg=bridge_cfg)
        save_project_branch(
            parent_id=extract_project_id(url) if url else None,
            child_id=pid,
            title=get_public_continuation_prompt_text(query)[:30],
            model=cfg.model,
            status=final_status,
        )
        return final_public_url, final_status, ext_dir, last_resp_text, None

    return None, "TIMEOUT", None, None, None


def send_message_with_auto_account_failover(
    url: str | None,
    query: str,
    email: str | None = None,
    password: str | None = None,
    bridge_cfg: BridgeConfig | None = None,
    json_path: str | None = None,
    progress_callback=None,
    on_project_start_callback=None,
) -> tuple[str | None, str, dict | None, str | None, str | None]:

    """
    النسخة الذكية بتبريد 29 ساعة + REFRESH_LOCK منفرد للإيميل + بصمة متسقة ثنائية لكل حساب.
    عند CREDIT_EXHAUSTED لا تُرجع الرد الجزئي: تُبرّد الحساب، تفرّع المشروع في حساب آخر،
    وترسل حرفياً "تابع " حتى يكتمل الرد أو تنفد الحسابات.
    """
    if bridge_cfg is None:
        bridge_cfg = BridgeConfig()
    if getattr(bridge_cfg, "run_started_at", None) is None:
        bridge_cfg.run_started_at = time.time()
    apply_project_runtime_binding(
        bridge_cfg,
        getattr(bridge_cfg, "selection_project_key", "") or None,
        requested_model=getattr(bridge_cfg, "model", DEFAULT_PROJECT_MODEL),
    )
    all_accounts = read_accounts_safe(json_path)

    owner_token = str(getattr(bridge_cfg, "selection_owner_token", "") or uuid.uuid4().hex)
    bridge_cfg.selection_owner_token = owner_token
    tried_emails = set()
    state_refresh = {}
    attempt = 0
    max_attempts = getattr(bridge_cfg, "max_account_attempts", 50)
    credit_continuations = 0
    max_credit_continuations = get_credit_continuation_limit(bridge_cfg)
    bridge_cfg.last_credit_continuations = 0
    bridge_cfg.last_credit_checkpoint_id = ""
    bridge_cfg.last_credit_resume_target_url = ""
    bridge_cfg.last_credit_resume_project_id = ""
    bridge_cfg.selected_account_email = ""
    bridge_cfg.selected_account_claim_state = ""
    bridge_cfg.account_journey = []  # 🧾 [P29] عزل مسار الحسابات لكل تشغيل جديد
    bridge_cfg.account_journey_spans = []  # ⏱️ [P30] عزل spans التوقيت لكل تشغيل جديد
    _set_credit_checkpoint_state(bridge_cfg, "", "")
    active_url = url
    active_query = query

    while attempt < max_attempts:
        attempt += 1
        curr_acc, ready_accounts, claim_reason = claim_eligible_account_for_owner(
            all_accounts,
            tried_emails,
            owner_token,
            project_key=str(getattr(bridge_cfg, "selection_project_key", "") or ""),
            attempt_number=attempt,
        )
        if claim_reason == "no-eligible":
            bridge_cfg.selected_account_claim_state = "no-eligible"
            notify_account_selection_observer(
                bridge_cfg,
                "no-eligible-accounts",
                status="ALL_ACCOUNTS_IN_COOLDOWN",
                max_attempts=max_attempts,
            )
            log_event("error", "كافة الحسابات المصرح بها حالياً في مهلة الـ 29h أو الحظر!")
            return None, "ALL_ACCOUNTS_IN_COOLDOWN", None, None, None
        if claim_reason == "busy":
            bridge_cfg.selected_account_claim_state = "busy"
            notify_account_selection_observer(
                bridge_cfg,
                "eligible-accounts-busy",
                status="ALL_ACCOUNTS_BUSY",
                max_attempts=max_attempts,
            )
            log_event("warning", "كل الحسابات المؤهلة الحالية محجوزة لمهمات أخرى؛ لا يوجد حساب حر الآن لهذه المهمة")
            return None, "ALL_ACCOUNTS_BUSY", None, None, None

        curr_acc = reactivate_account_if_due(curr_acc, json_path=json_path)
        curr_email = curr_acc.get("email")
        curr_pass = curr_acc.get("password", "")
        tried_emails.add(curr_email)
        bridge_cfg.selection_attempt_number = attempt
        bridge_cfg.selected_account_email = str(curr_email or "")
        bridge_cfg.selected_account_claim_state = "claimed"
        record_account_journey(bridge_cfg, curr_email)  # 🧾 [P29] لحظة الـ claim الفعلي فقط
        open_account_timing_span(bridge_cfg, curr_email, attempt_number=attempt)  # ⏱️ [P30] فتح span لحظة الـ claim

        fp = get_account_fingerprint(curr_email)
        bridge_cfg.user_agent = fp["user_agent"]
        bridge_cfg.current_browser = fp["browser"]
        notify_account_selection_observer(
            bridge_cfg,
            "account-claimed",
            status="CLAIMED",
            max_attempts=max_attempts,
            current_browser=fp["browser"],
        )

        log_event("info", f"تجربة حساب ({attempt}/{max_attempts}) | Profile: {fp['browser']}", email=curr_email)
        log_event("info", "تم حجز الحساب للمهمة الحالية أثناء التنفيذ", email=curr_email)

        now_ts = time.time()
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        update_account_data(curr_email, {"last_used": now_ts, "last_used_at": now_str}, json_path=json_path)

        try:
            pub_url, status, ext_dir, last_text, extra = send_message_and_make_public(
                url=active_url, email=curr_email, password=curr_pass, query=active_query,
                bridge_cfg=bridge_cfg, json_path=json_path,
                on_project_start_callback=on_project_start_callback,
            )

            # 🛑 [P25] إلغاء المستخدم التفاعلي → إنهاء فوري للمهمة كلها:
            # لا محاولة بحساب آخر، لا عقوبة/تبريد للحساب الحالي (يُحرَّر في finally)،
            # ولا progress_callback — المستخدم طلب الوقف القهري بنفسه.
            if status == CANCELLED_STATUS:
                notify_account_selection_observer(
                    bridge_cfg,
                    "user-cancelled",
                    status=CANCELLED_STATUS,
                    max_attempts=max_attempts,
                )
                log_event("warning", "🛑 [P25] أُلغيت المهمة بواسطة المستخدم — تحرير الحساب فوراً وإنهاء الـ failover", email=curr_email)
                update_account_data(curr_email, {"last_used": time.time(), "status": "active"}, json_path=json_path)
                return pub_url, CANCELLED_STATUS, curr_acc, ext_dir, last_text

            # 💰 [P13] رصيد منخفض مكتشف قبل الإرسال → الحساب مُبرَّد 29h بالفعل داخل
            # send_message_and_make_public — تخطٍ صامت فوري للحساب التالي:
            # لا progress_callback، لا إشعار للمستخدم، لا حظر auth_failed خاطئ.
            # Unconfirmed compact is handled before the business send. Only an
            # unsafe/unreadable session or failed durable deferral blocks that send.
            if status in ("CREDIT_UNCONFIRMED", "TIMEOUT", "READ_FAILED", "ACTIVITY_STOPPED"):
                return pub_url, status, curr_acc, ext_dir, last_text

            if status == "LOW_BALANCE":
                notify_account_selection_observer(
                    bridge_cfg,
                    "low-balance-skip",
                    status="LOW_BALANCE",
                    max_attempts=max_attempts,
                )
                log_event("info", "⏭️ تخطٍ صامت لحساب برصيد منخفض (مُبرَّد 29h) — الانتقال للحساب التالي", email=curr_email)
                continue

            # 🧬 [P20] خطأ AI Data Retention → بروتوكول نفاد الرصيد نفسه (تبريد 29h + حساب تالٍ)
            # لكن بتنبيه مميز، ومع إعادة إرسال «نفس آخر رسالة» المستخدمة في نفس الحساب
            # (سواء كانت رسالة استئناف أو رسالة مشروع جديد) — بدون التحويل لبرومبت الاستئناف.
            if status == "DATA_RETENTION":
                notify_account_selection_observer(
                    bridge_cfg,
                    "data-retention-blocked",
                    status="DATA_RETENTION",
                    max_attempts=max_attempts,
                )
                mark_account_cooldown(curr_email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                log_event(
                    "warning",
                    "🧬 [P20] رُصد خطأ AI Data Retention على هذا الحساب — معاملة كنفاد رصيد: تبريد وانتقال لحساب آخر مع إعادة إرسال نفس آخر رسالة كما هي",
                    email=curr_email,
                )
                # 🔄 [P44][D3] استثناء P20: لا Live Rebind هنا إطلاقاً — عقد
                # DATA_RETENTION الموثق = «إعادة إرسال نفس آخر رسالة كما هي»
                # (الفرع يعمل continue ولا يمر على بناء active_query أصلاً).
                log_event(
                    "info",
                    f"🔄 [P44] LIVE_REBIND_SKIPPED_P20 project={str(getattr(bridge_cfg, 'selection_project_key', '') or '')}",
                    email=curr_email,
                )
                continue

            if status == "CREDIT_EXHAUSTED" or (
                    status == "COMPLETED" and not is_model_decline_response(last_text)):
                duration = current_account_duration(bridge_cfg, curr_email)
                due = (duration <= COMPACT_TRIGGER_SECONDS
                       and not getattr(bridge_cfg, "compact_deferred", False))
                if status == "CREDIT_EXHAUSTED" and due:
                    bridge_cfg.compact_before_send = True
                schedule = getattr(bridge_cfg, "compact_schedule_callback", None)
                if callable(schedule) and (due or status == "COMPLETED"):
                    try:
                        schedule(status, pub_url, duration)
                    except Exception as err:
                        # Optional maintenance scheduling cannot override a real
                        # business outcome or skip the credit preservation callback.
                        bridge_cfg.compact_before_send = False
                        bridge_cfg.compact_deferred = True
                        bridge_cfg.compact_deferred_this_run = True
                        log_event("warning", f"[COMPACT] SCHEDULE_DEFERRED: {type(err).__name__}", email=curr_email)

            if status == "CREDIT_EXHAUSTED":
                credit_continuations += 1
                bridge_cfg.last_credit_continuations = credit_continuations
                _set_credit_checkpoint_state(bridge_cfg, "PENDING", "awaiting checkpoint/report preservation")

            callback_result = None
            callback_error = None
            event_meta = {}
            if progress_callback:
                if bool(getattr(bridge_cfg, "project_fast_lean_skip", False)):
                    # No scan of stale artifact trees even before the fast callback.
                    emit_event = status not in NON_ACTIONABLE_PROGRESS_STATUSES
                    event_meta = {"reason": "fast mode: cloud metadata only"}
                else:
                    emit_event, event_meta = should_emit_progress_event(
                        pub_url, status, ext_dir, min_mtime=getattr(bridge_cfg, "run_started_at", None)
                    )
                public_stage_query = get_public_continuation_prompt_text(active_query)
                safe_last_text = redact_github_secrets(last_text)
                if emit_event:
                    try:
                        callback_result = progress_callback(pub_url, status, ext_dir, safe_last_text, curr_email, public_stage_query)
                    except Exception as callback_err:
                        callback_error = callback_err
                        log_event("warning", f"فشل حفظ تحديث المشروع بدون إيقاف المهمة: {callback_err}", email=curr_email)
                else:
                    log_event(
                        "info",
                        f"تمت فلترة progress event غير قابل للحفظ للحالة {status}: {event_meta.get('reason')}",
                        email=curr_email,
                        extra=event_meta,
                    )

            is_401 = status in ("SESSION_EXPIRED", "LOGIN_FAILED")
            if is_401:
                refresh_count = state_refresh.get(curr_email, 0)
                notify_account_selection_observer(
                    bridge_cfg,
                    "session-refresh-required",
                    status=str(status or "SESSION_EXPIRED"),
                    refresh_count=refresh_count,
                    max_attempts=max_attempts,
                )
                if refresh_count >= 1:
                    notify_account_selection_observer(
                        bridge_cfg,
                        "session-refresh-exhausted",
                        status="auth_failed",
                        refresh_count=refresh_count,
                    )
                    log_event("error", "الحساب فشل بعد التجديد مرة واحدة -> وضع الحظر المؤقت", email=curr_email)
                    update_account_data(curr_email, {"status": "auth_failed", "active": False, "cooldown_until": time.time() + 1800}, json_path=json_path)
                    continue

                state_refresh[curr_email] = refresh_count + 1
                log_event("warning", "401 session منتهية! جاري التجديد مع راندوم Backoff...", email=curr_email)
                time.sleep(1 + random.uniform(0.5, 1.5))
                update_account_data(curr_email, {"cookies": {}, "status": "SESSION_EXPIRED"}, json_path=json_path)
                try:
                    mod = get_genspark_engine()
                    new_cookies = refresh_cookies_on_401(mod, curr_email, curr_pass, json_path=json_path)
                    if new_cookies and isinstance(new_cookies, dict):
                        notify_account_selection_observer(
                            bridge_cfg,
                            "session-refresh-succeeded",
                            status="active",
                            refresh_count=state_refresh.get(curr_email, 0),
                        )
                        tried_emails.discard(curr_email)
                        continue
                except Exception as e:
                    log_event("error", f"فشل تجديد كوكيز الحساب: {e}", email=curr_email)
                notify_account_selection_observer(
                    bridge_cfg,
                    "session-refresh-failed",
                    status="auth_failed",
                    refresh_count=state_refresh.get(curr_email, 0),
                )
                update_account_data(curr_email, {"cooldown_until": time.time() + 1800, "status": "auth_failed", "active": False}, json_path=json_path)
                continue

            if status == "CREDIT_EXHAUSTED":
                notify_account_selection_observer(
                    bridge_cfg,
                    "credit-exhausted-observed",
                    status="CREDIT_EXHAUSTED",
                    continuation_index=credit_continuations,
                    continuation_limit=max_credit_continuations,
                )
                mark_account_cooldown(curr_email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                gate = evaluate_credit_checkpoint_gate(
                    bridge_cfg,
                    callback_result=callback_result,
                    callback_error=callback_error,
                    progress_callback_present=bool(progress_callback),
                )
                if not gate["allow_continuation"]:
                    notify_account_selection_observer(
                        bridge_cfg,
                        "continuation-blocked",
                        status="CREDIT_EXHAUSTED",
                        reason=str(gate.get("reason") or ""),
                    )
                    log_event(
                        "error",
                        f"تم إيقاف continuation بعد نفاد الرصيد لأن checkpoint/report لم يثبت قبل المتابعة: {gate['reason']}",
                        email=curr_email,
                        extra=event_meta if event_meta else None,
                    )
                    return pub_url, status, curr_acc, ext_dir, last_text
                if credit_continuations >= max_credit_continuations:
                    notify_account_selection_observer(
                        bridge_cfg,
                        "credit-continuations-exhausted",
                        status="CREDIT_EXHAUSTED",
                        continuation_index=credit_continuations,
                        continuation_limit=max_credit_continuations,
                    )
                    log_event(
                        "error",
                        f"تجاوزنا الحد الآمن لمحاولات الاستئناف بعد نفاد الرصيد ({credit_continuations}/{max_credit_continuations})",
                        email=curr_email,
                    )
                    return pub_url, status, curr_acc, ext_dir, last_text

                source_pid = extract_project_id(pub_url) if pub_url else ""
                continuation_url = pub_url or (
                    f"https://www.genspark.ai/autopilotagent_viewer?id={source_pid}" if source_pid else active_url
                )
                if not continuation_url:
                    log_event("error", "تعذر تحديد رابط المشروع لاستئنافه بحساب آخر", email=curr_email)
                    return pub_url, status, curr_acc, ext_dir, last_text

                bridge_cfg.last_credit_resume_target_url = continuation_url
                bridge_cfg.last_credit_resume_project_id = source_pid or extract_project_id(continuation_url)
                # 🔄 [P44][D1] Live Rebind: إعادة قراءة الـ manifest حياً قبل بناء برومبت
                # الاستئناف — تعديل المستخدم أثناء الجلسة يصل لأول استئناف بعد نفاد الرصيد.
                # [D2] Fail-Open: أي استثناء → نكمل بالصورة القديمة (Snapshot₀) بصفر كسر.
                # [D3] فرع DATA_RETENTION مستثنى تماماً (لا يمر هنا — عقد P20 «نفس آخر رسالة»).
                # [D4] Display Parity: الـ rebind يسبق إشعار continuation-handoff-ready ليقرأ
                # الكارت (القراءة الحية في notify — continuation_prompt_public) القيمة ذاتها
                # التي ستُرسل فعلاً — «اللي يظهر = اللي يتبعت». قراءة الـ manifest تتم خلف
                # قفل الـ Registry القائم (self.lock) — بلا أي أقفال جديدة.
                # التوقيع القائم بنفس نمط الاستدعاء المرجعي في مسار المحرك.
                try:
                    apply_project_runtime_binding(
                        bridge_cfg,
                        getattr(bridge_cfg, "selection_project_key", "") or None,
                        requested_model=getattr(bridge_cfg, "model", DEFAULT_PROJECT_MODEL),
                    )
                    log_event(
                        "info",
                        f"🔄 [P44] LIVE_REBIND_OK project={str(getattr(bridge_cfg, 'selection_project_key', '') or '')}",
                        email=curr_email,
                    )
                except Exception as _rb_err:
                    log_event(
                        "warning",
                        f"🔄 [P44] LIVE_REBIND_FALLBACK reason={_rb_err}",
                        email=curr_email,
                    )
                notify_account_selection_observer(
                    bridge_cfg,
                    "continuation-handoff-ready",
                    status="CREDIT_EXHAUSTED",
                    continuation_index=credit_continuations,
                    continuation_limit=max_credit_continuations,
                    continuation_url=continuation_url,
                    source_project_id=bridge_cfg.last_credit_resume_project_id,
                    checkpoint_id=gate.get("checkpoint_id") or getattr(bridge_cfg, "last_credit_checkpoint_id", ""),
                )
                handoff_callback = getattr(bridge_cfg, "credit_handoff_callback", None)
                if callable(handoff_callback):
                    try:
                        handoff_callback({
                            "source_project_id": bridge_cfg.last_credit_resume_project_id,
                            "continuation_url": continuation_url,
                            "checkpoint_id": gate.get("checkpoint_id") or getattr(bridge_cfg, "last_credit_checkpoint_id", ""),
                            "continuation_index": credit_continuations,
                            "continuation_limit": max_credit_continuations,
                        })
                    except Exception as notify_err:
                        log_event("warning", f"فشل تبليغ handoff بدون إيقاف المتابعة: {notify_err}", email=curr_email)

                active_url = continuation_url
                # 🔄 [P44][D4] active_query يُبنى من نفس القيمة الحية التي قرأها الكارت أعلاه
                # (الـ rebind تم قبل continuation-handoff-ready) — تطابق العرض/الإرسال مضمون.
                active_query = get_bridge_cfg_runtime_resume_prompt(bridge_cfg)
                public_resume_prompt = summarize_resume_prompt_for_display(get_bridge_cfg_public_resume_prompt(bridge_cfg))
                log_event(
                    "warning",
                    f"نفد الرصيد؛ الرد غير مكتمل. الانتقال تلقائياً لحساب آخر وإرسال برومبت الاستئناف «{public_resume_prompt}» ({credit_continuations}/{max_credit_continuations})",
                    email=curr_email
                )
                continue

            if pub_url or status == "COMPLETED":
                notify_account_selection_observer(
                    bridge_cfg,
                    "attempt-succeeded",
                    status=str(status or "COMPLETED"),
                    public_url=str(pub_url or ""),
                )
                update_account_data(curr_email, {
                    "last_used": time.time(),
                    "status": "active",
                    "active": True,
                    "cooldown_until": 0,
                    "last_success_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                }, json_path=json_path)
                return pub_url, status, curr_acc, ext_dir, last_text

            notify_account_selection_observer(
                bridge_cfg,
                "attempt-failed-continue",
                status=str(status or "FAILED"),
            )
            update_account_data(curr_email, {"cooldown_until": time.time() + 300}, json_path=json_path)
            continue
        finally:
            close_account_timing_span(bridge_cfg, curr_email)  # ⏱️ [P30] إغلاق حتمي للـ span في كل المسارات
            release_account_selection(curr_email, owner_token)
            bridge_cfg.selected_account_claim_state = "released"
    return None, "MAX_ATTEMPTS_EXHAUSTED", None, None, None


