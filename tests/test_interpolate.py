#  Copyright (c) 2024. Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated
#  documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
#  persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
#  Software.
#
#  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#  WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import pytest

from ColorReliefEditor.color_config import GdalColorFile


@pytest.fixture
def color_ramp_file():
    """Fixture to create a new instance of ColorRampFile."""
    return GdalColorFile()


def test_interpolate_1_row(color_ramp_file):
    """Test interpolation with one row (duplicate the row)."""
    color_ramp_file._data = [(100, 255, 0, 0)]
    interpolated_row = color_ramp_file.interpolate(0)
    assert interpolated_row == [100, 255, 0, 0]


def test_interpolate_2_rows_0(color_ramp_file):
    """Test extrapolation with two rows."""
    color_ramp_file._data = [(100, 100, 120, 50), (200, 200, 220, 0)]
    interpolated_row = color_ramp_file.interpolate(0)
    assert interpolated_row == [0, 0, 20, 100]  # Extrapolate [0] and [1]


def test_interpolate_2_rows_1(color_ramp_file):
    """Test interpolation with two rows."""
    color_ramp_file._data = [(100, 0, 0, 255), (200, 255, 255, 0)]
    interpolated_row = color_ramp_file.interpolate(1)
    assert interpolated_row == [150, 128, 128, 128]  # Average of two rows


def test_interpolate_3_rows_0(color_ramp_file):
    """Test extrapolation when inserting before the first row."""
    color_ramp_file._data = [(200, 20, 100, 255), (300, 0, 0, 0), (200, 255, 255, 0)]
    interpolated_row = color_ramp_file.interpolate(0)
    assert interpolated_row == [100, 40, 200, 255]  # Extrapolate based on row 0 and row 1


def test_interpolate_3_rows_1(color_ramp_file):
    """Test interpolation between the first and second rows with three rows."""
    color_ramp_file._data = [(100, 0, 0, 0), (200, 255, 255, 255), (300, 128, 128, 128)]
    interpolated_row = color_ramp_file.interpolate(1)
    assert interpolated_row == [150, 128, 128, 128]  # Interpolation between row 0 and row 1


def test_interpolate_3_rows_2(color_ramp_file):
    """Test interpolation between the first and second rows with three rows."""
    color_ramp_file._data = [(100, 0, 0, 0), (200, 254, 254, 254), (300, 154, 54, 4)]
    interpolated_row = color_ramp_file.interpolate(2)
    assert interpolated_row == [250, 204, 154, 129]  # Interpolation between row 1 and row 2


def test_interpolate_3_rows_2a(color_ramp_file):
    """Test interpolation at the last row when there are three rows."""
    color_ramp_file._data = [(100, 0, 0, 0), (200, 255, 255, 255), (300, 128, 128, 128)]
    interpolated_row = color_ramp_file.interpolate(2)
    assert interpolated_row == [250, 192, 192, 192]  # Interpolate between row 1 and row 2


def test_interpolate_boundary_rgb_values(color_ramp_file):
    """Test boundary RGB values 0 and 255."""
    color_ramp_file._data = [(100, 0, 0, 255), (200, 255, 255, 0)]
    interpolated_row = color_ramp_file.interpolate(1)
    assert interpolated_row == [150, 128, 128, 128]  # RGB values interpolated and within bounds


def test_interpolate_negative_elevation_1(color_ramp_file):
    """Test interpolation with negative elevation values."""
    color_ramp_file._data = [(-100, 0, 0, 0), (160, 255, 255, 255)]
    interpolated_row = color_ramp_file.interpolate(1)
    assert interpolated_row == [30, 128, 128, 128]  # Interpolation for negative elevations


def test_interpolate_negative_elevation_0(color_ramp_file):
    """Test interpolation with negative elevation values."""
    color_ramp_file._data = [(160, 0, 0, 0), (-100, 255, 255, 255)]
    interpolated_row = color_ramp_file.interpolate(1)
    assert interpolated_row == [30, 128, 128, 128]  # Interpolation for negative elevations


def test_extrapolate_clamping(color_ramp_file):
    """Test RGB values clamping between 0 and 255 during extrapolation and elev
    not clamped
    """
    color_ramp_file._data = [(200, 255, 255, 255), (0, 195, 0, 30)]
    extrapolated_row = color_ramp_file.interpolate(0)
    assert extrapolated_row == [400, 255, 255, 255]  # Clamping RGB values
