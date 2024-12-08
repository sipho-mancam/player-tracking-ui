import types
import typing
import numpy as np
import cv2 as cv
from pathlib import Path
import json
import os

__CRICKET_CALIB_PATH__ = Path(r"C:\ProgramData\Player Tracking Software\shared_files\calibration_data\cricket")
__DATA_DIR__ = Path(r"C:\Users\Sipho\Pictures\Cricket Image Data")
"""
Data Requirements for the CricketCalibration Model
1. Frame - Cam 1, 2, 3
2. Polygons 
"""
class FramesModel:
    def __init__(self, id)->None:
        self._id = id
        self._current_frame = None
        self._data_path = __DATA_DIR__ / f"{self._id}"
        self._frames_buffer = []
        self._frame_index = 0
        self._width = 0
        self._height = 0
        self.load_frames()

    def get_dimensions(self)->tuple:
        return self._width, self._height   
        
    def load_frames(self)->None:
        if os.path.isdir(self._data_path):
            for file in os.scandir(self._data_path):
                if file.name.endswith('.bmp'):
                    self._frames_buffer.append(
                        cv.imread(file.path)
                    )

        if self._width == 0 or self._height == 0 and len(self._frames_buffer) > 0:
            frame = self._frames_buffer[0]
            self._height, self._width, _ = frame.shape

    def next_frame(self)->cv.Mat|None:
        if len(self._frames_buffer) == 0:
            return
        
        if self._frame_index < len(self._frames_buffer):
            self._current_frame = self._frames_buffer[self._frame_index]
            self._frame_index += 1
            return self._current_frame
        
        self._frame_index = 0
        self._current_frame = self._frames_buffer[self._frame_index]
        return self._current_frame

class CameraCalibrationModel:
    def __init__(self, id, frames_model:FramesModel = None)->None:
        self._id = id
        self._dst_poly = np.array([[0,0], [1, 0], [1,1], [0, 1]])
        self._src_poly = np.array([], dtype=np.float32)
        self._perspective_matrix = None
        self._calibration_state = {
            "dst_pts":self._dst_poly.tolist(),
        }
        self._frames_model = FramesModel(self._id) if frames_model is None else frames_model
        self._shape = self._frames_model.get_dimensions()
        self._normalized_src_poly = np.array([], dtype=np.float32)
        self._aligment_points = np.array([], dtype=np.float32)
        self._transformed_dst_pts = np.array([], dtype=np.float32)

    def update_perspective(self)->np.ndarray|None:
        if len(self._src_poly) == 0:
            return 
        self._perspective_matrix = cv.getPerspectiveTransform(np.array(self._src_poly, dtype=np.float32), 
                                                              np.array(self._dst_poly, dtype=np.float32))
        return self._perspective_matrix
    
    def get_alignment_points(self)->np.ndarray:
        return self._aligment_points.copy()

    def set_alignment_points(self, points:np.ndarray)->None:
        self._aligment_points = points.copy()
        self.update_dst_transformed_points(points)
    
    def update_dst_transformed_points(self, points:np.ndarray)->None:
        if points.shape[0] == 0:
            self._transformed_dst_pts = np.array([], dtype=np.float32)
            return
        
        scaled_alignment_pts = points.copy() * self._shape
        if self._perspective_matrix is not None:
            self._transformed_dst_pts = cv.perspectiveTransform(np.array([scaled_alignment_pts]), self._perspective_matrix)[0]

    def get_perspective_matrix(self)->np.ndarray|None:
        return self._perspective_matrix
    
    def update_src_poly(self, poly:np.ndarray)->None:
        self._normalized_src_poly = poly.copy()
        self._src_poly = poly * self._shape
        self._src_poly = np.round(self._src_poly)
        self.update_perspective()
        self._calibration_state["src_pts"] = self._src_poly.astype(np.int32).tolist()
        self.update_dst_transformed_points(self._aligment_points)
        
    def get_calibration_object(self)->dict:
        return self._calibration_state
    
    def get_src_poly(self)->np.ndarray:
        return self._normalized_src_poly
    
    def get_dst_poly(self)->np.ndarray:
        return self._dst_poly
    
    def get_transformed_dst_pts(self)->np.ndarray:
        return self._transformed_dst_pts.copy()
    
    def to_json(self)->None:
        src_pts = self._calibration_state.get('src_pts')
        if src_pts is None or len(src_pts) == 0:
            return 
        
        with open(__CRICKET_CALIB_PATH__ / f"calib_cam_{self._id}.json", "w") as fp:
            json.dump(self._calibration_state, fp)
        fp.close()

    def from_json(self)->None:
        if os.path.exists(__CRICKET_CALIB_PATH__ / f"calib_cam_{self._id}.json"):
            with open(__CRICKET_CALIB_PATH__ / f"calib_cam_{self._id}.json", "r") as fp:
                data = json.load(fp)
                self._calibration_state = data
                dst_pts = data['dst_pts']
                src_pts = data['src_pts']
                dst_pts = np.array(dst_pts, dtype=np.float32)
                src_pts = np.array(src_pts, dtype=np.float32)
                self._src_poly = src_pts
                self._dst_poly = dst_pts
                self._normalized_src_poly = src_pts.copy() / self._shape
                self.update_src_poly(self._normalized_src_poly)

    def next_frame(self)->cv.Mat:
        return self._frames_model.next_frame()


