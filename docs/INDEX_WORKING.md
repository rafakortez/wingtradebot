# Index Working for Both Flask and Django

## Changes Made

1. **Unified index.html**
   - Copied Flask's `index.html` to Django
   - Both apps now use the same template
   - Location:
     - Flask: `apps/flask_app/templates/index.html`
     - Django: `apps/django_app/dashboard/templates/dashboard/index.html`

2. **Django URLs Updated**
   - Added support for URLs with and without trailing slashes
   - Matches Flask's URL pattern (no trailing slashes)
   - Both patterns work: `/api/status/123` and `/api/status/123/`

3. **Django API Views Enhanced**
   - Added FastAPI health check (matches Flask)
   - Improved error handling with timeouts
   - Better error messages when FastAPI is not available
   - Same timeout values as Flask (15 seconds)

## API Endpoints (Both Flask and Django)

Both frameworks now expose the same endpoints:

- `GET /api/status/<login_number>` - Account status
- `GET /api/recent-db-orders/<login_number>` - Recent orders from DB
- `GET /api/webhook-outcomes/<login_number>` - Webhook outcomes
- `GET /api/recent-logs` - Recent logs (optional `?account=123`)
- `GET /api/simplefx-chart-data` - Chart data (query params: `symbol`, `timeframe`, `account`)

## Testing

**Flask:**
```bash
cd apps/flask_app
python app.py
# Visit http://localhost:5000
```

**Django:**
```bash
cd apps/django_app
python manage.py runserver
# Visit http://localhost:8001
```

Both should now display the same dashboard with full functionality!

## Notes

- Both apps require FastAPI to be running on `http://localhost:8000`
- Both apps use the same shared modules (`shared/`)
- Both apps use the same database (`sfx_historical_orders.db`)
- Django runs on port 8001 by default (configurable via `DJANGO_PORT` env var)
- Flask runs on port 5000 by default (configurable via `FLASK_PORT` env var)

