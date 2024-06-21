from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import (QLabel, QLineEdit, QPushButton, QWidget, QApplication, 
                            QVBoxLayout, QGridLayout, QHBoxLayout, QSizePolicy, 
                            QSpacerItem, QComboBox, QColorDialog, QMessageBox, QDialog, QDialogButtonBox)
from PyQt5.QtSvg import (QSvgWidget, QSvgRenderer)
from PyQt5.QtGui import QImage, QMouseEvent, QPixmap, QPainter, QPen, QColor
from PyQt5.QtXml import QDomDocument
from pathlib import Path
import sys
import os
import pprint

__ASSETS_DIR__ = Path(".\\assets")

class SvgManipulator(QWidget):
    def __init__(self, jersey_number, color, parent=None):
        super().__init__(parent)
        self.svg_path = (__ASSETS_DIR__ / 'jersey.svg').resolve().as_posix()

        # Load SVG content into QDomDocument
        self.dom_document = QDomDocument()
        with open(self.svg_path, 'r') as f:
            self.dom_document.setContent(f.read())
        # Manipulate the SVG DOM
        self.set_color(f"{color}")
        self.set_jersey_number(f"{jersey_number}")
        # Render the manipulated SVG
        self.renderer = QSvgRenderer(self.dom_document.toByteArray())
        # Setup UI
        self.init_ui()

    def set_color(self, color:str)->None:
        elems = self.dom_document.elementsByTagName('polygon')
        for i in range(elems.count()):
            elem = elems.item(i).toElement()
            elem.setAttribute('fill', color)
    
    def set_jersey_number(self, number:int|str)->None:
        elements = self.dom_document.elementsByTagName("text")
        for i in range(elements.count()):
            element = elements.item(i).toElement()
            element.setAttribute("fill", "white")
            element.firstChild().setNodeValue(f"{number}")
            

    def init_ui(self):
        layout = QVBoxLayout(self)
        # Create a QLabel to display the SVG
        self.label = QLabel()
        layout.addWidget(self.label)
        # Render the SVG to a QPixmap and display it
        pixmap = QPixmap(80, 40)  # Specify the desired size
        pixmap.fill(Qt.transparent)  # Ensure the background is transparent
        painter = QPainter(pixmap)
        self.renderer.render(painter)
        painter.end()
        self.label.setPixmap(pixmap)
        
        

class PlayerItem(QWidget):
    def __init__(self, position, parent=None)->None:
        super().__init__(parent)
        self.__layout = QVBoxLayout(self)
        self.__icon = QLabel()
        self.__text = QLabel()
        self.__position_widget = QLabel()
        self.__text_edit = QLineEdit()

        self.__player_name = "90"
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
        self.__icon.setFixedSize(80, 45)
        self.__icon.setPixmap(QPixmap.fromImage(icon))
        self.__icon.setObjectName('player-jersey-icon')
        # self.__icon.
        # self.__icon.setStyleSheet("#player-jersey-icon{border:1px solid black; padding: 0px;}")
        # self.__icon.setAlignment(Qt.AlignHCenter)
      
        self.__text.setText(f"{self.__player_name}")
        self.__text.setObjectName('player-name')
        self.__text.setStyleSheet("#player-name{font-weight:500;color:grey;}")
        self.__text.setFixedHeight(16)
        self.__text.setFixedWidth(80)
        self.__text.setAlignment(Qt.AlignHCenter)

        self.__text_edit.hide()
        self.__text_edit.setFixedHeight(16)
        self.__text_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.__text_edit.setFixedWidth(80)
        self.__text_edit.setPlaceholderText("Player Name")
        self.__text_edit.returnPressed.connect(self.grab_player_name)
        self.__text_edit.setAlignment(Qt.AlignCenter)
        
        self.__layout.addWidget(self.__position_widget)
        self.__layout.addWidget(self.__icon)
        self.__layout.addWidget(self.__text)
        self.__layout.addWidget(self.__text_edit)
        self.setContentsMargins(0, 0, 0, 0)
        self.setObjectName("player-object")
        self.setStyleSheet("#player-object{border:1px solid black;}")

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

