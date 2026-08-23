#!/bin/sh

#
# Copyright (c) 2025. Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
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
ERROR_INVALID_PREVIEW_SHIFT=114
ERROR_GDALBUILDVRT=115
ERROR_GDAL_CONTOUR_FAILED=116

# Define color codes
YELLOW="\033[33m"
RESET="\033[0m"

## color_relief.sh
## =========================
## A shell script for processing Digital Elevation Model (DEM) files using GDAL utilities.
## GDAL switches are configured via a YAML file, `${region}_relief.cfg`.
##
## .. note::
##
##    "init_dem" must be run once before any other commands.
##
## Command Line Options
## --------------------
##
##   - **\--init_dem** - Merges multiple DEM files into a single DEM file.
##   - **\--create_color_relief** - Generates a color relief image from a DEM file and color ramp.
##   - **\--create_hillshade** - Produces a hillshade image from a DEM file.
##   - **\--create_slope** - Produces a slope image from a DEM file.
##   - **\--merge_hillshade** - Merges color relief and hillshade images into a single image.
##   - **\--preview_dem** - Extracts a small section from the merged DEM file for preview generation.
##   - **\--create_contour** - Creates a contour shapefile
##   - **\--create_trigger** - Creates a trigger file for granular makefile dependency checking
##   - **\--doc** - Generates RST documentation from script comments starting with `##`.
##
## File Naming
## -----------
##   - **ending** - defaults to "tif"
##   - **suffix** - "_prv" or blank depending on preview mode
##   - **dem_file** - "${region}_${layer}_DEM${suffix}.${ending}"
##   - **color_relief** - "${region}_${layer}_color${suffix}.${ending}"
##   - **hillshade** - "${region}_${layer}$_hillshade${suffix}.${ending}"
##   - **slope** - "${region}_${layer}$_slope${suffix}.${ending}"
##   - **final** - "${region}_${layer}$_relief${suffix}.${ending}"
##   - **config** - "${region}_relief.cfg"
##
## GDAL Commands and Parameters
## ----------------------------
##   - **gdalbuildvrt**  - $vrt_flag "$target" $file_list
##   - **gdalwarp** - $warp_flags "$input_file" "$target"
##   - **gdaldem color-relief** - $gdaldem_flags "$dem_file" "${region}_color_ramp.txt" “$target"
##   - **gdaldem hillshade** - $gdaldem_flags $hillshade_flags $quiet "$dem_file" “$target"
##   - **gdal_calc.py** - -A "$color_file" -B "$hillshade_file" --A_band="$band" —B_band=1 --calc=“$merge_calc" $merge_flags --overwrite —outfile="$target"
##   - **gdal_merge.py** - $compress -separate -o "$target" $rgb_bands
##
## YAML Items
## ----------
## Shell script variables are mapped to YAML items as follows:
##
##   - **$vrt_flag** = VRT
##   - **$warp_flags** = WARP1 - WARP4
##   - **$gdaldem_flags** = OUTPUT_TYPE, EDGE
##   - **$hillshade_flags** = HILLSHADE1 - HILLSHADE4
##   - **$slope_flags** = SLOPE1
##   - **$merge_flags** = MERGE1
##   - **$merge_calc** = MERGE_CALC
##   - **$compress** = COMPRESS
##
##
## Utility Functions
## -----------------
##
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
## .. function::  init():
##
##    Initializes essential variables for the region and layer including:
##    region, layer, layer_id, quiet mode, config, file ending, dem_file name, gdaldem_flags
##    Verifies the config file exists and key utilities are available (yq, bc, gdal)
##
##    **Arguments:**
##      - $1: Region
##      - $2: Layer
##      - $3: Blank or "preview" to indicate preview generation or full file generation
##
init() {
  set -e
  # Check that these commands are available
  verify_command "gdaldem" $ERROR_MISSING_UTILITY
  verify_command "yq" $ERROR_MISSING_UTILITY
  verify_command "bc" $ERROR_MISSING_UTILITY

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

  # Get Layer Id (A,B,C, etc)
  layer_id=$(mandatory_flag  "LAYER")

  # Set quiet flag and file suffix based on "preview"
  if [ "$3" = "preview" ]; then
    suffix="_prv"
    quiet="-q"
  else
    suffix=""
    quiet=$(optional_flag  "QUIET")
  fi

  if [ "$quiet" = "-v" ]; then
    quiet=""
  fi

  # Some GDAL tools use a long version of the quiet switch
  long_quiet=""
  if [ "$quiet" = "-q" ]; then
    long_quiet="--quiet"
  fi

  # Set file ending and DEM (Digital Elevation) file name
  ending="tif"
  dem_file="${region}_${layer}_DEM${suffix}.${ending}"

  gdaldem_flags=$(get_flags  "OUTPUT_TYPE" "EDGE")

  # Start timing
  SECONDS=0
  echo >&2
}

