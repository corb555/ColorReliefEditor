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
from typing import Dict, Type

from project_config import ProjectConfig, app_files_path, create_file_from_resource
from tab_page import TabPage

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


class TabbedEditor(QMainWindow):
    """
    Tabbed editor that provides a flexible tab-based UI.
    """

    def __init__(
            self, app, app_config_name: str, app_name: str, base_tabs: Dict[str, Type[TabPage]],
            extended_tabs: Dict[str, Type[TabPage]], make_process=None, project=None,
            project_config=None
    ) -> None:
        super().__init__()
        self.verbose = 0
        self.current_tab = None
        self.make_process = make_process
        self.project = project
        self.proj_config = project_config
        self.tabs = QTabWidget()

        # Load application settings from a YAML config file
        print("Load settings")
        self.app_config = YamlConfig(archive_data=True)
        app_path = self.load_app_config(app_config_name)
        self.verbose = int(self.app_config.get("VERBOSE", "4"))

        # Display  config path if verbose
        self.info(f"App config file: {app_path}")
        print("app config\n", self.app_config._data)

        # Set up UI styling
        self.font_size = int(self.app_config.get("FONT_SIZE", "12"))
        self.setup_style(app, self.font_size)

        # Determine tabs to load based on app settings
        tab_pages = {**base_tabs, **extended_tabs} if self.app_config.get(
            "MODE"
        ) == "expert" and self.app_config.get("SHOW_TABS") == "extended" else base_tabs

        # Initialize tabbed UI
        self._init_ui(tab_pages, app_name)

    def _init_ui(self, tab_pages: Dict[str, Type[TabPage]], app_name) -> None:
        """
        Initialize the tabbed UI.
        """
        self.setWindowTitle(app_name)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        tab_section = QVBoxLayout(central_widget)
        tab_section.setContentsMargins(15, 15, 15, 15)
        tab_section.setSpacing(0)
        tab_section.addWidget(self.tabs)

        for tab_name, tab_page in tab_pages.items():
            tab = tab_page(self, tab_name)
            self.tabs.addTab(tab, tab_name)

        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.current_tab = self.tabs.currentIndex()
        self.set_tabs_available(False, ["Project", "Settings"])

    def on_tab_changed(self, index):
        """Notify tabs of tab change."""
        if self.current_tab is not None:
            self.tabs.widget(self.current_tab).on_tab_exit()
        self.current_tab = index
        self.tabs.widget(self.current_tab).on_tab_enter()

    def load_app_config(self, name):
        """Load or create application configuration."""
        app_path = app_files_path(name)
        success = self.app_config.load(app_path)
        if not success:
            self.warn(f"Creating default config for {name}.")
            self.create_default_app_config(app_path)
            self.app_config.load(app_path)
        return app_path

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
            print(f"Setting default style. OS unknown: {platform.system()}")

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
                   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0078D7, 
                   stop:1 #005F9E);
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
            tab = self.tabs.widget(index)  # Retrieve the  tab widget
            self.debug(f"Loading {tab.tab_name} tab")
            success = tab.load(self.project)  # Attempt to load project data into the tab

            if not success:
                # Update project status if loading fails for a specific tab
                self.project.set_status(f"{tab.tab_name} File error")
                return False  # Stop loading further tabs if an error occurs

        return True  # All tabs loaded successfully

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

    def warn(self, message):
        """Print warning messages if verbose mode ."""
        if self.verbose > 2:
            print(f"Warning: {message}")

    def info(self, message):
        """Print info messages if verbose mode ."""
        if self.verbose > 3:
            print(f"Info: {message}")

    def debug(self, message):
        """Print debug messages if verbose mode ."""
        if self.verbose > 4:
            print(f"Debug: {message}")

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
