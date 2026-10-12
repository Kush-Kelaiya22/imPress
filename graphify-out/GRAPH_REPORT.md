# Graph Report - imPress  (2026-10-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3018 nodes · 8312 edges · 205 communities (88 shown, 117 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 1302 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `74dc10ba`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 108
- Community 109
- Community 110
- Community 113
- Community 119
- Community 202
- Community 203
- Community 204

## God Nodes (most connected - your core abstractions)
1. `select()` - 159 edges
2. `User` - 126 edges
3. `login()` - 110 edges
4. `auth()` - 107 edges
5. `istnow()` - 100 edges
6. `EspDevice` - 96 edges
7. `ClassSession` - 84 edges
8. `_post()` - 74 edges
9. `log_activity()` - 66 edges
10. `functions()` - 50 edges

## Surprising Connections (you probably didn't know these)
- `test_every_setting_is_documented()` --uses--> `Settings`  [INFERRED]
  tests/test_docs_consistency.py → backend/app/config.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_device_keys.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_auth_sessions.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_create.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_gateway_autolink.py → run_tests.py

## Import Cycles
- None detected.

## Communities (205 total, 117 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (77): Admin router: user management, class (classroom) management & enrollment,…, ActivityLogResponse, AdminUserCreate, BulkStudentRegister, ClassAssignTeacher, ClassCreate, ClassDevicesResponse, ClassFacultyUpdate (+69 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (76): cJSON_Hooks, add_item_to_array(), add_item_to_object(), cJSON, case_insensitive_strcmp(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddBoolToObject() (+68 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (73): auth(), login(), fixture, su(), parametrize, Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py…, _session_row(), q() (+65 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (73): json, apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog() (+65 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (66): config, nvs_handle_t, cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str() (+58 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (69): api_key_ok(), Constant-time device API key comparison., commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, authorize(), _by_mac(), caller_for_key() (+61 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (29): cjson, esp_efuse, esp_err, esp_event, esp_idf_version, esp_log, esp_now, esp_random (+21 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (71): Poll, admin_class_devices(), admin_create_class(), admin_delete_class(), admin_get_module(), admin_link_device(), admin_list_classes(), admin_list_modules() (+63 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (65): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+57 more)

