# Art Factory Technical Architecture

## System Overview

Art Factory is a desktop application for managing AI-generated media (images, videos) through various AI providers. Built with PyQt6 for macOS, it prioritizes rapid development, rich media handling, and clean architecture through signal-based event handling.

## Technology Stack

### Core Technologies
- **Language**: Python 3.11+
- **UI Framework**: PyQt6
- **Database**: SQLite with SQLAlchemy ORM
- **Threading**: QThread for background operations
- **API Clients**: httpx for async provider calls
- **Image Processing**: Pillow (PIL)
- **Video Handling**: PyQt6 Multimedia (QMediaPlayer)

### Development Tools
- **Testing**: pytest + pytest-qt
- **Packaging**: PyInstaller for .app bundle
- **Version Control**: Git
- **Code Quality**: black, flake8, mypy

## Architecture Principles

### 1. Signal-Driven Architecture
All communication between layers uses PyQt signals/slots for:
- Decoupling UI from business logic
- Thread-safe updates across boundaries
- Clean event propagation
- Progress tracking and cancellation

### 2. MVC Pattern with Controllers
- **Models**: SQLAlchemy entities + domain objects
- **Views**: PyQt6 widgets and windows
- **Controllers**: Mediate between views and services

### 3. Direct Service Layer
No API layer needed - controllers call Python services directly:
- Simpler architecture
- Faster development iteration
- No serialization overhead
- Direct database access

## Application Structure

```
art-factory/
├── app/
│   ├── main.py              # Application entry point
│   ├── application.py       # QApplication setup
│   │
│   ├── models/              # Domain models & database
│   │   ├── __init__.py
│   │   ├── base.py         # SQLAlchemy base
│   │   ├── project.py
│   │   ├── order.py
│   │   ├── product.py
│   │   └── collection.py
│   │
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── order_service.py
│   │   ├── generation_service.py
│   │   └── product_service.py
│   │
│   ├── factories/           # Provider implementations
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── replicate_factory.py
│   │   └── fal_factory.py
│   │
│   ├── controllers/         # UI controllers
│   │   ├── __init__.py
│   │   ├── main_controller.py
│   │   ├── generation_controller.py
│   │   └── gallery_controller.py
│   │
│   ├── views/              # PyQt6 UI
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── widgets/
│   │   │   ├── gallery_widget.py
│   │   │   ├── parameter_panel.py
│   │   │   ├── image_viewer.py
│   │   │   └── progress_widget.py
│   │   └── dialogs/
│   │       ├── preferences_dialog.py
│   │       └── order_dialog.py
│   │
│   ├── signals/            # Event system
│   │   ├── __init__.py
│   │   ├── domain_signals.py
│   │   └── ui_signals.py
│   │
│   ├── workers/            # Background threads
│   │   ├── __init__.py
│   │   ├── generation_worker.py
│   │   └── import_worker.py
│   │
│   ├── resources/          # UI resources
│   │   ├── icons/
│   │   ├── styles/
│   │   └── themes/
│   │
│   └── utils/              # Utilities
│       ├── __init__.py
│       ├── image_utils.py
│       └── file_utils.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── storage/                # Default file storage
│   ├── products/
│   ├── thumbnails/
│   └── temp/
│
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

## Core Components

### 1. Signal Architecture

#### Domain Signals
```python
class DomainSignals(QObject):
    # Order/Generation lifecycle
    order_created = pyqtSignal(str)  # order_id
    generation_started = pyqtSignal(str, str)  # order_id, item_id
    generation_progress = pyqtSignal(str, int)  # item_id, percent
    generation_completed = pyqtSignal(str, object)  # item_id, product
    generation_failed = pyqtSignal(str, str)  # item_id, error

    # Product management
    product_created = pyqtSignal(object)  # product
    product_updated = pyqtSignal(str)  # product_id
    product_deleted = pyqtSignal(str)  # product_id

    # Collection management
    collection_created = pyqtSignal(str)  # collection_id
    collection_updated = pyqtSignal(str)  # collection_id
    products_added = pyqtSignal(str, list)  # collection_id, product_ids
