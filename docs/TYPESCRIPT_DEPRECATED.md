# ⚠️ TypeScript Code is DEPRECATED

## Status: REFERENCE ONLY

All TypeScript code in the `src/` directory is **DEPRECATED** and should **NOT be executed**.

All functionality has been migrated to Python in the `shared/` folder.

## ✅ Use Python Services Instead

- **FastAPI**: `apps/fastapi_service/` - Main API service
- **Flask**: `apps/flask_app/` - Dashboard
- **Django**: `apps/django_app/` - Dashboard
- **Shared**: `shared/` - All core functionality

## 🚫 Do NOT Run TypeScript

**Never run these commands:**
```bash
npm start
npm run dev
npm run build
pm2 start
ts-node src/server.ts
```

**These will cause 409 Conflict errors** because TypeScript and Python will try to authenticate with the same API key.

## ✅ Use Python Scripts Instead

```bash
# Install dependencies
scripts\setup\INSTALL_DEPENDENCIES.bat

# Start Flask (auto-starts FastAPI)
scripts\setup\START_FLASK.bat

# Start Django (auto-starts FastAPI)
scripts\setup\START_DJANGO.bat
```

## 📋 Migration Complete

All TypeScript functionality has been migrated:

| TypeScript | Python |
|-----------|--------|
| `src/config.ts` | `shared/config.py` |
| `src/database.ts` | `shared/database.py` |
| `src/services/simplefx.ts` | `shared/simplefx_client.py` |
| `src/services/simplefxWebSocket.ts` | `shared/simplefx_websocket.py` |
| `src/utils/webhookLogger.ts` | `shared/webhook_logger.py` |
| `src/utils/webhookQueue.ts` | `shared/webhook_queue.py` |
| `src/server.ts` | `apps/fastapi_service/main.py` |

## 🔍 If TypeScript is Running

If you see TypeScript services running:

1. **Stop them immediately:**
   ```bash
   scripts\setup\STOP_TYPESCRIPT.bat
   ```

2. **Check for auto-start:**
   - Check for Node.js processes: `tasklist | findstr node`
   - Check Windows Startup folder
   - Check Task Scheduler: `schtasks /query | findstr node`

3. **PM2 has been removed:**
   - All PM2 references removed from package.json
   - PM2 is no longer used for process management
   - Python services run directly without PM2

## ✅ Current Architecture

```
FastAPI (Python) - Only service that authenticates
    ↑
    ├── Flask (Python) - Uses FastAPI as proxy
    └── Django (Python) - Uses FastAPI as proxy
```

**All services use Python shared modules - NO TypeScript needed.**

