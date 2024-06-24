from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import (QLabel, QLineEdit, QPushButton, QWidget, QApplication, 
                            QVBoxLayout, QGridLayout, QHBoxLayout, QSizePolicy, 
                            QSpacerItem, QComboBox, QColorDialog, QMessageBox, QDialog, QDialogButtonBox, QStyleOption, QStyle)
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
        if int(number)//10 ==0:
            number = f"0{number}"
        
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
        self.setLayout(layout)

        self.setObjectName("jersey-widget")
        self.setStyleSheet("""
                    #jersey-widget{
                        border:1px solid black;   

                    }
            """)
        
    def rerender(self)->None:
        del self.renderer
        self.renderer = QSvgRenderer(self.dom_document.toByteArray())
        # Render the SVG to a QPixmap and display it
        pixmap = QPixmap(80, 40)  # Specify the desired size
        pixmap.fill(Qt.transparent)  # Ensure the background is transparent
        painter = QPainter(pixmap)
        self.renderer.render(painter)
        painter.end()
        self.label.setPixmap(pixmap)
    
    def paintEvent(self, paint_event)->None:
        style_op = QStyleOption()
        style_op.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, style_op, painter, self)
        
        

class PlayerItem(QWidget):
    def __init__(self, position, jersey_number = 90, color='bule', parent=None)->None:
        super().__init__(parent)
        self.__layout = QVBoxLayout(self)
        self.__icon = QLabel()
        self.__text = QLabel()
        self.__position_widget = QLabel()
        self.__text_edit = QLineEdit()
        self.__color = color

        self.__player_name = jersey_number
        self.__jersey_number = jersey_number
        self.__player_position = position
        self.__updated = False
        self.setLayout(self.__layout)
        self.init()

    def get_player_info(self)->dict:
        return {'player-name':self.__player_name, 'jersey_number':self.__jersey_number, 'position':self.__player_position}
    
    def is_updated(self)->None:
        return self.__updated
    
    def set_team_color(self, color:str)->None:
        self.__color = color
        self.__icon.set_color(self.__color)
        self.__icon.rerender()
        

    def init(self)->None:
        self.__position_widget.setText(f"{self.__player_position}")
        self.__position_widget.setObjectName("player-position")
        self.__position_widget.setStyleSheet("#player-position{font-weight:500;color:green;}")
        self.__position_widget.setFixedSize(100,16)
        self.__position_widget.setAlignment(Qt.AlignHCenter)

        self.__icon = SvgManipulator(self.__jersey_number, self.__color)
        self.__icon.setFixedSize(100, 60)
        self.__icon.setStyleSheet("#player-jersey-icon{border:none; padding: 0px;}")
      
        self.__text.setText(f"{self.__player_name}")
        self.__text.setObjectName('player-name')
        self.__text.setStyleSheet("#player-name{font-weight:500;color:grey;}")
        self.__text.setFixedHeight(16)
        self.__text.setFixedWidth(100)
        self.__text.setAlignment(Qt.AlignHCenter)

        self.__text_edit.hide()
        self.__text_edit.setFixedHeight(16)
        self.__text_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.__text_edit.setFixedWidth(100)
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
            self.__jersey_number = text
            self.__icon.set_jersey_number(self.__player_name)
            self.__icon.rerender()
            self.__text.setText(self.__player_name)
            self.__text_edit.hide()
            self.__text_edit.setText("")
            self.__text.show()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        # On Click, we hide the text and show a text label to set the text
        self.__text.hide()
        self.__text_edit.show()
        self.__text_edit.setText(self.__player_name)
        self.__text_edit.setFocus()
        self.__updated = True
        return super().mousePressEvent(event)

