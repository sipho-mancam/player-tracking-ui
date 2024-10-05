import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QDockWidget, 
                             QPushButton, QHBoxLayout,QVBoxLayout, 
                             QWidget, QTabWidget, QLabel,
                             QMenuBar, QAction, QDialog, QLineEdit, QDialogButtonBox, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QImage, QPixmap
from tracking_interface import PlayerIDAssociationApp
from team_information_view.controller import MatchController, DataAssociationsController
from cfg.paths_config import __ASSETS_DIR__, __CONFIG_DIR__
import re
import configparser

def is_valid_ip(ip):
    # Regular expression for validating an IPv4 address
    pattern = r'^((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$'
    return re.match(pattern, ip) is not None


class ConfigUpdater:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        """Loads the configuration file."""
        self.config.read(self.config_file)

    def update_ip(self, new_ip):
        """Updates the IP address in the 'bootstrap.servers' entry."""
        # Ensure that 'default' section exists
        if 'default' in self.config:
            bootstrap_key = 'bootstrap.servers'
            current_value = self.config['default'][bootstrap_key]
            
            # Update the IP part of 'bootstrap.servers' without altering the port
            port = current_value.split(':')[1]  # Extract the port (9092)
            new_value = f"{new_ip}:{port}"
            self.config.set('default', bootstrap_key, new_value)

            # Save the changes back to the config file
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            print(f"Updated {bootstrap_key} to {new_value} in {self.config_file}")
        else:
            print("'default' section not found in the config file!")


class IPDialog(QDialog):
    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Enter IP")
        self.__layout = QVBoxLayout()
        self.__heading_text = QLabel()
        self.__splash = QLabel()
        self.__input_field = QLineEdit()
        self.__input_field.setPlaceholderText("Enter Host IP Address: 10.0.0.49")
        self.__heading_text.setText("Player Tracking Start up Config")
        self.__heading_text.setObjectName("splash-heading")
        self.__heading_text.setStyleSheet("""
                #splash-heading{
                    font-weight:500;
                    font-size: 20px;
                }
            """)
        self.__layout.addWidget(self.__heading_text)
        self.__layout.addWidget(self.__splash)
        self.__layout.addWidget(self.__input_field)
        self.ip_address = None

        self.set_up_splash()

        self.__input_field.returnPressed.connect(self.accept_ip)

         # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.setDisabled(True)
        self.button_box.accepted.connect(self.accept_ip)
        self.__layout.addWidget(self.button_box)
        self.setLayout(self.__layout)

    def set_up_splash(self)->None:
        img = QImage((__ASSETS_DIR__ / "tracking_splash.jpg").resolve().as_posix())
        self.__splash.setPixmap(QPixmap.fromImage(img))


    def check_accept(self)->None:
        text = self.__input_field.text()
        if text == "":
            return
        self.button_box.setEnabled(True)

    def accept_ip(self)->None:
        self.check_accept()

        text = self.__input_field.text()
        if is_valid_ip(text):
            self.ip_address = text
            self.accept()
        else:
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Critical)
            message_box.setWindowTitle("Incorrect IP Format")
            message_box.setText("Please enter the right IP format")
            message_box.setInformativeText("The IP Address must be of the form xx.xx.xx.xx\nWhere xx is a number from 0-255\ne.g 192.168.123.99")
            message_box.setStandardButtons(QMessageBox.Ok)
            message_box.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    host_ip = None
    ip_dialog = IPDialog()
    if ip_dialog.exec_() == QDialog.Accepted:
        host_ip = ip_dialog.ip_address
        print(f"Connecting to IP: {host_ip}...")
    else:
        sys.exit(-1)

    conf = ConfigUpdater((__CONFIG_DIR__ / "tracking_core_kafka_config.ini"))
    conf.update_ip(host_ip)

    match_controller = MatchController(host_ip)
    da_controller = DataAssociationsController()
    da_controller.set_multi_view(True)
    da_controller.set_match_controller(match_controller)

    tracking_window = PlayerIDAssociationApp(match_controller)
    tracking_window.set_data_controller(da_controller)

    app.exec_()
    da_controller.stop()