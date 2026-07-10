from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.services.user_service import bootstrap_initial_admin, get_user_by_username


def test_bootstrap_creates_first_admin(db_session: Session) -> None:
    result = bootstrap_initial_admin(db_session)
    assert result is not None
    admin, password = result
    assert admin.username == "admin"
    assert admin.role == UserRole.ADMIN
    assert len(password) > 0


def test_bootstrap_is_noop_when_users_exist(db_session: Session, normal_user) -> None:
    result = bootstrap_initial_admin(db_session)
    assert result is None
    assert get_user_by_username(db_session, "admin") is None


def test_login_success_sets_session_cookie(client: TestClient, normal_user) -> None:
    response = client.post(
        "/api/auth/login", json={"username": "user_test", "password": "userpass123"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "user_test"
    assert "schoolprint_session" in response.cookies


def test_login_wrong_password_returns_401(client: TestClient, normal_user) -> None:
    response = client.post(
        "/api/auth/login", json={"username": "user_test", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_login_unknown_user_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"username": "nobody", "password": "whatever123"}
    )
    assert response.status_code == 401


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_after_login(client: TestClient, normal_user) -> None:
    client.post("/api/auth/login", json={"username": "user_test", "password": "userpass123"})
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["username"] == "user_test"


def test_logout_clears_session(client: TestClient, normal_user) -> None:
    client.post("/api/auth/login", json={"username": "user_test", "password": "userpass123"})
    client.post("/api/auth/logout")
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_change_password_and_relogin(client: TestClient, normal_user) -> None:
    client.post("/api/auth/login", json={"username": "user_test", "password": "userpass123"})
    response = client.post(
        "/api/auth/change-password",
        json={"current_password": "userpass123", "new_password": "newpassword123"},
    )
    assert response.status_code == 200
    client.post("/api/auth/logout")

    old_login = client.post(
        "/api/auth/login", json={"username": "user_test", "password": "userpass123"}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login", json={"username": "user_test", "password": "newpassword123"}
    )
    assert new_login.status_code == 200


def test_disabled_user_cannot_login(client: TestClient, db_session: Session, normal_user) -> None:
    from app.services.user_service import set_user_active

    set_user_active(db_session, normal_user, is_active=False)
    response = client.post(
        "/api/auth/login", json={"username": "user_test", "password": "userpass123"}
    )
    assert response.status_code == 401
