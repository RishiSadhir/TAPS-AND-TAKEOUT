import os
import json
import pytest
from datetime import date, timedelta

os.environ.setdefault("ADMIN_PASSWORD", "testpass")

import app as flask_app
import events as events_module
import menu_data as menu_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(events_module, "EVENTS_FILE", str(tmp_path / "events.json"))
    monkeypatch.setattr(menu_module, "MENU_FILE", str(tmp_path / "menu.json"))
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["WTF_CSRF_ENABLED"] = False
    flask_app.app.config["RATELIMIT_ENABLED"] = False
    with flask_app.app.test_client() as c:
        yield c


def login(client):
    return client.post("/admin", data={"username": "admin", "password": "testpass"})


# ---------------------------------------------------------------------------
# events.py unit tests
# ---------------------------------------------------------------------------

def test_load_events_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(events_module, "EVENTS_FILE", str(tmp_path / "missing.json"))
    assert events_module.load_events() == []


def test_save_load_events_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(events_module, "EVENTS_FILE", str(tmp_path / "events.json"))
    original = [{"title": "Test Event", "date": date(2026, 6, 1), "description": "Desc"}]
    events_module.save_events(original)
    loaded = events_module.load_events()
    assert loaded[0]["title"] == "Test Event"
    assert loaded[0]["date"] == date(2026, 6, 1)
    assert loaded[0]["description"] == "Desc"


def test_save_events_serializes_dates_as_strings(tmp_path, monkeypatch):
    path = str(tmp_path / "events.json")
    monkeypatch.setattr(events_module, "EVENTS_FILE", path)
    events_module.save_events([{"title": "T", "date": date(2026, 3, 1), "description": ""}])
    with open(path) as f:
        raw = json.load(f)
    assert raw[0]["date"] == "2026-03-01"


def test_load_events_deserializes_date_strings(tmp_path, monkeypatch):
    path = str(tmp_path / "events.json")
    monkeypatch.setattr(events_module, "EVENTS_FILE", path)
    with open(path, "w") as f:
        json.dump([{"title": "T", "date": "2026-03-01", "description": ""}], f)
    loaded = events_module.load_events()
    assert isinstance(loaded[0]["date"], date)
    assert loaded[0]["date"] == date(2026, 3, 1)


# ---------------------------------------------------------------------------
# menu_data.py unit tests
# ---------------------------------------------------------------------------

def test_load_menu_missing_file_returns_default(tmp_path, monkeypatch):
    monkeypatch.setattr(menu_module, "MENU_FILE", str(tmp_path / "missing.json"))
    menu = menu_module.load_menu()
    assert len(menu) > 0
    assert "section" in menu[0]
    assert "items" in menu[0]


def test_save_load_menu_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(menu_module, "MENU_FILE", str(tmp_path / "menu.json"))
    original = [{"section": "Drinks", "items": [{"name": "Beer", "description": "Cold"}]}]
    menu_module.save_menu(original)
    loaded = menu_module.load_menu()
    assert loaded[0]["section"] == "Drinks"
    assert loaded[0]["items"][0]["name"] == "Beer"


# ---------------------------------------------------------------------------
# Public route tests
# ---------------------------------------------------------------------------

def test_home(client):
    assert client.get("/").status_code == 200


def test_menu_page(client):
    assert client.get("/menu").status_code == 200


def test_events_page(client):
    assert client.get("/events").status_code == 200


def test_contact_page(client):
    assert client.get("/contact").status_code == 200


# ---------------------------------------------------------------------------
# Event filtering tests
# ---------------------------------------------------------------------------

def test_events_filters_out_past(client):
    events_module.save_events([
        {"title": "Past", "date": date.today() - timedelta(days=5), "description": ""},
        {"title": "Future", "date": date.today() + timedelta(days=5), "description": ""},
    ])
    html = client.get("/events").data.decode()
    assert "Future" in html
    assert "Past" not in html


def test_events_shows_yesterday(client):
    events_module.save_events([
        {"title": "Yesterday", "date": date.today() - timedelta(days=1), "description": ""},
    ])
    assert "Yesterday" in client.get("/events").data.decode()


