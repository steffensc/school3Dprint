from __future__ import annotations

from pydantic import BaseModel, Field


class UploadForm(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    student_note: str | None = Field(default=None, max_length=2000)
