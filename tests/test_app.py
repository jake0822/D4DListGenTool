from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import delete

from d4d_app.database import Base, SessionLocal, engine
from d4d_app.main import app
from d4d_app.models import CallHistory, Lead
from d4d_app.routers import web


def setup_module():
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def test_homepage_loads():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Driving for Dollars" in response.text


def test_address_search_endpoint(monkeypatch):
    async def fake_search(query: str):
        return [{"display_name": "123 Main St, Tallahassee, FL", "street_address": "123 Main St"}]

    monkeypatch.setattr(web, "search_leon_county_addresses", fake_search)

    client = TestClient(app)
    response = client.get("/api/address-search?q=123 Main")
    assert response.status_code == 200
    assert response.json()[0]["street_address"] == "123 Main St"


def test_create_lead_and_view_in_dashboard(monkeypatch):
    async def fake_lookup(self, street_address: str, city: str | None, zip_code: str | None):
        from d4d_app.services.leon_scraper import PropertyData

        return PropertyData(owner_name="Jane Owner", parcel_id="123-456")

    from d4d_app.services.leon_scraper import LeonPropertyLookupService

    monkeypatch.setattr(LeonPropertyLookupService, "lookup", fake_lookup)

    client = TestClient(app)

    response = client.post(
        "/properties/add",
        data={
            "street_address": "111 Test St",
            "city": "Tallahassee",
            "state": "Florida",
            "zip_code": "32301",
            "latitude": "30.1",
            "longitude": "-84.2",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    dashboard = client.get("/leads")
    assert dashboard.status_code == 200
    assert "111 Test St" in dashboard.text

    with SessionLocal() as db:
        db.execute(delete(CallHistory))
        db.execute(delete(Lead))
        db.commit()
