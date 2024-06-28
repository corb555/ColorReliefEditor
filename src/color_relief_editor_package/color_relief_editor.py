import os
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPainter, QColor, QLinearGradient
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTableWidget, QLineEdit,
                             QHBoxLayout, QColorDialog, QApplication, QLabel, QSizePolicy,
                             QFileDialog)


class ColorReliefEditor(QWidget):
    """
    Editor for the color definitions used by the gdaldem color-relief utility. This tool displays
    the color for each elevation
    and allows you to edit each color and elevation.  gdaldem generates a color relief map based
    on defining colors for each
    elevation based on a file with the following format:
    Each row has: elevation R G B [A]

    See:  https://gdal.org/programs/gdaldem.html
    """

    def __init__(self, filename):
        """
        Initialize the ColorReliefEditor.

        Args:
            filename (str): The path to the color file.

        Raises:
            FileNotFoundError: If the specified file is not found.
        """
        super().__init__()

        try:
            self.color_ramp = ColorRamp(filename)
            self.color_ramp.read()  # Read in the color definitions
        except FileNotFoundError as e:
            print(str(e))
            sys.exit(1)

        self.color_edit_widget, self.sample_view = None, None
        self.init_ui()

    def init_ui(self):
        """
        Initialize the user interface.

        The UI consists of the following panels:
        - ColorEditWidget: A panel to edit the colors and their elevations.
        - ViewSample: A panel to display a sample of the colors.
        """
        # Create ColorEditWidget - panel to edit colors
        self.color_edit_widget = ColorEditWidget(self.color_ramp)

        # Create SampleView widget - panel to display a sample of the colors
        self.sample_view = ViewSample(self.color_ramp)

        # Connect the update event of ColorPaneWidget to redraw the ViewSample
        self.color_edit_widget.data_updated.connect(self.sample_view.redraw)

        # Create the main display with sample view, and color pane
        main_pane = QHBoxLayout()  # QHBoxLayout arranges widgets in a single row, from left to
        # right.
        main_pane.addWidget(self.sample_view)  # Add the sample view to the main pane on the left
        main_pane.addWidget(
            self.color_edit_widget
            )  # Add the color edit widget to the main pane on the right
        self.setLayout(main_pane)  # Set the layout for this widget


class ColorRamp:
    """
    Class to read and save GDAL ColorRamp elevation and RGB(A) values from/to a file.
    The data is stored in the "data" array.
    Each line in the file contains: elevation, R, G, B, A (optional).
    Elevation can be "nv" indicating a special case for "no value".
    """

    def __init__(self, filename):
        """
        Initialize the ColorRamp instance.

        Args:
            filename (str): The path to the file containing elevation and RGB(A) values.
        """
        self.filename = filename
        self._data = []
        self.nv_line = None

    def read(self):
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
            with open(self.filename, 'r') as file:
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
            raise FileNotFoundError(f"File {os.path.abspath(self.filename)} not found.")

    def save(self):
        """
        Save the RGB(A) values to the file.
        """
        with open(self.filename, 'w') as file:
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