#
# .. function::  finished():
#
# If TIMING is enabled, displays
# elapsed time since the script started.
#
# **Arguments:**
#    - $1: File name of the created target
#
finished() {
  timing=$(optional_flag "TIMING")
  if [ "$timing" = "on" ]; then
    # Calculate and display elapsed time
    echo "    Elapsed time: $SECONDS seconds"
  fi
}

echo_error() {
  printf "color_relief.sh - ${YELLOW}ERROR: %s${RESET}\n" "$1" >&2
}


## .. function::  optional_flag():
##
## Retrieve an optional flag from the YAML configuration file. Echoes the value.
##
## **Arguments:**
##    - $1: Key to search for in the $config YAML file
##
optional_flag() {
  echo "Error: optional_flag: " >&2
  # Check if exactly 1 parameters are provided
  if [ "$#" -ne 1 ]; then
    echo "Error: optional_flag: " >&2
    echo "Error: 1 parameters required, but $# provided: $*" >&2
    exit $ERROR_OPTIONAL_FLAG_ERROR
  fi

  key="$1"
  yml_value=""

  # Run yq to extract YML key/value from config file
  yml_value=$(eval "yq \".${key}\" \"$config\"")

  # Remove enclosing quotation marks if present, but leave parentheses untouched
  yml_value=$(echo "$yml_value" | sed 's/^["'\''"]*//;s/["'\''"]*$//')

  # If the result is null, set it to an empty string
  [ "$yml_value" = "null" ] && yml_value=""

  # Output the value to the command
  echo "$yml_value"
}

## .. function::  mandatory_flag():
##
## Retrieve a mandatory flag from the YAML configuration file.  Echoes the value.
## Exits with an error if the key is not found.
##
## **Arguments:**
##    - $1: Key to search for in the $config YAML file
##
mandatory_flag() {
  key="$1"

  # Call optional_flag to retrieve the value
  flags=$(optional_flag  "$key")

  # If flags are empty  output  error message
  if [ -z "$flags" ]; then
    echo_error "'$key' not found for layer '$layer' in config '$config' ❌" >&2
    exit $ERROR_MANDATORY_FLAG_NOT_FOUND
  fi

  # Output flags (quoted) to ensure proper handling of spaces
  echo "$flags"
}


## .. function::  get_flags():
##
## Retrieves multiple flags from the YAML configuration file and returns concatenation
##
## **Arguments:**
##    - $1: List of keys to search for in the $config YAML file
##
get_flags() {
  flags=""

  for key in "$@"; do
    flag_value=$(optional_flag  "$key")
    flags="$flags $flag_value"
  done

  # Output flags to command
  echo "$flags"
}


## .. function::  verify_files():
##
## Verifies that each file in parameters exists.
## If any file is missing, exits with an error.
##
## **Arguments:**
##    - $1, $2, $3: List of file paths to check for existence
##
verify_files() {
  for file in "$@"; do
    [ ! -f "$file" ] && { echo_error "File not found: $file ❌" >&2; exit $ERROR_FILE_NOT_FOUND; }
  done
  # Return success
  return 0
}

##
## .. function::  verify_command():
##
## Verifies if a required command is available in the environment.
## Exits with error if the command is not found.
##
## **Arguments:**
##    - $1: Command name to check
##
verify_command() {
  if ! command -v "$1" > /dev/null 2>&1; then
    echo_error "'$1' utility not found. ❌" >&2
    current_shell=$(ps -p $$ -o comm=)
    echo "The shell is: $current_shell" >&2
    exit $2
  fi
}

## .. function::  set_crs():
##
## Applies CRS to the input file if provided. If no WARP flags exist, the input file is
## renamed to the target.
##
## **Arguments:**
##    - $1: Input file path
##    - $2: Target file path
##
## **YML Config Settings:**
##   - WARP1 through WARP4 - used for gdalwarp switches
##
set_crs() {
  input_file="$1"
  targ="$2"
  rm -f "${targ}"

  echo "set crs" $1 $2
  echo $config

  # Get gdalwarp switches from YML config
  warp_flags=$(get_flags  "WARP1" "WARP2" "WARP3" "WARP4")
  echo "= Set CRS =" >&2

  # Get optional Extent switch
  extent_flag=$(optional_flag   EXTENT."$layer_id")

  if [ -z "$warp_flags" ]; then
    echo "No CRS flags provided. Renaming $input_file to $targ" >&2
    if ! mv "$input_file" "$targ"; then
      echo_error "Renaming failed. ❌" >&2
      exit $ERROR_RENAMING_FAILED
    fi
  else
    echo "gdalwarp $warp_flags $extent_flag $quiet  $input_file $targ" >&2
    ls $input_file
    echo >&2
    if ! gdalwarp $warp_flags $extent_flag $quiet  "$input_file" "$targ"; then
      echo_error "gdalwarp failed. ❌" >&2
      exit $ERROR_GDALWARP_FAILED
    fi
  fi
}

## .. function::  adjust_brightness():
##
## Adjusts the brightness of an image
##
## Variables:
##   - $brightness: between .7 and 1.5.  Higher is brighter.  1 is no change
##   - $target: image file to adjust
##
adjust_brightness() {
  echo "= Adjust Brightness =" >&2
  brightness=$(get_flags  BRIGHTNESS."$layer_id" )
  echo $brightness
  bright_flag="uint8(clip(((A / 255.) * $brightness) * 255, 1, 254))"
  bright_calc="$bright_flag"  # Assign the final calculation string

  if [ -n "$brightness" ] && [ "$(echo "$brightness != 1" | bc)" -eq 1 ]; then
    echo "Adjust brightness to $brightness for $target..." >&2

    brightness_temp="${target%.tif}_brightness.tif"  # Temporary file for brightness adjustment
    echo gdal_calc.py -A "$target" --outfile="$brightness_temp" $long_quiet --calc="$bright_calc" >&2

    gdal_calc.py -A "$target" --outfile="$brightness_temp" $long_quiet --calc="$bright_calc" --type=Byte --overwrite
    # Rename brightness-adjusted file back to the target
    mv "$brightness_temp" "$target"
  fi
}

## .. function::  create_preview_dem():
##
## Extracts a smaller DEM file from input file for preview images. The Preview location
## is controlled by x_shift, y_shift
##
## **Arguments:**
##    - $1: Input file path (DEM)
##    - $2: Target output file path for preview DEM
##
## **YML Config Settings:**
##   - X_SHIFT - 0 is left, 0.5 is middle, 1 is right
##   - Y_SHIFT - 0 is top, 0.5 is middle, 1 is bottom
##   - PREVIEW - pixel size of preview DEM.  Default is 1000
##
create_preview_dem() {
  input_file="$1"
  targ="$2"

  # Retrieve preview size from config
  preview_size=$(optional_flag  "PREVIEW")

  # Retrieve x_shift and y_shift.  Determines where preview is sliced from
  x_shift=$(optional_flag  "X_SHIFT")
  y_shift=$(optional_flag  "Y_SHIFT")

  # Default to 0 if x_shift or y_shift is empty
  x_shift=${x_shift:-0}
  y_shift=${y_shift:-0}

  # Validate x_shift and y_shift are >= 0 and <= 1
  if [ "$(echo "$x_shift < 0 || $x_shift > 1" | bc)" -eq 1 ] || \
     [ "$(echo "$y_shift < 0 || $y_shift > 1" | bc)" -eq 1 ] || [ -z "$x_shift" ]; then
    echo_error "x_shift and y_shift must be >=0  and <= 1." >&2
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
    echo_error "Preview size exceeds image dimensions." >&2
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


## .. function::  format_creation_option():
##
## Different GDAL commands use different syntax for the creation option switch (-co vs --co)
## This creates the appropriate syntax for gdaldem and gdal_calc.
## Echoes the reformatted switch
##
## **Arguments:**
##    - $1: the gdal tool to be used
##    - $2: the original creation option(s) which should be in the format "-co xxx <-co xxx>"
##
format_creation_option() {
  local tool=$1
  local compress=$2

  # If no compression is specified or if suffix is "_prv" (preview), return empty
  if [ -z "$compress" ] || [ "$suffix" = "_prv" ]; then
    echo ""
    return
  fi

  # Format the creation option flag based on the tool
  case $tool in
    gdaldem)
      # Replace all occurrences of -co with -co (ensuring proper spacing)
      echo "${compress}"
      ;;
    gdal_calc.py)
      # Replace each "-co " with "--co=" to handle multiple occurrences
      formatted=$(echo "$compress" | sed 's/-co /--co=/g')
      echo "$formatted"
      ;;
    *)
      echo "Error: Unknown tool '$tool' for compression flag formatting." >&2
      exit 1
      ;;
  esac
}



