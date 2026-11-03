from flask import Blueprint, jsonify

bp = Blueprint("api", __name__, url_prefix="/api")


def errors(status, *messages):
    return jsonify(errors=list(messages)), status


from app.api import agents, events, inquiries, listings  # noqa: E402,F401
