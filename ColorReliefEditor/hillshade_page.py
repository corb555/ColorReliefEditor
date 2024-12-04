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

from YMLEditor.settings_widget import SettingsWidget

from ColorReliefEditor.instructions import get_instructions
from ColorReliefEditor.preview_widget import PreviewWidget
from ColorReliefEditor.tab_page import TabPage, expanding_vertical_spacer


class HillshadePage(TabPage):
    """
    A widget for editing Hillshade settings and generating GDAL hillshade images.
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
                "NAMES.@LAYER": ("Layer", "read_only", None, 180),
                "HILLSHADE1": ("Shading", "combo", ["-igor", '-alg Horn', '-alg '
                                                                          'ZevenbergenThorne',
                                                    '-combined', '-multidirectional', " "], 180),
                "HILLSHADE2": ("Z Factor", "line_edit", r'^-z\s+\d+(\s+)?$', 180),
                "HILLSHADE3": ("Other", "line_edit", None, 180),
            }, "basic": {
                "HILLSHADE1": ("Shading", "combo", ["-igor", '-alg Horn', '-alg '
                                                                          'ZevenbergenThorne',
                                                    '-combined', '-multidirectional', " "], 180),
                "HILLSHADE2": ("Z Factor", "line_edit", None, 180),
            }
        }

        # Create page
        mode = main.app_config["MODE"]

        # Widget for editing config settings
        self.settings_widget = SettingsWidget(main.proj_config, formats, mode)

        super().__init__(
            main, name, on_exit_callback=main.proj_config.save,
            on_enter_callback=self.settings_widget.display
        )

        # Widget for building and displaying a preview
        button_flags = {"make"}
        self.preview = PreviewWidget(
            main, self.tab_name, self.settings_widget, True, main.proj_config.save, button_flags
        )

        widgets = [self.settings_widget, expanding_vertical_spacer(20), self.preview]

        # Instructions
        if self.main.app_config["INSTRUCTIONS"] == "show":
            instructions = get_instructions(self.tab_name, (mode == "basic"))
        else:
            instructions = None

        # Create page with widgets vertically on left and instructions on right
        self.create_page(widgets, None, instructions, self.tab_name)

    def load(self, project):
        """
        Load project and set preview target.
        """
        super().load(project)

        # Set preview target and full path
        layer = self.main.project.get_layer()
        self.preview.target = self.main.project.get_target_image_name(self.tab_name, True, layer)

        project_dir = Path(self.main.project.project_directory)
        self.preview.image_file = str(project_dir / self.preview.target)
        return True
