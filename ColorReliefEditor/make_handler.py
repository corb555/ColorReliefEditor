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
        self.output_window.clear()
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
            self.output_window.clear()
            self.output("Image is up to date. ✅")
            return True
