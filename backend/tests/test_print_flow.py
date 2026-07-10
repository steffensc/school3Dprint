"""End-to-end DummyDriver flow (Section 17): upload -> approve -> slice ->
enqueue -> start print -> printer finishes -> job reflects FINISHED.

This is the primary end-to-end-testable milestone called out in Phase 6 of
the implementation plan, since real hardware (BambuLanDriver) can't be
exercised in this sandbox.
"""

from __future__ import annotations

import io
import time

from app.models.user import User


def _create_dummy_printer(client_as, admin_user: User) -> str:
    response = client_as(admin_user).post(
        "/api/admin/printers",
        json={"name": "Test Dummy Printer", "driver_type": "DUMMY"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _upload_approve_slice_enqueue(
    client_as, admin_user: User, normal_user: User, fake_slicer
) -> str:
    data = b"schoolprint-test".ljust(80, b"\0") + (0).to_bytes(4, "little")
    upload = client_as(normal_user).post(
        "/api/user/uploads",
        data={"title": "E2E Robot"},
        files={"file": ("robot.stl", io.BytesIO(data), "application/octet-stream")},
    )
    job_id = upload.json()["id"]
    client_as(admin_user).post(f"/api/admin/jobs/{job_id}/approve")
    client_as(admin_user).post(f"/api/admin/jobs/{job_id}/slice")
    client_as(admin_user).post(f"/api/admin/jobs/{job_id}/enqueue")
    return job_id


def test_full_dummy_driver_print_flow_reaches_finished(
    client_as,
    admin_user: User,
    normal_user: User,
    tmp_storage,
    fake_slicer,
    fast_dummy_driver,
) -> None:
    printer_id = _create_dummy_printer(client_as, admin_user)
    job_id = _upload_approve_slice_enqueue(client_as, admin_user, normal_user, fake_slicer)

    start = client_as(admin_user).post(
        f"/api/admin/jobs/{job_id}/start-print", json={"printer_id": printer_id}
    )
    assert start.status_code == 200
    body = start.json()
    assert body["status"] == "PRINTING"
    assert body["queue_position"] is None

    live = client_as(admin_user).get(f"/api/admin/jobs/{job_id}/live-status")
    assert live.status_code == 200
    assert live.json()["status"] == "PRINTING"

    time.sleep(0.2)  # let the (fast) dummy print duration elapse

    finished = client_as(admin_user).get(f"/api/admin/jobs/{job_id}")
    assert finished.status_code == 200
    assert finished.json()["status"] == "FINISHED"

    student_view = client_as(normal_user).get(f"/api/user/jobs/{job_id}")
    assert student_view.json()["status"] == "FINISHED"


def test_pause_resume_and_cancel_print(
    client_as,
    admin_user: User,
    normal_user: User,
    tmp_storage,
    fake_slicer,
) -> None:
    printer_id = _create_dummy_printer(client_as, admin_user)
    job_id = _upload_approve_slice_enqueue(client_as, admin_user, normal_user, fake_slicer)

    client_as(admin_user).post(
        f"/api/admin/jobs/{job_id}/start-print", json={"printer_id": printer_id}
    )

    pause = client_as(admin_user).post(f"/api/admin/jobs/{job_id}/pause-print")
    assert pause.status_code == 200
    assert pause.json()["status"] == "PAUSED"

    resume = client_as(admin_user).post(f"/api/admin/jobs/{job_id}/resume-print")
    assert resume.status_code == 200
    assert resume.json()["status"] == "PRINTING"

    cancel = client_as(admin_user).post(f"/api/admin/jobs/{job_id}/cancel-print")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "CANCELLED"


def test_cannot_start_print_on_inactive_printer(
    client_as,
    admin_user: User,
    normal_user: User,
    tmp_storage,
    fake_slicer,
) -> None:
    printer_id = _create_dummy_printer(client_as, admin_user)
    client_as(admin_user).patch(
        f"/api/admin/printers/{printer_id}", json={"is_active": False}
    )
    job_id = _upload_approve_slice_enqueue(client_as, admin_user, normal_user, fake_slicer)

    response = client_as(admin_user).post(
        f"/api/admin/jobs/{job_id}/start-print", json={"printer_id": printer_id}
    )
    assert response.status_code == 502


def test_cannot_start_print_on_unknown_printer(
    client_as,
    admin_user: User,
    normal_user: User,
    tmp_storage,
    fake_slicer,
) -> None:
    job_id = _upload_approve_slice_enqueue(client_as, admin_user, normal_user, fake_slicer)

    response = client_as(admin_user).post(
        f"/api/admin/jobs/{job_id}/start-print",
        json={"printer_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


def test_non_admin_cannot_start_print(client_as, normal_user: User) -> None:
    response = client_as(normal_user).post(
        "/api/admin/jobs/00000000-0000-0000-0000-000000000000/start-print",
        json={"printer_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 403
