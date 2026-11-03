from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def money(value):
    if value is None:
        return None
    return float(Decimal(str(value)).quantize(Decimal("0.01")))


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    office: Mapped[str] = mapped_column(String(80), nullable=False)
    listings: Mapped[list["Listing"]] = relationship(back_populates="agent")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "office": self.office,
        }


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    deal_type: Mapped[str] = mapped_column(String(10), nullable=False)
    price_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    area_sqm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[str] = mapped_column(String(200), default="")
    year_built: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    agent: Mapped[Agent] = relationship(back_populates="listings")
    inquiries: Mapped[list["Inquiry"]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )

    __mapper_args__ = {"polymorphic_on": "kind", "polymorphic_abstract": True}

    @property
    def price_per_sqm(self):
        if self.area_sqm in (None, 0, Decimal("0")):
            return None
        area = Decimal(str(self.area_sqm))
        if area == 0:
            return None
        return (Decimal(str(self.price_eur)) / area).quantize(Decimal("0.01"))

    def to_dict(self):
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "description": self.description or "",
            "deal_type": self.deal_type,
            "price_eur": money(self.price_eur),
            "area_sqm": money(self.area_sqm),
            "price_per_sqm": money(self.price_per_sqm),
            "city": self.city,
            "address": self.address or "",
            "year_built": self.year_built,
            "status": self.status,
            "agent_id": self.agent_id,
            "agent_name": self.agent.name if self.agent is not None else None,
            "created_at": self.created_at.isoformat(timespec="minutes") if self.created_at else None,
        }


class Apartment(Listing):
    __tablename__ = "apartments"

    id: Mapped[int] = mapped_column(ForeignKey("listings.id"), primary_key=True)
    rooms: Mapped[int] = mapped_column(nullable=False)
    floor: Mapped[int] = mapped_column(nullable=False)
    total_floors: Mapped[int] = mapped_column(nullable=False)
    has_elevator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_balcony: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "apartment"}

    def to_dict(self):
        data = super().to_dict()
        data.update(
            {
                "rooms": self.rooms,
                "floor": self.floor,
                "total_floors": self.total_floors,
                "has_elevator": self.has_elevator,
                "has_balcony": self.has_balcony,
            }
        )
        return data


class House(Listing):
    __tablename__ = "houses"

    id: Mapped[int] = mapped_column(ForeignKey("listings.id"), primary_key=True)
    floors: Mapped[int] = mapped_column(nullable=False)
    yard_sqm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    has_garage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "house"}

    def to_dict(self):
        data = super().to_dict()
        data.update(
            {
                "floors": self.floors,
                "yard_sqm": money(self.yard_sqm),
                "has_garage": self.has_garage,
            }
        )
        return data


class Inquiry(Base):
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    author_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    listing: Mapped[Listing] = relationship(back_populates="inquiries")

    def to_dict(self):
        return {
            "id": self.id,
            "listing_id": self.listing_id,
            "listing_title": self.listing.title if self.listing is not None else None,
            "author_name": self.author_name,
            "phone": self.phone,
            "message": self.message,
            "created_at": self.created_at.isoformat(timespec="minutes") if self.created_at else None,
        }


class ListingEvent(Base):
    __tablename__ = "listing_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    event: Mapped[str] = mapped_column(String(40), nullable=False)
    listing_id: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    payload: Mapped[str] = mapped_column(Text, default="")

    def to_dict(self):
        return {
            "id": self.id,
            "logged_at": self.logged_at.isoformat(timespec="minutes") if self.logged_at else None,
            "event": self.event,
            "listing_id": self.listing_id,
            "title": self.title,
            "payload": self.payload,
        }
