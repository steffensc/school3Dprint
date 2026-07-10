"""The `PrintJob` status machine (Section 9.4).

Centralizing the allowed transitions here means every code path (admin
approval, queueing, slicing, printing) enforces the same rules instead of
each service re-deriving them.
"""

from __future__ import annotations

from app.models.enums import PrintJobStatus as S


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: S, target: S) -> None:
        super().__init__(f"Cannot move job from {current.value} to {target.value}")
        self.current = current
        self.target = target


ALLOWED_TRANSITIONS: dict[S, set[S]] = {
    S.SUBMITTED: {S.APPROVED, S.REJECTED},
    # A rejected job's uploaded file is still subject to retention
    # (Section 9.9: "REJECTED älter als retention_days_rejected -> Datei
    # löschen"), so REJECTED can move straight to DELETED once its file
    # has been cleaned up.
    S.REJECTED: {S.DELETED},
    S.APPROVED: {S.SUBMITTED, S.SLICING, S.QUEUED},
    S.SLICING: {S.SLICED, S.FAILED},
    S.SLICED: {S.QUEUED},
    S.QUEUED: {S.READY_TO_PRINT, S.APPROVED},
    S.READY_TO_PRINT: {S.PRINTING, S.QUEUED},
    S.PRINTING: {S.PAUSED, S.FINISHED, S.FAILED, S.CANCELLED},
    S.PAUSED: {S.PRINTING, S.CANCELLED},
    S.FINISHED: {S.EXPIRED, S.DELETED},
    S.FAILED: {S.EXPIRED, S.DELETED},
    S.CANCELLED: {S.EXPIRED, S.DELETED},
    S.EXPIRED: {S.DELETED},
    S.DELETED: set(),
}


def assert_transition_allowed(current: S, target: S) -> None:
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidStatusTransitionError(current, target)
