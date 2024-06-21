import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtXml import QDomDocument
from PyQt5.QtCore import Qt
from src.cfg.paths_config import __ASSETS_DIR__

class SvgManipulator(QWidget):
    def __init__(self, jersey_number, color, parent=None):
        super().__init__(parent)
        self.svg_path = (__ASSETS_DIR__ / 'jersey.svg').resolve().as_posix()

        # Load SVG content into QDomDocument
        self.dom_document = QDomDocument()
        with open(self.svg_path, 'r') as f:
            self.dom_document.setContent(f.read())
        # Manipulate the SVG DOM
        self.set_color(f"{color}")
        self.set_jersey_number(f"{jersey_number}")
        # Render the manipulated SVG
        self.renderer = QSvgRenderer(self.dom_document.toByteArray())
        # Setup UI
        self.init_ui()

    def set_color(self, color:str)->None:
        elems = self.dom_document.elementsByTagName('polygon')
        for i in range(elems.count()):
            elem = elems.item(i).toElement()
            elem.setAttribute('fill', color)
    
    def set_jersey_number(self, number:int|str)->None:
        elements = self.dom_document.elementsByTagName("text")
        for i in range(elements.count()):
            element = elements.item(i).toElement()
            element.setAttribute("fill", "white")
            element.firstChild().setNodeValue(f"{number}")
            

    def init_ui(self):
        layout = QVBoxLayout(self)
        # Create a QLabel to display the SVG
        self.label = QLabel()
        layout.addWidget(self.label)
        # Render the SVG to a QPixmap and display it
        pixmap = QPixmap(400, 400)  # Specify the desired size
        pixmap.fill(Qt.transparent)  # Ensure the background is transparent
        painter = QPainter(pixmap)
        self.renderer.render(painter)
        painter.end()
        self.label.setPixmap(pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    svg_path = r"C:\Users\sipho-mancam\Documents\Programming\python\yolov8-python\UI\assets\Jersey.svg"
    window = SvgManipulator(14, 'red')
    window.show()

    sys.exit(app.exec_())
