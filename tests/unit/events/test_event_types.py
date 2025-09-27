"""
Tests for event types and Event class.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from app.events.event_types import Event, EventTypes, EventSeverity


class TestEvent:
    """Test Event class functionality."""

    def test_event_creation_defaults(self):
        """Test event creation with defaults."""
        event = Event(type=EventTypes.GENERATION_STARTED)

        assert event.type == EventTypes.GENERATION_STARTED
        assert event.id is not None
        assert len(event.id) == 36  # UUID format
        assert isinstance(event.timestamp, datetime)
        assert event.severity == EventSeverity.INFO
        assert event.source == ""
        assert event.data == {}
        assert event.context == {}

    def test_event_creation_with_data(self):
        """Test event creation with full data."""
        data = {"provider": "replicate", "model": "sdxl"}
        context = {"user_id": "123"}

        event = Event(
            type=EventTypes.GENERATION_STARTED,
            source="generation_service",
            severity=EventSeverity.DEBUG,
            order_id="order_123",
            order_item_id="item_456",
            data=data,
            context=context
        )

        assert event.type == EventTypes.GENERATION_STARTED
        assert event.source == "generation_service"
        assert event.severity == EventSeverity.DEBUG
        assert event.order_id == "order_123"
        assert event.order_item_id == "item_456"
        assert event.data == data
        assert event.context == context

    def test_event_correlation_fields(self):
        """Test all correlation fields."""
        event = Event(
            type=EventTypes.PRODUCT_CREATED,
            order_id="order_123",
            order_item_id="item_456",
            product_id="product_789",
            project_id="project_abc",
            session_id="session_def",
            request_id="request_ghi"
        )

        assert event.order_id == "order_123"
        assert event.order_item_id == "item_456"
        assert event.product_id == "product_789"
        assert event.project_id == "project_abc"
        assert event.session_id == "session_def"
        assert event.request_id == "request_ghi"

    def test_event_error_fields(self):
        """Test error-related fields."""
        event = Event(
            type=EventTypes.GENERATION_FAILED,
            severity=EventSeverity.ERROR,
            error_message="API timeout",
            error_type="TimeoutError",
            error_traceback="Traceback..."
        )

        assert event.error_message == "API timeout"
        assert event.error_type == "TimeoutError"
        assert event.error_traceback == "Traceback..."

    def test_event_string_representation(self):
        """Test event string representation."""
        event = Event(type=EventTypes.GENERATION_PROGRESS)
        event_str = str(event)

        assert "Event" in event_str
        assert EventTypes.GENERATION_PROGRESS in event_str
        assert event.id[:8] in event_str
        assert "info" in event_str.lower()

    def test_event_to_dict(self):
        """Test event to dictionary conversion."""
        event = Event(
            type=EventTypes.ORDER_CREATED,
            source="order_service",
            order_id="order_123",
            data={"provider": "replicate"},
            context={"user_action": True}
        )

        event_dict = event.to_dict()

        assert event_dict["id"] == event.id
        assert event_dict["type"] == EventTypes.ORDER_CREATED
        assert event_dict["source"] == "order_service"
        assert event_dict["order_id"] == "order_123"
        assert event_dict["data"] == {"provider": "replicate"}
        assert event_dict["context"] == {"user_action": True}
        assert event_dict["severity"] == "info"
        assert isinstance(event_dict["timestamp"], str)  # ISO format

    def test_event_with_correlation(self):
        """Test correlation ID updating."""
        event = Event(type=EventTypes.GENERATION_PROGRESS)

        # Update correlation IDs
        updated = event.with_correlation(
            order_id="order_123",
            order_item_id="item_456",
            session_id="session_789"
        )

        # Should be the same object (modified in place)
        assert updated is event
        assert event.order_id == "order_123"
        assert event.order_item_id == "item_456"
        assert event.session_id == "session_789"

    def test_event_timestamp_precision(self):
        """Test that event timestamps are precise."""
        event1 = Event(type=EventTypes.SYSTEM_STARTUP)
        event2 = Event(type=EventTypes.SYSTEM_STARTUP)

        # Should have different timestamps (even if created quickly)
        assert event1.timestamp != event2.timestamp

    def test_event_id_uniqueness(self):
        """Test that event IDs are unique."""
        events = [Event(type=EventTypes.USER_ACTION) for _ in range(100)]
        event_ids = [e.id for e in events]

        # All IDs should be unique
        assert len(set(event_ids)) == len(event_ids)


class TestEventTypes:
    """Test EventTypes constants."""

    def test_event_type_constants(self):
        """Test that event type constants are strings."""
        assert isinstance(EventTypes.GENERATION_STARTED, str)
        assert isinstance(EventTypes.ORDER_CREATED, str)
        assert isinstance(EventTypes.PRODUCT_CREATED, str)
        assert isinstance(EventTypes.FACTORY_VALIDATION_STARTED, str)

    def test_event_type_naming_convention(self):
        """Test event type naming follows conventions."""
        # Should follow domain.action pattern
        assert EventTypes.GENERATION_STARTED == "generation.started"
        assert EventTypes.ORDER_CREATED == "order.created"
        assert EventTypes.FACTORY_API_REQUEST == "factory.api.request"

    def test_event_type_coverage(self):
        """Test that we have event types for all major domains."""
        # Check we have events for each major domain
        generation_events = [
            EventTypes.GENERATION_STARTED,
            EventTypes.GENERATION_PROGRESS,
            EventTypes.GENERATION_COMPLETED,
            EventTypes.GENERATION_FAILED
        ]
        assert all(e.startswith("generation.") for e in generation_events)

        order_events = [
            EventTypes.ORDER_CREATED,
            EventTypes.ORDER_COMPLETED,
            EventTypes.ORDER_ITEM_CREATED
        ]
        assert all(e.startswith("order.") for e in order_events)

        factory_events = [
            EventTypes.FACTORY_VALIDATION_STARTED,
            EventTypes.FACTORY_API_REQUEST,
            EventTypes.FACTORY_API_RESPONSE
        ]
        assert all(e.startswith("factory.") for e in factory_events)


class TestEventSeverity:
    """Test EventSeverity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        assert EventSeverity.DEBUG.value == "debug"
        assert EventSeverity.INFO.value == "info"
        assert EventSeverity.WARNING.value == "warning"
        assert EventSeverity.ERROR.value == "error"
        assert EventSeverity.CRITICAL.value == "critical"

    def test_severity_ordering(self):
        """Test that severity levels can be compared."""
        severities = list(EventSeverity)
        severity_values = [s.value for s in severities]

        # Should be in logical order
        expected_order = ["debug", "info", "warning", "error", "critical"]
        assert severity_values == expected_order