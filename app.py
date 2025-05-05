from flask import Flask, render_template, request, redirect, url_for, render_template_string
from events import load_events, save_events

app = Flask(__name__)

SECRET_KEY = "secret123"  # You can change this to anything


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/menu')
def menu():
    return render_template('menu.html')


@app.route('/events')
def events():
    events_list = load_events()
    return render_template('events.html', events=events_list)


@app.route("/admin-events", methods=["GET", "POST"])
def admin_events():
    if request.args.get("key") != SECRET_KEY:
        return "Unauthorized", 403

    events = load_events()
    if request.method == "POST":
        title = request.form["title"]
        date = request.form["date"]
        description = request.form["description"]
        events.append({
            "title": title,
            "date": date,
            "description": description
        })
        save_events(events)
        return redirect(url_for("admin_events", key=SECRET_KEY))

    return render_template_string("""
        <h1>Admin Events</h1>
        <form method="post">
            <input name="title" placeholder="Event Title" required><br>
            <input name="date" placeholder="Date" required><br>
            <textarea name="description" placeholder="Description"></textarea><br>
            <button type="submit">Add Event</button>
        </form>
        <hr>
        <h2>Current Events</h2>
        <ul>
        {% for event in events %}
            <li><strong>{{ event.title }}</strong> ({{ event.date }}): {{ event.description }}</li>
        {% endfor %}
        </ul>
    """, events=events)


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
