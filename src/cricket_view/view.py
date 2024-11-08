from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QImage, QPixmap, QMouseEvent
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel,
                             QSizePolicy, QHBoxLayout)
from pathlib import Path
from .common_widget import *
from .controller import DataAssociationsController, StateGenerator
import numpy as np
import math
from typing import Callable
from cfg.paths_config import __CRICKET_STYLES__, __GREEN_CIRCLE__


def load_style_sheet(file_name)->str:
    with open(file_name, 'r') as fp:
        return fp.read()

class UITrackObjectState:
    def __init__(self, radius):
        """
        {
        track_id:point(x, y)
        }
        """
        self.__current_state = None
        self.__state_table = {}
        self.__point_radius = radius

    def update_state(self, state:list[dict])->None:
        self.__current_state = state
        for track in self.__current_state:
            track_id = track['track_id']
            if track_id is not None:
                self.__state_table[track_id] = track['ui-coordinates']

    def get_closest_id(self, point:QPoint)->None:
        MINIMUM_DISTANCE = math.inf
        MINIMUM_INDEX = -1

        for i, key in enumerate(self.__state_table.keys()):
            object_point = self.__state_table[key]
            p = QPoint(*object_point)
            dist = (point - p).manhattanLength()
            if dist < MINIMUM_DISTANCE and dist <= self.__point_radius:
                MINIMUM_DISTANCE = dist
                MINIMUM_INDEX = i
        
        if MINIMUM_DISTANCE is not math.inf:
            return list(self.__state_table.keys())[MINIMUM_INDEX]


class CricketOvalWindow(QLabel):
    def __init__(self, controller:DataAssociationsController, parent=None)->None:
        super().__init__(parent)
        self._original_pixmap = None
        self.__update_timer = QTimer()
        self.__update_timer.timeout.connect(self.update_view)
        self.__update_timer.start(50)
        self.__controller = controller
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setObjectName("cricket_oval")
        self.initUI()
        self.radius = 10
        self.__objects_state = UITrackObjectState(self.radius)
        self.__current_selected_id = None
        # A list of callback functions waiting to receive an ID when it's clicked
        self.__id_recievers = []
     
    def registerIDReceiver(self, func:Callable)->None:
        self.__id_recievers.append(func)

    def initUI(self)->None:
        self.__original_pixmap = QPixmap(__GREEN_CIRCLE__.as_posix())
        self.draw_boundaries()
        self.setPixmap(self.__original_pixmap.copy())
        
    def draw_boundaries(self)->None:
        painter = QPainter(self.__original_pixmap)
        pen = QPen(Qt.white, 6)

        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x, center_y = self.__original_pixmap.width()//2 , self.__original_pixmap.height()//2
        center_point = QPoint(center_x, center_y)

        radius_outer = round(self.__original_pixmap.width() * 0.9)//2
        painter.drawEllipse(center_point, radius_outer-20, radius_outer)
        
        radius_inner = round(self.__original_pixmap.width() * 0.5)//2
        painter.drawEllipse(center_point, radius_inner-20, radius_inner)

        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        text_offset = 80
        leg_text_position = QPoint(center_x - radius_inner - text_offset, center_y)
        painter.drawText(leg_text_position, "Leg")

        leg_text_position = QPoint(center_x + radius_inner + 30, center_y)
        painter.drawText(leg_text_position, "Off")

        rect_color = QBrush(QColor("#d9b99b"))
        painter.setBrush(rect_color)
        width = round(self.__original_pixmap.width()*0.07)
        height = round(self.__original_pixmap.height()*0.16)
        painter.setPen(QPen(QColor("#d9b99b"), 1))
        painter.drawRect(center_x-(width//2), center_y- (height//2), width, height)
        painter.end()


    def __draw_point(self, point:QPoint, painter:QPainter, details:dict = None)->None:
        if details is None:
            return

        default_brush = painter.brush()
        default_pen = painter.pen()

        track_id = details.get('track_id')
        if track_id is None:
            painter.setBrush(QBrush(Qt.red))
            painter.setPen(QPen(Qt.red, 1))

        status = details.get('state')
        if status == StateGenerator.UNASSOCIATED:
            painter.drawEllipse(point, self.radius, self.radius) 
            point.setY(point.y()-self.radius)
            point.setX(point.x()-self.radius+round(self.radius*0.01))
            font = painter.font()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.blue, 2))
            painter.drawText(point, f"{track_id}".zfill(2))
        
        elif status == StateGenerator.ASSOCIATED:
            color =  details.get('color')
            jersey_number = details.get('jersey_number')
            brush = QBrush(QColor(*color))
            pen = QPen(QColor(*color))
            painter.setBrush(brush)
            painter.setPen(pen)
            painter.drawEllipse(point, self.radius, self.radius) 
            point.setY(point.y()+round(self.radius*0.5))
            point.setX(point.x()-round(self.radius*0.8))
            font = painter.font()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.white, 2))
            painter.drawText(point, f"{jersey_number}".zfill(2))
        
        elif status == StateGenerator.CLICKED:
            painter.setPen(QPen(Qt.yellow, 3))
            painter.drawEllipse(point, self.radius, self.radius) 
            point.setY(point.y()-self.radius)
            point.setX((point.x()-self.radius)+round(self.radius*0.01))
            font = painter.font()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.blue, 2))
            painter.drawText(point, f"{track_id}".zfill(2))

        painter.setBrush(default_brush)
        painter.setPen(default_pen)

    def __generate_points(self, dets_list:list)->list[QPoint]:
        result = []
        width, height = self.__original_pixmap.width(), self.__original_pixmap.height()
        for det in dets_list:
            coord = det.get('coordinates')
            if coord is not None:
                x, y = coord
                x = (x * (0.9)) + 0.05
                y = (y * 0.9) + 0.05
                x, y = round(width * x), round(height * y)
                result.append(
                    QPoint(x, y)
                )
                det['ui-coordinates'] = (x, y)
        return result
    
    def update_view(self)->None:
        pix_map = self.__original_pixmap.copy()
        painter = QPainter(pix_map)
        pen = QPen(Qt.gray, 2)
        brush = QBrush(Qt.gray)
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.setRenderHint(QPainter.Antialiasing)
        current_state = self.__controller.get_current_state()
        dets_list = self.__generate_points(current_state)
        self.__objects_state.update_state(current_state)
    
        for i, point in enumerate(dets_list):
            self.__draw_point(point, painter, current_state[i])
        painter.end()
        self.setPixmap(pix_map)

    def mousePressEvent(self, ev:QMouseEvent):
        if ev.button() == Qt.LeftButton:
            pos = self.mapFrom(self, ev.pos())
            id = self.__objects_state.get_closest_id(pos)
            if id is not None:
                self.__controller.update_click(id)
            self.__current_selected_id = id
            for func in self.__id_recievers:
                func(*(id, ))
        return super().mousePressEvent(ev)


