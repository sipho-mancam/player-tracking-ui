from .model import TeamModel
from .model import FormationsModel, MatchModel, TrackingDataModel

from PyQt5.QtCore import QTimer
from pprint import pprint

class FormationsController:
    def __init__(self)->None:
        self.__formations_view = None
        self.__model = FormationsModel()

    def get_formations_list(self)->list|None:
        return self.__model.get_formations_list()

    def get_formation_by_name(self, name)->dict|None:
        return self.__model.get_formation_by_name(name)
    
    def create_formation(self, formation:dict)->None:
        self.__model.add_formation(formation)

    

class TeamController:
    def __init__(self, left=False, name=None) -> None:
        self.__team_model = TeamModel(left)
        if name is not None and TeamModel.team_exists(name):
            self.__team_model.set_team_info(TeamModel.load_from_disk(name))
        self.__team_view = None

    def set_team_view(self, team_view)->None:
        self.__team_view = team_view

    def is_team_init(self)->bool:
        return self.__team_model.is_team_init()

    def set_team_info(self, data)->None:
        self.__team_model.set_team_info(data)
        self.__team_view.set_team_info(self.__team_model.get_team_info())
    
    def get_team_info(self)->dict|None:
        return self.__team_model.get_team_info()
    
    def update_side(self, left)->None:
        self.__team_model.update_side(left)

class MatchController:
    def __init__(self)->None:
        self.__match_model = MatchModel()
        if self.__match_model.teams_exist():
            self.__teams_controllers = [TeamController(True, self.__match_model.get_teams_list()[0]), 
                                        TeamController(False, self.__match_model.get_teams_list()[1])]
        else:
            self.__teams_controllers = [TeamController(True), 
                                        TeamController(False)]
            
        self.__left =  True
        self.__start_button = None
        self.__team_a_set = False
        self.__team_b_set = False
        self.__tracking_view = None
        self.__match_view_widget = None
        self.__instruction_table = {}
        self.__formations_controller = FormationsController()
        self.__instruction_table[0x00] = self.swap_teams
        self.__teams_init = self.is_match_init()


    # This method receives instructions from the ui and acts accordingly
    def upload_message(self, instruction, data=None)->None:
        if not self.__teams_init:
            return
        
        self.__instruction_table[instruction](data)
        if self.__tracking_view is not None:
            self.__tracking_view.update_match_info(self.get_match_info())
        
        if self.__match_view_widget is not None:
            self.__match_view_widget.update_match_info(self.get_match_info())

    def is_match_init(self)->bool:
        return self.__teams_controllers[0].is_team_init() and self.__teams_controllers[1].is_team_init()

    def get_formations_controller(self)->FormationsController:
       return self.__formations_controller

    def swap_teams(self, data):
        if self.__teams_init:
            controller = self.__teams_controllers[0]
            self.__teams_controllers[0] = self.__teams_controllers[1]
            self.__teams_controllers[1] = controller
            
            self.__teams_controllers[0].update_side(self.__left)
            self.__teams_controllers[1].update_side(not self.__left)

    def set_team(self, left_team:bool, data:dict)->None:
        if left_team:
            self.__teams_controllers[0].set_team_info(data)
            self.__team_a_set = True
        else:
            self.__teams_controllers[1].set_team_info(data)
            self.__team_b_set = True
        
        self.__match_model.add_team(data['name'])

        if (self.__team_a_set and self.__team_b_set) and (not self.__teams_init):
            self.__start_button.setEnabled(True)
            self.__teams_init = True
            self.__match_model.save_teams()

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


class StateGenerator:
    def __init__(self, match_controller, tracking_model)->None:
        self.state = []
        self.__match_controller = match_controller
        self.__tracking_model = tracking_model

    def generate(self)->list[dict]:
        pass

class DataAssociationsController:
    '''
    This class combines the Tracking Data coming in from the Tracking Core
    along with the player data that already exist from the UI side and presents a unified 
    data set both to the UI update and going out to Kafka.
    State Object is represented as follows:
    [{
        track_id:int,
        coordinates: tuple|list[x_norm, y_norm],
        jersey_number: int,
        team: str, #Name of the team
        color: (R:int, G:int, B:int),
        options:{
            alert: bool,
            highlight: bool,
            connect:{
                state: bool,
                neighbour:tuple|list[x_norm, y_norm],
                id: int - Object ID we are connecting to.
            }
        }
    }]
    '''
    def __init__(self)->None:
        self.__tracking_model = TrackingDataModel()
        self.__match_controller = None
        self.__timer = QTimer()
        self.__state_object = []

        self.init()

    def init(self)->None:
        self.__timer.setInterval(20)
        self.__timer.timeout.connect(self.update_state)
        self.__timer.start()
       
    def set_match_controller(self, match_controller:MatchController)->None:
        self.__match_controller = match_controller

    def get_current_state(self)->dict:
        return self.__state_object

    def update_state(self)->None:
        # This checks if we have new data that came in.
        # Updates that data and performs associations
        # update the current state object
        # sends it to the UI as well as Publish it for
        # other services to consume it.
        
        if self.__tracking_model.is_data_ready():
            self.__state_object = []
            tracking_data = self.__tracking_model.get_data()
            # print(type(tracking_data))
            if tracking_data is not None:
                for elem in tracking_data['tracks']:
                    self.__state_object.append({
                            "track_id":elem.get('tracking-id'),
                            "coordinates": elem.get('coordinates'),
                            "jersey_number": elem.get('tracking-id'),
                            "team": "untracked", #Name of the team
                            "color": tuple([0, 0, 255]),
                            "options":{
                                "alert": False,
                                "highlight": False,
                                "connect":{
                                    "state": False,
                                    "neighbour":None,
                                    "id": None
                                }
                            }
                        })

    def stop(self)->None:
        self.__tracking_model.stop()
        self.__timer.stop()



