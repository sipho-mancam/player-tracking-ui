import cv2 as cv
import os
from view import FrameView, CameraSelector, CalibrationPage
from PyQt5.QtWidgets import QApplication
import sys
from threading import Thread
import time
__DATA_DIR__ = r"C:\Users\Sipho\Pictures\Cricket Image Data"


# cv.namedWindow("Preview", cv.WINDOW_NORMAL)
def update_frames(frame_view:CameraSelector)->None:
    for file in os.scandir(__DATA_DIR__):
        frame = cv.imread(file.path)
        frame_view.update_frame(frame)
        time.sleep(0.05)

def main():
    app = QApplication(sys.argv)
    frame_view = CalibrationPage()
    # t = Thread(target=update_frames, args=(frame_view,))
    # t.start()
    frame_view.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()