class PlayerStatsDialog(QDialog):
    def __init__(self, player_stats:dict, parent=None)->None:
        super().__init__(parent)
        self.__layout = QVBoxLayout()
        self.__player_info  = player_stats

        for key in self.__player_info.keys():
            player_name_view = QLabel(f"{key.upper()}:\t{self.__player_info[key]}")
            self.__layout.addWidget(player_name_view)

         # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        self.__layout.addWidget(self.button_box)
        self.setLayout(self.__layout)

class PlayerView(QWidget):
    def __init__(self, position, number, color, parent=None)->None:
        super().__init__(parent)
        self.__position = position
        self.__jersey_number = number
        self.__color = color

        self.__position_w = QLabel()
        self.__icon_w = None
        self.__number_w = QLabel()
        self.__layout = QVBoxLayout()
        self.setObjectName("player-view")
        self.setStyleSheet("#player-view{font-weight:500;}")
        self.init()
    
    def init(self)->None:
        self.__position_w.setText(f"{self.__position}")
        self.__position_w.setFixedSize(100, 16)
        self.__position_w.setAlignment(Qt.AlignHCenter)
        self.__position_w.setObjectName("position-view")
        self.__position_w.setStyleSheet("#position-view{font-weight:500; color:green;}")

        # self.__icon_w.setPixmap(self.__prepare_icon())
        # self.__icon_w.setPixmap(self.__prepare_icon())
        self.__icon_w = SvgManipulator(self.__jersey_number, self.__color)#self.__prepare_icon()
        self.__icon_w.setObjectName("icon-view")
        # self.__icon_w.setStyleSheet("#icon-view{border:1px solid black;}")
        self.__icon_w.setFixedSize(100, 80)

        self.__number_w.setText(f"{self.__jersey_number}")
        self.__number_w.setFixedSize(100, 16)
        self.__number_w.setAlignment(Qt.AlignHCenter)
        self.__number_w.setObjectName("jersey-view")
        self.__number_w.setStyleSheet("#jersey-view{font-weight:500; color:grey;}")

        self.__layout.addWidget(self.__position_w)
        self.__layout.addWidget(self.__icon_w)
        self.__layout.addWidget(self.__number_w)

        self.setLayout(self.__layout)

    def __prepare_icon(self)->QLabel:
        self.svg_holder = SvgManipulator(self.__jersey_number, self.__color)
        return self.svg_holder
    
    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        player_stats = PlayerStatsDialog({'jersey_number':self.__jersey_number, 'Position':self.__position})
        player_stats.show()
        player_stats.exec_()

        return super().mousePressEvent(event)

