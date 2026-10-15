# Graph Report - imPress  (2026-10-15)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 5397 nodes · 14632 edges · 349 communities (209 shown, 140 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1917 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `50eb52ba`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- User
- login
- select
- main.py
- app.js
- app/auth.py
- cJSON.c
- nvs_open
- App.jsx
- schemas.py
- firmware.py
- integrity.py
- backend/tests/conftest.py
- make_user
- release.py
- models.py
- services/deployments.py
- class_c6/main/main.c
- esp_websocket_client.c
- sandbox.py
- rootops.py
- test_firmware_signing.py
- quizzes.py
- make_class
- mesh_master.c
- display.c
- tests/test_student_modules.py
- ClassSession
- pages.js
- dbgateway.py
- cJSON_Utils.c
- test_mode.py
- make_student
- protocol.c
- Student
- re
- test_quiz_timer.py
- pathlib
- db
- ui.js
- class_s3/main/ota.c
- test_hardening.py
- test_device_batch_dedup.py
- stdint
- test_qualification.py
- services/backups.py
- .update
- test_spi_slave.c
- on_ws_command
- test_release.py
- migrations.py
- app/gpc.py
- wifi_client.c
- test_db_gateway.py
- api.js
- tests/test_deployments.py
- firmware/tests/test_classroom_sim.py
- run_tests.py
- cJSON_bool
- ota_chunk.c
- services/approvals.py
- test_question_import.py
- string
- UserSession
- screenshots.py
- test_ci_workflow.py
- traffic.py
- test_quiz_poll_lifecycle.py
- test_core_utils.py
- test_policy.py
- ed25519.py
- load
- presence
- testdata.js
- test_console_v22.py
- .fail
- auditsink.py
- ConnectionManager
- test_firmware_registry.py
- firmware
- test_spi_link.c
- Screen
- qualification.py
- test_schedule_occupancy.py
- console.md
- signing.py
- dashboard.js
- calls
- functions
- test_run_tests.py
- test_secure_defaults.py
- services/features.py
- iips.py
- test_device_api.py
- test_device_keys.py
- test_migrations.py
- test_super_admin_lockout.py
- classroom_sim.py
- msg_to_json
- ui_tests/conftest.py
- login
- test_manage_cli.py
- events.py
- test_fault_injection.py
- production-hardening.md
- test_backend_contract_fixture
- scripts/gpc.py
- Console
- .say
- boot_verify.py
- data-integrity.md
- playwright_sync_api
- sys
- test_c6_diagnostics.py
- test_login_throttle.py
- test_trusted_installer.py
- test_graphify.py
- test_docs_consistency.py
- FakeGitHub
- ._args
- _write_refused
- rootscreen.py
- create_poll
- test_iips.py
- upload_firmware
- test_ota_download_gating.py
- test_ota_results.py
- test_session_cookie.py
- test_sessions_v22.py
- test_spi_link.py
- tests/conftest.py
- throttle.py
- Test mode and test data
- test_results_enrolled_only.py
- test_role_escalation.py
- test_transport.py
- v2.2.md
- migrate
- finish_setup
- test_db_integrity.py
- strip_comments_and_strings
- test_health.py
- mesh_bridge.py
- settings.js
- test_e2e_ota.py
- Mesh frame authentication (design, proposed)
- launcher.sh
- test_motion.py
- main
- system.js
- spi_to_http_task
- v2.2 plan and engineering record
- Personalization, accessibility, search and the dashboard
- c_source.py
- test_install_scripts.py
- .run
- account_refusal
- ClassCreate
- test_gateway_autolink.py
- test_quiz_correct_option.py
- Data integrity: the database gateway, seals and self-repair
- Accounts, first sign-in and the default super admin
- Personalization, accessibility, search and the dashboard
- Student
- qemu_boot.py
- table
- Frequently asked questions
- test_c6_ota.py
- _repo
- test_upgrade_integrity.py
- key_id
- system_status
- prefs.py
- shell.js
- test_query_cascade.py
- Web app design and motion
- Production hardening checklist
- mentions
- test_qemu_boot.py
- _requirements
- console.py
- traffic_overview
- test_device_caps.py
- test_backup_script.py
- Incident response
- Build, configure and flash the firmware
- Administrator guide
- Gateway
- test_hardware_requirements.py
- test_csv_questions.py
- test_firmware.py
- Global policy control (GPC)
- Permissions and OTA review (v2.2)
- First 30 minutes with imPress
- Teacher guide
- gen_motion_tokens.py
- test_csp.py
- test_live_socket.py
- sqlite3
- test_graph_portal.py
- Control mapping
- Backups, restore and resetting the system
- test_csv_classes.py
- test_diagnostics.py
- .do_sessions
- test_a_background_loop_cancelled_mid_query_stops
- Privacy notice template
- test_gating_needs_the_line_to_exist_before_the_release
- ui_tests/test_student_modules.py
- test_system_approvals.py
- MigrationError
- onboarding.js
- class_c6/test_host/run.sh
- _stop
- build_signed.sh
- docker-entrypoint.sh
- firmware_key.sh
- motion.js
- cJSON_InitHooks
- afl-prepare-linux.sh
- afl.sh script
- ossfuzz.sh
- start_server.sh
- run_config.sh
- run_ota_logic.sh
- run_student_set.sh
- run_ws_command.sh
- protocol/test_host/run.sh
- run_answer_ack.sh
- run_backend_hint.sh
- run_mesh_dedup.sh
- run_ota_chunk.sh
- run_spi_link.sh
- run_host_tests.sh
- student/test_host/run.sh
- backup.sh
- console.sh
- console 2.sh
- install.sh
- start.sh
- datetime
- date
- WebSocket
- fixture
- cJSON
- esp_event_base_t
- esp_err_t
- TickType_t
- REST API

## God Nodes (most connected - your core abstractions)
1. `User` - 260 edges
2. `login()` - 254 edges
3. `auth()` - 253 edges
4. `select()` - 221 edges
5. `make_user()` - 151 edges
6. `istnow()` - 134 edges
7. `log_activity()` - 123 edges
8. `EspDevice` - 111 edges
9. `ClassSession` - 108 edges
10. `make_class()` - 94 edges

## Surprising Connections (you probably didn't know these)
- `Linux and macOS` --references--> `admin()`  [INFERRED]
  docs/install/platforms.md → backend/tests/test_class_import.py
- `Placeholders used in this documentation` --references--> `admin()`  [INFERRED]
  docs/reference/placeholders.md → backend/tests/test_class_import.py
- `1. Start the server` --references--> `admin()`  [INFERRED]
  docs/releases/v2.2.md → backend/tests/test_class_import.py
- `2. Log in` --references--> `admin()`  [INFERRED]
  docs/releases/v2.2.md → backend/tests/test_class_import.py
- `1. Install and sign in` --references--> `admin()`  [INFERRED]
  docs/user-guide/README.md → backend/tests/test_class_import.py

## Import Cycles
- None detected.

## Communities (349 total, 140 thin omitted)

### Community 0 - "User"
Cohesion: 0.05
Nodes (125): log_activity(), AsyncSession, Write one activity log entry., User, can_grant(), is_faculty_role(), is_super_role(), Enrol or remove students, list a class roster: anyone with class access… (+117 more)

### Community 1 - "login"
Cohesion: 0.04
Nodes (110): auth(), login(), _new(), parametrize, v2.2 accounts: display names, TA, the password rule, temporary credentials, the…, test_a_class_has_an_icon_and_a_colour(), test_a_deleted_account_goes_to_the_trash_and_comes_back(), test_a_new_account_gets_a_generated_password_that_must_be_changed() (+102 more)

### Community 2 - "select"
Cohesion: 0.05
Nodes (110): authorize(), _by_mac(), caller_for_key(), denial(), device_caller(), DeviceCaller, key_hash(), new_device_key() (+102 more)

### Community 3 - "main.py"
Cohesion: 0.04
Nodes (86): asyncio, Activity logging service — records all significant actions., api_key_ok(), Application configuration loaded from environment variables., The version with its patch number, as the release page names it (2.2.14). A…, Constant-time device API key comparison., _release_label(), get_db() (+78 more)

### Community 4 - "app.js"
Cohesion: 0.05
Nodes (76): activePanel(), deletedPanel(), openActivityDrawer(), peoplePanel(), reloadUsers(), renderAdminActivity(), renderAdminUsers(), renderUserAccess() (+68 more)

