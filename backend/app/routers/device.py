"""Device router: ESP32 devices register, heartbeat, and submit data."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import commit_or_conflict, get_db
from ..models import EspDevice, ClassSession, Attendance, StudentEnrollment, Student, ActivityLog, \
    Quiz, QuizAnswer, Poll, PollVote
from ..schemas import DeviceRegister, DeviceHeartbeat, DeviceStatusPing, DeviceAttendance, \
    DeviceDataBatch, DeviceFirmwareCheck, DeviceOtaApplied, OtaStatusResponse
from ..config import api_key_ok
from ..services.presence import mark_online, _push_after_commit
from ..services.firmware_store import artifact_file, resolve as resolve_firmware
from ..timeutil import istnow, istnow_aware
from ..ws.manager import manager

router = APIRouter(prefix="/api/device", tags=["device"])


async def _verify_api_key(x_api_key: str = Header(...)):
    if not api_key_ok(x_api_key):
        raise HTTPException(403, "Invalid device API key")


@router.post("/register", dependencies=[Depends(_verify_api_key)])
async def register_device(body: DeviceRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EspDevice).where(EspDevice.mac_address == body.mac_address)
    )
    device = result.scalar_one_or_none()

    if device:
        device.device_name = body.device_name
        device.device_type = body.device_type
        device.last_seen = istnow()
    else:
        device = EspDevice(
            mac_address=body.mac_address,
            device_name=body.device_name,
            device_type=body.device_type,
        )
        db.add(device)
        await db.flush()

    # Presence: log when this classroom ESP comes online.
    await mark_online(db, device)

    # Auto-assign a classroom node to its physical room on first boot (R2/R4).
    # Match either the short join `code` or the `classroom_code` label.
    linked_class_id = None
    if body.classroom_code and body.classroom_code.strip():
        code = body.classroom_code.strip()
        cls_result = await db.execute(
            select(ClassSession).where(
                (ClassSession.code == code) | (ClassSession.classroom_code == code)
            )
        )
        cls = cls_result.scalars().first()
        if cls:
            cls.device_id = device.id
            cls.classroom_code = cls.classroom_code or code
            device.is_connected = True
            linked_class_id = cls.id

    if linked_class_id is None:
        # A device already linked to a class keeps that linkage.
        linked = await db.execute(
            select(ClassSession.id).where(ClassSession.device_id == device.id)
        )
        linked_class_id = linked.scalar_one_or_none()

        if (linked_class_id is None
                and (body.device_type or "").lower() == "c6"
                and (not body.classroom_code or not body.classroom_code.strip())):
            # No room code given: auto-link this GATEWAY to the first active
            # classroom that has no gateway yet. Other device types (an S3
            # registering during its OTA hop, student nodes) must never take
            # over a class's gateway link.
            avail = await db.execute(
                select(ClassSession)
                .where(ClassSession.is_active.is_(True), ClassSession.device_id.is_(None))
                .order_by(ClassSession.id.asc())
            )
            cls = avail.scalars().first()
            if cls:
                cls.device_id = device.id
                device.is_connected = True
                linked_class_id = cls.id
                db.add(ActivityLog(
                    action="class.device_auto_linked",
                    entity_type="class",
                    entity_id=cls.id,
                    details={
                        "mac_address": body.mac_address,
                        "device_name": body.device_name,
                        "device_type": body.device_type,
                    },
                ))

    await db.commit()
    await db.refresh(device)
    # Fire-and-forget presence push to teachers (new session to avoid holding request DB)
    asyncio.create_task(_push_after_commit(device.id))
    return {"device_id": device.id, "status": "registered", "class_id": linked_class_id}


@router.post("/heartbeat", dependencies=[Depends(_verify_api_key)])
async def heartbeat(body: DeviceHeartbeat, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EspDevice).where(EspDevice.mac_address == body.mac_address)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not registered")

    device.last_seen = istnow()
    device.battery_pct = body.battery_pct
    device.rssi = body.rssi
    # Presence: log the offline → online transition (idempotent).
    await mark_online(db, device)
    if body.firmware_version:
        device.firmware_version = body.firmware_version

    # Node telemetry (R2/R4)
    if body.student_count:
        device.student_count = body.student_count
    if body.free_heap:
        device.free_heap = body.free_heap
    if body.total_flash:
        device.total_flash = body.total_flash
    await db.commit()
    # Fire-and-forget presence push to teachers (new session to avoid holding request DB)
    asyncio.create_task(_push_after_commit(device.id))

    return {"status": "ok", "server_time": istnow_aware().isoformat()}


@router.post("/ping", dependencies=[Depends(_verify_api_key)])
async def status_ping(body: DeviceStatusPing, db: AsyncSession = Depends(get_db)):
    """C6 classroom status ping (every ~2 minutes).

    Carries a periodic classroom update — current mesh student population,
    linked class_id, uptime, RSSI — that the backend records in the activity
    log ("class.status_update") and uses to keep the gateway's live presence
    and student_count fresh between heartbeats.
    """
    result = await db.execute(
        select(EspDevice).where(EspDevice.mac_address == body.mac_address)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not registered")

    device.last_seen = istnow()
    device.rssi = body.rssi
    if body.student_count:
        device.student_count = body.student_count
    if body.free_heap:
        device.free_heap = body.free_heap
    await mark_online(db, device)

    db.add(ActivityLog(
        action="class.status_update",
        entity_type="class",
        entity_id=body.class_id if body.class_id > 0 else None,
        details={
            "mac_address": body.mac_address,
            "student_count": body.student_count,
            "uptime_s": body.uptime_s,
            "rssi": body.rssi,
        },
    ))

    await db.commit()
    asyncio.create_task(_push_after_commit(device.id))

    return {"status": "ok", "server_time": istnow_aware().isoformat()}


@router.post("/firmware/check", response_model=OtaStatusResponse,
             dependencies=[Depends(_verify_api_key)])
async def firmware_check(body: DeviceFirmwareCheck, db: AsyncSession = Depends(get_db)):
    """Student node polls to see if an OTA update is pending (R8)."""
    result = await db.execute(
        select(EspDevice).where(EspDevice.mac_address == body.mac_address)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not registered")

    device.last_seen = istnow()
    device.is_connected = True
    device.firmware_version = body.current_version or device.firmware_version

    # An update is available when admin has pushed a version we don't have yet.
    update_available = bool(
        device.pending_version
        and device.pending_version != device.firmware_version
    )
    await db.commit()
    return OtaStatusResponse(
        update_available=update_available,
        version=device.pending_version if update_available else "",
        ota_status=device.ota_status or "idle",
        current_version=device.firmware_version,
    )


@router.post("/firmware/applied", dependencies=[Depends(_verify_api_key)])
async def firmware_applied(body: DeviceOtaApplied, db: AsyncSession = Depends(get_db)):
    """Node reports it finished applying the pushed update (R8)."""
    result = await db.execute(
        select(EspDevice).where(EspDevice.mac_address == body.mac_address)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not registered")

    version = body.version or device.pending_version
    if version:
        device.firmware_version = version
    device.pending_version = ""
    device.ota_status = "applied"
    device.is_connected = True
    device.last_seen = istnow()
    await db.commit()
    return {"status": "ok", "firmware_version": device.firmware_version}


@router.get("/firmware/download", dependencies=[Depends(_verify_api_key)])
async def firmware_download(mac_address: str, version: str,
                            db: AsyncSession = Depends(get_db)):
    """Stream the firmware image for a device's pending OTA update (R8).

    Only the version an admin pushed to this device is served, and only from
    the registry (#35): a validated image for the device's own type. The
    image's SHA-256 is sent as X-Firmware-SHA256 for the device to verify.
    """
    result = await db.execute(
        select(EspDevice).where(EspDevice.mac_address == mac_address)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not registered")

    version = version.strip()
    if not device.pending_version:
        raise HTTPException(403, "No OTA update is pending for this device")
    if version != device.pending_version:
        raise HTTPException(403, "Requested version does not match pending OTA")

    artifact = await resolve_firmware(db, (device.device_type or "").lower(), version)
    if artifact is None:
        raise HTTPException(404, f"No registered {device.device_type} firmware {version}")
    path = artifact_file(artifact)
    return FileResponse(path, media_type="application/octet-stream",
                        filename=f"{artifact.project}-{artifact.version}.bin",
                        headers={"X-Firmware-SHA256": artifact.sha256})


@router.post("/attendance", dependencies=[Depends(_verify_api_key)])
async def check_attendance(body: DeviceAttendance, db: AsyncSession = Depends(get_db)):
    """Student (mesh node) checks in to a class.

    Identity is the student's ENROLLMENT NUMBER. mac_address, when present, is
    the relaying class gateway (C6) and is used only to mark the node.
    """
    # Class lookup by code (active session)
    cls_result = await db.execute(
        select(ClassSession).where(ClassSession.code == body.class_code)
    )
    cls = cls_result.scalar_one_or_none()
    if not cls:
        raise HTTPException(404, "Class not found")
    if not cls.is_active:
        raise HTTPException(400, "Class is not active")

    # Resolve student by enrollment number (primary identity)
    roll = (body.enrollment_number or "").strip().upper()
    student = None
    if roll:
        stud_result = await db.execute(
            select(Student).where(Student.roll_number == roll)
        )
        student = stud_result.scalar_one_or_none()
        if not student:
            raise HTTPException(404, "Student not found")
    elif body.mac_address:
        stud_result = await db.execute(
            select(Student).where(Student.device_mac == body.mac_address, Student.is_active == True)  # noqa: E712
        )
        student = stud_result.scalar_one_or_none()
        if not student:
            raise HTTPException(404, "Student not found")
    else:
        raise HTTPException(400, "enrollment_number is required")

    # Resolve relay gateway (optional, diagnostics only — not student identity)
    device = None
    if body.mac_address:
        dev_result = await db.execute(
            select(EspDevice).where(EspDevice.mac_address == body.mac_address)
        )
        device = dev_result.scalar_one_or_none()

    # Optional: resolve esp_device for the class node so modules list stays fresh
    if device is None and cls.device_id:
        dev_result = await db.execute(select(EspDevice).where(EspDevice.id == cls.device_id))
        device = dev_result.scalar_one_or_none()

    enrollment = None
    enroll_res = await db.execute(
        select(StudentEnrollment)
        .where(StudentEnrollment.class_session_id == cls.id)
        .where(StudentEnrollment.student_id == student.id)
        .where(StudentEnrollment.is_active == True)  # noqa: E712
    )
    enrollment = enroll_res.scalar_one_or_none()

    # Fallback: legacy enrollment via device_id on StudentEnrollment
    if not enrollment and device is not None:
        enroll_res = await db.execute(
            select(StudentEnrollment)
            .where(StudentEnrollment.class_session_id == cls.id)
            .where(StudentEnrollment.device_id == device.id)
            .where(StudentEnrollment.is_active == True)  # noqa: E712
        )
        enrollment = enroll_res.scalar_one_or_none()

    # Upsert attendance, keyed on the student's enrollment (enrollment-number identity)
    if enrollment is not None:
        att_result = await db.execute(
            select(Attendance)
            .where(Attendance.class_session_id == cls.id,
                   Attendance.student_enrollment_id == enrollment.id)
        )
    elif device is not None:
        att_result = await db.execute(
            select(Attendance)
            .where(Attendance.class_session_id == cls.id, Attendance.device_id == device.id)
        )
    else:
        raise HTTPException(400, "Could not resolve enrollment for this student")

    att = att_result.scalar_one_or_none()

    if att:
        att.is_present = True
        att.check_in_time = istnow()
        if enrollment:
            att.student_enrollment_id = enrollment.id
    else:
        att = Attendance(
            class_session_id=cls.id,
            device_id=device.id if device else None,
            student_enrollment_id=enrollment.id if enrollment else None,
        )
        db.add(att)

    await db.commit()
    return {"status": "checked_in", "class_name": cls.name}


async def _resolve_student_id_by_enrollment(db: AsyncSession, msg: dict) -> int | None:
    """Resolve a student row from a batch message.

    Student identity is the ENROLLMENT NUMBER (roll_number, 10 chars).
    Optional 'device_mac'/'device_id' are accepted only as a *fallback* for
    legacy/relay callers — never as primary identity.
    """
    roll = (msg.get("enrollment_number") or msg.get("roll_number") or "").strip().upper()
    if roll:
        res = await db.execute(select(Student).where(Student.roll_number == roll))
        student = res.scalar_one_or_none()
        if student:
            return student.id

    mac = (msg.get("device_mac") or "").strip()
    if mac:
        res = await db.execute(select(Student).where(Student.device_mac == mac))
        student = res.scalar_one_or_none()
        if student:
            return student.id

    dev_id = msg.get("device_id")
    if isinstance(dev_id, int) and dev_id:
        res = await db.execute(select(StudentEnrollment).where(StudentEnrollment.device_id == dev_id))
        enr = res.scalar_one_or_none()
        if enr:
            return enr.student_id
    return None


def _ints(*values) -> bool:
    return all(isinstance(v, int) and not isinstance(v, bool) for v in values)


async def _record_quiz_answer(db: AsyncSession, msg: dict) -> dict | None:
    """Validate + de-duplicate one mesh quiz answer.

    Mesh relays can deliver the same press several times, so (quiz, question,
    student) is unique. Answers for unknown students, inactive/unknown quizzes,
    unknown questions or out-of-range options are dropped.
    Returns the teacher broadcast for a stored answer, else None.
    """
    quiz_id, order, option = msg.get("quiz_id"), msg.get("question_order", 0), msg.get("selected_option")
    if not _ints(quiz_id, order, option):
        return None
    student_id = await _resolve_student_id_by_enrollment(db, msg)
    quiz = await db.get(Quiz, quiz_id)
    if student_id is None or quiz is None or quiz.status != "active":
        return None
    question = next((q for q in quiz.questions if q.order_num == order), None)
    if question is None or not 0 <= option < len(question.options):
        return None
    dup = await db.execute(select(QuizAnswer.id).where(
        QuizAnswer.quiz_id == quiz_id, QuizAnswer.question_order == order,
        QuizAnswer.student_id == student_id))
    if dup.first() is not None:
        return None
    resp = msg.get("response_time_ms", 0)
    db.add(QuizAnswer(quiz_id=quiz_id, question_order=order, student_id=student_id,
                      selected_option=option, response_time_ms=resp if _ints(resp) else 0))
    return {"class_id": quiz.class_session_id, "type": "quiz_answer",
            "quiz_id": quiz_id, "question_order": order}


async def _record_poll_vote(db: AsyncSession, msg: dict) -> dict | None:
    """Validate + de-duplicate one mesh poll vote ((poll, student) is unique)."""
    poll_id, option = msg.get("poll_id"), msg.get("selected_option")
    if not _ints(poll_id, option):
        return None
    student_id = await _resolve_student_id_by_enrollment(db, msg)
    poll = await db.get(Poll, poll_id)
    if student_id is None or poll is None or poll.status != "active":
        return None
    if not 0 <= option < len(poll.options):
        return None
    dup = await db.execute(select(PollVote.id).where(
        PollVote.poll_id == poll_id, PollVote.student_id == student_id))
    if dup.first() is not None:
        return None
    db.add(PollVote(poll_id=poll_id, student_id=student_id, selected_option=option))
    return {"class_id": poll.class_session_id, "type": "poll_vote",
            "poll_id": poll_id, "selected_option": option}


async def _broadcast_participation(db: AsyncSession, event: dict) -> None:
    """Same live-count frames the HTTP answer/vote routes send to teachers."""
    class_id = event.pop("class_id")
    if event["type"] == "quiz_answer":
        total = await db.scalar(select(func.count()).select_from(QuizAnswer).where(
            QuizAnswer.quiz_id == event["quiz_id"],
            QuizAnswer.question_order == event["question_order"]))
        event["total_answers"] = total or 0
    else:
        total = await db.scalar(select(func.count()).select_from(PollVote).where(
            PollVote.poll_id == event["poll_id"]))
        event["total_votes"] = total or 0
    await manager.broadcast_to_class(class_id, event)


async def _record_ota_result(db: AsyncSession, msg: dict) -> bool:
    """An S3's OTA outcome, relayed by its C6 (#33).

    The S3 reports after rebooting into the new image (applied), after the
    bootloader reverted it (rolled_back), or when an attempt failed before
    any reboot (failed + esp_err_t). Success is recorded only for 'applied'
    with the version that was pushed: a reboot alone proves nothing.
    """
    mac = (msg.get("mac_address") or "").strip()
    version = str(msg.get("version") or "").strip()[:32]
    result = msg.get("result")
    if not mac or result not in ("applied", "rolled_back", "failed"):
        return False
    device = (await db.execute(select(EspDevice).where(EspDevice.mac_address == mac))).scalar_one_or_none()
    if device is None:
        return False
    expected = device.pending_version or ""
    if result == "applied":
        device.firmware_version = version            # what really runs
        device.ota_status = "applied" if (not expected or version == expected) else "failed"
        device.pending_version = ""
    elif result == "rolled_back":
        device.ota_status = "rolled_back"
        device.pending_version = ""                  # don't offer the bad image again
    else:
        device.ota_status = "failed"                 # transient: pending kept for a retry
    db.add(ActivityLog(action="module.ota_result", entity_type="device", entity_id=device.id, details={
        "mac": mac, "result": result, "version": version, "expected": expected,
        "error": msg.get("error", 0), "gateway_mac": msg.get("device_mac", "")}))
    return True


async def _resolve_gateway(db: AsyncSession, mac: str) -> EspDevice | None:
    """Resolve the relaying C6 gateway device by its MAC (from a mesh event)."""
    mac = (mac or "").strip()
    if not mac:
        return None
    res = await db.execute(select(EspDevice).where(EspDevice.mac_address == mac))
    return res.scalar_one_or_none()


@router.post("/batch", dependencies=[Depends(_verify_api_key)])
async def receive_batch(body: DeviceDataBatch, db: AsyncSession = Depends(get_db)):
    """C6 sends batched data from mesh students."""
    processed = 0
    skipped = 0
    touched_device_ids: list[int] = []
    participation: list[dict] = []
    for msg in body.messages:
        msg_type = msg.get("type", "")

        if msg_type == "heartbeat":
            mac = msg.get("device_mac", "")
            if mac:
                result = await db.execute(select(EspDevice).where(EspDevice.mac_address == mac))
                device = result.scalar_one_or_none()
                if device:
                    device.last_seen = istnow()
                    if isinstance(msg.get("battery_pct"), int):
                        device.battery_pct = msg.get("battery_pct", 100)
                    if isinstance(msg.get("rssi"), int):
                        device.rssi = msg.get("rssi", 0)
                    # Bring the relayed node back online (idempotent, logs
                    # the offline → online transition exactly once).
                    await mark_online(db, device)
                    touched_device_ids.append(device.id)
                    processed += 1

        elif msg_type == "student_join":
            # A classroom node reports a student module that appeared on its mesh
            # (ESP-NOW). Record EVERY connect, and auto-link the student to the
            # physical room (R4) when the class is known.
            roll = (msg.get("enrollment_number") or "").strip().upper()
            if not roll:
                continue

            stud_result = await db.execute(
                select(Student).where(Student.roll_number == roll)
            )
            student = stud_result.scalar_one_or_none()
            if not student:
                continue  # unknown enrollment — nothing to record

            # Audit trail: every student connect is logged.
            db.add(ActivityLog(
                action="student.connect",
                entity_type="student",
                entity_id=student.id,
                details={
                    "enrollment_number": roll,
                    "gateway_mac": msg.get("device_mac", ""),
                },
            ))

            gw = await _resolve_gateway(db, msg.get("device_mac"))
            if gw is not None:
                touched_device_ids.append(gw.id)

            code = (msg.get("class_code")
                    or msg.get("classroom_code")
                    or msg.get("room_code") or "").strip()
            if code:
                cls_result = await db.execute(
                    select(ClassSession).where(
                        (ClassSession.code == code) | (ClassSession.classroom_code == code)
                    )
                )
                cls = cls_result.scalars().first()
            else:
                cls = None

            if cls:
                # Identity is the enrollment number — we deliberately do NOT bind
                # student device MACs here (no physical tracking).
                already = await db.execute(
                    select(StudentEnrollment.id).where(
                        StudentEnrollment.class_session_id == cls.id,
                        StudentEnrollment.student_id == student.id,
                    )
                )
                if already.scalar_one_or_none() is None:
                    db.add(StudentEnrollment(
                        class_session_id=cls.id,
                        student_id=student.id,
                    ))
            processed += 1

        elif msg_type == "student_leave":
            # Student module went offline (timeout / explicit leave / shutdown).
            # Record EVERY disconnect; enrollment is the identity.
            roll = (msg.get("enrollment_number") or "").strip().upper()
            if not roll:
                continue

            stud_result = await db.execute(
                select(Student).where(Student.roll_number == roll)
            )
            student = stud_result.scalar_one_or_none()
            if not student:
                processed += 1
                continue  # unknown enrollment — nothing to record

            db.add(ActivityLog(
                action="student.disconnect",
                entity_type="student",
                entity_id=student.id,
                details={
                    "enrollment_number": roll,
                    "reason": msg.get("reason", 0),
                    "device_id": msg.get("device_id", 0),
                    "gateway_mac": msg.get("device_mac", ""),
                },
            ))

            gw = await _resolve_gateway(db, msg.get("device_mac"))
            if gw is not None:
                touched_device_ids.append(gw.id)
            processed += 1

        elif msg_type == "ota_result":
            if await _record_ota_result(db, msg):
                processed += 1
            else:
                skipped += 1

        elif msg_type in ("quiz_answer", "poll_vote"):
            record = _record_quiz_answer if msg_type == "quiz_answer" else _record_poll_vote
            event = await record(db, msg)
            if event is None:
                skipped += 1
            else:
                participation.append(event)
                processed += 1

    # A concurrent batch carrying the same answers can commit first; the unique
    # indexes reject ours. 503 makes the gateway retry, and the retry skips
    # what is already stored.
    await commit_or_conflict(db, "Concurrent duplicate submission; retry", status=503)
    for event in participation:
        await _broadcast_participation(db, event)
    # Push the refreshed presence to any connected teachers.
    for dev_id in set(touched_device_ids):
        asyncio.create_task(_push_after_commit(dev_id))
    return {"status": "ok", "processed": processed, "skipped": skipped}
