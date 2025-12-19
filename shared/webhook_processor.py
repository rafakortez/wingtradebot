"""Webhook processor for handling webhook data"""
import asyncio
import logging
from typing import Dict, Any, Optional
from shared.config import Config
from shared.simplefx_client import get_client
from shared.database import get_db
from shared.instrument_specs import get_instrument_specs
from shared.webhook_logger import get_webhook_logger
from shared.simplefx_websocket import get_websocket

logger = logging.getLogger(__name__)
webhook_logger = get_webhook_logger()

# Mutex for account-level locking
account_mutexes: Dict[str, asyncio.Lock] = {}

def get_mutex(login_number: str) -> asyncio.Lock:
    """Get mutex for account"""
    if login_number not in account_mutexes:
        account_mutexes[login_number] = asyncio.Lock()
    return account_mutexes[login_number]

async def process_webhook_data(alert_data: Dict[str, Any]):
    """Process webhook data - main processing function"""
    import time
    start_time = int(time.time() * 1000)
    symbol = "UNKNOWN"
    login = "UNKNOWN"
    action = "UNKNOWN"
    
    try:
        # Extract parameters
        raw_action = alert_data.get('a')
        take_profit = alert_data.get('t', 0)
        stop_loss = alert_data.get('s')
        login = alert_data.get('l') or Config.DEFAULT_ACCOUNT_NUMBER
        ob_reference = alert_data.get('o')
        consider_ob_reference = alert_data.get('u') == "1"
        size = alert_data.get('z', 0.01)
        max_size = alert_data.get('m', 0.01)
        reality = alert_data.get('r', 0)
        max_ob_candle_alert = alert_data.get('h')
        raw_symbol = alert_data.get('sy', 'EURUSD')
        timeframe = alert_data.get('tf')
        find_ob_type = alert_data.get('ft')
        filter_fvgs = alert_data.get('ff')
        fvg_distance = alert_data.get('fd')
        line_height = alert_data.get('lh')
        filter_fractal = alert_data.get('fr')
        import time
        alert_id = alert_data.get('id') or f"{int(time.time() * 1000)}_{hash(str(alert_data))}"
        alert_threshold = alert_data.get('th')
        
        action = raw_action or "UNKNOWN"
        
        # Parse symbol
        symbol = raw_symbol
        if ':' in symbol:
            symbol = symbol.split(':')[-1]
        symbol = symbol.upper().strip()
        
        # Validate
        if not login:
            webhook_logger.log_error("UNKNOWN", "UNKNOWN", "Missing login number", "UNKNOWN", alert_id, size)
            raise ValueError("Login number is required")
        
        if not symbol or symbol == "":
            webhook_logger.log_error(raw_symbol or "UNKNOWN", "UNKNOWN", f"Invalid symbol {raw_symbol}", login, alert_id, size)
            raise ValueError("Valid symbol is required")
        
        # Supported symbols
        supported_symbols = ["EURUSD", "GBPUSD", "US100", "US500"]
        if symbol not in supported_symbols:
            error_msg = f"Unsupported symbol: {symbol}. Supported: {', '.join(supported_symbols)}"
            webhook_logger.log_error(symbol, "UNKNOWN", error_msg, login, alert_id, size)
            raise ValueError(error_msg)
        
        # Get instrument specs
        instrument_specs = get_instrument_specs(symbol)
        
        # Validate pip values
        validation = validate_pip_values(take_profit, stop_loss, symbol, instrument_specs)
        if not validation['valid']:
            webhook_logger.log_order_rejected(symbol, action, validation['error'], login, alert_id, size)
            raise ValueError(validation['error'])
        
        # Convert TradingView pips
        converted = convert_trading_view_pips(take_profit, stop_loss, symbol, instrument_specs)
        
        # Get mutex for account
        mutex = get_mutex(login)
        
        async with mutex:
            # Get account settings
            db = get_db()
            account_settings = db.get_account_settings(login)
            trading_mode = account_settings.get('trading_mode', 'NORMAL')
            
            # Check exclusive mode
            if account_settings.get('exclusive_mode') == 1:
                total_orders = await get_total_open_orders_count(login)
                if total_orders > 0:
                    error_msg = f"Account {login} in Exclusive Mode and already has open trade"
                    webhook_logger.log_order_rejected(symbol, action, error_msg, login, alert_id, size)
                    raise ValueError(error_msg)
            
            # Check trading session
            current_session = get_current_trading_session()
            if current_session:
                session_key = f"{current_session}_session"
                if account_settings.get(session_key) != 1:
                    error_msg = f"{current_session.replace('_', ' ')} is disabled for account {login}"
                    webhook_logger.log_order_rejected(symbol, action, error_msg, login, alert_id, size)
                    raise ValueError(error_msg)
            
            # Check trading mode
            if trading_mode == "BUY_ONLY" and action != "B":
                error_msg = f"Account {login} is in BUY_ONLY mode"
                webhook_logger.log_order_rejected(symbol, action, error_msg, login, alert_id, size)
                raise ValueError(error_msg)
            
            if trading_mode == "SELL_ONLY" and action != "S":
                error_msg = f"Account {login} is in SELL_ONLY mode"
                webhook_logger.log_order_rejected(symbol, action, error_msg, login, alert_id, size)
                raise ValueError(error_msg)
            
            # Check duplicate
            if db.order_exists_with_alert_id(alert_id, login):
                error_msg = f"Alert ID {alert_id} already processed"
                webhook_logger.log_order_rejected(symbol, action, error_msg, login, alert_id, size)
                raise ValueError("Order already processed")
            
            # Check volume limits
            use_secondary = Config.should_use_secondary_api(login)
            total_volume = await get_total_open_volume(login)
            new_total = total_volume + size
            
            if new_total > max_size:
                error_msg = f"Max limit reached. Opened: {total_volume}, Attempted: {size}, Max: {max_size}"
                webhook_logger.log_order_rejected(symbol, action, error_msg, login, alert_id, size)
                raise ValueError("Max limit reached")
            
            # Check orders per side
            orders_same_side = await get_orders_count_by_side(login, action)
            if orders_same_side > 0:
                error_msg = f"Already have {orders_same_side} {action} order(s) open"
                webhook_logger.log_order_rejected(symbol, action, error_msg, login, alert_id, size)
                raise ValueError("Only one order per side allowed")
            
            # Get market data
            ws = get_websocket()
            quote = ws.get_quote(symbol)
            if not quote:
                # Wait a bit for quote
                await asyncio.sleep(0.5)
                quote = ws.get_quote(symbol)
            
            if not quote:
                error_msg = "No current market price available"
                webhook_logger.log_error(symbol, action, error_msg, login, alert_id, size)
                raise ValueError(error_msg)
            
            # Calculate stop loss
            market_price = quote['bid'] if action == "B" else quote['ask']
            sl_price = calculate_stop_loss(
                action, market_price, converted['stopLoss'],
                float(ob_reference) if ob_reference else None,
                consider_ob_reference, symbol
            )
            
            # Place trade
            client = get_client()
            reality_str = "LIVE" if Config.is_live_account(login) else "DEMO"
            
            trade_result = await client.place_trade(
                side='BUY' if action == 'B' else 'SELL',
                amount=size,
                login_number=login,
                take_profit_price=converted['takeProfit'],
                stop_loss_price=sl_price,
                reality=reality_str,
                symbol=symbol,
                use_secondary_api=use_secondary
            )
            
            # Handle different response formats
            if isinstance(trade_result, dict):
                if 'data' in trade_result:
                    orders = trade_result.get('data', {}).get('marketOrders', [])
                    if orders:
                        order = orders[0].get('order', orders[0])
                    else:
                        order = trade_result.get('data', {})
                else:
                    order = trade_result
            else:
                order = {}
            
            if not order or not order.get('id'):
                raise ValueError("No order returned from API")
            
            # Log success
            webhook_logger.log_order_placed(
                symbol, action, size, order.get('openPrice', 0),
                order.get('takeProfit', 0), order.get('stopLoss', 0),
                login, str(order.get('id', '')), alert_id
            )
            
            # Calculate real pip values
            real_tp_pips = abs(order.get('takeProfit', 0) - order.get('openPrice', 0)) / instrument_specs['pipValue']
            real_sl_pips = abs(order.get('stopLoss', 0) - order.get('openPrice', 0)) / instrument_specs['pipValue'] if order.get('stopLoss') else None
            
            # Prepare order data
            order_data = {
                'id': str(order.get('id', '')),
                'login': login,
                'symbol': symbol,
                'side': order.get('side', 'BUY'),
                'volume': order.get('volume', size),
                'openPrice': order.get('openPrice'),
                'closePrice': None,
                'takeProfit': order.get('takeProfit'),
                'stopLoss': order.get('stopLoss'),
                'openTime': order.get('openTime'),
                'closeTime': None,
                'profit': order.get('profit', 0),
                'swap': order.get('swaps', 0),
                'commission': order.get('commission', 0),
                'reality': reality_str,
                'leverage': order.get('leverage'),
                'margin': order.get('margin'),
                'marginRate': order.get('marginRate'),
                'requestId': order.get('requestId', ''),
                'isFIFO': order.get('isFIFO', False),
                'obReferencePrice': float(ob_reference) if ob_reference else None,
                'realSlPips': real_sl_pips,
                'realTpPips': real_tp_pips,
                'bidAtOpen': quote['bid'],
                'askAtOpen': quote['ask'],
                'spreadAtOpen': quote['ask'] - quote['bid'],
                'considerObReference': consider_ob_reference,
                'maxSize': max_size,
                'alertId': alert_id,
                'maxobalert': int(max_ob_candle_alert) if max_ob_candle_alert else None,
                'timeframe': timeframe,
                'exchange': 'simplefx',
                'findObType': find_ob_type,
                'filterFvgs': filter_fvgs == "1",
                'fvgDistance': float(fvg_distance) if fvg_distance else None,
                'lineHeight': line_height,
                'filterFractal': filter_fractal
            }
            
            # Upsert order
            db.upsert_order(order_data)
            db.update_max_size(login, max_size)
            
            import time
            logger.info(f"Webhook processed successfully for {symbol} in {int(time.time() * 1000) - start_time}ms")
            
    except Exception as e:
        error_msg = str(e)
        webhook_logger.log_error(symbol, action, error_msg, login, alert_id, size if 'size' in locals() else 0)
        raise


