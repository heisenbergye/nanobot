"""Canvas WebSocket server for real-time agent-driven UI."""

import asyncio
import json
from typing import Any

from loguru import logger

try:
    import websockets
    from websockets.server import serve, WebSocketServerProtocol
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


class CanvasServer:
    """WebSocket server for Canvas real-time updates."""
    
    _instance: "CanvasServer | None" = None
    
    def __init__(self, host: str = "127.0.0.1", port: int = 18791):
        self.host = host
        self.port = port
        self._clients: set[WebSocketServerProtocol] = set()
        self._server = None
        self._state: dict[str, Any] = {
            "title": "nanobot Canvas",
            "content": "",
            "components": [],
            "theme": "light",
        }
        self._running = False
    
    @classmethod
    def get_instance(cls, host: str = "127.0.0.1", port: int = 18791) -> "CanvasServer":
        if cls._instance is None:
            cls._instance = CanvasServer(host, port)
        return cls._instance
    
    async def start(self) -> None:
        """Start the Canvas WebSocket server."""
        if not WS_AVAILABLE:
            logger.warning("websockets not installed, Canvas disabled")
            return
        
        if self._running:
            return
        
        self._running = True
        self._server = await serve(
            self._handle_client,
            self.host,
            self.port,
        )
        logger.info("Canvas server started at ws://{}:{}", self.host, self.port)
    
    async def stop(self) -> None:
        """Stop the Canvas server."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        self._clients.clear()
    
    async def _handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """Handle a new Canvas client connection."""
        self._clients.add(websocket)
        logger.debug("Canvas client connected, total: {}", len(self._clients))
        
        # Send current state
        await websocket.send(json.dumps({
            "type": "state",
            "data": self._state,
        }))
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
            logger.debug("Canvas client disconnected, total: {}", len(self._clients))
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, data: dict) -> None:
        """Handle incoming message from client."""
        msg_type = data.get("type")
        
        if msg_type == "get_state":
            await websocket.send(json.dumps({
                "type": "state",
                "data": self._state,
            }))
    
    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connected clients."""
        if not self._clients:
            return
        
        data = json.dumps(message)
        await asyncio.gather(
            *[client.send(data) for client in self._clients],
            return_exceptions=True,
        )
    
    async def update_state(self, updates: dict[str, Any]) -> None:
        """Update canvas state and broadcast to clients."""
        self._state.update(updates)
        await self.broadcast({
            "type": "update",
            "data": updates,
        })
    
    async def set_content(self, content: str) -> None:
        """Set the main content (markdown/html)."""
        await self.update_state({"content": content})
    
    async def set_title(self, title: str) -> None:
        """Set the canvas title."""
        await self.update_state({"title": title})
    
    async def add_component(self, component: dict) -> None:
        """Add a component to the canvas."""
        self._state["components"].append(component)
        await self.broadcast({
            "type": "add_component",
            "data": component,
        })
    
    async def clear_components(self) -> None:
        """Clear all components."""
        self._state["components"] = []
        await self.broadcast({"type": "clear_components"})
    
    async def reset(self) -> None:
        """Reset canvas to initial state."""
        self._state = {
            "title": "nanobot Canvas",
            "content": "",
            "components": [],
            "theme": "light",
        }
        await self.broadcast({
            "type": "state",
            "data": self._state,
        })
    
    @property
    def client_count(self) -> int:
        return len(self._clients)
    
    @property
    def state(self) -> dict[str, Any]:
        return self._state.copy()
