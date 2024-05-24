import sys
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox)

from cfg.paths_config import __TEAMS_DIR__
from pathlib import Path

class TeamInputWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Team Input Application')

        # Layouts
        main_layout = QHBoxLayout()
        team_a_layout = QVBoxLayout()
        team_b_layout = QVBoxLayout()

        # Labels
        team_a_label = QLabel('Team A')
        team_b_label = QLabel('Team B')

        # Input fields for Team A
        self.team_a_inputs = [QLineEdit(self) for _ in range(11)]
        for i, input_field in enumerate(self.team_a_inputs):
            input_field.setPlaceholderText(f'Player {i + 1}')
            team_a_layout.addWidget(input_field)

        # Input fields for Team B
        self.team_b_inputs = [QLineEdit(self) for _ in range(11)]
        for i, input_field in enumerate(self.team_b_inputs):
            input_field.setPlaceholderText(f'Player {i + 1}')
            team_b_layout.addWidget(input_field)

        # Save button
        save_button = QPushButton('Save Teams', self)
        save_button.clicked.connect(self.save_teams)

        # Adding widgets to layouts
        team_a_layout.addWidget(team_a_label)
        team_b_layout.addWidget(team_b_label)

        main_layout.addLayout(team_a_layout)
        main_layout.addLayout(team_b_layout)

        # Adding save button to the main layout
        button_layout = QVBoxLayout()
        button_layout.addWidget(save_button)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def save_teams(self):
        team_a_names = [input_field.text() for input_field in self.team_a_inputs]
        team_b_names = [input_field.text() for input_field in self.team_b_inputs]

        # Check if any input is empty
        if '' in team_a_names or '' in team_b_names:
            QMessageBox.warning(self, 'Input Error', 'All fields must be filled!')
            return

        teams = {
            'Team A': team_a_names,
            'Team B': team_b_names
        }

        with open((__TEAMS_DIR__ / Path(r'teams.json')).resolve(), 'w') as file:
            json.dump(teams, file, indent=4)

        QMessageBox.information(self, 'Success', 'Teams saved successfully!')



def start_insert()->None:
    app = QApplication(sys.argv)
    ex = TeamInputWidget()
    ex.show()
    app.exec_()


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = TeamInputWidget()
#     ex.show()
#     sys.exit(app.exec_())
