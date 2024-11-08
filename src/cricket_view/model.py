from .kafka import KConsumer, KProducer
from pathlib import Path
import json
from cfg.paths_config import __KAFKA_CONFIG__

class TrackingDataModel:
    def __init__(self)->None:
        self.__kafka_consumer = KConsumer(__KAFKA_CONFIG__)
        self.__kafka_producer = KProducer(__KAFKA_CONFIG__)
        self.__tracking_data_current_state = {}
        self.init()

    def init(self)->None:
        self.__kafka_consumer.subscribe('ui-data')
        self.__kafka_consumer.start()
        # self.__timer.setInterval(50)
        # self.__timer.timeout.connect(self.update)
        # self.__timer.start()

    def is_data_ready(self)->bool:
        return self.__kafka_consumer.is_data_ready()
    
    def get_data(self)->None:
        return self.__kafka_consumer.getTrackingData(True)

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