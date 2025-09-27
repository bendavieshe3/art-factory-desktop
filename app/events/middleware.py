"""
Event middleware for processing, enrichment, and sanitization.
"""

import re
import time
from typing import Optional, Dict, Any, List, Pattern
from uuid import uuid4

from .event_types import Event


class EventMiddleware:
    """Base class for event middleware."""

    def __call__(self, event: Event) -> Optional[Event]:
        """Process event. Return None to filter out the event."""
        return self.process(event)

    def process(self, event: Event) -> Optional[Event]:
        """Process the event. Override in subclasses."""
        return event


class SanitizationMiddleware(EventMiddleware):
    """
    Middleware to sanitize sensitive data from events.

    Removes or masks:
    - API keys and tokens
    - Passwords
    - Email addresses (optionally)
    - Personal information
    - File paths with user directories
    """

    # Patterns for sensitive data
    API_KEY_PATTERNS: List[Pattern] = [
        re.compile(r'(api[_-]?key|apikey|api_token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_]+)["\']?', re.IGNORECASE),
        re.compile(r'(token|auth|authorization)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_]+)["\']?', re.IGNORECASE),
        re.compile(r'Bearer\s+([a-zA-Z0-9\-_.]+)', re.IGNORECASE),
        re.compile(r'sk-[a-zA-Z0-9]{48}'),  # OpenAI keys
        re.compile(r'r8_[a-zA-Z0-9]{40}'),  # Replicate keys
    ]

    PASSWORD_PATTERNS: List[Pattern] = [
        re.compile(r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']+)["\']?', re.IGNORECASE),
    ]

    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    # User directory patterns
    USER_DIR_PATTERNS: List[Pattern] = [
        re.compile(r'/Users/[^/]+'),
        re.compile(r'/home/[^/]+'),
        re.compile(r'C:\\Users\\[^\\]+'),
    ]

    def __init__(self, sanitize_emails: bool = False, custom_patterns: List[Pattern] = None):
        self.sanitize_emails = sanitize_emails
        self.custom_patterns = custom_patterns or []

    def process(self, event: Event) -> Optional[Event]:
        """Sanitize sensitive data from event."""
        # Sanitize event data
        if event.data:
            event.data = self._sanitize_dict(event.data)

        # Sanitize context
        if event.context:
            event.context = self._sanitize_dict(event.context)

        # Sanitize error message
        if event.error_message:
            event.error_message = self._sanitize_string(event.error_message)

        return event

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values."""
        sanitized = {}
        for key, value in data.items():
            # Check if key itself suggests sensitive data
            if self._is_sensitive_key(key):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_value(item) for item in value
                ]
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize a single value."""
        if isinstance(value, dict):
            return self._sanitize_dict(value)
        elif isinstance(value, str):
            return self._sanitize_string(value)
        else:
            return value

    def _sanitize_string(self, text: str) -> str:
        """Sanitize sensitive data from string."""
        # API keys and tokens
        for pattern in self.API_KEY_PATTERNS:
            text = pattern.sub(r'\1=***REDACTED***', text)

        # Passwords
        for pattern in self.PASSWORD_PATTERNS:
            text = pattern.sub(r'\1=***REDACTED***', text)

        # Emails
        if self.sanitize_emails:
            text = self.EMAIL_PATTERN.sub('***EMAIL***', text)

        # User directories
        for pattern in self.USER_DIR_PATTERNS:
            text = pattern.sub('/***USER_DIR***', text)

        # Custom patterns
        for pattern in self.custom_patterns:
            text = pattern.sub('***REDACTED***', text)

        return text

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a dictionary key suggests sensitive data."""
        sensitive_keys = [
            'password', 'passwd', 'pwd', 'secret', 'token',
            'api_key', 'apikey', 'auth', 'authorization',
            'private_key', 'access_token', 'refresh_token'
        ]
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in sensitive_keys)


class EnrichmentMiddleware(EventMiddleware):
    """
    Middleware to enrich events with additional context.

    Adds:
    - Session ID (if not present)
    - Request ID (for correlation)
    - Timestamp precision
    - Source detection
    """

    def __init__(self):
        self.session_id = str(uuid4())
        self.request_counter = 0

    def process(self, event: Event) -> Optional[Event]:
        """Enrich event with additional context."""
        # Add session ID if not present
        if not event.session_id:
            event.session_id = self.session_id

        # Add request ID for new requests
        if event.type in ["order.created", "generation.started", "factory.api.request"]:
            if not event.request_id:
                self.request_counter += 1
                event.request_id = f"{self.session_id[:8]}-{self.request_counter:04d}"

        # Propagate request ID to related events
        if event.order_item_id and not event.request_id:
            # Try to get request ID from context
            event.request_id = event.context.get("request_id")

        # Add source if not present
        if not event.source:
            # Try to detect source from event type
            if event.type.startswith("factory."):
                event.source = "factory"
            elif event.type.startswith("generation."):
                event.source = "generation_service"
            elif event.type.startswith("order."):
                event.source = "order_service"
            elif event.type.startswith("user."):
                event.source = "ui"

        # Add processing timestamp
        event.context["processed_at"] = time.time()

        return event


class ThrottlingMiddleware(EventMiddleware):
    """
    Middleware to throttle high-frequency events.

    Useful for progress events that might flood the system.
    """

    def __init__(self, throttle_interval: float = 0.1):
        """
        Initialize throttling middleware.

        Args:
            throttle_interval: Minimum time between events (in seconds)
        """
        self.throttle_interval = throttle_interval
        self.last_event_times: Dict[str, float] = {}

    def process(self, event: Event) -> Optional[Event]:
        """Throttle events based on type and correlation ID."""
        # Only throttle progress events
        if "progress" not in event.type:
            return event

        # Create throttle key based on event type and correlation
        throttle_key = f"{event.type}:{event.order_item_id or event.order_id or 'global'}"

        # Check if we should throttle
        current_time = time.time()
        last_time = self.last_event_times.get(throttle_key, 0)

        if current_time - last_time < self.throttle_interval:
            # Throttle this event
            return None

        # Update last event time
        self.last_event_times[throttle_key] = current_time

        # Clean up old entries (older than 1 minute)
        cutoff_time = current_time - 60
        self.last_event_times = {
            k: v for k, v in self.last_event_times.items()
            if v > cutoff_time
        }

        return event


class FilteringMiddleware(EventMiddleware):
    """
    Middleware to filter events based on criteria.

    Can filter by:
    - Event type patterns
    - Severity levels
    - Source components
    """

    def __init__(
        self,
        include_types: List[str] = None,
        exclude_types: List[str] = None,
        min_severity: str = None,
        include_sources: List[str] = None,
        exclude_sources: List[str] = None
    ):
        self.include_types = set(include_types) if include_types else None
        self.exclude_types = set(exclude_types) if exclude_types else None
        self.min_severity = min_severity
        self.include_sources = set(include_sources) if include_sources else None
        self.exclude_sources = set(exclude_sources) if exclude_sources else None

    def process(self, event: Event) -> Optional[Event]:
        """Filter event based on configured criteria."""
        # Type filtering
        if self.include_types and event.type not in self.include_types:
            return None
        if self.exclude_types and event.type in self.exclude_types:
            return None

        # Source filtering
        if self.include_sources and event.source not in self.include_sources:
            return None
        if self.exclude_sources and event.source in self.exclude_sources:
            return None

        # Severity filtering
        if self.min_severity:
            severity_order = ["debug", "info", "warning", "error", "critical"]
            min_level = severity_order.index(self.min_severity.lower())
            event_level = severity_order.index(event.severity.value)
            if event_level < min_level:
                return None

        return event


class BatchingMiddleware(EventMiddleware):
    """
    Middleware to batch related events together.

    Useful for UI updates where multiple events should be processed together.
    """

    def __init__(self, batch_window: float = 0.5, batch_size: int = 10):
        """
        Initialize batching middleware.

        Args:
            batch_window: Time window for batching (seconds)
            batch_size: Maximum batch size
        """
        self.batch_window = batch_window
        self.batch_size = batch_size
        self.batches: Dict[str, List[Event]] = {}
        self.batch_timers: Dict[str, float] = {}

    def process(self, event: Event) -> Optional[Event]:
        """Batch events for processing."""
        # Only batch certain event types
        batchable_types = ["product.created", "generation.progress"]
        if event.type not in batchable_types:
            return event

        # Create batch key
        batch_key = f"{event.type}:{event.order_id or 'global'}"

        # Initialize batch if needed
        if batch_key not in self.batches:
            self.batches[batch_key] = []
            self.batch_timers[batch_key] = time.time()

        # Add to batch
        self.batches[batch_key].append(event)

        # Check if batch should be released
        batch_ready = (
            len(self.batches[batch_key]) >= self.batch_size or
            time.time() - self.batch_timers[batch_key] >= self.batch_window
        )

        if batch_ready:
            # Create batch event
            batch_event = Event(
                type=f"{event.type}.batch",
                data={"events": [e.to_dict() for e in self.batches[batch_key]]},
                context={"batch_size": len(self.batches[batch_key])}
            )

            # Clean up batch
            del self.batches[batch_key]
            del self.batch_timers[batch_key]

            return batch_event

        # Hold event for batching
        return None