"""[VERBATIM SLICE] p12_handlers_main
المصدر: 01.33_telegram_gen_bridge.py — الأسطر 5853..6946
المحتوى: get_main_keyboard + handle_telegram_update + offset + polling + main (P17: بوابة is_chat_allowed للمسارين | P19: معالجات cmd:resume_copy_settings + cpysrc: | P25: معالجات cancel_prompt/cancel_exec/cancel_abort | P26: معالجات pdel_prompt/pdel_abort/pdel_exec ككتلة معزولة مبكرة)
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
def get_main_keyboard(chat_id: int | None = None):
    if chat_id is None:
        return build_dashboard_keyboard(next(iter(ALLOWED_CHAT_IDS)))
    return build_dashboard_keyboard(int(chat_id))


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

        if data == "cmd:show_dashboard":
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
                set_user_state(chat_id, {
                    **state,
                    "action": "AWAITING_NEW_PROJECT_RESUME_PROMPT_DECISION",
                    "project_model": project_model,
                    "pending_github_enabled": False,
                    "pending_github_repository": "",
                    "pending_github_token": "",
                    "pending_github_branch": "",
                    "pending_github_branch_mode": "disabled",
                    "pending_github_default_branch": "",
                    "pending_github_branches": [],
                    "pending_github_repo_check_status": "disabled",
                })
                send_telegram_message(chat_id, f"✅ <b>سيتم إعداد المشروع بدون GitHub حالياً.</b>\n<b>الاسم:</b> {html_escape(project_name)}\n<b>المفتاح:</b> <code>{html_escape(project_key)}</code>\n<b>الموديل:</b> <code>{html_escape(project_model)}</code>\nالآن اختر برومبت الاستئناف الافتراضي أو أدخل واحداً مخصصاً.", reply_markup=build_new_project_resume_prompt_keyboard())
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
            if action in renderers:
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
        elif data == "cmd:check_accs":
            acc = get_random_email_from_accounts_genspark()
            if acc:
                send_telegram_message(chat_id, f"📊 <b>فحص الحسابات:</b>\n📧 الحساب المختار: <code>{html_escape(acc.get('email'))}</code>\n💰 الرصيد: <b>{acc.get('balance', 0)}</b>")
            else:
                send_telegram_message(chat_id, "❌ لا توجد حسابات نشطة متاحة حالياً.")
        return

    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()
        # [P17] مسار message: نحكم بالجروب أو بهوية المُرسِل نفسه (msg.from)
        if not is_chat_allowed(chat_id, (msg.get("from") or {}).get("id")):
            return

        if text in ["/start", "/help"]:
            send_telegram_message(chat_id, render_dashboard_text(chat_id), reply_markup=get_main_keyboard(chat_id))
            return

        state = get_user_state(chat_id)
        action = state.get("action")

        if action == "AWAITING_NEW_PROJECT_NAME":
            project_name = re.sub(r"\s+", " ", text).strip()[:60] or "مشروع بدون اسم"
            project_key = f"prj_{uuid.uuid4().hex[:16]}"
            set_user_state(chat_id, {
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
            ctx = resolve_resume_context(text)
            if ctx["project_key"]:
                present_resume_summary(chat_id, project_key=ctx["project_key"], target_url=ctx["target_url"], target_pid=ctx["pid"])
                return
            present_external_resume_decision(chat_id, target_url=ctx["target_url"], target_pid=ctx["pid"])
            return

        if action == "AWAITING_NEW_PROMPT":
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
            ctx = resolve_resume_context(text)
            if ctx["project_key"]:
                present_resume_summary(chat_id, project_key=ctx["project_key"], target_url=ctx["target_url"], target_pid=ctx["pid"])
                return
            present_external_resume_decision(chat_id, target_url=ctx["target_url"], target_pid=ctx["pid"])
            return

        set_user_state(chat_id, {})
        try:
            EXECUTOR.submit(process_user_task_async, chat_id, None, text)
        except Exception as e:
            log_event("error", f"فشل جدولة المهمة: {e}")


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
    try:
        from curl_cffi import requests as cffi
        sess = cffi.Session()
    except Exception:
        import requests
        sess = requests.Session()

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
            except Exception as e:
                consecutive_errors += 1
                log_event("error", f"خطأ في حلقة Telegram polling: {e}")
            # إصلاح: backoff تدريجي عند تكرار الأخطاء (حتى 15 ثانية) بدل النوم الثابت
            time.sleep(min(3 * consecutive_errors, 15) if consecutive_errors else 1)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "⏹️ تم إيقاف البوت يدوياً (Ctrl+C)")


def main():
    log_event("success", f"RUNNING FILE VERIFIED: {pathlib.Path(__file__).resolve()}")
    if not TELEGRAM_BOT_TOKEN:
        log_event("error", "لم يتم العثور على توكن البوت — شغّل مع متغير البيئة TELEGRAM_BOT_TOKEN أو ملف telegram_bot_token.txt")
        sys.exit(1)
    run_telegram_polling()


if __name__ == "__main__":
    main()
