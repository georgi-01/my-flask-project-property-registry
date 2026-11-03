from sqlalchemy import select

from app.models import ListingEvent
from app.repositories.base import Repository


class EventRepository(Repository):
    def add(self, event, listing_id, title, payload):
        row = ListingEvent(event=event, listing_id=listing_id, title=title, payload=payload)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def latest(self, limit=100):
        stmt = select(ListingEvent).order_by(ListingEvent.logged_at.desc(), ListingEvent.id.desc()).limit(limit)
        return list(self.session.scalars(stmt))
