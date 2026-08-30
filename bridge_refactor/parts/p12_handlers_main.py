"""[VERBATIM SLICE] p12_handlers_main
المصدر: 01.33_telegram_gen_bridge.py — الأسطر 7079..8632
المحتوى: get_main_keyboard + handle_telegram_update + offset + polling + main (P42: كتلة Intent Guard & Safe Project Creation — AWAITING_PROJECT_CONFIRMATION + الثوابت top-level + classify_idle_text_intent (strong/ambiguous — صياغة فقط) + build_project_confirmation_keyboard (nonce لا نص — حد 64 بايت) + render_project_confirmation_card + handle_idle_intent_guard (البديل الوحيد للـ Fallback المحذوف — صفر Mutation) + forward_pending_prompt_after_wizard (Smart Prompt Forwarding بعد اكتمال الـ Wizard) + معالج pconf:yes/no:<nonce> ككتلة معزولة مبكرة (Anti-Stale + Idempotent Double-Click) + فرع حالة AWAITING_PROJECT_CONFIRMATION (نص جديد يُبطل البطاقة + Edge 6: رابط مشروع يفوز عبر منطق P41) + حمل pending_prompt في AWAITING_NEW_PROJECT_NAME + استدعاء forward في موضعي finalize | P41: handle_prompt_context_collision — حارس تصادم السياق النشط في فرعي AWAITING_NEW_PROMPT/AWAITING_CONT_PROMPT (سياق A نشط + رابط B ⟔ إغلاق السياق وتوجيه شرعي بدل التنفيذ الخطأ) + رفض صريح للرابط المشوّه في AWAITING_CONT_URL والفرع العام + عميل getUpdates = requests النقية حصرياً في run_telegram_polling (Clean Shutdown — curl_cffi باقٍ بكل مسارات Genspark) + KeyboardInterrupt/SystemExit يصعد من داخل الحلقة + خروج نظيف برسالة + sys.exit(0) | P37: معالج cmd:decline_retry:{key} — فتح بطاقة ملخص الاستئناف فوراً عبر start_project_resume_from_key + AWAITING_PROJECT_RESUME_DECISION بسياق نظيف + fallback مهذب عند الفشل | P35: معالجا cmd:decline_retry (إرشاد إعادة الصياغة — fallback بلا مفتاح) + cmd:decline_dashboard (لوحة التحكم — مكافئ حرفياً لـ cmd:dashboard بفرع منفصل) | P17: بوابة is_chat_allowed للمسارين | P19: معالجات cmd:resume_copy_settings + cpysrc: | P25: معالجات cancel_prompt/cancel_exec/cancel_abort | P26: معالجات pdel_prompt/pdel_abort/pdel_exec ككتلة معزولة مبكرة | P27: معالجات cmd:list_projects/plist:page:/plist:noop — تصفح الصفحات In-Place | P28: كتلة Document Ingestion المعزولة — .txt/.md → text بعد بوابة الصلاحيات وقبل /start مع دمج Caption ورفض ودي للامتداد/الحجم | P32: معالجات cmd:account_pwd_lookup/acc_page:/acc_view:/acc_cancel + المسار اليدوي AWAITING_ACCOUNT_PASSWORD_LOOKUP كأول فحص في سلسلة الحالات | P33: فرع cmd:dashboard المكافئ حرفياً لـ cmd:show_dashboard | P43: معالجا cmd:new_proj_fast_no/yes لخطوة Wizard وضع الملفات (pending_fast_mode في state) + عرض الخطوة فقط عند تخطي GitHub (D3) + معالج pset:fastmode (toggle bool حصراً) + معالج pctl:fetch — التنزيل المتأخر بالدوال القائمة مع رسالة فشل صريحة للجلسة المنتهية (D6))
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
# ══════════════════════════════════════════════════════════════
# 🛡️ [P42] Intent Guard & Safe Project Creation Flow
# ══════════════════════════════════════════════════════════════
# العقد المعماري (وثيقة 16_INTENT_GUARD_AND_SAFE_CREATION.MD / DEC-038):
#  • المبدأ الحاكم: Confirmation before ANY Mutation — أي نص حر في IDLE
#    ممنوع بنيوياً أن يصل للحدود الخمسة (توليد مفتاح/قفل تشغيل/تسجيل/
#    حجز حساب/بدء توليد) إلا عبر الـ Wizard الرسمي بعد تأكيد صريح.
#  • الـ Fallback القديم (نص عابر ⟔ مشروع تلقائي) حُذف من الوجود —
#    استُبدل باستدعاء handle_idle_intent_guard حصرياً.
#  • nonce (12 hex — نمط new_cancel_token) في callback_data والحالة معاً:
#    Anti-Stale-Callback + Idempotency، والنص يعيش في user_state فقط
#    (حد تيليجرام 64 بايت — pconf:yes:<nonce> = 21 بايت).
AWAITING_PROJECT_CONFIRMATION = "AWAITING_PROJECT_CONFIRMATION"
PROJECT_CONFIRM_CALLBACK_PREFIX = "pconf"
INTENT_GUARD_STRONG_MIN_CHARS = 20   # 🛡️ [P42] عتبة strong: طول النص
INTENT_GUARD_STRONG_MIN_WORDS = 4    # 🛡️ [P42] عتبة strong: عدد الكلمات
INTENT_GUARD_QUOTE_PREVIEW_LIMIT = 500  # 🛡️ [P42] قصّ الاقتباس للعرض فقط — pending_prompt يُحفظ كاملاً
INTENT_GUARD_STRONG_HINT = "🧠 يبدو هذا طلب مشروع حقيقي."
INTENT_GUARD_AMBIGUOUS_HINT = "🤔 يبدو نصاً عابراً — هل قصدت إنشاء مشروع؟"
INTENT_GUARD_EMPTY_MESSAGE = (
    "ℹ️ <b>لم أستلم نصاً يمكن العمل عليه.</b>\n"
    "أرسل وصف المشروع كنص، أو استخدم زر 🚀 مشروع جديد من لوحة التحكم."
)
INTENT_GUARD_EXPIRED_MESSAGE = "⌛ انتهت صلاحية هذا الطلب — أرسل النص من جديد لو ما زلت تريده."
INTENT_GUARD_ALREADY_CONFIRMED_MESSAGE = "ℹ️ تم بالفعل — أكمل خطوات الإعداد الجارية."
INTENT_GUARD_CANCELLED_MESSAGE = "🚮 تم الإلغاء — لم يُنشأ أي مشروع ولم يُحجز أي حساب."
PROJECT_CONFIRM_YES_LABEL = "✅ نعم، أنشئ مشروعاً بهذا الطلب"
PROJECT_CONFIRM_NO_LABEL = "❌ إلغاء"


def classify_idle_text_intent(text: str) -> str:
    """🛡️ [P42] تصنيف نية النص الحر في IDLE — نقية بلا أي أثر جانبي.

    strong = نص يشبه برومبت مشروع حقيقي (≥ 20 حرفاً و ≥ 4 كلمات)،
    ambiguous = نص قصير/رقمي/عابر. ⚠️ التصنيف يؤثر على صياغة البطاقة
    فقط — السلوك واحد (بطاقة تأكيد دائماً، صفر إنشاء تلقائي).
    """
    clean = str(text or "").strip()
    if len(clean) >= INTENT_GUARD_STRONG_MIN_CHARS and len(clean.split()) >= INTENT_GUARD_STRONG_MIN_WORDS:
        return "strong"
    return "ambiguous"


def build_project_confirmation_keyboard(nonce: str) -> dict:
    """🛡️ [P42] كيبورد بطاقة التأكيد — الزران يحملان الـ nonce لا النص (حد 64 بايت)."""
    safe_nonce = re.sub(r"[^a-f0-9]", "", str(nonce or ""))[:12]
    return make_inline_keyboard([
        [{"text": PROJECT_CONFIRM_YES_LABEL, "callback_data": f"{PROJECT_CONFIRM_CALLBACK_PREFIX}:yes:{safe_nonce}"}],
        [{"text": PROJECT_CONFIRM_NO_LABEL, "callback_data": f"{PROJECT_CONFIRM_CALLBACK_PREFIX}:no:{safe_nonce}"}],
    ])


def render_project_confirmation_card(text: str, intent: str) -> str:
    """🛡️ [P42] نص بطاقة التأكيد — اقتباس حرفي مُهرَّب مع قصّ للعرض فقط."""
    hint = INTENT_GUARD_STRONG_HINT if intent == "strong" else INTENT_GUARD_AMBIGUOUS_HINT
    quoted = str(text or "").strip()
    if len(quoted) > INTENT_GUARD_QUOTE_PREVIEW_LIMIT:
        quoted = quoted[:INTENT_GUARD_QUOTE_PREVIEW_LIMIT] + "…"
    return (
        f"{hint}\n\n"
        f"📝 <b>النص المستلم:</b>\n<code>{html_escape(quoted)}</code>\n\n"
        "⚠️ لن يُنشأ أي مشروع ولن يُحجز أي حساب قبل تأكيدك الصريح."
    )


def handle_idle_intent_guard(chat_id: int, text: str):
    """🛡️ [P42] حارس النية — البديل الوحيد للـ Fallback المحذوف.

    لا يملك أي صلاحية وصول للحدود الخمسة: نص فارغ ⟔ رفض مهذب،
    غير ذلك ⟔ بطاقة تأكيد بحالة AWAITING_PROJECT_CONFIRMATION
    (النص في pending_prompt والمعرف في confirm_nonce) — صفر Mutation.
    """
    clean = str(text or "").strip()
    if not clean:
        # Edge 3: صور/ستيكرز/Forward بلا نص ⟔ text="" — يُغلق أيضاً ثغرة المشروع بالنص الفارغ
        log_event("info", f"🛡️ [P42] Intent Guard EMPTY — رسالة بلا نص من chat={chat_id} (لا بطاقة، لا Mutation)")
        send_telegram_message(chat_id, INTENT_GUARD_EMPTY_MESSAGE)
        return
    intent = classify_idle_text_intent(clean)
    nonce = new_cancel_token()
    set_user_state(chat_id, {
        "action": AWAITING_PROJECT_CONFIRMATION,
        "pending_prompt": clean,
        "confirm_nonce": nonce,
    })
    log_event("info", f"🛡️ [P42] Intent Guard SHOWN ({intent}) — chat={chat_id} nonce={nonce} len={len(clean)}")
    send_telegram_message(
        chat_id,
        render_project_confirmation_card(clean, intent),
        reply_markup=build_project_confirmation_keyboard(nonce),
    )


def forward_pending_prompt_after_wizard(chat_id: int, state: dict, next_state: dict, settings: dict) -> dict:
    """🛡️ [P42] Smart Prompt Forwarding — تمرير البرومبت المحفوظ بعد اكتمال الـ Wizard.

    لا pending_prompt ⟔ ترجع next_state كما هي (السلوك القديم حرفياً — صفر انحدار).
    يوجد ⟔ جدولة process_user_task_async بسياق المشروع المُنشأ شرعياً
    (المفتاح/الاسم/الموديل من next_state — نفس معطيات فرع AWAITING_NEW_PROMPT)
    ثم ترجع {} (حالة نظيفة — البرومبت انطلق ولا انتظار لإدخال جديد).
    """
    pending_prompt = str((state or {}).get("pending_prompt") or "").strip()
    if not pending_prompt:
        return next_state
    project_key = str(next_state.get("project_key") or "")
    project_name = str(next_state.get("project_name") or "")
    project_model = normalize_project_model(next_state.get("project_model") or (settings or {}).get("model"))
    log_event("info", f"🛡️ [P42] Intent Guard FORWARDED — برومبت محفوظ ({len(pending_prompt)} حرفاً) انطلق تلقائياً لمشروع {project_key}")
    send_telegram_message(chat_id, "🚀 <b>برومبتك المحفوظ انطلق تلقائياً على المشروع الجديد.</b>")
    try:
        EXECUTOR.submit(process_user_task_async, chat_id, None, pending_prompt, project_model, project_key, project_name)
    except Exception as e:
        log_event("error", f"فشل جدولة المهمة: {e}")
    return {}


def get_main_keyboard(chat_id: int | None = None):
    if chat_id is None:
        return build_dashboard_keyboard(next(iter(ALLOWED_CHAT_IDS)))
    return build_dashboard_keyboard(int(chat_id))


def handle_prompt_context_collision(chat_id: int, state: dict, text: str, action: str) -> bool:
    """[P41] حارس تصادم السياق النشط — True = الرسالة عولجت (ممنوع جدولة البرومبت).

    سياق مشروع (A) نشط (AWAITING_NEW_PROMPT / AWAITING_CONT_PROMPT) + نص يحمل
    رابط/معرّف مشروع (B) ⟔ يستحيل تمرير الرابط كبرومبت للمشروع الخطأ:
    يُغلق السياق القديم ويُوجّه الرابط عبر المسار الشرعي نفسه (resolve_resume_context).
    الرابط المشوّه ⟔ رفض صريح مع بقاء السياق (يمكن إرسال برومبت صحيح بعده).
    برومبت عادي (kind=none) ⟔ False (المسار القديم حرفياً — صفر انحدار).
    """
    collision = detect_context_collision(state, text)
    if not collision:
        return False
    if collision["kind"] == "malformed":
        send_telegram_message(chat_id, MALFORMED_PROJECT_LINK_MESSAGE + "\n\nℹ️ ما زلت في وضع إدخال البرومبت — أرسل البرومبت النصي أو رابطاً صالحاً.")
        return True
    active_label = collision.get("active_project_key") or collision.get("active_pid") or str(state.get("project_name") or "") or "السياق الحالي"
    log_event("warn", f"🧭 [P41] تصادم سياق: رابط مشروع ({collision['pid']}) ورد أثناء {action} لـ ({active_label}) — أُغلق السياق ووُجّه الرابط لمساره الشرعي")
    set_user_state(chat_id, {})
    send_telegram_message(chat_id, f"🧭 <b>اكتشفت رابط مشروع بدل البرومبت.</b>\nأُغلق سياق إدخال البرومبت السابق ({html_escape(active_label)}) حمايةً من تنفيذ الرابط كمهمة على المشروع الخطأ — وجارٍ فتح الرابط المُرسل بمساره الصحيح:")
    ctx = resolve_resume_context(collision["raw"])
    if ctx["project_key"]:
        present_resume_summary(chat_id, project_key=ctx["project_key"], target_url=ctx["target_url"], target_pid=ctx["pid"])
    else:
        present_external_resume_decision(chat_id, target_url=ctx["target_url"], target_pid=ctx["pid"])
    return True


def handle_telegram_update(update: dict):
    if "callback_query" in update:
        cb = update["callback_query"]
        msg_info = cb.get("message") or {}
        chat_id = msg_info.get("chat", {}).get("id")
        if not chat_id:
            return
        data = cb.get("data", "")
        # [P17] مسار callback: نحكم بالجروب أو بهوية الضاغط نفسه (cb.from)
        if not is_chat_allowed(chat_id, (cb.get("from") or {}).get("id")):
            send_telegram_message(chat_id, "⛔ غير مصرح لك باستخدام هذا البوت.")
            return

        # ══════════════════════════════════════════════════════
        # 🛑 [P25] الإلغاء التفاعلي — خطوتا أمان قبل التنفيذ القهري
        # (يعالج مبكراً وبمعزل تام عن سلسلة if/elif — صفر تعارض مع pctl:* وغيرها)
        # ══════════════════════════════════════════════════════
        if data.startswith(("cancel_prompt:", "cancel_exec:", "cancel_abort:")):
            action, _, cancel_token = data.partition(":")
            entry = get_cancel_entry(cancel_token)
            card_msg_id = msg_info.get("message_id")
            if entry is None:
                # مهمة انتهت بالفعل أو توكن منتهي — ننظف الأزرار بهدوء
                if card_msg_id:
                    edit_telegram_message_reply_markup(chat_id, card_msg_id, None)
                send_telegram_message(chat_id, "ℹ️ هذه المهمة انتهت بالفعل — لا يوجد بناء نشط لإلغائه.")
                return
            live_pid = str(entry.get("live_pid") or "")
            if action == "cancel_prompt":
                # الخطوة 1: عرض كيبورد التأكيد فقط — لا إلغاء بعد
                if card_msg_id:
                    edit_telegram_message_reply_markup(
                        chat_id, card_msg_id,
                        build_live_preview_keyboard(live_pid, status="confirm_cancel", cancel_token=cancel_token),
                    )
            elif action == "cancel_abort":
                # تراجع: إعادة كيبورد التشغيل الأصلي والاستمرار كأن شيئاً لم يكن
                if card_msg_id:
                    edit_telegram_message_reply_markup(
                        chat_id, card_msg_id,
                        build_live_preview_keyboard(live_pid, status="running", cancel_token=cancel_token),
                    )
            elif action == "cancel_exec":
                # الخطوة 2 (مؤكدة): تفعيل الإلغاء القهري الفوري
                triggered = trigger_cancel(cancel_token)
                if triggered:
                    log_event("warning", f"🛑 [P25] المستخدم أكد إلغاء البناء (token={cancel_token}, pid={live_pid[:16]})")
                    if card_msg_id:
                        edit_telegram_message_text(
                            chat_id, card_msg_id,
                            "⛔ <b>تم إلغاء بناء المشروع فوراً بناءً على طلبك.</b>\n"
                            "🧹 جاري قطع البث وتحرير الحساب والموارد المحجوزة...",
                            reply_markup=None,
                        )
                else:
                    send_telegram_message(chat_id, "ℹ️ تعذر تفعيل الإلغاء — المهمة غالباً انتهت بالفعل.")
            return

        # ══════════════════════════════════════════════════════
        # 🗑️ [P26] حذف المشروع التفاعلي — تأكيد In-Place بخطوتي أمان
        # (كتلة معزولة مبكرة بنمط P25 — صفر تعارض مع pctl:/pset:/pview:)
        # ══════════════════════════════════════════════════════
        if data.startswith(("pdel_prompt:", "pdel_abort:", "pdel_exec:")):
            action, _, raw_key = data.partition(":")
            project_key = re.sub(r"[^A-Za-z0-9_-]", "_", str(raw_key or ""))[:80]
            card_msg_id = msg_info.get("message_id")
            if not project_key:
                send_telegram_message(chat_id, "⚠️ مفتاح المشروع غير صالح — لا يمكن المتابعة.")
                return
            if action == "pdel_prompt":
                # الخطوة 1: تحديث نفس الرسالة فوراً لشاشة التحذير — بدون Spam
                if card_msg_id:
                    edit_telegram_message_text(
                        chat_id, card_msg_id,
                        render_project_delete_confirm_text(project_key),
                        reply_markup=build_project_delete_confirm_keyboard(project_key),
                    )
                else:
                    send_telegram_message(chat_id, render_project_delete_confirm_text(project_key), reply_markup=build_project_delete_confirm_keyboard(project_key))
            elif action == "pdel_abort":
                # التراجع الفوري: عودة نفس الرسالة لشاشة التفاصيل — صفر تعديل ملفات
                if card_msg_id:
                    edit_telegram_message_text(
                        chat_id, card_msg_id,
                        render_project_status_text(project_key),
                        reply_markup=build_current_project_keyboard(project_key),
                    )
                else:
                    send_telegram_message(chat_id, render_project_status_text(project_key), reply_markup=build_current_project_keyboard(project_key))
            elif action == "pdel_exec":
                # الخطوة 2 (مؤكدة): الحذف الذري الشامل — الحماية تُفحص داخل الدالة
                outcome = delete_project_atomically(project_key)
                if outcome.get("ok"):
                    display_name = str(outcome.get("project_name") or project_key)
                    success_text = (
                        "✅ <b>تم حذف المشروع بنجاح.</b>\n"
                        f"📛 <b>الاسم:</b> {html_escape(display_name)}\n"
                        f"🔑 <b>المفتاح:</b> <code>{html_escape(project_key)}</code>\n"
                        "🧹 تم تنظيف الفهرس المركزي وشجرة الاستئناف ومجلد القرص بالكامل."
                    )
                    if card_msg_id:
                        edit_telegram_message_text(chat_id, card_msg_id, success_text, reply_markup=build_project_deleted_keyboard())
                    else:
                        send_telegram_message(chat_id, success_text, reply_markup=build_project_deleted_keyboard())
                elif outcome.get("reason") == "PROJECT_BUILD_ACTIVE":
                    warn_text = (
                        "🛡️ <b>لا يمكن حذف المشروع الآن — يوجد بناء نشط قيد التنفيذ.</b>\n"
                        "🛑 أوقف/ألغِ البناء الجاري أولاً (زر إلغاء البناء) ثم أعد المحاولة."
                    )
                    if card_msg_id:
                        edit_telegram_message_text(
                            chat_id, card_msg_id,
                            render_project_status_text(project_key),
                            reply_markup=build_current_project_keyboard(project_key),
                        )
                    send_telegram_message(chat_id, warn_text)
                elif outcome.get("reason") == "PROJECT_NOT_FOUND":
                    nf_text = "ℹ️ هذا المشروع محذوف بالفعل أو غير موجود في السجل."
                    if card_msg_id:
                        edit_telegram_message_text(chat_id, card_msg_id, nf_text, reply_markup=build_project_deleted_keyboard())
                    else:
                        send_telegram_message(chat_id, nf_text, reply_markup=build_project_deleted_keyboard())
                else:
                    send_telegram_message(chat_id, f"⚠️ تعذر إتمام الحذف: <code>{html_escape(str(outcome.get('reason') or 'UNKNOWN'))}</code> — راجع السجل.")
            return

        # ══════════════════════════════════════════════════════
        # 🛡️ [P42] بطاقة تأكيد إنشاء المشروع — pconf:yes/no:<nonce>
        # (كتلة معزولة مبكرة بنمط P25/P26 — صفر تعارض مع الفروع القائمة)
        # nonce مطابق لآخر بطاقة نشطة فقط ⟔ Anti-Stale + Idempotency
        # ══════════════════════════════════════════════════════
        if data.startswith(f"{PROJECT_CONFIRM_CALLBACK_PREFIX}:"):
            _, _, rest = data.partition(":")
            verb, _, raw_nonce = rest.partition(":")
            nonce = re.sub(r"[^a-f0-9]", "", str(raw_nonce or ""))[:12]
            state = get_user_state(chat_id)
            active = (
                state.get("action") == AWAITING_PROJECT_CONFIRMATION
                and nonce
                and state.get("confirm_nonce") == nonce
            )
            card_msg_id = msg_info.get("message_id")
            if verb == "yes":
                pending_prompt = str(state.get("pending_prompt") or "").strip()
                if active and pending_prompt:
                    # التأكيد لا ينفّذ أي Mutation — يدخل الـ Wizard الرسمي القائم فقط (DRY)
                    set_user_state(chat_id, {
                        "action": "AWAITING_NEW_PROJECT_NAME",
                        "pending_prompt": pending_prompt,
                        "consumed_confirm_nonce": nonce,
                    })
                    if card_msg_id:
                        edit_telegram_message_reply_markup(chat_id, card_msg_id, None)
                    log_event("info", f"🛡️ [P42] Intent Guard CONFIRMED — chat={chat_id} nonce={nonce} ⟔ دخول الـ Wizard الرسمي")
                    send_telegram_message(
                        chat_id,
                        "🚀 <b>بدء مشروع جديد</b>\n"
                        "اكتب اسم المشروع أولاً. الاسم يُطلب للمشروع الجديد فقط، وبعدها سنختار الموديل ثم نكمل إعداد GitHub أو بدون GitHub.\n"
                        "💾 <b>برومبتك محفوظ وسيُرسل تلقائياً بعد اكتمال الإعداد.</b>",
                    )
                elif nonce and str(state.get("consumed_confirm_nonce") or "") == nonce:
                    # Edge 4: Double-Click — الضغطة الثانية Idempotent بلا أي Mutation إضافي
                    log_event("info", f"🛡️ [P42] Intent Guard DUPLICATE — ضغطة تأكيد مكررة (chat={chat_id} nonce={nonce})")
                    send_telegram_message(chat_id, INTENT_GUARD_ALREADY_CONFIRMED_MESSAGE)
                else:
                    # Edge 1: بطاقة مُبطلة/قديمة — nonce لا يطابق آخر بطاقة نشطة
                    log_event("info", f"🛡️ [P42] Intent Guard EXPIRED — ضغطة على بطاقة مُبطلة (chat={chat_id} nonce={nonce})")
                    if card_msg_id:
                        edit_telegram_message_reply_markup(chat_id, card_msg_id, None)
                    send_telegram_message(chat_id, INTENT_GUARD_EXPIRED_MESSAGE)
            elif verb == "no":
                if active:
                    # إلغاء ⟔ تفريغ كامل — صفر مشروع / صفر تسجيل / صفر حجز / صفر توليد
                    set_user_state(chat_id, {})
                    if card_msg_id:
                        edit_telegram_message_reply_markup(chat_id, card_msg_id, None)
                    log_event("info", f"🛡️ [P42] Intent Guard CANCELLED — chat={chat_id} nonce={nonce} (صفر أثر)")
                    send_telegram_message(chat_id, INTENT_GUARD_CANCELLED_MESSAGE)
                else:
                    log_event("info", f"🛡️ [P42] Intent Guard EXPIRED — إلغاء على بطاقة مُبطلة (chat={chat_id} nonce={nonce})")
                    if card_msg_id:
                        edit_telegram_message_reply_markup(chat_id, card_msg_id, None)
                    send_telegram_message(chat_id, INTENT_GUARD_EXPIRED_MESSAGE)
            return

        if data == "cmd:show_dashboard":
            send_telegram_message(chat_id, render_dashboard_text(chat_id), reply_markup=get_main_keyboard(chat_id))
        elif data == "cmd:dashboard":
            # ⬅️ [P33] زر «رجوع للوحة التحكم» من رسالة الاكتمال — سلوك مطابق حرفياً
            # لـ cmd:show_dashboard (فرع منفصل عمداً: حراس P26 يرسون على حرفية الفرع القديم)
            send_telegram_message(chat_id, render_dashboard_text(chat_id), reply_markup=get_main_keyboard(chat_id))
        elif data == "cmd:decline_retry":
            # 🚫 [P35] زر «✒️ أعد صياغة البرومبت» بعد رفض الموديل — إرشاد فوري:
            # مؤشر الاستئناف لم يتقدم (الرفض كأن الطلب لم يُرسل)، فزر 🔄 استئناف
            # المشروع في نفس الرسالة يكمل من آخر نقطة صالحة قبل الرفض مباشرة.
            # (فرع الـ fallback القديم بحرفيته — يصل هنا فقط لو الكيبورد بلا مفتاح مشروع)
            send_telegram_message(
                chat_id,
                "✒️ <b>أعد صياغة البرومبت وأرسله الآن كرسالة جديدة.</b>\n"
                "🚫 الرفض عومل كأن الطلب لم يُرسل: مؤشر الاستئناف لم يتقدم ولم يُسجل أي ناتج.\n"
                "💡 جرّب صياغة أوضح أو قسّم الطلب لخطوات أصغر، ثم استخدم زر 🔄 استئناف هذا المشروع "
                "لإكمال نفس السياق، أو أرسل البرومبت مباشرة كمهمة جديدة.",
            )
        elif data.startswith("cmd:decline_retry:"):
            # 🔄 [P37] زر «✍️ أعد صياغة البرومبت» بمفتاح مشروع — فتح بطاقة ملخص
            # الاستئناف الكاملة فوراً: render_project_resume_summary_text + كيبوردها
            # التفاعلي (▶️ كمل الآن / ⚙️ عدّل الإعدادات) وضبط الحالة على
            # AWAITING_PROJECT_RESUME_DECISION بسياق المشروع النظيف (root/latest pid)
            # عبر start_project_resume_from_key — البرومبت الجديد التالي يكمل على
            # نفس المشروع مباشرة (المؤشر لم يتقدم لنقطة الرفض — عقد P35 محفوظ).
            retry_key = data.split("cmd:decline_retry:", 1)[1]
            if not start_project_resume_from_key(chat_id, retry_key):
                send_telegram_message(
                    chat_id,
                    "⚠️ <b>تعذر فتح ملخص الاستئناف لهذا المشروع.</b>\n"
                    "✒️ أعد صياغة البرومبت وأرسله كرسالة جديدة، أو استخدم زر 🔄 استئناف المشروع من الرسالة.",
                )
        elif data == "cmd:decline_dashboard":
            # 🚫 [P35] رجوع للوحة التحكم من رسالة الرفض — سلوك مطابق حرفياً لـ cmd:dashboard
            # (فرع منفصل عمداً — نفس فلسفة P33: ممنوع مسّ حرفية الفروع القديمة)
            send_telegram_message(chat_id, render_dashboard_text(chat_id), reply_markup=get_main_keyboard(chat_id))
        elif data == "cmd:new_proj":
            set_user_state(chat_id, {"action": "AWAITING_NEW_PROJECT_NAME"})
            send_telegram_message(chat_id, "🚀 <b>بدء مشروع جديد</b>\nاكتب اسم المشروع أولاً. الاسم يُطلب للمشروع الجديد فقط، وبعدها سنختار الموديل ثم نكمل إعداد GitHub أو بدون GitHub.")
        elif data.startswith("cmd:new_proj_model:"):
            state = get_user_state(chat_id)
            model_name = data.split("cmd:new_proj_model:", 1)[1]
            selected_model = normalize_project_model(model_name)
            if state.get("action") == "AWAITING_NEW_PROJECT_MODEL":
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_GITHUB_MODE",
                    "project_model": selected_model,
                })
                send_telegram_message(chat_id, f"✅ <b>الموديل المختار:</b> <code>{html_escape(selected_model)}</code>\nهل تريد تفعيل GitHub لهذا المشروع من البداية؟", reply_markup=build_new_project_github_choice_keyboard())
            elif state.get("action") == "AWAITING_PROJECT_SETTINGS_MODEL":
                project_key = str(state.get("project_key") or "")
                if not project_key:
                    send_telegram_message(chat_id, "ℹ️ افتح إعدادات مشروع موجود أولاً ثم اختر الموديل المطلوب.")
                else:
                    ProjectRegistry(project_key).set_project_model(selected_model)
                    set_user_state(chat_id, {})
                    send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم تحديث موديل المشروع.</b>\n<b>الموديل الجديد:</b> <code>{html_escape(selected_model)}</code>")
            elif state.get("action") == "AWAITING_BOUND_PROJECT_MODEL":
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_GITHUB_MODE",
                    "project_model": selected_model,
                })
                send_telegram_message(chat_id, f"✅ <b>الموديل المختار:</b> <code>{html_escape(selected_model)}</code>\nهل تريد تفعيل GitHub لهذا المشروع الخارجي من البداية؟", reply_markup=build_bound_project_github_choice_keyboard())
            else:
                send_telegram_message(chat_id, "ℹ️ ابدأ أولاً من زر <b>مشروع جديد</b> أو افتح إعدادات مشروع موجود أو ابدأ ربط مشروع خارجي قبل اختيار الموديل.")
        elif data == "cmd:new_proj_github_yes":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_NEW_PROJECT_GITHUB_MODE":
                send_telegram_message(chat_id, "ℹ️ ابدأ أولاً من زر <b>مشروع جديد</b> ثم اختر الموديل قبل إعداد GitHub.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_GITHUB_REPO",
                })
                send_telegram_message(chat_id, "🔗 <b>ربط GitHub لهذا المشروع</b>\nأرسل رابط المستودع أو الصيغة <code>owner/repo</code> أولاً.")
        elif data in {"cmd:new_proj_github_no", "cmd:new_proj_github_disable"}:
            state = get_user_state(chat_id)
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            project_model = normalize_project_model(state.get("project_model"))
            if not project_key or not project_name:
                send_telegram_message(chat_id, "ℹ️ ابدأ أولاً من زر <b>مشروع جديد</b> ثم اختر الاسم والموديل.")
            else:
                # ⚡ [P43-D4] GitHub معطل ⟔ خطوة الوضع السريع قبل برومبت الاستئناف
                # (مسار GitHub-yes لا يرى هذه الخطوة إطلاقاً ⟔ fast_mode=False ضمنياً)
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_FAST_MODE",
                    "project_model": project_model,
                    "pending_github_enabled": False,
                    "pending_github_repository": "",
                    "pending_github_token": "",
                    "pending_github_branch": "",
                    "pending_github_branch_mode": "disabled",
                    "pending_github_default_branch": "",
                    "pending_github_branches": [],
                    "pending_github_repo_check_status": "disabled",
                    "pending_fast_mode": False,
                })
                send_telegram_message(chat_id, f"✅ <b>سيتم إعداد المشروع بدون GitHub حالياً.</b>\n<b>الاسم:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\n<b>الموديل:</b> <code>{html_escape(project_model)}</code>\n\n⚡ <b>اختر وضع الملفات لهذا المشروع:</b>\n📦 <b>مشروع متكامل</b> — تنزيل الساندبوكس وحفظ الـ Diff بعد كل مهمة (الافتراضي).\n⚡ <b>توليد فائق السرعة</b> — تخطي تنزيل الملفات (يبقى الرابط العام والاستئناف، ويمكن التنزيل لاحقاً بزر ⬇️).", reply_markup=build_new_project_fast_mode_keyboard())
        elif data in {"cmd:new_proj_fast_no", "cmd:new_proj_fast_yes"}:
            # ⚡ [P43-D4] اختيار الوضع السريع — نجاة pending_prompt عبر **state (نمط 7113)
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_NEW_PROJECT_FAST_MODE":
                send_telegram_message(chat_id, "ℹ️ أكمل Wizard المشروع الجديد أولاً حتى تصل لخطوة وضع الملفات.")
            else:
                chosen_fast = data == "cmd:new_proj_fast_yes"
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION",
                    "pending_fast_mode": chosen_fast,
                })
                mode_line = (
                    "⚡ <b>الوضع السريع مفعّل</b> — سيُتخطى تنزيل الساندبوكس والـ Diff بعد كل مهمة."
                    if chosen_fast
                    else "📦 <b>المشروع المتكامل</b> — سيُحفظ الساندبوكس والـ Diff بعد كل مهمة."
                )
                send_telegram_message(chat_id, f"✅ <b>تم حفظ وضع الملفات.</b>\n{mode_line}\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_new_project_resume_prompt_keyboard())
        elif data.startswith("cmd:new_proj_branch_pick:"):
            chosen_branch = data[len("cmd:new_proj_branch_pick:"):]
            state = get_user_state(chat_id)
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            repository = str(state.get("pending_github_repository") or "")
            detected_default = str(state.get("pending_github_default_branch") or "")
            branches = list(state.get("pending_github_branches") or [])
            if not project_key or not project_name or not repository:
                send_telegram_message(chat_id, "ℹ️ لا توجد بيانات GitHub قيد الإعداد حالياً. ابدأ من <b>مشروع جديد</b>.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION",
                    "pending_github_enabled": True,
                    "pending_github_branch": chosen_branch,
                    "pending_github_branch_mode": "manual",
                    "pending_github_default_branch": detected_default,
                    "pending_github_branches": branches,
                    "pending_github_repo_check_status": "checked",
                })
                send_telegram_message(chat_id, f"✅ <b>تم اختيار الفرع بنجاح:</b> <code>{html_escape(chosen_branch)}</code>\n<b>المستودع:</b> <code>{html_escape(repository)}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_new_project_resume_prompt_keyboard())
        elif data == "cmd:new_proj_branch_default":
            state = get_user_state(chat_id)
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            repository = str(state.get("pending_github_repository") or "")
            detected_default = str(state.get("pending_github_default_branch") or "")
            branches = list(state.get("pending_github_branches") or [])
            if not project_key or not project_name or not repository:
                send_telegram_message(chat_id, "ℹ️ لا توجد بيانات GitHub قيد الإعداد حالياً. ابدأ من <b>مشروع جديد</b>.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION",
                    "pending_github_enabled": True,
                    "pending_github_branch": "",
                    "pending_github_branch_mode": "auto_default",
                    "pending_github_default_branch": detected_default,
                    "pending_github_branches": branches,
                    "pending_github_repo_check_status": "checked",
                })
                send_telegram_message(chat_id, f"✅ <b>تم حفظ إعداد GitHub المبدئي.</b>\n<b>المستودع:</b> <code>{html_escape(repository)}</code>\n<b>الفرع:</b> <code>{html_escape(detected_default or 'auto-default')}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_new_project_resume_prompt_keyboard())
        elif data == "cmd:new_proj_branch_manual":
            state = get_user_state(chat_id)
            if not state.get("pending_github_repository"):
                send_telegram_message(chat_id, "ℹ️ لا توجد بيانات مستودع جاهزة. أرسل أولاً رابط المستودع ثم التوكن من Wizard المشروع الجديد.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_GITHUB_BRANCH",
                })
                send_telegram_message(chat_id, "✍️ <b>أدخل اسم الـbranch المطلوب لهذا المشروع</b>\nمثال: <code>main</code> أو <code>develop</code> أو أي branch موجود عندك.")
        elif data == "cmd:new_proj_resume_default":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION":
                send_telegram_message(chat_id, "ℹ️ أكمل Wizard المشروع الجديد أولاً حتى تصل لخطوة برومبت الاستئناف.")
            else:
                settings, next_state = finalize_new_project_from_state(state, chat_id=chat_id, resume_prompt=DEFAULT_PROJECT_RESUME_PROMPT)
                # 🛡️ [P42] Smart Prompt Forwarding — لا pending_prompt ⟔ next_state كما هي (السلوك القديم حرفياً)
                next_state = forward_pending_prompt_after_wizard(chat_id, state, next_state, settings)
                set_user_state(chat_id, next_state)
                send_telegram_message(chat_id, f"✅ <b>تم حفظ إعدادات المشروع.</b>\n<b>الاسم:</b> {html_escape(str(state.get('project_name') or ''))}\n<b>المفتاح:</b> <code>{html_escape(str(state.get('project_key') or ''))}</code>\n<b>الموديل:</b> <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n<b>برومبت الاستئناف:</b> <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>\nأرسل الآن أول برومبت لبدء المشروع.")
        elif data == "cmd:new_proj_resume_custom":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION":
                send_telegram_message(chat_id, "ℹ️ أكمل Wizard المشروع الجديد أولاً حتى تصل لخطوة برومبت الاستئناف.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT",
                })
                send_telegram_message(chat_id, "✍️ <b>أدخل برومبت الاستئناف الخاص بهذا المشروع</b>\nلو أحببت لاحقاً يمكن تعديله من إعدادات المشروع. القيمة الافتراضية هي <code>تابع</code>.")
        elif data == "cmd:current_project":
            current = get_latest_project_for_chat(chat_id)
            if not current:
                send_telegram_message(chat_id, "⭐ <b>لا يوجد مشروع حالي محفوظ بعد.</b>\nاستخدم زر <b>مشروع جديد</b> أو أرسل رابط مشروع معروف للاستكمال.", reply_markup=get_main_keyboard(chat_id))
            else:
                send_telegram_message(chat_id, render_project_status_text(current["project_key"]), reply_markup=build_current_project_keyboard(current["project_key"]))
        elif data == "cmd:list_projects":
            # 📄 [P27] فتح شاشة تصفح المشاريع (الصفحة الأولى) — إصلاح الزر الميت + Pagination
            send_telegram_message(
                chat_id,
                render_projects_page_text(chat_id, page=1),
                reply_markup=build_projects_page_keyboard(chat_id, page=1),
            )
        elif data.startswith("plist:page:"):
            # 📄 [P27] تقليب الصفحات In-Place: تعديل نفس الرسالة — صفر Spam في المحادثة
            page_token = data.split("plist:page:", 1)[1]
            list_msg_id = msg_info.get("message_id")
            page_text = render_projects_page_text(chat_id, page=page_token)
            page_keyboard = build_projects_page_keyboard(chat_id, page=page_token)
            if list_msg_id:
                edit_telegram_message_text(chat_id, list_msg_id, page_text, reply_markup=page_keyboard)
            else:
                send_telegram_message(chat_id, page_text, reply_markup=page_keyboard)
        elif data == "plist:noop":
            # 📄 [P27] زر العداد «📄 N / X» — عرض فقط، لا يفعل شيئاً عمداً
            pass
        elif data.startswith("pview:"):
            project_key = data.split("pview:", 1)[1]
            send_telegram_message(chat_id, render_project_status_text(project_key), reply_markup=build_current_project_keyboard(project_key))
        elif data.startswith("pset:"):
            parts = data.split(":")
            action = parts[1] if len(parts) > 1 else ""
            project_key = re.sub(r"[^A-Za-z0-9_-]", "_", str(parts[2] if len(parts) > 2 else ""))[:80]
            identity = get_project_identity_record(project_key) or {}
            project_name = str(identity.get("project_name") or project_key)
            registry = ProjectRegistry(project_key)
            settings = registry.get_project_settings()
            github = settings.get("github", {})
            if action == "branch_pick":
                branch_name = ":".join(parts[3:]) if len(parts) > 3 else ""
                if not branch_name:
                    send_telegram_message(chat_id, "⚠️ لم يتم تحديد اسم الفرع بشكل صحيح.")
                else:
                    updated = update_existing_project_github_settings(project_key, branch=branch_name, branch_mode="manual", repo_check_status="checked")
                    set_user_state(chat_id, {})
                    send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم حفظ وتحديث GitHub branch للمشروع.</b>\n<b>الفرع المستخدم:</b> <code>{html_escape(branch_name)}</code>")
            if action == "view":
                set_user_state(chat_id, {})
                send_project_settings_panel(chat_id, project_key)
            elif action == "model":
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_MODEL",
                    "project_key": project_key,
                    "project_name": project_name,
                })
                send_telegram_message(chat_id, f"🧠 <b>تعديل موديل المشروع</b>\n<b>المشروع:</b> {html_escape(project_name)}\nاختر الموديل الجديد لهذا المشروع.", reply_markup=build_new_project_model_keyboard(back_callback=f"pset:view:{project_key}", back_label="⬅️ رجوع لإعدادات المشروع"))
            elif action == "resume":
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_RESUME_PROMPT",
                    "project_key": project_key,
                    "project_name": project_name,
                })
                send_telegram_message(chat_id, f"✍️ <b>تعديل برومبت الاستئناف</b>\n<b>المشروع:</b> {html_escape(project_name)}\nأرسل البرومبت الجديد الآن. القيمة الحالية هي <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>.")
            elif action == "repo":
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_GITHUB_REPO",
                    "project_key": project_key,
                    "project_name": project_name,
                    "settings_edit_scope": "repo_update",
                    "pending_github_enabled": bool(github.get("enabled")),
                })
                current_repo = str(github.get("repository") or "")
                current_repo_line = f"\n<b>المستودع الحالي:</b> <code>{html_escape(current_repo)}</code>" if current_repo else ""
                send_telegram_message(chat_id, f"🔗 <b>تعديل مستودع GitHub للمشروع</b>\n<b>المشروع:</b> {html_escape(project_name)}{current_repo_line}\nأرسل رابط المستودع الجديد أو الصيغة <code>owner/repo</code>.")
            elif action == "token":
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_GITHUB_TOKEN",
                    "project_key": project_key,
                    "project_name": project_name,
                    "settings_edit_scope": "token_update",
                    "pending_github_enabled": bool(github.get("enabled")),
                    "pending_github_repository": str(github.get("repository") or ""),
                })
                send_telegram_message(chat_id, f"🔑 <b>تحديث GitHub token للمشروع</b>\n<b>المشروع:</b> {html_escape(project_name)}\nأرسل token جديداً لهذا المشروع. لن أعرض قيمته في الرسائل.")
            elif action == "branch":
                repository = str(github.get("repository") or "").strip()
                if not repository:
                    send_telegram_message(chat_id, "⚠️ لا يوجد مستودع محفوظ لهذا المشروع بعد. استخدم زر <b>تعديل المستودع</b> أولاً.", reply_markup=build_project_settings_keyboard(project_key))
                else:
                    project_token = registry.get_project_github_token(allow_env_fallback=False)
                    if not project_token:
                        set_user_state(chat_id, {
                            "action": "AWAITING_PROJECT_SETTINGS_GITHUB_TOKEN",
                            "project_key": project_key,
                            "project_name": project_name,
                            "settings_edit_scope": "branch_update",
                            "pending_github_enabled": bool(github.get("enabled")),
                            "pending_github_repository": repository,
                        })
                        send_telegram_message(chat_id, f"🔑 <b>نحتاج GitHub token للمشروع قبل فحص الـbranch</b>\n<b>المشروع:</b> {html_escape(project_name)}\nأرسل token المشروع حتى أتحقق من الـdefault branch ثم أسمح لك بالتأكيد أو التعديل اليدوي.")
                    else:
                        inspection = inspect_github_repository(repository, token=project_token)
                        if inspection.get("ok"):
                            raw_branches = inspection.get("branches") or []
                            default_branch = inspection.get("default_branch") or (raw_branches[0] if raw_branches else "")
                            set_user_state(chat_id, {
                                "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH_DECISION",
                                "project_key": project_key,
                                "project_name": project_name,
                                "settings_edit_scope": "branch_update",
                                "pending_github_enabled": bool(github.get("enabled")),
                                "pending_github_repository": repository,
                                "pending_github_default_branch": default_branch,
                                "pending_github_branches": raw_branches,
                                "pending_github_repo_check_status": "checked",
                            })
                            summary_msg = format_github_repo_inspection_summary(repository, default_branch, raw_branches)
                            send_telegram_message(chat_id, summary_msg, reply_markup=build_existing_project_branch_choice_keyboard(project_key, branches=raw_branches, default_branch=default_branch))
                        else:
                            set_user_state(chat_id, {
                                "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH",
                                "project_key": project_key,
                                "project_name": project_name,
                                "settings_edit_scope": "branch_update",
                                "pending_github_enabled": bool(github.get("enabled")),
                                "pending_github_repository": repository,
                                "pending_github_default_branch": str(github.get("detected_default_branch") or ""),
                                "pending_github_branches": list(github.get("available_branches") or []),
                                "pending_github_repo_check_status": "manual-branch",
                            })
                            send_telegram_message(chat_id, f"⚠️ <b>تعذر فحص المستودع الآن:</b> {html_escape(inspection.get('reason') or 'سبب غير معروف')}\nأدخل branch يدويًا لهذا المشروع مثل <code>main</code> أو <code>develop</code>.")
            elif action == "branch_default":
                state = get_user_state(chat_id)
                if state.get("action") != "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH_DECISION" or str(state.get("project_key") or "") != project_key:
                    send_telegram_message(chat_id, "ℹ️ افتح أولاً خطوة تعديل الـbranch من إعدادات المشروع ثم اختر طريقة الحفظ.")
                else:
                    updated = finalize_existing_project_github_from_state(state, branch="", branch_mode="auto_default", repo_check_status="checked")
                    set_user_state(chat_id, {})
                    send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم تحديث GitHub branch للمشروع.</b>\n<b>الفرع المستخدم:</b> <code>{html_escape(updated.get('github', {}).get('detected_default_branch') or state.get('pending_github_default_branch') or 'auto-default')}</code>")
            elif action == "branch_manual":
                state = get_user_state(chat_id)
                if state.get("action") != "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH_DECISION" or str(state.get("project_key") or "") != project_key:
                    send_telegram_message(chat_id, "ℹ️ افتح أولاً خطوة تعديل الـbranch من إعدادات المشروع ثم اختر branch يدوي إذا أردت.")
                else:
                    set_user_state(chat_id, {
                        **state,
                        "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH",
                    })
                    send_telegram_message(chat_id, "✍️ <b>أدخل اسم الـbranch المطلوب لهذا المشروع</b>\nمثال: <code>main</code> أو <code>develop</code> أو أي branch موجود عندك.")
            elif action == "toggle":
                currently_enabled = bool(github.get("enabled"))
                if currently_enabled:
                    update_existing_project_github_settings(project_key, enabled=False, repo_check_status="disabled-by-user")
                    set_user_state(chat_id, {})
                    send_project_settings_panel(chat_id, project_key, prefix="✅ <b>تم تعطيل GitHub لهذا المشروع مع الاحتفاظ بالإعدادات المحفوظة.</b>")
                else:
                    repository = str(github.get("repository") or "").strip()
                    if not repository:
                        send_telegram_message(chat_id, "⚠️ لا يمكن تفعيل GitHub قبل حفظ المستودع لهذا المشروع. استخدم زر <b>تعديل المستودع</b> أولاً.", reply_markup=build_project_settings_keyboard(project_key))
                    else:
                        update_existing_project_github_settings(project_key, enabled=True, repo_check_status="enabled-by-user")
                        warning = ""
                        if not github.get("token_present"):
                            warning = "\n⚠️ <b>ملاحظة:</b> لا يوجد token محفوظ للمشروع حالياً؛ أضفه إذا كان المستودع خاصاً أو يحتاج صلاحيات كتابة."
                        set_user_state(chat_id, {})
                        send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم تفعيل GitHub لهذا المشروع بالإعدادات المحفوظة.</b>{warning}")
            elif action == "fastmode":
                # ⚡ [P43] Toggle الوضع السريع — يعكس ويحفظ ثم يعيد اللوحة بالكيبورد المحدّث.
                # الحدية 1: العلم يُقرأ عند بدء المهمة فقط — يسري من المهمة التالية.
                new_fast = not bool(settings.get("fast_mode"))
                registry.update_project_settings({"fast_mode": new_fast})
                set_user_state(chat_id, {})
                if new_fast:
                    prefix_msg = (
                        "⚡ <b>تم تفعيل الوضع السريع لهذا المشروع.</b>\n"
                        "سيتم تخطي تنزيل الساندبوكس وفك الضغط والـ Diff بعد اكتمال المهام القادمة "
                        "(ما دام GitHub معطلاً — تفعيل GitHub يعيد التنزيل إلزامياً).\n"
                        "يمكنك تنزيل الملفات لاحقاً بزر ⬇️ من كارت المشروع."
                    )
                else:
                    prefix_msg = (
                        "📦 <b>تم تعطيل الوضع السريع — عاد حفظ الساندبوكس والـ Diff.</b>\n"
                        "المهام القادمة ستنزّل الأرشيف وتحفظ اللقطات كالمعتاد."
                    )
                send_project_settings_panel(chat_id, project_key, prefix=prefix_msg)
            else:
                send_telegram_message(chat_id, "ℹ️ أمر إعدادات مشروع غير معروف.")
        elif data.startswith("pctl:"):
            _, action, project_key = data.split(":", 2)
            renderers = {
                "checkpoints": render_project_checkpoints_text,
                "archive": render_project_archive_text,
                "files": render_project_file_report_text,
                "history": render_project_history_text,
                "gh": render_project_github_status_text,
            }
            if action == "fetch":
                # ⬇️ [P43-D6] تنزيل الساندبوكس عند الطلب — Pipeline كامل بالدوال القائمة
                send_telegram_message(chat_id, run_project_late_fetch(project_key), reply_markup=build_current_project_keyboard(project_key))
            elif action in renderers:
                send_telegram_message(chat_id, renderers[action](project_key), reply_markup=build_current_project_keyboard(project_key))
            else:
                send_telegram_message(chat_id, run_project_upload_control(project_key, action), reply_markup=build_current_project_keyboard(project_key))
        elif data == "cmd:resume_continue":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_PROJECT_RESUME_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً ملخص الاستئناف للمشروع ثم اختر هل تريد المتابعة الآن.")
            else:
                project_key = str(state.get("project_key") or "")
                project_name = str(state.get("project_name") or "")
                project_model = normalize_project_model(state.get("project_model") or get_project_selected_model(project_key))
                target_url = str(state.get("url") or "")
                if target_url:
                    set_user_state(chat_id, {
                        "action": "AWAITING_CONT_PROMPT",
                        "url": target_url,
                        "project_key": project_key,
                        "project_name": project_name,
                        "project_model": project_model,
                    })
                    send_telegram_message(chat_id, f"✅ <b>جاهز لاستئناف المشروع.</b>\n<b>الاسم:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\n<b>الموديل:</b> <code>{html_escape(project_model)}</code>\nأرسل الآن التعديل أو البرومبت الجديد، وسيُستخدم السياق المحفوظ لهذا المشروع.")
                else:
                    set_user_state(chat_id, {
                        "action": "AWAITING_NEW_PROMPT",
                        "project_key": project_key,
                        "project_name": project_name,
                        "project_model": project_model,
                    })
                    send_telegram_message(chat_id, f"🆕 <b>هذا المشروع لا يملك رابط استئناف محفوظاً بعد.</b>\n<b>الاسم:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\n<b>الموديل:</b> <code>{html_escape(project_model)}</code>\nأرسل أول prompt الآن ليبدأ بنفس المفتاح والإعدادات المحفوظة.")
        elif data == "cmd:resume_settings":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_PROJECT_RESUME_DECISION" or not state.get("project_key"):
                send_telegram_message(chat_id, "ℹ️ افتح أولاً ملخص الاستئناف لمشروع محفوظ إذا أردت تعديل إعداداته قبل المتابعة.")
            else:
                send_project_settings_panel(chat_id, str(state.get("project_key") or ""), prefix="⚙️ <b>يمكنك تعديل إعدادات المشروع قبل المتابعة.</b>")
        elif data == "cmd:resume_quick_continue":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_UNBOUND_RESUME_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً رابط/Project ID غير محفوظ حتى تختار بين الحفظ أو الاستئناف السريع.")
            else:
                target_url = str(state.get("url") or "")
                pid_value = str(state.get("pid") or extract_project_id(target_url) or "")
                set_user_state(chat_id, {
                    "action": "AWAITING_CONT_PROMPT",
                    "url": target_url,
                    "project_key": "",
                    "project_name": "",
                    "project_model": DEFAULT_PROJECT_MODEL,
                    "pid": pid_value,
                })
                send_telegram_message(chat_id, f"⚡ <b>استئناف سريع بدون حفظ</b>\n<b>Project ID:</b> <code>{html_escape(pid_value)}</code>\nأرسل الآن التعديل أو البرومبت الذي تريد تنفيذه على هذا المشروع.")
        elif data == "cmd:resume_bind_saved":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_UNBOUND_RESUME_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً رابط/Project ID غير محفوظ حتى تبدأ ربطه كمشروع محفوظ.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_NAME",
                })
                send_telegram_message(chat_id, "📌 <b>ربط مشروع خارجي كمشروع محفوظ</b>\nاكتب اسماً واضحاً لهذا المشروع حتى يظهر لاحقاً في قائمة المشاريع.")
        elif data == "cmd:resume_copy_settings":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_UNBOUND_RESUME_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً رابط/Project ID غير محفوظ حتى تنسخ له إعدادات مشروع آخر.")
            elif not list_known_projects(chat_id=chat_id, limit=1):
                send_telegram_message(chat_id, "ℹ️ <b>لا توجد مشاريع محفوظة بعد لنسخ إعداداتها.</b>\nأنشئ مشروعاً محفوظاً أولاً ثم استخدم هذا الزر.", reply_markup=build_unbound_resume_keyboard())
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_COPY_SETTINGS_SOURCE",
                })
                send_telegram_message(chat_id, "📋 <b>نسخ إعدادات من مشروع آخر</b>\nاختر المشروع المصدر — سيتم نسخ إعدادات GitHub والموديل وبرومبت الاستئناف لمشروع جديد باسم تسلسلي تلقائي.", reply_markup=build_copy_settings_source_keyboard(chat_id))
        elif data == "cmd:resume_copy_back":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_COPY_SETTINGS_SOURCE":
                send_telegram_message(chat_id, "ℹ️ لا توجد عملية نسخ إعدادات جارية.")
            else:
                target_url = str(state.get("url") or "")
                pid_value = str(state.get("pid") or "")
                present_external_resume_decision(chat_id, target_url=target_url, target_pid=pid_value)
        elif data.startswith("cpysrc:"):
            source_key = data[len("cpysrc:"):]
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_COPY_SETTINGS_SOURCE":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً شاشة نسخ الإعدادات من زر «📋 نسخ إعدادات من مشروع آخر».")
            else:
                target_url = str(state.get("url") or "")
                pid_value = str(state.get("pid") or extract_project_id(target_url) or "")
                result = copy_project_settings_to_new_project(source_key, chat_id, target_url=target_url, target_pid=pid_value)
                if not result.get("ok"):
                    send_telegram_message(chat_id, f"⚠️ <b>تعذر نسخ الإعدادات:</b> {html_escape(str(result.get('reason') or 'سبب غير معروف'))}")
                else:
                    set_user_state(chat_id, {
                        "action": "AWAITING_CONT_PROMPT",
                        "url": target_url,
                        "project_key": str(result.get("project_key") or ""),
                        "project_name": str(result.get("project_name") or ""),
                        "project_model": normalize_project_model((result.get("settings") or {}).get("model")),
                        "pid": pid_value,
                    })
                    send_telegram_message(chat_id, format_copied_settings_summary(result))
        elif data == "cmd:bound_proj_github_yes":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_BOUND_PROJECT_GITHUB_MODE":
                send_telegram_message(chat_id, "ℹ️ ابدأ أولاً ربط المشروع الخارجي ثم اختر الموديل قبل إعداد GitHub.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_GITHUB_REPO",
                })
                send_telegram_message(chat_id, "🔗 <b>ربط GitHub للمشروع الخارجي</b>\nأرسل رابط المستودع أو الصيغة <code>owner/repo</code> أولاً.")
        elif data in {"cmd:bound_proj_github_no", "cmd:bound_proj_github_disable"}:
            state = get_user_state(chat_id)
            if state.get("action") not in {"AWAITING_BOUND_PROJECT_GITHUB_MODE", "AWAITING_BOUND_PROJECT_GITHUB_BRANCH_DECISION"}:
                send_telegram_message(chat_id, "ℹ️ ابدأ أولاً ربط المشروع الخارجي ثم اختر الموديل قبل تحديد وضع GitHub.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION",
                    "pending_github_enabled": False,
                    "pending_github_repository": "",
                    "pending_github_token": "",
                    "pending_github_branch": "",
                    "pending_github_branch_mode": "disabled",
                    "pending_github_default_branch": "",
                    "pending_github_branches": [],
                    "pending_github_repo_check_status": "disabled",
                })
                send_telegram_message(chat_id, "✅ <b>سيتم ربط المشروع الخارجي بدون GitHub حالياً.</b>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_bound_project_resume_prompt_keyboard())
        elif data.startswith("cmd:bound_proj_branch_pick:"):
            chosen_branch = data[len("cmd:bound_proj_branch_pick:"):]
            state = get_user_state(chat_id)
            detected_default = str(state.get("pending_github_default_branch") or "")
            branches = list(state.get("pending_github_branches") or [])
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION",
                "pending_github_enabled": True,
                "pending_github_branch": chosen_branch,
                "pending_github_branch_mode": "manual",
                "pending_github_default_branch": detected_default,
                "pending_github_branches": branches,
                "pending_github_repo_check_status": "checked",
            })
            send_telegram_message(chat_id, f"✅ <b>تم اختيار الفرع بنجاح:</b> <code>{html_escape(chosen_branch)}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_bound_project_resume_prompt_keyboard())
        elif data == "cmd:bound_proj_branch_default":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_BOUND_PROJECT_GITHUB_BRANCH_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً خطوة فحص GitHub للمشروع الخارجي ثم اختر طريقة الفرع.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION",
                    "pending_github_enabled": True,
                    "pending_github_branch": "",
                    "pending_github_branch_mode": "auto_default",
                    "pending_github_repo_check_status": "checked",
                })
                send_telegram_message(chat_id, "✅ <b>تم حفظ إعداد GitHub المبدئي للمشروع الخارجي.</b>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_bound_project_resume_prompt_keyboard())
        elif data == "cmd:bound_proj_branch_manual":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_BOUND_PROJECT_GITHUB_BRANCH_DECISION":
                send_telegram_message(chat_id, "ℹ️ افتح أولاً خطوة فحص GitHub للمشروع الخارجي ثم اختر branch يدوي إذا أردت.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_GITHUB_BRANCH",
                })
                send_telegram_message(chat_id, "✍️ <b>أدخل اسم الـbranch المطلوب لهذا المشروع الخارجي</b>\nمثال: <code>main</code> أو <code>develop</code>.")
        elif data == "cmd:bound_proj_resume_default":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION":
                send_telegram_message(chat_id, "ℹ️ أكمل أولاً ربط المشروع الخارجي حتى تصل لخطوة برومبت الاستئناف.")
            else:
                settings, next_state = finalize_bound_external_project_from_state(state, chat_id=chat_id, resume_prompt=DEFAULT_PROJECT_RESUME_PROMPT)
                set_user_state(chat_id, next_state)
                send_telegram_message(chat_id, f"✅ <b>تم ربط المشروع الخارجي كمشروع محفوظ.</b>\n<b>الاسم:</b> {html_escape(str(state.get('project_name') or ''))}\n<b>المفتاح:</b> <code>{html_escape(str(state.get('project_key') or ''))}</code>\n<b>الموديل:</b> <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n<b>برومبت الاستئناف:</b> <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>\nأرسل الآن التعديل أو البرومبت المطلوب على هذا المشروع الخارجي.")
        elif data == "cmd:bound_proj_resume_custom":
            state = get_user_state(chat_id)
            if state.get("action") != "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION":
                send_telegram_message(chat_id, "ℹ️ أكمل أولاً ربط المشروع الخارجي حتى تصل لخطوة برومبت الاستئناف.")
            else:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_RESUME_PROMPT",
                })
                send_telegram_message(chat_id, "✍️ <b>أدخل برومبت الاستئناف الخاص بهذا المشروع الخارجي</b>\nالقيمة الافتراضية هي <code>تابع</code> ويمكن تعديلها لاحقاً من إعدادات المشروع.")
        elif data == "cmd:cont_proj":
            set_user_state(chat_id, {"action": "AWAITING_CONT_URL"})
            send_telegram_message(chat_id, "🔄 <b>استئناف مشروع حالي:</b>\nأرسل رابط المشروع (URL) أو الـ Project ID لاستئناف الشغل عليه!")
        elif data.startswith("proj:"):
            project_key = data.split("proj:", 1)[1]
            if not start_project_resume_from_key(chat_id, project_key):
                send_telegram_message(chat_id, "⚠️ تعذر فتح هذا المشروع من الـRegistry الحالية.")
        elif data.startswith("cont:"):
            pid = data.split("cont:")[1]
            ctx = resolve_resume_context(pid)
            if ctx["project_key"]:
                present_resume_summary(chat_id, project_key=ctx["project_key"], target_url=ctx["target_url"], target_pid=ctx["pid"])
            else:
                present_external_resume_decision(chat_id, target_url=ctx["target_url"], target_pid=ctx["pid"])
        elif data.startswith("tree:") or data == "cmd:list_tree":
            pid = data.split("tree:")[1] if "tree:" in data else None
            if not pid:
                current = get_latest_project_for_chat(chat_id)
                current_pid = str(current.get("latest_genspark_pid") or current.get("root_genspark_pid") or "") if current else ""
                pid = current_pid
            if not pid:
                send_telegram_message(chat_id, "🌳 أرسل رابط المشروع أولاً أو اختر المشروع الحالي لعرض شجرة التفريعات الخاصة به.")
            else:
                branches = get_project_branches(pid)
                if not branches:
                    send_telegram_message(chat_id, f"ℹ️ لا توجد تفريعات سابقة للمشروع <code>{html_escape(pid[:8])}...</code>")
                else:
                    b_buttons = []
                    for b in branches[:6]:
                        b_pid = b.get("project_id")
                        b_title = html_escape(b.get("title", "فرع"))[:20]
                        b_buttons.append([{"text": f"📍 {b_title} ({str(b_pid)[:6]}...)", "callback_data": f"cont:{b_pid}"}])
                    send_telegram_message(chat_id, f"🌳 <b>نقاط الاستئناف المتاحة للمشروع <code>{html_escape(pid[:8])}...</code>:</b>", reply_markup=make_inline_keyboard(b_buttons))
        elif data == "cmd:account_pwd_lookup":
            # 🔐 [P32] فتح الشاشة الهجينة: تعيين الحالة التفاعلية (يفتح المسار اليدوي)
            # وعرض الصفحة الأولى من قائمة الحسابات في نفس اللحظة.
            set_user_state(chat_id, {"action": AWAITING_ACCOUNT_PASSWORD_LOOKUP, "page": 1})
            send_telegram_message(
                chat_id,
                render_account_lookup_text(page=1),
                reply_markup=build_account_lookup_keyboard(page=1),
            )
        elif data.startswith("acc_page:"):
            page_token = data.split("acc_page:", 1)[1]
            if page_token == "noop":
                # 🔐 [P32] زر العداد «📄 N / X» — عرض فقط، لا يفعل شيئاً عمداً
                pass
            else:
                # 🔐 [P32] تقليب الصفحات In-Place (نفس نمط P27) — صفر Spam في المحادثة.
                # الحالة التفاعلية تبقى قائمة ليظل المسار اليدوي متاحاً أثناء التصفح.
                safe_page, _total_pages, _start = compute_accounts_page_bounds(
                    len(list_lookup_accounts()), page_token
                )
                set_user_state(chat_id, {"action": AWAITING_ACCOUNT_PASSWORD_LOOKUP, "page": safe_page})
                page_text = render_account_lookup_text(page=safe_page)
                page_keyboard = build_account_lookup_keyboard(page=safe_page)
                lookup_msg_id = msg_info.get("message_id")
                if lookup_msg_id:
                    edit_telegram_message_text(chat_id, lookup_msg_id, page_text, reply_markup=page_keyboard)
                else:
                    send_telegram_message(chat_id, page_text, reply_markup=page_keyboard)
        elif data.startswith("acc_view:"):
            # 🔐 [P32] ضغط زر إيميل من القائمة: الفهرس المطلق داخل القائمة المرتبة.
            # أي فهرس تالف/خارج المدى يُرفض بهدوء بلا Crash.
            index_token = data.split("acc_view:", 1)[1]
            accounts = list_lookup_accounts()
            try:
                acc_index = int(index_token)
            except (TypeError, ValueError):
                acc_index = -1
            if 0 <= acc_index < len(accounts):
                set_user_state(chat_id, {})
                send_telegram_message(
                    chat_id,
                    render_account_password_card(accounts[acc_index]),
                    reply_markup=build_account_password_card_keyboard(),
                )
            else:
                send_telegram_message(
                    chat_id,
                    "⚠️ <b>تعذر عرض هذا الحساب</b> — تغيّرت قائمة الحسابات. افتح الشاشة من جديد.",
                    reply_markup=build_account_lookup_retry_keyboard(),
                )
        elif data == "acc_cancel":
            # 🔐 [P32] إلغاء حتمي: تصفير الحالة التفاعلية والعودة للوحة التحكم
            set_user_state(chat_id, {})
            send_telegram_message(
                chat_id,
                "↩️ <b>تم إلغاء استخراج الباسورد.</b>\n" + render_dashboard_text(chat_id),
                reply_markup=get_main_keyboard(chat_id),
            )
        return

    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()
        # [P17] مسار message: نحكم بالجروب أو بهوية المُرسِل نفسه (msg.from)
        if not is_chat_allowed(chat_id, (msg.get("from") or {}).get("id")):
            return

        # 📄 [P28] Document Ingestion: ملف .txt/.md يتحول لمحتوى نصي يغذي
        # نفس مسار text أدناه (كل حالات الـ Wizard + المسار الافتراضي) بلا تكرار.
        # رسائل الـ Document لا تحمل text أصلاً — الشرط يضمن Zero Regression للنصوص العادية.
        document = msg.get("document") or {}
        if document and not text:
            doc_name = str(document.get("file_name") or "")
            doc_ext = pathlib.Path(doc_name).suffix.lower()
            if doc_ext not in ALLOWED_DOCUMENT_EXTENSIONS:
                send_telegram_message(
                    chat_id,
                    "⚠️ <b>نوع الملف غير مدعوم.</b>\n"
                    f"المدعوم حالياً: <code>.txt</code> و <code>.md</code> فقط — "
                    f"استلمت: <code>{html_escape(doc_name or 'ملف بلا اسم')}</code>"
                )
                return
            doc_size = int(document.get("file_size") or 0)
            if doc_size > MAX_DOCUMENT_SIZE_BYTES:
                send_telegram_message(
                    chat_id,
                    "⚠️ <b>الملف أكبر من الحد المسموح (5 MB).</b>\n"
                    f"حجم الملف: <code>{doc_size / (1024 * 1024):.1f} MB</code> — "
                    "قسّمه أو اختصر محتواه ثم أعد الإرسال."
                )
                return
            doc_content = download_telegram_document_text(document.get("file_id") or "")
            if doc_content is None or not doc_content.strip():
                send_telegram_message(
                    chat_id,
                    "❌ <b>تعذر قراءة محتوى الملف.</b>\n"
                    "تأكد أنه ملف نصي سليم غير فارغ ثم أعد المحاولة."
                )
                return
            caption = str(msg.get("caption") or "").strip()
            text = f"{caption}\n\n{doc_content}".strip() if caption else doc_content.strip()
            log_event("info", f"📄 [P28] تم استيعاب ملف مهمة [{doc_name}] ({doc_size} بايت) من Chat {chat_id}")

        if text in ["/start", "/help"]:
            send_telegram_message(chat_id, render_dashboard_text(chat_id), reply_markup=get_main_keyboard(chat_id))
            return

        state = get_user_state(chat_id)
        action = state.get("action")

        # 🔐 [P32] المسار اليدوي لاستخراج الباسورد — أول فحص في سلسلة الحالات:
        # الإيميل نص عادي، ولو تُرك للمسار الافتراضي لأسفل لكان أُرسل كبرومبت مهمة.
        # كتلة مستقلة تماماً ← صفر تأثير على أي حالة Wizard أخرى.
        if action == AWAITING_ACCOUNT_PASSWORD_LOOKUP:
            requested_email = str(text or "").strip().lower()
            matched = find_account_by_email(requested_email)
            if matched:
                set_user_state(chat_id, {})
                send_telegram_message(
                    chat_id,
                    render_account_password_card(matched),
                    reply_markup=build_account_password_card_keyboard(),
                )
            else:
                # الحالة تبقى قائمة: المالك يعيد الكتابة فوراً بلا إعادة فتح الشاشة
                send_telegram_message(
                    chat_id,
                    "❌ <b>الحساب غير مسجل في قاعدة الحسابات.</b>\n"
                    f"البريد المطلوب: <code>{html_escape(requested_email or 'بلا إيميل')}</code>\n"
                    "تأكد من كتابته بشكل صحيح وأعد الإرسال، أو ارجع للوحة التحكم.",
                    reply_markup=build_account_lookup_retry_keyboard(),
                )
            return

        if action == AWAITING_PROJECT_CONFIRMATION:
            # 🛡️ [P42] نص جديد أثناء بطاقة التأكيد ⟔ إبطال ضمني للبطاقة القديمة:
            # Edge 6: رابط/معرّف مشروع يفوز — إغلاق الحالة وتوجيه شرعي عبر منطق P41 نفسه.
            locator = parse_project_locator(text)
            if locator["kind"] == "malformed":
                set_user_state(chat_id, {})
                log_event("info", f"🛡️ [P42] Intent Guard EXPIRED — رابط مشوّه أبطل بطاقة التأكيد (chat={chat_id})")
                send_telegram_message(chat_id, MALFORMED_PROJECT_LINK_MESSAGE)
                return
            if locator["kind"] == "pid":
                set_user_state(chat_id, {})
                log_event("info", f"🛡️ [P42] Intent Guard EXPIRED — رابط مشروع ({locator['pid']}) أبطل بطاقة التأكيد ووُجّه لمساره الشرعي (chat={chat_id})")
                ctx = resolve_resume_context(text)
                if ctx["project_key"]:
                    present_resume_summary(chat_id, project_key=ctx["project_key"], target_url=ctx["target_url"], target_pid=ctx["pid"])
                else:
                    present_external_resume_decision(chat_id, target_url=ctx["target_url"], target_pid=ctx["pid"])
                return
            # نص عادي ⟔ إعادة تشغيل الحارس بنص جديد وnonce جديد (البطاقة القديمة أُبطلت تلقائياً)
            handle_idle_intent_guard(chat_id, text)
            return

        if action == "AWAITING_NEW_PROJECT_NAME":
            project_name = re.sub(r"\s+", " ", text).strip()[:60] or "مشروع بدون اسم"
            project_key = f"prj_{uuid.uuid4().hex[:16]}"
            # 🛡️ [P42] التعديل الواعي الوحيد: حمل pending_prompt/consumed_confirm_nonce
            # إن وُجدا (مسار بطاقة التأكيد) — بقية انتقالات الـ Wizard تستخدم {**state} أصلاً.
            # مسار cmd:new_proj المباشر بلا pending_prompt ⟔ dict مطابق للقديم حرفياً.
            carried = {k: state[k] for k in ("pending_prompt", "consumed_confirm_nonce") if state.get(k)}
            set_user_state(chat_id, {
                **carried,
                "action": "AWAITING_NEW_PROJECT_MODEL",
                "project_key": project_key,
                "project_name": project_name,
            })
            send_telegram_message(chat_id, f"✅ <b>اسم المشروع:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\nاختر الآن الموديل المطلوب لهذا المشروع.", reply_markup=build_new_project_model_keyboard())
            return

        if action == "AWAITING_NEW_PROJECT_GITHUB_REPO":
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            project_model = normalize_project_model(state.get("project_model"))
            repository = parse_github_repository_ref(text)
            if not repository:
                send_telegram_message(chat_id, "⚠️ صيغة المستودع غير واضحة. أرسل رابط GitHub كامل أو الصيغة <code>owner/repo</code>.")
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_NEW_PROJECT_GITHUB_TOKEN",
                "project_key": project_key,
                "project_name": project_name,
                "project_model": project_model,
                "pending_github_repository": repository,
            })
            send_telegram_message(chat_id, f"✅ <b>المستودع:</b> <code>{html_escape(repository)}</code>\nأرسل الآن <b>GitHub token</b> الخاص بهذا المشروع حتى أتمكن من فحص المستودع والفروع، خصوصاً إذا كان المستودع خاصاً.")
            return

        if action == "AWAITING_NEW_PROJECT_GITHUB_TOKEN":
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            project_model = normalize_project_model(state.get("project_model"))
            repository = str(state.get("pending_github_repository") or "")
            token_value = str(text or "").strip()
            if not token_value:
                send_telegram_message(chat_id, "⚠️ أدخل GitHub token صالحاً لهذا المشروع أو استخدم زر المتابعة بدون GitHub.")
                return
            inspection = inspect_github_repository(repository, token=token_value)
            if inspection.get("ok"):
                raw_branches = inspection.get("branches") or []
                default_branch = inspection.get("default_branch") or (raw_branches[0] if raw_branches else "")
                set_user_state(chat_id, {
                    "action": "AWAITING_NEW_PROJECT_GITHUB_BRANCH_DECISION",
                    "project_key": project_key,
                    "project_name": project_name,
                    "project_model": project_model,
                    "pending_github_enabled": True,
                    "pending_github_repository": repository,
                    "pending_github_token": token_value,
                    "pending_github_default_branch": default_branch,
                    "pending_github_branches": raw_branches,
                    "pending_github_repo_check_status": "checked",
                })
                summary_msg = format_github_repo_inspection_summary(repository, default_branch, raw_branches)
                send_telegram_message(chat_id, summary_msg, reply_markup=build_new_project_branch_choice_keyboard(branches=raw_branches, default_branch=default_branch))
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_NEW_PROJECT_GITHUB_TOKEN",
                "pending_github_repository": repository,
                "pending_github_token": "",
            })
            send_telegram_message(chat_id, f"⚠️ <b>تعذر فحص المستودع الآن:</b> {html_escape(inspection.get('reason') or 'سبب غير معروف')}\nأعد إدخال token صالح لهذا المشروع، أو استخدم زر <b>المتابعة بدون GitHub</b> إذا أردت التخطي.")
            return

        if action == "AWAITING_NEW_PROJECT_GITHUB_BRANCH":
            repository = str(state.get("pending_github_repository") or "")
            branch = re.sub(r"\s+", "", text).strip()
            if not branch:
                send_telegram_message(chat_id, "⚠️ اكتب اسم branch صالح مثل <code>main</code> أو <code>develop</code>.")
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION",
                "pending_github_enabled": True,
                "pending_github_branch": branch,
                "pending_github_branch_mode": "manual",
                "pending_github_repo_check_status": "manual-branch",
            })
            send_telegram_message(chat_id, f"✅ <b>تم حفظ إعداد GitHub اليدوي.</b>\n<b>المستودع:</b> <code>{html_escape(repository)}</code>\n<b>الفرع:</b> <code>{html_escape(branch)}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_new_project_resume_prompt_keyboard())
            return

        if action == "AWAITING_NEW_PROJECT_RESUME_PROMPT":
            settings, next_state = finalize_new_project_from_state(state, chat_id=chat_id, resume_prompt=text)
            # 🛡️ [P42] Smart Prompt Forwarding — لا pending_prompt ⟔ next_state كما هي (السلوك القديم حرفياً)
            next_state = forward_pending_prompt_after_wizard(chat_id, state, next_state, settings)
            set_user_state(chat_id, next_state)
            send_telegram_message(chat_id, f"✅ <b>تم حفظ إعدادات المشروع.</b>\n<b>الاسم:</b> {html_escape(str(state.get('project_name') or ''))}\n<b>المفتاح:</b> <code>{html_escape(str(state.get('project_key') or ''))}</code>\n<b>الموديل:</b> <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n<b>برومبت الاستئناف:</b> <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>\nأرسل الآن أول برومبت لبدء المشروع.")
            return

        if action == "AWAITING_PROJECT_SETTINGS_RESUME_PROMPT":
            project_key = str(state.get("project_key") or "")
            if not project_key:
                send_telegram_message(chat_id, "⚠️ لا يوجد مشروع صالح لتعديل برومبت الاستئناف حالياً.")
                return
            ProjectRegistry(project_key).set_project_resume_prompt(text)
            set_user_state(chat_id, {})
            send_project_settings_panel(chat_id, project_key, prefix="✅ <b>تم تحديث برومبت الاستئناف للمشروع.</b>")
            return

        if action == "AWAITING_PROJECT_SETTINGS_GITHUB_REPO":
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            repository = parse_github_repository_ref(text)
            if not repository:
                send_telegram_message(chat_id, "⚠️ صيغة المستودع غير واضحة. أرسل رابط GitHub كامل أو الصيغة <code>owner/repo</code>.")
                return
            registry = ProjectRegistry(project_key)
            current_github = registry.get_project_settings().get("github", {})
            project_token = registry.get_project_github_token(allow_env_fallback=False)
            if not project_token:
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_PROJECT_SETTINGS_GITHUB_TOKEN",
                    "settings_edit_scope": "repo_update",
                    "pending_github_repository": repository,
                })
                send_telegram_message(chat_id, f"✅ <b>المستودع الجديد:</b> <code>{html_escape(repository)}</code>\nأرسل الآن <b>GitHub token</b> الخاص بهذا المشروع حتى أتمكن من فحص الـdefault branch والفروع المتاحة.")
                return
            inspection = inspect_github_repository(repository, token=project_token)
            if inspection.get("ok"):
                raw_branches = inspection.get("branches") or []
                default_branch = inspection.get("default_branch") or (raw_branches[0] if raw_branches else "")
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH_DECISION",
                    "project_key": project_key,
                    "project_name": project_name,
                    "settings_edit_scope": "repo_update",
                    "pending_github_enabled": bool(state.get("pending_github_enabled", current_github.get("enabled"))),
                    "pending_github_repository": repository,
                    "pending_github_default_branch": default_branch,
                    "pending_github_branches": raw_branches,
                    "pending_github_repo_check_status": "checked",
                })
                summary_msg = format_github_repo_inspection_summary(repository, default_branch, raw_branches)
                send_telegram_message(chat_id, summary_msg, reply_markup=build_existing_project_branch_choice_keyboard(project_key, branches=raw_branches, default_branch=default_branch))
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_PROJECT_SETTINGS_GITHUB_TOKEN",
                "settings_edit_scope": "repo_update",
                "pending_github_repository": repository,
            })
            send_telegram_message(chat_id, f"⚠️ <b>تعذر فحص المستودع بالتوكن المحفوظ حالياً:</b> {html_escape(inspection.get('reason') or 'سبب غير معروف')}\nأرسل token محدثاً لهذا المشروع، أو بعد ذلك سنسمح لك بإدخال branch يدوي إذا لزم الأمر.")
            return

        if action == "AWAITING_PROJECT_SETTINGS_GITHUB_TOKEN":
            project_key = str(state.get("project_key") or "")
            project_name = str(state.get("project_name") or "")
            registry = ProjectRegistry(project_key)
            current_github = registry.get_project_settings().get("github", {})
            repository = parse_github_repository_ref(state.get("pending_github_repository") or current_github.get("repository") or "")
            token_value = str(text or "").strip()
            scope = str(state.get("settings_edit_scope") or "token_update")
            if not token_value:
                send_telegram_message(chat_id, "⚠️ أدخل GitHub token صالحاً لهذا المشروع.")
                return
            if scope == "token_update" and not repository:
                update_existing_project_github_settings(project_key, token=token_value, repo_check_status="token-updated")
                set_user_state(chat_id, {})
                send_project_settings_panel(chat_id, project_key, prefix="✅ <b>تم تحديث GitHub token للمشروع.</b>")
                return
            inspection = inspect_github_repository(repository, token=token_value) if repository else {"ok": False, "reason": "لا يوجد repo محفوظ بعد."}
            if scope == "token_update":
                if repository and inspection.get("ok"):
                    default_branch = inspection.get("default_branch") or ((inspection.get("branches") or [""])[0])
                    update_existing_project_github_settings(
                        project_key,
                        enabled=bool(state.get("pending_github_enabled", current_github.get("enabled"))),
                        repository=repository,
                        detected_default_branch=default_branch,
                        available_branches=inspection.get("branches") or [],
                        repo_check_status="checked",
                        token=token_value,
                    )
                    set_user_state(chat_id, {})
                    send_project_settings_panel(chat_id, project_key, prefix="✅ <b>تم تحديث GitHub token للمشروع وفحص المستودع الحالي بنجاح.</b>")
                else:
                    update_existing_project_github_settings(project_key, token=token_value, repo_check_status="token-updated")
                    set_user_state(chat_id, {})
                    warning = ""
                    if repository and not inspection.get("ok"):
                        warning = f"\n⚠️ <b>ملاحظة:</b> تعذر فحص المستودع الحالي الآن: {html_escape(inspection.get('reason') or 'سبب غير معروف')}"
                    send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم تحديث GitHub token للمشروع.</b>{warning}")
                return
            if repository and inspection.get("ok"):
                raw_branches = inspection.get("branches") or []
                default_branch = inspection.get("default_branch") or (raw_branches[0] if raw_branches else "")
                set_user_state(chat_id, {
                    "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH_DECISION",
                    "project_key": project_key,
                    "project_name": project_name,
                    "settings_edit_scope": scope,
                    "pending_github_enabled": bool(state.get("pending_github_enabled", current_github.get("enabled"))),
                    "pending_github_repository": repository,
                    "pending_github_token": token_value,
                    "pending_github_default_branch": default_branch,
                    "pending_github_branches": raw_branches,
                    "pending_github_repo_check_status": "checked",
                })
                summary_msg = format_github_repo_inspection_summary(repository, default_branch, raw_branches)
                send_telegram_message(chat_id, summary_msg, reply_markup=build_existing_project_branch_choice_keyboard(project_key, branches=raw_branches, default_branch=default_branch))
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH",
                "settings_edit_scope": scope,
                "pending_github_repository": repository,
                "pending_github_token": token_value,
                "pending_github_repo_check_status": "manual-branch",
            })
            send_telegram_message(chat_id, f"⚠️ <b>تعذر فحص المستودع الآن:</b> {html_escape(inspection.get('reason') or 'سبب غير معروف')}\nاكتب اسم branch يدويًا لهذا المشروع مثل <code>main</code> أو <code>develop</code>.")
            return

        if action == "AWAITING_PROJECT_SETTINGS_GITHUB_BRANCH":
            project_key = str(state.get("project_key") or "")
            branch = re.sub(r"\s+", "", text).strip()
            if not branch:
                send_telegram_message(chat_id, "⚠️ اكتب اسم branch صالح مثل <code>main</code> أو <code>develop</code>.")
                return
            finalize_existing_project_github_from_state(state, branch=branch, branch_mode="manual", repo_check_status="manual-branch")
            set_user_state(chat_id, {})
            send_project_settings_panel(chat_id, project_key, prefix=f"✅ <b>تم حفظ branch المشروع يدوياً.</b>\n<b>الفرع:</b> <code>{html_escape(branch)}</code>")
            return

        if action == "AWAITING_BOUND_PROJECT_NAME":
            project_name = re.sub(r"\s+", " ", text).strip()[:60] or "مشروع خارجي بدون اسم"
            project_key = f"prj_{uuid.uuid4().hex[:16]}"
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_BOUND_PROJECT_MODEL",
                "project_key": project_key,
                "project_name": project_name,
            })
            send_telegram_message(chat_id, f"✅ <b>اسم المشروع الخارجي:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\nاختر الآن الموديل المطلوب لهذا المشروع.", reply_markup=build_new_project_model_keyboard())
            return

        if action == "AWAITING_BOUND_PROJECT_GITHUB_REPO":
            repository = parse_github_repository_ref(text)
            if not repository:
                send_telegram_message(chat_id, "⚠️ صيغة المستودع غير واضحة. أرسل رابط GitHub كامل أو الصيغة <code>owner/repo</code>.")
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_BOUND_PROJECT_GITHUB_TOKEN",
                "pending_github_repository": repository,
            })
            send_telegram_message(chat_id, f"✅ <b>المستودع:</b> <code>{html_escape(repository)}</code>\nأرسل الآن <b>GitHub token</b> الخاص بهذا المشروع الخارجي حتى أتمكن من فحص المستودع والفروع.")
            return

        if action == "AWAITING_BOUND_PROJECT_GITHUB_TOKEN":
            repository = str(state.get("pending_github_repository") or "")
            token_value = str(text or "").strip()
            if not token_value:
                send_telegram_message(chat_id, "⚠️ أدخل GitHub token صالحاً لهذا المشروع الخارجي.")
                return
            inspection = inspect_github_repository(repository, token=token_value)
            if inspection.get("ok"):
                raw_branches = inspection.get("branches") or []
                default_branch = inspection.get("default_branch") or (raw_branches[0] if raw_branches else "")
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_BOUND_PROJECT_GITHUB_BRANCH_DECISION",
                    "pending_github_enabled": True,
                    "pending_github_repository": repository,
                    "pending_github_token": token_value,
                    "pending_github_default_branch": default_branch,
                    "pending_github_branches": raw_branches,
                    "pending_github_repo_check_status": "checked",
                })
                summary_msg = format_github_repo_inspection_summary(repository, default_branch, raw_branches)
                send_telegram_message(chat_id, summary_msg, reply_markup=build_bound_project_branch_choice_keyboard(branches=raw_branches, default_branch=default_branch))
                return
            set_user_state(chat_id, {
                **state,
                "pending_github_repository": repository,
                "pending_github_token": "",
            })
            send_telegram_message(chat_id, f"⚠️ <b>تعذر فحص المستودع الآن:</b> {html_escape(inspection.get('reason') or 'سبب غير معروف')}\nأعد إدخال token صالح لهذا المشروع، أو استخدم المتابعة بدون GitHub إذا أردت التخطي.")
            return

        if action == "AWAITING_BOUND_PROJECT_GITHUB_BRANCH":
            branch = re.sub(r"\s+", "", text).strip()
            if not branch:
                send_telegram_message(chat_id, "⚠️ اكتب اسم branch صالح مثل <code>main</code> أو <code>develop</code>.")
                return
            set_user_state(chat_id, {
                **state,
                "action": "AWAITING_BOUND_PROJECT_RESUME_PROMPT_DECISION",
                "pending_github_enabled": True,
                "pending_github_branch": branch,
                "pending_github_branch_mode": "manual",
                "pending_github_repo_check_status": "manual-branch",
            })
            send_telegram_message(chat_id, f"✅ <b>تم حفظ إعداد GitHub اليدوي للمشروع الخارجي.</b>\n<b>الفرع:</b> <code>{html_escape(branch)}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_bound_project_resume_prompt_keyboard())
            return

        if action == "AWAITING_BOUND_PROJECT_RESUME_PROMPT":
            settings, next_state = finalize_bound_external_project_from_state(state, chat_id=chat_id, resume_prompt=text)
            set_user_state(chat_id, next_state)
            send_telegram_message(chat_id, f"✅ <b>تم ربط المشروع الخارجي كمشروع محفوظ.</b>\n<b>الاسم:</b> {html_escape(str(state.get('project_name') or ''))}\n<b>المفتاح:</b> <code>{html_escape(str(state.get('project_key') or ''))}</code>\n<b>الموديل:</b> <code>{html_escape(settings.get('model') or DEFAULT_PROJECT_MODEL)}</code>\n<b>برومبت الاستئناف:</b> <code>{html_escape(settings.get('continuation', {}).get('prompt') or DEFAULT_PROJECT_RESUME_PROMPT)}</code>\nأرسل الآن التعديل أو البرومبت المطلوب على هذا المشروع الخارجي.")
            return

        if action == "AWAITING_CONT_URL":
            if parse_project_locator(text)["kind"] == "malformed":
                send_telegram_message(chat_id, MALFORMED_PROJECT_LINK_MESSAGE)
                return
            ctx = resolve_resume_context(text)
            if ctx["project_key"]:
                present_resume_summary(chat_id, project_key=ctx["project_key"], target_url=ctx["target_url"], target_pid=ctx["pid"])
                return
            present_external_resume_decision(chat_id, target_url=ctx["target_url"], target_pid=ctx["pid"])
            return

        if action == "AWAITING_NEW_PROMPT":
            if handle_prompt_context_collision(chat_id, state, text, action):
                return
            state_project_key = state.get("project_key")
            state_project_name = state.get("project_name")
            state_project_model = normalize_project_model(state.get("project_model") or get_project_selected_model(state_project_key))
            set_user_state(chat_id, {})
            try:
                EXECUTOR.submit(process_user_task_async, chat_id, None, text, state_project_model, state_project_key, state_project_name)
            except Exception as e:
                log_event("error", f"فشل جدولة المهمة: {e}")
            return

        if action == "AWAITING_CONT_PROMPT":
            if handle_prompt_context_collision(chat_id, state, text, action):
                return
            target_url = state.get("url")
            state_project_key = state.get("project_key")
            state_project_name = state.get("project_name")
            state_project_model = normalize_project_model(state.get("project_model") or get_project_selected_model(state_project_key))
            set_user_state(chat_id, {})
            try:
                EXECUTOR.submit(process_user_task_async, chat_id, target_url, text, state_project_model, state_project_key, state_project_name)
            except Exception as e:
                log_event("error", f"فشل جدولة المهمة: {e}")
            return

        if "genspark.ai" in text or re.search(r"[a-f0-9\-]{36}", text):
            if parse_project_locator(text)["kind"] == "malformed":
                send_telegram_message(chat_id, MALFORMED_PROJECT_LINK_MESSAGE)
                return
            ctx = resolve_resume_context(text)
            if ctx["project_key"]:
                present_resume_summary(chat_id, project_key=ctx["project_key"], target_url=ctx["target_url"], target_pid=ctx["pid"])
                return
            present_external_resume_decision(chat_id, target_url=ctx["target_url"], target_pid=ctx["pid"])
            return

        # 🛡️ [P42] الـ Fallback القديم (نص عابر ⟔ مشروع تلقائي) حُذف من الوجود —
        # أي نص حر متبقٍّ في IDLE يمر على Intent Guard حصرياً (Confirmation before ANY Mutation)
        handle_idle_intent_guard(chat_id, text)


def load_telegram_offset() -> int:
    try:
        if TELEGRAM_OFFSET_FILE.exists():
            return int(TELEGRAM_OFFSET_FILE.read_text(encoding="utf-8").strip() or "0")
    except Exception:
        pass
    return 0


def save_telegram_offset(offset: int):
    try:
        TELEGRAM_OFFSET_FILE.write_text(str(offset), encoding="utf-8")
    except Exception:
        pass


def run_telegram_polling():
    print(Fore.GREEN + Style.BRIGHT + "╔══════════════════════════════════════════════════════════════╗")
    print(Fore.GREEN + Style.BRIGHT + f"║  🤖 تشغيل بوت تليجرام التفاعلي ({pathlib.Path(__file__).name})   ║")
    print(Fore.GREEN + Style.BRIGHT + "╚══════════════════════════════════════════════════════════════╝")
    print(Fore.YELLOW + f"📌 RUNNING FILE PATH: {pathlib.Path(__file__).resolve()}")

    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "⚠️ توكن البوت غير مضبوط!")
        log_event("error", "   اضبط متغير البيئة TELEGRAM_BOT_TOKEN أو أنشئ ملف telegram_bot_token.txt بجوار السكربت (خارج git).")
        return

    offset = load_telegram_offset()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    for cid in ALLOWED_CHAT_IDS:
        send_telegram_message(cid, f"🟢 <b>بوت Genspark Telegram Bridge ({pathlib.Path(__file__).name}) شغال ومستعد لاستقبال الأوامر!</b>", reply_markup=get_main_keyboard(cid))
    # [P41] عميل getUpdates = requests النقية حصرياً (Clean Shutdown):
    # curl_cffi ينفّذ I/O داخل امتداد C — Ctrl+C أثناء long-poll معلقة يظهر
    # كخطأ CFFI/curl:(23) (Exception عادي) فيُبتلع وتستمر الحلقة بالدوران.
    # requests النقية تسمح بوصول KeyboardInterrupt كـ BaseException حقيقي.
    # ⛔ كل مسارات Genspark الأخرى تبقى على curl_cffi بلا أي تغيير.
    import requests as polling_requests
    sess = polling_requests.Session()

    consecutive_errors = 0
    try:
        while True:
            try:
                r = sess.get(url, params={"offset": offset, "timeout": 20}, timeout=30)
                if r.status_code == 200:
                    consecutive_errors = 0
                    data = r.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        save_telegram_offset(offset)
                        try:
                            EXECUTOR.submit(handle_telegram_update, update)
                        except Exception as e:
                            log_event("error", f"فشل جدولة معالجة التحديث: {e}")
                else:
                    consecutive_errors += 1
                    log_event("warning", f"getUpdates HTTP {r.status_code}")
            except (KeyboardInterrupt, SystemExit):
                # [P41] ممنوع ابتلاع طلب الإيقاف في معالج أخطاء الحلقة — يصعد للمعالج الخارجي
                raise
            except Exception as e:
                consecutive_errors += 1
                log_event("error", f"خطأ في حلقة Telegram polling: {e}")
            # إصلاح: backoff تدريجي عند تكرار الأخطاء (حتى 15 ثانية) بدل النوم الثابت
            time.sleep(min(3 * consecutive_errors, 15) if consecutive_errors else 1)
    except (KeyboardInterrupt, SystemExit):
        # [P41] الخروج النظيف الفوري: رسالة إغلاق + sys.exit(0) — بلا Traceback
        print(Fore.YELLOW + "⏹️ تم إيقاف البوت يدوياً (Ctrl+C) — إغلاق نظيف")
        try:
            log_event("info", "⏹️ Clean shutdown: KeyboardInterrupt — sys.exit(0)")
        except Exception:
            pass
        sys.exit(0)


def main():
    log_event("success", f"RUNNING FILE VERIFIED: {pathlib.Path(__file__).resolve()}")
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "لم يتم العثور على توكن البوت — شغّل مع متغير البيئة TELEGRAM_BOT_TOKEN أو ملف telegram_bot_token.txt")
        sys.exit(1)
    run_telegram_polling()


if __name__ == "__main__":
    main()
