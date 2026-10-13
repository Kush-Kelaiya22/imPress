# Graph Report - imPress  (2026-10-13)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3513 nodes · 9698 edges · 235 communities (107 shown, 128 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1431 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fc052327`
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
- Community 128
- Community 129
- Community 130
- Community 131
- Community 133
- Community 139
- Community 140
- Community 231
- Community 232
- Community 233
- Community 234

## God Nodes (most connected - your core abstractions)
1. `select()` - 169 edges
2. `User` - 154 edges
3. `login()` - 153 edges
4. `auth()` - 151 edges
5. `EspDevice` - 109 edges
6. `istnow()` - 107 edges
7. `ClassSession` - 96 edges
8. `make_user()` - 93 edges
9. `_post()` - 77 edges
10. `log_activity()` - 72 edges

## Surprising Connections (you probably didn't know these)
- `test_every_setting_is_documented()` --uses--> `Settings`  [INFERRED]
  tests/test_docs_consistency.py → backend/app/config.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_db_integrity.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_device_api.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_device_batch_dedup.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_device_keys.py → run_tests.py

## Import Cycles
- None detected.

## Communities (235 total, 128 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (103): log_activity(), AsyncSession, Write one activity log entry., User, admin_class_devices(), admin_create_class(), admin_delete_class(), admin_get_module() (+95 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (83): _cleanup_once(), Delete sessions that are hard-expired, idle-expired, or revoked. Returns the…, auth(), login(), fixture, su(), parametrize, Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py… (+75 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (74): asyncio, check_secure(), insecure_settings(), Application configuration loaded from environment variables., Refuse to run with published secrets, or with unauthenticated WebSockets…, Names of settings still at their public, repo-published defaults., Settings, init_db() (+66 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (69): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+61 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (30): cjson, esp_app_desc, esp_bit_defs, esp_efuse, esp_err, esp_event, esp_idf_version, esp_system (+22 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (67): api_key_ok(), Constant-time device API key comparison., authorize(), _by_mac(), caller_for_key(), denial(), device_caller(), DeviceCaller (+59 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (66): ActivityLogResponse, AdminUserCreate, BulkStudentRegister, ClassAssignTeacher, ClassCreate, ClassDevicesResponse, ClassFacultyUpdate, ClassJoin (+58 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (62): config, nvs_handle_t, cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str() (+54 more)