### Community 10 - "Community 10"
Cohesion: 0.05
Nodes (52): playwright_sync_api, init_env(), Path, Create or complete backend/.env from backend/.env.example (#42). The public…, Returns the names of the secrets it generated., sys, tempfile, time (+44 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (63): errno, esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client_config_t, esp_websocket_client_handle_t (+55 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (59): DeploymentTarget, FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., _act(), cancel_deployment(), create_deployment(), deployment_dict() (+51 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (52): AsyncConnection, AsyncEngine, _add_columns(), add_device_keys(), add_diagnostics_columns(), add_firmware_signer(), add_quiz_question_started_at(), add_unique_constraints() (+44 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (43): asyncio, Activity logging service — records all significant actions., JWT + server-side session authentication helpers., Require admin or super_admin role., Require super_admin role., Require teacher, admin, or super_admin role., require_admin(), require_super_admin() (+35 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (47): adc_oneshot, crypto, esp_crt_bundle, esp_heap_caps, esp_http_client, esp_netif, esp_ota_handle_t, esp_ota_ops (+39 more)

### Community 16 - "Community 16"
Cohesion: 0.07
Nodes (46): check_secure(), insecure_settings(), Names of settings still at their public, repo-published defaults., Refuse to run with published secrets unless explicitly in DEBUG mode., Settings, client(), _drain_background_tasks(), fixture (+38 more)

### Community 17 - "Community 17"
Cohesion: 0.08
Nodes (49): BaseType_t, spi_slave_transaction_t, queue_slot(), ready_update(), spi_post_trans_cb(), spi_slave_init(), spi_slave_read(), spi_slave_send() (+41 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (47): argparse, _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts… (+39 more)

### Community 19 - "Community 19"
Cohesion: 0.09
Nodes (50): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get() (+42 more)

### Community 20 - "Community 20"
Cohesion: 0.09
Nodes (49): log_activity(), AsyncSession, Write one activity log entry., Student, StudentEnrollment, bulk_register_students(), _enroll_student(), enroll_students_bulk() (+41 more)

### Community 21 - "Community 21"
Cohesion: 0.09
Nodes (43): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), make_image(), _artifact(), _hub(), _push(), #36: firmware version manager: approval, deprecation, retention, usage., _set() (+35 more)

### Community 22 - "Community 22"
Cohesion: 0.15
Nodes (46): cJSON_AddItemToObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc(), apply_patch(), cJSON (+38 more)

### Community 23 - "Community 23"
Cohesion: 0.10
Nodes (40): advance(), deadline(), finish(), AsyncSession, datetime, Advance or end every timed quiz whose time is up. The caller commits, then…, When the current question (per_question) or the whole quiz (total) runs out;…, Seconds a module has for the question it is about to show: the per-question… (+32 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (38): make_class(), make_user(), Create a user through the admin API; returns (user_id, auth headers)., Create a class via /api/admin/classes; optionally activate it., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password() (+30 more)

### Community 25 - "Community 25"
Cohesion: 0.09
Nodes (38): create_session(), generate_session_token(), get_current_user(), get_current_user_light(), _load_session_by_hash(), AsyncSession, Request, Validate a session token. Returns (session, user, error_code) where error_code… (+30 more)

### Community 26 - "Community 26"
Cohesion: 0.13
Nodes (37): Any, ClassSession, activate_class(), class_presence(), _count_students(), create_class(), deactivate_class(), delete_class() (+29 more)

### Community 27 - "Community 27"
Cohesion: 0.09
Nodes (35): A student module seen on a gateway's mesh (#40): presence, not location. One…, StudentModule, class_id_for_device(), class_modules(), _device_to_dict(), presence_snapshot(), presence_sweep_loop(), _push_after_commit() (+27 more)

### Community 28 - "Community 28"
Cohesion: 0.12
Nodes (35): Course, create_course(), delete_course(), get_course(), list_courses(), AsyncSession, delete, get (+27 more)

### Community 29 - "Community 29"
Cohesion: 0.07
Nodes (23): Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, env(), fixture, #21: co-faculty can run quizzes/polls for their class; outsiders still can't., _teacher(), parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student… (+15 more)

### Community 30 - "Community 30"
Cohesion: 0.10
Nodes (34): msg_t, handle_c6_frame(), heartbeat_task(), on_student_message(), esp_now_recv_info_t, msg_type_t, extract_enrollment(), find_or_create_student() (+26 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (33): QuizAnswer, _count(), q(), _fk_violations(), q(), _insert_twice(), go(), #41: the database enforces its own integrity (foreign keys, uniqueness), and… (+25 more)

### Community 32 - "Community 32"
Cohesion: 0.09
Nodes (21): answer(), Gateway, join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., _marker() (+13 more)

### Community 33 - "Community 33"
Cohesion: 0.13
Nodes (33): display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown(), display_show_provision_state(), display_show_question(), display_show_result() (+25 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (30): create_access_token(), Legacy JWT creation (kept for device registration / backward compat)., _parse_time(), Convert "HH:MM" → minutes since midnight. Returns None if malformed., Two time slots overlap when neither fully precedes the other. Overnight / wrap-…, Two classes only clash if they run in the same semester/window. Priority:…, _same_academic_window(), _slots_conflict() (+22 more)

### Community 35 - "Community 35"
Cohesion: 0.09
Nodes (30): init_db(), Create missing tables and apply pending migrations (stops on failure)., _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), health() (+22 more)

### Community 36 - "Community 36"
Cohesion: 0.14
Nodes (29): msg_t, spi_slot_fifo_t, crc16_ccitt(), json_get_string(), msg_decode(), msg_verify_crc(), spi_record_read(), spi_record_write() (+21 more)

### Community 37 - "Community 37"
Cohesion: 0.09
Nodes (28): import_classes_csv(), Create courses and their sections from a CSV. All-or-nothing: any invalid row…, ClassImportRow, apply_class_import(), _changes(), export_rows(), plan_class_import(), AsyncSession (+20 more)

### Community 38 - "Community 38"
Cohesion: 0.22
Nodes (30): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+22 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (24): esp_app_desc, esp_bit_defs, esp_mac, event_groups, cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), esp_err_t (+16 more)

### Community 41 - "Community 41"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 42 - "Community 42"
Cohesion: 0.18
Nodes (25): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+17 more)

### Community 43 - "Community 43"
Cohesion: 0.19
Nodes (26): Quiz, User, class_import_template(), Example file with every column. Public: it contains no data., create_quiz(), get_quiz(), import_question_csv(), list_quizzes() (+18 more)

### Community 44 - "Community 44"
Cohesion: 0.20
Nodes (26): buffer_skip_whitespace(), cJSON_bool, cJSON_Compare(), cJSON_ParseWithLength(), cJSON_ParseWithLengthOpts(), cJSON_ParseWithOpts(), cJSON_PrintPreallocated(), compare_double() (+18 more)

### Community 45 - "Community 45"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 46 - "Community 46"
Cohesion: 0.16
Nodes (22): _activity(), q(), _device(), q(), Gateway-facing device API (routers/device.py) + presence service…, _register(), test_class_presence_snapshot_walks_gateway_tree(), resolve() (+14 more)

### Community 47 - "Community 47"
Cohesion: 0.13
Nodes (15): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+7 more)

