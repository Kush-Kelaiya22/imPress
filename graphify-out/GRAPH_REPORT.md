# Graph Report - impress-device-batch-fix-179  (2026-10-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3512 nodes · 9713 edges · 233 communities (109 shown, 124 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1433 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cbe9e1c3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- EspDevice
- select
- login
- App.jsx
- migrations.py
- app.js
- routers/auth.py
- schemas.py
- wifi_client.c
- models.py
- mesh_master.c
- class_c6/main/main.c
- nvs_open
- run_tests.py
- esp_websocket_client.c
- release.py
- login
- display.c
- make_user
- ClassSession
- test_quiz_timer.py
- test_fault_injection.py
- quizzes.py
- cJSON_Utils.c
- courses.py
- cJSON.c
- backend/tests/conftest.py
- firmware_signing.py
- cJSON_Delete
- make_class
- pathlib
- firmware_store.py
- firmware.py
- tests/test_deployments.py
- upload_firmware
- services/deployments.py
- students.py
- _post
- class_s3/main/ota.c
- ota_chunk.c
- test_question_import.py
- test_release.py
- api.js
- functions
- test_qualification.py
- make_student
- test_spi_slave.c
- cJSON
- test_ci_workflow.py
- test_quiz_poll_lifecycle.py
- test_firmware_registry.py
- test_maintenance_windows.py
- re
- test_firmware_signing.py
- test_db_integrity.py
- test_device_api.py
- test_schedule_occupancy.py
- tests/test_student_modules.py
- create_deployment
- ota_parse_check
- calls
- test_device_keys.py
- strip_comments_and_strings
- test_super_admin_lockout.py
- msg_to_json
- test_core_utils.py
- test_transport.py
- test_device_batch_dedup.py
- test_c6_diagnostics.py
- test_e2e_ota.py
- test_login_throttle.py
- test_graphify.py
- test_docs_consistency.py
- ConnectionManager
- test_ota_results.py
- on_ws_command
- test_backend_contract_fixture
- c_source.py
- tests/conftest.py
- Api
- schedule.py
- test_health.py
- test_role_escalation.py
- test_mesh_dedup.c
- FakeGitHub
- test_manage_cli.py
- maintenance.py
- test_secure_defaults.py
- istnow_aware
- mesh_bridge.py
- test_device_limits.py
- spi_to_http_task
- test_install_scripts.py
- test_gateway_autolink.py
- test_ota_download_gating.py
- test_device_caps.py
- test_c6_ota.py
- qemu_boot.py
- _repo
- test_query_cascade.py
- test_qemu_boot.py
- check_secure
- FakeWS
- test_hardware_requirements.py
- test_csv_questions.py
- datetime
- test_device_ws_contract.py
- test_signed_profile.py
- test_graph_portal.py
- test_csv_classes.py
- client
- test_gating_needs_the_line_to_exist_before_the_release
- _sqlite_pragmas
- class_c6/test_host/run.sh
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
- run_ota_chunk.sh
- run_host_tests.sh
- student/test_host/run.sh
- docker-entrypoint.sh
- install.sh
- start.sh
- _ancestry
- wf
- conftest
- REST API

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
  backend/tests/test_auth_sessions.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_create.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_import.py → run_tests.py
