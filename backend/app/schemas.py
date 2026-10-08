"""Pydantic request/response schemas."""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, date
from typing import Literal, Optional

# Academic calendar: Monsoon → Winter → Summer (R5)
SEMESTERS = ("Monsoon", "Winter", "Summer")

# Enrollment number: exactly 10 alphanumeric characters (R9)
ENROLL_RE = r"^[A-Za-z0-9]{10}$"


# ── Auth ─────────────────────────────────────────────────────────────

# The only roles the auth layer understands (auth.require_*).
Role = Literal["teacher", "admin", "super_admin"]

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str
    password: str = Field(min_length=6)
    full_name: str = ""
    role: Role = "teacher"


class AdminUserCreate(BaseModel):
    """Admin-only: can create admin or teacher accounts."""
    username: str = Field(min_length=3, max_length=64)
    email: str
    password: str = Field(min_length=6)
    full_name: str = ""
    role: Role = "teacher"  # admin/super_admin only grantable by a super admin


class SuperAdminUserCreate(BaseModel):
    """Super admin: can create other admin accounts."""
    username: str = Field(min_length=3, max_length=64)
    email: str
    password: str = Field(min_length=6)
    full_name: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


class PasswordChange(BaseModel):
    """A user changing their own password (requires current password)."""
    current_password: str
    new_password: str = Field(min_length=6)


class ProfileUpdate(BaseModel):
    """A user updating their own profile (display name)."""
    full_name: str = Field(..., min_length=1, max_length=128)


class PasswordReset(BaseModel):
    """Admin resetting another user's password."""
    new_password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    idle_timeout_s: int
    hard_timeout_s: int
    server_time: Optional[datetime] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[Role] = None


# ── Courses (universal catalog) ──────────────────────────────────────

class CourseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    credits: int = 0
    department: str = ""
    exam_date: Optional[date] = None
    exam_start_time: Optional[str] = None  # HH:MM
    exam_end_time: Optional[str] = None    # HH:MM


class CourseUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    exam_date: Optional[date] = None
    exam_start_time: Optional[str] = None
    exam_end_time: Optional[str] = None


class CourseResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str = ""
    credits: int = 0
    department: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    exam_date: Optional[date] = None
    exam_start_time: Optional[str] = None
    exam_end_time: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Classes / Classrooms ─────────────────────────────────────────────

class ScheduleSlot(BaseModel):
    day: str = Field(min_length=1)  # e.g. "Monday"
    start: str = Field(min_length=1)  # "09:00"
    end: str = Field(min_length=1)    # "10:30"


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=1, max_length=32)  # admin-input classroom code
    subject: str = ""
    course_id: Optional[int] = None
    course_section: str = ""
    term: str = ""          # Monsoon | Winter | Summer
    year: Optional[int] = None
    start_date: Optional[date] = None     # instruction start
    end_date: Optional[date] = None       # instruction end (before exams)
    exam_start_date: Optional[date] = None   # exams begin (ClassSession.exam_start_date)
    exam_end_date: Optional[date] = None     # exams end
    meeting_schedule: list[ScheduleSlot] = []
    location: str = ""
    capacity: int = 0
    teacher_id: Optional[int] = None  # assigned faculty (advisable), set by admin
    teacher_ids: Optional[list[int]] = None  # full faculty set (many-to-many); first becomes primary
    classroom_code: Optional[str] = Field(default=None, max_length=32)  # physical room label, e.g. "RM-201"

    @field_validator("term")
    @classmethod
    def _semester_is_valid(cls, v: str) -> str:
        v = v.strip()
        if v and v not in SEMESTERS:
            raise ValueError(f"term must be one of {SEMESTERS}")
        return v


