"""Extracts estimated print time / filament usage from slicer-generated
G-code comments (Section 9.6).

OrcaSlicer (like PrusaSlicer/Slic3r before it) emits informational
comments such as::

    ; estimated printing time (normal mode) = 1h 23m 45s
    ; total filament used [g] = 12.34

We parse these best-effort; if they're missing (or the format drifts in
a future slicer version) callers just get `None` back instead of failing
the whole slice.
"""

from __future__ import annotations

import re

_TIME_PATTERN = re.compile(
    r"estimated printing time.*?=\s*(?:(\d+)d\s*)?(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)?",
    re.IGNORECASE,
)
_FILAMENT_PATTERN = re.compile(
    r"total filament used \[g\]\s*=\s*([0-9.]+)",
    re.IGNORECASE,
)


def parse_estimated_print_time_seconds(gcode_text: str) -> int | None:
    for line in gcode_text.splitlines():
        if "estimated printing time" not in line.lower():
            continue
        match = _TIME_PATTERN.search(line)
        if not match:
            continue
        days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
        total = days * 86400 + hours * 3600 + minutes * 60 + seconds
        if total > 0:
            return total
    return None


def parse_estimated_filament_grams(gcode_text: str) -> float | None:
    for line in gcode_text.splitlines():
        match = _FILAMENT_PATTERN.search(line)
        if match:
            return float(match.group(1))
    return None
