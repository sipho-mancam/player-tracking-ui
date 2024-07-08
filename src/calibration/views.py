from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QColor, QPainter, QPixmap, QImage, QIcon
from PyQt5.QtWidgets import (QWidget, QApplication, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QStyle, QStyleOption,QSizePolicy,
                             QLabel, QListWidgetItem)
import sys
import cv2 as cv
from pathlib import Path


__ASSETS_DIR__ = Path(".\\assets")

class FrameViewResize(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__pixmap = QPixmap(640, 480)
        # self.__pixmap.setDevicePixelRatio(1)
        self.setScaledContents(True)
        self.setPixmap(self.__pixmap)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def resizeEvent(self, event)->None:
        self.updateScaledPixmap()
        super().resizeEvent(event)

    def updateScaledPixmap(self):
        if not self.pixmap():
            return
        
        pixmap = self.pixmap()
        size = self.size()
        scaled_pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled_pixmap)


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
        self.__frame_widget = FrameViewResize()
        self.__frame_widget.setMinimumHeight(480)
        self.__frame_widget.setMinimumWidth(640)

        buttons_container = QVBoxLayout()
        self.__bb_btn = QPushButton("Set Bounding Box")
        self.__plgn_btn = QPushButton("Set Polygons")
        self.__save_btn = QPushButton("Save Calib")

        buttons_container.addWidget(self.__bb_btn)
        buttons_container.addWidget(self.__plgn_btn)
        buttons_container.addWidget(self.__save_btn)
        buttons_container.setAlignment(Qt.AlignTop)

        self.__main_layout.addWidget(self.__frame_widget, 20)
        self.__main_layout.addLayout(buttons_container, 1)
        self.__main_layout.setAlignment(Qt.AlignTop)
        
    def paintEvent(self, paint_event)->None:
        style_op = QStyleOption()
        style_op.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, style_op, painter, self)
        painter.setRenderHint(QPainter.Antialiasing)

    def update_frame(self, frame:cv.Mat)->None:
        h, w, d = frame.shape
        row_bytes = w * 3
        image = QImage(frame.data, w, h, row_bytes,  QImage.Format_BGR888)
        pix_map = QPixmap.fromImage(image)
        pix_map.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.__frame_widget.setPixmap(pix_map)


class CalibrationPage(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setGeometry(100,100, 800, 400)
        self.__main_layout = QVBoxLayout(self)
        self.__top_bar = QHBoxLayout()
        self.__middle_layout = QHBoxLayout()
        self.__bottom_layout = QHBoxLayout()
        self.__bottom_bar = QHBoxLayout()

        self.__clear_all_btn = QPushButton('Clear All')
        self.__save_btn = QPushButton("Save")

        self.displayWidget = CameraCalibrationWidget()

        self.init()
        self.setLayout(self.__main_layout)
        self.__controller = None

    def set_controller(self, controller)->None:
        self.__controller = controller

    def update_frame(self, frame:cv.Mat)->None:
        self.displayWidget.update_frame(frame)
        

    def init(self)->None:
        self.__main_layout.setAlignment(Qt.AlignTop)

        self.__top_bar.setAlignment(Qt.AlignRight)
        self.__top_bar.addWidget(self.__save_btn)
        self.__top_bar.addWidget(self.__clear_all_btn)

        self.initMiddle()
        
        self.__main_layout.addLayout(self.__top_bar)
        self.__main_layout.addLayout(self.__middle_layout)
        self.__main_layout.addLayout(self.__bottom_layout)

    def list_click_listener(self, event:QModelIndex)->None:
        i_type = event.data(3)
        if i_type is not None and i_type == 1: # It's a camera item
            cam_id = event.data(4)
            if self.__controller is not None:
                self.__controller.select(cam_id)


    def initMiddle(self)->None:
        self.__options_list = QListWidget()

        self.__options_list.addItem("General")

        cam_icon_path = (__ASSETS_DIR__ / 'camera_icon.svg').resolve().as_posix()
        cam_icon = QIcon(cam_icon_path)
        for idx in range(3):
            cam = QListWidgetItem(self.__options_list)
            cam.setData(0, f"Cam {idx+1}")
            # cam.setData(1, idx)
            cam.setData(3, 1)# THis shows us the type of item clicked. 1 is for camera
            cam.setData(4, idx)
            cam.setIcon(cam_icon)
            self.__options_list.addItem(cam)

        self.__options_list.addItem("Iteractive Alignment")

        self.__options_list.clicked.connect(self.list_click_listener)
        self.__options_list.setFixedWidth(200)

        

        self.__middle_layout.addWidget(self.__options_list)
        self.__middle_layout.addWidget(self.displayWidget)





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalibrationPage()
    window.show()
    app.exec()