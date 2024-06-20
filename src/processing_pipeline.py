from camera.input import DeviceFactory, InputStreamB
from input_pipeline import InputPipeline
from space_merger import SpaceMerger, TrackBoxes
from output_ import DetectionsOutput
from pathlib import Path
from utils import CThread
from threading import Event, Thread
import cv2 as cv
import numpy as np
from botsort_tracker import *
from filter import DetectionsFilter
from pprint import pprint
import time
from ui.assignment_ui import ui_thread_start, app, ex


def load_mini_map(win_name)->cv.Mat:
    mini_map_bg = cv.imread("./App/assets/soccer_pitch_poles.png")
    ret = np.zeros(mini_map_bg.shape, dtype=np.uint8) + 128
    cv.imshow(win_name, ret)
    cv.waitKey(1)
    return mini_map_bg

def update_mini_map(win_name, bg_img, detections, cam_frames:list[list[dict]]=None):
    width = 0.89 * bg_img.shape[1] 
    height = 0.895 * bg_img.shape[0]
    clone_bg = np.array(bg_img)
    x_offset = 140
    y_offset = 85
    color = (255, 255, 0)
    for det in detections:
        coord = det['coordinates'] 
        # print(coord)
        if coord is not None :#and det.get('track_id') is not None:
            x_scaled = x_offset + int(coord[0]*width)
            y_scaled = y_offset + int(coord[1]*height)
            if det.get('is_overlap') is not None and det.get('is_overlap'):
                color = (0, 0, 255)
            else:
                color = det.get('color') if det.get('color') is not None else (255, 255, 0)

            if det.get('is_child'):
                color = (255, 0, 255)
            
            # det.get('color') if det.get('colors') else
            clone_bg = cv.circle(clone_bg, (x_scaled, y_scaled), 10,  color, cv.FILLED)

            if det.get('global_id') is not None:
                clone_bg = cv.putText(clone_bg, f"{det['global_id']}", (x_scaled-15, y_scaled+5), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2)

            # if det.get('track_id') is not None:
            #     clone_bg = cv.putText(clone_bg, f"{det['track_id']}", (x_scaled-15, y_scaled+5), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2)

    if cam_frames is not None:
        for boundary in cam_frames:
            if len(boundary) > 0:
                l = [point.get('coordinates') for point in boundary]
                c_l = [((int(x*width))+x_offset, (int(y*height)+y_offset)) for (x, y) in l]
                clone_bg = cv.polylines(clone_bg, [np.array(c_l)], True, boundary[0]['color_l'], 2)
            
    cv.imshow(win_name, clone_bg)
    cv.waitKey(1)


