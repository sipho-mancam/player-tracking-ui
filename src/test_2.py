from cricket_view.view import TrackingWidget, load_style_sheet, OnAirWindow
from PyQt5.QtWidgets import QApplication
import sys
from cfg.paths_config import __CRICKET_STYLES__




if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_style_sheet(__CRICKET_STYLES__))
    cricket_view = OnAirWindow()
    cricket_view.show()
    
    sys.exit(app.exec_())