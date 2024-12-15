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

# Function to calculate and print elapsed time
elapsed_time() {
    end_time=$(date +"%s")
    elapsed_time=$((end_time - start_time))
    minutes=$((elapsed_time / 60))
    seconds=$((elapsed_time % 60))
    echo "Elapsed time $minutes minutes and $seconds s."
}

# Function to merge files and clean up
merge_files() {
    local output_file="$prefix"_relief.tif

    local in_file1="$prefix"_cool_relief.tif
    local in_file2="$prefix"_arid_relief.tif
    precip_rgb_file="$prefix"_precip_ext.tif

    echo "Merge $in_file1 $in_file2 into $output_file" using mask $precip_rgb_file

    # Run gdal_calc.py for each band in parallel
    local temp_files=()

    for ((band = 1; band < 4; band++)); do
        run_gdal_calc "$band" "temp_$band.tif" &
        temp_files+=("temp_$band.tif")
    done

    # Wait for all background processes to finish
    wait

    # Merge the separate bands back into a single RGB file
    echo "Merging Bands into $output_file"
    gdal_merge.py -separate -o "$output_file" "${temp_files[@]}" || exit $?

    # Clean up temporary files
    # rm -f "${temp_files[@]}"
}

# Define the --calc argument
calculation1="A.astype(float)*(M.astype(float)+90.0)/345.0  +  B.astype(float)*(1.0 - (M.astype(float)+90.0)/345.0)"
calculation2="A.astype(float)*(M.astype(float))/255.0  +  B.astype(float)*(1.0 - (M.astype(float))/255.0)"

# Function to run gdal_calc.py with status update for specified band
run_gdal_calc() {
    local band="$1"
    local output_file=$2

    gdal_calc.py -A "$in_file1" -B "$in_file2" -M "$precip_rgb_file" \
        --A_band=$band --B_band=$band --M_band=1 \
        --calc="numpy.where(M > 50, $calculation1, $calculation2)" \
        --outfile="$output_file" --extent=intersect --projectionCheck \
        --NoDataValue=0 --co="COMPRESS=DEFLATE" --type=Byte --overwrite || exit $?
}

set -e
echo "------ merge_arid.sh --------------"
pwd

if [ "$#" -ne 1 ]; then
    echo "Error - Usage: merge_arid.sh <region>"
    exit 1
fi
# Read the region prefix from $1
prefix=$1

# Record the start time
start_time=$(date +"%s")

merge_files

elapsed_time

echo "DONE"
