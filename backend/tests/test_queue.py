from __future__ import annotations

import io

from app.models.user import User


def _upload_and_approve(client_as, admin_user: User, normal_user: User, title: str) -> str:
    data = b"schoolprint-test".ljust(80, b"\0") + (0).to_bytes(4, "little")
    upload_response = client_as(normal_user).post(
        "/api/user/uploads",
        data={"title": title},
        files={"file": (f"{title}.stl", io.BytesIO(data), "application/octet-stream")},
    )
    job_id = upload_response.json()["id"]
    client_as(admin_user).post(f"/api/admin/jobs/{job_id}/approve")
    return job_id


def test_enqueue_moves_job_to_queued(
    client_as, admin_user: User, normal_user: User, tmp_storage
) -> None:
    job_id = _upload_and_approve(client_as, admin_user, normal_user, "Job A")

    response = client_as(admin_user).post(f"/api/admin/jobs/{job_id}/enqueue")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "QUEUED"
    assert body["queue_position"] == 1


def test_cannot_enqueue_unapproved_job(
    client_as, admin_user: User, normal_user: User, tmp_storage
) -> None:
    data = b"schoolprint-test".ljust(80, b"\0") + (0).to_bytes(4, "little")
    upload_response = client_as(normal_user).post(
        "/api/user/uploads",
        data={"title": "Not approved"},
        files={"file": ("a.stl", io.BytesIO(data), "application/octet-stream")},
    )
    job_id = upload_response.json()["id"]

    response = client_as(admin_user).post(f"/api/admin/jobs/{job_id}/enqueue")
    assert response.status_code == 409


def test_queue_positions_are_sequential(
    client_as, admin_user: User, normal_user: User, tmp_storage
) -> None:
    job_a = _upload_and_approve(client_as, admin_user, normal_user, "Job A")
    job_b = _upload_and_approve(client_as, admin_user, normal_user, "Job B")
    job_c = _upload_and_approve(client_as, admin_user, normal_user, "Job C")

    for job_id in (job_a, job_b, job_c):
        client_as(admin_user).post(f"/api/admin/jobs/{job_id}/enqueue")

    response = client_as(admin_user).get("/api/admin/queue")
    assert response.status_code == 200
    positions = [job["queue_position"] for job in response.json()]
    assert positions == [1, 2, 3]


def test_remove_from_queue_renumbers_remaining_jobs(
    client_as, admin_user: User, normal_user: User, tmp_storage
) -> None:
    job_a = _upload_and_approve(client_as, admin_user, normal_user, "Job A")
    job_b = _upload_and_approve(client_as, admin_user, normal_user, "Job B")
    job_c = _upload_and_approve(client_as, admin_user, normal_user, "Job C")

    for job_id in (job_a, job_b, job_c):
        client_as(admin_user).post(f"/api/admin/jobs/{job_id}/enqueue")

    remove_response = client_as(admin_user).post(f"/api/admin/jobs/{job_b}/remove-from-queue")
    assert remove_response.status_code == 200
    assert remove_response.json()["status"] == "APPROVED"
    assert remove_response.json()["queue_position"] is None

    queue_response = client_as(admin_user).get("/api/admin/queue")
    remaining = queue_response.json()
    assert [job["id"] for job in remaining] == [job_a, job_c]
    assert [job["queue_position"] for job in remaining] == [1, 2]


def test_move_up_and_down(client_as, admin_user: User, normal_user: User, tmp_storage) -> None:
    job_a = _upload_and_approve(client_as, admin_user, normal_user, "Job A")
    job_b = _upload_and_approve(client_as, admin_user, normal_user, "Job B")
    job_c = _upload_and_approve(client_as, admin_user, normal_user, "Job C")

    for job_id in (job_a, job_b, job_c):
        client_as(admin_user).post(f"/api/admin/jobs/{job_id}/enqueue")

    response = client_as(admin_user).post(f"/api/admin/queue/{job_c}/move-up")
    assert response.status_code == 200
    ordered_ids = [job["id"] for job in response.json()]
    assert ordered_ids == [job_a, job_c, job_b]

    response = client_as(admin_user).post(f"/api/admin/queue/{job_a}/move-down")
    ordered_ids = [job["id"] for job in response.json()]
    assert ordered_ids == [job_c, job_a, job_b]


def test_move_up_at_top_is_noop(
    client_as, admin_user: User, normal_user: User, tmp_storage
) -> None:
    job_a = _upload_and_approve(client_as, admin_user, normal_user, "Job A")
    job_b = _upload_and_approve(client_as, admin_user, normal_user, "Job B")

    for job_id in (job_a, job_b):
        client_as(admin_user).post(f"/api/admin/jobs/{job_id}/enqueue")

    response = client_as(admin_user).post(f"/api/admin/queue/{job_a}/move-up")
    assert response.status_code == 200
    assert [job["id"] for job in response.json()] == [job_a, job_b]


def test_reorder_queue_full_permutation(
    client_as, admin_user: User, normal_user: User, tmp_storage
) -> None:
    job_a = _upload_and_approve(client_as, admin_user, normal_user, "Job A")
    job_b = _upload_and_approve(client_as, admin_user, normal_user, "Job B")
    job_c = _upload_and_approve(client_as, admin_user, normal_user, "Job C")

    for job_id in (job_a, job_b, job_c):
        client_as(admin_user).post(f"/api/admin/jobs/{job_id}/enqueue")

    response = client_as(admin_user).post(
        "/api/admin/queue/reorder", json={"ordered_job_ids": [job_c, job_a, job_b]}
    )
    assert response.status_code == 200
    assert [job["id"] for job in response.json()] == [job_c, job_a, job_b]


def test_reorder_rejects_mismatched_job_set(
    client_as, admin_user: User, normal_user: User, tmp_storage
) -> None:
    job_a = _upload_and_approve(client_as, admin_user, normal_user, "Job A")
    client_as(admin_user).post(f"/api/admin/jobs/{job_a}/enqueue")

    response = client_as(admin_user).post(
        "/api/admin/queue/reorder",
        json={"ordered_job_ids": ["00000000-0000-0000-0000-000000000000"]},
    )
    assert response.status_code == 409


def test_user_sees_queue_position(
    client_as, admin_user: User, normal_user: User, tmp_storage
) -> None:
    job_id = _upload_and_approve(client_as, admin_user, normal_user, "Job A")
    client_as(admin_user).post(f"/api/admin/jobs/{job_id}/enqueue")

    response = client_as(normal_user).get(f"/api/user/jobs/{job_id}")
    assert response.json()["queue_position"] == 1


def test_non_admin_cannot_view_queue(client_as, normal_user: User) -> None:
    response = client_as(normal_user).get("/api/admin/queue")
    assert response.status_code == 403
