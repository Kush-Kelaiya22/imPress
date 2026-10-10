# imPress Frontend

The frontend is a **Python-served single-page app** — no Node.js, no build step.

FastAPI serves:

- **`GET /`** → `app/templates/index.html` (the SPA shell, via Jinja2)
- **`/static/**`** → `app/static/css/style.css`, `app/static/js/api.js`, `app/static/js/app.js`
- Any other **non-API** path falls through to the same SPA shell (hash-based routing handles the pages)

All dynamic behaviour is client-side vanilla JS hitting the REST + WebSocket API.

## Access model

The web frontend is **admin/faculty only**. Students never log in — they
interact through their **ESP32 devices** on the mesh.

- **Central super admin** (seeded as `admin` / `admin123`) can create **other
  admins** and teachers. Admins can create teachers and classes.
- **Admin** creates classes (`#/admin/classes`) and assigns each to a faculty
  member. Faculty see **only their assigned classes**.
- **Any user's account** is created by an admin — there is **no public
  registration**; the web app shows login only.
- **Faculty / admin** register students into classes (teacher: from the class
  detail page; admin: from `#/admin/students`). Students' ESP32 devices link by
  MAC address, and check-in via the C6 gateway (`POST /api/device/attendance`).
- WebSocket connections from the dashboard use `role=teacher`; the C6 gateway
  uses its own upstream (HTTP + WS handled by firmware).

## Pages (hash-routed)

| Route                          | Page                                                                      |
|--------------------------------|---------------------------------------------------------------------------|
| `#/login`                      | Sign in (no registration — accounts are admin-created)                    |
| `#/dashboard`                  | Faculty: assigned classes + stats. Admin: redirects to `#/admin`          |
| `#/classes`                    | Faculty list of assigned classes                                          |
| `#/class?id=N`                 | Class detail: quizzes, polls, students, live WS feed                      |
| `#/quiz?class_id=N`            | Create quiz — planned/impromptu + timing (manual / per_question / total)  |
| `#/quiz-results?id=N`          | Per-question bar chart results                                            |
| `#/poll?class_id=N`            | Create poll — live or planned                                             |
| `#/poll-results?id=N`          | Vote bar chart results                                                    |
| `#/student?id=N&class=C`       | Individual student participation summary (quizzes/polls/attendance)       |
| `#/admin`                      | Admin dashboard (stats + quick actions + recent activity)                 |
| `#/admin/users`                | Create/deactivate users (super admin can create admins)                   |
| `#/admin/classes`              | Create classes and assign teachers                                        |
| `#/admin/students`             | Per-class student roster + registration                                   |
| `#/admin/activity`             | Full activity / audit log                                                 |

## Quiz & poll behaviour

- **Quiz modes**: `planned` (saved as draft, faculty presses ▶ Start to go
  live) or `impromptu` (created live instantly — on-the-spot quiz).
- **Timing modes**: `manual` (faculty advances questions with Next),
  `per_question` (the server advances after fixed seconds per question),
  `total` (the server ends the quiz after one countdown). Next and Stop are
  offered in every mode; a quiz the timer ends switches to Results live.
  Devices receive the question + `time_limit_s` over WS.
- **Poll modes**: `live` (starts immediately) or `planned` (draft until
  faculty starts it).
- All state changes (`quiz.start`, `poll.end`, `student.register`,
  `class.assign_teacher`, …) are recorded in the `activity_logs` table and
  visible in `#/admin/activity`.

## Files

```
backend/app/
├── templates/
│   └── index.html          # SPA shell (Jinja2)
└── static/
    ├── css/style.css       # design tokens; light/dark; v2 admin/faculty components
    └── js/
        ├── api.js          # REST client (auth/admin/classes/quizzes/polls) + ClassSocket
        └── app.js          # hash router + page renderers
```

## Backend routers

- `routers/auth.py`      — login + me (registration removed; admin-only now)
- `routers/admin.py`     — users, classes + teacher assignment, students, activity logs
- `routers/classes.py`   — faculty's assigned classes, activate/deactivate
- `routers/quizzes.py`   — quizzes with modes + timing
- `routers/polls.py`     — polls with modes
- `routers/device.py`    — ESP32 register / heartbeat / attendance / batch
- `activity.py`          — `log_activity()` helper used across routers
- `auth.py`              — JWT + `require_admin` / `require_super_admin` / `require_teacher_or_admin`

## Running

```bash
cd backend
.venv/Scripts/python -m uvicorn app.main:app --port 8000
# open http://localhost:8000       admin / admin123 (change in production)
```

> **Note:** the earlier React frontend in `frontend/` is superseded by this
> Python-served frontend and kept for reference only.