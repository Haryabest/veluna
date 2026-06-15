from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_db
from app.schemas import (
    ChatArtAttach,
    ChatCreate,
    ChatListResponse,
    ChatNarratorUpdate,
    ChatPinUpdate,
    ChatResponse,
    ChatScenarioUpdate,
    ChatUpdate,
    MessageCreate,
    MessageDeleteResponse,
    MessageResponse,
    PaginatedResponse,
    SendMessageResponse,
    UserResponse,
)
from app.services.chat_service import ChatService
from app.utils.locale import normalize_app_locale

router = APIRouter()


def _user_locale(user: UserResponse) -> str:
    return normalize_app_locale(user.language_code)


@router.get("", response_model=PaginatedResponse)
async def list_chats(
    page: int = Query(1, ge=1),
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    chats, total = await service.list_user_chats(user.id, page=page, locale=_user_locale(user))
    page_size = 20
    return PaginatedResponse(
        items=chats,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ChatResponse)
async def create_chat(
    data: ChatCreate,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    return await service.get_or_create_chat(
        user.id, data.character_id, data.scenario_id, data.narrator_id, locale=_user_locale(user)
    )


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    return await service.get_chat(user.id, chat_id, locale=_user_locale(user))


@router.patch("/{chat_id}/scenario", response_model=ChatResponse)
async def switch_chat_scenario(
    chat_id: UUID,
    data: ChatScenarioUpdate,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    return await service.switch_scenario(
        user.id, chat_id, data.scenario_id, locale=_user_locale(user)
    )


@router.patch("/{chat_id}/narrator", response_model=ChatResponse)
async def switch_chat_narrator(
    chat_id: UUID,
    data: ChatNarratorUpdate,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    return await service.switch_narrator(
        user.id, chat_id, data.narrator_id, locale=_user_locale(user)
    )


@router.patch("/{chat_id}", response_model=ChatListResponse)
async def update_chat(
    chat_id: UUID,
    data: ChatUpdate,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    item = await service.update_title(user.id, chat_id, data.title, locale=_user_locale(user))
    return item


@router.patch("/{chat_id}/pin", response_model=ChatListResponse)
async def pin_chat(
    chat_id: UUID,
    data: ChatPinUpdate,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    return await service.set_pinned(user.id, chat_id, data.pinned, locale=_user_locale(user))


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: UUID,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    await service.archive_chat(user.id, chat_id)
    return {"id": str(chat_id), "deleted": True, "ok": True}


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    chat_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    return await service.get_messages(user.id, chat_id, limit=limit)


@router.post("/{chat_id}/messages", response_model=SendMessageResponse, status_code=202)
async def send_message(
    chat_id: UUID,
    data: MessageCreate,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    return await service.send_message(user.id, chat_id, data.content, data.reply_to_id)


@router.post("/{chat_id}/art", response_model=MessageResponse)
async def attach_chat_art(
    chat_id: UUID,
    data: ChatArtAttach,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    return await service.attach_generation(user.id, chat_id, data.generation_id)


@router.delete("/{chat_id}/messages/{message_id}", response_model=MessageDeleteResponse)
async def delete_message(
    chat_id: UUID,
    message_id: UUID,
    scope: str = Query("self", pattern="^(self|all)$"),
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = ChatService(session)
    return await service.delete_message(user.id, chat_id, message_id, scope)
