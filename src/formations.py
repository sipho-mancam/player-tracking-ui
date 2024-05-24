from cfg.paths_config import __TEAMS_DIR__
import math
from pathlib import Path
import json
from PyQt5.QtCore import Qt

class FormationsManager:
    def __init__(self)->None:
        self.__formations_list = []
        self.__creating_formation = False
        self.__current_formation = {}
        self.__is_formation_complete = False
        self.__formations_selected =  False #{'A':False, 'B':False}
        self.width = 1140
        self.height = 636
        self.x_offset = 70
        self.y_offset = 35
        self.load_formations()

    def create_formation(self, name:str)->None:
        self.__current_formation['name'] = name
        self.__current_formation['players'] = []
        self.__creating_formation = True

    def normalize_coordinates(self):
        self.__current_formation['normalized'] = []
        for point in self.__current_formation['players']:
            x, y = point
            c_x , c_y = x-self.x_offset, y-self.y_offset
            n_x, n_y = c_x/self.width, c_y/self.height
            self.__current_formation['normalized'].append((n_x, n_y))
        
    def select_formation(self, name)->None:
        with open((__TEAMS_DIR__ / Path(name)).resolve().as_posix() + str('.json'), 'r') as fp:
            data = json.load( fp)
            self.__current_formation =  data

    def get_formations(self)->list[str]:
        return self.__formations_list

    def is_formation_selected(self)->bool:
        return self.__formations_selected
    
    def eucliden_distance(self, point1:tuple, point2:tuple)->float:
        return math.sqrt(((point1[0]-point2[0])**2) + ((point1[1] - point2[1])**2))

    def __remove(self, player)->tuple[bool, int]:
        for idx, c_player in enumerate(self.__current_formation['players']):
            if self.eucliden_distance(c_player, player) < 10:
                return (True, idx)
        else:
            return (False, -1)
    
    def add_player_to_formation(self, x, y)->None:
        if self.__creating_formation:
            check, idx = self.__remove((x, y))
            if check:
                self.__current_formation['players'].pop(idx)
                return

            if len(self.__current_formation['players']) < 11:
                self.__current_formation['players'].append((x, y))
                self.__is_formation_complete = not len(self.__current_formation['players']) < 11
            else:
                self.__is_formation_complete = True

    def load_formations(self)->None:
        # This loads the formations list.
        with open((__TEAMS_DIR__ / Path('formations-list')).resolve().as_posix() + str('.json'), 'r') as fp:
            data = json.load(fp)
            self.__formations_list = data['formations']

        

    def save_formation(self):
        self.__formations_list.append(self.__current_formation['name'])
        self.__creating_formation = False
        self.normalize_coordinates()
        self.transform_flip()# add the other side on the formation
        with open((__TEAMS_DIR__ / Path(self.__current_formation['name'])).resolve().as_posix() + str('.json'), 'w') as fp:
            json.dump(self.__current_formation, fp)

        with open((__TEAMS_DIR__ / Path('formations-list')).resolve().as_posix() + str('.json'), 'w') as fp:
            json.dump({'formations':self.__formations_list}, fp)

    def transform_flip(self):
        normalized = self.__current_formation.get('normalized')
        transformed = []
        if normalized is not None:
            for pos in normalized:
                x, y = pos
                if x <= 0.5:
                    x  = 1 - x
                transformed.append((x, y))
        self.__current_formation['normalized_right'] = transformed
    
  

    def handle_mouse_click(self, event)->None:
        if event.button() == Qt.LeftButton:
            x = event.x()
            y = event.y()
           
            if self.__creating_formation:
                self.add_player_to_formation(x, y)

    def is_players_11(self)->bool:
        return self.__is_formation_complete
    
    def is_creating_formations(self)->bool:
        return self.__creating_formation
    
    def get_players_list(self)->list:
        return self.__current_formation['players']
    
                