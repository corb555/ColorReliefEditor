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
from importlib.metadata import version, PackageNotFoundError
import platform
import sys
from typing import Dict, Type

from ColorReliefEditor.tab_page import TabPage

# Handle imports for PyQt6 versus PySide depending on which has been installed
try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, \
        QStyleFactory, QApplication
    from PySide6.QtGui import QColor
    from PySide6.QtCore import QEvent, QObject
except ImportError:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, \
        QStyleFactory, QApplication
    from PyQt6.QtGui import QColor
    from PyQt6.QtCore import QEvent, QObject

from YMLEditor.yaml_config import YamlConfig

from ColorReliefEditor.color_page import ColorPage
from ColorReliefEditor.elevation_page import ElevationPage
from ColorReliefEditor.hillshade_page import HillshadePage
from ColorReliefEditor.contour_page import ContourPage
from ColorReliefEditor.make_process import MakeProcess
from ColorReliefEditor.misc_page import MiscPage
from ColorReliefEditor.project_config import ProjectConfig, app_files_path, \
    create_file_from_resource
from ColorReliefEditor.project_page import ProjectPage
from ColorReliefEditor.relief_page import ReliefPage
from ColorReliefEditor.settings_page import AppSettingsPage


class ColorReliefEdit(QMainWindow):
    """
    Main window for the app. This uses Digital Elevation files and GDAL tools to create hillshade
    and color
    relief images which are combined into a final relief image.

    **Steps ColorReliefEditor uses for Generating Images:**

    1. The application provides a tabbed GUI to edit GDAL settings.
    2. These settings are saved in a YAML configuration file.
    3. When the user selects either the *Create* or *Preview*, the editor triggers a Make command with the corresponding target.
    4. The Makefile invokes `color_relief.sh` for the steps required to generate the selected image type.
    5. The `color_relief.sh` script reads the settings from the YAML file and runs the specified GDAL utilities to generate the requested image.

    Attributes:

    - make (QProcess or None): A QProcess object that handles GDAL makefile operations.
    - project (ProjectData): An instance of the ProjectData class, which handles the
      management of project data.
    - config (ConfigFile): An instance of the ConfigFile class, which manages configuration
      settings.
    - tabs (QTabWidget): A tab widget that contains the tabs for project
      settings, color ramps, and makefile operations.
    - current_tab (int): The index of the currently selected tab in the QTabWidget.
    - verbose (int): The verbosity level. 0=quiet, 1=error, 2=info.
    - app_config (YamlConfig): An instance of the AppConfig class.
    - font_size (int): The font size of the QApplication.

    **Methods**:
    """

    def __init__(self, app) -> None:
        super().__init__()
        self.verbose = 0
        self.current_tab = None
        self.tabs = QTabWidget()  # Tab for each feature

        # Load general application settings
        self.app_config = YamlConfig()
        app_path = self.load_app_config("relief_editor.cfg")
        self.verbose = int(self.app_config.get("VERBOSE")) or 0

        # Display version and config path if verbose > 0
        self.warn(f"ColorReliefEditor v{get_version('ColorReliefEditor')}")
        self.warn(f"App config file: {app_path}")  # Log path for config file

        # Set up stylesheet
        self.font_size = int(self.app_config.get("FONT_SIZE", "12"))
        self.setup_style(app, self.font_size)

        # Manage Makefile operations to build images
        self.make_process = MakeProcess(self.verbose, is_dark_mode())

        # Manage opening projects and paths to key project files
        self.project: ProjectConfig = ProjectConfig(self, verbose=self.verbose)

        # Manage project settings (Project_page will use this to load the projects)
        self.proj_config: YamlConfig = YamlConfig(verbose=self.verbose)

        # Base tabs/pages that are common to both basic and expert modes
        base_tabs: Dict[str, Type[TabPage]] = {
            "Project": ProjectPage, "Elevation Files": ElevationPage, "Hillshade": HillshadePage,
            "Color": ColorPage, "Create": ReliefPage,
        }

        # Extended tabs for expert mode if SHOW_TABS="extended"
        extended_tabs: Dict[str, Type[TabPage]] = {
            "Contour": ContourPage, "Misc": MiscPage, "Settings": AppSettingsPage,
        }

        # Use base tabs unless mode is expert and show_tabs is extended
        if self.app_config["MODE"] == "expert" and self.app_config["SHOW_TABS"] == "extended":
            tab_pages = {**base_tabs, **extended_tabs}
        else:
            tab_pages = base_tabs

        self._init_ui(tab_pages, app)

    def _init_ui(self, tab_pages: Dict[str, Type[TabPage]], app) -> None:
        """
        The UI is a tab control with a tab per feature
        """
        self.setWindowTitle("Color Relief")
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        tab_section = QVBoxLayout(central_widget)
        # Set margins around the tab section (left, top, right, bottom)
        tab_section.setContentsMargins(15, 15, 15, 15)
        tab_section.setSpacing(0)
        tab_section.addWidget(self.tabs)

        # Instantiate tabs
        for tab_name, tab_page in tab_pages.items():
            tab = tab_page(self, tab_name)
            self.tabs.addTab(tab, tab_name)

        # Note: when a project is loaded, all tabs will have load() called

        # Notify when user switches tabs
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.current_tab: int = self.tabs.currentIndex()  # Index of the current tab

        # Disable all tabs except Project until a project has been loaded
        self.set_tabs_available(False, ["Project", "Settings"])

    def setup_style(self, app, font_size):
        """
        Configure the application's style based on the operating system and theme.

        This method determines the application style (e.g., Fusion, macOS)
        and applies the appropriate stylesheet for the platform and adjusts colors based on the
        system's dark mode setting.

        Args:
            app (QApplication): The QT application instance.
            font_size (int): The default font size to be applied.

        Returns:
            None
        """
        if platform.system() == "Linux":
            # Use Fusion style for better cross-platform appearance on Linux
            style_name = "fusion"
            app.setStyle(style_name)
            background_color = "#3e3e3e" if is_dark_mode() else "#e5e5e5"
        elif platform.system() == "Darwin":
            # Use macOS native style
            style_name = "macos"
            app.setStyle(style_name)
            background_color = "#393939" if is_dark_mode() else "#e5e5e5"
        else:
            # Default style for other operating systems
            style_name = "default"
            background_color = None  # Default background color
            print(f"OS: {platform.system()}")

        # Get the text color based on the system theme
        text_color = self.tabs.palette().color(self.tabs.foregroundRole()).name()

        # Apply the custom stylesheet with the determined settings
        self.custom_stylesheet(app, font_size, style_name, background_color, text_color)

    def custom_stylesheet(self, app, font_size, style_name, background_color, text_color):
        """
        Apply a custom stylesheet to the application.

        This method defines styles for various widgets and adjusts their appearance
        based on the provided parameters such as font size, background color, and text color.

        Args:
            app (QApplication): The PyQt6 application instance.
            font_size (int): Default font size for the application.
            style_name (str): The name of the system style (e.g., 'fusion', 'macos').
            background_color (str): The background color for read-only widgets (in HEX format).
            text_color (str): The text color for editable and non-editable widgets (in HEX format).

        Returns:
            None
        """
        # Optional background color for read-only line edits
        line_edit_ro = f"background-color:{background_color};" if background_color else ""

        # Main application styles
        main_style = f"""
            QWidget {{
                font-size: {font_size}px; /* Default font size */
            }}
            QLineEdit:read-only {{
                {line_edit_ro}
                outline: none;
                border: none;
            }}
            QPlainTextEdit:read-only {{
                color: {text_color};
            }}
            QTextEdit {{
                border: none;
            }}
            QTableWidget {{
                outline: none;
                border: none;
                margin: 0px; /* Remove any margin inside the cells */
                padding: 0px; /* Remove any padding around cell content */
            }}
        """

        # Fusion dark mode-specific styles
        fusion_dark = """
            QWidget {
                color: #FFFFFF;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0078D7, stop:1 #005F9E);
                border-radius: 4px;
            }
            QTabBar::tab:disabled { /* Disabled tab */
                color: gray; /* Text color for disabled tab */
            }
        """

        # Combine and apply the styles
        if style_name == "fusion":
            # Append Fusion dark styles to the main style
            app.setStyleSheet(main_style + fusion_dark)
        else:
            # Apply the main style alone
            app.setStyleSheet(main_style)

    def save_settings(self):
        """
        Save App Settings and Project Settings
        """
        try:
            self.app_config.save()
            if self.proj_config.file_path is not None:
                self.proj_config.save()
        except Exception as e:
            self.warn(e)

    def create_default_app_config(self, app_path):
        """
        Create default config file for app settings if none exists.
        """
        self.warn("Creating default app config")
        self.app_config.file_path = app_path

        # Create the default app config file from resources
        create_file_from_resource(
            f"{ProjectConfig.file_suffix['app_config']}", app_path
        )

    def set_tabs_available(self, enable, always_enabled):
        """
        Enable or disable tabs based on enable flag. Tabs in "always_enabled"
        are always enabled.

        Args:
            enable (bool): Whether to enable or disable tabs.
            always_enabled (list): tabs that are always enabled.
        """
        for index in range(1, self.tabs.count()):
            if self.tabs.widget(index).tab_name in always_enabled:
                self.tabs.setTabEnabled(index, True)
            else:
                self.tabs.setTabEnabled(index, enable)

    def load_all_tabs(self):
        """
        Have each tab load data when a project is opened.
        If loading fails for any tab, update the project status, and halt further loading.

        Returns:
            bool: True if tabs are loaded successfully, False if any tab fails to load.
        """
        for index in range(self.tabs.count()):
            tab = self.tabs.widget(index)  # Retrieve the current tab widget
            success = tab.load(self.project)  # Attempt to load project data into the tab

            if not success:
                # Update project status if loading fails for a specific tab
                self.project.set_status(f"{tab.tab_name} File error")
                return False  # Stop loading further tabs if an error occurs

        return True  # All tabs loaded successfully

    def on_tab_changed(self, index):
        """
        Handle tab change events by notifying the old tab of exit and the new tab of enter.

        Args:
            index (int): The index of the newly selected tab.
        """
        self.tabs.widget(self.current_tab).on_tab_exit()
        self.current_tab = index
        self.tabs.widget(self.current_tab).on_tab_enter()

    def closeEvent(self, event) -> None:
        """
        Application close event - notify the current tab before the
        application exits.

        Args:
            event (QCloseEvent): The close event that triggers the application exit.
        """
        # Call on_tab_exit for the currently active tab
        self.tabs.widget(self.current_tab).on_tab_exit()
        super().closeEvent(event)

    def load_app_config(self, name):
        """
        Load the application settings. Create default configuration if it doesn't exist or fails to
        load.

        Args:
            name (str): The name of the application configuration file.

        Returns:
            str: The path to the application configuration file.
        """
        app_path = app_files_path(name)

        try:
            # Attempt to load the configuration
            success = self.app_config.load(app_path)
            if not success:
                # Handle unsuccessful load explicitly
                self.warn(f"App config load failed. {self.app_config._data['STATUS']}")
        except Exception as e:
            # Handle exceptions during load
            success = False
            self.warn(f"App config load error: {e}. ")

        if success:
            return app_path
        else:
            self.warn(f"Creating default config.")
            try:
                self.create_default_app_config(app_path)
                self.app_config.load(app_path)
            except Exception as e:
                # Handle exceptions during creation
                self.warn(f"Error creating default config: {e}. ")

    def warn(self, message):
        if self.verbose > 0:
            print(message)


