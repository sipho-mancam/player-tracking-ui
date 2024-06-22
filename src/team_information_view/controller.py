from .model import TeamModel

class TeamController:
    def __init__(self) -> None:
        self.__team_model = TeamModel()
        self.__team_view = None

    def set_team_view(self, team_view)->None:
        self.__team_view = team_view

    def set_team_info(self, data)->None:
        self.__team_model.set_team_info(data)
        self.__team_view.set_team_info(self.__team_model.get_team_info())
    
    def get_team_info(self)->dict|None:
        return self.__team_model.get_team_info()

class MatchController:
    def __init__(self)->None:
        self.__teams_controllers = [TeamController(), TeamController()]

    def set_team(self, left_team:bool, data:dict)->None:
        if left_team:
            self.__teams_controllers[0].set_team_info(data)
        else:
            self.__teams_controllers[1].set_team_info(data)
    
    def set_team_view(self, left_team:bool, view)->None:
        if left_team:
            self.__teams_controllers[0].set_team_view(view)
        else:
            self.__teams_controllers[1].set_team_view(view)

    def get_team_data(self, left)->dict:
        if left:
            return self.__teams_controllers[0].get_team_info()
        else:
            return self.__teams_controllers[1].get_team_info()


