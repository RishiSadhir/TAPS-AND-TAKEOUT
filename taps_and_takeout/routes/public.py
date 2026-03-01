from datetime import date, timedelta

from flask import Blueprint, current_app, jsonify, render_template


public_bp = Blueprint("public", __name__)


def _store():
    return current_app.extensions["content_store"]


@public_bp.get("/")
def index():
    return render_template("index.html")


@public_bp.get("/menu")
def menu():
    return render_template("menu.html", menu=_store().get_menu())


@public_bp.get("/events")
def events():
    events_list = _store().get_events()
    yesterday = date.today() - timedelta(days=1)
    pinned = [event for event in events_list if event.get("pinned")]
    upcoming = sorted(
        [event for event in events_list if not event.get("pinned") and event["date"] >= yesterday],
        key=lambda event: event["date"],
    )
    return render_template("events.html", pinned=pinned, events=upcoming)


@public_bp.get("/contact")
def contact():
    return render_template("contact.html")


@public_bp.get("/healthz")
def healthz():
    store = _store()
    return jsonify(
        {
            "status": "ok",
            "events_count": len(store.get_events()),
            "menu_sections": len(store.get_menu()),
        }
    )
