"""An in-memory, no-hardware printer driver used for the MVP end-to-end
flow before real drivers (BambuLanDriver) exist (Section 9.7).

State lives in a module-level dict keyed by printer id rather than in
the database: a `PrinterDriver` is supposed to represent the *device's*
state, and for a fake device that's exactly what an in-process dict is.
This does mean the simulated state resets on backend restart, which is
fine for a driver whose entire purpose is local testing/demos.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.printer_drivers.base import PrinterDriver, PrinterStatus, Temperatures

TARGET_NOZZLE_TEMP = 210.0
TARGET_BED_TEMP = 60.0


@dataclass
class _DummyState:
    status: PrinterStatus = PrinterStatus.IDLE
    current_file: str | None = None
    started_at: datetime | None = None
    elapsed_seconds_at_pause: float = 0.0
    duration_seconds: float = 0.0
    uploaded_files: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.duration_seconds:
            self.duration_seconds = get_settings().dummy_driver_print_duration_seconds


_STATE: dict[uuid.UUID, _DummyState] = {}


def reset_all_dummy_state() -> None:
    """Test helper: clears simulated state between test runs."""
    _STATE.clear()


class DummyDriver(PrinterDriver):
    def _state(self) -> _DummyState:
        return _STATE.setdefault(self.printer.id, _DummyState())

    def test_connection(self) -> bool:
        return True

    def upload_artifact(self, local_path: Path, remote_name: str) -> None:
        if not local_path.exists():
            raise FileNotFoundError(f"Artifact not found: {local_path}")
        self._state().uploaded_files.add(remote_name)

    def start_print(self, remote_name: str) -> None:
        state = self._state()
        if remote_name not in state.uploaded_files:
            raise ValueError(f"'{remote_name}' was not uploaded to this printer yet.")
        state.status = PrinterStatus.PRINTING
        state.current_file = remote_name
        state.started_at = datetime.now(UTC)
        state.elapsed_seconds_at_pause = 0.0

    def pause(self) -> None:
        state = self._state()
        if state.status != PrinterStatus.PRINTING:
            raise ValueError("Printer is not currently printing.")
        state.elapsed_seconds_at_pause = self._elapsed_seconds(state)
        state.status = PrinterStatus.PAUSED

    def resume(self) -> None:
        state = self._state()
        if state.status != PrinterStatus.PAUSED:
            raise ValueError("Printer is not paused.")
        state.started_at = datetime.now(UTC)
        state.status = PrinterStatus.PRINTING

    def cancel_print(self) -> None:
        state = self._state()
        state.status = PrinterStatus.IDLE
        state.current_file = None
        state.started_at = None
        state.elapsed_seconds_at_pause = 0.0

    def _elapsed_seconds(self, state: _DummyState) -> float:
        if state.status == PrinterStatus.PAUSED:
            return state.elapsed_seconds_at_pause
        if state.started_at is None:
            return 0.0
        running = (datetime.now(UTC) - state.started_at).total_seconds()
        return state.elapsed_seconds_at_pause + running

    def get_status(self) -> PrinterStatus:
        state = self._state()
        is_done = self._elapsed_seconds(state) >= state.duration_seconds
        if state.status == PrinterStatus.PRINTING and is_done:
            state.status = PrinterStatus.FINISHED
        return state.status

    def get_progress(self) -> float:
        state = self._state()
        if state.status == PrinterStatus.IDLE:
            return 0.0
        if self.get_status() == PrinterStatus.FINISHED:
            return 100.0
        elapsed = self._elapsed_seconds(state)
        return round(min(100.0, (elapsed / state.duration_seconds) * 100), 1)

    def get_temperatures(self) -> Temperatures:
        state = self._state()
        is_active = state.status in (PrinterStatus.PRINTING, PrinterStatus.PAUSED)
        return Temperatures(
            nozzle_actual=TARGET_NOZZLE_TEMP if is_active else 25.0,
            nozzle_target=TARGET_NOZZLE_TEMP if is_active else 0.0,
            bed_actual=TARGET_BED_TEMP if is_active else 22.0,
            bed_target=TARGET_BED_TEMP if is_active else 0.0,
        )
