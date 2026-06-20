# D4D Leon County CRM

A FastAPI-based personal driving-for-dollars CRM for Leon County, Florida.

## Stack

- Python 3.13
- FastAPI + Jinja2 templates
- SQLite + SQLAlchemy ORM
- Tailwind CSS (CDN)
- Vanilla JavaScript

## Setup

```bash
pip install -r requirements.txt
python app.py
```

The app creates the SQLite database automatically on startup.

## Configuration

Set environment variables as needed:

- `DATABASE_URL` (default: `sqlite:///./d4d_crm.db`)
- `NOMINATIM_BASE_URL` (default: `https://nominatim.openstreetmap.org`)
- `NOMINATIM_USER_AGENT` (set to your contact-friendly app identifier)
- `LEON_PROPERTY_SEARCH_URL` (optional endpoint for Leon County property data lookup)
- `APP_HOST` (default: `127.0.0.1`; use `0.0.0.0` to expose on LAN)
- `APP_PORT` (default: `8000`)

## Main Routes

- `/` - Address search with autocomplete and add-property flow
- `/leads` - Lead dashboard with status filter
- `/property/{id}` - Property details, status/notes updates, and call history

## Notes

- Address autocomplete is restricted to Leon County, Florida in the backend filter.
- Leon County property enrichment uses a fault-tolerant, best-effort lookup service and never crashes lead creation if property data is unavailable.
- Lead scoring bonus logic:
  - Absentee owner: +25
  - Owned 10+ years: +25 (when purchase date data exists)
  - No property data found: +10
