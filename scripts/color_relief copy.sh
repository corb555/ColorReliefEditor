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

# This script provides utilities to process DEM files with GDAL tools. It uses configuration values from a YML file.
# The main functions allow creating DEM files, generating hillshades, and applying color relief based on a region.
# Run `--help` for more details.

# UTILITY FUNCTIONS used by main functions:

# Function: display_help
# Description: Prints usage information and exits. Lists available operations and their descriptions.
# Parameters: None
display_help() {
  echo "Usage: $0 --create_color_relief <region>  | --create_hillshade <region>  | --merge_hillshade <region>  | --set_crs <region>  | --init_dem <region>"
  echo
  echo "These switches run GDAL utilities using parameters from a YML config file:"
  echo "1. --init_dem <region>: Creates a DEM file by merging multiple DEM files into a single output file."
  echo "2. --create_color_relief <region>: Creates a color relief image from a DEM file using a specified color ramp."
  echo "3. --create_hillshade <region>: Generates a hillshade image from a DEM file with specified hillshade parameters."
  echo "4. --merge_hillshade <region>: Merges a color relief image and a hillshade image into a single relief image."
  exit 1
}

# Function: init
# Description: Initializes essential variables for the region and layer, and verifies the config file exists.
# Parameters:
#   $1: Region name
#   $2: Layer name
#   $3: Blank or "preview" to indicate preview generation
init() {
  set -e
  # Verify these commands are available
  check_command "gdalinfo"
  check_command "yq"

  # Set key variables from parameters
  region=$1
  layer=$2
  if [ "$3" = "preview" ]; then
    suffix="_prv"
  else
    suffix=""
  fi

  config="${region}_relief.cfg"
  dem_file="${region}_${layer}${suffix}_DEM.tif"

  if [ ! -f "$config" ]; then
    echo "Error: Configuration file not found: $config" >&2
    exit 1
  fi
}

# Function: check_command
# Description: Verifies if a required command is available in the environment. Exits the script if the command is not found.
# Parameters:
#   $1: Command name to check (e.g., gdalinfo, yq)
check_command() {
  if ! command -v "$1" > /dev/null 2>&1; then
    echo "Error: '$1' utility not found." >&2
    exit 1
  fi
}

optional_flag() {
  # Check if exactly 3 parameters are provided
  if [ "$#" -ne 3 ]; then
    echo "Error: 3 parameters required, but $# were provided."
    echo "Usage: optional_flag <region> <config> <key>"
    exit 1
  fi

  region="$1"
  config="$2"
  key="$3"

  # Run the yq command and capture the result
  flags=$(eval "yq \".${key}\" \"$config\"")

  # If the result is null, set it to an empty string
  [ "$flags" = "null" ] && flags=""

  # Output the flags
  echo "$flags"
}

# Function: mandatory_flag
# Description: Retrieves a mandatory flag from the YAML configuration file. Exits with an error if the key is not found.
# Parameters:
#   $1: Region name
#   $2: Configuration file path
#   $3: Key to search for in the YAML file
mandatory_flag() {
  region="$1"
  config="$2"
  key="$3"

  flags=$(optional_flag "$region" "$config" "$key")

  # Check if flags are empty and output the error message
  if [ -z "$flags" ]; then
    echo "Error: '$key' flags not found for layer '$layer' in config '$config'" >&2
    exit 1
  fi

  echo "$flags"
}

# Function: get_flags
# Description: Retrieves multiple flags from the YAML configuration file by passing keys as arguments.
# Parameters:
#   $1: Region name
#   $2: Configuration file path
#   $3, ...: List of keys to search for in the YAML file
get_flags() {
  region="$1"
  config="$2"
  shift 2  # Shift the first two arguments off the list (region and config)
  flags=""

  for key in "$@"; do
    flag_value=$(optional_flag "$region" "$config" "$key")
    flags="$flags $flag_value"
  done

  echo "$flags"
}

# Function: verify_files
# Description: Verifies that each file passed as an argument exists. If any file is missing, the script exits with an error.
# Parameters:
#   $@ (variable): List of file paths to check for existence
verify_files() {
  for file in "$@"; do
    [ ! -f "$file" ] && { echo "Error: File not found: $file" >&2; exit 1; }
  done
  echo " "
}

