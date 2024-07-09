


class CameraCalibModel:
    def __init__(self)->None:
        self.__boundary_points = [
            (0,0),
            (1, 0),
            (1, 1),
            (0, 1)
        ]

    def get_boundary_points(self)->None:
        return self.__boundary_points
    
    def set_boundary_points(self, points:list[tuple[float]])->None:
        self.__boundary_points = points

    