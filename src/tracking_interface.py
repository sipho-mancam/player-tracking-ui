import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QGridLayout, 
                             QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QFrame,
                             QDialog, QDialogButtonBox, QComboBox, QLineEdit)
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5.QtCore import Qt, QTimer
from threading import Thread, Event 
from kafka import KConsumer, KProducer
from cfg.paths_config import __MINI_MAP_BG__, __TEAMS_DIR__
from pprint import pprint
import math
import json
from pathlib import Path
from team_states import TeamsManager
from formations import FormationsManager
from team_information_view.controller import MatchController

class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.__mouse_callback = None
        self.__doing_formations = False
        self.__formations_cb = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.x()
            y = event.y()
            if self.__mouse_callback is not None:
                if self.__doing_formations:
                    self.__formations_cb(*(event,))
                else:
                    self.__mouse_callback(*(x, y))

    def registerCallback(self, callback_function)->None:
        self.__mouse_callback = callback_function

    def registerFormationsCB(self, _cb):
        self.__formations_cb = _cb

    def clearFormationsRoutine(self)->None:
        self.__doing_formations = False

    def setFormationsRoutine(self)->None:
        self.__doing_formations = True

class StyledButton(QPushButton):
    def __init__(self, text='', parent=None)->None:
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedWidth(120)
        self.setStyleSheet(self.default_style())

    def default_style(self):
        return """
            QPushButton {
                border-radius:10px;
                border-style: outset;
                background: #f00;
                padding: 5px;
                color: #eee;
                font-weight:500;
            }
            QPushButton:pressed {
                background: #aaa;
            }
        """
    
    def toggled_style(self):
        return """
            QPushButton {
                border-radius:10px;
                border-style: outset;
                background: #7fc97f;
                padding: 5px;
                color: #fff;
            }
            QPushButton:pressed {
                background: #679267;
            }
        """
    
    def toggle_color(self):
        if self.isChecked():
            self.setStyleSheet(self.toggled_style())
        else:
            self.setStyleSheet(self.default_style())
    
class ButtonWithID(QPushButton):
    def __init__(self, button_text,  id:dict, parent=None)->None:
        super().__init__(button_text, parent)
        self.__button_text = button_text
        self.__id = id
        self.__button_click_callback = None
        self.setFixedSize(100, 40)  # Set fixed size to make it circular
        self.setStyleSheet("""
                    QPushButton {
                        border: 0px solid #555;
                        border-radius: 20px;
                        border-style: outset;
                        background: #ddd;
                        padding: 10px;
                        
                    }
                    QPushButton:pressed {
                        background: #aaa;
                    }
                """)
    def registerCallback(self, bt_callback)->None:
        self.__button_click_callback = bt_callback
    
    def button_clicked(self)->None:
        self.__button_click_callback(*(self.__id,))

    def get_button_id(self)->int:
        return self.__id
    
    def get_position(self)->str:
        return self.__id.get('position')

    def set_jersey_number(self, id)->None:
        self.__id['jersey_number'] = id
        self.__id['id'] = id

    def set_id(self, id)->None:
        self.__id['id'] = id
        self.__id['jersery_number'] = id
        self.setText(f"{self.__id['position']} -  {id}")
        
