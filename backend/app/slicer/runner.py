"""Subprocess wrapper around the OrcaSlicer CLI (Section 9.6 / 15).

Security-sensitive: this runs on user-uploaded files, so we:
  - never build a shell command string (subprocess with a list, no
    `shell=True`)
  - always pass an explicit timeout
  - run in a throwaway per-job working directory, not the shared uploads
    directory
  - use fixed, non-user-editable profile files (see
    `app/slicer/profiles/README.md`)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()

PRINTER_PROFILE = settings.slicer_profiles_dir / "bambu_a1_mini_printer.json"
PRINT_PROFILE = settings.slicer_profiles_dir / "bambu_a1_mini_0.4n_print.json"
FILAMENT_PROFILE = settings.slicer_profiles_dir / "generic_pla_filament.json"


class SlicerExecutionError(Exception):
    """The slicer process ran but exited non-zero."""

    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        message = f"Slicer exited with code {returncode}: {stderr.strip() or stdout.strip()}"
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class SlicerTimeoutError(Exception):
    """The slicer process did not finish within `slicer_timeout_seconds`."""


class SlicerBinaryNotFoundError(Exception):
    """The configured slicer binary could not be executed at all."""


def build_slice_command(input_stl: Path, output_3mf: Path) -> list[str]:
    """Builds the OrcaSlicer CLI invocation.

    Mirrors the documented headless workflow (`--load-settings`,
    `--load-filaments`, `--slice`, `--export-3mf`); see the design doc's
    references to the OrcaSlicer CLI discussions for the flag set this is
    based on.
    """
    return [
        settings.slicer_binary_path,
        "--load-settings",
        f"{PRINTER_PROFILE};{PRINT_PROFILE}",
        "--load-filaments",
        str(FILAMENT_PROFILE),
        "--slice",
        "1",
        "--export-3mf",
        str(output_3mf),
        str(input_stl),
    ]


def run_slicer(input_stl: Path, output_3mf: Path, *, timeout_seconds: int | None = None) -> str:
    """Runs the slicer and returns its combined stdout for logging.

    Raises `SlicerTimeoutError`, `SlicerExecutionError`, or
    `SlicerBinaryNotFoundError` on failure.
    """
    command = build_slice_command(input_stl, output_3mf)
    timeout = timeout_seconds or settings.slicer_timeout_seconds

    try:
        result = subprocess.run(  # noqa: S603 - fixed args list, no shell
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SlicerBinaryNotFoundError(
            f"Slicer binary '{settings.slicer_binary_path}' not found."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise SlicerTimeoutError(
            f"Slicer did not finish within {timeout}s."
        ) from exc

    if result.returncode != 0:
        raise SlicerExecutionError(result.returncode, result.stdout, result.stderr)

    return result.stdout
