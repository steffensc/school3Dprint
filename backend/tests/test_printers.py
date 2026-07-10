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
            "serial_number": "01P00A000000001",
            "access_code": "12345678",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["has_access_code"] is True
    assert "access_code" not in body


def test_bambu_lan_printer_requires_host_and_serial(client_as, admin_user: User) -> None:
    response = client_as(admin_user).post(
        "/api/admin/printers",
        json={"name": "Incomplete Bambu", "driver_type": "BAMBU_LAN"},
    )
    assert response.status_code == 400


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


def test_bambu_lan_connection_test_uses_real_driver(
    client_as, admin_user: User, monkeypatch
) -> None:
    """Even through the admin API, a `BAMBU_LAN` printer's connection test
    is routed to `BambuLanDriver` (mocked here at the MQTT layer, since a
    real Bambu A1 Mini isn't available in this sandbox)."""
    import app.printer_drivers.bambu_lan as bambu_lan_module

    class _AlwaysConnectsClient:
        def __init__(self, client_id=None):
            self.on_connect = None

        def username_pw_set(self, *a, **kw):
            pass

        def tls_set(self, **kw):
            pass

        def tls_insecure_set(self, *a):
            pass

        def connect(self, *a, **kw):
            pass

        def loop_start(self):
            if self.on_connect:
                self.on_connect(self, None, None, 0)

        def loop_stop(self):
            pass

        def disconnect(self):
            pass

    monkeypatch.setattr(bambu_lan_module.mqtt, "Client", _AlwaysConnectsClient)

    create = client_as(admin_user).post(
        "/api/admin/printers",
        json={
            "name": "Bambu via API",
            "driver_type": "BAMBU_LAN",
            "host": "10.0.0.7",
            "serial_number": "01P00A000000009",
            "access_code": "87654321",
        },
    )
    printer_id = create.json()["id"]

    response = client_as(admin_user).post(f"/api/admin/printers/{printer_id}/test-connection")
    assert response.status_code == 200
    assert response.json()["success"] is True
