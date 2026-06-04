import json

from app.core.config import Settings, get_settings
from app.database.redis import cache_client
from app.schemas.admin import PricingConfigResponse, PricingConfigUpdate

PRICING_CACHE_KEY = "veluna:platform:pricing"


class PlatformSettingsService:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()

    def _defaults(self) -> PricingConfigResponse:
        return PricingConfigResponse(
            gem_cost_per_message=self._settings.gem_cost_per_message,
            gem_cost_per_generation=self._settings.gem_cost_per_generation,
            default_user_gems=self._settings.default_user_gems,
        )

    async def get_pricing(self) -> PricingConfigResponse:
        try:
            raw = await cache_client.get(PRICING_CACHE_KEY)
        except Exception:
            return self._defaults()
        if not raw:
            return self._defaults()
        data = json.loads(raw)
        defaults = self._defaults()
        return PricingConfigResponse(
            gem_cost_per_message=data.get("gem_cost_per_message", defaults.gem_cost_per_message),
            gem_cost_per_generation=data.get("gem_cost_per_generation", defaults.gem_cost_per_generation),
            default_user_gems=data.get("default_user_gems", defaults.default_user_gems),
        )

    async def update_pricing(self, patch: PricingConfigUpdate) -> PricingConfigResponse:
        current = await self.get_pricing()
        updated = PricingConfigResponse(
            gem_cost_per_message=patch.gem_cost_per_message
            if patch.gem_cost_per_message is not None
            else current.gem_cost_per_message,
            gem_cost_per_generation=patch.gem_cost_per_generation
            if patch.gem_cost_per_generation is not None
            else current.gem_cost_per_generation,
            default_user_gems=patch.default_user_gems
            if patch.default_user_gems is not None
            else current.default_user_gems,
        )
        await cache_client.set(PRICING_CACHE_KEY, updated.model_dump_json())
        return updated