class TrackingData:
    def __init__(self)->None:
        self.__tracking_data = []
        self.__clicked_object = None
        self.__current_clicked_id = None
        self.__associations_table = {}
        self.__kafka_producer = None
        self.__teams_manager = None
        self.__frame_counter = 0
        self.__players_highlighted = {}
        self.__toggle_connections = False
        self.__toggle_highlight = False
        self.__connections_list = []

    def get_teams_manager(self)->TeamsManager:
        return self.__teams_manager
    
    def set_formations_data(self, formations_data:list, team:int)->None:
        data = []
        obj = {}

        for i, coord in enumerate(formations_data):
            obj['coordinates'] = coord
            obj['tracking-id'] = i + team*12
            data.append(obj)
            obj = {}
        self.__tracking_data = data

    def update(self, data, associate=False)->None:
        if data is not None:
            self.__tracking_data = data

            if associate and not self.__teams_manager.is_associations_init():
                # Perform associations here 
                self.__teams_manager.perform_associations(self.__tracking_data)

            for det in self.__tracking_data:
                if det.get('tracking-id') == self.__current_clicked_id:
                    det['clicked'] = True

                if det.get('tracking-id') in self.__associations_table:
                    id_struct = self.__associations_table[det.get('tracking-id')]
                    det['player-id'] = id_struct.get('id')
                    det['team'] = id_struct.get('team')

                    player = self.__players_highlighted.get(det.get('player-id'))
                    if player is not None and det.get('team') == player['team']:
                        det['highlight'] = player['id']
            
            self.update_connections_list(self.__tracking_data)
            self.update_connections_links()

            self.__frame_counter += 1
            if self.__teams_manager is not None:
                self.__teams_manager.update_team(self.__tracking_data)

    def update_connections_list(self, dets)->None:
        for det in dets:
            for connection in self.__connections_list:
                if det.get('player-id') is not None and connection.get('player-id') == det.get('player-id') and connection.get('team') == det.get('team'):
                    connection['coordinates'] = det['coordinates']
                    break;
    
    def update_connections_links(self)->None:
        for idx, connection in enumerate(self.__connections_list):
            if idx > 0:
                connection['next_link'] = self.__connections_list[idx-1].get('coordinates')
    
    def set_kafka_producer(self, producer:KProducer)->None:
        self.__kafka_producer = producer

    def set_teams_manager(self, teams_man:TeamsManager)->None:
        self.__teams_manager = teams_man

    def publish(self)->None:
        if self.__kafka_producer is not None:
            json_string = json.dumps({'tracks':self.__teams_manager.get_tracking_data(), 'frame_number':self.__frame_counter})
            self.__kafka_producer.send_message('system-data', json_string)    

    def eucliden_distance(self, point1:tuple, point2:tuple)->float:
        return math.sqrt(((point1[0]-point2[0])**2) + ((point1[1] - point2[1])**2))

    def get_clicked(self, x, y)->dict|None:
        for det in self.__tracking_data:
            if self.eucliden_distance(tuple(det.get('ui_coordinates')), (x,y)) <= 20:
                self.__clicked_object = det
                self.__current_clicked_id = det.get('tracking-id')
                
                if self.__toggle_highlight and det.get('player-id') and (det.get('highlight') == 0 or det.get('highlight') is None):
                    det['highlight'] = 1

                elif self.__toggle_highlight and (det.get('player-id') and det.get('highlight') == 1):
                    det['highlight'] = 0
                
                if det.get('player-id'):
                     self.__players_highlighted[det.get('player-id')]  =  {'id':det.get('highlight'), 'team':det.get('team')}
                det['clicked'] = True

                # Do the connections here
                if self.__toggle_connections and det.get('player-id'):
                    # You are connected, I'm clearing it.
                    idx = self.find_connected(det)
                    if idx >= 0:
                        self.__connections_list.pop(idx)
                        continue

                    # This assumes you are currently not connected
                    det['connected'] = self.__toggle_connections
                    det['next_link'] = self.__connections_list[-1].get('coordinates') if len(self.__connections_list) > 0 else det.get('coordinates')
                    self.__connections_list.append(det)
                         
        for det in self.__tracking_data:
            if 'clicked' in det and self.__clicked_object.get('tracking-id') != det.get('tracking-id'):
                det['clicked'] = False

    def find_connected(self, det)->int:
        for idx, con in enumerate(self.__connections_list):
            if con.get('player-id') == det.get('player-id') and con.get('team') == det.get('team'):
                return idx
        return -1

    def get_data(self)->dict:
        return self.__tracking_data
    
    def assign_to_player_to_id(self, id:dict)->None:
        for det in self.__tracking_data:
            if det.get('clicked'):
                det['player-id'] = id.get('id')
                det['team'] = id.get('team')
                self.__associations_table[det.get('tracking-id')] = id
                self.__current_clicked_id = -1

    def search_id(self, id:dict)->str:
        for key in self.__associations_table.keys():
            t_id = self.__associations_table[key]
            if (t_id.get('id') is not None) and t_id.get('id') == id.get('id') and (t_id.get('team') is not None) and id.get('team') == t_id.get('team'):
                return key

    def get_connections_list(self)->list|None:
        if len(self.__connections_list) <= 1:
            return None
        return self.__connections_list

    def toggle_connections(self)->None:
        self.__toggle_connections = not self.__toggle_connections
        self.__connections_list = []

    def toggle_highlight(self)->None:
        self.__toggle_highlight = not self.__toggle_highlight
      
