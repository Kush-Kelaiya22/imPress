# Graph Report - imPress  (2026-10-13)

## Corpus Check
- 339 files · ~307,812 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 51 file(s) not represented in the graph (top: (none) 20, .css 4, .in 4)

## Summary
- 3477 nodes · 9129 edges · 238 communities (108 shown, 130 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 1416 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d73ec172`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- User
- test_auth_sessions.py
- schemas.py
- main.py
- istnow
- nvs_open
- App.jsx
- app.js
- wifi_client.c
- protocol.c
- esp_websocket_client.c
- migrations.py
- services/deployments.py
- firmware.py
- display.c
- class_s3/main/ota.c
- test_user_delete.py
- cJSON_Utils.c
- ClassSession
- release.py
- playwright_sync_api
- test_quiz_timer.py
- cJSON.c
- imPress Hardware Integration Test Report
- students.py
- select
- test_core_utils.py
- QuizAnswer
- test_mesh_dedup.c
- Gateway
- routers/auth.py
- parse_image
- test_ws_auth.py
- test_device_api.py
- cJSON_Delete
- quizzes.py
- mesh_master.c
- test_students.py
- app/auth.py
- test_quiz_correct_option.py
- test_spi_slave.c
- cJSON
- test_maintenance_windows.py
- api.js
- test_question_import.py
- models.py
- test_class_import.py
- test_quiz_poll_lifecycle.py
- test_firmware_registry.py
- test_run_tests.py
- test_ci_workflow.py
- functions
- test_policy.py
- config.py
- test_schedule_occupancy.py
- run_tests.py
- pathlib
- tests/test_student_modules.py
- ota_parse_check
- _ota_task
- import_question_csv
- routers/deployments.py
- test_device_keys.py
- spi_to_http_task
- test_trusted_installer.py
- test_firmware_signing.py
- test_super_admin_lockout.py
- test_migrations.py
- test_transport.py
- strip_comments_and_strings
- test_c6_diagnostics.py
- test_login_throttle.py
- test_backend_contract_fixture
- pytest
- re
- test_manage_cli.py
- test_e2e_ota.py
- test_admin_users.py
- on_ws_command
- ui_tests/conftest.py
- test_device_batch_dedup.py
- test_classes_courses.py
- shutil
- gateway_sim.py
- test_user_lifecycle_api.py
- json
- test_repo_hygiene.py
- FakeGitHub
- test_firmware_manager.py
- get
- test_health.py
- test_signed_profile.py
- test_install_scripts.py
- test_device_limits.py
- firmware_signing.py
- test_gateway_autolink.py
- test_ota_download_gating.py
- websocket_linux.c
- test_session_revocation.py
- _repo
- test_session_token_storage.py
- test_hardware_requirements.py
- test_fault_injection.py
- passwords.py
- backend/tests/conftest.py
- test_gating_needs_the_line_to_exist_before_the_release
- _sqlite_pragmas
- test_vote_answer_auth.py
- class_c6/test_host/run.sh
- migrate
- build_signed.sh
- firmware_key.sh
- afl-prepare-linux.sh
- afl.sh script
- ossfuzz.sh
- start_server.sh
- run_config.sh
- run_ota_logic.sh
- run_student_set.sh
- run_ws_command.sh
- protocol/test_host/run.sh
- run_backend_hint.sh
- run_mesh_dedup.sh
- run_host_tests.sh
- student/test_host/run.sh
- docker-entrypoint.sh
- install.sh
- start.sh
- _ancestry
- wf
- .update
- test_results_access.py
- test_cofaculty_access.py
- test_class_create.py
- test_firmware_upload.py
- test_class_join.py
- check
- test_firmware.py
- datetime
- ui_tests/test_deployments.py
- ClassUpdate
- migrate_utc_to_ist.py
- test_real_build_output_parses
- refresh_session_activity
- MigrationError
- ClassDevicesResponse

## God Nodes (most connected - your core abstractions)
1. `select()` - 169 edges
2. `User` - 154 edges
3. `istnow()` - 107 edges
4. `EspDevice` - 106 edges
5. `ClassSession` - 96 edges
6. `_post()` - 77 edges
7. `log_activity()` - 72 edges
8. `functions()` - 50 edges
9. `escHtml()` - 42 edges
10. `Quiz` - 41 edges

## Surprising Connections (you probably didn't know these)
- `test_every_setting_is_documented()` --uses--> `Settings`  [INFERRED]
  tests/test_docs_consistency.py → backend/app/config.py
- `test_signature_status_is_shown()` --calls--> `make_image()`  [INFERRED]
  ui_tests/test_firmware.py → backend/tests/firmware_images.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_auth_sessions.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_create.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_import.py → run_tests.py

## Import Cycles
- None detected.

## Communities (238 total, 130 thin omitted)

### Community 0 - "User"
Cohesion: 0.05
Nodes (59): log_activity(), hash_password(), User, problem(), roster_access(), admin_class_devices(), admin_create_class(), admin_delete_class() (+51 more)

### Community 1 - "test_auth_sessions.py"
Cohesion: 0.13
Nodes (12): _session_row(), q(), _shift_session(), go(), test_expired_session_cannot_be_revived_by_activity_ping(), test_explicit_activity_ping_extends_the_session(), test_hard_expiry_reports_hard_code_even_if_active(), test_idle_expiry_reports_idle_code() (+4 more)

### Community 2 - "schemas.py"
Cohesion: 0.06
Nodes (43): ActivityLogResponse, AdminUserCreate, BulkStudentRegister, ClassAssignTeacher, ClassFacultyUpdate, ClassJoin, CourseCreate, CourseResponse (+35 more)

### Community 3 - "main.py"
Cohesion: 0.06
Nodes (18): lifespan(), account_refusal(), allowed(), can_grant(), class_owner_or_admin(), forbidden(), is_staff(), require() (+10 more)

### Community 4 - "istnow"
Cohesion: 0.05
Nodes (51): api_key_ok(), authorize(), _by_mac(), caller_for_key(), denial(), device_caller(), DeviceCaller, key_hash() (+43 more)

### Community 5 - "nvs_open"
Cohesion: 0.07
Nodes (58): cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str(), _store_dev_key(), ota_c6_boot_check() (+50 more)

### Community 6 - "App.jsx"
Cohesion: 0.06
Nodes (47): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+39 more)

### Community 7 - "app.js"
Cohesion: 0.08
Nodes (67): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+59 more)

### Community 8 - "wifi_client.c"
Cohesion: 0.07
Nodes (31): app_main(), heartbeat_task(), wifi_connect_with_backoff(), download(), fail(), ota_c6_set_mac(), ota_c6_start(), ota_task() (+23 more)

### Community 9 - "protocol.c"
Cohesion: 0.15
Nodes (25): crc16_ccitt(), msg_decode(), msg_verify_crc(), spi_record_read(), spi_record_write(), spi_slot_decode(), spi_slot_encode(), spi_slot_fifo_drop() (+17 more)

### Community 10 - "esp_websocket_client.c"
Cohesion: 0.10
Nodes (47): ws_client_reconnect(), ws_client_start(), ws_client_stop(), destroy_and_free_resources(), esp_websocket_client_abort_connection(), esp_websocket_client_append_header(), esp_websocket_client_close(), esp_websocket_client_close_with_code() (+39 more)

### Community 11 - "migrations.py"
Cohesion: 0.14
Nodes (13): _add_columns(), add_deployment_deferral(), add_device_keys(), add_diagnostics_columns(), add_firmware_signer(), add_quiz_question_started_at(), add_unique_constraints(), add_v2_columns() (+5 more)

### Community 12 - "services/deployments.py"
Cohesion: 0.06
Nodes (55): DeploymentTarget, FirmwareDeployment, active_target(), advance(), advance_all(), cancel(), create_deployment(), deployments_loop() (+47 more)

### Community 13 - "firmware.py"
Cohesion: 0.07
Nodes (31): FirmwareArtifact, approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get(), _latest_approved() (+23 more)

### Community 14 - "display.c"
Cohesion: 0.12
Nodes (31): display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown(), display_show_provision_state(), display_show_question(), display_show_result() (+23 more)

### Community 15 - "class_s3/main/ota.c"
Cohesion: 0.06
Nodes (5): ws_client_send(), read_file(), main(), _wifi_event_handler(), on_espnow_recv()

### Community 16 - "test_user_delete.py"
Cohesion: 0.08
Nodes (13): accounts(), _create(), test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected(), _exec(), _rows(), go() (+5 more)

### Community 17 - "cJSON_Utils.c"
Cohesion: 0.14
Nodes (46): cJSON_AddItemToArray(), cJSON_AddItemToObject(), cJSON_CreateObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc() (+38 more)

### Community 18 - "ClassSession"
Cohesion: 0.10
Nodes (28): ClassSession, class_access(), _accessible_class(), activate_class(), add_exception(), class_presence(), _count_students(), create_class() (+20 more)

### Community 19 - "release.py"
Cohesion: 0.08
Nodes (44): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+36 more)

### Community 20 - "playwright_sync_api"
Cohesion: 0.05
Nodes (15): _open(), test_invalid_rows_block_the_import(), test_valid_file_creates_courses_and_sections(), _open_create_quiz(), test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz() (+7 more)

### Community 21 - "test_quiz_timer.py"
Cohesion: 0.08
Nodes (33): advance(), answer_closed(), deadline(), finish(), quiz_timer_loop(), tick(), time_limit_s(), _transition() (+25 more)

### Community 22 - "cJSON.c"
Cohesion: 0.12
Nodes (31): buffer_skip_whitespace(), cJSON_AddBoolToObject(), cJSON_Compare(), cJSON_CreateBool(), cJSON_InitHooks(), cJSON_Minify(), cJSON_ParseWithLength(), cJSON_ParseWithLengthOpts() (+23 more)

### Community 23 - "imPress Hardware Integration Test Report"
Cohesion: 0.06
Nodes (31): 10. Reproducible Windows Commands (No Secrets), 11. Blocked/Unperformed Tests and Limitations, 12. Final Status: **PARTIAL**, 1. Hardware Configuration, 2. Toolchain Versions, 3. Network Configuration (Secret-Free), 4.1 Protocol Layer Tests (Host), 4.2 Backend Connectivity (+23 more)

### Community 24 - "students.py"
Cohesion: 0.16
Nodes (13): Student, bulk_create_students(), _create_one(), create_student(), deactivate_student(), get_student(), hard_delete_student(), import_students_to_class_csv() (+5 more)

### Community 25 - "select"
Cohesion: 0.22
Nodes (16): Poll, create_poll(), end_poll(), get_poll(), list_polls(), _poll_response(), poll_results(), start_poll() (+8 more)

### Community 26 - "test_core_utils.py"
Cohesion: 0.06
Nodes (21): _parse_time(), _slots_conflict(), normalize_version(), as_ist(), ist_epoch_ms(), ist_iso(), istnow_aware(), ConnectionManager (+13 more)

### Community 27 - "QuizAnswer"
Cohesion: 0.09
Nodes (30): commit_or_conflict(), Attendance, PollVote, QuizAnswer, StudentEnrollment, student_participation(), delete_class_records(), erase_student() (+22 more)

### Community 28 - "test_mesh_dedup.c"
Cohesion: 0.27
Nodes (11): mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main(), simulate(), test_dedup_window_and_wrap(), test_id_ignores_hops_but_not_content() (+3 more)

### Community 29 - "Gateway"
Cohesion: 0.15
Nodes (3): Gateway, rooms(), live()

### Community 30 - "routers/auth.py"
Cohesion: 0.12
Nodes (14): verify_password(), activity_ping(), change_password(), login(), logout(), me(), session_info(), session_status() (+6 more)

### Community 31 - "parse_image"
Cohesion: 0.18
Nodes (11): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), SignatureError, verify_signature(), test_an_image_changed_after_signing_is_refused() (+3 more)

### Community 32 - "test_ws_auth.py"
Cohesion: 0.16
Nodes (10): _rejected(), test_device_key_still_required(), test_inactive_user_rejected(), deactivate(), test_teacher_after_logout_rejected(), test_teacher_cannot_join_another_teachers_class(), test_teacher_with_bad_token_rejected(), test_teacher_with_idle_expired_session_rejected() (+2 more)

### Community 33 - "test_device_api.py"
Cohesion: 0.09
Nodes (33): _activity(), q(), _device(), q(), _register(), su(), test_attendance_paths(), count() (+25 more)

### Community 34 - "cJSON_Delete"
Cohesion: 0.13
Nodes (32): batch_flush(), add_item_to_object(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddFalseToObject(), cJSON_AddItemToObjectCS(), cJSON_AddNullToObject(), cJSON_AddNumberToObject() (+24 more)

### Community 35 - "quizzes.py"
Cohesion: 0.15
Nodes (19): Quiz, QuizQuestion, create_quiz(), get_quiz(), list_quizzes(), next_question(), question_csv_template(), _quiz_response() (+11 more)

### Community 36 - "mesh_master.c"
Cohesion: 0.15
Nodes (16): handle_c6_frame(), heartbeat_task(), on_student_message(), extract_enrollment(), find_or_create_student(), mesh_master_broadcast(), mesh_master_get_all_students(), mesh_master_get_student() (+8 more)

### Community 37 - "test_students.py"
Cohesion: 0.12
Nodes (4): _csv(), su(), test_csv_import_mixed_rows(), test_enrollment_number_must_be_10_alphanumerics()

### Community 38 - "app/auth.py"
Cohesion: 0.14
Nodes (11): create_access_token(), create_session(), generate_session_token(), get_current_user(), get_current_user_light(), _load_session_by_hash(), revoke_user_sessions(), _sha256_hex() (+3 more)

### Community 39 - "test_quiz_correct_option.py"
Cohesion: 0.25
Nodes (5): _create(), ctx(), test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 40 - "test_spi_slave.c"
Cohesion: 0.09
Nodes (31): queue_slot(), ready_update(), spi_post_trans_cb(), spi_slave_init(), spi_slave_read(), spi_slave_send(), clobber_stack(), gpio_config() (+23 more)

### Community 41 - "cJSON"
Cohesion: 0.12
Nodes (28): add_item_to_array(), case_insensitive_strcmp(), cJSON_AddItemReferenceToArray(), cJSON_AddItemReferenceToObject(), cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive(), cJSON_DetachItemFromArray() (+20 more)

### Community 42 - "test_maintenance_windows.py"
Cohesion: 0.15
Nodes (22): next_window(), _advance(), _artifact(), at(), clock(), _deploy(), _gateway(), h() (+14 more)

### Community 44 - "api.js"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 45 - "test_question_import.py"
Cohesion: 0.14
Nodes (26): _csv(), ctx(), _files(), import_(), parse(), questions(), q(), test_any_invalid_row_means_nothing_is_imported() (+18 more)

### Community 46 - "models.py"
Cohesion: 0.08
Nodes (16): Base, get_db(), ClassOccurrenceException, Course, LoginThrottle, ScheduleSource, create_course(), delete_course() (+8 more)

### Community 47 - "test_class_import.py"
Cohesion: 0.07
Nodes (33): ClassImportReport, ClassImportRow, _changes(), plan_class_import(), _resolve_aliases(), _row_fields(), csv_safe(), CsvFileError (+25 more)

### Community 48 - "test_quiz_poll_lifecycle.py"
Cohesion: 0.11
Nodes (21): env(), _poll(), _quiz(), test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted(), test_draft_quiz_cannot_be_stopped(), test_impromptu_quiz_is_live_immediately(), test_list_quizzes_for_class() (+13 more)

### Community 49 - "test_firmware_registry.py"
Cohesion: 0.15
Nodes (15): make_image(), _count(), q(), h(), test_admin_only(), test_corrupted_image_is_detected_by_its_hash(), test_device_downloads_its_registered_image_with_its_hash(), test_facts_come_from_the_image_not_the_form() (+7 more)

### Community 50 - "test_run_tests.py"
Cohesion: 0.09
Nodes (18): discover(), _requirements(), run_streaming(), test_every_default_runner_suite_runs_in_ci(), test_frontend_is_installed_from_its_lockfile(), test_closed_output_pipe_exits_quietly(), test_ctrl_c_stops_the_whole_process_group(), test_dev_requirements_cover_every_runtime_requirement() (+10 more)

### Community 51 - "test_ci_workflow.py"
Cohesion: 0.12
Nodes (16): _norm(), _on(), _steps_text(), test_actions_are_pinned_to_commit_shas(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_container_images_are_pinned_to_digests() (+8 more)

### Community 52 - "functions"
Cohesion: 0.08
Nodes (35): calls(), functions(), mentions(), test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch(), _order() (+27 more)

### Community 53 - "test_policy.py"
Cohesion: 0.09
Nodes (13): _calls(), _routes(), test_every_route_is_governed_by_the_policy_or_listed(), test_no_role_comparisons_outside_the_policy(), test_published_permission_matrix_matches_the_code(), _refused(), _routes(), test_device_routes_reject_a_wrong_key() (+5 more)

### Community 54 - "config.py"
Cohesion: 0.12
Nodes (8): check_secure(), insecure_settings(), Settings, _fresh_settings(), test_cors_only_configured_origins(), test_debug_and_sql_echo_off_by_default(), test_refuses_default_secrets_outside_debug(), test_unauthenticated_websockets_need_debug()

### Community 55 - "test_schedule_occupancy.py"
Cohesion: 0.16
Nodes (15): _add(), _busy(), phy(), su(), test_a_cancelled_day_frees_every_slot(), test_auris_rows_are_not_deleted_locally(), imported(), test_cancelled_moved_and_extra() (+7 more)

### Community 56 - "run_tests.py"
Cohesion: 0.10
Nodes (25): CaseResult, fmt_secs(), main(), markdown_report(), _missing(), missing_packages(), Paint, parse_coverage() (+17 more)

### Community 57 - "pathlib"
Cohesion: 0.10
Nodes (7): init_env(), call(), env_value(), main(), git(), tracked_files(), workflow()

### Community 58 - "tests/test_student_modules.py"
Cohesion: 0.22
Nodes (19): _age(), _batch(), beat(), join(), leave(), _modules(), _rows(), q() (+11 more)

### Community 59 - "ota_parse_check"
Cohesion: 0.14
Nodes (11): is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target(), cJSON_IsTrue(), test_digest_comparison(), test_nothing_offered() (+3 more)

### Community 60 - "_ota_task"
Cohesion: 0.16
Nodes (15): cfg_has_device_key(), _download_and_apply(), _firmware_check(), _get_mac(), _http_post(), _http_post_body(), _ota_finish_without_update(), _ota_task() (+7 more)

### Community 61 - "import_question_csv"
Cohesion: 0.14
Nodes (10): import_question_csv(), parse_question_csv(), device_text_warnings(), question_warnings(), QuestionImportReport, QuestionImportRow, QuizQuestionCreate, text_key() (+2 more)

### Community 62 - "routers/deployments.py"
Cohesion: 0.22
Nodes (12): _act(), cancel_deployment(), create_deployment(), deployment_dict(), DeploymentCreate, _get(), get_deployment(), list_deployments() (+4 more)

### Community 63 - "test_device_keys.py"
Cohesion: 0.22
Nodes (18): _beat(), _device(), q(), h(), _key(), _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out() (+10 more)

### Community 64 - "spi_to_http_task"
Cohesion: 0.16
Nodes (19): batch_add(), batch_flush_needed(), batch_init(), item_is_heartbeat(), msg_to_json(), process_spi_payload(), spi_to_http_task(), status_ping_task() (+11 more)

### Community 65 - "test_trusted_installer.py"
Cohesion: 0.21
Nodes (12): _artifact(), _deploy(), _download(), h(), _register(), strict(), test_a_database_edit_to_approved_is_not_enough(), test_a_tampered_file_is_never_served() (+4 more)

### Community 66 - "test_firmware_signing.py"
Cohesion: 0.22
Nodes (10): _digest(), h(), site_key(), test_a_foreign_key_is_refused_but_a_second_signature_by_the_site_key_counts(), test_an_unreadable_site_key_is_reported(), test_real_signatures_verify_and_the_key_digest_matches_espsecure(), test_unsigned_images_from_before_are_not_deployed_once_signing_is_required(), test_with_a_site_key_only_images_it_signed_are_accepted() (+2 more)

### Community 67 - "test_super_admin_lockout.py"
Cohesion: 0.14
Nodes (10): _me(), su(), test_concurrent_mutual_deactivation_leaves_one_super_admin(), deactivate(), race(), test_database_refuses_removing_the_last_super_admin(), go(), test_no_self_lockout_on_any_route() (+2 more)

### Community 68 - "test_migrations.py"
Cohesion: 0.25
Nodes (12): _all_versions(), _backups(), _indexes(), _legacy_db(), _migrate(), _model_unique_indexes(), _q(), test_a_failing_step_rolls_back_its_ddl() (+4 more)

### Community 69 - "test_transport.py"
Cohesion: 0.12
Nodes (8): enforce_https(), is_loopback(), needs_https(), _https(), strict(), test_a_reverse_proxy_counts_as_https(), test_https_works_and_gets_hsts(), test_loopback_is_exempt()

### Community 70 - "strip_comments_and_strings"
Cohesion: 0.14
Nodes (8): strip_comments_and_strings(), test_connection_failures_say_why(), test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), test_app_rollback_enabled(), test_detach_unregisters_reconnect_handler_before_disconnecting(), test_new_image_marked_valid_only_after_mesh_and_spi_init(), test_only_a_successful_install_reboots()

### Community 71 - "test_c6_diagnostics.py"
Cohesion: 0.16
Nodes (7): _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat(), test_docs_build_inputs_are_pinned_and_valid_python(), test_readthedocs_configuration_uses_reproducible_sphinx_build()

### Community 72 - "test_login_throttle.py"
Cohesion: 0.17
Nodes (10): clock(), test_another_username_is_not_affected(), test_counters_survive_a_restart(), test_existing_passwords_keep_working(), test_one_address_guessing_many_usernames_is_slowed(), test_sixth_failure_waits_and_the_password_is_not_checked(), test_success_resets_the_username_counter(), test_the_wait_doubles_then_ends() (+2 more)

### Community 73 - "test_backend_contract_fixture"
Cohesion: 0.21
Nodes (13): cJSON_GetArraySize(), cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput() (+5 more)

### Community 74 - "pytest"
Cohesion: 0.23
Nodes (8): test_gateway_key_joins_only_its_own_class(), _on(), test_generated_graph_is_valid_meaningful_and_covers_impress_components(), test_generated_output_has_no_local_paths_or_secret_values(), test_official_graphify_cli_is_available_when_graph_workflow_runs(), test_workflow_actions_are_pinned_and_generation_is_before_publish(), test_workflow_has_required_trigger_permissions_cache_and_recursion_guards(), _workflow()

### Community 75 - "re"
Cohesion: 0.11
Nodes (22): test_api_key_sent_as_header_not_in_uri_or_log(), _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_flushes_bounded_chunks_and_keeps_them_on_transport_errors(), test_c6_services_spi_while_wifi_is_down_with_a_bounded_batch(), test_clock_is_configurable_and_defaults_to_10_mhz(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+14 more)

### Community 76 - "test_manage_cli.py"
Cohesion: 0.16
Nodes (10): init_db(), main(), restore_super_admin(), _lock_out(), _restore(), _sql(), test_cli_exit_codes(), test_promotes_an_existing_account() (+2 more)

### Community 77 - "test_e2e_ota.py"
Cohesion: 0.34
Nodes (10): _advance(), _dep(), _deploy(), _prompt(), _sockets(), test_an_unhealthy_image_rolls_back_and_stops_the_rollout(), test_corrupt_download_is_refused_then_retried(), test_power_loss_mid_update_times_out_and_is_retried() (+2 more)

### Community 78 - "test_admin_users.py"
Cohesion: 0.12
Nodes (5): _import(), su(), test_create_user_field_limits(), test_csv_import_admin_rows_need_super_admin(), test_csv_import_inserts_valid_rows_and_reports_bad_ones()

### Community 79 - "on_ws_command"
Cohesion: 0.30
Nodes (13): handle_class_assignment(), on_ws_command(), clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame(), cJSON_GetNumberValue() (+5 more)

### Community 80 - "ui_tests/conftest.py"
Cohesion: 0.13
Nodes (5): Api, browser(), _free_port(), page(), server()

### Community 81 - "test_device_batch_dedup.py"
Cohesion: 0.23
Nodes (13): answer(), batch(), count(), q(), setup(), add_students(), test_distinct_students_and_questions_all_count(), test_inactive_quiz_and_closed_poll_skipped() (+5 more)

### Community 83 - "shutil"
Cohesion: 0.32
Nodes (4): _publish_graph_visualization(), setup(), _idf_command(), test_idf_docker_command_uses_init_and_skips_when_daemon_down()

### Community 84 - "gateway_sim.py"
Cohesion: 0.19
Nodes (5): answer(), join(), _marker(), _next_command(), test_a_quiz_runs_end_to_end_through_a_gateway()

### Community 85 - "test_user_lifecycle_api.py"
Cohesion: 0.19
Nodes (6): _row(), su(), test_allowed_actions_for_a_super_admin(), test_allowed_actions_for_an_admin(), test_hidden_actions_are_refused_by_the_server(), test_patch_edits_profile_only()

### Community 86 - "json"
Cohesion: 0.12
Nodes (14): _next_device_frame(), _project(), test_device_socket_receives_firmware_contract(), _idf_image_present(), append_coverage(), component_for(), enrich(), main() (+6 more)

### Community 88 - "FakeGitHub"
Cohesion: 0.19
Nodes (10): FakeGitHub, _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line(), test_inherited_issues_are_marked_with_their_line(), test_sync_changes_nothing_when_already_correct() (+2 more)

### Community 89 - "test_firmware_manager.py"
Cohesion: 0.26
Nodes (12): _artifact(), h(), _hub(), _push(), _set(), test_admin_only(), test_deletion_keeps_anything_a_device_needs(), test_deprecated_images_are_not_pushed_but_in_flight_updates_finish() (+4 more)

### Community 90 - "get"
Cohesion: 0.22
Nodes (6): _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), serve_frontend()

### Community 91 - "test_health.py"
Cohesion: 0.19
Nodes (7): health(), _dev(), test_heartbeat_stores_diagnostics_and_old_firmware_still_works(), get(), test_invalid_diagnostics_are_rejected(), test_precedence_offline_over_updating_over_error_over_degraded(), test_rules()

### Community 93 - "test_install_scripts.py"
Cohesion: 0.28
Nodes (8): _backend(), test_ci_runs_the_install_path(), test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets(), test_version_file_is_semver_and_matches_the_firmware(), _values()

### Community 94 - "test_device_limits.py"
Cohesion: 0.21
Nodes (6): cls(), _quiz(), test_backend_limits_match_the_firmware_frame(), test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons()

### Community 95 - "firmware_signing.py"
Cohesion: 0.20
Nodes (6): _der(), key_digest(), load_public_key(), _mgf1(), pss_verify(), _site_key()

### Community 96 - "test_gateway_autolink.py"
Cohesion: 0.36
Nodes (8): _class(), _gateway_of(), q(), _register(), test_explicit_classroom_code_still_assigns(), test_gateway_keeps_its_class_on_reregister(), test_non_gateway_registration_keeps_class_gateway(), test_second_gateway_takes_next_free_class()

### Community 97 - "test_ota_download_gating.py"
Cohesion: 0.36
Nodes (5): device(), dl(), test_download_requires_device_key(), test_no_pending_ota_means_no_download(), test_only_the_pushed_version_downloads()

### Community 98 - "websocket_linux.c"
Cohesion: 0.15
Nodes (3): log_error_if_nonzero(), main(), websocket_event_handler()

### Community 99 - "test_session_revocation.py"
Cohesion: 0.24
Nodes (8): _ok(), su(), test_admin_password_reset_logs_the_user_out(), test_open_teacher_socket_is_closed_on_deactivation(), test_own_password_change_keeps_only_the_current_session(), test_profile_edit_does_not_revoke(), test_reactivation_does_not_revive_old_tokens(), test_role_change_revokes_sessions()

### Community 100 - "_repo"
Cohesion: 0.28
Nodes (8): _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch(), test_the_branch_name_decides_the_line()

### Community 102 - "test_session_token_storage.py"
Cohesion: 0.24
Nodes (5): _scrub_raw_session_tokens(), _all_session_values(), test_legacy_raw_token_rows_revoked_and_scrubbed(), test_no_databases_tracked_in_git(), test_raw_token_not_stored_anywhere()

### Community 103 - "test_hardware_requirements.py"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub(), test_student_capacity_matches_on_hub_and_gateway()

### Community 104 - "test_fault_injection.py"
Cohesion: 0.24
Nodes (5): _stored(), q(), test_a_failed_commit_stores_nothing_and_the_retry_stores_once(), test_a_lost_response_makes_the_gateway_resend_harmlessly(), test_two_copies_racing_store_one_answer()

### Community 107 - "backend/tests/conftest.py"
Cohesion: 0.14
Nodes (8): auth(), client(), _drain_background_tasks(), login(), make_class(), make_user(), _reset_db(), upload_firmware()

### Community 112 - "migrate"
Cohesion: 0.29
Nodes (6): health(), _applied(), backup(), _db_file(), migrate(), schema_version()

### Community 134 - ".update"
Cohesion: 0.20
Nodes (8): link(), age(), push(), stale(), go(), set_pending(), go(), q()

### Community 156 - "test_class_create.py"
Cohesion: 0.28
Nodes (4): _stored(), q(), test_create_class_with_exam_dates_persists_them(), test_create_class_without_exam_dates()

### Community 167 - "test_firmware_upload.py"
Cohesion: 0.28
Nodes (5): _activity(), q(), test_firmware_upload_succeeds_and_is_logged(), test_s3_ota_push_prompts_gateway_and_logs(), link()

### Community 168 - "test_class_join.py"
Cohesion: 0.42
Nodes (6): _class(), _teacher(), test_co_faculty_cannot_delete_class(), test_join_adds_co_faculty_and_keeps_owner(), test_join_errors(), test_join_is_idempotent_and_owner_join_is_noop()

### Community 169 - "check"
Cohesion: 0.28
Nodes (4): check(), failed(), _free(), prune()

### Community 170 - "test_firmware.py"
Cohesion: 0.32
Nodes (4): _open(), test_invalid_upload_is_explained(), test_signature_status_is_shown(), test_upload_approve_and_push_from_modules()

## Knowledge Gaps
- **1 isolated node(s):** `ASAN_OPTIONS`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1142 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **130 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `select()` connect `select` to `User`, `test_auth_sessions.py`, `main.py`, `istnow`, `services/deployments.py`, `firmware.py`, `ClassSession`, `test_quiz_timer.py`, `students.py`, `QuizAnswer`, `test_class_create.py`, `routers/auth.py`, `test_device_api.py`, `quizzes.py`, `app/auth.py`, `test_firmware_upload.py`, `check`, `test_maintenance_windows.py`, `test_question_import.py`, `models.py`, `test_class_import.py`, `test_quiz_poll_lifecycle.py`, `test_firmware_registry.py`, `test_run_tests.py`, `run_tests.py`, `tests/test_student_modules.py`, `routers/deployments.py`, `test_device_keys.py`, `test_manage_cli.py`, `test_device_batch_dedup.py`, `test_health.py`, `test_gateway_autolink.py`, `test_fault_injection.py`, `refresh_session_activity`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 165 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 165 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ASAN_OPTIONS` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `User` be split into smaller, more focused modules?**
  _Cohesion score 0.04685942173479561 - nodes in this community are weakly interconnected._
- **Why does `istnow()` connect `istnow` to `User`, `test_auth_sessions.py`, `main.py`, `.update`, `migrations.py`, `services/deployments.py`, `firmware.py`, `test_quiz_timer.py`, `select`, `test_core_utils.py`, `routers/auth.py`, `test_ws_auth.py`, `test_device_api.py`, `quizzes.py`, `app/auth.py`, `datetime`, `models.py`, `tests/test_student_modules.py`, `routers/deployments.py`, `test_login_throttle.py`, `test_e2e_ota.py`, `test_session_token_storage.py`, `test_fault_injection.py`, `refresh_session_activity`, `migrate`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 130 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 130 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_auth_sessions.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12648221343873517 - nodes in this community are weakly interconnected._