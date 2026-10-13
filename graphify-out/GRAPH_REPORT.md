# Graph Report - imPress  (2026-10-13)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3151 nodes · 8651 edges · 218 communities (96 shown, 122 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1330 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `157f5c38`
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
- Community 120
- Community 126
- Community 127
- Community 214
- Community 215
- Community 216
- Community 217

## God Nodes (most connected - your core abstractions)
1. `select()` - 158 edges
2. `User` - 141 edges
3. `login()` - 125 edges
4. `auth()` - 122 edges
5. `istnow()` - 100 edges
6. `EspDevice` - 96 edges
7. `ClassSession` - 86 edges
8. `_post()` - 76 edges
9. `make_user()` - 75 edges
10. `log_activity()` - 70 edges

## Surprising Connections (you probably didn't know these)
- `test_every_setting_is_documented()` --uses--> `Settings`  [INFERRED]
  tests/test_docs_consistency.py → backend/app/config.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_auth_sessions.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_create.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_firmware_upload.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_gateway_autolink.py → run_tests.py

## Import Cycles
- None detected.

## Communities (218 total, 122 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (100): log_activity(), AsyncSession, Write one activity log entry., hash_password(), User, admin_class_devices(), admin_delete_class(), admin_get_module() (+92 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (84): UserSession, _cleanup_once(), Delete sessions that are hard-expired, idle-expired, or revoked. Returns the…, auth(), login(), fixture, su(), parametrize (+76 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (67): adc_oneshot, crypto, esp_crt_bundle, esp_efuse, esp_heap_caps, esp_http_client, esp_mac, esp_netif (+59 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (63): platform, Popen, posix_only, CaseResult, discover(), fmt_secs(), _idf_command(), _idf_image_present() (+55 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (66): Revoke every session of a user (except `keep_id`), in the caller's transaction…, revoke_user_sessions(), verify_password(), activity_ping(), change_password(), login(), logout(), me() (+58 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (69): errno, esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client, esp_websocket_client_config_t (+61 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (66): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+58 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (58): config, nvs_handle_t, init_nvs_config(), nvs_save_class_id(), _read_str(), _store_dev_key(), ota_c6_boot_check(), remember_target() (+50 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (64): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+56 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (61): Any, ClassSession, admin_create_class(), admin_list_classes(), admin_set_class_faculty(), admin_update_class(), assign_teacher(), _class_to_response() (+53 more)

### Community 11 - "Community 11"
Cohesion: 0.07
Nodes (54): AsyncConnection, AsyncEngine, _add_columns(), add_device_keys(), add_diagnostics_columns(), add_firmware_signer(), add_quiz_question_started_at(), add_unique_constraints() (+46 more)

### Community 12 - "Community 12"
Cohesion: 0.07
Nodes (54): Base, commit_or_conflict(), AsyncSession, Async SQLAlchemy engine and session factory., SQLite ignores foreign keys unless asked, per connection., Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, _sqlite_pragmas(), Attendance (+46 more)

### Community 13 - "Community 13"
Cohesion: 0.09
Nodes (58): authorize(), DeviceCaller, new_device_key(), (raw key for the device, hash to store)., Who is calling: the shared key (device None) or one device's own key., ActivityLog, EspDevice, _broadcast_participation() (+50 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (52): make_class(), make_user(), Create a user through the admin API; returns (user_id, auth headers)., Create a class via /api/admin/classes; optionally activate it., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password() (+44 more)

### Community 15 - "Community 15"
Cohesion: 0.08
Nodes (49): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), make_image(), _artifact(), _hub(), _push(), #36: firmware version manager: approval, deprecation, retention, usage., _set() (+41 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (43): esp_log, esp_now, esp_random, esp_wifi, display_clear(), display_deinit(), display_flush(), display_init() (+35 more)

### Community 17 - "Community 17"
Cohesion: 0.08
Nodes (46): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts…, Length of the app image itself (segments, checksum, appended SHA-256), without… (+38 more)

