# Graph Report - imPress  (2026-10-13)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3288 nodes · 9098 edges · 216 communities (90 shown, 126 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1379 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9c44166c`
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
- Community 115
- Community 121
- Community 122
- Community 212
- Community 213
- Community 214
- Community 215

## God Nodes (most connected - your core abstractions)
1. `select()` - 166 edges
2. `User` - 154 edges
3. `login()` - 142 edges
4. `auth()` - 140 edges
5. `istnow()` - 102 edges
6. `EspDevice` - 100 edges
7. `ClassSession` - 93 edges
8. `make_user()` - 89 edges
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

## Communities (216 total, 126 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (111): log_activity(), AsyncSession, Write one activity log entry., hash_password(), Server-side maintenance commands, run on the host that has the database (#120).…, Returns the new password. Raises LookupError for an unknown username., restore_super_admin(), User (+103 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (101): asyncio, api_key_ok(), Constant-time device API key comparison., authorize(), _by_mac(), caller_for_key(), denial(), device_caller() (+93 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (83): Activity logging service — records all significant actions., create_access_token(), create_session(), generate_session_token(), get_current_user(), get_current_user_light(), _load_session_by_hash(), AsyncSession (+75 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (82): DeploymentTarget, FirmwareArtifact, FirmwareDeployment, One uploaded firmware image. Facts come from the image itself…, A rollout of one firmware image to a set of devices, in stages (canary, then…, One device in a deployment, with its update state., _act(), cancel_deployment() (+74 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (78): auth(), login(), fixture, su(), parametrize, Auth + server-side session lifecycle (app/auth.py, routers/auth.py, main.py…, _session_row(), q() (+70 more)

