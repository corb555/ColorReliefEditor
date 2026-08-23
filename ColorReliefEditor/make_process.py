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
import os
import platform
import re
import shutil

# Handle imports for PyQt6 versus PySide depending on which has been installed
try:
    from PySide6.QtCore import QObject, Signal, QProcess
    from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor
except ImportError:
    from PyQt6.QtCore import QObject, pyqtSignal as Signal, QProcess
    from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor

# ANSI color mapping
ANSI_COLOR_MAP = {
    '30': 'black', '31': 'red', '32': 'green', '33': 'yellow', '34': 'blue', '35': 'magenta',
    '36': 'cyan', '37': 'white',
}
ANSI_ESCAPE = re.compile(r'\x1b\[([0-9;]*)m')


# Error codes
ERROR_COMMAND_NOT_FOUND = -102
ERROR_MAKEFILE_MISSING = -103
ERROR_CWD_FAILURE = -104
ERROR_START_FAILURE = -105

class Job:
    """
    Represents an individual job with associated metadata.

    Attributes:
        job_id (int): Unique identifier for the job.
        dry_run (bool): Whether the job is a dry-run.
        build_required (bool): Whether a build is required.
        process (QProcess): The running QProcess instance, if any.
    """

    def __init__(self, job_id):
        self.job_id = job_id
        self.dry_run = False
        self.build_required = False
        self.process = None
        self.user_data = None


