# Art Factory Desktop

A powerful PyQt6 desktop application for managing AI-generated art, supporting multiple providers and advanced generation workflows.

## Overview

Art Factory is designed for local deployment on macOS as a single-user tool that provides a unified interface for working with multiple AI generation providers like Replicate, fal.ai, and Civitai. It offers project-based organization, parameter management, and a signal-driven architecture for responsive user interactions.

## Features

- **Multi-Provider Support**: Integration with various AI generation services
- **Project Organization**: Group related work into projects and collections
- **Parameter Management**: Advanced parameter sets with token expansion and interpolation
- **Real-time Updates**: Signal-driven architecture for responsive UI
- **Generation Tracking**: Monitor order progress and manage generation history
- **Local Storage**: SQLite database with optional PostgreSQL support

## Requirements

- **Python 3.11+**
- **macOS** (primary target platform)
- **PyQt6** for the desktop interface
- **SQLite** for local data storage

## Installation

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/bendavieshe3/art-factory-desktop.git
cd art-factory-desktop

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Initialize database
python scripts/init_db.py

# Run the application
python app/main.py
```

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with debug mode
python app/main.py --debug

# Run tests
pytest

# Code formatting and linting
black app/ tests/
flake8 app/ tests/
mypy app/
```

## Usage

### Starting the Application

```bash
# Basic usage
python app/main.py

# Debug mode (enables signal logging)
python app/main.py --debug
# or
AF_DEBUG=1 python app/main.py
```

### Key Concepts

- **Projects**: Primary organizational unit for grouping related work
- **Orders**: Requests to create products with specific parameters
- **Products**: Generated outputs (images, videos, audio)
- **Providers**: AI services that generate content
- **Collections**: User-created groups of products

## Architecture

### Signal-Driven Design

The application uses PyQt6's signal/slot mechanism for event-driven communication:

```python
from signals import signal_bus

# Emit UI events
signal_bus.ui.request_generation.emit(parameters)

# Listen for domain events
signal_bus.domain.product_created.connect(handle_new_product)
```

### Directory Structure

```
app/
├── main.py              # Application entry point
├── application.py       # QApplication setup
├── models/             # SQLAlchemy models
├── views/              # PyQt6 UI components
├── controllers/        # Business logic controllers
├── services/           # Direct service layer
├── factories/          # Provider implementations
├── signals/            # Event system
├── workers/            # Background threads
├── resources/          # Icons, styles, themes
└── utils/              # Helper functions
```

### Signal Architecture

- **Domain Signals**: Business events (orders, products, projects)
- **UI Signals**: Interface interactions (view changes, loading states)
- **Signal Bus**: Centralized event coordination with debug logging

## Development

### Code Style

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/signals/test_signal_bus.py

# Debug a specific test
pytest tests/unit/test_service.py::test_function -vv --pdb
```

### Database Management

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Contributing

### Development Workflow

1. **Task Management**: Check `TASKS.md` for current priorities
2. **Branch Strategy**: Work directly on main for most tasks
3. **Testing**: Ensure all tests pass before committing
4. **Code Quality**: Run linting and formatting tools
5. **Documentation**: Update relevant docs for significant changes

### Commit Standards

```bash
git commit -m "Add feature description

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Adding New Components

#### New UI Widget
1. Create widget in `app/views/widgets/`
2. Connect to signal bus for events
3. Write tests in `tests/unit/views/`
4. Update parent window/widget

#### New Provider
1. Create factory class in `app/factories/`
2. Implement `BaseProductFactory` interface
3. Add provider configuration
4. Register in factory registry
5. Write comprehensive tests

#### New Signal
1. Add to `DomainSignals` or `UISignals`
2. Emit from appropriate component
3. Connect handlers where needed
4. Test signal emission and handling

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure Python path includes app directory
export PYTHONPATH=$PYTHONPATH:.
```

#### Qt Platform Plugin Error
```bash
# On macOS, set Qt plugin path
export QT_QPA_PLATFORM_PLUGIN_PATH=$(python -c "from PyQt6.QtCore import QLibraryInfo; print(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath))")
```

#### Database Locked
```bash
# Find processes using database
lsof storage/artfactory.db
# Kill if needed
kill -9 <PID>
```

### Debug Mode

Enable detailed signal logging:

```bash
AF_DEBUG=1 python app/main.py
```

This will show:
- Signal emissions with parameters
- Signal connections
- Application startup details

## Documentation

- **TASKS.md**: Current development tasks
- **docs/development-workflow.md**: Detailed development process
- **docs/technical-architecture.md**: System design details
- **docs/concepts.md**: Domain model and business logic
- **CLAUDE.md**: AI assistant guidance and project context

## License

[License information would go here]

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/bendavieshe3/art-factory-desktop/issues) page or check the task management system in `TASKS.md`.

## Related Projects

- [art-factory](https://github.com/bendavieshe3/art-factory) - Web-based version of Art Factory
- [presto](https://github.com/bendavieshe3/presto) - Command line tool for AI model invocation
- [draw-things-tool](https://github.com/bendavieshe3/draw-things-tool) - Batch generation for Draw Things app