# Data flows

Each section follows one user-visible action through every hop. Function names are given so you can jump straight into the code.

## 1. Teacher signs in and opens the live dashboard

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser (SPA)
    participant API as Backend
    participant DB as SQLite
    B->>API: POST /api/auth/login {username, password}
    API->>DB: verify bcrypt hash · INSERT user_sessions(token_hash = sha256(token))
    API-->>B: {access_token: "impress_…", idle_timeout_s, hard_timeout_s}
    Note over B: stored in localStorage
    B->>API: WS /ws/class/{id}?role=teacher&token=…
    API->>DB: validate_session(token, refresh_activity=False)
    API-->>B: {"event":"connected","role":"teacher"}
    loop every few seconds
        B->>API: GET /api/auth/session-status   (never extends the session)
    end
```

## 2. Teacher starts a quiz question → it appears on every module

```mermaid
sequenceDiagram
    autonumber
    participant T as Teacher
    participant API as Backend (quizzes.py)
    participant C6 as C6 gateway
    participant S3 as S3 hub
    participant ST as Student modules
    T->>API: POST /api/quizzes/{id}/start
    API->>API: status=active, current_question=0 · commit
    API-->>C6: WS {"event":"quiz_question","quiz_id","question_order","question_text","options","time_limit_s",…}
    API-->>T: same frame (UIs) + HTTP 200
    C6->>C6: on_ws_command → ws_command_to_frame → MSG_QUIZ_QUESTION<br/>(options clamped to 4)
    C6->>C6: spi_slave_send(frame) · raise READY C6→S3
    S3->>C6: READY edge IRQ → spi_link clocks one 4 KB slot
    S3->>S3: handle_c6_frame → mesh_master_broadcast (TTL 5, sender 0)
    S3--)ST: ESP-NOW broadcast
    ST--)ST: students relay (TTL 4…1), each copy de-duplicated
    ST->>ST: mesh_rx_task → on_mesh_message → OLED shows question, state QUIZ_ACTIVE
```

`POST /next` repeats steps 1–9 with the next `question_order`. Stopping, or calling `next` past the last question, sends `quiz_end`, which students turn into `MSG_QUIZ_END` and go back to `IDLE`. Polls use the same path with `poll_start` / `poll_end`.

## 3. A student answers → the teacher's count goes up

```mermaid
sequenceDiagram
    autonumber
    participant ST as Student
    participant RL as Other students (relays)
    participant S3 as S3 hub
    participant C6 as C6 gateway
    participant API as Backend (device.py)
    participant T as Teacher
    ST->>ST: button B → MSG_QUIZ_ANSWER {quiz_id, question_num, selected_option=1, enrollment}
    ST--)S3: ESP-NOW (direct, TTL 5)
    ST--)RL: same broadcast
    RL--)S3: relayed copies (TTL 4, 3, …)
    S3->>S3: on_espnow_recv: CRC ok → routing table update →<br/>mesh_dedup_check → first copy queued, the rest dropped
    S3->>C6: spi_link: spi_record_write [len][sender_id][frame] → SPI slot
    C6->>C6: spi2http: spi_record_read → msg_decode → JSON {"type":"quiz_answer",…}
    C6->>C6: batch (≤ 20 items / 500 ms)
    C6->>API: POST /api/device/batch (X-API-Key)
    API->>API: _record_quiz_answer: known student? active quiz? valid question and option? not answered yet?
    API->>API: INSERT quiz_answers · commit
    API-->>T: WS {"type":"quiz_answer","quiz_id","question_order","total_answers":n}
    API-->>C6: {"status":"ok","processed":1,"skipped":0}
```

Answers that fail a check are counted in `skipped` and never stored: unknown enrollment, inactive quiz, unknown question, option out of range, or a duplicate.

## 4. A student module joins the mesh

```mermaid
sequenceDiagram
    autonumber
    participant ST as Student
    participant S3 as S3 hub
    participant C6 as C6
    participant API as Backend
    loop every 2 s until connected (max 30 s)
        ST--)S3: MSG_STUDENT_JOIN {enrollment, device_id}
    end
    S3->>S3: find_or_create_student (routing table)
    S3--)ST: root MSG_HEARTBEAT (TTL 5)  — sent for EVERY join, even retries
    ST->>ST: sender_id == 0 → IS_CONNECTED, hop count learned → IDLE
    S3->>C6: first JOIN copy → SPI
    C6->>API: batch {"type":"student_join","enrollment_number",…}
    API->>API: ActivityLog student.connect (+ enrollment if class code known)
    Note over S3: no traffic for 60 s → sweep → MSG_STUDENT_LEAVE → "student.disconnect"
```

## 5. Device presence (online/offline)

```mermaid
sequenceDiagram
    autonumber
    participant C6 as C6
    participant API as Backend
    participant SW as presence_sweep_loop (15 s)
    participant T as Teacher sockets
    C6->>API: POST /register · /heartbeat (15 s) · /ping (120 s) · any WS message
    API->>API: last_seen = now · mark_online (logs esp_device.online only on offline→online)
    API--)T: _push_after_commit → presence snapshot (role = teacher)
    SW->>API: devices with last_seen older than 30 s
    API->>API: mark_offline (logs esp_device.offline once)
    API--)T: presence snapshot
```

The snapshot is the class gateway plus its relay tree (BFS over `gateway_id`), each device with `online = is_connected and last_seen ≤ 30 s`.

## 6. Firmware update of a hub (OTA)

```mermaid
sequenceDiagram
    autonumber
    participant A as Admin
    participant API as Backend
    participant C6 as C6
    participant S3 as S3
    A->>API: POST /api/admin/firmware/upload (s3, 1.2.0, .bin)
    A->>API: POST /api/admin/modules/{s3}/ota {"version":"1.2.0"}
    API->>API: pending_version = 1.2.0 · audit log
    API-->>C6: WS {"event":"device_command","command":"ota_update","payload":{"version":"1.2.0",…}}
    C6->>S3: MSG_OTA_PROMPT over SPI
    S3->>S3: s3_ota task: join Wi-Fi (mesh keeps running)
    S3->>API: POST /register · /heartbeat · /firmware/check
    API-->>S3: {"update_available":true,"version":"1.2.0"}
    S3->>API: GET /firmware/download?mac&version=1.2.0  (only the pending version is served)
    S3->>S3: esp_ota_write → esp_ota_end → set_boot_partition
    S3->>C6: MSG_OTA_APPLIED · reboot
    S3->>S3: first boot: PENDING_VERIFY → mesh + SPI ok → mark valid
    Note over S3: crash before mark-valid → bootloader rolls back.<br/>Nothing pending / failure → detach Wi-Fi, back on the mesh channel, no reboot.
```

## 7. Class assignment of a gateway

| Situation | Result |
|---|---|
| `register` with a `classroom_code` matching a class's `code` or `classroom_code` | that class's gateway := this device |
| `register` without a code, device already linked | keeps its class |
| `register` without a code, `device_type = c6`, not linked | first **active** class **without a gateway** |
| any other device type without a code (S3 OTA hop, student) | never links (issue #17) |
| WS `connected` / `connect_to_class` with a new class id | C6 saves it to NVS; the `app_main` loop restarts the WS on its own task (#5) |
