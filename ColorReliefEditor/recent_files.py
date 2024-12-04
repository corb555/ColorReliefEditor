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
import pickle

from YMLEditor.data_manager import DataManager


class RecentFiles(DataManager):
    """
    Manages a list of recently accessed files, extending `DataManager`.

    This class tracks and manages recent files in an application, storing the list in a pickle file.

    Attributes:
    - _data: List of recent file paths, with the most recent at the top.
    - file_path: Path to the recent files list.
    - unsaved_changes: Boolean indicating if changes need saving.
    - directory: Directory for the recent files.
    - max_items: Maximum number of recent files.

    Usage:
    Used in applications to track recent files, persisting them across sessions.

    Notes:
    - Re-initializes with an empty list if the file is corrupted/empty.
    - Limits the list to `max_items` entries (default=10)

    **Methods**:
    """

    def __init__(self, max_items=10):
        super().__init__()
        self._data = []  # Initialize the data as an empty list
        self.max_items = max_items

    def get_open_mode(self, write=False):
        """
        Return the appropriate file open mode based on the operation.
        """
        return 'wb' if write else 'rb'

    def _load_data(self, f):
        """
        Load recent files data (in pickle format).
        """
        try:
            return pickle.load(f)
        except EOFError:
            return []  # File is empty

    def _save_data(self, f, data):
        """
        Save data in pickle format for recent files.
        """
        pickle.dump(data, f)

    def insert(self, idx, item):
        """
        Insert item at the top of the list.
        """
        if item in self._data:
            self._data.remove(item)
        self._data.insert(0, item)
        self._data = self._data[:self.max_items]  # Keep only the last N entries
        self.unsaved_changes = True
        self.save()

    def add(self, file_name):
        """
        Public method to add a file name to the recent files list.
        """
        self.insert(0, file_name)
