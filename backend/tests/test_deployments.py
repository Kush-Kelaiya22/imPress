"""#38 + #34: OTA deployments: selection, staged rollout, the per-device state
machine, retries, timeouts, pause/resume/cancel, durability."""

from datetime import timedelta

import pytest
from sqlalchemy import select, update

from conftest import DEVICE, DEVICE_KEY, auth, login, make_user, upload_firmware


def _mac(i):
    return f"a1b2c3d4e5{i:02x}"


@pytest.fixture
def h(client):
    h = auth(login(client))
    upload_firmware(client, h, "impress_class_s3", "2.2.0")
    return h


def _register(client, i, device_type="s3", version="2.1.0"):
    r = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": _mac(i), "device_type": device_type, "device_name": f"{device_type}-{i}",
        "firmware_version": version})
    assert r.status_code == 200, r.text
    return r.json()["device_id"]


def _artifact_id(client, h, target="s3", version="2.2.0"):
    return next(a["id"] for a in client.get("/api/admin/firmware", headers=h).json()
                if (a["target"], a["version"]) == (target, version))


def _deploy(client, h, **body):
    body.setdefault("artifact_id", _artifact_id(client, h))
    return client.post("/api/admin/deployments", headers=h, json=body)


def _status(client, i, state, version="", **kw):
    return client.post("/api/device/ota/status", headers=DEVICE,
                       json={"mac_address": _mac(i), "state": state, "version": version, **kw})


def _advance(db):
    from app.services.deployments import advance_all
    return db(lambda s: advance_all(s))


def _dep(client, h, dep_id):
    return client.get(f"/api/admin/deployments/{dep_id}", headers=h).json()


def _states(dep):
    return [t["state"] for t in dep["targets"]]


def _set_firmware_version(db, i, version):
    from app.models import EspDevice

    async def go(s):
        await s.execute(update(EspDevice).where(EspDevice.mac_address == _mac(i)).values(firmware_version=version))
    db(go)


# ── Creating deployments ────────────────────────────────────────────────────

def test_only_approved_images_and_an_explicit_selection(client, h):
    upload_firmware(client, h, "impress_class_s3", "2.3.0", approve=False)
    _register(client, 1)
    r = _deploy(client, h, artifact_id=_artifact_id(client, h, version="2.3.0"), device_ids=[1])
    assert r.status_code == 409 and "only approved images deploy" in r.json()["detail"]
    assert _deploy(client, h).status_code == 422                          # no selection at all


def test_incompatible_and_ineligible_devices_are_excluded_with_reasons(client, db, h):
    ok = _register(client, 1)
    c6 = _register(client, 2, "c6")
    student = _register(client, 3, "student")
    same = _register(client, 4, version="2.2.0")
    newer = _register(client, 5, version="3.0.0")
    disabled = _register(client, 6)
    client.post(f"/api/admin/modules/{disabled}/access", headers=h, json={"is_active": False})
    r = _deploy(client, h, device_ids=[ok, c6, student, same, newer, disabled]).json()
    assert [t["device_id"] for t in r["deployment"]["targets"]] == [ok]
    reasons = {e["device_id"]: e["reason"] for e in r["excluded"]}
    assert "can't run a s3 image" in reasons[c6] and "can't run a s3 image" in reasons[student]
    assert reasons[same] == "already running 2.2.0"
    assert "would downgrade 3.0.0 → 2.2.0" in reasons[newer]
    assert reasons[disabled] == "device is disabled"
    # the same device can't be in two active deployments
    again = _deploy(client, h, device_ids=[ok])
    assert again.status_code == 409 and "already in deployment" in again.json()["detail"]["excluded"][0]["reason"]


