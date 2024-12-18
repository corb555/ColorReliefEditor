# Color Relief Editor

<img width="622" alt="sample" src="https://github.com/corb555/ColorReliefEditor/blob/main/docs/images/color%20sample.png?raw=true">

---

# Overview

This application uses GDAL tools to create high-quality color relief maps from 
Digital Elevation Model (DEM) files. 
The app provides user-configurable settings for the colors and parameters, and directly executes GDAL 
utilities, providing a seamless experience for creating relief maps.

---

## Features

### **Color Editor**
- **Real-Time Editing:** Modify settings and preview results instantly.
- **Color Palette Selector:** Choose colors for each elevation range with ease.
- **Undo Support:** Roll back unwanted changes.
- **Insert rows:** Insert rows with interpolation.
- **Rescale:** Rescale elevation values with one click.
- **Import:** Import standard GDAL color files.

### **Hillshade Editor**
- Modify hillshade settings and see immediate previews.

### **Final Relief Image Generation**
- **Blending:** Combines hillshade and color relief with composite multiply for smooth results.
- **Optimized Processing:**
  - Only rebuilds components when configurations change.
  - Supports multi-core processing for faster performance.
- **External Tools:** Links to external viewers like QGIS or GIMP for post-processing.
- **Convenient Workflow:** Copy the final image directly to a map server.

### **Elevation File Management**
- **Drag-and-Drop:** Easily upload elevation files via the Elevation Tab.
- **Coordinate Reference System (CRS):** Optionally set the CRS for your files.
- **Metadata:** Save source URLs and license information for all elevation files.

---

## Installation

---

## _Install Dependencies_

### Mac / Anaconda

```shell
conda install yq
conda install gdal
conda install make
```

### Mac / Homebrew
 
```shell
brew install yq
brew install gdal 
brew install make
```

### Debian / Ubuntu 
 
```shell
sudo apt-get install yq
sudo apt-get install gdal-bin
```

## _Install ColorReliefEditor_
   It is recommended that you set up a virtual Python environment for this.
   ```shell
   pip install ColorReliefEditor
   ```

## Usage - Create a Color Relief Image

1. **Launch ColorReliefEditor**
   - Start Terminal and type:
   ```shell
   ColorReliefEditor
   ```
   
2. **In Project Tab** - click _New_ to create a new project
3. **In Elevation Tab** - download Digital Elevation files and drag and drop them here
4. **In Hillshade and Color Tab** - edit Hillshade and Color settings and click _Preview_ to review
5. **In Relief Tab**  - click _Create_ to create a full size merge of hillshade and color relief

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

## Support
To report an issue, please visit the [issue tracker](https://github.com/corb555/ColorReliefEditor/issues).