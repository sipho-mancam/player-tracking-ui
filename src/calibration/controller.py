
class CamCalibController:
    def __init__(self, id)->None:
        self.__id = id
        self.__current_frame = None
        self.__view = None

        self.updated = False

    def update_frame(self, frame)->None:
        self.__current_frame = frame

        if self.__view is not None and not self.updated:
            self.__view.update_frame(self.__current_frame)
            self.updated = True

    def clear_view(self)->None:
        self.__view = None
        self.updated = False
    
    def set_view(self, view)->None:
        self.__view = view



class CalibrationManager:
    def __init__(self)->None:
        self.__cam_controllers = [
            CamCalibController(0),
            CamCalibController(1),
            CamCalibController(2)
        ]
        self.__current_selected = 1
        self.__frame_view = None
        self.init()

    def init(self)->None:
        self.__cam_controllers[self.__current_selected].set_view(self.__frame_view)

    def register_frame_view(self, frame_view)->None:
        self.__frame_view = frame_view
        self.select(self.__current_selected)
        self.__frame_view.set_controller(self)
    
    def select(self, id)->None:
        self.__cam_controllers[self.__current_selected].clear_view()
        self.__current_selected = id
        self.__cam_controllers[id].set_view(self.__frame_view)

    def get_camera_controllers(self)->list[CamCalibController]:
        return self.__cam_controllers