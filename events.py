import os
import json
from datetime import datetime, date

EVENTS_FILE = os.path.join("data", "events.json")


def load_events():
    if not os.path.exists(EVENTS_FILE):
        return []
    with open(EVENTS_FILE, "r") as f:
        events = json.load(f)
        # Convert string dates to datetime.date
        for event in events:
            if isinstance(event.get("date"), str):
                event["date"] = datetime.strptime(event["date"], "%Y-%m-%d").date()
        return events


def save_events(events):
    # 1. Make sure parent directory exists
    directory = os.path.dirname(EVENTS_FILE)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    # 2. Convert date objects back to ISO strings
    serializable_events = []
    for event in events:
        ev = event.copy()
        if isinstance(ev.get("date"), date):
            ev["date"] = ev["date"].isoformat()
        serializable_events.append(ev)

    # 3. Write the JSON file
    with open(EVENTS_FILE, "w") as f:
        json.dump(serializable_events, f, indent=2)
