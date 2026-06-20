from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx

from d4d_app.config import settings


@dataclass
class PropertyData:
    owner_name: str | None = None
    owner_mailing_address: str | None = None
    parcel_id: str | None = None
    property_type: str | None = None
    square_feet: int | None = None
    year_built: int | None = None
    bedrooms: float | None = None
    bathrooms: float | None = None
    assessed_value: float | None = None
    market_value: float | None = None
    purchase_date: date | None = None


class LeonPropertyLookupService:
    """Best-effort Leon County lookup.

    Leon County does not publish a stable, openly documented JSON API for free-form address
    lookups. This service uses an environment-configurable public endpoint if available and
    gracefully returns empty values when unavailable or changed.
    """

    def __init__(self, search_url: str | None = None) -> None:
        self.search_url = search_url or settings.leon_property_search_url

    async def lookup(self, street_address: str, city: str | None, zip_code: str | None) -> PropertyData:
        if not self.search_url:
            return PropertyData()

        query = ", ".join(part for part in [street_address, city, "FL", zip_code] if part)
        params = {"q": query}
        headers = {"User-Agent": settings.nominatim_user_agent}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.search_url, params=params, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            return PropertyData()

        return self._parse_payload(payload)

    def _parse_payload(self, payload: Any) -> PropertyData:
        if isinstance(payload, dict):
            source = payload.get("result") or payload
        elif isinstance(payload, list) and payload:
            source = payload[0]
        else:
            return PropertyData()

        return PropertyData(
            owner_name=source.get("owner_name") if isinstance(source, dict) else None,
            owner_mailing_address=source.get("owner_mailing_address") if isinstance(source, dict) else None,
            parcel_id=source.get("parcel_id") if isinstance(source, dict) else None,
            property_type=source.get("property_type") if isinstance(source, dict) else None,
            square_feet=_safe_int(source.get("square_feet") if isinstance(source, dict) else None),
            year_built=_safe_int(source.get("year_built") if isinstance(source, dict) else None),
            bedrooms=_safe_float(source.get("bedrooms") if isinstance(source, dict) else None),
            bathrooms=_safe_float(source.get("bathrooms") if isinstance(source, dict) else None),
            assessed_value=_safe_float(source.get("assessed_value") if isinstance(source, dict) else None),
            market_value=_safe_float(source.get("market_value") if isinstance(source, dict) else None),
        )


def _safe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() != "" else None
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None and str(value).strip() != "" else None
    except (TypeError, ValueError):
        return None
