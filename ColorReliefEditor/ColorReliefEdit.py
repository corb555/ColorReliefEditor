import sys
import argparse

from YMLEditor.yaml_config import YamlConfig

from ColorReliefEditor.color_page import ColorPage
from ColorReliefEditor.contour_page import ContourPage
from ColorReliefEditor.layers_page import LayersPage
from ColorReliefEditor.hillshade_page import HillshadePage
from ColorReliefEditor.make_process import MakeProcess
from ColorReliefEditor.misc_page import MiscPage
from ColorReliefEditor.project_config import ProjectConfig
from ColorReliefEditor.project_page import ProjectPage
from ColorReliefEditor.merge_page import MergePage
from ColorReliefEditor.settings_page import AppSettingsPage
from ColorReliefEditor.slope_page import SlopePage
from ColorReliefEditor.tabbed_editor import TabbedEditor, is_dark_mode

# Handle imports for PyQt6 versus PySide depending on which has been installed
try:
    from PySide6.QtWidgets import QApplication
except ImportError:
    from PyQt6.QtWidgets import QApplication


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
    print("ColorReliefEdit")
    app = QApplication(sys.argv)

    parser = argparse.ArgumentParser(description="Start the application GUI.")
    parser.add_argument(
        "-v", "--verbose",
        type=int,
        default=3,
        help="Verbosity level (0 = silent, higher = more verbose output)"
    )

    args = parser.parse_args()
    verbose = args.verbose

    base_tabs = {
        "Project": ProjectPage, "Layers": LayersPage, "Hillshade": HillshadePage,
        "Color": ColorPage, "Merge": MergePage,
    }

    extended_tabs = {
        "Slope": SlopePage, "Contour": ContourPage, "GDAL": MiscPage, "Settings": AppSettingsPage,
    }

    # Map tab names to the associated filename for the tab
    tab_to_files = {
        "Hillshade": "hillshade", "Color": "color", "Merge": "relief",
    }

    # Initialize the project and makefile process
    make_process = MakeProcess(verbose, is_dark_mode())
    project: ProjectConfig = ProjectConfig(tab_to_files, verbose=verbose)
    proj_config: YamlConfig = YamlConfig(verbose, archive_data = True)

    main_window = TabbedEditor(
        app, "ColorReliefEditor", "ColorReliefEditor", base_tabs, extended_tabs, make_process,
        project, proj_config, )
    project.set_main(main_window)
    print("show main")
    main_window.show()

    # Start QT App event loop
    sys.exit(_exec(app))


if __name__ == "__main__":
    main()
