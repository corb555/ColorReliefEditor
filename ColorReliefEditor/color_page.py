#  Copyright (c) 2024.
#   Copyright (c) 2024. Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the “Software”), to deal in the
#   Software without restriction,
#   including without limitation the rights to use, copy, modify, merge, publish, distribute,
#   sublicense, and/or sell copies
#   of the Software, and to permit persons to whom the Software is furnished to do so, subject to
#   the following conditions:
#  #
#   The above copyright notice and this permission notice shall be included in all copies or
#   substantial portions of the Software.
#  #
#   THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#   BUT NOT LIMITED TO THE
#   WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
#   EVENT SHALL THE AUTHORS OR
#   COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
#   CONTRACT, TORT OR
#   OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#  #
#   This uses QT for some components which has the primary open-source license is the GNU Lesser
#   General Public License v. 3 (“LGPL”).
#   With the LGPL license option, you can use the essential libraries and some add-on libraries
#   of Qt.
#   See https://www.qt.io/licensing/open-source-lgpl-obligations for QT details.

#
#
from pathlib import Path
import os
from ColorReliefEditor.color_config import ColorConfig
from ColorReliefEditor.file_drop_widget import FileDropWidget
from ColorReliefEditor.instructions import get_instructions
from ColorReliefEditor.preview_widget import PreviewWidget
from ColorReliefEditor.tab_page import TabPage, create_button, expanding_vertical_spacer, \
    create_hbox_layout, create_vbox_layout
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QFontMetrics, QLinearGradient
from PyQt6.QtWidgets import (QWidget, QPushButton, QTableWidget, QLineEdit, QColorDialog,
                             QHeaderView, QMessageBox, QInputDialog, QSizePolicy, QScrollBar)


class ColorPage(TabPage):
    """
    Provides an editor for the color table used by gdaldem color-relief

    1) Provides editing for colors and elevations including rescale, insert, and delete rows.
    2) Displays an elevation scaled sample of the color gradients
    3) Provides a preview of gdaldem color-relief with current settings.
    **Methods**:
    """

    def __init__(self, main, name):
        """
        Args:
            main (ColorReliefEdit): The main application.
            name: The name of the page.
        """
        # Create data_mgr to load and save color table
        self.data_mgr = ColorConfig()

        # Create color settings widget to edit the color table settings
        self.color_settings_widget = ColorSettingsWidget(self.data_mgr)

        # Set up callbacks for tab entry and exit
        super().__init__(
            main, name, on_exit_callback=self.data_mgr.save,
            on_enter_callback=self.color_settings_widget.display
        )

        # Styles for Drag and Drop box
        file_drop_style = f"""
             QLabel {{
                 font-size: {main.font_size + 2}px;
                 background-color: slategray;
                 padding: 30px;
             }}
            """
        status_style = """
             QLabel {
                 color: "orange";
             }
            """

        # Create drag and drop target for elevation files
        self.drop_widget = FileDropWidget(
            "Drag GDAL Color File Here", r"^.*\.txt[i]?$", self.import_color_file, file_drop_style,
            status_style
        )

        # If expert mode, add drag and drop for Color File to display
        if main.app_config["MODE"] == 'expert':
            widgets = [self.color_settings_widget, self.drop_widget]
        else:
            widgets = [self.color_settings_widget]

        # Create the main layout with color_sample and settings_widget plus drop target in expert mode
        color_settings_pane = create_vbox_layout(widgets, 0, 0, 0, 0, 5)

        # Create a preview widget to run gdaldem color-relief and display result
        button_flags = ["make"]
        self.preview = PreviewWidget(
            main, self.tab_name, self.color_settings_widget, True, self.data_mgr.save,
            button_flags, )

        # Determine whether we're in basic or expert mode
        mode = self.main.app_config["MODE"]

        # Get Instructions for this tab and mode
        if self.main.app_config["INSTRUCTIONS"] == "show":
            instructions = get_instructions(self.tab_name, (mode == "basic"))
        else:
            instructions = None

        widgets = [color_settings_pane, self.preview]
        stretch = [1, 3]

        # Create the page
        self.create_page(
            widgets, None, instructions, self.tab_name, vertical=False, stretch=stretch, )

        # When color is updated, notify color_sample to redisplay
        self.color_settings_widget.colors_updated.connect(
            self.color_settings_widget.color_sample.update
        )

    def load(self, project):
        """
        Load the color ramp file and update the display with its contents.
        Called when a new project is loaded
        """
        super().load(project)

        # Set preview target and full path
        layer = self.main.project.get_layer()
        self.preview.target = self.main.project.get_target_image_name(self.tab_name, True, layer)
        project_dir = Path(self.main.project.project_directory)
        self.preview.image_file = str(project_dir / self.preview.target)
        self.drop_widget.target_path = self.main.project.project_directory

        try:
            res = self.data_mgr.load(self.main.project.color_file_path)
            return res
        except (FileNotFoundError, ValueError) as e:
            QMessageBox.warning(self, "Error", f"Color File error: {str(e)}")
            return False

    def import_color_file(self, dropped_file):
        """
        Import a color file to this project

        Args:
            dropped_file (str): The file path of the file to add.
        """
        dropped_filename = os.path.basename(dropped_file)
        if " " in dropped_filename:
            QMessageBox.warning(
                self.main, "Note", f"File names cannot contain spaces. {dropped_filename}"
            )
            return

        target_filename = os.path.basename(self.main.project.color_file_path)
        target_path = self.main.project.color_file_path

        # Display a dialog with this warning
        warning = f"Info: {target_filename} will be overwritten by {dropped_filename}."
        dialog = QMessageBox(self.main)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("Overwrite Confirmation")
        dialog.setText(warning)

        # Add custom buttons
        overwrite_button = dialog.addButton("Overwrite", QMessageBox.ButtonRole.AcceptRole)
        dialog.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

        # Show the dialog and get the result
        dialog.exec()

        # Check if user chose to overwrite the file
        if dialog.clickedButton() == overwrite_button:
            try:
                # Load the new color file
                success = self.data_mgr.load(dropped_file)
                if success:
                    # Rename dropped file to the target filename
                    os.rename(dropped_file, target_path)
                    self.drop_widget.set_status("Imported Color File")
                    touch_file(target_path)
                    self.display()
            except OSError as e:
                success = False
                QMessageBox.critical(
                    self.main, "Error", f"Unable to use the file: {e}"
                )

            if not success:
                self.drop_widget.set_status(self.data_mgr.error)
        else:
            print("Operation canceled by the user.")

