"""SQLAlchemy ORM models for imPress."""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text, JSON, Table
)
from sqlalchemy.orm import relationship
from .database import Base
from .timeutil import istnow


# ── Users ────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(128), default="")
    role = Column(String(16), default="teacher")  # "super_admin" | "admin" | "teacher"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=istnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    classes = relationship("ClassSession", back_populates="teacher", lazy="selectin", foreign_keys="ClassSession.teacher_id")
    taught_classes = relationship("ClassSession", secondary="class_faculty", back_populates="faculty", lazy="selectin")


# ── Courses (universal catalog) ──────────────────────────────────────

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(16), unique=True, nullable=False, index=True)  # e.g. "CS101"
    name = Column(String(128), nullable=False)
    description = Column(Text, default="")
    credits = Column(Integer, default=0)
    department = Column(String(64), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=istnow)
    # Exam scheduling at course level (not per classroom section)
    exam_date = Column(Date, nullable=True)          # single exam date
    exam_start_time = Column(String(8), nullable=True)  # HH:MM format (e.g. "09:00")
    exam_end_time = Column(String(8), nullable=True)    # HH:MM format (e.g. "12:00")

    sections = relationship("ClassSession", back_populates="course", lazy="selectin")


# ── Class Sessions / Classrooms ──────────────────────────────────────

class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    subject = Column(String(128), default="")
    code = Column(String(32), unique=True, nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("esp_devices.id"), nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=istnow)

    # Classroom metadata (universal course + section + schedule)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    course_section = Column(String(16), default="")  # e.g. "A", "01"
    term = Column(String(16), default="")  # Monsoon | Winter | Summer
    year = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)   # instruction / class start
    end_date = Column(Date, nullable=True)     # instruction end (before exams)
    exam_start_date = Column(Date, nullable=True)  # exams begin
    exam_end_date = Column(Date, nullable=True)    # exams end
    meeting_schedule = Column(JSON, default=list)  # [{day, start, end}, ...]
    location = Column(String(128), default="")  # "Room 301, Block B"
    capacity = Column(Integer, default=0)
    classroom_code = Column(String(32), unique=True, nullable=True, index=True)  # physical room label, e.g. "RM-201"

    teacher = relationship("User", back_populates="classes", foreign_keys=[teacher_id], lazy="selectin")
    faculty = relationship("User", secondary="class_faculty", back_populates="taught_classes", lazy="selectin")
    creator = relationship("User", foreign_keys=[created_by], lazy="selectin")
    device = relationship("EspDevice", back_populates="class_session", lazy="selectin")
    course = relationship("Course", back_populates="sections", lazy="selectin")
    quizzes = relationship("Quiz", back_populates="class_session", lazy="selectin")
    polls = relationship("Poll", back_populates="class_session", lazy="selectin")
    attendance = relationship("Attendance", back_populates="class_session", lazy="selectin")
    enrollments = relationship("StudentEnrollment", back_populates="class_session", lazy="selectin")


# ── ESP Devices ──────────────────────────────────────────────────────

class EspDevice(Base):
    __tablename__ = "esp_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mac_address = Column(String(17), unique=True, nullable=False, index=True)
    device_name = Column(String(64), default="")
    device_type = Column(String(16), default="c6")  # "c6" (class node) | "s3" | "student"
    student_name = Column(String(128), default="")
    battery_pct = Column(Integer, default=100)
    rssi = Column(Integer, default=0)
    last_seen = Column(DateTime, default=istnow)
    registered_at = Column(DateTime, default=istnow)

    # Node connectivity (R7: not physical tracking — just linked/unlinked)
    is_connected = Column(Boolean, default=False)      # currently linked to its class node / gateway
    gateway_id = Column(Integer, ForeignKey("esp_devices.id"), nullable=True)  # node that relays this device
    is_active = Column(Boolean, default=True)          # access control (admin can disable)

    # Student enrollment link (for student nodes)
    student_enrollment_id = Column(Integer, ForeignKey("student_enrollments.id"), nullable=True)
    student_enrollment = relationship("StudentEnrollment", lazy="selectin")
    device_id = Column(Integer, nullable=True)  # device_id from firmware (enrollment number as uint32)

    # Firmware / OTA (R8: admin can push updates; device polls)
    firmware_version = Column(String(32), default="0.0.0")
    pending_version = Column(String(32), default="")
    ota_status = Column(String(16), default="idle")    # idle | downloading | applied | failed
    ota_requested_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)      # admin "verify" stamp

    # Telemetry from classroom node heartbeat
    student_count = Column(Integer, default=0)
    free_heap = Column(Integer, nullable=True)
    total_flash = Column(Integer, nullable=True)

    class_session = relationship("ClassSession", back_populates="device",
                                 lazy="selectin", uselist=False)
    relayed_by = relationship("EspDevice", remote_side=[id], foreign_keys=[gateway_id])


# ── Class Faculty Association (many-to-many) ───────────────────────────

