import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Draw Circle Example")
        self.setGeometry(100, 100, 400, 300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        painter.setPen(pen)
        
        brush = QColor(Qt.blue)
        painter.setBrush(brush)
        
        # Draw a circle at position (100, 100) with radius 50
        painter.drawEllipse(100, 100, 50, 50)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