def test_selection_by_type_version_and_class(client, db, h):
    ids = [_register(client, i, version=v) for i, v in ((1, "2.0.0"), (2, "2.1.0"), (3, "2.1.0"))]
    plan = client.post("/api/admin/deployments?dry_run=true", headers=h,
                       json={"artifact_id": _artifact_id(client, h), "running_version": "2.1.0"}).json()
    assert [x["device_id"] for x in plan["included"]] == ids[1:]
    plan = client.post("/api/admin/deployments?dry_run=true", headers=h,
                       json={"artifact_id": _artifact_id(client, h), "all_compatible": True,
                             "strategy": {"canary": 1, "batch_size": 1}}).json()
    assert [x["stage"] for x in plan["included"]] == [0, 1, 2]
    # by class: the class's gateway (C6) and the S3 it relays
    cid = client.post("/api/admin/classes", headers=h, json={"name": "Lab", "code": "LAB1"}).json()["id"]
    client.post(f"/api/classes/{cid}/activate", headers=h)
    c6 = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "48:F6:EE:00:00:01", "device_type": "c6", "device_name": "gw"}).json()["device_id"]
    client.post(f"/api/admin/modules/{c6}/link-device", headers=h, json={"device_id": ids[0]})
    plan = client.post("/api/admin/deployments?dry_run=true", headers=h,
                       json={"artifact_id": _artifact_id(client, h), "class_id": cid}).json()
    assert [x["device_id"] for x in plan["included"]] == [ids[0]]
    assert {e["device_id"] for e in plan["excluded"]} == {c6}           # c6 can't take an s3 image


# ── Staged rollout ──────────────────────────────────────────────────────────

def test_canary_then_batches_with_a_concurrency_limit(client, db, h):
    ids = [_register(client, i) for i in range(1, 7)]
    dep = _deploy(client, h, device_ids=ids,
                  strategy={"canary": 1, "batch_size": 4, "max_concurrent": 2}).json()["deployment"]
    assert _states(dep) == ["queued"] + ["waiting"] * 5                  # only the canary starts
    assert [t["stage"] for t in dep["targets"]] == [0, 1, 1, 1, 1, 2]
    _status(client, 1, "success", "2.2.0")
    _advance(db)
    dep = _dep(client, h, dep["id"])
    assert _states(dep) == ["success", "queued", "queued", "waiting", "waiting", "waiting"]   # 2 at a time
    for i in (2, 3):
        _status(client, i, "success", "2.2.0")
    _advance(db)
    assert _states(_dep(client, h, dep["id"]))[3:] == ["queued", "queued", "waiting"]
    for i in (4, 5):
        _status(client, i, "success", "2.2.0")
    _advance(db)
    assert _states(_dep(client, h, dep["id"]))[5] == "queued"           # last batch
    _status(client, 6, "success", "2.2.0")
    _advance(db)
    final = _dep(client, h, dep["id"])
    assert final["state"] == "completed" and final["counts"] == {"success": 6}
    assert {d["firmware_version"] for d in client.get("/api/admin/modules", headers=h).json()} == {"2.2.0"}


def test_failed_canary_pauses_the_rollout_until_resumed(client, db, h):
    ids = [_register(client, i) for i in range(1, 4)]
    dep = _deploy(client, h, device_ids=ids, strategy={"canary": 1, "max_attempts": 1}).json()["deployment"]
    _status(client, 1, "failed", error="esp_ota_end: image invalid", error_code=0x1503)
    _advance(db)
    d = _dep(client, h, dep["id"])
    assert d["state"] == "paused" and "canary" in d["note"]
    assert _states(d) == ["failed", "waiting", "waiting"]                # nobody else got it
    assert d["targets"][0]["error_code"] == 0x1503
    r = client.post(f"/api/admin/deployments/{dep['id']}/resume", headers=h).json()
    assert r["state"] == "running" and _states(r)[1:] == ["queued", "queued"]
    _advance(db)
    assert _dep(client, h, dep["id"])["state"] == "running"             # accepted failures don't re-pause


def test_failures_are_retried_a_bounded_number_of_times(client, db, h):
    from app.models import EspDevice
    _register(client, 1)
    dep = _deploy(client, h, device_ids=[1], strategy={"max_attempts": 2}).json()["deployment"]
    _status(client, 1, "downloading")
    _status(client, 1, "failed", error="http 503")

    async def pending(s):
        return (await s.execute(select(EspDevice).where(EspDevice.mac_address == _mac(1)))).scalar_one().pending_version
    assert db(pending) == "2.2.0"                                        # kept for the retry
    _advance(db)
    t = _dep(client, h, dep["id"])["targets"][0]
    assert (t["state"], t["attempts"]) == ("queued", 2)
    _status(client, 1, "failed")
    _advance(db)
    d = _dep(client, h, dep["id"])
    assert (d["targets"][0]["state"], d["state"]) == ("failed", "completed")
    assert db(pending) == ""