def test_events_shows_today(client):
    events_module.save_events([
        {"title": "Today", "date": date.today(), "description": ""},
    ])
    assert "Today" in client.get("/events").data.decode()


def test_events_sorted_ascending(client):
    events_module.save_events([
        {"title": "Later", "date": date.today() + timedelta(days=10), "description": ""},
        {"title": "Sooner", "date": date.today() + timedelta(days=2), "description": ""},
    ])
    html = client.get("/events").data.decode()
    assert html.index("Sooner") < html.index("Later")


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------

def test_login_wrong_password(client):
    r = client.post("/admin", data={"username": "admin", "password": "wrong"})
    assert r.status_code == 403


def test_login_wrong_username(client):
    r = client.post("/admin", data={"username": "notadmin", "password": "testpass"})
    assert r.status_code == 403


def test_login_correct_credentials(client):
    r = client.post("/admin", data={"username": "admin", "password": "testpass"})
    assert r.status_code == 302
    assert "/admin-events" in r.headers["Location"]


def test_admin_events_requires_login(client):
    r = client.get("/admin-events")
    assert r.status_code == 302
    assert "/admin" in r.headers["Location"]


def test_admin_menu_requires_login(client):
    r = client.get("/admin-menu")
    assert r.status_code == 302
    assert "/admin" in r.headers["Location"]


def test_logout_clears_session(client):
    login(client)
    client.get("/logout")
    assert client.get("/admin-events").status_code == 302


# ---------------------------------------------------------------------------
# Admin events CRUD tests
# ---------------------------------------------------------------------------