### Community 9 - "Community 9"
Cohesion: 0.06
Nodes (61): platform, Popen, posix_only, CaseResult, discover(), fmt_secs(), _idf_command(), _idf_image_present() (+53 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (61): create_access_token(), generate_session_token(), get_current_user(), get_current_user_light(), hash_password(), _load_session_by_hash(), AsyncSession, Request (+53 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (64): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+56 more)

### Community 12 - "Community 12"
Cohesion: 0.07
Nodes (62): Any, ClassOccurrenceException, ClassSession, One dated change to a class's weekly timetable (meeting_schedule). cancelled:…, account_refusal(), allowed(), can_grant(), class_access() (+54 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (58): AsyncConnection, AsyncEngine, _add_columns(), add_deployment_deferral(), add_device_caps(), add_device_keys(), add_diagnostics_columns(), add_firmware_qualification() (+50 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (63): esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client_config_t, esp_websocket_client_handle_t, esp_websocket_error_type_t (+55 more)

### Community 15 - "Community 15"
Cohesion: 0.08
Nodes (57): DeploymentTarget, FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., _act(), cancel_deployment(), create_deployment(), deployment_dict() (+49 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (49): make_user(), Create a user through the admin API; returns (user_id, auth headers)., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password(), test_admin_password_reset(), test_create_user_field_limits() (+41 more)

### Community 17 - "Community 17"
Cohesion: 0.08
Nodes (43): esp_random, esp_wifi, display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown(), display_show_provision_state() (+35 more)

### Community 18 - "Community 18"
Cohesion: 0.08
Nodes (46): advance(), answer_closed(), deadline(), finish(), AsyncSession, datetime, quiz_timer_loop(), Quiz timing (#73): advance `per_question` quizzes and end `total` quizzes when… (+38 more)

### Community 19 - "Community 19"
Cohesion: 0.06
Nodes (33): answer(), Gateway, join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent… (+25 more)

### Community 20 - "Community 20"
Cohesion: 0.15
Nodes (46): cJSON_AddItemToObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc(), apply_patch(), cJSON (+38 more)

### Community 21 - "Community 21"
Cohesion: 0.10
Nodes (44): Quiz, QuizQuestion, Example file with every column. Public: it contains no data., create_quiz(), get_quiz(), import_question_csv(), list_quizzes(), next_question() (+36 more)

### Community 22 - "Community 22"
Cohesion: 0.09
Nodes (45): Student, bulk_create_students(), _create_one(), create_student(), deactivate_student(), get_student(), hard_delete_student(), import_students_csv() (+37 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (42): class_modules(), _device_to_dict(), mark_offline(), presence_snapshot(), presence_sweep_loop(), push_presence(), datetime, ESP device presence monitoring (online/offline logs). Requirement: the backend… (+34 more)

### Community 24 - "Community 24"
Cohesion: 0.06
Nodes (25): Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, Smoke tests: the app boots on an empty DB and its basic contracts hold., test_seeded_super_admin_can_log_in(), env(), fixture, #21: co-faculty can run quizzes/polls for their class; outsiders still can't., _teacher(), parametrize (+17 more)

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (39): adc_oneshot, crypto, esp_heap_caps, esp_http_client, esp_ota_handle_t, esp_partition_t, esp_timer, app_main() (+31 more)

### Community 26 - "Community 26"
Cohesion: 0.09
Nodes (38): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts…, Length of the app image itself (segments, checksum, appended SHA-256), without… (+30 more)

### Community 27 - "Community 27"
Cohesion: 0.12
Nodes (38): cJSON_Hooks, buffer_skip_whitespace(), cJSON_bool, case_insensitive_strcmp(), cJSON_Compare(), cJSON_InitHooks(), cJSON_Minify(), cJSON_ParseWithLength() (+30 more)

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (35): playwright_sync_api, login(), _open(), #32: importing and exporting courses and sections on the Classrooms page., test_invalid_rows_block_the_import(), test_valid_file_creates_courses_and_sections(), _beat(), #39: health states and the read-only diagnostics panel on the Modules page. (+27 more)

### Community 29 - "Community 29"
Cohesion: 0.12
Nodes (37): Course, create_course(), delete_course(), get_course(), list_courses(), AsyncSession, delete, get (+29 more)

### Community 30 - "Community 30"
Cohesion: 0.11
Nodes (33): Base, Attendance, PollVote, QuizAnswer, SQLAlchemy ORM models for imPress., A student module seen on a gateway's mesh (#40): presence, not location. One…, StudentEnrollment, StudentModule (+25 more)

### Community 31 - "Community 31"
Cohesion: 0.12
Nodes (36): batch_init(), add_item_to_object(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddBoolToObject(), cJSON_AddFalseToObject(), cJSON_AddItemToObjectCS(), cJSON_AddNullToObject() (+28 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (33): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get() (+25 more)

### Community 33 - "Community 33"
Cohesion: 0.10
Nodes (28): esp_chip_info, esp_crt_bundle, esp_flash, esp_mac, esp_ota_ops, esp_psram, cfg_clear_device_key(), cfg_has_device_key() (+20 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (29): make_class(), Create a class via /api/admin/classes; optionally activate it., Classes (routers/classes.py, admin class routes) and courses…, test_activate_deactivate_toggle(), test_back_to_back_slots_do_not_warn(), test_class_codes_are_unique(), test_join_requires_known_active_code(), test_other_teachers_class_is_forbidden() (+21 more)

### Community 35 - "Community 35"
Cohesion: 0.13
Nodes (32): BaseType_t, esp_now, xSemaphoreGive(), xSemaphoreTake(), msg_t, handle_c6_frame(), heartbeat_task(), on_student_message() (+24 more)

### Community 36 - "Community 36"
Cohesion: 0.13
Nodes (30): spi_slave_read(), msg_t, spi_slot_fifo_t, crc16_ccitt(), json_get_string(), msg_decode(), msg_verify_crc(), spi_record_read() (+22 more)

### Community 37 - "Community 37"
Cohesion: 0.08
Nodes (25): os, init_env(), Path, Create or complete backend/.env from backend/.env.example (#42). The public…, Returns the names of the secrets it generated., secrets, socket, sys (+17 more)

### Community 38 - "Community 38"
Cohesion: 0.21
Nodes (31): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+23 more)

### Community 39 - "Community 39"
Cohesion: 0.16
Nodes (28): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), _artifact(), _hub(), _push(), #36: firmware version manager: approval, deprecation, retention, usage., _set(), test_admin_only() (+20 more)

### Community 40 - "Community 40"
Cohesion: 0.08
Nodes (19): client(), _drain_background_tasks(), fixture, TestClient on an empty database (the app seeds the super admin)., _reset_db(), _fresh_settings(), #11: no working public credentials or debug leaks by default., test_cors_only_configured_origins() (+11 more)

### Community 41 - "Community 41"
Cohesion: 0.13
Nodes (28): spi_slave_transaction_t, queue_slot(), spi_post_trans_cb(), spi_slave_init(), esp_err_t, SemaphoreHandle_t, spi_slave_transaction_t, TickType_t (+20 more)

### Community 42 - "Community 42"
Cohesion: 0.11
Nodes (25): ClassImportReport, ClassImportRow, All-or-nothing: any invalid row means nothing is imported., apply_class_import(), _changes(), export_rows(), plan_class_import(), AsyncSession (+17 more)

### Community 43 - "Community 43"
Cohesion: 0.18
Nodes (26): advance(), ota_rx_t, has(), ota_chunk_count(), ota_chunk_len(), ota_rx_accept(), ota_rx_complete(), ota_rx_init() (+18 more)

### Community 45 - "Community 45"
Cohesion: 0.11
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 46 - "Community 46"
Cohesion: 0.18
Nodes (25): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+17 more)

### Community 47 - "Community 47"
Cohesion: 0.12
Nodes (21): functions(), {name: body_text} for every top-level function definition in a C file., #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #7: the S3 loads its config before the mesh uses g_cfg.mesh_channel, and a…, test_config_loaded_before_mesh_init(), test_config_loader_initialises_nvs_itself(), test_mesh_init_reads_channel_from_config() (+13 more)

### Community 48 - "Community 48"
Cohesion: 0.12
Nodes (21): _Device, ota_client(), The OTA client of a gateway or hub, as the firmware implements it., The image must go through the simulated client, and each corruption must be…, _artifact(), _fail_report(), _problems(), parametrize (+13 more)

### Community 49 - "Community 49"
Cohesion: 0.13
Nodes (26): add_item_to_array(), cJSON, cJSON_AddItemReferenceToArray(), cJSON_AddItemReferenceToObject(), cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive(), cJSON_DetachItemFromArray() (+18 more)

### Community 50 - "Community 50"
Cohesion: 0.12
Nodes (22): make_student(), test_attendance_paths(), _matrix(), parametrize, Route × caller matrix (#122): which status every route returns to each kind of…, _seed(), test_route_matrix_matches_snapshot(), fixture (+14 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 52 - "Community 52"
Cohesion: 0.12
Nodes (16): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+8 more)

### Community 53 - "Community 53"
Cohesion: 0.13
Nodes (20): Digest of the public key every image must be signed with…, site_key_digest(), board_refusal(), _intact_bytes(), TrustedInstaller (Ring −2): the last check before firmware reaches a device…, The stored image, if it still has its registered size and SHA-256., The qualification report (#154); computed from the stored bytes for an image…, Does the image fit this board (#129)? Only checked where the board reported its… (+12 more)

### Community 54 - "Community 54"
Cohesion: 0.12
Nodes (19): _calls(), The authorization policy is the one place that decides access (#122)., A staff route without a policy permission is a new hole; device routes…, Role checks scattered across routers drifted before (#19-#21, #116, #121)., docs/design/authorization.md shows GRANTS; it must not drift., _routes(), test_every_route_is_governed_by_the_policy_or_listed(), test_no_role_comparisons_outside_the_policy() (+11 more)

### Community 55 - "Community 55"
Cohesion: 0.10
Nodes (11): ConnectionManager, WebSocket, Send a JSON message to ALL connections in a class room (teachers + devices)., Send a JSON message only to connections matching the given role., Alias for broadcast_to_class., Manages WebSocket connections grouped by class ID. Teachers connect to manage…, Close every socket of a user whose access was revoked (#118)., FakeWS (+3 more)

### Community 56 - "Community 56"
Cohesion: 0.16
Nodes (19): make_image(), _count(), q(), parametrize, #35: uploaded firmware is validated as a real imPress image and registered…, Against genuine ESP-IDF output when a local build exists (the synthetic images…, A scripts/build_signed.sh build (#66), when one exists locally., test_a_c6_image_is_never_pushed_to_an_s3() (+11 more)

### Community 57 - "Community 57"
Cohesion: 0.26
Nodes (19): _advance(), _artifact(), at(), clock(), _deploy(), _gateway(), fixture, Hub and gateway updates only in classroom downtime (#128). The room RM-1 has… (+11 more)

### Community 58 - "Community 58"
Cohesion: 0.13
Nodes (17): assert, backend_fail_t, errno, esp_log, esp_netif, esp_tls_errors, esp_websocket_client, esp_event_base_t (+9 more)

### Community 59 - "Community 59"
Cohesion: 0.16
Nodes (18): _der(), load_public_key(), (tag, start of content, end of content) of the DER element at pos., (n, e) from a PEM RSA public key (SubjectPublicKeyInfo, as written by…, _digest(), fixture, parametrize, #66 (2/3): signed firmware. The verifier is checked against images signed by… (+10 more)

### Community 60 - "Community 60"
Cohesion: 0.17
Nodes (18): _add(), _busy(), phy(), fixture, parametrize, Dated timetable changes and room occupancy (#126). 2026-10-12 is a Monday,…, su(), test_a_cancelled_day_frees_every_slot() (+10 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (17): create_session(), Create a new server-side session for the user. Returns (session_row,…, _sha256_hex(), Older versions stored the raw bearer token in user_sessions.session_token. Any…, _scrub_raw_session_tokens(), UserSession, Session housekeeping: periodic cleanup of expired server-side sessions. Expired…, Background task: periodically delete expired / revoked sessions. (+9 more)

### Community 62 - "Community 62"
Cohesion: 0.29
Nodes (19): _age(), _batch(), beat(), join(), leave(), _modules(), #40: the student module inventory. Modules seen on a gateway's mesh are listed…, _rows() (+11 more)

### Community 63 - "Community 63"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 64 - "Community 64"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 65 - "Community 65"
Cohesion: 0.28
Nodes (18): Poll, create_poll(), end_poll(), get_poll(), list_polls(), _poll_response(), poll_results(), AsyncSession (+10 more)

### Community 66 - "Community 66"
Cohesion: 0.15
Nodes (18): Two time slots overlap when neither fully precedes the other. Overnight / wrap-…, Two classes only clash if they run in the same semester/window. Priority:…, _same_academic_window(), _slots_conflict(), normalize_version(), as_ist(), Convert any aware/naive datetime to naive IST; naive input is treated as UTC., parametrize (+10 more)

### Community 67 - "Community 67"
Cohesion: 0.28
Nodes (18): _beat(), _device(), q(), _key(), #66: per-device keys. Devices register with the shared key and are issued their…, _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out() (+10 more)

### Community 68 - "Community 68"
Cohesion: 0.13
Nodes (12): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, #132: both backend clients classify a failure and log the hint, and the boot…, #129: both registrations append the caps object from device_caps.h., test_connection_failures_say_why(), test_every_backend_client_gets_the_tls_settings(), test_gateway_and_hub_report_their_capabilities(), test_version_comes_from_the_image() (+4 more)

### Community 69 - "Community 69"
Cohesion: 0.15
Nodes (10): importlib_util, stat, _backend(), #42: the documented install path: scripts, secrets, version, CI job., test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets() (+2 more)

### Community 70 - "Community 70"
Cohesion: 0.24
Nodes (16): _activity(), q(), _device(), q(), Gateway-facing device API (routers/device.py) + presence service…, _register(), test_firmware_check_and_applied_cycle(), test_heartbeat_updates_telemetry() (+8 more)

### Community 71 - "Community 71"
Cohesion: 0.15
Nodes (16): _me(), fixture, parametrize, At least one active super admin always remains (#116). The original failure: a…, The original lockout path: PUT with is_active=false on yourself (#116, #119)., Two super admins disabling each other at the same moment: one must fail., su(), test_concurrent_mutual_deactivation_leaves_one_super_admin() (+8 more)

### Community 72 - "Community 72"
Cohesion: 0.26
Nodes (15): msg_type_t, msg_to_json(), student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join() (+7 more)

### Community 73 - "Community 73"
Cohesion: 0.25
Nodes (16): answer(), batch(), count(), q(), fixture, parametrize, #6: /api/device/batch validates and de-duplicates mesh answers/votes., setup() (+8 more)

### Community 74 - "Community 74"
Cohesion: 0.25
Nodes (16): _advance(), _dep(), _deploy(), _prompt(), fixture, #43 end to end: a firmware release reaches three rooms through the staged…, Three rooms, each with a v2.1.0 gateway; a c6 2.2.0 image approved., Read this room's socket until the gateway's own OTA prompt. (+8 more)

### Community 75 - "Community 75"
Cohesion: 0.21
Nodes (15): _activity(), #16: admin firmware upload works and OTA prompts are audit-logged., test_bad_device_type_rejected(), test_firmware_upload_succeeds_and_is_logged(), test_s3_ota_push_prompts_gateway_and_logs(), link(), _class(), _gateway_of() (+7 more)

### Community 76 - "Community 76"
Cohesion: 0.15
Nodes (9): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat() (+1 more)

### Community 77 - "Community 77"
Cohesion: 0.23
Nodes (15): When each authoritative timetable source last synchronised (#126/#127). No row…, ScheduleSource, _at(), Busy, occupancy(), _parse_time(), AsyncSession, datetime (+7 more)

### Community 78 - "Community 78"
Cohesion: 0.17
Nodes (16): adopt_legacy_files(), artifact_file(), artifact_path(), AsyncSession, Path, UploadFile, Register valid <type>-<version>.bin files from the old store (once)., The site key if it signed the image, else its first signer, else "". (+8 more)

### Community 79 - "Community 79"
Cohesion: 0.15
Nodes (14): _publish_graph_visualization(), Sphinx configuration for the public imPress documentation site., Expose the generated graph beneath the hosted ``/graph/`` page., setup(), glob, find_qemu(), judge(), main() (+6 more)

### Community 80 - "Community 80"
Cohesion: 0.16
Nodes (10): json, main(), Fail clearly if committed Graphify output is incomplete, stale, or unsafe., source_commit(), subprocess, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards() (+2 more)

### Community 81 - "Community 81"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 82 - "Community 82"
Cohesion: 0.21
Nodes (14): _live(), next_window(), AsyncSession, datetime, Maintenance windows for classroom hubs and gateways (#128). A hub (S3) or…, The class whose room this device serves: a gateway's linked class, or the class…, (None, "") when the update may start now; otherwise (when to look again, why…, room_class() (+6 more)

### Community 83 - "Community 83"
Cohesion: 0.30
Nodes (14): _device(), q(), _push(), parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report(), test_applied_with_another_version_is_not_success(), test_applied_with_the_pushed_version_completes_the_update() (+6 more)

### Community 84 - "Community 84"
Cohesion: 0.30
Nodes (14): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+6 more)

### Community 85 - "Community 85"
Cohesion: 0.23
Nodes (14): cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput(), msg_t (+6 more)

### Community 86 - "Community 86"
Cohesion: 0.21
Nodes (12): mentions(), Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch(), #73: the student module counts down a timed question's time_limit_s and stops… (+4 more)

### Community 87 - "Community 87"
Cohesion: 0.20
Nodes (11): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+3 more)

### Community 88 - "Community 88"
Cohesion: 0.15
Nodes (12): Activity logging service — records all significant actions., _check(), problem(), Password policy for new and changed passwords (#153). Existing passwords keep…, Why `password` is not acceptable as a new password, or None., admin_import_students_csv(), import_users_csv(), UploadFile (+4 more)

### Community 89 - "Community 89"
Cohesion: 0.22
Nodes (13): parametrize, Password guessing is slowed; new passwords resist trivial guesses (#153)., test_another_username_is_not_affected(), test_counters_survive_a_restart(), test_existing_passwords_keep_working(), test_one_address_guessing_many_usernames_is_slowed(), test_password_equal_to_username_is_refused(), test_sixth_failure_waits_and_the_password_is_not_checked() (+5 more)

### Community 90 - "Community 90"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10, #119: only a super admin can grant/remove admin-level roles; roles are a…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 91 - "Community 91"
Cohesion: 0.27
Nodes (13): mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main(), simulate(), test_dedup_window_and_wrap(), test_id_ignores_hops_but_not_content() (+5 more)

### Community 92 - "Community 92"
Cohesion: 0.23
Nodes (11): append_coverage(), component_for(), enrich(), main(), node_id(), Path, Build imPress's deterministic Graphify graph and enrich non-code coverage.…, Latest commit that changed input, rather than a graph-only bot commit. (+3 more)

### Community 93 - "Community 93"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 94 - "Community 94"
Cohesion: 0.24
Nodes (10): main(), _lock_out(), Offline recovery of a locked-out installation (#120)., A database from before #116: no triggers, every super admin inactive., _restore(), _sql(), test_cli_exit_codes(), test_promotes_an_existing_account() (+2 more)

### Community 95 - "Community 95"
Cohesion: 0.22
Nodes (9): argparse, call(), env_value(), main(), HTTP smoke test of a running imPress backend (#42): the system audit's…, ssl, urllib_error, urllib_request (+1 more)

### Community 96 - "Community 96"
Cohesion: 0.33
Nodes (11): batch_add(), batch_flush(), batch_flush_needed(), cJSON, item_is_heartbeat(), process_spi_payload(), spi_to_http_task(), wifi_client_is_connected() (+3 more)

### Community 97 - "Community 97"
Cohesion: 0.24
Nodes (9): health(), datetime, Device health states (#39), computed from the latest heartbeat. Rules, in order…, (state, reasons) for one device., _dev(), parametrize, test_invalid_diagnostics_are_rejected(), test_precedence_offline_over_updating_over_error_over_degraded() (+1 more)

### Community 98 - "Community 98"
Cohesion: 0.20
Nodes (9): push_device_status(), push_poll_to_mesh(), push_quiz_to_mesh(), push_student_data(), Bridge service: connects ESP device data to WebSocket clients. This service…, Push student device data (heartbeats, answers, votes) to teacher dashboard., Push individual device status update., Push quiz question through WebSocket → C6 → SPI → S3 → mesh → students. (+1 more)

### Community 99 - "Community 99"
Cohesion: 0.31
Nodes (9): device(), set_pending(), go(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download() (+1 more)

### Community 100 - "Community 100"
Cohesion: 0.29
Nodes (8): _create(), ctx(), fixture, parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 101 - "Community 101"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 102 - "Community 102"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 103 - "Community 103"
Cohesion: 0.39
Nodes (6): _history(), Loading a user or a class list must not pull in the teaching history (#133).…, statements(), test_class_list_counts_without_loading_quizzes(), test_loading_a_user_is_one_statement(), load()

### Community 104 - "Community 104"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 105 - "Community 105"
Cohesion: 0.48
Nodes (6): _open_create_quiz(), #31: importing questions from CSV on the create-quiz page., test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz()

### Community 107 - "Community 107"
Cohesion: 0.50
Nodes (5): commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, test_commit_or_conflict_turns_a_unique_violation_into_409(), race()

### Community 109 - "Community 109"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

## Knowledge Gaps
- **51 isolated node(s):** `StaleRender`, `ASAN_OPTIONS`, `run.sh script`, `afl-prepare-linux.sh script`, `afl.sh script` (+46 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1066 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **128 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `Community 23` to `Community 0`, `Community 1`, `Community 2`, `Community 6`, `Community 10`, `Community 13`, `Community 15`, `Community 18`, `Community 19`, `Community 21`, `Community 22`, `Community 30`, `Community 32`, `Community 34`, `Community 38`, `Community 61`, `Community 62`, `Community 65`, `Community 66`, `Community 70`, `Community 74`, `Community 77`, `Community 89`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `User` connect `Community 0` to `Community 32`, `Community 65`, `Community 2`, `Community 34`, `Community 103`, `Community 71`, `Community 10`, `Community 42`, `Community 12`, `Community 15`, `Community 29`, `Community 21`, `Community 22`, `Community 54`, `Community 88`, `Community 61`, `Community 30`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `auth()` connect `Community 1` to `Community 16`, `Community 18`, `Community 19`, `Community 24`, `Community 29`, `Community 34`, `Community 38`, `Community 39`, `Community 46`, `Community 48`, `Community 50`, `Community 51`, `Community 53`, `Community 54`, `Community 56`, `Community 57`, `Community 59`, `Community 60`, `Community 61`, `Community 62`, `Community 67`, `Community 70`, `Community 71`, `Community 73`, `Community 74`, `Community 75`, `Community 78`, `Community 83`, `Community 89`, `Community 90`, `Community 94`, `Community 99`, `Community 100`, `Community 103`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 165 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 165 INFERRED edges - model-reasoned connections that need verification._
- **Are the 130 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 130 INFERRED edges - model-reasoned connections that need verification._
- **Are the 74 inferred relationships involving `EspDevice` (e.g. with `_by_mac()` and `caller_for_key()`) actually correct?**
  _`EspDevice` has 74 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `ASAN_OPTIONS`, `run.sh script` to the rest of the system?**
  _51 weakly-connected nodes found - possible documentation gaps or missing edges._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
