# 📜 سجل مخرجات تشغيل الاختبارات (TEST_EXECUTION_LOGS.md)

> **المسؤولية:** توثيق مخرجات التيرمينال الحقيقية، الـ Exit Codes، والأزمنة المقاسة  

---

## ⚡ آخر جلسة تشغيل ناجحة (Latest Execution Session)

* **التاريخ والوقت:** `2026-08-22 19:42:18 UTC`
* **الأمر المنفذ:** `python -m unittest discover tests -v`
* **الزمن المقاس:** `1.455 ثانية`
* **النتيجة العامة:** `Ran 678 tests — OK`
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
/home/user/webapp/01.33_telegram_gen_bridge.py:71: ResourceWarning: unclosed file <_io.TextIOWrapper name='/home/user/webapp/bridge_bot.log' mode='a' encoding='utf-8'>
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
/home/user/webapp/01.33_telegram_gen_bridge.py:71: ResourceWarning: unclosed file <_io.TextIOWrapper name='/home/user/webapp/bridge_bot.log' mode='a' encoding='utf-8'>
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
test_01_agents_md_exists_with_rule (test_p23_shared_paths.TestCentralRuleSignage.test_01_agents_md_exists_with_rule) ... ok
test_02_gemini_md_exists_with_rule (test_p23_shared_paths.TestCentralRuleSignage.test_02_gemini_md_exists_with_rule) ... ok
test_03_no_hardcoded_bot_token (test_p23_shared_paths.TestCentralRuleSignage.test_03_no_hardcoded_bot_token)
ممنوع الـ hardcode: لا يوجد توكن تيليجرام حرفي في المصدر ... ok
test_01_env_var_wins (test_p23_shared_paths.TestLoadBotTokenHierarchy.test_01_env_var_wins) ... ok
test_02_parent_token_file_used_when_local_missing (test_p23_shared_paths.TestLoadBotTokenHierarchy.test_02_parent_token_file_used_when_local_missing) ... ok
test_03_local_token_file_wins_over_parent (test_p23_shared_paths.TestLoadBotTokenHierarchy.test_03_local_token_file_wins_over_parent) ... ok
test_01_function_exists_and_returns_path (test_p23_shared_paths.TestResolveSharedPath.test_01_function_exists_and_returns_path) ... ok
test_02_local_file_wins (test_p23_shared_paths.TestResolveSharedPath.test_02_local_file_wins)
أولوية محلية: الملف الموجود جنب النسخة يُستخدم حتى لو الأب فيه نسخة ... ok
test_03_parent_fallback_when_local_missing (test_p23_shared_paths.TestResolveSharedPath.test_03_parent_fallback_when_local_missing)
لو الملف مش موجود محلياً يُلقط من الفولدر الأب تلقائياً ... ok
test_04_missing_everywhere_returns_local_for_creation (test_p23_shared_paths.TestResolveSharedPath.test_04_missing_everywhere_returns_local_for_creation)
لو غير موجود في الاثنين يرجع المسار المحلي (عشان الإنشاء الجديد) ... ok
test_05_works_for_directories_too (test_p23_shared_paths.TestResolveSharedPath.test_05_works_for_directories_too)
يدعم المجلدات (project_registry) وليس الملفات فقط ... ok
test_01_token_uses_resolver (test_p23_shared_paths.TestSharedPathWiring.test_01_token_uses_resolver) ... ok
test_02_registry_home_uses_resolver (test_p23_shared_paths.TestSharedPathWiring.test_02_registry_home_uses_resolver) ... ok
test_03_projects_tree_uses_resolver (test_p23_shared_paths.TestSharedPathWiring.test_03_projects_tree_uses_resolver) ... ok
test_04_accounts_candidates_use_resolver_first (test_p23_shared_paths.TestSharedPathWiring.test_04_accounts_candidates_use_resolver_first)
المرشح الأول في get_accounts_file_path هو المسار الموحد ... ok
test_05_registry_index_derived_from_home (test_p23_shared_paths.TestSharedPathWiring.test_05_registry_index_derived_from_home)
registry.json يظل مشتقاً من PROJECT_REGISTRY_HOME (فيرث المركزية) ... ok
test_06_resolver_defined_before_first_use (test_p23_shared_paths.TestSharedPathWiring.test_06_resolver_defined_before_first_use)
الدالة معرفة قبل أول استخدام (load_bot_token) ... ok
test_01_resolve_shared_path_exists (test_p24_qwen_commit_bridge.TestEngineSharedPath.test_01_resolve_shared_path_exists) ... ok
test_02_accounts_file_uses_resolver (test_p24_qwen_commit_bridge.TestEngineSharedPath.test_02_accounts_file_uses_resolver) ... ok
test_03_local_priority (test_p24_qwen_commit_bridge.TestEngineSharedPath.test_03_local_priority)
الملف المحلي موجود ➔ يفوز حتى لو الأب فيه نسخة (Zero Breaking) ... ok
test_04_parent_fallback (test_p24_qwen_commit_bridge.TestEngineSharedPath.test_04_parent_fallback)
لا محلي ➔ يلتقط من الفولدر الأب المركزي ... ok
test_05_local_for_creation (test_p24_qwen_commit_bridge.TestEngineSharedPath.test_05_local_for_creation)
غير موجود في الاثنين ➔ يرجع المحلي (للإنشاء) ... ok
test_01_all_accounts_race (test_p24_qwen_commit_bridge.TestOwnerDecisions.test_01_all_accounts_race)
قرار (A): 0 = كل الحسابات النشطة تتسابق ... ok
test_02_engine_timeout_unchanged (test_p24_qwen_commit_bridge.TestOwnerDecisions.test_02_engine_timeout_unchanged)
مهلة المحرك الأصلية 30ث/مرحلة كما هي — بدون اختراع أرقام ... ok
test_03_fallback_msg_constant (test_p24_qwen_commit_bridge.TestOwnerDecisions.test_03_fallback_msg_constant) ... ok
test_01_success_returns_commit (test_p24_qwen_commit_bridge.TestQwenCommitPrefix.test_01_success_returns_commit) ... ok
test_02_none_result_falls_back_empty (test_p24_qwen_commit_bridge.TestQwenCommitPrefix.test_02_none_result_falls_back_empty) ... ok
test_03_exception_is_isolated (test_p24_qwen_commit_bridge.TestQwenCommitPrefix.test_03_exception_is_isolated)
أي Exception من كوين ➔ prefix فارغ — الرفع لا ينكسر أبداً ... ok
test_04_empty_job_skips_engine (test_p24_qwen_commit_bridge.TestQwenCommitPrefix.test_04_empty_job_skips_engine)
job بلا ملفات ➔ كوين لا يُستدعى إطلاقاً (توفير الوقت والحسابات) ... ok
test_05_prefix_capped_150 (test_p24_qwen_commit_bridge.TestQwenCommitPrefix.test_05_prefix_capped_150) ... ok
test_01_prefix_computed_once_before_put_loop (test_p24_qwen_commit_bridge.TestUploaderMessageContract.test_01_prefix_computed_once_before_put_loop) ... ok
test_02_sync_message_ai_prefix_with_verbatim_fallback (test_p24_qwen_commit_bridge.TestUploaderMessageContract.test_02_sync_message_ai_prefix_with_verbatim_fallback) ... ok
test_03_delete_message_ai_prefix_with_verbatim_fallback (test_p24_qwen_commit_bridge.TestUploaderMessageContract.test_03_delete_message_ai_prefix_with_verbatim_fallback) ... ok
test_04_helper_is_fully_isolated (test_p24_qwen_commit_bridge.TestUploaderMessageContract.test_04_helper_is_fully_isolated)
الـ helper كله داخل try/except Exception — كوين لا يكسر الرفع ... ok
test_01_token_short_enough_for_callback_data (test_p25_interactive_cancel.TestCancellationManager.test_01_token_short_enough_for_callback_data) ... ok
test_02_register_returns_event (test_p25_interactive_cancel.TestCancellationManager.test_02_register_returns_event) ... ok
test_03_register_idempotent_same_event (test_p25_interactive_cancel.TestCancellationManager.test_03_register_idempotent_same_event) ... ok
test_04_register_empty_token_returns_none (test_p25_interactive_cancel.TestCancellationManager.test_04_register_empty_token_returns_none) ... ok
test_05_get_entry_metadata (test_p25_interactive_cancel.TestCancellationManager.test_05_get_entry_metadata) ... ok
test_06_get_entry_unknown_token_returns_none (test_p25_interactive_cancel.TestCancellationManager.test_06_get_entry_unknown_token_returns_none) ... ok
test_07_update_entry_live_pid (test_p25_interactive_cancel.TestCancellationManager.test_07_update_entry_live_pid) ... ok
test_08_update_unknown_token_returns_false (test_p25_interactive_cancel.TestCancellationManager.test_08_update_unknown_token_returns_false) ... ok
test_09_trigger_sets_event (test_p25_interactive_cancel.TestCancellationManager.test_09_trigger_sets_event) ... ok
test_10_trigger_unknown_token_returns_false (test_p25_interactive_cancel.TestCancellationManager.test_10_trigger_unknown_token_returns_false) ... ok
test_11_unregister_zero_leaks (test_p25_interactive_cancel.TestCancellationManager.test_11_unregister_zero_leaks) ... ok
test_12_cancelled_status_constant (test_p25_interactive_cancel.TestCancellationManager.test_12_cancelled_status_constant) ... ok
test_01_engine_reads_cancel_event_from_cfg (test_p25_interactive_cancel.TestEngineStreamAbortContract.test_01_engine_reads_cancel_event_from_cfg) ... ok
test_02_engine_checks_event_inside_iter_lines (test_p25_interactive_cancel.TestEngineStreamAbortContract.test_02_engine_checks_event_inside_iter_lines) ... ok
test_03_engine_returns_user_cancelled_marker (test_p25_interactive_cancel.TestEngineStreamAbortContract.test_03_engine_returns_user_cancelled_marker) ... ok
test_04_marker_priority_before_credit_classification (test_p25_interactive_cancel.TestEngineStreamAbortContract.test_04_marker_priority_before_credit_classification) ... ok
test_05_socket_closed_after_break (test_p25_interactive_cancel.TestEngineStreamAbortContract.test_05_socket_closed_after_break) ... ok
test_01_end_to_end_cancel_wakes_waiter_instantly (test_p25_interactive_cancel.TestFullCancelFlowSimulation.test_01_end_to_end_cancel_wakes_waiter_instantly) ... ok
test_02_abort_leaves_event_unset_and_task_continues (test_p25_interactive_cancel.TestFullCancelFlowSimulation.test_02_abort_leaves_event_unset_and_task_continues) ... ok
test_01_backward_compat_no_token_single_row (test_p25_interactive_cancel.TestLivePreviewKeyboard.test_01_backward_compat_no_token_single_row) ... ok
test_02_running_with_token_adds_danger_cancel_row (test_p25_interactive_cancel.TestLivePreviewKeyboard.test_02_running_with_token_adds_danger_cancel_row) ... ok
test_03_confirm_cancel_keyboard_two_step_safety (test_p25_interactive_cancel.TestLivePreviewKeyboard.test_03_confirm_cancel_keyboard_two_step_safety) ... ok
test_04_completed_keyboard_unchanged (test_p25_interactive_cancel.TestLivePreviewKeyboard.test_04_completed_keyboard_unchanged) ... ok
test_05_callback_data_within_telegram_64_bytes (test_p25_interactive_cancel.TestLivePreviewKeyboard.test_05_callback_data_within_telegram_64_bytes) ... ok
test_01_worker_registers_token_before_work (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_01_worker_registers_token_before_work) ... ok
test_02_worker_injects_event_into_cfg (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_02_worker_injects_event_into_cfg) ... ok
test_03_worker_finally_unregisters_zero_leaks (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_03_worker_finally_unregisters_zero_leaks) ... ok
test_04_failover_returns_cancelled_without_penalty (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_04_failover_returns_cancelled_without_penalty) ... ok
test_05_cancelled_check_before_low_balance (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_05_cancelled_check_before_low_balance) ... ok
test_06_precheck_before_attempt_starts (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_06_precheck_before_attempt_starts) ... ok
test_07_engine_marker_ends_task_without_retry (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_07_engine_marker_ends_task_without_retry) ... ok
test_08_polling_loop_checks_cancel_first (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_08_polling_loop_checks_cancel_first) ... ok
test_09_polling_sleep_is_interruptible_wait (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_09_polling_sleep_is_interruptible_wait) ... ok
test_10_callback_handler_three_actions_isolated (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_10_callback_handler_three_actions_isolated) ... ok
test_11_callback_exec_triggers_and_edits_message (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_11_callback_exec_triggers_and_edits_message) ... ok
test_12_callback_abort_restores_running_keyboard (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_12_callback_abort_restores_running_keyboard) ... ok
test_13_expired_token_cleans_buttons_quietly (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_13_expired_token_cleans_buttons_quietly) ... ok
test_14_worker_handles_cancelled_terminal_message (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_14_worker_handles_cancelled_terminal_message) ... ok
test_15_live_preview_card_carries_cancel_button (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_15_live_preview_card_carries_cancel_button) ... ok
test_16_bridge_config_declares_cancel_fields (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_16_bridge_config_declares_cancel_fields) ... ok
test_17_cancel_terminal_shows_full_dashboard_keyboard (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_17_cancel_terminal_shows_full_dashboard_keyboard) ... ok
test_18_cancel_terminal_has_no_orphan_single_button (test_p25_interactive_cancel.TestWorkerIntegrationContracts.test_18_cancel_terminal_has_no_orphan_single_button) ... ok
test_01_full_deletion_happy_path (test_p26_project_deletion.TestAtomicDeletion.test_01_full_deletion_happy_path) ... ok
test_02_identity_record_gone_after_delete (test_p26_project_deletion.TestAtomicDeletion.test_02_identity_record_gone_after_delete) ... ok
test_03_active_build_blocks_deletion (test_p26_project_deletion.TestAtomicDeletion.test_03_active_build_blocks_deletion) ... ok
test_04_deletion_allowed_after_build_finishes (test_p26_project_deletion.TestAtomicDeletion.test_04_deletion_allowed_after_build_finishes) ... ok
test_05_missing_project_reports_not_found (test_p26_project_deletion.TestAtomicDeletion.test_05_missing_project_reports_not_found) ... ok
test_06_empty_key_rejected (test_p26_project_deletion.TestAtomicDeletion.test_06_empty_key_rejected) ... ok
test_07_disk_only_project_still_deleted (test_p26_project_deletion.TestAtomicDeletion.test_07_disk_only_project_still_deleted) ... ok
test_08_all_pid_aliases_purged (test_p26_project_deletion.TestAtomicDeletion.test_08_all_pid_aliases_purged) ... ok
test_09_no_tree_file_is_safe (test_p26_project_deletion.TestAtomicDeletion.test_09_no_tree_file_is_safe) ... ok
test_10_project_without_pid_skips_tree_safely (test_p26_project_deletion.TestAtomicDeletion.test_10_project_without_pid_skips_tree_safely) ... ok
test_01_details_keyboard_has_delete_button (test_p26_project_deletion.TestDeleteKeyboards.test_01_details_keyboard_has_delete_button) ... ok
test_02_delete_button_is_danger_and_own_row (test_p26_project_deletion.TestDeleteKeyboards.test_02_delete_button_is_danger_and_own_row) ... ok
test_03_p25_cancel_button_still_present (test_p26_project_deletion.TestDeleteKeyboards.test_03_p25_cancel_button_still_present) ... ok
test_04_confirm_keyboard_two_step_safety (test_p26_project_deletion.TestDeleteKeyboards.test_04_confirm_keyboard_two_step_safety) ... ok
test_05_callback_data_within_telegram_limit (test_p26_project_deletion.TestDeleteKeyboards.test_05_callback_data_within_telegram_limit) ... ok
test_06_deleted_keyboard_has_next_actions (test_p26_project_deletion.TestDeleteKeyboards.test_06_deleted_keyboard_has_next_actions) ... ok
test_07_confirm_text_shows_name_and_key (test_p26_project_deletion.TestDeleteKeyboards.test_07_confirm_text_shows_name_and_key) ... ok
test_01_sibling_untouched_everywhere (test_p26_project_deletion.TestNeighborSafety.test_01_sibling_untouched_everywhere) ... ok
test_02_registry_index_file_survives_deletion (test_p26_project_deletion.TestNeighborSafety.test_02_registry_index_file_survives_deletion) ... ok
test_03_delete_is_idempotent (test_p26_project_deletion.TestNeighborSafety.test_03_delete_is_idempotent) ... ok
test_01_inactive_project_not_flagged (test_p26_project_deletion.TestRunningProtection.test_01_inactive_project_not_flagged) ... ok
test_02_active_build_is_flagged (test_p26_project_deletion.TestRunningProtection.test_02_active_build_is_flagged) ... ok
test_03_cancelled_build_not_flagged (test_p26_project_deletion.TestRunningProtection.test_03_cancelled_build_not_flagged) ... ok
test_04_unregistered_build_not_flagged (test_p26_project_deletion.TestRunningProtection.test_04_unregistered_build_not_flagged) ... ok
test_05_empty_key_never_flagged (test_p26_project_deletion.TestRunningProtection.test_05_empty_key_never_flagged) ... ok
test_01_pdel_block_isolated_and_early (test_p26_project_deletion.TestSourceContracts.test_01_pdel_block_isolated_and_early) ... ok
test_02_pdel_block_before_main_chain (test_p26_project_deletion.TestSourceContracts.test_02_pdel_block_before_main_chain) ... ok
test_03_confirmation_is_in_place_edit (test_p26_project_deletion.TestSourceContracts.test_03_confirmation_is_in_place_edit) ... ok
test_04_exec_calls_atomic_deletion (test_p26_project_deletion.TestSourceContracts.test_04_exec_calls_atomic_deletion) ... ok
test_05_abort_restores_details_screen (test_p26_project_deletion.TestSourceContracts.test_05_abort_restores_details_screen) ... ok
test_06_index_cleanup_under_registry_lock (test_p26_project_deletion.TestSourceContracts.test_06_index_cleanup_under_registry_lock) ... ok
test_07_project_key_sanitized_in_handler (test_p26_project_deletion.TestSourceContracts.test_07_project_key_sanitized_in_handler) ... ok
test_08_danger_style_is_allowed_value (test_p26_project_deletion.TestSourceContracts.test_08_danger_style_is_allowed_value) ... ok
test_100_projects_five_pages (test_p27_projects_pagination.TestComputePageBounds.test_100_projects_five_pages) ... ok
test_21_projects_two_pages (test_p27_projects_pagination.TestComputePageBounds.test_21_projects_two_pages)
21 مشروعاً = صفحتان، الثانية تبدأ من index 20 ... ok
test_47_projects_three_pages (test_p27_projects_pagination.TestComputePageBounds.test_47_projects_three_pages) ... ok
test_exactly_one_page_boundary (test_p27_projects_pagination.TestComputePageBounds.test_exactly_one_page_boundary)
20 مشروعاً = صفحة واحدة بالضبط ... ok
test_non_numeric_page_falls_back_to_first (test_p27_projects_pagination.TestComputePageBounds.test_non_numeric_page_falls_back_to_first)
توكن تالف (نص/None) ➔ الصفحة 1 بلا استثناء ... ok
test_numeric_string_page_accepted (test_p27_projects_pagination.TestComputePageBounds.test_numeric_string_page_accepted)
التوكن يصل من الـ callback كنص رقمي — يُقبل ... ok
test_page_below_one_clamped (test_p27_projects_pagination.TestComputePageBounds.test_page_below_one_clamped)
صفحة 0 أو سالبة ➔ قصّ للصفحة 1 ... ok
test_page_beyond_last_clamped (test_p27_projects_pagination.TestComputePageBounds.test_page_beyond_last_clamped)
صفحة أكبر من الأخيرة ➔ قصّ للصفحة الأخيرة (صفر Crash) ... ok
test_zero_projects_single_page (test_p27_projects_pagination.TestComputePageBounds.test_zero_projects_single_page) ... ok
test_dashboard_has_no_pagination_buttons (test_p27_projects_pagination.TestDashboardRegression.test_dashboard_has_no_pagination_buttons)
اللوحة الرئيسية لا تحمل أي أزرار تقليب — التصفح شاشة مستقلة ... ok
test_dashboard_keeps_list_projects_button (test_p27_projects_pagination.TestDashboardRegression.test_dashboard_keeps_list_projects_button)
زر «📁 مشاريعي» ما زال في اللوحة الرئيسية ويشير لـ cmd:list_projects ... ok
test_dashboard_still_previews_latest_3_only (test_p27_projects_pagination.TestDashboardRegression.test_dashboard_still_previews_latest_3_only)
قرار المالك: اللوحة الرئيسية تبقى معاينة سريعة بأحدث 3 مشاريع ... ok
test_constant_defined_once_in_source (test_p27_projects_pagination.TestPaginationConstant.test_constant_defined_once_in_source)
الثابت المركزي يُعرَّف مرة واحدة فقط (تغييره لاحقاً = سطر واحد) ... ok
test_projects_per_page_is_20 (test_p27_projects_pagination.TestPaginationConstant.test_projects_per_page_is_20)
قرار المالك الصريح: 20 مشروعاً في الصفحة ... ok
test_counter_button_shows_position (test_p27_projects_pagination.TestProjectsPageKeyboard.test_counter_button_shows_position)
زر العداد يعرض «📄 2 / 3» ويحمل plist:noop ... ok
test_empty_registry_shows_actions_only (test_p27_projects_pagination.TestProjectsPageKeyboard.test_empty_registry_shows_actions_only)
0 مشاريع: لا صفوف مشاريع ولا تنقل — فقط [مشروع جديد][رجوع] ... ok
test_first_page_has_next_but_no_prev (test_p27_projects_pagination.TestProjectsPageKeyboard.test_first_page_has_next_but_no_prev)
الصفحة الأولى: زر التالية موجود، زر السابقة محذوف ... ok
test_full_page_of_20_projects (test_p27_projects_pagination.TestProjectsPageKeyboard.test_full_page_of_20_projects)
20 مشروعاً بالضبط = 20 صفاً بلا تنقل ... ok
test_last_page_has_prev_but_no_next (test_p27_projects_pagination.TestProjectsPageKeyboard.test_last_page_has_prev_but_no_next)
الصفحة الأخيرة: زر السابقة موجود، زر التالية محذوف ... ok
test_middle_page_has_both_nav_buttons (test_p27_projects_pagination.TestProjectsPageKeyboard.test_middle_page_has_both_nav_buttons)
صفحة وسطى (47 مشروعاً ➔ صفحة 2 من 3): سابقة وتالية معاً + عداد ... ok
test_new_project_button_always_present (test_p27_projects_pagination.TestProjectsPageKeyboard.test_new_project_button_always_present)
صف الإجراءات [🚀 مشروع جديد][🏠 رجوع] حاضر في كل الحالات ... ok
test_other_chat_projects_excluded (test_p27_projects_pagination.TestProjectsPageKeyboard.test_other_chat_projects_excluded)
مشاريع محادثة أخرى لا تظهر أبداً (عزل chat_id) ... ok
test_out_of_bounds_page_renders_last_page (test_p27_projects_pagination.TestProjectsPageKeyboard.test_out_of_bounds_page_renders_last_page)
صفحة 999 على 21 مشروعاً ➔ تُعرض الصفحة الأخيرة بلا Crash ... ok
test_project_rows_reuse_existing_contracts (test_p27_projects_pagination.TestProjectsPageKeyboard.test_project_rows_reuse_existing_contracts)
صفوف المشاريع تستخدم نفس عقود proj:/pview: القائمة (صفر تغيير على تدفق الاختيار) ... ok
test_projects_ordered_newest_first (test_p27_projects_pagination.TestProjectsPageKeyboard.test_projects_ordered_newest_first)
أحدث مشروع (آخر upsert) يظهر أولاً في الصفحة الأولى ... ok
test_single_page_has_no_nav_row (test_p27_projects_pagination.TestProjectsPageKeyboard.test_single_page_has_no_nav_row)
≤20 مشروعاً = صفحة واحدة بلا أي أزرار تقليب ... ok
test_empty_registry_message (test_p27_projects_pagination.TestProjectsPageText.test_empty_registry_message) ... ok
test_last_partial_page_range (test_p27_projects_pagination.TestProjectsPageText.test_last_partial_page_range)
الصفحة الأخيرة الجزئية: 47 مشروعاً ➔ صفحة 3 تعرض 41–47 ... ok
test_out_of_bounds_page_text_clamped (test_p27_projects_pagination.TestProjectsPageText.test_out_of_bounds_page_text_clamped) ... ok
test_text_shows_total_and_position (test_p27_projects_pagination.TestProjectsPageText.test_text_shows_total_and_position) ... ok
test_dashboard_preview_limit_still_3 (test_p27_projects_pagination.TestSourceContracts.test_dashboard_preview_limit_still_3)
المعاينة السريعة في اللوحة تحتفظ حرفياً بـ limit=3 ... ok
test_dead_button_fixed_handler_exists (test_p27_projects_pagination.TestSourceContracts.test_dead_button_fixed_handler_exists)
🔴 إصلاح الزر الميت: فرع cmd:list_projects موجود الآن في الموزّع ... ok
test_existing_proj_handler_untouched (test_p27_projects_pagination.TestSourceContracts.test_existing_proj_handler_untouched)
معالج proj: القائم (الاستئناف المباشر) لم يُمس ... ok
test_list_projects_handler_uses_pagination_screen (test_p27_projects_pagination.TestSourceContracts.test_list_projects_handler_uses_pagination_screen)
معالج cmd:list_projects يفتح شاشة التصفح (النص + الكيبورد الجديدان) ... ok
test_noop_handler_exists (test_p27_projects_pagination.TestSourceContracts.test_noop_handler_exists) ... ok
test_page_flip_edits_same_message_in_place (test_p27_projects_pagination.TestSourceContracts.test_page_flip_edits_same_message_in_place)
التقليب يعدّل نفس الرسالة (edit_telegram_message_text) — صفر Spam ... ok
test_page_flip_handler_exists (test_p27_projects_pagination.TestSourceContracts.test_page_flip_handler_exists) ... ok
test_page_flip_has_send_fallback (test_p27_projects_pagination.TestSourceContracts.test_page_flip_has_send_fallback)
لو غاب message_id (حالة نادرة) ➔ fallback بإرسال رسالة جديدة بلا Crash ... ok
test_pagination_keyboard_defined_before_dispatcher (test_p27_projects_pagination.TestSourceContracts.test_pagination_keyboard_defined_before_dispatcher)
الدوال تُعرَّف قبل الموزّع (سلامة ترتيب single-file) ... ok
test_allowed_extensions_exact_set (test_p28_document_input.TestP28Constants.test_allowed_extensions_exact_set) ... ok
test_allowed_extensions_is_frozenset (test_p28_document_input.TestP28Constants.test_allowed_extensions_is_frozenset) ... ok
test_extensions_are_lowercase_with_dot (test_p28_document_input.TestP28Constants.test_extensions_are_lowercase_with_dot) ... ok
test_max_size_is_exactly_5mb (test_p28_document_input.TestP28Constants.test_max_size_is_exactly_5mb) ... ok
test_caption_merged_before_content (test_p28_document_input.TestP28DispatcherAccepted.test_caption_merged_before_content) ... ok
test_document_inside_awaiting_new_prompt_feeds_wizard (test_p28_document_input.TestP28DispatcherAccepted.test_document_inside_awaiting_new_prompt_feeds_wizard) ... ok
test_markdown_extension_accepted (test_p28_document_input.TestP28DispatcherAccepted.test_markdown_extension_accepted) ... ok
test_md_file_accepted (test_p28_document_input.TestP28DispatcherAccepted.test_md_file_accepted) ... ok
test_no_caption_content_only_stripped (test_p28_document_input.TestP28DispatcherAccepted.test_no_caption_content_only_stripped) ... ok
test_txt_file_schedules_task_with_content (test_p28_document_input.TestP28DispatcherAccepted.test_txt_file_schedules_task_with_content) ... ok
test_uppercase_extension_accepted (test_p28_document_input.TestP28DispatcherAccepted.test_uppercase_extension_accepted) ... ok
test_download_failure_sends_friendly_error (test_p28_document_input.TestP28DispatcherRejected.test_download_failure_sends_friendly_error) ... ok
test_empty_content_sends_friendly_error (test_p28_document_input.TestP28DispatcherRejected.test_empty_content_sends_friendly_error) ... ok
test_exactly_5mb_accepted (test_p28_document_input.TestP28DispatcherRejected.test_exactly_5mb_accepted) ... ok
test_missing_file_name_rejected (test_p28_document_input.TestP28DispatcherRejected.test_missing_file_name_rejected) ... ok
test_oversize_rejected_no_download (test_p28_document_input.TestP28DispatcherRejected.test_oversize_rejected_no_download) ... ok
test_pdf_rejected_no_download (test_p28_document_input.TestP28DispatcherRejected.test_pdf_rejected_no_download) ... ok
test_zip_rejected (test_p28_document_input.TestP28DispatcherRejected.test_zip_rejected) ... ok
test_download_http_404_returns_none (test_p28_document_input.TestP28DownloadFunction.test_download_http_404_returns_none) ... ok
test_empty_bot_token_returns_none_without_network (test_p28_document_input.TestP28DownloadFunction.test_empty_bot_token_returns_none_without_network) ... ok
test_getfile_http_500_returns_none (test_p28_document_input.TestP28DownloadFunction.test_getfile_http_500_returns_none) ... ok
test_getfile_ok_false_returns_none (test_p28_document_input.TestP28DownloadFunction.test_getfile_ok_false_returns_none) ... ok
test_getfile_passes_file_id_param (test_p28_document_input.TestP28DownloadFunction.test_getfile_passes_file_id_param) ... ok
test_invalid_utf8_bytes_replaced_not_crash (test_p28_document_input.TestP28DownloadFunction.test_invalid_utf8_bytes_replaced_not_crash) ... ok
test_missing_file_path_returns_none (test_p28_document_input.TestP28DownloadFunction.test_missing_file_path_returns_none) ... ok
test_network_exception_returns_none_no_crash (test_p28_document_input.TestP28DownloadFunction.test_network_exception_returns_none_no_crash) ... ok
test_success_returns_utf8_text (test_p28_document_input.TestP28DownloadFunction.test_success_returns_utf8_text) ... ok
test_download_uses_errors_replace (test_p28_document_input.TestP28SourceContracts.test_download_uses_errors_replace) ... ok
test_extension_normalized_lowercase (test_p28_document_input.TestP28SourceContracts.test_extension_normalized_lowercase) ... ok
test_guard_condition_document_and_not_text (test_p28_document_input.TestP28SourceContracts.test_guard_condition_document_and_not_text) ... ok
test_helper_lives_in_p04_next_to_send_document (test_p28_document_input.TestP28SourceContracts.test_helper_lives_in_p04_next_to_send_document) ... ok
test_ingestion_block_after_permission_gate (test_p28_document_input.TestP28SourceContracts.test_ingestion_block_after_permission_gate) ... ok
test_ingestion_block_before_start_command (test_p28_document_input.TestP28SourceContracts.test_ingestion_block_before_start_command) ... ok
test_document_from_disallowed_chat_blocked_before_download (test_p28_document_input.TestP28ZeroRegression.test_document_from_disallowed_chat_blocked_before_download) ... ok
test_message_with_both_text_and_document_treated_as_text (test_p28_document_input.TestP28ZeroRegression.test_message_with_both_text_and_document_treated_as_text) ... ok
test_plain_text_message_never_touches_document_path (test_p28_document_input.TestP28ZeroRegression.test_plain_text_message_never_touches_document_path) ... ok
test_start_command_still_shows_dashboard (test_p28_document_input.TestP28ZeroRegression.test_start_command_still_shows_dashboard) ... ok
test_bridgeconfig_instances_are_isolated (test_p29_account_observability.TestAccountJourneyRecording.test_bridgeconfig_instances_are_isolated) ... ok
test_consecutive_duplicates_collapse (test_p29_account_observability.TestAccountJourneyRecording.test_consecutive_duplicates_collapse) ... ok
test_empty_or_blank_email_never_recorded (test_p29_account_observability.TestAccountJourneyRecording.test_empty_or_blank_email_never_recorded) ... ok
test_missing_attribute_initialized_as_list (test_p29_account_observability.TestAccountJourneyRecording.test_missing_attribute_initialized_as_list) ... ok
test_none_cfg_is_safe (test_p29_account_observability.TestAccountJourneyRecording.test_none_cfg_is_safe) ... ok
test_records_in_claim_order (test_p29_account_observability.TestAccountJourneyRecording.test_records_in_claim_order) ... ok
test_return_to_previous_account_is_kept (test_p29_account_observability.TestAccountJourneyRecording.test_return_to_previous_account_is_kept) ... ok
test_blank_entries_filtered_before_count (test_p29_account_observability.TestFinalJourneyLine.test_blank_entries_filtered_before_count) ... ok
test_empty_journey_gives_empty_line (test_p29_account_observability.TestFinalJourneyLine.test_empty_journey_gives_empty_line) ... ok
test_journey_emails_html_escaped (test_p29_account_observability.TestFinalJourneyLine.test_journey_emails_html_escaped) ... ok
test_multi_account_journey_rendered_with_arrows (test_p29_account_observability.TestFinalJourneyLine.test_multi_account_journey_rendered_with_arrows) ... ok
test_single_account_gives_empty_line (test_p29_account_observability.TestFinalJourneyLine.test_single_account_gives_empty_line) ... ok
test_event_carries_journey_snapshot (test_p29_account_observability.TestImmutableEventSnapshots.test_event_carries_journey_snapshot) ... ok
test_event_without_cfg_has_empty_journey (test_p29_account_observability.TestImmutableEventSnapshots.test_event_without_cfg_has_empty_journey) ... ok
test_old_event_snapshot_never_mutates (test_p29_account_observability.TestImmutableEventSnapshots.test_old_event_snapshot_never_mutates) ... ok
test_active_account_line_appears_after_claim (test_p29_account_observability.TestLiveRendererActiveAccount.test_active_account_line_appears_after_claim) ... ok
test_active_account_updates_on_new_claim (test_p29_account_observability.TestLiveRendererActiveAccount.test_active_account_updates_on_new_claim) ... ok
test_handoff_then_claim_produces_switch_line (test_p29_account_observability.TestLiveRendererActiveAccount.test_handoff_then_claim_produces_switch_line) ... ok
test_handoff_then_same_account_no_switch_line (test_p29_account_observability.TestLiveRendererActiveAccount.test_handoff_then_same_account_no_switch_line) ... ok
test_no_active_line_before_any_claim (test_p29_account_observability.TestLiveRendererActiveAccount.test_no_active_line_before_any_claim) ... ok
test_no_switch_line_without_handoff (test_p29_account_observability.TestLiveRendererActiveAccount.test_no_switch_line_without_handoff) ... ok
test_renderer_email_html_escaped (test_p29_account_observability.TestLiveRendererActiveAccount.test_renderer_email_html_escaped) ... ok
test_bridgeconfig_declares_journey_with_default_factory (test_p29_account_observability.TestSourceContracts.test_bridgeconfig_declares_journey_with_default_factory) ... ok
test_event_snapshot_contract_in_notify (test_p29_account_observability.TestSourceContracts.test_event_snapshot_contract_in_notify) ... ok
test_final_message_uses_journey_block (test_p29_account_observability.TestSourceContracts.test_final_message_uses_journey_block) ... ok
test_journey_recorded_at_claim_moment (test_p29_account_observability.TestSourceContracts.test_journey_recorded_at_claim_moment) ... ok
test_journey_reset_at_failover_start (test_p29_account_observability.TestSourceContracts.test_journey_reset_at_failover_start) ... ok
test_start_message_has_no_email_line (test_p29_account_observability.TestSourceContracts.test_start_message_has_no_email_line) ... ok
test_fable_models_is_gpt41_hardcoded (test_p2_model_routing.TestP2ModelRouting.test_fable_models_is_gpt41_hardcoded) ... ok
test_gpt56_sol_contract (test_p2_model_routing.TestP2ModelRouting.test_gpt56_sol_contract) ... ok
test_kimi_k3_contract (test_p2_model_routing.TestP2ModelRouting.test_kimi_k3_contract) ... ok
test_normalize_always_returns_str (test_p2_model_routing.TestP2ModelRouting.test_normalize_always_returns_str) ... ok
test_opus5_has_no_ai_chat_model (test_p2_model_routing.TestP2ModelRouting.test_opus5_has_no_ai_chat_model) ... ok
test_protected_is_noop_and_logs_warning (test_p2_model_routing.TestP2ModelRouting.test_protected_is_noop_and_logs_warning) ... ok
test_sonnet5_has_both_use_and_ai_chat (test_p2_model_routing.TestP2ModelRouting.test_sonnet5_has_both_use_and_ai_chat) ... ok
test_unknown_gets_models_key_only (test_p2_model_routing.TestP2ModelRouting.test_unknown_gets_models_key_only) ... ok
test_empty_input (test_p30_account_timing.TestAggregation.test_empty_input) ... ok
test_garbage_entries_ignored (test_p30_account_timing.TestAggregation.test_garbage_entries_ignored) ... ok
test_multi_account_order_preserved (test_p30_account_timing.TestAggregation.test_multi_account_order_preserved) ... ok
test_open_span_counted_best_effort (test_p30_account_timing.TestAggregation.test_open_span_counted_best_effort) ... ok
test_returning_account_sums_both_spans (test_p30_account_timing.TestAggregation.test_returning_account_sums_both_spans)
SCENARIO C: A→B→A — مدخل واحد لـ A بمجموع فترتيه. ... ok
test_float_seconds_truncated (test_p30_account_timing.TestArabicDurationFormatter.test_float_seconds_truncated) ... ok
test_hours_and_minutes (test_p30_account_timing.TestArabicDurationFormatter.test_hours_and_minutes) ... ok
test_minutes_and_seconds (test_p30_account_timing.TestArabicDurationFormatter.test_minutes_and_seconds) ... ok
test_seconds_only (test_p30_account_timing.TestArabicDurationFormatter.test_seconds_only) ... ok
test_zero_and_invalid_inputs_no_crash (test_p30_account_timing.TestArabicDurationFormatter.test_zero_and_invalid_inputs_no_crash) ... ok
test_accounts_total_is_sum_of_spans (test_p30_account_timing.TestFinalMessageBlock.test_accounts_total_is_sum_of_spans) ... ok
test_empty_spans_returns_empty_string (test_p30_account_timing.TestFinalMessageBlock.test_empty_spans_returns_empty_string) ... ok
test_finisher_is_last_span_account (test_p30_account_timing.TestFinalMessageBlock.test_finisher_is_last_span_account)
SCENARIO B: «(المُنجِز)» لآخر حساب في الرحلة فقط. ... ok
test_full_email_no_masking (test_p30_account_timing.TestFinalMessageBlock.test_full_email_no_masking) ... ok
test_html_escaping_of_email (test_p30_account_timing.TestFinalMessageBlock.test_html_escaping_of_email) ... ok
test_resume_counter_independent_of_accounts_count (test_p30_account_timing.TestFinalMessageBlock.test_resume_counter_independent_of_accounts_count)
SCENARIO H: Resume ≠ Accounts−1 — 3 حسابات مع استئناف واحد فقط. ... ok
test_returning_account_finisher_and_multiplier (test_p30_account_timing.TestFinalMessageBlock.test_returning_account_finisher_and_multiplier)
SCENARIO C: A→B→A — A هو المُنجِز ويحمل ×2. ... ok
test_single_account_block_always_shown (test_p30_account_timing.TestFinalMessageBlock.test_single_account_block_always_shown)
SCENARIO A: الكتلة تظهر حتى بحساب واحد (عكس سطر P29 الشرطي). ... ok
test_bridgeconfig_default_spans_isolated_per_instance (test_p30_account_timing.TestIsolation.test_bridgeconfig_default_spans_isolated_per_instance) ... ok
test_open_initializes_missing_spans_list (test_p30_account_timing.TestIsolation.test_open_initializes_missing_spans_list) ... ok
test_duration_uses_monotonic_not_wall (test_p30_account_timing.TestMonotonicSource.test_duration_uses_monotonic_not_wall) ... ok
test_negative_monotonic_clamped (test_p30_account_timing.TestMonotonicSource.test_negative_monotonic_clamped) ... ok
test_bridgeconfig_declares_spans_field (test_p30_account_timing.TestSourceContracts.test_bridgeconfig_declares_spans_field) ... ok
test_failover_resets_spans_per_run (test_p30_account_timing.TestSourceContracts.test_failover_resets_spans_per_run) ... ok
test_final_message_includes_timing_block (test_p30_account_timing.TestSourceContracts.test_final_message_includes_timing_block) ... ok
test_monotonic_used_for_duration (test_p30_account_timing.TestSourceContracts.test_monotonic_used_for_duration) ... ok
test_no_rotation_or_resume_semantics_touched (test_p30_account_timing.TestSourceContracts.test_no_rotation_or_resume_semantics_touched)
الحارس السلبي: عداد الاستئناف يزداد فقط عند CREDIT_EXHAUSTED — سطر واحد كما كان. ... ok
test_span_closed_inside_finally_before_release (test_p30_account_timing.TestSourceContracts.test_span_closed_inside_finally_before_release)
الإغلاق داخل finally وقبل release_account_selection — حتمي في كل المسارات. ... ok
test_span_opened_at_claim_moment (test_p30_account_timing.TestSourceContracts.test_span_opened_at_claim_moment)
open يأتي مباشرة بعد record_account_journey (لحظة الـ claim الفعلي). ... ok
test_close_sets_duration_and_closed (test_p30_account_timing.TestSpanLifecycle.test_close_sets_duration_and_closed) ... ok
test_close_targets_matching_email_only (test_p30_account_timing.TestSpanLifecycle.test_close_targets_matching_email_only) ... ok
test_close_without_open_is_safe (test_p30_account_timing.TestSpanLifecycle.test_close_without_open_is_safe) ... ok
test_double_close_is_idempotent (test_p30_account_timing.TestSpanLifecycle.test_double_close_is_idempotent)
SCENARIO D: الإغلاق المزدوج لا يغيّر المدة المسجلة. ... ok
test_open_creates_span_with_monotonic_and_wall (test_p30_account_timing.TestSpanLifecycle.test_open_creates_span_with_monotonic_and_wall) ... ok
test_open_rejects_empty_email_and_none_cfg (test_p30_account_timing.TestSpanLifecycle.test_open_rejects_empty_email_and_none_cfg) ... ok
test_01_all_unchanged_files_never_call_qwen (test_p31_lazy_qwen_prefix.TestLazySkipsQwenWhenNothingChanged.test_01_all_unchanged_files_never_call_qwen)
كل الملفات مطابقة للريموت (نفس blob sha) ← كوين لا يُستدعى إطلاقاً ... ok
test_02_delete_of_missing_remote_file_never_calls_qwen (test_p31_lazy_qwen_prefix.TestLazySkipsQwenWhenNothingChanged.test_02_delete_of_missing_remote_file_never_calls_qwen)
delete_files كلها 404 على الريموت (لا حذف فعلي) ← كوين لا يُستدعى ... ok
test_03_unchanged_plus_missing_delete_combined_zero_calls (test_p31_lazy_qwen_prefix.TestLazySkipsQwenWhenNothingChanged.test_03_unchanged_plus_missing_delete_combined_zero_calls)
المزيج الكامل: unchanged + delete 404 ← صفر نداء (سيناريو sync cycle الدوري) ... ok
test_01_changed_file_calls_qwen_exactly_once (test_p31_lazy_qwen_prefix.TestLazyWakesQwenOnceOnRealChange.test_01_changed_file_calls_qwen_exactly_once)
ملف جديد (404 على الريموت) ← كوين مرة واحدة + البادئة في الرسالة ... ok
test_02_multiple_changed_files_still_one_qwen_call (test_p31_lazy_qwen_prefix.TestLazyWakesQwenOnceOnRealChange.test_02_multiple_changed_files_still_one_qwen_call)
3 ملفات متغيرة ← كوين مرة واحدة فقط (memoization — عقد DEC-019 محفوظ) ... ok
test_03_unchanged_then_changed_wakes_qwen_after_skip (test_p31_lazy_qwen_prefix.TestLazyWakesQwenOnceOnRealChange.test_03_unchanged_then_changed_wakes_qwen_after_skip)
ملف unchanged أولاً ثم ملف متغير ← كوين يستيقظ عند الثاني فقط — مرة واحدة ... ok
test_04_real_delete_wakes_qwen (test_p31_lazy_qwen_prefix.TestLazyWakesQwenOnceOnRealChange.test_04_real_delete_wakes_qwen)
delete فعلي (الملف موجود 200 على الريموت) ← كوين يُستدعى مرة واحدة ... ok
test_01_ai_prefix_starts_none_in_both (test_p31_lazy_qwen_prefix.TestSourceContracts.test_01_ai_prefix_starts_none_in_both) ... ok
test_02_lazy_helper_defined_in_both (test_p31_lazy_qwen_prefix.TestSourceContracts.test_02_lazy_helper_defined_in_both) ... ok
test_03_lazy_call_after_unchanged_check (test_p31_lazy_qwen_prefix.TestSourceContracts.test_03_lazy_call_after_unchanged_check)
النداء الكسول داخل حلقة الرفع يقع بعد فحص unchanged (وليس قبل الحلقة) ... ok
test_04_no_eager_call_before_put_loop (test_p31_lazy_qwen_prefix.TestSourceContracts.test_04_no_eager_call_before_put_loop)
لا يوجد استدعاء مباشر eager لـ _qwen_commit_prefix_for_job قبل الحلقة — ... ok
test_05_commit_messages_unchanged_verbatim (test_p31_lazy_qwen_prefix.TestSourceContracts.test_05_commit_messages_unchanged_verbatim)
صياغة رسائل sync/delete كما هي حرفياً (لم يمسها P31) ... ok
test_01_qwen_failure_keeps_old_message_verbatim (test_p31_lazy_qwen_prefix.TestVerbatimFallbackPreserved.test_01_qwen_failure_keeps_old_message_verbatim)
فشل كوين (Exception) ← نفس رسالة الكوميت القديمة حرفياً — الرفع لا ينكسر ... ok
test_02_failed_qwen_memoized_not_retried_per_file (test_p31_lazy_qwen_prefix.TestVerbatimFallbackPreserved.test_02_failed_qwen_memoized_not_retried_per_file)
فشل كوين مرة ← يُحفظ "" ولا تتكرر المحاولة لكل ملف (memoized حتى في الفشل) ... ok
test_01_click_email_button_shows_card (test_p32_account_password_lookup.TestAccountViewButton.test_01_click_email_button_shows_card) ... ok
test_02_click_from_second_page_index (test_p32_account_password_lookup.TestAccountViewButton.test_02_click_from_second_page_index) ... ok
test_03_card_offers_lookup_again_and_dashboard (test_p32_account_password_lookup.TestAccountViewButton.test_03_card_offers_lookup_again_and_dashboard) ... ok
test_04_state_cleared_after_view (test_p32_account_password_lookup.TestAccountViewButton.test_04_state_cleared_after_view) ... ok
test_05_out_of_range_index_is_graceful (test_p32_account_password_lookup.TestAccountViewButton.test_05_out_of_range_index_is_graceful) ... ok
test_06_garbage_index_is_graceful (test_p32_account_password_lookup.TestAccountViewButton.test_06_garbage_index_is_graceful) ... ok
test_07_negative_index_rejected (test_p32_account_password_lookup.TestAccountViewButton.test_07_negative_index_rejected) ... ok
test_01_first_page_of_twelve (test_p32_account_password_lookup.TestAccountsPageBounds.test_01_first_page_of_twelve) ... ok
test_02_middle_page (test_p32_account_password_lookup.TestAccountsPageBounds.test_02_middle_page) ... ok
test_03_last_page (test_p32_account_password_lookup.TestAccountsPageBounds.test_03_last_page) ... ok
test_04_page_beyond_last_clamps_down (test_p32_account_password_lookup.TestAccountsPageBounds.test_04_page_beyond_last_clamps_down) ... ok
test_05_zero_and_negative_clamp_up (test_p32_account_password_lookup.TestAccountsPageBounds.test_05_zero_and_negative_clamp_up) ... ok
test_06_garbage_page_defaults_to_first (test_p32_account_password_lookup.TestAccountsPageBounds.test_06_garbage_page_defaults_to_first) ... ok
test_07_empty_total_still_one_page (test_p32_account_password_lookup.TestAccountsPageBounds.test_07_empty_total_still_one_page) ... ok
test_08_exact_multiple_has_no_phantom_page (test_p32_account_password_lookup.TestAccountsPageBounds.test_08_exact_multiple_has_no_phantom_page) ... ok
test_01_cancel_clears_state (test_p32_account_password_lookup.TestCancelPath.test_01_cancel_clears_state) ... ok
test_02_cancel_returns_dashboard_keyboard (test_p32_account_password_lookup.TestCancelPath.test_02_cancel_returns_dashboard_keyboard) ... ok
test_03_cancel_message_confirms_cancellation (test_p32_account_password_lookup.TestCancelPath.test_03_cancel_message_confirms_cancellation) ... ok
test_04_text_after_cancel_is_normal_task_again (test_p32_account_password_lookup.TestCancelPath.test_04_text_after_cancel_is_normal_task_again) ... ok
test_01_new_button_label_present (test_p32_account_password_lookup.TestDashboardButtonContract.test_01_new_button_label_present) ... ok
test_02_new_callback_present (test_p32_account_password_lookup.TestDashboardButtonContract.test_02_new_callback_present) ... ok
test_03_old_check_accs_callback_removed (test_p32_account_password_lookup.TestDashboardButtonContract.test_03_old_check_accs_callback_removed) ... ok
test_04_old_button_label_removed (test_p32_account_password_lookup.TestDashboardButtonContract.test_04_old_button_label_removed) ... ok
test_05_dashboard_keyboard_exposes_lookup (test_p32_account_password_lookup.TestDashboardButtonContract.test_05_dashboard_keyboard_exposes_lookup) ... ok
test_06_state_constant_defined (test_p32_account_password_lookup.TestDashboardButtonContract.test_06_state_constant_defined) ... ok
test_07_page_size_is_five (test_p32_account_password_lookup.TestDashboardButtonContract.test_07_page_size_is_five) ... ok
test_01_deterministic_alphabetical_order (test_p32_account_password_lookup.TestLookupAccountListing.test_01_deterministic_alphabetical_order) ... ok
test_02_skips_entries_without_email (test_p32_account_password_lookup.TestLookupAccountListing.test_02_skips_entries_without_email) ... ok
test_03_empty_file_returns_empty_list (test_p32_account_password_lookup.TestLookupAccountListing.test_03_empty_file_returns_empty_list) ... ok
test_04_read_only_never_mutates_file (test_p32_account_password_lookup.TestLookupAccountListing.test_04_read_only_never_mutates_file) ... ok
test_01_first_page_shows_five_accounts (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_01_first_page_shows_five_accounts) ... ok
test_02_second_page_uses_absolute_indices (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_02_second_page_uses_absolute_indices) ... ok
test_03_first_page_has_next_but_no_prev (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_03_first_page_has_next_but_no_prev) ... ok
test_04_last_page_has_prev_but_no_next (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_04_last_page_has_prev_but_no_next) ... ok
test_05_middle_page_has_both_directions (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_05_middle_page_has_both_directions) ... ok
test_06_counter_button_is_noop (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_06_counter_button_is_noop) ... ok
test_07_single_page_hides_nav_row (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_07_single_page_hides_nav_row) ... ok
test_08_cancel_button_always_present (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_08_cancel_button_always_present) ... ok
test_09_callback_data_within_telegram_64_byte_limit (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_09_callback_data_within_telegram_64_byte_limit) ... ok
test_10_empty_db_text_reports_no_accounts (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_10_empty_db_text_reports_no_accounts) ... ok
test_11_text_shows_page_position_and_total (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_11_text_shows_page_position_and_total) ... ok
test_12_text_invites_manual_typing (test_p32_account_password_lookup.TestLookupKeyboardPagination.test_12_text_invites_manual_typing) ... ok
test_01_exact_match_returns_password (test_p32_account_password_lookup.TestManualEmailSearch.test_01_exact_match_returns_password) ... ok
test_02_case_and_whitespace_insensitive (test_p32_account_password_lookup.TestManualEmailSearch.test_02_case_and_whitespace_insensitive) ... ok
test_03_missing_email_returns_none (test_p32_account_password_lookup.TestManualEmailSearch.test_03_missing_email_returns_none) ... ok
test_04_blank_input_returns_none (test_p32_account_password_lookup.TestManualEmailSearch.test_04_blank_input_returns_none) ... ok
test_05_no_partial_substring_match (test_p32_account_password_lookup.TestManualEmailSearch.test_05_no_partial_substring_match) ... ok
test_01_typed_email_returns_password_card (test_p32_account_password_lookup.TestManualPathThroughUpdate.test_01_typed_email_returns_password_card) ... ok
test_02_typed_email_is_case_insensitive (test_p32_account_password_lookup.TestManualPathThroughUpdate.test_02_typed_email_is_case_insensitive) ... ok
test_03_state_cleared_after_success (test_p32_account_password_lookup.TestManualPathThroughUpdate.test_03_state_cleared_after_success) ... ok
test_04_email_is_not_dispatched_as_task_prompt (test_p32_account_password_lookup.TestManualPathThroughUpdate.test_04_email_is_not_dispatched_as_task_prompt) ... ok
test_05_unknown_email_reports_error_and_keeps_state (test_p32_account_password_lookup.TestManualPathThroughUpdate.test_05_unknown_email_reports_error_and_keeps_state) ... ok
test_06_unknown_email_offers_retry_keyboard (test_p32_account_password_lookup.TestManualPathThroughUpdate.test_06_unknown_email_offers_retry_keyboard) ... ok
test_07_retry_after_failure_succeeds (test_p32_account_password_lookup.TestManualPathThroughUpdate.test_07_retry_after_failure_succeeds) ... ok
test_08_no_regression_plain_text_still_becomes_task (test_p32_account_password_lookup.TestManualPathThroughUpdate.test_08_no_regression_plain_text_still_becomes_task) ... ok
test_01_sets_interactive_state_with_page_one (test_p32_account_password_lookup.TestOpenLookupScreen.test_01_sets_interactive_state_with_page_one) ... ok
test_02_sends_hybrid_screen_with_keyboard (test_p32_account_password_lookup.TestOpenLookupScreen.test_02_sends_hybrid_screen_with_keyboard) ... ok
test_01_next_page_edits_in_place (test_p32_account_password_lookup.TestPaginationThroughUpdate.test_01_next_page_edits_in_place) ... ok
test_02_next_page_shows_second_batch (test_p32_account_password_lookup.TestPaginationThroughUpdate.test_02_next_page_shows_second_batch) ... ok
test_03_prev_page_returns_to_first_batch (test_p32_account_password_lookup.TestPaginationThroughUpdate.test_03_prev_page_returns_to_first_batch) ... ok
test_04_page_persisted_in_state (test_p32_account_password_lookup.TestPaginationThroughUpdate.test_04_page_persisted_in_state) ... ok
test_05_manual_input_still_works_while_browsing (test_p32_account_password_lookup.TestPaginationThroughUpdate.test_05_manual_input_still_works_while_browsing) ... ok
test_06_out_of_range_page_clamps_without_crash (test_p32_account_password_lookup.TestPaginationThroughUpdate.test_06_out_of_range_page_clamps_without_crash) ... ok
test_07_garbage_page_token_clamps_to_first (test_p32_account_password_lookup.TestPaginationThroughUpdate.test_07_garbage_page_token_clamps_to_first) ... ok
test_08_noop_counter_does_nothing (test_p32_account_password_lookup.TestPaginationThroughUpdate.test_08_noop_counter_does_nothing) ... ok
test_01_email_and_password_are_copyable_code (test_p32_account_password_lookup.TestPasswordCardRendering.test_01_email_and_password_are_copyable_code) ... ok
test_02_missing_password_is_reported_explicitly (test_p32_account_password_lookup.TestPasswordCardRendering.test_02_missing_password_is_reported_explicitly) ... ok
test_03_absent_password_key_does_not_crash (test_p32_account_password_lookup.TestPasswordCardRendering.test_03_absent_password_key_does_not_crash) ... ok
test_04_html_special_chars_escaped (test_p32_account_password_lookup.TestPasswordCardRendering.test_04_html_special_chars_escaped) ... ok
test_05_status_line_reflects_active (test_p32_account_password_lookup.TestPasswordCardRendering.test_05_status_line_reflects_active) ... ok
test_06_banned_state_described (test_p32_account_password_lookup.TestPasswordCardRendering.test_06_banned_state_described) ... ok
test_07_cooldown_state_described (test_p32_account_password_lookup.TestPasswordCardRendering.test_07_cooldown_state_described) ... ok
test_08_card_keyboard_has_retry_and_back (test_p32_account_password_lookup.TestPasswordCardRendering.test_08_card_keyboard_has_retry_and_back) ... ok
test_01_manual_path_precedes_other_states (test_p32_account_password_lookup.TestSourceStructureContracts.test_01_manual_path_precedes_other_states)
المسار اليدوي يجب أن يكون أول فحص action وإلا التقطته حالة أخرى. ... ok
test_02_all_four_callbacks_handled (test_p32_account_password_lookup.TestSourceStructureContracts.test_02_all_four_callbacks_handled) ... ok
test_03_view_callback_uses_index_not_email (test_p32_account_password_lookup.TestSourceStructureContracts.test_03_view_callback_uses_index_not_email) ... ok
test_04_lookup_uses_read_accounts_safe_only (test_p32_account_password_lookup.TestSourceStructureContracts.test_04_lookup_uses_read_accounts_safe_only) ... ok
test_05_p29_p30_contracts_untouched (test_p32_account_password_lookup.TestSourceStructureContracts.test_05_p29_p30_contracts_untouched) ... ok
test_01_always_last_row_full_composition (test_p33_completed_quick_actions.TestBackToDashboardButton.test_01_always_last_row_full_composition) ... ok
test_02_always_last_even_minimal_composition (test_p33_completed_quick_actions.TestBackToDashboardButton.test_02_always_last_even_minimal_composition) ... ok
test_03_present_in_all_8_input_combinations (test_p33_completed_quick_actions.TestBackToDashboardButton.test_03_present_in_all_8_input_combinations) ... ok
test_04_new_project_row_stays_above_back_row (test_p33_completed_quick_actions.TestBackToDashboardButton.test_04_new_project_row_stays_above_back_row) ... ok
test_01_no_dead_url_button_when_pub_url_missing (test_p33_completed_quick_actions.TestConditionalRowsPreserved.test_01_no_dead_url_button_when_pub_url_missing)
url=None كان يكسر الرسالة كلها بصمت — العقد التاريخي محفوظ. ... ok
test_02_no_resume_rows_without_pid (test_p33_completed_quick_actions.TestConditionalRowsPreserved.test_02_no_resume_rows_without_pid) ... ok
test_03_no_details_button_without_project_key (test_p33_completed_quick_actions.TestConditionalRowsPreserved.test_03_no_details_button_without_project_key) ... ok
test_04_minimal_keyboard_still_has_two_rows (test_p33_completed_quick_actions.TestConditionalRowsPreserved.test_04_minimal_keyboard_still_has_two_rows) ... ok
test_05_resume_and_tree_share_same_row_as_before (test_p33_completed_quick_actions.TestConditionalRowsPreserved.test_05_resume_and_tree_share_same_row_as_before) ... ok
test_01_dedicated_row_alone (test_p33_completed_quick_actions.TestContinueNowButton.test_01_dedicated_row_alone) ... ok
test_02_callback_is_cont_resume_pid (test_p33_completed_quick_actions.TestContinueNowButton.test_02_callback_is_cont_resume_pid) ... ok
test_02b_style_is_success_green (test_p33_completed_quick_actions.TestContinueNowButton.test_02b_style_is_success_green)
زر ▶️ كمل الآن أخضر: style == "success" حرفياً. ... ok
test_02c_success_style_is_in_allowed_styles (test_p33_completed_quick_actions.TestContinueNowButton.test_02c_success_style_is_in_allowed_styles)
النمط المستخدم ضمن ALLOWED_BUTTON_STYLES — لن يسقط في make_inline_keyboard. ... ok
test_02d_legacy_resume_button_has_no_style (test_p33_completed_quick_actions.TestContinueNowButton.test_02d_legacy_resume_button_has_no_style)
Zero Breaking: زر 🔄 استئناف هذا المشروع القديم بلا style — لم يُمَس. ... ok
test_03_reuses_existing_cont_handler_prefix (test_p33_completed_quick_actions.TestContinueNowButton.test_03_reuses_existing_cont_handler_prefix)
يعيد استعمال معالج cont: القائم — نفس بادئة زر الاستئناف القديم حرفياً. ... ok
test_04_hidden_without_resume_pid (test_p33_completed_quick_actions.TestContinueNowButton.test_04_hidden_without_resume_pid) ... ok
test_05_hidden_with_empty_resume_pid (test_p33_completed_quick_actions.TestContinueNowButton.test_05_hidden_with_empty_resume_pid) ... ok
test_06_callback_data_within_telegram_64_byte_limit (test_p33_completed_quick_actions.TestContinueNowButton.test_06_callback_data_within_telegram_64_byte_limit)
عقد P25/P32: حد callback_data في تيليجرام 64 بايت — قياس فعلي بالبايتات. ... ok
test_01_cmd_dashboard_sends_full_dashboard (test_p33_completed_quick_actions.TestDashboardCallbackHandler.test_01_cmd_dashboard_sends_full_dashboard) ... ok
test_02_behavior_identical_to_show_dashboard (test_p33_completed_quick_actions.TestDashboardCallbackHandler.test_02_behavior_identical_to_show_dashboard) ... ok
test_03_unauthorized_chat_blocked (test_p33_completed_quick_actions.TestDashboardCallbackHandler.test_03_unauthorized_chat_blocked) ... ok
test_01_returns_inline_keyboard_dict (test_p33_completed_quick_actions.TestFullKeyboardComposition.test_01_returns_inline_keyboard_dict) ... ok
test_02_six_rows_in_exact_order (test_p33_completed_quick_actions.TestFullKeyboardComposition.test_02_six_rows_in_exact_order) ... ok
test_03_all_five_legacy_buttons_intact (test_p33_completed_quick_actions.TestFullKeyboardComposition.test_03_all_five_legacy_buttons_intact) ... ok
test_04_legacy_callbacks_unchanged (test_p33_completed_quick_actions.TestFullKeyboardComposition.test_04_legacy_callbacks_unchanged) ... ok
test_05_preview_button_is_url_not_callback (test_p33_completed_quick_actions.TestFullKeyboardComposition.test_05_preview_button_is_url_not_callback) ... ok
test_01_worker_calls_central_builder (test_p33_completed_quick_actions.TestSourceContracts.test_01_worker_calls_central_builder)
process_user_task_async يستدعي البنّاء المركزي بدل kb_rows المحلي. ... ok
test_02_builder_defined_exactly_once (test_p33_completed_quick_actions.TestSourceContracts.test_02_builder_defined_exactly_once) ... ok
test_03_dashboard_branch_exists_in_dispatcher (test_p33_completed_quick_actions.TestSourceContracts.test_03_dashboard_branch_exists_in_dispatcher) ... ok
test_04_legacy_show_dashboard_branch_untouched (test_p33_completed_quick_actions.TestSourceContracts.test_04_legacy_show_dashboard_branch_untouched)
مرساة حراس P26: حرفية الفرع القديم if data == "cmd:show_dashboard" باقية. ... ok
test_05_dashboard_branch_comes_after_show_dashboard (test_p33_completed_quick_actions.TestSourceContracts.test_05_dashboard_branch_comes_after_show_dashboard)
الفرع الجديد elif يلي الفرع القديم if في نفس السلسلة. ... ok
test_06_continue_now_button_text_in_source (test_p33_completed_quick_actions.TestSourceContracts.test_06_continue_now_button_text_in_source) ... ok
test_07_back_button_text_in_source (test_p33_completed_quick_actions.TestSourceContracts.test_07_back_button_text_in_source) ... ok
test_08_no_local_kb_rows_left_in_worker (test_p33_completed_quick_actions.TestSourceContracts.test_08_no_local_kb_rows_left_in_worker)
صفر بناء محلي متبقٍ للكيبورد داخل الـ worker (منع الازدواجية). ... ok
test_01_short_text_passes_verbatim (test_p34_safe_message_formatting.TestClampOutgoingText.test_01_short_text_passes_verbatim) ... ok
test_02_exactly_3900_passes_verbatim (test_p34_safe_message_formatting.TestClampOutgoingText.test_02_exactly_3900_passes_verbatim) ... ok
test_03_over_3900_trimmed_to_3800_or_less (test_p34_safe_message_formatting.TestClampOutgoingText.test_03_over_3900_trimmed_to_3800_or_less) ... ok
test_04_huge_text_trimmed (test_p34_safe_message_formatting.TestClampOutgoingText.test_04_huge_text_trimmed) ... ok
test_05_none_and_empty_safe (test_p34_safe_message_formatting.TestClampOutgoingText.test_05_none_and_empty_safe) ... ok
test_06_no_partial_html_tag_at_trim_point (test_p34_safe_message_formatting.TestClampOutgoingText.test_06_no_partial_html_tag_at_trim_point) ... ok
test_07_between_3801_and_3900_untouched (test_p34_safe_message_formatting.TestClampOutgoingText.test_07_between_3801_and_3900_untouched) ... ok
test_01_short_text_passes_verbatim (test_p34_safe_message_formatting.TestClampPreviewText.test_01_short_text_passes_verbatim) ... ok
test_02_exactly_1000_passes_verbatim_no_suffix (test_p34_safe_message_formatting.TestClampPreviewText.test_02_exactly_1000_passes_verbatim_no_suffix) ... ok
test_03_over_1000_truncated_with_suffix (test_p34_safe_message_formatting.TestClampPreviewText.test_03_over_1000_truncated_with_suffix) ... ok
test_04_body_never_exceeds_1000_plus_suffix (test_p34_safe_message_formatting.TestClampPreviewText.test_04_body_never_exceeds_1000_plus_suffix) ... ok
test_05_none_and_empty_safe (test_p34_safe_message_formatting.TestClampPreviewText.test_05_none_and_empty_safe) ... ok
test_06_no_partial_html_entity_at_cut (test_p34_safe_message_formatting.TestClampPreviewText.test_06_no_partial_html_entity_at_cut) ... ok
test_07_no_partial_html_tag_at_cut (test_p34_safe_message_formatting.TestClampPreviewText.test_07_no_partial_html_tag_at_cut) ... ok
test_08_old_2500_truncation_gone_from_source (test_p34_safe_message_formatting.TestClampPreviewText.test_08_old_2500_truncation_gone_from_source) ... ok
test_01_small_message_untouched (test_p34_safe_message_formatting.TestCompletionBudget.test_01_small_message_untouched) ... ok
test_02_oversized_message_capped_at_3500 (test_p34_safe_message_formatting.TestCompletionBudget.test_02_oversized_message_capped_at_3500) ... ok
test_03_shrink_hits_preview_first_metadata_preserved (test_p34_safe_message_formatting.TestCompletionBudget.test_03_shrink_hits_preview_first_metadata_preserved) ... ok
test_04_shrunk_preview_keeps_suffix (test_p34_safe_message_formatting.TestCompletionBudget.test_04_shrunk_preview_keeps_suffix) ... ok
test_05_no_preview_fallback_tail_trim (test_p34_safe_message_formatting.TestCompletionBudget.test_05_no_preview_fallback_tail_trim) ... ok
test_06_none_and_empty_safe (test_p34_safe_message_formatting.TestCompletionBudget.test_06_none_and_empty_safe) ... ok
test_07_extreme_overflow_always_capped (test_p34_safe_message_formatting.TestCompletionBudget.test_07_extreme_overflow_always_capped) ... ok
test_08_result_is_idempotent (test_p34_safe_message_formatting.TestCompletionBudget.test_08_result_is_idempotent) ... ok
test_01_preview_max_chars_is_1000 (test_p34_safe_message_formatting.TestP34Constants.test_01_preview_max_chars_is_1000) ... ok
test_02_truncation_suffix_exact_text (test_p34_safe_message_formatting.TestP34Constants.test_02_truncation_suffix_exact_text) ... ok
test_03_res_msg_max_chars_is_3500 (test_p34_safe_message_formatting.TestP34Constants.test_03_res_msg_max_chars_is_3500) ... ok
test_04_outgoing_hard_limit_is_3900 (test_p34_safe_message_formatting.TestP34Constants.test_04_outgoing_hard_limit_is_3900) ... ok
test_05_outgoing_safe_limit_is_3800 (test_p34_safe_message_formatting.TestP34Constants.test_05_outgoing_safe_limit_is_3800) ... ok
test_06_constants_defined_once_in_source (test_p34_safe_message_formatting.TestP34Constants.test_06_constants_defined_once_in_source) ... ok
test_07_safe_below_hard_below_telegram_4096 (test_p34_safe_message_formatting.TestP34Constants.test_07_safe_below_hard_below_telegram_4096) ... ok
test_01_sender_payload_uses_clamp (test_p34_safe_message_formatting.TestP34SourceContracts.test_01_sender_payload_uses_clamp) ... ok
test_02_worker_uses_clamp_preview_text (test_p34_safe_message_formatting.TestP34SourceContracts.test_02_worker_uses_clamp_preview_text) ... ok
test_03_worker_enforces_res_msg_budget (test_p34_safe_message_formatting.TestP34SourceContracts.test_03_worker_enforces_res_msg_budget) ... ok
test_04_budget_enforced_before_send (test_p34_safe_message_formatting.TestP34SourceContracts.test_04_budget_enforced_before_send) ... ok
test_05_functions_defined_once (test_p34_safe_message_formatting.TestP34SourceContracts.test_05_functions_defined_once) ... ok
test_06_preview_body_captured_for_budget (test_p34_safe_message_formatting.TestP34SourceContracts.test_06_preview_body_captured_for_budget) ... ok
test_07_refactor_mirror_has_p34_symbols (test_p34_safe_message_formatting.TestP34SourceContracts.test_07_refactor_mirror_has_p34_symbols) ... ok
test_01_long_text_trimmed_in_payload (test_p34_safe_message_formatting.TestSenderKeepsButtonsIntact.test_01_long_text_trimmed_in_payload) ... ok
test_02_reply_markup_rows_fully_intact (test_p34_safe_message_formatting.TestSenderKeepsButtonsIntact.test_02_reply_markup_rows_fully_intact) ... ok
test_03_short_text_not_modified (test_p34_safe_message_formatting.TestSenderKeepsButtonsIntact.test_03_short_text_not_modified) ... ok
test_04_boolean_wrapper_still_works (test_p34_safe_message_formatting.TestSenderKeepsButtonsIntact.test_04_boolean_wrapper_still_works) ... ok
test_01_markers_list_exists_and_lowercase (test_p35_model_decline.TestP35Constants.test_01_markers_list_exists_and_lowercase) ... ok
test_02_canonical_marker_present (test_p35_model_decline.TestP35Constants.test_02_canonical_marker_present) ... ok
test_03_max_chars_is_300 (test_p35_model_decline.TestP35Constants.test_03_max_chars_is_300) ... ok
test_04_status_constant_value (test_p35_model_decline.TestP35Constants.test_04_status_constant_value) ... ok
test_05_single_definition_of_each_constant (test_p35_model_decline.TestP35Constants.test_05_single_definition_of_each_constant) ... ok
test_01_first_row_is_retry_prompt_primary (test_p35_model_decline.TestP35DeclineKeyboard.test_01_first_row_is_retry_prompt_primary) ... ok
test_02_second_row_is_dashboard_danger (test_p35_model_decline.TestP35DeclineKeyboard.test_02_second_row_is_dashboard_danger) ... ok
test_03_styles_within_allowed_whitelist (test_p35_model_decline.TestP35DeclineKeyboard.test_03_styles_within_allowed_whitelist) ... ok
test_04_completed_keyboard_rows_appended_verbatim (test_p35_model_decline.TestP35DeclineKeyboard.test_04_completed_keyboard_rows_appended_verbatim) ... ok
test_05_no_dead_url_button_without_pub_url (test_p35_model_decline.TestP35DeclineKeyboard.test_05_no_dead_url_button_without_pub_url) ... ok
test_06_decline_rows_survive_all_input_combinations (test_p35_model_decline.TestP35DeclineKeyboard.test_06_decline_rows_survive_all_input_combinations) ... ok
test_07_resume_button_present_with_pid (test_p35_model_decline.TestP35DeclineKeyboard.test_07_resume_button_present_with_pid) ... ok
test_08_callback_data_within_telegram_64_bytes (test_p35_model_decline.TestP35DeclineKeyboard.test_08_callback_data_within_telegram_64_bytes) ... ok
test_01_canonical_decline_detected (test_p35_model_decline.TestP35Detection.test_01_canonical_decline_detected) ... ok
test_02_all_markers_detected (test_p35_model_decline.TestP35Detection.test_02_all_markers_detected) ... ok
test_03_case_insensitive (test_p35_model_decline.TestP35Detection.test_03_case_insensitive) ... ok
test_04_whitespace_stripped (test_p35_model_decline.TestP35Detection.test_04_whitespace_stripped) ... ok
test_05_none_and_empty_are_not_decline (test_p35_model_decline.TestP35Detection.test_05_none_and_empty_are_not_decline) ... ok
test_06_long_legit_response_quoting_marker_is_not_decline (test_p35_model_decline.TestP35Detection.test_06_long_legit_response_quoting_marker_is_not_decline) ... ok
test_07_boundary_at_exactly_300_chars (test_p35_model_decline.TestP35Detection.test_07_boundary_at_exactly_300_chars) ... ok
test_08_normal_short_answer_is_not_decline (test_p35_model_decline.TestP35Detection.test_08_normal_short_answer_is_not_decline) ... ok
test_09_detect_response_status_still_completed_for_decline_text (test_p35_model_decline.TestP35Detection.test_09_detect_response_status_still_completed_for_decline_text) ... ok
test_01_decline_retry_handler_exists (test_p35_model_decline.TestP35DispatcherHandlers.test_01_decline_retry_handler_exists) ... ok
test_02_decline_dashboard_handler_exists (test_p35_model_decline.TestP35DispatcherHandlers.test_02_decline_dashboard_handler_exists) ... ok
test_03_decline_dashboard_matches_dashboard_behavior (test_p35_model_decline.TestP35DispatcherHandlers.test_03_decline_dashboard_matches_dashboard_behavior) ... ok
test_04_retry_handler_sends_guidance_not_task (test_p35_model_decline.TestP35DispatcherHandlers.test_04_retry_handler_sends_guidance_not_task) ... ok
test_05_legacy_dashboard_branch_untouched (test_p35_model_decline.TestP35DispatcherHandlers.test_05_legacy_dashboard_branch_untouched) ... ok
test_01_kind_is_failure (test_p35_model_decline.TestP35TerminalOutcome.test_01_kind_is_failure) ... ok
test_02_allow_preview_true (test_p35_model_decline.TestP35TerminalOutcome.test_02_allow_preview_true) ... ok
test_03_title_is_distinct_decline_banner (test_p35_model_decline.TestP35TerminalOutcome.test_03_title_is_distinct_decline_banner) ... ok
test_04_note_explains_not_sent_semantics (test_p35_model_decline.TestP35TerminalOutcome.test_04_note_explains_not_sent_semantics) ... ok
test_05_completed_outcome_untouched (test_p35_model_decline.TestP35TerminalOutcome.test_05_completed_outcome_untouched) ... ok
test_06_other_failures_keep_allow_preview_false (test_p35_model_decline.TestP35TerminalOutcome.test_06_other_failures_keep_allow_preview_false) ... ok
test_01_reclassification_only_over_completed (test_p35_model_decline.TestP35WorkerSourceContracts.test_01_reclassification_only_over_completed) ... ok
test_02_status_becomes_model_declined (test_p35_model_decline.TestP35WorkerSourceContracts.test_02_status_becomes_model_declined) ... ok
test_03_final_pid_reset_blocks_resume_pointer_advance (test_p35_model_decline.TestP35WorkerSourceContracts.test_03_final_pid_reset_blocks_resume_pointer_advance) ... ok
test_04_decline_keyboard_used_for_declined_status (test_p35_model_decline.TestP35WorkerSourceContracts.test_04_decline_keyboard_used_for_declined_status) ... ok
test_05_completed_keyboard_still_default (test_p35_model_decline.TestP35WorkerSourceContracts.test_05_completed_keyboard_still_default) ... ok
test_06_reclassification_after_failover_before_identity_write (test_p35_model_decline.TestP35WorkerSourceContracts.test_06_reclassification_after_failover_before_identity_write) ... ok
test_01_completed_keyboard_has_no_decline_buttons (test_p35_model_decline.TestP35ZeroBreaking.test_01_completed_keyboard_has_no_decline_buttons) ... ok
test_02_completed_keyboard_contracts_intact (test_p35_model_decline.TestP35ZeroBreaking.test_02_completed_keyboard_contracts_intact) ... ok
test_03_credit_exhausted_flow_not_reclassified (test_p35_model_decline.TestP35ZeroBreaking.test_03_credit_exhausted_flow_not_reclassified) ... ok
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
Ran 678 tests in 0.909s

OK
```
