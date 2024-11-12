from pathlib import Path
import json
import os
from cfg.paths_config import __TEAMS_DIR__ , __KAFKA_CONFIG__
from .kafka import KConsumer, KProducer
from PyQt5.QtCore import QTimer
from typing import Callable


class FormationModel:
    def __init__(self, formation)->None:
        self.__name = formation.get('name')
        self.__positions = formation.get('positions')
        self.__formation_path = (__TEAMS_DIR__ / ('formations/'+ self.__name + ".json" )).resolve().as_posix()
        self.__transform_flip()
        # self.write_to_disk(

    @staticmethod
    def load_from_disk(name)->dict:
        __name = name
        path = (__TEAMS_DIR__ / ('formations/'+__name + ".json" )).resolve().as_posix()
        with open(path, 'r') as fp:
            data = json.load(fp)
            return data

    @staticmethod
    def formation_exists(name)->bool:
        path = (__TEAMS_DIR__ / ('formations/'+ name + ".json" )).resolve().as_posix()
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
        if os.path.exists(self.__list_path):
            self.load_formations_list()
            self.initialize_formation_models()
        else:
            with open(self.__list_path, 'w') as fp:
                return 

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
        self.__team_name = None
        self.__team_color = None
        self.__data_change_callbacks = set()

    @property
    def jersey_number(self)->float:
        return self.__jersey_number
    
    @property
    def track_id(self)->int:
        return self.__track_id
    
    @property
    def position(self)->str:
        return self.__position
    
    def triggerDataChanged(self)->None:
        for cb in self.__data_change_callbacks:
            cb(*(self.get_player_data(),))

    def set_coordinates(self, coordinates)->None:
        self.__coordinates = coordinates
        self.__player_data['coordinates'] = self.__coordinates
        self.triggerDataChanged()

    def set_tracker_id(self, id)->None:
        self.__track_id = id
        self.__player_data['track_id'] = self.__track_id
        self.triggerDataChanged()
    
    def set_jersey_number(self, number)->None:
        self.__jersey_number = number
        self.triggerDataChanged()
    
    def set_position(self, position)->None:
        self.__position = position
        self.triggerDataChanged()
    
    def set_player_data(self, data:dict)->None:
        self.__player_data = data
        self.__position = self.__player_data['position']
        self.__jersey_number = self.__player_data['jersey_number']
        self.__player_data['coordinates'] = self.__coordinates
        self.__player_data['track_id'] = self.__track_id
        self.triggerDataChanged()

    def get_player_data(self)->None:
        self.__player_data['position'] = self.__position
        self.__player_data['jersey_number'] = self.__jersey_number
        self.__player_data['coordinates'] = self.__coordinates
        self.__player_data['track_id'] = self.__track_id
        return self.__player_data
    
    def get_position(self)->str:
        return self.__position
    
    def registerDataChangeListener(self, func:Callable)->None:
        self.__data_change_callbacks.add(func)
    


