import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QPushButton, QHBoxLayout,QVBoxLayout, QWidget, QTabWidget, QStatusBar, QMenuBar, QAction, QDialog
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from camera.camera_ui import CameraWidget
from camera.controller import CamerasManager
from tracking_interface import PlayerIDAssociationApp, EnableMultiViewDialog
from team_information_view.widgets import MatchViewWidget, TeamLoadWidget, FormationManagerView
from team_information_view.controller import MatchController, DataAssociationsController
from calibration.views import CalibrationPage
from calibration.controller import CalibrationManager
from cfg.paths_config import __ASSETS_DIR__
from system_control.controller import ColorPaletteController
from system_control.palette import ColorPickerApp
from recording.view import RecordingConfigDialog
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
        self.__calibration_page = CalibrationPage()
        # Add pages to the tabes
        self.__tabs.addTab(self.__cameras_tab, "Cameras")
        self.__tabs.addTab(self.__track_tab, "Track")
        self.__tabs.addTab(self.__calib_tab, "Calibrate")
        self.__tabs.addTab(self.__config_tab, "Config")

        #Tracking Stuff
        self.load_view_a = None
        self.load_view_b = None
        self.__swap_teams = None
        self.__match_controller = None
        self.__formations_view = None
        self.__data_associations_controller = None
        
        self.init_pages()
        self.init_menue()
        self.setCentralWidget(self.__tabs)
        self.setStatusBar(self.__status_bar)

        self.__timer = QTimer(self)
        self.__timer.timeout.connect(self.update_ui)
        self.__timer.start(100)
        self.__palette_triggered = False
        self.__palette_colors = None
        self.__palette_controller = None
        self.recording_dialog = None
        self.__camera_models = None
    
    def load_camera_models(self, models:list)->None:
        self.__camera_models = models

    def update_ui(self)->None:
        if self.__palette_triggered:
            palette = ColorPickerApp(self.__palette_colors)
            if palette.exec() == QDialog.Accepted:
                # print(palette.selected_colors)
                self.__palette_triggered = False
                if self.__palette_controller is not None:
                    self.__palette_controller.update_selected_color(palette.selected_colors)

    def register_pallete_controller(self, controller)->None:
        self.__palette_controller = controller

    def set_color_palette(self, colors):
        self.__palette_colors = colors
        self.__palette_triggered = True
      
    def set_match_controller(self, controller)->None:
        self.__match_controller = controller
        if self.__match_controller is not None:
            self.__match_view_w.set_match_controller(self.__match_controller)
            self.__match_controller.set_start_button(self.open_button)
            self.open_button.setEnabled(self.__match_controller.is_match_init())

    def set_data_associations_controller(self, da_c)->None:
        self.__data_associations_controller = da_c

    def open_recording_config(self)->None:
        if self.recording_dialog is None:
            self.recording_dialog = RecordingConfigDialog(self)
        self.recording_dialog.show()
           
    def init_menue(self)->None:
        # Create a menu bar
        self.menuBar = self.menuBar()
        # Add a File menu
        file_menu = self.menuBar.addMenu('&File')
        start_recording = QAction('&Record', self)
        start_recording.setShortcut('Ctrl+R')
        start_recording.setStatusTip('Start recording all 3 streams')
        start_recording.triggered.connect(self.open_recording_config)
        file_menu.addAction(start_recording)

        team_info_menu = self.menuBar.addMenu('&Team')
        formations = QAction('&Formations', self)
        formations.triggered.connect(self.open_formation_manager)

        team_info_menu.addAction(formations)
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
    
    def get_calibration_page(self)->CalibrationPage:
        return self.__calibration_page
    
    def set_tracking_window(self, window:QWidget)->None:
        self.__tracking_window = window

    def init_pages(self)->None:
        # Other pages here...
        self.create_track_page()
        self.create_calib_page()
        self.create_cameras_page()
        
    def create_calib_page(self)->None:
        self.calib_layout = QVBoxLayout()
        self.calib_layout.addWidget(self.__calibration_page)

        self.calib_layout.setAlignment(Qt.AlignTop)
        self.__calib_tab.setLayout(self.calib_layout)
        

    def open_formation_manager(self)->None:
        if self.__formations_view is None:
            self.__formations_view = FormationManagerView(self.parentWidget())
            if self.__match_controller is not None:
                self.__formations_view.set_controller(self.__match_controller.get_formations_controller())
            self.__formations_view.show()
        else:
            self.__formations_view.show()
    

    def create_cameras_page(self)->None:
        # Create first dock widget
        qHorizantal_layout = QHBoxLayout(self)
        for cam_widget in self.__camera_docked_widgets:
            qHorizantal_layout.addWidget(cam_widget)
        self.__cameras_tab.setLayout(qHorizantal_layout)

    def load_team_a(self)->None:
        del self.load_view_a
        self.load_view_a = TeamLoadWidget(True, self.__match_controller, self.parentWidget())
        self.load_view_a.show()
       
    def load_team_b(self)->None:
        del self.load_view_b
        self.load_view_b = TeamLoadWidget(False, self.__match_controller, self.parentWidget())
        self.load_view_b.show()
        
    def swap_teams(self)->None:
        # Send an instruction to the controller to swap teams
        self.__match_controller.upload_message(0x00)
        self.update()
        
    def create_track_page(self)->None:
        self.t_layout = QVBoxLayout()
        self.__buttons_layout = QHBoxLayout()
        self.open_button = QPushButton(" Start Tracking")

        self.__load_team_a = QPushButton(' Configure Team A')
        self.__load_team_b = QPushButton(' Configure Team B')
        self.__swap_teams  = QPushButton(" Switch Sides")

        ico_path = (__ASSETS_DIR__ / 'play-24.ico').resolve().as_posix()
        bg_path = (__ASSETS_DIR__ / 'soccer_pitch_poles.png').resolve().as_posix()
        icon = QIcon(ico_path)
        self.open_button.setFixedSize(100, 30)
        # self.open_button.setFixedHeight(24)
        self.open_button.setIcon(icon)
        self.open_button.clicked.connect(self.enable_track_window)
        self.open_button.setDisabled(True)

        b_icon_path =  (__ASSETS_DIR__ / 'blue_dot.png').resolve().as_posix()
        b_icon = QIcon(b_icon_path)
        self.__load_team_a.setFixedSize(120,30)
        self.__load_team_a.clicked.connect(self.load_team_a)
        self.__load_team_a.setIcon(b_icon)

        r_icon_path = (__ASSETS_DIR__ / 'red_dot.png').resolve().as_posix()
        r_icon = QIcon(r_icon_path)
        self.__load_team_b.setFixedSize(120, 30)
        self.__load_team_b.clicked.connect(self.load_team_b)
        self.__load_team_b.setIcon(r_icon)

        s_icon_path = (__ASSETS_DIR__ / 'switch_icon.png').resolve().as_posix()
        s_icon = QIcon(s_icon_path)
        self.__swap_teams.setFixedSize(100, 30)
        self.__swap_teams.clicked.connect(self.swap_teams)
        self.__swap_teams.setIcon(s_icon)

        self.__buttons_layout.addWidget(self.open_button)
        self.__buttons_layout.addWidget(self.__swap_teams, stretch=0)
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
        self.__track_tab.setLayout(self.t_layout)

    def open_multi_view_dialog(self)->bool:
        mult_view = False
        dialog = EnableMultiViewDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            mult_view = dialog.get_result()
        return mult_view
    
    def enable_track_window(self)->None:
        m_view = self.open_multi_view_dialog()
        self.__multi_view = m_view
        self.__data_associations_controller.set_multi_view(self.__multi_view)
        self.__tracking_window = PlayerIDAssociationApp(self.__match_controller, self.parentWidget(), multi_view=m_view)
        self.__tracking_window.show()
        self.open_button.setDisabled(True)
        if self.__data_associations_controller is not None:
            self.__tracking_window.set_data_controller(self.__data_associations_controller)
    
    def closeEvent(self, event)->None:
        if self.__tracking_window is not None:
            self.__tracking_window.close()
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()

    color_pallete_controller = ColorPaletteController()
    color_pallete_controller.set_view(main_window)
    main_window.register_pallete_controller(color_pallete_controller)
    
    calibration_manager = CalibrationManager()
    calibration_manager.register_frame_view(main_window.get_calibration_page())

    cameras_manager = CamerasManager(main_window.get_camera_widgets())
    cameras_manager.registerCameraInputControllers(calibration_manager.get_camera_controllers())
    
    match_controller = MatchController()
    da_controller = DataAssociationsController()
    da_controller.set_match_controller(match_controller)

    main_window.set_match_controller(match_controller)
    main_window.set_data_associations_controller(da_controller)
    main_window.show()
    
    app.exec_()
    da_controller.stop()
    cameras_manager.stop()
    