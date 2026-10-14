"""v2.2: classroom protocol simulation (firmware/sim/classroom_sim.py).

The frame, de-duplication and SPI code under test is the firmware's own C
(firmware/protocol), compiled for the host. Fault injection is seeded; a
failure message includes the seed so the run can be repeated."""

import random
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sim"))
import classroom_sim as sim  # noqa: E402

pytestmark = pytest.mark.skipif(not (shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")),
                                reason="needs a C compiler for the firmware protocol code")


def _sent(seed, students):
    """The answers run_quiz sends, recomputed from the same seed."""
    rng = random.Random(seed)
    roster = [sim.Student(f"SIM{i:07d}", 0x1000 + i) for i in range(students)]
    return {s.enrollment: (rng.randrange(4), rng.randrange(200, 30_000)) for s in roster}


def test_frames_round_trip_through_the_firmware_codec():
    payload = sim.quiz_answer(7, 2, 3, "ABCDE12345", 0x1234, 1500)
    t, p = sim.decode(sim.encode(sim.MSG_QUIZ_ANSWER, payload))
    assert (t, p) == (sim.MSG_QUIZ_ANSWER, payload)


def test_corrupted_frame_is_rejected_by_the_firmware_crc():
    frame = bytearray(sim.encode(sim.MSG_QUIZ_ANSWER, sim.quiz_answer(1, 0, 0, "ABCDE12345", 1, 0)))
    for i in range(1, len(frame)):
        bad = bytearray(frame)
        bad[i] ^= 0x10
        assert sim.decode(bytes(bad)) is None, f"flipped byte {i} was accepted"


def test_mesh_payload_budget_is_enforced():
    s = sim.Student("ABCDE12345", 1)
    assert len(s.frame(sim.MSG_QUIZ_ANSWER, b"x" * 238)) == 250          # the ESP-NOW maximum exactly
    with pytest.raises(ValueError):
        s.frame(sim.MSG_QUIZ_ANSWER, b"x" * 239)


def test_clean_link_delivers_every_answer_once_with_its_fields():
    r = sim.run_quiz(30, seed=11)
    sent = _sent(11, 30)
    assert len(r.delivered) == 30
    for d in r.delivered:
        option, ms = sent[d["enrollment_number"]]
        assert (d["selected_option"], d["response_time_ms"], d["quiz_id"]) == (option, ms, 1)


@pytest.mark.parametrize("seed", range(1, 6))
def test_duplicates_and_reordering_never_double_count(seed):
    r = sim.run_quiz(60, seed=seed, duplicate=0.5, reorder=0.5)
    rolls = [d["enrollment_number"] for d in r.delivered]
    assert len(rolls) == len(set(rolls)) == 60, f"seed={seed}"
    assert r.hub["duplicate"] == r.radio["duplicated"], f"seed={seed}"


@pytest.mark.parametrize("seed", range(1, 6))
def test_corrupted_radio_frames_are_dropped_not_misread(seed):
    r = sim.run_quiz(60, seed=seed, corrupt=0.3)
    sent = _sent(seed, 60)
    assert r.radio["corrupted"] > 0
    for d in r.delivered:                    # nothing delivered differs from what a student sent
        assert d["enrollment_number"] in sent and d["selected_option"] == sent[d["enrollment_number"]][0], f"seed={seed}"


def test_without_acknowledgements_lost_answers_stay_lost():
    """A hub without #181 (or MESH_ANSWER_ACK off): the module sends its
    answer once over broadcast ESP-NOW, which has no acknowledgement, so every
    frame the radio loses is a missing answer."""
    r = sim.run_quiz(100, seed=4, loss=0.1)
    assert r.radio["lost"] > 0
    assert len(r.delivered) == 100 - r.radio["lost"]


def test_old_firmware_loses_a_batch_to_corrupted_spi_exchanges():
    """Before #182: both ends drop a slot once clocked, so a slot that fails its
    CRC at the gateway is gone, with every record in it."""
    r = sim.run_quiz(30, seed=5, spi_corrupt=1.0, spi_ack=False)
    assert r.gateway["bad_slots"] == r.gateway["slots"] and r.delivered == []


@pytest.mark.parametrize("seed", range(1, 6))
def test_acknowledged_spi_loses_nothing_to_corrupted_exchanges(seed):
    """#182: spi_link.c on both ends. A third of the slots in each direction
    fail their CRC; every answer still reaches the gateway exactly once."""
    r = sim.run_quiz(300, seed=seed, spi_corrupt=0.3)
    rolls = [d["enrollment_number"] for d in r.delivered]
    assert len(rolls) == len(set(rolls)) == 300, f"seed={seed}"
    assert r.gateway["bad_slots"] > 0, f"seed={seed}"
    old = sim.run_quiz(300, seed=seed, spi_corrupt=0.3, spi_ack=False)
    assert len(old.delivered) < 300, f"seed={seed}"                  # what #182 fixes


def test_a_very_noisy_spi_link_still_delivers_everything_once():
    r = sim.run_quiz(100, seed=7, spi_corrupt=0.6, max_exchanges=5000)
    rolls = [d["enrollment_number"] for d in r.delivered]
    assert len(rolls) == len(set(rolls)) == 100
    assert r.gateway["repeats"] > 0          # resends happened and were not delivered twice


def test_full_room_fits_the_hub_queue_at_the_default_poll_interval():
    r = sim.run_quiz(300, seed=3)
    assert r.hub["queue_full"] == 0 and len(r.delivered) == 300


def test_hub_queue_overflows_when_presses_outrun_the_spi_poll():
    """Boundary: the hub holds 63 frames (64-entry ring, one slot free). All
    300 presses inside one 500 ms poll overflow it; the overflow is counted."""
    r = sim.run_quiz(300, seed=3, arrival_gap_ms=0, spi_poll_ms=500)
    assert r.hub["accepted"] == 63 and r.hub["queue_full"] == 300 - 63


def test_gateway_terminates_an_unterminated_enrollment():
    gw = sim.Gateway()
    payload = bytearray(sim.quiz_answer(1, 0, 2, "ABCDE12345", 9, 10))
    payload[8 + 10] = ord("Z")                         # the 11th enrollment byte (after 8 header bytes), normally NUL
    item = gw.to_json(sim.MSG_QUIZ_ANSWER, bytes(payload))
    assert item["enrollment_number"] == "ABCDE12345"


def test_same_seed_same_run_and_report_names_the_sources():
    a = sim.run_quiz(50, seed=9, loss=0.2, duplicate=0.2, corrupt=0.1, reorder=0.2).summary()
    b = sim.run_quiz(50, seed=9, loss=0.2, duplicate=0.2, corrupt=0.1, reorder=0.2).summary()
    assert a == b and a["seed"] == 9 and len(a["firmware_sources_sha256"]) == 64
    c = sim.run_quiz(50, seed=10, loss=0.2, duplicate=0.2, corrupt=0.1, reorder=0.2).summary()
    assert c["radio"] != a["radio"]


def test_command_line_prints_a_json_report(capsys):
    assert sim.main(["--students", "5", "--seed", "2"]) == 0
    assert '"answers_delivered": 5' in capsys.readouterr().out


# ── Acknowledgements (#181): the firmware's answer_tx_* state machine ──

@pytest.mark.parametrize("seed", [1, 2, 3])
def test_acknowledged_answers_get_through_ten_percent_loss(seed):
    r = sim.run_quiz(300, seed=seed, loss=0.1, ack=True).summary()
    assert r["distinct_students_delivered"] == 300, f"seed={seed}"
    # a confirmation can be lost four times over (0.19^4 per module): a few
    # students are told to press again although their answer arrived
    assert r["delivery"]["told_not_delivered"] <= 3, f"seed={seed}"
    without = sim.run_quiz(300, seed=seed, loss=0.1).summary()
    assert without["distinct_students_delivered"] < 290, f"seed={seed}"        # what #181 fixes


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_heavy_loss_most_get_through_and_the_rest_are_told(seed):
    r = sim.run_quiz(300, seed=seed, loss=0.3, ack=True).summary()
    d = r["delivery"]
    assert r["distinct_students_delivered"] >= 295, f"seed={seed}"
    # Every module either got its confirmation or was told to press again.
    assert d["confirmed"] + d["told_not_delivered"] == 300, f"seed={seed}"


def test_a_dead_link_tells_every_student_after_three_resends():
    r = sim.run_quiz(30, seed=2, loss=1.0, ack=True).summary()
    assert r["answers_delivered"] == 0
    assert r["delivery"]["resends"] == 30 * 3 and r["delivery"]["told_not_delivered"] == 30


def test_resends_never_reach_the_results_twice():
    """Resends of an answer the hub already queued are duplicates. In a full
    room the hub's 64-entry de-duplication table can forget an id within
    seconds, so a resend may be queued again (hub "accepted" > students); the
    server keeps one answer per student and question (backend test)."""
    r = sim.run_quiz(300, seed=1, loss=0.1, ack=True)
    rolls = {d["enrollment_number"] for d in r.delivered}
    assert len(rolls) == 300 and r.hub["accepted"] >= 300


def test_hub_ack_reaches_only_as_far_as_the_module():
    hub = sim.Hub()
    direct = sim.Student("ABCDE12345", 7).press(1, 0, 2, 100)
    relayed = bytes([4]) + direct[1:5] + bytes([2]) + direct[6:]          # came through 2 relays
    assert hub.ack(direct, 1)[0] == 1 and hub.ack(relayed, 2)[0] == 3
    t, p = sim.decode(hub.ack(direct, 1)[sim.MESH_HDR:])
    assert t == sim.MSG_ACK and len(p) == 10
