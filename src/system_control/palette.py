import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, 
                             QPushButton, QColorDialog, QVBoxLayout, 
                             QDialog, QGridLayout, QScrollArea, QFrame, QHBoxLayout)
from PyQt5.QtGui import QColor, QPalette 
from PyQt5.QtCore import Qt

class ColorPalette(QDialog):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        self.selected_color = None
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        
        for index, color in enumerate(self.colors):
            label = QLabel()
            label.setAutoFillBackground(True)
            palette = label.palette()
            palette.setColor(QPalette.Window, QColor(color))
            label.setPalette(palette)
            label.setFrameStyle(QFrame.Box | QFrame.Plain)
            label.setLineWidth(2)
            label.mousePressEvent = self.createMousePressEvent(color)
            row = index // 10
            col = index % 10
            layout.addWidget(label, row, col)
        
        container = QWidget()
        container.setLayout(layout)
        
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(container)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(scrollArea)
        self.setLayout(mainLayout)
        
        self.setWindowTitle('Color Palette')
        self.setFixedSize(600, 400)

    def createMousePressEvent(self, color):
        def mousePressEvent(event):
            self.selected_color = color
            self.accept()
        return mousePressEvent

class ColorPickerApp(QDialog):
    def __init__(self, colors = [], selected_colors={}, parent=None):
        super().__init__(parent)
        self.selected_colors=selected_colors
        self.colors_ = colors
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Color Picker')
        self.setGeometry(100, 100, 300, 200)
        
        self.colors_selected = 0
        self.boxes = {
            "background_color": None,
            "team_a": None,
            "team_b": None
        }
        
        layout = QHBoxLayout()
        
        for label in self.boxes.keys():
            box = QLabel(label, self)
            box.setStyleSheet("background-color: white; border: 1px solid black;")
            box.setFixedSize(200, 50)
            box.mousePressEvent = lambda event, lbl=label: self.launch_color_palette(lbl)
            layout.addWidget(box)
            self.boxes[label] = box
        
        self.close_button = QPushButton('save', self)
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)
        
        self.setLayout(layout)
        self.setWindowModality(Qt.ApplicationModal)  # Make the window modal

    def launch_color_palette(self, label):
        dialog = ColorPalette(self.colors_, self)
        if dialog.exec_() == QDialog.Accepted:
            self.boxes[label].setStyleSheet(f"background-color: {dialog.selected_color}; border: 1px solid black;")
            self.selected_colors[label] = dialog.selected_color
            self.colors_selected += 1
            if self.colors_selected == 3:
                self.enable_close()

    def enable_close(self):
        self.close_button.setEnabled(True)

    def closeEvent(self, event):
        if self.colors_selected < 3:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    colors = [f'#{i:02x}{j:02x}{k:02x}' for i in range(0, 256, 51) for j in range(0, 256, 51) for k in range(0, 256, 51)][:10]  # Generate 100 colors
    dialog = ColorPickerApp(colors)
    if dialog.exec_() == QDialog.Accepted:
        selected_colors = dialog.selected_colors
        print("Selected Colors:", selected_colors)
