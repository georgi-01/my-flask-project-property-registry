import os

from flask import g
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = None
SessionLocal = None


class Base(DeclarativeBase):
    pass


def get_database_url():
    if os.environ.get("DB_ENGINE", "postgres").lower() == "sqlite":
        path = os.environ.get("SQLITE_PATH", "imoti.db")
        return f"sqlite:///{path}"
    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        database=os.environ["PGDATABASE"],
    )


def init_engine(url=None):
    global engine, SessionLocal
    url = url or get_database_url()
    connect_args = {}
    if str(url).startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(url, connect_args=connect_args, future=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return engine


def get_session():
    if "db_session" not in g:
        if SessionLocal is None:
            init_engine()
        g.db_session = SessionLocal()
    return g.db_session


def close_db(exception=None):
    session = g.pop("db_session", None)
    if session is not None:
        if exception is not None:
            session.rollback()
        session.close()
