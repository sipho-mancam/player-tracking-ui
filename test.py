import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tabbed Interface Example")
        self.setGeometry(100, 100, 600, 400)

        # Create the QTabWidget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create tabs
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        # Add tabs to the QTabWidget
        self.tabs.addTab(self.tab1, "Tab 1")
        self.tabs.addTab(self.tab2, "Tab 2")
        self.tabs.addTab(self.tab3, "Tab 3")

        # Add content to each tab
        self.create_tab_content()

    def create_tab_content(self):
        # Tab 1 content
        layout1 = QVBoxLayout()
        label1 = QLabel("This is the content of Tab 1")
        layout1.addWidget(label1)
        self.tab1.setLayout(layout1)

        # Tab 2 content
        layout2 = QVBoxLayout()
        label2 = QLabel("This is the content of Tab 2")
        layout2.addWidget(label2)
        self.tab2.setLayout(layout2)

        # Tab 3 content
        layout3 = QVBoxLayout()
        label3 = QLabel("This is the content of Tab 3")
        layout3.addWidget(label3)
        self.tab3.setLayout(layout3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
