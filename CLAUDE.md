# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A minimal Flask website for Taps & Takeout, a neighborhood pub. Intentionally simple and low-key by design — the client wants a basic site with optional event listings.

- Live site: https://taps-and-takeout.onrender.com/
- Admin panel: https://taps-and-takeout.onrender.com/admin (username: `admin`)

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py   # respects PORT, defaults to 5001 locally
# or
flask run --port 5001

# Production (via Render using Procfile)
gunicorn app:app
```

## Environment Variables

Create a `.env` file with:
```
FLASK_SECRET_KEY=...
ADMIN_PASSWORD=...
```

Both variables are required. The app now fails fast at startup if either one is missing.

## Architecture

- **`app.py`** — Flask routes: `/`, `/menu`, `/events`, `/contact`, `/admin` (login), `/admin-events` (events CRUD), `/admin-menu` (menu CRUD)
- **`events.py`** — `load_events()` / `save_events()`: reads/writes `data/events.json`, converting between `datetime.date` objects and ISO strings
- **`menu_data.py`** — `load_menu()` / `save_menu()`: reads/writes `data/menu.json`; falls back to built-in default seed if file missing
- **`data/events.json`** — flat JSON array of `{title, date, description}` objects; this is the events database
- **`data/menu.json`** — JSON array of `{section, items: [{name, description}]}` objects; this is the menu database
- **`templates/`** — Jinja2 templates; admin pages extend `admin_base.html` which extends `base.html`
- **`static/`** — single `style.css` + `images/` directory
- **`tests.py`** — pytest suite (currently 45 tests); run with `pytest tests.py -v`

## Key Behaviors

- Events page filters out events older than yesterday (`event.date >= yesterday`) and sorts by date — both done in Python in the `/events` route, not in the template
- Admin is session-based (8-hour timeout); login at `/admin`, manage events at `/admin-events`, manage menu at `/admin-menu`; login is rate-limited to 10 attempts/minute
- Admin POST handlers validate malformed numeric indices and return `400` instead of raising `500`
- Local `python app.py` runs respect `PORT` and default to `5001`; this avoids common macOS conflicts on `5000` and matches Render's runtime model
- No actual database — data is stored as JSON on disk, which means it resets on Render deploys unless a persistent disk is configured
