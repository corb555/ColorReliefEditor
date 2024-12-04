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
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, \
    QSpacerItem, QSizePolicy
from YMLEditor.yaml_config import YamlConfig

from ColorReliefEditor.app_settings_page import AppSettingsPage
from ColorReliefEditor.color_page import ColorPage
from ColorReliefEditor.elevation_page import ElevationPage
from ColorReliefEditor.hillshade_page import HillshadePage
from ColorReliefEditor.make_process import MakeProcess
from ColorReliefEditor.misc_page import MiscPage
from ColorReliefEditor.project_config import ProjectConfig, app_files_path
from ColorReliefEditor.project_page import ProjectPage
from ColorReliefEditor.relief_page import ReliefPage


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
    **Methods**:
    """

    def __init__(self, app) -> None:
        super().__init__()

        # Manage opening projects and keeping paths to key project files
        self.project: ProjectConfig = ProjectConfig(self)
        self.make_process = MakeProcess()  # Manage Makefile operations to build images
        self.proj_config: YamlConfig = YamlConfig()  # Manage project settings (loaded by Project tab)
        self.app_config: YamlConfig = YamlConfig()  # Manage general application settings

        # Load general application settings
        app_path = self.load_app_config("relief_editor.cfg")
        print(f"App config file: {app_path}")

        # The tabs to create (name and routine)
        self.current_tab = None
        self.tabs = QTabWidget()  # Tab for each feature
        # The features to launch
        tab_classes = {
            "Project": ProjectPage, "Elevation Files": ElevationPage, "Hillshade": HillshadePage,
            "Color": ColorPage, "Relief": ReliefPage,"Misc": MiscPage ,"Settings": AppSettingsPage
        }

        self.init_ui(tab_classes, app)

    def init_ui(self, tab_classes, app) -> None:
        """
        The UI is a tab control with a tab per feature
        """
        set_style(app)
        self.setWindowTitle("Color Relief")
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.addSpacerItem(expanding_vertical_spacer(10))
        layout.addWidget(self.tabs)
        layout.addSpacerItem(expanding_vertical_spacer(10))

        # Instantiate tabs
        for tab_name, tab_class in tab_classes.items():
            tab = tab_class(self, tab_name)
            self.tabs.addTab(tab, tab_name)

        # Note: when a project is loaded, all tabs will have load() called

        # Notify on tab changes
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.current_tab: int = self.tabs.currentIndex()  # Index of the current tab

        # Disable all tabs except Project and Settings until a project has been loaded
        self.set_tabs_available(False, ["Project", "Settings"])

    def create_default_app_config(self, app_path):
        """
        Create default config file for app settings if none exists.
        """
        default_config = {
            "DOWNLOAD": {
                "US": "https://earthexplorer.usgs.gov/",
                "US_HIGH": "https://apps.nationalmap.gov/downloader/"
            },
            "MODE": "basic",
            "VIEWER": "QGIS",
        }
        self.app_config.file_path = app_path
        self.app_config.create(default_config)

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
        # Load the application settings
        app_path = app_files_path(name)
        try:
            self.app_config.load(app_path)
        except Exception as e:
            # Catch any error and create default configuration
            print(f"App config load error: {e}. Creating app default config.")
            self.create_default_app_config(app_path)
        return app_path


def expanding_vertical_spacer(height):
    """
    Create a spacer that expands vertically to help align UI components.

    Args:
        height (int): The minimum height for the spacer.

    Returns:
        QSpacerItem: A spacer that expands vertically
    """
    return QSpacerItem(0, height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)


def set_style(app):
    # Set application Widget styles
    colors = {
        "grid": "#323232", "highlight": "lightslategray", "error": "Crimson", "normal": "Silver",
        "buttonBackground": "#323232", "background": "#4b4b4b", "readonly": "#3a3a3a",
        "lineedit": "#202020", "label": "white"
    }

    app.setStyleSheet(
        f"""
                QLineEdit {{
                    background-color:{colors["lineedit"]}; 
                }}
                QTextEdit {{
                    background-color:{colors["lineedit"]}; 
                    border: none;
                }}
                QLineEdit:read-only {{
                    color:{colors["highlight"]}; 
                    background-color:{colors["readonly"]};
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
                QTableWidget {{
                    gridline-color:{colors["grid"]};
                    background-color:{colors["grid"]};
                    outline:none; 
                    border:none;
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
    )


def main():
    """
    Entry point for the application. Initializes the QApplication and shows the main window.
    """
    app = QApplication(sys.argv)
    main_window = ColorReliefEdit(app)
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
