"""One-time migration: convert legacy naive-UTC timestamps to naive IST.

Prior to the IST rollout the backend stored ``datetime.utcnow()`` (naive UTC)
in all DateTime columns. Those values are reinterpreted by the new IST-aware
code as IST wall-clock, so every such value is 5h30m behind. This script shifts
them by +05:30 in place.

Only columns that were populated via ``utcnow()`` are touched. Calendar
Date/Time fields (exam dates, class start/end, section times) are left alone.

Run from backend/ with the venv python:
    .venv/Scripts/python.exe migrate_utc_to_ist.py
"""
import sqlite3
from datetime import datetime, timedelta

SHIFT = timedelta(hours=5, minutes=30)
FMT = "%Y-%m-%d %H:%M:%S.%f"

# table -> datetime columns that were utcnow() defaults
DATETIME_COLUMNS = {
    "users": ["created_at"],
    "courses": ["created_at"],
    "esp_devices": ["last_seen", "registered_at", "ota_requested_at", "verified_at"],
    "class_sessions": ["created_at"],
    "students": ["registered_at"],
    "activity_logs": ["timestamp"],
    "student_enrollments": ["enrolled_at"],
    "quizzes": ["created_at", "started_at", "ended_at"],
    "polls": ["created_at", "started_at", "ended_at"],
    "quiz_answers": ["submitted_at"],
    "poll_votes": ["submitted_at"],
    "attendance": ["check_in_time"],
    "user_sessions": ["created_at", "last_activity_at", "expires_at"],
}


def _shift(value):
    if value is None or value == "":
        return value
    try:
        dt = datetime.strptime(value, FMT)
    except ValueError:
        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return value  # not a datetime we recognize — leave it
    return (dt + SHIFT).strftime(FMT)


def main():
    con = sqlite3.connect("impress.db")
    total = 0
    for table, cols in DATETIME_COLUMNS.items():
        try:
            existing = {r[1] for r in con.execute(f'PRAGMA table_info("{table}")')}
        except sqlite3.Error:
            continue
        table_rows = 0
        for col in cols:
            if col not in existing:
                continue
            rows = con.execute(f'SELECT rowid, "{col}" FROM "{table}"').fetchall()
            for rowid, val in rows:
                new_val = _shift(val)
                if new_val != val:
                    con.execute(f'UPDATE "{table}" SET "{col}" = ? WHERE rowid = ?', (new_val, rowid))
                    table_rows += 1
        if table_rows:
            print(f"{table}: shifted {table_rows} value(s)")
            total += table_rows
    con.commit()
    con.close()
    print(f"DONE — {total} datetime values shifted UTC -> IST (+05:30)")


if __name__ == "__main__":
    main()