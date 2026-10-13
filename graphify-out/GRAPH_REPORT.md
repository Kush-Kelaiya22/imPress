# Graph Report - imPress  (2026-10-13)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3386 nodes · 9386 edges · 236 communities (109 shown, 127 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1401 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cdcd48e7`
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
- Community 132
- Community 134
- Community 140
- Community 141
- Community 232
- Community 233
- Community 234
- Community 235

## God Nodes (most connected - your core abstractions)
1. `select()` - 169 edges
2. `User` - 154 edges
3. `login()` - 149 edges
4. `auth()` - 147 edges
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
  backend/tests/test_auth_sessions.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_class_create.py → run_tests.py
- `q()` --calls--> `select()`  [INFERRED]
  backend/tests/test_firmware_upload.py → run_tests.py
- `get()` --calls--> `select()`  [INFERRED]
  backend/tests/test_health.py → run_tests.py

## Import Cycles
- None detected.

## Communities (236 total, 127 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (107): log_activity(), AsyncSession, Write one activity log entry., User, admin_class_devices(), admin_create_class(), admin_delete_class(), admin_get_module() (+99 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (90): auth(), login(), fixture, su(), parametrize, Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py…, _session_row(), q() (+82 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (79): Course catalog router: universal courses referenced by classroom sections., ActivityLogResponse, AdminUserCreate, ClassAssignTeacher, ClassCreate, ClassDevicesResponse, ClassFacultyUpdate, ClassJoin (+71 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (62): asyncio, Activity logging service — records all significant actions., hash_password(), JWT + server-side session authentication helpers., Application configuration loaded from environment variables., get_db(), init_db(), Async SQLAlchemy engine and session factory. (+54 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (73): api_key_ok(), Constant-time device API key comparison., commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, authorize(), _by_mac(), caller_for_key() (+65 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (65): config, nvs_handle_t, cfg_clear_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str(), _store_dev_key() (+57 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (67): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+59 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (59): adc_oneshot, crypto, esp_crt_bundle, esp_heap_caps, esp_http_client, esp_mac, esp_netif, esp_ota_handle_t (+51 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (59): BaseType_t, spi_slave_read(), xSemaphoreGive(), xSemaphoreTake(), msg_t, handle_c6_frame(), heartbeat_task(), on_student_message() (+51 more)

