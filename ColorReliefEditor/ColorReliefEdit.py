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
    relief images which are combined into a final relief image. All configurations, including
    colors and
    parameters, are set directly in the app. GDAL utilities are automatically executed to
    generate the color relief images.

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
    **Methods**:
    """

    def __init__(self, app) -> None:
        super().__init__()
        self.verbose = 0

        self.current_tab = None
        self.tabs = QTabWidget()  # Tab for each feature

        # Load general application settings
        self.app_config: YamlConfig = YamlConfig()  # Manage general application settings
        app_path = self.load_app_config("relief_editor.cfg")
        self.verbose = int(self.app_config.get("VERBOSE")) or 0

        self.warn(f"ColorReliefEditor v{get_version('ColorReliefEditor')}")
        self.warn(f"App config file: {app_path}")  # Log path for config file

        self.setup_style(app)

        # Manage Makefile operations to build images
        self.make_process = MakeProcess(self.verbose, is_dark_mode())

        # Manage opening projects and  paths to key project files
        self.project: ProjectConfig = ProjectConfig(self, verbose=self.verbose)

        # Manage project settings (Project tab will do the load)
        self.proj_config: YamlConfig = YamlConfig(verbose=self.verbose)

        # The tabs to launch for basic mode and expert mode
        if self.app_config["MODE"] == "basic":
            tab_classes = {
                "Project": ProjectPage, "Elevation Files": ElevationPage,
                "Hillshade": HillshadePage, "Color": ColorPage, "Create": ReliefPage,
            }
        else:
            if self.app_config["SHOW_TABS"] == "normal":
                # Expert Mode with SHOW_TABS="normal"
                tab_classes = {
                    "Project": ProjectPage, "Elevation Files": ElevationPage,
                    "Hillshade": HillshadePage, "Color": ColorPage, "Create": ReliefPage,
                }
            else:
                # Expert Mode with SHOW_TABS="extended" - Adds Misc and Settings Tab
                tab_classes = {
                    "Project": ProjectPage, "Elevation Files": ElevationPage,
                    "Hillshade": HillshadePage, "Color": ColorPage, "Create": ReliefPage,
                    "Contour": ContourPage, "Misc": MiscPage, "Settings": AppSettingsPage
                }

        self.init_ui(tab_classes, app)

    def setup_style(self, app):
        # Get preferred font size
        self.font_size = int(self.app_config.get("FONT_SIZE", "12"))

        # Set Application style
        if platform.system() == "Linux":
            style_name = "fusion"  # Use Fusion for Linux instead of default
            app.setStyle(style_name)
            if is_dark_mode():
                self.background_color = "#393939"
            else:
                self.background_color = "#e5e5e5"
        elif platform.system() == "Darwin":
            style_name = "MacOs"
            app.setStyle(style_name)
            if is_dark_mode():
                self.background_color = "#393939"
            else:
                self.background_color = "#e5e5e5"
        else:
            style_name = "default"
            print(f"OS: {platform.system()}")

        self.text_color = self.tabs.palette().color(self.tabs.foregroundRole()).name()
        self.custom_stylesheet(
            app, self.font_size, style_name, self.background_color, self.text_color
            )

    def init_ui(self, tab_classes, app) -> None:
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
        for tab_name, tab_class in tab_classes.items():
            tab = tab_class(self, tab_name)
            self.tabs.addTab(tab, tab_name)

        # Note: when a project is loaded, all tabs will have load() called

        # Notify when user changes tabs
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.current_tab: int = self.tabs.currentIndex()  # Index of the current tab

        # Disable all tabs except Project  until a project has been loaded
        self.set_tabs_available(False, ["Project", "Settings"])

    def save_settings(self):
        # Save App Settings and Project Settings
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

    def custom_stylesheet(self, app, font_size, style_name, background_color, text_color):
        # Set application Widget styles
        Zcolors = {
            "grid": "#323232", "highlight": "orange", "error": "Crimson", "normal": "Silver",
            "buttonBackground": "#323232", "background": "#4b4b4b", "readonly": "#3a3a3a",
            "lineedit": "#202020", "label": "white"
        }

        dark_style = f"""
                    QWidget {{
                        background-color: #353535;
                        color: #FFFFFF;
                    }}
                    QTabBar::tab:selected {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0078D7, 
                        stop:1 #005F9E);
                        border-radius: 4px;
                    }}
                    QTabBar::tab:disabled {{         /* Disabled tab */
                        color: gray;                 /* Text color for disabled tab */
                    }}
                    """

        min_style = f"""
                    QWidget {{
                        font-size: {font_size}px;  /* Default font size */
                    }}
                    QLineEdit:read-only {{
                        background-color:{background_color};
                        outline:none; 
                        border:none;
                    }}
                    QPlainTextEdit:read-only {{
                        color: {text_color};
                    }}
                    """
        """ 
        main_style = 
        
                    QWidget {{
                        font-size: {font_size}px;  /* Default font size */
                    }}
                    QLineEdit {{
                        background-color:{colors["lineedit"]}; 
                    }}
                    QTextEdit {{
                        background-color:{colors["lineedit"]}; 
                        border: none;
                    }}
                    QLineEdit:read-only {{
                        background-color:#f0f0f0;
                        outline:none; 
                        border:none;
                    }}
                    QLabel {{
                        color:{colors["label"]}; 
                    }}
                    QTextBrowser {{
                        background-color:{colors["grid"]}; 
                        border:none;
                    }}
                    QTableWidget::item {{
                        margin: 0px;  /* Remove margin inside the cells */
                        padding: 0px; /* Remove padding inside the cells */
                    }}
                    QTableWidget {{
                        gridline-color:{"red"};
                        background-color:{colors["grid"]};
                        outline:none; 
                        border:none;
                        margin: 0px;  /* Remove any margin inside the cells */
                        padding: 0px; /* Remove any padding around cell content */
                    }}
                    QHeaderView::section {{
                        background-color:{colors["grid"]};
                        padding:3px;
                    }}                  
                    QPlainTextEdit {{
                        background-color: {colors["background"]};
                    }}
                    QScrollBar::handle:vertical {{
                        background: white;
                        min-height: 15px;
                    }}
                    """

        if style_name == "fusion":
            # Add dark styles to main style
            min_style += dark_style

        print(min_style)
        app.setStyleSheet(min_style)


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

    This is achieved by analyzing the background and text colors of a common widget
    and applying a heuristic based on their brightness.

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
