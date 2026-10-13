"""Schedule changes on the class page (#126)."""

from playwright.sync_api import expect

from conftest import login


def test_record_and_remove_a_cancelled_class(server, page):
    base, api = server
    cid = api("/api/admin/classes", {"name": "Physics A", "code": "PHY101", "classroom_code": "RM-1",
                                     "meeting_schedule": [{"day": "Monday", "start": "09:00", "end": "10:00"}]})["id"]
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(f"{base}/#/class?id={cid}")
    card = page.locator("#class-exceptions")
    expect(card.locator("text=No changes recorded.")).to_be_visible()
    card.locator("#ex-kind").select_option("cancelled")
    card.locator("#ex-date").fill("2026-10-12")
    card.locator("#ex-slot").fill("09:00")
    card.locator("button", has_text="Save change").click()
    row = card.locator("tr", has_text="Cancelled")
    expect(row).to_contain_text("2026-10-12 09:00")
    page.once("dialog", lambda d: d.accept())
    row.locator("button", has_text="Remove").click()
    expect(card.locator("text=No changes recorded.")).to_be_visible()
