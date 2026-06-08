"""Redis cache for chat list, detail, and messages."""

from uuid import UUID

from app.core.config import get_settings
from app.database.redis import cache

CHAT_LIST_PREFIX = "veluna:chat:list:"
CHAT_DETAIL_PREFIX = "veluna:chat:detail:"
CHAT_MSGS_PREFIX = "veluna:chat:msgs:"


class ChatCacheService:
    def __init__(self) -> None:
        settings = get_settings()
        self._list_ttl = settings.chat_cache_list_ttl
        self._detail_ttl = settings.chat_cache_detail_ttl
        self._messages_ttl = settings.chat_cache_messages_ttl

    @staticmethod
    def _list_key(user_id: UUID, page: int) -> str:
        return f"{CHAT_LIST_PREFIX}{user_id}:p{page}"

    @staticmethod
    def _detail_key(chat_id: UUID) -> str:
        return f"{CHAT_DETAIL_PREFIX}{chat_id}"

    @staticmethod
    def _messages_key(chat_id: UUID, user_id: UUID, limit: int) -> str:
        return f"{CHAT_MSGS_PREFIX}{chat_id}:{user_id}:l{limit}"

    async def get_list(self, user_id: UUID, page: int) -> tuple[list[dict], int] | None:
        raw = await cache.get(self._list_key(user_id, page))
        if not raw or not isinstance(raw, dict):
            return None
        items = raw.get("items")
        total = raw.get("total")
        if not isinstance(items, list) or not isinstance(total, int):
            return None
        return items, total

    async def set_list(self, user_id: UUID, page: int, items: list[dict], total: int) -> None:
        await cache.set(
            self._list_key(user_id, page),
            {"items": items, "total": total},
            ttl=self._list_ttl,
        )

    async def get_detail(self, chat_id: UUID) -> dict | None:
        raw = await cache.get(self._detail_key(chat_id))
        return raw if isinstance(raw, dict) else None

    async def set_detail(self, chat_id: UUID, data: dict) -> None:
        await cache.set(self._detail_key(chat_id), data, ttl=self._detail_ttl)

    async def get_messages(self, chat_id: UUID, user_id: UUID, limit: int) -> list[dict] | None:
        raw = await cache.get(self._messages_key(chat_id, user_id, limit))
        return raw if isinstance(raw, list) else None

    async def set_messages(self, chat_id: UUID, user_id: UUID, limit: int, items: list[dict]) -> None:
        await cache.set(
            self._messages_key(chat_id, user_id, limit),
            items,
            ttl=self._messages_ttl,
        )

    async def invalidate_user_lists(self, user_id: UUID) -> None:
        await cache.delete_pattern(f"{CHAT_LIST_PREFIX}{user_id}:*")

    async def invalidate_chat(self, chat_id: UUID, user_id: UUID | None = None) -> None:
        await cache.delete(self._detail_key(chat_id))
        if user_id is not None:
            await cache.delete_pattern(f"{CHAT_MSGS_PREFIX}{chat_id}:{user_id}:*")
        else:
            await cache.delete_pattern(f"{CHAT_MSGS_PREFIX}{chat_id}:*")

    async def invalidate_all(self) -> int:
        deleted = 0
        for prefix in (CHAT_LIST_PREFIX, CHAT_DETAIL_PREFIX, CHAT_MSGS_PREFIX):
            deleted += await cache.delete_pattern(f"{prefix}*")
        return deleted


chat_cache = ChatCacheService()
