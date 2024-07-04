#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Remove old distribution files
echo "Cleaning up old distribution files..."
rm -rf ColorReliefEditor/dist/*.gz ColorReliefEditor/dist/*non

# Build the package
echo "Building the package..."
python3 -m build

# Upload the package to PyPI
echo "Uploading the package to PyPI..."
python3 -m twine upload dist/*

echo "Deployment complete."