import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QComboBox, QSpinBox, QLabel, QTextEdit, QGridLayout)
from PyQt5.QtGui import QPainter, QColor, QPen, QImage, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, QPoint

class POVWandDesigner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("POV Wand Pattern Designer")
        self.setMinimumSize(800, 600)

        # Set the window icon
        self.setWindowIcon(QIcon('pov_wand.ico'))  # Ensure this file exists in the directory

        # Initial parameters
        self.width = 64
        self.height = 16
        self.grid = [[False] * self.width for _ in range(self.height)]
        self.preview_grid = None
        self.current_tool = "draw"
        self.is_mouse_down = False
        self.start_point = None
        self.output_format = "heart"

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Controls
        controls_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 64)
        self.width_spin.setValue(self.width)
        self.width_spin.valueChanged.connect(self.update_width)
        controls_layout.addWidget(QLabel("Design Width:"))
        controls_layout.addWidget(self.width_spin)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["Heart Format (64 cols)", "Hanzi Format (16 cols)"])
        self.format_combo.currentTextChanged.connect(self.update_format)
        controls_layout.addWidget(QLabel("Output Format:"))
        controls_layout.addWidget(self.format_combo)
        layout.addLayout(controls_layout)

        # Tool buttons
        tools_layout = QHBoxLayout()
        self.tool_buttons = {}
        for tool in ["draw", "erase", "line", "circle"]:
            btn = QPushButton(tool.capitalize())
            btn.clicked.connect(lambda checked, t=tool: self.set_tool(t))
            self.tool_buttons[tool] = btn
            tools_layout.addWidget(btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_grid)
        tools_layout.addWidget(clear_btn)

        for pattern, color in [("Heart", "#FF6B6B"), ("HI", "#4CAF50"), ("Smiley", "#FFD700")]:
            btn = QPushButton(f"Draw {pattern}")
            btn.clicked.connect(getattr(self, f"draw_{pattern.lower()}"))
            btn.setStyleSheet(f"background-color: {color}")
            tools_layout.addWidget(btn)
        
        layout.addLayout(tools_layout)

        # Drawing and preview area
        self.grid_widget = GridWidget(self)
        self.preview_widget = PreviewWidget(self)
        display_layout = QHBoxLayout()
        display_layout.addWidget(self.grid_widget)
        display_layout.addWidget(self.preview_widget)
        layout.addLayout(display_layout)

        # Hex output
        self.generate_btn = QPushButton("Generate Hex Code")
        self.generate_btn.clicked.connect(self.generate_hex_code)
        layout.addWidget(self.generate_btn)

        self.hex_output = QTextEdit()
        self.hex_output.setReadOnly(True)
        layout.addWidget(self.hex_output)

        self.update_tool_buttons()

    def update_width(self, value):
        self.width = value
        self.grid = [[False] * self.width for _ in range(self.height)]
        self.grid_widget.update()
        self.preview_widget.update()

    def update_format(self, text):
        self.output_format = "heart" if "Heart" in text else "hanzi"

    def set_tool(self, tool):
        self.current_tool = tool
        self.update_tool_buttons()

    def update_tool_buttons(self):
        for tool, btn in self.tool_buttons.items():
            btn.setStyleSheet("background-color: #3498DB" if tool == self.current_tool else "")

    def clear_grid(self):
        self.grid = [[False] * self.width for _ in range(self.height)]
        self.hex_output.clear()
        self.grid_widget.update()
        self.preview_widget.update()

    def draw_line(self, grid, r0, c0, r1, c1, value):
        dr = abs(r1 - r0)
        dc = abs(c1 - c0)
        sr = 1 if r0 < r1 else -1
        sc = 1 if c0 < c1 else -1
        err = (dc if dc > dr else -dr) / 2

        while True:
            if 0 <= r0 < self.height and 0 <= c0 < self.width:
                grid[r0][c0] = value
            if r0 == r1 and c0 == c1:
                break
            err2 = err
            if err2 > -dc:
                err -= dr
                c0 += sc
            if err2 < dr:
                err += dc
                r0 += sr

    def draw_circle(self, grid, center_row, center_col, end_row, end_col, value):
        radius = math.sqrt((end_row - center_row) ** 2 + (end_col - center_col) ** 2)
        radius = round(radius)
        x = radius
        y = 0
        err = 0

        while x >= y:
            # Plot points in all eight octants
            points = [
                (center_row + y, center_col + x), (center_row + x, center_col + y),
                (center_row - y, center_col + x), (center_row - x, center_col + y),
                (center_row - y, center_col - x), (center_row - x, center_col - y),
                (center_row + y, center_col - x), (center_row + x, center_col - y)
            ]
            for r, c in points:
                if 0 <= r < self.height and 0 <= c < self.width:
                    grid[r][c] = value
            # Additional points to smooth the circle
            if x > y:
                points = [
                    (center_row + y + 1, center_col + x), (center_row + x, center_col + y + 1),
                    (center_row - y - 1, center_col + x), (center_row - x, center_col + y + 1),
                    (center_row - y - 1, center_col - x), (center_row - x, center_col - y - 1),
                    (center_row + y + 1, center_col - x), (center_row + x, center_col - y - 1)
                ]
                for r, c in points:
                    if 0 <= r < self.height and 0 <= c < self.width:
                        grid[r][c] = value
            y += 1
            err += 1 + 2 * y
            if 2 * (err - x) + 1 > 0:
                x -= 1
                err += 1 - 2 * x

    def fill_circle(self, grid, center_row, center_col, radius, value):
        """Fill a circle with a given value."""
        for r in range(self.height):
            for c in range(self.width):
                distance = math.sqrt((r - center_row) ** 2 + (c - center_col) ** 2)
                if distance <= radius:
                    grid[r][c] = value

    def draw_heart(self):
        self.clear_grid()
        # Heart pattern as binary strings (16 bits per row)
        heart_pattern = [
            "0000011000110000",  # Row 0
            "0001111111111000",  # Row 1
            "0011111111111100",  # Row 2
            "0111111111111110",  # Row 3
            "0111111111111110",  # Row 4
            "0111111111111110",  # Row 5
            "0011111111111100",  # Row 6
            "0001111111111000",  # Row 7
            "0000111111110000",  # Row 8
            "0000011111100000",  # Row 9
            "0000001111000000",  # Row 10
            "0000000110000000",  # Row 11
        ]
        # Calculate offset to center the pattern horizontally (16 bits wide)
        pattern_width = 16
        h_offset = (self.width - pattern_width) // 2
        # Shift down by 4 rows to center vertically (16 rows total, 12 rows pattern)
        v_offset = 2  # (16 - 12) // 2 + 2 = 4

        # Draw the heart pattern
        for row, binary in enumerate(heart_pattern):
            shifted_row = row + v_offset
            for col, bit in enumerate(binary):
                shifted_col = col + h_offset
                if 0 <= shifted_row < self.height and 0 <= shifted_col < self.width:
                    self.grid[shifted_row][shifted_col] = (bit == '1')

        self.grid_widget.update()
        self.preview_widget.update()

    def draw_hi(self):
        self.clear_grid()
        # Calculate offset to center the pattern
        pattern_width = 13  # Max col index (13) - Min col index (2) + 1
        offset = (self.width - pattern_width) // 2
        hi_pattern = [
            # Top half
            [
                # H left vertical line
                (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
                # H horizontal bar (on row 6)
                (3, 6), (4, 6), (5, 6),
                # H right vertical line
                (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7),
                # I top bar
                (9, 1), (10, 1), (11, 1), (12, 1), (13, 1),
                # I vertical bar
                (11, 2), (11, 3), (11, 4), (11, 5), (11, 6), (11, 7),
            ],
            # Bottom half
            [
                # H left vertical line
                (2, 8), (2, 9), (2, 10), (2, 11), (2, 12), (2, 13),
                # H right vertical line
                (6, 8), (6, 9), (6, 10), (6, 11), (6, 12), (6, 13),
                # I vertical bar
                (11, 8), (11, 9), (11, 10), (11, 11), (11, 12),
                # I bottom bar
                (9, 13), (10, 13), (11, 13), (12, 13), (13, 13)
            ]
        ]
        for points in hi_pattern:
            for col, row in points:
                shifted_col = col + offset
                if 0 <= shifted_col < self.width and row < self.height:
                    self.grid[row][shifted_col] = True
        self.grid_widget.update()
        self.preview_widget.update()

    def draw_smiley(self):
        self.clear_grid()
        # Center the smiley face
        center_col = self.width // 2
        center_row = self.height // 2  # Middle of 16 rows is 7-8
        radius = min(self.width // 4, 7)  # Adjust radius based on grid size, max 7 for height

        # Fill the face circle with lit LEDs (True) to create a solid background
        self.fill_circle(self.grid, center_row, center_col, radius, True)

        # Draw unlit eyes (False)
        eye_radius = radius // 4
        self.fill_circle(self.grid, center_row - radius // 2, center_col - radius // 2, eye_radius, False)
        self.fill_circle(self.grid, center_row - radius // 2, center_col + radius // 2, eye_radius, False)

        # Draw unlit mouth (False)
        mouth_radius = radius // 2
        for col in range(center_col - mouth_radius, center_col + mouth_radius + 1):
            row = center_row + radius // 2
            if 0 <= row < self.height and 0 <= col < self.width:
                self.grid[row][col] = False
        for col in [center_col - mouth_radius - 1, center_col + mouth_radius + 1]:
            row = center_row + radius // 2 - 1
            if 0 <= row < self.height and 0 <= col < self.width:
                self.grid[row][col] = False

        # Redraw the outline of the face circle to ensure it's crisp and black
        self.draw_circle(self.grid, center_row, center_col, center_row + radius, center_col, True)

        self.grid_widget.update()
        self.preview_widget.update()

    def generate_hex_code(self):
        bytes = []
        max_cols = min(self.width, 16 if self.output_format == "hanzi" else 64)

        for col in range(max_cols):
            top_byte = 0
            for row in range(8):
                if col < max_cols and row < self.height and self.grid[row][col]:
                    top_byte |= (1 << row)
            bytes.append(top_byte)

            bottom_byte = 0
            for row in range(8, 16):
                if col < max_cols and row < self.height and self.grid[row][col]:
                    bottom_byte |= (1 << (row - 8))
            bytes.append(bottom_byte)

        while len(bytes) < 128:
            bytes.append(0)

        formatted_code = ""
        for line in range(8):
            line_output = ""
            for i in range(16):
                byte_index = line * 16 + i
                line_output += f"0x{bytes[byte_index]:02X},"
            formatted_code += line_output + "\n"
        
        self.hex_output.setText(formatted_code)

class GridWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.cell_size = 20
        self.setMinimumSize(self.parent.width * self.cell_size, self.parent.height * self.cell_size)

    def paintEvent(self, event):
        painter = QPainter(self)
        grid = self.parent.preview_grid or self.parent.grid
        
        for row in range(self.parent.height):
            for col in range(self.parent.width):
                color = Qt.black if grid[row][col] else Qt.white
                painter.fillRect(col * self.cell_size, row * self.cell_size,
                               self.cell_size, self.cell_size, color)
                painter.setPen(Qt.gray)
                painter.drawRect(col * self.cell_size, row * self.cell_size,
                               self.cell_size, self.cell_size)
        
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(0, 8 * self.cell_size, self.parent.width * self.cell_size, 8 * self.cell_size)

    def mousePressEvent(self, event):
        self.parent.is_mouse_down = True
        row, col = event.pos().y() // self.cell_size, event.pos().x() // self.cell_size
        if self.parent.current_tool in ["line", "circle"]:
            self.parent.start_point = QPoint(int(col), int(row))
        else:
            self.handle_cell(int(row), int(col))
        self.update()

    def mouseMoveEvent(self, event):
        if not self.parent.is_mouse_down:
            return
        row, col = event.pos().y() // self.cell_size, event.pos().x() // self.cell_size
        if self.parent.current_tool in ["draw", "erase"]:
            self.handle_cell(int(row), int(col))
        elif self.parent.start_point:
            self.parent.preview_grid = [row[:] for row in self.parent.grid]
            if self.parent.current_tool == "line":
                self.parent.draw_line(self.parent.preview_grid, self.parent.start_point.y(),
                                    self.parent.start_point.x(), int(row), int(col), True)
            elif self.parent.current_tool == "circle":
                self.parent.draw_circle(self.parent.preview_grid, self.parent.start_point.y(),
                                      self.parent.start_point.x(), int(row), int(col), True)
        self.update()

    def mouseReleaseEvent(self, event):
        if self.parent.is_mouse_down and self.parent.start_point:
            row, col = event.pos().y() // self.cell_size, event.pos().x() // self.cell_size
            if self.parent.current_tool == "line":
                self.parent.draw_line(self.parent.grid, self.parent.start_point.y(),
                                    self.parent.start_point.x(), int(row), int(col), True)
            elif self.parent.current_tool == "circle":
                self.parent.draw_circle(self.parent.grid, self.parent.start_point.y(),
                                      self.parent.start_point.x(), int(row), int(col), True)
        self.parent.is_mouse_down = False
        self.parent.start_point = None
        self.parent.preview_grid = None
        self.update()
        self.parent.preview_widget.update()

    def handle_cell(self, row, col):
        if 0 <= row < self.parent.height and 0 <= col < self.parent.width:
            self.parent.grid[row][col] = self.parent.current_tool == "draw"
            self.parent.preview_widget.update()

class PreviewWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setMinimumSize(200, 200)

    def paintEvent(self, event):
        painter = QPainter(self)
        image = QImage(self.parent.width, self.parent.height, QImage.Format_RGB32)
        image.fill(Qt.white)
        
        for row in range(self.parent.height):
            for col in range(self.parent.width):
                if self.parent.grid[row][col]:
                    image.setPixel(col, row, QColor(Qt.black).rgb())
        
        # Simulate POV effect by stretching horizontally
        scaled = image.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
        painter.drawPixmap(0, 0, QPixmap.fromImage(scaled))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POVWandDesigner()
    window.show()
    sys.exit(app.exec_())