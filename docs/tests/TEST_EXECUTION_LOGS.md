# 📜 سجل مخرجات تشغيل الاختبارات (TEST_EXECUTION_LOGS.md)

> **المسؤولية:** توثيق مخرجات التيرمينال الحقيقية، الـ Exit Codes، والأزمنة المقاسة  

---

## ⚡ آخر جلسة تشغيل ناجحة (Latest Execution Session)

* **التاريخ والوقت:** `2026-08-20 22:33:57 UTC`
* **الأمر المنفذ:** `python -m unittest discover tests -v`
* **الزمن المقاس:** `0.504 ثانية`
* **النتيجة العامة:** `Ran 221 tests — OK`
* **فحص تكامل التوثيق (P10):** `PASS (33 files, 3 links)`
* **رمز الخروج (Exit Code):** `0` ✅

---

## 📋 مخرجات التيرمينال الحية:

```text
test_docs_integrity_no_broken_links (test_p10_docs_integrity.TestDocsIntegrityP10.test_docs_integrity_no_broken_links)
التحقق من عدم وجود أي روابط مكسورة في منظومة docs بأكملها ... ok
test_01_whitelist_exact_official_values (test_p11_button_styles.TestButtonStylesWhitelist.test_01_whitelist_exact_official_values)
1. الـ Whitelist يجب أن تكون بالظبط القيم الرسمية الثلاثة في Bot API 9.4 ... ok
test_02_valid_style_passes_through (test_p11_button_styles.TestButtonStylesWhitelist.test_02_valid_style_passes_through)
2. style صالح يمرر كما هو في الـ JSON النهائي ... ok
test_03_invalid_style_is_stripped (test_p11_button_styles.TestButtonStylesWhitelist.test_03_invalid_style_is_stripped)
3. أي style خارج الـ Whitelist يُحذف (positive/destructive ترجع 400 من تيليجرام) ... ok
test_04_style_normalized_case_and_spaces (test_p11_button_styles.TestButtonStylesWhitelist.test_04_style_normalized_case_and_spaces)
4. التطبيع: 'Danger' و ' SUCCESS ' تتحول للقيمة الرسمية الصغيرة ... ok
test_05_buttons_without_style_unchanged (test_p11_button_styles.TestButtonStylesWhitelist.test_05_buttons_without_style_unchanged)
5. عدم الانحدار: الأزرار القديمة بدون style تعمل كما هي بدون أي حقل زائد ... ok
test_06_style_json_serializable (test_p11_button_styles.TestButtonStylesWhitelist.test_06_style_json_serializable)
6. الكيبورد الملون قابل للتسلسل JSON خام (مسار reply_markup المباشر بدون مكتبة) ... ok
test_07_no_icon_custom_emoji_leakage (test_p11_button_styles.TestButtonStylesWhitelist.test_07_no_icon_custom_emoji_leakage)
7. حظر تسريب icon_custom_emoji_id (يتطلب Premium) — لا يمرر أبداً ... ok
test_08_live_preview_running_is_primary_blue (test_p11_button_styles.TestColoredKeyboardsIntegration.test_08_live_preview_running_is_primary_blue)
8. زر المعاينة الحية أثناء البناء = أزرق (primary) ... ok
test_09_live_preview_done_is_success_green (test_p11_button_styles.TestColoredKeyboardsIntegration.test_09_live_preview_done_is_success_green)
9. زر المشروع المكتمل = أخضر (success) ... ok
test_10_source_has_no_invalid_style_literals (test_p11_button_styles.TestColoredKeyboardsIntegration.test_10_source_has_no_invalid_style_literals)
10. فحص شفرة المصدر: لا توجد أي قيمة style غير رسمية مكتوبة حرفياً ... ok
test_07_carry_pid_mechanism_exists (test_p12_resume_same_project.TestBridgeSameProjectResume.test_07_carry_pid_mechanism_exists)
carry_pid يُلتقط من الـ callback ويُستأنف عليه في المحاولات التالية ... ok
test_08_carry_pid_skips_new_fork (test_p12_resume_same_project.TestBridgeSameProjectResume.test_08_carry_pid_skips_new_fork)
عند وجود carry_pid يجب تخطي مسار fork/url بالكامل (elif) — لا مشروع جديد ... ok
test_09_pid_always_captured_after_send_chat (test_p12_resume_same_project.TestBridgeSameProjectResume.test_09_pid_always_captured_after_send_chat)
بعد كل send_chat ناجح يثبت الـ pid في carry_pid للمحاولات التالية ... ok
test_10_stream_interrupted_enters_polling_not_fail (test_p12_resume_same_project.TestBridgeSameProjectResume.test_10_stream_interrupted_enters_polling_not_fail)
__STREAM_INTERRUPTED__ يجب أن يحول الحالة لـ RUNNING (متابعة) لا فشل ... ok
test_11_callback_forwarded_always (test_p12_resume_same_project.TestBridgeSameProjectResume.test_11_callback_forwarded_always)
الـ callback الداخلي يُمرر دائماً لـ send_chat (يلتقط الـ pid حتى مع عدم طلب preview) ... ok
test_12_live_preview_fires_on_resume_paths (test_p12_resume_same_project.TestBridgeSameProjectResume.test_12_live_preview_fires_on_resume_paths)
زر المعاينة يُطلق فور معرفة الـ pid في مسار الاستئناف ومسار الـ fork (P12-C) ... ok
test_01_stream_interrupt_returns_pid_not_new_chat (test_p12_resume_same_project.TestEngineStreamResilience.test_01_stream_interrupt_returns_pid_not_new_chat)
انقطاع البث مع pid حي يجب أن يرجع __STREAM_INTERRUPTED__ + نفس الـ pid ... ok
test_02_final_except_preserves_pid (test_p12_resume_same_project.TestEngineStreamResilience.test_02_final_except_preserves_pid)
الـ except الخارجي يجب ألا يرجع None للـ pid (كان يسبب chat id جديد) ... ok
test_03_no_terminal_live_stream (test_p12_resume_same_project.TestEngineStreamResilience.test_03_no_terminal_live_stream)
لا طباعة لحظية chunk-by-chunk في الترمنال — تجميع صامت فقط ... ok
test_04_full_response_printed_with_elapsed_seconds (test_p12_resume_same_project.TestEngineStreamResilience.test_04_full_response_printed_with_elapsed_seconds)
الطباعة الكاملة دفعة واحدة + سطر 'اخد X ثانية' بعد الاكتمال ... ok
test_05_timeout_is_idle_tuple_not_total_cut (test_p12_resume_same_project.TestEngineStreamResilience.test_05_timeout_is_idle_tuple_not_total_cut)
timeout يجب أن يكون tuple (اتصال، قراءة) مع stream=True — لا قطع كلي ... ok
test_06_ticket_file_still_written_incrementally (test_p12_resume_same_project.TestEngineStreamResilience.test_06_ticket_file_still_written_incrementally)
ملف التذكرة يبقى لحظياً (وظيفة أصلية) رغم إلغاء بث الترمنال ... ok
test_13_refactor_contains_p12_fixes (test_p12_resume_same_project.TestRuntimeParityAfterP12.test_13_refactor_contains_p12_fixes) ... ok
test_09_low_balance_handled_in_failover (test_p13_preflight_balance.TestFailoverSilentSkip.test_09_low_balance_handled_in_failover) ... ok
test_10_low_balance_skips_silently_with_continue (test_p13_preflight_balance.TestFailoverSilentSkip.test_10_low_balance_skips_silently_with_continue) ... ok
test_11_low_balance_skip_precedes_credit_exhausted_handling (test_p13_preflight_balance.TestFailoverSilentSkip.test_11_low_balance_skip_precedes_credit_exhausted_handling) ... ok
test_12_no_user_notification_in_skip_block (test_p13_preflight_balance.TestFailoverSilentSkip.test_12_no_user_notification_in_skip_block) ... ok
test_13_no_wrong_30min_auth_ban_for_low_balance (test_p13_preflight_balance.TestFailoverSilentSkip.test_13_no_wrong_30min_auth_ban_for_low_balance) ... ok
/home/user/webapp/01.31_telegram_gen_bridge.py:71: ResourceWarning: unclosed file <_io.TextIOWrapper name='/home/user/webapp/bridge_bot.log' mode='a' encoding='utf-8'>
  logging.basicConfig(
ResourceWarning: Enable tracemalloc to get the object allocation traceback
test_01_min_preflight_balance_default_100 (test_p13_preflight_balance.TestPreflightBalanceConfig.test_01_min_preflight_balance_default_100) ... ok
test_02_min_preflight_balance_configurable (test_p13_preflight_balance.TestPreflightBalanceConfig.test_02_min_preflight_balance_configurable) ... ok
test_03_gate_exists_and_reads_threshold (test_p13_preflight_balance.TestPreflightBalanceGate.test_03_gate_exists_and_reads_threshold) ... ok
test_04_low_balance_triggers_29h_cooldown (test_p13_preflight_balance.TestPreflightBalanceGate.test_04_low_balance_triggers_29h_cooldown) ... ok
test_05_low_balance_returns_before_any_fork_or_chat (test_p13_preflight_balance.TestPreflightBalanceGate.test_05_low_balance_returns_before_any_fork_or_chat) ... ok
test_06_recheck_after_session_refresh (test_p13_preflight_balance.TestPreflightBalanceGate.test_06_recheck_after_session_refresh) ... ok
test_07_network_failure_not_punished (test_p13_preflight_balance.TestPreflightBalanceGate.test_07_network_failure_not_punished) ... ok
test_08_valid_balance_persisted_to_account (test_p13_preflight_balance.TestPreflightBalanceGate.test_08_valid_balance_persisted_to_account) ... ok
test_14_p06_part_contains_preflight_gate (test_p13_preflight_balance.TestRefactorParityAfterP13.test_14_p06_part_contains_preflight_gate) ... ok
test_01_delete_guard_constants_exist (test_p14_upsert_sync.TestP14Constants.test_01_delete_guard_constants_exist) ... ok
test_02_identical_files_equal (test_p14_upsert_sync.TestP14ContentEqual.test_02_identical_files_equal) ... ok
test_03_crlf_vs_lf_considered_equal (test_p14_upsert_sync.TestP14ContentEqual.test_03_crlf_vs_lf_considered_equal) ... ok
test_04_different_content_not_equal (test_p14_upsert_sync.TestP14ContentEqual.test_04_different_content_not_equal) ... ok
test_05_missing_file_not_equal (test_p14_upsert_sync.TestP14ContentEqual.test_05_missing_file_not_equal) ... ok
test_10_partial_archive_does_not_wipe_repo (test_p14_upsert_sync.TestP14DeleteGuard.test_10_partial_archive_does_not_wipe_repo)
سيناريو saray2and2: أرشيف 4 ملفات مقابل ريبو 73 ملف ➔ صفر حذف. ... ok
test_11_full_archive_deletes_absent_files (test_p14_upsert_sync.TestP14DeleteGuard.test_11_full_archive_deletes_absent_files)
أرشيف كامل ينقصه ملف واحد ➔ يُحذف طبيعياً (نسبة الحذف < 50%). ... ok
test_12_git_dir_never_counted_or_deleted (test_p14_upsert_sync.TestP14DeleteGuard.test_12_git_dir_never_counted_or_deleted) ... ok
test_13_nested_root_detected_by_repo_overlap (test_p14_upsert_sync.TestP14RootDetection.test_13_nested_root_detected_by_repo_overlap)
أرشيف بمجلد متداخل عميق ➔ يُختار المستوى المطابق للريبو. ... ok
test_14_empty_repo_falls_back_to_legacy (test_p14_upsert_sync.TestP14RootDetection.test_14_empty_repo_falls_back_to_legacy)
ريبو فارغ ➔ fallback لسلوك get_source_root القديم. ... ok
test_15_call_site_after_clone_in_source (test_p14_upsert_sync.TestP14RootDetection.test_15_call_site_after_clone_in_source)
في process_single_tar: كشف الجذر يأتي بعد git clone وليس قبله. ... ok
test_16_secret_files_still_never_copied (test_p14_upsert_sync.TestP14SecretsProtection.test_16_secret_files_still_never_copied) ... ok
test_06_identical_file_not_touched (test_p14_upsert_sync.TestP14UpsertCopy.test_06_identical_file_not_touched) ... ok
test_07_crlf_only_difference_not_touched (test_p14_upsert_sync.TestP14UpsertCopy.test_07_crlf_only_difference_not_touched) ... ok
test_08_modified_file_is_overwritten (test_p14_upsert_sync.TestP14UpsertCopy.test_08_modified_file_is_overwritten) ... ok
test_09_new_file_is_copied (test_p14_upsert_sync.TestP14UpsertCopy.test_09_new_file_is_copied) ... ok
test_01_all_27_components_present (test_p15_qwen_engine.TestP15EngineCompleteness.test_01_all_27_components_present) ... ok
test_02_model_chain_contract (test_p15_qwen_engine.TestP15EngineCompleteness.test_02_model_chain_contract)
سلسلة الموديلات: مرحلتان بمهلة 30s + Thinking/Fast. ... ok
test_03_constants_values (test_p15_qwen_engine.TestP15EngineCompleteness.test_03_constants_values) ... ok
test_04_file_lock_is_real_lock (test_p15_qwen_engine.TestP15EngineCompleteness.test_04_file_lock_is_real_lock)
القفل الذري _QWEN_FILE_LOCK موجود وقابل للاستخدام. ... ok
test_05_dalvik_android15_headers_in_workers (test_p15_qwen_engine.TestP15EngineCompleteness.test_05_dalvik_android15_headers_in_workers)
هيدرات Dalvik / Android 15 موجودة في ثريد الحسابات وثريد الزائر. ... ok
test_06_sse_streaming_and_stop_event (test_p15_qwen_engine.TestP15EngineCompleteness.test_06_sse_streaming_and_stop_event)
تدفق SSE مع الإلغاء الفوري بـ stop_event في العاملين. ... ok
test_07_guest_worker_runs_in_parallel (test_p15_qwen_engine.TestP15EngineCompleteness.test_07_guest_worker_runs_in_parallel)
ثريد الزائر يُطلق بالتوازي داخل race_accounts (Bypass احتياطي). ... ok
test_08_auto_refresh_uses_password_hash (test_p15_qwen_engine.TestP15EngineCompleteness.test_08_auto_refresh_uses_password_hash) ... ok
test_09_logger_injection_works (test_p15_qwen_engine.TestP15EngineCompleteness.test_09_logger_injection_works) ... ok
test_10_generate_ai_summary_parses_commit_and_summary (test_p15_qwen_engine.TestP15EngineCompleteness.test_10_generate_ai_summary_parses_commit_and_summary)
استخراج COMMIT/SUMMARY من الرد — عبر حقن رد وهمي بدون شبكة. ... ok
test_11_uploader_imports_engine (test_p15_qwen_engine.TestP15UploaderDelegation.test_11_uploader_imports_engine) ... ok
test_12_no_duplicate_engine_functions_in_uploader (test_p15_qwen_engine.TestP15UploaderDelegation.test_12_no_duplicate_engine_functions_in_uploader)
ممنوع بقاء نسخ مكررة من دوال كوين داخل 04. ... ok
test_13_uploader_module_loads_with_compat_names (test_p15_qwen_engine.TestP15UploaderDelegation.test_13_uploader_module_loads_with_compat_names) ... ok
test_14_winner_state_accessed_via_module (test_p15_qwen_engine.TestP15UploaderDelegation.test_14_winner_state_accessed_via_module)
LAST_AI_* تُقرأ من qwen_engine (globals حية) وليس نسخة ميتة. ... ok
test_15_bridge_0128_banner_and_version (test_p15_qwen_engine.TestP15VersionBump.test_15_bridge_0128_banner_and_version) ... ok
test_16_scripts_reference_0128 (test_p15_qwen_engine.TestP15VersionBump.test_16_scripts_reference_0128) ... /home/user/webapp/tests/test_p15_qwen_engine.py:185: ResourceWarning: unclosed file <_io.TextIOWrapper name='/home/user/webapp/scripts/hadith_sijil.py' mode='r' encoding='utf-8'>
  gate = open(os.path.join(BASE_DIR, "scripts", "hadith_sijil.py"), encoding="utf-8").read()
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/home/user/webapp/tests/test_p15_qwen_engine.py:186: ResourceWarning: unclosed file <_io.TextIOWrapper name='/home/user/webapp/scripts/rebuild_refactor.py' mode='r' encoding='utf-8'>
  rebuild = open(os.path.join(BASE_DIR, "scripts", "rebuild_refactor.py"), encoding="utf-8").read()
ResourceWarning: Enable tracemalloc to get the object allocation traceback
ok
test_01_helper_defined_inside_send_public (test_p16_early_public.TestP16EarlyMakePublic.test_01_helper_defined_inside_send_public)
الدالة المساعدة معرفة داخل الدالة الرئيسية. ... ok
test_02_called_from_pid_capture_callback (test_p16_early_public.TestP16EarlyMakePublic.test_02_called_from_pid_capture_callback)
النشر المبكر يُستدعى من ملتقط الـ pid (مسار البث الحي). ... ok
test_03_called_in_carry_pid_resume_path (test_p16_early_public.TestP16EarlyMakePublic.test_03_called_in_carry_pid_resume_path)
مسار الاستئناف carry_pid ينشر مبكراً (المشروع القائم لا يرسل project_start). ... ok
test_04_called_in_fork_url_path (test_p16_early_public.TestP16EarlyMakePublic.test_04_called_in_fork_url_path)
مسار الفورك/URL ينشر مبكراً فور معرفة المشروع. ... ok
test_05_fire_and_forget_daemon_thread (test_p16_early_public.TestP16EarlyMakePublic.test_05_fire_and_forget_daemon_thread)
التنفيذ في خيط خلفي daemon — لا يعطّل البث الرئيسي. ... ok
test_06_once_per_pid_dedup (test_p16_early_public.TestP16EarlyMakePublic.test_06_once_per_pid_dedup)
عدم التكرار: pid منشور مسبقاً لا يُعاد نشره. ... ok
test_07_ignores_sentinel_pids (test_p16_early_public.TestP16EarlyMakePublic.test_07_ignores_sentinel_pids)
الـ pids الوهمية (تبدأ بـ __) تُتجاهل — لا نشر لـ __STREAM_INTERRUPTED__. ... ok
test_08_cookies_snapshot_isolation (test_p16_early_public.TestP16EarlyMakePublic.test_08_cookies_snapshot_isolation)
الخيط الخلفي يعمل على نسخة snapshot من الكوكيز — لا سباق مع الحلقة الرئيسية. ... ok
test_09_banner_and_version_reflect_p16 (test_p16_early_public.TestP16EarlyMakePublic.test_09_banner_and_version_reflect_p16)
البانر 01.31 يذكر P16 والنشر العام المبكر. ... ok
test_01_refresh_condition_includes_expired_session (test_p17_hardening.TestExpiredSessionGate.test_01_refresh_condition_includes_expired_session) ... ok
test_02_old_vulnerable_condition_gone (test_p17_hardening.TestExpiredSessionGate.test_02_old_vulnerable_condition_gone) ... ok
test_01_pytest_cache_untracked (test_p17_hardening.TestGeneratedFilesUntracked.test_01_pytest_cache_untracked) ... ok
test_02_bridge_log_untracked (test_p17_hardening.TestGeneratedFilesUntracked.test_02_bridge_log_untracked) ... ok
test_03_gitignore_covers_both (test_p17_hardening.TestGeneratedFilesUntracked.test_03_gitignore_covers_both) ... ok
/home/user/webapp/01.31_telegram_gen_bridge.py:71: ResourceWarning: unclosed file <_io.TextIOWrapper name='/home/user/webapp/bridge_bot.log' mode='a' encoding='utf-8'>
  logging.basicConfig(
ResourceWarning: Enable tracemalloc to get the object allocation traceback
test_01_allowed_private_user (test_p17_hardening.TestGroupChatSupport.test_01_allowed_private_user) ... ok
test_02_unknown_private_user_denied (test_p17_hardening.TestGroupChatSupport.test_02_unknown_private_user_denied) ... ok
test_03_default_channel_group_allowed (test_p17_hardening.TestGroupChatSupport.test_03_default_channel_group_allowed) ... ok
test_04_unknown_group_denied_without_allowed_sender (test_p17_hardening.TestGroupChatSupport.test_04_unknown_group_denied_without_allowed_sender) ... ok
test_05_unknown_group_allowed_with_allowed_sender (test_p17_hardening.TestGroupChatSupport.test_05_unknown_group_allowed_with_allowed_sender) ... ok
test_06_unknown_group_denied_with_unknown_sender (test_p17_hardening.TestGroupChatSupport.test_06_unknown_group_denied_with_unknown_sender) ... ok
test_07_invalid_ids_denied (test_p17_hardening.TestGroupChatSupport.test_07_invalid_ids_denied) ... ok
test_08_message_path_uses_gate (test_p17_hardening.TestGroupChatSupport.test_08_message_path_uses_gate) ... ok
test_09_callback_path_uses_gate (test_p17_hardening.TestGroupChatSupport.test_09_callback_path_uses_gate) ... ok
test_10_no_raw_membership_checks_left_in_handler (test_p17_hardening.TestGroupChatSupport.test_10_no_raw_membership_checks_left_in_handler) ... ok
test_11_env_extension_supported (test_p17_hardening.TestGroupChatSupport.test_11_env_extension_supported) ... ok
test_01_recheck_balance_after_mid_chat_refresh (test_p17_hardening.TestMidChatBalanceGate.test_01_recheck_balance_after_mid_chat_refresh) ... ok
test_02_low_balance_triggers_cooldown_and_silent_skip (test_p17_hardening.TestMidChatBalanceGate.test_02_low_balance_triggers_cooldown_and_silent_skip) ... ok
test_03_network_failure_not_punished (test_p17_hardening.TestMidChatBalanceGate.test_03_network_failure_not_punished) ... ok
test_04_retry_continue_preserved (test_p17_hardening.TestMidChatBalanceGate.test_04_retry_continue_preserved) ... ok
test_01_git_native_sync_removed (test_p17_hardening.TestRestOnlyUploader.test_01_git_native_sync_removed) ... ok
test_02_no_git_clone_or_push_in_uploader (test_p17_hardening.TestRestOnlyUploader.test_02_no_git_clone_or_push_in_uploader) ... ok
test_03_uses_contents_rest_api (test_p17_hardening.TestRestOnlyUploader.test_03_uses_contents_rest_api) ... ok
test_04_p20_decision_documented (test_p17_hardening.TestRestOnlyUploader.test_04_p20_decision_documented) ... ok
test_01_deep_thinking_detected (test_p18_activity_stop.TestExtractActivitySignature.test_01_deep_thinking_detected) ... ok
test_02_tasks_remaining_with_number (test_p18_activity_stop.TestExtractActivitySignature.test_02_tasks_remaining_with_number) ... ok
test_03_tasks_remaining_number_after_label (test_p18_activity_stop.TestExtractActivitySignature.test_03_tasks_remaining_number_after_label) ... ok
test_04_tasks_remaining_without_number (test_p18_activity_stop.TestExtractActivitySignature.test_04_tasks_remaining_without_number) ... ok
test_05_no_indicator (test_p18_activity_stop.TestExtractActivitySignature.test_05_no_indicator) ... ok
test_06_none_and_empty_safe (test_p18_activity_stop.TestExtractActivitySignature.test_06_none_and_empty_safe) ... ok
test_01_monitor_called_inside_polling_loop (test_p18_activity_stop.TestPollingLoopIntegration.test_01_monitor_called_inside_polling_loop) ... ok
test_02_baseline_captured_before_loop (test_p18_activity_stop.TestPollingLoopIntegration.test_02_baseline_captured_before_loop) ... ok
test_03_fetch_failure_returns_none_and_is_ignored (test_p18_activity_stop.TestPollingLoopIntegration.test_03_fetch_failure_returns_none_and_is_ignored) ... ok
test_04_build_version_bumped (test_p18_activity_stop.TestPollingLoopIntegration.test_04_build_version_bumped) ... ok
test_01_indicator_disappeared_stops (test_p18_activity_stop.TestShouldStopOnActivityChange.test_01_indicator_disappeared_stops) ... ok
test_02_tasks_increased_stops (test_p18_activity_stop.TestShouldStopOnActivityChange.test_02_tasks_increased_stops) ... ok
test_03_tasks_decreased_also_stops (test_p18_activity_stop.TestShouldStopOnActivityChange.test_03_tasks_decreased_also_stops) ... ok
test_04_tasks_same_continues (test_p18_activity_stop.TestShouldStopOnActivityChange.test_04_tasks_same_continues) ... ok
test_05_inactive_baseline_no_decision (test_p18_activity_stop.TestShouldStopOnActivityChange.test_05_inactive_baseline_no_decision) ... ok
test_06_none_prev_or_curr_no_decision (test_p18_activity_stop.TestShouldStopOnActivityChange.test_06_none_prev_or_curr_no_decision) ... ok
test_07_unknown_count_disappearance_still_stops (test_p18_activity_stop.TestShouldStopOnActivityChange.test_07_unknown_count_disappearance_still_stops) ... ok
test_08_deep_thinking_toggled_stops (test_p18_activity_stop.TestShouldStopOnActivityChange.test_08_deep_thinking_toggled_stops) ... ok
test_09_deep_thinking_appeared_stops (test_p18_activity_stop.TestShouldStopOnActivityChange.test_09_deep_thinking_appeared_stops) ... ok
test_10_stable_signature_continues (test_p18_activity_stop.TestShouldStopOnActivityChange.test_10_stable_signature_continues) ... ok
test_01_summary_mentions_source_and_new_name (test_p19_copy_settings.TestCopiedSettingsSummary.test_01_summary_mentions_source_and_new_name) ... ok
test_02_disabled_github_reported (test_p19_copy_settings.TestCopiedSettingsSummary.test_02_disabled_github_reported) ... ok
test_01_invalid_source_key_rejected (test_p19_copy_settings.TestCopyProjectSettings.test_01_invalid_source_key_rejected) ... ok
test_02_source_defined_with_no_env_fallback (test_p19_copy_settings.TestCopyProjectSettings.test_02_source_defined_with_no_env_fallback)
التوكن يُقرأ من مخزن المشروع فقط — allow_env_fallback=False حرفياً. ... ok
test_03_new_key_and_sequential_name (test_p19_copy_settings.TestCopyProjectSettings.test_03_new_key_and_sequential_name) ... ok
test_04_no_pid_skips_identity_upsert (test_p19_copy_settings.TestCopyProjectSettings.test_04_no_pid_skips_identity_upsert) ... ok
test_05_github_token_passed_only_when_enabled (test_p19_copy_settings.TestCopyProjectSettings.test_05_github_token_passed_only_when_enabled) ... ok
test_01_sources_as_cpysrc_buttons (test_p19_copy_settings.TestCopySettingsKeyboard.test_01_sources_as_cpysrc_buttons) ... ok
test_02_empty_projects_still_has_back_row (test_p19_copy_settings.TestCopySettingsKeyboard.test_02_empty_projects_still_has_back_row) ... ok
test_03_unbound_resume_keyboard_offers_copy (test_p19_copy_settings.TestCopySettingsKeyboard.test_03_unbound_resume_keyboard_offers_copy) ... ok
test_01_copy_settings_callback_wired (test_p19_copy_settings.TestHandlersIntegration.test_01_copy_settings_callback_wired) ... ok
test_02_copy_back_callback_wired (test_p19_copy_settings.TestHandlersIntegration.test_02_copy_back_callback_wired) ... ok
test_03_cpysrc_callback_invokes_copy (test_p19_copy_settings.TestHandlersIntegration.test_03_cpysrc_callback_invokes_copy) ... ok
test_04_success_transitions_to_cont_prompt (test_p19_copy_settings.TestHandlersIntegration.test_04_success_transitions_to_cont_prompt)
بعد النسخ الناجح: الحالة تتحول لـ AWAITING_CONT_PROMPT بالمفتاح الجديد. ... ok
test_05_guard_requires_unbound_decision_state (test_p19_copy_settings.TestHandlersIntegration.test_05_guard_requires_unbound_decision_state) ... ok
test_01_banner_and_version (test_p19_copy_settings.TestP19VersionBump.test_01_banner_and_version) ... ok
test_02_scripts_reference_0130 (test_p19_copy_settings.TestP19VersionBump.test_02_scripts_reference_0130) ... ok
test_01_fresh_name_unchanged (test_p19_copy_settings.TestSequentialProjectName.test_01_fresh_name_unchanged) ... ok
test_02_hajj1_becomes_hajj2 (test_p19_copy_settings.TestSequentialProjectName.test_02_hajj1_becomes_hajj2) ... ok
test_03_next_after_highest (test_p19_copy_settings.TestSequentialProjectName.test_03_next_after_highest) ... ok
test_04_bare_root_used (test_p19_copy_settings.TestSequentialProjectName.test_04_bare_root_used) ... ok
test_05_unrelated_root_keeps_name (test_p19_copy_settings.TestSequentialProjectName.test_05_unrelated_root_keeps_name)
جذر غير مستخدم إطلاقاً ➔ الاسم يُعاد كما هو (لا ترقيم بلا داعٍ). ... ok
test_06_empty_name_fallback (test_p19_copy_settings.TestSequentialProjectName.test_06_empty_name_fallback) ... ok
test_07_whitespace_normalized (test_p19_copy_settings.TestSequentialProjectName.test_07_whitespace_normalized) ... ok
test_default_branch_first (test_p1_github_branches.TestGitHubBranchesP1.test_default_branch_first) ... ok
test_extract_from_raw_list (test_p1_github_branches.TestGitHubBranchesP1.test_extract_from_raw_list) ... ok
test_extract_from_wrapper_json (test_p1_github_branches.TestGitHubBranchesP1.test_extract_from_wrapper_json) ... ok
test_paginate_100_100_37_exactly_3_requests (test_p1_github_branches.TestGitHubBranchesP1.test_paginate_100_100_37_exactly_3_requests) ... ok
test_01_keywords_defined (test_p20_rest_only_data_retention.TestDataRetentionDetection.test_01_keywords_defined) ... ok
test_02_detects_basic_phrase (test_p20_rest_only_data_retention.TestDataRetentionDetection.test_02_detects_basic_phrase) ... ok
test_03_detects_turn_on_phrase (test_p20_rest_only_data_retention.TestDataRetentionDetection.test_03_detects_turn_on_phrase) ... ok
test_04_detects_inside_dict_response (test_p20_rest_only_data_retention.TestDataRetentionDetection.test_04_detects_inside_dict_response) ... ok
test_05_priority_over_session_expired (test_p20_rest_only_data_retention.TestDataRetentionDetection.test_05_priority_over_session_expired) ... ok
test_06_priority_over_credit_exhausted (test_p20_rest_only_data_retention.TestDataRetentionDetection.test_06_priority_over_credit_exhausted) ... ok
test_07_normal_completed_not_affected (test_p20_rest_only_data_retention.TestDataRetentionDetection.test_07_normal_completed_not_affected) ... ok
test_08_empty_still_empty (test_p20_rest_only_data_retention.TestDataRetentionDetection.test_08_empty_still_empty) ... ok
test_01_failover_handles_data_retention (test_p20_rest_only_data_retention.TestDataRetentionFailover.test_01_failover_handles_data_retention) ... ok
test_02_cooldown_applied_like_credit_exhausted (test_p20_rest_only_data_retention.TestDataRetentionFailover.test_02_cooldown_applied_like_credit_exhausted) ... ok
test_03_continues_to_next_account (test_p20_rest_only_data_retention.TestDataRetentionFailover.test_03_continues_to_next_account) ... ok
test_04_distinct_observer_notification (test_p20_rest_only_data_retention.TestDataRetentionFailover.test_04_distinct_observer_notification) ... ok
test_05_observer_label_registered (test_p20_rest_only_data_retention.TestDataRetentionFailover.test_05_observer_label_registered) ... ok
test_06_resends_same_last_message_not_resume_prompt (test_p20_rest_only_data_retention.TestDataRetentionFailover.test_06_resends_same_last_message_not_resume_prompt) ... ok
test_07_polling_loop_treats_as_terminal (test_p20_rest_only_data_retention.TestDataRetentionFailover.test_07_polling_loop_treats_as_terminal) ... ok
test_08_terminal_describer_has_distinct_message (test_p20_rest_only_data_retention.TestDataRetentionFailover.test_08_terminal_describer_has_distinct_message) ... ok
test_01_refactor_has_data_retention (test_p20_rest_only_data_retention.TestRefactorParityP20.test_01_refactor_has_data_retention) ... ok
test_02_refactor_clean_of_git_native (test_p20_rest_only_data_retention.TestRefactorParityP20.test_02_refactor_clean_of_git_native) ... ok
test_03_refactor_uploader_rest_only (test_p20_rest_only_data_retention.TestRefactorParityP20.test_03_refactor_uploader_rest_only) ... ok
test_01_git_native_uploader_removed (test_p20_rest_only_data_retention.TestRestOnlyUpload.test_01_git_native_uploader_removed) ... ok
test_02_ai_commit_message_removed (test_p20_rest_only_data_retention.TestRestOnlyUpload.test_02_ai_commit_message_removed) ... ok
test_03_no_git_binary_operations (test_p20_rest_only_data_retention.TestRestOnlyUpload.test_03_no_git_binary_operations) ... ok
test_04_default_uploader_uses_contents_api (test_p20_rest_only_data_retention.TestRestOnlyUpload.test_04_default_uploader_uses_contents_api) ... ok
test_05_uploader_skips_unchanged_via_blob_sha (test_p20_rest_only_data_retention.TestRestOnlyUpload.test_05_uploader_skips_unchanged_via_blob_sha) ... ok
test_06_uploader_requires_project_token (test_p20_rest_only_data_retention.TestRestOnlyUpload.test_06_uploader_requires_project_token) ... ok
test_07_blob_sha_pure_python (test_p20_rest_only_data_retention.TestRestOnlyUpload.test_07_blob_sha_pure_python) ... ok
test_08_p20_decision_documented_inline (test_p20_rest_only_data_retention.TestRestOnlyUpload.test_08_p20_decision_documented_inline) ... ok
test_09_p21_uploader_distinguishes_new_vs_modified (test_p20_rest_only_data_retention.TestRestOnlyUpload.test_09_p21_uploader_distinguishes_new_vs_modified)
🎯 [P21] عقد دقة التصنيف: ملف موجود على الريموت بمحتوى مختلف = modified، ... ok
test_10_p21_github_sync_consumes_modified (test_p20_rest_only_data_retention.TestRestOnlyUpload.test_10_p21_github_sync_consumes_modified)
github_sync يقرأ modified من نتيجة التنفيذ ويمررها لرسالة تليجرام ... ok
test_fable_models_is_gpt41_hardcoded (test_p2_model_routing.TestP2ModelRouting.test_fable_models_is_gpt41_hardcoded) ... ok
test_gpt56_sol_contract (test_p2_model_routing.TestP2ModelRouting.test_gpt56_sol_contract) ... ok
test_kimi_k3_contract (test_p2_model_routing.TestP2ModelRouting.test_kimi_k3_contract) ... ok
test_normalize_always_returns_str (test_p2_model_routing.TestP2ModelRouting.test_normalize_always_returns_str) ... /home/user/webapp/01.31_telegram_gen_bridge.py:109: DeprecationWarning: The 'warn' method is deprecated, use 'warning' instead
  log_func(log_msg)
ok
test_opus5_has_no_ai_chat_model (test_p2_model_routing.TestP2ModelRouting.test_opus5_has_no_ai_chat_model) ... ok
test_protected_is_noop_and_logs_warning (test_p2_model_routing.TestP2ModelRouting.test_protected_is_noop_and_logs_warning) ... ok
test_sonnet5_has_both_use_and_ai_chat (test_p2_model_routing.TestP2ModelRouting.test_sonnet5_has_both_use_and_ai_chat) ... ok
test_unknown_gets_models_key_only (test_p2_model_routing.TestP2ModelRouting.test_unknown_gets_models_key_only) ... ok
test_continue_chat_payload_identical (test_p3_regression.TestP3RegressionSnapshots.test_continue_chat_payload_identical)
التحقق من أن مفاتيح الـ Continue والـ Force لا تتأثر بالـ Adapter ... ok
test_engine_selection_unchanged (test_p3_regression.TestP3RegressionSnapshots.test_engine_selection_unchanged)
التحقق من أن دالة get_genspark_engine في البوت تجلب المحرك الأساسي بنجاح ... ok
test_fable_payload_matches_new_contract (test_p3_regression.TestP3RegressionSnapshots.test_fable_payload_matches_new_contract) ... ok
test_gpt55_payload_byte_identical (test_p3_regression.TestP3RegressionSnapshots.test_gpt55_payload_byte_identical)
التحقق من أن مسار gpt-5.5 الخاص لم يتغير منه أي مفتاح ... ok
test_gpt56_sol_matches_new_contract (test_p3_regression.TestP3RegressionSnapshots.test_gpt56_sol_matches_new_contract) ... ok
test_kimi_k3_matches_new_contract (test_p3_regression.TestP3RegressionSnapshots.test_kimi_k3_matches_new_contract) ... ok
test_new_chat_payload_identical (test_p3_regression.TestP3RegressionSnapshots.test_new_chat_payload_identical)
التحقق من أن الحقول الافتراضية للـ New Chat ثابتة ... ok
test_opus48_payload_byte_identical (test_p3_regression.TestP3RegressionSnapshots.test_opus48_payload_byte_identical)
التحقق من أن مسار claude-opus-4-8 الخاص لم يتغير ... ok
test_opus5_matches_new_contract (test_p3_regression.TestP3RegressionSnapshots.test_opus5_matches_new_contract) ... ok
test_selected_engine_imports_model_runtime (test_p3_regression.TestP3RegressionSnapshots.test_selected_engine_imports_model_runtime)
التحقق من أن المحرك الأساسي المحمل قادر على معالجة عقود الموديلات ... ok
test_sonnet5_payload_matches_new_contract (test_p3_regression.TestP3RegressionSnapshots.test_sonnet5_payload_matches_new_contract) ... ok
test_ultra_flag_untouched_by_adapter (test_p3_regression.TestP3RegressionSnapshots.test_ultra_flag_untouched_by_adapter)
التحقق من أن flag الـ Ultra mode يعمل كما هو دون مساس من الـ adapter ... ok
test_01_build_viewer_url_formatting (test_p7_live_preview.TestLivePreviewP7.test_01_build_viewer_url_formatting)
1. التحقق من بناء رابط العارض السحابي وترميز المعرف بدقة ... ok
test_02_build_live_preview_keyboard_running (test_p7_live_preview.TestLivePreviewP7.test_02_build_live_preview_keyboard_running)
2. التحقق من بناء زر المعاينة الحية أثناء البناء (status=running) ... ok
test_03_build_live_preview_keyboard_completed (test_p7_live_preview.TestLivePreviewP7.test_03_build_live_preview_keyboard_completed)
3. التحقق من بناء زر المشروع المكتمل عند انتهاء التوليد (status=completed) ... ok
test_04_no_dead_buttons_or_unsupported_style (test_p7_live_preview.TestLivePreviewP7.test_04_no_dead_buttons_or_unsupported_style)
4. التحقق من خلو الأزرار من أي callback_data ميت أو حقل style مسبب لأخطاء 400 ... ok
test_05_project_start_callback_dispatch (test_p7_live_preview.TestLivePreviewP7.test_05_project_start_callback_dispatch)
5. التحقق من استدعاء الـ callback وتمرير project_id فور وصول حدث project_start ... ok
test_06_project_start_callback_resilience (test_p7_live_preview.TestLivePreviewP7.test_06_project_start_callback_resilience)
6. التحقق من صمود واستمرار تدفق الـ SSE حتى لو ألقى الـ callback خطأ استثنائي ... ok
test_07_project_field_fallback_dispatch (test_p7_live_preview.TestLivePreviewP7.test_07_project_field_fallback_dispatch)
7. التحقق من استدعاء الـ callback كـ fallback عند وصول حدث project_field ... ok
test_08_ask_proxy_uses_stream_true (test_p7_live_preview.TestTrueSSEStreamingGuard.test_08_ask_proxy_uses_stream_true)
8. طلب ask_proxy يجب أن يُفتح بـ stream=True (بث حي، لا تحميل كامل) ... ok
test_09_sse_loop_uses_iter_lines_not_text (test_p7_live_preview.TestTrueSSEStreamingGuard.test_09_sse_loop_uses_iter_lines_not_text)
9. حلقة الـ SSE يجب أن تستهلك iter_lines() ويُمنع r.text.splitlines() نهائياً ... ok
test_10_callback_fires_before_stream_completion (test_p7_live_preview.TestTrueSSEStreamingGuard.test_10_callback_fires_before_stream_completion)
10. محاكاة بث حي: الـ callback يجب أن يُستدعى عند سطر project_start قبل وصول باقي البث ... ok
test_account_selection_claims (test_refactor_parity.TestBehaviorSpotChecks.test_account_selection_claims) ... ok
test_credit_checkpoint_gate_blocks_on_error (test_refactor_parity.TestBehaviorSpotChecks.test_credit_checkpoint_gate_blocks_on_error) ... ok
test_credit_checkpoint_gate_untracked (test_refactor_parity.TestBehaviorSpotChecks.test_credit_checkpoint_gate_untracked) ... ok
test_detect_response_status (test_refactor_parity.TestBehaviorSpotChecks.test_detect_response_status) ... ok
test_engine_loads_from_bridge_home (test_refactor_parity.TestBehaviorSpotChecks.test_engine_loads_from_bridge_home) ... ok
test_extract_project_id_uuid (test_refactor_parity.TestBehaviorSpotChecks.test_extract_project_id_uuid) ... ok
test_terminal_outcome (test_refactor_parity.TestBehaviorSpotChecks.test_terminal_outcome) ... ok
test_parts_reassemble_to_original (test_refactor_parity.TestByteParity.test_parts_reassemble_to_original) ... ok
test_facades_reexport_identical_objects (test_refactor_parity.TestFacadeParity.test_facades_reexport_identical_objects) ... ok
test_all_toplevel_defs_present (test_refactor_parity.TestSymbolParity.test_all_toplevel_defs_present) ... ok
test_critical_features_present (test_refactor_parity.TestSymbolParity.test_critical_features_present) ... ok

----------------------------------------------------------------------
Ran 221 tests in 0.202s

OK
```
