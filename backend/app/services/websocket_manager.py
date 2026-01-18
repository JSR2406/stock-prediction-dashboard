"""
WebSocket Manager for Real-time Price Updates
Handles multiple client connections and broadcasts price updates.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
import random

logger = logging.getLogger(__name__)


@dataclass
class PriceUpdate:
    """Price update message."""
    type: str = "price_update"
    symbol: str = ""
    price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    high: float = 0.0
    low: float = 0.0
    volume: int = 0
    timestamp: str = ""


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts real-time price updates.
    
    Usage:
        manager = WebSocketManager()
        await manager.connect(websocket, client_id)
        await manager.subscribe(client_id, ["RELIANCE", "TCS"])
        await manager.broadcast_price_update("RELIANCE", price_data)
    """
    
    MAX_SUBSCRIPTIONS_PER_CLIENT = 20
    PRICE_UPDATE_INTERVAL = 30  # seconds
    
    def __init__(self):
        # client_id -> websocket
        self.active_connections: Dict[str, any] = {}
        
        # client_id -> set of subscribed symbols
        self.subscriptions: Dict[str, Set[str]] = {}
        
        # symbol -> set of client_ids subscribed
        self.symbol_subscribers: Dict[str, Set[str]] = {}
        
        # Cache for latest prices
        self.price_cache: Dict[str, PriceUpdate] = {}
        
        # Task for price streaming
        self._stream_task: Optional[asyncio.Task] = None
        
    async def connect(self, websocket, client_id: str):
        """
        Handle new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket instance
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()
        
        logger.info(f"WebSocket connected: {client_id}")
        
        # Send welcome message
        await self.send_to_client(client_id, {
            "type": "connected",
            "client_id": client_id,
            "message": "Connected to StockAI real-time feed",
            "max_subscriptions": self.MAX_SUBSCRIPTIONS_PER_CLIENT
        })
    
    def disconnect(self, client_id: str):
        """
        Handle WebSocket disconnection.
        
        Args:
            client_id: Client to disconnect
        """
        # Remove from all symbol subscriptions
        if client_id in self.subscriptions:
            for symbol in self.subscriptions[client_id]:
                if symbol in self.symbol_subscribers:
                    self.symbol_subscribers[symbol].discard(client_id)
            
            del self.subscriptions[client_id]
        
        # Remove connection
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        logger.info(f"WebSocket disconnected: {client_id}")
    
    async def subscribe(self, client_id: str, symbols: List[str]) -> Dict:
        """
        Subscribe client to stock symbols.
        
        Args:
            client_id: Client identifier
            symbols: List of symbols to subscribe to
            
        Returns:
            Dict with subscription result
        """
        if client_id not in self.subscriptions:
            return {"success": False, "error": "Client not connected"}
        
        # Validate symbols count
        current_count = len(self.subscriptions[client_id])
        new_symbols = [s.upper() for s in symbols if s.upper() not in self.subscriptions[client_id]]
        
        if current_count + len(new_symbols) > self.MAX_SUBSCRIPTIONS_PER_CLIENT:
            return {
                "success": False,
                "error": f"Maximum {self.MAX_SUBSCRIPTIONS_PER_CLIENT} subscriptions allowed"
            }
        
        # Add subscriptions
        subscribed = []
        for symbol in new_symbols:
            symbol = symbol.upper()
            self.subscriptions[client_id].add(symbol)
            
            if symbol not in self.symbol_subscribers:
                self.symbol_subscribers[symbol] = set()
            self.symbol_subscribers[symbol].add(client_id)
            
            subscribed.append(symbol)
            
            # Send current price if cached
            if symbol in self.price_cache:
                await self.send_to_client(client_id, asdict(self.price_cache[symbol]))
        
        logger.info(f"Client {client_id} subscribed to: {subscribed}")
        
        return {
            "success": True,
            "subscribed": subscribed,
            "total_subscriptions": len(self.subscriptions[client_id])
        }
    
    async def unsubscribe(self, client_id: str, symbols: List[str]) -> Dict:
        """
        Unsubscribe client from stock symbols.
        
        Args:
            client_id: Client identifier
            symbols: List of symbols to unsubscribe from
        """
        if client_id not in self.subscriptions:
            return {"success": False, "error": "Client not connected"}
        
        unsubscribed = []
        for symbol in symbols:
            symbol = symbol.upper()
            
            if symbol in self.subscriptions[client_id]:
                self.subscriptions[client_id].discard(symbol)
                
                if symbol in self.symbol_subscribers:
                    self.symbol_subscribers[symbol].discard(client_id)
                
                unsubscribed.append(symbol)
        
        return {
            "success": True,
            "unsubscribed": unsubscribed,
            "total_subscriptions": len(self.subscriptions[client_id])
        }
    
    async def broadcast_price_update(self, symbol: str, price_data: Dict):
        """
        Broadcast price update to all subscribers.
        
        Args:
            symbol: Stock symbol
            price_data: Price information
        """
        symbol = symbol.upper()
        
        if symbol not in self.symbol_subscribers:
            return
        
        # Create update message
        update = PriceUpdate(
            type="price_update",
            symbol=symbol,
            price=price_data.get('price', 0),
            change=price_data.get('change', 0),
            change_percent=price_data.get('change_percent', 0),
            high=price_data.get('high', 0),
            low=price_data.get('low', 0),
            volume=price_data.get('volume', 0),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        # Cache the update
        self.price_cache[symbol] = update
        
        # Send to all subscribers
        message = asdict(update)
        disconnected = []
        
        for client_id in self.symbol_subscribers[symbol]:
            try:
                await self.send_to_client(client_id, message)
            except Exception as e:
                logger.warning(f"Failed to send to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def send_to_client(self, client_id: str, message: Dict):
        """Send message to specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)
    
    async def start_price_stream(self):
        """
        Start background task to stream price updates.
        In production, this would fetch from real data sources.
        """
        logger.info("Starting price stream...")
        
        while True:
            try:
                # Get all subscribed symbols
                all_symbols = set()
                for symbols in self.subscriptions.values():
                    all_symbols.update(symbols)
                
                # Generate mock price updates
                # In production: fetch from Yahoo Finance, data provider, etc.
                for symbol in all_symbols:
                    # Demo price (would be real data in production)
                    base_price = self._get_base_price(symbol)
                    change = (random.random() - 0.5) * base_price * 0.01
                    
                    price_data = {
                        'price': base_price + change,
                        'change': change,
                        'change_percent': (change / base_price) * 100,
                        'high': base_price * 1.02,
                        'low': base_price * 0.98,
                        'volume': random.randint(100000, 5000000)
                    }
                    
                    await self.broadcast_price_update(symbol, price_data)
                
                # Wait before next update
                await asyncio.sleep(self.PRICE_UPDATE_INTERVAL)
                
            except asyncio.CancelledError:
                logger.info("Price stream stopped")
                break
            except Exception as e:
                logger.error(f"Price stream error: {e}")
                await asyncio.sleep(5)
    
    def _get_base_price(self, symbol: str) -> float:
        """Get base price for a symbol (demo data)."""
        prices = {
            'RELIANCE': 2456.30,
            'TCS': 3892.45,
            'HDFCBANK': 1654.20,
            'INFY': 1567.80,
            'ICICIBANK': 1023.45,
            'SBIN': 628.90,
            'BHARTIARTL': 1245.60,
            'ITC': 456.75,
            'KOTAKBANK': 1789.50,
            'LT': 2345.60,
            'WIPRO': 485.20,
            'TATAMOTORS': 987.60,
            'ADANIENT': 2856.45,
            'SUNPHARMA': 1234.80,
        }
        return prices.get(symbol, 1000 + random.random() * 1500)
    
    async def handle_message(self, client_id: str, message: Dict):
        """
        Handle incoming WebSocket message.
        
        Args:
            client_id: Client identifier
            message: Parsed message dict
        """
        msg_type = message.get('type')
        
        if msg_type == 'subscribe':
            symbols = message.get('symbols', [])
            result = await self.subscribe(client_id, symbols)
            await self.send_to_client(client_id, {
                "type": "subscribe_result",
                **result
            })
        
        elif msg_type == 'unsubscribe':
            symbols = message.get('symbols', [])
            result = await self.unsubscribe(client_id, symbols)
            await self.send_to_client(client_id, {
                "type": "unsubscribe_result",
                **result
            })
        
        elif msg_type == 'ping':
            await self.send_to_client(client_id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        
        elif msg_type == 'get_subscriptions':
            subscriptions = list(self.subscriptions.get(client_id, set()))
            await self.send_to_client(client_id, {
                "type": "subscriptions",
                "symbols": subscriptions
            })
        
        else:
            await self.send_to_client(client_id, {
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            })
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
    
    def get_stats(self) -> Dict:
        """Get WebSocket server statistics."""
        return {
            "active_connections": len(self.active_connections),
            "total_subscriptions": sum(len(s) for s in self.subscriptions.values()),
            "unique_symbols": len(self.symbol_subscribers),
            "cached_prices": len(self.price_cache)
        }


# Global manager instance
ws_manager = WebSocketManager()
