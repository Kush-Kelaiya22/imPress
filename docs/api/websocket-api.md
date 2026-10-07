# WebSocket API

One room per class: **`ws(s)://<host>/ws/class/{class_id}?role=teacher|device`**. Both roles share the room; the server routes some events to teachers only.

## Connecting

| Role | Credentials | Rejected with |
|---|---|---|
| `teacher` | `?token=<login session token>`, validated exactly like the REST API (revoked, idle- or hard-expired, inactive user → reject); role must be teacher/admin/super_admin | close **4401** |
| `device` | `X-API-Key: <device key>` header (preferred), or legacy `?api_key=` | close **4401** |
| anything else | – | close **4400** |

With `IMPRESS_WS_REQUIRE_AUTH=false` (debug only) any `teacher`/`device` connection is accepted.

On success the server sends:
```json
{"event": "connected", "class_id": 7, "role": "teacher", "message": "Connected to class 7 as teacher"}
```

Opening a socket **doesn't** extend the teacher's session (`refresh_activity=False`).

## Server → client events

Every frame has `type` (the vanilla SPA dispatches on it). Frames the C6 gateway and the React UI need also carry **`event`**.

| `event` | `type` | Payload | Sent when | Audience |
|---|---|---|---|---|
| `quiz_question` | `quiz_question` | `quiz_id, title, question_order, total_questions, question_text, options, timing_mode, time_limit, time_limit_s` | quiz started, `next`, impromptu create | everyone |
| `quiz_end` | `quiz_ended` | `quiz_id, title` | stop, or `next` past the last question | everyone |
| `poll_start` | `poll_started` | `poll_id, title, options` | live poll created, planned poll started | everyone |
| `poll_end` | `poll_ended` | `poll_id, title, option_counts, total_votes` | poll ended | everyone |
| – | `quiz_answer` | `quiz_id, question_order, total_answers` (+ `device_id` from the HTTP route) | an answer stored | everyone |
| – | `poll_vote` | `poll_id, selected_option, total_votes` (+ `device_id`) | a vote stored | everyone |
| `presence` | `presence` | `data`: [presence snapshot](device-api.md#presence-snapshot) | device online/offline, heartbeats, device WS messages | **teachers only** |
| `device_command` | – | `command, payload` (e.g. `ota_update {version, device_type, mac_address}`) | admin OTA push, teacher `broadcast_command` | everyone (the C6 acts on it) |
| `student_data` | – | `data` | a device sent `device_data` | everyone |
| `pong` | – | – | reply to `ping` | the sender |

### Firmware contract
The keys the C6 reads are pinned in `firmware/contract/device_ws_frames.json`:
```json
[{"event": "quiz_question", "quiz_id": 1, "question_order": 0, "question_text": "2+2?", "options": ["3","4","5","6"], "time_limit_s": 30},
 {"event": "quiz_end", "quiz_id": 1},
 {"event": "poll_start", "poll_id": 1, "title": "Lab on Friday?", "options": ["Yes","No","Maybe"]},
 {"event": "poll_end", "poll_id": 1}]
```
`backend/tests/test_device_ws_contract.py` regenerates and compares this against real server output; `firmware/class_c6/test_host/test_ws_command.c` decodes the same file through the firmware translator. **Don't rename these keys** without updating both (see [decision D5](../design/decisions.md#d5-the-backend--firmware-json-contract-is-a-committed-fixture)).

## Client → server messages

| Message | From | Effect |
|---|---|---|
| `{"event": "ping"}` | any | `{"event": "pong"}` |
| `{"event": "broadcast_command", "command": "...", "payload": {...}}` | teacher (any role in practice) | re-broadcast as `device_command` |
| `{"event": "device_data", "data": {...}}` | device | re-broadcast as `student_data` |
| any message | device | refreshes that gateway's presence (`last_seen`, battery, RSSI) |
| unknown event | any | logged and ignored |

Malformed JSON closes the socket.

## Client guidance

- **Reconnect** with backoff. The server holds no per-socket state beyond room membership.
- After a reconnect, fetch the current state over REST (`GET /api/quizzes/{id}`, `/results`, `/api/classes/{id}/presence`): events are not replayed.
- Browsers can't set WebSocket headers, so the teacher token is in the query string. **Use `wss://`** and keep access logs free of query strings at the proxy.
