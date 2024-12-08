from .model import CricketCalibrationModel
import cv2 as cv
import numpy as np

class CalibrationController:
    def __init__(self, view, models:list=None)->None:
        self.__model = CricketCalibrationModel(models) #if model is None else model
        self.__view = view

    def get_unified_space(self)->np.ndarray:
        return self.__model.get_unified_space()

    def next_frame(self)->cv.Mat:
        return self.__model.next_frame()
    
    def dump_to_json(self)->None:
        self.__model.dump_to_json()
    
    def load_from_json(self)->None:
        self.__model.load_from_json()

    def update_src_poly(self, poly:np.ndarray)->None:
        self.__model.update_src_poly(poly)
        self.__view.updateUI()

    def get_src_poly(self)->np.ndarray:
        return self.__model.get_src_poly()
    
    def get_dst_poly(self)->np.ndarray:
        return self.__model.get_dst_poly()
    
    def get_current_camera_index(self)->int:
        return self.__model.get_current_camera_index()
    
    def get_alignment_pts(self)->np.ndarray:
        return self.__model.get_alignment_pts()
    
    def set_alignment_pts(self, pts:np.ndarray)->None:
        self.__model.set_alignment_pts(pts)
        self.__view.updateUI()

    def get_transformed_dst_points(self)->np.ndarray:
        # print(self.__model.get_transformed_dst_pts())
        return self.__model.get_transformed_dst_pts()
    
    def get_perspective(self)->cv.Mat|None:
        return self.__model.get_perspective_matrix()
    
    def get_calibration_state(self)->dict:
        return self.__model.get_calibration_state()
    
    def select(self, id)->None:
        self.__model.select_model(id)
        if self.__view is None:
            return
        frame = self.__model.next_frame()
        if frame is not None:
            self.__view.update_frame(frame)
        self.__view.updateUI()