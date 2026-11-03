from flask import jsonify

from app.api import bp
from app.services.events import EventService

service = EventService()


@bp.get("/events")
def list_events():
    return jsonify([item.to_dict() for item in service.latest()])
