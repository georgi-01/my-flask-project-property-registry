from decimal import Decimal

import pytest

from app.errors import ValidationError
from app.models import Agent, Apartment, House
from app.services.agents import AgentService
from app.services.inquiries import InquiryService
from app.services.listings import ListingService


class FakeAgents:
    def __init__(self):
        self.rows = {}
        self.next_id = 1

    def add(self, agent):
        agent.id = self.next_id
        self.rows[agent.id] = agent
        self.next_id += 1
        return agent

    def get(self, agent_id):
        try:
            return self.rows.get(int(agent_id))
        except (TypeError, ValueError):
            return None

    def search(self, text=""):
        return list(self.rows.values())

    def delete(self, agent):
        del self.rows[agent.id]

    def count(self):
        return len(self.rows)

    def commit(self):
        return None


class FakeListings:
    def __init__(self):
        self.rows = {}
        self.next_id = 1

    def add(self, listing):
        listing.id = self.next_id
        self.rows[listing.id] = listing
        self.next_id += 1
        return listing

    def get(self, listing_id):
        return self.rows.get(listing_id)

    def search(self, filters=None):
        return list(self.rows.values())

    def delete(self, listing):
        del self.rows[listing.id]

    def commit(self):
        return None

    def counts_by_kind(self):
        counts = {}
        for listing in self.rows.values():
            counts[listing.kind] = counts.get(listing.kind, 0) + 1
        return counts

    def count_for_agent(self, agent_id):
        return sum(1 for listing in self.rows.values() if listing.agent_id == agent_id)


class FakeInquiries:
    def __init__(self):
        self.rows = {}
        self.next_id = 1

    def add(self, inquiry):
        inquiry.id = self.next_id
        self.rows[inquiry.id] = inquiry
        self.next_id += 1
        return inquiry

    def get(self, inquiry_id):
        return self.rows.get(inquiry_id)

    def all(self):
        return list(self.rows.values())

    def for_listing(self, listing_id):
        return [item for item in self.rows.values() if item.listing_id == listing_id]

    def delete(self, inquiry):
        del self.rows[inquiry.id]

    def commit(self):
        return None

    def count(self):
        return len(self.rows)


def agent_service():
    agents = FakeAgents()
    listings = FakeListings()
    service = AgentService(agents, listings)
    return service, agents, listings


def sample_agent(service):
    return service.create(
        {"name": "Мария Георгиева", "phone": "+359 88 410 2210", "email": "maria@imoti.example", "office": "София"}
    )


def apartment_data(agent_id, **extra):
    data = {
        "kind": "apartment",
        "title": "Двустаен в Лозенец",
        "description": "Южен.",
        "deal_type": "sale",
        "price_eur": "100000",
        "area_sqm": "50",
        "city": "София",
        "address": "ул. Цветна 12",
        "year_built": "2014",
        "status": "active",
        "agent_id": agent_id,
        "rooms": "2",
        "floor": "4",
        "total_floors": "8",
        "has_elevator": True,
        "has_balcony": False,
    }
    data.update(extra)
    return data


def test_create_apartment_computes_price_per_sqm():
    agents = FakeAgents()
    listings = FakeListings()
    published = []
    service = ListingService(listings, agents, FakeInquiries(), lambda name, data: published.append((name, data)))
    agent = Agent(name="Мария", phone="+359884102210", email="m@imoti.example", office="София")
    agents.add(agent)
    listing = service.create(apartment_data(agent.id))
    assert isinstance(listing, Apartment)
    assert listing.price_per_sqm == Decimal("2000.00")
    assert listing.rooms == 2
    assert published[0][0] == "listing.created"
    assert published[0][1]["price_per_sqm"] == 2000.0
    assert published[0][1]["price_eur"] == 100000.0


def test_create_house_requires_yard():
    agents = FakeAgents()
    listings = FakeListings()
    service = ListingService(listings, agents, FakeInquiries(), lambda *args: None)
    agent = Agent(name="Николай", phone="+359887331045", email="n@imoti.example", office="Пловдив")
    agents.add(agent)
    with pytest.raises(ValidationError) as error:
        service.create(
            {
                "kind": "house",
                "title": "Къща",
                "deal_type": "sale",
                "price_eur": "210000",
                "area_sqm": "160",
                "city": "Пловдив",
                "agent_id": agent.id,
                "floors": "2",
                "yard_sqm": "",
            }
        )
    assert "Въведете Двор." in error.value.args
    assert listings.rows == {}


def test_apartment_floor_cannot_exceed_building():
    agents = FakeAgents()
    service = ListingService(FakeListings(), agents, FakeInquiries(), lambda *args: None)
    agent = Agent(name="Елена", phone="+359889220118", email="e@imoti.example", office="Варна")
    agents.add(agent)
    with pytest.raises(ValidationError) as error:
        service.create(apartment_data(agent.id, floor="9", total_floors="8"))
    assert "Етажът не може да е над етажите на сградата." in error.value.args


