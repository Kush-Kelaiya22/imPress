# Graph Report - imPress  (2026-10-13)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3328 nodes · 9240 edges · 231 communities (103 shown, 128 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1396 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `783e43fc`
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
- Community 129
- Community 135
- Community 136
- Community 227
- Community 228
- Community 229
- Community 230

## God Nodes (most connected - your core abstractions)
1. `select()` - 168 edges
2. `User` - 154 edges
3. `login()` - 144 edges
4. `auth()` - 142 edges
5. `EspDevice` - 106 edges
6. `istnow()` - 104 edges
7. `ClassSession` - 96 edges
8. `make_user()` - 91 edges
9. `_post()` - 77 edges
10. `log_activity()` - 72 edges

## Surprising Connections (you probably didn't know these)
- `test_every_setting_is_documented()` --uses--> `Settings`  [INFERRED]
  tests/test_docs_consistency.py → backend/app/config.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_fault_injection.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_device_keys.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_auth_sessions.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_create.py → run_tests.py

## Import Cycles
- None detected.

## Communities (231 total, 128 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (116): log_activity(), AsyncSession, Write one activity log entry., User, allowed(), can_grant(), Enrol or remove students, list a class roster: the primary teacher or an…, Granting or taking away an administrative role needs users.assign_role. (+108 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (85): authorize(), _by_mac(), denial(), device_caller(), DeviceCaller, new_device_key(), AsyncSession, (raw key for the device, hash to store). (+77 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (80): auth(), login(), fixture, su(), parametrize, Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py…, _session_row(), q() (+72 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (72): backend_fail_t, errno, esp_event_handler_t, esp_tls_crypto, esp_tls_errors, esp_transport, esp_transport_ssl, esp_transport_tcp (+64 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (61): adc_oneshot, crypto, esp_crt_bundle, esp_heap_caps, esp_http_client, esp_log, esp_netif, esp_ota_handle_t (+53 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (67): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+59 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (61): platform, Popen, posix_only, CaseResult, discover(), fmt_secs(), _idf_command(), _idf_image_present() (+53 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (64): ActivityLogResponse, AdminUserCreate, BulkStudentRegister, ClassAssignTeacher, ClassCreate, ClassDevicesResponse, ClassFacultyUpdate, ClassJoin (+56 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (61): nvs_handle_t, cfg_clear_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str(), _store_dev_key(), ota_c6_boot_check() (+53 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (64): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+56 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (56): AsyncConnection, AsyncEngine, _add_columns(), add_deployment_deferral(), add_device_keys(), add_diagnostics_columns(), add_firmware_signer(), add_quiz_question_started_at() (+48 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (60): DeploymentTarget, FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., _act(), cancel_deployment(), create_deployment(), deployment_dict() (+52 more)

### Community 13 - "Community 13"
Cohesion: 0.05
Nodes (45): answer(), Gateway, join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent… (+37 more)

