from .model import TeamModel
from .model import FormationsModel

class FormationsController:
    def __init__(self)->None:
        self.__formations_view = None
        self.__model = FormationsModel()

    

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
        self.__start_button = None
        self.__team_a_set = False
        self.__team_b_set = False
        self.__tracking_view = None
        self.__match_view_widget = None
        self.__instruction_table = {}

        self.__instruction_table[0x00] = self.swap_teams
    # This method receives instructions from the ui and acts accordingly
    def upload_message(self, instruction, data=None)->None:
        self.__instruction_table[instruction](data)

        if self.__tracking_view is not None:
            self.__tracking_view.update_match_info(self.get_match_info())
        
        if self.__match_view_widget is not None:
            self.__match_view_widget.update_match_info(self.get_match_info())
    
    def swap_teams(self, data):
        controller = self.__teams_controllers[0]
        self.__teams_controllers[0] = self.__teams_controllers[1]
        self.__teams_controllers[1] = controller


    def set_team(self, left_team:bool, data:dict)->None:
        if left_team:
            self.__teams_controllers[0].set_team_info(data)
            self.__team_a_set = True
        else:
            self.__teams_controllers[1].set_team_info(data)
            self.__team_b_set = True

        if self.__team_a_set and self.__team_b_set:
            self.__start_button.setEnabled(True)

        if self.__tracking_view is not None:
            self.__tracking_view.update_match_info(self.get_match_info())
    
    def set_team_view(self, left_team:bool, view)->None:
        if left_team:
            self.__teams_controllers[0].set_team_view(view)
        else:
            self.__teams_controllers[1].set_team_view(view)
        
    def set_player_tracking_interface(self, player_tracking)->None:
        self.__tracking_view = player_tracking
    
    def set_match_view_widget(self, widget)->None:
        self.__match_view_widget = widget

    def get_match_info(self)->list:
        match_info = [self.__teams_controllers[0].get_team_info(), self.__teams_controllers[1].get_team_info()]
        return match_info

    def get_team_data(self, left)->dict:
        if left:
            return self.__teams_controllers[0].get_team_info()
        else:
            return self.__teams_controllers[1].get_team_info()
        
    def set_start_button(self, start_button)->None:
        self.__start_button = start_button


