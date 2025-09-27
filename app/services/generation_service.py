"""
Generation Management Service.

Handles generation orchestration, queue management, and progress tracking.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func, desc

from ..models import Order, OrderItem, GenerationQueue, Product
from ..models.database import session_scope


class GenerationServiceError(Exception):
    """Base exception for GenerationService errors."""

    pass


class QueueItemNotFoundError(GenerationServiceError):
    """Raised when a queue item cannot be found."""

    pass


class GenerationService:
    """
    Service for managing generation orchestration and queue.

    Provides queue management, progress tracking, and generation coordination
    between orders and the actual generation factories/workers.
    """

    def __init__(self, default_concurrency_limits: Optional[Dict[str, int]] = None):
        """
        Initialize the GenerationService.

        Args:
            default_concurrency_limits: Per-provider concurrency limits
        """
        self.logger = logging.getLogger(__name__)

        # Default concurrency limits per provider
        self.concurrency_limits = default_concurrency_limits or {
            "replicate": 3,
            "fal": 5,
            "civitai": 2,
            "default": 1,
        }

        # Restore any in-progress items on startup
        self._restore_interrupted_generations()

    def _restore_interrupted_generations(self):
        """Restore interrupted generations on service startup."""
        try:
            with session_scope() as session:
                # Find items that were processing but app was restarted
                interrupted_items = (
                    session.query(GenerationQueue)
                    .filter(GenerationQueue.status == "processing")
                    .all()
                )

                for item in interrupted_items:
                    self.logger.warning(f"Restoring interrupted generation: {item.order_item_id}")
                    # Reset to queued for reprocessing
                    item.status = "queued"
                    item.worker_id = None
                    item.started_at = None

                if interrupted_items:
                    session.commit()
                    self.logger.info(f"Restored {len(interrupted_items)} interrupted generations")

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to restore interrupted generations: {e}")

    def queue_order(self, order_id: str, priority: int = 0) -> List[str]:
        """
        Queue all items from an order for generation.

        Args:
            order_id: ID of the order to queue
            priority: Priority level (higher = more priority)

        Returns:
            List of queue item IDs created

        Raises:
            GenerationServiceError: If order cannot be queued
        """
        try:
            with session_scope() as session:
                # Get order with items
                order = (
                    session.query(Order)
                    .filter(and_(Order.id == order_id, Order.deleted_at.is_(None)))
                    .first()
                )

                if not order:
                    raise GenerationServiceError(f"Order not found: {order_id}")

                queue_items = []
                for order_item in order.order_items:
                    if order_item.deleted_at is None:
                        queue_item_id = self._queue_order_item(session, order_item, priority)
                        if queue_item_id:
                            queue_items.append(queue_item_id)

                session.commit()

                self.logger.info(f"Queued order {order_id} with {len(queue_items)} items")
                return queue_items

        except SQLAlchemyError as e:
            raise GenerationServiceError(f"Database error queuing order: {str(e)}")

    def queue_order_item(self, order_item_id: str, priority: int = 0) -> Optional[str]:
        """
        Queue a specific order item for generation.

        Args:
            order_item_id: ID of the order item to queue
            priority: Priority level (higher = more priority)

        Returns:
            Queue item ID if queued successfully, None if already queued

        Raises:
            GenerationServiceError: If order item cannot be queued
        """
        try:
            with session_scope() as session:
                order_item = (
                    session.query(OrderItem)
                    .filter(and_(OrderItem.id == order_item_id, OrderItem.deleted_at.is_(None)))
                    .first()
                )

                if not order_item:
                    raise GenerationServiceError(f"OrderItem not found: {order_item_id}")

                queue_item_id = self._queue_order_item(session, order_item, priority)
                session.commit()

                if queue_item_id:
                    self.logger.info(f"Queued order item: {order_item_id}")
                else:
                    self.logger.info(f"Order item already queued: {order_item_id}")

                return queue_item_id

        except SQLAlchemyError as e:
            raise GenerationServiceError(f"Database error queuing order item: {str(e)}")

    def _queue_order_item(
        self, session: Session, order_item: OrderItem, priority: int
    ) -> Optional[str]:
        """
        Internal method to queue an order item.

        Args:
            session: Database session
            order_item: OrderItem to queue
            priority: Priority level

        Returns:
            Queue item ID if created, None if already exists
        """
        # Check if already queued
        existing = (
            session.query(GenerationQueue)
            .filter(GenerationQueue.order_item_id == order_item.id)
            .first()
        )

        if existing:
            return None

        # Extract provider and model from order item
        gen_params = order_item.generation_parameter_set or {}
        provider = gen_params.get("provider", order_item.order.provider)
        model = gen_params.get("model", order_item.order.model)

        # Create queue item
        queue_item = GenerationQueue(
            order_item_id=order_item.id,
            order_id=order_item.order_id,
            provider=provider,
            model=model,
            priority=priority,
            status="queued",
        )

        # Set concurrency group
        queue_item.set_concurrency_group()

        session.add(queue_item)
        session.flush()  # Get the ID

        return queue_item.id

    def get_next_items(self, concurrency_check: bool = True) -> List[GenerationQueue]:
        """
        Get next items to process from the queue.

        Args:
            concurrency_check: Whether to respect concurrency limits

        Returns:
            List of GenerationQueue items ready for processing
        """
        try:
            with session_scope() as session:
                # Base query for queued items
                query = (
                    session.query(GenerationQueue)
                    .filter(GenerationQueue.status == "queued")
                    .order_by(desc(GenerationQueue.priority), GenerationQueue.created_at)
                )

                if not concurrency_check:
                    return query.limit(10).all()

                # Get current processing counts by provider
                processing_counts = self._get_processing_counts(session)

                available_items = []
                for item in query.limit(50).all():  # Look at top 50 by priority
                    provider = item.provider
                    limit = self.concurrency_limits.get(
                        provider, self.concurrency_limits["default"]
                    )
                    current_count = processing_counts.get(provider, 0)

                    if current_count < limit:
                        available_items.append(item)
                        processing_counts[provider] = current_count + 1

                        # Limit total items returned
                        if len(available_items) >= 10:
                            break

                return available_items

        except SQLAlchemyError:
            self.logger.error("Failed to get next queue items")
            return []

    def _get_processing_counts(self, session: Session) -> Dict[str, int]:
        """Get current processing counts by provider."""
        results = (
            session.query(GenerationQueue.provider, func.count(GenerationQueue.id))
            .filter(GenerationQueue.status == "processing")
            .group_by(GenerationQueue.provider)
            .all()
        )

        return {provider: count for provider, count in results}

    def start_generation(self, queue_item_id: str, worker_id: str = None) -> GenerationQueue:
        """
        Mark a queue item as processing.

        Args:
            queue_item_id: ID of the queue item
            worker_id: ID of the worker processing the item

        Returns:
            Updated GenerationQueue item

        Raises:
            QueueItemNotFoundError: If queue item not found
            GenerationServiceError: If operation fails
        """
        try:
            with session_scope() as session:
                queue_item = (
                    session.query(GenerationQueue)
                    .filter(GenerationQueue.id == queue_item_id)
                    .first()
                )

                if not queue_item:
                    raise QueueItemNotFoundError(f"Queue item not found: {queue_item_id}")

                if queue_item.status != "queued":
                    raise GenerationServiceError(
                        f"Queue item not in queued state: {queue_item.status}"
                    )

                queue_item.mark_processing(worker_id)
                session.commit()

                self.logger.info(f"Started generation for queue item: {queue_item_id}")
                return queue_item

        except SQLAlchemyError as e:
            raise GenerationServiceError(f"Database error starting generation: {str(e)}")

    def update_progress(
        self, queue_item_id: str, progress_percent: float, metadata: Dict[str, Any] = None
    ) -> GenerationQueue:
        """
        Update generation progress.

        Args:
            queue_item_id: ID of the queue item
            progress_percent: Progress percentage (0-100)
            metadata: Optional metadata update

        Returns:
            Updated GenerationQueue item

        Raises:
            QueueItemNotFoundError: If queue item not found
            GenerationServiceError: If operation fails
        """
        try:
            with session_scope() as session:
                queue_item = (
                    session.query(GenerationQueue)
                    .filter(GenerationQueue.id == queue_item_id)
                    .first()
                )

                if not queue_item:
                    raise QueueItemNotFoundError(f"Queue item not found: {queue_item_id}")

                queue_item.update_progress(progress_percent)

                if metadata:
                    current_metadata = queue_item.metadata or {}
                    current_metadata.update(metadata)
                    queue_item.metadata = current_metadata

                session.commit()
                return queue_item

        except SQLAlchemyError as e:
            raise GenerationServiceError(f"Database error updating progress: {str(e)}")

    def complete_generation(
        self, queue_item_id: str, product_data: Optional[Dict[str, Any]] = None
    ) -> GenerationQueue:
        """
        Mark generation as completed and optionally create product.

        Args:
            queue_item_id: ID of the queue item
            product_data: Optional product data for ProductService

        Returns:
            Updated GenerationQueue item

        Raises:
            QueueItemNotFoundError: If queue item not found
            GenerationServiceError: If operation fails
        """
        try:
            with session_scope() as session:
                queue_item = (
                    session.query(GenerationQueue)
                    .filter(GenerationQueue.id == queue_item_id)
                    .first()
                )

                if not queue_item:
                    raise QueueItemNotFoundError(f"Queue item not found: {queue_item_id}")

                queue_item.mark_completed()

                # Update OrderItem status
                order_item = queue_item.order_item
                if order_item:
                    order_item.status = "complete"
                    order_item.completed_at = datetime.utcnow()

                session.commit()

                self.logger.info(f"Completed generation for queue item: {queue_item_id}")
                return queue_item

        except SQLAlchemyError as e:
            raise GenerationServiceError(f"Database error completing generation: {str(e)}")

    def fail_generation(self, queue_item_id: str, error_message: str) -> GenerationQueue:
        """
        Mark generation as failed.

        Args:
            queue_item_id: ID of the queue item
            error_message: Error description

        Returns:
            Updated GenerationQueue item

        Raises:
            QueueItemNotFoundError: If queue item not found
            GenerationServiceError: If operation fails
        """
        try:
            with session_scope() as session:
                queue_item = (
                    session.query(GenerationQueue)
                    .filter(GenerationQueue.id == queue_item_id)
                    .first()
                )

                if not queue_item:
                    raise QueueItemNotFoundError(f"Queue item not found: {queue_item_id}")

                queue_item.mark_failed(error_message)

                # Update OrderItem status
                order_item = queue_item.order_item
                if order_item:
                    order_item.status = "failed"
                    order_item.error_message = error_message

                session.commit()

                self.logger.error(
                    f"Failed generation for queue item {queue_item_id}: {error_message}"
                )
                return queue_item

        except SQLAlchemyError as e:
            raise GenerationServiceError(f"Database error failing generation: {str(e)}")

    def cancel_generation(self, queue_item_id: str) -> bool:
        """
        Cancel a queued or processing generation.

        Args:
            queue_item_id: ID of the queue item to cancel

        Returns:
            True if cancelled successfully, False if not found or cannot cancel

        Raises:
            GenerationServiceError: If operation fails
        """
        try:
            with session_scope() as session:
                queue_item = (
                    session.query(GenerationQueue)
                    .filter(GenerationQueue.id == queue_item_id)
                    .first()
                )

                if not queue_item:
                    return False

                if queue_item.status not in ["queued", "processing"]:
                    return False

                queue_item.mark_cancelled()

                # Update OrderItem status
                order_item = queue_item.order_item
                if order_item:
                    order_item.status = "cancelled"

                session.commit()

                self.logger.info(f"Cancelled generation for queue item: {queue_item_id}")
                return True

        except SQLAlchemyError as e:
            raise GenerationServiceError(f"Database error cancelling generation: {str(e)}")

    def retry_failed_item(self, queue_item_id: str) -> bool:
        """
        Retry a failed generation.

        Args:
            queue_item_id: ID of the queue item to retry

        Returns:
            True if retry was queued, False if cannot retry

        Raises:
            QueueItemNotFoundError: If queue item not found
            GenerationServiceError: If operation fails
        """
        try:
            with session_scope() as session:
                queue_item = (
                    session.query(GenerationQueue)
                    .filter(GenerationQueue.id == queue_item_id)
                    .first()
                )

                if not queue_item:
                    raise QueueItemNotFoundError(f"Queue item not found: {queue_item_id}")

                if not queue_item.can_retry():
                    return False

                if queue_item.increment_retry():
                    # Reset OrderItem status
                    order_item = queue_item.order_item
                    if order_item:
                        order_item.status = "pending"
                        order_item.error_message = None

                    session.commit()

                    self.logger.info(
                        f"Retrying failed generation: {queue_item_id} "
                        f"(attempt {queue_item.retry_count + 1})"
                    )
                    return True

                return False

        except SQLAlchemyError as e:
            raise GenerationServiceError(f"Database error retrying generation: {str(e)}")

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue statistics.

        Returns:
            Dictionary with queue status information
        """
        try:
            with session_scope() as session:
                # Overall counts
                total_count = session.query(GenerationQueue).count()

                # Status breakdown
                status_counts = {}
                status_results = (
                    session.query(GenerationQueue.status, func.count(GenerationQueue.id))
                    .group_by(GenerationQueue.status)
                    .all()
                )

                for status, count in status_results:
                    status_counts[status] = count

                # Provider breakdown (active items only)
                provider_counts = {}
                provider_results = (
                    session.query(GenerationQueue.provider, func.count(GenerationQueue.id))
                    .filter(GenerationQueue.status.in_(["queued", "processing"]))
                    .group_by(GenerationQueue.provider)
                    .all()
                )

                for provider, count in provider_results:
                    provider_counts[provider] = count

                # Average queue time for processing items
                avg_wait_time = None
                processing_items = (
                    session.query(GenerationQueue)
                    .filter(
                        and_(
                            GenerationQueue.status == "processing",
                            GenerationQueue.started_at.isnot(None),
                        )
                    )
                    .all()
                )

                if processing_items:
                    wait_times = [
                        (item.started_at - item.created_at).total_seconds()
                        for item in processing_items
                    ]
                    avg_wait_time = sum(wait_times) / len(wait_times)

                return {
                    "total_items": total_count,
                    "status_counts": status_counts,
                    "provider_counts": provider_counts,
                    "concurrency_limits": self.concurrency_limits,
                    "average_wait_time_seconds": avg_wait_time,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except SQLAlchemyError:
            return {"error": "Failed to get queue status"}

    def get_generation_status(self, queue_item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed status for a specific generation.

        Args:
            queue_item_id: ID of the queue item

        Returns:
            Dictionary with generation status or None if not found
        """
        try:
            with session_scope() as session:
                queue_item = (
                    session.query(GenerationQueue)
                    .filter(GenerationQueue.id == queue_item_id)
                    .first()
                )

                if not queue_item:
                    return None

                duration = queue_item.get_duration()

                return {
                    "queue_item_id": queue_item.id,
                    "order_item_id": queue_item.order_item_id,
                    "order_id": queue_item.order_id,
                    "status": queue_item.status,
                    "provider": queue_item.provider,
                    "model": queue_item.model,
                    "progress_percent": queue_item.progress_percent,
                    "priority": queue_item.priority,
                    "retry_count": queue_item.retry_count,
                    "max_retries": queue_item.max_retries,
                    "worker_id": queue_item.worker_id,
                    "created_at": (
                        queue_item.created_at.isoformat() if queue_item.created_at else None
                    ),
                    "started_at": (
                        queue_item.started_at.isoformat() if queue_item.started_at else None
                    ),
                    "completed_at": (
                        queue_item.completed_at.isoformat() if queue_item.completed_at else None
                    ),
                    "duration_seconds": duration,
                    "error_message": queue_item.error_message,
                    "metadata": queue_item.metadata,
                    "can_retry": queue_item.can_retry(),
                }

        except SQLAlchemyError:
            return None

    def cleanup_completed_items(self, days_old: int = 7) -> int:
        """
        Clean up old completed queue items.

        Args:
            days_old: Items older than this many days will be cleaned up

        Returns:
            Number of items cleaned up

        Raises:
            GenerationServiceError: If cleanup fails
        """
        try:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            with session_scope() as session:
                items_to_delete = (
                    session.query(GenerationQueue)
                    .filter(
                        and_(
                            GenerationQueue.status.in_(["completed", "cancelled"]),
                            GenerationQueue.completed_at < cutoff_date,
                        )
                    )
                    .all()
                )

                count = len(items_to_delete)

                for item in items_to_delete:
                    session.delete(item)

                session.commit()

                self.logger.info(f"Cleaned up {count} old queue items")
                return count

        except SQLAlchemyError as e:
            raise GenerationServiceError(f"Database error during cleanup: {str(e)}")

    def set_concurrency_limit(self, provider: str, limit: int):
        """
        Update concurrency limit for a provider.

        Args:
            provider: Provider name
            limit: New concurrency limit
        """
        if limit > 0:
            self.concurrency_limits[provider] = limit
            self.logger.info(f"Set concurrency limit for {provider}: {limit}")
        else:
            self.logger.warning(f"Invalid concurrency limit for {provider}: {limit}")

    def get_order_progress(self, order_id: str) -> Dict[str, Any]:
        """
        Get aggregated progress for all items in an order.

        Args:
            order_id: ID of the order

        Returns:
            Dictionary with order progress information
        """
        try:
            with session_scope() as session:
                queue_items = (
                    session.query(GenerationQueue)
                    .filter(GenerationQueue.order_id == order_id)
                    .all()
                )

                if not queue_items:
                    return {"order_id": order_id, "total_items": 0}

                total_items = len(queue_items)
                completed_items = sum(1 for item in queue_items if item.is_finished)
                failed_items = sum(1 for item in queue_items if item.status == "failed")

                # Calculate overall progress
                total_progress = sum(item.progress_percent for item in queue_items)
                overall_progress = total_progress / total_items if total_items > 0 else 0

                # Determine overall status
                if completed_items == total_items:
                    overall_status = "completed"
                elif failed_items == total_items:
                    overall_status = "failed"
                elif any(item.status == "processing" for item in queue_items):
                    overall_status = "processing"
                elif any(item.status == "queued" for item in queue_items):
                    overall_status = "queued"
                else:
                    overall_status = "unknown"

                return {
                    "order_id": order_id,
                    "total_items": total_items,
                    "completed_items": completed_items,
                    "failed_items": failed_items,
                    "overall_progress_percent": overall_progress,
                    "overall_status": overall_status,
                    "items": [
                        {
                            "queue_item_id": item.id,
                            "order_item_id": item.order_item_id,
                            "status": item.status,
                            "progress_percent": item.progress_percent,
                            "provider": item.provider,
                        }
                        for item in queue_items
                    ],
                }

        except SQLAlchemyError:
            return {"error": f"Failed to get progress for order {order_id}"}