class TeamModel:
    def __init__(self, fielding_team:bool) -> None:
        self.__team_data  = {}
        self.__name = None
        self.__starting_line_up = None
        self.__subs = None
        self.__players = []
        self.__fielding_team = fielding_team
        self.__is_init = False 
        self.__path = None
        self._dumped = False
        self.__playerDataChangedCallbacks = set()
        self.__team_data_changed_callbacks = set()

    def __str__(self)->str:
        return self.__name

    def is_team_init(self)->bool:
        return self.__is_init
    
    def is_fielding(self)->bool|None:
        return self.__fielding_team
    
    def get_name(self)->str|None:
        return self.__name
    
    def set_fielding(self)->None:
        self.__fielding_team = True
        self.__team_data['fielding'] = self.__fielding_team
        self.triggerTeamDataChanged()
    
    def clear_fielding(self)->None:
        self.__fielding_team = False
        self.__team_data['fielding'] = self.__fielding_team
        self.triggerTeamDataChanged()
    
    def registerPlayerDataChanged(self, func:Callable)->None:
        if not self._dumped:
            self.__playerDataChangedCallbacks.add(func)
        else:
            for player in self.__players:
                player.registerDataChangeListener(func)

    def registerTeamDataChanged(self, func:Callable)->None:
        self.__team_data_changed_callbacks.add(func)
    
    def triggerTeamDataChanged(self)->None:
        for cb in self.__team_data_changed_callbacks:
            cb(*(self.__team_data, ))
            
    def set_team_info(self, data)->None:
        self.__team_data = data
        self.__name = data['name']
        self.__starting_line_up = data['players']
        for player in self.__starting_line_up:
            player['color'] = data.get('color')
            player['team'] = self.__name
        
        self.__fielding_team = data.get('fielding')
        self.__subs = data['subs']
        self.update_players(self.__starting_line_up)
        self.init_team()
        self.triggerTeamDataChanged()


    def write_to_disk(self)->None:
        self.__path = (__TEAMS_DIR__ / ("teams/" + self.__name + '.json')).resolve().as_posix()
        with open(self.__path, 'w') as fp:
            json.dump(self.__team_data, fp)
   
    def update_players(self, player_info:list[dict])->None:
        for player in player_info:
            for p in self.__players:
                if p.jersey_number == player.get('jersey_number'):
                    p.set_player_data(player)
                    break

    def set_player_position(self, position, jersey_number:int)->None:
        for player in self.__players:
            if player.jersey_number == jersey_number:
                player.set_position(position)
    
    def set_player_id(self, id, jersey_number:int)->None:
        for player in self.__players:
            if player.jersey_number == jersey_number:
                player.set_tracker_id(id)

    def set_player_data(self, data, jersey_number:int)->None:
        for player in self.__players:
            if player.jersey_number == jersey_number:
                player.set_player_data(data)

    def get_player_data(self, jersey_number)->dict|None:
        for player in self.__players:
            if player.jersey_number == jersey_number:
                return player.get_player_data()
            
    def get_team_info(self)->dict:
        if len(self.__team_data) == 0:
            return None
        
        self.__team_data['players'] = []
        for j, player in enumerate(self.__players):
            self.__team_data['players'].insert(j, player.get_player_data())
        return self.__team_data

    def init_team(self)->None:
        self.__players = []
        for player in self.__starting_line_up:
            p = PlayerInfoModel(player.get('jersey_number'), player.get('position'))
            p.set_player_data(player)
            if not self._dumped:
                for cb in self.__playerDataChangedCallbacks:
                    p.registerDataChangeListener(cb)
            self.__players.append(p)

        self._dumped = True
        self.__is_init = True

    @staticmethod
    def load_from_disk(name:str)->dict:
        __path = (__TEAMS_DIR__ / ('teams/'+name + '.json')).resolve().as_posix()
        with open(__path, 'r') as fp:
            return json.load(fp)
    
    @staticmethod
    def team_exists(name)->bool:
        __path = (__TEAMS_DIR__ / ('teams/'+name + '.json')).resolve().as_posix()
        return os.path.exists(__path)
      

