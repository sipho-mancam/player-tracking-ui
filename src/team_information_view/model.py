from pathlib import Path
import json

from cfg.paths_config import __TEAMS_DIR__


class FormationModel:
    def __init__(self, formation)->None:
        self.__name = formation.get('name')
        self.__positions = formation.get('positions')
        
        self.__transform_flip()

        # self.write_to_disk()

    def __transform_flip(self):
        for pos in self.__positions:
            x, y = pos.get('coordinates')
            if x <= 0.5:
                x  = 1 - x
            pos['r_coordinates'] = (x, y)

    def get_formation(self)->dict:
        return {
            'name':self.__name,
            'positions': self.__positions
        }
    
    def set_formation(self, formation)->None:
        self.__name = formation.get('name')
        self.__positions = formation.get('positions')
        self.__transform_flip()

    def write_to_disk(self)->None:
        path = (__TEAMS_DIR__ / (self.__name + ".json" )).resolve().as_posix()

        with open (path, 'w') as fp:
            json.dump({'name':self.__name, 'positions':self.__positions})
    
    def load_from_disk(self, name:str)->None:
        self.__name = name
        path = (__TEAMS_DIR__ / (self.__name + ".json" )).resolve().as_posix()

        with open(path, 'r') as fp:
            data = json.load(fp)
            self.__positions = data['positions']
            self.__name = data['name']

    def get_name(self)->str:
        return self.__name


class FormationsModel:
    def __init__(self)->None:
        self.__formations = []
        self.__formations_list = []

    def load_formations_list(self)->None:
        path = (__TEAMS_DIR__ / 'formations_list.json').resolve().as_posix()

        with open(path, 'r') as fp:
            data = json.load(fp)
            self.__formations_list = data['formations']

    def add_formation(self, formation:dict)->None:
        self.__formations.append(FormationModel(formation))
        self.__formations_list.append(formation.get('name'))
    


class PlayerInfoModel:
    def __init__(self, number, position)->None:
        self.__jersey_number = number
        self.__position = position
        self.__track_id = None
        self.__player_data = {}

    def setPlayerData(self, data:dict)->None:
        self.__player_data = data
        self.__position = self.__player_data['position']
        self.__jersey_number = self.__player_data['jersey_number']
    
    def get_player_data(self)->None:
        return self.__player_data
    

class TeamModel:
    def __init__(self) -> None:
        self.__team_data  = None
        
    def set_team_info(self, data)->None:
        self.__team_data = data

    def get_team_info(self)->dict:
        return self.__team_data


class MatchModel:
    def __init__(self)->None:
        pass


