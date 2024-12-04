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

from ColorReliefEditor.color_file import ColorFile


def test_valid_lines():
    """
    Test valid GDAL color mapping lines to ensure they are parsed correctly.

    This test verifies that properly formatted lines return the expected tuples
    of elevation and color values.
    """
    valid_cases = [("1000 255 255 255", (1000, 255, 255, 255, None)),
        ("500 128 64 32 255", (500, 128, 64, 32, 255)), ("200 0 0 0", (200, 0, 0, 0, None)), ]
    for line, expected in valid_cases:
        assert ColorFile._parse_gdal_line(line) == expected


def test_invalid_lines():
    """
    Test invalid GDAL color mapping lines to ensure ValueError is raised.

    This test checks various incorrectly formatted lines and confirms that a
    ValueError is raised for each case, indicating that the input is invalid.
    """
    invalid_cases = ["1000 255 255 256",  # Color value out of range
        "1000 255 255 -1",  # Negative color value
        "1000 255 255 255.5",  # Decimal value
        "1000 255 255 abc",  # Alphabetic color value
        "1000 255 255",  # Missing one color value
        "abc 255 255 255",  # Non-integer elevation
    ]

    for line in invalid_cases:
        print(f"Testing line: {line}")  # Print each line as it's being tested
        with pytest.raises(ValueError):
            ColorFile._parse_gdal_line(line)
