"""Integration tests — require running PostgreSQL and Redis."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.models import User, UserRole

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vcm:vcm_pass@localhost:5432/vcm_test")

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db):
    user = User(
        username="test_admin",
        hashed_password=get_password_hash("Admin@1234"),
        role=UserRole.admin,
        is_active=True,
        full_name="Test Admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def viewer_user(db):
    user = User(
        username="test_viewer",
        hashed_password=get_password_hash("Viewer@1234"),
        role=UserRole.viewer,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def admin_token(client, admin_user):
    resp = client.post("/api/auth/login",
                       json={"username": "test_admin", "password": "Admin@1234"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture()
def viewer_token(client, viewer_user):
    resp = client.post("/api/auth/login",
                       json={"username": "test_viewer", "password": "Viewer@1234"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ── Health ────────────────────────────────────────────────

class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


# ── Auth ──────────────────────────────────────────────────

class TestAuth:

    def test_login_success(self, client, admin_user):
        resp = client.post("/api/auth/login",
                           json={"username": "test_admin", "password": "Admin@1234"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "admin"

    def test_login_wrong_password(self, client, admin_user):
        resp = client.post("/api/auth/login",
                           json={"username": "test_admin", "password": "WrongPass"})
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        resp = client.post("/api/auth/login",
                           json={"username": "nobody", "password": "pass"})
        assert resp.status_code == 401

    def test_me_returns_current_user(self, client, admin_token):
        resp = client.get("/api/auth/me",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "test_admin"

    def test_me_without_token_fails(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 403


# ── Users ─────────────────────────────────────────────────

class TestUsers:

    def test_admin_can_list_users(self, client, admin_token):
        resp = client.get("/api/users/",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_viewer_cannot_list_users(self, client, viewer_token):
        resp = client.get("/api/users/",
                          headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 403

    def test_admin_can_create_user(self, client, admin_token):
        resp = client.post("/api/users/",
                           json={"username": "newuser", "password": "Pass@123",
                                 "role": "viewer"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 201
        assert resp.json()["username"] == "newuser"

    def test_duplicate_username_rejected(self, client, admin_token, admin_user):
        resp = client.post("/api/users/",
                           json={"username": "test_admin", "password": "Pass@123"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 409


# ── Dashboard ─────────────────────────────────────────────

class TestDashboard:

    def test_summary_accessible_to_viewer(self, client, viewer_token):
        resp = client.get("/api/dashboard/summary",
                          headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_vcenters" in data
        assert "open_findings" in data

    def test_audit_log_requires_admin(self, client, viewer_token):
        resp = client.get("/api/dashboard/audit-log",
                          headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 403

    def test_audit_log_accessible_to_admin(self, client, admin_token):
        resp = client.get("/api/dashboard/audit-log",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200


# ── Settings / Patterns ───────────────────────────────────

class TestPatterns:

    def test_create_valid_pattern(self, client, admin_token):
        resp = client.post("/api/settings/patterns",
                           json={"name": "Web VMs", "pattern_type": "vm_name",
                                 "regex_pattern": r"^(WEB)-\d+",
                                 "description": "Matches WEB-01, WEB-02"},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 201

    def test_invalid_regex_rejected(self, client, admin_token):
        resp = client.post("/api/settings/patterns",
                           json={"name": "Bad Pattern", "pattern_type": "vm_name",
                                 "regex_pattern": r"[invalid("},
                           headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 400

    def test_viewer_can_list_patterns(self, client, viewer_token):
        resp = client.get("/api/settings/patterns",
                          headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_viewer_cannot_create_pattern(self, client, viewer_token):
        resp = client.post("/api/settings/patterns",
                           json={"name": "X", "pattern_type": "vm_name",
                                 "regex_pattern": r"^X"},
                           headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 403
