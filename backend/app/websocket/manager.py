import asyncio
import json
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.core.security import verify_token

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}
        self._user_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        if room_id not in self._connections:
            self._connections[room_id] = set()
        self._connections[room_id].add(websocket)
        self._user_connections[user_id] = websocket
        logger.info("ws_connected", room_id=room_id, user_id=user_id)

    def disconnect(self, websocket: WebSocket, room_id: str, user_id: str):
        if room_id in self._connections:
            self._connections[room_id].discard(websocket)
            if not self._connections[room_id]:
                del self._connections[room_id]
        self._user_connections.pop(user_id, None)
        logger.info("ws_disconnected", room_id=room_id, user_id=user_id)

    async def send_to_room(self, room_id: str, message: dict):
        if room_id not in self._connections:
            return
        dead = set()
        for ws in self._connections[room_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self._connections[room_id] -= dead

    async def send_to_user(self, user_id: str, message: dict):
        ws = self._user_connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self._user_connections.pop(user_id, None)

    async def broadcast_typing(self, room_id: str, user_id: str, is_typing: bool):
        await self.send_to_room(room_id, {
            "type": "typing",
            "user_id": user_id,
            "is_typing": is_typing,
        })

    async def send_generation_update(self, user_id: str, generation_id: str, status: str, data: dict | None = None):
        await self.send_to_user(user_id, {
            "type": "generation_update",
            "generation_id": generation_id,
            "status": status,
            "data": data or {},
        })


manager = ConnectionManager()


async def authenticate_ws(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return None
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return None
    return payload.sub


async def websocket_chat_handler(websocket: WebSocket, chat_id: str):
    user_id = await authenticate_ws(websocket)
    if not user_id:
        return

    room_id = f"chat:{chat_id}"
    await manager.connect(websocket, room_id, user_id)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "message")

            if msg_type == "typing":
                await manager.broadcast_typing(room_id, user_id, data.get("is_typing", False))
            elif msg_type == "message":
                await manager.send_to_room(room_id, {
                    "type": "message",
                    "user_id": user_id,
                    "content": data.get("content", ""),
                    "status": "received",
                })
                from app.tasks.chat_tasks import process_ai_response
                process_ai_response.delay(chat_id, data.get("message_id", ""))
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, user_id)
    except Exception:
        logger.exception("ws_error", room_id=room_id)
        manager.disconnect(websocket, room_id, user_id)
