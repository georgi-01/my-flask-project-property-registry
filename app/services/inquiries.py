from app import events
from app.errors import ValidationError
from app.models import Inquiry
from app.parsing import clean_text
from app.repositories.inquiries import InquiryRepository
from app.repositories.listings import ListingRepository
from app.services.agents import _person_name, _phone


class InquiryService:
    def __init__(self, repo=None, listings=None, publisher=None):
        self.repo = repo or InquiryRepository()
        self.listings = listings or ListingRepository()
        self.publisher = events.publish if publisher is None else publisher

    def get(self, inquiry_id):
        return self.repo.get(inquiry_id)

    def all(self):
        return self.repo.all()

    def for_listing(self, listing_id):
        return self.repo.for_listing(listing_id)

    def create(self, listing_id, data):
        listing = self.listings.get(listing_id)
        if listing is None:
            return None
        cleaned = self.validate(data)
        inquiry = Inquiry(listing_id=listing.id, listing=listing, **cleaned)
        saved = self.repo.add(inquiry)
        self.publisher(
            "inquiry.created",
            {
                "id": saved.id,
                "listing_id": listing.id,
                "title": listing.title,
                "author_name": saved.author_name,
            },
        )
        return saved

    def update(self, inquiry_id, data):
        inquiry = self.repo.get(inquiry_id)
        if inquiry is None:
            return None
        cleaned = self.validate(data)
        inquiry.author_name = cleaned["author_name"]
        inquiry.phone = cleaned["phone"]
        inquiry.message = cleaned["message"]
        self.repo.commit()
        title = inquiry.listing.title if inquiry.listing is not None else ""
        self.publisher(
            "inquiry.updated",
            {
                "id": inquiry.id,
                "listing_id": inquiry.listing_id,
                "title": title,
                "author_name": inquiry.author_name,
            },
        )
        return inquiry

    def delete(self, inquiry_id):
        inquiry = self.repo.get(inquiry_id)
        if inquiry is None:
            return None
        title = inquiry.listing.title if inquiry.listing is not None else ""
        payload = {
            "id": inquiry.id,
            "listing_id": inquiry.listing_id,
            "title": title,
            "author_name": inquiry.author_name,
        }
        self.repo.delete(inquiry)
        self.publisher("inquiry.deleted", payload)
        return payload

    def validate(self, data):
        author_name = clean_text(data.get("author_name"))
        phone = clean_text(data.get("phone"))
        message = clean_text(data.get("message"))
        errors = []
        if not author_name:
            errors.append("Въведете име.")
        elif len(author_name) > 120 or not _person_name(author_name):
            errors.append("Името може да съдържа само букви, интервали, тирета и апострофи.")
        if len(phone) < 6 or len(phone) > 40 or not _phone(phone):
            errors.append("Въведете телефон.")
        if len(message) < 5:
            errors.append("Съобщението трябва да е поне 5 знака.")
        elif len(message) > 2000:
            errors.append("Съобщението трябва да е до 2000 знака.")
        if errors:
            raise ValidationError(*errors)
        return {"author_name": author_name, "phone": phone, "message": message}
