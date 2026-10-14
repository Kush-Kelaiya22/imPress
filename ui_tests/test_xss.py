"""v2.2: names with quotes are data, never markup or script (stored XSS)."""

from playwright.sync_api import expect

from conftest import login

CLASS = 'Evil" onmouseover="window.__xss=1" data-x="'
STUDENT = "Eve');window.__xss=2;//"
DEVICE = "Hub');window.__xss=3;//\" onfocus=\"window.__xss=4"


def test_hostile_names_do_not_run_script(server, page):
    base, api = server
    api("/api/admin/classes", {"name": CLASS, "code": "EVIL101"})
    api("/api/students/", {"roll_number": "EVIL000001", "student_name": STUDENT})
    api.device("/api/device/register", {"mac_address": "AA:BB:CC:00:00:99", "device_type": "s3",
                                        "device_name": DEVICE, "firmware_version": "2.1.0"})
    login(page, base)
    page.wait_for_url("**/#/admin*")
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    for route in ("#/admin/classes", "#/admin/students", "#/admin/modules"):
        page.goto(base + "/" + route)
        page.wait_for_timeout(800)
        # no attribute was injected, and the names are shown as typed
        assert page.locator("[onmouseover], [onfocus], [data-x]").count() == 0, route
        for el in page.locator("[onclick]:visible").all()[:12]:
            el.hover()
        assert page.evaluate("window.__xss") is None, route

    page.goto(base + "/#/admin/classes")
    expect(page.locator(".class-card h3, .class-card .name", has_text="Evil")).to_be_visible()
    page.locator('button[title="Delete"]').first.click()           # the name reaches the confirm text intact
    page.wait_for_timeout(300)
    assert any("window.__xss=1" in m for m in dialogs)
    assert page.evaluate("window.__xss") is None

    page.goto(base + "/#/admin/students")
    page.locator('button[title="Delete permanently"]').first.click()
    page.wait_for_timeout(300)
    assert page.evaluate("window.__xss") is None
    page.goto(base + "/#/admin/modules")
    page.locator("button", has_text="Push OTA").first.click()
    page.wait_for_timeout(500)
    assert page.evaluate("window.__xss") is None
