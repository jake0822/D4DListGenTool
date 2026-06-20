from __future__ import annotations

from typing import Any

import httpx

from d4d_app.config import settings


async def search_leon_county_addresses(query: str) -> list[dict[str, Any]]:
    trimmed = query.strip()
    if len(trimmed) < 3:
        return []

    params = {
        "q": f"{trimmed}, Leon County, Florida, United States",
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 8,
        "countrycodes": "us",
    }

    headers = {"User-Agent": settings.nominatim_user_agent}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(f"{settings.nominatim_base_url}/search", params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return []

    results: list[dict[str, Any]] = []
    for item in data:
        address = item.get("address", {})
        county = (address.get("county") or "").lower()
        state = (address.get("state") or "").lower()
        if "leon" not in county or "florida" not in state:
            continue
        results.append(
            {
                "display_name": item.get("display_name"),
                "street_address": (
                    address.get("house_number", "").strip() + " " + (address.get("road") or "")
                ).strip()
                or item.get("name"),
                "city": address.get("city") or address.get("town") or address.get("village"),
                "state": address.get("state"),
                "zip_code": address.get("postcode"),
                "latitude": float(item.get("lat")) if item.get("lat") else None,
                "longitude": float(item.get("lon")) if item.get("lon") else None,
            }
        )
    return results