```

#### UI Signals
```python
class UISignals(QObject):
    # User actions
    request_generation = pyqtSignal(dict)  # parameters
    request_cancel = pyqtSignal(str)  # item_id

    # View state
    view_changed = pyqtSignal(str)  # view_name
    selection_changed = pyqtSignal(list)  # selected_items
    filter_applied = pyqtSignal(dict)  # filter_params

    # Loading states
    loading_started = pyqtSignal(str)  # task_name
    loading_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)  # error_message
```

### 2. Controller Pattern

Controllers mediate between UI and services:

```python
class GenerationController(QObject):
    def __init__(self, domain_signals: DomainSignals):
        super().__init__()
        self.signals = domain_signals
        self.order_service = OrderService()
        self.generation_service = GenerationService()

        # Connect UI signals to actions
        self.ui_signals = UISignals()
        self.ui_signals.request_generation.connect(self.start_generation)

    def start_generation(self, params: dict):
        """Handle generation request from UI"""
        # Create order
        order = self.order_service.create_order(params)
        self.signals.order_created.emit(order.id)

        # Start worker thread
        worker = GenerationWorker(order)
        worker.progress.connect(
            lambda p: self.signals.generation_progress.emit(order.id, p)
        )
        worker.completed.connect(self._on_generation_complete)
        worker.start()
```

### 3. Worker Threads

Long-running operations use QThread:

```python
class GenerationWorker(QThread):
    progress = pyqtSignal(int)
    completed = pyqtSignal(str, object)  # item_id, product
    error = pyqtSignal(str)

    def __init__(self, order: Order):
        super().__init__()
        self.order = order

    def run(self):
        try:
            # Perform generation
            for i, item in enumerate(self.order.items):
                product = self.generate_product(item)
                progress = int((i + 1) / len(self.order.items) * 100)
                self.progress.emit(progress)
                self.completed.emit(item.id, product)
        except Exception as e:
            self.error.emit(str(e))
```

### 4. View Components

#### Main Window Structure
```python
class MainWindow(QMainWindow):
    def __init__(self, controller: MainController):
        super().__init__()
        self.controller = controller

        # Create UI components
        self.gallery = GalleryWidget()
        self.parameter_panel = ParameterPanel()
        self.progress_dock = ProgressDock()

        # Layout with dockable panels
        self.setCentralWidget(self.gallery)
        self.addDockWidget(Qt.RightDockWidgetArea, self.parameter_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.progress_dock)

        # Connect signals
        self.controller.signals.product_created.connect(
            self.gallery.add_product
        )
```

#### Gallery Widget
```python
class GalleryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.products = []

    def add_product(self, product: Product):
        thumbnail = ProductThumbnail(product)
        row = len(self.products) // 4
        col = len(self.products) % 4
        self.layout.addWidget(thumbnail, row, col)
        self.products.append(product)
```

## Data Layer

### Database Schema
Using SQLAlchemy with SQLite:

```python
class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"

    name: Mapped[str]
    description: Mapped[Optional[str]]
    products: Mapped[List["Product"]] = relationship(back_populates="project")

class Product(Base):
    __tablename__ = "products"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    file_path: Mapped[str]
    thumbnail_path: Mapped[Optional[str]]
    metadata: Mapped[dict] = mapped_column(JSON)
    project: Mapped["Project"] = relationship(back_populates="products")
```

### Direct Database Access
No ORM abstraction layer - services use SQLAlchemy directly:

```python
class ProductService:
    def __init__(self, session: Session):
        self.session = session

    def create_product(self, data: dict) -> Product:
        product = Product(**data)
        self.session.add(product)
        self.session.commit()
        return product

    def get_products(self, project_id: str) -> List[Product]:
        return self.session.query(Product)\
            .filter(Product.project_id == project_id)\
            .order_by(Product.created_at.desc())\
            .all()
```

## Provider Integration

### Factory Pattern
Each provider has its own factory implementation:

```python
class BaseProductFactory(ABC):
    @abstractmethod
    def validate_parameters(self, params: dict) -> dict:
        """Validate and normalize parameters"""
        pass

    @abstractmethod
    def generate(self, params: dict) -> Product:
        """Generate product from parameters"""
        pass

