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
import importlib.resources as pkg_resources

from ColorReliefEditor import resources


def get_instructions(
        basename, hide_inst, hide_class='class="expert-section"',
        show_class='class="show-expert-section"'
):
    """
    Retrieve the instructions and update based on the user's mode (basic or expert).

    This function reads an HTML file with the specified `basename`
    and modifies the content to either hide or show the specified section. The HTML file is
    expected to use class="expert-section" for the expert section and have a style defined
    for that which hides the section.

    In "expert" mode, this function replaces `expert-section` with `show-expert-section`. In "basic"
    mode, it replaces `show-expert-section` with `expert-section`.

    Args:
        basename (str): The name of the topic whose instructions are to be retrieved.
        hide_inst (bool): True to hide the section, False to show the section.
        hide_class (str): The class to hide sections.
        show_class (str): The class to show sections.

    Returns:
        str: The instructions HTML content with the correct sections shown/hidden based on filter.

    Raises:
        FileNotFoundError: If the HTML file for the topic does not exist.
    """

    # Read the resource file corresponding to the given topic (basename)
    inst = _read_resource(f"{basename}.html")

    # Filter out parts of the instructions based on mode
    inst = filter_instructions(inst, hide_class, show_class, hide=hide_inst)

    return inst


def filter_instructions(content, hide_class, show_class, hide=False):
    """
    Toggle sections in HTML content by replacing class names to hide or show content.

    Args:
        content (str): The HTML content to modify.
        hide_class (str): The class name used to hide specific sections.
        show_class (str): The class name used to show specific sections.
        hide (bool): If True, hides the section by setting `show_class` to `hide_class`.
                     If False, shows the section by setting `hide_class` to `show_class`.

    Returns:
        str: The modified HTML content with the specified sections hidden or shown.
    """
    if hide:
        return content.replace(show_class, hide_class)
    else:
        return content.replace(hide_class, show_class)


def _read_resource(resource_name):
    """
    Read the content of a resource file.

    Args:
        resource_name (str): The name of the resource to read.

    Returns:
        str: The content of the resource file.

    Raises:
        FileNotFoundError: If the resource file cannot be found.
        OSError: If there is an issue opening the file.
    """
    try:
        with pkg_resources.open_text(resources, resource_name) as resource:
            return resource.read()
    except (FileNotFoundError, OSError) as e:
        print(f"Error: Unable to open the resource file '{resource_name}'. {e}")
        raise


def load_text_resource(file):
    """
    Load a text resource from the 'resources' module.

    Args:
        file (str): The filename of the resource.

    Returns:
        str: The content of the resource file.
    """
    with pkg_resources.open_text(resources, file) as f:
        return f.read()