### Community 5 - "app/auth.py"
Cohesion: 0.05
Nodes (77): clear_session_cookie(), _client_family(), create_access_token(), create_session(), generate_session_token(), get_current_user(), get_current_user_light(), hash_password() (+69 more)

### Community 6 - "cJSON.c"
Cohesion: 0.08
Nodes (70): batch_init(), add_item_to_array(), add_item_to_object(), cJSON, case_insensitive_strcmp(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddBoolToObject() (+62 more)

### Community 7 - "nvs_open"
Cohesion: 0.08
Nodes (65): nvs_handle_t, cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str(), _store_dev_key() (+57 more)

### Community 8 - "App.jsx"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 9 - "schemas.py"
Cohesion: 0.05
Nodes (71): ActivityLogResponse, AdminUserCreate, ClassAssignTeacher, ClassDevicesResponse, ClassFacultyUpdate, ClassJoin, CourseCreate, CourseResponse (+63 more)

### Community 10 - "firmware.py"
Cohesion: 0.07
Nodes (63): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get() (+55 more)

### Community 11 - "integrity.py"
Cohesion: 0.08
Nodes (64): get(), Acknowledge, clear_data(), ClearRequest, integrity_acknowledge(), integrity_info(), integrity_verify(), BaseModel (+56 more)

### Community 12 - "backend/tests/conftest.py"
Cohesion: 0.04
Nodes (39): Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, Smoke tests: the app boots on an empty DB and its basic contracts hold., test_seeded_super_admin_can_log_in(), fixture, quiz(), v2.2: a simulated classroom feeds the real backend.…, env(), fixture (+31 more)

### Community 13 - "make_user"
Cohesion: 0.05
Nodes (59): make_user(), find(), Create a user through the admin API; returns (user_id, auth headers). A super…, _import(), fixture, parametrize, Admin user management (routers/admin.py /api/admin/users*)., su() (+51 more)

### Community 14 - "release.py"
Cohesion: 0.08
Nodes (64): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+56 more)

### Community 15 - "models.py"
Cohesion: 0.06
Nodes (59): Base, Attendance, ClassOccurrenceException, Poll, PollVote, QuizAnswer, QuizQuestion, SQLAlchemy ORM models for imPress. (+51 more)

### Community 16 - "services/deployments.py"
Cohesion: 0.07
Nodes (61): DeploymentTarget, FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., admin_push_ota(), Queue a firmware version for a node; the device pulls it on its next poll (R8).…, _act(), cancel_deployment() (+53 more)

### Community 17 - "class_c6/main/main.c"
Cohesion: 0.05
Nodes (44): crypto, esp_app_desc, esp_bit_defs, esp_http_client, esp_log, esp_mac, esp_ota_handle_t, esp_partition_t (+36 more)

### Community 18 - "esp_websocket_client.c"
Cohesion: 0.11
Nodes (59): esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client_config_t, esp_websocket_client_handle_t, esp_websocket_error_type_t (+51 more)

### Community 19 - "sandbox.py"
Cohesion: 0.08
Nodes (50): Course, generate(), _person(), Realistic, unique, internally consistent test data (v2.2 test mode).…, Values already in the database (or rows the user typed)., Three characters: 001-999, then base 36 (A00…): a roll stays 10 long., _serial(), Taken (+42 more)

### Community 20 - "rootops.py"
Cohesion: 0.06
Nodes (51): Revoke every session of a user (except `keep_id`), in the caller's transaction…, revoke_user_sessions(), act_as(), Set the principal for the rest of this request (or task)., DeletedUser, A deleted account, kept so it can be restored until `purge_after` (30 days). A…, complexity_problem(), generate() (+43 more)

### Community 21 - "test_firmware_signing.py"
Cohesion: 0.08
Nodes (47): argparse, _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts… (+39 more)

### Community 22 - "quizzes.py"
Cohesion: 0.10
Nodes (51): commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, Quiz, Example file with every column. Public: it contains no data., create_quiz(), get_quiz(), import_question_csv() (+43 more)

### Community 23 - "make_class"
Cohesion: 0.06
Nodes (44): make_class(), Create a class via /api/admin/classes; optionally activate it., fixture, Classes (routers/classes.py, admin class routes) and courses…, su(), test_activate_deactivate_toggle(), test_back_to_back_slots_do_not_warn(), test_class_codes_are_unique() (+36 more)

### Community 24 - "mesh_master.c"
Cohesion: 0.08
Nodes (47): BaseType_t, esp_efuse, esp_random, ready_update(), spi_slave_read(), spi_slave_send(), xSemaphoreGive(), xSemaphoreTake() (+39 more)

### Community 25 - "display.c"
Cohesion: 0.09
Nodes (48): esp_now, esp_wifi, firmware_student_main_config, firmware_student_main_display, display_clear(), display_deinit(), display_flush(), display_init() (+40 more)

### Community 26 - "tests/test_student_modules.py"
Cohesion: 0.11
Nodes (46): _advance(), _artifact(), at(), clock(), _deploy(), _gateway(), fixture, parametrize (+38 more)

### Community 27 - "ClassSession"
Cohesion: 0.10
Nodes (48): Any, ClassSession, class_access(), class_owner_or_admin(), Work with a class: its primary teacher, any co-faculty member, or an…, Delete a class: its primary teacher or an administrator., Re-select a class after mutation so selectin relationships load in the async…, _accessible_class() (+40 more)

### Community 28 - "pages.js"
Cohesion: 0.08
Nodes (44): ACTIVITY_KINDS, activityDetail(), activityItem(), activityKind(), activityPanel(), activityTitle(), APPROVAL_LABEL, approvalRow() (+36 more)

### Community 29 - "dbgateway.py"
Cohesion: 0.08
Nodes (40): _aggregate_mac(), _check_user_rows(), current(), _get_aggregate(), install(), _before_flush(), _check(), _on_commit() (+32 more)

### Community 30 - "cJSON_Utils.c"
Cohesion: 0.15
Nodes (46): cJSON_AddItemToObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc(), apply_patch(), cJSON (+38 more)

### Community 31 - "test_mode.py"
Cohesion: 0.11
Nodes (42): decide(), delete_dataset(), disable(), Enable, _err(), export(), Generate, import_() (+34 more)

