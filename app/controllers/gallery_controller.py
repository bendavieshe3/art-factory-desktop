"""
Gallery controller for managing product display and interactions.
"""

from PyQt6.QtCore import pyqtSlot, QTimer
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from .base_controller import BaseController
from signals.signal_bus import SignalBus


class GalleryController(BaseController):
    """Controller for managing gallery product display and interactions.

    Responsibilities:
    - Load and manage product data for gallery display
    - Handle product selection state and metadata updates
    - Manage file import/export operations
    - Coordinate product search and filtering
    - Handle product-related actions (delete, favorite, etc.)
    """

    def __init__(self, signal_bus: SignalBus):
        """Initialize the gallery controller."""
        super().__init__(signal_bus)
        self.logger = logging.getLogger(__name__)

        # Gallery state
        self.products: List[Dict[str, Any]] = []
        self.selected_products: List[str] = []
        self.current_filter: Dict[str, Any] = {}
        self.search_query: str = ""

        # Services (lazy loaded to avoid circular imports)
        self._product_service = None

        # Refresh timer for periodic gallery updates
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._periodic_refresh)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def _connect_signals(self):
        """Connect gallery controller signals."""
        # UI signals for gallery interactions
        self.signal_bus.ui.selection_changed.connect(self._on_selection_changed)
        self.signal_bus.ui.filter_applied.connect(self._on_filter_applied)
        self.signal_bus.ui.search_requested.connect(self._on_search_requested)
        self.signal_bus.ui.files_imported.connect(self._on_files_imported)

        # Domain signals for product lifecycle
        self.signal_bus.domain.product_created.connect(self._on_product_created)
        self.signal_bus.domain.product_liked.connect(self._on_product_liked)
        self.signal_bus.domain.product_deleted.connect(self._on_product_deleted)
        self.signal_bus.domain.project_changed.connect(self._on_project_changed)

        # Custom signals from gallery widget (if available)
        # These will be connected when the gallery widget is available

    @property
    def product_service(self):
        """Lazy loading of ProductService to avoid circular imports."""
        if self._product_service is None:
            # TODO: Import ProductService when it's implemented
            # from services.product_service import ProductService
            # self._product_service = ProductService()
            pass
        return self._product_service

    def load_products(
        self, project_id: Optional[str] = None, force_refresh: bool = False
    ):
        """Load products for display in the gallery.

        Args:
            project_id: Project ID to load products for, or None for all projects
            force_refresh: Whether to force refresh from database
        """
        try:
            self.start_loading("Loading products")
            self.logger.info(f"Loading products for project: {project_id}")

            # TODO: Load from ProductService when implemented
            # For now, create mock data
            if force_refresh or not self.products:
                self.products = self._create_mock_products(project_id)

            # Apply current filters and search
            filtered_products = self._apply_filters_and_search(self.products)

            # Update gallery widget with products
            self._update_gallery_display(filtered_products)

            self.finish_loading()
            self.logger.info(f"Loaded {len(filtered_products)} products")

        except Exception as e:
            self.handle_error(f"Failed to load products: {str(e)}", "Gallery")
            self.finish_loading()

    def _create_mock_products(self, project_id: Optional[str]) -> List[Dict[str, Any]]:
        """Create mock product data for testing.

        Args:
            project_id: Project ID to create products for

        Returns:
            List of mock product dictionaries
        """
        # This is temporary mock data until ProductService is implemented
        mock_products = []

        for i in range(12):  # Create 12 mock products
            product = {
                "id": f"product-{i+1}",
                "name": f"Generated Image {i+1}",
                "project_id": project_id or "default-project",
                "file_path": None,  # No actual files yet
                "thumbnail_path": None,
                "created_at": "2025-09-27T12:00:00Z",
                "parameters": {
                    "prompt": f"A beautiful landscape {i+1}",
                    "steps": 30,
                    "width": 1024,
                    "height": 1024,
                },
                "metadata": {
                    "file_size": 1024 * 1024 * 2,  # 2MB
                    "format": "PNG",
                    "model": "stable-diffusion-xl",
                    "provider": "replicate",
                },
            }
            mock_products.append(product)

        return mock_products

    def _apply_filters_and_search(
        self, products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply current filters and search query to products.

        Args:
            products: List of products to filter

        Returns:
            Filtered list of products
        """
        filtered = products

        # Apply search query
        if self.search_query:
            filtered = [
                p
                for p in filtered
                if self.search_query.lower() in p.get("name", "").lower()
                or self.search_query.lower()
                in p.get("parameters", {}).get("prompt", "").lower()
            ]

        # Apply filters
        if self.current_filter:
            # Apply project filter
            if "project_id" in self.current_filter:
                project_id = self.current_filter["project_id"]
                filtered = [p for p in filtered if p.get("project_id") == project_id]

            # Apply date range filter
            if "date_from" in self.current_filter or "date_to" in self.current_filter:
                # TODO: Implement date filtering
                pass

            # Apply model filter
            if "model" in self.current_filter:
                model = self.current_filter["model"]
                filtered = [
                    p for p in filtered if p.get("metadata", {}).get("model") == model
                ]

        return filtered

    def _update_gallery_display(self, products: List[Dict[str, Any]]):
        """Update the gallery widget with products.

        Args:
            products: List of products to display
        """
        # TODO: Update gallery widget when available
        # This will involve calling gallery_widget.set_products(products)
        pass

    @pyqtSlot(list)
    def _on_selection_changed(self, selected_product_ids: List[str]):
        """Handle product selection changes.

        Args:
            selected_product_ids: List of selected product IDs
        """
        self.selected_products = selected_product_ids
        self.logger.debug(
            f"Product selection changed: {len(selected_product_ids)} selected"
        )

        # Update metadata panel with first selected product
        if selected_product_ids:
            first_product_id = selected_product_ids[0]
            product_data = self._get_product_by_id(first_product_id)
            if product_data:
                self._update_metadata_panel(product_data)
        else:
            self._clear_metadata_panel()

    @pyqtSlot(dict)
    def _on_filter_applied(self, filter_params: Dict[str, Any]):
        """Handle filter application.

        Args:
            filter_params: Dictionary of filter parameters
        """
        self.current_filter = filter_params
        self.logger.info(f"Filter applied: {filter_params}")

        # Reload products with new filter
        main_controller = self.parent()
        project_id = getattr(main_controller, "current_project_id", None)
        self.load_products(project_id)

    @pyqtSlot(str)
    def _on_search_requested(self, query: str):
        """Handle search requests.

        Args:
            query: Search query string
        """
        self.search_query = query
        self.logger.info(f"Search requested: '{query}'")

        # Reload products with new search
        main_controller = self.parent()
        project_id = getattr(main_controller, "current_project_id", None)
        self.load_products(project_id)

    @pyqtSlot(list)
    def _on_files_imported(self, file_paths: List[str]):
        """Handle file import requests.

        Args:
            file_paths: List of file paths to import
        """
        try:
            self.start_loading(f"Importing {len(file_paths)} files")
            self.logger.info(f"Importing files: {file_paths}")

            # Get current project
            main_controller = self.parent()
            project_id = getattr(main_controller, "current_project_id", None)

            if not project_id:
                self.handle_error("No project selected for import", "Gallery")
                self.finish_loading()
                return

            imported_count = 0
            for file_path in file_paths:
                try:
                    success = self._import_file(file_path, project_id)
                    if success:
                        imported_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to import {file_path}: {e}")

            # Refresh gallery after import
            if imported_count > 0:
                self.load_products(project_id, force_refresh=True)

            self.finish_loading()
            self.logger.info(
                f"Successfully imported {imported_count} of {len(file_paths)} files"
            )

        except Exception as e:
            self.handle_error(f"File import failed: {str(e)}", "Gallery")
            self.finish_loading()

    def _import_file(self, file_path: str, project_id: str) -> bool:
        """Import a single file as a product.

        Args:
            file_path: Path to the file to import
            project_id: Project ID to import into

        Returns:
            True if import was successful, False otherwise
        """
        path = Path(file_path)

        # Validate file
        if not path.exists():
            self.logger.warning(f"File does not exist: {file_path}")
            return False

        if not path.suffix.lower() in [
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".webp",
        ]:
            self.logger.warning(f"Unsupported file format: {file_path}")
            return False

        # TODO: Create product record using ProductService
        # For now, just log the import
        self.logger.info(f"Would import {file_path} to project {project_id}")

        return True

    @pyqtSlot(str)
    def _on_product_created(self, product_id: str):
        """Handle product creation events.

        Args:
            product_id: ID of the created product
        """
        self.logger.info(f"Product created: {product_id}")

        # Refresh gallery to show new product
        main_controller = self.parent()
        project_id = getattr(main_controller, "current_project_id", None)
        self.load_products(project_id, force_refresh=True)

    @pyqtSlot(str)
    def _on_product_liked(self, product_id: str):
        """Handle product like events.

        Args:
            product_id: ID of the liked product
        """
        self.logger.info(f"Product liked: {product_id}")

        # Update product in local cache
        product = self._get_product_by_id(product_id)
        if product:
            product.setdefault("metadata", {})["liked"] = True

    @pyqtSlot(str)
    def _on_product_deleted(self, product_id: str):
        """Handle product deletion events.

        Args:
            product_id: ID of the deleted product
        """
        self.logger.info(f"Product deleted: {product_id}")

        # Remove from local cache
        self.products = [p for p in self.products if p.get("id") != product_id]

        # Remove from selection if selected
        if product_id in self.selected_products:
            self.selected_products.remove(product_id)

        # Refresh gallery display
        main_controller = self.parent()
        project_id = getattr(main_controller, "current_project_id", None)
        filtered_products = self._apply_filters_and_search(self.products)
        self._update_gallery_display(filtered_products)

    @pyqtSlot(str)
    def _on_project_changed(self, project_id: str):
        """Handle project change events.

        Args:
            project_id: ID of the new current project
        """
        self.logger.info(f"Project changed, loading products for: {project_id}")

        # Clear current state
        self.selected_products.clear()
        self._clear_metadata_panel()

        # Load products for new project
        self.load_products(project_id, force_refresh=True)

    def _get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a product by its ID.

        Args:
            product_id: ID of the product to find

        Returns:
            Product data dictionary, or None if not found
        """
        for product in self.products:
            if product.get("id") == product_id:
                return product
        return None

    def _update_metadata_panel(self, product_data: Dict[str, Any]):
        """Update the metadata panel with product information.

        Args:
            product_data: Product data to display
        """
        # TODO: Update metadata panel when available
        # This will involve updating the metadata panel widget
        self.logger.debug(
            f"Would update metadata panel for product: {product_data.get('id')}"
        )

    def _clear_metadata_panel(self):
        """Clear the metadata panel."""
        # TODO: Clear metadata panel when available
        self.logger.debug("Would clear metadata panel")

    def _periodic_refresh(self):
        """Periodic refresh of gallery data."""
        # Only refresh if we have a current project
        main_controller = self.parent()
        if (
            hasattr(main_controller, "current_project_id")
            and main_controller.current_project_id
        ):
            self.logger.debug("Performing periodic gallery refresh")
            self.load_products(main_controller.current_project_id)

    def get_gallery_stats(self) -> Dict[str, Any]:
        """Get gallery statistics.

        Returns:
            Dictionary with gallery statistics
        """
        return {
            "total_products": len(self.products),
            "selected_products": len(self.selected_products),
            "filtered_products": len(self._apply_filters_and_search(self.products)),
            "current_filter": self.current_filter.copy(),
            "search_query": self.search_query,
        }

    def export_selected_products(self, export_path: str) -> bool:
        """Export selected products to a directory.

        Args:
            export_path: Directory to export to

        Returns:
            True if export was successful, False otherwise
        """
        if not self.selected_products:
            self.handle_error("No products selected for export", "Gallery")
            return False

        try:
            self.start_loading(f"Exporting {len(self.selected_products)} products")

            # TODO: Implement actual export logic
            self.logger.info(
                f"Would export {len(self.selected_products)} products to {export_path}"
            )

            self.finish_loading()
            return True

        except Exception as e:
            self.handle_error(f"Export failed: {str(e)}", "Gallery")
            self.finish_loading()
            return False

    def cleanup(self):
        """Clean up gallery controller resources."""
        self.refresh_timer.stop()
        self.products.clear()
        self.selected_products.clear()
        self.current_filter.clear()
        self.search_query = ""
        self.logger.info("Gallery controller cleaned up")
