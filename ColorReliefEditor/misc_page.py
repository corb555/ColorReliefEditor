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
from YMLEditor.settings_widget import SettingsWidget


class MiscPage(TabPage):
    """
    A widget for editing miscellaneous settings.
    **Methods**:
    """

    def __init__(self, main, name):
        """
        Initialize

        Args:
            main (MainClass): Reference to the main application class.
            name (str): The name of the page.
        """
        # Set up display formats for the settings that this tab uses in basic and expert mode
        formats = {
            "expert": {
                "LABEL4": ("", "label", None, 400), "LABEL3": ("gdal_warp:   ", "label", None, 400),
                "WARP1": ("CRS", "line_edit", r'^\s*-t_srs\s+\S+$', 200),
                "WARP2": ("gdalwarp", "line_edit", r"(?:-(?:\w+(?:\s+\w+=[\w/]+)?)\s*)+", 500),
                "WARP4": ("Performance", "line_edit", None, 500),
                "WARP3": ("Resampling", "combo",
                                                                            ["-r bilinear",
                                                                             '-r cubic',
                                                                             '-r cubicspline',
                                                                             '-r lanczos', " "],
                                                                            200),
                "LABEL5": ("", "label", None, 400),
                "LABEL2": ("gdaldem:   ", "label", None, 400),
                "EDGE": ("Edges", "combo", ["-compute_edges", " "], 180),
                "OUTPUT_TYPE": ("Output Type", "line_edit", r'^\s*-of\s+\S+$', 200),
                "COLOR1": ("Nearest Color", "line_edit", None, 200),
                "LABEL6": ("", "label", None, 400),
                "LABEL1": ("gdal_calc:   ", "label", None, 400),
                "MERGE1": ("gdal_calc", "line_edit", r"^(--[a-zA-Z0-9]+(=["
                                                     r"a-zA-Z0-9]+)?)(\s+--["
                                                     r"a-zA-Z0-9]+(=["
                                                     r"a-zA-Z0-9]+)?)*$", 500),
                "COMPRESS": ("Compress", "line_edit", r'^-co COMPRESS=.*', 500),
            }, "basic": {
            }
        }

        # Create page
        mode = main.app_config["MODE"]

        # Widget for editing config settings
        self.settings_widget = SettingsWidget(main.proj_config, formats, mode, verbose=main.verbose)

        super().__init__(
            main, name, on_exit_callback=main.proj_config.save,
            on_enter_callback=self.settings_widget.display
        )

        widgets = [self.settings_widget, expanding_vertical_spacer(4)]

        # Instructions
        if self.main.app_config["INSTRUCTIONS"] == "show":
            instructions = get_instructions(self.tab_name, (mode == "basic"))
        else:
            instructions = None

        # Create page with widgets vertically on left and instructions on right
        self.create_page(widgets, None, instructions, self.tab_name)
