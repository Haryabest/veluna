"""Create all tables from models."""

from app.database.session import Base
from app.models import all_models  # noqa: F401

target_metadata = Base.metadata
