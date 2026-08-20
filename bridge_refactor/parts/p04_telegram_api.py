"""[VERBATIM SLICE] p04_telegram_api
المصدر: 01.31_telegram_gen_bridge.py — الأسطر 832..1375
المحتوى: Telegram API core + send/edit + AccountSelection Live Renderer/Transport + P22: LiveOpsReporter (شفافية الباك-إند: timeline ترمنال + رسالة تليجرام حية + ⏱️ اخد X ثانية) + send_document
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
# ══════════════════════════════════════════════════════════════
# 📲 [Task-1] دوال الاتصال المباشر والرفع الآلي لبوت تليجرام
# ══════════════════════════════════════════════════════════════
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
        "text": str(text or ""),
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
# 📡 [P22] LiveOpsReporter — شفافية الباك-إند الكاملة:
#   1) التيرمينال: طباعة كل مرحلة بأسلوب pipeline موقوت (زي qwen.log.md)
#      + صندوق ختامي ملخص + سطر «⏱️ اخد X ثانية».
#   2) تليجرام: رسالة حية واحدة تُعدَّل (editMessageText) بآخر المراحل
#      والزمن المنقضي — مع throttling لاحترام rate limits.
# ══════════════════════════════════════════════════════════════
def format_elapsed_seconds(seconds: float) -> str:
    """تنسيق الزمن المنقضي بالعربي: 713.1 ثانية / 4.5 ثانية"""
    try:
        return f"{float(seconds):.1f} ثانية"
    except Exception:
        return "؟ ثانية"


class LiveOpsReporter:
    """مراسل العمليات الحية: timeline موحّد للمراحل يُبث للتيرمينال + رسالة تليجرام لايف."""

    TELEGRAM_EDIT_MIN_INTERVAL = 4.0   # ⏳ أدنى فاصل بين تعديلات الرسالة الحية (rate-limit safety)
    MAX_TIMELINE_LINES = 10            # آخر N أحداث تظهر في رسالة تليجرام

    def __init__(self, chat_id=None, project_name: str = "", project_key: str = "", enable_telegram: bool = True):
        self.chat_id = chat_id
        self.project_name = str(project_name or "")
        self.project_key = str(project_key or "")
        self.enable_telegram = bool(enable_telegram and chat_id is not None)
        self.started_at = time.time()
        self.timeline: list[dict] = []       # [{ts, icon, text, took}]
        self.stage_seq = 0
        self.current_status = "بدء التشغيل"
        self.finished = False
        self.message_id = None
        self._last_edit_at = 0.0
        self._lock = threading.Lock()

    # ─── طبقة التيرمينال ───────────────────────────────────────
    def _terminal_line(self, text: str, level: str = "info"):
        log_event(level, text)

    # ─── تسجيل الأحداث ─────────────────────────────────────────
    def event(self, text: str, icon: str = "•", level: str = "info", took: float | None = None, push: bool = True):
        """حدث عام: يُطبع في التيرمينال فوراً ويُضاف للـ timeline ويُحدَّث تليجرام (مع throttle)."""
        took_str = f" ({took:.2f}s)" if isinstance(took, (int, float)) else ""
        with self._lock:
            self.timeline.append({
                "ts": time.time(),
                "icon": icon,
                "text": str(text or ""),
                "took": took_str,
            })
        self._terminal_line(f"{icon} {text}{took_str}", level=level)
        if push:
            self.push_telegram()

    def stage(self, label: str, level: str = "info"):
        """بداية مرحلة مرقمة: [N] label — وترجع دالة إغلاق تطبع الزمن المستغرق."""
        with self._lock:
            self.stage_seq += 1
            seq = self.stage_seq
        started = time.time()
        self.current_status = label
        self.event(f"[{seq}] {label}...", icon="🔄", level=level)

        def _close(note: str = "", level_close: str = "info"):
            took = time.time() - started
            suffix = f" — {note}" if note else ""
            self.event(f"[{seq}] {label} ✔{suffix}", icon="✅", level=level_close, took=took)
            return took

        return _close

    def heartbeat(self, status_text: str, extra: str = ""):
        """نبضة دورية أثناء الانتظار الطويل (polling): سطر ترمنال + تحديث الرسالة الحية."""
        elapsed = time.time() - self.started_at
        self.current_status = status_text
        line = f"⏳ لسه شغال — {status_text} | مضى {format_elapsed_seconds(elapsed)}"
        if extra:
            line += f" | {extra}"
        self._terminal_line(line, level="info")
        with self._lock:
            self.timeline.append({"ts": time.time(), "icon": "⏳", "text": f"{status_text} (مضى {format_elapsed_seconds(elapsed)})", "took": ""})
        self.push_telegram()

    # ─── طبقة تليجرام الحية ────────────────────────────────────
    def render_telegram(self) -> str:
        elapsed = time.time() - self.started_at
        header = "🛰️ <b>متابعة الباك-إند لايف</b>" if not self.finished else "🏁 <b>انتهت المهمة — التقرير النهائي</b>"
        lines = [header]
        if self.project_name:
            lines.append(f"📌 <b>المشروع:</b> {html_escape(self.project_name)}")
        if self.project_key:
            lines.append(f"🔐 <b>المفتاح:</b> <code>{html_escape(self.project_key)}</code>")
        lines.append(f"📟 <b>الحالة الحالية:</b> <code>{html_escape(self.current_status)}</code>")
        lines.append(f"⏱️ <b>الزمن المنقضي:</b> <code>{html_escape(format_elapsed_seconds(elapsed))}</code>")
        lines.append("— <b>آخر الأحداث:</b>")
        with self._lock:
            recent = self.timeline[-self.MAX_TIMELINE_LINES:]
        for entry in recent:
            stamp = datetime.fromtimestamp(entry["ts"]).strftime("%H:%M:%S")
            lines.append(f"<code>{stamp}</code> {entry['icon']} {html_escape(entry['text'])}{html_escape(entry['took'])}")
        return "\n".join(lines)

    def push_telegram(self, force: bool = False):
        """تحديث الرسالة الحية مع throttling — أول نداء يرسل رسالة جديدة ثم تعديلات فقط."""
        if not self.enable_telegram:
            return False
        now = time.time()
        if not force and self.message_id and (now - self._last_edit_at) < self.TELEGRAM_EDIT_MIN_INTERVAL:
            return False
        text = self.render_telegram()
        try:
            if self.message_id:
                res = edit_telegram_message_text(self.chat_id, self.message_id, text)
                ok = bool(res.get("ok"))
            else:
                res = send_telegram_message_detailed(self.chat_id, text)
                ok = bool(res.get("ok"))
                if ok and res.get("message_id") is not None:
                    self.message_id = res.get("message_id")
            if ok:
                self._last_edit_at = now
            return ok
        except Exception as push_err:
            log_event("warning", f"📡 [P22] تعذر تحديث رسالة اللايف: {push_err}")
            return False

    # ─── الختام: صندوق التيرمينال + «⏱️ اخد X ثانية» ──────────
    def finish(self, final_status: str, summary_lines: list[str] | None = None):
        """طباعة الصندوق الختامي في التيرمينال + آخر تحديث للرسالة الحية بزمن التنفيذ الكلي."""
        if self.finished:
            return
        self.finished = True
        elapsed = time.time() - self.started_at
        self.current_status = f"انتهى — {final_status}"
        box_width = 52
        rows = [f"📊 الحالة النهائية : {final_status}"]
        if self.project_name:
            rows.append(f"📌 المشروع        : {self.project_name}")
        if self.project_key:
            rows.append(f"🔐 المفتاح        : {self.project_key}")
        rows.append(f"🧮 مراحل منفذة    : {self.stage_seq}")
        rows.extend(str(x) for x in (summary_lines or []))
        print(Fore.CYAN + "  ╭" + "─" * box_width + "╮")
        for row in rows:
            print(Fore.CYAN + f"  │ {row}")
        print(Fore.CYAN + "  ╰" + "─" * box_width + "╯")
        print(Fore.GREEN + Style.BRIGHT + f"  ⏱️ اخد {format_elapsed_seconds(elapsed)}")
        logger.info(f"📡 [P22] المهمة انتهت ({final_status}) — اخد {format_elapsed_seconds(elapsed)}")
        with self._lock:
            self.timeline.append({"ts": time.time(), "icon": "🏁", "text": f"انتهى ({final_status}) — ⏱️ اخد {format_elapsed_seconds(elapsed)}", "took": ""})
        self.push_telegram(force=True)


def get_live_ops_reporter(bridge_cfg) -> "LiveOpsReporter | None":
    """جلب مراسل العمليات الحية من إعدادات المهمة بأمان (None لو مش متفعل)."""
    reporter = getattr(bridge_cfg, "live_ops_reporter", None) if bridge_cfg is not None else None
    return reporter if isinstance(reporter, LiveOpsReporter) else None


def attach_live_ops_reporter(bridge_cfg, chat_id=None, project_name: str = "", project_key: str = "", enable_telegram: bool = True):
    """تركيب مراسل حي على إعدادات المهمة (idempotent — لا يستبدل مراسلاً قائماً)."""
    if bridge_cfg is None:
        return None
    existing = get_live_ops_reporter(bridge_cfg)
    if existing is not None:
        return existing
    reporter = LiveOpsReporter(
        chat_id=chat_id,
        project_name=project_name,
        project_key=project_key,
        enable_telegram=enable_telegram,
    )
    bridge_cfg.live_ops_reporter = reporter
    return reporter


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

