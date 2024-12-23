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
import re
import shutil
import subprocess
import sys
import tempfile

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy, QMessageBox

from ColorReliefEditor.make_handler import MakeHandler
from ColorReliefEditor.tab_page import TabPage, create_hbox_layout, create_button, \
    create_readonly_window


class PreviewWidget(TabPage):
    """
    A widget for creating and displaying images using Make

    This widget has two modes:
    - **Preview Mode**: Generates small images for quick viewing.
    - **Full Build Mode**: Produces full-sized images with features for publishing, cleaning
    temporary files, and
      launching an external viewer.

    Attributes:
        preview_mode (bool): Determines the operational mode (Preview or Full Build).
        image_label (QLabel): Displays the generated image in preview mode.
        zoom_factor (float): The current zoom level for the image display.
        make_handler (MakeHandler): Manages the `make` process for image generation and maintenance.
    """

    def __init__(self, main, name, settings, preview_mode, on_save, button_flags):
        """
        Initialize

        Args:
            main (object): the main application object.
            name (str): The name of this widget/tab.
            settings (object): Application settings object for configuration.
            preview_mode (bool): Whether the widget is in preview mode.
            on_save (callable): Callback function executed upon saving.
            button_flags (list): List of buttons with their attributes to display.
        """
        self.image_file = None
        self.image = None
        self.image_layer = None
        self.settings = settings
        super().__init__(main, name, on_exit_callback=on_save, on_enter_callback=self.redisplay)

        # Button definitions
        self.button_definitions = [
            {"id": "make", "label": "Create", "callback": self.make_image, "focus": True},
            {"id": "view", "label": "View...", "callback": self.launch_viewer, "focus": False},
            {"id": "publish", "label": "Publish", "callback": self.publish, "focus": False}, {
                "id": "clean", "label": "Delete temp files", "callback": self.make_clean,
                "focus": False
            }, {
                "id": "cancel", "label": "Cancel", "callback": self.on_cancel_button, "focus": False
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
        # Create window for process output
        self.output_window = create_readonly_window()
        self.output_window.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Vertical size ratios of widgets:  button, output_window, image_label
        preview_ratio = [1, 3, 15]
        full_ratio = [1, 20, 0]

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
            stretch = preview_ratio
        else:
            # Full Build Mode
            # Create the buttons in button_flags
            buttons = []

            # Create buttons that are in self.button_flags
            for defn in self.button_definitions:
                if defn["id"] in self.button_flags:
                    button = create_button(defn["label"], defn["callback"], defn["focus"], self)
                    buttons.append(button)

            button_layout = create_hbox_layout(buttons)
            height = self.output_max_height
            stretch = full_ratio

        self.image = Image(
            self.main, tab_name=self.tab_name, image_label=self.image_label,
            preview_mode=self.preview_mode
        )

        self.output_window.setMinimumSize(60, height)

        widgets = [button_layout, self.output_window, self.image_label]
        self.create_page(widgets, None, None, None, vertical=True, stretch=stretch)

    def redisplay(self):
        self.settings.display()

        # If layer was changed, reload image for new layer
        if self.image_layer != self.main.project.get_layer() and self.image:
            self.image_layer = self.main.project.get_layer()
            self.output_window.clear()
            self.image.load_image(zoom=False)
            self.image.zoom_image()

    def make_image(self):
        self.set_buttons_ready(False)
        self.on_save()

        self.image_layer = self.main.project.get_layer()

        self.image_file = self.make_handler.make_image(
            self.image.get_image_base(), self.preview_mode, [self.image_layer]
        )

    def make_clean(self):
        self.set_buttons_ready(False)
        self.make_handler.make_clean([self.main.project.get_layer()])

    def on_make_done(self, name, exit_code):
        if name == self.tab_name:
            self.set_buttons_ready(True)

            if exit_code == 0:
                # Only display "Done" if this wasn't a dry run
                if not self.make_handler.dry_run:
                    msg = "Done ✅"
                    self.output(msg)

                # Display image
                if self.image_label:
                    # Load the image into the label
                    image_loaded = self.image.load_image()
                    if not image_loaded:
                        self.output(f"Error: cannot load {self.image_file} ❌")

    def publish(self):
        """
        Copy the generated image to the directory specified in config.

        Raises:
            OSError: If there is an issue during the file copy operation.
        """
        if self.image is None:
            QMessageBox.warning(
                self.main, "Error", f"No Image available"
            )
            return

        image_path = self.image.construct_image_path()
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
            self.image.get_image_base(), self.preview_mode, layer
        )
        if self.cancel_for_out_of_date("Publish", target):
            return

        target_path = destination_folder / Path(image_path).name
        try:
            shutil.copy2(image_path, target_path)
            QMessageBox.information(self.main, "Success", f"Image copied to {target_path}")
        except OSError as e:
            QMessageBox.warning(self.main, "Error", f"Error copying image: {str(e)}")

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

    def output(self, message):
        self.output_window.appendPlainText(message)

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
            msg_box.setWindowTitle("Out of Date")
            msg_box.setText(f"Image is out of date, {action} anyway?")

            # Add Action and Cancel buttons
            msg_box.addButton(action, QMessageBox.ButtonRole.AcceptRole)
            cancel_button = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

            # Execute the message box
            msg_box.exec()

            # Check which button was clicked and return True for cancel
            if msg_box.clickedButton() == cancel_button:
                return True
        return False

    def resizeEvent(self, event):
        """
        Resize the image when the window is resized
        """
        super().resizeEvent(event)
        if self.image:
            self.image.zoom_image()
        self.display()

    def launch_viewer(self):
        """
        Launch an external viewer for a very large image
        Returns:

        """
        image_path = ""
        if self.image:
            image_path = self.image.construct_image_path()
        if not os.path.exists(image_path):
            QMessageBox.warning(self, "Error", f"File '{image_path}' does not exist.")
            return

        # Check if the project is up to date and confirm action if build needed
        layer = self.main.project.get_layer()
        target = self.main.project.get_target_image_name(
            self.image.get_image_base(), self.preview_mode, layer
        )
        if self.cancel_for_out_of_date("View", target):
            return

        # Get user preferred viewer app from config
        app = self.main.app_config["VIEWER"]

        try:
            # Attempt to launch the viewer application
            app = self.launch_application(app, image_path)
        except Exception as e:
            self.output(f"Error launching {app}: {str(e)}")
            return

        self.output(f"Launching {app} ✅")

    def launch_application(self, app, image_path):
        """
        Launch an application to open the given image file.

        Args:
            app (str): The application to use ('default' for system viewer).
            image_path (str): Path to the image file.

        Returns:
            str: The name of the application chosen to launch.

        Raises:
            ValueError: If the operating system is unsupported or an invalid app is specified.
            FileNotFoundError: If the specified application is not found.
            RuntimeError: If the application fails to launch the file or the window cannot be
            activated.
        """
        system = platform.system()

        # Determine the default application for the OS
        if app == "default":
            if system == "Darwin":
                app = "Preview"
            elif system == "Linux":
                app = "xdg-open"
            elif system == "Windows":
                app = "explorer"
            else:
                raise ValueError(f"Unsupported operating system: {system}")

        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", "-a", app, image_path], check=True)
            elif system == "Linux":
                # Launch the app
                subprocess.run([app, image_path], check=True)

                # Attempt to bring the application window to the foreground
                if app != "xdg-open":  # Skip window activation for xdg-open
                    try:
                        subprocess.run(
                            ["xdotool", "search", "--onlyvisible", "--name", app, "windowactivate"],
                            check=True, )
                    except FileNotFoundError as e:
                        raise RuntimeError(
                            f"xdotool is not installed or failed to activate the window for '"
                            f"{app}'."
                        ) from e
            elif system == "Windows":
                subprocess.run([app, image_path], check=True)
            else:
                raise ValueError(f"Unsupported operating system: {system}")
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Application '{app}' not found. Ensure it is installed and accessible."
            ) from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to launch application '{app}' for file '{image_path}'.\n{str(e)}"
            ) from e

        return app


