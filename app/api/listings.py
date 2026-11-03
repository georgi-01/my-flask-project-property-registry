from flask import jsonify, request, url_for

from app.api import bp, errors
from app.errors import ValidationError
from app.services.listings import ListingService

service = ListingService()


def read_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def not_found(listing_id):
    return errors(404, f"Няма обява с номер {listing_id}.")


def filters_from_request():
    return {
        "q": request.args.get("q", ""),
        "city": request.args.get("city", ""),
        "deal_type": request.args.get("deal_type", ""),
        "kind": request.args.get("kind", ""),
        "status": request.args.get("status", ""),
        "min_price": request.args.get("min_price", ""),
        "max_price": request.args.get("max_price", ""),
        "agent_id": request.args.get("agent_id", ""),
    }


@bp.get("/listings")
def list_listings():
    return jsonify([item.to_dict() for item in service.search(filters_from_request())])


@bp.get("/listings/<int:listing_id>")
def get_listing(listing_id):
    listing = service.get(listing_id)
    if listing is None:
        return not_found(listing_id)
    return jsonify(listing.to_dict())


@bp.post("/listings")
def create_listing():
    try:
        listing = service.create(read_body())
    except ValidationError as error:
        return errors(400, *error.args)
    return jsonify(listing.to_dict()), 201, {"Location": url_for("api.get_listing", listing_id=listing.id)}


@bp.put("/listings/<int:listing_id>")
def update_listing(listing_id):
    try:
        listing = service.update(listing_id, read_body())
    except ValidationError as error:
        return errors(400, *error.args)
    if listing is None:
        return not_found(listing_id)
    return jsonify(listing.to_dict())


@bp.delete("/listings/<int:listing_id>")
def delete_listing(listing_id):
    deleted = service.delete(listing_id)
    if deleted is None:
        return not_found(listing_id)
    return "", 204
