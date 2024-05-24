import json
from cfg.paths_config import __TRACKING_DATA_DIR__
from pathlib import Path
import time

class Player:
    def __init__(self, id:int)->None:
        self.__player_id = id
        self.__is_activated = False
        self.__coordinates = None
        self.__raw_data = None
        self.__tracking_id = 0

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
    def __init__(self, team_id, player_ids:list)->None:
        self.__raw_data = None
        self.__players = [Player(id) for id in player_ids]
        self.__team_id = team_id


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
        self.__team_a = TeamManager(0, self.__teams_init.get('Team A'))
        self.__team_b = TeamManager(1, self.__teams_init.get('Team B'))

    
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