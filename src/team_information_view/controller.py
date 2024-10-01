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
    def __init__(self, name, left=False, host="10.0.0.49" ) -> None:
        self.__team_model = TeamModel(left)
        self.__host = host
        self.__team_name = name
        self.__team_model.set_team_info(TeamModel.load_from_network(self.__team_name, self.__host))
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
    def __init__(self, host_address)->None:
        self.__host = host_address
        self.__match_model = MatchModel()
        self.__teams_controllers = [TeamController(self.__match_model.get_teams_list()[0], left=True, host=self.__host), 
                                    TeamController(self.__match_model.get_teams_list()[1], left=False, host=self.__host)]
            
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
    UNASSOCIATED = 0
    ASSOCIATED = 1
    CLICKED = 2
    ALERT = 3
    def __init__(self, match_controller:MatchController, tracking_model:TrackingDataModel)->None:
        self.state = []
        self.__match_controller = match_controller
        self.__tracking_model = tracking_model
        self.__associations_table = {} #  {id: player_object}
        self.__current_clicked = -1
        self.__default_color = (120, 120, 120)
        self.__frames_count = 0

    def get_frames_count(self)->int:
        return self.__frames_count

    def associate(self, player:dict, id:int)->None:
        # Check if the player wasn't assigned before.
        player['alert'] = False

        for key in self.__associations_table.keys():
            p_l = self.__associations_table[key]
            if (str(p_l.get('team'))+str(p_l.get('jersey_number'))) == str(player.get('team'))+str(player.get('jersey_number')):
                self.__associations_table.pop(key, -1)
                break;
            
        self.__associations_table[id] = player
        self.__current_clicked = -1

    def update_clicked(self, id:int)->None:
        self.__current_clicked = id

    def update_team_color(self, team_name, color)->None:
        for key in self.__associations_table.keys():
            player = self.__associations_table[key]
            if player.get('team') == team_name:
                player['color'] = color

    def generate_state(self)->list[dict]:
        # First we find all the associated players and update their coordinates
        '''
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
        if self.__tracking_model.is_data_ready():
            self.state = []
            tracking_data = self.__tracking_model.get_data()['tracks']
            # Associated Tracks and Players already found
            for track in tracking_data:
                id = track.get('tracking-id')
                if id in self.__associations_table:
                    player = self.__associations_table[id]
                    self.state.append(self.__create_state_object(player, track))
                else:
                    # Create objects for unassociated state
                    self.state.append(self.__create_default_state_object(track))

            for obj in self.state:
                id = obj.get('track_id')
                if id == self.__current_clicked:
                    obj['state'] = StateGenerator.CLICKED
                    break

        return self.state

    def __create_default_state_object(self, track:dict)->None:
        return {
                    'track_id':track.get('tracking-id'),
                    'coordinates': track.get('coordinates'),
                    'jersey_number':track.get('tracking-id'),
                    'team':'default',
                    'color':self.__default_color, 
                    'kit_color':track.get('kit_color'),
                    'state':StateGenerator.UNASSOCIATED,
                    'options':{
                        'alert':False,
                        'highlight':False,
                }}


    def __create_state_object(self, player:dict, track:dict)->None:
        if player.get('alert') is None or not player.get('alert'):
            player['alert'] = track.get('alert')

        return {
                    'track_id':track.get('tracking-id'),
                    'coordinates': track.get('coordinates'),
                    'jersey_number':player.get('jersey_number'),
                    'team':player.get('team'),
                    'color':player.get('color'), 
                    'kit_color':track.get('kit_color'),
                    'state': StateGenerator.ASSOCIATED,
                    'options':{
                        'alert': player.get('alert') if player.get('alert') else False,
                        'highlight':False
                }}

    

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
        self.__state_generator = None
        self.__state_object = []
        self.init()

    def init(self)->None:
        self.__timer.setInterval(20)
        self.__timer.timeout.connect(self.update_state)
        self.__timer.start()
       
    def set_match_controller(self, match_controller:MatchController)->None:
        self.__match_controller = match_controller
        self.__state_generator = StateGenerator(self.__match_controller, self.__tracking_model)

    def get_current_state(self)->dict:
        return self.__state_object
    
    def associate_player(self, player, id)->None:
        if self.__state_generator is not None:
            self.__state_generator.associate(player, id)    

    def update_state(self)->None:
        if self.__state_generator is not None:
            self.__state_object = self.__state_generator.generate_state()

    def update_click(self, id)->None:
        if self.__state_generator is not None:
            self.__state_generator.update_clicked(id)

    def update_team_color(self, team_name:str, color:str)->None:
        self.__state_generator.update_team_color(team_name, color)

    def stop(self)->None:
        self.__tracking_model.stop()
        self.__timer.stop()



