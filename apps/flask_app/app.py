"""Flask application for WingTradeBot dashboard"""
import sys
import os
import asyncio
import threading
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import requests
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import Config
from shared.database import get_db
from shared.simplefx_websocket import get_websocket

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# FastAPI service URL (can be configured via env)
FASTAPI_URL = os.getenv('FASTAPI_URL', 'http://localhost:8000')

# WebSocket client for SimpleFX quotes
websocket_client = get_websocket()
dashboard_update_interval = 10  # seconds
last_dashboard_update = 0


def format_datetime(timestamp):
    """Format timestamp to datetime string"""
    if not timestamp:
        return 'N/A'
    if isinstance(timestamp, str):
        try:
            timestamp = int(timestamp)
        except ValueError:
            return timestamp
    try:
        dt = datetime.fromtimestamp(timestamp / 1000) if timestamp > 1e10 else datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return 'N/A'


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/status/<login_number>')
def get_status(login_number):
    """Get account status - proxy to FastAPI"""
    try:
        reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
        use_secondary = Config.should_use_secondary_api(login_number)
        
        # Verificar se FastAPI está disponível (timeout curto para não bloquear)
        try:
            health_check = requests.get(f"{FASTAPI_URL}/health", timeout=3)
            if health_check.status_code != 200:
                print(f"[WARNING] FastAPI health check returned {health_check.status_code}")
        except requests.exceptions.ConnectionError:
            return jsonify({
                "error": f"FastAPI service is not running at {FASTAPI_URL}. Please start the FastAPI service first.",
                "fastapi_url": FASTAPI_URL,
                "accountStatus": {},
                "activeOrders": {},
                "closedOrders": {},
                "unrealizedPnL": 0,
                "realizedPnL": 0,
                "orderCounts": {"buyVolume": 0, "sellVolume": 0},
                "serverTime": datetime.now(timezone.utc).isoformat()
            }), 503
        except requests.exceptions.Timeout:
            # Se health check timeout, ainda tenta fazer as requisições principais
            print(f"[WARNING] FastAPI health check timeout, but continuing with requests")
        
        # Get account status
        try:
            status_response = requests.get(
                f"{FASTAPI_URL}/api/simplefx/status/{login_number}",
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
                f"{FASTAPI_URL}/api/simplefx/orders/active/{login_number}",
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
                f"{FASTAPI_URL}/api/simplefx/orders/closed/{login_number}",
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
        
        return jsonify({
            "accountStatus": status_data.get('data', {}),
            "activeOrders": active_data.get('data', {}),
            "closedOrders": closed_data.get('data', {}),
            "unrealizedPnL": unrealized_pnl,
            "realizedPnL": realized_pnl,
            "orderCounts": {
                "buyVolume": buy_volume,
                "sellVolume": sell_volume
            },
            "serverTime": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "accountStatus": {},
            "activeOrders": {},
            "closedOrders": {},
            "unrealizedPnL": 0,
            "realizedPnL": 0,
            "orderCounts": {"buyVolume": 0, "sellVolume": 0},
            "serverTime": datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/api/recent-db-orders/<login_number>')
def get_recent_db_orders(login_number):
    """Get recent orders from database"""
    try:
        db = get_db()
        orders = db.get_recent_orders(login_number, limit=100)
        
        # Converter timestamps para formato legível se necessário
        for order in orders:
            # Garantir que campos numéricos são números
            if 'open_time' in order and order['open_time']:
                try:
                    order['openTime'] = order['open_time']
                except:
                    pass
            if 'close_time' in order and order['close_time']:
                try:
                    order['closeTime'] = order['close_time']
                except:
                    pass
            # Mapear campos para formato esperado pelo frontend
            if 'open_price' in order:
                order['openPrice'] = order.get('open_price')
            if 'close_price' in order:
                order['closePrice'] = order.get('close_price')
            if 'take_profit' in order:
                order['takeProfit'] = order.get('take_profit')
            if 'stop_loss' in order:
                order['stopLoss'] = order.get('stop_loss')
        return jsonify(orders)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/webhook-outcomes/<login_number>')
def get_webhook_outcomes(login_number):
    """Get webhook outcomes"""
    try:
        db = get_db()
        outcomes = db.get_webhook_outcomes(login_number, limit=100)
        return jsonify(outcomes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/recent-logs')
def get_recent_logs():
    """Get recent logs"""
    try:
        account = request.args.get('account')
        db = get_db()
        logs = db.get_recent_logs(account=account, limit=50)
        # Format logs
        formatted_logs = [
            {
                "time": format_datetime(log.get('timestamp')),
                "message": log.get('message', '')
            }
            for log in logs
        ]
        return jsonify(formatted_logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/simplefx-chart-data')
def get_chart_data():
    """Get chart data - proxy to FastAPI"""
    try:
        symbol = request.args.get('symbol', 'EURUSD')
        timeframe = request.args.get('timeframe', '1h')
        account = request.args.get('account', '3028761')
        
        response = requests.get(
            f"{FASTAPI_URL}/api/simplefx/chart-data",
            params={
                "symbol": symbol,
                "timeframe": timeframe,
                "account": account
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify(data.get('data', []))
        else:
            # Return empty array instead of error to prevent frontend issues
            print(f"[WARNING] Chart data request failed: {response.status_code} - {response.text}")
            return jsonify([])
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to FastAPI at {FASTAPI_URL}")
        return jsonify([])
    except Exception as e:
        print(f"[ERROR] Error fetching chart data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])


def update_dashboard_clients():
    """Update all connected dashboard clients with quotes"""
    global last_dashboard_update
    import time
    now = time.time()
    
    # Only update if enough time has passed
    if now - last_dashboard_update < dashboard_update_interval:
        return
    
    try:
        # Get quotes for all symbols
        quotes = {
            'EURUSD': websocket_client.get_quote('EURUSD'),
            'US100': websocket_client.get_quote('US100'),
            'GBPUSD': websocket_client.get_quote('GBPUSD'),
            'connectionStatus': {
                'connected': websocket_client.is_connected(),
                'lastUpdate': int(time.time() * 1000)
            }
        }
        
        # Broadcast to all connected clients
        socketio.emit('quotes', quotes)
        last_dashboard_update = now
        
    except Exception as e:
        print(f"[ERROR] Dashboard update failed: {e}")
        socketio.emit('quotes', {
            'error': True,
            'message': 'WebSocket connection failed',
            'connectionStatus': {
                'connected': False
            }
        })


def start_websocket_background():
    """Start WebSocket client in background"""
    import time
    
    def run_websocket():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(websocket_client.connect())
    
    thread = threading.Thread(target=run_websocket, daemon=True)
    thread.start()
    print("[INFO] SimpleFX WebSocket client started in background")
    
    # Add callback for quote updates
    def on_quote_update(symbol, bid, ask, timestamp):
        """Callback when quote is updated"""
        quotes = {
            symbol: {
                'bid': bid,
                'ask': ask,
                'timestamp': timestamp
            },
            'connectionStatus': {
                'connected': websocket_client.is_connected(),
                'lastUpdate': timestamp
            }
        }
        socketio.emit('quotes', quotes)
    
    websocket_client.add_callback(on_quote_update)
    
    # Start periodic dashboard updates
    def periodic_update():
        while True:
            time.sleep(dashboard_update_interval)
            update_dashboard_clients()
    
    update_thread = threading.Thread(target=periodic_update, daemon=True)
    update_thread.start()


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    emit('connected', {'data': 'Connected to server'})
    # Send initial quotes
    update_dashboard_clients()


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')


if __name__ == '__main__':
    # Start WebSocket client
    start_websocket_background()
    # Run Flask app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

