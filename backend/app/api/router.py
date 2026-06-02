from fastapi import APIRouter

from app.api.v1 import auth, characters, chats, generations, payments, admin, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(generations.router, prefix="/generations", tags=["generations"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
