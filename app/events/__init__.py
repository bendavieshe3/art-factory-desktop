"""
Event Architecture for Art Factory.

This module provides a centralized event bus system that enables:
- Single touch point for business events
- Multiple independent subscribers (logging, UI, metrics, history)
- Full context tracking for correlation
- Async processing for non-blocking operations
"""

from .event_bus import EventBus, event_bus
from .event_types import Event, EventTypes, EventSeverity

__all__ = [
    "EventBus",
    "event_bus",
    "Event",
    "EventTypes",
    "EventSeverity",
]