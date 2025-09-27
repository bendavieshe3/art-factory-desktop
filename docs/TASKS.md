# Art Factory Tasks (PyQt6 Desktop Architecture)

## Project Status
**Focus**: Desktop application foundation with PyQt6
**Last Updated**: 2025-09-27 (TASK-104 Gallery Widget completed - comprehensive product browsing UI ready)

### Task Summary
| Status | Count |
|--------|-------|
| Total Tasks | 28 |
| Completed | 9 |
| In Progress | 0 |
| Todo | 19 |
| Blocked | 0 |

---

## 🚀 Active Tasks

### TASK-105: Controller Layer [IN PROGRESS]
**Progress**: 0% - Just started
**Next Steps**: Create MainController base class and signal bus integration

---

## 📋 Todo

### TASK-105: Controller Layer [IN PROGRESS]
**Priority**: P1 - High
**Dependencies**: TASK-101 ✅, TASK-102 ✅
**Human Review**: ✅ Reviewed
**Started**: 2025-09-27

**Acceptance Criteria**:
- [ ] Create MainController for application coordination (singleton with signal bus)
- [ ] Implement GenerationController for AI workflow (order → generation → products)
- [ ] Create GalleryController for product management (data loading, selection, file ops)
- [ ] Add ProjectController for project lifecycle (CRUD, switching, project-specific data)
- [ ] Connect controllers to signal bus with clear ownership patterns
- [ ] Implement controller tests (unit tests with mocked dependencies, signal testing)

**Implementation Specifications**:
- **MainController**: Central coordinator managing other controllers, application state, cross-cutting concerns
- **GenerationController**: Parameter panel → OrderService → Generation workflow → Progress tracking
- **GalleryController**: Product data loading, selection state, file import/export, search/filtering
- **ProjectController**: Project CRUD, active project management, project-specific data coordination
- **Signal Integration**: Each controller owns specific signal groups, communicate via signal bus
- **Testing**: pytest-qt for signal testing, mocked dependencies, integration tests for coordination
- **Architecture**: MVC pattern with controllers mediating between views and services

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


### TASK-201: File Storage System [TODO]
**Priority**: P0 - Critical
**Dependencies**: TASK-100
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Implement organized directory structure for products
- [ ] Create automatic thumbnail generation (small/medium/large)
- [ ] Add file deduplication using SHA256 hashes
- [ ] Implement storage quota management
- [ ] Create file cleanup and maintenance routines
- [ ] Support multiple file formats (images, videos)
- [ ] Add file metadata extraction

---

### TASK-202: Provider Service Framework [TODO]
**Priority**: P0 - Critical
**Dependencies**: TASK-107
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create abstract provider API client management
- [ ] Implement API key storage in system keychain
- [ ] Add rate limiting and quota management
- [ ] Create error handling and retry logic
- [ ] Implement provider discovery and registration
- [ ] Add provider health checking
- [ ] Write provider integration tests

---

### TASK-203: Project Management UI [TODO]
**Priority**: P1 - High
**Dependencies**: TASK-103
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create project overview with grid of project cards
- [ ] Implement project detail pages with statistics
- [ ] Add featured product management interface
- [ ] Create project creation and editing dialogs
- [ ] Support project status management (active/archived)
- [ ] Add project search and filtering
- [ ] Implement project-level settings

---

### TASK-204: Order Creation Interface [TODO]
**Priority**: P1 - High
**Dependencies**: TASK-111, TASK-202
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create dynamic parameter form based on provider/model
- [ ] Implement parameter validation with inline feedback
- [ ] Add template loading and saving functionality
- [ ] Create order preview with expansion display
- [ ] Support batch order submission
- [ ] Add parameter hints and documentation
- [ ] Implement form state persistence

---

### TASK-205: Product Gallery Interface [TODO]
**Priority**: P1 - High
**Dependencies**: TASK-104, TASK-201
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Implement grid and list view toggles
- [ ] Add advanced filtering (type, date, project, tags)
- [ ] Create sorting options (date, size, rating)
- [ ] Support product selection and bulk operations
- [ ] Add lazy loading for performance
- [ ] Implement virtual scrolling for large collections
- [ ] Create product context menus

---

### TASK-206: Product Viewer Modal [TODO]
**Priority**: P1 - High
**Dependencies**: TASK-205
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create full-screen viewing with zoom and pan
- [ ] Add navigation between products in collection
- [ ] Implement metadata display sidebar
- [ ] Create action toolbar (download, favorite, regenerate)
- [ ] Support keyboard navigation
- [ ] Add image comparison mode
- [ ] Implement slideshow functionality

---

### TASK-207: Template System [TODO]
**Priority**: P2 - Medium
**Dependencies**: TASK-200
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Enable template creation from successful orders
- [ ] Create template management interface
- [ ] Support template categorization and tagging
- [ ] Implement template application to new orders
- [ ] Add template sharing and export
- [ ] Create template version management
- [ ] Support template parameter overrides

---

