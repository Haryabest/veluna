from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.balance import router as balance_router
from app.bot.handlers.locale import router as locale_router
from app.bot.handlers.payments import router as payments_router
from app.bot.handlers.start import router as start_router

__all__ = ["start_router", "locale_router", "payments_router", "balance_router", "admin_router"]
