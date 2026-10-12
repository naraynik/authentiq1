# Import all models here for Alembic migrations discovery
from app.database.database import Base  # noqa
from app.models.user import User  # noqa
from app.models.manufacturer import Manufacturer  # noqa
from app.models.product import Product  # noqa
from app.models.scan import ScanHistory  # noqa
from app.models.location import LocationHistory  # noqa
from app.models.audit import AuditLog  # noqa
from app.models.issue import Issue  # noqa
from app.models.app_state import AppState  # noqa
