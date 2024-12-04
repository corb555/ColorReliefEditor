Function: color_relief.sh
=========================
This script provides utilities for processing DEM files using GDAL tools.
All gdal flags are pulled from a YAML file.
##
Main Functions:
---------------
  - Create VRT from DEM files and set CRS
  - Generate hillshades
  - Create color reliefs
  - Merge hillshade and color relief images
##
The following options run GDAL utilities using parameters from a YAML config file:
  -  --init_dem <region>: Merges multiple DEM files into a single output DEM for the specified region.
  -  --create_color_relief <region>: Generates a color relief image from a DEM file using a specified color ramp.
  -  --create_hillshade <region>: Produces a hillshade image from a DEM file with configurable parameters.
  -  --merge_hillshade <region>: Combines color relief and hillshade images into a single relief image.
  -  --preview_dem <region>: Extracts a small section from the merged DEM file for preview generation.
##
File Naming Standards:
   - ending defaults to "tif"
   - suffix is "_prv" or blank depending on preview mode
   - config "${region}_relief.cfg"
   - dem_file "${region}_${layer}${suffix}_DEM.${ending}"
   - color_relief "${region}_${layer}${suffix}_color.${ending}"
   - hillshade "${region}_${layer}${suffix}_hillshade.${ending}"
Function: init
   Initializes essential variables for the region and layer.
   Verifies the config file exists and key utilities are available (yq, gdal)
   Sets quiet mode, file ending, and dem_file name
   Args:
     $1 Region:
     $2 Layer:
     $3 Preview: Blank or "preview" to indicate preview generation or full file generation
##
Function: finished
Called after function finished. If TIMING is enabled, displays
   elapsed time since the script started.
Args:
  $1: File name of the created target
Function: check_command
Verifies if a required command is available in the environment.
Exit script with error if the command is not found.
Args:
  $1: Command name to check
Function: optional_flag
Retrieve an optional flag from the YAML configuration file.
Args:
  $1: Configuration file path
  $2: Key to search for in the YAML file
Function: mandatory_flag
Retrieves a mandatory flag from the YAML configuration file.
Exits with an error if the key is not found.
Args:
  $1: Configuration file path
  $2: Key to search for in the YAML file
Function: get_flags
Retrieves multiple flags from the YAML configuration file.
Args:
  $1: Region name
  $2: Configuration file path
  $3, ...: List of keys to search for in the YAML file
Function: verify_files
Verifies that each file passed exists.
If any file is missing exit with an error.
Args:
  $@ (variable): List of file paths to check for existence
Function: run_gdal_calc
Runs gdal_calc.py to merge bands from two files using a calculation specified in the YAML config.
Args:
  $1: Band number to merge
  $2: Target output file
Shell variables:
  merge_calc: Calculation for merging A and B bands
  merge_flags: Flags for running gdal_calc
  color_file: RGB color relief file
  hillshade_file: Grayscale Hillshade
Function: set_crs
Applies CRS to the input file if provided. If no WARP flags exist, the input file is
renamed to the target.
Args:
  $1: Input file path
  $2: Target file path
YML Config Settings:
  WARP1 through WARP4 - used for gdalwarp flags
Function: create_preview_dem
Creates a smaller DEM file as a preview image. Preview location
is controlled by x_shift, y_shift
Args:
  $1: Input file path (DEM)
  $2: Target output file path for preview DEM
YML Config Settings:
  X_SHIFT - 0 is left, 0.5 is middle, 1 is right
  Y_SHIFT - 0 is top, 0.5 is middle, 1 is bottom
  PREVIEW - pixel size of preview DEM.  Default is 1000
--init_DEM - Create a merged DEM file and a truncated DEM preview file.  Optionally set CRS
             $1 is region name
             $2 is layer name
YML Config Settings:
  LAYER - The active layer_id (A-G).  (Different from layer name)
  FILES.layer_id - The file names for the active layer
--preview_dem -  Create a truncated DEM file to build fast previews
             $1 is region name $2 is layer name $3 preview
--create_color_relief -  gdaldem color-relief
             $1 is region name $2 is layer name $3 preview flag
YML Config Settings:
  OUTPUT_TYPE  -of GTiff
  EDGE -compute_edges
--hillshade -  gdaldem hillshade
             $1 is region name $2 is layer name $3 preview
YML Config Settings:
  OUTPUT_TYPE  -of GTiff
  HILLSHADE1-5 gdaldem hillshade hillshade flags
--merge - merge hillshade with color relief
             $1 is region name $2 is layer name $3 preview
YML Config Settings:
  MERGE1-4 - gdal_calc.py flags
  COMPRESS - compression type.  --co=COMPRESS=ZSTD
  MERGE_CALC - calculation to run in gdal_calc.py
--dem_trigger - create dem_trigger file if it doesnt exist
             $1 is region name $2 is layer name $3 preview
