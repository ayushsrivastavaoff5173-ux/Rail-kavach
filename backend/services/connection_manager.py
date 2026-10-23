import logging
from typing import List, Set

from fastapi import WebSocket

logger = logging.getLogger("railkavach.websocket")


class ConnectionManager:
    def __init__(self) -> None:
        self._clients: Set[WebSocket] = set()

    @property
    def count(self) -> int:
        return len(self._clients)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)
        logger.info("WebSocket client connected (%d total)", self.count)

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)
        logger.info("WebSocket client removed (%d total)", self.count)

    async def broadcast(self, message: str) -> None:
        failed: List[WebSocket] = []
        for websocket in list(self._clients):
            try:
                await websocket.send_text(message)
            except Exception as exc:
                logger.info("Dropping WebSocket client after send failure: %s", exc)
                failed.append(websocket)
        for websocket in failed:
            self.disconnect(websocket)