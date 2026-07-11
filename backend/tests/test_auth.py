from __future__ import annotations

import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.services.user_service import bootstrap_initial_admin, get_user_by_username


def _csrf_headers(login_response: httpx.Response) -> dict[str, str]:
    return {"X-CSRF-Token": login_response.cookies["schoolprint_csrf"]}


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
    assert "schoolprint_csrf" in response.cookies


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
    login = client.post(
        "/api/auth/login", json={"username": "user_test", "password": "userpass123"}
    )
    client.post("/api/auth/logout", headers=_csrf_headers(login))
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_change_password_and_relogin(client: TestClient, normal_user) -> None:
    login = client.post(
        "/api/auth/login", json={"username": "user_test", "password": "userpass123"}
    )
    response = client.post(
        "/api/auth/change-password",
        json={"current_password": "userpass123", "new_password": "newpassword123"},
        headers=_csrf_headers(login),
    )
    assert response.status_code == 200
    client.post("/api/auth/logout", headers=_csrf_headers(login))

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


def test_mutating_request_without_csrf_token_is_rejected(
    client: TestClient, normal_user
) -> None:
    client.post("/api/auth/login", json={"username": "user_test", "password": "userpass123"})
    response = client.post("/api/auth/logout")
    assert response.status_code == 403


def test_mutating_request_with_wrong_csrf_token_is_rejected(
    client: TestClient, normal_user
) -> None:
    client.post("/api/auth/login", json={"username": "user_test", "password": "userpass123"})
    response = client.post("/api/auth/logout", headers={"X-CSRF-Token": "not-the-real-token"})
    assert response.status_code == 403


def test_get_requests_do_not_require_csrf_token(client: TestClient, normal_user) -> None:
    client.post("/api/auth/login", json={"username": "user_test", "password": "userpass123"})
    response = client.get("/api/auth/me")
    assert response.status_code == 200


def test_mutating_request_without_any_session_is_not_blocked_by_csrf(
    client: TestClient,
) -> None:
    """No session cookie at all (e.g. a stale/no-op request, or the
    role-based `client_as` test fixture) has nothing CSRF-relevant to
    protect, so it should fail auth (401), not CSRF (403)."""
    response = client.post("/api/auth/logout")
    assert response.status_code != 403