def test_timeouts_mark_unreachable_or_timed_out(client, db, h):
    from app.models import DeploymentTarget
    from app.timeutil import istnow
    _register(client, 1)
    _register(client, 2)
    dep = _deploy(client, h, device_ids=[1, 2], strategy={"canary": 2, "max_attempts": 1,
                                                          "timeout_s": 60}).json()["deployment"]
    _status(client, 2, "downloading")

    async def age(s):
        await s.execute(update(DeploymentTarget).values(started_at=istnow() - timedelta(seconds=61)))
    db(age)
    _advance(db)
    d = _dep(client, h, dep["id"])
    assert _states(d) == ["unreachable", "timed_out"]       # never answered / stalled mid-download
    assert "not finished within 60 s" in d["targets"][1]["error"]


# ── Device-side state machine ───────────────────────────────────────────────

def test_progress_is_forward_only_and_duplicates_are_harmless(client, db, h):
    _register(client, 1)
    _deploy(client, h, device_ids=[1])
    for state in ("precheck", "downloading", "downloading", "verifying", "installing", "rebooting", "health_check"):
        r = _status(client, 1, state)
        assert r.status_code == 200 and r.json()["state"] == state, (state, r.text)
    back = _status(client, 1, "downloading")
    assert back.status_code == 409 and "backwards" in back.json()["detail"]
    assert _status(client, 1, "teleporting").status_code == 409
    assert _status(client, 1, "success", "2.2.0").json()["state"] == "success"
    assert _status(client, 1, "precheck").status_code == 409             # nothing in progress any more


def test_success_needs_the_expected_version(client, db, h):
    _register(client, 1)
    dep = _deploy(client, h, device_ids=[1], strategy={"max_attempts": 1}).json()["deployment"]
    assert _status(client, 1, "success", "2.1.0").json()["state"] == "failed"
    t = _dep(client, h, dep["id"])["targets"][0]
    assert "device runs 2.1.0 after the update, expected 2.2.0" in t["error"]


def test_rolled_back_keeps_the_old_version(client, db, h):
    _register(client, 1, version="2.1.0")
    _deploy(client, h, device_ids=[1], strategy={"max_attempts": 1})
    _status(client, 1, "rolled_back", "2.2.0")            # the S3 reports the target that failed
    dev = next(d for d in client.get("/api/admin/modules", headers=h).json() if d["mac_address"] == _mac(1))
    assert (dev["firmware_version"], dev["ota_status"], dev["pending_version"]) == ("2.1.0", "rolled_back", "")


def test_server_observes_precheck_and_download(client, db, h):
    _register(client, 1)
    dep = _deploy(client, h, device_ids=[1]).json()["deployment"]
    chk = client.post("/api/device/firmware/check", headers=DEVICE,
                      json={"mac_address": _mac(1), "current_version": "2.1.0"}).json()
    assert chk["update_available"] and len(chk["sha256"]) == 64 and chk["deployment_id"] == dep["id"]
    assert _dep(client, h, dep["id"])["targets"][0]["state"] == "precheck"
    dl = client.get("/api/device/firmware/download", headers=DEVICE,
                    params={"mac_address": _mac(1), "version": "2.2.0"})
    assert dl.status_code == 200 and dl.headers["x-firmware-sha256"] == chk["sha256"]
    assert _dep(client, h, dep["id"])["targets"][0]["state"] == "downloading"


def test_s3_results_relayed_by_the_c6_drive_the_state_machine(client, db, h):
    _register(client, 1)
    dep = _deploy(client, h, device_ids=[1]).json()["deployment"]
    client.post("/api/device/batch", headers=DEVICE, json={"device_type": "c6", "messages": [
        {"type": "ota_result", "mac_address": _mac(1), "version": "2.2.0", "result": "applied"}]})
    assert _dep(client, h, dep["id"])["targets"][0]["state"] == "success"


# ── Operator controls ───────────────────────────────────────────────────────

