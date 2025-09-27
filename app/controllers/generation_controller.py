"""
Generation controller for managing AI generation workflow.
"""

from PyQt6.QtCore import pyqtSlot
from typing import Dict, Any, Optional
import logging

from .base_controller import BaseController
from signals.signal_bus import SignalBus


class GenerationController(BaseController):
    """Controller for managing AI generation workflow.

    Responsibilities:
    - Handle generation requests from parameter panel
    - Create orders using OrderService with parameter expansion
    - Coordinate generation progress tracking
    - Manage generation state and error handling
    - Update UI components with generation results
    """

    def __init__(self, signal_bus: SignalBus):
        """Initialize the generation controller."""
        super().__init__(signal_bus)
        self.logger = logging.getLogger(__name__)

        # Generation state
        self.active_orders: Dict[str, Dict[str, Any]] = {}
        self.generation_queue: list = []

        # Services (will be imported when needed to avoid circular imports)
        self._order_service = None
        self._generation_service = None

    def _connect_signals(self):
        """Connect generation controller signals."""
        # UI signals for generation requests
        self.signal_bus.ui.request_generation.connect(self._on_generation_requested)
        self.signal_bus.ui.request_cancel.connect(self._on_cancel_requested)
        self.signal_bus.ui.request_regenerate.connect(self._on_regenerate_requested)

        # Domain signals for generation lifecycle
        self.signal_bus.domain.order_created.connect(self._on_order_created)
        self.signal_bus.domain.generation_started.connect(self._on_generation_started)
        self.signal_bus.domain.generation_progress.connect(self._on_generation_progress)
        self.signal_bus.domain.generation_completed.connect(self._on_generation_completed)
        self.signal_bus.domain.generation_failed.connect(self._on_generation_failed)

    @property
    def order_service(self):
        """Lazy loading of OrderService to avoid circular imports."""
        if self._order_service is None:
            from ..services.order_service import OrderService

            self._order_service = OrderService()
        return self._order_service

    @property
    def generation_service(self):
        """Lazy loading of GenerationService to avoid circular imports."""
        if self._generation_service is None:
            from ..services.generation_service import GenerationService

            self._generation_service = GenerationService()
        return self._generation_service

    @pyqtSlot(dict)
    def _on_generation_requested(self, parameters: Dict[str, Any]):
        """Handle generation request from UI.

        Args:
            parameters: Generation parameters from parameter panel
        """
        try:
            self.logger.info(f"Generation requested with parameters: {parameters}")

            # Validate required parameters
            if not self._validate_parameters(parameters):
                self.handle_error("Invalid generation parameters", "Generation")
                return

            # Get current project from main controller
            main_controller = self.parent()
            if hasattr(main_controller, "current_project_id"):
                project_id = main_controller.current_project_id
            else:
                project_id = None

            if not project_id:
                self.handle_error("No project selected", "Generation")
                return

            # Add project to parameters
            parameters["project_id"] = project_id

            # Start loading state
            self.start_loading("Creating generation order")

            # Create order using OrderService
            try:
                order = self.order_service.create_order(
                    project_id=project_id, base_parameters=parameters
                )

                # Store order state
                self.active_orders[order.id] = {
                    "order": order,
                    "parameters": parameters,
                    "status": "created",
                }

                # Emit order created signal
                self.signal_bus.domain.order_created.emit(order.id)

                self.logger.info(f"Order created: {order.id} with {len(order.items)} items")

            except Exception as e:
                self.handle_error(f"Failed to create order: {str(e)}", "Generation")
                self.finish_loading()
                return

            self.finish_loading()

            # Queue the order for generation processing
            self._queue_generation(order.id)

        except Exception as e:
            self.handle_error(f"Generation request failed: {str(e)}", "Generation")
            self.finish_loading()

    def _validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate generation parameters.

        Args:
            parameters: Parameters to validate

        Returns:
            True if parameters are valid, False otherwise
        """
        required_fields = ["prompt"]

        for field in required_fields:
            if field not in parameters or not parameters[field]:
                self.logger.warning(f"Missing required parameter: {field}")
                return False

        return True

    def _queue_generation(self, order_id: str):
        """Queue an order for generation processing.

        Args:
            order_id: ID of the order to queue for generation
        """
        if order_id not in self.active_orders:
            self.logger.error(f"Cannot queue unknown order: {order_id}")
            return

        try:
            # Queue the order using GenerationService
            queue_item_ids = self.generation_service.queue_order(order_id, priority=0)

            self.logger.info(f"Queued order {order_id} with {len(queue_item_ids)} items")

            # Emit started signal to update UI
            self.signal_bus.domain.generation_started.emit(order_id)

            # For now, simulate progress until we have real workers
            # In the future, workers will handle this
            self._simulate_generation_progress(order_id)

        except Exception as e:
            self.handle_error(f"Failed to queue order: {str(e)}", "Generation")
            # Update order status
            if order_id in self.active_orders:
                self.active_orders[order_id]["status"] = "failed"

    def _simulate_generation_progress(self, order_id: str):
        """Simulate generation progress (temporary until real implementation).

        Args:
            order_id: ID of the order being processed
        """
        # This is a placeholder - real implementation will use worker threads
        from PyQt6.QtCore import QTimer

        if order_id not in self.active_orders:
            return

        order_data = self.active_orders[order_id]
        order_data["status"] = "processing"
        order_data["progress"] = 0

        # Create a timer to simulate progress
        timer = QTimer()
        progress = 0

        def update_progress():
            nonlocal progress
            progress += 10
            self.signal_bus.domain.generation_progress.emit(order_id, progress)

            if progress >= 100:
                timer.stop()
                # Simulate completion
                self.signal_bus.domain.generation_completed.emit(order_id)

        timer.timeout.connect(update_progress)
        timer.start(500)  # Update every 500ms

    @pyqtSlot(str)
    def _on_cancel_requested(self, item_id: str):
        """Handle generation cancellation request.

        Args:
            item_id: ID of the item to cancel (could be order_item_id or queue_item_id)
        """
        self.logger.info(f"Cancellation requested for item: {item_id}")

        try:
            # Try to cancel using GenerationService
            # The item_id could be a queue_item_id or order_item_id
            cancelled = self.generation_service.cancel_generation(item_id)

            if cancelled:
                self.logger.info(f"Cancelled generation for item: {item_id}")
                # Emit cancellation signal
                self.signal_bus.domain.generation_cancelled.emit(item_id)
            else:
                self.logger.warning(f"Could not cancel item {item_id} - may not be in queue")

        except Exception as e:
            self.handle_error(f"Failed to cancel generation: {str(e)}", "Generation")

    @pyqtSlot(str)
    def _on_regenerate_requested(self, product_id: str):
        """Handle regeneration request for an existing product.

        Args:
            product_id: ID of the product to regenerate
        """
        self.logger.info(f"Regeneration requested for product: {product_id}")

        # TODO: Implement regeneration logic
        # This would involve:
        # 1. Getting the original parameters from the product
        # 2. Creating a new order with those parameters
        # 3. Starting generation
        self.handle_error("Regeneration not yet implemented", "Generation")

    def _find_order_by_item(self, item_id: str) -> Optional[str]:
        """Find the order ID that contains the given item ID.

        Args:
            item_id: ID of the item to find

        Returns:
            Order ID if found, None otherwise
        """
        for order_id, order_data in self.active_orders.items():
            order = order_data["order"]
            for item in order.items:
                if item.id == item_id:
                    return order_id
        return None

    @pyqtSlot(str)
    def _on_order_created(self, order_id: str):
        """Handle order created event.

        Args:
            order_id: ID of the created order
        """
        self.logger.debug(f"Order created event received: {order_id}")

    @pyqtSlot(str)
    def _on_generation_started(self, item_id: str):
        """Handle generation started event.

        Args:
            item_id: ID of the item that started generation
        """
        self.logger.info(f"Generation started for item: {item_id}")

        # Update UI to show generation is active
        # This could trigger progress panel visibility, etc.

    @pyqtSlot(str, int)
    def _on_generation_progress(self, item_id: str, percent: int):
        """Handle generation progress event.

        Args:
            item_id: ID of the item being generated
            percent: Progress percentage (0-100)
        """
        self.logger.debug(f"Generation progress for {item_id}: {percent}%")

    @pyqtSlot(str)
    def _on_generation_completed(self, item_id: str):
        """Handle generation completed event.

        Args:
            item_id: ID of the completed item
        """
        self.logger.info(f"Generation completed for item: {item_id}")

        # Find and update order status
        order_id = self._find_order_by_item(item_id)
        if order_id and order_id in self.active_orders:
            order_data = self.active_orders[order_id]
            order_data["status"] = "completed"

            # TODO: Create product records for completed generation
            # This will involve:
            # 1. Getting the generated file(s)
            # 2. Creating Product records in database
            # 3. Emitting product_created signals
            # 4. Updating gallery view

    @pyqtSlot(str, str)
    def _on_generation_failed(self, item_id: str, error: str):
        """Handle generation failed event.

        Args:
            item_id: ID of the failed item
            error: Error message
        """
        self.logger.error(f"Generation failed for item {item_id}: {error}")

        # Find and update order status
        order_id = self._find_order_by_item(item_id)
        if order_id and order_id in self.active_orders:
            order_data = self.active_orders[order_id]
            order_data["status"] = "failed"
            order_data["error"] = error

        # Show error to user
        self.handle_error(f"Generation failed: {error}", "Generation")

    def get_active_orders(self) -> Dict[str, Dict[str, Any]]:
        """Get all active orders.

        Returns:
            Dictionary of active orders
        """
        return self.active_orders.copy()

    def get_generation_queue_status(self) -> Dict[str, Any]:
        """Get the current generation queue status.

        Returns:
            Dictionary with queue information
        """
        return {
            "queue_length": len(self.generation_queue),
            "active_orders": len(self.active_orders),
            "queue": self.generation_queue.copy(),
        }

    def cleanup(self):
        """Clean up generation controller resources."""
        # Cancel any active generations
        for order_id in list(self.active_orders.keys()):
            order_data = self.active_orders[order_id]
            if order_data["status"] in ["processing", "queued"]:
                order_data["status"] = "cancelled"

        self.active_orders.clear()
        self.generation_queue.clear()
        self.logger.info("Generation controller cleaned up")
