import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QGridLayout, 
                             QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
from threading import Thread, Event 
from kafka import KConsumer
from cfg.paths_config import __MINI_MAP_BG__, __TEAMS_DIR__
from pprint import pprint
import math
import json
from pathlib import Path
class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.__mouse_callback = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.x()
            y = event.y()
            if self.__mouse_callback is not None:
                self.__mouse_callback(*(x, y))

    def registerCallback(self, callback_function)->None:
        self.__mouse_callback = callback_function

    
class ButtonWithID(QPushButton):
    def __init__(self, button_text,  id:dict, parent=None)->None:
        super().__init__(button_text, parent)
        self.__button_text = button_text
        self.__id = id
        self.__button_click_callback = None


    def registerCallback(self, bt_callback)->None:
        self.__button_click_callback = bt_callback
    
    def button_clicked(self)->None:
        self.__button_click_callback(*(self.__id,))

    def get_button_id(self)->int:
        return self.__id
    
        
    
class TrackingData:
    def __init__(self)->None:
        self.__tracking_data = []
        self.__clicked_object = None
        self.__current_clicked_id = None
        self.__associations_table = {}

    def update(self, data)->None:
        if data is not None:
            self.__tracking_data = data
            for det in self.__tracking_data:
                if det.get('tracking-id') == self.__current_clicked_id:
                    det['clicked'] = True

                if det.get('tracking-id') in self.__associations_table:
                    id_struct = self.__associations_table[det.get('tracking-id')]
                    det['player-id'] = id_struct.get('id')
                    det['team'] = id_struct.get('team')
            
                    

    def eucliden_distance(self, point1:tuple, point2:tuple)->float:
        return math.sqrt(((point1[0]-point2[0])**2) + ((point1[1] - point2[1])**2))


    def get_clicked(self, x, y)->dict|None:
        for det in self.__tracking_data:
            if self.eucliden_distance(tuple(det.get('ui_coordinates')), (x,y)) <= 10:
                self.__clicked_object = det
                self.__current_clicked_id = det.get('tracking-id')
                det['clicked'] = True
        
        for det in self.__tracking_data:
            if 'clicked' in det and self.__clicked_object.get('tracking-id') != det.get('tracking-id'):
                det['clicked'] = False

    def get_data(self)->dict:
        return self.__tracking_data
    
    def assign_to_player_to_id(self, id:dict)->None:
        # print(id)
        for det in self.__tracking_data:
            if det.get('clicked'):
                det['player-id'] = id.get('id')
                det['team'] = id.get('team')
                self.__associations_table[det.get('tracking-id')] = id
                self.__current_clicked_id = -1

                # print(det)
    
    def generate_data_for_kafka(self)->str:
        pass

class PlayerIDAssociationApp(QWidget):
    def __init__(self):
        super().__init__()

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.__frame = None
        self.__kafka_consumer = None
        self.__tracking_data = TrackingData()

        self.__team_sheets = None
        self.read_team_sheets()
        self.initUI()

    def setKafkaConsumer(self, kafka_consumer:KConsumer)->None:
        self.__kafka_consumer = kafka_consumer

    def read_team_sheets(self)->None:
        with open((__TEAMS_DIR__ / Path(r'teams.json')).resolve()) as fp:
            data = json.load(fp)
            self.__team_sheets = data


    def initUI(self):
        self.setWindowTitle('Player Tracking Interface')
        # Main layout
        main_layout = QHBoxLayout()
        # Left grid layout
        left_grid = QGridLayout()
        team_a = self.__team_sheets.get('Team A')

        self.left_buttons = [ButtonWithID(f'Player {team}', {'id':team, 'team':0}, self) for i, team in zip(range(11), team_a)]
        for i, btn in enumerate(self.left_buttons):
            btn.registerCallback(self.__tracking_data.assign_to_player_to_id)
            btn.clicked.connect(btn.button_clicked)
            row, col = divmod(i, 2)
            left_grid.addWidget(btn, row, col)

        # Right grid layout
        right_grid = QGridLayout()
        team_b = self.__team_sheets.get('Team B')
        self.right_buttons = [ButtonWithID(f'Player {team}',{'id':team, 'team':1}, self) for i, team in zip(range(11), team_b)]
        for i, btn in enumerate(self.right_buttons):
            btn.registerCallback(self.__tracking_data.assign_to_player_to_id)
            btn.clicked.connect(btn.button_clicked)
            row, col = divmod(i, 2)
            right_grid.addWidget(btn, row, col)

        # Image view
        self.image_label = ClickableLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.registerCallback(self.__tracking_data.get_clicked)

        # Add button to load video
        load_video_button = QPushButton('Start Associations', self)
        load_video_button.clicked.connect(self.open_video_dialog)

        # Layout to include load video button below image
        image_layout = QVBoxLayout()
        image_layout.addWidget(self.image_label)
        image_layout.addWidget(load_video_button)

        # Adding layouts to main layout
        main_layout.addLayout(left_grid)
        main_layout.addLayout(image_layout)
        main_layout.addLayout(right_grid)

        self.setLayout(main_layout)
        self.resize(800, 600)

        # load the mini_map bg
        self.__frame = cv2.imread(__MINI_MAP_BG__.as_posix(), cv2.COLOR_BGR2RGB)
        height, width,  _ = self.__frame.shape
        self.__frame = cv2.resize(self.__frame, (width//2, height//2))
        self.start_updates_timer()

    def open_video_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        video_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov);;All Files (*)", options=options)
        if video_path:
            self.start_video(video_path)

    def start_updates_timer(self):
        self.timer.start(100)  # Update every 30 ms (approx 33 FPS)

    def upload_frame(self, frame:cv2.Mat)->None:
        self.__frame = frame.copy()

    def update_mini_map(self, frame:cv2.Mat, detections)->cv2.Mat:
        width = 0.89 * frame.shape[1] 
        height = 0.895 * frame.shape[0]
        clone_bg = frame
        x_offset = 140//2
        y_offset = 85//2
        color = (255, 255, 0)
        for det in detections:
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
                
                # det.get('color') if det.get('colors') else
                clone_bg = cv2.circle(clone_bg, (x_scaled, y_scaled), 15,  color, cv2.FILLED)

                if det.get('player-id') is not None:
                    clone_bg = cv2.putText(clone_bg, f"{det['player-id']}", (x_scaled-15, y_scaled+5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2)
                else:
                    clone_bg = cv2.putText(clone_bg, f"??", (x_scaled-15, y_scaled+5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2)
                # if det.get('track_id') is not None:
                #     clone_bg = cv.putText(clone_bg, f"{det['track_id']}", (x_scaled-15, y_scaled+5), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2)
        return clone_bg

    def update_frame(self):
        frame = self.__frame.copy()
        if frame is None:
            # self.timer.stop()
            return
        # check if there's any data ready here.  
        if self.__kafka_consumer is not None:
            if self.__kafka_consumer.is_data_ready():
                tracking_data = self.__kafka_consumer.getTrackingData(as_json=True)
                if tracking_data and  'tracks' in tracking_data:
                    self.__tracking_data.update(tracking_data['tracks'])

                self.update_mini_map(frame, self.__tracking_data.get_data())
                

        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))

    def closeEvent(self, event):
        if self.cap is not None:
            self.cap.release()
        event.accept()






if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PlayerIDAssociationApp()
    ex.show()
    sys.exit(app.exec_())