def get_version(package_name: str) -> str:
    """
    Retrieves the version of the installed package.

    Args:
        package_name (str): Name of the installed package.

    Returns:
        str: Version string or an error message.
    """
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "Package not found or not installed."


def is_dark_mode() -> bool:
    """
    Determines whether the current application style is dark or light.

    This is achieved by analyzing the background and text colors of a common widget.
    If the text is brighter than the background, return True.

    Returns:
        bool: True if the style is considered dark, False otherwise.
    """
    # Create a temporary widget to sample colors
    temp_widget = QWidget()
    temp_widget.setStyleSheet("")  # Reset to default style

    # Get the background and text colors
    bg_color = temp_widget.palette().color(temp_widget.backgroundRole())
    text_color = temp_widget.palette().color(temp_widget.foregroundRole())

    def luminance(color: QColor) -> float:
        return (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255.0

    # Calculate brightness for both colors
    bg_brightness = luminance(bg_color)
    text_brightness = luminance(text_color)

    # If the background is darker than the text, consider it "dark mode"
    return bg_brightness < text_brightness


def _exec(obj):
    # PySide and PyQT handle exec differently
    if hasattr(obj, 'exec'):
        return obj.exec()
    else:
        return obj.exec_()


def main():
    """
    Entry point for the application. Initializes the QApplication and shows the main window.
    """
    app = QApplication(sys.argv)
    main_window = ColorReliefEdit(app)
    main_window.show()

    # Start QT App event loop
    sys.exit(_exec(app))


if __name__ == "__main__":
    main()
