"""
Tests for EventBus implementation.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch

from app.events.event_bus import EventBus, Subscription
from app.events.event_types import Event, EventTypes, EventSeverity


class TestSubscription:
    """Test Subscription class."""

    def test_subscription_creation(self):
        """Test creating a subscription."""
        handler = Mock()
        filters = {"severity": "error"}

        sub = Subscription(
            handler=handler,
            event_types={"generation.started"},
            priority=10,
            filters=filters
        )

        assert sub.handler == handler
        assert sub.event_types == {"generation.started"}
        assert sub.priority == 10
        assert sub.filters == filters

    def test_subscription_matches_event_type(self):
        """Test subscription matching by event type."""
        handler = Mock()
        sub = Subscription(
            handler=handler,
            event_types={"generation.started", "generation.completed"}
        )

        # Should match included types
        event1 = Event(type="generation.started")
        assert sub.matches(event1)

        event2 = Event(type="generation.completed")
        assert sub.matches(event2)

        # Should not match other types
        event3 = Event(type="order.created")
        assert not sub.matches(event3)

    def test_subscription_matches_wildcard(self):
        """Test subscription matching with wildcard."""
        handler = Mock()
        sub = Subscription(handler=handler, event_types={"*"})

        # Should match any event type
        event1 = Event(type="generation.started")
        assert sub.matches(event1)

        event2 = Event(type="order.created")
        assert sub.matches(event2)

    def test_subscription_filters(self):
        """Test subscription filtering."""
        handler = Mock()
        sub = Subscription(
            handler=handler,
            event_types={"*"},
            filters={"severity": EventSeverity.ERROR}
        )

        # Should match events with error severity
        error_event = Event(type="test", severity=EventSeverity.ERROR)
        assert sub.matches(error_event)

        # Should not match events with other severities
        info_event = Event(type="test", severity=EventSeverity.INFO)
        assert not sub.matches(info_event)

    def test_subscription_list_filters(self):
        """Test subscription filtering with lists."""
        handler = Mock()
        sub = Subscription(
            handler=handler,
            event_types={"*"},
            filters={"order_id": ["order1", "order2"]}
        )

        # Should match events with order_ids in the list
        event1 = Event(type="test", order_id="order1")
        assert sub.matches(event1)

        event2 = Event(type="test", order_id="order2")
        assert sub.matches(event2)

        # Should not match events with other order_ids
        event3 = Event(type="test", order_id="order3")
        assert not sub.matches(event3)

    def test_subscription_callable_filters(self):
        """Test subscription filtering with callable filters."""
        handler = Mock()
        sub = Subscription(
            handler=handler,
            event_types={"*"},
            filters={"order_id": lambda x: x and x.startswith("test_")}
        )

        # Should match events that pass the callable
        event1 = Event(type="test", order_id="test_123")
        assert sub.matches(event1)

        # Should not match events that don't pass
        event2 = Event(type="test", order_id="order_123")
        assert not sub.matches(event2)


class TestEventBus:
    """Test EventBus functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = EventBus(max_workers=2)

    def teardown_method(self):
        """Clean up after tests."""
        self.event_bus.shutdown()

    def test_event_bus_initialization(self):
        """Test event bus initialization."""
        assert len(self.event_bus._subscribers) == 0
        assert len(self.event_bus._middleware) == 0
        assert self.event_bus._max_history == 1000
        assert not self.event_bus._paused

    def test_subscribe_basic(self):
        """Test basic subscription."""
        handler = Mock()

        subscription = self.event_bus.subscribe(
            handler=handler,
            event_types=["generation.started"]
        )

        assert isinstance(subscription, Subscription)
        assert subscription.handler == handler
        assert "generation.started" in subscription.event_types
        assert len(self.event_bus._subscribers) == 1

    def test_subscribe_priority_ordering(self):
        """Test that subscribers are ordered by priority."""
        handler1 = Mock()
        handler2 = Mock()
        handler3 = Mock()

        # Subscribe with different priorities
        self.event_bus.subscribe(handler1, priority=10)
        self.event_bus.subscribe(handler2, priority=20)
        self.event_bus.subscribe(handler3, priority=5)

        # Should be ordered by priority (highest first)
        priorities = [s.priority for s in self.event_bus._subscribers]
        assert priorities == [20, 10, 5]

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        handler = Mock()
        subscription = self.event_bus.subscribe(handler)

        assert len(self.event_bus._subscribers) == 1

        # Unsubscribe
        result = self.event_bus.unsubscribe(subscription)
        assert result is True
        assert len(self.event_bus._subscribers) == 0

        # Try to unsubscribe again
        result = self.event_bus.unsubscribe(subscription)
        assert result is False

    def test_publish_sync(self):
        """Test synchronous event publishing."""
        handler = Mock()
        self.event_bus.subscribe(handler, event_types=["test.event"])

        event = Event(type="test.event", data={"key": "value"})
        self.event_bus.publish(event, async_=False)

        # Handler should be called
        handler.assert_called_once_with(event)

    def test_publish_async(self):
        """Test asynchronous event publishing."""
        handler = Mock()
        self.event_bus.subscribe(handler, event_types=["test.event"])

        event = Event(type="test.event", data={"key": "value"})
        self.event_bus.publish(event, async_=True)

        # Give async processing time to complete
        time.sleep(0.1)

        # Handler should be called
        handler.assert_called_once_with(event)

    def test_publish_with_filters(self):
        """Test publishing with subscription filters."""
        handler1 = Mock()
        handler2 = Mock()

        # Subscribe with different filters
        self.event_bus.subscribe(
            handler1,
            event_types=["test.event"],
            filters={"severity": EventSeverity.ERROR}
        )
        self.event_bus.subscribe(
            handler2,
            event_types=["test.event"],
            filters={"severity": EventSeverity.INFO}
        )

        # Publish error event
        error_event = Event(type="test.event", severity=EventSeverity.ERROR)
        self.event_bus.publish(error_event, async_=False)

        # Only handler1 should be called
        handler1.assert_called_once_with(error_event)
        handler2.assert_not_called()

    def test_middleware_processing(self):
        """Test middleware processing."""
        handler = Mock()
        middleware = Mock(side_effect=lambda event: event)  # Pass through

        self.event_bus.add_middleware(middleware)
        self.event_bus.subscribe(handler, event_types=["test.event"])

        event = Event(type="test.event")
        self.event_bus.publish(event, async_=False)

        # Middleware should be called
        middleware.assert_called_once_with(event)
        handler.assert_called_once()

    def test_middleware_filtering(self):
        """Test middleware filtering events."""
        handler = Mock()
        middleware = Mock(return_value=None)  # Filter out event

        self.event_bus.add_middleware(middleware)
        self.event_bus.subscribe(handler, event_types=["test.event"])

        event = Event(type="test.event")
        self.event_bus.publish(event, async_=False)

        # Middleware should be called, but handler should not
        middleware.assert_called_once_with(event)
        handler.assert_not_called()

    def test_error_handling_in_handlers(self):
        """Test error handling when handlers raise exceptions."""
        failing_handler = Mock(side_effect=Exception("Handler error"))
        working_handler = Mock()

        self.event_bus.subscribe(failing_handler, event_types=["test.event"])
        self.event_bus.subscribe(working_handler, event_types=["test.event"])

        event = Event(type="test.event")
        self.event_bus.publish(event, async_=False)

        # Both handlers should be called despite the exception
        failing_handler.assert_called_once()
        working_handler.assert_called_once()

    def test_convenience_methods(self):
        """Test convenience methods for common events."""
        handler = Mock()
        self.event_bus.subscribe(handler, event_types=["*"])

        # Test generation events
        self.event_bus.publish_generation_started("item_123", provider="replicate")
        self.event_bus.publish_generation_progress("item_123", 50, status="running")
        self.event_bus.publish_generation_completed("item_123", "product_456")
        self.event_bus.publish_generation_failed("item_123", "API timeout")

        # Should have called handler 4 times
        assert handler.call_count == 4

        # Check event types
        calls = handler.call_args_list
        assert calls[0][0][0].type == "generation.started"
        assert calls[1][0][0].type == "generation.progress"
        assert calls[2][0][0].type == "generation.completed"
        assert calls[3][0][0].type == "generation.failed"

    def test_event_history(self):
        """Test event history tracking."""
        event1 = Event(type="test.event1")
        event2 = Event(type="test.event2")

        self.event_bus.publish(event1, async_=False)
        self.event_bus.publish(event2, async_=False)

        history = self.event_bus.get_history()
        assert len(history) == 2
        assert history[0].type == "test.event1"
        assert history[1].type == "test.event2"

    def test_event_history_filtering(self):
        """Test event history filtering by type."""
        self.event_bus.publish(Event(type="test.event1"), async_=False)
        self.event_bus.publish(Event(type="test.event2"), async_=False)
        self.event_bus.publish(Event(type="test.event1"), async_=False)

        # Get history for specific type
        history = self.event_bus.get_history(event_type="test.event1")
        assert len(history) == 2
        assert all(e.type == "test.event1" for e in history)

    def test_event_history_limit(self):
        """Test event history size limit."""
        # Set small history limit
        self.event_bus._max_history = 3

        # Publish more events than the limit
        for i in range(5):
            self.event_bus.publish(Event(type=f"test.event{i}"), async_=False)

        history = self.event_bus.get_history()
        assert len(history) == 3
        # Should keep the most recent events
        assert history[0].type == "test.event2"
        assert history[1].type == "test.event3"
        assert history[2].type == "test.event4"

    def test_pause_resume(self):
        """Test pausing and resuming event processing."""
        handler = Mock()
        self.event_bus.subscribe(handler, event_types=["test.event"])

        # Pause event bus
        self.event_bus.pause()

        # Publish event while paused
        event = Event(type="test.event")
        self.event_bus.publish(event, async_=False)

        # Handler should not be called
        handler.assert_not_called()

        # Resume and publish again
        self.event_bus.resume()
        self.event_bus.publish(event, async_=False)

        # Handler should be called now
        handler.assert_called_once()

    def test_stats_tracking(self):
        """Test event statistics tracking."""
        self.event_bus.publish(Event(type="test.event1"), async_=False)
        self.event_bus.publish(Event(type="test.event2"), async_=False)
        self.event_bus.publish(Event(type="test.event1"), async_=False)

        stats = self.event_bus.get_stats()
        assert stats["test.event1"] == 2
        assert stats["test.event2"] == 1
        assert stats["total"] == 3

    def test_clear_history(self):
        """Test clearing event history and stats."""
        self.event_bus.publish(Event(type="test.event"), async_=False)

        assert len(self.event_bus.get_history()) == 1
        assert self.event_bus.get_stats()["total"] == 1

        self.event_bus.clear_history()

        assert len(self.event_bus.get_history()) == 0
        assert self.event_bus.get_stats()["total"] == 0

    def test_remove_middleware(self):
        """Test removing middleware."""
        middleware = Mock(side_effect=lambda x: x)

        self.event_bus.add_middleware(middleware)
        assert len(self.event_bus._middleware) == 1

        result = self.event_bus.remove_middleware(middleware)
        assert result is True
        assert len(self.event_bus._middleware) == 0

        # Try to remove again
        result = self.event_bus.remove_middleware(middleware)
        assert result is False