class ColorEditWidget(QWidget):
    """
    Widget to display and edit a list of elevations and their corresponding color.
    """
    # Class-level constants
    ROW_HEIGHT = 30
    PIXELS_PER_CHAR = 10  # Assuming a fixed value for PIXELS_PER_CHAR
    LABEL_WIDTH = 9 * PIXELS_PER_CHAR
    COLOR_FRAME_WIDTH = ROW_HEIGHT * 4

    data_updated = pyqtSignal()  # Signal emitted when the data has been updated.

    def __init__(self, color_ramp):
        """
        Initialize the ColorPaneWidget.

        Args:
            color_ramp (ColorRamp): An instance of the ColorRamp class containing color data.
        """
        super().__init__()
        self.color_ramp = color_ramp
        self.color_table = None
        self.save_button = None
        self.init_ui()
        self.set_data_changed(False)

    # noinspection PyUnboundLocalVariable
    def init_ui(self):
        """
        Initialize the user interface elements of the widget.

        The UI consists of:
        1. color_table to display and edit elevation and color information.
        2. Instruction label to guide the user.
        3. Save button to save changes.
        """
        # Create table with a column for elevation and column for color for each item in color_ramp
        self.color_table = QTableWidget(len(self.color_ramp), 2, self)
        self.color_table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeToContents
        )
        self.color_table.horizontalHeader().hide()  # Hide the horizontal header
        self.color_table.verticalHeader().hide()  # Hide the vertical header
        self.color_table.setFixedHeight(
            self.ROW_HEIGHT * len(self.color_ramp)
        )  # Set fixed height for the table

        # Populate the table with elevation in column 0 and color in column 1
        for idx, (elevation, r, g, b, a) in enumerate(self.color_ramp):
            # Create an editable cell for elevation
            elevation_edit = QLineEdit(str(elevation))
            elevation_edit.setFixedHeight(self.ROW_HEIGHT)  # Set fixed height for the cell
            elevation_edit.setFixedWidth(self.LABEL_WIDTH)  # Set fixed width for the cell
            elevation_edit.setAlignment(Qt.AlignBottom)  # Align text at the bottom
            elevation_edit.textEdited.connect(
                self.on_elevation_edited
            )  # Connect text edited signal
            self.color_table.setCellWidget(
                idx, 0, elevation_edit
            )  # Add the elevation cell to the table column 0

            # Create a button for each color to open a color picker
            color_button = QPushButton(self)
            color_button.setFlat(True)  # Makes the button look like a plain rectangle
            if a is not None:  # If alpha value is provided
                color_button.setStyleSheet(
                    "background-color: rgba({}, {}, {}, {}); border: none;".format(r, g, b, a)
                )
            else:
                color_button.setStyleSheet(
                    "background-color: rgb({}, {}, {}); border: none;".format(r, g, b)
                )
            color_button.setFixedSize(
                self.COLOR_FRAME_WIDTH, self.ROW_HEIGHT
            )  # Set fixed size for the color button
            color_button.clicked.connect(
                lambda _, idx=idx: self.open_color_picker(idx)
            )  # Connect click signal
            self.color_table.setCellWidget(
                idx, 1, color_button
            )  # Add the color button to the table column 1

            self.color_table.setRowHeight(idx, self.ROW_HEIGHT)  # Set fixed height for the row

        # Create an instruction label
        instructions_label = QLabel("Click on elevation or color above to edit", self)

        # Create a save button
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save)  # Connect click signal
        self.save_button.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )  # Set fixed size policy

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.color_table, 0)  # Add the color table to the layout at the top
        layout.addWidget(
            instructions_label, 0
        )  # Add the instruction label below the color table
        layout.addWidget(
            self.save_button, 0, Qt.AlignTop
        )  # Add the save button below the instruction label
        layout.addStretch(1)  # Add stretch to push all widgets to the top
        self.setLayout(layout)  # Set the layout for the widget

    def on_elevation_edited(self):
        """
        Handle the event when the elevation value is edited in the table.
        """
        sender = self.sender()
        if sender:
            idx = self.color_table.indexAt(sender.pos()).row()
            if 0 <= idx < len(self.color_ramp):
                try:
                    self.color_ramp[idx][0] = int(sender.text())
                except ValueError:
                    pass  # Handle invalid conversion to integer if needed
                self.set_data_changed(True)  # Mark that a change has been made

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
                self.set_data_changed(True)  # Mark that a change has been made

    def save(self):
        """
        Save the RGB values to the file and clear flag
        """
        self.color_ramp.save()
        self.set_data_changed(False)

    # noinspection PyUnresolvedReferences
    def set_data_changed(self, changed: bool):
        """
        Enable or disable the save button based on whether changes have been made.

        Args:
            changed (bool): True if changes have been made, False otherwise.
        """
        self.save_button.setEnabled(changed)
        if changed:
            self.data_updated.emit()


class ViewSample(QWidget):
    """
    Widget to display a sample of the colors.
    """

    def __init__(self, color_ramp):
        """
        Initialize the ViewSample widget.

        Args:
            color_ramp (ColorRamp): An instance of the ColorRamp class containing color information.
        """
        super().__init__()
        self.color_ramp = color_ramp
        self.offset = None
        self.offset_data = None
        self.setMinimumSize(220, 500)

    def scale_color_bands(self):
        """
        Calculate parameters for each color sample band.
        Each band is a scaled height filled with a gradient of the band's bottom color and top
        color.

        Returns:
            list: List of parameters for drawing each color band, including
                  coordinates, dimensions, and color information.
        """
        draw_parameters = []  # List to store parameters for drawRect

        # Determine the minimum y-value and offset to make all y-values positive.
        # Create offset_data list with all values offset
        min_y = min(self.color_ramp, key=lambda x: x[0])[0]
        self.offset = -min_y if min_y < 0 else 0
        self.offset_data = [(y + self.offset, r, g, b, a) for y, r, g, b, a in self.color_ramp]

        # Find the maximum y-value in offset_data to calculate scale factor
        max_y_value = float(max(self.offset_data, key=lambda x: x[0])[0])
        padding = max_y_value * 0.1  # Add space for the top band
        scale_factor = float(self.height()) / (max_y_value + padding)

        previous_y = self.height()  # Start from the top

        # Create list of parameters for each band: x, y, width, height, bot_color, top_color
        for i, data_row in enumerate(
                sorted(self.offset_data, key=lambda x: x[0], reverse=True)
        ):
            y_value, r, g, b, a = data_row
            scaled_y = int(y_value * scale_factor)
            band_height = max(1, previous_y - scaled_y)
            target_y = self.height() - (scaled_y + band_height)

            next_color = None
            if i + 1 < len(self.offset_data):
                next_r, next_g, next_b, next_a = self.offset_data[i + 1][1:5]
                next_color = QColor(
                    next_r, next_g, next_b, next_a
                ) if next_a is not None else QColor(next_r, next_g, next_b)

            color = QColor(r, g, b, a) if a is not None else QColor(r, g, b)

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

    def redraw(self):
        """
        Trigger a redraw of the color sample bands.
        """
        self.update()


def main():
    """
    Main function to launch the application.
    """
    app = QApplication(sys.argv)

    # Open a file dialog to select the color ramp file
    file_dialog = QFileDialog()
    file_dialog.setNameFilter("Color Ramp Files (*.txt);;All Files (*)")
    file_dialog.setWindowTitle("Select Color Ramp File")
    file_dialog.setFileMode(QFileDialog.ExistingFile)

    if file_dialog.exec_() == QFileDialog.Accepted:
        selected_file = file_dialog.selectedFiles()[0]
    else:
        sys.exit(0)

    # Launch the main application window
    window = ColorReliefEditor(selected_file)
    window.setWindowTitle(f"Color Relief Editor - {selected_file}")
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
