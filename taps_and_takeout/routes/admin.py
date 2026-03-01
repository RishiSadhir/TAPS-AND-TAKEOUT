from datetime import date, timedelta
import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from ..logging_utils import log_admin_action, log_validation_failure
from ..validation import validate_event_form, validate_item_form, validate_section_form


admin_bp = Blueprint("admin", __name__)


def _store():
    return current_app.extensions["content_store"]


def _require_admin():
    if not session.get("admin"):
        return redirect(url_for("admin.admin_login"))
    return None


def _render_admin_events(events, form_data=None, form_errors=None, row_form_data=None, row_errors=None, status=200):
    return (
        render_template(
            "admin_events.html",
            events=events,
            form_data=form_data or {},
            form_errors=form_errors or {},
            row_form_data=row_form_data or {},
            row_errors=row_errors or {},
        ),
        status,
    )


def _render_admin_menu(menu, section_form_data=None, section_form_errors=None, item_form_data=None, item_form_errors=None, status=200):
    return (
        render_template(
            "admin_menu.html",
            menu=menu,
            section_form_data=section_form_data or {},
            section_form_errors=section_form_errors or {},
            item_form_data=item_form_data or {},
            item_form_errors=item_form_errors or {},
        ),
        status,
    )


def _parse_index(value, label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {label}")


@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if username == "admin" and password == admin_password:
            session.permanent = True
            session["admin"] = True
            log_admin_action("login_success", remote_addr=request.remote_addr)
            return redirect(url_for("admin.admin_events"))
        log_admin_action("login_failure", remote_addr=request.remote_addr)
        return render_template("admin_login.html", error="Invalid credentials."), 403
    return render_template("admin_login.html")


@admin_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.admin_login"))


@admin_bp.route("/admin-events", methods=["GET", "POST"])
def admin_events():
    auth_redirect = _require_admin()
    if auth_redirect:
        return auth_redirect

    store = _store()
    events = store.get_events()

    if request.method == "POST":
        action = request.form.get("action")
        index = request.form.get("index")
        cleaned_form, errors = validate_event_form(
            request.form.get("title", ""),
            request.form.get("date", ""),
            request.form.get("description", ""),
            bool(request.form.get("pinned")),
        )

        if action == "add":
            if errors:
                log_validation_failure("event_add", errors=errors)
                return _render_admin_events(events, form_data=cleaned_form, form_errors=errors, status=400)
            new_event = {
                "title": cleaned_form["title"],
                "date": cleaned_form["date"] or date.today().isoformat(),
                "description": cleaned_form["description"],
                "pinned": cleaned_form["pinned"],
            }
            events.append(new_event)
            store.save_events(events)
            log_admin_action("event_added", title=new_event["title"], pinned=new_event["pinned"])
            flash(f"Added event “{new_event['title']}”.", "success")
            return redirect(url_for("admin.admin_events"))

        if action in ("update", "delete") and index is not None:
            try:
                idx = _parse_index(index, "index")
            except ValueError as exc:
                log_validation_failure("event_row_index", error=str(exc))
                return _render_admin_events(events, status=400, row_errors={"global": str(exc)})
            if idx < 0 or idx >= len(events):
                log_validation_failure("event_row_index", error="Invalid index", index=index)
                return _render_admin_events(events, status=400, row_errors={"global": "Invalid index"})

            if action == "update":
                if errors:
                    log_validation_failure("event_update", errors=errors, index=idx)
                    return _render_admin_events(events, row_form_data={idx: cleaned_form}, row_errors={idx: errors}, status=400)
                old_title = events[idx]["title"]
                events[idx] = {
                    "title": cleaned_form["title"],
                    "date": cleaned_form["date"] or date.today().isoformat(),
                    "description": cleaned_form["description"],
                    "pinned": cleaned_form["pinned"],
                }
                store.save_events(events)
                log_admin_action("event_updated", old_title=old_title, title=cleaned_form["title"], pinned=cleaned_form["pinned"])
                flash(f"Updated event “{cleaned_form['title']}”.", "success")
                return redirect(url_for("admin.admin_events"))

            deleted_title = events[idx]["title"]
            events.pop(idx)
            store.save_events(events)
            log_admin_action("event_deleted", title=deleted_title)
            flash(f"Deleted event “{deleted_title}”.", "success")
            return redirect(url_for("admin.admin_events"))

        if action == "clear_past":
            yesterday = date.today() - timedelta(days=1)
            before = len(events)
            events = [event for event in events if event.get("pinned") or event["date"] >= yesterday]
            store.save_events(events)
            removed = before - len(events)
            log_admin_action("event_clear_past", removed=removed)
            flash(f"Removed {removed} past event(s).", "success")
            return redirect(url_for("admin.admin_events"))

    return _render_admin_events(events)


@admin_bp.route("/admin-menu", methods=["GET", "POST"])
def admin_menu():
    auth_redirect = _require_admin()
    if auth_redirect:
        return auth_redirect

    store = _store()
    menu = store.get_menu()

    if request.method == "POST":
        action = request.form.get("action")
        section_index = request.form.get("section_index")
        section_form, section_errors = validate_section_form(request.form.get("section_name", ""))
        item_form, item_errors = validate_item_form(request.form.get("item_name", ""), request.form.get("item_description", ""))

        if action == "add_section":
            if section_errors:
                log_validation_failure("menu_add_section", errors=section_errors)
                return _render_admin_menu(menu, section_form_data=section_form, section_form_errors=section_errors, status=400)
            menu.append({"section": section_form["section_name"], "items": []})
            store.save_menu(menu)
            log_admin_action("menu_section_added", section=section_form["section_name"])
            flash(f"Added section “{section_form['section_name']}”.", "success")
            return redirect(url_for("admin.admin_menu"))

        if action == "delete_section" and section_index is not None:
            try:
                si = _parse_index(section_index, "section index")
            except ValueError as exc:
                log_validation_failure("menu_section_index", error=str(exc))
                return _render_admin_menu(menu, status=400, section_form_errors={"global": str(exc)})
            if si < 0 or si >= len(menu):
                log_validation_failure("menu_section_index", error="Invalid section index", index=section_index)
                return _render_admin_menu(menu, status=400, section_form_errors={"global": "Invalid section index"})
            deleted_section = menu[si]["section"]
            menu.pop(si)
            store.save_menu(menu)
            log_admin_action("menu_section_deleted", section=deleted_section)
            flash(f"Deleted section “{deleted_section}”.", "success")
            return redirect(url_for("admin.admin_menu"))

        if action == "add_item" and section_index is not None:
            try:
                si = _parse_index(section_index, "section index")
            except ValueError as exc:
                log_validation_failure("menu_item_section_index", error=str(exc))
                return _render_admin_menu(menu, status=400, item_form_errors={"global": str(exc)})
            if si < 0 or si >= len(menu):
                log_validation_failure("menu_item_section_index", error="Invalid section index", index=section_index)
                return _render_admin_menu(menu, status=400, item_form_errors={"global": "Invalid section index"})
            if item_errors:
                log_validation_failure("menu_item_add", errors=item_errors, section=si)
                return _render_admin_menu(menu, item_form_data={si: item_form}, item_form_errors={si: item_errors}, status=400)
            menu[si]["items"].append({"name": item_form["item_name"], "description": item_form["item_description"]})
            store.save_menu(menu)
            log_admin_action("menu_item_added", section=menu[si]["section"], item=item_form["item_name"])
            flash(f"Added item “{item_form['item_name']}” to {menu[si]['section']}.", "success")
            return redirect(url_for("admin.admin_menu"))

        if action in ("update_item", "delete_item") and section_index is not None:
            try:
                si = _parse_index(section_index, "section index")
            except ValueError as exc:
                log_validation_failure("menu_item_section_index", error=str(exc))
                return _render_admin_menu(menu, status=400, item_form_errors={"global": str(exc)})
            if si < 0 or si >= len(menu):
                log_validation_failure("menu_item_section_index", error="Invalid section index", index=section_index)
                return _render_admin_menu(menu, status=400, item_form_errors={"global": "Invalid section index"})

            item_index = request.form.get("item_index")
            try:
                ii = _parse_index(item_index, "item index")
            except ValueError as exc:
                log_validation_failure("menu_item_index", error=str(exc))
                return _render_admin_menu(menu, status=400, item_form_errors={"global": str(exc)})
            if ii < 0 or ii >= len(menu[si]["items"]):
                log_validation_failure("menu_item_index", error="Invalid item index", index=item_index)
                return _render_admin_menu(menu, status=400, item_form_errors={"global": "Invalid item index"})

            if action == "update_item":
                if item_errors:
                    key = f"{si}:{ii}"
                    log_validation_failure("menu_item_update", errors=item_errors, section=si, item=ii)
                    return _render_admin_menu(menu, item_form_data={key: item_form}, item_form_errors={key: item_errors}, status=400)
                old_name = menu[si]["items"][ii]["name"]
                menu[si]["items"][ii] = {"name": item_form["item_name"], "description": item_form["item_description"]}
                store.save_menu(menu)
                log_admin_action("menu_item_updated", section=menu[si]["section"], old_name=old_name, item=item_form["item_name"])
                flash(f"Updated item “{item_form['item_name']}”.", "success")
                return redirect(url_for("admin.admin_menu"))

            deleted_name = menu[si]["items"][ii]["name"]
            menu[si]["items"].pop(ii)
            store.save_menu(menu)
            log_admin_action("menu_item_deleted", section=menu[si]["section"], item=deleted_name)
            flash(f"Deleted item “{deleted_name}”.", "success")
            return redirect(url_for("admin.admin_menu"))

    return _render_admin_menu(menu)
