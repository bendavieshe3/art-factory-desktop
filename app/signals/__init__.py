"""Signal architecture for Art Factory application.

This module provides a centralized signal-based event system for communication
between different parts of the application. It includes:

- DomainSignals: Business domain events (orders, generations, products)
- UISignals: User interface interaction events
- SignalBus: Singleton pattern for centralized signal management

Usage:
    from app.signals import signal_bus

    # Connect to a signal
    signal_bus.domain.order_created.connect(my_handler)

    # Emit a signal
    signal_bus.domain.order_created.emit("order_123")
"""

from .domain_signals import DomainSignals
from .ui_signals import UISignals
from .signal_bus import SignalBus, signal_bus

__all__ = ["DomainSignals", "UISignals", "SignalBus", "signal_bus"]