### Community 48 - "Community 48"
Cohesion: 0.11
Nodes (19): One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent…, go(), link(), age(), push(), stale(), go(), parametrize (+11 more)

### Community 49 - "Community 49"
Cohesion: 0.17
Nodes (20): functions(), mentions(), {name: body_text} for every top-level function definition in a C file., #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch() (+12 more)

### Community 50 - "Community 50"
Cohesion: 0.14
Nodes (18): platform, CaseResult, fmt_secs(), _idf_image_present(), main(), markdown_report(), Paint, parse_host_output() (+10 more)

### Community 51 - "Community 51"
Cohesion: 0.12
Nodes (20): posix_only, discover(), _idf_command(), Run `cmd` and return (exit code, combined output, abort reason). Output is read…, run_streaming(), test_frontend_is_installed_from_its_lockfile(), skipif, Unit tests for the root test runner (run_tests.py). (+12 more)

### Community 52 - "Community 52"
Cohesion: 0.13
Nodes (20): make_student(), test_attendance_paths(), count(), fixture, Smoke steps 1-5: a class whose gateway registered with its room code., setup(), _csv(), fixture (+12 more)

### Community 53 - "Community 53"
Cohesion: 0.13
Nodes (21): _missing(), missing_packages(), parse_coverage(), parse_junit(), Path, _pytest_suite(), Test cases from a pytest JUnit XML file., Distribution names from a requirements file, following -r includes. (+13 more)

### Community 54 - "Community 54"
Cohesion: 0.27
Nodes (20): _age(), q(), _batch(), beat(), join(), leave(), _modules(), #40: the student module inventory. Modules seen on a gateway's mesh are listed… (+12 more)

### Community 55 - "Community 55"
Cohesion: 0.12
Nodes (10): ConnectionManager, WebSocket, Send a JSON message to ALL connections in a class room (teachers + devices)., Send a JSON message only to connections matching the given role., Alias for broadcast_to_class., Manages WebSocket connections grouped by class ID. Teachers connect to manage…, FakeWS, test_manager_disconnect_frees_empty_rooms() (+2 more)

### Community 56 - "Community 56"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 57 - "Community 57"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 58 - "Community 58"
Cohesion: 0.14
Nodes (10): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub() (+2 more)

### Community 59 - "Community 59"
Cohesion: 0.25
Nodes (17): batch_add(), batch_flush(), batch_flush_needed(), batch_init(), cJSON, msg_type_t, heartbeat_task(), item_is_heartbeat() (+9 more)

