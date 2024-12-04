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

import os
import re
import shutil

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class FileDropWidget(QWidget):
    def __init__(self, title, file_pattern, callback, style, status_style):
        """
        Create a widget that accepts file drag-and-drop, saves the file to target_path and
        calls callback to allow an app to do further processing.

        Args:
            title (str): The title for the widget.
            file_pattern (str): The file pattern to match against the file names.
            callback (function): A callback function that accepts a file name.
            style (str): A QWidget style.
        **Methods**:
        """
        super().__init__()
        self._target_path = None
        self.setAcceptDrops(True)
        self.file_pattern = re.compile(file_pattern)  # Compile the regex pattern
        self.callback = callback

        # Create drop target layout and label
        self.drop_label = QLabel(title, self)
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet(style)

        # Create status label
        self.status = QLabel("", self)
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if status_style:
            self.status.setStyleSheet(status_style)

        layout = QVBoxLayout()
        layout.addWidget(self.drop_label)
        layout.addWidget(self.status)
        self.setLayout(layout)

    @property
    def target_path(self):
        """Get the target path."""
        return self._target_path

    @target_path.setter
    def target_path(self, target_path):
        """Set the target path."""
        self._target_path = target_path

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Handle the drag event. Only accept it if the dragged item matches the regex pattern.

        Args:
            event (QDragEnterEvent): The event triggered when a file is dragged over the widget.
        """
        if event.mimeData().hasUrls():
            # Check if any file in the drop matches the regex pattern
            if any(self.file_pattern.match(url.toLocalFile()) for url in event.mimeData().urls()):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Triggered when one or more files are dropped onto the widget.
        Save each file to target and call callback.
        """
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path) and self.file_pattern.match(file_path):
                    self.update_file(file_path)
                else:
                    self.status.setText(f"Not a valid file: {os.path.basename(file_path)}")

        event.acceptProposedAction()

    def update_file(self, source_file):
        """
        Save the dropped file to the target path and call callback for app
        to handle the file

        Args:
            source_file (str): The path of the file being dragged.
        """
        # Extract the file name from the file path
        file_name = os.path.basename(source_file)
        destination = os.path.join(self._target_path, file_name)

        try:
            # Copy the file
            shutil.copy(source_file, destination)
            self.status.setText("")

            # Call the callback for app handling
            self.callback(source_file)
        except Exception as e:
            print(f"Failed to save file {file_name}: {e}")
            self.status.setText(f"Error saving {file_name}. {e}")

    def set_status(self, text):
        self.status.setText(text)