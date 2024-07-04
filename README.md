# Editor for the color text file used by gdaldem color-relief


![screenshot](https://github.com/corb555/ColorReliefEditor/blob/8b9dc20a4ae7fdd0e1b266afe9492fbab3d42d52/colorrelief.png)
# Description   
An editor for the color definition file used by the gdaldem color-relief utility. This tool displays the color for each elevation
and allows you to edit each color and elevation.  
gdaldem generates a color relief map based on defining colors for each elevation based on a file.  
For details on gdaldem:  https://gdal.org/programs/gdaldem.html

# Installation
`python3 -m pip install "ColorReliefEditor"`

# Usage
`python3 ColorReliefEditor`   
This will display a file dialog filtered for *.txt

This will edit a color relief file which contains lines of the format:  
_elevation_value red green blue_ 