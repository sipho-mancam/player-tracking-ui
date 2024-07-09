from PyQt5.QtCore import Qt, QModelIndex, QPoint, QTimer
from PyQt5.QtGui import (QColor, QMouseEvent, QPainter, QPixmap, 
                         QImage, QIcon, QPen, QBrush, QPaintEvent, QPolygon, QResizeEvent)

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
        
        for child in self.children():
            child.resizeEvent(event)

        super().resizeEvent(event)

    def updateScaledPixmap(self):
        if not self.pixmap():
            return
        pixmap = self.pixmap()
        size = self.size()
        scaled_pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled_pixmap)


class Circle(QWidget):
    def __init__(self, x, y, radius,  parent = None,) -> None:
        super().__init__(parent)
        self.setGeometry(x, y, radius*2, radius*2)
        self.__radius = radius
        self.__x = x
        self.__y = y
        self.__color = Qt.blue
        self.__brush = QBrush(self.__color)
        self.__pen = QPen()
        self.__dragging = False
        self.__start_pos =  None
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.perform_move)
        self.pending_move_position = None

    @property
    def circle_x(self)->int:
        return self.__x+self.__radius
    
    @property
    def circle_y(self)->int:
        return self.__y + self.__radius

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event.button() == Qt.LeftButton:
            self.__brush.setColor(Qt.red)
            self.__dragging = True
            self.__start_pos = event.pos()
            event.accept()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if  self.__dragging:
            self.__brush.setColor(Qt.red)
            self.move(self.mapToParent(event.pos() - self.__start_pos))
            self.__x = self.x()
            self.__y = self.y()
            self.update()
            self.parentWidget().update()
        event.accept()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        self.__brush.setColor(Qt.blue)
        self.__dragging = False
        self.__x = self.x()
        self.__y = self.y()
        event.accept()
        self.update()
        self.parentWidget().update()
        return super().mouseReleaseEvent(event)

    def paintEvent(self, paintEvent:QPaintEvent)->None:
        circle = QPainter(self)
        circle.setRenderHint(QPainter.Antialiasing)
        self.__pen.setWidth(2)
        self.__pen.setColor(Qt.red)
        circle.setBrush(self.__brush)
        circle.setPen(self.__pen)
        rect = self.rect()
        circle.drawEllipse(rect)
        paintEvent.accept()
        return super().paintEvent(paintEvent)

    def perform_move(self)->None:
        if self.__dragging:
            self.move(self.mapToParent(self.pending_move_position - self.__start_pos))

class Polygon(QWidget):
    def __init__(self, points=[], parent = None ) -> None:
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.__rect = parent.rect()
        self.__circle_radii = 10
        self.__circles = []

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        self.__rect = self.parentWidget().rect()
        self.resize(self.parentWidget().size())
       

    def paintEvent(self, paintEvnet:QPaintEvent)->None:
        painter = QPainter(self)
        pen = QPen(QColor("#0000ff"), 3, Qt.SolidLine)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        # Define the points of the polygon
        if len(self.__circles) == 0:
            points = [
                QPoint(50, 50),
                QPoint(self.__rect.width()-100, 100),
                QPoint(self.__rect.width()-100, self.__rect.height()-100),
                QPoint(50, self.__rect.height()-100),
            ]
            for point in points:
                self.__circles.append(Circle(int(point.x()), int(point.y()), self.__circle_radii , self))
        else:
            points = []
            for circle in self.__circles:
                # print(circle.circle_x, circle.circle_y)
                points.append(
                    QPoint(circle.circle_x, circle.circle_y)
                )
        # Create a QPolygon object
        polygon = QPolygon(points)
        # Draw the polygon
        painter.drawPolygon(polygon)

        for circle in self.__circles:
            circle.show()
        return super().paintEvent(paintEvnet)

    def get_normalize_coordinates(self)->list[tuple[float]]:
        pass


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

        poly = Polygon([], self.__frame_widget)

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