### TASK-208: Collection Management [TODO]
**Priority**: P2 - Medium
**Dependencies**: TASK-205
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create user-defined product collections
- [ ] Implement collection creation and management UI
- [ ] Add drag-and-drop product organization
- [ ] Support collection sharing and export
- [ ] Create smart collections with auto-rules
- [ ] Implement collection-level operations
- [ ] Add collection statistics and insights

---

### TASK-209: Advanced Provider Support [TODO]
**Priority**: P2 - Medium
**Dependencies**: TASK-202
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Implement fal.ai provider factory
- [ ] Create civitai provider integration
- [ ] Add provider capability discovery
- [ ] Support provider-specific features
- [ ] Implement provider switching logic
- [ ] Create provider comparison tools
- [ ] Add provider performance monitoring

---

### TASK-210: Progress Tracking System [TODO]
**Priority**: P2 - Medium
**Dependencies**: TASK-108, TASK-200
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create real-time generation progress updates
- [ ] Implement background task monitoring dashboard
- [ ] Add queue management and prioritization
- [ ] Support task cancellation and retry
- [ ] Create progress persistence across app restarts
- [ ] Add estimated completion time calculations
- [ ] Implement progress notifications

---

### TASK-211: Settings and Admin Interface [TODO]
**Priority**: P2 - Medium
**Dependencies**: TASK-103
**Human Review**: ❌ Not Reviewed

**Acceptance Criteria**:
- [ ] Create application preferences dialog
- [ ] Implement provider configuration management
- [ ] Add storage location and quota settings
- [ ] Create system diagnostics panel
- [ ] Support theme and appearance settings
- [ ] Add keyboard shortcuts configuration
- [ ] Implement backup and restore functionality

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

### TASK-114: Dark Theme Visual Refinement [TODO]
**Priority**: P2 - Medium
**Dependencies**: TASK-103
**Human Review**: ✅ Reviewed
**Created**: 2025-09-27

**Acceptance Criteria**:
- [ ] Fix project card styling in dark theme (contrast and borders)
- [ ] Improve text readability across all panels in dark theme
- [ ] Adjust button colors and hover states for dark backgrounds
- [ ] Fix dropdown and combo box styling in dark theme
- [ ] Ensure status indicators are visible in dark theme
- [ ] Update progress bars and group boxes for better dark theme appearance
- [ ] Test and refine scroll bar styling in dark theme
- [ ] Ensure all icons and symbols are visible in dark theme

**Implementation Notes**:
- Defer implementation until after core interface stabilizes
- Default theme should remain "light" until dark theme is polished
- Consider using Qt's built-in Fusion style as base for dark theme
- May need custom widget painting for some components
- Test on both standard and Retina displays

---

## ✅ Completed Tasks

### TASK-104: Gallery Widget Implementation [COMPLETED]
**Priority**: P1 - High
**Dependencies**: TASK-103 ✅
**Completed**: 2025-09-27

**Delivered**:
- ✅ Created responsive gallery grid widget (4-8 columns based on window width)
- ✅ Implemented virtual scrolling with 50-item buffer for performance
- ✅ Added thumbnail loading system with background QThread processing
- ✅ Built comprehensive selection system (single/multi/keyboard navigation)
- ✅ Created context menus with single and bulk actions
- ✅ Implemented drag and drop (file export + external file import)
- ✅ Built image preview modal with zoom, pan, and navigation
- ✅ Integrated with signal bus for UI coordination
- ✅ Added to main window replacing gallery placeholder
- ✅ Created test suite covering core functionality

**Components Created**:
- `GalleryWidget`: Main grid view with virtual scrolling and selection
- `GalleryItemWidget`: Individual product thumbnail with interaction
- `ThumbnailLoader`: Background image loading and caching system
- `ImagePreviewModal`: Full-size image viewer with controls
- `ThumbnailCache`: QPixmapCache wrapper for performance

**Impact**: Complete gallery functionality enabling product browsing, selection, and preview with professional-grade performance and UX.

---

### TASK-200: Order Management Service [COMPLETED]
**Priority**: P0 - Critical
**Dependencies**: TASK-102 ✅
**Completed**: 2025-09-27

**Delivered**:
- ✅ Complete OrderService with parameter expansion engine
- ✅ Two-phase implementation: basic order management + advanced expansion
- ✅ Token expansion: `[red,blue,green]` → multiple OrderItems
- ✅ Range interpolation: `steps:10..20` → step-by-step values
- ✅ Sub-prompt expansion: `"dog || cat"` → separate prompts
- ✅ Complex combination handling: tokens + ranges + sub-prompts
- ✅ Parameter validation framework with type checking
- ✅ Expansion preview functionality for UI integration
- ✅ Configurable limits with descriptive error handling
- ✅ Comprehensive test suite (23 tests) covering all scenarios
- ✅ Database integration with proper transaction management
- ✅ Order status management based on OrderItem completion

**Impact**: Core business logic foundation enabling AI generation workflow with sophisticated parameter expansion capabilities.

---

### TASK-103: Main Window and Layout [COMPLETED]
**Priority**: P1 - High
**Dependencies**: TASK-100
**Completed**: 2025-09-27

