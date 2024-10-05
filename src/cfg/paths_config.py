from pathlib import Path
import os

__BASE_PATH__ = Path(r'.').resolve()
__CONFIG_DIR__ =  (__BASE_PATH__ / Path(r'src\cfg')).resolve()
__KAFKA_CONFIG__ = (__CONFIG_DIR__ / Path(r'tracking_core_kafka_config.ini'))
__ASSETS_DIR__  = (__BASE_PATH__ / Path(r'assets')).resolve()
__MINI_MAP_BG__ = (__ASSETS_DIR__ / Path(r'soccer_pitch_poles.png'))
__TEAMS_DIR__ = Path(r"C:\ProgramData\Player Tracking Software\shared_files")#(__BASE_PATH__ / Path(r'src\teams')).resolve()
__TRACKING_DATA_DIR__ = (__BASE_PATH__ / Path(r'src\tracking_data')).resolve()
__VIDEO_REC_OUTPUT_DIR__ = Path(r"E:\Tracking Footage")
# print(os.path.exists(__TRACKING_DATA_DIR__), __TRACKING_DATA_DIR__.as_posix())