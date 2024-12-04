#!/bin/sh
## -
## Makefile for Color Relief Generation using GDAL
## -
## This Makefile automates the process of generating color relief images and hillshade overlays
## for a specified REGION and LAYER. It defines a set of rules for generating Digital Elevation
## Model (DEM) files, color relief images, and hillshades using the `color_relief.sh` script.
## Preview images are also generated for faster inspection. The Makefile supports both
## full-resolution and preview outputs, and includes targets for cleaning up intermediate files.
##
## Required Environment Variables:
##   - REGION: Specifies the region name (e.g., 'ICELAND').
##   - LAYER:  Specifies the data layer (e.g., 'A', 'B').
## -
## Usage Example:
##   make REGION='ICELAND' LAYER='A' all
## -
## Key Targets:
##   - help:       Displays Help text
##   - all:        Generates the final merged color relief image with hillshade.
##   - clean:      Removes intermediate files, keeping the final outputs.
##   - distclean:  Removes all generated files, including previews and final outputs.
##   - info_version: Displays the version of Make and this Makefile
## -
## Config Files:
##   - $(REGION)_relief.cfg: Configuration file for GDAL command parameters
##   - $(REGION)_color_ramp.txt: Color ramp file for `gdaldem` to create color relief images.
## -
## Output Files:
##   - $(REGION)_$(LAYER)_DEM.tif: Digital Elevation Model (DEM) file
##   - $(REGION)_$(LAYER)_color.tif: Color relief image.
##   - $(REGION)_$(LAYER)_hillshade.tif: Hillshade overlay.
##   - $(REGION)_$(LAYER)_relief.tif: Final merged relief image.
##   -
##   - Preview versions of these files are named $(REGION)_$(LAYER)_prv_*.
## -
## color_relief.sh:
##  This is called with:  color_relief.sh --COMMAND $(REGION) $(LAYER) preview

# To generate documentation for this from project root:
#      grep '^##' ColorReliefEditor/resources/Makefile | sed 's/^## //' > docs/source/makefile.rst

MAKEFLAGS += --warn-undefined-variables

# Ensure REGION and LAYER are set, otherwise exit with an error
ifndef REGION
$(error REGION is not set.  Usage: make REGION='ICELAND' LAYER='A'  all)
endif

ifndef LAYER
$(error LAYER is not set.  Usage: make REGION='ICELAND' LAYER='A'  all)
endif

# CONFIG_FILE contains the switches for GDAL commands
CONFIG_FILE = $(REGION)_relief.cfg

# Color ramp file for gdaldem color relief
COLOR_RAMP_FILE = $(REGION)_color_ramp.txt

# Ensure necessary files exist
$(CONFIG_FILE):
	$(error Config file not found: "$@")

$(COLOR_RAMP_FILE):
	$(error Color ramp file not found: "$@")

# Standard file starts with $(REGION)_$(LAYER)
PREFIX = $(REGION)_$(LAYER)

# Targets
DEM_TIF = $(PREFIX)_DEM.tif
COLOR_TIF = $(PREFIX)_color.tif
HILLSHADE_TIF = $(PREFIX)_hillshade.tif
FINAL_TIF = $(PREFIX)_relief.tif

# Targets for preview images
PRV_DEM_TIF = $(PREFIX)_DEM_prv.tif
PRV_COLOR_TIF = $(PREFIX)_color_prv.tif
PRV_HILLSHADE_TIF = $(PREFIX)_hillshade_prv.tif
PRV_FINAL_TIF = $(PREFIX)_relief_prv.tif
# Empty file used to trigger DEM rebuilds
DEM_TRIGGER = $(PREFIX)_DEM_trigger.cfg

# Phony targets
.PHONY: all clean distclean help

# Default target
all: $(FINAL_TIF)

# Create the DEM trigger if missing
$(DEM_TRIGGER):
	color_relief.sh --dem_trigger $(REGION) $(LAYER)

# Create the DEM Digital Elevation Model file
$(DEM_TIF): $(DEM_TRIGGER)
	color_relief.sh --init_dem $(REGION) $(LAYER)

# Create the preview Digital Elevation Model DEM file
$(PRV_DEM_TIF): $(DEM_TIF) $(DEM_TRIGGER)
	color_relief.sh --preview_dem $(REGION) $(LAYER)

# Create the color relief image
$(COLOR_TIF): $(DEM_TIF)  $(COLOR_RAMP_FILE)
	color_relief.sh --create_color_relief $(REGION) $(LAYER)

# Create the color relief preview image
$(PRV_COLOR_TIF): $(PRV_DEM_TIF) $(COLOR_RAMP_FILE)
	color_relief.sh --create_color_relief $(REGION) $(LAYER) preview

# Create the hillshade image
$(HILLSHADE_TIF): $(DEM_TIF)  $(CONFIG_FILE)
	color_relief.sh --create_hillshade $(REGION) $(LAYER)

# Create the hillshade preview image
$(PRV_HILLSHADE_TIF):  $(PRV_DEM_TIF) $(CONFIG_FILE)
	color_relief.sh --create_hillshade $(REGION) $(LAYER) preview

# Create the merged image. Merge the color relief and hillshade
$(FINAL_TIF): $(COLOR_TIF) $(HILLSHADE_TIF) $(CONFIG_FILE) $(DEM_TRIGGER)
	color_relief.sh --merge_hillshade $(REGION) $(LAYER)

# Create merged preview image. Merge the color relief and hillshade
$(PRV_FINAL_TIF): $(PRV_COLOR_TIF) $(PRV_HILLSHADE_TIF) $(CONFIG_FILE) $(DEM_TRIGGER)
	color_relief.sh --merge_hillshade $(REGION) $(LAYER) preview

# Clean up intermediate files
clean:
	rm -f $(DEM_TIF) $(COLOR_TIF) $(HILLSHADE_TIF)  $(PRV_COLOR_TIF) $(PRV_HILLSHADE_TIF) $(PRV_FINAL_TIF)

# Cleanup everything including the final output and preview DEM
distclean: clean
	rm -f $(FINAL_TIF) $(PRV_DEM_TIF)

# Display help and other info.  Any comment with ## is displayed in help
help:
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)
	@echo "Color Relief Makefile v0.1"
	@echo "Final target name: $(FINAL_TIF)"
	@echo "Config file: $(CONFIG_FILE)"
	@make --version
