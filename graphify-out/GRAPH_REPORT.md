# Graph Report - imPress  (2026-10-13)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3237 nodes · 8950 edges · 229 communities (103 shown, 126 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1355 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `509f4be6`
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
- Community 128
- Community 134
- Community 135
- Community 225
- Community 226
- Community 227
- Community 228

## God Nodes (most connected - your core abstractions)
1. `select()` - 161 edges
2. `User` - 149 edges
3. `login()` - 140 edges
4. `auth()` - 138 edges
5. `EspDevice` - 100 edges
6. `istnow()` - 100 edges
7. `ClassSession` - 91 edges
8. `make_user()` - 87 edges
9. `_post()` - 76 edges
10. `log_activity()` - 70 edges

## Surprising Connections (you probably didn't know these)
- `test_every_setting_is_documented()` --uses--> `Settings`  [INFERRED]
  tests/test_docs_consistency.py → backend/app/config.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_auth_sessions.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_create.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_gateway_autolink.py → run_tests.py
- `get()` --calls--> `select()`  [INFERRED]
  backend/tests/test_health.py → run_tests.py

## Import Cycles
- None detected.

## Communities (229 total, 126 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (96): auth(), login(), fixture, su(), parametrize, Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py…, _session_row(), q() (+88 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (88): A student module seen on a gateway's mesh (#40): presence, not location. One…, StudentModule, admin_class_devices(), admin_get_module(), admin_link_device(), admin_list_modules(), admin_push_ota(), admin_student_modules() (+80 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (70): make_class(), make_user(), Create a user through the admin API; returns (user_id, auth headers)., Create a class via /api/admin/classes; optionally activate it., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password() (+62 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (66): config, nvs_handle_t, cfg_clear_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str(), _store_dev_key() (+58 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (69): User, account_refusal(), allowed(), can_grant(), class_owner_or_admin(), forbidden(), HTTPException, Authorization policy: the one place that decides who may do what (#122). Every… (+61 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (60): adc_oneshot, crypto, esp_crt_bundle, esp_event, esp_heap_caps, esp_http_client, esp_netif, esp_ota_handle_t (+52 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (66): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+58 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (64): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+56 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (62): ActivityLog, DeploymentTarget, FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., _act(), cancel_deployment(), create_deployment() (+54 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (54): AsyncConnection, AsyncEngine, _add_columns(), add_device_keys(), add_diagnostics_columns(), add_firmware_signer(), add_quiz_question_started_at(), add_unique_constraints() (+46 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (59): esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client_config_t, esp_websocket_client_handle_t, esp_websocket_error_type_t (+51 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (53): Base, Async SQLAlchemy engine and session factory., SQLite ignores foreign keys unless asked, per connection., _sqlite_pragmas(), Attendance, QuizAnswer, SQLAlchemy ORM models for imPress., Student (+45 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (53): commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, Quiz, QuizQuestion, Example file with every column. Public: it contains no data., create_quiz(), get_quiz() (+45 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (54): Any, ClassSession, class_access(), Work with a class: its primary teacher, any co-faculty member, or an…, admin_create_class(), admin_list_classes(), admin_set_class_faculty(), admin_update_class() (+46 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (52): create_session(), generate_session_token(), get_current_user(), get_current_user_light(), hash_password(), _load_session_by_hash(), AsyncSession, Request (+44 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (52): api_key_ok(), Constant-time device API key comparison., authorize(), _by_mac(), caller_for_key(), denial(), device_caller(), DeviceCaller (+44 more)

### Community 17 - "Community 17"
Cohesion: 0.06
Nodes (39): make_student(), answer(), Gateway, join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway. (+31 more)