# Function: finished
# Description: Called after successfully creating a file.  Currently does nothing.
# Parameters:
#   $1: File name of the created target
finished() {
  :
}

# Function: run_gdal_calc
# Description: Runs gdal_calc.py to merge bands from two files using a calculation specified in the YAML config.
# Parameters:
#   $1: Band number to merge
#   $2: Target output file
run_gdal_calc() {
  band="$1"
  targ="$2"
  rm -f "$target"
  echo $band $merge_flags

  cmd="gdal_calc.py -A \"$in_file1\" -B \"$in_file2\" --A_band=\"$band\" --B_band=1 --calc=\"$merge_calc\" $merge_flags --overwrite --outfile=\"$targ\""
  echo "$cmd"
  eval "$cmd" || exit $?
}

# Function: set_crs
# Description: Applies CRS flags to the input file if provided. If no CRS flags exist, the input file is renamed to the target.
# Parameters:
#   $1: Input file path
#   $2: Target file path
set_crs() {
  input_file="$1"
  targ="$2"
  rm -f "${targ}"

  warp_flags=$(get_flags "$region" "$config" "WARP1" "WARP2" "WARP3" "WARP4")
  edge=$(get_flags "$region" "$config" "EDGE")
  echo "SET CRS: ${input_file} -> ${targ}"

  if [ -z "$warp_flags" ]; then
    echo "No CRS flags provided. Renaming $input_file to $targ"
    if ! mv "$input_file" "$targ"; then
      echo "Error: Renaming failed." >&2
      exit 1
    fi
  else
    echo "Running gdalwarp $warp_flags $edge -overwrite $input_file $targ"
    if ! gdalwarp $warp_flags -overwrite "$input_file" "$targ"; then
      echo "Error: gdalwarp failed." >&2
      exit 1
    fi
    echo "CRS set successfully: ${targ}"
  fi
}

# Function: create_preview_dem
# Description: Creates a smaller DEM file as a preview image. Extracts a portion of the input file based on the specified location.
# Parameters:
#   $1: Input file path (DEM)
#   $2: Target output file path for preview DEM
create_preview_dem() {
  input_file="$1"
  targ="$2"

  preview_size=$(optional_flag "$region" "$config" "PREVIEW")
  echo "Creating preview of ${input_file}."

  if [ -z "$preview_size" ] || [ "$preview_size" -eq 0 ]; then
    echo "Preview size is 0, skipping preview."
  else
    dimensions=$(gdalinfo "$input_file" | grep "Size is" | awk '{print $3, $4}')
    echo "Dimensions: $dimensions"

    # Extract width and height, removing commas
    width=$(echo "$dimensions" | awk -F', ' '{print $1}') # Use -F to split by ", "
    height=$(echo "$dimensions" | awk -F', ' '{print $2}')

    echo "Height: $height Width: $width"

    # Calculate the offsets
    x_offset=$(( (width - preview_size) / 2 ))
    y_offset=$(( (height - preview_size) / 2 ))

    # Create the preview using gdal_translate
    gdal_translate -srcwin "$x_offset" "$y_offset" "$preview_size" "$preview_size" "$input_file" "$targ"
  fi
}

# MAIN FUNCTIONS - CALLED BASED ON SWITCH

# --init_DEM - Create a merged DEM file and truncate to a DEM preview file.  Optionally set CRS
#              $1 is region name $2 is layer name
init_dem() {
  init "$@"

  # Get file pattern for DEM files
  layer_id=$(mandatory_flag  "$region" "$config" "LAYER")
  pattern=$(optional_flag  "$region" "$config" FILES."$layer_id")

    # Check if flags are empty and output the error message
  if [ -z "$pattern" ]; then
    echo
    echo "Error: Elevation Files is blank for layer '$layer'" >&2
    echo
    exit 1
  fi

  # Targets: DEM file and DEM preview file
  target="${region}_${layer}_DEM.tif"
  temp1=${region}_tmp1.tif

  # Clean up temp files
  rm -f "${temp1}"

  echo "Merge DEM files and set CRS"
  echo "DEM files matching $pattern:"
  ls $pattern

  # Merge DEM files
  echo "gdal_merge.py -o ${temp1} $pattern"
  if ! gdal_merge.py -v -o ${temp1} $pattern; then
      echo "Error: gdal_merge.py failed." >&2
      exit 1
  fi

  # Set CRS if CRS flags are provided, otherwise just rename to dem_file
  set_crs "${temp1}" "${target}"

  # Clean up temp files
  rm "${temp1}"

  finished "$target"
}

