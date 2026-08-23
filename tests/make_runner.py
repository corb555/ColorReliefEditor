import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLineEdit, QLabel
)
from PyQt6.QtCore import Qt
from make_process import MakeProcess  # Assuming MakeProcess is defined in make_process.py


class MakeRunnerApp(QWidget):
    """
    A PyQt6 application for executing commands concurrently.

    This GUI provides:
      - An input field to enter commands.
      - A "Run" button to execute the command.
      - A shared output area to display real-time command output.
      - Automatic handling of multiple concurrent processes.

    Sample Makefile commands:
      make REGION=USA LAYER=Leavenworth -f Makefile USA_Leavenworth_relief.tif
      make REGION=USA LAYER=WA -f Makefile USA_WA_relief.tif
      make REGION=USA LAYER=USA -f Makefile USA_USA_relief.tif

    Attributes:
        command_input (QLineEdit): Input field for the  command.
        run_button (QPushButton): Button to initiate command execution.
        output_display (QTextEdit): Widget for displaying process output.
        process_counter (int): Unique identifier for each job to distinguish processes.
    """

    def __init__(self):
        """Initialize the main window and UI elements."""
        super().__init__()
        self.setMinimumSize(800, 600)

        # Initialize layouts
        main_layout = QVBoxLayout()
        input_layout = QHBoxLayout()

        # Create command input field
        self.command_input = QLineEdit()

        # Create Run button and connect it to the handler
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_make_command)

        # Output area (read-only)
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)

        # Assemble the layouts
        input_layout.addWidget(QLabel("Command:"))
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.run_button)
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.output_display)

        self.setLayout(main_layout)

        # Used to assign unique job names to concurrent Make processes
        self.process_counter = 0
        self.running_processes = {}
        self.project_directory = "."

    def run_make_command(self):
        """
        Extract the command from the input field and start a new MakeProcess.

        Each command is assigned a unique job name to support concurrent execution.
        """
        command = self.command_input.text().strip()
        if not command:
            self.output_display.append("[ERROR] No command provided.\n")
            return

        self.start_make_process(self.project_directory, command)

    def start_make_process(self, dir, command):
        # Generate unique job name
        job_name = f"job_{self.process_counter}"
        self.process_counter += 1

        # Create a new MakeProcess instance
        make_proc = MakeProcess(verbose=1)
        make_proc._output_window = self.output_display
        make_proc.make_finished.connect(self.make_finished_callback)
        self.running_processes[job_name] = make_proc

        # Run the command in the current working directory
        make_proc.run_make(
            makefile_path="Makefile",  # Change if your Makefile path differs
            project_directory=dir,
            command=command,
            job_name=job_name,
            output_window=self.output_display
        )

    def make_finished_callback(self, job_name, exit_code):
        """
        Handle completion of a MakeProcess.

        Args:
            job_name (str): Unique name assigned to the job.
            exit_code (int): The exit code returned by the Make process.
        """
        self.output_display.append(f"\n[INFO] Job '{job_name}' done with exit code {exit_code}\n")

        # Clean up completed process
        if job_name in self.running_processes:
            del self.running_processes[job_name]
        else:
            print("[ERROR] Job '{job_name}' not found.\n")


def main():
    """
    Entry point for the MakeRunner application.
    Initializes the QApplication and shows the main window.
    """
    app = QApplication(sys.argv)
    window = MakeRunnerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
