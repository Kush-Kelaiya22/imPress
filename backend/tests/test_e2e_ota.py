"""#43 end to end: a firmware release reaches three rooms through the staged
deployment engine, each gateway behaving like firmware/class_c6/main/ota.c,
plus the update faults the engine must survive (corrupt download, power loss
mid-update, an image that fails its health check)."""

from contextlib import ExitStack
from datetime import timedelta

import pytest
from sqlalchemy import update

from conftest import DEVICE_KEY, auth, login, make_class, upload_firmware
from gateway_sim import Gateway


@pytest.fixture
def rooms(client):
    """Three rooms, each with a v2.1.0 gateway; a c6 2.2.0 image approved."""
    h = auth(login(client))
    image = upload_firmware(client, h, "impress_class_c6", "2.2.0")
    gws, cids = [], []
    for i in range(3):
        cid = make_class(client, h, f"Room {i}", f"RM{i}00", classroom_code=f"RM-{i}")
        gw = Gateway(client, f"48:F6:EE:00:00:0{i}", f"RM-{i}", name=f"gw{i}")
        assert gw.register()["class_id"] == cid
        gw.heartbeat()
        gws.append(gw), cids.append(cid)
    art = next(a for a in client.get("/api/admin/firmware", headers=h).json() if a["target"] == "c6")
    return h, gws, cids, art, image


def _deploy(client, h, art, **strategy):
    r = client.post("/api/admin/deployments", headers=h, json={
        "artifact_id": art["id"], "device_type": "c6", "all_compatible": True,
        "strategy": {"canary": 1, "batch_size": 2, **strategy}})
    assert r.status_code == 200, r.text
    return r.json()["deployment"]["id"]


def _advance(db):
    from app.services.deployments import advance_all
    db(lambda s: advance_all(s))


def _dep(client, h, dep_id):
    return client.get(f"/api/admin/deployments/{dep_id}", headers=h).json()


def _prompt(ws, gw):
    """Read this room's socket until the gateway's own OTA prompt."""
    while True:
        f = ws.receive_json()
        if gw.ota_prompt(f):
            return f


def _sockets(stack, client, cids):
    socks = [stack.enter_context(client.websocket_connect(f"/ws/class/{c}?role=device&api_key={DEVICE_KEY}"))
             for c in cids]
    for s in socks:
        s.receive_json()                                   # "connected"
    return socks


def test_staged_rollout_reaches_every_room(client, db, rooms):
    h, gws, cids, art, image = rooms
    with ExitStack() as stack:
        socks = _sockets(stack, client, cids)
        dep_id = _deploy(client, h, art)
        d = _dep(client, h, dep_id)
        assert [t["stage"] for t in d["targets"]] == [0, 1, 1]          # canary, then a batch of two
        canary = d["targets"][0]["mac_address"]
        order = sorted(range(3), key=lambda i: gws[i].mac != canary)   # the canary's room first

        first = order[0]
        _prompt(socks[first], gws[first])
        assert gws[first].update() == "success"
        assert sorted(t["state"] for t in _dep(client, h, dep_id)["targets"]) == ["success", "waiting", "waiting"]

        _advance(db)                                                   # canary healthy → next stage
        for i in order[1:]:
            _prompt(socks[i], gws[i])
            assert gws[i].update() == "success"
        _advance(db)

    d = _dep(client, h, dep_id)
    assert d["state"] == "completed" and {t["state"] for t in d["targets"]} == {"success"}
    assert gws[0].reports == ["precheck", "downloading", "verifying", "installing", "rebooting",
                              "health_check", "success"]
    mods = client.get("/api/admin/modules", headers=h).json()
    assert {(m["firmware_version"], m["pending_version"], m["health"]) for m in mods} == {("2.2.0", "", "ONLINE")}
    detail = client.get(f"/api/admin/firmware/{art['id']}", headers=h).json()
    assert detail["artifact"]["devices_running"] == 3


def test_corrupt_download_is_refused_then_retried(client, db, rooms):
    h, gws, cids, art, _ = rooms
    with ExitStack() as stack:
        [sock] = _sockets(stack, client, cids[:1])
        r = client.post("/api/admin/deployments", headers=h, json={
            "artifact_id": art["id"], "device_ids": [1], "strategy": {"max_attempts": 2}})
        dep_id = r.json()["deployment"]["id"]
        _prompt(sock, gws[0])
        assert gws[0].update(corrupt=True) == "failed"                 # sha256 mismatch: nothing installed
        t = _dep(client, h, dep_id)["targets"][0]
        assert (t["state"], t["error_code"]) == ("failed", 0x1503) and gws[0].version == "2.1.0"
        _advance(db)                                                   # attempt 2
        _prompt(sock, gws[0])
        assert gws[0].update() == "success"
    t = _dep(client, h, dep_id)["targets"][0]
    assert (t["state"], t["attempts"]) == ("success", 2)


def test_power_loss_mid_update_times_out_and_is_retried(client, db, rooms):
    from app.models import DeploymentTarget
    from app.timeutil import istnow
    h, gws, cids, art, _ = rooms
    with ExitStack() as stack:
        [sock] = _sockets(stack, client, cids[:1])
        dep_id = client.post("/api/admin/deployments", headers=h, json={
            "artifact_id": art["id"], "device_ids": [1], "strategy": {"timeout_s": 120}}).json()["deployment"]["id"]
        _prompt(sock, gws[0])
        assert gws[0].update(stop_after="installing") == "silent"     # power cut while writing flash

        async def later(s):
            await s.execute(update(DeploymentTarget).values(started_at=istnow() - timedelta(seconds=121)))
        db(later)
        _advance(db)
        t = _dep(client, h, dep_id)["targets"][0]
        assert t["state"] == "queued" and t["attempts"] == 2           # timed out, offered again
        # on power-up the old image still runs (the new slot was never made bootable)
        gws[0].register()
        _prompt(sock, gws[0])
        assert gws[0].update() == "success"


def test_an_unhealthy_image_rolls_back_and_stops_the_rollout(client, db, rooms):
    h, gws, cids, art, _ = rooms
    with ExitStack() as stack:
        socks = _sockets(stack, client, cids)
        dep_id = _deploy(client, h, art, max_attempts=1)
        canary = _dep(client, h, dep_id)["targets"][0]["mac_address"]
        i = next(i for i, g in enumerate(gws) if g.mac == canary)
        _prompt(socks[i], gws[i])
        assert gws[i].update(healthy=False) == "rolled_back"
        _advance(db)
    d = _dep(client, h, dep_id)
    assert d["state"] == "paused"                                      # max_failures 0: the batch never starts
    assert sorted(t["state"] for t in d["targets"]) == ["rolled_back", "waiting", "waiting"]
    mods = {m["mac_address"]: m for m in client.get("/api/admin/modules", headers=h).json()}
    assert mods[canary]["firmware_version"] == "2.1.0" and mods[canary]["health"] == "ERROR"
