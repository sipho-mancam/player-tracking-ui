from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QWidget, QApplication, QVBoxLayout, QGridLayout, QHBoxLayout, QSizePolicy, QSpacerItem
from PyQt5.QtGui import QImage, QMouseEvent, QPixmap
from pathlib import Path
import sys
import os
import pprint


__ASSETS_DIR__ = Path(".\\assets")



class PlayerItem(QWidget):
    def __init__(self, position, parent=None)->None:
        super().__init__(parent)
        self.__layout = QVBoxLayout(self)
        self.__icon = QLabel()
        self.__text = QLabel()
        self.__position_widget = QLabel()
        self.__text_edit = QLineEdit()

        self.__player_name = "Sipho Mancam"
        self.__jersey_number = 90
        self.__player_position = position
        self.__updated = False
        self.setLayout(self.__layout)
        self.init()

    def get_player_info(self)->dict:
        return {'player-name':self.__player_name, 'jersey':self.__jersey_number, 'position':self.__player_position}
    
    def is_updated(self)->None:
        return self.__updated

    def init(self)->None:
        self.__position_widget.setText(f"{self.__player_position}")
        self.__position_widget.setObjectName("player-position")
        self.__position_widget.setStyleSheet("#player-position{font-weight:500;color:green;}")
        self.__position_widget.setFixedSize(80,16)
        self.__position_widget.setAlignment(Qt.AlignHCenter)

        path = (__ASSETS_DIR__ / Path('jersey_1.png')).resolve().as_posix()
        icon = QImage(path)
        icon = icon.scaled(80, 40)
        self.__icon.setFixedSize(80, 40)
        self.__icon.setPixmap(QPixmap.fromImage(icon))
        self.__icon.setObjectName('player-jersey-icon')
        self.__icon.setAlignment(Qt.AlignHCenter)
        # self.__icon.setStyleSheet("#player-jersey-icon{border:1px solid black;}")

        self.__text.setText(f"{self.__player_name} - {self.__jersey_number}")
        self.__text.setObjectName('player-name')
        self.__text.setStyleSheet("#player-name{font-weight:500;}")
        self.__text.setFixedHeight(30)
        self.__text.setFixedWidth(200)

        self.__text_edit.hide()
        self.__text_edit.setFixedHeight(24)
        self.__text_edit.setFixedWidth(150)
        self.__text_edit.setPlaceholderText("Player Name")
        self.__text_edit.returnPressed.connect(self.grab_player_name)
        
        self.__layout.addWidget(self.__position_widget)
        self.__layout.addWidget(self.__icon)
        self.__layout.addWidget(self.__text)
        self.__layout.addWidget(self.__text_edit)
        self.setContentsMargins(0, 0, 0, 0)

    def grab_player_name(self):
        text = self.__text_edit.text()
        if not text.isspace() and len(text) > 0:
            self.__player_name = text
            self.__text.setText(self.__player_name)
            self.__text_edit.hide()
            self.__text_edit.setText("")
            self.__text.show()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        # On Click, we hide the text and show a text label to set the text
        self.__text.hide()
        self.__text_edit.show()
        self.__text_edit.setText(self.__player_name)
        self.__updated = True
        return super().mousePressEvent(event)
        # self.__layout.setContentsMargins(0,0,0,0)


