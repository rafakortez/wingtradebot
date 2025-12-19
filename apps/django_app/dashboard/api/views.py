"""API views for dashboard"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
from shared.config import Config
from shared.database import get_db


def get_status(request, login_number):
    """Get account status - proxy to FastAPI"""
    try:
        reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
        use_secondary = Config.should_use_secondary_api(login_number)
        
        # Check if FastAPI is available (short timeout to not block)
        try:
            health_check = requests.get(f"{settings.FASTAPI_URL}/health", timeout=3)
            if health_check.status_code != 200:
                print(f"[WARNING] FastAPI health check returned {health_check.status_code}")
        except requests.exceptions.ConnectionError:
            from datetime import datetime, timezone
            return JsonResponse({
                "error": f"FastAPI service is not running at {settings.FASTAPI_URL}. Please start the FastAPI service first.",
                "fastapi_url": settings.FASTAPI_URL,
                "accountStatus": {},
                "activeOrders": {},
                "closedOrders": {},
                "unrealizedPnL": 0,
                "realizedPnL": 0,
                "orderCounts": {"buyVolume": 0, "sellVolume": 0},
                "serverTime": datetime.now(timezone.utc).isoformat()
            }, status=503)
        except requests.exceptions.Timeout:
            # If health check timeout, still try main requests
            print(f"[WARNING] FastAPI health check timeout, but continuing with requests")
        
        # Get account status
        try:
            status_response = requests.get(
                f"{settings.FASTAPI_URL}/api/simplefx/status/{login_number}",
                params={"reality": reality, "use_secondary_api": use_secondary},
                timeout=15
            )
            status_data = status_response.json() if status_response.status_code == 200 else {}
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"[ERROR] Failed to get account status: {e}")
            status_data = {}
        
        # Get active orders
        try:
            active_response = requests.get(
                f"{settings.FASTAPI_URL}/api/simplefx/orders/active/{login_number}",
                params={"reality": reality, "use_secondary_api": use_secondary},
                timeout=15
            )
            active_data = active_response.json() if active_response.status_code == 200 else {}
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"[ERROR] Failed to get active orders: {e}")
            active_data = {}
        
        # Get closed orders
        try:
            closed_response = requests.get(
                f"{settings.FASTAPI_URL}/api/simplefx/orders/closed/{login_number}",
                params={"reality": reality, "use_secondary_api": use_secondary},
                timeout=15
            )
            closed_data = closed_response.json() if closed_response.status_code == 200 else {}
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"[ERROR] Failed to get closed orders: {e}")
            closed_data = {}
        
        # Calculate P&L
        unrealized_pnl = sum(
            float(order.get('profit', 0))
            for order in active_data.get('data', {}).get('data', {}).get('marketOrders', [])
        )
        
        realized_pnl = sum(
            float(order.get('profit', 0))
            for order in closed_data.get('data', {}).get('data', {}).get('marketOrders', [])
        )
        
        # Calculate order counts
        active_orders = active_data.get('data', {}).get('data', {}).get('marketOrders', [])
        buy_volume = sum(float(o.get('volume', 0)) for o in active_orders if o.get('side', '').upper() == 'BUY')
        sell_volume = sum(float(o.get('volume', 0)) for o in active_orders if o.get('side', '').upper() == 'SELL')
        
        return JsonResponse({
            "accountStatus": status_data.get('data', {}),
            "activeOrders": active_data.get('data', {}),
            "closedOrders": closed_data.get('data', {}),
            "unrealizedPnL": unrealized_pnl,
            "realizedPnL": realized_pnl,
            "orderCounts": {
                "buyVolume": buy_volume,
                "sellVolume": sell_volume
            },
            "serverTime": status_data.get('serverTime') if status_data else None
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_recent_db_orders(request, login_number):
    """Get recent orders from database"""
    try:
        db = get_db()
        orders = db.get_recent_orders(login_number, limit=100)
        # Converter campos para formato esperado pelo frontend
        for order in orders:
            if 'open_time' in order:
                order['openTime'] = order.get('open_time')
            if 'close_time' in order:
                order['closeTime'] = order.get('close_time')
            if 'open_price' in order:
                order['openPrice'] = order.get('open_price')
            if 'close_price' in order:
                order['closePrice'] = order.get('close_price')
            if 'take_profit' in order:
                order['takeProfit'] = order.get('take_profit')
            if 'stop_loss' in order:
                order['stopLoss'] = order.get('stop_loss')
        return JsonResponse(orders, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


def get_webhook_outcomes(request, login_number):
    """Get webhook outcomes"""
    try:
        db = get_db()
        outcomes = db.get_webhook_outcomes(login_number, limit=100)
        return JsonResponse(outcomes, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_recent_logs(request):
    """Get recent logs"""
    try:
        account = request.GET.get('account')
        db = get_db()
        logs = db.get_recent_logs(account=account, limit=50)
        # Format logs
        formatted_logs = [
            {
                "time": log.get('timestamp', ''),
                "message": log.get('message', '')
            }
            for log in logs
        ]
        return JsonResponse(formatted_logs, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_chart_data(request):
    """Get chart data - proxy to FastAPI"""
    try:
        symbol = request.GET.get('symbol', 'EURUSD')
        timeframe = request.GET.get('timeframe', '1h')
        account = request.GET.get('account', '3028761')
        
        response = requests.get(
            f"{settings.FASTAPI_URL}/api/simplefx/chart-data",
            params={
                "symbol": symbol,
                "timeframe": timeframe,
                "account": account
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return JsonResponse(data.get('data', []), safe=False)
        else:
            # Return empty array instead of error to prevent frontend issues
            print(f"[WARNING] Chart data request failed: {response.status_code} - {response.text}")
            return JsonResponse([], safe=False)
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to FastAPI at {settings.FASTAPI_URL}")
        return JsonResponse([], safe=False)
    except Exception as e:
        print(f"[ERROR] Error fetching chart data: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse([], safe=False)

