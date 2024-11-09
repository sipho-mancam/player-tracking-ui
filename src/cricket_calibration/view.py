from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import (QPixmap, QImage, QMouseEvent, QPainter, QPen, QBrush, 
                         QPolygon, QResizeEvent)
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                             QHBoxLayout, QSizePolicy, QPushButton, QDialog, QLayout)
import cv2 as cv
from .controller import CalibrationController
import numpy as np
from pathlib import Path
from cfg.paths_config import __WHITE_BG__, __GREEN_BG__

class PolygonDrawer(QLabel):
    def __init__(self, frame:cv.Mat, controller:CalibrationController, parent=None):
        super().__init__(parent)
        # Initialize state
        self.is_interactive = True
        self.selected_point = None
        self.point_radius = 10  # Radius of the circles around points
        self.saved_points = []  # List to store saved points as tuples
        self.__size = (940, 705)#(round(1920*.65), round(1080*.7))
        self.__current_frame = cv.resize(frame, self.__size)
        self.__normalized_poly_points = []
        self.__alignment_points = []
        self._add_alignment_points = False
        self.default_polygon()  # Set the default polygon
        self.pixmap_ = None
        self.update_frame(frame)
        self.setPixmap(self.pixmap_)
        self._controller = controller

    def clear_calibration(self)->None:
        self.__alignment_points.clear()
        self.__normalized_poly_points.clear()
        self._controller.set_alignment_pts(self.normalize_alignment_points())
        self.default_polygon()
        self._controller.update_src_poly(self.generate_updated_points())
        self.update_polygon()
    
    def toggle_alignment_points(self)->None:
        self._add_alignment_points = not self._add_alignment_points
        self.update_polygon()

    def generate_updated_points(self)->np.ndarray:
        self.__normalized_poly_points.clear()
        for point in self.points:
            x, y = point.x(), point.y()
            self.__normalized_poly_points.append(
                (x/self.__size[0], y/self.__size[1])
            )
        return np.array(self.__normalized_poly_points, dtype=np.float32)
    
    def normalize_alignment_points(self)->np.ndarray:
        result = []
        for point in self.__alignment_points:
            x, y = point.x(), point.y()
            result.append(
                (x/self.__size[0], y/self.__size[1])
            )
        return np.array(result, dtype=np.float32)
    
    def set_polygon(self, poly:np.ndarray)->None:
        if poly.shape[0] == 0:
            self.default_polygon()
            self.update_polygon()
            return
        
        self.points.clear()
        poly = np.array(poly)
        poly *= self.__size
        poly = np.round(poly).astype(np.int32)
        for point in poly:
            x, y = point
            self.points.append(
                QPoint(x, y)
            )
        self.update_polygon()

    def set_alignment_points(self, points:np.ndarray)->None:
        self.__alignment_points.clear()
        if points.shape[0] == 0:
            return
        points *= self.__size
        points = np.round(points).astype(np.int32)
        # self.__alignment_points.clear()
        for point in points:
            x, y = point
            self.__alignment_points.append(
                QPoint(x, y)
            )
        

    def default_polygon(self):
        """Set default polygon points."""
        height, width, _ = self.__current_frame.shape
        x, y, width, height = width//2, height//2, 200, 200
        self.points = [
            QPoint(x, y),  # Top-left
            QPoint(x + width, y),  # Top-right
            QPoint(x + width, y + height),  # Bottom-right
            QPoint(x, y + height)  # Bottom-left
        ]

    def save_points(self):
        """Save current polygon points as a list of tuples."""
        self.saved_points = [(point.x(), point.y()) for point in self.points]
        # QMessageBox.info
        print("Saved Points:", self.saved_points)  # Print the saved points

    def mousePressEvent(self, event):
        """Handle mouse press to start dragging a point."""

        if self._add_alignment_points:
            if event.button() == Qt.LeftButton:
                pos = self.mapFrom(self, event.pos())
                self.__alignment_points.append(pos)
                self.update_polygon()
                self._controller.set_alignment_pts(self.normalize_alignment_points())
                event.accept()
                return

        if self.is_interactive:
            pos = self.mapFrom(self, event.pos())
            
            for i, point in enumerate(self.points):
                # print((pos-point).manhattanLength(), self.point_radius)
                if (pos - point).manhattanLength() <= self.point_radius:
                    self.selected_point = i  # Select the point for dragging
                    break

    def mouseMoveEvent(self, event):
        """Handle mouse move to drag a selected point."""
        if self.is_interactive and self.selected_point is not None:
            pos = self.mapFrom(self, event.pos())
            # Update the position of the selected point
            self.points[self.selected_point] = pos
            # print(f"Updated Poly Points: {self.generate_updated_points()}")
            self._controller.update_src_poly(self.generate_updated_points())
            self.update_polygon()

    def mouseReleaseEvent(self, event):
        """Release the selected point after dragging."""
        self.selected_point = None

    def update_polygon(self):
        """Draw polygon on QLabel with draggable points."""
        if self.pixmap_:
            temp_pixmap = self.pixmap_.copy()
            painter = QPainter(temp_pixmap)
            
            pen = QPen(Qt.red, 3) if not self._add_alignment_points else QPen(Qt.gray, 3)
            painter.setPen(pen)

            # Draw polygon if we have at least 2 points
            if len(self.points) > 1:
                polygon = QPolygon(self.points)
                painter.drawPolygon(polygon)

            # Draw circles around points to indicate they can be moved
            brush = QBrush(Qt.blue) if not self._add_alignment_points else QBrush(Qt.gray)
            painter.setBrush(brush)
            for point in self.points:
                painter.drawEllipse(point, self.point_radius, self.point_radius)
            self.draw_points(painter)

            painter.end()
            self.setPixmap(temp_pixmap)

    def draw_points(self, painter:QPainter)->None:
        pen = QPen(Qt.green, 3)
        painter.setPen(pen)

        brush = QBrush(Qt.green)
        painter.setBrush(brush)

        for point in self.__alignment_points:
            painter.drawEllipse(point, self.point_radius-3, self.point_radius-3)

    def keyPressEvent(self, event):
        """Reset polygon if 'R' is pressed."""
        if event.key() == Qt.Key_R:
            self.points.clear()
            self.default_polygon()  # Reset to default polygon

    def update_frame(self, frame:cv.Mat)->None:
        # Every call to this function has implications that we are changing cameras
        self.__current_frame = frame.copy()
        self.__current_frame = cv.resize(self.__current_frame, self.__size)
        self.__update_pix_map()
        self.update_polygon()

    def __update_pix_map(self)->None:
        if self.__current_frame is None:
            return
        height, width, _ = self.__current_frame.shape
        self.__image = QImage(self.__current_frame.data, width, height,
                              self.__current_frame.nbytes//self.__current_frame.shape[0], QImage.Format_BGR888)
        self.pixmap_ = QPixmap.fromImage(self.__image)
        self.setPixmap(self.pixmap_)
        self.update()

class FrameView(QLabel):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.__current_frame = None
        self.setWindowTitle("FrameView")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.__scale = 0.7
        self.__size = (round(1920*self.__scale), round(1080*self.__scale))
        self.setFixedSize(*self.__size)

    def __update_pix_map(self)->None:
        if self.__current_frame is None:
            return
        self.__current_frame = cv.resize(self.__current_frame, self.__size)
        self.__pix_map = None
        self.__image = QImage(self.__current_frame.data, *self.__size,
                              self.__current_frame.nbytes//self.__current_frame.shape[0], QImage.Format_BGR888)
        self.__pix_map = QPixmap.fromImage(self.__image)
        self.setPixmap(self.__pix_map)
        self.update()

    def update_frame(self, frame:cv.Mat)->None:
        self.__current_frame = frame.copy()
        self.__update_pix_map()


class CameraSelectorObject(QLabel):
    def __init__(self, id, parent = None):
        super().__init__(parent)
        self.__id = id
        self.__frame_thumbnail = QLabel()
        # Set a black default thumbnail
        self.__size = (150, 100)
        black = np.zeros((120, 150, 3), dtype=np.int8)
        image = QImage(black.data, *self.__size, black.nbytes//self.__size[1], QImage.Format_BGR888)
        self.__frame_thumbnail.setPixmap(QPixmap.fromImage(image))
        self.__text_label = QLabel(f"Camera {self.__id + 1}")
        
        self.__layout = QVBoxLayout()
        self.__layout.addWidget(self.__frame_thumbnail)
        self.__layout.addWidget(self.__text_label)
        self.__text_label.setAlignment(Qt.AlignHCenter)
        self.__frame_thumbnail.setAlignment(Qt.AlignHCenter)
        self.__selected = False
        self.setFixedSize(*self.__size)
        self.setLayout(self.__layout)
        self.setObjectName("CameraSelector")
        self.setStyleSheet("""
            #CameraSelector:hover{
                border:4px solid #000000;
                border-style: outset;
            }
        """)
        self.__is_clicked_flag = False

    def mousePressEvent(self, ev:QMouseEvent):
        if ev.button() == Qt.LeftButton:
            self.clicked_event()
        return super().mousePressEvent(ev)

    def clicked_event(self):
        self.__is_clicked_flag = True

    def clear_click_state(self):
        self.__is_clicked_flag = False
        if not self.__selected:
            self.setStyleSheet("""
                #CameraSelector{
                    border:none;
                    border-style: outset;
                }
                #CameraSelector:hover{
                    border:4px solid #000000;
                    border-style: outset;
                }
            """)


    def is_clicked(self):
        return self.__is_clicked_flag

    def set_selected(self)->None:
        self.__selected = True
        self.update_selection_state()

    def clear_selected(self)->None:
        self.__selected = False
        self.update_selection_state()


    def update_selection_state(self):
        if self.__selected:
            self.setStyleSheet("""
                #CameraSelector{
                    border:4px solid black;
                    border-style: outset;
                }
                #CameraSelector:hover{
                    border:4px solid #000000;
                    border-style: outset;
                }
            """)
        else:
            self.setStyleSheet("""
                #CameraSelector{
                    border:none;
                    border-style: outset;
                }
                #CameraSelector:hover{
                    border:4px solid #000000;
                    border-style: outset;
                }
            """)

    def update_thumbnail(self, frame:cv.Mat)->None:
        frame = frame.copy()
        frame = cv.resize(frame, self.__size)
        image = QImage(frame.data, *self.__size,
                              frame.nbytes//frame.shape[0], QImage.Format_BGR888)
        self.__frame_thumbnail.setPixmap(QPixmap.fromImage(image))

class CameraSelector(QWidget):
    def __init__(self, controller, parent = None):
        super().__init__(parent)
        self.__layout = QHBoxLayout()
        self.__camera_widgets = [
            CameraSelectorObject(0, self),
            CameraSelectorObject(1, self),
            CameraSelectorObject(2, self)
        ]

        for object in self.__camera_widgets:
            object.clear_click_state()
            self.__layout.addWidget(object)
        self.__active_object = 0
        self.__camera_widgets[self.__active_object].set_selected()
        self.setLayout(self.__layout)
        self._controller = controller

    def mousePressEvent(self, event:QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.handle_click()
            event.accept()
        return super().mousePressEvent(event)

    def handle_click(self)->None:
        for i, cam_obj in enumerate(self.__camera_widgets):
            if cam_obj.is_clicked():
                self.select(i)
                cam_obj.set_selected()
        for cam_obj in self.__camera_widgets:
            if not cam_obj.is_clicked():
                cam_obj.clear_selected()
            cam_obj.clear_click_state()


    def update_thumbnail(self, frame:cv.Mat)->None:
        cam_object =  self.__camera_widgets[self.__active_object]
        cam_object.update_thumbnail(frame)

    def select(self, id)->None:
        self.__active_object = id
        self._controller.select(self.__active_object)


class PerspectiveView(QWidget):
    def __init__(self, white_bg:cv.Mat, controller:CalibrationController, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Perspective View")
        self.setStyleSheet("""
            *{
                font-size:16px;
            }
            PerspectiveView QLable{
                font-weight: 600;
            }
        """)
        self.__src_poly_view = QLabel()
        self.__src_pixmap = None
        self.__dst_pixmap = None
        self.__dst_poly_view = QLabel()
        self.__white_bg = white_bg
        self._scale = 0.4
        self.__size = (round(1920*self._scale), round(1080*self._scale))
        self._controller = controller
        self._src_poly = self._controller.get_src_poly()
        self.initUI()

    def initUI(self)->None:
        src_bg = cv.resize(self.__white_bg, self.__size).copy()
        h, w, _ = src_bg.shape
        image = QImage(src_bg.data, w, h, QImage.Format_BGR888)
        self.__src_poly_view.setPixmap(QPixmap.fromImage(image))
        self.__src_pixmap = self.__src_poly_view.pixmap().copy()

        dst_bg = src_bg.copy()
        h, w, _ = dst_bg.shape
        image = QImage(dst_bg.data, w, h, QImage.Format_BGR888)
        self.__dst_poly_view.setPixmap(QPixmap.fromImage(image))
        self.__dst_pixmap = self.__dst_poly_view.pixmap().copy()

        right_arrow = QLabel()
        image = QImage(Path("./Assets/right_arrow.png").resolve().as_posix())#, w, h, QImage.Format_BGR888)
        image = image.scaledToWidth(50)
        image = image.scaledToHeight(50)
        right_arrow.setPixmap(QPixmap.fromImage(image))

        self.main_layout = QVBoxLayout()

        self.cam_title_text = QLabel("Camera 1")
        self.main_layout.addWidget(self.cam_title_text)
        self.cam_title_text.setAlignment(Qt.AlignHCenter)

        self._layout = QHBoxLayout()

        self.world_title = QLabel("World Space")
        self.virtual_title = QLabel("Virtual Space")
 

        left_layout = QVBoxLayout()
        middle_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        left_layout.addWidget(self.world_title)
        left_layout.addWidget(self.__src_poly_view)

        middle_layout.addWidget(right_arrow)

        right_layout.addWidget(self.virtual_title)
        right_layout.addWidget(self.__dst_poly_view)

        self._layout.addLayout(left_layout)
        self._layout.addLayout(middle_layout)
        self._layout.addLayout(right_layout)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout.setAlignment(Qt.AlignHCenter)
        self.main_layout.addLayout(self._layout)
        self.setLayout(self.main_layout)

        self.setFixedSize(self.sizeHint())
        self.update_view()
        

    def update_view(self)->None:
        self.update_polygon(self._controller.get_src_poly().copy(), 
                            self.__src_poly_view, self.__src_pixmap, 
                            self._controller.get_alignment_pts())
        
        dst_poly = self._controller.get_dst_poly().copy()
        offsets = np.array([
            [0.1, 0.1],
            [-0.1, 0.1],
            [-0.1, -0.1],
            [0.1, -0.1]
        ], dtype=np.float32)
        self.update_polygon(dst_poly, self.__dst_poly_view, self.__dst_pixmap,
                            self._controller.get_transformed_dst_points())

        self.cam_title_text.setText(f"Camera {self._controller.get_current_camera_index()+1}")

        # Update Alignment Points here

    def update_polygon(self, points:np.ndarray, view:QLabel, original_pixmap:QPixmap, align_pts:np.ndarray):
        """Draw polygon on QLabel with draggable points."""
        if points.shape[0] == 0:
            return
        
        points *= self.__size
        points = np.round(points).astype(np.int32)
        point_radius = 5

        points_array = []

        for point in points:
            x, y = point
            points_array.append(
                QPoint(x, y)
            )
        
        if original_pixmap:
            temp_pixmap = original_pixmap.copy()
            painter = QPainter(temp_pixmap)
            pen = QPen(Qt.red, 3)
            painter.setPen(pen)

            # Draw polygon if we have at least 2 points
            if len(points) > 1:
                polygon = QPolygon(points_array)
                painter.drawPolygon(polygon)

            # Draw circles around points to indicate they can be moved
            brush = QBrush(Qt.blue)
            painter.setBrush(brush)
            for point in points_array:
                painter.drawEllipse(point, point_radius, point_radius)

            self.draw_points(painter, point_radius, align_pts)
            painter.end()
            view.setPixmap(temp_pixmap)

    def draw_points(self, painter:QPainter, point_radius, align_pts:np.ndarray)->None:
        alignment_points = align_pts
        if alignment_points.shape[0] == 0:
            return
        
        alignment_points *= self.__size
        alignment_points = np.round(alignment_points).astype(np.int32)
        points = []
        for point in alignment_points:
            x, y = point
            points.append(
                QPoint(x, y)
            )
        for point in points:
            painter.drawEllipse(point, point_radius, point_radius)


class MergedSpaceView(QLabel):
    def __init__(self, controller:CalibrationController, parent=None)->None:
        super().__init__(parent)
        self.__image = QImage(__GREEN_BG__.as_posix())
        self._original_pix_map = QPixmap.fromImage(self.__image)
        self.setPixmap(self._original_pix_map.copy())
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._controller = controller

    def resizeEvent(self, a0:QResizeEvent):
        size = a0.size()
        width = round(size.width()*0.98)
        height = round(size.height()*.8)
        self.__image = self.__image.scaled(width, height)
        self._original_pix_map = QPixmap.fromImage(self.__image)
        self.setPixmap(self._original_pix_map.copy())
        return super().resizeEvent(a0)
    
    def update_view(self):
        size = self._original_pix_map.size()
        width, height = size.width(), size.height()

        unified_space = self._controller.get_unified_space()
        if unified_space.shape[0] == 0:
            self.setPixmap(self._original_pix_map.copy())
            return
        
        unified_space *= (width, height)
        unified_space = np.round(unified_space).astype(np.int32)
        self.draw_points(unified_space)

    def draw_points(self, points:np.ndarray)->None:
        if points.shape[0] == 0:
            return
        
        gui_points = []
        for point in points:
            x, y = point
            gui_points.append(
                QPoint(x, y)
            )
        
        px_map = self._original_pix_map.copy()
        painter = QPainter(px_map)
        pen = QPen(Qt.white, 3)
        brush = QBrush(Qt.white)
        painter.setBrush(brush)
        painter.setPen(pen)

        for point in gui_points:
            painter.drawEllipse(point, 8, 8)
        painter.end()
        self.setPixmap(px_map) 

class CalibrationPage(QWidget):
    def __init__(self, cameras_models:list,  parent = None):
        super().__init__(parent)
        self.__window_name = ""
        self.__current_frame = None
        self._side_panel = QVBoxLayout()
        self.setObjectName("calib_page")
        self.setStyleSheet("""
            *{
                font-size:12px;
            }
        """)
        self.setMinimumSize(1920, 1080)
        self._controller = CalibrationController(self, cameras_models)
        self.perspective_view = None

        self.initUI()
        self._controller.select(0)
        self.update_frame(self._controller.next_frame())

        
    def showPerspectiveView(self)->None:
        if self.perspective_view is None:
            self.perspective_view = PerspectiveView(cv.imread(__WHITE_BG__), self._controller)
        self.perspective_view.show()

    def resizeEvent(self, a0:QResizeEvent):
        self._side_panel.setSizeConstraint(QLayout.SetFixedSize)
        return super().resizeEvent(a0)

    def initUI(self)->None:
        """
        1. Initialize Cams View Selecting between cameras and switching active models
        2.
        """
        self._calib_layout = QHBoxLayout()
        
        self.initSideBar(self._side_panel)

        self._clear_calib_layout = QHBoxLayout()
        self._clear_calib_button = QPushButton("Clear Calibration")
        self._clear_calib_button.clicked.connect(self.clearCalibration)
        self._clear_calib_button.setFixedWidth(150)
        self._clear_calib_button.setFixedHeight(40)

        self._save_calib_button = QPushButton("Save Calibration")
        self._save_calib_button.setFixedWidth(150)
        self._save_calib_button.setFixedHeight(40)
        self._save_calib_button.clicked.connect(self.save_calibration)
        
        self._status_message = QLabel("Status: Boundary Alignment")
        # self._status_message.setFixedWidth(200)
        self._status_message.setFixedHeight(40)
        self._clear_calib_layout.setAlignment(Qt.AlignRight)
        self._clear_calib_layout.addWidget(self._status_message)
        self._clear_calib_layout.addWidget(self._save_calib_button)
        self._clear_calib_layout.addWidget(self._clear_calib_button)
        self._status_message.setAlignment(Qt.AlignVCenter|Qt.AlignLeft)
      
        
        # self._side_panel.setAlignment(Qt.AlignLeft)
        self.__current_frame_view = PolygonDrawer(self._controller.next_frame(), self._controller)#FrameView()
        self.__camera_selector = CameraSelector(self._controller)
        self.__layout = QVBoxLayout()
    
        self.__layout.addLayout(self._clear_calib_layout)
        self.__layout.addWidget(self.__current_frame_view)
        self.__layout.addWidget(self.__camera_selector)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setAlignment(Qt.AlignRight|Qt.AlignTop)

        self._calib_layout.addLayout(self._side_panel)
        self._calib_layout.addLayout(self.__layout)
        self._calib_layout.addSpacing(100)
        self.setLayout(self._calib_layout)

    def updateUI(self):
        if self.perspective_view is not None:
            self.perspective_view.update_view()
        
        if self.merged_space is not None:
            self.merged_space.update_view()

    def clearCalibration(self)->None:
        if self.__current_frame_view is not None:
            self.__current_frame_view.clear_calibration() 
        self.updateUI()


    def toggle_add_alignment(self):
        if self.__current_frame_view:
            self.__current_frame_view.toggle_alignment_points()
            if self.__current_frame_view._add_alignment_points:
                self._status_message.setText("Status: Adding Alignment Points")
            else:
                self._status_message.setText("Status: Boundary Alignment")

    def initSideBar(self, layout:QVBoxLayout)->None:
        self._show_perspective_view = QPushButton("Show Perspective View")
        self._show_perspective_view.setFixedHeight(40)
        self._show_perspective_view.clicked.connect(self.showPerspectiveView)

        self._show_merged_view = QPushButton("Show Merged View")
        self._show_merged_view.setFixedHeight(40)
        self._add_alignment_points = QPushButton("Add Alignment Points")
        self._add_alignment_points.setFixedHeight(40)
        self._add_alignment_points.clicked.connect(self.toggle_add_alignment)
        self.merged_space = MergedSpaceView(self._controller, self)
        self.merged_space.setAlignment(Qt.AlignTop)
        self.merged_space_title = QLabel("Merged Virtual Space View")
        self.merged_space_title.setAlignment(Qt.AlignCenter)
        self.merged_space_title.setContentsMargins(0, 10, 0, 0)
        # self.merged_space.setMargin(10)

        layout.addWidget(self._show_perspective_view)
        layout.addWidget(self._show_merged_view)
        layout.addWidget(self._add_alignment_points)
        layout.addWidget(self.merged_space_title)
        layout.addWidget(self.merged_space)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)

    def update_frame(self, frame:cv.Mat):
        self.__current_frame_view.update_frame(frame)
        self.__camera_selector.update_thumbnail(frame)
        self.update_polygon(self._controller.get_src_poly())
    
    def update_polygon(self, poly:np.ndarray)->None:
        self.__current_frame_view.set_alignment_points(self._controller.get_alignment_pts())
        self.__current_frame_view.set_polygon(poly)

    def save_calibration(self)->None:
        self._controller.dump_to_json()

    def closeEvent(self, a0):
        if self.perspective_view is not None:
            self.perspective_view.close()
        return super().closeEvent(a0)