class FieldersGridView(QWidget):
    NUMBER_OF_FIELDERS = 10
    def __init__(self, controller:DataAssociationsController , text_title,  parent = None)->None:
        super().__init__(parent)
        self.__field_positions = [
            "WKT",  # Wicketkeeper
            "SLP",  # Slip
            "GUL",  # Gully
            "PTN",  # Point
            "COV",  # Cover
            "MID",  # Mid-off
            "MDF",  # Mid-on
            "MID",  # Midwicket
            "SQG",  # Square Leg
            "FNL"   # Fine Leg
        ]
        self.__fielder_positions_names = [
            "Wicket-keeper",
            "Slip",
            "Gully",
            "Point",
            "Cover",
            "Mid-off",
            "Mid-on",
            "Midwicket",
            "Square Leg",
            "Fine Leg"
        ]

        self.__text_title = QLabel(text_title)
        self.__text_title.setObjectName("text_title")
        self.__main_layout = QVBoxLayout()
        self.__buttons_grid_layout = QGridLayout()
        self.__fielders_buttons_widgets = []
        self.__bats_man_buttons_widgets = []
        self.__bowler_buttons_widget   = None
        self.__all_buttons = []
        self.__controller = controller
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setLayout(self.__main_layout)
        self.initUI()
        self.__current_selected_id = None

    def handleButtonClick(self, player:dict)->None:
        if self.__current_selected_id is None:
            return
        self.__controller.associate_player(player, self.__current_selected_id)

    def update_current_selected_id(self, id)->None:
        self.__current_selected_id = id
       
    def initUI(self)->None:
        for i, position in enumerate(self.__field_positions):
            btn = ButtonWithID(f"{position}", {"id":int(i), "jersey_number":i, "color":"#ff00ea", "team":"Test Team", 
                                               'player':{"jersey_number":i, "color":"#ff00ea", "team":"Test Team"}})
            btn.setToolTip(self.__fielder_positions_names[i])
            self.__fielders_buttons_widgets.append(btn)

        for i in range(FieldersGridView.NUMBER_OF_FIELDERS):
            row, col = divmod(i, 3)
            self.__buttons_grid_layout.addWidget(self.__fielders_buttons_widgets[i], row, col)

        for i in range(2):
            btn = ButtonWithID(f"BAT {i}", {"id":int(i), "jersey_number":i, "color":"#ff00ea", "team":"Test Team", 
                                               'player':{"jersey_number":i, "color":"#ff00ea", "team":"Test Team"}})
            btn.setToolTip(f"Bats Man {i}")
            self.__bats_man_buttons_widgets.append(btn)

        bats_position = 5
        bats_man_title = QLabel("Bats Man")
        bats_man_title.setObjectName("text_title")
        self.__buttons_grid_layout.addWidget(bats_man_title, bats_position, 0)
        row, col = (bats_position+1, 0)
        self.__buttons_grid_layout.addWidget(self.__bats_man_buttons_widgets[0], row, col)
        row, col = (bats_position+1, 1)
        self.__buttons_grid_layout.addWidget(self.__bats_man_buttons_widgets[1], row, col)

        bowler_position = 8
        bowler_title = QLabel("Bowler")
        bowler_title.setObjectName("text_title")
        self.__buttons_grid_layout.addWidget( bowler_title, bowler_position, 0)
        row, col = (bowler_position+1, 0)
        self.__bowler_buttons_widget = ButtonWithID("BOWL",{"id":int(20), "jersey_number":20, "color":"#ff00ea", "team":"Test Team", 
                                               'player':{"jersey_number":20, "color":"#ff00ea", "team":"Test Team"}})
        self.__bowler_buttons_widget.setToolTip("Bowler")
        self.__buttons_grid_layout.addWidget(self.__bowler_buttons_widget, row, col)  
    
        self.__main_layout.addWidget(self.__text_title)
        self.__main_layout.addLayout(self.__buttons_grid_layout)

        self.__all_buttons.extend(self.__fielders_buttons_widgets)
        self.__all_buttons.extend(self.__bats_man_buttons_widgets)
        self.__all_buttons.append(self.__bowler_buttons_widget)

        for btn in self.__all_buttons:
            btn.registerCallback(self.handleButtonClick)


class CricketTrackingWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Cricket Tracking")
        self.__controller = DataAssociationsController()
        self.__header_buttons_layout = QHBoxLayout()
        self.__main_layout = QGridLayout()
        self.__buttons_layout = QVBoxLayout()
        self.__cricket_view_map = CricketOvalWindow(self.__controller)
        self.__fielders_grid = FieldersGridView(self.__controller, "Fielders")
        self.__cricket_view_map.registerIDReceiver(self.__fielders_grid.update_current_selected_id)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.initTopBar()
        self.initUI()
        self.setFixedSize(self.sizeHint())

    def initUI(self)->None:
        self.__main_layout.addWidget(self.__cricket_view_map, 1, 0)
        self.__buttons_layout.addWidget(self.__fielders_grid)
     
        self.__buttons_layout.setContentsMargins(0,0,0,0)
        self.__main_layout.addLayout(self.__header_buttons_layout, 0, 0, Qt.AlignLeft)
        self.__main_layout.addLayout(self.__buttons_layout, 1, 1, Qt.AlignTop)
        self.__main_layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.__main_layout)


    def initTopBar(self)->None:
        self.switch_ends = StyledButton('Switch Ends', self)
        self.switch_ends.clicked.connect(self.switch_ends.toggle_color)

        self.distance = StyledButton('Calculate Distance', self)        
        self.distance.clicked.connect(self.distance.toggle_color)
      
        self.highlight_button = StyledButton('Highlight', self)
        self.highlight_button.clicked.connect(self.highlight_button.toggle_color)

        self.hide_player = StyledButton('Hide Player', self)
        self.hide_player.clicked.connect(self.hide_player.toggle_color)

        self.__header_buttons_layout.addWidget(self.highlight_button)
        self.__header_buttons_layout.addWidget(self.distance)
        self.__header_buttons_layout.addWidget(self.switch_ends)
        self.__header_buttons_layout.addWidget(self.hide_player)
        self.__header_buttons_layout.setAlignment(Qt.AlignLeft)
    
    def closeEvent(self, a0):
        self.__controller.stop()
        return super().closeEvent(a0)
