# Art Factory Development Workflow (PyQt6 Desktop)

## Project Setup

### Repository Structure
```
art-factory/
├── app/
│   ├── main.py              # Application entry point
│   ├── application.py       # QApplication setup
│   ├── models/             # SQLAlchemy models
│   ├── views/              # PyQt6 UI components
│   ├── controllers/        # Business logic controllers
│   ├── services/           # Direct service layer
│   ├── factories/          # Provider implementations
│   ├── signals/            # Event system
│   ├── workers/            # Background threads
│   ├── resources/          # Icons, styles, themes
│   └── utils/              # Helper functions
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── storage/                # Default file storage
│   ├── products/
│   ├── thumbnails/
│   └── temp/
├── docs/
│   ├── architecture/       # Architecture decisions
│   └── guides/            # User/developer guides
├── scripts/
│   ├── setup.sh           # Initial setup script
│   └── build.sh           # Build application bundle
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/art-factory.git
cd art-factory

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Initialize database
python scripts/init_db.py

# Run application
python app/main.py
```

## Development Process

### 1. Task Management

#### Task Types
- **Feature**: New functionality
- **Bug**: Something isn't working
- **Enhancement**: Improvement to existing functionality
- **Refactor**: Code improvement without functionality change

#### Task Workflow
1. Review task in TASKS.md
2. Mark task as IN PROGRESS
3. Create feature branch (optional)
4. Implement with regular commits
5. Update task checklist as you progress
6. Mark task as REVIEW when complete
7. Update documentation if needed

### 2. Branch Strategy (Solo Developer)

#### Simplified Branch Types
- `main`: Production-ready code (primary branch)
- `feature/task-xxx-*`: Task-specific work (optional)

#### Naming Convention
```
feature/task-002-backend-setup
feature/task-011-review-architecture
```

#### Why Simplified?
For solo development, complex branching adds overhead without benefit. Use feature branches only for experimental work or when you want to preserve work-in-progress.

### 3. Development Cycle

#### Starting New Work
```bash
# Work directly on main for most tasks
git checkout main
git pull origin main

# Optional: Create feature branch for complex work
git checkout -b feature/task-xxx-description

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements-dev.txt
```

#### During Development
```bash
# Run application in development mode
python app/main.py --debug

# Run specific component for testing
python -m app.views.main_window

# Watch for file changes (if using watchdog)
python app/main.py --watch
```

#### Code Style
```bash
# Format code with black
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/

# All in one command
make lint  # If Makefile is set up
```

### 4. Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_gallery_widget.py

# Run Qt-specific tests
pytest -m qt

# Run tests in watch mode
ptw  # pytest-watch

# Debug a specific test
pytest tests/unit/test_service.py::test_create_order -vv --pdb
```

### 5. PyQt6 Development Tips

#### UI Development
```bash
# Test UI components in isolation
python -c "from app.views.gallery_widget import GalleryWidget; from PyQt6.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); w = GalleryWidget(); w.show(); sys.exit(app.exec())"

# Use Qt Designer for complex UIs (optional)
designer  # If installed

# Convert .ui files to Python (if using Designer)
pyuic6 design.ui -o design_ui.py
```

#### Signal Debugging
```python
# Enable signal debugging in development
import os
os.environ['QT_LOGGING_RULES'] = '*.debug=true'

# Or add to main.py:
if __name__ == "__main__":
    import sys
    from PyQt6.QtCore import qInstallMessageHandler

    def message_handler(mode, context, message):
        print(f"[{context.function}] {message}")

    if "--debug" in sys.argv:
        qInstallMessageHandler(message_handler)
```

### 6. Database Management

#### Schema Changes
```bash
# Create new migration
alembic revision --autogenerate -m "Add new field"

# Review generated migration
cat alembic/versions/latest_*.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

#### Database Debugging
```bash
# Open SQLite database
sqlite3 storage/artfactory.db

# Common queries
.tables
.schema products
SELECT * FROM products LIMIT 10;
```

### 7. Commit Standards (Simplified)

#### Commit Message Format (Simplified)
```
<description>

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

#### Examples
```bash
git commit -m "Add Civitai provider support

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

git commit -m "Fix generation timeout handling

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### Git Aliases (Optional)
Add to ~/.gitconfig:
```
[alias]
    new-task = "!f() { git checkout -b feature/task-$1; }; f"
    task-commit = "!f() { git add -A && git commit -m \"$1\n\n🤖 Generated with Claude Code\n\nCo-Authored-By: Claude <noreply@anthropic.com>\"; }; f"
    wip = "!git add -A && git commit -m \"Work in progress\n\n🤖 Generated with Claude Code\n\nCo-Authored-By: Claude <noreply@anthropic.com>\""
```

