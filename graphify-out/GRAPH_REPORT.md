# Graph Report - imPress  (2026-10-13)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3447 nodes · 9537 edges · 229 communities (102 shown, 127 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1408 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `109b7447`
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
- Community 127
- Community 133
- Community 134
- Community 225
- Community 226
- Community 227
- Community 228

## God Nodes (most connected - your core abstractions)
1. `select()` - 169 edges
2. `User` - 154 edges
3. `login()` - 151 edges
4. `auth()` - 149 edges
5. `istnow()` - 107 edges
6. `EspDevice` - 106 edges
7. `ClassSession` - 96 edges
8. `make_user()` - 93 edges
9. `_post()` - 77 edges
10. `log_activity()` - 72 edges

## Surprising Connections (you probably didn't know these)
- `test_every_setting_is_documented()` --uses--> `Settings`  [INFERRED]
  tests/test_docs_consistency.py → backend/app/config.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_db_integrity.py → run_tests.py
- `dev()` --calls--> `select()`  [INFERRED]
  backend/tests/test_db_integrity.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_device_api.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_device_batch_dedup.py → run_tests.py

## Import Cycles
- None detected.

## Communities (229 total, 127 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (121): Any, log_activity(), AsyncSession, Write one activity log entry., User, Enrol or remove students, list a class roster: the primary teacher or an…, roster_access(), admin_class_devices() (+113 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (98): api_key_ok(), Constant-time device API key comparison., authorize(), _by_mac(), caller_for_key(), denial(), device_caller(), DeviceCaller (+90 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (89): asyncio, create_access_token(), create_session(), generate_session_token(), get_current_user(), get_current_user_light(), hash_password(), _load_session_by_hash() (+81 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (80): DeploymentTarget, FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., _act(), cancel_deployment(), create_deployment(), deployment_dict() (+72 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (77): _cleanup_once(), Delete sessions that are hard-expired, idle-expired, or revoked. Returns the…, auth(), login(), fixture, su(), parametrize, Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py… (+69 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (34): assert, backend_fail_t, cjson, errno, esp_efuse, esp_err, esp_event, esp_idf_version (+26 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (64): platform, Popen, posix_only, CaseResult, discover(), fmt_secs(), _idf_command(), _idf_image_present() (+56 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (69): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+61 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (67): ActivityLogResponse, AdminUserCreate, BulkStudentRegister, ClassAssignTeacher, ClassCreate, ClassDevicesResponse, ClassFacultyUpdate, ClassImportRow (+59 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (59): make_class(), make_user(), Create a user through the admin API; returns (user_id, auth headers)., Create a class via /api/admin/classes; optionally activate it., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password() (+51 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (59): LoginThrottle, Failed password attempts per key: user:<name>, ip:<address>, change:<user id>., advance(), answer_closed(), deadline(), finish(), AsyncSession, datetime (+51 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (58): config, nvs_handle_t, init_nvs_config(), nvs_save_class_id(), _read_str(), _store_dev_key(), ota_c6_boot_check(), remember_target() (+50 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (64): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+56 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (63): esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client_config_t, esp_websocket_client_handle_t, esp_websocket_error_type_t (+55 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (57): commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, Quiz, Example file with every column. Public: it contains no data., create_quiz(), get_quiz(), import_question_csv() (+49 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (55): ClassSession, account_refusal(), allowed(), can_grant(), class_access(), class_owner_or_admin(), forbidden(), HTTPException (+47 more)

### Community 17 - "Community 17"
Cohesion: 0.06
Nodes (46): adc_oneshot, crypto, esp_crt_bundle, esp_heap_caps, esp_http_client, esp_netif, esp_ota_handle_t, esp_ota_ops (+38 more)

### Community 18 - "Community 18"
Cohesion: 0.06
Nodes (36): answer(), Gateway, join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent… (+28 more)

