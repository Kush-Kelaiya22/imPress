# Graph Report - imPress  (2026-11-24)

## Corpus Check
- 387 files · ~282,122 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 58 file(s) not represented in the graph (top: (none) 21, .css 4, .in 4)

## Summary
- 4037 nodes · 9738 edges · 233 communities (159 shown, 74 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1256 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- models User
- main py
- run tests py
- App jsx
- services deployments py
- app js
- class c6 main main
- nvs open
- release py
- migrations py
- schemas py
- esp websocket client c
- test e2e ota py
- timeutil istnow
- test maintenance windows py
- display c
- routers auth py
- c_source functions
- models py
- models EspDevice
- models ClassSession
- mesh master c
- wifi client c
- playwright sync api
- class s3 main ota
- students py
- cJSON Utils c
- pathlib Group
- imPress v2 1 Engineering
- tests test deployments py
- courses py
- test core utils py
- cJSON c
- firmware py
- test spi slave c
- graphify yml
- re Group
- quizzes py
- test user delete py
- test policy py
- test question import py
- cJSON Delete
- protocol c
- test class import py
- test quiz timer py
- on ws command
- cJSON Module
- ci with
- test device api py
- test quiz poll lifecycle
- firmware store py
- api js
- cJSON bool
- json Group
- protocol h
- csv import py
- cJSON Library (ANSI C89
- test firmware registry py
- test ci workflow py
- models QuizAnswer
- tests test student modules
- os Group
- test schedule occupancy py
- timeutil py
- backend tests conftest py
- release with
- test secure defaults py
- test device keys py
- device auth py
- ci jobs
- test super admin lockout
- test ws auth py
- test manage cli py
- schedule py
- ui tests conftest py
- pytest Group
- test trusted installer py
- test admin users py
- quiz timer py
- appveyor yml
- test students py
- test firmware manager py
- test firmware signing py
- test c6 diagnostics py
- test classes courses py
- test login throttle py
- REST API Reference
- strip comments and strings
- test student set c
- test transport py
- test device batch dedup
- release env
- release outputs
- test health py
- test user lifecycle api
- Device API (Gateway <
- test_release FakeGitHub
- models QuizQuestion
- test hardware requirements py
- firmware build
- release firmware
- test session revocation py
- test install scripts py
- test device limits py
- accounts py
- imPress Documentation Map
- ci result
- release image
- readthedocs yaml
- test ota download gating
- test gateway autolink py
- test quiz correct option
- ESP32 C6 Classroom Gateway
- System Overview Architecture
- travis yml
- espressif esp websocket client
- ci container
- release jobs
- test repo hygiene py
- test vote answer auth
- Import Courses and Sections
- Deploy s3 v2 2
- espressif cjson idf component
- release on
- test cofaculty access py
- test results access py
- test class create py
- test class join py
- test firmware upload py
- Deployments List UI Screenshot
- Changelog v2 1
- test_release repo
- test firmware py
- CSV Questions Import Invalid
- CSV Questions Import &
- Firmware Page UI
- Student Modules Telemetry Table
- sbom cJSON yml
- image build
- .cz commitizen
- protocol Common Component
- test_quiz_timer env
- Telemetry Key Value Table
- class c6 main idf
- idf_component dependencies
- release Module
- release status
- ui tests test deployments
- Backend Architecture
- Shared Protocol Library (firmware
- Firmware Push Dialog UI
- cjson_read_fuzzer LLVMFuzzerTestOneInput
- ci env
- firmware signed
- ci on
- Python Served Vanilla JS
- Backend Runtime Dependencies (requirements
- Contributing & Maintenance Policy
- ESP NOW Flooding Mesh
- Room Capacity Limit (300
- ci changelog
- ci docs
- firmware static
- ci repo
- ci security
- ci ui
- test gating needs the
- test_student_modules setup
- Graphify Knowledge Graph Guide
- S3 C6 Full Duplex
- class c6 test host
- build signed sh
- firmware key sh
- Graphify Knowledge Graph Workflow
- RSA 3072 Firmware Signing
- test_device_keys h
- Owner Scoped Integration Lines
- Preview First All or
- v2 1 OTA Registry,
- v2 1 Security Hardening
- afl prepare linux sh
- afl sh script
- ossfuzz sh
- start server sh
- run config sh
- run ota logic sh
- run student set sh
- run ws command sh
- protocol test host run
- run backend hint sh
- run mesh dedup sh
- run host tests sh
- student test host run
- docker entrypoint sh
- install sh
- start sh
- test_release ancestry
- test_release wf
- Structured Issue Label Taxonomy
- Create Sections and Discard
- CSV File Dropzone
- CSV Schema and Atomic
- Download Template Button
- Existing Sections Conflict Dropdown
- Dry Run Section Preview
- Import Courses and Sections
- Import Summary Status Pills
- Two Step Atomic CSV
- Student Module (Classic ESP32)
- Timed Quizzes Scheduler (#73)
- v2 Audit Fixes (#1
- Backend Data Model
- esp devices Table
- Quizzes, Polls & Unique
- student modules Table
- Student Module GPIO Pinout
- Hardware Bench Checks H1
- Multi Layer Software Test
- imPress Classroom Response System
- KiCad Local History Snapshots

## God Nodes (most connected - your core abstractions)
1. `User` - 155 edges
2. `cJSON` - 123 edges
3. `istnow()` - 107 edges
4. `EspDevice` - 106 edges
5. `ClassSession` - 96 edges
6. `log_activity()` - 72 edges
7. `functions()` - 50 edges
8. `cJSON_bool` - 43 edges
9. `escHtml()` - 42 edges
10. `Quiz` - 41 edges

## Surprising Connections (you probably didn't know these)
- `test_every_setting_is_documented()` --uses--> `Settings`  [INFERRED]
  tests/test_docs_consistency.py → backend/app/config.py
- `test_signature_status_is_shown()` --calls--> `make_image()`  [INFERRED]
  ui_tests/test_firmware.py → backend/tests/firmware_images.py
- `state()` --calls--> `select()`  [INFERRED]
  backend/tests/test_quiz_poll_lifecycle.py → run_tests.py
- `main()` --uses--> `User`  [INFERRED]
  query_db.py → backend/app/models.py
- `main()` --uses--> `ClassSession`  [INFERRED]
  query_db.py → backend/app/models.py

## Import Cycles
- 2-file cycle: `backend/app/database.py -> backend/app/models.py -> backend/app/database.py`

## Hyperedges (group relationships)
- **Governance, Contribution, and Release Workflow** — code_of_conduct_policy, contributing_guide, changelog_document, contributing_integration_lines, contributing_release_automation [EXTRACTED 1.00]
- **Classroom Hardware-to-Backend Communication Pipeline** — readme_student_module, readme_esp_now_mesh, readme_esp32_s3_hub, readme_spi_10mhz_link, readme_esp32_c6_gateway, readme_fastapi_backend [EXTRACTED 1.00]
- **Python Dependency & Lockfile Chain** — backend_requirements_runtime, backend_requirements_dev_tools, backend_requirements_lock_manifest, ui_tests_requirements_playwright [EXTRACTED 1.00]
- **Classroom Hardware & Backend Pipeline** — docs_architecture_overview_student_module, docs_architecture_overview_s3_hub, docs_architecture_overview_c6_gateway, docs_architecture_overview_fastapi_backend [EXTRACTED 1.00]
- **Five-Layer Wire Protocol Stack** — docs_design_mesh_doc, docs_design_protocols_protocol_frame, docs_design_protocols_spi_slot, docs_api_device_api_batch_endpoint, docs_api_websocket_api_ws_contract [EXTRACTED 1.00]
- **Security & Authorization Architecture** — docs_design_security_model_trust_boundaries, docs_design_authorization_privilege_rings, docs_design_authorization_root_rules, docs_api_device_api_key_lifecycle [INFERRED 0.95]
- **Database Integrity and Versioned Migrations** — docs_engineering_database_migrations_doc, docs_engineering_database_migrations_atomic_startup_migrations, docs_engineering_database_migrations_foreign_key_enforcement, docs_engineering_database_migrations_unique_indexes_and_races, docs_engineering_v21_engineering_report_alembic_rejection [INFERRED 0.95]
- **v2.1 Security & Ring Authorization Controls** — docs_engineering_refactor_roadmap_lockout_invariant, docs_engineering_refactor_roadmap_ring_authorization_model, docs_engineering_security_review_per_device_keys, docs_engineering_security_review_upload_and_firmware_security, docs_guides_deployment_single_worker_and_tls [INFERRED 0.85]
- **OTA Security, TrustedInstaller & Staged Rollout** — docs_firmware_ota_architecture_doc, docs_firmware_ota_architecture_trusted_installer, docs_firmware_ota_architecture_state_machine, docs_firmware_ota_architecture_maintenance_deferral, docs_firmware_firmware_versioning_single_source, docs_guides_ota_updates_signing_and_dual_approver, docs_firmware_recovery_procedure_rollback_and_reflash [INFERRED 0.95]
- **CI, Release Automation & Multi-Layer Testing** — docs_guides_testing_doc, docs_guides_testing_multi_layer_contract_suites, docs_guides_releases_doc, docs_guides_releases_milestone_gating_and_containers, docs_engineering_v21_engineering_report_verification_summary [INFERRED 0.85]
- **Classroom Three-Tier Hardware Architecture** — docs_hardware_classroom_node_requirements_gateway_c6, docs_hardware_classroom_node_requirements_hub_s3, docs_hardware_classroom_node_requirements_student_module, docs_reference_hardware_s3_c6_wiring [EXTRACTED 1.00]
- **Class C6 Firmware Build & Managed Dependencies** — firmware_class_c6_cmakelists_impress_class_c6, firmware_class_c6_main_cmakelists_main_component, firmware_class_c6_managed_components_espressif__cjson_cmakelists_cjson_component, firmware_class_c6_managed_components_espressif__esp_websocket_client_cmakelists_esp_websocket_client_component, firmware_class_c6_version_firmware_version [EXTRACTED 1.00]
- **cJSON Library Build, Docs & Fuzzing Ecosystem** — firmware_class_c6_managed_components_espressif__cjson_readme_cjson_library, firmware_class_c6_managed_components_espressif__cjson_cmakelists_cjson_component, firmware_class_c6_managed_components_espressif__cjson_cjson_cmakelists_cjson_cmake_build, firmware_class_c6_managed_components_espressif__cjson_cjson_cmakelists_cjson_utils_target, firmware_class_c6_managed_components_espressif__cjson_cjson_fuzzing_cmakelists_fuzz_targets [INFERRED 0.85]
- **v2.1 Firmware Protocol Build Dependencies** — firmware_protocol_cmakelists_component, firmware_class_s3_cmakelists_project, firmware_class_s3_main_cmakelists_component, firmware_student_cmakelists_project, firmware_student_main_cmakelists_component [EXTRACTED 1.00]
- **CSV Question Import & Review Flow** — docs_assets_ui_csv_questions_preview_template_button, docs_assets_ui_csv_questions_preview_dropzone, docs_assets_ui_csv_questions_preview_validation_summary, docs_assets_ui_csv_questions_preview_table, docs_assets_ui_csv_questions_preview_footer_actions [INFERRED 0.95]
- **Staged Rollout Configuration Parameters** — docs_assets_ui_deploy_dialog_device_selector, docs_assets_ui_deploy_dialog_canary_input, docs_assets_ui_deploy_dialog_batch_size_input, docs_assets_ui_deploy_dialog_concurrency_input, docs_assets_ui_deploy_dialog_failure_threshold_input, docs_assets_ui_deploy_dialog_rollback_checkbox [INFERRED 0.95]
- **Firmware Upload to Staged Deployment UI Flow** — docs_assets_ui_deployments_list_firmware_dropzone, docs_assets_ui_deployments_list_s3_hub_card, docs_assets_ui_deployments_list_deployments_card, docs_assets_ui_deployments_list_deployment_row_1 [INFERRED 0.95]
- **Diagnostics Modal UI Architecture** — docs_assets_ui_diagnostics_modal, docs_assets_ui_diagnostics_key_value_list, docs_assets_ui_diagnostics_health_status, docs_assets_ui_diagnostics_heartbeat_telemetry, docs_assets_ui_diagnostics_readonly_notice, docs_assets_ui_diagnostics_action_controls [EXTRACTED 1.00]
- **Device-Type Firmware Sections** — docs_assets_ui_firmware_page_c6_gateway_section, docs_assets_ui_firmware_page_s3_hub_section, docs_assets_ui_firmware_page_student_module_section [EXTRACTED 1.00]
- **Firmware Push Modal Components** — docs_assets_ui_firmware_push_dialog_screenshot, docs_assets_ui_firmware_push_dialog_device_metadata, docs_assets_ui_firmware_push_dialog_firmware_selector, docs_assets_ui_firmware_push_dialog_push_action [EXTRACTED 1.00]
- **Student Modules Gateway Monitoring UI** — docs_assets_ui_student_modules_panel, docs_assets_ui_student_modules_header_status_badge, docs_assets_ui_student_modules_filter_toolbar, docs_assets_ui_student_modules_telemetry_table, docs_assets_ui_student_modules_state_distinction [INFERRED 0.95]

## Communities (233 total, 74 thin omitted)

### Community 0 - "models User"
Cohesion: 0.06
Nodes (49): log_activity(), User, can_grant(), roster_access(), admin_class_devices(), admin_create_class(), admin_delete_class(), admin_get_module() (+41 more)

### Community 1 - "main py"
Cohesion: 0.05
Nodes (30): init_db(), _documentation_index(), graph_data(), graph_portal(), graph_search(), graph_visualization(), lifespan(), serve_frontend() (+22 more)

### Community 2 - "run tests py"
Cohesion: 0.06
Nodes (47): CaseResult, discover(), fmt_secs(), _idf_command(), _idf_image_present(), main(), markdown_report(), _missing() (+39 more)

### Community 3 - "App jsx"
Cohesion: 0.06
Nodes (48): dependencies, axios@^1.7.0, react@^18.3.1, react-dom@^18.3.1, react-router-dom@^7.18.4, devDependencies, vite@^8.3.3, @vitejs/plugin-react@^6.1.2 (+40 more)

### Community 4 - "services deployments py"
Cohesion: 0.06
Nodes (37): DeploymentTarget, FirmwareDeployment, _act(), cancel_deployment(), create_deployment(), deployment_dict(), DeploymentCreate, _get() (+29 more)

### Community 5 - "app js"
Cohesion: 0.08
Nodes (67): _diagnosticsBody(), escHtml(), formatAgo(), formatBytes(), formatUptime(), getParams(), getRoute(), HEALTH_BADGE (+59 more)

### Community 6 - "class c6 main main"
Cohesion: 0.06
Nodes (19): c6_config_t, is_hex64(), is_semver(), ota_digest_matches(), ws_event_handler(), cJSON_Hooks, cJSON_InitHooks(), read_file() (+11 more)

### Community 7 - "nvs open"
Cohesion: 0.09
Nodes (49): init_nvs_config(), nvs_save_class_id(), _read_str(), _store_dev_key(), ota_c6_boot_check(), remember_target(), test_backend_assigned_class_id_survives_reboot(), test_bad_overrides_fall_back_to_defaults() (+41 more)

### Community 8 - "release py"
Cohesion: 0.08
Nodes (44): apply_status(), asset_base(), badge(), _badge_text(), changelog_at(), channels(), check_changelog(), clean_prs() (+36 more)

### Community 9 - "migrations py"
Cohesion: 0.06
Nodes (35): health(), _add_columns(), add_deployment_deferral(), add_device_keys(), add_diagnostics_columns(), add_firmware_signer(), add_quiz_question_started_at(), add_unique_constraints() (+27 more)

### Community 10 - "schemas py"
Cohesion: 0.05
Nodes (39): get_activity_logs(), ActivityLogResponse, AdminUserCreate, BulkStudentRegister, ClassAssignTeacher, ClassCreate, ClassDevicesResponse, ClassFacultyUpdate (+31 more)

### Community 11 - "esp websocket client c"
Cohesion: 0.10
Nodes (52): ws_client_reconnect(), ws_client_send(), ws_client_start(), ws_client_stop(), ws_recv_cb_t, destroy_and_free_resources(), esp_websocket_client_abort_connection(), esp_websocket_client_append_header() (+44 more)

### Community 12 - "test e2e ota py"
Cohesion: 0.06
Nodes (24): answer(), Gateway, join(), _advance(), _dep(), _deploy(), _prompt(), rooms() (+16 more)

### Community 13 - "timeutil istnow"
Cohesion: 0.06
Nodes (30): create_session(), get_current_user(), get_current_user_light(), _load_session_by_hash(), _sha256_hex(), validate_session(), _scrub_raw_session_tokens(), refresh_session_activity() (+22 more)

### Community 14 - "test maintenance windows py"
Cohesion: 0.08
Nodes (36): _live(), next_window(), room_class(), wire(), _advance(), _artifact(), at(), clock() (+28 more)

### Community 15 - "display c"
Cohesion: 0.08
Nodes (36): display_clear(), display_deinit(), display_flush(), display_init(), display_show_countdown(), display_show_provision_state(), display_show_question(), display_show_result() (+28 more)

### Community 16 - "routers auth py"
Cohesion: 0.07
Nodes (21): create_access_token(), hash_password(), revoke_user_sessions(), verify_password(), get_db(), LoginThrottle, _check(), problem() (+13 more)

### Community 17 - "c_source functions"
Cohesion: 0.08
Nodes (35): calls(), functions(), mentions(), test_heartbeat_hands_off_via_flag(), test_only_spi2http_path_touches_the_batch(), test_stack_watermark_reports_spi2http_not_app_main(), _users_of_batch(), _order() (+27 more)

### Community 18 - "models py"
Cohesion: 0.09
Nodes (28): Base, commit_or_conflict(), _sqlite_pragmas(), Attendance, ClassOccurrenceException, Poll, PollVote, ScheduleSource (+20 more)

### Community 19 - "models EspDevice"
Cohesion: 0.09
Nodes (30): authorize(), DeviceCaller, ActivityLog, EspDevice, _broadcast_participation(), check_attendance(), firmware_applied(), firmware_check() (+22 more)

### Community 20 - "models ClassSession"
Cohesion: 0.09
Nodes (30): ClassSession, allowed(), class_access(), class_owner_or_admin(), require(), dependency(), sees_all_classes(), _accessible_class() (+22 more)

### Community 21 - "mesh master c"
Cohesion: 0.09
Nodes (31): xSemaphoreGive(), xSemaphoreGiveFromISR(), xSemaphoreTake(), s3_config_t, handle_c6_frame(), heartbeat_task(), on_student_message(), spi_link_task() (+23 more)

### Community 22 - "wifi client c"
Cohesion: 0.08
Nodes (33): cfg_clear_device_key(), cfg_has_device_key(), cfg_set_device_key(), app_main(), heartbeat_task(), status_ping_task(), wifi_connect_with_backoff(), download() (+25 more)

### Community 23 - "playwright sync api"
Cohesion: 0.05
Nodes (15): _open(), test_invalid_rows_block_the_import(), test_valid_file_creates_courses_and_sections(), _open_create_quiz(), test_invalid_rows_block_the_import_and_are_explained(), test_template_link_downloads_the_example(), test_unusable_file_shows_the_reason(), test_valid_file_loads_into_the_form_and_creates_the_quiz() (+7 more)

### Community 24 - "class s3 main ota"
Cohesion: 0.07
Nodes (24): log_error_if_nonzero(), main(), websocket_event_handler(), esp_websocket_client, esp_websocket_error_codes_t, esp_websocket_error_type_t, esp_websocket_event_data_t, esp_websocket_transport_t (+16 more)

### Community 25 - "students py"
Cohesion: 0.10
Nodes (22): Student, class_import_template(), list_class_students(), _student_response(), me(), bulk_create_students(), _create_one(), create_student() (+14 more)

### Community 26 - "cJSON Utils c"
Cohesion: 0.13
Nodes (36): cJSON_AddItemToObject(), cJSON_free(), cJSON_IsArray(), cJSON_IsObject(), cJSON_malloc(), apply_patch(), cJSONUtils_AddPatchToArray(), cJSONUtils_ApplyPatches() (+28 more)

### Community 27 - "pathlib Group"
Cohesion: 0.11
Nodes (17): _cstr(), image_end(), ImageError, ImageInfo, parse_image(), _der(), key_digest(), load_public_key() (+9 more)

### Community 28 - "imPress v2 1 Engineering"
Cohesion: 0.07
Nodes (19): Database Migrations Documentation, Refactor Audit and Roadmap (v2.1), Security Review (v2.1), Three-Tier Classroom Hardware Architecture, System Audit: imPress v2 to v2.1, imPress v2.1 Engineering Report, v2.1 Automated Verification & Hardware Gap, v2 / v3 Branch Comparison (+11 more)

### Community 29 - "tests test deployments py"
Cohesion: 0.16
Nodes (30): _advance(), _artifact_id(), _dep(), _deploy(), h(), _mac(), _register(), _set_firmware_version() (+22 more)

### Community 30 - "courses py"
Cohesion: 0.09
Nodes (17): Course, export_classes_csv(), import_classes_csv(), create_course(), delete_course(), get_course(), list_courses(), update_course() (+9 more)

### Community 31 - "test core utils py"
Cohesion: 0.08
Nodes (14): _parse_time(), _slots_conflict(), normalize_version(), as_ist(), ConnectionManager, FakeWS, test_as_ist_treats_naive_as_utc(), test_manager_disconnect_frees_empty_rooms() (+6 more)

### Community 32 - "cJSON c"
Cohesion: 0.09
Nodes (29): cast_away_const(), cJSON_AddFalseToObject(), cJSON_AddItemReferenceToObject(), cJSON_AddNullToObject(), cJSON_AddRawToObject(), cJSON_AddTrueToObject(), cJSON_CreateArrayReference(), cJSON_CreateFalse() (+21 more)

### Community 33 - "firmware py"
Cohesion: 0.13
Nodes (17): FirmwareArtifact, approve_firmware(), delete_firmware(), deprecate_firmware(), firmware_detail(), FirmwareUpdate, _get(), _latest_approved() (+9 more)

### Community 34 - "test spi slave c"
Cohesion: 0.11
Nodes (22): queue_slot(), ready_update(), spi_post_trans_cb(), spi_slave_init(), spi_slave_read(), spi_slave_send(), clobber_stack(), gpio_config() (+14 more)

### Community 35 - "graphify yml"
Cohesion: 0.06
Nodes (33): concurrency, cancel-in-progress, group, env, GH_TOKEN, PYTHON_VERSION, SOURCE_SHA, TARGET_BRANCH (+25 more)

### Community 36 - "re Group"
Cohesion: 0.11
Nodes (22): test_api_key_sent_as_header_not_in_uri_or_log(), _src(), test_both_ends_use_standard_full_duplex_spi(), test_c6_flushes_bounded_chunks_and_keeps_them_on_transport_errors(), test_c6_services_spi_while_wifi_is_down_with_a_bounded_batch(), test_clock_is_configurable_and_defaults_to_10_mhz(), test_s3_heartbeat_record_is_not_copied_onto_itself(), test_s3_link_task_always_clocks_a_slot() (+14 more)

### Community 37 - "quizzes py"
Cohesion: 0.15
Nodes (19): Quiz, create_quiz(), get_quiz(), import_question_csv(), list_quizzes(), next_question(), parse_question_csv(), question_csv_template() (+11 more)

### Community 38 - "test user delete py"
Cohesion: 0.08
Nodes (13): accounts(), _create(), test_admin_cannot_create_super_admin(), test_admin_still_manages_teachers(), test_unknown_roles_rejected(), _exec(), _rows(), go() (+5 more)

### Community 39 - "test policy py"
Cohesion: 0.09
Nodes (13): _calls(), _routes(), test_every_route_is_governed_by_the_policy_or_listed(), test_no_role_comparisons_outside_the_policy(), test_published_permission_matrix_matches_the_code(), _refused(), _routes(), test_device_routes_reject_a_wrong_key() (+5 more)

### Community 40 - "test question import py"
Cohesion: 0.15
Nodes (22): _csv(), ctx(), _files(), import_(), parse(), questions(), test_any_invalid_row_means_nothing_is_imported(), test_database_failure_leaves_nothing_behind() (+14 more)

### Community 41 - "cJSON Delete"
Cohesion: 0.14
Nodes (30): batch_add(), batch_flush(), batch_flush_needed(), batch_init(), msg_to_json(), process_spi_payload(), spi_to_http_task(), wifi_client_is_connected() (+22 more)

### Community 42 - "protocol c"
Cohesion: 0.15
Nodes (27): crc16_ccitt(), json_get_string(), msg_decode(), msg_t, msg_verify_crc(), spi_record_read(), spi_record_write(), spi_slot_decode() (+19 more)

### Community 44 - "test class import py"
Cohesion: 0.16
Nodes (21): admin(), _count(), _csv(), _post(), test_admin_only(), test_any_invalid_row_means_nothing_is_imported(), test_brief_column_names_are_accepted(), test_conflicts_within_the_file() (+13 more)

### Community 45 - "test quiz timer py"
Cohesion: 0.17
Nodes (21): _get(), _mesh_answer(), _per_question(), _shift(), go(), _start(), test_http_answer_after_the_deadline_is_refused(), test_manual_and_unlimited_quizzes_are_never_advanced() (+13 more)

### Community 46 - "on ws command"
Cohesion: 0.13
Nodes (26): handle_class_assignment(), item_is_heartbeat(), on_ws_command(), ota_parse_check(), ota_prompt_target(), clamp_options(), num_item(), num_or() (+18 more)

### Community 47 - "cJSON Module"
Cohesion: 0.12
Nodes (29): cJSON, child, cJSON_DeleteItemFromArray(), cJSON_DeleteItemFromObject(), cJSON_DeleteItemFromObjectCaseSensitive(), cJSON_DetachItemFromArray(), cJSON_DetachItemFromObject(), cJSON_DetachItemFromObjectCaseSensitive() (+21 more)

### Community 48 - "ci with"
Cohesion: 0.17
Nodes (29): steps, steps, steps, steps, steps, steps, steps, steps (+21 more)

### Community 49 - "test device api py"
Cohesion: 0.13
Nodes (19): class_id_for_device(), _activity(), _device(), q(), _register(), su(), test_attendance_paths(), test_class_presence_snapshot_walks_gateway_tree() (+11 more)

### Community 50 - "test quiz poll lifecycle"
Cohesion: 0.11
Nodes (21): env(), _poll(), _quiz(), test_closed_poll_cannot_be_restarted_and_draft_cannot_be_ended(), test_completed_quiz_cannot_be_restarted(), test_draft_quiz_cannot_be_stopped(), test_impromptu_quiz_is_live_immediately(), test_list_quizzes_for_class() (+13 more)

### Community 51 - "firmware store py"
Cohesion: 0.13
Nodes (16): site_key_digest(), adopt_legacy_files(), artifact_file(), artifact_path(), resolve(), _signer(), store_dir(), store_upload() (+8 more)

### Community 52 - "api js"
Cohesion: 0.10
Nodes (19): adminApi, apiRequest(), authApi, classesApi, ClassSocket, classSocket, clearToken(), coursesApi (+11 more)

### Community 53 - "cJSON bool"
Cohesion: 0.18
Nodes (26): buffer_skip_whitespace(), cJSON_AddBoolToObject(), cJSON_bool, cJSON_Compare(), cJSON_CreateBool(), cJSON_ParseWithLength(), cJSON_ParseWithLengthOpts(), cJSON_ParseWithOpts() (+18 more)

### Community 54 - "json Group"
Cohesion: 0.13
Nodes (13): _next_device_frame(), _project(), test_device_socket_receives_firmware_contract(), append_coverage(), component_for(), enrich(), main(), node_id() (+5 more)

### Community 55 - "protocol h"
Cohesion: 0.11
Nodes (24): mesh_dedup_check(), mesh_dedup_t, mesh_msg_id(), ota_result_code_t, payload_heartbeat_t, payload_ota_prompt_t, payload_ota_result_t, payload_poll_start_t (+16 more)

### Community 56 - "csv import py"
Cohesion: 0.13
Nodes (12): question_warnings(), QuestionImportReport, QuestionImportRow, QuizQuestionCreate, csv_safe(), CsvFileError, _norm(), read_rows() (+4 more)

### Community 57 - "cJSON Library (ANSI C89"
Cohesion: 0.08
Nodes (21): impress_class_c6 ESP-IDF Project, EXTRA_COMPONENT_DIRS ../protocol, main ESP-IDF Component, cJSON v1.7.19 Changelog, cJSON Upstream CMake Build (v1.7.19), cjson_utils Library Target, cJSON Authors & Contributors, cJSON Fuzzing Targets (afl-main, fuzz_main) (+13 more)

### Community 58 - "test firmware registry py"
Cohesion: 0.13
Nodes (14): make_image(), _count(), h(), test_admin_only(), test_corrupted_image_is_detected_by_its_hash(), test_device_downloads_its_registered_image_with_its_hash(), test_facts_come_from_the_image_not_the_form(), test_identical_reupload_is_idempotent_and_different_bytes_conflict() (+6 more)

### Community 59 - "test ci workflow py"
Cohesion: 0.12
Nodes (16): _norm(), _on(), _steps_text(), test_actions_are_pinned_to_commit_shas(), test_backend_coverage_is_reported(), test_browser_ui_checks_run_in_ci(), test_ci_installs_the_hash_locked_dependency_set(), test_container_images_are_pinned_to_digests() (+8 more)

### Community 60 - "models QuizAnswer"
Cohesion: 0.16
Nodes (17): QuizAnswer, _count(), _fk_violations(), q(), _insert_twice(), go(), test_admin_class_delete_detaches_modules_linked_to_its_enrollments(), test_answers_without_identity_are_not_constrained() (+9 more)

### Community 61 - "tests test student modules"
Cohesion: 0.22
Nodes (20): StudentModule, _age(), q(), _batch(), beat(), join(), leave(), _modules() (+12 more)

### Community 62 - "os Group"
Cohesion: 0.11
Nodes (7): _stop(), init_env(), call(), env_value(), main(), main(), req_json()

### Community 63 - "test schedule occupancy py"
Cohesion: 0.16
Nodes (15): _add(), _busy(), phy(), su(), test_a_cancelled_day_frees_every_slot(), test_auris_rows_are_not_deleted_locally(), imported(), test_cancelled_moved_and_extra() (+7 more)

### Community 64 - "timeutil py"
Cohesion: 0.11
Nodes (8): _device_to_dict(), observe(), sweep(), _uid(), ist_epoch_ms(), ist_iso(), test_ist_epoch_ms_is_host_timezone_independent(), test_ist_iso_has_offset()

### Community 65 - "backend tests conftest py"
Cohesion: 0.12
Nodes (10): auth(), client(), _drain_background_tasks(), login(), make_class(), make_user(), _reset_db(), upload_firmware() (+2 more)

### Community 66 - "release with"
Cohesion: 0.15
Nodes (22): steps, steps, steps, steps, steps, steps, id, if (+14 more)

### Community 67 - "test secure defaults py"
Cohesion: 0.13
Nodes (9): check_secure(), insecure_settings(), Settings, _fresh_settings(), test_cors_only_configured_origins(), test_debug_and_sql_echo_off_by_default(), test_refuses_default_secrets_outside_debug(), test_unauthenticated_websockets_need_debug() (+1 more)

### Community 68 - "test device keys py"
Cohesion: 0.26
Nodes (16): _beat(), _device(), _key(), _register(), test_a_device_key_works_only_for_its_own_mac(), test_an_unused_key_is_replaced_so_a_lost_response_cannot_lock_the_device_out(), test_batch_messages_for_a_claimed_gateway_need_its_key(), test_direct_votes_only_for_the_callers_own_device() (+8 more)

### Community 69 - "device auth py"
Cohesion: 0.16
Nodes (8): generate_session_token(), api_key_ok(), _by_mac(), caller_for_key(), denial(), device_caller(), key_hash(), new_device_key()

### Community 70 - "ci jobs"
Cohesion: 0.10
Nodes (19): name, runs-on, timeout-minutes, concurrency, cancel-in-progress, group, name, runs-on (+11 more)

### Community 71 - "test super admin lockout"
Cohesion: 0.14
Nodes (10): _me(), su(), test_concurrent_mutual_deactivation_leaves_one_super_admin(), deactivate(), race(), test_database_refuses_removing_the_last_super_admin(), go(), test_no_self_lockout_on_any_route() (+2 more)

### Community 72 - "test ws auth py"
Cohesion: 0.15
Nodes (11): _rejected(), test_device_key_still_required(), test_gateway_key_joins_only_its_own_class(), test_inactive_user_rejected(), deactivate(), test_teacher_after_logout_rejected(), test_teacher_cannot_join_another_teachers_class(), test_teacher_with_bad_token_rejected() (+3 more)

### Community 73 - "test manage cli py"
Cohesion: 0.17
Nodes (9): main(), restore_super_admin(), _lock_out(), _restore(), _sql(), test_cli_exit_codes(), test_promotes_an_existing_account(), test_restores_a_locked_out_installation() (+1 more)

### Community 74 - "schedule py"
Cohesion: 0.18
Nodes (8): _at(), Busy, find_schedule_conflicts(), occupancy(), _same_academic_window(), schedule_is_current(), _span(), test_same_academic_window_rules()

### Community 75 - "ui tests conftest py"
Cohesion: 0.13
Nodes (5): Api, browser(), _free_port(), page(), server()

### Community 76 - "pytest Group"
Cohesion: 0.18
Nodes (10): git(), tracked_files(), workflow(), _on(), test_generated_graph_is_valid_meaningful_and_covers_impress_components(), test_generated_output_has_no_local_paths_or_secret_values(), test_official_graphify_cli_is_available_when_graph_workflow_runs(), test_workflow_actions_are_pinned_and_generation_is_before_publish() (+2 more)

### Community 77 - "test trusted installer py"
Cohesion: 0.21
Nodes (12): _artifact(), _deploy(), _download(), h(), _register(), strict(), test_a_database_edit_to_approved_is_not_enough(), test_a_tampered_file_is_never_served() (+4 more)

### Community 78 - "test admin users py"
Cohesion: 0.12
Nodes (5): _import(), su(), test_create_user_field_limits(), test_csv_import_admin_rows_need_super_admin(), test_csv_import_inserts_valid_rows_and_reports_bad_ones()

### Community 79 - "quiz timer py"
Cohesion: 0.23
Nodes (8): advance(), answer_closed(), deadline(), finish(), tick(), time_limit_s(), _transition(), race()

### Community 80 - "appveyor yml"
Cohesion: 0.11
Nodes (17): build_script, ps, configuration, environment, matrix, GENERATOR, platform, matrix (+9 more)

### Community 81 - "test students py"
Cohesion: 0.12
Nodes (4): _csv(), su(), test_csv_import_mixed_rows(), test_enrollment_number_must_be_10_alphanumerics()

### Community 82 - "test firmware manager py"
Cohesion: 0.24
Nodes (12): _artifact(), h(), _hub(), _push(), _set(), test_admin_only(), test_deletion_keeps_anything_a_device_needs(), test_deprecated_images_are_not_pushed_but_in_flight_updates_finish() (+4 more)

### Community 83 - "test firmware signing py"
Cohesion: 0.20
Nodes (10): _digest(), h(), site_key(), test_a_foreign_key_is_refused_but_a_second_signature_by_the_site_key_counts(), test_an_unreadable_site_key_is_reported(), test_real_signatures_verify_and_the_key_digest_matches_espsecure(), test_unsigned_images_from_before_are_not_deployed_once_signing_is_required(), test_with_a_site_key_only_images_it_signed_are_accepted() (+2 more)

### Community 84 - "test c6 diagnostics py"
Cohesion: 0.16
Nodes (7): _raw(), _schema_fields(), test_heartbeat_sends_every_diagnostic_the_schema_accepts(), test_reset_reason_names_cover_the_crash_rules(), test_s3_link_tracks_only_the_s3s_own_heartbeat(), test_docs_build_inputs_are_pinned_and_valid_python(), test_readthedocs_configuration_uses_reproducible_sphinx_build()

### Community 86 - "test login throttle py"
Cohesion: 0.17
Nodes (10): clock(), test_another_username_is_not_affected(), test_counters_survive_a_restart(), test_existing_passwords_keep_working(), test_one_address_guessing_many_usernames_is_slowed(), test_sixth_failure_waits_and_the_password_is_not_checked(), test_success_resets_the_username_counter(), test_the_wait_doubles_then_ends() (+2 more)

### Community 87 - "REST API Reference"
Cohesion: 0.14
Nodes (13): Auth & Session Endpoints (/api/auth/*), REST API Reference, Firmware Registry & Deployments Endpoints (/api/admin/firmware, /deployments), Quizzes & Polls Endpoints (/api/quizzes, /api/polls), Authorization Model (policy.py), Privilege Rings (TrustedInstaller, Root, super_admin, admin, teacher, student), Root Integrity Rules (LAST_SUPER_ADMIN, SELF_LOCKOUT, FORBIDDEN_TARGET), AURIS Timetable & Room Occupancy (Fail-Closed) (+5 more)

### Community 88 - "strip comments and strings"
Cohesion: 0.14
Nodes (8): strip_comments_and_strings(), test_connection_failures_say_why(), test_every_backend_client_gets_the_tls_settings(), test_version_comes_from_the_image(), test_app_rollback_enabled(), test_detach_unregisters_reconnect_handler_before_disconnecting(), test_new_image_marked_valid_only_after_mesh_and_spi_init(), test_only_a_successful_install_reboots()

### Community 89 - "test student set c"
Cohesion: 0.31
Nodes (10): find(), student_set_count(), student_set_init(), student_set_join(), student_set_leave(), student_set_root_uptime(), test_capacity_and_bad_input(), test_heartbeats_do_not_count_students() (+2 more)

### Community 90 - "test transport py"
Cohesion: 0.15
Nodes (4): _https(), strict(), test_a_reverse_proxy_counts_as_https(), test_https_works_and_gets_hsts()

### Community 91 - "test device batch dedup"
Cohesion: 0.30
Nodes (10): answer(), batch(), count(), test_distinct_students_and_questions_all_count(), test_inactive_quiz_and_closed_poll_skipped(), test_invalid_answers_skipped(), test_relay_copies_in_one_batch_and_across_batches_stored_once(), test_stored_answers_broadcast_live_counts() (+2 more)

### Community 92 - "release env"
Cohesion: 0.19
Nodes (15): BRANCH, CREATE, DEFAULT_BRANCH, EVENT, GH_TOKEN, LINE, NAME, OWNER (+7 more)

### Community 93 - "release outputs"
Cohesion: 0.13
Nodes (15): plan, asset, create, line, owner, previous, publish, sha (+7 more)

### Community 94 - "test health py"
Cohesion: 0.21
Nodes (6): health(), _dev(), test_heartbeat_stores_diagnostics_and_old_firmware_still_works(), test_invalid_diagnostics_are_rejected(), test_precedence_offline_over_updating_over_error_over_degraded(), test_rules()

### Community 95 - "test user lifecycle api"
Cohesion: 0.19
Nodes (6): _row(), su(), test_allowed_actions_for_a_super_admin(), test_allowed_actions_for_an_admin(), test_hidden_actions_are_refused_by_the_server(), test_patch_edits_profile_only()

### Community 96 - "Device API (Gateway <"
Cohesion: 0.18
Nodes (11): POST /api/device/batch, Device API (Gateway <-> Backend), Device Health States (UNKNOWN/OFFLINE/UPDATING/ERROR/DEGRADED/ONLINE), Device API Key Lifecycle (Shared vs Per-Device), Device OTA Endpoints (firmware/check, download, ota/status), Presence Snapshot & Student Modules Inventory, WebSocket API (/ws/class/{class_id}), Device WebSocket Contract (device_ws_frames.json) (+3 more)

### Community 97 - "test_release FakeGitHub"
Cohesion: 0.19
Nodes (10): FakeGitHub, _release(), test_a_new_release_is_published_with_its_status_section(), test_an_exact_patch_milestone_also_gates(), test_closing_a_2_1_issue_updates_every_release_built_on_2_1(), test_image_tags_per_owner_and_line(), test_inherited_issues_are_marked_with_their_line(), test_sync_changes_nothing_when_already_correct() (+2 more)

### Community 98 - "models QuizQuestion"
Cohesion: 0.24
Nodes (9): QuizQuestion, _history(), fill(), statements(), test_class_list_counts_without_loading_quizzes(), test_loading_a_user_is_one_statement(), load(), test_positions_are_unique_per_quiz() (+1 more)

### Community 99 - "test hardware requirements py"
Cohesion: 0.18
Nodes (6): _cfg(), _partitions_end(), test_flash_table_matches_partitions_and_headers(), test_psram_is_optional_on_the_hub(), test_student_capacity_matches_on_hub_and_gateway(), test_profile_verifies_updates_without_hardware_secure_boot()

### Community 100 - "firmware build"
Cohesion: 0.17
Nodes (13): strategy, container, name, runs-on, strategy, timeout-minutes, arch, runner (+5 more)

### Community 101 - "release firmware"
Cohesion: 0.15
Nodes (13): container, if, name, needs, runs-on, strategy, timeout-minutes, arch (+5 more)

### Community 102 - "test session revocation py"
Cohesion: 0.24
Nodes (8): _ok(), su(), test_admin_password_reset_logs_the_user_out(), test_open_teacher_socket_is_closed_on_deactivation(), test_own_password_change_keeps_only_the_current_session(), test_profile_edit_does_not_revoke(), test_reactivation_does_not_revive_old_tokens(), test_role_change_revokes_sessions()

### Community 103 - "test install scripts py"
Cohesion: 0.29
Nodes (7): _backend(), test_ci_runs_the_install_path(), test_existing_values_are_kept_and_missing_ones_added(), test_fresh_env_gets_random_secrets_never_the_defaults(), test_two_installs_get_different_secrets(), test_version_file_is_semver_and_matches_the_firmware(), _values()

### Community 104 - "test device limits py"
Cohesion: 0.21
Nodes (6): cls(), _quiz(), test_backend_limits_match_the_firmware_frame(), test_long_text_is_accepted_with_truncation_warnings(), test_poll_options_limited_to_the_four_buttons(), test_quiz_options_limited_to_the_four_buttons()

### Community 105 - "accounts py"
Cohesion: 0.20
Nodes (4): account_refusal(), forbidden(), allowed_actions(), error()

### Community 106 - "imPress Documentation Map"
Cohesion: 0.17
Nodes (10): End-to-End Data Flows, Hub OTA Update End-to-End Flow, Quiz Question & Answer End-to-End Flow, Caddy HTTPS Reverse Proxy & /data Volume, Container Image Deployment (impress-backend), Deployment Index, Design Decisions Record (D1-D15), imPress Documentation Map (+2 more)

### Community 107 - "ci result"
Cohesion: 0.17
Nodes (12): BASE, EVENT, LABELS, RESULTS, result, if, name, needs (+4 more)

### Community 108 - "release image"
Cohesion: 0.21
Nodes (12): permissions, name, needs, permissions, runs-on, timeout-minutes, image, contents (+4 more)

### Community 109 - "readthedocs yaml"
Cohesion: 0.17
Nodes (11): build, os, tools, requirements, python, install, sphinx, configuration (+3 more)

### Community 110 - "test ota download gating"
Cohesion: 0.27
Nodes (6): device(), set_pending(), dl(), test_download_requires_device_key(), test_no_pending_ota_means_no_download(), test_only_the_pushed_version_downloads()

### Community 111 - "test gateway autolink py"
Cohesion: 0.36
Nodes (7): _class(), _gateway_of(), _register(), test_explicit_classroom_code_still_assigns(), test_gateway_keeps_its_class_on_reregister(), test_non_gateway_registration_keeps_class_gateway(), test_second_gateway_takes_next_free_class()

### Community 112 - "test quiz correct option"
Cohesion: 0.25
Nodes (5): _create(), ctx(), test_boundaries_accepted(), test_negative_still_rejected(), test_out_of_range_rejected()

### Community 113 - "ESP32 C6 Classroom Gateway"
Cohesion: 0.24
Nodes (8): Hardware Deployment & E2E Integration Test Task, S3-to-C6 SPI 4096-Byte Frame Contract, ESP32-C6 Classroom Gateway, ESP32-S3 Classroom Hub, FastAPI Backend & SQLite Store, Shared C Wire Protocol (firmware/protocol), SPI 10 MHz 4 KB Slot Link, Student Module (ESP32)

### Community 114 - "System Overview Architecture"
Cohesion: 0.27
Nodes (9): C6 SPI Slave Model & spi2http Task, Firmware Architecture, S3 Hub Tasks (spi_link, s3_ota, routing table), Student Module State Machine & Identity Store, C6 Gateway (ESP32-C6, firmware/class_c6), System Overview Architecture, FastAPI Backend (backend/app), S3 Hub / Mesh Root (ESP32-S3, firmware/class_s3) (+1 more)

### Community 115 - "travis yml"
Cohesion: 0.18
Nodes (10): addons, apt, packages, compiler, dist, env, matrix, language (+2 more)

### Community 116 - "espressif esp websocket client"
Cohesion: 0.18
Nodes (10): dependencies, idf, description, version, repository, repository_info, commit_sha, path (+2 more)

### Community 117 - "ci container"
Cohesion: 0.18
Nodes (11): env, name, runs-on, timeout-minutes, IMPRESS_INITIAL_ADMIN_PASSWORD, env, name, runs-on (+3 more)

### Community 118 - "release jobs"
Cohesion: 0.18
Nodes (10): concurrency, cancel-in-progress, group, env, IMAGE, PYTHON_VERSION, RELEASE_OWNERS, jobs (+2 more)

### Community 121 - "Import Courses and Sections"
Cohesion: 0.22
Nodes (8): Course and Section CSV Column Schema, Existing Sections Conflict Policy Dropdown, Import Courses and Sections Panel, Line-by-Line CSV Validation Preview Table, CSV Courses and Sections Import Invalid Preview UI, Inactive or Unknown Teacher Username Error, Invalid Academic Term Enum Error, Row Validation Summary Pills

### Community 122 - "Deploy s3 v2 2"
Cohesion: 0.27
Nodes (10): Modal Action Buttons, Batch Size Input, Canary Devices Input, At Once (Max) Concurrency Input, Devices Target Selector, Failures Allowed Per Stage Input, Deploy s3 v2.2.0 Modal Dialog, Allow Downgrading (Rollback) Checkbox (+2 more)

### Community 123 - "espressif cjson idf component"
Cohesion: 0.20
Nodes (9): dependencies, idf, description, repository, repository_info, commit_sha, path, url (+1 more)

### Community 124 - "release on"
Cohesion: 0.20
Nodes (10): types, on, issues, schedule, workflow_dispatch, workflow_run, cron, branches (+2 more)

### Community 127 - "test class create py"
Cohesion: 0.28
Nodes (3): _stored(), test_create_class_with_exam_dates_persists_them(), test_create_class_without_exam_dates()

### Community 128 - "test class join py"
Cohesion: 0.42
Nodes (6): _class(), _teacher(), test_co_faculty_cannot_delete_class(), test_join_adds_co_faculty_and_keeps_owner(), test_join_errors(), test_join_is_idempotent_and_owner_join_is_noop()

### Community 130 - "test firmware upload py"
Cohesion: 0.28
Nodes (3): _activity(), test_firmware_upload_succeeds_and_is_logged(), test_s3_ota_push_prompts_gateway_and_logs()

### Community 131 - "Deployments List UI Screenshot"
Cohesion: 0.25
Nodes (9): C6 Gateway Firmware Card, Deployment #1 (s3 v2.2.0 Paused), Deployments List Card, Firmware Upload Dropzone, Monospace Card & Pill Badge Design Pattern, S3 Hub Firmware Card, Deployments List UI Screenshot (Firmware Page), Sidebar Navigation (+1 more)

### Community 132 - "Changelog v2 1"
Cohesion: 0.42
Nodes (9): Classroom Node Requirements, Device Compatibility Matrix, Changelog v2.1, Changelog v2, Hardware Reference, Known Issues and Limitations, v2.1 Release Notes Template, Hardware Validation Plan (+1 more)

### Community 133 - "test_release repo"
Cohesion: 0.28
Nodes (8): _repo(), g(), test_ancestry_is_read_from_git(), test_first_release_of_a_line_is_patch_zero(), test_patch_counts_pushes_since_the_owners_line_tag(), test_plan_refuses_feature_branches(), test_template_falls_back_to_the_default_branch(), test_the_branch_name_decides_the_line()

### Community 134 - "test firmware py"
Cohesion: 0.32
Nodes (4): _open(), test_invalid_upload_is_explained(), test_signature_status_is_shown(), test_upload_approve_and_push_from_modules()

### Community 135 - "CSV Questions Import Invalid"
Cohesion: 0.29
Nodes (7): CSV File Dropzone and Template Download Header, Case-Insensitive Duplicate Question Detection (line 5 skipped as duplicate of line 2), Line-by-Line Question Validation Preview Table, Inline Row Validation Error (correct_option 'E' must be A-D or 1-4), CSV Column and Size Constraints (UTF-8, max 500 rows / 1 MB), CSV Questions Import Invalid State UI Screenshot, Row Validation Summary Pills (4 rows, 2 valid, 1 invalid, 1 duplicate)

### Community 136 - "CSV Questions Import &"
Cohesion: 0.36
Nodes (8): CSV File Dropzone, Confirm & Discard Footer Actions, Non-Destructive Preview-Before-Commit Pattern, Variable Option Count Support (2-4 Options), CSV Questions Import & Preview UI, Question Preview Table, Download Template Action, Validation Summary Pills

### Community 137 - "Firmware Page UI"
Cohesion: 0.32
Nodes (8): Approval-Gated Firmware Lifecycle, C6 Gateway Firmware Section, S3 Hub Firmware Section, Firmware Page UI, Sidebar Navigation, Student Module Firmware Section, Toast Notifications, Upload Firmware Image Card

### Community 138 - "Student Modules Telemetry Table"
Cohesion: 0.32
Nodes (7): Example Seen-Only Module (0000BEEF / FGHIJ67890), Example Connected Module (1A2B3C4D / ABCDE12345), Module Search and Filter Toolbar, Gateway Room 201, Connected Count Summary Pill (1/2 connected), Student Modules Seen by Gateways UI Panel, Student Modules Telemetry Table

### Community 139 - "sbom cJSON yml"
Cohesion: 0.25
Nodes (7): cpe, description, hash, name, supplier, url, version

### Community 140 - "image build"
Cohesion: 0.25
Nodes (8): if, name, needs, runs-on, strategy, timeout-minutes, image-build, fail-fast

### Community 141 - ".cz commitizen"
Cohesion: 0.29
Nodes (6): commitizen, bump_message, pre_bump_hooks, tag_format, version, version_files

### Community 142 - "protocol Common Component"
Cohesion: 0.29
Nodes (7): impress_class_s3 CMake Project, class_s3 main Component, class_s3 Version 2.1.0, protocol Common Component, impress_student CMake Project, student main Component, student Version 2.1.0

### Community 143 - "test_quiz_timer env"
Cohesion: 0.33
Nodes (3): env(), add_student(), pause_scheduler()

### Community 144 - "Telemetry Key Value Table"
Cohesion: 0.40
Nodes (6): Refresh & Close Modal Controls, Health & S3 Link Status Badges, Heartbeat Telemetry Metrics, Telemetry Key-Value Table Layout, Diagnostics Modal (Room 102), Read-Only & Firmware v2.1+ Notice

### Community 145 - "class c6 main idf"
Cohesion: 0.33
Nodes (5): dependencies, espressif/cjson, espressif/esp_websocket_client, description, version

### Community 146 - "idf_component dependencies"
Cohesion: 0.33
Nodes (5): dependencies, espressif/esp_websocket_client, protocol_examples_common, version, path

### Community 147 - "release Module"
Cohesion: 0.33
Nodes (6): release, if, name, needs, runs-on, timeout-minutes

### Community 148 - "release status"
Cohesion: 0.33
Nodes (6): status, if, name, needs, runs-on, timeout-minutes

### Community 151 - "Backend Architecture"
Cohesion: 0.40
Nodes (4): Backend Background Tasks (presence_sweep_loop, session_cleanup_loop), ConnectionManager (In-Memory WebSocket Rooms), Backend Architecture, SQLite Persistence & Versioned Migrations

### Community 152 - "Shared Protocol Library (firmware"
Cohesion: 0.40
Nodes (4): Shared Protocol Library (firmware/protocol), ESP-IDF v6.1 Build Environment Blocker, Protocol Host Static Validation, Hardware Integration Test Report (2026-10-13)

### Community 153 - "Firmware Push Dialog UI"
Cohesion: 0.50
Nodes (5): Target Hub Metadata (s3, running v0.0.0), Approved Firmware Selector Dropdown, Approved OTA Firmware Push Workflow, Push Update Primary CTA Button, Firmware Push Dialog UI Screenshot

### Community 154 - "cjson_read_fuzzer LLVMFuzzerTestOneInput"
Cohesion: 0.60
Nodes (5): cJSON_Print(), cJSON_PrintBuffered(), cJSON_PrintUnformatted(), main(), LLVMFuzzerTestOneInput()

### Community 155 - "ci env"
Cohesion: 0.40
Nodes (5): env, FORCE_COLOR, NODE_VERSION, PIP_DISABLE_PIP_VERSION_CHECK, PYTHON_VERSION

### Community 156 - "firmware signed"
Cohesion: 0.40
Nodes (5): container, name, runs-on, timeout-minutes, firmware-signed

### Community 157 - "ci on"
Cohesion: 0.40
Nodes (5): on, pull_request, push, workflow_dispatch, branches

### Community 159 - "Python Served Vanilla JS"
Cohesion: 0.50
Nodes (4): Quiz & Poll Timing Modes, Python-Served Vanilla JS SPA Architecture, Main Web App SPA Shell (index.html), Legacy React + Vite SPA Entry (frontend/index.html)

### Community 160 - "Backend Runtime Dependencies (requirements"
Cohesion: 0.67
Nodes (4): Backend Dev & Audit Dependencies (requirements-dev.txt), Hash-Locked Dependency Manifest (requirements-lock.txt), Backend Runtime Dependencies (requirements.txt), Playwright UI Test Dependencies (ui_tests/requirements.txt)

### Community 162 - "Contributing & Maintenance Policy"
Cohesion: 0.50
Nodes (4): imPress Changelog (v2.0 - v2.1.3 & Unreleased), imPress Code of Conduct, Contributing & Maintenance Policy, Unified Test Runner (run_tests.py)

### Community 164 - "Room Capacity Limit (300"
Cohesion: 0.50
Nodes (3): Gateway Node (ESP32-C6), Room Capacity Limit (300 Students), Hub Node (ESP32-S3)

### Community 165 - "ci changelog"
Cohesion: 0.50
Nodes (4): name, runs-on, timeout-minutes, changelog

### Community 166 - "ci docs"
Cohesion: 0.50
Nodes (4): name, runs-on, timeout-minutes, docs

### Community 167 - "firmware static"
Cohesion: 0.50
Nodes (4): name, runs-on, timeout-minutes, firmware-static

### Community 168 - "ci repo"
Cohesion: 0.50
Nodes (4): repo, name, runs-on, timeout-minutes

### Community 169 - "ci security"
Cohesion: 0.50
Nodes (4): security, name, runs-on, timeout-minutes

### Community 170 - "ci ui"
Cohesion: 0.50
Nodes (4): ui, name, runs-on, timeout-minutes

## Knowledge Gaps
- **118 isolated node(s):** `next`, `prev`, `child`, `type`, `valuestring` (+113 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1435 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **74 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `istnow()` connect `timeutil istnow` to `models User`, `main py`, `services deployments py`, `migrations py`, `test e2e ota py`, `routers auth py`, `models py`, `models EspDevice`, `models ClassSession`, `tests test deployments py`, `test core utils py`, `firmware py`, `quizzes py`, `test device api py`, `tests test student modules`, `timeutil py`, `device auth py`, `test ws auth py`, `schedule py`, `quiz timer py`, `test login throttle py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 128 inferred relationships involving `User` (e.g. with `create_session()` and `get_current_user()`) actually correct?**
  _`User` has 128 INFERRED edges - model-reasoned connections that need verification._
- **What connects `next`, `prev`, `child` to the rest of the system?**
  _118 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `models User` be split into smaller, more focused modules?**
  _Cohesion score 0.05524752475247525 - nodes in this community are weakly interconnected._
- **Why does `User` connect `models User` to `main py`, `firmware py`, `models QuizQuestion`, `services deployments py`, `quizzes py`, `test policy py`, `test super admin lockout`, `test manage cli py`, `accounts py`, `schemas py`, `test class import py`, `timeutil istnow`, `test ws auth py`, `routers auth py`, `models py`, `models ClassSession`, `students py`, `courses py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 71 inferred relationships involving `EspDevice` (e.g. with `_by_mac()` and `caller_for_key()`) actually correct?**
  _`EspDevice` has 71 INFERRED edges - model-reasoned connections that need verification._
- **Should `main py` be split into smaller, more focused modules?**
  _Cohesion score 0.04695304695304695 - nodes in this community are weakly interconnected._