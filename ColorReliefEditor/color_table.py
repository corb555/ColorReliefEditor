from PySide6.QtGui import QPainter, QColor, QLinearGradient
from PySide6.QtWidgets import (QWidget, QSizePolicy)


class ColorGradientWidget(QWidget):
    """
    Widget to display a color sample with gradients between elevation level colors.
    """

    def __init__(self, color_table, height):
        """
        Initialize

        Args:
            color_table (DataManager): The color ramp data manager.
            height: The height of the widget.
        """
        super().__init__()
        self.color_table = color_table
        
        self.setMinimumSize(120, height)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )

    def scale_color_bands(self):
        """
        Scale each color band proportionally to its elevation range.

        This method calculates the parameters for rendering each color band,
        including its height and color gradient based on the elevation data. The result
        is used to create a visually accurate color gradient where each band represents a
        different elevation range.

        Returns:
            list[tuple]: A list of tuples, each containing:
                - color gradient (str): The color representation for the band.
                - target_y (float): The vertical position where the band should start.
                - band_height (float): The height of the band, indicating the elevation range it
                covers.
        """
        bands = []
        if len(self.color_table) == 0:
            print("color bands are empty")
            return bands

        # The highest elevation bands should be at the top of the sample display.
        min_y = min(self.color_table, key=lambda x: x[0])[0]
        max_y = max(self.color_table, key=lambda x: x[0])[0]

        # Offset to ensure non-negative values for target_y calculation
        offset = -min_y if min_y < 0 else 0
        height = self.height()

        # Calculate target_y with reversed elevation (higher elevations at smaller Y-values)
        target_y = [int(
            height - (elevation + offset) * height / (max_y + offset)
        ) for elevation, *_ in self.color_table]

        for i in range(len(target_y) - 1):
            y1, y2 = target_y[i], target_y[i + 1]
            c1 = QColor(*self.color_table[i][1:4])
            c2 = QColor(*self.color_table[i + 1][1:4])

            # Create a vertical gradient for each band
            gradient = QLinearGradient(0, y1, 0, y2)
            gradient.setColorAt(0, c1)
            gradient.setColorAt(1, c2)

            # Append the gradient, top Y coordinate, and height of the band
            bands.append((gradient, y1, y2 - y1))

        return bands

    def paintEvent(self, event):
        """
        Draw the color bands on the widget.

        Args:
            event: The paint event.
        """
        painter = QPainter(self)
        for gradient, y, height in self.scale_color_bands():
            painter.fillRect(0, y, self.width(), height, gradient)
