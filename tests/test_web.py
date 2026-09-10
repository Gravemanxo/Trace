from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app.database import Base, get_db
from app.main import app
from app.models import TimeEntry, WorkDay


@pytest.fixture
def web_client():
    test_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(test_engine)

    def override_db():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, test_engine
    app.dependency_overrides.clear()


def csrf(client: TestClient) -> str:
    client.get("/")
    return client.cookies.get("arbeitsraum_csrf")


def test_month_navigation_and_year_boundaries(web_client):
    client, _ = web_client
    december = client.get("/history?month=2026-12")
    assert december.status_code == 200
    assert "Dezember 2026" in december.text
    assert "/history?month=2027-01" in december.text
    january = client.get("/history?month=2027-01")
    assert "/history?month=2026-12" in january.text
    assert 'value="2027-01"' in january.text
    assert "Anzeigen" not in january.text


def test_check_in_and_check_out_transition(web_client, monkeypatch):
    client, test_engine = web_client
    token = csrf(client)
    monkeypatch.setattr(
        main_module,
        "now",
        lambda: datetime(2026, 9, 10, 8, 0, tzinfo=main_module.settings.timezone),
    )
    response = client.post("/check-in", data={"csrf_token": token}, follow_redirects=False)
    assert response.status_code == 303
    with Session(test_engine) as db:
        entry = db.scalar(select(TimeEntry))
        assert entry.start_time.hour == 8
        assert entry.end_time is None

    monkeypatch.setattr(
        main_module,
        "now",
        lambda: datetime(2026, 9, 10, 16, 30, tzinfo=main_module.settings.timezone),
    )
    dashboard = client.get("/")
    assert 'data-live-timer' in dashboard.text
    assert 'data-completed-seconds="0"' in dashboard.text
    response = client.post("/check-out", data={"csrf_token": token}, follow_redirects=False)
    assert response.status_code == 303
    with Session(test_engine) as db:
        day = db.scalar(select(WorkDay))
        assert day.entries[0].end_time.hour == 16
        assert day.entries[0].end_time.minute == 30


def test_csrf_and_security_headers(web_client):
    client, _ = web_client
    response = client.post("/check-in", data={}, follow_redirects=False)
    assert response.status_code == 403
    page = client.get("/")
    assert page.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
