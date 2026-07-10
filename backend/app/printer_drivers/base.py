"""The `PrinterDriver` interface (Section 9.7 / 12).

Every printer backend (Dummy, Bambu LAN, ...) implements this same
interface, so the rest of the app (queue/print service, API routes)
never needs to know which concrete driver it's talking to.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.models.printer import Printer


class PrinterStatus(str, enum.Enum):
    OFFLINE = "OFFLINE"
    IDLE = "IDLE"
    PRINTING = "PRINTING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


@dataclass
class Temperatures:
    nozzle_actual: float
    nozzle_target: float
    bed_actual: float
    bed_target: float


class PrinterDriverError(Exception):
    pass


class PrinterConnectionError(PrinterDriverError):
    pass


class PrinterDriver(ABC):
    """Base class for all printer drivers.

    Instances are cheap and stateless from the app's point of view: they
    are constructed per-call from a `Printer` row and talk to whatever
    backing store/device holds the real state (the physical printer for
    real drivers, an in-memory simulation for `DummyDriver`).
    """

    def __init__(self, printer: Printer) -> None:
        self.printer = printer

    @abstractmethod
    def test_connection(self) -> bool:
        """Returns True if the printer is reachable and responsive."""

    @abstractmethod
    def upload_artifact(self, local_path: Path, remote_name: str) -> None:
        """Transfers a sliced file to the printer's storage."""

    @abstractmethod
    def start_print(self, remote_name: str) -> None:
        """Starts printing a previously uploaded file."""

    @abstractmethod
    def pause(self) -> None: ...

    @abstractmethod
    def resume(self) -> None: ...

    @abstractmethod
    def cancel_print(self) -> None: ...

    @abstractmethod
    def get_status(self) -> PrinterStatus: ...

    @abstractmethod
    def get_temperatures(self) -> Temperatures: ...

    @abstractmethod
    def get_progress(self) -> float:
        """Returns 0-100 percent progress of the current print, or 0 if idle."""