class TeamLoadWidget(QWidget):
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
        self.__line_up_title = QLabel("Starting Line-up")
        self.__save_button = QPushButton("Save")
        self.__formations_dd = QComboBox()
        self.__formations_default_text = "Select Formation"
        self.__team_color_button = QPushButton("Select Team Color")
        self.__bottom_layout = QHBoxLayout()
       
        self.__change_team_name = QPushButton("Change Team")

        self.__positions = ["GK", "LOB", "LCB", "RCB", "ROB", "LW", "CM", "DCM", "RW", "ACM", "CF"]
        self.__team_list = [PlayerItem(self.__positions[i]) for i in range(11)]
        self.__subs_list = [PlayerItem("SUB") for _ in range(5)]
        self.__left_team = True
        self.__team_name = "Kaizer Chiefs"
        self.__team_formation = ""
        self.__team_color = ""
        self.__whats_missing = ""
        self.__data = {}

        self.setObjectName("team-show")
        self.setLayout(self.__main_layout)
        self.init()
   
    def init(self)->None:
        self.__team_name_text.setText(self.__team_name)
        self.__team_name_text.setFixedSize(500, 25)
        self.__team_name_text.setObjectName("team-name")
        self.__team_name_text.setStyleSheet("#team-name{font-weight:500;font-size:14px;border:1px solid #777; color:grey;}")
        self.__team_name_text.setAlignment(Qt.AlignLeft)
        self.__team_name_text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.__team_name_edit.setPlaceholderText('Team Name')
        self.__team_name_edit.setFixedSize(500, 25)
        self.__team_name_edit.setObjectName('team-name-edit')
        self.__team_name_edit.setStyleSheet("#team-name-edit{font-size:16px;}")
        self.__team_name_edit.setAlignment(Qt.AlignLeft)
        self.__team_name_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.__team_name_edit.hide()
        self.__team_name_edit.returnPressed.connect(self.change_team_name)

        self.__change_team_name.setFixedSize(100, 25)
        self.__change_team_name.clicked.connect(self.team_name_clicked)

        self.__formations_dd.addItem(self.__formations_default_text)
        self.__formations_dd.setFixedWidth(200)

        self.__team_name_layout.addWidget(self.__team_name_text)
        self.__team_name_layout.addWidget(self.__team_name_edit)
        self.__team_name_layout.addWidget(self.__change_team_name)
        self.__team_name_layout.addWidget(self.__formations_dd)
        self.__team_name_layout.setAlignment(Qt.AlignLeft)
        self.__team_name_layout.setContentsMargins(0,0,0,0)
        # self.__team_name_layout.setSizeConstraint(self.__team_name_layout.sizeConstraint())
        

        self.__line_up_title.setObjectName("line-up-title")
        self.__line_up_title.setStyleSheet("#line-up-title{font-size:14px; font-weight:500; border:1px solid grey; color:grey;}")
        self.__line_up_title.setAlignment(Qt.AlignLeft)
        self.__line_up_title.setFixedHeight(20)
    
        self.__layout.addWidget(self.__team_list[0], 1, 0)
        for i in range(1, 5):
            self.__layout.addWidget(self.__team_list[i], i-1, 1)
            self.__layout.addWidget(self.__team_list[i+4], i-1, 2)

        self.__layout.addWidget(self.__team_list[9], 1, 3)
        self.__layout.addWidget(self.__team_list[10], 2, 3)

        self.__subs_title.setObjectName("sub-title")
        self.__subs_title.setStyleSheet("#sub-title{font-size:14px; font-weight:500; border:1px solid grey; color:grey;}")
        self.__subs_title.setAlignment(Qt.AlignLeft)
        self.__subs_title.setFixedHeight(20)
       
        for j, sub in enumerate(self.__subs_list):
            row, col = divmod(j, 4)
            self.__subs_layout.addWidget(sub, row, col)

        self.__subs_main_layout.addLayout(self.__subs_layout)
        # self.__subs_layout.addItem(self.__sub_right_space)

        self.__save_button.setFixedWidth(200)
        self.__save_button.clicked.connect(self.save_information)

        self.__team_color_button.setFixedWidth(200)
        self.__team_color_button.clicked.connect(self.select_team_color)

        self.__bottom_layout.addWidget(self.__save_button, alignment=Qt.AlignLeft)
        self.__bottom_layout.addWidget(self.__team_color_button, alignment=Qt.AlignRight)

        self.__main_layout.addLayout(self.__team_name_layout)
        self.__main_layout.addWidget(self.__line_up_title)
        self.__main_layout.addLayout(self.__layout)
        self.__main_layout.addWidget(self.__subs_title)
        self.__main_layout.addLayout(self.__subs_main_layout)
        self.__main_layout.addLayout(self.__bottom_layout)

    def team_name_clicked(self):
        self.__team_name_text.hide()
        self.__team_name_edit.show()
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
                self.__whats_missing = "Please make sure all the players in the starting line up are added."
                break
        
        if clear_to_save:
            for sub in self.__subs_list:
                if not sub.is_updated():
                    clear_to_save = False
                    self.__whats_missing = "Please make sure all the subs are added."
         
        if clear_to_save:
            formation = self.__formations_dd.currentText()
            if formation == self.__formations_default_text:
                clear_to_save  = False
                self.__whats_missing = "Please select formation"
            else:
                self.__team_formation = formation


        if clear_to_save:
            if len(self.__team_color) == 0:
                self.__whats_missing = "Please make sure to select the team's color"
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
            self.__data['color'] = self.__team_color
            self.__data['formation'] = self.__team_formation
            # Update the controller and send a signal 

        else:
            # Open and Error Dialog
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setWindowTitle("Error")
            # msgBox.setTitle("Error")
            msgBox.setText(self.__whats_missing)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()

    def select_team_color(self)->None:
        color = QColorDialog.getColor()
        if color.isValid():
           self.__team_color = color.name()



