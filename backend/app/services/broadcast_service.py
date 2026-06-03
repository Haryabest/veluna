from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Broadcast, BroadcastStatus, User

logger = logging.getLogger(__name__)

TELEGRAM_SEND_INTERVAL = 0.05  # ~20 msg/s


class BroadcastService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_broadcasts(self, limit: int = 20) -> list[Broadcast]:
        result = await self._session.execute(
            select(Broadcast).order_by(Broadcast.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def _recipient_telegram_ids(self) -> list[int]:
        result = await self._session.execute(
            select(User.telegram_id).where(
                User.is_banned == False,  # noqa: E712
                User.is_active == True,  # noqa: E712
            )
        )
        return [int(row[0]) for row in result.all()]

    async def send_broadcast(
        self,
        message_text: str,
        admin_id: UUID | None = None,
        *,
        parse_mode: str = "HTML",
    ) -> Broadcast:
        text = message_text.strip()
        if not text:
            from app.core.exceptions import ValidationError

            raise ValidationError("Текст рассылки не может быть пустым")

        recipients = await self._recipient_telegram_ids()
        record = Broadcast(
            admin_id=admin_id,
            message_text=text,
            status=BroadcastStatus.RUNNING.value,
            total_recipients=len(recipients),
        )
        self._session.add(record)
        await self._session.flush()

        sent, failed = await self._deliver(text, recipients, parse_mode=parse_mode)
        record.sent_count = sent
        record.failed_count = failed
        record.status = (
            BroadcastStatus.COMPLETED.value
            if failed == 0
            else BroadcastStatus.COMPLETED.value
        )
        await self._session.flush()
        return record

    async def _deliver(
        self,
        text: str,
        telegram_ids: list[int],
        *,
        parse_mode: str,
    ) -> tuple[int, int]:
        settings = get_settings()
        if not settings.telegram_bot_token:
            from app.core.exceptions import ValidationError

            raise ValidationError("TELEGRAM_BOT_TOKEN не настроен")

        sent = 0
        failed = 0
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"

        async with httpx.AsyncClient(timeout=30.0) as client:
            for chat_id in telegram_ids:
                try:
                    response = await client.post(
                        url,
                        json={
                            "chat_id": chat_id,
                            "text": text,
                            "parse_mode": parse_mode,
                        },
                    )
                    data = response.json()
                    if data.get("ok"):
                        sent += 1
                    else:
                        failed += 1
                        logger.debug("Broadcast skip %s: %s", chat_id, data.get("description"))
                except Exception as exc:
                    failed += 1
                    logger.debug("Broadcast error %s: %s", chat_id, exc)
                await asyncio.sleep(TELEGRAM_SEND_INTERVAL)

        return sent, failed
