"""[VERBATIM SLICE] p04_telegram_api
المصدر: 01.33_telegram_gen_bridge.py — الأسطر 1140..1664
المحتوى: Telegram API core + P34: ثوابت ودوال Safe Message Formatting (PREVIEW_MAX_CHARS/RES_MSG_MAX_CHARS/OUTGOING limits + _strip_partial_html_token + clamp_preview_text + enforce_completion_message_budget + clamp_outgoing_text محقونة في payload الإرسال) + send/edit + editMessageReplyMarkup (P25) + AccountSelection Live Renderer/Transport (P29: سطر الحساب النشط + سطر تبديل الحساب بعد handoff) + send_document + P28: ALLOWED_DOCUMENT_EXTENSIONS/MAX_DOCUMENT_SIZE_BYTES + download_telegram_document_text (getFile → تنزيل UTF-8 آمن بلا Crash)
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
def _call_telegram_api_json(method: str, payload: dict, timeout: int = 15) -> dict:
    if not TELEGRAM_BOT_TOKEN:
        return {"ok": False, "status_code": 0, "result": {}, "description": "BOT_TOKEN_MISSING", "error": "BOT_TOKEN_MISSING"}
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    last_error = None
    for mode in ("curl_cffi", "requests"):
        try:
            if mode == "curl_cffi":
                from curl_cffi import requests as cffi
                response = cffi.post(url, json=payload, timeout=timeout)
            else:
                import requests
                response = requests.post(url, json=payload, timeout=timeout)
            try:
                body = response.json()
            except Exception:
                body = {}
            result = body.get("result") if isinstance(body, dict) and isinstance(body.get("result"), dict) else {}
            description = str(body.get("description") or getattr(response, "text", "") or "") if isinstance(body, dict) else str(getattr(response, "text", "") or "")
            ok = bool(getattr(response, "status_code", 0) == 200 and (not isinstance(body, dict) or body.get("ok", True)))
            return {
                "ok": ok,
                "status_code": int(getattr(response, "status_code", 0) or 0),
                "result": result,
                "description": description[:300],
                "error": "" if ok else description[:300],
            }
        except Exception as err:
            last_error = err
            continue
    return {
        "ok": False,
        "status_code": 0,
        "result": {},
        "description": str(last_error or "").strip()[:300],
        "error": str(last_error or "").strip()[:300],
    }


# ✂️ [P34] Safe Message Formatting — ثوابت الحدود المركزية (تعريف وحيد لكل حد)
PREVIEW_MAX_CHARS = 1000            # الحد الأقصى لجسم معاينة آخر رسالة توليد
PREVIEW_TRUNCATION_SUFFIX = "\n... [انقر على الرابط لمشاهدة الرد الكامل]"
RES_MSG_MAX_CHARS = 3500            # الحد الأقصى لرسالة الاكتمال المجمعة بالكامل
OUTGOING_TEXT_HARD_LIMIT = 3900     # عتبة تفعيل القص في طبقة الإرسال
OUTGOING_TEXT_SAFE_LIMIT = 3800     # الطول الآمن النهائي بعد القص


def _strip_partial_html_token(text: str) -> str:
    """✂️ [P34] إزالة أي وسم `<...` أو كيان `&...` مبتور عند نقطة القص — يمنع 400 Bad Request من تيليجرام."""
    trimmed = str(text or "")
    lt = trimmed.rfind("<")
    if lt != -1 and ">" not in trimmed[lt:]:
        trimmed = trimmed[:lt]
    amp = trimmed.rfind("&")
    if amp != -1 and ";" not in trimmed[amp:]:
        trimmed = trimmed[:amp]
    return trimmed


def clamp_preview_text(clean_text: str) -> str:
    """✂️ [P34] قصّ جسم المعاينة إلى 1000 حرف كحد أقصى + لاحقة إرشادية لرابط الرد الكامل."""
    body = str(clean_text or "")
    if len(body) <= PREVIEW_MAX_CHARS:
        return body
    return _strip_partial_html_token(body[:PREVIEW_MAX_CHARS]) + PREVIEW_TRUNCATION_SUFFIX


def enforce_completion_message_budget(res_msg: str, preview_body: str = "") -> str:
    """✂️ [P34] ضمان ألا تتجاوز رسالة الاكتمال المجمعة 3500 حرف:
    1. القصّ يقع على جسم المعاينة فقط (البيانات التشغيلية والروابط محفوظة حرفياً).
    2. fallback أخير: قصّ الذيل إن ظل التجاوز قائماً بدون معاينة قابلة للتقليص.
    """
    msg = str(res_msg or "")
    if len(msg) <= RES_MSG_MAX_CHARS:
        return msg
    body = str(preview_body or "")
    overflow = len(msg) - RES_MSG_MAX_CHARS
    if body and body in msg:
        keep = max(0, len(body) - overflow - len(PREVIEW_TRUNCATION_SUFFIX))
        shrunk_core = _strip_partial_html_token(body[:keep])
        if shrunk_core.endswith(PREVIEW_TRUNCATION_SUFFIX):
            shrunk = shrunk_core
        else:
            shrunk = shrunk_core + PREVIEW_TRUNCATION_SUFFIX
        msg = msg.replace(body, shrunk, 1)
    if len(msg) > RES_MSG_MAX_CHARS:
        msg = _strip_partial_html_token(msg[:RES_MSG_MAX_CHARS])
    return msg


def clamp_outgoing_text(text: str) -> str:
    """✂️ [P34] شبكة الأمان في طبقة الإرسال: نص > 3900 حرفاً ➔ قصّ آمن إلى 3800 حرفاً.
    reply_markup لا يُمس إطلاقاً — كل صفوف الأزرار التفاعلية تبقى سليمة بالكامل."""
    raw = str(text or "")
    if len(raw) <= OUTGOING_TEXT_HARD_LIMIT:
        return raw
    return _strip_partial_html_token(raw[:OUTGOING_TEXT_SAFE_LIMIT])


def send_telegram_message_detailed(
    chat_id: int | str,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str = "HTML",
) -> dict:
    """إرسال رسالة نصية مع إرجاع message_id إن توفر، بدون كسر callers القديمة."""
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "توكن البوت غير مضبوط — لا يمكن إرسال رسائل تليجرام")
        return {"ok": False, "message_id": None, "error": "BOT_TOKEN_MISSING"}
    payload = {
        "chat_id": chat_id,
        # ✂️ [P34] القصّ الآمن 3900→3800 يتم هنا مركزياً — الأزرار في reply_markup تبقى كما هي
        "text": clamp_outgoing_text(text),
        "disable_web_page_preview": False,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    result = _call_telegram_api_json("sendMessage", payload, timeout=15)
    if not result.get("ok"):
        detail = result.get("error") or result.get("description") or "UNKNOWN_TELEGRAM_SEND_ERROR"
        log_event("error", f"فشل إرسال رسالة تليجرام: HTTP {result.get('status_code', 0)} - {detail}")
    if result.get("ok"): log_event("info", f"📤 [P44] TG_SEND_OK chars={len(str(payload.get('text', '')))} chat={chat_id} caller={sys._getframe(1).f_code.co_name} origin={sys._getframe(1).f_back.f_code.co_name + ':' + str(sys._getframe(1).f_back.f_lineno) if sys._getframe(1).f_back else 'ROOT'}")
    return {
        "ok": bool(result.get("ok")),
        "message_id": (result.get("result") or {}).get("message_id"),
        "status_code": result.get("status_code", 0),
        "error": result.get("error", ""),
        "description": result.get("description", ""),
    }


def edit_telegram_message_text(
    chat_id: int | str,
    message_id: int | str,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str = "HTML",
) -> dict:
    """تعديل رسالة تليجرام قائمة بأقل transport ممكن لمسار live status."""
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "توكن البوت غير مضبوط — لا يمكن تعديل رسائل تليجرام")
        return {"ok": False, "message_id": None, "error": "BOT_TOKEN_MISSING"}
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": str(text or ""),
        "disable_web_page_preview": False,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    result = _call_telegram_api_json("editMessageText", payload, timeout=15)
    description = str(result.get("description") or "")
    if not result.get("ok") and "message is not modified" in description.lower():
        return {"ok": True, "message_id": message_id, "status_code": result.get("status_code", 0), "error": "", "description": description}
    if not result.get("ok"):
        detail = result.get("error") or result.get("description") or "UNKNOWN_TELEGRAM_EDIT_ERROR"
        log_event("warning", f"فشل تعديل رسالة تليجرام live: HTTP {result.get('status_code', 0)} - {detail}")
    return {
        "ok": bool(result.get("ok")),
        "message_id": message_id,
        "status_code": result.get("status_code", 0),
        "error": result.get("error", ""),
        "description": result.get("description", ""),
    }


def edit_telegram_message_reply_markup(
    chat_id: int | str,
    message_id: int | str,
    reply_markup: dict | None,
) -> dict:
    """🛑 [P25] تعديل أزرار رسالة قائمة فقط (editMessageReplyMarkup) بدون لمس النص —
    يستخدم لتبديل كيبورد الإلغاء ⇄ كيبورد التأكيد على بطاقة المعاينة الحية."""
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "توكن البوت غير مضبوط — لا يمكن تعديل أزرار رسائل تليجرام")
        return {"ok": False, "message_id": None, "error": "BOT_TOKEN_MISSING"}
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": json.dumps(reply_markup or {"inline_keyboard": []}, ensure_ascii=False),
    }
    result = _call_telegram_api_json("editMessageReplyMarkup", payload, timeout=15)
    description = str(result.get("description") or "")
    if not result.get("ok") and "message is not modified" in description.lower():
        return {"ok": True, "message_id": message_id, "status_code": result.get("status_code", 0), "error": "", "description": description}
    if not result.get("ok"):
        detail = result.get("error") or result.get("description") or "UNKNOWN_TELEGRAM_MARKUP_ERROR"
        log_event("warning", f"فشل تعديل أزرار رسالة تليجرام: HTTP {result.get('status_code', 0)} - {detail}")
    return {
        "ok": bool(result.get("ok")),
        "message_id": message_id,
        "status_code": result.get("status_code", 0),
        "error": result.get("error", ""),
        "description": result.get("description", ""),
    }


def send_telegram_message(
    chat_id: int | str,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str = "HTML"
) -> bool:
    """إرسال رسالة نصية إلى تليجرام مع الحفاظ على العقد القديم (bool فقط)."""
    return bool(send_telegram_message_detailed(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode).get("ok"))


def _account_selection_event_title(event_type: str) -> str:
    titles = {
        "account-claimed": "🔄 <b>تم اختيار حساب للمحاولة الحالية</b>",
        "no-eligible-accounts": "⚠️ <b>لا توجد حسابات مؤهلة حالياً</b>",
        "eligible-accounts-busy": "⏳ <b>كل الحسابات المؤهلة الحالية مشغولة</b>",
        "session-refresh-required": "♻️ <b>الحساب يحتاج تجديد جلسة</b>",
        "session-refresh-succeeded": "✅ <b>تم تجديد الجلسة وسيُعاد استخدام الحساب</b>",
        "session-refresh-failed": "⛔ <b>فشل تجديد الجلسة</b>",
        "credit-exhausted-observed": "⚠️ <b>تم رصد نفاد الرصيد</b>",
        "data-retention-blocked": "🧬 <b>رُصد خطأ AI Data Retention — معاملة كنفاد رصيد</b>",
        "credit-continuations-exhausted": "⛔ <b>بلغنا حد استئناف الرصيد</b>",
        "continuation-blocked": "⛔ <b>تم حجب continuation</b>",
        "continuation-handoff-ready": "🔁 <b>تم تجهيز handoff إلى برومبت الاستئناف</b>",
        "attempt-succeeded": "✅ <b>المحاولة الحالية نجحت</b>",
        "attempt-failed-continue": "↪️ <b>المحاولة فشلت وسيستمر البحث</b>",
    }
    return titles.get(str(event_type or "").strip(), "ℹ️ <b>تحديث اختيار الحساب</b>")


class AccountSelectionLiveRenderer:
    """يبني نص live status من observer events مع آخر 3 محاولات كحد أقصى."""
    def __init__(self, project_key: str, project_name: str):
        self.project_key = str(project_key or "")
        self.project_name = str(project_name or "")
        self.latest_event_type = ""
        self.latest_status = ""
        self.final_note = ""
        self.latest_handoff_url = ""
        self.latest_handoff_checkpoint = ""
        self.entries: list[dict] = []
        self.refresh_total = 0
        self.continuation_line = "0/0"
        # 🧾 [P29] مراقبة الحساب النشط وتبديل الحساب بعد handoff
        self.active_email = ""
        self.pending_handoff_from = ""
        self.switch_line = ""

    def _upsert_entry(self, event: dict) -> dict:
        attempt_no = int(event.get("attempt_number") or 0)
        email = str(event.get("selected_account_email") or "")
        existing = next((item for item in self.entries if item.get("attempt_number") == attempt_no), None)
        if existing is None:
            existing = {
                "attempt_number": attempt_no,
                "email": email,
                "status": str(event.get("status") or ""),
                "label": "",
                "claim_state": str(event.get("selected_account_claim_state") or ""),
            }
            self.entries.append(existing)
        if email:
            existing["email"] = email
        if event.get("status"):
            existing["status"] = str(event.get("status") or "")
        if event.get("selected_account_claim_state"):
            existing["claim_state"] = str(event.get("selected_account_claim_state") or "")
        return existing

    def apply(self, event: dict) -> str:
        event_type = str(event.get("event") or "").strip()
        self.latest_event_type = event_type
        self.latest_status = str(event.get("status") or self.latest_status or "")
        self.continuation_line = f"{int(event.get('credit_continuations') or 0)}/{int(event.get('max_credit_continuations') or 0)}"
        entry = self._upsert_entry(event)
        # 🧾 [P29] تحديث الحساب النشط من snapshot الحدث فقط (لا Email وهمي)
        event_email = str(event.get("selected_account_email") or "").strip()
        if event_type == "account-claimed" and event_email:
            if self.pending_handoff_from and event_email != self.pending_handoff_from:
                # أول claim بعد handoff → سطر تبديل الحساب (الحساب الجديد لا يُعرف إلا الآن)
                self.switch_line = f"من <code>{html_escape(self.pending_handoff_from)}</code> ← إلى <code>{html_escape(event_email)}</code>"
            self.pending_handoff_from = ""
            self.active_email = event_email
        elif event_email:
            self.active_email = event_email

        continuation_prompt_public = summarize_resume_prompt_for_display(event.get("continuation_prompt_public"))
        labels = {
            "account-claimed": "تم اختيار الحساب — لم يبدأ الحكم على النتيجة بعد",
            "session-refresh-required": "الجلسة تحتاج تجديداً قبل استكمال نفس الحساب",
            "session-refresh-succeeded": "تم تجديد الجلسة بنجاح وسيُعاد استخدام نفس الحساب",
            "session-refresh-failed": "فشل تجديد الجلسة",
            "credit-exhausted-observed": "تم رصد نفاد الرصيد على هذه المحاولة",
            "data-retention-blocked": "🧬 رُصد خطأ AI Data Retention (الموديل يتطلب تفعيله بالحساب) — تبريد الحساب والانتقال لحساب آخر بنفس آخر رسالة",
            "continuation-handoff-ready": f"تم تجهيز handoff إلى برومبت الاستئناف «{continuation_prompt_public}» عند نقطة التنفيذ الحالية",
            "continuation-blocked": f"تم حجب handoff قبل برومبت الاستئناف «{continuation_prompt_public}»",
            "credit-continuations-exhausted": "بلغنا حد استئناف الرصيد",
            "attempt-succeeded": "المحاولة الحالية نجحت",
            "attempt-failed-continue": "المحاولة فشلت وسيستمر البحث في حساب آخر إن وجد",
            "eligible-accounts-busy": "كل الحسابات المؤهلة الحالية مشغولة",
            "no-eligible-accounts": "لا توجد حسابات مؤهلة حالياً",
        }
        if event_type in labels:
            entry["label"] = labels[event_type]
        if event_type == "session-refresh-required":
            self.refresh_total += 1
        if event_type == "continuation-handoff-ready":
            self.pending_handoff_from = event_email or self.active_email  # 🧾 [P29] الحساب السابق لحظة الـ handoff
            self.latest_handoff_url = str(event.get("continuation_url") or "")
            self.latest_handoff_checkpoint = str(event.get("checkpoint_id") or "")
            self.final_note = "تم تجهيز handoff الآن؛ لم يتم إعلان اكتمال المهمة بعد."
        elif event_type == "continuation-blocked":
            self.final_note = f"تم حجب handoff: {str(event.get('reason') or '')}".strip()
        elif event_type == "credit-continuations-exhausted":
            self.final_note = "تم الوصول إلى حد استئناف الرصيد الحالي."
        elif event_type == "eligible-accounts-busy":
            self.final_note = "كل الحسابات المؤهلة الحالية محجوزة لمهمات أخرى؛ لا توجد جولة انتظار إضافية."
        elif event_type == "no-eligible-accounts":
            self.final_note = "لا توجد حسابات مؤهلة حالياً وفق الواقع الحالي؛ لا توجد جولة انتظار أو retry إضافية من الـUI."
        elif event_type == "attempt-succeeded":
            self.final_note = "المحاولة الحالية نجحت؛ الرسالة النهائية العامة يمكن أن تأتي لاحقاً من مسار المهمة نفسه."

        return self.render()

    def render(self) -> str:
        lines = [_account_selection_event_title(self.latest_event_type)]
        if self.project_name:
            lines.append(f"<b>المشروع:</b> {html_escape(self.project_name)}")
        if self.project_key:
            lines.append(f"<b>مفتاح المشروع:</b> <code>{html_escape(self.project_key)}</code>")
        if self.active_email:
            lines.append(f"📧 <b>الحساب النشط:</b> <code>{html_escape(self.active_email)}</code>")
        if self.switch_line:
            lines.append(f"🔁 <b>تبديل الحساب:</b> {self.switch_line}")
        lines.append(f"<b>إجمالي المحاولات المرصودة:</b> <code>{len([x for x in self.entries if x.get('attempt_number')])}</code>")
        lines.append(f"<b>عداد الاستئناف:</b> <code>{html_escape(self.continuation_line)}</code>")
        if self.refresh_total:
            lines.append(f"<b>مرات تجديد الجلسة المرصودة:</b> <code>{self.refresh_total}</code>")
        lines.append("<b>آخر 3 محاولات:</b>")
        recent = sorted((entry for entry in self.entries if entry.get("attempt_number")), key=lambda item: item.get("attempt_number", 0), reverse=True)[:3]
        if recent:
            for entry in recent:
                lines.append(
                    f"• <code>{int(entry.get('attempt_number') or 0)}</code> — <code>{html_escape(str(entry.get('email') or ''))}</code>"
                    f" — {html_escape(str(entry.get('label') or entry.get('status') or 'بدون توصيف'))}"
                )
        else:
            lines.append("• لا توجد محاولة مرصودة بعد.")
        if self.latest_status:
            lines.append(f"<b>الحالة الحالية:</b> <code>{html_escape(self.latest_status)}</code>")
        if self.latest_handoff_checkpoint:
            lines.append(f"<b>Checkpoint الحالى:</b> <code>{html_escape(self.latest_handoff_checkpoint)}</code>")
        if self.latest_handoff_url:
            lines.append(f"<b>رابط handoff:</b> {html_escape(self.latest_handoff_url)}")
        if self.final_note:
            lines.append(f"<b>ملاحظة:</b> {html_escape(self.final_note)}")
        return "\n".join(lines)


def render_account_selection_live_text(event: dict, project_name: str = "") -> str:
    renderer = AccountSelectionLiveRenderer(project_key=str(event.get("project_key") or ""), project_name=project_name)
    return renderer.apply(event)


def render_account_selection_handoff_text(event: dict, project_name: str = "") -> str:
    continuation_prompt_public = summarize_resume_prompt_for_display(event.get("continuation_prompt_public"))
    return "\n".join(
        part for part in [
            f"🔁 <b>تم تجهيز handoff إلى برومبت الاستئناف «{html_escape(continuation_prompt_public)}»</b>",
            f"<b>المشروع:</b> {html_escape(project_name)}" if project_name else "",
            f"<b>مفتاح المشروع:</b> <code>{html_escape(str(event.get('project_key') or ''))}</code>" if event.get("project_key") else "",
            f"<b>الحساب الحالي:</b> <code>{html_escape(str(event.get('selected_account_email') or ''))}</code>" if event.get("selected_account_email") else "",
            f"<b>Checkpoint:</b> <code>{html_escape(str(event.get('checkpoint_id') or ''))}</code>" if event.get("checkpoint_id") else "",
            f"<b>برومبت الاستئناف:</b> <code>{html_escape(continuation_prompt_public)}</code>",
            f"<b>رابط handoff:</b> {html_escape(str(event.get('continuation_url') or ''))}" if event.get("continuation_url") else "",
            "<b>الوضع:</b> لم يكتمل المشروع بعد؛ تم الوصول فقط إلى نقطة handoff الحالية وفق `D-012`."
        ]
        if part
    )


class AccountSelectionLiveTransport:
    """ينقل observer events إلى رسالة Telegram واحدة قابلة للتعديل بأقل تغيير."""
    def __init__(self, chat_id: int | str, project_key: str, project_name: str):
        self.chat_id = chat_id
        self.project_key = str(project_key or "")
        self.project_name = str(project_name or "")
        self.message_id = None
        self.last_text = ""
        self.renderer = AccountSelectionLiveRenderer(project_key=self.project_key, project_name=self.project_name)
        self.sent_handoff_signatures: set[str] = set()

    def publish(self, event: dict) -> bool:
        text = self.renderer.apply(event)
        send_ok = False
        if self.message_id:
            edited = edit_telegram_message_text(self.chat_id, self.message_id, text)
            if edited.get("ok"):
                self.last_text = text
                send_ok = True
        if not send_ok:
            sent = send_telegram_message_detailed(self.chat_id, text)
            if sent.get("ok") and sent.get("message_id") is not None:
                self.message_id = sent.get("message_id")
                self.last_text = text
                send_ok = True
            else:
                send_ok = bool(sent.get("ok"))
        if str(event.get("event") or "") == "continuation-handoff-ready":
            signature = f"{event.get('attempt_number')}:{event.get('checkpoint_id')}:{event.get('continuation_url')}"
            if signature not in self.sent_handoff_signatures:
                self.sent_handoff_signatures.add(signature)
                send_ok = bool(send_telegram_message_detailed(self.chat_id, render_account_selection_handoff_text(event, project_name=self.project_name)).get("ok")) and send_ok
        return send_ok


def attach_account_selection_live_transport(bridge_cfg, chat_id: int | str, project_key: str, project_name: str):
    if bridge_cfg is None or getattr(bridge_cfg, "account_selection_observer", None):
        return getattr(bridge_cfg, "account_selection_observer", None) if bridge_cfg is not None else None
    transport = AccountSelectionLiveTransport(chat_id=chat_id, project_key=project_key, project_name=project_name)
    bridge_cfg.account_selection_observer = transport.publish
    return transport


# ══════════════════════════════════════════════════════════════
# 📄 [P28] استقبال ملفات المهام (.txt / .md) — Document Ingestion
# ══════════════════════════════════════════════════════════════
# الامتدادات النصية المسموح تحويلها إلى Prompt (تُقارن بعد lower()).
ALLOWED_DOCUMENT_EXTENSIONS = frozenset({".txt", ".md", ".markdown", ".text"})
# حد أقصى وقائي — أكبر منه يُرفض ودياً قبل أي تنزيل (يحمي خيط الـ Polling).
MAX_DOCUMENT_SIZE_BYTES = 5 * 1024 * 1024


def download_telegram_document_text(file_id: str) -> str | None:
    """تنزيل ملف نصي من تليجرام عبر getFile ثم رابط الملف، وإرجاع محتواه كنص UTF-8.

    أي فشل (شبكة / HTTP غير 200 / ok=false / file_path مفقود) يُرجع None
    بدون أي استثناء يتسرب لخيط الـ Polling — التنبيه الودي مسؤولية المستدعي.
    """
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "توكن البوت غير مضبوط — لا يمكن تنزيل الملفات")
        return None
    try:
        import requests
        meta_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"
        meta_resp = requests.get(meta_url, params={"file_id": str(file_id)}, timeout=(10, 30))
        if meta_resp.status_code != 200:
            log_event("error", f"getFile فشل: HTTP {meta_resp.status_code} - {meta_resp.text[:200]}")
            return None
        meta = meta_resp.json()
        if not meta.get("ok"):
            log_event("error", f"getFile أعاد ok=false: {str(meta)[:200]}")
            return None
        file_path = (meta.get("result") or {}).get("file_path") or ""
        if not file_path:
            log_event("error", "getFile نجح لكن file_path مفقود — لا يمكن التنزيل")
            return None
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        file_resp = requests.get(file_url, timeout=(10, 60))
        if file_resp.status_code != 200:
            log_event("error", f"تنزيل الملف فشل: HTTP {file_resp.status_code}")
            return None
        # errors="replace" يضمن عدم الانهيار على بايتات غير UTF-8 (ترميزات قديمة).
        return file_resp.content.decode("utf-8", errors="replace")
    except Exception as err:
        log_event("error", f"استثناء أثناء تنزيل الملف من تليجرام: {err}")
        return None


def send_telegram_document(
    chat_id: int | str,
    document_path: str | pathlib.Path,
    caption: str | None = None,
    max_attempts: int = 3
) -> bool:
    """رفع ملف إلى تليجرام مع إعادة فتح الملف وإعادة المحاولة عند انقطاع الاتصال."""
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "توكن البوت غير مضبوط — لا يمكن رفع الملفات")
        return False
    doc_p = pathlib.Path(document_path).resolve()
    if not doc_p.exists() or not doc_p.is_file():
        log_event("error", f"الملف المراد رفعه غير موجود: {doc_p}")
        return False

    # حد Bot API الحالي للوثائق؛ الفحص المبكر أوضح من انتظار ConnectionReset مبهم.
    max_document_bytes = 50 * 1024 * 1024
    if doc_p.stat().st_size > max_document_bytes:
        log_event("error", f"الملف أكبر من حد تليجرام للبوتات (50 MB): {doc_p.name}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    attempts = max(1, int(max_attempts))
    for upload_attempt in range(1, attempts + 1):
        log_event("info", f"جارٍ رفع الملف [{doc_p.name}] إلى تليجرام (Chat: {chat_id}) — محاولة {upload_attempt}/{attempts}...")
        try:
            # يجب فتح الملف داخل كل محاولة: الطلب السابق قد يكون استهلك الـ stream قبل انقطاعه.
            import requests
            with open(doc_p, "rb") as f:
                files = {"document": (doc_p.name, f, "application/gzip")}
                data = {"chat_id": str(chat_id)}
                if caption:
                    data["caption"] = caption[:1024]
                    data["parse_mode"] = "HTML"
                r = requests.post(url, data=data, files=files, timeout=(20, 600))
            if r.status_code == 200:
                log_event("success", f"تم رفع الملف [{doc_p.name}] إلى تليجرام بنجاح!")
                return True
            # أخطاء 4xx (عدا rate limit) لن تنجح بإعادة نفس الطلب.
            log_event("error", f"فشل رفع الملف: HTTP {r.status_code} - {r.text[:300]}")
            if 400 <= r.status_code < 500 and r.status_code != 429:
                return False
        except Exception as err:
            log_event("warning", f"انقطع/فشل رفع الملف (محاولة {upload_attempt}/{attempts}): {err}")

        if upload_attempt < attempts:
            delay = min(20, 2 ** upload_attempt) + random.uniform(0, 0.75)
            log_event("info", f"إعادة محاولة رفع الملف بعد {delay:.1f} ثانية...")
            time.sleep(delay)

    log_event("error", f"تعذر رفع الملف [{doc_p.name}] بعد {attempts} محاولات")
    return False

# ══════════════════════════════════════════════════════════════
# 🌳 [Task-2] شجرة التفريعات وعلم انتهاء المشروع
# ══════════════════════════════════════════════════════════════
