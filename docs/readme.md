# Color Relief Editor
## Overview

This application uses Digital Elevation files and GDAL tools to create hillshade and color relief images which 
are combined into a final relief image. All settings, including colors and parameters, are set directly 
in the app and GDAL utilities are automatically executed to generate the images.  

Key Features:

* Color editor for color relief settings:
  * Fast preview.
  * Undo to back out unwanted changes.
  * Insert row with interpolation
  * Rescale to rescale all elevations
* Hillshade Settings editor with fast preview
* Final relief build:
  * Uses composite multiply to cleanly merge the hillshade and color relief for the final image.
  * Stores all settings, including DEM file sources, in a single configuration file.
  * Rebuilds only the necessary parts when settings are updated.
  * Uses multiple processors in parallel to boost performance.
  * Links to external viewer (QGIS or GIMP)
  * Copy file to map server
* Elevation Files
  * Download files and simply drop and drop them to Elevation Tab to add to configuration
  * Optionally sets the Coordinate Reference System (CRS).

 For a great introduction to GDAL and shaded relief, see Robert Simmons'
explanation [here](https://medium.com/@robsimmon/a-gentle-introduction-to-gdal-part-5-shaded-relief-ec29601db654).

## Initial Setup

- **Install Dependencies**
- [ ] **yq:** Install yq which is used to parse the config file. For MacOS you can use Homebrew:

```sh
brew install yq
```

- [ ] **GDAL:** Install GDAL, the Geospatial Data Abstraction Library   
  https://gdal.org/en/latest/download.html#binaries

## Create a Color Relief Image

1. **Launch ColorReliefEditor**
   - Start your systems Command shell / Terminal and type:
   ```shell
   ColorReliefEditor
   ```
2. **Project Tab** - Create New Project:
   - To start a new project, click New in the Project Tab. A dialog will appear where you can specify the project folder
   location. A sample color ramp and settings file will be automatically generated within this folder.
3. **Elevation Tab** - Add Digital Elevation files:
   - Click on **Download**.  This will bring you to the EarthExplorer
   - Select Digital Elevation under the Data Sets tab and choose GMTED2010. Download  gmted_mea files for your area.
   - In your system's Finder/File Manager, go to Downloads, drag and drop the TIF files to the blue box labelled _Drag Elevation 
     File Here_.
4. **Hillshade Tab** - Tune Hillshade parameters:
    - Try different Shading Algorithms and Z Factor settings. 
    - Click Preview to see a preview.  The first time this is run may take a long time.
5. **Color Tab** - Tune color parameters:
    - Try different Color and Elevations settings. 
    - Click Preview to see a preview.
6. **Relief Tab** - Generate final full size image:
    - Click Create to generate a full size image
    - Click View to view the image in QGIS or GIMP
    - Click Publish to copy the file to "Publish To" destination

## License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.