def validate_pip_values(take_profit: float, stop_loss: Optional[float], 
                        symbol: str, specs: Dict[str, Any]) -> Dict[str, Any]:
    """Validate pip values"""
    if not take_profit or take_profit <= 0:
        return {'valid': False, 'error': f"Invalid take profit: {take_profit}"}
    
    if stop_loss is not None and stop_loss <= 0:
        return {'valid': False, 'error': f"Invalid stop loss: {stop_loss}"}
    
    min_pips = 10 if symbol == "US100" else (10 if specs['type'] == 'index' else 5)
    
    if take_profit < min_pips:
        unit = "points" if specs['type'] == 'index' else "pips"
        return {'valid': False, 'error': f"Take profit too small. Minimum: {min_pips} {unit}"}
    
    if stop_loss and stop_loss < min_pips:
        unit = "points" if specs['type'] == 'index' else "pips"
        return {'valid': False, 'error': f"Stop loss too small. Minimum: {min_pips} {unit}"}
    
    return {'valid': True}


def convert_trading_view_pips(take_profit: float, stop_loss: Optional[float],
                              symbol: str, specs: Dict[str, Any]) -> Dict[str, float]:
    """Convert TradingView pips to actual values"""
    # For TradingView, pips are passed through directly
    return {
        'takeProfit': take_profit * specs['pipValue'],
        'stopLoss': stop_loss * specs['pipValue'] if stop_loss else None
    }


