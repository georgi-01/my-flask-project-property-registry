from app import events
from app.errors import ValidationError
from app.labels import DEAL_TYPES, KINDS, STATUSES
from app.models import Apartment, House
from app.parsing import as_bool, clean_text, optional_decimal, parse_decimal, parse_int
from app.repositories.agents import AgentRepository
from app.repositories.inquiries import InquiryRepository
from app.repositories.listings import ListingRepository


class ListingService:
    def __init__(self, repo=None, agents=None, inquiries=None, publisher=None):
        self.repo = repo or ListingRepository()
        self.agents = agents or AgentRepository()
        self.inquiries = inquiries or InquiryRepository()
        self.publisher = events.publish if publisher is None else publisher

    def get(self, listing_id):
        return self.repo.get(listing_id)

    def search(self, raw=None):
        return self.repo.search(self.filters(raw or {}))

    def counts(self):
        by_kind = self.repo.counts_by_kind()
        return {
            "listings": sum(by_kind.values()),
            "apartments": by_kind.get("apartment", 0),
            "houses": by_kind.get("house", 0),
            "agents": self.agents.count(),
            "inquiries": self.inquiries.count(),
        }

    def create(self, data):
        kind = clean_text(data.get("kind"))
        if kind not in KINDS:
            raise ValidationError("Изберете апартамент или къща.")
        cleaned = self.validate(data, kind)
        agent = self.agents.get(cleaned.pop("agent_id"))
        if agent is None:
            raise ValidationError("Изберете съществуващ брокер.")
        model = Apartment if kind == "apartment" else House
        listing = model(agent=agent, agent_id=agent.id, **cleaned)
        saved = self.repo.add(listing)
        self.publisher("listing.created", saved.to_dict())
        return saved

    def update(self, listing_id, data):
        listing = self.repo.get(listing_id)
        if listing is None:
            return None
        cleaned = self.validate(data, listing.kind)
        agent = self.agents.get(cleaned.pop("agent_id"))
        if agent is None:
            raise ValidationError("Изберете съществуващ брокер.")
        self.apply(listing, cleaned, agent)
        self.repo.commit()
        self.publisher("listing.updated", listing.to_dict())
        return listing

    def delete(self, listing_id):
        listing = self.repo.get(listing_id)
        if listing is None:
            return None
        payload = listing.to_dict()
        self.repo.delete(listing)
        self.publisher("listing.deleted", payload)
        return payload

    def filters(self, raw):
        filters = {
            "q": clean_text(raw.get("q")),
            "city": clean_text(raw.get("city")),
            "deal_type": clean_text(raw.get("deal_type")),
            "kind": clean_text(raw.get("kind")),
            "status": clean_text(raw.get("status")),
        }
        if filters["deal_type"] not in DEAL_TYPES:
            filters["deal_type"] = ""
        if filters["kind"] not in KINDS:
            filters["kind"] = ""
        if filters["status"] not in STATUSES:
            filters["status"] = ""
        filters["min_price"] = optional_decimal(raw.get("min_price"))
        filters["max_price"] = optional_decimal(raw.get("max_price"))
        agent_id = clean_text(raw.get("agent_id"))
        filters["agent_id"] = int(agent_id) if agent_id.isdigit() else None
        return filters

    def validate(self, data, kind):
        title = clean_text(data.get("title"))
        description = clean_text(data.get("description"))
        city = clean_text(data.get("city"))
        address = clean_text(data.get("address"))
        deal_type = clean_text(data.get("deal_type"))
        status = clean_text(data.get("status") or "active")
        errors = []
        if not title:
            errors.append("Въведете заглавие.")
        elif len(title) > 160:
            errors.append("Заглавието трябва да е до 160 знака.")
        if len(description) > 4000:
            errors.append("Описанието трябва да е до 4000 знака.")
        if deal_type not in DEAL_TYPES:
            errors.append("Изберете продажба или наем.")
        if status not in STATUSES:
            errors.append("Изберете статус.")
        if not city:
            errors.append("Въведете град.")
        elif len(city) > 80 or not all(char.isalpha() or char in " -" for char in city):
            errors.append("Градът може да съдържа само букви, интервали и тирета.")
        if len(address) > 200:
            errors.append("Адресът трябва да е до 200 знака.")
        if errors:
            raise ValidationError(*errors)

        price_eur = parse_decimal(data.get("price_eur"), "Цена", minimum=1, maximum=100000000)
        area_sqm = parse_decimal(data.get("area_sqm"), "Площ", minimum=1, maximum=100000)
        year_built = parse_int(data.get("year_built"), "Година на строеж", minimum=1850, maximum=2035, required=False)
        agent_id = parse_int(data.get("agent_id"), "Брокер", minimum=1)

        cleaned = {
            "title": title,
            "description": description,
            "deal_type": deal_type,
            "price_eur": price_eur,
            "area_sqm": area_sqm,
            "city": city,
            "address": address,
            "year_built": year_built,
            "status": status,
            "agent_id": agent_id,
        }
        if kind == "apartment":
            rooms = parse_int(data.get("rooms"), "Стаи", minimum=1, maximum=20)
            floor = parse_int(data.get("floor"), "Етаж", minimum=0, maximum=80)
            total_floors = parse_int(data.get("total_floors"), "Етажи в сградата", minimum=1, maximum=80)
            if floor > total_floors:
                raise ValidationError("Етажът не може да е над етажите на сградата.")
            cleaned.update(
                {
                    "rooms": rooms,
                    "floor": floor,
                    "total_floors": total_floors,
                    "has_elevator": as_bool(data.get("has_elevator")),
                    "has_balcony": as_bool(data.get("has_balcony")),
                }
            )
        else:
            floors = parse_int(data.get("floors"), "Етажи на къщата", minimum=1, maximum=8)
            yard_sqm = parse_decimal(data.get("yard_sqm"), "Двор", minimum=0, maximum=1000000)
            cleaned.update(
                {
                    "floors": floors,
                    "yard_sqm": yard_sqm,
                    "has_garage": as_bool(data.get("has_garage")),
                }
            )
        return cleaned

    def apply(self, listing, cleaned, agent):
        for field in (
            "title",
            "description",
            "deal_type",
            "price_eur",
            "area_sqm",
            "city",
            "address",
            "year_built",
            "status",
        ):
            setattr(listing, field, cleaned[field])
        listing.agent = agent
        if isinstance(listing, Apartment):
            for field in ("rooms", "floor", "total_floors", "has_elevator", "has_balcony"):
                setattr(listing, field, cleaned[field])
        elif isinstance(listing, House):
            for field in ("floors", "yard_sqm", "has_garage"):
                setattr(listing, field, cleaned[field])
