"""
Base model with common fields for all database models.
"""

import uuid
from datetime import datetime
import json

from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr


Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model with common fields.

    Provides:
    - UUID primary key
    - created_at, updated_at timestamps
    - deleted_at for soft deletes
    - JSON field helpers for SQLite
    """

    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name."""
        name = cls.__name__
        # Convert CamelCase to snake_case
        import re

        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
        return name + "s"  # Pluralize

    def soft_delete(self):
        """Mark record as deleted."""
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None

    @property
    def is_deleted(self):
        """Check if record is soft deleted."""
        return self.deleted_at is not None

    def to_dict(self):
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif column.name.endswith("_json") and value:
                # Handle JSON fields stored as text in SQLite
                value = json.loads(value) if isinstance(value, str) else value
            result[column.name] = value
        return result

    @classmethod
    def create_from_dict(cls, data: dict):
        """Create model instance from dictionary."""
        # Handle JSON fields
        processed_data = {}
        for key, value in data.items():
            if (
                key.endswith("_json")
                and value is not None
                and not isinstance(value, str)
            ):
                processed_data[key] = json.dumps(value)
            else:
                processed_data[key] = value
        return cls(**processed_data)


# Helper function for JSON fields in SQLite


def create_json_field(field_name):
    """
    Create a JSON field property for SQLite.

    Usage in model:
        _settings_json = Column('settings_json', Text)
        settings = create_json_field('settings_json')
    """

    def getter(self):
        value = getattr(self, f"_{field_name}")
        if value and isinstance(value, str):
            return json.loads(value)
        return value

    def setter(self, value):
        if value is not None and not isinstance(value, str):
            value = json.dumps(value)
        setattr(self, f"_{field_name}", value)

    return property(getter, setter)