def test_price_rejects_text():
    agents = FakeAgents()
    service = ListingService(FakeListings(), agents, FakeInquiries(), lambda *args: None)
    agent = Agent(name="Мария", phone="+359884102210", email="m2@imoti.example", office="София")
    agents.add(agent)
    with pytest.raises(ValidationError) as error:
        service.create(apartment_data(agent.id, price_eur="безплатно"))
    assert "Цена трябва да е число." in error.value.args


def test_update_recalculates_square_meter_price():
    agents = FakeAgents()
    listings = FakeListings()
    service = ListingService(listings, agents, FakeInquiries(), lambda *args: None)
    agent = Agent(name="Мария", phone="+359884102210", email="m3@imoti.example", office="София")
    agents.add(agent)
    listing = service.create(apartment_data(agent.id))
    updated = service.update(listing.id, apartment_data(agent.id, price_eur="150000", area_sqm="60"))
    assert updated.price_per_sqm == Decimal("2500.00")


def test_delete_listing_removes_it_and_publishes():
    agents = FakeAgents()
    listings = FakeListings()
    published = []
    service = ListingService(listings, agents, FakeInquiries(), lambda name, data: published.append(name))
    agent = Agent(name="Мария", phone="+359884102210", email="m4@imoti.example", office="София")
    agents.add(agent)
    listing = service.create(apartment_data(agent.id))
    service.delete(listing.id)
    assert listings.rows == {}
    assert published == ["listing.created", "listing.deleted"]


def test_unknown_agent_is_rejected():
    service = ListingService(FakeListings(), FakeAgents(), FakeInquiries(), lambda *args: None)
    with pytest.raises(ValidationError) as error:
        service.create(apartment_data(99))
    assert "Изберете съществуващ брокер." in error.value.args


def test_agent_names_are_required():
    service, agents, _listings = agent_service()
    with pytest.raises(ValidationError) as error:
        service.create({"name": "   ", "phone": "123", "email": "a@b.c", "office": ""})
    assert "Въведете име." in error.value.args
    assert "Въведете телефон." in error.value.args
    assert "Въведете офис." in error.value.args
    assert agents.rows == {}


def test_agent_with_listings_is_not_deleted():
    agents_repo = FakeAgents()
    listings_repo = FakeListings()
    agents = AgentService(agents_repo, listings_repo)
    listings = ListingService(listings_repo, agents_repo, FakeInquiries(), lambda *args: None)
    agent = sample_agent(agents)
    listings.create(apartment_data(agent.id))
    with pytest.raises(ValidationError) as error:
        agents.delete(agent.id)
    assert "не може да бъде изтрит" in error.value.args[0]
    assert agent.id in agents_repo.rows


def test_inquiry_needs_a_message_and_publishes_listing_title():
    agents = FakeAgents()
    listings_repo = FakeListings()
    inquiries = FakeInquiries()
    published = []
    listings = ListingService(listings_repo, agents, inquiries, lambda *args: None)
    inquiry_service = InquiryService(inquiries, listings_repo, lambda name, data: published.append((name, data)))
    agent = Agent(name="Мария", phone="+359884102210", email="m5@imoti.example", office="София")
    agents.add(agent)
    listing = listings.create(apartment_data(agent.id))
    with pytest.raises(ValidationError):
        inquiry_service.create(listing.id, {"author_name": "Иван Петров", "phone": "+359888000111", "message": "да"})
    saved = inquiry_service.create(
        listing.id,
        {"author_name": "Иван Петров", "phone": "+359888000111", "message": "Има ли гараж в цената?"},
    )
    assert saved.listing_id == listing.id
    assert published[0][0] == "inquiry.created"
    assert published[0][1]["title"] == "Двустаен в Лозенец"
    assert isinstance(listing, House) is False


def test_house_square_meter_price_uses_building_area_not_yard():
    agents = FakeAgents()
    service = ListingService(FakeListings(), agents, FakeInquiries(), lambda *args: None)
    agent = Agent(name="Елена", phone="+359889220118", email="e2@imoti.example", office="Варна")
    agents.add(agent)
    house = service.create(
        {
            "kind": "house",
            "title": "Къща в Сарафово",
            "deal_type": "sale",
            "price_eur": "180000",
            "area_sqm": "120",
            "city": "Бургас",
            "agent_id": agent.id,
            "floors": "1",
            "yard_sqm": "300",
            "has_garage": "1",
        }
    )
    assert isinstance(house, House)
    assert house.price_per_sqm == Decimal("1500.00")
    assert house.has_garage is True
    assert house.yard_sqm == Decimal("300.00")
