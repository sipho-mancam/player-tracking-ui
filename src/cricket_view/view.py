from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QImage, QPixmap, QMouseEvent
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel,
                             QSizePolicy, QHBoxLayout, QMessageBox, QDialog)
from PyQt5.QtCore import pyqtSignal
from pathlib import Path
from .common_widget import *
from .controller import DataAssociationsController, StateGenerator, EventsController
import numpy as np
import math
from typing import Callable
from cfg.paths_config import __CRICKET_STYLES__, __GREEN_CIRCLE__, __MINI_MAP_BG__



def load_style_sheet(file_name)->str:
    with open(file_name, 'r') as fp:
        return fp.read()
    
class KickerSideDialog(QDialog):
    kickSideSignal = pyqtSignal(tuple)
    def __init__(self, parent = None):
        super().__init__(parent)
        self.__left = QPushButton("Left Side",)
        self.__right = QPushButton("Right Side")
        self._layout = QHBoxLayout()
        self._layout.addWidget(self.__left)
        self._layout.addWidget(self.__right)
        self.setLayout(self._layout)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Select Kick Side")
        self.__right.clicked.connect(self.rightClicked)
        self.__left.clicked.connect(self.leftClicked)

    
    def leftClicked(self):
        self.close()
        self.kickSideSignal.emit((0.0, 0.5))
    
    def rightClicked(self):
        self.close()
        self.kickSideSignal.emit((1.0, 0.5))


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
    idXYChanged = pyqtSignal(int, float, float)
    idTrackCorrection = pyqtSignal(int)

    def __init__(self, controller:DataAssociationsController, parent=None)->None:
        super().__init__(parent)
        self._original_pixmap = None
        self.__update_timer = QTimer()
        self.__update_timer.timeout.connect(self.update_view)
        self.__update_timer.start(50)
        self.__controller = controller
        self.idXYChanged.connect(self.__controller.plottedIdCoordinatesChangedSlot)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedHeight(int(1080*0.6))
        self.setFixedWidth(int(1920*0.7))
        self.setObjectName("cricket_oval")
        self.initUI()
        self.radius = 10
        self.__objects_state = UITrackObjectState(self.radius)
        self.__current_selected_id = None
        # A list of callback functions waiting to receive an ID when it's clicked
        self._kicker_id = -1
        self._kick_side = None
        self.__id_recievers = set()
        self.__id_click_callbacks = set()
        self.current_state = None

    def setKickerIdSlot(self, id):
        self._kicker_id = id

    def resetKickerId(self):
        self._kicker_id = -1
     
    def registerIDReceiver(self, func:Callable)->None:
        self.__id_recievers.add(func)

    def initUI(self)->None:
        image = QImage(__MINI_MAP_BG__.as_posix())
        image = image.scaledToWidth(self.width()).scaledToHeight(self.height())
        
        self.__original_pixmap = QPixmap(QPixmap.fromImage(image))
        # self.draw_boundaries()
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
        font.setPixelSize(48)
        painter.setFont(font)
        text_offset = 80
        leg_text_position = QPoint(center_x - radius_inner - text_offset, center_y)
        painter.drawText(leg_text_position, "Off")

        leg_text_position = QPoint(center_x + radius_inner + 30, center_y)
        painter.drawText(leg_text_position, "Leg")

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

        # if details.get('mode_state') != StateGenerator.STATE_CLEAR:
        #     if details.get('mode') == StateGenerator.MODE_HIGHLIGHT:
        #         color = Qt.blue
        #     elif details.get('mode') ==StateGenerator.MODE_HIDE:
        #         color = Qt.purple

        default_brush = painter.brush()
        default_pen = painter.pen()

        track_id = details.get('track_id')
        if track_id is None:
            painter.setBrush(QBrush(Qt.red))
            painter.setPen(QPen(Qt.red, 1))
        mode = details.get('mode')
        status = details.get('state')
        position = QPoint(point.x(), point.y())

        if status == StateGenerator.UNASSOCIATED:
            if details.get('mode_state') != StateGenerator.STATE_CLEAR:
                if details.get('mode') == StateGenerator.MODE_HIGHLIGHT:
                    color = (0, 0, 255)
                    painter.setBrush(QColor(*color))
                elif details.get('mode') ==StateGenerator.MODE_HIDE:
                    color = (255, 255, 255) 
                    painter.setBrush(QColor(*color))
                elif details.get('mode') == StateGenerator.MODE_BOWLER:
                    color = (255, 255, 0) 
                    painter.setBrush(QColor(*color))
                elif details.get("mode") == StateGenerator.MODE_TEAM_A:
                    color = (255, 255, 0) 
                    painter.setBrush(QColor(*color))
                elif details.get("mode") == StateGenerator.MODE_TEAM_B:
                    color = (0, 0, 0) 
                    painter.setBrush(QColor(*color))

                elif details.get("mode") == StateGenerator.MODE_GK:
                    color = (128, 0, 128) 
                    painter.setBrush(QColor(*color))

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
            if details.get('mode_state') != StateGenerator.STATE_CLEAR:
                if details.get('mode') == StateGenerator.MODE_HIGHLIGHT:
                    color = (255, 0, 0)
                elif details.get('mode') ==StateGenerator.MODE_HIDE:
                    color = (255, 255, 255) 
                elif details.get("mode") == StateGenerator.MODE_TEAM_A:
                    color = (255, 255, 0) 
                    painter.setBrush(QColor(*color))
                elif details.get("mode") == StateGenerator.MODE_TEAM_B:
                    color = (0, 0, 0) 
                    painter.setBrush(QColor(*color))

                elif details.get("mode") == StateGenerator.MODE_GK:
                    color = (128, 0, 128) 
                    painter.setBrush(QColor(*color))

            jersey_number = details.get('jersey_number')
            brush = QBrush(QColor(*color))
            pen = QPen(QColor(*color))
            painter.setBrush(brush)
            painter.setPen(pen)
            # painter.drawEllipse(point, self.radius, self.radius) 
            point.setY(point.y()+round(self.radius*0.5))
            point.setX(point.x()-round(self.radius*0.8))
            font = painter.font()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.white, 2))
            painter.drawText(point, f"{jersey_number}".zfill(2))
        
        elif status == StateGenerator.CLICKED and (mode == StateGenerator.MODE_DEFAULT or mode is None):
            painter.setPen(QPen(Qt.yellow, 3))
            # painter.drawEllipse(point, self.radius, self.radius) 
            point.setY(point.y()-self.radius)
            point.setX((point.x()-self.radius)+round(self.radius*0.01))
            font = painter.font()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.blue, 2))
            painter.drawText(point, f"{track_id}".zfill(2))

        else:
            if details.get('mode') == StateGenerator.MODE_HIGHLIGHT:
                color = (0, 0, 255)
                painter.setBrush(QColor(*color))
            elif details.get('mode') ==StateGenerator.MODE_HIDE:
                color = (255, 255, 255) 
                painter.setBrush(QColor(*color))
            elif details.get('mode') == StateGenerator.MODE_BOWLER:
                color = (255, 255, 0) 
                painter.setBrush(QColor(*color))
            elif details.get("mode") == StateGenerator.MODE_TEAM_A:
                color = (255, 255, 0) 
                painter.setBrush(QColor(*color))
            elif details.get("mode") == StateGenerator.MODE_TEAM_B:
                color = (0, 0, 0) 
                painter.setBrush(QColor(*color))
            elif details.get("mode") == StateGenerator.MODE_GK:
                color = (128, 0, 128) 
                painter.setBrush(QColor(*color))


            # painter.drawEllipse(point, self.radius, self.radius) 
            point.setY(point.y()-self.radius)
            point.setX(point.x()-self.radius+round(self.radius*0.01))
            font = painter.font()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.blue, 2))
            painter.drawText(point, f"{track_id}".zfill(2))
        
        if status == StateGenerator.CLICKED and (mode == StateGenerator.MODE_DEFAULT or mode is None):
            painter.setPen(QPen(Qt.yellow, 3))
        else:
            painter.setPen(QPen(painter.brush().color()))
        
        if track_id == self._kicker_id and self._kicker_id != -1:
            w = 15
            painter.setBrush(QBrush(QColor(255, 0, 0)))
            painter.drawRect(position.x()-round(w/2), position.y()-round(w/2), w, w)
        else:
            painter.drawEllipse(position, self.radius, self.radius) 

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
        self.current_state = self.__controller.get_current_state()
 
        if self.__controller.is_distance_object_available():
            distance_object = self.__controller.get_distance_object()
            # print(distance_object)
            if distance_object is not None:
                id1 = distance_object.get('player_id_1')
                id2 = distance_object.get('player_id_2')
                track_1 = self.find_track(id1, self.current_state)
                track_2 = self.find_track(id2, self.current_state)
                if track_1 is not None and track_2 is not None:
                    self.draw_line(track_1, track_2, painter)

        dets_list = self.__generate_points(self.current_state)
        self.__objects_state.update_state(self.current_state)
    
        for i, point in enumerate(dets_list):
            self.__draw_point(point, painter, self.current_state[i])
        painter.end()
        self.setPixmap(pix_map)

    def find_track(self, id, tracks:list)->dict:
        for track in tracks:
            if track.get('track_id') == id:
                return track
            
    def draw_line(self, track1, track2, painter:QPainter)->None:
        points = self.__generate_points([track1, track2])
        painter.drawLine(points[0], points[1]) 

    def mousePressEvent(self, ev:QMouseEvent):
        if ev.button() == Qt.LeftButton:
            pos = self.mapFrom(self, ev.pos())
            id = self.__objects_state.get_closest_id(pos)

            if id is not None:
                self.__controller.update_click(id)
                for func in self.__id_recievers:
                    func(*(id, ))
                
                kb_mod = ev.modifiers()
                if kb_mod & Qt.CTRL:
                    # Disengage this id if it's on a tracked state to a plotted state and place
                    # it at the center of the board to be controlled'
                    self.idTrackCorrection.emit(id)
            else:
                if self.__current_selected_id is not None:
                    pos = self.mapFrom(self, ev.pos())
                    x, y = pos.x(), pos.y()
                    x /= self.__original_pixmap.width()
                    y /= self.__original_pixmap.height()
                    self.idXYChanged.emit(self.__current_selected_id, x, y)
            self.__current_selected_id = id
        return super().mousePressEvent(ev)
    
    def mouseMoveEvent(self, ev):
        if self.__current_selected_id is not None:
            pos = self.mapFrom(self, ev.pos())
            x, y = pos.x(), pos.y()
            x /= self.__original_pixmap.width()
            y /= self.__original_pixmap.height()
            self.idXYChanged.emit(self.__current_selected_id, x, y)
        return super().mouseMoveEvent(ev)
    


