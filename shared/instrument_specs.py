"""Instrument specifications for different trading symbols"""
from typing import Dict, Any


def get_instrument_specs(symbol: str) -> Dict[str, Any]:
    """Get instrument specifications for a symbol"""
    # Clean symbol from exchange prefix (e.g., "SIMPLEFX:US100" -> "US100")
    import re
    clean_symbol = re.sub(r"^[A-Z]+:", "", symbol).upper()
    
    forex_pairs = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", 
        "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"
    ]
    indices = [
        "US100", "US30", "NAS100", "SPX500", "GER40", 
        "UK100", "JPN225", "US500", "TECH100"
    ]
    
    if clean_symbol in indices:
        return {
            "type": "index",
            "pipValue": 1,
            "minDistance": 20,  # points
            "decimals": 1,
            "minTPDistance": 20,
            "minSLDistance": 20,
        }
    elif clean_symbol in forex_pairs:
        is_jpy_pair = "JPY" in clean_symbol
        return {
            "type": "forex",
            "pipValue": 0.01 if is_jpy_pair else 0.0001,
            "minDistance": 0.1 if is_jpy_pair else 0.001,  # 10 pips minimum
            "decimals": 3 if is_jpy_pair else 5,
            "minTPDistance": 10,
            "minSLDistance": 10,
        }
    else:
        # Default to forex
        return {
            "type": "forex",
            "pipValue": 0.0001,
            "minDistance": 0.001,
            "decimals": 5,
            "minTPDistance": 10,
            "minSLDistance": 10,
        }

