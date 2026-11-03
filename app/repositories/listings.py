from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from app.models import Listing
from app.repositories.base import Repository


class ListingRepository(Repository):
    def get(self, listing_id):
        stmt = select(Listing).options(joinedload(Listing.agent)).where(Listing.id == listing_id)
        return self.session.scalars(stmt).unique().first()

    def search(self, filters=None):
        filters = filters or {}
        stmt = select(Listing).options(joinedload(Listing.agent)).order_by(Listing.created_at.desc(), Listing.id.desc())
        text = (filters.get("q") or "").strip()
        if text:
            pattern = f"%{text}%"
            stmt = stmt.where(or_(Listing.title.ilike(pattern), Listing.city.ilike(pattern), Listing.address.ilike(pattern)))
        if filters.get("city"):
            stmt = stmt.where(Listing.city.ilike(filters["city"].strip()))
        if filters.get("deal_type"):
            stmt = stmt.where(Listing.deal_type == filters["deal_type"])
        if filters.get("kind"):
            stmt = stmt.where(Listing.kind == filters["kind"])
        if filters.get("status"):
            stmt = stmt.where(Listing.status == filters["status"])
        if filters.get("min_price") is not None:
            stmt = stmt.where(Listing.price_eur >= filters["min_price"])
        if filters.get("max_price") is not None:
            stmt = stmt.where(Listing.price_eur <= filters["max_price"])
        if filters.get("agent_id"):
            stmt = stmt.where(Listing.agent_id == filters["agent_id"])
        return list(self.session.scalars(stmt).unique().all())

    def add(self, listing):
        self.session.add(listing)
        self.session.commit()
        self.session.refresh(listing)
        return listing

    def commit(self):
        self.session.commit()

    def delete(self, listing):
        self.session.delete(listing)
        self.session.commit()

    def counts_by_kind(self):
        rows = self.session.execute(select(Listing.kind, func.count()).group_by(Listing.kind)).all()
        return {kind: count for kind, count in rows}

    def count_for_agent(self, agent_id):
        return (
            self.session.scalar(select(func.count()).select_from(Listing).where(Listing.agent_id == agent_id)) or 0
        )
