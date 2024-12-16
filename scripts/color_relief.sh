#!/bin/sh

#
# Copyright (c) 2024. Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including but not limited to the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

# Exit codes
ERROR_HELP=100
ERROR_CONFIG_NOT_FOUND=101
ERROR_MISSING_UTILITY=102
ERROR_OPTIONAL_FLAG_ERROR=103
ERROR_MANDATORY_FLAG_NOT_FOUND=104
ERROR_FILE_NOT_FOUND=105
ERROR_RENAMING_FAILED=106
ERROR_GDALWARP_FAILED=107
ERROR_GDAL_MERGE_FAILED=108
ERROR_PREVIEW_SIZE=109
ERROR_GDAL_COLOR_RELIEF_FAILED=110
ERROR_MISSING_FILE_PATTERN=111
ERROR_GDAL_MERGE_FAILED=112
ERROR_GDAL_CALC_FAILED=113
ERROR_INVALID_PREVIEW_SHIFT=114
ERROR_GDALBUILDVRT=115

## color_relief.sh
## =========================
## This shell script provides utilities for processing DEM files using GDAL tools.
## All gdal switches are pulled from a YAML file.
##
## Main Functions:
## ---------------
##   -  The following options run GDAL utilities using parameters from a YAML config file:
##   -  --init_dem <region>: Merges multiple DEM files into a single output DEM for the specified region.
##   -  --create_color_relief <region>: Generates a color relief image from a DEM file using a specified color ramp.
##   -  --create_hillshade <region>: Produces a hillshade image from a DEM file with configurable parameters.
##   -  --merge_hillshade <region>: Combines color relief and hillshade images into a single relief image.
##   -  --preview_dem <region>: Extracts a small section from the merged DEM file for preview generation.
##
## File Naming Standards:
## ----------------------
##    - ending defaults to "tif"
##    - suffix is "_prv" or blank depending on preview mode
##    - config "${region}_relief.cfg"
##    - dem_file "${region}_${layer}_DEM${suffix}.${ending}"
##    - color_relief "${region}_${layer}_color${suffix}.${ending}"
##    - hillshade "${region}_${layer}$_hillshade${suffix}.${ending}"
##    - final "${region}_${layer}$_relief${suffix}.${ending}"
##
## GDAL commands run:
## ------------------
## - gdalbuildvrt  $vrt_flag "$target" $file_list
## - gdalwarp $warp_flags "$input_file" "$target"
## - gdaldem color-relief $gdaldem_flags "$dem_file" "${region}_color_ramp.txt" “$target"
## - gdaldem hillshade $gdaldem_flags $hillshade_flags $quiet "$dem_file" “$target"
## - gdal_calc.py -A "$color_file" -B "$hillshade_file" --A_band="$band" —B_band=1 --calc=“$merge_calc" $merge_flags --overwrite —outfile="$target"
## - gdal_merge.py $compress -separate -o "$target" $rgb_bands
##
# UTILITY FUNCTIONS:

# Function: display_help
display_help() {
  echo "Usage: $0 --create_color_relief <region>  | --create_hillshade <region>  | --merge_hillshade <region>  | --set_crs <region>  | --init_dem <region>"
  echo $version
  echo
  echo "These switches run GDAL utilities using parameters from a YML config file:"
  echo "1. --init_dem <region>: Creates a DEM file by merging multiple DEM files into a single output file."
  echo "2. --create_color_relief <region>: Creates a color relief image from a DEM file using a specified color ramp."
  echo "3. --create_hillshade <region>: Generates a hillshade image from a DEM file with specified hillshade parameters."
  echo "4. --merge_hillshade <region>: Merges a color relief image and a hillshade image into a single relief image."
  echo "5. --doc: Generates documentation in docs/source/color_relief.rst"
  exit $ERROR_HELP
}
##
## Function: init():
##
##    Initializes essential variables for the region and layer.
##    Verifies the config file exists and key utilities are available (yq, gdal)
##    Sets quiet mode, file ending, and dem_file name
##      Args:
##        $1:
##          Region
##        $2:
##          Layer
##        $3:
##          Blank or "preview" to indicate preview generation or full file generation
##
init() {
  set -e
  # Verify these commands are available
  check_command "gdaldem" $ERROR_MISSING_UTILITY
  check_command "yq" $ERROR_MISSING_UTILITY
  check_command "bc" $ERROR_MISSING_UTILITY

  # Store the  working directory
  original_dir=$(pwd)

  # Set key variables from parameters
  region=$1
  layer=$2
  config="$(pwd)/${region}_relief.cfg"

  # Verify the config file exists
  if [ ! -f "$config" ]; then
    echo "Error: Configuration file not found: $config ❌" >&2
    exit $ERROR_CONFIG_NOT_FOUND
  fi

  # Set file suffix based on "preview" and set quiet flag
  if [ "$3" = "preview" ]; then
    suffix="_prv"
    quiet="-q"
  else
    suffix=""
    quiet=$(optional_flag "$config" "QUIET")
  fi

  # Some GDAL tools use a long version of the quiet switch
  long_quiet=""
  if [ "$quiet" = "-q" ]; then
    long_quiet="--quiet"
  fi

  # Set file ending and dem_file name
  ending="tif"
  dem_file="${region}_${layer}_DEM${suffix}.${ending}"

  gdaldem_flags=$(get_flags  "$config" "OUTPUT_TYPE" "EDGE")

  # Start timing
  SECONDS=0
  echo >&2
}
##
## Function: finished():
##
## Called after function finished. If TIMING is enabled, displays
## elapsed time since the script started.
##  Args:
##    $1:
##        File name of the created target
##
finished() {
  timing=$(optional_flag "$config" "TIMING")
  if [ "$timing" = "on" ]; then
    # Calculate and display elapsed time
    echo "    Elapsed time: $SECONDS seconds"
  fi
}


## Function: check_command():
##
## Verifies if a required command is available in the environment.
## Exit script with error if the command is not found.
##  Args:
##    $1:
##        Command name to check
##
check_command() {
  if ! command -v "$1" > /dev/null 2>&1; then
    echo "Error: '$1' utility not found. ❌" >&2
    current_shell=$(ps -p $$ -o comm=)
    echo "The shell is: $current_shell" >&2
    exit $2
  fi
}


