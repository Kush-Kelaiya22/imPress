"""Account lifecycle in the admin UI (#117, #119): buttons follow the server's allowed_actions."""

from playwright.sync_api import expect

from conftest import login


def _teacher(api, name="teach1"):
    return api("/api/admin/users", {"username": name, "email": f"{name}@example.edu", "password": "Passw0rd!x",
                                    "full_name": name.title(), "role": "teacher"})["id"]


def _confirm(page):
    page.click(".modal:not(.hidden) button[type=submit]")


def test_own_row_offers_no_lockout_actions(server, page):
    base, api = server
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    me = page.locator("tr", has_text="default.superadmin@impress.local")
    expect(me.locator("text=You")).to_be_visible()
    expect(me.locator('button[title="Disable"]')).to_have_count(0)
    me.locator('[data-action="toggle-menu"]').click()
    expect(me.locator(".menu")).not_to_contain_text("Delete account")


def test_a_new_account_is_added_with_a_generated_password_shown_once(server, page):
    base, api = server
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    page.click("text=Add account")
    page.fill("#new-fullname", "Nina Thomas")
    page.fill("#new-username", "nina")
    page.fill("#new-email", "nina@example.edu")
    page.click('#create-user-modal button[type="submit"]')
    expect(page.locator("#cred-pw")).to_be_visible()
    temp = page.inner_text("#cred-pw")
    assert len(temp) >= 12
    page.click("#cred-done")
    row = page.locator("tr", has_text="nina@example.edu")
    expect(row).to_contain_text("Pending setup")
    assert api("/api/auth/me") is not None


def test_a_typed_password_is_checked_as_you_type(server, page):
    base, api = server
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    page.click("text=Add account")
    page.click('[data-pwmode="manual"]')
    page.fill("#new-password", "weak")
    expect(page.locator("#new-password-label")).to_have_text("Too weak")
    page.fill("#new-password", "Tr0ub4dor&3-horse-staple")
    expect(page.locator("#new-password-label")).to_have_text("Strong")


def test_delete_moves_the_account_to_the_trash_and_it_can_be_restored(server, page):
    base, api = server
    _teacher(api)
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    row = page.locator("tr", has_text="teach1")
    row.locator('[data-action="toggle-menu"]').click()
    row.locator("button", has_text="Delete account").click()
    _confirm(page)
    expect(page.locator("tr", has_text="teach1")).to_have_count(0)
    page.click('[data-sub="deleted"]')
    expect(page.locator(".trash-note")).to_contain_text("30 days")
    expect(page.locator("tr", has_text="teach1")).to_contain_text("days")
    page.click('[data-action="usr-restore"]')
    page.click('[data-sub="people"]')
    expect(page.locator("tr", has_text="teach1")).to_be_visible()


def test_switching_faculty_and_ta_warns_and_switching_to_admin_asks(server, page):
    base, api = server
    _teacher(api)
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    row = page.locator("tr", has_text="teach1")
    row.locator('[data-action="toggle-menu"]').click()
    row.locator("button", has_text="Make teaching assistant").click()
    expect(page.locator(".confirm-warn")).to_contain_text("same permissions as faculty")
    _confirm(page)
    expect(page.locator("tr", has_text="teach1")).to_contain_text("Teaching assistant")
    row = page.locator("tr", has_text="teach1")
    row.locator('[data-action="toggle-menu"]').click()
    row.locator("button", has_text="Make administrator").click()
    expect(page.locator(".modal:not(.hidden) .modal-content")).to_contain_text("will become an administrator")
    _confirm(page)
    expect(page.locator("tr", has_text="teach1")).to_contain_text("Administrator")


def test_a_background_refresh_never_undoes_a_click(server, page):
    """v2.2 live refresh: a refresh that fetched before the click must not draw over its result."""
    base, api = server
    _teacher(api)
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    row = page.locator("tr", has_text="teach1")
    expect(row.locator('button[title="Disable"]')).to_be_visible()

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
    row.locator('button[title="Disable"]').click()
    _confirm(page)
    expect(page.locator("tr", has_text="teach1").locator('button[title="Enable"]')).to_be_visible()
    page.wait_for_timeout(2000)                         # the stale background answer has arrived by now
    assert page.locator("tr", has_text="teach1").locator('button[title="Enable"]').is_visible()   # no retry
