from pathlib import Path
import json
import os
from cfg.paths_config import __TEAMS_DIR__


class FormationModel:
    def __init__(self, formation)->None:
        self.__name = formation.get('name')
        self.__positions = formation.get('positions')
        self.__formation_path = (__TEAMS_DIR__ / (self.__name + ".json" )).resolve().as_posix()
        self.__transform_flip()
        # self.write_to_disk(

    @staticmethod
    def load_from_disk(name)->dict:
        __name = name
        path = (__TEAMS_DIR__ / (__name + ".json" )).resolve().as_posix()
        with open(path, 'r') as fp:
            data = json.load(fp)
            return data

    @staticmethod
    def formation_exists(name)->bool:
        path = (__TEAMS_DIR__ / (name + ".json" )).resolve().as_posix()
        return os.path.exists(path)

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
    
    def find_player_position(self, position)->dict|None:
        for pos in self.__positions:
            p_ = pos['position']
            if p_ == position:
                return pos
        return None

    def set_formation(self, formation)->None:
        self.__name = formation.get('name')
        self.__positions = formation.get('positions')
        self.__transform_flip()

    def write_to_disk(self)->None:
        with open (self.__formation_path, 'w') as fp:
            json.dump({'name':self.__name, 'positions':self.__positions}, fp)

    def get_name(self)->str:
        return self.__name


class FormationsModel:
    def __init__(self)->None:
        self.__formations = []
        self.__formations_list = []
        self.__list_path = (__TEAMS_DIR__ / 'formations_list.json').resolve().as_posix()

        self.init()

    def init(self)->None:
        self.load_formations_list()
        self.initialize_formation_models()

    def load_formations_list(self)->None:
        with open(self.__list_path, 'r') as fp:
            data = json.load(fp)
            self.__formations_list = data['formations']

    def get_formations_list(self)->list:
        return self.__formations_list

    def initialize_formation_models(self)->None:
        for form_name in self.__formations_list:
            if FormationModel.formation_exists(form_name):
                self.__formations.append(FormationModel(FormationModel.load_from_disk(form_name)))

    def get_formation_by_name(self, name:str)->dict:
        for formation in self.__formations:
            if formation.get_name() == name:
                return formation.get_formation()
        return None

    def add_formation(self, formation:dict)->None:
        f_model = FormationModel(formation)
        f_model.write_to_disk()
        self.__formations.append(f_model)
        self.__formations_list.append(formation.get('name'))
        self.__update_list_file()

    def __update_list_file(self)->None:
        with open(self.__list_path, 'w') as fp:
            json.dump({'formations':self.__formations_list}, fp)

class PlayerInfoModel:
    def __init__(self, number, position)->None:
        self.__jersey_number = number
        self.__position = position # This refers to the players position from the formation (GK LOB etc.)
        self.__track_id = -1
        self.__player_data = {}
        self.__coordinates = (0, 0)

    def set_coordinates(self, coordinates)->None:
        self.__coordinates = coordinates
        self.__player_data['coordinates'] = self.__coordinates

    def set_tracker_id(self, id)->None:
        self.__track_id = id
        self.__player_data['track_id'] = self.__track_id

    def setPlayerData(self, data:dict)->None:
        self.__player_data = data
        self.__position = self.__player_data['position']
        self.__jersey_number = self.__player_data['jersey_number']
        self.__player_data['coordinates'] = self.__coordinates
        self.__player_data['track_id'] = self.__track_id

    def get_player_data(self)->None:
        self.__player_data['position'] = self.__position
        self.__player_data['jersey_number'] = self.__jersey_number
        self.__player_data['coordinates'] = self.__coordinates
        self.__player_data['track_id'] = self.__track_id
        return self.__player_data
    
    def get_position(self)->str:
        return self.__position


class TeamModel:
    def __init__(self, left) -> None:
        self.__team_data  = None
        self.__name = None
        self.__formation = None
        self.__formation_name = None
        self.__starting_line_up = None
        self.__subs = None
        self.__players = []
        self.__left = left
        self.__is_init = False 
        self.__path = None

    def is_team_init(self)->bool:
        return self.__is_init
    
    def update_side(self, left)->None:
        self.__left = left
        for player in self.__players:
            pos = player.get_position()
            coord = self.__formation.find_player_position(pos)
            if left:
                player.set_coordinates(coord.get('coordinates'))
            else:
                player.set_coordinates(coord.get('r_coordinates'))
            

    def set_team_info(self, data)->None:
        self.__team_data = data
        self.__name = data['name']
        self.__formation_name = data['formation']
        self.__formation = FormationModel(FormationModel.load_from_disk(self.__formation_name))
        self.__starting_line_up = data['players']
        self.__subs = data['subs']
        
        if self.__is_init:
            self.write_to_disk()

        self.init_team()

    def write_to_disk(self)->None:
        self.__path = (__TEAMS_DIR__ / (self.__name + '.json')).resolve().as_posix()
        with open(self.__path, 'w') as fp:
            json.dump(self.__team_data, fp)

    @staticmethod
    def load_from_disk(name:str)->dict:
        __path = (__TEAMS_DIR__ / (name + '.json')).resolve().as_posix()
        with open(__path, 'r') as fp:
            return json.load(fp)
    
    @staticmethod
    def team_exists(name)->bool:
        __path = (__TEAMS_DIR__ / (name + '.json')).resolve().as_posix()
        return os.path.exists(__path)
    
    def update_players(self, player_info:list[dict])->None:
        pass

    def get_team_info(self)->dict:
        self.__team_data['players'] = []
        for j, player in enumerate(self.__players):
            self.__team_data['players'].insert(j, player.get_player_data())
        return self.__team_data

    def init_team(self)->None:
        if self.__is_init:
            return 
        for player in self.__starting_line_up:
            p = PlayerInfoModel(player.get('jersey_number'), player.get('position'))
            coord = self.__formation.find_player_position(player.get('position'))
            if self.__left:
                p.set_coordinates(coord.get('coordinates'))
            else:
                p.set_coordinates(coord.get('r_coordinates'))

            self.__players.append(p)
        self.__is_init = True
        if not TeamModel.team_exists(self.__name):
            self.write_to_disk()



class MatchModel:
    def __init__(self)->None:
        self.__current_teams = []
        self.__path = (__TEAMS_DIR__ / 'current_teams.json').resolve().as_posix()

        if self.teams_exist():
            self.load_teams_list()

    def load_teams_list(self)->None:
        with open(self.__path, 'r') as fp:
            self.__current_teams = json.load(fp)['teams']

    def get_teams_list(self)->list:
        return self.__current_teams
    
    def add_team(self, name)->None:
        self.__current_teams.insert(0, name)
    
    def save_teams(self)->None:
        self.write_teams()

    def write_teams(self)->None:
        with open(self.__path, 'w') as fp:
            json.dump({'teams':self.__current_teams[:2]}, fp)

    
    @staticmethod
    def teams_exist()->bool:
        __path = (__TEAMS_DIR__ / 'current_teams.json').resolve().as_posix()
        return os.path.exists(__path)


class TrackingDataModel:
    def __init__(self)->None:
        pass