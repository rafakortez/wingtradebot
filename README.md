# WingBot

Automated trading bot system integrating SimpleFX broker API with TradingView webhooks. Multi-framework implementation featuring FastAPI, Flask, and Django.

## Architecture

**Backend Services:**
- FastAPI REST API service for broker integration and webhook processing
- Shared Python modules for API client, database operations, and webhook handling

**Frontend Dashboards:**
- Flask web application with Socket.IO real-time updates
- Django web application with Channels WebSocket support

Both dashboard implementations provide identical functionality for account monitoring, order management, and real-time trading data visualization.

## Tech Stack

- **Backend:** FastAPI, Flask, Django
- **Database:** SQLite with SQLAlchemy ORM
- **Real-time:** Flask-SocketIO, Django Channels
- **API Integration:** SimpleFX REST API, WebSocket connections
- **Frontend:** React, HTML5, CSS3

## Quick Start

1. Install dependencies:
   ```bash
   scripts\setup\INSTALL_DEPENDENCIES.bat
   ```

2. Configure environment:
   - Copy `.env.example` to `.env`
   - Set SimpleFX API credentials and configuration

3. Start services:
   - FastAPI: `scripts\setup\START_FASTAPI.bat`
   - Flask: `scripts\setup\START_FLASK.bat`
   - Django: `scripts\setup\START_DJANGO.bat`

## Services

- FastAPI API: `http://localhost:8000` | Swagger: `http://localhost:8000/docs`
- Flask Dashboard: `http://localhost:5000`
- Django Dashboard: `http://localhost:8001`

## Project Structure

```
shared/              # Core modules (API client, database, webhooks)
apps/
  fastapi_service/   # REST API backend
  flask_app/         # Flask dashboard
  django_app/        # Django dashboard
scripts/setup/       # Setup and startup scripts
```

## Configuration

All sensitive credentials are managed via environment variables. See `.env.example` for required configuration.
