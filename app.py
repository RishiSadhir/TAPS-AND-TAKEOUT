import os
import logging
from datetime import datetime, date, timedelta
from events import load_events, save_events
from menu_data import load_menu, save_menu

from flask import Flask, render_template, request, redirect, url_for, session, current_app, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def parse_int_field(value, label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {label}")


def render_admin_events(events, form_data=None, form_errors=None, row_form_data=None, row_errors=None, status=200):
    return render_template(
        "admin_events.html",
        events=events,
        form_data=form_data or {},
        form_errors=form_errors or {},
        row_form_data=row_form_data or {},
        row_errors=row_errors or {},
    ), status


def render_admin_menu(menu, section_form_data=None, section_form_errors=None, item_form_data=None, item_form_errors=None, status=200):
    return render_template(
        "admin_menu.html",
        menu=menu,
        section_form_data=section_form_data or {},
        section_form_errors=section_form_errors or {},
        item_form_data=item_form_data or {},
        item_form_errors=item_form_errors or {},
    ), status


app = Flask(__name__)
app.secret_key = require_env("FLASK_SECRET_KEY")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
csrf = CSRFProtect(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/menu')
def menu():
    menu_sections = load_menu()
    return render_template('menu.html', menu=menu_sections)


@app.route('/events')
def events():
    events_list = load_events()
    yesterday = date.today() - timedelta(days=1)
    pinned = [e for e in events_list if e.get('pinned')]
    upcoming = sorted([e for e in events_list if not e.get('pinned') and e['date'] >= yesterday], key=lambda e: e['date'])
    return render_template('events.html', pinned=pinned, events=upcoming)


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/admin', methods=['GET', 'POST'])
@limiter.limit("10 per minute", exempt_when=lambda: current_app.config.get("TESTING", False))
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == require_env("ADMIN_PASSWORD"):
            session.permanent = True
            session['admin'] = True
            log.info("Admin login from %s", request.remote_addr)
            return redirect(url_for('admin_events'))
        log.warning("Failed admin login attempt from %s", request.remote_addr)
        return render_template('admin_login.html', error="Invalid credentials."), 403
    return render_template('admin_login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_login'))


@app.route("/admin-events", methods=["GET", "POST"])
def admin_events():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    events = load_events()

    if request.method == "POST":
        action = request.form.get("action")
        index = request.form.get("index")
        title = request.form.get("title", "").strip()
        date_str = request.form.get("date", "")
        description = request.form.get("description", "").strip()
        pinned = bool(request.form.get("pinned"))
        base_form = {
            "title": title,
            "date": date_str,
            "description": description,
            "pinned": pinned,
        }

        if action in ("add", "update"):
            if not pinned:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    error = {"date": "Enter a valid date."}
                    if action == "add":
                        return render_admin_events(events, form_data=base_form, form_errors=error, status=400)
                    try:
                        idx = parse_int_field(index, "index")
                    except ValueError as exc:
                        return render_admin_events(events, status=400, row_errors={"global": str(exc)})
                    return render_admin_events(events, row_form_data={idx: base_form}, row_errors={idx: error}, status=400)

        if action == "add":
            if not title:
                return render_admin_events(events, form_data=base_form, form_errors={"title": "Title is required."}, status=400)
            new_event = {
                "title": title,
                "date": date_str or date.today().isoformat(),
                "description": description,
                "pinned": pinned,
            }
            events.append(new_event)
            log.info("Admin: added event '%s' on %s", new_event["title"], new_event["date"])
            flash(f"Added event “{new_event['title']}”.", "success")

        elif action in ("update", "delete") and index is not None:
            try:
                idx = parse_int_field(index, "index")
            except ValueError as exc:
                return render_admin_events(events, status=400, row_errors={"global": str(exc)})
            if idx < 0 or idx >= len(events):
                return render_admin_events(events, status=400, row_errors={"global": "Invalid index"})

            if action == "update":
                if not title:
                    return render_admin_events(events, row_form_data={idx: base_form}, row_errors={idx: {"title": "Title is required."}}, status=400)
                old_title = events[idx]["title"]
                events[idx] = {
                    "title": title,
                    "date": date_str or date.today().isoformat(),
                    "description": description,
                    "pinned": pinned,
                }
                log.info("Admin: updated event '%s' → '%s'", old_title, title)
                flash(f"Updated event “{title}”.", "success")

            elif action == "delete":
                log.info("Admin: deleted event '%s'", events[idx]["title"])
                flash(f"Deleted event “{events[idx]['title']}”.", "success")
                events.pop(idx)

        elif action == "clear_past":
            yesterday = date.today() - timedelta(days=1)
            before = len(events)
            events = [e for e in events if e.get('pinned') or e['date'] >= yesterday]
            log.info("Admin: cleared %d past event(s)", before - len(events))
            flash(f"Removed {before - len(events)} past event(s).", "success")

        save_events(events)
        return redirect(url_for("admin_events"))

    return render_admin_events(events)


@app.route("/admin-menu", methods=["GET", "POST"])
def admin_menu():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    menu = load_menu()

    if request.method == "POST":
        action = request.form.get("action")
        section_index = request.form.get("section_index")
        section_name = request.form.get("section_name", "").strip()
        item_name = request.form.get("item_name", "").strip()
        item_description = request.form.get("item_description", "").strip()

        if action == "add_section":
            if section_name:
                menu.append({"section": section_name, "items": []})
                log.info("Admin: added menu section '%s'", section_name)
                flash(f"Added section “{section_name}”.", "success")
            else:
                return render_admin_menu(menu, section_form_data={"section_name": section_name}, section_form_errors={"section_name": "Section name is required."}, status=400)

        elif action == "delete_section" and section_index is not None:
            try:
                si = parse_int_field(section_index, "section index")
            except ValueError as exc:
                return render_admin_menu(menu, status=400, section_form_errors={"global": str(exc)})
            if si < 0 or si >= len(menu):
                return render_admin_menu(menu, status=400, section_form_errors={"global": "Invalid section index"})
            log.info("Admin: deleted menu section '%s'", menu[si]["section"])
            flash(f"Deleted section “{menu[si]['section']}”.", "success")
            menu.pop(si)

        elif action == "add_item" and section_index is not None:
            try:
                si = parse_int_field(section_index, "section index")
            except ValueError as exc:
                return render_admin_menu(menu, status=400, item_form_errors={"global": str(exc)})
            if si < 0 or si >= len(menu):
                return render_admin_menu(menu, status=400, item_form_errors={"global": "Invalid section index"})
            if not item_name:
                return render_admin_menu(menu, item_form_data={si: {"item_name": item_name, "item_description": item_description}}, item_form_errors={si: {"item_name": "Item name is required."}}, status=400)
            menu[si]["items"].append({"name": item_name, "description": item_description})
            log.info("Admin: added item '%s' to section '%s'", item_name, menu[si]["section"])
            flash(f"Added item “{item_name}” to {menu[si]['section']}.", "success")

        elif action in ("update_item", "delete_item") and section_index is not None:
            try:
                si = parse_int_field(section_index, "section index")
            except ValueError as exc:
                return render_admin_menu(menu, status=400, item_form_errors={"global": str(exc)})
            if si < 0 or si >= len(menu):
                return render_admin_menu(menu, status=400, item_form_errors={"global": "Invalid section index"})
            item_index = request.form.get("item_index")
            if item_index is not None:
                try:
                    ii = parse_int_field(item_index, "item index")
                except ValueError as exc:
                    return render_admin_menu(menu, status=400, item_form_errors={"global": str(exc)})
                if ii < 0 or ii >= len(menu[si]["items"]):
                    return render_admin_menu(menu, status=400, item_form_errors={"global": "Invalid item index"})
                if action == "update_item":
                    if not item_name:
                        key = f"{si}:{ii}"
                        return render_admin_menu(
                            menu,
                            item_form_data={key: {"item_name": item_name, "item_description": item_description}},
                            item_form_errors={key: {"item_name": "Item name is required."}},
                            status=400,
                        )
                    old_name = menu[si]["items"][ii]["name"]
                    menu[si]["items"][ii] = {
                        "name": item_name,
                        "description": item_description,
                    }
                    log.info("Admin: updated item '%s' → '%s' in '%s'", old_name, item_name, menu[si]["section"])
                    flash(f"Updated item “{item_name}”.", "success")
                elif action == "delete_item":
                    log.info("Admin: deleted item '%s' from '%s'", menu[si]["items"][ii]["name"], menu[si]["section"])
                    flash(f"Deleted item “{menu[si]['items'][ii]['name']}”.", "success")
                    menu[si]["items"].pop(ii)

        save_menu(menu)
        return redirect(url_for("admin_menu"))

    return render_admin_menu(menu)


if __name__ == '__main__':
    port = int(os.getenv("PORT", "5001"))
    app.run(host='0.0.0.0', port=port)
