"""Lightweight STL sanity checks (Section 9.3).

We deliberately don't do a full geometry parse/validation here (that's
the slicer's job in Phase 5) — just enough to reject obviously-broken or
mislabeled uploads early, without trusting the client-provided MIME type.
"""

from __future__ import annotations


class InvalidStlError(Exception):
    pass


def validate_stl_bytes(data: bytes) -> None:
    stripped = data.lstrip()
    if stripped[:5].lower() == b"solid":
        # ASCII STL: expect a matching "endsolid" somewhere in the file.
        if b"endsolid" not in data.lower():
            raise InvalidStlError("ASCII STL file is missing 'endsolid' terminator.")
        return

    if len(data) < 84:
        raise InvalidStlError("File is too small to be a valid binary STL file.")

    # Binary STL: 80-byte header, then a little-endian uint32 triangle
    # count, then exactly (count * 50) bytes of triangle data.
    triangle_count = int.from_bytes(data[80:84], byteorder="little", signed=False)
    expected_size = 84 + triangle_count * 50
    if expected_size != len(data):
        raise InvalidStlError(
            "Binary STL triangle count does not match file size; the file may be corrupt."
        )
