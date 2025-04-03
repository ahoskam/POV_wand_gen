import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QComboBox, QSpinBox, QLabel, QTextEdit, QGridLayout,
                            QButtonGroup)
from PyQt5.QtGui import QPainter, QColor, QPen, QImage, QPixmap, QIcon, QDrag
from PyQt5.QtCore import Qt, QSize, QPoint, QMimeData

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

        # Alphabet keyboard
        self.alphabet_keyboard = AlphabetKeyboard(self)
        layout.addWidget(self.alphabet_keyboard)

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
            points = [
                (center_row + y, center_col + x), (center_row + x, center_col + y),
                (center_row - y, center_col + x), (center_row - x, center_col + y),
                (center_row - y, center_col - x), (center_row - x, center_col - y),
                (center_row + y, center_col - x), (center_row + x, center_col - y)
            ]
            for r, c in points:
                if 0 <= r < self.height and 0 <= c < self.width:
                    grid[r][c] = value
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
        for r in range(self.height):
            for c in range(self.width):
                distance = math.sqrt((r - center_row) ** 2 + (c - center_col) ** 2)
                if distance <= radius:
                    grid[r][c] = value

    def draw_heart(self):
        self.clear_grid()
        heart_pattern = [
            "0000011000110000",
            "0001111111111000",
            "0011111111111100",
            "0111111111111110",
            "0111111111111110",
            "0111111111111110",
            "0011111111111100",
            "0001111111111000",
            "0000111111110000",
            "0000011111100000",
            "0000001111000000",
            "0000000110000000",
        ]
        pattern_width = 16
        h_offset = (self.width - pattern_width) // 2
        v_offset = 2

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
        pattern_width = 13
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
        center_col = self.width // 2
        center_row = self.height // 2
        radius = min(self.width // 4, 7)

        self.fill_circle(self.grid, center_row, center_col, radius, True)

        eye_radius = radius // 4
        self.fill_circle(self.grid, center_row - radius // 2, center_col - radius // 2, eye_radius, False)
        self.fill_circle(self.grid, center_row - radius // 2, center_col + radius // 2, eye_radius, False)

        mouth_radius = radius // 2
        for col in range(center_col - mouth_radius, center_col + mouth_radius + 1):
            row = center_row + radius // 2
            if 0 <= row < self.height and 0 <= col < self.width:
                self.grid[row][col] = False
        for col in [center_col - mouth_radius - 1, center_col + mouth_radius + 1]:
            row = center_row + radius // 2 - 1
            if 0 <= row < self.height and 0 <= col < self.width:
                self.grid[row][col] = False

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

class AlphabetKeyboard(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        layout = QHBoxLayout(self)
        layout.setSpacing(2)

        # Define the 9x5 letter patterns here for drag preview
        self.letter_patterns = {
            'A': [
                "00100",
                "01010",
                "10001",
                "10001",
                "11111",
                "10001",
                "10001",
                "10001",
                "10001"
            ],
            'B': [
                "11100",
                "10010",
                "10001",
                "10001",
                "11110",
                "10001",
                "10001",
                "10010",
                "11100"
            ],
            'C': [
                "01110",
                "10001",
                "10000",
                "10000",
                "10000",
                "10000",
                "10000",
                "10001",
                "01110"
            ],
            'D': [
                "11100",
                "10010",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10010",
                "11100"
            ],
            'E': [
                "11111",
                "10000",
                "10000",
                "10000",
                "11110",
                "10000",
                "10000",
                "10000",
                "11111"
            ],
            'F': [
                "11111",
                "10000",
                "10000",
                "10000",
                "11110",
                "10000",
                "10000",
                "10000",
                "10000"
            ],
            'G': [
                "01110",
                "10001",
                "10000",
                "10000",
                "10011",
                "10001",
                "10001",
                "10001",
                "01110"
            ],
            'H': [
                "10001",
                "10001",
                "10001",
                "10001",
                "11111",
                "10001",
                "10001",
                "10001",
                "10001"
            ],
            'I': [
                "11111",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "11111"
            ],
            'J': [
                "00111",
                "00010",
                "00010",
                "00010",
                "00010",
                "00010",
                "10010",
                "10010",
                "01100"
            ],
            'K': [
                "10001",
                "10010",
                "10100",
                "11000",
                "11000",
                "10100",
                "10010",
                "10001",
                "10001"
            ],
            'L': [
                "10000",
                "10000",
                "10000",
                "10000",
                "10000",
                "10000",
                "10000",
                "10000",
                "11111"
            ],
            'M': [
                "10001",
                "11011",
                "10101",
                "10101",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001"
            ],
            'N': [
                "10001",
                "11001",
                "11001",
                "10101",
                "10101",
                "10011",
                "10011",
                "10001",
                "10001"
            ],
            'O': [
                "01110",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "01110"
            ],
            'P': [
                "11110",
                "10001",
                "10001",
                "10001",
                "11110",
                "10000",
                "10000",
                "10000",
                "10000"
            ],
            'Q': [
                "01110",
                "10001",
                "10001",
                "10001",
                "10001",
                "10101",
                "10011",
                "10001",
                "01111"
            ],
            'R': [
                "11110",
                "10001",
                "10001",
                "10001",
                "11110",
                "10010",
                "10001",
                "10001",
                "10001"
            ],
            'S': [
                "01111",
                "10000",
                "10000",
                "10000",
                "01110",
                "00001",
                "00001",
                "00001",
                "11110"
            ],
            'T': [
                "11111",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100"
            ],
            'U': [
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "01110"
            ],
            'V': [
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "01010",
                "01010",
                "00100"
            ],
            'W': [
                "10001",
                "10001",
                "10001",
                "10001",
                "10101",
                "10101",
                "10101",
                "11011",
                "10001"
            ],
            'X': [
                "10001",
                "10001",
                "01010",
                "01010",
                "00100",
                "01010",
                "01010",
                "10001",
                "10001"
            ],
            'Y': [
                "10001",
                "10001",
                "10001",
                "01010",
                "01010",
                "00100",
                "00100",
                "00100",
                "00100"
            ],
            'Z': [
                "11111",
                "00001",
                "00010",
                "00100",
                "01000",
                "01000",
                "10000",
                "10000",
                "11111"
            ]
        }

        # Create buttons for each letter (A-Z)
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            btn = QPushButton(letter)
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("background-color: #D3D3D3; font-size: 14px;")
            btn.mousePressEvent = lambda event, l=letter: self.start_drag(event, l)
            layout.addWidget(btn)

    def create_letter_pixmap(self, letter):
        # Create a pixmap for the letter (9x5 pixels, scaled up for visibility)
        cell_size = 5  # Smaller cell size for the drag preview
        pixmap = QPixmap(5 * cell_size, 9 * cell_size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        
        pattern = self.letter_patterns[letter]
        for r, row in enumerate(pattern):
            for c, bit in enumerate(row):
                if bit == '1':
                    painter.fillRect(c * cell_size, r * cell_size, cell_size, cell_size, Qt.black)
        
        painter.end()
        return pixmap

    def start_drag(self, event, letter):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(letter)
            drag.setMimeData(mime_data)
            # Set the pixmap to show the letter while dragging
            pixmap = self.create_letter_pixmap(letter)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
            drag.exec_(Qt.CopyAction)

class GridWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.cell_size = 20
        self.setMinimumSize(self.parent.width * self.cell_size, self.parent.height * self.cell_size)
        self.setAcceptDrops(True)

        # 9x5 pixel font for letters A-Z (9 tall, 5 wide)
        self.letter_patterns = {
            'A': [
                "00100",
                "01010",
                "10001",
                "10001",
                "11111",
                "10001",
                "10001",
                "10001",
                "10001"
            ],
            'B': [
                "11100",
                "10010",
                "10001",
                "10001",
                "11110",
                "10001",
                "10001",
                "10010",
                "11100"
            ],
            'C': [
                "01110",
                "10001",
                "10000",
                "10000",
                "10000",
                "10000",
                "10000",
                "10001",
                "01110"
            ],
            'D': [
                "11100",
                "10010",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10010",
                "11100"
            ],
            'E': [
                "11111",
                "10000",
                "10000",
                "10000",
                "11110",
                "10000",
                "10000",
                "10000",
                "11111"
            ],
            'F': [
                "11111",
                "10000",
                "10000",
                "10000",
                "11110",
                "10000",
                "10000",
                "10000",
                "10000"
            ],
            'G': [
                "01110",
                "10001",
                "10000",
                "10000",
                "10011",
                "10001",
                "10001",
                "10001",
                "01110"
            ],
            'H': [
                "10001",
                "10001",
                "10001",
                "10001",
                "11111",
                "10001",
                "10001",
                "10001",
                "10001"
            ],
            'I': [
                "11111",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "11111"
            ],
            'J': [
                "00111",
                "00010",
                "00010",
                "00010",
                "00010",
                "00010",
                "10010",
                "10010",
                "01100"
            ],
            'K': [
                "10001",
                "10010",
                "10100",
                "11000",
                "11000",
                "10100",
                "10010",
                "10001",
                "10001"
            ],
            'L': [
                "10000",
                "10000",
                "10000",
                "10000",
                "10000",
                "10000",
                "10000",
                "10000",
                "11111"
            ],
            'M': [
                "10001",
                "11011",
                "10101",
                "10101",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001"
            ],
            'N': [
                "10001",
                "11001",
                "11001",
                "10101",
                "10101",
                "10011",
                "10011",
                "10001",
                "10001"
            ],
            'O': [
                "01110",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "01110"
            ],
            'P': [
                "11110",
                "10001",
                "10001",
                "10001",
                "11110",
                "10000",
                "10000",
                "10000",
                "10000"
            ],
            'Q': [
                "01110",
                "10001",
                "10001",
                "10001",
                "10001",
                "10101",
                "10011",
                "10001",
                "01111"
            ],
            'R': [
                "11110",
                "10001",
                "10001",
                "10001",
                "11110",
                "10010",
                "10001",
                "10001",
                "10001"
            ],
            'S': [
                "01111",
                "10000",
                "10000",
                "10000",
                "01110",
                "00001",
                "00001",
                "00001",
                "11110"
            ],
            'T': [
                "11111",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100",
                "00100"
            ],
            'U': [
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "01110"
            ],
            'V': [
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "10001",
                "01010",
                "01010",
                "00100"
            ],
            'W': [
                "10001",
                "10001",
                "10001",
                "10001",
                "10101",
                "10101",
                "10101",
                "11011",
                "10001"
            ],
            'X': [
                "10001",
                "10001",
                "01010",
                "01010",
                "00100",
                "01010",
                "01010",
                "10001",
                "10001"
            ],
            'Y': [
                "10001",
                "10001",
                "10001",
                "01010",
                "01010",
                "00100",
                "00100",
                "00100",
                "00100"
            ],
            'Z': [
                "11111",
                "00001",
                "00010",
                "00100",
                "01000",
                "01000",
                "10000",
                "10000",
                "11111"
            ]
        }

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
        if self.parent.current_tool in ["draw", "erase", "line", "circle"]:
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

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        letter = event.mimeData().text()
        if letter in self.letter_patterns:
            row = event.pos().y() // self.cell_size
            col = event.pos().x() // self.cell_size
            self.draw_letter(letter, row, col)
            self.update()
            self.parent.preview_widget.update()

    def draw_letter(self, letter, start_row, start_col):
        pattern = self.letter_patterns[letter]
        for r, row in enumerate(pattern):
            for c, bit in enumerate(row):
                grid_row = start_row + r
                grid_col = start_col + c
                if 0 <= grid_row < self.parent.height and 0 <= grid_col < self.parent.width:
                    self.parent.grid[grid_row][grid_col] = (bit == '1')

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
        
        scaled = image.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
        painter.drawPixmap(0, 0, QPixmap.fromImage(scaled))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POVWandDesigner()
    window.show()
    sys.exit(app.exec_())