# --preview_dem -  Create a truncated DEM file to build fast previews
#              $1 is region name $2 is layer name $3 preview
preview_dem() {
  init "$@"
  dem="${region}_${layer}_DEM.tif"
  verify_files "${dem}"

  target="${region}_${layer}_prv_DEM.tif"
  rm -f "${target}"

  # Create a truncated DEM file to build fast previews
  create_preview_dem "${dem}" "${target}"

  finished "target"
}

# --create_color_relief -  gdaldem color-relief
#              $1 is region name $2 is layer name $3 preview
create_color_relief() {
  init "$@"
  relief_flags=$(get_flags  "$region" "$config" "OUTPUT_TYPE" "EDGE")
    # If the third argument is "preview" then add "-q" to flags to suppress verbose output for preview
  if [ "$3" = "preview" ]; then
    relief_flags="$relief_flags -q"
  fi

  target="${region}_${layer}${suffix}_color.tif"
  rm -f "${target}"

  verify_files "${dem_file}" "${region}_color_ramp.txt"

  # Build the gdaldem color-relief command
  cmd="gdaldem color-relief $relief_flags \"$dem_file\" \"${region}_color_ramp.txt\" \"$target\""
  echo "$cmd"

  # Execute the command
  if ! eval "$cmd"; then
      echo "Error: gdaldem color-relief failed." >&2
      exit 1
  fi

  finished "$target"
}

# --hillshade -  gdaldem hillshade
#              $1 is region name $2 is layer name $3 preview
create_hillshade() {
  init "$@"

  target="${region}_${layer}${suffix}_hillshade.tif"
  rm -f "${target}"

  verify_files "${dem_file}"
  hillshade_flags=$(get_flags "$region" "$config" "OUTPUT_TYPE" "HILLSHADE1" "HILLSHADE2" "HILLSHADE3" "HILLSHADE4" "HILLSHADE5" "EDGE")


  # If the third argument is "-preview" then add "-q" to flags to suppress verbose output for preview
  if [ "$3" = "preview" ]; then
    hillshade_flags="$hillshade_flags -q"
  fi

  # Build the gdaldem hillshade command
  cmd="gdaldem hillshade $hillshade_flags \"$dem_file\" \"$target\""
  echo "$cmd"

  # Execute the command
  if ! eval "$cmd"; then
      echo "Error: gdaldem hillshade failed." >&2
      exit 1
  fi

  finished "$target"
}

# --merge - merge hillshade with color relief
#              $1 is region name $2 is layer name $3 preview
merge_hillshade() {
  init "$@"
  # Get merge flags from YML config
  merge_flags=$(get_flags "$region" "$config" "MERGE1" "MERGE2" "MERGE3" "MERGE4" "COMPRESS")
  target="${region}_${layer}${suffix}_relief.tif"
  in_file1="${region}_${layer}${suffix}_color.tif"
  in_file2="${region}_${layer}${suffix}_hillshade.tif"
  merge_calc=$(mandatory_flag  "$region" "$config" "MERGE_CALC")
  verify_files "$in_file1" "$in_file2"

  rm -f "${target}"

  echo "Merge $in_file1 and $in_file2 into $target for R G and B bands"
  echo

  temp_files=""

  # Run gdal_calc for each band in parallel
  for band in 1 2 3; do
    run_gdal_calc "$band" "temp_$band.tif" &
    temp_files="$temp_files temp_$band.tif"
  done

  # Wait for all gdal_calc processes to finish
  wait

  echo " "
  echo "Merging bands into $target :"
  echo "gdal_merge.py -separate -o $target $temp_files"
  if ! gdal_merge.py -separate -o "$target" $temp_files; then
      echo "Error: gdal_merge.py failed." >&2
      exit 1
  fi

  echo
  echo "color_relief.sh v0.6"
  echo "Removing temp files: $temp_files"
  rm -f $temp_files
  finished "$target"
  echo "     DONE    "
}

# Launch the specified command
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
  *)
    display_help
    exit 1
    ;;
esac

# Shift the positional parameters and call the corresponding function with the remaining arguments
shift
$command "$@"
