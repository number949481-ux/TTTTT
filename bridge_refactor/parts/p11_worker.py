"""[VERBATIM SLICE] p11_worker
المصدر: 01.31_telegram_gen_bridge.py — الأسطر 5145..5449
المحتوى: process_user_task_async (المشغل الكامل للمهمة)
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
def process_user_task_async(
    chat_id: int,
    url: str | None,
    query: str,
    model: str = "claude-fable-5",
    project_key_hint: str | None = None,
    project_name_hint: str | None = None,
):
    """دالة خلفية موازية تنفذ المهمة وترفع النتيجة مباشرة لتليجرام والقناة مع نص أحدث رسالة والمسار"""
    run_owner_token = uuid.uuid4().hex
    project_key = None
    claimed_project_run = False
    try:
        # إصلاح: تهريب HTML لكل مدخلات المستخدم قبل وضعها في رسالة
        safe_query = html_escape(query)[:80]
        task_started_at = time.time()
        cfg = BridgeConfig(model=model, cooldown_hours=29.0)
        cfg.run_started_at = task_started_at
        cfg.selection_owner_token = run_owner_token
        requested_pid = extract_project_id(url) if url else ""
        known_project_key = lookup_project_key_for_locator(url) if url else None
        hinted_project_key = re.sub(r"[^A-Za-z0-9_-]", "_", str(project_key_hint or ""))[:80]
        # نفس Project Context يُفضَّل من state/handler أولاً، ثم lookup من الـURL/PID، ثم مشروع جديد.
        project_key = hinted_project_key or known_project_key or f"prj_{uuid.uuid4().hex[:16]}"
        claimed_project_run = claim_project_run(project_key, run_owner_token)
        if not claimed_project_run:
            send_telegram_message(chat_id, f"⏳ <b>المشروع <code>{html_escape(project_key)}</code> قيد التنفيذ حالياً.</b>\nانتظر انتهاء المهمة الجارية أو أعد المحاولة بعد قليل.")
            return
        registry = ProjectRegistry(project_key)
        cfg.selection_project_key = project_key
        runtime_binding = apply_project_runtime_binding(cfg, project_key, requested_model=model, registry=registry)
        send_telegram_message(chat_id, f"🚀 <b>جاري بدء المعالجة والتوليد...</b> <code>v{BUILD_VERSION}</code>\n💬 البرومبت: <i>{safe_query}...</i>\n🧠 الموديل: <code>{html_escape(cfg.model)}</code>")
        existing_identity = get_project_identity_record(project_key) or {}
        project_name = project_name_hint or existing_identity.get("project_name") or re.sub(r"\s+", " ", query).strip()[:60] or "مشروع بدون اسم"
        runtime_identity = remember_registry_identity(
            registry,
            root_pid=existing_identity.get("root_genspark_pid") or requested_pid,
            latest_pid=requested_pid or existing_identity.get("latest_genspark_pid"),
            project_name=project_name,
            chat_id=chat_id,
            status="RESUME_REQUESTED" if requested_pid else "STARTED",
        ) or existing_identity
        if (
            getattr(send_telegram_message, "__name__", "") == "send_telegram_message"
            and getattr(send_telegram_message, "__module__", "") == __name__
        ):
            attach_account_selection_live_transport(cfg, chat_id=chat_id, project_key=project_key, project_name=project_name)

        def on_credit_handoff(handoff_meta: dict):
            context = summarize_project_context(
                runtime_identity,
                current_pid=handoff_meta.get("source_project_id"),
                current_url=handoff_meta.get("continuation_url"),
            )
            checkpoint_id = str(handoff_meta.get("checkpoint_id") or getattr(cfg, "last_credit_checkpoint_id", "") or "")
            root_pid = context.get("root_pid") or handoff_meta.get("source_project_id") or "غير معروف"
            latest_pid = context.get("latest_pid") or context.get("current_pid") or root_pid
            checkpoint_line = f"\n<b>Checkpoint:</b> <code>{html_escape(checkpoint_id)}</code>" if checkpoint_id else ""
            resume_url = context.get("resume_url") or str(handoff_meta.get("continuation_url") or "")
            public_resume_prompt = summarize_resume_prompt_for_display(get_bridge_cfg_public_resume_prompt(cfg))
            send_telegram_message(
                chat_id,
                "🔁 <b>تم تثبيت handoff وسيبدأ الآن الاستئناف بنفس سياق المشروع.</b>\n"
                f"<b>المشروع:</b> {html_escape(project_name)}\n"
                f"<b>مفتاح المشروع:</b> <code>{project_key}</code>\n"
                f"<b>Root Project ID:</b> <code>{html_escape(root_pid)}</code>\n"
                f"<b>Latest Project ID:</b> <code>{html_escape(latest_pid)}</code>\n"
                f"<b>عداد الاستئناف:</b> <code>{html_escape(str(handoff_meta.get('continuation_index') or 0))}/{html_escape(str(handoff_meta.get('continuation_limit') or get_credit_continuation_limit(cfg)))}</code>{checkpoint_line}\n"
                f"<b>برومبت الاستئناف التالي:</b> <code>{html_escape(public_resume_prompt)}</code>\n"
                f"<b>رابط الاستئناف التالي:</b> {html_escape(resume_url)}\n"
                "<b>الوضع:</b> سيتم إرسال برومبت الاستئناف الخاص بهذا المشروع بعد اكتمال الحفظ بنجاح."
            )

        cfg.credit_handoff_callback = on_credit_handoff

        def on_project_update(stage_url, stage_status, stage_dir, stage_text, stage_email, stage_query):
            nonlocal runtime_identity
            actionable, stage_meta = should_capture_project_update(stage_url, stage_status, stage_dir, min_mtime=task_started_at)
            if not actionable:
                log_event("warning", f"تم تخطي checkpoint/report للحالة {stage_status}: {stage_meta['reason']}", extra=stage_meta)
                return {
                    "allow_continuation": stage_status != "CREDIT_EXHAUSTED",
                    "project_update_preserved": False,
                    "reason": stage_meta["reason"],
                    "checkpoint_id": "",
                }
            runtime_identity = remember_registry_identity(
                registry,
                root_pid=(runtime_identity or {}).get("root_genspark_pid") or requested_pid or stage_meta["pid"],
                latest_pid=stage_meta["pid"],
                project_name=project_name,
                chat_id=chat_id,
                status=stage_status,
            ) or runtime_identity
            update = registry.snapshot(stage_dir, stage_url, stage_status, stage_text)
            checkpoint_id = str(update.get("checkpoint") or "")
            sync = registry.github_sync(update)
            all_jobs = sync.get("jobs") or []
            queued_jobs = [job for job in all_jobs if str(job.get("state") or "") != "synced"]
            queued_ids = sync.get("queued") or []
            context = summarize_project_context(runtime_identity, current_pid=stage_meta["pid"], current_url=stage_url)
            if queued_jobs:
                first_job = queued_jobs[0]
                dest = first_job.get("destination", {}) if isinstance(first_job, dict) else {}
                branch_label = dest.get("branch") or ("auto-default" if dest.get("branch_mode") == "auto_default" else "غير محدد")
                details = "\n".join(
                    f"• <code>{html_escape(job.get('job_id'))}</code> → <code>{html_escape(job.get('state'))}</code> → <code>{html_escape(dest.get('repository') or '')}</code> @ <code>{html_escape(branch_label)}</code>"
                    for job in queued_jobs[:3]
                )
                details += "\n• لم يتم تأكيد الرفع إلى GitHub بعد؛ هذه فقط job/queue جاهزة أو قيد التنفيذ."
            elif sync.get("upload_confirmed") or sync.get("uploaded") or sync.get("modified") or sync.get("deleted"):
                commit_info = f"\n• 🔗 <b>Commit:</b> <code>{html_escape(sync.get('commit_hash', ''))}</code>" if sync.get("commit_hash") else ""
                stats_line = f"• 📊 <b>الإحصائيات:</b> ➕ <b>{len(sync.get('uploaded', []))}</b> جديد | ✏️ <b>{len(sync.get('modified', []))}</b> معدل | 🗑️ <b>{len(sync.get('deleted', []))}</b> محذوف | ⏸️ <b>{len(sync.get('unchanged', []))}</b> مطابق"
                file_lines = []
                for x in sync.get("uploaded", [])[:10]:
                    file_lines.append(f"  ➕ <code>{html_escape(x)}</code>")
                for x in sync.get("modified", [])[:10]:
                    file_lines.append(f"  ✏️ <code>{html_escape(x)}</code>")
                for x in sync.get("deleted", [])[:10]:
                    file_lines.append(f"  🗑️ <code>{html_escape(x)}</code>")
                files_block = "\n" + "\n".join(file_lines) if file_lines else ""
                details = f"{stats_line}{commit_info}{files_block}"
            else:
                details = f"• لم يجد النظام أي تغيير جديد؛ المستودع مطابق تماماً للأرشيف الحالي (Unchanged: <code>{len(sync.get('unchanged', []))}</code>)."
            skipped = "\n".join(f"• <code>{html_escape(x)}</code>" for x in sync.get("skipped", [])[:8])
            github_label = "تم إنشاء job GitHub لهذا المشروع ولم يتم تأكيد الرفع بعد" if sync.get("enabled") and queued_jobs else ("✅ تم الرفع والمزامنة بنجاح لـ GitHub" if sync.get("upload_confirmed") or sync.get("uploaded") or sync.get("modified") else ("تعذر تأكيد رفع GitHub لهذه اللقطة" if sync.get("enabled") and sync.get("upload_error") else "غير مفعل لهذا المشروع أو إعدادات GitHub غير مكتملة"))
            stage_label = "⚠️ استنزاف رصيد — تم حفظ نقطة استئناف صالحة ويجري الآن تقييم handoff" if stage_status == "CREDIT_EXHAUSTED" else "🔄 تحديث مشروع صالح"
            continuation_line = ""
            handoff_line = ""
            if stage_status == "CREDIT_EXHAUSTED":
                public_resume_prompt = summarize_resume_prompt_for_display(get_bridge_cfg_public_resume_prompt(cfg))
                continuation_line = f"\n<b>عداد الاستئناف:</b> <code>{format_credit_continuation_progress(cfg)}</code>"
                handoff_line = (
                    f"\n<b>Checkpoint:</b> <code>{html_escape(checkpoint_id)}</code>"
                    f"\n<b>Root Project ID:</b> <code>{html_escape(context.get('root_pid') or stage_meta['pid'])}</code>"
                    f"\n<b>Latest Project ID:</b> <code>{html_escape(context.get('latest_pid') or stage_meta['pid'])}</code>"
                    f"\n<b>برومبت الاستئناف المرشح:</b> <code>{html_escape(public_resume_prompt)}</code>"
                    f"\n<b>رابط الاستئناف المرشح:</b> {html_escape(context.get('current_url') or context.get('resume_url') or build_genspark_viewer_url(stage_meta['pid']))}"
                    "\n<b>الوضع:</b> لم يبدأ إرسال برومبت الاستئناف بعد؛ سيبدأ فقط إذا اكتمل حفظ checkpoint/report ضمن نفس مفتاح المشروع."
                )
            msg = (f"{stage_label}\n<b>المشروع:</b> {html_escape(project_name)}\n"
                   f"<b>مفتاح المشروع:</b> <code>{project_key}</code>\n"
                   f"<b>الحالة:</b> <code>{html_escape(stage_status)}</code>\n"
                   f"<b>Project ID:</b> <code>{html_escape(stage_meta['pid'])}</code>{continuation_line}{handoff_line}\n"
                   f"<b>GitHub:</b> {github_label}\n<b>طابور/الملفات:</b>\n{details}")
            if skipped:
                msg += f"\n<b>ملفات لم تُرفع:</b>\n{skipped}"
            send_telegram_message(chat_id, msg)
            return {
                "allow_continuation": True,
                "project_update_preserved": True,
                "reason": "",
                "checkpoint_id": checkpoint_id,
                "queued": queued_ids,
                "resume_url": context.get("resume_url") or context.get("current_url"),
                "root_pid": context.get("root_pid"),
                "latest_pid": context.get("latest_pid"),
            }

        live_preview_msg_id = None
        seen_live_preview_pid = None

        def handle_live_project_start(live_pid: str):
            nonlocal live_preview_msg_id, seen_live_preview_pid
            if not live_pid or seen_live_preview_pid == live_pid:
                return
            seen_live_preview_pid = live_pid
            preview_kb = build_live_preview_keyboard(live_pid, status="running")
            text = (
                f"⚡ <b>بدأ بناء المشروع السحابي فوراً!</b>\n"
                f"📌 <b>المشروع:</b> {html_escape(project_name)}\n"
                f"🆔 <b>Project ID:</b> <code>{html_escape(live_pid)}</code>\n"
                f"🧠 <b>الموديل:</b> <code>{html_escape(cfg.model)}</code>\n\n"
                f"🌐 <i>يمكنك متابعة التوليد والأكواد لحظياً عبر الزر أدناه:</i>"
            )
            try:
                res = send_telegram_message_detailed(chat_id, text, reply_markup=preview_kb)
                if res and isinstance(res, dict) and res.get("ok"):
                    live_preview_msg_id = res.get("result", {}).get("message_id")
            except Exception as live_err:
                log_event("warning", f"تعذر إرسال بطاقة المعاينة الفورية: {live_err}")

        pub_url, status, used_acc, ext_dir, last_resp_text = send_message_with_auto_account_failover(
            url=url, query=query, bridge_cfg=cfg, progress_callback=on_project_update,
            on_project_start_callback=handle_live_project_start,
        )

        if status == "ALL_ACCOUNTS_IN_COOLDOWN":
            send_telegram_message(
                chat_id,
                "⚠️ <b>جميع الحسابات المصرح بها مشغولة أو في فترة التبريد حالياً.</b>\n"
                "يرجى المحاولة بعد قليل أو عند تجدد رصيد الحسابات تلقائياً (29h)."
            )
            return
        if status == "ALL_ACCOUNTS_BUSY":
            send_telegram_message(
                chat_id,
                "⏳ <b>كل الحسابات المؤهلة الحالية محجوزة لمهمات أخرى.</b>\n"
                "لم يبدأ التنفيذ على حساب جديد لأننا ثبّتْنا attribution آمن لكل مهمة. أعد المحاولة بعد قليل."
            )
            return

        acc_email = html_escape(used_acc.get("email")) if used_acc else "غير محدد"
        is_finished = check_project_finished_flag(status, last_resp_text)
        final_pid = extract_stage_project_id(pub_url, ext_dir)
        runtime_identity = remember_registry_identity(
            registry,
            root_pid=(runtime_identity or {}).get("root_genspark_pid") or requested_pid or final_pid,
            latest_pid=final_pid or requested_pid or (runtime_identity or {}).get("latest_genspark_pid"),
            project_name=project_name,
            chat_id=chat_id,
            status=status,
        ) or runtime_identity
        context = summarize_project_context(runtime_identity, current_pid=final_pid or requested_pid, current_url=pub_url or url)
        pid = context.get("current_pid") or final_pid or requested_pid or "غير معروف"
        resume_pid = context.get("resume_pid") or final_pid or requested_pid or ""
        outcome = describe_terminal_outcome(status, pub_url, cfg)

        response_preview = ""
        if outcome["allow_preview"] and last_resp_text:
            clean_text = redact_github_secrets(str(last_resp_text).strip())
            clean_text = html_escape(clean_text)
            if len(clean_text) > 2500:
                clean_text = clean_text[:2500] + "\n... [تم الاقتصاص لزيادة الحجم]"
            response_preview = f"💬 <b>آخر رسالة من التوليد:</b>\n<pre>{clean_text}</pre>\n\n"

        # إصلاح: لو مفيش رابط عام نكتب تنبيه بدل زر ميت (كان تليجرام يرفض الكيبورد بالكامل)
        if pub_url:
            url_line = f"🌐 <b>رابط الويب اب العام:</b> {html_escape(pub_url)}"
        else:
            url_line = "🌐 <b>رابط الويب اب العام:</b> غير متاح (المشروع قد يكون خاصاً أو لم يكتمل)"
        root_line = f"\n🌱 <b>Root Project ID:</b> <code>{html_escape(context.get('root_pid') or pid)}</code>"
        latest_line = f"\n🧷 <b>Latest Project ID:</b> <code>{html_escape(context.get('latest_pid') or pid)}</code>"
        resume_line = ""
        if context.get("resume_url"):
            resume_line = f"\n🔗 <b>رابط الاستئناف الحالي:</b> {html_escape(context.get('resume_url'))}"
        fork_line = ""
        if context.get("forked"):
            fork_line = "\n🔀 <b>سياق المشروع:</b> تم الحفاظ على نفس مفتاح المشروع رغم انتقال الـProject ID أثناء continuation/fork."

        res_msg = (
            f"{outcome['title']}\n\n"
            f"{response_preview}"
            f"🧭 <b>النتيجة النهائية:</b> {html_escape(outcome['note'])}\n"
            f"{url_line}\n"
            f"📁 <b>مسار الساندبوكس:</b> <code>{html_escape(ext_dir or 'غير متاح')}</code>\n"
            f"📊 <b>الحالة:</b> <code>{html_escape(status)}</code>\n"
            f"📌 <b>اسم المشروع:</b> {html_escape(project_name)}\n"
            f"🔐 <b>مفتاح المشروع:</b> <code>{project_key}</code>\n"
            f"📧 <b>الحساب المستعمل:</b> <code>{acc_email}</code>\n"
            f"🆔 <b>Project ID:</b> <code>{html_escape(pid)}</code>{root_line}{latest_line}{resume_line}{fork_line}\n"
            f"🏁 <b>علم الانتهاء:</b> {'✅ مكتمل (FINISHED)' if is_finished else '⚠️ غير مكتمل'}"
        )

        # إصلاح: بناء الكيبورد بدون أزرار فارغة (url=None كان يكسر الرسالة كلها بصمت)
        kb_rows = []
        if pub_url:
            kb_rows.append([{"text": "🌐 فتح المعاين المباشر", "url": pub_url}])
        if resume_pid:
            kb_rows.append([
                {"text": "🔄 استئناف هذا المشروع", "callback_data": f"cont:{resume_pid}"},
                {"text": "🌳 نقاط الاستئناف", "callback_data": f"tree:{resume_pid}"},
            ])
        if project_key:
            kb_rows.append([{"text": "⭐ تفاصيل المشروع", "callback_data": f"pview:{project_key}"}])
        kb_rows.append([{"text": "🚀 مشروع جديد", "callback_data": "cmd:new_proj"}])
        reply_markup = make_inline_keyboard(kb_rows)

        send_telegram_message(chat_id, res_msg, reply_markup=reply_markup)

        # 🟢 تحديث بطاقة المعاينة الفورية المتطورة لتصبح زر مكتمل (P7-A)
        if live_preview_msg_id and seen_live_preview_pid and status == "COMPLETED":
            completed_kb = build_live_preview_keyboard(seen_live_preview_pid, status="completed")
            completed_text = (
                f"✅ <b>اكتمل بناء المشروع بنجاح 100%!</b>\n"
                f"📌 <b>المشروع:</b> {html_escape(project_name)}\n"
                f"🆔 <b>Project ID:</b> <code>{html_escape(seen_live_preview_pid)}</code>\n"
                f"🧠 <b>الموديل:</b> <code>{html_escape(cfg.model)}</code>\n\n"
                f"🟢 <i>تم الانتهاء وجاهز للعرض والمعاينة التفاعلية:</i>"
            )
            try:
                edit_telegram_message_text(chat_id, live_preview_msg_id, completed_text, reply_markup=completed_kb)
            except Exception as edit_err:
                log_event("warning", f"تعذر تحديث بطاقة المعاينة المكتملة: {edit_err}")

        archive_path, archive_msg = describe_archive_delivery(ext_dir)

        if archive_msg:
            log_event("info", f"تم تعطيل رفع الأرشيف إلى Telegram وفق D-002: {archive_path.name}")
            send_telegram_message(chat_id, archive_msg)
            if str(chat_id) != DEFAULT_CHANNEL_ID:
                send_telegram_message(DEFAULT_CHANNEL_ID, res_msg, reply_markup=reply_markup)
    except Exception as e:
        # إصلاح: أي خطأ داخلي في المهمة يوصل للمستخدم بدل الاختفاء الصامت
        safe_error = redact_github_secrets(str(e))[:500]
        log_event("error", f"خطأ غير متوقع في معالجة المهمة: {safe_error}")
        try:
            send_telegram_message(chat_id, f"⚠️ <b>حدث خطأ داخلي أثناء المعالجة:</b>\n<code>{html_escape(safe_error)}</code>")
        except Exception:
            pass
    finally:
        if project_key and claimed_project_run:
            release_project_run(project_key, run_owner_token)


