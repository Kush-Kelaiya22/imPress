# Graph Report - repo  (2026-10-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3004 nodes · 8292 edges · 212 communities (98 shown, 114 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 1302 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c489266f`
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
- Community 210
- Community 211

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
  backend/tests/test_question_import.py → run_tests.py
- `log()` --calls--> `select()`  [INFERRED]
  backend/tests/test_question_import.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_auth_sessions.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_create.py → run_tests.py

## Import Cycles
- None detected.

## Communities (212 total, 114 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (83): errno, esp_crt_bundle, esp_event_handler_t, esp_netif, esp_system, esp_tls_crypto, esp_transport, esp_transport_ssl (+75 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (71): cJSON_Hooks, add_item_to_array(), add_item_to_object(), cJSON, case_insensitive_strcmp(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddBoolToObject() (+63 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (73): argparse, apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog() (+65 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (70): ActivityLogResponse, AdminUserCreate, ClassAssignTeacher, ClassCreate, ClassDevicesResponse, ClassImportReport, ClassJoin, CourseCreate (+62 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (73): admin_class_devices(), admin_create_class(), admin_delete_class(), admin_get_module(), admin_link_device(), admin_list_classes(), admin_list_modules(), admin_push_ota() (+65 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (65): esp_log, nvs_handle_t, cfg_clear_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str(), _store_dev_key() (+57 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (68): auth(), login(), fixture, su(), Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py…, _session_row(), q(), _shift_session() (+60 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (66): DeploymentTarget, FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., _act(), cancel_deployment(), create_deployment(), deployment_dict() (+58 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (65): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+57 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (59): log_activity(), AsyncSession, Write one activity log entry., Student, User, admin_import_students_csv(), bulk_register_students(), deactivate_user() (+51 more)

### Community 11 - "Community 11"
Cohesion: 0.07
Nodes (52): AsyncConnection, AsyncEngine, _add_columns(), add_device_keys(), add_diagnostics_columns(), add_firmware_signer(), add_quiz_question_started_at(), add_unique_constraints() (+44 more)

### Community 12 - "Community 12"
Cohesion: 0.07
Nodes (51): create_session(), generate_session_token(), get_current_user(), get_current_user_light(), hash_password(), _load_session_by_hash(), AsyncSession, Request (+43 more)

