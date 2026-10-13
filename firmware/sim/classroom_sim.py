"""Classroom protocol simulator: student modules -> S3 hub -> C6 gateway (v2.2).

What runs here, precisely:

- **Firmware code, host-compiled.** firmware/protocol/protocol.c and
  ota_chunk.c are compiled for this computer and called through ctypes:
  frame encode/decode and CRC, mesh message ids and de-duplication, SPI
  batch records, SPI slots and the slot FIFO, OTA chunking. These are the
  exact C sources the boards build.
- **Python models of board glue.** The radio (ESP-NOW broadcast), the
  student's button handling, the hub's receive queue (64 entries, as
  mesh_master.c) and the gateway's msg_to_json (class_c6/main/main.c) are
  re-stated in Python, so a difference between this model and the firmware
  is possible; the tests pin the parts that matter (field names, sizes).
- **Not simulated.** CPU execution of a compiled .bin, timing on silicon,
  RF behaviour, SPI electrical errors other than corrupted bytes, power.
  Those need the hardware tests (docs/testing/HARDWARE_VALIDATION.md).

Every random choice comes from one seeded random.Random; the report records
the seed so a failing run can be repeated exactly.

    python firmware/sim/classroom_sim.py --students 30 --loss 0.1 --seed 7
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import random
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

PROTOCOL = Path(__file__).resolve().parents[1] / "protocol"

# Constants from protocol.h / mesh_espnow.c / mesh_master.c / config.h.
MSG_HEARTBEAT, MSG_STUDENT_JOIN, MSG_ATTENDANCE = 0x01, 0x02, 0x04
MSG_QUIZ_QUESTION, MSG_QUIZ_ANSWER = 0x11, 0x12
MSG_POLL_START, MSG_POLL_VOTE = 0x20, 0x22
MSG_MAX_PAYLOAD, MSG_OVERHEAD = 240, 6
ESPNOW_MAX_DATA, MESH_HDR = 250, 6
SPI_SLOT_BYTES, SPI_SLOT_PAYLOAD_MAX = 4096, 4092
HUB_QUEUE = 64              # MSG_QUEUE_SIZE in class_s3/main/mesh_master.c (one slot is kept free)
RELAY_TTL = 5               # MESH_RELAY_TTL in student/main/config.h
SPI_POLL_MS = 50            # CONFIG_SPI_POLL_INTERVAL_MS default (class_s3 Kconfig)


# ── The firmware library ─────────────────────────────────────────────────


class _Msg(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("length", ctypes.c_uint16),
                ("payload", ctypes.c_uint8 * MSG_MAX_PAYLOAD), ("crc", ctypes.c_uint16)]


class _AnswerTx(ctypes.Structure):          # answer_tx_t (protocol.h, #181)
    _fields_ = [("state", ctypes.c_int), ("msg_id", ctypes.c_uint32), ("resends", ctypes.c_uint8),
                ("due_ms", ctypes.c_uint32)]


ANSWER_PENDING, ANSWER_DELIVERED, ANSWER_FAILED = 1, 2, 3
MSG_ACK = 0x30

_lib = None


def firmware() -> ctypes.CDLL:
    """Compile protocol.c + ota_chunk.c once per process and load them."""
    global _lib
    if _lib is None:
        cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        if not cc:
            raise RuntimeError("a C compiler (cc) is needed to run the firmware protocol code")
        out = Path(tempfile.mkdtemp(prefix="impress-sim-")) / "libprotocol.so"
        subprocess.run([cc, "-std=gnu11", "-O1", "-shared", "-fPIC", f"-I{PROTOCOL}",
                        str(PROTOCOL / "protocol.c"), str(PROTOCOL / "ota_chunk.c"), "-o", str(out)],
                       check=True, capture_output=True)
        lib = ctypes.CDLL(str(out))
        u8p, sz = ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t
        lib.msg_encode.argtypes = [ctypes.c_int, u8p, ctypes.c_uint16, u8p, sz]
        lib.msg_decode.argtypes = [u8p, sz, ctypes.POINTER(_Msg)]
        lib.msg_verify_crc.argtypes = [ctypes.POINTER(_Msg)]
        lib.msg_verify_crc.restype = ctypes.c_bool
        lib.mesh_msg_id.argtypes = [ctypes.c_uint32, u8p, sz]
        lib.mesh_msg_id.restype = ctypes.c_uint32
        lib.mesh_dedup_check.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]
        lib.mesh_dedup_check.restype = ctypes.c_bool
        lib.spi_record_write.argtypes = [u8p, sz, ctypes.c_uint32, u8p, ctypes.c_uint16]
        lib.spi_record_read.argtypes = [u8p, sz, ctypes.POINTER(ctypes.c_uint32),
                                        ctypes.POINTER(u8p), ctypes.POINTER(ctypes.c_uint16)]
        lib.spi_slot_encode.argtypes = [u8p, u8p, sz]
        lib.spi_slot_decode.argtypes = [u8p, u8p, sz]
        tx = ctypes.POINTER(_AnswerTx)
        lib.answer_tx_start.argtypes = [tx, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
        lib.answer_tx_poll.argtypes = [tx, ctypes.c_uint32, ctypes.c_uint32]
        lib.answer_tx_poll.restype = ctypes.c_bool
        lib.answer_tx_ack.argtypes = [tx, u8p, ctypes.c_uint32]
        lib.answer_tx_ack.restype = ctypes.c_bool
        lib.ack_ttl.argtypes = [ctypes.c_uint8, ctypes.c_uint8]
        lib.ack_ttl.restype = ctypes.c_uint8
        _lib = lib
    return _lib


def _buf(data: bytes | bytearray | int):
    """A C byte array: `data` zero bytes, or a copy of `data`."""
    if isinstance(data, int):
        return (ctypes.c_uint8 * data)()
    return (ctypes.c_uint8 * max(len(data), 1)).from_buffer_copy(bytes(data) or b"\0")


def encode(msg_type: int, payload: bytes) -> bytes:
    out = _buf(MSG_OVERHEAD + len(payload))
    n = firmware().msg_encode(msg_type, _buf(payload), len(payload), out, len(out))
    if n < 0:
        raise ValueError(f"msg_encode refused a {len(payload)}-byte payload")
    return bytes(out[:n])


def decode(frame: bytes) -> tuple[int, bytes] | None:
    """(type, payload) of a valid frame, else None (bad start, length or CRC)."""
    m = _Msg()
    n = firmware().msg_decode(_buf(frame), len(frame), ctypes.byref(m))
    if n <= 0 or not firmware().msg_verify_crc(ctypes.byref(m)):
        return None
    return m.type, bytes(m.payload[:m.length])


# ── Payloads (packed little-endian, as the boards lay them out) ─────────


def _enroll(e: str) -> bytes:
    return e.encode()[:10].ljust(11, b"\0")


def quiz_answer(quiz_id: int, question: int, option: int, enrollment: str, device_id: int,
                response_ms: int) -> bytes:
    return struct.pack("<HBBI11sI", quiz_id, question, option, response_ms, _enroll(enrollment), device_id)


def poll_vote(poll_id: int, option: int, enrollment: str, device_id: int) -> bytes:
    return struct.pack("<HB11sI", poll_id, option, _enroll(enrollment), device_id)


def student_join(enrollment: str, device_id: int, name: str = "") -> bytes:
    return struct.pack("<11sIH32s", _enroll(enrollment), device_id, 0, name.encode()[:31])


# ── Radio ────────────────────────────────────────────────────────────────


@dataclass
class Radio:
    """ESP-NOW broadcast between the modules and the hub: no MAC-level
    acknowledgement, so a lost frame is simply gone. Faults are drawn from
    the seeded rng in a fixed order."""
    rng: random.Random
    loss: float = 0.0
    duplicate: float = 0.0
    corrupt: float = 0.0
    reorder: float = 0.0
    log: dict = field(default_factory=lambda: {"sent": 0, "lost": 0, "duplicated": 0, "corrupted": 0})

    def carry(self, packets: list[bytes]) -> list[bytes]:
        out = []
        for p in packets:
            self.log["sent"] += 1
            if len(p) > ESPNOW_MAX_DATA:
                raise ValueError(f"{len(p)}-byte ESP-NOW frame exceeds {ESPNOW_MAX_DATA}")
            if self.rng.random() < self.loss:
                self.log["lost"] += 1
                continue
            if self.rng.random() < self.corrupt:
                b = bytearray(p)
                b[self.rng.randrange(len(b))] ^= 1 << self.rng.randrange(8)
                p = bytes(b)
                self.log["corrupted"] += 1
            out.append(p)
            if self.rng.random() < self.duplicate:
                out.append(p)
                self.log["duplicated"] += 1
        if self.reorder and len(out) > 1:
            for i in range(len(out) - 1):
                if self.rng.random() < self.reorder:
                    out[i], out[i + 1] = out[i + 1], out[i]
        return out


# ── Boards ───────────────────────────────────────────────────────────────


@dataclass
class Student:
    """A student module: buttons A-D pick an option; the answer is sent once
    (student/main/main.c on_button_press: there is no acknowledgement or
    resend), behind the 6-byte mesh header with TTL 5."""
    enrollment: str
    device_id: int

    def frame(self, msg_type: int, payload: bytes) -> bytes:
        if len(payload) > ESPNOW_MAX_DATA - MESH_HDR - MSG_OVERHEAD:
            raise ValueError("mesh payload above the 238-byte budget")
        return struct.pack("<BIB", RELAY_TTL, self.device_id, 0) + encode(msg_type, payload)

    def press(self, quiz_id: int, question: int, button: int, response_ms: int) -> bytes:
        if not 0 <= button <= 3:
            raise ValueError("buttons A-D are 0-3")
        return self.frame(MSG_QUIZ_ANSWER, quiz_answer(quiz_id, question, button, self.enrollment,
                                                       self.device_id, response_ms))

    def vote(self, poll_id: int, button: int) -> bytes:
        return self.frame(MSG_POLL_VOTE, poll_vote(poll_id, button, self.enrollment, self.device_id))


class Hub:
    """The S3: decode, verify CRC, de-duplicate relay copies (firmware
    mesh_dedup_check), queue (64 entries), then pack SPI records into one
    4 KB slot per exchange (firmware spi_record_write / spi_slot_encode)."""

    def __init__(self):
        self.dedup = ctypes.create_string_buffer(1024)          # mesh_dedup_t, zero = empty
        self.queue: list[tuple[int, bytes]] = []
        self.log = {"accepted": 0, "bad_frame": 0, "duplicate": 0, "queue_full": 0}

    def receive(self, packet: bytes, now_ms: int) -> str:
        """'queued', 'duplicate', 'full' or 'bad' (mesh_master.c on_espnow_recv)."""
        if len(packet) <= MESH_HDR:
            self.log["bad_frame"] += 1
            return "bad"
        _ttl, sender, _hops = struct.unpack("<BIB", packet[:MESH_HDR])
        frame = packet[MESH_HDR:]
        if sender == 0:                                         # the hub's own broadcast, relayed back
            return "bad"
        if decode(frame) is None:
            self.log["bad_frame"] += 1
            return "bad"
        n = len(frame)
        if firmware().mesh_dedup_check(self.dedup, firmware().mesh_msg_id(sender, _buf(frame), n), now_ms):
            self.log["duplicate"] += 1
            return "duplicate"
        if len(self.queue) >= HUB_QUEUE - 1:
            self.log["queue_full"] += 1
            return "full"
        self.queue.append((sender, frame))
        self.log["accepted"] += 1
        return "queued"

    def ack(self, packet: bytes, seq: int) -> bytes:
        """The MSG_ACK the hub broadcasts for a frame it queued or already had (#181)."""
        _ttl, sender, hops = struct.unpack("<BIB", packet[:MESH_HDR])
        frame = packet[MESH_HDR:]
        payload = struct.pack("<IIH", firmware().mesh_msg_id(sender, _buf(frame), len(frame)), sender, seq & 0xFFFF)
        return struct.pack("<BIB", firmware().ack_ttl(hops, RELAY_TTL), 0, 0) + encode(MSG_ACK, payload)

    def flush_slot(self) -> bytes:
        """One SPI slot (4096 bytes) holding as many queued records as fit."""
        records = _buf(SPI_SLOT_PAYLOAD_MAX)
        total = 0
        while self.queue:
            sender, frame = self.queue[0]
            n = firmware().spi_record_write(ctypes.cast(ctypes.byref(records, total), ctypes.POINTER(ctypes.c_uint8)),
                                            SPI_SLOT_PAYLOAD_MAX - total, sender, _buf(frame), len(frame))
            if n < 0:
                break
            total += n
            self.queue.pop(0)
        slot = _buf(SPI_SLOT_BYTES)
        if firmware().spi_slot_encode(slot, records, total) != 0:
            raise RuntimeError("spi_slot_encode refused the batch")
        return bytes(slot)


class Gateway:
    """The C6: validate the slot (firmware spi_slot_decode), read records
    (spi_record_read), decode frames and build the batch JSON the backend
    receives at POST /api/device/batch (model of msg_to_json)."""

    def __init__(self, mac: str = "AABBCCDDEEFF"):
        self.mac = mac
        self.log = {"slots": 0, "bad_slots": 0, "records": 0}

    def receive_slot(self, slot: bytes) -> list[dict]:
        self.log["slots"] += 1
        out = _buf(SPI_SLOT_BYTES)
        n = firmware().spi_slot_decode(_buf(slot), out, SPI_SLOT_BYTES)
        if n < 0:
            self.log["bad_slots"] += 1
            return []
        items, off = [], 0
        sender = ctypes.c_uint32()
        fptr = ctypes.POINTER(ctypes.c_uint8)()
        flen = ctypes.c_uint16()
        while True:
            used = firmware().spi_record_read(ctypes.cast(ctypes.byref(out, off), ctypes.POINTER(ctypes.c_uint8)),
                                              n - off, ctypes.byref(sender), ctypes.byref(fptr), ctypes.byref(flen))
            if used <= 0:
                break
            off += used
            self.log["records"] += 1
            decoded = decode(bytes(fptr[:flen.value]))
            if decoded:
                item = self.to_json(*decoded)
                if item:
                    items.append(item)
        return items

    def to_json(self, msg_type: int, p: bytes) -> dict | None:
        def enroll(b: bytes) -> str:                    # enrollment_of(): 10 bytes, always terminated
            return b[:10].split(b"\0", 1)[0].decode("latin-1")
        if msg_type == MSG_QUIZ_ANSWER and len(p) >= 23:
            quiz_id, q, opt, ms, en, dev = struct.unpack("<HBBI11sI", p[:23])
            return {"type": "quiz_answer", "quiz_id": quiz_id, "question_order": q,
                    "enrollment_number": enroll(en), "selected_option": opt,
                    "response_time_ms": ms, "device_id": dev}
        if msg_type == MSG_POLL_VOTE and len(p) >= 18:
            poll_id, opt, en, dev = struct.unpack("<HB11sI", p[:18])
            return {"type": "poll_vote", "poll_id": poll_id, "enrollment_number": enroll(en),
                    "selected_option": opt, "device_id": dev}
        if msg_type == MSG_STUDENT_JOIN and len(p) >= 49:
            en, dev = struct.unpack("<11sI", p[:15])
            return {"type": "student_join", "enrollment_number": enroll(en), "device_mac": self.mac,
                    "class_code": "", "device_id": dev}
        return None


# ── A classroom ──────────────────────────────────────────────────────────


@dataclass
class Report:
    seed: int
    students: int
    sent: int
    delivered: list[dict]
    radio: dict
    hub: dict
    gateway: dict
    delivery: dict = field(default_factory=dict)          # with acknowledgements (#181)

    def summary(self) -> dict:
        answered = {d["enrollment_number"] for d in self.delivered if d["type"] in ("quiz_answer", "poll_vote")}
        return {"seed": self.seed, "students": self.students, "answers_sent": self.sent,
                "answers_delivered": len(self.delivered), "distinct_students_delivered": len(answered),
                "radio": self.radio, "hub": self.hub, "gateway": self.gateway, "delivery": self.delivery,
                "firmware_sources_sha256": _sources_digest()}


def _sources_digest() -> str:
    h = hashlib.sha256()
    for f in ("protocol.c", "protocol.h", "ota_chunk.c", "ota_chunk.h"):
        h.update((PROTOCOL / f).read_bytes())
    return h.hexdigest()


def run_quiz(students: int = 30, *, seed: int = 1, loss: float = 0.0, duplicate: float = 0.0,
             corrupt: float = 0.0, reorder: float = 0.0, quiz_id: int = 1, question: int = 0,
             spi_corrupt: float = 0.0, roll_prefix: str = "SIM", arrival_gap_ms: int = 20,
             spi_poll_ms: int = SPI_POLL_MS, ack: bool = False) -> Report:
    """Every student answers one question; the hub drains to the gateway in
    SPI slots. Returns what reached the gateway's batch.

    ack=False: a hub without acknowledgements (before #181): one send per press.
    ack=True: the hub confirms with MSG_ACK over the same lossy radio and each
    module runs the firmware's answer_tx_* state machine (resend, then give up)."""
    if ack:
        return _run_acked(students, seed, loss, duplicate, corrupt, quiz_id, question, spi_corrupt,
                          roll_prefix, arrival_gap_ms, spi_poll_ms)
    rng = random.Random(seed)
    radio = Radio(rng, loss, duplicate, corrupt, reorder)
    hub, gw = Hub(), Gateway()
    roster = [Student(f"{roll_prefix}{i:07d}"[:10], 0x1000 + i) for i in range(students)]
    packets = [s.press(quiz_id, question, rng.randrange(4), rng.randrange(200, 30_000)) for s in roster]
    delivered = []

    def exchange():                                             # one SPI slot, hub -> gateway
        slot = bytearray(hub.flush_slot())
        if rng.random() < spi_corrupt:
            slot[rng.randrange(4, 64)] ^= 0x01                 # a bit error inside the payload
        delivered.extend(gw.receive_slot(bytes(slot)))

    now = last_flush = 0
    for p in radio.carry(packets):
        now += rng.randrange(0, arrival_gap_ms + 1)             # presses arrive over time
        if now - last_flush >= spi_poll_ms:                     # spi_link_task wakes every poll interval
            exchange()
            last_flush = now
        hub.receive(p, now)
    while hub.queue:
        exchange()
    return Report(seed, students, len(packets), delivered, radio.log, hub.log, gw.log)


def _run_acked(students, seed, loss, duplicate, corrupt, quiz_id, question, spi_corrupt, roll_prefix,
               arrival_gap_ms, spi_poll_ms, tick_ms: int = 10, loop_ms: int = 200) -> Report:
    """Time-stepped room with acknowledgements: presses spread over
    students * arrival_gap_ms; radio latency 1-20 ms each way; the module's
    main loop runs every 200 ms (student main.c); the hub drains every
    SPI poll interval."""
    lib = firmware()
    rng = random.Random(seed)
    up = Radio(rng, loss, duplicate, corrupt)
    down = Radio(rng, loss, duplicate, corrupt)
    hub, gw = Hub(), Gateway()
    roster = [Student(f"{roll_prefix}{i:07d}"[:10], 0x1000 + i) for i in range(students)]
    press_at = {s.device_id: rng.randrange(0, max(1, students * arrival_gap_ms)) for s in roster}
    frames, txs = {}, {s.device_id: _AnswerTx() for s in roster}
    to_hub, to_modules = [], []                                  # (arrival_ms, packet)
    delivered, seq, resends = [], 0, 0
    end = max(press_at.values()) + 10_000

    def jitter():
        return rng.randrange(0, 401)                             # ANSWER_JITTER_MS

    for now in range(0, end, tick_ms):
        for s in roster:
            if press_at[s.device_id] <= now and s.device_id not in frames:
                frames[s.device_id] = f = s.press(quiz_id, question, rng.randrange(4), rng.randrange(200, 30_000))
                frame = f[MESH_HDR:]
                lib.answer_tx_start(ctypes.byref(txs[s.device_id]),
                                    lib.mesh_msg_id(s.device_id, _buf(frame), len(frame)), now, jitter())
                to_hub += [(now + rng.randrange(1, 21), p) for p in up.carry([f])]
        for item in [x for x in to_hub if x[0] <= now]:
            to_hub.remove(item)
            outcome = hub.receive(item[1], now)
            if outcome in ("queued", "duplicate"):
                seq += 1
                to_modules += [(now + rng.randrange(1, 21), p) for p in down.carry([hub.ack(item[1], seq)])]
        for item in [x for x in to_modules if x[0] <= now]:
            to_modules.remove(item)
            got = decode(item[1][MESH_HDR:])
            if got and got[0] == MSG_ACK:
                _mid, dev, _seq = struct.unpack("<IIH", got[1])
                if dev in txs:
                    lib.answer_tx_ack(ctypes.byref(txs[dev]), _buf(got[1]), dev)
        if now % loop_ms == 0:
            for dev, tx in txs.items():
                if lib.answer_tx_poll(ctypes.byref(tx), now, jitter()):
                    resends += 1
                    to_hub += [(now + rng.randrange(1, 21), p) for p in up.carry([frames[dev]])]
        if now % spi_poll_ms == 0 and hub.queue:
            slot = bytearray(hub.flush_slot())
            if rng.random() < spi_corrupt:
                slot[rng.randrange(4, 64)] ^= 0x01
            delivered += gw.receive_slot(bytes(slot))
    while hub.queue:
        delivered += gw.receive_slot(hub.flush_slot())
    states = [tx.state for tx in txs.values()]
    return Report(seed, students, len(frames), delivered, up.log, hub.log, gw.log, {
        "acks_sent": seq, "acks_radio": down.log, "resends": resends,
        "confirmed": states.count(ANSWER_DELIVERED), "told_not_delivered": states.count(ANSWER_FAILED)})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--students", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    for f in ("loss", "duplicate", "corrupt", "reorder", "spi-corrupt"):
        ap.add_argument(f"--{f}", type=float, default=0.0)
    ap.add_argument("--ack", action="store_true", help="hub acknowledgements and module resends (#181)")
    a = ap.parse_args(argv)
    r = run_quiz(a.students, seed=a.seed, loss=a.loss, duplicate=a.duplicate, corrupt=a.corrupt,
                 reorder=a.reorder, spi_corrupt=a.spi_corrupt, ack=a.ack)
    json.dump(r.summary(), sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
