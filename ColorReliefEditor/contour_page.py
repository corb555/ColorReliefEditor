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

from PyQt6.QtWidgets import QVBoxLayout
from YMLEditor.settings_widget import SettingsWidget

from ColorReliefEditor.instructions import get_instructions
from ColorReliefEditor.preview_widget import PreviewWidget
from ColorReliefEditor.tab_page import TabPage, expanding_vertical_spacer


class ContourPage(TabPage):
    """
    A widget for editing Contour settings and generating GDAL contour shapefiles.
    **Methods**:
    """

    def __init__(self, main, name):
        """
        Initialize

        Args:
            main (MainClass): Reference to the main application class.
            name (str): The name of the page.
        """
        # Set up display format for settings in basic mode and expert mode
        formats = {
            "expert": {
                "INTERVAL": ("Interval", "line_edit", r'^-i\s+\d+(\s+)?$', 180),
            }, "basic": {

            }
        }

        # Get basic or expert mode
        mode = main.app_config["MODE"]

        # Widget for editing config settings
        settings_layout = QVBoxLayout()
        # Set margins (left, top, right, bottom) to 0 and spacing between widgets to 5
        settings_layout.setContentsMargins(0, 0, 0, 0)  # No external margins
        settings_layout.setSpacing(5)  # Internal padding between widgets
        self.settings_widget = SettingsWidget(main.proj_config, formats, mode, verbose=main.verbose)

        settings_layout.addWidget(self.settings_widget)
        settings_layout.addItem(expanding_vertical_spacer(1))

        super().__init__(
            main, name, on_exit_callback=main.proj_config.save, on_enter_callback=self.display
        )

        # Widget for building and displaying a preview
        button_flags = ["make", "view", "publish"]
        self.preview = PreviewWidget(
            main, self.tab_name, self.settings_widget, False, main.proj_config.save, button_flags, )

        widgets = [settings_layout, self.preview]
        stretch = [1, 3]

        # Instructions
        if self.main.app_config["INSTRUCTIONS"] == "show":
            instructions = get_instructions(self.tab_name, (mode == "basic"))
        else:
            instructions = None

        # Create page with widgets vertically on left and instructions on right
        self.create_page(
            widgets, None, instructions, self.tab_name, vertical=False, stretch=stretch
        )

    def display(self):
        self.settings_widget.display()
        if self.preview:
            self.preview.display()

