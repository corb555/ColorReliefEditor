from pathlib import Path


class MakeWrapper:
    """
    App interface for make_process for generating, viewing, and publishing images.
    High-level wrapper around MakeProcess
    Knows about the project structure (region, layer, makefile, etc.)
    Constructs make commands from domain-specific knowledge
    Triggers make, make clean, etc.
    Handles dry-run toggling and interprets layer configuration
    """

    def __init__(self, main, output_window, multiprocess_flag=" -j "):
        self.main = main
        self.output_window = output_window
        self.multiprocess_flag = multiprocess_flag
        self.dry_run = False
        self.make_process = main.make_process
        self.make = self.main.make_process.make

    def build_make_command(self, base, dry_run_flag=False):
        region = self.main.project.region
        layer = self.main.project.get_layer()

        if not layer:
            return (f"{self.make} REGION={region}"
                    f" LAYER='' -f Makefile layer_not_set")

        dry_run = " -n" if dry_run_flag else ""
        self.dry_run = dry_run_flag

        return (f"{self.make} {self.multiprocess_flag if not dry_run_flag else ''} REGION={region} "
                f"LAYER={layer} -f Makefile {base} {dry_run}")

    def make_image(self, target):
        """
        Generates an image using the provided target path.

        This method constructs a make command based on the provided target
        and executes it to generate the corresponding image.

        Args:
            target: The file system path of the target for which an image will
                be built.

        Returns:
            int: Job index if successful, or negative error code on failure.
        """
        command = self.build_make_command(target)
        return self.run_make(command)

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
        """
        Runs the Make command in the specified project environment.

        This method executes the specified Make command using the provided
        base image and project configuration settings. The output from the
        command is displayed in the associated output window.

        Args:
            command: the Make command and its
                arguments to be executed.

        Returns:
            int: The job_id or a negative error code
        """
        project_directory = self.main.project.project_directory
        makefile_path = self.main.project.makefile_path
        return self.make_process.run_make(
            makefile_path, project_directory, command, self.output_window
        )

    def up_to_date(self, target):
        """
        Check if the project is up to date by running a dry-run of the make process.
        Returns True if the project is up to date, False otherwise.
        """
        # Get the make command with the dry-run option
        command = self.build_make_command(dry_run_flag=True, base=target)

        project_directory = self.main.project.project_directory
        makefile_path = self.main.project.makefile_path

        # Run the make process with dry-run to check if anything would be built

        job_id = self.make_process.run_make(
            makefile_path, project_directory, command, self.output_window
        )

        # If no build is required, return True (project is up to date), otherwise False
        if self.make_process.build_required.get(job_id, False):
            self.output("The image is out of date.  Click Create to build the image.")
            return False
        else:
            self.output_window.clear()
            self.output("Image is up to date. ✅")
            return True

    def output(self, message):
        self.output_window.appendPlainText(message)
