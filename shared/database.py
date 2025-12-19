"""Database access module for SQLite"""
import sqlite3
import os
import threading
from typing import List, Dict, Any, Optional
from shared.config import Config


class Database:
    """SQLite database wrapper with thread-safe connections"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.DATABASE_PATH
        # Use thread-local storage for connections
        self._local = threading.local()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            # Enable check_same_thread=False for Flask's multi-threaded environment
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def connect(self):
        """Connect to database (for compatibility)"""
        self._get_connection()
    
    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query"""
        conn = self._get_connection()
        return conn.execute(query, params)
    
    def commit(self):
        """Commit transaction"""
        conn = self._get_connection()
        conn.commit()
    
    def get_recent_orders(self, login_number: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent orders from database"""
        try:
            # Verificar conexão
            if not os.path.exists(self.db_path):
                print(f"[ERROR] Database file not found: {self.db_path}")
                return []
            
            # Verificar se a tabela existe
            cursor = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sfx_historical_orders'")
            if not cursor.fetchone():
                print(f"[ERROR] Table sfx_historical_orders does not exist")
                return []
            
            # Buscar login como string (SQLite converte automaticamente)
            # CAST garante que funciona mesmo se login for INTEGER ou TEXT
            query = """
                SELECT * FROM sfx_historical_orders
                WHERE CAST(login AS TEXT) = ?
                ORDER BY open_time DESC
                LIMIT ?
            """
            cursor = self.execute(query, (str(login_number), limit))
            rows = cursor.fetchall()
            
            # Convert Row objects to dicts and map fields for frontend
            result = []
            for row in rows:
                row_dict = {}
                for key in row.keys():
                    row_dict[key] = row[key]
                
                # Map database fields to frontend expected format
                # Frontend expects: openPrice, closePrice, takeProfit, stopLoss, openTime, closeTime
                # Database has: open_price, close_price, take_profit, stop_loss, open_time, close_time
                if 'open_price' in row_dict:
                    row_dict['openPrice'] = row_dict['open_price']
                if 'close_price' in row_dict:
                    row_dict['closePrice'] = row_dict['close_price']
                if 'take_profit' in row_dict:
                    row_dict['takeProfit'] = row_dict['take_profit']
                if 'stop_loss' in row_dict:
                    row_dict['stopLoss'] = row_dict['stop_loss']
                if 'open_time' in row_dict:
                    row_dict['openTime'] = row_dict['open_time']
                if 'close_time' in row_dict:
                    row_dict['closeTime'] = row_dict['close_time']
                if 'order_id' in row_dict:
                    row_dict['id'] = row_dict['order_id']
                
                result.append(row_dict)
            return result
        except Exception as e:
            print(f"[ERROR] Error getting recent orders: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_webhook_outcomes(self, login_number: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get webhook outcomes from database"""
        try:
            # Verificar se a tabela existe
            cursor = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='webhook_outcomes'")
            if not cursor.fetchone():
                return []
            
            query = """
                SELECT * FROM webhook_outcomes
                WHERE account_number = ?
                ORDER BY processed_at DESC
                LIMIT ?
            """
            cursor = self.execute(query, (str(login_number), limit))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                row_dict = {}
                for key in row.keys():
                    row_dict[key] = row[key]
                result.append(row_dict)
            return result
        except Exception as e:
            print(f"Error getting webhook outcomes: {e}")
            return []
    
    def get_recent_logs(self, account: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent logs from database"""
        try:
            # Verificar se a tabela existe
            cursor = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
            if not cursor.fetchone():
                # Tabela não existe, retornar vazio silenciosamente
                return []
            
            if account:
                query = """
                    SELECT * FROM logs
                    WHERE account = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                cursor = self.execute(query, (str(account), limit))
            else:
                query = """
                    SELECT * FROM logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                cursor = self.execute(query, (limit,))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                row_dict = {}
                for key in row.keys():
                    row_dict[key] = row[key]
                result.append(row_dict)
            return result
        except Exception as e:
            # Log apenas se for erro diferente de "table doesn't exist"
            if "no such table" not in str(e).lower():
                print(f"Error getting recent logs: {e}")
            return []
    
    def upsert_order(self, order_data: Dict[str, Any]) -> bool:
        """Insert or update an order in the database (equivalent to TypeScript upsertOrder)"""
        try:
            from shared.instrument_specs import get_instrument_specs
            import time
            
            # Calculate duration_in_minutes
            duration_in_minutes = None
            if (order_data.get('openTime') and order_data.get('closeTime') and
                order_data.get('openTime') > 0 and order_data.get('closeTime') > 0 and
                order_data.get('closeTime') > order_data.get('openTime')):
                duration_ms = order_data['closeTime'] - order_data['openTime']
                duration_in_minutes = int(round(duration_ms / 60000))
            
            # Get pip value
            symbol = order_data.get('symbol', 'EURUSD')
            instrument_specs = get_instrument_specs(symbol)
            pip_value = instrument_specs.get('pipValue', 0.0001)
            
            # Calculate TP and SL pips
            real_tp_pips = order_data.get('realTpPips')
            real_sl_pips = order_data.get('realSlPips')
            
            if not real_tp_pips and order_data.get('takeProfit') and order_data.get('openPrice'):
                real_tp_pips = abs(order_data['takeProfit'] - order_data['openPrice']) / pip_value
            
            if not real_sl_pips and order_data.get('stopLoss') and order_data.get('openPrice'):
                real_sl_pips = abs(order_data['stopLoss'] - order_data['openPrice']) / pip_value
            
            # Calculate diff_op_ob
            diff_op_ob = None
            if order_data.get('openPrice') and order_data.get('obReferencePrice'):
                diff_op_ob = abs(order_data['openPrice'] - order_data['obReferencePrice']) / pip_value
            
            # Prepare SQL with ON CONFLICT (SQLite UPSERT)
            sql = """
                INSERT INTO sfx_historical_orders (
                    order_id, login, symbol, side, volume, open_price, close_price, take_profit, stop_loss,
                    open_time, close_time, profit, swap, commission, reality, leverage, margin, margin_rate,
                    request_id, is_fifo, ob_reference_price, real_sl_pips, real_tp_pips, bid_at_open,
                    ask_at_open, spread_at_open, consider_ob_reference, max_size, duration_in_minutes, last_update_time,
                    alert_id, maxobalert, diff_op_ob, timeframe, exchange, findObType, filterFvgs, fvgDistance, lineHeight, filterFractal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    login = excluded.login,
                    symbol = excluded.symbol,
                    side = excluded.side,
                    volume = excluded.volume,
                    open_price = excluded.open_price,
                    close_price = COALESCE(excluded.close_price, sfx_historical_orders.close_price),
                    take_profit = COALESCE(excluded.take_profit, sfx_historical_orders.take_profit),
                    stop_loss = COALESCE(excluded.stop_loss, sfx_historical_orders.stop_loss),
                    open_time = excluded.open_time,
                    close_time = COALESCE(excluded.close_time, sfx_historical_orders.close_time),
                    profit = COALESCE(excluded.profit, sfx_historical_orders.profit),
                    swap = COALESCE(excluded.swap, sfx_historical_orders.swap),
                    commission = COALESCE(excluded.commission, sfx_historical_orders.commission),
                    reality = excluded.reality,
                    leverage = COALESCE(excluded.leverage, sfx_historical_orders.leverage),
                    margin = COALESCE(excluded.margin, sfx_historical_orders.margin),
                    margin_rate = COALESCE(excluded.margin_rate, sfx_historical_orders.margin_rate),
                    request_id = COALESCE(excluded.request_id, sfx_historical_orders.request_id),
                    is_fifo = COALESCE(excluded.is_fifo, sfx_historical_orders.is_fifo),
                    ob_reference_price = COALESCE(excluded.ob_reference_price, sfx_historical_orders.ob_reference_price),
                    real_sl_pips = COALESCE(excluded.real_sl_pips, sfx_historical_orders.real_sl_pips),
                    real_tp_pips = COALESCE(excluded.real_tp_pips, sfx_historical_orders.real_tp_pips),
                    bid_at_open = COALESCE(excluded.bid_at_open, sfx_historical_orders.bid_at_open),
                    ask_at_open = COALESCE(excluded.ask_at_open, sfx_historical_orders.ask_at_open),
                    spread_at_open = COALESCE(excluded.spread_at_open, sfx_historical_orders.spread_at_open),
                    consider_ob_reference = COALESCE(excluded.consider_ob_reference, sfx_historical_orders.consider_ob_reference),
                    max_size = COALESCE(excluded.max_size, sfx_historical_orders.max_size),
                    duration_in_minutes = COALESCE(excluded.duration_in_minutes, sfx_historical_orders.duration_in_minutes),
                    last_update_time = excluded.last_update_time,
                    alert_id = COALESCE(excluded.alert_id, sfx_historical_orders.alert_id),
                    maxobalert = COALESCE(excluded.maxobalert, sfx_historical_orders.maxobalert),
                    diff_op_ob = COALESCE(excluded.diff_op_ob, sfx_historical_orders.diff_op_ob),
                    timeframe = COALESCE(excluded.timeframe, sfx_historical_orders.timeframe),
                    exchange = COALESCE(excluded.exchange, sfx_historical_orders.exchange),
                    findObType = COALESCE(excluded.findObType, sfx_historical_orders.findObType),
                    filterFvgs = COALESCE(excluded.filterFvgs, sfx_historical_orders.filterFvgs),
                    fvgDistance = COALESCE(excluded.fvgDistance, sfx_historical_orders.fvgDistance),
                    lineHeight = COALESCE(excluded.lineHeight, sfx_historical_orders.lineHeight),
                    filterFractal = COALESCE(excluded.filterFractal, sfx_historical_orders.filterFractal)
            """
            
            params = (
                str(order_data.get('id', '')),
                str(order_data.get('login', '')),
                order_data.get('symbol', 'EURUSD'),
                order_data.get('side', 'BUY'),
                float(order_data.get('volume', 0)),
                float(order_data.get('openPrice', 0)) if order_data.get('openPrice') else None,
                float(order_data.get('closePrice', 0)) if order_data.get('closePrice') else None,
                float(order_data.get('takeProfit', 0)) if order_data.get('takeProfit') else None,
                float(order_data.get('stopLoss', 0)) if order_data.get('stopLoss') else None,
                int(order_data.get('openTime', 0)) if order_data.get('openTime') else None,
                int(order_data.get('closeTime', 0)) if order_data.get('closeTime') else None,
                float(order_data.get('profit', 0)) if order_data.get('profit') is not None else 0,
                float(order_data.get('swap', 0)) if order_data.get('swap') is not None else 0,
                float(order_data.get('commission', 0)) if order_data.get('commission') is not None else 0,
                order_data.get('reality', 'DEMO'),
                int(order_data.get('leverage', 0)) if order_data.get('leverage') else None,
                float(order_data.get('margin', 0)) if order_data.get('margin') else None,
                float(order_data.get('marginRate', 0)) if order_data.get('marginRate') else None,
                order_data.get('requestId', ''),
                int(order_data.get('isFIFO', 0)) if order_data.get('isFIFO') else 0,
                float(order_data.get('obReferencePrice', 0)) if order_data.get('obReferencePrice') else None,
                float(real_sl_pips) if real_sl_pips else None,
                float(real_tp_pips) if real_tp_pips else None,
                float(order_data.get('bidAtOpen', 0)) if order_data.get('bidAtOpen') else None,
                float(order_data.get('askAtOpen', 0)) if order_data.get('askAtOpen') else None,
                float(order_data.get('spreadAtOpen', 0)) if order_data.get('spreadAtOpen') else None,
                int(order_data.get('considerObReference', 0)) if order_data.get('considerObReference') else 0,
                float(order_data.get('maxSize', 0)) if order_data.get('maxSize') else None,
                duration_in_minutes,
                int(time.time() * 1000),  # last_update_time
                order_data.get('alertId'),
                int(order_data.get('maxobalert', 0)) if order_data.get('maxobalert') else None,
                float(diff_op_ob) if diff_op_ob else None,
                order_data.get('timeframe'),
                order_data.get('exchange', 'simplefx'),
                order_data.get('findObType'),
                int(order_data.get('filterFvgs', 0)) if order_data.get('filterFvgs') else 0,
                float(order_data.get('fvgDistance', 0)) if order_data.get('fvgDistance') else None,
                order_data.get('lineHeight'),
                order_data.get('filterFractal'),
            )
            
            cursor = self.execute(sql, params)
            self.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Error upserting order {order_data.get('id')}: {e}")
            import traceback
            traceback.print_exc()
            return False


    def get_account_settings(self, login_number: str) -> Dict[str, Any]:
        """Get account settings"""
        try:
            cursor = self.execute(
                "SELECT * FROM account_settings WHERE login = ?",
                (login_number,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            else:
                # Return defaults
                return {
                    'login': login_number,
                    'trading_mode': 'NORMAL',
                    'asia_session': 1,
                    'london_session': 1,
                    'new_york_session': 1,
                    'limbo_session': 1,
                    'exclusive_mode': 0
                }
        except Exception as e:
            print(f"[ERROR] Error getting account settings: {e}")
            return {
                'login': login_number,
                'trading_mode': 'NORMAL',
                'asia_session': 1,
                'london_session': 1,
                'new_york_session': 1,
                'limbo_session': 1,
                'exclusive_mode': 0
            }
    
    def order_exists_with_alert_id(self, alert_id: str, login_number: str) -> bool:
        """Check if order exists with alert ID"""
        try:
            cursor = self.execute(
                "SELECT 1 FROM sfx_historical_orders WHERE alert_id = ? AND login = ? LIMIT 1",
                (alert_id, login_number)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"[ERROR] Error checking order existence: {e}")
            return False
    
    def update_max_size(self, login_number: str, max_size: float):
        """Update max size for account"""
        try:
            self.execute(
                """UPDATE sfx_historical_orders 
                   SET max_size = ? 
                   WHERE login = ? AND (max_size IS NULL OR max_size != ?)""",
                (max_size, login_number, max_size)
            )
            self.commit()
        except Exception as e:
            print(f"[ERROR] Error updating max size: {e}")
    
    def get_orders(self, login_number: str) -> List[Dict[str, Any]]:
        """Get all orders for account"""
        try:
            cursor = self.execute(
                "SELECT * FROM sfx_historical_orders WHERE login = ? ORDER BY open_time DESC",
                (login_number,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[ERROR] Error getting orders: {e}")
            return []


# Global database instance
_db: Optional[Database] = None

def get_db() -> Database:
    """Get global database instance"""
    global _db
    if _db is None:
        _db = Database()
    return _db

