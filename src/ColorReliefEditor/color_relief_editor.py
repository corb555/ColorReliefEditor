import os
import sys

from PyQt5.QtCore import pyqtSignal, Qt, QObject
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QFontMetrics
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTableWidget, QLineEdit,
                             QHBoxLayout, QColorDialog, QApplication, QLabel, QSizePolicy,
                             QFileDialog, QHeaderView)


class ColorReliefEditor(QWidget):
    """
    Editor for the color definitions used by the gdaldem color-relief utility. Read in the color
    ramp file, display the color for each elevation and allow you to edit each color and
    elevation.
    gdaldem generates a color relief map based on defining colors for each elevation

    See:  https://gdal.org/programs/gdaldem.html

    Args:
        sample_height (int): The height of the sample view panel.
        sample_width (int): The width of the sample view panel.
        initial_rows (int): The initial number of rows to display in the color edit widget.
    """

    def __init__(self, sample_height, sample_width, initial_rows):
        """
        Initialize the ColorReliefEditor.
        """
        super().__init__()

        # Read in file and put in ColorRamp
        self.color_ramp = ColorRamp()  # Reads, stores, and updates ColorRamp data
        self.filename = get_filename()
        if not self.filename:
            sys.exit(1)
        self.color_ramp.read(self.filename)

        # Create UI
        self.color_edit_widget, self.view_sample = None, None
        self.init_ui(sample_height, sample_width, initial_rows)

    def init_ui(self, sample_height, sample_width, initial_rows):
        """
        Initialize the user interface.

        The UI consists of the following panels:
        - ViewSample: A panel to display a sample of the colors.
        - ColorEditWidget: A panel to edit the colors and their elevations.
        - Save Button

        [main_layout - QVBox]
          [edit_pane - QHBox]
            [ViewSample]  [ColorEdit]
          [button_pane - QHBox]
            [save_button]
        """

        # Create the edit_pane with sample view, and ColorEditWidget
        edit_pane = QHBoxLayout()

        # Create SampleView on left - panel to display a sample of the color settings

        self.view_sample = ViewSample(self.color_ramp, sample_height, sample_width)
        edit_pane.addWidget(self.view_sample)  # Add the sample view on the left

        # Create ColorEditWidget on right - panel to edit elevation and colors
        self.color_edit_widget = ColorEditWidget(self.color_ramp, initial_rows)
        edit_pane.addWidget(self.color_edit_widget)  # Add  color edit widget on the  right

        # Create button pane with a Save button
        button_pane = QHBoxLayout()
        self.save_button = create_button('Save', self.on_save_button, self)
        self.save_button.setEnabled(False)  # Only enabled when data has been changed
        button_pane.addWidget(self.save_button)

        # Create main layout with edit_pane and button pane
        main_layout = QVBoxLayout()  # QVBoxLayout arranges widgets in a single column
        main_layout.addLayout(edit_pane)
        main_layout.addLayout(button_pane)
        self.setLayout(main_layout)  # Set the layout for this widget

        # Connect update methods so components update when the edit widget changes data
        self.color_edit_widget.data_updated.connect(self.on_data_updated)
        self.color_edit_widget.data_updated.connect(self.view_sample.update)

    def on_data_updated(self):
        """
        Enable the save button if changes have been made.
        """
        self.save_button.setEnabled(True)

    def on_save_button(self):
        """
        Save data and disable Save button
        """
        self.save_button.setEnabled(False)
        self.color_ramp.save(self.filename)


