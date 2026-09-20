import asyncio
import logging
from typing import Dict, List, Any

log = logging.getLogger("broadcast")

class MemoryBroadcaster:
    """
    In-memory pub-sub system for streaming live events (like scan progress) to SSE clients.
    Topic is usually the alert_id.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}

    async def subscribe(self, topic: str) -> asyncio.Queue:
        """Subscribe to a topic, returning an asyncio Queue."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        queue = asyncio.Queue()
        self._subscribers[topic].append(queue)
        log.debug(f"Subscribed to topic: {topic} (total {len(self._subscribers[topic])})")
        return queue

    def unsubscribe(self, topic: str, queue: asyncio.Queue):
        """Unsubscribe a specific queue from a topic."""
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(queue)
                log.debug(f"Unsubscribed from topic: {topic} (remaining {len(self._subscribers[topic])})")
                if not self._subscribers[topic]:
                    del self._subscribers[topic]
            except ValueError:
                pass

    async def publish(self, topic: str, message: Any):
        """Publish a message to all subscribers of a topic."""
        if topic in self._subscribers:
            for queue in self._subscribers[topic]:
                await queue.put(message)

# Global singleton
broadcaster = MemoryBroadcaster()
