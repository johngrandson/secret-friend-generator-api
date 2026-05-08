"""Redis Pub/Sub event bus for per-run agent event streaming.

publish sends each claude CLI event to a per-run channel.
subscribe yields events from that channel as an async generator.

Both methods are no-ops when redis_url is None or not a redis:// URL
so execution continues normally when the feature is disabled (tests, local
without Redis).
"""

import json
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis


class RedisRunEventBus:
    def __init__(self, redis_url: str | None = None) -> None:
        self._client: aioredis.Redis | None = None
        if redis_url and redis_url.startswith(("redis://", "rediss://", "redis+sentinel://")):
            self._client = aioredis.from_url(redis_url, decode_responses=True)

    def _channel(self, run_id: UUID) -> str:
        return f"run:{run_id}:events"

    async def publish(self, run_id: UUID, event: dict[str, Any]) -> None:
        if self._client is None:
            return
        await self._client.publish(self._channel(run_id), json.dumps(event))

    async def subscribe(self, run_id: UUID) -> AsyncGenerator[dict[str, Any], None]:
        if self._client is None:
            return
        pubsub = self._client.pubsub()
        await pubsub.subscribe(self._channel(run_id))
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                event: dict[str, Any] = json.loads(message["data"])
                yield event
                if event.get("type") == "_stream_done":
                    break
        finally:
            await pubsub.unsubscribe(self._channel(run_id))
