"""FastAPI service for SimpleFX API integration"""
import sys
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import asyncio
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.simplefx_client import get_client
from shared.config import Config
from shared.database import get_db
from shared.webhook_queue import get_webhook_queue
from shared.webhook_processor import process_webhook_data
from shared.webhook_logger import get_webhook_logger
from fastapi import Request, Body
from pydantic import BaseModel
from typing import Dict, Any
from apps.fastapi_service.models import (
    AccountStatusResponse,
    OrdersResponse,
    ChartDataResponse,
    TradeRequest,
    TradeResponse,
)
from apps.fastapi_service.config import API_PREFIX, HOST, PORT


async def sync_all_accounts():
    """Background task to sync orders for all monitored accounts with retry logic"""
    max_retries = 3
    retry_delay = 30
    
    while True:
        try:
            accounts = Config.ALL_MONITORED_ACCOUNTS
            if not accounts:
                await asyncio.sleep(600)
                continue
            
            print(f"[SYNC] Starting sync for {len(accounts)} accounts...")
            client = get_client()
            db = get_db()
            
            try:
                print("[SYNC] Pre-authenticating with primary API...")
                token = await client.get_access_token(use_secondary_api=False)
                if token:
                    print("[SYNC] Pre-authentication successful")
                else:
                    print("[SYNC] WARNING: Pre-authentication returned empty token")
            except Exception as e:
                print(f"[SYNC ERROR] Pre-authentication failed: {e}")
                print("[SYNC] Will retry authentication per account")
            
            for login_number in accounts:
                if Config.should_use_secondary_api(login_number):
                    print(f"[SYNC] Skipping account {login_number} - requires secondary API (not configured)")
                    continue
                
                retry_count = 0
                success = False
                
                await asyncio.sleep(1)
                
                while retry_count < max_retries and not success:
                    try:
                        reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
                        use_secondary = False
                        try:
                            active_data = await asyncio.wait_for(
                                client.get_active_orders(login_number, reality, False, 1, 1000),
                                timeout=30.0
                            )
                            await asyncio.sleep(0.5)
                            closed_data = await asyncio.wait_for(
                                client.get_closed_orders(login_number, reality, False, 1, 1000),
                                timeout=30.0
                            )
                        except asyncio.TimeoutError:
                            print(f"[SYNC ERROR] Account {login_number}: API timeout")
                            retry_count += 1
                            if retry_count < max_retries:
                                await asyncio.sleep(retry_delay)
                            continue
                        
                        active_orders = active_data.get('data', {}).get('marketOrders', [])
                        closed_orders = closed_data.get('data', {}).get('marketOrders', [])
                        all_orders = active_orders + closed_orders
                        
                        synced = 0
                        errors = []
                        for api_order in all_orders:
                            try:
                                order_data = {
                                    'id': str(api_order.get('id', '')),
                                    'login': login_number,
                                    'symbol': api_order.get('symbol', 'EURUSD'),
                                    'side': api_order.get('side', 'BUY'),
                                    'volume': api_order.get('volume', 0),
                                    'openPrice': api_order.get('openPrice'),
                                    'closePrice': api_order.get('closePrice'),
                                    'takeProfit': api_order.get('takeProfit'),
                                    'stopLoss': api_order.get('stopLoss'),
                                    'openTime': api_order.get('openTime'),
                                    'closeTime': api_order.get('closeTime'),
                                    'profit': api_order.get('profit', 0),
                                    'swap': api_order.get('swaps', 0),
                                    'commission': api_order.get('commission', 0),
                                    'reality': reality,
                                    'leverage': api_order.get('leverage'),
                                    'margin': api_order.get('margin'),
                                    'marginRate': api_order.get('marginRate'),
                                    'requestId': api_order.get('requestId', ''),
                                    'isFIFO': api_order.get('isFIFO', False),
                                    'exchange': 'simplefx',
                                }
                                
                                if db.upsert_order(order_data):
                                    synced += 1
                            except Exception as e:
                                errors.append(f"Order {api_order.get('id')}: {e}")
                                if len(errors) <= 5:
                                    print(f"[SYNC ERROR] Order {api_order.get('id')}: {e}")
                        
                        print(f"[SYNC] Account {login_number}: {synced}/{len(all_orders)} orders synced" + 
                              (f" ({len(errors)} errors)" if errors else ""))
                        success = True
                        
                    except Exception as e:
                        retry_count += 1
                        error_msg = str(e)
                        if "409" in error_msg or "Conflict" in error_msg:
                            print(f"[SYNC ERROR] Account {login_number} (attempt {retry_count}/{max_retries}): 409 Conflict - waiting longer...")
                            if retry_count < max_retries:
                                await asyncio.sleep(retry_delay * 2)
                            continue
                        print(f"[SYNC ERROR] Account {login_number} (attempt {retry_count}/{max_retries}): {e}")
                        if retry_count < max_retries:
                            await asyncio.sleep(retry_delay)
                        else:
                            print(f"[SYNC ERROR] Account {login_number}: Failed after {max_retries} retries")
            
            print(f"[SYNC] Completed. Next sync in 10 minutes...")
        except Exception as e:
            print(f"[SYNC ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(600)


def check_for_nodejs_services():
    """Check if Node.js/TypeScript services are running and warn user"""
    import subprocess
    import sys
    
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq node.exe", "/FO", "CSV"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "node.exe" in result.stdout:
                print("\n" + "="*60)
                print("WARNING: Node.js processes detected!")
                print("="*60)
                print("TypeScript/Node.js services are running and may conflict")
                print("with FastAPI authentication (409 Conflict errors).")
                print("\nSOLUTION:")
                print("1. Stop TypeScript service: scripts\\setup\\STOP_TYPESCRIPT.bat")
                print("2. Or kill Node.js processes manually")
                print("3. Or run: scripts\\setup\\STOP_TYPESCRIPT.bat")
                print("="*60 + "\n")
                return True
    except Exception as e:
        pass
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    check_for_nodejs_services()
    
        sync_task = asyncio.create_task(sync_all_accounts())
        yield
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="WingBot SimpleFX API Service",
    description="FastAPI service for SimpleFX broker integration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{API_PREFIX}/status/{{login_number}}", response_model=AccountStatusResponse)
