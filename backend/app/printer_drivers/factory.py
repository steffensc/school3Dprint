"""Maps `Printer.driver_type` to a concrete `PrinterDriver` implementation."""

from __future__ import annotations

from app.models.enums import PrinterDriverType
from app.models.printer import Printer
from app.printer_drivers.base import PrinterDriver
from app.printer_drivers.dummy import DummyDriver


class UnsupportedDriverError(Exception):
    pass


def get_driver(printer: Printer) -> PrinterDriver:
    if printer.driver_type == PrinterDriverType.DUMMY:
        return DummyDriver(printer)
    if printer.driver_type == PrinterDriverType.BAMBU_LAN:
        from app.printer_drivers.bambu_lan import BambuLanDriver

        return BambuLanDriver(printer)

    raise UnsupportedDriverError(
        f"Driver type '{printer.driver_type.value}' is not supported. "
        "SchoolPrint deliberately doesn't support OctoPrint/Moonraker."
    )
