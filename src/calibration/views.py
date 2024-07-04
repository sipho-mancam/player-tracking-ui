from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtWidgets import (QWidget, QApplication, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QStyle, QStyleOption,
                             QLabel)
import sys



class CameraCalibrationWidget(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("""
                CameraCalibrationWidget {
                        border:1px solid grey;
                        background-color: #ffffff;
                        width: 100%;
                    }
            """)
        
        self.__main_layout = QHBoxLayout()
        
        self.init()
        self.setLayout(self.__main_layout)

    def init(self)->None:
        self.__frame_widget = QLabel()
        self.__frame_widget.setMinimumHeight(480)
        self.__frame_widget.setMinimumWidth(640)
        pix_map = QPixmap(640, 480)
        pix_map.fill(QColor('#000'))
        self.__frame_widget.setPixmap(pix_map)

        buttons_container = QVBoxLayout()
        self.__bb_btn = QPushButton("Set Bounding Box")
        self.__plgn_btn = QPushButton("Set Polygons")
        self.__save_btn = QPushButton("Save Calib")

        buttons_container.addWidget(self.__bb_btn)
        buttons_container.addWidget(self.__plgn_btn)
        buttons_container.addWidget(self.__save_btn)
        buttons_container.setAlignment(Qt.AlignTop)



        self.__main_layout.addWidget(self.__frame_widget)
        self.__main_layout.addLayout(buttons_container)
        self.__main_layout.setAlignment(Qt.AlignTop)
        
    def paintEvent(self, paint_event)->None:
        style_op = QStyleOption()
        style_op.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, style_op, painter, self)
        painter.setRenderHint(QPainter.Antialiasing)


class CalibrationPage(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setGeometry(100,100, 800, 400)
        self.__main_layout = QVBoxLayout(self)
        self.__top_bar = QHBoxLayout()
        self.__middle_layout = QHBoxLayout()
        self.__bottom_layout = QHBoxLayout()

        self.__clear_all_btn = QPushButton('Clear All')
        self.__save_btn = QPushButton("Save")


        self.init()

        self.setLayout(self.__main_layout)
        

    def init(self)->None:
        self.__main_layout.setAlignment(Qt.AlignTop)

        self.__top_bar.setAlignment(Qt.AlignRight)
        self.__top_bar.addWidget(self.__save_btn)
        self.__top_bar.addWidget(self.__clear_all_btn)

        self.initMiddle()
        
        self.__main_layout.addLayout(self.__top_bar)
        self.__main_layout.addLayout(self.__middle_layout)
        self.__main_layout.addLayout(self.__bottom_layout)
       

    def initMiddle(self)->None:
        self.__options_list = QListWidget()

        self.__options_list.addItem("General")
        self.__options_list.addItem("Cam 1")
        self.__options_list.addItem("Cam 2")
        self.__options_list.addItem("Cam 3")
        self.__options_list.addItem("Iteractive Alignment")
        self.__options_list.setFixedWidth(200)


        self.displayWidget = CameraCalibrationWidget()

        self.__middle_layout.addWidget(self.__options_list)
        self.__middle_layout.addWidget(self.displayWidget)





if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = CalibrationPage()
    window.show()

    app.exec()