## MAIN FUNCTIONS
## --------------
##
## .. function::  init_dem():
##
## *color_relief.sh \--init_dem region layer*
##
## Create a merged DEM file and a truncated DEM preview file.  Optionally set CRS
##
## **Arguments:**
##    - $1: region name
##    - $2: layer name
##
## **YML Config Settings:**
##   - LAYER - The active layer_id (A-G).  (Different from layer name)
##   - FILES.layer_id - The file names for the active layer
##
init_dem() {
  init "$@"
  echo "= Create DEM file =" >&2

  # Get GDAL switches from YML config
  vrt_flag=$(optional_flag    "VRT")
  resample=$(optional_flag    "WARP3")

  # Get file list for DEM files.  layer_id is (A-G) not the layer text name
  file_list=$(optional_flag   FILES."$layer_id")

  # Check if flags are empty and output error message
  if [ -z "$file_list" ]; then
    echo >&2
    echo_error "No elevation files configured for layer '$layer' ❌" >&2
    exit $ERROR_MISSING_FILE_PATTERN
  fi

# Get folder for elevation DEM files
dem_folder=$(mandatory_flag  "DEM_FOLDER")

# Change to the dem_folder
cd "$dem_folder" || {
  echo_error "Unable to change to directory $dem_folder" >&2
  exit 1
}

# Temp vrt file
vrt_temp="${region}_tmp1.vrt"

# Remove old temp file
rm -f "$vrt_temp"

# Create DEM VRT
echo gdalbuildvrt $quiet $vrt_flag $resample "$vrt_temp" $file_list >&2
if ! gdalbuildvrt $quiet $vrt_flag $resample "$vrt_temp" $file_list; then
  echo_error "gdalbuildvrt failed ❌" >&2
  exit $ERROR_GDALBUILDVRT
fi

  # Set CRS if CRS flags are provided, otherwise just rename
  set_crs "${vrt_temp}" "../${dem_file}"

  # Clean up temp file
  rm "${vrt_temp}"

  # Change back to the original directory if needed
  cd "$original_dir" || {
  echo_error "Failed to change back to original directory $original_dir" >&2
  exit 1
}

finished "$dem_file"
}

