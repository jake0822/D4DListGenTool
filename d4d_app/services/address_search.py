from __future__ import annotations

from typing import Any

import httpx

from d4d_app.config import settings


async def search_leon_county_addresses(query: str) -> list[dict[str, Any]]:
    """
    Uses Google Places Autocomplete to find Leon County/Tallahassee addresses.
    Returns the same JSON structure expected by the frontend.
    """

    trimmed = query.strip()

    if len(trimmed) < 3:
        return []

    print("\n========================")
    print("GOOGLE ADDRESS SEARCH")
    print("Query:", trimmed)

    api_key = settings.GOOGLE_MAPS_API_KEY

    if not api_key:
        print("ERROR: GOOGLE_MAPS_API_KEY is missing")
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:

            # Step 1: Autocomplete search
            autocomplete_response = await client.get(
                "https://maps.googleapis.com/maps/api/place/autocomplete/json",
                params={
                    "input": trimmed,
                    "types": "address",
                    "components": "country:us",
                    "location": "30.4383,-84.2807",
                    "radius": 35000,
                    "key": api_key,
                },
            )

            autocomplete_response.raise_for_status()

            autocomplete_data = autocomplete_response.json()

            print(
                "Autocomplete results:",
                len(autocomplete_data.get("predictions", []))
            )

            results = []

            for prediction in autocomplete_data.get("predictions", []):

                place_id = prediction.get("place_id")

                if not place_id:
                    continue

                # Step 2: Get detailed address info
                details_response = await client.get(
                    "https://maps.googleapis.com/maps/api/place/details/json",
                    params={
                        "place_id": place_id,
                        "fields": (
                            "address_component,"
                            "geometry,"
                            "formatted_address"
                        ),
                        "key": api_key,
                    },
                )

                details_response.raise_for_status()

                details = details_response.json().get("result", {})

                components = details.get("address_components", [])

                address = {
                    "street_number": "",
                    "route": "",
                    "city": "",
                    "state": "",
                    "zip": "",
                }

                for component in components:
                    types = component.get("types", [])

                    if "street_number" in types:
                        address["street_number"] = component["long_name"]

                    elif "route" in types:
                        address["route"] = component["long_name"]

                    elif "locality" in types:
                        address["city"] = component["long_name"]

                    elif "administrative_area_level_1" in types:
                        address["state"] = component["short_name"]

                    elif "postal_code" in types:
                        address["zip"] = component["long_name"]

                street_address = (
                    f"{address['street_number']} {address['route']}"
                ).strip()

                # Filter to Leon County/Tallahassee area
                if (
                    "Tallahassee"
                    not in details.get("formatted_address", "")
                ):
                    continue

                location = (
                    details.get("geometry", {})
                    .get("location", {})
                )

                result = {
                    "display_name": details.get("formatted_address"),
                    "street_address": street_address,
                    "city": address["city"],
                    "state": address["state"],
                    "zip_code": address["zip"],
                    "latitude": location.get("lat"),
                    "longitude": location.get("lng"),
                }

                print("FOUND:", result["display_name"])

                results.append(result)

            print("FINAL RESULTS:", len(results))
            print("========================\n")

            return results

    except Exception as e:
        print("GOOGLE ADDRESS SEARCH ERROR:", e)
        return []