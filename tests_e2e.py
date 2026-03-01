import os
import threading

import pytest
from werkzeug.serving import make_server

os.environ.setdefault("ADMIN_PASSWORD", "testpass")
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")

playwright = pytest.importorskip("playwright.sync_api")
expect = playwright.expect
sync_playwright = playwright.sync_playwright

import app as flask_app
import events as events_module
import menu_data as menu_module


@pytest.fixture
def live_server(tmp_path, monkeypatch):
    monkeypatch.setattr(events_module, "EVENTS_FILE", str(tmp_path / "events.json"))
    monkeypatch.setattr(menu_module, "MENU_FILE", str(tmp_path / "menu.json"))
    flask_app.app.config["TESTING"] = True

    server = make_server("127.0.0.1", 0, flask_app.app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("dialog", lambda dialog: dialog.accept())
        try:
            yield page
        finally:
            browser.close()


def test_admin_event_crud_smoke(live_server, page):
    page.goto(f"{live_server}/admin")
    page.get_by_placeholder("Username").fill("admin")
    page.get_by_placeholder("Password").fill("testpass")
    page.get_by_role("button", name="Log In").click()

    expect(page).to_have_url(f"{live_server}/admin-events")
    expect(page.locator("h1.page-title")).to_have_text("Events")

    add_form = page.locator("form.admin-form").first
    add_form.get_by_placeholder("Event Title").fill("Browser Event")
    add_form.locator('input[name="date"]').fill("2026-03-20")
    add_form.get_by_placeholder("Description").fill("Created in a real browser")
    add_form.get_by_role("button", name="Add Event").click()

    expect(page.locator(".flash-message")).to_contain_text("Added event")
    event_form = page.locator("form.admin-row-form").filter(has=page.locator('input[name="title"][value="Browser Event"]')).first
    expect(event_form.locator('input[name="title"]')).to_have_value("Browser Event")

    event_form.locator('input[name="title"]').fill("Updated In Browser")
    event_form.locator('input[name="date"]').fill("2026-03-21")
    event_form.locator('textarea[name="description"]').fill("Updated in a real browser")
    event_form.get_by_role("button", name="Update").click()

    expect(page.locator(".flash-message")).to_contain_text("Updated event")
    event_form = page.locator("form.admin-row-form").filter(has=page.locator('input[name="title"][value="Updated In Browser"]')).first
    expect(event_form.locator('input[name="title"]')).to_have_value("Updated In Browser")

    event_form.get_by_role("button", name="Delete").click()
    expect(page.locator(".flash-message")).to_contain_text("Deleted event")
    expect(page.locator("form.admin-row-form")).to_have_count(0)