## Function: optional_flag
## Retrieve an optional flag from the YAML configuration file.
##  Args:
##   $1: Configuration file path
##   $2: Key to search for in the YAML file
##
optional_flag() {
  # Check if exactly 2 parameters are provided
  if [ "$#" -ne 2 ]; then
    echo "Error: optional_flag: " >&2
    echo "Error: 2 parameters required, but $# provided: $*" >&2

    exit $ERROR_OPTIONAL_FLAG_ERROR
  fi

  config="$1"
  key="$2"
  yml_value=""

  # Run yq to extract YML key/value from config file
  yml_value=$(eval "yq \".${key}\" \"$config\"")

  # Remove enclosing quotation marks if present
  yml_value=$(echo "$yml_value" | sed 's/^["'\''\(]//;s/["'\''\)]$//')

  # If the result is null, set it to an empty string
  [ "$yml_value" = "null" ] && yml_value=""

  # Output the value to the command
  echo "$yml_value"
}


## Function: mandatory_flag
## Retrieves a mandatory flag from the YAML configuration file.
## Exits with an error if the key is not found.
##  Args:
##   $1: Configuration file path
##   $2: Key to search for in the YAML file
##
mandatory_flag() {
  config="$1"
  key="$2"

  # Use optional_flag to retrieve the value
  flags=$(optional_flag "$config" "$key")

  # Check if flags are empty and output the error message
  if [ -z "$flags" ]; then
    echo "Error: '$key' not found for layer '$layer' in config '$config' ❌" >&2
    exit $ERROR_MANDATORY_FLAG_NOT_FOUND
  fi

  # Output flags (quoted) to ensure proper handling of spaces
  echo "$flags"
}


## Function: get_flags
## Retrieves multiple flags from the YAML configuration file.
##  Args:
##   $1:
##      Region name
##   $2:
##      Configuration file path
##   $3:
##      List of keys to search for in the YAML file
##
get_flags() {
  config="$1"
  shift 1  # Shift the first argument off the list (config)
  flags=""

  for key in "$@"; do
    flag_value=$(optional_flag  "$config" "$key")

    flags="$flags $flag_value"
  done

  # Output flags to command
  echo "$flags"
}


## Function: verify_files
## Verifies that each file passed exists.
## If any file is missing exit with an error.
## Args:
##   $@ (variable): List of file paths to check for existence
##
verify_files() {
  for file in "$@"; do
    [ ! -f "$file" ] && { echo "Error: File not found: $file ❌" >&2; exit $ERROR_FILE_NOT_FOUND; }
  done
  # Return success
  return 0
}

## Function: run_gdal_calc
## Runs gdal_calc.py to merge bands from two files using a calculation specified in the YAML config.
## Args:
##   $1: Band number to merge
##   $2: Target output file
## Shell variables:
##   merge_calc: Calculation for merging A and B bands
##   merge_flags: Flags for running gdal_calc
##   color_file: RGB color relief file
##   hillshade_file: Grayscale Hillshade
##
run_gdal_calc() {
  band="$1"
  targ="$2"
  rm -f "$targ"  # Fix target filename typo

  # Construct the gdal_calc.py command
  cmd="gdal_calc.py -A \"$color_file\" -B \"$hillshade_file\" --A_band=\"$band\" --B_band=1 $merge_calc $merge_flags \"$long_quiet\" --overwrite --outfile=\"$targ\""

  # Log the command (just need it once for band 1)
  if [ "$band" -eq 1 ]; then
    echo >&2
    echo "$cmd" >&2
    echo >&2
  fi

  # Preprocess $merge_calc: Remove '--calc=' prefix so we can quote the calc expression, otherwise
  # the shell will expand items like * in the expression
  calc_expression="${merge_calc#--calc=}"  # Strip the '--calc=' prefix

  # Execute gdal_calc.py
  gdal_calc.py -A "$color_file" -B "$hillshade_file" --A_band="$band" --B_band=1 --calc="$calc_expression" $merge_flags $long_quiet --overwrite --outfile="$targ" || {
    echo "Error: gdal_calc.py execution failed." >&2
    exit $ERROR_GDAL_CALC_FAILED
  }
}

## Function: set_crs
## Applies CRS to the input file if provided. If no WARP flags exist, the input file is
## renamed to the target.
## Args:
##   $1: Input file path
##   $2: Target file path
## YML Config Settings:
##   WARP1 through WARP4 - used for gdalwarp switches
##
set_crs() {
  input_file="$1"
  targ="$2"
  rm -f "${targ}"

  echo "set crs" $1 $2
  echo $config

  # Get GDAL switches from YML config
  warp_flags=$(get_flags  "$config" "WARP1" "WARP2" "WARP3" "WARP4")
  echo "= Set CRS =" >&2

  if [ -z "$warp_flags" ]; then
    echo "No CRS flags provided. Renaming $input_file to $targ" >&2
    if ! mv "$input_file" "$targ"; then
      echo "Error: Renaming failed. ❌" >&2
      exit $ERROR_RENAMING_FAILED
    fi
  else
    echo "gdalwarp $warp_flags $quiet  $input_file $targ" >&2
    ls $input_file
    echo >&2
    if ! gdalwarp $warp_flags $quiet  "$input_file" "$targ"; then
      echo "Error: gdalwarp failed. ❌" >&2
      exit $ERROR_GDALWARP_FAILED
    fi
  fi
}


## Function: create_preview_dem
## Creates a smaller DEM file as a preview image. The Preview location
## is controlled by x_shift, y_shift
## Args:
##   $1: Input file path (DEM)
##   $2: Target output file path for preview DEM
## YML Config Settings:
##   X_SHIFT - 0 is left, 0.5 is middle, 1 is right
##   Y_SHIFT - 0 is top, 0.5 is middle, 1 is bottom
##   PREVIEW - pixel size of preview DEM.  Default is 1000
##
create_preview_dem() {
  input_file="$1"
  targ="$2"

  # Retrieve preview size from config
  preview_size=$(optional_flag "$config" "PREVIEW")

  # Retrieve x_shift and y_shift.  Determines where preview is sliced from
  x_shift=$(optional_flag "$config" "X_SHIFT")
  y_shift=$(optional_flag "$config" "Y_SHIFT")

  # Default to 0 if x_shift or y_shift is empty
  x_shift=${x_shift:-0}
  y_shift=${y_shift:-0}

  # Validate x_shift and y_shift are >= 0 and <= 1
  if [ "$(echo "$x_shift < 0 || $x_shift > 1" | bc)" -eq 1 ] || \
     [ "$(echo "$y_shift < 0 || $y_shift > 1" | bc)" -eq 1 ] || [ -z "$x_shift" ]; then
    echo "ERROR: x_shift and y_shift must be >=0  and <= 1." >&2
    exit "$ERROR_INVALID_PREVIEW_SHIFT"
  fi

  # Use default if preview_size is not defined
  if [ -z "$preview_size" ] || [ "$preview_size" -eq 0 ]; then
     preview_size=1000
  fi

  # Get the image dimensions using gdalinfo
  dimensions=$(gdalinfo "$input_file" | grep "Size is" | awk '{print $3, $4}')
  width=$(echo "$dimensions" | awk -F',' '{print $1}')
  height=$(echo "$dimensions" | awk -F',' '{print $2}')

  # Validate preview size against image dimensions
  if [ "$width" -le "$preview_size" ] || [ "$height" -le "$preview_size" ]; then
    echo "ERROR: Preview size exceeds image dimensions." >&2
    exit "$ERROR_PREVIEW_SIZE"
  fi

  echo "Selecting preview section from ${input_file}" >&2
  echo >&2

  # Calculate the offsets for preview (use bc for float support)
  x_offset=$(printf "%.0f" "$(echo "($width - $preview_size) * $x_shift" | bc)")
  y_offset=$(printf "%.0f" "$(echo "($height - $preview_size) * $y_shift" | bc)")

  # Create the preview using gdal_translate
  echo gdal_translate $quiet -srcwin "$x_offset" "$y_offset" "$preview_size" "$preview_size" "$input_file" "$targ" >&2
  gdal_translate $quiet -srcwin "$x_offset" "$y_offset" "$preview_size" "$preview_size" "$input_file" "$targ"
}


# MAIN FUNCTIONS
#
## --init_DEM - Create a merged DEM file and a truncated DEM preview file.  Optionally set CRS
##              $1 is region name
##              $2 is layer name
## YML Config Settings:
##   LAYER - The active layer_id (A-G).  (Different from layer name)
##   FILES.layer_id - The file names for the active layer
##
init_dem() {
  init "$@"
  echo "= Create DEM file =" >&2

  # Get GDAL switches from YML config
  vrt_flag=$(optional_flag   "$config" "VRT")

  # Get file list for DEM files.  layer_id is (A-G) not the layer text name
  layer_id=$(mandatory_flag  "$config" "LAYER")
  file_list=$(optional_flag  "$config" FILES."$layer_id")

  # Check if flags are empty and output error message
  if [ -z "$file_list" ]; then
    echo >&2
    echo "Error: No elevation files configured for layer '$layer' ❌" >&2
    echo >&2
    exit $ERROR_MISSING_FILE_PATTERN
  fi

# Get folder for elevation DEM files
dem_folder=$(mandatory_flag "$config" "DEM_FOLDER")

# Change to the dem_folder
cd "$dem_folder" || {
  echo "Error: Failed to change to directory $dem_folder" >&2
  exit 1
}

# Temp vrt file
vrt_temp="${region}_tmp1.vrt"

# Remove old temp file
rm -f "$vrt_temp"

# Create DEM VRT
echo gdalbuildvrt $quiet $vrt_flag "$vrt_temp" $file_list >&2
if ! eval gdalbuildvrt $quiet $vrt_flag "$vrt_temp" $file_list; then
  echo "gdalbuildvrt error ❌" >&2
  exit $ERROR_GDALBUILDVRT
fi

  # Set CRS if CRS flags are provided, otherwise just rename
  set_crs "${vrt_temp}" "../${dem_file}"

  # Clean up temp file
  rm "${vrt_temp}"

  # Change back to the original directory if needed
  cd "$original_dir" || {
  echo "Error: Failed to change back to original directory $original_dir" >&2
  exit 1
}

finished "$dem_file"
}


## --preview_dem -  Create a truncated DEM file to build fast previews
##              $1 is region name $2 is layer name $3 preview
##
preview_dem() {
  init "$@"
  verify_files "${dem_file}"

  target="${region}_${layer}_DEM_prv.${ending}"
  rm -f "${target}"

  create_preview_dem "${dem_file}" "${target}"
  finished "target"
}


## --create_color_relief -  gdaldem color-relief
##              $1 is region name $2 is layer name $3 preview flag
## YML Config Settings:
##   OUTPUT_TYPE  -of GTiff
##   EDGE -compute_edges
##
create_color_relief() {
  init "$@"
  echo "= Create Color Relief =" >&2

  target="${region}_${layer}_color${suffix}.${ending}"
  rm -f "${target}"

  verify_files "${dem_file}" "${region}_color_ramp.txt"

  # Build the gdaldem color-relief command
  color_flags=$(get_flags "$config" "COLOR1" "COLOR2" )
  cmd="gdaldem color-relief $gdaldem_flags $color_flags $quiet \"$dem_file\" \"${region}_color_ramp.txt\" \"$target\""
  echo "$cmd"  >&2
  echo >&2

  # Execute the command
  if ! eval "$cmd"; then
      echo "Error: gdaldem color-relief failed. ❌" >&2
      exit $ERROR_GDAL_COLOR_RELIEF_FAILED
  fi

  finished "$target"
}


## --hillshade -  gdaldem hillshade
##              $1 is region name $2 is layer name $3 preview
## YML Config Settings:
##   OUTPUT_TYPE  -of GTiff
##   HILLSHADE1-5 gdaldem hillshade hillshade flags
##
create_hillshade() {
  init "$@"
  echo "= Create Hillshade =" >&2

  target="${region}_${layer}_hillshade${suffix}.${ending}"
  rm -f "${target}"

  verify_files "${dem_file}"

  # Build the gdaldem hillshade command
  hillshade_flags=$(get_flags "$config" "HILLSHADE1" "HILLSHADE2" "HILLSHADE3" "HILLSHADE4" )
  cmd="gdaldem hillshade $gdaldem_flags $hillshade_flags $quiet \"$dem_file\" \"$target\""
  echo "$cmd"  >&2
  echo >&2

  # Execute the command
  if ! eval "$cmd"; then
      echo "Error: gdaldem hillshade failed. ❌" >&2
      exit $ERROR_GDAL_MERGE_FAILED
  fi

  finished "$target"
}

## --merge - merge hillshade with color relief
##              $1 is region name $2 is layer name $3 preview
## YML Config Settings:
##   MERGE1-4 - gdal_calc.py flags
##   COMPRESS - compression type.  --co=COMPRESS=ZSTD
##   MERGE_CALC - calculation to run in gdal_calc.py
##
merge_hillshade() {
  init "$@"
  echo "= Merge Hillshade and Color Relief =" >&2

  # Get GDAL switches from YML config
  merge_flags=$(get_flags "$config" "MERGE1" "MERGE2" "MERGE3" "MERGE4")
  compress=$(get_flags "$config" "COMPRESS")

  target="${region}_${layer}_relief${suffix}.${ending}"
  color_file="${region}_${layer}_color${suffix}.${ending}"
  hillshade_file="${region}_${layer}_hillshade${suffix}.${ending}"

  merge_calc=$(mandatory_flag "$config" "MERGE_CALC")
  verify_files "$color_file" "$hillshade_file"

  rm -f "${target}"

  rgb_bands=""
  pids=""

  # Run gdal_calc for each band in parallel, track RGB file names
  for band in 1 2 3; do
    run_gdal_calc "$band" "rgb_$band.$ending" &
    pids="$pids $!" # Append process ID to the string
    rgb_bands="$rgb_bands rgb_$band.$ending"
  done

  # Wait for all gdal_calc bands to finish and check for errors
  for pid in $pids; do
    if ! wait "$pid"; then
      echo "Error: run_gdal_calc failed for one or more bands. ❌" >&2
      exit $ERROR_GDAL_CALC_FAILED
    fi
  done

  # Merge R, G, and B bands back together
  cmd="gdal_merge.py $quiet $compress -separate -o \"$target\" $rgb_bands"
  echo "$cmd" >&2
  echo >&2

  # Execute the command
  if ! eval "$cmd"; then
    echo "Error: gdal_merge.py failed. ❌" >&2
    exit $ERROR_GDAL_MERGE_FAILED
  fi

  echo >&2
  if [ "$quiet" != "-q" ]; then
    echo "color_relief.sh $version" >&2
  fi

  rm -f $rgb_bands
  finished "$target"
}


## --dem_trigger - create dem_trigger file if it doesnt exist
##              $1 is region name $2 is layer name $3 preview
##
dem_trigger(){
  init "$@"

  dem_trigger="${region}_${layer}_DEM_trigger.cfg"

  # If DEM trigger file doesn't exist, create it
  if [ ! -f "$dem_trigger" ]; then
    touch "$dem_trigger"
  fi
}

## --doc - create rst documentation for this shell script
##
doc(){
  echo "Creating Documentation in docs/source/color_relief.rst"
  # Validate that script and folder exists
  if [ ! -f color_relief.sh ]; then
    pwd
    echo "You must be in source root directory that contains scripts folder"
    exit
  fi
 # Process the documentation, applying required transformations
  grep '^##' color_relief.sh | sed -e 's/^## //' \
                                   -e 's/^##//' \
                                   -e 's/^Function:/def /'  > ../docs/source/color_relief.rst
}


# LAUNCH THE SPECIFIED COMMAND
case "$1" in
  --create_color_relief)
    command="create_color_relief"
    ;;
  --create_hillshade)
    command="create_hillshade"
    ;;
  --preview_dem)
    command="preview_dem"
    ;;
  --merge_hillshade)
    command="merge_hillshade"
    ;;
  --init_dem)
    command="init_dem"
    ;;
  --doc)
    command="doc"
    ;;
  --dem_trigger)
    command="dem_trigger"
    ;;
  *)
    display_help
    exit 100
    ;;
esac

# Shift the positional parameters and call the corresponding function
version="0.1.10"
shift
$command "$@"

## YAML File:
## ----------
## The YAML file contains the values for the GDAL switches.
## These are mapped to shell script variables as below:
##
## - $vrt_flag=
## VRT: -strict
##
## - $warp_flags=
## WARP1: -t_srs epsg:3857
## WARP2: -wo INIT_DEST=NO_DATA  -overwrite
## WARP3: -r bilinear
## WARP4: -multi -wo NUM_THREADS=val/ALL_CPUS --config GDAL_CACHEMAX 30%
##
## - $gdaldem_flags=
## OUTPUT_TYPE:
## EDGE: -compute_edges
##
## - $hillshade_flags=
## HILLSHADE1: -alg ZevenbergenThorne
## HILLSHADE2: -z  2
## HILLSHADE3: ''
## HILLSHADE4: ‘’
##
## - $merge_flags=
## MERGE1: --extent=intersect —type=Byte
##
## - $merge_calc=
## MERGE_CALC: --calc=(A/255.0) * B
##
## - $compress=
## COMPRESS: -co COMPRESS=JPEG
##