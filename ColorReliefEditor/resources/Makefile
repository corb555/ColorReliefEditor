#!/bin/sh
##
## Color Relief Generation Makefile
## ====================================
##
## This Makefile automates the generation of color relief images and hillshade images
## for a specified REGION and LAYER. It defines rules for creating Digital Elevation Model (DEM) files,
## color relief images, and hillshades using the `color_relief.sh` script.
## Dependencies ensure that only necessary steps run for each image type.
##
## Additionally, preview images can be generated for faster inspection. This Makefile supports
## both full-resolution and preview outputs and includes targets for cleaning up intermediate files.
##
## Required Environment Variables
## ------------------------------
##   - **REGION**: Specifies the region name (e.g., 'ICELAND').
##   - **LAYER**: Specifies the data layer (e.g., 'A', 'B').
##
## Usage Example
## -------------
## To generate a color relief image, run the following command:
##
## .. code-block:: shell
##
##    make REGION='ICELAND' LAYER='A' all
##
## Configuration Files
## -------------------
##   - ``$(REGION)_relief.cfg``: Contains GDAL command parameters.
##   - ``$(REGION)_color_ramp.txt``: Color ramp file for `gdaldem` to create color relief images.
##
## General Targets
## ---------------
##   - **all**: Generates the final merged color relief image with hillshade.
##   - **clean**: Removes intermediate files while keeping final outputs.
##   - **distclean**: Removes all generated files, including previews and final outputs.
##   - **info_version**: Displays the version of Make and this Makefile.
##   - **docs**: Generates documentation using all lines starting with `##`.
##
## Output Files
## ------------
##
##   - ``$(REGION)_$(LAYER)_DEM.tif``: Digital Elevation Model (DEM) file.
##   - ``$(REGION)_$(LAYER)_color.tif``: Color relief image.
##   - ``$(REGION)_$(LAYER)_hillshade.tif``: Hillshade overlay.
##   - ``$(REGION)_$(LAYER)_relief.tif``: Final merged relief image.
##   - Preview versions of these files are named ``$(REGION)_$(LAYER)_xxx_prv.tif``.
##
## color_relief.sh
## ----------------
## This script is executed by Make with a specific command replacing `--COMMAND`:
##
## .. code-block:: shell
##
##    color_relief.sh --COMMAND $(REGION) $(LAYER) <preview>
##
## Create documentation for this makefile
## -------------
## Run the following from project root
##
##     .. code-block:: shell
##
##        make -f ColorReliefEditor/resources/Makefile docs
##

MAKEFLAGS += --warn-undefined-variables

# Ensure REGION and LAYER are set, unless the target is "docs"
ifneq ($(filter docs,$(MAKECMDGOALS)),docs)
    ifndef REGION
        $(error ERROR: REGION is not set. Usage: make REGION='ICELAND' LAYER='A' all)
    endif

    ifndef LAYER
        $(error ERROR: LAYER is not set. Usage: make REGION='ICELAND' LAYER='A' all)
    endif
endif

# CONFIG_FILE - contains the switches for GDAL commands
CONFIG_FILE = $(REGION)_relief.cfg

# Color ramp file - for gdaldem color relief
COLOR_RAMP_FILE = $(REGION)_color_ramp.txt

# Set project name variable
PROJECT_NAME = ColorReliefEditor

# Ensure necessary files exist
$(CONFIG_FILE):
	$(error ERROR: Config file not found: "$@")

$(COLOR_RAMP_FILE):
	$(error ERROR: Color ramp file not found: "$@")

# Standard image files start with $(REGION)_$(LAYER)
PREFIX = $(REGION)_$(LAYER)

# Targets for full images
DEM_TIF = $(PREFIX)_DEM.tif
COLOR_TIF = $(PREFIX)_color.tif
HILLSHADE_TIF = $(PREFIX)_hillshade.tif
SLOPE_TIF = $(PREFIX)_slope.tif
CONTOUR_SHP = $(PREFIX)_contour.shp
FINAL_TIF = $(PREFIX)_relief.tif