def test_add_event(client):
    login(client)
    r = client.post("/admin-events", data={
        "action": "add", "title": "New Event",
        "date": "2026-06-01", "description": "Fun",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert "New Event" in r.data.decode()


def test_add_event_empty_title(client):
    login(client)
    r = client.post("/admin-events", data={
        "action": "add", "title": "  ", "date": "2026-06-01", "description": "",
    })
    assert r.status_code == 400


def test_add_event_invalid_date(client):
    login(client)
    r = client.post("/admin-events", data={
        "action": "add", "title": "X", "date": "not-a-date", "description": "",
    })
    assert r.status_code == 400


def test_update_event(client):
    events_module.save_events([{"title": "Old", "date": date(2026, 6, 1), "description": ""}])
    login(client)
    r = client.post("/admin-events", data={
        "action": "update", "index": "0",
        "title": "Updated", "date": "2026-06-01", "description": "",
    }, follow_redirects=True)
    html = r.data.decode()
    assert "Updated" in html
    assert "Old" not in html


def test_update_event_out_of_bounds(client):
    login(client)
    r = client.post("/admin-events", data={
        "action": "update", "index": "999",
        "title": "X", "date": "2026-06-01", "description": "",
    })
    assert r.status_code == 400


def test_delete_event(client):
    events_module.save_events([{"title": "Gone", "date": date(2026, 6, 1), "description": ""}])
    login(client)
    r = client.post("/admin-events", data={
        "action": "delete", "index": "0",
        "title": "Gone", "date": "2026-06-01", "description": "",
    }, follow_redirects=True)
    assert "Gone" not in r.data.decode()


def test_delete_event_out_of_bounds(client):
    login(client)
    r = client.post("/admin-events", data={
        "action": "delete", "index": "999",
        "title": "X", "date": "2026-06-01", "description": "",
    })
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Pinned event tests
# ---------------------------------------------------------------------------

def test_pinned_event_always_shows(client):
    events_module.save_events([
        {"title": "Pinned", "date": date(2000, 1, 1), "description": "", "pinned": True},
    ])
    html = client.get("/events").data.decode()
    assert "Pinned" in html
    assert "Recurring" in html


def test_pinned_event_not_shown_as_dated(client):
    events_module.save_events([
        {"title": "Pinned", "date": date(2000, 1, 1), "description": "", "pinned": True},
    ])
    html = client.get("/events").data.decode()
    assert "2000" not in html


def test_pinned_event_shown_before_upcoming(client):
    events_module.save_events([
        {"title": "Upcoming", "date": date.today() + timedelta(days=1), "description": "", "pinned": False},
        {"title": "Pinned", "date": date(2000, 1, 1), "description": "", "pinned": True},
    ])
    html = client.get("/events").data.decode()
    assert html.index("Pinned") < html.index("Upcoming")


def test_add_pinned_event_no_date(client):
    login(client)
    r = client.post("/admin-events", data={
        "action": "add", "title": "Jazz Night", "date": "", "description": "Every Saturday", "pinned": "1",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert "Jazz Night" in r.data.decode()


def test_unpinned_event_still_requires_date(client):
    login(client)
    r = client.post("/admin-events", data={
        "action": "add", "title": "One-off", "date": "", "description": "",
    })
    assert r.status_code == 400


def test_clear_past_events(client):
    events_module.save_events([
        {"title": "Old Gig", "date": date.today() - timedelta(days=5), "description": "", "pinned": False},
        {"title": "Upcoming Gig", "date": date.today() + timedelta(days=5), "description": "", "pinned": False},
        {"title": "Weekly Jazz", "date": date(2000, 1, 1), "description": "", "pinned": True},
    ])
    login(client)
    r = client.post("/admin-events", data={"action": "clear_past"}, follow_redirects=True)
    html = r.data.decode()
    assert "Old Gig" not in html
    assert "Upcoming Gig" in html
    assert "Weekly Jazz" in html


# ---------------------------------------------------------------------------
# Admin menu CRUD tests
# ---------------------------------------------------------------------------

def test_add_section(client):
    login(client)
    r = client.post("/admin-menu", data={
        "action": "add_section", "section_name": "Happy Hour",
    }, follow_redirects=True)
    assert "Happy Hour" in r.data.decode()


def test_delete_section(client):
    menu_module.save_menu([{"section": "Temporary", "items": []}])
    login(client)
    r = client.post("/admin-menu", data={
        "action": "delete_section", "section_index": "0",
    }, follow_redirects=True)
    assert "Temporary" not in r.data.decode()


def test_delete_section_out_of_bounds(client):
    login(client)
    r = client.post("/admin-menu", data={
        "action": "delete_section", "section_index": "999",
    })
    assert r.status_code == 400


def test_add_item(client):
    menu_module.save_menu([{"section": "Drinks", "items": []}])
    login(client)
    r = client.post("/admin-menu", data={
        "action": "add_item", "section_index": "0",
        "item_name": "Lager", "item_description": "$5",
    }, follow_redirects=True)
    assert "Lager" in r.data.decode()


def test_add_item_empty_name(client):
    menu_module.save_menu([{"section": "Drinks", "items": []}])
    login(client)
    r = client.post("/admin-menu", data={
        "action": "add_item", "section_index": "0",
        "item_name": "  ", "item_description": "",
    })
    assert r.status_code == 400


def test_update_item(client):
    menu_module.save_menu([{"section": "S", "items": [{"name": "Old", "description": ""}]}])
    login(client)
    r = client.post("/admin-menu", data={
        "action": "update_item", "section_index": "0", "item_index": "0",
        "item_name": "New", "item_description": "Better",
    }, follow_redirects=True)
    html = r.data.decode()
    assert "New" in html
    assert "Old" not in html


def test_update_item_out_of_bounds(client):
    menu_module.save_menu([{"section": "S", "items": []}])
    login(client)
    r = client.post("/admin-menu", data={
        "action": "update_item", "section_index": "0", "item_index": "999",
        "item_name": "X", "item_description": "",
    })
    assert r.status_code == 400


def test_delete_item(client):
    menu_module.save_menu([{"section": "S", "items": [{"name": "Gone", "description": ""}]}])
    login(client)
    r = client.post("/admin-menu", data={
        "action": "delete_item", "section_index": "0", "item_index": "0",
    }, follow_redirects=True)
    assert "Gone" not in r.data.decode()


def test_delete_item_out_of_bounds(client):
    menu_module.save_menu([{"section": "S", "items": []}])
    login(client)
    r = client.post("/admin-menu", data={
        "action": "delete_item", "section_index": "0", "item_index": "999",
    })
    assert r.status_code == 400
