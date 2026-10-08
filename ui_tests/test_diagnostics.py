"""#39: health states and the read-only diagnostics panel on the Modules page."""

from playwright.sync_api import expect

from conftest import SHOTS, login

CRASHED, WEAK = "48:F6:EE:00:00:01", "48:F6:EE:00:00:02"


def _row(page, dialog, label):
    return dialog.locator("tr").filter(has=page.locator("th", has_text=label))


def _beat(api, mac, **diag):
    api.device("/api/device/heartbeat", {"mac_address": mac, "rssi": -60, "free_heap": 180000, **diag})


def test_health_badges_and_diagnostics_refresh(server, page):
    base, api = server
    for mac, name in ((CRASHED, "Room 101"), (WEAK, "Room 102")):
        api.device("/api/device/register", {"mac_address": mac, "device_type": "c6", "device_name": name})
    _beat(api, CRASHED, uptime_s=30, reset_reason="task_wdt", boot_count=9, min_free_heap=90000,
          s3_link_ok=True, s3_uptime_s=25)
    _beat(api, WEAK, uptime_s=7200, reset_reason="poweron", boot_count=1, min_free_heap=90000, s3_link_ok=False)

    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/modules")
    crashed = page.locator("tr", has_text="Room 101")
    expect(crashed).to_contain_text("error")
    expect(crashed).to_contain_text("reset by task_wdt")
    expect(page.locator("tr", has_text="Room 102")).to_contain_text("degraded")
    expect(page.locator("tr", has_text="Room 102")).to_contain_text("S3 link down")
    expect(page.locator(".stat-card", has_text="Need attention")).to_contain_text("2")

    page.locator("tr", has_text="Room 102").get_by_role("button", name="Diagnostics").click()
    dialog = page.locator(".modal-content")
    expect(dialog).to_contain_text("Diagnostics · Room 102")
    expect(_row(page, dialog, "S3 link")).to_contain_text("down")
    expect(_row(page, dialog, "Uptime")).to_contain_text("2h 0m")
    expect(_row(page, dialog, "Last reset")).to_contain_text("poweron")

    # the S3 comes back: Refresh shows it without reopening
    _beat(api, WEAK, uptime_s=7215, reset_reason="poweron", boot_count=1, min_free_heap=90000,
          s3_link_ok=True, s3_uptime_s=12)
    dialog.get_by_role("button", name="Refresh").click()
    expect(_row(page, dialog, "S3 link")).to_contain_text("up")
    expect(_row(page, dialog, "Health")).to_contain_text("online")
    SHOTS.mkdir(exist_ok=True)
    dialog.screenshot(path=str(SHOTS / "diagnostics.png"))
    dialog.get_by_role("button", name="Close").click()
    expect(page.locator(".modal")).to_have_count(0)
