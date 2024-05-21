from kafka import KConsumer
from cfg.paths_config import __KAFKA_CONFIG__
from user_interface import QApplication, PlayerIDAssociationApp
import sys
import os
from cfg.paths_config import __TEAMS_DIR__
from pathlib import Path
from insert_teams import start_insert

def main()->int:
    # Initialize kafka in it's own thread.
    kafka_consumer = KConsumer(__KAFKA_CONFIG__)
    kafka_consumer.subscribe('system-data')
    kafka_consumer.start()

    if not os.path.exists((__TEAMS_DIR__ / Path(r'teams.json'))):
        start_insert()

    # Set up UI objects
    app = QApplication(sys.argv)
    associations_widget = PlayerIDAssociationApp()
    associations_widget.setKafkaConsumer(kafka_consumer)
    associations_widget.show()
    app.exec()
    # Clean up for the kafka service    
    kafka_consumer.stop()
    return 0


if __name__ =="__main__":
    main()