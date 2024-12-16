# Color Relief Editor
## Overview

This application uses Digital Elevation files and GDAL tools to create hillshade and color relief images which 
are combined into a final relief image. All settings, including colors and parameters, are set directly 
in the app and the app executes GDAL utilities to generate the images.  

**Features**:

* **Color editor for color relief settings:**
  * Edit settings and see fast preview 
  * Color palette selector for each color
  * Undo to back out unwanted changes
  * Insert row with interpolation
  * Rescale to rescale all elevations
  * Import any standard GDAL color setting file 
* **Hillshade Settings editor:**
  * Edit settings and see fast preview
* **Final relief build:**
  * Uses composite multiply to cleanly merge the hillshade and color relief for the final image.
  * All settings are stored in a configuration file.
  * Does the minimum steps needed to generate the image (only rebuilds items with config changes).
  * Uses multiple processors in parallel to boost performance.
  * Links to external viewer (QGIS or GIMP)
  * Copy file to map server
* **Elevation Files**
  * Download files and simply drop and drop them to Elevation Tab
  * Optionally sets the Coordinate Reference System (CRS)
  * Store their source URL and License

 For a great introduction to GDAL and shaded relief, see Robert Simmons'
explanation [here](https://medium.com/@robsimmon/a-gentle-introduction-to-gdal-part-5-shaded-relief-ec29601db654).

## Installation

### Mac - Install Dependencies
Use  Homebrew or Anaconda to install these items (whichever your system normally uses).
Note - this has not been tested with the Anaconda package manager.
- [ ] **yq:** Used to parse the config file.
- [ ] **gdal:** Install GDAL, the Geospatial Data Abstraction Library 
- [ ] **gmake:** Make, used to determine what needs to be built

### Linux Install Dependencies
Use whichever package manager your system has to install these:
- [ ] **yq:** Used to parse the config file.
- [ ] **gdal-bin:** Install GDAL, the Geospatial Data Abstraction Library 

### Install ColorReliefEditor
   ```shell
   pip install ColorReliefEditor
   ```

## Create a Color Relief Image

1. **Launch ColorReliefEditor**
   - Start your systems Command shell / Terminal and type:
   ```shell
   ColorReliefEditor
   ```
   - Click on New to create a new project
   - In Elevation tab: download elevation files and drag and drop them here
   - In Hillshade and Color tab: Edit settings and click Preview to review
   - In Relief tab:  click Create to create a full size merge of hillshade and color relief

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