class ClassImportRow(BaseModel):
    line: int
    status: str            # create | update | duplicate | unchanged | invalid
    course_code: str
    course_name: str
    section: str
    class_code: str
    teacher_username: str
    class_name: str
    classroom_code: Optional[str] = None
    term: str = ""
    year: Optional[int] = None
    capacity: Optional[int] = None
    location: str = ""
    new_course: bool = False   # this row creates the course
    changes: list[str] = []    # update mode: fields that change
    note: Optional[str] = None
    errors: list[str] = []


class ClassImportReport(BaseModel):
    """All-or-nothing: any invalid row means nothing is imported."""
    mode: str              # create | update
    total: int
    create: int
    update: int
    duplicate: int         # already present (and unchanged in update mode): skipped
    invalid: int
    new_courses: int
    imported: int
    skipped: int
    committed: bool = False
    rows: list[ClassImportRow]


class ClassUpdate(BaseModel):
    """Editable scheduling fields for an existing class (hybrid scheduling)."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    code: Optional[str] = Field(default=None, min_length=1, max_length=32)
    subject: Optional[str] = None
    classroom_code: Optional[str] = Field(default=None, max_length=32)
    course_id: Optional[int] = None
    course_section: Optional[str] = None
    term: Optional[str] = None
    year: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    meeting_schedule: Optional[list[ScheduleSlot]] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None
    teacher_ids: Optional[list[int]] = None  # replace faculty set (many-to-many); first becomes primary

    @field_validator("term")
    @classmethod
    def _semester_is_valid(cls, v):  # type: ignore[no-redef]
        if v is None:
            return v
        v = v.strip()
        if v and v not in SEMESTERS:
            raise ValueError(f"term must be one of {SEMESTERS}")
        return v


class ClassJoin(BaseModel):
    code: str


class ClassAssignTeacher(BaseModel):
    teacher_id: int


class ClassFacultyUpdate(BaseModel):
    """Set the full set of faculty assigned to a class (replaces the list)."""
    teacher_ids: list[int]


class ClassResponse(BaseModel):
    id: int
    name: str
    subject: str = ""
    code: str
    teacher_id: int
    teacher_name: str = ""
    is_active: bool
    created_at: Optional[datetime] = None
    course_id: Optional[int] = None
    course_code: str = ""
    course_name: str = ""
    course_section: str = ""
    term: str = ""
    year: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    exam_date: Optional[date] = None
    exam_start_time: Optional[str] = None
    exam_end_time: Optional[str] = None
    reading_week_start: Optional[date] = None  # derived: exam_date minus 7 days
    meeting_schedule: list = []
    location: str = ""
    capacity: int = 0
    classroom_code: str = ""      # physical room label, e.g. "RM-201"
    teacher_ids: list[int] = []   # all assigned faculty (many-to-many)
    faculty_names: list = []      # [{id, full_name}, ...]
    student_count: int = 0
    quiz_count: int = 0
    poll_count: int = 0
    warnings: list = []  # schedule-clash warnings (hybrid scheduling, R6)

    model_config = {"from_attributes": True}


# ── Quizzes ──────────────────────────────────────────────────────────

# What a student module can show (firmware/protocol/protocol.h): four answer
# buttons; payload_quiz_question_t.question_text[140] and options[4][15];
# payload_poll_start_t.title[64]. Sizes are bytes of UTF-8 including the NUL.
# test_device_limits.py keeps these in step with the header.
DEVICE_MAX_OPTIONS = 4
DEVICE_TEXT_BYTES = {"question": 139, "option": 14, "poll_title": 63}


def device_text_warnings(label: str, text: str, kind: str) -> list[str]:
    """Text longer than the device field is truncated on the module's display."""
    n, limit = len(text.encode()), DEVICE_TEXT_BYTES[kind]
    return [f"{label} is {n} bytes; student modules show the first {limit}"] if n > limit else []


def question_warnings(number: int, question_text: str, options: list[str]) -> list[str]:
    out = device_text_warnings(f"Question {number}", question_text, "question")
    for j, opt in enumerate(options):
        out += device_text_warnings(f"Question {number} option {'ABCD'[j]}", opt, "option")
    return out


