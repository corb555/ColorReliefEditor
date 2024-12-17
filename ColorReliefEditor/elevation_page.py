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
from functools import partial
import os
import platform
import subprocess

from ColorReliefEditor.file_drop_widget import FileDropWidget
from ColorReliefEditor.instructions import get_instructions
from ColorReliefEditor.tab_page import TabPage, create_button, create_hbox_layout, \
    expanding_vertical_spacer
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMessageBox
from YMLEditor.settings_widget import SettingsWidget


class ElevationPage(TabPage):
    """
    Widget for editing Digital Elevation Model (DEM) settings in the application.

    This tab allows users to define and configure DEM layers, set files for
    each layer, and specify GDAL settings to merge DEM files. The tab also supports drag-and-drop
    for adding elevation files and provides buttons for DEM download sites.

    Attributes:
        main (MainClass): Reference to the main application instance.
        settings_widget (SettingsWidget): Widget for displaying and editing DEM settings based on
        the configuration.
        drop_widget (FileDropWidget): Widget for handling file drops for files with .tif extensions.
        tab_name (str): Name of the page.

    **Methods**:
    """

    def __init__(self, main, name):
        """
        Args:
            main (MainClass): Reference to the main application class.
            name (str): Name of the widget.
        """

        # Set up display format for the config settings that this tab uses
        formats = {
            "expert": {
                "NAMES": ("Layers", "read_only", None, 680), "LAYER": (
                    "Active Layer", "combo", ["A", 'B', 'C', "D", 'E', 'F', "G", 'H', 'I'], 204),
                "NAMES.@LAYER": ("Layer Name", "line_edit", r'^\w+$', 200),
                "FILES.@LAYER": ("Elevation Files", "text_edit", r"^([a-zA-Z0-9._*-]+)( [a-zA-Z0-9._*-]+)*$", 680),
                "SOURCES.@LAYER": ("Source", "line_edit", None, 680),
                "LICENSES.@LAYER": ("License", "line_edit", None, 680),
                "LABEL3": ("", "label", None, 400), "LABEL4": ("", "label", None, 400),
            }, "basic": {
                "FILES.@LAYER": ("Elevation Files", "text_edit", r"^([a-zA-Z0-9._-]+\.tif)( [a-zA-Z0-9._-]+\.tif)*$", 680),
                "LABEL3": ("", "label", None, 400), "LABEL4": ("", "label", None, 400),
            }
        }
        mode = main.app_config["MODE"]

        # Create widget to display and edit settings
        # Redisplay if LAYER changes

        self.settings_widget = SettingsWidget(
            main.proj_config, formats, mode, ["LAYER"], verbose=main.verbose
            )

        super().__init__(
            main, name, on_exit_callback=main.proj_config.save,
            on_enter_callback=self.settings_widget.display
        )

        # Setup buttons for download websites
        download_buttons = [("Download Elevation", 'DOWNLOAD.US'),
                            ("Download US High Res", 'DOWNLOAD.US_HIGH'), ]

        button_layout = self.create_download_buttons(download_buttons)

        # Styles for Drag and Drop box
        file_drop_style = f"""
             QLabel {{
                 font-size: {main.font_size + 2}px;
                 background-color: slategray;
                 padding: 40px;
             }}
            """
        status_style = """
             QLabel {
                 color: "orange";
             }
            """

        # Create drag and drop target for elevation files
        self.drop_widget = FileDropWidget(
            "Drag Elevation Files Here", r"^.*\.tif[i]?$", self.update_files_list, file_drop_style,
            status_style
        )

        # Instructions
        if self.main.app_config["INSTRUCTIONS"] == "show":
            instructions = get_instructions(self.tab_name, (mode == "basic"))
        else:
            instructions = None

        # Create the Page
        widgets = [self.drop_widget, button_layout, self.settings_widget,
                   expanding_vertical_spacer(4)]
        self.create_page(widgets, None, instructions, self.tab_name)

    def load(self, project):
        """
        Load settings for the selected project and update the display.

        Args:
            project (Project): The project instance to load settings from.

        Returns:
            bool: True if settings were loaded and displayed successfully.
        """
        super().load(project)

        # Get the paths for file drop target
        self.drop_widget.target_path = self.main.project.dem_directory

        # Update proxy file if WARP or FILES changes. This forces DEM rebuild
        self.main.proj_config.add_proxy(
            self.main.project.get_proxy_path(), ["WARP1", "WARP2", "WARP3", "WARP4", "FILES"]
        )

        self.validate()
        self.settings_widget.display()
        return True

    def on_tab_enter(self):
        """
        Refreshes and validates settings when the tab is entered
        """
        self.validate()
        self.drop_widget.set_status("")  # Clear drop status
        super().on_tab_enter()

    def update_files_list(self, source_file):
        """
        Adds a new DEM file to the list of elevation files maintaining unique
        entries.

        Args:
            source_file (str): The file path of the  file to add.
        """
        file_name = os.path.basename(source_file)
        if " " in file_name:
            QMessageBox.warning(
                self.main, "Note", f"File names cannot contain spaces. {file_name}"
            )
            return

        file_list = self.main.proj_config.get("FILES.@LAYER", "")

        # Add the new file to the file list and remove duplicates
        unique_files = set(file_list.split())  # Convert to set to prevent duplicates
        unique_files.add(file_name)  # Add new file name

        # Convert back into a string, set config entry, and redisplay
        self.main.proj_config.set("FILES.@LAYER", " ".join(sorted(unique_files)))
        self.settings_widget.display()

    def validate(self):
        """
        todo: Validate the elevation files specified exist
        Not implemented.
        Validates the elevation files specified in the configuration to ensure they exist.

        If any files are missing, updates the status label to notify the user.
        """
        pass

    def create_download_buttons(self, button_list):
        """
        Creates download buttons and connects each button to open its respective URL.

        Args:
            button_list (list of tuple): List of tuples where each tuple contains:
                - label (str): The button label.
                - config_key (str): The configuration key to retrieve the URL.

        Returns:
            QLayout: A layout containing all the created download buttons.
        """
        # Initialize an empty list to hold the created buttons
        buttons = []

        # Loop through the button_list to create buttons and set their connections
        for label, config_key in button_list:
            button = create_button(label)

            # Connect the button to open the URL dynamically using lookup with config_key
            button.clicked.connect(partial(self.open_url, config_key))

            buttons.append(button)

        # Create the layout with the buttons and return it
        return create_hbox_layout(buttons)

    def open_url(self, config_key):
        """
        Opens the URL from the configuration file in the default web browser.

        Args:
            config_key (str): Key in the application configuration that maps to a URL.

        Raises:
            Warning: Displays a warning message if the URL is empty, invalid, or cannot be opened.
        """

        # Fetch the URL from the app config using config_key
        url = self.main.app_config.get(config_key)

        # Check if URL is None or empty
        if not url:
            QMessageBox.warning(
                self.main, "File Not Found", f"Empty or invalid URL for: {config_key}"
                )
            print(f"Empty or invalid URL for: {config_key}")
            return

        # Trim whitespace from front and back of URL
        trimmed_url = url.strip()

        success = True
        if platform.system() == "Linux":
            try:
                # Use xdg-open to open item
                result = subprocess.run(
                    ["xdg-open", trimmed_url], check=True, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                success = result.returncode == 0

            except subprocess.CalledProcessError as e:
                success = False
                error_message = e.stderr.decode("utf-8")
                print(f"Error opening item with xdg-open: {error_message}")
        else:
            # Create a QUrl object
            qurl = QUrl(trimmed_url)

            # Try to open the URL
            try:
                success = QDesktopServices.openUrl(qurl)
            except Exception as e:
                success = False
                print(f"Error opening URL: {e}")

        if not success:
            QMessageBox.warning(self.main, "URL Error", f"Error opening website: {trimmed_url}")
            print(f"Error opening website: {trimmed_url}")