##
## .. function::  preview_dem():
##
## *color_relief.sh \--preview_dem region layer*
##
## Create a truncated DEM file to build fast previews
##
## **Arguments:**
##    - $1: region name
##    - $2: layer name
##
preview_dem() {
  init "$@"
  verify_files "${dem_file}"

  target="${region}_${layer}_DEM_prv.${ending}"
  rm -f "${target}"

  create_preview_dem "${dem_file}" "${target}"
  finished "target"
}

##
## .. function::  create_hillshade():
##
## *color_relief.sh \--create_hillshade region layer*
##
## Create a hillshade image
##
## **Arguments:**
##    - $1: region name
##    - $2: layer name
##
## **YML Config Settings:**
##   - OUTPUT_TYPE  -of GTiff
##   - HILLSHADE1-5 gdaldem hillshade flags
##
create_hillshade() {
  init "$@"
  echo "= Create Hillshade =" >&2
  compress=$(get_flags  "COMPRESS")

  target="${region}_${layer}_hillshade${suffix}.${ending}"
  rm -f "${target}"

  verify_files "${dem_file}"

  # Format the compression flag for gdaldem
  gdaldem_compress=$(format_creation_option gdaldem "$compress")

  # Build the gdaldem hillshade command
  hillshade_flags=$(get_flags "HILLSHADE1" "HILLSHADE3" "HILLSHADE4" )
  hillz_flag=$(get_flags   HILLSHADEZ."$layer_id")
  cmd="gdaldem hillshade $gdaldem_flags $gdaldem_compress $hillz_flag $hillshade_flags $quiet \"$dem_file\" \"$target\""
  echo "$cmd" >&2
  echo >&2

  # Execute the command
  if ! eval "$cmd"; then
      echo_error "gdaldem hillshade failed. ❌" >&2
      exit $ERROR_GDAL_MERGE_FAILED
  fi

  # If brightness is not 1, then adjust brightness of hillshade
  adjust_brightness

  finished "$target"
}

