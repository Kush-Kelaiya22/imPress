# Graph Report - repo  (2026-10-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3032 nodes · 8329 edges · 219 communities (100 shown, 119 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 1303 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `23e38b6c`
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
- Community 131
- Community 216
- Community 217
- Community 218

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
  backend/tests/test_auth_sessions.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_create.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_import.py → run_tests.py
- `check()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_import.py → run_tests.py

## Import Cycles
- None detected.

## Communities (219 total, 119 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (39): cjson, crypto, esp_app_desc, esp_bit_defs, esp_efuse, esp_err, esp_event, esp_http_client (+31 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (82): DeploymentTarget, FirmwareArtifact, FirmwareDeployment, One uploaded firmware image. Facts come from the image itself…, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., _act(), cancel_deployment() (+74 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (74): cJSON_Hooks, msg_type_t, msg_to_json(), add_item_to_array(), add_item_to_object(), cJSON, cast_away_const(), cJSON_AddArrayToObject() (+66 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (68): config, nvs_handle_t, cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str() (+60 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (63): import_users_csv(), Admin router: user management, class (classroom) management & enrollment,…, Mass-import user accounts from CSV. Required columns (all compulsory):…, ActivityLogResponse, AdminUserCreate, BulkStudentRegister, ClassAssignTeacher, ClassCreate (+55 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (64): _cleanup_once(), Delete sessions that are hard-expired, idle-expired, or revoked. Returns the…, auth(), login(), fixture, su(), parametrize, Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py… (+56 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (65): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+57 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (64): errno, esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client_config_t, esp_websocket_client_handle_t (+56 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (64): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+56 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (52): AsyncConnection, AsyncEngine, _add_columns(), add_device_keys(), add_diagnostics_columns(), add_firmware_signer(), add_quiz_question_started_at(), add_unique_constraints() (+44 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (53): Any, ClassSession, admin_create_class(), admin_delete_class(), assign_teacher(), Re-select a class after mutation so selectin relationships load in the async…, Admin creates a classroom (course section): picks course, faculty, schedule,…, Admin assigns a teacher to a class. (+45 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (53): log_activity(), AsyncSession, Write one activity log entry., Student, User, bulk_register_students(), deactivate_user(), delete_user() (+45 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (46): advance(), answer_closed(), deadline(), finish(), AsyncSession, datetime, quiz_timer_loop(), Quiz timing (#73): advance `per_question` quizzes and end `total` quizzes when… (+38 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (46): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), make_image(), fixture, Three rooms, each with a v2.1.0 gateway; a c6 2.2.0 image approved., rooms(), _artifact(), _hub() (+38 more)

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (49): cJSON_AddItemToObject(), cJSON_CreateObject(), cJSON_Duplicate(), cJSON_free(), cJSON_GetStringValue(), cJSON_IsArray(), cJSON_IsObject(), cJSON_IsString() (+41 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (46): adc_oneshot, esp_crt_bundle, esp_heap_caps, esp_netif, esp_ota_handle_t, esp_partition_t, esp_system, esp_timer (+38 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (46): Activity logging service — records all significant actions., create_session(), generate_session_token(), get_current_user(), get_current_user_light(), hash_password(), _load_session_by_hash(), AsyncSession (+38 more)

### Community 18 - "Community 18"
Cohesion: 0.10
Nodes (43): Quiz, QuizQuestion, create_quiz(), get_quiz(), import_question_csv(), list_quizzes(), next_question(), parse_question_csv() (+35 more)

### Community 19 - "Community 19"
Cohesion: 0.09
Nodes (42): Course, admin_get_module(), admin_link_device(), admin_push_ota(), admin_reset_device_key(), admin_toggle_module_access(), admin_unlink_device(), admin_verify_module() (+34 more)

### Community 20 - "Community 20"
Cohesion: 0.08
Nodes (38): make_class(), make_user(), Create a user through the admin API; returns (user_id, auth headers)., Create a class via /api/admin/classes; optionally activate it., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password() (+30 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (38): ActivityLog, EspDevice, _broadcast_participation(), firmware_applied(), firmware_download(), heartbeat(), _ints(), _observe_module() (+30 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (33): create_access_token(), Legacy JWT creation (kept for device registration / backward compat)., _parse_time(), Convert "HH:MM" → minutes since midnight. Returns None if malformed., Two time slots overlap when neither fully precedes the other. Overnight / wrap-…, _slots_conflict(), normalize_version(), as_ist() (+25 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (35): check_secure(), insecure_settings(), Application configuration loaded from environment variables., Names of settings still at their public, repo-published defaults., Refuse to run with published secrets unless explicitly in DEBUG mode., Settings, init_db(), Create missing tables and apply pending migrations (stops on failure). (+27 more)

### Community 24 - "Community 24"
Cohesion: 0.13
Nodes (35): Base, commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, Attendance, Poll, PollVote, SQLAlchemy ORM models for imPress. (+27 more)

### Community 25 - "Community 25"
Cohesion: 0.10
Nodes (31): client(), _drain_background_tasks(), fixture, TestClient on an empty database (the app seeds the super admin)., _reset_db(), _beat(), _device(), q() (+23 more)

### Community 26 - "Community 26"
Cohesion: 0.07
Nodes (28): Gateway, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent…, go(), link(), age() (+20 more)

### Community 27 - "Community 27"
Cohesion: 0.12
Nodes (34): BaseType_t, xSemaphoreGive(), xSemaphoreTake(), msg_t, handle_c6_frame(), heartbeat_task(), on_student_message(), spi_link_task() (+26 more)

### Community 28 - "Community 28"
Cohesion: 0.10
Nodes (34): spi_slave_transaction_t, queue_slot(), ready_update(), spi_post_trans_cb(), spi_slave_init(), spi_slave_read(), spi_slave_send(), esp_err_t (+26 more)

### Community 29 - "Community 29"
Cohesion: 0.12
Nodes (34): QuizAnswer, _count(), q(), _fk_violations(), q(), _insert_twice(), go(), #41: the database enforces its own integrity (foreign keys, uniqueness), and… (+26 more)

### Community 30 - "Community 30"
Cohesion: 0.08
Nodes (36): A student module seen on a gateway's mesh (#40): presence, not location. One…, StudentModule, admin_class_devices(), admin_list_classes(), admin_list_modules(), admin_set_class_faculty(), admin_student_modules(), admin_update_class() (+28 more)

### Community 31 - "Community 31"
Cohesion: 0.09
Nodes (30): admin_import_students_csv(), import_classes_csv(), UploadFile, Create courses and their sections from a CSV. All-or-nothing: any invalid row…, Import students from CSV and enroll them into a specific class. Columns:…, ClassImportReport, ClassImportRow, All-or-nothing: any invalid row means nothing is imported. (+22 more)

### Community 32 - "Community 32"
Cohesion: 0.14
Nodes (29): msg_t, spi_slot_fifo_t, crc16_ccitt(), json_get_string(), msg_decode(), msg_verify_crc(), spi_record_read(), spi_record_write() (+21 more)

### Community 33 - "Community 33"
Cohesion: 0.15
Nodes (31): display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown(), display_show_provision_state(), display_show_question(), display_show_result() (+23 more)

### Community 34 - "Community 34"
Cohesion: 0.22
Nodes (30): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+22 more)

### Community 35 - "Community 35"
Cohesion: 0.11
Nodes (28): platform, CaseResult, _idf_command(), _idf_image_present(), _missing(), missing_packages(), parse_coverage(), parse_host_output() (+20 more)

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (24): _sha256_hex(), Older versions stored the raw bearer token in user_sessions.session_token. Any…, _scrub_raw_session_tokens(), UserSession, Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, _next_device_frame(), _project(), Contract test: frames the C6 gateway receives on its device WebSocket (#3). The… (+16 more)

### Community 37 - "Community 37"
Cohesion: 0.13
Nodes (27): approve_firmware(), delete_firmware(), firmware_detail(), FirmwareUpdate, _get(), _latest_approved(), list_firmware(), AsyncSession (+19 more)

### Community 38 - "Community 38"
Cohesion: 0.18
Nodes (28): buffer_skip_whitespace(), cJSON_bool, case_insensitive_strcmp(), cJSON_Compare(), cJSON_ParseWithLength(), cJSON_ParseWithLengthOpts(), cJSON_PrintBuffered(), cJSON_PrintPreallocated() (+20 more)

### Community 40 - "Community 40"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 41 - "Community 41"
Cohesion: 0.18
Nodes (25): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+17 more)

### Community 42 - "Community 42"
Cohesion: 0.15
Nodes (24): class_id_for_device(), mark_offline(), Mark stale devices offline. Returns number of transitions logged., Mark a device offline and log the transition., Walk gateway_id chain up to the class gateway; return ClassSession.id or None., _sweep_once(), _activity(), q() (+16 more)

### Community 43 - "Community 43"
Cohesion: 0.08
Nodes (14): env(), fixture, #21: co-faculty can run quizzes/polls for their class; outsiders still can't., _teacher(), env(), fixture, #20: quiz/poll details and results follow the class access rule., _teacher() (+6 more)

### Community 44 - "Community 44"
Cohesion: 0.11
Nodes (19): asyncio, get_db(), Async SQLAlchemy engine and session factory., SQLite ignores foreign keys unless asked, per connection., Dependency that yields an async DB session., _sqlite_pragmas(), _device_to_dict(), push_presence() (+11 more)

### Community 45 - "Community 45"
Cohesion: 0.14
Nodes (23): api_key_ok(), Constant-time device API key comparison., authorize(), _by_mac(), caller_for_key(), denial(), device_caller(), DeviceCaller (+15 more)

### Community 46 - "Community 46"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 47 - "Community 47"
Cohesion: 0.12
Nodes (16): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+8 more)

### Community 48 - "Community 48"
Cohesion: 0.12
Nodes (22): make_student(), test_attendance_paths(), count(), live(), fixture, fixture, Smoke steps 1-5: a class whose gateway registered with its room code., setup() (+14 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (21): posix_only, discover(), Run `cmd` and return (exit code, combined output, abort reason). Output is read…, run_streaming(), signal, test_frontend_is_installed_from_its_lockfile(), test_runner_discovers_every_host_suite(), skipif (+13 more)

### Community 50 - "Community 50"
Cohesion: 0.17
Nodes (20): key_digest(), load_public_key(), ValueError, (n, e) from a PEM RSA public key (SubjectPublicKeyInfo, as written by…, The key's Secure Boot V2 digest: SHA-256 over n, e, rinv, mdash as they sit in…, SignatureError, _site_key(), _digest() (+12 more)

### Community 51 - "Community 51"
Cohesion: 0.11
Nodes (20): Session housekeeping: periodic cleanup of expired server-side sessions. Expired…, Background task: periodically delete expired / revoked sessions., session_cleanup_loop(), #15: POST /api/classes/ works (it 500'd on every call)., _stored(), q(), test_admin_route_unaffected(), test_create_class_with_exam_dates_persists_them() (+12 more)

### Community 52 - "Community 52"
Cohesion: 0.14
Nodes (15): answer(), join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, _marker(), _next_command(), #43 end to end: a teacher runs a quiz in a room, and the answers arrive through…, Frames the socket got before a marker broadcast now (so a missing frame fails…, The next frame ws_command.c acts on: it dispatches on "event" and ignores the… (+7 more)

### Community 53 - "Community 53"
Cohesion: 0.17
Nodes (20): functions(), mentions(), {name: body_text} for every top-level function definition in a C file., #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch() (+12 more)

### Community 54 - "Community 54"
Cohesion: 0.27
Nodes (20): _age(), q(), _batch(), beat(), join(), leave(), _modules(), #40: the student module inventory. Modules seen on a gateway's mesh are listed… (+12 more)

### Community 55 - "Community 55"
Cohesion: 0.13
Nodes (12): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, strip_comments_and_strings(), #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), #13: S3 OTA — rollback protection and no reboot when nothing is installed. (+4 more)

### Community 56 - "Community 56"
Cohesion: 0.14
Nodes (19): Require admin or super_admin role., Require teacher, admin, or super_admin role., require_admin(), require_teacher_or_admin(), create_course(), delete_course(), get_course(), list_courses() (+11 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 58 - "Community 58"
Cohesion: 0.19
Nodes (17): cfg_has_device_key(), esp_err_t, esp_event_base_t, _download_and_apply(), _firmware_check(), _get_mac(), _http_post(), _http_post_body() (+9 more)

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 60 - "Community 60"
Cohesion: 0.17
Nodes (16): playwright_sync_api, login(), _open(), #35/#36: the Firmware page and pushing an approved image from Modules., test_invalid_upload_is_explained(), test_push_dialog_without_approved_images_points_to_the_firmware_page(), test_signature_status_is_shown(), test_upload_approve_and_push_from_modules() (+8 more)

### Community 61 - "Community 61"
Cohesion: 0.17
Nodes (16): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts…, Length of the app image itself (segments, checksum, appended SHA-256), without… (+8 more)

### Community 62 - "Community 62"
Cohesion: 0.20
Nodes (17): Digest of the public key every image must be signed with…, site_key_digest(), adopt_legacy_files(), artifact_file(), artifact_path(), AsyncSession, Path, UploadFile (+9 more)

### Community 63 - "Community 63"
Cohesion: 0.14
Nodes (10): ast, conftest, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules() (+2 more)

### Community 64 - "Community 64"
Cohesion: 0.29
Nodes (13): student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join(), student_set_leave(), student_set_root_uptime() (+5 more)

### Community 65 - "Community 65"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 66 - "Community 66"
Cohesion: 0.30
Nodes (14): _device(), q(), _push(), parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report(), test_applied_with_another_version_is_not_success(), test_applied_with_the_pushed_version_completes_the_update() (+6 more)

### Community 67 - "Community 67"
Cohesion: 0.16
Nodes (9): main(), Fail clearly if committed Graphify output is incomplete, stale, or unsafe., source_commit(), subprocess, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards(), _workflow() (+1 more)

### Community 68 - "Community 68"
Cohesion: 0.20
Nodes (13): observe(), AsyncSession, datetime, Student module inventory (#40): which modules each gateway's mesh can see.…, Record a join / leave / heartbeat relayed by `gateway`. Returns the row, or…, Mark silent modules disconnected; returns their gateways' ids., sweep(), _uid() (+5 more)

### Community 69 - "Community 69"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10: only a super admin can grant/remove admin-level roles; roles are a closed…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 70 - "Community 70"
Cohesion: 0.24
Nodes (13): cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput(), msg_t, frame_of() (+5 more)

### Community 71 - "Community 71"
Cohesion: 0.27
Nodes (13): mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main(), simulate(), test_dedup_window_and_wrap(), test_id_ignores_hops_but_not_content() (+5 more)

### Community 72 - "Community 72"
Cohesion: 0.16
Nodes (10): #29: guards for the S3 <-> C6 link as ported from v3…, _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_student_count_comes_from_join_and_leave_only(), test_c6_validates_received_slots(), test_master_drops_a_payload_only_after_a_successful_transfer(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+2 more)

### Community 73 - "Community 73"
Cohesion: 0.23
Nodes (11): append_coverage(), component_for(), enrich(), main(), node_id(), Path, Build imPress's deterministic Graphify graph and enrich non-code coverage.…, Latest commit that changed input, rather than a graph-only bot commit. (+3 more)

### Community 74 - "Community 74"
Cohesion: 0.22
Nodes (10): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+2 more)

### Community 75 - "Community 75"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 76 - "Community 76"
Cohesion: 0.18
Nodes (11): _der(), _mgf1(), pss_verify(), Signed firmware images (#66): ESP-IDF Secure Boot V2 RSA-3072 signatures,…, () if nothing follows the image (unsigned). Otherwise check the padding and…, (tag, start of content, end of content) of the DER element at pos., verify_signature(), base64 (+3 more)

### Community 77 - "Community 77"
Cohesion: 0.18
Nodes (6): ConnectionManager, WebSocket, Send a JSON message to ALL connections in a class room (teachers + devices)., Send a JSON message only to connections matching the given role., Alias for broadcast_to_class., Manages WebSocket connections grouped by class ID. Teachers connect to manage…

### Community 78 - "Community 78"
Cohesion: 0.35
Nodes (12): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+4 more)

### Community 79 - "Community 79"
Cohesion: 0.29
Nodes (9): importlib_util, stat, _backend(), #42: the documented install path: scripts, secrets, version, CI job., test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets() (+1 more)

### Community 80 - "Community 80"
Cohesion: 0.26
Nodes (8): fmt_secs(), main(), markdown_report(), Paint, print_report(), SuiteResult, test_coverage_report_is_parsed_and_shown(), test_markdown_report_lists_every_suite()

### Community 81 - "Community 81"
Cohesion: 0.21
Nodes (11): socket, tempfile, browser(), _free_port(), page(), fixture, Browser UI checks: a real backend on a temp database, driven by Playwright.…, A page that fails the test on any uncaught JS error; screenshot at the end. (+3 more)

### Community 82 - "Community 82"
Cohesion: 0.20
Nodes (10): class_websocket(), _device_key_ok(), websocket, The shared key (unless IMPRESS_DEVICE_KEYS_REQUIRED) or an active-able per-…, Validate a login session token for WebSocket auth. Returns the User or None.…, WebSocket endpoint for real-time class communication. Connect with:…, _ws_user_from_token(), db() (+2 more)

### Community 83 - "Community 83"
Cohesion: 0.24
Nodes (8): cls(), fixture, parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student…, test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons()

### Community 84 - "Community 84"
Cohesion: 0.33
Nodes (11): batch_add(), batch_flush(), batch_flush_needed(), batch_init(), cJSON, item_is_heartbeat(), process_spi_payload(), spi_to_http_task() (+3 more)

### Community 85 - "Community 85"
Cohesion: 0.24
Nodes (8): argparse, call(), env_value(), main(), HTTP smoke test of a running imPress backend (#42): the system audit's…, ssl, urllib_error, uuid

### Community 86 - "Community 86"
Cohesion: 0.31
Nodes (9): device(), set_pending(), go(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download() (+1 more)

### Community 87 - "Community 87"
Cohesion: 0.29
Nodes (8): _create(), ctx(), fixture, parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 88 - "Community 88"
Cohesion: 0.27
Nodes (8): Security review (#16 of the v2.1 brief): every route refuses a caller without…, 401/403, or 422 for the missing device-key header (a required `X-API-Key` is…, _refused(), _routes(), test_device_routes_reject_a_wrong_key(), test_every_route_needs_credentials(), fastapi_routing, importlib

### Community 89 - "Community 89"
Cohesion: 0.22
Nodes (8): init_env(), Path, Create or complete backend/.env from backend/.env.example (#42). The public…, Returns the names of the secrets it generated., sys, _mac(), #38/#34: a staged OTA rollout from the Firmware page., test_preview_start_progress_pause_and_resume()

### Community 90 - "Community 90"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 91 - "Community 91"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 93 - "Community 93"
Cohesion: 0.25
Nodes (4): Api, Tiny JSON client for setting up data the test then checks in the UI., multipart/form-data POST of one file field named 'file'., A device call (X-API-Key), e.g. registration or an OTA status report.

### Community 94 - "Community 94"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 95 - "Community 95"
Cohesion: 0.48
Nodes (6): _open_create_quiz(), #31: importing questions from CSV on the create-quiz page., test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz()

### Community 97 - "Community 97"
Cohesion: 0.50
Nodes (4): health(), datetime, Device health states (#39), computed from the latest heartbeat. Rules, in order…, (state, reasons) for one device.

### Community 99 - "Community 99"
Cohesion: 0.60
Nodes (4): _open(), #32: importing and exporting courses and sections on the Classrooms page., test_invalid_rows_block_the_import(), test_valid_file_creates_courses_and_sections()

### Community 100 - "Community 100"
Cohesion: 0.60
Nodes (4): _beat(), #39: health states and the read-only diagnostics panel on the Modules page., _row(), test_health_badges_and_diagnostics_refresh()

### Community 101 - "Community 101"
Cohesion: 0.50
Nodes (4): Distribution names from a requirements file, following -r includes., _requirements(), test_dev_requirements_cover_every_runtime_requirement(), test_requirements_parsing_follows_includes_and_strips_specifiers()

### Community 102 - "Community 102"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

### Community 104 - "Community 104"
Cohesion: 0.67
Nodes (3): Popen, Terminate the child and everything it started (npm, ninja, docker run)., _stop()

## Knowledge Gaps
- **49 isolated node(s):** `StaleRender`, `ASAN_OPTIONS`, `run.sh script`, `afl-prepare-linux.sh script`, `afl.sh script` (+44 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 913 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **119 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `Community 68` to `Community 1`, `Community 5`, `Community 6`, `Community 10`, `Community 11`, `Community 12`, `Community 13`, `Community 17`, `Community 18`, `Community 19`, `Community 21`, `Community 22`, `Community 23`, `Community 24`, `Community 26`, `Community 30`, `Community 34`, `Community 36`, `Community 37`, `Community 42`, `Community 44`, `Community 45`, `Community 51`, `Community 52`, `Community 54`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `login()` connect `Community 6` to `Community 1`, `Community 13`, `Community 14`, `Community 19`, `Community 20`, `Community 25`, `Community 26`, `Community 29`, `Community 34`, `Community 36`, `Community 41`, `Community 42`, `Community 43`, `Community 46`, `Community 48`, `Community 50`, `Community 51`, `Community 52`, `Community 54`, `Community 66`, `Community 69`, `Community 83`, `Community 86`, `Community 87`, `Community 92`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `auth()` connect `Community 6` to `Community 1`, `Community 13`, `Community 14`, `Community 19`, `Community 20`, `Community 25`, `Community 26`, `Community 29`, `Community 34`, `Community 36`, `Community 41`, `Community 42`, `Community 43`, `Community 46`, `Community 48`, `Community 50`, `Community 51`, `Community 52`, `Community 54`, `Community 66`, `Community 69`, `Community 83`, `Community 86`, `Community 87`, `Community 92`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 155 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 155 INFERRED edges - model-reasoned connections that need verification._
- **Are the 110 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 110 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `ASAN_OPTIONS`, `run.sh script` to the rest of the system?**
  _49 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05183861082737487 - nodes in this community are weakly interconnected._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
