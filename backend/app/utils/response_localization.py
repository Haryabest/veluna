"""Map DB entities to API responses with locale-aware display fields."""

from __future__ import annotations

from app.models import Character, CharacterNarrator, CharacterScenario, ShopProduct
from app.schemas import (
    CharacterDetailResponse,
    CharacterNarratorResponse,
    CharacterResponse,
    CharacterScenarioResponse,
)
from app.schemas.catalog import ShopProductResponse
from app.utils.localized_text import pick_localized, pick_localized_list
from app.utils.locale import AppLocale, normalize_app_locale


def request_locale(language_code: str | None) -> AppLocale:
    return normalize_app_locale(language_code)


def character_response(c: Character, locale: str | AppLocale) -> CharacterResponse:
    base = CharacterResponse.model_validate(c)
    sub = pick_localized(c.subtitle, c.subtitle_alt, locale)
    params = pick_localized_list(
        c.behavior_params, getattr(c, "behavior_params_alt", None), locale
    )
    return base.model_copy(
        update={
            "name": pick_localized(c.name, c.name_alt, locale),
            "description": pick_localized(c.description, c.description_alt, locale),
            "subtitle": sub if sub else None,
            "behavior_params": params,
            "tags": params,
        }
    )


def character_detail_response(c: Character, locale: str | AppLocale) -> CharacterDetailResponse:
    base = CharacterDetailResponse.model_validate(c)
    sub = pick_localized(c.subtitle, c.subtitle_alt, locale)
    params = pick_localized_list(
        c.behavior_params, getattr(c, "behavior_params_alt", None), locale
    )
    return base.model_copy(
        update={
            "name": pick_localized(c.name, c.name_alt, locale),
            "description": pick_localized(c.description, c.description_alt, locale),
            "subtitle": sub if sub else None,
            "behavior_params": params,
            "tags": params,
        }
    )


def scenario_response(s: CharacterScenario, locale: str | AppLocale) -> CharacterScenarioResponse:
    base = CharacterScenarioResponse.model_validate(s)
    return base.model_copy(
        update={
            "title": pick_localized(s.title, s.title_alt, locale),
            "story": pick_localized(s.story, getattr(s, "story_alt", None), locale),
            "communication_style": pick_localized(
                s.communication_style,
                getattr(s, "communication_style_alt", None),
                locale,
            ),
        }
    )


def narrator_response(n: CharacterNarrator, locale: str | AppLocale) -> CharacterNarratorResponse:
    base = CharacterNarratorResponse.model_validate(n)
    return base.model_copy(
        update={
            "name": pick_localized(n.name, n.name_alt, locale),
            "description": pick_localized(
                n.description,
                getattr(n, "description_alt", None),
                locale,
            ),
        }
    )


def shop_product_response(p: ShopProduct, locale: str | AppLocale) -> ShopProductResponse:
    base = ShopProductResponse.model_validate(p)
    return base.model_copy(update={"name": pick_localized(p.name, p.name_alt, locale)})
