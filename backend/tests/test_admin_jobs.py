from __future__ import annotations

import io

from app.models.user import User


def _upload(client_as, user: User, title: str = "Test job"):
    data = b"schoolprint-test".ljust(80, b"\0") + (0).to_bytes(4, "little")
    response = client_as(user).post(
        "/api/user/uploads",
        data={"title": title},
        files={"file": ("model.stl", io.BytesIO(data), "application/octet-stream")},
    )
    assert response.status_code == 201
    return response.json()


def test_admin_can_approve_job(client_as, admin_user: User, normal_user: User, tmp_storage) -> None:
    job = _upload(client_as, normal_user)

    response = client_as(admin_user).post(
        f"/api/admin/jobs/{job['id']}/approve", json={"teacher_note": "Looks good"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "APPROVED"
    assert body["teacher_note"] == "Looks good"
    assert body["approved_at"] is not None

    my_job = client_as(normal_user).get(f"/api/user/jobs/{job['id']}")
    assert my_job.json()["status"] == "APPROVED"


def test_admin_can_reject_job(client_as, admin_user: User, normal_user: User, tmp_storage) -> None:
    job = _upload(client_as, normal_user)

    response = client_as(admin_user).post(
        f"/api/admin/jobs/{job['id']}/reject", json={"teacher_note": "Not printable"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["rejected_at"] is not None


def test_admin_can_unapprove_job(
    client_as, admin_user: User, normal_user: User, tmp_storage
) -> None:
    job = _upload(client_as, normal_user)
    client_as(admin_user).post(f"/api/admin/jobs/{job['id']}/approve")

    response = client_as(admin_user).post(f"/api/admin/jobs/{job['id']}/unapprove")
    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"


def test_cannot_approve_already_rejected_job(
    client_as, admin_user: User, normal_user: User, tmp_storage
) -> None:
    job = _upload(client_as, normal_user)
    client_as(admin_user).post(f"/api/admin/jobs/{job['id']}/reject")

    response = client_as(admin_user).post(f"/api/admin/jobs/{job['id']}/approve")
    assert response.status_code == 409


def test_non_admin_cannot_approve_job(
    client_as, normal_user: User, admin_user: User, tmp_storage
) -> None:
    job = _upload(client_as, normal_user)

    response = client_as(normal_user).post(f"/api/admin/jobs/{job['id']}/approve")
    assert response.status_code == 403


def test_approve_unknown_job_returns_404(client_as, admin_user: User) -> None:
    response = client_as(admin_user).post(
        "/api/admin/jobs/00000000-0000-0000-0000-000000000000/approve"
    )
    assert response.status_code == 404
