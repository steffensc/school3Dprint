from __future__ import annotations

from app.models.user import User


def test_admin_can_create_and_list_printer(client_as, admin_user: User) -> None:
    response = client_as(admin_user).post(
        "/api/admin/printers",
        json={"name": "Bambu A1 Mini #1", "driver_type": "DUMMY", "location": "Room 3"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Bambu A1 Mini #1"
    assert body["is_active"] is True
    assert body["has_access_code"] is False

    listing = client_as(admin_user).get("/api/admin/printers")
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_access_code_is_encrypted_and_not_exposed(client_as, admin_user: User) -> None:
    response = client_as(admin_user).post(
        "/api/admin/printers",
        json={
            "name": "Bambu A1 Mini #2",
            "driver_type": "BAMBU_LAN",
            "host": "10.0.0.5",
            "access_code": "12345678",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["has_access_code"] is True
    assert "access_code" not in body


def test_update_printer(client_as, admin_user: User) -> None:
    create = client_as(admin_user).post(
        "/api/admin/printers", json={"name": "Printer", "driver_type": "DUMMY"}
    )
    printer_id = create.json()["id"]

    update = client_as(admin_user).patch(
        f"/api/admin/printers/{printer_id}", json={"name": "Renamed", "is_active": False}
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Renamed"
    assert update.json()["is_active"] is False


def test_delete_printer(client_as, admin_user: User) -> None:
    create = client_as(admin_user).post(
        "/api/admin/printers", json={"name": "Printer", "driver_type": "DUMMY"}
    )
    printer_id = create.json()["id"]

    delete = client_as(admin_user).delete(f"/api/admin/printers/{printer_id}")
    assert delete.status_code == 204

    listing = client_as(admin_user).get("/api/admin/printers")
    assert listing.json() == []


def test_dummy_driver_connection_test_succeeds(client_as, admin_user: User) -> None:
    create = client_as(admin_user).post(
        "/api/admin/printers", json={"name": "Printer", "driver_type": "DUMMY"}
    )
    printer_id = create.json()["id"]

    response = client_as(admin_user).post(f"/api/admin/printers/{printer_id}/test-connection")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_non_admin_cannot_manage_printers(client_as, normal_user: User) -> None:
    response = client_as(normal_user).get("/api/admin/printers")
    assert response.status_code == 403
