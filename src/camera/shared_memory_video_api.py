from multiprocessing.shared_memory import SharedMemory
import numpy as np
import cv2 as cv
import time


class SharedEvent:
    def __init__(self, name:str, create:bool=False)->None:
        self.__memory_identifier = name
        self.__shared_mem = SharedMemory(self.__memory_identifier, create, 4)
        self.__state = 0
        self.__loop_start = 0
        self.__loop_end = 0

    def set(self)->None:
        self.__state = 1
        self.__shared_mem.buf[0] = self.__state
        
    def clear(self)->None:
        self.__state = 0
        self.__shared_mem.buf[0] = self.__state
        self.__loop_start = 0
       
    def wait(self, time_out=-1, state=0)->None:
        self.__loop_start = time.time()
        while self.__state == state:
            self.__state = self.__shared_mem.buf[0]
            self.__loop_end = time.time()
            if time_out == -1:
                continue
            if round((self.__loop_end - self.__loop_start)*1000) > time_out:
                break
    
    def is_set(self)->bool:
        return self.__state == 1
        

class VideoShared:
    def __init__(self, mem_name:str, video_size:int)->None:
        """
        VideoSize: (width, height, depth)
        mem_name: SharedMemory Identifier
        """
        self.__memory_identifier = mem_name
        self.__total_bytes = video_size
        self.__shared_mem_buffer = None
        
        try:
            self.__shared_mem = SharedMemory(self.__memory_identifier, True, self.__total_bytes)
        except FileExistsError:
            self.__shared_mem = SharedMemory(self.__memory_identifier)

        try:
            self.__event = SharedEvent(self.__memory_identifier + "_event", True)
        except FileExistsError:
            self.__event = SharedEvent(self.__memory_identifier+ "_event")


    def get_video_bytes_size(self):
        return self.__total_bytes
    
    def write_buffer(self, buf:np.ndarray)->None:
        self.__event.wait(10, state=1) # Wait for it to be cleared
        if self.__shared_mem_buffer is None:
            self.__shared_mem_buffer = np.ndarray(buf.shape, buf.dtype, buffer=self.__shared_mem.buf)
        self.__shared_mem_buffer[:] = buf[:]
        self.__event.set()
        

class VideoSharedRead:
    def __init__(self, mem_name, shape, dtype)->None:
        self.__memory_identifier = mem_name
        self.__shape = shape
        self.__dtype = dtype
        self.__shared_mem_buffer = None
        self.__shared_mem = SharedMemory(self.__memory_identifier)
        self.__event = SharedEvent(self.__memory_identifier+"_event")
    
    def read(self)->np.ndarray:
        self.__event.wait()
        if self.__shared_mem_buffer is None:
            self.__shared_mem_buffer = np.ndarray(self.__shape, self.__dtype, self.__shared_mem.buf)
        self.__event.clear()
        return self.__shared_mem_buffer
    



    


    



