from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.models import Inquiry
from app.repositories.base import Repository


class InquiryRepository(Repository):
    def get(self, inquiry_id):
        stmt = select(Inquiry).options(joinedload(Inquiry.listing)).where(Inquiry.id == inquiry_id)
        return self.session.scalars(stmt).unique().first()

    def all(self):
        stmt = select(Inquiry).options(joinedload(Inquiry.listing)).order_by(Inquiry.created_at.desc(), Inquiry.id.desc())
        return list(self.session.scalars(stmt).unique().all())

    def for_listing(self, listing_id):
        stmt = (
            select(Inquiry)
            .where(Inquiry.listing_id == listing_id)
            .order_by(Inquiry.created_at.desc(), Inquiry.id.desc())
        )
        return list(self.session.scalars(stmt))

    def add(self, inquiry):
        self.session.add(inquiry)
        self.session.commit()
        self.session.refresh(inquiry)
        return inquiry

    def commit(self):
        self.session.commit()

    def delete(self, inquiry):
        self.session.delete(inquiry)
        self.session.commit()

    def count(self):
        return self.session.scalar(select(func.count()).select_from(Inquiry)) or 0
