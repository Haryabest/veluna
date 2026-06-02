from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.payments import router as payments_router
from app.bot.handlers.start import router as start_router

__all__ = ["start_router", "payments_router", "admin_router"]
