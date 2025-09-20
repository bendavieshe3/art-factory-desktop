# Art Factory User Experience (PyQt6 Desktop)

This document defines the user interface requirements, layouts, and interaction patterns for Art Factory desktop application.

## Design Principles

### Native Desktop Design
- Optimized for macOS desktop experience
- Native PyQt6 widgets and interactions
- Consistent with macOS Human Interface Guidelines
- Progressive disclosure of complexity through docks and dialogs

### User-Centered Approach
- Minimize cognitive load for common tasks
- Clear visual hierarchy with native controls
- Immediate feedback for user actions
- Graceful error handling with native dialogs

## Application Structure

### Main Window Layout
The application uses a QMainWindow with dockable panels:

- **Central Widget**: Primary content area (Projects overview or Gallery)
- **Menu Bar**: File, Edit, View, Tools, Window, Help
- **Toolbar**: Quick access to common actions
- **Dockable Panels**: Parameter panel, progress panel, metadata panel
- **Status Bar**: Current operation status and system information

### Navigation Sections
Main application modes accessible via menu or toolbar:

- **Projects Mode**: Project management and overview (default)
- **Gallery Mode**: Browse and manage all products
- **Order Mode**: Create new orders with parameter forms
- **Monitoring Mode**: Track generation progress and system status

### Native UI Elements

#### Menu Bar
- **File**: New Project, Import, Export, Preferences, Quit
- **Edit**: Undo, Redo, Cut, Copy, Paste, Select All
- **View**: Show/Hide panels, Zoom, Full Screen
- **Tools**: Providers, Templates, Collections
- **Window**: Minimize, Zoom, standard window controls
- **Help**: Documentation, About

#### Toolbars
- Customizable quick access to frequent actions
- Icon + text labels for clarity
- Context-sensitive tools based on current mode

#### Dockable Panels
- **Parameter Panel**: Model selection and parameter controls
- **Progress Panel**: Active generations and queue
- **Metadata Panel**: Selected product information
- **Collections Panel**: User-defined product groups

#### Error Handling
- Native QMessageBox dialogs for errors
- Toast-style notifications for non-critical feedback
- Inline validation in forms with visual indicators
- Progress dialogs for long-running operations

## Main Sections

### Projects Mode (Default View)

**Purpose**: Primary entry point and organizational hub for all work

#### Projects Overview Widget
**Layout**:
- QScrollArea with project cards in grid layout
- Each project card (custom QWidget) showing:
  - Project name and description
  - Featured product thumbnails (3-4 images using QLabel)
  - Order count and product count (QLabel with metrics)
  - Last activity timestamp
  - Status indicator with colored icon
  - Context menu for actions (view, edit, archive)
- QToolButton for "Create New Project"
- QLineEdit search bar with live filtering
- QComboBox and QDateEdit for filtering

**Actions**:
- Create new project with QDialog form
- Double-click project card to view details
- Context menu actions: View Details, Edit, Archive, Duplicate
- Search with live filtering as user types
- Sort by name, date, activity using QHeaderView

#### Project List Widget (Alternative View)
**Layout**:
- QTableWidget with sortable columns
- Columns: Name, Description, Status, Orders, Products, Created, Updated
- QHeaderView with sorting capabilities
- Custom QItemDelegate for rich cell content
- QProgressBar for loading states

**Actions**:
- Multi-selection with Ctrl/Cmd+click
- Bulk operations via context menu
- Export to CSV via File menu
- Column customization via right-click header

#### Project Detail Dialog
**Layout**:
- QDialog with tabbed interface (QTabWidget):
  - **Overview Tab**: Project info and statistics
  - **Products Tab**: Filtered gallery view
  - **Orders Tab**: Order history list
  - **Settings Tab**: Project configuration
- Statistics display using custom QWidget with charts
- QPushButton actions: Edit, Archive, Delete, Close

**Actions**:
- Edit project details with inline editing
- Manage featured products with drag-and-drop
- Create new order with pre-filled project context
- Switch to gallery mode with project filter active

### Order Section

**Purpose**: Place new orders and monitor recent activity

#### Layout Components

**Order Form** (top/left):
- Provider and model selection dropdown
- Dynamic parameter form based on selection
- Prompt text area with smart token support
- Advanced parameters (collapsible)
- "Place Order" button with validation

**Preview Area** (top/right):
- A place to show the outputs of the last generation when it is complete
- If we implement result streaming from the APIs, the product will be progressively rendered or have actual progress shown

**Recent Products** (Product Collection - Strip Layout)
- Horizontal strip of recently created products using compact Product Cards
- Updated live; when a new product is generated it is added to the left, and products are removed from the right
- Provides navigation context when opening the product viewer modal 


**Recent Orders List** (bottom/right):
- Shows: ID, model used, status, timestamp
- Expandable to show order items
- Status updates in real-time



#### Functionality
- Dynamic form field updates based on model selection
- Form validation with inline error messages
- Asynchronous order submission
- Real-time status updates
- Parameter preservation across form changes

### Production Section

**Purpose**: Monitor generation progress and system status

#### Production Summary
- Key metrics: incomplete orders, active workers
- System status indicators
- Recent activity overview

#### Active Orders
- List of orders in progress
- Progress indicators and status
- Estimated completion times
- Error states and retry options

