"""Central application configuration.

Settings are sourced from environment variables (and an optional `.env`
file) so the same code runs unmodified in local dev, CI, and the Podman
deployment on the Raspberry Pi.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SCHOOLPRINT_", extra="ignore")

    # General
    app_name: str = "SchoolPrint"
    environment: str = "development"
    school_name: str = "SchoolPrint"

    # Database
    database_url: str = "postgresql+psycopg://schoolprint:schoolprint@localhost:5432/schoolprint"

    # Auth
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 12
    session_cookie_name: str = "schoolprint_session"
    cookie_secure: bool = False

    # Storage (local filesystem, never DB blobs)
    storage_root: Path = Path("/var/lib/schoolprint")
    uploads_dirname: str = "uploads"
    sliced_dirname: str = "sliced"
    previews_dirname: str = "previews"
    backups_dirname: str = "backups"

    # Upload validation
    max_upload_size_mb: int = 50
    allowed_upload_extensions: tuple[str, ...] = (".stl",)

    # Slicer
    slicer_binary_path: str = "orcaslicer"
    slicer_profiles_dir: Path = Path(__file__).resolve().parent.parent / "slicer" / "profiles"
    slicer_timeout_seconds: int = 300

    # Retention defaults (also stored/overridable in system_settings table)
    retention_days_finished: int = 90
    retention_days_rejected: int = 30
    retention_days_failed: int = 30

    # Updates
    update_repo: str = "example-org/schoolprint"
    update_channel: str = "stable"

    @property
    def uploads_dir(self) -> Path:
        return self.storage_root / self.uploads_dirname

    @property
    def sliced_dir(self) -> Path:
        return self.storage_root / self.sliced_dirname

    @property
    def previews_dir(self) -> Path:
        return self.storage_root / self.previews_dirname

    @property
    def backups_dir(self) -> Path:
        return self.storage_root / self.backups_dirname


@lru_cache
def get_settings() -> Settings:
    return Settings()
