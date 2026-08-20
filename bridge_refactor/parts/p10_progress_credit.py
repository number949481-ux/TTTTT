"""[VERBATIM SLICE] p10_progress_credit
المصدر: 01.31_telegram_gen_bridge.py — الأسطر 4824..5104
المحتوى: Stage artifacts + progress gate + credit checkpoint gate + terminal outcome describer
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
def _is_fresh_artifact(path: pathlib.Path, min_mtime: float | None) -> bool:
    if min_mtime is None:
        return True
    try:
        return path.stat().st_mtime >= (float(min_mtime) - 1.0)
    except Exception:
        return False


def inspect_stage_artifacts(stage_dir: str | None, min_mtime: float | None = None) -> dict:
    details = {
        "stage_dir": str(stage_dir or ""),
        "stage_dir_exists": False,
        "archive_exists": False,
        "archive_fresh": False,
        "payload_files": 0,
        "fresh_payload_files": 0,
        "stale_only": False,
    }
    if not stage_dir:
        return details
    try:
        root = pathlib.Path(stage_dir).resolve()
    except Exception:
        return details
    if not root.exists() or not root.is_dir():
        return details
    details["stage_dir_exists"] = True
    archive_path = root / "webapp.tar.gz"
    if archive_path.exists() and archive_path.is_file() and archive_path.stat().st_size > 0:
        details["archive_exists"] = True
        details["archive_fresh"] = _is_fresh_artifact(archive_path, min_mtime)
    for item in root.rglob("*"):
        if item.is_file() and item.name != "webapp.tar.gz":
            details["payload_files"] += 1
            if _is_fresh_artifact(item, min_mtime):
                details["fresh_payload_files"] += 1
    any_artifacts = details["archive_exists"] or details["payload_files"] > 0
    details["stale_only"] = any_artifacts and not (details["archive_fresh"] or details["fresh_payload_files"] > 0)
    return details


def should_capture_project_update(stage_url: str | None, stage_status: str | None, stage_dir: str | None, min_mtime: float | None = None) -> tuple[bool, dict]:
    pid = extract_stage_project_id(stage_url, stage_dir)
    artifacts = inspect_stage_artifacts(stage_dir, min_mtime=min_mtime)
    has_artifacts = artifacts["archive_fresh"] or artifacts["fresh_payload_files"] > 0
    reason = ""
    if not pid:
        reason = "لا يوجد Project ID صالح للحفظ أو الاستئناف"
    elif artifacts["stale_only"]:
        reason = "الملفات الموجودة قديمة من تشغيل سابق وليست artefacts جديدة لهذه المحاولة"
    elif not has_artifacts:
        reason = "لا توجد ملفات أو archive صالحة للحفظ من هذه المحاولة"
    actionable = bool(pid and has_artifacts)
    return actionable, {
        "pid": pid,
        "status": str(stage_status or ""),
        "has_artifacts": has_artifacts,
        "reason": reason,
        **artifacts,
    }


NON_ACTIONABLE_PROGRESS_STATUSES = {
    "NO_ENGINE", "LOGIN_FAILED", "SESSION_EXPIRED", "FORBIDDEN",
    "FAILED", "CHAT_ERROR", "TIMEOUT",
}


def should_emit_progress_event(stage_url: str | None, stage_status: str | None, stage_dir: str | None, min_mtime: float | None = None) -> tuple[bool, dict]:
    status = str(stage_status or "").strip()
    actionable, meta = should_capture_project_update(stage_url, stage_status, stage_dir, min_mtime=min_mtime)
    if status not in NON_ACTIONABLE_PROGRESS_STATUSES:
        meta["emit_reason"] = "actionable-status"
        return True, meta
    if actionable:
        meta["emit_reason"] = "failure-with-salvageable-artifacts"
        return True, meta
    meta["emit_reason"] = "filtered-non-actionable-failure-event"
    return False, meta


def describe_archive_delivery(ext_dir: str | None) -> tuple[pathlib.Path | None, str | None]:
    if not ext_dir:
        return None, None
    archive_path = pathlib.Path(ext_dir) / "webapp.tar.gz"
    if not archive_path.exists() or not archive_path.is_file():
        return None, None
    # إرجاع None للرسالة حتى لا يتم إرسال أي إشعار مزعج في التليجرام
    return archive_path, None


def get_credit_continuation_limit(bridge_cfg: BridgeConfig | None) -> int:
    try:
        return max(1, int(getattr(bridge_cfg, "max_credit_continuations", 10) or 10))
    except Exception:
        return 10


def get_credit_continuation_progress(bridge_cfg: BridgeConfig | None) -> tuple[int, int]:
    limit = get_credit_continuation_limit(bridge_cfg)
    try:
        current = max(0, int(getattr(bridge_cfg, "last_credit_continuations", 0) or 0))
    except Exception:
        current = 0
    return current, limit


def format_credit_continuation_progress(bridge_cfg: BridgeConfig | None) -> str:
    current, limit = get_credit_continuation_progress(bridge_cfg)
    return f"{current}/{limit}"


def _set_credit_checkpoint_state(bridge_cfg: BridgeConfig | None, state: str, note: str = "") -> None:
    if bridge_cfg is None:
        return
    bridge_cfg.last_credit_checkpoint_state = str(state or "")
    bridge_cfg.last_credit_checkpoint_note = str(note or "")
    if not state:
        bridge_cfg.last_credit_checkpoint_id = ""
        bridge_cfg.last_credit_resume_target_url = ""
        bridge_cfg.last_credit_resume_project_id = ""


def _normalize_progress_callback_result(callback_result) -> dict:
    if isinstance(callback_result, dict):
        return {
            "allow_continuation": bool(callback_result.get("allow_continuation", True)),
            "project_update_preserved": callback_result.get("project_update_preserved"),
            "reason": str(callback_result.get("reason") or ""),
            "checkpoint_id": str(callback_result.get("checkpoint_id") or ""),
        }
    if callback_result is False:
        return {
            "allow_continuation": False,
            "project_update_preserved": False,
            "reason": "progress_callback returned False",
            "checkpoint_id": "",
        }
    return {
        "allow_continuation": True,
        "project_update_preserved": None,
        "reason": "",
        "checkpoint_id": "",
    }


def evaluate_credit_checkpoint_gate(
    bridge_cfg: BridgeConfig | None,
    callback_result=None,
    callback_error: Exception | None = None,
    progress_callback_present: bool = False,
) -> dict:
    if not progress_callback_present:
        _set_credit_checkpoint_state(bridge_cfg, "UNTRACKED", "no progress callback attached")
        return {"allow_continuation": True, "reason": "", "checkpoint_id": ""}
    if callback_error is not None:
        reason = f"progress_callback failed: {callback_error}"
        _set_credit_checkpoint_state(bridge_cfg, "BLOCKED_CALLBACK_ERROR", reason)
        if bridge_cfg is not None:
            bridge_cfg.last_credit_checkpoint_id = ""
        return {"allow_continuation": False, "reason": reason, "checkpoint_id": ""}
    decision = _normalize_progress_callback_result(callback_result)
    if decision["project_update_preserved"] is True:
        note = decision["checkpoint_id"] or "checkpoint preserved"
        _set_credit_checkpoint_state(bridge_cfg, "PRESERVED", note)
        if bridge_cfg is not None:
            bridge_cfg.last_credit_checkpoint_id = decision["checkpoint_id"]
        return {
            "allow_continuation": bool(decision["allow_continuation"]),
            "reason": decision["reason"],
            "checkpoint_id": decision["checkpoint_id"],
        }
    if decision["project_update_preserved"] is False or not decision["allow_continuation"]:
        reason = decision["reason"] or "checkpoint/report was not preserved before continuation"
        _set_credit_checkpoint_state(bridge_cfg, "BLOCKED_NOT_PRESERVED", reason)
        if bridge_cfg is not None:
            bridge_cfg.last_credit_checkpoint_id = decision["checkpoint_id"]
        return {"allow_continuation": False, "reason": reason, "checkpoint_id": decision["checkpoint_id"]}
    _set_credit_checkpoint_state(bridge_cfg, "UNSPECIFIED", decision["reason"])
    if bridge_cfg is not None:
        bridge_cfg.last_credit_checkpoint_id = decision["checkpoint_id"]
    return {
        "allow_continuation": bool(decision["allow_continuation"]),
        "reason": decision["reason"],
        "checkpoint_id": decision["checkpoint_id"],
    }


def describe_credit_checkpoint_state(bridge_cfg: BridgeConfig | None) -> str:
    state = str(getattr(bridge_cfg, "last_credit_checkpoint_state", "") or "") if bridge_cfg else ""
    note = str(getattr(bridge_cfg, "last_credit_checkpoint_note", "") or "") if bridge_cfg else ""
    if state == "PRESERVED":
        if note:
            return f"تم حفظ آخر checkpoint صالح قبل التوقف ({note})."
        return "تم حفظ آخر checkpoint صالح قبل التوقف."
    if state == "BLOCKED_CALLBACK_ERROR":
        return f"لم يتم الانتقال تلقائياً للحساب التالي لأن حفظ checkpoint/report فشل: {note}."
    if state == "BLOCKED_NOT_PRESERVED":
        return f"لم يتم الانتقال تلقائياً للحساب التالي لأن آخر مرحلة CREDIT_EXHAUSTED لم تنتج checkpoint صالحاً: {note}."
    if state == "UNTRACKED":
        return "لم يكن هناك progress callback فعّال لتأكيد checkpoint/runtime preservation لهذه المرحلة."
    return ""


def describe_terminal_outcome(status: str | None, pub_url: str | None, bridge_cfg: BridgeConfig | None = None) -> dict:
    status = str(status or "").strip()
    if status == "COMPLETED":
        return {
            "kind": "success",
            "title": "🎉 <b>تم التوليد بنجاح!</b>",
            "note": "اكتمل التنفيذ أو تم الحصول على رابط عام صالح للمشروع.",
            "allow_preview": True,
        }

    mapping = {
        "MAX_ATTEMPTS_EXHAUSTED": (
            "⚠️ <b>توقفت المهمة بعد استنفاد كل محاولات تغيير الحسابات.</b>",
            "لم ينجح أي حساب في إكمال الطلب ضمن الحد المسموح للمحاولات.",
        ),
        "ALL_ACCOUNTS_IN_COOLDOWN": (
            "⚠️ <b>جميع الحسابات في فترة تبريد حالياً.</b>",
            "لا يوجد حساب جاهز الآن لبدء الطلب؛ جرّب لاحقاً بعد انتهاء التبريد.",
        ),
        "ALL_ACCOUNTS_BUSY": (
            "⏳ <b>الحسابات المؤهلة الحالية مشغولة بمهمات أخرى.</b>",
            "لا يوجد حساب حر الآن يمكن نسبه لهذه المهمة بأمان؛ أعد المحاولة بعد قليل.",
        ),
        "CREDIT_EXHAUSTED": (
            "⚠️ <b>توقف التنفيذ قبل الاكتمال بسبب نفاد الرصيد.</b>",
            " ".join(
                part for part in [
                    f"قد يكون تم حفظ آخر تقدم صالح، لكن المشروع لم يكتمل في هذه المحاولة. عداد الاستئناف الحالي: {format_credit_continuation_progress(bridge_cfg)}.",
                    describe_credit_checkpoint_state(bridge_cfg),
                ]
                if part
            ),
        ),
        "DATA_RETENTION": (
            "🧬 <b>توقفت المحاولة بسبب خطأ AI Data Retention على الحساب.</b>",
            "الموديل يتطلب تفعيل AI Data Retention من إعدادات الحساب (Settings → Data Controls)؛ عومل الحساب كنفاد رصيد وتم تبريده، وأعيد إرسال نفس آخر رسالة على حساب آخر إن وُجد.",
        ),
        "LOGIN_FAILED": (
            "⛔ <b>فشل التنفيذ بسبب مشكلة تسجيل دخول بالحسابات.</b>",
            "لم يتم الوصول إلى جلسة صالحة لإكمال الطلب؛ راجع حالة الحسابات أو جرّب لاحقاً.",
        ),
        "auth_failed": (
            "⛔ <b>فشل التنفيذ بسبب جلسة غير صالحة.</b>",
            "الحساب المستخدم دخل فترة تبريد بعد فشل التحقق أو التحديث.",
        ),
        "TIMEOUT": (
            "⏳ <b>توقفت المهمة بعد انتهاء مهلة الانتظار.</b>",
            "لم يصل رد نهائي صالح قبل انتهاء المهلة المحددة لهذه المحاولة.",
        ),
        "FAILED": (
            "⚠️ <b>انتهت المهمة بدون مشروع صالح مكتمل.</b>",
            "المحاولة انتهت بدون Project ID أو ناتج صالح للاستكمال.",
        ),
        "CHAT_ERROR": (
            "⚠️ <b>فشل التنفيذ بسبب خطأ أثناء إرسال الطلب.</b>",
            "حدث خطأ في طبقة المحادثة قبل اكتمال المشروع الحالي.",
        ),
        "NO_ENGINE": (
            "⛔ <b>تعذر بدء التنفيذ لعدم توفر محرك Genspark صالح.</b>",
            "لم يتم تحميل محرك التوليد المطلوب داخل البيئة الحالية.",
        ),
        "FORBIDDEN": (
            "⛔ <b>توقفت المهمة بسبب رفض الوصول للمشروع.</b>",
            "تم رفض الاستمرار في المشروع الحالي قبل الوصول إلى ناتج قابل للحفظ.",
        ),
    }
    title, note = mapping.get(
        status,
        (
            "⚠️ <b>انتهت المهمة بدون نجاح مكتمل.</b>",
            "الحالة النهائية لا تمثل نجاحاً كاملاً، لذلك لم يتم إعلان اكتمال المشروع.",
        ),
    )
    return {"kind": "failure", "title": title, "note": note, "allow_preview": False}


