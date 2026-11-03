from flask import jsonify, request, url_for

from app.api import bp, errors
from app.errors import ValidationError
from app.services.inquiries import InquiryService

service = InquiryService()


def read_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def not_found(inquiry_id):
    return errors(404, f"Няма запитване с номер {inquiry_id}.")


@bp.get("/inquiries")
def list_inquiries():
    return jsonify([item.to_dict() for item in service.all()])


@bp.get("/listings/<int:listing_id>/inquiries")
def list_listing_inquiries(listing_id):
    return jsonify([item.to_dict() for item in service.for_listing(listing_id)])


@bp.post("/listings/<int:listing_id>/inquiries")
def create_inquiry(listing_id):
    try:
        inquiry = service.create(listing_id, read_body())
    except ValidationError as error:
        return errors(400, *error.args)
    if inquiry is None:
        return errors(404, f"Няма обява с номер {listing_id}.")
    return jsonify(inquiry.to_dict()), 201, {"Location": url_for("api.get_inquiry", inquiry_id=inquiry.id)}


@bp.get("/inquiries/<int:inquiry_id>")
def get_inquiry(inquiry_id):
    inquiry = service.get(inquiry_id)
    if inquiry is None:
        return not_found(inquiry_id)
    return jsonify(inquiry.to_dict())


@bp.put("/inquiries/<int:inquiry_id>")
def update_inquiry(inquiry_id):
    try:
        inquiry = service.update(inquiry_id, read_body())
    except ValidationError as error:
        return errors(400, *error.args)
    if inquiry is None:
        return not_found(inquiry_id)
    return jsonify(inquiry.to_dict())


@bp.delete("/inquiries/<int:inquiry_id>")
def delete_inquiry(inquiry_id):
    deleted = service.delete(inquiry_id)
    if deleted is None:
        return not_found(inquiry_id)
    return "", 204
