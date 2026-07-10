from __future__ import annotations

from app.models.user import User


def test_admin_can_view_system_status(client_as, admin_user: User, tmp_storage) -> None:
    response = client_as(admin_user).get("/api/admin/system/status")
    assert response.status_code == 200
    body = response.json()
    assert body["cpu_percent"] >= 0
    assert body["ram_total_bytes"] > 0
    assert body["ram_used_bytes"] > 0
    assert body["disk_total_bytes"] > 0
    assert body["uptime_seconds"] >= 0


def test_admin_can_view_version_info(client_as, admin_user: User) -> None:
    response = client_as(admin_user).get("/api/admin/system/version")
    assert response.status_code == 200
    body = response.json()
    assert body["backend_version"]
    assert body["frontend_version"]
    assert body["container_version"]
    assert body["environment"]


def test_non_admin_cannot_view_system_endpoints(client_as, normal_user: User) -> None:
    assert client_as(normal_user).get("/api/admin/system/status").status_code == 403
    assert client_as(normal_user).get("/api/admin/system/version").status_code == 403