- `check()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_import.py → run_tests.py

## Import Cycles
- None detected.

## Communities (233 total, 124 thin omitted)

### Community 0 - "EspDevice"
Cohesion: 0.03
Nodes (139): asyncio, Activity logging service — records all significant actions., JWT + server-side session authentication helpers., api_key_ok(), Application configuration loaded from environment variables., Constant-time device API key comparison., get_db(), Async SQLAlchemy engine and session factory. (+131 more)

### Community 1 - "select"
Cohesion: 0.05
Nodes (120): log_activity(), AsyncSession, Write one activity log entry., User, account_refusal(), can_grant(), forbidden(), HTTPException (+112 more)

### Community 2 - "login"
Cohesion: 0.05
Nodes (85): auth(), login(), fixture, su(), parametrize, Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py…, _session_row(), q() (+77 more)

### Community 3 - "App.jsx"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 4 - "migrations.py"
Cohesion: 0.05
Nodes (68): AsyncConnection, AsyncEngine, _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), health() (+60 more)

### Community 5 - "app.js"
Cohesion: 0.08
Nodes (69): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+61 more)

### Community 6 - "routers/auth.py"
Cohesion: 0.05
Nodes (65): create_session(), generate_session_token(), get_current_user(), get_current_user_light(), hash_password(), _load_session_by_hash(), AsyncSession, Request (+57 more)

### Community 7 - "schemas.py"
Cohesion: 0.05
Nodes (67): ActivityLogResponse, AdminUserCreate, BulkStudentRegister, ClassAssignTeacher, ClassCreate, ClassFacultyUpdate, ClassJoin, ClassResponse (+59 more)

### Community 8 - "wifi_client.c"
Cohesion: 0.05
Nodes (60): adc_oneshot, backend_fail_t, crypto, esp_heap_caps, esp_http_client, esp_log, esp_netif, esp_ota_handle_t (+52 more)

### Community 9 - "models.py"
Cohesion: 0.07
Nodes (64): Base, Attendance, ClassOccurrenceException, LoginThrottle, Poll, PollVote, QuizAnswer, QuizQuestion (+56 more)

### Community 10 - "mesh_master.c"
Cohesion: 0.07
Nodes (64): BaseType_t, esp_now, spi_slave_read(), spi_slave_send(), SemaphoreHandle_t, xSemaphoreGive(), xSemaphoreGiveFromISR(), xSemaphoreTake() (+56 more)

### Community 11 - "class_c6/main/main.c"
Cohesion: 0.06
Nodes (28): cjson, esp_app_desc, esp_bit_defs, esp_efuse, esp_err, esp_event, esp_idf_version, esp_transport_ws (+20 more)

### Community 12 - "nvs_open"
Cohesion: 0.08
Nodes (61): config, nvs_handle_t, init_nvs_config(), nvs_save_class_id(), _read_str(), ota_c6_boot_check(), remember_target(), test_backend_assigned_class_id_survives_reboot() (+53 more)

### Community 13 - "run_tests.py"
Cohesion: 0.06
Nodes (60): platform, Popen, posix_only, CaseResult, discover(), fmt_secs(), _idf_command(), _idf_image_present() (+52 more)

### Community 14 - "esp_websocket_client.c"
Cohesion: 0.09
Nodes (64): errno, esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client_config_t, esp_websocket_client_handle_t (+56 more)

### Community 15 - "release.py"
Cohesion: 0.08
Nodes (64): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+56 more)

### Community 16 - "login"
Cohesion: 0.07
Nodes (45): os, playwright_sync_api, init_env(), Path, Create or complete backend/.env from backend/.env.example (#42). The public…, Returns the names of the secrets it generated., socket, sys (+37 more)

### Community 17 - "display.c"
Cohesion: 0.08
Nodes (44): esp_random, esp_wifi, display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown(), display_show_provision_state() (+36 more)

### Community 18 - "make_user"
Cohesion: 0.07
Nodes (48): make_user(), Create a user through the admin API; returns (user_id, auth headers)., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password(), test_admin_password_reset(), test_create_user_field_limits() (+40 more)

### Community 19 - "ClassSession"
Cohesion: 0.10
Nodes (50): Any, ClassSession, allowed(), class_access(), class_owner_or_admin(), Authorization policy: the one place that decides who may do what (#122). Every…, Delete a class: its primary teacher or an administrator., Does `user`'s role grant `permission`? Default deny, inactive denied. (+42 more)

### Community 20 - "test_quiz_timer.py"
Cohesion: 0.08
Nodes (46): advance(), answer_closed(), deadline(), finish(), AsyncSession, datetime, quiz_timer_loop(), Quiz timing (#73): advance `per_question` quizzes and end `total` quizzes when… (+38 more)

### Community 21 - "test_fault_injection.py"
Cohesion: 0.06
Nodes (35): answer(), Gateway, join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent… (+27 more)

### Community 22 - "quizzes.py"
Cohesion: 0.09
Nodes (46): commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, Quiz, Example file with every column. Public: it contains no data., create_quiz(), get_quiz(), import_question_csv() (+38 more)

### Community 23 - "cJSON_Utils.c"
Cohesion: 0.15
Nodes (46): cJSON_AddItemToObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc(), apply_patch(), cJSON (+38 more)

### Community 24 - "courses.py"
Cohesion: 0.07
Nodes (41): Course, create_course(), delete_course(), get_course(), list_courses(), AsyncSession, delete, get (+33 more)

### Community 25 - "cJSON.c"
Cohesion: 0.12
Nodes (38): cJSON_Hooks, buffer_skip_whitespace(), cJSON_bool, case_insensitive_strcmp(), cJSON_Compare(), cJSON_InitHooks(), cJSON_Minify(), cJSON_ParseWithLength() (+30 more)

### Community 26 - "backend/tests/conftest.py"
Cohesion: 0.06
Nodes (21): Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, Smoke tests: the app boots on an empty DB and its basic contracts hold., test_seeded_super_admin_can_log_in(), #21: co-faculty can run quizzes/polls for their class; outsiders still can't., _create(), parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted() (+13 more)

### Community 27 - "firmware_signing.py"
Cohesion: 0.10
Nodes (36): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts…, Length of the app image itself (segments, checksum, appended SHA-256), without… (+28 more)

### Community 28 - "cJSON_Delete"
Cohesion: 0.12
Nodes (36): batch_init(), add_item_to_object(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddBoolToObject(), cJSON_AddFalseToObject(), cJSON_AddItemToObjectCS(), cJSON_AddNullToObject() (+28 more)

### Community 29 - "make_class"
Cohesion: 0.09
Nodes (31): make_class(), Create a class via /api/admin/classes; optionally activate it., Classes (routers/classes.py, admin class routes) and courses…, test_activate_deactivate_toggle(), test_back_to_back_slots_do_not_warn(), test_class_codes_are_unique(), test_join_requires_known_active_code(), test_other_teachers_class_is_forbidden() (+23 more)

### Community 30 - "pathlib"
Cohesion: 0.09
Nodes (27): argparse, json, pathlib, append_coverage(), component_for(), enrich(), main(), node_id() (+19 more)

### Community 31 - "firmware_store.py"
Cohesion: 0.13
Nodes (31): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, Digest of the public key every image must be signed with…, site_key_digest(), adopt_legacy_files(), artifact_file(), artifact_path(), AsyncSession (+23 more)

### Community 32 - "firmware.py"
Cohesion: 0.13
Nodes (31): approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get(), _latest_approved(), list_firmware() (+23 more)

### Community 33 - "tests/test_deployments.py"
Cohesion: 0.21
Nodes (31): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+23 more)

### Community 34 - "upload_firmware"
Cohesion: 0.16
Nodes (28): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), _artifact(), _hub(), _push(), #36: firmware version manager: approval, deprecation, retention, usage., _set(), test_admin_only() (+20 more)

### Community 35 - "services/deployments.py"
Cohesion: 0.14
Nodes (29): DeploymentTarget, One device in a deployment, with its update state., active_target(), cancel(), create_deployment(), exclusion_reason(), _finish(), observe_download() (+21 more)

### Community 36 - "students.py"
Cohesion: 0.15
Nodes (29): Student, bulk_create_students(), _create_one(), create_student(), deactivate_student(), get_student(), hard_delete_student(), import_students_csv() (+21 more)

### Community 37 - "_post"
Cohesion: 0.15
Nodes (28): cancel_deployment(), Continue a paused deployment, accepting the failures that paused it., Cancel devices that haven't started installing; the rest finish., resume_deployment(), _count(), q(), _csv(), _post() (+20 more)

### Community 38 - "class_s3/main/ota.c"
Cohesion: 0.11
Nodes (25): esp_chip_info, esp_crt_bundle, esp_flash, esp_mac, esp_ota_ops, esp_psram, cfg_has_device_key(), esp_err_t (+17 more)

### Community 39 - "ota_chunk.c"
Cohesion: 0.17
Nodes (27): assert, advance(), ota_rx_t, has(), ota_chunk_count(), ota_chunk_len(), ota_rx_accept(), ota_rx_complete() (+19 more)

### Community 40 - "test_question_import.py"
Cohesion: 0.16
Nodes (27): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+19 more)

### Community 42 - "api.js"
Cohesion: 0.11
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 43 - "functions"
Cohesion: 0.12
Nodes (21): functions(), {name: body_text} for every top-level function definition in a C file., #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #7: the S3 loads its config before the mesh uses g_cfg.mesh_channel, and a…, test_config_loaded_before_mesh_init(), test_config_loader_initialises_nvs_itself(), test_mesh_init_reads_channel_from_config() (+13 more)

### Community 44 - "test_qualification.py"
Cohesion: 0.12
Nodes (21): _Device, ota_client(), The OTA client of a gateway or hub, as the firmware implements it., The image must go through the simulated client, and each corruption must be…, _artifact(), _fail_report(), _problems(), parametrize (+13 more)

### Community 45 - "make_student"
Cohesion: 0.11
Nodes (23): make_student(), live(), fixture, _matrix(), parametrize, Route × caller matrix (#122): which status every route returns to each kind of…, _seed(), test_route_matrix_matches_snapshot() (+15 more)

### Community 46 - "test_spi_slave.c"
Cohesion: 0.14
Nodes (25): queue_slot(), ready_update(), spi_slave_init(), esp_err_t, spi_slave_transaction_t, TickType_t, clobber_stack(), gpio_config() (+17 more)

### Community 47 - "cJSON"
Cohesion: 0.13
Nodes (26): add_item_to_array(), cJSON, cJSON_AddItemReferenceToArray(), cJSON_AddItemReferenceToObject(), cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive(), cJSON_DetachItemFromArray() (+18 more)

### Community 48 - "test_ci_workflow.py"
Cohesion: 0.12
Nodes (17): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+9 more)

### Community 49 - "test_quiz_poll_lifecycle.py"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 50 - "test_firmware_registry.py"
Cohesion: 0.14
Nodes (21): make_image(), _count(), q(), parametrize, #35: uploaded firmware is validated as a real imPress image and registered…, Against genuine ESP-IDF output when a local build exists (the synthetic images…, A scripts/build_signed.sh build (#66), when one exists locally., test_a_c6_image_is_never_pushed_to_an_s3() (+13 more)

### Community 51 - "test_maintenance_windows.py"
Cohesion: 0.22
Nodes (21): _advance(), _artifact(), at(), clock(), _deploy(), _gateway(), fixture, parametrize (+13 more)

### Community 52 - "re"
Cohesion: 0.12
Nodes (19): _calls(), The authorization policy is the one place that decides access (#122)., A staff route without a policy permission is a new hole; device routes…, Role checks scattered across routers drifted before (#19-#21, #116, #121)., docs/design/authorization.md shows GRANTS; it must not drift., _routes(), test_every_route_is_governed_by_the_policy_or_listed(), test_no_role_comparisons_outside_the_policy() (+11 more)

### Community 53 - "test_firmware_signing.py"
Cohesion: 0.15
Nodes (19): _der(), load_public_key(), (tag, start of content, end of content) of the DER element at pos., (n, e) from a PEM RSA public key (SubjectPublicKeyInfo, as written by…, _digest(), h(), fixture, parametrize (+11 more)

### Community 54 - "test_db_integrity.py"
Cohesion: 0.14
Nodes (21): _count(), q(), _fk_violations(), q(), _insert_twice(), go(), fixture, #41: the database enforces its own integrity (foreign keys, uniqueness), and… (+13 more)

### Community 55 - "test_device_api.py"
Cohesion: 0.19
Nodes (19): _activity(), q(), _device(), q(), Gateway-facing device API (routers/device.py) + presence service…, _register(), test_attendance_paths(), count() (+11 more)

### Community 56 - "test_schedule_occupancy.py"
Cohesion: 0.17
Nodes (18): _add(), _busy(), phy(), fixture, parametrize, Dated timetable changes and room occupancy (#126). 2026-10-12 is a Monday,…, su(), test_a_cancelled_day_frees_every_slot() (+10 more)

### Community 57 - "tests/test_student_modules.py"
Cohesion: 0.27
Nodes (20): _age(), q(), _batch(), beat(), join(), leave(), _modules(), #40: the student module inventory. Modules seen on a gateway's mesh are listed… (+12 more)

### Community 58 - "create_deployment"
Cohesion: 0.18
Nodes (20): FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, _act(), create_deployment(), deployment_dict(), DeploymentCreate, _get(), get_deployment() (+12 more)

### Community 59 - "ota_parse_check"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 60 - "calls"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 61 - "test_device_keys.py"
Cohesion: 0.28
Nodes (18): _beat(), _device(), q(), _key(), #66: per-device keys. Devices register with the shared key and are issued their…, _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out() (+10 more)

### Community 62 - "strip_comments_and_strings"
Cohesion: 0.13
Nodes (12): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, #132: both backend clients classify a failure and log the hint, and the boot…, #129: both registrations append the caps object from device_caps.h., test_connection_failures_say_why(), test_every_backend_client_gets_the_tls_settings(), test_gateway_and_hub_report_their_capabilities(), test_version_comes_from_the_image() (+4 more)

### Community 63 - "test_super_admin_lockout.py"
Cohesion: 0.15
Nodes (16): _me(), fixture, parametrize, At least one active super admin always remains (#116). The original failure: a…, The original lockout path: PUT with is_active=false on yourself (#116, #119)., Two super admins disabling each other at the same moment: one must fail., su(), test_concurrent_mutual_deactivation_leaves_one_super_admin() (+8 more)

### Community 64 - "msg_to_json"
Cohesion: 0.26
Nodes (15): msg_type_t, msg_to_json(), student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join() (+7 more)

### Community 65 - "test_core_utils.py"
Cohesion: 0.18
Nodes (16): _parse_time(), Convert "HH:MM" → minutes since midnight. Returns None if malformed., Two time slots overlap when neither fully precedes the other. Overnight / wrap-…, Two classes only clash if they run in the same semester/window. Priority:…, _same_academic_window(), _slots_conflict(), normalize_version(), parametrize (+8 more)

### Community 66 - "test_transport.py"
Cohesion: 0.15
Nodes (11): is_loopback(), needs_https(), Should this request be refused for arriving without TLS?, _https(), fixture, HTTPS for staff traffic and browser security headers (#152)., uvicorn turns X-Forwarded-Proto from a trusted proxy into the scheme; the test…, strict() (+3 more)

### Community 67 - "test_device_batch_dedup.py"
Cohesion: 0.29
Nodes (16): answer(), batch(), count(), q(), parametrize, #6: /api/device/batch validates and de-duplicates mesh answers/votes., test_distinct_students_and_questions_all_count(), test_inactive_quiz_and_closed_poll_skipped() (+8 more)

### Community 68 - "test_c6_diagnostics.py"
Cohesion: 0.15
Nodes (9): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat() (+1 more)

### Community 69 - "test_e2e_ota.py"
Cohesion: 0.28
Nodes (15): advance_all(), deployments_loop(), Background task: advance running deployments (durable across restarts)., _advance(), _dep(), _deploy(), _prompt(), #43 end to end: a firmware release reaches three rooms through the staged… (+7 more)

### Community 70 - "test_login_throttle.py"
Cohesion: 0.18
Nodes (15): clock(), fixture, parametrize, Password guessing is slowed; new passwords resist trivial guesses (#153)., test_another_username_is_not_affected(), test_counters_survive_a_restart(), test_existing_passwords_keep_working(), test_one_address_guessing_many_usernames_is_slowed() (+7 more)

### Community 71 - "test_graphify.py"
Cohesion: 0.15
Nodes (10): _publish_graph_visualization(), Sphinx configuration for the public imPress documentation site., Expose the generated graph beneath the hosted ``/graph/`` page., setup(), shutil, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards() (+2 more)

### Community 72 - "test_docs_consistency.py"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 73 - "ConnectionManager"
Cohesion: 0.15
Nodes (7): ConnectionManager, WebSocket, Send a JSON message to ALL connections in a class room (teachers + devices)., Send a JSON message only to connections matching the given role., Alias for broadcast_to_class., Manages WebSocket connections grouped by class ID. Teachers connect to manage…, Close every socket of a user whose access was revoked (#118).

### Community 74 - "test_ota_results.py"
Cohesion: 0.30
Nodes (14): _device(), q(), _push(), parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report(), test_applied_with_another_version_is_not_success(), test_applied_with_the_pushed_version_completes_the_update() (+6 more)

### Community 75 - "on_ws_command"
Cohesion: 0.30
Nodes (14): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+6 more)

### Community 76 - "test_backend_contract_fixture"
Cohesion: 0.23
Nodes (14): cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput(), msg_t (+6 more)

### Community 77 - "c_source.py"
Cohesion: 0.21
Nodes (12): mentions(), Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch(), #73: the student module counts down a timed question's time_limit_s and stops… (+4 more)

### Community 78 - "tests/conftest.py"
Cohesion: 0.20
Nodes (11): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+3 more)

### Community 79 - "Api"
Cohesion: 0.13
Nodes (11): Api, browser(), _free_port(), page(), fixture, A page that fails the test on any uncaught JS error; screenshot at the end., Tiny JSON client for setting up data the test then checks in the UI., multipart/form-data POST of one file field named 'file'. (+3 more)

### Community 80 - "schedule.py"
Cohesion: 0.26
Nodes (13): When each authoritative timetable source last synchronised (#126/#127). No row…, ScheduleSource, _at(), Busy, occupancy(), AsyncSession, datetime, Schedule conflict validation for classroom sections (hybrid scheduling).… (+5 more)

### Community 81 - "test_health.py"
Cohesion: 0.21
Nodes (12): health(), datetime, Device health states (#39), computed from the latest heartbeat. Rules, in order…, (state, reasons) for one device., _dev(), parametrize, #39: device health states from the latest heartbeat diagnostics., test_heartbeat_stores_diagnostics_and_old_firmware_still_works() (+4 more)

### Community 82 - "test_role_escalation.py"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10, #119: only a super admin can grant/remove admin-level roles; roles are a…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 83 - "test_mesh_dedup.c"
Cohesion: 0.27
Nodes (13): mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main(), simulate(), test_dedup_window_and_wrap(), test_id_ignores_hops_but_not_content() (+5 more)

### Community 84 - "FakeGitHub"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 85 - "test_manage_cli.py"
Cohesion: 0.24
Nodes (10): main(), _lock_out(), Offline recovery of a locked-out installation (#120)., A database from before #116: no triggers, every super admin inactive., _restore(), _sql(), test_cli_exit_codes(), test_promotes_an_existing_account() (+2 more)

### Community 86 - "maintenance.py"
Cohesion: 0.26
Nodes (12): _live(), next_window(), AsyncSession, datetime, Maintenance windows for classroom hubs and gateways (#128). A hub (S3) or…, The class whose room this device serves: a gateway's linked class, or the class…, (None, "") when the update may start now; otherwise (when to look again, why…, room_class() (+4 more)

### Community 87 - "test_secure_defaults.py"
Cohesion: 0.19
Nodes (8): _reset_db(), _fresh_settings(), #11: no working public credentials or debug leaks by default., test_cors_only_configured_origins(), test_debug_and_sql_echo_off_by_default(), test_first_admin_password_is_random_not_admin123(), test_refuses_default_secrets_outside_debug(), fastapi_testclient

### Community 88 - "istnow_aware"
Cohesion: 0.18
Nodes (12): create_access_token(), Legacy JWT creation (kept for device registration / backward compat)., as_ist(), ist_iso(), istnow_aware(), datetime, Current time as an offset-aware IST datetime., Convert any aware/naive datetime to naive IST; naive input is treated as UTC. (+4 more)

### Community 89 - "mesh_bridge.py"
Cohesion: 0.17
Nodes (11): push_device_status(), push_poll_to_mesh(), push_quiz_to_mesh(), push_student_data(), Bridge service: connects ESP device data to WebSocket clients. This service…, Push student device data (heartbeats, answers, votes) to teacher dashboard., Push individual device status update., Send a command to C6 devices connected via WebSocket. (+3 more)

### Community 90 - "test_device_limits.py"
Cohesion: 0.24
Nodes (8): cls(), fixture, parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student…, test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons()

### Community 91 - "spi_to_http_task"
Cohesion: 0.33
Nodes (11): batch_add(), batch_flush(), batch_flush_needed(), cJSON, item_is_heartbeat(), process_spi_payload(), spi_to_http_task(), wifi_client_is_connected() (+3 more)

### Community 92 - "test_install_scripts.py"
Cohesion: 0.33
Nodes (8): stat, _backend(), #42: the documented install path: scripts, secrets, version, CI job., test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets(), _values()

### Community 93 - "test_gateway_autolink.py"
Cohesion: 0.42
Nodes (9): _class(), _gateway_of(), q(), #17: registration must not steal a class's gateway link., _register(), test_explicit_classroom_code_still_assigns(), test_gateway_keeps_its_class_on_reregister(), test_non_gateway_registration_keeps_class_gateway() (+1 more)

### Community 94 - "test_ota_download_gating.py"
Cohesion: 0.31
Nodes (9): device(), set_pending(), go(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download() (+1 more)

### Community 95 - "test_device_caps.py"
Cohesion: 0.31
Nodes (7): Boards report what they are; images must fit them (#129)., The 32 MB octal hub image on an 8 MB quad hub aborts at boot., _register(), test_an_image_built_for_more_flash_than_the_board_has(), test_an_image_larger_than_the_board_slot_is_excluded(), test_caps_are_stored_and_shown(), test_older_firmware_without_caps_is_unknown_not_refused()

### Community 96 - "test_c6_ota.py"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 97 - "qemu_boot.py"
Cohesion: 0.28
Nodes (8): glob, find_qemu(), judge(), main(), Boot a firmware image in Espressif's QEMU and judge the serial log (#154).…, (passed, reason) for a captured log., threading, time

### Community 98 - "_repo"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 99 - "test_query_cascade.py"
Cohesion: 0.39
Nodes (6): _history(), Loading a user or a class list must not pull in the teaching history (#133).…, statements(), test_class_list_counts_without_loading_quizzes(), test_loading_a_user_is_one_statement(), load()

### Community 101 - "check_secure"
Cohesion: 0.38
Nodes (7): check_secure(), insecure_settings(), Refuse to run with published secrets, or with unauthenticated WebSockets…, Names of settings still at their public, repo-published defaults., Settings, test_unauthenticated_websockets_need_debug(), BaseSettings

### Community 102 - "FakeWS"
Cohesion: 0.29
Nodes (4): FakeWS, test_manager_disconnect_frees_empty_rooms(), test_manager_role_routing_and_dead_socket_cleanup(), scenario()

### Community 103 - "test_hardware_requirements.py"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 104 - "test_csv_questions.py"
Cohesion: 0.48
Nodes (6): _open_create_quiz(), #31: importing questions from CSV on the create-quiz page., test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz()

### Community 105 - "datetime"
Cohesion: 0.40
Nodes (5): main(), One-time migration: convert legacy naive-UTC timestamps to naive IST. Prior to…, _shift(), datetime, sqlite3

### Community 106 - "test_device_ws_contract.py"
Cohesion: 0.47
Nodes (5): _next_device_frame(), _project(), Contract test: frames the C6 gateway receives on its device WebSocket (#3). The…, The single frame an action broadcasts; it must carry a firmware event. Reads…, test_device_socket_receives_firmware_contract()

### Community 109 - "test_csv_classes.py"
Cohesion: 0.60
Nodes (4): _open(), #32: importing and exporting courses and sections on the Classrooms page., test_invalid_rows_block_the_import(), test_valid_file_creates_courses_and_sections()

### Community 110 - "client"
Cohesion: 0.50
Nodes (4): client(), _drain_background_tasks(), fixture, TestClient on an empty database (the app seeds the super admin).

### Community 111 - "test_gating_needs_the_line_to_exist_before_the_release"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

### Community 112 - "_sqlite_pragmas"
Cohesion: 0.67
Nodes (3): SQLite ignores foreign keys unless asked, per connection., _sqlite_pragmas(), listens_for

## Knowledge Gaps
- **51 isolated node(s):** `StaleRender`, `ASAN_OPTIONS`, `run.sh script`, `afl-prepare-linux.sh script`, `afl.sh script` (+46 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1061 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **124 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `EspDevice` to `select`, `login`, `migrations.py`, `routers/auth.py`, `models.py`, `test_quiz_timer.py`, `test_fault_injection.py`, `quizzes.py`, `make_class`, `firmware.py`, `tests/test_deployments.py`, `services/deployments.py`, `test_device_api.py`, `tests/test_student_modules.py`, `create_deployment`, `test_core_utils.py`, `test_e2e_ota.py`, `test_login_throttle.py`, `schedule.py`, `istnow_aware`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `select()` connect `select` to `EspDevice`, `login`, `routers/auth.py`, `models.py`, `run_tests.py`, `ClassSession`, `test_quiz_timer.py`, `test_fault_injection.py`, `quizzes.py`, `courses.py`, `firmware_store.py`, `firmware.py`, `tests/test_deployments.py`, `services/deployments.py`, `students.py`, `_post`, `test_question_import.py`, `test_quiz_poll_lifecycle.py`, `test_firmware_registry.py`, `test_db_integrity.py`, `test_device_api.py`, `tests/test_student_modules.py`, `create_deployment`, `test_device_keys.py`, `test_device_batch_dedup.py`, `test_e2e_ota.py`, `test_ota_results.py`, `schedule.py`, `test_health.py`, `maintenance.py`, `test_gateway_autolink.py`, `test_query_cascade.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `User` connect `select` to `EspDevice`, `firmware.py`, `test_query_cascade.py`, `students.py`, `_post`, `routers/auth.py`, `models.py`, `ClassSession`, `re`, `quizzes.py`, `courses.py`, `create_deployment`, `make_class`, `test_super_admin_lockout.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
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