### Community 60 - "Community 60"
Cohesion: 0.25
Nodes (16): _advance(), _dep(), _deploy(), _prompt(), fixture, #43 end to end: a firmware release reaches three rooms through the staged…, Three rooms, each with a v2.1.0 gateway; a c6 2.2.0 image approved., Read this room's socket until the gateway's own OTA prompt. (+8 more)

### Community 61 - "Community 61"
Cohesion: 0.27
Nodes (13): student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join(), student_set_leave(), student_set_root_uptime() (+5 more)

### Community 62 - "Community 62"
Cohesion: 0.15
Nodes (10): main(), Fail clearly if committed Graphify output is incomplete, stale, or unsafe., source_commit(), shutil, subprocess, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards() (+2 more)

### Community 63 - "Community 63"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 64 - "Community 64"
Cohesion: 0.30
Nodes (14): _device(), q(), _push(), parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report(), test_applied_with_another_version_is_not_success(), test_applied_with_the_pushed_version_completes_the_update() (+6 more)

### Community 65 - "Community 65"
Cohesion: 0.15
Nodes (8): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), #13: S3 OTA — rollback protection and no reboot when nothing is installed., test_detach_unregisters_reconnect_handler_before_disconnecting(), test_new_image_marked_valid_only_after_mesh_and_spi_init(), test_only_a_successful_install_reboots()

### Community 66 - "Community 66"
Cohesion: 0.20
Nodes (11): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+3 more)

### Community 67 - "Community 67"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10: only a super admin can grant/remove admin-level roles; roles are a closed…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 68 - "Community 68"
Cohesion: 0.24
Nodes (13): cJSON_Parse(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput(), msg_t, frame_of() (+5 more)

### Community 69 - "Community 69"
Cohesion: 0.16
Nodes (10): #29: guards for the S3 <-> C6 link as ported from v3…, _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_student_count_comes_from_join_and_leave_only(), test_c6_validates_received_slots(), test_master_drops_a_payload_only_after_a_successful_transfer(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+2 more)

### Community 70 - "Community 70"
Cohesion: 0.23
Nodes (11): append_coverage(), component_for(), enrich(), main(), node_id(), Path, Build imPress's deterministic Graphify graph and enrich non-code coverage.…, Latest commit that changed input, rather than a graph-only bot commit. (+3 more)

### Community 71 - "Community 71"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 72 - "Community 72"
Cohesion: 0.18
Nodes (12): class_websocket(), _device_key_ok(), websocket, The shared key (unless IMPRESS_DEVICE_KEYS_REQUIRED) or an active-able per-…, Refresh presence for the device that spoke over WS. The C6's primary heartbeat…, Validate a login session token for WebSocket auth. Returns the User or None.…, WebSocket endpoint for real-time class communication. Connect with:…, _touch_device_on_message() (+4 more)

### Community 73 - "Community 73"
Cohesion: 0.37
Nodes (12): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+4 more)

### Community 74 - "Community 74"
Cohesion: 0.17
Nodes (12): hash_password(), admin_import_students_csv(), create_user(), import_users_csv(), UploadFile, Admin sets a new password for a user (forgot-password flow)., Only a super admin may grant (or take away) admin-level roles., Admin creates a teacher or admin account. Super admin can also create admins. (+4 more)

### Community 75 - "Community 75"
Cohesion: 0.24
Nodes (10): _sha256_hex(), Older versions stored the raw bearer token in user_sessions.session_token. Any…, _scrub_raw_session_tokens(), _all_session_values(), skipif, #12: raw bearer tokens are never persisted; legacy raw rows are revoked., test_legacy_raw_token_rows_revoked_and_scrubbed(), insert_legacy() (+2 more)

### Community 76 - "Community 76"
Cohesion: 0.27
Nodes (8): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat()

