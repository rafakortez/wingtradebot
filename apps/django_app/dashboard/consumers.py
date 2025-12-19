"""WebSocket consumers for dashboard"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from shared.simplefx_websocket import get_websocket


class DashboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time dashboard updates with SimpleFX quotes"""
    
    async def connect(self):
        await self.accept()
        self.websocket_client = get_websocket()
        
        # Add callback for quote updates
        def on_quote_update(symbol, bid, ask, timestamp):
            asyncio.create_task(self.send_quote_update(symbol, bid, ask, timestamp))
        
        self.websocket_client.add_callback(on_quote_update)
        
        # Ensure WebSocket client is connected
        if not self.websocket_client.is_connected():
            asyncio.create_task(self.websocket_client.connect())
        
        # Send initial connection message
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'Connected to Django Channels',
            'quotes': {
                'EURUSD': self.websocket_client.get_quote('EURUSD'),
                'US100': self.websocket_client.get_quote('US100'),
                'GBPUSD': self.websocket_client.get_quote('GBPUSD'),
                'connectionStatus': {
                    'connected': self.websocket_client.is_connected()
                }
            }
        }))
        
        # Start periodic updates
        self.update_task = asyncio.create_task(self.periodic_updates())
    
    async def disconnect(self, close_code):
        if hasattr(self, 'update_task'):
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'subscribe':
                symbol = text_data_json.get('symbol')
                if symbol:
                    await self.websocket_client.subscribe_to_symbol(symbol)
                    await self.send(text_data=json.dumps({
                        'type': 'subscribed',
                        'symbol': symbol
                    }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def send_quote_update(self, symbol, bid, ask, timestamp):
        """Send quote update to client"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'quotes',
                symbol: {
                    'bid': bid,
                    'ask': ask,
                    'timestamp': timestamp
                },
                'connectionStatus': {
                    'connected': self.websocket_client.is_connected(),
                    'lastUpdate': timestamp
                }
            }))
        except Exception as e:
            print(f"[ERROR] Failed to send quote update: {e}")
    
    async def periodic_updates(self):
        """Send periodic quote updates"""
        while True:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                quotes = {
                    'EURUSD': self.websocket_client.get_quote('EURUSD'),
                    'US100': self.websocket_client.get_quote('US100'),
                    'GBPUSD': self.websocket_client.get_quote('GBPUSD'),
                    'connectionStatus': {
                        'connected': self.websocket_client.is_connected(),
                        'lastUpdate': int(asyncio.get_event_loop().time() * 1000)
                    }
                }
                
                await self.send(text_data=json.dumps({
                    'type': 'quotes',
                    **quotes
                }))
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[ERROR] Periodic update error: {e}")
                await asyncio.sleep(10)

