import cv2 as cv
import numpy as np
from pathlib import Path
import os
from threading import Thread, Event, Condition
from pypylon import pylon, genicam
import cv2
import threading
import time

import mmap
import ctypes
from ctypes import wintypes
import ctypes.wintypes
import cv2
import numpy as np
import time
# from cfg.paths_config import __VIDEO_REC_OUTPUT_DIR__
import cupy as cp
from .shared_memory_video_api import VideoShared
# from network_stream import UDPStream

__VIDEO_REC_OUTPUT_DIR__ = Path(r"E:\Tracking Footage")

class BInputSource:
    def __init__(self, i_type:str, stream_id):
        self._type = i_type
        self._stream_id = stream_id
        self._frame_drops = 0
        self._stream_data = {}

    def get_frame_drops(self)->int:
        return self._frame_drops

    def get_stream_data(self)->dict:
        return self._stream_data 

    def update_stream_data(self)->None:
        pass

    def start_grabbing(self)->None:
        pass


class SharedMemoryReader:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.buffer = bytearray(size)# Create a ctypes array for the buffer
        self.pBuf = None

        # Open the file mapping object
        self.hMapFile = ctypes.windll.kernel32.OpenFileMappingW(
            wintypes.DWORD(0xF001F),  # FILE_MAP_ALL_ACCESS
            wintypes.BOOL(False),
            wintypes.LPCWSTR(name)
        )

        if not self.hMapFile:
            raise Exception(f"Could not open file mapping object ({ctypes.GetLastError()}).\nMake sure the Kit Detector process is running before running this process.")
        
        self.file_map = mmap.mmap(0, size, tagname=name, access=mmap.ACCESS_READ)

        # Open the event object for synchronization
        self.hEvent = ctypes.windll.kernel32.OpenEventW(
            wintypes.DWORD(0x1F0003),  # EVENT_ALL_ACCESS
            wintypes.BOOL(False),
            wintypes.LPCWSTR(name + "_Event")
        )

        if not self.hEvent:
            ctypes.windll.kernel32.UnmapViewOfFile(self.pBuf)
            ctypes.windll.kernel32.CloseHandle(self.hMapFile)
            raise Exception(f"Could not open event object ({ctypes.GetLastError()}).")

        print("Shared Reader created successfully")

    def __del__(self):
        if self.pBuf:
            ctypes.windll.kernel32.UnmapViewOfFile(self.pBuf)
        if self.hMapFile:
            ctypes.windll.kernel32.CloseHandle(self.hMapFile)
        if self.hEvent:
            ctypes.windll.kernel32.CloseHandle(self.hEvent)

    def read_from_memory(self):
        result = ctypes.windll.kernel32.WaitForSingleObject(self.hEvent, wintypes.DWORD(-1))  # INFINITE
        
        if result != 0:  # WAIT_OBJECT_0
            raise Exception(f"WaitForSingleObject failed ({ctypes.GetLastError()}).")
        
        self.file_map.seek(0)
        self.buffer = self.file_map[:]
        return self.buffer


class CameraModel(BInputSource):
    def __init__(self, stream_id, event_object:Condition)->None:
        super().__init__('', stream_id)
        self.__stream_id = stream_id
        self.__event_object = event_object
        self.__current_frame = None
        self.__frame_count = 0
        self._data_updated = False

        self._stream_data = {}
        self._stream_data['name'] = "Camera "+str(stream_id)
        self._stream_data['frame_rate'] = 0
        self._stream_data['frame_drops'] = 0
        self._stream_data['frame_count']  = self.__frame_count
        self._stream_data['frame_size'] =  (1942, 2048)
        self._stream_data['Memory Name'] =  "default mem from VIS"

    def update_frame(self, frame)->None:
        self.__current_frame = frame
        self.__frame_count += 1
        self.update_stream_data()
        self._data_updated  = True

    def _is_updated(self)->bool:
        return self._data_updated
    
    def set_frame_rate(self, fps)->None:
        self._stream_data['frame_rate'] = fps

    def next(self)->cv.Mat:
        # This waits until the manager triggers it.
        self.__event_object.acquire(True)
        self.__event_object.wait_for(self._is_updated)
        self._data_updated = False
        # self.__event_object.release()
        return self.__current_frame
    
    def update_stream_data(self) -> None:
        super().update_stream_data()
        self._stream_data['frame_count'] = self.__frame_count
    
    def stop(self)->None:
        self._data_updated = True
    
    


class InputManager:
    """
    This class is a utility class that implements the portability between having a physical input directly
    and using shared memory utilities to receive video information.
    The logic in this class is that, it implements the threaded waiting and the input loop,
    that splits the unified memory buffer to individual camera frames and assign them to each
    camera model class that is assigned to the controller,
    if necessary, updates the frame rate and other paramenters for each camera

    """
    def __init__(self, shared_mem_name, size)->None:
        self.__frame_size = size
        self.__shm_name = shared_mem_name
        self.__shm = SharedMemoryReader(self.__shm_name, self.__frame_size*3)
        self._data_ready_event = Condition()
        self.__camera_models = [CameraModel(0, self._data_ready_event), 
                                CameraModel(1, self._data_ready_event), 
                                CameraModel(2, self._data_ready_event)]
        self.__stop_event = Event()
        self.worker = None
        self.init()

    def init(self)->None:
        """
        This function implements the start up sequence of our SHM camera model
        """
        self.worker = Thread(target=self.__run)
        self.worker.start()

    def __run(self)->None:
        current_frame_rate = 0
        while not self.__stop_event.is_set():
            start_time = time.time()
            buffer = self.__shm.read_from_memory()
            for i in range(3):
                curr = bytearray(buffer[i * self.__frame_size:(i + 1) * self.__frame_size])
                frame = np.frombuffer(curr, dtype=np.uint8).reshape((1942, 2590, 3))
                self.__camera_models[i].update_frame(frame)
                self.__camera_models[i].set_frame_rate(current_frame_rate)
            try:
                self._data_ready_event.acquire()
                self._data_ready_event.notify_all()
                self._data_ready_event.release()
            except RuntimeError as re:
                print("There was a runtime error on the conditional variable ")
                print(re.with_traceback())
            end_time = time.time()
            print(f"Waited for: {round((end_time- start_time)*1e3)} ms")
            current_frame_rate = round(1e3/((end_time- start_time)*1e3),1)

    def stop(self)->None:
        if self.worker is not None:
            self.__stop_event.set()
            self.worker.join() 
            return 
        self.__stop_event.set()
        self._data_ready_event.release()

     
    def __del__(self)->None:
        self.stop()

    def get_input_stream(self, index:int)->CameraModel:
        return self.__camera_models[index]