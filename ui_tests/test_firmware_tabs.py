"""Separate firmware views per device family (#131)."""

import os
import sys

from playwright.sync_api import expect

from conftest import ROOT, login

sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend" / "tests")]
os.environ.setdefault("IMPRESS_DEBUG", "true")
from firmware_images import make_image  # noqa: E402


def test_tabs_show_one_family_with_its_rules(server, page):
    base, api = server
    api.upload("/api/admin/firmware", "c6.bin", make_image("impress_class_c6", "2.2.0"))
    api.upload("/api/admin/firmware", "s3.bin", make_image("impress_class_s3", "2.2.0"))
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/firmware")
    c6, s3 = page.locator('.card[data-family="c6"]'), page.locator('.card[data-family="s3"]')
    expect(c6).to_be_visible()
    expect(s3).to_be_visible()                                          # "All devices" by default
    page.locator('#fw-tabs [data-tab="s3"]').click()
    expect(c6).to_be_hidden()
    expect(s3).to_contain_text("Images for one do not run on the other")
    expect(page.locator('#fw-tabs [data-tab="s3"]')).to_have_attribute("aria-selected", "true")
    page.reload()                                                       # the choice is remembered
    expect(page.locator('.card[data-family="c6"]')).to_be_hidden()
    page.locator('#fw-tabs [data-tab="student"]').click()
    expect(page.locator('.card[data-family="student"]')).to_contain_text("No over-the-air path yet")
    page.locator('#fw-tabs [data-tab="all"]').click()
    expect(page.locator('.card[data-family="c6"]')).to_be_visible()