# Targets for preview images
PRV_DEM_TIF = $(PREFIX)_DEM_prv.tif
PRV_COLOR_TIF = $(PREFIX)_color_prv.tif
PRV_HILLSHADE_TIF = $(PREFIX)_hillshade_prv.tif
PRV_SLOPE_TIF = $(PREFIX)_slope_prv.tif
PRV_FINAL_TIF = $(PREFIX)_relief_prv.tif

# Empty files used to trigger DEM and Hillshade rebuilds
DEM_TRIGGER = $(PREFIX)_DEM_trigger.cfg
HILLSHADE_TRIGGER = $(REGION)_hillshade_trigger.cfg

# Phony targets
.PHONY: all clean distclean help docs

# Default target
all: $(FINAL_TIF)

# Create the DEM trigger if missing
$(DEM_TRIGGER):
	color_relief.sh --create_trigger $(REGION) $(LAYER) $(DEM_TRIGGER)

# Create the Hillshade trigger if missing
$(HILLSHADE_TRIGGER):
	color_relief.sh --create_trigger $(REGION) $(LAYER) $(HILLSHADE_TRIGGER)

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
$(HILLSHADE_TIF): $(DEM_TIF)  $(HILLSHADE_TRIGGER)
	color_relief.sh --create_hillshade $(REGION) $(LAYER)

# Create the hillshade preview image
$(PRV_HILLSHADE_TIF):  $(PRV_DEM_TIF) $(HILLSHADE_TRIGGER)
	color_relief.sh --create_hillshade $(REGION) $(LAYER) preview

# Create the slope image
$(SLOPE_TIF): $(DEM_TIF)  $(HILLSHADE_TRIGGER)
	color_relief.sh --create_slope $(REGION) $(LAYER)

# Create the slope preview image
$(PRV_SLOPE_TIF):  $(PRV_DEM_TIF) $(HILLSHADE_TRIGGER)
	color_relief.sh --create_slope $(REGION) $(LAYER) preview

# Merge the color relief and hillshade into the final image
$(FINAL_TIF): $(COLOR_TIF) $(HILLSHADE_TIF) $(CONFIG_FILE) $(DEM_TRIGGER)
	color_relief.sh --merge_hillshade $(REGION) $(LAYER)

# Create the contour shapefile
$(CONTOUR_SHP): $(DEM_TIF) $(CONFIG_FILE)
	color_relief.sh --create_contour $(REGION) $(LAYER)

# Create merged preview image. Merge the color relief and hillshade
$(PRV_FINAL_TIF): $(PRV_COLOR_TIF) $(PRV_HILLSHADE_TIF) $(CONFIG_FILE) $(DEM_TRIGGER)
	color_relief.sh --merge_hillshade $(REGION) $(LAYER) preview

# Clean up intermediate files
clean:
	rm -f $(DEM_TIF) $(COLOR_TIF) $(HILLSHADE_TIF) $(PRV_DEM_TIF) $(PRV_COLOR_TIF) $(PRV_HILLSHADE_TIF) $(PRV_FINAL_TIF)
	@echo "Done"

# Cleanup everything including the final output and preview DEM
distclean: clean
	rm -f $(FINAL_TIF) $(PRV_DEM_TIF)
	@echo "Done"

# Generate RST documentation from Makefile ## comments. Must run from project root
ABS_DOCS_PATH := $(abspath docs/source/makefile.rst)
ABS_MAKEFILE_PATH := $(abspath $(PROJECT_NAME)/resources/Makefile)
SED_COMMAND_FILE := $(abspath $(PROJECT_NAME)/resources/sed_doc.txt)

docs: $(ABS_DOCS_PATH)

$(ABS_DOCS_PATH): $(ABS_MAKEFILE_PATH) $(SED_COMMAND_FILE)
	@grep '^##' $(ABS_MAKEFILE_PATH) | sed -f $(SED_COMMAND_FILE) > $@
	@echo "Generated Makefile documentation: $@"
