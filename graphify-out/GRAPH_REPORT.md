# Graph Report - imPress  (2026-10-13)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3134 nodes · 8596 edges · 228 communities (106 shown, 122 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1326 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `065f8e1a`
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
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 130
- Community 136
- Community 137
- Community 224
- Community 225
- Community 226
- Community 227

## God Nodes (most connected - your core abstractions)
1. `select()` - 157 edges
2. `User` - 139 edges
3. `login()` - 121 edges
4. `auth()` - 119 edges
5. `istnow()` - 100 edges
6. `EspDevice` - 96 edges
7. `ClassSession` - 86 edges
8. `_post()` - 76 edges
9. `make_user()` - 73 edges
10. `log_activity()` - 68 edges

## Surprising Connections (you probably didn't know these)
- `test_every_setting_is_documented()` --uses--> `Settings`  [INFERRED]
  tests/test_docs_consistency.py → backend/app/config.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_auth_sessions.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_create.py → run_tests.py
- `get()` --calls--> `select()`  [INFERRED]
  backend/tests/test_health.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_device_api.py → run_tests.py

## Import Cycles
- None detected.

## Communities (228 total, 122 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (84): _cleanup_once(), Delete sessions that are hard-expired, idle-expired, or revoked. Returns the…, auth(), login(), fixture, su(), Smoke tests: the app boots on an empty DB and its basic contracts hold., test_seeded_super_admin_can_log_in() (+76 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (98): log_activity(), AsyncSession, Write one activity log entry., hash_password(), Revoke every session of a user (except `keep_id`), in the caller's transaction…, revoke_user_sessions(), User, admin_class_devices() (+90 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (87): verify_password(), activity_ping(), login(), logout(), me(), AsyncSession, get, put (+79 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (63): config, nvs_handle_t, cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str() (+55 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (66): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+58 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (58): Activity logging service — records all significant actions., Base, get_db(), init_db(), Async SQLAlchemy engine and session factory., SQLite ignores foreign keys unless asked, per connection., Dependency that yields an async DB session., Create missing tables and apply pending migrations (stops on failure). (+50 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (64): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+56 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (63): errno, esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client_config_t, esp_websocket_client_handle_t (+55 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (54): AsyncConnection, AsyncEngine, _add_columns(), add_device_keys(), add_diagnostics_columns(), add_firmware_signer(), add_quiz_question_started_at(), add_unique_constraints() (+46 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (51): make_class(), make_student(), Create a class via /api/admin/classes; optionally activate it., Classes (routers/classes.py, admin class routes) and courses…, test_activate_deactivate_toggle(), test_back_to_back_slots_do_not_warn(), test_class_codes_are_unique(), test_join_requires_known_active_code() (+43 more)