class FieldersGridView(QWidget):
    NUMBER_OF_FIELDERS = 10
    def __init__(self, controller:DataAssociationsController, match_controller, text_title,  parent = None)->None:
        super().__init__(parent)
        self.__field_positions = [
            "WKT",  # Wicketkeeper
            "SLP",  # Slip
            "GUL",  # Gully
            "PTN",  # Point
            "COV",  # Cover
            "MID",  # Mid-off
            "MDF",  # Mid-on
            "MIW",  # Midwicket
            "SQL",  # Square Leg
            "FNL"   # Fine Leg
        ]
        self.__fielder_positions_names = {
            "WKT":"Wicket-keeper",
            "SLP":"Slip",
            "GUL":"Gully",
            "PTN":"Point",
            "COV":"Cover",
            "MID":"Mid-off",
            "MDF":"Mid-on",
            "MIW":"Midwicket",
            "SQL":"Square Leg",
            "FNL":"Fine Leg"
        }
        self.__match_controller = match_controller

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
        self.__clicked_callbacks = set()

    def handleButtonClick(self, player:dict)->None:
        if self.__current_selected_id is None:
            return
        self.__controller.associate_player(player, self.__current_selected_id)

    def registerIDClickCallback(self, cb:Callable)->None:
        self.__clicked_callbacks.add(cb)
    

    def update_current_selected_id(self, id)->None:
        self.__current_selected_id = id

       
    def initUI(self)->None:
        team = self.__match_controller.get_fielding_team_info()
        players = team.get("players")
        for i, position in enumerate(self.__field_positions):
            player = players[i]
            btn = ButtonWithID(f"{player.get('position')}", {"id":player.get('track_id'), "jersey_number":player.get("jersey_number"), "color":player.get('color'), "team":player.get("team"), 
                                               'player':player})
            btn.setToolTip(self.__fielder_positions_names[player.get("position")])
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
    untrackedIdsChanged = pyqtSignal(dict)
    startEventSignal = pyqtSignal()
    selectKickerSignal = pyqtSignal(int)
    resetStateSignal = pyqtSignal()
    resetKickerSignal = pyqtSignal()


    def __init__(self, controller, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Cricket Tracking")
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowMinimizeButtonHint)      
        self.__controller = DataAssociationsController()
        self.__controller.untrackedIdsChangedSignal.connect(self.untrackedIdsChanged)
        self.__header_buttons_layout = QHBoxLayout()
        self.__match_controller = controller
        self.__main_layout = QGridLayout()
        self.__buttons_layout = QVBoxLayout()
        self.__cricket_view_map = CricketOvalWindow(self.__controller)
        self.__cricket_view_map.idTrackCorrection.connect(self.__controller.idTrackCorrectSlot)
        self.__fielders_grid = FieldersGridView(self.__controller, self.__match_controller, "Fielders")
        self.__cricket_view_map.registerIDReceiver(self.__fielders_grid.update_current_selected_id)
        self.__current_mode = StateGenerator.MODE_DEFAULT
        self.__event_type = StateGenerator.MODE_DEFAULT
        self.__previous_mode = StateGenerator.MODE_DEFAULT
        self.__current_selected = None
        self.__mode_ids = None
        self.__distance_ids = []
        self.__events_controller = EventsController()
        self.__header_buttons = []
        self.__kickSideDialog = KickerSideDialog(self)
        self.__kick_side = None

        self.__kickSideDialog.kickSideSignal.connect(self.setKickSide)


        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.initTopBar()
        self.initUI()
        self.setFixedSize(self.sizeHint())
        self.__cricket_view_map.registerIDReceiver(self.clicked_id)
    
    #### Slots for received signals
    def toggleOnAirMode(self, flag)->None:
        self.__on_air_flag = flag
        self.__controller.onAirModeSlot(flag)
    
    def setKickSide(self, point:tuple):
        self.__kick_side = point
        print("Kick Side: ", self.__kick_side)
    
    def plotIdActivated(self, id)->None:
        self.__controller.enableIdPlot(id)
    

    def setCurrentMode(self, mode:int)->None:
        self.__current_mode = mode

    def clicked_id(self, id)->None:
        if self.__event_type == StateGenerator.MODE_MODE:
            self.__mode_ids = id
            event = self.__events_controller._build_event_object(StateGenerator.MODE_MODE, 
                                                         self.__current_mode, 
                                                         StateGenerator.STATE_SET if self.__current_mode != StateGenerator.MODE_DEFAULT else StateGenerator.STATE_CLEAR,
                                                         self.__mode_ids)
            self.__events_controller.send_current_event()
            self.__event_type = StateGenerator.MODE_DEFAULT

        elif self.__current_mode == StateGenerator.MODE_SELECT_KICKER:
            self.__mode_ids = id
            event = self.__events_controller._build_event_object(
                StateGenerator.MODE_INSTRUCTION,
                StateGenerator.MODE_SELECT_KICKER,
                StateGenerator.STATE_SET,
                self.__mode_ids
            )
            event["data"]["kick_side"] = self.__kick_side
            self.__events_controller.send_current_event(event)
            self.selectKickerSignal.emit(id)
            
        elif self.__current_mode != StateGenerator.MODE_DISTANCE:
            self.__mode_ids = id
            event = self.__events_controller._build_event_object(self.__current_mode, 
                                                         self.__current_mode, 
                                                         StateGenerator.STATE_SET if self.__current_mode != StateGenerator.MODE_DEFAULT else StateGenerator.STATE_CLEAR,
                                                         self.__mode_ids)
            self.__events_controller.send_current_event() 
        else:
           self.__distance_ids.append(id)
           if len(self.__distance_ids) >= 2:
                event = self.__events_controller._build_event_object(self.__current_mode, 
                                                            self.__current_mode, 
                                                            StateGenerator.STATE_SET,
                                                            self.__distance_ids)
                self.__events_controller.send_current_event() 

    def get_modes(self)->list[int]:
        return [StateGenerator.MODE_DEFAULT, 
                StateGenerator.MODE_HIGHLIGHT, 
                StateGenerator.MODE_HIDE, 
                StateGenerator.MODE_DISTANCE, 
                StateGenerator.MODE_BOWLER,
                StateGenerator.MODE_TEAM_A,
                StateGenerator.MODE_TEAM_B,
                StateGenerator.MODE_GK
            ]


    def initUI(self)->None:
        self.__main_layout.addWidget(self.__cricket_view_map, 1, 0)
        self.__fielders_grid.hide()
        self.__buttons_layout.setContentsMargins(0,0,0,0)
        self.__main_layout.addLayout(self.__header_buttons_layout, 0, 0, Qt.AlignLeft)
        self.__main_layout.addLayout(self.__buttons_layout, 1, 1, Qt.AlignTop)
        self.__main_layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.__main_layout)

    def select_mode(self, mode:int)->None:
        if self.__current_mode == mode and self.__current_mode != StateGenerator.MODE_DEFAULT:
            self.__current_mode = StateGenerator.MODE_DEFAULT
            self.__current_selected = ""
        else:
            self.__current_mode =  mode

        for but in self.__header_buttons:
            obj_name = but.objectName()
            if self.__current_selected != obj_name:
                but.clear_toggle()

    def select_highlight(self)->None:
        self.__current_selected = "highlight"
        self.select_mode(StateGenerator.MODE_HIGHLIGHT)

    def select_show_player(self)->None:
        self.__current_selected = "show_player"
        self.select_mode(StateGenerator.MODE_HIDE)

    def select_clear(self)->None:
        self.__current_selected = "clear_mode"
        self.select_mode(StateGenerator.MODE_DEFAULT)

    def select_dist(self)->None:
        self.__current_selected = "clear_dist"
        self.select_mode(StateGenerator.MODE_DEFAULT)
        event = self.__events_controller._build_event_object(StateGenerator.MODE_DISTANCE, 
                                                         StateGenerator.MODE_DISTANCE, 
                                                         StateGenerator.STATE_SET,
                                                         (-1, -1))
        self.__events_controller.send_current_event()
        self.__distance_ids.clear()
        
    
    def select_distance(self)->None:
        self.__current_selected = "distance_cal"
        self.select_mode(StateGenerator.MODE_DISTANCE)

    def select_reset(self)->None:
        self.__current_selected = "reset_button"
        self.select_mode(StateGenerator.MODE_RESET)
        event = self.__events_controller._build_event_object(StateGenerator.MODE_RESET, 
                                                         StateGenerator.MODE_RESET, 
                                                         StateGenerator.STATE_SET,
                                                         -1)
        self.__events_controller.send_current_event() 
        self.resetStateSignal.emit()

    
    def select_reset_kicker(self)->None:
        self.__current_selected = "reset_kicker_button"
        self.select_mode(StateGenerator.MODE_RESET_KICKER)
        event = self.__events_controller._build_event_object(StateGenerator.MODE_INSTRUCTION, 
                                                         StateGenerator.MODE_RESET_KICKER, 
                                                         StateGenerator.STATE_SET,
                                                         -1)
        self.__events_controller.send_current_event() 
        self.resetKickerSignal.emit()


    def select_start_event(self)->None:
        self.__current_selected = "start_event_button"
        self.__event_type = StateGenerator.MODE_MODE
        self.select_mode(StateGenerator.MODE_START_EVENT)
        self.startEventSignal.emit()

    def select_select_kicker(self)->None:
        self.__current_selected = "select_kicker_button"
        self.__event_type = StateGenerator.MODE_MODE
        self.__kickSideDialog.open()
        self.select_mode(StateGenerator.MODE_SELECT_KICKER)
        
        
    def select_team_a(self)->None:
        self.__current_selected = "team_a_btn"
        self.__event_type = StateGenerator.MODE_TEAM_A
        self.select_mode(StateGenerator.MODE_TEAM_A)

    def select_team_b(self)->None:
        self.__current_selected = "team_b_btn"
        self.__event_type = StateGenerator.MODE_TEAM_B
        self.select_mode(StateGenerator.MODE_TEAM_B)

    def select_gk(self)->None:
        self.__current_selected = "goalkeeper"
        self.__event_type = StateGenerator.MODE_GK
        self.select_mode(StateGenerator.MODE_GK)
        
    def initTopBar(self)->None:

        self.start_event_button = StyledButton('Start Event', self)
        self.start_event_button.setObjectName("start_event_button")
        self.start_event_button.clicked.connect(self.start_event_button.toggle_color)
        self.start_event_button.clicked.connect(self.select_start_event)
        # This signal tells data aggregator to pause the continuos state and only update and send the last frame.
        self.startEventSignal.connect(self.__events_controller.startGameEventSlot)
        self.start_event_button.setEnabled(True)

        self.select_kicker = StyledButton('Select Kicker', self)
        self.select_kicker.setObjectName("select_kicker_button")
        self.select_kicker.clicked.connect(self.select_kicker.toggle_color)
        self.select_kicker.clicked.connect(self.select_select_kicker)
        self.selectKickerSignal.connect(self.__events_controller.selectKickerEventSlot)
        self.selectKickerSignal.connect(self.__cricket_view_map.setKickerIdSlot)
        self.select_kicker.setEnabled(True)

        self.reset_button = StyledButton('Reset', self)
        self.reset_button.setObjectName("reset_button")
        self.reset_button.clicked.connect(self.reset_button.toggle_color)
        self.reset_button.clicked.connect(self.select_reset)
        self.resetStateSignal.connect(self.__events_controller.resetStateEventSlot)
        self.resetStateSignal.connect(self.__cricket_view_map.resetKickerId)
        self.reset_button.setEnabled(True)

        self.reset_kicker_button = StyledButton('Reset Kicker', self)
        self.reset_kicker_button.setObjectName("reset_kicker_button")
        self.reset_kicker_button.clicked.connect(self.reset_kicker_button.toggle_color)
        self.reset_kicker_button.clicked.connect(self.select_reset_kicker)
        self.resetKickerSignal.connect(self.__cricket_view_map.resetKickerId)
        self.reset_kicker_button.setEnabled(True)

        self.show_player = StyledButton('Show Player', self)
        self.show_player.setObjectName('show_player')
        self.show_player.clicked.connect(self.show_player.toggle_color)
        self.show_player.clicked.connect(self.select_show_player)

        self.teamAButton = StyledButton("Team A", self)
        self.teamAButton.setObjectName("team_a_btn")
        self.teamAButton.clicked.connect(self.teamAButton.toggle_color)
        self.teamAButton.clicked.connect(self.select_team_a)

        self.teamBButton = StyledButton("Team B", self)
        self.teamBButton.setObjectName("team_b_btn")
        self.teamBButton.clicked.connect(self.teamBButton.toggle_color)
        self.teamBButton.clicked.connect(self.select_team_b)
       
        self.__header_buttons.append(self.reset_button)
        self.__header_buttons.append(self.show_player)
        self.__header_buttons.append(self.teamAButton)
        self.__header_buttons.append(self.teamBButton)
        self.__header_buttons.append(self.start_event_button)
        self.__header_buttons.append(self.select_kicker)
        self.__header_buttons.append(self.reset_kicker_button)
       
        self.__header_buttons_layout.addWidget(self.start_event_button)
        self.__header_buttons_layout.addWidget(self.select_kicker)
        self.__header_buttons_layout.addWidget(self.show_player)
        self.__header_buttons_layout.addWidget(self.teamAButton)
        self.__header_buttons_layout.addWidget(self.teamBButton)
        self.__header_buttons_layout.addWidget(self.reset_kicker_button)
        self.__header_buttons_layout.addWidget(self.reset_button)
        self.__header_buttons_layout.setAlignment(Qt.AlignLeft)
    
    def closeEvent(self, a0):
        self.__controller.stop()
        return super().closeEvent(a0)