def calculate_stop_loss(action: str, market_price: float, stop_loss_pips: float,
                       ob_reference_price: Optional[float], consider_ob_reference: bool,
                       symbol: str) -> float:
    """Calculate stop loss price"""
    from shared.instrument_specs import get_instrument_specs
    specs = get_instrument_specs(symbol)
    pip_value = specs['pipValue']
    
    base_price = ob_reference_price if (consider_ob_reference and ob_reference_price) else market_price
    min_distance = 10 if symbol == "US100" else (5 if pip_value == 1 else 0.0002)
    
    if action == "B":
        raw_sl = base_price - (stop_loss_pips * pip_value)
        raw_sl = min(raw_sl, market_price - min_distance)
    else:
        raw_sl = base_price + (stop_loss_pips * pip_value)
        raw_sl = max(raw_sl, market_price + min_distance)
    
    decimals = 2 if pip_value == 1 else 5
    return round(raw_sl, decimals)


def get_current_trading_session() -> Optional[str]:
    """Get current trading session"""
    from datetime import datetime
    now = datetime.utcnow()
    hour = now.hour
    
    # Asia: 00:00-08:00 UTC
    if 0 <= hour < 8:
        return "asia"
    # London: 08:00-16:00 UTC
    elif 8 <= hour < 16:
        return "london"
    # New York: 16:00-00:00 UTC
    elif 16 <= hour < 24:
        return "new_york"
    return None


async def get_total_open_volume(login: str) -> float:
    """Get total open volume for account"""
    client = get_client()
    reality = "LIVE" if Config.is_live_account(login) else "DEMO"
    use_secondary = Config.should_use_secondary_api(login)
    
    active_data = await client.get_active_orders(login, reality, use_secondary, 1, 1000)
    orders = active_data.get('data', {}).get('marketOrders', [])
    return sum(o.get('volume', 0) for o in orders)


async def get_total_open_orders_count(login: str) -> int:
    """Get total open orders count"""
    client = get_client()
    reality = "LIVE" if Config.is_live_account(login) else "DEMO"
    use_secondary = Config.should_use_secondary_api(login)
    
    active_data = await client.get_active_orders(login, reality, use_secondary, 1, 1000)
    return len(active_data.get('data', {}).get('marketOrders', []))


async def get_orders_count_by_side(login: str, side: str) -> int:
    """Get orders count by side"""
    client = get_client()
    reality = "LIVE" if Config.is_live_account(login) else "DEMO"
    use_secondary = Config.should_use_secondary_api(login)
    
    active_data = await client.get_active_orders(login, reality, use_secondary, 1, 1000)
    orders = active_data.get('data', {}).get('marketOrders', [])
    
    normalized_side = "BUY" if side == "B" else "SELL"
    return len([o for o in orders if o.get('side', '').upper() == normalized_side])

