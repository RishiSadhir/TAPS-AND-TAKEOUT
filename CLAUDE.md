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
python app.py
# or
flask run

# Production (via Render using Procfile)
gunicorn app:app
```

## Environment Variables

Create a `.env` file with:
```
FLASK_SECRET_KEY=...
ADMIN_PASSWORD=...
```

Both fall back to insecure defaults (`devfallback` / `admin`) if not set. Note: `ADMIN_PASSWORD` has no fallback in production — if unset, `os.getenv` returns `None` and login will always fail.

## Architecture

- **`app.py`** — Flask routes: `/`, `/menu`, `/events`, `/contact`, `/admin` (login), `/admin-events` (events CRUD), `/admin-menu` (menu CRUD)
- **`events.py`** — `load_events()` / `save_events()`: reads/writes `data/events.json`, converting between `datetime.date` objects and ISO strings
- **`menu_data.py`** — `load_menu()` / `save_menu()`: reads/writes `data/menu.json`; falls back to built-in default seed if file missing
- **`data/events.json`** — flat JSON array of `{title, date, description}` objects; this is the events database
- **`data/menu.json`** — JSON array of `{section, items: [{name, description}]}` objects; this is the menu database
- **`templates/`** — Jinja2 templates; admin pages extend `admin_base.html` which extends `base.html`
- **`static/`** — single `style.css` + `images/` directory
- **`tests.py`** — pytest suite; run with `pytest tests.py -v`

## Key Behaviors

- Events page filters out events older than yesterday (`event.date >= yesterday`) and sorts by date — both done in Python in the `/events` route, not in the template
- Admin is session-based (8-hour timeout); login at `/admin`, manage events at `/admin-events`, manage menu at `/admin-menu`; login is rate-limited to 10 attempts/minute
- No actual database — data is stored as JSON on disk, which means it resets on Render deploys unless a persistent disk is configured
