"""Realistic, unique, internally consistent test data (v2.2 test mode).

`generate(seed, counts, taken)` returns one list of rows per sheet:

  teachers -> courses -> students -> classes -> enrollments -> quizzes -> polls

Every reference points at something that exists (in the same data or in
`taken`, what the database already has), and every unique value is unique
across both: usernames, e-mails, course and class codes, room codes and
enrollment numbers. Timetables don't double-book a room or a teacher. The same
seed always gives the same data; a different seed, different data.

Values look natural rather than random: names from regional and international
name pools, departments with their own course catalogues and question banks,
roll numbers in the institution's format (year + programme + serial), Monday/
Wednesday/Friday or Tuesday/Thursday slots in teaching hours, and students
taking the courses of their own programme first.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta

# ── Pools ────────────────────────────────────────────────────────────────

FIRST = [
    "Aarav", "Aditi", "Aditya", "Akash", "Ananya", "Anika", "Anjali", "Arjun", "Aryan", "Avni", "Diya", "Dhruv",
    "Gauri", "Ishaan", "Ishita", "Kabir", "Kavya", "Krish", "Lakshmi", "Meera", "Mihir", "Naina", "Neha", "Nikhil",
    "Pooja", "Pranav", "Priya", "Rahul", "Riya", "Rohan", "Saanvi", "Sahil", "Sanjana", "Shreya", "Siddharth",
    "Sneha", "Tanvi", "Tara", "Varun", "Vihaan", "Yash", "Zara", "Farhan", "Ayesha", "Imran", "Sana", "Kiran",
    "Harpreet", "Gurleen", "Manish", "Deepa", "Suresh", "Lavanya", "Karthik", "Divya", "Arvind", "Nandini",
    "Joel", "Maria", "Daniel", "Sarah", "Wei", "Mei", "Hiro", "Yuki", "Omar", "Leila", "Lucas", "Sofia",
]
LAST = [
    "Sharma", "Verma", "Iyer", "Nair", "Reddy", "Rao", "Patel", "Shah", "Mehta", "Kapoor", "Khanna", "Malhotra",
    "Gupta", "Agarwal", "Bose", "Banerjee", "Chatterjee", "Das", "Ghosh", "Mukherjee", "Pillai", "Menon",
    "Kulkarni", "Joshi", "Deshpande", "Patil", "Singh", "Gill", "Sandhu", "Khan", "Qureshi", "Siddiqui",
    "Fernandes", "D'Souza", "Thomas", "Mathew", "Krishnan", "Subramanian", "Venkatesh", "Hegde", "Shetty",
    "Chen", "Wang", "Tanaka", "Sato", "Haddad", "Garcia", "Silva", "Martin",
]

DEPARTMENTS = {
    "CSE": ("Computer Science and Engineering", "B.Tech CSE", [
        ("Introduction to Programming", 4), ("Data Structures", 4), ("Algorithms", 4), ("Database Systems", 3),
        ("Operating Systems", 4), ("Computer Networks", 3), ("Software Engineering", 3),
        ("Machine Learning", 3), ("Computer Architecture", 3), ("Theory of Computation", 3)]),
    "ECE": ("Electronics and Communication Engineering", "B.Tech ECE", [
        ("Circuit Theory", 4), ("Digital Electronics", 4), ("Signals and Systems", 4), ("Analog Electronics", 3),
        ("Microprocessors", 3), ("Communication Systems", 3), ("Embedded Systems", 3), ("VLSI Design", 3)]),
    "MEC": ("Mechanical Engineering", "B.Tech ME", [
        ("Engineering Mechanics", 4), ("Thermodynamics", 4), ("Fluid Mechanics", 4), ("Strength of Materials", 3),
        ("Manufacturing Processes", 3), ("Machine Design", 3), ("Heat Transfer", 3)]),
    "MAT": ("Mathematics", "B.Sc Mathematics", [
        ("Calculus", 4), ("Linear Algebra", 4), ("Probability and Statistics", 4), ("Discrete Mathematics", 3),
        ("Differential Equations", 3), ("Numerical Methods", 3), ("Real Analysis", 3)]),
    "PHY": ("Physics", "B.Sc Physics", [
        ("Mechanics", 4), ("Electricity and Magnetism", 4), ("Optics", 3), ("Quantum Physics", 4),
        ("Thermal Physics", 3), ("Modern Physics", 3)]),
}

# Which CSE questions belong to which course (others: any course of the department).
TOPICS = {
    "Introduction to Programming": ("stack", "git", "binary search", "fifo"),
    "Data Structures": ("fifo", "stack", "binary search tree", "traversal", "lifo"),
    "Algorithms": ("binary search", "sorting", "dijkstra", "merge"),
    "Database Systems": ("sql", "normal form"),
    "Operating Systems": ("page table", "deadlock"),
    "Computer Networks": ("tcp/ip", "transport"),
    "Software Engineering": ("git",),
}

BANK = {
    "CSE": [
        ("Which data structure follows the FIFO principle?", ["Stack", "Queue", "Binary tree", "Hash table"], 1),
        ("What is the worst-case time of binary search on n sorted items?", ["O(1)", "O(log n)", "O(n)", "O(n log n)"], 1),
        ("Which traversal of a binary search tree visits keys in sorted order?", ["Preorder", "Inorder", "Postorder", "Level order"], 1),
        ("A stack uses which ordering?", ["FIFO", "LIFO", "Priority", "Random"], 1),
        ("Which sorting algorithm has O(n log n) average time and is stable?", ["Quick sort", "Merge sort", "Selection sort", "Heap sort"], 1),
        ("Which SQL clause filters groups after aggregation?", ["WHERE", "HAVING", "ORDER BY", "LIMIT"], 1),
        ("What does a page table translate?", ["Virtual to physical addresses", "IP to MAC", "Names to IPs", "Files to inodes"], 0),
        ("Which layer of TCP/IP provides reliable delivery?", ["Application", "Transport", "Internet", "Link"], 1),
        ("A deadlock needs mutual exclusion, hold and wait, no preemption and…", ["Starvation", "Circular wait", "Paging", "Thrashing"], 1),
        ("Which normal form removes transitive dependencies?", ["1NF", "2NF", "3NF", "4NF"], 2),
        ("Dijkstra's algorithm fails with…", ["Cycles", "Negative edge weights", "Dense graphs", "Unweighted graphs"], 1),
        ("In Git, which command records staged changes?", ["git add", "git commit", "git push", "git fetch"], 1),
    ],
    "ECE": [
        ("Ohm's law relates voltage, current and…", ["Power", "Resistance", "Charge", "Frequency"], 1),
        ("A NAND gate outputs 0 only when…", ["Any input is 0", "All inputs are 1", "All inputs are 0", "Inputs differ"], 1),
        ("The Nyquist rate for a 4 kHz band-limited signal is…", ["2 kHz", "4 kHz", "8 kHz", "16 kHz"], 2),
        ("Which device is voltage-controlled?", ["BJT", "MOSFET", "Diode", "Thyristor"], 1),
        ("A flip-flop stores…", ["One bit", "One byte", "An analog value", "Nothing"], 0),
        ("Amplitude modulation varies the carrier's…", ["Frequency", "Phase", "Amplitude", "Wavelength"], 2),
        ("The unit of capacitance is the…", ["Henry", "Farad", "Ohm", "Tesla"], 1),
        ("A low-pass filter passes…", ["High frequencies", "Low frequencies", "Only DC", "No signal"], 1),
    ],
    "MEC": [
        ("The first law of thermodynamics is a statement of conservation of…", ["Mass", "Energy", "Momentum", "Entropy"], 1),
        ("Bernoulli's equation applies along a streamline for flow that is…", ["Viscous", "Inviscid", "Turbulent", "Compressible only"], 1),
        ("Young's modulus is the ratio of stress to…", ["Strain", "Force", "Area", "Time"], 0),
        ("Which process removes material with a rotating multi-point tool?", ["Turning", "Milling", "Casting", "Forging"], 1),
        ("Heat transfer through a solid wall is mainly…", ["Radiation", "Convection", "Conduction", "Advection"], 2),
        ("A Carnot engine's efficiency depends on…", ["Working fluid", "Reservoir temperatures", "Pressure only", "Size"], 1),
        ("The unit of torque is…", ["N/m", "N·m", "J/s", "Pa"], 1),
    ],
    "MAT": [
        ("The derivative of sin x is…", ["cos x", "-cos x", "tan x", "sec x"], 0),
        ("A square matrix is invertible exactly when its determinant is…", ["0", "Non-zero", "1", "Positive"], 1),
        ("The probability of two independent events both occurring is…", ["Sum", "Product", "Difference", "Maximum"], 1),
        ("How many subsets does a set of 4 elements have?", ["4", "8", "16", "24"], 2),
        ("The integral of 1/x dx is…", ["x²/2", "ln|x| + C", "1/x²", "e^x"], 1),
        ("Eigenvalues of a symmetric real matrix are…", ["Complex", "Real", "Zero", "Negative"], 1),
        ("The mean of 2, 4, 6, 8 is…", ["4", "5", "6", "20"], 1),
    ],
    "PHY": [
        ("Newton's second law states F equals…", ["mv", "ma", "mg/h", "p/v"], 1),
        ("The speed of light in vacuum is about…", ["3 × 10⁵ m/s", "3 × 10⁸ m/s", "3 × 10¹⁰ m/s", "340 m/s"], 1),
        ("Snell's law describes…", ["Reflection", "Refraction", "Diffraction", "Polarisation"], 1),
        ("The photoelectric effect shows that light has…", ["Wave nature", "Particle nature", "No energy", "Mass"], 1),
        ("The SI unit of magnetic field is the…", ["Weber", "Tesla", "Gauss", "Henry"], 1),
        ("Entropy of an isolated system…", ["Decreases", "Never decreases", "Is zero", "Oscillates"], 1),
    ],
}

POLLS = [
    ("How was the pace of today's lecture?", ["Too slow", "Just right", "Too fast"]),
    ("Which topic should we revise next class?", ["Last week's topic", "Today's topic", "Exam problems", "Nothing, move on"]),
    ("Did the lab exercise work for you?", ["Yes", "Partly", "No"]),
    ("Preferred format for the next tutorial?", ["Problem solving", "Live coding/demo", "Q&A", "Quiz"]),
    ("How confident are you with this unit?", ["Very", "Somewhat", "Not yet"]),
]

SLOTS = [("09:00", "10:00"), ("10:15", "11:15"), ("11:30", "12:30"), ("13:30", "14:30"), ("14:45", "15:45"),
         ("16:00", "17:00")]
PATTERNS = [("Monday", "Wednesday", "Friday"), ("Tuesday", "Thursday"), ("Monday", "Wednesday"),
            ("Tuesday", "Friday")]
BUILDINGS = ["A", "B", "C", "L"]
DOMAIN = "example.edu"            # a reserved domain: no real mailbox


@dataclass
class Taken:
    """Values already in the database (or rows the user typed)."""
    usernames: set = field(default_factory=set)
    emails: set = field(default_factory=set)
    course_codes: set = field(default_factory=set)
    class_codes: set = field(default_factory=set)
    rooms: set = field(default_factory=set)
    rolls: set = field(default_factory=set)
    teachers: list = field(default_factory=list)       # existing teacher usernames, used when none are generated


DEFAULT_COUNTS = {"teachers": 8, "courses": 10, "students": 120, "classes": 12, "classes_per_student": 3,
                  "quizzes_per_class": 2, "questions_per_quiz": 4, "polls_per_class": 1, "past_share": 0.6}
LIMITS = {"teachers": 200, "courses": 200, "students": 5000, "classes": 300, "classes_per_student": 8,
          "quizzes_per_class": 10, "questions_per_quiz": 12, "polls_per_class": 5}


def _serial(n: int) -> str:
    """Three characters: 001-999, then base 36 (A00…): a roll stays 10 long."""
    if n <= 999:
        return f"{n:03d}"
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    n += 36 ** 2 * 10 - 1000                       # continue after "9ZZ" -> "A00"
    out = ""
    for _ in range(3):
        out = digits[n % 36] + out
        n //= 36
    return out


def _unique(base: str, taken: set, rng: random.Random, sep: str = "") -> str:
    v, n = base, 1
    while v.lower() in taken:
        n += 1
        v = f"{base}{sep}{n}"
    taken.add(v.lower())
    return v


def _person(rng: random.Random, used_names: set) -> tuple[str, str]:
    for _ in range(50):
        first, last = rng.choice(FIRST), rng.choice(LAST)
        if (first, last) not in used_names:
            used_names.add((first, last))
            return first, last
    first, last = rng.choice(FIRST), rng.choice(LAST)
    return first, last


def generate(seed: int, counts: dict | None = None, taken: Taken | None = None, today: date | None = None) -> dict:
    c = {**DEFAULT_COUNTS, **(counts or {})}
    for k, lim in LIMITS.items():
        c[k] = max(0, min(int(c[k]), lim))
    rng = random.Random(seed)
    taken = taken or Taken()
    t_users, t_emails = set(taken.usernames), set(taken.emails)
    t_courses, t_classes, t_rooms, t_rolls = set(taken.course_codes), set(taken.class_codes), set(taken.rooms), set(taken.rolls)
    today = today or date.today()
    names: set = set()
    depts = list(DEPARTMENTS)

    # Teachers: Dr./Prof., a home department each.
    teachers = []
    for i in range(c["teachers"]):
        first, last = _person(rng, names)
        dept = depts[i % len(depts)] if i < len(depts) else rng.choice(depts)
        username = _unique(f"{first[0]}{last}".lower().replace("'", ""), t_users, rng)
        email = _unique(f"{first}.{last}".lower().replace("'", ""), t_emails, rng, ".") + f"@{DOMAIN}"
        title = rng.choice(["Dr.", "Prof.", "Dr.", "Dr."])
        teachers.append({"username": username, "full_name": f"{title} {first} {last}", "email": email,
                         "department": DEPARTMENTS[dept][0], "_dept": dept})

    # Courses: from each department's catalogue, codes like CSE201.
    courses = []
    catalogue = [(d, name, credits, n) for d in depts for n, (name, credits) in enumerate(DEPARTMENTS[d][2])]
    rng.shuffle(catalogue)
    catalogue.sort(key=lambda x: x[3])               # introductory courses first, mixed departments
    for d, name, credits, n in catalogue[:c["courses"]]:
        level = 100 * (1 + min(n // 3, 3))
        code = _unique(f"{d}{level + rng.randint(1, 49):03d}", t_courses, rng)
        courses.append({"code": code, "name": name, "credits": credits, "department": DEPARTMENTS[d][0],
                        "description": f"{name}: core course of the {DEPARTMENTS[d][0]} programme.", "_dept": d})

    # Students: roll = intake year + department + serial (10 characters).
    students = []
    year_now = today.year
    serials: dict = {}
    for _ in range(c["students"]):
        first, last = _person(rng, names) if len(names) < len(FIRST) * len(LAST) - 10 else (rng.choice(FIRST), rng.choice(LAST))
        d = rng.choices(depts, weights=[5, 3, 2, 2, 2])[0]
        intake = year_now - rng.choice([0, 1, 1, 2, 2, 3])
        while True:
            serials[(intake, d)] = serials.get((intake, d), 0) + 1
            roll = f"{intake}{d}{_serial(serials[(intake, d)])}"
            if roll.lower() not in t_rolls:
                t_rolls.add(roll.lower())
                break
        email = _unique(f"{first}.{last}{str(intake)[2:]}".lower().replace("'", ""), t_emails, rng, ".") + f"@{DOMAIN}"
        students.append({"roll_number": roll, "student_name": f"{first} {last}", "email": email,
                         "program": DEPARTMENTS[d][1], "enrollment_year": intake, "graduation_year": intake + 4,
                         "_dept": d})

    # Classes: sections of courses; each in its own room; no room or teacher clash.
    classes = []
    if courses and (teachers or taken.teachers):
        busy_teacher: dict = {}
        term = "Monsoon" if 7 <= today.month <= 12 else "Winter"
        start = today - timedelta(days=rng.randint(21, 45))
        for i in range(c["classes"]):
            course = courses[i % len(courses)]
            section = "AB"[(i // len(courses)) % 2] if i >= len(courses) else "A"
            pool = ([t for t in teachers if t["_dept"] == course["_dept"]] or teachers
                    or [{"username": u, "_dept": course["_dept"]} for u in taken.teachers])
            pattern, slot = None, None
            for _ in range(60):
                teacher = rng.choice(pool) if pool else None
                pattern, slot = rng.choice(PATTERNS), rng.choice(SLOTS)
                key = teacher["username"] if teacher else ""
                if all((key, d, slot) not in busy_teacher for d in pattern):
                    break
            for d in pattern:
                busy_teacher[(teacher["username"] if teacher else "", d, slot)] = True
            room = _unique(f"RM-{rng.choice(BUILDINGS)}{rng.randint(1, 4)}{rng.randint(1, 30):02d}", t_rooms, rng, "-")
            code = _unique(f"{course['code']}-{section}", t_classes, rng)
            others = [t["username"] for t in pool if teacher and t["username"] != teacher["username"]]
            co = rng.sample(others, 1) if others and rng.random() < 0.25 else []
            classes.append({
                "code": code, "name": course["name"], "course_code": course["code"], "section": section,
                "term": term, "year": today.year, "teacher_username": teacher["username"] if teacher else "",
                "co_faculty": ",".join(co), "classroom_code": room,
                "location": f"Room {room[3:]}, Block {room[3]}", "capacity": rng.choice([40, 48, 60, 72]),
                "days": ",".join(d[:3] for d in pattern), "start": slot[0], "end": slot[1],
                "start_date": start.isoformat(), "end_date": (start + timedelta(weeks=15)).isoformat(),
                "_dept": course["_dept"]})

    # Enrollments: own programme first, then electives; capacity respected.
    enrollments = []
    seats = {cl["code"]: cl["capacity"] for cl in classes}
    by_dept: dict = {}
    for cl in classes:
        by_dept.setdefault(cl["_dept"], []).append(cl)
    for st in students:
        want = min(c["classes_per_student"], len(classes))
        own = [cl for cl in by_dept.get(st["_dept"], []) if seats[cl["code"]] > 0]
        rng.shuffle(own)
        rest = [cl for cl in classes if cl not in own and seats[cl["code"]] > 0]
        rng.shuffle(rest)
        chosen, courses_taken = [], set()
        for cl in own + rest:
            if len(chosen) >= want:
                break
            if cl["course_code"] in courses_taken:            # one section per course
                continue
            chosen.append(cl)
            courses_taken.add(cl["course_code"])
            seats[cl["code"]] -= 1
        enrollments += [{"roll_number": st["roll_number"], "class_code": cl["code"]} for cl in chosen]

    # Quizzes: one row per question, from the department's bank; earlier ones completed.
    quizzes = []
    for cl in classes:
        keys = TOPICS.get(cl["name"], ())
        topical = [b for b in BANK[cl["_dept"]] if any(k in b[0].lower() for k in keys)]
        general = [b for b in BANK[cl["_dept"]] if b not in topical]
        for q in range(c["quizzes_per_class"]):
            rng.shuffle(topical)
            rng.shuffle(general)
            bank = topical + general                # the course's own topics first
            week = q + 1 + rng.randint(0, 2)
            title = f"Week {week} check: {cl['name']}"
            status = "completed" if rng.random() < c["past_share"] else "draft"
            for text_, options, correct in bank[:min(c["questions_per_quiz"], len(bank))]:
                opts = list(options) + [""] * (4 - len(options))
                quizzes.append({"class_code": cl["code"], "title": title, "status": status, "question_text": text_,
                                "option_a": opts[0], "option_b": opts[1], "option_c": opts[2], "option_d": opts[3],
                                "correct": "ABCD"[correct]})

    polls = []
    for cl in classes:
        for title, options in rng.sample(POLLS, min(c["polls_per_class"], len(POLLS))):
            polls.append({"class_code": cl["code"], "title": title, "options": " | ".join(options),
                          "status": "closed" if rng.random() < c["past_share"] else "draft"})

    strip = lambda rows: [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]  # noqa: E731
    return {"teachers": strip(teachers), "courses": strip(courses), "students": strip(students),
            "classes": strip(classes), "enrollments": enrollments, "quizzes": quizzes, "polls": polls}
