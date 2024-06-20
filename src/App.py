from kafka import KConsumer, KProducer
from cfg.paths_config import __KAFKA_CONFIG__
from tracking_interface import QApplication, PlayerIDAssociationApp
import sys
import os
from cfg.paths_config import __TEAMS_DIR__
from pathlib import Path
from insert_teams import start_insert

def main()->int:
    # Initialize kafka in it's own thread.
    kafka_consumer = KConsumer(__KAFKA_CONFIG__)
    kafka_consumer.subscribe('ui-data')
    kafka_consumer.start()
    kafka_producer = KProducer(__KAFKA_CONFIG__)

    if not os.path.exists((__TEAMS_DIR__ / Path(r'teams.json'))):
        start_insert()

    if not os.path.exists((__TEAMS_DIR__ / Path(r'teams.json'))):
        sys.exit(-1)
        
    # Set up UI objects
    app = QApplication(sys.argv)
    associations_widget = PlayerIDAssociationApp()
    associations_widget.setKafkaConsumer(kafka_consumer)
    associations_widget.setKafkaProducer(kafka_producer)
    associations_widget.show()
    app.exec()
    # Clean up for the kafka service    
    kafka_consumer.stop()
    kafka_producer.close()
    return 0


if __name__ =="__main__":
    main()