class ReplicateFactory(BaseProductFactory):
    def __init__(self):
        self.client = replicate.Client()

    def generate(self, params: dict) -> Product:
        # Call Replicate API
        output = self.client.run(
            params["model"],
            input=params["input"]
        )
        # Save file and create product
        return self.save_product(output)
```

## File Storage

### Storage Structure
```
storage/
├── products/
│   ├── {project_id}/
│   │   ├── {year}/
│   │   │   ├── {month}/
│   │   │   │   └── {product_id}_{hash}.{ext}
├── thumbnails/
│   ├── small/    # 150x150
│   ├── medium/   # 400x400
│   └── large/    # 800x800
├── temp/         # Temporary files during generation
└── exports/      # User exports
```

### Thumbnail Generation
Automatic thumbnail creation on product import:

```python
def generate_thumbnails(image_path: str) -> dict:
    """Generate multiple thumbnail sizes"""
    thumbnails = {}
    with Image.open(image_path) as img:
        for size_name, dimensions in THUMBNAIL_SIZES.items():
            thumb = img.copy()
            thumb.thumbnail(dimensions, Image.Resampling.LANCZOS)
            thumb_path = get_thumbnail_path(image_path, size_name)
            thumb.save(thumb_path)
            thumbnails[size_name] = thumb_path
    return thumbnails
```

## Performance Considerations

### 1. Lazy Loading
- Gallery uses virtual scrolling for large collections
- Images loaded on-demand with placeholder thumbnails
- Database queries paginated

### 2. Background Operations
- All API calls in worker threads
- Image processing off main thread
- Database writes batched when possible

### 3. Caching
- In-memory cache for recent products
- Thumbnail cache with LRU eviction
- Parameter templates cached

## Security

### API Key Management
- Stored in system keychain (not config files)
- Never logged or displayed in UI
- Encrypted in memory when possible

### File Safety
- Sanitize filenames
- Validate file types before processing
- Sandbox file operations to storage directory

## Testing Strategy

### Unit Tests
```python
def test_generation_controller():
    controller = GenerationController(mock_signals)
    params = {"prompt": "test image"}
    controller.start_generation(params)

    assert mock_signals.order_created.emit.called
    assert controller.worker.isRunning()
```

### Integration Tests
```python
@pytest.mark.qt
def test_gallery_widget(qtbot):
    gallery = GalleryWidget()
    qtbot.addWidget(gallery)

    product = Product(name="test")
    gallery.add_product(product)

    assert len(gallery.products) == 1
    assert gallery.layout.count() == 1
```

## Deployment

### Development
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run application
python app/main.py

# Run tests
pytest tests/
```

### Production Build
```bash
# Build with PyInstaller
pyinstaller art-factory.spec

# Output: dist/ArtFactory.app
```

### Application Bundle Structure
```
ArtFactory.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   └── art-factory  # Main executable
│   ├── Resources/
│   │   ├── icon.icns
│   │   └── qt_plugins/
│   └── Frameworks/
│       └── Python.framework
```

## Migration from Web Architecture

### Removed Components
- ❌ FastAPI backend
- ❌ React frontend
- ❌ Docker containers
- ❌ Redis caching
- ❌ API authentication
- ❌ CORS configuration
- ❌ WebSocket connections

### Simplified Components
- ✅ Direct database access (no API)
- ✅ Direct file system access
- ✅ Single process architecture
- ✅ Native UI components
- ✅ System keychain for secrets

## Future Considerations

### Potential Enhancements
1. **Plugin System**: Allow custom provider plugins
2. **Automation**: AppleScript/Shortcuts support
3. **Cloud Sync**: Optional iCloud backup
4. **Multi-window**: Support multiple projects open

### Performance Optimizations
1. **GPU Acceleration**: For image processing
2. **Parallel Generation**: Multiple providers simultaneously
3. **Smart Caching**: Predictive loading based on usage

## Conclusion

This PyQt6 desktop architecture provides:
- **Rapid Development**: Single language, no API layer
- **Rich UI**: Native widgets for media handling
- **Clean Architecture**: Signal-based decoupling
- **Performance**: Direct operations without web overhead
- **Maintainability**: Clear separation of concerns

The focus on Python-only development with PyQt6 dramatically simplifies the stack while providing all necessary features for a professional media generation application.