class SpaceMergerModel:
    def __init__(self, models_list:list[CameraCalibrationModel])->None:
        self.__models_list = models_list
        self._left = 0.3
        self._right = 0.3
        self._middle = 0.4
        self._unified_space = []

    def update_points(self)->None:
        self._unified_space.clear()
        for i, model in enumerate(self.__models_list):
            dst_pts =  model.get_transformed_dst_pts()
            if dst_pts.shape[0] == 0:
                continue

            if i ==0:
                dst_pts *= (self._left, 1)
            elif i==1:
                dst_pts *= (self._middle, 1)
                dst_pts += (self._left, 0)
            elif i==2:
                dst_pts *= (self._right, 1)
                dst_pts += (self._left + self._middle, 0)
            self._unified_space.extend(dst_pts.tolist())

    def get_unified_space(self)->np.ndarray:
        self.update_points()
        return np.array(self._unified_space, dtype=np.float32).copy()

class CricketCalibrationModel:
    def __init__(self, frames_models:list[FramesModel]=None)->None:
        if frames_models is None:
            self._models_list = [
                CameraCalibrationModel(0),
                CameraCalibrationModel(1),
                CameraCalibrationModel(2)
            ]
        else:
            self._models_list = [
                CameraCalibrationModel(0, frames_models[0]),
                CameraCalibrationModel(1, frames_models[1]),
                CameraCalibrationModel(2, frames_models[2])
            ]

        self._selected_model = 0
        self._current_active_model = self._models_list[self._selected_model]
        self.__space_merger = SpaceMergerModel(self._models_list)

    def get_unified_space(self)->np.ndarray:
        return self.__space_merger.get_unified_space()

    def get_current_camera_index(self)->int:
        return self._selected_model
    
    def select_model(self, id)->None:
        if id >= len(self._models_list):
            return
        self._current_active_model = self._models_list[id]
        self._selected_model = id

    def get_alignment_pts(self)->np.ndarray:
        return self._current_active_model.get_alignment_points()
    
    def set_alignment_pts(self, points:np.ndarray)->None:
        self._current_active_model.set_alignment_points(points)

    def get_transformed_dst_pts(self)->np.ndarray:
        return self._current_active_model.get_transformed_dst_pts()


    def get_perspective_matrix(self)->cv.Mat|None:
        return self._current_active_model.get_perspective_matrix()
    
    def get_src_poly(self)->np.ndarray:
        return self._current_active_model.get_src_poly()
    
    def get_dst_poly(self)->np.ndarray:
        return self._current_active_model.get_dst_poly()
    
    def dump_to_json(self)->None:
        for model in self._models_list:
            model.to_json()
        
    def load_from_json(self)->None:
        self._current_active_model.from_json()
    
    def get_calibration_state(self)->dict:
        return self._current_active_model.get_calibration_object()
    
    def update_src_poly(self, poly:np.ndarray)->None:
        self._current_active_model.update_src_poly(poly)

    def next_frame(self)->cv.Mat|None:
        return self._current_active_model.next_frame()
