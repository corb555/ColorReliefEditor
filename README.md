# ColorReliefEditor
Editor for the color text file used by gdaldem color-relief

![screenshot](https://github.com/corb555/openstreetmap-carto-walking/blob/1fe3b736e584b62f742cadb9c64ec72148f3dbe2/seattle_z16.png)

# Description   
gdaldem color-relief uses a file with lines describing the RGB values to be used for each elevation   
This provides an editor for the colors and elevations and displays all the colors together

# Usage
colorReliefEditor color_text_file   

filename is a color relief file which contains lines of the format:  
_elevation_value red green blue_ 
