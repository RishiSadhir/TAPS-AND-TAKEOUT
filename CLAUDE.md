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

Both fall back to insecure defaults (`devfallback` / `admin`) if not set.

## Architecture

- **`app.py`** — Flask routes: `/`, `/menu`, `/events`, `/contact`, `/admin` (login), `/admin-events` (CRUD)
- **`events.py`** — `load_events()` / `save_events()`: reads/writes `data/events.json`, converting between `datetime.date` objects and ISO strings
- **`data/events.json`** — flat JSON array of `{title, date, description}` objects; this is the database
- **`templates/`** — Jinja2 templates extending `base.html`; all pages share the logo header
- **`static/`** — single `style.css` + `images/` directory

## Key Behaviors

- Events page filters out events older than yesterday (`event.date >= yesterday`) and sorts by date — both handled in the Jinja2 template
- Admin is session-based; login at `/admin`, manage events at `/admin-events`
- No actual database — events are stored as JSON on disk, which means they reset on Render deploys unless a persistent disk is configured
