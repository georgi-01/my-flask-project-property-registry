import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_ENGINE", "sqlite")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "api.sqlite"))
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("RABBITMQ_ENABLED", "0")
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_seed_listings_include_price_and_area(client):
    response = client.get("/api/listings")
    assert response.status_code == 200
    body = response.get_json()
    assert len(body) >= 9
    kinds = {item["kind"] for item in body}
    assert kinds == {"apartment", "house"}
    sample = next(item for item in body if item["title"] == "Двустаен в Лозенец")
    assert sample["price_eur"] == 198000.0
    assert sample["price_per_sqm"] == 2538.46
    assert sample["rooms"] == 2


def test_api_creates_updates_and_deletes_house(client):
    agents = client.get("/api/agents").get_json()
    agent_id = agents[0]["id"]
    created = client.post(
        "/api/listings",
        json={
            "kind": "house",
            "title": "Къща край реката",
            "description": "Нова обява от теста.",
            "deal_type": "sale",
            "price_eur": 90000,
            "area_sqm": 100,
            "city": "Велико Търново",
            "address": "ул. Речна 1",
            "year_built": 1990,
            "status": "active",
            "agent_id": agent_id,
            "floors": 1,
            "yard_sqm": 250,
            "has_garage": False,
        },
    )
    assert created.status_code == 201
    house = created.get_json()
    assert house["kind"] == "house"
    assert house["price_per_sqm"] == 900.0
    assert house["yard_sqm"] == 250.0

    updated = client.put(
        f"/api/listings/{house['id']}",
        json={
            "title": "Къща край реката",
            "deal_type": "sale",
            "price_eur": 100000,
            "area_sqm": 100,
            "city": "Велико Търново",
            "status": "reserved",
            "agent_id": agent_id,
            "floors": 1,
            "yard_sqm": 250,
        },
    )
    assert updated.status_code == 200
    assert updated.get_json()["status"] == "reserved"
    assert updated.get_json()["price_per_sqm"] == 1000.0

    inquiry = client.post(
        f"/api/listings/{house['id']}/inquiries",
        json={"author_name": "Анна-Мария", "phone": "+359888111222", "message": "Свободна ли е в събота?"},
    )
    assert inquiry.status_code == 201

    removed = client.delete(f"/api/listings/{house['id']}")
    assert removed.status_code == 204
    missing = client.get(f"/api/listings/{house['id']}")
    assert missing.status_code == 404


def test_api_rejects_bad_listing(client):
    response = client.post("/api/listings", json={"kind": "apartment", "title": ""})
    assert response.status_code == 400
    assert response.get_json()["errors"]


def test_pages_render_catalog(client):
    page = client.get("/")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "Имотен регистър" in html
    assert "Двустаен в Лозенец" in html
    assert "€" in html
    catalog = client.get("/listings?kind=house")
    assert catalog.status_code == 200
    assert "Къща с двор в Бояна" in catalog.get_data(as_text=True)
    assert "Двустаен в Лозенец" not in catalog.get_data(as_text=True)


def test_duplicate_agent_email(client):
    response = client.post(
        "/api/agents",
        json={
            "name": "Нов Брокер",
            "phone": "+359888000000",
            "email": "maria.georgieva@imoti.bg",
            "office": "София",
        },
    )
    assert response.status_code == 400
    assert "имейл" in response.get_json()["errors"][0]