##
## .. function::  create_contour():
##
## *color_relief.sh \--create_contour region layer*
##
## Create a contour shapefile
##
## **Arguments:**
##    - $1: region name
##    - $2: layer name
##
## **YML Config Settings:**
##   - INTERVAL  -i 20
##
create_contour() {
  init "$@"
  echo "= Create Contour =" >&2

  target="${region}_${layer}_contour.shp"
  rm -f "${target}"

  verify_files "${dem_file}"

  # Build the command
  contour_flags=$(get_flags  "INTERVAL" )
  cmd="gdal_contour -a elev $contour_flags \"$dem_file\" \"$target\" "
  echo "$cmd" >&2
  echo >&2

  # Execute the command
  if ! eval "$cmd"; then
      echo_error "gdal_contour failed. ❌" >&2
      exit $ERROR_GDAL_CONTOUR_FAILED
  fi

  finished "$target"
}


##
## .. function::  create_slope():
##
## *color_relief.sh \--create_slope region layer*
##
## Create a slope image
##
## **Arguments:**
##    - $1: region name
##    - $2: layer name
##
## **YML Config Settings:**
##   - OUTPUT_TYPE  -of GTiff
##   - SLOPE1 gdaldem slope flags
##
create_slope() {
  init "$@"
  echo "= Create Slope =" >&2
  compress=$(get_flags  "COMPRESS")
  slope_min=$(get_flags  "SLOPEMIN")
  slope_max=$(get_flags  "SLOPEMAX")

  target="${region}_${layer}_slope${suffix}.${ending}"
  rm -f "${target}"

  verify_files "${dem_file}"

  # Format the compression flag for gdaldem
  gdaldem_compress=$(format_creation_option gdaldem "$compress")

  # Build the gdaldem slope command
  slope_flags=$(get_flags "SLOPE1" )
  cmd="gdaldem slope $gdaldem_flags  $slope_flags $quiet \"$dem_file\" temp.tif"

  # Execute the command
  echo "$cmd" >&2
  echo >&2
  if ! eval "$cmd"; then
      echo_error "gdaldem slope failed. ❌" >&2
      exit $ERROR_GDAL_MERGE_FAILED
  fi

  #Scale the output
  cmd="gdal_translate -scale $slope_min $slope_max -ot Byte   $quiet temp.tif mask.tif "
  # Execute the command
  echo "$cmd" >&2
  echo >&2
  if ! eval "$cmd"; then
      echo_error "gdal_translate failed. ❌" >&2
      exit $ERROR_GDAL_MERGE_FAILED
  fi

  relief_name="${region}_${layer}_relief${suffix}.${ending}"

  calc=$(get_flags "SLOPECALC" )
  # (1.0 - A/255.0) * B + (A/255.0) * (0.33 * B + 0.33 * C + 0.33 * D)

  echo "gdal_calc.py --outfile=r.tif -A mask.tif -B $relief_name -C $relief_name -D $relief_name"
  echo "$calc"

  # Process Red Channel
gdal_calc.py -A mask.tif -B "$relief_name" -C "$relief_name" -D "$relief_name" \
    --A_band=1 --B_band=1 --C_band=2 --D_band=3 \
    --calc="$calc" \
    --outfile="r.tif" --overwrite

# Process Green Channel
gdal_calc.py -A mask.tif -B "$relief_name" -C "$relief_name" -D "$relief_name" \
    --A_band=1 --B_band=2 --C_band=1 --D_band=3 \
    --calc="$calc" \
    --outfile="g.tif" --overwrite

# Process Blue Channel
gdal_calc.py -A mask.tif -B "$relief_name" -C "$relief_name" -D "$relief_name" \
    --A_band=1 --B_band=3 --C_band=1 --D_band=2 \
    --calc="$calc" \
    --outfile="b.tif" --overwrite

# Merge channels back into a single RGB file
gdal_merge.py -separate -o "$target" r.tif g.tif b.tif

 rm -f temp.tif r.tif g.tif b.tif

finished "$target"
}


