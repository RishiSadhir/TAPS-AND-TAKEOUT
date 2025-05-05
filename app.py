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
        action = request.form.get("action") # Either 'add', 'update', or, 'delete'
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
        return redirect(url_for("admin_events", key=SECRET_KEY))

    else:
        return render_template("admin_events.html", events=events)


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