class QuizQuestionCreate(BaseModel):
    question_text: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=DEVICE_MAX_OPTIONS)
    correct_option: int = Field(ge=0)

    @model_validator(mode="after")
    def _correct_option_in_range(self):
        if self.correct_option >= len(self.options):
            raise ValueError(
                f"correct_option must be < number of options ({len(self.options)})")
        return self


class QuestionImportRow(BaseModel):
    line: int                          # line in the CSV file (header = 1)
    status: str                        # valid | invalid | duplicate
    question_text: str
    options: list[str]
    correct_option: Optional[int] = None
    errors: list[str] = []
    warnings: list[str] = []
    duplicate_of: Optional[str] = None   # "line N" | "already in this quiz"


class QuestionImportReport(BaseModel):
    """All-or-nothing: any invalid row means nothing is imported; duplicates
    are skipped. `committed` is true only when questions were stored."""
    total: int
    valid: int
    invalid: int
    duplicate: int
    imported: int
    skipped: int
    committed: bool = False
    rows: list[QuestionImportRow]


class QuizCreate(BaseModel):
    class_session_id: int
    title: str = Field(min_length=1, max_length=128)
    questions: list[QuizQuestionCreate] = Field(min_length=1)
    quiz_mode: str = "planned"  # "planned" | "impromptu"
    timing_mode: str = "manual"  # "per_question" | "total" | "manual"
    question_time_limit: int = 0  # seconds per question (for per_question mode)
    total_time_limit: int = 0  # seconds for entire quiz (for total mode)


class QuizResponse(BaseModel):
    id: int
    class_session_id: int
    title: str
    status: str
    quiz_mode: str = "planned"
    timing_mode: str = "manual"
    question_time_limit: int = 0
    total_time_limit: int = 0
    current_question: int = 0
    is_live: bool = False
    question_count: int = 0
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    warnings: list[str] = []   # text a student module will truncate

    model_config = {"from_attributes": True}


class QuizAnswerSubmit(BaseModel):
    device_id: int
    selected_option: int = Field(ge=0, le=DEVICE_MAX_OPTIONS - 1)
    response_time_ms: int = 0


# ── Polls ────────────────────────────────────────────────────────────

class PollCreate(BaseModel):
    class_session_id: int
    title: str = Field(min_length=1, max_length=256)
    options: list[str] = Field(min_length=2, max_length=DEVICE_MAX_OPTIONS)
    poll_mode: str = "live"  # "planned" | "live"


class PollResponse(BaseModel):
    id: int
    class_session_id: int
    title: str
    options: list
    poll_mode: str = "live"
    status: str
    is_live: bool = False
    total_votes: int = 0
    created_at: Optional[datetime] = None
    warnings: list[str] = []   # text a student module will truncate

    model_config = {"from_attributes": True}


class PollVoteSubmit(BaseModel):
    device_id: int
    selected_option: int = Field(ge=0, le=DEVICE_MAX_OPTIONS - 1)


# ── Students (universal registry) ────────────────────────────────────

