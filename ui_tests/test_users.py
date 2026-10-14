"""Account lifecycle in the admin UI (#117, #119): buttons follow the server's allowed_actions."""

from playwright.sync_api import expect

from conftest import login


def _teacher(api, name="teach1"):
    return api("/api/admin/users", {"username": name, "email": f"{name}@example.edu", "password": "Passw0rd!x",
                                    "full_name": name.title(), "role": "teacher"})["id"]


def test_own_row_offers_no_lockout_actions(server, page):
    base, api = server
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    me = page.locator("tr", has_text="admin@impress.local")
    expect(me.locator("text=You")).to_be_visible()
    for label in ("Deactivate", "Delete permanently"):
        expect(me.locator("button", has_text=label)).to_have_count(0)


def test_delete_needs_the_username(server, page):
    base, api = server
    _teacher(api)
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    row = page.locator("tr", has_text="teach1")
    page.once("dialog", lambda d: d.accept("wrong-name"))
    row.locator("button", has_text="Delete permanently").click()
    expect(page.locator("text=Username did not match")).to_be_visible()
    expect(page.locator("tr", has_text="teach1")).to_be_visible()
    page.once("dialog", lambda d: d.accept("teach1"))
    page.locator("tr", has_text="teach1").locator("button", has_text="Delete permanently").click()
    expect(page.locator("tr", has_text="teach1")).to_have_count(0)


def test_a_background_refresh_never_undoes_a_click(server, page):
    """v2.2 live refresh: a refresh that fetched before the click must not draw over its result."""
    base, api = server
    _teacher(api)
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    row = page.locator("tr", has_text="teach1")
    expect(row.locator("button", has_text="Deactivate")).to_be_visible()

    # background requests answer late: the stale answer arrives after the click's
    page.evaluate("""() => {
      const real = window.fetch;
      window.fetch = async (url, opts = {}) => {
        const res = await real(url, opts);
        if (opts.headers && opts.headers['X-Impress-Background'] && String(url).includes('/admin/users')) await new Promise(r => setTimeout(r, 1500));
        return res;
      };
      void quietRefresh();          // in flight: fetches the users as they are now
    }""")
    page.once("dialog", lambda d: d.accept())
    row.locator("button", has_text="Deactivate").click()
    expect(page.locator("tr", has_text="teach1").locator("button", has_text="Reactivate")).to_be_visible()
    page.wait_for_timeout(2000)                         # the stale background answer has arrived by now
    assert page.locator("tr", has_text="teach1").locator("button", has_text="Reactivate").is_visible()   # no retry
