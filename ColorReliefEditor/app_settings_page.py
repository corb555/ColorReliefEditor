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
from ColorReliefEditor.tab_page import TabPage, expanding_vertical_spacer
from PyQt6.QtWidgets import QStyleFactory
from YMLEditor.settings_widget import SettingsWidget


class AppSettingsPage(TabPage):
    """
    Widget for editing general application settings
    **Methods**:
    """

    def __init__(self, main, name):
        """
        Args:
            main (MainClass): Reference to the main application class.
            name (str): Name of the page.
        """
        styles = [style.lower() for style in QStyleFactory.keys()] + ["default"]

        # Set up display format for the app settings that this tab uses
        app_formats = {
            "expert": {
                "LABEL1": ("URLs:", "label", None, 400),
                "DOWNLOAD.US": ("Download", "line_edit", r'^(https?):\/\/.*\..+', 400),
                "DOWNLOAD.US_HIGH": ("US High Res", "line_edit", r'^(https?):\/\/.*\..+', 400),
                "LABEL2": ("", "label", None, 400),
                "VIEWER": ("Viewer", "combo", ['default', "QGIS", 'GIMP','Firefox',], 180),
                "LABEL3": ("", "label", None, 400),
                "MULTI": ("Multiprocessor", "combo", ["multi", 'single'], 180),
                "VERBOSE": ("Verbose", "combo", ["0", '1', '2'], 180),
                "STYLE": ("Style", "combo", styles, 400),
                "FONT_SIZE": ("Font Size", "line_edit", r"^\d{1,2}$", 90),
            },
            "basic": {
            }
        }

        # Create widget to display and edit settings
        mode = main.app_config["MODE"]
        self.app_settings_widget = SettingsWidget(
            main.app_config, app_formats, mode, verbose=main.verbose
            )

        # This tab uses app_config, not config for data
        super().__init__(
            main, name, on_exit_callback=main.app_config.save,
            on_enter_callback=self.app_settings_widget.display
        )

        # Instructions
        if self.main.app_config["INSTRUCTIONS"] == "show":
            instructions = get_instructions(self.tab_name, (mode == "basic"))
        else:
            instructions = None

        widgets = [self.app_settings_widget, expanding_vertical_spacer(10)]
        self.create_page(widgets, None, instructions, self.tab_name)
