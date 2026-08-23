# color_ramp_editor.py
import os
import sys
from functools import partial

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QLinearGradient
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QFileDialog,
    QSlider, QDoubleSpinBox, QSizePolicy, QAbstractItemView
)

from ColorReliefEditor.color_ramp_hsv import read_color_file, adjust_color_table


class ColorGradientWidget(QWidget):
    """
    Widget to display a color sample with gradients between elevation level colors.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.color_table = []
        self.setMinimumWidth(120)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def set_color_table(self, color_table: list):
        """Updates the widget with a new color table and triggers a repaint."""
        # Filter out non-data lines for gradient rendering
        self.color_table = [row[1] for row in color_table if row[0] is True]
        self.update() # Schedule a repaint

    def scale_color_bands(self):
        """
        Calculates the rendering parameters for each color band in the gradient.
        """
        bands = []
        if len(self.color_table) < 2:
            return bands

        min_y = min(self.color_table, key=lambda x: x[0])[0]
        max_y = max(self.color_table, key=lambda x: x[0])[0]

        # Avoid division by zero if all elevations are the same
        if min_y == max_y:
            return bands

        offset = -min_y if min_y < 0 else 0
        total_range = (max_y + offset) - (min_y + offset)
        widget_height = self.height()

        for i in range(len(self.color_table) - 1):
            elev1, r1, g1, b1, _ = self.color_table[i]
            elev2, r2, g2, b2, _ = self.color_table[i+1]

            # Calculate y position, scaling from elevation to widget coordinates
            y1 = widget_height - ((elev1 + offset) * widget_height / total_range)
            y2 = widget_height - ((elev2 + offset) * widget_height / total_range)

            c1 = QColor(r1, g1, b1)
            c2 = QColor(r2, g2, b2)

            gradient = QLinearGradient(0, y1, 0, y2)
            gradient.setColorAt(0, c1)
            gradient.setColorAt(1, c2)

            bands.append((gradient, y2, y1 - y2)) # y-pos is top of rect

        return bands

    def paintEvent(self, event):
        """Draws the color bands on the widget."""
        painter = QPainter(self)
        # Paint a default background
        painter.fillRect(self.rect(), QColor("#2b2b2b"))

        for gradient, y, height in self.scale_color_bands():
            painter.fillRect(self.rect().x(), y, self.width(), height, gradient)


class ColorHueEditor(QMainWindow):
    """
    An application to visually edit GDAL color ramp files using HSV adjustments.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Color Ramp Editor")
        self.resize(1200, 800)

        # --- Data Storage ---
        self.source_color_table = []
        self.current_file_path = ""

        # --- Debounce Timer ---
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(150) # 150ms delay
        self.debounce_timer.timeout.connect(self._update_previews)

        # --- Main Layout ---
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # --- Left Panel: Color Table ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Elevation", "Original", "Adjusted"])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        left_layout.addWidget(self.table_widget)

        # --- Center Panel: Gradient ---
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.addWidget(QLabel("Adjusted Gradient Preview:"))
        self.gradient_widget = ColorGradientWidget()
        center_layout.addWidget(self.gradient_widget)

        # --- Right Panel: Controls ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.controls = {}
        control_specs = [
            ("saturation", "Saturation", 0.0, 3.0, 0.1, 1.0),
            ("shadow_adjust", "Shadow Adjust", -1.0, 1.0, 0.05, 0.0),
            ("mid_adjust", "Mid Adjust", -1.0, 1.0, 0.05, 0.0),
            ("highlight_adjust", "Highlight Adjust", -1.0, 1.0, 0.05, 0.0),
            ("min_hue", "Min Hue", 0, 360, 1, 0),
            ("max_hue", "Max Hue", 0, 360, 1, 0),
            ("target_hue", "Target Hue", 0, 360, 1, 0),
        ]

        for name, label, min_val, max_val, step, default in control_specs:
            right_layout.addWidget(QLabel(label))
            slider = QSlider(Qt.Orientation.Horizontal)
            spinner = QDoubleSpinBox()

            is_float = isinstance(min_val, float)
            multiplier = 100.0 if is_float else 1.0

            slider.setRange(int(min_val * multiplier), int(max_val * multiplier))
            spinner.setRange(min_val, max_val)
            spinner.setSingleStep(step)

            slider.setValue(int(default * multiplier))
            spinner.setValue(default)

            # Use functools.partial to connect signals with parameters
            slider.valueChanged.connect(
                partial(self._slider_to_spinner, spinner=spinner, multiplier=multiplier)
            )
            spinner.valueChanged.connect(
                partial(self._spinner_to_slider, slider=slider, multiplier=multiplier)
            )

            self.controls[name] = spinner

            control_layout = QHBoxLayout()
            control_layout.addWidget(slider)
            control_layout.addWidget(spinner)
            right_layout.addLayout(control_layout)

        # Buttons
        self.load_button = QPushButton("Load Color Ramp...")
        self.reset_button = QPushButton("Reset to Defaults")
        self.load_button.clicked.connect(self._load_color_ramp)
        self.reset_button.clicked.connect(self._reset_controls)

        right_layout.addStretch()
        right_layout.addWidget(self.reset_button)
        right_layout.addWidget(self.load_button)

        main_layout.addWidget(left_panel, 3) # Table takes 3/5ths width
        main_layout.addWidget(center_panel, 1) # Gradient takes 1/5th
        main_layout.addWidget(right_panel, 1) # Controls take 1/5th

    def _slider_to_spinner(self, value, spinner, multiplier):
        spinner.setValue(value / multiplier)
        self.debounce_timer.start()

    def _spinner_to_slider(self, value, slider, multiplier):
        slider.setValue(int(value * multiplier))
        self.debounce_timer.start()

    def _reset_controls(self):
        """Resets all control sliders and spinners to their default values."""
        defaults = {
            "saturation": 1.0, "shadow_adjust": 0.0, "mid_adjust": 0.0,
            "highlight_adjust": 0.0, "min_hue": 0, "max_hue": 0, "target_hue": 0,
        }
        for name, spinner in self.controls.items():
            spinner.setValue(defaults[name])
        # Manually trigger one final update
        self._update_previews()

    def _load_color_ramp(self):
        """Opens a file dialog and loads the selected color ramp file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open GDAL Color Ramp File", "", "Text Files (*.txt);;All Files (*)"
        )
        if not file_path:
            return

        try:
            self.source_color_table = read_color_file(file_path)
            self.current_file_path = file_path
            self.setWindowTitle(f"Color Ramp Editor - {os.path.basename(file_path)}")
            self._reset_controls() # Reset and do an initial population
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load or parse file:\n{e}")

    def _update_previews(self):
        """
        The display update function, called by the debounce timer.
        Recalculates colors and updates all UI widgets.
        """
        if not self.source_color_table:
            return

        # 1. Get current values from all controls
        params = {name: spinner.value() for name, spinner in self.controls.items()}

        # 2. Recalculate the color table
        adjusted_table = adjust_color_table(
            self.source_color_table,
            saturation_multiplier=params["saturation"],
            shadow_adjust=params["shadow_adjust"],
            mid_adjust=params["mid_adjust"],
            highlight_adjust=params["highlight_adjust"],
            min_hue=params["min_hue"],
            max_hue=params["max_hue"],
            target_hue=params["target_hue"],
        )

        # 3. Update the table widget
        self.table_widget.setRowCount(0) # Clear table
        for i, (has_data, data) in enumerate(self.source_color_table):
            if not has_data:
                continue

            self.table_widget.insertRow(self.table_widget.rowCount())

            # Original data
            elev, r_orig, g_orig, b_orig, _ = data
            # Adjusted data
            _, r_adj, g_adj, b_adj, _ = adjusted_table[i][1]

            # Populate cells
            self.table_widget.setItem(self.table_widget.rowCount() - 1, 0, QTableWidgetItem(str(elev)))

            orig_item = QTableWidgetItem()
            orig_item.setBackground(QColor(r_orig, g_orig, b_orig))
            self.table_widget.setItem(self.table_widget.rowCount() - 1, 1, orig_item)

            adj_item = QTableWidgetItem()
            adj_item.setBackground(QColor(r_adj, g_adj, b_adj))
            self.table_widget.setItem(self.table_widget.rowCount() - 1, 2, adj_item)

        self.table_widget.resizeColumnsToContents()

        # 4. Update the gradient widget
        self.gradient_widget.set_color_table(adjusted_table)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorHueEditor()
    window.show()
    sys.exit(app.exec())