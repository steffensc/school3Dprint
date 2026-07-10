"""ORM models.

Importing this package registers every model on `Base.metadata`, which is
required for Alembic autogenerate and for `Base.metadata.create_all()` in
tests.
"""

from app.models.audit_log import AuditLog
from app.models.print_job import PrintJob
from app.models.printer import Printer
from app.models.sliced_artifact import SlicedArtifact
from app.models.system_setting import SystemSetting
from app.models.update_run import UpdateRun
from app.models.uploaded_file import UploadedFile
from app.models.user import User

__all__ = [
    "AuditLog",
    "PrintJob",
    "Printer",
    "SlicedArtifact",
    "SystemSetting",
    "UpdateRun",
    "UploadedFile",
    "User",
]