##
## .. function::  create_color_relief():
##
## *color_relief.sh \--create_color_relief region layer*
##
## Create a color relief image using gdaldem color-relief
##
## **Arguments:**
##    - $1: region name
##    - $2: layer name
##
## **YML Config Settings:**
##   - OUTPUT_TYPE  -of GTiff
##   - EDGE -compute_edges
##
create_color_relief() {
  init "$@"
  echo "= Create Color Relief =" >&2
  color_flags=$(get_flags  "COLOR1" "COLOR2" )
  compress=$(get_flags  "COMPRESS")

  target="${region}_${layer}_color${suffix}.${ending}"
  rm -f "${target}"

  verify_files "${dem_file}" "${region}_color_ramp.txt"

  # Format the compression flag for gdaldem
  gdaldem_compress=$(format_creation_option gdaldem "$compress")

  # Build the gdaldem color-relief command
  cmd="gdaldem color-relief $gdaldem_flags $color_flags $quiet $gdaldem_compress \"$dem_file\" \"${region}_color_ramp.txt\" \"$target\""
  echo "$cmd"  >&2
  echo >&2

  # Execute the color-relief command
  if ! eval "$cmd"; then
      echo_error "gdaldem color-relief failed. ❌" >&2
      exit $ERROR_GDAL_COLOR_RELIEF_FAILED
  fi

  finished "$target"
}

