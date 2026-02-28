import os
import logging
from datetime import datetime, date, timedelta
from events import load_events, save_events
from menu_data import load_menu, save_menu

from flask import Flask, render_template, request, redirect, url_for, session, current_app
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

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "devfallback")
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
    upcoming = sorted([e for e in events_list if e['date'] >= yesterday], key=lambda e: e['date'])
    return render_template('events.html', events=upcoming)


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/admin', methods=['GET', 'POST'])
@limiter.limit("10 per minute", exempt_when=lambda: current_app.config.get("TESTING", False))
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == os.getenv("ADMIN_PASSWORD"):
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

        if action in ("add", "update"):
            date_str = request.form.get("date", "")
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return "Invalid date format", 400

        if action == "add":
            title = request.form.get("title", "").strip()
            if not title:
                return "Title is required", 400
            new_event = {
                "title": title,
                "date": request.form["date"],
                "description": request.form.get("description", "").strip(),
            }
            events.append(new_event)
            log.info("Admin: added event '%s' on %s", new_event["title"], new_event["date"])

        elif action in ("update", "delete") and index is not None:
            idx = int(index)
            if idx < 0 or idx >= len(events):
                return "Invalid index", 400

            if action == "update":
                title = request.form.get("title", "").strip()
                if not title:
                    return "Title is required", 400
                old_title = events[idx]["title"]
                events[idx] = {
                    "title": title,
                    "date": request.form["date"],
                    "description": request.form.get("description", "").strip(),
                }
                log.info("Admin: updated event '%s' → '%s'", old_title, title)

            elif action == "delete":
                log.info("Admin: deleted event '%s'", events[idx]["title"])
                events.pop(idx)

        save_events(events)
        return redirect(url_for("admin_events"))

    return render_template("admin_events.html", events=events)


@app.route("/admin-menu", methods=["GET", "POST"])
def admin_menu():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    menu = load_menu()

    if request.method == "POST":
        action = request.form.get("action")
        section_index = request.form.get("section_index")

        if action == "add_section":
            section_name = request.form.get("section_name", "").strip()
            if section_name:
                menu.append({"section": section_name, "items": []})
                log.info("Admin: added menu section '%s'", section_name)

        elif action == "delete_section" and section_index is not None:
            si = int(section_index)
            if si < 0 or si >= len(menu):
                return "Invalid section index", 400
            log.info("Admin: deleted menu section '%s'", menu[si]["section"])
            menu.pop(si)

        elif action == "add_item" and section_index is not None:
            si = int(section_index)
            if si < 0 or si >= len(menu):
                return "Invalid section index", 400
            item_name = request.form.get("item_name", "").strip()
            if not item_name:
                return "Item name is required", 400
            item_description = request.form.get("item_description", "").strip()
            menu[si]["items"].append({"name": item_name, "description": item_description})
            log.info("Admin: added item '%s' to section '%s'", item_name, menu[si]["section"])

        elif action in ("update_item", "delete_item") and section_index is not None:
            si = int(section_index)
            if si < 0 or si >= len(menu):
                return "Invalid section index", 400
            item_index = request.form.get("item_index")
            if item_index is not None:
                ii = int(item_index)
                if ii < 0 or ii >= len(menu[si]["items"]):
                    return "Invalid item index", 400
                if action == "update_item":
                    item_name = request.form.get("item_name", "").strip()
                    if not item_name:
                        return "Item name is required", 400
                    old_name = menu[si]["items"][ii]["name"]
                    menu[si]["items"][ii] = {
                        "name": item_name,
                        "description": request.form.get("item_description", "").strip(),
                    }
                    log.info("Admin: updated item '%s' → '%s' in '%s'", old_name, item_name, menu[si]["section"])
                elif action == "delete_item":
                    log.info("Admin: deleted item '%s' from '%s'", menu[si]["items"][ii]["name"], menu[si]["section"])
                    menu[si]["items"].pop(ii)

        save_menu(menu)
        return redirect(url_for("admin_menu"))

    return render_template("admin_menu.html", menu=menu)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
