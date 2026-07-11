from __future__ import annotations

from app.models.user import User


def test_non_admin_cannot_list_users(client_as, normal_user: User) -> None:
    c = client_as(normal_user)
    response = c.get("/api/admin/users")
    assert response.status_code == 403


def test_admin_can_list_users(client_as, admin_user: User, normal_user: User) -> None:
    c = client_as(admin_user)
    response = c.get("/api/admin/users")
    assert response.status_code == 200
    usernames = {u["username"] for u in response.json()}
    assert usernames == {"admin_test", "user_test"}


def test_admin_can_create_user(client_as, admin_user: User) -> None:
    c = client_as(admin_user)
    response = c.post(
        "/api/admin/users",
        json={
            "username": "new_student",
            "display_name": "New Student",
            "password": "somepassword1",
            "role": "USER",
            "class_name": "6b",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "new_student"
    assert body["class_name"] == "6b"


def test_admin_cannot_create_duplicate_username(
    client_as, admin_user: User, normal_user: User
) -> None:
    c = client_as(admin_user)
    response = c.post(
        "/api/admin/users",
        json={
            "username": "user_test",
            "display_name": "Duplicate",
            "password": "somepassword1",
            "role": "USER",
        },
    )
    assert response.status_code == 409


def test_admin_can_reset_password(client_as, admin_user: User, normal_user: User) -> None:
    c = client_as(admin_user)
    response = c.post(
        f"/api/admin/users/{normal_user.id}/reset-password",
        json={"new_password": "brandnewpassword1"},
    )
    assert response.status_code == 200


def test_admin_can_disable_and_enable_user(client_as, admin_user: User, normal_user: User) -> None:
    c = client_as(admin_user)
    disable_response = c.post(f"/api/admin/users/{normal_user.id}/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["is_active"] is False

    enable_response = c.post(f"/api/admin/users/{normal_user.id}/enable")
    assert enable_response.status_code == 200
    assert enable_response.json()["is_active"] is True


def test_get_unknown_user_returns_404(client_as, admin_user: User) -> None:
    c = client_as(admin_user)
    response = c.get("/api/admin/users/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
