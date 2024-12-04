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
#   With the LGPL license option, you can use the essential libraries and some add-on libraries of Qt.
#   See https://www.qt.io/licensing/open-source-lgpl-obligations for QT details.

#
#
import os

from PyQt6.QtCore import QObject, pyqtSignal, QProcess
from PyQt6.QtGui import QTextCursor


class MakeProcess(QObject):
    """
    Executes Makefile commands, streaming real-time output to an optional output window and
    emitting a `make_finished` signal upon completion. Supports dry-run mode to preview actions
    without execution and provides `build_required` to indicate if the dry-run determined that a
    build
    is required.

    Attributes:
        make_finished (pyqtSignal): Signal emitted when the make process finishes, with
            the job name and exit code.
        job_name (str): Name of the current job being processed.
        dry_run (bool): Specifies if the current process is a dry-run. Set to True if the
            make command ends with '-n'. Runs the process synchronously for analysis
            without actual execution.
        build_required (bool): Indicates whether a build is required based on the output
            of a dry-run. Set to True if any files or commands in the make process indicate
            a build is necessary, or if there is error output.

    **Methods**:
    """

    make_finished = pyqtSignal(str, int)

    def __init__(self):
        """
        Initialize the MakeProcess object.
        """
        super().__init__()
        self.dry_run = False
        self.build_required = False
        self.process = QProcess()
        self.job_name = ""
        self._output_window = None
        self.process.readyReadStandardOutput.connect(self._on_standard_output)
        self.process.readyReadStandardError.connect(self._on_standard_error)
        self.process.finished.connect(self._on_process_finished)

    def run_make(self, makefile_path, project_directory, command, job_name, output_window=None):
        """
        Execute the given Makefile command.
        Runs synchronously if '-n' is in the command (fast dry-run),
        otherwise runs the process asynchronously and emits the `make_finished` signal

        Args:
            makefile_path (str): The path to the Makefile file.
            command (str): The make command to execute.
            job_name (str): The name of the job for tracking purposes.
            output_window (QPlainTextEdit, optional): The window to display process output.
            project_directory (str): The path to the project directory.

        Returns:
            int: Exit code if running synchronously, 0 if running asynchronously.
        """
        self._output_window = output_window
        self.clear_output()
        self.job_name = job_name
        self.output(f"{command}\n")

        if not makefile_path or not os.path.isfile(makefile_path):
            self.return_error(103, f"Error: Makefile not found at: {makefile_path}")

        # chdir to the project directory
        try:
            os.chdir(project_directory)
        except OSError as e:
            self.return_error(104, f"Error: Unable to change directory to: {project_directory} {e}")

        # Start the make process
        self.build_required = False
        self.process.startCommand(command)

        # Check if this is a dry-run command
        if command.strip().endswith("-n"):
            # Run dry-run synchronously and scan output for ".sh" to determine if
            # build_required
            print(command)
            self.dry_run = True
            self.process.waitForFinished()
        else:
            # Run asynchronously and handle with signal
            self.dry_run = False

    def return_error(self, error, message):
        self.output(message)
        self.make_finished.emit(self.job_name, error)
        return error

    def clear_output(self):
        """
        Clear output window
        """
        if self._output_window:
            self._output_window.clear()

    def output(self, text):
        """
        Output the given text to the output window

        Args:
            text (str): The text to display in the output window.
        """
        if self._output_window:
            self._output_window.appendPlainText(text)

    def cancel(self):
        """
        Cancel the currently running make process.
        """
        self.process.kill()
        self.make_finished.emit(self.job_name, 2)

    def _on_standard_output(self):
        """
        Handle and display standard output from the make process.
        """
        output = self.process.readAllStandardOutput().data().decode()

        if self._output_window:
            self._output_window.moveCursor(QTextCursor.MoveOperation.End)
            self._output_window.insertPlainText(output)
            self._output_window.moveCursor(QTextCursor.MoveOperation.End)

        # During dry run check if output contains ".sh" (indicating work to be done)
        if self.dry_run and ".sh" in output:
            # If there are script names in the dry run output, a build is required
            self.build_required = True

    def _on_standard_error(self):
        """
        Handle and display standard error output from the make process.
        """
        self.build_required = True
        output = self.process.readAllStandardError().data().decode()
        self.output(output)

    def _on_process_finished(self, exit_code):
        """
        Handle the process finished event.

        Args:
            exit_code (int): The exit code of the completed process.
        """
        self.make_finished.emit(self.job_name, exit_code)