def touch_file(filename):
    """
    Set the file's modification and access time to the current time.

    Args:
        filename (str): Path to the file.
    """
    with open(filename, 'a'):
        print(f"touch {filename}")
        os.utime(filename, None)

def scrollbar_width():
    """
    Calculate the width of the vertical scrollbar for the current style and environment.
    Returns:
        int: Width of the scrollbar in pixels.
    """
    dummy_scrollbar = QScrollBar()
    return dummy_scrollbar.sizeHint().width()


class ColorSettingsWidget(QWidget):
    """
    Widget for editing elevation levels and colors and
    synchronizing changes to data_mgr
    """
    colors_updated = pyqtSignal()

    def __init__(self, data_mgr):
        """
        Initialize

        Args:
            data_mgr(FileHandler): The color ramp to be edited.
        """
        super().__init__()
        # Timer to only save periodically
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)  # Ensure it only fires once per typing pause
        self.save_timer.timeout.connect(self.save)

        self.table_width = 200  # the  width for the table
        self.initial_rows = 15
        self.row_height, self.color_table = None, None
        self.insert_button, self.delete_button, self.rescale_button, self.layout = (
            None, None, None, None)
        self.data_mgr = data_mgr
        self.init_ui()

    def save(self):
        self.data_mgr.save()

    def init_ui(self):
        """
        Create the color table and add row manipulation buttons.
        """
        self.row_height = QFontMetrics(self.font()).height() + 6
        self.table_height = self.row_height * self.initial_rows
        self.color_width = self.row_height * 2

        # Create a widget to display a scaled sample with color gradients
        self.color_sample = ColorSampleWidget(self.data_mgr, self.table_height)

        # Initialize the color table widget with a column for elevation and a column for color
        # button
        self.color_table = QTableWidget(self.initial_rows, 2, self)

        # Set fixed height for the table
        self.color_table.setFixedHeight(self.table_height)
        self.color_table.setFixedWidth(
            self.elevation_width() + self.color_width + scrollbar_width() + 5
        )

        # Columns size
        self.color_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.color_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )

        # Disable grid lines
        self.color_table.setShowGrid(False)

        # Adjust cell spacing to zero
        self.color_table.setContentsMargins(0, 0, 0, 0)

        # Hide the headers
        self.color_table.horizontalHeader().hide()
        self.color_table.verticalHeader().hide()

        # Add buttons for insert row, delete row, rescale, undo
        self.insert_button = create_button("Insert", self.insert_row, False, self)
        self.delete_button = create_button("Delete", self.delete_row, False, self)
        self.undo_button = create_button("Undo", self.undo, False, self)
        self.rescale_button = create_button("Rescale", self.rescale, False, self)
        buttons = [self.insert_button, self.delete_button, self.undo_button, self.rescale_button]
        top_button_panel = create_hbox_layout(buttons, 0, 0, 0, 0)

        # Edit panel (horizontal) - Expander, Color_Sample, Color_Table
        self.edit_panel = create_hbox_layout([self.color_sample, self.color_table], spacing=0)

        # Main layout for ColorSettings widget
        widgets = [top_button_panel, self.edit_panel, expanding_vertical_spacer(5)]
        self.layout = create_vbox_layout(widgets)

        # Set the layout
        self.setLayout(self.layout)

    def display(self):
        """Populate the table with rows from the color data file."""
        if self.data_mgr and len(self.data_mgr) > 0:
            # Set the table row count to the number of data rows
            self.color_table.setRowCount(len(self.data_mgr))

            for row_idx, row in enumerate(self.data_mgr._data):
                # Unpack the row data into elevation and RGBA components
                elevation, r, g, b, a = row

                # Create a line edit widget for modifying the elevation value and
                # place it in the first column of the current row
                elevation_edit = self._create_line_edit(row_idx, elevation)
                self.color_table.setCellWidget(row_idx, 0, elevation_edit)

                # Create a color button displaying the color represented by the RGBA values
                # When clicked, it opens a color picker dialog for color modification
                color_button = self._create_color_button(row_idx, r, g, b, a)
                self.color_table.setCellWidget(row_idx, 1, color_button)
                self.color_table.setRowHeight(row_idx, self.row_height)

    def rescale(self):
        """
        Rescale the elevations for each row.
        The scale is calculated using the current max elevation vs new_max elevation and applying
        the scale to all rows.
        """
        # Open a dialog to get the new max elevation value from the user
        new_max, ok = QInputDialog.getInt(
            self, "Rescale Elevations", "Enter new maximum elevation:", min=0
        )

        if ok:
            # Save snapshot
            self.save()

            # Calculate the current max elevation of the table
            current_max: int = max([row[0] for row in self.data_mgr._data])

            # Calculate scale factor for the new max
            scale_factor = new_max / current_max if current_max else 1

            # Scale each elevation in the table
            for row_idx, row in enumerate(self.data_mgr._data):
                elevation = row[0]
                scaled_elevation = int(elevation * scale_factor)
                self.data_mgr.update_line(row_idx, elevation=scaled_elevation)

            # Refresh the display after rescaling
            self.display()
            self.colors_updated.emit()

    def _create_line_edit(self, row_idx, value):
        """Create a QLineEdit widget for the elevation."""
        elevation_edit = QLineEdit(str(value))
        elevation_edit.setFixedHeight(self.row_height)
        elevation_edit.setFixedWidth(self.elevation_width())
        elevation_edit.editingFinished.connect(lambda: self.on_elevation_update(row_idx))
        return elevation_edit

    def on_elevation_update(self, row_idx):
        """Update elevation data when UI changes and notify sample display."""
        line_edit = self.color_table.cellWidget(row_idx, 0)

        # Do saves periodically
        self.save_timer.start(500)  # 500 milliseconds debounce time

        if isinstance(line_edit, QLineEdit):
            try:
                # Attempt to parse elevation as an int or float based on content
                text = line_edit.text()
                new_elevation = int(text) if text.isdigit() else float(text)

                # Update data manager with the parsed elevation
                self.data_mgr.update_line(row_idx, elevation=new_elevation)

                # Reset the style to default if parsing is successful
                line_edit.setStyleSheet("")
            except ValueError:
                # Set cell background to Crimson if parsing fails
                line_edit.setStyleSheet("background-color: Crimson;")

        # Emit signal to indicate color data has been updated
        self.colors_updated.emit()

    def open_color_picker(self, idx):
        """Open color picker dialog and update data with result"""
        r, g, b, a = self.data_mgr[idx][1:5]
        current_color = QColor(r, g, b, a)
        dialog = QColorDialog(current_color)
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, True)
        if dialog.exec():
            new_color = dialog.currentColor()
            if new_color.isValid():
                self.on_color_update(idx, new_color)
        self.colors_updated.emit()

    def on_color_update(self, idx, new_color):
        # Save snapshot
        self.save()

        """Update the color button and data for the given index."""
        color_button = self.color_table.cellWidget(idx, 1)
        r, g, b, a = new_color.red(), new_color.green(), new_color.blue(), new_color.alpha()
        self.data_mgr.update_line(idx, colors=[r, g, b, a])
        color_button.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, {a}); border: none;")
        self.colors_updated.emit()

    def insert_row(self):
        # Save snapshot
        self.save()

        """Insert a new row by interpolating elevation and colors."""
        current_row_idx = self.color_table.currentRow()
        new_row = self.data_mgr.interpolate(current_row_idx)

        # Insert the new row into the data manager
        self.data_mgr.insert(current_row_idx, new_row)
        self.display()
        self.colors_updated.emit()

    def delete_row(self):
        # Save snapshot
        self.save()

        """Delete the current row from the color table."""
        current_row = self.color_table.currentRow()
        if current_row != -1:
            self.data_mgr.delete(current_row)
            self.display()
            self.colors_updated.emit()

    def undo(self):
        """Undo - revert back to previous color settings"""
        self.data_mgr.snapshot_undo()
        self.display()
        self.colors_updated.emit()

    def _create_color_button(self, row_idx, r, g, b, a):
        """
        Create a button for the color.
        Shows color and brings up color picker when clicked
        """
        color_button = QPushButton(self)
        color_button.setFlat(True)
        color_button.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, {a}); border: none;")
        color_button.setFixedSize(self.color_width, self.row_height)
        color_button.clicked.connect(lambda: self.open_color_picker(row_idx))
        return color_button

    def elevation_width(self):
        font_metrics = QFontMetrics(self.font())
        return font_metrics.horizontalAdvance("9999999") + 10


