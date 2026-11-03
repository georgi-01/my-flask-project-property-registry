from flask import render_template

from app.pages import bp
from app.services.events import EventService

events = EventService()


@bp.route("/journal")
def journal():
    return render_template("journal.html", events=events.latest())
