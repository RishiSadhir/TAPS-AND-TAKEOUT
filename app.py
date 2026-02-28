import os
from datetime import datetime, date, timedelta
from events import load_events, save_events

from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "devfallback")
csrf = CSRFProtect(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/menu')
def menu():
    return render_template('menu.html')


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
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == os.getenv("ADMIN_PASSWORD"):
            session['admin'] = True
            return redirect(url_for('admin_events'))
        return "Invalid credentials", 403
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
        # Inside your "add" or "update" logic:
        date_str = request.form["date"]
        try:
            # Validates YYYY-MM-DD
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return "Invalid date format", 400
        # Either 'add', 'update', or, 'delete'
        action = request.form.get("action")
        index = request.form.get("index")

        if action == "add":
            # Add a new event from form data
            new_event = {
                "title": request.form["title"],
                "date": request.form["date"],
                "description": request.form["description"]
            }
            events.append(new_event)

        elif action in ["update", "delete"] and index is not None:
            index = int(index)
            if action == "update":
                events[index] = {
                    "title": request.form["title"],
                    "date": request.form["date"],
                    "description": request.form["description"]
                }

            elif action == "delete":
                # Delete the event at the given index
                events.pop(index)

        save_events(events)
        return redirect(url_for("admin_events"))

    else:
        return render_template("admin_events.html", events=events)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
