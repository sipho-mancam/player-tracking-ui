

class TeamController:
    def __init__(self) -> None:
        self.__team_model = None


class MatchController:
    def __init__(self)->None:
        self.__teams_controllers = [TeamController(), TeamController()]

