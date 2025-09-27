"""
Core event bus implementation with pub/sub pattern.
"""

import asyncio
import logging
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Dict, List, Any, Optional, Set
import weakref

from PyQt6.QtCore import QObject, QThread

from .event_types import Event, EventSeverity


logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """Represents a subscription to the event bus."""

    handler: Callable[[Event], None]
    event_types: Set[str]
    priority: int = 0
    filters: Dict[str, Any] = None
    async_handler: bool = False
    weak_ref: bool = False  # Use weak reference for handler

    def __hash__(self):
        return id(self.handler)

    def matches(self, event: Event) -> bool:
        """Check if this subscription matches the given event."""
        # Check event type
        if "*" not in self.event_types and event.type not in self.event_types:
            return False

        # Apply filters
        if self.filters:
            for key, value in self.filters.items():
                event_value = getattr(event, key, None) if hasattr(event, key) else event.data.get(key)

                # Handle different filter types
                if isinstance(value, (list, tuple)):
                    if event_value not in value:
                        return False
                elif callable(value):
                    if not value(event_value):
                        return False
                else:
                    if event_value != value:
                        return False

        return True


class EventBus(QObject):
    """
    Central event bus for pub/sub communication.

    Features:
    - Multiple subscribers per event type
    - Priority-based subscription ordering
    - Event filtering
    - Async and sync handlers
    - Middleware support
    - Thread-safe operations
    """

    def __init__(self, max_workers: int = 4):
        super().__init__()
        self._subscribers: List[Subscription] = []
        self._middleware: List[Callable[[Event], Optional[Event]]] = []
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._stats = defaultdict(int)
        self._paused = False

    def subscribe(
        self,
        handler: Callable[[Event], None],
        event_types: Optional[List[str]] = None,
        priority: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        weak_ref: bool = False
    ) -> Subscription:
        """
        Subscribe to events.

        Args:
            handler: Function to call when event matches
            event_types: List of event types to subscribe to (or ["*"] for all)
            priority: Higher priority subscribers are called first
            filters: Additional filters to apply
            weak_ref: Use weak reference (for UI components that may be destroyed)

        Returns:
            Subscription object (can be used for unsubscribe)
        """
        if event_types is None:
            event_types = ["*"]

        subscription = Subscription(
            handler=handler,
            event_types=set(event_types),
            priority=priority,
            filters=filters or {},
            async_handler=asyncio.iscoroutinefunction(handler),
            weak_ref=weak_ref
        )

        with self._lock:
            self._subscribers.append(subscription)
            # Sort by priority (higher first)
            self._subscribers.sort(key=lambda s: s.priority, reverse=True)

        logger.debug(f"Subscribed {getattr(handler, '__name__', str(handler))} to events: {event_types}")
        return subscription

    def unsubscribe(self, subscription: Subscription) -> bool:
        """
        Unsubscribe from events.

        Args:
            subscription: Subscription to remove

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            try:
                self._subscribers.remove(subscription)
                logger.debug(f"Unsubscribed {getattr(subscription.handler, '__name__', str(subscription.handler))}")
                return True
            except ValueError:
                return False

    def publish(self, event: Event, async_: bool = True) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event: Event to publish
            async_: If True, process in background thread
        """
        if self._paused:
            logger.debug(f"Event bus paused, skipping event: {event.type}")
            return

        # Apply middleware
        for middleware in self._middleware:
            original_event = event
            event = middleware(event)
            if event is None:
                logger.debug(f"Event filtered by middleware: {original_event.type}")
                return

        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

            # Update stats
            self._stats[event.type] += 1
            self._stats["total"] += 1

        # Process event
        if async_ and not QThread.currentThread() == QThread.currentThread().thread():
            self._executor.submit(self._process_event, event)
        else:
            self._process_event(event)

    def _process_event(self, event: Event) -> None:
        """Process event by calling matching subscribers."""
        logger.debug(f"Processing event: {event}")

        # Find matching subscribers
        with self._lock:
            matching_subscribers = [
                sub for sub in self._subscribers
                if sub.matches(event)
            ]

        # Call handlers
        for subscription in matching_subscribers:
            try:
                if subscription.weak_ref:
                    # Handle weak references (for UI components)
                    handler = subscription.handler
                    if handler is None:
                        # Reference is dead, remove subscription
                        self.unsubscribe(subscription)
                        continue
                else:
                    handler = subscription.handler

                # Call handler
                if subscription.async_handler:
                    asyncio.create_task(handler(event))
                else:
                    handler(event)

            except Exception as e:
                logger.error(
                    f"Error in event handler {getattr(subscription.handler, '__name__', str(subscription.handler))}: {e}",
                    exc_info=True
                )
                # Publish error event (but avoid infinite recursion)
                if event.type != "system.error":
                    self.publish(Event(
                        type="system.error",
                        source="event_bus",
                        severity=EventSeverity.ERROR,
                        error_message=str(e),
                        error_type=type(e).__name__,
                        context={"original_event": event.type}
                    ), async_=False)

    def add_middleware(self, middleware: Callable[[Event], Optional[Event]]) -> None:
        """
        Add middleware to process events before subscribers.

        Middleware can:
        - Modify events (return modified event)
        - Filter events (return None to stop propagation)
        - Enrich events with additional context

        Args:
            middleware: Function that takes and returns an Event (or None)
        """
        with self._lock:
            self._middleware.append(middleware)
        logger.debug(f"Added middleware: {getattr(middleware, '__name__', str(middleware))}")

    def remove_middleware(self, middleware: Callable[[Event], Optional[Event]]) -> bool:
        """Remove middleware from the pipeline."""
        with self._lock:
            try:
                self._middleware.remove(middleware)
                return True
            except ValueError:
                return False

    # Convenience methods for common events

    def publish_generation_started(self, order_item_id: str, **kwargs) -> None:
        """Publish generation started event."""
        self.publish(Event(
            type="generation.started",
            order_item_id=order_item_id,
            data=kwargs
        ))

    def publish_generation_progress(
        self,
        order_item_id: str,
        progress: int,
        **kwargs
    ) -> None:
        """Publish generation progress event."""
        self.publish(Event(
            type="generation.progress",
            order_item_id=order_item_id,
            data={"progress": progress, **kwargs}
        ))

    def publish_generation_completed(
        self,
        order_item_id: str,
        product_id: str,
        **kwargs
    ) -> None:
        """Publish generation completed event."""
        self.publish(Event(
            type="generation.completed",
            order_item_id=order_item_id,
            product_id=product_id,
            data=kwargs
        ))

    def publish_generation_failed(
        self,
        order_item_id: str,
        error_message: str,
        **kwargs
    ) -> None:
        """Publish generation failed event."""
        self.publish(Event(
            type="generation.failed",
            order_item_id=order_item_id,
            severity=EventSeverity.ERROR,
            error_message=error_message,
            data=kwargs
        ))

    def publish_performance_timing(
        self,
        operation: str,
        duration: float,
        **kwargs
    ) -> None:
        """Publish performance timing event."""
        self.publish(Event(
            type="performance.timing",
            severity=EventSeverity.DEBUG,
            data={"operation": operation, "duration": duration, **kwargs}
        ))

    # Management methods

    def pause(self) -> None:
        """Pause event processing (useful for testing)."""
        self._paused = True
        logger.info("Event bus paused")

    def resume(self) -> None:
        """Resume event processing."""
        self._paused = False
        logger.info("Event bus resumed")

    def get_stats(self) -> Dict[str, int]:
        """Get event statistics."""
        with self._lock:
            stats = dict(self._stats)
            # Ensure total is always present
            if "total" not in stats:
                stats["total"] = 0
            return stats

    def get_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get recent event history."""
        with self._lock:
            history = self._event_history[-limit:]
            if event_type:
                history = [e for e in history if e.type == event_type]
            return history

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
            self._stats.clear()

    def shutdown(self) -> None:
        """Shutdown the event bus and cleanup resources."""
        logger.info("Shutting down event bus")
        self._executor.shutdown(wait=True)
        self.clear_history()
        with self._lock:
            self._subscribers.clear()
            self._middleware.clear()


# Global event bus instance
event_bus = EventBus()