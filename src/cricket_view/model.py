from .kafka import KConsumer, KProducer
from pathlib import Path
import json
from cfg.paths_config import __KAFKA_CONFIG__
from PyQt5.QtCore import QObject, pyqtSignal
from pathlib import Path

def __load_config__(configPath:Path=Path(r"C:\ProgramData\Player Tracking Software\config.json")):
    with open(configPath, 'r') as fp:
        data = json.load(fp)
    return data

class TrackingDataModel(QObject):
    untrackedIdsChangedSignal = pyqtSignal(dict)
    idXYChangedSignal  = pyqtSignal(int, float, float)

    def __init__(self)->None:
        super().__init__()
        self.__kafka_consumer = KConsumer(__KAFKA_CONFIG__)
        self.__kafka_producer = KProducer(__KAFKA_CONFIG__)
        self.__tracking_data_current_state = {}
        self.config = __load_config__()
        self.init()

    def untrackedIdsSlot(self, event)->None:
        self.untrackedIdsChangedSignal.emit(event)
      
    def init(self)->None:
        self.__kafka_consumer.subscribe('ui-data')
        self.__kafka_consumer.subscribe(self.config['gui']['events_topic'])
        self.__kafka_consumer.start()

        self.__kafka_consumer.dataEventsSignal.connect(self.untrackedIdsSlot)
    
    def sendTCEvent(self, event:dict)->None:
        self.__kafka_producer.send_message(
            self.config["tracking_core"]["kafka"]["events_topic"] if self.config else "tracking-core-events",
            json.dumps(event) 
        )

    def onAirModeSlot(self, flag)->None:
        event = {}
        event["event_name"] = "set_on_air"
        event["event_data"] = {
            "on_air_mode":flag
        }
        self.sendTCEvent(event)

    def idXYChangedSlot(self, id, x, y)->None:
        event = {}
        event["event_name"] = "update_idxy"
        event["event_data"]={
            "id":id,
            "coordinates":[x, y]
        }
        self.sendTCEvent(event)
       
    
    def enableIdPlot(self, id)->None:
        event = {}
        event["event_name"] = "enable_id_plot"
        event["event_data"] = {
            "id":id
        }
        self.sendTCEvent(event)

    def idTrackCorrectSlot(self, id)->None:
        event = {}
        event["event_name"] = "id_track_correct"
        event["event_data"] = {
            "id":id
        }
        self.sendTCEvent(event)
        print(event)

    
    def is_data_ready(self)->bool:
        return self.__kafka_consumer.is_data_ready()
    
    def get_data(self)->None:
        data = self.__kafka_consumer.getTrackingData(True)
        return data

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

if __name__ == "__main__":
    pass
    # tm = TrackingDataModel()
    # while True:
    #     print(tm.next_frame())