### Community 32 - "make_student"
Cohesion: 0.07
Nodes (40): make_student(), test_attendance_paths(), count(), live(), fixture, _matrix(), parametrize, Route × caller matrix (#122): which status every route returns to each kind of… (+32 more)

### Community 33 - "protocol.c"
Cohesion: 0.10
Nodes (39): answer_tx_t, load_tx(), msg_t, on_student_message(), answer_tx_ack(), answer_tx_poll(), answer_tx_start(), msg_t (+31 more)

### Community 34 - "Student"
Cohesion: 0.11
Nodes (41): Student, StudentEnrollment, bulk_create_students(), _create_one(), create_student(), deactivate_student(), get_student(), hard_delete_student() (+33 more)

### Community 35 - "re"
Cohesion: 0.08
Nodes (37): ClassImportReport, ClassImportRow, question_warnings(), QuestionImportReport, QuestionImportRow, QuizQuestionCreate, All-or-nothing: any invalid row means nothing is imported., All-or-nothing: any invalid row means nothing is imported; duplicates are… (+29 more)

### Community 36 - "test_quiz_timer.py"
Cohesion: 0.10
Nodes (36): _get(), _mesh_answer(), pause_scheduler(), idle(), _per_question(), fixture, parametrize, #73: timed quizzes advance (per_question) and end (total) by themselves, the… (+28 more)

### Community 37 - "pathlib"
Cohesion: 0.07
Nodes (31): v2.2: strings from a radio frame are not trusted to be NUL-terminated. The…, _kconfig_default(), The hub fetches its own updates from BACKEND_HOST (class_s3), so its default…, _sdkconfig(), test_hub_and_gateway_default_to_the_same_server(), json, os, pathlib (+23 more)

### Community 38 - "db"
Cohesion: 0.07
Nodes (38): go(), go(), go(), profile(), lifespan(), Create tables and seed a default super admin on startup., banner(), _boot_password() (+30 more)

### Community 39 - "ui.js"
Cohesion: 0.08
Nodes (28): Actions, afterShell(), avatar(), brandMark(), CALLABLE, callAttr(), COMMON_PASSWORDS, CRUMBS (+20 more)

### Community 40 - "class_s3/main/ota.c"
Cohesion: 0.08
Nodes (32): esp_chip_info, esp_crt_bundle, esp_flash, esp_netif, esp_ota_ops, esp_psram, esp_system, esp_websocket_client (+24 more)

### Community 41 - "test_hardening.py"
Cohesion: 0.07
Nodes (33): Problems in a chain file; empty when it is intact from the first line., verify_file(), approved(), Dual control (v2.2): request `action`, have it approved (by `approver` headers,…, v2.2 hardening: dual control, the policy view, the external audit trail,…, test_a_dangerous_action_needs_an_approval(), test_a_reset_keeps_recent_audit_entries(), test_an_approval_is_for_one_action_only() (+25 more)

### Community 42 - "test_device_batch_dedup.py"
Cohesion: 0.10
Nodes (34): A keyed, one-way reference to a student for audit entries that must outlive the…, student_ref(), answer(), batch(), count(), q(), parametrize, #6: /api/device/batch validates and de-duplicates mesh answers/votes. (+26 more)

### Community 43 - "stdint"
Cohesion: 0.10
Nodes (9): esp_err, esp_event, esp_idf_version, esp_transport_ws, protocol, socket, stdbool, stddef (+1 more)

### Community 44 - "test_qualification.py"
Cohesion: 0.12
Nodes (32): attest(), attested(), What the report is about: the exact bytes and the build that made them., Made by this server's TrustedInstaller, by the current stages, for exactly this…, _seal(), subject(), _artifact(), _excluded() (+24 more)

### Community 45 - "services/backups.py"
Cohesion: 0.13
Nodes (31): delete_backup(), describe_backup(), _err(), list_backups(), AsyncSession, BaseModel, get, HTTPException (+23 more)

### Community 46 - ".update"
Cohesion: 0.06
Nodes (25): Gateway, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent…, age(), go(), _set_firmware_version() (+17 more)

### Community 47 - "test_spi_slave.c"
Cohesion: 0.11
Nodes (31): config, esp_err_t, spi_slave_transaction_t, queue_slot(), spi_post_trans_cb(), spi_slave_init(), esp_random(), SemaphoreHandle_t (+23 more)

### Community 48 - "on_ws_command"
Cohesion: 0.10
Nodes (29): ctype, handle_class_assignment(), on_ws_command(), cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches() (+21 more)

### Community 49 - "test_release.py"
Cohesion: 0.06
Nodes (6): release, _ancestry(), fixture, Releases (#96, #100, #104): owner-prefixed names, patch numbers per push, the…, A fake git: `older` is an ancestor of `newer` when (older, newer) is listed., wf()

### Community 50 - "migrations.py"
Cohesion: 0.12
Nodes (30): AsyncConnection, add_account_and_class_fields(), _add_columns(), add_deployment_deferral(), add_device_caps(), add_device_keys(), add_diagnostics_columns(), add_firmware_qualification() (+22 more)

### Community 51 - "app/gpc.py"
Cohesion: 0.13
Nodes (30): at_least_as_safe(), build(), changed_on_disk(), check_signed_file(), coerce(), current(), enforce_startup(), Flag (+22 more)

### Community 52 - "wifi_client.c"
Cohesion: 0.12
Nodes (27): adc_oneshot, backend_fail_t, errno, esp_event_base_t, esp_heap_caps, heartbeat_task(), _battery_pct(), _check_auth() (+19 more)

### Community 53 - "test_db_gateway.py"
Cohesion: 0.12
Nodes (28): DatabaseWriteRefused, Exception, _db_file(), _first_user(), _load(), _outside(), parametrize, v2.2 database gateway: per-table write rules, row seals, verification,… (+20 more)

### Community 54 - "api.js"
Cohesion: 0.09
Nodes (21): adminApi, apiRequest(), approvalsApi, authApi, classesApi, ClassSocket, clearToken(), coursesApi (+13 more)

### Community 55 - "tests/test_deployments.py"
Cohesion: 0.23
Nodes (29): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+21 more)

### Community 56 - "firmware/tests/test_classroom_sim.py"
Cohesion: 0.08
Nodes (19): parametrize, v2.2: classroom protocol simulation (firmware/sim/classroom_sim.py). The frame,…, Boundary: the hub holds 63 frames (64-entry ring, one slot free). All 300…, Resends of an answer the hub already queued are duplicates. In a full room the…, The answers run_quiz sends, recomputed from the same seed., A hub without #181 (or MESH_ANSWER_ACK off): the module sends its answer once…, Before #182: both ends drop a slot once clocked, so a slot that fails its CRC…, #182: spi_link.c on both ends. A third of the slots in each direction fail… (+11 more)

### Community 57 - "run_tests.py"
Cohesion: 0.12
Nodes (27): CaseResult, _idf_command(), _idf_image_present(), _missing(), missing_packages(), parse_coverage(), parse_host_output(), parse_junit() (+19 more)

### Community 58 - "cJSON_bool"
Cohesion: 0.17
Nodes (28): buffer_skip_whitespace(), cJSON_bool, cJSON_Compare(), cJSON_ParseWithLength(), cJSON_ParseWithLengthOpts(), cJSON_ParseWithOpts(), cJSON_PrintPreallocated(), compare_double() (+20 more)

### Community 59 - "ota_chunk.c"
Cohesion: 0.18
Nodes (26): advance(), ota_rx_t, has(), ota_chunk_count(), ota_chunk_len(), ota_rx_accept(), ota_rx_complete(), ota_rx_init() (+18 more)

### Community 60 - "services/approvals.py"
Cohesion: 0.15
Nodes (26): Approval, A request for a dangerous action that a second super admin must approve (policy…, approve(), deny(), list_requests(), NewRequest, Password, AsyncSession (+18 more)

### Community 61 - "test_question_import.py"
Cohesion: 0.18
Nodes (25): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+17 more)

### Community 62 - "string"
Cohesion: 0.13
Nodes (19): assert, read_file(), main(), mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main() (+11 more)

### Community 63 - "UserSession"
Cohesion: 0.11
Nodes (20): _sha256_hex(), Older versions stored the raw bearer token in user_sessions.session_token. Any…, _scrub_raw_session_tokens(), Touch last_activity_at for live user sessions on each API request. Best-effort…, refresh_session_activity(), UserSession, offer: what /firmware/check returns; fetch(): the downloaded bytes., call() (+12 more)

### Community 64 - "screenshots.py"
Cohesion: 0.11
Nodes (17): ansi_to_svg(), Api, free_port(), main(), Path, Regenerate the pictures in docs/images from a throw-away demo server. pip…, root_screen(), run_server() (+9 more)

### Community 65 - "test_ci_workflow.py"
Cohesion: 0.12
Nodes (17): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+9 more)

### Community 66 - "traffic.py"
Cohesion: 0.13
Nodes (24): alerts(), _flag(), kind_of(), label(), _persist(), _prune(), Traffic monitor (v2.2): notices unusual request rates and tells administrators.…, 0-100 from this account's recent behaviour; `reasons` explains every point. (+16 more)

### Community 67 - "test_quiz_poll_lifecycle.py"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 68 - "test_core_utils.py"
Cohesion: 0.13
Nodes (23): _parse_time(), Convert "HH:MM" → minutes since midnight. Returns None if malformed., Two time slots overlap when neither fully precedes the other. Overnight / wrap-…, _slots_conflict(), normalize_version(), as_ist(), ist_iso(), istnow_aware() (+15 more)

### Community 69 - "test_policy.py"
Cohesion: 0.11
Nodes (20): routes(), _calls(), The authorization policy is the one place that decides access (#122)., A staff route without a policy permission is a new hole; device routes…, Role checks scattered across routers drifted before (#19-#21, #116, #121)., docs/design/authorization.md shows GRANTS; it must not drift., _routes(), test_every_route_is_governed_by_the_policy_or_listed() (+12 more)

### Community 70 - "ed25519.py"
Cohesion: 0.19
Nodes (21): _add(), _compress(), _decompress(), _equal(), _expand(), generate_seed(), _h(), _inv() (+13 more)

### Community 71 - "load"
Cohesion: 0.24
Nodes (21): load(), Compute the policy from the settings and the signed file, and make it the…, _doc(), _files(), _no_state(), fixture, parametrize, Global policy control: defaults per profile, the root-signed file, inline… (+13 more)

### Community 72 - "presence"
Cohesion: 0.10
Nodes (21): database_principal(), Count the request for the traffic monitor (it flags and alerts, it never…, Every request starts as anonymous for the database gateway (v2.2); signing in…, traffic_monitor(), presence(), Who is signed in and active right now, and who was active lately (admins and…, Containers, Locked until verified (+13 more)

### Community 73 - "testdata.js"
Cohesion: 0.26
Nodes (22): parseDelimited(), renderTestData(), TD, tdCell(), tdCols(), tdCopy(), tdEdit(), tdEnsureRows() (+14 more)

### Community 74 - "test_console_v22.py"
Cohesion: 0.17
Nodes (21): box(), The root console and the launch flags, run the way root runs them: as separate…, _seed_default(), test_backups_from_the_console(), test_classes_students_and_courses_from_the_shell(), test_creating_accounts_and_the_pending_setup_state(), test_features_are_switched_as_root_and_can_be_locked(), test_help_is_grouped_and_familiar_names_work() (+13 more)

### Community 75 - ".fail"
Cohesion: 0.14
Nodes (8): api METHOD PATH [JSON]: call any of the application's routes as a super admin,…, classes list | show ID | create NAME CODE [--teacher USER] [--room R] [--icon…, students list [TEXT] | add ROLL NAME [--email E] | delete ID | enroll ID…, courses list | add CODE NAME | delete ID, devices list | show ID: gateways, hubs and student modules, firmware list | approve ID | deprecate ID | delete ID, and: firmware…, approvals list | deny ID: requests that need a second super admin (approving…, verify: check the database's integrity now (the same as System, Verify now)

### Community 76 - "auditsink.py"
Cohesion: 0.12
Nodes (21): describe(), clear_options(), csp_report(), event_stream(), policy_view(), get, Request, Read-only: nothing in the web app or the API changes the policy. (+13 more)

### Community 77 - "ConnectionManager"
Cohesion: 0.10
Nodes (11): ConnectionManager, WebSocket, Send a JSON message to ALL connections in a class room (teachers + devices)., Send a JSON message only to connections matching the given role., Alias for broadcast_to_class., Manages WebSocket connections grouped by class ID. Teachers connect to manage…, Close every socket of a user whose access was revoked (#118)., FakeWS (+3 more)

### Community 78 - "test_firmware_registry.py"
Cohesion: 0.15
Nodes (19): make_image(), _count(), q(), parametrize, #35: uploaded firmware is validated as a real imPress image and registered…, Against genuine ESP-IDF output when a local build exists (the synthetic images…, A scripts/build_signed.sh build (#66), when one exists locally., test_a_c6_image_is_never_pushed_to_an_s3() (+11 more)

### Community 79 - "firmware"
Cohesion: 0.14
Nodes (15): CDLL, _buf(), decode(), firmware(), Hub, _Msg, A C byte array: `data` zero bytes, or a copy of `data`., (type, payload) of a valid frame, else None (bad start, length or CRC). (+7 more)

### Community 80 - "test_spi_link.c"
Cohesion: 0.28
Nodes (20): spi_link_drop_head(), spi_link_init(), spi_link_rx(), spi_link_tx(), trailers(), build(), exchange(), got_all_once() (+12 more)

### Community 81 - "Screen"
Cohesion: 0.18
Nodes (8): Break a coloured line at `width` terminal cells; ANSI styles cost no width., Screen, wrap_ansi(), test_root_screen_keeps_scrollable_log_history(), In a container, The console, The root console and the root screen, The root screen

### Community 82 - "qualification.py"
Cohesion: 0.14
Nodes (18): analysis(), bootloader_checks(), _Device, emulator(), _inside(), _key(), ota_client(), qualify() (+10 more)

### Community 83 - "test_schedule_occupancy.py"
Cohesion: 0.17
Nodes (18): _add(), _busy(), phy(), fixture, parametrize, Dated timetable changes and room occupancy (#126). 2026-10-12 is a Monday,…, su(), test_a_cancelled_day_frees_every_slot() (+10 more)

### Community 84 - "console.md"
Cohesion: 0.12
Nodes (10): Backups, restore and resetting the system, Resetting the system, Restoring, What a backup is, Before you begin, Install imPress on a server, Linux and macOS, Next steps (+2 more)

### Community 85 - "signing.py"
Cohesion: 0.21
Nodes (19): app_dir(), build_manifest(), _canonical(), collect(), _export_seed(), _key_path(), Path, Signatures the server produces and checks (v2.2), all Ed25519. * **Code… (+11 more)

### Community 86 - "dashboard.js"
Cohesion: 0.18
Nodes (16): Charts, Dash, dashboardData(), DEFAULT_LAYOUT, drawWidgets(), greeting(), layoutFor(), openWidgetGallery() (+8 more)

### Community 87 - "calls"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 88 - "functions"
Cohesion: 0.15
Nodes (16): functions(), {name: body_text} for every top-level function definition in a C file., #7: the S3 loads its config before the mesh uses g_cfg.mesh_channel, and a…, test_config_loaded_before_mesh_init(), test_config_loader_initialises_nvs_itself(), test_mesh_init_reads_channel_from_config(), test_set_channel_result_checked_on_s3_and_student(), #13: S3 OTA — rollback protection and no reboot when nothing is installed. (+8 more)

### Community 89 - "test_run_tests.py"
Cohesion: 0.14
Nodes (17): posix_only, discover(), Run `cmd` and return (exit code, combined output, abort reason). Output is read…, run_streaming(), skipif, Unit tests for the root test runner (run_tests.py)., test_closed_output_pipe_exits_quietly(), test_ctrl_c_stops_the_whole_process_group() (+9 more)

### Community 90 - "test_secure_defaults.py"
Cohesion: 0.15
Nodes (14): check_secure(), insecure_settings(), Names of settings still at their public, repo-published defaults., Refuse to run with published secrets, or with unauthenticated WebSockets…, Settings, _reset_db(), _fresh_settings(), #11: no working public credentials or debug leaks by default. (+6 more)

### Community 91 - "services/features.py"
Cohesion: 0.20
Nodes (18): FeatureFlag, PolicyLog, A feature an administrator can switch on or off at run time…, Who changed which policy or feature, when, and from what to what…, describe(), Feature, history(), load() (+10 more)

### Community 92 - "iips.py"
Cohesion: 0.22
Nodes (18): baseline_path(), check(), compare(), _files(), _key(), Path, imPress Integrity Protection Service (IIPS, v2.2): the program's own files are…, Run at start-up. Sets and returns the state: ok | baseline_created | violation… (+10 more)

### Community 93 - "test_device_api.py"
Cohesion: 0.22
Nodes (17): _activity(), q(), _device(), q(), Gateway-facing device API (routers/device.py) + presence service…, _register(), test_class_presence_snapshot_walks_gateway_tree(), test_firmware_check_and_applied_cycle() (+9 more)

### Community 94 - "test_device_keys.py"
Cohesion: 0.28
Nodes (18): _beat(), _device(), q(), _key(), #66: per-device keys. Devices register with the shared key and are issued their…, _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out() (+10 more)

### Community 95 - "test_migrations.py"
Cohesion: 0.25
Nodes (15): _all_versions(), _backups(), _indexes(), _legacy_db(), _migrate(), _model_unique_indexes(), _q(), #41: versioned migrations adopt old databases safely and atomically. (+7 more)

### Community 96 - "test_super_admin_lockout.py"
Cohesion: 0.15
Nodes (17): _me(), fixture, parametrize, At least one active super admin always remains (#116). The original failure: a…, The original lockout path: PUT with is_active=false on yourself (#116, #119)., Two super admins disabling each other at the same moment: one must fail., su(), test_concurrent_mutual_deactivation_leaves_one_super_admin() (+9 more)

### Community 97 - "classroom_sim.py"
Cohesion: 0.16
Nodes (15): ctypes, dataclasses, _AnswerTx, _boot_link(), main(), Radio, Classroom protocol simulator: student modules -> S3 hub -> C6 gateway (v2.2).…, ESP-NOW broadcast between the modules and the hub: no MAC-level… (+7 more)

### Community 98 - "msg_to_json"
Cohesion: 0.25
Nodes (15): msg_type_t, msg_to_json(), student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join() (+7 more)

### Community 99 - "ui_tests/conftest.py"
Cohesion: 0.13
Nodes (13): Api, browser(), _free_port(), page(), fixture, Browser UI checks: a real backend on a temp database, driven by Playwright.…, A page that fails the test on any uncaught JS error; screenshot at the end., Tiny JSON client for setting up data the test then checks in the UI. (+5 more)

### Community 100 - "login"
Cohesion: 0.19
Nodes (16): login(), #51: only the latest navigation renders., test_normal_navigation_and_in_page_rerender_still_work(), test_quick_navigation_is_not_overwritten_by_a_slower_page(), #73: the class page offers Next for every timing mode, and a quiz the server's…, test_timed_quiz_has_next_and_ends_on_the_timer(), _confirm(), Account lifecycle in the admin UI (#117, #119): buttons follow the server's… (+8 more)

### Community 101 - "test_manage_cli.py"
Cohesion: 0.18
Nodes (14): init_db(), Create missing tables and apply pending migrations (stops on failure)., main(), Server-side maintenance commands, run on the host that has the database (#120).…, Returns the new password. Raises LookupError for an unknown username., restore_super_admin(), _lock_out(), Offline recovery of a locked-out installation (#120). (+6 more)

### Community 102 - "events.py"
Cohesion: 0.16
Nodes (15): _sse(), stream_events(), changed(), _deliver(), _flush(), Server events for the web app (v2.2): one in-process publish/subscribe. Every…, One person's open pages only (e.g. their account was disabled)., Data in these tables changed (called after a commit). (+7 more)

### Community 103 - "test_fault_injection.py"
Cohesion: 0.17
Nodes (10): answer(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, #43 fault injection on the answer path: what the gateway's retry rules (keep a…, _stored(), q(), test_a_failed_commit_stores_nothing_and_the_retry_stores_once(), test_a_lost_response_makes_the_gateway_resend_harmlessly(), test_answers_buffered_while_offline_count_only_if_the_quiz_is_still_open() (+2 more)

### Community 104 - "production-hardening.md"
Cohesion: 0.19
Nodes (10): Data inventory, Things to check, Privacy and compliance toolkit, Roles to decide first, What imPress does for you, and what it does not, Erasure and backups, Legal holds, Retention schedule (+2 more)

### Community 105 - "test_backend_contract_fixture"
Cohesion: 0.17
Nodes (17): cJSON_Minify(), cJSON_Parse(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), minify_string(), skip_multiline_comment(), skip_oneline_comment() (+9 more)

### Community 106 - "scripts/gpc.py"
Cohesion: 0.20
Nodes (14): app, base64, cmd_flags(), cmd_keygen(), cmd_manifest(), cmd_show(), cmd_sign(), cmd_verify() (+6 more)

### Community 107 - "Console"
Cohesion: 0.15
Nodes (5): Console, password show | reset [--password P]: the default super admin's password.…, quizzes list | start ID | stop ID, and: polls list | start ID | end ID, clear: clear the screen., exit: leave the console.

### Community 108 - ".say"
Cohesion: 0.13
Nodes (8): kv(), status: the state of the system: version, profile, database, super admins,…, version: the imPress version., audit verify FILE: check an external audit trail's hash chain., testmode status: whether test mode is on, forced by root, or not allowed., iips status | rehash: imPress Integrity Protection. 'rehash' makes the…, date: the server's time (Indian Standard Time), help [COMMAND]: the commands, or how to use one

### Community 109 - "boot_verify.py"
Cohesion: 0.17
Nodes (16): locked_down(), TrustedInstaller has not verified the host (or found it unable to run imPress):…, requirements(), _check(), _data_dir(), in_container(), inspect(), locked() (+8 more)

### Community 110 - "data-integrity.md"
Cohesion: 0.15
Nodes (11): At every start, imPress Integrity Protection Service (IIPS), Limits, Root's choices, What it records, Global policy, Launch flags, Launch flags, features and the global policy (+3 more)

### Community 111 - "playwright_sync_api"
Cohesion: 0.12
Nodes (12): playwright_sync_api, _mac(), #38/#34: a staged OTA rollout from the Firmware page., test_preview_start_progress_pause_and_resume(), Separate firmware views per device family (#131)., test_tabs_show_one_family_with_its_rules(), Schedule changes on the class page (#126)., test_record_and_remove_a_cancelled_class() (+4 more)

### Community 112 - "sys"
Cohesion: 0.19
Nodes (14): ArgumentParser, lines(), The imPress mark and version, printed when the server and the root console…, The mark and the root screen use box-drawing characters: a Windows console that…, show(), utf8_output(), build_parser(), main() (+6 more)

### Community 113 - "test_c6_diagnostics.py"
Cohesion: 0.15
Nodes (9): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat() (+1 more)

### Community 114 - "test_login_throttle.py"
Cohesion: 0.18
Nodes (15): clock(), fixture, parametrize, Password guessing is slowed; new passwords resist trivial guesses (#153)., test_another_username_is_not_affected(), test_counters_survive_a_restart(), test_existing_passwords_keep_working(), test_one_address_guessing_many_usernames_is_slowed() (+7 more)

### Community 115 - "test_trusted_installer.py"
Cohesion: 0.24
Nodes (14): _artifact(), _deploy(), _download(), fixture, TrustedInstaller (#123): firmware reaches a device only after its own checks,…, The production defaults: no unsigned images, no self-approval., _register(), strict() (+6 more)

### Community 116 - "test_graphify.py"
Cohesion: 0.15
Nodes (10): _publish_graph_visualization(), Sphinx configuration for the public imPress documentation site., Expose the generated graph beneath the hosted ``/graph/`` page., setup(), shutil, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards() (+2 more)

### Community 117 - "test_docs_consistency.py"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 118 - "FakeGitHub"
Cohesion: 0.23
Nodes (13): release(), FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1() (+5 more)

### Community 119 - "._args"
Cohesion: 0.17
Nodes (8): _opts(), users list [--role R] | show USER | create USER --role admin|teacher [--name N]…, superadmin create USER [--name N] [--email E] [--password P] The only way to…, system reset --confirm "RESET EVERYTHING": clear everything and start over (a…, feature NAME on|off [--lock]: switch a feature as root. Root outranks…, (positional, {name: value}) from a simple --name value / --flag command line., activity [N] [--flagged]: the latest entries of the activity log, ls [users|classes|students|courses|devices]: list things (users by default)

### Community 120 - "_write_refused"
Cohesion: 0.15
Nodes (15): _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), health(), get, Request (+7 more)

### Community 121 - "rootscreen.py"
Cohesion: 0.22
Nodes (12): c(), _cell_width(), _fit_ansi(), The root screen (v2.2): what root sees when imPress is started from a terminal…, Clip a line to terminal cells, not Python characters, without counting ANSI…, Colour a log line by its level; access-log lines are quiet., run(), pump() (+4 more)

### Community 122 - "create_poll"
Cohesion: 0.28
Nodes (15): create_poll(), end_poll(), get_poll(), list_polls(), _poll_response(), poll_results(), AsyncSession, get (+7 more)

### Community 123 - "test_iips.py"
Cohesion: 0.20
Nodes (14): locked(), violation_message(), _check(), fixture, parametrize, IIPS: the program's own files are hashed at first start and checked at every…, test_a_hand_edited_baseline_does_not_help(), test_any_difference_disables() (+6 more)

### Community 124 - "upload_firmware"
Cohesion: 0.35
Nodes (14): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), _artifact(), _hub(), _push(), #36: firmware version manager: approval, deprecation, retention, usage., _set(), test_admin_only() (+6 more)

### Community 125 - "test_ota_download_gating.py"
Cohesion: 0.20
Nodes (13): _marker(), _next_command(), #43 end to end: a teacher runs a quiz in a room, and the answers arrive through…, Frames the socket got before a marker broadcast now (so a missing frame fails…, The next frame ws_command.c acts on: it dispatches on "event" and ignores the…, test_a_quiz_runs_end_to_end_through_a_gateway(), device(), dl() (+5 more)

### Community 126 - "test_ota_results.py"
Cohesion: 0.30
Nodes (14): _device(), q(), _push(), parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report(), test_applied_with_another_version_is_not_success(), test_applied_with_the_pushed_version_completes_the_update() (+6 more)

### Community 127 - "test_session_cookie.py"
Cohesion: 0.24
Nodes (13): _browser_login(), v2.2: the browser's session lives in an HttpOnly cookie, never in page storage…, test_bearer_clients_need_no_csrf_header(), test_cookie_authenticates_reads(), test_cookie_change_with_csrf_header_allowed(), test_cookie_change_without_csrf_header_refused(), test_cross_site_socket_refused(), test_login_sets_httponly_strict_cookie() (+5 more)

### Community 128 - "test_sessions_v22.py"
Cohesion: 0.22
Nodes (14): _age_sessions(), v2.2 session rules: 5-minute idle limit (30 for faculty in class), one device…, test_a_second_device_is_refused_and_flagged(), flagged(), test_a_teacher_outside_class_has_five_minutes(), test_a_timetable_slot_counts_as_class_time(), test_after_sign_out_or_timeout_another_device_may_sign_in(), test_an_admin_can_end_a_users_sessions() (+6 more)

### Community 129 - "test_spi_link.py"
Cohesion: 0.15
Nodes (11): #29: guards for the S3 <-> C6 link as ported from v3…, _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_flushes_bounded_chunks_and_keeps_them_on_transport_errors(), test_c6_student_count_comes_from_join_and_leave_only(), test_c6_validates_received_slots(), test_master_drops_a_payload_only_after_a_successful_transfer(), test_s3_heartbeat_record_is_not_copied_onto_itself() (+3 more)

### Community 130 - "tests/conftest.py"
Cohesion: 0.20
Nodes (11): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+3 more)

### Community 131 - "throttle.py"
Cohesion: 0.26
Nodes (13): LoginThrottle, Failed password attempts per key: user:<name>, ip:<address>, change:<user id>., check(), failed(), _free(), prune(), AsyncSession, datetime (+5 more)

### Community 132 - "Test mode and test data"
Cohesion: 0.14
Nodes (12): inactive (deactivated) | pending_setup (temporary credentials, never signed in)…, What the interface calls this person., computed_field, Check and import, Forced by root (`--test-mode`), Lifecycle, Notes, Safety rules and policy (+4 more)

### Community 133 - "test_results_enrolled_only.py"
Cohesion: 0.31
Nodes (12): _answer(), _batch(), _enrol(), _notices(), fixture, #186: a class with a roster counts only its enrolled students; the teacher is…, room(), test_a_class_without_a_roster_counts_everyone() (+4 more)

### Community 134 - "test_role_escalation.py"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10, #119: only a super admin can grant/remove admin-level roles; roles are a…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 135 - "test_transport.py"
Cohesion: 0.16
Nodes (9): _https(), fixture, HTTPS for staff traffic and browser security headers (#152)., uvicorn turns X-Forwarded-Proto from a trusted proxy into the scheme; the test…, strict(), test_a_reverse_proxy_counts_as_https(), test_https_works_and_gets_hsts(), test_teacher_socket_needs_wss() (+1 more)

### Community 136 - "v2.2.md"
Cohesion: 0.14
Nodes (13): 1. Start the server, 2. Log in, 3. Prepare the devices, Check the installation, Downloads, First use, Help and documentation, Install and set up (+5 more)

### Community 137 - "migrate"
Cohesion: 0.21
Nodes (11): AsyncEngine, as_system, `with as_system():` the server's own housekeeping inside a request (reading the…, _applied(), backup(), _db_file(), migrate(), Path (+3 more)

### Community 138 - "finish_setup"
Cohesion: 0.15
Nodes (12): client(), post(), run(), go(), _drain_background_tasks(), finish_setup(), go(), policy() (+4 more)

### Community 139 - "test_db_integrity.py"
Cohesion: 0.21
Nodes (12): _insert_twice(), fixture, #41: the database enforces its own integrity (foreign keys, uniqueness), and…, A class with a quiz, a poll, an enrolled student who answered and voted over…, test_one_answer_per_device_and_question(), dev(), test_one_answer_per_student_and_question(), test_one_enrollment_per_student_and_class() (+4 more)

### Community 140 - "strip_comments_and_strings"
Cohesion: 0.19
Nodes (8): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, #132: both backend clients classify a failure and log the hint, and the boot…, #129: both registrations append the caps object from device_caps.h., test_connection_failures_say_why(), test_every_backend_client_gets_the_tls_settings(), test_gateway_and_hub_report_their_capabilities(), test_version_comes_from_the_image()

### Community 141 - "test_health.py"
Cohesion: 0.26
Nodes (10): health(), datetime, Device health states (#39), computed from the latest heartbeat. Rules, in order…, (state, reasons) for one device., _dev(), parametrize, #39: device health states from the latest heartbeat diagnostics., test_invalid_diagnostics_are_rejected() (+2 more)

### Community 142 - "mesh_bridge.py"
Cohesion: 0.17
Nodes (11): push_device_status(), push_poll_to_mesh(), push_quiz_to_mesh(), push_student_data(), Bridge service: connects ESP device data to WebSocket clients. This service…, Push student device data (heartbeats, answers, votes) to teacher dashboard., Push individual device status update., Send a command to C6 devices connected via WebSocket. (+3 more)

### Community 143 - "settings.js"
Cohesion: 0.29
Nodes (9): renderSettings(), rerenderSettings(), SECTIONS, seg(), sel(), setRow(), settingsSections(), sw() (+1 more)

### Community 144 - "test_e2e_ota.py"
Cohesion: 0.44
Nodes (11): _advance(), _dep(), _deploy(), _prompt(), #43 end to end: a firmware release reaches three rooms through the staged…, Read this room's socket until the gateway's own OTA prompt., _sockets(), test_an_unhealthy_image_rolls_back_and_stops_the_rollout() (+3 more)

### Community 145 - "Mesh frame authentication (design, proposed)"
Cohesion: 0.17
Nodes (11): Cost, Decisions needed, Frame, Getting the keys where they belong, Keys, Mesh frame authentication (design, proposed), Migration, Proposed design (+3 more)

### Community 146 - "launcher.sh"
Cohesion: 0.35
Nodes (11): confirm(), die(), ensure_port_free(), find_python(), IMPRESS_HOST, IMPRESS_PORT, ok_python(), pids_on_port() (+3 more)

### Community 147 - "test_motion.py"
Cohesion: 0.32
Nodes (11): MOTION, _anim(), v2.2: the motion is there, plays when the route changes, never replays on a…, The route's entry has played and ended (it is set when the page has rendered,…, _settled(), test_a_background_refresh_never_replays_it(), test_a_route_change_plays_the_entry_and_then_settles(), test_buttons_press_and_morph() (+3 more)

### Community 148 - "main"
Cohesion: 0.26
Nodes (8): fmt_secs(), main(), markdown_report(), Paint, print_report(), SuiteResult, test_coverage_report_is_parsed_and_shown(), test_markdown_report_lists_every_suite()

### Community 149 - "system.js"
Cohesion: 0.31
Nodes (10): backupsTab(), featuresTab(), policyCard(), RANK_TEXT, renderSystem(), requirementsTab(), securityTab(), systemTab() (+2 more)

### Community 150 - "spi_to_http_task"
Cohesion: 0.33
Nodes (11): cJSON, batch_add(), batch_flush(), batch_flush_needed(), item_is_heartbeat(), process_spi_payload(), spi_to_http_task(), status_ping_task() (+3 more)

### Community 151 - "v2.2 plan and engineering record"
Cohesion: 0.18
Nodes (9): Audit findings, Communication paths and their trust boundaries, Hardware testing (Kush), Migration from v2.1, Phase 0: branch and ESP32 integration, Remaining for 2.2, Simulation and emulation: what is feasible, v2.2 plan and engineering record (+1 more)

### Community 152 - "Personalization, accessibility, search and the dashboard"
Cohesion: 0.18
Nodes (10): Accessibility, Advanced mode (administrators), Appearance, Date, time and numbers, Notices that cover the page, Notifications, Personalization, accessibility, search and the dashboard, Search and quick settings (+2 more)

### Community 153 - "c_source.py"
Cohesion: 0.18
Nodes (4): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #66: the signed-app profile and the scripts that build with it.

### Community 154 - "test_install_scripts.py"
Cohesion: 0.33
Nodes (8): stat, _backend(), #42: the documented install path: scripts, secrets, version, CI job., test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets(), _values()

### Community 155 - ".run"
Cohesion: 0.20
Nodes (4): deadlock check: run global_deadlock_prevention now (rolls back and creates a…, features: every feature, whether it is on, and who set it last (administrators,…, policylog [FLAG]: who changed which policy or feature, and when., uptime: how long the server has been running, and how many sessions are open

### Community 156 - "account_refusal"
Cohesion: 0.24
Nodes (10): account_refusal(), feature(), dependency(), forbidden(), HTTPException, Route dependency: refuse with 403 when root switched the feature off (a policy…, Why `actor` may not do `action` to `target`'s account, or None. Actions: edit,…, dependency() (+2 more)

### Community 157 - "ClassCreate"
Cohesion: 0.29
Nodes (4): ClassCreate, ClassUpdate, Editable scheduling fields for an existing class (hybrid scheduling)., field_validator

### Community 158 - "test_gateway_autolink.py"
Cohesion: 0.42
Nodes (9): _class(), _gateway_of(), q(), #17: registration must not steal a class's gateway link., _register(), test_explicit_classroom_code_still_assigns(), test_gateway_keeps_its_class_on_reregister(), test_non_gateway_registration_keeps_class_gateway() (+1 more)

### Community 159 - "test_quiz_correct_option.py"
Cohesion: 0.29
Nodes (8): _create(), ctx(), fixture, parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 160 - "Data integrity: the database gateway, seals and self-repair"
Cohesion: 0.20
Nodes (10): 1. Every write goes through the gateway, 2. Seals: detecting changes made outside imPress, 3. Temporary backups and self-repair, 4. Clearing, resetting and accepting a changed database, 5. Where it shows up in the app, 6. Limits, Data integrity: the database gateway, seals and self-repair, Dual control (+2 more)

### Community 161 - "Accounts, first sign-in and the default super admin"
Cohesion: 0.20
Nodes (10): Accounts, first sign-in and the default super admin, Active accounts, disabling and the trash, Creating an account, Global deadlock prevention, Names, Roles and designations, Sessions, The default super admin (+2 more)

### Community 162 - "Personalization, accessibility, search and the dashboard"
Cohesion: 0.20
Nodes (10): Accessibility, Advanced mode (administrators), Appearance, Date, time and numbers, Notices that cover the page, Notifications, Personalization, accessibility, search and the dashboard, Search and quick settings (+2 more)

### Community 163 - "Student"
Cohesion: 0.27
Nodes (7): encode(), _enroll(), poll_vote(), quiz_answer(), A student module: buttons A-D pick an option; the answer is sent once…, Student, student_join()

### Community 164 - "qemu_boot.py"
Cohesion: 0.24
Nodes (9): glob, find_qemu(), judge(), main(), Boot a firmware image in Espressif's QEMU and judge the serial log (#154).…, (passed, reason) for a captured log., tempfile, threading (+1 more)

### Community 165 - "table"
Cohesion: 0.22
Nodes (5): backup list | save NAME | restore ID --yes: the backups (see 'list' for ids…, policy show: the effective global policy (flags, values and where each came…, requirements: what TrustedInstaller checks on this host (system, memory, disk,…, env: the settings imPress runs with (secrets are hidden), table()

### Community 166 - "Frequently asked questions"
Cohesion: 0.22
Nodes (9): A device is registered but offline, A migration failed or an upgrade changed the database, A teacher cannot see a class, Can student modules receive OTA updates?, Frequently asked questions, I can open the page locally but another computer cannot sign in, The first admin password is not in the browser, Where should I report a problem? (+1 more)

### Community 167 - "test_c6_ota.py"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 168 - "_repo"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 169 - "test_upgrade_integrity.py"
Cohesion: 0.43
Nodes (7): app_services, _db(), _outside(), An upgrade changes the schema (new columns change every row's seal): that is…, test_a_backup_from_an_older_schema_is_upgraded_when_restored(), test_a_database_that_changed_during_an_upgrade_is_resealed_not_restored(), test_the_same_change_without_an_upgrade_is_still_tampering()

### Community 170 - "key_id"
Cohesion: 0.25
Nodes (8): key_id(), Short, stable name of a public key (first 16 hex digits of its SHA-256)., canonical(), What `scripts/gpc.py sign` writes: the policy plus root's signature., sign_document(), Public: the key that verifies the server's signed exports…, signing_key(), export_public_key()

### Community 171 - "system_status"
Cohesion: 0.29
Nodes (8): AsyncSession, system_status(), enabled(), Route dependency: 403 when the feature is switched off., Is the feature on? (the web app asks this through /api/system/status; routes…, require_feature(), dependency(), snapshot()

### Community 172 - "prefs.py"
Cohesion: 0.46
Nodes (7): _choice(), PreferenceError, ValueError, A user's saved preferences (v2.2): personalization, accessibility, advanced…, The cleaned subset of `changes` (unknown keys are an error). Advanced mode is…, validate(), _widgets()

### Community 173 - "shell.js"
Cohesion: 0.25
Nodes (4): Help, Overlays, Palette, ROLE_TITLES

### Community 174 - "test_query_cascade.py"
Cohesion: 0.39
Nodes (6): _history(), Loading a user or a class list must not pull in the teaching history (#133).…, statements(), test_class_list_counts_without_loading_quizzes(), test_loading_a_user_is_one_statement(), load()

### Community 175 - "Web app design and motion"
Cohesion: 0.25
Nodes (7): Adding to it, Principles, Rules that keep it from glitching, The springs, The v2.2 refinement, Web app design and motion, What moves

### Community 176 - "Production hardening checklist"
Cohesion: 0.25
Nodes (8): 1. Secrets and HTTPS, 2. Root key and the signed policy, 3. An audit trail the application cannot rewrite, 4. Signed firmware and device TLS, 5. Backups you can restore, 6. Start hardened, then check, Production hardening checklist, Roles to settle before go-live

### Community 177 - "mentions"
Cohesion: 0.43
Nodes (7): mentions(), #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch(), test_c6_services_spi_while_wifi_is_down_with_a_bounded_batch()

### Community 179 - "_requirements"
Cohesion: 0.25
Nodes (8): _marker_applies(), False for a requirement whose environment marker excludes this interpreter…, Distribution names from a requirements file, following -r includes., _requirements(), A Windows-only requirement is not 'missing' elsewhere (and vice versa)., test_dev_requirements_cover_every_runtime_requirement(), test_requirements_follow_environment_markers(), test_requirements_parsing_follows_includes_and_strips_specifiers()

### Community 180 - "console.py"
Cohesion: 0.33
Nodes (6): main(), The root console (v2.2): an interactive shell for operating imPress as root,…, The separate console (ssh, docker exec) is closed when root.allow_access is off…, _root_screen_allowed(), cmd, shlex

### Community 181 - "traffic_overview"
Cohesion: 0.33
Nodes (7): feature_log(), list_features(), AsyncSession, get, traffic_overview(), rank_of(), busiest()

### Community 182 - "test_device_caps.py"
Cohesion: 0.43
Nodes (5): Boards report what they are; images must fit them (#129)., _register(), test_an_image_larger_than_the_board_slot_is_excluded(), test_caps_are_stored_and_shown(), test_older_firmware_without_caps_is_unknown_not_refused()

### Community 183 - "test_backup_script.py"
Cohesion: 0.33
Nodes (5): conftest, tarfile, scripts/backup.sh: a consistent, checksummed archive of the database, firmware…, _run(), test_the_backup_is_complete_checksummed_and_restorable()

### Community 184 - "Incident response"
Cohesion: 0.29
Nodes (7): After, Contacts (fill in), First hour, Incident response, Notify (decide with your privacy lead and counsel), Recover, What will tell you

### Community 185 - "Build, configure and flash the firmware"
Cohesion: 0.29
Nodes (6): Build, configure and flash the firmware, Configure and build each role, First v2.1 bootloader update, Flash and verify, Safety and prerequisites, Student enrollment

### Community 186 - "Administrator guide"
Cohesion: 0.29
Nodes (7): Accounts and the account lifecycle, Administrator guide, Audit, backup and restore, Classrooms and rosters, Courses, Devices and firmware, Features, backups and the system

### Community 187 - "Gateway"
Cohesion: 0.38
Nodes (3): Gateway, The C6: validate the slot (firmware spi_slot_decode), read records…, spi_slave_read(): the hub clocked `slot` and read self.armed. Returns the batch…

### Community 188 - "test_hardware_requirements.py"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 189 - "test_csv_questions.py"
Cohesion: 0.48
Nodes (6): _open_create_quiz(), #31: importing questions from CSV on the create-quiz page., test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz()

### Community 190 - "test_firmware.py"
Cohesion: 0.38
Nodes (6): _open(), #35/#36: the Firmware page and pushing an approved image from Modules., test_invalid_upload_is_explained(), test_push_dialog_without_approved_images_points_to_the_firmware_page(), test_signature_status_is_shown(), test_upload_approve_and_push_from_modules()

### Community 191 - "Global policy control (GPC)"
Cohesion: 0.33
Nodes (6): Global policy control (GPC), Related, The flags, The signed code manifest, Using it, Why not a setting in the database or an admin screen?

### Community 192 - "Permissions and OTA review (v2.2)"
Cohesion: 0.33
Nodes (5): Method, OTA path, in software, Permissions and OTA review (v2.2), Result, What is not covered

### Community 193 - "First 30 minutes with imPress"
Cohesion: 0.33
Nodes (6): 1. Install and sign in, 2. Create the teaching team and course, 3. Connect the room, 4. Run a practice question, 5. Try a poll and finish, First 30 minutes with imPress

### Community 194 - "Teacher guide"
Cohesion: 0.33
Nodes (6): Create and run a poll, Create and run a quiz, Open a class, Results and student privacy, Teacher guide, Your first sign-in

### Community 195 - "gen_motion_tokens.py"
Cohesion: 0.53
Nodes (5): math, Spring easings for the web app's motion (Material 3 Expressive), as CSS custom…, settle_time(), step(), token()

### Community 196 - "test_csp.py"
Cohesion: 0.47
Nodes (4): v2.2: the page's Content-Security-Policy forbids inline script, and the app…, test_every_page_loads_and_its_buttons_work_under_the_policy(), test_inline_script_is_blocked_and_reported(), _watch()

### Community 197 - "test_live_socket.py"
Cohesion: 0.60
Nodes (5): _count_sockets(), The live class page stops retrying when the server refuses it (#160)., _teacher_with_class(), test_a_class_without_access_shows_why_and_stops(), test_a_disabled_teacher_sees_a_notice_then_the_sign_in_page()

### Community 198 - "sqlite3"
Cohesion: 0.50
Nodes (4): main(), One-time migration: convert legacy naive-UTC timestamps to naive IST. Prior to…, _shift(), sqlite3

### Community 200 - "Control mapping"
Cohesion: 0.40
Nodes (5): Control mapping, GDPR Article 32 (security of processing), examples, NIST CSF 2.0 (functions), Other articles the software helps with, OWASP ASVS 5.0 (chapters)

### Community 201 - "Backups, restore and resetting the system"
Cohesion: 0.40
Nodes (4): Backups, restore and resetting the system, Resetting the system, Restoring, What a backup is

### Community 202 - "test_csv_classes.py"
Cohesion: 0.60
Nodes (4): _open(), #32: importing and exporting courses and sections on the Classrooms page., test_invalid_rows_block_the_import(), test_valid_file_creates_courses_and_sections()

### Community 203 - "test_diagnostics.py"
Cohesion: 0.60
Nodes (4): _beat(), #39: health states and the read-only diagnostics panel on the Modules page., _row(), test_health_badges_and_diagnostics_refresh()

### Community 205 - "test_a_background_loop_cancelled_mid_query_stops"
Cohesion: 0.67
Nodes (4): A task cancelled while its session is querying or committing must see…, test_a_background_loop_cancelled_mid_query_stops(), loop_body(), main()

### Community 206 - "Privacy notice template"
Cohesion: 0.50
Nodes (3): How [INSTITUTION] uses imPress in class, Privacy notice template, Staff version: add

### Community 207 - "test_gating_needs_the_line_to_exist_before_the_release"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

### Community 208 - "ui_tests/test_student_modules.py"
Cohesion: 0.67
Nodes (3): #40: student modules that joined a gateway appear in the inventory, the class…, _seed(), test_inventory_filters_and_class_view()

### Community 209 - "test_system_approvals.py"
Cohesion: 0.67
Nodes (3): login_api(), v2.2: dangerous actions on the System page need a second super admin (dual…, test_clear_data_needs_a_second_super_admin()

### Community 210 - "MigrationError"
Cohesion: 0.67
Nodes (3): MigrationError, RuntimeError, A migration cannot be applied safely; the message says what to do.

### Community 213 - "_stop"
Cohesion: 0.67
Nodes (3): Popen, Terminate the child and everything it started (npm, ninja, docker run)., _stop()

## Knowledge Gaps
- **269 isolated node(s):** `StaleRender`, `Feature`, `Things to check`, `Roles to decide first`, `What imPress does for you, and what it does not` (+264 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1709 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **140 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `test_sessions_v22.py`, `select`, `main.py`, `app/auth.py`, `firmware.py`, `integrity.py`, `backend/tests/conftest.py`, `finish_setup`, `make_user`, `models.py`, `services/deployments.py`, `sandbox.py`, `rootops.py`, `quizzes.py`, `make_class`, `ClassSession`, `account_refusal`, `dbgateway.py`, `test_mode.py`, `Student`, `re`, `db`, `test_hardening.py`, `services/backups.py`, `test_query_cascade.py`, `traffic_overview`, `test_db_gateway.py`, `services/approvals.py`, `UserSession`, `traffic.py`, `test_policy.py`, `presence`, `auditsink.py`, `test_super_admin_lockout.py`, `test_manage_cli.py`, `events.py`, `boot_verify.py`, `create_poll`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Why does `login()` connect `login` to `test_sessions_v22.py`, `test_results_enrolled_only.py`, `test_role_escalation.py`, `test_db_integrity.py`, `backend/tests/conftest.py`, `make_user`, `integrity.py`, `test_health.py`, `test_e2e_ota.py`, `sandbox.py`, `test_firmware_signing.py`, `make_class`, `tests/test_student_modules.py`, `test_gateway_autolink.py`, `test_quiz_correct_option.py`, `make_student`, `test_quiz_timer.py`, `test_hardening.py`, `test_device_batch_dedup.py`, `test_upgrade_integrity.py`, `test_qualification.py`, `.update`, `test_query_cascade.py`, `test_db_gateway.py`, `test_device_caps.py`, `tests/test_deployments.py`, `test_question_import.py`, `UserSession`, `test_quiz_poll_lifecycle.py`, `test_policy.py`, `test_firmware_registry.py`, `test_schedule_occupancy.py`, `test_device_api.py`, `test_device_keys.py`, `test_super_admin_lockout.py`, `test_manage_cli.py`, `events.py`, `test_fault_injection.py`, `test_login_throttle.py`, `test_trusted_installer.py`, `upload_firmware`, `test_ota_download_gating.py`, `test_ota_results.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `auth()` connect `login` to `test_sessions_v22.py`, `test_results_enrolled_only.py`, `test_role_escalation.py`, `test_transport.py`, `test_db_integrity.py`, `backend/tests/conftest.py`, `make_user`, `integrity.py`, `test_health.py`, `test_e2e_ota.py`, `sandbox.py`, `test_firmware_signing.py`, `make_class`, `tests/test_student_modules.py`, `test_gateway_autolink.py`, `test_quiz_correct_option.py`, `make_student`, `test_quiz_timer.py`, `test_hardening.py`, `test_device_batch_dedup.py`, `test_upgrade_integrity.py`, `test_qualification.py`, `.update`, `test_query_cascade.py`, `test_db_gateway.py`, `test_device_caps.py`, `tests/test_deployments.py`, `test_question_import.py`, `UserSession`, `test_quiz_poll_lifecycle.py`, `test_policy.py`, `test_firmware_registry.py`, `test_schedule_occupancy.py`, `test_device_api.py`, `test_device_keys.py`, `test_super_admin_lockout.py`, `test_manage_cli.py`, `test_fault_injection.py`, `test_login_throttle.py`, `test_trusted_installer.py`, `upload_firmware`, `test_ota_download_gating.py`, `test_ota_results.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 211 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 211 INFERRED edges - model-reasoned connections that need verification._
- **Are the 217 inferred relationships involving `select()` (e.g. with `in_class_now()` and `live_sessions()`) actually correct?**
  _`select()` has 217 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `make_user()` (e.g. with `User` and `find()`) actually correct?**
  _`make_user()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `Feature`, `Things to check` to the rest of the system?**
  _269 weakly-connected nodes found - possible documentation gaps or missing edges._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