class MakeProcess(QObject):
    """
    Executes Makefile commands via QProcess
    Streaming real-time output to an optional output window
    Emits a `make_finished` signal upon completion.
    Supports dry-run mode and provides build_required per job.
    """

    make_finished = Signal(int, int)  # Emits job_id and exit code

    def __init__(self, verbose=3, dark_mode=True):
        super().__init__()
        self.dark_mode = dark_mode
        self.verbose = verbose
        self._output_window = None
        self.jobs = {}
        self.last_job_id = 0

        system = platform.system()
        #self.make = "gmake" if system == "Darwin" else "make"
        self.make = "make"

    def run_make(self, makefile_path, project_directory, command, output_window=None, user_data=None):
        """
        Runs a Make command using the provided makefile and project directory. It handles both synchronous
        and asynchronous execution of the make command, including dry-runs and actual builds. Processes
        are managed internally, ensuring proper error handling and output redirection.

        Args:
            makefile_path: str
                The path to the Makefile that will be executed.
            project_directory: str
                The directory in which the Makefile is located and where the command should execute.
            command: str
                The Make command to be executed, including any options or arguments.
            output_window: Optional[Any]
                An optional output window where the process logs and errors will be redirected.
                If not provided, the default output mechanism will be used.

        Returns:
            int: The job ID of the initiated Make process or a negative number if an error occurs.

        """
        self.last_job_id += 1
        job = Job(self.last_job_id)
        job.user_data = user_data
        self.jobs[job.job_id] = job
        self._output_window = output_window
        self.clear_output()
        self.output(f"{command}\n")

        if shutil.which(command.split()[0]) is None:
            return self.return_error(job.job_id, ERROR_COMMAND_NOT_FOUND,
                                     f"ERROR: Command not found: {command.split()[0]}")

        if not makefile_path or not os.path.isfile(makefile_path):
            return self.return_error(job.job_id, ERROR_MAKEFILE_MISSING,
                                     f"ERROR: Makefile not found at: {makefile_path}")

        try:
            os.chdir(project_directory)
        except OSError as e:
            return self.return_error(job.job_id, ERROR_CWD_FAILURE,
                                     f"ERROR: Unable to change directory to: {project_directory} {e}")

        # Dry-run handled synchronously
        if command.strip().endswith("-n"):
            job.dry_run = True
            process = QProcess()
            process.startCommand(command)

            if not process.waitForStarted():
                return self.return_error(job.job_id, ERROR_START_FAILURE,
                                         f"\nERROR: Failed to start dry-run: {command}")

            process.waitForFinished()
            output = process.readAllStandardOutput().data().decode()
            error_output = process.readAllStandardError().data().decode()

            if any(x in output for x in [".sh", "make"]) or error_output:
                job.build_required = True

            self.output(output)
            self.output(error_output)
            self.make_finished.emit(job.job_id, process.exitCode())
            return process.exitCode()

        # Async process
        job.dry_run = False
        job.process = QProcess()

        job.process.readyReadStandardOutput.connect(lambda job_id=job.job_id: self._on_standard_output(job_id))
        job.process.readyReadStandardError.connect(lambda job_id=job.job_id: self._on_standard_error(job_id))
        job.process.finished.connect(lambda code, _=None, job_id=job.job_id: self._on_process_finished(job_id, code))

        self.info(f"ID {job.job_id} - Make command: {command}")

        try:
            job.process.startCommand(command)
        except Exception as e:
            return self.return_error(job.job_id, ERROR_START_FAILURE,
                                     f"ERROR: Unable to start process: {e}")

        if not job.process.waitForStarted():
            return self.return_error(job.job_id, ERROR_START_FAILURE,
                                     f"\nERROR: Unable to run {command}")

        return job.job_id

    def _on_process_finished(self, job_id, exit_code):
        self.info(f"Job {job_id} finished with exit code {exit_code}")
        job = self.jobs.pop(job_id, None)
        if job and job.process:
            job.process.deleteLater()
        self.make_finished.emit(job_id, exit_code)

    def return_error(self, job_id, error, message):
        self.output(f"\033[33m{message}\x1b[0m")
        self.make_finished.emit(job_id, error)
        return error

    def get_user_data(self, job_id):
        return self.jobs[job_id].user_data

    def clear_output(self):
        """
        Clear output window
        """
        # todo if self._output_window:
            #self._output_window.clear()
        pass

    def output(self, text):
        """
        Output the given text to the output window

        Args:
            text (str): The text to display in the output window.
        """
        if self._output_window:
            self._output_window.moveCursor(QTextCursor.MoveOperation.End)
            self._append_ansi_text(text)
            self._output_window.moveCursor(QTextCursor.MoveOperation.End)

    def cancel(self):
        """
        Cancel the currently running make process.
        """
        # todo - walk through all processes in self.processes and kill them
        #self.process.kill()
        #self.make_finished.emit(self.job_id, 2)

    def _on_standard_output(self, job_id):
        """
        Handle and display standard output from the specified make process.

        Args:
            job_id (int): Identifier for the job.
        """
        job = self.jobs.get(job_id)
        if not job or not job.process:
            return

        output = job.process.readAllStandardOutput().data().decode()

        if self._output_window:
            self._output_window.moveCursor(QTextCursor.MoveOperation.End)
            self._append_ansi_text(output)
            self._output_window.moveCursor(QTextCursor.MoveOperation.End)

        # Detect if dry run shows work to be done
        if job.dry_run and ".sh " in output:
            job.build_required = True

    def _on_standard_error(self, job_id):
        """
        Handle and display standard error output from the specified make process.

        Args:
            job_id (str): Identifier for the  job.
        """
        job = self.jobs.get(job_id)
        if not job or not job.process:
            return

        job.build_required = True

        output = job.process.readAllStandardError().data().decode()

        if self._output_window:
            self._output_window.moveCursor(QTextCursor.MoveOperation.End)

            # Highlight likely errors
            if any(keyword in output for keyword in ("ERR", "err", "Err", "failed")):
                self._append_ansi_text(f"\033[33m{output}\x1b[0m")
            else:
                self._append_ansi_text(output)

            self._output_window.moveCursor(QTextCursor.MoveOperation.End)

    def _append_ansi_text(self, text):
        """
        Parse ANSI escape sequences and append styled text to the output window.

        Args:
            text (str): The text containing ANSI escape sequences.
        """
        cursor = self._output_window.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        default_format = QTextCharFormat()
        current_format = QTextCharFormat()
        if self.dark_mode:
            current_format.setForeground(QColor('white'))  # Default color
        else:
            current_format.setForeground(QColor('black'))  # Default color

        pos = 0
        for match in ANSI_ESCAPE.finditer(text):
            start, end = match.span()

            # Insert the text up to the ANSI escape sequence
            cursor.insertText(text[pos:start], current_format)
            pos = end

            # Update the current format based on ANSI codes
            codes = match.group(1).split(';')
            if '0' in codes:  # Reset to default
                current_format = QTextCharFormat(default_format)
            for code in codes:
                if code in ANSI_COLOR_MAP:
                    color = ANSI_COLOR_MAP[code]
                    current_format.setForeground(QColor(color))

        # Insert the remaining text
        cursor.insertText(text[pos:], current_format)

    def warn(self, message):
        if self.verbose > 2:
            print(f"WARNING: {message}")

    def info(self, message):
        if self.verbose > 3:
            print(f"INFO: {message}")