class ColorSampleWidget(QWidget):
    """
    Widget to display color bands with gradients between elevation levels.
    """

    def __init__(self, color_ramp, height):
        """
        Initialize

        Args:
            color_ramp: The color ramp to be displayed.
            height: The height of the widget.
        """
        super().__init__()
        self.color_ramp = color_ramp
        self.setMinimumSize(120, height)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )

    def scale_color_bands(self):
        """
        Scale each color band proportionally to its elevation range.

        This method calculates the parameters for rendering each color band,
        including its height and color gradient based on the elevation data. The result
        is used to create a visually accurate color gradient where each band represents a
        different elevation range.

        Returns:
            list[tuple]: A list of tuples, each containing:
                - color gradient (str): The color representation for the band.
                - target_y (float): The vertical position where the band should start.
                - band_height (float): The height of the band, indicating the elevation range it
                covers.
        """
        bands = []
        if len(self.color_ramp._data) == 0:
            print("color bands are empty")
            return bands

        # The highest elevation bands should be at the top of the sample display.
        min_y = min(self.color_ramp._data, key=lambda x: x[0])[0]
        max_y = max(self.color_ramp._data, key=lambda x: x[0])[0]

        # Offset to ensure non-negative values for target_y calculation
        offset = -min_y if min_y < 0 else 0
        height = self.height()

        # Calculate target_y with reversed elevation (higher elevations at smaller Y-values)
        target_y = [int(
            height - (elevation + offset) * height / (max_y + offset)
        ) for elevation, *_ in self.color_ramp._data]

        for i in range(len(target_y) - 1):
            y1, y2 = target_y[i], target_y[i + 1]
            c1 = QColor(*self.color_ramp._data[i][1:4])
            c2 = QColor(*self.color_ramp._data[i + 1][1:4])

            # Create a vertical gradient for each band
            gradient = QLinearGradient(0, y1, 0, y2)
            gradient.setColorAt(0, c1)
            gradient.setColorAt(1, c2)

            # Append the gradient, top Y coordinate, and height of the band
            bands.append((gradient, y1, y2 - y1))

        return bands

    def paintEvent(self, event):
        """
        Draw the color bands on the widget.

        Args:
            event: The paint event.
        """
        painter = QPainter(self)
        for gradient, y, height in self.scale_color_bands():
            painter.fillRect(0, y, self.width(), height, gradient)
