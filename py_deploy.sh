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

# deploy.sh

# This script automates the process of deploying a Python package to PyPI.

# 1. Optionally increments the patch version number in the pyproject.toml file if the --increment switch is present.
# 2. Removes previous build artifacts from the dist directory.
# 3. Builds the package using the build module.
# 4. Uploads the package to PyPI using twine.

# Usage:
# Run the script using: ./deploy.sh [--increment]
#
# Note: This script is intended for macOS.
# For Linux, modify the sed command accordingly.

# Function to increment the patch version number
increment_version() {
    local version=$1
    local base_version=$(echo "$version" | awk -F. '{print $1"."$2}')
    local patch_version=$(echo "$version" | awk -F. '{print $3 + 1}')
    echo "$base_version.$patch_version"
}

# Extract the current version number from pyproject.toml
CURRENT_VERSION=$(grep -E 'version = "[0-9]+\.[0-9]+\.[0-9]+"' pyproject.toml | awk -F\" '{print $2}')

# Increment version number if --increment switch is present
if [ "$1" == "--increment" ]; then
    NEW_VERSION=$(increment_version "$CURRENT_VERSION")
    # Update the version number in pyproject.toml
    sed -i '' "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
else
    NEW_VERSION=$CURRENT_VERSION
fi

echo "Deploying version $NEW_VERSION"

# Remove previous build artifacts
rm -rf dist/*

# Build the package
python3 -m build

# Upload the package to PyPI
python3 -m twine upload dist/*

echo "Deployment complete"
