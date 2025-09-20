# Art Factory Tasks (PyQt6 Desktop Architecture)

## Project Status
**Focus**: Desktop application foundation with PyQt6
**Last Updated**: 2025-09-20 (Architecture pivot to PyQt6 desktop)

### Task Summary
| Status | Count |
|--------|-------|
| Total Tasks | 15 |
| Completed | 1 |
| In Progress | 1 |
| Todo | 13 |
| Blocked | 0 |

---

## 🚀 Active Tasks

### TASK-011: Review Technical Architecture [IN PROGRESS]
**Started**: 2025-09-20
**Progress**: Pivoted architecture to PyQt6 desktop application

---

## 📋 Todo

### TASK-001: GitHub Repository Setup [TODO]
**Priority**: P0 - Critical
**Dependencies**: TASK-000 (completed)
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create GitHub repository
- [ ] Push local repository to GitHub
- [ ] Initialize README with PyQt6 desktop project overview
- [ ] Set up branch protection rules
- [ ] Create issue templates for desktop app

---

### TASK-100: PyQt6 Application Setup [TODO]
**Priority**: P0 - Critical
**Dependencies**: None
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create app directory structure
- [ ] Set up Python virtual environment
- [ ] Create requirements.txt with PyQt6 and core dependencies
- [ ] Implement basic QApplication and main window
- [ ] Add application icon and metadata
- [ ] Create run script for development
- [ ] Verify PyQt6 runs on macOS

---

### TASK-101: Signal Architecture Setup [TODO]
**Priority**: P0 - Critical
**Dependencies**: TASK-100
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create signals module with DomainSignals class
- [ ] Create UISignals class for user interactions
- [ ] Implement signal bus singleton pattern
- [ ] Add signal logging for debugging
- [ ] Write tests for signal emission and handling

---

### TASK-102: Database Models Implementation [TODO]
**Priority**: P0 - Critical
**Dependencies**: TASK-100
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Set up SQLAlchemy with SQLite
- [ ] Create base model with common fields
- [ ] Implement Project, Order, Product, Collection models
- [ ] Add Alembic for migrations
- [ ] Create database initialization script
- [ ] Implement soft delete support
- [ ] Write model tests

---

### TASK-103: Main Window and Layout [TODO]
**Priority**: P1 - High
**Dependencies**: TASK-100
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create QMainWindow with menu bar
- [ ] Implement dockable panels layout
- [ ] Add gallery as central widget
- [ ] Create parameter panel dock
- [ ] Add progress dock at bottom
- [ ] Implement view state persistence
- [ ] Add dark/light theme support

---

### TASK-104: Gallery Widget Implementation [TODO]
**Priority**: P1 - High
**Dependencies**: TASK-103
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create gallery grid widget
- [ ] Implement virtual scrolling for performance
- [ ] Add thumbnail loading with placeholders
- [ ] Support selection (single and multi)
- [ ] Add context menu for actions
- [ ] Implement drag and drop support
- [ ] Add image preview on click

---

### TASK-105: Controller Layer [TODO]
**Priority**: P1 - High
**Dependencies**: TASK-101, TASK-102
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create MainController for app coordination
- [ ] Implement GenerationController
- [ ] Create GalleryController
- [ ] Add ProjectController
- [ ] Connect controllers to signals
- [ ] Implement controller tests

---

### TASK-106: Service Layer Implementation [TODO]
**Priority**: P1 - High
**Dependencies**: TASK-102
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create OrderService for order management
- [ ] Implement GenerationService
- [ ] Create ProductService
- [ ] Add ProjectService
- [ ] Implement direct database access patterns
- [ ] Write service tests

---

### TASK-107: Base Factory Implementation [TODO]
**Priority**: P1 - High
**Dependencies**: TASK-106
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create BaseProductFactory abstract class
- [ ] Implement parameter validation
- [ ] Add parameter interpolation logic
- [ ] Implement token expansion ([red,blue,green])
- [ ] Create factory registry pattern
- [ ] Write comprehensive tests

---

### TASK-108: Worker Thread Framework [TODO]
**Priority**: P1 - High
**Dependencies**: TASK-101
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create base QThread worker class
- [ ] Implement GenerationWorker
- [ ] Add ImportWorker for file imports
- [ ] Support progress reporting
- [ ] Implement cancellation
- [ ] Add error handling
- [ ] Write worker tests with qtbot

---

### TASK-109: Replicate Provider Implementation [TODO]
**Priority**: P2 - Medium
**Dependencies**: TASK-107
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create ReplicateFactory class
- [ ] Implement Replicate API client
- [ ] Add model configuration
- [ ] Support image generation
- [ ] Handle API errors gracefully
- [ ] Store API key in keychain
- [ ] Test with mock API responses

---

### TASK-110: Image Viewer Widget [TODO]
**Priority**: P2 - Medium
**Dependencies**: TASK-104
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create image viewer with QGraphicsView
- [ ] Implement pan and zoom controls
- [ ] Add fit-to-window option
- [ ] Support high-resolution images
- [ ] Add basic image info display
- [ ] Implement fullscreen mode

---

### TASK-111: Parameter Panel UI [TODO]
**Priority**: P2 - Medium
**Dependencies**: TASK-103
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create parameter input widgets
- [ ] Support different parameter types
- [ ] Add parameter validation UI
- [ ] Implement parameter presets
- [ ] Add collapsible sections
- [ ] Support parameter dependencies

---

### TASK-112: Testing Infrastructure [TODO]
**Priority**: P2 - Medium
**Dependencies**: TASK-100
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Configure pytest with pytest-qt
- [ ] Set up test database fixtures
- [ ] Create Qt test helpers
- [ ] Add coverage reporting
- [ ] Set up CI with GitHub Actions
- [ ] Create pre-commit hooks

---

### TASK-113: PyInstaller Packaging [TODO]
**Priority**: P3 - Low
**Dependencies**: TASK-100
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create PyInstaller spec file
- [ ] Configure bundle metadata
- [ ] Include all resources
- [ ] Create macOS .app bundle
- [ ] Add code signing setup
- [ ] Create DMG installer
- [ ] Test on clean macOS

---

## ✅ Completed Tasks

### TASK-000: Local Git Initialization [COMPLETED]
**Completed**: 2025-09-20
**Outcome**: Git repository initialized with comprehensive workflow setup
- Initialized git repository with main branch
- Created comprehensive .gitignore for Python/Node.js/IDE/OS files
- Set up commit message template
- Made initial commit with all project documentation
- Updated workflow documentation for solo developer approach
- Added git aliases and workflow guidelines to CLAUDE.md

---

## 🔄 Backlog

### Phase 2: Additional Features

- Additional Providers (fal.ai, Civitai)
- Collections Management UI
- Template System
- Advanced Search and Filtering
- Batch Operations
- Export/Import Functionality
- Statistics Dashboard
- User Preferences Dialog
- Keyboard Shortcuts
- Video Player Widget

### Phase 3: Polish & Distribution

- Performance Optimization
- Memory Management
- Apple Notarization
- Auto-update System
- Crash Reporting
- User Documentation
- Demo Content

---

## 📝 Notes

### Context for Claude Code
- Desktop application using PyQt6
- Python-only development (no web stack)
- Direct database access with SQLAlchemy
- Signal-based architecture for clean separation
- Target is macOS initially

### Development Approach
1. Foundation first (app setup, signals, database)
2. Core UI components (main window, gallery)
3. Business logic (controllers, services)
4. Provider integration
5. Polish and packaging

---

*Last Updated: 2025-09-20*