class MatchModel:
    def __init__(self)->None:
        self.__current_teams = []
        self.__teams = []
        self.__match_init = False
        self.__teams_data_structure = {}
        self.__fielding_team = None
        self.__batting_team = None
        self.init_teams()

    
    def match_data_init(self)->bool:
        return self.__match_init

    def init_teams(self)->None:
        if self.__match_init:
            # load teams from disk
            return
        
        self.__teams.append(TeamModel(True))# Add the Fielding Team
        self.__teams.append(TeamModel(False))# Add Bowling Team

    def swap_teams(self)->None:
        if self.__batting_team is None or self.__fielding_team is None:
            return
        temp = self.__batting_team
        self.__batting_team = self.__fielding_team
        self.__fielding_team = temp
        self.__teams_data_structure[self.__fielding_team].set_fielding()
        self.__teams_data_structure[self.__batting_team].clear_fielding()
        

    def registerTeamDataChangedListener(self, func:Callable)->None:
        for team in self.__teams:
            team.registerTeamDataChanged(func)
    
    def registerPlayerDataChanged(self, func:Callable)->None:
        for team in self.__teams:
            team.registerPlayerDataChanged(func)

    def initialize_team_info(self, team_info:dict)->None:
        fielding = team_info.get("fielding")
        if fielding:
            for team in self.__teams:
                if team.is_fielding():
                    team.set_team_info(team_info)
                    team.set_fielding()
                    self.__fielding_team = team.get_name()
                    self.__teams_data_structure[team.get_name()] = team
        else:              
            for team in self.__teams:
                if not team.is_fielding():
                    team.set_team_info(team_info)
                    team.clear_fielding()
                    self.__batting_team = team.get_name()
                    self.__teams_data_structure[team.get_name()] = team

        if len(self.__teams_data_structure) >= 2:
            self.__match_init = True
        
    def set_player_data(self, team_name:str, data:dict)->None:
        team = self.__teams_data_structure[team_name]
        team.set_player_data(data)

    def set_position(self, team_name:str, position:str, jersey_number:int)->None:
        team = self.__teams_data_structure[team_name]
        team.set_player_position(position, jersey_number)
    
    def set_player_tracker_id(self, team_name, track_id:int, jersey_number:int)->None:
        team = self.__teams_data_structure[team_name]
        team.set_player_id(track_id, jersey_number)

    def set_fielding_team(self, team_name)->None:
        team = self.__teams_data_structure[team_name]
        team.set_fielding()
        self.__fielding_team = team.get_name()

        for key in self.__teams_data_structure.keys():
            if key != team_name:
                team.clear_fielding()
                self.__batting_team = team.get_name()

    def set_team_info(self, team_name, team_info:dict)->None:
        if team_info.get('fielding'):
            self.__fielding_team = team_name
        else:
            self.__batting_team = team_name
        self.__teams_data_structure[team_name].set_team_info(team_info)

    def get_fielding_team_info(self)->dict:
        return self.__teams_data_structure[self.__fielding_team].get_team_info()
    
    def is_fielding_team_init(self)->bool:
        return self.__fielding_team is not None

    def get_bowling_team_info(self)->dict:
        return self.__teams_data_structure[self.__batting_team].get_team_info()
            
    def is_bowling_team_init(self)->bool:
        return self.__batting_team is not None

    def get_player_data(self, team_name, jersey_number)->dict|None:
        team = self.__teams_data_structure[team_name]
        return team.get_player_data(jersey_number)
    
    def get_team_info(self, team_name)->dict|None:
        team = self.__teams_data_structure[team_name]
        return team.get_team_info()

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
        self.__kafka_consumer = KConsumer(__KAFKA_CONFIG__)
        self.__kafka_producer = KProducer(__KAFKA_CONFIG__)
        self.__tracking_data_current_state = {}
        self.__timer = QTimer()

        self.init()

    def init(self)->None:
        self.__kafka_consumer.subscribe('ui-data')
        self.__kafka_consumer.start()

    def is_data_ready(self)->bool:
        return self.__kafka_consumer.is_data_ready()
    
    def get_data(self)->None:
        return self.__kafka_consumer.getTrackingData(True)

    def update(self)->None:
        if self.__kafka_consumer.is_data_ready():
            print(self.__kafka_consumer.getTrackingData())

    def stop(self)->None:
        self.__kafka_consumer.stop()
        # self.__timer.stop()

    def update_tracking_data(self, data:dict)->None:
        self.__tracking_data_current_state = data

    def publish_data(self)->None:
        # pprint(self.__tracking_data_current_state)
        self.__kafka_producer.send_message('tracking-data-0', json.dumps(self.__tracking_data_current_state))
