from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from d4d_app.database import get_db
from d4d_app.models import CallHistory, Lead
from d4d_app.services.address_search import search_leon_county_addresses
from d4d_app.services.lead_service import create_or_get_lead

router = APIRouter()
templates = Jinja2Templates(directory="templates")

VALID_STATUSES = ["TO_CALL", "CALLED", "FOLLOW_UP", "NOT_INTERESTED", "UNDER_CONTRACT"]


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@router.get("/api/address-search")
async def address_search(q: str = Query(default="")):
    results = await search_leon_county_addresses(q)
    return JSONResponse(results)


@router.post("/properties/add")
async def add_property(
    street_address: str = Form(...),
    city: str = Form(default=""),
    state: str = Form(default=""),
    zip_code: str = Form(default=""),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    db: Session = Depends(get_db),
):
    lead, _ = await create_or_get_lead(
        db,
        {
            "street_address": street_address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "latitude": latitude,
            "longitude": longitude,
        },
    )
    return RedirectResponse(url=f"/property/{lead.id}", status_code=303)


@router.get("/leads")
async def leads_dashboard(request: Request, status: str | None = Query(default=None), db: Session = Depends(get_db)):
    stmt = select(Lead)
    if status in VALID_STATUSES:
        stmt = stmt.where(Lead.lead_status == status)
    stmt = stmt.order_by(desc(Lead.created_at))
    leads = db.execute(stmt).scalars().all()
    return templates.TemplateResponse(
        request,
        "leads.html",
        {
            "leads": leads,
            "statuses": VALID_STATUSES,
            "selected_status": status,
        },
    )


@router.get("/property/{lead_id}")
async def property_detail(lead_id: int, request: Request, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        return RedirectResponse(url="/leads", status_code=303)

    history = (
        db.execute(select(CallHistory).where(CallHistory.property_id == lead_id).order_by(desc(CallHistory.call_date)))
        .scalars()
        .all()
    )
    return templates.TemplateResponse(
        request,
        "property_detail.html",
        {"lead": lead, "statuses": VALID_STATUSES, "call_history": history},
    )


@router.post("/property/{lead_id}/update")
async def update_property(
    lead_id: int,
    phone_number: str = Form(default=""),
    email: str = Form(default=""),
    notes: str = Form(default=""),
    lead_status: str = Form(default="TO_CALL"),
    db: Session = Depends(get_db),
):
    lead = db.get(Lead, lead_id)
    if not lead:
        return RedirectResponse(url="/leads", status_code=303)

    lead.phone_number = phone_number.strip() or None
    lead.email = email.strip() or None
    lead.notes = notes.strip() or None
    lead.lead_status = lead_status if lead_status in VALID_STATUSES else "TO_CALL"
    db.commit()
    return RedirectResponse(url=f"/property/{lead_id}", status_code=303)


@router.post("/property/{lead_id}/calls")
async def add_call_history(
    lead_id: int,
    result: str = Form(default=""),
    notes: str = Form(default=""),
    next_follow_up_date: str = Form(default=""),
    db: Session = Depends(get_db),
):
    lead = db.get(Lead, lead_id)
    if not lead:
        return RedirectResponse(url="/leads", status_code=303)

    follow_up_date = None
    if next_follow_up_date:
        try:
            follow_up_date = datetime.strptime(next_follow_up_date, "%Y-%m-%d").date()
        except ValueError:
            follow_up_date = None

    entry = CallHistory(
        property_id=lead_id,
        result=result.strip() or None,
        notes=notes.strip() or None,
        next_follow_up_date=follow_up_date,
    )
    db.add(entry)
    db.commit()
    return RedirectResponse(url=f"/property/{lead_id}", status_code=303)