### Community 13 - "Community 13"
Cohesion: 0.10
Nodes (51): api_key_ok(), Constant-time device API key comparison., authorize(), _by_mac(), caller_for_key(), denial(), device_caller(), DeviceCaller (+43 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (41): dataclasses, platform, Popen, CaseResult, fmt_secs(), _idf_command(), _idf_image_present(), main() (+33 more)

### Community 15 - "Community 15"
Cohesion: 0.15
Nodes (46): cJSON_AddItemToArray(), cJSON_AddItemToObject(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc(), apply_patch(), cJSON (+38 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (34): os, playwright_sync_api, Create or complete backend/.env from backend/.env.example (#42). The public…, Check a firmware image the way the backend will at upload (#35, #66), before…, sys, tempfile, time, login() (+26 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (41): Any, ClassSession, activate_class(), class_presence(), _count_students(), create_class(), deactivate_class(), delete_class() (+33 more)

### Community 18 - "Community 18"
Cohesion: 0.10
Nodes (40): BaseType_t, ready_update(), spi_slave_send(), SemaphoreHandle_t, gpio_set_level(), xSemaphoreGive(), xSemaphoreGiveFromISR(), xSemaphoreTake() (+32 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (40): Base, Attendance, PollVote, QuizAnswer, StudentEnrollment, Get a student's participation summary across quizzes and polls., student_participation(), _ints() (+32 more)

### Community 20 - "Community 20"
Cohesion: 0.09
Nodes (14): cjson, esp_err, esp_event, esp_idf_version, esp_transport_ws, msg_t, on_student_message(), protocol (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.12
Nodes (35): esp_efuse, esp_mac, esp_random, display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown() (+27 more)

### Community 22 - "Community 22"
Cohesion: 0.09
Nodes (34): asyncio, SQLAlchemy ORM models for imPress., A student module seen on a gateway's mesh (#40): presence, not location. One…, StudentModule, datetime, Device health states (#39), computed from the latest heartbeat. Rules, in order…, class_modules(), _device_to_dict() (+26 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (35): check_secure(), insecure_settings(), Application configuration loaded from environment variables., Names of settings still at their public, repo-published defaults., Refuse to run with published secrets unless explicitly in DEBUG mode., Settings, init_db(), Create missing tables and apply pending migrations (stops on failure). (+27 more)

### Community 24 - "Community 24"
Cohesion: 0.09
Nodes (32): adc_oneshot, crypto, esp_heap_caps, esp_http_client, esp_ota_handle_t, esp_ota_ops, esp_partition_t, esp_timer (+24 more)

### Community 25 - "Community 25"
Cohesion: 0.09
Nodes (34): make_class(), make_user(), Create a user through the admin API; returns (user_id, auth headers)., Create a class via /api/admin/classes; optionally activate it., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password() (+26 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (35): Course, create_course(), delete_course(), get_course(), list_courses(), AsyncSession, delete, get (+27 more)

### Community 27 - "Community 27"
Cohesion: 0.13
Nodes (35): commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, Quiz, QuizQuestion, create_quiz(), get_quiz(), import_question_csv() (+27 more)

### Community 28 - "Community 28"
Cohesion: 0.10
Nodes (31): create_access_token(), Legacy JWT creation (kept for device registration / backward compat)., artifact_file(), artifact_path(), normalize_version(), Path, Firmware artifact store (#35). Uploads are validated as ESP-IDF app images…, store_dir() (+23 more)

### Community 29 - "Community 29"
Cohesion: 0.12
Nodes (33): approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get(), _latest_approved(), list_firmware() (+25 more)

### Community 30 - "Community 30"
Cohesion: 0.14
Nodes (27): _get(), _mesh_answer(), pause_scheduler(), _per_question(), fixture, parametrize, #73: timed quizzes advance (per_question) and end (total) by themselves, the…, Stop the app's own 1 s loop from racing the explicit ticks below (it looks… (+19 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (22): esp_app_desc, esp_bit_defs, esp_now, esp_wifi, event_groups, spi_slave_transaction_t, spi_post_trans_cb(), input_init() (+14 more)

### Community 32 - "Community 32"
Cohesion: 0.22
Nodes (30): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+22 more)

### Community 33 - "Community 33"
Cohesion: 0.15
Nodes (28): spi_slave_read(), msg_t, spi_slot_fifo_t, crc16_ccitt(), json_get_string(), msg_decode(), msg_verify_crc(), spi_record_read() (+20 more)

### Community 34 - "Community 34"
Cohesion: 0.17
Nodes (29): buffer_skip_whitespace(), cJSON_bool, cJSON_Compare(), cJSON_ParseWithLength(), cJSON_ParseWithLengthOpts(), cJSON_ParseWithOpts(), cJSON_PrintBuffered(), cJSON_PrintPreallocated() (+21 more)

### Community 35 - "Community 35"
Cohesion: 0.11
Nodes (25): import_classes_csv(), Create courses and their sections from a CSV. All-or-nothing: any invalid row…, ClassImportRow, apply_class_import(), _changes(), export_rows(), plan_class_import(), AsyncSession (+17 more)

### Community 36 - "Community 36"
Cohesion: 0.17
Nodes (26): batch_add(), batch_flush(), batch_flush_needed(), batch_init(), cJSON, handle_class_assignment(), heartbeat_task(), item_is_heartbeat() (+18 more)

### Community 38 - "Community 38"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 39 - "Community 39"
Cohesion: 0.18
Nodes (25): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+17 more)

### Community 40 - "Community 40"
Cohesion: 0.12
Nodes (18): answer(), join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, _marker(), _next_command(), #43 end to end: a teacher runs a quiz in a room, and the answers arrive through…, Frames the socket got before a marker broadcast now (so a missing frame fails…, The next frame ws_command.c acts on: it dispatches on "event" and ignores the… (+10 more)

### Community 41 - "Community 41"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 42 - "Community 42"
Cohesion: 0.12
Nodes (19): cJSON_Minify(), cJSON_Parse(), cJSON_Print(), cJSON_PrintUnformatted(), minify_string(), skip_multiline_comment(), skip_oneline_comment(), main() (+11 more)

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (23): posix_only, discover(), Distribution names from a requirements file, following -r includes., _requirements(), signal, test_every_default_runner_suite_runs_in_ci(), test_frontend_is_installed_from_its_lockfile(), test_runner_discovers_every_host_suite() (+15 more)

### Community 44 - "Community 44"
Cohesion: 0.09
Nodes (16): Gateway, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent…, go(), link(), age() (+8 more)

### Community 45 - "Community 45"
Cohesion: 0.22
Nodes (22): Require teacher, admin, or super_admin role., require_teacher_or_admin(), Poll, create_poll(), end_poll(), get_poll(), list_polls(), _poll_response() (+14 more)

### Community 46 - "Community 46"
Cohesion: 0.17
Nodes (20): functions(), mentions(), {name: body_text} for every top-level function definition in a C file., #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch() (+12 more)

### Community 47 - "Community 47"
Cohesion: 0.13
Nodes (14): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+6 more)

### Community 48 - "Community 48"
Cohesion: 0.19
Nodes (20): class_id_for_device(), Walk gateway_id chain up to the class gateway; return ClassSession.id or None., _activity(), q(), _device(), q(), Gateway-facing device API (routers/device.py) + presence service…, _register() (+12 more)

### Community 49 - "Community 49"
Cohesion: 0.19
Nodes (21): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), h(), fixture, fixture, Three rooms, each with a v2.1.0 gateway; a c6 2.2.0 image approved., rooms(), _artifact() (+13 more)

### Community 50 - "Community 50"
Cohesion: 0.16
Nodes (19): make_image(), _count(), q(), parametrize, #35: uploaded firmware is validated as a real imPress image and registered…, Against genuine ESP-IDF output when a local build exists (the synthetic images…, A scripts/build_signed.sh build (#66), when one exists locally., test_a_c6_image_is_never_pushed_to_an_s3() (+11 more)

### Community 51 - "Community 51"
Cohesion: 0.16
Nodes (21): config, queue_slot(), spi_slave_init(), esp_err_t, spi_slave_transaction_t, TickType_t, clobber_stack(), gpio_config() (+13 more)

### Community 52 - "Community 52"
Cohesion: 0.17
Nodes (18): key_digest(), load_public_key(), (n, e) from a PEM RSA public key (SubjectPublicKeyInfo, as written by…, The key's Secure Boot V2 digest: SHA-256 over n, e, rinv, mdash as they sit in…, _site_key(), _digest(), h(), fixture (+10 more)

### Community 53 - "Community 53"
Cohesion: 0.13
Nodes (15): client(), _drain_background_tasks(), fixture, Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, TestClient on an empty database (the app seeds the super admin)., _reset_db(), _fresh_settings(), #11: no working public credentials or debug leaks by default. (+7 more)

### Community 54 - "Community 54"
Cohesion: 0.27
Nodes (20): _age(), q(), _batch(), beat(), join(), leave(), _modules(), #40: the student module inventory. Modules seen on a gateway's mesh are listed… (+12 more)

### Community 55 - "Community 55"
Cohesion: 0.18
Nodes (18): cfg_has_device_key(), esp_err_t, esp_event_base_t, _download_and_apply(), _firmware_check(), _get_mac(), _http_post(), _http_post_body() (+10 more)

### Community 56 - "Community 56"
Cohesion: 0.12
Nodes (10): ConnectionManager, WebSocket, Send a JSON message to ALL connections in a class room (teachers + devices)., Send a JSON message only to connections matching the given role., Alias for broadcast_to_class., Manages WebSocket connections grouped by class ID. Teachers connect to manage…, FakeWS, test_manager_disconnect_frees_empty_rooms() (+2 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 58 - "Community 58"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 59 - "Community 59"
Cohesion: 0.21
Nodes (18): advance(), answer_closed(), deadline(), finish(), AsyncSession, datetime, quiz_timer_loop(), Quiz timing (#73): advance `per_question` quizzes and end `total` quizzes when… (+10 more)

### Community 60 - "Community 60"
Cohesion: 0.28
Nodes (18): _beat(), _device(), q(), _key(), #66: per-device keys. Devices register with the shared key and are issued their…, _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out() (+10 more)

### Community 61 - "Community 61"
Cohesion: 0.25
Nodes (15): msg_type_t, msg_to_json(), student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join() (+7 more)

### Community 62 - "Community 62"
Cohesion: 0.14
Nodes (10): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub() (+2 more)

### Community 63 - "Community 63"
Cohesion: 0.19
Nodes (17): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts…, Length of the app image itself (segments, checksum, appended SHA-256), without… (+9 more)

### Community 64 - "Community 64"
Cohesion: 0.15
Nodes (14): class_websocket(), _device_key_ok(), websocket, WebSocket endpoint handler for class rooms., The shared key (unless IMPRESS_DEVICE_KEYS_REQUIRED) or an active-able per-…, Validate a login session token for WebSocket auth. Returns the User or None.…, WebSocket endpoint for real-time class communication. Connect with:…, _ws_user_from_token() (+6 more)

### Community 65 - "Community 65"
Cohesion: 0.18
Nodes (15): make_student(), test_attendance_paths(), count(), _csv(), parametrize, Student registry (routers/students.py) and class enrollment (admin enroll…, test_csv_import_mixed_rows(), test_duplicate_enrollment_number_rejected() (+7 more)

### Community 66 - "Community 66"
Cohesion: 0.16
Nodes (12): env(), fixture, #21: co-faculty can run quizzes/polls for their class; outsiders still can't., _teacher(), device(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed. (+4 more)

### Community 67 - "Community 67"
Cohesion: 0.25
Nodes (16): answer(), batch(), count(), q(), fixture, parametrize, #6: /api/device/batch validates and de-duplicates mesh answers/votes., setup() (+8 more)

### Community 68 - "Community 68"
Cohesion: 0.25
Nodes (16): _device(), q(), hub(), _push(), fixture, parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report() (+8 more)

### Community 69 - "Community 69"
Cohesion: 0.14
Nodes (11): conftest, main(), Fail clearly if committed Graphify output is incomplete, stale, or unsafe., source_commit(), shutil, subprocess, _on(), Contract tests for the keyless Graphify generation and GitHub automation. (+3 more)

### Community 70 - "Community 70"
Cohesion: 0.15
Nodes (13): Activity logging service — records all significant actions., Require admin or super_admin role., require_admin(), get_db(), Async SQLAlchemy engine and session factory., SQLite ignores foreign keys unless asked, per connection., Dependency that yields an async DB session., _sqlite_pragmas() (+5 more)

### Community 71 - "Community 71"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 72 - "Community 72"
Cohesion: 0.15
Nodes (8): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), #13: S3 OTA — rollback protection and no reboot when nothing is installed., test_detach_unregisters_reconnect_handler_before_disconnecting(), test_new_image_marked_valid_only_after_mesh_and_spi_init(), test_only_a_successful_install_reboots()

### Community 73 - "Community 73"
Cohesion: 0.13
Nodes (11): Api, browser(), _free_port(), page(), fixture, A page that fails the test on any uncaught JS error; screenshot at the end., Tiny JSON client for setting up data the test then checks in the UI., multipart/form-data POST of one file field named 'file'. (+3 more)

### Community 74 - "Community 74"
Cohesion: 0.34
Nodes (13): _advance(), _dep(), _deploy(), _prompt(), #43 end to end: a firmware release reaches three rooms through the staged…, Read this room's socket until the gateway's own OTA prompt., _sockets(), test_an_unhealthy_image_rolls_back_and_stops_the_rollout() (+5 more)

### Community 75 - "Community 75"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10: only a super admin can grant/remove admin-level roles; roles are a closed…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 76 - "Community 76"
Cohesion: 0.27
Nodes (13): mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main(), simulate(), test_dedup_window_and_wrap(), test_id_ignores_hops_but_not_content() (+5 more)

### Community 77 - "Community 77"
Cohesion: 0.16
Nodes (10): #29: guards for the S3 <-> C6 link as ported from v3…, _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_student_count_comes_from_join_and_leave_only(), test_c6_validates_received_slots(), test_master_drops_a_payload_only_after_a_successful_transfer(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+2 more)

### Community 78 - "Community 78"
Cohesion: 0.23
Nodes (11): Path, append_coverage(), component_for(), enrich(), main(), node_id(), Build imPress's deterministic Graphify graph and enrich non-code coverage.…, Latest commit that changed input, rather than a graph-only bot commit. (+3 more)

### Community 79 - "Community 79"
Cohesion: 0.22
Nodes (10): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+2 more)

### Community 80 - "Community 80"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 81 - "Community 81"
Cohesion: 0.22
Nodes (13): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, adopt_legacy_files(), AsyncSession, UploadFile, Register valid <type>-<version>.bin files from the old store (once)., The site key if it signed the image, else its first signer, else ""., Validate and register an upload. Returns (artifact, created). Not committed. (+5 more)

### Community 82 - "Community 82"
Cohesion: 0.18
Nodes (11): _der(), _mgf1(), pss_verify(), Signed firmware images (#66): ESP-IDF Secure Boot V2 RSA-3072 signatures,…, (tag, start of content, end of content) of the DER element at pos., Build structurally valid ESP-IDF app images for tests (real header layout, app…, base64, functools (+3 more)

### Community 83 - "Community 83"
Cohesion: 0.29
Nodes (9): importlib_util, stat, _backend(), #42: the documented install path: scripts, secrets, version, CI job., test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets() (+1 more)

### Community 84 - "Community 84"
Cohesion: 0.27
Nodes (10): health(), (state, reasons) for one device., _dev(), parametrize, #39: device health states from the latest heartbeat diagnostics., test_heartbeat_stores_diagnostics_and_old_firmware_still_works(), get(), test_invalid_diagnostics_are_rejected() (+2 more)

### Community 85 - "Community 85"
Cohesion: 0.24
Nodes (8): cls(), fixture, parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student…, test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons()

### Community 86 - "Community 86"
Cohesion: 0.25
Nodes (10): parametrize, #8: teacher WebSocket auth uses the login session token; roles are recorded., _rejected(), test_device_key_still_required(), test_inactive_user_rejected(), deactivate(), test_roles_recorded_and_role_broadcast_targets_teachers(), test_teacher_after_logout_rejected() (+2 more)

### Community 87 - "Community 87"
Cohesion: 0.27
Nodes (8): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat()

### Community 88 - "Community 88"
Cohesion: 0.42
Nodes (9): _class(), _gateway_of(), q(), #17: registration must not steal a class's gateway link., _register(), test_explicit_classroom_code_still_assigns(), test_gateway_keeps_its_class_on_reregister(), test_non_gateway_registration_keeps_class_gateway() (+1 more)

### Community 89 - "Community 89"
Cohesion: 0.29
Nodes (8): _create(), ctx(), fixture, parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 90 - "Community 90"
Cohesion: 0.27
Nodes (8): Security review (#16 of the v2.1 brief): every route refuses a caller without…, 401/403, or 422 for the missing device-key header (a required `X-API-Key` is…, _refused(), _routes(), test_device_routes_reject_a_wrong_key(), test_every_route_needs_credentials(), fastapi_routing, importlib

### Community 91 - "Community 91"
Cohesion: 0.22
Nodes (5): live(), fixture, parametrize, #9: poll vote / quiz answer endpoints require the device key, a registered…, test_vote_and_answer_require_device_key()

### Community 92 - "Community 92"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 93 - "Community 93"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 95 - "Community 95"
Cohesion: 0.29
Nodes (4): env(), fixture, #20: quiz/poll details and results follow the class access rule., _teacher()

### Community 96 - "Community 96"
Cohesion: 0.48
Nodes (6): _open_create_quiz(), #31: importing questions from CSV on the create-quiz page., test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz()

### Community 97 - "Community 97"
Cohesion: 0.47
Nodes (5): _next_device_frame(), _project(), Contract test: frames the C6 gateway receives on its device WebSocket (#3). The…, The single frame an action broadcasts; it must carry a firmware event. Reads…, test_device_socket_receives_firmware_contract()

### Community 98 - "Community 98"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

### Community 102 - "Community 102"
Cohesion: 0.67
Nodes (3): init_env(), Path, Returns the names of the secrets it generated.

## Knowledge Gaps
- **49 isolated node(s):** `StaleRender`, `afl-prepare-linux.sh script`, `afl.sh script`, `ossfuzz.sh script`, `start_server.sh script` (+44 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 898 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **114 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `select()` connect `Community 4` to `Community 7`, `Community 8`, `Community 10`, `Community 12`, `Community 13`, `Community 14`, `Community 17`, `Community 19`, `Community 22`, `Community 23`, `Community 25`, `Community 26`, `Community 27`, `Community 29`, `Community 32`, `Community 35`, `Community 39`, `Community 40`, `Community 41`, `Community 43`, `Community 44`, `Community 45`, `Community 48`, `Community 50`, `Community 54`, `Community 59`, `Community 60`, `Community 65`, `Community 67`, `Community 68`, `Community 81`, `Community 84`, `Community 88`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `login()` connect `Community 7` to `Community 12`, `Community 19`, `Community 25`, `Community 26`, `Community 30`, `Community 32`, `Community 39`, `Community 40`, `Community 41`, `Community 48`, `Community 49`, `Community 50`, `Community 52`, `Community 53`, `Community 54`, `Community 60`, `Community 65`, `Community 66`, `Community 67`, `Community 68`, `Community 74`, `Community 75`, `Community 81`, `Community 84`, `Community 85`, `Community 86`, `Community 88`, `Community 89`, `Community 91`, `Community 94`, `Community 95`, `Community 97`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `istnow()` connect `Community 12` to `Community 4`, `Community 7`, `Community 8`, `Community 11`, `Community 13`, `Community 19`, `Community 22`, `Community 23`, `Community 27`, `Community 28`, `Community 29`, `Community 32`, `Community 40`, `Community 44`, `Community 45`, `Community 48`, `Community 54`, `Community 59`, `Community 64`, `Community 74`, `Community 86`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 155 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 155 INFERRED edges - model-reasoned connections that need verification._
- **Are the 110 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 110 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `afl-prepare-linux.sh script`, `afl.sh script` to the rest of the system?**
  _49 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