#### System Status
- Background worker status
- API rate limit information
- Recent system events and logs

### Inventory Section

**Purpose**: Browse, manage, and organize generated products

#### Layout Components

**Product Display Area** (main area):
- Toggle between grid and list views
- Area controls:
  - View toggle (grid/list)
  - Sorting (latest, earliest, file size)
  - Grouping (none, project, order)
  - Filtering (all, images, videos, other)

**Product Detail Sidebar** (right side):
- Fixed to right side of screen
- Shows selected product details:
  - Large thumbnail (clickable for full view)
  - Prompt text (truncated with "more" option)
  - Metadata (type, date, size)
  - Input/output parameters (expandable)
  - Action buttons (download, reorder, delete)

**Product Viewer Modal**:
A sophisticated full-screen viewing experience for products:

**Core Features**:
- Full-screen dark modal overlay
- Maximum viewport utilization for image display
- Smooth zoom and pan functionality:
  - Mouse wheel zoom (10% - 500%)
  - Click and drag to pan when zoomed
  - Zoom controls with reset button
- Navigation between products in collection:
  - Previous/Next buttons with visual indicators
  - Keyboard arrow key navigation
  - Maintains collection context from entry point
- Collapsible information sidebar:
  - Product metadata and parameters
  - File information (dimensions, size, creation date)
  - Order and factory machine details
  - Action toolbar (download, favorite, regenerate, delete)
  - External toggle button for accessibility

**User Interactions**:
- Click on product card "View" button to open
- Escape key or close button to dismiss
- Browser back button integration (pending Issue #67)
- Arrow keys for product navigation
- Mouse wheel for zoom control
- Click and drag for panning zoomed images
- All actions provide immediate feedback

**Technical Implementation**:
- Overlays content rather than pushing layout
- Sidebar floats over image area when expanded
- Smart data fetching ensures all metadata available
- Responsive design adapts to screen size
- Accessibility features include ARIA labels and keyboard navigation

#### Product Grid View
- Responsive grid layout
- Product cards with:
  - Thumbnail image or type icon
  - Product type badge
  - Selection indicator
  - Hover tooltip with metadata
  - Quick action controls

#### Product List View
- Vertical list with:
  - Small thumbnail/icon
  - Product name and type
  - Creation date and file size
  - Quick action buttons
  - Selection checkbox

#### Functionality
- Product selection (single/multiple)
- Real-time updates for new products
- Smooth transitions for deletions
- Keyboard navigation (arrow keys, spacebar)
- Bulk operations on selected products

### Admin Section

**Purpose**: System configuration and monitoring

#### Settings
- API key management
- Default parameter configuration
- File storage settings
- Disk space monitoring
- System reset options

#### Events & Logs
- Recent system events
- Error logs and debugging information
- Event filtering and search
- System health monitoring

## Reusable Components

### Product Card
**Definition**: The visual representation of a product (image + optional metadata/actions)

**Variants**:
- **Compact**: Image only with hover overlay (used in thumbnail strips)
- **Standard**: Image + title + basic metadata (used in inventory grid)
- **Detailed**: Full information display (future use in search results)

**Features**:
- Thumbnail with type indicator
- Metadata overlay on hover
- Selection state visualization
- Quick action menu
- Consistent behavior across all contexts

### Product Collection
**Definition**: A container that manages and displays multiple Product Cards

**Layouts**:
- **Grid**: Responsive grid layout (inventory page)
- **Strip**: Horizontal scrolling strip (order page recent products)
- **List**: Vertical list with details (future search results)
- **Masonry**: Pinterest-style layout (future gallery view)

**Features**:
- Manages selection state across products
- Provides navigation context for viewer modal
- Handles filtering and sorting
- Supports bulk operations
- Real-time updates via WebSocket

### Parameter Form
- Dynamic field generation
- Smart token input with autocomplete
- Parameter validation and hints
- Collapsible advanced sections
- Template loading/saving

### Status Indicators
- Generation progress bars
- Real-time status badges
- Error state indicators
- System health indicators

## Interaction Patterns

### Selection
- Click product card/thumbnail to select
- Selected state clearly indicated
- Multi-select with Ctrl/Cmd+click
- Keyboard navigation with arrow keys

### Actions
- Primary actions prominently displayed
- Secondary actions in context menus
- Confirmation for destructive actions
- Undo capability where appropriate

### Real-time Updates
- Smooth animations for content changes
- Progress indicators for long operations
- Graceful handling of connection issues
- Clear feedback for user actions

## Accessibility

### Keyboard Navigation
- Tab order follows logical flow
- Arrow keys for grid/list navigation
- Spacebar for selection/activation
- Escape for modal dismissal

### Screen Reader Support
- Proper ARIA labels and roles
- Descriptive text for images
- Status announcements
- Form validation messages

### Visual Design
- Sufficient color contrast
- Clear visual hierarchy
- Consistent interaction patterns
- Responsive text sizing

## Performance Considerations

### Image Loading
- Lazy loading for large galleries
- Progressive image enhancement
- Thumbnail optimization
- Efficient caching strategies

### Interface Responsiveness
- Immediate UI feedback
- Non-blocking operations
- Progressive loading indicators
- Graceful degradation

### Memory Management
- Efficient DOM handling
- Image memory optimization
- Cleanup of unused resources
- Pagination for large datasets