"""
Background thumbnail loading system for the gallery widget.
"""

from PyQt6.QtCore import QThread, pyqtSignal, QObject, QMutex, QWaitCondition
from PyQt6.QtGui import QPixmap, QImage
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import queue
import time


class ThumbnailLoader(QObject):
    """Handles thumbnail loading requests in a worker thread."""

    thumbnail_loaded = pyqtSignal(str, QPixmap)  # product_id, pixmap
    loading_failed = pyqtSignal(str, str)  # product_id, error_message

    def __init__(self):
        super().__init__()
        self.request_queue = queue.Queue()
        self.stop_requested = False
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()

    def request_thumbnail(self, product_id: str, image_path: Path, priority: int = 0):
        """Request a thumbnail to be loaded."""
        # Higher priority items are loaded first (lower number = higher priority)
        self.request_queue.put((priority, product_id, image_path))
        self.wait_condition.wakeAll()

    def process_requests(self):
        """Process thumbnail loading requests (runs in worker thread)."""
        while not self.stop_requested:
            try:
                # Get next request with timeout
                priority, product_id, image_path = self.request_queue.get(timeout=0.1)

                # Load the image
                if image_path.exists():
                    pixmap = self._load_thumbnail(image_path)
                    if pixmap and not pixmap.isNull():
                        self.thumbnail_loaded.emit(product_id, pixmap)
                    else:
                        self.loading_failed.emit(product_id, "Failed to load image")
                else:
                    self.loading_failed.emit(product_id, "File not found")

            except queue.Empty:
                # No requests, wait for signal
                self.mutex.lock()
                if not self.stop_requested and self.request_queue.empty():
                    self.wait_condition.wait(self.mutex, 100)
                self.mutex.unlock()
            except Exception as e:
                print(f"Error loading thumbnail: {e}")

    def _load_thumbnail(self, image_path: Path) -> Optional[QPixmap]:
        """Load and create a thumbnail from an image file."""
        try:
            # Load image
            image = QImage(str(image_path))

            if image.isNull():
                return None

            # Convert to pixmap
            pixmap = QPixmap.fromImage(image)

            # Scale to thumbnail size (max 360x360 for retina displays)
            # This is 2x the display size for high DPI screens
            if pixmap.width() > 360 or pixmap.height() > 360:
                pixmap = pixmap.scaled(
                    360,
                    360,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

            return pixmap

        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None

    def stop(self):
        """Stop processing requests."""
        self.stop_requested = True
        self.wait_condition.wakeAll()


class ThumbnailLoaderThread(QThread):
    """Thread for running the thumbnail loader."""

    def __init__(self, loader: ThumbnailLoader):
        super().__init__()
        self.loader = loader

    def run(self):
        """Run the thumbnail loading process."""
        self.loader.process_requests()


class ThumbnailCache:
    """Simple cache for loaded thumbnails using QPixmapCache."""

    def __init__(self, cache_size_mb: int = 100):
        """Initialize cache with size in MB."""
        from PyQt6.QtGui import QPixmapCache

        # Set cache size (in KB)
        QPixmapCache.setCacheLimit(cache_size_mb * 1024)
        self.cache_keys: Dict[str, str] = {}  # product_id -> cache_key

    def get(self, product_id: str) -> Optional[QPixmap]:
        """Get a cached thumbnail."""
        from PyQt6.QtGui import QPixmapCache

        if product_id in self.cache_keys:
            pixmap = QPixmapCache.find(self.cache_keys[product_id])
            if pixmap:
                return pixmap
            else:
                # Cache miss, remove stale key
                del self.cache_keys[product_id]
        return None

    def put(self, product_id: str, pixmap: QPixmap):
        """Store a thumbnail in cache."""
        from PyQt6.QtGui import QPixmapCache

        # Generate unique key
        cache_key = f"thumb_{product_id}_{time.time()}"
        QPixmapCache.insert(cache_key, pixmap)
        self.cache_keys[product_id] = cache_key

    def clear(self):
        """Clear the cache."""
        from PyQt6.QtGui import QPixmapCache

        QPixmapCache.clear()
        self.cache_keys.clear()


# Import Qt for AspectRatioMode and TransformationMode
from PyQt6.QtCore import Qt
