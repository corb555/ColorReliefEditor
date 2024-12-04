-
Makefile for Color Relief Generation using GDAL
-
This Makefile automates the process of generating color relief images and hillshade overlays
for a specified REGION and LAYER. It defines a set of rules for generating Digital Elevation
Model (DEM) files, color relief images, and hillshades using the `color_relief.sh` script.
Preview images are also generated for faster inspection. The Makefile supports both
full-resolution and preview outputs, and includes targets for cleaning up intermediate files.

Required Environment Variables:
  - REGION: Specifies the region name (e.g., 'ICELAND').
  - LAYER:  Specifies the data layer (e.g., 'A', 'B').
-
Usage Example:
  make REGION='ICELAND' LAYER='A' all
-
Key Targets:
  - help:       Displays Help text
  - all:        Generates the final merged color relief image with hillshade.
  - clean:      Removes intermediate files, keeping the final outputs.
  - distclean:  Removes all generated files, including previews and final outputs.
  - info_version: Displays the version of Make and this Makefile
-
Config Files:
  - $(REGION)_relief.cfg: Configuration file for GDAL command parameters
  - $(REGION)_color_ramp.txt: Color ramp file for `gdaldem` to create color relief images.
-
Output Files:
  - $(REGION)_$(LAYER)_DEM.tif: Digital Elevation Model (DEM) file
  - $(REGION)_$(LAYER)_color.tif: Color relief image.
  - $(REGION)_$(LAYER)_hillshade.tif: Hillshade overlay.
  - $(REGION)_$(LAYER)_relief.tif: Final merged relief image.
  -
  - Preview versions of these files are named $(REGION)_$(LAYER)_prv_*.
-
color_relief.sh:
 This is called with:  color_relief.sh --COMMAND $(REGION) $(LAYER) preview
