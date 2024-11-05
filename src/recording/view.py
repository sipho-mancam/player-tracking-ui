import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLineEdit, QLabel,
    QVBoxLayout, QFileDialog, QMessageBox, QHBoxLayout, QDialog, QGridLayout
)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt
from cfg.paths_config import __SYSTEM_DATA_DIR__

class RecordingConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize recording status
        self.is_recording = False
        self.recording_status = "Stopped"

        # Create layout
        self.layout = QVBoxLayout()

        # Create button to toggle recording status
        r_button_layout = QHBoxLayout()
        self.record_button = QPushButton("Start Recording")
        self.record_button.setFixedWidth(100)
        self.record_button.clicked.connect(self.toggle_recording)
        r_button_layout.addWidget(self.record_button)
        r_button_layout.setAlignment(Qt.AlignRight)
        self.layout.addLayout(r_button_layout)

        # Create layout for recording status with icon
        self.status_layout = QHBoxLayout()

        # Create label to display recording status
        self.status_label = QLabel(f"Recording Status:")
        self.recording_status_text = QLabel(f"{self.recording_status}")
        self.status_layout.addWidget(self.status_label)
        self.status_layout.addWidget(self.recording_status_text)
        
        # Create SVG red dot for recording indicator
        self.red_dot = QSvgWidget()
        self.red_dot.setFixedSize(20, 20)
        self.red_dot.load(bytearray(self.get_red_dot_svg(), encoding="utf-8"))
        self.red_dot.setVisible(False)  # Initially hidden
        self.status_layout.addWidget(self.red_dot)

        # Add the status layout to the main layout
        self.layout.addLayout(self.status_layout)

        # Create text field for recording name
        r_name_layout = QHBoxLayout()
        self.recording_name_label = QLabel("Recording Name:")
        r_name_layout.addWidget(self.recording_name_label)
        self.recording_name_field = QLineEdit(self)
        self.recording_name_field.setFixedWidth(300)
        r_name_layout.addWidget(self.recording_name_field)
        self.layout.addLayout(r_name_layout)

        # Create save as field to get the path
        save_as_layout = QHBoxLayout()
        self.path_label = QLineEdit("Save Path: Not selected")
        self.path_label.setDisabled(True)
        self.path_label.setFixedWidth(300)
        save_as_layout.addWidget(self.path_label)
        self.save_as_button = QPushButton("Save As Directory")
        self.save_as_button.clicked.connect(self.get_save_path)
        save_as_layout.addWidget(self.save_as_button)
        self.layout.addLayout(save_as_layout)


        # Create close button to save configuration
        buttons_layout = QHBoxLayout()
        self.close_button = QPushButton("Save Config")
        self.close_button.clicked.connect(self.save_config)
        self.close_button.setFixedWidth(100)
        buttons_layout.addWidget(self.close_button)
        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedWidth(100)
        self.close_btn.clicked.connect(self.close)
        # buttons_layout.addWidget()
        buttons_layout.addWidget(self.close_btn)
        buttons_layout.setAlignment(Qt.AlignRight)

        self.layout.addLayout(buttons_layout)

        # Set layout and window title
        self.setLayout(self.layout)
        self.setWindowTitle("Recording Configuration")

        # Initialize save path
        self.save_path = ""

    def toggle_recording(self):
        """Toggle recording status between Recording and Stopped."""
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.record_button.setText("Stop Recording")
            self.recording_status = "Recording"
            self.red_dot.setVisible(True)  # Show red dot
        else:
            self.record_button.setText("Start Recording")
            self.recording_status = "Stopped"
            self.red_dot.setVisible(False)  # Hide red dot
        self.recording_status_text.setText(f"{self.recording_status}")

    def get_save_path(self):
        """Open a dialog to select a directory and save the path."""
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", "", options=options)
        if directory:
            self.save_path = directory
            self.path_label.setText(f"Save Path: {self.save_path}")

    def save_config(self):
        """Save the current configuration to a JSON file."""
        recording_name = self.recording_name_field.text()
        if not recording_name or not self.save_path:
            QMessageBox.warning(self, "Error", "Please provide a recording name and save directory.")
            return

        config = {
            "recording_name": recording_name,
            "recording_status": 1 if self.recording_status == "Recording" else 0,
            "save_path": self.save_path
        }

        try:
            with open((__SYSTEM_DATA_DIR__ / "recording_config.json"), "w") as json_file:
                json.dump(config, json_file, indent=4)
            QMessageBox.information(self, "Success", "Configuration saved successfully.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    def get_red_dot_svg(self):
        """Return an SVG string for a red dot."""
        return """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="30" fill="red" stroke="black" stroke-width="10"/>
        </svg>
        """

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = RecordingConfigDialog()
#     window.show()
#     sys.exit(app.exec_())
