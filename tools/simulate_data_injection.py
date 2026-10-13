import urllib.request
import json
import sys

BASE_URL = "http://192.168.137.155:8000"

def req_json(path, data=None, token=None, method="GET"):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        print(f"HTTP {e.code} on {method} {path}: {err}", file=sys.stderr)
        raise

def main():
    print("[1] Authenticating as admin...")
    login = req_json("/api/auth/login", {"username": "admin", "password": "dev-admin"}, method="POST")
    token = login["access_token"]
    print("Token obtained successfully.")

    # 1. Faculty
    print("\n[2] Ensuring 2 Faculty members exist...")
    users = req_json("/api/admin/users", token=token)
    user_map = {u["username"]: u for u in users}

    if "fac.mehta" in user_map:
        fac1 = user_map["fac.mehta"]
    else:
        fac1 = req_json("/api/admin/users", {
            "username": "fac.mehta", "email": "mehta@impress.test",
            "password": "Lab-Fac1-2026!x", "full_name": "Dr. R. Mehta", "role": "teacher"
        }, token=token, method="POST")

    if "fac.iyer" in user_map:
        fac2 = user_map["fac.iyer"]
    else:
        fac2 = req_json("/api/admin/users", {
            "username": "fac.iyer", "email": "iyer@impress.test",
            "password": "Lab-Fac2-2026!x", "full_name": "Dr. S. Iyer", "role": "teacher"
        }, token=token, method="POST")
    print(f"Faculty: {fac1['full_name']} (ID {fac1['id']}), {fac2['full_name']} (ID {fac2['id']})")

    # 2. Courses
    print("\n[3] Ensuring 2 Courses exist...")
    courses = req_json("/api/courses/", token=token)
    course_map = {c["code"]: c for c in courses}

    if "PHY101" in course_map:
        course1 = course_map["PHY101"]
    else:
        course1 = req_json("/api/courses/", {
            "code": "PHY101", "name": "Engineering Physics", "credits": 4, "department": "Physics"
        }, token=token, method="POST")

    if "CSE102" in course_map:
        course2 = course_map["CSE102"]
    else:
        course2 = req_json("/api/courses/", {
            "code": "CSE102", "name": "Embedded Systems", "credits": 3, "department": "CSE"
        }, token=token, method="POST")
    print(f"Courses: {course1['code']} (ID {course1['id']}), {course2['code']} (ID {course2['id']})")

    # 3. Students
    print("\n[4] Registering 10 Students...")
    existing_students = req_json("/api/students/", token=token)
    existing_rolls = {s["roll_number"]: s for s in existing_students}

    students_payload = [
        {"roll_number": "IMP2026A01", "student_name": "Asha Rao", "program": "B.Tech", "enrollment_year": 2026, "device_mac": "84:1F:E8:1B:73:90"},
        {"roll_number": "IMP2026A02", "student_name": "Vikram Shah", "program": "B.Tech", "enrollment_year": 2026},
        {"roll_number": "IMP2026A03", "student_name": "Neha Patel", "program": "B.Tech", "enrollment_year": 2026},
        {"roll_number": "IMP2026A04", "student_name": "Arjun Nair", "program": "B.Tech", "enrollment_year": 2026},
        {"roll_number": "IMP2026A05", "student_name": "Priya Das", "program": "B.Tech", "enrollment_year": 2026},
        {"roll_number": "IMP2026A06", "student_name": "Rohan Gupta", "program": "B.Tech", "enrollment_year": 2026},
        {"roll_number": "IMP2026A07", "student_name": "Kavya Menon", "program": "B.Tech", "enrollment_year": 2026},
        {"roll_number": "IMP2026A08", "student_name": "Imran Khan", "program": "B.Tech", "enrollment_year": 2026},
        {"roll_number": "IMP2026A09", "student_name": "Sara Joseph", "program": "B.Tech", "enrollment_year": 2026},
        {"roll_number": "IMP2026A10", "student_name": "Dev Malhotra", "program": "B.Tech", "enrollment_year": 2026}
    ]

    to_create = [s for s in students_payload if s["roll_number"] not in existing_rolls]
    if to_create:
        req_json("/api/admin/students/bulk", {"students": to_create}, token=token, method="POST")
        print(f"Bulk registered {len(to_create)} new students.")
    else:
        print("All 10 students already registered.")

    all_students = req_json("/api/students/", token=token)
    sim_students = [s for s in all_students if s["roll_number"].startswith("IMP2026A")]
    sim_students.sort(key=lambda s: s["roll_number"])
    print(f"Verified {len(sim_students)} simulation students in database.")

    # 4. Classroom
    print("\n[5] Ensuring Classroom (PHY101A / RM-001) exists...")
    all_classes = req_json("/api/admin/classes", token=token)
    class_map = {c["code"]: c for c in all_classes}

    if "PHY101A" in class_map:
        classroom = class_map["PHY101A"]
        print(f"Classroom PHY101A already exists (ID {classroom['id']}).")
    else:
        cls_payload = {
            "name": "Engineering Physics - Sec A",
            "code": "PHY101A",
            "subject": "Physics",
            "course_id": course1["id"],
            "course_section": "A",
            "year": 2026,
            "teacher_ids": [fac1["id"], fac2["id"]],
            "classroom_code": "RM-001",
            "location": "Block A, Room 001",
            "capacity": 6
        }
        classroom = req_json("/api/admin/classes", cls_payload, token=token, method="POST")
        print(f"Classroom created: {classroom['name']} (ID {classroom['id']}, Room {classroom['classroom_code']})")

    # 5. Assignment Logic: 6 students
    print("\n[6] Executing Assignment Logic: Enrolling 6 students...")
    assigned_6 = sim_students[:6]
    assigned_ids = [s["id"] for s in assigned_6]
    print(f"Assigning students to Room {classroom.get('classroom_code', 'RM-001')}: {[s['roll_number'] for s in assigned_6]}")
    enroll_result = req_json(f"/api/admin/classes/{classroom['id']}/enroll-bulk", {"student_ids": assigned_ids}, token=token, method="POST")
    print(f"Enrollment response: {enroll_result}")

    # 6. Activate Class
    print("\n[7] Activating Classroom session...")
    act_res = req_json(f"/api/classes/{classroom['id']}/activate", token=token, method="POST")
    print(f"Class activation status: {act_res.get('status', 'active')}")

    print("\n" + "="*50)
    print("[SUCCESS] PHASE 1 COMPLETE: DATA MODELING & INJECTION VERIFIED")
    print("="*50)
    print(f"Active Class ID   : {classroom['id']}")
    print(f"Class Code        : {classroom['code']}")
    print(f"Classroom Code    : {classroom.get('classroom_code', 'RM-001')}")
    print(f"Enrolled Count    : {enroll_result.get('count', 6)}")
    print(f"Physical Target   : Roll IMP2026A01 | Name: Asha Rao | MAC: 84:1F:E8:1B:73:90")

if __name__ == "__main__":
    main()