### Community 18 - "Community 18"
Cohesion: 0.08
Nodes (46): advance(), answer_closed(), deadline(), finish(), AsyncSession, datetime, quiz_timer_loop(), Quiz timing (#73): advance `per_question` quizzes and end `total` quizzes when… (+38 more)

### Community 19 - "Community 19"
Cohesion: 0.07
Nodes (44): Activity logging service — records all significant actions., Course, create_course(), delete_course(), get_course(), list_courses(), AsyncSession, delete (+36 more)

### Community 20 - "Community 20"
Cohesion: 0.14
Nodes (48): cJSON_AddItemToArray(), cJSON_AddItemToObject(), cJSON_CreateObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc() (+40 more)

### Community 21 - "Community 21"
Cohesion: 0.10
Nodes (41): Quiz, Example file with every column. Public: it contains no data., create_quiz(), get_quiz(), import_question_csv(), list_quizzes(), next_question(), parse_question_csv() (+33 more)

### Community 22 - "Community 22"
Cohesion: 0.09
Nodes (41): BaseType_t, spi_slave_send(), SemaphoreHandle_t, xSemaphoreGive(), xSemaphoreGiveFromISR(), xSemaphoreTake(), msg_t, handle_c6_frame() (+33 more)

### Community 23 - "Community 23"
Cohesion: 0.12
Nodes (38): cJSON_Hooks, buffer_skip_whitespace(), cJSON_bool, cJSON_AddBoolToObject(), cJSON_Compare(), cJSON_CreateBool(), cJSON_InitHooks(), cJSON_Minify() (+30 more)

### Community 24 - "Community 24"
Cohesion: 0.09
Nodes (35): os, playwright_sync_api, tempfile, time, login(), Browser UI checks: a real backend on a temp database, driven by Playwright.…, _open(), #32: importing and exporting courses and sections on the Classrooms page. (+27 more)

### Community 25 - "Community 25"
Cohesion: 0.10
Nodes (39): Student, admin_import_students_csv(), import_users_csv(), UploadFile, Import students from CSV and enroll them into a specific class. Columns:…, Mass-import user accounts from CSV. Required columns (all compulsory):…, bulk_create_students(), _create_one() (+31 more)

### Community 26 - "Community 26"
Cohesion: 0.11
Nodes (37): DeploymentTarget, FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., active_target(), advance(), advance_all(), cancel() (+29 more)

### Community 27 - "Community 27"
Cohesion: 0.06
Nodes (18): Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, Smoke tests: the app boots on an empty DB and its basic contracts hold., test_seeded_super_admin_can_log_in(), env(), fixture, #21: co-faculty can run quizzes/polls for their class; outsiders still can't., _teacher(), env() (+10 more)

### Community 28 - "Community 28"
Cohesion: 0.10
Nodes (31): client(), _drain_background_tasks(), fixture, TestClient on an empty database (the app seeds the super admin)., _reset_db(), _beat(), _device(), q() (+23 more)

### Community 29 - "Community 29"
Cohesion: 0.10
Nodes (10): cjson, esp_err, esp_event, esp_idf_version, esp_transport_ws, protocol, socket, stdbool (+2 more)

### Community 30 - "Community 30"
Cohesion: 0.08
Nodes (21): answer(), Gateway, join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., _marker() (+13 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (33): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get() (+25 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (30): spi_slave_transaction_t, queue_slot(), ready_update(), spi_post_trans_cb(), spi_slave_init(), spi_slave_read(), esp_err_t, spi_slave_transaction_t (+22 more)

### Community 33 - "Community 33"
Cohesion: 0.13
Nodes (33): batch_flush(), add_item_to_object(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddFalseToObject(), cJSON_AddItemToObjectCS(), cJSON_AddNullToObject(), cJSON_AddNumberToObject() (+25 more)

### Community 34 - "Community 34"
Cohesion: 0.09
Nodes (28): create_access_token(), Legacy JWT creation (kept for device registration / backward compat)., _parse_time(), Convert "HH:MM" → minutes since midnight. Returns None if malformed., Two time slots overlap when neither fully precedes the other. Overnight / wrap-…, _slots_conflict(), normalize_version(), as_ist() (+20 more)

### Community 35 - "Community 35"
Cohesion: 0.21
Nodes (31): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+23 more)

### Community 36 - "Community 36"
Cohesion: 0.15
Nodes (27): msg_t, spi_slot_fifo_t, crc16_ccitt(), msg_decode(), msg_verify_crc(), spi_record_read(), spi_record_write(), spi_slot_decode() (+19 more)

### Community 37 - "Community 37"
Cohesion: 0.10
Nodes (27): _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), health(), lifespan(), get (+19 more)

### Community 38 - "Community 38"
Cohesion: 0.16
Nodes (27): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+19 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (29): add_item_to_array(), cJSON, case_insensitive_strcmp(), cJSON_AddItemReferenceToArray(), cJSON_AddItemReferenceToObject(), cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive() (+21 more)

### Community 40 - "Community 40"
Cohesion: 0.15
Nodes (19): msg_type_t, msg_to_json(), student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join() (+11 more)

### Community 42 - "Community 42"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (22): esp_app_desc, esp_bit_defs, event_groups, cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), esp_err_t, esp_event_base_t (+14 more)

### Community 44 - "Community 44"
Cohesion: 0.10
Nodes (24): make_student(), fixture, A class with a quiz, a poll, an enrolled student who answered and voted over…, world(), link_module(), test_attendance_paths(), count(), fixture (+16 more)

### Community 45 - "Community 45"
Cohesion: 0.19
Nodes (24): _count(), q(), _csv(), _post(), parametrize, #32: import courses and their sections (class sessions) from CSV., test_admin_only(), test_any_invalid_row_means_nothing_is_imported() (+16 more)

### Community 46 - "Community 46"
Cohesion: 0.11
Nodes (24): create_session(), generate_session_token(), get_current_user(), get_current_user_light(), _load_session_by_hash(), AsyncSession, Request, JWT + server-side session authentication helpers. (+16 more)

### Community 47 - "Community 47"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 48 - "Community 48"
Cohesion: 0.12
Nodes (16): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+8 more)

### Community 49 - "Community 49"
Cohesion: 0.13
Nodes (18): asyncio, _device_to_dict(), presence_snapshot(), push_presence(), datetime, ESP device presence monitoring (online/offline logs). Requirement: the backend…, Full live snapshot of one class's devices: root gateway + relayed tree., Build a presence snapshot and broadcast to teacher connections. (+10 more)

### Community 50 - "Community 50"
Cohesion: 0.16
Nodes (22): mark_offline(), Mark stale devices offline. Returns number of transitions logged., Mark a device offline and log the transition., _sweep_once(), _activity(), q(), _device(), q() (+14 more)

### Community 51 - "Community 51"
Cohesion: 0.22
Nodes (22): Require teacher, admin, or super_admin role., require_teacher_or_admin(), Poll, create_poll(), end_poll(), get_poll(), list_polls(), _poll_response() (+14 more)

### Community 52 - "Community 52"
Cohesion: 0.23
Nodes (22): wire(), _age(), q(), _batch(), beat(), join(), leave(), _modules() (+14 more)

### Community 53 - "Community 53"
Cohesion: 0.17
Nodes (20): functions(), mentions(), {name: body_text} for every top-level function definition in a C file., #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch() (+12 more)

### Community 54 - "Community 54"
Cohesion: 0.14
Nodes (20): api_key_ok(), check_secure(), insecure_settings(), Application configuration loaded from environment variables., Names of settings still at their public, repo-published defaults., Refuse to run with published secrets unless explicitly in DEBUG mode., Constant-time device API key comparison., Settings (+12 more)

### Community 55 - "Community 55"
Cohesion: 0.12
Nodes (20): One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent…, go(), link(), age(), push(), stale(), later(), go() (+12 more)

### Community 56 - "Community 56"
Cohesion: 0.13
Nodes (16): argparse, pathlib, init_env(), Path, Create or complete backend/.env from backend/.env.example (#42). The public…, Returns the names of the secrets it generated., call(), env_value() (+8 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 58 - "Community 58"
Cohesion: 0.15
Nodes (16): _publish_graph_visualization(), Sphinx configuration for the public imPress documentation site., Expose the generated graph beneath the hosted ``/graph/`` page., setup(), append_coverage(), component_for(), enrich(), main() (+8 more)

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 60 - "Community 60"
Cohesion: 0.17
Nodes (15): init_db(), Create missing tables and apply pending migrations (stops on failure)., main(), Server-side maintenance commands, run on the host that has the database (#120).…, Returns the new password. Raises LookupError for an unknown username., restore_super_admin(), _lock_out(), Offline recovery of a locked-out installation (#120). (+7 more)

### Community 61 - "Community 61"
Cohesion: 0.22
Nodes (18): _act(), cancel_deployment(), create_deployment(), deployment_dict(), DeploymentCreate, _get(), get_deployment(), list_deployments() (+10 more)

### Community 62 - "Community 62"
Cohesion: 0.20
Nodes (17): Digest of the public key every image must be signed with…, site_key_digest(), adopt_legacy_files(), artifact_file(), artifact_path(), AsyncSession, Path, UploadFile (+9 more)

### Community 63 - "Community 63"
Cohesion: 0.15
Nodes (16): _me(), fixture, parametrize, At least one active super admin always remains (#116). The original failure: a…, The original lockout path: PUT with is_active=false on yourself (#116, #119)., Two super admins disabling each other at the same moment: one must fail., su(), test_concurrent_mutual_deactivation_leaves_one_super_admin() (+8 more)

### Community 64 - "Community 64"
Cohesion: 0.25
Nodes (16): answer(), batch(), count(), q(), fixture, parametrize, #6: /api/device/batch validates and de-duplicates mesh answers/votes., setup() (+8 more)

### Community 65 - "Community 65"
Cohesion: 0.15
Nodes (9): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat() (+1 more)

### Community 66 - "Community 66"
Cohesion: 0.21
Nodes (15): cJSON_GetArraySize(), cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput() (+7 more)

### Community 67 - "Community 67"
Cohesion: 0.16
Nodes (10): json, main(), Fail clearly if committed Graphify output is incomplete, stale, or unsafe., source_commit(), subprocess, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards() (+2 more)

### Community 68 - "Community 68"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 69 - "Community 69"
Cohesion: 0.15
Nodes (7): ConnectionManager, WebSocket, Send a JSON message to ALL connections in a class room (teachers + devices)., Send a JSON message only to connections matching the given role., Alias for broadcast_to_class., Manages WebSocket connections grouped by class ID. Teachers connect to manage…, Close every socket of a user whose access was revoked (#118).

### Community 70 - "Community 70"
Cohesion: 0.30
Nodes (14): _advance(), _dep(), _deploy(), _prompt(), fixture, #43 end to end: a firmware release reaches three rooms through the staged…, Three rooms, each with a v2.1.0 gateway; a c6 2.2.0 image approved., Read this room's socket until the gateway's own OTA prompt. (+6 more)

### Community 71 - "Community 71"
Cohesion: 0.30
Nodes (14): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+6 more)

### Community 72 - "Community 72"
Cohesion: 0.15
Nodes (8): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), #13: S3 OTA — rollback protection and no reboot when nothing is installed., test_detach_unregisters_reconnect_handler_before_disconnecting(), test_new_image_marked_valid_only_after_mesh_and_spi_init(), test_only_a_successful_install_reboots()

### Community 73 - "Community 73"
Cohesion: 0.13
Nodes (11): Api, browser(), _free_port(), page(), fixture, A page that fails the test on any uncaught JS error; screenshot at the end., Tiny JSON client for setting up data the test then checks in the UI., multipart/form-data POST of one file field named 'file'. (+3 more)

### Community 74 - "Community 74"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10, #119: only a super admin can grant/remove admin-level roles; roles are a…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 75 - "Community 75"
Cohesion: 0.27
Nodes (13): mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main(), simulate(), test_dedup_window_and_wrap(), test_id_ignores_hops_but_not_content() (+5 more)

### Community 76 - "Community 76"
Cohesion: 0.16
Nodes (10): #29: guards for the S3 <-> C6 link as ported from v3…, _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_student_count_comes_from_join_and_leave_only(), test_c6_validates_received_slots(), test_master_drops_a_payload_only_after_a_successful_transfer(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+2 more)

### Community 77 - "Community 77"
Cohesion: 0.22
Nodes (10): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+2 more)

### Community 78 - "Community 78"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 79 - "Community 79"
Cohesion: 0.21
Nodes (12): fixture, parametrize, Separate account operations and server-provided allowed_actions (#119)., Whatever allowed_actions leaves out, the route refuses (UI is not the guard)., _row(), su(), test_allowed_actions_for_a_super_admin(), test_allowed_actions_for_an_admin() (+4 more)

### Community 80 - "Community 80"
Cohesion: 0.24
Nodes (10): _sha256_hex(), Older versions stored the raw bearer token in user_sessions.session_token. Any…, _scrub_raw_session_tokens(), _all_session_values(), skipif, #12: raw bearer tokens are never persisted; legacy raw rows are revoked., test_legacy_raw_token_rows_revoked_and_scrubbed(), insert_legacy() (+2 more)

### Community 81 - "Community 81"
Cohesion: 0.26
Nodes (10): health(), datetime, Device health states (#39), computed from the latest heartbeat. Rules, in order…, (state, reasons) for one device., _dev(), parametrize, #39: device health states from the latest heartbeat diagnostics., test_invalid_diagnostics_are_rejected() (+2 more)

### Community 82 - "Community 82"
Cohesion: 0.17
Nodes (11): push_device_status(), push_poll_to_mesh(), push_quiz_to_mesh(), push_student_data(), Bridge service: connects ESP device data to WebSocket clients. This service…, Push student device data (heartbeats, answers, votes) to teacher dashboard., Push individual device status update., Send a command to C6 devices connected via WebSocket. (+3 more)

### Community 83 - "Community 83"
Cohesion: 0.20
Nodes (5): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #66: the signed-app profile and the scripts that build with it., re

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (9): importlib_util, stat, _backend(), #42: the documented install path: scripts, secrets, version, CI job., test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets() (+1 more)

### Community 85 - "Community 85"
Cohesion: 0.20
Nodes (10): class_websocket(), _device_key_ok(), websocket, The shared key (unless IMPRESS_DEVICE_KEYS_REQUIRED) or an active-able per-…, Validate a login session token for WebSocket auth. Returns the User or None.…, WebSocket endpoint for real-time class communication. Connect with:…, _ws_user_from_token(), db() (+2 more)

### Community 86 - "Community 86"
Cohesion: 0.24
Nodes (8): cls(), fixture, parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student…, test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons()

### Community 87 - "Community 87"
Cohesion: 0.31
Nodes (9): device(), set_pending(), go(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download() (+1 more)

### Community 88 - "Community 88"
Cohesion: 0.29
Nodes (8): _create(), ctx(), fixture, parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 89 - "Community 89"
Cohesion: 0.27
Nodes (8): Security review (#16 of the v2.1 brief): every route refuses a caller without…, 401/403, or 422 for the missing device-key header (a required `X-API-Key` is…, _refused(), _routes(), test_device_routes_reject_a_wrong_key(), test_every_route_needs_credentials(), fastapi_routing, importlib

### Community 90 - "Community 90"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 91 - "Community 91"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 92 - "Community 92"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 93 - "Community 93"
Cohesion: 0.48
Nodes (6): _open_create_quiz(), #31: importing questions from CSV on the create-quiz page., test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz()

### Community 94 - "Community 94"
Cohesion: 0.33
Nodes (6): observe(), AsyncSession, Record a join / leave / heartbeat relayed by `gateway`. Returns the row, or…, Mark silent modules disconnected; returns their gateways' ids., sweep(), _uid()

### Community 95 - "Community 95"
Cohesion: 0.47
Nodes (5): _next_device_frame(), _project(), Contract test: frames the C6 gateway receives on its device WebSocket (#3). The…, The single frame an action broadcasts; it must carry a firmware event. Reads…, test_device_socket_receives_firmware_contract()

### Community 97 - "Community 97"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

## Knowledge Gaps
- **49 isolated node(s):** `StaleRender`, `afl-prepare-linux.sh script`, `afl.sh script`, `ossfuzz.sh script`, `start_server.sh script` (+44 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 958 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **122 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `Community 13` to `Community 0`, `Community 1`, `Community 5`, `Community 11`, `Community 12`, `Community 18`, `Community 21`, `Community 26`, `Community 30`, `Community 31`, `Community 34`, `Community 35`, `Community 37`, `Community 46`, `Community 49`, `Community 50`, `Community 51`, `Community 52`, `Community 54`, `Community 55`, `Community 70`, `Community 80`, `Community 94`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `select()` connect `Community 10` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 12`, `Community 13`, `Community 15`, `Community 18`, `Community 19`, `Community 21`, `Community 25`, `Community 26`, `Community 28`, `Community 30`, `Community 31`, `Community 35`, `Community 37`, `Community 38`, `Community 44`, `Community 45`, `Community 46`, `Community 47`, `Community 49`, `Community 50`, `Community 51`, `Community 52`, `Community 54`, `Community 60`, `Community 61`, `Community 62`, `Community 64`, `Community 80`, `Community 94`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `EspDevice` connect `Community 13` to `Community 0`, `Community 1`, `Community 10`, `Community 12`, `Community 15`, `Community 21`, `Community 26`, `Community 28`, `Community 30`, `Community 31`, `Community 35`, `Community 44`, `Community 49`, `Community 50`, `Community 51`, `Community 52`, `Community 54`, `Community 81`, `Community 87`, `Community 94`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 154 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 154 INFERRED edges - model-reasoned connections that need verification._
- **Are the 121 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 121 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `afl-prepare-linux.sh script`, `afl.sh script` to the rest of the system?**
  _49 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.04989322461657931 - nodes in this community are weakly interconnected._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
