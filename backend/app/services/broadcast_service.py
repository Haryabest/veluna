from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Broadcast, BroadcastStatus, User
from app.utils.localized_text import pick_localized
from app.utils.locale import normalize_app_locale

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

    async def _recipients(self) -> list[tuple[int, str]]:
        result = await self._session.execute(
            select(User.telegram_id, User.language_code).where(
                User.is_banned == False,  # noqa: E712
                User.is_active == True,  # noqa: E712
            )
        )
        rows: list[tuple[int, str]] = []
        for telegram_id, language_code in result.all():
            rows.append((int(telegram_id), normalize_app_locale(language_code)))
        return rows

    async def send_broadcast(
        self,
        message_text: str,
        admin_id: UUID | None = None,
        *,
        message_text_alt: str | None = None,
        parse_mode: str = "HTML",
    ) -> Broadcast:
        text = message_text.strip()
        alt = (message_text_alt or "").strip() or None
        if not text:
            from app.core.exceptions import ValidationError

            raise ValidationError("Текст рассылки не может быть пустым")

        recipients = await self._recipients()
        record = Broadcast(
            admin_id=admin_id,
            message_text=text,
            message_text_alt=alt,
            status=BroadcastStatus.RUNNING.value,
            total_recipients=len(recipients),
        )
        self._session.add(record)
        await self._session.flush()

        sent, failed = await self._deliver(text, alt, recipients, parse_mode=parse_mode)
        record.sent_count = sent
        record.failed_count = failed
        record.status = BroadcastStatus.COMPLETED.value
        await self._session.flush()
        return record

    async def _deliver(
        self,
        primary: str,
        alt: str | None,
        recipients: list[tuple[int, str]],
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
            for chat_id, locale in recipients:
                body = pick_localized(primary, alt, locale)
                try:
                    response = await client.post(
                        url,
                        json={
                            "chat_id": chat_id,
                            "text": body,
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
