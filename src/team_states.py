import json
from cfg.paths_config import __TRACKING_DATA_DIR__
from pathlib import Path
import time
from formations import FormationsManager

class Player:
    def __init__(self, id:int)->None:
        self.__player_id = id
        self.__is_activated = False
        self.__coordinates = None
        self.__raw_data = None
        self.__tracking_id = 0

    def is_init(self)->bool:
        return not (self.__coordinates is None)

    def update_coordinates(self, tracking_data:dict)->None:
        self.__raw_data = tracking_data
        self.__coordinates = self.__raw_data.get('coordinates')
        self.__is_activated = True

    def is_activated(self)->bool:
        return self.__is_activated

    def is_equal(self, player_id:int)->bool:
        return self.__player_id == player_id
    
    def get_tracking_data(self)->dict:
        return self.__raw_data


class TeamManager:
    def __init__(self, team_id, player_ids:list, side=0)->None:
        self.__raw_data = None
        self.__players = [Player(id) for id in player_ids]
        self.__team_id = team_id
        self.__formation_manager = FormationsManager()
        self.__side = side
        self.__init_saved = False
        self.__is_associated = False

    def perform_associations(self, tracks:list[dict])->None:
        print("Performing Associations ...")
        
        self.__is_associated = True

    def is_associations_init(self)->bool:
        return self.__is_associated

    def get_id(self)->int:
        return self.__team_id

    def get_side(self)->int:
        return self.__side

    def is_init(self)->bool:
        return (self.__init_saved and self.__check_init())

    def save_formation(self)->None:
        self.__init_saved = True

    def players_done(self)->bool:
        return self.__check_init()
    
    def __check_init(self)->bool:
        is_init = True
        for player in self.__players:
            if not player.is_init():
                is_init = False
                return is_init
        return is_init
    
    
    def init(self, formation_name, create:bool)->None:
        """
        1. This call should block until all team specific settings are implemented.
        Init Sequence:
            a. Load Formations.
        """
        if create:
            self.__formation_manager.create_formation(formation_name)
            self.__formation_manager.get_formation() # get the currently selected formation.
    
    def get_formations_manager(self)->FormationsManager:
        return self.__formation_manager

    def select_formation(self, formation_name:str)->None:
        # Select formations from formations manager and load it in.
        self.__formation_manager.select_formation(formation_name)



    def update_players(self, tracking_data:list[dict])->None:
        for player in self.__players:
            for det in tracking_data:
                if det.get('player-id') is not None and player.is_equal(det.get('player-id')):
                    player.update_coordinates(det)
                    break
    
    def get_team_data(self)->list[dict]:
        res_list = []
        for player in self.__players:
            if player.is_activated():
                res_list.append(player.get_tracking_data())
        return res_list
    

class TeamsManager:
    def __init__(self, teams_init:list[dict])->None:
        self.__teams_init = teams_init
        self.__team_a = TeamManager(0, self.__teams_init.get('Team A'), 0)
        self.__team_b = TeamManager(1, self.__teams_init.get('Team B'), 1) # right
        self.__teams_init = False
    
   
    # This checks if we have initialized the initial state with formations
    def is_init(self)->bool:
        return (self.__team_a.is_init() and self.__team_b.is_init())
    
    def get_current_team_initializing(self)->TeamManager:
        if not self.__team_a.is_init():
            return self.__team_a
        
        return self.__team_b
    
    def is_associations_init(self)->bool:
        return (self.__team_a.is_associations_init() and self.__team_b.is_associations_init())

    def perform_associations(self, tracks:list)->None:
        self.__team_a.perform_associations(tracks)
        self.__team_b.perform_associations(tracks)
    
    def update_team(self, tracking_data:list[dict])->None:
        self.__team_a.update_players(tracking_data)
        self.__team_b.update_players(tracking_data)

    def get_tracking_data(self)->list[dict]:
        res = self.__team_a.get_team_data()
        res.extend(self.__team_b.get_team_data())
        return res
    
    def write_to_file(self)->None:
        data = self.get_tracking_data()
        if len(data) > 0:
            with open((__TRACKING_DATA_DIR__ / Path(f'tracking_data_{time.time()}.json')), 'w') as fp:
                json.dump({'tracks':data}, fp)