class Image:
    def __init__(self, main, tab_name, image_label, preview_mode):
        self._pixmap = None
        self.zoom_factor = None
        self.main = main
        self.tab_name = tab_name
        self.image_label = image_label
        self.preview_mode = preview_mode
        self._image_file = None

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

    def construct_image_path(self):
        layer = self.main.project.get_layer()
        target = self.main.project.get_target_image_name(
            self.get_image_base(), self.preview_mode, layer
        )
        return str(Path(self.main.project.project_directory) / target)

    def get_image_base(self):
        if self.tab_name.lower() == "create":
            return "relief"
        else:
            return self.tab_name.lower()

    def load_image(self, zoom=True):
        """
        Load and display an image from the given file path.

        Args:
            zoom (bool): Whether the image should be zoomed.
        Returns:
            True if image loaded
        """
        if not self.image_label:
            return

        # self.image_layer = self.main.project.get_layer()
        file_path = self.construct_image_path()
        if not file_path:
            self.image_label.clear()  # Clear the image label
            self.image_label.update()  # Update the label to reflect the clear state
            return False

        # Load the image.  Filter stderr during load for spurious warnings on GeoTiff tags
        with filter_stderr(r'Unknown field with tag \d+'):
            self._pixmap = QPixmap(file_path)

        if self._pixmap.width() == 0:
            # Can't load image
            self.image_label.clear()  # Clear the image label
            self.image_label.update()  # Update the display
            self.zoom_factor = 1
            return False
        if zoom:
            # Use a single-shot timer to defer zoom until geometry is set
            QTimer.singleShot(0, self.zoom_image)
        else:
            # todo self.use_error_layout(False)
            self.image_label.setPixmap(self._pixmap)
            self.image_label.update()

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


@contextmanager
def filter_stderr(pattern):
    """
    Context manager to suppress specific warnings in stderr.

    Args:
        pattern (str): Suppress messages containing this regular expression.
    """
    # Save the original stderr file descriptor
    original_stderr_fd = os.dup(sys.stderr.fileno())

    # Create a temporary file to capture stderr
    with tempfile.TemporaryFile(mode='w+') as temp_stderr:
        # Redirect stderr to the temporary file
        os.dup2(temp_stderr.fileno(), sys.stderr.fileno())
        try:
            yield
        finally:
            # Flush and restore stderr
            os.dup2(original_stderr_fd, sys.stderr.fileno())
            os.close(original_stderr_fd)
            # Process the temporary file for filtering
            temp_stderr.seek(0)
            for line in temp_stderr:
                if not re.search(pattern, line):
                    sys.stderr.write(line)
