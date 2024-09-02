import cv2 as cv
import numpy as np
from pathlib import Path
import os
from threading import Thread, Event
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

class InputStream(BInputSource):
    def __init__(self, path:Path, id, **kwargs)->None:
        super().__init__('video_file', id)
        self.__path = path
        self.__stream = [] # keeps list of 3 frame
        self.__files_list = []
        self.__current_index = 0
        self.__index = 0
        self.__worker = None
        self.__stream_id = id
        self.__video = False
        self.__polygons = []
        self.__start_flag = None
        if 'video' in kwargs:
            self.__video = kwargs.get('video')
        self.__init()

    def set_start_flag(self, flag:Event)->None:
        self.__start_flag = flag

    def __init(self)->None:
        # The stream is a video
        if self.__video:
            self.__stream =  cv.VideoCapture(self.__path)
            return

        # Directory with still images
        if os.path.isdir(self.__path):
            for file in os.scandir(self.__path):
                if file.path.endswith(('.bmp', '.tiff', '.png', '.jpg', '.jpeg')):
                    self.__files_list.append(file.path)
        self.__bootstrap()
    
    def __bootstrap(self):
        for idx, file in enumerate(self.__files_list):
            self.__stream.append(cv.imread(file))
            self.__current_index += 1
            if self.__current_index >= 5:
                return

    def readOne(self):
        for i in range(1): 
            if len(self.__stream) > 10:
                return 
            if len(self.__files_list)-1 > self.__current_index:     
                self.__stream.append(cv.imread(self.__files_list[self.__current_index]))
                self.__current_index +=1

    
    def next(self)->cv.Mat:
        if self.__video:
            _, frame = self.__stream.read()
            if frame is None: # this means the video is at the end, kill the object and restart the video reader.
                del self.__stream
                self.__init()
                _, frame = self.__stream.read()
            return frame

        if (len(self.__stream)-1) < self.__index and self.__worker is not None:
            self.__worker.join()

        self.__worker = Thread(target=self.readOne).start()
        frame = self.__stream.pop(0)
        # frame = self.__fill_polygons(frame)
        self.__index += 1
        return frame
    
    def stop(self)->None:
        if self.__video:
            self.__stream.release()

    def stop_recording(self)->None:
        pass

    def stop_grabbing(self)->None:
        pass

    def start_recording(self)->None:
        pass

    def start_grabbing(self)->None:
        pass

    def set_polygons(self, poly):
        self.__polygons = poly

    def is_recording(self)->bool:
        # if self.__video:
        return False
    
    def get_frame_rate(self)->float:
        return 0
    
    def Is_grabbing(self)->bool:
        if self.__video:
            return self.__stream.isOpened()
        return True
    
    def start_grabbing(self)->None:
        pass

    def __fill_polygons(self, frame:cv.Mat)->cv.Mat:
        # height, width = frame.shape[:2]
        masked_img = frame#.copy()  # White canvas
        for poly in self.__polygons:
            masked_img = cv.fillPoly(masked_img, [poly], (0,0,0))
        return masked_img
    

