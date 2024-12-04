#  Copyright (c) 2024.
#   Permission is hereby granted, free of charge, to any person obtaining a
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
import importlib.resources as pkg_resources
import os
from pathlib import Path

from appdirs import user_config_dir
from YMLEditor.data_manager import DataManager

from ColorReliefEditor import resources
from ColorReliefEditor.recent_files import RecentFiles


class ProjectConfig(DataManager):
    """
    Manage project config, including opening a project and storing paths to all project files
    """

    # Project file names are <region>_<suffix>
    file_suffix = {
        "color_ramp": "_color_ramp.txt",
        "config": "_relief.cfg",
        "dem": "_DEM_trigger.cfg"
    }

    def __init__(self, main):
        """
        Initialize

        Args:
            main (MainClass): Main application class.
        """
        super().__init__()
        self.main = main
        self._data = {}
        self.project_directory, self.color_file_path, self.makefile_path = None, None, None,
        self.recent_files = RecentFiles()
        self.recent_files.load(str(app_files_path("recent_files.pkl")))
        self.region = None

    def _load_data(self, _):
        """ Update project data and statuses."""
        data = {
            "STATUS": "Project Opened",
            "PROJECT": self.region,
            "FOLDER": self.project_directory,
            "SETTINGS": self.main.proj_config.file_path,
            "COLORFILE": self.color_file_path,
            "MAKEFILE": self.makefile_path,
            "SCRIPT": 'color_relief.sh'
        }
        return data

    def set_status(self, message):
        """ Set Project error message """
        self._data["STATUS"] = message

    def _save_data(self, f, data):
        pass

    def load(self, config_path):
        """
        Load project data and update internal data.

        Args:
            config_path (str): Path to the project configuration file.
        Returns:
            True on success, False on failure.
        """
        try:
            self.main.proj_config.load(config_path)
        except Exception as e:
            self.set_status( f"{e}")
            return False

        self.region = os.path.basename(config_path).replace(ProjectConfig.file_suffix["config"], "")
        self.project_directory = os.path.dirname(config_path)
        dem_path = self.main.proj_config["DEM_FOLDER"]
        self.dem_directory = os.path.join(os.path.dirname(config_path), dem_path)
        self.color_file_path = os.path.join(
            self.project_directory, os.path.basename(config_path).replace(
                ProjectConfig.file_suffix["config"], ProjectConfig.file_suffix["color_ramp"]
            )
        )
        self.makefile_path = os.path.join(self.project_directory, "Makefile")

        # Update recent_files list
        self.recent_files.add(config_path)

        # Load and verify data
        self._data = self._load_data(None)
        self.print_project_files(config_path)
        error = not self.verify(["SETTINGS", "COLORFILE", "MAKEFILE"], ["SCRIPT"], "FOLDER", )
        if error:
            self._data["STATUS"] = "Files missing"
            return False
        else:
            self._data["STATUS"] = "Project loaded"
            return True

    def print_project_files(self, config_path):
        """
        Print project file paths.
        """
        print(f"\nProject config file: {config_path} ")
        print(f"Color definition file: {self.color_file_path} ")
        print(f"Makefile: {self.makefile_path} ")
        print(f"Color relief script: color_relief.sh ")

    def get_target_image_name(self, basename, preview_mode, layer):
        """
        Get target image name - <region>_<layer>_<basename>_<prv>.tif
        Args:
            basename: The basename for the target image (hillshade, relief, etc.)
            preview_mode (bool): True if we are in preview mode.False for normal mode
            layer: The layer name

        Returns:
            target image name
        """
        preview = "_prv" if preview_mode else ""
        return f"{self.region}_{layer}_{basename}{preview}.tif"

    def get_layer(self):
        """
        Get the name for the currently selected layer.
        """
        # Get active layer id
        layer_id = self.main.proj_config["LAYER"]

        # Get the name for the active layer id
        return self.main.proj_config[f"NAMES.{layer_id}"]

    def verify(self, file_keys, script_keys, folder_keys):
        """
        Verify the presence of required files and scripts and update status accordingly.
        Returns:
            bool: True if the files are present, False otherwise.
        """
        file_error = False

        for name, value in self._data.items():
            if name in file_keys:
                if not value or not os.path.isfile(value):
                    self._data[name] = f"{value} is missing"
                    file_error = True
            elif name in folder_keys:
                if not value or not os.path.isdir(value):
                    self._data[name] = f"{value} is missing"
                    file_error = True
            elif name in script_keys:
                if not script_available(value):
                    self._data[name] = f"{value} script missing"
                    file_error = True

        return not file_error

    def get_proxy_path(self):
        """
        Return path for Config file proxy
        """
        layer = self.main.project.get_layer()
        target = f"{self.main.project.region}_{layer}_DEM_trigger.cfg"
        return str(Path(self.main.project.project_directory) / target)

    def create_new_project(self, directory):
        """
        Creates a new project directory and initializes it with necessary files.

        Args:
            directory (str): Path to existing project directory to initialize.

        Returns:
           tuple: (success, error_message)

        Notes:
            - The function creates the following files using templates in the project resources:
              1. Config file for the region (if not already present).
              2. Color ramp file for rendering.
              3. A Makefile if it doesn't exist in the parent directory.
            - Creates an empty DEM proxy file.
            - The function ensures no existing config or ramp file is overwritten.
        """
        # Determine the region name based on the directory name
        region = os.path.basename(directory)

        # Construct file paths for the config, DEM proxy, and color ramp
        config_file_path = os.path.join(
            directory, f"{region}{ProjectConfig.file_suffix['config']}"
        )
        dem_proxy_path = os.path.join(directory, f"{region}{ProjectConfig.file_suffix['dem']}")
        ramp_file_path = os.path.join(
            directory, f"{region}{ProjectConfig.file_suffix['color_ramp']}"
        )

        # Check if config or ramp file already exists in the target directory
        if os.path.exists(config_file_path) or os.path.exists(ramp_file_path):
            # Exit if files already exist
            return False, f"Config file or ramp file already exists in {directory}."

        # Update the main configuration object with the new config file path
        self.main.proj_config.file_path = config_file_path

        # Define the Makefile path
        makefile_file_path = os.path.join(directory, "Makefile")

        # Create a Makefile if it doesn't already exist
        if not os.path.exists(makefile_file_path):
            create_file_from_resource("Makefile", makefile_file_path)

        # Create the default config file and color ramp file from resources
        create_file_from_resource(
            f"default{ProjectConfig.file_suffix['config']}", config_file_path
        )
        create_file_from_resource(
            f"default{ProjectConfig.file_suffix['color_ramp']}", ramp_file_path
        )

        # Create an empty DEM proxy file as a placeholder
        touch_file(dem_proxy_path)

        # Return True, None if no errors occurred during the process
        return True, None


