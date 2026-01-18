"""
WebSocket Routes for Real-time Price Updates
"""

import uuid
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional

from ..services.websocket_manager import ws_manager
from ..utils.logging import logger

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/stocks")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time stock price updates.
    
    **Connection:**
    ```
    ws://localhost:8000/ws/stocks
    ```
    
    **Subscribe to stocks:**
    ```json
    {
        "type": "subscribe",
        "symbols": ["RELIANCE", "TCS", "INFY"]
    }
    ```
    
    **Unsubscribe:**
    ```json
    {
        "type": "unsubscribe",
        "symbols": ["RELIANCE"]
    }
    ```
    
    **Price update response:**
    ```json
    {
        "type": "price_update",
        "symbol": "RELIANCE",
        "price": 2456.30,
        "change": 12.50,
        "change_percent": 0.51,
        "high": 2480.00,
        "low": 2430.00,
        "volume": 1234567,
        "timestamp": "2026-01-16T23:58:00Z"
    }
    ```
    
    **Ping/Pong heartbeat:**
    ```json
    {"type": "ping"}
    ```
    Response:
    ```json
    {"type": "pong", "timestamp": "..."}
    ```
    """
    client_id = str(uuid.uuid4())
    
    try:
        # Accept connection
        await ws_manager.connect(websocket, client_id)
        logger.info(f"WebSocket client connected: {client_id}")
        
        # Start price stream if this is the first connection
        if ws_manager.get_connection_count() == 1:
            asyncio.create_task(ws_manager.start_price_stream())
        
        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                
                # Parse JSON
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON"
                    })
                    continue
                
                # Handle message
                await ws_manager.handle_message(client_id, message)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error for {client_id}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    finally:
        # Clean up on disconnect
        ws_manager.disconnect(client_id)
        logger.info(f"WebSocket client disconnected: {client_id}")


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket server statistics.
    
    Returns connection count, subscription count, etc.
    """
    return {
        "success": True,
        "data": ws_manager.get_stats()
    }
