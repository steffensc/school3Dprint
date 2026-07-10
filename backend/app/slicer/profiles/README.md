# Slicer profiles

This directory holds the OrcaSlicer printer/print/filament profiles used
by the slicer service (Section 9.6 / 12).

For the MVP, exactly one combination is supported:

- `bambu_a1_mini_printer.json` — Bambu Lab A1 Mini printer profile
- `bambu_a1_mini_0.4n_print.json` — a conservative 0.4mm-nozzle print profile
- `generic_pla_filament.json` — a generic PLA filament profile

These are intentionally **not** user- or teacher-editable through the
web UI (Section 9.6): letting untrusted users tune slicer settings that
get fed into a subprocess is a needless attack surface, and a single
well-tested profile combination is enough for a school MVP.

The placeholder JSON files checked into this repo are minimal stand-ins.
Before printing on real hardware, export real profiles for your printer
from OrcaSlicer/Bambu Studio (Device > Printer/Filament/Process presets
-> Export) and replace these files, keeping the same filenames so
`SlicerSettings` in `app/slicer/service.py` doesn't need to change.
