# Taps & Takeout

A minimal Flask website for a neighborhood pub. Intentionally simple and borderline offputting — the bar's ask was a basic site they can occasionally list events on.

**Live site:** https://taps-and-takeout.onrender.com
**Admin panel:** https://taps-and-takeout.onrender.com/admin (username: `admin`)

---

## Scope

- Public pages: home, menu, events, contact
- Admin panel: manage events and menu sections/items via a simple web UI
- No database — data lives in JSON files on disk
- No user accounts — single admin protected by a password env var

## Structure

```
app.py              # Flask routes and request handling
events.py           # load_events() / save_events() — reads/writes data/events.json
menu_data.py        # load_menu() / save_menu() — reads/writes data/menu.json
tests.py            # pytest suite (45 tests)

data/
  menu.json         # Menu sections and items (committed; seeded from original hardcoded menu)
  events.json       # Upcoming events (not committed; resets on redeploy)

templates/
  base.html         # Shared site layout (header, nav, footer)
  admin_base.html   # Admin layout extending base.html (adds admin nav bar)
  index.html
  menu.html
  events.html
  contact.html
  admin_login.html
  admin_events.html
  admin_menu.html

static/
  style.css
  images/
```

## Running locally

```bash
pip install -r requirements.txt

# Create .env with:
# FLASK_SECRET_KEY=...
# ADMIN_PASSWORD=...

# Both are required. The app will fail fast at startup if either is missing.

python app.py           # respects PORT, defaults to 5001 locally
# or
flask run --port 5001   # port 5000 blocked by macOS AirPlay
```

## Tests

```bash
pytest tests.py -v
```

## Deployment

Hosted on Render (free tier, auto-deploys from `main`). Set both `FLASK_SECRET_KEY` and `ADMIN_PASSWORD` in the Render environment before deploy. The app also respects Render's `PORT` environment variable at runtime. Data resets on redeploy — events are expected to be re-entered, menu is seeded from `data/menu.json` in the repo.
