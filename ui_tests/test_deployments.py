"""#38/#34: a staged OTA rollout from the Firmware page."""

import os
import sys

from playwright.sync_api import expect

from conftest import ROOT, SHOTS, login

sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend" / "tests")]
os.environ.setdefault("IMPRESS_DEBUG", "true")
from firmware_images import make_image  # noqa: E402


def _mac(i):
    return f"a1b2c3d4e5{i:02x}"


def test_preview_start_progress_pause_and_resume(server, page):
    base, api = server
    art = api.upload("/api/admin/firmware", "s3.bin", make_image("impress_class_s3", "2.2.0"))
    api(f"/api/admin/firmware/{art['id']}/approve", {})
    for i in range(1, 4):
        api.device("/api/device/register", {"mac_address": _mac(i), "device_type": "s3",
                                            "device_name": f"Hub {i}", "firmware_version": "2.1.0"})
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/firmware")
    page.locator("tr", has_text="v2.2.0").locator("[data-act=deploy]").click()
    dialog = page.locator(".modal")
    page.select_option("#dep-mode", "all")
    page.fill("#dep-batch", "2")
    page.click("#dep-preview")
    expect(dialog.locator("#dep-plan")).to_contain_text("3 device(s) in 2 stage(s)")
    expect(dialog.locator("#dep-plan")).to_contain_text("canary: 1")
    SHOTS.mkdir(exist_ok=True)
    page.locator(".modal-content").screenshot(path=str(SHOTS / "deploy-dialog.png"))
    page.click("#dep-start")

    row = page.locator("#fw-deployments tr", has_text="s3 v2.2.0")
    expect(row).to_contain_text("running")
    expect(row).to_contain_text("0/3 updated")
    row.locator("[data-dact=details]").click()
    expect(page.locator(".modal")).to_contain_text("canary")
    states = page.locator(".modal tbody tr td:nth-child(2)").all_inner_texts()
    assert [s.split()[0] for s in states] == ["queued", "waiting", "waiting"]   # only the canary is offered
    page.click("#dep-details-close")

    # the canary reports success; the scheduler moves on and the page refreshes itself
    api.device("/api/device/ota/status", {"mac_address": _mac(1), "state": "success", "version": "2.2.0"})
    expect(page.locator("#fw-deployments tr", has_text="s3 v2.2.0")).to_contain_text("1/3 updated", timeout=20000)

    page.locator("#fw-deployments [data-dact=pause]").click()
    row = page.locator("#fw-deployments tr", has_text="s3 v2.2.0")
    expect(row).to_contain_text("paused")
    expect(row).to_contain_text("paused by an administrator")
    page.wait_for_timeout(700)
    page.screenshot(path=str(SHOTS / "deployments-list.png"))
    row.locator("[data-dact=resume]").click()
    expect(page.locator("#fw-deployments tr", has_text="s3 v2.2.0")).to_contain_text("running")
    detail = api(f"/api/admin/deployments/{api('/api/admin/deployments')[0]['id']}")
    assert [t["state"] for t in detail["targets"]] == ["success", "queued", "queued"]
