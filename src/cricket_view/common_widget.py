
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QGridLayout, QVBoxLayout, QHBoxLayout, QDialog)
from PyQt5.QtGui import QImage, QPixmap, QColor, QPaintEvent, QPen, QBrush, QPainter
from PyQt5.QtCore import Qt, QTimer


    
class ButtonWithID(QPushButton):
    def __init__(self, button_text,  id:dict, parent=None)->None:
        super().__init__(button_text, parent)
        self.__button_text = button_text
        self.__id = id
        self.__button_click_callback = None
        self.__assigned_id = None
        self.setFixedSize(100, 40)  # Set fixed size to make it circular
        self.setStyleSheet("""
                    QPushButton {
                        border: 0px solid #555;
                        border-radius: 20px;
                        border-style: outset;
                        background: #ddd;
                        padding: 10px;
                        font-weight:500;
                        font-size:14px;
                        text-align:left;
                        margin-left:20;
                        
                    }
                    QPushButton:pressed {
                        background: #aaa;
                    }
                """)
        
    def set_color(self, color:str)->None:
        self.__id['color'] = color

    def registerCallback(self, bt_callback)->None:
        self.__button_click_callback = bt_callback
    
    def button_clicked(self)->None:
        player = self.__id.get('player')
        clr = QColor(self.__id.get('color'))
        clr = (clr.red(), clr.green(), clr.blue())
        player['color'] = clr
        player['team'] = self.__id.get('team')
        ret_data = self.__button_click_callback(*(player,))

        if self.__assigned_id is None:
            self.__assigned_id = ret_data

        if ret_data is not None:
            self.set_button_assigned(ret_data)
            self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.button_clicked()
        return super().mousePressEvent(e)

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
        self.setText(f"{self.__id['position']}")

    def set_button_assigned(self, id)->None:
        self.__assigned_id = id

    def clear_id(self, id)->None:
        if id == self.__assigned_id:
            self.__assigned_id = None
            self.update()
    
    def draw_id(self)->None:
        if self.__assigned_id is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(0, 0, 255), 2, Qt.SolidLine)
            pen.setWidth(1)
            brush = QBrush(QColor(0, 0, 255))
            painter.setPen(pen)
            painter.setBrush(brush)

            c_width = 0.05
            rect = self.rect()
            w , m_h = rect.width() , rect.height()
            x = rect.x()
            x , w = round(x+(w*(1-0-0))), round(w*c_width)
            d_1, y = m_h - w, rect.y()
            y += d_1//2
            rect.setX(x) 
            rect.setY(y)
            rect.setWidth(w)
            rect.setHeight(w)
            painter.drawEllipse(rect)
            p = QPen(QColor(255, 255, 255), 3)
            painter.setPen(p)
            painter.drawText(rect, Qt.AlignCenter, str(self.__assigned_id))

    def draw_jersey(self)->None:
        id = self.__id.get('jersey_number') 
        if id is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(0, 0, 0), 2, Qt.SolidLine)
            pen.setWidth(1)
            brush = QBrush(QColor(0, 0, 0))
            painter.setPen(pen)
            painter.setBrush(brush)

            c_width = 0.2
            rect = self.rect()
            w , m_h = rect.width() , rect.height()
            x = rect.x()
            x , w = round(x+(w*(1-c_width-0.15))), round(w*c_width)
            d_1, y = m_h - w, rect.y()
            y += d_1//2
            rect.setX(x) 
            rect.setY(y)
            rect.setWidth(w)
            rect.setHeight(w)
            painter.drawEllipse(rect)
            p = QPen(QColor(255, 255, 255), 3)
            painter.setPen(p)
            painter.drawText(rect, Qt.AlignCenter, str(id))

    def paintEvent(self, event:QPaintEvent)->None:
        super().paintEvent(event)
        self.draw_id()
        self.draw_jersey()

    def update_player_info(self, player_info:dict)->None:
        self.__id = player_info
    

class StyledButton(QPushButton):
    def __init__(self, text='', parent=None)->None:
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedWidth(120)
        self.setStyleSheet(self.default_style())
        self._state = False # Pressed or cleared

    def default_style(self):
        return """
            QPushButton {
                border-radius:14px;
                border-style: outset;
                background: #f00;
                padding: 5px;
                color: #eee;
                font-size:16px;
            }
            QPushButton:pressed {
                background: #aaa;
            }
        """
    
    def toggled_style(self):
        return """
            QPushButton {
                border-radius:14px;
                border-style: outset;
                background: #7fc97f;
                padding: 5px;
                color: #fff;
                font-size:16px;
            }
            QPushButton:pressed {
                background: #679267;
            }
        """
    
    def toggle_color(self):
        # if self.isChecked():
        self.setStyleSheet(self.toggled_style())
        self._state = True
        # else:
        #     self.setStyleSheet(self.default_style())
    
    def clear_toggle(self)->None:
        self.setStyleSheet(self.default_style())
        self._state = False

    def get_state(self)->bool:
        return self._state