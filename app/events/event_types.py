"""
Event type definitions and Event class for the event bus system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from uuid import uuid4


class EventSeverity(Enum):
    """Severity levels for events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventTypes:
    """
    Centralized event type constants.

    Event naming convention:
    - domain.action (e.g., generation.started)
    - domain.entity.action (e.g., order.item.created)
    """

    # Generation pipeline events
    GENERATION_QUEUED = "generation.queued"
    GENERATION_STARTED = "generation.started"
    GENERATION_PROGRESS = "generation.progress"
    GENERATION_COMPLETED = "generation.completed"
    GENERATION_FAILED = "generation.failed"
    GENERATION_CANCELLED = "generation.cancelled"
    GENERATION_RETRY = "generation.retry"
    GENERATION_RESTORED = "generation.restored"

    # Order lifecycle events
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_COMPLETED = "order.completed"
    ORDER_FAILED = "order.failed"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_QUEUED = "order.queued"
    ORDER_ITEM_CREATED = "order.item.created"
    ORDER_ITEMS_CREATED = "order.items.created"
    ORDER_ITEMS_EXPANDED = "order.items.expanded"

    # Parameter validation and expansion events
    PARAMETER_EXPANSION = "parameter.expansion"
    EXPANSION_LIMIT_EXCEEDED = "parameter.expansion.limit_exceeded"
    VALIDATION_FAILED = "validation.failed"
    VALIDATION_WARNING = "validation.warning"

    # Product events
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    PRODUCT_LIKED = "product.liked"
    PRODUCT_UNLIKED = "product.unliked"
    PRODUCT_EXPORTED = "product.exported"
    PRODUCT_IMPORTED = "product.imported"

    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    PROJECT_ACTIVATED = "project.activated"
    PROJECT_ARCHIVED = "project.archived"

    # Factory events
    FACTORY_VALIDATION_STARTED = "factory.validation.started"
    FACTORY_VALIDATION_COMPLETED = "factory.validation.completed"
    FACTORY_VALIDATION_FAILED = "factory.validation.failed"
    FACTORY_GENERATION_STARTED = "factory.generation.started"
    FACTORY_API_REQUEST = "factory.api.request"
    FACTORY_API_RESPONSE = "factory.api.response"
    FACTORY_API_ERROR = "factory.api.error"

    # Performance events
    PERFORMANCE_TIMING = "performance.timing"
    PERFORMANCE_MEMORY = "performance.memory"
    PERFORMANCE_CACHE_HIT = "performance.cache.hit"
    PERFORMANCE_CACHE_MISS = "performance.cache.miss"

    # User action events
    USER_ACTION = "user.action"
    USER_NAVIGATION = "user.navigation"
    USER_PREFERENCE_CHANGED = "user.preference.changed"
    USER_SESSION_STARTED = "user.session.started"
    USER_SESSION_ENDED = "user.session.ended"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_CONFIG_CHANGED = "system.config.changed"
    SYSTEM_RECOVERY = "system.recovery"

    # Database events
    DATABASE_QUERY = "database.query"
    DATABASE_TRANSACTION_START = "database.transaction.start"
    DATABASE_TRANSACTION_COMMIT = "database.transaction.commit"
    DATABASE_TRANSACTION_ROLLBACK = "database.transaction.rollback"
    DATABASE_ERROR = "database.error"


@dataclass
class Event:
    """
    Base event structure for all application events.

    An event represents something that happened in the system and carries
    all necessary context for subscribers to process it appropriately.
    """

    # Required fields
    type: str  # Event type from EventTypes

    # Auto-generated fields
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Optional context fields
    source: str = ""  # Component/module that emitted the event
    severity: EventSeverity = EventSeverity.INFO

    # Correlation IDs for request tracing
    order_id: Optional[str] = None
    order_item_id: Optional[str] = None
    product_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None

    # Event data
    data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    # Error information (if applicable)
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    error_traceback: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the event."""
        return f"Event({self.type}, id={self.id[:8]}..., severity={self.severity.value})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "type": self.type,
            "source": self.source,
            "severity": self.severity.value,
            "order_id": self.order_id,
            "order_item_id": self.order_item_id,
            "product_id": self.product_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "data": self.data,
            "context": self.context,
            "error_message": self.error_message,
            "error_type": self.error_type,
        }

    def with_correlation(self, **kwargs) -> "Event":
        """
        Create a new event with updated correlation IDs.

        This is useful for maintaining correlation context across events.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self