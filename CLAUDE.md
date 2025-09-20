# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Art Factory is a tool for managing the generation, remixing and refinement of images, videos, and multimedia products from AI services. It's designed for local deployment on Mac OS for single-user use.

## Architecture and Domain Model

### Core Entities
- **Providers**: AI services (Replicate, fal.ai, civitai) that generate content
- **Models**: Specific AI models grouped by family (Stable Diffusion, Midjourney, etc.) and modality (text-to-image, image-to-video, etc.)
- **ProductFactory**: Provider-specific implementations for generation tasks, using hierarchy: BaseProductFactory → ProviderProductFactory → ModelModalityProductFactory → ModelSpecificFactory
- **Orders**: User requests to create products with base parameter sets
- **OrderItems**: Individual API requests to providers (replaces "Generation" concept)
- **Products**: Generated outputs (images, videos, audio)
- **Projects**: Primary organizational unit for grouping related work
- **Collections**: User-created groups of products

### Key Concepts
- **Parameter Sets**: Configuration for generations (base, generation, actual, return)
- **ParameterSpecs**: Validation rules and UI hints for parameters
- **Token Expansion**: [red,blue,green] syntax for multiple variations
- **Parameter Interpolation**: steps:10..20 for range values
- **Sub-prompts**: prompt1 || prompt2 for separate generations

## Technology Stack

### Desktop Application
- **Python 3.11+** with **PyQt6** framework
- **SQLAlchemy 2.0** with SQLite database
- **Signal-based architecture** for component communication
- **QThread** for background operations
- **pytest-qt** for UI testing
- **PyInstaller** for application packaging

### Key Components
- **Signal Bus**: Centralized event system with debug logging
- **Domain Signals**: Business events (orders, generation, products, projects)
- **UI Signals**: User interface interactions and state changes
- **Factory Pattern**: Provider-specific generation implementations
- **MVC Architecture**: Models, Views, Controllers with signal mediation

## Development Commands

### Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Verify PyQt6 installation
python3 -c "import PyQt6; print('PyQt6 installed successfully')"
```

### Development
```bash
# Run PyQt6 application
source venv/bin/activate && python3 app/main.py

# Run with debug mode (enables signal logging)
python3 app/main.py --debug

# Or use development script (handles venv automatically)
python3 scripts/run_dev.py [--debug]

# Run tests
pytest                    # All tests
pytest tests/unit/        # Unit tests only
pytest --cov=app         # With coverage
```

### Code Quality
```bash
# Format and lint (run before committing)
black app/ tests/        # Format code
flake8 app/ tests/       # Lint code
mypy app/               # Type check

# All in sequence
black app/ tests/ && flake8 app/ tests/ && pytest
```

### Task Implementation Workflow
```bash
# 1. Implement task
# 2. Run quality checks
black app/ tests/ && flake8 app/ tests/ && pytest

# 3. Update TASKS.md (mark completed, move to completed section)
# 4. Commit with descriptive message
git add -A && git commit -m "Complete TASK-XXX: Description

- Implementation details
- Key features added
- Tests passing

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Git Workflow (Solo Developer)
```bash
# Basic workflow - work directly on main
git add -A
git commit -m "Task description

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Optional: Use feature branches for complex work
git checkout -b feature/task-xxx-description
# ... work ...
git checkout main
git merge feature/task-xxx-description

# Useful git aliases (add to ~/.gitconfig):
# new-task = "!f() { git checkout -b feature/task-$1; }; f"
# task-commit = "!f() { git add -A && git commit -m \"$1\n\n🤖 Generated with Claude Code\n\nCo-Authored-By: Claude <noreply@anthropic.com>\"; }; f"
# wip = "!git add -A && git commit -m \"Work in progress\n\n🤖 Generated with Claude Code\n\nCo-Authored-By: Claude <noreply@anthropic.com>\""
```

### Signal Architecture Usage
```python
# Import signal bus
from signals import signal_bus

# Connect to signals
signal_bus.domain.order_created.connect(handle_order)
signal_bus.ui.loading_started.connect(show_loading)

# Emit signals
signal_bus.domain.order_created.emit("order_123")
signal_bus.ui.loading_started.emit("Loading products...")

# Debug mode shows signal logging
export AF_DEBUG=1  # or use --debug flag
```

### Database (Future)
```bash
# Will be added when TASK-102 is implemented
# SQLAlchemy + Alembic for database management
```

## Project Structure

```
app/
├── main.py              # Application entry point
├── application.py       # QApplication setup
├── models/              # SQLAlchemy models (future)
├── views/               # PyQt6 UI components
│   ├── main_window.py   # Main application window
│   └── widgets/         # Reusable UI widgets
├── controllers/         # Business logic controllers (future)
├── services/            # Direct service layer (future)
├── factories/           # Provider implementations (future)
├── signals/             # Signal architecture ✅
│   ├── domain_signals.py   # Business event signals
│   ├── ui_signals.py       # UI interaction signals
│   └── signal_bus.py       # Singleton signal bus
├── workers/             # Background threads (future)
├── resources/           # Icons, styles, themes
└── utils/               # Helper functions

tests/
├── unit/
│   └── signals/         # Signal system tests ✅
├── integration/         # Integration tests (future)
└── conftest.py          # Pytest configuration

scripts/
├── run_dev.py           # Development runner ✅
└── build.sh             # Build script (future)
```