async def get_status(
    login_number: str,
    reality: Optional[str] = Query(None, description="Account reality: LIVE or DEMO"),
    use_secondary_api: Optional[bool] = Query(False, description="Use secondary API key")
):
    """Get account status"""
    try:
        if reality is None:
            reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
        
        client = get_client()
        data = await client.get_account_status(login_number, reality, use_secondary_api)
        return AccountStatusResponse(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{API_PREFIX}/orders/active/{{login_number}}", response_model=OrdersResponse)
async def get_active_orders(
    login_number: str,
    reality: Optional[str] = Query(None, description="Account reality: LIVE or DEMO"),
    use_secondary_api: Optional[bool] = Query(False, description="Use secondary API key"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get active orders for an account"""
    try:
        if reality is None:
            reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
        
        client = get_client()
        data = await client.get_active_orders(
            login_number, reality, use_secondary_api, page, limit
        )
        return OrdersResponse(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{API_PREFIX}/orders/closed/{{login_number}}", response_model=OrdersResponse)
async def get_closed_orders(
    login_number: str,
    reality: Optional[str] = Query(None, description="Account reality: LIVE or DEMO"),
    use_secondary_api: Optional[bool] = Query(False, description="Use secondary API key"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    time_from: Optional[int] = Query(None, description="Start timestamp in milliseconds"),
    time_to: Optional[int] = Query(None, description="End timestamp in milliseconds")
):
    """Get closed orders for an account"""
    try:
        if reality is None:
            reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
        
        client = get_client()
        data = await client.get_closed_orders(
            login_number, reality, use_secondary_api, page, limit, time_from, time_to
        )
        return OrdersResponse(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{API_PREFIX}/chart-data", response_model=ChartDataResponse)
async def get_chart_data(
    symbol: str = Query("EURUSD", description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1d"),
    account: str = Query("3979937", description="Account number"),
    time_from: Optional[int] = Query(None, description="Start timestamp in milliseconds"),
    time_to: Optional[int] = Query(None, description="End timestamp in milliseconds")
):
    """Get chart data (candles) for a symbol"""
    try:
        client = get_client()
        data = await client.get_chart_data(symbol, timeframe, account, time_from, time_to)
        return ChartDataResponse(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{API_PREFIX}/trade", response_model=TradeResponse)
async def place_trade(request: TradeRequest):
    """Place a trade via SimpleFX API"""
    try:
        client = get_client()
        data = await client.place_trade(
            side=request.side,
            amount=request.amount,
            login_number=request.login_number,
            take_profit_price=request.take_profit_price,
            stop_loss_price=request.stop_loss_price,
            reality=request.reality,
            symbol=request.symbol,
            use_secondary_api=request.use_secondary_api,
        )
        return TradeResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{API_PREFIX}/sync-orders/{{login_number}}")
async def sync_orders(
    login_number: str,
    reality: Optional[str] = Query(None, description="Account reality: LIVE or DEMO"),
    use_secondary_api: Optional[bool] = Query(False, description="Use secondary API key")
):
    """Sync orders from SimpleFX API to database"""
    try:
        if reality is None:
            reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
        
        client = get_client()
        db = get_db()
        
        active_data = await client.get_active_orders(login_number, reality, use_secondary_api, 1, 1000)
        closed_data = await client.get_closed_orders(login_number, reality, use_secondary_api, 1, 1000)
        
        active_orders = active_data.get('data', {}).get('marketOrders', [])
        closed_orders = closed_data.get('data', {}).get('marketOrders', [])
        all_orders = active_orders + closed_orders
        
        synced_count = 0
        errors = []
        
        for api_order in all_orders:
            try:
                order_data = {
                    'id': str(api_order.get('id', '')),
                    'login': login_number,
                    'symbol': api_order.get('symbol', 'EURUSD'),
                    'side': api_order.get('side', 'BUY'),
                    'volume': api_order.get('volume', 0),
                    'openPrice': api_order.get('openPrice'),
                    'closePrice': api_order.get('closePrice'),
                    'takeProfit': api_order.get('takeProfit'),
                    'stopLoss': api_order.get('stopLoss'),
                    'openTime': api_order.get('openTime'),
                    'closeTime': api_order.get('closeTime'),
                    'profit': api_order.get('profit', 0),
                    'swap': api_order.get('swaps', 0),
                    'commission': api_order.get('commission', 0),
                    'reality': reality,
                    'leverage': api_order.get('leverage'),
                    'margin': api_order.get('margin'),
                    'marginRate': api_order.get('marginRate'),
                    'requestId': api_order.get('requestId', ''),
                    'isFIFO': api_order.get('isFIFO', False),
                    'exchange': 'simplefx',
                }
                
                if db.upsert_order(order_data):
                    synced_count += 1
            except Exception as e:
                errors.append(f"Order {api_order.get('id')}: {str(e)}")
        
        return {
            "success": True,
            "synced": synced_count,
            "total": len(all_orders),
            "errors": errors[:10] if errors else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook")
async def webhook_endpoint(request: Request):
    """Webhook endpoint for TradingView alerts"""
    import time
    start_time = time.time() * 1000
    
    try:
        try:
            body = await request.json()
        except:
            body_text = await request.body()
            import json
            body = json.loads(body_text.decode())
        
        login = body.get('l') or Config.DEFAULT_ACCOUNT_NUMBER
        alert_id = body.get('id') or f"{int(time.time() * 1000)}_{hash(str(body))}"
        
        db = get_db()
        if db.order_exists_with_alert_id(alert_id, login):
            webhook_logger = get_webhook_logger()
            symbol = body.get('sy', 'UNKNOWN')
            action = body.get('a', 'UNKNOWN')
            size = body.get('z', 0)
            webhook_logger.log_duplicate(symbol, action, login, alert_id, size)
            return {
                "message": "Alert already processed",
                "alertId": alert_id,
                "account": login
            }
        
        webhook_queue = get_webhook_queue()
        if webhook_queue.check_for_duplicate(body, login):
            webhook_logger = get_webhook_logger()
            symbol = body.get('sy', 'UNKNOWN')
            action = body.get('a', 'UNKNOWN')
            size = body.get('z', 0)
            webhook_logger.log_duplicate(symbol, action, login, alert_id, size)
            return {
                "message": "Duplicate webhook detected and ignored",
                "account": login
            }
        
        webhook_logger = get_webhook_logger()
        symbol = body.get('sy', 'UNKNOWN')
        action = body.get('a', 'UNKNOWN')
        size = body.get('z', 0)
        tp = body.get('t', 0)
        sl = body.get('s', 0)
        webhook_logger.log_webhook_received(symbol, action, size, tp, sl, login, alert_id)
        
        job_id = await webhook_queue.add(body, login)
        queue_status = webhook_queue.get_queue_status()
        
        return {
            "success": True,
            "message": "Webhook queued for processing",
            "jobId": job_id,
            "queueStatus": queue_status,
            "processingTime": int(time.time() * 1000) - start_time
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": "Failed to queue webhook",
            "details": str(e)
        }, 500


@app.get("/api/list-accounts")
async def list_accounts():
    """List all monitored accounts"""
    return {
        "accounts": Config.ALL_MONITORED_ACCOUNTS,
        "default": Config.DEFAULT_ACCOUNT_NUMBER,
        "default2": Config.DEFAULT_ACCOUNT_NUMBER2
    }


@app.get("/api/db-orders/{login_number}")
async def get_db_orders(login_number: str):
    """Get all orders from database for account"""
    try:
        db = get_db()
        orders = db.get_orders(login_number)
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recent-db-orders/{login_number}")
async def get_recent_db_orders(login_number: str, limit: int = Query(100, ge=1, le=1000)):
    """Get recent orders from database"""
    try:
        db = get_db()
        orders = db.get_recent_orders(login_number, limit)
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/webhook-outcomes/{login_number}")
async def get_webhook_outcomes(login_number: str, limit: int = Query(100, ge=1, le=1000)):
    """Get webhook outcomes for account"""
    try:
        db = get_db()
        outcomes = db.get_webhook_outcomes(login_number, limit)
        return outcomes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/account-settings/{login_number}")
async def get_account_settings(login_number: str):
    """Get account settings"""
    try:
        db = get_db()
        settings = db.get_account_settings(login_number)
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/account-settings/{login_number}")
async def update_account_settings(login_number: str, settings: Dict[str, Any] = Body(...)):
    """Update account settings"""
    try:
        db = get_db()
        return {"success": True, "message": "Settings updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fastapi-simplefx"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    client = get_client()
    await client.close()


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