### Community 18 - "Community 18"
Cohesion: 0.14
Nodes (48): cJSON_AddItemToArray(), cJSON_AddItemToObject(), cJSON_CreateObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc() (+40 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (16): cjson, esp_efuse, esp_err, esp_idf_version, esp_transport_ws, read_file(), main(), msg_t (+8 more)

### Community 20 - "Community 20"
Cohesion: 0.12
Nodes (38): cJSON_Hooks, buffer_skip_whitespace(), cJSON_bool, cJSON_AddBoolToObject(), cJSON_Compare(), cJSON_CreateBool(), cJSON_InitHooks(), cJSON_Minify() (+30 more)

### Community 21 - "Community 21"
Cohesion: 0.06
Nodes (31): _parse_time(), Convert "HH:MM" → minutes since midnight. Returns None if malformed., Two time slots overlap when neither fully precedes the other. Overnight / wrap-…, Two classes only clash if they run in the same semester/window. Priority:…, _same_academic_window(), _slots_conflict(), normalize_version(), as_ist() (+23 more)

### Community 22 - "Community 22"
Cohesion: 0.07
Nodes (38): _sha256_hex(), Older versions stored the raw bearer token in user_sessions.session_token. Any…, _scrub_raw_session_tokens(), Touch last_activity_at for live user sessions on each API request. Best-effort…, refresh_session_activity(), UserSession, _cleanup_once(), Delete sessions that are hard-expired, idle-expired, or revoked. Returns the… (+30 more)

### Community 23 - "Community 23"
Cohesion: 0.10
Nodes (39): BaseType_t, esp_wifi, spi_slave_send(), SemaphoreHandle_t, xSemaphoreGive(), xSemaphoreGiveFromISR(), xSemaphoreTake(), handle_c6_frame() (+31 more)

### Community 24 - "Community 24"
Cohesion: 0.13
Nodes (33): esp_mac, display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown(), display_show_provision_state(), display_show_question() (+25 more)

### Community 25 - "Community 25"
Cohesion: 0.07
Nodes (25): Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, Smoke tests: the app boots on an empty DB and its basic contracts hold., test_seeded_super_admin_can_log_in(), cls(), fixture, parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student… (+17 more)

### Community 26 - "Community 26"
Cohesion: 0.08
Nodes (26): esp_app_desc, esp_bit_defs, esp_log, esp_now, esp_random, esp_tls_errors, event_groups, spi_slave_transaction_t (+18 more)

### Community 27 - "Community 27"
Cohesion: 0.08
Nodes (28): check_secure(), insecure_settings(), Names of settings still at their public, repo-published defaults., Refuse to run with published secrets, or with unauthenticated WebSockets…, Settings, client(), _drain_background_tasks(), fixture (+20 more)

### Community 28 - "Community 28"
Cohesion: 0.09
Nodes (33): Course, admin_import_students_csv(), export_classes_csv(), import_classes_csv(), UploadFile, Create courses and their sections from a CSV. All-or-nothing: any invalid row…, Every course section in the import layout. Cells that would start a spreadsheet…, Import students from CSV and enroll them into a specific class. Columns:… (+25 more)

### Community 29 - "Community 29"
Cohesion: 0.09
Nodes (29): is_staff(), A logged-in, active member of staff (any assignable role)., _device_to_dict(), presence_snapshot(), _push_after_commit(), push_presence(), datetime, ESP device presence monitoring (online/offline logs). Requirement: the backend… (+21 more)

### Community 30 - "Community 30"
Cohesion: 0.12
Nodes (33): approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get(), _latest_approved(), list_firmware() (+25 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (27): make_image(), _count(), q(), #35: uploaded firmware is validated as a real imPress image and registered…, test_a_c6_image_is_never_pushed_to_an_s3(), test_admin_only(), test_corrupted_image_is_detected_by_its_hash(), test_device_downloads_its_registered_image_with_its_hash() (+19 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (33): batch_flush(), add_item_to_object(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddFalseToObject(), cJSON_AddItemToObjectCS(), cJSON_AddNullToObject(), cJSON_AddNumberToObject() (+25 more)

### Community 33 - "Community 33"
Cohesion: 0.15
Nodes (29): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), _artifact(), _hub(), _push(), #36: firmware version manager: approval, deprecation, retention, usage., _set(), test_admin_only() (+21 more)

### Community 34 - "Community 34"
Cohesion: 0.21
Nodes (31): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+23 more)

