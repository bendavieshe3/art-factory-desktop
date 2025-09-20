"""UI signals for user interface events in Art Factory.

These signals represent user interface interaction events, such as
user actions, view changes, and UI state updates.
"""

# Type hints for signal parameters
from PyQt6.QtCore import QObject, pyqtSignal


class UISignals(QObject):
    """User interface interaction signals.

    Signals:
        request_generation: User requests a new generation
        request_cancel: User requests to cancel an operation
        view_changed: User switches between different views
        selection_changed: Selection changes in gallery or list
        filter_applied: User applies filters to content
        loading_started: UI begins a loading operation
        loading_finished: UI completes a loading operation
        error_occurred: An error needs to be displayed to the user

    Example:
        signals = UISignals()
        signals.request_generation.connect(handle_generation_request)
        signals.request_generation.emit({"prompt": "A cat", "steps": 20})
    """

    # User action events
    request_generation = pyqtSignal(dict)  # parameters dict
    request_cancel = pyqtSignal(str)  # item_id to cancel
    request_regenerate = pyqtSignal(str)  # product_id to regenerate

    # View state events
    view_changed = pyqtSignal(str)  # view_name (e.g., "projects", "gallery")
    selection_changed = pyqtSignal(list)  # list of selected item IDs
    filter_applied = pyqtSignal(dict)  # filter parameters

    # UI state events
    loading_started = pyqtSignal(str)  # task_name describing what's loading
    loading_finished = pyqtSignal()  # loading complete
    error_occurred = pyqtSignal(str)  # error_message to display

    # Navigation events
    page_changed = pyqtSignal(int)  # page number for paginated views
    search_requested = pyqtSignal(str)  # search query

    def __init__(self):
        """Initialize UISignals."""
        super().__init__()