class PlayerStatsDialog(QDialog):
    def __init__(self, player_stats:dict, parent=None)->None:
        super().__init__(parent)
        self.__layout = QVBoxLayout()
        self.__player_info  = player_stats
        self.setWindowTitle("Player Stats")

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
        self.setStyleSheet("""
                           #player-view{
                                font-weight:500; 
                                border:1px solid white;
                                border-radius:5;
                                background-color: rgba(255, 255, 255, 100);
                    }""")
        self.init()

    def get_position(self):
        return self.__position

    def set_position(self, position)->None:
        self.__position = position
        self.__position_w.setText(f"{self.__position}")
    
    def set_jersey_number(self, number)->None:
        self.__jersey_number = number
        self.__number_w.setText(f"{self.__jersey_number}")
        self.__icon_w.set_jersey_number(self.__jersey_number)
        self.__icon_w.rerender()
    
    def set_color(self, color:str)->None:
        self.__color = color
        self.__icon_w.set_color(self.__color)
        self.__icon_w.rerender()

    
    def init(self)->None:
        self.__position_w.setText(f"{self.__position}")
        self.__position_w.setFixedSize(100, 16)
        self.__position_w.setAlignment(Qt.AlignHCenter)
        self.__position_w.setObjectName("position-view")
        self.__position_w.setStyleSheet("#position-view{font-weight:500; color:black;}")

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
        self.__number_w.setStyleSheet("#jersey-view{font-weight:500; color:navy-blue;}")

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
    
    def paintEvent(self, paint_event)->None:
        style_op = QStyleOption()
        style_op.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, style_op, painter, self)

        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the frosted glass effect
        self.drawFrostedGlassEffect(painter)

    def drawFrostedGlassEffect(self, painter):
        # Draw a translucent white rectangle for the frosted effect
        rect = self.rect()
        frosted_color = QColor(255, 255, 255, 50)
        painter.fillRect(rect, frosted_color)

        # Draw another layer with a slight opacity to simulate blur (not a real blur)
        overlay_color = QColor(255, 255, 255, 20)
        painter.fillRect(rect, overlay_color)
       

class TeamLoadWidget(QWidget):
    def __init__(self, left_team=True, controller=None, parent=None)->None:
        super().__init__(parent)
        self.setWindowTitle("Load Team Information")
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
       
        self.__change_team_name = QPushButton("Change Name")

        self.__left_team = left_team
        self.__match_controller = controller
        self.__positions = ["GK", "LOB", "LCB", "RCB", "ROB", "LW", "CM", "DCM", "RW", "ACM", "CF"]

        self.__team_name = "Kaizer Chiefs"
        self.__team_formation = ""
        self.__team_color = ""
        self.__whats_missing = ""
        self.__data = {}

        if self.__match_controller:
            team  = self.__match_controller.get_team_data(self.__left_team)
            self.__team_list = [PlayerItem(player.get('position'), player.get('jersey_number'), team.get('color')) for i, player in enumerate(team['players'])]
            self.__subs_list = [PlayerItem(sub.get('position'), sub.get('jersey_number'), team.get('color')) for sub in team['subs']]
            self.__team_color = team.get('color')
            self.__team_formation = team.get('formation')
            self.__team_name = team.get('name')
            # self.__formations_dd.setCurrentText(self.__team_formation)
        else:
            self.__team_list = [PlayerItem(self.__positions[i]) for i in range(11)]
            self.__subs_list = [PlayerItem("SUB") for _ in range(5)]
        
        self.__formation_controller = None if self.__match_controller is None else self.__match_controller.get_formations_controller()

        self.setObjectName("team-show")
        self.setLayout(self.__main_layout)
        self.init()
        self.setFixedSize(self.sizeHint())

    def showEvent(self, show_event)->None:
        
        while self.__formations_dd.count() > 1:
            x = self.__formations_dd.count()
            for i in range(1, x, 1):
                self.__formations_dd.removeItem(i)
            
        if self.__formation_controller is not None:
            for i, form_name in enumerate(self.__formation_controller.get_formations_list()):  
                self.__formations_dd.insertItem(i+1, form_name)
        super().showEvent(show_event)

    def set_match_controller(self, controller)->None:
        self.__match_controller = controller
        self.__formation_controller = self.__match_controller.get_formations_controller()
        
   
    def init(self)->None:
        self.__team_name_text.setText(self.__team_name)
        self.__team_name_text.setFixedSize(500, 22)
        self.__team_name_text.setObjectName("team-name")
        self.__team_name_text.setStyleSheet("#team-name{font-weight:500;font-size:14px;border:1px solid #777; color:grey;}")
        self.__team_name_text.setAlignment(Qt.AlignLeft)
        self.__team_name_text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.__team_name_edit.setPlaceholderText('Team Name')
        self.__team_name_edit.setFixedSize(500, 22)
        self.__team_name_edit.setObjectName('team-name-edit')
        self.__team_name_edit.setStyleSheet("#team-name-edit{font-size:16px;}")
        self.__team_name_edit.setAlignment(Qt.AlignLeft)
        self.__team_name_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.__team_name_edit.hide()
        self.__team_name_edit.returnPressed.connect(self.change_team_name)

        self.__change_team_name.setFixedSize(100, 30)
        self.__change_team_name.clicked.connect(self.team_name_clicked)

        self.__formations_dd.addItem(self.__formations_default_text)
        self.__formations_dd.setFixedSize(200, 30)

        self.__team_name_layout.addWidget(self.__team_name_text)
        self.__team_name_layout.addWidget(self.__team_name_edit)
        self.__team_name_layout.addWidget(self.__change_team_name)
        self.__team_name_layout.addWidget(self.__formations_dd)
        self.__team_name_layout.setAlignment(Qt.AlignLeft)
        self.__team_name_layout.setContentsMargins(0,0,0,0)
     
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

        clear_to_save = self.__match_controller.is_match_init()

        if self.__formations_dd.currentText() == self.__formations_default_text and self.__match_controller.is_match_init():
            self.__formations_dd.setCurrentText(self.__team_formation)
        else:
            self.__team_formation = self.__formations_dd.currentText()

        if clear_to_save:
            # Collect the data into an object and save
            for idx, player in enumerate(self.__team_list):
                if 'players' not in self.__data:
                    self.__data['players'] = []
                if len(self.__data['players']) == 11: # It means we have all the players
                    self.__data['players'][idx] = player.get_player_info()
                else:
                    self.__data['players'].append(player.get_player_info())

            for idx, sub in enumerate(self.__subs_list):
                if 'subs' not in self.__data:
                    self.__data['subs'] = []
                if len(self.__data['subs']) == 5:
                    self.__data['subs'][idx] = sub.get_player_info()
                else:
                    self.__data['subs'].append(sub.get_player_info())

            self.__data['name'] = self.__team_name
            self.__data['color'] = self.__team_color
            self.__data['formation'] = self.__team_formation
            # Update the controller and send a signal 
            if self.__match_controller is not None:
                self.__match_controller.set_team(self.__left_team, self.__data) 
            self.hide()

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
            for player in self.__team_list:
               player.set_team_color(self.__team_color)
            
            for sub in self.__subs_list:
                sub.set_team_color(self.__team_color)
            

