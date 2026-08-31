import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
import models  # noqa: F401  - register every table before create_all
from app import app
from fastapi.testclient import TestClient

TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Fresh schema per test. These tests mutate lifetime PlayerStats
    totals, so leaking rows between them would make assertions depend on
    execution order."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def roster(client):
    """Four users, returned as the ids CreateGame would send:
    blue offense, blue defense, red offense, red defense."""
    ids = []
    for name in ("blue_off", "blue_def", "red_off", "red_def"):
        r = client.post("/users/", json={"name": name})
        assert r.status_code == 200, r.text
        ids.append(r.json()["id"])
    return ids


@pytest.fixture
def match(client, roster):
    r = client.post("/matches/start", json={
        "player1_id": roster[0], "player2_id": roster[1],
        "player3_id": roster[2], "player4_id": roster[3],
    })
    assert r.status_code == 200, r.text
    return r.json()