def app_files_path(filename):
    """
    Determine the platform-appropriate path for app files.
    """
    app_name = "ColorReliefEditor"
    config_dir = user_config_dir(app_name)
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, filename)


def script_available(script_name):
    """
    Check if a script file is available on the user's PATH.

    Args:
        script_name (str): Name of the script file.

    Returns:
        bool: True if the script is available, False otherwise.
    """
    # Get the list of directories in the user's PATH environment variable
    path_dirs = os.getenv('PATH', '').split(os.pathsep)

    # Check each directory for the script file
    for directory in path_dirs:
        script_path = os.path.join(directory, script_name)
        if os.path.isfile(script_path) and os.access(script_path, os.X_OK):
            return True
    return False


def create_file_from_resource(
        resource_name, target_path, replace_text=None, new_text=None
):
    """
    Create a file from a resource template, optionally replacing text.

    Args:
        resource_name (str): The name of the resource to read.
        target_path (str): The path where the file should be created.
        replace_text (str, optional): The text to be replaced in the resource.
        new_text (str, optional): The text to replace replace_text with.
    """
    file_data = _read_resource(resource_name)
    if replace_text and new_text:
        file_data = file_data.replace(replace_text, new_text)
    _create_file(target_path, file_data)


def _create_file(target_path, file_data):
    """
    Create a file based on the provided data.

    Args:
        target_path (str): The path to the file to be created.
        file_data (str): The data to write to the file.
    """
    with open(target_path, 'w') as file:
        file.write(file_data)


def _read_resource(resource_name):
    """
    Read the content of a resource file.
    Args:
        resource_name (str): The name of the resource to read.

    Returns:
        str: The content of the resource file.
    """
    with pkg_resources.open_text(resources, resource_name) as resource:
        return resource.read()


def touch_file(filename):
    """
    Set the file's modification and access time to the current time.

    Args:
        filename (str): Path to the file.
    """
    with open(filename, 'a'):
        os.utime(filename, None)
