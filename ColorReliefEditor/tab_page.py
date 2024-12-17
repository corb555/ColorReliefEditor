#  Copyright (c) 2024.
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the “Software”), to deal in the
#   Software without restriction,
#   including without limitation the rights to use, copy, modify, merge, publish, distribute,
#   sublicense, and/or sell copies
#   of the Software, and to permit persons to whom the Software is furnished to do so, subject to
#   the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or
#   substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#   BUT NOT LIMITED TO THE
#   WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
#   EVENT SHALL THE AUTHORS OR
#   COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
#   CONTRACT, TORT OR
#   OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#
#   This uses QT for some components which has the primary open-source license is the GNU Lesser
#   General Public License v. 3 (“LGPL”).
#   With the LGPL license option, you can use the essential libraries and some add-on libraries
#   of Qt.
#   See https://www.qt.io/licensing/open-source-lgpl-obligations for QT details.
#
#
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QLabel, QPushButton, QWidget, QTextBrowser, QSizePolicy, QHBoxLayout,
                             QVBoxLayout, QPlainTextEdit, QTableWidget, QAbstractItemView, QDialog,
                             QListWidget, QDialogButtonBox, QSpacerItem)


def create_table(rows, columns, column_titles, editable=True):
    """
    Create a QTableWidget.

    Args:
        rows (int): Number of rows in the table.
        columns (int): Number of columns in the table.
        column_titles (list of str): Column header titles.
        editable (bool, optional): If False, makes the table read-only. Defaults to True.

    Returns:
        QTableWidget: The created table widget.

    **Methods**:
    """
    table_widget = QTableWidget(rows, columns)
    table_widget.verticalHeader().setVisible(False)
    table_widget.horizontalHeader().setVisible(False)
    table_widget.horizontalHeader().setStretchLastSection(True)
    table_widget.setSizePolicy(
        QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
    )

    if not editable:
        table_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    return table_widget


def expanding_vertical_spacer(height):
    # Create a spacer
    """
            Create a spacer that expands vertically to help align UI components.

            Args:
                height (int): The minimum height for the spacer.

            Returns:
                QSpacerItem: A spacer that expands vertically
            """
    return QSpacerItem(0, height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)


def expanding_horizontal_spacer(height):
    # Create a spacer
    """
            Create a spacer that expands vertically to help align UI components.

            Args:
                height (int): The minimum height for the spacer.

            Returns:
                QSpacerItem: A spacer that expands vertically
            """
    return QSpacerItem(0, height, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)