def test_cancel_stops_only_devices_that_have_not_started_installing(client, db, h):
    for i in range(1, 4):
        _register(client, i)
    dep = _deploy(client, h, device_ids=[1, 2, 3], strategy={"canary": 2}).json()["deployment"]
    _status(client, 1, "installing")
    d = client.post(f"/api/admin/deployments/{dep['id']}/cancel", headers=h).json()
    assert d["state"] == "cancelled" and _states(d) == ["installing", "cancelled", "cancelled"]
    assert _status(client, 1, "rebooting").status_code == 200           # the installing one finishes


def test_pause_and_idempotency_key(client, db, h):
    _register(client, 1)
    first = _deploy(client, h, device_ids=[1], idempotency_key="rollout-42").json()
    replay = _deploy(client, h, device_ids=[1], idempotency_key="rollout-42").json()
    assert replay["replayed"] is True and replay["deployment"]["id"] == first["deployment"]["id"]
    dep_id = first["deployment"]["id"]
    assert client.post(f"/api/admin/deployments/{dep_id}/pause", headers=h).json()["state"] == "paused"
    assert client.post(f"/api/admin/deployments/{dep_id}/pause", headers=h).status_code == 409
    listed = client.get("/api/admin/deployments", headers=h).json()
    assert [(x["id"], x["state"], x["total"]) for x in listed] == [(dep_id, "paused", 1)]


def test_rollback_needs_explicit_confirmation(client, db, h):
    upload_firmware(client, h, "impress_class_s3", "2.0.0")
    _register(client, 1, version="2.2.0")
    old = _artifact_id(client, h, version="2.0.0")
    assert _deploy(client, h, artifact_id=old, device_ids=[1]).status_code == 409
    dep = _deploy(client, h, artifact_id=old, device_ids=[1], allow_downgrade=True).json()["deployment"]
    assert dep["kind"] == "rollback" and dep["version"] == "2.0.0"
    # the per-device push takes the same confirmation
    _register(client, 2, version="2.2.0")
    r = client.post("/api/admin/modules/2/ota", headers=h, json={"version": "2.0.0"})
    assert r.status_code == 409 and "would downgrade" in r.json()["detail"]
    assert client.post("/api/admin/modules/2/ota", headers=h,
                       json={"version": "2.0.0", "allow_downgrade": True}).status_code == 200


def test_activation_prompts_the_device_through_its_gateway(client, db, h):
    from app.models import EspDevice
    cid = client.post("/api/admin/classes", headers=h, json={"name": "Lab", "code": "LAB1"}).json()["id"]
    client.post(f"/api/classes/{cid}/activate", headers=h)
    c6 = client.post("/api/device/register", headers=DEVICE, json={
        "mac_address": "48:F6:EE:00:00:01", "device_type": "c6", "device_name": "gw"}).json()["device_id"]
    s3 = _register(client, 1)

    async def link(s):
        await s.execute(update(EspDevice).where(EspDevice.id == s3).values(gateway_id=c6))
    db(link)
    with client.websocket_connect(f"/ws/class/{cid}?role=device&api_key={DEVICE_KEY}") as ws:
        ws.receive_json()
        _deploy(client, h, device_ids=[s3])
        frame = ws.receive_json()
    assert frame["command"] == "ota_update"
    assert frame["payload"] == {"device_type": "s3", "version": "2.2.0", "mac_address": _mac(1)}


def test_a_restarted_backend_resumes_running_deployments(client, db, h):
    """All state is in the database: a fresh session (as after a restart)
    advances exactly where the old one stopped."""
    ids = [_register(client, i) for i in range(1, 4)]
    dep = _deploy(client, h, device_ids=ids, strategy={"canary": 1, "batch_size": 2}).json()["deployment"]
    _status(client, 1, "success", "2.2.0")
    from app.database import engine
    db(lambda s: engine.dispose())                       # drop every connection, like a restart
    _advance(db)
    assert _states(_dep(client, h, dep["id"])) == ["success", "queued", "queued"]


def test_admin_only(client, h):
    _, teacher = make_user(client, h, "teach1")
    assert client.get("/api/admin/deployments", headers=teacher).status_code == 403
    assert client.post("/api/admin/deployments", headers=teacher, json={"artifact_id": 1}).status_code == 403