class ColorEditWidget(QWidget):
    """
    Widget for displaying and editing a table of color_ramp elevation levels and their
    corresponding colors.

    This widget allows users to view and modify both the elevation values and their associated
    colors (RGB or RGBA). Each row contains an elevation level and its color. Rows can be
    inserted and deleted.

    Emits data_updated when any data is edited
    """
    data_updated = pyqtSignal()  # Signal that data has been updated and needs redisplay

    def __init__(self, color_ramp, initial_rows):
        """
        Initialize the ColorEditWidget.

        Args:
            color_ramp (ColorRamp): An instance of the ColorRamp class containing color data.
        """
        super().__init__()
        self.color_ramp = color_ramp
        self.initial_rows = initial_rows
        self.color_table = None
        self.insert_button, self.delete_button = None, None
        self.font_metrics = QFontMetrics(self.font())
        self.row_height = self.font_metrics.height() + 10  # Calc row height with some padding
        self.init_ui()
        self.data_updated.connect(self.on_data_updated)

    def init_ui(self):
        """
        Initialize the user interface elements of the widget.

        The UI consists of:
        1. color_table to display and edit elevation and color information at the top.
        2. Instruction label to guide the user next.
        3. Insert and Delete buttons at the bottom.
        """
        # Create the color_table with a column for elevation and column for color
        self.color_table = QTableWidget(1, 2, self)
        self.color_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.color_table.horizontalHeader().hide()  # Hide the horizontal header
        self.color_table.verticalHeader().hide()  # Hide the vertical header
        self.color_table.setFixedHeight(self.row_height * self.initial_rows)  # Set 10 row height

        # Populate the color_table with color_ramp elevations and colors
        self.on_data_updated()

        # Create an instruction label
        instructions_label = QLabel("Click elev or color above to edit", self)

        # Create a button row for insert and delete buttons
        button_layout = QHBoxLayout()
        button_help = QLabel("Row ", self)
        button_layout.addWidget(button_help)
        self.insert_button = create_button('Insert', self.insert_row, self)
        button_layout.addWidget(self.insert_button)
        self.delete_button = create_button('Delete', self.delete_row, self)
        button_layout.addWidget(self.delete_button)

        # Set up the overall layout with these widgets vertically
        layout = QVBoxLayout()
        layout.addWidget(self.color_table, 0)  # Add the color table at the top
        layout.addWidget(instructions_label, 0)  # Add the instruction label next
        layout.addLayout(button_layout)  # Add the insert button row
        layout.addStretch(1)  # Add stretch to push all widgets to the top
        self.setLayout(layout)  # Set the layout

    def on_data_updated(self):
        """
        Populate the color_table with color_ramp elevation in column 0 and color in column 1.
        """
        self.color_table.setRowCount(len(self.color_ramp))
        for idx, (elevation, r, g, b, a) in enumerate(self.color_ramp):
            # Create an editable cell for elevation
            elevation_edit = QLineEdit(str(elevation))
            elevation_edit.setFixedHeight(
                self.row_height
            )  # Set fixed height for the cell
            elevation_edit.setFixedWidth(
                self.font_metrics.boundingRect(str("99999")).width()
            )  # Set fixed width for the cell
            elevation_edit.setAlignment(Qt.AlignBottom)  # Align text at the bottom
            elevation_edit.editingFinished.connect(
                lambda idx=idx: self.on_elevation_edited(idx)
            )  # Connect editing finished signal
            self.color_table.setCellWidget(
                idx, 0, elevation_edit
            )  # Add the elevation cell to the table column 0

            # Create a button for each color to open a color picker
            color_button = QPushButton(self)
            color_button.setFlat(True)  # Makes the button look like a plain rectangle
            color_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: rgba({r}, {g}, {b}, {a if a is not None else 255});
                    border: none;
                }}
                QPushButton:focus {{
                    border: 2px solid blue;
                }}
                """
            )

            color_button.setFixedSize(self.row_height * 2, self.row_height)
            color_button.clicked.connect(lambda _, idx=idx: self.open_color_picker(idx))
            self.color_table.setCellWidget(idx, 1, color_button)
            self.color_table.setRowHeight(idx, self.row_height)

            # Set column widths based on the widgets' sizes
            if self.color_table.rowCount() > 0:
                elevation_edit = self.color_table.cellWidget(0, 0)
                color_button = self.color_table.cellWidget(0, 1)
                if elevation_edit and color_button:
                    self.color_table.setColumnWidth(0, elevation_edit.width())
                    self.color_table.setColumnWidth(1, color_button.width())
                    # Set the fixed width of the table based on the sum of column widths
                    self.color_table.setFixedWidth(
                        elevation_edit.width() + color_button.width() + 5
                        )

    def on_elevation_edited(self, idx):
        """
        Handle the event when the elevation value is edited in the table.
        """
        elevation_edit = self.color_table.cellWidget(idx, 0)
        if elevation_edit:
            try:
                val = int(elevation_edit.text())
                self.color_ramp[idx][0] = val
            except ValueError:
                pass  # Handle invalid conversion to integer if needed
        self.data_updated.emit()  # Emit signal that data has updated

    def insert_row(self):
        """
        Insert a new row into the color_table.
        """
        current_row = self.color_table.currentRow()
        if current_row >= 0:
            current = self.color_ramp[current_row]

            # Current elev plus 1, white color, current alpha
            new_data = [current[0] + 1] + [255, 255, 255] + [current[4]]

            self.color_ramp.insert(current_row, new_data)
            self.color_table.setFixedHeight(self.row_height * len(self.color_ramp) + 5)
            self.data_updated.emit()

    def delete_row(self):
        """
        Delete the current row from the color_table.
        """
        current_row = self.color_table.currentRow()  # Get the currently selected row
        if current_row != -1:  # If a valid row is selected
            self.color_ramp.delete(current_row)  # Delete the row from the color_ramp data
            self.color_table.setFixedHeight(
                self.row_height * len(self.color_ramp) + 5
            )  # Adjust height
            self.data_updated.emit()

    def open_color_picker(self, idx):
        """
        Open the color picker dialog to choose a new color.

        Args:
            idx (int): The index of the color in the data list.
        """
        # Retrieve the QPushButton for the color at the given index
        color_button = self.color_table.cellWidget(idx, 1)

        # Extract RGB(A) values from the data
        r, g, b, a = self.color_ramp[idx][1:5]

        # Create a QColor object with the current color values
        current_color = QColor(r, g, b) if a is None else QColor(r, g, b, a)

        # Open the QColorDialog to select a new color
        dialog = QColorDialog(current_color)
        dialog.setOption(QColorDialog.ShowAlphaChannel, True)

        if dialog.exec_():
            new_color = dialog.currentColor()
            if new_color.isValid():
                # Update the color data with the new values
                r, g, b, a = (new_color.red(), new_color.green(), new_color.blue(),
                              new_color.alpha() if a is not None else None)
                self.color_ramp[idx][1:5] = [r, g, b, a]

                # Update the color button's style to reflect the new color
                color_style = """
                    QPushButton {background-color: %s; border: none;}
                    QPushButton:pressed {background-color: %s; border: none;}
                    QPushButton:released {background-color: %s; border: none;}
                """ % (new_color.name(), new_color.name(), new_color.name())
                color_button.setStyleSheet(color_style)
        self.data_updated.emit()  # Emit signal that data has updated


class ViewSample(QWidget):
    """
    Widget to display a sample of color bands with gradients between colors.
    Each band's height is scaled according to elevation values.
    """

    def __init__(self, color_ramp, height, width):
        """
        Initialize the ViewSample widget.

        Args:
            color_ramp (ColorRamp): An instance of the ColorRamp class containing color information.
        """
        super().__init__()
        self.color_ramp = color_ramp
        self.offset = None
        self.offset_data = None
        self.setMinimumSize(width, height)

    def scale_color_bands(self):
        """
        Calculate parameters for each color sample band.
        Each band is a scaled height filled with a gradient of the band's bottom color and top color.

        Returns:
            list: List of parameters for drawing each color band, including coordinates, dimensions,
                  and color information.
        """
        # Offset all elevations so they are positive
        min_y = min(self.color_ramp, key=lambda x: x[0])[0]
        self.offset = -min_y if min_y < 0 else 0     # Offset everything so it is positive
        self.offset_data = [(y + self.offset, r, g, b, a) for y, r, g, b, a in self.color_ramp]

        # Calculate scale factor to scale max elevation to window height
        max_y_value = float(max(self.offset_data, key=lambda x: x[0])[0])
        padding = max_y_value * 0.1
        scale_factor = 1 if max_y_value + padding == 0 else float(self.height()) / (
                    max_y_value + padding)

        previous_y = self.height()   # Start at top
        draw_parameters = []

        # Calculate draw parameters for each band - scaled x, y, w, h, bottom and top color
        sorted_data = sorted(self.offset_data, key=lambda x: x[0], reverse=True)
        for i, (y_value, r, g, b, a) in enumerate(sorted_data):
            scaled_y = int(y_value * scale_factor)
            band_height = max(1, previous_y - scaled_y)
            target_y = self.height() - (scaled_y + band_height)
            color = QColor(r, g, b, a) if a is not None else QColor(r, g, b)

            next_color = None
            if i + 1 < len(self.offset_data):
                next_r, next_g, next_b, next_a = self.offset_data[i + 1][1:5]
                next_color = QColor(
                    next_r, next_g, next_b, next_a
                    ) if next_a is not None else QColor(next_r, next_g, next_b)

            draw_parameters.append((0, target_y, self.width(), band_height, color, next_color))
            previous_y = scaled_y

        return draw_parameters

    def paintEvent(self, event):
        """
        Paint the color sample bands using the calculated draw parameters.

        Args:
            event (QPaintEvent): The paint event triggered by the system.
        """
        painter = QPainter(self)

        for x, y, w, h, color, next_color in self.scale_color_bands():
            if next_color:
                gradient = QLinearGradient(0, y, 0, y + h)
                gradient.setColorAt(0, color)
                gradient.setColorAt(1, next_color)
                painter.setBrush(gradient)
            else:
                painter.setBrush(color)

            painter.setPen(Qt.NoPen)
            painter.drawRect(x, y, w, h)

        painter.end()


class ColorRamp(QObject):
    """
    Class to read GDAL ColorRamp elevation and RGB(A) values from a file and support
    updates to the data and file save.
    """

    def __init__(self):
        """
        Initialize the ColorRamp instance.
        """
        super().__init__()
        self._data = []
        self.nv_line = None

    def read(self, filename):
        """
        Read elevation and RGB(A) values from the file and store them in "_data".
        Each line in the file contains: elevation, R, G, B, A (optional).
        Elevation can be "nv" indicating a special case for "no value".
        """

        def validate_rgba(values):
            """
            Validate that the RGBA values are within the acceptable range (0-255).

            Args:
                values (list): List of RGB(A) values.

            Raises:
                ValueError: If any of the RGB(A) values are out of the range 0-255.
            """
            for val in values[1:]:
                if not (0 <= val <= 255):
                    raise ValueError(f"RGBA values must be between 0 and 255. Found {val}.")

        try:
            with open(filename, 'r') as file:
                for line_number, line in enumerate(file, start=1):
                    tokens = line.strip().split()
                    try:
                        if tokens[0].lower() == "nv":  # Special case for "no value"
                            self.nv_line = line.strip()
                            continue

                        if len(tokens) not in (4, 5):
                            raise ValueError(
                                f"Incorrect number of values (expected 4 or 5, got {len(tokens)})"
                            )

                        elevation, r, g, b = map(int, tokens[0:4])
                        a = int(tokens[4]) if len(tokens) == 5 else None

                        validate_rgba([elevation, r, g, b, a])
                        self._data.append([elevation, r, g, b, a])

                    except (ValueError, IndexError) as e:
                        print(
                            f"ERROR in Color Ramp: line {line_number}: {str(e)} \n {line.strip()}"
                        )
                        sys.exit(1)

        except FileNotFoundError:
            raise FileNotFoundError(f"File {os.path.abspath(filename)} not found.")

    def save(self, filename):
        """
        Save the RGB(A) values to the file in GDAL format
        """
        with open(filename, 'w') as file:
            if self.nv_line:
                file.write(self.nv_line + '\n')
            for row in self._data:
                file.write(" ".join(map(str, [value for value in row if value is not None])) + '\n')

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, index):
        """
        Get an item from the data list by index.
        """
        return self._data[index]

    def __setitem__(self, index, value):
        """
        Set an item in the data list at the specified index.
        """
        self._data[index] = value

    def __len__(self):
        """
        Get the number of items in the data list.
        """
        return len(self._data)

    def insert(self, index, value):
        """
        Insert an item into the data list before the specified index.

        Args:
            index (int): The index before which the item should be inserted.
            value (list): The item to be inserted into the data list.
        """
        self._data.insert(index, value)

    def delete(self, index):
        """
        Delete an item from the data list at the specified index.

        Args:
            index (int): The index of the item to be deleted.
        """
        if 0 <= index < len(self._data):
            del self._data[index]


def create_button(text, callback, parent):
    """
    Create a QPushButton.

    Args:
        text (str): The text to display on the button.
        callback (callable): The function to call when the button is clicked.

    Returns:
        QPushButton: The created button.
    """
    button = QPushButton(text, parent)
    button.clicked.connect(callback)
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    return button

def get_filename():
    """
    Popup a file dialog to select a color ramp file.

    Returns:
        str: The selected file name or None if no file was selected.
    """
    file_dialog = QFileDialog()
    file_dialog.setNameFilter("Color Ramp Files (*.txt);;All Files (*)")
    file_dialog.setWindowTitle("Select Color Ramp File")
    file_dialog.setFileMode(QFileDialog.ExistingFile)
    file_dialog.setAcceptMode(QFileDialog.AcceptOpen)

    if file_dialog.exec_() == QFileDialog.Accepted:
        file_name = file_dialog.selectedFiles()[0]
        return file_name
    else:
        return None


def main():
    """
    Main function
    Display the ColorReliefEditor window to edit the file contents
    """
    app = QApplication(sys.argv)

    # Launch the main application window
    window = ColorReliefEditor(600,500, 10)
    window.setWindowTitle(f"Color Relief Editor")
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
