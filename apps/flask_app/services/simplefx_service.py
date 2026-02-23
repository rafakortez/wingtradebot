"""SimpleFX service for Flask app"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.simplefx_client import SimpleFXClient, get_client
from shared.config import Config
from typing import Dict, Any, Optional

class SimpleFXService:
    """Service for SimpleFX operations"""
    
    def __init__(self):
        self.client = get_client()
    
    async def get_account_status(self, login_number: str) -> Dict[str, Any]:
        """Get account status"""
        reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
        use_secondary = Config.should_use_secondary_api(login_number)
        return await self.client.get_account_status(login_number, reality, use_secondary)
    
    async def get_active_orders(self, login_number: str, page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """Get active orders"""
        reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
        use_secondary = Config.should_use_secondary_api(login_number)
        return await self.client.get_active_orders(login_number, reality, use_secondary, page, limit)
    
    async def get_closed_orders(self, login_number: str, page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """Get closed orders"""
        reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
        use_secondary = Config.should_use_secondary_api(login_number)
        return await self.client.get_closed_orders(login_number, reality, use_secondary, page, limit)
    
    async def place_trade(self, login_number: str, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place a trade"""
        reality = "LIVE" if Config.is_live_account(login_number) else "DEMO"
        use_secondary = Config.should_use_secondary_api(login_number)
        return await self.client.place_trade(login_number, reality, use_secondary, trade_data)
    
    async def get_chart_data(self, symbol: str, timeframe: str, account: str) -> Dict[str, Any]:
        """Get chart data"""
        return await self.client.get_chart_data(symbol, timeframe, account)



