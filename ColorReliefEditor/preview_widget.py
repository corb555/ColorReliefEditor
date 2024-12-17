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
from contextlib import contextmanager
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from ColorReliefEditor.tab_page import TabPage, create_hbox_layout, create_button, \
    create_readonly_window
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy, QMessageBox


class PreviewWidget(TabPage):
    """
    A widget for creating and optionally displaying generated images.

    This widget supports two operational modes:
    - **Preview Mode**: Generates smaller images for quick viewing.
    - **Full Build Mode**: Produces full-sized images with additional options for viewing,
      publishing, and cleaning temporary files.

    Attributes:
        preview_mode (bool): Determines the operational mode (Preview or Full Build).
        connected_to_make (bool): Indicates if the widget is connected to the make process.
        button_flags (list): Specifies the set of buttons available for the mode.
        image_label (QLabel): Displays the generated image in preview mode.
        zoom_factor (float): The current zoom level for the image display.
        make_handler (MakeHandler): Manages the `make` process for image generation and maintenance.
    """

    def __init__(self, main, name, settings, preview_mode, on_save, button_flags):
        """
        Initialize the widget and configure its components based on the operational mode.

        Args:
            main (object): Reference to the main application object.
            name (str): The name of this widget/tab.
            settings (object): Application settings object for configuration.
            preview_mode (bool): Whether the widget is in preview mode.
            on_save (callable): Callback function executed upon saving.
            button_flags (list): Flags specifying which buttons to display.
        """
        super().__init__(main, name, on_exit_callback=on_save, on_enter_callback=settings.display)
        # Button definitions
        self.button_definitions = [
            {"flag": "make", "label": "Create", "callback": self.make_image, "focus": True},
            {"flag": "view", "label": "View...", "callback": self.launch_viewer, "focus": False},
            {"flag": "publish", "label": "Publish", "callback": self.publish, "focus": False}, {
                "flag": "clean", "label": "Delete temp files", "callback": self.make_clean,
                "focus": False
            }, {
                "flag": "cancel", "label": "Cancel", "callback": self.on_cancel_button,
                "focus": False
            }, ]
        self.preview_mode = preview_mode
        self.connected_to_make = False
        self.button_flags = button_flags

        # Image parameters
        self._image_file = None
        self._pixmap = None

        self.image_label = None
        self.zoom_factor = 1.0

        # General Buttons
        self.make_button = None

        # Full Build Buttons
        self.cancel_button = None
        self.clean_button = None
        self.publish_button = None
        self.view_button = None

        # Output window parameters
        self.output_max_height = 400
        self.output_min_height = 80
        self.output_window = None

        self.init_ui()

        # Run make in multiprocessor mode?
        if self.main.app_config["MULTI"] == 'multi':
            multi = ' -j '
        else:
            multi = ''
        self.make_handler = MakeHandler(
            main, self.output_window, self.tab_name, multiprocess_flag=multi
        )

        if not self.connected_to_make:
            self.make_handler.make_process.make_finished.connect(self.on_make_done)
            self.connected_to_make = True

    def init_ui(self):
        """
        Initialize UI components for the display
        """
        self.standard_stretch = [1, 2, 8]
        self.error_stretch = [1, 5, 5]
        self.full_stretch = [1, 8, 0]
        if self.preview_mode:
            # Preview Build Mode - create widget to display a preview image
            self.image_label = QLabel(self)
            self.image_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            self.image_label.setMinimumSize(
                400, 400
            )  # Allow the QLabel to shrink to a reasonable minimum size

            # Preview mode just has "Preview" button
            self.make_button = create_button("Preview", self.make_image, True, self)
            button_layout = create_hbox_layout([self.make_button])
            height = self.output_min_height
            stretch = self.standard_stretch
        else:
            # Full Build Mode
            # Create the buttons in button_flags
            buttons = []

            # Create buttons that are in self.button_flags
            for defn in self.button_definitions:
                if defn["flag"] in self.button_flags:
                    button = create_button(defn["label"], defn["callback"], defn["focus"], self)
                    buttons.append(button)

            button_layout = create_hbox_layout(buttons)
            height = self.output_max_height
            stretch = self.full_stretch

        # Create window for process output
        self.output_window = create_readonly_window()
        self.output_window.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.output_window.setMinimumSize(100, 250)

        widgets = [button_layout, self.output_window, self.image_label]
        self.create_page(widgets, None, None, None, vertical=True, stretch=stretch)

    def make_image(self):
        self.on_save()
        self.set_buttons_ready(False)
        layer = self.main.project.get_layer()
        self.image_file = self.make_handler.make_image(
            self.tab_name.lower(), self.preview_mode, [layer]
        )

    def make_clean(self):
        self.set_buttons_ready(False)
        layer = self.main.project.get_layer()
        self.make_handler.make_clean([layer])

    def on_make_done(self, name, exit_code):
        if name == self.tab_name:
            self.set_buttons_ready(True)

            if exit_code == 0:
                # Only display "Done" if this wasn't a dry run
                if not self.make_handler.dry_run:
                    msg = "Done ✅"
                    self.output(msg)

                # Success: Display image
                if self.image_label:
                    self.use_error_layout(False)

                    # Load the image into the label
                    success = self.load_image(self.image_file)
                    if not success:
                        self.output(f"Error: cannot load {self.image_file} ❌")
            else:
                # Error: Display output window at full size
                self.output(f"Error - exit={exit_code} ❌")

                if self.output_window:
                    self.use_error_layout(True)

    def publish(self):
        """
        Copy the generated image to the directory specified in config.

        Raises:
            OSError: If there is an issue during the file copy operation.
        """
        image_path = self.get_image_path()
        dest = self.main.proj_config.get("PUBLISH") or ""
        if dest != "":
            destination_folder = Path(dest)  # Convert to Path object
        else:
            destination_folder = ""

        if destination_folder == "" or not destination_folder.is_dir():
            QMessageBox.warning(
                self.main, "Error", f"Publish directory '{destination_folder}' does not exist."
            )
            return

        # Check if the project is up to date and confirm action if needed
        layer = self.main.project.get_layer()
        target = self.main.project.get_target_image_name(
            self.tab_name.lower(), self.preview_mode, layer
        )
        if self.cancel_for_out_of_date("Publish", target):
            return

        target_path = destination_folder / Path(image_path).name
        try:
            shutil.copy2(image_path, target_path)
            QMessageBox.information(self.main, "Success", f"Image copied to {target_path}")
        except OSError as e:
            QMessageBox.warning(self.main, "Error", f"Error copying image: {str(e)}")

    def use_error_layout(self, error):
        """
        Adjust image size and output size based on whether an error occurred
        """
        if self.preview_mode:
            if error:
                # Error -  expand output size
                output_height = self.output_max_height
            else:
                # No error - expand image and shrink output
                output_height = self.output_min_height

            self.output_window.setFixedHeight(output_height)

    def on_cancel_button(self):
        """
        Cancel the make process.
        """
        self.make_handler.make_process.cancel()

    def set_buttons_ready(self, ready):
        """
        Enable or disable buttons based on the state.
        The cancel button takes the opposite state
        Args:
            ready (bool): Whether buttons should be enabled.
        """
        for button, state in [(self.make_button, ready), (self.clean_button, ready),
                              (self.publish_button, ready), (self.view_button, ready),
                              (self.cancel_button, not ready)]:
            if button:
                button.setEnabled(state)

    @property
    def image_file(self):
        """
        Get the path of the preview file.
        """
        return self._image_file

    @image_file.setter
    def image_file(self, file_path):
        """
        Set the path of the preview file.

        Args:
            file_path (str): Path to the preview file.
        """
        self._image_file = file_path

    def output(self, message):
        self.output_window.appendPlainText(message)

    def launch_viewer(self):
        """
        Launch an external viewer for a very large image
        Returns:

        """
        image_path = self.get_image_path()

        # Check if the project is up to date and confirm action if build needed
        layer = self.main.project.get_layer()
        target = self.main.project.get_target_image_name(
            self.tab_name.lower(), self.preview_mode, layer
        )
        if self.cancel_for_out_of_date("View", target):
            return

        # Get user preferred viewer app from config
        app = self.main.app_config["VIEWER"]
        self.output(f"Launched {app} ✅")
        system = platform.system()

        # On Mac/Darwin use Preview as the default viewer
        if system == "Darwin" and app == "default":
            app = "Preview"

        # On Linux, use xdg-open to bring up the default viewer
        if system == "Linux" and app == "default":
            # Linux: Use xdg-open to launch the default viewer
            try:
                subprocess.Popen(
                    ["xdg-open", image_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
            except Exception as e:
                self._handle_viewer_error(e, "xdg-open", image_path)

            except subprocess.CalledProcessError as e:
                success = False
                error_message = e.stderr.decode("utf-8")
                print(f"Error opening item with xdg-open: {error_message}")
        else:
            launch_app(app, image_path)

    def _handle_viewer_error(self, error, app_name, file_path):
        """
        Handles errors when launching a viewer application.

        Args:
            error (Exception): Exception that occurred.
            app_name (str): Name of the viewer application.
            file_path (str): Path to the file attempted to open.

        Returns:
            None
        """
        error_message = f"Failed to launch '{app_name}' for file '{file_path}'.\nError: {str(error)}"
        print(error_message)
        QMessageBox.critical(self, "Viewer Error", error_message)

    def cancel_for_out_of_date(self, action, target):
        """
        Displays a confirmation dialog if the project is out of date.

        Args:
            action (str): The name of the action (e.g., 'Publish', 'View') to display in the dialog.
            target (str): The name of the target
        Returns:
            bool: True if out of date, and they cancel, False to proceed,
        """
        # Check if the project is up to date
        if not self.make_handler.up_to_date(target):
            # Prompt the user to confirm action even if not up to date
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirmation")
            msg_box.setText(f"Build is out of date, {action} anyway?")

            # Add Action and Cancel buttons
            msg_box.addButton(action, QMessageBox.ButtonRole.AcceptRole)
            cancel_button = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

            # Execute the message box
            msg_box.exec()

            # Check which button was clicked and return True for cancel
            if msg_box.clickedButton() == cancel_button:
                return True
        return False

    def get_image_path(self):
        layer = self.main.project.get_layer()
        target = self.main.project.get_target_image_name(
            self.tab_name.lower(), self.preview_mode, layer
        )
        return str(Path(self.main.project.project_directory) / target)

    def load_image(self, file_path):
        """
        Load and display an image from the given file path.

        Args:
            file_path (str): Path to the image file.
        Returns:
            True on success
        """
        if not file_path:
            raise ValueError("Image file path is empty.")

        self._pixmap = QPixmap(file_path)

        if self._pixmap.width() == 0:
            self.zoom_factor = 1
            return False

        # Use a single-shot timer to defer zoom until geometry is set
        QTimer.singleShot(0, self.zoom_image)
        return True

    def zoom_image(self):
        """
        Update the displayed image according to the current zoom factor.
        """
        if not self._pixmap:
            return

        label_width = self.image_label.width()
        label_height = self.image_label.height()

        # Get dimensions of the pixmap and the image label
        image_width = self._pixmap.width()
        image_height = self._pixmap.height()
        if image_width == 0:
            return

        # Calculate the scaling factors for both width and height
        width_factor = label_width / image_width
        height_factor = label_height / image_height

        # Use the smaller of the two scaling factors to fit the image
        self.zoom_factor = min(width_factor, height_factor)
        scaled_pixmap = self._pixmap.scaled(
            int(self._pixmap.width() * self.zoom_factor),
            int(self._pixmap.height() * self.zoom_factor), Qt.AspectRatioMode.KeepAspectRatio
        )
        self.image_label.setPixmap(scaled_pixmap)
        self.display()

    def resizeEvent(self, event):
        """
        This method is called whenever the window is resized.
        """
        super().resizeEvent(event)
        self.zoom_image()


@contextmanager
def suppress_stderr():
    """
    Context manager to suppress stderr output.
    """
    # Save original stderr
    old_stderr = sys.stderr
    stderr_fileno = sys.stderr.fileno()

    # Open a null device (to discard output)
    devnull = open(os.devnull, 'w')

    # Redirect stderr to null device
    os.dup2(devnull.fileno(), stderr_fileno)

    try:
        yield
    finally:
        # Restore original stderr
        os.dup2(old_stderr.fileno(), stderr_fileno)
        devnull.close()


def launch_app(app_name, file_path, parent=None):
    """
    Launches the specified application with the  file and brings the app to the front.

    Args:
        app_name (str): The name of the application to launch.
        file_path (str): The path to the file for the app
        parent (QWidget, optional): The parent widget for the error message dialog.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the operating system is not supported.
    """
    if not os.path.exists(file_path):
        QMessageBox.warning(parent, "Error", f"File '{file_path}' does not exist.")
        return

    system = platform.system()

    try:
        if system == "Linux":
            subprocess.run([app_name, file_path], check=True)
            subprocess.run(
                ['xdotool', 'search', '--onlyvisible', '--name', app_name, 'windowactivate']
            )
        elif system == "Darwin":  # macOS
            subprocess.run(["open", "-a", app_name, file_path], check=True)
            subprocess.run(['osascript', '-e', f'tell application "{app_name}" to activate'])
        elif system == "Windows":
            subprocess.run([app_name, file_path], check=True)
        else:
            raise OSError(f"Unsupported operating system: {system}")

    except FileNotFoundError:
        QMessageBox.warning(parent, "Error", f"{app_name} not found.")
    except subprocess.CalledProcessError as e:
        QMessageBox.warning(parent, "Error", f"{app_name} not found. {e}")
    except OSError as e:
        QMessageBox.warning(parent, "Error", str(e))


class MakeHandler:
    """
    Handles make process for generating, viewing, and publishing images.
    """

    def __init__(self, main, output_window, tab_name, multiprocess_flag=" -j "):
        self.main = main
        self.output_window = output_window
        self.tab_name = tab_name
        self.multiprocess_flag = multiprocess_flag
        self.dry_run = False
        self.make_process = main.make_process
        self.make = self.main.make_process.make

    def output(self, message):
        self.output_window.appendPlainText(message)

    def get_make_command(self, base, dry_run_flag=False):
        region = self.main.project.region
        layer = self.main.project.get_layer()

        if not layer:
            return f"{self.make} REGION={region} LAYER='' -f Makefile layer_not_set"

        dry_run = " -n" if dry_run_flag else ""
        self.dry_run = dry_run_flag

        return (f"{self.make} {self.multiprocess_flag if not dry_run_flag else ''} REGION={region} "
                f"LAYER={layer} -f Makefile {base} {dry_run}")

    def make_image(self, base, preview_mode, layers):
        for layer in layers:
            target = self.main.project.get_target_image_name(base, preview_mode, layer)
            command = self.get_make_command(target)
            self.run_make(command)
            return target

    def make_clean(self, layers):
        for layer in layers:
            if layer and self.main.project.region:
                command = (
                    f"{self.make} REGION={self.main.project.region} LAYER={layer} -f Makefile "
                    f"clean")
                self.run_make(command)
            else:
                self.output("Error: layer name is empty.")

    def run_make(self, command):
        project_directory = self.main.project.project_directory
        makefile_path = self.main.project.makefile_path
        self.make_process.run_make(
            makefile_path, project_directory, command, self.tab_name, self.output_window
        )

    def up_to_date(self, target):
        """
        Check if the project is up to date by running a dry-run of the make process.
        Returns True if the project is up to date, False otherwise.
        """
        # Get the make command with the dry-run option
        command = self.get_make_command(dry_run_flag=True, base=target)

        project_directory = self.main.project.project_directory
        makefile_path = self.main.project.makefile_path

        # Run the make process with dry-run to check if anything would be built

        self.make_process.run_make(
            makefile_path, project_directory, command, self.tab_name, self.output_window
        )

        # If no build is required, return True (project is up to date), otherwise False
        if self.make_process.build_required:
            self.output("The image is out of date.  Click Create to build the image.")
            return False
        else:
            self.output("Image is up to date. ✅")
            return True