### Community 5 - "Community 5"
Cohesion: 0.04
Nodes (74): ActivityLogResponse, AdminUserCreate, ClassAssignTeacher, ClassDevicesResponse, ClassFacultyUpdate, ClassJoin, ClassUpdate, CourseResponse (+66 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (72): Quiz, advance(), answer_closed(), broadcast(), deadline(), finish(), AsyncSession, datetime (+64 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (66): config, nvs_handle_t, cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), init_nvs_config(), nvs_save_class_id(), _read_str() (+58 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (49): dependencies, axios, react, react-dom, react-router-dom, devDependencies, vite, @vitejs/plugin-react (+41 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (66): AsyncConnection, AsyncEngine, _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), health() (+58 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (67): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+59 more)

### Community 11 - "Community 11"
Cohesion: 0.07
Nodes (64): xSemaphoreGive(), xSemaphoreTake(), msg_t, handle_c6_frame(), heartbeat_task(), on_student_message(), spi_link_task(), esp_now_recv_info_t (+56 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (26): assert, backend_fail_t, cjson, crypto, esp_err, esp_event, esp_http_client, esp_idf_version (+18 more)

### Community 13 - "Community 13"
Cohesion: 0.09
Nodes (64): errno, esp_event_handler_t, esp_tls_crypto, esp_transport, esp_transport_ssl, esp_transport_tcp, esp_websocket_client_config_t, esp_websocket_client_handle_t (+56 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (64): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+56 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (62): Any, ClassSession, class_access(), class_owner_or_admin(), Delete a class: its primary teacher or an administrator., Work with a class: its primary teacher, any co-faculty member, or an…, sees_all_classes(), admin_create_class() (+54 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (55): adc_oneshot, esp_crt_bundle, esp_heap_caps, esp_netif, esp_ota_handle_t, esp_partition_t, esp_system, esp_timer (+47 more)

### Community 17 - "Community 17"
Cohesion: 0.05
Nodes (47): When each authoritative timetable source last synchronised (#126/#127). No row…, ScheduleSource, _at(), Busy, occupancy(), _parse_time(), AsyncSession, datetime (+39 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (47): make_user(), Create a user through the admin API; returns (user_id, auth headers)., _import(), parametrize, Admin user management (routers/admin.py /api/admin/users*)., test_admin_cannot_reset_super_admin_password(), test_admin_password_reset(), test_create_user_field_limits() (+39 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (44): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), ValueError, Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts…, Length of the app image itself (segments, checksum, appended SHA-256), without… (+36 more)

### Community 20 - "Community 20"
Cohesion: 0.06
Nodes (34): answer(), Gateway, join(), A simulated C6 gateway for end-to-end tests (#43). It talks to the backend…, Mesh messages arriving from the S3 (msg_to_json adds device_mac)., POST the buffer; returns the HTTP status. Keeps it on a 5xx., ws_command.c → ota_prompt_target: only a prompt for this gateway., One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes silent… (+26 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (48): cJSON_AddItemToArray(), cJSON_AddItemToObject(), cJSON_CreateObject(), cJSON_Duplicate(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc() (+40 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (37): os, playwright_sync_api, tempfile, time, login(), Browser UI checks: a real backend on a temp database, driven by Playwright.…, _open(), #32: importing and exporting courses and sections on the Classrooms page. (+29 more)

### Community 23 - "Community 23"
Cohesion: 0.11
Nodes (42): Base, commit_or_conflict(), AsyncSession, Commit; a uniqueness/foreign-key violation becomes an HTTP error. Application…, Attendance, ClassOccurrenceException, Poll, PollVote (+34 more)

### Community 24 - "Community 24"
Cohesion: 0.11
Nodes (39): cJSON_Hooks, buffer_skip_whitespace(), cJSON_bool, cJSON_AddBoolToObject(), cJSON_Compare(), cJSON_CreateBool(), cJSON_InitHooks(), cJSON_Minify() (+31 more)

### Community 25 - "Community 25"
Cohesion: 0.09
Nodes (36): dataclasses, platform, CaseResult, fmt_secs(), _idf_command(), _idf_image_present(), main(), markdown_report() (+28 more)

### Community 26 - "Community 26"
Cohesion: 0.07
Nodes (32): argparse, json, pathlib, append_coverage(), component_for(), enrich(), main(), node_id() (+24 more)

### Community 27 - "Community 27"
Cohesion: 0.12
Nodes (34): esp_efuse, esp_mac, display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown(), display_show_provision_state() (+26 more)

### Community 28 - "Community 28"
Cohesion: 0.11
Nodes (36): QuizAnswer, _count(), q(), _fk_violations(), q(), _insert_twice(), go(), #41: the database enforces its own integrity (foreign keys, uniqueness), and… (+28 more)

### Community 29 - "Community 29"
Cohesion: 0.11
Nodes (32): BaseType_t, spi_slave_transaction_t, queue_slot(), ready_update(), spi_post_trans_cb(), spi_slave_init(), spi_slave_read(), spi_slave_send() (+24 more)

### Community 30 - "Community 30"
Cohesion: 0.10
Nodes (30): make_class(), Create a class via /api/admin/classes; optionally activate it., Classes (routers/classes.py, admin class routes) and courses…, test_activate_deactivate_toggle(), test_back_to_back_slots_do_not_warn(), test_class_codes_are_unique(), test_join_requires_known_active_code(), test_other_teachers_class_is_forbidden() (+22 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (33): batch_flush(), add_item_to_object(), cast_away_const(), cJSON_AddArrayToObject(), cJSON_AddFalseToObject(), cJSON_AddItemToObjectCS(), cJSON_AddNullToObject(), cJSON_AddNumberToObject() (+25 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (31): approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get(), _latest_approved(), list_firmware() (+23 more)

### Community 33 - "Community 33"
Cohesion: 0.08
Nodes (29): Popen, posix_only, discover(), Distribution names from a requirements file, following -r includes., Terminate the child and everything it started (npm, ninja, docker run)., Run `cmd` and return (exit code, combined output, abort reason). Output is read…, _requirements(), run_streaming() (+21 more)

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (29): QuizQuestion, fill(), _csv(), _files(), import_(), parse(), parametrize, questions() (+21 more)

### Community 35 - "Community 35"
Cohesion: 0.14
Nodes (30): Student, bulk_create_students(), _create_one(), create_student(), deactivate_student(), get_student(), hard_delete_student(), import_students_csv() (+22 more)

### Community 36 - "Community 36"
Cohesion: 0.22
Nodes (30): _advance(), _artifact_id(), _dep(), _deploy(), _mac(), #38 + #34: OTA deployments: selection, staged rollout, the per-device state…, All state is in the database: a fresh session (as after a restart) advances…, _register() (+22 more)

### Community 37 - "Community 37"
Cohesion: 0.14
Nodes (29): Example file with every column. Public: it contains no data., create_quiz(), get_quiz(), import_question_csv(), list_quizzes(), next_question(), parse_question_csv(), AsyncSession (+21 more)

### Community 38 - "Community 38"
Cohesion: 0.10
Nodes (27): make_student(), fixture, A class with a quiz, a poll, an enrolled student who answered and voted over…, world(), link_module(), _routes(), test_device_routes_reject_a_wrong_key(), _matrix() (+19 more)

### Community 39 - "Community 39"
Cohesion: 0.09
Nodes (19): client(), _drain_background_tasks(), fixture, Shared pytest fixtures for the imPress backend. Every test gets a fresh SQLite…, TestClient on an empty database (the app seeds the super admin)., Smoke tests: the app boots on an empty DB and its basic contracts hold., test_seeded_super_admin_can_log_in(), _next_device_frame() (+11 more)

### Community 40 - "Community 40"
Cohesion: 0.12
Nodes (29): add_item_to_array(), cJSON, case_insensitive_strcmp(), cJSON_AddItemReferenceToArray(), cJSON_AddItemReferenceToObject(), cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive() (+21 more)

### Community 41 - "Community 41"
Cohesion: 0.11
Nodes (25): ClassImportReport, ClassImportRow, All-or-nothing: any invalid row means nothing is imported., apply_class_import(), _changes(), export_rows(), plan_class_import(), AsyncSession (+17 more)

### Community 42 - "Community 42"
Cohesion: 0.13
Nodes (26): Digest of the public key every image must be signed with…, site_key_digest(), adopt_legacy_files(), artifact_file(), artifact_path(), AsyncSession, Path, UploadFile (+18 more)

### Community 43 - "Community 43"
Cohesion: 0.08
Nodes (18): env(), fixture, #21: co-faculty can run quizzes/polls for their class; outsiders still can't., _teacher(), _create(), ctx(), fixture, parametrize (+10 more)

### Community 44 - "Community 44"
Cohesion: 0.12
Nodes (26): _activity(), q(), _device(), q(), fixture, Gateway-facing device API (routers/device.py) + presence service…, _register(), su() (+18 more)

### Community 46 - "Community 46"
Cohesion: 0.12
Nodes (26): Course, account_refusal(), allowed(), forbidden(), HTTPException, Why `actor` may not do `action` to `target`'s account, or None. Actions: edit,…, Does `user`'s role grant `permission`? Default deny, inactive denied., Route dependency: the authenticated user must hold `permission`. (+18 more)

### Community 47 - "Community 47"
Cohesion: 0.10
Nodes (18): adminApi, apiRequest(), authApi, classesApi, ClassSocket, clearToken(), coursesApi, deploymentsApi (+10 more)

### Community 48 - "Community 48"
Cohesion: 0.09
Nodes (19): esp_app_desc, esp_bit_defs, esp_log, esp_now, esp_random, esp_wifi, event_groups, esp_now_recv_info_t (+11 more)

### Community 49 - "Community 49"
Cohesion: 0.15
Nodes (23): _count(), q(), _csv(), parametrize, #32: import courses and their sections (class sessions) from CSV., test_admin_only(), test_any_invalid_row_means_nothing_is_imported(), test_brief_column_names_are_accepted() (+15 more)

### Community 50 - "Community 50"
Cohesion: 0.13
Nodes (15): _norm(), _on(), The CI workflow is well-formed and actually runs every suite the repo has.…, _steps_text(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_dependencies_are_audited() (+7 more)

### Community 51 - "Community 51"
Cohesion: 0.17
Nodes (20): functions(), mentions(), {name: body_text} for every top-level function definition in a C file., #4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.…, test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch() (+12 more)

### Community 52 - "Community 52"
Cohesion: 0.13
Nodes (19): Older versions stored the raw bearer token in user_sessions.session_token. Any…, _scrub_raw_session_tokens(), health(), (state, reasons) for one device., _dev(), parametrize, #39: device health states from the latest heartbeat diagnostics., test_heartbeat_stores_diagnostics_and_old_firmware_still_works() (+11 more)

### Community 53 - "Community 53"
Cohesion: 0.16
Nodes (19): make_image(), _count(), q(), parametrize, #35: uploaded firmware is validated as a real imPress image and registered…, Against genuine ESP-IDF output when a local build exists (the synthetic images…, A scripts/build_signed.sh build (#66), when one exists locally., test_a_c6_image_is_never_pushed_to_an_s3() (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.13
Nodes (16): check_secure(), insecure_settings(), Names of settings still at their public, repo-published defaults., Refuse to run with published secrets, or with unauthenticated WebSockets…, Settings, _reset_db(), _fresh_settings(), #11: no working public credentials or debug leaks by default. (+8 more)

### Community 55 - "Community 55"
Cohesion: 0.12
Nodes (17): _calls(), The authorization policy is the one place that decides access (#122)., A staff route without a policy permission is a new hole; device routes…, Role checks scattered across routers drifted before (#19-#21, #116, #121)., docs/design/authorization.md shows GRANTS; it must not drift., _routes(), test_every_route_is_governed_by_the_policy_or_listed(), test_no_role_comparisons_outside_the_policy() (+9 more)

### Community 56 - "Community 56"
Cohesion: 0.17
Nodes (18): _add(), _busy(), phy(), fixture, parametrize, Dated timetable changes and room occupancy (#126). 2026-10-12 is a Monday,…, su(), test_a_cancelled_day_frees_every_slot() (+10 more)

### Community 57 - "Community 57"
Cohesion: 0.27
Nodes (20): _age(), q(), _batch(), beat(), join(), leave(), _modules(), #40: the student module inventory. Modules seen on a gateway's mesh are listed… (+12 more)

### Community 58 - "Community 58"
Cohesion: 0.14
Nodes (17): ctype, cJSON, ota_offer_t, is_hex64(), is_semver(), ota_digest_matches(), ota_parse_check(), ota_prompt_target() (+9 more)

### Community 59 - "Community 59"
Cohesion: 0.19
Nodes (17): cfg_has_device_key(), esp_err_t, esp_event_base_t, _download_and_apply(), _firmware_check(), _get_mac(), _http_post(), _http_post_body() (+9 more)

### Community 60 - "Community 60"
Cohesion: 0.17
Nodes (15): calls(), _graph(), #5: nothing running on the websocket client's own task may stop/destroy it.…, _reachable(), test_reassignment_is_applied_from_app_main(), test_ws_task_never_stops_or_destroys_its_client(), #66: the C6 and S3 use their own device key once issued, keep the shared key…, test_c6_re_registers_after_a_reset() (+7 more)

### Community 61 - "Community 61"
Cohesion: 0.28
Nodes (18): _beat(), _device(), q(), _key(), #66: per-device keys. Devices register with the shared key and are issued their…, _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out() (+10 more)

### Community 62 - "Community 62"
Cohesion: 0.25
Nodes (15): msg_type_t, msg_to_json(), student_set_t, find(), student_set_t, student_set_count(), student_set_init(), student_set_join() (+7 more)

### Community 63 - "Community 63"
Cohesion: 0.24
Nodes (16): Register (and by default approve, so it can be pushed) a structurally valid…, upload_firmware(), _artifact(), _deploy(), _download(), fixture, TrustedInstaller (#123): firmware reaches a device only after its own checks,…, The production defaults: no unsigned images, no self-approval. (+8 more)

### Community 64 - "Community 64"
Cohesion: 0.15
Nodes (16): _me(), fixture, parametrize, At least one active super admin always remains (#116). The original failure: a…, The original lockout path: PUT with is_active=false on yourself (#116, #119)., Two super admins disabling each other at the same moment: one must fail., su(), test_concurrent_mutual_deactivation_leaves_one_super_admin() (+8 more)

### Community 65 - "Community 65"
Cohesion: 0.14
Nodes (10): strip_comments_and_strings(), #66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and every…, #132: both backend clients classify a failure and log the hint, and the boot…, test_connection_failures_say_why(), test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), #13: S3 OTA — rollback protection and no reboot when nothing is installed., test_detach_unregisters_reconnect_handler_before_disconnecting() (+2 more)

### Community 66 - "Community 66"
Cohesion: 0.15
Nodes (9): ast, #39: the C6 heartbeat carries the diagnostics the backend's health rules read,…, A function's text with its string literals (functions() blanks them)., _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat() (+1 more)

### Community 67 - "Community 67"
Cohesion: 0.15
Nodes (10): _publish_graph_visualization(), Sphinx configuration for the public imPress documentation site., Expose the generated graph beneath the hosted ``/graph/`` page., setup(), shutil, _on(), Contract tests for the keyless Graphify generation and GitHub automation., test_workflow_has_required_trigger_permissions_cache_and_recursion_guards() (+2 more)

### Community 68 - "Community 68"
Cohesion: 0.21
Nodes (15): cJSON_GetArraySize(), cJSON_Parse(), cJSON_ParseWithOpts(), cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput() (+7 more)

### Community 69 - "Community 69"
Cohesion: 0.17
Nodes (11): _anchors(), parametrize, Docs stay in sync with the code: links resolve, every route and setting is…, _route_paths(), _slug(), _strip_code(), test_code_fences_are_balanced_and_mermaid_typed(), test_every_api_route_is_documented() (+3 more)

### Community 70 - "Community 70"
Cohesion: 0.30
Nodes (14): _device(), q(), _push(), parametrize, #33: OTA outcomes are recorded only from what the device really runs, and a…, _report(), test_applied_with_another_version_is_not_success(), test_applied_with_the_pushed_version_completes_the_update() (+6 more)

### Community 71 - "Community 71"
Cohesion: 0.30
Nodes (14): handle_class_assignment(), on_ws_command(), cJSON, clamp_options(), num_item(), num_or(), str_or_null(), ws_command_to_frame() (+6 more)

### Community 72 - "Community 72"
Cohesion: 0.13
Nodes (11): Api, browser(), _free_port(), page(), fixture, A page that fails the test on any uncaught JS error; screenshot at the end., Tiny JSON client for setting up data the test then checks in the UI., multipart/form-data POST of one file field named 'file'. (+3 more)

### Community 73 - "Community 73"
Cohesion: 0.19
Nodes (8): accounts(), _create(), fixture, parametrize, #10, #119: only a super admin can grant/remove admin-level roles; roles are a…, test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected()

### Community 74 - "Community 74"
Cohesion: 0.27
Nodes (13): mesh_dedup_check(), mesh_msg_id(), legacy_hash(), legacy_seen(), main(), simulate(), test_dedup_window_and_wrap(), test_id_ignores_hops_but_not_content() (+5 more)

### Community 75 - "Community 75"
Cohesion: 0.16
Nodes (10): #29: guards for the S3 <-> C6 link as ported from v3…, _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_student_count_comes_from_join_and_leave_only(), test_c6_validates_received_slots(), test_master_drops_a_payload_only_after_a_successful_transfer(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+2 more)

### Community 76 - "Community 76"
Cohesion: 0.22
Nodes (10): git(), fixture, Shared helpers for repository-level tests (CI, hygiene, docs, test runner)., tracked_files(), workflow(), Nothing generated at runtime or compiled is tracked; scripts are portable., test_no_tracked_file_is_gitignored(), test_run_tests_is_executable_entry_point() (+2 more)

### Community 77 - "Community 77"
Cohesion: 0.19
Nodes (12): FakeGitHub, #104: the first page already has the badges, the Beta/Stable box and the test…, The cascade: one milestone, three lines from two owners., _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line() (+4 more)

### Community 78 - "Community 78"
Cohesion: 0.24
Nodes (10): main(), _lock_out(), Offline recovery of a locked-out installation (#120)., A database from before #116: no triggers, every super admin inactive., _restore(), _sql(), test_cli_exit_codes(), test_promotes_an_existing_account() (+2 more)

### Community 79 - "Community 79"
Cohesion: 0.36
Nodes (12): _artifact(), _hub(), _push(), #36: firmware version manager: approval, deprecation, retention, usage., _set(), test_admin_only(), test_deletion_keeps_anything_a_device_needs(), test_deprecated_images_are_not_pushed_but_in_flight_updates_finish() (+4 more)

### Community 80 - "Community 80"
Cohesion: 0.29
Nodes (9): importlib_util, stat, _backend(), #42: the documented install path: scripts, secrets, version, CI job., test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_generated_env_is_accepted_by_the_backend_settings(), test_two_installs_get_different_secrets() (+1 more)

### Community 81 - "Community 81"
Cohesion: 0.24
Nodes (8): cls(), fixture, parametrize, _quiz(), #49: the API only accepts what a student module can show and answer. Student…, test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons()

### Community 82 - "Community 82"
Cohesion: 0.18
Nodes (4): Tiny C source helpers for structural firmware tests (no compiler needed). Good…, #11: the C6 must not put the device API key in the WS URL or the log., test_api_key_sent_as_header_not_in_uri_or_log(), #66: the signed-app profile and the scripts that build with it.

### Community 83 - "Community 83"
Cohesion: 0.42
Nodes (9): _class(), _gateway_of(), q(), #17: registration must not steal a class's gateway link., _register(), test_explicit_classroom_code_still_assigns(), test_gateway_keeps_its_class_on_reregister(), test_non_gateway_registration_keeps_class_gateway() (+1 more)

### Community 84 - "Community 84"
Cohesion: 0.31
Nodes (9): device(), set_pending(), go(), dl(), fixture, #13: firmware can only be downloaded for an OTA an admin actually pushed., test_download_requires_device_key(), test_no_pending_ota_means_no_download() (+1 more)

### Community 85 - "Community 85"
Cohesion: 0.28
Nodes (6): _order(), #34: the C6 OTA client keeps its safety ordering (behaviour of the pure parts…, test_download_checks_status_size_and_completeness_and_hashes_while_streaming(), test_image_is_verified_before_it_can_boot(), test_new_image_is_confirmed_only_when_healthy_or_reverted(), test_prompts_are_routed_by_target()

### Community 86 - "Community 86"
Cohesion: 0.28
Nodes (9): aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION…, _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch() (+1 more)

### Community 87 - "Community 87"
Cohesion: 0.43
Nodes (5): _cfg(), _partitions_end(), #30: hardware requirements stay true to the build configuration., test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub()

### Community 88 - "Community 88"
Cohesion: 0.48
Nodes (6): _open_create_quiz(), #31: importing questions from CSV on the create-quiz page., test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz()

### Community 90 - "Community 90"
Cohesion: 0.50
Nodes (4): parametrize, #104: found live: a new line on the same commit as an older release must not…, test_gating_needs_the_line_to_exist_before_the_release(), test_milestone_gating_follows_the_git_ancestry()

### Community 91 - "Community 91"
Cohesion: 0.67
Nodes (3): SQLite ignores foreign keys unless asked, per connection., _sqlite_pragmas(), listens_for

## Knowledge Gaps
- **50 isolated node(s):** `StaleRender`, `HEALTH_BADGE`, `routes`, `run_ota_logic.sh script`, `run_student_set.sh script` (+45 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 992 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **126 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `Community 1` to `Community 0`, `Community 32`, `Community 2`, `Community 3`, `Community 4`, `Community 37`, `Community 6`, `Community 36`, `Community 9`, `Community 44`, `Community 15`, `Community 17`, `Community 20`, `Community 52`, `Community 23`, `Community 57`, `Community 30`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `User` connect `Community 0` to `Community 32`, `Community 64`, `Community 2`, `Community 3`, `Community 35`, `Community 37`, `Community 39`, `Community 41`, `Community 46`, `Community 15`, `Community 49`, `Community 52`, `Community 55`, `Community 23`, `Community 30`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `select()` connect `Community 15` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 17`, `Community 20`, `Community 23`, `Community 25`, `Community 28`, `Community 32`, `Community 33`, `Community 34`, `Community 35`, `Community 36`, `Community 37`, `Community 38`, `Community 39`, `Community 41`, `Community 42`, `Community 44`, `Community 46`, `Community 49`, `Community 52`, `Community 53`, `Community 57`, `Community 61`, `Community 70`, `Community 83`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 162 inferred relationships involving `select()` (e.g. with `_load_session_by_hash()` and `validate_session()`) actually correct?**
  _`select()` has 162 INFERRED edges - model-reasoned connections that need verification._
- **Are the 130 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 130 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StaleRender`, `HEALTH_BADGE`, `routes` to the rest of the system?**
  _50 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.048750194069243906 - nodes in this community are weakly interconnected._

## Repository Coverage
- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.
- Tracked Markdown documentation and configuration files are cataloged deterministically.
- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.
- This CI mode is keyless: semantic document summarization is intentionally disabled.
