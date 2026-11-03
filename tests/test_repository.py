from decimal import Decimal

from app import db
from app.models import Agent, Apartment, House, Listing
from app.repositories.agents import AgentRepository
from app.repositories.listings import ListingRepository


def test_joined_inheritance_roundtrip(tmp_path):
    url = f"sqlite:///{tmp_path / 'registry.sqlite'}"
    db.init_engine(url)
    db.Base.metadata.create_all(db.engine)
    session = db.SessionLocal()
    agents = AgentRepository(lambda: session)
    listings = ListingRepository(lambda: session)
    agent = agents.add(Agent(name="Мария Георгиева", phone="+359884102210", email="maria@imoti.example", office="София"))
    apartment = listings.add(
        Apartment(
            title="Двустаен",
            description="",
            deal_type="sale",
            price_eur=Decimal("198000.00"),
            area_sqm=Decimal("78.00"),
            city="София",
            address="ул. Цветна 12",
            year_built=2014,
            status="active",
            agent=agent,
            rooms=2,
            floor=4,
            total_floors=8,
            has_elevator=True,
            has_balcony=True,
        )
    )
    house = listings.add(
        House(
            title="Къща",
            description="",
            deal_type="rent",
            price_eur=Decimal("1800.00"),
            area_sqm=Decimal("190.00"),
            city="София",
            address="ул. Боровец 2",
            status="active",
            agent=agent,
            floors=2,
            yard_sqm=Decimal("400.00"),
            has_garage=True,
        )
    )
    session.close()

    fresh = db.SessionLocal()
    loaded = ListingRepository(lambda: fresh).get(apartment.id)
    assert isinstance(loaded, Apartment)
    assert not isinstance(loaded, House)
    assert loaded.rooms == 2
    assert loaded.price_per_sqm == Decimal("2538.46")
    assert loaded.agent.name == "Мария Георгиева"
    houses = [item for item in ListingRepository(lambda: fresh).search({"kind": "house"})]
    assert len(houses) == 1
    assert isinstance(houses[0], House)
    assert houses[0].id == house.id
    assert ListingRepository(lambda: fresh).count_for_agent(agent.id) == 2
    again = fresh.get(Listing, apartment.id)
    assert again.kind == "apartment"
    fresh.close()
