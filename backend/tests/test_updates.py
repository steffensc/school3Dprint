from __future__ import annotations

import httpx
import pytest

from app.models.user import User
from app.services import updater_runner


class _FakeResponse:
    def __init__(self, json_data: dict, status_code: int = 200) -> None:
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)  # type: ignore[arg-type]

    def json(self) -> dict:
        return self._json_data


def test_update_check_reports_available_update(
    client_as, admin_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_get(url: str, **kwargs):
        return _FakeResponse(
            {
                "tag_name": "v9.9.9",
                "html_url": "https://github.com/example-org/schoolprint/releases/tag/v9.9.9",
                "body": "Big new release",
                "published_at": "2026-01-01T00:00:00Z",
            }
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    response = client_as(admin_user).get("/api/admin/updates/check")
    assert response.status_code == 200
    body = response.json()
    assert body["update_available"] is True
    assert body["latest_version"] == "v9.9.9"
    assert body["release_url"].endswith("v9.9.9")
    assert body["error"] is None


def test_update_check_reports_no_update_when_current(
    client_as, admin_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_get(url: str, **kwargs):
        return _FakeResponse({"tag_name": "v0.1.0", "html_url": "", "body": ""})

    monkeypatch.setattr(httpx, "get", fake_get)

    response = client_as(admin_user).get("/api/admin/updates/check")
    assert response.status_code == 200
    body = response.json()
    assert body["update_available"] is False
    assert body["current_version"] == "0.1.0"


def test_update_check_handles_network_error_gracefully(
    client_as, admin_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_get(url: str, **kwargs):
        raise httpx.ConnectError("no route to host")

    monkeypatch.setattr(httpx, "get", fake_get)

    response = client_as(admin_user).get("/api/admin/updates/check")
    assert response.status_code == 200
    body = response.json()
    assert body["update_available"] is False
    assert body["latest_version"] is None
    assert body["error"] is not None


def test_install_update_succeeds_and_records_run(
    client_as, admin_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        updater_runner,
        "run_updater",
        lambda **kwargs: updater_runner.UpdaterResult(returncode=0, stdout="all good"),
    )

    response = client_as(admin_user).post("/api/admin/updates/install")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCEEDED"
    assert body["log"] == "all good"
    assert body["from_version"] == "0.1.0"

    status_response = client_as(admin_user).get("/api/admin/updates/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "SUCCEEDED"


def test_install_update_marks_failed_on_nonzero_exit(
    client_as, admin_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        updater_runner,
        "run_updater",
        lambda **kwargs: updater_runner.UpdaterResult(returncode=1, stdout="pull failed"),
    )

    response = client_as(admin_user).post("/api/admin/updates/install")
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"


def test_install_update_marks_failed_when_updater_service_unreachable(
    client_as, admin_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run_updater(**kwargs):
        raise updater_runner.UpdaterServiceUnavailableError("connection refused")

    monkeypatch.setattr(updater_runner, "run_updater", fake_run_updater)

    response = client_as(admin_user).post("/api/admin/updates/install")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert "connection refused" in body["log"]


def test_update_status_is_null_when_no_run_yet(client_as, admin_user: User) -> None:
    response = client_as(admin_user).get("/api/admin/updates/status")
    assert response.status_code == 200
    assert response.json() is None


def test_non_admin_cannot_access_update_endpoints(client_as, normal_user: User) -> None:
    assert client_as(normal_user).get("/api/admin/updates/check").status_code == 403
    assert client_as(normal_user).post("/api/admin/updates/install").status_code == 403
    assert client_as(normal_user).get("/api/admin/updates/status").status_code == 403