class_faculty = Table(
    "class_faculty",
    Base.metadata,
    Column("class_session_id", Integer, ForeignKey("class_sessions.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)


# ── Students (universal registry) ────────────────────────────────────

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    roll_number = Column(String(32), unique=True, nullable=False, index=True)
    student_name = Column(String(128), nullable=False)
    email = Column(String(128), default="")
    phone = Column(String(16), default="")
    program = Column(String(64), default="")  # e.g. "B.Tech CS"
    enrollment_year = Column(Integer, nullable=True)
    graduation_year = Column(Integer, nullable=True)
    device_mac = Column(String(17), nullable=True)  # linked ESP32
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=istnow)
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    enrollments = relationship("StudentEnrollment", back_populates="student", lazy="selectin")


# ── Student Enrollments (link Student ↔ ClassSession) ────────────────

class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    enrolled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    enrolled_at = Column(DateTime, default=istnow)
    is_active = Column(Boolean, default=True)

    class_session = relationship("ClassSession", back_populates="enrollments")
    student = relationship("Student", back_populates="enrollments")
    enroller = relationship("User", foreign_keys=[enrolled_by])


# ── Quizzes ──────────────────────────────────────────────────────────

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False)
    title = Column(String(128), nullable=False)
    status = Column(String(16), default="draft")  # draft | active | completed
    quiz_mode = Column(String(16), default="planned")  # planned | impromptu
    timing_mode = Column(String(16), default="manual")  # per_question | total | manual
    question_time_limit = Column(Integer, default=0)  # seconds per question, 0 = no limit
    total_time_limit = Column(Integer, default=0)  # seconds for entire quiz, 0 = no limit
    current_question = Column(Integer, default=0)  # 0-indexed, which question is live
    is_live = Column(Boolean, default=False)  # whether quiz is currently visible to students
    created_at = Column(DateTime, default=istnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    class_session = relationship("ClassSession", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", lazy="selectin")
    answers = relationship("QuizAnswer", back_populates="quiz", lazy="selectin")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    order_num = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # list of option strings
    correct_option = Column(Integer, nullable=False)  # 0-indexed

    quiz = relationship("Quiz", back_populates="questions")


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_order = Column(Integer, nullable=False)
    device_id = Column(Integer, ForeignKey("esp_devices.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True,
                        index=True, doc="Student identity is the enrollment number (roll_number); kept NULL if unknown")
    selected_option = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, default=0)
    submitted_at = Column(DateTime, default=istnow)

    quiz = relationship("Quiz", back_populates="answers")
    device = relationship("EspDevice")
    student = relationship("Student")


# ── Polls ────────────────────────────────────────────────────────────

class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False)
    title = Column(String(256), nullable=False)
    options = Column(JSON, nullable=False)  # list of option strings
    poll_mode = Column(String(16), default="live")  # planned | live
    status = Column(String(16), default="draft")  # draft | active | closed
    is_live = Column(Boolean, default=False)
    created_at = Column(DateTime, default=istnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    class_session = relationship("ClassSession", back_populates="polls")
    votes = relationship("PollVote", back_populates="poll", lazy="selectin")


class PollVote(Base):
    __tablename__ = "poll_votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("esp_devices.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True,
                        index=True, doc="Student identity is the enrollment number (roll_number); kept NULL if unknown")
    selected_option = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, default=istnow)

    poll = relationship("Poll", back_populates="votes")
    device = relationship("EspDevice")
    student = relationship("Student")


# ── Attendance ───────────────────────────────────────────────────────

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("esp_devices.id"), nullable=True,
                      doc="Relay gateway (C6) — diagnostics only")
    student_enrollment_id = Column(Integer, ForeignKey("student_enrollments.id"), nullable=True,
                                   index=True)
    check_in_time = Column(DateTime, default=istnow)
    is_present = Column(Boolean, default=True)

    class_session = relationship("ClassSession", back_populates="attendance")
    device = relationship("EspDevice")
    enrollment = relationship("StudentEnrollment")


# ── Activity Logs ────────────────────────────────────────────────────

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(64), nullable=False)  # e.g. "user.create", "quiz.start", "class.activate"
    entity_type = Column(String(32), default="")  # "user", "class", "quiz", "poll", "student"
    entity_id = Column(Integer, nullable=True)
    details = Column(JSON, default=dict)  # additional context
    timestamp = Column(DateTime, default=istnow)

    user = relationship("User")


# ── User Sessions (server-side) ───────────────────────────────────────

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)  # sha256 hex of the opaque token
    session_token = Column(String(64), unique=True, nullable=False)            # opaque string, returned to client
    created_at = Column(DateTime, default=istnow)
    last_activity_at = Column(DateTime, default=istnow)
    expires_at = Column(DateTime, nullable=False)          # created_at + SESSION_HARD_MINUTES
    ip = Column(String(45), default="")
    user_agent = Column(String(255), default="")
    revoked = Column(Boolean, default=False)
    user = relationship("User")
