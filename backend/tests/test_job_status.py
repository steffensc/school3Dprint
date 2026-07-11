from __future__ import annotations

import pytest

from app.models.enums import PrintJobStatus as S
from app.services.job_status import InvalidStatusTransitionError, assert_transition_allowed


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (S.SUBMITTED, S.APPROVED),
        (S.SUBMITTED, S.REJECTED),
        (S.APPROVED, S.SUBMITTED),
        (S.APPROVED, S.QUEUED),
        (S.QUEUED, S.READY_TO_PRINT),
        (S.READY_TO_PRINT, S.PRINTING),
        (S.PRINTING, S.FINISHED),
        (S.PRINTING, S.FAILED),
    ],
)
def test_allowed_transitions(current: S, target: S) -> None:
    assert_transition_allowed(current, target)  # should not raise


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (S.SUBMITTED, S.QUEUED),
        (S.SUBMITTED, S.PRINTING),
        (S.REJECTED, S.APPROVED),
        (S.FINISHED, S.PRINTING),
        (S.DELETED, S.SUBMITTED),
    ],
)
def test_disallowed_transitions_raise(current: S, target: S) -> None:
    with pytest.raises(InvalidStatusTransitionError):
        assert_transition_allowed(current, target)
