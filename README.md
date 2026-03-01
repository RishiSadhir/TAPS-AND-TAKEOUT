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
app.py              # Thin entrypoint that creates the Flask app
events.py           # JSON event persistence helpers
menu_data.py        # JSON menu persistence helpers
tests.py            # pytest suite (50 tests)
tests_e2e.py        # Playwright smoke tests for real browser admin flows
requirements-dev.txt

taps_and_takeout/
  app_factory.py    # Flask app creation and extension wiring
  storage.py        # content-store abstraction over JSON data
  validation.py     # sanitization and field length limits
  logging_utils.py  # structured admin/validation logging
  routes/
    public.py       # public pages + /healthz
    admin.py        # admin login and CRUD routes

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

Browser smoke test:

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
pytest tests_e2e.py -v
```

CI:

- GitHub Actions runs both suites on pushes to `main` and on pull requests.

## Deployment

Hosted on Render (free tier, auto-deploys from `main`). Set both `FLASK_SECRET_KEY` and `ADMIN_PASSWORD` in the Render environment before deploy. The app also respects Render's `PORT` environment variable at runtime. Data resets on redeploy — events are expected to be re-entered, menu is seeded from `data/menu.json` in the repo.

## Operations

- Health check: `/healthz`
- Admin inputs are sanitized server-side and capped before writing to disk.
