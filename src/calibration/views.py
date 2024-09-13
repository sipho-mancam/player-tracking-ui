from PyQt5.QtCore import Qt, QModelIndex, QPoint, QTimer, QRect
from PyQt5.QtGui import (QColor, QMouseEvent, QPainter, QPixmap, 
                         QImage, QIcon, QPen, QBrush, QPaintEvent, QPolygon, QResizeEvent)

from PyQt5.QtWidgets import (QWidget, QApplication, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QStyle, QStyleOption,QSizePolicy,
                             QLabel, QListWidgetItem)
import sys
import cv2 as cv
from pathlib import Path
import random


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
        self.__triggered = False

        parent_rect = self.parentWidget().rect()
        self.x_lower_limit = parent_rect.x()
        self.y_lower_limit = parent_rect.y()
        self.x_upper_limit = parent_rect.width()
        self.y_upper_limit = parent_rect.height()

    def set_xy_pos(self, xy_p:tuple): 
        self.__x = int(abs(xy_p[0] - self.__radius))
        self.__y = int(abs(xy_p[1] - self.__radius))
        rect = QRect(self.__x, self.__y, self.__radius * 2, self.__radius*2)
        self.setGeometry(rect)


    @property
    def circle_x(self)->int:
        return self.__x + self.__radius
    
    @property
    def circle_y(self)->int:
        return self.__y + self.__radius

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        parent_rect = self.parentWidget().rect()
        self.x_lower_limit = parent_rect.x()
        self.y_lower_limit = parent_rect.y() 
        self.x_upper_limit = parent_rect.width() 
        self.y_upper_limit = parent_rect.height() 

        if event.button() == Qt.LeftButton:
            self.__brush.setColor(Qt.red)
            self.__dragging = True
            self.__start_pos = event.pos()

            const = 20 + self.__radius
            if self.__triggered:
                x = self.x_lower_limit +  const if self.x() <= self.x_lower_limit else self.x() 
                x = self.x_upper_limit - const if x >= self.x_upper_limit else x
                y = self.y_lower_limit + const if self.y() <= self.y_lower_limit else self.y()
                y = self.y_upper_limit - const if y >= self.y_upper_limit else y
                self.__triggered = False
                self.set_xy_pos((x, y))

            event.accept()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if  self.__dragging:
            self.__brush.setColor(Qt.red)
            if (self.x() >= self.x_lower_limit and self.y() >= self.y_lower_limit and self.x() < self.x_upper_limit  and self.y() < self.y_upper_limit):
                self.move(self.mapToParent(event.pos() - self.__start_pos))
                self.__x = self.x()
                self.__y = self.y()
                self.update()
                self.parentWidget().update()
            else:
                self.__triggered = True
        
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
    def __init__(self, points=[], parent = None, filled = False,) -> None:
        super().__init__(parent)
        self.__poly_points_n = points
        self.__rect = None
        # self.calculate_widget_rect()
        self.__rect = self.parentWidget().rect()
        self.setGeometry(self.parentWidget().rect())
        self.__circle_radii = 10
        self.__circles = []
        self.__poly_points  = []
        self.__fill = filled
        self.update_polygon(points)
        self.setVisible(True)
        
        self.__id  = random.randint(0, 100)
    
    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        self.click_handle()
        return super().mousePressEvent(a0)
    

    def calculate_widget_rect(self)->None:
        """
        1. First get the enclosing rectangle
        2. 
        """
        p_rect = self.parentWidget().rect()
        p_width = p_rect.width()
        p_height = p_rect.height()

        x_list , y_list = [], []

        for point in self.__poly_points_n:
            x_n, y_n = point
            x_list.append(x_n)
            y_list.append(y_n)

        x_t = round(min(x_list) * p_width)
        y_t = round(min(y_list) * p_height)

        x_b = round(max(x_list) * p_width)
        y_b = round(max(y_list)  *p_height)
        self.__rect = QRect(QPoint(x_t, y_t), QPoint(x_b, y_b))


    def set_full_size_rect(self)->None:
        """
        1. This sets the widget to currently fill the whole view port
        """
        print("I execute \{set_full_size_rect\}")
        self.__rect = self.parentWidget().rect()
        self.setGeometry(self.__rect)
        # self.resize(self.parentWidget().size())
        self.updateGeometry()
    
    def clear_full_size_rect(self)->None:
        print("I execute {clear_full_size_rect()}")
        self.calculate_widget_rect()
        self.setGeometry(self.__rect)
        # self.resize(self.__rect.width(), self.__rect.height())
        self.updateGeometry()


    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        self.__rect  = self.parentWidget().rect()
        self.resize(self.parentWidget().size())
        self.update_polygon(self.__poly_points_n)
        self.update()

    def update_polygon(self, points:list[tuple[float]])->None:
        self.__poly_points = []
        self.__poly_points_n = points

        width = self.__rect.width()
        height = self.__rect.height()

        for i, point in enumerate(self.__poly_points_n):
            xpos , ypos = point
            xpos *= width
            ypos *= height
            self.__poly_points.append((round(xpos), round(ypos)))
            if len(self.__circles) < 4:
                self.__circles.append(Circle(int(xpos), int(ypos), self.__circle_radii, self))
            else:
                self.__circles[i].set_xy_pos((xpos, ypos))

       
    def paintEvent(self, paintEvnet:QPaintEvent)->None:
        painter = QPainter(self)
        pen = QPen(QColor("#0000ff"), 3, Qt.SolidLine)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        # Define the points of the polygon
        if len(self.__circles) == 0:
            points = [
                QPoint(*self.__poly_points[0]),
                QPoint(*self.__poly_points[1]),
                QPoint(*self.__poly_points[2]),
                QPoint(*self.__poly_points[3])
            ]
            for point in points:
                self.__circles.append(Circle(int(point.x()), int(point.y()), self.__circle_radii , self))
        else:
            self.__poly_points = []
            points = []
            for circle in self.__circles:

                # print("X: {} Y: {}".format(circle.circle_x, circle.circle_y))
                points.append(
                    QPoint(circle.circle_x, circle.circle_y)
                )
                self.__poly_points.append(
                    (circle.circle_x, circle.circle_y)
                )
            # print("\n\n\n")
            self.normalize_coordinates()
        # Create a QPolygon object
        polygon = QPolygon(points)
        # Draw the polygon
        if self.__fill:
            painter.setBrush(QColor(0, 0, 0))

        painter.drawPolygon(polygon, Qt.OddEvenFill)
        # print(self.__poly_points_n)
        for circle in self.__circles:
            circle.show()
        return super().paintEvent(paintEvnet)

    def normalize_coordinates(self)->None:
        width = self.__rect.width()
        height = self.__rect.height()
        self.__poly_points_n = []

        for point in self.__poly_points:
            x, y = point
            self.__poly_points_n.append((x/width, y/height))

    def get_normalize_coordinates(self)->list[tuple[float]]:
        return self.__poly_points_n
    
    def click_handle(self)->None:
        print(f"Polygon clicked ... {self.__id}")

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
        self.__current_poly = None
        self.init()
        self.setLayout(self.__main_layout)
        self.__current_calib_data = None        
        self.__polygons_list = []

    def init(self)->None:
        self.__frame_widget = FrameViewResize()
        self.__frame_widget.setMinimumHeight(480)
        self.__frame_widget.setMinimumWidth(640)

        self.__current_poly = Polygon([(0,0), (0.9, 0), (0.9,0.9), (0, 0.9)], self.__frame_widget)

        buttons_container = QVBoxLayout()
        self.__bb_btn = QPushButton("Add Bounding Box")
        self.__plgn_btn = QPushButton("Add Mask") # This add a filled Polygon
        # self.__save_btn = QPushButton("Save Calib")

        self.__plgn_btn.clicked.connect(self.add_mask_poly)

        buttons_container.addWidget(self.__bb_btn)
        buttons_container.addWidget(self.__plgn_btn)
        # buttons_container.addWidget(self.__save_btn)
        buttons_container.setAlignment(Qt.AlignTop)

        self.__main_layout.addWidget(self.__frame_widget, 20)
        self.__main_layout.addLayout(buttons_container, 1)
        self.__main_layout.setAlignment(Qt.AlignTop)

    def update_boundary_coordinates(self, boundary_coordinates)->None:
        pass

    def add_mask_poly(self)->None:
        self.__polygons_list.append(
            Polygon([(0.3,0.3), (0.5, 0.3), (0.5,0.5), (0, 0.5)], self.__frame_widget, True)
        )
        self.__frame_widget.update()
        
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

    def update_calibration_data(self, calib)->None:
        self.__current_calib_data  = calib
        self.__current_poly.update_polygon(self.__current_calib_data["poly_points"])
        self.update()

    def get_calibration_data(self)->dict:
        if self.__current_calib_data is None:
            return {}
        
        self.__current_calib_data["poly_points"] = self.__current_poly.get_normalize_coordinates()
        return self.__current_calib_data

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
    
    def set_camera_data(self, cam_calib_data)->None:
        self.displayWidget.update_calibration_data(cam_calib_data)

    def get_camera_data(self)->dict:
        return self.displayWidget.get_calibration_data()
    
    def save_calib(self)->None:
        if self.__controller is None:
            return
        self.__controller.save_current_cam_calib()

    def update_frame(self, frame:cv.Mat)->None:
        self.displayWidget.update_frame(frame)

    def update_boundary_poly(self, poly_points)->None:
        pass
        

    def init(self)->None:
        self.__main_layout.setAlignment(Qt.AlignTop)
        self.__top_bar.setAlignment(Qt.AlignRight)
        self.__top_bar.addWidget(self.__save_btn)
        self.__top_bar.addWidget(self.__clear_all_btn)

        self.initMiddle()
        
        self.__main_layout.addLayout(self.__top_bar)
        self.__main_layout.addLayout(self.__middle_layout)
        self.__main_layout.addLayout(self.__bottom_layout)

        self.__save_btn.clicked.connect(self.save_calib)

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