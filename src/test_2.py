from cricket_view.view import CricketTrackingWidget, load_style_sheet
from PyQt5.QtWidgets import QApplication
import sys
from cfg.paths_config import __CRICKET_STYLES__




if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_style_sheet(__CRICKET_STYLES__))
    cricket_view = CricketTrackingWidget()
    cricket_view.show()
    
    sys.exit(app.exec_())