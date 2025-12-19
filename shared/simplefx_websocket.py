"""SimpleFX WebSocket client for real-time quotes"""
import asyncio
import json
import time
from typing import Dict, Optional, Callable, Set
from websockets.client import connect
from websockets.exceptions import ConnectionClosed, WebSocketException
import logging

logger = logging.getLogger(__name__)

class SimpleFXWebSocket:
    """WebSocket client for SimpleFX quotes"""
    
    WS_URL = "wss://web-quotes-core.simplefx.com/websocket/quotes"
    
    def __init__(self):
        self.ws = None
        self.request_id = 0
        self.subscribed_symbols: Set[str] = set()
        self.quotes: Dict[str, Dict] = {}
        self.last_quote: Optional[Dict] = None
        self.connected = False
        self.callbacks: list[Callable] = []
        self._reconnect_task = None
        self._running = False
        
    def get_next_request_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    async def connect(self):
        """Connect to SimpleFX WebSocket"""
        if self._running:
            return
            
        self._running = True
        await self._connect_loop()
    
    async def _connect_loop(self):
        """Connection loop with reconnection"""
        while self._running:
            try:
                logger.info(f"Connecting to SimpleFX WebSocket: {self.WS_URL}")
                async with connect(self.WS_URL) as websocket:
                    self.ws = websocket
                    self.connected = True
                    logger.info("WebSocket connected to SimpleFX")
                    
                    # Subscribe to default symbols
                    await self.subscribe_to_symbol("EURUSD")
                    await self.subscribe_to_symbol("US100")
                    await self.subscribe_to_symbol("GBPUSD")
                    
                    # Listen for messages
                    async for message in websocket:
                        await self._handle_message(message)
                        
            except (ConnectionClosed, WebSocketException) as e:
                logger.warning(f"WebSocket connection lost: {e}. Reconnecting in 5s...")
                self.connected = False
                if self._running:
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.connected = False
                if self._running:
                    await asyncio.sleep(5)
    
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            path = data.get('p', '')
            
            if path == '/quotes/subscribed' or path == '/lastprices/list':
                if 'd' in data and len(data['d']) > 0:
                    quote = data['d'][0]
                    symbol = quote.get('s')
                    if symbol:
                        self.quotes[symbol] = {
                            'bid': quote.get('b'),
                            'ask': quote.get('a'),
                            'timestamp': quote.get('t', int(time.time() * 1000))
                        }
                        self.last_quote = self.quotes[symbol]
                        
                        # Notify callbacks
                        for callback in self.callbacks:
                            try:
                                # Callbacks can be sync or async
                                result = callback(symbol, quote.get('b'), quote.get('a'), quote.get('t'))
                                if asyncio.iscoroutine(result):
                                    # Schedule async callback
                                    asyncio.create_task(result)
                            except Exception as e:
                                logger.error(f"Error in callback: {e}")
                                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def subscribe_to_symbol(self, symbol: str):
        """Subscribe to a symbol"""
        if symbol in self.subscribed_symbols:
            return
            
        if not self.ws or not self.connected:
            logger.warning(f"Cannot subscribe to {symbol}: not connected")
            return
        
        try:
            request = {
                'p': '/subscribe/addList',
                'i': self.get_next_request_id(),
                'd': [symbol]
            }
            await self.ws.send(json.dumps(request))
            self.subscribed_symbols.add(symbol)
            logger.info(f"Subscribed to {symbol}")
            
            # Request last known price
            last_price_request = {
                'p': '/lastprices/list',
                'i': self.get_next_request_id(),
                'd': [symbol]
            }
            await self.ws.send(json.dumps(last_price_request))
        except Exception as e:
            logger.error(f"Error subscribing to {symbol}: {e}")
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get latest quote for a symbol"""
        return self.quotes.get(symbol)
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.connected and self.ws is not None
    
    def add_callback(self, callback: Callable):
        """Add callback for quote updates"""
        self.callbacks.append(callback)
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        self._running = False
        self.connected = False
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None
        logger.info("WebSocket disconnected")


# Global instance
_websocket_instance: Optional[SimpleFXWebSocket] = None

def get_websocket() -> SimpleFXWebSocket:
    """Get global WebSocket instance"""
    global _websocket_instance
    if _websocket_instance is None:
        _websocket_instance = SimpleFXWebSocket()
    return _websocket_instance