class InputStreamB(BInputSource):
    def __init__(self, camera:pylon.InstantCamera, id=0):
        super().__init__('camera', 0)
        self.camera = camera
        self.is_grabbing = False
        self.grab_thread = None
        self.frames_buffer = []
        self.converter = pylon.ImageFormatConverter()
        self.data_ready = Event()
        self.recording = False
        self.video_writer = None
        self.__polygons = None
        self.__start_flag = None
        self.__mask_image = None
        self.__cuda_stream = cp.cuda.Stream()
        # self.__udp_stream = UDPStream('127.0.0.1', 9129)
        self.__frame_time = 1
        self.__frame_count = 0
        self.__frame = None
        self.__stream_id = id
        self.__shared_mem = []
        self.__shared_mem_name = None
        self.init()

    def set_start_flag(self, flag:Event)->None:
        self.__start_flag = flag

    def set_polygons(self, polys):
        self.__polygons = polys

    def get_frame_rate(self)->float:
        if self.__frame_time ==0:
            self.__frame_time = 1000

        frame_rate = 1000/self.__frame_time
        return round(frame_rate, 1)
    
    def __fill_polygons(self, frame:cv.Mat)->cv.Mat:
        # start_time = time.time()
        if self.__mask_image is None:
            self.__generate_masked_image(frame)

        with self.__cuda_stream:
            frame_gpu = cp.asarray(frame, blocking=True)
            frame_gpu[self.__mask_image == 0] = [0, 0, 0]
            frame_cpu = cp.asnumpy(frame_gpu, self.__cuda_stream, blocking=True)
            # end_time = time.time()
            # proc_time = round((end_time - start_time)*1000)
            # print(f"Poly Fill Time: {proc_time}ms {self.camera.GetDeviceInfo().GetFriendlyName()}")
            return frame_cpu
     
    
    def __generate_masked_image(self, image:cv.Mat)->None:
        self.__mask_image = np.zeros(image.shape[:2], dtype=np.uint8) + 255
        self.__mask_image = cv.fillPoly(self.__mask_image, self.__polygons, 0)
        with self.__cuda_stream:
            self.__mask_image = cp.asarray(self.__mask_image, blocking=True)
    
    def init(self):
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        # self.__udp_stream.start()

    def is_recording(self)->bool:
        return self.recording

    def start_grabbing(self):
        while not self.camera.IsGrabbing():
            try:
                    self.camera.StartGrabbing()
            except genicam.GenericException as ge:
                pass
            finally:
                time.sleep(0.1)

        self.is_grabbing = self.camera.IsGrabbing()
        self.grab_thread = threading.Thread(target=self._grab_loop)
        self.grab_thread.start()

    def Is_grabbing(self)->bool:
        return self.camera.IsGrabbing()

    def _grab_loop(self):
        while self.is_grabbing:
            start_time = time.time()
            try:    
                grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grab_result.GrabSucceeded():
                    image = self.converter.Convert(grab_result)
                    img = image.GetArray()
                    
                    if self.recording:
                        try:
                            self.video_writer.write(img)
                        except Exception as e:
                            pass
                    #  # add the poly fill
                    if self.__polygons is not None:
                        img = self.__fill_polygons(img)
                    
                    if len(self.__shared_mem) == 0:
                        self.__shared_mem_name = "frame_buffer_"+str(self.__stream_id)
                        self.__shared_mem = [ 
                            VideoShared("frame_buffer_"+str(self.__stream_id)+"_0", img.nbytes),
                            VideoShared("frame_buffer_"+str(self.__stream_id)+"_1", img.nbytes)
                        ]
                    
                    self.__shared_mem[self.__frame_count*0].write_buffer(img)
                    self.__frame_count += 1
                    self.frames_buffer.append(img)
                    self.__frame = img
                    self.data_ready.set()
                    if len(self.frames_buffer) > 5:
                        self.frames_buffer.pop(0) # remove the oldest frame
                        self._frame_drops += 1
                grab_result.Release()
            except genicam.GenericException as ge:
                pass

            end_time = time.time()
            self.__frame_time = round((end_time - start_time)*1000)
            self.update_stream_data()


    def update_stream_data(self)->None:
        super().update_stream_data()
        self._stream_data['name'] = self.camera.GetDeviceInfo().GetFriendlyName()
        self._stream_data['frame_rate'] = self.get_frame_rate()
        self._stream_data['frame_drops'] = self.get_frame_drops()
        self._stream_data['frame_count']  = self.__frame_count
        self._stream_data['frame_size'] = self.__frame.shape[:2] if self.__frame is not None else (1942, 2048)
        self._stream_data['Memory Name'] =  self.__shared_mem_name 


    def start_recording(self, fps=10.0):
        output_file_name = self.camera.GetDeviceInfo().GetFriendlyName() + str(time.time()) + ".mp4"
        output_file = (__VIDEO_REC_OUTPUT_DIR__ / Path(output_file_name)).resolve().as_posix()
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(output_file, fourcc, fps, (self.camera.Width.GetValue(), self.camera.Height.GetValue()))
        self.recording = True

    def stop_recording(self):
        self.recoring = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

    def next(self)->cv.Mat:
        self.data_ready.wait()
        if len(self.frames_buffer) > 0:
            self.data_ready.clear()
            return self.frames_buffer.pop(0)

    def stop_grabbing(self):
        self.is_grabbing = False
        self.camera.StopGrabbing()
        if self.grab_thread:
            self.grab_thread.join()

    def get_camera_info(self):
        try:
            frame_rate = self.camera.AcquisitionFrameRate.GetValue()
            transmission_speed = self.camera.ResultingDataRate.GetValue()
            return {
                'frame_rate': frame_rate,
                'transmission_speed': transmission_speed
            }
        except Exception as e:
            return  {
                'frame_rate': "N/A",
                'transmission_speed': "N/A"
            }
        
    def stop(self):
        self.stop_recording()
        self.stop_grabbing()
        self.camera.Close()


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
            raise Exception(f"Could not open file mapping object ({ctypes.GetLastError()}).")
        
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