##
##
## .. function::  merge_hillshade():
##
## *color_relief.sh \--merge_hillshade region layer*
##
## Merge hillshade with color relief
##
## **Arguments:**
##    - $1: region name
##    - $2: layer name
##
## **YML Config Settings:**
##   - MERGE1-4 - gdal_calc.py flags
##   - COMPRESS - compression type.  --co=COMPRESS=ZSTD
##   - MERGE_CALC - calculation to run in gdal_calc.py
##
merge_hillshade() {
  init "$@"
  echo "= Merge Hillshade and Color Relief =" >&2

  target="${region}_${layer}_relief${suffix}.${ending}"
  color_file="${region}_${layer}_color${suffix}.${ending}"
  hillshade_file="${region}_${layer}_hillshade${suffix}.${ending}"

  # Get GDAL switches from YML config
  merge_flags=$(get_flags  "MERGE1" "MERGE2" "MERGE3" "MERGE4")
  compress=$(get_flags  "COMPRESS")

  verify_files "$color_file" "$hillshade_file"
  rm -f "${target}"

  merge_calc=$(mandatory_flag  "MERGE_CALC")

  # Remove '--calc=' prefix in $merge_calc so we can quote the expression
  calc_expression="${merge_calc#--calc=}"  # Strip the '--calc=' prefix

  # Format the compression flag for gdal_calc.py
  gdal_calc_compress=$(format_creation_option gdal_calc.py "$compress")
  cmd="gdal_calc.py -B \"$color_file\" -A \"$hillshade_file\" --allBands=B --calc=\"$calc_expression\" $merge_flags $gdal_calc_compress $long_quiet --overwrite --outfile=\"$target\""

  echo "$cmd" >&2
  echo >&2

  # Execute the command
  if ! eval "$cmd"; then
    echo_error "gdal_calc.py failed. ❌" >&2
    exit $ERROR_GDAL_MERGE_FAILED
  fi

  # Build overviews with gdaladdo
  echo "⏳ Creating overviews with gdaladdo..." >&2
  if ! gdaladdo -r average "$target" 2 4 8 16; then
    echo_error "gdaladdo failed on $target ❌" >&2
    exit $ERROR_GDAL_MERGE_FAILED
  fi

  echo >&2
  if [ "$quiet" != "-q" ]; then
    echo "color_relief.sh $version" >&2
  fi

  finished "$target"
}

##
## .. function::  create_trigger():
##
## *color_relief.sh \--create_trigger region layer*
##
## Create a trigger file for makefile granular dependency checks
##
## **Arguments:**
##    - $1: region name
##    - $2: layer name
##
create_trigger(){
  init "$@"
  trigger_name=$3

  # If  trigger file doesn't exist, create it
  if [ ! -f "$trigger_name" ]; then
    touch "$trigger_name"
  fi
}

##
## .. function::  doc():
##
## *color_relief.sh \--doc*
##
## Create rst documentation for this shell script from comments with ##
##
## **Arguments:**
##    - none
##
doc(){

  # Validate that script and folder exists
  if [ ! -f color_relief.sh ]; then
    pwd
    echo "You must be in the directory that contains the script"
    exit
  fi
 # Process the documentation, applying required transformations
  grep '^##' color_relief.sh | sed -e 's/^## //' \
                                   -e 's/^##//' \
                                   -e 's/^Function:/def /'  > ../docs/source/color_relief.rst
  echo "Created color_relief.rst doc in ../docs/source/"
}


# LAUNCH THE SPECIFIED COMMAND
case "$1" in
  --create_color_relief)
    command="create_color_relief"
    ;;
  --create_hillshade)
    command="create_hillshade"
    ;;
  --create_contour)
    command="create_contour"
    ;;
  --create_slope)
    command="create_slope"
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
  --create_trigger)
    command="create_trigger"
    ;;
  *)
    echo_error "Unknown switch " $1
    display_help
    exit 100
    ;;
esac

# Shift the positional parameters and call the corresponding function
version="0.7"
shift
$command "$@"
