from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from d4d_app.database import Base


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    street_address: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_mailing_address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    parcel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    property_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    square_feet: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bedrooms: Mapped[float | None] = mapped_column(Float, nullable=True)
    bathrooms: Mapped[float | None] = mapped_column(Float, nullable=True)

    market_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    assessed_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    lead_status: Mapped[str] = mapped_column(String(50), default="TO_CALL", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    absentee_owner: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    years_owned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow_naive, onupdate=utcnow_naive, nullable=False
    )

    call_history: Mapped[list[CallHistory]] = relationship(
        "CallHistory", back_populates="property", cascade="all, delete-orphan"
    )


class CallHistory(Base):
    __tablename__ = "call_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    call_date: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive, nullable=False)
    result: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    property: Mapped[Lead] = relationship("Lead", back_populates="call_history")