class TeamViewWidget(QWidget):
    def __init__(self, color, left = True, parent=None)->None:
        super().__init__(parent)
        self.__positions = ["GK", "LOB", "LCB", "RCB", "ROB", "LW", "CM", "DCM", "RW", "ACM", "CF"]
        self.__players = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        self.__color = color
        self.__formation = "4-4-2"
        self.__team_name = "Kaizer Chiefs"
        self.__left_team = left
        self.__team_color = color
       
        self.__players_w = [PlayerView(self.__positions[j], self.__players[j], color) for j in range(11)]
        self.__layout = QGridLayout()
        self.__bottom_layout = QVBoxLayout()
        self.__main_layout = QVBoxLayout()

        self.init()
        widgSize = self.sizeHint()
        widgSize.setHeight(widgSize.height()+60)
        self.setFixedSize(widgSize)

    def set_team_players(self, players:list[dict])->None:
        for i, player in enumerate(players):
            # print(player)
            self.__positions[i] = player['position']
            self.__players[i] = player['jersey_number']
        self.__update_players()

    def set_team_color(self, color:str)->None:
        self.__team_color = color 

    def set_team_name(self, team_name)->None:
        self.__team_name = team_name   

    def __update_players(self)->None:
        for player_widget in self.__players_w:
            position = player_widget.get_position()
            idx = self.__positions.index(position)
            player_widget.set_jersey_number(self.__players[idx])
            player_widget.set_color(self.__team_color)
    
    def set_team_info(self, team_info:dict)->None:
        self.__team_color = team_info['color']
        self.__team_name = team_info['name']
        self.__formation = team_info['formation']
        self.set_team_players(team_info['players'])
        self.__team_name_view.setText(f"Name:\t{self.__team_name}")
        self.__team_formations_view.setText(f"Formation:\t{self.__formation}")

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
        self.__team_name_view.setStyleSheet("#team-name-view{border-bottom:1px solid black; color:white; font-weight:500; font-size:16px;}")

        self.__team_formations_view = QLabel(f"Formation:\t{self.__formation}")
        self.__team_formations_view.setObjectName("team-formations-view")
        self.__team_formations_view.setStyleSheet("#team-formations-view{border-bottom:1px solid black; color:white; font-weight:500; font-size:16px;}")
        
        self.__bottom_layout.addWidget(self.__team_name_view)
        self.__bottom_layout.addWidget(self.__team_formations_view)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(Qt.white, 2, Qt.SolidLine)
        painter.setPen(pen)
        
        brush = QColor(self.__team_color)
        painter.setBrush(brush)

        # # Get the widget's width and height
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
        self.__teams = [TeamViewWidget('blue', True, self), TeamViewWidget('red',False, self)]
        self.__layout = QHBoxLayout()
        self.__match_controller = None
        self.init()

    def set_match_controller(self, controller)->None:
        self.__match_controller = controller
        if self.__match_controller is not None:
            self.__match_controller.set_team_view(True, self.__teams[0])
            self.__match_controller.set_team_view(False, self.__teams[1])
            self.__match_controller.set_match_view_widget(self)
            if self.__match_controller.is_match_init():
                self.update_match_info(self.__match_controller.get_match_info())

    def set_left_team(self, team_info:dict)->None:
        self.__teams[0].set_team_info(team_info)
    
    def set_right_team(self, team_info:dict)->None:
        self.__teams[1].set_team_info(team_info)
    
    def update_match_info(self, match_info:list)->None:
        self.__match_info = match_info
        self.__teams[0].set_team_info(self.__match_info[0])
        self.__teams[1].set_team_info(self.__match_info[1])
        
    def init(self)->None:
        self.__layout.addWidget(self.__teams[0])
        self.__layout.addWidget(self.__teams[1])
        self.setLayout(self.__layout)
        self.set_background()

    def set_background(self)->None:
        path = (__ASSETS_DIR__ / 'soccer_pitch_poles.png').resolve().as_posix()
        self.setObjectName("match-view")
        # Load and resize the background image
        self.background_image = QPixmap(path)
        self.background_image = self.background_image.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
        self.setStyleSheet("""
                           #match-view{
                            background-image:url(""" + path + """); 
                            background-repeat:no-repeat; 
                            background-position:center;
                            background-size:cover;
                            border:1px solid black;
                           }""")
        
    def resizeEvent(self, event):
        # Resize the background image when the widget is resized
        self.background_image = self.background_image.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.update()
        
    def paintEvent(self, paint_event)->None:
        style_op = QStyleOption()
        style_op.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, style_op, painter, self)

         # Draw the background image
        painter.drawPixmap(self.rect(), self.background_image)

class RoundButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(50, 50)
        self.__radius = int(self.width()/2)
        self.setObjectName("round-button")
        self.setStyleSheet(f"""
                            #round-button{{
                                border-style: outset;
                               
                                border-radius:25;
                                background-color: #ccc;
                            
                            }}
                           #round-button:pressed{{
                                background: #aaa; 
                           }}
        """)
        self.__is_activated = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_position = event.pos()

    def is_activated(self)->bool:
        return self.__is_activated
    
    def clear_activation(self):
        self.__is_activated = False

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToParent(event.pos() - self.drag_start_position))
            self.__is_activated = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            print(self.x(), self.y())

class FormationManagerView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Formations Manager")

        self.__main_layout = QVBoxLayout()
        self.__top_buttons_layout = QHBoxLayout()
        self.__middle_layout = QHBoxLayout()
        self.__position_widgets_grid = QGridLayout() 

        self.__create_formation_button = QPushButton("Create Formation")
        self.__modify_formation_button = QPushButton("Modify Formation")
        self.__save_button = QPushButton("Save")

        self.__formation_name = QLabel("Formation Name")
        self.__formation_name_edit = QLineEdit()
        self.__half_pitch = QLabel()

        self.__positions = ["GK", "LOB", "LCB", "RCB", "ROB", "LW", "CM", "DCM", "RW", "ACM", "CF"]
        self.__position_buttons = []
        self.__name = ""
        self.__data = {}
        self.__whats_missing = ""
        self.__formations_controller = None
        
        self.init()
        self.setFixedSize(self.sizeHint())

    def load_bg(self)->None:
        path = (__ASSETS_DIR__ / 'soccer_pitch_poles_half.png')
        pix_map = QPixmap(path.resolve().as_posix())
        pix_map = pix_map.scaled(600, 850)
        self.__half_pitch.setPixmap(pix_map)

    def set_controller(self, controller)->None:
        self.__formations_controller = controller

    def save_formation(self)->None:
        #Check if the formation name has been set
        # Check if all the players have been placed
        # Compute the normalized position for each player
        # save all of this in a dictionery
        # pass it to the controller and close.
        clear_to_save = True
        if len(self.__name) == 0:
            clear_to_save = False
            self.__whats_missing = "Please give the formation a name"

        if clear_to_save:
            for player in self.__position_buttons:
                if not player.is_activated():
                    clear_to_save = False
                    self.__whats_missing = "Please make sure all the positions are added to the formation"
                    break
        
        if clear_to_save:
            self.__data['name'] = self.__name
            self.__data['positions'] = []
            for position in self.__position_buttons:
                self.__data['positions'].append({'position':position.text(), 
                                                 'coordinates':self.__normalize_position(position.x(), position.y())})
                position.clear_activation()
            
            if self.__formations_controller is not None:
                self.__formations_controller.create_formation(self.__data)

            self.hide()
        else:
            # Open and Error Dialog
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setWindowTitle("Error")
            # msgBox.setTitle("Error")
            msgBox.setText(self.__whats_missing)
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_() 

    def __normalize_position(self, x, y)->tuple:
        width = self.__half_pitch.width()
        height = self.__half_pitch.height() 
        x_norm = (x/(width*2))
        y_norm=  (y/(height))
        return (x_norm, y_norm)

    def create_formation(self)->None:
        self.__formation_name.hide()
        self.__formation_name_edit.setText(self.__name)
        self.__formation_name_edit.show()

    def add_positions(self)->None:
        for idx, pos in enumerate(self.__positions):
            row, col  = divmod(idx, 3)
            btn = RoundButton(pos)
            self.__position_buttons.append(btn)
            self.__position_widgets_grid.addWidget(btn, row, col)
        self.__position_widgets_grid.setAlignment(Qt.AlignTop)

    def update_formation_name(self)->None:
        text = self.__formation_name_edit.text()
        if not text.isspace() and len(text) > 0:
            self.__name = text
            self.__formation_name_edit.hide()
            self.__formation_name.setText(f"{self.__name}")
            self.__formation_name.show()

    def init(self)->None:
        self.__create_formation_button.setFixedSize(100, 24)
        self.__create_formation_button.clicked.connect(self.create_formation)

        self.__modify_formation_button.setFixedSize(100, 24)
        self.__modify_formation_button.setDisabled(True)

        self.__save_button.setFixedSize(100, 24)
        self.__save_button.clicked.connect(self.save_formation)

        self.__formation_name.setFixedSize(300, 24)
        self.__formation_name.setObjectName("formation-name")
        self.__formation_name.setStyleSheet("""#formation-name{
                                            border:1px solid black;
                                            font-size:14px;
                                            font-weight:500;                                        
                                            }""")
        self.__formation_name.setAlignment(Qt.AlignHCenter)

        self.__formation_name_edit.setPlaceholderText("Formation eg. 4-4-2")
        self.__formation_name_edit.setFixedSize(300, 24)
        self.__formation_name_edit.setAlignment(Qt.AlignCenter)
        self.__formation_name_edit.hide()
        self.__formation_name_edit.returnPressed.connect(self.update_formation_name)

        self.__top_buttons_layout.addWidget(self.__create_formation_button)
        self.__top_buttons_layout.addWidget(self.__modify_formation_button)
        self.__top_buttons_layout.addWidget(self.__formation_name)
        self.__top_buttons_layout.addWidget(self.__formation_name_edit)
        self.__top_buttons_layout.addWidget(self.__save_button, alignment=Qt.AlignLeft)
        self.__top_buttons_layout.setAlignment(Qt.AlignLeft)

        self.load_bg()
        self.add_positions()

        self.__middle_layout.addWidget(self.__half_pitch)
        self.__middle_layout.addLayout(self.__position_widgets_grid)

        self.__main_layout.addLayout(self.__top_buttons_layout)
        self.__main_layout.addLayout(self.__middle_layout)
        self.__main_layout.setAlignment(Qt.AlignTop)

        self.setLayout(self.__main_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    player = FormationManagerView()
    player.show()

    app.exec_()