"""Version info exposed on the admin System page (Section 10.4) and used
by the update checker (Section 9.10) to compare against GitHub Releases.

Backend, frontend and container are built and released together, so they
share one version string (`app.__version__`) sourced from `pyproject.toml`
at build time; `git_commit` is best-effort (absent in slim production
images without a `.git` directory)."""

from __future__ import annotations

import subprocess
from functools import lru_cache

from app import __version__
from app.core.config import get_settings


@lru_cache
def get_git_commit() -> str | None:
    try:
        result = subprocess.run(  # noqa: S603, S607 - fixed args, no shell, no user input
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return None
    if result.returncode != 0:
        return None
    commit = result.stdout.strip()
    return commit or None


def get_backend_version() -> str:
    return __version__


def get_frontend_version() -> str:
    # Built and released in lockstep with the backend for the MVP.
    return __version__


def get_container_version() -> str:
    return __version__


def get_environment() -> str:
    return get_settings().environment