class ProcessingPipeline:
    def __init__(self, stream1, stream2, stream3, weights)->None:
        self.__input_streams = [InputPipeline(stream1, 0, weights), 
                                InputPipeline(stream2, 1, weights),
                                InputPipeline(stream3, 2, weights)]
        self.__space_merger = SpaceMerger(self.__input_streams)
        self.__space_filter = DetectionsFilter()
        self.__detections_output = DetectionsOutput()

        self.mm_win_name = "Mini-Map View"
        self.width = 2590
        self.height = 1942
        self.mm_bg = load_mini_map(self.mm_win_name)
        self.__box_tracker = TrackBoxes(self.width*3, self.height)
        self.mini_map_data = []
        self.mm_boundary = []
        self.filtered_output = []

        self.__stop = False
        self.__frame_counter = 0
        self.__stop_event = Event()
        self.__ui_update_event = Event()
        self.__buffer_clear = Event()

        
        self.cams_frames_output = []
    
    def stop(self):
        print("Closing processing pipeline ...")
        for input in self.__input_streams:
            input.stop()     
        self.__stop = True
       
        
    def start_recording(self):
        for input in self.__input_streams:
            input.start_recording()
    
    def stop_recording(self):
        for input in self.__input_streams:
            input.stop_recording()

    def ui_main_loop(self):
        while not self.__stop_event.is_set():
            # cv.waitKey(1)
            self.__ui_update_event.wait()
            self.update_ui()
            self.__ui_update_event.clear()
            # print("I'm here-- main loop")
        

    def update_ui(self)->None:
        cv.namedWindow("Preview Window", cv.WINDOW_NORMAL)
        local = self.cams_frames_output
        merged_image = self.__space_merger.merge_frame(local)
        self.__buffer_clear.set()
        
        # Merge detections results for mini_map <normalized>
        merged_image = cv.putText(merged_image, "1. Press Q to quit.", 
                                    (int(merged_image.shape[1]*0.8), 30),
                                    cv.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 0), 1)
        
        merged_image = cv.putText(merged_image, "2. Press R to start recording.", 
                                    (int(merged_image.shape[1]*0.8), 30+20), 
                                    cv.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 0), 1)
        
        merged_image = cv.putText(merged_image, "3. Press S to stop recording.", 
                                    (int(merged_image.shape[1]*0.8), 30+40), 
                                    cv.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 0), 1)
        
        merged_image = cv.putText(merged_image, f"Frame Number: {self.__frame_counter}", 
                                    (int(merged_image.shape[1]*0.2), 20+5), 
                                    cv.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 0), 1)
        cv.imshow("Preview Window", merged_image)
        self.__box_tracker.update(self.filtered_output)
        # self.__detections_output.write_to_file()
        
        update_mini_map(self.mm_win_name, self.mm_bg, self.mini_map_data, self.mm_boundary)
        # print("I Execute here")
        key = cv.waitKey(1)
        if key == 113: # Key Q
            self.__stop_event.set()
            self.stop()
        elif key==114: # Key R
            print("Recording started ...")
            self.start_recording()
        elif key ==115: # key S
            print("Recording stopped ...")
            self.stop_recording() 
            

    def run(self, mm_win_name="")->None:
        width = 2590
        height = 1942
        """
        Testing code, to delete later
        """
        self.mm_win_name = mm_win_name
        # b_t = TrackBoxes(3*width, height)
        # Run the input pipeline
        # run the space merger
        # run the output and repeat
        
        # ui_thread = Thread(target=self.ui_main_loop, daemon=True)
        # ui_thread.start()
        # initiailize the streams here

        ui_thread_start(self.mm_bg)

        for stream in self.__input_streams:
            stream.init() 
        try:
            for stream in self.__input_streams:
                stream.start()
                s_id, boundary_list = stream.getSrcPts()
                dst_pts = stream.getDstPtsRaw()
                boundary_list = [(p[0]+ s_id * width, p[1]) for p in boundary_list]
                dst_pts = [(p[0] + s_id * width, p[1]) for p in dst_pts]

                self.__box_tracker.set_boundaries(boundary_list)
                self.__box_tracker.set_boundaries(dst_pts)
            # run the streams continuosly
            while not self.__stop:
                start_time = time.time()
                cams_output = []
                self.cams_frames_output = []
                frames_clean = []

                for _, stream in enumerate(self.__input_streams):
                    # wait for stream 1, 2 and then 3 
                    res = stream.get_result()
                    if res is not None:  
                        self.cams_frames_output.append(res[0])
                        cams_output.append(res[1])
                        frames_clean.append(res[-1])
                
                if len(cams_output) == 3:
                    if not self.__space_merger.is_init():
                        self.__space_merger.set_mini_map_callback(update_mini_map, (self.mm_win_name, self.mm_bg, None))
                        self.__space_merger.init(self.cams_frames_output)

                        for stream in self.__input_streams:
                            # print(stream.getDstPts())
                            self.mm_boundary.append(self.__space_merger.align_frame_points(stream.getDstPts(), stream.get_stream_id()))

                    #TCF
                    frame_track = self.__space_merger.merge_frame_for_tracking(frames_clean)
                    merged_space = self.__space_merger.merge(cams_output)
                    self.filtered_output = self.__space_filter.filter(merged_space)
                    self.mini_map_data, structured_data = track2(frame_track, self.filtered_output)
                    
                    # Outputs
                    structured_data['frame_number'] = self.__frame_counter
                    print(self.__frame_counter)
                    self.__detections_output.update(structured_data) 
                    self.__detections_output.write_to_kafka()
                    self.__frame_counter +=1
                    self.update_ui()
                    end_time = time.time()
                print(f"Processing Time: {round((end_time-start_time)*1000)} ms")

        except KeyboardInterrupt as ke:
            self.stop()