### Community 77 - "Community 77"
Cohesion: 0.20
Nodes (9): push_device_status(), push_poll_to_mesh(), push_quiz_to_mesh(), push_student_data(), Bridge service: connects ESP device data to WebSocket clients. This service…, Push student device data (heartbeats, answers, votes) to teacher dashboard., Push individual device status update., Push quiz question through WebSocket → C6 → SPI → S3 → mesh → students. (+1 more)

### Community 78 - "Community 78"
Cohesion: 0.31
Nodes (9): device(), set_pending(), go(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download() (+1 more)

### Community 79 - "Community 79"
Cohesion: 0.29
Nodes (8): _create(), ctx(), fixture, parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 80 - "Community 80"
Cohesion: 0.27
Nodes (8): Security review (#16 of the v2.1 brief): every route refuses a caller without…, 401/403, or 422 for the missing device-key header (a required `X-API-Key` is…, _refused(), _routes(), test_device_routes_reject_a_wrong_key(), test_every_route_needs_credentials(), fastapi_routing, importlib

### Community 81 - "Community 81"
Cohesion: 0.31
Nodes (8): _dev(), parametrize, #39: device health states from the latest heartbeat diagnostics., test_heartbeat_stores_diagnostics_and_old_firmware_still_works(), get(), test_invalid_diagnostics_are_rejected(), test_precedence_offline_over_updating_over_error_over_degraded(), test_rules()

### Community 82 - "Community 82"
Cohesion: 0.22
Nodes (5): live(), fixture, parametrize, #9: poll vote / quiz answer endpoints require the device key, a registered…, test_vote_and_answer_require_device_key()

### Community 83 - "Community 83"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 84 - "Community 84"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 86 - "Community 86"
Cohesion: 0.50
Nodes (4): health(), datetime, Device health states (#39), computed from the latest heartbeat. Rules, in order…, (state, reasons) for one device.

### Community 88 - "Community 88"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

### Community 89 - "Community 89"
Cohesion: 0.67
Nodes (3): SQLite ignores foreign keys unless asked, per connection., _sqlite_pragmas(), listens_for

### Community 91 - "Community 91"
Cohesion: 0.67
Nodes (3): Popen, Terminate the child and everything it started (npm, ninja, docker run)., _stop()

## Knowledge Gaps
- **49 isolated node(s):** `StaleRender`, `run_student_set.sh script`, `run_ws_command.sh script`, `run.sh script`, `run_mesh_dedup.sh script` (+44 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 906 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **117 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `Community 27` to `Community 0`, `Community 2`, `Community 6`, `Community 8`, `Community 12`, `Community 13`, `Community 14`, `Community 19`, `Community 23`, `Community 25`, `Community 32`, `Community 34`, `Community 35`, `Community 38`, `Community 43`, `Community 46`, `Community 48`, `Community 54`, `Community 60`, `Community 72`, `Community 75`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `select()` connect `Community 8` to `Community 2`, `Community 6`, `Community 12`, `Community 16`, `Community 19`, `Community 20`, `Community 21`, `Community 23`, `Community 24`, `Community 25`, `Community 26`, `Community 27`, `Community 28`, `Community 31`, `Community 32`, `Community 35`, `Community 37`, `Community 38`, `Community 42`, `Community 43`, `Community 45`, `Community 46`, `Community 50`, `Community 51`, `Community 52`, `Community 53`, `Community 54`, `Community 64`, `Community 72`, `Community 74`, `Community 75`, `Community 81`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `login()` connect `Community 2` to `Community 16`, `Community 18`, `Community 21`, `Community 23`, `Community 24`, `Community 28`, `Community 29`, `Community 31`, `Community 32`, `Community 38`, `Community 42`, `Community 45`, `Community 46`, `Community 48`, `Community 52`, `Community 54`, `Community 60`, `Community 64`, `Community 67`, `Community 75`, `Community 78`, `Community 79`, `Community 81`, `Community 82`, `Community 85`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 155 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 155 INFERRED edges - model-reasoned connections that need verification._
- **Are the 110 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 110 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `run_student_set.sh script`, `run_ws_command.sh script` to the rest of the system?**
  _49 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.04647160068846816 - nodes in this community are weakly interconnected._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
