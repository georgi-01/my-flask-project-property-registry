import pytest


@pytest.fixture(autouse=True)
def disable_rabbit(monkeypatch):
    monkeypatch.setenv("RABBITMQ_ENABLED", "0")