### Community 19 - "Community 19"
Cohesion: 0.07
Nodes (48): esp_now, esp_random, esp_wifi, xSemaphoreGive(), xSemaphoreTake(), msg_t, handle_c6_frame(), heartbeat_task() (+40 more)

### Community 20 - "Community 20"
Cohesion: 0.08
Nodes (49): Student, admin_import_students_csv(), import_users_csv(), UploadFile, Import students from CSV and enroll them into a specific class. Columns:…, Mass-import user accounts from CSV. Required columns (all compulsory):…, bulk_create_students(), _create_one() (+41 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (48): cJSON_AddItemToArray(), cJSON_AddItemToObject(), cJSON_CreateObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc() (+40 more)

### Community 22 - "Community 22"
Cohesion: 0.07
Nodes (39): playwright_sync_api, login(), _open(), #32: importing and exporting courses and sections on the Classrooms page., test_invalid_rows_block_the_import(), test_valid_file_creates_courses_and_sections(), _open_create_quiz(), #31: importing questions from CSV on the create-quiz page. (+31 more)

### Community 23 - "Community 23"
Cohesion: 0.09
Nodes (43): Base, Attendance, ClassOccurrenceException, PollVote, QuizAnswer, QuizQuestion, SQLAlchemy ORM models for imPress., One dated change to a class's weekly timetable (meeting_schedule). cancelled:… (+35 more)

### Community 24 - "Community 24"
Cohesion: 0.06
Nodes (33): _parse_time(), Convert "HH:MM" → minutes since midnight. Returns None if malformed., Two time slots overlap when neither fully precedes the other. Overnight / wrap-…, Two classes only clash if they run in the same semester/window. Priority:…, _same_academic_window(), _slots_conflict(), normalize_version(), as_ist() (+25 more)

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (42): class_id_for_device(), Mark stale devices offline. Returns number of transitions logged., Walk gateway_id chain up to the class gateway; return ClassSession.id or None., _sweep_once(), _activity(), q(), _device(), q() (+34 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (38): cJSON_Hooks, buffer_skip_whitespace(), cJSON_bool, cJSON_AddBoolToObject(), cJSON_Compare(), cJSON_CreateBool(), cJSON_InitHooks(), cJSON_Minify() (+30 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (38): Activity logging service — records all significant actions., Course, create_course(), delete_course(), get_course(), list_courses(), AsyncSession, delete (+30 more)

### Community 28 - "Community 28"
Cohesion: 0.10
Nodes (34): BaseType_t, esp_app_desc, spi_slave_transaction_t, queue_slot(), ready_update(), spi_post_trans_cb(), spi_slave_init(), spi_slave_read() (+26 more)

### Community 29 - "Community 29"
Cohesion: 0.10
Nodes (33): _der(), key_digest(), load_public_key(), _mgf1(), pss_verify(), ValueError, Signed firmware images (#66): ESP-IDF Secure Boot V2 RSA-3072 signatures,…, () if nothing follows the image (unsigned). Otherwise check the padding and… (+25 more)

### Community 30 - "Community 30"
Cohesion: 0.12
Nodes (32): app_main(), batch_add(), batch_flush_needed(), batch_init(), cJSON, msg_type_t, heartbeat_task(), item_is_heartbeat() (+24 more)

### Community 31 - "Community 31"
Cohesion: 0.12
Nodes (33): approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get(), _latest_approved(), list_firmware() (+25 more)

### Community 32 - "Community 32"
Cohesion: 0.14
Nodes (31): next_window(), AsyncSession, datetime, The class whose room this device serves: a gateway's linked class, or the class…, (None, "") when the update may start now; otherwise (when to look again, why…, room_class(), _advance(), _artifact() (+23 more)

### Community 33 - "Community 33"
Cohesion: 0.11
Nodes (28): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts…, Length of the app image itself (segments, checksum, appended SHA-256), without… (+20 more)

### Community 34 - "Community 34"
Cohesion: 0.11
Nodes (29): make_image(), _count(), q(), parametrize, #35: uploaded firmware is validated as a real imPress image and registered…, Against genuine ESP-IDF output when a local build exists (the synthetic images…, A scripts/build_signed.sh build (#66), when one exists locally., test_a_c6_image_is_never_pushed_to_an_s3() (+21 more)

### Community 35 - "Community 35"
Cohesion: 0.13
Nodes (33): batch_flush(), add_item_to_object(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddFalseToObject(), cJSON_AddItemToObjectCS(), cJSON_AddNullToObject(), cJSON_AddNumberToObject() (+25 more)

### Community 36 - "Community 36"
Cohesion: 0.07
Nodes (18): env(), fixture, #21: co-faculty can run quizzes/polls for their class; outsiders still can't., _teacher(), accounts(), _create(), fixture, parametrize (+10 more)

### Community 37 - "Community 37"
Cohesion: 0.21
Nodes (31): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+23 more)

### Community 38 - "Community 38"
Cohesion: 0.09
Nodes (24): argparse, glob, find_qemu(), judge(), main(), Boot a firmware image in Espressif's QEMU and judge the serial log (#154).…, (passed, reason) for a captured log., Check a firmware image the way the backend will at upload (#35, #66), before… (+16 more)

### Community 39 - "Community 39"
Cohesion: 0.08
Nodes (21): Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, Smoke tests: the app boots on an empty DB and its basic contracts hold., test_seeded_super_admin_can_log_in(), _next_device_frame(), _project(), Contract test: frames the C6 gateway receives on its device WebSocket (#3). The…, The single frame an action broadcasts; it must carry a firmware event. Reads…, test_device_socket_receives_firmware_contract() (+13 more)

### Community 40 - "Community 40"
Cohesion: 0.15
Nodes (28): spi_master_poll(), msg_t, spi_slot_fifo_t, crc16_ccitt(), json_get_string(), msg_decode(), msg_verify_crc(), spi_record_read() (+20 more)

### Community 41 - "Community 41"
Cohesion: 0.13
Nodes (28): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, adopt_legacy_files(), artifact_file(), artifact_path(), AsyncSession, Path, UploadFile (+20 more)

### Community 42 - "Community 42"
Cohesion: 0.16
Nodes (27): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+19 more)

### Community 43 - "Community 43"
Cohesion: 0.12
Nodes (29): add_item_to_array(), cJSON, case_insensitive_strcmp(), cJSON_AddItemReferenceToArray(), cJSON_AddItemReferenceToObject(), cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive() (+21 more)

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (27): AsyncConnection, _add_columns(), add_deployment_deferral(), add_device_keys(), add_diagnostics_columns(), add_firmware_qualification(), add_firmware_signer(), add_quiz_question_started_at() (+19 more)

### Community 45 - "Community 45"
Cohesion: 0.13
Nodes (23): esp_bit_defs, event_groups, cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), esp_err_t, esp_event_base_t, _download_and_apply() (+15 more)

### Community 47 - "Community 47"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 48 - "Community 48"
Cohesion: 0.10
Nodes (22): _calls(), The authorization policy is the one place that decides access (#122)., A staff route without a policy permission is a new hole; device routes…, Role checks scattered across routers drifted before (#19-#21, #116, #121)., docs/design/authorization.md shows GRANTS; it must not drift., test_every_route_is_governed_by_the_policy_or_listed(), test_no_role_comparisons_outside_the_policy(), test_published_permission_matrix_matches_the_code() (+14 more)

### Community 49 - "Community 49"
Cohesion: 0.18
Nodes (26): display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown(), display_show_provision_state(), display_show_question(), display_show_result() (+18 more)

### Community 50 - "Community 50"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (15): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+7 more)

### Community 52 - "Community 52"
Cohesion: 0.12
Nodes (21): make_student(), test_attendance_paths(), live(), fixture, fixture, Smoke steps 1-5: a class whose gateway registered with its room code., setup(), _csv() (+13 more)

### Community 53 - "Community 53"
Cohesion: 0.19
Nodes (20): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), _artifact(), _hub(), _push(), #36: firmware version manager: approval, deprecation, retention, usage., _set(), test_admin_only() (+12 more)

### Community 54 - "Community 54"
Cohesion: 0.17
Nodes (20): functions(), mentions(), {name: body_text} for every top-level function definition in a C file., #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch() (+12 more)

### Community 55 - "Community 55"
Cohesion: 0.17
Nodes (18): _add(), _busy(), phy(), fixture, parametrize, Dated timetable changes and room occupancy (#126). 2026-10-12 is a Monday,…, su(), test_a_cancelled_day_frees_every_slot() (+10 more)

### Community 56 - "Community 56"
Cohesion: 0.15
Nodes (19): _count(), q(), _fk_violations(), q(), _insert_twice(), go(), fixture, #41: the database enforces its own integrity (foreign keys, uniqueness), and… (+11 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 58 - "Community 58"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (15): init_db(), Create missing tables and apply pending migrations (stops on failure)., main(), Server-side maintenance commands, run on the host that has the database (#120).…, Returns the new password. Raises LookupError for an unknown username., restore_super_admin(), _lock_out(), Offline recovery of a locked-out installation (#120). (+7 more)

### Community 60 - "Community 60"
Cohesion: 0.29
Nodes (18): Poll, create_poll(), end_poll(), get_poll(), list_polls(), _poll_response(), poll_results(), AsyncSession (+10 more)

### Community 61 - "Community 61"
Cohesion: 0.28
Nodes (18): _beat(), _device(), q(), _key(), #66: per-device keys. Devices register with the shared key and are issued their…, _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out() (+10 more)

### Community 62 - "Community 62"
Cohesion: 0.25
Nodes (15): _all_versions(), _backups(), _indexes(), _legacy_db(), _migrate(), _model_unique_indexes(), _q(), #41: versioned migrations adopt old databases safely and atomically. (+7 more)

### Community 63 - "Community 63"
Cohesion: 0.21
Nodes (16): _routes(), _artifact(), _deploy(), _download(), fixture, TrustedInstaller (#123): firmware reaches a device only after its own checks,…, The production defaults: no unsigned images, no self-approval., _register() (+8 more)

### Community 64 - "Community 64"
Cohesion: 0.15
Nodes (16): _me(), fixture, parametrize, At least one active super admin always remains (#116). The original failure: a…, The original lockout path: PUT with is_active=false on yourself (#116, #119)., Two super admins disabling each other at the same moment: one must fail., su(), test_concurrent_mutual_deactivation_leaves_one_super_admin() (+8 more)

### Community 65 - "Community 65"
Cohesion: 0.15
Nodes (11): is_loopback(), needs_https(), Should this request be refused for arriving without TLS?, _https(), fixture, HTTPS for staff traffic and browser security headers (#152)., uvicorn turns X-Forwarded-Proto from a trusted proxy into the scheme; the test…, strict() (+3 more)

### Community 66 - "Community 66"
Cohesion: 0.25
Nodes (16): answer(), batch(), count(), q(), fixture, parametrize, #6: /api/device/batch validates and de-duplicates mesh answers/votes., setup() (+8 more)

### Community 67 - "Community 67"
Cohesion: 0.14
Nodes (10): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, #132: both backend clients classify a failure and log the hint, and the boot…, test_connection_failures_say_why(), test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), #13: S3 OTA — rollback protection and no reboot when nothing is installed., test_detach_unregisters_reconnect_handler_before_disconnecting() (+2 more)

### Community 68 - "Community 68"
Cohesion: 0.15
Nodes (9): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat() (+1 more)

### Community 69 - "Community 69"
Cohesion: 0.18
Nodes (15): clock(), fixture, parametrize, Password guessing is slowed; new passwords resist trivial guesses (#153)., test_another_username_is_not_affected(), test_counters_survive_a_restart(), test_existing_passwords_keep_working(), test_one_address_guessing_many_usernames_is_slowed() (+7 more)

### Community 70 - "Community 70"
Cohesion: 0.15
Nodes (10): _publish_graph_visualization(), Sphinx configuration for the public imPress documentation site., Expose the generated graph beneath the hosted ``/graph/`` page., setup(), shutil, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards() (+2 more)

### Community 71 - "Community 71"
Cohesion: 0.21
Nodes (15): cJSON_GetArraySize(), cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput() (+7 more)

### Community 72 - "Community 72"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 73 - "Community 73"
Cohesion: 0.30
Nodes (14): _device(), q(), _push(), parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report(), test_applied_with_another_version_is_not_success(), test_applied_with_the_pushed_version_completes_the_update() (+6 more)

### Community 74 - "Community 74"
Cohesion: 0.30
Nodes (14): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+6 more)

### Community 75 - "Community 75"
Cohesion: 0.16
Nodes (12): json, call(), env_value(), main(), HTTP smoke test of a running imPress backend (#42): the system audit's…, main(), Fail clearly if committed Graphify output is incomplete, stale, or unsafe., source_commit() (+4 more)

### Community 76 - "Community 76"
Cohesion: 0.16
Nodes (14): _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), get, Request, Touch last_activity_at for live user sessions on each API request. Best-effort… (+6 more)

### Community 77 - "Community 77"
Cohesion: 0.27
Nodes (13): mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main(), simulate(), test_dedup_window_and_wrap(), test_id_ignores_hops_but_not_content() (+5 more)

### Community 78 - "Community 78"
Cohesion: 0.16
Nodes (10): #29: guards for the S3 <-> C6 link as ported from v3…, _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_student_count_comes_from_join_and_leave_only(), test_c6_validates_received_slots(), test_master_drops_a_payload_only_after_a_successful_transfer(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+2 more)

### Community 79 - "Community 79"
Cohesion: 0.23
Nodes (11): append_coverage(), component_for(), enrich(), main(), node_id(), Path, Build imPress's deterministic Graphify graph and enrich non-code coverage.…, Latest commit that changed input, rather than a graph-only bot commit. (+3 more)

### Community 80 - "Community 80"
Cohesion: 0.22
Nodes (10): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+2 more)

### Community 81 - "Community 81"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 82 - "Community 82"
Cohesion: 0.26
Nodes (11): _sha256_hex(), Older versions stored the raw bearer token in user_sessions.session_token. Any…, _scrub_raw_session_tokens(), UserSession, _all_session_values(), skipif, #12: raw bearer tokens are never persisted; legacy raw rows are revoked., test_legacy_raw_token_rows_revoked_and_scrubbed() (+3 more)

### Community 83 - "Community 83"
Cohesion: 0.19
Nodes (8): _reset_db(), _fresh_settings(), #11: no working public credentials or debug leaks by default., test_cors_only_configured_origins(), test_debug_and_sql_echo_off_by_default(), test_first_admin_password_is_random_not_admin123(), test_refuses_default_secrets_outside_debug(), fastapi_testclient

### Community 84 - "Community 84"
Cohesion: 0.21
Nodes (12): fixture, parametrize, Separate account operations and server-provided allowed_actions (#119)., Whatever allowed_actions leaves out, the route refuses (UI is not the guard)., _row(), su(), test_allowed_actions_for_a_super_admin(), test_allowed_actions_for_an_admin() (+4 more)

### Community 85 - "Community 85"
Cohesion: 0.20
Nodes (5): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #66: the signed-app profile and the scripts that build with it., re

### Community 86 - "Community 86"
Cohesion: 0.24
Nodes (8): cls(), fixture, parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student…, test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons()

### Community 87 - "Community 87"
Cohesion: 0.33
Nodes (8): stat, _backend(), #42: the documented install path: scripts, secrets, version, CI job., test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets(), _values()

### Community 88 - "Community 88"
Cohesion: 0.29
Nodes (10): AsyncEngine, health(), _applied(), backup(), _db_file(), migrate(), Path, Copy the SQLite file before migrating it. Returns the backup path. (+2 more)

### Community 89 - "Community 89"
Cohesion: 0.42
Nodes (9): _class(), _gateway_of(), q(), #17: registration must not steal a class's gateway link., _register(), test_explicit_classroom_code_still_assigns(), test_gateway_keeps_its_class_on_reregister(), test_non_gateway_registration_keeps_class_gateway() (+1 more)

### Community 90 - "Community 90"
Cohesion: 0.31
Nodes (9): device(), set_pending(), go(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download() (+1 more)

### Community 91 - "Community 91"
Cohesion: 0.29
Nodes (8): _create(), ctx(), fixture, parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 92 - "Community 92"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 93 - "Community 93"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 94 - "Community 94"
Cohesion: 0.36
Nodes (7): _dev(), parametrize, #39: device health states from the latest heartbeat diagnostics., test_heartbeat_stores_diagnostics_and_old_firmware_still_works(), test_invalid_diagnostics_are_rejected(), test_precedence_offline_over_updating_over_error_over_degraded(), test_rules()

### Community 95 - "Community 95"
Cohesion: 0.29
Nodes (4): env(), fixture, #20: quiz/poll details and results follow the class access rule., _teacher()

### Community 97 - "Community 97"
Cohesion: 0.38
Nodes (7): check_secure(), insecure_settings(), Refuse to run with published secrets, or with unauthenticated WebSockets…, Names of settings still at their public, repo-published defaults., Settings, test_unauthenticated_websockets_need_debug(), BaseSettings

### Community 98 - "Community 98"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 99 - "Community 99"
Cohesion: 0.50
Nodes (4): main(), One-time migration: convert legacy naive-UTC timestamps to naive IST. Prior to…, _shift(), sqlite3

### Community 101 - "Community 101"
Cohesion: 0.50
Nodes (4): client(), _drain_background_tasks(), fixture, TestClient on an empty database (the app seeds the super admin).

### Community 102 - "Community 102"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

### Community 103 - "Community 103"
Cohesion: 0.67
Nodes (3): SQLite ignores foreign keys unless asked, per connection., _sqlite_pragmas(), listens_for

### Community 104 - "Community 104"
Cohesion: 0.67
Nodes (3): MigrationError, A migration cannot be applied safely; the message says what to do., RuntimeError

## Knowledge Gaps
- **50 isolated node(s):** `StaleRender`, `ASAN_OPTIONS`, `run.sh script`, `afl-prepare-linux.sh script`, `afl.sh script` (+45 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1048 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **127 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 11`, `Community 15`, `Community 18`, `Community 20`, `Community 23`, `Community 24`, `Community 25`, `Community 31`, `Community 37`, `Community 44`, `Community 60`, `Community 69`, `Community 76`, `Community 82`, `Community 88`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `select()` connect `Community 20` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 7`, `Community 10`, `Community 11`, `Community 15`, `Community 16`, `Community 23`, `Community 25`, `Community 27`, `Community 31`, `Community 32`, `Community 34`, `Community 37`, `Community 41`, `Community 42`, `Community 50`, `Community 56`, `Community 59`, `Community 60`, `Community 61`, `Community 66`, `Community 73`, `Community 76`, `Community 82`, `Community 89`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `User` connect `Community 0` to `Community 64`, `Community 2`, `Community 3`, `Community 4`, `Community 27`, `Community 10`, `Community 15`, `Community 16`, `Community 48`, `Community 82`, `Community 20`, `Community 23`, `Community 59`, `Community 60`, `Community 31`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 165 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 165 INFERRED edges - model-reasoned connections that need verification._
- **Are the 130 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 130 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `ASAN_OPTIONS`, `run.sh script` to the rest of the system?**
  _50 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.042355100970364545 - nodes in this community are weakly interconnected._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