## Implementation Guidelines

### Factory Pattern
```python
# New provider implementation
class NewProviderFactory(BaseProductFactory):
    def validate_parameters(self, params: dict) -> dict:
        # Provider-specific validation
        pass
    
    def generate(self, params: dict) -> list[Product]:
        # API interaction logic
        pass
```

### API Endpoints Pattern
- REST endpoints under `/api/v1/`
- WebSocket at `/ws/generation/{order_id}`
- Consistent error responses
- Request validation with Pydantic

### Database Patterns
- Soft deletes with `deleted_at`
- Denormalized counts for performance
- JSON fields for flexible parameter storage
- Strategic indexes on foreign keys and common queries

### Testing Requirements
- 80% coverage target
- Unit tests for business logic
- Integration tests for API endpoints
- Mock external providers in tests

## Common Tasks

### Adding a New Provider
1. Create factory class in `backend/app/factories/`
2. Add provider config to database
3. Write tests for the factory
4. Update frontend provider selection
5. Document provider parameters

### Adding New Parameter Type
1. Define in `backend/app/schemas/parameters.py`
2. Add validation in factory base class
3. Create UI component in frontend
4. Add interpolation support if needed
5. Write tests

### Running Migrations
1. Make model changes
2. Generate: `alembic revision --autogenerate -m "message"`
3. Review generated migration
4. Apply: `alembic upgrade head`

## Task Management

### Quick Commands
- `/task-list` - Show current tasks and what to work on next
- `/task-status` - Get current task status and update TASKS.md
- `/task-implement` - Start working on a specific task
- `/task-create` - Create a new task entry
- `/task-prioritize` - Prioritize and organize tasks
- `/task-completed-review` - Review completed task implementation
- `/task-coverage-review` - Analyze task coverage vs requirement docs
- `/task-help` - Show task management command help

### Task Tracking
- **TASKS.md** - Active task tracking
- **TASKS-ARCHIVE.md** - Completed tasks archive
- Tasks move through: TODO → IN PROGRESS → REVIEW → COMPLETED
- Each task has ID (TASK-XXX), priority (P0-P3), and acceptance criteria
- Complex tasks have detailed docs in ./docs/tasks/

### Human Review Workflow
**IMPORTANT**: All tasks require human review before implementation to ensure clarity and completeness.

#### Review Status
Each task has a **Human Review** field:
- ❌ Not Reviewed - Task needs human review before implementation
- ✅ Reviewed - Task has been reviewed and is ready for implementation

#### Review Process
1. **New Tasks**: Always created with ❌ Not Reviewed status
2. **Before Implementation**: `/task-implement` checks review status and prompts if not reviewed
3. **Review Prompt**: When review needed, Claude will:
   - Alert that task needs human review
   - Offer to help elaborate task details
   - Suggest breaking down complex requirements
   - Help clarify acceptance criteria
4. **Marking as Reviewed**: Only after human confirms task details are sufficient

#### Best Practices
- Review tasks immediately after creation when details are fresh
- Use Claude's assistance to elaborate complex tasks
- Ensure acceptance criteria are specific and measurable
- Consider edge cases and technical requirements during review
- Update task to ✅ Reviewed only when confident in task clarity

### Requirements Coverage Analysis
The `/task-coverage-review` command ensures alignment between requirement documents, tasks, and implementation:

#### Purpose
- Verify all requirements have corresponding tasks
- Identify inconsistencies between docs and tasks
- Find gaps in task coverage
- Detect over-specification or outdated requirements

#### Process
1. **Scan Documents**: Read vision.md, concepts.md, ux.md, technical-architecture.md
2. **Map Coverage**: Match requirements to existing tasks
3. **Check Implementation**: Verify completed tasks have code
4. **Identify Gaps**: Find missing tasks or inconsistencies
5. **Recommend Actions**: Suggest new tasks or doc updates

#### Quick Analysis
```bash
./scripts/requirements-coverage.sh  # Quick coverage summary
```

#### Outcomes
- **New Tasks**: Generated for uncovered requirements (marked ❌ Not Reviewed)
- **Doc Updates**: Remove inconsistencies or outdated specs
- **Traceability**: Link requirements to tasks for tracking
- **Priority Guidance**: Based on dependencies and requirements

### Task Report
```bash
./scripts/task-report.sh  # Generate task status summary
```

## Key Documentation

- **TASKS.md**: Current sprint and active task tracking
- **concepts.md**: Domain model and business logic
- **ux.md**: UI/UX specifications
- **technical-architecture.md**: System design details
- **database-schema.md**: Complete schema specification
- **development-workflow.md**: Development process
- **testing-strategy.md**: Testing approach
- **task-management-strategy.md**: Task tracking approach
- **clarifying-questions.md**: Technical decisions and rationale