class TabPage(QWidget):
    """
    A base class for creating a tab page with a consistent layout of widgets, buttons,
    instructions, and title.
    Has optional callbacks for saving data on tab exit and updating the display.

    Attributes:
        tab_name (str): The name of the tab.
        on_exit_callback (callable, optional): Callback for saving data when the tab is exited.
        on_enter_callback (callable, optional): Callback for updating the display when the tab
        is entered.
    """

    def __init__(self, main, name, on_exit_callback=None, on_enter_callback=None):
        """
        Initialize the tab page widget.

        Args:
            main (QMainWindow): The main window instance.
            name (str): The name of the tab.
            on_exit_callback (callable, optional): Optional callback for saving data on tab exit.
            on_enter_callback (callable, optional): Optional callback for updating the display.
        """
        super().__init__()
        self.main = main
        self.tab_name = name
        self.on_exit_callback = on_exit_callback
        self.on_enter_callback = on_enter_callback
        self.right_layout, self.left_layout, self.page_layout = None, None, None

    def create_page(
            self, widgets, buttons, instructions=None, title=None, vertical=True, stretch=None
            ):
        """
        Set up a page layout with widgets, buttons, instructions, and a title.

        Args:
            widgets (list): List of widgets to add.
            buttons (QLayout): Layout for action buttons.
            instructions (str, optional): HTML instructions to display.
            title (str, optional): The title of the page.
            stretch (list, optional): A list of stretch values for each widget
        """
        # Validate stretch length
        if stretch is not None and len(stretch) != len(widgets):
            raise ValueError("The 'stretch' list must have the same length as the 'widgets' list.")

        # Create the page layout to hold the Widget panel and Instruction panel
        self.page_layout = QHBoxLayout()

        # Set margins around the page (left, top, right, bottom)
        self.page_layout.setContentsMargins(0, 5, 0, 0)
        self.page_layout.setSpacing(3)  # Internal padding between widgets

        # Create Left Panel - with Widgets and Buttons
        if widgets or buttons:
            widget_panel = QWidget(self)
            widget_panel_layout = QVBoxLayout(widget_panel) if vertical else QHBoxLayout(
                widget_panel
                )
            widget_panel.setLayout(widget_panel_layout)
            widget_panel_layout.setContentsMargins(0, 0, 0, 0)  # No external margins
            widget_panel_layout.setSpacing(5)  # Internal padding between widgets

            # Add widgets to the panel
            if widgets:
                for idx, widget in enumerate(widgets):
                    if isinstance(widget, QSpacerItem):
                        widget_panel_layout.addSpacerItem(widget)
                    elif isinstance(widget, (QHBoxLayout, QVBoxLayout)):
                        widget_panel_layout.addLayout(widget)
                    elif widget:
                        widget_panel_layout.addWidget(widget)

                    # Set corresponding stretch value from the stretch list
                    if stretch and idx < len(stretch):
                        widget_panel_layout.setStretch(idx, stretch[idx])

            # Add buttons to the panel
            if buttons:
                if isinstance(buttons, (QHBoxLayout, QVBoxLayout)):
                    widget_panel_layout.addLayout(buttons)
                elif buttons:
                    widget_panel_layout.addWidget(buttons)

            self.page_layout.addWidget(widget_panel)

        # Create Right Panel - with title and instructions
        if instructions:
            inst_panel = QWidget(self)
            inst_panel_layout = QVBoxLayout(inst_panel)
            inst_panel.setLayout(inst_panel_layout)

            # Add title and instructions to the panel
            if title:
                title_label = QLabel(f"<h1>{title}</h1>", self)
                title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                inst_panel_layout.addWidget(title_label)

            instructions_display = QTextBrowser(self)
            instructions_display.setHtml(instructions)
            instructions_display.setMinimumWidth(300)
            instructions_display.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            inst_panel_layout.addWidget(instructions_display)

            self.page_layout.addWidget(inst_panel)

            # Make the left panel take 3/4 of the space and the right panel take 1/4
            if widgets:
                self.page_layout.setStretch(0, 3)
                self.page_layout.setStretch(1, 1)

        # Create a container widget with a white border
        container_widget = QWidget(self)
        container_widget.setLayout(self.page_layout)
        # container_widget.setStyleSheet("QWidget { border: 2px solid white; }")

        # Set the bordered container as the layout's top-level widget
        top_layout = QVBoxLayout(self)
        top_layout.setContentsMargins(0, 0, 0, 0)  # No external margins
        top_layout.setSpacing(5)  # Internal padding between widgets
        top_layout.addWidget(container_widget)

    def load(self, project):
        """
        Load project data and update display

        Args:
            project (ProjectData): The project data.
        """
        self.display()
        return True

    def display(self):
        """Update the display using the callback if it exists."""
        if callable(self.on_enter_callback):
            self.on_enter_callback()

    def on_tab_enter(self):
        """Refresh the display when entering the tab."""
        self.display()

    def on_save(self):
        """Save the data using the callback if it exists."""
        if callable(self.on_exit_callback):
            self.on_exit_callback()

    def on_tab_exit(self):
        """Save data when exiting the tab."""
        self.on_save()

    def show_list_dialog(self, title, item_list):
        """
        Show a dialog with a list of items to select from.

        Args:
            title (str): The title of the dialog.
            item_list (list of str): The items to display.

        Returns:
            str: The selected item, or None if cancelled.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget(dialog)

        for idx, item in item_list:
            display_text = f"...{item[-40:]}" if len(item) > 40 else item
            list_widget.addItem(display_text)
            list_widget.item(list_widget.count() - 1).setData(256, item)

        layout.addWidget(list_widget)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog
        )
        layout.addWidget(button_box)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = list_widget.selectedItems()
            return selected_items[0].data(256) if selected_items else None

        return None


def create_readonly_window():
    """
    Create a read-only text window with a specified height and width, and set the background color.

    Args:
        height (int): The height of the text window.
        width (int): The width of the text window.

    Returns:
        QPlainTextEdit: A read-only plain text widget.
    """

    output_window = QPlainTextEdit()
    output_window.setReadOnly(True)

    # Set size policy for expansion
    output_window.setSizePolicy(
        QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
    )

    return output_window


def create_button(text, callback=None, focus=False, parent=None):
    """
    Create a QPushButton with an optional callback and focus setting.

    Args:
        text (str): The button label text.
        callback (callable, optional): The function to call on click. Defaults to None.
        focus (bool, optional): If True, the button will receive focus. Defaults to False.
        parent (QWidget, optional): The parent widget. Defaults to None.

    Returns:
        QPushButton: The created button.
    """
    button = QPushButton(text, parent)
    button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    button.setFocusPolicy(Qt.FocusPolicy.StrongFocus if focus else Qt.FocusPolicy.NoFocus)

    if callback:
        button.clicked.connect(callback)

    return button


def create_vbox_layout(
        widgets, margin_top=None, margin_bottom=None, margin_left=None, margin_right=None,
        spacing=None
):
    """
    Create a QVBoxLayout with optional margins and spacing and add supplied widgets to it.

    Args:
        widgets (list of QWidget): The widgets to add to the layout.
        margin_top (int, optional): Top margin in pixels. Defaults to None.
        margin_bottom (int, optional): Bottom margin in pixels. Defaults to None.
        margin_left (int, optional): Left margin in pixels. Defaults to None.
        margin_right (int, optional): Right margin in pixels. Defaults to None.
        spacing (int, optional): Spacing between items in pixels. Defaults to None (Qt's default).

    Returns:
        QVBoxLayout: Configured QVBoxLayout instance.
        :param widgets:
    """
    return _create_layout(
        QVBoxLayout, widgets, margin_top, margin_bottom, margin_left, margin_right, spacing
    )


def create_hbox_layout(
        widgets, margin_top=None, margin_bottom=None, margin_left=None, margin_right=None,
        spacing=None
):
    """
    Create a QHBoxLayout with optional margins and spacing and add supplied widgets to it.

    Args:
        margin_top (int, optional): Top margin in pixels. Defaults to None.
        margin_bottom (int, optional): Bottom margin in pixels. Defaults to None.
        margin_left (int, optional): Left margin in pixels. Defaults to None.
        margin_right (int, optional): Right margin in pixels. Defaults to None.
        spacing (int, optional): Spacing between items in pixels. Defaults to None (Qt's default).

    Returns:
        QHBoxLayout: Configured QHBoxLayout instance.
    """
    return _create_layout(
        QHBoxLayout, widgets, margin_top, margin_bottom, margin_left, margin_right, spacing
    )


def _create_layout(
        layout_class, widgets, margin_top=None, margin_bottom=None, margin_left=None,
        margin_right=None, spacing=None
):
    """
    Helper function to create a layout with optional margins and spacing. Add widgets to it.

    Args:
        layout_class (type): The layout class to instantiate (e.g., QVBoxLayout or QHBoxLayout).
        widgets (list): List of widgets, spacers, or other items to add to the layout.
        margin_top (int, optional): Top margin in pixels. Defaults to None.
        margin_bottom (int, optional): Bottom margin in pixels. Defaults to None.
        margin_left (int, optional): Left margin in pixels. Defaults to None.
        margin_right (int, optional): Right margin in pixels. Defaults to None.
        spacing (int, optional): Spacing between items in pixels. Defaults to None (Qt's default).

    Returns:
        QLayout: An instance of the specified layout class with configured margins and spacing.
    """
    layout = layout_class()

    # Set margins if all values are provided
    if None not in (margin_top, margin_bottom, margin_left, margin_right):
        layout.setContentsMargins(margin_left, margin_top, margin_right, margin_bottom)

    # Set spacing if provided
    if spacing is not None:
        layout.setSpacing(spacing)

    # Add items to the layout
    for item in widgets:
        if item == 'stretch':
            layout.addStretch()
        elif isinstance(item, QWidget):
            layout.addWidget(item)
        elif isinstance(item, QSpacerItem):
            layout.addSpacerItem(item)
        elif isinstance(item, (QVBoxLayout, QHBoxLayout)):
            layout.addLayout(item)
        else:
            raise TypeError(
                f"Unsupported item type: {type(item)}. Only QWidget, QSpacerItem, "
                f"QLayoutItem, or 'stretch' are allowed."
            )

    return layout

