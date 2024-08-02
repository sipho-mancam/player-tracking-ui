import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QTextEdit, QListView, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class LineGraphCanvas(FigureCanvas):
    def __init__(self, parent=None, width=4, height=1.5, dpi=100):
        self.fig, self.ax = plt.subplots()
        super().__init__(self.fig)
        self.setParent(parent)
        self.title_font_size = 8
        self.line, = self.ax.plot([], [], 'b-')  # 'g-' means green line
        self.ax.set_xlim(0, 19)
        self.ax.set_ylim(0, 15)  # You can adjust the limits as needed
        self.x_data = np.arange(20)
        self.y_data = np.zeros(20)
        self.line.set_data(self.x_data, self.y_data)
        
        self.background = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        self.draw()

        # Set a fixed size for the canvas
        self.setFixedSize(int(width * dpi), int(height * dpi))

         # Enable grid and remove axes
        self.ax.grid(True)
        self.ax.set_title("Frame Rate", fontsize=self.title_font_size)
        # Set font size for tick labels
        self.ax.tick_params(labelsize=self.title_font_size)
        self.ax.set_xticklabels([])
        self.ax.set_xticks([i for i in range(20)])
        self.ax.set_yticks([i for i in range(15)])

    
    def update_graph(self, new_values):
        self.fig.canvas.restore_region(self.background)
        self.y_data = new_values
        self.line.set_ydata(self.y_data)
        self.ax.draw_artist(self.line)
        self.fig.canvas.blit(self.ax.bbox)
        self.fig.canvas.flush_events()
        self.draw()


