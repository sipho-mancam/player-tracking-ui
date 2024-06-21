
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
        pass

class MatchModel:
    def __init__(self)->None:
        pass


