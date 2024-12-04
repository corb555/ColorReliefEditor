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

if [ "$#" -ne 2 ]; then
    echo "Error - Usage: create_precip_out_file.sh <min value> <max value>"
    exit 1
fi

echo
pwd
# Read the region prefix from the YAML config file using yq
prefix=$(yq eval '.settings.region' config.yml)

precip_file="$prefix"_precip_ext.tif
precip_out_file="$prefix"_precip_rgb.tif

# temp files
precip_byte_file=precip_tmpb.tif
precip_vrt_file=precip_tmpv.vrt

echo Convert grayscale precip file $precip_file to RGB and scale $1 $2 to 0 255
echo Output "$precip_out_file"

# Convert the precipitation file to Byte resources type and rescale it
echo gdal_translate -scale $1 $2 0 255 -ot Byte "$precip_file" "$precip_byte_file"
gdal_translate -scale $1 $2 0 255 -ot Byte "$precip_file" "$precip_byte_file"

# Create a virtual raster with three identical bands from precip grayscale file
gdalbuildvrt -separate "$precip_vrt_file" "$precip_byte_file" "$precip_byte_file" "$precip_byte_file"

# Convert the virtual raster to a real RGB file
gdal_translate -ot Byte -of GTiff -co PHOTOMETRIC=RGB "$precip_vrt_file" "$precip_out_file"
rm "$precip_vrt_file"
rm "$precip_byte_file"
