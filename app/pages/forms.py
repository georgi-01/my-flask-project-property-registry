from types import SimpleNamespace

from flask import flash


def namespace(data):
    return SimpleNamespace(**data)


def show_errors(error):
    for message in error.args:
        flash(message, "error")


def listing_from_form(form):
    return {
        "kind": form.get("kind", ""),
        "title": form.get("title", ""),
        "description": form.get("description", ""),
        "deal_type": form.get("deal_type", ""),
        "price_eur": form.get("price_eur", ""),
        "area_sqm": form.get("area_sqm", ""),
        "city": form.get("city", ""),
        "address": form.get("address", ""),
        "year_built": form.get("year_built", ""),
        "status": form.get("status", "active"),
        "agent_id": form.get("agent_id", ""),
        "rooms": form.get("rooms", ""),
        "floor": form.get("floor", ""),
        "total_floors": form.get("total_floors", ""),
        "has_elevator": form.get("has_elevator") == "1",
        "has_balcony": form.get("has_balcony") == "1",
        "floors": form.get("floors", ""),
        "yard_sqm": form.get("yard_sqm", ""),
        "has_garage": form.get("has_garage") == "1",
    }


def blank_listing():
    return namespace(
        {
            "kind": "apartment",
            "title": "",
            "description": "",
            "deal_type": "sale",
            "price_eur": "",
            "area_sqm": "",
            "city": "",
            "address": "",
            "year_built": "",
            "status": "active",
            "agent_id": "",
            "rooms": "",
            "floor": "",
            "total_floors": "",
            "has_elevator": False,
            "has_balcony": False,
            "floors": "",
            "yard_sqm": "",
            "has_garage": False,
        }
    )


def agent_from_form(form):
    return {
        "name": form.get("name", ""),
        "phone": form.get("phone", ""),
        "email": form.get("email", ""),
        "office": form.get("office", ""),
    }


def inquiry_from_form(form):
    return {
        "author_name": form.get("author_name", ""),
        "phone": form.get("phone", ""),
        "message": form.get("message", ""),
    }