### Community 35 - "Community 35"
Cohesion: 0.09
Nodes (27): asyncio, Application configuration loaded from environment variables., _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), health() (+19 more)

### Community 36 - "Community 36"
Cohesion: 0.15
Nodes (28): spi_slave_read(), msg_t, spi_slot_fifo_t, crc16_ccitt(), json_get_string(), msg_decode(), msg_verify_crc(), spi_record_read() (+20 more)

### Community 37 - "Community 37"
Cohesion: 0.12
Nodes (28): class_id_for_device(), _log(), mark_offline(), Mark stale devices offline. Returns number of transitions logged., Write a presence entry to the activity log., Mark a device offline and log the transition., Walk gateway_id chain up to the class gateway; return ClassSession.id or None., _sweep_once() (+20 more)

### Community 38 - "Community 38"
Cohesion: 0.10
Nodes (24): _calls(), The authorization policy is the one place that decides access (#122)., A staff route without a policy permission is a new hole; device routes…, Role checks scattered across routers drifted before (#19-#21, #116, #121)., docs/design/authorization.md shows GRANTS; it must not drift., _routes(), test_every_route_is_governed_by_the_policy_or_listed(), test_no_role_comparisons_outside_the_policy() (+16 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (29): add_item_to_array(), cJSON, case_insensitive_strcmp(), cJSON_AddItemReferenceToArray(), cJSON_AddItemReferenceToObject(), cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive() (+21 more)

### Community 40 - "Community 40"
Cohesion: 0.10
Nodes (22): #39: device health states from the latest heartbeat diagnostics., device(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download(), test_only_the_pushed_version_downloads() (+14 more)

### Community 42 - "Community 42"
Cohesion: 0.10
Nodes (27): CaseResult, _idf_command(), _missing(), missing_packages(), parse_coverage(), parse_host_output(), parse_junit(), Path (+19 more)

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 44 - "Community 44"
Cohesion: 0.18
Nodes (25): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+17 more)

### Community 45 - "Community 45"
Cohesion: 0.13
Nodes (24): _get(), _mesh_answer(), _per_question(), parametrize, Pretend the current question / the quiz started `seconds` earlier., _shift(), go(), _start() (+16 more)

### Community 46 - "Community 46"
Cohesion: 0.15
Nodes (24): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, adopt_legacy_files(), artifact_file(), artifact_path(), AsyncSession, Path, UploadFile (+16 more)

### Community 47 - "Community 47"
Cohesion: 0.19
Nodes (24): _count(), q(), _csv(), _post(), parametrize, #32: import courses and their sections (class sessions) from CSV., test_admin_only(), test_any_invalid_row_means_nothing_is_imported() (+16 more)

### Community 48 - "Community 48"
Cohesion: 0.14
Nodes (25): queue_slot(), ready_update(), spi_slave_init(), esp_err_t, spi_slave_transaction_t, TickType_t, clobber_stack(), gpio_config() (+17 more)

### Community 49 - "Community 49"
Cohesion: 0.12
Nodes (22): log_activity(), AsyncSession, Activity logging service — records all significant actions., Write one activity log entry., create_course(), delete_course(), get_course(), list_courses() (+14 more)

### Community 50 - "Community 50"
Cohesion: 0.21
Nodes (24): Poll, PollVote, Get a student's participation summary across quizzes and polls., student_participation(), create_poll(), end_poll(), get_poll(), list_polls() (+16 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 52 - "Community 52"
Cohesion: 0.12
Nodes (16): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+8 more)

### Community 53 - "Community 53"
Cohesion: 0.11
Nodes (21): posix_only, discover(), Run `cmd` and return (exit code, combined output, abort reason). Output is read…, run_streaming(), signal, test_frontend_is_installed_from_its_lockfile(), test_runner_discovers_every_host_suite(), skipif (+13 more)