class TeamViewWidget(QWidget):
    def __init__(self, color, left = True, parent=None)->None:
        super().__init__(parent)
        self.__positions = ["GK", "LOB", "LCB", "RCB", "ROB", "LW", "CM", "DCM", "RW", "ACM", "CF"]
        self.__players = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        self.__color = color
        self.__formation = "4-4-2"
        self.__team_name = "Kaizer Chiefs"
        self.__left_team = left

        self.__players_w = [PlayerView(self.__positions[j], self.__players[j], color) for j in range(11)]
        self.__layout = QGridLayout()
        self.__bottom_layout = QVBoxLayout()
        self.__main_layout = QVBoxLayout()

        self.init()
        widgSize = self.sizeHint()
        widgSize.setHeight(widgSize.height()+60)
        self.setFixedSize(widgSize)

    def init(self)->None:
        if self.__left_team:
            self.arrange_left_players()
        else:
            self.arrange_right_players()

        self.add_team_stats()

        self.__main_layout.addLayout(self.__layout)
        self.__main_layout.addLayout(self.__bottom_layout)
        self.setLayout(self.__main_layout)

    def arrange_left_players(self)->None:
        self.__layout.addWidget(self.__players_w[0], 1, 0)

        for i in range(1, 5):
            self.__layout.addWidget(self.__players_w[i], i-1, 1)
            self.__layout.addWidget(self.__players_w[i+4],i-1, 2)
        
        self.__layout.addWidget(self.__players_w[9], 1, 3)
        self.__layout.addWidget(self.__players_w[10], 2, 3)

    def arrange_right_players(self)->None:
        self.__layout.addWidget(self.__players_w[0], 1, 3)
        for i in range(1, 5):
            self.__layout.addWidget(self.__players_w[i], i-1, 2)
            self.__layout.addWidget(self.__players_w[i+4],i-1, 1)

        self.__layout.addWidget(self.__players_w[9], 1, 0)
        self.__layout.addWidget(self.__players_w[10], 2, 0)

    def add_team_stats(self)->None:
        self.__team_name_view = QLabel(f"Name:\t{self.__team_name}")
        self.__team_name_view.setObjectName("team-name-view")
        self.__team_name_view.setStyleSheet("#team-name-view{border-bottom:1px solid black;}")

        self.__team_formations_view = QLabel(f"Formation:\t{self.__formation}")
        
        self.__bottom_layout.addWidget(self.__team_name_view)
        self.__bottom_layout.addWidget(self.__team_formations_view)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        painter.setPen(pen)
        
        brush = QColor(self.__color)
        painter.setBrush(brush)

        # Get the widget's width and height
        widget_width = self.width()
        widget_height = self.height()
        
        # Circle parameters
        circle_radius = 20
        circle_diameter = circle_radius * 2
        # Calculate the position to draw the circle at the bottom center
        x_position = (widget_width - circle_diameter) // 2
        y_position = (widget_height - circle_diameter - 5) 
        # Draw the circle
        painter.drawEllipse(x_position, y_position, circle_diameter, circle_diameter)
        

 
class MatchViewWidget(QWidget):
    def __init__(self, parent= None) -> None:
        super().__init__(parent)
        self.__teams = [TeamViewWidget('green', True, self), TeamViewWidget('red',False, self)]
        self.__layout = QHBoxLayout()

        self.init()

    def init(self)->None:
        self.__layout.addWidget(self.__teams[0])
        self.__layout.addWidget(self.__teams[1])
        self.setLayout(self.__layout)
        self.set_background()

    def set_background(self)->None:
        path = (__ASSETS_DIR__ / 'soccer_pitch_poles.png').resolve().as_posix()
        self.setObjectName("match-view")
    
        self.setStyleSheet("""
                           #match-view{
                            background-image:url(""" + path + """); 
                            background-repeat:no-repeat; 
                            background-position:center;
                            border:1px solid black;
                           }""")



if __name__ == "__main__":
    app = QApplication(sys.argv)

    player = MatchViewWidget()
    player.show()

    app.exec_()