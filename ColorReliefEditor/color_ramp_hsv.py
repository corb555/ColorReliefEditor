import colorsys
from pathlib import Path
import re
from typing import List, Tuple, Any


def read_color_file(input_path: str) -> List[Tuple[bool, Any]]:
    """
    Reads and parses a GDAL color ramp file into a structured list.

    Args:
        input_path: The path to the source GDAL color configuration file.

    Returns:
        A list of tuples, where each tuple represents a parsed line from the file.
        For data lines: (True, (elevation, r, g, b, alpha))
        For non-data lines: (False, "original line content")

    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    color_table = []
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_file.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            has_data, data = parse_gdal_line(line)
            color_table.append((has_data, data))

    return color_table


def write_color_file(output_path: str, color_table: List[Tuple[bool, Any]]) -> None:
    """
    Writes a structured color table to a GDAL color ramp file.

    Args:
        output_path: The path where the configuration file will be saved.
        color_table: A structured list representing the color ramp data,
            as produced by `read_color_file`.

    Raises:
        IOError: If the file cannot be written.
    """
    output_lines = []
    for has_data, data in color_table:
        if has_data:
            elev, r, g, b, alpha = data
            output_line = f"{elev} {r} {g} {b}"
            if alpha is not None:
                output_line += f" {alpha}"
            output_lines.append(output_line)
        else:
            # For comments or other line types, data is the original string
            output_lines.append(str(data))

    try:
        with open(output_path, "w", encoding="utf-8") as f_out:
            f_out.write("\n".join(output_lines))
    except IOError as e:
        raise IOError(f"Failed to write to output file: {output_path}") from e


def adjust_color_ramp(
        input_path: str, output_path: str, saturation_multiplier: float,
        shadow_adjust: float, mid_adjust: float, highlight_adjust: float,
        min_hue: float, max_hue: float, target_hue: float
) -> None:
    """
    Reads a GDAL color ramp file, adjusts its colors in HSV space, and writes a new file.

    This function serves as a high-level orchestrator for the color adjustment process.

    Args:
        input_path: Path to the source GDAL color configuration file.
        output_path: Path where the adjusted configuration file will be saved.
        saturation_multiplier: Multiplies the saturation of each color.
            - 1.0 = no change.
            - > 1.0 = increases saturation (more vivid colors).
            - < 1.0 = decreases saturation (more muted colors).
        shadow_adjust: Additively adjusts the brightness of dark colors (v < 0.5).
        mid_adjust: Additively adjusts the brightness of mid-range colors (v ~ 0.5).
        highlight_adjust: Additively adjusts the brightness of light colors (v > 0.5).
        min_hue: The lower bound (in degrees, 0-360) of the hue range to be adjusted.
        max_hue: The upper bound (in degrees, 0-360) of the hue range to be adjusted.
        target_hue: The target hue (in degrees, 0-360) that colors within the specified
            range will be shifted towards.
    """
    # Phase 1: Read and parse the input file into a structured table.
    color_table = read_color_file(input_path)

    # Phase 2: Apply the color transformations to the data.
    adjusted_table = adjust_color_table(
        color_table,
        saturation_multiplier=saturation_multiplier,
        shadow_adjust=shadow_adjust,
        mid_adjust=mid_adjust,
        highlight_adjust=highlight_adjust,
        min_hue=min_hue,
        max_hue=max_hue,
        target_hue=target_hue
    )

    # Phase 3: Format and write the adjusted table back to a file.
    write_color_file(output_path, adjusted_table)

def adjust_color_table(
        color_table: list, saturation_multiplier: float = 1.0, shadow_adjust: float = 0.0,
        mid_adjust: float = 0.0, highlight_adjust: float = 0.0, min_hue: float = 0.0,
        max_hue: float = 0.0, target_hue: float = 0.0
) -> list:
    """
    Applies HSV transformations to a structured list of color data.

    This function iterates through a table of parsed color ramp lines. For each line
    containing color data, it converts the RGB values to HSV, applies all specified
    adjustments, converts the result back to RGB, and stores it. Non-color lines
    (like comments) are preserved in their original form.

    Args:
        color_table: A list of tuples, where each tuple represents a line from
            a GDAL color file, e.g., (True, (elev, r, g, b, a)) for a data line,
            or (False, "# a comment") for a non-data line.
        saturation_multiplier: Multiplies the saturation of each color.
            - 1.0 = no change.
            - > 1.0 = increases saturation.
            - < 1.0 = decreases saturation.
        shadow_adjust: Additively adjusts the brightness of dark colors.
        mid_adjust: Additively adjusts the brightness of mid-range colors.
        highlight_adjust: Additively adjusts the brightness of light colors.
        min_hue: The lower bound (degrees, 0-360) of the hue range to adjust.
        max_hue: The upper bound (degrees, 0-360) of the hue range to adjust.
        target_hue: The target hue (degrees, 0-360) to shift towards.

    Returns:
        A new list with the adjusted color data, preserving non-data lines.
    """
    adjusted_table = []

    def clamp(x):
        """Helper to clamp a value between 0 and 255 and convert to int."""
        return max(0, min(255, int(round(x))))

    print("\n\nADJUST:")

    for has_data, data in color_table:
        # Pass through non-data lines (comments, 'nv' lines) unchanged
        if has_data != True:
            adjusted_table.append((has_data, data))
            continue

        # Unpack, process, and repack data lines
        elev, r, g, b, alpha = data

        # Convert RGB to HSV
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

        # Apply the combined HSV adjustment logic
        h, s, v = adjust_hsv(
            h, s, v, saturation_multiplier=saturation_multiplier, shadow_adjust=shadow_adjust,
            mid_adjust=mid_adjust, highlight_adjust=highlight_adjust, min_hue=min_hue,
            max_hue=max_hue, target_hue=target_hue
        )

        # Convert back to RGB
        r_new, g_new, b_new = [clamp(c * 255.0) for c in colorsys.hsv_to_rgb(h, s, v)]

        print(f"    {elev} - {r_new} {g_new} {b_new}")

        # Append the new data to the results table
        adjusted_data = (elev, r_new, g_new, b_new, alpha)
        adjusted_table.append((True, adjusted_data))

    return adjusted_table

# In color_ramp_hsv.py

def adjust_hsv(
        h: float, s: float, v: float, saturation_multiplier: float, shadow_adjust: float,
        mid_adjust: float, highlight_adjust: float, min_hue: float,
        max_hue: float, target_hue: float
) -> (float, float, float):
    """
    Safely adjusts Hue, Saturation, and Value for a single color.
    """
    # --- 1. First, determine the final brightness (Value) ---
    shadow_weight = max(0, 1 - v * 2)
    highlight_weight = max(0, (v - 0.5) * 2)
    mid_weight = 1 - abs((v - 0.5) * 2)
    total_adjustment = (
            shadow_weight * shadow_adjust + mid_weight * mid_adjust + highlight_weight *
            highlight_adjust)
    final_v = max(0.0, min(1.0, v + total_adjustment))

    # --- 2. Create a "Fade Factor" based on ORIGINAL brightness and saturation ---
    # This is used ONLY for the hue shift to prevent colorizing greys.
    fade_factor = (1 - abs((v - 0.5) * 2)) * min(1.0, s * 4)

    # --- 3. Calculate and apply the HUE shift, scaled by the fade_factor ---
    final_h = h
    min_h_norm, max_h_norm, target_h_norm = min_hue / 360.0, max_hue / 360.0, target_hue / 360.0
    in_range = (min_h_norm <= h <= max_h_norm) if min_h_norm <= max_h_norm else (
            h >= min_h_norm or h <= max_h_norm)

    if in_range and min_hue != max_hue:
        diff = target_h_norm - h
        if diff > 0.5:
            diff -= 1.0
        elif diff < -0.5:
            diff += 1.0
        weight = 1.0
        hue_change = diff * weight * fade_factor
        final_h = (h + hue_change) % 1.0

    # --- 4. Calculate and apply the SATURATION change directly ---
    # THIS IS THE CORRECTED LOGIC
    # The multiplier is applied directly to the original saturation.
    # It is NOT scaled by the fade_factor.
    final_s = s * saturation_multiplier
    final_s = max(0.0, min(1.0, final_s)) # Clamp the final result

    return final_h, final_s, final_v


def parse_gdal_line(line: str) -> (bool, any):
    """
    Parses a single line from a GDAL color ramp file.

    It distinguishes between data lines (containing elevation and color values)
    and non-data lines (like comments or the 'nv' keyword for no-data).

    Args:
        line: A single, stripped line from the GDAL color text file.

    Returns:
        A tuple of `(has_data, data)` where:
        - `has_data` (bool): Is True if the line contains color data, False otherwise.
        - `data`: If `has_data` is True, this is a tuple of
          (elevation, r, g, b, alpha). Alpha may be None.
          If `has_data` is False, this is the original string of the line.

    Raises:
        ValueError: If a data line has an invalid format or its color
            values are outside the valid 0-255 range.
    """
    line = line.strip()
    if line.startswith("#") or line.startswith("nv"):
        return False, line

    # Split the line using comma, tab, or space as separators
    parts = re.split(r'[,\t\s]+', line)

    if not 4 <= len(parts) <= 5:
        raise ValueError(
            f"Invalid line format: expected 4 or 5 values, but got {len(parts)} in '{line}'"
        )

    try:
        elevation = float(parts[0]) if '.' in parts[0] else int(parts[0])
        color_values = [int(value) for value in parts[1:]]
    except (ValueError, IndexError):
        raise ValueError(
            "Elevation must be a number and color values must be integers."
        )

    if not all(0 <= value <= 255 for value in color_values):
        raise ValueError("Color values must be between 0 and 255.")

    r, g, b, *a = color_values
    alpha = a[0] if a else None

    return True, (elevation, r, g, b, alpha)
