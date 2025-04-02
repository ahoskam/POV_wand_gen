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

        # Set the window icon (replace 'pov_wand.ico' with your icon file path)
        self.setWindowIcon(QIcon('pov_wand.ico'))  # Ensure this file exists in the same directory

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
        sr = 1 self.draw_circle(self.grid, 7, 8, 15, 16, True)
        self.draw_circle(self.grid, 4, 5, 5, 7, True)
        self.draw_circle(self.grid, 4, 11, 5, 13, True)
        for col in range(5, 12):
            self.grid[9][col] = True
        for r, c in [(10, 4), (10, 12), (11, 3), (11, 13)]:
            self.grid[r][c] = True
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