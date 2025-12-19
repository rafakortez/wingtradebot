"""SimpleFX API client for Python"""
import time
import httpx
import asyncio
import json
from typing import Optional, Dict, Any, List
from shared.config import Config

try:
    Config.validate_api_keys()
    api_info = Config.get_api_key_info()
    print(f"[CONFIG] Using API keys from: {api_info.get('source', 'shared/config.py')}")
    print(f"[CONFIG] Primary API Key: {api_info['SIMPLEFX_API_KEY']}")
    if api_info['SIMPLEFX_API_KEY2'] != "NOT SET":
        print(f"[CONFIG] Secondary API Key: {api_info['SIMPLEFX_API_KEY2']}")
except Exception as e:
    print(f"[CONFIG] Warning: Could not display API key info: {e}")

_global_auth_lock = asyncio.Lock()


class SimpleFXClient:
    """Client for SimpleFX API with token management"""
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.secondary_access_token: Optional[str] = None
        self.token_expiration: Optional[int] = None
        self.secondary_token_expiration: Optional[int] = None
        self.base_url = Config.SIMPLEFX_API_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_access_token(self, use_secondary_api: bool = False) -> str:
        """Get access token for SimpleFX API - PRIMARY API ONLY"""
        now = int(time.time() * 1000)
        
        if (self.access_token and 
            self.token_expiration and 
            now < self.token_expiration):
            return self.access_token
        
        async with _global_auth_lock:
            if (self.access_token and 
                self.token_expiration and 
                now < self.token_expiration):
                return self.access_token
            
            max_retries = 3
            base_delay = 10
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    print(f"[AUTH] Attempting authentication (attempt {attempt + 1}/{max_retries})...")
                    key_preview = Config.SIMPLEFX_API_KEY[:8] + "..." + Config.SIMPLEFX_API_KEY[-8:] if len(Config.SIMPLEFX_API_KEY) > 16 else "***"
                    secret_preview = Config.SIMPLEFX_API_SECRET[:8] + "..." + Config.SIMPLEFX_API_SECRET[-8:] if len(Config.SIMPLEFX_API_SECRET) > 16 else "***"
                    print(f"[AUTH] Using Key: {key_preview}, Secret: {secret_preview}")
                    
                    api_key = Config.SIMPLEFX_API_KEY
                    api_secret = Config.SIMPLEFX_API_SECRET
                    
                    print(f"[AUTH DEBUG] Key length: {len(api_key)} chars")
                    print(f"[AUTH DEBUG] Secret length: {len(api_secret)} chars")
                    print(f"[AUTH DEBUG] Key repr: {repr(api_key)}")
                    print(f"[AUTH DEBUG] Secret repr: {repr(api_secret)}")
                    print(f"[AUTH DEBUG] Key type: {type(api_key).__name__}")
                    print(f"[AUTH DEBUG] Secret type: {type(api_secret).__name__}")
                    
                    payload = {
                        "clientId": api_key,
                        "clientSecret": api_secret,
                    }
                    json_str = json.dumps(payload, ensure_ascii=False)
                    json_bytes = json_str.encode('utf-8')
                    print(f"[AUTH DEBUG] JSON payload: {json_str}")
                    print(f"[AUTH DEBUG] JSON bytes (UTF-8): {json_bytes}")
                    
                    response = await self.client.post(
                        f"{self.base_url}/auth/key",
                        json=payload,
                        headers={
                            "Content-Type": "application/json"
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    self.access_token = data.get("data", {}).get("token", "")
                    self.token_expiration = now + 3600000
                    print(f"[AUTH] Authentication successful, token expires in 1 hour")
                    return self.access_token
                except httpx.HTTPStatusError as e:
                    last_error = e
                    print(f"[AUTH VERBOSE] Full Error Response:")
                    print(f"[AUTH VERBOSE]   Status Code: {e.response.status_code}")
                    print(f"[AUTH VERBOSE]   Status Text: {e.response.reason_phrase}")
                    print(f"[AUTH VERBOSE]   Response Headers: {dict(e.response.headers)}")
                    try:
                        error_body = e.response.json()
                        print(f"[AUTH VERBOSE]   Response Body: {json.dumps(error_body, indent=2)}")
                        error_code = error_body.get('code', 'N/A')
                        error_message = error_body.get('message', 'N/A')
                        web_request_id = error_body.get('webRequestId', 'N/A')
                        print(f"[AUTH VERBOSE]   Error Code: {error_code}")
                        print(f"[AUTH VERBOSE]   Error Message: {error_message}")
                        print(f"[AUTH VERBOSE]   Web Request ID: {web_request_id}")
                        error_detail = f" - {error_message}"
                    except Exception as parse_error:
                        try:
                            error_text = e.response.text
                            print(f"[AUTH VERBOSE]   Response Text (not JSON): {error_text}")
                            error_detail = ""
                        except:
                            print(f"[AUTH VERBOSE]   Could not parse response: {parse_error}")
                            error_detail = ""
                    
                    if e.response.status_code == 409:
                        if attempt < max_retries - 1:
                            wait_time = base_delay * (attempt + 1)
                            print(f"[AUTH] 409 Conflict{error_detail}")
                            if "INVALID_CREDENTIALS" in error_detail or "AUTHENTICATION_INVALID_CREDENTIALS" in error_detail:
                                print(f"[AUTH] Error 1501: AUTHENTICATION_INVALID_CREDENTIALS")
                                print(f"[AUTH] This could mean:")
                                print(f"[AUTH]   1. IP address not whitelisted (check SimpleFX API settings)")
                                print(f"[AUTH]   2. API key not activated/enabled")
                                print(f"[AUTH]   3. API key expired or revoked")
                                print(f"[AUTH]   4. Wrong environment (check if key is for DEMO vs LIVE)")
                                print(f"[AUTH]   5. 2FA enabled (may need special configuration)")
                                print(f"[AUTH] Verify in SimpleFX dashboard: API Settings → Check IP whitelist and key status")
                                raise
                            else:
                                print(f"[AUTH] Active session exists - waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                                print(f"[AUTH] NOTE: If TypeScript service is running, stop it or wait for its session to expire")
                                await asyncio.sleep(wait_time)
                                continue
                        else:
                            print(f"[AUTH] ERROR: Failed to authenticate after {max_retries} attempts")
                            print(f"[AUTH] Error details: {error_detail}")
                            if "INVALID_CREDENTIALS" in error_detail or "AUTHENTICATION_INVALID_CREDENTIALS" in error_detail:
                                print(f"[AUTH]")
                                print(f"[AUTH] SOLUTION: Your API keys appear to be INVALID")
                                print(f"[AUTH] 1. Verify keys in shared/config.py match SimpleFX website exactly")
                                print(f"[AUTH] 2. Check if keys are active/enabled in SimpleFX dashboard")
                                print(f"[AUTH] 3. Ensure no typos or extra spaces in API key or secret")
                                print(f"[AUTH] 4. Try generating new API keys from SimpleFX if needed")
                            else:
                                print(f"[AUTH] 409 Conflict persists - there's likely another service using the same API key")
                                print(f"[AUTH] SOLUTION: Stop any TypeScript/Node.js services, or wait 1 hour for session to expire")
                    print(f"[AUTH] Authentication failed: {e.response.status_code} - {e}")
                    raise
                except Exception as e:
                    last_error = e
                    print(f"[AUTH] Authentication error: {e}")
                    raise
            
            if last_error:
                raise last_error
            return self.access_token or ""
    
    def clear_access_tokens(self, clear_secondary: bool = True):
        """Clear cached access tokens"""
        self.access_token = None
        self.token_expiration = None
        if clear_secondary:
            self.secondary_access_token = None
            self.secondary_token_expiration = None
    
    async def get_account_status(
        self, 
        login_number: str, 
        reality: str, 
        use_secondary_api: bool = False
    ) -> Dict[str, Any]:
        """Get account status"""
        try:
            token = await self.get_access_token(False)
            response = await self.client.get(
                f"{self.base_url}/accounts/{reality}/{login_number}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self.clear_access_tokens(False)
                token = await self.get_access_token(False)
                response = await self.client.get(
                    f"{self.base_url}/accounts/{reality}/{login_number}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }
                )
                response.raise_for_status()
                return response.json()
            raise
    
    async def get_active_orders(
        self,
        login_number: str,
        reality: str,
        use_secondary_api: bool = False,
        page: int = 1,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get active orders for a trading account"""
        try:
            token = await self.get_access_token(False)
            response = await self.client.post(
                f"{self.base_url}/trading/orders/active",
                json={
                    "login": int(login_number),
                    "reality": reality,
                    "page": page,
                    "limit": limit,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            data = response.json()
            if "data" in data and "marketOrders" not in data["data"]:
                data["data"]["marketOrders"] = []
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self.clear_access_tokens(False)
                token = await self.get_access_token(False)
                response = await self.client.post(
                    f"{self.base_url}/trading/orders/active",
                    json={
                        "login": int(login_number),
                        "reality": reality,
                        "page": page,
                        "limit": limit,
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }
                )
                response.raise_for_status()
                data = response.json()
                if "data" in data and "marketOrders" not in data["data"]:
                    data["data"]["marketOrders"] = []
                return data
            raise
    
    async def get_closed_orders(
        self,
        login_number: str,
        reality: str,
        use_secondary_api: bool = False,
        page: int = 1,
        limit: int = 100,
        time_from: Optional[int] = None,
        time_to: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get closed orders for a trading account - PRIMARY API ONLY"""
        import time as time_module
        
        now = int(time_module.time() * 1000)
        if time_from is None:
            time_from = now - (180 * 24 * 60 * 60 * 1000)
        if time_to is None:
            time_to = now
        
        try:
            token = await self.get_access_token(False)
            response = await self.client.post(
                f"{self.base_url}/trading/orders/history",
                json={
                    "login": int(login_number),
                    "reality": reality,
                    "timeFrom": time_from,
                    "timeTo": time_to,
                    "page": page,
                    "limit": limit,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            data = response.json()
            if "data" in data and "marketOrders" not in data["data"]:
                data["data"]["marketOrders"] = []
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self.clear_access_tokens(False)
                token = await self.get_access_token(False)
                response = await self.client.post(
                    f"{self.base_url}/trading/orders/history",
                    json={
                        "login": int(login_number),
                        "reality": reality,
                        "timeFrom": time_from,
                        "timeTo": time_to,
                        "page": page,
                        "limit": limit,
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }
                )
                response.raise_for_status()
                data = response.json()
                if "data" in data and "marketOrders" not in data["data"]:
                    data["data"]["marketOrders"] = []
                return data
            raise
    
    async def get_chart_data(
        self,
        symbol: str,
        timeframe: str,
        login_number: str,
        time_from: Optional[int] = None,
        time_to: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get chart data (candles) for a symbol - PRIMARY API ONLY"""
        import time as time_module
        
        token = await self.get_access_token(False)
        
        timeframe_map = {
            "1m": "M1",
            "5m": "M5",
            "15m": "M15",
            "1h": "H1",
            "4h": "H4",
            "1d": "D1",
        }
        sfx_timeframe = timeframe_map.get(timeframe, "H1")
        
        now = int(time_module.time() * 1000)
        if time_from is None:
            timeframe_ms = {
                "1m": 60 * 1000,
                "5m": 5 * 60 * 1000,
                "15m": 15 * 60 * 1000,
                "1h": 60 * 60 * 1000,
                "4h": 4 * 60 * 60 * 1000,
                "1d": 24 * 60 * 60 * 1000,
            }.get(timeframe, 60 * 60 * 1000)
            time_from = now - (timeframe_ms * 200)
        if time_to is None:
            time_to = now
        
        try:
            response = await self.client.get(
                f"{self.base_url}/market/candles/{symbol}/{sfx_timeframe}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                params={
                    "from": int(time_from / 1000),
                    "to": int(time_to / 1000),
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data and "data" in data and "candles" in data["data"]:
                candles = data["data"]["candles"]
                return [
                    {
                        "time": candle["timestamp"],
                        "open": float(f"{candle['open']:.5f}"),
                        "high": float(f"{candle['high']:.5f}"),
                        "low": float(f"{candle['low']:.5f}"),
                        "close": float(f"{candle['close']:.5f}"),
                    }
                    for candle in candles
                ]
            return []
        except Exception as e:
            print(f"Error fetching chart data: {e}")
            return []
    
    async def place_trade(
        self,
        side: str,
        amount: float,
        login_number: str,
        take_profit_price: float,
        stop_loss_price: Optional[float],
        reality: str,
        symbol: str = "EURUSD",
        use_secondary_api: bool = False,
    ) -> Dict[str, Any]:
        """Place a trade via SimpleFX API"""
        from shared.instrument_specs import get_instrument_specs
        
        instrument_specs = get_instrument_specs(symbol)
        
        min_lot_size = 0.1 if instrument_specs["type"] == "index" else 0.01
        if amount < min_lot_size:
            raise ValueError(f"Volume {amount} is below minimum {min_lot_size} for {symbol}")
        
        def format_price(price: float) -> float:
            if instrument_specs["type"] == "index":
                return round(price * 10) / 10
            return float(f"{price:.{instrument_specs['decimals']}f}")
        
        request_body = {
            "Reality": reality.upper(),
            "Login": int(login_number),
            "Symbol": symbol,
            "Side": "BUY" if side.upper() in ["B", "BUY"] else "SELL",
            "Volume": amount,
            "TakeProfit": format_price(take_profit_price),
            "StopLoss": format_price(stop_loss_price) if stop_loss_price else None,
            "IsFIFO": False,
            "RequestId": f"TV_{int(time.time() * 1000)}",
            "Activity": "TradingView Webhook Order",
        }
        
        try:
            token = await self.get_access_token(False)
            response = await self.client.post(
                f"{self.base_url}/trading/orders/market",
                json=request_body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("data", {}).get("marketOrders"):
                raise ValueError("Invalid API response: No market orders returned")
            
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self.clear_access_tokens(False)
                token = await self.get_access_token(False)
                response = await self.client.post(
                    f"{self.base_url}/trading/orders/market",
                    json=request_body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }
                )
                response.raise_for_status()
                data = response.json()
                if not data.get("data", {}).get("marketOrders"):
                    raise ValueError("Invalid API response: No market orders returned")
                return data
            raise
    
    async def close_all_positions(
        self,
        login_number: str,
        reality: str,
        use_secondary_api: bool = False,
    ) -> Dict[str, Any]:
        """Close all positions for a trading account - PRIMARY API ONLY"""
        try:
            token = await self.get_access_token(False)
            response = await self.client.post(
                f"{self.base_url}/trading/orders/close-all",
                json={
                    "login": int(login_number),
                    "reality": reality,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self.clear_access_tokens(False)
                token = await self.get_access_token(False)
                response = await self.client.post(
                    f"{self.base_url}/trading/orders/close-all",
                    json={
                        "login": int(login_number),
                        "reality": reality,
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }
                )
                response.raise_for_status()
                return response.json()
            raise
    
    async def get_deposit_history(
        self,
        login_number: str,
        reality: str,
        use_secondary_api: bool = False,
    ) -> Dict[str, Any]:
        """Get deposit history for a trading account - PRIMARY API ONLY"""
        try:
            token = await self.get_access_token(False)
            response = await self.client.get(
                f"{self.base_url}/accounts/{reality}/{login_number}/deposits",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self.clear_access_tokens(False)
                token = await self.get_access_token(False)
                response = await self.client.get(
                    f"{self.base_url}/accounts/{reality}/{login_number}/deposits",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }
                )
                response.raise_for_status()
                return response.json()
            raise
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

_client: Optional[SimpleFXClient] = None

def get_client() -> SimpleFXClient:
    """Get global SimpleFX client instance"""
    global _client
    if _client is None:
        _client = SimpleFXClient()
    return _client


