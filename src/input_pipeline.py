from camera.input import InputStream, InputStreamB
from detector import ISDetector
from coordinate_transforms import draw_points, Transformer
from pathlib import Path
import cv2 as cv
from utils import CThread
from threading import Event
import numpy as np
import json
from cfg.paths_config import __CALIBRATION_CFG_DIR__
import os
import time


class InputPipeline:
    def __init__(self, stream:InputStream|InputStreamB, id:int, weights:Path|str, engine:bool=True, **kwargs) -> None:
        self.__path = stream
        self.__id = id
        self.__input_stream = stream
        self.__weights = weights
        self.__engine = engine
        self.__detector = ISDetector(self.__weights, self.__engine, id)
        self.__transformer = Transformer(id)
        # self.__interactive_calibration =
        self.__worker_thread = None
        self.__exit_event = Event()
        self.__result = None
        self.__results_buffer = []
        self.__is_result_ready = Event()
        self.__data_ready = Event()
        self.__started = False
        self.__clean_frame = None
        self.__polygons = []
        self.__points = []
        self.__is_mask_init = False
        self.__frame = None
        self.__conf_window = "Init Poly Masks"
        self.__calib__path = f"{__CALIBRATION_CFG_DIR__.as_posix()}/poly_fill_cam_{self.__id}.json"
        self.__start_flag  = None

    def set_start_flag(self, flag)->None:
        self.__start_flag = flag
        self.__input_stream.set_start_flag(self.__start_flag)

    def get_frame_rate(self)->float:
        return self.__input_stream.get_frame_rate()

    def get_frame_drops(self)->int:
        return self.__input_stream.get_frame_drops()

    def init(self)->None:
        if not self.__input_stream.Is_grabbing():
            self.__input_stream.start_grabbing()
        self.__detector.start() # Start the detections loop
        self.next()

    def write_calib(self):
        data = {}
        with open(self.__calib__path, "w") as fp:
            data["polygons"] = [point.tolist() for point in self.__polygons]
            json.dump(data, fp)
    
    def read_calib(self):
        data = {}
        with open(self.__calib__path, 'r') as fp:
            data = json.load(fp)
            polygons = data.get('polygons')
            for poly in polygons:
                self.__polygons.append(np.array(poly))
        return data
    
    def is_calib(self)->bool:
        return os.path.exists(self.__calib__path)

    def __init__polymasks(self, frame)->None:
        if self.is_calib():
            self.read_calib()
            return
        self.__conf_window = "Init Poly Masks"
        self.__frame = frame
        cv.namedWindow(self.__conf_window, cv.WINDOW_NORMAL)
        cv.imshow(self.__conf_window, self.__frame)
        cv.setMouseCallback(self.__conf_window, self.get_poly_masks)
        key = cv.waitKey(10)
        while key != 115:
            key = cv.waitKey(0)
        
        self.__is_mask_init = True
        cv.destroyWindow(self.__conf_window)
        self.write_calib()

    
    def get_poly_masks(self, event, x, y, flags, params):
        frame = self.__frame.copy()
        if event == cv.EVENT_MOUSEMOVE:
            if len(self.__points) > 0:
                frame = cv.polylines(frame, [np.array(self.__points)], False, (0, 255, 0), 2)
                frame = cv.line(frame, self.__points[-1], (x, y), (0, 255, 0), 2)
                

        elif event == cv.EVENT_LBUTTONDOWN:
            if len(self.__points) < 4:
                self.__points.append((x, y))
                frame = cv.circle(frame, (x, y), 5, (0, 255, 0), cv.FILLED)
            if len(self.__points) == 4:
                self.__polygons.append(np.array(self.__points))
                self.__points = []

        for poly in self.__polygons:
            frame = cv.polylines(frame, [poly], True, (0, 255, 0), 2)

        cv.imshow(self.__conf_window, frame)

    def __fill_polygons(self, frame:cv.Mat)->cv.Mat:
        height, width = frame.shape[:2]
        masked_img = frame#.copy()  # White canvas
        for poly in self.__polygons:
            mask = np.zeros((height, width), dtype=np.uint8)
            cv.fillPoly(mask, [poly], 255)
            mask = 255 - mask
            masked_img = cv.bitwise_and(masked_img, masked_img, mask=mask)
        return masked_img

    def getDstPtsRaw(self):
        return self.__transformer.getDstPtsRaw()

    def getDstPts(self):
        return self.__transformer.getDstPts()
    
    def get_mini_boundary(self)->list[dict]:
        return self.__transformer.get_mini_boudary()
    
    def getSrcPts(self)->tuple[int, list]:
        return (self.__id, self.__transformer.getSrcPts())
    
    def get_offsets(self)->tuple:
        return self.__transformer.get_offsets()
    
    def normalize_one(self, det:list[dict])->tuple:
        return self.__transformer.normalize_one(det)
    
    def set_perspective_transform(self, pers_trans)->None:
        self.__transformer.set_perspective_transform(pers_trans)
    

    def transform_one(self, det:list[dict])->list[dict]:
        return self.__transformer.transform_one(det)
  

    def next(self)->tuple[dict, cv.Mat]:
        # read input from the input stream
        # Pass the input Matrix into the Detector
        # Get the results of the Detector
        # pass the results of the detector to the Transformer
        # populate the result list with the output of the transformer
        
        if not self.__input_stream.Is_grabbing():
            self.__input_stream.start_grabbing()

        start_time = time.time() 
        frame = self.__input_stream.next()
        
        if not self.__is_mask_init:
            self.__init__polymasks(frame)
            self.__input_stream.set_polygons(self.__polygons)
      
        self.__detector.detect(frame)
        res_obj, detections, self.__clean_frame = self.__detector.get_result()

        if detections is not None and res_obj is not None:
            img, dets, res_vec  = self.__transformer.transform(res_obj.orig_img, detections)
            # end_time = time.time()
            # proc_time_ms = round((end_time - start_time)*1000)
            # if proc_time_ms >= 50:
            #     print(f"Stream Processing Time: {proc_time_ms}ms \t Number of Detections: {len(detections)} \t Stream ID: {self.get_stream_id()}")
            return img, dets, res_vec, self.__clean_frame
        return res_obj.orig_img, detections, [], self.__clean_frame
        
    def get_clean_frame(self)->cv.Mat:
        return self.__clean_frame

    def __run(self)->None:
        while not self.__exit_event.is_set():
            # start_time = time.time()
            self.__result = self.next()
            self.__results_buffer.append(self.__result)
            if len(self.__results_buffer) >= 5:
                # self.__results_buffer.pop(0) # Pop the earliest frame to be 10 frames behind atmost.
                if type(self.__input_stream) is InputStream:
                    time.sleep(0.01)
            self.__is_result_ready.set()

            
            if type(self.__input_stream) is InputStream:
                time.sleep(0.01)
            
            # if proc_time >= 100:
            #     print(f"Stream Processing Time: {proc_time}ms Stream ID: {self.get_stream_id()}")
              
    def get_stream_id(self)->int:
        return self.__id

    def isOutputReady(self)->bool:
        return self.__is_result_ready.is_set()
    
    def get_result(self)->tuple|None:
        start_time = time.time()
        if len(self.__results_buffer) == 0:
            self.__is_result_ready.wait() # wait for the data to be ready
            result = self.__results_buffer.pop(0)
        else:
            result = self.__results_buffer.pop(0)
        self.__is_result_ready.clear()
        end_time = time.time()
        return result

    def start(self)->None:
        if not self.__started:
            self.__worker_thread = CThread(target=self.__run)
            self.__worker_thread.start()
            self.__started = True

    def start_recording(self):
        if not self.__input_stream.is_recording():
            self.__input_stream.start_recording()
    
    def stop_recording(self):
        if self.__input_stream.is_recording():
            self.__input_stream.stop_recording()

    def is_recording(self)->bool:
        return self.__input_stream.is_recording()

    def is_grabbing(self)->bool:
        return self.__input_stream.Is_grabbing()

    
    def stop(self)->None:
        print(f"Closing stream {self.__id} ...")
        self.__exit_event.set()
        self.__data_ready.set() # to close it
        self.__worker_thread.join()
        self.__input_stream.stop()
        self.__detector.stop_detector()
        
        
        del self.__worker_thread
        
