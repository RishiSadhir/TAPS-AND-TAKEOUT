import os
import json

EVENTS_FILE = os.path.join("data", "events.json")


def load_events():
    if not os.path.exists(EVENTS_FILE):
        return []
    with open(EVENTS_FILE, "r") as f:
        return json.load(f)


def save_events(events):
    with open(EVENTS_FILE, "w") as f:
        json.dump(events, f, indent=2)
