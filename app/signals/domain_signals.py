"""Domain signals for business events in Art Factory.

These signals represent core business domain events that occur during
application operation, such as order creation, generation progress,
and product management.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class DomainSignals(QObject):
    """Business domain event signals.

    Signals:
        order_created: Emitted when a new order is created
        order_items_expanded: Emitted when order items are expanded from parameters
        generation_started: Emitted when generation begins for an order item
        generation_progress: Emitted to report generation progress
        generation_completed: Emitted when generation finishes successfully
        product_created: Emitted when a new product is created
        product_liked: Emitted when a product is liked/favorited
        project_changed: Emitted when the active project changes

    Example:
        signals = DomainSignals()
        signals.order_created.connect(lambda id: print(f"Order {id} created"))
        signals.order_created.emit("order_123")
    """

    # Order lifecycle events
    order_created = pyqtSignal(str)  # order_id
    order_items_expanded = pyqtSignal(str, int)  # order_id, item_count

    # Generation lifecycle events
    generation_started = pyqtSignal(str)  # item_id
    generation_progress = pyqtSignal(str, int)  # item_id, percent (0-100)
    generation_completed = pyqtSignal(str)  # item_id
    generation_failed = pyqtSignal(str, str)  # item_id, error

    # Product events
    product_created = pyqtSignal(str)  # product_id
    product_liked = pyqtSignal(str)  # product_id
    product_deleted = pyqtSignal(str)  # product_id

    # Project events
    project_changed = pyqtSignal(str)  # project_id
    project_created = pyqtSignal(str)  # project_id
    project_deleted = pyqtSignal(str)  # project_id

    def __init__(self):
        """Initialize DomainSignals."""
        super().__init__()