class CustomDialog(QDialog):
    def __init__(self, formationsList:list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Formation")

        # Dialog layout
        layout = QVBoxLayout()
        # ComboBox
        self.combo_box = QComboBox()
        new_list = [s for s in formationsList]
        new_list.append("custom")
        self.combo_box.addItems(new_list)
        layout.addWidget(self.combo_box)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_selected_option(self):
        return self.combo_box.currentText()


class AddFormation(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Formation")

        # Dialog layout
        layout = QVBoxLayout()
        # ComboBox
        self.formation_name = QLineEdit(self)
        self.formation_name.setPlaceholderText('4-4-2')
        layout.addWidget(self.formation_name)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_formation_name(self):
        return self.formation_name.text()
    

class SaveFormation(QDialog):
     def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Formation")

        # Dialog layout
        layout = QVBoxLayout()
        # ComboBox
        self.formation_name = QLabel('Save Formation',self)
        layout.addWidget(self.formation_name)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)


class PlayerIDAssociationApp(QWidget):
    def __init__(self, match_controller:MatchController, parent=None):
        super().__init__(parent)
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.__frame = None
        self.__kafka_consumer = None
        self.__tracking_data = TrackingData()
        self.__kafka_producer = None
        # self.__team_sheets = None
        # self.__formations_manager = FormationsManager()
        self.__init_associations = False

        self.__match_controller = match_controller
        self.__match_data = None
          # Main layout
        self.main_layout = QVBoxLayout()
        # Left grid layout
        self.top_bar = QHBoxLayout()
        self.middle_layout = QHBoxLayout()
        self.bottom_layout = QHBoxLayout()
        self.__teams_buttons = []
        self.__teams_widgets = []
        # self.read_team_sheets()
        self.initUI()
        self.__match_controller.set_player_tracking_interface(self)

    def setKafkaConsumer(self, kafka_consumer:KConsumer)->None:
        self.__kafka_consumer = kafka_consumer

    def setKafkaProducer(self, producer)->None:
        self.__kafka_producer = producer
        self.__tracking_data.set_kafka_producer(producer)

    def read_team_sheets(self)->None:
        with open((__TEAMS_DIR__ / Path(r'teams.json')).resolve()) as fp:
            data = json.load(fp)
            self.__team_sheets = data

    def init_associations(self)->None:
        # if not self.__init_associations
        self.__init_associations = True

    def init_team(self, left:bool)->None:
        self.__teams_widgets.append({})
        team_data = self.__match_controller.get_team_data(left)
        players = team_data.get('players')
        current_index = 0 if left else 1

        left_vertical_layout = QVBoxLayout()
        left_grid = QGridLayout()
      
        self.buttons = [ButtonWithID(f'{player.get("position")}  - {player.get("jersey_number")}', 
                                     {'id':int(player.get("jersey_number")), 'team':0 if left else 1, 'position':player.get("position")}, 
                                    self) for  player in players]
        
        self.__teams_buttons.insert(current_index, self.buttons)

        self.__teams_widgets[current_index]['buttons'] = self.buttons

        for i, btn in enumerate(self.buttons):
            btn.registerCallback(self.__tracking_data.assign_to_player_to_id)
            btn.clicked.connect(btn.button_clicked)
            row, col = divmod(i, 3)
            left_grid.addWidget(btn, row, col)
        
        team_a_text = QLabel(team_data.get("name"), self)
        self.__teams_widgets[current_index]['team_name'] = team_a_text
        
        team_a_text.setStyleSheet(""" 
                                QLabel {
                                  font-weight:500;
                                  font-size:20px;
                                }
                                """)
        left_grid.addWidget(team_a_text, 4, 0, 1, 3)
        left_vertical_layout.addLayout(left_grid)
        left_vertical_layout.setAlignment(Qt.AlignTop)
        self.bottom_layout.addLayout(left_vertical_layout)

    def update_match_info(self, match_info:list)->None:
        self.__match_data = match_info
        for idx, team in enumerate(match_info):
            self.__teams_widgets[idx]['team_name'].setText(team.get('name'))
            for player in team['players']:
                # find the button associated with this player
                id = player.get('jersey_number')
                for button in self.__teams_widgets[idx]['buttons']:
                    if button.get_position() == player.get('position'):
                        button.set_id(id)
    
    def init_top_bar(self)->None:
        self.connect_button = StyledButton('Connect Players', self)
        self.connect_button.clicked.connect(self.connect_button.toggle_color)
        self.connect_button.clicked.connect(self.__tracking_data.toggle_connections)

        self.start_associations = StyledButton('Start Associations', self)        
        self.start_associations.clicked.connect(self.start_associations.toggle_color)
        self.start_associations.clicked.connect(self.init_associations)

        self.highlight_button = StyledButton('Start Highlighting', self)
        self.highlight_button.clicked.connect(self.highlight_button.toggle_color)
        self.highlight_button.clicked.connect(self.__tracking_data.toggle_highlight)

        self.top_bar.addWidget(self.start_associations)
        self.top_bar.addWidget(self.connect_button)
        self.top_bar.addWidget(self.highlight_button)
        self.top_bar.setAlignment(Qt.AlignLeft)

    def initUI(self):
        self.setWindowTitle('Player Tracking Interface')
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowMinimizeButtonHint)        
         
        self.top_bar.setContentsMargins(0, 0, 0, 0)
        self.middle_layout.setContentsMargins(0,0,0,0)
        self.bottom_layout.setContentsMargins(0,0,0,0)

        self.init_top_bar()

        # Initialize team A (Left Team)
        self.init_team(True)
        #Initialize Team B (Right Team)
        self.init_team(False)

        # Image view
        self.image_label = ClickableLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.registerCallback(self.__tracking_data.get_clicked)
        
        image_layout = QVBoxLayout()
        image_layout.addWidget(self.image_label)
        image_layout.setContentsMargins(0,0,0,0)
        self.middle_layout.addLayout(image_layout)

        # Adding layouts to main layout
        self.main_layout.addLayout(self.top_bar)
        self.main_layout.addLayout(self.middle_layout)
        self.main_layout.addLayout(self.bottom_layout)
        self.setLayout(self.main_layout)
        self.resize(800, 600)

        # load the mini_map bg
        self.__frame = QImage(__MINI_MAP_BG__.as_posix())
        height, width,  _ = self.__frame.height(), self.__frame.width(), 3
        self.__frame = self.__frame.scaled(width//2, height//2-100)
        self.image_label.setFixedSize(width//2, height//2-100)
        self.image_label.setMargin(0)
        self.image_label.setPixmap(QPixmap.fromImage(self.__frame))
        self.image_label.setObjectName("frame_view")
        self.image_label.setStyleSheet("#frame_view{border:1px solid black;}")

        self.__frame = cv2.imread(__MINI_MAP_BG__.as_posix())
        self.__frame = cv2.resize(self.__frame, (width//2, height//2-100))

        self.start_updates_timer()
        self.show()
        self.setFixedSize(self.size())
    
    def update(self):
        frame = self.__frame.copy()
        if frame is None:
            return
    
        frame = self.render_team(frame, self.__match_controller.get_team_data(True))
        frame = self.render_team(frame, self.__match_controller.get_team_data(False))
        # self.__kafka_consumer is not None
        # if self.__kafka_consumer.is_data_ready():
        #     tracking_data = self.__kafka_consumer.getTrackingData(as_json=True)
        #     if tracking_data and  'tracks' in tracking_data:
        #         self.__tracking_data.update(tracking_data['tracks'], self.__init_associations)
        #         self.__tracking_data.publish()
        #         self.__init_associations = False
        #     self.update_mini_map(frame, self.__tracking_data.get_data())

        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))


    # def open_video_dialog(self):
    #     options = QFileDialog.Options()
    #     options |= QFileDialog.ReadOnly
    #     video_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov);;All Files (*)", options=options)
    #     if video_path:
    #         self.start_video(video_path)

    def start_updates_timer(self):
        self.timer.start(50)  # Update every 30 ms (approx 33 FPS)

    def upload_frame(self, frame:cv2.Mat)->None:
        self.__frame = frame.copy()

    def draw_connection_line(self, frame:cv2.Mat, point1, point2, offsets, dimensions)->cv2.Mat:
        x1, y1 = point1
        # print(point2)
        x2, y2 = point2
        x_offset, y_offset = offsets
        width, height = dimensions

        x1 = x_offset + (x1*width)
        y1 = y_offset + (y1*height)

        x2 = x_offset + (x2*width)
        y2 = y_offset + (y2*height)

        frame = cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 255), 2)
        return frame
    
    def update_connections(self, frame:cv2.Mat, offsets, dimensions)->cv2.Mat:
        connections = self.__tracking_data.get_connections_list()
        if connections is not None:
            for i, c in enumerate(connections):
                if i > 0:
                    point1 = c.get('coordinates')
                    point2 = c.get('next_link')
                    frame = self.draw_connection_line(frame, point1, point2, offsets, dimensions)
        return frame
    
    def render_team(self, frame, team_info)->None:
        width = 0.89 * frame.shape[1] 
        height = 0.895 * frame.shape[0]
        clone_bg = frame
        x_offset = 140//2
        y_offset = 85//2
        color = team_info['color']

        cr = QColor(color)
        color = (cr.red(), cr.green(), cr.blue())

        for _, det in enumerate(team_info['players']):
            coord = det['coordinates'] 
            if coord is not None :
                x_scaled = x_offset + int(coord[0]*width)
                y_scaled = y_offset + int(coord[1]*height)
                det['ui_coordinates'] = (x_scaled, y_scaled)

                clone_bg = cv2.circle(clone_bg, (x_scaled, y_scaled), 15,  color, cv2.FILLED)

                if det.get('jersey_number') is not None:
                    if det.get('highlight') == 1:
                        text_color = (255, 0, 0)
                    else:
                        text_color = (255, 255, 255)

                    clone_bg = cv2.putText(clone_bg, f"{det.get('jersey_number')}", (x_scaled-5, y_scaled+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
        return clone_bg
    
    def update_mini_map(self, frame:cv2.Mat, detections)->cv2.Mat:
        width = 0.89 * frame.shape[1] 
        height = 0.895 * frame.shape[0]
        clone_bg = frame
        x_offset = 140//2
        y_offset = 85//2
        color = (255, 255, 0)
        self.update_connections(clone_bg, (x_offset, y_offset), (width, height))
        for _, det in enumerate(detections):
            coord = det['coordinates'] 
            # print(coord)
            if coord is not None :#and det.get('track_id') is not None:
                x_scaled = x_offset + int(coord[0]*width)
                y_scaled = y_offset + int(coord[1]*height)
                det['ui_coordinates'] = (x_scaled, y_scaled)
                if det.get('is_overlap') is not None and det.get('is_overlap'):
                    color = (0, 0, 255)
                else:
                    color = det.get('color') if det.get('color') is not None else (255, 255, 255)

                    if det.get('clicked') is not None and det.get('clicked'):
                        color = (255, 0, 0)

                    if det.get('player-id'):
                        if det.get('team') == 0:
                            color = (0, 254, 233)
                        elif det.get('team') == 1:
                            color = (0, 244, 0)

                if det.get('is_child'):
                    color = (255, 0, 255)
                
                clone_bg = cv2.circle(clone_bg, (x_scaled, y_scaled), 15,  color, cv2.FILLED)

                if det.get('player-id') is not None:
                    if det.get('highlight') == 1:
                        text_color = (255, 0, 0)
                    else:
                        text_color = (0, 0,  0)
                    
                    clone_bg = cv2.putText(clone_bg, f"{det['player-id']}", (x_scaled, y_scaled+5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
                else:
                    clone_bg = cv2.putText(clone_bg, f"??", (x_scaled, y_scaled+5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2)
        return clone_bg

   
        

    def closeEvent(self, event):
        if self.cap is not None:
            self.cap.release()
        event.accept()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PlayerIDAssociationApp()
    ex.show()
    sys.exit(app.exec_())
