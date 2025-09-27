"""
Parameter panel for generation controls.

Left-docked panel for configuring and creating new generations.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QTextEdit,
    QPushButton,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal


class ParameterPanel(QWidget):
    """
    Left dock panel for generation parameters and controls.

    Provides interface for:
    - Provider and model selection
    - Parameter configuration
    - Order placement
    - Template management
    """

    # Signals
    generation_requested = pyqtSignal(dict)  # parameters
    template_saved = pyqtSignal(str, dict)  # name, parameters
    template_loaded = pyqtSignal(dict)  # parameters

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the parameter panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Title
        title_label = QLabel("Generate Product")
        title_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #333;"
        )
        layout.addWidget(title_label)

        # Scroll area for parameters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Parameters widget
        params_widget = QWidget()
        params_layout = QVBoxLayout(params_widget)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(8)

        # Provider selection
        provider_group = QGroupBox("Provider & Model")
        provider_layout = QVBoxLayout(provider_group)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Replicate", "fal.ai", "Civitai"])
        provider_layout.addWidget(QLabel("Provider:"))
        provider_layout.addWidget(self.provider_combo)

        self.model_combo = QComboBox()
        self.model_combo.addItems(
            [
                "stability-ai/sdxl",
                "stability-ai/stable-diffusion-xl-base-1.0",
                "black-forest-labs/flux-schnell",
            ]
        )
        provider_layout.addWidget(QLabel("Model:"))
        provider_layout.addWidget(self.model_combo)

        params_layout.addWidget(provider_group)

        # Prompt section
        prompt_group = QGroupBox("Prompt")
        prompt_layout = QVBoxLayout(prompt_group)

        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("Enter your prompt here...")
        self.prompt_text.setMaximumHeight(100)
        prompt_layout.addWidget(self.prompt_text)

        self.negative_prompt_text = QTextEdit()
        self.negative_prompt_text.setPlaceholderText(
            "Negative prompt (optional)..."
        )
        self.negative_prompt_text.setMaximumHeight(60)
        prompt_layout.addWidget(QLabel("Negative Prompt:"))
        prompt_layout.addWidget(self.negative_prompt_text)

        params_layout.addWidget(prompt_group)

        # Basic parameters
        basic_group = QGroupBox("Basic Parameters")
        basic_layout = QVBoxLayout(basic_group)

        # Steps
        steps_layout = QHBoxLayout()
        steps_layout.addWidget(QLabel("Steps:"))
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(1, 100)
        self.steps_spin.setValue(30)
        steps_layout.addWidget(self.steps_spin)
        steps_layout.addStretch()
        basic_layout.addLayout(steps_layout)

        # Guidance scale
        guidance_layout = QHBoxLayout()
        guidance_layout.addWidget(QLabel("Guidance Scale:"))
        self.guidance_spin = QDoubleSpinBox()
        self.guidance_spin.setRange(1.0, 20.0)
        self.guidance_spin.setValue(7.5)
        self.guidance_spin.setSingleStep(0.5)
        guidance_layout.addWidget(self.guidance_spin)
        guidance_layout.addStretch()
        basic_layout.addLayout(guidance_layout)

        # Seed
        seed_layout = QHBoxLayout()
        seed_layout.addWidget(QLabel("Seed:"))
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(-1, 2147483647)
        self.seed_spin.setValue(-1)  # -1 for random
        seed_layout.addWidget(self.seed_spin)
        self.random_seed_check = QCheckBox("Random")
        self.random_seed_check.setChecked(True)
        seed_layout.addWidget(self.random_seed_check)
        seed_layout.addStretch()
        basic_layout.addLayout(seed_layout)

        params_layout.addWidget(basic_group)

        # Advanced parameters (collapsible)
        self.advanced_group = QGroupBox("Advanced Parameters")
        self.advanced_group.setCheckable(True)
        self.advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout(self.advanced_group)

        # Width/Height
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(256, 2048)
        self.width_spin.setValue(1024)
        self.width_spin.setSingleStep(64)
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("×"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(256, 2048)
        self.height_spin.setValue(1024)
        self.height_spin.setSingleStep(64)
        size_layout.addWidget(self.height_spin)
        size_layout.addStretch()
        advanced_layout.addLayout(size_layout)

        params_layout.addWidget(self.advanced_group)

        # Stretch to push controls to top
        params_layout.addStretch()

        scroll_area.setWidget(params_widget)
        layout.addWidget(scroll_area)

        # Action buttons
        buttons_layout = QHBoxLayout()

        self.template_button = QPushButton("Templates...")
        self.template_button.setEnabled(False)  # Placeholder
        buttons_layout.addWidget(self.template_button)

        buttons_layout.addStretch()

        self.generate_button = QPushButton("Generate")
        self.generate_button.setStyleSheet(
            """
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """
        )
        buttons_layout.addWidget(self.generate_button)

        layout.addLayout(buttons_layout)

    def _connect_signals(self):
        """Connect internal signals."""
        self.generate_button.clicked.connect(self._on_generate_clicked)
        self.random_seed_check.toggled.connect(self._on_random_seed_toggled)

    def _on_generate_clicked(self):
        """Handle generate button click."""
        parameters = self.get_parameters()
        self.generation_requested.emit(parameters)

    def _on_random_seed_toggled(self, checked):
        """Handle random seed checkbox toggle."""
        self.seed_spin.setEnabled(not checked)
        if checked:
            self.seed_spin.setValue(-1)

    def get_parameters(self):
        """Get current parameter values as dict."""
        return {
            "provider": self.provider_combo.currentText().lower(),
            "model": self.model_combo.currentText(),
            "prompt": self.prompt_text.toPlainText(),
            "negative_prompt": self.negative_prompt_text.toPlainText(),
            "steps": self.steps_spin.value(),
            "guidance_scale": self.guidance_spin.value(),
            "seed": (
                self.seed_spin.value()
                if not self.random_seed_check.isChecked()
                else -1
            ),
            "width": self.width_spin.value(),
            "height": self.height_spin.value(),
        }

    def set_parameters(self, parameters):
        """Set parameter values from dict."""
        if "provider" in parameters:
            provider_text = parameters["provider"].title()
            index = self.provider_combo.findText(provider_text)
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)

        if "model" in parameters:
            index = self.model_combo.findText(parameters["model"])
            if index >= 0:
                self.model_combo.setCurrentIndex(index)

        if "prompt" in parameters:
            self.prompt_text.setPlainText(parameters["prompt"])

        if "negative_prompt" in parameters:
            self.negative_prompt_text.setPlainText(
                parameters["negative_prompt"]
            )

        if "steps" in parameters:
            self.steps_spin.setValue(parameters["steps"])

        if "guidance_scale" in parameters:
            self.guidance_spin.setValue(parameters["guidance_scale"])

        if "seed" in parameters:
            seed = parameters["seed"]
            if seed == -1:
                self.random_seed_check.setChecked(True)
                self.seed_spin.setValue(-1)
            else:
                self.random_seed_check.setChecked(False)
                self.seed_spin.setValue(seed)

        if "width" in parameters:
            self.width_spin.setValue(parameters["width"])

        if "height" in parameters:
            self.height_spin.setValue(parameters["height"])

    def enable_generation(self, enabled=True):
        """Enable or disable generation controls."""
        self.generate_button.setEnabled(enabled)
        self.generate_button.setText(
            "Generate" if enabled else "Generating..."
        )