**Delivered**:
- ✅ Created QMainWindow with comprehensive menu bar (File, Edit, View, Tools, Help)
- ✅ Implemented dockable panels with proper workflow separation
- ✅ Added projects overview as central widget (default view)
- ✅ Created parameter panel (left dock) for generation controls
- ✅ Created metadata panel (right dock) for product inspection
- ✅ Added progress panel (bottom dock) for generation monitoring
- ✅ Implemented view state persistence using QSettings
- ✅ Added dark/light theme support with toggle (light as default)
- ✅ **NEW**: Screen-based navigation system (Projects/Generate/Gallery)
- ✅ **NEW**: Smart panel visibility management based on application context
- ✅ **NEW**: PreviewPanel widget for Generate screen center area
- ✅ **NEW**: Renamed "Parameter Panel" to "Generate Product" for clarity

**Notes**:
- Implemented spatial workflow as requested: left for creation, right for inspection
- Responsive grid layout for project cards
- Signal bus integration throughout
- Screen navigation provides intuitive user experience
- Dark theme needs refinement (see TASK-114)

---

### TASK-102: Database Models Implementation [COMPLETED]
**Completed**: 2025-09-27
**Outcome**: Successfully implemented SQLAlchemy models with SQLite backend
- Created BaseModel with UUID primary keys, timestamps, and soft delete support
- Implemented Project, Order, OrderItem, Product, Collection, and CollectionProduct models
- Added JSON field handling for SQLite using TEXT serialization
- Built comprehensive database manager with session handling and foreign key support
- Created extensive test suite covering all models and relationships
- All tests passing with proper code formatting and linting
- Updated database schema documentation for SQLite implementation

### TASK-011: Review Technical Architecture [COMPLETED]
**Completed**: 2025-09-20
**Outcome**: Successfully pivoted to PyQt6 desktop architecture
- Rewrote technical-architecture.md for PyQt6 desktop application
- Defined signal-driven architecture with clean separation of concerns
- Created comprehensive application structure and component hierarchy
- Documented event/signal strategy for UI and domain events
- Replaced old web-based task list with PyQt6-focused tasks
- Updated development workflow for desktop development
- Removed all web-related components (FastAPI, React, Docker)

### TASK-101: Signal Architecture Setup [COMPLETED]
**Completed**: 2025-09-20
**Outcome**: Successfully implemented comprehensive signal-based architecture
- Created app/signals/ module with DomainSignals and UISignals classes
- Implemented SignalBus singleton pattern with debug logging capabilities
- Added 12 domain signals for business events (orders, generation, products, projects)
- Added 10 UI signals for user interface interactions
- Built comprehensive test suite with 28 tests covering all signal functionality
- Integrated signal bus with MainWindow for real-time status updates
- All tests passing with excellent code coverage

### TASK-100: PyQt6 Application Setup [COMPLETED]
**Completed**: 2025-09-20
**Outcome**: Successfully established PyQt6 desktop application foundation
- Created Python 3.13.3 virtual environment with PyQt6 6.7.0
- Established minimal app directory structure (models, views, resources, utils)
- Implemented QApplication setup with metadata configuration
- Created main window with menu bar, central placeholder, and status bar
- Added development run script with debug mode support
- Verified PyQt6 functionality on macOS with comprehensive testing
- All core dependencies installed and working correctly

### TASK-001: GitHub Repository Setup [COMPLETED]
**Completed**: 2025-09-27
**Outcome**: GitHub repository created and configured
- Created GitHub repository as art-factory-desktop
- Pushed local repository to GitHub with SSH authentication
- Updated README with proper repository URLs and project distinction
- Set up branch protection rules for main branch
- Created comprehensive issue templates for bug reports, features, UI/UX, and provider integration
- Added issue template configuration with helpful links

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

### Phase 3: Advanced Features

- Export/Import Functionality
- Statistics Dashboard
- Video Player Widget
- Batch Operations (advanced)
- Advanced Search with AI
- Automation and Workflows

### Phase 4: Polish & Distribution

- Performance Optimization
- Memory Management
- Apple Notarization
- Auto-update System
- Crash Reporting
- User Documentation
- Demo Content
- Internationalization

---

## 📝 Notes

### Context for Claude Code
- Desktop application using PyQt6
- Python-only development (no web stack)
- Direct database access with SQLAlchemy
- Signal-based architecture for clean separation
- Target is macOS initially
- Architecture documented in technical-architecture.md
- Development workflow in development-workflow.md

### Development Approach
1. Foundation first (app setup, signals, database)
2. Core UI components (main window, gallery)
3. Business logic (controllers, services)
4. Provider integration
5. Polish and packaging

---

## 🏆 **Major Milestone**: Foundation Complete (25% Done)

✅ **Infrastructure**: Application setup, signals, database, main window
✅ **UI Framework**: Navigation system, panel management, responsive layout
🎯 **Next Phase**: Core business logic and service layer implementation

**Recommended Next Tasks**:
1. **TASK-200** - Order Management Service (enables generation workflow)
2. **TASK-104** - Gallery Widget Implementation (completes core UI)
3. **TASK-105** - Controller Layer (application coordination)

---

*Last Updated: 2025-09-27*