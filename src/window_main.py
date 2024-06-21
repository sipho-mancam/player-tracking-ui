import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QPushButton, QHBoxLayout,QVBoxLayout, QWidget, QTabWidget, QStatusBar, QMenuBar, QAction
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from camera.camera_ui import CameraWidget
from camera.controller import CamerasManager
from tracking_interface import PlayerIDAssociationApp
from team_information_view.widgets import MatchViewWidget
from cfg.paths_config import __ASSETS_DIR__

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set main window properties
        self.setWindowTitle("Player Tracking Application")
        self.setGeometry(100, 100, 800, 600)
        self.__tabs = QTabWidget(self)
        self.__status_bar = QStatusBar(self)
        self.t_layout = None
        self.__tracking_window = None

        #Create tab pages
        self.__cameras_tab = QWidget()
        self.__config_tab = QWidget()
        self.__calib_tab = QWidget()
        self.__track_tab = QWidget()

        self.__camera_docked_widgets = [
                CameraWidget("Camera 1", self),
                CameraWidget("Camera 2", self),
                CameraWidget("Camera 3", self)
            ]
        # Add pages to the tabes
        self.__tabs.addTab(self.__cameras_tab, "Cameras")
        self.__tabs.addTab(self.__track_tab, "Track")
        self.__tabs.addTab(self.__calib_tab, "Calibrate")
        self.__tabs.addTab(self.__config_tab, "Config")
        
        self.init_pages()
        self.init_menue()
        self.setCentralWidget(self.__tabs)
        self.setStatusBar(self.__status_bar)

    def init_menue(self)->None:
        # Create a menu bar
        self.menuBar = self.menuBar()
        # Add a File menu
        file_menu = self.menuBar.addMenu('&File')
        start_recording = QAction('&Record', self)
        start_recording.setShortcut('Ctrl+R')
        start_recording.setStatusTip('Start recording all 3 streams')
        file_menu.addAction(start_recording)

        # Add actions to the File menu
        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Add a Help menu
        help_menu = self.menuBar.addMenu('&Help')

        # Add actions to the Help menu
        about_action = QAction('&About', self)
        about_action.setStatusTip('About this application')
        # about_action.triggered.connect(self.about_message)
        help_menu.addAction(about_action)

    def get_camera_widgets(self)->list[CameraWidget]:
        return self.__camera_docked_widgets
    
    def set_tracking_window(self, window:QWidget)->None:
        self.__tracking_window = window

    def init_pages(self)->None:
        self.create_cameras_page()
        # Other pages here...
        self.create_track_page()

    def create_cameras_page(self)->None:
        # Create first dock widget
        qHorizantal_layout = QHBoxLayout(self)
        for cam_widget in self.__camera_docked_widgets:
            qHorizantal_layout.addWidget(cam_widget)
        self.__cameras_tab.setLayout(qHorizantal_layout)

    def create_track_page(self)->None:
        self.t_layout = QVBoxLayout()
        self.__buttons_layout = QHBoxLayout()
        self.open_button = QPushButton(" Start Tracking")

        self.__load_team_a = QPushButton('Load Beam A')
        self.__load_team_b = QPushButton('Load Team B')
    

        ico_path = (__ASSETS_DIR__ / 'play-24.ico').resolve().as_posix()
        bg_path = (__ASSETS_DIR__ / 'soccer_pitch_poles.png').resolve().as_posix()
        icon = QIcon(ico_path)
        self.open_button.setFixedSize(100, 24)
        # self.open_button.setFixedHeight(24)
        self.open_button.setIcon(icon)
        self.open_button.clicked.connect(self.enable_track_window)

        self.__load_team_a.setFixedSize(100, 24)
        self.__load_team_b.setFixedSize(100, 24)

        self.__buttons_layout.addWidget(self.open_button)
        self.__buttons_layout.addWidget(self.__load_team_a, stretch=0)
        self.__buttons_layout.addWidget(self.__load_team_b, stretch=0)
        self.__buttons_layout.setSpacing(0)
        self.__buttons_layout.setAlignment(Qt.AlignLeft)


        self.__match_view_w = MatchViewWidget()
        self.__match_view_w.setStyleSheet(
            """
                           #match-view{
                            background-image:url(""" + bg_path + """); 
                            background-repeat:no-repeat; 
                            background-position:center;
                            border:1px solid black;
                           }"""
        )


        self.t_layout.addLayout(self.__buttons_layout)
        self.t_layout.addWidget(self.__match_view_w)
        
        # t_layout.addWidget(PlayerIDAssociationApp(self))
        self.__track_tab.setLayout(self.t_layout)
    
    def enable_track_window(self)->None:
        self.__tracking_window = PlayerIDAssociationApp(self.parentWidget())
        self.__tracking_window.show()
        self.open_button.setDisabled(True)
    
    def closeEvent(self, event)->None:
        if self.__tracking_window is not None:
            self.__tracking_window.close()
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    cameras_manager = CamerasManager(main_window.get_camera_widgets())
    match_controller = None
    main_window.show()
    app.exec_()
    cameras_manager.stop()