def _valid_enrollment_number(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("enrollment number cannot be empty")
    if len(v) != 10 or not v.isalnum():
        raise ValueError("enrollment number must be exactly 10 alphanumeric characters")
    return v.upper()


class StudentCreate(BaseModel):
    roll_number: str
    student_name: str = Field(min_length=1, max_length=128)
    email: str = ""
    phone: str = ""
    program: str = ""
    enrollment_year: Optional[int] = None
    graduation_year: Optional[int] = None
    device_mac: str = ""

    _roll = field_validator("roll_number")(_valid_enrollment_number)


class StudentUpdate(BaseModel):
    student_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    program: Optional[str] = None
    enrollment_year: Optional[int] = None
    graduation_year: Optional[int] = None
    device_mac: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(BaseModel):
    id: int
    roll_number: str
    student_name: str
    email: str = ""
    phone: str = ""
    program: str = ""
    enrollment_year: Optional[int] = None
    graduation_year: Optional[int] = None
    device_mac: Optional[str] = None
    is_active: bool = True
    registered_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class StudentRegister(BaseModel):
    """Create a student and optionally enroll them in a class."""
    roll_number: str
    student_name: str = Field(min_length=1, max_length=128)
    email: str = ""
    phone: str = ""
    program: str = ""
    enrollment_year: Optional[int] = None
    graduation_year: Optional[int] = None
    device_mac: str = ""
    class_session_id: Optional[int] = None  # optional: enroll right away

    _roll = field_validator("roll_number")(_valid_enrollment_number)


class BulkStudentRegister(BaseModel):
    class_session_id: Optional[int] = None
    students: list[StudentRegister]


class StudentEnroll(BaseModel):
    """Enroll an existing student into a class."""
    student_id: int


# ── ESP Device ───────────────────────────────────────────────────────

class DeviceRegister(BaseModel):
    mac_address: str
    device_name: str = ""
    device_type: str = "student"  # "c6" (class node) | "s3" | "student"
    firmware_version: str = "0.0.0"
    classroom_code: str = ""  # optional: physical room code for auto-assignment


class DeviceHeartbeat(BaseModel):
    mac_address: str
    battery_pct: int = 100
    rssi: int = 0
    firmware_version: str = ""
    student_count: int = 0
    free_heap: int = 0
    total_flash: int = 0
    # Diagnostics (#39). Optional: older firmware omits them.
    uptime_s: Optional[int] = Field(None, ge=0)
    reset_reason: Optional[str] = Field(None, max_length=16)
    boot_count: Optional[int] = Field(None, ge=0)
    min_free_heap: Optional[int] = Field(None, ge=0)
    s3_link_ok: Optional[bool] = None
    s3_uptime_s: Optional[int] = Field(None, ge=0)


class DeviceStatusPing(BaseModel):
    """C6 classroom status ping (every ~2 minutes). Gives the backend a
    periodic classroom update: current mesh student population, class link,
    uptime, RSSI. Also refreshes liveness so the gateway stays online."""
    mac_address: str
    class_id: int = 0
    student_count: int = 0
    uptime_s: int = 0
    rssi: int = 0
    free_heap: int = 0


class DeviceAttendance(BaseModel):
    """Student check-in. Identity is the ENROLLMENT NUMBER, not the device MAC.

    The class node (C6) relays a check-in on behalf of a mesh student whose
    identity is its enrollment number (roll_number). mac_address is the class
    gateway that relayed it (optional, for diagnostics only).
    """
    enrollment_number: str = ""
    class_code: str
    mac_address: str = ""  # relay gateway MAC (optional, diagnostics)


class DeviceFirmwareCheck(BaseModel):
    mac_address: str
    current_version: str = "0.0.0"


class DeviceOtaApplied(BaseModel):
    mac_address: str
    version: str = ""  # version the device reports it just applied


class DeviceResponse(BaseModel):
    id: int
    mac_address: str
    device_name: str = ""
    device_type: str = "student"
    student_name: str = ""
    battery_pct: int = 100
    rssi: int = 0
    is_connected: bool = False
    gateway_id: Optional[int] = None
    is_active: bool = True
    firmware_version: str = "0.0.0"
    pending_version: str = ""
    ota_status: str = "idle"
    ota_requested_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    class_id: Optional[int] = None
    class_code: str = ""
    class_name: str = ""
    # Telemetry from classroom node
    student_count: int = 0
    free_heap: int = 0
    # Per-device key (#66): shared (none issued) | issued (not used yet) | active
    key_state: str = "shared"
    key_confirmed_at: Optional[datetime] = None
    # Health (#39): state + why, and the diagnostics behind it
    health: str = "UNKNOWN"
    health_reasons: list[str] = []
    uptime_s: Optional[int] = None
    reset_reason: Optional[str] = None
    boot_count: Optional[int] = None
    min_free_heap: Optional[int] = None
    s3_link_ok: Optional[bool] = None
    s3_uptime_s: Optional[int] = None
    diag_at: Optional[datetime] = None
    total_flash: int = 0

    model_config = {"from_attributes": True}


class ModuleAccessUpdate(BaseModel):
    is_active: bool


class FirmwareArtifactResponse(BaseModel):
    id: int
    sha256: str
    size: int
    target: str
    chip: str
    project: str
    version: str
    idf_version: str = ""
    build_date: str = ""
    elf_sha256: str = ""
    status: str
    channel: str
    release_notes: str = ""
    legacy: bool = False
    uploaded_by: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    created: Optional[bool] = None     # upload response: false = these bytes were already registered
    devices_running: int = 0           # devices whose firmware_version is this
    devices_pending: int = 0           # devices about to install it
    latest_approved: bool = False      # highest approved version for its target
    signer: str = ""                   # key digest of its signature, "" unsigned (#66)
    signed_by_site_key: Optional[bool] = None   # None when no site key is configured

    model_config = {"from_attributes": True}


class ModuleOtaRequest(BaseModel):
    version: str = Field(min_length=1, max_length=32)
    allow_downgrade: bool = False   # confirm a rollback to an older version (#37)


class ClassDevicesResponse(BaseModel):
    """A class node plus the student devices currently linked to it (R8)."""
    node: Optional[DeviceResponse] = None
    student_devices: list[DeviceResponse] = []
    student_modules: list[dict] = []     # the mesh inventory (#40); see services/student_modules.py


class ModuleLinkDevice(BaseModel):
    """Logically link a student device to a class node (R7)."""
    device_id: int


class OtaStatusResponse(BaseModel):
    """Device-side response to a firmware poll (R8)."""
    update_available: bool = False
    version: str = ""          # the version to download, when available
    ota_status: str = "idle"   # what the server currently thinks
    current_version: str = ""
    sha256: str = ""           # of the image to download: verify it before installing (#34)
    size: int = 0
    deployment_id: Optional[int] = None


class DeviceOtaStatus(BaseModel):
    """A device reporting its OTA progress (#34)."""
    mac_address: str = Field(min_length=1, max_length=17)
    state: str                 # precheck|downloading|verifying|installing|rebooting|health_check|success|rolled_back|failed
    version: str = Field(default="", max_length=32)    # running version (success / rolled_back)
    error: str = Field(default="", max_length=200)
    error_code: Optional[int] = None                   # esp_err_t


class DeviceDataBatch(BaseModel):
    """Batched data from C6 (via SPI aggregation)."""
    device_type: str = "c6"
    messages: list[dict]


# ── CSV Import ──────────────────────────────────────────────────────

class CsvImportError(BaseModel):
    row: int
    roll_number: str
    error: str

class CsvImportResult(BaseModel):
    inserted: int
    skipped: list[CsvImportError] = []
    total_rows: int

# ── Activity Logs ────────────────────────────────────────────────────

class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: str = ""
    action: str
    entity_type: str = ""
    entity_id: Optional[int] = None
    details: dict = {}
    timestamp: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Device Tree ────────────────────────────────────────────────────────

class DeviceTreeNode(BaseModel):
    """Single node in the classroom device tree (relay topology)."""
    id: int
    enrollment: Optional[str] = None
    device_id: int
    hop_count: int
    rssi: int
    is_direct: bool
    parent_enrollment: Optional[str] = None
    device_type: str
    student_name: Optional[str] = None
    is_connected: bool
    battery_pct: int

    model_config = {"from_attributes": True}


class DeviceTreeResponse(BaseModel):
    """Device tree for a class: root (C6) + relayed students (S3 mesh)."""
    class_id: int
    root: DeviceTreeNode
    nodes: list[DeviceTreeNode]

    model_config = {"from_attributes": True}
