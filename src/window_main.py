import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QPushButton, QHBoxLayout,QVBoxLayout, QWidget, QTabWidget, QStatusBar, QMenuBar, QAction, QDialog
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from tracking_interface import PlayerIDAssociationApp
from team_information_view.controller import MatchController, DataAssociationsController
from cfg.paths_config import __ASSETS_DIR__


if __name__ == "__main__":
    app = QApplication(sys.argv)
    match_controller = MatchController()
    da_controller = DataAssociationsController()
    da_controller.set_match_controller(match_controller)
    
    tracking_window = PlayerIDAssociationApp(match_controller)
    tracking_window.set_data_controller(da_controller)

    app.exec_()
    da_controller.stop()