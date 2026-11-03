import os
import socket

from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app import api, pages
from app.db import Base, close_db, init_engine
from app.formatting import format_ppm, format_price, format_sqm, format_when
from app.labels import DEAL_TYPES, EVENT_LABELS, KINDS, STATUSES
from app.seed import seed_if_empty


def create_app():
    load_dotenv()
    database = init_engine()
    Base.metadata.create_all(database)
    seed_if_empty()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    app.json.ensure_ascii = False
    app.json.compact = False
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    app.jinja_env.globals["hostname"] = socket.gethostname()
    app.jinja_env.globals["deal_types"] = DEAL_TYPES
    app.jinja_env.globals["kinds"] = KINDS
    app.jinja_env.globals["statuses"] = STATUSES
    app.jinja_env.globals["event_labels"] = EVENT_LABELS
    app.jinja_env.filters["price"] = format_price
    app.jinja_env.filters["ppm"] = format_ppm
    app.jinja_env.filters["sqm"] = format_sqm
    app.jinja_env.filters["when"] = format_when
    app.teardown_appcontext(close_db)
    app.register_blueprint(pages.bp)
    app.register_blueprint(api.bp)
    return app
