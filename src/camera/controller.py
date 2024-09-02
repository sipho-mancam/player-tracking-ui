from threading import Thread, Event
from .camera_ui import CameraWidget
from .input import InputManager, CameraModel

class CameraController:
    def __init__(self, model, view)->None:
        self.__model = model
        self.__view = view
        self.__stop_event = Event()
        self.__worker = None
        self.__input_outlet_controllers = []

    def registerController(self, controller)->None:
        self.__input_outlet_controllers.append(controller)

    def __run(self)->None:
        # Runs the event loop between the model update and the view events
        while not self.__stop_event.is_set():
            frame_buffer = self.__model.next()
            self.__view.update_frame(frame_buffer)
            self.__view.set_camera_data(self.__model.get_stream_data())

            # update controllers
            for controller in self.__input_outlet_controllers:
                controller.update_frame(frame_buffer)

    def start(self)->None:
        # Start the the models grab loop
        self.__model.start_grabbing()
        if self.__worker is None:
            self.__worker = Thread(target=self.__run)
            self.__worker.start()

    def stop(self)->None:
        if self.__worker is not None:
            self.__stop_event.set()
            self.__worker.join()
            self.__model.stop()

class CamerasManager:
    
    def __init__(self, views_list:list[CameraWidget])->None:
        self.__views_list = views_list
        self.frame_size = 15089340
        self.__input_manager = InputManager("Kit Detector", self.frame_size)
        self.__controllers = []
        self.init()

    def init(self)->None:
        for idx, view in enumerate(self.__views_list):
            self.__controllers.append(
                CameraController(self.__input_manager.get_input_stream(idx), view)
            )
            if idx >= 2:
                break

        for controller in self.__controllers:
            controller.start()

    def registerCameraInputControllers(self, controllers:list)->None:
        for idx, controller in enumerate(controllers):
            self.__controllers[idx].registerController(controller)

    def stop(self)->None:
        self.__input_manager.stop()
        for controller in self.__controllers:
            controller.stop()
        