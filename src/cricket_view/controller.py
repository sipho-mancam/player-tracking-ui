
from .model import TrackingDataModel
from PyQt5.QtCore import QTimer
from pprint import pprint


class StateGenerator:
    UNASSOCIATED = 0
    ASSOCIATED = 1
    CLICKED = 2
    ALERT = 3
    STATE_SET = 1
    STATE_CLEAR = 0
    MODE_HIGHLIGHT = 0
    MODE_HIDE = 1
    def __init__(self, tracking_model:TrackingDataModel)->None:
        self.state = []
        self.__tracking_model = tracking_model
        self.__associations_table = {} #  {id: player_object}
        self.__current_clicked = -1
        self.__default_color = (120, 120, 49)
        self.__frames_count = 0
        self.__multi_view = False
        self.__is_distance = False
        self.__distance_object = {}

    def set_multi_view(self, m_view)->None:
        self.__multi_view = m_view

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

    def is_distance_object_available(self)->bool:
        return self.__is_distance

    def get_distance_object(self)->dict:
        return self.__distance_object.copy()

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
            mode: int[HIGHTLIGHT, HIDE]
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
            tracking_data_raw = self.__tracking_model.get_data()
            tracking_data = tracking_data_raw['tracks']

            if 'distance_object' in tracking_data_raw:
                self.__is_distance = True
                self.__distance_object = tracking_data_raw['distance_object']
                # print(self.__distance_object)
            else:
                self.__is_distance = False
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
            tracking_data_raw['tracks'] = self.state
            tracking_data_raw['multi_view'] =  self.__multi_view
            self.__tracking_model.update_tracking_data(tracking_data_raw)
            self.__tracking_model.publish_data()
        return self.state

    def __create_default_state_object(self, track:dict)->None:
        return {
                    'track_id':track.get('tracking-id'),
                    'coordinates': track.get('coordinates'),
                    'jersey_number':-1,#track.get('tracking-id'),
                    'team':'default',
                    'color':self.__default_color, 
                    'kit_color':track.get('kit_color'),
                    'state':StateGenerator.UNASSOCIATED,
                    'mode': track.get('mod'),
                    'mode_state': track.get('state_object'),
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
                    'mode': track.get('mod'),
                    'mode_state': track.get('state_object'),
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
        self.__timer = QTimer()
        self.__state_generator = None
        self.__state_object = []
        self.__multi_view = False
        self.init()

    def init(self)->None:
        self.__state_generator = StateGenerator(self.__tracking_model)
        self.__state_generator.set_multi_view(self.__multi_view)
        pass
        # self.__timer.setInterval(20)
        # self.__timer.timeout.connect(self.update_state)
        # self.__timer.start()

    def is_distance_object_available(self)->bool:
        if self.__state_generator is None:
            return False
        return self.__state_generator.is_distance_object_available()

    def get_distance_object(self)->dict:
        if self.__state_generator is None:
            return {}
        return self.__state_generator.get_distance_object()
       
    def set_match_controller(self)->None:
        self.__state_generator = StateGenerator(self.__tracking_model)
        self.__state_generator.set_multi_view(self.__multi_view)

    def set_multi_view(self, m_view:bool)->None:
        self.__multi_view = m_view
        self.__state_generator.set_multi_view(self.__multi_view)

    def get_current_state(self)->dict:
        self.update_state()
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
        # self.__timer.stop()