class TeamWidget(QWidget):
    def __init__(self, parent=None)->None:
        super().__init__(parent)
        self.__main_layout = QVBoxLayout(self)
        self.__team_name_layout = QHBoxLayout()
        self.__layout = QGridLayout()
        self.__subs_main_layout = QHBoxLayout()
        self.__sub_right_space = QSpacerItem(200, 200, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.__subs_layout = QGridLayout()
        self.__team_name_edit = QLineEdit()
        self.__team_name_text = QLabel()
        self.__subs_title = QLabel("Substitues")
        self.__save_button = QPushButton("Save")
       
        self.__change_team_name = QPushButton("Change Team")

        self.__positions = ["GK", "LOB", "LCB", "RCB", "ROB", "LW", "CM", "DCM", "RW", "ACM", "CF"]
        self.__team_list = [PlayerItem(self.__positions[i]) for i in range(11)]
        self.__subs_list = [PlayerItem("SUB") for _ in range(5)]
        self.__left_team = True
        self.__team_name = "Kaizer Chiefs"
        self.__data = {}

        self.setObjectName("team-show")
        # self.setStyleSheet("#team-show{background-color:#7B7A72; color:white} QWidget{color:white;}")
        self.setLayout(self.__main_layout)
        self.init()

    def team_name_clicked(self):
        self.__team_name_edit.show()
        self.__team_name_text.hide()
        self.__change_team_name.setDisabled(True)
        self.__team_name_edit.setText(self.__team_name)

    def change_team_name(self)->None:
        text = self.__team_name_edit.text()
        self.__team_name_edit.hide()
        
        if not text.isspace() and len(text) > 0:
            self.__team_name = text
            self.__team_name_text.setText(self.__team_name)

        self.__team_name_text.show()
        self.__change_team_name.setEnabled(True)
    
    def save_information(self):
        # Go through all the players and check if they are updated,
        clear_to_save = True
        for player in self.__team_list:
            if not player.is_updated():
                clear_to_save = False
                break
        
        for sub in self.__subs_list:
            if not sub.is_updated():
                clear_to_save = False

        if clear_to_save:
            # Collect the data into an object and save
            
            for player in self.__team_list:
                if 'players' not in self.__data:
                    self.__data['players'] = []
                self.__data['players'].append(player.get_player_info())

            for sub in self.__subs_list:
                if 'subs' not in self.__data:
                    self.__data['subs'] = []
                self.__data['subs'].append(sub.get_player_info())
            self.__data['team_name'] = self.__team_name

            # Update the controller and send a signal 

        else:
            # Open and Error Dialog
            pass

    def init(self)->None:
        self.__team_name_text.setText(self.__team_name)
        self.__team_name_text.setFixedSize(500, 25)
        self.__team_name_text.setObjectName("team-name")
        self.__team_name_text.setStyleSheet("#team-name{font-weight:500;font-size:16px;border:1px solid #777;}")
        self.__team_name_text.setAlignment(Qt.AlignLeft)

        self.__team_name_edit.setPlaceholderText('Team Name')
        self.__team_name_edit.setFixedSize(400, 25)
        self.__team_name_edit.setObjectName('team-name-edit')
        self.__team_name_edit.setStyleSheet("#team-name-edit{font-size:16px;}")
        self.__team_name_edit.hide()
        self.__team_name_edit.returnPressed.connect(self.change_team_name)

        self.__change_team_name.setFixedSize(100, 25)
        self.__change_team_name.clicked.connect(self.team_name_clicked)

        self.__team_name_layout.addWidget(self.__team_name_text)
        self.__team_name_layout.addWidget(self.__team_name_edit)
        self.__team_name_layout.addWidget(self.__change_team_name)
        self.__team_name_layout.setAlignment(Qt.AlignLeft)
        
        self.__layout.addWidget(self.__team_list[0], 1, 0)
        for i in range(1, 5):
            self.__layout.addWidget(self.__team_list[i], i-1, 1)
            self.__layout.addWidget(self.__team_list[i+4], i-1, 2)

        self.__layout.addWidget(self.__team_list[9], 1, 3)
        self.__layout.addWidget(self.__team_list[10], 2, 3)

        self.__subs_title.setObjectName("sub-title")
        self.__subs_title.setStyleSheet("#sub-title{font-size:16px; font-weight:500; border:1px solid #777;}")
        self.__subs_title.setAlignment(Qt.AlignLeft)
        self.__subs_title.setFixedHeight(25)
        self.__subs_layout.setSpacing(0)
        for j, sub in enumerate(self.__subs_list):
            row, col = divmod(j, 4)
            sub.setContentsMargins(0,0,0,0)
            sub.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.__subs_layout.addWidget(sub, row, col, Qt.AlignLeft)
        self.__subs_main_layout.addLayout(self.__subs_layout)
        self.__subs_layout.addItem(self.__sub_right_space)

        self.__save_button.setFixedWidth(200)
        self.__save_button.clicked.connect(self.save_information)
        # self.__save_button.setDisabled(True)

        self.__main_layout.addLayout(self.__team_name_layout)
        self.__main_layout.addLayout(self.__layout)
        self.__main_layout.addWidget(self.__subs_title)
        self.__main_layout.addLayout(self.__subs_main_layout)
        self.__main_layout.addWidget(self.__save_button)




if __name__ == "__main__":
    app = QApplication(sys.argv)

    player = TeamWidget()
    player.show()

    app.exec_()