class CameraWidget(QDockWidget):
    def __init__(self, name:str, parent:QWidget)->None:
        super().__init__(name, parent)
        self.__window_name =  name
        self.__parent = parent
        self.__camera_input = None # Camera Input Device.
        self.__heading_text = name
        self.__main_layout = None
        self.__frame_container = None
        self.__details_list = None
        self.__details_widget = QWidget(self)
        self.__frame_rate = None
        self.__frame_drop = None
        self.__frame_count = None
        self.__frame_size = None
        self.__main_widget = QWidget(self)
        self.__bold_text = "font-weight: 500; font-size: 12px;"
        self.__ui_width = 600
        self.__ui_height = 480
        self.__camera_data = {}
        self.__update_timer = QTimer()
        self.__frame_rate_timer = QTimer()
        self.__frame_rate_list = []
        self.__frame_rate_avg = 0
        self.__fr_history_data = []
        self.__fr_index = 0
        self.__frame = None
        self.init()

    def init(self)->None:
        self.__main_layout = QVBoxLayout(self)
        # self.__heading_text = QLabel(f"{self.__window_name}")
        # self.__heading_text.setStyleSheet(self.__bold_text)
        
        self.__frame_container = QLabel()
        self.__frame_container.setPixmap(QPixmap(self.__ui_width, self.__ui_height))
        self.__frame_container.setStyleSheet("background-color:black;")
        
        # Details List:
        # list_heading = QLabel("Details", self)
        # list_heading.setStyleSheet(self.__bold_text)
        self.__details_list = QVBoxLayout(self)
        self.__name = QLabel(f"Name : {self.__window_name}", self)
        self.__frame_size = QLabel("Frame Size: 2048 x 1942", self)
        self.__frame_rate = QLabel("Frame Rate: 10 fps", self)
        self.__frame_drop = QLabel("Frame Drops: 0", self)
        self.__frame_count = QLabel("Frame Count: 0", self)
        self.__shared_memory = QLabel("Memory Name: ", self)

        font_style = "font-size: 14px;"
        self.__name.setStyleSheet(font_style)
        self.__frame_size.setStyleSheet(font_style)
        self.__frame_rate.setStyleSheet(font_style)
        self.__frame_drop.setStyleSheet(font_style)
        self.__frame_count.setStyleSheet(font_style)
        self.__shared_memory.setStyleSheet(font_style)
        
        # Add list items
        self.__details_list.addWidget(self.__name)
        self.__details_list.addWidget(self.__frame_size)
        self.__details_list.addWidget(self.__frame_rate)
        self.__details_list.addWidget(self.__frame_drop)
        self.__details_list.addWidget(self.__frame_count)
        self.__details_list.addWidget(self.__shared_memory)
        self.__details_list.setSpacing(0)
        self.__details_list.setContentsMargins(20,10,0,0)

        self.__details_widget.setLayout(self.__details_list)

        self.__frame_rate_graph = QLabel()
        self.__frame_rate_graph.setPixmap(QPixmap(self.__ui_width//3, self.__ui_height//3))
        self.__frame_rate_graph.setStyleSheet("background-color: black;")
        self.__camera_canvas = LineGraphCanvas(self)

        # Add Widgets to the main layout
        # self.__main_layout.addWidget(self.__heading_text)
        self.__main_layout.addWidget(self.__frame_container)
        # self.__main_layout.addWidget(list_heading)
        self.__main_layout.addWidget(self.__details_widget)
        self.__main_layout.addWidget(self.__camera_canvas)
        self.__main_layout.setSpacing(0)

        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.__main_widget.setLayout(self.__main_layout)
        self.__main_widget.setObjectName("main-widget")
        self.__main_widget.setStyleSheet("#main-widget{border:1px solid grey;}")

        self.setWidget(self.__main_widget)

        self.__update_timer.timeout.connect(self.update)
        self.__update_timer.start(50)
        self.__frame_rate_timer.timeout.connect(self.update_frame_rate)
        self.__frame_rate_timer.start(1000)


    def set_camera_input(self, input_source)->None:
        self.__camera_input = input_source

    def update_frame_rate(self)->None:
        try:
            arr = np.array(self.__frame_rate_list)
            self.__frame_rate_avg = np.round(np.average(arr), 1)
            self.__frame_rate_list = []
            self.__frame_rate.setText(f"Frame Rate: {self.__frame_rate_avg} fps")

            if len(self.__fr_history_data) == 0:
                self.__fr_history_data = [0 for i in range(20)]
                self.__fr_history_data = np.array(self.__fr_history_data)

            if self.__fr_index == 19:
                self.__fr_history_data = self.__fr_history_data[1:]
                self.__fr_history_data = np.append(self.__fr_history_data, self.__frame_rate_avg)
            else:
                self.__fr_history_data[self.__fr_index] = self.__frame_rate_avg

            if self.__fr_index < 19:
                self.__fr_index  += 1
            
            self.__camera_canvas.update_graph(self.__fr_history_data)
        except Exception as e:
            pass

    def set_camera_data(self, data)->None:
        # This is a dictionary containing all the data we need to update with on the UI
        self.__camera_data = data

    def update(self)->None:
        name = self.__camera_data.get('name')
        if name is not None:
            self.__name.setText(f"Name: {name}")
        
        size = self.__camera_data.get('frame_size')
        if size is not None:
            self.__frame_size.setText(f"Frame Size: {size[1]} x {size[0]}")
        
        frame_rate = self.__camera_data.get('frame_rate')
        if frame_rate is not None:
            self.__frame_rate_list.append(frame_rate)
           
        
        frame_drops = self.__camera_data.get('frame_drops')
        if frame_drops is not None:
            self.__frame_drop.setText(f"Frame Drops: {frame_drops}")
        
        frame_counter = self.__camera_data.get('frame_count')
        if frame_counter is not None:
            self.__frame_count.setText(f"Frame Counter: {frame_counter}")

        shared_mem_name = self.__camera_data.get("Memory Name")
        if shared_mem_name is not None:
            self.__shared_memory.setText(f"Memory Name: {shared_mem_name}_instance(int)")

        if self.__frame is not None:
            self.__frame = cv.resize(self.__frame,  (self.__ui_width, self.__ui_height))
            height, width, _  = self.__frame.shape
            row_bytes = 3 * width
            q_img = QImage(self.__frame.data, width, height, row_bytes, QImage.Format_BGR888)
            self.__frame_container.setPixmap(QPixmap.fromImage(q_img))


    def update_frame(self, frame:cv.Mat)->None:
        self.__frame = frame.copy()
        
       


