#!/bin/bash

#
# Copyright (c) 2024. Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
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

# Read the region prefix from the YAML config file using yq
prefix=$(yq eval '.settings.region' config.yml)

source_geotiff="$prefix"_arid_relief.tif
target_geotiff="$prefix"_precip.tif
output_geotiff="$prefix"_precip_ext.tif

pwd
echo Set the extent and dimensions of $target_geotiff to match $source_geotiff and output as $output_geotiff

# Get gdalinfo in JSON format from the source GeoTIFF
gdalinfo_result=$(gdalinfo -json "$source_geotiff")

# Extract coordinates from gdalinfo JSON output using jq
xmin=$(jq -r '.cornerCoordinates.upperLeft[0]' <<< "$gdalinfo_result")
ymax=$(jq -r '.cornerCoordinates.upperLeft[1]' <<< "$gdalinfo_result")

xmax=$(jq -r '.cornerCoordinates.lowerRight[0]' <<< "$gdalinfo_result")
ymin=$(jq -r '.cornerCoordinates.lowerRight[1]' <<< "$gdalinfo_result")

# Extract dimensions from the gdalinfo JSON output using jq
width=$(jq -r '.size[0]' <<< "$gdalinfo_result")
height=$(jq -r '.size[1]' <<< "$gdalinfo_result")

echo Coordinates "$xmin" , "$ymin" , "$xmax" , "$ymax"

# Use gdalwarp to apply settings to the target file
#echo gdalwarp -overwrite  -r lanczos -te "$xmin" "$ymin" "$xmax" "$ymax"  -ts $width $height -of GTiff  "$target_geotiff"  "$output_geotiff"
#gdalwarp -overwrite  -r lanczos -te "$xmin" "$ymin" "$xmax" "$ymax"  -ts $width $height -of GTiff  "$target_geotiff"  "$output_geotiff"
echo NO ACTION ON SET EXTENT
