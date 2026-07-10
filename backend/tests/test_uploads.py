from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()


def _valid_binary_stl(triangle_count: int = 0) -> bytes:
    header = b"schoolprint-test-stl".ljust(80, b"\0")
    count_bytes = triangle_count.to_bytes(4, byteorder="little")
    triangles = b"\0" * (50 * triangle_count)
    return header + count_bytes + triangles


def _valid_ascii_stl() -> bytes:
    return b"solid test\nfacet normal 0 0 0\nendfacet\nendsolid test\n"


def test_user_can_upload_valid_stl(client_as, normal_user: User, tmp_storage) -> None:
    c = client_as(normal_user)
    response = c.post(
        "/api/user/uploads",
        data={"title": "My Robot"},
        files={"file": ("robot.stl", io.BytesIO(_valid_binary_stl()), "application/octet-stream")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "My Robot"
    assert body["status"] == "SUBMITTED"
    assert body["uploaded_file"]["original_filename"] == "robot.stl"

    stored_files = list((settings.uploads_dir).glob("*.stl"))
    assert len(stored_files) == 1


def test_user_can_upload_ascii_stl(client_as, normal_user: User, tmp_storage) -> None:
    c = client_as(normal_user)
    response = c.post(
        "/api/user/uploads",
        data={"title": "Ascii model"},
        files={"file": ("ascii.stl", io.BytesIO(_valid_ascii_stl()), "application/octet-stream")},
    )
    assert response.status_code == 201


def test_upload_rejects_non_stl_extension(client_as, normal_user: User, tmp_storage) -> None:
    c = client_as(normal_user)
    response = c.post(
        "/api/user/uploads",
        data={"title": "Not an STL"},
        files={"file": ("model.obj", io.BytesIO(b"not stl"), "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_rejects_corrupt_binary_stl(client_as, normal_user: User, tmp_storage) -> None:
    c = client_as(normal_user)
    corrupt = _valid_binary_stl(triangle_count=5)[:100]  # truncated, size won't match count
    response = c.post(
        "/api/user/uploads",
        data={"title": "Corrupt"},
        files={"file": ("broken.stl", io.BytesIO(corrupt), "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_rejects_empty_file(client_as, normal_user: User, tmp_storage) -> None:
    c = client_as(normal_user)
    response = c.post(
        "/api/user/uploads",
        data={"title": "Empty"},
        files={"file": ("empty.stl", io.BytesIO(b""), "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_rejects_oversized_file(
    client_as, normal_user: User, tmp_storage, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)
    c = client_as(normal_user)
    response = c.post(
        "/api/user/uploads",
        data={"title": "Too big"},
        files={"file": ("robot.stl", io.BytesIO(_valid_binary_stl()), "application/octet-stream")},
    )
    assert response.status_code == 400


def test_user_sees_only_own_jobs(
    client_as, normal_user: User, admin_user: User, tmp_storage
) -> None:
    # `client_as` mutates a shared dependency override on the same app/client,
    # so each identity switch must happen immediately before its request.
    client_as(normal_user).post(
        "/api/user/uploads",
        data={"title": "User job"},
        files={"file": ("a.stl", io.BytesIO(_valid_binary_stl()), "application/octet-stream")},
    )

    client_as(admin_user).post(
        "/api/user/uploads",
        data={"title": "Admin job"},
        files={"file": ("b.stl", io.BytesIO(_valid_binary_stl()), "application/octet-stream")},
    )

    response = client_as(normal_user).get("/api/user/jobs")
    assert response.status_code == 200
    titles = {job["title"] for job in response.json()}
    assert titles == {"User job"}


def test_admin_sees_all_jobs(client_as, normal_user: User, admin_user: User, tmp_storage) -> None:
    client_as(normal_user).post(
        "/api/user/uploads",
        data={"title": "User job"},
        files={"file": ("a.stl", io.BytesIO(_valid_binary_stl()), "application/octet-stream")},
    )

    response = client_as(admin_user).get("/api/admin/jobs")
    assert response.status_code == 200
    titles = {job["title"] for job in response.json()}
    assert titles == {"User job"}


def test_user_cannot_access_other_users_job(
    client_as, normal_user: User, admin_user: User, tmp_storage
) -> None:
    create_response = client_as(admin_user).post(
        "/api/user/uploads",
        data={"title": "Admin job"},
        files={"file": ("b.stl", io.BytesIO(_valid_binary_stl()), "application/octet-stream")},
    )
    job_id = create_response.json()["id"]

    response = client_as(normal_user).get(f"/api/user/jobs/{job_id}")
    assert response.status_code == 404


def test_uploads_require_authentication(client: TestClient, tmp_storage) -> None:
    response = client.post(
        "/api/user/uploads",
        data={"title": "Nope"},
        files={"file": ("a.stl", io.BytesIO(_valid_binary_stl()), "application/octet-stream")},
    )
    assert response.status_code == 401