### Community 11 - "Community 11"
Cohesion: 0.07
Nodes (50): Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), make_image(), _next_device_frame(), _project(), Contract test: frames the C6 gateway receives on its device WebSocket (#3). The…, The single frame an action broadcasts; it must carry a firmware event. Reads… (+42 more)

### Community 12 - "Community 12"
Cohesion: 0.10
Nodes (53): Any, ClassSession, admin_create_class(), admin_list_classes(), admin_set_class_faculty(), admin_update_class(), assign_teacher(), _class_to_response() (+45 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (44): adc_oneshot, crypto, esp_crt_bundle, esp_err, esp_event, esp_heap_caps, esp_http_client, esp_idf_version (+36 more)

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (47): make_user(), Create a user through the admin API; returns (user_id, auth headers)., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password(), test_admin_password_reset(), test_create_user_field_limits() (+39 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (49): create_access_token(), Legacy JWT creation (kept for device registration / backward compat)., authorize(), DeviceCaller, Who is calling: the shared key (device None) or one device's own key., ActivityLog, EspDevice, _broadcast_participation() (+41 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (44): advance(), answer_closed(), deadline(), finish(), AsyncSession, datetime, Quiz timing (#73): advance `per_question` quizzes and end `total` quizzes when…, Advance or end every timed quiz whose time is up. The caller commits, then… (+36 more)

### Community 17 - "Community 17"
Cohesion: 0.14
Nodes (48): cJSON_AddItemToArray(), cJSON_AddItemToObject(), cJSON_CreateObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc() (+40 more)

### Community 18 - "Community 18"
Cohesion: 0.08
Nodes (45): _count(), q(), _fk_violations(), q(), _insert_twice(), go(), #41: the database enforces its own integrity (foreign keys, uniqueness), and…, test_admin_class_delete_detaches_modules_linked_to_its_enrollments() (+37 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (43): Course, export_classes_csv(), Every course section in the import layout. Cells that would start a spreadsheet…, create_course(), delete_course(), get_course(), list_courses(), AsyncSession (+35 more)

### Community 20 - "Community 20"
Cohesion: 0.12
Nodes (38): cJSON_Hooks, buffer_skip_whitespace(), cJSON_bool, cJSON_AddBoolToObject(), cJSON_Compare(), cJSON_CreateBool(), cJSON_InitHooks(), cJSON_Minify() (+30 more)

### Community 21 - "Community 21"
Cohesion: 0.06
Nodes (31): _parse_time(), Convert "HH:MM" → minutes since midnight. Returns None if malformed., Two time slots overlap when neither fully precedes the other. Overnight / wrap-…, Two classes only clash if they run in the same semester/window. Priority:…, _same_academic_window(), _slots_conflict(), normalize_version(), as_ist() (+23 more)

### Community 22 - "Community 22"
Cohesion: 0.10
Nodes (41): DeploymentTarget, FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., active_target(), advance(), advance_all(), cancel() (+33 more)

### Community 23 - "Community 23"
Cohesion: 0.09
Nodes (11): cjson, read_file(), main(), msg_t, on_student_message(), protocol, stdbool, stddef (+3 more)

### Community 24 - "Community 24"
Cohesion: 0.12
Nodes (35): esp_efuse, esp_mac, esp_random, display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown() (+27 more)

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (33): asyncio, class_modules(), _device_to_dict(), _log(), mark_offline(), presence_snapshot(), push_presence(), datetime (+25 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (37): commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, Quiz, Example file with every column. Public: it contains no data., create_quiz(), get_quiz(), import_question_csv() (+29 more)

### Community 27 - "Community 27"
Cohesion: 0.09
Nodes (24): esp_app_desc, esp_bit_defs, esp_log, esp_now, esp_wifi, event_groups, esp_event_base_t, ws_client_send() (+16 more)

### Community 28 - "Community 28"
Cohesion: 0.12
Nodes (32): app_main(), batch_add(), batch_flush_needed(), batch_init(), cJSON, msg_type_t, heartbeat_task(), item_is_heartbeat() (+24 more)

### Community 29 - "Community 29"
Cohesion: 0.08
Nodes (21): answer(), Gateway, join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., _marker() (+13 more)

### Community 30 - "Community 30"
Cohesion: 0.12
Nodes (33): approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get(), _latest_approved(), list_firmware() (+25 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (32): Student, bulk_create_students(), _create_one(), create_student(), deactivate_student(), get_student(), hard_delete_student(), import_students_csv() (+24 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (33): batch_flush(), add_item_to_object(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddFalseToObject(), cJSON_AddItemToObjectCS(), cJSON_AddNullToObject(), cJSON_AddNumberToObject() (+25 more)

### Community 33 - "Community 33"
Cohesion: 0.09
Nodes (27): _sha256_hex(), Older versions stored the raw bearer token in user_sessions.session_token. Any…, _scrub_raw_session_tokens(), UserSession, Session housekeeping: periodic cleanup of expired server-side sessions. Expired…, Background task: periodically delete expired / revoked sessions., session_cleanup_loop(), _dev() (+19 more)

### Community 34 - "Community 34"
Cohesion: 0.21
Nodes (31): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+23 more)

### Community 35 - "Community 35"
Cohesion: 0.12
Nodes (29): add_item_to_array(), cJSON, case_insensitive_strcmp(), cJSON_AddItemReferenceToArray(), cJSON_AddItemReferenceToObject(), cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive() (+21 more)

### Community 37 - "Community 37"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 38 - "Community 38"
Cohesion: 0.09
Nodes (18): cls(), fixture, parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student…, test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons() (+10 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (23): ClassImportReport, ClassImportRow, All-or-nothing: any invalid row means nothing is imported., apply_class_import(), _changes(), plan_class_import(), AsyncSession, CSV → courses and their sections (class sessions) (#32). One row = one section… (+15 more)

### Community 40 - "Community 40"
Cohesion: 0.14
Nodes (25): queue_slot(), ready_update(), spi_slave_init(), esp_err_t, spi_slave_transaction_t, TickType_t, clobber_stack(), gpio_config() (+17 more)

### Community 41 - "Community 41"
Cohesion: 0.12
Nodes (17): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+9 more)

### Community 42 - "Community 42"
Cohesion: 0.11
Nodes (24): create_session(), generate_session_token(), get_current_user(), get_current_user_light(), _load_session_by_hash(), AsyncSession, Request, JWT + server-side session authentication helpers. (+16 more)

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (23): One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent…, go(), link(), age(), wire(), later(), go(), link() (+15 more)

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 45 - "Community 45"
Cohesion: 0.15
Nodes (23): BaseType_t, spi_slave_transaction_t, spi_post_trans_cb(), spi_slave_send(), SemaphoreHandle_t, xSemaphoreGive(), xSemaphoreGiveFromISR(), xSemaphoreTake() (+15 more)

### Community 46 - "Community 46"
Cohesion: 0.15
Nodes (21): cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), _store_dev_key(), esp_err_t, esp_event_base_t, _download_and_apply(), _firmware_check() (+13 more)

### Community 47 - "Community 47"
Cohesion: 0.14
Nodes (21): argparse, _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts… (+13 more)

### Community 48 - "Community 48"
Cohesion: 0.17
Nodes (20): functions(), mentions(), {name: body_text} for every top-level function definition in a C file., #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch() (+12 more)

### Community 49 - "Community 49"
Cohesion: 0.14
Nodes (18): platform, CaseResult, fmt_secs(), _idf_image_present(), main(), markdown_report(), Paint, parse_host_output() (+10 more)

### Community 50 - "Community 50"
Cohesion: 0.13
Nodes (20): _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), health(), get, Request (+12 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (21): presence_sweep_loop(), Mark stale devices offline. Returns number of transitions logged., Background task: periodically sweep and log offline transitions., _sweep_once(), module_to_dict(), observe(), AsyncSession, datetime (+13 more)

### Community 52 - "Community 52"
Cohesion: 0.13
Nodes (19): posix_only, discover(), _idf_command(), Run `cmd` and return (exit code, combined output, abort reason). Output is read…, run_streaming(), skipif, Unit tests for the root test runner (run_tests.py)., test_closed_output_pipe_exits_quietly() (+11 more)

### Community 53 - "Community 53"
Cohesion: 0.13
Nodes (21): _missing(), missing_packages(), parse_coverage(), parse_junit(), Path, _pytest_suite(), Test cases from a pytest JUnit XML file., Distribution names from a requirements file, following -r includes. (+13 more)

### Community 54 - "Community 54"
Cohesion: 0.27
Nodes (20): _age(), q(), _batch(), beat(), join(), leave(), _modules(), #40: the student module inventory. Modules seen on a gateway's mesh are listed… (+12 more)

### Community 55 - "Community 55"
Cohesion: 0.20
Nodes (19): _act(), cancel_deployment(), create_deployment(), deployment_dict(), DeploymentCreate, _get(), get_deployment(), list_deployments() (+11 more)

### Community 56 - "Community 56"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 57 - "Community 57"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 58 - "Community 58"
Cohesion: 0.28
Nodes (18): _beat(), _device(), q(), _key(), #66: per-device keys. Devices register with the shared key and are issued their…, _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out() (+10 more)

### Community 59 - "Community 59"
Cohesion: 0.22
Nodes (17): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, adopt_legacy_files(), artifact_file(), artifact_path(), AsyncSession, Path, UploadFile (+9 more)

### Community 60 - "Community 60"
Cohesion: 0.13
Nodes (13): client(), _drain_background_tasks(), fixture, TestClient on an empty database (the app seeds the super admin)., _reset_db(), _fresh_settings(), #11: no working public credentials or debug leaks by default., test_cors_only_configured_origins() (+5 more)

### Community 61 - "Community 61"
Cohesion: 0.19
Nodes (14): Build structurally valid ESP-IDF app images for tests (real header layout, app…, _digest(), h(), fixture, #66 (2/3): signed firmware. The verifier is checked against images signed by…, site_key(), test_a_foreign_key_is_refused_but_a_second_signature_by_the_site_key_counts(), test_an_unreadable_site_key_is_reported() (+6 more)

### Community 62 - "Community 62"
Cohesion: 0.15
Nodes (16): _me(), fixture, parametrize, At least one active super admin always remains (#116). The original failure: a…, The original lockout path: PUT with is_active=false on yourself (#116, #119)., Two super admins disabling each other at the same moment: one must fail., su(), test_concurrent_mutual_deactivation_leaves_one_super_admin() (+8 more)

### Community 63 - "Community 63"
Cohesion: 0.20
Nodes (16): msg_t, json_get_string(), msg_decode(), msg_verify_crc(), spi_record_read(), spi_record_write(), crc_ref(), frame_vote() (+8 more)

### Community 64 - "Community 64"
Cohesion: 0.18
Nodes (14): playwright_sync_api, login(), #51: only the latest navigation renders., test_normal_navigation_and_in_page_rerender_still_work(), test_quick_navigation_is_not_overwritten_by_a_slower_page(), #73: the class page offers Next for every timing mode, and a quiz the server's…, test_timed_quiz_has_next_and_ends_on_the_timer(), #40: student modules that joined a gateway appear in the inventory, the class… (+6 more)

### Community 65 - "Community 65"
Cohesion: 0.15
Nodes (9): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat() (+1 more)

### Community 66 - "Community 66"
Cohesion: 0.24
Nodes (15): answer(), batch(), count(), q(), fixture, parametrize, #6: /api/device/batch validates and de-duplicates mesh answers/votes., setup() (+7 more)

### Community 67 - "Community 67"
Cohesion: 0.21
Nodes (15): cJSON_GetArraySize(), cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput() (+7 more)

### Community 68 - "Community 68"
Cohesion: 0.23
Nodes (15): mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main(), simulate(), test_dedup_window_and_wrap(), test_id_ignores_hops_but_not_content() (+7 more)

### Community 69 - "Community 69"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 70 - "Community 70"
Cohesion: 0.30
Nodes (14): _advance(), _dep(), _deploy(), _prompt(), fixture, #43 end to end: a firmware release reaches three rooms through the staged…, Three rooms, each with a v2.1.0 gateway; a c6 2.2.0 image approved., Read this room's socket until the gateway's own OTA prompt. (+6 more)

### Community 71 - "Community 71"
Cohesion: 0.30
Nodes (14): _device(), q(), _push(), parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report(), test_applied_with_another_version_is_not_success(), test_applied_with_the_pushed_version_completes_the_update() (+6 more)

### Community 72 - "Community 72"
Cohesion: 0.30
Nodes (14): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+6 more)

### Community 73 - "Community 73"
Cohesion: 0.15
Nodes (8): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), #13: S3 OTA — rollback protection and no reboot when nothing is installed., test_detach_unregisters_reconnect_handler_before_disconnecting(), test_new_image_marked_valid_only_after_mesh_and_spi_init(), test_only_a_successful_install_reboots()

### Community 74 - "Community 74"
Cohesion: 0.16
Nodes (9): main(), Fail clearly if committed Graphify output is incomplete, stale, or unsafe., source_commit(), subprocess, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards(), _workflow() (+1 more)

### Community 75 - "Community 75"
Cohesion: 0.20
Nodes (11): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+3 more)

### Community 76 - "Community 76"
Cohesion: 0.23
Nodes (13): api_key_ok(), Constant-time device API key comparison., _by_mac(), caller_for_key(), denial(), device_caller(), key_hash(), new_device_key() (+5 more)

### Community 77 - "Community 77"
Cohesion: 0.19
Nodes (13): _der(), key_digest(), load_public_key(), _mgf1(), pss_verify(), Signed firmware images (#66): ESP-IDF Secure Boot V2 RSA-3072 signatures,…, (tag, start of content, end of content) of the DER element at pos., (n, e) from a PEM RSA public key (SubjectPublicKeyInfo, as written by… (+5 more)

### Community 78 - "Community 78"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10, #119: only a super admin can grant/remove admin-level roles; roles are a…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 79 - "Community 79"
Cohesion: 0.16
Nodes (10): #29: guards for the S3 <-> C6 link as ported from v3…, _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_student_count_comes_from_join_and_leave_only(), test_c6_validates_received_slots(), test_master_drops_a_payload_only_after_a_successful_transfer(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+2 more)

### Community 80 - "Community 80"
Cohesion: 0.23
Nodes (11): append_coverage(), component_for(), enrich(), main(), node_id(), Path, Build imPress's deterministic Graphify graph and enrich non-code coverage.…, Latest commit that changed input, rather than a graph-only bot commit. (+3 more)

### Community 81 - "Community 81"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 82 - "Community 82"
Cohesion: 0.35
Nodes (12): spi_slave_read(), spi_slot_fifo_t, crc16_ccitt(), spi_slot_decode(), spi_slot_encode(), spi_slot_fifo_drop(), spi_slot_fifo_init(), spi_slot_fifo_peek() (+4 more)

### Community 83 - "Community 83"
Cohesion: 0.20
Nodes (5): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #66: the signed-app profile and the scripts that build with it., re

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (9): importlib_util, stat, _backend(), #42: the documented install path: scripts, secrets, version, CI job., test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets() (+1 more)

### Community 85 - "Community 85"
Cohesion: 0.24
Nodes (10): tempfile, time, browser(), _free_port(), page(), fixture, Browser UI checks: a real backend on a temp database, driven by Playwright.…, A page that fails the test on any uncaught JS error; screenshot at the end. (+2 more)

### Community 86 - "Community 86"
Cohesion: 0.27
Nodes (9): check_secure(), insecure_settings(), Application configuration loaded from environment variables., Names of settings still at their public, repo-published defaults., Refuse to run with published secrets unless explicitly in DEBUG mode., Settings, BaseSettings, pydantic_settings (+1 more)

### Community 87 - "Community 87"
Cohesion: 0.20
Nodes (9): push_device_status(), push_poll_to_mesh(), push_quiz_to_mesh(), push_student_data(), Bridge service: connects ESP device data to WebSocket clients. This service…, Push student device data (heartbeats, answers, votes) to teacher dashboard., Push individual device status update., Push quiz question through WebSocket → C6 → SPI → S3 → mesh → students. (+1 more)

### Community 88 - "Community 88"
Cohesion: 0.42
Nodes (9): _class(), _gateway_of(), q(), #17: registration must not steal a class's gateway link., _register(), test_explicit_classroom_code_still_assigns(), test_gateway_keeps_its_class_on_reregister(), test_non_gateway_registration_keeps_class_gateway() (+1 more)

### Community 89 - "Community 89"
Cohesion: 0.31
Nodes (9): device(), set_pending(), go(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download() (+1 more)

### Community 90 - "Community 90"
Cohesion: 0.27
Nodes (8): Security review (#16 of the v2.1 brief): every route refuses a caller without…, 401/403, or 422 for the missing device-key header (a required `X-API-Key` is…, _refused(), _routes(), test_device_routes_reject_a_wrong_key(), test_every_route_needs_credentials(), fastapi_routing, importlib

### Community 91 - "Community 91"
Cohesion: 0.22
Nodes (8): init_env(), Path, Create or complete backend/.env from backend/.env.example (#42). The public…, Returns the names of the secrets it generated., sys, _mac(), #38/#34: a staged OTA rollout from the Firmware page., test_preview_start_progress_pause_and_resume()

### Community 92 - "Community 92"
Cohesion: 0.24
Nodes (8): call(), env_value(), main(), HTTP smoke test of a running imPress backend (#42): the system audit's…, ssl, urllib_error, urllib_request, uuid

### Community 93 - "Community 93"
Cohesion: 0.33
Nodes (9): handle_c6_frame(), heartbeat_task(), mesh_master_broadcast(), mesh_master_get_student_count(), mesh_master_sweep_timeouts(), ota_start(), msg_type_t, msg_encode() (+1 more)

### Community 94 - "Community 94"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 95 - "Community 95"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 96 - "Community 96"
Cohesion: 0.25
Nodes (4): Api, Tiny JSON client for setting up data the test then checks in the UI., multipart/form-data POST of one file field named 'file'., A device call (X-API-Key), e.g. registration or an OTA status report.

### Community 97 - "Community 97"
Cohesion: 0.33
Nodes (7): _ints(), Resolve a student row from a batch message. Student identity is the ENROLLMENT…, Validate + de-duplicate one mesh quiz answer. Mesh relays can deliver the same…, Validate + de-duplicate one mesh poll vote ((poll, student) is unique)., _record_poll_vote(), _record_quiz_answer(), _resolve_student_id_by_enrollment()

### Community 98 - "Community 98"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 99 - "Community 99"
Cohesion: 0.48
Nodes (6): _open_create_quiz(), #31: importing questions from CSV on the create-quiz page., test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz()

### Community 100 - "Community 100"
Cohesion: 0.38
Nodes (6): _open(), #35/#36: the Firmware page and pushing an approved image from Modules., test_invalid_upload_is_explained(), test_push_dialog_without_approved_images_points_to_the_firmware_page(), test_signature_status_is_shown(), test_upload_approve_and_push_from_modules()

### Community 101 - "Community 101"
Cohesion: 0.33
Nodes (6): esp_now_recv_info_t, extract_enrollment(), find_or_create_student(), mesh_master_get_student(), on_espnow_recv(), student_entry_t

### Community 102 - "Community 102"
Cohesion: 0.50
Nodes (4): health(), datetime, Device health states (#39), computed from the latest heartbeat. Rules, in order…, (state, reasons) for one device.

### Community 104 - "Community 104"
Cohesion: 0.60
Nodes (4): _open(), #32: importing and exporting courses and sections on the Classrooms page., test_invalid_rows_block_the_import(), test_valid_file_creates_courses_and_sections()

### Community 105 - "Community 105"
Cohesion: 0.60
Nodes (4): _beat(), #39: health states and the read-only diagnostics panel on the Modules page., _row(), test_health_badges_and_diagnostics_refresh()

### Community 106 - "Community 106"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

### Community 108 - "Community 108"
Cohesion: 0.67
Nodes (3): Popen, Terminate the child and everything it started (npm, ninja, docker run)., _stop()

## Knowledge Gaps
- **49 isolated node(s):** `StaleRender`, `ASAN_OPTIONS`, `run.sh script`, `afl-prepare-linux.sh script`, `afl.sh script` (+44 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 952 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **122 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `Community 51` to `Community 0`, `Community 1`, `Community 2`, `Community 6`, `Community 9`, `Community 10`, `Community 15`, `Community 16`, `Community 21`, `Community 22`, `Community 25`, `Community 26`, `Community 29`, `Community 30`, `Community 33`, `Community 34`, `Community 42`, `Community 43`, `Community 50`, `Community 54`, `Community 70`, `Community 76`, `Community 97`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `select()` connect `Community 12` to `Community 0`, `Community 1`, `Community 2`, `Community 6`, `Community 10`, `Community 11`, `Community 15`, `Community 16`, `Community 18`, `Community 19`, `Community 22`, `Community 25`, `Community 26`, `Community 29`, `Community 30`, `Community 31`, `Community 33`, `Community 34`, `Community 39`, `Community 42`, `Community 43`, `Community 44`, `Community 49`, `Community 50`, `Community 51`, `Community 52`, `Community 53`, `Community 54`, `Community 55`, `Community 58`, `Community 59`, `Community 66`, `Community 71`, `Community 76`, `Community 88`, `Community 97`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `login()` connect `Community 0` to `Community 10`, `Community 11`, `Community 14`, `Community 16`, `Community 18`, `Community 19`, `Community 29`, `Community 33`, `Community 34`, `Community 38`, `Community 43`, `Community 44`, `Community 54`, `Community 58`, `Community 61`, `Community 62`, `Community 66`, `Community 70`, `Community 71`, `Community 78`, `Community 88`, `Community 89`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 153 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 153 INFERRED edges - model-reasoned connections that need verification._
- **Are the 121 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 121 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `ASAN_OPTIONS`, `run.sh script` to the rest of the system?**
  _49 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0392156862745098 - nodes in this community are weakly interconnected._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
