"""#40: student modules that joined a gateway appear in the inventory, the
class device view and the live presence panel."""

from playwright.sync_api import expect

from conftest import SHOTS, login

GW = "48:F6:EE:00:00:C6"


def _seed(api):
    cls = api("/api/admin/classes", {"name": "Physics", "code": "PHY101", "classroom_code": "RM-201"})
    for roll, name in (("ABCDE12345", "Asha Rao"), ("FGHIJ67890", "Ben Ito")):
        api("/api/students/", {"roll_number": roll, "student_name": name})
    api.device("/api/device/register", {"mac_address": GW, "device_type": "c6", "device_name": "Room 201",
                                        "classroom_code": "RM-201"})
    join = lambda uid, roll: {"type": "student_join", "device_mac": GW, "device_id": uid,
                              "enrollment_number": roll, "class_code": ""}
    api.device("/api/device/batch", {"device_type": "c6", "messages": [
        join(0x1A2B3C4D, "ABCDE12345"), join(0x0000BEEF, "FGHIJ67890"),
        {"type": "heartbeat", "device_mac": GW, "device_id": 0x1A2B3C4D, "battery_pct": 76, "rssi": -58},
        {"type": "student_leave", "device_mac": GW, "device_id": 0x0000BEEF,
         "enrollment_number": "FGHIJ67890", "reason": 0}]})
    return cls["id"]


def test_inventory_filters_and_class_view(server, page):
    base, api = server
    cid = _seed(api)
    login(page, base)
    page.wait_for_url("**/#/admin*")

    page.goto(base + "/#/admin/modules")
    card = page.locator("#student-modules")
    expect(card).to_contain_text("1/2 connected")
    rows = card.locator("#sm-rows tr")
    expect(rows).to_have_count(2)
    expect(card.locator("tr", has_text="1A2B3C4D")).to_contain_text("connected")
    expect(card.locator("tr", has_text="1A2B3C4D")).to_contain_text("76%")
    expect(card.locator("tr", has_text="0000BEEF")).to_contain_text("seen")
    SHOTS.mkdir(exist_ok=True)
    card.screenshot(path=str(SHOTS / "student-modules.png"))

    page.fill("#sm-q", "beef")
    expect(rows).to_have_count(1)
    expect(rows.first).to_contain_text("FGHIJ67890")
    page.fill("#sm-q", "")
    page.select_option("#sm-state", "connected")
    expect(rows).to_have_count(1)
    expect(rows.first).to_contain_text("ABCDE12345")
    page.select_option("#sm-state", "")
    expect(page.locator("#sm-class option")).to_have_count(2)       # "All classes" + PHY101

    # smoke step 7: the class's device view lists the modules
    page.goto(f"{base}/#/class?id={cid}")
    devices = page.locator(".card", has_text="Class Devices")
    expect(devices).to_contain_text("ABCDE12345")
    expect(devices).to_contain_text("via Room 201")
    expect(page.locator("#live-devices-grid")).to_contain_text("Student modules · 1/2 connected")
