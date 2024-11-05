from .model import CameraCalibModel

class CamCalibController:
    def __init__(self, id)->None:
        self.__id = id
        self.__current_frame = None
        self.__view = None
        self.__model = CameraCalibModel()
        self.updated = False

    def update_frame(self, frame)->None:
        self.__current_frame = frame.copy()
        if self.__view is not None and not self.updated:
            self.__view.update_frame(self.__current_frame)
            self.updated = True

    def get_model_data(self)->dict:
        """
        Return the Model Dictionary with 
        {
            poly_points: [tuple[float], tuple[float], tuple[float], tuple[float]],
            mask_polys: [list[tuple[float]]]
        }
        """
        return self.__model.get_data()

    def clear_view(self)->None:
        self.__view = None
        self.updated = False
    
    def set_view(self, view)->None:
        self.__view = view
    
    def set_boundary_points(self, points:list[tuple[float]])->None:
        if points is None:
            return
        self.__model.set_boundary_points(points)
    
    def set_mask_polys(self, mask_polys)->None:
        if mask_polys is None:
            return
        self.__model.set_mask_polys(mask_polys)



class CalibrationManager:
    def __init__(self)->None:
        self.__cam_controllers = [
            CamCalibController(0),
            CamCalibController(1),
            CamCalibController(2)
        ]
        self.__current_selected = 0
        self.__frame_view = None
        self.init()

    def init(self)->None:
        self.__cam_controllers[self.__current_selected].set_view(self.__frame_view)

    def register_frame_view(self, frame_view)->None:
        self.__frame_view = frame_view
        self.select(self.__current_selected)
        self.__frame_view.set_controller(self)
        data = self.__cam_controllers[self.__current_selected].get_model_data()
        self.__frame_view.set_camera_data(data)
    
    def save_current_cam_calib(self)->None:
        print("Camera Calib Saved ...")
        data = self.__frame_view.get_camera_data()
        self.__cam_controllers[self.__current_selected].set_boundary_points(data.get('poly_points'))
        self.__cam_controllers[self.__current_selected].set_mask_polys(data.get('mask_polys'))
    
    def select(self, id)->None:
        self.__cam_controllers[self.__current_selected].clear_view()
        self.__current_selected = id
        self.__cam_controllers[id].set_view(self.__frame_view)
        data = self.__cam_controllers[id].get_model_data()
        self.__frame_view.set_camera_data(data)

    def get_camera_controllers(self)->list[CamCalibController]:
        return self.__cam_controllers