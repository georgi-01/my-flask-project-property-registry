from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Agent, Apartment, House, now_utc


def seed_if_empty():
    session = db.SessionLocal()
    try:
        for agent in session.scalars(select(Agent).where(Agent.email.like("%@imoti.example"))):
            agent.email = agent.email.replace("@imoti.example", "@imoti.bg")
        existing = session.scalar(select(func.count()).select_from(Agent))
        if existing:
            session.commit()
            return
        maria = Agent(
            name="Мария Георгиева",
            phone="+359 88 410 2210",
            email="maria.georgieva@imoti.bg",
            office="София",
        )
        nikolay = Agent(
            name="Николай Петров",
            phone="+359 88 733 1045",
            email="nikolay.petrov@imoti.bg",
            office="Пловдив",
        )
        elena = Agent(
            name="Елена Димитрова",
            phone="+359 88 922 0118",
            email="elena.dimitrova@imoti.bg",
            office="Варна",
        )
        session.add_all([maria, nikolay, elena])
        session.flush()
        rows = [
                Apartment(
                    title="Двустаен в Лозенец",
                    description="Южен апартамент след освежен санитарен възел, на тиха улица до парка.",
                    deal_type="sale",
                    price_eur=198000,
                    area_sqm=78,
                    city="София",
                    address="ул. „Цветна“ 12",
                    year_built=2014,
                    status="active",
                    agent=maria,
                    rooms=2,
                    floor=4,
                    total_floors=8,
                    has_elevator=True,
                    has_balcony=True,
                ),
                Apartment(
                    title="Тристаен в Капана",
                    description="Тухлена сграда с високи тавани и вътрешен двор. Подходящ и за офис.",
                    deal_type="sale",
                    price_eur=156000,
                    area_sqm=95,
                    city="Пловдив",
                    address="ул. „Райко Даскалов“ 8",
                    year_built=1936,
                    status="active",
                    agent=nikolay,
                    rooms=3,
                    floor=2,
                    total_floors=4,
                    has_elevator=False,
                    has_balcony=True,
                ),
                Apartment(
                    title="Тристаен с морска панорама",
                    description="Широка всекидневна към морето, гараж в цената не е включен.",
                    deal_type="sale",
                    price_eur=245000,
                    area_sqm=110,
                    city="Варна",
                    address="ул. „Никола Вапцаров“ 21",
                    year_built=2008,
                    status="active",
                    agent=elena,
                    rooms=3,
                    floor=7,
                    total_floors=10,
                    has_elevator=True,
                    has_balcony=True,
                ),
                Apartment(
                    title="Двустаен под наем в Младост",
                    description="Обзаведен, с такса за поддръжка извън наема. Свободен от 1-во число.",
                    deal_type="rent",
                    price_eur=780,
                    area_sqm=68,
                    city="София",
                    address="бул. „Александър Малинов“ 78",
                    year_built=1982,
                    status="active",
                    agent=maria,
                    rooms=2,
                    floor=6,
                    total_floors=8,
                    has_elevator=True,
                    has_balcony=True,
                ),
                Apartment(
                    title="Студио до ски лифта",
                    description="Готов за отдаване през сезона. Такса поддръжка към комплекса е отделно.",
                    deal_type="sale",
                    price_eur=89000,
                    area_sqm=46,
                    city="Банско",
                    address="ул. „Глазне“ 3",
                    year_built=2006,
                    status="reserved",
                    agent=nikolay,
                    rooms=1,
                    floor=3,
                    total_floors=5,
                    has_elevator=True,
                    has_balcony=True,
                ),
                House(
                    title="Къща с двор в Бояна",
                    description="Две нива, камина и отделен гараж. Дворът е равен, с плодни дървета.",
                    deal_type="sale",
                    price_eur=640000,
                    area_sqm=240,
                    city="София",
                    address="ул. „Панорама“ 4",
                    year_built=2011,
                    status="active",
                    agent=maria,
                    floors=2,
                    yard_sqm=650,
                    has_garage=True,
                ),
                House(
                    title="Къща в Беломорски",
                    description="Тиха улица, нуждае се от освежаване на фасадата. Има лятна кухня.",
                    deal_type="sale",
                    price_eur=210000,
                    area_sqm=160,
                    city="Пловдив",
                    address="ул. „Орехова гора“ 15",
                    year_built=1998,
                    status="active",
                    agent=nikolay,
                    floors=2,
                    yard_sqm=480,
                    has_garage=False,
                ),
                House(
                    title="Едноетажна къща в Сарафово",
                    description="Десет минути до плажа. Дворът е ограден, с място за втора кола.",
                    deal_type="sale",
                    price_eur=175000,
                    area_sqm=130,
                    city="Бургас",
                    address="кв. Сарафово, ул. „Лазур“ 9",
                    year_built=2004,
                    status="active",
                    agent=elena,
                    floors=1,
                    yard_sqm=320,
                    has_garage=True,
                ),
                House(
                    title="Къща под наем в Драгалевци",
                    description="Семеен наем за дълъг срок. Отопление на газ, двор без басейн.",
                    deal_type="rent",
                    price_eur=1800,
                    area_sqm=190,
                    city="София",
                    address="ул. „Боровец“ 2",
                    year_built=2001,
                    status="archived",
                    agent=maria,
                    floors=2,
                    yard_sqm=400,
                    has_garage=True,
                ),
            ]
        started = now_utc()
        for index, row in enumerate(rows):
            row.created_at = started - timedelta(minutes=index)
        session.add_all(rows)
        session.commit()
    except IntegrityError:
        session.rollback()
    finally:
        session.close()