### Community 14 - "Community 14"
Cohesion: 0.09
Nodes (49): cJSON_Hooks, add_item_to_array(), add_item_to_object(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddBoolToObject(), cJSON_AddFalseToObject(), cJSON_AddItemReferenceToArray() (+41 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (42): asyncio, Activity logging service — records all significant actions., api_key_ok(), Application configuration loaded from environment variables., Constant-time device API key comparison., get_db(), Async SQLAlchemy engine and session factory., SQLite ignores foreign keys unless asked, per connection. (+34 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (47): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts…, Length of the app image itself (segments, checksum, appended SHA-256), without… (+39 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (43): check_secure(), insecure_settings(), Names of settings still at their public, repo-published defaults., Refuse to run with published secrets, or with unauthenticated WebSockets…, Settings, _reset_db(), _beat(), _device() (+35 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (47): make_class(), make_user(), Create a user through the admin API; returns (user_id, auth headers)., Create a class via /api/admin/classes; optionally activate it., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password() (+39 more)

### Community 19 - "Community 19"
Cohesion: 0.07
Nodes (17): assert, cjson, esp_err, esp_event, esp_idf_version, esp_transport_ws, read_file(), main() (+9 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (49): ClassOccurrenceException, ClassSession, One dated change to a class's weekly timetable (meeting_schedule). cancelled:…, class_access(), class_owner_or_admin(), Delete a class: its primary teacher or an administrator., Work with a class: its primary teacher, any co-faculty member, or an…, Re-select a class after mutation so selectin relationships load in the async… (+41 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (48): cJSON_AddItemToArray(), cJSON_AddItemToObject(), cJSON_CreateObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc() (+40 more)

### Community 22 - "Community 22"
Cohesion: 0.07
Nodes (45): Any, When each authoritative timetable source last synchronised (#126/#127). No row…, ScheduleSource, _at(), Busy, find_schedule_conflicts(), occupancy(), _parse_time() (+37 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (38): playwright_sync_api, time, login(), Browser UI checks: a real backend on a temp database, driven by Playwright.…, _open(), #32: importing and exporting courses and sections on the Classrooms page., test_invalid_rows_block_the_import(), test_valid_file_creates_courses_and_sections() (+30 more)

### Community 24 - "Community 24"
Cohesion: 0.10
Nodes (37): esp_efuse, esp_mac, display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown(), display_show_provision_state() (+29 more)

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (39): Course, create_course(), delete_course(), get_course(), list_courses(), AsyncSession, delete, get (+31 more)

### Community 26 - "Community 26"
Cohesion: 0.09
Nodes (37): create_access_token(), create_session(), generate_session_token(), get_current_user(), get_current_user_light(), _load_session_by_hash(), AsyncSession, Request (+29 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (38): Base, Attendance, Student, StudentEnrollment, Resolve a student row from a batch message. Student identity is the ENROLLMENT…, _resolve_student_id_by_enrollment(), bulk_create_students(), _create_one() (+30 more)

### Community 28 - "Community 28"
Cohesion: 0.09
Nodes (36): config, esp_app_desc, spi_slave_transaction_t, queue_slot(), ready_update(), spi_post_trans_cb(), spi_slave_init(), spi_slave_send() (+28 more)

### Community 29 - "Community 29"
Cohesion: 0.08
Nodes (31): argparse, client(), _drain_background_tasks(), fixture, Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, TestClient on an empty database (the app seeds the super admin)., _next_device_frame(), _project() (+23 more)

### Community 30 - "Community 30"
Cohesion: 0.09
Nodes (33): hash_password(), Revoke every session of a user (except `keep_id`), in the caller's transaction…, revoke_user_sessions(), verify_password(), init_db(), Create missing tables and apply pending migrations (stops on failure)., lifespan(), Create tables and seed a default super admin on startup. (+25 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (32): BaseType_t, xSemaphoreGive(), xSemaphoreTake(), handle_c6_frame(), heartbeat_task(), spi_link_task(), esp_now_recv_info_t, msg_type_t (+24 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (32): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, _response(), UploadFile, Read an uploaded file, refusing anything larger than max_bytes (413)., read_upload(), Digest of the public key every image must be signed with…, site_key_digest() (+24 more)

### Community 33 - "Community 33"
Cohesion: 0.22
Nodes (30): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+22 more)

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (28): spi_slave_read(), msg_t, spi_slot_fifo_t, crc16_ccitt(), json_get_string(), msg_decode(), msg_verify_crc(), spi_record_read() (+20 more)

### Community 35 - "Community 35"
Cohesion: 0.17
Nodes (27): wire(), _advance(), _artifact(), at(), clock(), _deploy(), _gateway(), h() (+19 more)

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (29): approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get(), _latest_approved(), list_firmware() (+21 more)

### Community 37 - "Community 37"
Cohesion: 0.12
Nodes (24): esp_bit_defs, event_groups, cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), esp_err_t, esp_event_base_t, _download_and_apply() (+16 more)

### Community 38 - "Community 38"
Cohesion: 0.18
Nodes (24): _get(), _mesh_answer(), _per_question(), parametrize, #73: timed quizzes advance (per_question) and end (total) by themselves, the…, Pretend the current question / the quiz started `seconds` earlier., _shift(), go() (+16 more)

### Community 40 - "Community 40"
Cohesion: 0.11
Nodes (24): _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), health(), get, Request (+16 more)

### Community 41 - "Community 41"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 42 - "Community 42"
Cohesion: 0.18
Nodes (25): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+17 more)

### Community 43 - "Community 43"
Cohesion: 0.12
Nodes (24): esp_now, esp_random, esp_wifi, mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main() (+16 more)

### Community 44 - "Community 44"
Cohesion: 0.23
Nodes (24): Poll, PollVote, Validate + de-duplicate one mesh poll vote ((poll, student) is unique)., _record_poll_vote(), create_poll(), end_poll(), get_poll(), list_polls() (+16 more)

### Community 45 - "Community 45"
Cohesion: 0.11
Nodes (21): _calls(), The authorization policy is the one place that decides access (#122)., A staff route without a policy permission is a new hole; device routes…, Role checks scattered across routers drifted before (#19-#21, #116, #121)., docs/design/authorization.md shows GRANTS; it must not drift., _routes(), test_every_route_is_governed_by_the_policy_or_listed(), test_no_role_comparisons_outside_the_policy() (+13 more)

### Community 46 - "Community 46"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 47 - "Community 47"
Cohesion: 0.21
Nodes (25): buffer_skip_whitespace(), cJSON_bool, cJSON_Compare(), cJSON_ParseWithLength(), cJSON_ParseWithLengthOpts(), cJSON_PrintPreallocated(), compare_double(), ensure() (+17 more)

### Community 48 - "Community 48"
Cohesion: 0.14
Nodes (25): cJSON, case_insensitive_strcmp(), cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive(), cJSON_DetachItemFromArray(), cJSON_DetachItemFromObject(), cJSON_DetachItemFromObjectCaseSensitive() (+17 more)

### Community 49 - "Community 49"
Cohesion: 0.12
Nodes (16): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+8 more)

### Community 50 - "Community 50"
Cohesion: 0.23
Nodes (23): Quiz, Example file with every column. Public: it contains no data., create_quiz(), get_quiz(), import_question_csv(), list_quizzes(), next_question(), AsyncSession (+15 more)

### Community 51 - "Community 51"
Cohesion: 0.12
Nodes (22): make_student(), test_attendance_paths(), count(), live(), fixture, fixture, Smoke steps 1-5: a class whose gateway registered with its room code., setup() (+14 more)

### Community 52 - "Community 52"
Cohesion: 0.15
Nodes (21): functions(), mentions(), {name: body_text} for every top-level function definition in a C file., #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch() (+13 more)

### Community 53 - "Community 53"
Cohesion: 0.17
Nodes (22): QuizAnswer, _count(), q(), _fk_violations(), q(), _insert_twice(), go(), #41: the database enforces its own integrity (foreign keys, uniqueness), and… (+14 more)

### Community 54 - "Community 54"
Cohesion: 0.10
Nodes (14): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, #132: both backend clients classify a failure and log the hint, and the boot…, test_connection_failures_say_why(), test_every_backend_client_gets_the_tls_settings(), #33: OTA root causes stay fixed (version source, premature success, unchecked…, test_download_checks_http_status_before_touching_flash(), test_s3_result_is_an_spi_record_and_the_c6_relays_it() (+6 more)

### Community 55 - "Community 55"
Cohesion: 0.18
Nodes (20): Mark stale devices offline. Returns number of transitions logged., _sweep_once(), _activity(), q(), _device(), q(), fixture, Gateway-facing device API (routers/device.py) + presence service… (+12 more)

### Community 56 - "Community 56"
Cohesion: 0.10
Nodes (11): ConnectionManager, WebSocket, Send a JSON message to ALL connections in a class room (teachers + devices)., Send a JSON message only to connections matching the given role., Alias for broadcast_to_class., Manages WebSocket connections grouped by class ID. Teachers connect to manage…, Close every socket of a user whose access was revoked (#118)., FakeWS (+3 more)

### Community 57 - "Community 57"
Cohesion: 0.16
Nodes (19): make_image(), _count(), q(), parametrize, #35: uploaded firmware is validated as a real imPress image and registered…, Against genuine ESP-IDF output when a local build exists (the synthetic images…, A scripts/build_signed.sh build (#66), when one exists locally., test_a_c6_image_is_never_pushed_to_an_s3() (+11 more)

### Community 58 - "Community 58"
Cohesion: 0.11
Nodes (12): parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student…, test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons(), #43 fault injection on the answer path: what the gateway's retry rules (keep a…, parametrize (+4 more)

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (18): _add(), _busy(), phy(), fixture, parametrize, Dated timetable changes and room occupancy (#126). 2026-10-12 is a Monday,…, su(), test_a_cancelled_day_frees_every_slot() (+10 more)

### Community 60 - "Community 60"
Cohesion: 0.27
Nodes (20): _age(), q(), _batch(), beat(), join(), leave(), _modules(), #40: the student module inventory. Modules seen on a gateway's mesh are listed… (+12 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (15): calls(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset(), test_only_401_drops_the_key(), test_register_stores_the_issued_key_on_both_boards(), test_the_shared_key_is_kept_for_re_registration(), #29: guards for the S3 <-> C6 link as ported from v3…, _src() (+7 more)

### Community 62 - "Community 62"
Cohesion: 0.13
Nodes (17): parse_question_csv(), UploadFile, Validate a question CSV and return a per-row preview. Stores nothing: the…, question_warnings(), QuestionImportReport, All-or-nothing: any invalid row means nothing is imported; duplicates are…, csv_safe(), CsvFileError (+9 more)

### Community 63 - "Community 63"
Cohesion: 0.19
Nodes (19): advance(), answer_closed(), deadline(), finish(), AsyncSession, datetime, quiz_timer_loop(), Quiz timing (#73): advance `per_question` quizzes and end `total` quizzes when… (+11 more)

### Community 64 - "Community 64"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 65 - "Community 65"
Cohesion: 0.15
Nodes (16): json, append_coverage(), component_for(), enrich(), main(), node_id(), Path, Build imPress's deterministic Graphify graph and enrich non-code coverage.… (+8 more)

### Community 66 - "Community 66"
Cohesion: 0.25
Nodes (15): msg_type_t, msg_to_json(), student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join() (+7 more)

### Community 67 - "Community 67"
Cohesion: 0.16
Nodes (17): ClassImportReport, ClassImportRow, All-or-nothing: any invalid row means nothing is imported., apply_class_import(), _changes(), export_rows(), plan_class_import(), AsyncSession (+9 more)

### Community 68 - "Community 68"
Cohesion: 0.25
Nodes (16): _device(), q(), hub(), _push(), fixture, parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report() (+8 more)

### Community 69 - "Community 69"
Cohesion: 0.23
Nodes (15): _artifact(), _deploy(), _download(), h(), fixture, TrustedInstaller (#123): firmware reaches a device only after its own checks,…, The production defaults: no unsigned images, no self-approval., _register() (+7 more)

### Community 70 - "Community 70"
Cohesion: 0.15
Nodes (9): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat() (+1 more)

### Community 71 - "Community 71"
Cohesion: 0.17
Nodes (13): _exec(), fixture, DELETE /api/admin/users/{id} removes the account and settles references (#117)., A new column pointing at users.id must decide what deletion does to it., _rows(), go(), su(), test_delete_removes_account_and_keeps_history() (+5 more)

### Community 72 - "Community 72"
Cohesion: 0.15
Nodes (10): _publish_graph_visualization(), Sphinx configuration for the public imPress documentation site., Expose the generated graph beneath the hosted ``/graph/`` page., setup(), shutil, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards() (+2 more)

### Community 73 - "Community 73"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 74 - "Community 74"
Cohesion: 0.35
Nodes (14): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), _artifact(), _hub(), _push(), #36: firmware version manager: approval, deprecation, retention, usage., _set(), test_admin_only() (+6 more)

### Community 75 - "Community 75"
Cohesion: 0.19
Nodes (13): _me(), parametrize, At least one active super admin always remains (#116). The original failure: a…, The original lockout path: PUT with is_active=false on yourself (#116, #119)., Two super admins disabling each other at the same moment: one must fail., test_concurrent_mutual_deactivation_leaves_one_super_admin(), deactivate(), race() (+5 more)

### Community 76 - "Community 76"
Cohesion: 0.30
Nodes (14): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+6 more)

### Community 77 - "Community 77"
Cohesion: 0.23
Nodes (14): cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput(), msg_t (+6 more)

### Community 78 - "Community 78"
Cohesion: 0.20
Nodes (11): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+3 more)

### Community 79 - "Community 79"
Cohesion: 0.13
Nodes (11): Api, browser(), _free_port(), page(), fixture, A page that fails the test on any uncaught JS error; screenshot at the end., Tiny JSON client for setting up data the test then checks in the UI., multipart/form-data POST of one file field named 'file'. (+3 more)

### Community 80 - "Community 80"
Cohesion: 0.34
Nodes (13): answer(), batch(), count(), q(), parametrize, #6: /api/device/batch validates and de-duplicates mesh answers/votes., test_distinct_students_and_questions_all_count(), test_inactive_quiz_and_closed_poll_skipped() (+5 more)

### Community 81 - "Community 81"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10, #119: only a super admin can grant/remove admin-level roles; roles are a…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 82 - "Community 82"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 83 - "Community 83"
Cohesion: 0.24
Nodes (10): main(), _lock_out(), Offline recovery of a locked-out installation (#120)., A database from before #116: no triggers, every super admin inactive., _restore(), _sql(), test_cli_exit_codes(), test_promotes_an_existing_account() (+2 more)

### Community 84 - "Community 84"
Cohesion: 0.21
Nodes (12): fixture, parametrize, Separate account operations and server-provided allowed_actions (#119)., Whatever allowed_actions leaves out, the route refuses (UI is not the guard)., _row(), su(), test_allowed_actions_for_a_super_admin(), test_allowed_actions_for_an_admin() (+4 more)

### Community 85 - "Community 85"
Cohesion: 0.27
Nodes (10): QuizQuestion, _history(), fill(), Loading a user or a class list must not pull in the teaching history (#133).…, statements(), test_class_list_counts_without_loading_quizzes(), test_loading_a_user_is_one_statement(), load() (+2 more)

### Community 86 - "Community 86"
Cohesion: 0.24
Nodes (11): health(), datetime, (state, reasons) for one device., _dev(), parametrize, #39: device health states from the latest heartbeat diagnostics., test_heartbeat_stores_diagnostics_and_old_firmware_still_works(), get() (+3 more)

### Community 87 - "Community 87"
Cohesion: 0.18
Nodes (4): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #66: the signed-app profile and the scripts that build with it.

### Community 88 - "Community 88"
Cohesion: 0.20
Nodes (9): push_device_status(), push_poll_to_mesh(), push_quiz_to_mesh(), push_student_data(), Bridge service: connects ESP device data to WebSocket clients. This service…, Push student device data (heartbeats, answers, votes) to teacher dashboard., Push individual device status update., Push quiz question through WebSocket → C6 → SPI → S3 → mesh → students. (+1 more)

### Community 89 - "Community 89"
Cohesion: 0.42
Nodes (9): _class(), _gateway_of(), q(), #17: registration must not steal a class's gateway link., _register(), test_explicit_classroom_code_still_assigns(), test_gateway_keeps_its_class_on_reregister(), test_non_gateway_registration_keeps_class_gateway() (+1 more)

### Community 90 - "Community 90"
Cohesion: 0.29
Nodes (8): _create(), ctx(), fixture, parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 91 - "Community 91"
Cohesion: 0.24
Nodes (8): call(), env_value(), main(), HTTP smoke test of a running imPress backend (#42): the system audit's…, ssl, urllib_error, urllib_request, uuid

### Community 92 - "Community 92"
Cohesion: 0.22
Nodes (9): class_websocket(), _device_refusal(), websocket, WebSocket endpoint for real-time class communication. Connect with:…, Why a device may not join this class room, or None (#66, #121). A per-device…, Refresh presence for the device that spoke over WS. The C6's primary heartbeat…, Validate a login session token for WebSocket auth. Returns the User or None.…, _touch_device_on_message() (+1 more)

### Community 93 - "Community 93"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 94 - "Community 94"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 96 - "Community 96"
Cohesion: 0.29
Nodes (4): env(), fixture, #21: co-faculty can run quizzes/polls for their class; outsiders still can't., _teacher()

### Community 97 - "Community 97"
Cohesion: 0.43
Nodes (7): device(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download(), test_only_the_pushed_version_downloads()

### Community 98 - "Community 98"
Cohesion: 0.29
Nodes (4): env(), fixture, #20: quiz/poll details and results follow the class access rule., _teacher()

### Community 99 - "Community 99"
Cohesion: 0.33
Nodes (6): as_ist(), datetime, Indian Standard Time (IST) helpers — the backend's single source of truth for…, Convert any aware/naive datetime to naive IST; naive input is treated as UTC., test_as_ist_treats_naive_as_utc(), zoneinfo

### Community 100 - "Community 100"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 101 - "Community 101"
Cohesion: 0.33
Nodes (5): env(), add_student(), pause_scheduler(), fixture, Stop the app's own 1 s loop from racing the explicit ticks below (it looks…

### Community 102 - "Community 102"
Cohesion: 0.53
Nodes (5): _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client()

### Community 103 - "Community 103"
Cohesion: 0.50
Nodes (5): commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, test_commit_or_conflict_turns_a_unique_violation_into_409(), race()

### Community 105 - "Community 105"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

## Knowledge Gaps
- **50 isolated node(s):** `StaleRender`, `ASAN_OPTIONS`, `run.sh script`, `afl-prepare-linux.sh script`, `afl.sh script` (+45 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1003 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **128 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `Community 26` to `Community 0`, `Community 1`, `Community 2`, `Community 11`, `Community 12`, `Community 13`, `Community 15`, `Community 22`, `Community 30`, `Community 33`, `Community 36`, `Community 40`, `Community 44`, `Community 50`, `Community 55`, `Community 58`, `Community 60`, `Community 63`, `Community 92`, `Community 99`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `select()` connect `Community 44` to `Community 0`, `Community 1`, `Community 2`, `Community 7`, `Community 12`, `Community 13`, `Community 15`, `Community 17`, `Community 20`, `Community 22`, `Community 25`, `Community 26`, `Community 27`, `Community 29`, `Community 30`, `Community 32`, `Community 33`, `Community 35`, `Community 36`, `Community 42`, `Community 46`, `Community 50`, `Community 51`, `Community 53`, `Community 55`, `Community 57`, `Community 60`, `Community 63`, `Community 67`, `Community 68`, `Community 80`, `Community 85`, `Community 86`, `Community 89`, `Community 92`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `User` connect `Community 0` to `Community 2`, `Community 67`, `Community 36`, `Community 40`, `Community 75`, `Community 12`, `Community 44`, `Community 45`, `Community 15`, `Community 50`, `Community 20`, `Community 85`, `Community 62`, `Community 25`, `Community 26`, `Community 27`, `Community 30`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 164 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 164 INFERRED edges - model-reasoned connections that need verification._
- **Are the 130 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 130 INFERRED edges - model-reasoned connections that need verification._
- **Are the 73 inferred relationships involving `EspDevice` (e.g. with `_by_mac()` and `caller_for_key()`) actually correct?**
  _`EspDevice` has 73 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `ASAN_OPTIONS`, `run.sh script` to the rest of the system?**
  _50 weakly-connected nodes found - possible documentation gaps or missing edges._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
