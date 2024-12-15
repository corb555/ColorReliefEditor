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

from ColorReliefEditor.instructions import get_instructions
from ColorReliefEditor.project_config import ProjectConfig
from ColorReliefEditor.tab_page import create_button, TabPage, expanding_vertical_spacer, \
    create_hbox_layout
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from YMLEditor.settings_widget import SettingsWidget


class ProjectPage(TabPage):
    """
    A widget for creating projects, opening projects, and displaying project status.

    Provides:
    - Buttons to create a new project, open an existing project, or access recent projects.
    - A summary of the project's status, showing either success or error details.

    **Methods**:
    """

    # Display formats for the Project settings
    project_formats = {
        "error": {
            "PROJECT": ("Project", "read_only", None, 600),
            "STATUS": ("Status", "read_only", r'^(?!.*\b(missing|error)\b).*', 600),
            "FOLDER": ("Folder", "read_only", r'^(?!.*\b(missing|error)\b).*', 600),
            "SETTINGS": ("Settings", "read_only", r'^(?!.*\b(missing|error)\b).*', 600),
            "COLORFILE": ("Color File", "read_only", r'^(?!.*\b(missing|error)\b).*', 600),
            "MAKEFILE": ("Makefile", "read_only", r'^(?!.*\b(missing|error)\b).*', 600),
            "SCRIPT": ("Script", "read_only", r'^(?!.*\b(missing|error)\b).*', 600),
            "MAKE": ("Make", "read_only", r'^(?!.*\b(missing|error)\b).*', 600),
        }, "success": {
            "PROJECT": ("Project", "read_only", None, 600),
            "STATUS": ("Status", "read_only", None, 600),
            "FOLDER": ("Folder", "read_only", None, 600),
        }
    }

    # Set up display format for the app settings that this tab uses
    app_formats = {
        "expert": {
            "LABEL1": (" ", "label", None, 180),
            "MODE": ("Mode", "combo", ["basic", "expert"], 180),
            "INSTRUCTIONS": ("Instructions", "combo", ["show", 'hide'], 180),
            "SHOW_TABS": ("Tabs", "combo", ["normal", 'extended'], 180),
        },

        "basic": {
            "LABEL1": (" ", "label", None, 180),
            "MODE": ("Mode", "combo", ["basic", "expert"], 180),
            "INSTRUCTIONS": ("Instructions", "combo", ["show", 'hide'], 180),
        }
    }

    def __init__(self, main, name):
        """
        Initialize

        Args:
            main (MainClass): Main application class reference.
            name (str): Name of the widget.
        """
        # Initialize the parent TabPage with the display callback
        super().__init__(
            main, name, on_exit_callback=main.save_settings, on_enter_callback=self.display_settings
        )

        # Buttons for creating, opening, and accessing recent projects
        self.new_button, self.recent_button, self.open_button = None, None, None
        self.status = ""

        mode = main.app_config["MODE"]

        # Configure project status display
        self.project_settings = SettingsWidget(
            main.project, self.project_formats, "success", verbose=main.verbose
        )

        # If these keys change, notify user that restart is required
        watch = ["MODE", "INSTRUCTIONS", "SHOW_TABS"]

        # Configure application settings display
        self.app_settings_widget = SettingsWidget(
            main.app_config, self.app_formats, mode, verbose=main.verbose, trigger_keys=watch, callback=self.restart_dialog
            )

        # Setup buttons for project actions
        self.open_button = create_button("Open", self.open_project_dialog, False, self)
        self.recent_button = create_button("Open Recent", self.open_recent_dialog, False, self)
        self.new_button = create_button("New", self.create_new_project, True, self)
        buttons = [self.open_button, self.recent_button, self.new_button, ]

        # Arrange buttons in a horizontal layout
        button_layout = create_hbox_layout(buttons, 0, 0, 0, 0, 5)

        # Instructions
        if self.main.app_config["INSTRUCTIONS"] == "show":
            instructions = get_instructions(self.tab_name, (mode == "basic"))
        else:
            instructions = None

        # Create the tab page with widgets, buttons, and optional instructions
        widgets = [button_layout, self.project_settings, self.app_settings_widget,
                   expanding_vertical_spacer(4), ]
        self.create_page(widgets, None, instructions, self.tab_name)
        self.app_settings_widget.display()

    def display_settings(self):
        self.project_settings.display()
        self.app_settings_widget.display()

    def load_project(self, config_path):
        """
        Load the project and update the layout.

        Args:
            config_path (str): Path to the project configuration file.
        """
        if config_path:
            success = self.main.project.load(config_path)

            # Attempt to load all tabs after project load
            if success:
                success = self.main.load_all_tabs()

            # Update the page layout based on the load success
            self.set_project_status(success)

    def restart_dialog(self, key, value):
        QMessageBox.information(
            self.main, "Note",
            f"You will need to restart for these changes to take effect."
        )

    def set_project_status(self, success):
        """
        Update the project display layout based on load success.

        Args:
            success (bool): True if the project loaded successfully; False otherwise.
        """
        if success:
            # Set project layout to "success"
            self.project_settings.set_layout("success")

            # Enable all tabs
            self.main.set_tabs_available(True, [])
        else:
            # Set project layout to "error"
            self.project_settings.set_layout("error")

            # Disable all tabs except Project Tab and Settings Tab
            self.main.set_tabs_available(False, ["Project"])

    def open_project_dialog(self):
        """Open a file dialog to select a project configuration file."""
        config_file_path = self.show_file_dialog(
            "open_file", "Open Project Config",
            f"Config Files (*{ProjectConfig.file_suffix['config']})"
        )
        self.status = "Project Opened"
        self.load_project(config_file_path)

    def open_recent_dialog(self):
        """Open a file dialog to select a recent project configuration file."""
        config_file_path = self.show_file_dialog("recent_file", "Open Recent Project")
        self.status = "Project Opened"
        self.load_project(config_file_path)

    def create_new_project(self):
        """
        Create a new project and open it.

        Displays a dialog to select a new folder, initializes the project, and loads it.
        """
        QMessageBox.information(
            self, "New Project", "Create a new folder in the next dialog and open it."
        )

        # Open a directory selection dialog
        directory = self.show_file_dialog("directory", "Select Folder for New Project")
        if directory:
            success, error_message = self.main.project.create_new_project(directory)

            if not success:
                QMessageBox.warning(self, "Error", error_message)
                return

            self.status = "Project Created"
            self.load_project(self.main.proj_config.file_path)

    def show_file_dialog(self, dialog_type, title, file_type_filter=""):
        """
        Display a file or directory selection dialog.

        Args:
            dialog_type (str): Type of dialog ("open_file", "recent_file", "directory").
            title (str): Title of the dialog.
            file_type_filter (str): Filter for file types (used only for file selection).

        Returns:
            str: The selected file or directory path, or None if cancelled.
        """
        if dialog_type == "open_file":
            return QFileDialog.getOpenFileName(self, title, "", file_type_filter)[0]
        elif dialog_type == "recent_file":
            recent_files = self.main.project.recent_files.items()
            if not recent_files:
                QMessageBox.warning(self, "Recent Files", "No recent files found.")
                return None
            return self.show_list_dialog(title, recent_files)
        elif dialog_type == "directory":
            return QFileDialog.getExistingDirectory(
                self, title, "", options=QFileDialog.Option.ShowDirsOnly
            )
        return None