### 8. Building & Packaging

#### Development Build
```bash
# Quick test build
python setup.py build

# Run from build
./build/exe.*/app
```

#### Production Build
```bash
# Create macOS app bundle
pyinstaller art-factory.spec

# Or use build script
./scripts/build.sh

# Output location
ls -la dist/ArtFactory.app
```

#### Testing the Bundle
```bash
# Run the app bundle
open dist/ArtFactory.app

# Check bundle contents
ls -la dist/ArtFactory.app/Contents/

# Debug bundle issues
dist/ArtFactory.app/Contents/MacOS/art-factory --debug
```

## Common Tasks

### Adding a New View/Widget
1. Create widget in `app/views/widgets/`
2. Add to main window or parent widget
3. Connect to appropriate signals
4. Write tests in `tests/unit/views/`
5. Update documentation

### Adding a New Provider
1. Create factory class in `app/factories/`
2. Implement BaseProductFactory interface
3. Add provider configuration
4. Register in factory registry
5. Write tests with mocked API
6. Document provider parameters

### Adding a New Signal
1. Add to DomainSignals or UISignals
2. Emit from appropriate location
3. Connect in relevant controllers
4. Document signal parameters
5. Test signal emission

### Debugging Tips

#### PyQt6 Debugging
```python
# Print all signals from an object
from PyQt6.QtCore import QMetaObject

def print_signals(obj):
    meta = obj.metaObject()
    for i in range(meta.methodCount()):
        method = meta.method(i)
        if method.methodType() == 2:  # Signal
            print(method.methodSignature())

# Debug widget hierarchy
def print_widget_tree(widget, indent=0):
    print("  " * indent + widget.__class__.__name__)
    for child in widget.children():
        if hasattr(child, 'isWidgetType'):
            print_widget_tree(child, indent + 1)
```

#### Performance Profiling
```bash
# Profile application
python -m cProfile -o profile.stats app/main.py

# Analyze results
python -m pstats profile.stats
> sort cumtime
> stats 20

# Memory profiling
python -m memory_profiler app/main.py
```

## Quick Reference

### Key Commands
```bash
# Development
python app/main.py              # Run app
pytest                          # Run tests
black app/                      # Format code
flake8 app/                     # Lint

# Git
git new-task 123               # Create branch
git task-commit "message"       # Commit with format
git wip                        # Quick WIP commit

# Database
alembic upgrade head           # Apply migrations
sqlite3 storage/artfactory.db  # Open database

# Build
pyinstaller art-factory.spec   # Create app bundle
```

### Project Files
- `app/main.py` - Entry point
- `app/signals/domain_signals.py` - Event definitions
- `app/controllers/main_controller.py` - Main logic
- `app/views/main_window.py` - Main UI
- `tests/conftest.py` - Test configuration

### Environment Variables
```bash
export QT_LOGGING_RULES='*.debug=true'  # Debug Qt
export PYTHONPATH=$PYTHONPATH:.         # Include app
export QT_SCALE_FACTOR=2                # HiDPI scaling
```

## Troubleshooting

### Common Issues

#### ImportError in tests
```bash
# Make sure app is in PYTHONPATH
export PYTHONPATH=$PYTHONPATH:.
```

#### Qt platform plugin error
```bash
# On macOS, might need:
export QT_QPA_PLATFORM_PLUGIN_PATH=$(python -c "from PyQt6.QtCore import QLibraryInfo; print(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath))")
```

#### Database locked
```bash
# Find process using database
lsof storage/artfactory.db
# Kill if needed
kill -9 <PID>
```

#### PyInstaller bundle issues
```bash
# Check for missing modules
pyinstaller --debug=imports art-factory.spec

# Add hidden imports to spec file
hiddenimports=['module_name']
```

## Best Practices

1. **Test UI components in isolation** before integrating
2. **Use signals for all cross-component communication**
3. **Keep controllers thin** - logic in services
4. **Thread all API calls** - never block UI
5. **Cache expensive operations** - thumbnails, API responses
6. **Profile regularly** - catch performance issues early
7. **Document complex flows** - especially signal chains
8. **Use type hints** - helps with IDE and mypy

## Resources

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt Documentation](https://doc.qt.io/qt-6/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/)
- [PyInstaller Documentation](https://pyinstaller.org/)