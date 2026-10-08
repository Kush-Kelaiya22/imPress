"""#35/#36: the Firmware page and pushing an approved image from Modules."""

import os
import sys

from playwright.sync_api import expect

from conftest import ROOT, SHOTS, login

sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend" / "tests")]
os.environ.setdefault("IMPRESS_DEBUG", "true")       # importing the parser loads app settings
from firmware_images import make_image  # noqa: E402


def _open(server, page):
    base, api = server
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/firmware")
    expect(page.locator("#fw-upload")).to_be_visible()
    return base, api


def test_invalid_upload_is_explained(server, page, tmp_path):
    _open(server, page)
    junk = tmp_path / "junk.bin"
    junk.write_bytes(os.urandom(4096))
    page.set_input_files("#fw-file", str(junk))
    expect(page.locator("#fw-result")).to_contain_text("not an ESP-IDF firmware image")


def test_upload_approve_and_push_from_modules(server, page, tmp_path):
    base, api = _open(server, page)
    image = tmp_path / "impress_class_s3.bin"
    image.write_bytes(make_image("impress_class_s3", "2.2.0"))
    page.set_input_files("#fw-file", str(image))
    row = page.locator("tr", has_text="v2.2.0")
    expect(row).to_contain_text("uploaded")
    row.locator("[data-act=approve]").click()
    row = page.locator("tr", has_text="v2.2.0")
    expect(row).to_contain_text("approved")
    expect(row).to_contain_text("latest")
    # every action stays inside the table (the first version clipped them)
    assert page.evaluate("[...document.querySelectorAll('.table-wrap')].every(w => w.scrollWidth <= w.clientWidth + 1)")
    SHOTS.mkdir(exist_ok=True)
    page.wait_for_timeout(700)                         # let the page's fade-in finish
    page.screenshot(path=str(SHOTS / "firmware-page.png"), full_page=False)

    row.locator("[data-act=history]").click()
    expect(page.locator(".modal")).to_contain_text("firmware.approve")
    page.click("#fw-history-close")

    # a hub registers; push the approved image from the Modules page
    import json
    import urllib.request
    req = urllib.request.Request(base + "/api/device/register", method="POST",
                                 data=json.dumps({"mac_address": "a1b2c3d4e5f6", "device_type": "s3",
                                                  "device_name": "Room 201 hub"}).encode(),
                                 headers={"content-type": "application/json", "x-api-key": "ui-device-key"})
    urllib.request.urlopen(req)
    page.goto(base + "/#/admin/modules")
    page.locator("tr", has_text="Room 201 hub").locator("button", has_text="Push OTA").click()
    dialog = page.locator(".modal")
    expect(dialog.locator("#ota-version option")).to_have_count(1)
    expect(dialog).to_contain_text("v2.2.0 (latest)")
    page.locator(".modal-content").screenshot(path=str(SHOTS / "firmware-push-dialog.png"))
    page.click("#ota-go")
    expect(page.locator("tr", has_text="Room 201 hub")).to_contain_text("→ v2.2.0")
    dev = next(d for d in api("/api/admin/modules") if d["mac_address"] == "a1b2c3d4e5f6")
    assert dev["pending_version"] == "2.2.0"


def test_push_dialog_without_approved_images_points_to_the_firmware_page(server, page):
    base, api = server
    import json
    import urllib.request
    urllib.request.urlopen(urllib.request.Request(
        base + "/api/device/register", method="POST",
        data=json.dumps({"mac_address": "a1b2c3d4e5f6", "device_type": "s3", "device_name": "hub"}).encode(),
        headers={"content-type": "application/json", "x-api-key": "ui-device-key"}))
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/modules")
    page.locator("button", has_text="Push OTA").click()
    expect(page.locator(".modal")).to_contain_text("No approved s3 firmware yet")
    expect(page.locator("#ota-go")).to_have_count(0)
