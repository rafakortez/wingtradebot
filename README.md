# WingTradeBot

Automated trading bot for SimpleFX integration with TradingView webhooks.

## Overview

This project implements a trading bot system with multiple dashboard implementations for exploratory work in software engineering frameworks. The system consists of:

- **FastAPI Service**: Backend API service for SimpleFX broker integration
- **Flask Dashboard**: Web dashboard implementation using Flask
- **Django Dashboard**: Web dashboard implementation using Django

Both Flask and Django implementations provide the same functionality, serving as exploratory work to understand and compare different Python web frameworks.

## Architecture

- `shared/`: Core functionality shared across all services
  - `simplefx_client.py`: SimpleFX API client
  - `config.py`: Configuration management
  - `database.py`: Database operations
  - `webhook_processor.py`: Webhook processing logic

- `apps/fastapi_service/`: FastAPI backend service
- `apps/flask_app/`: Flask dashboard implementation
- `apps/django_app/`: Django dashboard implementation

## Setup

1. **Install dependencies**:
   ```bash
   scripts\setup\INSTALL_DEPENDENCIES.bat
   ```

2. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Fill in your SimpleFX API keys and other configuration

3. **Start services**:
   - FastAPI: `cd apps\fastapi_service && python run.py`
   - Flask: `scripts\setup\START_FLASK.bat`
   - Django: `scripts\setup\START_DJANGO.bat`

## Configuration

All sensitive data (API keys, secrets, passwords) should be configured via environment variables in `.env` file. See `.env.example` for required variables.

## Services

- **FastAPI**: http://localhost:8000 (API) | http://localhost:8000/docs (Swagger)
- **Flask Dashboard**: http://localhost:5000
- **Django Dashboard**: http://localhost:8001

## Framework Comparison

This project includes both Flask and Django implementations as exploratory work to:
- Compare framework approaches and patterns
- Understand differences in routing, templating, and middleware
- Evaluate performance and development experience
- Learn best practices for each framework

Both implementations provide identical functionality, allowing for direct comparison of the frameworks in a real-world application context.

## License

See LICENSE file for details.