class OnAirWindow(QWidget):
    idButtonClickedSignal = pyqtSignal(int)
    onAirClickedSignal = pyqtSignal(bool)
    def __init__(self, parent = None):
        super().__init__(parent)
        self.__tracked_ids = [1, 2, 3, 5, 6, 10]
        self.__main_layout = QVBoxLayout()
        self.__on_air_button = QPushButton("Go On Air")
        self.__on_air_flag = False
        self.ids_layout = QGridLayout()
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowMinimizeButtonHint)      
        self.setWindowTitle("Untracked IDs")
        self.initUI()

    def initUI(self)->None:
        self.initHeaderButtons()
        self.updateTrackedIds()
        self.__main_layout.addLayout(self.ids_layout)
        self.setLayout(self.__main_layout)

    def onAirMode(self)->None:
        self.__on_air_flag = not self.__on_air_flag
        if self.__on_air_flag:
            self.__on_air_button.setText("Go Off Air")
        else:
            self.__on_air_button.setText("Go On Air")
        
        self.onAirClickedSignal.emit(self.__on_air_flag)

    def initHeaderButtons(self)->None:
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.__on_air_button)
        self.__on_air_button.clicked.connect(self.onAirMode)
        self.__main_layout.addLayout(buttons_layout)
    
    def trackedIdsChangedSlot(self, untracked_ids_event: dict)->None:
        # print("Received Event: ", untracked_ids_event)
        if untracked_ids_event["event_name"] == "update_untracked_ids":
            data = untracked_ids_event["event_data"]
            self.__tracked_ids = data["untracked_ids"]
            self.updateTrackedIds()

    def idClickedSlot(self, id)->None:
        if self.__on_air_flag:
            self.idButtonClickedSignal.emit(id)
        else:
            QMessageBox.critical(None, "Error ID Plot", "You can't plot IDs without going on air.")
        
    def updateTrackedIds(self)->None:
        # First update the elements with the IDS
        number_of_ids = len(self.__tracked_ids)
        to_hide_or_create = self.ids_layout.count() - number_of_ids
        # We have buttons that are either more than what we need or exactly what we need.
        if to_hide_or_create >= 0: 
            for idx, id in enumerate(self.__tracked_ids):
                widget = self.ids_layout.itemAt(idx).widget()
                widget.setText(f"{id}")
                widget.setId(id)
                widget.show()

            hide_from = len(self.__tracked_ids)
            for i in range(hide_from, self.ids_layout.count()):
                widget = self.ids_layout.itemAt(i).widget()
                widget.hide()

        # We don't have enough buttons to work with, so we might need to create some
        elif to_hide_or_create < 0:
            update_upto = self.ids_layout.count()
            for idx, id in enumerate(self.__tracked_ids):
                if idx >= update_upto:
                    break
                widget = self.ids_layout.itemAt(idx).widget()
                widget.setText(f"{id}")
                widget.setId(id)
                widget.show()

            for idx in range(update_upto, len(self.__tracked_ids)):
                id = self.__tracked_ids[idx]
                row, col = divmod(idx, 5)
                btn = RoundButtonWidget(id, f"{id}", 50, 50)
                btn.onClickSignal.connect(self.idClickedSlot)
                self.ids_layout.addWidget(btn, row, col)
           
        