class InputStreams:
    def __init__(self, num_of_streams, paths_list, **kwargs)->None:
        self.number_of_streams = num_of_streams
        self.paths_list = paths_list
        self.streams_list = []
        self.__init()

    def __init(self)->None:
        for idx, p in enumerate(self.paths_list):
            self.streams_list.append(InputStream(p,idx))
        
    def next(self)->list[cv.Mat]:
        result = []
        for stream in self.streams_list:
            frame = stream.next()
           
            if frame is not None:
                result.append(frame)
        return result
    
class DeviceFactory:
    def __init__(self):
        self.cameras = []

    def wait_for_cameras(self, num_cameras=3):
        print("waiting for cameras ...")
        tlFactory = pylon.TlFactory.GetInstance()
        devices = tlFactory.EnumerateDevices()
        while len(devices) < num_cameras:
            # pass
            # Initialize cameras and add to the list
           devices = tlFactory.EnumerateDevices()
           if len(devices) < num_cameras:
               print(f"Waiting for {num_cameras - len(devices)} cameras to come online ...")
               time.sleep(1)
               continue
           
        for dev in devices:
            cam = pylon.InstantCamera()
            cam.Attach(tlFactory.CreateDevice(dev))
            self.cameras.append(cam)
        
    def get_input_stream(self, index=0):
        if index < len(self.cameras):
            return InputStreamB(self.cameras[index], index)
        else:
            raise IndexError("Camera index out of range")


# This is for testing the camera input stream
if __name__ == "__main__":
    factory = DeviceFactory()
    factory.wait_for_cameras(3)
    
    # Assuming you want to work with the first camera
    cam_stream = factory.get_input_stream(0)
    cam_stream_2 = factory.get_input_stream(1)
    cam_stream_3 = factory.get_input_stream(2)

    cam_stream.start_grabbing()
    cam_stream_2.start_grabbing()
    cam_stream_3.start_grabbing()

    # cam_stream.start_recording()
    # cam_stream_2.start_recording()
    # cam_stream_3.start_recording()
    # input("Press Enter to stop grabbing...")

    windows = ['cam 1', 'cam 2', 'cam 3']

    for window in windows:
        cv.namedWindow(window, cv.WINDOW_NORMAL)

    key  = cv.waitKey(1)
    while  key != 113:
       buffer = cam_stream.next()
       buffer = cv.putText(buffer, f"Frame Rate: {cam_stream.get_frame_rate()}", 
                           (20, 20), 
                           cv.FONT_HERSHEY_COMPLEX, 
                           1, (0, 244, 0), 2)
       cv.imshow(windows[0], buffer)

       buffer = cam_stream_2.next()
       buffer = cv.putText(buffer, f"Frame Rate: {cam_stream_2.get_frame_rate()}", 
                           (20, 20), 
                           cv.FONT_HERSHEY_COMPLEX, 
                           1, (0, 244, 0), 2)
       cv.imshow(windows[1],buffer)

       buffer = cam_stream_3.next()
       buffer = cv.putText(buffer, f"Frame rate: {cam_stream_3.get_frame_rate()}", 
                           (20, 20), 
                           cv.FONT_HERSHEY_COMPLEX, 
                           1, (0, 244, 0), 2)
       cv.imshow(windows[2], buffer)
       key = cv.waitKey(20)
      
    cam_stream.stop()
    cam_stream_2.stop()
    cam_stream_3.stop()       
    cv2.destroyAllWindows()