### Community 54 - "Community 54"
Cohesion: 0.14
Nodes (21): argparse, _der(), key_digest(), load_public_key(), _mgf1(), pss_verify(), ValueError, Signed firmware images (#66): ESP-IDF Secure Boot V2 RSA-3072 signatures,… (+13 more)

### Community 55 - "Community 55"
Cohesion: 0.13
Nodes (21): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts…, Length of the app image itself (segments, checksum, appended SHA-256), without… (+13 more)

### Community 56 - "Community 56"
Cohesion: 0.17
Nodes (20): functions(), mentions(), {name: body_text} for every top-level function definition in a C file., #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch() (+12 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (21): _count(), q(), _fk_violations(), q(), _insert_twice(), go(), fixture, #41: the database enforces its own integrity (foreign keys, uniqueness), and… (+13 more)

### Community 58 - "Community 58"
Cohesion: 0.27
Nodes (20): _age(), q(), _batch(), beat(), join(), leave(), _modules(), #40: the student module inventory. Modules seen on a gateway's mesh are listed… (+12 more)

### Community 59 - "Community 59"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 60 - "Community 60"
Cohesion: 0.19
Nodes (17): cfg_has_device_key(), esp_err_t, esp_event_base_t, _download_and_apply(), _firmware_check(), _get_mac(), _http_post(), _http_post_body() (+9 more)

### Community 61 - "Community 61"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 62 - "Community 62"
Cohesion: 0.16
Nodes (15): platform, Popen, fmt_secs(), _idf_image_present(), main(), markdown_report(), Paint, print_report() (+7 more)

### Community 63 - "Community 63"
Cohesion: 0.21
Nodes (18): advance(), answer_closed(), deadline(), finish(), AsyncSession, datetime, quiz_timer_loop(), Quiz timing (#73): advance `per_question` quizzes and end `total` quizzes when… (+10 more)

### Community 64 - "Community 64"
Cohesion: 0.28
Nodes (18): _beat(), _device(), q(), _key(), #66: per-device keys. Devices register with the shared key and are issued their…, _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out() (+10 more)

### Community 65 - "Community 65"
Cohesion: 0.25
Nodes (15): msg_type_t, msg_to_json(), student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join() (+7 more)

### Community 66 - "Community 66"
Cohesion: 0.15
Nodes (16): _me(), fixture, parametrize, At least one active super admin always remains (#116). The original failure: a…, The original lockout path: PUT with is_active=false on yourself (#116, #119)., Two super admins disabling each other at the same moment: one must fail., su(), test_concurrent_mutual_deactivation_leaves_one_super_admin() (+8 more)

### Community 67 - "Community 67"
Cohesion: 0.18
Nodes (14): playwright_sync_api, login(), #51: only the latest navigation renders., test_normal_navigation_and_in_page_rerender_still_work(), test_quick_navigation_is_not_overwritten_by_a_slower_page(), #73: the class page offers Next for every timing mode, and a quiz the server's…, test_timed_quiz_has_next_and_ends_on_the_timer(), #40: student modules that joined a gateway appear in the inventory, the class… (+6 more)

### Community 68 - "Community 68"
Cohesion: 0.25
Nodes (16): _device(), q(), hub(), _push(), fixture, parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report() (+8 more)

### Community 69 - "Community 69"
Cohesion: 0.14
Nodes (10): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, #132: both backend clients classify a failure and log the hint, and the boot…, test_connection_failures_say_why(), test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), #13: S3 OTA — rollback protection and no reboot when nothing is installed., test_detach_unregisters_reconnect_handler_before_disconnecting() (+2 more)

### Community 70 - "Community 70"
Cohesion: 0.15
Nodes (9): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat() (+1 more)

### Community 71 - "Community 71"
Cohesion: 0.15
Nodes (10): _publish_graph_visualization(), Sphinx configuration for the public imPress documentation site., Expose the generated graph beneath the hosted ``/graph/`` page., setup(), shutil, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards() (+2 more)

### Community 72 - "Community 72"
Cohesion: 0.21
Nodes (15): cJSON_GetArraySize(), cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput() (+7 more)

### Community 73 - "Community 73"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 74 - "Community 74"
Cohesion: 0.30
Nodes (14): _advance(), _dep(), _deploy(), _prompt(), fixture, #43 end to end: a firmware release reaches three rooms through the staged…, Three rooms, each with a v2.1.0 gateway; a c6 2.2.0 image approved., Read this room's socket until the gateway's own OTA prompt. (+6 more)

### Community 75 - "Community 75"
Cohesion: 0.30
Nodes (14): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+6 more)

### Community 76 - "Community 76"
Cohesion: 0.34
Nodes (13): answer(), batch(), count(), q(), parametrize, #6: /api/device/batch validates and de-duplicates mesh answers/votes., test_distinct_students_and_questions_all_count(), test_inactive_quiz_and_closed_poll_skipped() (+5 more)

### Community 77 - "Community 77"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10, #119: only a super admin can grant/remove admin-level roles; roles are a…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 78 - "Community 78"
Cohesion: 0.27
Nodes (13): mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main(), simulate(), test_dedup_window_and_wrap(), test_id_ignores_hops_but_not_content() (+5 more)

### Community 79 - "Community 79"
Cohesion: 0.16
Nodes (10): #29: guards for the S3 <-> C6 link as ported from v3…, _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_student_count_comes_from_join_and_leave_only(), test_c6_validates_received_slots(), test_master_drops_a_payload_only_after_a_successful_transfer(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+2 more)

### Community 80 - "Community 80"
Cohesion: 0.23
Nodes (11): append_coverage(), component_for(), enrich(), main(), node_id(), Path, Build imPress's deterministic Graphify graph and enrich non-code coverage.…, Latest commit that changed input, rather than a graph-only bot commit. (+3 more)

### Community 81 - "Community 81"
Cohesion: 0.22
Nodes (10): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+2 more)

### Community 82 - "Community 82"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 83 - "Community 83"
Cohesion: 0.24
Nodes (10): main(), _lock_out(), Offline recovery of a locked-out installation (#120)., A database from before #116: no triggers, every super admin inactive., _restore(), _sql(), test_cli_exit_codes(), test_promotes_an_existing_account() (+2 more)

### Community 84 - "Community 84"
Cohesion: 0.20
Nodes (5): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #66: the signed-app profile and the scripts that build with it., re

### Community 85 - "Community 85"
Cohesion: 0.24
Nodes (10): create_access_token(), Legacy JWT creation (kept for device registration / backward compat)., ist_iso(), istnow_aware(), datetime, Indian Standard Time (IST) helpers — the backend's single source of truth for…, Current time as an offset-aware IST datetime., ISO-8601 string of *dt* (or now) in IST with explicit +05:30 offset. (+2 more)

### Community 86 - "Community 86"
Cohesion: 0.24
Nodes (10): tempfile, time, browser(), _free_port(), page(), fixture, Browser UI checks: a real backend on a temp database, driven by Playwright.…, A page that fails the test on any uncaught JS error; screenshot at the end. (+2 more)

### Community 87 - "Community 87"
Cohesion: 0.29
Nodes (8): assert, backend_fail_t, errno, esp_event_base_t, ws_event_handler(), backend_classify(), backend_hint(), main()

### Community 88 - "Community 88"
Cohesion: 0.24
Nodes (9): health(), datetime, Device health states (#39), computed from the latest heartbeat. Rules, in order…, (state, reasons) for one device., _dev(), parametrize, test_invalid_diagnostics_are_rejected(), test_precedence_offline_over_updating_over_error_over_degraded() (+1 more)

### Community 89 - "Community 89"
Cohesion: 0.20
Nodes (9): push_device_status(), push_poll_to_mesh(), push_quiz_to_mesh(), push_student_data(), Bridge service: connects ESP device data to WebSocket clients. This service…, Push student device data (heartbeats, answers, votes) to teacher dashboard., Push individual device status update., Push quiz question through WebSocket → C6 → SPI → S3 → mesh → students. (+1 more)

### Community 90 - "Community 90"
Cohesion: 0.29
Nodes (8): _create(), ctx(), fixture, parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 91 - "Community 91"
Cohesion: 0.22
Nodes (8): init_env(), Path, Create or complete backend/.env from backend/.env.example (#42). The public…, Returns the names of the secrets it generated., sys, _mac(), #38/#34: a staged OTA rollout from the Firmware page., test_preview_start_progress_pause_and_resume()

### Community 92 - "Community 92"
Cohesion: 0.24
Nodes (8): call(), env_value(), main(), HTTP smoke test of a running imPress backend (#42): the system audit's…, ssl, urllib_error, urllib_request, uuid

### Community 93 - "Community 93"
Cohesion: 0.22
Nodes (5): live(), fixture, parametrize, #9: poll vote / quiz answer endpoints require the device key, a registered…, test_vote_and_answer_require_device_key()

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
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 98 - "Community 98"
Cohesion: 0.48
Nodes (6): _open_create_quiz(), #31: importing questions from CSV on the create-quiz page., test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz()

### Community 99 - "Community 99"
Cohesion: 0.38
Nodes (6): _open(), #35/#36: the Firmware page and pushing an approved image from Modules., test_invalid_upload_is_explained(), test_push_dialog_without_approved_images_points_to_the_firmware_page(), test_signature_status_is_shown(), test_upload_approve_and_push_from_modules()

### Community 101 - "Community 101"
Cohesion: 0.50
Nodes (4): main(), Fail clearly if committed Graphify output is incomplete, stale, or unsafe., source_commit(), subprocess

### Community 102 - "Community 102"
Cohesion: 0.60
Nodes (4): _open(), #32: importing and exporting courses and sections on the Classrooms page., test_invalid_rows_block_the_import(), test_valid_file_creates_courses_and_sections()

### Community 103 - "Community 103"
Cohesion: 0.60
Nodes (4): _beat(), #39: health states and the read-only diagnostics panel on the Modules page., _row(), test_health_badges_and_diagnostics_refresh()

### Community 104 - "Community 104"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

## Knowledge Gaps
- **50 isolated node(s):** `StaleRender`, `ASAN_OPTIONS`, `run.sh script`, `afl-prepare-linux.sh script`, `afl.sh script` (+45 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 980 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **126 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `Community 22` to `Community 0`, `Community 1`, `Community 5`, `Community 9`, `Community 10`, `Community 12`, `Community 13`, `Community 15`, `Community 16`, `Community 17`, `Community 21`, `Community 29`, `Community 30`, `Community 34`, `Community 35`, `Community 37`, `Community 40`, `Community 50`, `Community 58`, `Community 63`, `Community 74`, `Community 85`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `select()` connect `Community 14` to `Community 0`, `Community 1`, `Community 2`, `Community 5`, `Community 9`, `Community 12`, `Community 13`, `Community 15`, `Community 16`, `Community 17`, `Community 22`, `Community 25`, `Community 28`, `Community 29`, `Community 30`, `Community 31`, `Community 34`, `Community 37`, `Community 42`, `Community 44`, `Community 46`, `Community 47`, `Community 49`, `Community 50`, `Community 51`, `Community 53`, `Community 57`, `Community 58`, `Community 62`, `Community 63`, `Community 64`, `Community 68`, `Community 76`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `login()` connect `Community 0` to `Community 2`, `Community 17`, `Community 22`, `Community 25`, `Community 31`, `Community 33`, `Community 34`, `Community 37`, `Community 38`, `Community 40`, `Community 44`, `Community 47`, `Community 51`, `Community 57`, `Community 58`, `Community 64`, `Community 66`, `Community 68`, `Community 74`, `Community 76`, `Community 77`, `Community 83`, `Community 90`, `Community 93`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 157 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 157 INFERRED edges - model-reasoned connections that need verification._
- **Are the 125 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 125 INFERRED edges - model-reasoned connections that need verification._
- **Are the 69 inferred relationships involving `EspDevice` (e.g. with `_by_mac()` and `caller_for_key()`) actually correct?**
  _`EspDevice` has 69 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `ASAN_OPTIONS`, `run.sh script` to the rest of the system?**
  _50 weakly-connected nodes found - possible documentation gaps or missing edges._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