### Community 10 - "Community 10"
Cohesion: 0.10
Nodes (62): esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client_config_t, esp_websocket_client_handle_t, esp_websocket_error_type_t (+54 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (56): AsyncConnection, AsyncEngine, _add_columns(), add_deployment_deferral(), add_device_keys(), add_diagnostics_columns(), add_firmware_signer(), add_quiz_question_started_at() (+48 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (57): DeploymentTarget, FirmwareDeployment, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., _act(), cancel_deployment(), create_deployment(), deployment_dict() (+49 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (56): FirmwareArtifact, One uploaded firmware image. Facts come from the image itself…, approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get() (+48 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (46): esp_log, esp_now, esp_random, esp_wifi, display_clear(), display_deinit(), display_flush(), display_init() (+38 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (25): cjson, esp_app_desc, esp_bit_defs, esp_efuse, esp_err, esp_event, esp_idf_version, esp_transport_ws (+17 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (49): make_user(), Create a user through the admin API; returns (user_id, auth headers)., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password(), test_admin_password_reset(), test_create_user_field_limits() (+41 more)

### Community 17 - "Community 17"
Cohesion: 0.14
Nodes (48): cJSON_AddItemToArray(), cJSON_AddItemToObject(), cJSON_CreateObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc() (+40 more)

### Community 18 - "Community 18"
Cohesion: 0.11
Nodes (46): ClassOccurrenceException, ClassSession, One dated change to a class's weekly timetable (meeting_schedule). cancelled:…, class_access(), class_owner_or_admin(), Delete a class: its primary teacher or an administrator., Work with a class: its primary teacher, any co-faculty member, or an…, _accessible_class() (+38 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (46): apply_status(), asset_base(), badge(), _badge_text(), channels(), check_changelog(), clean_prs(), current_latest() (+38 more)

### Community 20 - "Community 20"
Cohesion: 0.08
Nodes (36): playwright_sync_api, tempfile, time, login(), Browser UI checks: a real backend on a temp database, driven by Playwright.…, _open(), #32: importing and exporting courses and sections on the Classrooms page., test_invalid_rows_block_the_import() (+28 more)

### Community 21 - "Community 21"
Cohesion: 0.10
Nodes (40): advance(), deadline(), finish(), AsyncSession, datetime, Advance or end every timed quiz whose time is up. The caller commits, then…, When the current question (per_question) or the whole quiz (total) runs out;…, Seconds a module has for the question it is about to show: the per-question… (+32 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (39): cJSON_Hooks, buffer_skip_whitespace(), cJSON_bool, cJSON_AddBoolToObject(), cJSON_Compare(), cJSON_CreateBool(), cJSON_InitHooks(), cJSON_Minify() (+31 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (41): create_access_token(), Legacy JWT creation (kept for device registration / backward compat)., A student module seen on a gateway's mesh (#40): presence, not location. One…, StudentModule, class_modules(), _device_to_dict(), mark_offline(), presence_snapshot() (+33 more)

### Community 24 - "Community 24"
Cohesion: 0.10
Nodes (42): Base, Attendance, Student, StudentEnrollment, bulk_create_students(), _create_one(), create_student(), deactivate_student() (+34 more)

### Community 25 - "Community 25"
Cohesion: 0.07
Nodes (40): Course, export_classes_csv(), Every course section in the import layout. Cells that would start a spreadsheet…, create_course(), delete_course(), get_course(), list_courses(), AsyncSession (+32 more)

### Community 26 - "Community 26"
Cohesion: 0.06
Nodes (31): _parse_time(), Convert "HH:MM" → minutes since midnight. Returns None if malformed., Two time slots overlap when neither fully precedes the other. Overnight / wrap-…, Two classes only clash if they run in the same semester/window. Priority:…, _same_academic_window(), _slots_conflict(), normalize_version(), as_ist() (+23 more)

### Community 27 - "Community 27"
Cohesion: 0.12
Nodes (40): Poll, PollVote, QuizAnswer, Get a student's participation summary across quizzes and polls., student_participation(), create_poll(), end_poll(), get_poll() (+32 more)

### Community 28 - "Community 28"
Cohesion: 0.09
Nodes (29): assert, backend_fail_t, errno, esp_tls_errors, esp_event_base_t, ws_client_is_connected(), ws_client_send(), ws_event_handler() (+21 more)

### Community 29 - "Community 29"
Cohesion: 0.08
Nodes (22): answer(), Gateway, join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., _marker() (+14 more)

### Community 30 - "Community 30"
Cohesion: 0.12
Nodes (32): Revoke every session of a user (except `keep_id`), in the caller's transaction…, revoke_user_sessions(), verify_password(), LoginThrottle, Failed password attempts per key: user:<name>, ip:<address>, change:<user id>., activity_ping(), change_password(), login() (+24 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (32): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts…, Length of the app image itself (segments, checksum, appended SHA-256), without… (+24 more)

### Community 32 - "Community 32"
Cohesion: 0.10
Nodes (30): make_class(), Create a class via /api/admin/classes; optionally activate it., Classes (routers/classes.py, admin class routes) and courses…, test_activate_deactivate_toggle(), test_back_to_back_slots_do_not_warn(), test_class_codes_are_unique(), test_join_requires_known_active_code(), test_other_teachers_class_is_forbidden() (+22 more)

### Community 33 - "Community 33"
Cohesion: 0.10
Nodes (30): One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent…, go(), link(), age(), _activity(), q(), _device(), q() (+22 more)

### Community 34 - "Community 34"
Cohesion: 0.13
Nodes (33): batch_flush(), add_item_to_object(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddFalseToObject(), cJSON_AddItemToObjectCS(), cJSON_AddNullToObject(), cJSON_AddNumberToObject() (+25 more)

### Community 35 - "Community 35"
Cohesion: 0.13
Nodes (32): Quiz, QuizQuestion, Example file with every column. Public: it contains no data., create_quiz(), get_quiz(), import_question_csv(), list_quizzes(), next_question() (+24 more)

### Community 36 - "Community 36"
Cohesion: 0.22
Nodes (30): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+22 more)

### Community 37 - "Community 37"
Cohesion: 0.09
Nodes (27): make_student(), fixture, A class with a quiz, a poll, an enrolled student who answered and voted over…, world(), link_module(), test_attendance_paths(), count(), _matrix() (+19 more)

### Community 38 - "Community 38"
Cohesion: 0.11
Nodes (27): create_session(), generate_session_token(), get_current_user(), get_current_user_light(), _load_session_by_hash(), AsyncSession, Request, Load a session by its token_hash, checking revoked/expired status. (+19 more)

### Community 39 - "Community 39"
Cohesion: 0.09
Nodes (14): Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, #21: co-faculty can run quizzes/polls for their class; outsiders still can't., _create(), parametrize, #22: correct_option must index one of the question's options., test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected() (+6 more)

### Community 40 - "Community 40"
Cohesion: 0.13
Nodes (28): spi_slave_transaction_t, queue_slot(), spi_post_trans_cb(), spi_slave_init(), esp_err_t, SemaphoreHandle_t, spi_slave_transaction_t, TickType_t (+20 more)

### Community 41 - "Community 41"
Cohesion: 0.12
Nodes (29): add_item_to_array(), cJSON, case_insensitive_strcmp(), cJSON_AddItemReferenceToArray(), cJSON_AddItemReferenceToObject(), cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive() (+21 more)

### Community 42 - "Community 42"
Cohesion: 0.19
Nodes (25): _advance(), _artifact(), at(), clock(), _deploy(), _gateway(), fixture, parametrize (+17 more)

### Community 44 - "Community 44"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 45 - "Community 45"
Cohesion: 0.18
Nodes (25): _csv(), _files(), import_(), parse(), parametrize, questions(), q(), #31: import quiz questions from CSV (parse/preview, all-or-nothing import). (+17 more)

### Community 46 - "Community 46"
Cohesion: 0.14
Nodes (24): Any, When each authoritative timetable source last synchronised (#126/#127). No row…, ScheduleSource, _at(), Busy, find_schedule_conflicts(), occupancy(), AsyncSession (+16 more)

### Community 47 - "Community 47"
Cohesion: 0.19
Nodes (24): _count(), q(), _csv(), _post(), parametrize, #32: import courses and their sections (class sessions) from CSV., test_admin_only(), test_any_invalid_row_means_nothing_is_imported() (+16 more)

### Community 48 - "Community 48"
Cohesion: 0.13
Nodes (24): _poll(), parametrize, _quiz(), Quiz and poll state machines + results (routers/quizzes.py, routers/polls.py).…, #76: a restarted poll would keep its old votes., #76: its answers are still stored, so devices would be refused on Q1., test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted() (+16 more)

### Community 49 - "Community 49"
Cohesion: 0.14
Nodes (21): make_image(), _count(), q(), parametrize, #35: uploaded firmware is validated as a real imPress image and registered…, Against genuine ESP-IDF output when a local build exists (the synthetic images…, A scripts/build_signed.sh build (#66), when one exists locally., test_a_c6_image_is_never_pushed_to_an_s3() (+13 more)

### Community 50 - "Community 50"
Cohesion: 0.11
Nodes (21): posix_only, discover(), Run `cmd` and return (exit code, combined output, abort reason). Output is read…, run_streaming(), signal, test_every_default_runner_suite_runs_in_ci(), test_frontend_is_installed_from_its_lockfile(), test_runner_discovers_every_host_suite() (+13 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (15): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+7 more)

### Community 52 - "Community 52"
Cohesion: 0.17
Nodes (20): functions(), mentions(), {name: body_text} for every top-level function definition in a C file., #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch() (+12 more)

### Community 53 - "Community 53"
Cohesion: 0.12
Nodes (18): _calls(), The authorization policy is the one place that decides access (#122)., A staff route without a policy permission is a new hole; device routes…, Role checks scattered across routers drifted before (#19-#21, #116, #121)., docs/design/authorization.md shows GRANTS; it must not drift., _routes(), test_every_route_is_governed_by_the_policy_or_listed(), test_no_role_comparisons_outside_the_policy() (+10 more)

### Community 54 - "Community 54"
Cohesion: 0.13
Nodes (16): check_secure(), insecure_settings(), Refuse to run with published secrets, or with unauthenticated WebSockets…, Names of settings still at their public, repo-published defaults., Settings, _reset_db(), _fresh_settings(), #11: no working public credentials or debug leaks by default. (+8 more)

### Community 55 - "Community 55"
Cohesion: 0.17
Nodes (18): _add(), _busy(), phy(), fixture, parametrize, Dated timetable changes and room occupancy (#126). 2026-10-12 is a Monday,…, su(), test_a_cancelled_day_frees_every_slot() (+10 more)

### Community 56 - "Community 56"
Cohesion: 0.16
Nodes (16): platform, CaseResult, fmt_secs(), _idf_image_present(), main(), markdown_report(), Paint, parse_host_output() (+8 more)

### Community 57 - "Community 57"
Cohesion: 0.12
Nodes (16): argparse, os, init_env(), Path, Create or complete backend/.env from backend/.env.example (#42). The public…, Returns the names of the secrets it generated., call(), env_value() (+8 more)

### Community 58 - "Community 58"
Cohesion: 0.29
Nodes (19): _age(), _batch(), beat(), join(), leave(), _modules(), #40: the student module inventory. Modules seen on a gateway's mesh are listed…, _rows() (+11 more)

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
Cohesion: 0.15
Nodes (18): account_refusal(), allowed(), can_grant(), forbidden(), is_staff(), HTTPException, Authorization policy: the one place that decides who may do what (#122). Every…, Enrol or remove students, list a class roster: the primary teacher or an… (+10 more)

### Community 63 - "Community 63"
Cohesion: 0.28
Nodes (18): _beat(), _device(), q(), _key(), #66: per-device keys. Devices register with the shared key and are issued their…, _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out() (+10 more)

### Community 64 - "Community 64"
Cohesion: 0.25
Nodes (15): msg_type_t, msg_to_json(), student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join() (+7 more)

### Community 65 - "Community 65"
Cohesion: 0.24
Nodes (16): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), _artifact(), _deploy(), _download(), fixture, TrustedInstaller (#123): firmware reaches a device only after its own checks,…, The production defaults: no unsigned images, no self-approval. (+8 more)

### Community 66 - "Community 66"
Cohesion: 0.19
Nodes (14): Build structurally valid ESP-IDF app images for tests (real header layout, app…, _digest(), h(), fixture, #66 (2/3): signed firmware. The verifier is checked against images signed by…, site_key(), test_a_foreign_key_is_refused_but_a_second_signature_by_the_site_key_counts(), test_an_unreadable_site_key_is_reported() (+6 more)

### Community 67 - "Community 67"
Cohesion: 0.15
Nodes (16): _me(), fixture, parametrize, At least one active super admin always remains (#116). The original failure: a…, The original lockout path: PUT with is_active=false on yourself (#116, #119)., Two super admins disabling each other at the same moment: one must fail., su(), test_concurrent_mutual_deactivation_leaves_one_super_admin() (+8 more)

### Community 68 - "Community 68"
Cohesion: 0.21
Nodes (18): changelog_at(), find_template(), git(), _key(), notes_path(), owner_versions(), parse_branch(), plan() (+10 more)

### Community 69 - "Community 69"
Cohesion: 0.15
Nodes (11): is_loopback(), needs_https(), Should this request be refused for arriving without TLS?, _https(), fixture, HTTPS for staff traffic and browser security headers (#152)., uvicorn turns X-Forwarded-Proto from a trusted proxy into the scheme; the test…, strict() (+3 more)

### Community 70 - "Community 70"
Cohesion: 0.14
Nodes (10): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, #132: both backend clients classify a failure and log the hint, and the boot…, test_connection_failures_say_why(), test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), #13: S3 OTA — rollback protection and no reboot when nothing is installed., test_detach_unregisters_reconnect_handler_before_disconnecting() (+2 more)

### Community 71 - "Community 71"
Cohesion: 0.15
Nodes (9): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat() (+1 more)

### Community 72 - "Community 72"
Cohesion: 0.18
Nodes (15): clock(), fixture, parametrize, Password guessing is slowed; new passwords resist trivial guesses (#153)., test_another_username_is_not_affected(), test_counters_survive_a_restart(), test_existing_passwords_keep_working(), test_one_address_guessing_many_usernames_is_slowed() (+7 more)

### Community 73 - "Community 73"
Cohesion: 0.21
Nodes (15): cJSON_GetArraySize(), cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput() (+7 more)

### Community 74 - "Community 74"
Cohesion: 0.16
Nodes (10): json, main(), Fail clearly if committed Graphify output is incomplete, stale, or unsafe., source_commit(), subprocess, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards() (+2 more)

### Community 75 - "Community 75"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 76 - "Community 76"
Cohesion: 0.22
Nodes (12): main(), Returns the new password. Raises LookupError for an unknown username., restore_super_admin(), _lock_out(), Offline recovery of a locked-out installation (#120)., A database from before #116: no triggers, every super admin inactive., _restore(), _sql() (+4 more)

### Community 77 - "Community 77"
Cohesion: 0.30
Nodes (14): _advance(), _dep(), _deploy(), _prompt(), fixture, #43 end to end: a firmware release reaches three rooms through the staged…, Three rooms, each with a v2.1.0 gateway; a c6 2.2.0 image approved., Read this room's socket until the gateway's own OTA prompt. (+6 more)

### Community 78 - "Community 78"
Cohesion: 0.30
Nodes (14): _device(), q(), _push(), parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report(), test_applied_with_another_version_is_not_success(), test_applied_with_the_pushed_version_completes_the_update() (+6 more)

### Community 79 - "Community 79"
Cohesion: 0.30
Nodes (14): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+6 more)

### Community 80 - "Community 80"
Cohesion: 0.13
Nodes (11): Api, browser(), _free_port(), page(), fixture, A page that fails the test on any uncaught JS error; screenshot at the end., Tiny JSON client for setting up data the test then checks in the UI., multipart/form-data POST of one file field named 'file'. (+3 more)

### Community 81 - "Community 81"
Cohesion: 0.34
Nodes (13): answer(), batch(), count(), q(), parametrize, #6: /api/device/batch validates and de-duplicates mesh answers/votes., test_distinct_students_and_questions_all_count(), test_inactive_quiz_and_closed_poll_skipped() (+5 more)

### Community 82 - "Community 82"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10, #119: only a super admin can grant/remove admin-level roles; roles are a…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 83 - "Community 83"
Cohesion: 0.20
Nodes (12): _publish_graph_visualization(), Sphinx configuration for the public imPress documentation site., Expose the generated graph beneath the hosted ``/graph/`` page., setup(), pathlib, shutil, _open_create_quiz(), #31: importing questions from CSV on the create-quiz page. (+4 more)

### Community 84 - "Community 84"
Cohesion: 0.16
Nodes (10): #29: guards for the S3 <-> C6 link as ported from v3…, _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_student_count_comes_from_join_and_leave_only(), test_c6_validates_received_slots(), test_master_drops_a_payload_only_after_a_successful_transfer(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+2 more)

### Community 85 - "Community 85"
Cohesion: 0.22
Nodes (13): _idf_command(), _missing(), missing_packages(), _pytest_suite(), Packages from `requirements` (plus pytest) not installed in this interpreter., run_suite(), Suite, test_failing_command_is_reported() (+5 more)

### Community 86 - "Community 86"
Cohesion: 0.23
Nodes (11): append_coverage(), component_for(), enrich(), main(), node_id(), Path, Build imPress's deterministic Graphify graph and enrich non-code coverage.…, Latest commit that changed input, rather than a graph-only bot commit. (+3 more)

### Community 87 - "Community 87"
Cohesion: 0.22
Nodes (10): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+2 more)

### Community 88 - "Community 88"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 89 - "Community 89"
Cohesion: 0.36
Nodes (12): _artifact(), _hub(), _push(), #36: firmware version manager: approval, deprecation, retention, usage., _set(), test_admin_only(), test_deletion_keeps_anything_a_device_needs(), test_deprecated_images_are_not_pushed_but_in_flight_updates_finish() (+4 more)

### Community 90 - "Community 90"
Cohesion: 0.20
Nodes (12): _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), health(), get, Request (+4 more)

### Community 91 - "Community 91"
Cohesion: 0.26
Nodes (10): health(), datetime, Device health states (#39), computed from the latest heartbeat. Rules, in order…, (state, reasons) for one device., _dev(), parametrize, #39: device health states from the latest heartbeat diagnostics., test_invalid_diagnostics_are_rejected() (+2 more)

### Community 92 - "Community 92"
Cohesion: 0.20
Nodes (5): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #66: the signed-app profile and the scripts that build with it., re

### Community 93 - "Community 93"
Cohesion: 0.29
Nodes (9): importlib_util, stat, _backend(), #42: the documented install path: scripts, secrets, version, CI job., test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets() (+1 more)

### Community 94 - "Community 94"
Cohesion: 0.24
Nodes (8): cls(), fixture, parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student…, test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons()

### Community 95 - "Community 95"
Cohesion: 0.20
Nodes (9): push_device_status(), push_poll_to_mesh(), push_quiz_to_mesh(), push_student_data(), Bridge service: connects ESP device data to WebSocket clients. This service…, Push student device data (heartbeats, answers, votes) to teacher dashboard., Push individual device status update., Push quiz question through WebSocket → C6 → SPI → S3 → mesh → students. (+1 more)

### Community 96 - "Community 96"
Cohesion: 0.42
Nodes (9): _class(), _gateway_of(), q(), #17: registration must not steal a class's gateway link., _register(), test_explicit_classroom_code_still_assigns(), test_gateway_keeps_its_class_on_reregister(), test_non_gateway_registration_keeps_class_gateway() (+1 more)

### Community 97 - "Community 97"
Cohesion: 0.31
Nodes (9): device(), set_pending(), go(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download() (+1 more)

### Community 98 - "Community 98"
Cohesion: 0.20
Nodes (10): parse_coverage(), parse_junit(), Path, Test cases from a pytest JUnit XML file., Distribution names from a requirements file, following -r includes., Total line coverage (%) from a Cobertura XML report (pytest-cov)., _requirements(), test_dev_requirements_cover_every_runtime_requirement() (+2 more)

### Community 99 - "Community 99"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 100 - "Community 100"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 102 - "Community 102"
Cohesion: 0.32
Nodes (6): Loading a user or a class list must not pull in the teaching history (#133).…, statements(), test_class_list_counts_without_loading_quizzes(), test_loading_a_user_is_one_statement(), load(), contextlib

### Community 103 - "Community 103"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 104 - "Community 104"
Cohesion: 0.47
Nodes (5): _next_device_frame(), _project(), Contract test: frames the C6 gateway receives on its device WebSocket (#3). The…, The single frame an action broadcasts; it must carry a firmware event. Reads…, test_device_socket_receives_firmware_contract()

### Community 105 - "Community 105"
Cohesion: 0.50
Nodes (4): _check(), problem(), Password policy for new and changed passwords (#153). Existing passwords keep…, Why `password` is not acceptable as a new password, or None.

### Community 107 - "Community 107"
Cohesion: 0.50
Nodes (4): client(), _drain_background_tasks(), fixture, TestClient on an empty database (the app seeds the super admin).

### Community 108 - "Community 108"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

### Community 109 - "Community 109"
Cohesion: 0.67
Nodes (3): SQLite ignores foreign keys unless asked, per connection., _sqlite_pragmas(), listens_for

### Community 110 - "Community 110"
Cohesion: 0.67
Nodes (3): put, A logged-in user updates their own display name., update_profile()

### Community 112 - "Community 112"
Cohesion: 0.67
Nodes (3): Popen, Terminate the child and everything it started (npm, ninja, docker run)., _stop()

## Knowledge Gaps
- **50 isolated node(s):** `StaleRender`, `ASAN_OPTIONS`, `run.sh script`, `afl-prepare-linux.sh script`, `afl.sh script` (+45 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1024 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **127 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `Community 23` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 11`, `Community 12`, `Community 13`, `Community 21`, `Community 26`, `Community 27`, `Community 29`, `Community 30`, `Community 32`, `Community 33`, `Community 35`, `Community 36`, `Community 38`, `Community 46`, `Community 58`, `Community 72`, `Community 77`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `select()` connect `Community 27` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 12`, `Community 13`, `Community 18`, `Community 21`, `Community 23`, `Community 24`, `Community 25`, `Community 29`, `Community 30`, `Community 33`, `Community 35`, `Community 36`, `Community 37`, `Community 38`, `Community 42`, `Community 45`, `Community 46`, `Community 47`, `Community 48`, `Community 49`, `Community 50`, `Community 56`, `Community 58`, `Community 63`, `Community 76`, `Community 78`, `Community 81`, `Community 85`, `Community 96`, `Community 102`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `User` connect `Community 0` to `Community 32`, `Community 3`, `Community 35`, `Community 67`, `Community 38`, `Community 102`, `Community 76`, `Community 12`, `Community 110`, `Community 13`, `Community 47`, `Community 18`, `Community 53`, `Community 30`, `Community 24`, `Community 25`, `Community 27`, `Community 62`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 165 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 165 INFERRED edges - model-reasoned connections that need verification._
- **Are the 130 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 130 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `ASAN_OPTIONS`, `run.sh script` to the rest of the system?**
  _50 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.04837364470391994 - nodes in this community are weakly interconnected._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
