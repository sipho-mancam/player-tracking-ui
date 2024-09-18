from .palette import ColorPickerApp
from .model import ColorPaletteListener
from PyQt5.QtWidgets import QDialog, QApplication
import sys

class ColorPaletteController:
    def __init__(self)->None:
        self.__view = None
        self.__model = ColorPaletteListener("system-control")
        self.__model.register_listener(self.trigger_view)
        self._data_path = r"C:\ProgramData\Player Tracking Software\color_data.txt"

    def set_view(self, view)->None:
        self.__view  = view
    
    def trigger_view(self, colors)->None:
        self.__view.set_color_palette(colors) 

    def update_selected_color(self, selected_colors:dict)->None:
        with open(self._data_path, 'w') as fp:
            lines = []
            bg_color  = selected_colors.get('background_color')
            lines.append(f"{bg_color[0]} {bg_color[1]} {bg_color[2]}\n")
            bg_color  = selected_colors.get('team_a')
            lines.append(f"{bg_color[0]} {bg_color[1]} {bg_color[2]}\n")
            bg_color  = selected_colors.get('team_b')
            lines.append(f"{bg_color[0]} {bg_color[1]} {bg_color[2]}\n")
            fp.writelines(lines)
        # = ColorPickerApp(colors)  
        # if self.__view.exec() == QDialog.Accepted:
        #     print(self.__view.selected_colors)
        
        # self.__view = None

