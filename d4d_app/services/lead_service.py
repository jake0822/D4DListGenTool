from __future__ import annotations

from datetime import date
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from d4d_app.models import Lead
from d4d_app.services.leon_scraper import LeonPropertyLookupService, PropertyData


def find_existing_lead(db: Session, street_address: str, city: str | None, state: str | None, zip_code: str | None) -> Lead | None:
    stmt = select(Lead).where(
        Lead.street_address == street_address,
        Lead.city == city,
        Lead.state == state,
        Lead.zip_code == zip_code,
    )
    return db.execute(stmt).scalar_one_or_none()


async def create_or_get_lead(db: Session, payload: dict[str, Any], scraper: LeonPropertyLookupService | None = None) -> tuple[Lead, bool]:
    street_address = (payload.get("street_address") or "").strip()
    city = (payload.get("city") or "").strip() or None
    state = (payload.get("state") or "").strip() or None
    zip_code = (payload.get("zip_code") or "").strip() or None

    existing = find_existing_lead(db, street_address, city, state, zip_code)
    if existing:
        return existing, False

    lead = Lead(
        street_address=street_address,
        city=city,
        state=state,
        zip_code=zip_code,
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        lead_status="TO_CALL",
    )

    lookup = scraper or LeonPropertyLookupService()
    property_data = await lookup.lookup(street_address, city, zip_code)
    lead.owner_name = property_data.owner_name
    lead.owner_mailing_address = property_data.owner_mailing_address
    lead.parcel_id = property_data.parcel_id
    lead.property_type = property_data.property_type
    lead.square_feet = property_data.square_feet
    lead.year_built = property_data.year_built
    lead.bedrooms = property_data.bedrooms
    lead.bathrooms = property_data.bathrooms
    lead.assessed_value = property_data.assessed_value
    lead.market_value = property_data.market_value

    lead.absentee_owner = int(_is_absentee_owner(lead.street_address, lead.owner_mailing_address))
    lead.years_owned = _years_of_ownership(property_data.purchase_date)
    lead.lead_score = _calculate_lead_score(lead.absentee_owner == 1, lead.years_owned, property_data)

    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead, True


def _is_absentee_owner(property_address: str, mailing_address: str | None) -> bool:
    if not mailing_address:
        return False
    return property_address.lower() not in mailing_address.lower()


def _years_of_ownership(purchase_date: date | None) -> int | None:
    if not purchase_date:
        return None
    today = date.today()
    years = today.year - purchase_date.year
    if (today.month, today.day) < (purchase_date.month, purchase_date.day):
        years -= 1
    return max(years, 0)


def _calculate_lead_score(absentee_owner: bool, years_owned: int | None, property_data: PropertyData) -> int:
    score = 0
    if absentee_owner:
        score += 25
    if years_owned is not None and years_owned >= 10:
        score += 25
    if not any(
        (
            property_data.owner_name,
            property_data.parcel_id,
            property_data.property_type,
            property_data.square_feet,
            property_data.year_built,
            property_data.market_value,
            property_data.assessed_value,
        )
    ):
        score += 10
    return score
