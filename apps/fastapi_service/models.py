"""Pydantic models for FastAPI"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AccountStatusResponse(BaseModel):
    """Account status response"""
    data: Dict[str, Any]
    success: bool = True


class OrdersResponse(BaseModel):
    """Orders response"""
    data: Dict[str, Any]
    success: bool = True


class ChartDataResponse(BaseModel):
    """Chart data response"""
    data: List[Dict[str, Any]]
    success: bool = True


class TradeRequest(BaseModel):
    """Trade request model"""
    side: str
    amount: float
    login_number: str
    take_profit_price: float
    stop_loss_price: Optional[float] = None
    reality: str
    symbol: str = "EURUSD"
    use_secondary_api: bool = False


class TradeResponse(BaseModel):
    """Trade response"""
    data: Dict[str, Any]
    success: bool = True



