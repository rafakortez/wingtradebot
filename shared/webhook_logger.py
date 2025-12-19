"""Webhook logger for consistent logging"""
import logging
from typing import Optional
from shared.database import get_db

logger = logging.getLogger(__name__)

class WebhookLogger:
    """Centralized webhook logging"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def log_webhook_received(self, symbol: str, action: str, size: float, 
                            tp: float, sl: float, account: str, alert_id: str):
        """Log webhook received"""
        message = f"WEBHOOK: {symbol} {action} {size} TP:{tp} SL:{sl} | Acc:{account} | ID:{alert_id}"
        logger.info(message)
        self._store_outcome(account, alert_id, "RECEIVED", message, symbol, action, size)
    
    def log_order_placed(self, symbol: str, action: str, size: float, 
                        open_price: float, tp: float, sl: float,
                        account: str, order_id: str, alert_id: str):
        """Log order placed"""
        message = f"ORDER PLACED: {symbol} {action} {size} @ {open_price} TP:{tp} SL:{sl} | Acc:{account} | OrderID:{order_id} | AlertID:{alert_id}"
        logger.info(message)
        self._store_outcome(account, alert_id, "PLACED", message, symbol, action, size, order_id)
    
    def log_order_rejected(self, symbol: str, action: str, reason: str, 
                          account: str, alert_id: str, size: float):
        """Log order rejected"""
        message = f"ORDER REJECTED: {symbol} {action} {size} | Acc:{account} | Reason: {reason} | AlertID:{alert_id}"
        logger.warning(message)
        self._store_outcome(account, alert_id, "REJECTED", message, symbol, action, size)
    
    def log_error(self, symbol: str, action: str, error: str, 
                 account: str, alert_id: str, size: float):
        """Log error"""
        message = f"ERROR: {symbol} {action} {size} | Acc:{account} | Error: {error} | AlertID:{alert_id}"
        logger.error(message)
        self._store_outcome(account, alert_id, "ERROR", message, symbol, action, size)
    
    def log_duplicate(self, symbol: str, action: str, account: str, 
                     alert_id: str, size: float):
        """Log duplicate"""
        message = f"DUPLICATE: {symbol} {action} {size} | Acc:{account} | AlertID:{alert_id}"
        logger.info(message)
        self._store_outcome(account, alert_id, "DUPLICATE", message, symbol, action, size)
    
    def _store_outcome(self, account: str, alert_id: str, status: str, 
                      message: str, symbol: str, action: str, size: float,
                      order_id: Optional[str] = None):
        """Store webhook outcome in database"""
        try:
            import time
            db = get_db()
            db.execute(
                """INSERT INTO webhook_outcomes 
                   (account_number, alert_id, status, message, symbol, action, size, order_id, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (account, alert_id, status, message, symbol, action, size, order_id, int(time.time() * 1000))
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to store webhook outcome: {e}")


# Global instance
_webhook_logger: Optional[WebhookLogger] = None

def get_webhook_logger() -> WebhookLogger:
    """Get global webhook logger instance"""
    global _webhook_logger
    if _webhook_logger is None:
        _webhook_logger = WebhookLogger()
    return _webhook_logger


